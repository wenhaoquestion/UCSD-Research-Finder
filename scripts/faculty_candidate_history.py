"""Preserve dated non-final candidate snapshots without reasserting old fields."""
from __future__ import annotations

import copy
import re

from faculty_profile_bindings import profile_metadata, verified_profile_bindings, captured_source
from collect_ucsd_coverage import profiles_appointment, faculty_table_rows, academic_title_clause
from lab_resource_reviews import record_sha256
from refresh_faculty_directories import identity_name, possible_legacy_initial_alias


def candidate_history(history, people, faculty, queue, cache):
    if history.get('entries') and not re.fullmatch(r'[0-9a-f]{64}', history.get('sourceCandidateAtlasSha256', '')):
        raise ValueError('Candidate history requires the exact earlier atlas fingerprint')
    available = {person['id'] for person in people}
    people_by_id = {person['id']:person for person in people}
    proposed = {person['id'] for person in faculty['professors']}
    items = {item['url']:item for item in queue['items'].values()}
    patches, archives, seen = {}, [], set()
    for entry in history.get('entries', []):
        record = entry.get('record', {})
        rid = record.get('id')
        if (not rid or rid in seen or not entry.get('reason')
                or entry.get('recordSha256') != record_sha256(record)):
            raise ValueError('Candidate history requires one unchanged whole snapshot and explicit reason per identity')
        seen.add(rid)
        source_sha = entry.get('sourceCandidateAtlasSha256', history['sourceCandidateAtlasSha256'])
        if not re.fullmatch(r'[0-9a-f]{64}', source_sha):
            raise ValueError('Candidate history requires the specific snapshot fingerprint')
        if entry.get('disposition') == 'retain_previous_observations':
            if rid not in available:
                raise ValueError('Previous candidate observations cannot be assigned to another identity')
            target = patches.setdefault(rid, {'previousFieldObservations':[], 'fieldEvidence':{}})
            target['previousFieldObservations'].append({
                'field':'candidateSnapshot','value':copy.deepcopy(record),
                'reason':entry['reason'],'sourceCandidateAtlasSha256':source_sha})
        elif entry.get('disposition') == 'resolved_observation_binding_to_original_person':
            target_id = entry.get('targetProfessorId')
            binding = entry.get('observationBinding', {})
            if rid in available or rid in proposed or target_id not in people_by_id or target_id == rid:
                raise ValueError('A bound previous candidate requires a separate retained target and cannot remain published')
            verified = verified_profile_bindings({'entries':[binding]}, queue, cache, {'professors':people})
            if len(verified) != 1:
                raise ValueError('A previous candidate requires one explicit verified observation binding')
            bound = next(iter(verified.values())); own = bound['captures'][1]
            if bound['professorId'] != target_id:
                raise ValueError('Previous candidate binding target changed')
            _, markup = profile_metadata(items[own['requestedUrl']], cache)
            _, observed = profiles_appointment(items[own['requestedUrl']]['fetch'], markup)
            previous = [row for row in record.get('directoryListings', [])
                        if row.get('sourceUrl') == own['sourceUrl'] and row.get('observedAt') == own['observedAt']
                        and identity_name(row.get('name','')) == identity_name(own['nameAsDisplayed'])]
            applied = [row for row in faculty.get('byProfessorId', {}).get(target_id, {}).get('directoryListings', [])
                       if row.get('sourceUrl') == own['sourceUrl'] and row.get('observedAt') == own['observedAt']
                       and row.get('identityEvidence', {}).get('profileIdentityBinding') == bound]
            alias_ids = [rid] + record.get('aliasIds', [])
            if (observed is None or observed['discoveryId'] != rid or not previous or not applied
                    or set(alias_ids) & available):
                raise ValueError('A previous candidate alias requires its own retained snapshot and actually applied source observation')
            target = patches.setdefault(target_id, {'previousFieldObservations':[], 'fieldEvidence':{}})
            target['previousFieldObservations'].append({'field':'candidateSnapshot','value':copy.deepcopy(record),
                'reason':entry['reason'],'sourceCandidateAtlasSha256':source_sha})
            for field in ['professorIds','labAffiliations']:
                if record.get(field):
                    target['previousFieldObservations'].append({'field':field,'value':copy.deepcopy(record[field]),
                        'fieldEvidence':copy.deepcopy(record.get('fieldEvidence',{}).get(field,[])),
                        'reason':entry['reason'],'sourceCandidateAtlasSha256':source_sha})
            target.setdefault('candidateObservationAliases', []).append({
                'sourceProposedProfessorId':rid,'targetProfessorId':target_id,'aliasIds':alias_ids,
                'sourceRecordSha256':entry['recordSha256'],'sourceCandidateAtlasSha256':source_sha,
                'reason':entry['reason'],'candidateHistoryVerified':True,'observationBinding':bound})
        elif entry.get('disposition') == 'pending_unmapped_unit_legacy_alias_review':
            if rid in available or rid in proposed:
                raise ValueError('An unmapped-unit held candidate cannot also be a current proposal')
            holds = [row for row in faculty['uncertainListings']
                     if row.get('reason') == 'unmapped_unit_legacy_initials_requires_identity_review'
                     and row.get('listing', {}).get('discoveryId') == rid]
            proofs = entry.get('captures', [])
            candidates = entry.get('candidateProfessorIds', [])
            if len(holds) != 1 or len(proofs) != 1 or not candidates or candidates != holds[0].get('candidateProfessorIds'):
                raise ValueError('An unmapped-unit archive requires its exact current initial-alias hold')
            item = items.get(proofs[0]['requestedUrl'])
            if item is None:
                raise ValueError('Unmapped-unit archive requires its actual own-profile capture')
            actual, markup = profile_metadata(item, cache)
            assessment, observed = profiles_appointment(item['fetch'], markup)
            listing = holds[0]['listing']
            previous_listing = any(old.get('sourceUrl') == actual['sourceUrl']
                                   and old.get('observedAt') == actual['observedAt']
                                   and identity_name(old.get('name', '')) == identity_name(record['name'])
                                   for old in record.get('directoryListings', []))
            if (actual != proofs[0] or observed is None or observed['discoveryId'] != rid or not previous_listing
                    or assessment['mappedDepartment'] != 'Unknown'
                    or identity_name(observed['name']) != identity_name(record['name'])
                    or listing.get('department') != 'Unknown' or listing.get('sourceUrl') != actual['sourceUrl']
                    or listing.get('observedAt') != actual['observedAt']
                    or any(pid not in people_by_id or not possible_legacy_initial_alias(record['name'], people_by_id[pid])
                           for pid in candidates)):
                raise ValueError('Unmapped-unit archive source, qualification or possible legacy identity changed')
            archives.append({**copy.deepcopy(entry),'candidateHistoryVerified':True,
                             'sourceCandidateAtlasSha256':source_sha})
        elif entry.get('disposition') == 'pending_cross_department_initial_alias_review':
            if rid in available or rid in proposed:
                raise ValueError('A cross-department initial-alias hold cannot also be published')
            holds = [hold for hold in faculty['uncertainListings']
                     if hold.get('reason') == 'cross_department_legacy_initials_requires_identity_review'
                     and hold.get('provisionalRecordSnapshot', {}).get('id') == rid]
            proofs, candidates = entry.get('captures', []), entry.get('candidateProfessorIds', [])
            if len(holds) != 1 or len(proofs) != 1 or candidates != holds[0].get('candidateProfessorIds'):
                raise ValueError('The cross-department archive requires its exact current qualified alias-review hold')
            hold = holds[0]; listing = hold['listing']; current = hold['provisionalRecordSnapshot']
            if (not candidates or current['name'] != record['name'] or current['department'] != record['department']
                    or any(pid not in people_by_id or people_by_id[pid]['department'] == current['department']
                           or not possible_legacy_initial_alias(record['name'], people_by_id[pid]) for pid in candidates)):
                raise ValueError('The initial-only originals and distinct named source department must remain review leads only')
            item = items.get(proofs[0].get('requestedUrl'))
            if item is None:
                raise ValueError('The cross-department hold requires its actual positive source')
            if listing.get('profileDiscovery'):
                actual, markup = profile_metadata(item, cache)
                assessment, observed = profiles_appointment(item['fetch'], markup)
                valid = (observed is not None and observed['discoveryId'] == rid
                         and identity_name(observed['name']) == identity_name(record['name'])
                         and observed['department'] == record['department'] and record['department'] != 'Unknown'
                         and actual['requestedUrl'] == listing['profileUrl'])
            else:
                actual, markup = captured_source(item, cache)
                rows = faculty_table_rows(record['department'], item['fetch'], markup)
                matching = [row for row in rows if all(row.get(k) == listing.get(k)
                            for k in ['name', 'department', 'listedRole', 'profileUrl', 'sourceUrl', 'observedAt'])]
                valid = (entry.get('qualificationType') == 'named_faculty_table_row' and len(matching) == 1
                         and academic_title_clause(listing['listedRole'])
                         and record['officialProfileUrl'] == listing['profileUrl'])
            previous = any(old.get('sourceUrl') == actual['sourceUrl'] and old.get('observedAt') == actual['observedAt']
                           and identity_name(old.get('name', '')) == identity_name(record['name'])
                           for old in record.get('directoryListings', []))
            if (not valid or actual != proofs[0] or not previous
                    or (listing['sourceUrl'], listing['observedAt']) != (actual['sourceUrl'], actual['observedAt'])):
                raise ValueError('The old whole candidate must retain the actual dated qualifying named source observation')
            archives.append({**copy.deepcopy(entry), 'candidateHistoryVerified': True,
                             'sourceCandidateAtlasSha256': source_sha})
        elif entry.get('disposition') == 'pending_peer_profile_identity_review':
            if rid in available or rid in proposed:
                raise ValueError('A held previous candidate cannot also be a current proposal')
            holds = [row for row in faculty['uncertainListings']
                     if row.get('reason') == 'distinct_profile_same_or_similar_name_requires_identity_review'
                     and row.get('listing', {}).get('discoveryId') == rid]
            proofs = entry.get('captures', [])
            if not holds or len(proofs) != 2:
                raise ValueError('A held previous candidate requires its explicit current unresolved observation')
            actual = [profile_metadata(items[p['requestedUrl']], cache)[0] for p in proofs]
            if (actual != proofs or actual[0]['requestedUrl'] != record['officialProfileUrl']
                    or any(identity_name(p['nameAsDisplayed']) != identity_name(record['name']) for p in actual)
                    or actual[0]['canonicalUri'] == actual[1]['canonicalUri']
                    or actual[0]['rdfAlternateUri'] == actual[1]['rdfAlternateUri']):
                raise ValueError('Peer-profile hold requires the two actual named captures with different identifiers')
            archives.append({**copy.deepcopy(entry),'candidateHistoryVerified':True,
                             'sourceCandidateAtlasSha256':source_sha})
        else:
            raise ValueError('Unknown historical candidate disposition')
    return patches, archives


def attach_history_patches(patches, history_patches):
    for rid, previous in history_patches.items():
        target = patches.setdefault(rid, {'fieldEvidence':{}})
        observations = target.setdefault('previousFieldObservations', [])
        observations.extend(copy.deepcopy(row) for row in previous['previousFieldObservations'] if row not in observations)
        if previous.get('candidateObservationAliases'):
            aliases = target.setdefault('candidateObservationAliases', [])
            aliases.extend(copy.deepcopy(row) for row in previous['candidateObservationAliases'] if row not in aliases)
