import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collect_ucsd_coverage import Queue, analyze, discover_math_profile_metadata, url_key
from review_ucsd_coverage import source_coverage


SOURCE = 'https://math.ucsd.edu/export/people/faculty'


class MathMetadataDiscoveryTests(unittest.TestCase):
    def fixture(self, tmp, rows):
        queue = Queue(Path(tmp) / 'queue.json')
        queue.add(SOURCE, 'Mathematics', 'directory', 'https://www.math.ucsd.edu/people/faculty', 1)
        item = queue.state['items'][url_key(SOURCE)]
        body = json.dumps(rows)
        meta = {'status': 'ok', 'sourceUrl': SOURCE, 'finalUrl': SOURCE,
                'observedAt': '2026-10-16T01:00:00+00:00', 'sha256': hashlib.sha256(body.encode()).hexdigest()}
        item.update(state='done', fetch=meta)
        return queue, item, meta, body

    def test_public_metadata_discovers_links_without_qualifying_faculty(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = [{'view_node_1': '/people/profiles/first-person', 'nid_1': '1', 'field_work_email': 'first@ucsd.edu', 'field_person_title': ''},
                    {'view_node_1': '/people/profiles/second-person', 'nid_1': '2', 'field_work_email': 'second@ucsd.edu', 'field_person_title': 'Assistant Professor'}]
            queue, item, meta, body = self.fixture(tmp, rows)
            analyze(queue, item, meta, body, {'professors': [], 'labs': []})
            self.assertEqual(len(queue.state['items']), 3)
            self.assertEqual(queue.state['facultyListings'], [])
            self.assertEqual(queue.state['labCandidates'], {})
            self.assertEqual(item['structuredProfileDiscovery']['facultyAppointmentsAsserted'], 0)
            target = queue.state['items'][url_key('https://math.ucsd.edu/people/profiles/first-person')]
            self.assertEqual(target['depth'], 2)
            self.assertEqual(target['sourceMetadataObservations'][0]['jsonPointer'], '/0')
            self.assertEqual(target['sourceMetadataObservations'][0]['observedAt'], meta['observedAt'])
            self.assertNotIn('name', target['sourceMetadataObservations'][0])
            coverage = source_coverage(queue.state)
            self.assertEqual(coverage[0]['personMetadataDiscovery']['profileLinks'], 2)
            self.assertEqual(coverage[0]['contentReviewStatus'], 'discovery_only_or_no_supported_records_extracted')

    def test_arbitrary_external_personal_and_query_links_are_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = [{'view_node_1': value, 'field_website': 'https://external.example/unrelated'}
                    for value in ['https://external.example/person', '//evil.example/person', '/people/profiles/../../login',
                                  '/people/profiles/person?token=x', '/people/profiles/person#x', '/people/staff/person', None]]
            queue, item, meta, body = self.fixture(tmp, rows)
            discover_math_profile_metadata(queue, item, meta, body)
            self.assertEqual(len(queue.state['items']), 1)
            self.assertEqual(item['structuredProfileDiscovery']['invalidRows'], len(rows))

    def test_replay_preserves_each_dated_row_and_deduplicates_profile_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = [{'view_node_1': '/people/profiles/person', 'nid_1': '1', 'field_work_email': 'one@ucsd.edu'},
                    {'view_node_1': '/people/profiles/person', 'nid_1': '2', 'field_work_email': 'two@ucsd.edu'}]
            queue, item, meta, body = self.fixture(tmp, rows)
            for _ in range(2):
                discover_math_profile_metadata(queue, item, meta, body)
            target = queue.state['items'][url_key('https://math.ucsd.edu/people/profiles/person')]
            self.assertEqual(len(queue.state['items']), 2)
            self.assertEqual(len(target['sourceMetadataObservations']), 2)
            self.assertEqual(target['sourceMetadataObservations'][0]['bodySha256'], meta['sha256'])
            self.assertEqual(item['structuredProfileDiscovery']['profileLinks'], 1)

    def test_invalid_body_hash_redirect_payload_and_depth_do_not_expand_scope(self):
        for mode in ['hash', 'redirect', 'payload', 'depth', 'context', 'too-many-rows']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                rows = [{'view_node_1': '/people/profiles/person'}]
                if mode == 'payload':
                    rows = {'unexpected': rows}
                if mode == 'too-many-rows':
                    rows *= 1001
                queue, item, meta, body = self.fixture(tmp, rows)
                if mode == 'hash':
                    meta['sha256'] = 'wrong'
                elif mode == 'redirect':
                    meta['finalUrl'] = 'https://another.ucsd.edu/export/people/faculty'
                elif mode == 'depth':
                    item['depth'] = 2
                elif mode == 'context':
                    item['contexts'][0]['kind'] = 'profile'
                discover_math_profile_metadata(queue, item, meta, body)
                self.assertEqual(len(queue.state['items']), 1)
                self.assertEqual(item['structuredProfileDiscovery']['profileLinks'], 0)

    def test_only_the_named_official_endpoint_is_recognized(self):
        with tempfile.TemporaryDirectory() as tmp:
            queue, item, meta, body = self.fixture(tmp, [])
            item['url'] = 'https://another.ucsd.edu/export/people/faculty'
            self.assertFalse(discover_math_profile_metadata(queue, item, meta, body))
            self.assertNotIn('structuredProfileDiscovery', item)
