#!/usr/bin/env python3
"""Refresh dated outcomes for every original unverified case; no network I/O."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from collect_ucsd_coverage import ROOT, atomic_json, url_key
from queue_resource_keys import normalize_queue_keys, rebind_decisions
from refresh_labs import now


def report(cache):
    source = ROOT / 'data/ucsd/lab-expansion-candidates.json'
    original = json.loads(source.read_text())
    candidates = [c for c in original['candidates'] if c['status'] == 'unverified']
    queue = json.loads((cache / 'queue.json').read_text())
    normalize_queue_keys(queue)
    decisions = rebind_decisions(json.loads((ROOT / 'data/ucsd/coverage-20261016-decisions.json').read_text()), queue)['labs']
    reviews = json.loads((ROOT / 'data/ucsd/coverage-20261016-original-candidate-reviews.json').read_text())['reviews']
    if set(reviews) != {c['candidate_id'] for c in candidates}:
        raise ValueError('Every original unverified case must have exactly one review disposition')
    rows = []
    for candidate in candidates:
        cid = candidate['candidate_id']
        items = [i for i in queue['items'].values() if any(c.get('candidateId') == cid for c in i['contexts'])]
        # Some old cases stored a skipped Profiles target only in pageStatus.
        # Join that actual historical URL; never invent a profile slug.
        historical_target = (candidate.get('pageStatus') or {}).get('url', '')
        linked_item = queue['items'].get(url_key(historical_target)) if historical_target else None
        if linked_item and linked_item not in items:
            items.append(linked_item)
        outcome = dict(reviews[cid])
        decision = decisions.get(url_key(candidate.get('labWebsiteUrl', '')), {})
        if decision.get('action') in {'accept', 'alias', 'accept_shared_entities'}:
            outcome = {'status': decision['action'] + '_reviewed_pending_completed_export', 'reason': decision['reason'], 'decision': decision}
        checks = [{'requestedUrl': i['url'], 'queueState': i['state'], 'attempts': i['attempts'], 'fetch': i.get('fetch'), 'attemptHistory': i.get('attemptHistory', [])} for i in items]
        rows.append({'candidateId': cid, 'originalLabName': candidate['labName'], 'department': candidate['department'],
                     'originalStatus': candidate['status'], 'originalObservedAt': candidate.get('observedAt'),
                     'originalReason': candidate['reason'], 'originalWebsiteUrl': candidate.get('labWebsiteUrl'),
                     'outcome': outcome, 'sourceChecks': checks,
                     'pendingSourceUrls': [i['url'] for i in items if i['state'] in {'pending', 'running'}]})
    result = {'schemaVersion': 1, 'generatedAt': now(), 'collectionState': queue['collectionState'], 'queueCheckpointAt': queue['updatedAt'],
              'originalArtifact': str(source.relative_to(ROOT)), 'originalArtifactSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'originalGeneratedAt': original['generatedAt'], 'originalUnverifiedCases': len(candidates), 'casesAccountedFor': len(rows),
              'outcomeCounts': dict(Counter(r['outcome']['status'] for r in rows)), 'cases': rows,
              'policy': 'Case counts are not individual laboratory counts: some original cases bundle several people/entities. Pending export is not a published addition. Failed sources do not establish absence or closure; source observation dates are preserved. Refresh this checkpoint after the eligible queue completes.'}
    atomic_json(ROOT / 'data/ucsd/coverage-20261016-original-candidate-outcomes.json', result)
    print(json.dumps({k: result[k] for k in ['collectionState', 'casesAccountedFor', 'outcomeCounts']}, indent=2))


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--cache', type=Path, default=ROOT / '.cache/coverage-20261016')
    report(cli.parse_args().cache)
