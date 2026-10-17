"""Resolve a retained research-link label using its original named faculty card.

This is a parser-artifact review, not a name-similarity person merge. The old
record and ID survive; the target's name, primary URI and department stay put.
"""
from __future__ import annotations

import re
import urllib.parse

from faculty_profile_bindings import captured_source, profile_metadata
from refresh_faculty_directories import identity_name, valid_person_name, individual_profile
from refresh_labs import DOM
from collect_ucsd_coverage import academic_title_clause, safe_url
from lab_resource_reviews import record_sha256


KIND = 'misparsed_research_link_in_named_faculty_card'


def resource_label_binding(source, target, roster_item, profile_item, cache, people):
    """Re-read both exact captures and the primary/secondary DOM relationship."""
    if (valid_person_name(source['name']) or not valid_person_name(target['name'])
            or not re.fullmatch(re.escape(target['name'].split()[-1]) + r' Research', source['name'])
            or source['department'] != target['department']):
        raise ValueError('A resource-label review requires a malformed research label and an unchanged named target')
    target_host = urllib.parse.urlsplit(target['officialProfileUrl']).hostname or ''
    if (not individual_profile(target['officialProfileUrl'])
            or not (target_host == 'ucsd.edu' or target_host.endswith('.ucsd.edu'))):
        raise ValueError('The target must retain its individual official campus profile')
    base, markup = captured_source(roster_item, cache)
    parsed = urllib.parse.urlsplit(base['sourceUrl'])
    if (parsed.hostname == 'profiles.ucsd.edu' or not re.search(r'/faculty(?:/|$|[-_.])', parsed.path)
            or any(base['requestedUrl'] not in person.get('sourceUrls', []) for person in [source, target])):
        raise ValueError('The exact retained roster source must belong to both original records')
    if profile_item['url'] != source['officialProfileUrl']:
        raise ValueError('The own capture must request the original malformed record URI exactly')
    own, _ = profile_metadata(profile_item, cache)
    if identity_name(own['nameAsDisplayed']) != identity_name(target['name']):
        raise ValueError('The linked own profile must name the target as its subject')
    cards = []
    for card in DOM(markup).main().walk():
        if card.tag != 'div' or 'faculty-profile' not in card.attrs.get('class', '').split():
            continue
        headings = [n for n in card.walk() if n.tag in {'h1', 'h2', 'h3', 'h4'}]
        if len(headings) != 1 or headings[0].tag != 'h3' or headings[0].text() != target['name']:
            continue
        heading = headings[0]
        primary = [n for n in heading.walk() if n.tag == 'a' and n.attrs.get('href')]
        secondary = [n for n in card.walk() if n.tag == 'a' and n.attrs.get('href')
                     and n.text() == source['name'] and n not in primary]
        roles = [n for n in card.walk() if n.tag == 'h6' and academic_title_clause(n.text())]
        if len(primary) != 1 or len(secondary) != 1 or len(roles) != 1:
            continue
        name_link, research_link = primary[0], secondary[0]
        if (name_link.text() != target['name']
                or safe_url(urllib.parse.urljoin(base['sourceUrl'], name_link.attrs['href'])) != target['officialProfileUrl']
                or safe_url(urllib.parse.urljoin(base['sourceUrl'], research_link.attrs['href'])) != source['officialProfileUrl']
                or research_link.parent is None or research_link.parent.tag != 'h6'):
            continue
        cards.append({**base, 'cardTag': card.tag, 'cardClass': card.attrs.get('class', ''),
                      'headingTag': heading.tag, 'nameAsDisplayed': heading.text(), 'cardText': card.text(),
                      'roleAsListed': roles[0].text(), 'primaryRawHref': name_link.attrs['href'],
                      'secondaryLabel': research_link.text(), 'secondaryRawHref': research_link.attrs['href']})
    if len(cards) != 1:
        raise ValueError('A resource-label review requires one primary name and secondary research link in the same faculty card')
    owners = [p['id'] for p in people if p.get('officialProfileUrl') == target['officialProfileUrl']]
    if owners != [target['id']]:
        raise ValueError('The named primary card link has a competing original owner')
    return {'kind': KIND, 'roster': cards[0], 'ownProfile': own,
            'scope': 'Correct a secondary research-link label parsed as a person; preserve both original records and all old observations. No legal-name-change, current-employment or catalog-initial expansion claim.'}


def verify_resource_label_review(row, source, target, people, queue, cache):
    items = {item['url']: item for item in queue['items'].values()}
    binding = row.get('resourceLabelBinding', {})
    try:
        roster = items[binding['roster']['requestedUrl']]
        own = items[binding['ownProfile']['requestedUrl']]
    except (KeyError, TypeError) as error:
        raise ValueError('A resource-label review requires its two actual captures') from error
    verified = resource_label_binding(source, target, roster, own, cache, people)
    if binding != verified or row.get('identityBasis') != {'type': KIND, 'value': source['officialProfileUrl']}:
        raise ValueError('The reviewed resource-label binding changed')
    previous = row.get('previousCandidateObservation')
    if previous is not None:
        old = previous.get('record', {})
        if (not re.fullmatch(r'[0-9a-f]{64}', previous.get('candidateAtlasSha256', ''))
                or previous.get('recordSha256') != record_sha256(old)
                or any(old.get(k) != source.get(k) for k in ['id', 'name', 'department', 'officialProfileUrl'])):
            raise ValueError('A previous malformed candidate snapshot must retain its exact record hash and original identity fields')
    # This disposition does not choose a new scalar value or reclassify a unit.
    fields = {'department': target['department'], 'officialProfileUrl': target['officialProfileUrl']}
    if row.get('fields') != fields or row.get('unsupportedDepartmentValues'):
        raise ValueError('A resource-label review must preserve target identity fields')
    proofs = row.get('evidence', [])
    card_proofs = [p for p in proofs if p.get('requestedUrl') == verified['roster']['requestedUrl']]
    for label, uri in [(target['name'], target['officialProfileUrl']), (source['name'], source['officialProfileUrl'])]:
        if not any(p.get('evidenceType') == 'named_link' and p.get('linkText') == label and p.get('linkUrl') == uri for p in card_proofs):
            raise ValueError('Both card links need their exact dated evidence')
    if not any(p.get('requestedUrl') == verified['ownProfile']['requestedUrl'] for p in proofs):
        raise ValueError('The own named profile needs its dated evidence')
    if (set(row.get('fieldEvidence', {})) != set(fields)
            or any(not row['fieldEvidence'][f] or any(p not in card_proofs for p in row['fieldEvidence'][f]) for f in fields)
            or row.get('departmentEvidence') != [{'department': target['department'],
                                                   'fieldEvidence': row['fieldEvidence']['department'], 'status': 'as_listed'}]):
        raise ValueError('Target fields require the explicit retained faculty-card proof')
