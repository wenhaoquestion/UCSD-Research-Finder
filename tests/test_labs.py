import importlib.util
from pathlib import Path
import unittest
import datetime as dt
import hashlib
import json
import tempfile


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


if __name__ == "__main__":
    unittest.main()
