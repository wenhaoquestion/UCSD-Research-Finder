import importlib.util
from pathlib import Path
import unittest
import datetime as dt
import hashlib
import json
import tempfile
import copy
import contextlib
import io
import sys
from types import SimpleNamespace
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
SPEC = importlib.util.spec_from_file_location("refresh_labs", Path(__file__).resolve().parents[1] / "scripts/refresh_labs.py")
LABS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LABS)


class EvidenceExtractionTests(unittest.TestCase):
    def setUp(self):
        self.person = {"id": "ada", "name": "Ada Example", "department": "Example", "officialProfileUrl": "https://example.ucsd.edu/people/ada"}
        self.meta = {"status": "ok", "sourceUrl": self.person["officialProfileUrl"], "observedAt": "2026-10-02T12:00:00+00:00"}

    def test_navigation_cannot_create_lab_or_email(self):
        patch, labs = LABS.parse_profile(self.person, self.meta, '''<title>Ada Example</title><nav><a href="/bad">Wrong Lab</a></nav>
        <main><h1>Ada Example</h1><p><a href="mailto:ada@ucsd.edu">ada@ucsd.edu</a></p>
        <aside><a href="mailto:staff@ucsd.edu">staff@ucsd.edu</a><a href="/bad2">Other Lab</a></aside></main>
        <footer><a href="/bad3">Footer Lab</a></footer>''')
        self.assertEqual(labs, [])
        self.assertEqual(patch["email"], "ada@ucsd.edu")
        self.assertTrue(patch["verification"]["identityMatched"])

    def test_wrong_person_page_does_not_supply_fields(self):
        patch, labs = LABS.parse_profile(self.person, self.meta, '<main><h1>Bob Example</h1><p>Collaborator: Ada Example</p><a href="/lab">Bob Lab</a></main>')
        self.assertEqual(patch["verification"]["status"], "identity_not_confirmed")
        self.assertEqual(labs, [])

    def test_drupal_page_layout_class_is_not_a_sidebar(self):
        patch, labs = LABS.parse_profile(self.person, self.meta, '<body class="layout-one-sidebar"><main><h1>Ada Example</h1><a href="/lab">Example Lab</a></main></body>')
        self.assertTrue(patch["verification"]["identityMatched"])
        self.assertEqual(len(labs), 1)

    def test_aspnet_page_form_preserves_profile_content(self):
        patch, labs = LABS.parse_profile(self.person, self.meta, '<body><form id="aspnetForm"><main><h1>Ada Example</h1><a href="mailto:ada@ucsd.edu">ada@ucsd.edu</a><a href="/lab/">Example Lab</a></main></form></body>')
        self.assertEqual(patch["email"], "ada@ucsd.edu")
        self.assertEqual(len(labs), 1)

    def test_profiles_footer_and_bibliography_are_not_personal_research(self):
        markup = '<title>Ada Example | UCSD Profiles</title><body><form><div id="ctl00_divProfilesContentMain"><h1>Ada Example</h1><div id="xPropertyGroupBibliographic"><a href="/bad">Other Author Lab</a></div></div><div id="researcherprofiles--footer-collaboration"><p>UCSD Profiles is managed by the UC San Diego Altman Clinical and Translational Research Institute. We use cookies to analyze our site performance.</p></div></form></body>'
        patch, labs = LABS.parse_profile(self.person, self.meta, markup)
        self.assertNotIn("researchSummary", patch)
        self.assertEqual(labs, [])

    def test_named_lab_and_scholar_links_keep_observation_time(self):
        patch, labs = LABS.parse_profile(self.person, self.meta, '<main><h1>Ada Example</h1><a href="https://ada.ucsd.edu">Example Lab</a><a href="https://scholar.google.com/citations?user=abc">Google Scholar</a></main>')
        self.assertEqual(len(labs), 1)
        self.assertEqual(patch["googleScholarUrl"], "https://scholar.google.com/citations?user=abc")
        self.assertEqual(patch["fieldEvidence"]["labAffiliation"]["observedAt"], self.meta["observedAt"])

    def test_explicit_lab_website_link_is_an_affiliation_not_pi_assertion(self):
        patch, labs = LABS.parse_profile(self.person, self.meta, '<main><h1>Ada Example</h1><a href="https://ada.ucsd.edu/lab/">Lab Website</a></main>')
        self.assertEqual(len(labs), 1)
        self.assertEqual(labs[0]["principalInvestigator"], "Not found")
        self.assertEqual(labs[0]["professorIds"], ["ada"])

    def test_table_cells_do_not_cross_assign_pis(self):
        bob = {"id": "bob", "name": "Bob Other", "department": "Example", "officialProfileUrl": "https://example.ucsd.edu/people/bob"}
        markup = '<main><table><tr><td><a href="/ada-lab">Ada Lab</a> Principal Investigator: <a href="/people/ada">Ada Example</a></td><td><a href="/bob-lab">Bob Lab</a> Principal Investigator: <a href="/people/bob">Bob Other</a></td></tr></table></main>'
        labs = LABS.parse_directory("Example", self.meta, markup, [self.person, bob])
        self.assertEqual(labs[0]["professorIds"], ["ada"])
        self.assertEqual(labs[1]["professorIds"], ["bob"])

    def test_profile_list_card_includes_pi_sibling(self):
        markup = '<main><li class="profile-listing-card"><p><a href="/ada-lab">Ada Lab</a></p><p>Principal Investigator: <a href="/people/ada">Ada Example</a></p></li></main>'
        labs = LABS.parse_directory("Example", self.meta, markup, [self.person])
        self.assertEqual(labs[0]["professorIds"], ["ada"])

    def test_directory_redirect_does_not_make_every_lab_an_affiliation(self):
        links = ''.join(f'<a href="/lab{i}">Example {i} Lab</a>' for i in range(8))
        patch, labs = LABS.parse_profile(self.person, self.meta, '<title>Ada Example</title><main><h1>Ada Example</h1>' + links + '</main>')
        self.assertEqual(labs, [])

    def test_expired_cache_is_not_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            fetcher = LABS.Fetcher(Path(folder), max_cache_age_days=30)
            url = "https://profiles.ucsd.edu/ada.example"
            path = Path(folder) / (hashlib.sha256(url.encode()).hexdigest() + ".json")
            path.write_text(json.dumps({"observedAt": (dt.datetime.now(dt.UTC) - dt.timedelta(days=31)).isoformat()}))
            self.assertFalse(fetcher.cached_fresh(url))
            path.write_text(json.dumps({"observedAt": dt.datetime.now(dt.UTC).isoformat()}))
            self.assertTrue(fetcher.cached_fresh(url))

    def test_verification_date_follows_san_diego_calendar(self):
        self.assertEqual(LABS.observed_date("2026-10-03T00:05:00+00:00"), "2026-10-02")

    def test_slow_budget_advances_past_fresh_cache(self):
        people = [{"id": str(i), "officialProfileUrl": f"https://profiles.ucsd.edu/person.{i}"} for i in range(3)]
        class Cache:
            def __init__(self, count):
                self.count = count
            def cached_fresh(self, url):
                return int(url.rsplit(".", 1)[-1]) < self.count
            def cached_observed_at(self, url):
                return None
        selected, deferred = LABS.select_slow_profiles(people, Cache(1), True, 1)
        self.assertEqual([p["id"] for p in selected], ["0", "1"])
        self.assertEqual(deferred, {"2"})
        selected, deferred = LABS.select_slow_profiles(people, Cache(2), True, 1)
        self.assertEqual([p["id"] for p in selected], ["0", "1", "2"])
        self.assertEqual(deferred, set())

    def test_never_seen_slow_pages_are_not_starved_by_expired_early_pages(self):
        people = [{"id": "a", "officialProfileUrl": "https://profiles.ucsd.edu/stale"}, {"id": "b", "officialProfileUrl": "https://profiles.ucsd.edu/new"}]
        class Cache:
            def cached_fresh(self, url):
                return False
            def cached_observed_at(self, url):
                return dt.datetime(2025, 1, 1, tzinfo=dt.UTC) if url.endswith("stale") else None
        selected, deferred = LABS.select_slow_profiles(people, Cache(), True, 1)
        self.assertEqual([p["id"] for p in selected], ["b"])
        self.assertEqual(deferred, {"a"})

    def test_personal_site_requires_named_lab_and_owner(self):
        meta = {**self.meta, "sourceUrl": "https://example-lab.org/"}
        proof = {"sourceUrl": self.person["officialProfileUrl"]}
        check, _, lab = LABS.parse_personal_site(self.person, meta, '<title>Example Lab</title><main><p>Principal Investigator: Ada Example</p></main>', proof)
        self.assertEqual(check["status"], "verified_lab_site")
        self.assertEqual(lab["principalInvestigator"], "Ada Example")

    def test_personal_site_cannot_assign_another_pi_to_professor(self):
        meta = {**self.meta, "sourceUrl": "https://example-lab.org/"}
        proof = {"sourceUrl": self.person["officialProfileUrl"]}
        check, _, lab = LABS.parse_personal_site(self.person, meta, '<title>Example Lab</title><main><p>Principal Investigator: Bob Other. Alumni: Ada Example</p></main>', proof)
        self.assertEqual(check["status"], "identity_not_confirmed")
        self.assertIsNone(lab)

    def test_verified_personal_homepage_is_not_automatically_a_lab(self):
        meta = {**self.meta, "sourceUrl": "https://example-lab.org/"}
        proof = {"sourceUrl": self.person["officialProfileUrl"]}
        check, _, lab = LABS.parse_personal_site(self.person, meta, '<title>Ada Example</title><main><h1>Ada Example</h1><p>Publications and teaching.</p></main>', proof)
        self.assertEqual(check["status"], "verified_personal_site_not_lab")
        self.assertIsNone(lab)

    def test_papers_and_publication_sections_cannot_become_labs(self):
        markup = '<main><h1>Ada Example</h1><a href="https://urldefense.com/v3/https://doi.org/10.1/x">On Body-Environment Continuities from a Laboratory Commensalism</a><a href="/paper.pdf">Reputation from the Field to the Lab</a><a href="https://lab.ucsd.edu/publications.html">Jiang Lab Publications</a><a href="https://profiles.ucsd.edu/search/default.aspx?searchfor=lab">Research in my laboratory focuses on the structure</a></main>'
        patch, labs = LABS.parse_profile(self.person, self.meta, markup)
        self.assertEqual(labs, [])

    def test_external_university_group_is_not_the_primary_ucsd_lab(self):
        patch, labs = LABS.parse_profile(self.person, self.meta, '<main><h1>Ada Example</h1><a href="https://www.educ.cam.ac.uk/research/groups/">Cambridge Educational Dialogue Research Group</a></main>')
        self.assertEqual(len(labs), 1)
        self.assertEqual(labs[0]["institution"], "University of Cambridge")
        self.assertEqual(patch["labAffiliations"][0]["relationship"], "external_research_group_link")
        self.assertNotIn("labAffiliation", patch)

    def test_news_and_malformed_destinations_are_not_lab_sites(self):
        rejected = [
            "https://ucsdnews.ucsd.edu/feature/lab-receives-awards",
            "https://health.ucsd.edu/news/releases/2024-01-01-lab-grown-blood/",
            "https://www.washingtonpost.com/science/lab-discovery_story.html://",
            "https://www.kusi.com/uc-san-diego-lab-discovery/",
            "https://example.ucsd.edu/news/releases/lab-study",
            "https://example.ucsd.edu/press-releases/new-lab.html",
            "https://example.ucsd.edu/article.html%3A%2F%2F",
            "javascript:alert(1)", "https://example.ucsd.edu:bad/lab/",
        ]
        for url in rejected:
            with self.subTest(url=url):
                self.assertFalse(LABS.is_lab_destination(url))
        for url in ["https://example.ucsd.edu/lab/", "https://health.ucsd.edu/research/labs/ada/", "https://example.org/news-lab/", "https://example.ucsd.edu/research/featured-labs/ada/"]:
            with self.subTest(url=url):
                self.assertTrue(LABS.is_lab_destination(url))

    def test_profile_lab_labels_on_news_links_cannot_create_labs_or_affiliations(self):
        urls = ["https://ucsdnews.ucsd.edu/feature/lab-receives-awards", "https://health.ucsd.edu/news/releases/lab-grown-blood/", "https://www.washingtonpost.com/science/lab-discovery_story.html://", "https://www.kusi.com/uc-san-diego-lab-discovery/"]
        markup = '<main><h1>Ada Example</h1>' + ''.join(f'<a href="{url}">Our Lab Research</a>' for url in urls) + '</main>'
        patch, labs = LABS.parse_profile(self.person, self.meta, markup)
        self.assertEqual(patch["verification"]["status"], "verified")
        self.assertEqual(labs, [])
        self.assertEqual(patch["labAffiliations"], [])
        self.assertNotIn("labAffiliation", patch)


