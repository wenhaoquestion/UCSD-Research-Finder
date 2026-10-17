"""Complete own research sections, excluding career and publication tabs.

Biology publishes an explicitly labelled Research tab. The Jacobs template
places its short focus and own research statement before Capsule Bio. These
readers never select a paragraph merely because it mentions a research institute.
"""
import re
from urllib.parse import urlsplit

from faculty_profile_bindings import captured_source, jacobs_academic_qualification
from faculty_scoped_titles import same_named_subject
from refresh_faculty_directories import identity_name
from refresh_labs import DOM, every_node

BIOLOGY = 'biology_named_research_tab'
JACOBS = 'jacobs_named_research_before_capsule_bio'
TEMPLATES = {BIOLOGY, JACOBS}
SUBJECT_CONTINUITY = 'unchanged_original_resource_with_published_shorter_middle_initial_form'


def reviewed_subject(original_name, template, continuity=None):
    """A field-source observation is not a name correction or person merger.

    Permit one explicitly reviewed missing trailing middle initial on the
    unchanged original Biology resource. Full first, middle and family names
    must otherwise match. The initial remains unexpanded in the canonical name.
    """
    if continuity is None:
        return original_name
    displayed = continuity.get('nameAsDisplayed', '')
    original, published = identity_name(original_name).split(), identity_name(displayed).split()
    if (template != BIOLOGY or continuity != {'kind': SUBJECT_CONTINUITY, 'nameAsDisplayed': displayed}
            or len(published) < 3 or len(original) != len(published) + 1
            or len(original[-2]) != 1 or len(published[-2]) < 2
            or original[-2] != published[-2][0]
            or original[:-2] + original[-1:] != published):
        raise ValueError('Own field subject continuity requires the unchanged full published given/family names and one retained unexpanded middle initial')
    return displayed


def one(nodes, label):
    found = list(nodes)
    if len(found) != 1:
        raise ValueError('Own research requires one ' + label)
    return found[0]


def classes(node):
    return set(node.attrs.get('class', '').split())


