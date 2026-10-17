"""Verify a named faculty-source chain before consolidating published names.

Full given/family-name compatibility only rejects unrelated subjects. Identity
requires the original named roster links, two independently captured personal
identifiers and the target's own named academic profile. Initial-only records
and nickname/surname substitutions do not qualify through this workflow.
"""
from __future__ import annotations

import re
import urllib.parse

from collect_ucsd_coverage import profiles_appointment, safe_url
from faculty_profile_bindings import captured_source, profile_metadata, jacobs_academic_qualification
from faculty_resource_label_reviews import KIND as RESOURCE_KIND, verify_resource_label_review
from lab_identity_merges import verify_capture_proofs
from lab_resource_reviews import record_sha256
from refresh_faculty_directories import identity_name
from refresh_labs import DOM

KIND = 'explicit_named_roster_personal_identifier_chain'


def compatible_full_names(left, right):
    a, b = identity_name(left).split(), identity_name(right).split()
    if (min(len(a), len(b)) < 2 or min(len(a[0]), len(b[0]), len(a[-1]), len(b[-1])) < 2
            or a[0] != b[0] or a[-1] != b[-1]):
        return False
    return (not a[1:-1] or not b[1:-1]
            or len(a[1:-1]) == len(b[1:-1]) and all(
                x == y or min(len(x), len(y)) == 1 and x[0] == y[0]
                for x, y in zip(a[1:-1], b[1:-1])))


def named_faculty_table_link(person, item, cache):
    base, markup = captured_source(item, cache)
    if (base['requestedUrl'] not in person.get('sourceUrls', [])
            or not re.search(r'/faculty-directory\.html$', urllib.parse.urlsplit(base['sourceUrl']).path)):
        raise ValueError('The named table must be an exact retained faculty directory source')
    main = DOM(markup).main()
    headings = [n.text() for n in main.walk() if n.tag == 'h1']
    if headings != ['Department of ' + person['department'] + ' Faculty Directory']:
        raise ValueError('The named faculty directory must state its original department')
    matches = []
    for table in main.walk():
        if table.tag != 'table' or table.attrs.get('id') != 'datatable':
            continue
        for row in table.walk():
            if row.tag != 'tr':
                continue
            cells = [n for n in row.children if hasattr(n, 'tag') and n.tag == 'td']
            anchors = [n for n in row.walk() if n.tag == 'a' and n.attrs.get('href')]
            if len(cells) != 2 or len(anchors) != 1 or anchors[0] not in list(cells[0].walk()):
                continue
            anchor = anchors[0]; parts = [p.strip() for p in anchor.text().split(',')]
            if (len(parts) < 2 or any(re.sub(r'[^A-Za-z]', '', p).lower() not in {'md', 'phd', 'mph', 'ms', 'do'} for p in parts[2:])
                    or identity_name(parts[1] + ' ' + parts[0]) != identity_name(person['name'])
                    or cells[0].text() != anchor.text()
                    or safe_url(urllib.parse.urljoin(base['sourceUrl'], anchor.attrs['href'])) != person['officialProfileUrl']):
                continue
            matches.append({**base, 'nameAsDisplayed': anchor.text(), 'nameAsParsed': parts[1] + ' ' + parts[0],
                            'rawHref': anchor.attrs['href'], 'linkUrl': person['officialProfileUrl'],
                            'tableId': 'datatable', 'rowText': row.text(), 'divisionAsListed': cells[1].text()})
    if len(matches) != 1:
        raise ValueError('The source requires one complete original name and literal own-profile link in its primary faculty table cell')
    return matches[0]


def profile_chain_binding(source, target, request, reviews, people, queue, cache):
    if not compatible_full_names(source['name'], target['name']):
        raise ValueError('An initial, nickname, surname substitution or conflicting full middle name needs a different review')
    bridge_rows = [r for r in reviews if r.get('sourceProfessorId') == request.get('bridgeSourceProfessorId')
                   and r.get('identityBasis', {}).get('type') == RESOURCE_KIND and r.get('targetProfessorId') == target['id']]
    if len(bridge_rows) != 1:
        raise ValueError('The chain needs one separately reviewed named-card resource link to this same target')
    bridge = bridge_rows[0]; indexed = {p['id']: p for p in people}
    bridge_source = indexed.get(bridge['sourceProfessorId'])
    if (bridge_source is None or bridge.get('originalSourceRecord') != bridge_source
            or bridge.get('originalTargetRecord') != target
            or bridge.get('sourceRecordSha256') != record_sha256(bridge_source)
            or bridge.get('targetRecordSha256') != record_sha256(target)):
        raise ValueError('The chain bridge must retain both exact unchanged original records')
    verify_capture_proofs(bridge['evidence'], queue, cache, bridge_source['name'])
    verify_resource_label_review(bridge, bridge_source, target, people, queue, cache)
    items = {i['url']: i for i in queue['items'].values()}
    try:
        roster_item = items[request['sourceRosterRequestedUri']]
        own_item = items[source['officialProfileUrl']]
        target_item = items[target['officialProfileUrl']]
    except KeyError as error:
        raise ValueError('The complete source chain requires all actual original captures') from error
    roster = named_faculty_table_link(source, roster_item, cache)
    own, markup = profile_metadata(own_item, cache)
    assessment, appointment = profiles_appointment(own_item['fetch'], markup)
    bridge_own = bridge['resourceLabelBinding']['ownProfile']
    if (appointment is None or assessment.get('mappedDepartment') != source['department']
            or identity_name(own['nameAsDisplayed']) != identity_name(target['name'])
            or identity_name(bridge_own['nameAsDisplayed']) != identity_name(own['nameAsDisplayed'])
            or any(own[k] != bridge_own[k] for k in ['canonicalUri', 'rdfAlternateUri'])
            or own['requestedUrl'] == bridge_own['requestedUrl']):
        raise ValueError('Both literal own-profile captures must independently declare the same named personal identifiers and source appointment')
    qualification = jacobs_academic_qualification(target_item, cache, target['name'])
    if qualification is None:
        raise ValueError('The original target needs its own named primary academic profile capture')
    for uri, expected in [(source['officialProfileUrl'], source['id']), (target['officialProfileUrl'], target['id'])]:
        if [p['id'] for p in people if p.get('officialProfileUrl') == uri] != [expected]:
            raise ValueError('The chain has a competing original profile owner')
    return {'kind': KIND, 'bridgeSourceProfessorId': bridge_source['id'],
            'bridgeRoster': bridge['resourceLabelBinding']['roster'], 'bridgeOwnProfile': bridge_own,
            'sourceNamedRoster': roster, 'sourceOwnProfile': own,
            'sourceAppointment': appointment, 'targetOwnQualification': qualification,
            'publishedNames': [target['name'], source['name']],
            'scope': 'Consolidate separately published complete-name records through the verified named source chain and own personal identifiers; retain both published names and all old records. No legal-name-change, current-employment or catalog-initial expansion claim.'}


