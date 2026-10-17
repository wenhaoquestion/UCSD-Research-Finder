import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collect_ucsd_coverage import Queue, safe_url, url_key, replay_literal_uri_discovery
from refresh_labs import canonical_url, parse_directory
from test_coverage_queue import SimulatedFetcher


class LiteralTransportUriTests(unittest.TestCase):
    def test_scheme_host_path_and_query_are_not_silently_rewritten(self):
        for url in ['http://sinhagroup.ucsd.edu/', 'http://www.cogsci.ucsd.edu/a?x=1',
                    'https://www.jacobsschool.ucsd.edu/profile?id=3', 'http://example.org/lab']:
            with self.subTest(url=url):
                self.assertEqual(safe_url(url), url)
                self.assertEqual(canonical_url(url), url)

    def test_http_and_https_have_independent_robots_requests_bodies_and_caches(self):
        with tempfile.TemporaryDirectory() as tmp:
            http, https = 'http://example.ucsd.edu/', 'https://example.ucsd.edu/'
            pages = {http + 'robots.txt': (404, {}, '', ''), https + 'robots.txt': (404, {}, '', ''),
                     http: (200, {'content-type': 'text/html'}, '<title>Allen Lab</title>', ''),
                     https: (200, {'content-type': 'text/html'}, '<title>Different Lab</title>', '')}
            fetcher = SimulatedFetcher(Path(tmp) / 'responses', pages)
            first, body = fetcher.fetch(http)
            second, other_body = fetcher.fetch(https)
            self.assertEqual(first['sourceUrl'], http)
            self.assertEqual(first['finalUrl'], http)
            self.assertEqual(first['redirects'], [])
            self.assertIn('Allen Lab', body)
            self.assertIn('Different Lab', other_body)
            self.assertNotEqual(first['sha256'], second['sha256'])
            self.assertEqual({u for u, _ in fetcher.requests}, set(pages))
            for url in [http, https]:
                self.assertTrue((Path(tmp) / 'responses' / (hashlib.sha256(url.encode()).hexdigest() + '.json')).exists())

    def test_explicit_http_redirect_checks_actual_https_target_robots(self):
        with tempfile.TemporaryDirectory() as tmp:
            http, https = 'http://example.ucsd.edu/', 'https://example.ucsd.edu/'
            pages = {http + 'robots.txt': (404, {}, '', ''),
                     http: (301, {'location': https}, '', ''),
                     https + 'robots.txt': (200, {}, 'User-agent: *\nDisallow: /', '')}
            fetcher = SimulatedFetcher(Path(tmp), pages)
            meta, body = fetcher.fetch(http)
            self.assertEqual(meta['status'], 'robots_denied')
            self.assertEqual(meta['redirects'][0]['from'], http)
            self.assertEqual(meta['redirects'][0]['to'], https)
            self.assertNotIn(https, [u for u, _ in fetcher.requests])

    def test_directory_lab_url_retains_the_actual_http_link(self):
        meta = {'status': 'ok', 'sourceUrl': 'https://dept.ucsd.edu/faculty', 'finalUrl': 'https://dept.ucsd.edu/faculty', 'observedAt': '2026-10-01'}
        rows = parse_directory('Example', meta, '<main><p><a href="http://example.ucsd.edu/">Example Lab</a></p></main>', [])
        self.assertTrue(rows)
        self.assertEqual(rows[0]['labWebsiteUrl'], 'http://example.ucsd.edu/')

    def test_replay_discovers_original_literal_uri_without_rewriting_old_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / 'responses').mkdir()
            source, target = 'https://dept.ucsd.edu/faculty', 'http://example.ucsd.edu/'
            raw = b'<main><a href="http://example.ucsd.edu/">Example Lab</a></main>\r\n'
            path = cache / 'responses' / (hashlib.sha256(source.encode()).hexdigest() + '.html')
            path.write_bytes(raw)
            meta = {'status': 'ok', 'sourceUrl': source, 'finalUrl': source, 'observedAt': '2026-10-01', 'sha256': hashlib.sha256(raw).hexdigest()}
            queue = Queue(cache / 'queue.json')
            queue.add(source, 'Example', 'faculty_directory')
            item = queue.state['items'][url_key(source)]
            item.update(state='done', fetch=meta)
            replay_literal_uri_discovery(queue, cache, {'professors': [], 'labs': []})
            self.assertIn(url_key(target), queue.state['items'])
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(item['fetch'], meta)
            count = len(queue.state['items'])
            replay_literal_uri_discovery(queue, cache, {'professors': [], 'labs': []})
            self.assertEqual(len(queue.state['items']), count)
            self.assertEqual(queue.state['literalUriDiscoveryReplay']['wireRequests'], 0)

    def test_replay_rejects_changed_capture_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            queue = Queue(cache / 'queue.json')
            queue.add('https://dept.ucsd.edu/', 'Example', 'directory')
            item = next(iter(queue.state['items'].values()))
            item.update(state='done', fetch={'status': 'ok', 'finalUrl': item['url'], 'sha256': 'not-a-matching-capture'})
            with self.assertRaisesRegex(ValueError, 'unchanged original capture'):
                replay_literal_uri_discovery(queue, cache, {'professors': [], 'labs': []})

    def test_profile_replay_keeps_the_own_appointment_gate_for_personal_websites(self):
        from collect_ucsd_coverage import profiles_appointment
        for title, eligible in [('Professor, Mathematics', True), ('Staff Research Associate', False)]:
            with self.subTest(title=title), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp)
                (cache / 'responses').mkdir()
                source, target = 'https://profiles.ucsd.edu/jane.example', 'http://example.ucsd.edu/'
                body = '<main><div class="pageTitle"><h2>Jane Example</h2></div><table><tr><th>Title(s)</th><td>' + title + '</td></tr><tr><th>School</th><td>VC-Academic Affairs</td></tr></table><a href="' + target + '">Website</a></main>'
                raw = body.encode()
                (cache / 'responses' / (hashlib.sha256(source.encode()).hexdigest() + '.html')).write_bytes(raw)
                meta = {'status': 'ok', 'sourceUrl': source, 'finalUrl': source, 'observedAt': '2026-10-01', 'sha256': hashlib.sha256(raw).hexdigest()}
                queue = Queue(cache / 'queue.json')
                queue.add(source, 'Unknown', 'profile_discovery')
                item = queue.state['items'][url_key(source)]
                item.update(state='done', fetch=meta, profileEligibility=profiles_appointment(meta, body)[0])
                replay_literal_uri_discovery(queue, cache, {'professors': [], 'labs': []})
                self.assertEqual(url_key(target) in queue.state['items'], eligible)
                self.assertEqual(queue.state['facultyListings'], [])

    def test_destination_review_cannot_substitute_https_for_the_requested_http_uri(self):
        import apply_ucsd_coverage as apply
        http, https = 'http://example.ucsd.edu/', 'https://example.ucsd.edu/'
        for substitute in [False, True]:
            with self.subTest(substitute=substitute), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / 'data/ucsd').mkdir(parents=True)
                cache = root / 'cache'
                (cache / 'responses').mkdir(parents=True)
                requested = https if substitute else http
                raw = b'<title>Allen Lab</title><main>Contact Monica Allen.</main>'
                (cache / 'responses' / (hashlib.sha256(requested.encode()).hexdigest() + '.html')).write_bytes(raw)
                meta = {'status': 'ok', 'sourceUrl': requested, 'finalUrl': requested, 'observedAt': '2026-10-01'}
                queue = {'items': {url_key(requested): {'url': requested, 'fetch': meta}}}
                proof = {'requestedUrl': http, 'sourceUrl': http, 'observedAt': '2026-10-01', 'bodySha256': hashlib.sha256(raw).hexdigest(), 'evidenceType': 'document_title', 'evidence': 'Allen Lab'}
                row = {'labId': 'sinha', 'action': 'record_destination_assessment', 'evidence': [proof]}
                (root / 'data/ucsd/legacy-lab-identity-review-20261016.json').write_text(json.dumps({'entries': [row]}))
                with patch.object(apply, 'ROOT', root):
                    if substitute:
                        with self.assertRaises(ValueError):
                            apply.verified_destination_reviews(queue, cache)
                    else:
                        self.assertEqual(apply.verified_destination_reviews(queue, cache), [row])

    def test_rebuild_keeps_mismatch_unresolved_despite_historical_field_evidence(self):
        from test_atlas_quality import atlas
        from rebuild_verified_atlas import build
        from refresh_labs import make_lab
        data = atlas()
        source = 'http://example.ucsd.edu/'
        meta = {'sourceUrl': source, 'finalUrl': source, 'observedAt': '2020-01-01'}
        lab = make_lab('Sinha Research Group', source, 'Physics', meta, 'Original historical lab listing')
        data['labs'] = [lab]
        row = {'labId': lab['id'], 'action': 'record_destination_assessment', 'identityStatus': 'mismatch', 'observedPageType': 'lab',
               'evidence': [{'sourceUrl': source, 'observedAt': '2026-10-01', 'evidence': 'Allen Lab'}]}
        first, *_ = build(data, {}, {}, {}, {}, coverage_evidence={'destinationIdentityReviews': [row]})
        kept = first['labs'][0]
        self.assertEqual(kept['labName'], 'Sinha Research Group')
        self.assertEqual(kept['labWebsiteUrl'], source)
        self.assertEqual(kept['verification']['status'], 'needs_review')
        self.assertEqual(kept['fieldEvidence']['labName'][0]['observedAt'], '2020-01-01')
        self.assertNotIn('closed', kept)
