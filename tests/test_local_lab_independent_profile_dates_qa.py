"""Independent offline boundary oracles for separately dated profile routes.

Temporary fixture files only; real subprocesses, PID probes and fetchers are
forbidden by the shared fixture. These tests do not establish real transport.
"""
import copy
import json
import unittest
from pathlib import Path

import test_local_lab_independent_profile_dates as dated
import local_lab_summary_gaps as gaps


class IndependentDateBoundaryQATests(unittest.TestCase):
    def setUp(self):
        self.d = dated.IndependentProfileDateTests()
        self.d.setUp()
        self.addCleanup(self.d.doCleanups)
        self.f = self.d.f

    def test_current_projected_access_refusal_beats_rehashed_clean_route_report(self):
        original = copy.deepcopy(self.f.packet)
        for field in ('relatedDestinationChecks', 'followupChecks', 'destinationAttemptHistory'):
            for status in ('authentication_required', 'access_challenge', 'robots_denied'):
                with self.subTest(field=field, status=status):
                    self.f.packet = copy.deepcopy(original)
                    self.f.packet[field] = [{'transportStatus': status, 'checkedUrl': self.f.listed}]
                    self.f.freeze_records()
                    self.d.reviews()  # Fresh hashes cannot bless an incorrect clean declaration.
                    self.assertEqual(self.d.helper(), [])

    def test_current_login_capture_history_beats_unchanged_old_review(self):
        for destination in ('https://shibboleth.ucsd.edu/idp/profile',
                            'https://example.ucsd.edu/oauth2/authorize',
                            'https://example.ucsd.edu/login.aspx'):
            with self.subTest(destination=destination):
                self.f.captures = {'later': {'url': self.f.listed, 'state': 'unresolved',
                    'fetch': {}, 'attemptHistory': [{'status': 'ok', 'httpStatus': 200,
                        'finalUrl': destination}]}}
                self.assertEqual(self.d.helper(), [])

    def test_current_orphan_wire_and_robots_only_journal_close_without_page_proof(self):
        footprints = [
            {'wireEvents': [{'url': self.f.url, 'requestOutcome': 'transport_started_response_indeterminate'}]},
            {'wireEvents': [{'url': 'http://example.ucsd.edu/robots.txt',
                             'originalObservationUrl': self.f.url, 'kind': 'robots'}]},
            {'originalUriObservationStarts': {self.f.url: {'state': 'started_not_completed',
                                                         'journalIsNotPageRequestProof': True}}},
        ]
        for footprint in footprints:
            with self.subTest(footprint=footprint):
                self.f.put('gap-results.json', dict(items={}, **footprint))
                self.assertEqual(self.d.helper(), [])
                self.assertNotIn('actualPageRequestMade', json.dumps(footprint))

    def test_current_robots_refusal_dominates_clean_reports_and_later_not_found(self):
        self.f.put_robots({'status': 'not_found', 'httpStatus': 404, 'error': 'access_challenge'})
        self.f.put_robots({'status': 'not_found', 'httpStatus': 404, 'error': ''},
                          self.f.out / 'gap-cache')
        self.assertEqual(self.d.helper(), [])

    def test_new_contract_cannot_reuse_two_megabyte_exception_or_supported_entity(self):
        self.f.entry.update(maxPageBytes=8_000_000, sizeLimitReviewPath='unused',
                            sizeLimitReviewSha256='0' * 64)
        self.assertEqual(self.d.helper(), [])
        self.f.entry['maxPageBytes'] = 2_000_000
        self.f.raw['status'] = 'supported'
        self.f.freeze_records(); self.d.reviews()
        self.assertEqual(self.d.helper(), [])

    def test_registry_isolation_and_missing_reports_never_fallback_to_old_contract(self):
        self.assertEqual(len(self.d.helper()), 1)
        self.f.put('reviewed-independent-date-profile-links.json', {'items': []})
        self.f.put('reviewed-profile-lab-links.json', {'items': [self.f.entry]})
        self.assertEqual(gaps.reviewed_historical_profile_links([]), [])
        self.assertEqual(gaps.reviewed_independently_dated_profile_links([]), [])
        self.f.entry['purpose'] = 'observe_literal_historical_profile_lab_link'
        self.f.write()
        self.assertEqual(gaps.reviewed_historical_profile_links([]), [])

    def test_old_same_capture_string_equality_and_new_instant_inequality_are_distinct(self):
        # Same instant with a different negative offset is never a new capture.
        self.f.proof['observedAt'] = '2026-10-07T15:04:19-07:00'
        self.f.entry['historicalFieldObservedAt'] = self.f.proof['observedAt']
        self.f.rebind_baseline(); self.d.reviews()
        self.assertEqual(self.d.helper(), [])
        self.f.entry['purpose'] = 'observe_literal_historical_profile_lab_link'
        self.f.write()
        self.assertEqual(gaps.reviewed_historical_profile_links([]), [])

    def test_original_sidecar_time_cannot_be_retimed_with_only_capture_hashes_rebound(self):
        meta = json.loads(self.f.meta_path.read_text())
        meta['observedAt'] = '2026-10-08T22:04:19+00:00'
        self.f.put(self.f.meta_path.name, meta)
        capture = self.f.entry['profileCapture']
        capture['observedAt'] = meta['observedAt']
        capture['metadataSha256'] = dated.fixtures.digest(self.f.meta_path.read_bytes())
        self.assertEqual(self.d.helper(), [])

    def test_report_body_tamper_or_symlink_escape_fails_closed(self):
        path = Path(self.f.entry['routeBoundaryReviewPath'])
        original = path.read_bytes()
        path.write_bytes(original + b' ')
        self.assertEqual(self.d.helper(), [])
        outside = self.f.root / 'outside-route.json'
        outside.write_bytes(original)
        path.unlink(); path.symlink_to(outside)
        self.f.entry['routeBoundaryReviewSha256'] = dated.fixtures.digest(original)
        self.assertEqual(self.d.helper(), [])

    def test_independent_route_interruption_resets_scope_without_page_success(self):
        candidate = dict(self.d.helper()[0], requiresLiveFetch=True)
        before = [p.read_bytes() for p in (self.f.body_path, self.f.meta_path,
                  self.f.out / 'records/one.json', self.f.out / 'packets/one.json')]
        with self.assertRaises(KeyboardInterrupt):
            self.f.execute_fixture(candidate, stage='robots', error=KeyboardInterrupt())
        ledger = json.loads((self.f.out / 'gap-results.json').read_text())
        self.assertEqual(ledger['items'], {})
        self.assertEqual(ledger['originalUriObservationStarts'][self.f.url]['journalContextKind'],
                         gaps.INDEPENDENT_PROFILE_LINK_KIND)
        self.assertTrue(ledger['originalUriObservationStarts'][self.f.url]['notAnOriginalListedURLCheck'])
        self.assertEqual(self.f.last_fetcher.currentPageMaxBytes, 2_000_000)
        self.assertIsNone(self.f.last_fetcher.currentOriginalObservationUrl)
        self.assertEqual(self.d.helper(), [])
        self.assertEqual(before, [p.read_bytes() for p in (self.f.body_path, self.f.meta_path,
                         self.f.out / 'records/one.json', self.f.out / 'packets/one.json')])