def labelled_research(item, cache, name, template, phrases=None):
    capture, markup = captured_source(item, cache)
    visited = capture['requestedUrl']
    for hop in item['fetch'].get('redirects', []):
        if hop.get('from') != visited or hop.get('httpStatus') not in {301, 302, 303, 307, 308}:
            raise ValueError('Own research requires an actual continuous redirect chain')
        visited = hop.get('to')
    if visited != capture['sourceUrl'] or item['fetch'].get('httpStatus') != 200:
        raise ValueError('Own research requires the exact successful captured resource')
    requested, final = [urlsplit(capture[k]) for k in ['requestedUrl', 'sourceUrl']]
    dom = DOM(markup); nodes = list(dom.main().walk())
    title = one((n for n in every_node(dom.root) if n.tag == 'title'), 'document title').text()
    if template == BIOLOGY:
        if (any(p.hostname != 'biology.ucsd.edu' or p.query or p.fragment
                or not re.fullmatch(r'/research/faculty/[a-z0-9-]+', p.path) for p in [requested, final])
                or requested.path != final.path):
            raise ValueError('Biology research requires the unchanged own faculty resource')
        subject = one((n for n in nodes if n.tag == 'h1' and n.attrs.get('id') == 'facName'), 'Biology facName')
        if len([n for n in nodes if n.tag == 'h1']) != 1:
            raise ValueError('Biology research requires a single own subject')
        tab = one((n for n in nodes if n.tag == 'div' and n.attrs.get('id') == 'research'
                   and n.attrs.get('role') == 'tabpanel' and 'tab-pane' in classes(n)), 'own Research tab')
        children = [n for n in tab.children if hasattr(n, 'tag')]
        if (not children or children[0].tag != 'h2' or children[0].text() != 'Research'
                or any(n.tag in {'h1', 'h2', 'h3', 'h4', 'ul', 'ol', 'table', 'article'}
                       for child in children[1:] for n in every_node(child))):
            raise ValueError('Biology text must follow Research within its own tab, excluding other sections')
        paragraphs = [n.text() for n in children[1:] if n.tag == 'p' and n.text()]
        if not 1 <= len(paragraphs) <= 8:
            raise ValueError('Biology research requires its complete bounded direct published paragraphs')
        summary = ' '.join(paragraphs)
        if (not isinstance(phrases, list) or not 1 <= len(phrases) <= 10
                or len(phrases) != len(set(phrases))
                or any(not isinstance(term, str) or not 2 <= len(term) <= 160
                       or not re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', summary) for term in phrases)):
            raise ValueError('Reviewed research phrases must be complete literal terms in the own Research text')
        areas = phrases
        scope = {'tabId': 'research', 'tabRole': 'tabpanel', 'headingTag': 'h2', 'headingAsPublished': 'Research',
                 'paragraphSelection': 'complete_direct_nonempty_paragraphs', 'paragraphCount': len(paragraphs),
                 'researchAreaSelection': 'reviewer_selected_literal_own_research_phrases', 'literalPhrasesAsReviewed': phrases}
    elif template == JACOBS:
        if (any(p.hostname != 'jacobsschool.ucsd.edu' or p.path != '/faculty/profile'
                or not re.fullmatch(r'id=[0-9]+', p.query) or p.fragment for p in [requested, final])
                or requested.query != final.query or phrases is not None):
            raise ValueError('Jacobs research requires the unchanged original individual profile and literal focus')
        subject = one((n for n in nodes if n.tag == 'h3' and 'faculty_profile_name' in classes(n)), 'Jacobs own subject')
        qualification = jacobs_academic_qualification(item, cache, name)
        if qualification is None or 'col-9' not in classes(subject.parent):
            raise ValueError('Jacobs research requires the named own primary academic profile column')
        blocks = [n for n in subject.parent.children if hasattr(n, 'tag') and n.tag == 'div']
        bio_indexes = [i for i, n in enumerate(blocks) if any(c.tag == 'p' and c.text() == 'Capsule Bio:'
                       and 'font-weight-bold' in classes(c) for c in n.children if hasattr(c, 'tag'))]
        if (bio_indexes != [2] or classes(blocks[0]) != {'mt-5', 'font-weight-bold'}
                or classes(blocks[1]) != {'mb-5'} or classes(blocks[2]) != {'mb-5'}):
            raise ValueError('Jacobs focus and research must be the two direct blocks before Capsule Bio')
        focus, research = blocks[:2]
        if any(n.tag not in {'div', 'p', 'a', 'strong', 'em', 'b', 'i', 'br', 'span'}
               for block in [focus, research] for n in every_node(block)):
            raise ValueError('Jacobs research blocks must contain plain own text rather than lists or other subjects')
        summary = research.text(); focus_text = focus.text()
        if (not 8 <= len(focus_text) <= 160
                or not re.match(r"(?:Professor|Prof\.)\s+" + re.escape(subject.text().split()[-1])
                                + r"(?:’s|'s)\s+research\b", summary)):
            raise ValueError('Jacobs research must explicitly describe its own named subject, with a complete short focus')
        areas = [focus_text]
        scope = {'ownColumnClass': 'col-9', 'directResearchBlockIndex': 1, 'followingExcludedLabel': 'Capsule Bio:',
                 'focusAsPublished': focus_text, 'researchAreaSelection': 'complete_literal_own_focus_statement'}
    else:
        raise ValueError('Unsupported labelled own research template')
    if not same_named_subject(name, subject.text()) or not 90 <= len(summary) <= 5000:
        raise ValueError('Research must retain the full own subject and complete bounded published text')
    fields = {'researchSummary': summary, 'researchAreas': areas}
    common = {**capture, 'status': 'verified', 'method': 'named_own_profile_labelled_research_section',
              'evidenceType': 'main_text_quote', 'sourceTemplate': template,
              'nameAsDisplayed': subject.text(), **scope}
    evidence = {'researchSummary': [{**common, 'evidence': summary}],
                'researchAreas': [{**common, 'evidence': summary if template == BIOLOGY else areas[0]}]}
    return {'capture': capture, 'sourceTemplate': template, 'nameAsDisplayed': subject.text(),
            'documentTitle': title, 'sectionScope': scope, 'fields': fields, 'fieldEvidence': evidence,
            'scope': 'Complete own research section and literal focus/explicitly reviewed literal research phrases only. Career biography,publications,other people and navigation are excluded. No identity,primary,appointment,department,lab/PI,HR or legacy-date change.'}
