import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_ucsd_preservation import audit
from lab_identity_merges import apply_reviewed_merges, redirect_text, verified_reviews, verify_capture_proofs


class LabIdentityMergeTests(unittest.TestCase):
    def heading_fixture(self, tmp):
        cache = Path(tmp)
        (cache / 'responses').mkdir()
        uri = 'https://center.ucsd.edu/'
        raw = b'<header><h1>Computational Neurology Center</h1></header><main><h2>Research</h2><p>We study objective measurement of movement disorders.</p></main>'
        (cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')).write_bytes(raw)
        meta = {'status': 'ok', 'sourceUrl': uri, 'finalUrl': uri, 'observedAt': '2026-10-16T01:00:00+00:00'}
        proof = {'requestedUrl': uri, 'sourceUrl': uri, 'observedAt': meta['observedAt'],
                 'bodySha256': hashlib.sha256(raw).hexdigest(), 'evidenceType': 'document_heading',
                 'headingTag': 'h1', 'evidence': 'Computational Neurology Center'}
        return cache, {'items': {uri: {'url': uri, 'fetch': meta}}}, proof

    def test_own_document_branding_heading_outside_main_is_capture_verifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, queue, proof = self.heading_fixture(tmp)
            verify_capture_proofs([proof], queue, cache, 'center')
            with self.assertRaises(ValueError):
                verify_capture_proofs([{**proof, 'evidenceType': 'main_text_quote'}], queue, cache, 'center')

    def test_heading_proof_requires_exact_text_and_actual_heading_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, queue, proof = self.heading_fixture(tmp)
            for changes in [{'evidence': 'Neurology Center'}, {'headingTag': 'h2'}, {'headingTag': 'header'}, {'headingTag': None}]:
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    verify_capture_proofs([{**proof, **changes}], queue, cache, 'center')

    def test_heading_proof_preserves_raw_capture_date_and_hash_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, queue, proof = self.heading_fixture(tmp)
            for changes in [{'observedAt': '2020-01-01'}, {'bodySha256': '0' * 64}, {'sourceUrl': 'https://other.ucsd.edu/'}]:
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    verify_capture_proofs([{**proof, **changes}], queue, cache, 'center')

    def test_document_link_verifies_header_navigation_without_a_main_content_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, queue, proof = self.heading_fixture(tmp)
            path = cache / 'responses' / (hashlib.sha256(proof['requestedUrl'].encode()).hexdigest() + '.html')
            path.write_bytes(path.read_bytes().replace(b'<header>', b'<header><a href="/home">Center Home</a>'))
            proof.update(bodySha256=hashlib.sha256(path.read_bytes()).hexdigest(), evidenceType='document_link',
                         evidence='Center Home -> https://center.ucsd.edu/home', linkText='Center Home', linkUrl='https://center.ucsd.edu/home')
            verify_capture_proofs([proof], queue, cache, 'center')
            with self.assertRaises(ValueError):
                verify_capture_proofs([{**proof, 'evidenceType': 'named_link'}], queue, cache, 'center')

    def test_document_link_requires_the_actual_named_anchor_and_resolved_uri(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, queue, proof = self.heading_fixture(tmp)
            path = cache / 'responses' / (hashlib.sha256(proof['requestedUrl'].encode()).hexdigest() + '.html')
            path.write_bytes(path.read_bytes().replace(b'<header>', b'<header><a href="/home">Center Home</a>'))
            proof.update(bodySha256=hashlib.sha256(path.read_bytes()).hexdigest(), evidenceType='document_link',
                         evidence='Center Home -> https://center.ucsd.edu/home', linkText='Center Home', linkUrl='https://center.ucsd.edu/home')
            for changes in [{'linkText': 'Another Lab'}, {'linkUrl': 'http://center.ucsd.edu/home'},
                            {'linkUrl': 'https://center.ucsd.edu/other'}, {'evidence': 'A different quoted link'}]:
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    verify_capture_proofs([{**proof, **changes}], queue, cache, 'center')

    def test_publisher_attribute_proof_verifies_literal_saved_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, queue, proof = self.heading_fixture(tmp)
            path = cache / 'responses' / (hashlib.sha256(proof['requestedUrl'].encode()).hexdigest() + '.html')
            path.write_bytes(path.read_bytes() + b'<meta property="og:url" content="https://publisher.example/own-site">')
            proof.update(bodySha256=hashlib.sha256(path.read_bytes()).hexdigest(), evidenceType='html_attribute',
                         elementTag='meta', attributeName='content', attributeValue='https://publisher.example/own-site',
                         selectorAttributes={'property': 'og:url'}, evidence='meta[content] = https://publisher.example/own-site')
            verify_capture_proofs([proof], queue, cache, 'center')
            for changes in [{'selectorAttributes': {'property': 'og:image'}}, {'elementTag': 'link'},
                            {'attributeName': 'href'}, {'attributeValue': 'http://publisher.example/own-site'},
                            {'observedAt': '2020-01-01'}, {'bodySha256': '0' * 64}, {'evidence': 'Invented attribute'}]:
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    verify_capture_proofs([{**proof, **changes}], queue, cache, 'center')

    def fixture(self):
        old_proof = {'sourceUrl': 'https://old.ucsd.edu/', 'observedAt': '2020-01-01T00:00:00+00:00', 'evidence': 'Example Lab'}
        data = {'labs': [{'id': 'canonical', 'labName': 'Example Lab', 'labWebsiteUrl': 'https://new.ucsd.edu/', 'sourceUrls': [], 'fieldEvidence': {}},
                         {'id': 'legacy', 'labName': 'Example Lab Homepage', 'labWebsiteUrl': 'https://old.ucsd.edu/', 'sourceUrls': [old_proof['sourceUrl']], 'professorIds': ['person'], 'fieldEvidence': {'labName': [old_proof]}}],
                'professors': [{'id': 'person', 'labAffiliation': 'Example Lab Homepage', 'labAffiliationUrl': 'https://old.ucsd.edu/',
                                'sourceUrls': [old_proof['sourceUrl']], 'labAffiliations': [{'labId': 'legacy', 'url': 'https://old.ucsd.edu/', 'fieldEvidence': old_proof}],
                                'fieldEvidence': {'labAffiliationUrl': [old_proof]}}]}
        proof = {'requestedUrl': 'https://new.ucsd.edu/', 'sourceUrl': 'https://new.ucsd.edu/', 'observedAt': '2026-01-01T00:00:00+00:00', 'evidence': 'Example Lab', 'bodySha256': 'raw-hash'}
        row = {'action': 'merge', 'sourceLabId': 'legacy', 'targetLabId': 'canonical', 'reason': 'Explicit captured same-entity identity review',
               'primaryLabName': 'Example Lab', 'primaryLabWebsiteUrl': 'https://new.ucsd.edu/', 'acceptedAliasUrls': ['https://old.ucsd.edu/'],
               'captureVerified': True, 'evidence': [proof]}
        return data, row

    def test_merge_preserves_legacy_id_full_record_dates_and_professor_links(self):
        data, row = self.fixture()
        data['labs'][1]['aliasResourceReviews'] = [{'url': 'https://old.ucsd.edu/', 'reason': 'Retained exact URI review'}]
        baseline = copy.deepcopy(data)
        removed = apply_reviewed_merges(data, [row])
        self.assertEqual(removed[0]['record'], baseline['labs'][1])
        self.assertEqual(data['labs'][0]['aliasIds'], ['legacy'])
        self.assertEqual(data['professors'][0]['labAffiliations'][0]['labId'], 'canonical')
        self.assertEqual(data['professors'][0]['labAffiliationUrl'], 'https://new.ucsd.edu/')
        self.assertIn(row['evidence'][0]['sourceUrl'], data['professors'][0]['sourceUrls'])
        self.assertEqual(data['labs'][0]['aliasResourceReviews'], baseline['labs'][1]['aliasResourceReviews'])
        self.assertEqual(audit(baseline, data, [removed])['status'], 'passed')
        first = copy.deepcopy(data)
        self.assertEqual(apply_reviewed_merges(data, [row]), [])
        self.assertEqual(first, data)

    def test_invalid_later_merge_cannot_partially_mutate_an_earlier_valid_merge(self):
        data, row = self.fixture()
        original = copy.deepcopy(data)
        invalid = {**row, 'sourceLabId': 'another', 'captureVerified': False}
        with self.assertRaises(ValueError):
            apply_reviewed_merges(data, [row, invalid])
        self.assertEqual(data, original)

    def test_cycles_are_rejected_before_any_record_changes(self):
        data, row = self.fixture()
        original = copy.deepcopy(data)
        with self.assertRaisesRegex(ValueError, 'acyclic'):
            apply_reviewed_merges(data, [row, {**row, 'sourceLabId': 'canonical', 'targetLabId': 'legacy'}])
        self.assertEqual(data, original)

    def test_replaying_a_retired_alias_does_not_reintroduce_duplicate_links_or_old_labels(self):
        from rebuild_verified_atlas import merge_patch
        data, row = self.fixture()
        old = copy.deepcopy(data)
        merge_patch(data['labs'][1], old['labs'][1])
        apply_reviewed_merges(data, [row])
        first = copy.deepcopy(data)
        merge_patch(data['labs'][0], old['labs'][1])
        data['professors'][0]['labAffiliations'].extend(copy.deepcopy(old['professors'][0]['labAffiliations']))
        self.assertEqual(apply_reviewed_merges(data, [row]), [])
        self.assertEqual(data, first)

    def test_capture_verifier_requires_original_raw_bytes_date_and_actual_redirects(self):
        _, row = self.fixture()
        url = 'https://old.ucsd.edu/'
        raw = b'<main>Example Lab\r\nidentity</main>'
        chain = [{'from': url, 'to': 'https://new.ucsd.edu/', 'httpStatus': 301}]
        meta = {'status': 'ok', 'sourceUrl': url, 'finalUrl': 'https://new.ucsd.edu/', 'observedAt': '2020-01-01', 'redirects': chain}
        proof = {'requestedUrl': url, 'sourceUrl': meta['finalUrl'], 'observedAt': meta['observedAt'], 'bodySha256': hashlib.sha256(raw).hexdigest(), 'evidence': 'Example Lab identity'}
        queue = {'items': {'old': {'url': url, 'fetch': meta}}}
        row['evidence'] = [proof]
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / 'responses').mkdir()
            path = cache / 'responses' / (hashlib.sha256(url.encode()).hexdigest() + '.html')
            path.write_bytes(raw)
            self.assertTrue(verified_reviews({'entries': [row]}, queue, cache)[0]['captureVerified'])
            row['evidence'] = [{**proof, 'evidenceType': 'redirect_chain', 'redirects': chain, 'evidence': redirect_text(chain)}]
            self.assertTrue(verified_reviews({'entries': [row]}, queue, cache)[0]['captureVerified'])
            for field, wrong in [('observedAt', '2026-01-01'), ('bodySha256', hashlib.sha256(path.read_text().encode()).hexdigest()), ('redirects', [{'from': url, 'to': 'https://unrelated.ucsd.edu/', 'httpStatus': 301}])]:
                bad = copy.deepcopy(row)
                bad['evidence'][0][field] = wrong
                with self.subTest(field=field), self.assertRaises(ValueError):
                    verified_reviews({'entries': [bad]}, queue, cache)
            bad = copy.deepcopy(row)
            bad['acceptedAliasUrls'].append('http://www.old.ucsd.edu/')
            with self.assertRaisesRegex(ValueError, 'no actual positive capture'):
                verified_reviews({'entries': [bad]}, queue, cache)

    def test_named_person_page_link_must_point_to_the_reviewed_lab_homepage(self):
        _, row = self.fixture()
        url, target = 'https://example.ucsd.edu/person', 'https://lab.ucsd.edu/'
        row.pop('primaryLabWebsiteUrl')
        row['acceptedAliasUrls'] = []
        for actual_target in [target, 'https://different.ucsd.edu/']:
            with self.subTest(target=actual_target), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp)
                (cache / 'responses').mkdir()
                raw = f'<main>Nadir Example <a href="{actual_target}">Example Lab</a></main>'
                (cache / 'responses' / (hashlib.sha256(url.encode()).hexdigest() + '.html')).write_text(raw)
                meta = {'status': 'ok', 'finalUrl': url, 'observedAt': '2026-01-01T00:00:00+00:00'}
                proof = {'requestedUrl': url, 'sourceUrl': url, 'observedAt': meta['observedAt'], 'bodySha256': hashlib.sha256(raw.encode()).hexdigest(),
                         'evidenceType': 'named_link', 'linkText': 'Example Lab', 'linkUrl': target, 'evidence': 'Example Lab -> ' + target}
                row['evidence'] = [proof]
                queue = {'items': {url: {'url': url, 'fetch': meta}}}
                if actual_target == target:
                    self.assertTrue(verified_reviews({'entries': [row]}, queue, cache)[0]['captureVerified'])
                else:
                    with self.assertRaises(ValueError):
                        verified_reviews({'entries': [row]}, queue, cache)


if __name__ == '__main__':
    unittest.main()
