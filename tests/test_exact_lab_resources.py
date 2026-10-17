import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from atlas_urls import url_key, comparison_key
from lab_entities import LabIndex
from rebuild_verified_atlas import build
from refresh_labs import make_lab
from validate_data import validate_references
from audit_ucsd_preservation import audit


class ExactLabResourceTests(unittest.TestCase):
    def fixture(self):
        from test_atlas_quality import atlas
        data = atlas()
        uri = 'http://example.ucsd.edu/'
        meta = {'sourceUrl': uri, 'finalUrl': uri, 'observedAt': '2020-01-01'}
        old = make_lab('Example Lab', uri, 'Unknown', meta, 'Example Lab at UC San Diego')
        old['id'] = 'existing'
        data['labs'] = [old]
        incoming = copy.deepcopy(old)
        incoming.update(id='capture-side-id', labWebsiteUrl='https://example.ucsd.edu/')
        return data, incoming

    def test_protocol_www_default_path_and_query_variants_do_not_resolve(self):
        data, _ = self.fixture()
        index = LabIndex(data['labs'])
        for uri in ['https://example.ucsd.edu/', 'http://www.example.ucsd.edu/',
                    'http://example.ucsd.edu/index.html', 'http://example.ucsd.edu/?utm_source=x']:
            with self.subTest(uri=uri):
                self.assertIsNone(index.resolve(uri))
                self.assertEqual([r['id'] for r in index.possible_variants(uri)], ['existing'])
        self.assertEqual(index.resolve('http://example.ucsd.edu/#part')['id'], 'existing')

    def test_same_uri_with_a_different_name_is_held_without_overwriting_entity(self):
        data, incoming = self.fixture()
        incoming.update(labName='Different Lab', labWebsiteUrl=data['labs'][0]['labWebsiteUrl'])
        first, _, _, _ = build(data, {'labs': [incoming]}, {}, {}, {})
        self.assertEqual(len(first['labs']), 1)
        self.assertEqual(first['labs'][0]['labName'], 'Example Lab')
        self.assertEqual(first['unresolvedLabCaptureInputs'][0]['record'], incoming)
        self.assertNotIn('capture-side-id', first['labs'][0].get('aliasIds', []))

    def test_unreviewed_capture_and_relationship_are_preserved_as_unresolved(self):
        data, incoming = self.fixture()
        baseline = copy.deepcopy(data)
        proof = {'sourceUrl': 'https://dept.ucsd.edu/person', 'observedAt': '2026-01-01', 'evidence': 'Example Lab website'}
        old_uri = data['labs'][0]['labWebsiteUrl']
        data['professors'][0].update(labAffiliation='Example Lab', labAffiliationUrl=old_uri,
            fieldEvidence={'labAffiliation': [proof], 'labAffiliationUrl': [proof]})
        delta = {'labs': [incoming], 'byProfessorId': {'p': {'labAffiliation': 'Example Lab', 'labAffiliationUrl': incoming['labWebsiteUrl'],
            'fieldEvidence': {'labAffiliation': [proof], 'labAffiliationUrl': [proof]},
            'labAffiliations': [{'labId': incoming['id'], 'labName': 'Example Lab', 'url': incoming['labWebsiteUrl'], 'fieldEvidence': proof}]}}}
        first, _, _, archive = build(data, copy.deepcopy(delta), {}, {}, {})
        self.assertEqual(first['labs'][0]['id'], 'existing')
        self.assertEqual(first['professors'][0]['labAffiliationUrl'], old_uri)
        self.assertEqual(first['professors'][0]['labAffiliations'], [])
        self.assertEqual(first['unresolvedLabCaptureInputs'][0]['record'], incoming)
        self.assertTrue(first['professors'][0]['unresolvedLabLinks'])
        validate_references(first)
        self.assertEqual(audit(baseline, first, [archive])['status'], 'passed')
        second, *_ = build(copy.deepcopy(first), copy.deepcopy(delta), {}, {}, {})
        self.assertEqual(first, second)

    def test_existing_identity_does_not_change_primary_resource_on_capture_replay(self):
        data, incoming = self.fixture()
        incoming['id'] = 'existing'
        incoming['fieldEvidence']['labWebsiteUrl'] = {'sourceUrl': incoming['labWebsiteUrl'], 'observedAt': '2026-01-01', 'evidence': 'Listed website'}
        first, *_ = build(data, {'labs': [incoming]}, {}, {}, {})
        kept = first['labs'][0]
        self.assertEqual(kept['labWebsiteUrl'], 'http://example.ucsd.edu/')
        self.assertEqual(kept['additionalLabResourceObservations'][0]['value'], 'https://example.ucsd.edu/')
        self.assertNotIn('https://example.ucsd.edu/', kept.get('alternateWebsiteUrls', []))

    def test_heuristic_key_is_only_a_review_hint(self):
        first, second = 'http://www.example.ucsd.edu/index.html?utm_source=x', 'https://example.ucsd.edu/'
        self.assertEqual(comparison_key(first), comparison_key(second))
        self.assertNotEqual(url_key(first), url_key(second))

    def test_shared_url_and_same_lab_label_do_not_override_conflicting_pi_identity(self):
        data, incoming = self.fixture()
        data['labs'][0]['principalInvestigator'] = 'Jane Example'
        incoming.update(labWebsiteUrl=data['labs'][0]['labWebsiteUrl'], principalInvestigator='John Example')
        first, *_ = build(data, {'labs': [incoming]}, {}, {}, {})
        self.assertEqual(first['labs'][0]['principalInvestigator'], 'Jane Example')
        self.assertEqual(first['unresolvedLabCaptureInputs'][0]['record'], incoming)
