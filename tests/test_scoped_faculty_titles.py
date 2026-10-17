import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from faculty_scoped_titles import scoped_academic_qualification
from review_ucsd_coverage import faculty_review
from test_atlas_quality import professor


class ScopedFacultyTitleTests(unittest.TestCase):
    def fixture(self, cache, kind='economics'):
        paths = {'economics': '/faculty-and-research/faculty-profiles/example.html',
                 'chemistry': '/faculty/profiles/example', 'matsci': '/faculty/example',
                 'sociology': '/people/faculty/example.html', 'communication': '/people/faculty/example.html'}
        uri = 'https://' + kind + '.ucsd.edu' + paths[kind]
        header = '<h1>Jane A. Example</h1>'
        bodies = {
            'economics': '<article id="profileTab" class="profile-section-tabs">'
                         '<div class="resp-tab-content"><p>Type: Faculty</p><p>Name: Jane A. Example</p>'
                         '<p>Title: Associate Professor, Vice Chair</p></div></article>',
            'chemistry': '<div><h2>Contact Information</h2><div><div><strong>Titles:</strong>'
                         '<ul class="list-unstyled"><li>Director of Laboratory</li>'
                         '<li>1992-1993 Professor, Other University</li>'
                         '<li>Distinguished Professor of Chemistry</li></ul></div></div></div>',
            'matsci': '<article class="faculty-listing" about="/faculty/example"><div class="mb-4">'
                      '<h5><div class="field--name-field-department">Chemistry</div></h5>'
                      '<h4><div class="field--name-field-primary-title">Department Chair</div></h4>'
                      '<em><div class="field--name-field-additional-titles">'
                      '<div class="field__item">Professor, Department of Chemistry</div>'
                      '<div class="field__item">Institute Director</div></div></em></div>'
                      '<p>Professor Another Person</p></article>',
            'sociology': '',
            'communication': '',
        }
        if kind == 'sociology':
            header = '<header class="profile-section-header">' + header + '<p class="subhead">Yankelovich Endowed Chair Professor</p></header>'
        if kind == 'communication':
            header = '<header class="profile-section-header" aria-label="Profile Name">' + header + '<p class="subhead">Professor and Chair</p></header>'
        raw = '<html><body><main>' + header + bodies[kind] + '</main></body></html>'
        (cache / 'responses').mkdir(exist_ok=True)
        path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
        path.write_text(raw)
        meta = {'sourceUrl': uri, 'finalUrl': uri, 'status': 'ok', 'observedAt': '2020-02-03T04:05:06Z',
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        item = {'url': uri, 'fetch': meta, 'state': 'done', 'contexts': []}
        return item, path

    def revise(self, item, path, old, new):
        path.write_text(path.read_text().replace(old, new))
        item['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()

    def test_explicit_fields_keep_complete_titles_units_and_actual_source_provenance(self):
        for kind in ['economics', 'chemistry', 'matsci', 'sociology', 'communication']:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, path = self.fixture(cache, kind); before = copy.deepcopy(item)
                q = scoped_academic_qualification(item, cache, 'Jane A. Example')
                self.assertIsNotNone(q)
                self.assertIn('Professor', q['roleAsListed'])
                self.assertEqual(q['nameAsDisplayed'], 'Jane A. Example')
                self.assertEqual(q['unitAsListed'], 'Chemistry' if kind == 'matsci' else '')
                self.assertEqual(q['evidence']['requestedUrl'], item['url'])
                self.assertEqual(q['evidence']['sourceUrl'], item['fetch']['finalUrl'])
                self.assertEqual(q['evidence']['observedAt'], '2020-02-03T04:05:06Z')
                self.assertEqual(q['evidence']['bodySha256'], hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(q['fieldEvidence']['roleAsListed'], q['evidence'])
                if kind == 'economics':
                    self.assertEqual(q['roleAsListed'], 'Associate Professor, Vice Chair')
                if kind == 'chemistry':
                    self.assertNotIn('1992-1993', q['roleAsListed'])
                    self.assertIn('1992-1993 Professor, Other University', q['titleFieldsAsListed']['Titles'])
                if kind == 'matsci':
                    self.assertEqual(q['roleAsListed'], 'Department Chair | Professor, Department of Chemistry | Institute Director')
                self.assertEqual(item, before)

    def test_named_header_rejects_biography_roles_wrong_structure_and_nonacademic_titles(self):
        changes = [('Professor and Chair', 'Department Director'),
                   ('Professor and Chair', 'Former Professor, Another University'),
                   ('aria-label="Profile Name"', 'aria-label="Unrelated"'),
                   ('</header>', '<p class="subhead">Professor</p></header>'),
                   ('<h1>Jane A. Example</h1>', '<h1>Jane B. Example</h1>')]
        for old, new in changes:
            with self.subTest(change=new), tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp); item,path=self.fixture(cache,'communication')
                self.revise(item,path,old,new)
                self.revise(item,path,'</main>','<p>Professor Jane A. Example</p></main>')
                self.assertIsNone(scoped_academic_qualification(item,cache,'Jane A. Example'))

    def test_real_review_preserves_original_person_id_primary_uri_and_roster_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, _ = self.fixture(cache)
            source = 'https://economics.ucsd.edu/faculty-and-research/faculty-profiles/index.html'
            row = {'name': 'Jane A. Example', 'department': 'Economics', 'listedRole': 'Ph.D., University, 2001 Research Interests: labor',
                   'appointmentStatus': 'listed_faculty', 'directorySection': 'Faculty', 'sourceUrl': source,
                   'observedAt': '2019-01-01', 'profileUrl': item['url'], 'namedLinkUrl': item['url'],
                   'email': '', 'personalWebsiteUrl': '', 'googleScholarUrl': '', 'researchAreas': [],
                   'evidence': {'sourceUrl': source, 'observedAt': '2019-01-01', 'method': 'official_faculty_directory_card', 'evidence': 'Jane A. Example | Research Interests: labor'}}
            old = professor('unchanged-id', 'Jane A. Example', 'Economics'); old['officialProfileUrl'] = item['url']
            queue = {'items': {item['url']: item}, 'facultyListings': [row]}; before = copy.deepcopy(queue)
            result = faculty_review(copy.deepcopy(queue), {'professors': [old], 'labs': []}, cache, profile_identity_review={'entries': []})
            self.assertEqual(result['professors'], [])
            self.assertEqual(result['uncertainListings'], [])
            self.assertEqual(set(result['byProfessorId']), {'unchanged-id'})
            patch = result['byProfessorId']['unchanged-id']; listing = patch['directoryListings'][0]
            for field in ['listedRole', 'sourceUrl', 'observedAt', 'evidence', 'department']:
                self.assertEqual(listing[field], row[field])
            self.assertEqual(listing['academicQualification']['roleAsListed'], 'Associate Professor, Vice Chair')
            self.assertNotIn('officialProfileUrl', patch)
            self.assertNotIn('name', patch)
            self.assertIn(item['url'], patch['sourceUrls'])
            self.assertEqual(queue, before)

    def test_wrong_conflicting_or_multiple_subjects_and_initial_only_names_fail_closed(self):
        for listed, replacement in [('Another Person', None), ('Jane B. Example', None), ('J. Example', None),
                                    ('Jane A. Example', '<h1>Jane A. Example</h1><h1>Another Person</h1>')]:
            with self.subTest(listed=listed, replacement=replacement), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, path = self.fixture(cache)
                if replacement:
                    self.revise(item, path, '<h1>Jane A. Example</h1>', replacement)
                self.assertIsNone(scoped_academic_qualification(item, cache, listed))

    def test_newly_qualified_title_cannot_expand_an_original_initial_name_or_primary_uri(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, _ = self.fixture(cache)
            source = 'https://economics.ucsd.edu/faculty-and-research/faculty-profiles/index.html'
            row = {'name': 'Jane A. Example', 'department': 'Economics', 'listedRole': 'Research Interests: labor',
                   'appointmentStatus': 'listed_faculty', 'directorySection': 'Faculty', 'sourceUrl': source,
                   'observedAt': '2019-01-01', 'profileUrl': item['url'], 'namedLinkUrl': item['url'],
                   'email': '', 'personalWebsiteUrl': '', 'googleScholarUrl': '', 'researchAreas': [],
                   'evidence': {'sourceUrl': source, 'observedAt': '2019-01-01', 'method': 'official_faculty_directory_card', 'evidence': 'Jane A. Example | Research Interests: labor'}}
            old = professor('unchanged-initial-id', 'J. Example', 'Economics')
            old['officialProfileUrl'] = 'https://catalog.ucsd.edu/faculty/ECON.html'
            before = copy.deepcopy(old)
            result = faculty_review({'items': {item['url']: item}, 'facultyListings': [row]},
                                    {'professors': [old], 'labs': []}, cache, profile_identity_review={'entries': []})
            self.assertEqual(result['professors'], [])
            self.assertEqual(result['byProfessorId'], {})
            self.assertEqual(len(result['uncertainListings']), 1)
            hold = result['uncertainListings'][0]
            self.assertEqual(hold['reason'], 'qualified_title_legacy_initial_alias_requires_identity_review')
            self.assertEqual(hold['candidateProfessorIds'], ['unchanged-initial-id'])
            self.assertEqual(hold['listing']['academicQualification']['roleAsListed'], 'Associate Professor, Vice Chair')
            self.assertEqual(hold['listing']['listedRole'], row['listedRole'])
            self.assertEqual(old, before)

    def test_unrelated_biography_navigation_and_nonacademic_fields_do_not_qualify(self):
        for kind in ['economics', 'chemistry', 'matsci', 'sociology']:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, path = self.fixture(cache, kind)
                raw = path.read_text().replace('Associate Professor, Vice Chair', 'Staff Researcher').replace('Distinguished Professor of Chemistry', 'Laboratory Director').replace('Professor, Department of Chemistry', 'Institute Director').replace('Yankelovich Endowed Chair Professor', 'Department Administrator')
                path.write_text(raw.replace('</main>', '<p>Professor, Chemistry</p><nav>Professor Another Person</nav></main>'))
                item['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertIsNone(scoped_academic_qualification(item, cache, 'Jane A. Example'))

    def test_conflicting_duplicate_and_missing_labeled_fields_fail_closed(self):
        changes = [('Type: Faculty', 'Type: Staff'), ('Name: Jane A. Example', 'Name: Another Person'),
                   ('<p>Title: Associate Professor, Vice Chair</p>', ''),
                   ('</article>', '<p>Title: Professor</p></article>'),
                   ('id="profileTab"', 'id="unrelated"')]
        for old, new in changes:
            with self.subTest(old=old), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, path = self.fixture(cache); self.revise(item, path, old, new)
                self.assertIsNone(scoped_academic_qualification(item, cache, 'Jane A. Example'))

    def test_actual_receipt_bytes_scope_and_redirect_subject_are_required(self):
        for mode in ['changed_bytes', 'missing_body', 'failed_fetch', 'foreign_redirect', 'generic_request', 'wrong_article']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, path = self.fixture(cache, 'matsci')
                if mode == 'changed_bytes': path.write_text(path.read_text() + 'changed')
                if mode == 'missing_body': path.unlink()
                if mode == 'failed_fetch': item['fetch']['status'] = 'error'
                if mode == 'foreign_redirect': item['fetch']['finalUrl'] = 'https://other.ucsd.edu/faculty/example'
                if mode == 'generic_request':
                    item['url'] = item['fetch']['sourceUrl'] = 'https://matsci.ucsd.edu/'
                    path.rename(cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html'))
                if mode == 'wrong_article': self.revise(item, path, 'about="/faculty/example"', 'about="/faculty/another"')
                self.assertIsNone(scoped_academic_qualification(item, cache, 'Jane A. Example'))

    def test_published_parenthetical_given_name_and_label_spacing_remain_exact_fields_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, path = self.fixture(cache)
            self.revise(item, path, 'Name: Jane A. Example', 'Name Janet (Jane) A. Example')
            q = scoped_academic_qualification(item, cache, 'Jane A. Example')
            self.assertEqual(q['nameAsDisplayed'], 'Jane A. Example')
            self.assertEqual(q['titleFieldsAsListed']['Name'], ['Janet (Jane) A. Example'])
            self.revise(item, path, 'Janet (Jane)', 'Janet (Other)')
            self.assertIsNone(scoped_academic_qualification(item, cache, 'Jane A. Example'))

    def test_literal_index_php_request_uses_its_actual_body_without_rewriting_the_uri(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, path = self.fixture(cache, 'matsci')
            item['url'] = item['fetch']['sourceUrl'] = item['fetch']['finalUrl'] = 'https://matsci.ucsd.edu/index.php/faculty/example'
            path.rename(cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html'))
            q = scoped_academic_qualification(item, cache, 'Jane A. Example')
            self.assertEqual(q['evidence']['requestedUrl'], item['url'])
            self.assertEqual(q['evidence']['sourceUrl'], item['url'])
            new_path = cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html')
            self.revise(item, new_path, 'about="/faculty/example"', 'about="/index.php/faculty/example"')
            self.assertIsNotNone(scoped_academic_qualification(item, cache, 'Jane A. Example'))
