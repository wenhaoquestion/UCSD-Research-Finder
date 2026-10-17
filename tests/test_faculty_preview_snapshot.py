import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import preview_ucsd_faculty as preview
import review_ucsd_coverage as review
from collect_ucsd_coverage import Queue, REQUIRED_SOURCE_FILES


class FacultyPreviewSnapshotTests(unittest.TestCase):
    def test_current_rule_version_still_replaces_stale_shadow_with_new_captured_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); cache = root / '.cache/coverage-20261016'
            output = cache / 'profile-qualification-preview'
            (cache / 'responses').mkdir(parents=True); output.mkdir()
            (root / 'data').mkdir(); (root / 'docs/operations').mkdir(parents=True)
            (root / 'scripts').mkdir()
            for name in REQUIRED_SOURCE_FILES:
                (root / 'scripts' / name).write_text('# Recorded test source version\n')
            (root / 'data/research-atlas.json').write_text(json.dumps({'professors': [], 'labs': []}))
            queue = Queue(cache / 'queue.json')
            uri = 'https://profiles.ucsd.edu/jane.example'
            queue.add(uri, 'Unknown', 'profile_discovery')
            raw = b'<title>Jane Example</title><main><h2>Jane Example</h2></main>'
            meta = {'sourceUrl': uri, 'finalUrl': uri, 'status': 'ok', 'observedAt': '2020-01-01', 'sha256': hashlib.sha256(raw).hexdigest()}
            queue.state['items'][uri].update(state='done', fetch=meta)
            queue.state.update(profileQualificationVersion=2)
            queue.save()
            body_path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
            meta_path = body_path.with_suffix('.json')
            body_path.write_bytes(raw); meta_path.write_text(json.dumps(meta))
            before = {path: path.read_bytes() for path in [queue.path, body_path, meta_path]}
            stale = Queue(output / 'queue.json'); stale.state.update(profileQualificationVersion=2); stale.save()
            process = {'networkCoordination': {'collectorCodeSha256': 'loaded-source', 'requiredSourceFiles': {'collect_ucsd_coverage.py': 'loaded-source'}}}
            (cache / 'process.json').write_text(json.dumps(process))
            with patch.object(preview, 'ROOT', root), patch.object(review, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as completed:
                    preview.main()
            self.assertEqual(completed.exception.code, 0)
            shadow = json.loads((output / 'queue.json').read_text())
            self.assertIn(uri, shadow['items'], 'Fresh review must never point to a shadow missing newly captured sources')
            self.assertEqual(shadow['items'][uri]['fetch'], meta)
            self.assertEqual(shadow['profileQualificationVersion'], 2)
            for path, previous_bytes in before.items():
                self.assertEqual(path.read_bytes(), previous_bytes, 'Preview must preserve the live checkpoint and all raw source files')
            receipt = json.loads((root / 'docs/operations/profile-qualification-repair-20261016.json').read_text())
            self.assertFalse(receipt['qualificationReplayPerformed'])
            self.assertEqual(receipt['sourceQueueReadSha256'], hashlib.sha256(before[queue.path]).hexdigest())
            self.assertEqual(receipt['previewQueueSha256'], hashlib.sha256((output / 'queue.json').read_bytes()).hexdigest())
            self.assertEqual(receipt['sourceCaptureCount'], 1)
            self.assertEqual(set(receipt['requiredNextSourceHashes']), set(REQUIRED_SOURCE_FILES))
            self.assertEqual(receipt['changedSourceFiles'], [])
            self.assertEqual(receipt['changedSourceObservations'], [])
            fixed=root/'fixed-queue.json';fixed.write_bytes(before[queue.path])
            newer=Queue(queue.path);newer.add('https://profiles.ucsd.edu/later.person','Unknown','profile_discovery');newer.save()
            newer_bytes=queue.path.read_bytes()
            with patch.object(preview,'ROOT',root),patch.object(review,'ROOT',root),contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as completed:
                    preview.main(['--queue-preview',str(fixed)])
            self.assertEqual(completed.exception.code,0)
            self.assertEqual(queue.path.read_bytes(),newer_bytes)
            self.assertEqual(fixed.read_bytes(),before[queue.path])
            shadow=json.loads((output/'queue.json').read_text())
            self.assertEqual(set(shadow['items']),{uri})
            receipt=json.loads((root/'docs/operations/profile-qualification-repair-20261016.json').read_text())
            self.assertFalse(receipt['sourceQueueInputIsLive'])
            self.assertEqual(receipt['sourceQueuePath'],str(fixed.resolve()))
