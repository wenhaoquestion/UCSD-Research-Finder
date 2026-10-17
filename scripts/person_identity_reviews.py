"""Explicit person identity decisions, with independent department evidence.

Name/email similarity only discovers a review case. Applying a decision requires
the original stable-ID records and dated raw captures of a shared identifier.
Whole source records, conflicting observations and retired IDs remain preserved.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import urllib.parse
from pathlib import Path

from atlas_urls import valid_url, url_key
from lab_identity_merges import verify_capture_proofs
from lab_resource_reviews import record_sha256
from refresh_labs import DOM, every_node, person_matches, merge_observed_fields, unique_values, evidence_items, has_value
from faculty_resource_label_reviews import KIND as RESOURCE_LABEL_KIND, verify_resource_label_review
from faculty_profile_chain_reviews import KIND as PROFILE_CHAIN_KIND, verify_profile_chain_review
from faculty_shared_primary_reviews import KIND as SHARED_PRIMARY_KIND, verify_shared_primary_review, retain_shared_primary_observations
from faculty_career_identity_reviews import KIND as CAREER_KIND, verify_career_review, retain_career_observations


def official_profile_uri(uri):
    if not valid_url(uri):
        return False
    host = urllib.parse.urlsplit(uri).hostname or ''
    return host == 'ucsd.edu' or host.endswith('.ucsd.edu')


def json_pointer(value, pointer):
    if not isinstance(pointer, str) or not pointer.startswith('/'):
        raise ValueError('A source JSON record requires an explicit pointer')
    for component in pointer[1:].split('/'):
        if re.search(r'~(?![01])', component):
            raise ValueError('Invalid source JSON pointer escape')
        component = component.replace('~1', '/').replace('~0', '~')
        if isinstance(value, list):
            if not re.fullmatch(r'0|[1-9][0-9]*', component):
                raise ValueError('Invalid source JSON array index')
            value = value[int(component)]
        else:
            value = value[component]
    return value


def verify_person_proofs(proofs, queue, cache, label):
    items = {item['url']: item for item in queue['items'].values()}
    for proof in proofs:
        if proof.get('evidenceType') != 'json_record':
            verify_capture_proofs([proof], queue, cache, label)
            continue
        meta = items.get(proof.get('requestedUrl'), {}).get('fetch', {})
        path = Path(cache) / 'responses' / (hashlib.sha256(proof.get('requestedUrl', '').encode()).hexdigest() + '.html')
        if (not path.exists() or meta.get('status') != 'ok' or meta.get('sourceUrl') != proof.get('requestedUrl')
                or meta.get('finalUrl') != proof.get('sourceUrl') or meta.get('observedAt') != proof.get('observedAt')
                or hashlib.sha256(path.read_bytes()).hexdigest() != proof.get('bodySha256')):
            raise ValueError('Person identity JSON proof does not match its actual capture: ' + label)
        try:
            record = json_pointer(json.loads(path.read_bytes()), proof.get('sourceJsonPointer'))
        except (ValueError, TypeError, KeyError, IndexError) as error:
            raise ValueError('Person identity source JSON pointer changed') from error
        if (record != proof.get('sourceRecord') or proof.get('evidence') != json.dumps(record, ensure_ascii=False, sort_keys=True)):
            raise ValueError('Person identity JSON record/quotation changed: ' + label)
    if not proofs:
        raise ValueError('Person identity review requires source evidence')


def verified_person_reviews(review, queue, cache, baseline, faculty_review=None):
    people = {p['id']: p for p in baseline['professors']}
    rows = copy.deepcopy(review.get('entries', []))
    sources, targets = [r['sourceProfessorId'] for r in rows], {r['targetProfessorId'] for r in rows}
    if len(set(sources)) != len(sources) or set(sources) & targets:
        raise ValueError('Person identity decisions must be explicit and acyclic')
    for row in rows:
        source, target = people.get(row['sourceProfessorId']), people.get(row['targetProfessorId'])
        if (row.get('action') != 'merge' or not row.get('reason') or source is None or target is None
                or row.get('originalSourceRecord') != source or row.get('originalTargetRecord') != target
                or row.get('sourceRecordSha256') != record_sha256(source) or row.get('targetRecordSha256') != record_sha256(target)
                or row.get('name') != target['name']):
            raise ValueError('Person merge requires unchanged full source/target records and the reviewed target name')
        proofs = row.get('evidence', [])
        verify_person_proofs(proofs, queue, cache, row['name'])
        identifiers = row.get('identitySources', [])
        basis = row.get('identityBasis', {})
        kind, identifier = basis.get('type'), basis.get('value', '')
        if kind == RESOURCE_LABEL_KIND:
            verify_resource_label_review(row, source, target, list(people.values()), queue, cache)
            row['captureVerified'] = True
            continue
        if kind == PROFILE_CHAIN_KIND:
            verify_profile_chain_review(row, source, target, rows, list(people.values()), queue, cache)
            row['captureVerified'] = True
            continue
        if kind == SHARED_PRIMARY_KIND:
            verify_shared_primary_review(row, source, target, list(people.values()), queue, cache)
            row['captureVerified'] = True
            continue
        if kind == CAREER_KIND:
            verify_career_review(row, source, target, list(people.values()), queue, cache, faculty_review)
            row['captureVerified'] = True
            continue
        if source['name'] != target['name']:
            raise ValueError('Person merge requires unchanged full source/target records with the same full name')
        if (kind not in {'shared_public_email', 'shared_personal_website', 'shared_named_endowed_chair'} or not identifier
                or len(identifiers) < 2 or len({p['nameEvidence']['requestedUrl'] for p in identifiers}) < 2):
            raise ValueError('Person identity requires independently captured shared identifiers')
        if kind == 'shared_public_email':
            if not re.fullmatch(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', identifier):
                raise ValueError('Invalid shared public email')
            owners = {p['name'] for p in people.values() if str(p.get('email', '')).lower() == identifier.lower()}
            if owners != {row['name']} or any(p.get('email', '').lower() != identifier.lower() for p in [source, target]):
                raise ValueError('Shared department contacts cannot identify a person')
        if kind == 'shared_personal_website' and (not valid_url(identifier) or any(url_key(p.get('personalWebsiteUrl', '')) != url_key(identifier) for p in [source, target])):
            raise ValueError('Shared personal link must match the retained individual records')
        if kind == 'shared_named_endowed_chair' and (len(identifier.split()) < 5 or 'endowed chair' not in identifier.lower()):
            raise ValueError('A generic academic position cannot identify a person')
        for item in identifiers:
            name_proof, identifier_proof = item['nameEvidence'], item['identifierEvidence']
            if not official_profile_uri(name_proof.get('sourceUrl', '')):
                raise ValueError('Person identity sources require official campus provenance')
            if name_proof not in proofs or identifier_proof not in proofs or name_proof['requestedUrl'] != identifier_proof['requestedUrl']:
                raise ValueError('Each shared identifier must belong to its own named source')
            if name_proof.get('evidenceType') == 'json_record':
                record = name_proof['sourceRecord']
                own_name = ' '.join(record.get(f, '') for f in ['first_name', 'last_name'])
                subject_matches = own_name == row['name']
            else:
                path = Path(cache) / 'responses' / (hashlib.sha256(name_proof['requestedUrl'].encode()).hexdigest() + '.html')
                subject_matches = any(person_matches(row['name'], node.text()) for node in every_node(DOM(path.read_text()).root)
                                      if node.tag in {'title', 'h1'})
            if not subject_matches:
                raise ValueError('The source must explicitly name the reviewed person as its subject')
            if kind == 'shared_personal_website':
                identifier_matches = identifier_proof.get('evidenceType') == 'named_link' and url_key(identifier_proof.get('linkUrl', '')) == url_key(identifier)
            else:
                identifier_matches = identifier in identifier_proof['evidence']
            if not identifier_matches:
                raise ValueError('Shared identifier is absent from its dated captured proof')
        fields = row.get('fields', {})
        if set(fields) - {'department', 'officialProfileUrl'} or not fields.get('department') or not official_profile_uri(fields.get('officialProfileUrl', '')):
            raise ValueError('Person identity review requires an explicit department and individual profile')
        if not any(url_key(fields['officialProfileUrl']) in {url_key(p['requestedUrl']), url_key(p['sourceUrl'])} and person_matches(row['name'], p['evidence']) for p in proofs):
            raise ValueError('Canonical individual profile requires its own positive named capture')
        for field in fields:
            if not row.get('fieldEvidence', {}).get(field) or any(p not in proofs for p in row['fieldEvidence'][field]):
                raise ValueError('Person field correction lacks its specific reviewed proof')
        for affiliation in row.get('departmentEvidence', []):
            if not affiliation.get('department') or not affiliation.get('fieldEvidence') or any(p not in proofs for p in affiliation['fieldEvidence']):
                raise ValueError('Each departmental association requires separate captured evidence')
        if fields['department'] not in {a['department'] for a in row.get('departmentEvidence', [])}:
            raise ValueError('Primary department must have an explicit department review')
        row['captureVerified'] = True
    return rows


def apply_person_reviews(data, reviews):
    people = {p['id']: p for p in data['professors']}
    sources = [r['sourceProfessorId'] for r in reviews]
    if len(set(sources)) != len(sources) or set(sources) & {r['targetProfessorId'] for r in reviews}:
        raise ValueError('Person merges must be acyclic')
    for row in reviews:
        source, target = people.get(row['sourceProfessorId']), people.get(row['targetProfessorId'])
        if (not row.get('captureVerified') or not row.get('evidence') or not row.get('reason') or target is None
                or (source is None and row['sourceProfessorId'] not in target.get('aliasIds', []))):
            raise ValueError('Person merge requires a verified decision and preserved stable IDs')
    removed = []
    for row in reviews:
        source, target = people.get(row['sourceProfessorId']), people[row['targetProfessorId']]
        before = copy.deepcopy(target)
        if row['identityBasis']['type'] == RESOURCE_LABEL_KIND:
            # A malformed resource label has no trusted person fields to copy.
            # Keep its complete observed record under the resolved identity,
            # including old ratings, contacts, source links and relationships.
            if source is not None:
                target['aliasIds'] = unique_values(target.get('aliasIds', []) + [source['id']] + source.get('aliasIds', []))
                target['previousFieldObservations'] = unique_values(target.get('previousFieldObservations', []) + [
                    {'field': 'misparsedResourceRecord', 'value': copy.deepcopy(source),
                     'sourceProfessorId': source['id'], 'reason': row['reason']}])
                removed.append({'reason': row['reason'], 'record': copy.deepcopy(source),
                                'targetBeforeMerge': before, 'personIdentityReview': copy.deepcopy(row)})
                del people[source['id']]
            if row.get('previousCandidateObservation'):
                previous = row['previousCandidateObservation']
                target['previousFieldObservations'] = unique_values(target.get('previousFieldObservations', []) + [
                    {'field': 'misparsedResourcePreviousCandidate', 'value': copy.deepcopy(previous['record']),
                     'recordSha256': previous['recordSha256'], 'candidateAtlasSha256': previous['candidateAtlasSha256'],
                     'sourceProfessorId': row['sourceProfessorId'], 'reason': row['reason']}])
            target['personIdentityReviews'] = unique_values(target.get('personIdentityReviews', []) + [row])
            target['sourceUrls'] = unique_values(target.get('sourceUrls', []) + [p['sourceUrl'] for p in row['evidence']])
            proofs = target.setdefault('fieldEvidence', {})
            proofs['aliasIds'] = unique_values(evidence_items(proofs.get('aliasIds')) + [
                {**proof, 'method': 'verified_existing_professor_id_from_misparsed_resource_label',
                 'sourceProfessorId': row['sourceProfessorId'], 'targetProfessorId': row['targetProfessorId']}
                for proof in row['evidence']])
            continue
        if source is not None:
            original = copy.deepcopy(source)
            scalar_source = copy.deepcopy(source)
            scalar_source['fieldEvidence'] = {field: proof for field, proof in source.get('fieldEvidence', {}).items()
                                               if field != 'teaching' and not field.startswith('ratings.')
                                               and not (row['identityBasis']['type'] in {PROFILE_CHAIN_KIND, SHARED_PRIMARY_KIND, CAREER_KIND} and field == 'name')
                                               and not (row['identityBasis']['type'] in {SHARED_PRIMARY_KIND, CAREER_KIND}
                                                        and field in {'appointmentStatus', 'personalWebsiteUrl'})
                                               and not (row['identityBasis']['type'] == CAREER_KIND
                                                        and field in {'department', 'officialProfileUrl'})}
            merged = merge_observed_fields(target, scalar_source)
            merged['id'] = before['id']
            for field, value in source.items():
                if (field not in {'id', 'name', 'department', 'officialProfileUrl', 'fieldEvidence', 'verification', 'ratings', 'teaching'}
                        and not (row['identityBasis']['type'] in {SHARED_PRIMARY_KIND, CAREER_KIND}
                                 and field in {'appointmentStatus', 'personalWebsiteUrl'})
                        and not has_value(merged.get(field))):
                    merged[field] = copy.deepcopy(value)
            for field in ['sourceUrls', 'directoryListings', 'departmentAffiliations', 'labAffiliations', 'aliasNames', 'unverifiedFields',
                          'previousFieldObservations', 'verificationHistory', 'additionalProfileObservations', 'appliedEvidencePatches', 'unresolvedLabLinks', 'sourceUrlObservations']:
                if source.get(field):
                    merged[field] = unique_values(merged.get(field, []) + source[field])
            if source.get('teaching'):
                teaching = {**source['teaching'], **before.get('teaching', {})}
                for field in ['courses', 'candidates']:
                    if source['teaching'].get(field):
                        teaching[field] = unique_values(before.get('teaching', {}).get(field, []) + source['teaching'][field])
                merged['teaching'] = teaching
                teaching_proofs = unique_values(evidence_items(before.get('fieldEvidence', {}).get('teaching')) + evidence_items(source.get('fieldEvidence', {}).get('teaching')))
                if teaching_proofs:
                    merged.setdefault('fieldEvidence', {})['teaching'] = teaching_proofs
            for platform, rating in source.get('ratings', {}).items():
                if platform not in merged.setdefault('ratings', {}):
                    merged['ratings'][platform] = copy.deepcopy(rating)
                    field = 'ratings.' + platform
                    if source.get('fieldEvidence', {}).get(field):
                        merged.setdefault('fieldEvidence', {})[field] = copy.deepcopy(source['fieldEvidence'][field])
            for field in ['ratings', 'academicProfile', 'teaching']:
                if source.get(field) and source[field] != before.get(field):
                    history = {'field': field, 'value': copy.deepcopy(source[field]), 'reason': row['reason'], 'sourceProfessorId': source['id']}
                    merged['previousFieldObservations'] = unique_values(merged.get('previousFieldObservations', []) + [history])
            target.clear(); target.update(merged)
            target['aliasIds'] = unique_values(target.get('aliasIds', []) + [source['id']] + source.get('aliasIds', []))
            removed.append({'reason': row['reason'], 'record': original, 'targetBeforeMerge': before, 'personIdentityReview': copy.deepcopy(row)})
            del people[source['id']]
        corrected = merge_observed_fields(target, {**row['fields'], 'fieldEvidence': row['fieldEvidence']})
        target.clear(); target.update(corrected)
        # This is an explicit verified identity/resource selection. A newer
        # observation under a retired ID cannot reverse that selection simply
        # because its capture date is later than the decision's source proof.
        for field, selected in row['fields'].items():
            if target.get(field) == selected:
                continue
            observation = {'field': field, 'value': copy.deepcopy(target.get(field)),
                           'fieldEvidence': copy.deepcopy(evidence_items(target.get('fieldEvidence', {}).get(field))),
                           'reason': 'Preserve the newer source observation separately from the explicitly reviewed canonical person field.'}
            target['previousFieldObservations'] = unique_values(target.get('previousFieldObservations', []) + [observation])
            target[field] = copy.deepcopy(selected)
            target.setdefault('fieldEvidence', {})[field] = copy.deepcopy(row['fieldEvidence'][field])
        affiliations = unique_values(target.get('departmentAffiliations', []) + [a['department'] for a in row['departmentEvidence']])
        rejected = row.get('unsupportedDepartmentValues', [])
        for department in [value for value in affiliations if value in rejected]:
            observation = {'field': 'departmentAffiliations', 'value': [department], 'reason': 'Not supported by captured departmental evidence; historical observation retained without claiming absence of an appointment.'}
            target['previousFieldObservations'] = unique_values(target.get('previousFieldObservations', []) + [observation])
        target['departmentAffiliations'] = [value for value in affiliations if value not in rejected]
        target['departmentAffiliationEvidence'] = unique_values(target.get('departmentAffiliationEvidence', []) + row['departmentEvidence'])
        target['personIdentityReviews'] = unique_values(target.get('personIdentityReviews', []) + [row])
        target['sourceUrls'] = unique_values(target.get('sourceUrls', []) + [p['sourceUrl'] for p in row['evidence']])
        proofs = target.setdefault('fieldEvidence', {})
        proofs['personIdentityReview'] = unique_values(evidence_items(proofs.get('personIdentityReview')) + row['evidence'])
        proofs['departmentAffiliations'] = unique_values(evidence_items(proofs.get('departmentAffiliations')) + [p for a in row['departmentEvidence'] for p in a['fieldEvidence']])
        if row['identityBasis']['type'] == SHARED_PRIMARY_KIND:
            retain_shared_primary_observations(target, row)
        if row['identityBasis']['type'] == CAREER_KIND:
            retain_career_observations(target, row)
        if row['identityBasis']['type'] == PROFILE_CHAIN_KIND:
            for listing in target.get('directoryListings', []):
                if (listing.get('department') in row.get('unsupportedDepartmentValues', [])
                        and not listing.get('departmentAsListed') and not listing.get('departmentExplicitlyListed')):
                    target['previousFieldObservations'] = unique_values(target.get('previousFieldObservations', []) + [
                        {'field': 'directoryListings', 'value': [copy.deepcopy(listing)],
                         'reason': 'Inherited source-context placeholder is unverified as an academic department; preserve its complete observation without asserting absence of an appointment.'}])
                    listing['sourceDepartmentContext'] = listing['department']
                    listing['department'] = 'Unknown'
                    listing['departmentMappingStatus'] = 'unverified_source_context_only'
            # Alias-ID captures may carry the longer published name. Preserve
            # that observation while keeping this review's named primary form.
            preferred_name = row['originalTargetRecord']['name']
            qualification = row['profileChainBinding']['targetOwnQualification']
            corrected = merge_observed_fields(target, {'name': preferred_name,
                'fieldEvidence': {'name': qualification['fieldEvidence']['nameAsDisplayed']}})
            target.clear(); target.update(corrected)
            proofs = target.setdefault('fieldEvidence', {})
            published = row['profileChainBinding']['sourceNamedRoster']
            target['aliasNames'] = [name for name in unique_values(target.get('aliasNames', []) + [row['originalSourceRecord']['name']])
                                    if name != preferred_name]
            proofs['aliasNames'] = unique_values(evidence_items(proofs.get('aliasNames')) + [
                {**published, 'sourceUrl': published['sourceUrl'], 'observedAt': published['observedAt'],
                 'method': 'verified_published_name_from_named_personal_profile_chain', 'evidence': published['rowText']}])
            if row.get('previousCandidateObservation'):
                previous = row['previousCandidateObservation']
                target['previousFieldObservations'] = unique_values(target.get('previousFieldObservations', []) + [
                    {'field': 'personProfileChainPreviousCandidate', 'value': copy.deepcopy(previous['record']),
                     'recordSha256': previous['recordSha256'], 'candidateAtlasSha256': previous['candidateAtlasSha256'],
                     'sourceProfessorId': row['sourceProfessorId'], 'reason': row['reason']}])
    data['professors'] = [p for p in data['professors'] if p['id'] in people]
    canonical = {rid: p['id'] for p in data['professors'] for rid in [p['id']] + p.get('aliasIds', [])}
    for lab in data.get('labs', []):
        previous = lab.get('professorIds', [])
        updated = list(dict.fromkeys(canonical.get(pid, pid) for pid in previous))
        if previous != updated:
            lab['previousFieldObservations'] = unique_values(lab.get('previousFieldObservations', []) + [{'field': 'professorIds', 'value': previous, 'reason': 'Explicit reviewed person ID consolidation; original links retained.'}])
            lab['professorIds'] = updated
    return removed
