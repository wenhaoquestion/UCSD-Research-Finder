"""The one audited Salk relationship cannot become UCSD ownership or a general exception."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lab_summary_handoff import _external_program_lab, HandoffImportError


class ExternalProgramTests(unittest.TestCase):
    def fixture(self):
        lid = 'ucsd-live-lab-f65b4596f0a5e3'
        proofs = [{'evidence': value} for value in ['own access', 'named faculty card', 'literal campus link']]
        lab = {'id': lid, 'labName': 'Kosuri Lab', 'labWebsiteUrl': 'https://kosurilab.com/',
               'institution': 'Salk Institute for Biological Studies',
               'relationshipScope': 'ucsd_graduate_program_affiliate', 'department': 'Unknown',
               'professorIds': [], 'principalInvestigator': 'Not found',
               'campusProgramRelationships': [{'institution': 'University of California San Diego',
                   'programName': 'Bioinformatics and Systems Biology',
                   'relationship': 'program_listing_and_own_rotation_guidance',
                   'facultyRoleAsListed': 'Assistant Professor, Salk Institute for Biological Studies',
                   'programSourceUrl': 'https://bioinformatics.ucsd.edu/faculty'}],
               'fieldEvidence': {'campusProgramRelationships': proofs}}
        decision = {'institution': lab['institution'], 'programAffiliationReview': {
            'kind': 'ucsd_graduate_program_external_lab', 'labId': lid, 'labWebsiteUrl': lab['labWebsiteUrl'],
            'ownStudentAccessEvidence': proofs[0], 'campusCardEvidence': proofs[1], 'campusLabLinkEvidence': proofs[2]}}
        return lab, decision

    def test_exact_external_scope_passes(self):
        self.assertIsNone(_external_program_lab(*self.fixture()))

    def test_ownership_pi_department_or_identity_promotion_fails(self):
        for field, value in [('id', 'another-lab'), ('institution', 'University of California San Diego'),
                             ('department', 'Bioengineering'), ('principalInvestigator', 'Pallav Kosuri'),
                             ('professorIds', ['guessed-professor'])]:
            lab, decision = self.fixture()
            lab[field] = value
            with self.subTest(field=field), self.assertRaises(HandoffImportError):
                _external_program_lab(lab, decision)

    def test_independent_program_and_own_access_proofs_required(self):
        lab, decision = self.fixture()
        lab['fieldEvidence']['campusProgramRelationships'] = lab['fieldEvidence']['campusProgramRelationships'][1:]
        with self.assertRaises(HandoffImportError):
            _external_program_lab(lab, decision)
        lab, decision = self.fixture()
        lab['campusProgramRelationships'][0]['facultyRoleAsListed'] = 'Professor, UCSD'
        with self.assertRaises(HandoffImportError):
            _external_program_lab(lab, decision)
