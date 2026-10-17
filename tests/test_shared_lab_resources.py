import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from shared_lab_resources import verified_shared_resources, apply_shared_resources
from lab_resource_reviews import record_sha256
from lab_entities import LabIndex
from rebuild_verified_atlas import build
from audit_ucsd_preservation import audit
from validate_data import validate_references
from test_atlas_quality import atlas
import test_shared_lab_entities as fixtures


class SharedResourceTests(unittest.TestCase):
    def fixture(self, cache):
        resource = 'http://landing.ucsd.edu/'; items = {}
        def capture(uri, raw):
            (cache / 'responses').mkdir(exist_ok=True)
            path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html'); path.write_text(raw)
            meta = {'sourceUrl':uri,'finalUrl':uri,'observedAt':'2026-01-01','status':'ok','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            items[uri] = {'url':uri,'fetch':meta}
            return {'requestedUrl':uri,'sourceUrl':uri,'observedAt':meta['observedAt'],'bodySha256':meta['sha256']}
        primary = capture(fixtures.URL,'<main>'+fixtures.TEXT+'</main>')
        collective = 'Example A & Example B Labs'
        landing_text = 'Shared landing page for '+collective+'.'
        landing = capture(resource,'<main>'+landing_text+' <a href="'+fixtures.URL+'">Current webpage</a></main>')
        group = {**landing,'evidenceType':'main_text_quote','evidence':landing_text}
        link = {**landing,'evidenceType':'named_link','evidence':'Current webpage -> '+fixtures.URL,'linkText':'Current webpage','linkUrl':fixtures.URL}
        identity = {**primary,'evidenceType':'main_text_quote','evidence':fixtures.TEXT}
        labs = fixtures.labs()
        row = {'action':'register_shared_lab_resource','resourceKind':'shared_landing_page','groupId':'example-labs',
               'memberLabIds':['lab-a','lab-b'],'primaryUri':fixtures.URL,'resourceUri':resource,
               'originalLabRecords':copy.deepcopy(labs),'originalLabRecordSha256':{lab['id']:record_sha256(lab) for lab in labs},
               'collectiveName':collective,'collectiveNameEvidence':group,'primaryLinkEvidence':link,
               'memberIdentityEvidence':{lab['id']:[identity] for lab in labs},'evidence':[group,link,identity],
               'reason':'The captured landing page names the complete group and links its individually named primary page.'}
        data = atlas();data.update(qualityMigrationVersion=1,labs=labs)
        return data,{'items':items},row

    def test_two_labs_keep_their_ids_and_generic_resource_links_remain_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,queue,row=self.fixture(cache);before=copy.deepcopy(data)
            reviews=verified_shared_resources({'entries':[row]},queue,cache,data['labs'])
            first,_,_,archives=build(copy.deepcopy(data),{},{},{},{},coverage_evidence={'sharedLabResourceReviews':reviews})
            index=LabIndex(first['labs']);index.validate_sharing();validate_references(first)
            self.assertEqual(len(first['labs']),2)
            self.assertIsNone(index.resolve(row['resourceUri']))
            self.assertIsNone(index.resolve(row['resourceUri'],name='Lab Website'))
            self.assertEqual(index.resolve(row['resourceUri'],lab_id='lab-a')['id'],'lab-a')
            self.assertEqual(index.resolve(row['resourceUri'],name='Example Lab B')['id'],'lab-b')
            self.assertFalse(index.url_groups()[1]);self.assertEqual(len(index.url_groups()[0]),2)
            self.assertEqual(first['dataQuality']['coverage']['reviewedSharedLabWebsiteGroups'],1)
            self.assertTrue(all(lab['labWebsiteUrl']==fixtures.URL and not lab.get('aliasIds') for lab in first['labs']))
            self.assertEqual(audit(before,first,[archives])['status'],'passed')
            second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence={'sharedLabResourceReviews':reviews})
            self.assertEqual(first,second)

    def test_shared_primary_site_does_not_automatically_exempt_alternative_uri_collisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            data,_,row=self.fixture(Path(tmp))
            for lab in data['labs']:lab['alternateWebsiteUrls']=[row['resourceUri']]
            self.assertEqual(len(LabIndex(data['labs']).url_groups()[1]),1)

    def test_incomplete_group_or_unobserved_variant_cannot_register_a_resource(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,queue,row=self.fixture(cache)
            for change in ['member','group','uri','snapshot','date','hash','link','identity']:
                bad=copy.deepcopy(row)
                if change=='member':bad['memberLabIds']=['lab-a']
                if change=='group':bad['groupId']='unrelated'
                if change=='uri':bad['resourceUri']='https://landing.ucsd.edu/'
                if change=='snapshot':bad['originalLabRecords'][0]['labName']='Changed'
                if change=='date':bad['collectiveNameEvidence']['observedAt']='2020-01-01'
                if change=='hash':bad['collectiveNameEvidence']['bodySha256']='changed'
                if change=='link':bad['primaryLinkEvidence']['linkUrl']='https://unvisited.ucsd.edu/'
                if change=='identity':bad['memberIdentityEvidence'].pop('lab-b')
                with self.subTest(change=change),self.assertRaises(ValueError):
                    verified_shared_resources({'entries':[bad]},queue,cache,data['labs'])

    def test_generic_unrelated_collective_name_does_not_identify_the_complete_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,queue,row=self.fixture(cache)
            row['collectiveName']='Shared landing page'
            with self.assertRaisesRegex(ValueError,'actually name the group'):
                verified_shared_resources({'entries':[row]},queue,cache,data['labs'])

    def test_failed_batch_is_atomic_and_one_member_cannot_register_a_group_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,queue,row=self.fixture(cache)
            reviews=verified_shared_resources({'entries':[row]},queue,cache,data['labs']);before=copy.deepcopy(data)
            with self.assertRaises(ValueError):apply_shared_resources(data,reviews+[{**reviews[0],'memberLabIds':['lab-a']}])
            self.assertEqual(data,before)
            apply_shared_resources(data,reviews)
            data['labs'][1].pop('sharedResourceReviews')
            self.assertEqual(len(LabIndex(data['labs']).url_groups()[1]),1)
            with self.assertRaisesRegex(ValueError,'shared resource'):LabIndex(data['labs']).validate_sharing()

    def test_a_resource_owned_by_another_lab_cannot_be_added_to_the_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);data,queue,row=self.fixture(cache)
            other=copy.deepcopy(data['labs'][0]);other.update(id='other',labName='Unrelated Lab',labWebsiteUrl=row['resourceUri']);other.pop('websiteSharing');data['labs'].append(other)
            with self.assertRaises(ValueError):verified_shared_resources({'entries':[row]},queue,cache,data['labs'])
