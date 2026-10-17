import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_ucsd_preservation import audit


def dataset():
    proof = {'sourceUrl': 'https://example.ucsd.edu/person', 'observedAt': '2020-01-01',
             'method': 'official_identity', 'evidence': 'Jane Example'}
    return {'professors': [{'id': 'person', 'sourceUrls': [proof['sourceUrl']],
                             'fieldEvidence': {'name': [proof]},
                             'labAffiliations': [{'labId': 'old-lab', 'fieldEvidence': copy.deepcopy(proof)}]}],
            'labs': [{'id': 'old-lab', 'sourceUrls': [], 'professorIds': ['person']}]}


class PreservationAuditTests(unittest.TestCase):
    def test_baseline_survives_alias_merge_and_dated_field_history(self):
        old = dataset()
        current = copy.deepcopy(old)
        person = current['professors'][0]
        person['previousFieldObservations'] = [{'field': 'name', 'value': 'Jane Example',
                                                'fieldEvidence': person['fieldEvidence'].pop('name')}]
        lab = current['labs'][0]
        lab.update(id='canonical-lab', aliasIds=['old-lab'])
        person['labAffiliations'][0]['labId'] = 'canonical-lab'
        result = audit(old, current)
        self.assertEqual(result['status'], 'passed', result)
        self.assertEqual(result['counts']['aliasIds'], 1)

    def test_a_new_date_or_an_unrelated_person_cannot_replace_old_evidence(self):
        old = dataset()
        for mutation in ['date', 'identity', 'field']:
            with self.subTest(mutation=mutation):
                current = copy.deepcopy(old)
                person = current['professors'][0]
                if mutation == 'date':
                    person['fieldEvidence']['name'][0]['observedAt'] = '2026-01-01'
                elif mutation == 'identity':
                    current['professors'].append({'id': 'unrelated', 'fieldEvidence': person.pop('fieldEvidence')})
                else:
                    person['fieldEvidence']['email'] = person['fieldEvidence'].pop('name')
                result = audit(old, current)
                self.assertEqual(result['issueCounts']['lostEvidence'], 1)
                self.assertEqual(result['lostEvidence'][0]['observedAt'], '2020-01-01')

    def test_reasoned_whole_record_archive_preserves_isolated_lab_and_relationship(self):
        old = dataset()
        current = copy.deepcopy(old)
        removed = current['labs'].pop()
        links = current['professors'][0].pop('labAffiliations')
        archive = {'reason': 'Explicit non-lab review', 'record': removed,
                   'affectedProfessorObservations': [{'professorId': 'person', 'labAffiliations': links}]}
        self.assertEqual(audit(old, current, [[archive]])['status'], 'passed')
        archive.pop('reason')
        result = audit(old, current, [[archive]])
        self.assertEqual(result['issueCounts']['missingRecords'], 1)
        self.assertEqual(result['issueCounts']['lostRelationships'], 2)
        self.assertEqual(result['issueCounts']['lostEvidence'], 1)

    def test_alias_collision_fails_even_when_all_original_ids_and_evidence_exist(self):
        old = dataset()
        current = copy.deepcopy(old)
        current['labs'].append({'id': 'second-lab', 'aliasIds': ['old-lab']})
        result = audit(old, current)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['ambiguousAliasIds'], [{'id': 'old-lab', 'owners': ['old-lab', 'second-lab']}])

    def test_source_loss_and_relationship_loss_are_reported_separately(self):
        old = dataset()
        current = copy.deepcopy(old)
        current['professors'][0]['sourceUrls'] = []
        current['labs'][0]['professorIds'] = []
        result = audit(old, current)
        self.assertEqual(result['issueCounts']['lostSourceUrls'], 1)
        self.assertEqual(result['issueCounts']['lostRelationships'], 1)
        self.assertEqual(result['issueCounts']['lostEvidence'], 0)

    def test_partial_archive_cannot_substitute_for_a_whole_original_record(self):
        old = dataset()
        old['labs'][0]['description'] = 'An original retained value'
        current = copy.deepcopy(old)
        removed = current['labs'].pop()
        removed.pop('description')
        result = audit(old, current, [[{'reason': 'Review', 'record': removed}]])
        self.assertEqual(result['issueCounts']['missingRecords'], 1)

    def test_builder_refuses_to_overwrite_when_baseline_record_is_missing(self):
        from test_atlas_quality import atlas
        from rebuild_verified_atlas import build
        original, *_ = build(atlas(), {}, {}, {}, {})
        actual = copy.deepcopy(original)
        actual['professors'] = []
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            baseline, current, output = tmp / 'baseline.json', tmp / 'current.json', tmp / 'served.json'
            baseline.write_text(json.dumps(original))
            current.write_text(json.dumps(actual))
            output.write_text('preserve existing served bytes')
            result = subprocess.run([sys.executable, str(root / 'scripts/rebuild_verified_atlas.py'),
                                     '--atlas', str(current), '--evidence-dir', str(tmp / 'empty'),
                                     '--out', str(output), '--quality-dir', str(tmp / 'quality'),
                                     '--preservation-baseline', str(baseline)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Baseline preservation audit failed', result.stderr)
            self.assertEqual(output.read_text(), 'preserve existing served bytes')
            report = json.loads((tmp / 'quality/coverage-20261016-preservation.json').read_text())
            self.assertEqual(report['issueCounts']['missingRecords'], 1)

    def test_later_archive_snapshot_cannot_replace_an_older_observation_of_same_id(self):
        from rebuild_verified_atlas import combine_review_archive
        old = {'reason': 'Explicit review', 'record': {'id': 'legacy', 'fieldEvidence': {'name': [{'sourceUrl': 'https://a.ucsd.edu/', 'observedAt': '2020-01-01', 'evidence': 'Old name'}]}}}
        new = copy.deepcopy(old)
        new['record']['fieldEvidence']['name'][0].update(observedAt='2026-01-01', evidence='New name')
        combined = combine_review_archive([old], [new])
        self.assertEqual(combined, [old, new])
        self.assertEqual(combine_review_archive(combined, [new, old]), combined)


if __name__ == '__main__':
    unittest.main()
