import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from legacy_lab_review import apply_destination_identity_reviews


class DestinationIdentityReviewTests(unittest.TestCase):
    def data(self):
        proof = {'sourceUrl': 'https://department.ucsd.edu/course', 'observedAt': '2020-01-01', 'evidence': 'original source'}
        return {'labs': [{'id': 'bad', 'labName': 'Group Study', 'labWebsiteUrl': proof['sourceUrl'], 'fieldEvidence': {'labName': [proof]}},
                         {'id': 'good', 'labName': 'Real Lab', 'labWebsiteUrl': 'https://real.ucsd.edu/'}],
                'professors': [{'id': 'person', 'labAffiliation': 'Group Study', 'labAffiliationUrl': proof['sourceUrl'],
                                'labAffiliations': [{'labId': 'bad', 'url': proof['sourceUrl'], 'fieldEvidence': [proof]}, {'labId': 'good', 'url': 'https://real.ucsd.edu/'}],
                                'fieldEvidence': {'labAffiliation': [proof], 'labAffiliationUrl': [proof]}}]}

    def review(self):
        return {'labId': 'bad', 'action': 'isolate_non_lab', 'identityStatus': 'mismatch', 'observedPageType': 'course',
                'evidence': [{'sourceUrl': 'https://department.ucsd.edu/course', 'observedAt': '2026-01-01', 'evidence': 'Course units: 2-4'}]}

    def test_non_lab_is_archived_with_id_old_evidence_and_affected_relationships(self):
        data = self.data()
        original = copy.deepcopy(data)
        archive = apply_destination_identity_reviews(data, [self.review()])
        self.assertEqual([l['id'] for l in data['labs']], ['good'])
        self.assertEqual(archive[0]['record'], original['labs'][0])
        self.assertEqual(archive[0]['affectedProfessorObservations'][0]['labAffiliations'], original['professors'][0]['labAffiliations'][:1])
        person = data['professors'][0]
        self.assertEqual(person['labAffiliations'], original['professors'][0]['labAffiliations'][1:])
        self.assertEqual(person['labAffiliationUrl'], 'Not found')
        previous = next(p for p in person['previousFieldObservations'] if p['field'] == 'labAffiliationUrl')
        self.assertEqual(previous['fieldEvidence'], original['professors'][0]['fieldEvidence']['labAffiliationUrl'])

    def test_destination_mismatch_retains_lab_and_old_url_without_closure_claim(self):
        data = self.data()
        row = self.review()
        row.update(action='record_destination_assessment', observedPageType='institutional_homepage')
        archive = apply_destination_identity_reviews(data, [row])
        self.assertFalse(archive)
        self.assertEqual(data['labs'][0]['labWebsiteUrl'], 'https://department.ucsd.edu/course')
        self.assertEqual(data['labs'][0]['verification']['destinationIdentityStatus'], 'mismatch')
        self.assertNotIn('closed', data['labs'][0])

    def test_invalid_isolation_cannot_partially_apply_valid_earlier_reviews(self):
        data = self.data()
        original = copy.deepcopy(data)
        invalid = {**self.review(), 'labId': 'good', 'observedPageType': 'lab'}
        with self.assertRaisesRegex(ValueError, 'alone cannot exclude'):
            apply_destination_identity_reviews(data, [self.review(), invalid])
        self.assertEqual(data, original)

    def test_rebuild_does_not_replace_the_first_archive_or_its_relationships(self):
        data = self.data()
        row = self.review()
        row['originalRecord'] = copy.deepcopy(data['labs'][0])
        first_archive = apply_destination_identity_reviews(data, [row])
        rebuilt = copy.deepcopy(data)
        self.assertFalse(apply_destination_identity_reviews(data, [row]))
        self.assertEqual(data, rebuilt)
        self.assertTrue(first_archive[0]['affectedProfessorObservations'])
