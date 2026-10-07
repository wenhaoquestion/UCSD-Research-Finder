#!/usr/bin/env python3
"""Discover UCSD departments and likely faculty/lab source URLs.

This is the school-level discovery layer. It finds departments first, then
creates candidate faculty/research/lab URLs that downstream adapters can verify.
When the network is poor, the script falls back to a curated snapshot from UCSD
official department pages so the rest of the app can still build.
"""

from __future__ import annotations

import datetime as dt
import concurrent.futures
import json
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "ucsd"
DEPARTMENTS_PATH = DATA_DIR / "departments.json"
CANDIDATES_PATH = DATA_DIR / "source-candidates.json"

USER_AGENT = "ucsd-research-finder-discovery/0.1 (+https://github.com/)"
DISCOVERY_WORKERS = 10
EVC_DEPARTMENTS_URL = "https://evc.ucsd.edu/_resources/General%20Campus%20Department%20Chairs.html"
MED_DEPARTMENTS_URL = "https://medschool.ucsd.edu/about/departments.html"

SOURCE_PATHS = {
    "faculty": [
        "faculty",
        "faculty/index.html",
        "faculty-directory",
        "faculty-directory/index.html",
        "faculty-and-research/faculty-profiles/faculty.html",
        "people/faculty",
        "people/faculty/index.html",
        "people/faculty.html",
        "people/faculty-directory",
        "people/faculty/faculty-directory.html",
        "people/faculty-profiles",
        "people/profiles",
        "people/people-directory",
        "people/people-directory.html",
        "our-people/faculty",
        "directory/faculty",
        "faculty-and-research/faculty",
        "faculty-research/faculty.html",
        "faculty-research/faculty-directory",
        "faculty/radiation-oncology/index.html",
        "faculty/medical-physics/index.html",
        "faculty/applied-sciences/index.html",
        "research/faculty/index.html",
        "research/faculty",
        "faculty-research/faculty",
        "about/faculty",
        "about/faculty-directory",
    ],
    "labs": [
        "research/labs/index.html",
        "research/labs",
        "research/research-labs.html",
        "research/faculty-labs/index.html",
        "research/faculty-labs",
        "research/faculty-research-labs/index.html",
        "research/faculty-research-labs",
        "research/laboratories",
        "research/laboratories/index.html",
        "research/groups",
        "research/groups/index.html",
        "research/research-groups",
        "research/research-groups/index.html",
        "research/labs-and-centers",
        "labs",
        "labs/index.html",
        "labs-and-centers",
        "research/centers",
        "research/centers/index.html",
        "research/programs",
        "faculty-research/ece-laboratories",
    ],
    "research": [
        "research",
        "research/index.html",
        "research-areas",
        "research-focus",
        "faculty-research/ece-research-areas",
        "research/research-topics/index.html",
        "research/research-topics",
        "research/topics/index.html",
        "research/topics",
        "research-groups/research-groups-overview.html",
        "about-us/overview",
    ],
    "people": ["people", "people/index.html"],
}

