"""Resource identity and campus links must not promote institutional ownership."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lab_summary_handoff import _unknown_owner_group, HandoffImportError


class UnknownOwnerTests(unittest.TestCase):
    def fixture(self):
        lid = 'ucsd-live-lab-a92dafc16a6dae'
        proofs = [{'evidence': x} for x in ['named card', 'literal link', 'recorded transport']]
        lab = {'id': lid, 'labName': 'Insight', 'recordSubtype': 'research_group',
               'labWebsiteUrl': 'https://insight.ucsd.edu/', 'institution': 'Unknown',
               'department': 'Unknown', 'principalInvestigator': 'Not found', 'professorIds': [],
               'relationshipScope': 'official_campus_research_resource', 'unverifiedFields': ['institution'],
               'institutionAssessment': {'status': 'unresolved', 'reason': 'ownership not established'},
               'fieldEvidence': {'campusResearchRelationships': proofs}}
        decision = {'institution': 'Unknown', 'institutionUnresolvedReason': 'ownership not established',
                    'campusResearchResourceReview': {'kind': 'named_campus_linked_research_group', 'labId': lid,
                        'campusCardEvidence': proofs[0], 'campusLinkEvidence': proofs[1], 'transportEvidence': proofs[2]}}
        return lab, decision

    def test_audited_group_with_unknown_owner_passes(self):
        self.assertIsNone(_unknown_owner_group(*self.fixture()))

    def test_owner_department_pi_and_lab_type_promotions_fail(self):
        for field, value in [('institution', 'University of California San Diego'), ('department', 'Cognitive Science'),
                             ('principalInvestigator', 'Ying Wu'), ('recordSubtype', 'lab'),
                             ('professorIds', ['guessed-id']), ('id', 'another-group')]:
            lab, decision = self.fixture()
            lab[field] = value
            with self.subTest(field=field), self.assertRaises(HandoffImportError):
                _unknown_owner_group(lab, decision)

    def test_independent_resource_chain_and_unknown_marker_required(self):
        lab, decision = self.fixture()
        lab['fieldEvidence']['campusResearchRelationships'] = []
        with self.assertRaises(HandoffImportError):
            _unknown_owner_group(lab, decision)
        lab, decision = self.fixture()
        lab['unverifiedFields'] = []
        with self.assertRaises(HandoffImportError):
            _unknown_owner_group(lab, decision)
