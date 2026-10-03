"""Backfill must preserve full captures and resume without transferred HTML."""
import copy
import contextlib
import io
import json
import sys
import tempfile
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_profile_backfill as backfill

STAMP = "2026-10-02T00:00:00+00:00"


def person(pid):
    return {"id": pid, "name": "Alice " + pid.title(), "department": "Medicine", "officialProfileUrl": "https://profiles.ucsd.edu/" + pid}


def proof(text):
    return {"sourceUrl": "https://medicine.ucsd.edu/faculty", "observedAt": STAMP, "evidence": text, "method": "official_directory"}


def fixture():
    capture = {"schemaVersion": 1, "collectionState": "completed", "generatedAt": STAMP, "collectionPolicy": {"preserve": True},
        "byProfessorId": {"p0": {"verification": {"status": "verified"}, "fieldEvidence": {"name": proof("Alice P0")}, "email": "p0@ucsd.edu"}},
        "labs": [{"id": "existing-lab", "labName": "Existing Named Lab", "labWebsiteUrl": "https://lab.ucsd.edu/", "sourceUrls": ["https://medicine.ucsd.edu/faculty"], "professorIds": ["p0"], "fieldEvidence": {"labName": proof("Existing Named Lab")}}],
        "professors": [{"id": "new-directory-person", "name": "New Directory Person", "department": "Medicine"}],
        "directoryListings": {"p0": {"role": "Professor"}}, "personalSiteChecks": [{"professorId": "p0", "status": "verified_lab_site"}],
        "fetches": [{"url": "https://old.example.edu", "status": "old_shape", "custom": [1, 2]}, "legacy-fetch-marker"],
        "stats": {"professorRecords": 3, "profileAttempts": 1, "customCounter": 19}}
    for pid in ["p1", "p2"]:
        capture["byProfessorId"][pid] = {"verification": {"status": backfill.DEFERRED, "sourceUrl": person(pid)["officialProfileUrl"], "observedAt": None},
            "fieldEvidence": {"researchSummary": {**proof("Existing personal-site research"), "method": "identity_matched_personal_site_research_excerpt"}},
            "researchSummary": "Existing personal-site research", "labAffiliations": [], "directorySection": "Affiliated"}
    return capture, {"professors": [person(pid) for pid in ["p0", "p1", "p2"]]}


class FakeFetcher:
    timeout = 0
    def __init__(self, statuses=None):
        self.calls, self.results = [], {}
        self.statuses = statuses or {}

    def fetch(self, url):
        self.calls.append(url)
        pid = url.rsplit("/", 1)[-1]
        status = self.statuses.get(pid, "ok")
        meta = {"sourceUrl": url, "finalUrl": url, "observedAt": STAMP, "status": status}
        if status == "http_error":
            meta["httpStatus"] = 429
        self.results[url] = meta
        body = f'<html><main><h1>Alice {pid.title()}</h1><a href="mailto:{pid}@ucsd.edu">Contact</a><a href="https://lab.ucsd.edu/">Existing Named Lab</a></main></html>'
        return meta, body


def run(capture, atlas, fetcher=None, **kwargs):
    return backfill.process_batch(capture, atlas, fetcher or FakeFetcher(), max_seconds=0, emit=lambda value: None, **kwargs)


