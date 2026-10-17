"""Offline admission of an individually reviewed historical official source."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import local_lab_summaries as ledger
import local_lab_summary_gaps as gaps


def proof_hash(proof):
    return hashlib.sha256(json.dumps(proof,ensure_ascii=False,sort_keys=True,
        separators=(',',':')).encode('utf-8')).hexdigest()


class ReviewedOfficialSourceGapTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=gaps.OUT);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.out=self.root/'data/local-lab-summaries';self.cache=self.root/'collector'
        (self.out/'records').mkdir(parents=True);(self.out/'packets').mkdir();self.cache.mkdir()
        self.url='https://astro.ucsd.edu/research/labs/index.html'
        self.proof={'sourceUrl':self.url,'observedAt':'2026-10-07T22:55:23+00:00',
            'evidence':'历史实验室名称及指向主页的链接。','method':'manual_review_official_page_names_lab',
            'status':'verified','extraOriginalField':{'scope':'historical_reference_only'}}
        self.lab={'id':'one','labName':'Space Weather Laboratory','labWebsiteUrl':'https://forecast.ucsd.edu/',
            'fieldEvidence':{'labName':[self.proof],'labWebsiteUrl':[copy.deepcopy(self.proof)]}}
        self.baseline={'labs':[self.lab]};self.baseline_file=self.root/'data/research-atlas.json'
        self.baseline_file.parent.mkdir(parents=True,exist_ok=True)
        self.baseline_file.write_text(json.dumps(self.baseline,ensure_ascii=False))
        self.baseline_hash=hashlib.sha256(self.baseline_file.read_bytes()).hexdigest()
        self.entry={'labId':'one','url':self.url,'baselineSha256':self.baseline_hash,'field':'labName',
            'fieldObservedAt':self.proof['observedAt'],'fieldProofSha256':proof_hash(self.proof),
            'reviewedAt':'2026-10-16T05:45:00+00:00','purpose':'verify_historical_lab_identity',
            'reason':'Explicitly reviewed finite identity-source gap.'}
        self.entries=[self.entry];self.captures={}
        self.raw={'labId':'one','status':'partial','summaryZh':None,'researchQuestions':[],
            'topics':[],'methods':[],'evidence':[],
            'identity':{'status':'uncertain','entityType':'unconfirmed','reason':'Needs current identity source.'},
            'affiliation':{'status':'uncertain','reason':'Unknown.'},'uncertainty':['Current mapping unknown.'],
            'blockers':['Historical lab-source URI not captured.'],'reviewedAt':'2026-10-16T05:44:00+00:00'}
        self.packet={'labId':'one','labName':self.lab['labName'],'listedWebsite':self.lab['labWebsiteUrl'],
            'preparedAt':'2026-10-16T05:44:00+00:00','destinationQueueStates':['done'],
            'latestDestinationFetch':{'sourceUrl':self.lab['labWebsiteUrl'],'status':'ok','httpStatus':200,
                'finalUrl':self.lab['labWebsiteUrl'],'observedAt':'2026-10-16T05:42:55+00:00','redirects':[]},'sources':[]}
        for obj,name,value in [(gaps,'ROOT',self.root),(gaps,'BASELINE_HASH',self.baseline_hash),
                (gaps,'OUT',self.out),(gaps,'CACHE',self.cache),(ledger,'ROOT',self.root),(ledger,'OUT',self.out)]:
            p=patch.object(obj,name,value);p.start();self.addCleanup(p.stop)
        p=patch.object(gaps,'coordination_ready',return_value=False);p.start();self.addCleanup(p.stop)

    def put(self,name,value,base=None):
        path=(base or self.out)/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value,ensure_ascii=False))

    def write(self):
        for name,value in [('manifest.json',{'items':[]}),('records/one.json',self.raw),
                ('packets/one.json',self.packet),('reviewed-official-source-gaps.json',{'items':self.entries})]:self.put(name,value)
        self.put('queue.json',{'items':self.captures},self.cache)

    def plan(self):
        self.write();return gaps.plan()

    def rebind_baseline(self):
        self.baseline_file.write_text(json.dumps(self.baseline,ensure_ascii=False))
        digest=hashlib.sha256(self.baseline_file.read_bytes()).hexdigest()
        gaps.BASELINE_HASH=digest;self.entry['baselineSha256']=digest

    def test_exact_reviewed_baseline_field_reference_admits_only_historical_gap(self):
        result=self.plan();self.assertEqual(result['liveCandidateCount'],1)
        item=result['items'][0]
        self.assertEqual(item['url'],self.url);self.assertEqual(item['labIds'],['one'])
        self.assertEqual(item['kind'],'reviewed_official_identity_source_gap')
        self.assertTrue(item['historicalReferenceOnly']);self.assertTrue(item['notAnAcceptedCanonicalLabUrl'])
        self.assertEqual(item['historicalFieldReference']['observedAt'],self.proof['observedAt'])
        self.assertNotIn('sourceObservedAt',item);self.assertNotIn('sourceId',item)
        self.assertNotIn('actualPageRequestMade',item)

    def test_exact_lab_website_field_is_also_allowed_and_canonical_json_order_independent(self):
        self.entry['field']='labWebsiteUrl'
        self.lab['fieldEvidence']['labWebsiteUrl'][0]=dict(reversed(list(self.proof.items())))
        self.rebind_baseline();self.assertEqual(self.plan()['liveCandidateCount'],1)

    def test_unreviewed_sources_are_not_automatically_queued(self):
        self.entries=[];self.assertEqual(self.plan()['items'],[])

    def test_missing_or_stale_review_baseline_id_purpose_and_proof_are_rejected(self):
        original=copy.deepcopy(self.entry)
        for field in ['labId','baselineSha256','field','fieldObservedAt','fieldProofSha256','reviewedAt','purpose']:
            with self.subTest(missing=field):
                self.entry.clear();self.entry.update(original);self.entry.pop(field)
                self.assertEqual(self.plan()['items'],[])
        for field,value in [('labId','other'),('labId',[]),('baselineSha256','0'*64),
                ('field',[]),('field','principalInvestigator'),
                ('fieldObservedAt','2026-10-07T22:55:24+00:00'),('fieldProofSha256','0'*64),
                ('fieldProofSha256',123),('reviewedAt','2026-10-16T05:45:00'),('purpose','crawl_all_sources')]:
            with self.subTest(field=field,value=value):
                self.entry.clear();self.entry.update(original);self.entry[field]=value
                self.assertEqual(self.plan()['items'],[])

    def test_actual_baseline_bytes_are_pinned_and_full_proof_fields_are_bound(self):
        self.baseline_file.write_text(self.baseline_file.read_text()+'\n')
        self.assertEqual(self.plan()['items'],[])
        self.proof['extraOriginalField']['scope']='different'
        self.rebind_baseline()  # Still needs a newly reviewed full proof hash.
        self.assertEqual(self.plan()['items'],[])

    def test_reference_url_must_equal_the_literal_proof_uri(self):
        for url in ['http://astro.ucsd.edu/research/labs/index.html',
                self.url+'?new=1',self.url+'/',self.url.replace('astro.','www.astro.')]:
            with self.subTest(url=url):
                self.entry['url']=url;self.assertEqual(self.plan()['items'],[])

    def test_official_https_host_and_auth_boundaries_apply_even_to_reviewed_proofs(self):
        for url in ['http://astro.ucsd.edu/research/labs/index.html','https://evilucsd.edu/labs',
                'https://astro.ucsd.edu.evil.test/labs','https://user:password@astro.ucsd.edu/labs',
                'https://astro.ucsd.edu:8080/labs','https://astro.ucsd.edu/login',
                'https://sso.ucsd.edu/labs','file:///tmp/labs','https://astro.ucsd.edu/labs#section']:
            with self.subTest(url=url):
                self.entry['url']=url;self.proof['sourceUrl']=url
                self.lab['fieldEvidence']['labWebsiteUrl']=[copy.deepcopy(self.proof)]
                self.entry['fieldProofSha256']=proof_hash(self.proof);self.rebind_baseline()
                self.assertEqual(self.plan()['items'],[])

    def test_current_raw_must_exist_and_be_partial_or_unresolved(self):
        for status in ['supported','awaiting_collection','unprocessed']:
            with self.subTest(status=status):
                self.raw['status']=status;self.assertEqual(self.plan()['items'],[])
        self.raw['status']='unresolved';self.assertEqual(self.plan()['liveCandidateCount'],1)
        self.write();(self.out/'records/one.json').unlink()
        self.assertEqual(gaps.plan()['items'],[])

    def test_exact_target_or_its_robots_explicit_refusal_is_not_bypassed(self):
        for meta in [{'sourceUrl':self.url,'status':'http_error','httpStatus':403},
                {'sourceUrl':self.url,'status':'authentication_required'},
                {'sourceUrl':self.url,'status':'access_challenge'},
                {'sourceUrl':'https://astro.ucsd.edu/robots.txt','status':'http_error','httpStatus':401},
                {'sourceUrl':self.url,'status':'robots_unavailable','robots':{'status':'unavailable','error':'access_challenge'}}]:
            with self.subTest(meta=meta):
                self.captures={'known':{'url':meta['sourceUrl'],'state':'unresolved','fetch':meta}}
                self.assertEqual(self.plan()['items'],[])
        self.captures={'known':{'url':self.url,'state':'done','fetch':{'sourceUrl':self.url,'status':'ok'},
            'attemptHistory':[{'sourceUrl':self.url,'status':'http_error','httpStatus':403}]}}
        self.assertEqual(self.plan()['items'],[])

    def test_cached_success_is_reuse_and_pending_capture_waits_without_duplicate_request(self):
        for state,status,expected in [('done','ok','captured_reuse_only'),('pending',None,'awaiting_collection')]:
            with self.subTest(state=state):
                self.captures={'existing':{'url':self.url,'state':state,'fetch':{'sourceUrl':self.url,'status':status}}}
                item=self.plan()['items'][0];self.assertFalse(item['requiresLiveFetch'])
                self.assertEqual(item['availability'],expected)
        self.captures={'historical':{'url':self.url,'state':'retained_prior_evidence'}}
        item=self.plan()['items'][0]
        self.assertEqual(item['availability'],'historical_evidence_only')
        self.assertTrue(item['requiresLiveFetch'])

    def test_unrelated_path_auth_refusal_does_not_invent_a_directory_refusal(self):
        self.captures={'other':{'url':'https://astro.ucsd.edu/private/login',
            'state':'unresolved','fetch':{'sourceUrl':'https://astro.ucsd.edu/private/login',
                'status':'authentication_required','httpStatus':403}}}
        self.assertEqual(self.plan()['liveCandidateCount'],1)

    def test_cached_origin_robots_rule_still_blocks_without_queue_mutation(self):
        robots='https://astro.ucsd.edu/robots.txt';stem='robots-'+hashlib.sha256(robots.encode()).hexdigest()
        self.put('responses/'+stem+'.json',{'status':'checked','sourceUrl':robots,'observedAt':self.proof['observedAt']},self.cache)
        (self.cache/'responses'/(stem+'.html')).write_text('User-agent: *\nDisallow: /research\n')
        item=self.plan()['items'][0]
        self.assertFalse(item['requiresLiveFetch']);self.assertEqual(item['availability'],'access_boundary_do_not_bypass')

    def test_no_science_entity_canonical_acceptance_or_old_observation_mutation(self):
        self.entry.update(maxPageBytes=8_000_000,observationOnly=True,sourceId='fake-current-source')
        self.write();before={name:(self.out/name).read_bytes() for name in ['records/one.json','packets/one.json']}
        queue_before=(self.cache/'queue.json').read_bytes();item=gaps.plan()['items'][0]
        self.assertEqual(item['maxPageBytes'],2_000_000);self.assertNotIn('observationOnly',item)
        self.assertNotIn('sourceId',item)
        self.assertEqual(before,{name:(self.out/name).read_bytes() for name in before})
        self.assertEqual(queue_before,(self.cache/'queue.json').read_bytes())
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(url['entityAcceptanceStatus'],'provisional_or_unresolved')
        self.assertFalse(url['canCountAsVerifiedLabGroupURL']);self.assertEqual(url['redirectChain'],[])


if __name__=='__main__':unittest.main()
