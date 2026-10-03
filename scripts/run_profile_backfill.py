#!/usr/bin/env python3
"""Resume only deferred UCSD Profiles observations in a complete lab capture.

The full evidence JSON is the resume state. Every completed record atomically
replaces --out, preserving all unrelated records, faculty exports, directory
observations and personal-site checks. No prior HTML cache is required. When
--out differs from --evidence, use the previous --out as the next --evidence.
The small checkpoint/progress files are informative, never a source of records.

Exit 0: batch complete, budget exhausted, or no eligible profiles. Exit 75:
HTTP 429 or unavailable/disallowed robots stopped the whole host; preserve the
checkpoint and stop subsequent batches. Rebuild/validation/publication belong
to the calling workflow and are deliberately not performed here.
"""
from __future__ import annotations

import argparse
import collections
import copy
import datetime as dt
import fcntl
import hashlib
import json
import os
import signal
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from refresh_labs import Fetcher, UA, canonical_url, now, parse_profile

ROOT = Path(__file__).resolve().parents[1]
HOST = "profiles.ucsd.edu"
DEFERRED = "deferred_crawl_delay"
HOST_STOP_STATUSES = {"robots_denied", "robots_unavailable"}


def profile_url(url):
    if not isinstance(url, str):
        return ""
    try:
        url = canonical_url(url)
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme == "https" and parsed.hostname == HOST and not parsed.username and not parsed.password and parsed.port in {None, 443}:
            return url
    except ValueError:
        pass
    return ""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class RequestInterval:
    """Space every wire request, including robots and redirects, by >=10s."""
    def __init__(self, seconds=10, clock=time.monotonic, sleep=time.sleep):
        self.seconds = max(10, seconds)
        self.clock, self.sleep, self.last = clock, sleep, None

    def wait(self):
        if self.last is not None:
            remaining = self.seconds - (self.clock() - self.last)
            if remaining > 0:
                self.sleep(remaining)
        self.last = self.clock()


