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
