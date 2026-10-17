import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_ucsd_preservation import audit
from lab_resource_reviews import record_sha256
from professor_biography_reviews import gps_own_research_summary
from professor_own_field_reviews import verified_professor_fields,apply_professor_fields
from rebuild_verified_atlas import build,derive_research_tags
from test_atlas_quality import atlas

class ProfessorBiographyReviewTests(unittest.TestCase):
    def fixture(self,path,personal=False):
        data,*_=build(atlas(),{},{},{},{})
        person=data['professors'][0];uri='https://gps.ucsd.edu/faculty-directory/ada-lovelace.html';site='https://ada.example.org/';summary='Lovelace’s research focuses on organizational economics and worker wellbeing.';old='We study absenteeism in one firm.';paragraph='Ada Lovelace is a professor. '+summary+' She previously held another appointment.'
        body=f'<title>Ada Lovelace</title><main><h1>Ada Lovelace</h1><article id="profileTab" aria-label="Profile Tabs"><ul><li role="tab" id="tab_item-0">Profile</li></ul><div class="resp-tab-content" aria-labelledby="tab_item-0"><p>{paragraph}</p><p>More information: <a href="{site}">Personal Website</a></p><h2>Education and CV</h2><p>Unrelated research after education.</p></div></article></main>'
        (path/'responses').mkdir();queue={'items':{}}
        def capture(u,text):
            file=path/'responses'/(hashlib.sha256(u.encode()).hexdigest()+'.html');file.write_text(text);m={'sourceUrl':u,'finalUrl':u,'observedAt':'2026-10-16T12:00:00+00:00','status':'ok','sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'redirects':[]};queue['items'][u]={'url':u,'fetch':m}
            def proof(text,kind='main_text_quote',**extra):return {'requestedUrl':u,'sourceUrl':u,'observedAt':m['observedAt'],'bodySha256':m['sha256'],'evidence':text,'evidenceType':kind,'method':'reviewed_original_summary_scope',**extra}
            return proof
        campus=capture(uri,body);person.update(officialProfileUrl=uri,personalWebsiteUrl=site,researchSummary=old)
        person['fieldEvidence']['researchSummary']=[{'sourceUrl':site if personal else uri,'observedAt':'2026-10-01T00:00:00+00:00','evidence':old,'method':'identity_matched_personal_site_research_excerpt' if personal else 'official_profile_research_paragraph_excerpt'}]
        observation=gps_own_research_summary(queue['items'][uri],path,person['name'],summary)
        row={'professorId':person['id'],'sourceProfessorId':person['id'],'originalSourceProfessorRecord':copy.deepcopy(person),'originalSourceRecordSha256':record_sha256(person),'sourceTemplate':'gps_profile_tabs_biography','reason':'Use the exact own biography research statement; retain the old scoped excerpt and dates.','sourceObservation':observation,'fields':observation['fields'],'fieldEvidence':observation['fieldEvidence']}
        if personal:
            title='Absenteeism in One Firm';card=title+' '+old+' Journal of Economics, 2024.'
            publisher=capture(site,f'<title>Ada Lovelace</title><main><div class="s-item-text-group"><div class="s-item-title">{title}</div><p>{old}</p><p>Journal of Economics, 2024.</p></div></main>')
            identity=publisher('Ada Lovelace','document_title');link=campus('Personal Website -> '+site,'named_link',linkText='Personal Website',linkUrl=site);paper=publisher(card)
            row['previousSummaryScopeReview']={'kind':'single_paper_abstract','paperTitle':title,'publisherIdentityEvidence':identity,'publishedPersonalLinkEvidence':link,'paperScopeEvidence':paper,'evidence':[identity,link,paper]}
        return data,queue,row,summary

    def test_explicit_biography_summary_corrects_single_paper_scope_and_preserves_every_old_fact(self):
        for personal in [False,True]:
            with self.subTest(personal=personal),tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp);data,q,row,summary=self.fixture(path,personal);before=copy.deepcopy(data);reviews=verified_professor_fields({'entries':[row]},q,path,data['professors']);first,*_=build(copy.deepcopy(data),{},{},{},{},coverage_evidence={'reviewedProfessorFieldUpdates':reviews})
                person=first['professors'][0];self.assertEqual(person['researchSummary'],summary)
                for f in ['id','name','department','officialProfileUrl','personalWebsiteUrl','researchAreas','recruitingStatus','lastVerified']:self.assertEqual(person[f],before['professors'][0][f])
                self.assertEqual(person['professorFieldReviews'][0]['originalSourceProfessorRecord'],before['professors'][0]);self.assertEqual(audit(before,first)['status'],'passed');second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence={'reviewedProfessorFieldUpdates':reviews});self.assertEqual(first,second);self.assertEqual(data,before)

    def test_named_profile_biography_tab_and_sentence_scope_exclude_publications_news_and_appointments(self):
        for mode in ['h1','title','no_tab','conflicting_tab','intro','education','appointment','partial','unpublished','other_person_research','bytes','foreign','redirect']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp);data,q,row,summary=self.fixture(path);item=q['items'][data['professors'][0]['officialProfileUrl']];file=path/'responses'/(hashlib.sha256(item['url'].encode()).hexdigest()+'.html');s=file.read_text()
                if mode=='h1':s=s.replace('<h1>Ada Lovelace</h1>','<h1>Other Person</h1>')
                if mode=='title':s=s.replace('<title>Ada Lovelace</title>','<title>Other Person</title>')
                if mode=='no_tab':s=s.replace('Profile Tabs','Publications')
                if mode=='conflicting_tab':s=s.replace('</article>','<div class="resp-tab-content" aria-labelledby="tab_item-0"><p>Other research</p></div></article>')
                if mode=='intro':s=s.replace('Ada Lovelace is a professor.','Another Person is a professor.')
                if mode=='education':summary='Unrelated research after education.'
                if mode=='appointment':summary='Ada Lovelace is a professor. '+summary
                if mode=='partial':summary=summary[5:]
                if mode=='unpublished':summary='Lovelace’s research studies an invented topic.'
                if mode=='other_person_research':
                    s=s.replace(summary,'Another Person’s research focuses on organizational economics and worker wellbeing.');summary='Another Person’s research focuses on organizational economics and worker wellbeing.'
                if mode=='foreign':item['fetch']['finalUrl']='https://other.ucsd.edu/faculty-directory/ada-lovelace.html'
                if mode=='redirect':item['fetch']['redirects']=[{'from':'https://unrelated.example/','to':item['url'],'httpStatus':302}]
                file.write_text(s+'changed' if mode=='bytes' else s)
                if mode!='bytes':item['fetch']['sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
                with self.assertRaises(ValueError):gps_own_research_summary(item,path,data['professors'][0]['name'],summary)

    def test_personal_summary_override_needs_exact_paper_card_identity_and_published_resource(self):
        for mode in ['missing','wrong_paper','whole_publications','wrong_owner','wrong_link','wrong_old_value','date','hash','ambiguous_card']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp);data,q,row,_=self.fixture(path,True);scope=row['previousSummaryScopeReview'];site=data['professors'][0]['personalWebsiteUrl'];file=path/'responses'/(hashlib.sha256(site.encode()).hexdigest()+'.html')
                if mode=='missing':row.pop('previousSummaryScopeReview')
                if mode=='wrong_paper':scope['paperTitle']='Other paper'
                if mode=='whole_publications':
                    file.write_text(file.read_text().replace('class="s-item-text-group"','class="publications"'));q['items'][site]['fetch']['sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
                if mode=='wrong_owner':scope['publisherIdentityEvidence']['evidence']='Other Person'
                if mode=='wrong_link':scope['publishedPersonalLinkEvidence']['linkUrl']='https://other.example/'
                if mode=='wrong_old_value':data['professors'][0]['researchSummary']='Another old value'
                if mode=='date':scope['paperScopeEvidence']['observedAt']='2000-01-01'
                if mode=='hash':scope['publisherIdentityEvidence']['bodySha256']='0'*64
                if mode=='ambiguous_card':file.write_text(file.read_text()*2);q['items'][site]['fetch']['sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
                with self.assertRaises(ValueError):verified_professor_fields({'entries':[row]},q,path,data['professors'])

    def test_old_review_cannot_replace_a_newer_or_different_personal_summary(self):
        for mode in ['newer','different']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp);data,q,row,_=self.fixture(path,True);reviews=verified_professor_fields({'entries':[row]},q,path,data['professors']);person=data['professors'][0]
                if mode=='newer':person['fieldEvidence']['researchSummary'][0]['observedAt']='2026-10-17T12:00:00+00:00'
                else:person['researchSummary']='Different subsequently reviewed personal research summary.'
                old=copy.deepcopy(person);apply_professor_fields(data,reviews);self.assertEqual(person['researchSummary'],old['researchSummary']);self.assertEqual(person['fieldEvidence']['researchSummary'],old['fieldEvidence']['researchSummary']);self.assertEqual(len(person['professorFieldReviews']),1)

    def test_explicit_portfolio_enumeration_supplies_only_literal_fields_and_keeps_compound_lists_unparsed(self):
        for compound in [False,True]:
            with self.subTest(compound=compound),tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp);data,q,row,old=self.fixture(path,True);uri=data['professors'][0]['officialProfileUrl'];item=q['items'][uri];file=path/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html')
                terms=['development economics','organizational economics','labor economics','health economics']
                statement='Lovelace’s research portfolio spans the fields of '+', '.join(terms[:-1])+' and '+terms[-1]+'.'
                if compound:statement=statement.replace('organizational economics','law and economics')
                file.write_text(file.read_text().replace(old,statement));item['fetch']['sha256']=hashlib.sha256(file.read_bytes()).hexdigest();actual=gps_own_research_summary(item,path,data['professors'][0]['name'],statement)
                if compound:self.assertNotIn('researchAreas',actual['fields'])
                else:
                    self.assertEqual(actual['fields']['researchAreas'],terms)
                    row.update(sourceObservation=actual,fields=actual['fields'],fieldEvidence=actual['fieldEvidence'])
                    link=row['previousSummaryScopeReview']['publishedPersonalLinkEvidence'];link['bodySha256']=item['fetch']['sha256']
                    reviews=verified_professor_fields({'entries':[row]},q,path,data['professors']);original=copy.deepcopy(data);apply_professor_fields(data,reviews)
                    self.assertEqual(data['professors'][0]['researchAreas'],terms);self.assertEqual(data['professors'][0]['researchSummary'],statement)
                    first,*_=build(original,{},{},{},{},coverage_evidence={'reviewedProfessorFieldUpdates':reviews})
                    second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence={'reviewedProfessorFieldUpdates':reviews})
                    self.assertEqual(first['professors'][0]['researchAreas'],terms);self.assertEqual(first,second)

    def test_unverified_embedded_labels_do_not_bypass_normal_tag_derivation(self):
        record={'researchSummary':'Research in labor economics.','researchAreas':['Invented topic'],
                'fieldEvidence':{'researchSummary':[{'sourceUrl':'https://gps.ucsd.edu/example','observedAt':'2026-10-16','evidence':'Research in labor economics.'}],'researchAreas':[{'evidence':'Invented topic'}]},
                'professorFieldReviews':[{'captureVerified':False,'fields':{'researchAreas':['Invented topic']},'fieldEvidence':{'researchAreas':[{'evidence':'Invented topic'}]}}]}
        derive_research_tags(record);self.assertEqual(record['researchAreas'],['Labor economics'])

    def test_newer_explicit_directory_labels_are_not_hidden_by_an_older_own_field_review(self):
        old={'sourceUrl':'https://gps.ucsd.edu/ada','observedAt':'2026-10-16T00:00:00+00:00','evidence':'Explicit own field: development economics'}
        new={'sourceUrl':'https://gps.ucsd.edu/faculty','observedAt':'2026-10-17T00:00:00+00:00','evidence':'Explicit directory field: Ecology'}
        record={'researchSummary':'Not found','researchAreas':['development economics'],'researchAreasFromDirectory':['Ecology'],
                'fieldEvidence':{'researchAreas':[old],'researchAreasFromDirectory':[new]},
                'professorFieldReviews':[{'captureVerified':True,'fields':{'researchAreas':['development economics']},'fieldEvidence':{'researchAreas':[old]}}]}
        derive_research_tags(record);self.assertEqual(record['researchAreas'],['Ecology'])
