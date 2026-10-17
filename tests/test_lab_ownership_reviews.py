import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from lab_ownership_reviews import KIND, UCSD, verified_lab_ownership_reviews, apply_lab_ownership_reviews
from lab_resource_reviews import record_sha256


class LabOwnershipReviewTests(unittest.TestCase):
    def fixture(self, cache):
        home, contact = 'https://lab.example/', 'https://lab.example/contact/'
        title = 'Home | Example Lab - Research Institute'
        address = 'EXAMPLE LABORATORY The Research Institute 100 Research Road City, CA 12345'
        documents = {
            home:f'<title>{title}</title><nav><a href="{contact}">Contact Us</a></nav><main><h1>Example Lab</h1></main>',
            contact:f'<title>Contact | Example Lab - Research Institute</title><main><h5>Contact Us</h5><p>{address}</p></main>'}
        queue = {'items':{}}
        (cache/'responses').mkdir()
        for uri, markup in documents.items():
            path = cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.write_text(markup)
            queue['items'][uri] = {'url':uri,'fetch':{'status':'ok','sourceUrl':uri,'finalUrl':uri,
                'observedAt':'2020-01-01T00:00:00+00:00','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}
        def proof(uri, kind, text, **extra):
            m = queue['items'][uri]['fetch']
            return {'requestedUrl':uri,'sourceUrl':uri,'observedAt':m['observedAt'],'bodySha256':m['sha256'],
                    'evidenceType':kind,'evidence':text,**extra}
        identity = proof(home,'document_heading','Example Lab',headingTag='h1')
        named_title = proof(home,'document_title',title)
        link = proof(home,'html_attribute','a[href] = '+contact,elementTag='a',attributeName='href',attributeValue=contact)
        contact_title = proof(contact,'document_title','Contact | Example Lab - Research Institute')
        claim = proof(contact,'main_text_quote',address,method='reviewed_own_lab_contact_institution')
        lab = {'id':'old-lab-id','labName':'Daniel Example Lab','institution':UCSD,'department':'Biological Sciences',
               'labWebsiteUrl':home.rstrip('/'),'principalInvestigator':'Daniel W. Example','recordSubtype':'lab',
               'fieldEvidence':{},'sourceUrls':['https://campus.ucsd.edu/research'], 'lastVerified':'2019-01-01',
               'websiteCheck':{'status':'reachable','sourceUrl':home.rstrip('/'),'observedAt':'2019-01-01','title':title}}
        row = {'kind':KIND,'labId':lab['id'],'originalLabRecord':copy.deepcopy(lab),
               'originalLabRecordSha256':record_sha256(lab),'primaryRequestedUri':home,'contactRequestedUri':contact,
               'ownLabNameAsDisplayed':'Example Lab','institution':'Research Institute',
               'institutionAsDisplayed':'The Research Institute',
               'departmentContextReview':{'action':'retain_unverified_routing_context','previousDepartment':'Biological Sciences'},
               'ownIdentityEvidence':identity,'ownTitleEvidence':named_title,'contactLinkEvidence':link,
               'contactTitleEvidence':contact_title,'institutionEvidence':claim,
               'evidence':[identity,named_title,link,contact_title,claim],
               'reason':'The named own lab contact identifies its institution; retain the earlier campus routing context independently.'}
        return lab, queue, {'entries':[row]}

    def rewrite(self, queue, cache, review, uri, old, new):
        path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html')
        path.write_text(path.read_text().replace(old,new));digest=hashlib.sha256(path.read_bytes()).hexdigest()
        queue['items'][uri]['fetch']['sha256']=digest
        for p in review['entries'][0]['evidence']:
            if p['requestedUrl']==uri:p['bodySha256']=digest

    def test_real_interface_corrects_only_unsupported_ownership_and_retains_history_id_and_people(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);lab,q,review=self.fixture(cache);inputs=copy.deepcopy((lab,q,review))
            verified=verified_lab_ownership_reviews(review,q,cache,[lab])
            data={'labs':[copy.deepcopy(lab)],'professors':[{'id':'untouched-person','name':'Daniel W. Example'}]}
            apply_lab_ownership_reviews(data,verified);updated=data['labs'][0]
            self.assertEqual(updated['id'],lab['id']);self.assertEqual(updated['institution'],'Research Institute')
            self.assertEqual(updated['department'],'Unknown');self.assertEqual(updated['principalInvestigator'],lab['principalInvestigator'])
            self.assertEqual(updated['labWebsiteUrl'],lab['labWebsiteUrl']);self.assertEqual(updated['websiteCheck'],lab['websiteCheck'])
            self.assertEqual(updated['lastVerified'],lab['lastVerified']);self.assertEqual(data['professors'],[{'id':'untouched-person','name':'Daniel W. Example'}])
            self.assertEqual({p['field']:p['value'] for p in updated['previousFieldObservations']},
                             {'institution':UCSD,'department':'Biological Sciences'})
            self.assertEqual(updated['labOwnershipReviews'][0]['originalLabRecord'],lab)
            self.assertNotIn('department',updated['fieldEvidence'])
            repeated=copy.deepcopy(data);apply_lab_ownership_reviews(data,verified);self.assertEqual(data,repeated)
            self.assertEqual((lab,q,review),inputs)

    def test_stale_dates_bytes_labels_and_original_records_fail_closed(self):
        for mode in ['date','bytes','name','record','missing_scope']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);lab,q,review=self.fixture(cache);row=review['entries'][0]
                if mode=='date':row['institutionEvidence']['observedAt']='2030-01-01'
                elif mode=='bytes':row['institutionEvidence']['bodySha256']='changed'
                elif mode=='name':row['ownLabNameAsDisplayed']='Different Lab'
                elif mode=='record':row['originalLabRecord']['institution']='Different legacy institution'
                else:row.pop('departmentContextReview')
                with self.assertRaises(ValueError):verified_lab_ownership_reviews(review,q,cache,[lab])

    def test_verified_department_or_institution_and_duplicate_resource_owners_cannot_be_overwritten(self):
        for field in ['department','institution','duplicate_owner']:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);lab,q,review=self.fixture(cache);labs=[lab]
                if field=='duplicate_owner':
                    other=copy.deepcopy(lab);other['id']='another-lab-id';labs.append(other)
                else:
                    lab['fieldEvidence'][field]=[{'evidence':'a verified own affiliation'}]
                    review['entries'][0]['originalLabRecord']=copy.deepcopy(lab)
                    review['entries'][0]['originalLabRecordSha256']=record_sha256(lab)
                with self.assertRaises(ValueError):verified_lab_ownership_reviews(review,q,cache,labs)

    def test_named_navigation_and_own_contact_heading_are_required_even_with_current_byte_proofs(self):
        for mode in ['body_link','biography_heading','old_named_resource']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);lab,q,review=self.fixture(cache);row=review['entries'][0]
                if mode=='body_link':
                    self.rewrite(q,cache,review,row['primaryRequestedUri'],'<nav>','<div>')
                    self.rewrite(q,cache,review,row['primaryRequestedUri'],'</nav>','</div>')
                elif mode=='biography_heading':self.rewrite(q,cache,review,row['contactRequestedUri'],'<h5>Contact Us</h5>','<h5>Biography</h5>')
                else:
                    lab['websiteCheck']['title']='Different old lab';row['originalLabRecord']=copy.deepcopy(lab)
                    row['originalLabRecordSha256']=record_sha256(lab)
                with self.assertRaises(ValueError):verified_lab_ownership_reviews(review,q,cache,[lab])

    def test_unrequested_scheme_variant_and_shared_host_entity_paths_are_not_own_contact_scope(self):
        for mode in ['scheme','path']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);lab,q,review=self.fixture(cache);row=review['entries'][0]
                if mode=='scheme':lab['labWebsiteUrl']='http://lab.example/'
                else:lab['labWebsiteUrl']='https://lab.example/another-group/'
                row['originalLabRecord']=copy.deepcopy(lab);row['originalLabRecordSha256']=record_sha256(lab)
                with self.assertRaises(ValueError):verified_lab_ownership_reviews(review,q,cache,[lab])
