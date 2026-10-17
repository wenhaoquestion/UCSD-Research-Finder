import copy,hashlib,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from lab_child_research_fields import child_research_fields
from lab_own_metadata import verified_own_metadata,apply_own_metadata
from lab_resource_reviews import record_sha256
from refresh_labs import make_lab


class ChildResearchFieldsTests(unittest.TestCase):
    def capture(self,cache,q,u,markup):
        f=cache/'responses'/(hashlib.sha256(u.encode()).hexdigest()+'.html');f.parent.mkdir(exist_ok=True);f.write_text(markup)
        item={'url':u,'fetch':{'sourceUrl':u,'finalUrl':u,'status':'ok','httpStatus':200,'redirects':[],
            'observedAt':'2026-10-17T14:22:25+00:00','sha256':hashlib.sha256(f.read_bytes()).hexdigest()}}
        q['items'][u]=item;return item,f

    def fixture(self,cache):
        q={'items':{}};root='https://sites.ucsd.edu/example-lab/';child=root+'research/'
        home,hp=self.capture(cache,q,root,f'<html><head><title>Example Lab – Research</title></head><body><nav>'
            f'<a class="navbar-brand-sitename" rel="home" href="{root}" title="Example Lab"></a></nav>'
            f'<main><p>Collective research.</p><a class="rcn-text-link" href="{child}">Our research ↗</a></main></body></html>')
        values=['Circuit-based therapies','Cognitive dysfunction','Calcium imaging','Behavioral experiments','Circuit manipulations','Molecular profiling']
        cards=''.join(f'<div class="rcn-technique"><h3>{x}</h3><p>Method explanation.</p></div>' for x in values[2:])
        research,cp=self.capture(cache,q,child,'<html><head><title>Research – Example Lab</title></head><body><main>'
            '<article class="page type-page hentry"><h1>Research</h1>'
            f'<section class="rcn-research-section" aria-labelledby="movement"><h2 id="movement">{values[0]}</h2><p>Our research.</p></section>'
            f'<section class="rcn-research-section rcn-cognition" aria-labelledby="cognition"><h2 id="cognition">{values[1]}</h2></section>'
            f'<section class="rcn-techniques" aria-labelledby="techniques"><h2 id="techniques">Techniques we use</h2><div class="rcn-technique-grid">{cards}</div></section>'
            '<section><h2>Personal biography topics</h2></section></article></main><footer><h3>Unrelated publication title</h3></footer></body></html>')
        lab=make_lab('Example Lab',root,'Unknown',home['fetch'],'Example Lab');lab.update(id='stable-lab',researchAreas=[],description='Existing collective description.',professorIds=[],lastVerified='2020-01-01')
        actual=child_research_fields(home,research,cache,lab['labName'])
        row={'labId':lab['id'],'originalLabRecord':copy.deepcopy(lab),'originalLabRecordSha256':record_sha256(lab),
            'reason':'Use only labelled own research section and technique-card headings.',
            'fields':actual['fields'],'fieldEvidence':actual['fieldEvidence'],'evidence':actual['evidence'],
            'identityEvidence':actual['identityEvidence'],'sourceScope':actual}
        return q,lab,row,hp,cp,values

    def verify(self,q,lab,row,cache,labs=None):
        return verified_own_metadata({'entries':[row]},[],q,cache,labs or [lab])

    def rewrite(self,q,u,f,old,new):
        f.write_text(f.read_text().replace(old,new));q['items'][u]['fetch']['sha256']=hashlib.sha256(f.read_bytes()).hexdigest()

    def test_literal_themes_and_techniques_exclude_biography_publications_and_identity_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);q,lab,row,_,_,values=self.fixture(cache);before=copy.deepcopy(lab)
            reviewed=self.verify(q,lab,row,cache);apply_own_metadata({'labs':[lab]},reviewed)
            self.assertEqual(lab['researchAreas'],values)
            for field in ['id','labName','labWebsiteUrl','institution','department','description','principalInvestigator','professorIds','recruitingStatus','lastVerified']:
                self.assertEqual(lab.get(field),before.get(field),field)
            self.assertNotIn('Personal biography topics',str(lab['researchAreas']))
            self.assertNotIn(row['sourceScope']['requestedUrl'],lab.get('alternateWebsiteUrls',[]))
            first=copy.deepcopy(lab);apply_own_metadata({'labs':[lab]},reviewed);self.assertEqual(lab,first)

    def test_named_parent_and_child_titles_brand_and_published_link_are_required(self):
        for mode in ['parent-title','brand','link','child-title']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);q,lab,row,hp,cp,_=self.fixture(cache);root=lab['labWebsiteUrl']
                if mode=='parent-title':self.rewrite(q,root,hp,'Example Lab – Research','Other Lab – Research')
                if mode=='brand':self.rewrite(q,root,hp,'title="Example Lab"','title="Other Lab"')
                if mode=='link':self.rewrite(q,root,hp,'rcn-text-link','other-link')
                if mode=='child-title':self.rewrite(q,root+'research/',cp,'Research – Example Lab','Research – Other Lab')
                with self.assertRaises(ValueError):self.verify(q,lab,row,cache)

    def test_missing_duplicate_or_foreign_section_headings_fail_closed(self):
        changes=[('id="movement"','id="other"'),('aria-labelledby="cognition"','aria-labelledby="movement"'),
            ('<h2 id="movement">','<h3 id="movement">'),
            ('<p>Method explanation.</p>','<h3>Other person</h3>'),
            ('class="rcn-technique-grid"','class="other-people"'),('Techniques we use','Personal bibliography')]
        for old,new in changes:
            with self.subTest(change=new),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);q,lab,row,_,cp,_=self.fixture(cache);self.rewrite(q,lab['labWebsiteUrl']+'research/',cp,old,new)
                with self.assertRaises(ValueError):self.verify(q,lab,row,cache)

    def test_stale_values_bytes_dates_or_arbitrary_area_fields_are_rejected(self):
        for mode in ['value','bytes','date','kind','extra-field']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);q,lab,row,_,cp,_=self.fixture(cache);u=lab['labWebsiteUrl']+'research/'
                if mode=='value':row['fields']['researchAreas'].append('Invented keyword')
                if mode=='bytes':cp.write_text(cp.read_text()+'changed')
                if mode=='date':q['items'][u]['fetch']['observedAt']='2026-10-18T00:00:00+00:00'
                if mode=='kind':row['sourceScope']['kind']='named_own_parent_published_child'
                if mode=='extra-field':row['fields']['department']='Neurosciences'
                with self.assertRaises(ValueError):self.verify(q,lab,row,cache)

    def test_shared_changed_or_redirected_resource_cannot_supply_other_lab_fields(self):
        for mode in ['shared','primary','redirect']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);q,lab,row,_,_,_=self.fixture(cache);labs=[lab]
                if mode=='shared':other=copy.deepcopy(lab);other.update(id='other-lab',labName='Other Lab');labs.append(other)
                if mode=='primary':lab['labWebsiteUrl']='https://sites.ucsd.edu/other-lab/'
                if mode=='redirect':q['items'][lab['labWebsiteUrl']+'research/']['fetch']['redirects']=[{'from':lab['labWebsiteUrl']+'research/','to':'https://other.ucsd.edu/','httpStatus':301}]
                with self.assertRaises(ValueError):self.verify(q,lab,row,cache,labs)

    def test_alias_registration_cannot_hide_multiple_current_primary_owners(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);q,lab,row,_,_,_=self.fixture(cache)
            other=copy.deepcopy(lab);other.update(id='other-lab',labName='Other Lab')
            aliases=[{'labId':lab['id'],'url':lab['labWebsiteUrl'],'captureVerified':True}]
            with self.assertRaises(ValueError):
                verified_own_metadata({'entries':[row]},aliases,q,cache,[lab,other])


if __name__=='__main__':unittest.main()
