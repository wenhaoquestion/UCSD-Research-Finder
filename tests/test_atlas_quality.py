import copy
import sys
import unittest
import tempfile
import subprocess
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rebuild_verified_atlas import build, clean_legacy, attach_evidence, valid_url, consolidate_catalog_duplicates, derive_research_tags, url_key, reject_nonlabs, apply_lab_identity_review
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
