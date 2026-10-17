import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collect_ucsd_coverage import profiles_appointment
from faculty_profile_bindings import profile_metadata, verified_profile_bindings
from lab_resource_reviews import record_sha256
from review_ucsd_coverage import faculty_review
from test_atlas_quality import professor


class NamedRosterBindingTests(unittest.TestCase):
    def fixture(self, cache, original_name='Charley Coffey', profile_name='Charles Coffey'):
        original='http://profiles.ucsd.edu/charles.coffey'; target='https://profiles.ucsd.edu/charles.coffey'
        roster='https://oto.ucsd.edu/faculty'; final_roster=roster+'/'
        canonical=target; rdf='https://researcherprofiles.org/profile/123/123.rdf'
        person=professor('retained-original-id',original_name,'Otolaryngology')
        person.update(officialProfileUrl=original,email='Not found',personalWebsiteUrl='Not found',sourceUrls=[original,roster])
        atlas={'professors':[person],'labs':[]}; queue={'items':{},'facultyListings':[]};(cache/'responses').mkdir()
        def save(uri,final,raw,date):
            path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.write_text(raw)
            meta={'sourceUrl':uri,'finalUrl':final,'status':'ok','observedAt':date,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            queue['items'][uri]={'url':uri,'fetch':meta,'state':'done','contexts':[]};return meta
        raw=(f'<html><head><title>{profile_name} | UCSD Profiles</title><link rel="canonical" href="{canonical}">'
             f'<link rel="alternate" type="application/rdf+xml" href="{rdf}"></head><body><main>'
             f'<div class="pageTitle"><h2>{profile_name}</h2></div><table><tr><th>Title(s)</th><td>Clinical Professor, Otolaryngology</td></tr>'
             '<tr><th>School</th><td>Vc-health Sciences-schools</td></tr></table></main></body></html>')
        save(original,target,raw,'2020-01-01');target_meta=save(target,target,raw,'2021-01-01')
        _,listing=profiles_appointment(target_meta,raw);queue['facultyListings']=[listing]
        label=original_name+', MD, FACS';role='Professor of Otolaryngology'
        roster_raw=f'<main><ul><li class="profile-listing-card"><span class="profile-listing-data"><h3><a href="{original}">{label}</a></h3><p>{role}</p></span></li></ul></main>'
        meta=save(roster,final_roster,roster_raw,'2019-01-01')
        link={'requestedUrl':roster,'sourceUrl':final_roster,'observedAt':meta['observedAt'],'bodySha256':meta['sha256'],
              'nameAsDisplayed':original_name,'nameLabelAsDisplayed':label,'subjectTag':'h3','rawHref':original,'linkUrl':original,
              'roleAsListed':role,'roleTag':'p','cardTag':'li','cardClass':'profile-listing-card'}
        captures=[profile_metadata(queue['items'][uri],cache)[0] for uri in [original,target]]+[link]
        row={'action':'bind_observation_to_existing_person','professorId':person['id'],'originalProfileUri':original,
             'originalProfessorRecordSha256':record_sha256(person),'captures':captures,
             'identityBasis':{'type':'official_named_roster_original_profile_link','canonicalUri':canonical,'rdfAlternateUri':rdf,'rosterRequestedUri':roster},
             'nameReview':{'rosterNameAsDisplayed':original_name,'profileNameAsDisplayed':profile_name,
                           'scope':'Separate published display names; no legal-name-change or current-employment claim.'},
             'qualificationAsListed':{'nameAsDisplayed':profile_name,'titleAsListed':'Clinical Professor, Otolaryngology','schoolAsListed':'Vc-health Sciences-schools'},
             'reason':'The retained named department roster explicitly links the exact original profile request; two actual own captures declare the same personal canonical and RDF identifiers.'}
        return atlas,queue,{'entries':[row]}

    def test_real_review_binds_explicit_roster_chain_and_keeps_original_id_name_and_primary_uri(self):
        for old,new in [('Charley Coffey','Charles Coffey'),('Andrea LaCroix','Andrea La Croix'),('Brittany Larsen','Britta Larsen Demartini')]:
            with self.subTest(names=(old,new)),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);atlas,queue,review=self.fixture(cache,old,new);before=copy.deepcopy((atlas,queue,review))
                control=faculty_review(copy.deepcopy(queue),atlas,cache,profile_identity_review={'entries':[]})
                self.assertEqual(len(control['professors']),1)
                treated=faculty_review(copy.deepcopy(queue),atlas,cache,profile_identity_review=review)
                self.assertEqual(treated['professors'],[]);self.assertEqual(treated['uncertainListings'],[])
                patch=treated['byProfessorId']['retained-original-id']
                self.assertNotIn('name',patch);self.assertNotIn('officialProfileUrl',patch)
                self.assertIn(new,patch['nameAliases'])
                self.assertEqual(patch['directoryListings'][0]['identityEvidence']['method'],'reviewed_named_roster_original_profile_link_identity')
                self.assertEqual((atlas,queue,review),before)

    def rewrite(self, queue, cache, uri, before, after):
        path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html')
        raw=path.read_text();self.assertIn(before,raw);path.write_text(raw.replace(before,after))
        queue['items'][uri]['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()

    def test_matching_current_metadata_without_the_original_named_roster_is_not_enough(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);atlas,queue,review=self.fixture(cache)
            review['entries'][0]['captures'].pop()
            with self.assertRaisesRegex(ValueError,'distinct actual named source'):
                verified_profile_bindings(review,queue,cache,atlas)

    def test_wrong_named_card_role_scope_raw_link_and_retained_source_fail_closed(self):
        for mode in ['wrong_name','staff_role','navigation','second_heading','wrong_href','unretained_source']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);atlas,queue,review=self.fixture(cache);row=review['entries'][0];proof=row['captures'][2];uri=proof['requestedUrl']
                if mode=='wrong_name':self.rewrite(queue,cache,uri,'Charley Coffey, MD, FACS','Another Person, MD')
                if mode=='staff_role':self.rewrite(queue,cache,uri,'Professor of Otolaryngology','Staff Researcher')
                if mode=='navigation':self.rewrite(queue,cache,uri,'<main>','<main><nav>');self.rewrite(queue,cache,uri,'</main>','</nav></main>')
                if mode=='second_heading':self.rewrite(queue,cache,uri,'</h3>','</h3><h3>Another Person</h3>')
                if mode=='wrong_href':self.rewrite(queue,cache,uri,'href="http://','href="https://')
                if mode=='unretained_source':
                    atlas['professors'][0]['sourceUrls'].remove(uri);row['originalProfessorRecordSha256']=record_sha256(atlas['professors'][0])
                proof['bodySha256']=queue['items'][uri]['fetch']['sha256']
                with self.assertRaises(ValueError):verified_profile_bindings(review,queue,cache,atlas)

    def test_different_personal_identifiers_are_not_overridden_by_the_published_roster_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);atlas,queue,review=self.fixture(cache);row=review['entries'][0];uri=row['captures'][1]['requestedUrl']
            self.rewrite(queue,cache,uri,'/123/123.rdf','/456/456.rdf')
            row['captures'][1]=profile_metadata(queue['items'][uri],cache)[0]
            row['identityBasis']['rdfAlternateUri']=row['captures'][1]['rdfAlternateUri']
            with self.assertRaisesRegex(ValueError,'shared personal identifiers'):
                verified_profile_bindings(review,queue,cache,atlas)

    def test_an_unrelated_current_subject_cannot_replace_the_retained_roster_person(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);atlas,queue,review=self.fixture(cache);row=review['entries'][0]
            for index in [0,1]:
                uri=row['captures'][index]['requestedUrl'];self.rewrite(queue,cache,uri,'Charles Coffey','Alan Turing')
                row['captures'][index]=profile_metadata(queue['items'][uri],cache)[0]
            row['nameReview']['profileNameAsDisplayed']='Alan Turing';row['qualificationAsListed']['nameAsDisplayed']='Alan Turing'
            with self.assertRaisesRegex(ValueError,'compatible subjects'):
                verified_profile_bindings(review,queue,cache,atlas)

    def test_changed_raw_bytes_dates_or_competing_existing_owners_are_not_accepted(self):
        for mode in ['body','date','duplicate_owner']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);atlas,queue,review=self.fixture(cache);uri=review['entries'][0]['captures'][2]['requestedUrl']
                if mode=='body':
                    path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.write_text(path.read_text()+'<!-- changed -->')
                if mode=='date':queue['items'][uri]['fetch']['observedAt']='2022-01-01'
                if mode=='duplicate_owner':
                    other=copy.deepcopy(atlas['professors'][0]);other['id']='another-original-id';other['officialProfileUrl']=review['entries'][0]['captures'][1]['requestedUrl'];atlas['professors'].append(other)
                with self.assertRaises(ValueError):verified_profile_bindings(review,queue,cache,atlas)
