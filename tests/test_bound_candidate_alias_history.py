import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_ucsd_preservation import audit
from faculty_candidate_history import candidate_history, attach_history_patches
from lab_resource_reviews import record_sha256
from rebuild_verified_atlas import build
from review_ucsd_coverage import faculty_review
from test_atlas_quality import atlas as minimal_atlas
import test_faculty_named_roster_binding as roster_fixtures


class BoundCandidateAliasHistoryTests(unittest.TestCase):
    def fixture(self, cache):
        atlas, queue, review = roster_fixtures.NamedRosterBindingTests().fixture(cache)
        person=atlas['professors'][0];person['aliasIds']=['older-retained-alias']
        review['entries'][0]['originalProfessorRecordSha256']=record_sha256(person)
        before=faculty_review(copy.deepcopy(queue),atlas,cache,profile_identity_review={'entries':[]})
        current=faculty_review(copy.deepcopy(queue),atlas,cache,profile_identity_review=review)
        old=before['professors'][0];old['labAffiliations']=[{'labId':'older-observed-lab'}]
        old['aliasIds']=['older-provisional-alias']
        binding=current['byProfessorId'][person['id']]['directoryListings'][0]['identityEvidence']['profileIdentityBinding']
        entry={'record':copy.deepcopy(old),'recordSha256':record_sha256(old),
               'disposition':'resolved_observation_binding_to_original_person','targetProfessorId':person['id'],
               'observationBinding':binding,'reason':'Preserve the whole earlier proposed record; its actual qualifying observation now binds to the retained named roster identity.'}
        return atlas,queue,current,{'sourceCandidateAtlasSha256':'a'*64,'entries':[entry]}

    def test_actual_assembler_preserves_the_whole_prior_candidate_and_old_links_without_copying_its_scalar_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);atlas,queue,current,history=self.fixture(cache);before=copy.deepcopy((atlas,queue,current,history))
            patches,archives=candidate_history(history,atlas['professors'],current,queue,cache)
            self.assertEqual(archives,[])
            combined=copy.deepcopy(current['byProfessorId']);attach_history_patches(combined,patches);attach_history_patches(combined,patches)
            data=minimal_atlas();data['professors']=copy.deepcopy(atlas['professors'])
            coverage={'professors':current['professors'],'byProfessorId':combined}
            assembled,_,_,_=build(data,{}, {}, {}, {},coverage_evidence=coverage)
            person=assembled['professors'][0];old=history['entries'][0]['record']
            self.assertEqual(len(assembled['professors']),1)
            self.assertEqual(person['id'],'retained-original-id');self.assertEqual(person['name'],'Charley Coffey')
            self.assertEqual(person['officialProfileUrl'],atlas['professors'][0]['officialProfileUrl'])
            self.assertTrue({'older-retained-alias',old['id'],'older-provisional-alias'}<=set(person['aliasIds']))
            self.assertEqual(person['fieldEvidence']['aliasIds'][0]['method'],'verified_candidate_id_alias_from_captured_observation_binding')
            self.assertFalse(person.get('labAffiliations'))
            preservation=audit({'professors':[old],'labs':[]},assembled)
            self.assertEqual(preservation['status'],'passed',preservation['issueCounts'])
            repeated,_,_,_=build(copy.deepcopy(assembled),{}, {}, {}, {},coverage_evidence=coverage)
            self.assertEqual(assembled,repeated)
            self.assertEqual((atlas,queue,current,history),before)

    def test_missing_actual_assignment_changed_target_or_modified_snapshot_fail_before_alias_creation(self):
        for mode in ['missing_assignment','wrong_target','changed_snapshot','active_candidate','wrong_binding']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);atlas,queue,current,history=self.fixture(cache);entry=history['entries'][0]
                if mode=='missing_assignment':current['byProfessorId']={}
                if mode=='wrong_target':entry['targetProfessorId']='another-id'
                if mode=='changed_snapshot':entry['record']['name']='Changed subject'
                if mode=='active_candidate':current['professors']=[entry['record']]
                if mode=='wrong_binding':entry['observationBinding']['captures'][2]['rawHref']='https://profiles.ucsd.edu/somebody.else'
                with self.assertRaises(ValueError):candidate_history(history,atlas['professors'],current,queue,cache)

    def test_assembler_rejects_tampered_candidate_alias_target_or_snapshot_hash(self):
        for mode in ['target','hash']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);atlas,queue,current,history=self.fixture(cache)
                patches,_=candidate_history(history,atlas['professors'],current,queue,cache)
                aliases=patches['retained-original-id']['candidateObservationAliases']
                if mode=='target':aliases[0]['targetProfessorId']='another-id'
                else:aliases[0]['sourceRecordSha256']='0'*64
                combined=copy.deepcopy(current['byProfessorId']);attach_history_patches(combined,patches)
                data=minimal_atlas();data['professors']=copy.deepcopy(atlas['professors'])
                with self.assertRaisesRegex(ValueError,'candidate alias'):
                    build(data,{}, {}, {}, {},coverage_evidence={'byProfessorId':combined})
