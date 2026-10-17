import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from person_identity_reviews import verified_person_reviews, verify_person_proofs, apply_person_reviews
from lab_resource_reviews import record_sha256
from audit_ucsd_preservation import audit
from rebuild_verified_atlas import build
from test_atlas_quality import atlas, professor


class PersonIdentityReviewTests(unittest.TestCase):
    def fixture(self, cache):
        name, email = 'Jane Example', 'jane@ucsd.edu'
        target = professor('canonical', name, 'Unproved legacy department')
        source = professor('retired', name, 'Mathematics')
        proofs, identifiers, items = [], [], {}
        for person, url in [(target, 'https://math.ucsd.edu/jane'), (source, 'https://www.math.ucsd.edu/jane')]:
            raw = f'<title>{name} | Department of Mathematics</title><main><h1>{name}</h1>Email: {email}</main>'.encode()
            (cache / 'responses').mkdir(exist_ok=True)
            (cache / 'responses' / (hashlib.sha256(url.encode()).hexdigest() + '.html')).write_bytes(raw)
            meta = {'sourceUrl': url, 'finalUrl': url, 'status': 'ok', 'observedAt': '2026-01-01T00:00:00+00:00'}
            items[url] = {'url': url, 'fetch': meta}
            common = {'requestedUrl': url, 'sourceUrl': url, 'observedAt': meta['observedAt'], 'bodySha256': hashlib.sha256(raw).hexdigest()}
            title = {**common, 'evidenceType': 'document_title', 'evidence': name + ' | Department of Mathematics'}
            contact = {**common, 'evidenceType': 'main_text_quote', 'evidence': 'Email: ' + email}
            proofs.extend([title, contact]); identifiers.append({'nameEvidence': title, 'identifierEvidence': contact})
            person.update(email=email, officialProfileUrl=url, personalWebsiteUrl='Not found', sourceUrls=[url],
                          fieldEvidence={'email': [{'sourceUrl': url, 'observedAt': '2020-01-01', 'evidence': email}]})
        data = atlas(); data.update(qualityMigrationVersion=1, professors=[target, source])
        row = {'action': 'merge', 'name': name, 'sourceProfessorId': source['id'], 'targetProfessorId': target['id'],
               'originalSourceRecord': copy.deepcopy(source), 'originalTargetRecord': copy.deepcopy(target),
               'sourceRecordSha256': record_sha256(source), 'targetRecordSha256': record_sha256(target),
               'identityBasis': {'type': 'shared_public_email', 'value': email}, 'identitySources': identifiers,
               'fields': {'department': 'Mathematics', 'officialProfileUrl': target['officialProfileUrl']},
               'fieldEvidence': {'department': [proofs[0]], 'officialProfileUrl': [proofs[0]]},
               'departmentEvidence': [{'department': 'Mathematics', 'fieldEvidence': [proofs[0], proofs[2]], 'status': 'as_listed'}],
               'unsupportedDepartmentValues': ['Unproved legacy department'], 'evidence': proofs,
               'reason': 'Two independently captured named individual profiles share the same unique professional contact.'}
        return data, {'items': items}, row

    def test_source_id_whole_record_conflict_and_evidence_survive_department_correction(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, queue, row = self.fixture(Path(tmp)); baseline = copy.deepcopy(data)
            rows = verified_person_reviews({'entries': [row]}, queue, Path(tmp), baseline)
            removed = apply_person_reviews(data, rows)
            self.assertEqual(data['professors'][0]['id'], 'canonical')
            self.assertEqual(data['professors'][0]['aliasIds'], ['retired'])
            self.assertEqual(data['professors'][0]['department'], 'Mathematics')
            self.assertEqual(removed[0]['record'], baseline['professors'][1])
            self.assertTrue(any(o.get('value') == 'Unproved legacy department' for o in data['professors'][0]['previousFieldObservations']))
            self.assertEqual(audit(baseline, data, [removed])['status'], 'passed')
            first = copy.deepcopy(data)
            self.assertEqual(apply_person_reviews(data, rows), [])
            self.assertEqual(first, data)

    def test_shared_department_mailbox_or_changed_original_record_cannot_merge_people(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, queue, row = self.fixture(Path(tmp))
            unrelated = professor('another', 'Another Person'); unrelated['email'] = 'jane@ucsd.edu'
            data['professors'].append(unrelated)
            with self.assertRaisesRegex(ValueError, 'department contacts'):
                verified_person_reviews({'entries': [row]}, queue, Path(tmp), data)
            data['professors'].pop(); row['originalSourceRecord']['email'] = 'changed@ucsd.edu'
            with self.assertRaisesRegex(ValueError, 'unchanged full'):
                verified_person_reviews({'entries': [row]}, queue, Path(tmp), data)

    def test_newer_retired_id_observation_cannot_reverse_verified_canonical_resource_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,q,row=self.fixture(cache)
            reviews=verified_person_reviews({'entries':[row]},q,cache,data)
            source=data['professors'][1]
            fresh={'sourceUrl':source['officialProfileUrl'],'observedAt':'2026-02-01T00:00:00+00:00',
                   'method':'official_profile_heading_identity','evidence':source['name']}
            source['fieldEvidence']['officialProfileUrl']=[fresh]
            captured={'byProfessorId':{'retired':{'officialProfileUrl':source['officialProfileUrl'],
                       'fieldEvidence':{'officialProfileUrl':[fresh]}}},'personIdentityReviews':reviews}
            first,*_=build(copy.deepcopy(data),{},{},{},{},{},{},{},copy.deepcopy(captured))
            person=first['professors'][0]
            self.assertEqual(person['officialProfileUrl'],row['fields']['officialProfileUrl'])
            self.assertTrue(any(o.get('field')=='officialProfileUrl' and o.get('value')==source['officialProfileUrl']
                                and fresh in o.get('fieldEvidence',[]) for o in person['previousFieldObservations']))
            repeated,*_=build(copy.deepcopy(first),{},{},{},{},{},{},{},copy.deepcopy(captured))
            self.assertEqual(first,repeated)

    def test_matching_email_on_a_different_named_page_is_not_a_person_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache)
            uri = row['identitySources'][1]['nameEvidence']['requestedUrl']
            path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
            raw = b'<title>Another Person</title><main>Email: jane@ucsd.edu</main>'; path.write_bytes(raw)
            for p in row['evidence']:
                if p['requestedUrl'] == uri:
                    p['bodySha256'] = hashlib.sha256(raw).hexdigest()
                    if p['evidenceType'] == 'document_title': p['evidence'] = 'Another Person'
            with self.assertRaisesRegex(ValueError, 'subject'):
                verified_person_reviews({'entries': [row]}, queue, cache, data)

    def test_json_record_requires_exact_raw_bytes_date_pointer_and_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache)
            uri = 'https://physics.ucsd.edu/api/faculty'; value = {'first_name': 'Jane', 'last_name': 'Example', 'email': 'jane@ucsd.edu'}
            raw = (json.dumps([value]) + '\r\n').encode(); path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html'); path.write_bytes(raw)
            queue['items'][uri] = {'url': uri, 'fetch': {'sourceUrl': uri, 'finalUrl': uri, 'status': 'ok', 'observedAt': '2026-01-01'}}
            proof = {'requestedUrl': uri, 'sourceUrl': uri, 'observedAt': '2026-01-01', 'bodySha256': hashlib.sha256(raw).hexdigest(),
                     'evidenceType': 'json_record', 'sourceJsonPointer': '/0', 'sourceRecord': value, 'evidence': json.dumps(value, ensure_ascii=False, sort_keys=True)}
            verify_person_proofs([proof], queue, cache, 'Jane Example')
            for field, wrong in [('sourceJsonPointer', '/1'), ('sourceJsonPointer', '/-1'), ('sourceJsonPointer', '/00'), ('observedAt', '2020-01-01'), ('bodySha256', 'changed'), ('sourceRecord', {'first_name': 'Different'}), ('evidence', 'Jane Example | invented caption')]:
                with self.subTest(field=field), self.assertRaises(ValueError):
                    verify_person_proofs([{**proof, field: wrong}], queue, cache, 'Jane Example')

    def test_failed_later_review_and_cycles_cannot_partially_mutate_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, queue, row = self.fixture(Path(tmp)); rows = verified_person_reviews({'entries': [row]}, queue, Path(tmp), data)
            before = copy.deepcopy(data)
            with self.assertRaises(ValueError): apply_person_reviews(data, rows + [{**rows[0], 'sourceProfessorId': 'missing', 'captureVerified': False}])
            self.assertEqual(before, data)
            with self.assertRaisesRegex(ValueError, 'acyclic'):
                apply_person_reviews(data, rows + [{**rows[0], 'sourceProfessorId': 'canonical', 'targetProfessorId': 'retired'}])
            self.assertEqual(before, data)

    def test_first_build_collects_all_alias_courses_and_replaying_alias_patches_is_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, queue, row = self.fixture(Path(tmp)); rows = verified_person_reviews({'entries': [row]}, queue, Path(tmp), data)
            def course(code):
                return {'courseCode': code, 'term': 'Fall 2025', 'sourceUrl': 'https://courses.ucsd.edu/', 'observedAt': '2025-10-01', 'evidence': code + ' | Jane Example'}
            teaching = {'generatedAt': '2026-01-01', 'byProfessorId': {'canonical': [course('CSE 101')], 'retired': [course('MATH 101')]}}
            captured = {'byProfessorId': {'retired': {'researchSummary': 'Research in geometry.', 'fieldEvidence': {'researchSummary': row['evidence'][:1]}}}}
            first, *_ = build(copy.deepcopy(data), captured, teaching, {}, {}, coverage_evidence={'personIdentityReviews': rows})
            self.assertEqual([c['courseCode'] for c in first['professors'][0]['teaching']['courses']], ['CSE 101', 'MATH 101'])
            second, *_ = build(copy.deepcopy(first), captured, teaching, {}, {}, coverage_evidence={'personIdentityReviews': rows})
            self.assertEqual(first, second)

    def test_lab_foreign_keys_are_remapped_with_their_original_relationships_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, queue, row = self.fixture(Path(tmp)); rows = verified_person_reviews({'entries': [row]}, queue, Path(tmp), data)
            data['labs'] = [{'id': 'lab', 'professorIds': ['retired', 'canonical']}]
            before = copy.deepcopy(data); removed = apply_person_reviews(data, rows)
            self.assertEqual(data['labs'][0]['professorIds'], ['canonical'])
            self.assertEqual(data['labs'][0]['previousFieldObservations'][0]['value'], ['retired', 'canonical'])
            self.assertEqual(audit(before, data, [removed])['status'], 'passed')

    def test_person_identity_does_not_assign_one_rating_profiles_proof_to_another_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, queue, row = self.fixture(Path(tmp)); rows = verified_person_reviews({'entries': [row]}, queue, Path(tmp), data)
            for person, score in zip(data['professors'], [3.5, 4.5]):
                uri = 'https://ratings.example/' + person['id']
                person['ratings'] = {'rateMyProfessors': {'status': 'verified', 'score': score, 'sourceUrl': uri}}
                person['fieldEvidence']['ratings.rateMyProfessors'] = [{'sourceUrl': uri, 'observedAt': '2020-01-01', 'evidence': str(score)}]
                person['sourceUrls'].append(uri)
            before = copy.deepcopy(data); archive = apply_person_reviews(data, rows); person = data['professors'][0]
            self.assertEqual(person['ratings']['rateMyProfessors']['score'], 3.5)
            self.assertEqual(person['fieldEvidence']['ratings.rateMyProfessors'], before['professors'][0]['fieldEvidence']['ratings.rateMyProfessors'])
            self.assertEqual(archive[0]['record']['ratings']['rateMyProfessors']['score'], 4.5)
            self.assertEqual(audit(before, data, [archive])['status'], 'passed')
