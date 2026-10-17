import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lab_entities import LabIndex
from rebuild_verified_atlas import build, consolidate_lab_urls, merge_patch
from refresh_labs import make_lab
from validate_data import validate_references
import apply_ucsd_coverage as apply


URL = 'https://example-lab.ucsd.edu/'
TEXT = 'Example Lab A and Example Lab B are two distinct laboratories at UC San Diego.'
PROOF = {'sourceUrl': URL, 'observedAt': '2026-10-01T00:00:00+00:00', 'method': 'reviewed_distinct_named_labs', 'evidence': TEXT}


def labs():
    sharing = {'kind': 'distinct_named_labs', 'groupId': 'example-labs', 'memberLabIds': ['lab-a', 'lab-b'], 'evidence': [PROOF]}
    result = []
    for rid, name in [('lab-a', 'Example Lab A'), ('lab-b', 'Example Lab B')]:
        record = make_lab(name, URL, 'Unknown', {'sourceUrl': URL, 'finalUrl': URL, 'observedAt': PROOF['observedAt']}, TEXT)
        record.update(id=rid, websiteSharing=copy.deepcopy(sharing))
        record['fieldEvidence'] = {field: value if isinstance(value, list) else [value] for field, value in record['fieldEvidence'].items()}
        record['fieldEvidence']['websiteSharing'] = copy.deepcopy(sharing['evidence'])
        result.append(record)
    return result


