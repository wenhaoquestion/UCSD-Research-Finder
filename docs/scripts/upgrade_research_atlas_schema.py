#!/usr/bin/env python3
"""Upgrade the current Research Atlas JSON to the richer v2.1 data shape.

This is an offline, deterministic normalizer. It does not call Google Scholar,
LinkedIn, OpenAlex, Semantic Scholar, or any other remote service. Use it after
collection/enrichment to backfill additive fields consumed by the redesigned UI.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import unicodedata
import urllib.parse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ATLAS = ROOT / "data" / "research-atlas.json"
DEFAULT_REPORT = ROOT / "data" / "ucsd" / "schema-upgrade-report.json"

MISSING = "Not found"
UNKNOWN = "Unknown"
URL_RE = re.compile(r"^https?://", re.I)

FALSE_POSITIVE_PROFESSOR_NAMES = {
    "Administrative Staff",
    "Acting Faculty",
    "Admin Staff",
    "Affiliated Faculty",
    "Dance Faculty",
    "Design Faculty",
    "Directing Faculty",
    "Emeritus Profile",
    "Endowed Chairs",
    "Faculty In Memoriam",
    "Faculty Emeriti",
    "Faculty Leadership",
    "Faculty by Areas of Specialization",
    "Faculty Profile",
    "Faculty Profiles",
    "Full-Time Faculty",
    "Instructional Support",
    "International Relations",
    "King Research",
    "Kistler Research",
    "La Jolla Playhouse",
    "Literature Faculty",
    "Our Job Market Candidates",
    "Performance Studies Faculty",
    "Playwriting Faculty",
    "Production Staff",
    "Research Faculty",
    "Research Development",
    "Stage Management Faculty",
    "Technical Staff",
    "University Professor",
    "Distinguished Rady Faculty",
    "Emeriti Faculty",
    "Emeritus Faculty",
    "Visiting Artists",
    "Visiting Faculty and Scholars",
    "Visiting Scholars",
}


def is_known(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(text and text.lower() not in {"not found", "unknown"})


def unique(values: list[Any]) -> list[Any]:
    seen: set[str] = set()
    out: list[Any] = []
    for value in values:
        if not is_known(value):
            continue
        key = str(value).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def canonical_name(name: Any) -> str:
    text = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"\b(dr|prof|professor)\.?\b", " ", text, flags=re.I)
    text = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    return " ".join(text.split())


def canonical_url(value: Any) -> str:
    url = str(value or "").strip()
    if not URL_RE.search(url):
        return ""
    url = re.sub(r"#.*$", "", url)
    url = re.sub(r"\?.*$", "", url)
    url = url.rstrip("/").lower()
    url = re.sub(r"^https?://(www\.)?", "", url)
    return url.replace("/index.html", "").replace("/index.htm", "").replace("/index.php", "")


def generic_email(email: str, total_uses: int = 1) -> bool:
    local = email.split("@", 1)[0].lower()
    generic_tokens = (
        "admin",
        "contact",
        "info",
        "media",
        "support",
        "web",
        "webmaster",
        "dept",
        "faculty",
        "grad",
    )
    return total_uses > 3 or any(token in local for token in generic_tokens)


def today() -> str:
    return dt.date.today().isoformat()


def now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def scholar_search_url(professor: dict[str, Any]) -> str:
    existing = str(professor.get("googleScholarSearchUrl") or "")
    if existing.startswith("http"):
        return existing
    query = f"{professor.get('name', '')} {professor.get('institution', 'UC San Diego')}"
    params = urllib.parse.urlencode({"view_op": "search_authors", "mauthors": query, "hl": "en"})
    return f"https://scholar.google.com/citations?{params}"


def linkedin_search_url(professor: dict[str, Any]) -> str:
    existing = str(professor.get("linkedinSearchUrl") or "")
    if existing.startswith("http"):
        return existing
    query = f'site:linkedin.com/in "{professor.get("name", "")}" "UC San Diego"'
    return f"https://www.google.com/search?{urllib.parse.urlencode({'q': query})}"


def profile_status(profile_url: str, expected_host: str) -> str:
    if not is_known(profile_url):
        return "candidate_search"
    return "confirmed" if expected_host in profile_url else "candidate_search"


def profile_source_url(profile_url: str, source_urls: list[str], host: str) -> str:
    if is_known(profile_url) and host in profile_url:
        return profile_url
    for url in source_urls:
        if host in str(url):
            return str(url)
    return MISSING


def external_profiles_for(professor: dict[str, Any]) -> dict[str, dict[str, str]]:
    sources = [str(url) for url in professor.get("sourceUrls", []) if URL_RE.search(str(url))]
    scholar_profile = str(professor.get("googleScholarUrl") or MISSING)
    linkedin_profile = str(professor.get("linkedinUrl") or MISSING)
    scholar_search = scholar_search_url(professor)
    linkedin_search = linkedin_search_url(professor)
    return {
        "googleScholar": {
            "profileUrl": scholar_profile if profile_status(scholar_profile, "scholar.google.") == "confirmed" else MISSING,
            "searchUrl": scholar_search,
            "status": profile_status(scholar_profile, "scholar.google."),
            "sourceUrl": profile_source_url(scholar_profile, sources, "scholar.google."),
            "lastChecked": today(),
        },
        "linkedin": {
            "profileUrl": linkedin_profile if profile_status(linkedin_profile, "linkedin.com/in/") == "confirmed" else MISSING,
            "searchUrl": linkedin_search,
            "status": profile_status(linkedin_profile, "linkedin.com/in/"),
            "sourceUrl": profile_source_url(linkedin_profile, sources, "linkedin.com/in/"),
            "lastChecked": today(),
        },
    }


def impact_factor_marker() -> dict[str, str]:
    return {
        "value": UNKNOWN,
        "year": UNKNOWN,
        "source": "Unavailable in open-data mode",
        "status": "unavailable_open_data",
    }


def doi_from_publication(publication: dict[str, Any]) -> str:
    doi = str(publication.get("doi") or "")
    if doi:
        return doi
    url = str(publication.get("url") or "")
    if "doi.org/" in url:
        return url
    return UNKNOWN


def normalize_publication(publication: dict[str, Any]) -> dict[str, Any]:
    item = dict(publication)
    item.setdefault("title", MISSING)
    item.setdefault("year", UNKNOWN)
    item.setdefault("publicationDate", UNKNOWN)
    item.setdefault("citationCount", UNKNOWN)
    item.setdefault("venue", UNKNOWN)
    item.setdefault("url", MISSING)
    item["doi"] = doi_from_publication(item)
    item.setdefault("openAlexUrl", item.get("id") if str(item.get("id", "")).startswith("http") else UNKNOWN)
    item.setdefault("semanticScholarUrl", UNKNOWN)
    item.setdefault("journalImpactFactor", impact_factor_marker())
    item.setdefault("source", UNKNOWN)
    return item


def metric_sources(profile: dict[str, Any]) -> list[dict[str, Any]]:
    sources = list(profile.get("metricSources") or [])
    source_names = {str(item.get("source")) for item in sources if isinstance(item, dict)}
    if is_known(profile.get("openAlexUrl")) and "OpenAlex" not in source_names:
        sources.append(
            {
                "source": "OpenAlex",
                "url": profile.get("openAlexUrl"),
                "matchConfidence": profile.get("matchConfidence", 0),
                "lastVerified": profile.get("lastVerified", today()),
            }
        )
    if is_known(profile.get("semanticScholarUrl")) and "Semantic Scholar" not in source_names:
        sources.append(
            {
                "source": "Semantic Scholar",
                "url": profile.get("semanticScholarUrl"),
                "matchConfidence": profile.get("semanticScholarMatchConfidence", profile.get("matchConfidence", 0)),
                "lastVerified": profile.get("lastVerified", today()),
            }
        )
    return sources


def numeric(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def academic_quality(profile: dict[str, Any]) -> tuple[float, float, float, float]:
    return (
        1.0 if is_known(profile.get("openAlexUrl")) or is_known(profile.get("semanticScholarUrl")) else 0.0,
        numeric(profile.get("citationCount")),
        numeric(profile.get("hIndex")),
        numeric(profile.get("worksCount")),
    )


def low_information_summary(value: Any) -> bool:
    text = str(value or "").strip()
    if not is_known(text):
        return True
    lowered = text.lower()
    return (
        len(text) < 90
        or lowered.startswith("faculty listing from")
        or lowered.startswith("public ")
        or "profile, lab and email links need" in lowered
    )


def professor_quality(professor: dict[str, Any]) -> tuple[int, int, int, int, int, int]:
    academic = professor.get("academicProfile") or {}
    official = str(professor.get("officialProfileUrl") or "")
    return (
        1 if is_known(academic.get("openAlexUrl")) or is_known(academic.get("semanticScholarUrl")) else 0,
        1 if is_known(professor.get("personalWebsiteUrl")) else 0,
        1 if is_known(professor.get("email")) else 0,
        1 if is_known(official) and "catalog.ucsd.edu" not in official and "/api/" not in official else 0,
        0 if low_information_summary(professor.get("researchSummary")) else 1,
        len(professor.get("sourceUrls") or []),
    )


def best_known(records: list[dict[str, Any]], field: str) -> Any:
    for record in sorted(records, key=professor_quality, reverse=True):
        value = record.get(field)
        if is_known(value):
            return value
    return MISSING


def best_summary(records: list[dict[str, Any]]) -> str:
    candidates = [str(record.get("researchSummary") or "") for record in records if not low_information_summary(record.get("researchSummary"))]
    if candidates:
        return max(candidates, key=len)
    return str(best_known(records, "researchSummary") or MISSING)


def best_academic_profile(records: list[dict[str, Any]]) -> dict[str, Any]:
    profiles = [dict(record.get("academicProfile") or {}) for record in records]
    if not profiles:
        return normalize_academic_profile({})
    return max(profiles, key=academic_quality)


def merge_professor_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    best = dict(max(records, key=professor_quality))
    departments = unique([best.get("department"), *[record.get("department") for record in records]])
    source_urls = unique(
        [
            *(best.get("sourceUrls") or []),
            *[url for record in records for url in (record.get("sourceUrls") or [])],
            *[record.get("officialProfileUrl") for record in records],
            *[record.get("personalWebsiteUrl") for record in records],
            *[record.get("labAffiliationUrl") for record in records],
        ]
    )
    best["departments"] = departments
    best["department"] = str(departments[0]) if departments else str(best.get("department") or UNKNOWN)
    best["mergedProfessorIds"] = unique([record.get("id") for record in records])
    best["sourceUrls"] = source_urls
    best["researchAreas"] = unique([area for record in records for area in (record.get("researchAreas") or [])]) or [best["department"]]
    best["researchSummary"] = best_summary(records)
    best["email"] = best_known(records, "email")
    best["officialProfileUrl"] = best_known(records, "officialProfileUrl")
    best["personalWebsiteUrl"] = best_known(records, "personalWebsiteUrl")
    best["labAffiliation"] = best_known(records, "labAffiliation")
    best["labAffiliationUrl"] = best_known(records, "labAffiliationUrl")
    best["googleScholarUrl"] = best_known(records, "googleScholarUrl")
    best["linkedinUrl"] = best_known(records, "linkedinUrl")
    best["academicProfile"] = normalize_academic_profile({"academicProfile": best_academic_profile(records)})
    best["googleScholarSearchUrl"] = scholar_search_url(best)
    best["linkedinSearchUrl"] = linkedin_search_url(best)
    best["externalProfiles"] = external_profiles_for(best)
    return best


def merge_duplicate_professors(professors: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parent = list(range(len(professors)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    email_uses: dict[str, set[str]] = {}
    for professor in professors:
        email = str(professor.get("email") or "").lower()
        if is_known(email):
            email_uses.setdefault(email, set()).add(canonical_name(professor.get("name")))

    key_to_index: dict[tuple[str, str], int] = {}

    def add_key(index: int, key: tuple[str, str]) -> None:
        if not key[1]:
            return
        previous = key_to_index.get(key)
        if previous is None:
            key_to_index[key] = index
        else:
            union(previous, index)

    for index, professor in enumerate(professors):
        name_key = canonical_name(professor.get("name"))
        if len(name_key.split()) >= 2:
            add_key(index, ("name", name_key))
        email = str(professor.get("email") or "").lower()
        if is_known(email) and not generic_email(email, len(email_uses.get(email, set()))):
            add_key(index, ("email", email))
        academic = professor.get("academicProfile") or {}
        openalex_key = canonical_url(academic.get("openAlexUrl") or academic.get("openAlexAuthorId"))
        if openalex_key:
            add_key(index, ("openalex", openalex_key))
    groups: dict[int, list[dict[str, Any]]] = {}
    for index, professor in enumerate(professors):
        groups.setdefault(find(index), []).append(professor)

    merged = []
    report_rows = []
    for group in groups.values():
        if len(group) == 1:
            merged.append(group[0])
            continue
        record = merge_professor_records(group)
        merged.append(record)
        report_rows.append(
            {
                "keptId": record.get("id"),
                "name": record.get("name"),
                "departments": record.get("departments", []),
                "mergedProfessorIds": record.get("mergedProfessorIds", []),
            }
        )
    return sorted(merged, key=lambda item: (str(item.get("department", "")), str(item.get("name", "")))), report_rows


def normalize_academic_profile(professor: dict[str, Any]) -> dict[str, Any]:
    profile = dict(professor.get("academicProfile") or {})
    profile.setdefault("source", "OpenAlex")
    profile.setdefault("openAlexAuthorId", MISSING)
    profile.setdefault("openAlexUrl", MISSING)
    profile.setdefault("semanticScholarAuthorId", MISSING)
    profile.setdefault("semanticScholarUrl", MISSING)
    profile.setdefault("matchedName", MISSING)
    profile.setdefault("matchConfidence", 0)
    profile.setdefault("worksCount", UNKNOWN)
    profile.setdefault("citationCount", UNKNOWN)
    profile.setdefault("hIndex", UNKNOWN)
    profile.setdefault("i10Index", UNKNOWN)
    profile["recentPublications"] = [normalize_publication(item) for item in profile.get("recentPublications", [])]
    profile["metricSources"] = metric_sources(profile)
    profile.setdefault("lastVerified", today())
    return profile


def entity_type_for(lab: dict[str, Any]) -> str:
    value = f"{lab.get('labName', '')} {lab.get('labWebsiteUrl', '')} {lab.get('legacyKind', '')}".lower()
    checks = [
        ("research_group", ["research group"]),
        ("core", ["core"]),
        ("clinic", ["clinic"]),
        ("studio", ["studio"]),
        ("observatory", ["observatory"]),
        ("facility", ["facility", "facilities"]),
        ("institute", ["institute"]),
        ("center", ["center", "centre"]),
        ("personal_research_site", ["personal_site", "personal research", "research site"]),
    ]
    for label, needles in checks:
        if any(needle in value for needle in needles):
            return label
    return "lab"


def confidence_for(lab: dict[str, Any]) -> str:
    if lab.get("legacyKind") == "curated_lab":
        return "high"
    if is_known(lab.get("principalInvestigator")) and len(lab.get("sourceUrls") or []) > 1:
        return "high"
    if is_known(lab.get("principalInvestigator")) or len(lab.get("sourceUrls") or []) > 1:
        return "medium"
    return "low"


def normalize_lab(lab: dict[str, Any]) -> dict[str, Any]:
    updated = dict(lab)
    source_urls = [str(url) for url in updated.get("sourceUrls", []) if URL_RE.search(str(url))]
    pi = str(updated.get("principalInvestigator") or MISSING)
    updated.setdefault("departments", unique([updated.get("department")]))
    updated.setdefault("entityType", entity_type_for(updated))
    updated.setdefault("coverageStatus", "entity_verified" if is_known(updated.get("labWebsiteUrl")) else "overview_only")
    updated.setdefault("discoveryMethod", str(updated.get("legacyKind") or updated.get("recordSubtype") or "unknown"))
    updated.setdefault("confidence", confidence_for(updated))
    updated.setdefault("piCandidates", [pi] if is_known(pi) else [])
    updated.setdefault("overviewSourceUrl", source_urls[0] if source_urls else MISSING)
    return updated


def lab_quality(lab: dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        1 if is_known(lab.get("principalInvestigator")) else 0,
        1 if str(lab.get("confidence") or "") == "high" else 0,
        len(lab.get("sourceUrls") or []),
        len(lab.get("researchAreas") or []),
    )


def merge_lab_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    best = dict(max(records, key=lab_quality))
    departments = unique([best.get("department"), *[dept for record in records for dept in (record.get("departments") or [record.get("department")])]])
    source_urls = unique([url for record in records for url in (record.get("sourceUrls") or [])] + [record.get("labWebsiteUrl") for record in records])
    areas = unique([area for record in records for area in (record.get("researchAreas") or [])])
    pi_candidates = unique([candidate for record in records for candidate in (record.get("piCandidates") or [])] + [record.get("principalInvestigator") for record in records])
    best["departments"] = departments
    best["department"] = str(departments[0]) if departments else str(best.get("department") or UNKNOWN)
    best["mergedLabIds"] = unique([record.get("id") for record in records])
    best["sourceUrls"] = source_urls
    best["researchAreas"] = areas or best.get("researchAreas") or [best["department"]]
    best["piCandidates"] = pi_candidates
    if pi_candidates and not is_known(best.get("principalInvestigator")):
        best["principalInvestigator"] = pi_candidates[0]
    return best


def merge_duplicate_labs(labs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_url: dict[str, list[dict[str, Any]]] = {}
    singles: list[dict[str, Any]] = []
    for lab in labs:
        key = canonical_url(lab.get("labWebsiteUrl"))
        if not key:
            singles.append(lab)
            continue
        by_url.setdefault(key, []).append(lab)

    merged = list(singles)
    report_rows = []
    for group in by_url.values():
        if len(group) == 1:
            merged.append(group[0])
            continue
        record = merge_lab_records(group)
        merged.append(record)
        report_rows.append(
            {
                "keptId": record.get("id"),
                "labName": record.get("labName"),
                "departments": record.get("departments", []),
                "mergedLabIds": record.get("mergedLabIds", []),
                "labWebsiteUrl": record.get("labWebsiteUrl"),
            }
        )
    return sorted(merged, key=lambda item: (str(item.get("department", "")), str(item.get("labName", "")))), report_rows


def suspicious_professor(professor: dict[str, Any]) -> bool:
    name = str(professor.get("name") or "").strip()
    if name in FALSE_POSITIVE_PROFESSOR_NAMES:
        return True
    if re.search(r"\b(Profile|Profiles|Scholars|Support|Development|Chairs)\b", name) and not is_known(professor.get("email")):
        return True
    return False


def upgrade(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    removed = []
    professors = []
    for professor in data.get("professors", []):
        if suspicious_professor(professor):
            removed.append({"id": professor.get("id"), "name": professor.get("name"), "department": professor.get("department")})
            continue
        updated = dict(professor)
        updated["googleScholarSearchUrl"] = scholar_search_url(updated)
        updated["linkedinSearchUrl"] = linkedin_search_url(updated)
        updated["externalProfiles"] = external_profiles_for(updated)
        updated["academicProfile"] = normalize_academic_profile(updated)
        professors.append(updated)
    professors, duplicate_report = merge_duplicate_professors(professors)

    labs = [normalize_lab(lab) for lab in data.get("labs", [])]
    labs, duplicate_lab_report = merge_duplicate_labs(labs)
    retained_research_site_labs = [
        {
            "id": lab.get("id"),
            "labName": lab.get("labName"),
            "department": lab.get("department"),
            "principalInvestigator": lab.get("principalInvestigator"),
            "labWebsiteUrl": lab.get("labWebsiteUrl"),
            "entityType": lab.get("entityType"),
        }
        for lab in labs
        if lab.get("entityType") == "personal_research_site"
    ]
    upgraded = dict(data)
    upgraded["schemaVersion"] = "2.1.0"
    upgraded["generatedAt"] = now_iso()
    upgraded["professors"] = professors
    upgraded["labs"] = labs
    report = {
        "generatedAt": upgraded["generatedAt"],
        "inputProfessorCount": len(data.get("professors", [])),
        "outputProfessorCount": len(professors),
        "mergedDuplicateProfessorGroups": duplicate_report,
        "removedDuplicateProfessorRecords": sum(max(0, len(row["mergedProfessorIds"]) - 1) for row in duplicate_report),
        "inputLabCount": len(data.get("labs", [])),
        "labCount": len(labs),
        "mergedDuplicateLabGroups": duplicate_lab_report,
        "removedDuplicateLabRecords": sum(max(0, len(row["mergedLabIds"]) - 1) for row in duplicate_lab_report),
        "removedFalsePositiveProfessors": removed,
        "retainedResearchSiteLabs": retained_research_site_labs,
        "removedPersonalSiteLabs": [],
        "openDataPolicy": {
            "googleScholar": "No direct scraping; confirmed profile URLs only from public source links or manual overrides.",
            "linkedin": "No direct scraping; confirmed profile URLs only from public source links or manual overrides.",
            "journalImpactFactor": "Official JIF requires licensed Clarivate/JCR access; open-data mode marks it unavailable.",
        },
    }
    return upgraded, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_ATLAS)
    parser.add_argument("--out", type=Path, default=DEFAULT_ATLAS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    upgraded, report = upgrade(data)
    args.out.write_text(json.dumps(upgraded, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Upgraded {report['outputProfessorCount']} professors and {report['labCount']} labs; "
        f"removed {len(report['removedFalsePositiveProfessors'])} false-positive professors, "
        f"merged {report['removedDuplicateProfessorRecords']} duplicate professor records, "
        f"merged {report['removedDuplicateLabRecords']} duplicate lab records, "
        f"retained {len(report['retainedResearchSiteLabs'])} research-site lab records"
    )


if __name__ == "__main__":
    main()
