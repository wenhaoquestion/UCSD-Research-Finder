"""Independent offline oracles for reviewed historical profile lab-link routes.

Every fixture lives in a temporary worktree. No real collector, gate or network
transport is invoked; execution tests use the real summary journal/instrumenter.
"""
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import local_lab_summaries as summaries
import local_lab_summary_gaps as gaps


def digest(data):
    return hashlib.sha256(data).hexdigest()


def proof_hash(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')).encode())


class ReviewedHistoricalProfileLinkTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='profile-link-oracle-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.out = self.root / 'data/local-lab-summaries'
        self.cache = self.root / 'collector'
        (self.cache / 'responses').mkdir(parents=True)
        (self.out / 'records').mkdir(parents=True)
        (self.out / 'packets').mkdir()
        self.url = 'http://example.ucsd.edu/Lab/index.html?view=1'
        self.listed = self.url.replace('http:', 'https:', 1)
        self.profile = 'https://profiles.ucsd.edu/example.person'
        self.when = '2026-10-07T22:04:19+00:00'
        self.label = 'Example Lab'
        self.proof = {'sourceUrl': self.profile, 'observedAt': self.when,
                      'status': 'verified', 'method': 'official_profile_explicit_lab_link',
                      'evidence': self.label + ' → ' + self.listed,
                      'preservedExtraField': {'scope': 'historical'}}
        self.lab = {'id': 'one', 'labName': 'Example Lab',
                    'labWebsiteUrl': self.listed, 'principalInvestigator': 'Not found',
                    'professorIds': ['person'],
                    'fieldEvidence': {'labWebsiteUrl': [self.proof]}}
        self.professor = {'id': 'person', 'officialProfileUrl': self.profile}
        self.baseline = {'labs': [self.lab], 'professors': [self.professor]}
        self.raw = {'labId': 'one', 'status': 'unresolved', 'summaryZh': None,
                    'researchQuestions': [], 'topics': [], 'methods': [], 'evidence': [],
                    'identity': {'status': 'uncertain', 'entityType': 'unconfirmed',
                                 'reason': 'No laboratory body.'},
                    'affiliation': {'status': 'uncertain', 'reason': 'Unknown.'},
                    'uncertainty': ['A personal profile is not whole-lab research.'],
                    'blockers': ['HTTPS robots TLS check failed.'],
                    'reviewedAt': '2026-10-16T06:00:00+00:00'}
        self.root_fetch = {'sourceUrl': self.listed, 'observedAt': self.raw['reviewedAt'],
                           'status': 'robots_unavailable', 'redirects': [],
                           'blockedUrl': self.listed,
                           'robots': {'sourceUrl': 'https://example.ucsd.edu/robots.txt',
                                      'observedAt': self.raw['reviewedAt'],
                                      'status': 'unavailable', 'httpStatus': 0,
                                      'error': 'curl: (60) certificate validation failed'}}
        self.packet = {'labId': 'one', 'labName': 'Example Lab',
                       'listedWebsite': self.listed, 'preparedAt': self.raw['reviewedAt'],
                       'destinationQueueStates': ['unresolved'],
                       'latestDestinationFetch': copy.deepcopy(self.root_fetch),
                       'sources': [], 'relatedDestinationChecks': [], 'followupChecks': []}
        self.body_path = self.out / 'profile.html'
        self.meta_path = self.out / 'profile.original.json'
        self.entry = {'labId': 'one', 'url': self.url, 'listedWebsite': self.listed,
                      'purpose': 'observe_literal_historical_profile_lab_link',
                      'observationOnly': True, 'reviewedAt': '2026-10-16T06:35:00+00:00',
                      'maxPageBytes': 2_000_000, 'professorId': 'person',
                      'latestDestinationFetch': copy.deepcopy(self.root_fetch),
                      'literalAnchor': {'label': self.label, 'href': self.url}}
        self.entries = [self.entry]
        self.captures = {}
        self.decisions = {'items': []}
        self._patch(gaps, 'ROOT', self.root)
        self._patch(gaps, 'OUT', self.out)
        self._patch(gaps, 'CACHE', self.cache)
        self._patch(summaries, 'ROOT', self.root)
        self._patch(summaries, 'OUT', self.out)
        self._patch(gaps, 'coordination_ready', lambda: False)
        self._patch(gaps, 'load_fetcher', lambda *a, **k: self.fail('Real fetcher forbidden'))
        self._patch(gaps, 'coordination_snapshot', lambda *a, **k: self.fail('Real PID probe forbidden'))
        network = patch('subprocess.run', side_effect=AssertionError('Real subprocess transport forbidden'))
        network.start()
        self.addCleanup(network.stop)
        self.rebind_baseline()
        self.set_markup(self.good_markup())
        self.freeze_records()
        self.write()

    def _patch(self, obj, name, value):
        guard = patch.object(obj, name, value)
        guard.start()
        self.addCleanup(guard.stop)

    def put(self, name, value, base=None):
        path = (base or self.out) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        return path

    def good_markup(self, anchor=None):
        anchor = anchor or f'<a href="{self.url}">{self.label}</a>'
        return ('<html><title>Example Person | UCSD Profiles</title><body>'
                '<div id="ctl00_divProfilesContentMain"><h1>Example Person</h1>'
                '<div id="http://profiles.catalyst.harvard.edu/ontology/prns#PropertyGroupFeaturedContent">'
                '<div id="http://vivoweb.org/ontology/core#webpage">' + anchor +
                '</div></div></div></body></html>')

    def set_markup(self, markup):
        self.body_path.write_bytes(markup.encode())
        meta = {'sourceUrl': self.profile, 'finalUrl': self.profile,
                'observedAt': self.when, 'status': 'ok', 'httpStatus': 200,
                'sha256': digest(self.body_path.read_bytes())}
        self.put(self.meta_path.name, meta)
        self.entry['profileCapture'] = {
            'sourceUrl': self.profile, 'observedAt': self.when,
            'bodyPath': str(self.body_path), 'metadataPath': str(self.meta_path),
            'bodySha256': digest(self.body_path.read_bytes()),
            'metadataSha256': digest(self.meta_path.read_bytes())}

    def rebind_baseline(self):
        path = self.put('research-atlas.json', self.baseline, self.root / 'data')
        digest_value = digest(path.read_bytes())
        if not hasattr(self, '_baseline_patch'):
            self._baseline_patch = patch.object(gaps, 'BASELINE_HASH', digest_value)
            self._baseline_patch.start()
            self.addCleanup(self._baseline_patch.stop)
        else:
            gaps.BASELINE_HASH = digest_value
        self.entry['baselineSha256'] = digest_value
        self.entry['fieldProofSha256'] = proof_hash(self.proof)

    def freeze_records(self):
        rp = self.put('records/one.json', self.raw)
        pp = self.put('packets/one.json', self.packet)
        self.entry.update(rawSha256=digest(rp.read_bytes()), packetSha256=digest(pp.read_bytes()))

    def write(self):
        self.put('records/one.json', self.raw)
        self.put('packets/one.json', self.packet)
        self.put('reviewed-profile-lab-links.json', {'items': self.entries})
        self.put('identity-decisions.json', self.decisions)
        self.put('manifest.json', {'items': [{'labId': 'one', 'packetPath': str(self.out / 'packets/one.json')}]})
        self.put('queue.json', {'items': self.captures}, self.cache)

    def helper(self):
        self.write()
        return gaps.reviewed_historical_profile_links(list(self.captures.values()))

    def plan(self):
        self.write()
        return gaps.plan()

    def assert_rejected(self):
        self.assertEqual(self.helper(), [])

    def put_robots(self, meta, base=None, body=None):
        url = 'http://example.ucsd.edu/robots.txt'
        stem = 'robots-' + digest(url.encode())
        self.put(stem + '.json', dict(sourceUrl=url, observedAt=self.when, **meta),
                 base or self.cache / 'responses')
        if body is not None:
            (base or self.cache / 'responses').joinpath(stem + '.html').write_text(body)

    def test_positive_route_has_separate_kind_and_changes_no_entity_or_root(self):
        before = [(self.out / p).read_bytes() for p in ['records/one.json', 'packets/one.json']]
        item = self.plan()['items'][0]
        self.assertEqual(item['kind'], gaps.PROFILE_LINK_KIND)
        self.assertTrue(item['requiresLiveFetch'])
        self.assertEqual(item['url'], self.url)
        self.assertTrue(item['notAnOriginalListedURLCheck'])
        self.assertTrue(item['notAnAcceptedCanonicalLabUrl'])
        self.assertEqual(item['observationScope'], 'related_historical_profile_link_only')
        self.assertNotIn('originalURIObservationReviews', item)
        self.assertEqual(item['maxPageBytes'], 2_000_000)
        self.assertEqual(before, [(self.out / p).read_bytes() for p in ['records/one.json', 'packets/one.json']])
        _, root = summaries.hydrate(self.raw, self.packet)
        self.assertIsNone(root['requestedUrl'])
        self.assertFalse(root['canCountAsVerifiedLabGroupURL'])
        self.assertEqual(self.lab['principalInvestigator'], 'Not found')

    def test_generic_lab_site_proof_is_route_only_and_must_match_capture_date(self):
        self.label = 'Lab Site'
        self.entry['literalAnchor']['label'] = self.label
        self.proof.update(method='official_profile_generic_lab_link', evidence=self.label + ' → ' + self.listed)
        self.rebind_baseline()
        self.set_markup(self.good_markup())
        self.assertEqual(len(self.helper()), 1)
        self.proof['observedAt'] = '2026-10-03T01:44:19+00:00'
        self.rebind_baseline()
        self.assert_rejected()

    def test_missing_entry_bindings_fail_closed(self):
        original = copy.deepcopy(self.entry)
        for field in original:
            with self.subTest(field=field):
                self.entry.clear()
                self.entry.update(copy.deepcopy(original))
                self.entry.pop(field)
                self.assert_rejected()

    def test_wrong_review_markers_baseline_cap_and_hashes_fail_closed(self):
        original = copy.deepcopy(self.entry)
        changes = [('purpose', 'verify_historical_lab_identity'), ('observationOnly', 1),
                   ('reviewedAt', '2026-10-16T06:35:00'), ('baselineSha256', '0' * 64),
                   ('maxPageBytes', 8_000_000), ('maxPageBytes', 2_000_000.0),
                   ('maxPageBytes', True), ('rawSha256', '0' * 64),
                   ('packetSha256', '0' * 64), ('fieldProofSha256', '0' * 64)]
        for field, value in changes:
            with self.subTest(field=field, value=value):
                self.entry.clear()
                self.entry.update(copy.deepcopy(original))
                self.entry[field] = value
                self.assert_rejected()

    def test_actual_baseline_bytes_and_complete_proof_are_frozen(self):
        p = self.root / 'data/research-atlas.json'
        p.write_text(p.read_text() + '\n')
        self.assert_rejected()
        self.proof['preservedExtraField']['scope'] = 'different'
        old_hash = self.entry['fieldProofSha256']
        self.rebind_baseline()
        self.entry['fieldProofSha256'] = old_hash
        self.assert_rejected()

    def test_professor_relation_profile_and_verified_field_are_required(self):
        original_lab = copy.deepcopy(self.lab)
        for field, value in [('professorIds', []), ('labWebsiteUrl', self.url)]:
            with self.subTest(field=field):
                self.lab.clear(); self.lab.update(copy.deepcopy(original_lab))
                self.lab[field] = value
                self.rebind_baseline()
                self.assert_rejected()
        self.lab.clear(); self.lab.update(original_lab)
        self.professor['officialProfileUrl'] = 'https://profiles.ucsd.edu/other.person'
        self.rebind_baseline()
        self.assert_rejected()

    def test_rehashed_unverified_or_non_link_field_proof_never_admits(self):
        original = copy.deepcopy(self.proof)
        for field, value in [('status', 'unverified'),
                             ('method', 'ucsd_profiles_overview_section'),
                             ('evidence', self.label + ' → ' + self.url),
                             ('sourceUrl', 'https://profiles.ucsd.edu/other.person')]:
            with self.subTest(field=field):
                self.proof.clear(); self.proof.update(copy.deepcopy(original))
                self.proof[field] = value
                self.rebind_baseline()
                self.assert_rejected()

    def test_new_profile_route_does_not_relax_the_original_listed_uri_contract(self):
        for listed in [self.listed, self.url]:
            with self.subTest(listedWebsite=listed):
                self.write()
                entry = dict(copy.deepcopy(self.entry), labIds=['one'], listedWebsite=listed)
                self.put('reviewed-original-uri-observations.json', {'items': [entry]})
                self.assertEqual(gaps.reviewed_original_uri_observations([]), [])
                self.assertEqual(len(gaps.reviewed_historical_profile_links([])), 1)

    def test_snapshot_body_metadata_hash_url_time_status_and_path_are_bound(self):
        original = copy.deepcopy(self.entry['profileCapture'])
        (self.root / 'outside.html').write_bytes(self.body_path.read_bytes())
        for field, value in [('bodySha256', '0' * 64), ('metadataSha256', '0' * 64),
                             ('observedAt', '2026-10-07T22:04:20+00:00'),
                             ('sourceUrl', 'https://profiles.ucsd.edu/other.person'),
                             ('bodyPath', str(self.root / 'outside.html'))]:
            with self.subTest(field=field):
                self.entry['profileCapture'] = copy.deepcopy(original)
                self.entry['profileCapture'][field] = value
                self.assert_rejected()

    def test_rehashed_sidecar_cannot_change_original_request_time_or_response(self):
        original = json.loads(self.meta_path.read_text())
        for field, value in [('sourceUrl', 'https://profiles.ucsd.edu/other'),
                             ('finalUrl', 'https://profiles.ucsd.edu/other'),
                             ('observedAt', self.entry['reviewedAt']), ('httpStatus', True),
                             ('httpStatus', 403), ('status', 'access_challenge'),
                             ('sha256', '0' * 64)]:
            with self.subTest(field=field):
                meta = copy.deepcopy(original); meta[field] = value
                self.put(self.meta_path.name, meta)
                self.entry['profileCapture']['metadataSha256'] = digest(self.meta_path.read_bytes())
                self.assert_rejected()

    def test_byte_tampering_with_stale_hash_is_rejected(self):
        self.body_path.write_bytes(self.body_path.read_bytes() + b' ')
        self.assert_rejected()

    def test_dom_anchor_must_be_live_inside_explicit_profile_main_and_featured_webpage(self):
        good = self.good_markup()
        variants = [good.replace('ctl00_divProfilesContentMain', 'unrelated-content'),
                    good.replace('http://vivoweb.org/ontology/core#webpage', 'unrelated-webpage'),
                    good.replace('http://profiles.catalyst.harvard.edu/ontology/prns#PropertyGroupFeaturedContent', 'other-section')]
        for markup in variants:
            with self.subTest(markup=markup):
                self.set_markup(markup)
                self.assert_rejected()

    def test_script_comment_template_nav_and_hidden_anchors_are_not_discoveries(self):
        anchor = f'<a href="{self.url}">{self.label}</a>'
        wrappers = [f'<script>{anchor}</script>', f'<!--{anchor}-->',
                    f'<template>{anchor}</template>', f'<nav>{anchor}</nav>',
                    f'<div hidden>{anchor}</div>', f'<div aria-hidden="true">{anchor}</div>',
                    f'<div style="display:none">{anchor}</div>',
                    f'<div style="visibility:hidden">{anchor}</div>']
        for markup in wrappers:
            with self.subTest(markup=markup):
                self.set_markup(self.good_markup(markup))
                self.assert_rejected()

    def test_raw_literal_href_label_and_effective_target_are_not_guessed(self):
        original = copy.deepcopy(self.entry['literalAnchor'])
        for value in [{'label': self.label, 'href': self.listed},
                      {'label': 'Website', 'href': self.url},
                      {'label': self.label, 'href': '/Lab/index.html?view=1'}]:
            with self.subTest(value=value):
                self.entry['literalAnchor'] = value
                self.assert_rejected()
        self.entry['literalAnchor'] = original
        self.set_markup(self.good_markup(f'<a href="{self.listed}">{self.label}</a>'))
        self.assert_rejected()

    def test_scheme_host_path_query_and_nonroot_slash_must_match_retained_https(self):
        original = self.entry['url']
        variants = [self.listed, original.replace('example.', 'www.example.'),
                    original.replace('/Lab/', '/lab/'), original.replace('?view=1', '?view=2'),
                    original.replace('index.html?', 'index.html/?'),
                    original.replace('http:', 'ftp:'), original.replace('.edu/', '.edu:80/'),
                    original + '#section', original.replace('example.ucsd.edu', 'example.ucsd.edu.evil.test')]
        for value in variants:
            with self.subTest(value=value):
                self.entry['url'] = value
                self.entry['literalAnchor']['href'] = value
                self.set_markup(self.good_markup(f'<a href="{value}">{self.label}</a>'))
                self.assert_rejected()
        self.entry['url'] = original

    def test_literal_wire_uri_rejects_whitespace_and_controls_even_with_all_hashes_rebound(self):
        original = self.url
        for value in [' ' + original, original + ' ', original.replace('/Lab/', '/La\tb/'),
                      original.replace('http:', '\nhttp:'), original + '#',
                      original.replace('/Lab/', '/La\x00b/'),
                      original.replace('/Lab/', '/La\x7fb/')]:
            with self.subTest(value=repr(value)):
                self.url = value
                self.entry['url'] = value
                self.entry['literalAnchor']['href'] = value
                self.set_markup(self.good_markup())
                self.assert_rejected()

    def test_mismatch_inventory_raw_gates_and_supported_status_cannot_be_relaxed(self):
        original = copy.deepcopy(self.raw)
        for change in [{'status': 'supported'}, {'identity': {'status': 'mismatch'}},
                       {'identity': {'status': 'uncertain', 'hasUnresolvedMismatch': True}}]:
            with self.subTest(change=change):
                self.raw.clear(); self.raw.update(copy.deepcopy(original)); self.raw.update(change)
                self.freeze_records(); self.assert_rejected()
        self.raw.clear(); self.raw.update(original); self.freeze_records()
        self.decisions = {'initialMismatchLabIds': ['one'], 'items': []}
        self.assert_rejected()
        self.decisions = {'items': [{'labId': 'one', 'unresolvedMismatch': True}]}
        self.assert_rejected()

    def test_record_bytes_and_full_nested_root_metadata_remain_frozen(self):
        self.raw['uncertainty'].append('Unreviewed change')
        self.assert_rejected()
        self.raw['uncertainty'].pop()
        self.packet['latestDestinationFetch']['robots']['attempts'] = 3
        self.freeze_records()  # Rehash alone cannot update the separately frozen fetch binding.
        self.assert_rejected()

    def test_https_tls_failure_is_not_an_attempt_at_the_literal_http_uri(self):
        self.captures = {'normalized': {'url': self.url, 'state': 'unresolved',
                                       'fetch': copy.deepcopy(self.root_fetch)}}
        result = self.plan()
        self.assertEqual(result['liveCandidateCount'], 1)
        self.assertEqual(result['items'][0]['availability'], 'not_captured')

    def test_any_exact_actual_uri_attempt_or_pending_target_closes_one_shot(self):
        for status in ['ok', 'http_error', 'robots_unavailable', 'fetch_error']:
            with self.subTest(status=status):
                self.captures = {'exact': {'url': self.url, 'state': 'unresolved',
                                          'fetch': {'sourceUrl': self.url, 'status': status,
                                                    'observedAt': self.when}}}
                self.assert_rejected()
        for state in ['pending', 'running']:
            with self.subTest(state=state):
                self.captures = {'pending': {'url': self.url, 'state': state}}
                self.assert_rejected()

    def test_top_level_history_blocked_url_and_proven_final_close_exact_uri(self):
        attempts = [{'sourceUrl': self.url, 'status': 'fetch_error'},
                    {'sourceUrl': self.listed, 'status': 'robots_unavailable', 'blockedUrl': self.url},
                    {'sourceUrl': self.listed, 'status': 'ok', 'httpStatus': 200, 'finalUrl': self.url},
                    {'sourceUrl': self.listed, 'redirects': [{'from': self.url, 'to': self.listed}]}]
        for meta in attempts:
            with self.subTest(meta=meta):
                self.captures = {'old': {'url': self.listed, 'state': 'unresolved',
                                        'fetch': {}, 'attemptHistory': [meta]}}
                self.assert_rejected()

    def test_bare_redirect_target_or_unproven_final_is_not_an_actual_target_attempt(self):
        attempts = [{'sourceUrl': self.listed, 'httpStatus': 301, 'finalUrl': self.listed,
                     'redirects': [{'from': self.listed, 'to': self.url}]},
                    {'sourceUrl': self.listed, 'finalUrl': self.url},
                    {'sourceUrl': self.listed, 'httpStatus': 0, 'finalUrl': self.url}]
        for meta in attempts:
            with self.subTest(meta=meta):
                self.captures = {'not_requested': {'url': self.listed, 'state': 'unresolved', 'fetch': meta}}
                self.assertEqual(len(self.helper()), 1)

    def test_journal_and_orphan_wire_close_without_proving_page_or_saving_a_result(self):
        ledgers = [{'originalUriObservationStarts': {self.url: {'state': 'started_not_completed'}}},
                   {'wireEvents': [{'url': self.url, 'kind': 'page_or_redirect'}]},
                   {'wireEvents': [{'url': 'http://example.ucsd.edu/robots.txt',
                                    'originalObservationUrl': self.url, 'kind': 'robots'}]}]
        for value in ledgers:
            with self.subTest(value=value):
                self.put('gap-results.json', dict(items={}, **value))
                self.assert_rejected()

    def test_explicit_denial_and_legacy_http200_login_in_root_or_history_close_route(self):
        original = copy.deepcopy(self.packet)
        refusals = [{'status': 'authentication_required'}, {'httpStatus': 403},
                    {'status': 'access_challenge'}, {'error': 'access_challenge', 'httpStatus': 404},
                    {'status': 'ok', 'httpStatus': 200, 'finalUrl': 'https://accounts.google.com/'},
                    {'status': 'ok', 'httpStatus': 200, 'finalUrl': 'https://example.ucsd.edu/signin'},
                    {'redirects': [{'from': self.listed, 'to': 'https://login.microsoftonline.com/'}]}]
        for meta in refusals:
            for field in ['destinationAttemptHistory', 'relatedDestinationChecks', 'followupChecks']:
                with self.subTest(meta=meta, field=field):
                    self.packet.clear(); self.packet.update(copy.deepcopy(original))
                    self.packet[field] = [meta]
                    self.freeze_records(); self.assert_rejected()

    def test_projected_transport_status_is_still_an_access_boundary(self):
        for status in ['authentication_required', 'access_challenge', 'robots_denied']:
            with self.subTest(status=status):
                self.packet['relatedDestinationChecks'] = [{'transportStatus': status,
                                                           'checkedUrl': self.listed}]
                self.freeze_records(); self.assert_rejected()

    def test_collector_authentication_target_forms_close_root_even_with_http200(self):
        destinations = ['https://shibboleth.ucsd.edu/idp/profile',
                        'https://example.ucsd.edu/oauth2/authorize',
                        'https://example.ucsd.edu/login.aspx',
                        'https://accounts.google.com/',
                        'https://login.microsoftonline.com/',
                        'https://login.ucsd.edu/']
        for url in destinations:
            with self.subTest(destination=url):
                meta = {'sourceUrl': self.listed, 'observedAt': self.when,
                        'status': 'ok', 'httpStatus': 200, 'finalUrl': url}
                self.packet['latestDestinationFetch'] = meta
                self.entry['latestDestinationFetch'] = copy.deepcopy(meta)
                self.freeze_records()
                self.assert_rejected()

    def test_login_in_capture_history_or_nested_robots_blocks_related_route(self):
        boundaries = [{'status': 'ok', 'httpStatus': 200,
                       'finalUrl': 'https://example.ucsd.edu/login.aspx'},
                      {'status': 'robots_unavailable',
                       'robots': {'sourceUrl': 'http://example.ucsd.edu/robots.txt',
                                  'status': 'ok', 'httpStatus': 200,
                                  'finalUrl': 'https://shibboleth.ucsd.edu/idp/profile'}}]
        for meta in boundaries:
            with self.subTest(meta=meta):
                self.captures = {'legacy': {'url': self.listed, 'state': 'unresolved',
                                            'fetch': {}, 'attemptHistory': [meta]}}
                self.assert_rejected()

    def test_robots_timestamp_order_is_instant_based_and_conflicting_ties_fail_closed(self):
        robots_url = 'http://example.ucsd.edu/robots.txt'
        stem = 'robots-' + digest(robots_url.encode()) + '.json'
        # +01:00 string sorts after Z-like +00, but is actually the earlier instant.
        self.put(stem, {'sourceUrl': robots_url, 'observedAt': '2026-10-16T07:00:00+01:00',
                        'status': 'not_found', 'httpStatus': 404}, self.cache / 'responses')
        self.put(stem, {'sourceUrl': robots_url, 'observedAt': '2026-10-16T06:01:00+00:00',
                        'status': 'unavailable', 'httpStatus': 0}, self.out / 'gap-cache')
        self.assert_rejected()
        # Same instant: a conflicting unavailable record cannot be hidden by order.
        self.put(stem, {'sourceUrl': robots_url, 'observedAt': '2026-10-16T06:00:00+00:00',
                        'status': 'unavailable', 'httpStatus': 0}, self.out / 'gap-cache')
        self.assert_rejected()

    def test_known_http_origin_robots_unavailable_closes_but_404_not_found_does_not(self):
        self.put_robots({'status': 'unavailable', 'httpStatus': 302,
                         'error': 'robots_redirect_is_not_a_robots_file'})
        self.assert_rejected()
        self.put_robots({'status': 'not_found', 'httpStatus': 404, 'error': ''})
        self.assertEqual(len(self.helper()), 1)

    def test_http_robots_unavailable_in_capture_metadata_blocks_even_without_sidecar(self):
        self.captures = {'other': {'url': 'http://example.ucsd.edu/other', 'state': 'unresolved',
                                 'fetch': {'sourceUrl': 'http://example.ucsd.edu/other',
                                           'status': 'robots_unavailable',
                                           'robots': {'sourceUrl': 'http://example.ucsd.edu/robots.txt',
                                                      'status': 'unavailable', 'httpStatus': 0,
                                                      'observedAt': self.when, 'error': 'timeout'}}}}
        self.assert_rejected()

    def test_robots_explicit_denial_or_challenge_dominates_later_non_refusal(self):
        self.put_robots({'status': 'checked', 'httpStatus': 200}, body='User-agent: *\nDisallow: /\n')
        self.assert_rejected()
        self.put_robots({'status': 'not_found', 'httpStatus': 404, 'error': 'access_challenge'})
        self.put_robots({'status': 'not_found', 'httpStatus': 404, 'error': ''}, self.out / 'gap-cache')
        self.assert_rejected()

    def execute_fixture(self, candidate, stage='success', error=None):
        case = self
        calls = []
        class FakePublicFetcher:
            def __init__(self, *args, **kwargs):
                case.last_fetcher = self
            def _wire(self, url, minimum=1, max_bytes=2_000_000):
                return self._transport(url, max_bytes)
            def _transport(self, url, max_bytes):
                calls.append((url, max_bytes))
                if stage == 'returned_error':
                    return 0, {}, '', 'offline curl timeout'
                if stage == 'after_initial_redirect' and url == case.url:
                    return 301, {'location': case.listed}, '', ''
                if error is not None:
                    raise error
                return 200, {}, 'fixture', ''
            def fetch(self, url):
                if stage == 'before_wire':
                    raise error
                robots = 'http://example.ucsd.edu/robots.txt'
                if stage == 'robots':
                    self._wire(robots, max_bytes=300_000)
                elif stage == 'after_initial_redirect':
                    self._wire(url)
                    self._wire('https://example.ucsd.edu/robots.txt', max_bytes=300_000)
                else:
                    if stage == 'success':
                        self._wire(robots, max_bytes=300_000)
                    self._wire(url)
                return {'sourceUrl': url, 'observedAt': case.when,
                        'status': 'fetch_error' if stage == 'returned_error' else 'ok',
                        'httpStatus': 0 if stage == 'returned_error' else 200,
                        'finalUrl': url}, 'fixture'
        module = types.SimpleNamespace(PublicFetcher=FakePublicFetcher, safe_url=lambda x: x)
        snapshot = {'sourceHashes': {'collectorCodeSha256': 'offline-fixture'}, 'requiredSourceHashes': {}}
        self.put('network-coordination.json', dict(snapshot, adapterVerification={
            'adapterSha256': digest(Path(gaps.__file__).read_bytes())}))
        with patch.object(gaps, 'coordination_ready', return_value=True), \
                patch.object(gaps, 'coordination_snapshot', return_value=snapshot), \
                patch.object(gaps, 'load_fetcher', return_value=module), \
                patch.object(gaps, 'plan', return_value={'items': [candidate]}), \
                contextlib.redirect_stdout(io.StringIO()):
            result = gaps.execute(1)
        return result, calls

    def test_real_execution_journal_marks_related_route_and_preserves_all_source_and_root_bytes(self):
        candidate = self.plan()['items'][0]
        paths = [self.body_path, self.meta_path, self.out / 'records/one.json', self.out / 'packets/one.json']
        before = [p.read_bytes() for p in paths]
        result, calls = self.execute_fixture(candidate)
        self.assertEqual(result['attempted'], 1)
        self.assertEqual(calls, [('http://example.ucsd.edu/robots.txt', 300_000), (self.url, 2_000_000)])
        saved = json.loads((self.out / 'gap-results.json').read_text())
        start = saved['originalUriObservationStarts'][self.url]
        self.assertEqual(start['journalContextKind'], gaps.PROFILE_LINK_KIND)
        self.assertTrue(start['notAnOriginalListedURLCheck'])
        self.assertTrue(start['journalIsNotPageRequestProof'])
        self.assertTrue(saved['items'][self.url]['fetch']['actualPageRequestMade'])
        self.assertEqual(self.last_fetcher.currentPageMaxBytes, 2_000_000)
        self.assertIsNone(self.last_fetcher.currentOriginalObservationUrl)
        self.assertEqual(before, [p.read_bytes() for p in paths])
        self.assertEqual(self.plan()['liveCandidateCount'], 0)

    def test_transport_exception_or_hard_interrupt_closes_once_without_fake_response_proof(self):
        candidate = self.plan()['items'][0]
        for stage in ['before_wire', 'robots', 'page']:
            for exception in [RuntimeError('offline failure'), KeyboardInterrupt()]:
                with self.subTest(stage=stage, exception=type(exception).__name__):
                    (self.out / 'gap-results.json').unlink(missing_ok=True)
                    with self.assertRaises(type(exception)):
                        self.execute_fixture(candidate, stage, exception)
                    saved = json.loads((self.out / 'gap-results.json').read_text())
                    self.assertEqual(self.last_fetcher.currentPageMaxBytes, 2_000_000)
                    self.assertIsNone(self.last_fetcher.currentOriginalObservationUrl)
                    if isinstance(exception, Exception):
                        meta = saved['items'][self.url]['fetch']
                        self.assertEqual(meta['status'], 'fetch_exception')
                        self.assertFalse(meta['actualPageRequestMade'])
                        self.assertIsNone(meta['liveCheckedAt'])
                        self.assertFalse({'httpStatus', 'finalUrl', 'sha256'} & set(meta))
                    else:
                        self.assertEqual(saved['items'], {})
                    self.assertEqual(self.plan()['liveCandidateCount'], 0)

    def test_returned_curl_error_proves_attempt_but_not_success_or_new_lab_identity(self):
        candidate = self.plan()['items'][0]
        self.execute_fixture(candidate, 'returned_error')
        saved = json.loads((self.out / 'gap-results.json').read_text())
        self.assertTrue(saved['items'][self.url]['fetch']['actualPageRequestMade'])
        self.assertEqual(saved['items'][self.url]['fetch']['httpStatus'], 0)
        self.assertEqual(self.raw['identity']['status'], 'uncertain')
        self.assertEqual(self.plan()['liveCandidateCount'], 0)

    def test_initial_redirect_response_followed_by_robots_error_keeps_actual_initial_page_proof(self):
        candidate = self.plan()['items'][0]
        with self.assertRaises(RuntimeError):
            self.execute_fixture(candidate, 'after_initial_redirect', RuntimeError('robots failure'))
        saved = json.loads((self.out / 'gap-results.json').read_text())
        meta = saved['items'][self.url]['fetch']
        self.assertEqual(meta['status'], 'fetch_exception')
        self.assertTrue(meta['actualPageRequestMade'])
        self.assertNotIn('finalUrl', meta)
        self.assertEqual(saved['wireEvents'][0]['httpStatus'], 301)
        self.assertEqual(self.plan()['liveCandidateCount'], 0)


if __name__ == '__main__':
    unittest.main()
