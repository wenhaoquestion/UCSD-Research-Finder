"""Publish committed recovery checkpoints into the authorized desktop checkout."""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time

SOURCE = Path('/private/tmp/ucsd-research-20261016')
DESKTOP = Path('/Users/question/Desktop/research web')
PREFIX = 'data/ucsd/recovery-backfill-20261017/'
DATA = 'data/research-atlas.json'
RECEIPT = DESKTOP / 'docs/operations/desktop-recovery-integration-20261017.json'
QUALITY = DESKTOP / 'data/quality/refresh-report.json'
sys.path.insert(0, str(DESKTOP / 'scripts'))
from rebuild_verified_atlas import profile


def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def atomic(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name('.' + path.name + '.integration-pending')
    with pending.open('wb') as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(pending, path)


def update_block(path, body):
    begin = '<!-- recovery-integration:start -->'
    end = '<!-- recovery-integration:end -->'
    text = path.read_text()
    block = begin + '\n' + body + '\n' + end
    if begin in text:
        left, tail = text.split(begin, 1)
        _, right = tail.split(end, 1)
        text = left + block + right
    else:
        first, rest = text.split('\n', 1)
        text = first + '\n\n' + block + '\n' + rest
    atomic(path, text.encode())


def sync():
    ref = git('rev-parse', 'HEAD').decode().strip()
    raw = git('show', ref + ':' + PREFIX + 'candidate.json')
    digest = sha(raw)
    progress = json.loads(git('show', ref + ':docs/operations/recovery-backfill-progress-20261017.json'))
    checkpoint = progress['latestBatch']
    if checkpoint['candidateSha256'] != digest:
        raise ValueError('Committed candidate and checkpoint hash differ')
    reviewed_hold = (checkpoint.get('mode') == 'identity_hold_review'
                     and checkpoint.get('allBaselineWholeRecordsUnchanged') is True
                     and checkpoint.get('allQuarantinedWholeRecordsArchived') is True)
    if checkpoint['idAndForeignKeyValidation'] != 'passed' or not (checkpoint['existingWholeRecordsUnchanged'] or reviewed_hold):
        raise ValueError('Checkpoint preservation/schema validation missing')
    previous = json.loads(RECEIPT.read_text()) if RECEIPT.exists() else None
    baseline = git('show', 'e9a4326:' + DATA)
    expected = previous['servedSha256'] if previous else sha(baseline)
    actual = sha((DESKTOP / DATA).read_bytes())
    if actual != expected:
        raise ValueError('Desktop data changed outside integration; preserved without overwriting')
    state = json.loads((SOURCE / 'docs/operations/recovery-pipeline-20261017.json').read_text())
    state_brief = {k: state.get(k) for k in ['pipelineId', 'status', 'cursor', 'manifestRows', 'remainingManifestRows']}
    quality_raw = QUALITY.read_bytes()
    expected_quality = previous.get('qualityReportSha256') if previous else None
    if expected_quality and sha(quality_raw) != expected_quality:
        raise ValueError('Desktop quality report changed outside integration; preserved without overwriting')
    if previous and digest == previous.get('sourceCandidateSha256') and previous.get('pipeline') == state_brief and expected_quality:
        return state['status']
    dataset = json.loads(raw)
    # Preserve retired baseline lab bookmarks without adding invalid entities back to lab counts.
    active_labs = {x['id'] for x in dataset['labs']}
    lab_aliases = {a for x in dataset['labs'] for a in x.get('aliasIds', [])}
    retired = []
    for old in json.loads(baseline)['labs']:
        if old['id'] in active_labs or old['id'] in lab_aliases:
            continue
        retired.append({
            'id': old['id'], 'label': old['labName'], 'department': old['department'],
            'institution': old['institution'], 'sourceUrl': old['labWebsiteUrl'],
            'sourceUrls': old['sourceUrls'], 'classification': 'historical_record_not_active_lab',
            'reason': 'Historical baseline entry retired from the recovered active lab set; retained for old bookmarks and complete historical evidence, without a new entity or URL verification claim.',
            'previousLabObservations': [{'scope': 'original_record', 'record': old}]
        })
    dataset.setdefault('recovery', {})['retiredLabResources'] = retired
    served_raw = (json.dumps(dataset, ensure_ascii=False, indent=2) + '\n').encode()
    served_digest = sha(served_raw)
    pending = DESKTOP / 'data/.recovery-validation.json'
    atomic(pending, served_raw)
    try:
        subprocess.run(['/opt/homebrew/bin/python3', 'scripts/validate_data.py', str(pending)], cwd=DESKTOP, check=True)
    finally:
        pending.unlink(missing_ok=True)
    paths = git('ls-tree', '-rz', '--name-only', ref, '--', PREFIX).decode().split('\0')
    artifact_count = 0
    for rel in paths:
        if not rel or rel == PREFIX + 'candidate.json':
            continue
        content = git('show', ref + ':' + rel)
        target = DESKTOP / rel
        if target.exists():
            if target.read_bytes() == content:
                artifact_count += 1
                continue
            # Upgrade a task-owned tool only if the desktop still matches its exact previous source commit.
            previous_tool_matches = (rel.startswith(PREFIX + 'tools/') and previous
                                     and target.read_bytes() == git('show', previous['sourceCommit'] + ':' + rel))
            if not rel.endswith('/state.json') and not previous_tool_matches:
                raise ValueError('Existing desktop recovery artifact differs: ' + rel)
        atomic(target, content)
        artifact_count += 1
    if sha((DESKTOP / DATA).read_bytes()) != expected:
        raise ValueError('Desktop data changed during validation; preserved without overwriting')
    atomic(DESKTOP / DATA, served_raw)
    subprocess.run(['/opt/homebrew/bin/python3', 'scripts/validate_data.py'], cwd=DESKTOP, check=True)
    professors, labs = len(dataset['professors']), len(dataset['labs'])
    quality = json.loads(quality_raw)
    quality.setdefault('historicalReportGeneratedAt', quality.get('generatedAt'))
    quality['generatedAt'] = dataset['generatedAt']
    quality['after'] = dataset['dataQuality']['coverage']
    departments = sorted({x['department'] for group in ['professors', 'labs'] for x in dataset[group]})
    quality['departments'] = {department: profile({
        group: [x for x in dataset[group] if x['department'] == department]
        for group in ['professors', 'labs']
    }) for department in departments}
    quality['recoveryIntegration'] = {
        'sourceCandidateSha256': digest, 'servedSha256': served_digest,
        'latestBatchId': checkpoint['batchId'], 'pipeline': state_brief,
        'coverageScope': 'after and departments reflect current served arrays; before, remediationCounts, sourceCheckStatuses, quarantinedRecords and captureCoverage retain historical report accounting.',
        'fieldDatesPreserved': True, 'originalLostRawCorpusRestored': False,
    }
    new_quality_raw = (json.dumps(quality, ensure_ascii=False, indent=2) + '\n').encode()
    atomic(QUALITY, new_quality_raw)
    receipt = {
        'integratedAt': dt.datetime.now(dt.timezone.utc).isoformat(),
        'canonicalDataPath': DATA, 'servedSha256': served_digest,
        'sourceCandidateSha256': digest, 'retiredBaselineLabResources': len(retired),
        'qualityReportSha256': sha(new_quality_raw),
        'professors': professors, 'labs': labs,
        'sourceCommit': ref, 'sourceCandidatePath': str(SOURCE / PREFIX / 'candidate.json'),
        'latestBatchId': checkpoint['batchId'], 'pipeline': state_brief,
        'artifactFilesCopied': artifact_count, 'schemaAndReferences': 'passed',
        'desktopBaselineWasUnmodified': True,
        'originalLostRosterAndRawCorpusRecovered': False,
        'historicalSourceDatesPreserved': True,
        'refreshInstruction': 'Claude and the local website must read data/research-atlas.json. Counts are array lengths; historical reports below may describe older snapshots.'
    }
    atomic(RECEIPT, (json.dumps(receipt, ensure_ascii=False, indent=2) + '\n').encode())
    update_block(DESKTOP / 'README.md',
        f'当前本地正式数据：**{professors:,} 位教授、{labs:,} 个实验室**。Claude 与网站统一读取 `data/research-atlas.json`。\n\n'
        '恢复批次存档与证据在 `data/ucsd/recovery-backfill-20261017/`；同步来源、SHA 和批次状态见 '
        '`docs/operations/desktop-recovery-integration-20261017.json`。历史来源日期保留；恢复数量不代表所有字段均已重新核验。')
    update_block(DESKTOP / 'docs/DATA_QUALITY_REPORT.md',
        f'当前正式数据已整合恢复批次：**{professors:,} 位教授 / {labs:,} 个实验室**。\n\n'
        '当前计数与字段覆盖请读取 `data/research-atlas.json` 的数组及 `dataQuality.coverage`；'
        '同步回执见 `docs/operations/desktop-recovery-integration-20261017.json`。'
        '**以下内容保留为 2026-10-07 的历史质量报告，不代表当前记录数量。**')
    print(json.dumps({'integrated': True, 'professors': professors, 'labs': labs, 'batch': checkpoint['batchId'], 'pipeline': state_brief}), flush=True)
    return state['status']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--follow', action='store_true')
    parser.add_argument('--follow-seconds', type=int, default=1800)
    args = parser.parse_args()
    if not 1 <= args.follow_seconds <= 10800:
        parser.error('--follow-seconds must be 1..10800')
    deadline = time.monotonic() + args.follow_seconds
    while True:
        status = sync()
        if not args.follow or status != 'running':
            print('SYNC_FINISHED ' + status, flush=True)
            break
        if time.monotonic() > deadline:
            raise TimeoutError('Bounded desktop integration watcher ended; latest checkpoint is saved')
        time.sleep(15)
