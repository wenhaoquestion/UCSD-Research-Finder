#!/usr/bin/env python3
"""Build UCSD coverage reports for Research Atlas.

The report is intentionally conservative: a department is considered covered
when it has lab/research entities in the canonical atlas, or when it has an
explicit overview-only reason backed by discovered public research candidates.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ATLAS = ROOT / "data" / "research-atlas.json"
DEFAULT_DEPARTMENTS = ROOT / "data" / "ucsd" / "departments.json"
DEFAULT_CANDIDATES = ROOT / "data" / "ucsd" / "source-candidates.json"
DEFAULT_RESEARCH_INDEX = ROOT / "data" / "ucsd" / "research-index.json"
DEFAULT_REPORT = ROOT / "data" / "ucsd" / "coverage-report.json"
DEFAULT_REJECTED = ROOT / "data" / "ucsd" / "rejected-lab-candidates.json"

MISSING = {"", "Not found", "Unknown", None}
URL_RE = re.compile(r"^https?://", re.I)


def load_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def known(value: Any) -> bool:
    return value not in MISSING


def url_key(url: str) -> str:
    value = str(url or "").lower().split("#", 1)[0].split("?", 1)[0].rstrip("/")
    value = re.sub(r"^https?://", "", value)
    value = re.sub(r"^www\.", "", value)
    return value.replace("/index.html", "").replace("/index.htm", "").replace("/index.php", "")


def department_rows(departments_data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in departments_data.get("departments", []):
        rows.append(
            {
                "id": item.get("id"),
                "department": item.get("name") or item.get("department"),
                "school": item.get("school", ""),
                "homepage": item.get("homepage", ""),
            }
        )
    return [row for row in rows if row["department"]]


def candidate_rows(candidates_data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for dept in candidates_data.get("departments", []):
        for candidate in dept.get("candidates", []):
            rows.append(
                {
                    "department": dept.get("department"),
                    "school": dept.get("school", ""),
                    "kind": candidate.get("kind"),
                    "url": candidate.get("url"),
                    "linkText": candidate.get("linkText", ""),
                    "verified": bool(candidate.get("verified")),
                    "discovered": bool(candidate.get("discovered")),
                    "sourceUrl": candidate.get("sourceUrl", ""),
                }
            )
    return rows


def research_index_counts(records: list[dict[str, Any]]) -> dict[str, Counter]:
    counts: dict[str, Counter] = defaultdict(Counter)
    for record in records:
        dept = record.get("department")
        if not dept:
            continue
        counts[str(dept)][str(record.get("kind") or "unknown")] += 1
    return counts


def academic_coverage(professors: list[dict[str, Any]]) -> dict[str, Any]:
    confirmed_scholar = 0
    candidate_scholar = 0
    confirmed_linkedin = 0
    candidate_linkedin = 0
    openalex = 0
    semantic = 0
    recent_publications = 0
    email = 0
    personal_site = 0
    for professor in professors:
        external = professor.get("externalProfiles") or {}
        scholar = external.get("googleScholar") or {}
        linkedin = external.get("linkedin") or {}
        if scholar.get("status") == "confirmed":
            confirmed_scholar += 1
        elif scholar.get("status") == "candidate_search" or known(professor.get("googleScholarSearchUrl")):
            candidate_scholar += 1
        if linkedin.get("status") == "confirmed":
            confirmed_linkedin += 1
        elif linkedin.get("status") == "candidate_search" or known(professor.get("linkedinSearchUrl")):
            candidate_linkedin += 1
        academic = professor.get("academicProfile") or {}
        if known(academic.get("openAlexUrl")):
            openalex += 1
        if known(academic.get("semanticScholarUrl")):
            semantic += 1
        if academic.get("recentPublications"):
            recent_publications += 1
        if known(professor.get("email")):
            email += 1
        if known(professor.get("personalWebsiteUrl")):
            personal_site += 1
    return {
        "professorCount": len(professors),
        "confirmedGoogleScholarProfiles": confirmed_scholar,
        "candidateGoogleScholarSearches": candidate_scholar,
        "confirmedLinkedInProfiles": confirmed_linkedin,
        "candidateLinkedInSearches": candidate_linkedin,
        "openAlexProfiles": openalex,
        "semanticScholarProfiles": semantic,
        "recentPublicationProfiles": recent_publications,
        "emails": email,
        "personalWebsites": personal_site,
    }


def build_reports(
    atlas: dict[str, Any],
    departments_data: dict[str, Any],
    candidates_data: dict[str, Any],
    research_index: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    departments = department_rows(departments_data)
    candidates = candidate_rows(candidates_data)
    professors = atlas.get("professors", [])
    labs = atlas.get("labs", [])
    index_counts = research_index_counts(research_index.get("records", []))

    professors_by_dept = Counter(professor.get("department") for professor in professors)
    labs_by_dept = Counter(lab.get("department") for lab in labs)
    missing_pi_by_dept = Counter(
        lab.get("department") for lab in labs if not known(lab.get("principalInvestigator"))
    )
    candidate_counts: dict[str, Counter] = defaultdict(Counter)
    for candidate in candidates:
        candidate_counts[str(candidate.get("department"))][str(candidate.get("kind"))] += 1

    used_lab_urls = {url_key(lab.get("labWebsiteUrl", "")) for lab in labs if URL_RE.search(str(lab.get("labWebsiteUrl", "")))}
    for lab in labs:
        for source_url in lab.get("sourceUrls", []):
            if URL_RE.search(str(source_url)):
                used_lab_urls.add(url_key(str(source_url)))

    department_coverage = []
    for department in departments:
        name = department["department"]
        lab_count = labs_by_dept[name]
        research_like = sum(index_counts[name].get(kind, 0) for kind in ["lab", "research_area", "center", "program"])
        research_candidates = candidate_counts[name].get("research", 0)
        lab_candidates = candidate_counts[name].get("labs", 0)
        if lab_count:
            status = "lab_entities"
            reason = "canonical lab/research entities are available"
        elif research_like or research_candidates:
            status = "overview_only"
            reason = "public research pages exist, but no parseable entity-level lab records were published"
        else:
            status = "needs_source_review"
            reason = "no parseable lab or research overview source found"
        department_coverage.append(
            {
                **department,
                "coverageStatus": status,
                "coverageReason": reason,
                "professorCount": professors_by_dept[name],
                "labCount": lab_count,
                "missingPiCount": missing_pi_by_dept[name],
                "candidateCounts": dict(candidate_counts[name]),
                "legacyResearchIndexCounts": dict(index_counts[name]),
            }
        )

    rejected = []
    for candidate in candidates:
        kind = candidate.get("kind")
        if kind not in {"labs", "research"}:
            continue
        key = url_key(str(candidate.get("url") or ""))
        if key in used_lab_urls:
            continue
        if kind == "research":
            reason = "research_overview_candidate_not_published_as_lab"
        elif labs_by_dept[candidate.get("department")]:
            reason = "candidate_directory_not_selected_or_no_entity_links"
        else:
            reason = "no_parseable_entity_links_for_department"
        rejected.append({**candidate, "reason": reason})

    report = {
        "generatedAt": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "departmentCount": len(department_coverage),
        "coveredDepartments": sum(1 for row in department_coverage if row["coverageStatus"] in {"lab_entities", "overview_only"}),
        "labEntityDepartments": sum(1 for row in department_coverage if row["coverageStatus"] == "lab_entities"),
        "overviewOnlyDepartments": sum(1 for row in department_coverage if row["coverageStatus"] == "overview_only"),
        "needsSourceReviewDepartments": sum(1 for row in department_coverage if row["coverageStatus"] == "needs_source_review"),
        "professorAcademicCoverage": academic_coverage(professors),
        "labQuality": {
            "labCount": len(labs),
            "missingPiCount": sum(1 for lab in labs if not known(lab.get("principalInvestigator"))),
            "entityTypes": dict(Counter(lab.get("entityType", "lab") for lab in labs)),
            "confidence": dict(Counter(lab.get("confidence", "unknown") for lab in labs)),
        },
        "departments": department_coverage,
    }
    rejected_report = {
        "generatedAt": report["generatedAt"],
        "count": len(rejected),
        "candidates": rejected,
    }
    return report, rejected_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas", type=Path, default=DEFAULT_ATLAS)
    parser.add_argument("--departments", type=Path, default=DEFAULT_DEPARTMENTS)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--research-index", type=Path, default=DEFAULT_RESEARCH_INDEX)
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--rejected-out", type=Path, default=DEFAULT_REJECTED)
    args = parser.parse_args()

    report, rejected = build_reports(
        load_json(args.atlas, {}),
        load_json(args.departments, {"departments": []}),
        load_json(args.candidates, {"departments": []}),
        load_json(args.research_index, {"records": []}),
    )
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.rejected_out.write_text(json.dumps(rejected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Coverage: {report['coveredDepartments']}/{report['departmentCount']} departments; "
        f"{report['labEntityDepartments']} with lab entities, {report['overviewOnlyDepartments']} overview-only; "
        f"{rejected['count']} rejected candidates"
    )


if __name__ == "__main__":
    main()
