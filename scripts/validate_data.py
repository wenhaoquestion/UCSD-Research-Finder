#!/usr/bin/env python3
"""Validate the static Research Atlas dataset."""

from __future__ import annotations

import json
import re
import sys
import argparse
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
    "externalProfiles",
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
    "entityType",
    "coverageStatus",
    "discoveryMethod",
    "confidence",
    "piCandidates",
    "overviewSourceUrl",
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
    if not URL_RE.search(value):
        fail(f"{record_id}.{field} must be http(s) URL or missing marker: {value}")


def validate_sources(record_id: str, source_urls: List[str]) -> None:
    if not source_urls:
        fail(f"{record_id} must include at least one source URL")
    for url in source_urls:
        if not URL_RE.search(url):
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
    if not isinstance(areas, list) or not areas or not all(str(area).strip() for area in areas):
        fail(f"{record_id}.researchAreas must be a non-empty list")

    validate_sources(record_id, record.get("sourceUrls", []))
    validate_recruiting(record_id, record)


def validate_professor(record: Dict[str, object]) -> None:
    require_fields("professor", record, PROFESSOR_REQUIRED)
    validate_common("professor", record)
    record_id = str(record["id"])
    if not str(record.get("name", "")).strip():
        fail(f"{record_id} missing professor name")
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
    validate_external_profiles(record_id, record.get("externalProfiles"))
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

    policies = data.get("collectionPolicy", {})
    if policies.get("recruitingClaimsRequireExplicitEvidence") is not True:
        fail("collectionPolicy.recruitingClaimsRequireExplicitEvidence must be true")

    print(f"Validated {len(professors)} professors and {len(labs)} labs")


if __name__ == "__main__":
    main()
