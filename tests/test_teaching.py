"""Meaningful regressions for provenance, column boundaries, and identity safety."""
import datetime as dt
import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts/refresh_teaching.py"
spec = importlib.util.spec_from_file_location("refresh_teaching", MODULE)
teaching = importlib.util.module_from_spec(spec)
spec.loader.exec_module(teaching)


class TeachingTests(unittest.TestCase):
    def test_rowspan_does_not_shift_quarters_or_leak_between_tables(self):
        doc = teaching.html_data('''<table><tr><td rowspan="2">MATH 10A</td>
          <td rowspan="2">Calculus</td><td>001</td><td>Fall Teacher</td><td></td><td>Spring Teacher</td></tr>
          <tr><td>002</td><td></td><td>Winter Teacher</td><td></td></tr></table>
          <table><tr><td>New table</td></tr></table>''')
        self.assertEqual(doc.rows[1]["cells"], ["MATH 10A", "Calculus", "002", "", "Winter Teacher", ""])
        self.assertEqual(doc.rows[2]["cells"], ["New table"])

    def test_scripts_cannot_become_course_titles(self):
        doc = teaching.html_data('<table><tr><td>ECE 17<style>malformed css</style> Object-Oriented Programming</td></tr></table>')
        self.assertEqual(doc.rows[0]["cells"][0], "ECE 17 Object-Oriented Programming")

    def test_unknown_instructors_and_section_labels_are_not_people(self):
        self.assertEqual(teaching.instructor_names("001: Bussey, T; 002: TBD; 003: Bussey, T"), ["Bussey, T"])
        self.assertEqual(teaching.instructor_names("Yang (Primary), Bal (Secondary)", comma_separated=True), ["Yang", "Bal"])
        self.assertEqual(teaching.instructor_names("Staff, Staff"), [])

    def test_ambiguous_surnames_and_cross_department_names_stay_unmatched(self):
        professors = [
            {"id": "1", "name": "Alice Smith", "department": "Physics"},
            {"id": "2", "name": "Alan Smith", "department": "Physics"},
            {"id": "3", "name": "Alice Smith", "department": "Mathematics"},
        ]
        matches, status, candidates = teaching.matching_professors("Smith", "Physics", professors)
        self.assertFalse(matches)
        self.assertEqual(status, "ambiguous")
        self.assertEqual(candidates, ["1", "2"])
        self.assertFalse(teaching.matching_professors("A. Smith", "Physics", professors)[0])
        self.assertEqual([p["id"] for p in teaching.matching_professors("Alice Smith", "Physics", professors)[0]], ["1"])
        self.assertFalse(teaching.matching_professors("Alice Smith", "Chemistry", professors)[0])

    def test_surname_only_link_is_not_verified(self):
        record = {"courseCode": "MATH 1", "title": "Title", "term": "Fall 2026", "instructorName": "Smith", "sourceId": "one", "department": "Mathematics"}
        linked, unmatched = teaching.bind([record], [{"id": "1", "name": "Alice Smith", "department": "Mathematics"}])
        self.assertEqual(linked["1"][0]["verificationStatus"], "needs_review")
        self.assertEqual(linked["1"][0]["matchConfidence"], "low")

    def test_cross_listing_requires_observed_directory_evidence(self):
        professor = {"id": "1", "name": "Kam Arnold", "department": "Physics", "departmentAffiliations": ["Astronomy and Astrophysics"]}
        self.assertFalse(teaching.matching_professors("Kam Arnold", "Astronomy and Astrophysics", [professor])[0])
        professor["directoryListings"] = [{"department": "Astronomy and Astrophysics", "sourceUrl": "https://astro.ucsd.edu/people/faculty/index.html", "observedAt": "2026-10-02T00:00:00Z"}]
        record = {"courseCode": "ASTR 1", "title": "Astronomy", "term": "Fall 2026", "instructorName": "Arnold", "sourceId": "astro", "department": "Astronomy and Astrophysics"}
        linked, _ = teaching.bind([record], [professor])
        self.assertEqual(linked["1"][0]["matchMethod"], "unique_surname_same_department_documented_affiliation")
        self.assertEqual(linked["1"][0]["verificationStatus"], "needs_review")

    def test_catalog_and_availability_tables_cannot_prove_teaching(self):
        body = '<p class="course-name">MATH 10A. Calculus (4)</p>'
        for parser in ["titles_only", "no_instructors"]:
            source = {"parser": parser}
            self.assertEqual(teaching.parse_source(source, body, {}, dt.date(2026, 10, 2), {}), [])

    def test_csv_uses_explicit_assignment_and_catalog_only_for_title(self):
        source = {"parser": "csv", "termCols": [1, 2, 3], "id": "cogs", "department": "Cognitive Science", "url": "https://example.edu/schedule", "titleSourceId": "cogs-catalog"}
        rows = teaching.parse_source(source, "Course,Fall 2026,Winter 2027,Spring 2027\nCOGS 001,Alice Smith,,Staff\nCOGS 002,,,", {"observedAt": "2026-10-02T00:00:00Z"}, dt.date(2026, 10, 2), {"COGS 1": "Introduction"})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["courseCode"], "COGS 1")
        self.assertEqual(rows[0]["title"], "Introduction")
        self.assertEqual(rows[0]["status"], "scheduled")
        self.assertEqual(rows[0]["assignmentBasis"], "advertised_department_schedule")

    def test_term_status_does_not_call_future_teaching_historical(self):
        self.assertEqual(teaching.term_status("Spring 2026", dt.date(2026, 10, 2)), "historical")
        self.assertEqual(teaching.term_status("Winter 2027", dt.date(2026, 10, 2)), "scheduled")
        self.assertEqual(teaching.term_status(None, dt.date(2026, 10, 2)), "undated")

    def test_rollover_schedule_cannot_silently_keep_old_terms(self):
        source = {"parser": "csv", "termCols": [1, 2, 3]}
        with self.assertRaisesRegex(ValueError, "term headers changed"):
            teaching.parse_source(source, "Course,Fall 2027,Winter 2028,Spring 2028\nCOGS 1,Alice Smith,,", {}, dt.date(2026, 10, 2), {})

    def test_pdf_table_retains_empty_quarter_cells(self):
        import json
        source = {"parser": "pdf_tables", "id": "soc", "department": "Sociology", "url": "https://example.edu/schedule.pdf"}
        rows = teaching.parse_source(source, json.dumps([[["2", "The Study of Society", "4", "", "Estefan", "Payne"]]]), {"observedAt": "2026-10-02T00:00:00Z"}, dt.date(2026, 10, 2), {})
        self.assertEqual([(r["term"], r["instructorName"]) for r in rows], [("Winter 2027", "Estefan"), ("Spring 2027", "Payne")])


if __name__ == "__main__":
    unittest.main()
