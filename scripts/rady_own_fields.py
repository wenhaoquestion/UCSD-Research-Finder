"""Verify literal research lists and email on an existing own Rady profile."""
from urllib.parse import urlsplit
import re

from faculty_profile_bindings import captured_source
from faculty_scoped_titles import same_named_subject
from refresh_faculty_directories import public_email
from refresh_labs import DOM, every_node


def rady_own_fields(item, cache, name):
    """Return own labelled fields with exact captured subject/section proofs.

    The caller separately verifies the original ID and unique primary ownership.
    This reader cannot qualify faculty, bind another profile or infer a topic.
    """
    base, markup = captured_source(item, cache)
    for uri in [base['requestedUrl'], base['sourceUrl']]:
        parsed = urlsplit(uri)
        if (parsed.hostname != 'rady.ucsd.edu'
                or not re.fullmatch(r'/faculty-research/faculty/[a-z0-9-]+\.html', parsed.path)
                or parsed.query or parsed.fragment):
            raise ValueError('Rady own fields require the exact original individual faculty resource')
    visited = base['requestedUrl']
    for hop in item['fetch'].get('redirects', []):
        if hop.get('from') != visited or hop.get('httpStatus') not in {301, 302, 303, 307, 308}:
            raise ValueError('Rady fields require the actual continuous redirect chain')
        visited = hop.get('to')
    if visited != base['sourceUrl'] or item['fetch'].get('httpStatus') != 200:
        raise ValueError('Rady fields require an actual successful own-source response')
    dom = DOM(markup); nodes = list(every_node(dom.main()))
    containers = [n for n in nodes if n.tag == 'section' and n.attrs.get('aria-label') == 'Profile Container']
    titles = [n.text() for n in every_node(dom.root) if n.tag == 'title']
    subjects = [n for n in nodes if n.tag == 'h1']
    if (len(containers) != 1 or len(subjects) != 1 or len(titles) != 1
            or not same_named_subject(name, subjects[0].text())
            or not same_named_subject(subjects[0].text(), titles[0].split(',', 1)[0].strip())):
        raise ValueError('Rady fields require one unchanged complete person in the title and H1')
    container = containers[0]; subject = subjects[0]
    if (subject not in list(every_node(container)) or not subject.parent
            or subject.parent.tag != 'header' or subject.parent.attrs.get('aria-label') != 'Profile Name'
            or not {'profile-section', 'profile-section-header'} <= set(subject.parent.attrs.get('class', '').split())):
        raise ValueError('Rady fields require the named own-profile header')
    tabs = [n for n in every_node(container) if n.tag == 'article'
            and n.attrs.get('id') == 'profileTab' and n.attrs.get('aria-label') == 'Profile Tabs']
    if len(tabs) != 1:
        raise ValueError('Rady research fields require the single own Profile Tabs article')
    labels = [n for n in every_node(tabs[0]) if n.tag == 'li' and n.attrs.get('role') == 'tab'
              and n.text() == 'Research Areas' and n.attrs.get('id') == n.attrs.get('aria-controls')]
    if len(labels) != 1 or not labels[0].attrs.get('id'):
        raise ValueError('Rady research requires its explicitly labelled Research Areas tab')
    key = labels[0].attrs['id']
    panels = [n for n in every_node(tabs[0]) if n.tag == 'div' and n.attrs.get('aria-labelledby') == key
              and 'resp-tab-content' in n.attrs.get('class', '').split()]
    if len(panels) != 1 or not panels[0].parent or 'resp-tabs-container' not in panels[0].parent.attrs.get('class', '').split():
        raise ValueError('Rady research requires the matching own Research Areas panel')
    panel = panels[0]; siblings = [n for n in panel.parent.children if hasattr(n, 'tag')]
    index = siblings.index(panel); heading = siblings[index - 1] if index else None
    if (heading is None or heading.tag != 'h2' or heading.text() != 'Research Areas'
            or heading.attrs.get('aria-controls') != key or 'resp-accordion' not in heading.attrs.get('class', '').split()):
        raise ValueError('The Rady research panel must follow its matching accordion heading')
    children = [n for n in panel.children if hasattr(n, 'tag') and n.text()]
    expected = ['Methodological Areas:', 'Application Domains:']
    if len(children) != 4:
        raise ValueError('Research terms must be the two explicitly labelled own lists')
    groups = []
    for index, label in enumerate(expected):
        paragraph, listing = children[index * 2:index * 2 + 2]
        strong = [n for n in paragraph.children if hasattr(n, 'tag')]
        terms = [n for n in listing.children if hasattr(n, 'tag')]
        if (paragraph.tag != 'p' or paragraph.text() != label or len(strong) != 1
                or strong[0].tag != 'strong' or strong[0].text() != label
                or listing.tag != 'ul' or not terms or any(n.tag != 'li' for n in terms)
                or any(any(hasattr(child, 'tag') for child in n.children) for n in terms)):
            raise ValueError('Rady research areas must remain literal direct list items under their own category')
        values = [n.text() for n in terms]
        if any(not 1 < len(value) <= 160 or value.lower() in {'unknown', 'not found', 'n/a', 'coming soon'} for value in values):
            raise ValueError('Empty or placeholder Rady topics cannot become verified research areas')
        groups.append({'labelAsListed': label, 'valuesAsListed': values})
    areas = list(dict.fromkeys(value for group in groups for value in group['valuesAsListed']))
    common = {**base, 'status': 'verified', 'subjectTemplate': 'rady_profile_tabs_own_fields',
              'nameAsDisplayed': subject.text(), 'containerLabel': 'Profile Container'}
    fields = {'researchAreas': areas}
    proofs = {'researchAreas': [{**common, 'method': 'named_rady_own_research_area_lists',
               'evidenceType': 'labelled_list', 'articleId': 'profileTab', 'tabLabel': 'Research Areas',
               'tabId': key, **group, 'evidence': subject.text() + ' | Research Areas | '
               + group['labelAsListed'] + ' ' + ' | '.join(group['valuesAsListed'])} for group in groups]}
    contacts = [n for n in every_node(container) if n.tag == 'article' and n.attrs.get('aria-label') == 'Profile Details'
                and 'profile-section-contact' in n.attrs.get('class', '').split()]
    if len(contacts) > 1:
        raise ValueError('Conflicting own Rady contact articles require review')
    emails = [n for article in contacts for n in every_node(article)
              if n.tag == 'li' and 'email' in n.attrs.get('class', '').split()]
    if len(emails) > 1:
        raise ValueError('Conflicting own Rady email fields require review')
    if emails:
        node = emails[0]; anchors = [n for n in node.children if hasattr(n, 'tag')]
        value = public_email(node.text())
        if (len(anchors) != 1 or anchors[0].tag != 'a' or not value or value != node.text()
                or anchors[0].text() != value or anchors[0].attrs.get('href') != 'mailto:' + value):
            raise ValueError('Rady contact evidence requires the complete literal own mailto address')
        fields['email'] = value
        proofs['email'] = [{**common, 'method': 'named_rady_own_public_email_contact',
                            'evidenceType': 'own_contact_mailto', 'rawHref': 'mailto:' + value,
                            'valueAsListed': value, 'evidence': subject.text() + ' | Email: ' + value}]
    return {'capture': base, 'nameAsDisplayed': subject.text(), 'sourceTemplate': 'rady_profile_tabs_own_fields',
            'groupsAsListed': groups, 'fields': fields, 'fieldEvidence': proofs,
            'scope': 'Literal own Research Areas lists and professional email only. No identity binding,rank,appointment,department,institution,publication-topic,PI or current-HR inference.'}
