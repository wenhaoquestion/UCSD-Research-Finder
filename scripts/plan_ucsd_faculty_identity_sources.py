#!/usr/bin/env python3
"""Prioritize exact existing person URIs needed by unresolved identity reviews.

The plan adds source requests, never person aliases, faculty acceptances or
scientific field updates. Names select a review case only. New metadata must
later establish the actual relationship between the independently named pages.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import urllib.parse
from collections import Counter
from pathlib import Path

from atlas_urls import valid_url
from collect_ucsd_coverage import Queue, profiles_appointment, safe_url, url_key as queue_key, atomic_json, now
from collection_scope import ScopePolicy
from lab_resource_reviews import record_sha256
from refresh_faculty_directories import identity_name, individual_profile
from refresh_labs import person_matches

ROOT = Path(__file__).resolve().parents[1]
PLAN_NAME = 'faculty-identity-source-plan-20261016.json'


def prepare_plan(review, queue, atlas, cache):
    people = {person['id']: person for person in atlas['professors']}
    by_requested_uri = {safe_url(item['url']): item for item in queue['items'].values() if safe_url(item['url'])}
    by_observation = {}
    for item in queue['items'].values():
        meta = item.get('fetch', {})
        if meta.get('status') == 'ok':
            by_observation.setdefault((meta.get('finalUrl'), meta.get('observedAt')), []).append(item)
    checked, cases, requested, skipped = {}, {}, {}, Counter()
    for unresolved in review['uncertainListings']:
        if unresolved.get('reason') != 'distinct_profile_same_or_similar_name_requires_identity_review':
            continue
        row = unresolved['listing']
        for pid in unresolved.get('candidateProfessorIds', []):
            person = people.get(pid)
            if person is None:
                skipped['unpublished_candidate_not_an_original_id'] += 1
                continue
            uri, name = person['officialProfileUrl'], identity_name(person['name'])
            host = urllib.parse.urlsplit(uri).hostname or ''
            if not valid_url(uri) or not (host == 'ucsd.edu' or host.endswith('.ucsd.edu')) or not individual_profile(uri):
                skipped['original_uri_is_not_an_individual_campus_page'] += 1
                continue
            if not name or len(name.split()[0]) < 2 or not person_matches(name, row['name']):
                skipped['initial_or_name_variant_requires_separate_review'] += 1
                continue
            key = (row['sourceUrl'], row['observedAt'])
            if key not in checked:
                sources = by_observation.get(key, [])
                source = next((item for item in sources if item['url'] == row['sourceUrl']), sources[0] if sources else None)
                if source is None:
                    raise ValueError('Identity source plan has no exact dated Profiles observation')
                meta = source['fetch']
                path = Path(cache) / 'responses' / (hashlib.sha256(source['url'].encode()).hexdigest() + '.html')
                if (urllib.parse.urlsplit(meta['finalUrl']).hostname != 'profiles.ucsd.edu' or not path.exists()
                        or hashlib.sha256(path.read_bytes()).hexdigest() != meta.get('sha256')):
                    raise ValueError('Identity source plan requires unchanged actual campus Profile bytes')
                assessment, appointment = profiles_appointment(meta, path.read_text())
                if appointment is None:
                    raise ValueError('Unresolved faculty identity input lacks its own explicit campus appointment table')
                checked[key] = {'requestedUrl': source['url'], 'sourceUrl': meta['finalUrl'], 'observedAt': meta['observedAt'],
                                'bodySha256': meta['sha256'], 'nameAsDisplayed': appointment['name'],
                                'titleAsListed': assessment['titleAsListed'], 'schoolAsListed': assessment['schoolAsListed']}
            observed = checked[key]
            if identity_name(observed['nameAsDisplayed']) != identity_name(row['name']):
                raise ValueError('Unresolved faculty row does not match the actual named Profile subject')
            original_key = safe_url(uri)
            item = by_requested_uri.get(original_key)
            state = item['state'] if item else 'not_queued'
            fingerprint = hashlib.sha256(json.dumps([pid, uri, observed], sort_keys=True).encode()).hexdigest()[:20]
            case = {'caseId': 'identity-source-' + fingerprint, 'professorId': pid, 'originalName': person['name'],
                    'originalDepartment': person['department'], 'originalProfileUri': uri, 'requestedTransportUri': original_key,
                    'originalProfessorRecordSha256': record_sha256(person), 'qualificationSource': observed,
                    'originalSourceQueueState': state,
                    'originalSourceCapture': {k: item.get('fetch', {}).get(k) for k in ['status', 'observedAt', 'httpStatus', 'finalUrl', 'sha256', 'error', 'redirects']} if item else None,
                    'reviewStatus': 'source_check_proposed' if state in {'not_queued', 'pending', 'running', 'retained_prior_evidence'}
                                    else 'captured_original_source_available_for_identifier_review' if item.get('fetch', {}).get('status') == 'ok'
                                    else 'existing_source_failure_retained_without_reset',
                    'identityEstablished': False}
            if original_key != uri:
                case.update(reviewStatus='original_uri_requires_transport_normalization_review',
                            requestedTransportUri='', originalSourceQueueState='not_requested_exactly',
                            originalSourceCapture=None,
                            transportNormalizationReview={
                                'normalizedUri': original_key, 'normalizedUriQueueState': state,
                                'reason': 'The stored original URI changes during transport normalization. Preserve it as a record/link review case; do not use a stripped fragment or other normalized URI as evidence for this named person.'})
            cases[case['caseId']] = case
            if case['reviewStatus'] == 'source_check_proposed':
                request_key = (uri, pid)
                request = requested.setdefault(request_key, {'url': uri, 'department': person['department'], 'kind': 'profile_identity_review',
                    'professorId': pid, 'sourceUrl': observed['sourceUrl'], 'depth': 2, 'identityDepth': 2,
                    'discoveryMethod': 'exact_original_record_uri_for_unresolved_person_identity',
                    'identitySourcePlan': PLAN_NAME, 'identitySourceCaseIds': [],
                    'scopeNote': 'Original individual campus URI, as listed. Name compatibility schedules a source check only; no identity, appointment, rank, alias, URI equivalence or merge is inferred.'})
                request['identitySourceCaseIds'].append(case['caseId'])
    return {'schemaVersion': 1, 'generatedAt': now(), 'isFinalIdentityReview': False, 'wireRequests': 0,
            'sourceQueueCheckpointAt': queue.get('updatedAt'), 'skippedInputCounts': dict(skipped), 'cases': list(cases.values()),
            'counts': {'reviewCases': len(cases), 'reviewCaseStates': dict(Counter(case['reviewStatus'] for case in cases.values())),
                       'sourceContexts': len(requested), 'uniqueRequestUris': len({request['url'] for request in requested.values()})},
            'policy': 'Only exact existing individual campus URIs are requested. Preserve old source receipts and retry bounds. These requests do not qualify, merge, rename or create a professor. No guessed protocol, WWW, path or profile variant.'}, list(requested.values())


def preserve_plan_history(plan, previous):
    """Keep configured case references valid when the unresolved input changes."""
    current = {case['caseId']: case for case in plan['cases']}
    old_cases = {case['caseId']: case for case in previous.get('historicalCases', [])}
    old_cases.update({case['caseId']: case for case in previous.get('cases', [])})
    historical = {}
    for old in old_cases.values():
        if old['caseId'] not in current:
            historical[old['caseId']] = copy.deepcopy(old)
            continue
        new = current[old['caseId']]
        observations = copy.deepcopy(old.get('previousSourcePlanObservations', []))
        old_value = {key: value for key, value in old.items() if key != 'previousSourcePlanObservations'}
        if old_value != new and old_value not in observations:
            observations.append(copy.deepcopy(old_value))
        if observations:
            new['previousSourcePlanObservations'] = observations
    plan['historicalCases'] = list(historical.values())
    plan['historicalCaseMeaning'] = 'No longer in the current unresolved input; this does not independently claim identity resolution or acceptance.'
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Append validated contexts to the existing collector configuration; never write its live queue')
    args = parser.parse_args()
    cache = ROOT / '.cache/coverage-20261016'
    preview = cache / 'profile-qualification-preview'
    queue_bytes, review_bytes = (preview / 'queue.json').read_bytes(), (preview / 'faculty-review.json').read_bytes()
    atlas_bytes = (ROOT / 'data/research-atlas.json').read_bytes()
    queue, review, atlas = json.loads(queue_bytes), json.loads(review_bytes), json.loads(atlas_bytes)
    plan, sources = prepare_plan(review, queue, atlas, cache)
    previous_path = ROOT / 'data/ucsd' / PLAN_NAME
    if args.apply and previous_path.exists():
        preserve_plan_history(plan, json.loads(previous_path.read_bytes()))
    output = cache / 'faculty-identity-source-plan-preview'; output.mkdir(exist_ok=True)
    shadow = Queue(output / 'queue.json'); shadow.state = copy.deepcopy(queue)
    before = set(shadow.state['items'])
    retained = {uri: copy.deepcopy(item.get('retainedEvidence')) for uri, item in shadow.state['items'].items() if item['state'] == 'retained_prior_evidence'}
    for source in sources:
        shadow.add(source['url'], source['department'], source['kind'], source['sourceUrl'], source['depth'], professor_id=source['professorId'], identity_depth=source['identityDepth'])
    collisions = []
    for source in sources:
        item = shadow.state['items'].get(queue_key(source['url']))
        if item is None or safe_url(item['url']) != safe_url(source['url']):
            collisions.append({'professorId': source['professorId'], 'literalOriginalUri': source['url'],
                               'queueKey': queue_key(source['url']), 'storedRequestedUri': item.get('url') if item else None,
                               'storedFetchObservedAt': item.get('fetch', {}).get('observedAt') if item else None})
    if collisions:
        plan.update(appliedToConfiguration=False, liveQueueWritten=False, previewStateSaved=False,
                    unsafeQueueKeyCollisions=collisions, failure='queue_key_collapses_distinct_path_uris',
                    sourceQueueSha256=hashlib.sha256(queue_bytes).hexdigest(), facultyReviewSha256=hashlib.sha256(review_bytes).hexdigest(),
                    baselineAtlasSha256=hashlib.sha256(atlas_bytes).hexdigest(),
                    requiredRepair='Migrate keys by actual requested URI, preserving every old observation, candidate/decision binding and stable scientific ID. Replay actual saved literal links, not guessed slash variants. Do not restart the healthy live child or write its queue from this preview.')
        atomic_json(output / PLAN_NAME, plan)
        print(json.dumps({'counts': plan['counts'], 'unsafeQueueKeyCollisions': len(collisions), 'appliedToConfiguration': False, 'liveQueueWritten': False}))
        raise SystemExit(2)
    policy = ScopePolicy(shadow.state, atlas)
    denied = [{'uri': source['url'], 'reason': policy.request_reason(shadow.state['items'][queue_key(source['url'])])} for source in sources]
    denied = [row for row in denied if row['reason']]
    if denied:
        raise ValueError('Identity source plan fails the existing scope policy: ' + json.dumps(denied))
    reopened = [uri for uri, receipt in retained.items() if shadow.state['items'][uri]['state'] == 'pending']
    if any(receipt not in shadow.state['items'][uri].get('retainedEvidenceHistory', []) for uri, receipt in retained.items() if uri in reopened):
        raise ValueError('Identity source preview lost an older retained receipt')
    shadow.save()
    config_path = ROOT / 'data/ucsd/coverage-20261016-additional-sources.json'
    config = json.loads(config_path.read_bytes()); original = copy.deepcopy(config['sources'])
    retired = [source for source in original if source.get('identitySourcePlan') == PLAN_NAME
               and safe_url(source['url']) != source['url']]
    if args.apply and retired:
        config['sources'] = [source for source in original if source not in retired]
        history = config.setdefault('retiredIdentitySourceContexts', [])
        for source in retired:
            history.append({'source': copy.deepcopy(source), 'retiredAt': now(),
                            'reason': 'Original URI requires transport normalization review; its complete context is retained without scheduling a guessed or fragment-stripped person request.'})
    keys = {(source['url'], source.get('kind'), source.get('professorId')) for source in config['sources']}
    added = [source for source in sources if (source['url'], source['kind'], source['professorId']) not in keys]
    if args.apply:
        config['sources'].extend(added)
        atomic_json(config_path, config)
    plan.update(sourceQueueSha256=hashlib.sha256(queue_bytes).hexdigest(), facultyReviewSha256=hashlib.sha256(review_bytes).hexdigest(),
                baselineAtlasSha256=hashlib.sha256(atlas_bytes).hexdigest(), newPreviewQueueUris=len(set(shadow.state['items']) - before),
                reopenedRetainedSources=len(reopened), oldRetentionReceiptsPreserved=True, scopePolicyPassed=True,
                exactStoredUriChecksPassed=True, unsafeQueueKeyCollisions=[],
                originalAdditionalSourceContextsPreserved=config['sources'][:len(original)] == original,
                malformedSourceContextsWhollyRetired=len(retired) if args.apply else 0,
                configuredSourceContextsAfterApply=len(config['sources']),
                configuredNewSourceContexts=len(added) if args.apply else 0, appliedToConfiguration=args.apply, liveQueueWritten=False,
                activation='Next natural collector child batch through its ordinary lease, cache, robots and shared host scheduling; do not interrupt the healthy collector.')
    destination = ROOT / 'data/ucsd' / PLAN_NAME if args.apply else output / PLAN_NAME
    atomic_json(destination, plan)
    print(json.dumps({key: plan[key] for key in ['counts', 'newPreviewQueueUris', 'reopenedRetainedSources', 'configuredNewSourceContexts', 'appliedToConfiguration', 'liveQueueWritten']}))


if __name__ == '__main__':
    main()
