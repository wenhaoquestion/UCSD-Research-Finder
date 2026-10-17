"""Independent pinned capture admission fails closed on bytes, URI or receipt mismatch."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import lab_summary_handoff as h


class SupplementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.url = 'https://example.ucsd.edu/main.html'
        path = self.root/'frame-capture-responses'/(hashlib.sha256(self.url.encode()).hexdigest()+'.html')
        path.parent.mkdir()
        body = b'<main>Example research</main>'
        path.write_bytes(body)
        digest = hashlib.sha256(body).hexdigest()
        meta = {'status': 'ok', 'sourceUrl': self.url, 'httpStatus': 200,
                'observedAt': '2026-10-16T22:00:00+00:00', 'sha256': digest}
        self.entry = {'item': {'url': self.url, 'fetch': meta}, 'bodySha256': digest, 'cachePath': str(path),
                      'receipt': {'requestedUrl': self.url, 'capture': copy.deepcopy(meta), 'wireRequests': 1,
                                  'maximumContentAttempts': 1, 'liveQueueWritten': False}}

    def load(self, entry):
        data = (json.dumps({'items': [entry]})+'\n').encode()
        pin = hashlib.sha256(data).hexdigest()
        (self.root/('frame-source-captures-'+pin+'.json')).write_bytes(data)
        with patch.object(h, 'SUPPLEMENT_SHA256', pin), patch.object(h, 'SUPPLEMENT_URLS', frozenset({self.url})):
            return h._load_supplement(self.root)

    def test_exact_frozen_receipt_and_raw_body_pass(self):
        self.assertEqual(set(self.load(self.entry)), {self.url})

    def test_corrupted_body_and_mismatched_receipt_fail(self):
        bad = copy.deepcopy(self.entry)
        bad['receipt']['capture']['observedAt'] = '2026-10-16T23:00:00+00:00'
        with self.assertRaises(h.HandoffImportError):
            self.load(bad)
        Path(self.entry['cachePath']).write_bytes(b'changed')
        with self.assertRaises(h.HandoffImportError):
            self.load(self.entry)

    def test_uri_and_path_escape_fail(self):
        bad = copy.deepcopy(self.entry)
        bad['item']['url'] = 'http://example.ucsd.edu/main.html'
        with self.assertRaises(h.HandoffImportError):
            self.load(bad)
        bad = copy.deepcopy(self.entry)
        bad['cachePath'] = str(self.root/'outside.html')
        with self.assertRaises(h.HandoffImportError):
            self.load(bad)
