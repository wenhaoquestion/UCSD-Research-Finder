"""Offline adapter integration: robots and redirect wires share one gate."""
import contextlib
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import local_lab_summary_gaps as gaps


class FakeSlot(dict):
    def record_response(self,status,headers):
        self.update(lastResponseStatus=status,responseCooldownSet=False)
        if status in {0,408,429,*range(500,600)} or 'retry-after' in headers:
            self.update(responseCooldownSet=True,notBeforeEpoch=time.time()+max(60,float(headers.get('retry-after',60))))
        return dict(self)

class SharedAdapterTests(unittest.TestCase):
    def test_wire_uri_policy_preserves_http_www_and_public_origin_validation(self):
        module=gaps.load_fetcher()
        url='http://www.cogsci.ucsd.edu/(Lab)?topic=one#section'
        self.assertEqual(module.safe_url(url),'http://www.cogsci.ucsd.edu/%28Lab%29?topic=one')
        for invalid in ['file:///tmp/lab','http://127.0.0.1/lab','http://localhost/lab','https://example.local/lab','https://user:secret@example.ucsd.edu/','https://example.ucsd.edu:8080/']:
            self.assertEqual(module.safe_url(invalid),'')

    def test_original_http_page_and_robots_redirects_keep_their_actual_addresses(self):
        module=gaps.load_fetcher();slots=[];held=[]
        base='http://www.cogsci.ucsd.edu';secure='https://www.cogsci.ucsd.edu'
        class Gate:
            @contextlib.contextmanager
            def request_slot(self,url,minimum_interval=1):
                slots.append(url);held.append(url)
                try:yield FakeSlot(lastRequestAt=time.time())
                finally:held.pop()
        def transport(fetcher,url,max_bytes):
            self.assertEqual(held,[url])
            if url==base+'/robots.txt':return 301,{'location':secure+'/robots.txt'},'', ''
            if url.endswith('/robots.txt'):return 404,{},'', ''
            if url==base+'/lab':return 301,{'location':secure+'/lab'},'', ''
            return 200,{'content-type':'text/html'},'<h1>Example Lab</h1>', ''
        with tempfile.TemporaryDirectory(dir=gaps.OUT) as temp:
            out=Path(temp);cache=out/'collector';cache.mkdir();(cache/'queue.json').write_text(json.dumps({'items':{}}))
            ledger={'items':{},'wireEvents':[],'wireRequestsTotal':0}
            with patch.object(gaps,'OUT',out),patch.object(gaps,'CACHE',cache),patch.object(module,'HostRequestGate',Gate),patch.object(module.PublicFetcher,'_transport',transport):
                fetcher=gaps.instrumented_fetcher(module,out/'own-cache',ledger)
                meta,_=fetcher.fetch(base+'/lab')
            self.assertEqual(slots,[base+'/robots.txt',secure+'/robots.txt',base+'/lab',secure+'/robots.txt',secure+'/lab'])
            self.assertEqual(meta['sourceUrl'],base+'/lab')
            self.assertEqual(meta['finalUrl'],secure+'/lab')
            self.assertEqual(meta['redirects'],[{'from':base+'/lab','to':secure+'/lab','httpStatus':301}])
            self.assertIsNotNone(gaps.page_live_event(module,base+'/lab',ledger['wireEvents']))

    def test_loaded_fetcher_expires_robots_memory_without_queue_lease(self):
        module=gaps.load_fetcher();clock=[1000.0]
        class Gate:pass
        with tempfile.TemporaryDirectory(dir=gaps.OUT) as temp,patch.object(module,'HostRequestGate',Gate),patch.object(module,'task_lease',create=True) as lease:
            fetcher=module.PublicFetcher(Path(temp),clock=lambda:clock[0])
            with patch.object(fetcher,'_wire',return_value=(200,{},'User-agent: *\nAllow: /\n','')) as wire:
                fetcher._rules('https://example.ucsd.edu/one')
                clock[0]+=86401
                fetcher._rules('https://example.ucsd.edu/two')
                self.assertEqual(wire.call_count,2)
            lease.assert_not_called()

    def test_encoded_request_matches_actual_page_wire(self):
        module=gaps.load_fetcher();url='https://www.ece.ucsd.edu/group/(Professor%20Name)'
        event={'url':module.safe_url(url),'kind':'page_or_redirect','startedAt':'2026-10-16T02:16:22+00:00'}
        self.assertIs(gaps.page_live_event(module,url,[event]),event)
        self.assertIsNone(gaps.page_live_event(module,url,[{'url':url,'kind':'robots'}]))

    def test_every_robots_redirect_and_page_transport_holds_shared_slot(self):
        module=gaps.load_fetcher();slots=[];held=[]
        class Gate:
            @contextlib.contextmanager
            def request_slot(self,url,minimum_interval=1):
                slots.append((url,minimum_interval));held.append(url)
                try:yield FakeSlot(lastRequestAt=time.time())
                finally:held.pop()
        def transport(fetcher,url,max_bytes):
            self.assertEqual(held,[url])
            if url.endswith('/robots.txt'):return 404,{},'', ''
            if url=='https://a.ucsd.edu/':return 302,{'location':'https://b.ucsd.edu/lab'},'', ''
            return 200,{'content-type':'text/html'},'<h1>Example Lab</h1>', ''
        with tempfile.TemporaryDirectory(dir=gaps.OUT) as temp:
            out=Path(temp);cache=out/'collector';cache.mkdir();(cache/'queue.json').write_text(json.dumps({'items':{}}))
            ledger={'items':{},'wireEvents':[],'wireRequestsTotal':0}
            with patch.object(gaps,'OUT',out),patch.object(gaps,'CACHE',cache),patch.object(module,'HostRequestGate',Gate),patch.object(module.PublicFetcher,'_transport',transport):
                fetcher=gaps.instrumented_fetcher(module,out/'own-cache',ledger)
                meta,body=fetcher.fetch('https://a.ucsd.edu/')
            self.assertEqual(meta['status'],'ok')
            self.assertEqual([x[0] for x in slots],['https://a.ucsd.edu/robots.txt','https://a.ucsd.edu/','https://b.ucsd.edu/robots.txt','https://b.ucsd.edu/lab'])
            self.assertEqual(ledger['wireRequestsTotal'],4)
            self.assertEqual(len(ledger['wireEvents']),4)
            self.assertIn('Example Lab',body)

    def test_retry_after_from_robots_stops_page_without_claiming_wire(self):
        module=gaps.load_fetcher()
        class Gate:
            @contextlib.contextmanager
            def request_slot(self,url,minimum_interval=1):yield FakeSlot(lastRequestAt=time.time())
        def transport(fetcher,url,max_bytes):return 429,{'retry-after':'600'},'', ''
        with tempfile.TemporaryDirectory(dir=gaps.OUT) as temp:
            out=Path(temp);cache=out/'collector';cache.mkdir();(cache/'queue.json').write_text(json.dumps({'items':{}}))
            ledger={'items':{},'wireEvents':[],'wireRequestsTotal':0}
            with patch.object(gaps,'OUT',out),patch.object(gaps,'CACHE',cache),patch.object(module,'HostRequestGate',Gate),patch.object(module.PublicFetcher,'_transport',transport):
                fetcher=gaps.instrumented_fetcher(module,out/'own-cache',ledger)
                meta,_=fetcher.fetch('https://a.ucsd.edu/')
                with self.assertRaises(gaps.RetryAfterDeferred):fetcher._wire('https://a.ucsd.edu/next')
            self.assertEqual(meta['status'],'robots_unavailable')
            self.assertEqual(len(ledger['wireEvents']),1)
            self.assertGreater(ledger['hostRetryAfter']['a.ucsd.edu'],time.time()+590)

    def test_hash_mismatch_refuses_before_process_probe_or_network(self):
        state={'state':'active','protocolVersion':gaps.PROTOCOL,'directory':str(gaps.SHARED),'robotsAndRedirectsIncluded':True,'profilesMinimumSeconds':10,'collectorCodeSha256':'wrong','coordinationCodeSha256':'wrong'}
        with patch.object(gaps,'read',return_value={'pid':1,'networkCoordination':state}),patch.object(Path,'is_dir',return_value=True),patch.object(gaps.subprocess,'run') as probe:
            with self.assertRaisesRegex(RuntimeError,'hashes differ'):gaps.coordination_snapshot()
            self.assertTrue(all(call.args[0][0]=='git' for call in probe.call_args_list))

    def test_exact_committed_source_can_match_running_code_after_edit(self):
        from types import SimpleNamespace
        import hashlib
        expected_bytes=b'# exact loaded source\n'
        expected=hashlib.sha256(expected_bytes).hexdigest()
        with tempfile.TemporaryDirectory(dir=gaps.OUT) as temp:
            out=Path(temp);path=out/'collector.py';path.write_text('# later working edit\n')
            result=SimpleNamespace(returncode=0,stdout=expected_bytes)
            with patch.object(gaps,'OUT',out),patch.object(gaps.subprocess,'run',return_value=result):
                data,origin=gaps.verified_source(path,expected)
        self.assertEqual(data,expected_bytes)
        self.assertIn('Git HEAD',origin)

    def test_changed_dependency_receipt_refuses_before_compilation(self):
        state={'collectorCodeSha256':'collector','coordinationCodeSha256':'gate',
               'requiredSourceFiles':{'collection_scope.py':'changed'}}
        with patch.object(gaps,'read',return_value={'networkCoordination':state}),patch.object(gaps,'verified_source') as source:
            with self.assertRaisesRegex(RuntimeError,'dependencies changed'):
                gaps.load_fetcher(expected_sources={'collection_scope.py':'approved'})
            source.assert_not_called()

    def test_partial_dependency_receipt_cannot_enable_current_loader(self):
        state={'collectorCodeSha256':'collector','coordinationCodeSha256':'gate',
               'requiredSourceFiles':{'collection_scope.py':'scope'}}
        with patch.object(gaps,'read',return_value={'networkCoordination':state}),patch.object(gaps,'verified_source') as source:
            with self.assertRaisesRegex(RuntimeError,'incomplete or inconsistent'):
                gaps.load_fetcher()
            source.assert_not_called()

    def test_cached_robots_denial_stops_new_route_without_request(self):
        import hashlib
        url='https://example.ucsd.edu/Research/Projects/'
        robots_url='https://example.ucsd.edu/robots.txt'
        stem='robots-'+hashlib.sha256(robots_url.encode()).hexdigest()
        with tempfile.TemporaryDirectory(dir=gaps.OUT) as temp:
            root=Path(temp);cache=root/'responses';cache.mkdir()
            (cache/(stem+'.json')).write_text(json.dumps({'sourceUrl':robots_url,'status':'checked','observedAt':'2026-10-16T00:59:43+00:00'}))
            (cache/(stem+'.html')).write_text('User-agent: *\nDisallow: /Research/\n')
            with patch.object(gaps,'OUT',root),patch.object(gaps,'CACHE',root):
                self.assertEqual(gaps.cached_robots_boundary(url)['decision'],'robots_denied_from_cached_rules_no_request')
                self.assertIsNone(gaps.cached_robots_boundary('https://example.ucsd.edu/'))

if __name__=='__main__':unittest.main()
