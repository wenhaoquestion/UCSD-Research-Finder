"""Offline reviewed image-map area discovery; no automatic link following."""
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


class ReviewedImageMapTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=gaps.OUT);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.out=self.root/'data';self.cache=self.root/'collector'
        (self.out/'records').mkdir(parents=True);(self.out/'packets').mkdir();self.cache.mkdir()
        self.html=self.root/'navigation.html';self.url='http://example.ucsd.edu/lab/navigation.htm'
        self.source={'sourceId':'reviewed-navigation','sourceUrl':self.url,
            'observedAt':'2026-10-16T05:33:15+00:00','cachePath':str(self.html),
            'title':'Navigation','text':'','role':'reviewed_followup_requires_entity_match'}
        self.packet={'labId':'one','labName':'Named Lab','listedWebsite':'http://example.ucsd.edu/lab/',
            'preparedAt':'2026-10-16T05:34:00+00:00','destinationQueueStates':['done'],
            'latestDestinationFetch':{'sourceUrl':'http://example.ucsd.edu/lab/',
                'finalUrl':'http://example.ucsd.edu/lab/','status':'ok','httpStatus':200,
                'observedAt':'2026-10-16T04:57:00+00:00','redirects':[]},'sources':[self.source]}
        self.raw={'labId':'one','status':'partial','summaryZh':None,'researchQuestions':[],
            'topics':[],'methods':[],'evidence':[],
            'identity':{'status':'uncertain','entityType':'unconfirmed','reason':'Target unreviewed.'},
            'affiliation':{'status':'uncertain','reason':'Unknown.'},'uncertainty':['Research unknown.'],
            'blockers':['Only navigation captured.'],'reviewedAt':'2026-10-16T05:34:00+00:00'}
        self.href='mads/mads-new.htm?view=1'
        self.entry={'url':'http://example.ucsd.edu/lab/'+self.href,'labIds':['one'],
            'sourceId':self.source['sourceId'],'sourceObservedAt':self.source['observedAt'],
            'reviewedAt':'2026-10-16T05:35:00+00:00','discoveryMechanism':'html_image_map_area',
            'originalHtmlAttribute':self.href,'mapName':'FrontPageMap',
            'kind':'reviewed_identity_research_gap','reason':'Reviewed actual used image-map area.'}
        self.entries=[self.entry];self.captures={}
        self.valid=f'<MAP NAME="FrontPageMap"><AREA HREF="{self.href}"></MAP><img src="nav.gif" usemap="#FrontPageMap">'
        self.markup(self.valid)
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

    def test_reviewed_real_used_image_map_area_is_admitted(self):
        result=self.plan();self.assertEqual(result['liveCandidateCount'],1)
        candidate=result['items'][0]
        self.assertEqual(candidate['discoveryMechanism'],'html_image_map_area')
        self.assertEqual(candidate['url'],self.entry['url'])
        self.assertEqual(candidate['mapName'],'FrontPageMap')
        self.assertTrue(candidate['notAnAcceptedCanonicalLabUrl'])
        # This mechanism discovers navigation, so valid nav markup is allowed.
        self.markup('<nav>'+self.valid+'</nav>')
        self.assertEqual(self.plan()['liveCandidateCount'],1)

    def test_multiple_real_areas_require_individual_reviewed_entries(self):
        self.markup(f'<map name="FrontPageMap"><area href="{self.href}"><area href="flower/intro.htm"></map><img usemap="#FrontPageMap">')
        self.assertEqual([x['url'] for x in self.plan()['items']],[self.entry['url']])
        flower=dict(self.entry,url='http://example.ucsd.edu/lab/flower/intro.htm',originalHtmlAttribute='flower/intro.htm')
        self.entries.append(flower)
        self.assertEqual({x['url'] for x in self.plan()['items']},{self.entry['url'],flower['url']})

    def test_orphan_area_unused_map_or_wrong_usemap_cannot_admit(self):
        for html in [f'<area href="{self.href}"><img usemap="#FrontPageMap">',
                f'<map name="FrontPageMap"><area href="{self.href}"></map>',
                f'<map name="FrontPageMap"></map><area href="{self.href}"><img usemap="#FrontPageMap">',
                f'<map name="FrontPageMap"><map name="OtherMap"><area href="{self.href}"></map></map><img usemap="#FrontPageMap">',
                self.valid.replace('#FrontPageMap','#OtherMap'),
                self.valid.replace('#FrontPageMap','FrontPageMap'),
                self.valid.replace('usemap="#FrontPageMap"','usemap="navigation.htm#FrontPageMap"')]:
            with self.subTest(html=html):
                self.markup(html);self.assertEqual(self.plan()['items'],[])

    def test_script_style_comment_anchor_image_and_webbot_spoofs_are_rejected(self):
        for html in ['<!-- webbot bot="ImageMap" '+self.valid+' -->',
                '<style>'+self.valid+'</style>','<script>var x=\''+self.valid+'\';</script>',
                f'<a href="{self.href}">Research</a>',
                f'<map name="FrontPageMap"><a href="{self.href}">Research</a></map><img usemap="#FrontPageMap">',
                f'<map name="FrontPageMap"><area href="{self.href}"></map><a usemap="#FrontPageMap">Image</a>',
                f'<img src="{self.href}" usemap="#FrontPageMap">']:
            with self.subTest(html=html):
                self.markup(html);self.assertEqual(self.plan()['items'],[])

    def test_map_name_and_literal_href_are_mandatory_and_exact(self):
        original=copy.deepcopy(self.entry)
        for field in ['mapName','originalHtmlAttribute']:
            with self.subTest(missing=field):
                self.entry.clear();self.entry.update(original);self.entry.pop(field)
                self.assertEqual(self.plan()['items'],[])
        for field,value in [('mapName','OtherMap'),('mapName','frontpagemap'),('mapName',None),
                ('originalHtmlAttribute','./'+self.href),('originalHtmlAttribute',None)]:
            with self.subTest(field=field,value=value):
                self.entry.clear();self.entry.update(original);self.entry[field]=value
                self.assertEqual(self.plan()['items'],[])

    def test_target_scheme_port_query_path_cannot_use_folded_discovery_keys(self):
        original=self.entry['url']
        for url in [original.replace('http:','https:'),original.replace('.edu/','.edu:80/'),
                original.replace('view=1','view=2'),original.replace('.htm?','.htm/?'),
                original.replace('/mads/','/invented/')]:
            with self.subTest(url=url):
                self.entry['url']=url;self.assertEqual(self.plan()['items'],[])

    def test_actual_cross_host_or_invalid_protocol_area_is_rejected(self):
        for url in ['http://other.ucsd.edu/research','javascript:alert(1)',
                'http://name:password@example.ucsd.edu/lab/research']:
            with self.subTest(url=url):
                self.entry.update(url=url,originalHtmlAttribute=url)
                self.markup(f'<map name="FrontPageMap"><area href="{url}"></map><img usemap="#FrontPageMap">')
                self.assertEqual(self.plan()['items'],[])

    def test_source_review_id_time_hash_bindings_cannot_be_missing_or_stale(self):
        original=copy.deepcopy(self.entry)
        for field in ['sourceId','sourceObservedAt','reviewedAt','sourceBodySha256']:
            with self.subTest(missing=field):
                self.entry.clear();self.entry.update(original);self.entry.pop(field)
                self.assertEqual(self.plan()['items'],[])
        for field,value in [('sourceId','other'),('sourceObservedAt','2026-10-16T05:33:16+00:00'),
                ('sourceObservedAt','2026-10-16T05:33:15'),('reviewedAt',None),
                ('reviewedAt','2026-10-16T05:35:00'),('sourceBodySha256','0'*64),('sourceBodySha256',123)]:
            with self.subTest(field=field,value=value):
                self.entry.clear();self.entry.update(original);self.entry[field]=value
                self.assertEqual(self.plan()['items'],[])

    def test_changed_cache_or_absent_packet_hash_is_rejected(self):
        self.html.write_text(self.valid+'<p>Changed after review</p>')
        self.assertEqual(self.plan()['items'],[])
        self.markup(self.valid);self.source.pop('bodySha256')
        self.assertEqual(self.plan()['items'],[])

    def test_explicit_root_and_robots_boundaries_are_preserved(self):
        original=copy.deepcopy(self.packet['latestDestinationFetch'])
        for change in [{'status':'robots_denied'},{'status':'authentication_required'},
                {'httpStatus':401},{'httpStatus':403},{'error':'access_challenge'},
                {'robots':{'status':'robots_denied'}},{'attemptHistory':[{'status':'access_challenge'}]}]:
            with self.subTest(change=change):
                self.packet['latestDestinationFetch']=dict(original,**change)
                self.assertEqual(self.plan()['items'],[])

    def test_no_automatic_area_discovery_or_entity_science_root_mutation(self):
        self.entries=[];self.assertEqual(self.plan()['items'],[])
        self.entries=[self.entry];self.write()
        before=[(self.out/name).read_bytes() for name in ['records/one.json','packets/one.json']]
        self.assertEqual(gaps.plan()['liveCandidateCount'],1)
        self.assertEqual(before,[(self.out/name).read_bytes() for name in ['records/one.json','packets/one.json']])
        _,url=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(url['entityAcceptanceStatus'],'provisional_or_unresolved')
        self.assertFalse(url['canCountAsVerifiedLabGroupURL'])
        self.assertEqual(url['redirectChain'],[])
        self.assertEqual(url['observedFinalUrl'],self.packet['listedWebsite'])


if __name__=='__main__':unittest.main()
