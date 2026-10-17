"""Offline reviewed document-preload discovery; no script execution or acceptance."""
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


class ReviewedDocumentPreloadTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=gaps.OUT);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.out=self.root/'data';self.cache=self.root/'collector'
        (self.out/'records').mkdir(parents=True);(self.out/'packets').mkdir();self.cache.mkdir()
        self.html=self.root/'root.html';self.url='http://example.ucsd.edu/'
        self.source={'sourceId':'reviewed-root','sourceUrl':self.url,
            'observedAt':'2026-10-16T04:57:07+00:00','cachePath':str(self.html),
            'title':'Intro Animation','text':'Named Research Group','role':'listed_lab_destination'}
        self.packet={'labId':'one','labName':'Named Research Group','listedWebsite':self.url,
            'preparedAt':'2026-10-16T05:00:00+00:00','destinationQueueStates':['done'],
            'latestDestinationFetch':{'sourceUrl':self.url,'finalUrl':self.url,'status':'ok',
                'observedAt':self.source['observedAt'],'httpStatus':200,'redirects':[]},
            'sources':[self.source]}
        self.raw={'labId':'one','status':'partial','summaryZh':None,'researchQuestions':[],
            'topics':[],'methods':[],'evidence':[],
            'identity':{'status':'uncertain','entityType':'unconfirmed','reason':'Target not reviewed.'},
            'affiliation':{'status':'uncertain','reason':'Unknown.'},'uncertainty':['Research unknown.'],
            'blockers':['No lab research body.'],'reviewedAt':'2026-10-16T05:00:00+00:00'}
        self.entry={'url':'http://example.ucsd.edu/home.html','labIds':['one'],
            'sourceId':self.source['sourceId'],'sourceObservedAt':self.source['observedAt'],
            'reviewedAt':'2026-10-16T05:05:00+00:00','discoveryMechanism':'html_document_preload',
            'originalHtmlAttribute':'home.html','kind':'reviewed_identity_research_gap',
            'reason':'Separately reviewed literal document preload; target entity unaccepted.'}
        self.entries=[self.entry];self.captures={}
        self.markup('<head><link rel="preload" href="home.html" as="document"></head>')
        for obj,name,value in [(gaps,'OUT',self.out),(gaps,'CACHE',self.cache),
                (ledger,'ROOT',self.root),(ledger,'OUT',self.out)]:
            p=patch.object(obj,name,value);p.start();self.addCleanup(p.stop)
        p=patch.object(gaps,'coordination_ready',return_value=False);p.start();self.addCleanup(p.stop)

    def put(self,name,value,base=None):
        path=(base or self.out)/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value))

    def markup(self,value):
        self.html.write_text(value);self.source['bodySha256']=hashlib.sha256(self.html.read_bytes()).hexdigest()
        self.entry['sourceBodySha256']=self.source['bodySha256']

    def write(self):
        for name,value in [('manifest.json',{'items':[]}),('records/one.json',self.raw),
                ('packets/one.json',self.packet),('reviewed-gap-additions.json',{'items':self.entries})]:self.put(name,value)
        self.put('queue.json',{'items':self.captures},self.cache)

    def plan(self):
        self.write();return gaps.plan()

    def test_reviewed_literal_link_document_preload_is_admitted_without_display_text(self):
        for rel in ['preload','prefetch preload','PRELOAD']:
            with self.subTest(rel=rel):
                self.markup(f'<link rel="{rel}" href="home.html" as="document">')
                result=self.plan();self.assertEqual(result['liveCandidateCount'],1)
                candidate=result['items'][0]
                self.assertEqual(candidate['discoveryMechanism'],'html_document_preload')
                self.assertEqual(candidate['url'],self.entry['url'])
                self.assertTrue(candidate['notAnAcceptedCanonicalLabUrl'])

    def test_script_comment_style_anchor_image_and_other_preloads_are_not_documents(self):
        for html in ['<script>window.location.href="home.html";</script>',
                '<script>var x=\'<link rel="preload" href="home.html" as="document">\';</script>',
                '<!-- <link rel="preload" href="home.html" as="document"> -->',
                '<style><link rel="preload" href="home.html" as="document"></style>',
                '<a rel="preload" href="home.html" as="document">Home</a>',
                '<img rel="preload" src="home.html" as="document">',
                '<link rel="preload" href="home.html" as="style">',
                '<link rel="preload" href="home.html" as="image">',
                '<link rel="stylesheet" href="home.html" as="document">',
                '<link rel="preloader" href="home.html" as="document">',
                '<link rel="preload" href="home.html">']:
            with self.subTest(html=html):
                self.markup(html);self.assertEqual(self.plan()['items'],[])

    def test_literal_href_must_be_explicit_and_exact_even_if_resolved_url_matches(self):
        original=copy.deepcopy(self.entry)
        for value in [None,'','./home.html','http://example.ucsd.edu/home.html','invented.html']:
            with self.subTest(value=value):
                self.entry.clear();self.entry.update(original);self.entry['originalHtmlAttribute']=value
                self.assertEqual(self.plan()['items'],[])
        self.entry.clear();self.entry.update(original);self.entry.pop('originalHtmlAttribute')
        self.assertEqual(self.plan()['items'],[])

    def test_resolved_target_requires_exact_scheme_port_query_and_path(self):
        for url in ['https://example.ucsd.edu/home.html','http://example.ucsd.edu:80/home.html',
                'http://example.ucsd.edu/home.html?q=1','http://example.ucsd.edu/home.html/',
                'http://example.ucsd.edu/other.html']:
            with self.subTest(url=url):
                self.entry['url']=url;self.assertEqual(self.plan()['items'],[])

    def test_actual_cross_host_non_http_and_credentialed_links_are_rejected(self):
        for url in ['http://other.ucsd.edu/home.html','javascript:alert(1)',
                'http://name:password@example.ucsd.edu/home.html']:
            with self.subTest(url=url):
                self.entry.update(url=url,originalHtmlAttribute=url)
                self.markup(f'<link rel="preload" href="{url}" as="document">')
                self.assertEqual(self.plan()['items'],[])

    def test_source_id_time_review_and_hash_are_required_and_cannot_be_stale(self):
        original=copy.deepcopy(self.entry)
        for field in ['sourceId','sourceObservedAt','reviewedAt','sourceBodySha256']:
            with self.subTest(missing=field):
                self.entry.clear();self.entry.update(original);self.entry.pop(field)
                self.assertEqual(self.plan()['items'],[])
        for field,value in [('sourceId','another'),('sourceObservedAt','2026-10-16T04:57:08+00:00'),
                ('sourceObservedAt','2026-10-16T04:57:07'),('reviewedAt','2026-10-16T05:05:00'),
                ('reviewedAt',None),('sourceBodySha256','0'*64),('sourceBodySha256',123)]:
            with self.subTest(field=field,value=value):
                self.entry.clear();self.entry.update(original);self.entry[field]=value
                self.assertEqual(self.plan()['items'],[])

    def test_actual_cache_hash_must_match_and_packet_hash_cannot_be_missing(self):
        self.html.write_text('<link rel="preload" href="home.html" as="document"><p>changed</p>')
        self.assertEqual(self.plan()['items'],[])
        self.markup('<link rel="preload" href="home.html" as="document">')
        self.source.pop('bodySha256');self.assertEqual(self.plan()['items'],[])

    def test_explicit_root_robots_auth_challenge_and_prior_boundary_are_not_bypassed(self):
        meta=copy.deepcopy(self.packet['latestDestinationFetch'])
        for change in [{'status':'robots_denied'},{'status':'authentication_required'},
                {'httpStatus':401},{'httpStatus':403},{'error':'access_challenge'},
                {'robots':{'status':'robots_denied'}},
                {'attemptHistory':[{'status':'access_challenge'}]}]:
            with self.subTest(change=change):
                self.packet['latestDestinationFetch']=dict(meta,**change)
                self.assertEqual(self.plan()['items'],[])

    def test_unreviewed_document_preload_is_never_automatically_discovered(self):
        self.entries=[];self.assertEqual(self.plan()['items'],[])

    def test_preload_discovery_does_not_accept_entity_or_mutate_original_root_or_science(self):
        self.write();before=[(self.out/name).read_bytes() for name in ['records/one.json','packets/one.json']]
        result=gaps.plan();self.assertEqual(result['liveCandidateCount'],1)
        self.assertEqual(before,[(self.out/name).read_bytes() for name in ['records/one.json','packets/one.json']])
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(url['entityAcceptanceStatus'],'provisional_or_unresolved')
        self.assertFalse(url['canCountAsVerifiedLabGroupURL'])
        self.assertEqual(url['redirectChain'],[]);self.assertEqual(url['observedFinalUrl'],self.url)


if __name__=='__main__':unittest.main()
