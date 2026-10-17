import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from faculty_profile_bindings import profile_metadata, verified_profile_bindings
from collect_ucsd_coverage import profiles_appointment
from lab_resource_reviews import record_sha256
from review_ucsd_coverage import faculty_review
from test_atlas_quality import professor


class FacultyProfileBindingTests(unittest.TestCase):
    def fixture(self, cache):
        canonical = 'https://profiles.ucsd.edu/jane.example'
        rdf = 'https://researcherprofiles.org/profile/123/123.rdf'
        original = 'https://profiles.ucsd.edu/Jane.Example'
        person = professor('old-stable-id', 'Jane Example', 'Pediatrics')
        person['officialProfileUrl'] = original
        person['email'] = 'Not found'
        queue = {'items': {}, 'facultyListings': []}
        (cache / 'responses').mkdir()
        for uri in [original, canonical]:
            raw = ('<html><head><title>Jane Example | UCSD Profiles</title>'
                   f'<link rel="canonical" href="{canonical}">'
                   f'<link rel="alternate" type="application/rdf+xml" href="{rdf}"></head>'
                   '<body><main><div class="pageTitle"><h2>Jane Example</h2></div>'
                   '<table><tr><th>Title(s)</th><td>Associate Professor, Pediatrics</td></tr>'
                   '<tr><th>School</th><td>Vc-health Sciences-schools</td></tr></table></main></body></html>')
            path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
            path.write_text(raw)
            meta = {'sourceUrl': uri, 'finalUrl': uri, 'status': 'ok',
                    'observedAt': '2020-01-01T00:00:00+00:00', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            queue['items'][uri] = {'url': uri, 'fetch': meta, 'state': 'done', 'contexts': []}
        assessment, listing = profiles_appointment(queue['items'][canonical]['fetch'], raw)
        queue['facultyListings'] = [listing]
        proofs = [profile_metadata(queue['items'][uri], cache)[0] for uri in [original, canonical]]
        row = {'action': 'bind_observation_to_existing_person', 'professorId': person['id'],
               'originalProfileUri': original, 'originalProfessorRecordSha256': record_sha256(person),
               'captures': proofs, 'identityBasis': {'type': 'shared_canonical_and_personal_rdf', 'canonicalUri': canonical, 'rdfAlternateUri': rdf},
               'qualificationAsListed': {k: assessment[k] for k in ['nameAsDisplayed', 'titleAsListed', 'schoolAsListed']},
               'reason': 'Both named own pages declare the same individual canonical and numeric RDF identifiers.'}
        return {'professors': [person], 'labs': []}, queue, {'entries': [row]}

    def rewrite(self, queue, cache, uri, old, new):
        path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
        path.write_text(path.read_text().replace(old, new))
        queue['items'][uri]['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()

    def test_real_review_resolves_a_held_observation_without_new_id_or_primary_uri_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            atlas, queue, review = self.fixture(cache)
            before = copy.deepcopy((atlas, queue, review))
            held = faculty_review(copy.deepcopy(queue), atlas, cache, profile_identity_review={'entries': []})
            self.assertEqual(held['uncertainListings'][0]['reason'], 'distinct_profile_same_or_similar_name_requires_identity_review')
            result = faculty_review(copy.deepcopy(queue), atlas, cache, profile_identity_review=review)
            self.assertFalse(result['professors'])
            self.assertFalse(result['uncertainListings'])
            self.assertEqual(set(result['byProfessorId']), {'old-stable-id'})
            patch = result['byProfessorId']['old-stable-id']
            self.assertNotIn('officialProfileUrl', patch)
            proof = patch['directoryListings'][0]['identityEvidence']
            self.assertEqual(len(proof['profileIdentityBinding']['captures']), 2)
            self.assertEqual(proof['observedAt'], '2020-01-01T00:00:00+00:00')
            self.assertEqual((atlas, queue, review), before)
            self.assertEqual(result, faculty_review(copy.deepcopy(queue), atlas, cache, profile_identity_review=review))

    def test_stale_raw_bytes_date_subject_and_original_record_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            atlas, queue, review = self.fixture(cache)
            for field, value in [('observedAt', '1999-01-01'), ('bodySha256', 'changed'), ('nameAsDisplayed', 'Other Person'), ('requestedUrl', 'https://profiles.ucsd.edu/Other.Case')]:
                changed = copy.deepcopy(review)
                changed['entries'][0]['captures'][0][field] = value
                with self.subTest(field=field), self.assertRaises(ValueError):
                    verified_profile_bindings(changed, queue, cache, atlas)
            changed = copy.deepcopy(atlas)
            changed['professors'][0]['department'] = 'Different department'
            with self.assertRaisesRegex(ValueError, 'unchanged explicit'):
                verified_profile_bindings(review, queue, cache, changed)

    def test_same_name_or_one_shared_identifier_cannot_bind_distinct_person_profiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            atlas, queue, review = self.fixture(cache)
            uri = review['entries'][0]['captures'][1]['requestedUrl']
            self.rewrite(queue, cache, uri, '/123/123.rdf', '/456/456.rdf')
            review['entries'][0]['captures'][1] = profile_metadata(queue['items'][uri], cache)[0]
            with self.assertRaisesRegex(ValueError, 'same canonical and personal RDF'):
                verified_profile_bindings(review, queue, cache, atlas)

    def test_biography_identifiers_generic_canonicals_and_shared_directory_rdf_are_not_subject_metadata(self):
        for old, new in [('</head>', '</head><main>'), ('/jane.example', '/search'), ('/123/123.rdf', '/directory.rdf')]:
            with self.subTest(change=new), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp)
                atlas, queue, review = self.fixture(cache)
                uri = review['entries'][0]['captures'][1]['requestedUrl']
                if old == '</head>':
                    self.rewrite(queue, cache, uri, '<head>', '<div>')
                    self.rewrite(queue, cache, uri, '</head>', '</div>')
                else:
                    self.rewrite(queue, cache, uri, old, new)
                with self.assertRaises(ValueError):
                    profile_metadata(queue['items'][uri], cache)

    def test_existing_duplicate_ids_and_changed_qualification_require_separate_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            atlas, queue, review = self.fixture(cache)
            duplicate = copy.deepcopy(atlas['professors'][0]); duplicate['id'] = 'another-existing-id'
            atlas['professors'].append(duplicate)
            with self.assertRaisesRegex(ValueError, 'separate person merge'):
                verified_profile_bindings(review, queue, cache, atlas)
            atlas['professors'].pop()
            review['entries'][0]['qualificationAsListed']['titleAsListed'] = 'Professor of an invented department'
            with self.assertRaisesRegex(ValueError, 'appointment table'):
                verified_profile_bindings(review, queue, cache, atlas)
