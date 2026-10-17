import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lab_resource_reviews import verified_resource_reviews, verified_alias_reviews, register_resource_reviews, record_sha256
from lab_entities import LabIndex
from rebuild_verified_atlas import build
import test_exact_lab_resources as resource_fixtures


class ResourceReviewTests(unittest.TestCase):
    def fixture(self, cache):
        data, incoming = resource_fixtures.ExactLabResourceTests().fixture()
        proofs, items = [], {}
        for url in [data['labs'][0]['labWebsiteUrl'], incoming['labWebsiteUrl']]:
            raw = b'<title>Example Lab</title><main>Example Lab at UC San Diego</main>'
            (cache / 'responses').mkdir(exist_ok=True)
            (cache / 'responses' / (hashlib.sha256(url.encode()).hexdigest() + '.html')).write_bytes(raw)
            meta = {'sourceUrl': url, 'finalUrl': url, 'status': 'ok', 'observedAt': '2026-01-01', 'redirects': []}
            items[url] = {'url': url, 'fetch': meta}
            proofs.append({'requestedUrl': url, 'sourceUrl': url, 'observedAt': meta['observedAt'],
                           'bodySha256': hashlib.sha256(raw).hexdigest(), 'evidence': 'Example Lab at UC San Diego'})
        row = {'action': 'bind_capture_identity', 'captureId': incoming['id'], 'targetLabId': data['labs'][0]['id'],
               'captureUri': incoming['labWebsiteUrl'], 'targetUri': data['labs'][0]['labWebsiteUrl'],
               'captureRecordSha256': record_sha256(incoming), 'originalCaptureRecord': copy.deepcopy(incoming),
               'resourceStatus': 'verified_same_lab', 'reason': 'Both actual pages identify the same named group.', 'evidence': proofs}
        return data, incoming, {'items': items}, row

    def test_explicit_identity_binding_registers_only_observed_resource_and_keeps_primary(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, incoming, queue, row = self.fixture(Path(tmp))
            rows = verified_resource_reviews({'entries': [row]}, queue, Path(tmp), [incoming], data['labs'])
            original = copy.deepcopy(data)
            index = LabIndex(data['labs'])
            register_resource_reviews(index, [incoming], rows)
            self.assertEqual(index.resolve(incoming['labWebsiteUrl'])['id'], 'existing')
            self.assertEqual(data['labs'][0]['labWebsiteUrl'], original['labs'][0]['labWebsiteUrl'])
            first, *_ = build(data, {'labs': [incoming]}, {}, {}, {}, coverage_evidence={'labResourceReviews': rows})
            second, *_ = build(copy.deepcopy(first), {'labs': [incoming]}, {}, {}, {}, coverage_evidence={'labResourceReviews': rows})
            self.assertEqual(first, second)
            self.assertEqual(len(first['labs']), 1)
            self.assertEqual(first['unresolvedLabCaptureInputs'], [])

    def test_uri_similarity_and_unchecked_redirect_fields_cannot_substitute_for_a_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, incoming, queue, row = self.fixture(Path(tmp))
            row['evidence'] = row['evidence'][:1]
            row['evidence'][0]['redirects'] = [{'from': row['targetUri'], 'to': row['captureUri'], 'httpStatus': 301}]
            with self.assertRaisesRegex(ValueError, 'Both exact resource'):
                verified_resource_reviews({'entries': [row]}, queue, Path(tmp), [incoming], data['labs'])

    def test_changed_body_date_input_or_primary_uri_invalidates_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, incoming, queue, row = self.fixture(Path(tmp))
            for key, wrong in [('observedAt', '2020-01-01'), ('bodySha256', 'changed')]:
                bad = copy.deepcopy(row)
                bad['evidence'][0][key] = wrong
                with self.subTest(key=key), self.assertRaises(ValueError):
                    verified_resource_reviews({'entries': [bad]}, queue, Path(tmp), [incoming], data['labs'])
            for key, wrong in [('captureUri', 'http://different.ucsd.edu/'), ('targetUri', 'https://different.ucsd.edu/'), ('captureRecordSha256', 'changed')]:
                with self.subTest(key=key), self.assertRaises(ValueError):
                    verified_resource_reviews({'entries': [{**row, key: wrong}]}, queue, Path(tmp), [incoming], data['labs'])

    def test_invalid_as_listed_uri_binds_scientific_record_without_repair_or_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, incoming, queue, row = self.fixture(Path(tmp))
            incoming['labWebsiteUrl'] = 'https://example.ucsd.edu /'
            row.update(captureUri=incoming['labWebsiteUrl'], resourceStatus='invalid_as_listed',
                       captureRecordSha256=record_sha256(incoming), originalCaptureRecord=copy.deepcopy(incoming), evidence=row['evidence'][:1])
            rows = verified_resource_reviews({'entries': [row]}, queue, Path(tmp), [incoming], data['labs'])
            old_uri = data['labs'][0]['labWebsiteUrl']
            data['professors'][0].update(labAffiliation='Example Lab', labAffiliationUrl=old_uri,
                fieldEvidence={'labAffiliation': row['evidence'][:1], 'labAffiliationUrl': row['evidence'][:1]})
            delta = {'labs': [incoming], 'byProfessorId': {'p': {'labAffiliationUrl': incoming['labWebsiteUrl'],
                     'fieldEvidence': {'labAffiliationUrl': row['evidence'][:1]}}}}
            first, *_ = build(data, delta, {}, {}, {}, coverage_evidence={'labResourceReviews': rows})
            lab = first['labs'][0]
            self.assertIn(incoming['id'], lab['aliasIds'])
            self.assertNotIn('alternateWebsiteUrls', lab)
            self.assertEqual(lab['additionalLabResourceObservations'][0]['value'], incoming['labWebsiteUrl'])
            self.assertEqual(first['professors'][0]['labAffiliationUrl'], old_uri, 'invalid recapture cannot erase an existing valid lab association')
            row['resourceStatus'] = 'verified_same_lab'
            with self.assertRaisesRegex(ValueError, 'Invalid resource'):
                verified_resource_reviews({'entries': [row]}, queue, Path(tmp), [incoming], data['labs'])

    def test_listed_unvisited_resource_is_not_owned_and_failed_batch_is_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, incoming, queue, row = self.fixture(Path(tmp))
            row.update(resourceStatus='listed_unverified', evidence=row['evidence'][:1])
            rows = verified_resource_reviews({'entries': [row]}, queue, Path(tmp), [incoming], data['labs'])
            index = LabIndex(data['labs'])
            before = copy.deepcopy(data)
            with self.assertRaises(ValueError):
                register_resource_reviews(index, [incoming], rows + [{**rows[0], 'captureId': 'missing'}])
            self.assertEqual(before, data)
            register_resource_reviews(index, [incoming], rows)
            self.assertIsNone(index.resolve(incoming['labWebsiteUrl']))

    def test_later_sourced_binding_resolves_a_hold_without_discarding_original_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, incoming, queue, row = self.fixture(Path(tmp))
            held, *_ = build(data, {'labs': [incoming]}, {}, {}, {})
            original_hold = copy.deepcopy(held['unresolvedLabCaptureInputs'][0])
            rows = verified_resource_reviews({'entries': [row]}, queue, Path(tmp), [incoming], held['labs'])
            result, *_ = build(held, {'labs': [incoming]}, {}, {}, {}, coverage_evidence={'labResourceReviews': rows})
            self.assertEqual(result['unresolvedLabCaptureInputs'], [])
            self.assertEqual(result['resolvedLabCaptureInputHistory'][0]['previousUnresolvedInput'], original_hold)

    def test_every_alias_requires_its_own_reviewed_actual_uri(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, incoming, queue, row = self.fixture(Path(tmp))
            alias = {'labId': 'existing', 'url': incoming['labWebsiteUrl'], 'fieldEvidence': row['evidence']}
            review = {'labId': alias['labId'], 'url': alias['url'], 'originalAliasRecord': copy.deepcopy(alias),
                      'originalAliasRecordSha256': record_sha256(alias), 'reason': 'Captured named lab page', 'evidence': row['evidence']}
            self.assertTrue(verified_alias_reviews({'entries': [review]}, [alias], queue, Path(tmp))[0]['captureVerified'])
            with self.assertRaisesRegex(ValueError, 'Every accepted exact'):
                verified_alias_reviews({'entries': []}, [alias], queue, Path(tmp))
            review.update(url='http://www.example.ucsd.edu/')
            alias['url'] = review['url']
            review.update(originalAliasRecord=copy.deepcopy(alias), originalAliasRecordSha256=record_sha256(alias))
            with self.assertRaisesRegex(ValueError, 'not actually observed'):
                verified_alias_reviews({'entries': [review]}, [alias], queue, Path(tmp))
