"""Provenance/accounting regressions for the independent summary ledger."""
import copy
import contextlib
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import local_lab_summaries as ledger
import local_lab_summary_gaps as gaps


class SummaryProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.packet={'labId':'stable-id','labName':'Example Lab','listedWebsite':'https://example.ucsd.edu/',
            'preparedAt':'2026-10-16T01:00:00+00:00','destinationQueueStates':['done'],
            'latestDestinationFetch':{'status':'ok','httpStatus':200,'finalUrl':'https://example.ucsd.edu/',
                'sourceUrl':'https://example.ucsd.edu/',
                'observedAt':'2026-10-01T01:00:00+00:00','redirects':[]},
            'sources':[{'sourceId':'src-1','sourceUrl':'https://example.ucsd.edu/',
                'requestedUrl':'https://example.ucsd.edu/',
                'observedAt':'2026-10-01T01:00:00+00:00','role':'listed_lab_destination',
                'text':'Example Lab at UCSD studies memory using behavioral experiments.',
                'title':'Example Lab','sourceContentDates':[{'kind':'dateModified','value':'2025-03-01'}]}]}
        digest=hashlib.sha256(self.packet['sources'][0]['text'].encode()).hexdigest()
        self.packet['sources'][0]['bodySha256']=digest
        self.packet['latestDestinationFetch']['sha256']=digest
        self.raw={'labId':'stable-id','status':'supported','summaryZh':'该实验室研究记忆，使用行为实验。',
            'topics':['记忆'],'methods':['行为实验'],'researchQuestions':[],
            'reviewedAt':'2026-10-16T02:00:00+00:00',
            'identity':{'status':'confirmed','entityType':'lab','reason':'明确自称'},
            'affiliation':{'status':'source_reported','reason':'明确UCSD'},
            'evidence':[{'sourceId':'src-1','quote':self.packet['sources'][0]['text'],
                         'supports':['identity','research','topics','methods','affiliation']}]}

    def test_capture_and_content_dates_are_not_replaced_by_review_time(self):
        summary,url=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(summary['observedAt'],['2026-10-01T01:00:00+00:00'])
        self.assertEqual(url['lastCheckedAt'],'2026-10-01T01:00:00+00:00')
        self.assertEqual(summary['sourceContentDates'][0]['dates'][0]['value'],'2025-03-01')

    def test_actual_request_key_preserves_scheme_host_and_path_boundaries(self):
        self.assertNotEqual(ledger.request_key('http://example.ucsd.edu/'),ledger.request_key('https://example.ucsd.edu/'))
        self.assertNotEqual(ledger.request_key('https://www.example.ucsd.edu/'),ledger.request_key('https://example.ucsd.edu/'))
        self.assertNotEqual(ledger.request_key('https://example.ucsd.edu/lab'),ledger.request_key('https://example.ucsd.edu/lab/'))
        self.assertEqual(ledger.request_key('https://example.ucsd.edu/(Lab)'),ledger.request_key('https://example.ucsd.edu/%28Lab%29'))
        self.assertNotEqual(ledger.request_key('https://example.ucsd.edu/a%2Fb'),ledger.request_key('https://example.ucsd.edu/a/b'))

    def test_direct_request_is_preferred_over_later_arrival_from_other_url(self):
        direct={'url':'https://example.ucsd.edu/','fetch':{'sourceUrl':'https://example.ucsd.edu/','observedAt':'2026-10-16T01:00:00+00:00'}}
        arrival={'url':'https://old.ucsd.edu/lab','fetch':{'sourceUrl':'https://old.ucsd.edu/lab','finalUrl':'https://example.ucsd.edu/','observedAt':'2026-10-16T02:00:00+00:00'}}
        primary,related=ledger.destination_captures(self.packet['listedWebsite'],[arrival,direct])
        self.assertEqual(primary,[direct]);self.assertEqual(related,[arrival])

    def test_https_variant_does_not_claim_original_http_check_or_redirect(self):
        self.packet['listedWebsite']='http://example.ucsd.edu/'
        self.packet['sources'][0]['role']='related_destination_variant'
        summary,url=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(summary['status'],'supported')
        self.assertEqual(url['listedUrl'],'http://example.ucsd.edu/')
        self.assertEqual(url['requestedUrl'],'https://example.ucsd.edu/')
        self.assertEqual(url['checkScope'],'related_url_request_only')
        self.assertEqual(url['redirectChain'],[])
        self.assertFalse(url['listedUrlDirectlyChecked'])
        self.assertFalse(url['canCountAsVerifiedLabGroupURL'])
        self.assertEqual(url['pageIdentity']['status'],'confirmed')

    @contextlib.contextmanager
    def listed_gap_plan_fixture(self):
        with tempfile.TemporaryDirectory(dir=ledger.OUT) as temp:
            root=Path(temp);out=root/'data';out.mkdir();(out/'records').mkdir();(out/'packets').mkdir();cache=root/'collector';cache.mkdir()
            self.packet['listedWebsite']='http://example.ucsd.edu/'
            self.packet['sources'][0]['role']='related_destination_variant'
            entry={'url':self.packet['listedWebsite'],'labIds':['stable-id'],'relatedCapture':{'requestedUrl':'https://example.ucsd.edu/','sourceUrl':'https://example.ucsd.edu/','observedAt':self.packet['latestDestinationFetch']['observedAt'],'bodySha256':self.packet['latestDestinationFetch']['sha256']}}
            normalized={'url':entry['url'],'state':'done','fetch':copy.deepcopy(self.packet['latestDestinationFetch'])}
            def write():
                for p,value in [(out/'manifest.json',{'items':[{'labId':'stable-id','packetPath':str(out/'packets/stable-id.json')}]}),(out/'records/stable-id.json',self.raw),(out/'packets/stable-id.json',self.packet),(out/'reviewed-listed-url-gaps.json',{'items':[entry]}),(cache/'queue.json',{'items':{'one':normalized}})]:p.write_text(json.dumps(value))
            write()
            with patch.object(gaps,'OUT',out),patch.object(gaps,'CACHE',cache),patch.object(ledger,'OUT',out):
                yield entry,normalized,write

    def test_supported_research_does_not_close_the_reviewed_original_http_request_gap(self):
        with self.listed_gap_plan_fixture():
            result=gaps.plan()
        self.assertEqual(result['liveCandidateCount'],1)
        self.assertEqual(result['items'][0]['url'],'http://example.ucsd.edu/')
        self.assertEqual(result['items'][0]['availability'],'not_captured')
        self.assertEqual(result['items'][0]['kind'],'listed_url_direct_provenance_gap')

    def test_changed_capture_or_unresolved_identity_cannot_admit_an_original_uri_gap(self):
        with self.listed_gap_plan_fixture() as (entry,_,write):
            entry['relatedCapture']['observedAt']='2026-10-02T01:00:00+00:00';write()
            self.assertEqual(gaps.plan()['items'],[])
            entry['relatedCapture']['observedAt']=self.packet['latestDestinationFetch']['observedAt']
            self.raw['identity']['hasUnresolvedMismatch']=True;write()
            self.assertEqual(gaps.plan()['items'],[])

    def test_actual_original_uri_access_denial_is_not_retried_as_a_normalization_gap(self):
        with self.listed_gap_plan_fixture() as (_,capture,write):
            capture.update(state='unresolved',fetch={'sourceUrl':'http://example.ucsd.edu/','observedAt':'2026-10-16T01:00:00+00:00','status':'robots_denied'})
            write();result=gaps.plan()
        self.assertEqual(result['liveCandidateCount'],0)
        self.assertEqual(result['items'][0]['availability'],'access_boundary_do_not_bypass')

    def test_related_redirect_chain_belongs_to_its_actual_requested_url(self):
        meta=self.packet['latestDestinationFetch'];meta.update(sourceUrl='https://old.ucsd.edu/lab',redirects=[{'from':'https://old.ucsd.edu/lab','to':'https://example.ucsd.edu/','httpStatus':301}])
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(url['requestedUrl'],'https://old.ucsd.edu/lab')
        self.assertEqual(url['listedUrl'],'https://example.ucsd.edu/')
        self.assertFalse(url['listedUrlDirectlyChecked'])
        self.assertFalse(url['canCountAsVerifiedLabGroupURL'])
        self.assertEqual(url['redirectChain'][0]['from'],url['requestedUrl'])

    def test_legacy_follow_targets_are_not_claimed_as_preserved_location_headers(self):
        self.packet['latestDestinationFetch']['redirects']=[{'from':'https://example.ucsd.edu/','to':'https://example.ucsd.edu/','httpStatus':301}]
        _,legacy=ledger.hydrate(self.raw,self.packet)
        self.assertFalse(legacy['redirectLocationHeadersPreserved'])
        self.assertTrue(any('Location' in x for x in legacy['verificationLimitations']))
        self.packet['latestDestinationUrlPolicy']='preserve_wire_uri_after_pinned_public_origin_validation'
        _,current=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(current['redirectTargetNormalizationPolicy'],self.packet['latestDestinationUrlPolicy'])
        self.assertFalse(any('旧采集器' in x for x in current['verificationLimitations']))

    def test_missing_request_provenance_never_counts_as_verified_listed_url(self):
        del self.packet['latestDestinationFetch']['sourceUrl']
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertIsNone(url['requestedUrl'])
        self.assertEqual(url['checkScope'],'unknown_request_provenance')
        self.assertFalse(url['canCountAsVerifiedLabGroupURL'])

    def test_saved_projection_audit_rejects_fabricated_listed_url_success_and_redirect(self):
        self.packet['listedWebsite']='http://example.ucsd.edu/'
        self.packet['sources'][0]['role']='related_destination_variant'
        summary,url=ledger.hydrate(self.raw,self.packet)
        summary['evidence'][0]['evidence']='Invented laboratory statement.'
        url['canCountAsVerifiedLabGroupURL']=True
        url['redirectChain']=[{'from':'http://example.ucsd.edu/','to':'https://example.ucsd.edu/','httpStatus':301}]
        url['attemptHistory']=[{'sourceUrl':'https://unrelated.ucsd.edu/','observedAt':url['lastCheckedAt']}]
        url['redirectLocationHeadersPreserved']=True
        with tempfile.TemporaryDirectory(dir=ledger.OUT) as temp:
            out=Path(temp);(out/'records').mkdir();(out/'packets').mkdir()
            packet_path=out/'packets/stable-id.json'
            fixture={'manifest.json':{'eligibleCount':1,'items':[{'labId':'stable-id','packetPath':str(packet_path)}]},
                'checkpoint.json':{'counts':{'supported':1},'validationErrors':[]},
                'queue.json':{'items':[{'labId':'stable-id','status':'supported'}]},
                'records/stable-id.json':self.raw,'packets/stable-id.json':self.packet}
            for name,value in fixture.items():(out/name).write_text(json.dumps(value))
            (out/'summaries.jsonl').write_text(json.dumps(summary)+'\n')
            (out/'url-verification.jsonl').write_text(json.dumps(url)+'\n')
            with patch.object(ledger,'OUT',out),patch.object(ledger,'ROOT',out):result=ledger.audit_outputs()
        self.assertFalse(result['passed'])
        self.assertTrue(any('direct listed URL' in e for e in result['errors']))
        self.assertTrue(any('redirect/final URL' in e for e in result['errors']))
        self.assertTrue(any('Saved evidence quote/source/time/hash' in e for e in result['errors']))
        self.assertTrue(any('Original URL attempt history' in e for e in result['errors']))
        self.assertTrue(any('redirect normalization/header provenance' in e for e in result['errors']))

    def test_same_final_url_and_second_cannot_borrow_another_request_identity_quote(self):
        self.packet['sources'][0]['requestedUrl']='https://other.ucsd.edu/arrival'
        self.packet['sources'][0].update(canonicalLinkUrls=['https://wrong.ucsd.edu/'],htmlMetaRefreshes=[{'targetUrl':'https://wrong.ucsd.edu/'}])
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(url['entityIdentity']['status'],'confirmed')
        self.assertEqual(url['pageIdentity']['status'],'uncertain')
        self.assertFalse(url['canCountAsVerifiedLabGroupURL'])
        self.assertEqual(url['canonicalLinkUrls'],[])
        self.assertEqual(url['htmlMetaRefreshes'],[])

    def test_same_request_and_second_cannot_borrow_another_body_identity_quote(self):
        self.packet['latestDestinationFetch']['sha256']='actual-capture'
        self.packet['sources'][0]['bodySha256']='different-capture'
        self.packet['sources'][0].update(canonicalLinkUrls=['https://wrong.ucsd.edu/'],htmlMetaRefreshes=[{'targetUrl':'https://wrong.ucsd.edu/'}])
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(url['pageIdentity']['status'],'uncertain')
        self.assertFalse(url['canCountAsVerifiedLabGroupURL'])
        self.assertEqual(url['canonicalLinkUrls'],[])
        self.assertEqual(url['htmlMetaRefreshes'],[])

    def test_redirect_without_an_actual_initial_request_url_proves_no_page_wire(self):
        for meta in [
            {'redirects':[{'httpStatus':301,'to':'https://example.ucsd.edu/'}]},
            {'sourceUrl':'invalid','redirects':[{'from':'invalid','httpStatus':302}]},
        ]:
            self.assertFalse(ledger.page_request_proven(meta))

    def test_identity_verification_requires_an_actual_capture_body_hash(self):
        del self.packet['latestDestinationFetch']['sha256']
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(url['pageIdentity']['status'],'uncertain')
        self.assertFalse(url['canCountAsVerifiedLabGroupURL'])

    def test_quote_not_present_in_capture_is_rejected(self):
        self.raw['evidence'][0]['quote']='Example Lab uses fMRI and machine learning.'
        with self.assertRaises(AssertionError):ledger.hydrate(self.raw,self.packet)

    def test_successful_http_does_not_confirm_entity(self):
        self.raw.update(status='partial',identity={'status':'uncertain','entityType':'unconfirmed','reason':'unmatched'})
        self.raw['blockers']=['The fetched page does not establish the named entity.']
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(url['httpStatus'],200)
        self.assertEqual(url['pageIdentity']['status'],'uncertain')

    def test_failure_retains_historical_identity_separately(self):
        self.packet['latestDestinationFetch'].update(status='http_error',httpStatus=404)
        summary,url=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(summary['identity']['status'],'confirmed')
        self.assertEqual(url['pageIdentity']['status'],'uncertain')
        self.assertIsNone(url['canonicalUrl'])
        self.assertEqual(summary['evidence'][0]['observedAt'],'2026-10-01T01:00:00+00:00')

    def test_directory_identity_is_not_destination_page_identity(self):
        self.packet['sources'][0]['role']='historical_field_labName'
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(url['entityIdentity']['status'],'confirmed')
        self.assertEqual(url['pageIdentity']['status'],'uncertain')

    def test_supported_requires_research_quote_and_matching_entity(self):
        self.raw['evidence'][0]['supports']=['identity']
        with self.assertRaises(AssertionError):ledger.hydrate(self.raw,self.packet)
        self.raw['evidence'][0]['supports']=['research']
        self.raw['identity']['status']='uncertain'
        with self.assertRaises(AssertionError):ledger.hydrate(self.raw,self.packet)

    def test_naive_or_fabricated_review_time_is_rejected(self):
        for value in ['2026-10-16','tomorrow',None]:
            self.raw['reviewedAt']=value
            with self.assertRaises(AssertionError):ledger.hydrate(self.raw,self.packet)

    def test_only_completed_accepted_additions_import(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'data/local-lab-summaries') as temp:
            root=Path(temp);(root/'data/ucsd').mkdir(parents=True)
            baseline=json.dumps({'labs':[{'id':'baseline'}]}).encode()
            (root/'data/research-atlas.json').write_bytes(baseline)
            export={'collectionState':'pending','labs':[{'id':'new-approved'},{'id':'unreviewed'}],
                'reviewedLabDecisions':[{'labId':'new-approved','decision':{'action':'accept'}}]}
            file=root/'data/ucsd/coverage-expansion-evidence.json';file.write_text(json.dumps(export))
            with patch.object(ledger,'ROOT',root),patch.object(ledger,'COLLECTION',root),patch.object(ledger,'BASELINE_HASH',hashlib.sha256(baseline).hexdigest()):
                self.assertEqual(len(ledger.load_labs()[0]),1)
                export['collectionState']='completed';file.write_text(json.dumps(export))
                labs,imports=ledger.load_labs()
                self.assertEqual([x['id'] for x in labs],['baseline','new-approved'])
                self.assertEqual(imports[0]['labId'],'new-approved')

    def test_gap_execution_refuses_unverified_coordinator_without_network(self):
        with patch.object(gaps,'coordination_ready',return_value=False):
            with self.assertRaisesRegex(RuntimeError,'Network not started'):
                gaps.execute(1)

    def test_fetcher_refuses_loaded_version_change_after_snapshot(self):
        with patch.object(gaps,'read',return_value={'networkCoordination':{'collectorCodeSha256':'changed'}}):
            with self.assertRaisesRegex(RuntimeError,'changed after the verified'):
                gaps.load_fetcher({'collectorCodeSha256':'verified'})

    def test_execution_refuses_changed_summary_adapter_before_any_fetch(self):
        with patch.object(gaps,'coordination_ready',return_value=True),patch.object(gaps,'coordination_snapshot',return_value={'sourceHashes':{},'requiredSourceHashes':{}}),patch.object(gaps,'read',return_value={'sourceHashes':{},'requiredSourceHashes':{},'adapterVerification':{'adapterSha256':'old'}}):
            with self.assertRaisesRegex(RuntimeError,'summary adapter changed'):
                gaps.execute(1)

    def test_reviewed_mismatch_cannot_reenter_accepted_counts(self):
        decisions={'items':[{'labId':'stable-id','unresolvedMismatch':True}]}
        with patch.object(ledger,'read',return_value=decisions):
            with self.assertRaisesRegex(AssertionError,'reviewed unresolved mismatch'):
                ledger.hydrate(self.raw,self.packet)

    def test_identity_mismatch_cannot_be_supported_or_accepted(self):
        self.raw['identity']['hasUnresolvedMismatch']=True
        with self.assertRaisesRegex(AssertionError,'unresolved identity mismatch'):
            ledger.hydrate(self.raw,self.packet)

    def test_robots_only_wire_does_not_claim_page_live_check(self):
        self.packet['latestDestinationCheckOrigin']='summary_task_live_request'
        self.packet['latestDestinationFetch'].update(status='robots_unavailable',actualPageRequestMade=False)
        self.packet['latestDestinationFetch'].pop('httpStatus')
        self.packet['latestDestinationFetch'].pop('sha256')
        self.packet['latestDestinationFetch']['robots']={'httpStatus':200}
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertFalse(url['liveCheckedByThisTask'])
        self.assertIsNone(url['liveCheckedAt'])
        self.assertFalse(url['pageRequestProven'])
        self.assertFalse(url['listedUrlDirectlyChecked'])
        self.assertIsNone(url['requestedUrl'])
        self.assertEqual(url['checkScope'],'listed_url_access_precheck_only')

    def test_real_initial_redirect_is_a_request_even_if_target_robots_blocks(self):
        meta=self.packet['latestDestinationFetch'];meta.pop('httpStatus');meta.pop('sha256')
        meta.update(status='robots_denied',redirects=[{'from':'https://example.ucsd.edu/','to':'https://target.ucsd.edu/','httpStatus':301}],blockedUrl='https://target.ucsd.edu/')
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertTrue(url['pageRequestProven'])
        self.assertTrue(url['listedUrlDirectlyChecked'])
        self.assertEqual(url['requestedUrl'],'https://example.ucsd.edu/')
        self.assertIsNone(url['canonicalUrl'])
        self.assertFalse(url['canCountAsVerifiedLabGroupURL'])

    def test_cache_reuse_preserves_original_request_proof_without_new_live_claim(self):
        self.packet['latestDestinationCheckOrigin']='summary_task_live_request'
        self.packet['latestDestinationFetch']['actualPageRequestMade']=False
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertTrue(url['pageRequestProven'])
        self.assertTrue(url['listedUrlDirectlyChecked'])
        self.assertFalse(url['liveCheckedByThisTask'])
        self.assertEqual(url['checkOrigin'],'summary_task_cache_reuse')
        self.assertIsNone(url['liveCheckedAt'])

    def test_failed_transport_attempt_is_distinct_from_robots_only(self):
        self.packet['latestDestinationFetch'].update(status='fetch_error',httpStatus=0,error='Could not resolve host')
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertTrue(url['pageRequestProven'])
        self.assertTrue(url['listedUrlDirectlyChecked'])
        self.assertEqual(url['failureCategory'],'dns_error')
        self.assertFalse(url['canCountAsVerifiedLabGroupURL'])

    def test_gap_discovery_retains_research_paths_and_excludes_shared_about(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'data/local-lab-summaries') as temp:
            root=Path(temp);out=root/'data';out.mkdir();(out/'records').mkdir()
            markup=root/'captured.html';markup.write_text('<main><h1>Lab</h1></main><nav><a href="research.html">Research</a><a href="/about/">About</a></nav>')
            packet={'latestDestinationFetch':{'status':'ok'},'sources':[{'role':'listed_lab_destination','sourceUrl':'https://example.ucsd.edu/labs/specific/index.html','observedAt':'2026-10-01T00:00:00+00:00','cachePath':str(markup)}]}
            packetpath=out/'packet.json';packetpath.write_text(json.dumps(packet))
            (out/'manifest.json').write_text(json.dumps({'items':[{'labId':'lab1','packetPath':str(packetpath)}]}))
            (out/'records/lab1.json').write_text(json.dumps({'status':'partial','identity':{'status':'confirmed','entityType':'lab'}}))
            cache=root/'cache';cache.mkdir();(cache/'queue.json').write_text(json.dumps({'items':{}}))
            with patch.object(gaps,'OUT',out),patch.object(gaps,'CACHE',cache),patch.object(ledger,'ROOT',root):
                result=gaps.plan()
            self.assertEqual([x['url'] for x in result['items']],['https://example.ucsd.edu/labs/specific/research.html'])

    def test_projects_anchors_stay_inside_the_specific_lab_path(self):
        dom=gaps.DOM('<nav><a href="projects.html">Projects</a><a href="/projects">Explore Our Projects</a></nav>')
        found=ledger.research_links(dom,'https://example.ucsd.edu/labs/specific/index.html')
        self.assertEqual(found,[('Projects','https://example.ucsd.edu/labs/specific/projects.html')])

    def test_html_refresh_does_not_replace_observed_http_destination(self):
        dom=gaps.DOM('<meta http-equiv="Refresh" content="0; url=\'https://new.example.ucsd.edu/\'">')
        self.packet['sources'][0]['htmlMetaRefreshes']=ledger.html_meta_refreshes(dom,self.packet['listedWebsite'])
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(url['canonicalUrl'],self.packet['listedWebsite'])
        self.assertEqual(url['redirectChain'],[])
        self.assertEqual(url['htmlMetaRefreshes'][0]['targetUrl'],'https://new.example.ucsd.edu/')
        self.assertFalse(url['htmlMetaRefreshes'][0]['isObservedHTTPRedirect'])
        self.assertEqual(url['htmlMetaRefreshes'][0]['sourceObservedAt'],'2026-10-01T01:00:00+00:00')

    def test_html_refresh_requires_a_public_http_target(self):
        markup='<meta http-equiv="refresh" content="0;url=javascript:alert(1)"><meta http-equiv="refresh" content="0;url=https://name:password@example.ucsd.edu/"><meta http-equiv="refresh" content="5;URL=/new">'
        found=ledger.html_meta_refreshes(gaps.DOM(markup),'https://example.ucsd.edu/old')
        self.assertEqual([x['targetUrl'] for x in found],['https://example.ucsd.edu/new'])

    def test_reviewed_cross_host_refresh_requires_the_literal_verified_directive(self):
        with tempfile.TemporaryDirectory(dir=ledger.OUT) as temp:
            root=Path(temp);out=root/'data';out.mkdir();(out/'records').mkdir();(out/'packets').mkdir();cache=root/'collector';cache.mkdir()
            html=root/'source.html';html.write_text('<meta http-equiv="Refresh" content="0;URL=https://new.example.ucsd.edu/">')
            entry={'url':'https://new.example.ucsd.edu/','labIds':['one'],'sourceId':'root-source','sourceObservedAt':'2026-10-16T01:00:00+00:00','sourceBodySha256':hashlib.sha256(html.read_bytes()).hexdigest(),'kind':'reviewed_identity_research_gap','discoveryMechanism':'html_meta_refresh','label':'HTML meta refresh','reason':'Actual reviewed HTML directive'}
            packet={'latestDestinationFetch':{'status':'ok'},'sources':[{'sourceId':'root-source','sourceUrl':'https://old.example.ucsd.edu/','observedAt':entry['sourceObservedAt'],'cachePath':str(html),'bodySha256':entry['sourceBodySha256']}]}
            for path,value in [(out/'manifest.json',{'items':[]}),(out/'records/one.json',{'status':'partial','identity':{'status':'uncertain','entityType':'unconfirmed'}}),(out/'packets/one.json',packet),(out/'reviewed-gap-additions.json',{'items':[entry]}),(cache/'queue.json',{'items':{}})]:path.write_text(json.dumps(value))
            with patch.object(gaps,'OUT',out),patch.object(gaps,'CACHE',cache),patch.object(ledger,'ROOT',root):
                planned=gaps.plan();self.assertEqual(len(planned['items']),1)
                self.assertTrue(planned['items'][0]['requiresLiveFetch'])
                entry['url']='https://unrelated.example.ucsd.edu/';(out/'reviewed-gap-additions.json').write_text(json.dumps({'items':[entry]}))
                self.assertEqual(gaps.plan()['items'],[])
                entry['url']='https://new.example.ucsd.edu/';entry['sourceBodySha256']='unreviewed';(out/'reviewed-gap-additions.json').write_text(json.dumps({'items':[entry]}))
                self.assertEqual(gaps.plan()['items'],[])

    def test_reviewed_uncertain_identity_can_plan_real_same_site_anchor(self):
        with tempfile.TemporaryDirectory(dir=ledger.OUT) as temp:
            root=Path(temp);out=root/'data';out.mkdir();(out/'records').mkdir();(out/'packets').mkdir();cache=root/'collector';cache.mkdir()
            html=root/'source.html';html.write_text('<nav><a href="research">Research</a></nav><main>Named person</main>')
            entry={'url':'https://example.ucsd.edu/research','labIds':['one'],'sourceId':'old-source','sourceObservedAt':'2026-10-16T01:00:00+00:00','kind':'reviewed_identity_research_gap','label':'Research','reason':'Actual named-page anchor'}
            packet={'latestDestinationFetch':{'status':'ok'},'sources':[{'sourceId':'old-source','sourceUrl':'https://example.ucsd.edu/','observedAt':entry['sourceObservedAt'],'cachePath':str(html)}]}
            for path,value in [(out/'manifest.json',{'items':[]}),(out/'records/one.json',{'status':'partial','identity':{'status':'uncertain','entityType':'personal_research_site'}}),(out/'packets/one.json',packet),(out/'reviewed-gap-additions.json',{'items':[entry]}),(cache/'queue.json',{'items':{}})]:path.write_text(json.dumps(value))
            with patch.object(gaps,'OUT',out),patch.object(gaps,'CACHE',cache),patch.object(ledger,'ROOT',root):
                planned=gaps.plan();self.assertEqual(len(planned['items']),1)
                self.assertTrue(planned['items'][0]['requiresLiveFetch'])
                packet['latestDestinationFetch']['status']='robots_denied';(out/'packets/one.json').write_text(json.dumps(packet))
                self.assertEqual(gaps.plan()['items'],[])

    def test_recovered_prose_requires_actual_source_review_receipt(self):
        with tempfile.TemporaryDirectory(dir=ledger.OUT) as temp:
            out=Path(temp);(out/'packets').mkdir()
            change={'labId':'one','sourceUrl':'https://example.ucsd.edu/'}
            (out/'extraction-impact.json').write_text(json.dumps({'items':[change]}))
            (out/'packets/one.json').write_text(json.dumps({'sources':[{'sourceId':'recovered','sourceUrl':change['sourceUrl'],'textExtractionVersion':ledger.EXTRACTION_VERSION}]}))
            with patch.object(ledger,'OUT',out):
                self.assertEqual(ledger.extraction_review_state()['pendingRecordCount'],1)
                receipt={'items':[{'labId':'one','reviewedAt':'2026-10-16T02:00:00+00:00','sourceIdsRead':['recovered'],'decision':'unchanged'}]}
                (out/'extraction-review-test.json').write_text(json.dumps(receipt))
                self.assertEqual(ledger.extraction_review_state()['pendingRecordCount'],0)

    def test_live_request_origin_includes_failed_live_checks(self):
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertFalse(url['liveCheckedByThisTask'])
        self.assertEqual(url['checkOrigin'],'reused_collection_capture')
        self.packet['latestDestinationCheckOrigin']='summary_task_live_request'
        self.packet['latestDestinationFetch'].update(status='http_error',httpStatus=503)
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertTrue(url['liveCheckedByThisTask'])
        self.assertEqual(url['checkOrigin'],'summary_task_live_request')
        self.assertEqual(url['lastCheckedAt'],'2026-10-01T01:00:00+00:00')

    def test_saved_projection_audit_rejects_wrong_url_id(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'data/local-lab-summaries') as temp:
            root=Path(temp);(root/'records').mkdir()
            files={'manifest.json':{'eligibleCount':1,'items':[{'labId':'one'}]},
                'checkpoint.json':{'counts':{'supported':1},'validationErrors':[]},
                'queue.json':{'items':[{'labId':'one','status':'supported'}]}}
            for name,data in files.items():(root/name).write_text(json.dumps(data))
            (root/'summaries.jsonl').write_text(json.dumps({'labId':'one','status':'supported','identity':{'status':'confirmed'},'entityAcceptanceStatus':'accepted_lab_group','evidence':[]})+'\n')
            (root/'url-verification.jsonl').write_text(json.dumps({'labId':'wrong'})+'\n')
            with patch.object(ledger,'OUT',root),patch.object(ledger,'ROOT',root):
                result=ledger.audit_outputs()
            self.assertFalse(result['passed'])
            self.assertTrue(any('url IDs' in x for x in result['errors']))

    def test_old_identity_quote_does_not_confirm_a_later_capture(self):
        self.packet['latestDestinationFetch']['observedAt']='2026-10-16T00:00:00+00:00'
        summary,url=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(summary['identity']['status'],'confirmed')
        self.assertEqual(url['pageIdentity']['status'],'uncertain')

    def test_saved_wire_audit_rejects_fabricated_page_check_time(self):
        with tempfile.TemporaryDirectory(dir=ledger.OUT) as temp:
            out=Path(temp);(out/'records').mkdir()
            fixture={'manifest.json':{'eligibleCount':0,'items':[]},'checkpoint.json':{'counts':{},'validationErrors':[]},'queue.json':{'items':[]},
                'gap-results.json':{'wireRequestsTotal':1,'wireEvents':[{'kind':'robots','startedAt':'2026-10-16T02:00:00+00:00','sharedProtocol':'fcntl-host-clock-v1'}],
                    'items':{'one':{'url':'https://example.ucsd.edu/','wireEventRange':[0,1],'fetch':{'actualPageRequestMade':True,'liveCheckedAt':'2026-10-16T02:01:00+00:00'}}}}}
            for name,value in fixture.items():(out/name).write_text(json.dumps(value))
            for name in ['summaries.jsonl','url-verification.jsonl']:(out/name).write_text('')
            with patch.object(ledger,'OUT',out),patch.object(ledger,'ROOT',out):result=ledger.audit_outputs()
            self.assertFalse(result['passed'])
            self.assertTrue(any('real wire event' in error for error in result['errors']))

    def test_title_identity_quote_keeps_its_location(self):
        self.raw['evidence'].append({'sourceId':'src-1','quote':'Example Lab','quoteLocation':'title','supports':['identity']})
        summary,_=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(summary['evidence'][-1]['evidenceLocation'],'title')
        self.raw['evidence'][-1]['quote']='Different Lab'
        with self.assertRaises(AssertionError):ledger.hydrate(self.raw,self.packet)


if __name__=='__main__':unittest.main()
