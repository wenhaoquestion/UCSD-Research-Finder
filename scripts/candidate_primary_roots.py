"""Retain a previously qualified candidate's actual primary across cohorts.

An incoming same-name source cannot replace that identity merely by appearing
earlier in a later source array. A reviewed root must still be independently
qualified in the current admission input and literally published by its named
roster. This ordering decision does not bind the alternative person resource.
"""
from __future__ import annotations

import copy
import re

from collect_ucsd_coverage import academic_title_clause
from faculty_profile_bindings import captured_source
from lab_identity_merges import verify_capture_proofs
from lab_resource_reviews import record_sha256
from refresh_faculty_directories import identity_name, individual_profile
from refresh_labs import DOM, links, normalized


def source_key(row):
    return [row.get('sourceUrl'), row.get('observedAt'), identity_name(row.get('name', '')),
            row.get('department'), row.get('listedRole')]


def root_observation(record, row, items, cache):
    primary = record.get('officialProfileUrl')
    expected_id = row.get('discoveryId') or 'ucsd-faculty-live-' + normalized(row.get('name', '')).replace(' ', '-')
    accepted = [r for r in record.get('directoryListings', []) if source_key(r) == source_key(row)
                and r.get('namedLinkUrl') == primary]
    name = identity_name(record.get('name', '')).split()
    if (record.get('id') != expected_id or len(name) < 2 or any(len(t) < 2 for t in [name[0], name[-1]])
            or identity_name(row.get('name', '')) != identity_name(record.get('name', ''))
            or record.get('department') != row.get('department') or len(accepted) != 1
            or row.get('profileUrl') != primary or row.get('namedLinkUrl') != primary
            or not individual_profile(primary) or not academic_title_clause(row.get('listedRole', ''))):
        raise ValueError('A retained candidate root must be the same still-qualified complete subject and primary')
    source_item, own_item = items.get(row.get('sourceUrl')), items.get(primary)
    if source_item is None or own_item is None:
        raise ValueError('Retained candidate root requires both actual successful source captures')
    source, markup = captured_source(source_item, cache)
    own, own_markup = captured_source(own_item, cache)
    if (source['sourceUrl'] != row['sourceUrl'] or source['observedAt'] != row['observedAt']
            or own['sourceUrl'] != primary or own_item['fetch'].get('httpStatus') != 200):
        raise ValueError('Retained root must keep the exact dated roster and direct individual resource')
    headings = [n.text() for n in DOM(own_markup).main().walk() if n.tag == 'h1']
    if len(headings) != 1 or identity_name(headings[0]) != identity_name(record['name']):
        raise ValueError('The retained primary must name its exact accepted complete subject')
    literal = [(label, uri) for node, label, uri in links(DOM(markup).main(), source['sourceUrl'])
               if uri == primary and identity_name(label) == identity_name(record['name'])]
    quote = row.get('evidence', {}).get('evidence')
    if len(literal) != 1 or not quote or quote not in DOM(markup).main().text():
        raise ValueError('Retained root requires its literal named roster link and original academic card quote')
    common = {'status': 'verified', 'method': 'reviewed_previously_qualified_candidate_primary'}
    proofs = [{**source, **common, 'evidenceType': 'main_text_quote', 'evidence': quote},
              {**source, **common, 'evidenceType': 'named_link', 'linkText': literal[0][0],
               'linkUrl': primary, 'evidence': literal[0][0] + ' -> ' + primary},
              {**own, **common, 'evidenceType': 'document_heading', 'headingTag': 'h1', 'evidence': headings[0]}]
    return {'primaryProfileUri': primary, 'sourceObservationKey': source_key(row),
            'qualifiedSourceListingAsPreviouslyAccepted': copy.deepcopy(accepted[0]),
            'ownPrimaryCapture': own, 'rosterCapture': source, 'evidence': proofs,
            'scope': 'Previously accepted primary ordering only; no alternative-source binding, identity merge, name expansion, new appointment or new faculty qualification.'}


def reviewed_primary_roots(review, records, professors, queue, cache):
    items = {i['url']: i for i in queue['items'].values()}
    existing_ids = {p['id'] for p in professors}
    existing_uris = {p.get('officialProfileUrl') for p in professors}
    seen, primary_uris, keys, verified = set(), set(), set(), []
    for raw in review.get('entries', []):
        entry = copy.deepcopy(raw)
        original = entry.get('originalProfessorRecord', {})
        pid = entry.get('professorId')
        if (pid != original.get('id') or pid in seen or pid in existing_ids
                or original.get('officialProfileUrl') in primary_uris
                or original.get('officialProfileUrl') in existing_uris or not entry.get('reason')
                or entry.get('action') != 'retain_previously_qualified_primary'
                or entry.get('originalProfessorRecordSha256') != record_sha256(original)
                or not re.fullmatch(r'[a-f0-9]{64}', entry.get('sourceCandidateAtlasSha256', ''))):
            raise ValueError('A candidate primary review requires its unchanged preceding qualified identity')
        selected = [r for r in records if source_key(r) == entry.get('sourceObservationKey')
                    and r.get('profileUrl') == original.get('officialProfileUrl')]
        if len(selected) != 1:
            raise ValueError('A previous root absent from current qualified admission input cannot be resurrected')
        actual = root_observation(original, selected[0], items, cache)
        if entry.get('sourceObservation') != actual:
            raise ValueError('The retained candidate primary must equal its actual named source observations')
        verify_capture_proofs(actual['evidence'], queue, cache, pid)
        entry['captureVerified'] = True
        verified.append(entry); seen.add(pid); primary_uris.add(original['officialProfileUrl'])
        keys.add(tuple(entry['sourceObservationKey']))
    # Retained roots precede newly encountered alternatives, while every other
    # admission row keeps its original relative order and eligibility checks.
    ordered = [r for r in records if tuple(source_key(r)) in keys]
    ordered += [r for r in records if tuple(source_key(r)) not in keys]
    return ordered, verified
