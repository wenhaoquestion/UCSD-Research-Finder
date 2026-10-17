import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import test_faculty_resource_label_reviews as resource_cases
from faculty_profile_chain_reviews import KIND, profile_chain_binding, compatible_full_names
from faculty_resource_label_reviews import resource_label_binding
from person_identity_reviews import verified_person_reviews
from lab_resource_reviews import record_sha256
from rebuild_verified_atlas import build
from audit_ucsd_preservation import audit
from test_atlas_quality import professor


class FacultyProfileChainReviewTests(unittest.TestCase):
    def fixture(self, cache):
        data, queue, bridge = resource_cases.FacultyResourceLabelReviewTests().fixture(cache)
        target, artifact = data['professors']
        source = professor('source-person', 'Jane Alice Example', 'Medicine')
        own_uri = 'https://profiles.ucsd.edu/jane.example'
        roster_uri = 'https://med.ucsd.edu/about/faculty-directory.html'
        source.update(officialProfileUrl=own_uri, sourceUrls=[own_uri, roster_uri])
        data['professors'].append(source)
        def save(uri, body):
            path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
            path.write_text(body)
            meta = {'status': 'ok', 'sourceUrl': uri, 'finalUrl': uri.replace('http:', 'https:'),
                    'observedAt': '2026-01-01', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            queue['items'][uri] = {'url': uri, 'fetch': meta}
            return {k: meta[k] for k in ['sourceUrl', 'observedAt']}
        http_path = cache / 'responses' / (hashlib.sha256(artifact['officialProfileUrl'].encode()).hexdigest() + '.html')
        own = http_path.read_text().replace('</main>', '<table><tr><th>Title(s)</th><td>Associate Professor, Medicine</td></tr><tr><th>School</th><td>Vc-health Sciences-schools</td></tr></table></main>')
        for uri in [artifact['officialProfileUrl'], own_uri]: save(uri, own)
        bridge['resourceLabelBinding'] = resource_label_binding(artifact, target, queue['items'][bridge['resourceLabelBinding']['roster']['requestedUrl']], queue['items'][artifact['officialProfileUrl']], cache, data['professors'])
        for proof in bridge['evidence']:
            proof['bodySha256'] = queue['items'][proof['requestedUrl']]['fetch']['sha256']
        save(roster_uri, '<main><h1>Department of Medicine Faculty Directory</h1><table id="datatable"><tbody><tr><td><a href="' + own_uri + '">Example, Jane Alice, M.D., PhD</a></td><td>Cardiovascular Medicine</td></tr></tbody></table></main>')
        save(target['officialProfileUrl'], '<main><div><h3 class="faculty_profile_name">Jane Example</h3><p class="mb-5">Associate Professor, BENG and Medicine</p><hr></div></main>')
        request = {'bridgeSourceProfessorId': artifact['id'], 'sourceRosterRequestedUri': roster_uri}
        binding = profile_chain_binding(source, target, request, [bridge], data['professors'], queue, cache)
        def proof(uri, text, kind='main_text_quote', **extra):
            meta = queue['items'][uri]['fetch']
            return {'requestedUrl': uri, 'sourceUrl': meta['finalUrl'], 'observedAt': meta['observedAt'],
                    'bodySha256': meta['sha256'], 'evidenceType': kind, 'evidence': text, **extra}
        named = proof(roster_uri, 'Example, Jane Alice, M.D., PhD -> ' + own_uri, 'named_link', linkText='Example, Jane Alice, M.D., PhD', linkUrl=own_uri)
        own_role = proof(own_uri, 'Associate Professor, Medicine')
        target_role = proof(target['officialProfileUrl'], 'Jane Example Associate Professor, BENG and Medicine')
        proofs = bridge['evidence'] + [named, own_role, target_role]
        source['fieldEvidence'] = {'name': [named]}
        row = {'action': 'merge', 'name': target['name'], 'sourceProfessorId': source['id'], 'targetProfessorId': target['id'],
               'originalSourceRecord': copy.deepcopy(source), 'originalTargetRecord': copy.deepcopy(target),
               'sourceRecordSha256': record_sha256(source), 'targetRecordSha256': record_sha256(target),
               'identityBasis': {'type': KIND, 'value': binding['sourceOwnProfile']['rdfAlternateUri']},
               'profileChainRequest': request, 'profileChainBinding': binding,
               'fields': {'department': target['department'], 'officialProfileUrl': target['officialProfileUrl']},
               'fieldEvidence': {'department': [target_role], 'officialProfileUrl': [target_role]},
               'departmentEvidence': [{'department': target['department'], 'fieldEvidence': [target_role], 'status': 'as_listed'},
                                      {'department': source['department'], 'fieldEvidence': [own_role], 'status': 'as_listed'}],
               'evidence': proofs, 'reason': 'Five exact captures connect the two originally named faculty records through their own personal identifiers.'}
        return data, queue, [bridge, row]

    def test_verified_named_chain_preserves_ids_names_courses_and_repeat_assembly(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, rows = self.fixture(cache)
            reviews = verified_person_reviews({'entries': rows}, queue, cache, data)
            def course(code): return {'courseCode': code, 'term': 'Fall 2025', 'sourceUrl': rows[-1]['evidence'][-1]['sourceUrl'], 'observedAt': '2025-10-01', 'evidence': code}
            teaching = {'byProfessorId': {'canonical': [course('BENG 100')], 'source-person': [course('MED 100')]}}
            first, _, _, archives = build(copy.deepcopy(data), {}, teaching, {}, {}, {}, {}, {}, {'personIdentityReviews': reviews})
            target = first['professors'][0]
            self.assertEqual(len(first['professors']), 1)
            self.assertEqual(set(target['aliasIds']), {'misparsed', 'source-person'})
            self.assertEqual(target['name'], 'Jane Example')
            self.assertEqual(target['aliasNames'], ['Jane Alice Example'])
            self.assertEqual(set(target['departmentAffiliations']), {'Bioengineering', 'Medicine'})
            self.assertEqual({c['courseCode'] for c in target['teaching']['courses']}, {'BENG 100', 'MED 100'})
            self.assertEqual(audit(data, first, [archives])['status'], 'passed')
            second, *_ = build(copy.deepcopy(first), {}, teaching, {}, {}, {}, {}, {}, {'personIdentityReviews': reviews})
            self.assertEqual(first, second)

    def test_new_name_capture_through_retired_id_preserves_reviewed_primary_form(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, rows = self.fixture(cache)
            reviews = verified_person_reviews({'entries': rows}, queue, cache, data)
            first, *_ = build(copy.deepcopy(data), {}, {}, {}, {}, {}, {}, {}, {'personIdentityReviews': reviews})
            name_proof = copy.deepcopy(rows[-1]['evidence'][-3]); name_proof['method'] = 'later_name_observation'
            captures = {'byProfessorId': {'source-person': {'name': 'Jane Alice Example', 'fieldEvidence': {'name': [name_proof]}}}}
            updated, *_ = build(copy.deepcopy(first), captures, {}, {}, {}, {}, {}, {}, {'personIdentityReviews': reviews})
            self.assertEqual(updated['professors'][0]['name'], 'Jane Example')
            self.assertEqual(updated['professors'][0]['aliasNames'], ['Jane Alice Example'])
            repeated, *_ = build(copy.deepcopy(updated), captures, {}, {}, {}, {}, {}, {}, {'personIdentityReviews': reviews})
            self.assertEqual(updated, repeated)

    def test_inherited_unmapped_context_stays_in_history_not_displayed_as_a_department(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,queue,rows=self.fixture(cache);row=rows[-1]
            uri='https://cardiology.ucsd.edu/about/faculty.html';raw=b'<main><h1>Faculty</h1><a href="https://profiles.ucsd.edu/jane.example">Jane Example</a></main>'
            path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.write_bytes(raw)
            meta={'sourceUrl':uri,'finalUrl':uri,'status':'ok','observedAt':'2026-01-01','sha256':hashlib.sha256(raw).hexdigest()};queue['items'][uri]={'url':uri,'fetch':meta}
            listing={'name':'Jane Example','department':'Interdisciplinary','sourceUrl':uri,'observedAt':meta['observedAt'],
                     'sourceListingSelectionHistory':[{'selected':{'department':'Unknown','namedLinkUrl':data['professors'][2]['officialProfileUrl']},'bodySha256':meta['sha256']}]}
            previous=copy.deepcopy(data['professors'][2]);previous.update(departmentAffiliations=['Medicine','Interdisciplinary'],directoryListings=[listing])
            row['previousCandidateObservation']={'candidateAtlasSha256':'a'*64,'recordSha256':record_sha256(previous),'record':previous}
            row['unsupportedDepartmentValues']=['Interdisciplinary']
            reviews=verified_person_reviews({'entries':rows},queue,cache,data)
            coverage={'personIdentityReviews':reviews,'byProfessorId':{'source-person':{'departmentAffiliations':['Medicine','Interdisciplinary'],'directoryListings':[listing]}}}
            first,*_=build(copy.deepcopy(data),{},{},{},{},{},{},{},coverage)
            target=first['professors'][0]
            self.assertEqual(set(target['departmentAffiliations']),{'Bioengineering','Medicine'})
            self.assertEqual(target['directoryListings'][0]['department'],'Unknown')
            self.assertEqual(target['directoryListings'][0]['sourceDepartmentContext'],'Interdisciplinary')
            self.assertTrue(any(h.get('field')=='directoryListings' and h.get('value')==[listing] for h in target['previousFieldObservations']))
            repeated,*_=build(copy.deepcopy(first),{},{},{},{},{},{},{},coverage)
            self.assertEqual(first,repeated)
            for mode in ['named_department','missing_unmapped_marker','positive_department_proof']:
                altered=copy.deepcopy(rows);r=altered[-1]
                if mode=='named_department':r['unsupportedDepartmentValues']=['Biochemistry']
                elif mode=='missing_unmapped_marker':r['previousCandidateObservation']['record']['directoryListings'][0]['sourceListingSelectionHistory']=[]
                else:r['previousCandidateObservation']['record']['fieldEvidence']['departmentAffiliations']=r['evidence'][:1]
                r['previousCandidateObservation']['recordSha256']=record_sha256(r['previousCandidateObservation']['record'])
                with self.subTest(mode=mode),self.assertRaises(ValueError):verified_person_reviews({'entries':altered},queue,cache,data)

    def test_initials_nicknames_and_conflicting_middle_names_cannot_use_the_chain(self):
        for left, right in [('J. Example', 'Jane Example'), ('Jane A. Example', 'Jane B. Example'),
                            ('Mike Campbell', 'Edward Campbell'), ('Jane Example', 'Jane Different')]:
            with self.subTest(left=left, right=right): self.assertFalse(compatible_full_names(left, right))

    def test_missing_unscoped_or_wrong_named_table_link_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, rows = self.fixture(cache); row = rows[-1]
            uri = row['profileChainRequest']['sourceRosterRequestedUri'];path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html');original = path.read_text()
            for raw in [original.replace('id="datatable"', 'id="other"'), original.replace('<main>', '<nav>').replace('</main>', '</nav>'),
                        original.replace('Jane Alice', 'Another Alice'), original.replace('https://profiles', 'http://profiles'),
                        original.replace('PhD', 'Another Person'), original.replace('</td><td>', '</td><td><a href="https://profiles.ucsd.edu/rival">Rival Person</a>'),
                        original.replace('Medicine Faculty', 'Staff Faculty')]:
                path.write_text(raw); state = copy.deepcopy(queue);state['items'][uri]['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                with self.subTest(raw=raw), self.assertRaises(ValueError):
                    profile_chain_binding(data['professors'][2], data['professors'][0], row['profileChainRequest'], rows, data['professors'], state, cache)

    def test_different_own_subject_personal_identifiers_or_target_title_cannot_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, rows = self.fixture(cache); row = rows[-1]
            for uri, old, replacement in [(data['professors'][2]['officialProfileUrl'], 'Jane Example', 'Another Example'),
                                           (data['professors'][2]['officialProfileUrl'], '/123/123.rdf', '/124/124.rdf'),
                                           (data['professors'][2]['officialProfileUrl'], 'jane.example', 'another.example'),
                                           (data['professors'][0]['officialProfileUrl'], 'Associate Professor', 'Staff Scientist')]:
                path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html');original = path.read_bytes();path.write_bytes(original.replace(old.encode(), replacement.encode()));state = copy.deepcopy(queue);state['items'][uri]['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                with self.subTest(uri=uri, replacement=replacement), self.assertRaises(ValueError):
                    profile_chain_binding(data['professors'][2], data['professors'][0], row['profileChainRequest'], rows, data['professors'], state, cache)
                path.write_bytes(original)

    def test_changed_original_binding_date_bytes_omitted_capture_or_competing_owner_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, rows = self.fixture(cache)
            for mode in ['original', 'binding', 'date', 'missing_evidence', 'missing_bridge', 'competing_owner', 'wrong_department_proof']:
                state=copy.deepcopy(queue);reviews=copy.deepcopy(rows);baseline=copy.deepcopy(data);r=reviews[-1]
                if mode=='original': r['originalSourceRecord']['name']='Changed Example'
                elif mode=='binding': r['profileChainBinding']['sourceOwnProfile']['rdfAlternateUri']='changed'
                elif mode=='date': state['items'][baseline['professors'][0]['officialProfileUrl']]['fetch']['observedAt']='2020-01-01'
                elif mode=='missing_evidence': r['evidence']=r['evidence'][:-1]
                elif mode=='missing_bridge': reviews=reviews[1:]
                elif mode=='competing_owner': rival=copy.deepcopy(baseline['professors'][2]);rival['id']='rival';baseline['professors'].append(rival)
                else: r['departmentEvidence'][1]['fieldEvidence']=r['fieldEvidence']['department']
                with self.subTest(mode=mode), self.assertRaises(ValueError): verified_person_reviews({'entries':reviews},state,cache,baseline)


if __name__ == '__main__':
    unittest.main()
