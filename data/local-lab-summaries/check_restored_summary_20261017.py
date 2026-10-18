"""Minimal offline recovery check; does not refresh data or restart collection.

Preserves the recovered exports and all historical receipts. Writes only a new
recovery report and a content-hash-based local evidence resolution sidecar.
"""
import collections
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import local_lab_summaries as m

P = m.OUT
HEAD = '5917f0a7c4b5e3feb0cae13e44baa3fe7053dfe9'
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
manifest = m.read(P / 'manifest.json')
checkpoint = m.read(P / 'checkpoint.json')
summaries = [json.loads(line) for line in (P / 'summaries.jsonl').read_text().splitlines()]
urls = [json.loads(line) for line in (P / 'url-verification.jsonl').read_text().splitlines()]
ids = [item['labId'] for item in manifest['items']]
assert len(ids) == len(set(ids)) == len(summaries) == len(urls) == 916
assert ids == [row['labId'] for row in summaries] == [row['labId'] for row in urls]
assert manifest['baselineCount'] == 868 and len(manifest['imports']) == 48
all_evidence = []
for summary, url in zip(summaries, urls):
    lid = summary['labId']
    raw = m.read(P / 'records' / (lid + '.json'))
    packet = m.read(P / 'packets' / (lid + '.json'))
    assert (summary, url) == m.hydrate(raw, packet), lid
    all_evidence.extend(dict(e, labId=lid) for e in summary['evidence'])
counts = dict(collections.Counter(row['status'] for row in summaries))
assert counts == checkpoint['counts'] == {'supported': 766, 'partial': 60, 'unresolved': 90}
assert sum(row['status'] == 'supported' and row['identity']['entityType'] in {'lab', 'research_group'}
           for row in summaries) == checkpoint['supportedLabOrGroupSummaries'] == 752
assert sum(row['canCountAsVerifiedLabGroupURL'] for row in urls) == checkpoint['verifiedAcceptedLabGroupURLCount'] == 600

# Existing committed copies are indexed by bytes, not by URL equivalence.
# A saved copy is not a new capture and does not alter any observation date.
html_by_sha = collections.defaultdict(list)
for path in P.rglob('*.html'):
    html_by_sha[sha(path)].append(str(path))
for values in html_by_sha.values():
    values.sort()
resolutions, unavailable, direct_mismatches = [], [], []
direct_paths = {}
for evidence in all_evidence:
    path, expected = evidence.get('cachePath'), evidence.get('bodySha256')
    if not path or not expected:
        continue
    original = Path(path)
    if original.is_file():
        if path not in direct_paths:
            direct_paths[path] = sha(original)
        actual = direct_paths[path]
        if actual != expected:
            direct_mismatches.append({'labId': evidence['labId'], 'sourceId': evidence['sourceId'],
                                      'path': path, 'expected': expected, 'actual': actual})
        continue
    candidates = html_by_sha.get(expected, [])
    item = {'labId': evidence['labId'], 'sourceId': evidence['sourceId'],
            'sourceUrl': evidence['sourceUrl'], 'sourceObservedAt': evidence['observedAt'],
            'originalCachePath': path, 'bodySha256': expected}
    if candidates:
        resolutions.append(dict(item, recoveredBodyPath=candidates[0],
                                resolution='saved_byte_identical_body_only_not_new_capture'))
    else:
        unavailable.append(item)
assert not direct_mismatches

handoff_paths, decision_paths = {}, {}
for item in manifest['imports']:
    admission = item['reviewedHandoff']
    path = Path(admission['sourceFile'])
    assert sha(path) == admission['sourceSha256']
    handoff_paths[str(path)] = admission['sourceSha256']
    decision = Path(admission['decisionArtifactPath'])
    assert sha(decision) == admission['decisionArtifactSha256']
    decision_paths[str(decision)] = admission['decisionArtifactSha256']
last = manifest['imports'][-1]['reviewedHandoff']
last_handoff = m.read(last['sourceFile'])
assert len(last_handoff['labs']) == 48
assert {row['id'] for row in last_handoff['labs']} == {row['labId'] for row in manifest['imports']}
latest_mutable = Path(last['originalCollectorHandoffPath'])
old_package = Path('/tmp/ucsd-final-acceptance-20261017/UCSD-Local-Accepted-Subset-20261017.zip')
last_handoff_bodies = []
for source in last_handoff['sourceManifest']:
    expected = source.get('bodySha256')
    original = Path(source['cachePath']) if source.get('cachePath') else None
    saved = html_by_sha.get(expected, [])
    direct = bool(original and original.is_file() and sha(original) == expected)
    last_handoff_bodies.append({'sourceUrl': source['sourceUrl'],
                               'sourceObservedAt': source['observedAt'],
                               'bodySha256': expected,
                               'originalCachePath': str(original) if original else None,
                               'availableBodyPath': str(original) if direct else saved[0] if saved else None,
                               'bodyAvailable': direct or bool(saved)})
