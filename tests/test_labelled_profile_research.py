import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from labelled_profile_research import BIOLOGY,JACOBS,SUBJECT_CONTINUITY,labelled_research,reviewed_subject
from professor_own_field_reviews import verified_professor_fields,apply_professor_fields
from lab_resource_reviews import record_sha256
from rebuild_verified_atlas import build
from test_atlas_quality import atlas,professor


class LabelledProfileResearchTests(unittest.TestCase):
    def fixture(self,cache,template=BIOLOGY):
        name='Jane Example'
        summary=('The Example lab studies pancreatic cancer using organoid models. ' +
                 'Our experiments identify therapeutic targets and characterize disease mechanisms in tissue. '*15).strip()
        uri='https://biology.ucsd.edu/research/faculty/jexample' if template==BIOLOGY else 'https://jacobsschool.ucsd.edu/faculty/profile?id=172'
        if template==BIOLOGY:
            markup='<title>Jane Example</title><main><h1 id="facName">Jane Example</h1><div id="research" class="tab-pane active" role="tabpanel"><h2>Research</h2><p>'+summary+'</p></div><div id="biography"><h2>Biography</h2><p>Jane trained at a Research Institute. Biography-only invented topic.</p></div><div id="publications"><h2>Select Publications</h2><p>Another Person studies borrowed topics.</p></div></main>'
            department='Biological Sciences';phrases=['pancreatic cancer']
        else:
            summary='Professor Example’s research is in seismic design and testing of steel structures. '+summary
            markup='<title>Faculty Profiles | Jacobs School</title><main><div class="col-9"><h3 class="faculty_profile_name">Jane Example</h3><p class="mb-5">Professor, SE</p><hr><div class="mt-5 font-weight-bold"><p><p>Earthquake engineering, seismic analysis and steel structures.</p></p></div><div class="mb-5"><p><p>'+summary+'</p></p></div><div class="mb-5"><p class="font-weight-bold">Capsule Bio:</p><p>Jane joined a Research Institute and won teaching awards.</p></div></div></main>'
            department='Structural Engineering';phrases=None
        path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.parent.mkdir();path.write_text(markup)
        item={'url':uri,'fetch':{'sourceUrl':uri,'finalUrl':uri,'observedAt':'2026-10-16T01:00:00+00:00','status':'ok','httpStatus':200,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}
        person=professor('original-id',name,department);person.update(officialProfileUrl=uri,researchSummary='Old career excerpt with no own research description.',researchAreas=['Old inferred topic'])
        person['teaching']={'status':'not_checked','lastChecked':None,'courses':[]}
        person['ratings']={key:{'platform':platform,'status':'not_checked','score':None,'scale':5,'reviewCount':None,'sourceUrl':None,'observedAt':None} for key,platform in [('rateMyPI','PI Review'),('rateMyProfessors','Rate My Professors')]}
        person['fieldEvidence']={'researchSummary':[{'sourceUrl':uri,'observedAt':'2020-01-01','method':'old_career_excerpt','evidence':person['researchSummary']}],
                                 'researchAreas':[{'sourceUrl':uri,'observedAt':'2020-01-01','method':'old_career_topic','evidence':'Old inferred topic'}]}
        actual=labelled_research(item,cache,name,template,phrases)
        row={'professorId':person['id'],'sourceProfessorId':person['id'],'originalSourceProfessorRecord':copy.deepcopy(person),
             'originalSourceRecordSha256':record_sha256(person),'previousCompiledProfessorRecord':copy.deepcopy(person),
             'previousCompiledProfessorRecordSha256':record_sha256(person),'sourceCandidateAtlasSha256':'a'*64,
             'sourceTemplate':template,'reason':'Use the own Research section instead of a career-only Research Institute substring.',
             'sourceObservation':actual,'fields':actual['fields'],'fieldEvidence':actual['fieldEvidence']}
        if phrases is not None:row['reviewedResearchPhrases']=phrases
        return person,item,row,path,summary

    def test_complete_biology_research_excludes_career_and_publications_and_rebuilds_losslessly(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,item,row,_,summary=self.fixture(cache);baseline=copy.deepcopy(person)
            reviews=verified_professor_fields({'entries':[row]},{'items':{'own':item}},cache,[person])
            data=atlas();data.update(qualityMigrationVersion=1,professors=[person])
            first,*_=build(copy.deepcopy(data),{},{},{},{},{},{},{},{'reviewedProfessorFieldUpdates':reviews})
            result=first['professors'][0]
            self.assertEqual(result['researchSummary'],summary);self.assertGreater(len(summary),1000)
            self.assertEqual(result['researchAreas'],['pancreatic cancer'])
            self.assertNotIn('Biography-only invented topic',str(row['fields']))
            self.assertNotIn('Another Person',str(row['fields']))
            for key in ['id','name','department','officialProfileUrl','appointmentStatus','lastVerified','ratings','teaching']:
                self.assertEqual(result.get(key),baseline.get(key),key)
            self.assertTrue(any(x.get('field')=='labelledResearchPreviousCandidate' and x.get('value')==baseline for x in result['previousFieldObservations']))
            repeated,*_=build(copy.deepcopy(first),{},{},{},{},{},{},{},{'reviewedProfessorFieldUpdates':reviews});self.assertEqual(first,repeated)

    def test_jacobs_uses_own_focus_and_research_before_capsule_bio_not_awards(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,item,row,_,summary=self.fixture(cache,JACOBS)
            actual=labelled_research(item,cache,person['name'],JACOBS)
            self.assertEqual(actual['fields']['researchSummary'],summary)
            self.assertEqual(actual['fields']['researchAreas'],['Earthquake engineering, seismic analysis and steel structures.'])
            self.assertNotIn('teaching awards',str(actual['fields']))
            reviews=verified_professor_fields({'entries':[row]},{'items':{'own':item}},cache,[person]);data={'professors':[person]};apply_professor_fields(data,reviews)
            self.assertEqual(person['researchSummary'],summary)
            once=copy.deepcopy(data);apply_professor_fields(data,reviews);self.assertEqual(data,once)

    def test_biology_wrong_or_duplicate_subject_tab_labels_and_borrowed_sections_fail_closed(self):
        changes=[('id="facName">Jane Example','id="facName">Another Person'),('<h2>Research</h2>','<h2>Biography</h2>'),
                 ('id="research"','id="publications-actually"'),('role="tabpanel"','role="other"'),
                 ('</main>','<h1 id="facName">Jane Example</h1></main>'),
                 ('<p>The Example lab studies','<h3>Another Person</h3><p>The Example lab studies')]
        for old,new in changes:
            with self.subTest(change=new),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);person,item,_,path,_=self.fixture(cache);path.write_text(path.read_text().replace(old,new));item['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                with self.assertRaises(ValueError):labelled_research(item,cache,person['name'],BIOLOGY,['pancreatic cancer'])

    def test_only_exact_bounded_literal_own_research_phrases_can_be_selected(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,item,_,_,_=self.fixture(cache)
            for phrases in [None,[],['Biography-only invented topic'],['canc'],['pancreatic cancer','pancreatic cancer'],['invented treatment']]:
                with self.subTest(phrases=phrases),self.assertRaises(ValueError):labelled_research(item,cache,person['name'],BIOLOGY,phrases)

    def test_complete_direct_research_paragraphs_exclude_figure_caption_containers(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,item,_,path,summary=self.fixture(cache)
            second='Our lab uses chemical genetics to investigate signaling pathways and stem cell decisions.'
            path.write_text(path.read_text().replace('</p></div><div id="biography">',
                '</p><p>'+second+'</p><div>Figure 2. Illustration caption only.</div></div><div id="biography">'))
            item['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            actual=labelled_research(item,cache,person['name'],BIOLOGY,['pancreatic cancer'])
            self.assertEqual(actual['fields']['researchSummary'],summary+' '+second)
            self.assertNotIn('Illustration caption',actual['fields']['researchSummary'])
            self.assertEqual(actual['sectionScope']['paragraphCount'],2)

    def test_jacobs_own_subject_role_and_bio_boundary_cannot_be_replaced_by_nearby_text(self):
        changes=[('faculty_profile_name','other-subject'),('Professor, SE','Industry Partner, SE'),('Capsule Bio:','Research:'),
                 ('Professor Example’s research','Professor Another’s research'),
                 ('<div class="mt-5 font-weight-bold"><p><p>Earthquake','<div class="other"><p><p>Earthquake')]
        for old,new in changes:
            with self.subTest(change=new),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);person,item,_,path,_=self.fixture(cache,JACOBS);path.write_text(path.read_text().replace(old,new));item['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                with self.assertRaises(ValueError):labelled_research(item,cache,person['name'],JACOBS)

    def test_stale_body_date_review_values_or_preceding_identity_snapshot_are_rejected(self):
        for mode in ['bytes','date','value','snapshot','primary','additional']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);person,item,row,path,_=self.fixture(cache)
                if mode=='bytes':path.write_text(path.read_text()+'changed')
                if mode=='date':item['fetch']['observedAt']='2026-10-17T00:00:00+00:00'
                if mode=='value':row['fields']['researchSummary']='Invented summary'
                if mode=='snapshot':row['previousCompiledProfessorRecord']['name']='Another Person'
                if mode=='primary':row['previousCompiledProfessorRecord']['officialProfileUrl']='https://profiles.ucsd.edu/jane.example'
                if mode=='additional':row['additionalSourceIdentity']={'requestedUrl':item['url']}
                with self.assertRaises(ValueError):verified_professor_fields({'entries':[row]},{'items':{'own':item}},cache,[person])

    def test_original_resource_field_subject_can_omit_one_reviewed_initial_without_renaming_or_aliasing(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,item,row,path,_=self.fixture(cache)
            path.write_text(path.read_text().replace('Jane Example','Jane Alice Example'))
            item['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            person['name']='Jane Alice A. Example'
            continuity={'kind':SUBJECT_CONTINUITY,'nameAsDisplayed':'Jane Alice Example'}
            selected=reviewed_subject(person['name'],BIOLOGY,continuity)
            actual=labelled_research(item,cache,selected,BIOLOGY,['pancreatic cancer']);actual['sourceSubjectContinuity']=continuity
            row.update(originalSourceProfessorRecord=copy.deepcopy(person),originalSourceRecordSha256=record_sha256(person),
                previousCompiledProfessorRecord=copy.deepcopy(person),previousCompiledProfessorRecordSha256=record_sha256(person),
                sourceSubjectContinuity=continuity,sourceObservation=actual,fields=actual['fields'],fieldEvidence=actual['fieldEvidence'])
            reviews=verified_professor_fields({'entries':[row]},{'items':{'own':item}},cache,[person]);data={'professors':[person]}
            apply_professor_fields(data,reviews)
            self.assertEqual(person['name'],'Jane Alice A. Example');self.assertNotIn('aliasIds',person);self.assertNotIn('aliasNames',person)
            self.assertEqual(person['professorFieldReviews'][0]['sourceObservation']['nameAsDisplayed'],'Jane Alice Example')
            once=copy.deepcopy(data);apply_professor_fields(data,reviews);self.assertEqual(data,once)
            for name in ['Jane Anne A. Example','Jane Alice Brian Example','Jane B. Example','Jane Alice B. Example']:
                with self.subTest(name=name),self.assertRaises(ValueError):reviewed_subject(name,BIOLOGY,continuity)
            with self.assertRaises(ValueError):reviewed_subject('Jane Alice A. Example',JACOBS,continuity)
            other=copy.deepcopy(row['originalSourceProfessorRecord']);other['id']='competing-owner'
            with self.assertRaises(ValueError):verified_professor_fields({'entries':[row]},{'items':{'own':item}},cache,[row['originalSourceProfessorRecord'],other])


if __name__=='__main__':unittest.main()
