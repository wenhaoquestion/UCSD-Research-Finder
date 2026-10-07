"""Regressions for explicit faculty identity and source-field provenance."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import refresh_faculty_directories as faculty


META = {"sourceUrl": "https://example.ucsd.edu/people/faculty", "finalUrl": "https://example.ucsd.edu/people/faculty", "observedAt": "2026-10-02T00:00:00Z", "status": "ok", "sha256": "abc"}


def listing(name="Alice Smith", department="Physics", **fields):
    return {"name": name, "department": department, "profileUrl": "", "namedLinkUrl": "", "email": "", "personalWebsiteUrl": "", "googleScholarUrl": "", "researchAreas": [],
        "listedRole": "Professor", "appointmentStatus": "listed_faculty", "directorySection": "Faculty", "sourceUrl": META["sourceUrl"], "observedAt": META["observedAt"], "evidence": dict(META), **fields}


class FacultyDirectoryTests(unittest.TestCase):
    def test_wrapped_chemistry_name_link_and_plain_email_are_explicit(self):
        source = ("chem", "Chemistry & Biochemistry", META["sourceUrl"], "profile-container", "chemistry")
        rows = faculty.card_records(source, META, '<main><div class="profile-container"><a href="/faculty/profiles/alice-smith"><h3>Alice Smith</h3></a><p>alice@ucsd.edu | 123</p><p>Titles Associate Professor</p></div></main>')
        self.assertEqual(rows[0]["profileUrl"], "https://example.ucsd.edu/faculty/profiles/alice-smith")
        self.assertEqual(rows[0]["email"], "alice@ucsd.edu")

    def test_emeritus_and_affiliate_sections_remain_explicit(self):
        source = ("astro", "Astronomy and Astrophysics", META["sourceUrl"], "profile-listing-card", "astronomy")
        rows = faculty.card_records(source, META, '<main><h1>Emeritus Faculty</h1><li class="profile-listing-card"><p class="h3">Alice Smith</p><p>Professor</p></li><h1>Affiliate Faculty</h1><li class="profile-listing-card"><p class="h3">Bob Smith</p><p>Professor</p></li></main>')
        self.assertEqual([r["appointmentStatus"] for r in rows], ["emeritus", "affiliate"])

    def test_same_department_initial_expansion_needs_unambiguous_full_name(self):
        old = [{"id": "old", "name": "H. Kim", "department": "Structural Engineering"}]
        first = listing("Hyonny Kim", "Structural Engineering")
        second = listing("Hyunsun Kim", "Structural Engineering")
        self.assertEqual(faculty.match_existing(first, old, [first])[0]["id"], "old")
        self.assertIsNone(faculty.match_existing(first, old, [first, second])[0])
        additions, patches, uncertain = faculty.build_evidence([first, second], old)
        self.assertFalse(additions)
        self.assertEqual(len(uncertain), 2)

    def test_matching_does_not_cross_departments_on_initials_or_surname(self):
        old = [{"id": "old", "name": "A. Smith", "department": "Mathematics"}]
        self.assertIsNone(faculty.match_existing(listing("Alice Smith"), old)[0])
        self.assertFalse(faculty.valid_person_name("A. Smith"))
        self.assertFalse(faculty.valid_person_name("Staff Directory"))

    def test_alias_punctuation_and_exact_leading_initial_omission(self):
        self.assertEqual(faculty.identity_name("John O’Quigley"), faculty.identity_name("John O'quigley"))
        self.assertTrue(faculty.legacy_initials_compatible("Thomas Bond", "F. Thomas Bond"))
        self.assertFalse(faculty.legacy_initials_compatible("John Helton", "J. William Helton"))

    def test_known_individual_profile_is_preserved_and_new_fields_have_evidence(self):
        old = {"id": "old", "name": "Alice Smith", "department": "Physics", "officialProfileUrl": "https://cse.ucsd.edu/people/faculty-profiles/alice-smith", "email": "Not found"}
        row = listing(profileUrl="https://jacobsschool.ucsd.edu/faculty/profile?id=123", email="alice@ucsd.edu")
        _, patches, _ = faculty.build_evidence([row], [old])
        self.assertNotIn("officialProfileUrl", patches["old"])
        self.assertEqual(patches["old"]["fieldEvidence"]["email"]["sourceUrl"], META["sourceUrl"])
        additions, _, _ = faculty.build_evidence([row], [])
        self.assertIn("email", additions[0]["fieldEvidence"])
        self.assertIn("officialProfileUrl", additions[0]["fieldEvidence"])

    def test_public_physics_nonfaculty_row_is_excluded(self):
        body = json.dumps([{"first_name": "Alice", "last_name": "Smith", "employee_class": "Academic: Non-Faculty"}, {"first_name": "Bob", "last_name": "Smith", "employee_class": "Academic: Emeriti", "email": "bob@ucsd.edu", "display_title": "Research Professor"}])
        rows = faculty.physics_records(META, body)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["appointmentStatus"], "emeritus")

    def test_public_profile_ids_and_escaped_paths(self):
        self.assertEqual(faculty.profile_identity("https://jacobsschool.ucsd.edu/faculty/profile?id=12"), faculty.profile_identity("https://jacobsschool.ucsd.edu/faculty/faculty_bios/index.sfe?fmp_recid=12"))
        self.assertFalse(faculty.individual_profile("https://jacobsschool.ucsd.edu/faculty/faculty_bios/"))
        self.assertFalse(faculty.individual_profile("https://chemistry.ucsd.edu/faculty/index.shtml"))
        self.assertIn("%20", faculty.safe_link("https://chemistry.ucsd.edu/faculty/profiles/tin yiu-lam"))


if __name__ == "__main__":
    unittest.main()
