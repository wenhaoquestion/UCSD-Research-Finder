import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from review_ucsd_coverage import faculty_review
from test_atlas_quality import professor
from rebuild_verified_atlas import merge_patch


class JacobsFacultyQualificationTests(unittest.TestCase):
    def fixture(self, cache, role='Professor, CSE', name='Jane Example'):
        requested = 'http://jacobsschool.ucsd.edu/faculty/faculty_bios/index.sfe?fmp_recid=123'
        final = 'https://jacobsschool.ucsd.edu/faculty/profile?id=123'
        raw = ('<html><head><title>Faculty Profiles | Jacobs School</title></head><body><main>'
               '<h1>Faculty Profiles</h1><div class="row mb-5"><div class="col-9">'
               f'<h3 class="faculty_profile_name">{name}</h3><p class="mb-5">{role}</p>'
               '<hr><div class="mb-5">Professor Another Person, BENG</div></div></div></main></body></html>')
        (cache / 'responses').mkdir()
        path = cache / 'responses' / (hashlib.sha256(requested.encode()).hexdigest() + '.html')
        path.write_text(raw)
        meta = {'sourceUrl': requested, 'finalUrl': final, 'status': 'ok',
                'observedAt': '2020-01-01T00:00:00+00:00', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        proof = {'sourceUrl': 'https://be.ucsd.edu/faculty', 'observedAt': '2019-01-01T00:00:00+00:00',
                 'method': 'official_faculty_card', 'evidence': 'Jane Example | Affiliate Example Research'}
        row = {'name': 'Jane Example', 'department': 'Bioengineering', 'listedRole': 'Affiliate Example Research',
               'appointmentStatus': 'listed_faculty', 'directorySection': 'Affiliate', 'sourceUrl': proof['sourceUrl'],
               'observedAt': proof['observedAt'], 'evidence': proof, 'profileUrl': requested, 'namedLinkUrl': requested,
               'email': '', 'personalWebsiteUrl': '', 'googleScholarUrl': '', 'researchAreas': []}
        queue = {'items': {requested: {'url': requested, 'fetch': meta, 'state': 'done', 'contexts': []}}, 'facultyListings': [row]}
        return {'professors': [], 'labs': []}, queue, path

    def test_real_review_qualifies_own_jacobs_role_and_preserves_affiliate_listing_and_provenance(self):
        for role in ['Professor, CSE', 'Professor and Department Chair, BENG']:
            with self.subTest(role=role), tempfile.TemporaryDirectory() as tmp:
                atlas, queue, path = self.fixture(Path(tmp), role)
                original = copy.deepcopy(queue)
                result = faculty_review(copy.deepcopy(queue), atlas, Path(tmp), profile_identity_review={'entries': []})
                self.assertEqual(result['uncertainListings'], [])
                self.assertEqual(len(result['professors']), 1)
                person = result['professors'][0]
                listing = person['directoryListings'][0]
                self.assertEqual(person['department'], 'Bioengineering')
                self.assertEqual(person['officialProfileUrl'], original['facultyListings'][0]['profileUrl'])
                for field in ['listedRole', 'department', 'evidence', 'observedAt', 'directorySection']:
                    self.assertEqual(listing[field], original['facultyListings'][0][field])
                qualification = listing['academicQualification']
                self.assertEqual(qualification['roleAsListed'], role)
                self.assertEqual(qualification['unitAsListed'], role.split(', ')[1])
                self.assertEqual(qualification['nameAsDisplayed'], 'Jane Example')
                proof = qualification['evidence']
                self.assertEqual(proof['requestedUrl'], original['facultyListings'][0]['profileUrl'])
                self.assertEqual(proof['sourceUrl'], original['items'][proof['requestedUrl']]['fetch']['finalUrl'])
                self.assertEqual(proof['bodySha256'], hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(proof['observedAt'], '2020-01-01T00:00:00+00:00')
                self.assertEqual(qualification['fieldEvidence'], {field: proof for field in ['nameAsDisplayed', 'roleAsListed', 'unitAsListed']})
                self.assertEqual(queue, original)

    def test_existing_person_id_and_primary_uri_stay_attached_to_the_original_listing(self):
        with tempfile.TemporaryDirectory() as tmp:
            atlas, queue, _ = self.fixture(Path(tmp), 'Associate Professor, NENG')
            person = professor('stable-existing-id', 'Jane Example', 'Bioengineering')
            person['officialProfileUrl'] = queue['facultyListings'][0]['profileUrl']
            atlas['professors'] = [person]
            original = copy.deepcopy(atlas)
            result = faculty_review(copy.deepcopy(queue), atlas, Path(tmp), profile_identity_review={'entries': []})
            self.assertEqual(result['professors'], [])
            self.assertEqual(result['uncertainListings'], [])
            self.assertEqual(set(result['byProfessorId']), {'stable-existing-id'})
            patch = result['byProfessorId']['stable-existing-id']
            self.assertNotIn('officialProfileUrl', patch)
            self.assertEqual(patch['directoryListings'][0]['listedRole'], 'Affiliate Example Research')
            qualification = patch['directoryListings'][0]['academicQualification']
            self.assertEqual(qualification['fieldEvidence']['roleAsListed']['method'], 'identity_matched_jacobs_primary_appointment')
            self.assertIn(qualification['evidence']['sourceUrl'], patch['sourceUrls'])
            self.assertEqual(atlas, original)
            assembled = copy.deepcopy(person)
            older_listing = {'sourceUrl': 'https://be.ucsd.edu/older-roster', 'listedRole': 'Affiliate', 'observedAt': '2018-01-01'}
            assembled['directoryListings'] = [older_listing]
            merge_patch(assembled, patch)
            once = copy.deepcopy(assembled)
            merge_patch(assembled, patch)
            self.assertEqual(assembled, once)
            self.assertIn(older_listing, assembled['directoryListings'])
            self.assertIn(patch['directoryListings'][0], assembled['directoryListings'])
            self.assertEqual(assembled['officialProfileUrl'], original['professors'][0]['officialProfileUrl'])

    def test_biography_other_people_nonacademic_and_external_primary_roles_remain_unqualified(self):
        for mode in ['wrong_subject', 'conflicting_middle_name', 'two_subjects', 'biography_only', 'generic_fallback', 'nonadjacent_role',
                     'missing_separator', 'staff', 'external_primary', 'affiliate_only', 'generic_request']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                atlas, queue, path = self.fixture(Path(tmp))
                raw = path.read_text()
                replacements = {
                    'wrong_subject': ('>Jane Example</h3>', '>Another Person</h3>'),
                    'conflicting_middle_name': ('>Jane Example</h3>', '>Jane B. Example</h3>'),
                    'two_subjects': ('<hr>', '<hr><h3 class="faculty_profile_name">Another Person</h3>'),
                    'biography_only': ('<p class="mb-5">Professor, CSE</p>', '<p class="mb-5"></p>'),
                    'nonadjacent_role': ('</h3>', '</h3><p>Contact</p>'),
                    'missing_separator': ('<hr>', ''),
                    'staff': ('Professor, CSE', 'Staff Researcher, CSE'),
                    'external_primary': ('Professor, CSE', 'Professor, Other University Faculty-Affiliate, CSE'),
                    'affiliate_only': ('Professor, CSE', 'Faculty-Affiliate, CSE')}
                if mode in replacements:
                    raw = raw.replace(*replacements[mode])
                if mode == 'conflicting_middle_name':
                    queue['facultyListings'][0]['name'] = 'Jane A. Example'
                if mode == 'generic_fallback':
                    raw = raw.replace('<title>Faculty Profiles | Jacobs School</title>', '<title>Jane Example | Jacobs School</title>')
                    raw = raw.replace('<p class="mb-5">Professor, CSE</p>', '<p class="mb-5"></p>')
                    raw = raw.replace('<div class="mb-5">Professor Another Person, BENG</div>', '<p>Professor, CSE</p>')
                path.write_text(raw)
                item = next(iter(queue['items'].values()))
                item['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                if mode == 'generic_request':
                    uri = 'https://jacobsschool.ucsd.edu/faculty'
                    path.rename(path.with_name(hashlib.sha256(uri.encode()).hexdigest() + '.html'))
                    item['url'] = item['fetch']['sourceUrl'] = uri
                    queue['items'] = {uri: item}
                    queue['facultyListings'][0]['profileUrl'] = uri
                result = faculty_review(copy.deepcopy(queue), atlas, Path(tmp), profile_identity_review={'entries': []})
                self.assertEqual(result['professors'], [])
                self.assertEqual([r['reason'] for r in result['uncertainListings']], ['explicit_academic_title_not_observed'])

    def test_missing_changed_and_retained_captures_cannot_supply_qualification(self):
        for mode in ['missing_body', 'changed_body', 'old_retention', 'wrong_requested_receipt', 'missing_date', 'external_final']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                atlas, queue, path = self.fixture(Path(tmp))
                item = next(iter(queue['items'].values()))
                if mode == 'missing_body':
                    path.unlink()
                elif mode == 'changed_body':
                    path.write_text(path.read_text() + '<!-- changed -->')
                elif mode == 'old_retention':
                    item['state'] = 'retained_prior_evidence'
                    item['fetch']['status'] = 'http_error'
                elif mode == 'wrong_requested_receipt':
                    item['fetch']['sourceUrl'] = 'https://jacobsschool.ucsd.edu/faculty/profile?id=456'
                elif mode == 'missing_date':
                    item['fetch']['observedAt'] = ''
                elif mode == 'external_final':
                    item['fetch']['finalUrl'] = 'https://example.edu/faculty/profile?id=123'
                result = faculty_review(copy.deepcopy(queue), atlas, Path(tmp), profile_identity_review={'entries': []})
                self.assertEqual(result['professors'], [])
                self.assertEqual([r['reason'] for r in result['uncertainListings']], ['explicit_academic_title_not_observed'])

    def test_other_jacobs_template_retains_its_independent_review_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            atlas, queue, path = self.fixture(Path(tmp))
            uri = 'https://jacobsschool.ucsd.edu/people/profile/jane-example'
            raw = path.read_text().replace('<title>Faculty Profiles | Jacobs School</title>', '<title>Jane Example | Jacobs School</title>')
            raw = raw.replace('<h3 class="faculty_profile_name">Jane Example</h3>', '<h1>Jane Example</h1>')
            path.write_text(raw)
            path.rename(path.with_name(hashlib.sha256(uri.encode()).hexdigest() + '.html'))
            item = next(iter(queue['items'].values()))
            item['url'] = item['fetch']['sourceUrl'] = item['fetch']['finalUrl'] = uri
            item['fetch']['sha256'] = hashlib.sha256(raw.encode()).hexdigest()
            queue['items'] = {uri: item}
            queue['facultyListings'][0]['profileUrl'] = uri
            result = faculty_review(copy.deepcopy(queue), atlas, Path(tmp), profile_identity_review={'entries': []})
            self.assertEqual(result['uncertainListings'], [])
            self.assertEqual(len(result['professors']), 1)
            self.assertNotIn('academicQualification', result['professors'][0]['directoryListings'][0])
