import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lab_resource_associations import verified_resource_associations, apply_resource_associations
from lab_resource_reviews import record_sha256
from lab_entities import LabIndex
from refresh_labs import make_lab
from rebuild_verified_atlas import build
from audit_ucsd_preservation import audit
from validate_data import validate_references
from lab_field_reviews import own_lab_source
from test_atlas_quality import atlas


class ResourceAssociationTests(unittest.TestCase):
    def fixture(self, cache):
        items = {}; proofs = []
        for uri in ['http://old.ucsd.edu/', 'https://current.ucsd.edu/', 'https://current.ucsd.edu/people']:
            raw = ('<title>Current Lab</title><main>Current Lab at UC San Diego</main>' if not uri.endswith('people')
                   else '<main>Jane Example Principal Investigator</main>')
            (cache / 'responses').mkdir(exist_ok=True)
            path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
            path.write_text(raw)
            meta = {'sourceUrl': uri, 'finalUrl': uri, 'observedAt': '2026-01-01', 'status': 'ok', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            items[uri] = {'url': uri, 'fetch': meta}
            proofs.append({'requestedUrl': uri, 'sourceUrl': uri, 'observedAt': meta['observedAt'], 'bodySha256': meta['sha256'],
                           'evidenceType': 'main_text_quote' if uri.endswith('people') else 'document_title',
                           'evidence': 'Jane Example Principal Investigator' if uri.endswith('people') else 'Current Lab'})
        old = make_lab('Previous Lab', proofs[0]['sourceUrl'], 'Physics', proofs[0], 'Previous Lab')
        old.update(id='old', principalInvestigator='Different Person', description='Historical scattering research')
        current = make_lab('Current Lab', proofs[1]['sourceUrl'], 'Physics', proofs[1], 'Current Lab')
        current.update(id='current', principalInvestigator='Not found')
        row = {'action': 'record_resource_mismatch_and_current_lab', 'mismatchedLabId': old['id'], 'currentLabId': current['id'],
               'resourceUri': old['labWebsiteUrl'], 'currentLabUri': current['labWebsiteUrl'],
               'previousLabRecord': copy.deepcopy(old), 'previousLabRecordSha256': record_sha256(old),
               'currentLabRecord': copy.deepcopy(current), 'currentLabRecordSha256': record_sha256(current),
               'resourceEvidence': proofs[0], 'currentLabEvidence': proofs[1], 'currentLabPrincipalInvestigator': 'Jane Example',
               'currentLabLeadershipEvidence': [proofs[2]], 'evidence': proofs, 'reason': 'Actual named page content matches another distinct existing lab.'}
        destination = {'action': 'record_destination_assessment', 'labId': old['id'], 'identityStatus': 'mismatch', 'evidence': [proofs[0]]}
        data = atlas(); data.update(qualityMigrationVersion=1, labs=[old, current])
        person = data['professors'][0]
        person['labAffiliations'] = [{'labId': old['id'], 'labName': old['labName'], 'url': old['labWebsiteUrl'], 'fieldEvidence': proofs[0]}]
        return data, {'items': items}, row, [destination]

    def test_current_resource_resolves_separately_from_preserved_scientific_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row, destinations = self.fixture(cache)
            original = copy.deepcopy(data)
            reviews = verified_resource_associations({'entries': [row]}, queue, cache, data['labs'], destinations)
            delta = {'labResourceAssociationReviews': reviews, 'destinationIdentityReviews': destinations}
            first, _, _, archives = build(copy.deepcopy(data), {}, {}, {}, {}, coverage_evidence=delta)
            index = LabIndex(first['labs']); index.validate_sharing(); validate_references(first)
            self.assertEqual(index.resolve(row['resourceUri'])['id'], 'current')
            self.assertIsNone(index.resolve(row['resourceUri'], lab_id='old'))
            self.assertEqual(index.by_id['old']['labWebsiteUrl'], row['resourceUri'])
            self.assertEqual(index.by_id['old']['description'], 'Historical scattering research')
            self.assertEqual(index.by_id['old']['principalInvestigator'], 'Different Person')
            self.assertEqual(index.by_id['current']['principalInvestigator'], 'Not found', 'Resource association does not apply scientific field changes')
            self.assertNotIn('old', index.by_id['current'].get('aliasIds', []))
            self.assertEqual(len(first['labs']), 2)
            self.assertFalse(index.url_groups()[1])
            person = first['professors'][0]
            self.assertFalse(person['labAffiliations'], 'An old explicit person ID link must not silently retarget to the current resource owner')
            self.assertEqual(person['unresolvedLabLinks'][0]['labId'], 'old')
            self.assertEqual(audit(original, first, [archives])['status'], 'passed')
            second, *_ = build(copy.deepcopy(first), {}, {}, {}, {}, coverage_evidence=delta)
            self.assertEqual(first, second)
            self.assertFalse(own_lab_source(index.by_id['old'], row['resourceUri'], queue))
            without_legacy_review, *_ = build(copy.deepcopy(data), {}, {}, {}, {}, coverage_evidence={'labResourceAssociationReviews': reviews})
            self.assertEqual(without_legacy_review['labs'][0]['verification']['status'], 'needs_review')

    def test_unreviewed_mismatch_never_reassigns_a_resource(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, _, row, destinations = self.fixture(Path(tmp))
            data['labs'][0]['destinationIdentityAssessment'] = destinations[0]
            self.assertEqual(LabIndex(data['labs']).resolve(row['resourceUri'])['id'], 'old')

    def test_different_page_bytes_names_or_own_pi_cannot_be_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row, destinations = self.fixture(cache)
            for change in ['hash', 'name', 'pi']:
                modified = copy.deepcopy(row)
                if change == 'hash': modified['currentLabEvidence']['bodySha256'] = 'different'
                if change == 'name':
                    data_copy = copy.deepcopy(data); data_copy['labs'][1]['labName'] = 'Unrelated Lab'
                    modified['currentLabRecord'] = copy.deepcopy(data_copy['labs'][1]); modified['currentLabRecordSha256'] = record_sha256(modified['currentLabRecord'])
                else: data_copy = data
                if change == 'pi': modified['currentLabPrincipalInvestigator'] = 'Different Person'
                with self.subTest(change=change), self.assertRaises(ValueError):
                    verified_resource_associations({'entries': [modified]}, queue, cache, data_copy['labs'], destinations)

    def test_source_dates_individual_uri_capture_and_original_records_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row, destinations = self.fixture(cache)
            for change in ['date', 'uri', 'snapshot', 'assessment']:
                modified = copy.deepcopy(row); dst = destinations
                if change == 'date': modified['resourceEvidence']['observedAt'] = '2020-01-01'
                if change == 'uri': modified['resourceUri'] = 'https://old.ucsd.edu/'
                if change == 'snapshot': modified['previousLabRecord']['id'] = 'wrong'
                if change == 'assessment': dst = []
                with self.subTest(change=change), self.assertRaises(ValueError):
                    verified_resource_associations({'entries': [modified]}, queue, cache, data['labs'], dst)

    def test_failed_batch_is_atomic_and_incomplete_associations_fail_reference_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row, destinations = self.fixture(cache)
            reviews = verified_resource_associations({'entries': [row]}, queue, cache, data['labs'], destinations)
            before = copy.deepcopy(data)
            with self.assertRaises(ValueError):
                apply_resource_associations(data, reviews + [{**reviews[0], 'currentLabId': 'missing'}])
            self.assertEqual(data, before)
            apply_resource_associations(data, reviews)
            data['labs'][1].pop('resourceAssociationReviews')
            with self.assertRaisesRegex(ValueError, 'resource association'):
                LabIndex(data['labs']).validate_sharing()
