#!/usr/bin/env python3
"""Schedule exact public roster links whose own academic title is not captured.

Only append source contexts after validating the saved directory's own named
link. Discovery never establishes academic rank, department appointment, person
identity, primary-URI equivalence or current employment. The healthy collector
loads these contexts at a natural batch boundary; its live queue is never edited.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import urllib.parse
from collections import Counter
from pathlib import Path

from collect_ucsd_coverage import Queue, atomic_json, now, official, safe_url, url_key
from collection_scope import ScopePolicy
from faculty_profile_bindings import captured_source
from plan_ucsd_faculty_identity_sources import preserve_plan_history
from refresh_faculty_directories import identity_name, individual_profile
from refresh_labs import DOM, links
from review_ucsd_coverage import credential_free_name

ROOT = Path(__file__).resolve().parents[1]
PLAN_NAME = 'faculty-title-source-plan-20261016.json'
CARD_CLASSES = {'faculty-profile', 'profile-listing-card', 'profile-container',
                'faculty-member', 'profile-window', 'col-md-3', 'faculty-card'}


def own_named_link(node, label, name):
    wanted = identity_name(credential_free_name(name))
    if len(wanted.split()) < 2:
        return False
    if identity_name(credential_free_name(label)) == wanted:
        return True
    # Some rosters put "UCSD Profile" beside the person's name in one card.
    if label not in {'UCSD Profile', 'UCSD Profiles', 'Research Profile', 'Profile'}:
        return False
    parent = node.parent
    while parent is not None:
        if parent.tag == 'tr' or CARD_CLASSES.intersection(parent.attrs.get('class', '').split()):
            return bool(re.search(r'\b' + re.escape(wanted) + r'\b', identity_name(parent.text())))
        parent = parent.parent
    return False


def prepare_plan(review, queue, cache):
    by_request = {item['url']: item for item in queue['items'].values()}
    by_observation = {}
    for item in queue['items'].values():
        meta = item.get('fetch', {})
        if meta.get('status') == 'ok':
            by_observation.setdefault((meta.get('finalUrl'), meta.get('observedAt')), []).append(item)
    parsed, cases, requested = {}, {}, {}
    for hold in review['uncertainListings']:
        if hold.get('reason') != 'explicit_academic_title_not_observed':
            continue
        row = hold['listing']; uri = row.get('profileUrl', '')
        observation = {k: copy.deepcopy(row.get(k)) for k in
                       ['name', 'department', 'listedRole', 'sourceUrl', 'observedAt', 'profileUrl', 'evidence']}
        fingerprint = hashlib.sha256(json.dumps(observation, sort_keys=True).encode()).hexdigest()[:20]
        item = by_request.get(uri)
        case = {'caseId': 'title-source-' + fingerprint, 'listingObservation': observation,
                'requestedTransportUri': uri, 'originalSourceQueueState': item['state'] if item else 'not_queued',
                'academicQualificationEstablished': False, 'personIdentityEstablished': False}
        cases[case['caseId']] = case
        if not uri:
            case['reviewStatus'] = 'no_profile_uri_supplied'; continue
        if safe_url(uri) != uri or not official(uri) or not individual_profile(uri):
            case['reviewStatus'] = 'not_an_exact_individual_campus_uri'; continue
        if item and item.get('fetch', {}).get('status') == 'ok':
            try:
                capture, _ = captured_source(item, cache)
                case['existingCapture'] = capture
                case['reviewStatus'] = 'captured_source_requires_scoped_title_review'
            except ValueError:
                case['reviewStatus'] = 'positive_receipt_without_verified_body_requires_capture_repair'
            continue
        if item and item['state'] not in {'retained_prior_evidence', 'pending', 'running'}:
            case['reviewStatus'] = 'existing_source_failure_or_scope_decision_retained_without_reset'; continue
        if item and item['state'] in {'pending', 'running'}:
            case['reviewStatus'] = 'already_in_active_source_queue'; continue
        key = (row['sourceUrl'], row['observedAt'])
        if key not in parsed:
            candidates = by_observation.get(key, [])
            candidates = sorted(candidates, key=lambda i: i['url'] != row['sourceUrl'])
            captures = []
            for source in candidates:
                base, markup = captured_source(source, cache)
                captures.append((base, list(links(DOM(markup).main(), base['sourceUrl']))))
            parsed[key] = captures
        found = []
        for base, anchors in parsed[key]:
            for node, label, target in anchors:
                literal = urllib.parse.urljoin(base['sourceUrl'], node.attrs.get('href', ''))
                if (target == uri and safe_url(literal) == uri and own_named_link(node, label, row['name'])
                        and row.get('evidence', {}).get('sourceUrl') == row['sourceUrl']
                        and row.get('evidence', {}).get('observedAt') == row['observedAt']):
                    found.append({**base, 'nameAsListed': row['name'], 'rawHref': node.attrs['href'],
                                  'linkText': label, 'resolvedLinkUri': literal, 'requestedTransportUri': uri})
        if not found:
            case['reviewStatus'] = 'exact_named_link_not_verified_in_dated_directory_capture'; continue
        case['discoveryCapture'] = found[0]
        case['reviewStatus'] = 'exact_linked_source_check_proposed'
        source_key = (uri, row['department'], row['sourceUrl'])
        source = requested.setdefault(source_key, {'url': uri, 'department': row['department'],
            'kind': 'profile_identity_review', 'professorId': '', 'sourceUrl': row['sourceUrl'],
            'depth': 2, 'identityDepth': 2, 'qualificationSourcePlan': PLAN_NAME, 'qualificationSourceCaseIds': [],
            'scopeNote': 'Read only the exact individual campus URI explicitly linked in its dated faculty roster. This schedules an identity/field source check, not qualification, rank, affiliation, employment, alias, URI equivalence or person merging.'})
        source['qualificationSourceCaseIds'].append(case['caseId'])
    return {'schemaVersion': 1, 'generatedAt': now(), 'isFinalQualificationReview': False,
            'wireRequests': 0, 'cases': list(cases.values()),
            'counts': {'reviewCases': len(cases), 'reviewCaseStates': dict(Counter(c['reviewStatus'] for c in cases.values())),
                       'sourceContexts': len(requested), 'uniqueRequestUris': len({s['url'] for s in requested.values()})}}, list(requested.values())


def source_key(source):
    return tuple(source.get(k, default) for k, default in
                 [('url', ''), ('department', ''), ('kind', 'directory'), ('sourceUrl', ''),
                  ('professorId', ''), ('depth', 0), ('identityDepth', None)])


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--apply', action='store_true', help='Append validated contexts; never modify the live queue')
    args = cli.parse_args()
    cache = ROOT / '.cache/coverage-20261016'; preview = cache / 'profile-qualification-preview'
    queue_bytes, review_bytes = (preview / 'queue.json').read_bytes(), (preview / 'faculty-review.json').read_bytes()
    state = json.loads(queue_bytes)
    plan, sources = prepare_plan(json.loads(review_bytes), state, cache)
    plan_path = ROOT / 'data/ucsd' / PLAN_NAME
    if plan_path.exists():
        preserve_plan_history(plan, json.loads(plan_path.read_bytes()))
    # Reuse the actual ordinary admission path in an isolated shadow. This
    # checks exact keys, scope and complete old receipts without a live writer.
    shadow = Queue.__new__(Queue); shadow.state = copy.deepcopy(state)
    prior = {source['url']: copy.deepcopy(state['items'].get(url_key(source['url']))) for source in sources}
    for source in sources:
        shadow.add(source['url'], source['department'], source['kind'], source['sourceUrl'],
                   source['depth'], professor_id='', identity_depth=source['identityDepth'])
    policy = ScopePolicy(shadow.state, json.loads((ROOT / 'data/research-atlas.json').read_text()))
    for source in sources:
        item = shadow.state['items'][url_key(source['url'])]; old = prior[source['url']]
        if item['url'] != source['url'] or policy.request_reason(item):
            raise ValueError('Title source check failed exact-URI/scope preflight')
        if old:
            if any(item.get(k) != old.get(k) for k in ['attempts', 'retryAt', 'fetch']):
                raise ValueError('Title source plan cannot reset attempts, deadlines or source observations')
            if old.get('retainedEvidence') and old['retainedEvidence'] not in item.get('retainedEvidenceHistory', []):
                raise ValueError('Title source plan lost the original retained receipt')
    config_path = ROOT / 'data/ucsd/coverage-20261016-additional-sources.json'
    config = json.loads(config_path.read_bytes()); original = copy.deepcopy(config['sources'])
    keys = {source_key(s) for s in original}; added = [s for s in sources if source_key(s) not in keys]
    if args.apply:
        config['sources'].extend(added)
        atomic_json(config_path, config)
    plan.update(sourceQueueSha256=hashlib.sha256(queue_bytes).hexdigest(), facultyReviewSha256=hashlib.sha256(review_bytes).hexdigest(),
                sourceQueueCheckpointAt=state.get('updatedAt'), configuredNewSourceContexts=len(added) if args.apply else 0,
                newSourceUrisInShadow=sum(old is None for old in prior.values()),
                retainedSourceUrisReopenedInShadow=sum(old is not None and old['state'] == 'retained_prior_evidence' for old in prior.values()),
                originalAdditionalSourceContextsPreserved=config['sources'][:len(original)] == original,
                exactStoredUriChecksPassed=True, scopePolicyPassed=True, oldRetentionReceiptsPreserved=True,
                attemptsDeadlinesAndFetchObservationsUnchanged=True,
                appliedToConfiguration=args.apply, liveQueueWritten=False,
                activation='Next natural finite collector batch under its ordinary lease, cache, robots and unchanged shared host gate; do not restart the healthy child.')
    output = cache / 'faculty-title-source-plan-preview'; output.mkdir(exist_ok=True)
    atomic_json(plan_path if args.apply else output / PLAN_NAME, plan)
    print(json.dumps({key: plan[key] for key in ['counts', 'configuredNewSourceContexts', 'appliedToConfiguration', 'liveQueueWritten']}))


if __name__ == '__main__':
    main()
