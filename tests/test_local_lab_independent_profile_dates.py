"""Distinct original capture dates never replace baseline field observations."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

import test_local_lab_profile_link_gaps as fixtures
import local_lab_summary_gaps as gaps


class IndependentProfileDateTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.ReviewedHistoricalProfileLinkTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.f.proof['observedAt'] = '2026-10-03T01:44:19+00:00'
        self.f.rebind_baseline()
        self.f.entry.update(purpose='observe_literal_independently_dated_profile_lab_link',
                            sourceDateContract='independent_original_profile_capture',
                            historicalFieldObservedAt=self.f.proof['observedAt'])
        self.reviews()

    def reviews(self):
        f = self.f
        e = f.entry
        self.primary_row = dict(labId='one', listedWebsite=f.listed,
            oldFieldProof=copy.deepcopy(f.proof), oldFieldProofSha256=e['fieldProofSha256'],
            oldFieldObservedAt=f.proof['observedAt'],
            literalLabLink=copy.deepcopy(e['literalAnchor']),
            sameHostPathQueryDifferentScheme=True, independentDatedSourceValid=True,
            isSameOriginalFieldObservation=False, oldFieldDateUnchanged=True,
            sameExactProfileSourceURL=True, actualIndependentCaptureObservedAt=f.when,
            independentProfileBodySha256=e['profileCapture']['bodySha256'],
            rawSha256AtReview=e['rawSha256'], packetSha256AtReview=e['packetSha256'],
            currentRootFetchPreserved=copy.deepcopy(f.root_fetch),
            baselineProfessorRelations=[{'professorId':'person','officialProfileUrl':f.profile}])
        self.profile = dict(sourceUrl=f.profile, finalUrl=f.profile,
            actualCaptureObservedAt=f.when, bodySha256=e['profileCapture']['bodySha256'],
            originalMetadataSha256=e['profileCapture']['metadataSha256'], mainReadCompletely=True,
            mainTextSha256=fixtures.digest(gaps.DOM(f.body_path.read_text()).main().text().encode()))
        self.route = dict(labId='one', listedWebsite=f.listed,
            oldFieldProof=copy.deepcopy(f.proof), oldFieldProofSha256=e['fieldProofSha256'],
            oldFieldObservedAt=f.proof['observedAt'], literalLabLink=copy.deepcopy(e['literalAnchor']),
            sameHostPathQueryDifferentScheme=True,
            actualIndependentProfileCapture={'sourceUrl':f.profile,'actualCaptureObservedAt':f.when,
                'bodySha256':e['profileCapture']['bodySha256'],
                'originalMetadataSha256':e['profileCapture']['metadataSha256']},
            rawSha256=e['rawSha256'], packetSha256=e['packetSha256'],
            latestDestinationFetch=copy.deepcopy(f.root_fetch),
            decision='unobserved_literal_related_route_requires_independent_date_contract',
            literalOriginRobotsUnavailable=False, identityMismatchBoundary=False, externalTarget=False,
            exactRequestKeyLogicalAttempts=[], exactRequestKeyPending=[], ownWireEvents=[],
            ownOneShotJournals=[], explicitAccessBoundaries=[], packetExactRequestKeyChecks=[])
        self.write_reviews()

    def write_reviews(self, primary_rows=None, profiles=None, route_rows=None):
        f = self.f
        a = f.put('primary-review.json', {'items':primary_rows if primary_rows is not None else [self.primary_row],
                                       'profiles':profiles if profiles is not None else [self.profile]})
        f.entry.update(primaryReviewPath=str(a), primaryReviewSha256=fixtures.digest(a.read_bytes()))
        b = f.put('route-review.json', {'inputPrimaryReview':{'sha256':f.entry['primaryReviewSha256']},
                                       'items':route_rows if route_rows is not None else [self.route]})
        f.entry.update(routeBoundaryReviewPath=str(b), routeBoundaryReviewSha256=fixtures.digest(b.read_bytes()))

    def helper(self):
        self.f.write()
        self.f.put('reviewed-independent-date-profile-links.json', {'items':[self.f.entry]})
        return gaps.reviewed_independently_dated_profile_links(list(self.f.captures.values()))

    def test_distinct_capture_admits_separate_related_kind_without_retiming_root_or_field(self):
        before = copy.deepcopy((self.f.proof,self.f.raw,self.f.packet))
        result = self.helper()
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['kind'],gaps.INDEPENDENT_PROFILE_LINK_KIND)
        self.assertTrue(result[0]['notAnOriginalListedURLCheck'])
        self.assertEqual(result[0]['maxPageBytes'],2_000_000)
        self.assertEqual(before,(self.f.proof,self.f.raw,self.f.packet))
        plan = gaps.plan()
        self.assertEqual(plan['liveCandidateCount'],1)
        self.assertEqual(plan['items'][0]['kind'],gaps.INDEPENDENT_PROFILE_LINK_KIND)

    def test_old_same_capture_contract_stays_strict_and_purposes_cannot_cross_registries(self):
        self.assertEqual(len(self.helper()),1)
        old = dict(self.f.entry,purpose='observe_literal_historical_profile_lab_link')
        self.f.put('reviewed-profile-lab-links.json', {'items':[old]})
        self.assertEqual(gaps.reviewed_historical_profile_links([]),[])
        self.f.put('reviewed-independent-date-profile-links.json', {'items':[old]})
        self.assertEqual(gaps.reviewed_independently_dated_profile_links([]),[])

    def test_independent_source_requires_actual_distinct_instants_even_with_reports_rebound(self):
        self.f.proof['observedAt'] = self.f.when
        self.f.entry['historicalFieldObservedAt'] = self.f.when
        self.f.rebind_baseline();self.reviews()
        self.assertEqual(self.helper(),[])
        self.f.proof['observedAt'] = '2026-10-07T23:04:19+01:00'
        self.f.entry['historicalFieldObservedAt'] = self.f.proof['observedAt']
        self.f.rebind_baseline();self.reviews()
        self.assertEqual(self.helper(),[])

    def test_each_independent_contract_field_is_required(self):
        original = copy.deepcopy(self.f.entry)
        for field in ['sourceDateContract','historicalFieldObservedAt','primaryReviewPath',
                      'primaryReviewSha256','routeBoundaryReviewPath','routeBoundaryReviewSha256']:
            with self.subTest(field=field):
                self.f.entry.clear();self.f.entry.update(copy.deepcopy(original));self.f.entry.pop(field)
                self.assertEqual(self.helper(),[])

    def test_reports_must_be_owned_unchanged_and_unique_for_target(self):
        self.assertEqual(len(self.helper()),1)
        path = Path(self.f.entry['primaryReviewPath'])
        original = path.read_bytes();path.write_bytes(original+b' ')
        self.assertEqual(self.helper(),[]);path.write_bytes(original)
        outside = self.f.root/'outside.json';outside.write_bytes(original)
        self.f.entry['primaryReviewPath'] = str(outside)
        self.assertEqual(self.helper(),[])
        self.write_reviews(primary_rows=[self.primary_row,self.primary_row])
        self.assertEqual(self.helper(),[])
        self.write_reviews(profiles=[self.profile,self.profile])
        self.assertEqual(self.helper(),[])
        self.write_reviews(route_rows=[self.route,self.route])
        self.assertEqual(self.helper(),[])

    def test_rehashed_primary_report_still_binds_source_date_proof_label_professor_and_frozen_root(self):
        original = copy.deepcopy(self.primary_row)
        changes = {'oldFieldProofSha256':'0'*64,'oldFieldObservedAt':self.f.when,
            'actualIndependentCaptureObservedAt':'2026-10-08T00:00:00+00:00',
            'independentProfileBodySha256':'0'*64,'literalLabLink':{'label':'Other','href':self.f.url},
            'baselineProfessorRelations':[], 'oldFieldDateUnchanged':False,
            'isSameOriginalFieldObservation':True,'independentDatedSourceValid':False,
            'sameExactProfileSourceURL':False,'rawSha256AtReview':'0'*64,
            'packetSha256AtReview':'0'*64,'currentRootFetchPreserved':{},
            'oldFieldProof':dict(self.f.proof,status='unverified')}
        for field,value in changes.items():
            with self.subTest(field=field):
                self.primary_row = dict(copy.deepcopy(original),**{field:value});self.write_reviews()
                self.assertEqual(self.helper(),[])

    def test_rehashed_profile_review_requires_full_main_hash_and_original_sidecar(self):
        original = copy.deepcopy(self.profile)
        for field,value in [('mainReadCompletely',False),('mainTextSha256','0'*64),
                            ('originalMetadataSha256','0'*64),('finalUrl','https://profiles.ucsd.edu/other')]:
            with self.subTest(field=field):
                self.profile=dict(copy.deepcopy(original),**{field:value});self.write_reviews()
                self.assertEqual(self.helper(),[])

    def test_rehashed_route_review_cannot_hide_boundaries_attempts_or_old_source_tuple(self):
        original = copy.deepcopy(self.route)
        changes = {'literalOriginRobotsUnavailable':True,'identityMismatchBoundary':True,
            'externalTarget':True,'exactRequestKeyLogicalAttempts':[{}],
            'exactRequestKeyPending':[{}],'ownWireEvents':[{}],'ownOneShotJournals':[{}],
            'explicitAccessBoundaries':[{}],'packetExactRequestKeyChecks':[{}],
            'decision':'already_observed','actualIndependentProfileCapture':{},
            'rawSha256':'0'*64,'packetSha256':'0'*64,'latestDestinationFetch':{}}
        for field,value in changes.items():
            with self.subTest(field=field):
                self.route = dict(copy.deepcopy(original),**{field:value});self.write_reviews()
                self.assertEqual(self.helper(),[])

    def test_current_once_pending_robots_and_auth_boundaries_override_old_reports(self):
        for state in ['pending','running']:
            self.f.captures = {'x':{'url':self.f.url,'state':state}}
            self.assertEqual(self.helper(),[])
        self.f.captures={}
        self.f.put('gap-results.json', {'items':{},'originalUriObservationStarts':{self.f.url:{}}})
        self.assertEqual(self.helper(),[])
        self.f.put('gap-results.json', {'items':{}})
        self.f.put_robots({'status':'unavailable','httpStatus':302})
        self.assertEqual(self.helper(),[])

    def test_no_effective_root_slash_redirect_inference_and_no_https_substitution(self):
        f=self.f
        f.url='http://example.ucsd.edu';f.listed='https://example.ucsd.edu/'
        f.lab['labWebsiteUrl']=f.listed;f.proof['evidence']=f.label+' → '+f.listed
        f.entry.update(url=f.url,listedWebsite=f.listed,literalAnchor={'label':f.label,'href':f.url})
        f.packet['listedWebsite']=f.listed;f.rebind_baseline();f.set_markup(f.good_markup());f.freeze_records();self.reviews()
        f.captures={'https':{'url':f.listed,'state':'unresolved','fetch':copy.deepcopy(f.root_fetch)}}
        self.assertEqual(len(self.helper()),1)
        plan=gaps.plan();self.assertEqual(plan['items'][0]['availability'],'not_captured')
        self.assertEqual(plan['items'][0]['url'],'http://example.ucsd.edu')
        self.assertNotIn('redirects',plan['items'][0])

    def test_execution_journal_keeps_distinct_kind_and_two_dates_without_upgrading_root(self):
        candidate=dict(self.helper()[0],requiresLiveFetch=True)
        result,calls=self.f.execute_fixture(candidate)
        ledger=json.loads((self.f.out/'gap-results.json').read_text())
        start=ledger['originalUriObservationStarts'][self.f.url]
        self.assertEqual(start['journalContextKind'],gaps.INDEPENDENT_PROFILE_LINK_KIND)
        self.assertTrue(start['notAnOriginalListedURLCheck'])
        context=ledger['items'][self.f.url]['contexts']
        self.assertNotEqual(context['historicalFieldObservedAt'],context['profileCapture']['observedAt'])
        self.assertEqual(self.helper(),[])
        self.assertEqual(len(calls),2)