FALLBACK_DEPARTMENTS = [
    ("School of Arts & Humanities", "History", "https://history.ucsd.edu/"),
    ("School of Arts & Humanities", "Literature", "https://literature.ucsd.edu/"),
    ("School of Arts & Humanities", "Music", "https://music-cms.ucsd.edu/"),
    ("School of Arts & Humanities", "Philosophy", "https://philosophy.ucsd.edu/"),
    ("School of Arts & Humanities", "Theatre & Dance", "https://theatre.ucsd.edu/"),
    ("School of Arts & Humanities", "Visual Arts", "https://visarts.ucsd.edu/"),
    ("School of Biological Sciences", "Cell and Developmental Biology", "https://biology.ucsd.edu/"),
    ("School of Biological Sciences", "Ecology, Behavior and Evolution", "https://biology.ucsd.edu/"),
    ("School of Biological Sciences", "Molecular Biology", "https://biology.ucsd.edu/"),
    ("School of Biological Sciences", "Neurobiology", "https://biology.ucsd.edu/"),
    ("School of Biological Sciences", "Biological Sciences", "https://biology.ucsd.edu/"),
    ("School of Computing, Information and Data Sciences", "Halicioğlu Data Science Institute", "https://datascience.ucsd.edu/"),
    ("School of Global Policy and Strategy", "Global Policy and Strategy", "https://gps.ucsd.edu/"),
    ("Jacobs School of Engineering", "Bioengineering", "https://be.ucsd.edu/"),
    ("Jacobs School of Engineering", "Computer Science and Engineering", "https://cse.ucsd.edu/"),
    ("Jacobs School of Engineering", "Electrical and Computer Engineering", "https://www.ece.ucsd.edu/"),
    ("Jacobs School of Engineering", "Mechanical & Aerospace Engineering", "https://mae.ucsd.edu/"),
    ("Jacobs School of Engineering", "NanoEngineering", "https://nanoengineering.ucsd.edu/"),
    ("Jacobs School of Engineering", "Structural Engineering", "https://se.ucsd.edu/"),
    ("School of Physical Sciences", "Astronomy and Astrophysics", "https://astro.ucsd.edu/"),
    ("School of Physical Sciences", "Biochemistry and Molecular Biophysics", "https://physicalsciences.ucsd.edu/"),
    ("School of Physical Sciences", "Chemistry & Biochemistry", "https://chemistry.ucsd.edu/"),
    ("School of Physical Sciences", "Mathematics", "https://www.math.ucsd.edu/"),
    ("School of Physical Sciences", "Physics", "https://physics.ucsd.edu/"),
    ("Rady School of Management", "Rady School of Management", "https://rady.ucsd.edu/"),
    ("School of Social Sciences", "Anthropology", "https://anthropology.ucsd.edu/"),
    ("School of Social Sciences", "Cognitive Science", "https://www.cogsci.ucsd.edu/"),
    ("School of Social Sciences", "Communication", "https://communication.ucsd.edu/"),
    ("School of Social Sciences", "Economics", "https://economics.ucsd.edu/"),
    ("School of Social Sciences", "Education Studies", "https://eds.ucsd.edu/"),
    ("School of Social Sciences", "Ethnic Studies", "https://ethnicstudies.ucsd.edu/"),
    ("School of Social Sciences", "Linguistics", "https://linguistics.ucsd.edu/"),
    ("School of Social Sciences", "Political Science", "https://polisci.ucsd.edu/"),
    ("School of Social Sciences", "Psychology", "https://psychology.ucsd.edu/"),
    ("School of Social Sciences", "Sociology", "https://sociology.ucsd.edu/"),
    ("School of Social Sciences", "Urban Studies & Planning", "https://usp.ucsd.edu/"),
    ("Scripps Institution of Oceanography", "Scripps Institution of Oceanography", "https://scripps.ucsd.edu/"),
    ("Herbert Wertheim School of Public Health", "Public Health", "https://hwsph.ucsd.edu/"),
    ("Skaggs School of Pharmacy and Pharmaceutical Sciences", "Pharmacy and Pharmaceutical Sciences", "https://pharmacy.ucsd.edu/"),
    ("School of Medicine", "Anesthesiology", "https://anesthesia.ucsd.edu/"),
    ("School of Medicine", "Cellular & Molecular Medicine", "https://cmm.ucsd.edu/"),
    ("School of Medicine", "Dermatology", "https://dermatology.ucsd.edu/"),
    ("School of Medicine", "Emergency Medicine", "https://emergencymed.ucsd.edu/"),
    ("School of Medicine", "Family Medicine", "https://familymedicine.ucsd.edu/"),
    ("School of Medicine", "Medicine", "https://med.ucsd.edu/"),
    ("School of Medicine", "Neurological Surgery", "https://neurosurgery.ucsd.edu/"),
    ("School of Medicine", "Neurosciences", "https://neurosciences.ucsd.edu/"),
    ("School of Medicine", "Obstetrics, Gynecology & Reproductive Sciences", "https://obgyn.ucsd.edu/"),
    ("School of Medicine", "Ophthalmology", "https://shileyeye.ucsd.edu/"),
    ("School of Medicine", "Orthopaedic Surgery", "https://ortho.ucsd.edu/"),
    ("School of Medicine", "Otolaryngology", "https://oto.ucsd.edu/"),
    ("School of Medicine", "Pathology", "https://pathology.ucsd.edu/"),
    ("School of Medicine", "Pediatrics", "https://pediatrics.ucsd.edu/"),
    ("School of Medicine", "Pharmacology", "https://pharmacology.ucsd.edu/"),
    ("School of Medicine", "Psychiatry", "https://psychiatry.ucsd.edu/"),
    ("School of Medicine", "Radiation Medicine", "https://radonc.ucsd.edu/"),
    ("School of Medicine", "Radiology", "https://radiology.ucsd.edu/"),
    ("School of Medicine", "Surgery", "https://surgery.ucsd.edu/"),
    ("School of Medicine", "Urology", "https://urology.ucsd.edu/"),
]

