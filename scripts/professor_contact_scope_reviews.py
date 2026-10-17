"""Review what a published contact identifies, separately from page ownership.

A named card can display a correct address behind another person's mailto.
A profile contact can repeat the site's Feedback mailbox. Retain those exact
observations without treating the link target as personal identity evidence.
"""
from __future__ import annotations

import copy
import re
from urllib.parse import unquote, urljoin, urlsplit

from faculty_profile_bindings import captured_source, profile_metadata
from faculty_scoped_titles import same_named_subject
from lab_resource_reviews import record_sha256
from refresh_faculty_directories import public_email, valid_person_name
from refresh_labs import DOM, every_node


IDENTITY = ('id', 'name', 'department', 'officialProfileUrl')
MISSING = 'Not found'


def email_proofs(person):
    value = person.get('fieldEvidence', {}).get('email', [])
    return [value] if isinstance(value, dict) else value


def _source(item, cache):
    capture, markup = captured_source(item, cache)
    visited = item['url']
    for hop in item['fetch'].get('redirects', []):
        if hop.get('from') != visited or hop.get('httpStatus') not in {301, 302, 303, 307, 308}:
            raise ValueError('Contact review requires the actual continuous redirect chain')
        visited = hop.get('to')
    if item['fetch'].get('httpStatus') != 200 or visited != capture['sourceUrl']:
        raise ValueError('Contact review requires its exact successful official capture')
    return capture, DOM(markup)


def directory_email_scope(item, cache, person, own_item=None):
    capture, dom = _source(item, cache)
    matches = []
    for card in dom.main().walk():
        if card.tag != 'li' or 'profile-listing-card' not in card.attrs.get('class', '').split():
            continue
        data = [n for n in card.walk() if 'profile-listing-data' in n.attrs.get('class', '').split()]
        if len(data) != 1:
            continue
        headings = [n for n in data[0].walk() if n.tag == 'h3' or n.tag == 'p' and 'h3' in n.attrs.get('class', '').split()]
        if len(headings) != 1 or not same_named_subject(person['name'], headings[0].text()):
            continue
        heading = headings[0]
        emails = [n for n in data[0].walk() if n.tag == 'a' and n.attrs.get('href', '').startswith('mailto:')]
        if len(emails) != 1 or not public_email(emails[0].text()):
            raise ValueError('One named card must display exactly one literal email')
        email = emails[0]; href = email.attrs['href']; raw = href[7:].split('?', 1)[0].split('#', 1)[0]
        displayed = email.text()
        if raw == displayed or not public_email(raw):
            raise ValueError('This review requires the actual mismatched old mailto value')
        links = [n for n in heading.walk() if n.tag == 'a' and n.attrs.get('href')]
        if len(links) == 1 and urljoin(capture['sourceUrl'], links[0].attrs['href']) == person['officialProfileUrl']:
            identity = {'kind': 'literal_retained_primary_in_named_card', 'rawHref': links[0].attrs['href'],
                        'profileUrl': person['officialProfileUrl']}
        else:
            if own_item is None or own_item['url'] != person['officialProfileUrl']:
                raise ValueError('A card without the retained primary link needs its separately captured own subject')
            own, _ = profile_metadata(own_item, cache)
            if (own['sourceUrl'] != person['officialProfileUrl'] or own['canonicalUri'] != person['officialProfileUrl']
                    or not same_named_subject(person['name'], own['nameAsDisplayed'])):
                raise ValueError('The retained personal primary must independently name the unchanged person')
            identity = {'kind': 'independent_retained_profiles_subject', 'ownProfile': own}
        matches.append({'capture': capture, 'kind': 'named_directory_card_displayed_email',
                        'nameAsDisplayed': heading.text(), 'headingTag': heading.tag,
                        'headingClass': heading.attrs.get('class', ''), 'cardText': card.text(),
                        'emailAsDisplayed': displayed, 'rawMailtoHref': href, 'oldParsedMailtoValue': raw,
                        'decodedMailtoValue': unquote(raw).strip(),
                        'conflictKind': 'encoded_whitespace_in_mailto' if unquote(raw).strip() == displayed else 'display_href_conflict',
                        'sourceIdentity': identity})
    if len(matches) != 1:
        raise ValueError('Contact review requires one scoped named directory card')
    return matches[0]


