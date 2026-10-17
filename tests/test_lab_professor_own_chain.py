import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lab_professor_own_chain import observed_chain, KIND
from lab_field_reviews import verified_lab_fields, apply_lab_fields
from lab_resource_reviews import record_sha256
from test_atlas_quality import professor


class LabProfessorOwnChainTests(unittest.TestCase):
    def fixture(self, cache):
        original = 'https://cse.ucsd.edu/people/faculty-profiles/jane-example'
        personal = 'https://jane.example.org/'
        jacobs = 'https://jacobsschool.ucsd.edu/faculty/profile?id=123'
        laburi = 'https://example-lab.ucsd.edu/home'
        members = 'https://example-lab.ucsd.edu/members'
        pages = {
            original: '<title>Jane Example</title><main><h1>Jane Example</h1><div class="field--name-field-web-page"><a href="'+personal+'">Website</a></div></main>',
            personal: '<title>Jane A. Example</title><main><h1>Jane A. Example</h1></main>',
            jacobs: '<main><h3 class="faculty_profile_name">Jane Example</h3><div class="col-3"><p><a href="'+personal+'">JANE A. EXAMPLE</a></p><p><a href="'+laburi+'">Example Research Lab</a></p></div></main>',
            laburi: '<title>Example Research Lab</title><main><h1>Example Research Lab</h1></main>',
            members: '<title>Members</title><main><h1>Members</h1><p>Principal Investigator: Jane A. Example</p></main>',
        }
        (cache / 'responses').mkdir()
        items = {}
        for uri, html in pages.items():
            path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest()+'.html'); path.write_text(html)
            items[uri] = {'url': uri, 'state': 'done', 'fetch': {'status':'ok', 'sourceUrl':uri, 'finalUrl':uri, 'observedAt':'2026-10-16T00:00:00+00:00', 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}
        person = professor('original-id', 'Jane Example', 'Computer Science and Engineering')
        person.update(officialProfileUrl=original, personalWebsiteUrl=personal, labAffiliation='Not found', labAffiliationUrl='Not found')
        lab = {'id':'named-lab-id', 'labName':'Example Research Lab', 'labWebsiteUrl':laburi, 'principalInvestigator':'Not found', 'professorIds':[]}
        q = {'items':items}
        def proof(uri, text):
            m=items[uri]['fetch'];return {'requestedUrl':uri, 'sourceUrl':uri, 'observedAt':m['observedAt'], 'bodySha256':m['sha256'], 'evidenceType':'main_text_quote', 'evidence':text, 'method':'captured_own_identity_chain_fixture'}
        identities = [proof(original,'Jane Example'), proof(personal,'Jane A. Example'), proof(jacobs,'Jane Example')]
        labproof = proof(laburi, lab['labName']); piproof = proof(members,'Principal Investigator: Jane A. Example')
        row = {'labId':lab['id'], 'originalLabRecord':copy.deepcopy(lab), 'originalLabRecordSha256':record_sha256(lab), 'professorId':person['id'],
               'fields':{'principalInvestigator':'Jane A. Example', 'principalInvestigatorProfileUrl':original},
               'fieldEvidence':{'principalInvestigator':[piproof], 'principalInvestigatorProfileUrl':identities},
               'personEvidence':identities, 'identityEvidence':[labproof], 'evidence':identities+[labproof,piproof],
               'reason':'The original and corroborating campus own Website fields share the exact unique personal identifier and the named lab link.',
               'personIdentityBasis':{'type':KIND, 'originalProfessorRecord':copy.deepcopy(person), 'originalProfessorRecordSha256':record_sha256(person),
                  'personalWebsiteRequestUri':personal, 'jacobsProfileRequestUri':jacobs,
                  'chain':observed_chain(person,lab,q,cache,personal,jacobs,[person])}, 'linkProfessorLab':True}
        return person,lab,q,row

    def change(self, cache, q, uri, old, new):
        path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.write_text(path.read_text().replace(old,new));q['items'][uri]['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()

    def test_three_actual_self_fields_link_as_listed_pi_without_changing_original_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);p,lab,q,row=self.fixture(cache);before=copy.deepcopy(p)
            reviews=verified_lab_fields({'entries':[row]},q,cache,[lab],[p]);data={'labs':[lab],'professors':[p]};apply_lab_fields(data,reviews)
            for k in ['id','name','officialProfileUrl','department','email','lastVerified']:self.assertEqual(p[k],before[k])
            self.assertEqual(lab['principalInvestigator'],'Jane A. Example');self.assertEqual(lab['principalInvestigatorProfileUrl'],p['officialProfileUrl'])
            self.assertEqual(lab['professorIds'],[p['id']]);self.assertTrue(lab['fieldEvidence']['professorIds'])
            self.assertEqual(p['labAffiliation'],lab['labName']);self.assertEqual(p['labAffiliations'][0]['labId'],lab['id'])
            for proofs in p['fieldEvidence'].values():
                for proof in proofs:
                    self.assertIn(proof['sourceUrl'],p['sourceUrls'])
            once=copy.deepcopy(data);apply_lab_fields(data,reviews);self.assertEqual(data,once)

    def test_shared_website_or_unpublished_middle_name_without_chain_cannot_bind(self):
        for mode in ['shared','no_chain','tamper_snapshot','tamper_chain','wrong_pi_name','missing_capture_proof']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);p,lab,q,row=self.fixture(cache);people=[p]
                if mode=='shared':people.append({**copy.deepcopy(p),'id':'other-person'})
                if mode=='no_chain':row.pop('personIdentityBasis')
                if mode=='tamper_snapshot':row['personIdentityBasis']['originalProfessorRecord']['email']='invented@ucsd.edu'
                if mode=='tamper_chain':row['personIdentityBasis']['chain']['fullOwnNameAsDisplayed']='Jane B. Example'
                if mode=='wrong_pi_name':row['fields']['principalInvestigator']='Jane B. Example'
                if mode=='missing_capture_proof':row['personEvidence']=row['personEvidence'][:2]
                with self.assertRaises(ValueError):verified_lab_fields({'entries':[row]},q,cache,[lab],people)

    def test_own_template_and_exact_literal_transport_are_required(self):
        for mode in ['unscoped_website','unscoped_lab','different_literal_uri','ambiguous_jacobs_column','wrong_personal_subject','initial_name','foreign_profile_redirect','changed_body']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);p,lab,q,row=self.fixture(cache);basis=row['personIdentityBasis'];original=p['officialProfileUrl'];personal=p['personalWebsiteUrl'];jacobs=basis['jacobsProfileRequestUri']
                if mode=='unscoped_website':self.change(cache,q,original,'field--name-field-web-page','arbitrary-biography')
                if mode=='unscoped_lab':self.change(cache,q,jacobs,'class="col-3"','class="coauthor-list"')
                if mode=='different_literal_uri':basis['personalWebsiteRequestUri']=personal.replace('https:','http:')
                if mode=='ambiguous_jacobs_column':
                    path=cache/'responses'/(hashlib.sha256(jacobs.encode()).hexdigest()+'.html');html=path.read_text();column=html[html.index('<div'):html.index('</div>')+6];self.change(cache,q,jacobs,'</main>',column+'</main>')
                if mode=='wrong_personal_subject':self.change(cache,q,personal,'Jane A. Example','John Other')
                if mode=='initial_name':p['name']='J. Example';basis['originalProfessorRecord']=copy.deepcopy(p);basis['originalProfessorRecordSha256']=record_sha256(p)
                if mode=='foreign_profile_redirect':q['items'][original]['fetch']['finalUrl']='https://other.ucsd.edu/people/jane-example'
                if mode=='changed_body':
                    path=cache/'responses'/(hashlib.sha256(personal.encode()).hexdigest()+'.html');path.write_text(path.read_text()+'changed')
                with self.assertRaises(ValueError):verified_lab_fields({'entries':[row]},q,cache,[lab],[p])

    def test_fresh_receipts_still_reject_unscoped_or_ambiguous_self_links(self):
        for mode in ['unscoped_original', 'unscoped_jacobs', 'duplicate_column', 'different_subject', 'generic_original_uri']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);p,lab,q,row=self.fixture(cache);personal=p['personalWebsiteUrl'];jacobs=row['personIdentityBasis']['jacobsProfileRequestUri'];original=p['officialProfileUrl']
                if mode=='unscoped_original':self.change(cache,q,original,'field--name-field-web-page','coauthor-biography')
                if mode=='unscoped_jacobs':self.change(cache,q,jacobs,'class="col-3"','class="unrelated"')
                if mode=='duplicate_column':
                    path=cache/'responses'/(hashlib.sha256(jacobs.encode()).hexdigest()+'.html');html=path.read_text();column=html[html.index('<div'):html.index('</div>')+6];self.change(cache,q,jacobs,'</main>',column+'</main>')
                if mode=='different_subject':self.change(cache,q,personal,'Jane A. Example','John Other')
                if mode=='generic_original_uri':
                    uri='https://cse.ucsd.edu/people/faculty-profiles/';item=copy.deepcopy(q['items'][original]);item['url']=uri;item['fetch'].update(sourceUrl=uri,finalUrl=uri);q['items'][uri]=item;p['officialProfileUrl']=uri
                    (cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html')).write_bytes((cache/'responses'/(hashlib.sha256(original.encode()).hexdigest()+'.html')).read_bytes())
                with self.assertRaises(ValueError):observed_chain(p,lab,q,cache,personal,jacobs,[p])

    def test_adding_verified_relationship_does_not_replace_another_supported_lab_scalar(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);p,lab,q,row=self.fixture(cache);p.update(labAffiliation='Another Research Lab',labAffiliationUrl='https://another-lab.ucsd.edu/')
            row['personIdentityBasis']['originalProfessorRecord']=copy.deepcopy(p);row['personIdentityBasis']['originalProfessorRecordSha256']=record_sha256(p)
            reviews=verified_lab_fields({'entries':[row]},q,cache,[lab],[p]);apply_lab_fields({'labs':[lab],'professors':[p]},reviews)
            self.assertEqual(p['labAffiliation'],'Another Research Lab');self.assertEqual(p['labAffiliationUrl'],'https://another-lab.ucsd.edu/');self.assertEqual(p['labAffiliations'][0]['labId'],lab['id'])


if __name__=='__main__':unittest.main()
