"""Offline admission of reviewed literal frame sources, without entity acceptance."""
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


class ReviewedFrameDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=gaps.OUT)
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.out=self.root/'data';self.cache=self.root/'collector'
        (self.out/'packets').mkdir(parents=True);(self.out/'records').mkdir();self.cache.mkdir()
        self.html=self.root/'source.html'
        self.url='http://example.ucsd.edu/old/index.htm'
        self.source={'sourceId':'reviewed-root','sourceUrl':self.url,
            'observedAt':'2026-10-16T01:00:00+00:00','cachePath':str(self.html),
            'role':'listed_lab_destination','title':'Example Lab','text':''}
        self.packet={'labId':'one','labName':'Example Lab','listedWebsite':self.url,
            'preparedAt':'2026-10-16T02:00:00+00:00','destinationQueueStates':['done'],
            'latestDestinationFetch':{'sourceUrl':self.url,'finalUrl':self.url,
                'observedAt':self.source['observedAt'],'status':'ok','httpStatus':200,'redirects':[]},
            'sources':[self.source]}
        self.raw={'labId':'one','status':'partial','summaryZh':None,'researchQuestions':[],
            'topics':[],'methods':[],'evidence':[],
            'identity':{'status':'uncertain','entityType':'unconfirmed','reason':'Frames do not establish identity.'},
            'affiliation':{'status':'uncertain','reason':'Unknown.'},'uncertainty':['Research is unknown.'],
            'blockers':['Frame target not reviewed.'],'reviewedAt':'2026-10-16T02:00:00+00:00'}
        self.entry={'url':'http://example.ucsd.edu/old/home.htm?view=1','labIds':['one'],
            'sourceId':self.source['sourceId'],'sourceObservedAt':self.source['observedAt'],
            'discoveryMechanism':'html_frame_source','originalHtmlAttribute':'home.htm?view=1',
            'reviewedAt':'2026-10-16T02:05:00+00:00','kind':'reviewed_identity_research_gap',
            'reason':'Individually reviewed literal main frame.'}
        self.entries=[self.entry];self.captures={}
        self.markup('<frameset><frame name="main" src="home.htm?view=1"></frameset>')
        for target,name,value in [(gaps,'OUT',self.out),(gaps,'CACHE',self.cache),
                (ledger,'ROOT',self.root),(ledger,'OUT',self.out)]:
            p=patch.object(target,name,value);p.start();self.addCleanup(p.stop)
        # No process probing, transport, or shared state is needed for admission.
        p=patch.object(gaps,'coordination_ready',return_value=False);p.start();self.addCleanup(p.stop)

    def put(self,name,value,base=None):
        path=(base or self.out)/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value))

    def markup(self,value):
        self.html.write_text(value)
        digest=hashlib.sha256(self.html.read_bytes()).hexdigest()
        self.source['bodySha256']=digest;self.entry['sourceBodySha256']=digest

    def write(self):
        self.put('manifest.json',{'items':[]})
        self.put('records/one.json',self.raw);self.put('packets/one.json',self.packet)
        self.put('reviewed-gap-additions.json',{'items':self.entries})
        self.put('queue.json',{'items':self.captures},self.cache)

    def plan(self):
        self.write();return gaps.plan()

    def test_literal_frame_and_iframe_with_no_display_text_are_admitted(self):
        for tag in ['frame','iframe']:
            with self.subTest(tag=tag):
                self.markup(f'<{tag} src="home.htm?view=1"></{tag}>')
                planned=self.plan();self.assertEqual(planned['liveCandidateCount'],1)
                candidate=planned['items'][0]
                self.assertEqual(candidate['url'],self.entry['url'])
                self.assertEqual(candidate['discoveryMechanism'],'html_frame_source')
                self.assertTrue(candidate['notAnAcceptedCanonicalLabUrl'])

    def test_actual_frameset_can_admit_main_and_navigation_frames_separately(self):
        self.markup('<frameset><frame src="side.htm" name="side"><frame src="home.htm?view=1" name="main"></frameset>')
        side=dict(self.entry,url='http://example.ucsd.edu/old/side.htm',originalHtmlAttribute='side.htm')
        self.entries.append(side)
        self.assertEqual({x['url'] for x in self.plan()['items']},{self.entry['url'],side['url']})

    def test_unseen_target_or_different_literal_src_is_rejected(self):
        original=copy.deepcopy(self.entry)
        for change in [{'url':'http://example.ucsd.edu/old/invented.htm'},
                {'originalHtmlAttribute':'./home.htm?view=1'},
                {'originalHtmlAttribute':'research.htm'}]:
            with self.subTest(change=change):
                self.entry.clear();self.entry.update(original);self.entry.update(change)
                self.assertEqual(self.plan()['items'],[])

    def test_ordinary_anchor_image_or_text_cannot_impersonate_a_frame(self):
        for markup in ['<a href="home.htm?view=1">Research</a>',
                '<img src="home.htm?view=1">',
                '<script>var x = \'<frame src="home.htm?view=1">\';</script>',
                '<!-- <frame src="home.htm?view=1"> -->']:
            with self.subTest(markup=markup):
                self.markup(markup);self.assertEqual(self.plan()['items'],[])

    def test_literal_cross_host_frame_is_rejected(self):
        self.entry.update(url='http://other.ucsd.edu/home.htm',originalHtmlAttribute='http://other.ucsd.edu/home.htm')
        self.markup('<iframe src="http://other.ucsd.edu/home.htm"></iframe>')
        self.assertEqual(self.plan()['items'],[])

    def test_scheme_query_path_and_port_changes_do_not_reuse_folded_url_keys(self):
        for target in ['https://example.ucsd.edu/old/home.htm?view=1',
                'http://example.ucsd.edu/old/home.htm?view=2',
                'http://example.ucsd.edu/old/home.htm/?view=1',
                'http://example.ucsd.edu:80/old/home.htm?view=1']:
            with self.subTest(target=target):
                self.entry['url']=target;self.assertEqual(self.plan()['items'],[])

    def test_non_http_or_credentialed_target_is_rejected(self):
        for target in ['javascript:alert(1)','http://name:password@example.ucsd.edu/old/home.htm']:
            with self.subTest(target=target):
                self.entry.update(url=target,originalHtmlAttribute=target)
                self.markup(f'<iframe src="{target}"></iframe>')
                self.assertEqual(self.plan()['items'],[])

    def test_actual_review_and_source_times_are_required(self):
        original=copy.deepcopy(self.entry)
        for field,value in [('reviewedAt',None),('reviewedAt','2026-10-16T02:05:00'),
                ('sourceObservedAt','2026-10-16T01:00:00'),('sourceObservedAt','invalid')]:
            with self.subTest(field=field,value=value):
                self.entry.clear();self.entry.update(original);self.entry[field]=value
                if field=='sourceObservedAt':self.source['observedAt']=value
                self.assertEqual(self.plan()['items'],[])

    def test_source_id_time_and_both_hash_bindings_must_be_current(self):
        original=copy.deepcopy(self.entry);source=copy.deepcopy(self.source)
        for change in [{'sourceId':'other'},{'sourceObservedAt':'2026-10-16T01:00:01+00:00'},
                {'sourceBodySha256':None},{'sourceBodySha256':123},{'sourceBodySha256':'stale'}]:
            with self.subTest(change=change):
                self.entry.clear();self.entry.update(original);self.entry.update(change)
                self.assertEqual(self.plan()['items'],[])
        self.entry.clear();self.entry.update(original);self.source.pop('bodySha256')
        self.assertEqual(self.plan()['items'],[])
        self.source.clear();self.source.update(source)

    def test_changed_cache_bytes_are_not_admitted_under_old_review_hash(self):
        self.html.write_text('<frame src="home.htm?view=1"><p>Changed after review.</p>')
        self.assertEqual(self.plan()['items'],[])

    def test_explicit_root_or_robots_boundaries_are_not_bypassed(self):
        original=copy.deepcopy(self.packet['latestDestinationFetch'])
        for change in [{'status':'robots_denied'},{'httpStatus':403},
                {'robots':{'status':'authentication_required','httpStatus':401}},
                {'attemptHistory':[{'status':'access_challenge'}]}]:
            with self.subTest(change=change):
                self.packet['latestDestinationFetch']=dict(original,**change)
                self.assertEqual(self.plan()['items'],[])

    def test_cached_robots_denial_and_existing_target_capture_keep_existing_controls(self):
        robots_url='http://example.ucsd.edu/robots.txt'
        stem='robots-'+hashlib.sha256(robots_url.encode()).hexdigest()
        self.put('responses/'+stem+'.json',{'status':'checked','sourceUrl':robots_url,
            'observedAt':self.source['observedAt']},self.cache)
        (self.cache/'responses'/(stem+'.html')).write_text('User-agent: *\nDisallow: /old/home.htm\n')
        candidate=self.plan()['items'][0]
        self.assertFalse(candidate['requiresLiveFetch'])
        self.assertEqual(candidate['availability'],'access_boundary_do_not_bypass')
        self.captures={'target':{'url':self.entry['url'],'state':'done','fetch':{
            'sourceUrl':self.entry['url'],'finalUrl':self.entry['url'],'status':'ok',
            'observedAt':'2026-10-16T02:00:00+00:00'}}}
        candidate=self.plan()['items'][0]
        self.assertFalse(candidate['requiresLiveFetch'])
        self.assertEqual(candidate['availability'],'captured_reuse_only')

    def test_discovery_does_not_accept_entity_rewrite_root_or_modify_science(self):
        self.write()
        before=[(self.out/name).read_bytes() for name in ['records/one.json','packets/one.json']]
        self.assertEqual(gaps.plan()['liveCandidateCount'],1)
        self.assertEqual(before,[(self.out/name).read_bytes() for name in ['records/one.json','packets/one.json']])
        _,verification=ledger.hydrate(self.raw,self.packet)
        self.assertEqual(verification['entityAcceptanceStatus'],'provisional_or_unresolved')
        self.assertFalse(verification['canCountAsVerifiedLabGroupURL'])
        self.assertEqual(verification['redirectChain'],[])
        self.assertEqual(verification['observedFinalUrl'],self.url)


if __name__=='__main__':unittest.main()
