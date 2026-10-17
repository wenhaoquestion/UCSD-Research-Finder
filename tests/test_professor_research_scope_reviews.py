import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from professor_research_scope_reviews import research_scope, keyword_scope, payload, digest, verified_research_scopes, apply_research_scopes, preserves_reviewed_research, proofs, RESEARCH_GROUP
from professor_own_field_reviews import apply_professor_fields
from rebuild_verified_atlas import RESEARCH_PHRASES, build, derive_research_tags
from refresh_labs import UCSD_PROFILES_OVERVIEW, UCSD_PROFILES_KEYWORDS
from test_atlas_quality import professor, atlas


class ResearchScopeReviewTests(unittest.TestCase):
    def fixture(self, cache, hold=False, generic=False):
        uri = 'https://department.ucsd.edu/people/jane' if generic else 'https://profiles.ucsd.edu/jane.example'
        career = 'Jane Example earned a BA in Social Ecology and a masters degree in Public Health. ' + 'Her clinical and committee work is described here. ' * 22
        research = 'Her research focuses on compensatory cognitive training and neuromodulation for cognitive impairment. She studies interventions for individuals with psychiatric illness.'
        full = career if hold else career + 'Research Interests ' + research
        if generic:
            markup = '<title>Jane Example</title><main><h1>Jane Example</h1><p>' + full + '</p><section>Another Person studies unrelated Cancer outside the reviewed paragraph.</section></main>'
        else:
            markup = ('<head><link rel="canonical" href="' + uri + '"><link rel="alternate" type="application/rdf+xml" href="https://researcherprofiles.org/profile/123/123.rdf"></head>'
                      '<main><div class="pageTitle"><h2>Jane Example</h2></div><div id="' + UCSD_PROFILES_OVERVIEW + '">' + full + '</div>'
                      '<section>Another Person studies unrelated Cancer outside the own overview.</section></main>')
        path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html');path.parent.mkdir();path.write_text(markup)
        item = {'url': uri, 'fetch': {'sourceUrl': uri, 'finalUrl': uri, 'httpStatus': 200, 'status': 'ok', 'observedAt': '2026-10-16T01:00:00+00:00', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}}
        person = professor('original', 'Jane Example', 'Psychiatry');person.update(officialProfileUrl=uri, sourceUrls=[uri], researchSummary=full[:1000], researchAreas=['Ecology', 'Public health'], researchKeywords=[], researchAreasFromDirectory=[])
        person['fieldEvidence'] = {f: [{'sourceUrl':uri, 'observedAt':item['fetch']['observedAt'], 'evidence':full[:1000], 'method':'ucsd_profiles_overview_section' if f=='researchSummary' else 'explicit_topic_phrases_in_sourced_research_paragraph'}] for f in ['researchSummary','researchAreas']}
        derive_research_tags(person)
        row = {'professorId':person['id'], 'originalPersonIdentity':{k:person[k] for k in ['id','name','department','officialProfileUrl']},
               'retainedCanonicalIdentity':{k:person[k] for k in ['id','name','department','officialProfileUrl']},
               'sourceCandidateAtlasSha256':'a'*64, 'previousFields':{k:copy.deepcopy(person[k]) for k in ['researchSummary','researchAreas']},
               'previousFieldEvidence':{k:copy.deepcopy(proofs(person,k)) for k in ['researchSummary','researchAreas']},
               'previousDependencies':{k:[] for k in ['researchKeywords','researchAreasFromDirectory']},
               'previousDependencyEvidence':{k:[] for k in ['researchKeywords','researchAreasFromDirectory']},
               'sourceScope':research_scope(item,cache,person['researchSummary']), 'researchPassages':[] if hold else [research],
               'areaClaims':[] if hold else [{'label':label,'literalPhrase':label,'evidencePassage':research} for label in ['compensatory cognitive training','neuromodulation']],
               'retainedDirectoryAreas':[], 'retainedDirectoryEvidence':[],
               'disposition':'hold_no_explicit_research_passage_selected' if hold else 'reviewed_explicit_own_research_passages',
               'semanticAssessment':'The degree labels are education. Use the later own research interests, or keep the fields unknown within this scope.',
               'reason':'Preserve old degree/clinical observations as history; no identity, primary, appointment or legacy-date change.'}
        row['previousFieldsSha256']=digest(row['previousFields']);row['fields'],row['fieldEvidence']=payload(row,RESEARCH_PHRASES)
        people={person['id']:person};routes={uri:[person]};queue={'items':{'own':item}}
        return person,item,row,path,research,people,routes,queue

    def test_degree_labels_are_replaced_by_the_complete_later_research_statement(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,item,row,_,research,people,routes,q=self.fixture(cache);original=copy.deepcopy(person)
            reviews=verified_research_scopes({'entries':[row]},q,cache,people,routes,RESEARCH_PHRASES)
            apply_research_scopes({'professors':[person]},reviews,RESEARCH_PHRASES)
            self.assertEqual(person['researchSummary'],research);self.assertNotIn(research,row['previousFields']['researchSummary'])
            self.assertEqual(person['researchAreas'],['compensatory cognitive training','neuromodulation'])
            for key in ['id','name','department','officialProfileUrl','lastVerified','recruitingStatus']:
                self.assertEqual(person[key],original[key])
            for field in ['researchSummary','researchAreas']:
                self.assertTrue(any(o.get('field')==field and o['value']==original[field] and o['fieldEvidence']==original['fieldEvidence'][field] for o in person['previousFieldObservations']))
            self.assertTrue(preserves_reviewed_research(person));before=copy.deepcopy(person);derive_research_tags(person);apply_research_scopes({'professors':[person]},reviews,RESEARCH_PHRASES);self.assertEqual(before,person)

    def test_source_scoped_hold_retains_clinical_bio_without_claiming_research_absence(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,_,row,_,_,people,routes,q=self.fixture(cache,hold=True);old=copy.deepcopy(person)
            reviews=verified_research_scopes({'entries':[row]},q,cache,people,routes,RESEARCH_PHRASES);apply_research_scopes({'professors':[person]},reviews,RESEARCH_PHRASES)
            self.assertEqual(person['researchSummary'],'Not found');self.assertEqual(person['researchAreas'],[])
            self.assertNotIn('researchSummary',person['fieldEvidence']);self.assertNotIn('researchAreas',person['fieldEvidence'])
            self.assertEqual(person['lastVerified'],old['lastVerified']);self.assertEqual(person['department'],'Psychiatry')
            self.assertTrue(any(o['value']==old['researchSummary'] for o in person['previousFieldObservations']))
            before=copy.deepcopy(person);derive_research_tags(person);self.assertEqual(person,before)

    def test_stale_capture_or_identity_and_unowned_or_competing_resources_fail_closed(self):
        for mode in ['bytes','date','name','owner','competing','redirect','scope','duplicate']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);person,item,row,path,_,people,routes,q=self.fixture(cache)
                if mode=='bytes':path.write_text(path.read_text()+'changed')
                if mode=='date':item['fetch']['observedAt']='2026-10-17T00:00:00+00:00'
                if mode=='name':person['name']='Another Person'
                if mode=='owner':routes={}
                if mode=='competing':routes[item['url']].append({**person,'id':'competing'})
                if mode=='redirect':item['fetch']['redirects']=[{'from':'https://different.ucsd.edu/','to':item['url'],'httpStatus':301}]
                if mode=='scope':row['sourceScope']['fullText']='Borrowed research statement'
                entries=[row,row] if mode=='duplicate' else [row]
                with self.assertRaises(ValueError):verified_research_scopes({'entries':entries},q,cache,people,routes,RESEARCH_PHRASES)

    def test_degree_or_other_person_text_cannot_justify_a_selected_research_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);_,_,row,_,_,people,routes,q=self.fixture(cache)
            for label,phrase in [('Ecology','Ecology'),('Public health','Public Health'),('Cancer','Cancer')]:
                wrong=copy.deepcopy(row);wrong['areaClaims']=[{'label':label,'literalPhrase':phrase,'evidencePassage':row['researchPassages'][0]}]
                with self.subTest(label=label),self.assertRaises(ValueError):payload(wrong,RESEARCH_PHRASES)
            wrong=copy.deepcopy(row);wrong['researchPassages']=['Another Person studies unrelated Cancer outside the own overview.']
            with self.assertRaises(ValueError):payload(wrong,RESEARCH_PHRASES)
            wrong=copy.deepcopy(row);wrong['fields']['researchSummary']='Invented research'
            with self.assertRaises(ValueError):verified_research_scopes({'entries':[wrong]},q,cache,people,routes,RESEARCH_PHRASES)

    def test_new_observations_cannot_be_overridden_by_replaying_an_older_semantic_review(self):
        for mode in ['summary','keyword','directory','proof']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);person,_,row,_,_,people,routes,q=self.fixture(cache);reviews=verified_research_scopes({'entries':[row]},q,cache,people,routes,RESEARCH_PHRASES);apply_research_scopes({'professors':[person]},reviews,RESEARCH_PHRASES)
                if mode=='summary':person['researchSummary']='A later independently sourced research observation.'
                if mode=='keyword':person['researchKeywords']=['Later keyword']
                if mode=='directory':person['researchAreasFromDirectory']=['Later topic']
                if mode=='proof':person['fieldEvidence']['researchSummary'][0]['observedAt']='2026-10-17'
                before=copy.deepcopy(person);self.assertFalse(preserves_reviewed_research(person))
                with self.assertRaises(ValueError):apply_research_scopes({'professors':[person]},reviews,RESEARCH_PHRASES)
                self.assertEqual(person,before)

    def test_generic_paragraph_and_literal_mapping_are_scoped_to_actual_research(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,_,row,_,research,people,routes,q=self.fixture(cache,generic=True)
            row['areaClaims']=[{'label':'Cognitive science','literalPhrase':'cognitive','evidencePassage':research}]
            with self.assertRaises(ValueError):payload(row,RESEARCH_PHRASES)
            row['areaClaims']=[{'label':'neuromodulation','literalPhrase':'neuromodulation','evidencePassage':research}];row['fields'],row['fieldEvidence']=payload(row,RESEARCH_PHRASES)
            reviews=verified_research_scopes({'entries':[row]},q,cache,people,routes,RESEARCH_PHRASES)
            self.assertEqual(reviews[0]['sourceScope']['kind'],'named_main_own_paragraph')
            self.assertNotIn('Cancer',str(reviews[0]['fields']))

    def test_build_cannot_resurrect_unsupported_topics_and_is_idempotent(self):
        for hold in [False,True]:
            with self.subTest(hold=hold),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);person,_,row,_,_,people,routes,q=self.fixture(cache,hold=hold);reviews=verified_research_scopes({'entries':[row]},q,cache,people,routes,RESEARCH_PHRASES)
                data=atlas();data.update(qualityMigrationVersion=1,professors=[person]);first,*_=build(copy.deepcopy(data),{},{},{},{},{},{},{},{'reviewedProfessorResearchScopes':reviews})
                repeated,*_=build(copy.deepcopy(first),{},{},{},{},{},{},{},{'reviewedProfessorResearchScopes':reviews});self.assertEqual(first,repeated)
                self.assertNotIn('Ecology',first['professors'][0]['researchAreas']);self.assertEqual(first['professors'][0]['researchSummary'],row['fields']['researchSummary'])

    def test_directly_reviewed_directory_labels_keep_their_original_proof_and_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,_,row,_,_,people,routes,q=self.fixture(cache)
            old={'sourceUrl':'https://directory.ucsd.edu/faculty','observedAt':'2020-01-01','method':'explicit_research_areas_in_official_directory','evidence':'Jane Example | Exact directory topic'}
            person['researchAreasFromDirectory']=['Exact directory topic'];person['researchAreas'].insert(0,'Exact directory topic');person['fieldEvidence']['researchAreasFromDirectory']=[old];person['fieldEvidence']['researchAreas'].insert(0,old)
            row['previousFields']['researchAreas']=copy.deepcopy(person['researchAreas']);row['previousFieldsSha256']=digest(row['previousFields']);row['previousFieldEvidence']['researchAreas']=copy.deepcopy(proofs(person,'researchAreas'));row['previousDependencies']['researchAreasFromDirectory']=person['researchAreasFromDirectory'];row['previousDependencyEvidence']['researchAreasFromDirectory']=[old];row['retainedDirectoryAreas']=['Exact directory topic'];row['retainedDirectoryEvidence']=[old];row['fields'],row['fieldEvidence']=payload(row,RESEARCH_PHRASES)
            reviews=verified_research_scopes({'entries':[row]},q,cache,people,routes,RESEARCH_PHRASES);apply_research_scopes({'professors':[person]},reviews,RESEARCH_PHRASES)
            self.assertEqual(person['researchAreas'][0],'Exact directory topic');self.assertIn(old,person['fieldEvidence']['researchAreas'])
            wrong=copy.deepcopy(row);wrong['retainedDirectoryEvidence'][0]['observedAt']='2026-10-17'
            with self.assertRaises(ValueError):verified_research_scopes({'entries':[wrong]},q,cache,people,routes,RESEARCH_PHRASES)

    def test_clinical_overview_hold_keeps_separate_declared_research_keywords(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,item,row,path,_,people,routes,q=self.fixture(cache,hold=True)
            path.write_text(path.read_text().replace('</main>',f'<div id="{RESEARCH_GROUP}"><div id="{UCSD_PROFILES_KEYWORDS}"><a>Machine learning</a><a>Genetics</a></div></div></main>'))
            item['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();person['researchKeywords']=['Machine learning','Genetics'];person['researchAreas']=['Machine learning','Genetics']
            row.update(sourceScope=research_scope(item,cache,person['researchSummary']),retainedKeywordAreas=person['researchAreas'],retainedKeywordSources=[keyword_scope(item,cache)])
            row['previousFields']['researchAreas']=copy.deepcopy(person['researchAreas']);row['previousFieldsSha256']=digest(row['previousFields']);row['previousDependencies']['researchKeywords']=copy.deepcopy(person['researchKeywords']);row['fields'],row['fieldEvidence']=payload(row,RESEARCH_PHRASES)
            reviews=verified_research_scopes({'entries':[row]},q,cache,people,routes,RESEARCH_PHRASES);apply_research_scopes({'professors':[person]},reviews,RESEARCH_PHRASES)
            self.assertEqual(person['researchSummary'],'Not found');self.assertEqual(person['researchAreas'],['Machine learning','Genetics']);self.assertEqual(person['researchKeywords'],['Machine learning','Genetics'])
            self.assertEqual(person['fieldEvidence']['researchAreas'][0]['researchGroupId'],RESEARCH_GROUP)
            wrong=copy.deepcopy(row);wrong['retainedKeywordAreas']=['Cancer']
            with self.assertRaises(ValueError):payload(wrong,RESEARCH_PHRASES)
            wrong=copy.deepcopy(row);wrong['retainedKeywordSources'][0]['terms']=['Different topic']
            with self.assertRaises(ValueError):verified_research_scopes({'entries':[wrong]},q,cache,people,routes,RESEARCH_PHRASES)
            path.write_text(path.read_text().replace(RESEARCH_GROUP,'different-group'));item['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):keyword_scope(item,cache)

    def test_same_owned_page_can_replace_a_wrong_career_paragraph_with_explicit_research(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,item,row,path,research,people,routes,q=self.fixture(cache,generic=True)
            path.write_text(path.read_text().replace('</main>','<p>'+research+'</p></main>'));item['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            row['sourceScope']=research_scope(item,cache,person['researchSummary'],research);row['fields'],row['fieldEvidence']=payload(row,RESEARCH_PHRASES)
            verified=verified_research_scopes({'entries':[row]},q,cache,people,routes,RESEARCH_PHRASES)
            self.assertEqual(verified[0]['sourceScope']['kind'],'named_main_reviewed_research_paragraph')
            self.assertTrue(verified[0]['sourceScope']['previousExcerptParagraphText'].startswith('Jane Example earned'))
            self.assertEqual(verified[0]['fields']['researchSummary'],research)
            with self.assertRaises(ValueError):research_scope(item,cache,person['researchSummary'],'Invented paragraph')

    def test_funded_own_research_description_is_separate_from_role_only_overview(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,item,row,path,_,people,routes,q=self.fixture(cache,hold=True)
            funded='Defensive Healthcare Research NIH R01 Jan 1, 2020 - Dec 31, 2022 Role: Co-Principal Investigator Description: Our project develops and tests resilient healthcare systems and patient-safety tools.'
            path.write_text(path.read_text().replace('</main>',f'<div id="{RESEARCH_GROUP}">research activities and funding {funded}</div></main>'));item['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            row['sourceScope']=research_scope(item,cache,person['researchSummary'],reviewed_research_group=True);row['researchPassages']=[funded];row['disposition']='reviewed_explicit_own_research_passages';row['fields'],row['fieldEvidence']=payload(row,RESEARCH_PHRASES)
            verified=verified_research_scopes({'entries':[row]},q,cache,people,routes,RESEARCH_PHRASES)
            self.assertIn('2022',verified[0]['fields']['researchSummary']);self.assertEqual(verified[0]['sourceScope']['kind'],'profiles_own_research_funding_group');self.assertEqual(verified[0]['sourceScope']['previousOverviewText'][:1000],person['researchSummary'])
            path.write_text(path.read_text().replace('Description:','Other:'));item['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):research_scope(item,cache,person['researchSummary'],reviewed_research_group=True)

    def test_independent_own_badges_survive_later_scope_review_and_older_review_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);person,item,row,_,_,people,routes,q=self.fixture(cache)
            badge={'sourceUrl':'https://math.ucsd.edu/people/jane','observedAt':'2020-01-01','method':'named_own_badge','evidence':'Exact own research badge'}
            own={'professorId':person['id'],'sourceProfessorId':person['id'],'captureVerified':True,'fields':{'researchAreas':['Exact badge']},'fieldEvidence':{'researchAreas':[badge]},'sourceObservation':{'nameAsDisplayed':person['name'],'capture':row['sourceScope']['capture']}}
            person['researchAreas']=['Exact badge'];person['fieldEvidence']['researchAreas']=[badge];person['professorFieldReviews']=[copy.deepcopy(own)];row['previousFields']['researchAreas']=['Exact badge'];row['previousFieldsSha256']=digest(row['previousFields']);row['previousFieldEvidence']['researchAreas']=[badge];row['retainedOwnFieldAreas']=['Exact badge'];row['retainedOwnFieldEvidence']=[badge];row['fields'],row['fieldEvidence']=payload(row,RESEARCH_PHRASES)
            with self.assertRaises(ValueError):verified_research_scopes({'entries':[row]},q,cache,people,routes,RESEARCH_PHRASES)
            reviews=verified_research_scopes({'entries':[row]},q,cache,people,routes,RESEARCH_PHRASES,[own]);apply_research_scopes({'professors':[person]},reviews,RESEARCH_PHRASES);before=copy.deepcopy(person)
            apply_professor_fields({'professors':[person]},[own]);self.assertEqual(person,before);self.assertIn('Exact badge',person['researchAreas']);self.assertIn('neuromodulation',person['researchAreas'])

    def test_scripps_research_topic_label_keeps_its_published_punctuation(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);uri='https://scripps.ucsd.edu/profiles/jexample';markup='<main><h1>Jane Example</h1><div class="views-field views-field-research-topic"><span class="views-label views-label-research-topic">Research Topics:</span><span><a>Marine Microbiology</a><a>Genomics</a></span></div></main>'
            path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.parent.mkdir();path.write_text(markup);item={'url':uri,'fetch':{'sourceUrl':uri,'finalUrl':uri,'observedAt':'2026-10-16','httpStatus':200,'status':'ok','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}
            scope=keyword_scope(item,cache);self.assertEqual(scope['terms'],['Marine Microbiology','Genomics']);self.assertEqual(scope['fieldLabelAsPublished'],'Research Topics:');self.assertNotIn('researchGroupId',scope)
            path.write_text(markup.replace('Research Topics:','Clinical Services:'));item['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):keyword_scope(item,cache)


if __name__=='__main__':unittest.main()
