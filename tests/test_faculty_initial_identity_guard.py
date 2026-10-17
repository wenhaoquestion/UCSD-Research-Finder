"""A faculty appointment does not identify an initial-only catalog person."""
import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collect_ucsd_coverage import profiles_appointment
from review_ucsd_coverage import faculty_review
from test_atlas_quality import professor


class FacultyInitialIdentityGuardTests(unittest.TestCase):
    def review(self, shared_email=False, exact_profile=False):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            uri = 'https://profiles.ucsd.edu/jane.example'
            markup = ('<main><div class="pageTitle"><h2>Jane Example</h2></div>'
                      '<table><tr><th>Title(s)</th><td>Professor, Economics</td></tr>'
                      '<tr><th>School</th><td>Vc-academic Affairs</td></tr>'
                      '<tr><th>Email</th><td>jexample@ucsd.edu</td></tr></table></main>')
            meta = {'sourceUrl': uri, 'finalUrl': uri, 'observedAt': '2026-10-16T00:00:00Z',
                    'status': 'ok', 'sha256': hashlib.sha256(markup.encode()).hexdigest()}
            _, row = profiles_appointment(meta, markup)
            old = professor('original-initial-id', 'J. Example', 'Economics')
            old['officialProfileUrl'] = uri if exact_profile else 'https://catalog.ucsd.edu/faculty/ECON.html'
            if shared_email:
                old['email'] = 'jexample@ucsd.edu'
            before = copy.deepcopy(old)
            (cache / 'responses').mkdir()
            (cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')).write_text(markup)
            queue = {'items': {uri: {'url': uri, 'state': 'done', 'fetch': meta, 'contexts': []}},
                     'facultyListings': [row]}
            result = faculty_review(queue, {'professors': [old], 'labs': []}, cache,
                                    profile_identity_review={'entries': []})
            self.assertEqual(old, before)
            return result

    def test_explicit_profiles_title_and_same_unit_do_not_expand_initials(self):
        result = self.review()
        self.assertEqual(result['professors'], [])
        self.assertEqual(result['byProfessorId'], {})
        self.assertEqual(len(result['uncertainListings']), 1)
        hold = result['uncertainListings'][0]
        self.assertEqual(hold['reason'], 'qualified_title_legacy_initial_alias_requires_identity_review')
        self.assertEqual(hold['candidateProfessorIds'], ['original-initial-id'])
        self.assertEqual(hold['listing']['name'], 'Jane Example')
        self.assertEqual(hold['listing']['listedRole'], 'Professor, Economics')

    def test_independent_shared_own_contact_remains_an_identity_basis(self):
        result = self.review(shared_email=True)
        self.assertEqual(result['uncertainListings'], [])
        self.assertEqual(set(result['byProfessorId']), {'original-initial-id'})

    def test_exact_existing_individual_profile_remains_an_identity_basis(self):
        result = self.review(exact_profile=True)
        self.assertEqual(result['uncertainListings'], [])
        self.assertEqual(set(result['byProfessorId']), {'original-initial-id'})
