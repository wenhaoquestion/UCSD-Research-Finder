import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from professor_contact_scope_reviews import (IDENTITY, apply_contact_scopes, contact_payload,
    directory_email_scope, email_proofs, site_feedback_scope, verified_contact_scopes)
from lab_resource_reviews import record_sha256
from rebuild_verified_atlas import build, merge_patch
from test_atlas_quality import atlas, professor


class ContactScopeTests(unittest.TestCase):
    def fixture(self, cache, encoded=False, feedback=False, own=False):
        uri = 'https://literature.ucsd.edu/people/contact.html' if feedback else 'https://department.ucsd.edu/people/faculty/index.html'
        primary = 'https://literature.ucsd.edu/people/faculty/memoriam-jane.html' if feedback else 'https://profiles.ucsd.edu/jane.example'
        old = 'litinfo@ucsd.edu' if feedback else '%20jane@ucsd.edu' if encoded else 'another@ucsd.edu'
        person = professor('jane', 'Jane Q. Example', 'Literature' if feedback else 'Medicine')
        person.update(officialProfileUrl=primary, email=old, sourceUrls=[primary, uri],
                      fieldEvidence={'email': [{'sourceUrl':primary if feedback else uri,
                          'observedAt':'2026-10-16T01:00:00+00:00',
                          'method':'identity_matched_profile_unique_contact' if feedback else 'explicit_person_card_value',
                          'evidence':old,'status':'verified'}]})
        if feedback:
            markup = '<main><h1>Contact</h1><h3>Mailing Address</h3><p>Literature Department</p></main><footer><ul class="footer-links"><li><a href="mailto:litinfo@ucsd.edu">Feedback</a></li></ul></footer>'
        else:
            title = '<p class="h3">Jane Example, PhD</p>' if own else '<h3><a href="'+primary+'">Jane Example, PhD</a></h3>'
            markup = '<main><ul><li class="profile-listing-card"><span class="profile-listing-data">'+title+'<p>Assistant Professor</p><a href="mailto:'+old+'">jane@ucsd.edu</a></span></li><li class="profile-listing-card"><span class="profile-listing-data"><h3>Another Person</h3><a href="mailto:unrelated@ucsd.edu">unrelated@ucsd.edu</a></span></li></ul></main>'
        def capture(uri, body):
            path = cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html')
            path.parent.mkdir(exist_ok=True); path.write_text(body)
            return {'url':uri,'state':'done','fetch':{'sourceUrl':uri,'finalUrl':uri,'httpStatus':200,
                'status':'ok','observedAt':'2026-10-16T01:00:00+00:00','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}, path
        item, path = capture(uri, markup); q = {'items':{uri:item}}; own_item = None
        if own:
            own_item, _ = capture(primary,'<head><link rel="canonical" href="'+primary+'"><link rel="alternate" type="application/rdf+xml" href="https://researcherprofiles.org/profile/123/123.rdf"></head><main><div class="pageTitle"><h2>Jane Example</h2></div></main>')
            q['items'][primary] = own_item
        scope = site_feedback_scope(item,cache) if feedback else directory_email_scope(item,cache,person,own_item)
        row = {'professorId':person['id'],'originalPersonIdentity':{k:person[k] for k in IDENTITY},
               'retainedCanonicalIdentity':{k:person[k] for k in IDENTITY},'sourceCandidateAtlasSha256':'a'*64,
               'previousEmail':old,'previousEmailEvidence':copy.deepcopy(email_proofs(person)),
               'sourceScope':scope,'disposition':'hold_shared_site_feedback_as_personal_email' if feedback else 'correct_published_directory_email',
               'reason':'Preserve the original exact contact and all evidence as history; do not infer a person merge or change a canonical identity.'}
        row['previousEmailSha256'] = record_sha256({'email':old,'fieldEvidence':row['previousEmailEvidence']})
        row['email'], row['fieldEvidence'] = contact_payload(row)
        return person,item,row,path,q

    def test_displayed_email_overrides_another_persons_mailto_without_identity_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            person,_,row,_,q = self.fixture(Path(tmp)); before = copy.deepcopy(person)
            checked = verified_contact_scopes({'entries':[row]},q,Path(tmp),{person['id']:person})
            apply_contact_scopes({'professors':[person]},checked)
            self.assertEqual(person['email'],'jane@ucsd.edu')
            self.assertEqual(person['fieldEvidence']['email'][0]['rawMailtoHref'],'mailto:another@ucsd.edu')
            self.assertEqual(person['fieldEvidence']['email'][0]['observedAt'],'2026-10-16T01:00:00+00:00')
            self.assertTrue(any(o['value']==before['email'] and o['fieldEvidence']==email_proofs(before) for o in person['previousFieldObservations']))
            for key in [*IDENTITY,'lastVerified','recruitingStatus']:
                self.assertEqual(person[key],before[key])
            applied=copy.deepcopy(person);apply_contact_scopes({'professors':[person]},checked);self.assertEqual(applied,person)

    def test_encoded_whitespace_is_supported_by_the_literal_display_not_inferred(self):
        with tempfile.TemporaryDirectory() as tmp:
            person,_,row,_,q = self.fixture(Path(tmp),encoded=True)
            checked=verified_contact_scopes({'entries':[row]},q,Path(tmp),{person['id']:person})
            self.assertEqual(checked[0]['sourceScope']['conflictKind'],'encoded_whitespace_in_mailto')
            self.assertEqual(checked[0]['email'],'jane@ucsd.edu')

    def test_a_card_without_a_primary_link_needs_an_independent_retained_own_subject(self):
        with tempfile.TemporaryDirectory() as tmp:
            person,item,row,_,q=self.fixture(Path(tmp),own=True)
            checked=verified_contact_scopes({'entries':[row]},q,Path(tmp),{person['id']:person})
            self.assertEqual(checked[0]['sourceScope']['sourceIdentity']['kind'],'independent_retained_profiles_subject')
            with self.assertRaises(ValueError):directory_email_scope(item,Path(tmp),person)
            q['items'][person['officialProfileUrl']]['fetch']['observedAt']='2026-10-17T01:00:00+00:00'
            with self.assertRaises(ValueError):verified_contact_scopes({'entries':[row]},q,Path(tmp),{person['id']:person})

    def test_feedback_is_retained_with_its_actual_role_without_a_personal_email_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            person,_,row,_,q=self.fixture(Path(tmp),feedback=True)
            person['verification']={'status':'source_checked','lastEvidenceAt':'2026-10-16T01:00:00+00:00'}
            before=copy.deepcopy(person)
            checked=verified_contact_scopes({'entries':[row]},q,Path(tmp),{person['id']:person});apply_contact_scopes({'professors':[person]},checked)
            self.assertEqual(person['email'],'Not found');self.assertNotIn('email',person['fieldEvidence'])
            self.assertEqual(person['sharedSiteContactObservations'][0]['roleAsPublished'],'Feedback')
            self.assertEqual(person['sharedSiteContactObservations'][0]['email'],'litinfo@ucsd.edu')
            self.assertEqual(person['lastVerified'],before['lastVerified'])
            self.assertEqual(person['verification']['status'],'legacy_unverified')
            self.assertNotIn('lastEvidenceAt',person['verification'])
            self.assertTrue(any(o['value']==before['email'] for o in person['previousFieldObservations']))

    def test_catalog_original_keeps_its_identity_while_the_retained_own_subject_scopes_the_contact(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);retained,_,row,_,q=self.fixture(cache,own=True)
            original=copy.deepcopy(retained);original['officialProfileUrl']='https://catalog.ucsd.edu/faculty/TEST.html'
            row['originalPersonIdentity']={key:original[key] for key in IDENTITY}
            people={original['id']:original}
            checked=verified_contact_scopes({'entries':[row]},q,cache,people)
            apply_contact_scopes({'professors':[retained]},checked)
            self.assertEqual(retained['officialProfileUrl'],'https://profiles.ucsd.edu/jane.example')
            self.assertEqual(original['officialProfileUrl'],'https://catalog.ucsd.edu/faculty/TEST.html')
            self.assertEqual(retained['email'],'jane@ucsd.edu')
            people['ambiguous']={**original,'id':'ambiguous','department':'Another Department'}
            with self.assertRaises(ValueError):verified_contact_scopes({'entries':[row]},q,cache,people)

    def test_source_owner_card_quote_capture_and_payload_tampering_fail_closed(self):
        for mode in ['bytes','date','person','other_card','card_quote','display','primary_owner','duplicate']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);person,item,row,path,q=self.fixture(cache);people={person['id']:person};rows=[row]
                if mode=='bytes':path.write_text(path.read_text()+'changed')
                if mode=='date':item['fetch']['observedAt']='2026-10-17T01:00:00+00:00'
                if mode=='person':person['name']='Another Person'
                if mode=='other_card':row['sourceScope']['nameAsDisplayed']='Another Person'
                if mode=='card_quote':row['sourceScope']['cardText']+=' invented assertion'
                if mode=='display':row['email']='unpublished@ucsd.edu'
                if mode=='primary_owner':people['other']={**person,'id':'other'}
                if mode=='duplicate':rows.append(copy.deepcopy(row))
                with self.assertRaises(ValueError):verified_contact_scopes({'entries':rows},q,cache,people)

    def test_feedback_cannot_replace_independent_personal_contact_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,_,row,_,q=self.fixture(cache,feedback=True)
            row['previousEmailEvidence'][0]['method']='named_math_own_public_email_field'
            row['previousEmailSha256']=record_sha256({'email':row['previousEmail'],'fieldEvidence':row['previousEmailEvidence']})
            with self.assertRaises(ValueError):verified_contact_scopes({'entries':[row]},q,cache,{person['id']:person})

    def test_newer_email_proof_blocks_a_stale_decision_before_any_batch_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,_,row,_,q=self.fixture(cache);checked=verified_contact_scopes({'entries':[row]},q,cache,{person['id']:person})
            other=copy.deepcopy(person);other['id']='other';other['email']='new@ucsd.edu';other_row=copy.deepcopy(checked[0]);other_row['professorId']='other';other_row['retainedCanonicalIdentity']['id']='other';data={'professors':[person,other]};before=copy.deepcopy(data)
            with self.assertRaises(ValueError):apply_contact_scopes(data,checked+[other_row])
            self.assertEqual(data,before)

    def test_full_assembly_and_old_patch_replay_preserve_the_reviewed_contact(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,_,row,_,q=self.fixture(cache);checked=verified_contact_scopes({'entries':[row]},q,cache,{person['id']:person})
            data=atlas();data.update(professors=[person],qualityMigrationVersion=1)
            patch={'fields':{'email':person['email']},'fieldEvidence':{'email':copy.deepcopy(email_proofs(person))}}
            coverage={'byProfessorId':{person['id']:patch},'reviewedProfessorContactScopes':checked}
            first,*_=build(data,{},{},{},{},coverage_evidence=coverage)
            repeated,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence=coverage)
            self.assertEqual(first,repeated);self.assertEqual(first['professors'][0]['email'],'jane@ucsd.edu')
            before=copy.deepcopy(first['professors'][0]);merge_patch(first['professors'][0],patch);self.assertEqual(before,first['professors'][0])
