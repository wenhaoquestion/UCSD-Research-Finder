#!/usr/bin/env python3
"""Validate the static Research Atlas dataset."""

from __future__ import annotations

import json
import re
import sys
import argparse
import datetime as dt
import urllib.parse
from pathlib import Path
from typing import Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = ROOT / "data" / "research-atlas.json"

URL_RE = re.compile(r"^https?://", re.I)
EMAIL_RE = re.compile(r"^([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|Not found|Unknown)$")
ALLOWED_STATUS = {"Recruiting", "Not recruiting", "Unknown"}
ALLOWED_PROFILE_STATUS = {"confirmed", "candidate_search", "not_found", "blocked", "unavailable"}
ALLOWED_IMPACT_STATUS = {"confirmed", "unavailable_open_data", "not_found", "unknown"}
ALLOWED_COVERAGE_STATUS = {"entity_verified", "overview_only", "needs_source_review"}
MISSING = {"", "Not found", "Unknown"}

PROFESSOR_REQUIRED = {
    "id",
    "name",
    "institution",
    "department",
    "officialProfileUrl",
    "personalWebsiteUrl",
    "email",
    "researchAreas",
    "researchSummary",
    "googleScholarUrl",
    "labAffiliation",
    "recruitingStatus",
    "recruitingEvidence",
    "sourceUrls",
    "lastVerified",
}

LAB_REQUIRED = {
    "id",
    "labName",
    "institution",
    "department",
    "labWebsiteUrl",
    "principalInvestigator",
    "researchAreas",
    "description",
    "contactEmail",
    "recruitingStatus",
    "recruitingEvidence",
    "sourceUrls",
    "lastVerified",
}


