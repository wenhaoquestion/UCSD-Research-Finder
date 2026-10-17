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
import plan_ucsd_faculty_title_sources as planner


class FacultyTitleSourcePlanTests(unittest.TestCase):
    def fixture(self, root, label='Jane Example'):
        cache = root / '.cache/coverage-20261016'; (cache / 'responses').mkdir(parents=True)
        preview = cache / 'profile-qualification-preview'; preview.mkdir()
        source = 'https://be.ucsd.edu/faculty'
        target = 'http://jacobsschool.ucsd.edu/faculty/faculty_bios/index.sfe?fmp_recid=123'
        raw = f'<main><div class="faculty-profile"><h3>Jane Example</h3><a href="{target}">{label}</a>Affiliate</div></main>'
        path = cache / 'responses' / (hashlib.sha256(source.encode()).hexdigest() + '.html'); path.write_text(raw)
        meta = {'sourceUrl': source, 'finalUrl': source, 'status': 'ok', 'observedAt': '2020-01-01',
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        queue = collector.Queue(preview / 'queue.json'); queue.add(source, 'Bioengineering', 'faculty_directory')
        queue.state['items'][source].update(state='done', fetch=meta)
        queue.add(target, 'Bioengineering', 'new_faculty_profile', source)
        queue.state['items'][target].update(state='retained_prior_evidence', attempts=0,
                                           retainedEvidence={'originalId': 'unchanged-old-id', 'observedAt': '2018-01-01'})
        row = {'name': 'Jane Example', 'department': 'Bioengineering', 'listedRole': 'Affiliate',
               'profileUrl': target, 'sourceUrl': source, 'observedAt': meta['observedAt'],
               'evidence': {'sourceUrl': source, 'observedAt': meta['observedAt'], 'evidence': 'Jane Example | Affiliate'}}
        review = {'uncertainListings': [{'reason': 'explicit_academic_title_not_observed', 'listing': row}]}
        return cache, queue, review, path

    def test_literal_roster_request_reopens_only_in_shadow_and_does_not_qualify_or_bind_a_person(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, queue, review, path = self.fixture(Path(tmp)); before = copy.deepcopy(queue.state)
            plan, sources = planner.prepare_plan(review, queue.state, cache)
            self.assertEqual(queue.state, before)
            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0]['url'], review['uncertainListings'][0]['listing']['profileUrl'])
            self.assertEqual(sources[0]['professorId'], '')
            case = plan['cases'][0]
            self.assertFalse(case['academicQualificationEstablished']); self.assertFalse(case['personIdentityEstablished'])
            self.assertEqual(case['discoveryCapture']['rawHref'], sources[0]['url'])
            self.assertEqual(case['discoveryCapture']['bodySha256'], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(case['discoveryCapture']['observedAt'], '2020-01-01')

    def test_link_variants_wrong_people_navigation_and_unscoped_generic_labels_are_not_sources(self):
        for mode in ['scheme', 'wrong_name', 'navigation', 'outside_card', 'external', 'directory']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache, queue, review, path = self.fixture(Path(tmp)); raw = path.read_text()
                source, target = list(queue.state['items'])
                if mode == 'scheme': raw = raw.replace('href="http:', 'href="https:')
                if mode == 'wrong_name': raw = raw.replace('>Jane Example</a>', '>Another Person</a>')
                if mode == 'navigation': raw = '<main><nav>' + raw + '</nav></main>'
                if mode == 'outside_card': raw = raw.replace(' class="faculty-profile"', '').replace('>Jane Example</a>', '>Profile</a>')
                if mode == 'external': review['uncertainListings'][0]['listing']['profileUrl'] = 'https://example.edu/faculty/jane'
                if mode == 'directory': review['uncertainListings'][0]['listing']['profileUrl'] = 'https://be.ucsd.edu/faculty'
                path.write_text(raw); queue.state['items'][source]['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                plan, sources = planner.prepare_plan(review, queue.state, cache)
                self.assertEqual(sources, [])
                self.assertNotEqual(plan['cases'][0]['reviewStatus'], 'exact_linked_source_check_proposed')

    def test_generic_profile_label_requires_the_own_named_card_and_source_bytes_and_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, queue, review, path = self.fixture(Path(tmp), label='UCSD Profile')
            self.assertEqual(len(planner.prepare_plan(review, queue.state, cache)[1]), 1)
            bad_date = copy.deepcopy(review); bad_date['uncertainListings'][0]['listing']['observedAt'] = '2021-01-01'
            self.assertEqual(planner.prepare_plan(bad_date, queue.state, cache)[1], [])
            raw = path.read_text().replace('<h3>Jane Example</h3>', '<h3>Another Person</h3>'); path.write_text(raw)
            source = next(iter(queue.state['items']))
            queue.state['items'][source]['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(planner.prepare_plan(review, queue.state, cache)[1], [])
            path.write_text(path.read_text() + '<!-- changed -->')
            with self.assertRaisesRegex(ValueError, 'exact successful campus capture'):
                planner.prepare_plan(review, queue.state, cache)

    def test_failures_active_requests_positive_sources_and_missing_uris_are_accounted_without_retries(self):
        for mode in ['failure', 'pending', 'positive', 'no_uri']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache, queue, review, _ = self.fixture(Path(tmp)); target = review['uncertainListings'][0]['listing']['profileUrl']
                item = queue.state['items'][target]
                if mode == 'failure': item.update(state='unresolved', attempts=3, retryAt=9999999999, fetch={'status': 'http_error', 'httpStatus': 403, 'observedAt': '2019-01-01'})
                if mode == 'pending': item.update(state='pending', attempts=2, retryAt=9999999999)
                if mode == 'positive': item.update(state='done', fetch={'status': 'ok'})
                if mode == 'no_uri': review['uncertainListings'][0]['listing']['profileUrl'] = ''
                before = copy.deepcopy(queue.state)
                plan, sources = planner.prepare_plan(review, queue.state, cache)
                self.assertEqual(sources, []); self.assertEqual(plan['counts']['reviewCases'], 1)
                self.assertEqual(queue.state, before)

    def test_apply_preserves_existing_contexts_source_files_and_preview_queue_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); cache, queue, review, path = self.fixture(root)
            (root / 'data/ucsd').mkdir(parents=True)
            (root / 'data/research-atlas.json').write_text(json.dumps({'professors': [], 'labs': []}))
            config_path = root / 'data/ucsd/coverage-20261016-additional-sources.json'
            original = {'url': 'https://math.ucsd.edu/people/faculty', 'department': 'Mathematics', 'kind': 'directory'}
            config_path.write_text(json.dumps({'sources': [original]}))
            queue.save(); queue_bytes = queue.path.read_bytes(); source_bytes = path.read_bytes()
            (cache / 'profile-qualification-preview/faculty-review.json').write_text(json.dumps(review))
            with patch.object(planner, 'ROOT', root), patch.object(sys, 'argv', ['planner', '--apply']), contextlib.redirect_stdout(io.StringIO()):
                planner.main()
                first = config_path.read_bytes()
                planner.main()
            config = json.loads(config_path.read_bytes()); plan = json.loads((root / 'data/ucsd' / planner.PLAN_NAME).read_bytes())
            self.assertEqual(config['sources'][0], original); self.assertEqual(len(config['sources']), 2)
            self.assertEqual(config_path.read_bytes(), first)
            self.assertEqual(plan['configuredNewSourceContexts'], 0)
            self.assertEqual(plan['retainedSourceUrisReopenedInShadow'], 1)
            self.assertEqual(plan['newSourceUrisInShadow'], 0)
            self.assertTrue(plan['oldRetentionReceiptsPreserved']); self.assertFalse(plan['liveQueueWritten'])
            self.assertEqual(queue.path.read_bytes(), queue_bytes); self.assertEqual(path.read_bytes(), source_bytes)

    def test_a_positive_receipt_without_verified_raw_bytes_is_reported_as_a_capture_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, queue, review, _ = self.fixture(Path(tmp))
            target = review['uncertainListings'][0]['listing']['profileUrl']
            queue.state['items'][target].update(state='done', fetch={'status': 'ok'})
            before = copy.deepcopy(queue.state)
            plan, sources = planner.prepare_plan(review, queue.state, cache)
            self.assertEqual(sources, [])
            self.assertEqual(plan['cases'][0]['reviewStatus'], 'positive_receipt_without_verified_body_requires_capture_repair')
            self.assertEqual(queue.state, before)