class SharedLabEntityTests(unittest.TestCase):
    def test_shared_url_needs_identity_or_exact_name_to_resolve(self):
        records = labs()
        index = LabIndex(records)
        index.validate_sharing()
        self.assertIsNone(index.resolve(URL))
        self.assertIsNone(index.resolve(URL, name='Lab'))
        self.assertEqual(index.resolve(URL, name='Example Lab B')['id'], 'lab-b')
        self.assertEqual(index.resolve(URL, lab_id='lab-a')['id'], 'lab-a')
        self.assertIsNone(index.resolve(URL, lab_id='unknown'))
        self.assertEqual([len(g) for g in index.url_groups()[0]], [2])
        self.assertEqual(index.url_groups()[1], [])

    def test_shared_review_must_be_complete_consistent_and_distinct(self):
        for mode in ['missing-member', 'inconsistent', 'same-name', 'no-proofs', 'wrong-members']:
            records = labs()
            if mode == 'missing-member':
                records.pop()
            elif mode == 'inconsistent':
                records[1]['websiteSharing']['groupId'] = 'different'
            elif mode == 'same-name':
                records[1]['labName'] = records[0]['labName']
            elif mode == 'no-proofs':
                for record in records:
                    record['websiteSharing']['evidence'] = []
            else:
                for record in records:
                    record['websiteSharing']['memberLabIds'] = ['lab-a', 'unrelated']
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'shared website group'):
                LabIndex(records).validate_sharing()

    def test_unreviewed_url_duplicates_are_still_detected(self):
        records = labs()
        for record in records:
            record.pop('websiteSharing')
        self.assertEqual(len(LabIndex(records).url_groups()[1]), 1)
        data = {'labs': records}
        removed = consolidate_lab_urls(data)
        self.assertEqual(len(data['labs']), 2, 'different named entities cannot merge from a shared URI alone')
        self.assertEqual(removed, [])
        self.assertEqual(len(LabIndex(data['labs']).url_groups()[1]), 1)

    def test_reindex_does_not_preserve_an_unreviewed_retired_url(self):
        record = labs()[0]
        record.pop('websiteSharing')
        index = LabIndex([record])
        record['labWebsiteUrl'] = 'https://new-example.ucsd.edu/'
        index.add(record)
        self.assertIsNone(index.resolve(URL))
        self.assertEqual(index.resolve(record['labWebsiteUrl'])['id'], record['id'])

    def test_two_relationships_on_one_url_survive_patch_merge(self):
        record = {'id': 'p', 'fieldEvidence': {}, 'sourceUrls': [], 'labAffiliations': []}
        for lab in labs():
            merge_patch(record, {'labAffiliations': [{'labId': lab['id'], 'labName': lab['labName'], 'url': URL, 'fieldEvidence': PROOF}], 'fieldEvidence': {}})
        self.assertEqual({r['labId'] for r in record['labAffiliations']}, {'lab-a', 'lab-b'})

    def test_unique_resource_merges_preserve_capture_id_as_resolvable_alias(self):
        from test_atlas_quality import atlas
        data = atlas()
        original = labs()[0]
        original.pop('websiteSharing')
        original['fieldEvidence'].pop('websiteSharing')
        data['labs'] = [original]
        capture = copy.deepcopy(original)
        capture['id'] = 'capture-side-lab-id'
        proof = {'labId': capture['id'], 'labName': original['labName'], 'url': URL, 'fieldEvidence': PROOF}
        first, *_ = build(data, {'labs': [capture], 'byProfessorId': {'p': {'labAffiliations': [proof]}}}, {}, {}, {})
        self.assertIn(capture['id'], first['labs'][0]['aliasIds'])
        self.assertEqual(first['professors'][0]['labAffiliations'][0]['labId'], original['id'])
        validate_references(first)

    def test_profile_candidate_id_cannot_select_one_shared_lab(self):
        index = LabIndex(labs())
        for label, expected in [('Lab website', None), ('Example Lab B', 'lab-b')]:
            original = {'labAffiliations': [{'labId': 'lab-a', 'labName': label, 'url': URL, 'fieldEvidence': PROOF}],
                        'labAffiliation': label, 'labAffiliationUrl': URL, 'fieldEvidence': {}}
            result = apply.resolve_profile_lab_links(original, index)
            if expected:
                self.assertEqual(result['labAffiliations'][0]['labId'], expected)
            else:
                self.assertEqual(result['labAffiliations'], [])
                self.assertNotIn('labAffiliationUrl', result)
                self.assertEqual(result['unresolvedLabLinks'][0]['fieldEvidence'], PROOF)
                target = {'id': 'p', 'fieldEvidence': {}, 'sourceUrls': []}
                merge_patch(target, result)
                self.assertEqual(target['unresolvedLabLinks'], result['unresolvedLabLinks'])

    def test_full_build_keeps_both_entities_and_ambiguous_link_evidence(self):
        from test_atlas_quality import atlas
        data = atlas()
        evidence = {'generatedAt': PROOF['observedAt'], 'labs': labs(), 'byProfessorId': {'p': {
            'labAffiliations': [{'labName': 'Lab website', 'url': URL, 'fieldEvidence': PROOF}], 'fieldEvidence': {}}}}
        first, *_ = build(data, {}, {}, {}, {}, coverage_evidence=copy.deepcopy(evidence))
        self.assertEqual({r['id'] for r in first['labs']}, {'lab-a', 'lab-b'})
        self.assertEqual(first['professors'][0]['labAffiliations'], [])
        self.assertEqual(first['professors'][0]['unresolvedLabLinks'][0]['fieldEvidence'], PROOF)
        validate_references(first)
        second, *_ = build(copy.deepcopy(first), {}, {}, {}, {}, coverage_evidence=copy.deepcopy(evidence))
        self.assertEqual(first, second)
        self.assertEqual(first['dataQuality']['coverage']['duplicateLabUrlGroups'], 0)
        self.assertEqual(first['dataQuality']['coverage']['reviewedSharedLabWebsiteGroups'], 1)

    def test_handoff_verifies_actual_shared_identity_text_and_hash(self):
        from test_reviewed_handoff import ReviewedHandoffTests
        for tamper in [None, 'text', 'bytes']:
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as tmp:
                root, cache, decisions, proposal = ReviewedHandoffTests().fixture(tmp)
                body = '<main>' + TEXT + '</main>'
                path = cache / 'responses' / (hashlib.sha256(URL.encode()).hexdigest() + '.html')
                path.write_text(body)
                queue = json.loads((cache / 'queue.json').read_text())
                queue['items'][URL]['fetch']['sha256'] = hashlib.sha256(body.encode()).hexdigest()
                (cache / 'queue.json').write_text(json.dumps(queue))
                proof = copy.deepcopy(PROOF)
                if tamper == 'text':
                    proof['evidence'] += ' Fabricated distinction.'
                if tamper == 'bytes':
                    path.write_text(body + ' altered')
                entities = [{'stableLabId': lab['id'], 'name': lab['labName'], 'identityEvidence': [PROOF],
                             'reason': 'Explicitly separately named labs', 'departmentUnresolvedReason': 'No department stated'} for lab in labs()]
                decisions.write_text(json.dumps({'labs': {URL: {'action': 'accept_shared_entities', 'sharedEntities': entities,
                    'sharingGroupId': 'example-labs', 'sharingEvidence': [proof]}}}))
                output = root / 'handoff.json'
                with patch.object(apply, 'ROOT', root), patch.object(apply, 'prepare', return_value=[proposal]):
                    if tamper:
                        with self.assertRaisesRegex(ValueError, 'dated capture'):
                            apply.export_reviewed_lab_handoff(cache, decisions, output)
                        self.assertFalse(output.exists())
                    else:
                        apply.export_reviewed_lab_handoff(cache, decisions, output)
                        handoff = json.loads(output.read_text())
                        self.assertEqual({lab['id'] for lab in handoff['labs']}, {'lab-a', 'lab-b'})
                        self.assertEqual(len(handoff['sourceManifest']), 1)