def verify_profile_chain_review(row, source, target, reviews, people, queue, cache):
    binding = profile_chain_binding(source, target, row.get('profileChainRequest', {}), reviews, people, queue, cache)
    if (row.get('profileChainBinding') != binding
            or row.get('identityBasis') != {'type': KIND, 'value': binding['sourceOwnProfile']['rdfAlternateUri']}):
        raise ValueError('The reviewed named profile chain changed')
    if row.get('fields') != {'department': target['department'], 'officialProfileUrl': target['officialProfileUrl']}:
        raise ValueError('The profile chain must preserve target preferred identity fields')
    previous = row.get('previousCandidateObservation')
    if previous is not None:
        old = previous.get('record', {})
        if (not re.fullmatch(r'[0-9a-f]{64}', previous.get('candidateAtlasSha256', ''))
                or previous.get('recordSha256') != record_sha256(old)
                or any(old.get(k) != source.get(k) for k in ['id', 'name', 'department', 'officialProfileUrl'])):
            raise ValueError('The previous source candidate must preserve its exact record hash and identity')
    proofs = row['evidence']
    uris = {binding['bridgeRoster']['requestedUrl'], binding['bridgeOwnProfile']['requestedUrl'],
            binding['sourceNamedRoster']['requestedUrl'], binding['sourceOwnProfile']['requestedUrl'],
            binding['targetOwnQualification']['evidence']['requestedUrl']}
    if len(uris) != 5 or {p['requestedUrl'] for p in proofs} != uris:
        raise ValueError('The chain needs evidence for all five distinct actual source captures')
    for field in row['fields']:
        if (not row.get('fieldEvidence', {}).get(field)
                or any(p not in proofs or p['requestedUrl'] not in {
                    binding['bridgeRoster']['requestedUrl'], binding['targetOwnQualification']['evidence']['requestedUrl']}
                       for p in row['fieldEvidence'][field])):
            raise ValueError('The unchanged preferred fields still require their own captured proof')
    departments = {target['department'], source['department']}
    if ({a.get('department') for a in row.get('departmentEvidence', [])} != departments
            or any(not a.get('fieldEvidence') or any(p not in proofs for p in a['fieldEvidence']) for a in row['departmentEvidence'])
            ):
        raise ValueError('Keep the two independently sourced departmental associations as listed')
    for affiliation in row['departmentEvidence']:
        allowed = ({binding['sourceOwnProfile']['requestedUrl']} if affiliation['department'] == source['department']
                   else {binding['bridgeRoster']['requestedUrl'], binding['targetOwnQualification']['evidence']['requestedUrl']})
        if any(p['requestedUrl'] not in allowed for p in affiliation['fieldEvidence']):
            raise ValueError('Each departmental association must use its own separately captured appointment source')
    held = row.get('unsupportedDepartmentValues', [])
    prior = row.get('previousCandidateObservation', {}).get('record', {})
    if (set(held) - {'Unknown', 'Interdisciplinary'} or set(held) & departments
            or set(held) & set(target.get('departmentAffiliations', []))
            or set(held) - set(prior.get('departmentAffiliations', []))):
        raise ValueError('Only explicitly reviewed inherited source-context placeholders may be held')
    for value in held:
        if (prior.get('fieldEvidence', {}).get('departmentAffiliations')
                or any(a.get('department') == value for a in prior.get('departmentAffiliationEvidence', []) or [])):
            raise ValueError('Independently evidenced department associations need their own review')
        listings = [r for r in prior.get('directoryListings', []) if r.get('department') == value]
        if not listings or any(r.get('departmentAsListed') or r.get('departmentExplicitlyListed') for r in listings):
            raise ValueError('A held placeholder needs its actual unqualified source-context listing')
        for listing in listings:
            observations = [h for h in listing.get('sourceListingSelectionHistory', [])
                            if h.get('selected', {}).get('department') == 'Unknown']
            matched = False
            for item in queue['items'].values():
                meta = item.get('fetch', {})
                if (meta.get('finalUrl'), meta.get('observedAt')) != (listing['sourceUrl'], listing['observedAt']):
                    continue
                base, _ = captured_source(item, cache)
                matched = any(h.get('bodySha256') == base['bodySha256']
                              and h['selected'].get('namedLinkUrl') == source['officialProfileUrl']
                              for h in observations)
                if matched:
                    break
            if not matched:
                raise ValueError('The context hold needs its exact dated raw capture and recorded unmapped source row')
