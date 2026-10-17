#!/usr/bin/env python3
"""Resume finite collection batches until the queue drains or STOP is requested."""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from collections import Counter
from pathlib import Path

from collection_lock import task_lease
from collect_ucsd_coverage import ROOT, atomic_json, now


def run_batches(cache, workers=8, batch_pages=250, collector=None):
    if batch_pages < 1:
        raise ValueError('A finite positive batch size is required')
    collector = collector or ROOT / 'scripts/collect_ucsd_coverage.py'
    cache = Path(cache)
    with task_lease(cache / 'batch-runner.lock'):
        receipt = {'pid': os.getpid(), 'startedAt': now(), 'batchPages': batch_pages, 'workers': workers, 'completedBatches': 0}

        def save(status, **extra):
            receipt.update(status=status, updatedAt=now(), **extra)
            atomic_json(cache / 'batch-runner.json', receipt)

        while True:
            if (cache / 'STOP').exists():
                save('stopped_by_sentinel')
                return 0
            if (cache / 'queue.json').exists():
                queue = json.loads((cache / 'queue.json').read_text())
                states = Counter(i['state'] for i in queue['items'].values())
                if not states['pending'] and not states['running']:
                    save('eligible_queue_drained', queueStates=dict(states))
                    return 0
            save('starting_batch')
            child = subprocess.Popen([sys.executable, str(collector), '--cache', str(cache), '--workers', str(workers), '--max-pages', str(batch_pages)])
            save('collecting', collectorPid=child.pid)
            result = child.wait()
            if result:
                save('collector_failed', collectorExitCode=result)
                return result
            receipt['completedBatches'] += 1
            save('batch_checkpointed', collectorExitCode=result)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--cache', type=Path, default=ROOT / '.cache/coverage-20261016')
    cli.add_argument('--workers', type=int, default=8)
    cli.add_argument('--batch-pages', type=int, default=250)
    args = cli.parse_args()

    def stop(*_):
        args.cache.mkdir(parents=True, exist_ok=True)
        (args.cache / 'STOP').touch()

    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, stop)
    raise SystemExit(run_batches(args.cache, args.workers, args.batch_pages))


if __name__ == '__main__':
    main()
