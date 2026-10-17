import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from review_ucsd_coverage import faculty_review
from test_atlas_quality import professor


class FacultyDepartmentContextTests(unittest.TestCase):
    def row(self, source='https://cardiology.ucsd.edu/about/faculty.html'):
        return {'name': 'Jane Example', 'department': 'Interdisciplinary', 'listedRole': 'Associate Professor',
                'appointmentStatus': 'listed_faculty', 'directorySection': 'Faculty', 'sourceUrl': source,
                'observedAt': '2026-01-01', 'evidence': {'sourceUrl': source, 'observedAt': '2026-01-01', 'evidence': 'Jane Example | Associate Professor'},
                'profileUrl': 'https://profiles.ucsd.edu/jane.example', 'namedLinkUrl': 'https://profiles.ucsd.edu/jane.example',
                'email': '', 'personalWebsiteUrl': '', 'googleScholarUrl': '', 'researchAreas': []}

    def review(self, rows, people):
        with tempfile.TemporaryDirectory() as cache:
            return faculty_review({'facultyListings': rows, 'items': {}}, {'professors': people}, Path(cache), profile_identity_review={'entries': []})

    def person(self):
        p=professor('known', 'Jane Example', 'Medicine')
        p['officialProfileUrl']='https://profiles.ucsd.edu/jane.example'
        return p

    def test_unknown_source_bucket_does_not_become_an_existing_person_department(self):
        row=self.row();person=self.person();before=copy.deepcopy([row,person]);result=self.review([row],[person])
        patch=result['byProfessorId']['known'];listing=patch['directoryListings'][0]
        self.assertEqual(listing['department'],'Unknown')
        self.assertEqual(listing['sourceDepartmentContext'],'Interdisciplinary')
        self.assertNotIn('Interdisciplinary',patch['departmentAffiliations'])
        old=listing['sourceDepartmentContextReview']['previousListing']
        for field in ['name','listedRole','sourceUrl','observedAt','evidence','namedLinkUrl']:
            self.assertEqual(old[field],listing[field])
        self.assertEqual(old['department'],'Interdisciplinary')
        self.assertEqual([row,person],before)
        self.assertEqual(result['sourceDepartmentContextReview']['professorsAffected'],1)
        self.assertEqual(result,self.review([row],[person]))

    def test_explicit_unit_and_known_department_source_are_preserved(self):
        explicit=self.row();explicit['departmentExplicitlyListed']=True
        known=self.row('https://pulmonary.ucsd.edu/faculty.html')
        result=self.review([explicit,known],[self.person()]);listings=result['byProfessorId']['known']['directoryListings']
        self.assertEqual({r['department'] for r in listings},{'Interdisciplinary','Medicine'})
        self.assertFalse(any('sourceDepartmentContextReview' in r for r in listings))
        self.assertEqual(result['sourceDepartmentContextReview']['sourceRowObservations'],0)

    def test_center_only_role_does_not_gain_new_faculty_eligibility(self):
        result=self.review([self.row()],[])
        self.assertEqual(result['professors'],[])
        self.assertEqual(result['byProfessorId'],{})
        self.assertEqual(result['uncertainListings'][0]['reason'],'ucsd_department_appointment_not_established_by_program_or_center_listing')

    def test_new_named_department_person_retains_context_card_without_false_affiliation(self):
        roster=self.row('https://med.ucsd.edu/about/faculty-directory.html');roster['department']='Medicine'
        center=self.row();result=self.review([center,roster],[])
        self.assertEqual(len(result['professors']),1)
        person=result['professors'][0]
        self.assertEqual(person['department'],'Medicine')
        self.assertEqual(person['departmentAffiliations'],['Medicine'])
        self.assertEqual(len(person['directoryListings']),2)
        self.assertEqual({r['department'] for r in person['directoryListings']},{'Medicine','Unknown'})

    def test_named_unit_does_not_bypass_a_possible_initial_alias_in_another_department(self):
        roster=self.row('https://med.ucsd.edu/about/faculty-directory.html');roster['department']='Medicine'
        original=professor('original-initial','J. Example','Bioengineering')
        result=self.review([roster],[original])
        self.assertEqual(result['professors'],[])
        self.assertEqual(result['byProfessorId'],{})
        hold=result['uncertainListings'][0]
        self.assertEqual(hold['reason'],'cross_department_legacy_initials_requires_identity_review')
        self.assertEqual(hold['candidateProfessorIds'],['original-initial'])
        self.assertEqual(hold['provisionalRecordSnapshot']['name'],'Jane Example')
        self.assertEqual(original['name'],'J. Example')


if __name__=='__main__':
    unittest.main()
