"""Own research statements and explicit corrections of publication scope.

These reviews concern existing individual profiles only. An explicit research
portfolio enumeration can supply its literal terms, without a topic mapping.
They establish no faculty qualification, appointment or person identity binding.
"""
import copy
import hashlib
import re
from pathlib import Path
from urllib.parse import urlsplit

from faculty_profile_bindings import captured_source
from faculty_scoped_titles import same_named_subject
from lab_identity_merges import verify_capture_proofs
from refresh_labs import DOM, every_node, evidence_items, merge_observed_fields, observation_time, unique_values


def gps_own_research_summary(item, cache, name, statement):
    base, markup = captured_source(item, cache)
    for uri in [base['requestedUrl'], base['sourceUrl']]:
        parsed = urlsplit(uri)
        if (parsed.hostname != 'gps.ucsd.edu' or not re.fullmatch(r'/faculty-directory/[a-z0-9-]+\.html', parsed.path)
                or parsed.query or parsed.fragment):
            raise ValueError('Biography summary requires the exact original individual GPS profile')
    visited = item['url']
    for hop in item['fetch'].get('redirects', []):
        if hop.get('from') != visited or hop.get('httpStatus') not in {301, 302, 303, 307, 308}:
            raise ValueError('Biography summary requires its actual continuous redirect chain')
        visited = hop.get('to')
    if visited != base['sourceUrl']:
        raise ValueError('Biography summary requires its actual continuous redirect chain')
    dom = DOM(markup)
    titles = [n.text() for n in every_node(dom.root) if n.tag == 'title']
    subjects = [n.text() for n in every_node(dom.main()) if n.tag == 'h1']
    if (len(titles) != 1 or len(subjects) != 1
            or not same_named_subject(name, subjects[0]) or not same_named_subject(subjects[0], titles[0])):
        raise ValueError('GPS biography requires one unchanged complete subject in its title and H1')
    tabs = [n for n in every_node(dom.main()) if n.tag == 'article' and n.attrs.get('id') == 'profileTab'
            and n.attrs.get('aria-label') == 'Profile Tabs']
    if len(tabs) != 1:
        raise ValueError('GPS biography requires its explicit named Profile tab')
    labels = [n for n in every_node(tabs[0]) if n.tag == 'li' and n.attrs.get('role') == 'tab'
              and n.attrs.get('id') == 'tab_item-0' and n.text() == 'Profile']
    panels = [n for n in every_node(tabs[0]) if n.tag == 'div' and n.attrs.get('aria-labelledby') == 'tab_item-0'
              and 'resp-tab-content' in n.attrs.get('class', '').split()]
    if len(labels) != 1 or len(panels) != 1:
        raise ValueError('GPS biography requires one Profile tab panel')
    paragraphs = []
    for node in panels[0].children:
        if not hasattr(node, 'tag'):
            continue
        if node.tag in {'h1', 'h2', 'h3'}:
            break  # Education, spotlight, publications and news are not the biography.
        if node.tag == 'p' and node.text():
            paragraphs.append(node.text())
    if not paragraphs or not paragraphs[0].startswith(subjects[0] + ' is '):
        raise ValueError('GPS biography must introduce its own named subject')
    matches = [p for p in paragraphs if isinstance(statement, str) and statement and statement in p]
    if (len(matches) != 1 or len(statement) > 1500 or not statement.endswith('.')
            or not re.search(r'\bresearch\b', statement, re.I)
            or re.search(r'\b(?:professor|appointed|appointment|co-founder|director|previously|prior to|served as)\b', statement, re.I)):
        raise ValueError('GPS summary requires an exact research statement inside the own biography')
    paragraph = matches[0]
    surname = subjects[0].split()[-1]
    own_names = re.escape(subjects[0]) + '|' + re.escape(surname)
    if (not re.match(r'(?:' + own_names + r')(?=[ ’\'])', paragraph)
            or not re.match(r'(?:(?:' + own_names + r')[’\']s (?:current )?research\b|'
                            r'(?:His|Her|Their) (?:current )?research\b)', statement)):
        raise ValueError('GPS research statement and paragraph must remain scoped to the named subject')
    start = paragraph.index(statement)
    end = start + len(statement)
    if (start and not re.search(r'\.\s+$', paragraph[:start])
            or end < len(paragraph) and not paragraph[end:].startswith(' ')):
        raise ValueError('GPS summary must preserve complete sentence boundaries')
    proof = {**base, 'method': 'reviewed_named_gps_biography_research_statement', 'evidenceType': 'main_text_quote',
             'evidence': statement, 'status': 'verified', 'subjectTemplate': 'gps_profile_tabs_biography',
             'nameAsDisplayed': subjects[0], 'articleId': 'profileTab', 'tabLabel': 'Profile', 'paragraphText': paragraph}
    fields, field_proofs = {'researchSummary': statement}, {'researchSummary': [proof]}
    enumeration = re.fullmatch(r'(?:' + own_names + r')[’\']s research portfolio spans the fields of (.+)\.', statement)
    if enumeration and enumeration[1].count(' and ') == 1 and enumeration[1].count(', ') >= 2:
        terms = enumeration[1].replace(' and ', ', ').split(', ')
        if (2 <= len(terms) <= 10 and len(set(terms)) == len(terms)
                and all(re.fullmatch(r'[A-Za-z][A-Za-z -]{1,100}', t) for t in terms)):
            fields['researchAreas'] = terms
            field_proofs['researchAreas'] = [{**proof, 'method': 'reviewed_named_gps_explicit_research_portfolio_fields',
                                             'valuesAsListed': terms}]
    return {'capture': base, 'nameAsDisplayed': subjects[0], 'sourceTemplate': 'gps_profile_tabs_biography',
            'fields': fields, 'fieldEvidence': field_proofs,
            'scope': 'Exact own biography research statement and unambiguous literal portfolio terms only; no name, qualification, affiliation, appointment or leadership inference.'}


