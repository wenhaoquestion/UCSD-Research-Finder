"""Recover only exact historical body hashes from existing local backups."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import local_lab_summaries as m

P = m.OUT
before = m.read(P / 'TEMP-DIRECTORY-RECOVERY-20261017.json')
wanted = {x['bodySha256'] for x in before['evidenceAvailability']['unavailableBodies']}
destination = P / 'restored-byte-identical-evidence-20261017'
matches = {}


def save(data, origin):
    digest = hashlib.sha256(data).hexdigest()
    if digest not in wanted:
        return
    path = destination / (digest + '.html')
    if not path.exists():
        destination.mkdir(exist_ok=True)
        fd, temp = tempfile.mkstemp(dir=destination)
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    matches.setdefault(digest, {'bodySha256': digest, 'restoredBodyPath': str(path),
                               'bytes': len(data), 'savedCopies': []})['savedCopies'].append(origin)


main_cache = Path('/Users/question/Desktop/research web/.cache')
files = list(main_cache.rglob('*.html'))
for path in files:
    save(path.read_bytes(), {'kind': 'existing_persistent_cache_bytes', 'path': str(path)})

head = subprocess.run(['git', 'ls-tree', '-r', '5917f0a7c4b5e3feb0cae13e44baa3fe7053dfe9'],
                      cwd=ROOT, check=True, capture_output=True, text=True).stdout
known = {line.split()[2] for line in head.splitlines()}
objects = subprocess.run(['git', 'rev-list', '--objects', '--all'], cwd=ROOT,
                         check=True, capture_output=True, text=True).stdout
candidates = {}
for line in objects.splitlines():
    if ' ' not in line:
        continue
    oid, path = line.split(' ', 1)
    if oid not in known and path.lower().endswith(('.html', '.htm', '.zip')):
        candidates[oid] = path
for oid, path in candidates.items():
    data = subprocess.run(['git', 'cat-file', 'blob', oid], cwd=ROOT,
                          check=True, capture_output=True).stdout
    save(data, {'kind': 'existing_committed_git_blob', 'gitBlob': oid, 'historicalPath': path})
report = {'schemaVersion': 1, 'restoredAt': m.now(),
          'inputRecoveryCheckAt': before['checkedAt'],
          'missingUniqueBodyHashesBefore': len(wanted),
          'persistentMainCacheHtmlCandidatesRead': len(files),
          'otherCommittedHtmlOrZipBlobsRead': len(candidates),
          'restoredUniqueBodyHashes': len(matches),
          'restoredBytes': sum(x['bytes'] for x in matches.values()),
          'items': list(matches.values()),
          'scope': 'Exact recorded body SHA256 matches only; copied bytes are historical evidence, not new captures. Packet URLs, source dates, original request/redirect receipts and IDs are unchanged.',
          'collectorOrMainWorkingTreeWrites': 0, 'networkRequests': 0,
          'uncommittedRecoveryOrLostFoundScanAttempted': False}
m.atomic(P / 'PERSISTENT-EVIDENCE-BYTE-RECOVERY-20261017.json', report)
print(json.dumps({k: v for k, v in report.items() if k != 'items'}))
