"""Exact composite-link captures flag a review, never resolve person identity."""
import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from faculty_profile_bindings import profile_metadata
from lab_resource_reviews import record_sha256
from professor_profile_link_reviews import verified_profile_link_reviews, apply_profile_link_reviews
from test_atlas_quality import professor, atlas
from rebuild_verified_atlas import build
from validate_data import validate_professor


class ProfessorProfileLinkReviewTests(unittest.TestCase):
    def fixture(self, cache):
        uris = ['https://profiles.ucsd.edu/another.person', 'https://profiles.ucsd.edu/jane.example']
        items = {}
        (cache / 'responses').mkdir()
        for uri, name, rid in zip(uris, ['Another Person', 'Jane Example'], ['100', '200']):
            raw = ('<html><head><link rel="canonical" href="' + uri + '">'
                   '<link rel="alternate" type="application/rdf+xml" href="https://researcherprofiles.org/profile/'
                   + rid + '/' + rid + '.rdf"></head><body><main>'
                   '<div class="pageTitle"><h2>' + name + '</h2></div></main></body></html>')
            path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
            path.write_text(raw)
            items[uri] = {'url': uri, 'state': 'done', 'fetch': {'sourceUrl': uri, 'finalUrl': uri,
                'observedAt': '2026-10-16T00:00:00Z', 'status': 'ok', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}}
        person = professor('same-original-id', 'Jane Example', 'Economics')
        person['officialProfileUrl'] = '#'.join(uris)
        person['sourceUrls'] = [person['officialProfileUrl']]
        row = {'action': 'flag_composite_profile_link_identity_review', 'professorId': person['id'],
               'originalProfileUri': person['officialProfileUrl'], 'originalProfessorRecordSha256': record_sha256(person),
               'reason': 'Retain the stored link and both actual named observations as an unresolved link review.',
               'identityResolved': False, 'captures': [profile_metadata(items[u], cache)[0] for u in uris]}
        return person, {'items': items}, {'entries': [row]}

    def test_actual_named_captures_flag_only_the_original_link_and_repeat_identically(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); person, queue, review = self.fixture(cache)
            originals = copy.deepcopy((person, queue, review))
            rows = verified_profile_link_reviews(review, queue, cache, [person])
            data = {'professors': [copy.deepcopy(person)]}; apply_profile_link_reviews(data, rows)
            updated = data['professors'][0]
            for field in person:
                if field not in {'sourceUrls', 'fieldEvidence'}:
                    self.assertEqual(updated[field], person[field], field)
            self.assertEqual(updated['officialProfileUrl'], person['officialProfileUrl'])
            self.assertNotIn('aliasIds', updated)
            self.assertIs(updated['profileLinkIdentityReview']['identityResolved'], False)
            self.assertEqual(updated['profileLinkIdentityReview']['status'], 'needs_review')
            self.assertEqual(len(updated['fieldEvidence']['profileLinkIdentityReview']), 2)
            self.assertTrue(all(p['status'] == 'review_required' for p in updated['fieldEvidence']['profileLinkIdentityReview']))
            once = copy.deepcopy(data); apply_profile_link_reviews(data, rows); self.assertEqual(data, once)
            self.assertEqual((person, queue, review), originals)

    def test_dates_hashes_request_identity_and_unchanged_original_record_are_required(self):
        for mode in ['bytes', 'date', 'request', 'original_name', 'primary_uri', 'resolved', 'duplicate']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); person, queue, review = self.fixture(cache); row = review['entries'][0]
                if mode == 'bytes': next((cache / 'responses').iterdir()).write_text('changed')
                if mode == 'date': row['captures'][0]['observedAt'] = '2020-01-01'
                if mode == 'request': row['captures'][0]['requestedUrl'] = person['officialProfileUrl']
                if mode == 'original_name': person['name'] = 'Janet Example'
                if mode == 'primary_uri': person['officialProfileUrl'] = row['captures'][1]['requestedUrl']
                if mode == 'resolved': row['identityResolved'] = True
                if mode == 'duplicate': review['entries'].append(copy.deepcopy(row))
                with self.assertRaises(ValueError): verified_profile_link_reviews(review, queue, cache, [person])

    def test_compatible_subject_or_shared_identifiers_cannot_support_a_mismatch_review(self):
        for mode in ['same_subject', 'same_canonical', 'same_rdf', 'other_separate_subject']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); person, queue, review = self.fixture(cache); captures = review['entries'][0]['captures']
                uri = captures[0]['requestedUrl'] if mode != 'other_separate_subject' else captures[1]['requestedUrl']
                path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
                raw = path.read_text()
                if mode == 'same_subject': raw = raw.replace('Another Person', 'Jane Example')
                if mode == 'same_canonical': raw = raw.replace('rel="canonical" href="' + uri + '"', 'rel="canonical" href="' + captures[1]['canonicalUri'] + '"')
                if mode == 'same_rdf': raw = raw.replace('/100/100.rdf', '/200/200.rdf')
                if mode == 'other_separate_subject': raw = raw.replace('Jane Example', 'Janet Example')
                path.write_text(raw); queue['items'][uri]['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                review['entries'][0]['captures'] = [profile_metadata(queue['items'][p['requestedUrl']], cache)[0] for p in captures]
                with self.assertRaises(ValueError): verified_profile_link_reviews(review, queue, cache, [person])

    def test_unique_original_uri_and_verified_application_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); person, queue, review = self.fixture(cache)
            other = {**copy.deepcopy(person), 'id': 'other-original-id'}
            with self.assertRaises(ValueError): verified_profile_link_reviews(review, queue, cache, [person, other])
            with self.assertRaises(ValueError): apply_profile_link_reviews({'professors': [copy.deepcopy(person)]}, review['entries'])
            rows = verified_profile_link_reviews(review, queue, cache, [person]); changed = copy.deepcopy(person); changed['officialProfileUrl'] = rows[0]['captures'][1]['requestedUrl']
            with self.assertRaises(ValueError): apply_profile_link_reviews({'professors': [changed]}, rows)

    def test_real_rebuild_never_promotes_a_link_issue_into_verified_person_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); person, queue, review = self.fixture(cache)
            rows = verified_profile_link_reviews(review, queue, cache, [person])
            baseline = atlas(); baseline['professors'] = [person]
            assembled, *_ = build(baseline, {}, {}, {}, {}, coverage_evidence={'professorProfileLinkReviews': rows})
            result = assembled['professors'][0]
            self.assertEqual(result['verification']['status'], 'needs_review')
            self.assertNotIn('profileLinkIdentityReview', result['verification']['fieldsVerified'])
            self.assertEqual(result['name'], person['name'])
            self.assertEqual(result['officialProfileUrl'], person['officialProfileUrl'])
            self.assertEqual(result['lastVerified'], person['lastVerified'])
            validate_professor(result)
            repeated, *_ = build(copy.deepcopy(assembled), {}, {}, {}, {}, coverage_evidence={'professorProfileLinkReviews': rows})
            self.assertEqual(assembled, repeated)