SCHOOL_PREFIXES = {
    "School of",
    "Jacobs School",
    "Rady School",
    "Scripps Institution",
    "Herbert Wertheim",
    "Skaggs School",
}

FALLBACK_NAME_BY_SCHOOL = {(school, name) for school, name, _homepage in FALLBACK_DEPARTMENTS}
FALLBACK_NAMES = {name for _school, name, _homepage in FALLBACK_DEPARTMENTS}

EXCLUDED_LINK_NAMES = {
    "Accessibility",
    "Alumni",
    "Clinical Trials",
    "Contact Us",
    "Continuing Professional Development",
    "Culture of Belonging",
    "Education",
    "Faculty & Staff",
    "Faculty Development",
    "Give",
    "Giving",
    "Graduate Programs (MS & PhD)",
    "Health Sciences",
    "Information for",
    "Interactive Campus Map",
    "Land Acknowledgement",
    "Leadership",
    "Leadership Opportunities",
    "Living in San Diego",
    "MD & Combined Programs",
    "Medical Education & Technology",
    "News",
    "Parking Information",
    "Pathway Programs",
    "Patient Care",
    "Physician Assistant Program",
    "Pivot Grants",
    "Privacy",
    "Requests for Clinical Data",
    "Research Centers & Institutes",
    "Residency & Fellowship Programs",
    "Residents & Fellows",
    "Skip to main content",
    "Student Opportunities",
    "Students",
    "Terms of Use",
    "Training Facilities",
    "UC San Diego School of Medicine",
    "hospitals and clinics",
    "research laboratories",
}

PERSON_OR_NAV_PATH_RE = re.compile(
    r"/(people|person|profiles?|faculty/.+|research/faculty|node|information-for|about/news|education|giving|maps?|profile)/",
    re.I,
)
DIRECTORY_PERSON_PATH_RE = re.compile(
    r"/(?:profiles?|people/faculty|faculty-directory|research/faculty)/[^/]+(?:\.html)?/?$",
    re.I,
)
SOURCE_DISCOVERY_SEEDS = [
    "",
    "research/",
    "research/index.html",
    "people/",
    "people/index.html",
    "faculty/",
    "faculty/index.html",
    "faculty-research/",
    "faculty-and-research/",
]
SOURCE_DISCOVERY_EXCLUDED_TERMS = {
    "alumni",
    "apply",
    "award",
    "calendar",
    "careers",
    "check-list",
    "checklist",
    "clinical-trial",
    "clinical-trials",
    "contact",
    "course",
    "development",
    "education",
    "event",
    "expectation",
    "feedback",
    "funding",
    "give",
    "giving",
    "grant",
    "honor",
    "job",
    "mentor",
    "news",
    "onboarding",
    "privacy",
    "publication",
    "recruit",
    "resource",
    "seminar",
    "skip",
    "staff",
    "student",
    "symposium",
    "training",
    "undergraduate",
    "wellness",
}


class LinkTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self.current_heading = ""
        self._heading_tag = ""
        self._heading_parts: list[str] = []
        self._href = ""
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag in {"h2", "h3"}:
            self._heading_tag = tag
            self._heading_parts = []
        if tag == "a":
            self._href = attrs_dict.get("href") or ""
            self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._heading_tag:
            self._heading_parts.append(data)
        if self._href:
            self._text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == self._heading_tag:
            heading = clean_text(" ".join(self._heading_parts))
            if heading:
                self.current_heading = heading
            self._heading_tag = ""
            self._heading_parts = []
        if tag == "a" and self._href:
            text = clean_text(" ".join(self._text_parts))
            if text:
                self.links.append({"text": text, "href": self._href, "heading": self.current_heading})
            self._href = ""
            self._text_parts = []


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str) -> str:
    value = value.lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def fetch(url: str, timeout: int) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(900_000).decode(response.headers.get_content_charset() or "utf-8", errors="replace")


def normalize_homepage_url(homepage: str) -> str:
    parsed = urllib.parse.urlparse(homepage)
    path = parsed.path or "/"
    if path.endswith("/index.html/") or path.endswith("/index.aspx/"):
        path = path[:-1]
    if re.search(r"/[^/]+\.(?:html|aspx|php)$", path, re.I):
        normalized_path = path
    else:
        normalized_path = path if path.endswith("/") else f"{path}/"
    return urllib.parse.urlunparse(parsed._replace(path=normalized_path))


