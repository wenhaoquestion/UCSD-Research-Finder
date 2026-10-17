import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_ucsd_preservation import audit
from lab_identity_merges import redirect_text
from lab_preferred_resources import verified_preferred_resources
from lab_profile_source_upgrades import KIND
from lab_resource_reviews import record_sha256, verified_alias_reviews
from rebuild_verified_atlas import build
from refresh_labs import make_lab, DOM, every_node
from test_atlas_quality import atlas


class ProfileOnlyLabUpgradeTests(unittest.TestCase):
    def fixture(self, path):
        old='https://pharmacy.ucsd.edu/faculty/example'
        own='https://example.ucsd.edu/'; http='http://example.ucsd.edu/'
        campus='https://program.ucsd.edu/faculty'; people=own+'people/'
        html={own:'<title>Example Lab</title><main><h1>Example Lab</h1><h2>Example Lab at UC San Diego</h2></main>',
              campus:'<title>Participating Faculty</title><main><div id="person"><a href="http://example.ucsd.edu">Lab Site</a><a href="'+old+'">Profile</a><h3>Jane Example</h3><p>Professor, School of Pharmacy</p></div><div id="other"><h3>Other Person</h3><a href="https://pharmacy.ucsd.edu/faculty/other">Profile</a></div></main>',
              people:'<title>People · Example Lab</title><main><article><h1 id="pi">PI <a href="#pi">Link to heading</a></h1><p>Jane Example</p><p><a href="info">More information</a></p><h1>Lab Members</h1><p>Other Person</p></article></main>'}
        html[http]=html[own]; (path/'responses').mkdir(); q={'items':{}}
        for uri,body in html.items():
            file=path/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');file.write_text(body)
            q['items'][uri]={'url':uri,'fetch':{'sourceUrl':uri,'finalUrl':own if uri==http else uri,
                'status':'ok','httpStatus':200,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
                'observedAt':'2026-10-16T12:00:00+00:00',
                'redirects':[{'from':http,'to':own,'httpStatus':301}] if uri==http else []}}
        q['items'][old]={'url':old,'fetch':{'sourceUrl':old,'finalUrl':old,'status':'http_error','httpStatus':500}}
        def proof(u,kind,text,**kw):
            m=q['items'][u]['fetch'];return {'requestedUrl':u,'sourceUrl':m['finalUrl'],'observedAt':m['observedAt'],
                'bodySha256':m['sha256'],'evidenceType':kind,'evidence':text,**kw}
        lab=make_lab('Example Lab',old,'Pharmacy and Pharmaceutical Sciences',
            {'sourceUrl':old,'observedAt':'2026-10-07T22:00:00+00:00'},'Skip to main content')
        lab.update(profile_only=True,sourceKind='profile_only',independentLabWebsiteVerified=False,
                   identityReview={'reason':'Profile-only descriptive label;independent lab not yet established.'})
        lab['fieldEvidence'] = {key:[value] for key,value in lab['fieldEvidence'].items()}
        data=atlas();data['professors']=[];data['labs']=[lab]
        card=next(n for n in every_node(DOM(html[campus]).main()) if n.attrs.get('id')=='person')
        proofs=[proof(campus,'main_text_quote',card.text()),
            proof(campus,'named_link','Profile -> '+old,linkText='Profile',linkUrl=old),
            proof(campus,'named_link','Lab Site -> '+http,linkText='Lab Site',linkUrl=http),
            proof(http,'redirect_chain',redirect_text(q['items'][http]['fetch']['redirects']),redirects=q['items'][http]['fetch']['redirects']),
            proof(own,'document_title','Example Lab'),proof(own,'document_heading','Example Lab',headingTag='h1'),
            proof(own,'document_heading','Example Lab at UC San Diego',headingTag='h2'),
            proof(people,'document_title','People · Example Lab'),
            proof(people,'main_text_quote','PI Link to heading Jane Example More information')]
        keys=['campusCardEvidence','campusProfileLinkEvidence','campusLabLinkEvidence','transportEvidence',
            'ownTitleEvidence','ownNameEvidence','ownInstitutionEvidence','ownPeopleTitleEvidence','ownPiSectionEvidence']
        binding=dict(zip(keys,proofs));binding.update(kind=KIND,baselineLabRecord=copy.deepcopy(lab),
            baselineLabRecordSha256=record_sha256(lab),campusDirectoryUrl=campus,
            campusCardSelectorAttributes={'id':'person'},personNameAsPublished='Jane Example',
            literalCampusLabHref='http://example.ucsd.edu',evidence=proofs)
        binding['departmentUnresolvedReason']='The person appointment does not prove a group academic department.'
        alias={'labId':lab['id'],'url':own,'fieldEvidence':proofs,'reason':'Literal named card and actual own lab.'}
        aliases=verified_alias_reviews({'entries':[{'labId':lab['id'],'url':own,'originalAliasRecord':alias,
            'originalAliasRecordSha256':record_sha256(alias),'reason':alias['reason'],'evidence':proofs[4:6]}]},[alias],q,path)
        row={'labId':lab['id'],'action':'select_preferred_lab_resource','previousPreferredUrl':old,'preferredUrl':own,
            'originalLabRecord':copy.deepcopy(lab),'originalLabRecordSha256':record_sha256(lab),'reason':alias['reason'],
            'evidence':proofs,'identityEvidence':[proofs[4],proofs[5]],'profileSourceUpgrade':binding}
        return data,q,row,alias,aliases

    def verified(self,path,data,q,row,aliases):
        return verified_preferred_resources({'entries':[row]},aliases,q,path,data['labs'])

    def test_upgrade_preserves_id_legacy_date_old_bad_proofs_and_replays_without_person_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data,q,row,alias,aliases=self.fixture(path);before=copy.deepcopy(data)
            rows=self.verified(path,data,q,row,aliases)
            coverage={'labAliases':[alias],'labAliasResourceReviews':aliases,'labPreferredResourceReviews':rows}
            first,*_=build(copy.deepcopy(data),{},{},{},{},coverage_evidence=coverage);lab=first['labs'][0]
            self.assertEqual(lab['id'],before['labs'][0]['id']); self.assertEqual(lab['lastVerified'],before['labs'][0]['lastVerified'])
            self.assertEqual(lab['labWebsiteUrl'],row['preferredUrl']);self.assertFalse(lab['profile_only']);self.assertTrue(lab['independentLabWebsiteVerified'])
            self.assertEqual(lab['principalInvestigator'],'Jane Example');self.assertEqual(lab['principalInvestigatorProfileUrl'],'Not found')
            self.assertEqual(lab['professorIds'],[]);self.assertEqual(first['professors'],[]);self.assertEqual(lab['contactEmail'],'Not found')
            self.assertEqual(lab['department'],'Unknown')
            self.assertTrue(any(x['field']=='department' and x['value']=='Pharmacy and Pharmaceutical Sciences' for x in lab['previousFieldObservations']))
            self.assertTrue(any(x['field']=='labName' and x['fieldEvidence']==before['labs'][0]['fieldEvidence']['labName'] for x in lab['previousFieldObservations']))
            self.assertEqual(audit(before,first)['status'],'passed')
            second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence=coverage);self.assertEqual(first,second);self.assertEqual(data,before)

    def test_profile_only_resource_cannot_use_the_generic_preference_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data,q,row,_,aliases=self.fixture(path);row.pop('profileSourceUpgrade')
            with self.assertRaisesRegex(ValueError,'unchanged baseline identity'):self.verified(path,data,q,row,aliases)

    def test_replayed_legacy_expansion_cannot_restore_defective_active_proofs_or_grow_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data,q,row,alias,aliases=self.fixture(path)
            rows=self.verified(path,data,q,row,aliases)
            expansion={'additions':copy.deepcopy(data['labs'])}
            coverage={'labAliases':[alias],'labAliasResourceReviews':aliases,'labPreferredResourceReviews':rows}
            first,*_=build(copy.deepcopy(data),{},{},{},{},coverage_evidence=coverage,lab_expansion=expansion)
            second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence=coverage,lab_expansion=expansion)
            self.assertEqual(first,second)
            for field in ['labName','labWebsiteUrl']:
                self.assertTrue(all('Skip to main content' not in p['evidence'] for p in first['labs'][0]['fieldEvidence'][field]))

    def test_a_real_profile_link_elsewhere_on_the_page_cannot_bind_this_card(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data,q,row,_,aliases=self.fixture(path);proof=row['profileSourceUpgrade']['campusProfileLinkEvidence']
            proof['linkUrl']='https://pharmacy.ucsd.edu/faculty/other';proof['evidence']='Profile -> '+proof['linkUrl']
            with self.assertRaisesRegex(ValueError,'same uniquely named campus card'):self.verified(path,data,q,row,aliases)

    def test_baseline_identity_and_exact_source_bytes_dates_transport_and_own_name_are_required(self):
        for mode in ['snapshot','name','body','date','redirect','literal','no-proof','person-edge']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp);data,q,row,_,aliases=self.fixture(path);binding=row['profileSourceUpgrade']
                if mode=='snapshot':binding['baselineLabRecord']['department']='Other'
                elif mode=='name':binding['ownNameEvidence']['evidence']='Another Lab'
                elif mode=='body':next((path/'responses').glob('*.html')).write_text('Changed')
                elif mode=='date':binding['ownTitleEvidence']['observedAt']='2026-10-17'
                elif mode=='redirect':q['items']['http://example.ucsd.edu/']['fetch']['redirects'][0]['from']='https://other.ucsd.edu/'
                elif mode=='literal':binding['literalCampusLabHref']='https://example.ucsd.edu/'
                elif mode=='no-proof':binding['evidence']=binding['evidence'][:-1]
                else:data['labs'][0]['professorIds']=['invented-person']
                with self.assertRaises(ValueError):self.verified(path,data,q,row,aliases)

    def test_a_published_lab_member_outside_the_pi_section_is_not_a_pi(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data,q,row,_,aliases=self.fixture(path);binding=row['profileSourceUpgrade']
            # This quotation really exists in the same own people page.
            binding['ownPiSectionEvidence']['evidence']='Lab Members Other Person'
            with self.assertRaisesRegex(ValueError,'single published name inside the explicit PI section'):
                self.verified(path,data,q,row,aliases)


if __name__=='__main__':unittest.main()
