import copy
import sys
import unittest
import tempfile
import subprocess
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rebuild_verified_atlas import build, clean_legacy, attach_evidence, valid_url, consolidate_catalog_duplicates, derive_research_tags, url_key, reject_nonlabs, apply_lab_identity_review, encode_url
from enrich_professor_metadata import likely_same_person
from validate_data import validate_professor
from refresh_real_portal import parse_cards


def professor(pid="p", name="Ada Lovelace", department="Computer Science and Engineering"):
    return {"id": pid, "name": name, "institution": "University of California San Diego", "department": department,
            "officialProfileUrl": "https://cse.ucsd.edu/ada", "personalWebsiteUrl": "http://courses.ucsd.edu/",
            "email": "ctri-support@ucsd.edu", "researchAreas": ["Cryptography"],
            "researchSummary": "Official profile signals research in Cryptography.",
            "googleScholarUrl": "https://cse.ucsd.edu/visiting-scholars", "labAffiliation": "ACTRI",
            "labAffiliationUrl": "https://actri.ucsd.edu", "sourceUrls": ["https://cse.ucsd.edu/ada"],
            "lastVerified": "2026-05-18", "recruitingStatus": "Unknown", "recruitingEvidence": {"text": "", "url": ""}}


def atlas():
    return {"schemaVersion": "2.0.0", "generatedAt": "2026-05-18T00:00:00+00:00", "professors": [professor()], "labs": [],
            "collectionPolicy": {"recruitingClaimsRequireExplicitEvidence": True}}


