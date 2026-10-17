import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_ucsd_preservation import audit
from lab_own_metadata import UCSD, verified_own_metadata, apply_own_metadata
from lab_resource_reviews import record_sha256, verified_alias_reviews
from rebuild_verified_atlas import build
from refresh_labs import make_lab
from test_atlas_quality import atlas


class OwnLabMetadataTests(unittest.TestCase):
    def child_fixture(self, path, parent='https://sites.ucsd.edu/research/example-lab/index.html'):
        data, queue, row, _, _ = self.fixture(path)
        old = next(iter(queue['items']))
        child = parent.rsplit('/', 1)[0] + '/research.html'
        description = 'The ongoing research in the Example Lab aims to investigate inflammation.'
        def capture(uri, body):
            file = path / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
            file.write_text(body)
            meta = {'sourceUrl': uri, 'finalUrl': uri, 'status': 'ok',
                    'observedAt': '2026-10-16T12:00:00+00:00',
                    'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}
            queue['items'][uri] = {'url': uri, 'fetch': meta}
            def proof(text, kind, **extra):
                return {'requestedUrl': uri, 'sourceUrl': uri, 'observedAt': meta['observedAt'],
                        'bodySha256': meta['sha256'], 'evidence': text, 'evidenceType': kind,
                        'method': 'reviewed_own_lab_research_description', **extra}
            return proof
        p = capture(parent, '<title>Example Lab</title><main><h1>Example Lab</h1>'
                    '<a href="research.html">About the research</a></main>')
        c = capture(child, '<title>Research Projects</title><main><h1>Research Projects</h1>'
                    f'<p>{description}</p></main>')
        queue['items'].pop(old)
        lab = data['labs'][0]; lab['labWebsiteUrl'] = parent
        identity = p('Example Lab', 'document_title')
        link = p('About the research -> ' + child, 'named_link',
                 linkText='About the research', linkUrl=child)
        claim = c(description, 'main_text_quote')
        row.update(originalLabRecord=copy.deepcopy(lab), originalLabRecordSha256=record_sha256(lab),
                   fields={'description': description}, fieldEvidence={'description': [claim]},
                   identityEvidence=[identity], evidence=[identity, link, claim],
                   sourceScope={'kind': 'named_own_parent_published_child', 'requestedUrl': child,
                                'publishedLinkEvidence': link, 'researchSubject': 'Example Lab',
                                'subjectStatement': description})
        return data, queue, row

    def test_published_research_child_updates_description_without_becoming_a_home_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp); data, queue, row = self.child_fixture(path)
            before = copy.deepcopy(data)
            rows = verified_own_metadata({'entries': [row]}, [], queue, path, data['labs'])
            first, *_ = build(copy.deepcopy(data), {}, {}, {}, {}, coverage_evidence={'labOwnMetadataReviews': rows})
            self.assertEqual(first['labs'][0]['description'], row['fields']['description'])
            self.assertEqual(first['labs'][0]['labWebsiteUrl'], before['labs'][0]['labWebsiteUrl'])
            self.assertNotIn('websiteAliases', first['labs'][0])
            self.assertEqual(audit(before, first)['status'], 'passed')
            second, *_ = build(copy.deepcopy(first), {}, {}, {}, {}, coverage_evidence={'labOwnMetadataReviews': rows})
            self.assertEqual(first, second)

    def test_child_scope_rejects_unpublished_or_foreign_subjects_and_redirect_escapes(self):
        for mode in ['no_scope', 'different_subject', 'no_subject', 'unpublished', 'foreign_path',
                     'redirect_escape', 'broken_redirect', 'parent_identity_on_child', 'wrong_field', 'changed_bytes']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp); data, queue, row = self.child_fixture(path)
                child = row['sourceScope']['requestedUrl']
                if mode == 'no_scope': row.pop('sourceScope')
                if mode == 'different_subject': row['sourceScope']['researchSubject'] = 'Collaborator Lab'
                if mode == 'no_subject': row['sourceScope']['subjectStatement'] = 'Unrelated research'
                if mode == 'unpublished': row['sourceScope']['publishedLinkEvidence'] = {}
                if mode in {'foreign_path', 'redirect_escape', 'broken_redirect'}:
                    target = 'https://sites.ucsd.edu/other-lab/research.html'
                    meta = queue['items'][child]['fetch']; meta['finalUrl'] = target
                    meta['redirects'] = [{'from': child if mode != 'broken_redirect' else 'https://other.example/',
                                          'to': target, 'httpStatus': 302}]
                    row['evidence'][-1]['sourceUrl'] = target
                    if mode == 'foreign_path': meta['redirects'] = []
                if mode == 'parent_identity_on_child': row['identityEvidence'] = [row['evidence'][-1]]
                if mode == 'wrong_field': row['fields']['institution'] = UCSD
                if mode == 'changed_bytes':
                    (path / 'responses' / (hashlib.sha256(child.encode()).hexdigest()+'.html')).write_text('Changed')
                with self.assertRaises(ValueError):
                    verified_own_metadata({'entries': [row]}, [], queue, path, data['labs'])

    def test_campus_root_is_not_a_lab_directory_for_research_child_ownership(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data,queue,row=self.child_fixture(path,'https://sites.ucsd.edu/index.html')
            with self.assertRaisesRegex(ValueError,'named parent'):
                verified_own_metadata({'entries':[row]},[],queue,path,data['labs'])

    def test_exact_primary_name_declaration_changes_generic_label_without_an_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp); data,queue,row,_,_=self.fixture(path)
            uri=next(iter(queue['items']));lab=data['labs'][0]
            lab.update(labWebsiteUrl=uri,labName='Jane Example — lab website')
            identity=row['identityEvidence'][0];identity['method']='reviewed_own_lab_name_declaration'
            row.update(originalLabRecord=copy.deepcopy(lab),originalLabRecordSha256=record_sha256(lab),documentLabName='Example Lab')
            row['fields']['labName']='Example Lab';row['fieldEvidence']['labName']=[identity]
            rows=verified_own_metadata({'entries':[row]},[],queue,path,data['labs'])
            first,*_=build(copy.deepcopy(data),{},{},{},{},coverage_evidence={'labOwnMetadataReviews':rows})
            self.assertEqual(first['labs'][0]['labName'],'Example Lab')
            self.assertEqual(first['labs'][0]['labWebsiteUrl'],uri)
            self.assertNotIn('websiteAliases',first['labs'][0])
            self.assertEqual(audit(data,first)['status'],'passed')
            second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence={'labOwnMetadataReviews':rows})
            self.assertEqual(first,second)
            for mode in ['wrong_name','unscoped_title','wrong_method']:
                bad=copy.deepcopy(row)
                if mode=='wrong_name':bad['fields']['labName']='Another Lab'
                if mode=='unscoped_title':bad['fieldEvidence']['labName'][0]['evidenceType']='main_text_quote'
                if mode=='wrong_method':bad['fieldEvidence']['labName'][0]['method']='arbitrary'
                with self.subTest(mode=mode),self.assertRaises(ValueError):
                    verified_own_metadata({'entries':[bad]},[],queue,path,data['labs'])

    def test_explicit_named_group_affiliation_replaces_old_department_context_but_not_people(self):
        text='Welcome to Example Lab in the Department of Chemical Engineering at the University of Rochester.'
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data,queue,row,aliases,_=self.fixture(path,text)
            claim=row['fieldEvidence']['institution'][0];claim['method']='reviewed_own_lab_group_affiliation'
            row['groupAffiliationStatement']=claim
            row['fields'].update(institution='University of Rochester',department='Chemical Engineering')
            row['fieldEvidence']['department']=[claim]
            before=copy.deepcopy(data)
            rows=verified_own_metadata({'entries':[row]},aliases,queue,path,data['labs'])
            first,*_=build(copy.deepcopy(data),{},{},{},{},coverage_evidence={'labOwnMetadataReviews':rows})
            lab=first['labs'][0]
            self.assertEqual((lab['department'],lab['institution']),('Chemical Engineering','University of Rochester'))
            self.assertEqual(lab['relationshipScope'],'reviewed_own_group_affiliation')
            self.assertEqual(first['professors'],before['professors'])
            self.assertEqual(lab['principalInvestigator'],before['labs'][0]['principalInvestigator'])
            self.assertEqual(audit(before,first)['status'],'passed')
            second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence={'labOwnMetadataReviews':rows})
            self.assertEqual(first,second)
            for mode in ['person_appointment','different_lab','different_department','missing_paired_department']:
                bad=copy.deepcopy(row)
                if mode=='person_appointment':bad['groupAffiliationStatement']['evidence']='Professor Example at the University of Rochester.'
                if mode=='different_lab':bad['groupAffiliationStatement']['evidence']=text.replace('Example Lab','Other Lab')
                if mode=='different_department':bad['fields']['department']='NanoEngineering'
                if mode=='missing_paired_department':bad['fields'].pop('department')
                with self.subTest(mode=mode),self.assertRaises(ValueError):
                    verified_own_metadata({'entries':[bad]},aliases,queue,path,data['labs'])

    def fixture(self, path, contact='Contact us Department of Medicine University of California, San Diego'):
        uri = 'https://sites.ucsd.edu/example-lab/'
        description = 'We study inflammatory airway disease.'
        body = f'<title>Example Lab</title><main><h1>Example Lab</h1><p>{description}</p><p>{contact}</p></main>'
        (path / 'responses').mkdir()
        file = path / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
        file.write_text(body)
        meta = {'sourceUrl': uri, 'finalUrl': uri, 'observedAt': '2026-10-16T12:00:00+00:00',
                'status': 'ok', 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}
        queue = {'items': {uri: {'url': uri, 'fetch': meta}}}
        def proof(text, kind='main_text_quote', method='reviewed_own_lab_research_description'):
            return {'requestedUrl': uri, 'sourceUrl': uri, 'observedAt': meta['observedAt'],
                    'bodySha256': meta['sha256'], 'evidenceType': kind, 'method': method, 'evidence': text}
        lab = make_lab('Example Lab', 'https://old.example.ucsd.edu/', 'Medicine', meta, 'Old directory entry')
        lab.update(institution='Unknown', description='Unverified profile navigation projection.')
        data = atlas(); data['professors'] = []; data['labs'] = [lab]
        identity = proof('Example Lab', 'document_title')
        alias = {'labId': lab['id'], 'url': uri, 'fieldEvidence': [identity], 'reason': 'Reviewed named own resource'}
        aliases = verified_alias_reviews({'entries': [{'labId': lab['id'], 'url': uri,
            'originalAliasRecord': alias, 'originalAliasRecordSha256': record_sha256(alias),
            'reason': alias['reason'], 'evidence': [identity]}]}, [alias], queue, path)
        affiliation = proof(contact, method='reviewed_own_lab_contact_institution')
        research = proof(description)
        row = {'labId': lab['id'], 'originalLabRecord': copy.deepcopy(lab),
               'originalLabRecordSha256': record_sha256(lab), 'reason': 'Use exact named own statements',
               'fields': {'description': description, 'institution': UCSD},
               'fieldEvidence': {'description': [research], 'institution': [affiliation]},
               'identityEvidence': [identity], 'evidence': [identity, research, affiliation]}
        return data, queue, row, aliases, alias

    def test_named_owned_statements_replace_legacy_values_losslessly_and_replay_identically(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, queue, row, aliases, alias = self.fixture(Path(tmp)); before = copy.deepcopy(data)
            rows = verified_own_metadata({'entries': [row]}, aliases, queue, Path(tmp), data['labs'])
            coverage = {'labAliases': [alias], 'labAliasResourceReviews': aliases, 'labOwnMetadataReviews': rows}
            first, *_ = build(copy.deepcopy(data), {}, {}, {}, {}, coverage_evidence=coverage)
            lab = first['labs'][0]
            self.assertEqual(lab['description'], row['fields']['description'])
            self.assertEqual(lab['institution'], UCSD)
            self.assertEqual(lab['relationshipScope'], 'reviewed_ucsd_affiliation')
            self.assertEqual(lab['labWebsiteUrl'], before['labs'][0]['labWebsiteUrl'])
            self.assertEqual(lab['lastVerified'], before['labs'][0]['lastVerified'])
            self.assertEqual(lab['labOwnMetadataReviews'][0]['originalLabRecord'], before['labs'][0])
            self.assertEqual(audit(before, first)['status'], 'passed')
            second, *_ = build(copy.deepcopy(first), {}, {}, {}, {}, coverage_evidence=coverage)
            self.assertEqual(first, second)
            self.assertEqual(data, before)

    def test_source_bytes_dates_claim_text_identity_and_role_field_cannot_be_substituted(self):
        for mode in ['date', 'hash', 'body', 'claim', 'identity', 'pi', 'unverified_alias', 'ambiguous_owner', 'alias_target']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp); data, queue, row, aliases, alias = self.fixture(path)
                if mode == 'date': row['evidence'][1]['observedAt'] = '2000-01-01'
                if mode == 'hash': row['evidence'][1]['bodySha256'] = '0' * 64
                if mode == 'body': next((path / 'responses').glob('*.html')).write_text('Changed source')
                if mode == 'claim': row['fields']['description'] = 'Invented research claim'
                if mode == 'identity': row['identityEvidence'][0]['evidenceType'] = 'main_text_quote'
                if mode == 'pi': row['fields']['principalInvestigator'] = 'Professor Example'
                if mode == 'unverified_alias': aliases[0]['captureVerified'] = False
                if mode == 'ambiguous_owner': aliases.append({'labId': 'other', 'url': alias['url'], 'captureVerified': True})
                if mode == 'alias_target':
                    data['labs'][0]['aliasIds'] = ['retired-id']; row['labId'] = 'retired-id'
                with self.assertRaises(ValueError):
                    verified_own_metadata({'entries': [row]}, aliases, queue, path, data['labs'])

    def test_institution_is_not_inferred_from_contact_email_or_a_person_appointment(self):
        for text in ['Contact us example@ucsd.edu', 'Professor at University of California, San Diego']:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp); data, queue, row, aliases, _ = self.fixture(path, text)
                with self.assertRaisesRegex(ValueError, 'explicit own contact affiliation'):
                    verified_own_metadata({'entries': [row]}, aliases, queue, path, data['labs'])

    def test_another_uri_on_same_shared_host_cannot_supply_the_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp); data, queue, row, aliases, _ = self.fixture(path)
            old = next(iter(queue['items'])); other = 'https://sites.ucsd.edu/other-lab/'
            meta = copy.deepcopy(queue['items'][old]['fetch']); meta.update(sourceUrl=other, finalUrl=other)
            queue['items'][other] = {'url': other, 'fetch': meta}
            (path / 'responses' / (hashlib.sha256(other.encode()).hexdigest() + '.html')).write_bytes(
                (path / 'responses' / (hashlib.sha256(old.encode()).hexdigest() + '.html')).read_bytes())
            for proof in row['evidence']: proof.update(requestedUrl=other, sourceUrl=other)
            with self.assertRaisesRegex(ValueError, 'exact reviewed alias'):
                verified_own_metadata({'entries': [row]}, aliases, queue, path, data['labs'])

    def test_all_targets_are_checked_before_any_record_is_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp); data, queue, row, aliases, _ = self.fixture(path)
            rows = verified_own_metadata({'entries': [row]}, aliases, queue, path, data['labs'])
            rows.append({**copy.deepcopy(rows[0]), 'labId': 'missing'})
            before = copy.deepcopy(data)
            with self.assertRaises(ValueError): apply_own_metadata(data, rows)
            self.assertEqual(data, before)

    def test_exact_current_primary_needs_no_alias_but_keeps_resource_and_old_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data,queue,row,_,_=self.fixture(path)
            uri=next(iter(queue['items']));data['labs'][0].update(labWebsiteUrl=uri,labName='Example Clinical Research Group',aliasNames=['Example Lab'])
            row['originalLabRecord']=copy.deepcopy(data['labs'][0]);row['originalLabRecordSha256']=record_sha256(row['originalLabRecord'])
            before=copy.deepcopy(data)
            rows=verified_own_metadata({'entries':[row]},[],queue,path,data['labs'])
            first,*_=build(copy.deepcopy(data),{},{},{},{},coverage_evidence={'labOwnMetadataReviews':rows})
            self.assertEqual(first['labs'][0]['description'],row['fields']['description'])
            self.assertEqual(first['labs'][0]['labWebsiteUrl'],uri)
            self.assertNotIn('websiteAliases',first['labs'][0])
            self.assertEqual(audit(before,first)['status'],'passed')
            second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence={'labOwnMetadataReviews':rows})
            self.assertEqual(first,second)
            other=copy.deepcopy(data['labs'][0]);other['id']='other-lab'
            with self.assertRaises(ValueError):verified_own_metadata({'entries':[row]},[],queue,path,data['labs']+[other])

    def test_primary_redirect_requires_its_actual_continuous_capture_and_explicit_name_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data,queue,row,_,_=self.fixture(path)
            final=next(iter(queue['items']));requested='https://sites.ucsd.edu/old-lab/'
            item=queue['items'].pop(final);item['url']=requested;item['fetch'].update(sourceUrl=requested,redirects=[{'from':requested,'to':final,'httpStatus':301}]);queue['items'][requested]=item
            (path/'responses'/(hashlib.sha256(requested.encode()).hexdigest()+'.html')).write_bytes((path/'responses'/(hashlib.sha256(final.encode()).hexdigest()+'.html')).read_bytes())
            for proof in row['evidence']:proof['requestedUrl']=requested
            lab=data['labs'][0];lab.update(labName='Jane Example — lab website',labWebsiteUrl=requested)
            row.update(originalLabRecord=copy.deepcopy(lab),originalLabRecordSha256=record_sha256(lab),documentLabName='Example Lab')
            update={'labId':lab['id'],'fields':{'labName':'Example Lab'},'fieldEvidence':{'labName':row['identityEvidence']}}
            with self.assertRaisesRegex(ValueError,'explicit reviewed name update'):verified_own_metadata({'entries':[row]},[],queue,path,data['labs'])
            rows=verified_own_metadata({'entries':[row]},[],queue,path,data['labs'],[update])
            coverage={'labUpdates':[update],'labOwnMetadataReviews':rows}
            first,*_=build(copy.deepcopy(data),{},{},{},{},coverage_evidence=coverage)
            self.assertEqual(first['labs'][0]['labName'],'Example Lab')
            self.assertEqual(first['labs'][0]['description'],row['fields']['description'])
            self.assertEqual(first['labs'][0]['labOwnMetadataReviews'][0]['originalLabRecord'],lab)
            self.assertEqual(audit(data,first)['status'],'passed')
            second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence=coverage);self.assertEqual(first,second)
            bad=copy.deepcopy(update);bad['fieldEvidence']['labName'][0]['evidenceType']='main_text_quote'
            with self.assertRaisesRegex(ValueError,'document declaration'):verified_own_metadata({'entries':[row]},[],queue,path,data['labs'],[bad])
            item['fetch']['redirects'][0]['from']='https://unrelated.ucsd.edu/'
            with self.assertRaisesRegex(ValueError,'continuous redirect'):verified_own_metadata({'entries':[row]},[],queue,path,data['labs'],[update])
