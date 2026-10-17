import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

import test_matsci_own_fields as fixtures
from professor_own_field_reviews import verified_professor_fields, apply_professor_fields
from lab_resource_reviews import record_sha256


class RetainedMaterialsPrimaryTests(unittest.TestCase):
    def fixture(self, cache):
        helper=fixtures.MaterialsOwnFieldTests()
        item,_,person,_=helper.fixture(cache)
        row=helper.review(person,item,cache)
        uri=item['url'];publisher='https://matsci.ucsd.edu/index.php/faculty'
        href='/faculty/jane-example';date='2026-10-16T01:09:46+00:00'
        markup=f'<html><head><title>Faculty</title></head><body><main><a href="{href}">Jane Example</a></main></body></html>'
        path=cache/'responses'/(hashlib.sha256(publisher.encode()).hexdigest()+'.html')
        path.write_text(markup)
        parent={'url':publisher,'fetch':{'sourceUrl':publisher,'finalUrl':publisher,'status':'ok','httpStatus':200,
            'observedAt':date,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}
        previous=copy.deepcopy(person)
        previous.setdefault('fieldEvidence',{})['officialProfileUrl']=[{'sourceUrl':publisher,'observedAt':date,
            'method':'explicit_individual_profile_link_from_directory','status':'verified','evidence':'Jane Example → '+uri}]
        person['officialProfileUrl']='https://catalog.ucsd.edu/faculty/MAE.html'
        row.update(originalSourceProfessorRecord=copy.deepcopy(person),originalSourceRecordSha256=record_sha256(person),
            previousCompiledProfessorRecord=previous,previousCompiledProfessorRecordSha256=record_sha256(previous),
            retainedDirectoryPrimaryIdentity={'type':'retain_accepted_directory_selected_own_primary',
                'originalBaselineProfileUri':person['officialProfileUrl'],'retainedPrimaryUri':uri},
            publishedOriginalPrimaryEvidence={'requestedUrl':publisher,'sourceUrl':publisher,'observedAt':date,
                'bodySha256':parent['fetch']['sha256'],'evidenceType':'named_link','linkText':'Jane Example',
                'rawHref':href,'linkUrl':uri,'evidence':'Jane Example -> '+uri,'status':'verified'})
        listing={'name':'Jane Example','sourceUrl':publisher,'observedAt':date,'namedLinkUrl':uri,
            'identityMatchMethod':'explicit_directory_link_to_identity_matched_official_profile',
            'identityEvidence':{'sourceUrl':uri,'observedAt':item['fetch']['observedAt'],
                'method':'explicit_directory_link_to_official_profile_heading','evidence':'Jane Example','status':'verified'}}
        faculty={'byProfessorId':{person['id']:{'officialProfileUrl':uri,'verifiedCanonicalProfile':True,'directoryListings':[listing]}}}
        return row,{'items':{'own':item,'publisher':parent}},person,faculty,path

    def verify(self,row,q,person,faculty,cache):
        return verified_professor_fields({'entries':[row]},q,cache,[person],faculty_review=faculty)

    def test_previously_accepted_primary_is_retained_with_exact_current_source_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);row,q,person,faculty,_=self.fixture(cache)
            reviewed=self.verify(row,q,person,faculty,cache)
            before=copy.deepcopy(row['previousCompiledProfessorRecord']);data={'professors':[copy.deepcopy(before)]}
            apply_professor_fields(data,reviewed)
            self.assertEqual(data['professors'][0]['officialProfileUrl'],before['officialProfileUrl'])
            self.assertEqual(data['professors'][0]['id'],person['id'])
            self.assertEqual(data['professors'][0]['researchSummary'],row['fields']['researchSummary'])

    def test_missing_reselected_or_ambiguous_current_primary_is_rejected(self):
        for mode in ['missing','replacement','unqualified','duplicate-owner']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);row,q,person,faculty,_=self.fixture(cache);patch=faculty['byProfessorId'][person['id']]
                if mode=='missing':faculty=None
                if mode=='replacement':patch['officialProfileUrl']='https://profiles.ucsd.edu/jane.example'
                if mode=='unqualified':patch['verifiedCanonicalProfile']=False
                if mode=='duplicate-owner':faculty['byProfessorId']['another-scientist']=copy.deepcopy(patch)
                with self.assertRaises(ValueError):self.verify(row,q,person,faculty,cache)

    def test_shared_catalog_owners_do_not_become_owners_of_the_retained_individual_uri(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);row,q,person,faculty,_=self.fixture(cache)
            other=copy.deepcopy(person);other.update(id='other-person',name='Other Person')
            reviewed=verified_professor_fields({'entries':[row]},q,cache,[person,other],faculty_review=faculty)
            self.assertEqual(len(reviewed),1)
            self.assertEqual(reviewed[0]['professorId'],person['id'])

    def test_a_shared_catalog_page_without_retained_primary_review_still_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);row,q,person,faculty,_=self.fixture(cache)
            other=copy.deepcopy(person);other.update(id='other-person',name='Other Person')
            row.pop('retainedDirectoryPrimaryIdentity')
            with self.assertRaises(ValueError):
                verified_professor_fields({'entries':[row]},q,cache,[person,other],faculty_review=faculty)

    def test_historical_primary_cannot_be_replaced_or_fabricated(self):
        for mode in ['hash','old-primary','old-proof','individual-baseline']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);row,q,person,faculty,_=self.fixture(cache)
                if mode=='hash':row['previousCompiledProfessorRecordSha256']='changed'
                if mode=='old-primary':
                    row['previousCompiledProfessorRecord']['officialProfileUrl']='https://profiles.ucsd.edu/jane.example'
                    row['previousCompiledProfessorRecordSha256']=record_sha256(row['previousCompiledProfessorRecord'])
                if mode=='old-proof':
                    row['previousCompiledProfessorRecord']['fieldEvidence']['officialProfileUrl'][0]['evidence']='Someone else'
                    row['previousCompiledProfessorRecordSha256']=record_sha256(row['previousCompiledProfessorRecord'])
                if mode=='individual-baseline':
                    person['officialProfileUrl']='https://profiles.ucsd.edu/jane.example'
                    row['originalSourceProfessorRecord']=copy.deepcopy(person);row['originalSourceRecordSha256']=record_sha256(person)
                    row['retainedDirectoryPrimaryIdentity']['originalBaselineProfileUri']=person['officialProfileUrl']
                with self.assertRaises(ValueError):self.verify(row,q,person,faculty,cache)

    def test_literal_named_publisher_and_current_own_heading_dates_are_required(self):
        for mode in ['bytes','raw-href','duplicate','current-heading','date']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);row,q,person,faculty,path=self.fixture(cache)
                if mode=='bytes':path.write_text(path.read_text().replace('Jane Example','Other Person'))
                if mode=='raw-href':row['publishedOriginalPrimaryEvidence']['rawHref']='/faculty/another-person'
                if mode=='duplicate':
                    path.write_text(path.read_text().replace('</main>','<a href="/faculty/jane-example">Jane Example</a></main>'))
                    digest=hashlib.sha256(path.read_bytes()).hexdigest();q['items']['publisher']['fetch']['sha256']=digest
                    row['publishedOriginalPrimaryEvidence']['bodySha256']=digest
                identity=faculty['byProfessorId'][person['id']]['directoryListings'][0]['identityEvidence']
                if mode=='current-heading':identity['evidence']='Other Person'
                if mode=='date':identity['observedAt']='2026-10-17T00:00:00+00:00'
                with self.assertRaises(ValueError):self.verify(row,q,person,faculty,cache)

    def test_retained_scope_cannot_bind_another_uri_or_change_identity_or_fields(self):
        for mode in ['additional','template','department']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);row,q,person,faculty,_=self.fixture(cache)
                if mode=='additional':row['additionalSourceIdentity']={'requestedUrl':row['sourceObservation']['capture']['requestedUrl']}
                if mode=='template':row['sourceTemplate']='rady_profile_tabs_own_fields'
                if mode=='department':row['fields']['department']='Physics'
                with self.assertRaises(ValueError):self.verify(row,q,person,faculty,cache)


if __name__=='__main__':unittest.main()
