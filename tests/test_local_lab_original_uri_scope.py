"""Offline admission and scoped byte caps for reviewed original-URI observations."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
import urllib.parse
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import local_lab_summaries as ledger
import local_lab_summary_gaps as gaps


class OriginalURIObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=gaps.OUT)
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.out=self.root/'data/local-lab-summaries'
        self.cache=self.root/'collector';(self.cache/'responses').mkdir(parents=True)
        (self.out/'packets').mkdir(parents=True);(self.out/'records').mkdir()
        self.url='http://example.ucsd.edu/lab?view=1'
        self.meta={'sourceUrl':'https://example.ucsd.edu/lab?view=1',
            'observedAt':'2026-10-16T01:00:00+00:00','status':'http_error',
            'httpStatus':404,'finalUrl':'https://example.ucsd.edu/lab?view=1',
            'redirects':[],'error':'','actualPageRequestMade':True,
            'robots':{'sourceUrl':'https://example.ucsd.edu/robots.txt',
                'observedAt':'2026-10-16T00:59:00+00:00','status':'not_found','httpStatus':404}}
        self.packet={'labId':'one','labName':'Unconfirmed lab','listedWebsite':self.url,
            'preparedAt':'2026-10-16T01:30:00+00:00','destinationQueueStates':['done'],
            'latestDestinationFetch':copy.deepcopy(self.meta),'sources':[]}
        self.raw={'labId':'one','status':'unresolved','summaryZh':None,
            'researchQuestions':[],'topics':[],'methods':[],'evidence':[],
            'identity':{'status':'uncertain','entityType':'unconfirmed','reason':'not established'},
            'affiliation':{'status':'uncertain','reason':'unknown'},
            'uncertainty':['Research is unknown.'],'blockers':['No research text.'],
            'reviewedAt':'2026-10-16T01:30:00+00:00'}
        self.entry={'url':self.url,'listedWebsite':self.url,'labIds':['one'],
            'latestDestinationFetch':copy.deepcopy(self.meta),'observationOnly':True,
            'reviewedAt':'2026-10-16T02:00:00+00:00'}
        self.entries=[self.entry];self.decisions={'items':[]}
        self.capture={'url':self.url,'state':'done','fetch':copy.deepcopy(self.meta)}
        self.captures={'related':self.capture}
        self.baseline={'labs':[{'id':'one','labWebsiteUrl':self.url}]}
        self.write()
        baseline_hash=hashlib.sha256((self.root/'data/research-atlas.json').read_bytes()).hexdigest()
        for target,name,value in [(gaps,'ROOT',self.root),(gaps,'BASELINE_HASH',baseline_hash),
                (gaps,'OUT',self.out),(gaps,'CACHE',self.cache),(ledger,'ROOT',self.root),(ledger,'OUT',self.out)]:
            p=patch.object(target,name,value);p.start();self.addCleanup(p.stop)

    def put(self,name,data,base=None):
        path=(base or self.out)/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(data))

    def write(self):
        self.put('packets/one.json',self.packet);self.put('records/one.json',self.raw)
        self.put('reviewed-original-uri-observations.json',{'items':self.entries})
        self.put('identity-decisions.json',self.decisions)
        self.put('manifest.json',{'items':[{'labId':'one','packetPath':str(self.out/'packets/one.json')}]})
        self.put('queue.json',{'items':self.captures},self.cache)
        self.put('research-atlas.json',self.baseline,self.root/'data')

    def plan(self):
        self.write();return gaps.plan()

    def bind_current(self):
        self.entry['latestDestinationFetch']=copy.deepcopy(self.packet['latestDestinationFetch'])

    def size_proof(self):
        self.packet['latestDestinationFetch'].update(status='fetch_error',httpStatus=200,
            error='curl: (63) Maximum file size exceeded')
        self.bind_current();self.entry['maxPageBytes']=8_000_000
        proof={'items':[{'labId':'one','url':self.url,
            'latestDestinationFetch':copy.deepcopy(self.packet['latestDestinationFetch']),
            'maxPageBytes':8_000_000,'metadataOnly':True,
            'reviewedAt':'2026-10-16T02:00:00+00:00','decision':'bounded_original_uri_once_8mb'}]}
        path=self.out/'size-review.json';self.put(path.name,proof)
        self.entry.update(sizeLimitReviewPath=str(path),sizeLimitReviewSha256=hashlib.sha256(path.read_bytes()).hexdigest())
        return proof,path

    def execute_failure_fixture(self,candidate,stage,error):
        """Run the real journal/instrumentation with transport-only fakes."""
        case=self
        class FakePublicFetcher:
            def __init__(self,*args,**kwargs):case.last_fake_fetcher=self
            def _wire(self,url,minimum=1,max_bytes=2_000_000):return self._transport(url,max_bytes)
            def _transport(self,url,max_bytes):
                if stage=='after_original_response' and url==candidate['url']:
                    return 301,{'location':'https://example.ucsd.edu/lab'},'', ''
                if stage=='returned_error':return 0,{},'', 'curl returned a timeout error'
                raise error
            def fetch(self,url):
                if stage in {'before_wire','deferred'}:raise error
                parsed=urllib.parse.urlsplit(url)
                robots=urllib.parse.urlunsplit((parsed.scheme,parsed.netloc,'/robots.txt','',''))
                if stage=='robots':self._wire(robots,max_bytes=300_000)
                else:self._wire(url)
                if stage=='after_original_response':self._wire(robots,max_bytes=300_000)
                return {'sourceUrl':url,'observedAt':'2026-10-16T03:00:00+00:00',
                    'status':'fetch_error','httpStatus':0,'error':'curl returned a timeout error'},''
        module=types.SimpleNamespace(PublicFetcher=FakePublicFetcher,safe_url=lambda x:x)
        snapshot={'sourceHashes':{'collectorCodeSha256':'fixture'},'requiredSourceHashes':{}}
        self.put('network-coordination.json',dict(snapshot,adapterVerification={
            'adapterSha256':hashlib.sha256(Path(gaps.__file__).read_bytes()).hexdigest()}))
        with patch.object(gaps,'coordination_ready',return_value=True),patch.object(gaps,'coordination_snapshot',return_value=snapshot),\
                patch.object(gaps,'load_fetcher',return_value=module),\
                patch.object(gaps,'plan',return_value={'items':[candidate]}),contextlib.redirect_stdout(io.StringIO()):
            return gaps.execute(1)

    def test_unaccepted_entity_can_be_observed_without_acceptance_or_record_edits(self):
        before=[(self.out/name).read_bytes() for name in ['records/one.json','packets/one.json']]
        planned=gaps.plan();candidate=planned['items'][0]
        self.assertEqual(planned['liveCandidateCount'],1)
        self.assertEqual(candidate['kind'],'listed_url_direct_provenance_gap')
        self.assertTrue(candidate['observationOnly']);self.assertEqual(candidate['url'],self.url)
        self.assertEqual(candidate['maxPageBytes'],2_000_000)
        self.assertEqual(before,[(self.out/name).read_bytes() for name in ['records/one.json','packets/one.json']])
        _,verification=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(verification['entityAcceptanceStatus'],'provisional_or_unresolved')
        self.assertFalse(verification['canCountAsVerifiedLabGroupURL'])

    def test_related_robots_404_is_not_an_access_refusal(self):
        self.assertEqual(self.plan()['liveCandidateCount'],1)

    def test_https_robots_tls_failure_admits_only_the_standard_original_route(self):
        self.packet['latestDestinationFetch']={'sourceUrl':self.meta['sourceUrl'],
            'observedAt':self.meta['observedAt'],'status':'robots_unavailable',
            'robots':{'status':'unavailable','httpStatus':0,'attempts':3,'error':'curl: (35) SSL_ERROR_SYSCALL'}}
        self.bind_current();candidate=self.plan()['items'][0]
        self.assertEqual(candidate['latestDestinationFetch']['robots']['attempts'],3)
        self.assertTrue(candidate['observationOnly'])

    def test_full_metadata_binding_rejects_nested_or_uncited_field_changes(self):
        original=copy.deepcopy(self.packet['latestDestinationFetch'])
        for change in [lambda x:x['robots'].update(httpStatus=200),
                lambda x:x.update(error='new error'),lambda x:x.update(retrievedEpoch=123),
                lambda x:x.update(observedAt='2026-10-16T01:01:00+00:00'),
                lambda x:x.update(redirects=[{'from':x['sourceUrl'],'to':x['finalUrl'],'httpStatus':301}]),
                lambda x:x.update(actualPageRequestMade=1)]:
            with self.subTest(change=change):
                self.packet['latestDestinationFetch']=copy.deepcopy(original);change(self.packet['latestDestinationFetch'])
                self.assertEqual(self.plan()['items'],[])

    def test_missing_review_marker_or_timezone_is_rejected(self):
        original=copy.deepcopy(self.entry)
        for field,value in [('observationOnly',False),('observationOnly',1),('reviewedAt',None),
                ('reviewedAt','2026-10-16T02:00:00'),('listedWebsite','http://example.ucsd.edu/other')]:
            with self.subTest(field=field,value=value):
                self.entry.clear();self.entry.update(copy.deepcopy(original));self.entry[field]=value
                self.assertEqual(self.plan()['items'],[])

    def test_immutable_baseline_hash_and_literal_uri_are_required(self):
        self.baseline['labs'][0]['labWebsiteUrl']='http://example.ucsd.edu/invented'
        self.assertEqual(self.plan()['items'],[])
        self.baseline['labs'][0]['labWebsiteUrl']=self.url
        self.packet['listedWebsite']=self.url+'#fragment'
        self.assertEqual(self.plan()['items'],[])

    def test_no_new_host_path_query_scheme_or_www_alias(self):
        original=copy.deepcopy(self.packet['latestDestinationFetch'])
        for related in ['https://other.ucsd.edu/lab?view=1','https://www.example.ucsd.edu/lab?view=1',
                'https://example.ucsd.edu/lab/?view=1','https://example.ucsd.edu/lab?view=2',self.url]:
            with self.subTest(related=related):
                self.packet['latestDestinationFetch']=dict(original,sourceUrl=related);self.bind_current()
                self.assertEqual(self.plan()['items'],[])

    def test_explicit_root_or_robots_boundaries_and_status_codes_are_rejected(self):
        original=copy.deepcopy(self.packet['latestDestinationFetch'])
        for location in ['root','robots']:
            for boundary in [{'status':'robots_denied'},{'status':'authentication_required'},
                    {'status':'access_challenge'},{'httpStatus':401},{'httpStatus':403},
                    {'status':'not_found','httpStatus':404,'error':'access_challenge'}]:
                with self.subTest(location=location,boundary=boundary):
                    self.packet['latestDestinationFetch']=copy.deepcopy(original)
                    target=self.packet['latestDestinationFetch'] if location=='root' else self.packet['latestDestinationFetch']['robots']
                    target.update(boundary);self.bind_current();self.assertEqual(self.plan()['items'],[])

    def test_earlier_explicit_denial_is_not_erased_by_latest_success(self):
        self.packet['latestDestinationFetch']['attemptHistory']=[{'status':'authentication_required'}]
        self.bind_current();self.assertEqual(self.plan()['items'],[])

    def test_real_capture_top_level_related_refusal_history_is_rejected(self):
        for refusal in [{'status':'authentication_required','httpStatus':403},
                {'status':'robots_denied'},{'status':'access_challenge'},
                {'status':'ok','robots':{'httpStatus':401}}]:
            with self.subTest(refusal=refusal):
                self.capture['attemptHistory']=[dict(refusal,sourceUrl=self.meta['sourceUrl'],
                    observedAt='2026-10-16T00:30:00+00:00')]
                self.assertEqual(self.plan()['items'],[])

    def test_other_path_refusal_history_does_not_block_this_original_route(self):
        self.capture['attemptHistory']=[{'sourceUrl':'https://example.ucsd.edu/another-path',
            'status':'authentication_required','httpStatus':403}]
        self.assertEqual(self.plan()['liveCandidateCount'],1)

    def test_separately_captured_same_origin_robots_refusal_stays_relevant(self):
        self.captures['robots']={'url':'https://example.ucsd.edu/robots.txt','state':'unresolved',
            'fetch':{'sourceUrl':'https://example.ucsd.edu/robots.txt','httpStatus':403}}
        self.assertEqual(self.plan()['items'],[])

    def test_all_thirteen_decision_ids_and_raw_mismatch_flags_stay_excluded(self):
        for index in range(13):
            with self.subTest(index=index):
                self.decisions={'items':[{'labId':f'decision-{n}','unresolvedMismatch':True} for n in range(13)]}
                self.decisions['items'][index]['labId']='one'
                self.assertEqual(self.plan()['items'],[])
        self.decisions={'items':[]};self.raw['identity']['hasUnresolvedMismatch']=True
        self.assertEqual(self.plan()['items'],[])
        self.raw['identity'].pop('hasUnresolvedMismatch');self.raw['identity']['status']='mismatch'
        self.assertEqual(self.plan()['items'],[])

    def test_original_uri_metadata_including_prechecks_or_history_is_not_retried(self):
        for original in [{'sourceUrl':self.url,'status':'robots_unavailable'},
                {'sourceUrl':self.url,'status':'fetch_error','httpStatus':0},
                {'sourceUrl':self.url,'status':'ok','httpStatus':200}]:
            with self.subTest(original=original):
                self.capture['attemptHistory']=[original]
                self.assertEqual(self.plan()['items'],[])
        self.capture['attemptHistory']=[];self.capture['fetch']={'sourceUrl':self.url,'status':'robots_unavailable'}
        self.assertEqual(self.plan()['items'],[])

    def test_original_uri_visited_as_a_redirect_hop_also_closes_observation(self):
        self.capture['fetch']['redirects']=[{'from':self.url,'to':self.meta['finalUrl'],'httpStatus':301}]
        self.assertEqual(self.plan()['items'],[])

    def test_orphan_page_transport_start_closes_once_without_response_proof(self):
        self.put('gap-results.json',{'items':{},'wireEvents':[{'url':self.url,
            'kind':'page_or_redirect','startedAt':'2026-10-16T02:30:00+00:00'}]})
        self.assertEqual(self.plan()['items'],[])
        _,verification=ledger.hydrate(self.raw,self.packet)
        self.assertFalse(verification['listedUrlDirectlyChecked'])

    def test_orphan_robots_start_has_owner_or_journal_without_page_proof(self):
        for footprint in [{'wireEvents':[{'url':'http://example.ucsd.edu/robots.txt',
                'kind':'robots','originalObservationUrl':self.url}]},
                {'originalUriObservationStarts':{self.url:{'state':'started_not_completed',
                    'journalIsNotPageRequestProof':True}},'wireEvents':[]}]:
            with self.subTest(footprint=footprint):
                self.put('gap-results.json',dict(footprint,items={}))
                self.assertEqual(self.plan()['items'],[])
                _,verification=ledger.hydrate(self.raw,self.packet)
                self.assertFalse(verification['listedUrlDirectlyChecked'])

    def test_cached_http_origin_robots_denial_remains_enforced(self):
        robots='http://example.ucsd.edu/robots.txt';stem='robots-'+hashlib.sha256(robots.encode()).hexdigest()
        self.put(stem+'.json',{'status':'checked','sourceUrl':robots,'observedAt':self.meta['observedAt']},self.cache/'responses')
        (self.cache/'responses'/(stem+'.html')).write_text('User-agent: *\nDisallow: /\n')
        planned=self.plan();self.assertEqual(planned['liveCandidateCount'],0)
        self.assertEqual(planned['items'][0]['availability'],'access_boundary_do_not_bypass')

    def test_request_key_dedup_preserves_all_reviews_and_does_not_fold_slashes(self):
        self.entries.append(copy.deepcopy(self.entry));self.entries[1]['reviewedAt']='2026-10-16T02:01:00+00:00'
        planned=self.plan();self.assertEqual(len(planned['items']),1)
        self.assertEqual(len(planned['items'][0]['originalURIObservationReviews']),2)
        self.assertEqual(ledger.request_key('http://example.ucsd.edu'),ledger.request_key('http://example.ucsd.edu/'))
        self.assertNotEqual(ledger.request_key('http://example.ucsd.edu/lab'),ledger.request_key('http://example.ucsd.edu/lab/'))

    def test_existing_accepted_entity_route_does_not_gain_a_relaxed_gate(self):
        self.entries.clear();self.put('reviewed-listed-url-gaps.json',{'items':[{
            'url':self.url,'labIds':['one'],'relatedCapture':{'requestedUrl':self.meta['sourceUrl'],
                'sourceUrl':self.meta['finalUrl'],'observedAt':self.meta['observedAt'],'bodySha256':None}}]})
        self.assertEqual(self.plan()['items'],[])

    def test_only_exact_reviewed_8m_local_size_failure_gets_a_larger_cap(self):
        self.size_proof();candidate=self.plan()['items'][0]
        self.assertEqual(candidate['maxPageBytes'],8_000_000)
        self.assertEqual(candidate['latestDestinationFetch']['status'],'fetch_error')
        self.assertEqual(candidate['latestDestinationFetch']['httpStatus'],200)

    def test_other_caps_or_missing_size_proof_are_rejected(self):
        original=copy.deepcopy(self.entry)
        for cap in [8_000_000,9_000_000,2_000_001,False,2_000_000.0,'8000000']:
            with self.subTest(cap=cap):
                self.entry.clear();self.entry.update(copy.deepcopy(original));self.entry['maxPageBytes']=cap
                self.assertEqual(self.plan()['items'],[])

    def test_size_review_hash_full_binding_identity_and_scope_must_match(self):
        proof,path=self.size_proof();original=copy.deepcopy(proof)
        for field,value in [('labId','other'),('url','http://example.ucsd.edu/other'),
                ('metadataOnly',False),('reviewedAt','undated'),('maxPageBytes',9_000_000),
                ('decision','automatically_retry')]:
            with self.subTest(field=field):
                changed=copy.deepcopy(original);changed['items'][0][field]=value
                self.put(path.name,changed);self.entry['sizeLimitReviewSha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(self.plan()['items'],[])
        changed=copy.deepcopy(original);changed['items'][0]['latestDestinationFetch']['robots']['httpStatus']=200
        self.put(path.name,changed);self.entry['sizeLimitReviewSha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(self.plan()['items'],[])
        self.put(path.name,original);self.assertEqual(self.plan()['items'],[])

    def test_non_size_error_or_access_boundary_never_gets_8m(self):
        for patch_meta in [{'error':'curl: (6) Could not resolve host'},
                {'httpStatus':404},{'status':'access_challenge'},
                {'error':'curl: (63) Maximum file size exceeded','robots':{'httpStatus':403}}]:
            with self.subTest(patch_meta=patch_meta):
                self.size_proof();self.packet['latestDestinationFetch'].update(patch_meta);self.bind_current()
                self.assertEqual(self.plan()['items'],[])

    def test_response_exceeds_size_limit_is_an_explicit_local_failure(self):
        proof,path=self.size_proof();self.packet['latestDestinationFetch']['error']='response_exceeds_size_limit'
        self.bind_current();proof['items'][0]['latestDestinationFetch']=copy.deepcopy(self.packet['latestDestinationFetch'])
        self.put(path.name,proof);self.entry['sizeLimitReviewSha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(self.plan()['items'][0]['maxPageBytes'],8_000_000)

    def test_page_cap_is_scoped_per_fetch_and_redirect_robots_cap_unchanged(self):
        self.size_proof();candidate=self.plan()['items'][0]
        candidate2={'url':'http://second.ucsd.edu/','labIds':['two'],'requiresLiveFetch':True}
        calls=[]
        class FakePublicFetcher:
            def __init__(self,*args,**kwargs):pass
            def _wire(self,url,minimum=1,max_bytes=2_000_000):return self._transport(url,max_bytes)
            def _transport(self,url,max_bytes):
                calls.append((url,max_bytes));return 200,{},'body',''
            def fetch(self,url):
                parsed=urllib.parse.urlsplit(url)
                self._wire(urllib.parse.urlunsplit((parsed.scheme,parsed.netloc,'/robots.txt','','')),max_bytes=300_000)
                self._wire(url)
                self._wire(url+'/real-redirect-hop')
                return {'sourceUrl':url,'observedAt':'2026-10-16T03:00:00+00:00',
                    'status':'ok','httpStatus':200,'finalUrl':url},'body'
        module=types.SimpleNamespace(PublicFetcher=FakePublicFetcher,safe_url=lambda x:x)
        snapshot={'sourceHashes':{'collectorCodeSha256':'fixture'},'requiredSourceHashes':{}}
        self.put('network-coordination.json',dict(snapshot,adapterVerification={
            'adapterSha256':hashlib.sha256(Path(gaps.__file__).read_bytes()).hexdigest()}))
        with patch.object(gaps,'coordination_ready',return_value=True),patch.object(gaps,'coordination_snapshot',return_value=snapshot),\
                patch.object(gaps,'load_fetcher',return_value=module),\
                patch.object(gaps,'plan',return_value={'items':[candidate,candidate2]}),contextlib.redirect_stdout(io.StringIO()):
            result=gaps.execute(2)
        self.assertEqual(result['attempted'],2)
        self.assertEqual([cap for _,cap in calls],[300_000,8_000_000,8_000_000,300_000,2_000_000,2_000_000])
        actual=json.loads((self.out/'gap-results.json').read_text())
        self.assertEqual([e['maxResponseBytes'] for e in actual['wireEvents']],[cap for _,cap in calls])
        self.assertEqual(actual['items'][candidate['url']]['fetch']['summaryPageMaxBytes'],8_000_000)
        self.assertEqual(actual['items'][candidate2['url']]['fetch']['summaryPageMaxBytes'],2_000_000)

    def test_transport_exceptions_save_receipt_reset_cap_and_close_once(self):
        self.size_proof();candidate=self.plan()['items'][0]
        for stage in ['page','robots','before_wire']:
            for error in [RuntimeError('offline transport aborted'),subprocess.TimeoutExpired('offline fixture',1)]:
                with self.subTest(stage=stage,error=type(error).__name__):
                    (self.out/'gap-results.json').unlink(missing_ok=True)
                    with self.assertRaises(type(error)):self.execute_failure_fixture(candidate,stage,error)
                    saved=json.loads((self.out/'gap-results.json').read_text());meta=saved['items'][self.url]['fetch']
                    self.assertEqual(meta['status'],'fetch_exception')
                    self.assertEqual(meta['exceptionType'],type(error).__name__)
                    self.assertFalse(meta['actualPageRequestMade']);self.assertIsNone(meta['liveCheckedAt'])
                    self.assertFalse(any(key in meta for key in ['httpStatus','finalUrl','redirects','sha256']))
                    self.assertEqual(self.last_fake_fetcher.currentPageMaxBytes,2_000_000)
                    self.assertIsNone(self.last_fake_fetcher.currentOriginalObservationUrl)
                    self.assertEqual(self.plan()['liveCandidateCount'],0)
                    if stage!='before_wire':
                        event=saved['wireEvents'][0]
                        self.assertEqual(event['originalObservationUrl'],self.url)
                        self.assertEqual(event['requestOutcome'],'transport_started_response_indeterminate')
                        self.assertNotIn('httpStatus',event)
                        self.assertEqual(event['maxResponseBytes'],300_000 if stage=='robots' else 8_000_000)

    def test_keyboard_interrupt_is_not_swallowed_and_durable_start_closes_once(self):
        self.size_proof();candidate=self.plan()['items'][0]
        for stage in ['page','robots','before_wire']:
            with self.subTest(stage=stage):
                (self.out/'gap-results.json').unlink(missing_ok=True)
                with self.assertRaises(KeyboardInterrupt):self.execute_failure_fixture(candidate,stage,KeyboardInterrupt())
                saved=json.loads((self.out/'gap-results.json').read_text())
                self.assertEqual(saved['items'],{})
                self.assertEqual(saved['originalUriObservationStarts'][self.url]['state'],'started_not_completed')
                self.assertTrue(saved['originalUriObservationStarts'][self.url]['journalIsNotPageRequestProof'])
                self.assertEqual(self.last_fake_fetcher.currentPageMaxBytes,2_000_000)
                self.assertIsNone(self.last_fake_fetcher.currentOriginalObservationUrl)
                self.assertEqual(self.plan()['liveCandidateCount'],0)
                if stage!='before_wire':
                    event=saved['wireEvents'][0]
                    self.assertEqual(event['originalObservationUrl'],self.url)
                    self.assertNotIn('httpStatus',event)
                    self.assertFalse(event.get('transportReturned'))

    def test_returned_original_response_survives_later_exception_without_invented_final(self):
        self.size_proof();candidate=self.plan()['items'][0]
        with self.assertRaises(RuntimeError):self.execute_failure_fixture(candidate,'after_original_response',RuntimeError('robots aborted'))
        saved=json.loads((self.out/'gap-results.json').read_text());meta=saved['items'][self.url]['fetch']
        self.assertTrue(meta['actualPageRequestMade'])
        self.assertEqual(meta['liveCheckedAt'],saved['wireEvents'][0]['startedAt'])
        self.assertFalse(any(key in meta for key in ['finalUrl','redirects','sha256']))

    def test_returned_curl_error_is_attempt_evidence_but_deferred_zero_wire_is_not(self):
        self.size_proof();candidate=self.plan()['items'][0]
        self.execute_failure_fixture(candidate,'returned_error',None)
        saved=json.loads((self.out/'gap-results.json').read_text())
        self.assertTrue(saved['items'][self.url]['fetch']['actualPageRequestMade'])
        self.assertTrue(saved['wireEvents'][0]['transportReturned'])
        (self.out/'gap-results.json').unlink()
        self.execute_failure_fixture(candidate,'deferred',gaps.RetryAfterDeferred(self.url))
        saved=json.loads((self.out/'gap-results.json').read_text());meta=saved['items'][self.url]['fetch']
        self.assertEqual(saved['wireEvents'],[])
        self.assertEqual(meta['status'],'deferred_retry_after')
        self.assertFalse(meta['actualPageRequestMade']);self.assertIsNone(meta['liveCheckedAt'])
        self.assertFalse(any(key in meta for key in ['httpStatus','finalUrl','redirects','sha256']))


if __name__=='__main__':unittest.main()
