import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from professor_own_field_reviews import math_own_fields, verified_professor_fields, apply_professor_fields
from lab_resource_reviews import record_sha256
from refresh_labs import DOM
from test_atlas_quality import professor


class ProfessorOwnFieldTests(unittest.TestCase):
    def fixture(self, cache):
        uri = 'https://math.ucsd.edu/people/profiles/jane-example'
        raw = '''<html><head><title>Jane A. Example | Department of Mathematics</title></head><body>
        <aside><div class="block-page-title-block" id="block-bootstrap-math-page-title"><h1 class="title">Jane A. Example</h1></div>
        <p>Research Areas</p><a class="badge">Unrelated sidebar term</a></aside>
        <main><div class="row"><div class="col-sm-3"><div class="mt-3"><p>Research Areas</p>
        <a class="badge">Algebra</a><span class="badge">Groups</span></div>
        <p><strong>Email:</strong><span id="person_email">jexample@ucsd.edu</span></p></div>
        <div class="col-sm-9"><h4 id="profile_full_name"></h4><p id="person_titles"></p>
        <p>Biography: Another Person researches Topology.</p></div></div></main>
        <footer><p>Research Areas</p><a class="badge">Unrelated footer term</a></footer></body></html>'''
        path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
        path.parent.mkdir(); path.write_text(raw)
        item = {'url': uri, 'state': 'done', 'fetch': {'sourceUrl': uri, 'finalUrl': uri, 'status': 'ok',
                'observedAt': '2026-10-16T05:00:00+00:00', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}}
        person = professor('unchanged-id', 'Jane A. Example', 'Mathematics')
        person['officialProfileUrl'] = uri
        return item, path, person

    def revise(self, item, path, old, new):
        path.write_text(path.read_text().replace(old, new))
        item['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()

    def review(self, item, cache, person, target=None):
        observation = math_own_fields(item, cache, person['name'])
        return {'professorId': target or person['id'], 'sourceProfessorId': person['id'],
                'originalSourceProfessorRecord': copy.deepcopy(person), 'originalSourceRecordSha256': record_sha256(person),
                'reason': 'Read explicitly labelled fields on the unchanged original own source.',
                'sourceObservation': observation, 'fields': observation['fields'], 'fieldEvidence': observation['fieldEvidence']}

    def test_scoped_aside_title_with_main_fields_keeps_exact_receipt_and_excludes_other_people(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, path, person = self.fixture(cache); before = copy.deepcopy(item)
            self.assertFalse(any(n.tag == 'h1' for n in DOM(path.read_text()).main().walk()))
            result = math_own_fields(item, cache, person['name'])
            self.assertEqual(result['fields'], {'researchAreas': ['Algebra', 'Groups'], 'email': 'jexample@ucsd.edu'})
            for proofs in result['fieldEvidence'].values():
                proof = proofs[0]
                self.assertEqual(proof['requestedUrl'], item['url'])
                self.assertEqual(proof['observedAt'], item['fetch']['observedAt'])
                self.assertEqual(proof['bodySha256'], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(item, before)

    def test_wrong_conflicting_missing_subjects_and_ambiguous_template_fail_closed(self):
        changes = [('Jane A. Example | Department', 'Another Person | Department'),
                   ('<h1 class="title">Jane A. Example</h1>', '<h1 class="title">Another Person</h1>'),
                   ('<h1 class="title">Jane A. Example</h1>', '<h1 class="title">Jane A. Example</h1><h1 class="title">Another Person</h1>'),
                   ('id="block-bootstrap-math-page-title"', 'id="other-title"'),
                   ('id="profile_full_name"></h4>', 'id="profile_full_name">Another Person</h4>'),
                   ('class="row"', 'class="unrelated"'),
                   ('id="person_titles"', 'id="other-roles"')]
        for old, new in changes:
            with self.subTest(old=old), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, path, person = self.fixture(cache); self.revise(item, path, old, new)
                with self.assertRaises(ValueError): math_own_fields(item, cache, person['name'])
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, _, _ = self.fixture(cache)
            with self.assertRaises(ValueError): math_own_fields(item, cache, 'J. Example')

    def test_immutable_actual_bytes_individual_uri_and_own_host_are_required(self):
        for mode in ['bytes', 'missing', 'failure', 'foreign', 'generic']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, path, person = self.fixture(cache)
                if mode == 'bytes': path.write_text(path.read_text() + 'changed')
                if mode == 'missing': path.unlink()
                if mode == 'failure': item['fetch']['status'] = 'error'
                if mode == 'foreign': item['fetch']['finalUrl'] = 'https://other.ucsd.edu/people/profiles/jane-example'
                if mode == 'generic': item['fetch']['finalUrl'] = 'https://math.ucsd.edu/people/'
                with self.assertRaises(ValueError): math_own_fields(item, cache, person['name'])

    def test_unlabelled_empty_and_placeholder_values_never_clear_existing_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, path, person = self.fixture(cache)
            self.revise(item, path, '<a class="badge">Algebra</a><span class="badge">Groups</span>', '<span class="badge">Coming soon</span>')
            self.revise(item, path, 'jexample@ucsd.edu', '')
            self.assertEqual(math_own_fields(item, cache, person['name'])['fields'], {})
            row = self.review(item, cache, person)
            with self.assertRaises(ValueError): verified_professor_fields({'entries': [row]}, {'items': {'x': item}}, cache, [person])
            self.assertEqual(person['researchAreas'], ['Cryptography'])

    def test_duplicate_labels_and_nonbadge_research_text_require_review(self):
        for old, new in [('<p>Research Areas</p>\n', '<p>Research Areas</p><p>Research Areas</p>\n'),
                         ('<span class="badge">Groups</span>', '<span>Groups</span>'),
                         ('<span id="person_email">jexample@ucsd.edu</span>', '<span id="person_email">jexample@ucsd.edu</span><span id="person_email">other@ucsd.edu</span>')]:
            with self.subTest(new=new), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, path, person = self.fixture(cache); self.revise(item, path, old, new)
                with self.assertRaises(ValueError): math_own_fields(item, cache, person['name'])

    def test_unchanged_full_record_and_exact_values_and_proofs_are_verified_again(self):
        for mode in ['target', 'snapshot', 'value', 'proof', 'duplicate', 'owner']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, _, person = self.fixture(cache); row = self.review(item, cache, person); rows = [row]; people = [person]
                if mode == 'target': row['professorId'] = 'other'
                if mode == 'snapshot':
                    row['originalSourceProfessorRecord']['email'] = 'invented@ucsd.edu'
                    row['originalSourceRecordSha256'] = record_sha256(row['originalSourceProfessorRecord'])
                if mode == 'value': row['fields'] = {'researchAreas': ['Invented']}
                if mode == 'proof': row['fieldEvidence'] = {}
                if mode == 'duplicate': rows.append(copy.deepcopy(row))
                if mode == 'owner': people.append({**copy.deepcopy(person), 'id': 'other'})
                with self.assertRaises(ValueError): verified_professor_fields({'entries': rows}, {'items': {'x': item}}, cache, people)

    def test_verified_alias_is_required_and_application_preserves_identity_and_old_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, _, source = self.fixture(cache)
            target = {**copy.deepcopy(source), 'id': 'retained-id'}
            row = self.review(item, cache, source, target['id']); q = {'items': {'x': item}}
            merge = {'sourceProfessorId': source['id'], 'targetProfessorId': target['id'], 'captureVerified': True}
            with self.assertRaises(ValueError): verified_professor_fields({'entries': [row]}, q, cache, [source, target])
            with self.assertRaises(ValueError): verified_professor_fields({'entries': [row]}, q, cache, [source, target], [{**merge, 'captureVerified': False}])
            verified = verified_professor_fields({'entries': [row]}, q, cache, [source, target], [merge])
            target['aliasIds'] = [source['id']]
            target['fieldEvidence'] = {'researchAreas': [{'sourceUrl': 'https://math.ucsd.edu/older', 'observedAt': '2020-01-01', 'evidence': 'Cryptography'}]}
            data = {'professors': [target]}; before = copy.deepcopy(target)
            apply_professor_fields(data, verified)
            for key in ['id', 'name', 'officialProfileUrl', 'department', 'recruitingStatus', 'lastVerified']:
                self.assertEqual(target[key], before[key])
            self.assertEqual(target['researchAreas'], ['Algebra', 'Groups'])
            self.assertIn({'field': 'researchAreas', 'value': ['Cryptography'], 'fieldEvidence': before['fieldEvidence']['researchAreas']}, target['previousFieldObservations'])
            first = copy.deepcopy(data); apply_professor_fields(data, verified); self.assertEqual(data, first)
            with self.assertRaises(ValueError): apply_professor_fields({'professors': [source, {**target, 'aliasIds': []}]}, verified)

    def test_older_observation_remains_inspectable_without_replacing_newer_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, _, person = self.fixture(cache)
            row = self.review(item, cache, person)
            verified = verified_professor_fields({'entries': [row]}, {'items': {'x': item}}, cache, [person])
            person['researchAreas'] = ['Newer observation']
            person['fieldEvidence'] = {'researchAreas': [{'sourceUrl': 'https://math.ucsd.edu/newer', 'observedAt': '2026-10-17T00:00:00+00:00'}]}
            apply_professor_fields({'professors': [person]}, verified)
            self.assertEqual(person['researchAreas'], ['Newer observation'])
            self.assertEqual(person['professorFieldReviews'][0]['fields']['researchAreas'], ['Algebra', 'Groups'])


if __name__ == '__main__': unittest.main()
