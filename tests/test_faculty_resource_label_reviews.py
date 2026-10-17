import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from faculty_resource_label_reviews import KIND, resource_label_binding
from person_identity_reviews import verified_person_reviews, apply_person_reviews
from lab_resource_reviews import record_sha256
from audit_ucsd_preservation import audit
from rebuild_verified_atlas import build
from test_atlas_quality import atlas, professor


class FacultyResourceLabelReviewTests(unittest.TestCase):
    def fixture(self, cache):
        target = professor('canonical', 'Jane Example', 'Bioengineering')
        source = professor('misparsed', 'Example Research', 'Bioengineering')
        roster_uri = 'http://be.ucsd.edu/faculty'
        target_uri = 'https://jacobsschool.ucsd.edu/faculty/profile?id=123'
        own_uri = 'http://profiles.ucsd.edu/jane.example'
        source.update(officialProfileUrl=own_uri, sourceUrls=[own_uri, roster_uri])
        target.update(officialProfileUrl=target_uri, sourceUrls=[target_uri, roster_uri])
        card = f'<div class="faculty-profile"><div class="faculty-information"><h3><a href="{target_uri}">Jane Example</a></h3><h6>Associate Professor<h6><a href="{own_uri}">Example Research</a></h6></h6></div></div>'
        roster = f'<main><h1>Faculty Profiles</h1>{card}</main>'
        own = '<html><head><title>Jane Example | UCSD Profiles</title><link rel="canonical" href="https://profiles.ucsd.edu/jane.example"><link rel="alternate" type="application/rdf+xml" href="https://researcherprofiles.org/profile/123/123.rdf"></head><body><main><div class="pageTitle"><h2>Jane Example</h2></div></main></body></html>'
        queue = {'items': {}}
        (cache / 'responses').mkdir()
        for uri, body, final in [(roster_uri, roster, 'https://be.ucsd.edu/faculty'), (own_uri, own, 'https://profiles.ucsd.edu/jane.example')]:
            raw = body.encode(); (cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')).write_bytes(raw)
            meta = {'status': 'ok', 'sourceUrl': uri, 'finalUrl': final, 'observedAt': '2026-01-01', 'sha256': hashlib.sha256(raw).hexdigest()}
            queue['items'][uri] = {'url': uri, 'fetch': meta}
        binding = resource_label_binding(source, target, queue['items'][roster_uri], queue['items'][own_uri], cache, [target, source])
        base = binding['roster']
        common = {k: base[k] for k in ['requestedUrl', 'sourceUrl', 'observedAt', 'bodySha256']}
        proofs = [{**common, 'evidenceType': 'named_link', 'linkText': label, 'linkUrl': uri, 'evidence': label + ' -> ' + uri}
                  for label, uri in [(target['name'], target_uri), (source['name'], own_uri)]]
        common = {k: binding['ownProfile'][k] for k in ['requestedUrl', 'sourceUrl', 'observedAt', 'bodySha256']}
        proofs.append({**common, 'evidenceType': 'document_title', 'evidence': 'Jane Example | UCSD Profiles'})
        row = {'action': 'merge', 'name': target['name'], 'sourceProfessorId': source['id'], 'targetProfessorId': target['id'],
               'originalSourceRecord': copy.deepcopy(source), 'originalTargetRecord': copy.deepcopy(target),
               'sourceRecordSha256': record_sha256(source), 'targetRecordSha256': record_sha256(target),
               'identityBasis': {'type': KIND, 'value': own_uri}, 'resourceLabelBinding': binding,
               'fields': {'department': target['department'], 'officialProfileUrl': target_uri},
               'fieldEvidence': {field: proofs[:1] for field in ['department', 'officialProfileUrl']},
               'departmentEvidence': [{'department': target['department'], 'fieldEvidence': proofs[:1], 'status': 'as_listed'}],
               'evidence': proofs, 'reason': 'The retained secondary research link was parsed as a separate person; the original named faculty card and its own linked personal subject identify the existing target.'}
        data = atlas(); data.update(professors=[target, source], qualityMigrationVersion=1)
        return data, queue, row

    def test_label_resolves_to_existing_person_with_whole_history_and_repeat_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache); before = copy.deepcopy(data)
            previous = copy.deepcopy(data['professors'][1]); previous['verification'] = {'issues': [], 'fieldsVerified': []}
            row['previousCandidateObservation'] = {'candidateAtlasSha256': 'a' * 64, 'recordSha256': record_sha256(previous), 'record': previous}
            reviews = verified_person_reviews({'entries': [row]}, queue, cache, before)
            archive = apply_person_reviews(data, reviews)
            self.assertEqual(len(data['professors']), 1)
            target = data['professors'][0]
            self.assertEqual(target['aliasIds'], ['misparsed'])
            for field in ['name', 'department', 'officialProfileUrl']:
                self.assertEqual(target[field], before['professors'][0][field])
            self.assertNotIn('Example Research', target.get('aliasNames', []))
            self.assertEqual(archive[0]['record'], before['professors'][1])
            self.assertTrue(any(o.get('field') == 'misparsedResourcePreviousCandidate' and o['value'] == previous
                                for o in target['previousFieldObservations']))
            self.assertEqual(audit(before, data, [archive])['status'], 'passed')
            first = copy.deepcopy(data); self.assertEqual(apply_person_reviews(data, reviews), []); self.assertEqual(data, first)

    def test_same_uri_or_page_wide_links_without_scoped_card_cannot_resolve_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache)
            uri = row['resourceLabelBinding']['roster']['requestedUrl']
            path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html'); original = path.read_text()
            variants = [original.replace('faculty-profile', 'unscoped-container'), original.replace('<main>', '<nav>').replace('</main>', '</nav>'),
                        original.replace('>Jane Example</a>', '>Another Example</a>'),
                        original.replace('id=123', 'id=124'), original.replace('http://profiles.ucsd.edu/jane.example', 'https://profiles.ucsd.edu/jane.example'),
                        original.replace('</h3>', '</h3><h3>Another Person</h3>'), original.replace('Associate Professor', 'Staff Scientist'),
                        original.replace('>Example Research</a>', '>Research Website</a>')]
            for raw in variants:
                with self.subTest(raw=raw):
                    path.write_text(raw); state = copy.deepcopy(queue); state['items'][uri]['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                    with self.assertRaises(ValueError):
                        resource_label_binding(data['professors'][1], data['professors'][0], state['items'][uri], state['items'][data['professors'][1]['officialProfileUrl']], cache, data['professors'])

    def test_conflicts_or_changed_review_cannot_authorize_a_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache)
            mutations = [lambda r: r['resourceLabelBinding']['roster'].update(observedAt='2020-01-01'),
                         lambda r: r['resourceLabelBinding']['ownProfile'].update(nameAsDisplayed='Another Person'),
                         lambda r: r['fields'].update(department='Medicine'),
                         lambda r: r.update(identityBasis={'type': 'shared_personal_website', 'value': data['professors'][1]['officialProfileUrl']}),
                         lambda r: r.update(evidence=r['evidence'][1:]),
                         lambda r: r.update(previousCandidateObservation={'candidateAtlasSha256': 'a' * 64, 'recordSha256': 'changed', 'record': data['professors'][1]}),
                         lambda r: r.update(previousCandidateObservation={'candidateAtlasSha256': 'a' * 64, 'recordSha256': record_sha256(data['professors'][0]), 'record': data['professors'][0]}),
                         lambda r: r['originalSourceRecord'].update(name='Jane Example')]
            for mutate in mutations:
                r = copy.deepcopy(row); mutate(r)
                with self.subTest(row=r), self.assertRaises(ValueError): verified_person_reviews({'entries': [r]}, queue, cache, data)
            competing = copy.deepcopy(data); rival = copy.deepcopy(data['professors'][0]); rival['id'] = 'rival'; competing['professors'].append(rival)
            with self.assertRaisesRegex(ValueError, 'competing'):
                verified_person_reviews({'entries': [row]}, queue, cache, competing)

    def test_wrong_own_subject_or_tampered_original_capture_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache)
            uri = data['professors'][1]['officialProfileUrl']
            path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html'); original = path.read_bytes()
            for mode in ['different_subject', 'missing_personal_identifier', 'tampered_bytes', 'tampered_observation_date']:
                state = copy.deepcopy(queue); path.write_bytes(original)
                if mode == 'different_subject':
                    path.write_bytes(original.replace(b'Jane Example', b'Another Example'))
                    state['items'][uri]['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                elif mode == 'missing_personal_identifier':
                    path.write_bytes(original.replace(b'application/rdf+xml', b'text/plain'))
                    state['items'][uri]['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                elif mode == 'tampered_bytes': path.write_bytes(original + b' changed')
                else: state['items'][uri]['fetch']['observedAt'] = '2020-01-01'
                with self.subTest(mode=mode), self.assertRaises(ValueError):
                    verified_person_reviews({'entries': [row]}, state, cache, data)

    def test_malformed_record_fields_and_future_alias_captures_are_history_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache)
            proof = row['evidence'][0]
            source = data['professors'][1]
            source.update(email='unreviewed@ucsd.edu', researchSummary='Unreviewed old resource text',
                          sourceUrls=source['sourceUrls'] + ['https://researcherprofiles.org/profile/999'])
            source.setdefault('fieldEvidence', {})['researchSummary'] = [proof]
            row.update(originalSourceRecord=copy.deepcopy(source), sourceRecordSha256=record_sha256(source))
            reviews = verified_person_reviews({'entries': [row]}, queue, cache, data)
            captured = {'byProfessorId': {'misparsed': {'researchSummary': 'Another unreviewed source observation',
                                                       'fieldEvidence': {'researchSummary': [proof]}}}}
            course = {'courseCode': 'BENG 999', 'term': 'Fall 2025', 'sourceUrl': proof['sourceUrl'],
                      'observedAt': proof['observedAt'], 'evidence': 'Example Research'}
            teaching = {'byProfessorId': {'misparsed': [course]}}
            ratings = {'byProfessorId': {'misparsed': {'rateMyProfessors': {'status': 'verified', 'score': 5}}}}
            first, _, _, archives = build(copy.deepcopy(data), captured, teaching, ratings, {}, {}, {}, {}, {'personIdentityReviews': reviews})
            target = first['professors'][0]
            self.assertNotEqual(target['email'], source['email'])
            self.assertNotIn('unreviewed', target['researchSummary'].lower())
            self.assertNotIn('https://researcherprofiles.org/profile/999', target['sourceUrls'])
            self.assertEqual(target['teaching']['courses'], [])
            self.assertIsNone(target['ratings']['rateMyProfessors']['score'])
            history = next(o for o in target['previousFieldObservations'] if o['field'] == 'misparsedResourceCaptureInputs')
            self.assertEqual(history['value']['teaching'], [course])
            self.assertEqual(history['value']['ratings'], ratings['byProfessorId']['misparsed'])
            self.assertEqual(audit(data, first, [archives])['status'], 'passed')
            second, *_ = build(copy.deepcopy(first), captured, teaching, ratings, {}, {}, {}, {}, {'personIdentityReviews': reviews})
            self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()