def is_school_name(name: str) -> bool:
    return any(name.startswith(prefix) for prefix in SCHOOL_PREFIXES)


def normalize_department_name(name: str) -> str:
    replacements = {
        "S tru ctural Engineering": "Structural Engineering",
        "Obstetrics, Gynecology & Reproductive Sciences": "Obstetrics, Gynecology & Reproductive Sciences",
    }
    return replacements.get(clean_text(name), clean_text(name))


def is_allowed_department_link(name: str, href: str, school: str) -> bool:
    if name in EXCLUDED_LINK_NAMES or is_school_name(name):
        return False
    if (school, name) in FALLBACK_NAME_BY_SCHOOL or name in FALLBACK_NAMES:
        return True
    parsed = urllib.parse.urlparse(href)
    path = parsed.path.rstrip("/")
    if PERSON_OR_NAV_PATH_RE.search(f"{path}/"):
        return False
    if len(name.split()) == 2 and all(part[:1].isupper() for part in name.split()):
        return False
    return False


def parse_departments(markup: str, base_url: str, default_school: str | None = None) -> list[dict]:
    parser = LinkTextParser()
    parser.feed(markup)
    departments = []
    for link in parser.links:
        name = normalize_department_name(link["text"].strip("† "))
        if not name or is_school_name(name):
            continue
        href = urllib.parse.urljoin(base_url, link["href"])
        host = urllib.parse.urlparse(href).netloc
        if not host.endswith("ucsd.edu"):
            continue
        school = default_school or clean_text(link.get("heading") or "")
        if not school or school in {"Departments", "About"}:
            continue
        if name in {"About", "Research", "Faculty Directory", "Departments", "UC San Diego Health"}:
            continue
        if not is_allowed_department_link(name, href, school):
            continue
        departments.append(department_record(school, name, href, "discovered"))
    return departments


def department_record(school: str, name: str, homepage: str, source: str) -> dict:
    normalized_homepage = normalize_homepage_url(homepage)
    return {
        "id": f"ucsd-{slugify(name)}",
        "name": name,
        "school": school,
        "homepage": normalized_homepage,
        "source": source,
        "sourceUrl": EVC_DEPARTMENTS_URL if source == "discovered" else "fallback_snapshot",
    }


def canonical_candidate_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    path = re.sub(r"/{2,}", "/", parsed.path)
    path = path.rstrip("/") if path not in {"", "/"} else path
    return urllib.parse.urlunparse(parsed._replace(path=path, fragment="", query=""))


