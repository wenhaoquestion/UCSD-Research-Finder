import argparse
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import collect_ucsd_coverage as collector
from collection_scope import ScopePolicy, key as scope_key
from refresh_faculty_directories import safe_link
from queue_resource_keys import normalize_queue_keys, rebind_decisions, candidate_selector
from refresh_labs import make_lab
from network_coordination import HostRequestGate


class ExactQueueKeyTests(unittest.TestCase):
    def legacy(self, requested='https://lab.ucsd.edu/group/', literal=None):
        old='https://lab.ucsd.edu/group'
        source={'sourceUrl':requested,'finalUrl':requested,'status':'ok','observedAt':'2019-01-01','sha256':'body'}
        record=make_lab('Example Lab',literal or requested,'Physics',source,'Example Lab')
        return {'items':{old:{'url':requested,'state':'unresolved','attempts':3,'retryAt':1234567890,'contexts':[{'kind':'lab_destination','department':'Physics'}],'fetch':source}},
                'labCandidates':{old:{'record':record,'observations':[{'sourceUrl':'https://roster.ucsd.edu/','observedAt':'2018-01-01','label':'Example Lab'}]}},
                'centers':{old:{'id':'center-id','url':requested,'name':'Example Center','observations':[]}},'facultyListings':[],'sources':{}}

    def test_transport_keys_keep_paths_queries_hosts_and_protocols_distinct(self):
        for first,second in [('https://example.ucsd.edu/x','https://example.ucsd.edu/x/'),
                             ('https://example.ucsd.edu/','https://example.ucsd.edu//'),
                             ('http://example.ucsd.edu/','https://example.ucsd.edu/'),
                             ('https://example.ucsd.edu/','https://www.example.ucsd.edu/'),
                             ('https://example.ucsd.edu/x','https://example.ucsd.edu/x/index.html'),
                             ('https://example.ucsd.edu/x?a=1&b=2','https://example.ucsd.edu/x?b=2&a=1')]:
            with self.subTest(first=first):
                self.assertNotEqual(collector.url_key(first),collector.url_key(second))
                self.assertNotEqual(scope_key(first),scope_key(second))
        self.assertEqual(collector.url_key('https://example.ucsd.edu'),collector.url_key('https://example.ucsd.edu/#fragment'))
        self.assertEqual(collector.url_key('https://bad.ucsd.edu /'),'')
        literal = "https://example.ucsd.edu/Optics%20(Professor);v=2&lab=group+$'!@:"
        self.assertEqual(safe_link(literal), literal)
        self.assertEqual(safe_link(literal.replace('(', '%28')), literal.replace('(', '%28'))

    def test_reindex_preserves_whole_entries_failure_dates_retries_and_scientific_ids(self):
        state=self.legacy();before=copy.deepcopy(state)
        normalize_queue_keys(state)
        for collection in ['items','labCandidates','centers']:
            self.assertEqual(next(iter(state[collection].values())),next(iter(before[collection].values())))
            self.assertEqual(list(state[collection]),['https://lab.ucsd.edu/group/'])
        self.assertEqual(state['items']['https://lab.ucsd.edu/group/']['fetch']['observedAt'],'2019-01-01')
        self.assertEqual(state['items']['https://lab.ucsd.edu/group/']['retryAt'],1234567890)
        again=copy.deepcopy(state);normalize_queue_keys(state);self.assertEqual(state,again)

    def test_legacy_review_binds_its_actual_capture_and_does_not_accept_the_other_literal_path(self):
        state=self.legacy(literal='https://lab.ucsd.edu/group');before=copy.deepcopy(state)
        decisions={'labs':{'https://lab.ucsd.edu/group':{'action':'accept','stableLabId':'frozen-scientific-id','reason':'Actual captured page names the lab'}}}
        original=copy.deepcopy(decisions);normalize_queue_keys(state);bound=rebind_decisions(decisions,state)
        self.assertEqual(decisions,original)
        self.assertEqual(list(bound['labs']),['https://lab.ucsd.edu/group/'])
        self.assertEqual(bound['labs']['https://lab.ucsd.edu/group/']['stableLabId'],'frozen-scientific-id')
        self.assertEqual(bound['legacyDecisionKeyBindings'][0]['originalDecision'],original['labs']['https://lab.ucsd.edu/group'])
        record=next(iter(state['labCandidates'].values()))['record']
        self.assertEqual(record,next(iter(before['labCandidates'].values()))['record'])
        self.assertEqual(candidate_selector(state,record),'https://lab.ucsd.edu/group/')
        binding=state['requestResourceKeyMigration']['candidateRequestBindings'][0]
        self.assertFalse(binding['literalTargetVisitEstablished'])
        bound['labs']['https://lab.ucsd.edu/group']={'action':'hold','reason':'New independently visited path'}
        self.assertEqual(rebind_decisions(bound,state),bound,'New versioned exact selectors must never be remapped as old ones')
        policy=ScopePolicy(state,{'professors':[],'labs':[]},original)
        self.assertEqual(policy.decision({'url':'https://lab.ucsd.edu/group','contexts':[]}),{})

    def test_collision_failure_is_atomic_and_invalid_literals_are_not_turned_into_root_requests(self):
        state=self.legacy();state['items']['other-selector']=copy.deepcopy(next(iter(state['items'].values())))
        before=copy.deepcopy(state)
        with self.assertRaisesRegex(ValueError,'Duplicate exact resource'):normalize_queue_keys(state)
        self.assertEqual(state,before)
        invalid='https://bad.ucsd.edu /';state={'items':{invalid:{'url':invalid,'state':'scope_excluded','fetch':{'status':'robots_unavailable','observedAt':'2018-01-01'}}}}
        previous=copy.deepcopy(state['items']);normalize_queue_keys(state)
        self.assertEqual(state['items'],previous);self.assertNotIn('/',state['items']);self.assertNotIn('',state['items'])

    def test_distinct_legacy_decisions_cannot_silently_overwrite_each_other(self):
        state=self.legacy();decisions={'labs':{'https://lab.ucsd.edu/group':{'action':'accept'},'https://lab.ucsd.edu/group/':{'action':'hold'}}}
        with self.assertRaisesRegex(ValueError,'Two reviewed decisions'):rebind_decisions(decisions,state)

    def test_saved_literal_replay_recovers_either_slash_direction_without_inventing_a_variant(self):
        for old_uri,target in [('https://lab.ucsd.edu/group/','https://lab.ucsd.edu/group'),('https://lab.ucsd.edu/group','https://lab.ucsd.edu/group/')]:
            with self.subTest(old=old_uri),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);(cache/'responses').mkdir();source='https://roster.ucsd.edu/research'
                raw='<main><a href="'+target+'">Example Lab</a></main>'
                state=self.legacy(requested=old_uri,literal=target)
                state['items']['https://lab.ucsd.edu/group']['state']='done'
                for uri,body in [(source,raw),(old_uri,'<main>Example Lab</main>')]:
                    path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.write_text(body)
                    meta={'sourceUrl':uri,'finalUrl':uri,'status':'ok','observedAt':'2019-01-01','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
                    if uri==source:state['items'][uri]={'url':uri,'state':'done','depth':1,'contexts':[{'kind':'directory','department':'Physics'}],'fetch':meta}
                    else:state['items']['https://lab.ucsd.edu/group'].update(fetch=meta,depth=0)
                state.update(literalUriDiscoveryVersion=1,literalUriDiscoveryReplay={'version':1,'at':'2020-01-01'})
                normalize_queue_keys(state);queue=collector.Queue(cache/'queue.json');queue.state=state
                before={p:p.read_bytes() for p in (cache/'responses').glob('*')};old_fetch=copy.deepcopy(state['items'][old_uri]['fetch'])
                collector.replay_literal_uri_discovery(queue,cache,{'professors':[],'labs':[]})
                self.assertIn(target,queue.state['items']);self.assertEqual(queue.state['items'][target]['state'],'pending')
                self.assertEqual(queue.state['items'][old_uri]['fetch'],old_fetch)
                self.assertEqual(len(queue.state['labCandidates']),1,'Same old discovery case/ID survives the newly recovered literal link')
                self.assertEqual(queue.state['literalUriDiscoveryReplay']['wireRequests'],0)
                self.assertEqual(queue.state['literalUriDiscoveryReplayHistory'][0]['at'],'2020-01-01')
                for path,body in before.items():self.assertEqual(path.read_bytes(),body)
                snapshot=copy.deepcopy(queue.state);collector.replay_literal_uri_discovery(queue,cache,{'professors':[],'labs':[]});self.assertEqual(queue.state,snapshot)
                self.assertNotIn('https://www.lab.ucsd.edu/group/',queue.state['items'])

    def test_real_finite_batch_reads_a_legacy_key_and_requests_only_its_actual_uri(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data/ucsd').mkdir(parents=True);(root/'docs/operations').mkdir(parents=True)
            (root/'data/research-atlas.json').write_text(json.dumps({'professors':[],'labs':[]}));(root/'data/ucsd/departments.json').write_text(json.dumps({'departments':[]}))
            cache=root/'cache';cache.mkdir();uri='https://lab.ucsd.edu/group/'
            state=self.legacy();state['items']['https://lab.ucsd.edu/group'].update(state='pending',attempts=0,fetch={});state['items']['https://lab.ucsd.edu/group']['contexts']=[{'kind':'profile_identity_review','department':'Physics'}]
            (cache/'queue.json').write_text(json.dumps(state));raw='<main>Example Lab</main>'
            meta={'sourceUrl':uri,'finalUrl':uri,'status':'ok','observedAt':'2020-01-01','sha256':hashlib.sha256(raw.encode()).hexdigest()}
            class CacheOnly:
                def __init__(self):self.wire_requests=0;self.network_gate=HostRequestGate(cache/'test-gate');self.requested=[]
                def scheduling_wait(self,url):return 0
                def fetch(self,url):self.requested.append(url);return meta,raw
            fetcher=CacheOnly();args=argparse.Namespace(cache=cache,timeout=18,workers=1,max_pages=1,reparse_cached=False,reparse_profile_appointments=False)
            with patch.object(collector,'ROOT',root),patch.object(collector,'PublicFetcher',return_value=fetcher),patch.object(collector.Queue,'seed'),patch.object(collector.Queue,'retain_recent_profiles'),patch.object(collector.signal,'signal'),patch('builtins.print'):
                collector.collect(args)
            saved=json.loads((cache/'queue.json').read_text());self.assertEqual(fetcher.requested,[uri]);self.assertEqual(saved['items'][uri]['fetch'],meta);self.assertNotIn(uri.rstrip('/'),saved['items'])
