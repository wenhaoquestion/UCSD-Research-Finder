import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from apply_ucsd_coverage import reviewed_lab_records
from lab_program_affiliations import verified_program_affiliate_labs, KIND
from lab_resource_reviews import record_sha256
from refresh_labs import DOM, every_node, make_lab


class ProgramAffiliateLabTests(unittest.TestCase):
    def fixture(self, root, contact=False, canonical_contact="contact@partner.org"):
        own='https://example-lab.org/'; program='https://program.ucsd.edu/faculty'
        html={own:'<html><head><title>Example Lab</title></head><body><main><div id="contact">Example Lab Partner Institute 100 Science Road</div><p>For UCSD graduate students, we consider rotation students from across all programs and backgrounds.</p></main></body></html>',
              program:'<html><head><title>Faculty | Example Graduate Program</title></head><body><main><div id="person"><h3>Jane Example</h3><span>Assistant Professor, Partner Institute</span><a href="https://example-lab.org/">Lab Site</a></div><div><h3>Another Person</h3><a href="https://example-lab.org/">Other lab</a></div></main></body></html>'}
        if contact:
            html[own]=html[own].replace('100 Science Road','100 Science Road contact [at] partner.org')
            html[program]=html[program].replace('Partner Institute</span>','Partner Institute</span><span>Email: '+canonical_contact+'</span>')
        (root/'responses').mkdir();q={'items':{},'labCandidates':{}}
        for u,raw in html.items():
            m={'status':'ok','httpStatus':200,'sourceUrl':u,'finalUrl':u,'observedAt':'2026-10-16T01:00:00+00:00','sha256':hashlib.sha256(raw.encode()).hexdigest(),'redirects':[]}
            (root/'responses'/(hashlib.sha256(u.encode()).hexdigest()+'.html')).write_text(raw);q['items'][u]={'url':u,'fetch':m}
        def proof(u,text,kind='main_text_quote',**extra):
            m=q['items'][u]['fetch'];return {'requestedUrl':u,'sourceUrl':u,'observedAt':m['observedAt'],'bodySha256':m['sha256'],'evidenceType':kind,'evidence':text,**extra}
        raw=make_lab('Lab Site',own,'Interdisciplinary',q['items'][own]['fetch'],'Lab Site');raw['institution']='Unknown';raw['professorIds']=[];q['labCandidates'][own]={'record':copy.deepcopy(raw)}
        identity=proof(own,'Example Lab','document_title');inst=proof(own,next(n.text() for n in every_node(DOM(html[own]).main()) if n.attrs.get('id')=='contact'));access=proof(own,'For UCSD graduate students, we consider rotation students from across all programs and backgrounds.');pr=proof(program,'Faculty | Example Graduate Program','document_title');card=next(n for n in every_node(DOM(html[program]).main()) if n.attrs.get('id')=='person');cardp=proof(program,card.text());link=proof(program,'Lab Site -> '+own,'named_link',linkText='Lab Site',linkUrl=own)
        review={'kind':KIND,'labId':raw['id'],'labWebsiteUrl':own,'originalRequestedUri':own,'originalSourceRecord':copy.deepcopy(raw),'originalSourceRecordSha256':record_sha256(raw),'institution':'Partner Institute','programName':'Example Graduate Program','programSourceUrl':program,'facultyNameAsListed':'Jane Example','facultyRoleAsListed':'Assistant Professor, Partner Institute','campusCardSelectorAttributes':{'id':'person'},'ownIdentityEvidence':identity,'ownInstitutionEvidence':inst,'ownStudentAccessEvidence':access,'programEvidence':pr,'campusCardEvidence':cardp,'campusLabLinkEvidence':link,'evidence':[identity,inst,access,pr,cardp,link],'reason':'Separate actual external ownership from the listed graduate-program connection.'}
        if contact:review['encodedContactEmail']={'rawText':'contact [at] partner.org','canonicalEmail':'contact@partner.org'}
        decision={'action':'accept','stableLabId':raw['id'],'name':'Example Lab','institution':'Partner Institute','institutionEvidence':[inst],'identityEvidence':[identity],'departmentUnresolvedReason':'Program listing is not a lab academic department.','programAffiliationReview':review,'reason':'Explicit external ownership and program-specific rotation guidance.'}
        proposal={'urlKey':own,'status':'unresolved','record':copy.deepcopy(raw),'destinationCheck':q['items'][own]['fetch']}
        labs,*_=reviewed_lab_records({'labs':[]},[proposal],{'labs':{own:decision}})
        return labs,q

    def test_actual_handoff_construction_preserves_external_owner_and_id_without_inventing_pi_or_person(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);labs,q=self.fixture(root);before=copy.deepcopy((labs,q));verified=verified_program_affiliate_labs(labs,q,root);lab=verified[0]
            self.assertEqual(lab['websiteCheck']['observedAt'],'2026-10-16T01:00:00+00:00');self.assertEqual(lab['verification']['lastAttemptedAt'],lab['websiteCheck']['observedAt']);
            self.assertEqual(lab['institution'],'Partner Institute');self.assertEqual(lab['department'],'Unknown');self.assertEqual(lab['principalInvestigator'],'Not found');self.assertEqual(lab['professorIds'],[]);self.assertEqual(lab['campusProgramRelationships'][0]['programName'],'Example Graduate Program');self.assertEqual(lab['id'],labs[0]['id']);self.assertEqual((labs,q),before);self.assertEqual(verified_program_affiliate_labs(verified,q,root),verified)

    def test_bracket_at_contact_requires_both_exact_own_encoding_and_canonical_program_address(self):
        from apply_ucsd_coverage import validate_reviewed_contacts
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);labs,q=self.fixture(root,contact=True);verified=verified_program_affiliate_labs(labs,q,root)
            self.assertEqual(verified[0]['contactEmail'],'contact@partner.org');validate_reviewed_contacts(verified,q,root)
            for field,value in [('rawText','invented [at] partner.org'),('canonicalEmail','guessed@partner.org')]:
                bad=copy.deepcopy(labs);bad[0]['programAffiliationReview']['encodedContactEmail'][field]=value
                with self.assertRaises(ValueError):verified_program_affiliate_labs(bad,q,root)
            missing=copy.deepcopy(verified);missing[0]['programAffiliationReview'].pop('encodedContactEmail')
            with self.assertRaises(ValueError):validate_reviewed_contacts(missing,q,root)
            bad=copy.deepcopy(verified);bad[0]['contactEmail']='other@partner.org'
            with self.assertRaises(ValueError):validate_reviewed_contacts(bad,q,root)

        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);labs,q=self.fixture(root,contact=True,canonical_contact='notcontact@partner.org')
            with self.assertRaises(ValueError):verified_program_affiliate_labs(labs,q,root)

    def test_explicit_foreign_decision_without_program_review_cannot_fall_back_to_ucsd(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);labs,q=self.fixture(root);lab=labs[0];row=lab['programAffiliationReview'];raw=row['originalSourceRecord'];u=row['originalRequestedUri']
            decision={'action':'accept','stableLabId':raw['id'],'name':'Example Lab','institution':'Partner Institute','institutionEvidence':[row['ownInstitutionEvidence']],'identityEvidence':[row['ownIdentityEvidence']],'reason':'An external declaration cannot be silently overwritten.'}
            proposal={'urlKey':u,'status':'unresolved','record':raw,'destinationCheck':q['items'][u]['fetch']}
            with self.assertRaisesRegex(ValueError,'explicit external institution'):
                reviewed_lab_records({'labs':[]},[proposal],{'labs':{u:decision}})

    def test_external_institution_cannot_be_relabelled_as_ucsd_or_accepted_without_review(self):
        for field,value in [('institution','University of California San Diego'),('programAffiliationReview',None),('department','Biology'),('professorIds',['guessed-person'])]:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);labs,q=self.fixture(root);labs[0][field]=value
                with self.assertRaises(ValueError):verified_program_affiliate_labs(labs,q,root)

    def test_lab_link_elsewhere_on_program_page_does_not_bind_the_selected_faculty_card(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);labs,q=self.fixture(root);u='https://program.ucsd.edu/faculty';path=root/'responses'/(hashlib.sha256(u.encode()).hexdigest()+'.html');path.write_text(path.read_text().replace('href="https://example-lab.org/">Lab Site','href="https://another-lab.org/">Lab Site').replace('>Other lab<','>Lab Site<'));digest=hashlib.sha256(path.read_bytes()).hexdigest();q['items'][u]['fetch']['sha256']=digest
            for p in labs[0]['programAffiliationReview']['evidence']:
                if p['requestedUrl']==u:p['bodySha256']=digest
            with self.assertRaisesRegex(ValueError,'one program card'):verified_program_affiliate_labs(labs,q,root)

    def test_affiliation_requires_own_rotation_guidance_and_named_contact_not_an_email_host(self):
        for key in ['ownStudentAccessEvidence','ownInstitutionEvidence']:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);labs,q=self.fixture(root);row=labs[0]['programAffiliationReview'];row[key]=row['campusCardEvidence']
                with self.assertRaises(ValueError):verified_program_affiliate_labs(labs,q,root)

    def test_tampered_capture_and_frozen_source_id_are_rejected(self):
        for change in ['body','id']:
            with self.subTest(change=change),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);labs,q=self.fixture(root)
                if change=='body':next((root/'responses').glob('*.html')).write_text('Changed')
                else:labs[0]['id']='invented-id'
                with self.assertRaises(ValueError):verified_program_affiliate_labs(labs,q,root)


if __name__=='__main__':unittest.main()
