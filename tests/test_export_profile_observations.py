import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from apply_ucsd_coverage import accumulate_export_profile_patch, export_profile_routes
from rebuild_verified_atlas import build
from test_atlas_quality import atlas, professor


class ExportProfileObservationTests(unittest.TestCase):
    def test_same_name_sitemap_context_cannot_route_an_unbound_source_to_an_original_person(self):
        original='https://profiles.ucsd.edu/legacy.example';incoming='https://profiles.ucsd.edu/jane.example'
        person={'id':'original','name':'Jane Example','officialProfileUrl':original};people={'original':person}
        item={'url':incoming,'state':'done','fetch':{'status':'ok','sourceUrl':incoming,'finalUrl':incoming,'observedAt':'2026-10-17'},
              'contexts':[{'professorId':'original','sourceUrl':'https://profiles.ucsd.edu/sitemap.xml'}]}
        queue={'items':{'incoming':item}};routes,held=export_profile_routes(people,{},queue,[])
        self.assertEqual(routes[original],[person]);self.assertNotIn(incoming,routes)
        self.assertEqual(len(held),1);self.assertFalse(held[0]['fieldsApplied']);self.assertEqual(held[0]['capture'],item['fetch'])
        verified={'captureVerified':True,'professorId':'original','captures':[{'requestedUrl':incoming,'canonicalUri':incoming,'rdfAlternateUri':'https://researcherprofiles.org/profile/1/1.rdf'}]}
        routed,holds=export_profile_routes(people,{},queue,[verified]);self.assertEqual(routed[incoming],[person]);self.assertEqual(holds,[])
        with self.assertRaises(ValueError):export_profile_routes(people,{},queue,[{**verified,'captureVerified':False}])
        with self.assertRaises(ValueError):export_profile_routes(people,{},queue,[{**verified,'professorId':'unknown'}])

    def test_export_routes_keep_competing_original_owners_and_do_not_route_publisher_pages(self):
        uri='https://profiles.ucsd.edu/shared';publisher='https://department.ucsd.edu/faculty'
        people={pid:{'id':pid,'name':'Jane Example','officialProfileUrl':uri} for pid in ['first','second']}
        binding={'captureVerified':True,'professorId':'first','captures':[{'requestedUrl':publisher,'nameAsDisplayed':'Jane Example'}]}
        routes,holds=export_profile_routes(people,{}, {'items':{}},[binding])
        self.assertEqual({r['id'] for r in routes[uri]},{'first','second'});self.assertNotIn(publisher,routes)
        self.assertEqual(holds,[])

    def test_only_verified_person_merges_can_canonicalize_shared_resource_owners(self):
        uri='https://profiles.ucsd.edu/shared'
        people={pid:{'id':pid,'name':'Jane Example','officialProfileUrl':uri} for pid in ['retired','canonical']}
        review={'captureVerified':True,'sourceProfessorId':'retired','targetProfessorId':'canonical'}
        queue={'items':{'own':{'url':uri,'contexts':[{'professorId':'retired','sourceUrl':'https://profiles.ucsd.edu/sitemap.xml'}]}}}
        routes,holds=export_profile_routes(people,{},queue,[],[review]);self.assertEqual(routes[uri],[people['canonical']]);self.assertEqual(holds,[])
        with self.assertRaises(ValueError):export_profile_routes(people,{},queue,[],[{**review,'captureVerified':False}])
        with self.assertRaises(ValueError):export_profile_routes(people,{},queue,[],[review,{**review,'sourceProfessorId':'canonical','targetProfessorId':'retired'}])

    def test_multiple_captures_preserve_reviewed_history_sources_and_exact_proofs(self):
        old={'field':'appointmentStatus','value':'listed_faculty','fieldEvidence':[{'sourceUrl':'https://ece.ucsd.edu/people/faculty/emeritus','observedAt':'2026-10-16','evidence':'Professor Emeritus'}]}
        target={'previousFieldObservations':[old],'sourceUrls':['https://ece.ucsd.edu/people/faculty/emeritus'],
                'fieldEvidence':{'appointmentStatus':old['fieldEvidence']}}
        incoming={'previousFieldObservations':[{'field':'researchSummary','value':'Older own summary'}],
                  'sourceUrls':['https://profiles.ucsd.edu/jane.example'],
                  'fieldEvidence':{'appointmentStatus':[{'sourceUrl':'https://profiles.ucsd.edu/jane.example','observedAt':'2026-10-17','evidence':'Emeritus Professor'}]}}
        before=copy.deepcopy(incoming)
        accumulate_export_profile_patch(target,incoming,{})
        self.assertEqual(incoming,before)
        self.assertIn(old,target['previousFieldObservations'])
        self.assertEqual(target['sourceUrls'],['https://ece.ucsd.edu/people/faculty/emeritus','https://profiles.ucsd.edu/jane.example'])
        self.assertEqual(len(target['fieldEvidence']['appointmentStatus']),2)
        once=copy.deepcopy(target);accumulate_export_profile_patch(target,incoming,{});self.assertEqual(target,once)

    def test_redirect_or_another_display_name_cannot_reselect_reviewed_identity(self):
        original={'name':'Jane A. Example','officialProfileUrl':'https://profiles.ucsd.edu/jane.a.example'}
        target={**original,'fieldEvidence':{'officialProfileUrl':[{'sourceUrl':'https://directory.ucsd.edu/','evidence':'Jane A. Example -> own primary'}]}}
        incoming={'name':'Jane Example','officialProfileUrl':'https://profiles.ucsd.edu/jane.example','verifiedCanonicalProfile':True,
                  'sourceUrls':['https://profiles.ucsd.edu/jane.example'],
                  'researchSummary':'Complete positively observed own summary.',
                  'fieldEvidence':{k:[{'sourceUrl':'https://profiles.ucsd.edu/jane.example','observedAt':'2026-10-17','evidence':v}] for k,v in
                      [('name','Jane Example'),('officialProfileUrl','actual redirected resource'),('researchSummary','Complete positively observed own summary.')]}}
        accumulate_export_profile_patch(target,incoming,original)
        for k,v in original.items():self.assertEqual(target[k],v)
        self.assertNotIn('verifiedCanonicalProfile',target)
        self.assertEqual(target['researchSummary'],incoming['researchSummary'])
        self.assertEqual({o['field'] for o in target['additionalProfileObservations']},{'name','officialProfileUrl'})
        self.assertEqual(target['fieldEvidence']['officialProfileUrl'][0]['sourceUrl'],'https://directory.ucsd.edu/')
        once=copy.deepcopy(target);accumulate_export_profile_patch(target,incoming,original);self.assertEqual(target,once)

    def test_original_primary_is_retained_even_when_no_directory_patch_was_proposed(self):
        person={'name':'Jane Example','officialProfileUrl':'https://jacobsschool.ucsd.edu/faculty/faculty_bios/index.sfe?fmp_recid=1'}
        target={'fieldEvidence':{}}
        incoming={'officialProfileUrl':'https://jacobsschool.ucsd.edu/faculty/profile?id=1','verifiedCanonicalProfile':True,
                  'fieldEvidence':{'officialProfileUrl':[{'sourceUrl':person['officialProfileUrl'],'evidence':'actual301'}]}}
        accumulate_export_profile_patch(target,incoming,person)
        self.assertNotIn('officialProfileUrl',target)
        self.assertEqual(target['additionalProfileObservations'][0]['value'],incoming['officialProfileUrl'])
        self.assertNotIn('verifiedCanonicalProfile',target)

    def test_distinct_website_values_keep_their_own_proof_and_older_replays_cannot_roll_back(self):
        first='https://example.ucsd.edu/person';second=first+'/'
        oldproof={'sourceUrl':'https://directory.ucsd.edu/','observedAt':'2026-10-16T00:00:00+00:00','evidence':'Personal Website '+first}
        newproof={'sourceUrl':'https://department.ucsd.edu/jane','observedAt':'2026-10-17T00:00:00+00:00','evidence':'Personal Website '+second}
        target={'personalWebsiteUrl':first,'fieldEvidence':{'personalWebsiteUrl':[oldproof]}}
        fresh={'personalWebsiteUrl':second,'fieldEvidence':{'personalWebsiteUrl':[newproof]}}
        accumulate_export_profile_patch(target,fresh,{})
        self.assertEqual(target['personalWebsiteUrl'],second)
        self.assertEqual(target['fieldEvidence']['personalWebsiteUrl'],[newproof])
        self.assertTrue(any(o.get('field')=='personalWebsiteUrl' and o.get('value')==first
                            and o.get('fieldEvidence')==[oldproof] for o in target['previousFieldObservations']))
        accumulate_export_profile_patch(target,{'personalWebsiteUrl':first,'fieldEvidence':{'personalWebsiteUrl':[oldproof]}},{})
        self.assertEqual(target['personalWebsiteUrl'],second)
        self.assertEqual(target['fieldEvidence']['personalWebsiteUrl'],[newproof])
        once=copy.deepcopy(target);accumulate_export_profile_patch(target,fresh,{});self.assertEqual(target,once)

    def test_later_reachability_check_keeps_earlier_parsed_catalog_fact_and_its_date(self):
        uri='https://catalog.ucsd.edu/faculty/DSC.html'
        person=professor('jane','Jane Example','Mathematics')
        person.update(officialProfileUrl=uri,sourceUrls=[uri])
        data=atlas();data.update(professors=[person],qualityMigrationVersion=1)
        old={'sourceUrl':uri,'status':'reachable','observedAt':'2026-10-02T00:00:00+00:00',
             'catalogListings':[{'name':'Jane Example','listingRole':'Participating Faculty','evidence':'Jane Example, Professor, Mathematics'}]}
        fresh={'sourceUrl':uri,'status':'reachable','observedAt':'2026-10-17T00:00:00+00:00'}
        first,*_=build(copy.deepcopy(data),{},{},{},{'checks':[old]},{},{},{},{'checks':[fresh]})
        result=first['professors'][0]
        self.assertEqual(result['catalogListing']['observedAt'],old['observedAt'])
        self.assertEqual(result['fieldEvidence']['catalogListing'][0]['observedAt'],old['observedAt'])
        self.assertEqual(result['fieldEvidence']['catalogListing'][0]['evidence'],old['catalogListings'][0]['evidence'])
        repeated,*_=build(copy.deepcopy(first),{},{},{},{'checks':[old]},{},{},{},{'checks':[fresh]})
        self.assertEqual(first,repeated)


if __name__=='__main__':unittest.main()
