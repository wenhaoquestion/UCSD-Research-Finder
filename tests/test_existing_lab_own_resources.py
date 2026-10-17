import copy,hashlib,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from existing_lab_own_resources import verified_existing_own_resources,attach_existing_own_resources,KIND
from lab_resource_reviews import record_sha256
from lab_preferred_resources import verified_preferred_resources
from rebuild_verified_atlas import build
from audit_ucsd_preservation import audit
from refresh_labs import make_lab
from test_atlas_quality import atlas


class ExistingOwnResourceTests(unittest.TestCase):
    def fixture(self,cache):
        q={'items':{}};name='Example Scientific Optics Research Group';pi='Ada Scientist'
        own='https://example-optics.ucsd.edu/';member=own+'members'
        old='https://www.ece.ucsd.edu/faculty-research/failed-lab-label'
        roster='https://ece.ucsd.edu/faculty-research/ece-laboratories'
        publisher='https://jacobsschool.ucsd.edu/faculty/profile?id=123'
        files={}
        def capture(uri,markup):
            f=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');f.parent.mkdir(exist_ok=True);f.write_text(markup);files[uri]=f
            m={'sourceUrl':uri,'finalUrl':uri,'observedAt':'2026-10-17T14:22:56+00:00','status':'ok','httpStatus':200,'redirects':[],
               'sha256':hashlib.sha256(f.read_bytes()).hexdigest()};q['items'][uri]={'url':uri,'fetch':m}
            def proof(text,kind='main_text_quote',**extra):return {'requestedUrl':uri,'sourceUrl':uri,'observedAt':m['observedAt'],
                'bodySha256':m['sha256'],'evidenceType':kind,'evidence':text,'status':'verified',**extra}
            return proof
        r=capture(own,f'<html><head><title>{name}</title></head><body><nav><a href="/members" role="link" data-url="/members">Members</a></nav><main><h1>{name} at UC San Diego</h1></main></body></html>')
        t=capture(member,f'<html><head><title>{name} - Members</title></head><body><main><h1>Members</h1><h1>Principal Investigator</h1><p>Prof. {pi}</p><h1>Graduate Students</h1><p>Another Student</p></main></body></html>')
        declaration=name+' (Professor Ada Scientist)'
        s=capture(roster,f'<html><head><title>ECE Laboratories | Electrical and Computer Engineering</title></head><body><main><h1>ECE Laboratories</h1><ul><li><a href="bad lab reference">{name}</a> (Professor Ada Scientist)</li></ul></main></body></html>')
        p=capture(publisher,f'<html><head><title>Faculty Profiles</title></head><body><main><h3 class="faculty_profile_name">A. Scientist</h3><a href="{own}">Website</a></main></body></html>')
        failed={'sourceUrl':old,'finalUrl':old,'observedAt':'2026-10-16T00:00:00+00:00','status':'http_error','httpStatus':404,'redirects':[]}
        q['items'][old]={'url':old,'fetch':failed}
        lab=make_lab(name,old,'Electrical and Computer Engineering',q['items'][roster]['fetch'],declaration)
        lab.update(id='unchanged-group',principalInvestigator=pi,professorIds=[],sourceUrls=[old,own,roster],lastVerified='2020-01-01')
        retained={'sourceUrl':own,'observedAt':'2026-10-07T23:03:17+00:00','method':'manual_review_explicit_lab_leadership',
                  'evidence':'The research group is directed by Prof. '+pi+'.','status':'verified'}
        lab['fieldEvidence']['principalInvestigator']=[retained]
        lab['fieldEvidence']['labName']=[{'sourceUrl':roster,'observedAt':'2026-10-07T00:00:00+00:00','evidence':declaration,'status':'verified'}]
        row={'kind':KIND,'labId':lab['id'],'originalLabRecord':copy.deepcopy(lab),'originalLabRecordSha256':record_sha256(lab),
            'ownResourceUri':own,'retainedLeadershipSourceProof':retained,'previousPrimaryObservation':failed,
            'publisherNameAsPublished':'A. Scientist','reason':'Reverify the exact original retained leadership source as this named own group resource.'}
        row.update(ownTitleEvidence=r(name,'document_title'),ownGroupHeadingEvidence=r(name+' at UC San Diego','document_heading',headingTag='h1'),
            ownMembersTitleEvidence=t(name+' - Members','document_title'),ownPiSectionEvidence=t('Principal Investigator Prof. '+pi),
            ownMembersLinkEvidence=r('a[href] = /members','html_attribute',elementTag='a',attributeName='href',attributeValue='/members',selectorAttributes={'role':'link','data-url':'/members'},linkUrl=member),
            campusRosterTitleEvidence=s('ECE Laboratories | '+lab['department'],'document_title'),campusNamedGroupEvidence=s(declaration),
            namedPublisherLinkEvidence=p('Website -> '+own,'named_link',linkText='Website',linkUrl=own))
        row['evidence']=[row[k] for k in ['ownTitleEvidence','ownGroupHeadingEvidence','ownMembersTitleEvidence','ownPiSectionEvidence',
            'ownMembersLinkEvidence','campusRosterTitleEvidence','campusNamedGroupEvidence','namedPublisherLinkEvidence']]
        return q,lab,row,files

    def verify(self,q,lab,row,cache,labs=None):
        return verified_existing_own_resources({'entries':[row]},q,cache,labs or [lab])

    def test_reverified_original_source_selects_own_home_without_person_pi_or_identity_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);q,lab,row,_=self.fixture(cache);before=copy.deepcopy(lab)
            resources=self.verify(q,lab,row,cache);coverage={'labAliases':[],'labAliasResourceReviews':[]}
            attach_existing_own_resources(coverage,resources)
            preferred={'labId':lab['id'],'action':'select_preferred_lab_resource','previousPreferredUrl':lab['labWebsiteUrl'],
                'preferredUrl':row['ownResourceUri'],'originalLabRecord':copy.deepcopy(lab),'originalLabRecordSha256':record_sha256(lab),
                'identityEvidence':[row['ownTitleEvidence']],'evidence':row['evidence'],'reason':row['reason']}
            coverage['labPreferredResourceReviews']=verified_preferred_resources({'entries':[preferred]},coverage['labAliasResourceReviews'],q,cache,[lab])
            data=atlas();data['labs']=[lab]
            first,*_=build(copy.deepcopy(data),{},{},{},{},coverage_evidence=coverage);actual=first['labs'][0]
            self.assertEqual(actual['labWebsiteUrl'],row['ownResourceUri'])
            for field in ['id','labName','institution','department','principalInvestigator','professorIds','researchAreas','lastVerified']:
                self.assertEqual(actual.get(field),before.get(field),field)
            self.assertTrue(any(x.get('field')=='labWebsiteUrl' and x.get('value')==before['labWebsiteUrl'] for x in actual['previousFieldObservations']))
            self.assertEqual(actual['websiteCheck']['status'],'reachable')
            second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence=coverage);self.assertEqual(first,second)

    def test_domain_or_name_similarity_without_original_retained_leadership_is_rejected(self):
        for mode in ['source-url','proof','pi','fingerprint','positive-old-primary']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);q,lab,row,_=self.fixture(cache)
                if mode=='source-url':lab['sourceUrls'].remove(row['ownResourceUri'])
                if mode=='proof':lab['fieldEvidence']['principalInvestigator'][0]['method']='unverified_label'
                if mode=='pi':lab['principalInvestigator']='Different Investigator'
                if mode in ['source-url','proof','pi']:row['originalLabRecord']=copy.deepcopy(lab);row['originalLabRecordSha256']=record_sha256(lab)
                if mode=='fingerprint':row['originalLabRecordSha256']='changed'
                if mode=='positive-old-primary':q['items'][lab['labWebsiteUrl']]['fetch'].update(status='ok',httpStatus=200)
                with self.assertRaises(ValueError):self.verify(q,lab,row,cache)

    def test_scoped_own_titles_members_and_current_campus_listing_are_required(self):
        for mode in ['root-name','member-name','student-role','campus-label','publisher-link']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);q,lab,row,files=self.fixture(cache)
                if mode=='root-name':u=row['ownResourceUri'];old=lab['labName'];new='Another Scientific Optics Research Group'
                if mode=='member-name':u=row['ownResourceUri']+'members';old=lab['labName']+' - Members';new='Another Group - Members'
                if mode=='student-role':u=row['ownResourceUri']+'members';old='Principal Investigator';new='Graduate Students'
                if mode=='campus-label':u=row['campusNamedGroupEvidence']['requestedUrl'];old='Professor Ada Scientist';new='Professor Other Scientist'
                if mode=='publisher-link':u=row['namedPublisherLinkEvidence']['requestedUrl'];old=row['ownResourceUri'];new='https://another.ucsd.edu/'
                files[u].write_text(files[u].read_text().replace(old,new));q['items'][u]['fetch']['sha256']=hashlib.sha256(files[u].read_bytes()).hexdigest()
                with self.assertRaises(ValueError):self.verify(q,lab,row,cache)

    def test_stale_dates_bytes_and_redirect_inferences_are_rejected(self):
        for mode in ['bytes','date','redirect']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);q,lab,row,files=self.fixture(cache);u=row['ownResourceUri']
                if mode=='bytes':files[u].write_text(files[u].read_text()+'changed')
                if mode=='date':q['items'][u]['fetch']['observedAt']='2026-10-18T00:00:00+00:00'
                if mode=='redirect':q['items'][u]['fetch']['redirects']=[{'from':u,'to':'https://another.ucsd.edu/','httpStatus':301}]
                with self.assertRaises(ValueError):self.verify(q,lab,row,cache)

    def test_colliding_owners_and_person_edges_require_separate_scopes(self):
        for mode in ['owner','pi-person-edge','shared-resource','name-collision']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);q,lab,row,_=self.fixture(cache);labs=[lab]
                if mode in ['owner','name-collision']:
                    other=copy.deepcopy(lab);other['id']='another-group'
                    if mode=='owner':other.update(labName='Another Group',labWebsiteUrl=row['ownResourceUri'])
                    labs.append(other)
                if mode=='pi-person-edge':lab['professorIds']=['a-person']
                if mode=='shared-resource':lab['websiteSharing']={'kind':'distinct_named_labs'}
                with self.assertRaises(ValueError):self.verify(q,lab,row,cache,labs)

    def test_registration_validates_the_whole_batch_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);q,lab,row,_=self.fixture(cache);resources=self.verify(q,lab,row,cache)
            for mode in ['unverified','duplicate','mismatched-alias']:
                coverage={'labAliases':[],'labAliasResourceReviews':[]};bad=copy.deepcopy(resources[0])
                if mode=='unverified':bad['captureVerified']=False
                if mode=='duplicate':pass
                if mode=='mismatched-alias':bad['resourceAlias']['url']='https://other.ucsd.edu/'
                with self.assertRaises(ValueError):attach_existing_own_resources(coverage,resources+[bad])
                self.assertEqual(coverage,{'labAliases':[],'labAliasResourceReviews':[]})


if __name__=='__main__':unittest.main()