def site_feedback_scope(item, cache):
    capture, dom = _source(item, cache)
    if capture['sourceUrl'] != 'https://literature.ucsd.edu/people/contact.html':
        raise ValueError('The shared mailbox requires the reviewed official Literature Contact resource')
    headings = [n.text() for n in dom.main().walk() if n.tag == 'h1']
    if headings != ['Contact'] or 'Literature Department' not in dom.main().text() or 'Mailing Address' not in dom.main().text():
        raise ValueError('The contact resource must independently declare its department context')
    links = []
    for node in every_node(dom.root):
        if node.tag != 'a' or node.text() != 'Feedback' or not node.attrs.get('href', '').startswith('mailto:'):
            continue
        ancestors = []; parent = node.parent
        while parent is not None:
            ancestors.append(parent); parent = parent.parent
        if (not any(n.tag == 'footer' for n in ancestors)
                or not any(n.tag == 'ul' and 'footer-links' in n.attrs.get('class', '').split() for n in ancestors)):
            continue
        address = public_email(node.attrs['href'])
        if address:
            links.append({'capture': capture, 'kind': 'shared_site_feedback_contact', 'department': 'Literature',
                          'roleAsPublished': 'Feedback', 'email': address, 'rawMailtoHref': node.attrs['href'],
                          'documentHeading': 'Contact', 'departmentContext': dom.main().text()})
    if len(links) != 1:
        raise ValueError('The department site must publish one explicitly labelled footer Feedback mailbox')
    return links[0]


def contact_payload(row):
    scope = row['sourceScope']
    if row['disposition'] == 'correct_published_directory_email':
        if scope['kind'] != 'named_directory_card_displayed_email' or row['previousEmail'] != scope['oldParsedMailtoValue']:
            raise ValueError('Only the exact observed mailto parsing conflict can be corrected')
        proof = {**scope['capture'], 'status': 'verified', 'method': 'reviewed_named_directory_displayed_email',
                 'evidenceType': 'main_text_quote', 'evidence': scope['cardText'],
                 **{key: scope[key] for key in ['nameAsDisplayed', 'emailAsDisplayed', 'rawMailtoHref', 'conflictKind']}}
        return scope['emailAsDisplayed'], [proof]
    if (row['disposition'] != 'hold_shared_site_feedback_as_personal_email'
            or scope['kind'] != 'shared_site_feedback_contact' or row['previousEmail'] != scope['email']):
        raise ValueError('A shared-site contact hold cannot assert another personal email')
    return MISSING, []


def verified_contact_scopes(review, queue, cache, people):
    items = {item['url']: item for item in queue['items'].values()}; rows = []; seen = set()
    for raw in review.get('entries', []):
        row = copy.deepcopy(raw); pid = row.get('professorId'); person = people.get(pid)
        scope = row.get('sourceScope', {}); item = items.get(scope.get('capture', {}).get('requestedUrl'))
        previous = {'email': row.get('previousEmail'), 'fieldEvidence': row.get('previousEmailEvidence')}
        if (person is None or pid in seen or not valid_person_name(person['name']) or not row.get('reason')
                or row.get('originalPersonIdentity') != {key: person.get(key) for key in IDENTITY}
                or not re.fullmatch(r'[0-9a-f]{64}', row.get('sourceCandidateAtlasSha256', ''))
                or not isinstance(row.get('previousEmailEvidence'), list)
                or row.get('previousEmailSha256') != record_sha256(previous) or item is None
                or any(row.get('retainedCanonicalIdentity', {}).get(key) != person.get(key) for key in ['id', 'name'])):
            raise ValueError('Contact review requires its unchanged original person and exact preceding email observation')
        retained = row['retainedCanonicalIdentity']
        if scope.get('kind') == 'named_directory_card_displayed_email':
            own = scope.get('sourceIdentity', {}).get('ownProfile', {})
            actual = directory_email_scope(item, cache, retained, items.get(own.get('requestedUrl')))
            primary_owners = {p['id'] for p in people.values() if p.get('officialProfileUrl') == retained['officialProfileUrl']}
            named_owners = {p['id'] for p in people.values() if valid_person_name(p['name'])
                            and same_named_subject(p['name'], retained['name'])}
            if (not any(p.get('sourceUrl') == actual['capture']['sourceUrl'] for p in row['previousEmailEvidence'])
                    or primary_owners - {pid} or named_owners != {pid}):
                raise ValueError('The displayed contact requires its prior named source proof and uncontested retained primary')
        else:
            actual = site_feedback_scope(item, cache)
            if (retained.get('department') != 'Literature' or person['department'] != 'Literature'
                    or urlsplit(retained.get('officialProfileUrl', '')).hostname != 'literature.ucsd.edu'
                    or not row['previousEmailEvidence'] or any(p.get('method') != 'identity_matched_profile_unique_contact'
                        or urlsplit(p.get('sourceUrl', '')).hostname != 'literature.ucsd.edu' for p in row['previousEmailEvidence'])):
                raise ValueError('A generic Feedback review cannot supersede independently verified personal contact evidence')
        if actual != scope or (row.get('email'), row.get('fieldEvidence')) != contact_payload(row):
            raise ValueError('Contact fields must equal their exact recomputed published scope')
        row['captureVerified'] = True; row['contactScopeReviewed'] = True; rows.append(row); seen.add(pid)
    return rows


