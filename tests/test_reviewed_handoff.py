import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import apply_ucsd_coverage as apply
from refresh_labs import make_lab


class ReviewedHandoffTests(unittest.TestCase):
    def test_reciprocal_reviewed_lab_links_keep_source_scope_and_existing_fields(self):
        proof = [{'sourceUrl': 'https://department.ucsd.edu/faculty', 'observedAt': '2026-10-16', 'evidence': 'Named Professor Example Lab'}]
        lab = {'id': 'lab', 'labName': 'Example Lab', 'labWebsiteUrl': 'https://lab.ucsd.edu/',
               'professorIds': ['person'], 'fieldEvidence': {'labWebsiteUrl': proof}}
        patches = {'person': {'email': 'existing@ucsd.edu', 'labAffiliations': [{'labId': 'previous'}]}}
        apply.attach_reviewed_lab_associations(patches, [lab], {'person': {}})
        self.assertEqual(patches['person']['email'], 'existing@ucsd.edu')
        self.assertEqual(patches['person']['labAffiliations'][0], {'labId': 'previous'})
        link = patches['person']['labAffiliations'][1]
        self.assertEqual(link['relationship'], 'official_directory_same_record')
        self.assertEqual(link['fieldEvidence'], proof)
        self.assertNotIn('principalInvestigator', patches['person'])
        first = copy.deepcopy(patches)
        apply.attach_reviewed_lab_associations(patches, [lab], {'person': {}})
        self.assertEqual(patches, first)

    def test_reciprocal_links_validate_all_people_before_mutating_patches(self):
        lab = {'id': 'lab', 'labName': 'Example Lab', 'labWebsiteUrl': 'https://lab.ucsd.edu/',
               'professorIds': ['person', 'unknown'], 'fieldEvidence': {'labWebsiteUrl': [{'sourceUrl': 'https://ucsd.edu/'}]}}
        patches = {}
        with self.assertRaisesRegex(ValueError, 'Unknown linked professor'):
            apply.attach_reviewed_lab_associations(patches, [lab], {'person': {}})
        self.assertEqual(patches, {})

    def test_reciprocal_links_reject_associations_without_directory_evidence(self):
        lab = {'id': 'lab', 'professorIds': ['person'], 'fieldEvidence': {}}
        with self.assertRaisesRegex(ValueError, 'source evidence'):
            apply.attach_reviewed_lab_associations({}, [lab], {'person': {}})

    def fixture(self, tmp):
        root = Path(tmp)
        (root / 'data').mkdir()
        atlas = root / 'data/research-atlas.json'
        atlas.write_text(json.dumps({'professors': [], 'labs': []}))
        cache = root / 'cache'
        (cache / 'responses').mkdir(parents=True)
        url = 'https://example-lab.ucsd.edu/'
        body = '<h1>Example Lab</h1>\r\n<p>UC San Diego</p>'
        meta = {'sourceUrl': url, 'finalUrl': url, 'observedAt': '2026-10-01T00:00:00+00:00', 'status': 'ok', 'sha256': hashlib.sha256(body.encode()).hexdigest()}
        (cache / 'responses' / (hashlib.sha256(url.encode()).hexdigest() + '.html')).write_text(body)
        queue = {'updatedAt': '2026-10-02', 'counts': {'done': 1, 'pending': 1}, 'items': {url: {'url': url, 'state': 'done', 'fetch': meta}, 'pending': {'url': 'https://other.ucsd.edu/', 'state': 'pending'}}}
        (cache / 'queue.json').write_text(json.dumps(queue))
        record = make_lab('Example Lab', url, 'Inferred department', meta, 'Example Lab')
        proposal = {'urlKey': url, 'status': 'reviewable_identity_match', 'record': record, 'destinationCheck': meta}
        decisions = root / 'decisions.json'
        decisions.write_text(json.dumps({'labs': {url: {'action': 'accept', 'stableLabId': record['id'], 'reason': 'Reviewed fixture', 'departmentUnresolvedReason': 'No academic department stated on this homepage'}}}))
        return root, cache, decisions, proposal

    def test_incremental_handoff_keeps_pending_queue_atlas_and_source_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, cache, decisions, proposal = self.fixture(tmp)
            old_atlas = (root / 'data/research-atlas.json').read_bytes()
            old_queue = (cache / 'queue.json').read_bytes()
            output = root / 'handoff.json'
            with patch.object(apply, 'ROOT', root), patch.object(apply, 'prepare', return_value=[proposal]):
                apply.export_reviewed_lab_handoff(cache, decisions, output)
            result = json.loads(output.read_text())
            self.assertEqual(result['collectionState'], 'reviewed_incremental')
            self.assertFalse(result['isFinalExport'])
            self.assertEqual(result['labs'][0]['department'], 'Unknown')
            self.assertNotIn('department', result['labs'][0]['fieldEvidence'])
            self.assertEqual(result['sourceManifest'][0]['observedAt'], '2026-10-01T00:00:00+00:00')
            self.assertEqual((root / 'data/research-atlas.json').read_bytes(), old_atlas)
            self.assertEqual((cache / 'queue.json').read_bytes(), old_queue)

    def test_published_lab_alias_name_survives_handoff_with_its_exact_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,cache,path,proposal=self.fixture(tmp);uri=proposal['urlKey']+'aliases';name='Example Research Group'
            raw='<main><h1>'+name+'</h1><p>Also known as Example Lab.</p></main>'
            body=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');body.write_text(raw)
            meta={**proposal['destinationCheck'],'sourceUrl':uri,'finalUrl':uri,'sha256':hashlib.sha256(body.read_bytes()).hexdigest()}
            q=json.loads((cache/'queue.json').read_text());q['items'][uri]={'url':uri,'state':'done','fetch':meta};(cache/'queue.json').write_text(json.dumps(q))
            proof={'requestedUrl':uri,'sourceUrl':uri,'observedAt':meta['observedAt'],'bodySha256':meta['sha256'],'method':'reviewed_explicit_group_alias_name','aliasName':name,'evidenceType':'main_text_quote','evidence':name}
            d=json.loads(path.read_text());d['labs'][proposal['urlKey']].update(aliasNames=[name],aliasNameEvidence=[proof]);path.write_text(json.dumps(d))
            with patch.object(apply,'ROOT',root),patch.object(apply,'prepare',return_value=[proposal]):apply.export_reviewed_lab_handoff(cache,path,root/'handoff.json')
            lab=json.loads((root/'handoff.json').read_text())['labs'][0]
            self.assertEqual(lab['aliasNames'],[name]);self.assertEqual(lab['fieldEvidence']['aliasNames'],[proof])

    def test_alias_name_cannot_be_invented_or_taken_from_an_unrelated_own_resource(self):
        for mode in ['invented','other_lab','date','hash']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                _,cache,_,proposal=self.fixture(tmp);uri='https://other-lab.ucsd.edu/' if mode=='other_lab' else proposal['urlKey'];meta=proposal['destinationCheck']
                raw='<main>Example Research Group at UC San Diego</main>';p=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');p.write_text(raw)
                q={'items':{uri:{'url':uri,'fetch':{**meta,'sourceUrl':uri,'finalUrl':uri,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}}}}
                proof={'requestedUrl':uri,'sourceUrl':uri,'observedAt':meta['observedAt'],'bodySha256':hashlib.sha256(p.read_bytes()).hexdigest(),'method':'reviewed_explicit_group_alias_name','aliasName':'Example Research Group','evidenceType':'main_text_quote','evidence':'Invented Group' if mode=='invented' else 'Example Research Group'}
                if mode=='date':proof['observedAt']='2020-01-01'
                if mode=='hash':proof['bodySha256']='0'*64
                lab={'id':'example','labWebsiteUrl':proposal['urlKey'],'aliasNames':['Example Research Group'],'fieldEvidence':{'aliasNames':[proof]}}
                with self.assertRaises(ValueError):apply.validate_reviewed_alias_names([lab],q,cache)

    def test_reviewed_alias_can_target_a_later_accepted_identity_in_the_same_cohort(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, path, proposal = self.fixture(tmp)
            decisions = json.loads(path.read_text())
            alias_uri = 'https://example-lab.ucsd.edu/home'
            alias = copy.deepcopy(proposal)
            alias.update(urlKey=alias_uri, destinationCheck={**proposal['destinationCheck'], 'finalUrl': alias_uri})
            decisions['labs'][alias_uri] = {'action': 'alias', 'labId': proposal['record']['id'],
                'reason': 'Actual named own-home link and dated positive captures reviewed',
                'aliasEvidence': [{'sourceUrl': alias_uri, 'observedAt': '2026-10-01', 'evidence': 'Example Lab'}]}
            labs, aliases, _, _, _ = apply.reviewed_lab_records({'labs': []}, [alias, proposal], decisions)
            self.assertEqual(len(labs), 1)
            self.assertEqual(aliases[0]['labId'], labs[0]['id'])
            self.assertEqual(aliases[0]['url'], alias_uri)

    def test_an_alias_does_not_create_an_unaccepted_target_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, path, proposal = self.fixture(tmp)
            decisions = json.loads(path.read_text())
            decisions['labs'][proposal['urlKey']] = {'action': 'alias', 'labId': proposal['record']['id'],
                'reason': 'An alias cannot approve its own missing identity', 'aliasEvidence': [{'evidence': 'Example Lab'}]}
            with self.assertRaisesRegex(ValueError, 'known lab ID'):
                apply.reviewed_lab_records({'labs': []}, [proposal], decisions)

    def test_reviewed_contact_must_exist_in_actual_own_lab_capture(self):
        for value in ['lab@ucsd.edu', 'invented@ucsd.edu']:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmp:
                root, cache, decisions, proposal = self.fixture(tmp)
                url = proposal['urlKey']
                path = cache / 'responses' / (hashlib.sha256(url.encode()).hexdigest() + '.html')
                path.write_bytes(path.read_bytes() + b'<p>Contact email: lab@ucsd.edu</p>')
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                proposal['destinationCheck']['sha256'] = digest
                queue = json.loads((cache / 'queue.json').read_text())
                queue['items'][url]['fetch']['sha256'] = digest
                (cache / 'queue.json').write_text(json.dumps(queue))
                data = json.loads(decisions.read_text())
                data['labs'][url].update(contactEmail=value, contactEvidence=[{'sourceUrl': url, 'observedAt': proposal['destinationCheck']['observedAt'], 'evidence': 'Contact email: ' + value}])
                decisions.write_text(json.dumps(data))
                with patch.object(apply, 'ROOT', root), patch.object(apply, 'prepare', return_value=[proposal]):
                    if value == 'lab@ucsd.edu':
                        apply.export_reviewed_lab_handoff(cache, decisions, root / 'handoff.json')
                        result = json.loads((root / 'handoff.json').read_text())
                        self.assertEqual(result['labs'][0]['contactEmail'], value)
                        self.assertEqual(result['sourceManifest'][0]['bodySha256'], digest)
                    else:
                        with self.assertRaisesRegex(ValueError, 'absent from an own-lab'):
                            apply.export_reviewed_lab_handoff(cache, decisions, root / 'handoff.json')
                        self.assertFalse((root / 'handoff.json').exists())

    def test_another_lab_on_a_shared_host_cannot_supply_contact(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / 'responses').mkdir()
            source = 'https://sites.ucsd.edu/another-lab/contact/'
            body = '<p>Contact: someone@ucsd.edu</p>'
            (cache / 'responses' / (hashlib.sha256(source.encode()).hexdigest() + '.html')).write_text(body)
            meta = {'status': 'ok', 'finalUrl': source, 'observedAt': '2026-01-01', 'sha256': hashlib.sha256(body.encode()).hexdigest()}
            lab = {'id': 'own-lab', 'labWebsiteUrl': 'https://sites.ucsd.edu/own-lab/', 'contactEmail': 'someone@ucsd.edu',
                   'fieldEvidence': {'contactEmail': [{'sourceUrl': source, 'observedAt': meta['observedAt'], 'evidence': body}]}}
            with self.assertRaisesRegex(ValueError, 'absent from an own-lab'):
                apply.validate_reviewed_contacts([lab], {'items': {source: {'url': source, 'fetch': meta}}}, cache)

    def test_handoff_cannot_overwrite_served_or_final_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, cache, decisions, _ = self.fixture(tmp)
            with patch.object(apply, 'ROOT', root):
                for output in [root / 'data/research-atlas.json', root / 'data/ucsd/coverage-expansion-evidence.json', decisions]:
                    with self.assertRaisesRegex(ValueError, 'must not overwrite'):
                        apply.export_reviewed_lab_handoff(cache, decisions, output)

    def test_uncaptured_field_date_cannot_be_handed_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, cache, decisions, proposal = self.fixture(tmp)
            proposal['record']['fieldEvidence']['labName']['observedAt'] = '2020-01-01T00:00:00+00:00'
            with patch.object(apply, 'ROOT', root), patch.object(apply, 'prepare', return_value=[proposal]):
                with self.assertRaisesRegex(ValueError, 'no matching observed capture'):
                    apply.export_reviewed_lab_handoff(cache, decisions, root / 'handoff.json')
            self.assertFalse((root / 'handoff.json').exists())

    def test_exposed_stable_id_cannot_change_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, decisions, proposal = self.fixture(tmp)
            data = json.loads(decisions.read_text())
            data['labs'][proposal['urlKey']]['stableLabId'] = 'different-id'
            with self.assertRaisesRegex(ValueError, 'stable lab ID changed'):
                apply.reviewed_lab_records({'labs': []}, [proposal], data)

    def test_reviewed_alias_still_resolves_after_its_target_id_is_consolidated(self):
        proof = {'sourceUrl': 'https://lab.ucsd.edu/', 'observedAt': '2026-01-01', 'evidence': 'Example Lab'}
        atlas = {'labs': [{'id': 'canonical', 'aliasIds': ['old-stable-id'], 'labWebsiteUrl': proof['sourceUrl']}]}
        url = 'https://lab.ucsd.edu/home'
        proposal = {'urlKey': url, 'status': 'reviewable_identity_match', 'destinationCheck': {'status': 'ok', 'finalUrl': url}}
        decisions = {'labs': {url: {'action': 'alias', 'labId': 'old-stable-id', 'aliasEvidence': [proof], 'reason': 'Reviewed same lab home page'}}}
        _, aliases, _, _, _ = apply.reviewed_lab_records(atlas, [proposal], decisions)
        self.assertEqual(aliases[0]['labId'], 'canonical')

    def test_reviewed_description_keeps_exact_own_research_quote_and_immutable_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,cache,decisions,proposal=self.fixture(tmp);url=proposal['urlKey']
            description='We study neural circuits using quantitative imaging.'
            path=cache/'responses'/(hashlib.sha256(url.encode()).hexdigest()+'.html')
            path.write_bytes(path.read_bytes()+('<p>'+description+'</p>').encode());meta=proposal['destinationCheck'];meta['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            queue=json.loads((cache/'queue.json').read_text());queue['items'][url]['fetch']=dict(meta);(cache/'queue.json').write_text(json.dumps(queue))
            proof={'requestedUrl':url,'sourceUrl':url,'observedAt':meta['observedAt'],'bodySha256':meta['sha256'],
                   'method':'reviewed_own_lab_research_description','evidenceType':'main_text_quote','evidence':description}
            data=json.loads(decisions.read_text());data['labs'][url].update(description=description,descriptionEvidence=[proof]);decisions.write_text(json.dumps(data))
            old_queue=(cache/'queue.json').read_bytes();old_atlas=(root/'data/research-atlas.json').read_bytes()
            with patch.object(apply,'ROOT',root),patch.object(apply,'prepare',return_value=[proposal]):apply.export_reviewed_lab_handoff(cache,decisions,root/'handoff.json')
            record=json.loads((root/'handoff.json').read_text())['labs'][0]
            self.assertEqual(record['description'],description);self.assertEqual(record['fieldEvidence']['description'],[proof])
            self.assertEqual((cache/'queue.json').read_bytes(),old_queue);self.assertEqual((root/'data/research-atlas.json').read_bytes(),old_atlas)

    def test_description_requires_exact_actual_bytes_date_and_own_resource(self):
        for mode in ['invented_quote','changed_date','changed_hash','other_lab']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root,cache,decisions,proposal=self.fixture(tmp);url=proposal['urlKey'];meta=proposal['destinationCheck']
                proof={'requestedUrl':url,'sourceUrl':url,'observedAt':meta['observedAt'],'bodySha256':meta['sha256'],
                       'method':'reviewed_own_lab_research_description','evidenceType':'main_text_quote','evidence':'Example Lab UC San Diego'}
                lab={'id':'example','labWebsiteUrl':url,'description':proof['evidence'],'fieldEvidence':{'description':[proof]}}
                queue=json.loads((cache/'queue.json').read_text())
                if mode=='invented_quote':lab['description']=proof['evidence']='Invented research claim'
                if mode=='changed_date':proof['observedAt']='2020-01-01'
                if mode=='changed_hash':proof['bodySha256']='0'*64
                if mode=='other_lab':lab['labWebsiteUrl']='https://another-lab.ucsd.edu/'
                with self.assertRaises(ValueError):apply.validate_reviewed_descriptions([lab],queue,cache)

    def test_descriptions_on_another_shared_host_entity_are_not_own_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);(cache/'responses').mkdir();items={};description='We study neural circuits.'
            for uri,body in [('https://sites.ucsd.edu/own-lab/','<h1>Own Lab</h1>'),('https://sites.ucsd.edu/other-lab/','<p>'+description+'</p>')]:
                path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.write_text(body);meta={'sourceUrl':uri,'finalUrl':uri,'status':'ok','observedAt':'2026-10-16','sha256':hashlib.sha256(path.read_bytes()).hexdigest()};items[uri]={'url':uri,'fetch':meta}
            uri='https://sites.ucsd.edu/other-lab/';meta=items[uri]['fetch'];proof={'requestedUrl':uri,'sourceUrl':uri,'observedAt':meta['observedAt'],'bodySha256':meta['sha256'],'method':'reviewed_own_lab_research_description','evidence':description}
            lab={'id':'own','labWebsiteUrl':'https://sites.ucsd.edu/own-lab/','description':description,'fieldEvidence':{'description':[proof]}}
            with self.assertRaisesRegex(ValueError,'own resource'):apply.validate_reviewed_descriptions([lab],{'items':items},cache)

    def test_description_cannot_bypass_capture_validation_with_a_different_method(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,_,decisions,proposal=self.fixture(tmp);data=json.loads(decisions.read_text());data['labs'][proposal['urlKey']].update(description='Claim',descriptionEvidence=[{'method':'unverified','evidence':'Claim'}])
            with self.assertRaisesRegex(ValueError,'complete exact source quote'):apply.reviewed_lab_records({'labs':[]},[proposal],data)
