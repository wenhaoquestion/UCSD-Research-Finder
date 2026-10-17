"""Exercise finite real collection batches with a deterministic offline wire."""
import argparse
import copy
import hashlib
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import collect_ucsd_coverage as collector
from network_coordination import HostRequestGate
from collection_schedule import host_wait_seconds


class OfflineFetcher(collector.PublicFetcher):
    def __init__(self, cache):
        self.logical_time = [time.time()]
        self.requests = []
        super().__init__(cache, clock=lambda:self.logical_time[0], sleep=self.advance)
        self.network_gate = HostRequestGate(cache.parent / 'test-gate', clock=self.clock,
                                           monotonic=self.clock, sleep=self.advance)

    def advance(self, seconds):
        if seconds >= 30:
            raise RuntimeError('Offline fixture: this submitted task would wait for a cooling host')
        self.logical_time[0] += seconds

    def _transport(self, url, max_bytes):
        self.requests.append(url)
        if url.endswith('/robots.txt'):
            return 200, {'content-type':'text/plain'}, 'User-agent: *\nAllow: /\n', ''
        return 200, {'content-type':'text/html'}, '<main>Saved public profile.</main>', ''


class CollectionHostDeferralTests(unittest.TestCase):
    def fixture(self, root):
        (root / 'data/ucsd').mkdir(parents=True)
        (root / 'docs/operations').mkdir(parents=True)
        (root / 'data/research-atlas.json').write_text(json.dumps({'professors':[],'labs':[]}))
        (root / 'data/ucsd/departments.json').write_text(json.dumps({'departments':[]}))
        cache = root / 'cache'
        queue = collector.Queue(cache / 'queue.json')
        cold, warm = 'https://cold.ucsd.edu/faculty/example', 'https://warm.ucsd.edu/faculty/example'
        for uri in [cold, warm]:
            queue.add(uri, 'Pediatrics', 'profile_identity_review')
        queue.save()
        return cache, queue, OfflineFetcher(cache / 'responses'), cold, warm

    def run_batch(self, root, cache, fetcher, max_pages=1):
        args = argparse.Namespace(cache=cache, timeout=18, workers=1, max_pages=max_pages,
                                  reparse_cached=False, reparse_profile_appointments=False)
        with patch.object(collector, 'ROOT', root), patch.object(collector, 'PublicFetcher', return_value=fetcher), \
                patch.object(collector.Queue, 'seed'), patch.object(collector.Queue, 'retain_recent_profiles'), \
                patch.object(collector.signal, 'signal'), patch('builtins.print'):
            collector.collect(args)

    def test_known_cooling_host_does_not_consume_the_last_batch_slot_or_an_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache, queue, fetcher, cold, warm = self.fixture(root)
            fetcher.network_gate.defer(cold, fetcher.clock() + 3600, 'fixture_server_retry_after')
            clock_path = fetcher.network_gate.paths(cold)[2]
            original_clock = clock_path.read_bytes()
            self.run_batch(root, cache, fetcher)
            saved = json.loads(queue.path.read_text())
            self.assertEqual(fetcher.requests, ['https://warm.ucsd.edu/robots.txt', warm])
            self.assertEqual(saved['items'][warm]['state'], 'done')
            self.assertEqual(saved['items'][cold]['state'], 'pending')
            self.assertEqual(saved['items'][cold]['attempts'], 0)
            self.assertNotIn('fetch', saved['items'][cold])
            self.assertNotIn('attemptHistory', saved['items'][cold])
            self.assertEqual(clock_path.read_bytes(), original_clock)
            report=json.loads((root/'data/ucsd/coverage-20261016-report.json').read_text())
            self.assertIn('cold.ucsd.edu',report['hostScheduling']['deferredHosts'])
            self.assertEqual(report['blocked'],[])

    def test_independent_hosts_without_cooldown_use_the_allowed_two_page_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache, queue, fetcher, cold, warm = self.fixture(root)
            self.run_batch(root, cache, fetcher, max_pages=2)
            saved = json.loads(queue.path.read_text())
            self.assertEqual(fetcher.requests, ['https://cold.ucsd.edu/robots.txt',cold,
                                                'https://warm.ucsd.edu/robots.txt',warm])
            self.assertTrue(all(item['state']=='done' for item in saved['items'].values()))

    def test_deferring_an_older_failure_preserves_its_entire_entry_and_retry_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            cache,queue,fetcher,cold,warm=self.fixture(root)
            old={'sourceUrl':cold,'finalUrl':cold,'status':'http_error','httpStatus':500,'observedAt':'2019-01-01'}
            queue.state['items'][cold].update(attempts=2,fetch=old,attemptHistory=[copy.deepcopy(old)],
                retryAt=fetcher.clock()-1,retainedEvidenceHistory=[{'professorId':'old-person','observedAt':'2018-01-01'}])
            queue.save();before=copy.deepcopy(queue.state['items'][cold])
            fetcher.network_gate.defer(cold,fetcher.clock()+3600,'fixture_server_retry_after')
            self.run_batch(root,cache,fetcher)
            saved=json.loads(queue.path.read_text())
            self.assertEqual(saved['items'][cold],before)
            self.assertEqual(saved['items'][warm]['state'],'done')

    def test_cached_success_is_usable_during_host_cooldown_and_expired_cache_does_not_bypass_it(self):
        for age_days in [1,31]:
            with self.subTest(age_days=age_days), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                cache,queue,fetcher,cold,warm=self.fixture(root)
                fetcher.network_gate.defer(cold,fetcher.clock()+3600,'fixture_server_retry_after')
                meta_path,body_path=fetcher._paths(cold)
                raw=b'<main>Original saved profile.</main>'
                meta={'sourceUrl':cold,'finalUrl':cold,'status':'ok','observedAt':'2019-01-01',
                      'retrievedEpoch':fetcher.clock()-age_days*86400,'sha256':hashlib.sha256(raw).hexdigest()}
                meta_path.write_text(json.dumps(meta));body_path.write_bytes(raw)
                clock_path=fetcher.network_gate.paths(cold)[2]
                before={p:p.read_bytes() for p in [meta_path,body_path,clock_path]}
                self.run_batch(root,cache,fetcher)
                saved=json.loads(queue.path.read_text())
                if age_days==1:
                    self.assertEqual(fetcher.requests,[])
                    self.assertEqual(saved['items'][cold]['fetch'],meta)
                    self.assertEqual(saved['items'][cold]['state'],'done')
                    self.assertEqual(saved['items'][warm]['state'],'pending')
                else:
                    self.assertEqual(fetcher.requests,['https://warm.ucsd.edu/robots.txt',warm])
                    self.assertEqual(saved['items'][cold]['attempts'],0)
                    self.assertNotIn('fetch',saved['items'][cold])
                for path,original in before.items():
                    self.assertEqual(path.read_bytes(),original)

    def test_all_cooling_sources_wait_resumably_or_stop_without_attempts(self):
        for stop_early in [False,True]:
            with self.subTest(stop_early=stop_early), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                cache,queue,fetcher,cold,warm=self.fixture(root)
                del queue.state['items'][warm];queue.save()
                fetcher.network_gate.defer(cold,fetcher.clock()+60,'fixture_server_retry_after')
                waits=[]
                class Signal:
                    stopped=False
                    def is_set(self):return self.stopped
                    def wait(self,seconds):
                        waits.append(seconds)
                        if len(waits)>5:raise AssertionError('Deferred queue did not resume')
                        if stop_early:self.stopped=True
                        else:fetcher.logical_time[0]+=seconds
                        return self.stopped
                with patch.object(collector,'threading',SimpleNamespace(Event=Signal)):
                    self.run_batch(root,cache,fetcher)
                saved=json.loads(queue.path.read_text())
                self.assertTrue(waits)
                if stop_early:
                    self.assertEqual(fetcher.requests,[])
                    self.assertEqual(saved['items'][cold]['attempts'],0)
                    self.assertEqual(saved['collectionState'],'in_progress')
                    self.assertNotIn('fetch',saved['items'][cold])
                else:
                    self.assertEqual(fetcher.requests,['https://cold.ucsd.edu/robots.txt',cold])
                    self.assertEqual(saved['items'][cold]['attempts'],1)
                    self.assertEqual(saved['collectionState'],'completed')


