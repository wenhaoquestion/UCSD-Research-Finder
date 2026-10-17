import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from faculty_career_identity_reviews import KIND, career_binding, retained_career_field_lineage
from person_identity_reviews import verified_person_reviews, apply_person_reviews
from professor_own_field_reviews import verified_professor_fields, apply_professor_fields
from matsci_own_fields import matsci_own_fields
from lab_resource_reviews import record_sha256
from audit_ucsd_preservation import audit
from rebuild_verified_atlas import build
from test_atlas_quality import atlas, professor
import test_matsci_retained_directory_primary as retained_fixtures


class CareerIdentityTests(unittest.TestCase):
    def fixture(self, cache):
        own, queue, source, faculty, _ = retained_fixtures.RetainedMaterialsPrimaryTests().fixture(cache)
        department = 'Electrical and Computer Engineering'
        source['department'] = department
        source['email'] = 'Not found'
        source['officialProfileUrl'] = 'https://catalog.ucsd.edu/faculty/ECE.html'
        own['originalSourceProfessorRecord'] = copy.deepcopy(source)
        own['originalSourceRecordSha256'] = record_sha256(source)
        own['retainedDirectoryPrimaryIdentity']['originalBaselineProfileUri'] = source['officialProfileUrl']
        own['previousCompiledProfessorRecord']['department'] = department
        own['previousCompiledProfessorRecordSha256'] = record_sha256(own['previousCompiledProfessorRecord'])
        items = {x['url']: x for x in queue['items'].values()}
        def save(uri, markup, final=None, redirects=None):
            path = cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html')
            path.write_text(markup)
            items[uri] = {'url': uri, 'fetch': {'sourceUrl': uri, 'finalUrl': final or uri,
                'status': 'ok', 'httpStatus': 200, 'observedAt': '2026-10-16T01:16:08+00:00',
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'redirects': redirects or []}}
        email = 'jexample@ucsd.edu'
        career = ('J. Example is a Professor in Electrical and Computer Engineering. '
                  'She received M.Sc and Ph.D degrees in 1979 and 1983 and joined UCSD in 1990. '
                  + 'She directed the named optical instruments research project and received an individual science award. '*24)
        uri = own['sourceObservation']['capture']['requestedUrl']
        path = cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html')
        text = path.read_text().replace('<div class="field--name-body">Another Person studied unsupported biography topics.</div>',
            '<div class="field--name-field-department">'+department+'</div>'
            '<div class="field--name-field-faculty-email">'+email+'</div>'
            '<div class="field--name-body field__item">'+career+'</div>')
        save(uri, text)
        actual = matsci_own_fields(items[uri], cache, source['name'])
        own.update(sourceObservation=actual, fields=actual['fields'], fieldEvidence=actual['fieldEvidence'])
        listing = faculty['byProfessorId'][source['id']]['directoryListings'][0]
        listing['identityEvidence']['observedAt'] = items[uri]['fetch']['observedAt']
        pub = own['publishedOriginalPrimaryEvidence']['requestedUrl']
        save(pub, '<title>Faculty</title><main><div class="faculty-listing"><h5><a href="/faculty/jane-example">Jane Example</a></h5>Professor '+department+'</div></main>')
        own['publishedOriginalPrimaryEvidence'].update(observedAt=items[pub]['fetch']['observedAt'], bodySha256=items[pub]['fetch']['sha256'])
        listing['observedAt'] = items[pub]['fetch']['observedAt']
        oldproof = own['previousCompiledProfessorRecord']['fieldEvidence']['officialProfileUrl'][0]
        oldproof['observedAt'] = listing['observedAt']
        own['previousCompiledProfessorRecordSha256'] = record_sha256(own['previousCompiledProfessorRecord'])
        target = professor('canonical', 'J. Jane Example', department)
        target.update(officialProfileUrl='https://jacobsschool.ucsd.edu/faculty/profile?id=32',
                      email=email, personalWebsiteUrl='https://example.ucsd.edu/', appointmentStatus='listed_faculty')
        legacy = 'http://jacobsschool.ucsd.edu/faculty/faculty_bios/index.sfe?fmp_recid=32'
        save(legacy, '<title>Faculty Profiles | Jacobs School</title><main><div class="row mb-5">'
             '<div class="col-9"><h3 class="faculty_profile_name">J. Jane Example</h3>'
             '<p class="mb-5">Professor, ECE Faculty-Affiliate, Calit2</p><hr>'
             '<div class="mb-5"><p class="font-weight-bold">Capsule Bio:</p><p>'+career+'</p></div></div>'
             '<div class="col-3"><p>Email: '+email+'</p></div></div></main>', target['officialProfileUrl'],
             [{'from':legacy,'to':target['officialProfileUrl'],'httpStatus':301}])
        roster = 'https://ece.ucsd.edu/people/faculty'
        save(roster, '<title>Faculty | Electrical and Computer Engineering</title><main><div class="faculty-member"><h2><a href="'+legacy+'">J. Jane Example</a></h2><p>Distinguished Professor <a href="mailto:'+email+'">'+email+'</a> 1234</p></div></main>')
        q = {'items': items}; data = atlas(); data['professors'] = [target, source]
        request = {'targetOwnRequestedUri':legacy,'targetRosterRequestedUri':roster}
        binding = career_binding(source, target, own, request, data['professors'], q, cache, faculty)
        ev = binding['evidence']
        compiled_source = copy.deepcopy(own['previousCompiledProfessorRecord']); compiled_source['email'] = email
        row = {'action':'merge','name':target['name'],'sourceProfessorId':source['id'],'targetProfessorId':target['id'],
            'originalSourceRecord':copy.deepcopy(source),'originalTargetRecord':copy.deepcopy(target),
            'sourceRecordSha256':record_sha256(source),'targetRecordSha256':record_sha256(target),
            'identityBasis':{'type':KIND,'value':binding['careerSha256']},'sourceOwnFieldReview':own,
            'careerIdentityRequest':request,'careerIdentityBinding':binding,'evidence':ev,
            'fields':{'name':target['name'],'department':department,'officialProfileUrl':target['officialProfileUrl']},
            'fieldEvidence':{'name':[ev[10],ev[9]],'department':[ev[4],ev[8]],'officialProfileUrl':[ev[10],ev[9]]},
            'departmentEvidence':[{'department':department,'status':'named_department_rosters_and_own_profile','fieldEvidence':[ev[1],ev[4],ev[8]]}],
            'previousCandidateObservations':[{'record':p,'recordSha256':record_sha256(p),'candidateAtlasSha256':'a'*64} for p in [compiled_source,copy.deepcopy(target)]],
            'reason':'Independent named own personal careers, contacts and literal named faculty chains.'}
        return data,q,row,faculty

    def verify(self, data, q, row, faculty, cache):
        return verified_person_reviews({'entries':[row]}, q, cache, data, faculty_review=faculty)

    def test_merge_preserves_names_primary_contacts_whole_records_and_alias_lineage_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,q,row,faculty=self.fixture(cache);before=copy.deepcopy(data)
            reviews=self.verify(data,q,row,faculty,cache)
            field=copy.deepcopy(row['sourceOwnFieldReview']);field['professorId']='canonical'
            field['reviewedPersonAliasLineage']={'kind':KIND,'identityBasis':row['identityBasis'],
                'sourceProfessorId':row['sourceProfessorId'],'targetProfessorId':'canonical',
                'previousOwnFieldReviewSha256':record_sha256(row['sourceOwnFieldReview'])}
            verified=verified_professor_fields({'entries':[field]},q,cache,data['professors'],reviews,faculty_review=faculty)
            archives=apply_person_reviews(data,reviews);apply_professor_fields(data,verified)
            person=data['professors'][0]
            for key in ['id','name','department','officialProfileUrl','personalWebsiteUrl','appointmentStatus','ratings','teaching']:
                self.assertEqual(person.get(key),before['professors'][0].get(key),key)
            self.assertEqual(person['aliasIds'],[row['sourceProfessorId']]);self.assertIn('Jane Example',person['aliasNames'])
            self.assertEqual(person['researchAreas'],field['fields']['researchAreas'])
            self.assertEqual(len([o for o in person['previousFieldObservations'] if o['field']=='careerIdentityPreviousCandidate']),2)
            self.assertEqual(audit(before,data,[archives])['status'],'passed')
            once=copy.deepcopy(data);apply_person_reviews(data,reviews);apply_professor_fields(data,verified);self.assertEqual(data,once)

    def test_wrong_career_scope_or_named_roster_cannot_be_substituted_by_shared_email(self):
        for mode in ['career','bio-label','own-email','roster-link','roster-name','email-scope','redirect']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);data,q,row,faculty=self.fixture(cache)
                request=row['careerIdentityRequest'];uri=request['targetOwnRequestedUri']
                if mode.startswith('roster'):uri=request['targetRosterRequestedUri']
                path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');text=path.read_text()
                if mode=='career':text=text.replace('joined UCSD in 1990','joined UCSD in 1991')
                if mode=='bio-label':text=text.replace('Capsule Bio:','Publications:')
                if mode=='own-email':text=text.replace('Email: jexample@ucsd.edu','Email: another@ucsd.edu')
                if mode=='roster-link':text=text.replace('fmp_recid=32','fmp_recid=99')
                if mode=='roster-name':text=text.replace('J. Jane Example','Another Person')
                if mode=='email-scope':text=text.replace('class="col-3"','class="other-person"')
                if mode=='redirect':q['items'][uri]['fetch']['redirects'][0]['from']='https://unobserved.ucsd.edu/'
                path.write_text(text);q['items'][uri]['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                with self.assertRaises(ValueError):career_binding(data['professors'][1],data['professors'][0],row['sourceOwnFieldReview'],request,data['professors'],q,cache,faculty)

    def test_newer_alias_directory_patch_cannot_displace_original_target_primary_on_rebuild(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,q,row,faculty=self.fixture(cache);data['qualityMigrationVersion']=1
            reviews=self.verify(data,q,row,faculty,cache);sid=row['sourceProfessorId']
            own=row['sourceOwnFieldReview'];uri=own['sourceObservation']['capture']['sourceUrl']
            patch={'name':row['originalSourceRecord']['name'],'officialProfileUrl':uri,
                'fieldEvidence':{'name':[row['evidence'][3]],'officialProfileUrl':[{**own['publishedOriginalPrimaryEvidence'],'observedAt':'2026-10-18'}]}}
            coverage={'byProfessorId':{sid:patch},'personIdentityReviews':reviews}
            first,*_=build(copy.deepcopy(data),{},{},{},{},{},{},{},copy.deepcopy(coverage))
            self.assertEqual(first['professors'][0]['officialProfileUrl'],row['originalTargetRecord']['officialProfileUrl'])
            self.assertEqual(first['professors'][0]['name'],row['originalTargetRecord']['name'])
            repeated,*_=build(copy.deepcopy(first),{},{},{},{},{},{},{},copy.deepcopy(coverage))
            self.assertEqual(first,repeated)

    def test_original_snapshots_initials_and_contact_collisions_fail_closed(self):
        for mode in ['third-email','third-patch-email','third-primary','third-patch-primary','name','snapshot','source-primary','missing-faculty','missing-evidence','date','bytes']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);data,q,row,faculty=self.fixture(cache)
                if mode=='third-email':data['professors'].append({**copy.deepcopy(data['professors'][0]),'id':'third'})
                if mode=='third-patch-email':faculty['byProfessorId']['third']={'email':'jexample@ucsd.edu'}
                if mode=='third-primary':data['professors'].append({**copy.deepcopy(data['professors'][0]),'id':'third','email':'another@ucsd.edu'})
                if mode=='third-patch-primary':faculty['byProfessorId']['third']={'officialProfileUrl':data['professors'][0]['officialProfileUrl']}
                if mode=='name':data['professors'][0]['name']='John Jane Example'
                if mode=='snapshot':row['previousCandidateObservations'][0]['record']['email']='other@ucsd.edu'
                if mode=='source-primary':row['sourceOwnFieldReview']['previousCompiledProfessorRecord']['officialProfileUrl']='https://profiles.ucsd.edu/jane.example'
                if mode=='missing-faculty':faculty=None
                if mode=='missing-evidence':row['evidence'].pop()
                if mode=='date':q['items'][row['careerIdentityRequest']['targetOwnRequestedUri']]['fetch']['observedAt']='2026-10-17'
                if mode=='bytes':
                    uri=row['careerIdentityRequest']['targetOwnRequestedUri'];(cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html')).write_text('changed')
                with self.assertRaises(ValueError):self.verify(data,q,row,faculty,cache)

    def test_own_fields_require_exact_separately_verified_alias_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,q,row,faculty=self.fixture(cache);reviews=self.verify(data,q,row,faculty,cache)
            own=copy.deepcopy(row['sourceOwnFieldReview']);own['professorId']='canonical'
            for mode in ['missing-lineage','changed-fields','unverified-review','wrong-kind']:
                field=copy.deepcopy(own);rs=copy.deepcopy(reviews)
                field['reviewedPersonAliasLineage']={'kind':KIND,'identityBasis':row['identityBasis'],'sourceProfessorId':row['sourceProfessorId'],
                    'targetProfessorId':'canonical','previousOwnFieldReviewSha256':record_sha256(row['sourceOwnFieldReview'])}
                if mode=='missing-lineage':field.pop('reviewedPersonAliasLineage')
                if mode=='changed-fields':field['fields']['researchAreas'].append('Invented')
                if mode=='unverified-review':rs[0]['captureVerified']=False
                if mode=='wrong-kind':rs[0]['identityBasis']['type']='shared_public_email'
                with self.subTest(mode=mode),self.assertRaises(ValueError):verified_professor_fields({'entries':[field]},q,cache,data['professors'],rs,faculty_review=faculty)
                self.assertIsNone(retained_career_field_lineage(field,rs))


if __name__=='__main__':unittest.main()
