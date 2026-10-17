"""New independent person pages must not merge solely by their displayed names."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collect_ucsd_coverage import profiles_appointment
from review_ucsd_coverage import faculty_review
from candidate_profile_associations import clinical_profile_links, provider_metadata, same_subject


class NewCandidateProfileAssociationTests(unittest.TestCase):
    def fixture(self, cache, second_name='Jane Example', shared_ids=False):
        (cache/'responses').mkdir();items={};rows=[]
        for index,(name,unit) in enumerate([('Jane Example','Physics'),(second_name,'Provost - Revelle')]):
            uri='https://profiles.ucsd.edu/jane'+('.a' if index else '')+'.example'
            canonical='https://profiles.ucsd.edu/jane.example' if shared_ids else uri
            rdf='100' if shared_ids or not index else '200'
            raw=('<html><head><link rel="canonical" href="'+canonical+'"><link rel="alternate" type="application/rdf+xml" href="https://researcherprofiles.org/profile/'+rdf+'/'+rdf+'.rdf"></head><body><main><div class="pageTitle"><h2>'+name+'</h2></div><table><tr><th>Title(s)</th><td>Professor, '+unit+'</td></tr><tr><th>School</th><td>Vc-academic Affairs</td></tr></table></main></body></html>')
            path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.write_text(raw)
            meta={'sourceUrl':uri,'finalUrl':uri,'observedAt':f'2026-10-16T0{index}:00:00Z','status':'ok','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            _,row=profiles_appointment(meta,raw);rows.append(row);items[uri]={'url':uri,'state':'done','fetch':meta,'contexts':[]}
        return {'items':items,'facultyListings':rows},rows

    def review(self, queue, cache):
        return faculty_review(queue,{'professors':[],'labs':[]},cache,profile_identity_review={'entries':[]})

    def test_same_display_name_in_different_units_retains_first_source_and_holds_unproved_association(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);queue,rows=self.fixture(cache);result=self.review(queue,cache)
            self.assertEqual(len(result['professors']),1)
            person=result['professors'][0]
            self.assertEqual(person['id'],rows[0]['discoveryId'])
            self.assertEqual(person['officialProfileUrl'],rows[0]['profileUrl'])
            self.assertEqual(len(person['directoryListings']),1)
            self.assertEqual(len(result['uncertainListings']),1)
            hold=result['uncertainListings'][0]
            self.assertEqual(hold['listing']['sourceUrl'],rows[1]['sourceUrl'])
            self.assertEqual(hold['reason'],'distinct_profile_same_or_similar_name_requires_identity_review')
            self.assertEqual(hold['candidateProposedProfessorIds'],[person['id']])

    def test_middle_name_omission_cannot_merge_different_captured_person_identifiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);queue,rows=self.fixture(cache,second_name='Jane A. Example');result=self.review(queue,cache)
            self.assertEqual(result['professors'][0]['officialProfileUrl'],rows[0]['profileUrl'])
            self.assertEqual(len(result['professors'][0]['directoryListings']),1)
            self.assertEqual(len(result['uncertainListings']),1)

    def test_same_declared_canonical_and_personal_rdf_corroborates_without_replacing_first_primary(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);queue,rows=self.fixture(cache,shared_ids=True);result=self.review(queue,cache)
            self.assertEqual(result['uncertainListings'],[])
            person=result['professors'][0]
            self.assertEqual(person['id'],rows[0]['discoveryId'])
            self.assertEqual(person['officialProfileUrl'],rows[0]['profileUrl'])
            self.assertEqual(len(person['directoryListings']),2)
            evidence=person['directoryListings'][1]['identityEvidence']
            self.assertEqual(evidence['newCandidateSourceIdentity']['type'],'shared_canonical_and_personal_rdf')

    def test_actual_canonical_declares_literal_uncaptured_first_uri(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);queue,rows=self.fixture(cache,shared_ids=True)
            del queue['items'][rows[0]['sourceUrl']]
            result=self.review(queue,cache)
            self.assertEqual(result['uncertainListings'],[])
            self.assertEqual(result['professors'][0]['officialProfileUrl'],rows[0]['profileUrl'])
            self.assertEqual(len(result['professors'][0]['directoryListings']),2)

    def test_conflicting_captured_personal_rdf_prevents_single_canonical_shortcut(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);queue,rows=self.fixture(cache)
            item=queue['items'][rows[1]['sourceUrl']]
            path=cache/'responses'/(hashlib.sha256(item['url'].encode()).hexdigest()+'.html')
            path.write_text(path.read_text().replace('rel="canonical" href="'+item['url']+'"',
                                                    'rel="canonical" href="'+rows[0]['sourceUrl']+'"'))
            item['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            result=self.review(queue,cache)
            self.assertEqual(len(result['uncertainListings']),1)
            self.assertEqual(len(result['professors'][0]['directoryListings']),1)

    def test_clinical_contact_requires_own_table_and_rejects_coauthor_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);queue,rows=self.fixture(cache)
            item=queue['items'][rows[0]['sourceUrl']]
            path=cache/'responses'/(hashlib.sha256(item['url'].encode()).hexdigest()+'.html')
            original=path.read_text()
            link='<a href="https://providers.ucsd.edu/details/123/neurology">Clinical Profile</a>'
            for context,expected in [('<div id="view_links_table"><table><tr class="website-table"><td>'+link+'</td></tr></table></div>',1),
                                     ('<div class="publicationList">'+link+'</div>',0),
                                     ('<div id="view_links_table"><table><tr><td>'+link+'</td></tr></table></div>',0)]:
                path.write_text(original.replace('</main>',context+'</main>'))
                item['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(len(clinical_profile_links(item,cache,'Jane Example')),expected)
            self.assertEqual(clinical_profile_links(item,cache,'Jane B. Other'),[])

    def test_provider_metadata_requires_unique_canonical_matching_own_titles_and_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);(cache/'responses').mkdir()
            uri='https://providers.ucsd.edu/details/123/neurology'
            title='Jane A. Example, MD | Neurology | UC San Diego Health'
            markup='<html><head><title>'+title+'</title><meta property="og:title" content="'+title+'"><link rel="canonical" href="'+uri+'"></head></html>'
            path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.write_text(markup)
            item={'url':uri,'fetch':{'status':'ok','sourceUrl':uri,'finalUrl':uri,'observedAt':'2026-10-16T00:00:00Z','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}
            self.assertEqual(provider_metadata(item,cache,'Jane Example')['canonicalUri'],uri)
            self.assertIsNone(provider_metadata(item,cache,'Jane B. Example'))
            path.write_text(markup.replace('</head>','<link rel="canonical" href="'+uri+'"></head>'))
            item['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertIsNone(provider_metadata(item,cache,'Jane Example'))

    def test_conflicting_middle_names_do_not_qualify_subject(self):
        self.assertFalse(same_subject('Jane B. Example','Jane A. Example'))
        self.assertTrue(same_subject('Jane A. Example','Jane Alice Example'))
        self.assertTrue(same_subject('Jorge A. Munoz Pineda','Jorge Munoz Pineda'))
