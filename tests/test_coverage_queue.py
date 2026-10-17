"""Policy regressions for public collection; no live network in tests."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collect_ucsd_coverage import PublicFetcher, Queue, atomic_json, safe_url, url_key, discovery_links, profiles_appointment, discover_lab_identity_pages, replay_identity_discovery, retryable_fetch, replay_profile_qualifications
from refresh_labs import DOM, parse_directory
from refresh_faculty_directories import match_existing
from review_ucsd_coverage import credential_free_name, department_owner, faculty_review, homepage_identity_key, canonical_department
from rebuild_verified_atlas import merge_patch, attach_evidence
from apply_ucsd_coverage import reviewed_pi, export
from network_coordination import HostRequestGate


class SimulatedFetcher(PublicFetcher):
    def __init__(self, cache, pages):
        self.t = 1000
        self.pages, self.requests = pages, []
        super().__init__(cache, clock=lambda: self.t, sleep=self.advance)
        self.network_gate = HostRequestGate(Path(cache) / 'test-coordination', clock=lambda: self.t, monotonic=lambda: self.t, sleep=self.advance)

    def advance(self, seconds):
        self.t += seconds

    def _transport(self, url, max_bytes):
        self.requests.append((url, self.t))
        return self.pages[url]


class PublicPolicyTests(unittest.TestCase):
    def test_legal_reserved_path_characters_stay_literal_and_do_not_alias_percent_encoded_variants(self):
        literal = "https://example.ucsd.edu/Optics%20Group%20(Professor%20Fainman);v=2&unit=lab+group,$'!@:"
        self.assertEqual(safe_url(literal), literal)
        encoded = literal.replace('(', '%28').replace(')', '%29')
        self.assertEqual(safe_url(encoded), encoded)
        self.assertNotEqual(url_key(literal), url_key(encoded))
        self.assertEqual(safe_url('https://example.ucsd.edu/José'), 'https://example.ucsd.edu/Jos%C3%A9')

    def test_invalid_literal_uri_is_accounted_without_repair_request_or_source_date_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            queue = Queue(Path(tmp) / 'queue.json'); source = 'https://example.ucsd.edu/jane'
            queue.add(source, 'Physics', 'profile')
            queue.state['items'][source]['fetch'] = {'status': 'ok', 'observedAt': '2020-01-01', 'sha256': 'original-body'}
            invalid = 'https://briankeating.com /'
            queue.add(invalid, 'Physics', 'lab_link_candidate', source, professor_id='jane')
            queue.add(invalid, 'Physics', 'lab_link_candidate', source, professor_id='jane')
            self.assertEqual(safe_url(invalid), '')
            self.assertEqual(len(queue.state['invalidSourceUris']), 1)
            observation = queue.state['invalidSourceUris'][0]
            self.assertEqual(observation['literalUri'], invalid)
            self.assertEqual(observation['contextSourceCapture']['observedAt'], '2020-01-01')
            self.assertEqual(observation['contextSourceCapture']['bodySha256'], 'original-body')
            self.assertEqual(observation['literalUriEvidenceStatus'], 'queue_input_as_listed_not_body_verified')
            self.assertNotIn('sourceObservedAt', observation, 'A context response date must not be mislabeled as the literal URI observation date')
            self.assertEqual(list(queue.state['items']), [source])
            from collection_scope import ScopePolicy
            policy = ScopePolicy(queue.state, {'professors': [], 'labs': []})
            self.assertIn('Malformed literal', policy.request_reason({'url': invalid, 'contexts': []}))

    def test_explicit_identity_review_reopens_retained_source_without_retiming_old_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            queue = Queue(Path(tmp) / 'queue.json'); uri = 'https://profiles.ucsd.edu/jane.example'
            queue.add(uri, 'Medicine', 'profile_discovery')
            prior = {'professorId': 'jane', 'verification': {'status': 'verified', 'observedAt': '2020-01-01'}}
            queue.state['items'][uri].update(state='retained_prior_evidence', retainedEvidence=prior)
            queue.add(uri, 'Medicine', 'profile_identity_review', professor_id='jane', depth=2)
            item = queue.state['items'][uri]
            self.assertEqual(item['state'], 'pending')
            self.assertEqual(item['retainedEvidenceHistory'], [prior])
            self.assertEqual(prior['verification']['observedAt'], '2020-01-01')
            queue.add(uri, 'Medicine', 'profile_identity_review', professor_id='jane', depth=2)
            self.assertEqual(item['retainedEvidenceHistory'], [prior])

    def test_identity_review_and_future_context_types_execute_a_real_finite_batch(self):
        import argparse, hashlib
        import collect_ucsd_coverage as collector
        for kind in ['profile_identity_review', 'future_review_type']:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); (root / 'data/ucsd').mkdir(parents=True); (root / 'docs/operations').mkdir(parents=True)
                (root / 'data/research-atlas.json').write_text(json.dumps({'professors': [], 'labs': []}))
                (root / 'data/ucsd/departments.json').write_text(json.dumps({'departments': []}))
                cache = root / 'cache'; (cache / 'responses').mkdir(parents=True)
                queue = Queue(cache / 'queue.json'); uri = 'https://example.ucsd.edu/jane'
                queue.add(uri, 'Medicine', kind, depth=2); queue.save()
                raw = '<title>Jane Example</title><main><h1>Jane Example</h1>Reviewed source</main>'
                meta = {'sourceUrl': uri, 'finalUrl': uri, 'status': 'ok', 'observedAt': '2020-01-01T00:00:00+00:00', 'sha256': hashlib.sha256(raw.encode()).hexdigest()}
                class CachedOnly:
                    def __init__(self):
                        self.wire_requests = 0
                        self.network_gate = HostRequestGate(cache / 'test-coordination')
                    def fetch(self, url):
                        self.asserted = url
                        return meta, raw
                    def scheduling_wait(self, url):
                        return 0
                fetcher = CachedOnly()
                args = argparse.Namespace(cache=cache, timeout=18, workers=1, max_pages=1, reparse_cached=False, reparse_profile_appointments=False)
                with patch.object(collector, 'ROOT', root), patch.object(collector, 'PublicFetcher', return_value=fetcher), patch.object(collector.Queue, 'seed', return_value=None), patch.object(collector.Queue, 'retain_recent_profiles', return_value=None), patch.object(collector.signal, 'signal'), patch('builtins.print'):
                    collector.collect(args)
                result = json.loads((cache / 'queue.json').read_text())
                self.assertEqual(result['items'][uri]['state'], 'done')
                self.assertEqual(result['items'][uri]['fetch'], meta)
                self.assertEqual(fetcher.asserted, uri)

    def test_finite_batch_reopens_last_new_association_and_replays_cached_navigation(self):
        import argparse
        import hashlib
        import collect_ucsd_coverage as collector
        profile, root_url = 'https://profiles.ucsd.edu/jane.example', 'https://example-lab.org/'
        for previous in ['pending', 'done']:
            with self.subTest(previous=previous), tempfile.TemporaryDirectory() as tmp:
                task_root = Path(tmp)
                (task_root / 'data/ucsd').mkdir(parents=True)
                (task_root / 'docs/operations').mkdir(parents=True)
                (task_root / 'data/research-atlas.json').write_text(json.dumps({'professors': [], 'labs': []}))
                (task_root / 'data/ucsd/departments.json').write_text(json.dumps({'departments': [{'name': 'Pediatrics', 'homepage': 'https://pediatrics.ucsd.edu/'}]}))
                cache = task_root / 'cache'
                (cache / 'responses').mkdir(parents=True)
                queue = Queue(cache / 'queue.json')
                queue.add(profile, 'Pediatrics', 'profile_discovery')
                queue.add(root_url, 'Pediatrics', 'lab_link_candidate', profile, depth=1)
                root = queue.state['items'][root_url]
                root.update(state='scope_excluded', scopeAssessment={'status': 'excluded', 'reason': 'No previous person association', 'previousQueueState': previous})
                raw = '<h1>Jane Example Lab</h1><nav><a href="/people">Our Team</a></nav><p>UC San Diego research</p>'
                root_path = cache / 'responses' / (hashlib.sha256(root_url.encode()).hexdigest() + '.html')
                if previous == 'done':
                    root.update(fetch={'sourceUrl': root_url, 'finalUrl': root_url, 'status': 'ok', 'observedAt': '2020-01-01T00:00:00+00:00'},
                                page={'title': 'Jane Example Lab', 'headings': ['Jane Example Lab'], 'mainTextExcerpt': 'Jane Example Lab UC San Diego'})
                    root_path.write_text(raw)
                queue.save()
                body = '<div class="pageTitle"><h2>Jane Example</h2></div><table><tr><th>Title(s)</th><td>Professor, Pediatrics</td></tr><tr><th>School</th><td>Vc-health Sciences-schools</td></tr></table><a href="https://example-lab.org/">Lab Website</a>'
                fetcher = SimulatedFetcher(cache / 'responses', {'https://profiles.ucsd.edu/robots.txt': (404, {}, '', ''), profile: (200, {'content-type': 'text/html'}, body, '')})
                args = argparse.Namespace(cache=cache, timeout=18, workers=1, max_pages=1, reparse_cached=False, reparse_profile_appointments=False)
                with patch.object(collector, 'ROOT', task_root), patch.object(collector, 'PublicFetcher', return_value=fetcher), patch.object(collector.Queue, 'seed', return_value=None), patch.object(collector.Queue, 'retain_recent_profiles', return_value=None), patch.object(collector.signal, 'signal'), patch('builtins.print'):
                    collector.collect(args)
                saved = json.loads((cache / 'queue.json').read_text())
                self.assertEqual(saved['items'][root_url]['state'], previous)
                self.assertGreater(saved['counts'].get('pending', 0), 0)
                self.assertNotIn(root_url, [url for url, _ in fetcher.requests])
                if previous == 'done':
                    self.assertIn('https://example-lab.org/people', saved['items'])
                    self.assertEqual(saved['items'][root_url]['fetch']['observedAt'], '2020-01-01T00:00:00+00:00')
                    self.assertEqual(root_path.read_text(), raw)
                self.assertEqual(saved['scopeReassessmentHistory'][-1]['wireRequests'], 0)

    def test_transient_robots_waits_for_server_deadline_then_rechecks_permission(self):
        with tempfile.TemporaryDirectory() as cache:
            fetch = SimulatedFetcher(cache, {'https://a.ucsd.edu/robots.txt': (503, {'retry-after': '120'}, '', '')})
            first, _ = fetch.fetch('https://a.ucsd.edu/one')
            self.assertTrue(retryable_fetch(first))
            self.assertEqual(first['retryAfterEpoch'], 1120)
            fetch.advance(119)
            self.assertEqual(fetch.fetch('https://a.ucsd.edu/two')[0]['robots']['observedAt'], first['robots']['observedAt'])
            self.assertEqual(len(fetch.requests), 1)
            fetch.advance(1)
            fetch.pages['https://a.ucsd.edu/robots.txt'] = (200, {}, 'User-agent: *\nDisallow: /', '')
            last, _ = fetch.fetch('https://a.ucsd.edu/one')
            self.assertEqual(last['status'], 'robots_denied')
            self.assertEqual(fetch.requests, [('https://a.ucsd.edu/robots.txt', 1000), ('https://a.ucsd.edu/robots.txt', 1120)])
            self.assertEqual(last['robots']['attemptHistory'][0], first['robots'])

    def test_robots_retries_are_bounded_per_origin_across_pages_and_restarts(self):
        with tempfile.TemporaryDirectory() as cache:
            pages = {'https://a.ucsd.edu/robots.txt': (522, {}, '', '')}
            fetch = SimulatedFetcher(cache, pages)
            first, _ = fetch.fetch('https://a.ucsd.edu/one')
            # A new fetcher must reuse the same failure until its deadline.
            restarted = SimulatedFetcher(cache, pages)
            self.assertEqual(restarted.fetch('https://a.ucsd.edu/two')[0]['robots'], first['robots'])
            self.assertFalse(restarted.requests)
            restarted.advance(60)
            second, _ = restarted.fetch('https://a.ucsd.edu/two')
            self.assertEqual(second['robots']['attempts'], 2)
            restarted.advance(120)
            third, _ = restarted.fetch('https://a.ucsd.edu/three')
            self.assertEqual(third['robots']['attempts'], 3)
            self.assertFalse(retryable_fetch(third))
            restarted.advance(1000)
            self.assertEqual(restarted.fetch('https://a.ucsd.edu/four')[0]['robots'], third['robots'])
            self.assertEqual(len(restarted.requests), 2)
            self.assertEqual(len(third['robots']['attemptHistory']), 2)

    def test_old_transient_robots_queue_reopens_without_changing_observation(self):
        import copy
        with tempfile.TemporaryDirectory() as cache:
            path = Path(cache) / 'queue.json'
            queue = Queue(path)
            for host, code, error in [('temporary', 500, ''), ('certificate', 0, 'curl: (60) SSL certificate problem'), ('forbidden', 403, ''), ('challenge', 503, 'access_challenge')]:
                queue.add(f'https://{host}.ucsd.edu/', 'Example', 'lab_destination')
                item = queue.state['items'][f'https://{host}.ucsd.edu/']
                item.update(state='unresolved', attempts=1, fetch={'status': 'robots_unavailable', 'observedAt': '2020-01-01', 'robots': {'httpStatus': code, 'error': error, 'retrievedEpoch': 1000, 'observedAt': '2019-12-31'}})
            old = copy.deepcopy(queue.state['items'])
            queue.save()
            resumed = Queue(path).state['items']
            self.assertEqual(resumed['https://temporary.ucsd.edu/']['state'], 'pending')
            for url, item in resumed.items():
                self.assertEqual(item['fetch'], old[url]['fetch'])
                if 'temporary' not in url:
                    self.assertEqual(item['state'], 'unresolved')

    def test_partial_robots_timeout_retries_but_html_and_challenge_do_not(self):
        cases = [(200, '', 'curl: (28) Operation timed out', True), (200, '<html>ordinary error</html>', '', False), (503, '<html>Verify you are human</html>', '', False)]
        for code, body, error, expected in cases:
            with self.subTest(code=code, body=body), tempfile.TemporaryDirectory() as cache:
                fetch = SimulatedFetcher(cache, {'https://a.ucsd.edu/robots.txt': (code, {}, body, error)})
                meta, _ = fetch.fetch('https://a.ucsd.edu/lab')
                self.assertEqual(meta['status'], 'robots_unavailable')
                self.assertEqual(retryable_fetch(meta), expected)
                self.assertEqual(len(fetch.requests), 1)

    def test_long_run_refreshes_expired_in_memory_robots_before_new_page(self):
        with tempfile.TemporaryDirectory() as cache:
            fetch = SimulatedFetcher(cache, {
                'https://a.ucsd.edu/robots.txt': (200, {}, 'User-agent: *\nAllow: /', ''),
                'https://a.ucsd.edu/a': (200, {'content-type': 'text/html'}, '<h1>Allowed</h1>', ''),
            })
            self.assertEqual(fetch.fetch('https://a.ucsd.edu/a')[0]['status'], 'ok')
            fetch.advance(86401)
            fetch.pages['https://a.ucsd.edu/robots.txt'] = (200, {}, 'User-agent: *\nDisallow: /b', '')
            self.assertEqual(fetch.fetch('https://a.ucsd.edu/b')[0]['status'], 'robots_denied')
            self.assertEqual([u for u, _ in fetch.requests].count('https://a.ucsd.edu/robots.txt'), 2)
            self.assertNotIn('https://a.ucsd.edu/b', [u for u, _ in fetch.requests])

    def test_login_redirect_is_a_blocker_without_fetching_the_login_flow(self):
        with tempfile.TemporaryDirectory() as cache:
            fetch = SimulatedFetcher(cache, {
                'https://a.ucsd.edu/robots.txt': (404, {}, '', ''),
                'https://a.ucsd.edu/lab': (302, {'location': 'https://accounts.google.com/v3/signin/identifier'}, '', ''),
            })
            meta, body = fetch.fetch('https://a.ucsd.edu/lab')
            self.assertEqual(meta['status'], 'authentication_required')
            self.assertEqual(len(fetch.requests), 2)
            self.assertFalse(body)

    def test_redirect_cannot_skip_target_robots(self):
        with tempfile.TemporaryDirectory() as cache:
            fetch = SimulatedFetcher(cache, {
                'https://a.ucsd.edu/robots.txt': (404, {}, '', ''),
                'https://a.ucsd.edu/lab': (302, {'location': 'https://b.ucsd.edu/private/lab'}, '', ''),
                'https://b.ucsd.edu/robots.txt': (200, {}, 'User-agent: *\nDisallow: /private/', ''),
            })
            meta, body = fetch.fetch('https://a.ucsd.edu/lab')
            self.assertEqual(meta['status'], 'robots_denied')
            self.assertEqual(meta['blockedUrl'], 'https://b.ucsd.edu/private/lab')
            self.assertFalse(body)
            self.assertNotIn('https://b.ucsd.edu/private/lab', [u for u, _ in fetch.requests])

    def test_profiles_robots_and_redirects_share_ten_second_clock(self):
        with tempfile.TemporaryDirectory() as cache:
            fetch = SimulatedFetcher(cache, {
                'https://profiles.ucsd.edu/robots.txt': (200, {}, 'User-Agent: *\nCrawl-Delay: 10', ''),
                'https://profiles.ucsd.edu/old': (301, {'location': '/new'}, '', ''),
                'https://profiles.ucsd.edu/new': (200, {'content-type': 'text/html'}, '<h1>A Person</h1>', ''),
            })
            meta, body = fetch.fetch('https://profiles.ucsd.edu/old')
            self.assertEqual(meta['status'], 'ok')
            self.assertEqual([t for _, t in fetch.requests], [1000, 1010, 1020])
            self.assertEqual(meta['finalUrl'], 'https://profiles.ucsd.edu/new')
            # Cache replay preserves the actual observation and consumes no wire I/O.
            replay, _ = fetch.fetch('https://profiles.ucsd.edu/old')
            self.assertEqual(replay['observedAt'], meta['observedAt'])
            self.assertEqual(len(fetch.requests), 3)

    def test_robots_failure_does_not_turn_into_permission(self):
        with tempfile.TemporaryDirectory() as cache:
            fetch = SimulatedFetcher(cache, {'https://a.ucsd.edu/robots.txt': (503, {}, '', '')})
            meta, _ = fetch.fetch('https://a.ucsd.edu/lab')
            self.assertEqual(meta['status'], 'robots_unavailable')
            self.assertEqual(len(fetch.requests), 1)

    def test_interrupted_queue_recovers_stable_url_and_contexts(self):
        with tempfile.TemporaryDirectory() as cache:
            path = Path(cache) / 'queue.json'
            queue = Queue(path)
            queue.add('https://a.ucsd.edu/lab/', 'Biology', 'lab_destination')
            queue.add('https://a.ucsd.edu/lab', 'Chemistry', 'directory')
            self.assertEqual(len(queue.state['items']), 2)
            item = next(iter(queue.state['items'].values()))
            item['state'] = 'running'
            queue.save()
            recovered = next(iter(Queue(path).state['items'].values()))
            self.assertEqual(recovered['state'], 'pending')
            self.assertEqual(len(recovered['contexts']), 1)
            self.assertEqual(recovered['url'], 'https://a.ucsd.edu/lab/')
            other = Queue(path).state['items']['https://a.ucsd.edu/lab']
            self.assertEqual(other['contexts'][0]['department'], 'Chemistry')
            self.assertEqual(other['attempts'], 0)

    def test_public_url_boundary_and_atomic_checkpoint(self):
        for value in ['file:///etc/passwd', 'http://localhost/', 'http://127.0.0.1/', 'https://person:secret@ucsd.edu/', 'https://ucsd.edu:8080/']:
            self.assertEqual(safe_url(value), '')
        with tempfile.TemporaryDirectory() as cache:
            path = Path(cache) / 'checkpoint.json'
            atomic_json(path, {'state': 'pending'})
            atomic_json(path, {'state': 'done'})
            self.assertEqual(json.loads(path.read_text()), {'state': 'done'})
            self.assertEqual(list(Path(cache).iterdir()), [path])


class EvidenceBoundaryTests(unittest.TestCase):
    def faculty_row(self, name, source, role='Professor', profile=''):
        return {'name': name, 'department': 'Pediatrics', 'departmentExplicitlyListed': True,
                'listedRole': role, 'appointmentStatus': 'listed_faculty', 'directorySection': 'Faculty',
                'sourceUrl': source, 'observedAt': '2026-01-01T00:00:00+00:00',
                'evidence': {'sourceUrl': source, 'observedAt': '2026-01-01T00:00:00+00:00', 'evidence': name + ' | ' + role},
                'profileUrl': profile, 'namedLinkUrl': profile, 'email': '', 'personalWebsiteUrl': '', 'googleScholarUrl': '', 'researchAreas': []}

    def test_degree_and_pi_label_variant_reuses_new_person_without_losing_profile_link(self):
        team = self.faculty_row('PhD - PI Francesca Briganti', 'https://pediatrics.ucsd.edu/research/team.html', 'Assistant Professor')
        roster = self.faculty_row('Francesca Briganti', 'https://pediatrics.ucsd.edu/faculty/index.html', 'Assistant Professor', 'https://profiles.ucsd.edu/francesca.briganti')
        with tempfile.TemporaryDirectory() as cache:
            result = faculty_review({'facultyListings': [team, roster], 'items': {}}, {'professors': []}, Path(cache), profile_identity_review={'entries': []})
        self.assertEqual(len(result['professors']), 1)
        self.assertEqual(result['professors'][0]['name'], 'Francesca Briganti')
        self.assertEqual(result['professors'][0]['officialProfileUrl'], roster['profileUrl'])
        self.assertEqual(len(result['professors'][0]['directoryListings']), 2)

    def test_source_scoped_visiting_team_hold_does_not_suppress_independent_roster(self):
        import hashlib
        import review_ucsd_coverage as reviewer
        team = self.faculty_row('Youn Lee', 'https://pediatrics.ucsd.edu/research/team.html', 'Visiting Professor')
        roster = self.faculty_row('Youn Lee', 'https://pediatrics.ucsd.edu/faculty/index.html', 'Professor', 'https://profiles.ucsd.edu/youn.lee')
        body = '<main>Youn Lee Visiting Professor, Korea</main>'
        hold = {'sourceScoped': True, 'listedName': 'Youn Lee', 'sourceUrl': team['sourceUrl'],
                'observedAt': team['observedAt'], 'bodySha256': hashlib.sha256(body.encode()).hexdigest(),
                'sourceExcerpt': 'Youn Lee Visiting Professor, Korea', 'reason': 'Visiting lab-team relationship; campus appointment unconfirmed'}
        original_read = reviewer.read
        def read_review(path, default=None):
            return {'aliases': [], 'holdbacks': [hold]} if path.name == 'faculty-identity-review-20261016.json' else original_read(path, default)
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / 'responses').mkdir()
            (cache / 'responses' / (hashlib.sha256(team['sourceUrl'].encode()).hexdigest() + '.html')).write_text(body)
            item = {'url': team['sourceUrl'], 'fetch': {'status': 'ok', 'observedAt': team['observedAt']}}
            with patch.object(reviewer, 'read', side_effect=read_review):
                result = faculty_review({'facultyListings': [team, roster], 'items': {team['sourceUrl']: item}}, {'professors': []}, cache, profile_identity_review={'entries': []})
        self.assertEqual(len(result['professors']), 1)
        self.assertEqual(result['professors'][0]['officialProfileUrl'], roster['profileUrl'])
        self.assertEqual(len(result['professors'][0]['directoryListings']), 1)
        self.assertEqual(result['uncertainListings'][0]['reason'], hold['reason'])

    def test_name_order_review_requires_actual_named_link_and_keeps_stable_identity(self):
        import hashlib
        import review_ucsd_coverage as reviewer
        source, profile = 'https://pediatrics.ucsd.edu/faculty/index.html', 'https://profiles.ucsd.edu/yue.huang'
        row = self.faculty_row('Huang Yue', source, 'Assistant Clinical Professor', profile)
        heading = '<div class="pageTitle"><h2>Yue Huang</h2></div><table><tr><th>Title(s)</th><td>Assistant Clinical Professor, Pediatrics</td></tr><tr><th>School</th><td>Vc-health Sciences-schools</td></tr></table>'
        original_read = reviewer.read
        existing = {'id': 'old-stable', 'name': 'Huang Yue', 'department': 'Pediatrics', 'officialProfileUrl': profile, 'email': ''}
        for linked_url in [profile, 'https://profiles.ucsd.edu/someone.else']:
            with self.subTest(link=linked_url), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp)
                (cache / 'responses').mkdir()
                roster = f'<main><a href="{linked_url}">Huang Yue</a> Assistant Clinical Professor</main>'
                items, captures = {}, []
                for url, body, quote in [(source, roster, 'Huang Yue Assistant Clinical Professor'), (profile, heading, 'Yue Huang')]:
                    (cache / 'responses' / (hashlib.sha256(url.encode()).hexdigest() + '.html')).write_text(body)
                    meta = {'sourceUrl': url, 'finalUrl': url, 'status': 'ok', 'observedAt': row['observedAt']}
                    items[url] = {'url': url, 'fetch': meta}
                    captures.append({'requestedUrl': url, 'sourceUrl': url, 'observedAt': row['observedAt'], 'bodySha256': hashlib.sha256(body.encode()).hexdigest(), 'evidence': quote})
                correction = {'listedName': 'Huang Yue', 'canonicalName': 'Yue Huang', 'sourceUrl': source, 'profileUrl': profile, 'captures': captures}
                def read_review(path, default=None):
                    return {'aliases': [], 'holdbacks': [], 'nameCorrections': [correction]} if path.name == 'faculty-identity-review-20261016.json' else original_read(path, default)
                with patch.object(reviewer, 'read', side_effect=read_review):
                    result = faculty_review({'facultyListings': [row], 'items': items}, {'professors': [existing]}, cache, profile_identity_review={'entries': []})
                self.assertFalse(result['professors'])
                if linked_url == profile:
                    self.assertEqual(result['byProfessorId']['old-stable']['name'], 'Yue Huang')
                    self.assertEqual(result['byProfessorId']['old-stable']['directoryListings'][0]['nameAsListed'], 'Huang Yue')
                    self.assertIn('Huang Yue', result['byProfessorId']['old-stable']['nameAliases'])
                else:
                    self.assertEqual(result['uncertainListings'][0]['reason'], 'reviewed_name_correction_capture_changed_requires_review')

    def test_explicit_department_spelling_maps_only_exact_canonical_words(self):
        self.assertEqual(canonical_department('Mechanical and Aerospace Engineering'), 'Mechanical & Aerospace Engineering')
        self.assertEqual(canonical_department('Unlisted Center of Mechanics'), 'Unlisted Center of Mechanics')

    def test_profile_contact_must_come_from_own_email_table_not_collaborator_biography(self):
        import hashlib
        profile = 'https://profiles.ucsd.edu/jane.example'
        row = self.faculty_row('Jane Example', 'https://pediatrics.ucsd.edu/faculty/index.html', 'Professor', profile)
        for contact, expected in [('', 'Not found'), ('<tr><th>Email</th><td>jane@ucsd.edu</td></tr>', 'jane@ucsd.edu')]:
            with self.subTest(contact=contact), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp)
                (cache / 'responses').mkdir()
                body = '<div class="pageTitle"><h2>Jane Example</h2></div><table>' + contact + '</table><p>Collaborator: alice@ucsd.edu</p>'
                (cache / 'responses' / (hashlib.sha256(profile.encode()).hexdigest() + '.html')).write_text(body)
                meta = {'status': 'ok', 'sourceUrl': profile, 'finalUrl': profile, 'observedAt': row['observedAt']}
                result = faculty_review({'facultyListings': [row], 'items': {profile: {'url': profile, 'fetch': meta}}}, {'professors': []}, cache, profile_identity_review={'entries': []})
                self.assertEqual(result['professors'][0]['email'], expected)

    def test_deep_directory_discovery_does_not_consume_lab_identity_depth(self):
        with tempfile.TemporaryDirectory() as cache:
            queue = Queue(Path(cache) / 'queue.json')
            queue.add('https://lab.ucsd.edu/', 'Example', 'discovered_lab', depth=3)
            item = queue.state['items']['https://lab.ucsd.edu/']
            dom = DOM('<nav><a href="/people/">Meet Our Team</a><a href="https://other.ucsd.edu/people">People</a></nav><main><h1>Example Lab</h1></main>')
            discover_lab_identity_pages(queue, item, {'finalUrl': item['url']}, dom)
            target = queue.state['items']['https://lab.ucsd.edu/people/']
            self.assertEqual(target['contexts'][0]['identityDepth'], 1)
            self.assertNotIn('https://other.ucsd.edu/people', queue.state['items'])
            discover_lab_identity_pages(queue, target, {'finalUrl': target['url']}, DOM('<a href="/contact">Contact</a>'))
            final = queue.state['items']['https://lab.ucsd.edu/contact']
            self.assertEqual(final['contexts'][0]['identityDepth'], 2)
            discover_lab_identity_pages(queue, final, {'finalUrl': final['url']}, DOM('<a href="/another">Team</a>'))
            self.assertNotIn('https://lab.ucsd.edu/another', queue.state['items'])

    def test_identity_replay_discovers_image_home_without_mutating_captures(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            queue = Queue(cache / 'queue.json')
            queue.add('https://lab.ucsd.edu/', 'Example', 'lab_destination')
            item = queue.state['items']['https://lab.ucsd.edu/']
            item.update(state='done', fetch={'status': 'ok', 'finalUrl': item['url'], 'observedAt': '2020-01-01'})
            body = '<a href="/home/"><img src="/logo.png"></a>'
            (cache / 'responses').mkdir()
            path = cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html')
            path.write_text(body)
            replay_identity_discovery(queue, cache)
            self.assertIn('https://lab.ucsd.edu/home/', queue.state['items'])
            self.assertEqual(item['fetch']['observedAt'], '2020-01-01')
            self.assertEqual(path.read_text(), body)
            self.assertEqual(queue.state['identityDiscoveryReplay']['wireRequests'], 0)
            count = len(queue.state['items'])
            replay_identity_discovery(queue, cache)
            self.assertEqual(len(queue.state['items']), count)

    def test_root_home_is_a_duplicate_review_key_without_collapsing_shared_sites(self):
        self.assertEqual(homepage_identity_key('https://dongwang.ucsd.edu/home'), homepage_identity_key('https://dongwang.ucsd.edu/'))
        self.assertEqual(homepage_identity_key('https://sites.google.com/ucsd.edu/group-a/home'), homepage_identity_key('https://sites.google.com/ucsd.edu/group-a/'))
        self.assertNotEqual(homepage_identity_key('https://sites.google.com/ucsd.edu/group-a/home'), homepage_identity_key('https://sites.google.com/ucsd.edu/group-b/home'))
        self.assertNotEqual(homepage_identity_key('https://department.ucsd.edu/labs/a'), homepage_identity_key('https://department.ucsd.edu/labs/b'))

    def test_profiles_eligibility_requires_appointment_table_not_biography(self):
        meta = {'sourceUrl': 'https://profiles.ucsd.edu/jane.example', 'finalUrl': 'https://profiles.ucsd.edu/jane.example', 'observedAt': '2026-10-16T00:00:00+00:00'}
        body = '<main><h1>Jane Example</h1><table><tr><th>Title(s)</th><td>Project Scientist, Neurosciences</td></tr><tr><th>School</th><td>Vc-health Sciences-schools</td></tr></table><p>I collaborate with Professor Alice Other.</p></main>'
        assessment, row = profiles_appointment(meta, body)
        self.assertIsNone(row)
        self.assertEqual(assessment['status'], 'no_explicit_faculty_title_captured')
        assessment, row = profiles_appointment(meta, body.replace('Project Scientist, Neurosciences', 'Assistant Professor, Psychiatry'))
        self.assertEqual(row['department'], 'Psychiatry')
        self.assertEqual(row['name'], 'Jane Example')
        self.assertTrue(row['discoveryId'].startswith('ucsd-profile-faculty-'))
        assessment, row = profiles_appointment(meta, body.replace('Project Scientist, Neurosciences', 'Assistant to Professor Alice Other'))
        self.assertIsNone(row)
        self.assertEqual(assessment['status'], 'academic_title_clause_requires_review')

    def test_production_profiles_h2_identity_uses_own_table_and_ignores_site_heading(self):
        meta = {'sourceUrl': 'https://profiles.ucsd.edu/yue.huang', 'finalUrl': 'https://profiles.ucsd.edu/yue.huang', 'observedAt': '2026-10-16T02:23:49+00:00'}
        markup = '<header><h1>UCSD Profiles</h1></header><div id="ctl00_divProfilesContentMain"><div class="pageTitle"><h2>Yue Huang</h2></div><table><tr><th>Title(s)</th><td>Assistant Clinical Professor, Pediatrics</td></tr><tr><th>School</th><td>Vc-health Sciences-schools</td></tr></table><h2>Overview</h2><p>I collaborate with Professor Someone Else.</p></div>'
        assessment, row = profiles_appointment(meta, markup)
        self.assertEqual(assessment['identityHeadingMethod'], 'profiles_page_title_h2')
        self.assertEqual(row['name'], 'Yue Huang')
        self.assertEqual(row['department'], 'Pediatrics')
        self.assertEqual(row['departmentAsListed'], 'Pediatrics')
        self.assertEqual(row['departmentMappingStatus'], 'matched_saved_department')
        _, unmapped = profiles_appointment(meta, markup.replace('Professor, Pediatrics', 'Professor, Marine Physical Laboratory'))
        self.assertEqual(unmapped['department'], 'Unknown')
        self.assertEqual(unmapped['departmentAsListed'], 'Marine Physical Laboratory')
        self.assertEqual(unmapped['departmentMappingStatus'], 'explicit_unit_unmapped')
        self.assertEqual(row['observedAt'], meta['observedAt'])
        _, row = profiles_appointment(meta, markup.replace('Assistant Clinical Professor, Pediatrics', 'Project Scientist, Pediatrics'))
        self.assertIsNone(row)
        _, row = profiles_appointment(meta, markup.replace('class="pageTitle"', 'class="biography"'))
        self.assertIsNone(row)

    def test_initial_only_profile_heading_is_recorded_without_guessing_full_identity(self):
        meta = {'sourceUrl': 'https://profiles.ucsd.edu/h.kirk.hammond', 'finalUrl': 'https://profiles.ucsd.edu/h.kirk.hammond', 'observedAt': '2026-10-16T00:00:00+00:00'}
        markup = '<div class="pageTitle"><h2>H Hammond</h2></div><table><tr><th>Title(s)</th><td>Professor In Residence, Medicine</td></tr><tr><th>School</th><td>Vc-health Sciences-schools</td></tr></table>'
        assessment, row = profiles_appointment(meta, markup)
        self.assertIsNone(row)
        self.assertEqual(assessment['nameAsDisplayed'], 'H Hammond')
        self.assertEqual(assessment['status'], 'profile_identity_heading_requires_review')
        self.assertEqual(assessment['titleAsListed'], 'Professor In Residence, Medicine')

    def test_qualification_replay_recovers_h2_without_wire_or_changed_source_dates(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            queue = Queue(cache / 'queue.json')
            (cache / 'responses').mkdir()
            files = {}
            for name, role in [('Jane Example', 'Associate Professor, Pediatrics'), ('Staff Example', 'Project Scientist, Pediatrics')]:
                url = 'https://profiles.ucsd.edu/' + name.lower().replace(' ', '.')
                queue.add(url, 'Unknown', 'profile_discovery')
                meta = {'sourceUrl': url, 'finalUrl': url, 'status': 'ok', 'observedAt': '2020-01-01T00:00:00+00:00'}
                old = {'status': 'missing_identity_or_appointment_table', 'observedAt': meta['observedAt']}
                item = queue.state['items'][url]
                item.update(state='done', fetch=meta, profileEligibility=old)
                raw = f'<div class="pageTitle"><h2>{name}</h2></div><table><tr><th>Title(s)</th><td>{role}</td></tr><tr><th>School</th><td>Vc-health Sciences-schools</td></tr></table>'
                stem = hashlib.sha256(url.encode()).hexdigest()
                for suffix, data in [('html', raw), ('json', json.dumps(meta))]:
                    path = cache / 'responses' / (stem + '.' + suffix)
                    path.write_text(data)
                    files[path] = path.read_bytes()
            replay_profile_qualifications(queue, cache)
            self.assertEqual(queue.state['profileQualificationReplay']['wireRequests'], 0)
            self.assertEqual(queue.state['profileQualificationReplay']['newFacultyRows'], 1)
            self.assertEqual(queue.state['facultyListings'][0]['name'], 'Jane Example')
            self.assertEqual(queue.state['facultyListings'][0]['observedAt'], '2020-01-01T00:00:00+00:00')
            self.assertEqual(queue.state['items']['https://profiles.ucsd.edu/jane.example']['profileEligibilityHistory'][0]['status'], 'missing_identity_or_appointment_table')
            replay_profile_qualifications(queue, cache)
            self.assertEqual(len(queue.state['facultyListings']), 1)
            self.assertTrue(all(path.read_bytes() == raw for path, raw in files.items()))

    def test_named_collaborator_cannot_inherit_another_persons_pi_title(self):
        with self.assertRaises(ValueError):
            reviewed_pi({'principalInvestigator': 'Jane Example', 'piEvidence': [{'evidence': 'PI Alice Other; collaborator Jane Example'}]})
        self.assertEqual(reviewed_pi({'principalInvestigator': 'John Hwang', 'piEvidence': [{'evidence': 'LSDO Lab is a research group led by Prof. John Hwang'}]})['fields']['principalInvestigator'], 'John Hwang')

    def test_unfinished_queue_cannot_be_exported_to_the_builder(self):
        with tempfile.TemporaryDirectory() as cache:
            atomic_json(Path(cache) / 'queue.json', {'items': {'a': {'state': 'pending'}}})
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                export(Path(cache), Path(cache) / 'decisions.json')

    def test_navigation_discovers_targets_without_supporting_lab_facts(self):
        markup = '<nav><a class="menu-link" href="/faculty">Faculty</a><a class="menu-link" href="https://ghost.ucsd.edu/">Ghost Lab</a></nav><main><h1>Research</h1></main>'
        found = [label for _, label, _ in discovery_links(DOM(markup).root, 'https://a.ucsd.edu/')]
        self.assertIn('Faculty', found)
        self.assertIn('Ghost Lab', found)
        self.assertEqual(parse_directory('Example', {'sourceUrl': 'https://a.ucsd.edu/', 'observedAt': '2026-10-16T00:00:00+00:00', 'status': 'ok'}, markup, []), [])

    def test_given_name_spacing_reuses_id_but_nicknames_and_conflicts_do_not(self):
        row = {'name': 'DeeDee Halleck', 'department': 'Communication', 'profileUrl': '', 'email': ''}
        people = [{'id': 'old', 'name': 'Dee Dee Halleck', 'department': 'Communication', 'officialProfileUrl': '', 'email': ''}]
        self.assertEqual(match_existing(row, people)[0]['id'], 'old')
        people = [{'id': 'old', 'name': 'Alice B. Example', 'department': 'Example', 'officialProfileUrl': '', 'email': ''}]
        self.assertIsNone(match_existing({**row, 'name': 'Alice A. Example', 'department': 'Example'}, people)[0])
        people[0]['name'] = 'Samuel Museus'
        self.assertIsNone(match_existing({**row, 'name': 'Sam Museus', 'department': 'Example'}, people)[0])

    def test_repeat_observation_cannot_erase_the_original_timestamp(self):
        proof = {'sourceUrl': 'https://a.ucsd.edu/', 'observedAt': '2026-10-01T00:00:00+00:00', 'evidence': 'A Person', 'method': 'official_heading'}
        later = {**proof, 'observedAt': '2026-10-16T00:00:00+00:00'}
        record = {}
        for item in [proof, later, proof, later]:
            attach_evidence(record, 'name', item)
        self.assertEqual(record['fieldEvidence']['name'], [proof, later])

    def test_incremental_build_keeps_multiple_relationships_and_dates(self):
        first = {'sourceUrl': 'https://a.ucsd.edu/', 'observedAt': '2026-10-01T00:00:00+00:00', 'evidence': 'A Lab'}
        second = {'sourceUrl': 'https://b.ucsd.edu/', 'observedAt': '2026-10-16T00:00:00+00:00', 'evidence': 'B Lab'}
        record = {'fieldEvidence': {}, 'labAffiliations': [{'labId': 'a', 'url': 'https://a.ucsd.edu/', 'fieldEvidence': first}], 'directoryListings': [{'sourceUrl': 'https://a.ucsd.edu/', 'observedAt': first['observedAt']}]}
        merge_patch(record, {'labAffiliations': [{'labId': 'b', 'url': 'https://b.ucsd.edu/', 'fieldEvidence': second}], 'directoryListings': [{'sourceUrl': 'https://b.ucsd.edu/', 'observedAt': second['observedAt']}]})
        self.assertEqual([a['labId'] for a in record['labAffiliations']], ['a', 'b'])
        self.assertEqual(record['labAffiliations'][0]['fieldEvidence'], first)
        self.assertEqual(len(record['directoryListings']), 2)

    def test_credentials_do_not_create_duplicate_person_identities(self):
        self.assertEqual(credential_free_name('M.D. Reid Oldenburg'), 'Reid Oldenburg')
        self.assertEqual(credential_free_name('Sharon, MD, MPH Brouha'), 'Sharon Brouha')
        self.assertEqual(credential_free_name('PhD, MS, MSW Hyunkyung (Yulia) Yun'), 'Hyunkyung (Yulia) Yun')
        self.assertEqual(credential_free_name('Dr. Laura Case'), 'Laura Case')
        self.assertEqual(credential_free_name('PhD - PI Francesca Briganti'), 'Francesca Briganti')
        self.assertEqual(credential_free_name('MD, PhD – PI Francesca Briganti'), 'Francesca Briganti')

    def test_cross_department_link_does_not_move_a_directory(self):
        self.assertEqual(department_owner('https://hwsph.ucsd.edu/people/faculty/faculty-directory.html', 'Pediatrics'), 'Public Health')
        self.assertEqual(department_owner('https://anthropology.ucsd.edu/people/faculty/index.html', 'Structural Engineering'), 'Anthropology')

    def test_staff_cards_do_not_become_professors(self):
        row = {'name': 'NP Example Person', 'department': 'Otolaryngology', 'listedRole': 'Faculty directory listing',
               'appointmentStatus': 'listed_faculty', 'directorySection': 'Faculty',
               'sourceUrl': 'https://oto.ucsd.edu/faculty/index.html', 'profileUrl': '',
               'observedAt': '2026-10-16T00:00:00+00:00', 'evidence': {'evidence': 'NP Example Person'},
               'email': '', 'personalWebsiteUrl': '', 'googleScholarUrl': '', 'researchAreas': []}
        with tempfile.TemporaryDirectory() as cache:
            output = faculty_review({'facultyListings': [row], 'items': {}}, {'professors': []}, Path(cache), profile_identity_review={'entries': []})
        self.assertEqual(output['professors'], [])
        self.assertEqual(output['uncertainListings'][0]['reason'], 'explicit_academic_title_not_observed')


if __name__ == '__main__':
    unittest.main()
