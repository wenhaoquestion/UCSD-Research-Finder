import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_ucsd_preservation import audit
from lab_entities import LabIndex
from lab_own_metadata import verified_own_metadata,apply_own_metadata
from lab_preferred_resources import verified_preferred_resources
from lab_resource_reviews import record_sha256
from published_organization_resources import verified_published_organizations,attach_published_organization_aliases
from rebuild_verified_atlas import build
from refresh_labs import make_lab
from test_atlas_quality import atlas

class PublishedOrganizationResourcesTests(unittest.TestCase):
    def fixture(self,path):
        data,*_=build(atlas(),{},{},{},{})
        person=data['professors'][0];campus=person['officialProfileUrl'];publisher='https://ada.example.org/';requested='http://www.foundation.example.org/';new='https://foundation.example.org/'
        queue={'items':{}};(path/'responses').mkdir()
        def capture(uri,body,final=None):
            file=path/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');file.write_text(body)
            meta={'sourceUrl':uri,'finalUrl':final or uri,'observedAt':'2026-10-16T12:00:00+00:00','status':'ok','httpStatus':200,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'redirects':[]}
            if final:meta['redirects']=[{'from':uri,'to':final,'httpStatus':308}]
            queue['items'][uri]={'url':uri,'fetch':meta}
            def proof(text,kind='main_text_quote',**extra):
                return {'requestedUrl':uri,'sourceUrl':meta['finalUrl'],'observedAt':meta['observedAt'],'bodySha256':meta['sha256'],'evidenceType':kind,'method':'reviewed_published_organization_resource','evidence':text,**extra}
            return proof
        association='She is also the co-founder of Example Foundation, a global nonprofit.'
        p=capture(campus,f'<title>Ada Lovelace</title><main><h1>Ada Lovelace</h1><p>{association}</p><a href="{publisher}">Personal Website</a></main>')
        s=capture(publisher,f'<title>Ada Lovelace</title><main><h1>Example Foundation</h1><a href="{requested}">Example Foundation</a><p>Unrelated paper abstract.</p></main>')
        mission='Example Foundation is a global NGO that improves worker wellbeing.'
        o=capture(requested,f'<title>Example Foundation</title><main><h1>Worker wellbeing</h1><p>{mission}</p></main>',new)
        lab=make_lab('Example Foundation',publisher,'Computer Science and Engineering',queue['items'][publisher]['fetch'],'Old profile link')
        lab.update(institution='Unknown',professorIds=[person['id']],description='Unrelated paper abstract.',relationshipScope='institution_not_confirmed')
        lab['fieldEvidence']={'labName':[s('Example Foundation','document_heading',headingTag='h1')],'labWebsiteUrl':[s('Example Foundation','document_heading',headingTag='h1')]}
        person.update(personalWebsiteUrl=publisher,labAffiliation=lab['labName'],labAffiliationUrl=publisher,labAffiliations=[{'labId':lab['id'],'labName':lab['labName'],'url':publisher,'relationship':'faculty_lab_link','fieldEvidence':copy.deepcopy(lab['fieldEvidence']['labName'])}])
        data['labs']=[lab]
        named_person=p('Ada Lovelace','document_heading',headingTag='h1');named_publisher=s('Ada Lovelace','document_title');named_org=o('Example Foundation','document_title');personal_link=p('Personal Website -> '+publisher,'named_link',linkText='Personal Website',linkUrl=publisher);org_link=s('Example Foundation -> '+requested,'named_link',linkText='Example Foundation',linkUrl=requested);associated=p(association)
        row={'labId':lab['id'],'professorId':person['id'],'action':'register_published_organization_resource','originalLabRecord':copy.deepcopy(lab),'originalLabRecordSha256':record_sha256(lab),'originalProfessorRecord':copy.deepcopy(person),'originalProfessorRecordSha256':record_sha256(person),'originalPersonIdentityEvidence':named_person,'publisherIdentityEvidence':named_publisher,'organizationIdentityEvidence':named_org,'publishedPersonalLinkEvidence':personal_link,'publishedOrganizationLinkEvidence':org_link,'associationEvidence':associated,'evidence':[named_person,personal_link,associated,named_publisher,org_link,named_org],'reason':'Exact original campus-person/personal/named-organization publisher chain; no new identity or role.'}
        typed=o(mission);typed['method']='reviewed_own_organization_type';desc=o(mission);desc['method']='reviewed_own_organization_description'
        metadata={'labId':lab['id'],'originalLabRecord':copy.deepcopy(lab),'originalLabRecordSha256':record_sha256(lab),'fields':{'recordSubtype':'ngo','description':mission},'fieldEvidence':{'recordSubtype':[typed],'description':[desc]},'identityEvidence':[named_org],'evidence':[named_org,typed,desc],'reason':'Use the explicit own NGO type and mission; preserve old faculty routing context without treating it as an organization department.'}
        preferred={'labId':lab['id'],'action':'select_preferred_lab_resource','previousPreferredUrl':publisher,'preferredUrl':new,'originalLabRecord':copy.deepcopy(lab),'originalLabRecordSha256':record_sha256(lab),'identityEvidence':[named_org],'evidence':row['evidence'],'reason':row['reason']}
        return data,queue,row,metadata,preferred

    def verified(self,path,data,queue,row):
        return verified_published_organizations({'entries':[row]},queue,path,data['labs'],data['professors'])

    def test_official_publisher_chain_selects_real_ngo_resource_and_preserves_originals_on_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data,q,row,metadata,preferred=self.fixture(path);before=copy.deepcopy(data);rows=self.verified(path,data,q,row)
            coverage={'labAliases':[],'labAliasResourceReviews':[]};attach_published_organization_aliases(coverage,rows)
            aliases=coverage['labAliasResourceReviews'];coverage['labOwnMetadataReviews']=verified_own_metadata({'entries':[metadata]},aliases,q,path,data['labs']);coverage['labPreferredResourceReviews']=verified_preferred_resources({'entries':[preferred]},aliases,q,path,data['labs'])
            first,*_=build(copy.deepcopy(data),{},{},{},{},coverage_evidence=coverage);lab=first['labs'][0];person=first['professors'][0]
            self.assertEqual(lab['id'],before['labs'][0]['id']);self.assertEqual(lab['recordSubtype'],'ngo');self.assertEqual(lab['department'],'Unknown');self.assertEqual(lab['institution'],'Unknown');self.assertEqual(lab['description'],metadata['fields']['description']);self.assertEqual(lab['labWebsiteUrl'],preferred['preferredUrl'])
            self.assertEqual(lab['principalInvestigator'],before['labs'][0]['principalInvestigator']);self.assertEqual(lab['professorIds'],before['labs'][0]['professorIds']);self.assertEqual(lab['lastVerified'],before['labs'][0]['lastVerified']);self.assertEqual(person['officialProfileUrl'],before['professors'][0]['officialProfileUrl']);self.assertEqual(person['personalWebsiteUrl'],before['professors'][0]['personalWebsiteUrl'])
            self.assertEqual(person['labAffiliationUrl'],preferred['preferredUrl']);self.assertEqual(person['labAffiliations'][0]['relationship'],'faculty_organization_link');self.assertEqual(person['labAffiliations'][0]['recordSubtype'],'ngo')
            self.assertEqual(lab['labOwnMetadataReviews'][-1]['originalLabRecord'],before['labs'][0]);self.assertEqual(lab['preferredResourceReviews'][-1]['originalLabRecord'],before['labs'][0]);self.assertIsNone(LabIndex(first['labs']).resolve(preferred['previousPreferredUrl']));self.assertEqual(audit(before,first)['status'],'passed')
            second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence=coverage);self.assertEqual(first,second);self.assertEqual(data,before)

    def test_resource_requires_actual_original_person_named_links_and_redirects(self):
        for mode in ['no_association','other_person','unpublished_personal','unnamed_org_link','wrong_org','different_date','changed_bytes','metadata_hash','missing_redirect','redirect_escape','already_owned','not_official','changed_snapshot']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp);data,q,row,_,_=self.fixture(path)
                if mode=='no_association':data['labs'][0]['professorIds']=[]
                if mode=='other_person':row['professorId']='different-person'
                if mode=='unpublished_personal':row['publishedPersonalLinkEvidence']['linkUrl']='https://unpublished.example/'
                if mode=='unnamed_org_link':row['publishedOrganizationLinkEvidence']['linkText']='Other organization'
                if mode=='wrong_org':row['organizationIdentityEvidence']['evidence']='Other Foundation'
                if mode=='different_date':row['evidence'][0]['observedAt']='2000-01-01'
                if mode=='changed_bytes':next((path/'responses').glob('*.html')).write_text('Changed source')
                requested=row['publishedOrganizationLinkEvidence']['linkUrl']
                if mode=='metadata_hash':q['items'][requested]['fetch']['sha256']='0'*64
                if mode=='missing_redirect':q['items'][requested]['fetch']['redirects']=[]
                if mode=='redirect_escape':q['items'][requested]['fetch']['redirects'][0]['from']='https://unrelated.example/'
                if mode=='already_owned':data['labs'].append(dict(copy.deepcopy(data['labs'][0]),id='different-lab',labWebsiteUrl=row['organizationIdentityEvidence']['sourceUrl']))
                if mode=='not_official':data['professors'][0]['officialProfileUrl']='https://external.example/ada'
                if mode=='changed_snapshot':row['originalLabRecord']['description']='Changed old record'
                with self.assertRaises(ValueError):self.verified(path,data,q,row)

    def test_ngo_type_cannot_override_verified_institution_department_or_invent_mission(self):
        for mode in ['institution','department','not_ngo','non_ngo_quote','invented_description','pi']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp);data,q,row,metadata,_=self.fixture(path);rows=self.verified(path,data,q,row);aliases=[rows[0]['resourceAliasReview']]
                if mode=='institution':data['labs'][0]['institution']='University of California San Diego'
                if mode=='department':data['labs'][0]['fieldEvidence']['department']=[copy.deepcopy(metadata['evidence'][1])]
                if mode=='not_ngo':metadata['fields']['recordSubtype']='lab'
                if mode=='non_ngo_quote':metadata['fieldEvidence']['recordSubtype'][0]['evidence']='Example Foundation'
                if mode=='invented_description':metadata['fields']['description']='A UCSD academic laboratory.'
                if mode=='pi':metadata['fields']['principalInvestigator']='Ada Lovelace'
                with self.assertRaises(ValueError):verified_own_metadata({'entries':[metadata]},aliases,q,path,data['labs'])

    def test_alias_attachment_rejects_unverified_or_duplicate_resource_before_any_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data,q,row,_,_=self.fixture(path);rows=self.verified(path,data,q,row)
            for mode in ['unverified','duplicate']:
                bad=copy.deepcopy(rows);coverage={'labAliases':[],'labAliasResourceReviews':[]}
                if mode=='unverified':bad[0]['captureVerified']=False
                else:coverage['labAliases']=[copy.deepcopy(rows[0]['resourceAlias'])]
                before=copy.deepcopy(coverage)
                with self.assertRaises(ValueError):attach_published_organization_aliases(coverage,bad)
                self.assertEqual(coverage,before)

    def test_old_ngo_routing_review_does_not_clear_a_subsequent_verified_department(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data,q,row,metadata,_=self.fixture(path);resources=self.verified(path,data,q,row)
            reviews=verified_own_metadata({'entries':[metadata]},[resources[0]['resourceAliasReview']],q,path,data['labs'])
            lab=data['labs'][0];proof={'sourceUrl':'https://foundation.example.org/units','observedAt':'2026-10-17T12:00:00+00:00','evidence':'New verified organizational unit'}
            lab['department']='Worker Wellbeing';lab['fieldEvidence']['department']=[proof]
            apply_own_metadata(data,reviews)
            self.assertEqual(lab['department'],'Worker Wellbeing');self.assertEqual(lab['fieldEvidence']['department'],[proof])
