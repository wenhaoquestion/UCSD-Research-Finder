"""Real process-lock tests, plus clock-policy tests without live network I/O."""
import hashlib
import json
import multiprocessing
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from network_coordination import HostRequestGate, migrate_legacy_clocks, PROTOCOL_VERSION
from collect_ucsd_coverage import PublicFetcher


class ProcessClock:
    def __init__(self, value):
        self.value = value
    def now(self):
        with self.value.get_lock():
            return self.value.value
    def advance(self, seconds):
        with self.value.get_lock():
            self.value.value += seconds


def wire_worker(directory, host, clock_value, active, maximum, result, barrier=None, logical=True):
    clock = ProcessClock(clock_value)
    gate = HostRequestGate(directory, clock=clock.now, monotonic=clock.now, sleep=clock.advance) if logical else HostRequestGate(directory)
    with gate.request_slot('https://' + host + '/robots.txt', 1) as slot:
        with active.get_lock():
            active.value += 1
            with maximum.get_lock():
                maximum.value = max(maximum.value, active.value)
        if barrier:
            barrier.wait(timeout=5)
        time.sleep(.15)
        result.put((host, slot['lastRequestAt']))
        with active.get_lock():
            active.value -= 1


def cooldown_worker(directory, clock_value, ready, result, path, status, headers, wait=False):
    if wait:
        ready.wait(timeout=5)
    clock = ProcessClock(clock_value)
    gate = HostRequestGate(directory, clock=clock.now, monotonic=clock.now, sleep=clock.advance)
    with gate.request_slot('https://lab.ucsd.edu/' + path) as slot:
        start = slot['lastRequestAt']
        policy = slot.record_response(status, headers)
        if not wait:
            ready.set()
            time.sleep(.05)
        result.put((path, start, policy.get('notBeforeEpoch')))


class CooldownFetcher(PublicFetcher):
    def __init__(self, cache, directory, logical, pages):
        self.logical, self.pages, self.requests = logical, pages, []
        super().__init__(cache, clock=lambda: logical[0], sleep=self.advance)
        self.network_gate = HostRequestGate(directory, clock=lambda: logical[0], monotonic=lambda: logical[0], sleep=self.advance)

    def advance(self, seconds):
        self.logical[0] += seconds

    def _transport(self, url, max_bytes):
        self.requests.append((url, self.logical[0]))
        return self.pages[url]


