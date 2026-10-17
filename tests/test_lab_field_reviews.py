import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lab_field_reviews import verified_lab_fields, apply_lab_fields, own_lab_source
from lab_resource_reviews import record_sha256
from refresh_labs import make_lab
from rebuild_verified_atlas import build
from audit_ucsd_preservation import audit
from test_atlas_quality import atlas, professor
import test_shared_lab_entities as shared_fixtures


class LabFieldReviewTests(unittest.TestCase):
    def test_own_pi_name_can_have_a_degree_before_its_explicit_role(self):
        for suffix in ['Ph.D','M.D.']:
            with self.subTest(suffix=suffix),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);data,queue,row=self.fixture(cache);before=copy.deepcopy(data)
                text='Jane Example, '+suffix+' Principal Investigator'
                uri=data['labs'][0]['labWebsiteUrl']+'people'
                claim=self.capture(cache,queue['items'],uri,'<main>'+text+'</main>')
                claim.update(evidenceType='main_text_quote',evidence=text)
                row['fieldEvidence']['principalInvestigator']=[claim]
                row['evidence']=row['identityEvidence']+[claim]+row['personEvidence']
                reviews=verified_lab_fields({'entries':[row]},queue,cache,data['labs'],data['professors'])
                first,*_=build(copy.deepcopy(data),{},{},{},{},coverage_evidence={'reviewedLabFieldUpdates':reviews})
                self.assertEqual(first['labs'][0]['principalInvestigator'],'Jane Example')
                self.assertEqual(first['labs'][0]['principalInvestigatorProfileUrl'],'https://people.ucsd.edu/jane')
                self.assertEqual(audit(before,first)['status'],'passed')
                second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence={'reviewedLabFieldUpdates':reviews})
                self.assertEqual(first,second)

    def test_pi_degree_cannot_skip_another_name_or_unrelated_role_words(self):
        for text in ['Jane Example Ph.D John Other Principal Investigator',
                     'Jane Example Ph.D Research Principal Investigator',
                     'Jane Example Ph.D student Principal Investigator']:
            with self.subTest(text=text),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);data,queue,row=self.fixture(cache)
                uri=data['labs'][0]['labWebsiteUrl']+'people'
                claim=self.capture(cache,queue['items'],uri,'<main>'+text+'</main>')
                claim.update(evidenceType='main_text_quote',evidence=text)
                row['fieldEvidence']['principalInvestigator']=[claim]
                row['evidence']=row['identityEvidence']+[claim]+row['personEvidence']
                with self.assertRaisesRegex(ValueError,'explicit own-site leadership'):
                    verified_lab_fields({'entries':[row]},queue,cache,data['labs'],data['professors'])

    def test_own_pi_section_can_include_its_faculty_profile_link_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,queue,row=self.fixture(cache);before=copy.deepcopy(data)
            uri=data['labs'][0]['labWebsiteUrl']+'people'
            claim=self.capture(cache,queue['items'],uri,'<main><section><h2>Principal Investigator</h2><a href="https://people.ucsd.edu/jane">Faculty Profile</a><h3>Jane Example</h3></section></main>')
            claim.update(evidenceType='main_text_quote',evidence='Principal Investigator Faculty Profile Jane Example')
            row['fieldEvidence']['principalInvestigator']=[claim]
            row['evidence']=row['identityEvidence']+[claim]+row['personEvidence']
            reviews=verified_lab_fields({'entries':[row]},queue,cache,data['labs'],data['professors'])
            first,*_=build(copy.deepcopy(data),{},{},{},{},coverage_evidence={'reviewedLabFieldUpdates':reviews})
            self.assertEqual(first['labs'][0]['principalInvestigator'],'Jane Example')
            self.assertEqual(first['labs'][0]['principalInvestigatorProfileUrl'],'https://people.ucsd.edu/jane')
            self.assertEqual(first['labs'][0]['professorIds'],['jane'])
            self.assertEqual(first['professors'][0]['id'],'jane')
            self.assertEqual(audit(before,first)['status'],'passed')
            second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence={'reviewedLabFieldUpdates':reviews})
            self.assertEqual(first,second)

    def test_profile_link_label_cannot_skip_another_person_or_invent_a_role(self):
        for text in ['Principal Investigator Faculty Profile John Other Jane Example',
                     'Faculty Profile Jane Example Professor',
                     'Principal Investigator Research Faculty Profile Jane Example']:
            with self.subTest(text=text),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);data,queue,row=self.fixture(cache)
                uri=data['labs'][0]['labWebsiteUrl']+'people'
                claim=self.capture(cache,queue['items'],uri,'<main>'+text+'</main>')
                claim.update(evidenceType='main_text_quote',evidence=text)
                row['fieldEvidence']['principalInvestigator']=[claim]
                row['evidence']=row['identityEvidence']+[claim]+row['personEvidence']
                with self.assertRaisesRegex(ValueError,'explicit own-site leadership'):
                    verified_lab_fields({'entries':[row]},queue,cache,data['labs'],data['professors'])

    def recruiting_fixture(self,cache,text='Undergraduate Students: RECRUITING!!!',shared=False):
        data,queue,row=self.fixture(cache,shared=shared)
        uri=data['labs'][0]['labWebsiteUrl']+'opportunities'
        claim=self.capture(cache,queue['items'],uri,'<main>'+text+'</main>')
        claim.update(evidenceType='main_text_quote',evidence=text,method='reviewed_explicit_own_lab_recruiting_statement')
        row.pop('professorId');row.pop('personEvidence')
        row.update(fields={'recruitingStatus':'Recruiting','recruitingEvidence':{'text':text,'url':claim['sourceUrl']}},
                   fieldEvidence={'recruitingStatus':[claim],'recruitingEvidence':[claim]},evidence=row['identityEvidence']+[claim])
        return data,queue,row

    def test_explicit_recruiting_keeps_exact_scope_source_dates_and_prior_data(self):
        for text,status in [('Undergraduate Students: RECRUITING!!!','Recruiting'),('We are not currently recruiting students.','Not recruiting')]:
            with self.subTest(status=status),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);data,queue,row=self.recruiting_fixture(cache,text);row['fields']['recruitingStatus']=status;before=copy.deepcopy(data)
                rows=verified_lab_fields({'entries':[row]},queue,cache,data['labs'],data['professors'])
                first,*_=build(copy.deepcopy(data),{},{},{},{},coverage_evidence={'reviewedLabFieldUpdates':rows})
                self.assertEqual(first['labs'][0]['recruitingStatus'],status)
                self.assertEqual(first['labs'][0]['recruitingEvidence'],row['fields']['recruitingEvidence'])
                self.assertEqual(first['labs'][0]['fieldEvidence']['recruitingStatus'],row['fieldEvidence']['recruitingStatus'])
                self.assertEqual(audit(before,first)['status'],'passed')
                second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence={'reviewedLabFieldUpdates':rows})
                self.assertEqual(first,second)

    def test_missing_or_opposite_recruiting_statement_cannot_supply_status(self):
        for text,status in [('Join our mailing list.','Recruiting'),('We are not currently recruiting students.','Recruiting'),('We are recruiting students.','Not recruiting')]:
            with self.subTest(text=text,status=status),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);data,queue,row=self.recruiting_fixture(cache,text);row['fields']['recruitingStatus']=status
                with self.assertRaisesRegex(ValueError,'corresponding published statement'):
                    verified_lab_fields({'entries':[row]},queue,cache,data['labs'],data['professors'])

    def test_recruiting_cannot_use_foreign_origin_rewrite_quote_or_tamper_capture(self):
        for mode in ['foreign_lab','quote','source_url','date','hash']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);data,queue,row=self.recruiting_fixture(cache)
                if mode=='foreign_lab':
                    uri='https://another.ucsd.edu/lab/opportunities';claim=self.capture(cache,queue['items'],uri,'<main>We are recruiting students.</main>');claim.update(evidenceType='main_text_quote',evidence='We are recruiting students.',method='reviewed_explicit_own_lab_recruiting_statement');row['fields']['recruitingEvidence']={'text':claim['evidence'],'url':claim['sourceUrl']};row['fieldEvidence']={'recruitingStatus':[claim],'recruitingEvidence':[claim]};row['evidence']=row['identityEvidence']+[claim]
                if mode=='quote':row['fields']['recruitingEvidence']['text']='Invented recruitment'
                if mode=='source_url':row['fields']['recruitingEvidence']['url']='https://different.ucsd.edu/'
                if mode=='date':row['evidence'][-1]['observedAt']='2020-01-01'
                if mode=='hash':row['evidence'][-1]['bodySha256']='0'*64
                with self.assertRaises(ValueError):verified_lab_fields({'entries':[row]},queue,cache,data['labs'],data['professors'])

    def test_generic_shared_resource_recruitment_does_not_apply_to_both_labs(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,queue,row=self.recruiting_fixture(cache,shared=True)
            with self.assertRaisesRegex(ValueError,'separately scoped'):
                verified_lab_fields({'entries':[row]},queue,cache,data['labs'],data['professors'])

    def capture(self, cache, items, uri, raw, final=None):
        (cache / 'responses').mkdir(exist_ok=True)
        path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
        path.write_bytes(raw.encode())
        meta = {'sourceUrl': uri, 'finalUrl': final or uri, 'status': 'ok', 'observedAt': '2026-01-01', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        items[uri] = {'url': uri, 'fetch': meta}
        return {'requestedUrl': uri, 'sourceUrl': meta['finalUrl'], 'observedAt': meta['observedAt'], 'bodySha256': meta['sha256']}

    def fixture(self, cache, shared=False):
        items = {}; home = shared_fixtures.URL if shared else 'https://example.ucsd.edu/lab/'
        text = shared_fixtures.TEXT if shared else 'Example Lab at UC San Diego'
        root = self.capture(cache, items, home, '<title>Example Lab</title><main>' + text + '</main>')
        labs = shared_fixtures.labs() if shared else [make_lab('Example Lab', home, 'Physics', root, text)]
        person = professor('jane', 'Jane Example', 'Physics'); person['sourceUrls'] = ['https://people.ucsd.edu/jane']
        profile = self.capture(cache, items, 'https://people.ucsd.edu/jane', '<title>Jane Example</title><main><h3>Jane Example</h3><p>Professor</p></main>')
        profile.update(evidenceType='document_title', evidence='Jane Example')
        people_uri = home + 'people'
        pi = self.capture(cache, items, people_uri, '<main><p>Principal Investigator Jane Example</p></main>')
        pi.update(evidenceType='main_text_quote', evidence='Principal Investigator Jane Example')
        identity = {**root, 'evidenceType': 'main_text_quote', 'evidence': text}
        lab = labs[0]
        row = {'labId': lab['id'], 'originalLabRecord': copy.deepcopy(lab), 'originalLabRecordSha256': record_sha256(lab),
               'professorId': person['id'], 'reason': 'Explicit own-lab role and independently named individual profile.',
               'fields': {'principalInvestigator': person['name'], 'principalInvestigatorProfileUrl': profile['sourceUrl']},
               'fieldEvidence': {'principalInvestigator': [pi], 'principalInvestigatorProfileUrl': [profile]},
               'identityEvidence': [identity], 'personEvidence': [profile], 'evidence': [identity, pi, profile]}
        data = atlas(); data.update(qualityMigrationVersion=1, professors=[person], labs=labs)
        return data, {'items': items}, row

    def test_explicit_own_pi_links_both_entities_and_preserves_previous_association_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache)
            old = {'labId': row['labId'], 'labName': data['labs'][0]['labName'], 'url': data['labs'][0]['labWebsiteUrl'], 'relationship': 'faculty_lab_link', 'fieldEvidence': row['identityEvidence']}
            data['professors'][0]['labAffiliations'] = [old]; before = copy.deepcopy(data)
            rows = verified_lab_fields({'entries': [row]}, queue, cache, data['labs'], data['professors'])
            first, *_ = build(copy.deepcopy(data), {}, {}, {}, {}, coverage_evidence={'reviewedLabFieldUpdates': rows})
            lab, person = first['labs'][0], first['professors'][0]
            self.assertEqual(lab['principalInvestigator'], 'Jane Example')
            self.assertEqual(lab['professorIds'], ['jane'])
            self.assertEqual(person['labAffiliations'][0]['relationship'], 'principal_investigator')
            self.assertTrue(any(o.get('value') == [old] for o in person['previousFieldObservations']))
            self.assertEqual(audit(before, first)['status'], 'passed')
            second, *_ = build(copy.deepcopy(first), {}, {}, {}, {}, coverage_evidence={'reviewedLabFieldUpdates': rows})
            self.assertEqual(first, second)

    def test_professor_title_or_another_persons_pi_role_cannot_establish_leadership(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache)
            for text in ['Professor Jane Example', 'Principal Investigator Alice Other; collaborator Jane Example']:
                pi = self.capture(cache, queue['items'], row['fieldEvidence']['principalInvestigator'][0]['requestedUrl'], '<main>' + text + '</main>')
                pi.update(evidenceType='main_text_quote', evidence=text)
                modified = copy.deepcopy(row); modified['evidence'][1] = pi; modified['fieldEvidence']['principalInvestigator'] = [pi]
                with self.subTest(text=text), self.assertRaisesRegex(ValueError, 'explicit own-site leadership'):
                    verified_lab_fields({'entries': [modified]}, queue, cache, data['labs'], data['professors'])

    def test_same_host_other_lab_or_unobserved_scheme_and_www_do_not_own_contacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache); lab = data['labs'][0]
            for uri in ['https://example.ucsd.edu/another-lab/contact', 'http://example.ucsd.edu/lab/contact', 'https://www.example.ucsd.edu/lab/contact']:
                contact = self.capture(cache, queue['items'], uri, '<main>Contact: lab@ucsd.edu</main>')
                contact.update(evidenceType='main_text_quote', evidence='Contact: lab@ucsd.edu')
                modified = copy.deepcopy(row); modified['fields']['contactEmail'] = 'lab@ucsd.edu'; modified['fieldEvidence']['contactEmail'] = [contact]; modified['evidence'].append(contact)
                self.assertFalse(own_lab_source(lab, uri, queue))
                with self.subTest(uri=uri), self.assertRaisesRegex(ValueError, 'exact own-lab source'):
                    verified_lab_fields({'entries': [modified]}, queue, cache, data['labs'], data['professors'])

    def test_actual_root_redirect_can_support_its_observed_final_origin(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, _ = self.fixture(cache); lab = data['labs'][0]
            lab['labWebsiteUrl'] = 'http://example.ucsd.edu/lab/'
            old_uri = 'http://example.ucsd.edu/lab/'
            self.capture(cache, queue['items'], old_uri, '<main>Example Lab</main>', final='https://example.ucsd.edu/lab/')
            self.assertTrue(own_lab_source(lab, 'https://example.ucsd.edu/lab/contact', queue))
            self.assertFalse(own_lab_source(lab, 'http://example.ucsd.edu/lab/contact', queue))
            self.assertFalse(own_lab_source(lab, 'https://www.example.ucsd.edu/lab/contact', queue))

    def test_shared_homepage_does_not_assign_a_generic_pi_to_both_labs(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache, shared=True)
            with self.assertRaisesRegex(ValueError, 'explicit own-site leadership'):
                verified_lab_fields({'entries': [row]}, queue, cache, data['labs'], data['professors'])

    def test_linked_profile_directorship_requires_named_subject_clause_link_and_complete_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache, shared=True); home = data['labs'][0]['labWebsiteUrl']; uri = row['personEvidence'][0]['requestedUrl']
            raw = '<title>Jane Example</title><main><h3>Jane Example</h3><a href="' + home + '">Example Lab A</a><a href="' + home + '">Example Lab B</a><p>Jane Example studies control. He directs two distinct <a href="' + home + '">research laboratories</a>.</p></main>'
            common = self.capture(cache, queue['items'], uri, raw)
            subject = {**common, 'evidenceType': 'document_title', 'evidence': 'Jane Example'}
            clause = {**common, 'evidenceType': 'main_text_quote', 'evidence': 'He directs two distinct research laboratories .'}
            scope_link = {**common, 'evidenceType': 'named_link', 'evidence': 'research laboratories -> ' + home, 'linkText': 'research laboratories', 'linkUrl': home}
            named = {**common, 'evidenceType': 'named_link', 'evidence': 'Example Lab A -> ' + home, 'linkText': 'Example Lab A', 'linkUrl': home}
            row.update(personEvidence=[subject], evidence=row['identityEvidence'] + [subject, clause, scope_link, named], piScope={'kind': 'named_profile_link_to_two_labs', 'directedLabIds': ['lab-a', 'lab-b'], 'subjectEvidence': subject, 'clauseEvidence': clause, 'scopeLinkEvidence': scope_link, 'namedLabLinkEvidence': named})
            row['fieldEvidence'] = {'principalInvestigator': [subject, clause, scope_link, named], 'principalInvestigatorProfileUrl': [subject]}
            verified = verified_lab_fields({'entries': [row]}, queue, cache, data['labs'], data['professors'])
            self.assertTrue(verified[0]['captureVerified'])
            bad = copy.deepcopy(row); bad['piScope']['directedLabIds'] = ['lab-a']
            with self.assertRaisesRegex(ValueError, 'complete reviewed'):
                verified_lab_fields({'entries': [bad]}, queue, cache, data['labs'], data['professors'])

    def test_mismatched_destination_and_a_failed_later_row_cannot_mutate_valid_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache)
            verified = verified_lab_fields({'entries': [row]}, queue, cache, data['labs'], data['professors']); before = copy.deepcopy(data)
            with self.assertRaises(ValueError): apply_lab_fields(data, verified + [{**verified[0], 'labId': 'missing'}])
            self.assertEqual(data, before)
            data['labs'][0]['destinationIdentityAssessment'] = {'identityStatus': 'mismatch'}
            with self.assertRaisesRegex(ValueError, 'explicit identity'):
                verified_lab_fields({'entries': [row]}, queue, cache, data['labs'], data['professors'])

    def test_qualified_display_name_requires_its_existing_captured_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache)
            lab = data['labs'][0]; lab['labName'] = 'Example Lab (Quantum Devices and Imaging)'
            row['originalLabRecord'] = copy.deepcopy(lab); row['originalLabRecordSha256'] = record_sha256(lab)
            with self.assertRaisesRegex(ValueError, 'specifically named lab'):
                verified_lab_fields({'entries': [row]}, queue, cache, data['labs'], data['professors'])
            lab['aliasNames'] = ['Example Lab']
            row['originalLabRecord'] = copy.deepcopy(lab); row['originalLabRecordSha256'] = record_sha256(lab)
            self.assertTrue(verified_lab_fields({'entries': [row]}, queue, cache, data['labs'], data['professors'])[0]['captureVerified'])

    def test_named_campus_json_with_unique_existing_email_can_link_an_explicit_own_lab_pi(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); data, queue, row = self.fixture(cache); person = data['professors'][0]
            uri = 'https://example.ucsd.edu/faculty.json'; person['email'] = 'jane@ucsd.edu'; person['sourceUrls'].append(uri)
            record = {'first_name': 'Jane', 'last_name': 'Example', 'email': person['email'], 'display_title': 'Professor'}
            proof = self.capture(cache, queue['items'], uri, json.dumps([record]))
            proof.update(evidenceType='json_record', evidence=json.dumps(record,ensure_ascii=False,sort_keys=True), sourceJsonPointer='/0', sourceRecord=record)
            row['personEvidence'] = [proof]; row['evidence'] = row['identityEvidence'] + row['fieldEvidence']['principalInvestigator'] + [proof]
            row['fields'].pop('principalInvestigatorProfileUrl'); row['fieldEvidence'].pop('principalInvestigatorProfileUrl')
            row.update(personIdentityBasis={'type':'unique_named_campus_json_email','email':person['email']},
                       originalProfessorRecord=copy.deepcopy(person), originalProfessorRecordSha256=record_sha256(person))
            self.assertTrue(verified_lab_fields({'entries': [row]}, queue, cache, data['labs'], data['professors'])[0]['captureVerified'])
            for change in ['pointer', 'email', 'snapshot', 'shared_email', 'missing_source', 'profile_url']:
                bad = copy.deepcopy(row); people = copy.deepcopy(data['professors'])
                if change == 'pointer': bad['personEvidence'][0]['sourceJsonPointer'] = '/9'
                if change == 'email': bad['personIdentityBasis']['email'] = 'someoneelse@ucsd.edu'
                if change == 'snapshot': bad['originalProfessorRecord']['id'] = 'other'
                if change == 'shared_email': people.append({**copy.deepcopy(person), 'id':'other'})
                if change == 'missing_source': people[0]['sourceUrls'] = []
                if change == 'profile_url':
                    bad['fields']['principalInvestigatorProfileUrl'] = 'https://example.ucsd.edu/individual-profile'
                    bad['fieldEvidence']['principalInvestigatorProfileUrl'] = [proof]
                with self.subTest(change=change), self.assertRaises(ValueError):
                    verified_lab_fields({'entries': [bad]}, queue, cache, data['labs'], people)
