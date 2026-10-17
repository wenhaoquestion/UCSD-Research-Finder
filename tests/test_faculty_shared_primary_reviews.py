import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from faculty_shared_primary_reviews import KIND, shared_primary_binding
from person_identity_reviews import verified_person_reviews, apply_person_reviews
from lab_resource_reviews import record_sha256
from audit_ucsd_preservation import audit
from rebuild_verified_atlas import build
from test_atlas_quality import atlas, professor


class SharedPrimaryIdentityTests(unittest.TestCase):
    def fixture(self, cache):
        source = professor('affiliate', 'Jane Example', 'Bioengineering')
        target = professor('canonical', 'Jane Alice Example', 'Medicine')
        own = 'https://profiles.ucsd.edu/jane.example'
        affiliate = 'https://be.ucsd.edu/faculty'
        medicine = 'https://med.ucsd.edu/about/faculty-directory.html'
        for person, roster in [(source, affiliate), (target, medicine)]:
            person.update(officialProfileUrl=own, sourceUrls=[own, roster])
        items = {}
        def save(uri, text):
            folder = cache/'responses'; folder.mkdir(exist_ok=True)
            raw=text.encode();(folder/(hashlib.sha256(uri.encode()).hexdigest()+'.html')).write_bytes(raw)
            items[uri]={'url':uri,'fetch':{'sourceUrl':uri,'finalUrl':uri,'status':'ok','httpStatus':200,
                                        'observedAt':'2026-01-01T00:00:00+00:00','sha256':hashlib.sha256(raw).hexdigest()}}
        save(affiliate, '<title>Faculty Profiles | Department of Bioengineering</title><main><div class="faculty-information"><h3><a href="'+own+'">Jane Example</a></h3><h6>Affiliate <h6></h6><a href="https://lab.ucsd.edu/">Example Research</a></h6></div></main>')
        save(medicine, '<main><h1>Department of Medicine Faculty Directory</h1><table id="datatable"><tr><td><a href="'+own+'">Example, Jane Alice, M.D., PhD</a></td><td>Cardiovascular Medicine</td></tr></table></main>')
        rdf='https://researcherprofiles.org/profile/123/123.rdf'
        save(own, '<head><title>Jane Example | UCSD Profiles</title><link rel="canonical" href="'+own+'"><link rel="alternate" type="application/rdf+xml" href="'+rdf+'"></head><main><div class="pageTitle"><h2>Jane Example</h2></div><table><tr><th>Title(s)</th><td>Professor, Medicine</td></tr><tr><th>School</th><td>Vc-health Sciences-schools</td></tr></table></main>')
        data=atlas();data.update(qualityMigrationVersion=1,professors=[target,source])
        q={'items':items};request={'sourceRosterRequestedUri':affiliate,'targetRosterRequestedUri':medicine}
        binding=shared_primary_binding(source,target,request,data['professors'],q,cache)
        def proof(uri,kind,text,**extra):
            m=items[uri]['fetch'];return {'requestedUrl':uri,'sourceUrl':uri,'observedAt':m['observedAt'],'bodySha256':m['sha256'],'evidenceType':kind,'evidence':text,**extra}
        card=proof(affiliate,'main_text_quote',binding['sourceNamedAffiliateCard']['cardText'])
        title=proof(affiliate,'document_title','Faculty Profiles | Department of Bioengineering')
        link=proof(affiliate,'named_link','Jane Example -> '+own,linkText='Jane Example',linkUrl=own)
        table=proof(medicine,'named_link','Example, Jane Alice, M.D., PhD -> '+own,linkText='Example, Jane Alice, M.D., PhD',linkUrl=own)
        dept=proof(medicine,'document_heading','Department of Medicine Faculty Directory',headingTag='h1')
        name=proof(own,'document_heading','Jane Example',headingTag='h2')
        canonical=proof(own,'html_attribute','link[href] = '+own,elementTag='link',attributeName='href',attributeValue=own,selectorAttributes={'rel':'canonical'})
        identifier=proof(own,'html_attribute','link[href] = '+rdf,elementTag='link',attributeName='href',attributeValue=rdf,selectorAttributes={'rel':'alternate','type':'application/rdf+xml'})
        appointment=proof(own,'main_text_quote','Professor, Medicine')
        source.update(appointmentStatus='affiliate',personalWebsiteUrl='https://lab.ucsd.edu/')
        source['fieldEvidence']={'appointmentStatus':[card],'personalWebsiteUrl':[proof(affiliate,'named_link','Example Research -> https://lab.ucsd.edu/',linkText='Example Research',linkUrl='https://lab.ucsd.edu/')]}
        target.update(appointmentStatus='listed_faculty',personalWebsiteUrl='Not found')
        target['fieldEvidence']={'appointmentStatus':[appointment]}
        row={'action':'merge','name':target['name'],'sourceProfessorId':source['id'],'targetProfessorId':target['id'],
             'originalSourceRecord':copy.deepcopy(source),'originalTargetRecord':copy.deepcopy(target),
             'sourceRecordSha256':record_sha256(source),'targetRecordSha256':record_sha256(target),
             'identityBasis':{'type':KIND,'value':rdf},'sharedPrimaryRequest':request,'sharedPrimaryBinding':binding,
             'fields':{'name':target['name'],'department':'Medicine','officialProfileUrl':own},
             'fieldEvidence':{'name':[table],'department':[appointment,dept],'officialProfileUrl':[canonical,table]},
             'departmentEvidence':[{'department':'Medicine','status':'own_appointment_as_listed','roleAsListed':'Professor, Medicine','fieldEvidence':[appointment,dept]},
                                   {'department':'Bioengineering','status':'affiliate_as_listed','roleAsListed':'Affiliate','fieldEvidence':[card,title]}],
             'previousCandidateObservations':[{'record':copy.deepcopy(p),'recordSha256':record_sha256(p),'candidateAtlasSha256':'a'*64} for p in [source,target]],
             'sourceCardEvidence':card,'sourceTitleEvidence':title,'sourceLinkEvidence':link,'targetLinkEvidence':table,
             'targetDepartmentEvidence':dept,'ownNameEvidence':name,'ownCanonicalEvidence':canonical,'ownRdfEvidence':identifier,'ownAppointmentEvidence':appointment,
             'evidence':[card,title,link,table,dept,name,canonical,identifier,appointment],
             'reason':'Independent original named directories literally link their shared named individual primary and personal RDF identifier.'}
        return data,q,row

    def test_shared_original_name_chain_preserves_full_names_ids_whole_snapshots_and_repeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,q,row=self.fixture(cache);before=copy.deepcopy(data)
            reviews=verified_person_reviews({'entries':[row]},q,cache,data);archives=apply_person_reviews(data,reviews)
            person=data['professors'][0];self.assertEqual(person['name'],'Jane Alice Example');self.assertEqual(person['aliasIds'],['affiliate']);self.assertEqual(person['aliasNames'],['Jane Example'])
            self.assertEqual(person['appointmentStatus'],'listed_faculty');self.assertEqual(person['personalWebsiteUrl'],'Not found');self.assertEqual(person['fieldEvidence']['appointmentStatus'],before['professors'][0]['fieldEvidence']['appointmentStatus']);self.assertEqual({x['field'] for x in person['additionalProfileObservations']},{'appointmentStatus','personalWebsiteUrl'})
            self.assertEqual(person['department'],'Medicine');self.assertEqual(set(person['departmentAffiliations']),{'Medicine','Bioengineering'})
            self.assertEqual([x['status'] for x in person['departmentAffiliationEvidence']],['own_appointment_as_listed','affiliate_as_listed'])
            snapshots=[x['value'] for x in person['previousFieldObservations'] if x['field']=='sharedPrimaryPreviousCandidate'];self.assertCountEqual(snapshots,before['professors'])
            self.assertEqual(audit(before,data,[archives])['status'],'passed');first=copy.deepcopy(data);self.assertEqual(apply_person_reviews(data,reviews),[]);self.assertEqual(first,data)

    def test_repeated_build_alias_patches_keep_full_target_name_and_scoped_rating_proofs(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,q,row=self.fixture(cache)
            for p,score in zip(data['professors'],[3.5,4.5]):
                uri='https://ratings.example/'+p['id'];p['ratings']={'rateMyProfessors':{'status':'verified','score':score,'sourceUrl':uri}};p.setdefault('fieldEvidence',{})['ratings.rateMyProfessors']=[{'sourceUrl':uri,'observedAt':'2020-01-01','evidence':str(score)}];p['sourceUrls'].append(uri)
            source,target=data['professors'][1],data['professors'][0]
            for key,p in [('Source',source),('Target',target)]:row['original'+key+'Record']=copy.deepcopy(p);row[key.lower()+'RecordSha256']=record_sha256(p)
            row['previousCandidateObservations']=[{'record':copy.deepcopy(p),'recordSha256':record_sha256(p),'candidateAtlasSha256':'a'*64} for p in [source,target]]
            reviews=verified_person_reviews({'entries':[row]},q,cache,data)
            captured={'byProfessorId':{'affiliate':{'name':'Jane Example','fieldEvidence':{'name':[row['ownNameEvidence']]}}}}
            first,_,_,archives=build(copy.deepcopy(data),captured,{},{},{},{},{},{},{'personIdentityReviews':reviews})
            person=first['professors'][0];self.assertEqual(person['name'],'Jane Alice Example');self.assertEqual(person['ratings']['rateMyProfessors']['score'],3.5)
            self.assertEqual(person['fieldEvidence']['ratings.rateMyProfessors'],target['fieldEvidence']['ratings.rateMyProfessors']);self.assertEqual(audit(data,first,[archives])['status'],'passed')
            repeated,*_=build(copy.deepcopy(first),captured,{},{},{},{},{},{},{'personIdentityReviews':reviews});self.assertEqual(first,repeated)

    def test_independent_named_roster_links_cannot_be_replaced_by_unscoped_links_or_nearby_people(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,q,row=self.fixture(cache)
            for uri,replacements in [(row['sharedPrimaryRequest']['sourceRosterRequestedUri'],[('faculty-information','other'),('</h6></div>','</h6><h6>Another role</h6></div>'),('Jane Example','Another Example'),('<h6>Affiliate','<h6>Professor'),('href="https://profiles.ucsd.edu/jane.example"','href="https://profiles.ucsd.edu/other.example"')]),
                                     (row['sharedPrimaryRequest']['targetRosterRequestedUri'],[('id="datatable"','id="other"'),('Jane Alice','Another Alice'),('Department of Medicine','Department of Staff')])]:
                path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');original=path.read_text()
                for old,new in replacements:
                    path.write_text(original.replace(old,new));state=copy.deepcopy(q);state['items'][uri]['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                    with self.subTest(uri=uri,change=new),self.assertRaises(ValueError):shared_primary_binding(data['professors'][1],data['professors'][0],row['sharedPrimaryRequest'],data['professors'],state,cache)
                path.write_text(original)

    def test_generic_or_conflicting_own_identifiers_and_appointment_cannot_supply_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,q,row=self.fixture(cache);uri=data['professors'][0]['officialProfileUrl'];path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');original=path.read_text()
            for old,new in [('Jane Example','Another Example'),('/123/123.rdf','/124/124.rdf'),('rel="canonical" href="'+uri,'rel="canonical" href="https://profiles.ucsd.edu/search'),('Professor, Medicine','Professor, Surgery')]:
                path.write_text(original.replace(old,new));state=copy.deepcopy(q);state['items'][uri]['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                with self.subTest(change=new),self.assertRaises(ValueError):verified_person_reviews({'entries':[row]},state,cache,data)
            path.write_text(original)

    def test_changed_records_snapshots_missing_proofs_or_third_original_owner_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,q,row=self.fixture(cache)
            for mode in ['snapshot','original','binding','third_owner','missing_proof','invented_affiliation']:
                baseline=copy.deepcopy(data);r=copy.deepcopy(row)
                if mode=='snapshot':r['previousCandidateObservations'][0]['record']['name']='Changed'
                elif mode=='original':r['originalTargetRecord']['name']='Changed'
                elif mode=='binding':r['sharedPrimaryBinding']['ownProfile']['rdfAlternateUri']='https://researcherprofiles.org/profile/999/999.rdf'
                elif mode=='third_owner':baseline['professors'].append({**copy.deepcopy(baseline['professors'][0]),'id':'third'})
                elif mode=='missing_proof':r['evidence'].remove(r['ownRdfEvidence'])
                else:r['departmentEvidence'][1]['status']='primary_appointment'
                with self.subTest(mode=mode),self.assertRaises(ValueError):verified_person_reviews({'entries':[r]},q,cache,baseline)


if __name__=='__main__':unittest.main()