def fail(message: str) -> None:
    print(f"validation error: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_fields(kind: str, record: Dict[str, object], required: Iterable[str]) -> None:
    missing = set(required) - set(record)
    if missing:
        fail(f"{kind} {record.get('id', '<unknown>')} missing {sorted(missing)}")


def validate_urlish(record_id: str, field: str, value: str) -> None:
    if value in {"Not found", "Unknown"}:
        return
    if not valid_url(value):
        fail(f"{record_id}.{field} must be http(s) URL or missing marker: {value}")


def validate_sources(record_id: str, source_urls: List[str]) -> None:
    if not isinstance(source_urls, list) or not source_urls:
        fail(f"{record_id} must include at least one source URL")
    for url in source_urls:
        if not valid_url(url):
            fail(f"{record_id} has invalid source URL: {url}")


def validate_recruiting(record_id: str, record: Dict[str, object]) -> None:
    status = record.get("recruitingStatus")
    if status not in ALLOWED_STATUS:
        fail(f"{record_id} has invalid recruitingStatus: {status}")

    evidence = record.get("recruitingEvidence")
    if not isinstance(evidence, dict):
        fail(f"{record_id}.recruitingEvidence must be an object")

    text = str(evidence.get("text", ""))
    url = str(evidence.get("url", ""))
    if status in {"Recruiting", "Not recruiting"}:
        if not text.strip():
            fail(f"{record_id} claims {status} without explicit evidence text")
        if not URL_RE.search(url):
            fail(f"{record_id} claims {status} without evidence URL")
        if url not in record.get("sourceUrls", []):
            fail(f"{record_id} evidence URL must also appear in sourceUrls")


def validate_external_profiles(record_id: str, profiles: object) -> None:
    if not isinstance(profiles, dict):
        fail(f"{record_id}.externalProfiles must be an object")
    for key in ["googleScholar", "linkedin"]:
        profile = profiles.get(key)
        if not isinstance(profile, dict):
            fail(f"{record_id}.externalProfiles.{key} must be an object")
        for field in ["profileUrl", "searchUrl", "status", "sourceUrl", "lastChecked"]:
            if field not in profile:
                fail(f"{record_id}.externalProfiles.{key} missing {field}")
        if profile["status"] not in ALLOWED_PROFILE_STATUS:
            fail(f"{record_id}.externalProfiles.{key}.status is invalid: {profile['status']}")
        for field in ["profileUrl", "searchUrl", "sourceUrl"]:
            validate_urlish(record_id, f"externalProfiles.{key}.{field}", str(profile[field]))


def validate_impact_factor(record_id: str, publication: Dict[str, object]) -> None:
    impact = publication.get("journalImpactFactor")
    if not isinstance(impact, dict):
        fail(f"{record_id}.academicProfile.recentPublications.journalImpactFactor must be an object")
    if impact.get("status") not in ALLOWED_IMPACT_STATUS:
        fail(f"{record_id}.academicProfile.recentPublications.journalImpactFactor.status invalid: {impact.get('status')}")
    for field in ["value", "year", "source", "status"]:
        if field not in impact:
            fail(f"{record_id}.academicProfile.recentPublications.journalImpactFactor missing {field}")


def validate_publication(record_id: str, publication: Dict[str, object]) -> None:
    for field in ["title", "year", "publicationDate", "citationCount", "venue", "url", "source"]:
        if field not in publication:
            fail(f"{record_id}.academicProfile.recentPublications entry missing {field}")
    for field in ["url", "doi", "openAlexUrl", "semanticScholarUrl"]:
        if field in publication:
            validate_urlish(record_id, f"academicProfile.recentPublications.{field}", str(publication[field]))
    validate_impact_factor(record_id, publication)


def validate_metric_sources(record_id: str, academic: Dict[str, object]) -> None:
    sources = academic.get("metricSources", [])
    if not isinstance(sources, list):
        fail(f"{record_id}.academicProfile.metricSources must be a list")
    for source in sources:
        if not isinstance(source, dict):
            fail(f"{record_id}.academicProfile.metricSources entries must be objects")
        if "source" not in source or "url" not in source:
            fail(f"{record_id}.academicProfile.metricSources entries must include source and url")
        validate_urlish(record_id, "academicProfile.metricSources.url", str(source["url"]))


def validate_common(kind: str, record: Dict[str, object]) -> None:
    record_id = str(record.get("id", ""))
    if not record_id:
        fail(f"{kind} record missing id")
    if not str(record.get("institution", "")).strip():
        fail(f"{record_id} missing institution")
    if not str(record.get("department", "")).strip():
        fail(f"{record_id} missing department")

    areas = record.get("researchAreas")
    if not isinstance(areas, list) or not all(isinstance(area, str) and area.strip() for area in areas):
        fail(f"{record_id}.researchAreas must be a list of non-empty strings (empty means unknown)")

    validate_sources(record_id, record.get("sourceUrls", []))
    validate_recruiting(record_id, record)
    if "fieldEvidence" in record:
        validate_evidence(record)
    if record.get("lastVerified"):
        validate_date(record_id + ".lastVerified", record["lastVerified"])


def valid_url(value):
    if not isinstance(value, str) or re.search(r"\s", value):
        return False
    try:
        parsed = urllib.parse.urlsplit(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def validate_date(label, value):
    try:
        date = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        fail(f"{label} must be an ISO date/time")
    if date.date() > dt.datetime.now(dt.timezone.utc).date():
        fail(f"{label} cannot be in the future")


def validate_evidence(record):
    rid = record["id"]
    fields = record["fieldEvidence"]
    if not isinstance(fields, dict):
        fail(f"{rid}.fieldEvidence must be an object")
    for field, items in fields.items():
        if not isinstance(items, list) or not items:
            fail(f"{rid}.fieldEvidence.{field} must be a non-empty list")
        for e in items:
            if not isinstance(e, dict) or not valid_url(e.get("sourceUrl")) or not str(e.get("evidence", "")).strip():
                fail(f"{rid}.{field} evidence requires supporting text and source URL")
            if e["sourceUrl"] not in record["sourceUrls"]:
                fail(f"{rid}.{field} evidence URL missing from sourceUrls")
            validate_date(f"{rid}.{field}.observedAt", e.get("observedAt"))
    v = record.get("verification", {})
    if v.get("status") not in {"source_checked", "needs_review", "unavailable", "legacy_unverified"}:
        fail(f"{rid}: invalid record verification status")
    if v.get("status") == "source_checked" and not fields:
        fail(f"{rid}: source_checked requires field evidence")
    if set(v.get("fieldsVerified", [])) != set(fields):
        fail(f"{rid}: fieldsVerified does not match fieldEvidence")


def validate_teaching_and_ratings(record):
    rid = record["id"]
    teaching = record.get("teaching", {})
    courses = teaching.get("courses", [])
    if not isinstance(courses, list):
        fail(f"{rid}.teaching.courses must be a list")
    for c in courses:
        if not isinstance(c, dict) or not all(c.get(f) for f in ["courseCode", "term", "sourceUrl", "observedAt", "evidence"]):
            fail(f"{rid}: course requires code, term, evidence and timestamp")
        if not valid_url(c["sourceUrl"]) or c["sourceUrl"] not in record["sourceUrls"]:
            fail(f"{rid}: course source missing/invalid")
        if c.get("status") not in {"historical", "scheduled", "undated", "current", "planned", "tentative"}:
            fail(f"{rid}: invalid teaching status")
        if c.get("matchConfidence") == "low" or c.get("verificationStatus") == "needs_review":
            fail(f"{rid}: unconfirmed course identity must remain a candidate")
        validate_date(f"{rid}.teaching.observedAt", c["observedAt"])
    for platform, rating in record.get("ratings", {}).items():
        if rating.get("status") not in {"verified", "no_reviews", "not_checked", "not_found", "unavailable", "needs_review"}:
            fail(f"{rid}.{platform}: invalid rating status")
        score, count = rating.get("score"), rating.get("reviewCount")
        if rating.get("status") == "verified":
            if type(score) not in {int, float} or not 1 <= score <= 5 or rating.get("scale") != 5:
                fail(f"{rid}.{platform}: verified rating requires a score in [1, 5] on scale 5")
            if type(count) is not int or count < 1:
                fail(f"{rid}.{platform}: verified rating requires a positive review count")
            if not valid_url(rating.get("sourceUrl")) or not record.get("fieldEvidence", {}).get("ratings." + platform):
                fail(f"{rid}.{platform}: verified rating requires provenance")
            validate_date(f"{rid}.{platform}.observedAt", rating.get("observedAt"))
        elif score is not None:
            fail(f"{rid}.{platform}: unverified ratings must use null, not zero or a guessed score")


def validate_professor(record: Dict[str, object]) -> None:
    require_fields("professor", record, PROFESSOR_REQUIRED)
    validate_common("professor", record)
    record_id = str(record["id"])
    if not str(record.get("name", "")).strip():
        fail(f"{record_id} missing professor name")
    if "researchKeywords" in record:
        keywords = record["researchKeywords"]
        if not isinstance(keywords, list) or not all(isinstance(k, str) and k.strip() for k in keywords):
            fail(f"{record_id}.researchKeywords must be a list of non-empty strings")
        if keywords and not record.get("fieldEvidence", {}).get("researchKeywords"):
            fail(f"{record_id}.researchKeywords requires field evidence")
    if not str(record.get("researchSummary", "")).strip():
        fail(f"{record_id} missing research summary")
    if not EMAIL_RE.search(str(record.get("email", ""))):
        fail(f"{record_id}.email is invalid")
    for field in ["officialProfileUrl", "personalWebsiteUrl", "googleScholarUrl", "labAffiliationUrl"]:
        if field in record:
            validate_urlish(record_id, field, str(record[field]))
    for field in ["googleScholarSearchUrl", "linkedinSearchUrl", "possibleScholarSourceUrl"]:
        if field in record:
            validate_urlish(record_id, field, str(record[field]))
    # June schema fields: checked when present, not required by schema 3.0 records.
    if "externalProfiles" in record:
        validate_external_profiles(record_id, record.get("externalProfiles"))
    if "fieldEvidence" in record:
        scholar = record.get("googleScholarUrl")
        if scholar not in MISSING and scholar is not None:
            parsed = urllib.parse.urlsplit(scholar)
            if parsed.hostname not in {"scholar.google.com", "scholar.google.ch", "scholar.google.co.uk"} or parsed.path.rstrip("/") != "/citations" or not urllib.parse.parse_qs(parsed.query).get("user"):
                fail(f"{record_id}: Google Scholar profile must identify an author")
        validate_teaching_and_ratings(record)
    academic = record.get("academicProfile")
    if isinstance(academic, dict):
        for field in ["openAlexAuthorId", "openAlexUrl", "semanticScholarUrl"]:
            if field in academic:
                validate_urlish(record_id, f"academicProfile.{field}", str(academic[field]))
        validate_metric_sources(record_id, academic)
        publications = academic.get("recentPublications", [])
        if not isinstance(publications, list):
            fail(f"{record_id}.academicProfile.recentPublications must be a list")
        for publication in publications:
            if not isinstance(publication, dict):
                fail(f"{record_id}.academicProfile.recentPublications entries must be objects")
            validate_publication(record_id, publication)


def validate_lab(record: Dict[str, object]) -> None:
    require_fields("lab", record, LAB_REQUIRED)
    validate_common("lab", record)
    record_id = str(record["id"])
    if not str(record.get("labName", "")).strip():
        fail(f"{record_id} missing lab name")
    if not str(record.get("description", "")).strip():
        fail(f"{record_id} missing description")
    if not EMAIL_RE.search(str(record.get("contactEmail", ""))):
        fail(f"{record_id}.contactEmail is invalid")
    for field in ["labWebsiteUrl", "principalInvestigatorProfileUrl"]:
        if field in record:
            validate_urlish(record_id, field, str(record[field]))
    # June lab coverage fields: checked when present, not required by schema 3.0 records.
    if "coverageStatus" in record:
        if record.get("coverageStatus") not in ALLOWED_COVERAGE_STATUS:
            fail(f"{record_id}.coverageStatus is invalid: {record.get('coverageStatus')}")
        if not str(record.get("entityType", "")).strip():
            fail(f"{record_id}.entityType is required")
        if not str(record.get("discoveryMethod", "")).strip():
            fail(f"{record_id}.discoveryMethod is required")
        if not str(record.get("confidence", "")).strip():
            fail(f"{record_id}.confidence is required")
        if not isinstance(record.get("piCandidates"), list):
            fail(f"{record_id}.piCandidates must be a list")
        validate_urlish(record_id, "overviewSourceUrl", str(record.get("overviewSourceUrl", "")))


def validate_references(data: Dict[str, object]) -> None:
    """Validate canonical professor/lab references after identity consolidation.

    Callers must pass the served records, not capture-side alias IDs. Collections
    without relationship fields remain valid; every declared relationship must
    identify an existing record of the correct kind.
    """
    if not isinstance(data, dict):
        fail("dataset must be an object")
    groups = {}
    for kind in ["professors", "labs"]:
        records = data.get(kind, [])
        if not isinstance(records, list):
            fail(f"dataset.{kind} must be a list")
        ids = set()
        for record in records:
            if not isinstance(record, dict):
                fail(f"dataset.{kind} entries must be objects")
            rid = record.get("id")
            if not isinstance(rid, str) or not rid.strip():
                fail(f"dataset.{kind} record id must be a non-empty string")
            if rid in ids:
                fail(f"duplicate {kind} id {rid}")
            ids.add(rid)
        groups[kind] = ids
    shared = groups["professors"] & groups["labs"]
    if shared:
        fail(f"id used by both professor and lab: {sorted(shared)[0]}")

    for lab in data.get("labs", []):
        if "professorIds" not in lab:
            continue
        ids = lab["professorIds"]
        if not isinstance(ids, list):
            fail(f"{lab['id']}.professorIds must be a list")
        for pid in ids:
            if not isinstance(pid, str) or not pid.strip():
                fail(f"{lab['id']}.professorIds entries must be non-empty strings")
            if pid not in groups["professors"]:
                fail(f"{lab['id']}.professorIds references missing professor {pid}")

    for professor in data.get("professors", []):
        if "labAffiliations" not in professor:
            continue
        affiliations = professor["labAffiliations"]
        if not isinstance(affiliations, list):
            fail(f"{professor['id']}.labAffiliations must be a list")
        for index, affiliation in enumerate(affiliations):
            label = f"{professor['id']}.labAffiliations[{index}]"
            if not isinstance(affiliation, dict):
                fail(f"{label} must be an object")
            lid = affiliation.get("labId")
            if not isinstance(lid, str) or not lid.strip():
                fail(f"{label}.labId must be a non-empty string")
            if lid not in groups["labs"]:
                fail(f"{label}.labId references missing lab {lid}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_path", nargs="?", type=Path, default=DEFAULT_DATA_PATH)
    args = parser.parse_args()

    if not args.data_path.exists():
        fail(f"missing {args.data_path}")

    data = json.loads(args.data_path.read_text(encoding="utf-8"))
    professors = data.get("professors", [])
    labs = data.get("labs", [])
    if not professors and not labs:
        fail("dataset must contain at least one professor or lab")

    seen = set()
    for record in professors:
        validate_professor(record)
        if record["id"] in seen:
            fail(f"duplicate id {record['id']}")
        seen.add(record["id"])

    for record in labs:
        validate_lab(record)
        if record["id"] in seen:
            fail(f"duplicate id {record['id']}")
        seen.add(record["id"])

    validate_references(data)

    policies = data.get("collectionPolicy", {})
    if policies.get("recruitingClaimsRequireExplicitEvidence") is not True:
        fail("collectionPolicy.recruitingClaimsRequireExplicitEvidence must be true")

    print(f"Validated {len(professors)} professors and {len(labs)} labs")


if __name__ == "__main__":
    main()
