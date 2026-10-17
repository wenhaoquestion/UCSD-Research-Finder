import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collect_ucsd_coverage import profiles_appointment
from refresh_faculty_directories import build_evidence
from test_atlas_quality import professor


class UnmappedFacultyAliasTests(unittest.TestCase):
    def fixture(self):
        uri = 'https://profiles.ucsd.edu/jane.example'
        markup = '<main><div class="pageTitle"><h2>Jane Example</h2></div><table><tr><th>Title(s)</th><td>Professor, Structural System Facility</td></tr><tr><th>School</th><td>Vc-academic Affairs</td></tr></table></main>'
        meta = {'sourceUrl': uri, 'finalUrl': uri, 'observedAt': '2020-01-01'}
        _, row = profiles_appointment(meta, markup)
        old = professor('retained-original-id', 'J. Example', 'Structural Engineering')
        old['officialProfileUrl'] = 'https://catalog.ucsd.edu/faculty/SE.html'
        return row, old

    def test_actual_assembly_holds_unmapped_unit_initial_alias_instead_of_creating_a_second_id(self):
        for old_name in ['J. Example', 'J. Andrew Example']:
            with self.subTest(old_name=old_name):
                row, old = self.fixture(); old['name'] = old_name; before = copy.deepcopy((row, old))
                additions, patches, holds = build_evidence([row], [old])
                self.assertEqual(additions, [])
                self.assertEqual(patches, {})
                self.assertEqual(holds[0]['reason'], 'unmapped_unit_legacy_initials_requires_identity_review')
                self.assertEqual(holds[0]['candidateProfessorIds'], [old['id']])
                self.assertEqual(holds[0]['listing']['departmentAsListed'], 'Structural System Facility')
                self.assertEqual((row, old), before)

    def test_initial_overlap_in_a_different_explicit_department_does_not_merge_or_suppress_the_named_person(self):
        row, old = self.fixture(); row['department'] = 'Psychiatry'; row['departmentAsListed'] = 'Psychiatry'
        row['departmentMappingStatus'] = 'matched_saved_department'
        additions, patches, holds = build_evidence([row], [old])
        self.assertEqual(holds, [])
        self.assertEqual(len(additions), 1)
        self.assertNotEqual(additions[0]['id'], old['id'])
        self.assertNotIn(old['id'], patches)

    def test_unmapped_role_with_no_matching_initial_identity_remains_a_separate_named_candidate(self):
        row, old = self.fixture(); old['name'] = 'K. Example'
        additions, _, holds = build_evidence([row], [old])
        self.assertEqual(len(additions), 1)
        self.assertEqual(holds, [])
