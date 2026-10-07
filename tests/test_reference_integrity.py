"""Canonical IDs must remain valid after captures and aliases are merged."""
import contextlib
import copy
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_data import validate_references


def dataset():
    return {
        "professors": [{"id": "professor-1", "labAffiliations": [{"labId": "lab-1"}]}],
        "labs": [{"id": "lab-1", "professorIds": ["professor-1"]}],
    }


class ReferenceIntegrityTests(unittest.TestCase):
    def assert_invalid(self, data, expected):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            validate_references(data)
        self.assertIn(expected, stderr.getvalue())

    def test_valid_reciprocal_links_are_read_only(self):
        data = dataset()
        original = copy.deepcopy(data)
        validate_references(data)
        self.assertEqual(data, original)

    def test_optional_relationships_and_empty_collections_are_valid(self):
        validate_references({"professors": [{"id": "p"}], "labs": [{"id": "l"}]})
        validate_references({"professors": [], "labs": []})
        validate_references({"professors": [{"id": "p", "labAffiliations": []}], "labs": [{"id": "l", "professorIds": []}]})

    def test_alias_id_must_be_canonicalized_before_publication(self):
        data = dataset()
        data["professors"][0]["aliasIds"] = ["old-professor-id"]
        data["labs"][0]["professorIds"] = ["old-professor-id"]
        self.assert_invalid(data, "references missing professor old-professor-id")

    def test_missing_lab_or_wrong_record_kind_is_rejected(self):
        for lid in ["missing-lab", "professor-1"]:
            with self.subTest(lid=lid):
                data = dataset()
                data["professors"][0]["labAffiliations"][0]["labId"] = lid
                self.assert_invalid(data, "references missing lab")
        data = dataset()
        data["labs"][0]["professorIds"] = ["lab-1"]
        self.assert_invalid(data, "references missing professor")

    def test_professor_id_container_and_elements_are_typed(self):
        for invalid in ["professor-1", {}, None]:
            with self.subTest(container=invalid):
                data = dataset()
                data["labs"][0]["professorIds"] = invalid
                self.assert_invalid(data, "professorIds must be a list")
        for invalid in [1, False, None, "", " ", {}]:
            with self.subTest(element=invalid):
                data = dataset()
                data["labs"][0]["professorIds"] = [invalid]
                self.assert_invalid(data, "entries must be non-empty strings")

    def test_affiliations_require_object_entries_with_lab_id(self):
        for invalid in [{}, None, "lab-1"]:
            with self.subTest(container=invalid):
                data = dataset()
                data["professors"][0]["labAffiliations"] = invalid
                self.assert_invalid(data, "labAffiliations must be a list")
        for invalid in [None, "lab-1", []]:
            with self.subTest(entry=invalid):
                data = dataset()
                data["professors"][0]["labAffiliations"] = [invalid]
                self.assert_invalid(data, "must be an object")
        for invalid in [{}, {"labId": None}, {"labId": False}, {"labId": 1}, {"labId": ""}]:
            with self.subTest(lab_id=invalid):
                data = dataset()
                data["professors"][0]["labAffiliations"] = [invalid]
                self.assert_invalid(data, "labId must be a non-empty string")

    def test_duplicate_or_untyped_target_ids_cannot_hide_ambiguity(self):
        data = dataset()
        data["professors"].append({"id": "professor-1"})
        self.assert_invalid(data, "duplicate professors id")
        data = dataset()
        data["labs"].append({"id": "professor-1"})
        self.assert_invalid(data, "used by both professor and lab")
        data = dataset()
        data["professors"][0]["id"] = 1
        self.assert_invalid(data, "id must be a non-empty string")


if __name__ == "__main__":
    unittest.main()
