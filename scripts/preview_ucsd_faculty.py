#!/usr/bin/env python3
"""Replay saved Profiles qualifications into an isolated, incomplete preview.

Reads the live checkpoint atomically but writes only a separate cache queue,
faculty review and an explicitly non-final receipt. No network requests, final
capture export or served atlas replacement are performed here.
"""
from __future__ import annotations

import copy
import argparse
import datetime as dt
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from collect_ucsd_coverage import Queue, replay_profile_qualifications, url_key, REQUIRED_SOURCE_FILES
from review_ucsd_coverage import faculty_review
from queue_resource_keys import normalize_queue_keys

ROOT = Path(__file__).resolve().parents[1]


def main(argv=()):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--queue-preview', type=Path, help='Review a fixed actual-capture snapshot instead of the changing live checkpoint')
    args = cli.parse_args(argv)
    cache = ROOT / '.cache/coverage-20261016'
    source_path = args.queue_preview or cache / 'queue.json'
    live_bytes = source_path.read_bytes()
    live = json.loads(live_bytes)
    process_at_start = json.loads((cache / 'process.json').read_text())
    output = cache / 'profile-qualification-preview'
    output.mkdir(exist_ok=True)
    shadow = Queue(output / 'queue.json')
    shadow.state = copy.deepcopy(live)
    normalize_queue_keys(shadow.state)
    sources = {url_key(item['url']): item for item in live['items'].values() if item.get('fetch', {}).get('status') == 'ok'
               and item['fetch'].get('finalUrl', '').startswith('https://profiles.ucsd.edu/')}
    hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for item in sources.values()
              for path in [cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.' + suffix) for suffix in ['html', 'json']] if path.exists()}
    before = Counter(item.get('profileEligibility', {}).get('status', 'not_assessed') for item in sources.values())
    replay_profile_qualifications(shadow, cache)
    # A current qualification version skips replay (and its internal save).
    # Still persist this newly read checkpoint, rather than referencing an old
    # preview queue beside a freshly generated faculty review.
    shadow.save()
    after = Counter(shadow.state['items'][key].get('profileEligibility', {}).get('status', 'not_assessed') for key in sources)
    after_by_request = {item['url']: item for item in shadow.state['items'].values()}
    changed_observations = [item['url'] for item in live['items'].values()
                            if item.get('fetch') != after_by_request[item['url']].get('fetch')]
    changed_files = [path for path, digest in hashes.items() if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest]
    print(json.dumps({'sources': len(sources), 'eligibilityBefore': dict(before), 'eligibilityAfter': dict(after)}), flush=True)
    faculty = faculty_review(shadow.state, json.loads((ROOT / 'data/research-atlas.json').read_text()), cache)
    (output / 'faculty-review.json').write_text(json.dumps(faculty, ensure_ascii=False, indent=2) + '\n')
    receipt = {'at': dt.datetime.now(dt.timezone.utc).isoformat(), 'isFinalExport': False, 'liveQueueWritten': False, 'wireRequests': 0,
               'sourceQueueCheckpointAt': live.get('updatedAt'), 'sourceQueueReadSha256': hashlib.sha256(live_bytes).hexdigest(),
               'sourceQueuePath': str(source_path.resolve()), 'sourceQueueInputIsLive': source_path.resolve() == (cache / 'queue.json').resolve(),
               'previewQueuePath': str((output / 'queue.json').resolve()), 'sourceCaptureCount': len(sources),
               'previewQueueSha256': hashlib.sha256((output / 'queue.json').read_bytes()).hexdigest(),
               'qualificationReplayPerformed': live.get('profileQualificationVersion', 0) < 2,
               'sourceEligibilityBefore': dict(before), 'sourceEligibilityAfter': dict(after), 'replay': shadow.state.get('profileQualificationReplay'),
               'changedSourceObservations': changed_observations, 'changedSourceFiles': changed_files, 'sourceFilesChecked': len(hashes),
               'facultyPreview': faculty['coverage'], 'byDepartment': dict(Counter(p['department'] for p in faculty['professors'])),
               'namedProfileLimitations': [shadow.state['items'][key]['profileEligibility'] for key in sources
                                          if shadow.state['items'][key].get('profileEligibility', {}).get('status') in {'profile_identity_heading_requires_review', 'missing_identity_or_appointment_table'}],
               'activeCollectorHashAtStart': process_at_start['networkCoordination']['collectorCodeSha256'],
               'requiredNextCollectorHash': hashlib.sha256((ROOT / 'scripts/collect_ucsd_coverage.py').read_bytes()).hexdigest(),
               'requiredNextSourceHashes': {name: hashlib.sha256((ROOT / 'scripts' / name).read_bytes()).hexdigest()
                                            for name in REQUIRED_SOURCE_FILES},
               'activation': 'Version-2 qualification is active in the live checkpoint.' if live.get('profileQualificationVersion', 0) >= 2 else 'Automatic cache-only replay loads at the next natural child batch under its collector lease. The healthy live batch is left running.',
               'limitations': ['Incremental review with pending sources, not final acceptance of all proposed faculty.',
                               'An absent faculty title or partial heading is a captured-source limitation, not proof of non-faculty status.']}
    (ROOT / 'docs/operations/profile-qualification-repair-20261016.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'faculty': faculty['coverage'], 'changedObservations': len(changed_observations), 'changedFiles': len(changed_files)}), flush=True)
    raise SystemExit(1 if changed_observations or changed_files else 0)


if __name__ == '__main__':
    main(sys.argv[1:])
