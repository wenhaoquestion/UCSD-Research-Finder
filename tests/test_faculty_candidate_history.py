import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from faculty_candidate_history import candidate_history, attach_history_patches
from faculty_profile_bindings import profile_metadata
from lab_resource_reviews import record_sha256
from rebuild_verified_atlas import merge_patch, build
from test_atlas_quality import atlas as minimal_atlas
from audit_ucsd_preservation import evidence_keys, source_urls
import test_faculty_profile_bindings as bindings_test
from collect_ucsd_coverage import profiles_appointment


class FacultyCandidateHistoryTests(unittest.TestCase):
    def fixture(self, cache):
        helper = bindings_test.FacultyProfileBindingTests()
        atlas, queue, review = helper.fixture(cache)
        old = atlas['professors'][0]
        old['researchSummary'] = 'Earlier observed summary.'
        old['fieldEvidence'] = {'researchSummary': {'sourceUrl': old['officialProfileUrl'], 'observedAt':'2019-01-01', 'method':'dated_quote', 'evidence':'Earlier observed summary.'}}
        old['sourceUrls'] = [old['officialProfileUrl']]
        entry = {'record':copy.deepcopy(old),'recordSha256':record_sha256(old),
                 'disposition':'retain_previous_observations','reason':'Preserve an earlier candidate snapshot without reapplying its scalar claims.'}
        history = {'sourceCandidateAtlasSha256':'a'*64,'entries':[entry]}
        return helper, atlas, queue, review, history

    def test_history_retains_old_evidence_and_sources_without_overwriting_current_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp)
            _, atlas, queue, _, history = self.fixture(cache)
            history['entries'][0]['sourceCandidateAtlasSha256']='b'*64
            current=copy.deepcopy(atlas['professors'][0]);current['researchSummary']='Newer supported summary.'
            current['fieldEvidence']={};current['sourceUrls']=[]
            before=copy.deepcopy(history)
            additions, archives=candidate_history(history,[current],{'professors':[]},queue,cache)
            self.assertFalse(archives)
            patches={};attach_history_patches(patches,additions);attach_history_patches(patches,additions)
            self.assertEqual(len(patches[current['id']]['previousFieldObservations']),1)
            self.assertEqual(patches[current['id']]['previousFieldObservations'][0]['sourceCandidateAtlasSha256'],'b'*64)
            merge_patch(current,patches[current['id']])
            self.assertEqual(current['researchSummary'],'Newer supported summary.')
            self.assertTrue(evidence_keys(history['entries'][0]['record']) <= evidence_keys(current))
            self.assertTrue(source_urls(history['entries'][0]['record']) <= source_urls(current))
            first=copy.deepcopy(current);merge_patch(current,patches[current['id']]);self.assertEqual(current,first)
            self.assertEqual(history,before)

    def test_peer_hold_archives_the_complete_old_candidate_and_never_publishes_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp)
            helper, atlas, queue, review, history=self.fixture(cache)
            uri=review['entries'][0]['captures'][1]['requestedUrl']
            helper.rewrite(queue,cache,uri,'href="https://profiles.ucsd.edu/jane.example"','href="https://profiles.ucsd.edu/jane.alias"')
            helper.rewrite(queue,cache,uri,'/123/123.rdf','/456/456.rdf')
            entry=history['entries'][0];entry['disposition']='pending_peer_profile_identity_review'
            entry['captures']=[profile_metadata(queue['items'][p['requestedUrl']],cache)[0] for p in review['entries'][0]['captures']]
            faculty={'professors':[],'uncertainListings':[{'reason':'distinct_profile_same_or_similar_name_requires_identity_review','listing':{'discoveryId':entry['record']['id']}}]}
            patches,archives=candidate_history(history,[],faculty,queue,cache)
            self.assertFalse(patches);self.assertEqual(archives[0]['record'],atlas['professors'][0]);self.assertTrue(archives[0]['candidateHistoryVerified'])
            with self.assertRaisesRegex(ValueError,'current proposal'):
                candidate_history(history,atlas['professors'],faculty,queue,cache)

    def test_changed_snapshots_unknown_owners_and_missing_hold_evidence_fail_before_application(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp)
            _,atlas,queue,_,history=self.fixture(cache)
            with self.assertRaisesRegex(ValueError,'another identity'):
                candidate_history(history,[],{'professors':[]},queue,cache)
            history['entries'][0]['record']['name']='Changed subject'
            with self.assertRaisesRegex(ValueError,'unchanged whole snapshot'):
                candidate_history(history,atlas['professors'],{'professors':[]},queue,cache)

    def unmapped_fixture(self, cache):
        helper, atlas, queue, review, history = self.fixture(cache)
        uri = atlas['professors'][0]['officialProfileUrl']
        helper.rewrite(queue,cache,uri,'Associate Professor, Pediatrics','Professor, Structural System Facility')
        proof, markup = profile_metadata(queue['items'][uri], cache)
        _, listing = profiles_appointment(queue['items'][uri]['fetch'], markup)
        entry = history['entries'][0]; entry['record']['id'] = listing['discoveryId']; entry['record']['department'] = 'Unknown'
        entry['record']['directoryListings'] = [copy.deepcopy(listing)]
        entry['recordSha256'] = record_sha256(entry['record'])
        entry.update(disposition='pending_unmapped_unit_legacy_alias_review', captures=[proof], candidateProfessorIds=['legacy-catalog-id'])
        legacy = copy.deepcopy(atlas['professors'][0]); legacy.update(id='legacy-catalog-id',name='J. Example',department='Structural Engineering',officialProfileUrl='https://catalog.ucsd.edu/faculty/SE.html')
        faculty = {'professors':[],'uncertainListings':[{'reason':'unmapped_unit_legacy_initials_requires_identity_review', 'listing':listing, 'candidateProfessorIds':['legacy-catalog-id']}]}
        return history, [legacy], faculty, queue

    def test_unmapped_initial_alias_keeps_the_whole_previous_candidate_without_publishing_or_merging_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);history,people,faculty,queue=self.unmapped_fixture(cache)
            before=copy.deepcopy((history,people,faculty,queue))
            patches,archives=candidate_history(history,people,faculty,queue,cache)
            self.assertEqual(patches,{})
            self.assertEqual(archives[0]['record'],history['entries'][0]['record'])
            self.assertTrue(archives[0]['candidateHistoryVerified'])
            self.assertEqual((history,people,faculty,queue),before)
            data = minimal_atlas(); data['professors'] = copy.deepcopy(people)
            assembled, _, _, quarantine = build(data, {}, {}, {}, {}, coverage_evidence={'heldFacultyCandidates': archives})
            self.assertEqual([p['id'] for p in assembled['professors']], ['legacy-catalog-id'])
            self.assertIn(archives[0], quarantine)
            with self.assertRaisesRegex(ValueError,'current proposal'):
                candidate_history(history,people+[history['entries'][0]['record']],faculty,queue,cache)

    def test_unmapped_archive_requires_unchanged_own_capture_current_hold_and_compatible_original_identity(self):
        for mode in ['no_hold','changed_date','wrong_candidate','changed_bytes']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);history,people,faculty,queue=self.unmapped_fixture(cache)
                if mode=='no_hold':faculty['uncertainListings']=[]
                if mode=='changed_date':faculty['uncertainListings'][0]['listing']['observedAt']='2022-01-01'
                if mode=='wrong_candidate':people[0]['name']='K. Example'
                if mode=='changed_bytes':
                    uri=history['entries'][0]['captures'][0]['requestedUrl']
                    path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.write_text(path.read_text()+'<!-- changed -->')
                with self.assertRaises(ValueError):candidate_history(history,people,faculty,queue,cache)
