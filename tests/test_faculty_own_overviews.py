import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from faculty_own_overviews import own_overview_listing, OVERVIEW, GROUP
from review_ucsd_coverage import faculty_review
from test_atlas_quality import professor


class OwnOverviewAppointmentTests(unittest.TestCase):
    def fixture(self, cache, text='Jane A. Example, PhD is an Associate Clinical Professor at UC San Diego’s School of Medicine. She also manages a clinical program.', title=''):
        uri='https://profiles.ucsd.edu/jane.example'
        body=('<html><head><title>Jane Example | UCSD Profiles</title>'
              f'<link rel="canonical" href="{uri}">'
              '<link rel="alternate" type="application/rdf+xml" href="https://researcherprofiles.org/profile/123/123.rdf">'
              '</head><body><main><div class="pageTitle"><h2>Jane Example</h2></div><table>'
              +(f'<tr><th>Title(s)</th><td>{title}</td></tr>' if title else '')
              +f'</table><div class="PropertyGroupItem" id="{GROUP}"><div class="PropertyGroupData">'
              f'<div id="{OVERVIEW}">{text}</div></div></div></main></body></html>')
        (cache/'responses').mkdir(exist_ok=True)
        path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.write_text(body)
        meta={'sourceUrl':uri,'finalUrl':uri,'status':'ok','observedAt':'2026-10-16T12:00:00+00:00','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        return {'url':uri,'fetch':meta,'profileEligibility':{'status':'missing_identity_or_appointment_table'}},path

    def test_exact_named_ucsd_overview_qualifies_a_record_without_inventing_a_department(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);item,path=self.fixture(cache);before=copy.deepcopy(item)
            row=own_overview_listing(item,cache)
            self.assertEqual(row['name'],'Jane Example')
            self.assertEqual(row['listedRole'],'Associate Clinical Professor')
            self.assertEqual(row['department'],'Unknown')
            self.assertEqual(row['academicQualification']['unitAsListed'],'')
            self.assertEqual(row['evidence']['overviewSubjectAsListed'],'Jane A. Example')
            self.assertEqual(row['evidence']['bodySha256'],hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(row['evidence']['observedAt'],item['fetch']['observedAt'])
            self.assertNotIn('clinical program',row['evidence']['evidence'])
            result=faculty_review({'items':{item['url']:item},'facultyListings':[]},
                                  {'professors':[],'labs':[]},cache,profile_identity_review={'entries':[]})
            self.assertEqual(len(result['professors']),1)
            person=result['professors'][0]
            self.assertEqual(person['department'],'Unknown')
            self.assertEqual(person['officialProfileUrl'],item['url'])
            self.assertEqual(result['byProfessorId'][person['id']]['directoryListings'][0]['academicQualification'],row['academicQualification'])
            self.assertEqual(item,before)

    def test_other_people_history_foreign_posts_and_nonacademic_jobs_do_not_qualify(self):
        for text in ['Another Person is a Professor at UC San Diego.',
                     'Jane A. Example was a Professor at UC San Diego.',
                     'Jane A. Example is a former Professor at UC San Diego.',
                     'Jane A. Example is an Assistant Professor at Other University and collaborates with UC San Diego.',
                     'Jane A. Example is a Clinical Ethics Manager at UC San Diego.',
                     'Jane A. Example studies ethics. Her mentor is a Professor at UC San Diego.',
                     'Jane A. Example is not an Assistant Professor at UC San Diego.']:
            with self.subTest(text=text),tempfile.TemporaryDirectory() as tmp:
                item,_=self.fixture(Path(tmp),text)
                self.assertIsNone(own_overview_listing(item,Path(tmp)))

    def test_a_stated_table_role_is_not_overridden_by_biography(self):
        for title in ['Program Manager','Clinical Professor, Medicine']:
            with self.subTest(title=title),tempfile.TemporaryDirectory() as tmp:
                item,_=self.fixture(Path(tmp),title=title)
                self.assertIsNone(own_overview_listing(item,Path(tmp)))

    def test_exact_owned_overview_structure_and_captured_bytes_are_required(self):
        for mode in ['outside_overview','outside_group','duplicate_overview','body','failed','wrong_host','date_receipt']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);item,path=self.fixture(cache)
                if mode=='outside_overview':path.write_text(path.read_text().replace(OVERVIEW,'publication'))
                if mode=='outside_group':path.write_text(path.read_text().replace('PropertyGroupData','Unrelated'))
                if mode=='duplicate_overview':path.write_text(path.read_text().replace('</main>',f'<div id="{OVERVIEW}">Other text</div></main>'))
                if mode=='body':path.write_text(path.read_text()+'Changed')
                elif mode in {'outside_overview','outside_group','duplicate_overview'}:item['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                if mode=='failed':item['fetch']['status']='http_error'
                if mode=='wrong_host':item['fetch']['finalUrl']='https://outside.example/jane'
                if mode=='date_receipt':item['fetch']['observedAt']=None
                self.assertIsNone(own_overview_listing(item,cache))

    def test_a_qualified_overview_does_not_resolve_initials_or_another_individual_profile(self):
        for name in ['J. Example','Jane Example']:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);item,_=self.fixture(cache)
                old=professor('original',name,'Medicine');old['officialProfileUrl']='https://profiles.ucsd.edu/other.example'
                before=copy.deepcopy(old)
                result=faculty_review({'items':{item['url']:item},'facultyListings':[]},
                    {'professors':[old],'labs':[]},cache,profile_identity_review={'entries':[]})
                self.assertEqual(result['professors'],[])
                self.assertTrue(result['uncertainListings'])
                self.assertEqual(old,before)