class ProfileBackfillTests(unittest.TestCase):
    def test_resume_from_full_evidence_preserves_every_unrelated_result(self):
        capture, atlas = fixture()
        original = copy.deepcopy(capture)
        checkpoints = []
        first_fetcher = FakeFetcher()
        first, summary, code = run(capture, atlas, first_fetcher, maximum=1, persist=lambda full, progress: checkpoints.append(copy.deepcopy(full)))
        self.assertEqual(code, 0)
        self.assertEqual(summary["remainingDeferredProfiles"], 1)
        self.assertEqual(capture, original)
        for field in ["professors", "directoryListings", "personalSiteChecks", "collectionPolicy"]:
            self.assertEqual(first[field], original[field])
        self.assertEqual(first["byProfessorId"]["p0"], original["byProfessorId"]["p0"])
        self.assertEqual(first["byProfessorId"]["p2"], original["byProfessorId"]["p2"])
        self.assertEqual(first["byProfessorId"]["p1"]["researchSummary"], "Existing personal-site research")
        self.assertEqual(first["byProfessorId"]["p1"]["email"], "p1@ucsd.edu")
        self.assertEqual(first["fetches"][:2], original["fetches"])
        self.assertTrue(all(len(c["byProfessorId"]) == 3 for c in checkpoints))
        # A fresh fetcher has no cached HTML or previous in-memory cursor.
        second_fetcher = FakeFetcher()
        second, summary, _ = run(first, atlas, second_fetcher)
        self.assertEqual(second_fetcher.calls, [person("p2")["officialProfileUrl"]])
        self.assertEqual(summary["remainingDeferredProfiles"], 0)
        self.assertEqual(second["stats"]["profileAttempts"], 3)

    def test_existing_lab_ids_and_professor_relationships_are_unioned(self):
        capture, atlas = fixture()
        output, _, _ = run(capture, atlas)
        self.assertEqual(len(output["labs"]), 1)
        self.assertEqual(output["labs"][0]["id"], "existing-lab")
        self.assertEqual(output["labs"][0]["professorIds"], ["p0", "p1", "p2"])
        self.assertEqual(output["byProfessorId"]["p1"]["labAffiliations"][0]["labId"], "existing-lab")

    def test_failed_fetch_retains_prior_fields_and_is_not_still_deferred(self):
        capture, atlas = fixture()
        output, summary, code = run(capture, atlas, FakeFetcher({"p1": "fetch_error"}), maximum=1)
        self.assertEqual(code, 0)
        self.assertEqual(output["byProfessorId"]["p1"]["verification"]["status"], "fetch_error")
        self.assertEqual(output["byProfessorId"]["p1"]["researchSummary"], capture["byProfessorId"]["p1"]["researchSummary"])
        self.assertEqual(summary["failedProfiles"], 1)

    def test_host_block_stops_after_current_record_and_saves_failure(self):
        for status in ["http_error", "robots_denied", "robots_unavailable"]:
            with self.subTest(status=status):
                capture, atlas = fixture()
                fetcher = FakeFetcher({"p1": status})
                output, summary, code = run(capture, atlas, fetcher)
                self.assertEqual(code, 75)
                self.assertEqual(len(fetcher.calls), 1)
                self.assertTrue(summary["hostStopped"])
                self.assertEqual(output["byProfessorId"]["p1"]["verification"]["status"], status)
                self.assertEqual(output["byProfessorId"]["p2"]["verification"]["status"], backfill.DEFERRED)

    def test_budget_and_interruption_leave_unattempted_records_pending(self):
        capture, atlas = fixture()
        fetcher = FakeFetcher()
        output, summary, code = backfill.process_batch(capture, atlas, fetcher, max_seconds=5, emit=lambda value: None)
        self.assertEqual(code, 0)
        self.assertEqual(fetcher.calls, [])
        self.assertEqual(summary["stopReason"], "time_budget")
        self.assertEqual(summary["remainingDeferredProfiles"], 2)
        _, summary, code = run(capture, atlas, stopped=lambda: True)
        self.assertEqual(code, 130)
        self.assertEqual(summary["runState"], "interrupted")

    def test_only_deferred_profile_host_urls_are_eligible(self):
        capture, atlas = fixture()
        capture["byProfessorId"]["p1"]["verification"]["sourceUrl"] = "https://profiles.ucsd.edu.evil.example/alice"
        pending, _, outside = backfill.pending_profiles(capture, atlas)
        self.assertEqual([p["id"] for p in pending], ["p2"])
        self.assertEqual(outside, ["p1"])
        self.assertFalse(backfill.profile_url("https://someone@profiles.ucsd.edu/alice"))
        self.assertFalse(backfill.profile_url("https://profiles.ucsd.edu:8443/alice"))

    def test_missing_roster_identity_is_reported_not_guessed(self):
        capture, atlas = fixture()
        atlas["professors"] = [person("p0")]
        pending, unresolved, _ = backfill.pending_profiles(capture, atlas)
        self.assertEqual(pending, [])
        self.assertEqual(unresolved, ["p1", "p2"])

    def test_partial_baseline_is_rejected_before_any_fetch(self):
        capture, atlas = fixture()
        capture["collectionState"] = "in_progress"
        fetcher = FakeFetcher()
        with self.assertRaisesRegex(ValueError, "completed full capture"):
            run(capture, atlas, fetcher)
        self.assertEqual(fetcher.calls, [])
        capture["collectionState"] = "completed"
        del capture["byProfessorId"]["p2"]
        with self.assertRaisesRegex(ValueError, "full-roster statistics"):
            run(capture, atlas, fetcher)

    def test_new_profile_excerpt_does_not_erase_personal_site_result(self):
        capture, _ = fixture()
        incoming = {"verification": {"status": "verified"}, "researchSummary": "New official profile text", "fieldEvidence": {"researchSummary": proof("New official profile text")}, "labAffiliations": []}
        merged = backfill.merge_profile_patch(capture["byProfessorId"]["p1"], incoming)
        self.assertEqual(merged["researchSummary"], "Existing personal-site research")
        self.assertEqual(merged["additionalProfileObservations"][0]["value"], "New official profile text")

    def test_atomic_write_failure_preserves_previous_full_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.json"
            path.write_text('{"old": true}\n')
            with mock.patch.object(backfill.os, "replace", side_effect=OSError("simulated disk error")), self.assertRaises(OSError):
                backfill.atomic_json(path, {"new": True})
            self.assertEqual(json.loads(path.read_text()), {"old": True})
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_dry_run_cannot_fetch_or_modify_baseline(self):
        capture, atlas = fixture()
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "capture.json"
            roster = Path(directory) / "atlas.json"
            evidence.write_text(json.dumps(capture)); roster.write_text(json.dumps(atlas))
            before = evidence.read_bytes()
            with mock.patch.object(backfill, "ProfileFetcher", side_effect=AssertionError("network construction forbidden")), contextlib.redirect_stdout(io.StringIO()) as stdout:
                code = backfill.main(["--evidence", str(evidence), "--atlas", str(roster), "--dry-run"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["eligibleProfiles"], 2)
            self.assertEqual(evidence.read_bytes(), before)
            self.assertEqual(len(list(Path(directory).iterdir())), 2)

    def test_every_redirect_waits_ten_seconds_and_cannot_change_host(self):
        with tempfile.TemporaryDirectory() as directory:
            fetcher = backfill.ProfileFetcher(Path(directory))
            clock = [0]
            fetcher.interval = backfill.RequestInterval(clock=lambda: clock[0], sleep=lambda seconds: clock.__setitem__(0, clock[0] + seconds))
            headers = Message(); headers["Location"] = "/new-name"
            response = mock.MagicMock(); response.__enter__.return_value = response
            response.read.return_value = b"<h1>Alice</h1>"; response.geturl.return_value = "https://profiles.ucsd.edu/new-name"
            response.status = 200; response.headers = Message(); response.headers["Content-Type"] = "text/html; charset=utf-8"
            request_times = []
            def open_request(request, **kwargs):
                request_times.append(clock[0])
                if len(request_times) == 1:
                    raise urllib.error.HTTPError(request.full_url, 302, "redirect", headers, io.BytesIO())
                return response
            fetcher.opener.open = open_request
            fetcher._request("https://profiles.ucsd.edu/old-name")
            self.assertEqual(request_times, [0, 10])
            headers.replace_header("Location", "https://elsewhere.example/person")
            fetcher.opener.open = mock.Mock(side_effect=urllib.error.HTTPError("https://profiles.ucsd.edu/name", 302, "redirect", headers, io.BytesIO()))
            with self.assertRaisesRegex(ValueError, "outside_ucsd_profiles"):
                fetcher._request("https://profiles.ucsd.edu/name")
            self.assertEqual(fetcher.opener.open.call_count, 1)


if __name__ == "__main__":
    unittest.main()