historical_validation = m.read(P / 'validation.json')
body_recovery = m.read(P / 'PERSISTENT-EVIDENCE-BYTE-RECOVERY-20261017.json')
result = {
    'schemaVersion': 1, 'checkedAt': m.now(), 'restoredFromCommit': HEAD,
    'restorationMethod': 'Original retained worktree index; checkout-index --all; no reset, prune, fetch or collector mutation.',
    'freshRecoveryChecks': {'readableSummaryRecords': 916, 'readableUrlRecords': 916,
                           'rawAndPacketHydrationsMatchExistingExports': 916,
                           'stableUniqueIdsAndOrderingMatch': True,
                           'literalPacketReferencesAndOriginalDatesPreserved': True,
                           'counts': counts, 'supportedLabOrGroupSummaries': 752,
                           'verifiedHistoricalOriginalLabGroupURLs': 600},
    'evidenceAvailability': {
        'evidenceQuoteEntries': len(all_evidence),
        'uniqueLabSourceAssociations': len({(e['labId'], e['sourceId']) for e in all_evidence}),
        'existingReferencedBodyPathsVerified': len(direct_paths),
        'savedHtmlFilesAvailable': sum(len(v) for v in html_by_sha.values()),
        'uniqueSavedHtmlBodyHashes': len(html_by_sha),
        'missingOriginalPathsResolvedByExactBodyHashEntries': len(resolutions),
        'missingRawBodyEntriesWithoutSavedCopy': len(unavailable),
        'missingRawBodySourceAssociations': len({(e['labId'], e['sourceId']) for e in unavailable}),
        'missingRawBodyFileReferences': len({e['originalCachePath'] for e in unavailable}),
        'missingUniqueRawBodyHashes': len({e['bodySha256'] for e in unavailable}),
        'missingRawBodyAffectedRecords': len({e['labId'] for e in unavailable}),
        'resolvedOriginalMissingSourceAssociations': len({(e['labId'], e['sourceId']) for e in resolutions}),
        'historicalFieldsWithoutRawBodyHashEntries': sum(not e.get('bodySha256') for e in all_evidence),
        'availableBodyHashMismatches': direct_mismatches,
        'unavailableBodies': unavailable,
        'sourcePacketTextSurvivesRegardlessOfRawBodyAvailability': True},
    'reviewedHandoffRecovery': {'baselineCount': 868, 'approvedIncrementCount': 48,
                               'frozenHandoffFilesVerified': handoff_paths,
                               'frozenDecisionFilesVerified': decision_paths,
                               'lastApprovedHandoffPath': last['sourceFile'],
                               'lastApprovedHandoffSha256': last['sourceSha256'],
                               'lastApprovedHandoffGeneratedAt': last['generatedAt'],
                               'lastApprovedSourceManifestCount': len(last_handoff['sourceManifest']),
                               'lastApprovedRawBodyRowsAvailable': sum(x['bodyAvailable'] for x in last_handoff_bodies),
                               'lastApprovedRawBodyRowsMissing': sum(not x['bodyAvailable'] for x in last_handoff_bodies),
                               'lastApprovedRawBodyResolution': last_handoff_bodies,
                               'collectorMutableHandoffCurrentlyExists': latest_mutable.is_file(),
                               'collectorMutableHandoffCurrentSha256': sha(latest_mutable) if latest_mutable.is_file() else None,
                               'mutableHandoffNotAdmittedOrModified': True},
    'lossBoundary': {'collectorRawResponsesDirectoryExists': Path('/tmp/ucsd-research-20261016/.cache/coverage-20261016/responses').is_dir(),
                     'historicalAcceptanceZipExists': old_package.is_file(),
                     'historicalAcceptanceZipPath': str(old_package),
                     'historicalZipNotRecreatedOrCRCRechecked': True,
                     'uncommittedOrIgnoredFilesNotRestorableFromGitUnlessSeparatelySaved': True,
                     'oldProcessLeaseOrCoordinationReceiptsNotUsedAsCurrentState': True,
                     'deletionCauseAndExactTimeNotIndependentlyEstablished': True},
    'persistentBackupSearch': {'checkedFilenameScope': ['Desktop', 'Documents', 'Downloads'],
                              'separateMatchingAcceptanceZipOrBackupFound': False,
                              'durableRecoveryAuthority': '/Users/question/Desktop/research web/.git'},
    'persistentBodyBackupSearch': body_recovery,
    'historicalValidationReceipt': {'path': str(P / 'validation.json'),
                                    'sha256': sha(P / 'validation.json'),
                                    'originalCheckedAt': historical_validation.get('checkedAt'),
                                    'rerunAfterRecovery': False},
    'preservedExportSha256': {name: sha(P / name) for name in
                             ['summaries.jsonl', 'url-verification.jsonl', 'manifest.json', 'checkpoint.json', 'validation.json']},
    'networkRequests': 0, 'collectionOrNetworkWorkersStarted': 0, 'collectorWrites': 0,
    'historicalTestsOrLiveChecksRerun': False,
    'scope': 'Fresh offline schema/reference/loading recovery checks only. Historical evidence and validation receipts keep their original dates and are not new observations.'}
m.atomic(P / 'RESTORED-EVIDENCE-RESOLUTION-20261017.json', {
    'schemaVersion': 1, 'createdAt': m.now(), 'newCapture': False,
    'originalRecordsPacketsAndObservationTimesUnchanged': True,
    'items': resolutions})
m.atomic(P / 'TEMP-DIRECTORY-RECOVERY-20261017.json', result)
print(json.dumps({'loaded': 916, 'counts': counts, 'evidenceAvailability': {
    k: v for k, v in result['evidenceAvailability'].items() if k != 'unavailableBodies'},
    'lastApprovedHandoffSha256': last['sourceSha256'], 'lossBoundary': result['lossBoundary']}, ensure_ascii=False))
