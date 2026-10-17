import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from apply_ucsd_coverage import reviewed_lab_records
from lab_identity_merges import redirect_text
from lab_research_resource_reviews import KIND, verified_new_lab_scopes
from lab_resource_reviews import record_sha256
from refresh_labs import DOM, every_node, make_lab


class CampusResearchResourceTests(unittest.TestCase):
    def fixture(self, root):
        own = 'https://example.ucsd.edu/'
        http = 'http://example.ucsd.edu/'
        team = own+'our-team/'
        directory = 'https://institute.ucsd.edu/people/'
        mission = 'We explore higher order cognition at the intersection between mind, brain, and body.'
        role = 'Project Director JANE M EXAMPLE ASSISTANT RESEARCH SCIENTIST Institute, UCSD'
        group = 'The website showcases the projects of the Example lab.'
        html = {
            own: '<html><head><title>Example – Jane Example research</title></head><body><header><a href="'+own+'">Example</a></header><main><p>'+mission+'</p></main></body></html>',
            team: '<html><head><title>Our Team – Example</title></head><body><main><h1>Our Team</h1><h2>Project Director</h2><div>JANE M EXAMPLE ASSISTANT RESEARCH SCIENTIST Institute, UCSD</div><h2>Current Research Assistants</h2><p>'+group+'</p></main></body></html>',
            directory: '<html><head><title>Core Faculty</title></head><body><main><div class="card"><h3>Jane Example</h3><p>Assistant Research Scientist</p><a href="http://example.ucsd.edu">Lab Web Site</a></div><div class="card"><h3>Other Person</h3><a href="http://other.ucsd.edu">Lab Web Site</a></div></main></body></html>'}
        html[http] = html[own]
        (root/'responses').mkdir()
        queue = {'items': {}, 'labCandidates': {}}
        for uri, body in html.items():
            (root/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html')).write_text(body)
            queue['items'][uri] = {'url': uri, 'fetch': {'sourceUrl': uri, 'status': 'ok',
                'httpStatus': 200, 'finalUrl': own if uri == http else uri,
                'observedAt': '2026-10-16T01:00:00+00:00', 'sha256': hashlib.sha256(body.encode()).hexdigest(),
                'redirects': [{'from': http, 'to': own, 'httpStatus': 301}] if uri == http else []}}
        def proof(uri, kind, text, **extra):
            meta = queue['items'][uri]['fetch']
            return {'requestedUrl': uri, 'sourceUrl': meta['finalUrl'], 'observedAt': meta['observedAt'],
                'bodySha256': meta['sha256'], 'method': 'reviewed_own_lab_research_description' if text == mission else 'reviewed_named_resource',
                'evidenceType': kind, 'evidence': text, **extra}
        raw = make_lab('Lab Web Site', own, 'Interdisciplinary', queue['items'][own]['fetch'], 'Lab Web Site')
        raw['professorIds'] = []
        queue['labCandidates'][own] = {'record': copy.deepcopy(raw)}
        card = next(n for n in every_node(DOM(html[directory]).main()) if n.tag == 'div' and n.text().startswith('Jane Example '))
        proofs = [proof(own, 'document_title', 'Example – Jane Example research'),
            proof(own, 'document_link', 'Example -> '+own, linkText='Example', linkUrl=own),
            proof(own, 'main_text_quote', mission), proof(team, 'document_title', 'Our Team – Example'),
            proof(team, 'main_text_quote', role), proof(team, 'main_text_quote', group),
            proof(directory, 'document_title', 'Core Faculty'), proof(directory, 'main_text_quote', card.text()),
            proof(directory, 'named_link', 'Lab Web Site -> '+http, linkText='Lab Web Site', linkUrl=http),
            proof(http, 'redirect_chain', redirect_text(queue['items'][http]['fetch']['redirects']), redirects=queue['items'][http]['fetch']['redirects'])]
        keys = ['ownTitleEvidence','ownBrandEvidence','ownMissionEvidence','ownTeamTitleEvidence',
            'ownTeamRoleEvidence','ownGroupContextEvidence','directoryTitleEvidence','campusCardEvidence',
            'campusLinkEvidence','transportEvidence']
        row = dict(zip(keys, proofs))
        row.update(kind=KIND, labId=raw['id'], labWebsiteUrl=own, originalRequestedUri=own,
            originalSourceRecord=copy.deepcopy(raw), originalSourceRecordSha256=record_sha256(raw),
            teamSourceUrl=team, directorySourceUrl=directory, directoryNameAsPublished='Core Faculty',
            listedNameAsPublished='Jane Example', projectDirectorNameAsPublished='JANE M EXAMPLE',
            projectDirectorRoleAsPublished='ASSISTANT RESEARCH SCIENTIST Institute, UCSD',
            campusCardSelectorAttributes={'class':'card'}, literalCampusHref='http://example.ucsd.edu',
            evidence=proofs, reason='A resource listing establishes a connection, not ownership or a PI appointment.')
        decision = {'action':'accept', 'stableLabId':raw['id'], 'name':'Example', 'recordSubtype':'research_group',
            'institution':'Unknown', 'identityEvidence':proofs[:2], 'description':mission, 'descriptionEvidence':[proofs[2]],
            'institutionUnresolvedReason':'No group ownership statement.', 'departmentUnresolvedReason':'The listed person is not the group department.',
            'campusResearchResourceReview':row, 'reason':row['reason']}
        proposal = {'urlKey':own, 'status':'unresolved', 'record':raw, 'destinationCheck':queue['items'][own]['fetch']}
        labs, *_ = reviewed_lab_records({'labs':[]}, [proposal], {'labs':{own:decision}})
        return labs, queue

    def test_acceptance_and_repeat_preserve_unknown_ownership_without_people_or_keywords(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); labs,q=self.fixture(root); before=copy.deepcopy((labs,q))
            verified=verified_new_lab_scopes(labs,q,root); lab=verified[0]
            self.assertEqual((labs,q),before)
            self.assertEqual(lab['institution'],'Unknown'); self.assertEqual(lab['department'],'Unknown')
            self.assertEqual(lab['principalInvestigator'],'Not found'); self.assertEqual(lab['contactEmail'],'Not found')
            self.assertEqual(lab['professorIds'],[]); self.assertEqual(lab['researchAreas'],[])
            self.assertEqual(lab['campusResearchRelationships'][0]['listedNameAsPublished'],'Jane Example')
            self.assertEqual(lab['alternateWebsiteUrls'],['http://example.ucsd.edu/'])
            self.assertEqual(verified_new_lab_scopes(verified,q,root),verified)

    def test_directory_and_project_director_cannot_be_promoted_to_ownership_pi_or_professor(self):
        for field,value in [('institution','University of California San Diego'),('department','Institute'),
                ('principalInvestigator','Jane M Example'),('contactEmail','jane@ucsd.edu'),
                ('professorIds',['invented-person']),('recordSubtype','lab'),('researchAreas',['Cognition']),
                ('alternateWebsiteUrls',['https://other.ucsd.edu/']),
                ('campusResearchResourceReview',None),('programAffiliationReview',{'kind':'other'})]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); labs,q=self.fixture(root); labs[0][field]=value
                with self.assertRaises(ValueError): verified_new_lab_scopes(labs,q,root)

    def test_an_unscoped_card_link_elsewhere_on_page_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); labs,q=self.fixture(root); row=labs[0]['campusResearchResourceReview']
            # Both links are real on the same captured page; only one belongs to Jane's card.
            link=row['campusLinkEvidence']; link['linkUrl']='http://other.ucsd.edu/'
            link['evidence']='Lab Web Site -> '+link['linkUrl']
            with self.assertRaisesRegex(ValueError,'one unique campus card'):
                verified_new_lab_scopes(labs,q,root)

    def test_frozen_source_identity_date_bytes_and_observed_transport_cannot_be_substituted(self):
        for change in ['id','source','date','body','redirect','literal']:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); labs,q=self.fixture(root); row=labs[0]['campusResearchResourceReview']
                if change=='id': labs[0]['id']='new-id'
                elif change=='source': row['originalSourceRecord']['department']='Different'
                elif change=='date': row['ownMissionEvidence']['observedAt']='2026-10-17T01:00:00+00:00'
                elif change=='body': next((root/'responses').glob('*.html')).write_text('Changed')
                elif change=='redirect': q['items']['http://example.ucsd.edu/']['fetch']['redirects'][0]['from']='http://other.ucsd.edu/'
                else: row['literalCampusHref']='https://example.ucsd.edu/'
                with self.assertRaises(ValueError): verified_new_lab_scopes(labs,q,root)

    def test_individual_description_and_incompatible_subject_do_not_establish_this_group(self):
        for change in ['mission','subject','team','missing-proof','ownership-evidence']:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); labs,q=self.fixture(root); row=labs[0]['campusResearchResourceReview']
                if change=='mission': labs[0]['description']='I explore cognition.'
                elif change=='subject': row['projectDirectorNameAsPublished']='OTHER PERSON'
                elif change=='team': row['ownGroupContextEvidence']=row['ownTeamRoleEvidence']
                elif change=='missing-proof': row['evidence'].remove(row['ownMissionEvidence'])
                else: labs[0]['fieldEvidence']['institution']=[row['campusCardEvidence']]
                with self.assertRaises(ValueError): verified_new_lab_scopes(labs,q,root)

    def test_unknown_or_foreign_groups_without_a_review_still_fail_closed(self):
        for institution in ['Unknown','Partner Institute']:
            with self.subTest(institution=institution):
                with self.assertRaises(ValueError):
                    verified_new_lab_scopes([{'id':'unreviewed','institution':institution}], {'items':{}}, Path('/tmp'))


if __name__=='__main__': unittest.main()