def verified_previous_paper_scope(scope, person, queue, cache):
    """Prove the retained old excerpt is a single paper on the known own site."""
    scope = copy.deepcopy(scope)
    proofs = scope.get('evidence', [])
    verify_capture_proofs(proofs, queue, cache, person['id'])
    items = {i['url']: i for i in queue['items'].values()}
    identity, link, paper = [scope.get(k, {}) for k in ['publisherIdentityEvidence', 'publishedPersonalLinkEvidence', 'paperScopeEvidence']]
    uri = person.get('personalWebsiteUrl')
    item = items.get(uri, {})
    meta = item.get('fetch', {})
    old = person.get('researchSummary')
    old_proofs = evidence_items(person.get('fieldEvidence', {}).get('researchSummary'))
    if (scope.get('kind') != 'single_paper_abstract' or not scope.get('paperTitle')
            or any(p not in proofs for p in [identity, link, paper])
            or identity.get('requestedUrl') != uri or identity.get('evidenceType') != 'document_title'
            or identity.get('evidence') != person['name'] or identity.get('bodySha256') != meta.get('sha256')
            or link.get('requestedUrl') != person['officialProfileUrl'] or link.get('linkUrl') != uri
            or link.get('evidenceType') != 'named_link' or paper.get('requestedUrl') != uri
            or paper.get('evidenceType') != 'main_text_quote' or not old or old not in paper.get('evidence', '')
            or not old_proofs or any(p.get('sourceUrl') != uri or p.get('evidence') != old
                                    or 'personal_site' not in p.get('method', '') for p in old_proofs)):
        raise ValueError('Paper scope correction requires the original excerpt and exact named published personal resource')
    file = Path(cache) / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
    visited = uri
    for hop in meta.get('redirects', []):
        if hop.get('from') != visited or hop.get('httpStatus') not in {301, 302, 303, 307, 308}:
            raise ValueError('Paper scope requires the actual continuous personal-source redirect chain')
        visited = hop.get('to')
    if visited != meta.get('finalUrl'):
        raise ValueError('Paper scope requires the actual continuous personal-source redirect chain')
    dom = DOM(file.read_text())
    groups = [n for n in every_node(dom.main()) if 's-item-text-group' in n.attrs.get('class', '').split()
              and n.text() == paper['evidence']]
    if (len(groups) != 1
            or len([n for n in every_node(groups[0]) if 's-item-title' in n.attrs.get('class', '').split()
                    and n.text() == scope['paperTitle']]) != 1
            or len([n for n in every_node(groups[0]) if n.tag == 'p' and n.text() == old]) != 1):
        raise ValueError('Paper excerpt must belong to its one specifically titled publication card')
    scope['captureVerified'] = True
    return scope


def apply_biography_summary(person, row):
    proofs = row['fieldEvidence']['researchSummary']
    old_proofs = evidence_items(person.get('fieldEvidence', {}).get('researchSummary'))
    if not any('personal_site' in p.get('method', '') for p in old_proofs):
        return merge_observed_fields(person, {**row['fields'], 'fieldEvidence': row['fieldEvidence']})
    other_fields = {k: v for k, v in row['fields'].items() if k != 'researchSummary'}
    other_proofs = {k: v for k, v in row['fieldEvidence'].items() if k in other_fields}
    updated = merge_observed_fields(person, {**other_fields, 'fieldEvidence': other_proofs})
    # The generic backfill rule still protects personal-site summaries. Only an
    # explicit reviewed scope error in this exact original value can override it.
    if (row.get('previousSummaryScopeReview', {}).get('captureVerified')
            and person.get('researchSummary') == row['originalSourceProfessorRecord'].get('researchSummary')
            and observation_time(proofs) >= observation_time(old_proofs)):
        observation = {'field': 'researchSummary', 'value': person['researchSummary'],
                       'fieldEvidence': copy.deepcopy(old_proofs), 'reason': row['reason']}
        updated['previousFieldObservations'] = unique_values(updated.get('previousFieldObservations', []) + [observation])
        updated['researchSummary'] = row['fields']['researchSummary']
        updated.setdefault('fieldEvidence', {})['researchSummary'] = copy.deepcopy(proofs)
    return updated
