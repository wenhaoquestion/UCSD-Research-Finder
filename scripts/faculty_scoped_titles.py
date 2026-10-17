"""Read academic qualifications from named campus profile title fields.

These fields qualify an existing roster observation only. They do not rename a
person, resolve an identity, replace a roster role, or map an academic unit.
Biography, publication, navigation and unrelated-person text are excluded.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from collect_ucsd_coverage import academic_title_clause
from faculty_profile_bindings import captured_source
from refresh_faculty_directories import identity_name
from refresh_labs import DOM, evidence


def same_named_subject(left, right):
    """Accept punctuation/diacritics and compatible middle initials only."""
    a, b = identity_name(left).split(), identity_name(right).split()
    if a == b and len(a) >= 3 and any(len(token) > 1 for token in a[:-1]):
        return True
    return (min(len(a), len(b)) >= 2 and min(len(a[0]), len(b[0])) > 1
            and a[0] == b[0] and a[-1] == b[-1]
            and (not a[1:-1] or not b[1:-1]
                 or len(a[1:-1]) == len(b[1:-1]) and all(
                     x == y or min(len(x), len(y)) == 1 and x[0] == y[0]
                     for x, y in zip(a[1:-1], b[1:-1]))))


def classes(node):
    return set(node.attrs.get('class', '').split())


def scoped_academic_qualification(item, cache, name):
    if not item:
        return None
    try:
        base, markup = captured_source(item, cache)
    except ValueError:
        return None
    requested, final = [urlsplit(base[key]) for key in ['requestedUrl', 'sourceUrl']]
    if requested.hostname != final.hostname or requested.query or final.query:
        return None
    host, path = final.hostname, final.path
    requested_path = requested.path
    if host == 'matsci.ucsd.edu':
        path = path.removeprefix('/index.php')
        requested_path = requested_path.removeprefix('/index.php')
    templates = {
        'economics.ucsd.edu': '/faculty-and-research/faculty-profiles/',
        'chemistry.ucsd.edu': '/faculty/profiles/',
        'matsci.ucsd.edu': '/faculty/',
        'sociology.ucsd.edu': '/people/faculty/',
        'communication.ucsd.edu': '/people/faculty/',
        'eds.ucsd.edu': '/people/faculty/',
        'theatre.ucsd.edu': '/people/faculty/',
        'literature.ucsd.edu': '/people/faculty/',
        'polisci.ucsd.edu': '/people/faculty/',
        'rady.ucsd.edu': '/faculty-research/faculty/',
    }
    if (host not in templates or not path.startswith(templates[host])
            or not requested_path.startswith(templates[host])):
        return None
    nodes = list(DOM(markup).main().walk())
    subjects = [n for n in nodes if n.tag == 'h1']
    if len(subjects) != 1 or not same_named_subject(name, subjects[0].text()):
        return None
    subject = subjects[0]
    fields, roles, unit = {}, [], ''
    if host == 'economics.ucsd.edu':
        tabs = [n for n in nodes if n.tag == 'article' and n.attrs.get('id') == 'profileTab'
                and 'profile-section-tabs' in classes(n)]
        if len(tabs) != 1:
            return None
        for n in tabs[0].walk():
            if n.tag != 'p':
                continue
            match = re.fullmatch(r'(Type|Name|Title)(?::\s*|\s+)(.+)', n.text())
            if match:
                fields.setdefault(match[1], []).append(match[2])
        if (any(len(fields.get(k, [])) != 1 for k in ['Type', 'Name', 'Title'])
                or fields['Type'][0] not in {'Faculty', 'Affiliated Faculty', 'Adjunct Faculty'}
                or not (same_named_subject(subject.text(), fields['Name'][0])
                        or same_named_subject(subject.text(), re.sub(
                            r'^\S+\s+\(([^()\s]+)\)(?=\s)', r'\1', fields['Name'][0])))):
            return None
        roles = fields['Title']
        template = 'economics_named_profile_title_field'
    elif host == 'chemistry.ucsd.edu':
        labels = [n for n in nodes if n.tag == 'strong' and n.text() == 'Titles:']
        if len(labels) != 1:
            return None
        parent = labels[0].parent
        title_lists = [n for n in parent.children if hasattr(n, 'tag') and n.tag == 'ul'
                       and 'list-unstyled' in classes(n)]
        contact = parent.parent.parent if parent.parent else None
        if (len(title_lists) != 1 or not contact
                or not any(n.tag == 'h2' and n.text() == 'Contact Information'
                           for n in contact.children if hasattr(n, 'tag'))):
            return None
        fields['Titles'] = [n.text() for n in title_lists[0].children if hasattr(n, 'tag') and n.tag == 'li']
        roles = [text for text in fields['Titles'] if academic_title_clause(text)]
        template = 'chemistry_named_contact_titles_field'
    elif host == 'matsci.ucsd.edu':
        articles = [n for n in nodes if n.tag == 'article' and 'faculty-listing' in classes(n)
                    and n.attrs.get('about', '').removeprefix('/index.php') == path]
        if len(articles) != 1:
            return None
        own = list(articles[0].walk())
        primary = [n for n in own if 'field--name-field-primary-title' in classes(n)]
        if len(primary) != 1 or primary[0].parent.tag != 'h4':
            return None
        header = primary[0].parent.parent
        if 'mb-4' not in classes(header):
            return None
        units = [n for n in header.walk() if 'field--name-field-department' in classes(n)]
        extras = [n for n in header.walk() if 'field--name-field-additional-titles' in classes(n)]
        if len(units) != 1 or len(extras) > 1:
            return None
        fields = {'Primary title': [primary[0].text()], 'Additional titles': [
                      n.text() for field in extras for n in field.children
                      if hasattr(n, 'tag') and 'field__item' in classes(n)],
                  'Department': [units[0].text()]}
        roles = fields['Primary title'] + fields['Additional titles']
        unit = units[0].text()
        template = 'matsci_named_primary_and_additional_title_fields'
    elif host != 'sociology.ucsd.edu':
        header = subject.parent
        if (header.tag != 'header' or 'profile-section-header' not in classes(header)
                or header.attrs.get('aria-label') != 'Profile Name'):
            return None
        children = [n for n in header.children if hasattr(n, 'tag')]
        if (len(children) != 2 or children[0] is not subject or children[1].tag != 'p'
                or 'subhead' not in classes(children[1])):
            return None
        fields['Primary profile title'] = roles = [children[1].text()]
        template = 'campus_named_primary_profile_header'
    else:
        header = subject.parent
        if header.tag != 'header' or 'profile-section-header' not in classes(header):
            return None
        subheads = [n for n in header.children if hasattr(n, 'tag') and n.tag == 'p' and 'subhead' in classes(n)]
        if len(subheads) != 1 or not re.fullmatch(r"(?:[A-Za-z'’&.-]+\s+){1,8}Endowed Chair Professor", subheads[0].text()):
            return None
        fields['Named academic title'] = roles = [subheads[0].text()]
        template = 'sociology_named_endowed_professor_header'
    if (not roles or any(len(role) > 500 for role in roles) or len(unit) > 200
            or not (host == 'sociology.ucsd.edu' or any(academic_title_clause(role) for role in roles))):
        return None
    # Keep complete field text, including nonacademic additional titles, while
    # making the exact observed fields available separately for inspection.
    role = ' | '.join(dict.fromkeys(roles))
    excerpt = subject.text() + ' | ' + ' | '.join(key + ': ' + ' | '.join(values) for key, values in fields.items())
    proof = {**evidence(item['fetch'], 'identity_matched_official_profile_title_field', excerpt),
             **base, 'template': template, 'subjectTag': subject.tag,
             'subjectClass': subject.attrs.get('class', ''), 'titleFieldsAsListed': fields}
    return {'nameAsDisplayed': subject.text(), 'roleAsListed': role, 'unitAsListed': unit,
            'titleFieldsAsListed': fields, 'evidence': proof,
            'fieldEvidence': {field: proof for field in ['nameAsDisplayed', 'roleAsListed'] + (['unitAsListed'] if unit else [])}}