def candidate_allowed_for_department(url: str, homepage: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    home = urllib.parse.urlparse(homepage)
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.netloc.endswith("ucsd.edu"):
        return False
    if parsed.netloc != home.netloc and not parsed.netloc.endswith(f".{home.netloc.removeprefix('www.')}"):
        return False
    lowered_path = parsed.path.lower()
    if any(f"/{term}" in lowered_path for term in SOURCE_DISCOVERY_EXCLUDED_TERMS):
        return False
    if DIRECTORY_PERSON_PATH_RE.search(lowered_path):
        return False
    return True


def classify_source_link(text: str, url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    if "@" in text:
        return None
    value = f" {text} {parsed.path} ".lower().replace("-", " ").replace("_", " ")
    if not any(term in value for term in ("faculty", "people", "research", "lab", "laborator", "group", "center", "topic")):
        return None
    if any(term in value for term in SOURCE_DISCOVERY_EXCLUDED_TERMS):
        return None
    if any(
        term in value
        for term in (
            "faculty lab",
            "research lab",
            "lab directory",
            "laborator",
            "research group",
            "research groups",
            "centers labs",
            "centers and labs",
            "labs and centers",
            "centers and institutes",
        )
    ):
        return "labs"
    if any(
        term in value
        for term in (
            "research topic",
            "research topics",
            "research area",
            "research areas",
            "research center",
            "research centers",
            "research focus",
        )
    ):
        return "research"
    if "faculty" in value or "people faculty" in value or "faculty directory" in value:
        return "faculty"
    if "research" in value:
        return "research"
    return None


def discovered_candidate_urls(department: dict, timeout: int) -> list[dict]:
    homepage = department["homepage"]
    seed_urls = []
    seen_seeds = set()
    for seed in SOURCE_DISCOVERY_SEEDS:
        url = urllib.parse.urljoin(homepage, seed)
        if url not in seen_seeds:
            seen_seeds.add(url)
            seed_urls.append(url)

    candidates = []
    seen_candidates = set()
    for seed_url in seed_urls:
        try:
            markup = fetch(seed_url, timeout)
        except Exception:
            continue
        parser = LinkTextParser()
        parser.feed(markup)
        for link in parser.links:
            label = clean_text(link.get("text", ""))
            href = canonical_candidate_url(urllib.parse.urljoin(seed_url, link.get("href", "")))
            if href in seen_candidates or not candidate_allowed_for_department(href, homepage):
                continue
            kind = classify_source_link(label, href)
            if not kind:
                continue
            seen_candidates.add(href)
            candidates.append(
                {
                    "kind": kind,
                    "url": href,
                    "verified": False,
                    "discovered": True,
                    "sourceUrl": seed_url,
                    "linkText": label,
                }
            )
    return candidates


def candidate_urls(homepage: str, discovered: list[dict] | None = None) -> list[dict]:
    urls = []
    seen = set()
    for candidate in discovered or []:
        url = canonical_candidate_url(candidate["url"])
        if url in seen:
            continue
        seen.add(url)
        urls.append({**candidate, "url": url})
    for kind, paths in SOURCE_PATHS.items():
        for path in paths:
            url = canonical_candidate_url(urllib.parse.urljoin(homepage, path))
            if url in seen:
                continue
            seen.add(url)
            urls.append({"kind": kind, "url": url, "verified": False})
    return urls


def department_candidate_record(department: dict, timeout: int, offline: bool) -> dict:
    discovered = [] if offline else discovered_candidate_urls(department, timeout)
    return {
        "departmentId": department["id"],
        "department": department["name"],
        "school": department["school"],
        "homepage": department["homepage"],
        "candidates": candidate_urls(department["homepage"], discovered),
    }


def dedupe_departments(departments: list[dict]) -> list[dict]:
    by_key = {}
    for department in departments:
        key = (department["school"], department["name"])
        existing = by_key.get(key)
        if not existing or existing.get("source") != "discovered":
            by_key[key] = department
    return sorted(by_key.values(), key=lambda item: (item["school"], item["name"]))


def fallback_departments() -> list[dict]:
    return [
        department_record(school, name, homepage, "fallback")
        for school, name, homepage in FALLBACK_DEPARTMENTS
    ]


def discover(timeout: int, offline: bool) -> tuple[list[dict], list[str]]:
    warnings = []
    if offline:
        return fallback_departments(), ["offline mode: used embedded official-source snapshot"]

    departments = fallback_departments()
    try:
        departments.extend(parse_departments(fetch(EVC_DEPARTMENTS_URL, timeout), EVC_DEPARTMENTS_URL))
    except Exception as exc:
        warnings.append(f"EVC discovery failed: {type(exc).__name__}: {exc}")
    try:
        departments.extend(parse_departments(fetch(MED_DEPARTMENTS_URL, timeout), MED_DEPARTMENTS_URL, "School of Medicine"))
    except Exception as exc:
        warnings.append(f"School of Medicine discovery failed: {type(exc).__name__}: {exc}")

    if len(departments) <= len(FALLBACK_DEPARTMENTS):
        warnings.append("online discovery added no verified departments; kept fallback snapshot")
    return departments, warnings


def main() -> None:
    offline = "--offline" in sys.argv
    timeout = 8
    departments, warnings = discover(timeout, offline)
    departments = dedupe_departments(departments)
    generated_at = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()
    with concurrent.futures.ThreadPoolExecutor(max_workers=DISCOVERY_WORKERS) as executor:
        candidate_records = list(executor.map(lambda department: department_candidate_record(department, timeout, offline), departments))

    registry = {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "university": {"id": "ucsd", "name": "UC San Diego", "url": "https://ucsd.edu/"},
        "sourcePages": [EVC_DEPARTMENTS_URL, MED_DEPARTMENTS_URL],
        "warnings": warnings,
        "departments": departments,
    }
    candidates = {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "university": registry["university"],
        "departments": candidate_records,
    }

    DEPARTMENTS_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    CANDIDATES_PATH.write_text(json.dumps(candidates, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {DEPARTMENTS_PATH} with {len(departments)} departments")
    print(f"Wrote {CANDIDATES_PATH}")
    for warning in warnings:
        print(f"warning: {warning}")


if __name__ == "__main__":
    main()
