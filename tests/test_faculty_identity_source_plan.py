import contextlib
import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import collect_ucsd_coverage as collector
import plan_ucsd_faculty_identity_sources as planner


class FacultyIdentitySourcePlanTests(unittest.TestCase):
    def fixture(self, root):
        cache = root / '.cache/coverage-20261016'; (cache / 'responses').mkdir(parents=True)
        preview = cache / 'profile-qualification-preview'; preview.mkdir()
        (root / 'data/ucsd').mkdir(parents=True)
        (root / 'data/ucsd/departments.json').write_text(json.dumps({'departments':[{'name':'Physics'}]}))
        uri = 'https://profiles.ucsd.edu/jane.example'
        raw = '<main><div class="pageTitle"><h2>Jane Example</h2></div><table><tr><th>Title(s)</th><td>Professor, Physics</td></tr><tr><th>School</th><td>VC-Academic Affairs</td></tr></table></main>'
        path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest()+'.html'); path.write_text(raw)
        meta = {'sourceUrl':uri,'finalUrl':uri,'status':'ok','observedAt':'2020-01-01','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        q = collector.Queue(preview / 'queue.json');q.add(uri,'Physics','profile_discovery');q.state['items'][uri].update(state='done',fetch=meta);q.save()
        person = {'id':'known','name':'Jane A. Example','department':'Physics','officialProfileUrl':'http://profiles.ucsd.edu/Jane.Example','email':'jane@ucsd.edu'}
        atlas = {'professors':[person],'labs':[]}
        review = {'uncertainListings':[{'reason':'distinct_profile_same_or_similar_name_requires_identity_review','candidateProfessorIds':['known'],
                  'listing':{'name':'Jane Example','sourceUrl':uri,'profileUrl':uri,'observedAt':meta['observedAt']}}]}
        return cache,q,review,atlas,path

    def test_plan_schedules_only_the_literal_original_uri_and_never_establishes_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cache,q,review,atlas,_=self.fixture(root);before=copy.deepcopy(q.state)
            with patch.object(collector,'ROOT',root):plan,sources=planner.prepare_plan(review,q.state,atlas,cache)
            self.assertEqual(q.state,before)
            self.assertEqual([source['url'] for source in sources],['http://profiles.ucsd.edu/Jane.Example'])
            self.assertFalse(plan['cases'][0]['identityEstablished'])
            self.assertEqual(plan['cases'][0]['qualificationSource']['observedAt'],'2020-01-01')
            self.assertEqual(plan['cases'][0]['originalSourceQueueState'],'not_queued')

    def test_previous_failure_is_accounted_without_resetting_attempts_or_retry_deadline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cache,q,review,atlas,_=self.fixture(root);uri=atlas['professors'][0]['officialProfileUrl'];q.add(uri,'Physics','profile')
            q.state['items'][uri].update(state='unresolved',attempts=3,retryAt=1234567890,fetch={'status':'http_error','httpStatus':403,'observedAt':'2019-01-01'})
            before=copy.deepcopy(q.state)
            with patch.object(collector,'ROOT',root):plan,sources=planner.prepare_plan(review,q.state,atlas,cache)
            self.assertEqual(sources,[]);self.assertEqual(q.state,before)
            self.assertEqual(plan['cases'][0]['reviewStatus'],'existing_source_failure_retained_without_reset')
            self.assertEqual(plan['cases'][0]['originalSourceCapture']['httpStatus'],403)

    def test_fragment_or_composite_original_uri_is_retained_for_review_without_a_normalized_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cache,q,review,atlas,_=self.fixture(root)
            original=atlas['professors'][0]['officialProfileUrl']
            for suffix in ['#contact', '#https://profiles.ucsd.edu/another.person']:
                data=copy.deepcopy(atlas);data['professors'][0]['officialProfileUrl']=original+suffix
                before=copy.deepcopy(q.state)
                with patch.object(collector,'ROOT',root):plan,sources=planner.prepare_plan(review,q.state,data,cache)
                self.assertEqual(sources,[]);self.assertEqual(q.state,before)
                case=plan['cases'][0]
                self.assertEqual(case['originalProfileUri'],original+suffix)
                self.assertEqual(case['requestedTransportUri'],'')
                self.assertEqual(case['reviewStatus'],'original_uri_requires_transport_normalization_review')
                self.assertFalse(case['identityEstablished']);self.assertIsNone(case['originalSourceCapture'])

    def test_apply_wholly_retires_its_malformed_context_and_preserves_other_contexts_and_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cache,q,review,atlas,path=self.fixture(root)
            uri=atlas['professors'][0]['officialProfileUrl']+'#https://profiles.ucsd.edu/another.person'
            atlas['professors'][0]['officialProfileUrl']=uri
            (cache/'profile-qualification-preview/faculty-review.json').write_text(json.dumps(review))
            (root/'data/research-atlas.json').write_text(json.dumps(atlas))
            config_path=root/'data/ucsd/coverage-20261016-additional-sources.json'
            old={'url':'https://physics.ucsd.edu/','department':'Physics','kind':'directory'}
            malformed={'url':uri,'department':'Physics','kind':'profile_identity_review','professorId':'known','identitySourcePlan':planner.PLAN_NAME,'identitySourceCaseIds':['old-case']}
            config_path.write_text(json.dumps({'sources':[old,malformed]}));before=q.path.read_bytes();body=path.read_bytes()
            for _ in range(2):
                with patch.object(planner,'ROOT',root),patch.object(collector,'ROOT',root),patch.object(sys,'argv',['plan','--apply']),contextlib.redirect_stdout(io.StringIO()):planner.main()
            config=json.loads(config_path.read_text())
            self.assertEqual(config['sources'],[old]);self.assertEqual(len(config['retiredIdentitySourceContexts']),1)
            self.assertEqual(config['retiredIdentitySourceContexts'][0]['source'],malformed)
            self.assertEqual(q.path.read_bytes(),before);self.assertEqual(path.read_bytes(),body)

    def test_initial_nickname_external_and_directory_inputs_do_not_expand_the_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cache,q,review,atlas,_=self.fixture(root)
            for mode in ['initial','nickname','external','directory','unpublished']:
                data=copy.deepcopy(atlas);r=copy.deepcopy(review)
                if mode=='initial':data['professors'][0]['name']='J. Example'
                if mode=='nickname':data['professors'][0]['name']='Jean Example'
                if mode=='external':data['professors'][0]['officialProfileUrl']='https://example.edu/people/jane'
                if mode=='directory':data['professors'][0]['officialProfileUrl']='https://physics.ucsd.edu/people/faculty'
                if mode=='unpublished':r['uncertainListings'][0]['candidateProfessorIds']=['unpublished-id']
                with self.subTest(mode=mode),patch.object(collector,'ROOT',root):
                    plan,sources=planner.prepare_plan(r,q.state,data,cache)
                    self.assertEqual(sources,[]);self.assertEqual(plan['cases'],[])

    def test_changed_capture_or_non_faculty_table_cannot_authorize_a_source_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cache,q,review,atlas,path=self.fixture(root);original=path.read_text();uri=review['uncertainListings'][0]['listing']['sourceUrl']
            for mode in ['bytes','date','subject','title']:
                state=copy.deepcopy(q.state);data=copy.deepcopy(atlas);r=copy.deepcopy(review);path.write_text(original)
                if mode=='bytes':path.write_text('Changed body')
                if mode=='date':r['uncertainListings'][0]['listing']['observedAt']='2021-01-01'
                if mode=='subject':
                    data['professors'][0]['name']='Janet Example';r['uncertainListings'][0]['listing']['name']='Janet Example'
                if mode=='title':
                    path.write_text(original.replace('Professor, Physics','Research Associate, Physics'))
                    state['items'][uri]['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                with self.subTest(mode=mode),patch.object(collector,'ROOT',root),self.assertRaises(ValueError):
                    planner.prepare_plan(r,state,data,cache)

    def test_applied_plan_is_idempotent_and_never_writes_the_live_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cache,q,review,atlas,path=self.fixture(root)
            (cache/'profile-qualification-preview/faculty-review.json').write_text(json.dumps(review))
            (root/'data/research-atlas.json').write_text(json.dumps(atlas))
            config_path=root/'data/ucsd/coverage-20261016-additional-sources.json';old={'url':'https://physics.ucsd.edu/','department':'Physics','kind':'directory'}
            config_path.write_text(json.dumps({'sources':[old]}));live=cache/'queue.json';live.write_text('Live queue sentinel')
            original_live,original_body,original_preview=live.read_bytes(),path.read_bytes(),q.path.read_bytes()
            for _ in range(2):
                with patch.object(planner,'ROOT',root),patch.object(collector,'ROOT',root),patch.object(sys,'argv',['plan','--apply']),contextlib.redirect_stdout(io.StringIO()):
                    planner.main()
            config=json.loads(config_path.read_text());plan=json.loads((root/'data/ucsd'/planner.PLAN_NAME).read_text())
            self.assertEqual(len(config['sources']),2);self.assertEqual(config['sources'][0],old)
            self.assertEqual(plan['configuredNewSourceContexts'],0)
            self.assertEqual(live.read_bytes(),original_live);self.assertEqual(path.read_bytes(),original_body);self.assertEqual(q.path.read_bytes(),original_preview)

    def test_case_history_preserves_configured_references_and_can_restore_a_returning_case(self):
        old={'caseId':'case-a','reviewStatus':'source_check_scheduled','qualificationSource':{'observedAt':'2020-01-01'}}
        absent=planner.preserve_plan_history({'cases':[]},{'cases':[old]})
        self.assertEqual(absent['historicalCases'],[old])
        returning=planner.preserve_plan_history({'cases':[{**old,'reviewStatus':'captured_original_source_available_for_identifier_review'}]},absent)
        self.assertEqual(returning['historicalCases'],[])
        self.assertEqual(returning['cases'][0]['previousSourcePlanObservations'],[old])

    def test_apply_refuses_a_missing_exact_entry_from_a_broken_queue_adder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cache,q,review,atlas,_=self.fixture(root)
            original=atlas['professors'][0]['officialProfileUrl'];atlas['professors'][0]['officialProfileUrl']=original+'/'
            q.add(original,'Physics','profile');q.state['items'][collector.url_key(original)].update(state='done',fetch={'status':'ok','observedAt':'2019-01-01'});q.save()
            (cache/'profile-qualification-preview/faculty-review.json').write_text(json.dumps(review))
            (root/'data/research-atlas.json').write_text(json.dumps(atlas))
            config_path=root/'data/ucsd/coverage-20261016-additional-sources.json';config_path.write_text(json.dumps({'sources':[]}));before=config_path.read_bytes()
            actual_add = collector.Queue.add
            def broken_add(queue, uri, *args, **kwargs):
                return actual_add(queue, original if uri == original+'/' else uri, *args, **kwargs)
            with patch.object(planner,'ROOT',root),patch.object(collector,'ROOT',root),patch.object(collector.Queue,'add',broken_add),patch.object(sys,'argv',['plan','--apply']),contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as refused:planner.main()
            self.assertEqual(refused.exception.code,2);self.assertEqual(config_path.read_bytes(),before)
            self.assertFalse((root/'data/ucsd'/planner.PLAN_NAME).exists())
            saved=json.loads((cache/'faculty-identity-source-plan-preview'/planner.PLAN_NAME).read_text())
            self.assertFalse(saved['appliedToConfiguration']);self.assertFalse(saved['liveQueueWritten'])
            self.assertEqual(saved['unsafeQueueKeyCollisions'][0]['literalOriginalUri'],original+'/')
            self.assertIsNone(saved['unsafeQueueKeyCollisions'][0]['storedRequestedUri'])
