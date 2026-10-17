"""An additional source needs named personal identifiers and an exact actual feed link."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import test_professor_own_field_reviews as own_fixtures
from professor_own_field_reviews import math_own_fields, additional_math_source_identity, verified_professor_fields, apply_professor_fields
from lab_resource_reviews import record_sha256


class AdditionalMathSourceTests(unittest.TestCase):
    def fixture(self, cache):
        item, path, person = own_fixtures.ProfessorOwnFieldTests().fixture(cache)
        person.update(officialProfileUrl=item['url'].replace('https://math.', 'https://www.math.'),
                      email='jexample@ucsd.edu', personalWebsiteUrl='https://math.ucsd.edu/~jexample/')
        publisher='https://soeapp.ucsd.edu/tools/eah/department.php'
        common={'sourceUrl':publisher,'observedAt':'2026-10-01T00:00:00Z','status':'verified'}
        person['fieldEvidence']={'name':[{**common,'method':'official_directory_public_feed_rendering_rules','evidence':'Mathematics directory | Jane A. Example | Professor'}],
            'email':[{**common,'method':'explicit_person_card_value','evidence':'Jane A. Example | email: jexample@ucsd.edu'}],
            'personalWebsiteUrl':[{**common,'method':'explicit_person_card_value','evidence':'Jane A. Example | personalWebsiteUrl: https://math.ucsd.edu/~jexample/'}]}
        uri='https://math.ucsd.edu/export/people/faculty'
        raw=[{'nid_1':'123','field_work_email':person['email'],'field_website':person['personalWebsiteUrl'],'view_node_1':'/people/profiles/jane-example'}]
        fp=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');fp.write_text(json.dumps(raw))
        feed={'url':uri,'state':'done','fetch':{'sourceUrl':uri,'finalUrl':uri,'status':'ok','observedAt':'2026-10-16T01:00:00Z','sha256':hashlib.sha256(fp.read_bytes()).hexdigest()}}
        actual=math_own_fields(item,cache,person['name']);owners={'email':{person['email']:{person['id']}},'personalWebsiteUrl':{person['personalWebsiteUrl']:{person['id']}}}
        identity=additional_math_source_identity(person,actual,feed,cache,owners,person['id'])
        row={'sourceProfessorId':person['id'],'professorId':person['id'],'reason':'Associate the additional named source using its explicit personal contacts and literal directory link.',
             'originalSourceProfessorRecord':copy.deepcopy(person),'originalSourceRecordSha256':record_sha256(person),
             'sourceObservation':actual,'fields':actual['fields'],'fieldEvidence':actual['fieldEvidence'],'additionalSourceIdentity':identity}
        failed={'url':person['officialProfileUrl'],'state':'unresolved','attempts':3,'fetch':{'sourceUrl':person['officialProfileUrl'],'status':'fetch_error','observedAt':'2026-10-16T02:00:00Z'},'attemptHistory':[{'status':'fetch_error'}]}
        return person,{'items':{item['url']:item,uri:feed,failed['url']:failed}},{'entries':[row]},fp

    def test_additional_source_uses_same_id_preserves_failed_primary_and_never_claims_uri_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,queue,review,_=self.fixture(cache);before=copy.deepcopy((person,queue,review))
            rows=verified_professor_fields(review,queue,cache,[person]);data={'professors':[copy.deepcopy(person)]};apply_professor_fields(data,rows);result=data['professors'][0]
            self.assertEqual(result['id'],person['id']);self.assertEqual(result['officialProfileUrl'],person['officialProfileUrl'])
            self.assertEqual(result['name'],person['name']);self.assertEqual(result['department'],person['department']);self.assertEqual(result['lastVerified'],person['lastVerified'])
            self.assertEqual(result['researchAreas'],['Algebra','Groups']);self.assertEqual(result['email'],person['email'])
            self.assertNotIn('aliasIds',result);self.assertNotIn('alternateProfileUrls',result)
            self.assertIn('https://math.ucsd.edu/people/profiles/jane-example',result['sourceUrls'])
            self.assertIn('https://math.ucsd.edu/export/people/faculty',result['sourceUrls'])
            once=copy.deepcopy(data);apply_professor_fields(data,rows);self.assertEqual(data,once);self.assertEqual((person,queue,review),before)

    def test_shared_email_website_or_already_owned_source_cannot_attach_to_another_identity(self):
        for field in ['email','personalWebsiteUrl','officialProfileUrl']:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);person,queue,review,_=self.fixture(cache);other={**copy.deepcopy(person),'id':'another-original-id','name':'Another Person','officialProfileUrl':'https://math.ucsd.edu/people/profiles/another'}
                other['email']='other@ucsd.edu';other['personalWebsiteUrl']='https://math.ucsd.edu/~other/'
                other[field]=review['entries'][0]['additionalSourceIdentity']['requestedUrl'] if field=='officialProfileUrl' else person[field]
                with self.assertRaises(ValueError):verified_professor_fields(review,queue,cache,[person,other])

    def test_older_anchors_must_be_dated_verified_and_in_the_same_named_card(self):
        for mode in ['email_unverified','website_missing','name_date_changed','wrong_card_name']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);person,queue,review,_=self.fixture(cache)
                if mode=='email_unverified':person['fieldEvidence']['email'][0]['status']='legacy_unverified'
                if mode=='website_missing':person['fieldEvidence'].pop('personalWebsiteUrl')
                if mode=='name_date_changed':person['fieldEvidence']['name'][0]['observedAt']='2020-01-01'
                if mode=='wrong_card_name':person['fieldEvidence']['name'][0]['evidence']='Mathematics directory | Another Person | Professor'
                review['entries'][0]['originalSourceProfessorRecord']=copy.deepcopy(person);review['entries'][0]['originalSourceRecordSha256']=record_sha256(person)
                with self.assertRaises(ValueError):verified_professor_fields(review,queue,cache,[person])

    def test_feed_must_publish_literal_uri_and_both_contacts_without_any_host_repair(self):
        for mode in ['www_variant','different_email','different_website','duplicate_email','changed_bytes']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);person,queue,review,fp=self.fixture(cache);raw=json.loads(fp.read_text())
                if mode=='www_variant':raw[0]['view_node_1']='https://www.math.ucsd.edu/people/profiles/jane-example'
                if mode=='different_email':raw[0]['field_work_email']='another@ucsd.edu'
                if mode=='different_website':raw[0]['field_website']='https://math.ucsd.edu/~another/'
                if mode=='duplicate_email':raw.append({**raw[0],'view_node_1':'/people/profiles/another'})
                fp.write_text(json.dumps(raw)+' ')
                if mode!='changed_bytes':
                    feed=queue['items']['https://math.ucsd.edu/export/people/faculty'];feed['fetch']['sha256']=hashlib.sha256(fp.read_bytes()).hexdigest()
                    review['entries'][0]['additionalSourceIdentity']['directoryCapture']['bodySha256']=feed['fetch']['sha256']
                    review['entries'][0]['additionalSourceIdentity']['directoryRow']=raw[0]
                with self.assertRaises(ValueError):verified_professor_fields(review,queue,cache,[person])

    def test_declared_additional_binding_and_subject_must_equal_actual_sources(self):
        for mode in ['changed_binding_type','wrong_source_name','missing_feed','changed_capture_date']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);person,queue,review,_=self.fixture(cache);row=review['entries'][0]
                if mode=='changed_binding_type':row['additionalSourceIdentity']['type']='inferred_www_alias'
                if mode=='wrong_source_name':person['name']='Janet Example';row['originalSourceProfessorRecord']=copy.deepcopy(person);row['originalSourceRecordSha256']=record_sha256(person)
                if mode=='missing_feed':queue['items'].pop('https://math.ucsd.edu/export/people/faculty')
                if mode=='changed_capture_date':row['sourceObservation']['capture']['observedAt']='2020-01-01'
                with self.assertRaises(ValueError):verified_professor_fields(review,queue,cache,[person])
