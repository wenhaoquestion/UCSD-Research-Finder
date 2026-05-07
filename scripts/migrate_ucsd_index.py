#!/usr/bin/env python3
"""Migrate the legacy UCSD research index into the Research Atlas schema."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "ucsd" / "research-index.json"
DEFAULT_OUTPUT = ROOT / "data" / "research-atlas.json"
DEFAULT_SUPPLEMENT = ROOT / "data" / "lab-overrides.json"

MISSING = "Not found"
UNKNOWN = "Unknown"
URL_RE = re.compile(r"^https?://", re.I)
LAB_TOKEN_RE = re.compile(r"(^|[^a-z])lab(orator(?:y|ies))?([^a-z]|$)|research[-_\s]?group|research[-_\s]?lab", re.I)

DEPARTMENT_ALIASES = {
    "Data Science": "Halicioğlu Data Science Institute",
    "Halicioglu Data Science Institute": "Halicioğlu Data Science Institute",
}

BAD_LAB_NAMES = {
    "academic departments",
    "amazon.",
    "contact",
    "directory",
    "events",
    "facilities",
    "facilities and resources",
    "faculty & research",
    "faq",
    "flyer",
    "funding opportunities & resources",
    "innovation",
    "initiatives and units",
    "language program",
    "lecturer",
    "login",
    "observatories & collaborations",
    "oped project",
    "research faculty",
    "research topics",
    "teaching labs",
    "uc davis science communications program",
}

BAD_LAB_URL_PARTS = {
    "academic-sections",
    "amazon.com/",
    "amazon.science/research-awards",
    "/assets/pdf/",
    ".pdf",
    "blog.cirm.ca.gov",
    "calendar",
    "cs.umd.edu/article",
    "events",
    "faculty-and-research/index",
    "faculty-staff",
    "felicefrankel.com",
    "facilities-resources",
    "funding-opportunities-resources",
    "jobs",
    "language-program/faqs",
    "news",
    "philosophy.ucsd.edu/research-groups/index",
    "qualcomm.com/research/university-relations",
    "research/arch-labs",
    "research/bio-anth-labs",
    "research/ling-anthro-labs",
    "research/labs/index",
    "research-labs.html",
    "research/psych-anthro-labs",
    "research/academic-departments",
    "research/facilities",
    "research/innovation",
    "research/research-topics/index",
    "research/shared-resources",
    "github.com/",
    "findinggeniuspodcast.com",
    "/faq/",
    "kusi.com/",
    "researchgate.net/",
    "/publications",
    "/publication",
    "/pubs",
    "/project/",
    "/projects/",
    "simons.berkeley.edu/people",
    "tags/undergraduate-research",
    "the-scientist.com",
    "today.ucsd.edu/story",
    "sio_auth",
    "theopedproject.org",
    "ucsdphilclub.wordpress.com",
    "undergraduate/faq",
    "undergraduate/index",
    "undergraduate/teaching-labs",
}

LABISH_TERMS = {
    "lab",
    "laboratory",
    "research group",
    "group",
    "center",
    "centre",
    "core",
}

GENERIC_LAB_LABELS = {
    "lab / research",
    "lab site",
    "research",
    "website",
    "source",
}

GENERIC_PI_NAMES = {
    "Faculty Affiliates",
    "Research Faculty",
}


def unique(values: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def first_url(record: Dict[str, object], labels: Iterable[str], fallback: bool = False) -> str:
    wanted = [label.lower() for label in labels]
    for link in record.get("links", []):
        label = str(link.get("label", "")).lower()
        url = unwrap_url(str(link.get("url", "")))
        if URL_RE.search(url) and any(want in label for want in wanted):
            return url
    if fallback:
        for link in record.get("links", []):
            url = unwrap_url(str(link.get("url", "")))
            if URL_RE.search(url):
                return url
    return MISSING


def first_link_label_for_url(record: Dict[str, object], url: str) -> str:
    for link in record.get("links", []):
        if link.get("url") == url:
            return str(link.get("label") or MISSING)
    return MISSING


def first_email(record: Dict[str, object]) -> str:
    for contact in record.get("contacts", []):
        if contact.get("type") == "email" and contact.get("value"):
            return str(contact["value"])
    return MISSING


def source_urls(record: Dict[str, object]) -> List[str]:
    urls = [unwrap_url(str(link.get("url", ""))) for link in record.get("links", [])]
    if record.get("sourceUrl"):
        urls.append(str(record["sourceUrl"]))
    return unique(url for url in urls if URL_RE.search(url))


def department_name(value: object) -> str:
    raw = str(value or UNKNOWN)
    return DEPARTMENT_ALIASES.get(raw, raw)


def unwrap_url(url: str) -> str:
    if "urldefense.com" not in url:
        return url
    match = re.search(r"__([^_]+)__", url)
    if not match:
        return url
    unwrapped = match.group(1)
    unwrapped = unwrapped.replace(":/", "://", 1)
    return unwrapped


def normalized_url(url: str) -> str:
    url = unwrap_url(url)
    parsed = re.sub(r"#.*$", "", url.strip())
    parsed = re.sub(r"\?.*$", "", parsed)
    parsed = parsed.rstrip("/")
    return parsed.lower()


def canonical_url_key(url: str) -> str:
    value = normalized_url(url)
    value = re.sub(r"^https?://", "", value)
    value = re.sub(r"^www\.", "", value)
    value = value.replace("/index.html", "").replace("/index.htm", "").replace("/index.php", "")
    if labish_host(value):
        host = value.split("/", 1)[0]
        return host
    return value


def canonical_display_url(url: str) -> str:
    url = unwrap_url(url)
    cleaned = re.sub(r"#.*$", "", str(url).strip())
    cleaned = re.sub(r"\?.*$", "", cleaned).rstrip("/")
    if labish_host(canonical_url_key(cleaned)):
        parsed = re.match(r"^(https?://[^/]+)", cleaned, re.I)
        if parsed:
            return parsed.group(1) + "/"
    return cleaned


def labish_host(value: str) -> bool:
    host = re.sub(r"^https?://", "", value).split("/", 1)[0]
    return bool(LAB_TOKEN_RE.search(host))


def label_for(record: Dict[str, object], labels: Iterable[str]) -> str:
    wanted = [label.lower() for label in labels]
    for link in record.get("links", []):
        label = str(link.get("label", ""))
        if any(want in label.lower() for want in wanted):
            return label
    return ""


def lab_site_url(record: Dict[str, object]) -> str:
    return first_url(record, ["lab site", "lab / research", "laboratory", "research group"], fallback=True)


def is_bad_lab_candidate(name: str, url: str, text: str = "") -> bool:
    lowered_name = name.strip().lower()
    lowered = f"{lowered_name} {url} {text}".lower()
    if lowered_name in BAD_LAB_NAMES:
        return True
    if url in {MISSING, UNKNOWN, ""}:
        return True
    return any(part in lowered for part in BAD_LAB_URL_PARTS)


def looks_like_actual_lab(
    name: str,
    url: str,
    text: str = "",
    has_pi: bool = False,
    explicit_lab_label: bool = False,
    pi: str = "",
) -> bool:
    if not URL_RE.search(url):
        return False
    if is_bad_lab_candidate(name, url, text):
        return False

    lowered = f"{name} {url} {text}".lower()
    if LAB_TOKEN_RE.search(lowered):
        return True
    if LAB_TOKEN_RE.search(normalized_url(url)):
        return True
    if explicit_lab_label and has_pi:
        normalized = normalized_url(url)
        last = short_person_name(pi).lower()
        if len(last) >= 3 and last in normalized:
            return True
        if "research" in normalized:
            return True
        return False
    return False


def same_ucsd_generic_page(url: str) -> bool:
    lowered = normalized_url(url)
    generic_parts = [
        "/research/index",
        "/people/faculty/index",
        "/faculty/index",
        "/faculty-and-research/index",
        "/research/topics",
        "/research/research-topics",
    ]
    return "ucsd.edu" in lowered and any(part in lowered for part in generic_parts)


def clean_lab_name(name: str, pi: str = "") -> str:
    name = str(name or "").strip()
    name = re.sub(r"\.html?$", "", name, flags=re.I).strip()
    if name.isupper() and len(name.split()) <= 3:
        name = " ".join(part.capitalize() for part in name.split())
    if name.lower() in GENERIC_LAB_LABELS and pi:
        return f"{short_person_name(pi)} Lab"
    if pi and not any(term in name.lower() for term in ["lab", "laboratory", "research group", "center"]):
        return f"{name} Lab"
    return name or (f"{short_person_name(pi)} Lab" if pi else "Research Lab")


def short_person_name(name: str) -> str:
    parts = [part.strip(".,()") for part in str(name).split() if part.strip(".,()")]
    if not parts:
        return "Research"
    last = parts[-1]
    if len(last) == 1 and len(parts) > 1:
        last = parts[-2]
    return last


def base_lab_name(name: str) -> str:
    value = str(name or "").lower()
    value = re.sub(r"\.html?$", "", value)
    value = re.sub(r"\b(lab|laboratory|research group|group|center|centers and labs|affiliates)\b", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value).strip()
    return value


def areas(record: Dict[str, object]) -> List[str]:
    values = []
    for key in ["interests", "researchDirections", "methods"]:
        values.extend(str(item) for item in record.get(key, []) if item)
    department = str(record.get("department") or "")
    if department:
        values.append(department)
    return unique(values) or ["Research"]


def verified_date(data: Dict[str, object]) -> str:
    generated = data.get("generatedAt")
    if not generated:
        return dt.date.today().isoformat()
    try:
        return dt.datetime.fromisoformat(str(generated).replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return dt.date.today().isoformat()


def institution_name(data: Dict[str, object]) -> str:
    university = data.get("university") or {}
    name = university.get("name") if isinstance(university, dict) else None
    if name == "UC San Diego":
        return "University of California San Diego"
    return str(name or "University of California San Diego")


def professor_from(record: Dict[str, object], institution: str, date: str) -> Optional[Dict[str, object]]:
    name = str(record.get("name") or "").strip()
    if not name:
        return None

    profile_url = first_url(record, ["faculty profile", "full profile", "catalog faculty listing", "profile"], fallback=True)
    personal_url = first_url(record, ["website", "personal"])
    scholar_url = first_url(record, ["google scholar", "scholar"])
    lab_url = first_url(record, ["lab / research", "lab", "laboratory", "research group"])
    lab_label = first_link_label_for_url(record, lab_url) if lab_url != MISSING else MISSING
    if lab_label in {"Lab / research", "Research"}:
        lab_label = "Lab or research page"

    urls = source_urls(record)
    if not urls and profile_url != MISSING:
        urls = [profile_url]
    if not urls:
        return None

    return {
        "id": str(record.get("id") or f"ucsd-prof-{slug(name)}"),
        "name": name,
        "institution": institution,
        "department": department_name(record.get("department")),
        "officialProfileUrl": profile_url,
        "personalWebsiteUrl": personal_url,
        "email": first_email(record),
        "researchAreas": areas(record),
        "researchSummary": str(record.get("summary") or "Public faculty record from UC San Diego sources."),
        "googleScholarUrl": scholar_url,
        "labAffiliation": lab_label,
        "labAffiliationUrl": lab_url,
        "recruitingStatus": UNKNOWN,
        "recruitingEvidence": {"text": "", "url": ""},
        "sourceUrls": urls,
        "lastVerified": date,
        "legacyKind": "faculty",
    }


def lab_from(record: Dict[str, object], institution: str, date: str) -> Optional[Dict[str, object]]:
    name = str(record.get("name") or "").strip()
    if not name:
        return None

    kind = str(record.get("kind") or "lab")
    if kind != "lab":
        return None

    site_url = lab_site_url(record)
    pi = MISSING
    for person in record.get("people", []):
        if person.get("name"):
            pi = str(person["name"])
            break
    if pi in GENERIC_PI_NAMES:
        return None

    explicit_label = bool(label_for(record, ["lab site", "lab / research", "laboratory", "research group"]))
    if not looks_like_actual_lab(name, site_url, "", pi != MISSING, explicit_label, pi):
        return None

    urls = source_urls(record)
    if not urls and site_url != MISSING:
        urls = [site_url]
    if not urls:
        return None

    if "profiles." in normalized_url(site_url):
        return None
    lab_website_url = canonical_display_url(site_url)

    return {
        "id": str(record.get("id") or f"ucsd-{kind}-{slug(name)}"),
        "labName": clean_lab_name(name, pi),
        "institution": institution,
        "department": department_name(record.get("department")),
        "labWebsiteUrl": lab_website_url,
        "principalInvestigator": pi,
        "principalInvestigatorProfileUrl": MISSING,
        "researchAreas": areas(record),
        "description": str(record.get("summary") or "Public research record from UC San Diego sources."),
        "contactEmail": first_email(record),
        "recruitingStatus": UNKNOWN,
        "recruitingEvidence": {"text": "", "url": ""},
        "sourceUrls": urls,
        "lastVerified": date,
        "recordSubtype": "lab",
        "legacyKind": kind,
    }


def lab_name_from_url(url: str, pi: str) -> str:
    parsed = re.sub(r"^www\.", "", re.sub(r":\d+$", "", re.sub(r"^.*://", "", url)).split("/")[0])
    host_part = parsed.split(".")[0]
    path_parts = [part for part in re.sub(r"^https?://[^/]+/?", "", url).split("/") if part]
    candidates = [host_part] + path_parts[:2]
    for candidate in candidates:
        cleaned = re.sub(r"[-_]+", " ", candidate)
        cleaned = re.sub(r"\b(ucsd|edu|www|home|index|research|people|faculty)\b", "", cleaned, flags=re.I)
        cleaned = re.sub(r"(?i)([a-z])lab$", r"\1 Lab", cleaned)
        cleaned = cleaned.strip()
        if not cleaned:
            continue
        if cleaned.lower() in {"lab", "labs"}:
            continue
        if "lab" in cleaned.lower():
            words = [word.capitalize() for word in cleaned.split()]
            return " ".join(words)
    return f"{short_person_name(pi)} Lab"


def lab_from_professor_link(record: Dict[str, object], institution: str, date: str, link: Dict[str, str]) -> Optional[Dict[str, object]]:
    label = str(link.get("label") or "")
    url = unwrap_url(str(link.get("url") or ""))
    if not URL_RE.search(url):
        return None
    if is_bad_lab_candidate(label, url):
        return None
    if not any(term in label.lower() for term in ["lab", "laboratory", "research group"]):
        return None

    pi = str(record.get("name") or "").strip()
    if not pi:
        return None
    if pi in GENERIC_PI_NAMES:
        return None

    summary = str(record.get("summary") or "")
    normalized = normalized_url(url)
    if "profiles." in normalized:
        return None
    last = short_person_name(pi).lower()
    has_specific_lab_signal = (
        LAB_TOKEN_RE.search(normalized)
        or "research-group" in normalized
        or "research_group" in normalized
    )
    if not has_specific_lab_signal:
        return None
    if not looks_like_actual_lab(label, url, summary, has_pi=True, explicit_lab_label=True, pi=pi):
        return None

    profile_url = first_url(record, ["faculty profile", "full profile", "catalog faculty listing", "profile"], fallback=True)
    urls = unique([url, profile_url] + source_urls(record))
    display_url = canonical_display_url(url)
    name = lab_name_from_url(display_url, pi)

    return {
        "id": f"ucsd-lab-from-faculty-{slug(canonical_url_key(display_url))}",
        "labName": clean_lab_name(name, pi),
        "institution": institution,
        "department": department_name(record.get("department")),
        "labWebsiteUrl": display_url,
        "principalInvestigator": pi,
        "principalInvestigatorProfileUrl": profile_url,
        "researchAreas": areas(record),
        "description": summary or f"Professor-linked lab or research page for {pi}.",
        "contactEmail": first_email(record),
        "recruitingStatus": UNKNOWN,
        "recruitingEvidence": {"text": "", "url": ""},
        "sourceUrls": urls,
        "lastVerified": date,
        "recordSubtype": "lab",
        "legacyKind": "faculty_lab_link",
    }


def merge_lab(existing: Dict[str, object], incoming: Dict[str, object]) -> Dict[str, object]:
    merged = dict(existing)
    merged["sourceUrls"] = unique(list(existing.get("sourceUrls", [])) + list(incoming.get("sourceUrls", [])))
    merged["researchAreas"] = unique(list(existing.get("researchAreas", [])) + list(incoming.get("researchAreas", [])))
    if existing.get("principalInvestigator") in {MISSING, UNKNOWN, ""} and incoming.get("principalInvestigator"):
        merged["principalInvestigator"] = incoming["principalInvestigator"]
    if existing.get("principalInvestigatorProfileUrl") in {MISSING, UNKNOWN, ""} and incoming.get("principalInvestigatorProfileUrl"):
        merged["principalInvestigatorProfileUrl"] = incoming["principalInvestigatorProfileUrl"]
    if existing.get("contactEmail") in {MISSING, UNKNOWN, ""} and incoming.get("contactEmail"):
        merged["contactEmail"] = incoming["contactEmail"]
    if len(str(incoming.get("description", ""))) > len(str(existing.get("description", ""))):
        merged["description"] = incoming["description"]
    if existing.get("legacyKind") == "lab" and incoming.get("principalInvestigator") not in {MISSING, UNKNOWN, ""}:
        merged["principalInvestigator"] = incoming["principalInvestigator"]
        merged["principalInvestigatorProfileUrl"] = incoming.get("principalInvestigatorProfileUrl", merged.get("principalInvestigatorProfileUrl", MISSING))
        if incoming.get("contactEmail") not in {MISSING, UNKNOWN, ""}:
            merged["contactEmail"] = incoming["contactEmail"]
    if existing.get("labName", "").lower() in GENERIC_LAB_LABELS and incoming.get("labName"):
        merged["labName"] = incoming["labName"]
    return merged


def merge_same_name_labs(labs: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    merged: Dict[tuple, Dict[str, object]] = {}
    for lab in labs:
        pi = lab.get("principalInvestigator")
        name_key = base_lab_name(str(lab.get("labName", "")))
        if pi in {MISSING, UNKNOWN, "", None} or not name_key:
            key = ("id", lab["id"])
        else:
            key = (lab.get("department"), pi, name_key)
        merged[key] = merge_lab(merged[key], lab) if key in merged else lab
    return list(merged.values())


def lab_from_supplement(item: Dict[str, object], date: str) -> Optional[Dict[str, object]]:
    url = str(item.get("labWebsiteUrl") or "")
    name = str(item.get("labName") or "").strip()
    if not name or is_bad_lab_candidate(name, url):
        return None
    source_urls = unique([url] + [str(u) for u in item.get("sourceUrls", []) if URL_RE.search(str(u))])
    if not source_urls:
        return None
    pi = str(item.get("principalInvestigator") or MISSING)
    return {
        "id": str(item.get("id") or f"ucsd-lab-curated-{slug(canonical_url_key(url))}"),
        "labName": clean_lab_name(name, pi),
        "institution": str(item.get("institution") or "University of California San Diego"),
        "department": department_name(item.get("department")),
        "labWebsiteUrl": canonical_display_url(url),
        "principalInvestigator": pi,
        "principalInvestigatorProfileUrl": str(item.get("principalInvestigatorProfileUrl") or MISSING),
        "researchAreas": unique([str(x) for x in item.get("researchAreas", []) if x] or ["Research"]),
        "description": str(item.get("description") or f"Curated lab record for {name}."),
        "contactEmail": str(item.get("contactEmail") or MISSING),
        "recruitingStatus": str(item.get("recruitingStatus") or UNKNOWN),
        "recruitingEvidence": item.get("recruitingEvidence") or {"text": "", "url": ""},
        "sourceUrls": source_urls,
        "lastVerified": str(item.get("lastVerified") or date),
        "recordSubtype": "lab",
        "legacyKind": "curated_lab",
    }


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unknown"


def migrate(data: Dict[str, object], supplement_path: Optional[Path] = None) -> Dict[str, object]:
    institution = institution_name(data)
    date = verified_date(data)
    professors = []
    labs_by_url: Dict[str, Dict[str, object]] = {}

    for record in data.get("records", []):
        kind = record.get("kind")
        if kind == "faculty":
            professor = professor_from(record, institution, date)
            if professor:
                professors.append(professor)
            for link in record.get("links", []):
                lab = lab_from_professor_link(record, institution, date, link)
                if lab:
                    key = canonical_url_key(lab["labWebsiteUrl"])
                    labs_by_url[key] = merge_lab(labs_by_url[key], lab) if key in labs_by_url else lab
        elif kind in {"lab", "research_area", "center", "program", "contact"}:
            lab = lab_from(record, institution, date)
            if lab:
                key = canonical_url_key(lab["labWebsiteUrl"])
                labs_by_url[key] = merge_lab(labs_by_url[key], lab) if key in labs_by_url else lab

    if supplement_path and supplement_path.exists():
        supplement = json.loads(supplement_path.read_text(encoding="utf-8"))
        for item in supplement.get("labs", []):
            lab = lab_from_supplement(item, date)
            if not lab:
                continue
            key = canonical_url_key(lab["labWebsiteUrl"])
            labs_by_url[key] = merge_lab(labs_by_url[key], lab) if key in labs_by_url else lab

    labs = sorted(merge_same_name_labs(labs_by_url.values()), key=lambda item: (item["department"], item["labName"]))

    return {
        "schemaVersion": "2.0.0",
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "datasetName": "Research Atlas UCSD dataset",
        "description": "Migrated from the legacy UCSD public research index into the canonical Research Atlas schema.",
        "collectionPolicy": {
            "publicPagesOnly": True,
            "recruitingClaimsRequireExplicitEvidence": True,
            "unknownMeansNoExplicitStatementCaptured": True,
            "studentPrivacyBoundary": "Do not collect private rosters, login-only pages, or non-public student information.",
        },
        "professors": professors,
        "labs": labs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--supplement", type=Path, default=DEFAULT_SUPPLEMENT)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    dataset = migrate(data, args.supplement)
    args.out.write_text(json.dumps(dataset, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(dataset['professors'])} professors and {len(dataset['labs'])} lab records to {args.out}")


if __name__ == "__main__":
    main()