class QualityTests(unittest.TestCase):
    def test_navigation_contamination_is_quarantined(self):
        data = atlas()
        changes, _ = clean_legacy(data)
        p = data["professors"][0]
        self.assertEqual(p["email"], "Not found")
        self.assertEqual(p["googleScholarUrl"], "Not found")
        self.assertEqual(p["labAffiliationUrl"], "Not found")
        self.assertEqual(p["personalWebsiteUrl"], "Not found")
        self.assertEqual(p["researchAreas"], [])
        self.assertTrue(any(c["previousValue"] == "ctri-support@ucsd.edu" for c in changes))
        self.assertEqual(clean_legacy(data), ([], []))

    def test_fresh_fetch_is_not_whole_record_verification(self):
        data, _, _, _ = build(atlas(), {}, {}, {}, {"generatedAt": "2026-10-02T00:00:00+00:00", "checks": []})
        p = data["professors"][0]
        self.assertEqual(p["lastVerified"], "2026-05-18")
        self.assertEqual(p["verification"]["status"], "legacy_unverified")
        self.assertIsNone(p["ratings"]["rateMyProfessors"]["score"])
        validate_professor(p)

    def test_rebuild_is_idempotent_without_new_capture(self):
        first, *_ = build(atlas(), {}, {}, {}, {})
        second, *_ = build(copy.deepcopy(first), {}, {}, {}, {})
        self.assertEqual(first, second)

    def test_legacy_commands_cannot_overwrite_v3_data(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "protected.json"
            text = json.dumps({"schemaVersion": "3.0.0"})
            path.write_text(text)
            for script in ["collect_research_data.py", "migrate_ucsd_index.py", "enrich_professor_metadata.py"]:
                result = subprocess.run([sys.executable, str(root / "scripts" / script), "--out", str(path)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, script)
                self.assertIn("cannot overwrite", result.stderr)
                self.assertEqual(path.read_text(), text)

    def test_unrelated_profile_names_are_not_matched(self):
        self.assertFalse(likely_same_person("Alan Turing", "Ada Lovelace"))
        self.assertFalse(likely_same_person("Maria A Smith", "Maria B Smith"))
        self.assertTrue(likely_same_person("Ada M Lovelace", "Ada Lovelace"))
        self.assertFalse(likely_same_person("", "Ada Lovelace"))

    def test_ambiguous_teaching_is_not_published_as_verified(self):
        course = {"courseCode": "CSE 100", "term": "Fall 2026", "status": "scheduled", "title": "Algorithms",
                  "sourceUrl": "https://cse.ucsd.edu/schedule", "observedAt": "2026-10-02T00:00:00+00:00", "evidence": "Lovelace", "matchConfidence": "low"}
        data, _, _, _ = build(atlas(), {}, {"byProfessorId": {"p": [course]}}, {}, {})
        self.assertEqual(data["professors"][0]["teaching"]["courses"], [])
        self.assertEqual(len(data["professors"][0]["teaching"]["candidates"]), 1)

    def test_evidence_requires_actual_support_and_is_idempotent(self):
        p = professor()
        e = {"sourceUrl": "https://cse.ucsd.edu/ada", "observedAt": "2026-10-02T00:00:00+00:00", "evidence": "Ada Lovelace", "method": "heading"}
        self.assertTrue(attach_evidence(p, "name", e))
        attach_evidence(p, "name", e)
        self.assertEqual(len(p["fieldEvidence"]["name"]), 1)
        self.assertFalse(attach_evidence(p, "email", {**e, "evidence": ""}))

    def test_malformed_urls_fail(self):
        self.assertFalse(valid_url("https:///ucsd.edu/page"))
        self.assertFalse(valid_url("javascript:alert(1)"))
        self.assertFalse(valid_url("https://ucsd.edu/two words"))
        self.assertTrue(valid_url("https://ucsd.edu/two%20words"))

    def test_url_identity_keeps_person_queries_but_removes_tracking(self):
        self.assertEqual(url_key("https://lab.ucsd.edu/index.html?utm_source=a"), url_key("http://lab.ucsd.edu/"))
        self.assertEqual(url_key("http://muscle.ucsd.edu /"), url_key("https://muscle.ucsd.edu/"))
        self.assertEqual(url_key("http://ucsd.edu/two words"), url_key("http://ucsd.edu/two%20words"))
        self.assertNotEqual(url_key("https://ucsd.edu/profile?id=1"), url_key("https://ucsd.edu/profile?id=2"))

    def test_research_tags_require_sourced_paragraph_and_whole_phrases(self):
        p = professor()
        p["researchSummary"] = "Our main work studies machine learning and social interactions."
        p["researchAreas"] = []
        derive_research_tags(p)
        self.assertEqual(p["researchAreas"], [])
        attach_evidence(p, "researchSummary", {"sourceUrl": p["officialProfileUrl"], "observedAt": "2026-10-02T00:00:00+00:00", "evidence": p["researchSummary"]})
        derive_research_tags(p)
        self.assertEqual(p["researchAreas"], ["Machine learning"])
        p["researchSummary"] = "Our work concerns topology."
        derive_research_tags(p)
        self.assertEqual(p["researchAreas"], [])
        self.assertNotIn("researchAreas", p["fieldEvidence"])

    def test_directory_research_labels_survive_paragraph_tagging(self):
        p = professor()
        p["researchSummary"] = "Our work concerns machine learning."
        p["researchAreasFromDirectory"] = ["Chemical Education"]
        for field in ["researchSummary", "researchAreasFromDirectory"]:
            attach_evidence(p, field, {"sourceUrl": p["officialProfileUrl"], "observedAt": "2026-10-02T00:00:00+00:00", "evidence": "Chemical Education; machine learning"})
        derive_research_tags(p)
        self.assertEqual(p["researchAreas"], ["Chemical Education", "Machine learning"])
        self.assertEqual(len(p["fieldEvidence"]["researchAreas"]), 2)
        derive_research_tags(p)
        self.assertEqual(len(p["fieldEvidence"]["researchAreas"]), 2)

    def test_new_capture_removes_stale_course_and_rating_evidence(self):
        d = atlas()
        p = d["professors"][0]
        p["teaching"] = {"status": "verified", "courses": [{"courseCode": "CSE 100", "term": "Fall 2025"}]}
        e = {"sourceUrl": p["officialProfileUrl"], "observedAt": "2026-10-02T00:00:00+00:00", "evidence": "Old assignment"}
        attach_evidence(p, "teaching", e)
        attach_evidence(p, "ratings.rateMyProfessors", e)
        rating = {"status": "not_found", "score": None}
        result, *_ = build(d, {}, {"byProfessorId": {}}, {"byProfessorId": {"p": {"rateMyProfessors": rating}}}, {})
        p = result["professors"][0]
        self.assertEqual(p["teaching"]["courses"], [])
        self.assertEqual(p["teaching"]["status"], "not_checked")
        self.assertNotIn("teaching", p["fieldEvidence"])
        self.assertNotIn("ratings.rateMyProfessors", p["fieldEvidence"])

    def test_alias_ids_preserve_captured_courses_and_ratings(self):
        d = atlas()
        course = {"courseCode": "CSE 100", "term": "Fall 2026", "sourceUrl": "https://cse.ucsd.edu/ada",
                  "observedAt": "2026-10-02T00:00:00+00:00", "evidence": "Ada Lovelace"}
        rating = {"status": "no_reviews", "score": None, "reviewCount": 0}
        result, *_ = build(d, {"professors": [professor("new-id")]},
                           {"byProfessorId": {"new-id": [course]}},
                           {"byProfessorId": {"new-id": {"rateMyProfessors": rating}}}, {})
        self.assertEqual(len(result["professors"]), 1)
        self.assertEqual(result["professors"][0]["teaching"]["courses"], [course])
        self.assertEqual(result["professors"][0]["ratings"]["rateMyProfessors"], rating)

    def test_paper_with_lab_in_title_cannot_be_lab(self):
        d = atlas()
        p = d["professors"][0]
        p["labAffiliationUrl"] = "https://doi.org/10.1234/test"
        d["labs"] = [{"id": "paper", "labName": "Taking Games to the Lab", "labWebsiteUrl": p["labAffiliationUrl"]}]
        removed = reject_nonlabs(d)
        self.assertEqual(len(removed), 1)
        self.assertEqual(d["labs"], [])
        self.assertEqual(p["labAffiliationUrl"], "Not found")

    def test_news_lab_mentions_are_archived_and_all_relationships_repaired(self):
        # These are the four observed false lab entities in the cloud capture.
        news = [
            ("cres", "Our lab receives three CRES awards", "https://ucsdnews.ucsd.edu/feature/chancellors-research-excellence-scholars-program-launches"),
            ("stem", "New Blood: Lab-Grown Stem Cells Bode Well for Transplants, Aging Research", "https://health.ucsd.edu/news/releases/Pages/2021-08-12-new-blood-lab-grown-stem-cells-bode-well-for-transplants-aging-research.aspx"),
            ("space", "Stem cell research finds a unique lab — the International Space Station", "https://www.washingtonpost.com/science/stem-cells-in-space/2020/12/04/8915f700-2471-11eb-a688-5298ad5d580a_story.html://"),
            ("kusi", "UC San Diego to advance stem cell therapies in new space station lab", "https://www.kusi.com/uc-san-diego-to-advance-stem-cell-therapies-in-new-space-station-lab/"),
        ]
        good_url = "https://real-lab.ucsd.edu/"
        proof = {"sourceUrl": "https://profiles.ucsd.edu/ada", "observedAt": "2026-10-03T01:45:49+00:00", "method": "official_profile_explicit_lab_link", "evidence": "Real Lab"}
        d = atlas()
        d["professors"] = []
        d["labs"] = [{"id": "real", "labName": "Real Lab", "labWebsiteUrl": good_url, "fieldEvidence": {"labName": [proof]}}]
        for index, (lid, title, url) in enumerate(news):
            p = professor(lid)
            e = {**proof, "evidence": f"{title} → {url}"}
            bad = {"id": lid, "labName": title, "labWebsiteUrl": url, "professorIds": [lid], "fieldEvidence": {"labName": [e], "labWebsiteUrl": [e]}, "sourceUrls": [proof["sourceUrl"], url], "lastVerified": "2026-10-02", "extraCapturedMetadata": {"keep": True}}
            d["labs"].append(bad)
            p.update(labAffiliation=title, labAffiliationUrl=url, fieldEvidence={"labAffiliation": [e], "labAffiliationUrl": [e]})
            p["labAffiliations"] = [{"labId": lid, "labName": title, "url": url, "fieldEvidence": e}]
            if index == 0:
                p["labAffiliations"].append({"labId": "real", "labName": "Real Lab", "url": good_url, "fieldEvidence": proof})
            d["professors"].append(p)
        originals = copy.deepcopy(d["labs"])

        removed = reject_nonlabs(d)

        self.assertEqual({r["record"]["id"]: r["record"] for r in removed}, {r["id"]: r for r in originals[1:]})
        self.assertTrue(all(r["reason"] for r in removed))
        self.assertEqual(d["labs"], originals[:1])
        self.assertEqual(d["professors"][0]["labAffiliation"], "Real Lab")
        self.assertEqual(d["professors"][0]["labAffiliationUrl"], good_url)
        self.assertEqual(d["professors"][0]["fieldEvidence"]["labAffiliationUrl"], [proof])
        for p in d["professors"][1:]:
            self.assertEqual(p["labAffiliation"], "Not found")
            self.assertEqual(p["labAffiliationUrl"], "Not found")
            self.assertEqual(p["labAffiliations"], [])
            self.assertNotIn("labAffiliation", p["fieldEvidence"])
            self.assertNotIn("labAffiliationUrl", p["fieldEvidence"])
        surviving_ids = {lab["id"] for lab in d["labs"]}
        self.assertTrue(all(a["labId"] in surviving_ids for p in d["professors"] for a in p["labAffiliations"]))
        self.assertEqual(reject_nonlabs(d), [])

    def test_damaged_url_is_not_saved_as_a_lab_homepage(self):
        d = atlas()
        damaged = "https://example.ucsd.edu/lab.html://"
        p = d["professors"][0]
        p.update(labAffiliation="Example Lab", labAffiliationUrl=damaged)
        p["labAffiliations"] = [{"labId": "damaged", "labName": "Example Lab", "url": damaged}]
        d["labs"] = [{"id": "damaged", "labName": "Example Lab", "labWebsiteUrl": damaged}]
        original = copy.deepcopy(d["labs"][0])
        removed = reject_nonlabs(d)
        self.assertEqual(removed[0]["record"], original)
        self.assertEqual(d["labs"], [])
        self.assertEqual(p["labAffiliations"], [])
        self.assertEqual(p["labAffiliationUrl"], "Not found")

    def test_full_build_normalizes_recaptured_lab_urls_before_classification(self):
        # A normalized canonical record can be overwritten by its raw capture
        # during merge. Exercise that complete ordering, not reject_nonlabs alone.
        urls = {
            "sebat": "https://sebatlab.org /",
            "muscle": "http://muscle.ucsd.edu /",
            "optics": "https://www.ece.ucsd.edu/faculty-research/Ultrafast and Nanoscale Optics Group (Professor Shaya Fainman)",
            "damaged": "https://broken.ucsd.edu/lab%3A%2F%2F",
        }
        d = atlas()
        d["qualityMigrationVersion"] = 1
        raw_labs, affiliations = [], []
        for lid, raw_url in urls.items():
            e = {"sourceUrl": "https://profiles.ucsd.edu/ada", "observedAt": "2026-10-03T01:45:49+00:00", "method": "official_profile_explicit_lab_link", "evidence": f"{lid} Lab → {raw_url}"}
            raw = {"id": lid, "labName": lid + " Lab", "labWebsiteUrl": raw_url,
                   "department": "Bioengineering", "sourceUrls": [e["sourceUrl"], raw_url],
                   "professorIds": ["p"], "fieldEvidence": {"labName": [e], "labWebsiteUrl": [e]}}
            raw_labs.append(raw)
            d["labs"].append({**copy.deepcopy(raw), "labWebsiteUrl": encode_url(raw_url)})
            affiliations.append({"labId": lid, "labName": raw["labName"], "url": raw_url, "fieldEvidence": e})
        d["professors"][0].update(labAffiliation="sebat Lab", labAffiliationUrl=encode_url(urls["sebat"]))
        capture = {"labs": raw_labs, "byProfessorId": {"p": {"labAffiliations": affiliations}}}
        original_capture = copy.deepcopy(capture)

        result, _, _, quarantine = build(d, capture, {}, {}, {})

        self.assertEqual({lab["id"] for lab in result["labs"]}, {"sebat", "muscle", "optics"})
        for lab in result["labs"]:
            self.assertEqual(lab["labWebsiteUrl"], encode_url(urls[lab["id"]]))
        self.assertEqual([row["record"]["id"] for row in quarantine], ["damaged"])
        self.assertEqual(quarantine[0]["record"]["labWebsiteUrl"], urls["damaged"])
        p = result["professors"][0]
        self.assertEqual(p["labAffiliationUrl"], "https://sebatlab.org/")
        self.assertEqual({a["labId"] for a in p["labAffiliations"]}, {"sebat", "muscle", "optics"})
        self.assertTrue(all(a["url"] == encode_url(urls[a["labId"]]) for a in p["labAffiliations"]))
        self.assertEqual(capture, original_capture)

    def test_catalog_duplicate_merge_retains_alias_and_sources(self):
        d = atlas()
        old = professor("catalog")
        old["officialProfileUrl"] = "https://catalog.ucsd.edu/faculty/CSE.html"
        old["sourceUrls"] = [old["officialProfileUrl"]]
        d["professors"].append(old)
        removed = consolidate_catalog_duplicates(d)
        self.assertEqual(len(removed), 1)
        self.assertEqual(len(d["professors"]), 1)
        self.assertIn("catalog", d["professors"][0]["aliasIds"])
        self.assertIn(old["officialProfileUrl"], d["professors"][0]["sourceUrls"])

    def test_reviewed_lab_merge_rejects_institute_url_and_remaps_affiliation(self):
        d = atlas()
        p = d["professors"][0]
        old_url, lab_url = "https://institute.ucsd.edu/", "https://lab.ucsd.edu/"
        d["labs"] = [{"id": rid, "labName": "Ada Lab", "labWebsiteUrl": url, "sourceUrls": [url], "fieldEvidence": {}}
                     for rid, url in [("wrong", old_url), ("right", lab_url)]]
        p["labAffiliationUrl"] = old_url
        p["labAffiliations"] = [{"labId": "wrong", "labName": "Ada Lab", "url": old_url}]
        e = {"sourceUrl": p["officialProfileUrl"], "observedAt": "2026-10-02T00:00:00+00:00", "evidence": "Institute link is a stale directory target; same lab has its own website."}
        review = {"entries": [{"sourceLabId": "wrong", "targetLabId": "right", "action": "merge", "reason": "Same lab, wrong old URL", "evidence": [e], "acceptedAliasUrls": []}]}
        removed = apply_lab_identity_review(d, review)
        self.assertEqual(len(removed), 1)
        self.assertEqual(p["labAffiliations"][0]["labId"], "right")
        self.assertEqual(p["labAffiliationUrl"], lab_url)
        self.assertNotIn(old_url, d["labs"][0]["alternateWebsiteUrls"])
        self.assertIn("wrong", d["labs"][0]["aliasIds"])

    def test_real_card_fields_do_not_pollute_description(self):
        markup = '''<li id="card12_238"><div class="crd--more__header"><h3>Research intern</h3><h4>UC San Diego</h4></div>
        <div><h3>Description</h3><p><div class="fr-view"><p>Study neural circuits.</p></div><div class="grd"><label>Application Procedure</label><p>Contact the lab.</p><label>Affiliation</label><p>UCSD-affiliated</p><label>Is this position paid or unpaid?</label><p>Unpaid</p></div></p></div></li>'''
        r = parse_cards(markup, "2026-10-02T00:00:00+00:00")[0]
        self.assertEqual(r["description"], "Study neural circuits.")
        self.assertEqual(r["applicationProcedure"], "Contact the lab.")
        self.assertEqual(r["detailFields"]["Affiliation"], "UCSD-affiliated")
        self.assertEqual(r["detailFields"]["Is this position paid or unpaid?"], "Unpaid")


if __name__ == "__main__":
    unittest.main()