class IncrementalCaptureTests(unittest.TestCase):
    def setUp(self):
        self.old_time = "2026-10-02T12:00:00+00:00"
        self.new_time = "2026-10-03T12:00:00+00:00"
        self.ada = {"id": "ada", "name": "Ada Example", "institution": "University of California San Diego", "department": "Example", "officialProfileUrl": "https://example.ucsd.edu/people/ada"}
        self.cloud = {**self.ada, "id": "cloud", "name": "Cloud Example", "officialProfileUrl": "https://profiles.ucsd.edu/cloud.example"}
        self.proof = {"sourceUrl": self.ada["officialProfileUrl"], "observedAt": self.old_time, "status": "verified", "method": "profile_email", "evidence": "old@ucsd.edu"}
        self.old_patch = {"verification": {"status": "verified", "sourceUrl": self.ada["officialProfileUrl"], "observedAt": self.old_time, "identityMatched": True}, "email": "old@ucsd.edu", "fieldEvidence": {"email": self.proof}, "labAffiliations": []}

    def test_fresh_failure_updates_status_but_keeps_historical_fields(self):
        fresh = {"verification": {"status": "http_error", "sourceUrl": self.ada["officialProfileUrl"], "observedAt": self.new_time, "identityMatched": False}, "fieldEvidence": {}, "labAffiliations": []}
        merged = LABS.merge_profile_observation(self.old_patch, fresh)
        self.assertEqual(merged["verification"]["status"], "http_error")
        self.assertEqual(merged["email"], "old@ucsd.edu")
        self.assertEqual(merged["fieldEvidence"]["email"], self.proof)
        self.assertEqual(merged["verificationHistory"], [self.old_patch["verification"]])
        # No new observation, or an older cache response, cannot degrade a newer
        # cloud result even if the cache's status is a failure.
        for stamp in [None, "2026-09-01T12:00:00Z"]:
            fresh["verification"]["observedAt"] = stamp
            self.assertEqual(LABS.merge_profile_observation(self.old_patch, fresh), self.old_patch)

    def test_new_success_updates_value_with_separate_old_proof(self):
        fresh = copy.deepcopy(self.old_patch)
        fresh["verification"]["observedAt"] = self.new_time
        fresh["email"] = "new@ucsd.edu"
        fresh["fieldEvidence"]["email"].update(observedAt=self.new_time, evidence="new@ucsd.edu")
        merged = LABS.merge_profile_observation(self.old_patch, fresh)
        self.assertEqual(merged["email"], "new@ucsd.edu")
        self.assertEqual(merged["fieldEvidence"]["email"], fresh["fieldEvidence"]["email"])
        self.assertEqual(merged["previousFieldObservations"], [{"field": "email", "value": "old@ucsd.edu", "fieldEvidence": [self.proof]}])
        self.assertEqual(self.old_patch["email"], "old@ucsd.edu")

    def test_profile_refresh_preserves_independent_personal_site_fields(self):
        old = copy.deepcopy(self.old_patch)
        old["researchSummary"] = "Detailed personal-site research"
        old["fieldEvidence"]["researchSummary"] = {**self.proof, "method": "identity_matched_personal_site_research_excerpt"}
        fresh = {"researchSummary": "Short profile bio", "fieldEvidence": {"researchSummary": {**self.proof, "observedAt": self.new_time, "method": "profile_research_excerpt"}}}
        merged = LABS.merge_observed_fields(old, fresh)
        self.assertEqual(merged["researchSummary"], old["researchSummary"])
        self.assertEqual(merged["fieldEvidence"]["researchSummary"], old["fieldEvidence"]["researchSummary"])
        self.assertEqual(merged["additionalProfileObservations"][0]["value"], "Short profile bio")
        # A real subsequent visit to the personal site may update its own field.
        fresh["fieldEvidence"]["researchSummary"]["method"] = "identity_matched_personal_site_research_excerpt"
        self.assertEqual(LABS.merge_observed_fields(old, fresh)["researchSummary"], "Short profile bio")

    def test_generic_profile_link_does_not_rename_a_named_lab_or_drop_link_evidence(self):
        prior = self.capture()
        meta = {"status": "ok", "sourceUrl": self.ada["officialProfileUrl"], "observedAt": self.old_time}
        patch, labs = LABS.parse_profile(self.ada, meta, '<main><h1>Ada Example</h1><a href="https://ada.ucsd.edu/lab/">Cardiovascular Imaging Lab</a></main>')
        prior["byProfessorId"] = {"ada": patch}
        prior["labs"] = labs
        prior["stats"]["professorRecords"] = 1
        meta = {**meta, "observedAt": self.new_time}
        response = (meta, '<main><h1>Ada Example</h1><a href="https://ada.ucsd.edu/lab/">Lab Website</a></main>')
        with tempfile.TemporaryDirectory() as folder:
            output = self.run_capture(folder, [self.ada], prior, {meta["sourceUrl"]: response})
        result = output["byProfessorId"]["ada"]
        self.assertEqual(output["labs"][0]["labName"], "Cardiovascular Imaging Lab")
        self.assertEqual(result["labAffiliation"], "Cardiovascular Imaging Lab")
        self.assertEqual(result["labAffiliations"][0]["labName"], "Cardiovascular Imaging Lab")
        self.assertEqual({p["observedAt"] for p in output["labs"][0]["fieldEvidence"]["labWebsiteUrl"]}, {self.old_time, self.new_time})
        self.assertEqual(output["labs"][0]["additionalLabLinkObservations"][0]["fieldEvidence"][0]["method"], "official_profile_generic_lab_link")

    def test_affiliation_union_preserves_explicit_pi_and_directory_relationships(self):
        meta = {"status": "ok", "sourceUrl": self.ada["officialProfileUrl"], "observedAt": self.new_time}
        fresh, _ = LABS.parse_profile(self.ada, meta, '<main><h1>Ada Example</h1><a href="https://ada.ucsd.edu/lab/">Lab Website</a></main>')
        for relationship in ["personal_site_explicit_pi", "official_directory_same_record"]:
            old = copy.deepcopy(self.old_patch)
            old["labAffiliations"] = [{"labId": "stable", "labName": "Named Lab", "url": "https://ada.ucsd.edu/lab/", "relationship": relationship, "fieldEvidence": {**self.proof, "method": relationship}}]
            merged = LABS.merge_profile_observation(old, fresh)["labAffiliations"][0]
            self.assertEqual(merged["labId"], "stable")
            self.assertEqual(merged["labName"], "Named Lab")
            self.assertEqual(merged["relationship"], relationship)
            self.assertEqual({p["observedAt"] for p in merged["fieldEvidence"]}, {self.old_time, self.new_time})

    def test_generic_upgrade_and_changed_primary_lab_keep_name_url_consistent(self):
        url = "https://ada.ucsd.edu/lab/"
        meta = {"status": "ok", "sourceUrl": self.ada["officialProfileUrl"], "observedAt": self.new_time}
        generic = LABS.make_lab("Lab Website", url, "Example", meta, "Lab Website", self.ada)
        named = LABS.make_lab("Named Lab", url, "Example", {**meta, "observedAt": self.old_time}, "Named Lab", self.ada)
        self.assertEqual(LABS.merge_observed_fields(generic, named)["labName"], "Named Lab")
        # Legacy captures had no generic-specific method; exact generated labels
        # remain upgradeable using the old method and generated suffix.
        generic["fieldEvidence"]["labName"]["method"] = "official_profile_explicit_lab_link"
        self.assertEqual(LABS.merge_observed_fields(generic, named)["labName"], "Named Lab")
        generic["labName"] = "Lab Site"
        self.assertEqual(LABS.merge_observed_fields(generic, named)["labName"], "Named Lab")
        self.assertTrue(LABS.generic_lab_name("Lab Site", LABS.make_lab("Lab Site", url, "Example", meta, "Lab Site", self.ada)["fieldEvidence"]["labName"]))
        old = {"labAffiliation": "Named Lab", "labAffiliationUrl": url, "fieldEvidence": {"labAffiliation": self.proof, "labAffiliationUrl": self.proof}}
        fresh = {"labAffiliation": "Ada Example — lab website", "labAffiliationUrl": "https://new-lab.ucsd.edu/", "fieldEvidence": {"labAffiliation": {**self.proof, "method": "official_profile_generic_lab_link", "observedAt": self.new_time}, "labAffiliationUrl": {**self.proof, "observedAt": self.new_time}}}
        result = LABS.merge_observed_fields(old, fresh)
        self.assertEqual((result["labAffiliation"], result["labAffiliationUrl"]), (fresh["labAffiliation"], fresh["labAffiliationUrl"]))

    def run_capture(self, folder, people, previous, responses, *, directories=None, discovered=None, personal_sites=False):
        source, target = Path(folder) / "atlas.json", Path(folder) / "evidence.json"
        source.write_text(json.dumps({"professors": people}))
        if previous is not None:
            target.write_text(json.dumps(previous))

        class FakeFetcher:
            def __init__(self, *args):
                self.results = {}
            def cached_fresh(self, url):
                return False
            def cached_observed_at(self, url):
                return None
            def fetch(self, url):
                meta, markup = responses[url]
                self.results[url] = meta
                return meta, markup

        args = SimpleNamespace(input=source, out=target, cache=Path(folder) / "cache", timeout=1, delay=0, refresh=False, max_cache_age_days=30, include_slow_profiles=False, slow_profile_limit=0, limit=0, workers=1, personal_sites=personal_sites, personal_site_limit=0)
        with mock.patch.object(LABS, "Fetcher", FakeFetcher), mock.patch.object(LABS, "discover_faculty", return_value=discovered or ([], {}, {})), mock.patch.object(LABS, "directory_seeds", return_value=directories or {}), contextlib.redirect_stdout(io.StringIO()):
            LABS.run(args)
        return json.loads(target.read_text())

    def capture(self):
        return {"schemaVersion": 1, "collectionState": "completed", "labs": [], "professors": [], "directoryListings": {}, "byProfessorId": {}, "personalSiteChecks": [], "fetches": [], "stats": {"professorRecords": 0, "profileAttempts": 500}, "profileBackfill": {"latestRun": {"runState": "completed", "attemptedProfiles": 400}, "previousRuns": [{"attemptedProfiles": 100}]}}

    def test_cold_cache_partial_refresh_preserves_full_cloud_capture_and_runner_compatibility(self):
        prior = self.capture()
        meta = {"status": "ok", "sourceUrl": self.cloud["officialProfileUrl"], "observedAt": self.old_time}
        patch, labs = LABS.parse_profile(self.cloud, meta, '<main><h1>Cloud Example</h1><a href="https://cloud-lab.ucsd.edu/">Cloud Lab</a><a href="mailto:cloud@ucsd.edu">cloud@ucsd.edu</a></main>')
        # Simulate a stable lab ID retained during cloud merging, not the parser's
        # freshly computed ID; rediscovery of the URL must preserve it.
        labs[0]["id"] = "existing-cloud-lab"
        patch["labAffiliations"][0]["labId"] = labs[0]["id"]
        prior["labs"] = labs
        prior["byProfessorId"] = {"cloud": patch, "ada": self.old_patch}
        prior["professors"] = [self.cloud]
        prior["directoryListings"] = {"directory-only": {"facultyStatus": "emeritus", "directorySection": "Emeritus", "evidence": self.proof}}
        prior["personalSiteChecks"] = [{"professorId": "cloud", "sourceUrl": "https://cloud-lab.ucsd.edu/", "status": "verified_lab_site", "observedAt": self.old_time}]
        prior["fetches"] = ["legacy-fetch-reference", {"sourceUrl": meta["sourceUrl"], "status": "ok", "observedAt": self.old_time}]
        prior["stats"]["professorRecords"] = 2
        fresh_meta = {"status": "ok", "sourceUrl": self.ada["officialProfileUrl"], "observedAt": self.new_time}
        responses = {self.ada["officialProfileUrl"]: (fresh_meta, '<main><h1>Ada Example</h1><a href="mailto:new@ucsd.edu">new@ucsd.edu</a><a href="https://cloud-lab.ucsd.edu/">Cloud Lab</a></main>')}
        with tempfile.TemporaryDirectory() as folder:
            # The new input intentionally lacks the previously exported faculty;
            # the prior capture still preserves the full roster and evidence.
            output = self.run_capture(folder, [self.ada], prior, responses, personal_sites=True)
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])
        self.assertEqual(output["byProfessorId"]["cloud"], patch)
        self.assertEqual(output["byProfessorId"]["ada"]["email"], "new@ucsd.edu")
        self.assertEqual(output["labs"][0]["id"], "existing-cloud-lab")
        self.assertEqual(set(output["labs"][0]["professorIds"]), {"cloud", "ada"})
        self.assertEqual(output["byProfessorId"]["ada"]["labAffiliations"][0]["labId"], "existing-cloud-lab")
        self.assertEqual(output["professors"], prior["professors"])
        self.assertEqual(output["directoryListings"], prior["directoryListings"])
        self.assertEqual(output["personalSiteChecks"], prior["personalSiteChecks"])
        self.assertEqual(output["profileBackfill"], prior["profileBackfill"])
        self.assertEqual(output["fetches"][:2], prior["fetches"])
        self.assertEqual(output["stats"]["profileAttempts"], 501)
        self.assertEqual(output["refreshRun"]["completedProfileObservations"], 1)
        self.assertEqual(output["refreshRun"]["slowDeferredProfiles"], 1)
        self.assertEqual(output["collectionState"], "completed")
        # The standalone cloud runner must still accept this as a full capture.
        with mock.patch.dict(sys.modules, {"refresh_labs": LABS}):
            spec = importlib.util.spec_from_file_location("backfill_compat", Path(__file__).resolve().parents[1] / "scripts/run_profile_backfill.py")
            runner = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(runner)
        runner.validate_capture(output)
        self.assertEqual(runner.pending_profiles(output, {"professors": [self.ada, self.cloud]}), ([], [], []))

    def test_run_records_new_failure_without_erasing_cloud_or_personal_evidence(self):
        prior = self.capture()
        prior["byProfessorId"] = {"ada": self.old_patch}
        prior["stats"]["professorRecords"] = 1
        meta = {"status": "http_error", "sourceUrl": self.ada["officialProfileUrl"], "observedAt": self.new_time, "httpStatus": 404}
        with tempfile.TemporaryDirectory() as folder:
            output = self.run_capture(folder, [self.ada], prior, {meta["sourceUrl"]: (meta, "")}, personal_sites=True)
        self.assertEqual(output["byProfessorId"]["ada"]["verification"]["status"], "http_error")
        self.assertEqual(output["byProfessorId"]["ada"]["fieldEvidence"]["email"], self.proof)
        self.assertEqual(output["stats"]["verificationStatuses"], {"http_error": 1})

    def test_first_capture_still_exports_every_record_when_profiles_deferred(self):
        with tempfile.TemporaryDirectory() as folder:
            output = self.run_capture(folder, [self.cloud], None, {})
        self.assertEqual(output["byProfessorId"]["cloud"]["verification"]["status"], "deferred_crawl_delay")
        self.assertEqual(output["stats"]["professorRecords"], 1)
        self.assertEqual(output["stats"]["profileAttempts"], 0)

    def test_unobserved_old_placeholder_can_become_pending_without_losing_directory_evidence(self):
        prior = self.capture()
        prior["byProfessorId"] = {"cloud": {"verification": {"status": "not_attempted", "observedAt": None}, "fieldEvidence": {"name": self.proof}, "labAffiliations": []}}
        prior["stats"]["professorRecords"] = 1
        with tempfile.TemporaryDirectory() as folder:
            output = self.run_capture(folder, [self.cloud], prior, {})
        self.assertEqual(output["byProfessorId"]["cloud"]["verification"]["status"], "deferred_crawl_delay")
        self.assertEqual(output["byProfessorId"]["cloud"]["fieldEvidence"]["name"], self.proof)

    def test_directory_updates_require_newer_evidence_and_do_not_remove_missing_people(self):
        prior = self.capture()
        prior["byProfessorId"] = {"cloud": copy.deepcopy(self.old_patch)}
        prior["byProfessorId"]["cloud"].update(facultyStatus="faculty", directorySection="Faculty")
        prior["byProfessorId"]["cloud"]["fieldEvidence"].update(facultyStatus=self.proof, directorySection=self.proof)
        old_listing = {"facultyStatus": "faculty", "directorySection": "Faculty", "evidence": self.proof}
        prior["directoryListings"] = {"cloud": old_listing, "not-returned": old_listing}
        prior["stats"]["professorRecords"] = 1
        fresh_listing = {"facultyStatus": "emeritus", "directorySection": "Emeritus", "evidence": {**self.proof, "observedAt": self.new_time}}
        for stamp, expected in [(self.new_time, "emeritus"), ("2025-01-01T00:00:00Z", "faculty")]:
            fresh_listing["evidence"]["observedAt"] = stamp
            with tempfile.TemporaryDirectory() as folder:
                output = self.run_capture(folder, [self.cloud], prior, {}, discovered=([], {}, {"cloud": fresh_listing}))
            self.assertEqual(output["directoryListings"]["cloud"]["facultyStatus"], expected)
            self.assertEqual(output["byProfessorId"]["cloud"]["facultyStatus"], expected)
            self.assertEqual(output["directoryListings"]["not-returned"], old_listing)
            self.assertEqual(output["byProfessorId"]["cloud"]["verification"], self.old_patch["verification"])

    def test_atomic_write_failure_leaves_previous_capture_intact(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "capture.json"
            path.write_text(json.dumps(self.capture()))
            original = path.read_bytes()
            with mock.patch.object(LABS.os, "replace", side_effect=OSError("simulated failure")), self.assertRaises(OSError):
                LABS.atomic_capture(path, {"replacement": True})
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])

    def test_invalid_previous_capture_is_rejected_before_any_network_or_write(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "evidence.json"
            path.write_text('{"labs": []}')
            original = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "Refusing to replace"):
                self.run_capture(folder, [self.ada], {"labs": []}, {})
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