def preserves_reviewed_contact(person, row):
    return (row in person.get('professorContactScopeReviews', []) and person.get('email') == row['email']
            and email_proofs(person) == row['fieldEvidence'])


def apply_contact_scopes(data, reviews):
    people = {person['id']: person for person in data['professors']}
    if len({row.get('professorId') for row in reviews}) != len(reviews):
        raise ValueError('Only one contact scope decision may apply to a retained person')
    for row in reviews:
        person = people.get(row.get('professorId'))
        if (person is None or not row.get('captureVerified') or not row.get('contactScopeReviewed')
                or row['retainedCanonicalIdentity'] != {key: person.get(key) for key in IDENTITY}
                or row.get('previousEmailSha256') != record_sha256({'email': row['previousEmail'], 'fieldEvidence': row['previousEmailEvidence']})
                or (row['email'], row['fieldEvidence']) != contact_payload(row)):
            raise ValueError('Only an exact verified contact decision may reach its unchanged canonical person')
        if preserves_reviewed_contact(person, row):
            continue
        if person.get('email') != row['previousEmail'] or email_proofs(person) != row['previousEmailEvidence']:
            raise ValueError('Contact scope cannot replace newer or independently changed email evidence')
    for row in reviews:
        person = people[row['professorId']]
        if preserves_reviewed_contact(person, row):
            continue
        history = {'field': 'email', 'value': person['email'], 'fieldEvidence': copy.deepcopy(email_proofs(person)),
                   'sourceCandidateAtlasSha256': row['sourceCandidateAtlasSha256'], 'contactScopeReview': True,
                   'reason': row['reason']}
        if history not in person.setdefault('previousFieldObservations', []):
            person['previousFieldObservations'].append(history)
        person['email'] = row['email']; person.setdefault('fieldEvidence', {}).pop('email', None)
        if row['fieldEvidence']:
            person['fieldEvidence']['email'] = copy.deepcopy(row['fieldEvidence'])
        if row['sourceScope']['kind'] == 'shared_site_feedback_contact':
            person.setdefault('sharedSiteContactObservations', []).append(copy.deepcopy(row['sourceScope']))
        person.setdefault('professorContactScopeReviews', []).append(copy.deepcopy(row))
        person['sourceUrls'] = list(dict.fromkeys(person.get('sourceUrls', []) + [row['sourceScope']['capture'][key] for key in ['requestedUrl', 'sourceUrl']]))
        person['unverifiedFields'] = [field for field in person.get('unverifiedFields', []) if field != 'email']
        verification = person.setdefault('verification', {})
        verification['fieldsVerified'] = sorted(field for field in person['fieldEvidence'] if field != 'profileLinkIdentityReview')
        dates = [p['observedAt'] for values in person['fieldEvidence'].values()
                 for p in (values if isinstance(values, list) else [values]) if p.get('observedAt')]
        if dates:
            verification['lastEvidenceAt'] = max(dates)
        else:
            verification.pop('lastEvidenceAt', None)
            if verification.get('status') == 'source_checked':
                verification['status'] = 'needs_review' if person.get('unresolvedLabLinks') else 'legacy_unverified'