class SharedNetworkTests(unittest.TestCase):
    def run_processes(self, hosts, *, barrier=False, logical=True):
        ctx = multiprocessing.get_context('spawn')
        with tempfile.TemporaryDirectory() as directory:
            clock, active, maximum = ctx.Value('d', 1000), ctx.Value('i', 0), ctx.Value('i', 0)
            result = ctx.Queue()
            sync = ctx.Barrier(len(hosts)) if barrier else None
            processes = [ctx.Process(target=wire_worker, args=(directory, host, clock, active, maximum, result, sync, logical)) for host in hosts]
            for process in processes:
                process.start()
            try:
                for process in processes:
                    process.join(timeout=10)
                    self.assertFalse(process.is_alive(), 'wire process deadlocked')
                    self.assertEqual(process.exitcode, 0)
                rows = [result.get(timeout=2) for _ in hosts]
                states = [json.loads(p.read_text()) for p in Path(directory).glob('*.json')]
                return rows, maximum.value, states
            finally:
                for process in processes:
                    if process.is_alive():
                        process.terminate()
                        process.join(timeout=2)
                result.close()

    def test_independent_processes_share_profiles_clock_and_wire_lock(self):
        rows, maximum, states = self.run_processes(['profiles.ucsd.edu', 'profiles.ucsd.edu'])
        starts = sorted(t for _, t in rows)
        self.assertEqual(maximum, 1)
        self.assertGreaterEqual(starts[1] - starts[0], 10)
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0]['protocolVersion'], PROTOCOL_VERSION)

    def test_actual_wall_clock_interval_is_shared_across_processes(self):
        rows, maximum, _ = self.run_processes(['lab.ucsd.edu', 'lab.ucsd.edu'], logical=False)
        starts = sorted(t for _, t in rows)
        self.assertEqual(maximum, 1)
        self.assertGreaterEqual(starts[1] - starts[0], .99)

    def test_different_hosts_can_do_wire_work_concurrently(self):
        _, maximum, states = self.run_processes(['one.ucsd.edu', 'two.ucsd.edu'], barrier=True)
        self.assertEqual(maximum, 2)
        self.assertEqual(len(states), 2)

    def test_migration_keeps_cache_dates_and_strongest_interval(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            cache = base / 'cache'
            cache.mkdir()
            for netloc, stamp in [('profiles.ucsd.edu', 1000), ('profiles.ucsd.edu:443', 1005)]:
                (cache / ('clock-' + hashlib.sha256(netloc.encode()).hexdigest() + '.json')).write_text(json.dumps({'lastRequestAt': stamp}))
            robot_url = 'https://profiles.ucsd.edu/robots.txt'
            stem = 'robots-' + hashlib.sha256(robot_url.encode()).hexdigest()
            (cache / (stem + '.json')).write_text(json.dumps({'status': 'checked', 'observedAt': '2026-10-01T00:00:00+00:00'}))
            (cache / (stem + '.html')).write_text('User-agent: *\nCrawl-delay: 20\n')
            source = cache / 'old-observation.json'
            source.write_text(json.dumps({'observedAt': '2026-10-01T00:00:00+00:00', 'evidence': 'Original capture'}))
            before = {p.name: p.read_bytes() for p in cache.iterdir()}
            logical = [1006.0]
            gate = HostRequestGate(base / 'coordination', clock=lambda: logical[0], monotonic=lambda: logical[0], sleep=lambda seconds: logical.__setitem__(0, logical[0] + seconds))
            receipt = migrate_legacy_clocks(cache, ['https://profiles.ucsd.edu/person', 'https://profiles.ucsd.edu:443/person'], gate, 'ResearchAtlasEvidenceBot/2.0')
            with gate.request_slot('http://profiles.ucsd.edu/next', 1) as slot:
                self.assertEqual(slot['lastRequestAt'], 1025)
                self.assertEqual(slot['minimumIntervalSeconds'], 20)
            self.assertEqual(receipt['legacyClocksImported'], 2)
            self.assertEqual(before, {p.name: p.read_bytes() for p in cache.iterdir()})

    def test_two_processes_and_urls_share_retry_after_and_default_backoff(self):
        ctx = multiprocessing.get_context('spawn')
        for code, headers, delay in [(429, {'Retry-After': '120'}, 120), (429, {'Retry-After': 'Thu, 01 Jan 1970 00:20:00 GMT'}, 200), (503, {}, 60), (522, {}, 60)]:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as directory:
                clock, ready, result = ctx.Value('d', 1000), ctx.Event(), ctx.Queue()
                processes = [ctx.Process(target=cooldown_worker, args=(directory, clock, ready, result, 'one', code, headers)),
                             ctx.Process(target=cooldown_worker, args=(directory, clock, ready, result, 'two', 200, {}, True))]
                for p in processes:
                    p.start()
                try:
                    for p in processes:
                        p.join(timeout=10)
                        self.assertFalse(p.is_alive())
                        self.assertEqual(p.exitcode, 0)
                    rows = {row[0]: row[1:] for row in [result.get(timeout=2), result.get(timeout=2)]}
                    self.assertGreaterEqual(rows['two'][0], rows['one'][0] + delay)
                    self.assertGreaterEqual(rows['one'][1], rows['one'][0] + delay)
                finally:
                    for p in processes:
                        if p.is_alive():
                            p.terminate(); p.join(timeout=2)
                    result.close()

    def test_robots_retry_after_delays_another_fetcher_before_its_robots(self):
        with tempfile.TemporaryDirectory() as temporary:
            base, logical = Path(temporary), [1000.0]
            first = CooldownFetcher(base / 'one', base / 'gate', logical, {'https://lab.ucsd.edu/robots.txt': (429, {'retry-after': '90'}, '', '')})
            meta, _ = first.fetch('https://lab.ucsd.edu/one')
            self.assertEqual(meta['status'], 'robots_unavailable')
            self.assertEqual(meta['robots']['retryAfterEpoch'], 1090)
            second = CooldownFetcher(base / 'two', base / 'gate', logical, {
                'https://lab.ucsd.edu/robots.txt': (404, {}, '', ''),
                'https://lab.ucsd.edu/two': (200, {'content-type': 'text/html'}, '<h1>Lab</h1>', '')})
            self.assertEqual(second.fetch('https://lab.ucsd.edu/two')[0]['status'], 'ok')
            self.assertGreaterEqual(second.requests[0][1], 1090)

    def test_page_default_backoff_delays_another_url_and_fetcher(self):
        with tempfile.TemporaryDirectory() as temporary:
            base, logical = Path(temporary), [1000.0]
            first = CooldownFetcher(base / 'one', base / 'gate', logical, {
                'https://lab.ucsd.edu/robots.txt': (404, {}, '', ''), 'https://lab.ucsd.edu/one': (503, {}, '', '')})
            meta, _ = first.fetch('https://lab.ucsd.edu/one')
            deadline = meta['retryAfterEpoch']
            second = CooldownFetcher(base / 'two', base / 'gate', logical, {
                'https://lab.ucsd.edu/robots.txt': (404, {}, '', ''), 'https://lab.ucsd.edu/two': (200, {'content-type': 'text/html'}, 'Lab', '')})
            second.fetch('https://lab.ucsd.edu/two')
            self.assertGreaterEqual(second.requests[0][1], deadline)

    def test_page_redirect_retry_after_is_honored_before_target_robots(self):
        with tempfile.TemporaryDirectory() as temporary:
            base, logical = Path(temporary), [1000.0]
            fetch = CooldownFetcher(base / 'cache', base / 'gate', logical, {
                'https://a.ucsd.edu/robots.txt': (404, {}, '', ''),
                'https://a.ucsd.edu/start': (302, {'location': 'https://b.ucsd.edu/end', 'retry-after': '90'}, '', ''),
                'https://b.ucsd.edu/robots.txt': (404, {}, '', ''),
                'https://b.ucsd.edu/end': (200, {'content-type': 'text/html'}, 'Lab', '')})
            meta, _ = fetch.fetch('https://a.ucsd.edu/start')
            self.assertEqual(meta['status'], 'ok')
            starts = dict(fetch.requests)
            self.assertGreaterEqual(starts['https://b.ucsd.edu/robots.txt'], starts['https://a.ucsd.edu/start'] + 90)
            self.assertEqual(meta['redirects'][0]['retryAfterEpoch'], 1091)

    def test_robots_redirect_retry_after_is_honored_before_redirect_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            base, logical = Path(temporary), [1000.0]
            fetch = CooldownFetcher(base / 'cache', base / 'gate', logical, {
                'https://a.ucsd.edu/robots.txt': (302, {'location': 'https://b.ucsd.edu/robots.txt', 'retry-after': '90'}, '', ''),
                'https://b.ucsd.edu/robots.txt': (200, {}, 'User-agent: *\nAllow: /', ''),
                'https://a.ucsd.edu/page': (200, {'content-type': 'text/html'}, 'Lab', '')})
            meta, _ = fetch.fetch('https://a.ucsd.edu/page')
            self.assertEqual(meta['status'], 'ok')
            self.assertGreaterEqual(dict(fetch.requests)['https://b.ucsd.edu/robots.txt'], 1090)

    def test_active_cached_cooldowns_and_seed_preserve_deadlines_and_observations(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary); cache = base / 'cache'; cache.mkdir()
            source = cache / 'response.json'
            source.write_text(json.dumps({'sourceUrl': 'https://lab.ucsd.edu/one', 'observedAt': '2020-01-01', 'httpStatus': 429, 'retryAfterEpoch': 1200}))
            before = source.read_bytes(); logical = [1000.0]
            gate = HostRequestGate(base / 'gate', clock=lambda: logical[0], monotonic=lambda: logical[0], sleep=lambda s: logical.__setitem__(0, logical[0] + s))
            receipt = migrate_legacy_clocks(cache, [], gate, 'Test', [{'url': 'https://orphan.ucsd.edu/one', 'retryAt': 1300, 'fetch': {'status': 'fetch_error'}}])
            gate.seed('lab.ucsd.edu', 1005, 1)
            with gate.request_slot('https://lab.ucsd.edu/two') as slot:
                self.assertGreaterEqual(slot['lastRequestAt'], 1200)
            with gate.request_slot('https://orphan.ucsd.edu/two') as slot:
                self.assertGreaterEqual(slot['lastRequestAt'], 1300)
            self.assertEqual(receipt['legacyCooldownsImported'], 2)
            self.assertEqual(source.read_bytes(), before)

    def test_cached_redirect_cooldown_restores_both_hosts_without_changing_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary); cache = base / 'cache'; cache.mkdir()
            source = cache / 'redirect.json'
            source.write_text(json.dumps({'sourceUrl': 'https://a.ucsd.edu/one', 'observedAt': '2020-01-01', 'redirects': [{'from': 'https://a.ucsd.edu/one', 'to': 'https://b.ucsd.edu/two', 'retryAfterEpoch': 1400}]}))
            before = source.read_bytes(); logical = [1000.0]
            gate = HostRequestGate(base / 'gate', clock=lambda: logical[0], monotonic=lambda: logical[0], sleep=lambda s: logical.__setitem__(0, logical[0] + s))
            migrate_legacy_clocks(cache, [], gate, 'Test')
            for host in ['a.ucsd.edu', 'b.ucsd.edu']:
                gate.seed(host, 1005)
                _, _, path = gate.paths(host)
                self.assertEqual(json.loads(path.read_text())['notBeforeEpoch'], 1400)
            with gate.request_slot('https://b.ucsd.edu/robots.txt') as slot:
                self.assertGreaterEqual(slot['lastRequestAt'], 1400)
            self.assertEqual(source.read_bytes(), before)

    def test_response_policy_cannot_be_written_after_unlock(self):
        with tempfile.TemporaryDirectory() as directory:
            gate = HostRequestGate(directory)
            with gate.request_slot('https://lab.ucsd.edu/one') as slot:
                slot.record_response(200, {})
            with self.assertRaisesRegex(RuntimeError, 'before releasing'):
                slot.record_response(429, {'retry-after': '120'})


if __name__ == '__main__':
    unittest.main()