class SchedulingClockTests(unittest.TestCase):
    def test_readiness_preserves_cooldown_under_wall_clock_jumps_without_writing_clocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            wall,mono=[1000],[100]
            gate=HostRequestGate(tmp,clock=lambda:wall[0],monotonic=lambda:mono[0])
            gate.defer('cold.ucsd.edu',1120,'fixture_server_retry_after')
            path=gate.paths('cold.ucsd.edu')[2];before=path.read_bytes()
            self.assertEqual(host_wait_seconds(gate,'https://cold.ucsd.edu/profile'),120)
            wall[0]=2000;mono[0]=110
            self.assertEqual(host_wait_seconds(gate,'https://cold.ucsd.edu/profile'),110)
            wall[0]=900;mono[0]=120
            self.assertEqual(host_wait_seconds(gate,'https://cold.ucsd.edu/profile'),220)
            self.assertEqual(host_wait_seconds(gate,'https://warm.ucsd.edu/profile'),0)
            self.assertEqual(path.read_bytes(),before)

    def test_profiles_minimum_and_previous_robots_interval_are_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            wall,mono=[1000],[100]
            gate=HostRequestGate(tmp,clock=lambda:wall[0],monotonic=lambda:mono[0])
            gate.seed('profiles.ucsd.edu',1000,1)
            self.assertEqual(host_wait_seconds(gate,'https://profiles.ucsd.edu/person'),10)
            gate.seed('slow.ucsd.edu',1000,90)
            self.assertEqual(host_wait_seconds(gate,'https://slow.ucsd.edu/person'),90)
            wall[0]+=10;mono[0]+=10
            self.assertEqual(host_wait_seconds(gate,'https://profiles.ucsd.edu/person'),0)