class ProfileFetcher(Fetcher):
    """Shared robots/cache handling with strict serialized profile-host I/O."""
    def __init__(self, cache, timeout=25):
        super().__init__(cache, timeout=timeout, delay=10, refresh=False, max_cache_age_days=30)
        self.interval = RequestInterval()
        self.opener = urllib.request.build_opener(NoRedirect())
        self.wire_requests = 0

    def _request(self, url, max_bytes=1_500_000):
        # Redirects are followed manually so urllib cannot issue an unthrottled
        # follow-up request or leave the authorized host.
        current = profile_url(url)
        if not current:
            raise ValueError("outside_ucsd_profiles_host")
        for _ in range(6):
            self.interval.wait()
            self.wire_requests += 1
            request = urllib.request.Request(current, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"})
            try:
                with self.opener.open(request, timeout=self.timeout) as response:
                    payload = response.read(max_bytes + 1)
                    if len(payload) > max_bytes:
                        raise ValueError("response_exceeds_size_limit")
                    return payload.decode(response.headers.get_content_charset() or "utf-8", "replace"), response.geturl(), response.status, response.headers.get("Content-Type", "")
            except urllib.error.HTTPError as error:
                if error.code not in {301, 302, 303, 307, 308} or not error.headers.get("Location"):
                    raise
                target = profile_url(urllib.parse.urljoin(current, error.headers["Location"]))
                error.close()
                if not target:
                    raise ValueError("redirect_outside_ucsd_profiles_host")
                current = target
        raise ValueError("too_many_profile_redirects")


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def unique(items):
    seen, result = set(), []
    for item in items:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            result.append(copy.deepcopy(item))
    return result


def evidence_list(value):
    return value if isinstance(value, list) else [value] if isinstance(value, dict) else []


def has_value(value):
    return value is not None and value not in ("", "Unknown", "Not found", [])


def url_identity(url):
    return canonical_url(url).rstrip("/")


def merge_profile_patch(previous, incoming):
    """Retain older independent evidence; only successful fields may change."""
    merged = copy.deepcopy(previous)
    merged["verification"] = copy.deepcopy(incoming["verification"])
    if incoming["verification"].get("status") != "verified":
        return merged
    fields = merged.setdefault("fieldEvidence", {})
    for field, proof in incoming.get("fieldEvidence", {}).items():
        fresh_proof = evidence_list(proof)
        old_proof = evidence_list(fields.get(field))
        if field not in incoming:
            fields[field] = unique(old_proof + fresh_proof)
            continue
        value = incoming[field]
        if not has_value(value):
            continue
        # Preserve already-verified personal-site excerpts/Scholar findings.
        # Store the profile's additional observation without discarding either.
        personal_proof = any("personal_site" in e.get("method", "") for e in old_proof)
        if personal_proof and field in {"researchSummary", "googleScholarUrl"} and has_value(merged.get(field)) and merged[field] != value:
            merged.setdefault("additionalProfileObservations", []).append({"field": field, "value": value, "fieldEvidence": fresh_proof})
            continue
        if has_value(merged.get(field)) and merged[field] != value:
            merged.setdefault("previousFieldObservations", []).append({"field": field, "value": copy.deepcopy(merged[field]), "fieldEvidence": old_proof})
            fields[field] = copy.deepcopy(fresh_proof)
        else:
            fields[field] = unique(old_proof + fresh_proof)
        merged[field] = copy.deepcopy(value)
    affiliations = merged.setdefault("labAffiliations", [])
    existing_urls = {url_identity(a["url"]) for a in affiliations}
    for affiliation in incoming.get("labAffiliations", []):
        if url_identity(affiliation["url"]) not in existing_urls:
            affiliations.append(copy.deepcopy(affiliation))
            existing_urls.add(url_identity(affiliation["url"]))
    return merged


def merge_labs(output, additions):
    """Union relationships while keeping established lab IDs and labels."""
    by_url = {url_identity(lab["labWebsiteUrl"]): lab for lab in output["labs"]}
    for fresh in additions:
        key = url_identity(fresh["labWebsiteUrl"])
        old = by_url.get(key)
        if old is None:
            old = copy.deepcopy(fresh)
            output["labs"].append(old)
            by_url[key] = old
            continue
        for field in ["sourceUrls", "professorIds", "relatedProfessorNames"]:
            old[field] = unique(old.get(field, []) + fresh.get(field, []))
        fields = old.setdefault("fieldEvidence", {})
        for field, proof in fresh.get("fieldEvidence", {}).items():
            if not has_value(old.get(field)):
                old[field] = copy.deepcopy(fresh.get(field))
                fields[field] = copy.deepcopy(proof)
            elif old.get(field) == fresh.get(field):
                fields[field] = unique(evidence_list(fields.get(field)) + evidence_list(proof))
    return {url: lab["id"] for url, lab in by_url.items()}


def pending_profiles(capture, atlas):
    people = {}
    for person in atlas.get("professors", []) + capture.get("professors", []):
        people.setdefault(person["id"], person)
    aliases = collections.defaultdict(list)
    for person in people.values():
        for alias in person.get("aliasIds", []):
            aliases[alias].append(person)
    selected, unresolved, outside = [], [], []
    for pid, patch in sorted(capture["byProfessorId"].items()):
        verification = patch.get("verification", {})
        if verification.get("status") != DEFERRED:
            continue
        url = profile_url(verification.get("sourceUrl", ""))
        if not url or urllib.parse.urlsplit(url).path in {"", "/", "/robots.txt"}:
            outside.append(pid)
            continue
        person = people.get(pid)
        if person is None and len(aliases.get(pid, [])) == 1:
            person = aliases[pid][0]
        if not person or not all(person.get(k) for k in ["name", "department"]):
            unresolved.append(pid)
            continue
        # Keep the capture-side ID; the builder already resolves canonical IDs.
        selected.append({**person, "id": pid, "officialProfileUrl": url})
    return selected, unresolved, outside


def validate_capture(capture):
    if capture.get("collectionState") != "completed":
        raise ValueError("--evidence must be a completed full capture, not an in-progress/subset run")
    for key, kind in [("byProfessorId", dict), ("labs", list), ("professors", list), ("fetches", list), ("personalSiteChecks", list), ("directoryListings", dict)]:
        if not isinstance(capture.get(key), kind):
            raise ValueError(f"full capture requires {key} as {kind.__name__}")
    expected = capture.get("stats", {}).get("professorRecords")
    if type(expected) is int and expected > len(capture["byProfessorId"]):
        raise ValueError("capture is missing professor records declared by its full-roster statistics")


def update_stats(output):
    stats = output.setdefault("stats", {})
    stats.update(professorsProcessed=len(output["byProfessorId"]),
        verificationStatuses=dict(collections.Counter(p.get("verification", {}).get("status", "unknown") for p in output["byProfessorId"].values())),
        labs=len(output["labs"]), labsWithProfessorMatch=sum(bool(l.get("professorIds")) for l in output["labs"]),
        fetchStatuses=dict(collections.Counter(f.get("status", "unknown") for f in output["fetches"] if isinstance(f, dict))))


def process_batch(capture, atlas, fetcher, *, maximum=500, max_seconds=5700, persist=None, emit=print, clock=time.monotonic, stopped=lambda: False):
    """Pure merge boundaries and injectable I/O make resume/failure testable."""
    validate_capture(capture)
    output = copy.deepcopy(capture)
    pending, unresolved, outside = pending_profiles(output, atlas)
    chosen = pending[:maximum]
    start = clock()
    summary = {"schemaVersion": 1, "startedAt": now(), "updatedAt": now(), "runState": "in_progress", "eligibleAtStart": len(pending),
        "selectedProfiles": len(chosen), "attemptedProfiles": 0, "verifiedProfiles": 0, "failedProfiles": 0, "identityNotConfirmedProfiles": 0,
        "remainingDeferredProfiles": len(pending), "unresolvedProfessorIds": unresolved, "outsideProfileHostIds": outside,
        "maxProfiles": maximum, "maxSeconds": max_seconds, "crawlDelaySeconds": 10, "hostStopped": False, "stopReason": None, "attemptedProfessorIds": []}
    run_history = copy.deepcopy(output.get("profileBackfill", {}).get("previousRuns", []))
    previous_run = output.get("profileBackfill", {}).get("latestRun")
    if previous_run:
        run_history.append({k: v for k, v in previous_run.items() if k != "attemptedProfessorIds"})
    baseline_attempts = output.get("stats", {}).get("profileAttempts", 0)

    def save():
        summary["updatedAt"] = now()
        summary["elapsedSeconds"] = round(clock() - start, 3)
        summary["remainingDeferredProfiles"] = len(pending_profiles(output, atlas)[0])
        summary["wireRequests"] = getattr(fetcher, "wire_requests", None)
        output["generatedAt"] = summary["updatedAt"]
        output["profileBackfill"] = {"latestRun": copy.deepcopy(summary), "previousRuns": run_history}
        output.setdefault("stats", {})["profileAttempts"] = baseline_attempts + summary["attemptedProfiles"]
        update_stats(output)
        if persist:
            persist(output, summary)

    emit(json.dumps({"event": "started", **summary}, ensure_ascii=False))
    save()
    for person in chosen:
        # Leave enough time for the next request and its mandatory host delay.
        if stopped():
            summary["stopReason"] = "interrupted"
            break
        if max_seconds and clock() - start + 10 + getattr(fetcher, "timeout", 25) >= max_seconds:
            summary["stopReason"] = "time_budget"
            break
        try:
            meta, markup = fetcher.fetch(person["officialProfileUrl"])
            try:
                patch, labs = parse_profile(person, meta, markup)
            except Exception as error:
                patch, labs = {"verification": {"status": "parse_error", "sourceUrl": meta["sourceUrl"], "observedAt": meta["observedAt"], "identityMatched": False, "error": str(error)[:300]}, "fieldEvidence": {}, "labAffiliations": []}, []
        except KeyboardInterrupt:
            summary["stopReason"] = "interrupted"
            break
        except Exception as error:
            meta = {"sourceUrl": person["officialProfileUrl"], "observedAt": now(), "status": "fetch_error", "error": str(error)[:300]}
            patch, labs = parse_profile(person, meta, "")
        pid = person["id"]
        output["byProfessorId"][pid] = merge_profile_patch(output["byProfessorId"][pid], patch)
        lab_ids = merge_labs(output, labs)
        for affiliation in output["byProfessorId"][pid].get("labAffiliations", []):
            target = lab_ids.get(url_identity(affiliation["url"]))
            if target:
                affiliation["labId"] = target
        # Never coerce or replace heterogeneous legacy fetch entries.
        fetched = list(getattr(fetcher, "results", {}).values())
        output["fetches"] = unique(output["fetches"] + fetched + [meta])
        summary["attemptedProfiles"] += 1
        summary["attemptedProfessorIds"].append(pid)
        state = patch["verification"]["status"]
        if state == "verified":
            summary["verifiedProfiles"] += 1
        elif state == "identity_not_confirmed":
            summary["identityNotConfirmedProfiles"] += 1
        else:
            summary["failedProfiles"] += 1
        if meta.get("status") in HOST_STOP_STATUSES or meta.get("httpStatus") == 429:
            summary.update(hostStopped=True, stopReason="http_429" if meta.get("httpStatus") == 429 else meta["status"])
        save()
        if summary["attemptedProfiles"] == 1 or summary["attemptedProfiles"] % 25 == 0:
            emit(json.dumps({"event": "progress", **summary}, ensure_ascii=False))
        if summary["hostStopped"]:
            break
    summary["stopReason"] = summary["stopReason"] or ("batch_limit" if len(pending) > len(chosen) else "no_eligible_profiles" if not chosen else "batch_complete")
    summary["runState"] = "host_stopped" if summary["hostStopped"] else "interrupted" if summary["stopReason"] == "interrupted" else "completed"
    save()
    emit(json.dumps({"event": "finished", **summary}, ensure_ascii=False))
    return output, summary, 75 if summary["hostStopped"] else 130 if summary["runState"] == "interrupted" else 0


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--atlas", type=Path, default=ROOT / "data/research-atlas.json")
    cli.add_argument("--evidence", type=Path, default=ROOT / "data/ucsd/lab-evidence.json", help="Full completed baseline or previous full checkpoint")
    cli.add_argument("--out", type=Path, help="Full merged capture; defaults to --evidence")
    cli.add_argument("--checkpoint", type=Path, help="Small resume summary; defaults beside --out")
    cli.add_argument("--progress", type=Path, help="Machine-readable progress; defaults beside --out")
    cli.add_argument("--cache", type=Path, default=Path(tempfile.gettempdir()) / "ucsd-profile-backfill-cache")
    cli.add_argument("--max-profiles", type=int, default=500)
    cli.add_argument("--max-seconds", type=float, default=5700, help="Wall-clock budget; 0 disables the budget")
    cli.add_argument("--timeout", type=float, default=25)
    cli.add_argument("--dry-run", action="store_true", help="Count eligible records without network or file changes")
    args = cli.parse_args(argv)
    if args.max_profiles < 1 or args.max_seconds < 0 or args.timeout <= 0:
        cli.error("max-profiles and timeout must be positive; max-seconds must be non-negative")
    args.out = args.out or args.evidence
    args.checkpoint = args.checkpoint or args.out.with_name("profile-backfill-checkpoint.json")
    args.progress = args.progress or args.out.with_name("profile-backfill-progress.json")
    paths = [args.out.resolve(), args.checkpoint.resolve(), args.progress.resolve()]
    if len(set(paths)) != 3 or args.atlas.resolve() in paths or args.evidence.resolve() in paths[1:]:
        cli.error("atlas, evidence output, checkpoint and progress paths must not overwrite one another")
    capture = json.loads(args.evidence.read_text())
    atlas = json.loads(args.atlas.read_text())
    validate_capture(capture)
    if args.dry_run:
        pending, unresolved, outside = pending_profiles(capture, atlas)
        print(json.dumps({"dryRun": True, "eligibleProfiles": len(pending), "selectedProfiles": min(args.max_profiles, len(pending)), "unresolvedProfessorIds": unresolved,
            "outsideProfileHostIds": outside, "estimatedMinimumBatchSeconds": min(args.max_profiles, len(pending)) * 10,
            "fullCaptureProfessorIds": len(capture["byProfessorId"]), "output": str(args.out)}, ensure_ascii=False, indent=2))
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)
    lock_directory = Path(tempfile.gettempdir()) / "ucsd-profile-backfill-locks"
    lock_directory.mkdir(parents=True, exist_ok=True)
    lock_path = lock_directory / (hashlib.sha256(str(args.out.resolve()).encode()).hexdigest() + ".lock")
    with lock_path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            cli.error("another backfill process is writing this output")
        # Read after acquiring the lock, so a prior writer cannot make the
        # in-memory baseline stale between the initial read and first save.
        capture = json.loads(args.evidence.read_text())
        stop = [False]
        def stop_signal(signum, frame):
            stop[0] = True
        old_handlers = {s: signal.signal(s, stop_signal) for s in [signal.SIGINT, signal.SIGTERM]}
        def persist(output, summary):
            atomic_json(args.out, output)
            atomic_json(args.checkpoint, {**summary, "evidencePath": str(args.out), "resumeInstruction": "Use evidencePath as --evidence; completed statuses in the full capture determine what remains."})
            atomic_json(args.progress, {k: v for k, v in summary.items() if k != "attemptedProfessorIds"})
        try:
            _, _, code = process_batch(capture, atlas, ProfileFetcher(args.cache, args.timeout), maximum=args.max_profiles,
                max_seconds=args.max_seconds, persist=persist, emit=lambda value: print(value, flush=True), stopped=lambda: stop[0])
            return code
        finally:
            for s, handler in old_handlers.items():
                signal.signal(s, handler)


if __name__ == "__main__":
    sys.exit(main())
