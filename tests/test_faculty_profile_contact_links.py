import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from faculty_profile_bindings import own_profile_links,profile_metadata,verified_profile_bindings
from lab_resource_reviews import record_sha256
from review_ucsd_coverage import faculty_review
from collect_ucsd_coverage import profiles_appointment
from faculty_candidate_history import candidate_history
import test_faculty_profile_bindings as metadata_tests


class FacultyOwnProfileLinkTests(unittest.TestCase):
    def variation_fixture(self, cache, target_name='Brenton Example'):
        helper,atlas,queue,review=self.fixture(cache,'radonc')
        person=atlas['professors'][0];person['name']='Brent Example'
        row=review['entries'][0];original=row['originalProfileUri'];target=row['captures'][1]['requestedUrl']
        for uri,name in [(original,person['name']),(target,target_name)]:
            helper.rewrite(queue,cache,uri,'Jane Example',name)
        row['originalProfessorRecordSha256']=record_sha256(person)
        row['captures']=[own_profile_links(queue['items'][original],cache,person['name'])[0],
                         profile_metadata(queue['items'][target],cache)[0]]
        path=cache/'responses'/(hashlib.sha256(target.encode()).hexdigest()+'.html')
        assessment,listing=profiles_appointment(queue['items'][target]['fetch'],path.read_text())
        queue['facultyListings']=[listing]
        row['qualificationAsListed']={k:assessment[k] for k in ['nameAsDisplayed','titleAsListed','schoolAsListed']}
        row['nameReview']={'originalNameAsDisplayed':person['name'],'profileNameAsDisplayed':target_name,
                           'scope':'Separate published display names; no legal-name-change or current-employment claim.'}
        return atlas,queue,review

    def test_published_name_variation_requires_actual_self_link_and_preserves_both_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);atlas,queue,review=self.variation_fixture(cache)
            before=copy.deepcopy((atlas,queue,review))
            result=faculty_review(copy.deepcopy(queue),atlas,cache,profile_identity_review=review)
            self.assertFalse(result['professors']);self.assertFalse(result['uncertainListings'])
            patch=result['byProfessorId']['old-stable-id']
            self.assertNotIn('name',patch);self.assertNotIn('officialProfileUrl',patch)
            self.assertEqual(patch['nameAliases'],['Brenton Example'])
            listing=patch['directoryListings'][0]
            self.assertEqual(listing['name'],'Brenton Example')
            self.assertEqual(listing['identityEvidence']['profileIdentityBinding']['nameReview'],review['entries'][0]['nameReview'])
            self.assertEqual((atlas,queue,review),before)
            control=faculty_review(copy.deepcopy(queue),atlas,cache,profile_identity_review={'entries':[]})
            previous=copy.deepcopy(control['professors'][0])
            previous['directoryListings']=control['byProfessorId'][previous['id']]['directoryListings']
            history={'sourceCandidateAtlasSha256':'a'*64,'entries':[{
                'record':previous,'recordSha256':record_sha256(previous),
                'disposition':'resolved_observation_binding_to_original_person',
                'targetProfessorId':'old-stable-id','observationBinding':review['entries'][0],
                'reason':'Retain the former proposal and its ID under the captured original self-profile binding.'}]}
            patches,archives=candidate_history(history,atlas['professors'],result,queue,cache)
            self.assertFalse(archives)
            alias=patches['old-stable-id']['candidateObservationAliases'][0]
            self.assertEqual(alias['aliasIds'],[previous['id']])
            self.assertEqual(patches['old-stable-id']['previousFieldObservations'][0]['value'],previous)

    def test_reviewed_name_labels_cannot_forge_a_variation_or_replace_the_self_link(self):
        for mode in ['missing_review','wrong_original','wrong_profile','wrong_scope','unrelated_subject','wrong_link']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp)
                atlas,queue,review=self.variation_fixture(cache,'Another Person' if mode=='unrelated_subject' else 'Brenton Example')
                row=review['entries'][0]
                if mode=='missing_review':row.pop('nameReview')
                elif mode=='wrong_original':row['nameReview']['originalNameAsDisplayed']='Brenton Example'
                elif mode=='wrong_profile':row['nameReview']['profileNameAsDisplayed']='Brent Example'
                elif mode=='wrong_scope':row['nameReview']['scope']='Same legal name and current employment'
                elif mode=='wrong_link':row['identityBasis']['linkedProfileUri']='https://profiles.ucsd.edu/other.person'
                with self.assertRaises(ValueError):verified_profile_bindings(review,queue,cache,atlas)

    def fixture(self,cache,kind='contact',bridge=False):
        helper=metadata_tests.FacultyProfileBindingTests()
        atlas,queue,_=helper.fixture(cache)
        target='https://profiles.ucsd.edu/jane.example'
        original=('https://jacobsschool.ucsd.edu/faculty/profile?id=123' if kind=='jacobs'
                  else 'https://radonc.ucsd.edu/faculty/radiation-oncology/example.html' if kind=='radonc'
                  else 'https://pharmacology.ucsd.edu/faculty/department-faculty1/jane-example.html' if kind=='pharmacology'
                  else 'https://department.ucsd.edu/faculty/jane')
        person=atlas['professors'][0];person['officialProfileUrl']=original
        href='http://profiles.ucsd.edu/Jane.Example' if bridge else target+'#narrative'
        contexts={
            'contact':f'<p class="metaContact"><a href="{href}">UCSD Profile</a></p>',
            'contact_list':f'<ul class="profile-contact-list"><li><a href="{href}">Personal Website</a></li></ul>',
            'website':f'<div class="field--name-field-web-page"><a href="{href}">Website</a></div>',
            'links':f'<div><h2>Links</h2><p><a href="{href}">UCSD Profile</a></p></div>',
            'radonc':f'<div class="styled"><h2>Education</h2><p>M.D., University</p><h2>Links</h2><a href="{href}">UCSD Profile</a><br></div>',
            'pharmacology':f'<div class="facultyMeta pt-60"><div class="sidebarContactCallout"><h4>CONTACT</h4><p class="metaContact">jexample@ucsd.edu</p><h4>Websites</h4><p><span class="md"><a href="{href}">UCSD Profile</a></span></p></div></div>',
            'jacobs':f'<div class="row mb-5"><h3 class="faculty_profile_name">Jane Example</h3><div class="col-3"><p><a href="{href}">Website</a></p></div></div>'}
        content=contexts[kind]
        markup=('<html><head><title>Jane Example | Department</title><link rel="canonical" href="https://department.ucsd.edu/faculty"></head>'
                '<body><main>'+('<h1>Faculty Profiles</h1>' if kind=='jacobs' else '<h1>Jane Example</h1>')+content+'</main></body></html>')
        path=cache/'responses'/(hashlib.sha256(original.encode()).hexdigest()+'.html');path.write_text(markup)
        meta={'sourceUrl':original,'finalUrl':original,'status':'ok','observedAt':'2019-01-01','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        queue['items'][original]={'url':original,'state':'done','fetch':meta,'contexts':[]}
        source=own_profile_links(queue['items'][original],cache,person['name'])[0]
        target_proof,_=profile_metadata(queue['items'][target],cache)
        row={'action':'bind_observation_to_existing_person','professorId':person['id'],
             'originalProfileUri':original,'originalProfessorRecordSha256':record_sha256(person),'captures':[source,target_proof],
             'identityBasis':{'type':'official_own_profile_contact_link','linkedProfileUri':source['linkUrl'],
                              'canonicalUri':target_proof['canonicalUri'],'rdfAlternateUri':target_proof['rdfAlternateUri']},
             'qualificationAsListed':{'nameAsDisplayed':'Jane Example','titleAsListed':'Associate Professor, Pediatrics','schoolAsListed':'Vc-health Sciences-schools'},
             'reason':'The unchanged named individual page explicitly supplies this self-profile link in its own contact field.'}
        return helper,atlas,queue,{'entries':[row]}

    def test_real_faculty_review_uses_each_own_contact_template_without_replacing_id_or_primary_uri(self):
        for kind in ['contact','contact_list','website','links','jacobs','radonc','pharmacology']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);_,atlas,queue,review=self.fixture(cache,kind)
                before=copy.deepcopy((atlas,queue,review))
                control=faculty_review(copy.deepcopy(queue),atlas,cache,profile_identity_review={'entries':[]})
                self.assertEqual(len(control['uncertainListings']),1)
                result=faculty_review(copy.deepcopy(queue),atlas,cache,profile_identity_review=review)
                self.assertFalse(result['professors']);self.assertFalse(result['uncertainListings'])
                self.assertEqual(set(result['byProfessorId']),{'old-stable-id'})
                patch=result['byProfessorId']['old-stable-id'];self.assertNotIn('officialProfileUrl',patch)
                self.assertEqual(patch['directoryListings'][0]['identityEvidence']['method'],'reviewed_explicit_own_profile_contact_link_identity')
                self.assertEqual((atlas,queue,review),before)

    def test_pharmacology_link_requires_the_named_own_contact_websites_block(self):
        for old,new in [('<h4>Websites</h4>','<h4>Publications</h4>'),
                        ('<h4>CONTACT</h4>','<h4>Collaborators</h4>'),
                        ('class="facultyMeta pt-60"','class="unrelated"'),
                        ('class="sidebarContactCallout"','class="unrelated"'),
                        ('<h4>Websites</h4>','<h4>Websites</h4><p>Another person</p>')]:
            with self.subTest(change=new),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);_,atlas,queue,review=self.fixture(cache,'pharmacology');uri=review['entries'][0]['originalProfileUri'];path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.write_text(path.read_text().replace(old,new));queue['items'][uri]['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();self.assertEqual(own_profile_links(queue['items'][uri],cache,'Jane Example'),[])

    def test_radonc_direct_link_requires_its_own_immediately_preceding_links_heading(self):
        for old,new in [('<h2>Links</h2>','<h2>Publications</h2>'),
                        ('<h2>Links</h2>','<h2>Links</h2><p>Professor Another Person</p>'),
                        ('class="styled"','class="unrelated"')]:
            with self.subTest(change=new),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);_,atlas,queue,review=self.fixture(cache,'radonc')
                uri=review['entries'][0]['originalProfileUri'];path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html')
                path.write_text(path.read_text().replace(old,new));queue['items'][uri]['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(own_profile_links(queue['items'][uri],cache,'Jane Example'),[])

    def test_navigation_biography_publication_links_and_wrong_subjects_are_not_self_profile_fields(self):
        for replacement in ['<p><a href="https://profiles.ucsd.edu/jane.example">UCSD Profile</a></p>',
                            '<nav><p class="metaContact"><a href="https://profiles.ucsd.edu/jane.example">UCSD Profile</a></p></nav>',
                            '<section><h2>Publications</h2><p><a href="https://profiles.ucsd.edu/jane.example">Example J</a></p></section>',
                            'wrong_subject']:
            with self.subTest(replacement=replacement),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);_,atlas,queue,review=self.fixture(cache)
                uri=review['entries'][0]['originalProfileUri'];path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html')
                text=path.read_text()
                if replacement=='wrong_subject':text=text.replace('<h1>Jane Example</h1>','<h1>Another Person</h1>')
                else:
                    start=text.index('<p class="metaContact">');end=text.index('</p>',start)+4;text=text[:start]+replacement+text[end:]
                path.write_text(text);digest=hashlib.sha256(path.read_bytes()).hexdigest();queue['items'][uri]['fetch']['sha256']=digest
                review['entries'][0]['captures'][0]['bodySha256']=digest
                with self.assertRaises(ValueError):verified_profile_bindings(review,queue,cache,atlas)

    def test_http_or_path_case_variants_require_their_actual_named_capture_and_redirect_trace(self):
        for mode in ['valid','different_rdf','missing_redirect_trace']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);helper,atlas,queue,review=self.fixture(cache,bridge=True)
                with self.assertRaisesRegex(ValueError,'exact captured destination'):
                    verified_profile_bindings(review,queue,cache,atlas)
                uri='http://profiles.ucsd.edu/Jane.Example';final='https://profiles.ucsd.edu/Jane.Example'
                target='https://profiles.ucsd.edu/jane.example';target_path=cache/'responses'/(hashlib.sha256(target.encode()).hexdigest()+'.html')
                raw=target_path.read_bytes();path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.write_bytes(raw)
                hops=[{'from':uri,'to':final,'httpStatus':301}]
                queue['items'][uri]={'url':uri,'fetch':{'sourceUrl':uri,'finalUrl':final,'status':'ok','observedAt':'2018-01-01','sha256':hashlib.sha256(raw).hexdigest(),'redirects':hops}}
                if mode=='different_rdf':helper.rewrite(queue,cache,uri,'/123/123.rdf','/456/456.rdf')
                if mode=='missing_redirect_trace':queue['items'][uri]['fetch']['redirects']=[];hops=[]
                review['entries'][0]['captures'].append(profile_metadata(queue['items'][uri],cache)[0]);review['entries'][0]['linkedTransportRedirects']=hops
                if mode=='valid':self.assertEqual(len(verified_profile_bindings(review,queue,cache,atlas)),1)
                else:
                    with self.assertRaises(ValueError):verified_profile_bindings(review,queue,cache,atlas)

    def test_profiles_coauthor_pages_and_changed_raw_hrefs_cannot_supply_an_own_department_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);_,atlas,queue,review=self.fixture(cache)
            original='https://profiles.ucsd.edu/Jane.Example'
            with self.assertRaisesRegex(ValueError,'coauthor page'):
                own_profile_links(queue['items'][original],cache,'Jane Example')
            review['entries'][0]['captures'][0]['rawHref']='http://profiles.ucsd.edu/jane.example'
            with self.assertRaisesRegex(ValueError,'actual self-labelled'):
                verified_profile_bindings(review,queue,cache,atlas)

    def test_a_contact_link_cannot_silently_select_one_of_multiple_existing_profile_owners(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);_,atlas,queue,review=self.fixture(cache)
            duplicate=copy.deepcopy(atlas['professors'][0]);duplicate['id']='another-existing-id';duplicate['officialProfileUrl']='https://profiles.ucsd.edu/jane.example';atlas['professors'].append(duplicate)
            with self.assertRaisesRegex(ValueError,'separate person merge'):
                verified_profile_bindings(review,queue,cache,atlas)
