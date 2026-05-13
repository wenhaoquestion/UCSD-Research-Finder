#!/usr/bin/env python3
"""Enrich Math/Physics professor pages and personal research sites.

Math and Physics often do not maintain department-level lab directories. The
useful student-facing target is frequently a professor's personal site, group
site, or profile research page. This script consumes public department APIs,
optionally expands to public web search, and writes high-confidence personal
research-site records into the canonical Research Atlas dataset.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import html
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ATLAS = ROOT / "data" / "research-atlas.json"
DEFAULT_CACHE = ROOT / "data" / "ucsd" / "physical-sciences-site-cache.json"
DEFAULT_CANDIDATES = ROOT / "data" / "ucsd" / "physical-sciences-site-candidates.json"

USER_AGENT = "ResearchAtlas/1.0 physical-sciences-public-site-enrichment"
MISSING = "Not found"
UNKNOWN = "Unknown"
TARGET_DEPARTMENTS = {"Mathematics", "Physics"}
MAX_PAGE_BYTES = 900_000

MATH_PROFILE_EXPORT_URL = "https://math.ucsd.edu/export/people/faculty"
MATH_EAH_URL = "https://soeapp.ucsd.edu/tools/eah/department.php"
MATH_DEPARTMENT_CODE = "000212"
PHYSICS_PROFILE_LIST_URL = "https://physics.ucsd.edu/api/profiles/faculty/000220"
PHYSICS_PROFILE_URL = "https://physics.ucsd.edu/api/profile/{profile_id}/000220"

MATH_FACULTY_JOB_CODES = {
    "001096",
    "001100",
    "001143",
    "001200",
    "001243",
    "001300",
    "001343",
    "001603",
    "001607",
    "001680",
}

JOB_TITLES = {
    "001096": "Professor",
    "001100": "Professor",
    "001143": "Professor",
    "001200": "Associate Professor",
    "001243": "Associate Professor",
    "001300": "Assistant Professor",
    "001343": "Assistant Professor",
    "001603": "Teaching Professor",
    "001607": "Associate Teaching Professor",
    "001680": "Assistant Teaching Professor",
}

BAD_PROFESSOR_NAMES = {
    "Administrative Staff",
}

SKIP_HOSTS = {
    "catalog.ucsd.edu",
    "evc.ucsd.edu",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "profiles.ucsd.edu",
    "researchgate.net",
    "scholar.google.com",
    "twitter.com",
    "x.com",
    "youtube.com",
}

BROAD_PATH_RE = re.compile(
    r"/(?:about|academic|admissions?|alumni|calendar|careers?|contact|course|"
    r"education|events?|facilities|giving|news|people/faculty|resources|"
    r"search|shops-recharge-facilities|students)(?:/|$)",
    re.I,
)

PHYSICS_BROAD_RESEARCH_RE = re.compile(r"^/(?:Research|research)/(?:[^/?#]+)$", re.I)
OLD_PROFILE_PATH_RE = re.compile(r"/(?:people/profile|fac_staff/fac_profile|faculty/profile)", re.I)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
WHITESPACE_RE = re.compile(r"\s+")
TAG_RE = re.compile(r"<[^>]+>")

AREA_KEYWORDS = {
    "Algebra": [" algebra ", "algebraic"],
    "Algebraic geometry": ["algebraic geometry"],
    "Applied mathematics": ["applied math", "applied mathematics"],
    "Astrophysics": ["astrophysics", "cosmology", "galaxy", "galaxies"],
    "Atomic, molecular, and optical physics": ["atomic", "molecular", "optical", "amo"],
    "Biological physics": ["biological physics", "biophysics", "cell", "protein"],
    "Combinatorics": ["combinatorics"],
    "Condensed matter physics": ["condensed matter", "superconduct", "quantum material"],
    "Differential equations": ["differential equation", "pde", "partial differential"],
    "Geometry and topology": ["geometry", "topology", "geometric"],
    "High energy physics": ["high energy", "particle physics", "lhc", "higgs", "cms experiment"],
    "Mathematical biology": ["mathematical biology", "biology"],
    "Mathematical physics": ["mathematical physics"],
    "Number theory": ["number theory", "automorphic", "arithmetic"],
    "Optimization": ["optimization"],
    "Plasma physics": ["plasma"],
    "Probability theory": ["probability", "stochastic"],
    "Quantum physics": ["quantum"],
    "Representation theory": ["representation theory"],
    "Statistics": ["statistics", "statistical", "data science"],
}

RECRUITING_POSITIVE = [
    "we are recruiting",
    "currently recruiting",
    "open positions",
    "positions available",
    "apply to join",
    "accepting graduate students",
    "accepting phd students",
    "recruiting graduate students",
    "recruiting phd students",
]

RECRUITING_NEGATIVE = [
    "not accepting students",
    "not accepting new students",
    "not recruiting",
    "no open positions",
    "no positions available",
]


class SimpleHTMLParser(HTMLParser):
    def __init__(self, base_url: str = "") -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title_parts: list[str] = []
        self.meta_descriptions: list[str] = []
        self.heading_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[dict[str, str]] = []
        self._capture_title = False
        self._capture_heading = False
        self._anchor_href = ""
        self._anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "title":
            self._capture_title = True
        elif tag.lower() in {"h1", "h2", "h3"}:
            self._capture_heading = True
        elif tag.lower() == "meta":
            name = (attr.get("name") or attr.get("property") or "").lower()
            if name in {"description", "og:description"} and attr.get("content"):
                self.meta_descriptions.append(clean_text(attr["content"]))
        elif tag.lower() == "a" and attr.get("href"):
            self._anchor_href = attr["href"]
            self._anchor_text = []

    def handle_data(self, data: str) -> None:
        text = clean_text(data)
        if not text:
            return
        if self._capture_title:
            self.title_parts.append(text)
        if self._capture_heading:
            self.heading_parts.append(text)
        if self._anchor_href:
            self._anchor_text.append(text)
        self.text_parts.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._capture_title = False
        elif tag.lower() in {"h1", "h2", "h3"}:
            self._capture_heading = False
        elif tag.lower() == "a" and self._anchor_href:
            self.links.append(
                {
                    "href": absolute_url(self.base_url, self._anchor_href),
                    "text": clean_text(" ".join(self._anchor_text)),
                }
            )
            self._anchor_href = ""
            self._anchor_text = []

    @property
    def title(self) -> str:
        return clean_text(" ".join(self.title_parts))

    @property
    def text(self) -> str:
        return clean_text(" ".join(self.text_parts))


def clean_text(value: Any) -> str:
    return WHITESPACE_RE.sub(" ", html.unescape(str(value or "").replace("\xa0", " "))).strip()


def strip_tags(value: str) -> str:
    return clean_text(TAG_RE.sub(" ", value or ""))


def is_known(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value and value.strip().lower() not in {"", MISSING.lower(), UNKNOWN.lower()})
    return value is not None and value != []


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", normalize_ascii(value).lower())
    return value.strip("-") or "unknown"


def normalize_ascii(value: str) -> str:
    value = html.unescape(value or "").replace("\u2019", "'").replace("\u2013", "-").replace("\u2014", "-")
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


def name_tokens(name: str) -> list[str]:
    value = normalize_ascii(name)
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"\b(?:Dr|Prof|Professor|PhD|Ph\.D)\b\.?", " ", value, flags=re.I)
    return [token.lower() for token in re.findall(r"[A-Za-z]+", value)]


def canonical_name(name: str) -> str:
    return " ".join(name_tokens(name))


def compact_name_key(name: str) -> str:
    return "".join(name_tokens(name))


def names_match(left: str, right: str) -> bool:
    left_tokens = name_tokens(left)
    right_tokens = name_tokens(right)
    if not left_tokens or not right_tokens:
        return False
    if left_tokens == right_tokens:
        return True
    if left_tokens[0] == right_tokens[0] and left_tokens[-1] == right_tokens[-1]:
        return True
    if left_tokens[0] == right_tokens[0] and set(left_tokens[1:]) & set(right_tokens[1:]):
        return True
    return compact_name_key(left) == compact_name_key(right)


def unique(values: list[Any]) -> list[Any]:
    seen = set()
    out = []
    for value in values:
        key = json.dumps(value, sort_keys=True) if isinstance(value, dict) else str(value)
        if value in {None, ""} or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def absolute_url(base_url: str, url: str) -> str:
    value = clean_text(url)
    if value.startswith("//"):
        return "https:" + value
    return urllib.parse.urljoin(base_url, value)


def normalize_url(url: str) -> str:
    value = clean_text(url)
    if not value:
        return ""
    if value.startswith("//"):
        value = "https:" + value
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return ""
    if "." not in parsed.netloc:
        return ""
    parsed = parsed._replace(fragment="")
    return urllib.parse.urlunparse(parsed)


def host_for(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")


def path_for(url: str) -> str:
    return urllib.parse.urlparse(url).path or "/"


def is_skipped_host(url: str) -> bool:
    host = host_for(url)
    return any(host == skip or host.endswith("." + skip) for skip in SKIP_HOSTS)


def request_text(url: str, *, timeout: int = 15, data: bytes | None = None) -> str:
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json,text/plain;q=0.9,*/*;q=0.8",
        },
    )
    if data is not None:
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_PAGE_BYTES + 1)
        charset = response.headers.get_content_charset() or "utf-8"
    return raw[:MAX_PAGE_BYTES].decode(charset, errors="replace")


def request_json(url: str, *, timeout: int = 15, data: bytes | None = None) -> Any:
    return json.loads(request_text(url, timeout=timeout, data=data))


def cached_fetch(cache: dict[str, Any], namespace: str, key: str, loader) -> Any:
    bucket = cache.setdefault(namespace, {})
    if key not in bucket:
        bucket[key] = loader()
    return bucket[key]


def fetch_page(cache: dict[str, Any], url: str) -> dict[str, Any]:
    normalized = normalize_url(url)
    if not normalized:
        return {"ok": False, "url": url, "reason": "invalid_url"}

    def load() -> dict[str, Any]:
        try:
            markup = request_text(normalized, timeout=12)
        except Exception as exc:
            return {"ok": False, "url": normalized, "reason": type(exc).__name__}
        parser = SimpleHTMLParser(normalized)
        parser.feed(markup)
        return {
            "ok": True,
            "url": normalized,
            "title": parser.title,
            "headings": parser.heading_parts[:8],
            "metaDescriptions": parser.meta_descriptions[:4],
            "text": parser.text[:12000],
            "links": parser.links[:200],
        }

    return cached_fetch(cache, "pages", normalized, load)


def infer_research_areas(*values: str, department: str) -> list[str]:
    haystack = f" {' '.join(clean_text(value).lower() for value in values)} "
    areas = []
    for label, needles in AREA_KEYWORDS.items():
        if any(needle in haystack for needle in needles):
            areas.append(label)
    areas.append(department)
    return unique(areas)


def snippet_for(text: str, phrase: str) -> str:
    lowered = text.lower()
    pos = lowered.find(phrase)
    if pos < 0:
        return ""
    start = max(0, pos - 120)
    end = min(len(text), pos + len(phrase) + 140)
    return clean_text(text[start:end])


def detect_recruitment(text: str, url: str) -> dict[str, str]:
    lowered = f" {text.lower()} "
    for phrase in RECRUITING_NEGATIVE:
        if phrase in lowered:
            return {"status": "Not recruiting", "text": snippet_for(text, phrase), "url": url}
    for phrase in RECRUITING_POSITIVE:
        if phrase in lowered:
            return {"status": "Recruiting", "text": snippet_for(text, phrase), "url": url}
    return {"status": UNKNOWN, "text": "", "url": ""}


def first_email(*values: str) -> str:
    for value in values:
        for email in EMAIL_RE.findall(value or ""):
            if not email.lower().startswith(("info@", "support@", "webmaster@")):
                return email.lower()
    return MISSING


def low_information_summary(summary: str) -> bool:
    lowered = clean_text(summary).lower()
    return (
        not lowered
        or "needs manual review" in lowered
        or "catalog faculty listing" in lowered
        or "queued for full directory enrichment" in lowered
        or len(lowered) < 80
    )


def summary_from_text(name: str, department: str, text: str, fallback: str = "") -> str:
    plain = strip_tags(text)
    sentences = re.split(r"(?<=[.!?])\s+", plain)
    for sentence in sentences:
        lowered = sentence.lower()
        if 70 <= len(sentence) <= 320 and any(
            token in lowered for token in ["research", "study", "group", "lab", "work", "interested"]
        ):
            return clean_text(sentence)
    return fallback or f"Public {department} research profile for {name}."


def page_has_person_signal(page: dict[str, Any], name: str, email: str = "") -> bool:
    text = f"{page.get('title', '')} {' '.join(page.get('headings', []))} {page.get('text', '')}".lower()
    tokens = name_tokens(name)
    if len(tokens) >= 2:
        if " ".join(tokens) in text:
            return True
        if tokens[0] in text and tokens[-1] in text:
            return True
        if tokens[0] in text and set(tokens[1:]) & set(re.findall(r"[a-z]+", text)):
            return True
        title = str(page.get("title", "")).lower()
        if any(token in title for token in tokens[1:]) and any(marker in title for marker in ["lab", "group", "home page"]):
            return True
    if email and email.lower() in text:
        return True
    return False


def site_kind_for_professor(url: str, name: str, department: str) -> str:
    normalized = normalize_url(url)
    if not normalized or is_skipped_host(normalized):
        return "skip"
    parsed = urllib.parse.urlparse(normalized)
    host = host_for(normalized)
    path = parsed.path
    lowered = f"{host} {path}".lower()

    if BROAD_PATH_RE.search(path):
        return "skip"
    if department == "Physics" and host == "physics.ucsd.edu" and PHYSICS_BROAD_RESEARCH_RE.search(path):
        return "broad_research_area"
    if OLD_PROFILE_PATH_RE.search(path):
        return "profile"
    if "lab" in lowered or "group" in lowered:
        return "research_group"
    if "~" in path:
        return "personal_site"

    tokens = name_tokens(name)
    if tokens:
        first, last = tokens[0], tokens[-1]
        compact = compact_name_key(name)
        path_slug = slugify(path)
        host_slug = slugify(host)
        if last in host_slug or compact in host_slug or last in path_slug or compact in path_slug:
            return "personal_site"
        if len(first) > 1 and f"{first[0]}{last}" in f"{host_slug}-{path_slug}":
            return "personal_site"

    if host.endswith("github.io") or "sites.google.com" in host:
        return "personal_site"
    if host.endswith("ucsd.edu") and department.lower() in lowered:
        return "research_group"
    return "candidate"


def should_publish_research_site(
    professor: dict[str, Any],
    url: str,
    page: dict[str, Any],
    source: str,
) -> tuple[bool, str]:
    department = str(professor.get("department", ""))
    name = str(professor.get("name", ""))
    kind = site_kind_for_professor(url, name, department)
    if kind in {"skip", "profile", "broad_research_area"}:
        return False, kind
    if source in {"math_api", "physics_api"} and kind in {"personal_site", "research_group"}:
        return True, kind
    if not page.get("ok"):
        return source in {"math_api", "physics_api"} and kind in {"personal_site", "research_group"}, kind

    text = f"{page.get('title', '')} {' '.join(page.get('headings', []))} {page.get('text', '')}".lower()
    research_signal = any(
        token in text
        for token in ["research", "publication", "preprint", "students", "group", "lab", "projects", "teaching"]
    )
    person_signal = page_has_person_signal(page, name, str(professor.get("email", "")))
    if kind == "candidate":
        return bool(research_signal and person_signal), kind
    return bool(research_signal and (person_signal or kind in {"personal_site", "research_group"})), kind


def load_math_records(cache: dict[str, Any]) -> list[dict[str, Any]]:
    profile_rows = cached_fetch(cache, "api", MATH_PROFILE_EXPORT_URL, lambda: request_json(MATH_PROFILE_EXPORT_URL))
    profile_by_email = {row.get("field_work_email", "").lower(): row for row in profile_rows}
    post_data = urllib.parse.urlencode({"department_code[]": MATH_DEPARTMENT_CODE}).encode()
    people = cached_fetch(cache, "api", "math_eah_faculty", lambda: request_json(MATH_EAH_URL, data=post_data))

    records = []
    seen = set()
    for person in people:
        if person.get("employee_class") != "Academic: Faculty":
            continue
        if person.get("employee_status") in {"Retired", "Terminated"}:
            continue
        job_code = str(person.get("job_code", ""))
        if job_code not in MATH_FACULTY_JOB_CODES:
            continue
        email = str(person.get("identity_email_address_current") or person.get("employee_work_email_address_current") or "").lower()
        if not email or email in seen:
            continue
        seen.add(email)
        profile = profile_by_email.get(email, {})
        first = clean_text(person.get("employee_preferred_first_name_current", ""))
        last = clean_text(person.get("employee_preferred_last_name_current", ""))
        name = clean_text(f"{first} {last}")
        profile_url = absolute_url("https://www.math.ucsd.edu/", profile.get("view_node_1", ""))
        records.append(
            {
                "source": "math_api",
                "name": name,
                "email": email,
                "title": JOB_TITLES.get(job_code, clean_text(person.get("job_code_description", "")) or "Faculty"),
                "department": "Mathematics",
                "profileUrl": profile_url,
                "website": normalize_url(profile.get("field_website", "")),
                "researchArea": clean_text(profile.get("field_primary_research_area", "")),
                "sourceUrls": [MATH_PROFILE_EXPORT_URL, "https://www.math.ucsd.edu/people/faculty/"],
            }
        )
    return records


def load_physics_records(cache: dict[str, Any], workers: int) -> list[dict[str, Any]]:
    profiles = cached_fetch(cache, "api", PHYSICS_PROFILE_LIST_URL, lambda: request_json(PHYSICS_PROFILE_LIST_URL))

    def detail_for(profile: dict[str, Any]) -> dict[str, Any]:
        email = str(profile.get("identity_email_address_current") or profile.get("email") or "").lower()
        profile_id = email.split("@", 1)[0]
        url = PHYSICS_PROFILE_URL.format(profile_id=urllib.parse.quote(profile_id))

        def load() -> Any:
            try:
                return request_json(url)
            except Exception as exc:
                return {"associations": [], "publications": [], "news": [], "_error": type(exc).__name__}

        detail = cached_fetch(cache, "api", url, load)
        associations = detail.get("associations") or []
        base = dict(profile)
        if associations:
            base.update(associations[0])
        first = clean_text(base.get("first_name", ""))
        last = clean_text(base.get("last_name", ""))
        website = normalize_url(base.get("website", ""))
        research = strip_tags(clean_text(base.get("research", "")))
        profile_url = f"https://physics.ucsd.edu/people/profile?id={profile_id}"
        return {
            "source": "physics_api",
            "name": clean_text(f"{first} {last}"),
            "email": email,
            "title": clean_text(base.get("display_title", "")) or JOB_TITLES.get(str(base.get("job_code", "")), "Faculty"),
            "department": "Physics",
            "profileUrl": profile_url,
            "website": website,
            "research": research,
            "researchHtml": clean_text(base.get("research", "")),
            "researchGroup": clean_text(base.get("research_group", "")),
            "sourceUrls": [PHYSICS_PROFILE_LIST_URL, profile_url],
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(detail_for, profiles))


def record_key(record: dict[str, Any]) -> str:
    return canonical_name(str(record.get("name", "")))


def build_professor_indexes(professors: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_name: dict[str, dict[str, Any]] = {}
    by_email: dict[str, dict[str, Any]] = {}
    for professor in professors:
        by_name.setdefault(f"{professor.get('department', '')}:{record_key(professor)}", professor)
        email = str(professor.get("email", "")).lower()
        if is_known(email):
            by_email[f"{professor.get('department', '')}:{email}"] = professor
    return by_name, by_email


def find_professor_match(
    professors: list[dict[str, Any]],
    by_name: dict[str, dict[str, Any]],
    by_email: dict[str, dict[str, Any]],
    source_record: dict[str, Any],
) -> dict[str, Any] | None:
    email = str(source_record.get("email", "")).lower()
    name = str(source_record.get("name", ""))
    department = str(source_record.get("department", ""))
    email_key = f"{department}:{email}"
    name_key = f"{department}:{canonical_name(name)}"
    if email and email_key in by_email:
        return by_email[email_key]
    if name_key in by_name:
        return by_name[name_key]
    for professor in professors:
        if professor.get("department") != department:
            continue
        if names_match(name, str(professor.get("name", ""))):
            return professor
    return None


def professor_id(institution_slug: str, department: str, name: str) -> str:
    return f"{institution_slug}-{slugify(department)}-{slugify(name)}"


def ensure_professor(
    professors: list[dict[str, Any]],
    by_name: dict[str, dict[str, Any]],
    by_email: dict[str, dict[str, Any]],
    source_record: dict[str, Any],
) -> dict[str, Any]:
    name = source_record.get("name", "")
    email = str(source_record.get("email", "")).lower()
    professor = find_professor_match(professors, by_name, by_email, source_record)

    if professor:
        by_name[f"{source_record.get('department', '')}:{canonical_name(name)}"] = professor
        if source_record.get("email"):
            by_email[f"{source_record.get('department', '')}:{str(source_record['email']).lower()}"] = professor
        return professor

    today = dt.date.today().isoformat()
    department = source_record["department"]
    profile_url = source_record.get("profileUrl") or MISSING
    areas = infer_research_areas(
        source_record.get("researchArea", ""),
        source_record.get("research", ""),
        source_record.get("researchGroup", ""),
        department=department,
    )
    professor = {
        "id": professor_id("ucsd", department, name),
        "name": name,
        "institution": "University of California San Diego",
        "department": department,
        "officialProfileUrl": profile_url,
        "personalWebsiteUrl": MISSING,
        "email": email or MISSING,
        "researchAreas": areas,
        "researchSummary": summary_from_text(name, department, source_record.get("research", ""), ""),
        "googleScholarUrl": MISSING,
        "labAffiliation": MISSING,
        "labAffiliationUrl": MISSING,
        "recruitingStatus": UNKNOWN,
        "recruitingEvidence": {"text": "", "url": ""},
        "sourceUrls": unique([*(source_record.get("sourceUrls") or []), profile_url, source_record.get("website", "")]),
        "lastVerified": today,
        "legacyKind": "public_department_api",
    }
    professors.append(professor)
    by_name[f"{department}:{canonical_name(name)}"] = professor
    if source_record.get("email"):
        by_email[f"{department}:{str(source_record['email']).lower()}"] = professor
    return professor


def apply_source_record(
    professor: dict[str, Any],
    source_record: dict[str, Any],
    cache: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    today = dt.date.today().isoformat()
    source_urls = list(professor.get("sourceUrls") or [])
    source_urls.extend(source_record.get("sourceUrls") or [])
    profile_url = source_record.get("profileUrl", "")
    website = normalize_url(source_record.get("website", ""))

    if is_known(profile_url) and (not is_known(professor.get("officialProfileUrl")) or "catalog.ucsd.edu" in str(professor.get("officialProfileUrl"))):
        professor["officialProfileUrl"] = profile_url
    if is_known(source_record.get("email")) and not is_known(professor.get("email")):
        professor["email"] = source_record["email"]

    source_text = " ".join(
        [
            str(source_record.get("researchArea", "")),
            str(source_record.get("research", "")),
            str(source_record.get("researchGroup", "")),
        ]
    )
    professor["researchAreas"] = unique(
        list(professor.get("researchAreas") or [])
        + infer_research_areas(source_text, department=str(professor.get("department", "")))
    )
    if low_information_summary(str(professor.get("researchSummary", ""))):
        professor["researchSummary"] = summary_from_text(
            str(professor.get("name", "")),
            str(professor.get("department", "")),
            source_record.get("research", ""),
            f"Public {professor.get('department')} faculty profile for {professor.get('name')}.",
        )

    if website:
        page = fetch_page(cache, website)
        publish, kind = should_publish_research_site(professor, website, page, str(source_record.get("source", "")))
        candidate = {
            "professorId": professor.get("id", ""),
            "name": professor.get("name", ""),
            "department": professor.get("department", ""),
            "url": website,
            "source": source_record.get("source", ""),
            "kind": kind,
            "accepted": publish,
            "title": page.get("title", ""),
            "reason": page.get("reason", ""),
        }
        candidates.append(candidate)
        current_personal = normalize_url(str(professor.get("personalWebsiteUrl", "")))
        if publish or kind in {"personal_site", "research_group"}:
            professor["personalWebsiteUrl"] = website
        elif current_personal == website and source_record.get("source") == "physics_api":
            professor["personalWebsiteUrl"] = MISSING
            if normalize_url(str(professor.get("labAffiliationUrl", ""))) == website:
                professor["labAffiliationUrl"] = MISSING
                professor["labAffiliation"] = MISSING
            source_urls = [url for url in source_urls if canonical_url_key(str(url)) != canonical_url_key(website)]
        if publish:
            if not is_known(professor.get("labAffiliationUrl")):
                professor["labAffiliationUrl"] = website
                professor["labAffiliation"] = research_site_name(str(professor.get("name", "")), kind)
            source_urls.append(website)

    professor["sourceUrls"] = unique([url for url in source_urls if normalize_url(str(url))])
    professor["lastVerified"] = today
    return professor


def research_site_name(name: str, kind: str) -> str:
    if kind == "research_group":
        return f"{name} Research Group"
    return f"{name} Research Site"


def make_lab_record(
    professor: dict[str, Any],
    website: str,
    cache: dict[str, Any],
    candidate_kind: str,
) -> dict[str, Any]:
    today = dt.date.today().isoformat()
    page = fetch_page(cache, website)
    page_text = clean_text(
        " ".join(
            [
                page.get("title", ""),
                " ".join(page.get("headings", [])),
                " ".join(page.get("metaDescriptions", [])),
                page.get("text", ""),
            ]
        )
    )
    name = str(professor.get("name", ""))
    department = str(professor.get("department", ""))
    lab_name = research_site_name(name, candidate_kind)
    areas = unique(list(professor.get("researchAreas") or []) + infer_research_areas(page_text, department=department))
    description = summary_from_text(
        name,
        department,
        page_text,
        f"Personal research site for {name}, a {department} faculty member at UC San Diego.",
    )
    contact_email = first_email(page_text, str(professor.get("email", "")))
    recruitment = detect_recruitment(page_text, website)
    if recruitment["status"] != UNKNOWN and not recruitment["text"]:
        recruitment = {"status": UNKNOWN, "text": "", "url": ""}
    source_urls = unique([website, professor.get("officialProfileUrl", ""), *(professor.get("sourceUrls") or [])])
    return {
        "id": f"ucsd-{slugify(department)}-research-site-{slugify(name)}",
        "labName": lab_name,
        "institution": professor.get("institution", "University of California San Diego"),
        "department": department,
        "labWebsiteUrl": website,
        "principalInvestigator": name,
        "principalInvestigatorProfileUrl": professor.get("officialProfileUrl", MISSING),
        "researchAreas": areas or [department],
        "description": description,
        "contactEmail": contact_email,
        "recruitingStatus": recruitment["status"],
        "recruitingEvidence": {"text": recruitment["text"], "url": recruitment["url"]},
        "sourceUrls": [url for url in source_urls if normalize_url(str(url))],
        "lastVerified": today,
        "recordSubtype": "personal_research_site" if candidate_kind == "personal_site" else "research_group",
        "legacyKind": "physical_sciences_personal_site",
    }


def parse_duckduckgo_results(markup: str, base_url: str) -> list[str]:
    parser = SimpleHTMLParser(base_url)
    parser.feed(markup)
    results = []
    for link in parser.links:
        text = f"{link.get('text', '')} {link.get('href', '')}".lower()
        href = link.get("href", "")
        if "result__a" not in text and "duckduckgo.com/l/" not in href and "uddg=" not in href:
            continue
        parsed = urllib.parse.urlparse(href)
        query = urllib.parse.parse_qs(parsed.query)
        target = query.get("uddg", [href])[0]
        target = normalize_url(urllib.parse.unquote(target))
        if target:
            results.append(target)
    return unique(results)


def search_candidates(professor: dict[str, Any], cache: dict[str, Any], max_results: int) -> list[dict[str, Any]]:
    name = str(professor.get("name", ""))
    department = str(professor.get("department", ""))
    queries = [
        f'"{name}" "UCSD" "{department}" research',
        f'"{name}" "UC San Diego" "{department}" lab',
        f'"{name}" "UC San Diego" homepage',
    ]
    if department == "Mathematics":
        queries.insert(0, f'site:math.ucsd.edu/~ "{name}"')
        queries.insert(1, f'site:mathweb.ucsd.edu/~ "{name}"')
    elif department == "Physics":
        queries.insert(0, f'site:physics.ucsd.edu/~ "{name}"')
        queries.insert(1, f'"{name}" "UCSD" physics group')

    results = []
    for query in queries:
        search_url = f"https://duckduckgo.com/html/?{urllib.parse.urlencode({'q': query})}"

        def load() -> dict[str, Any]:
            try:
                return {"ok": True, "markup": request_text(search_url, timeout=15)}
            except Exception as exc:
                return {"ok": False, "reason": type(exc).__name__}

        payload = cached_fetch(cache, "search", search_url, load)
        if not payload.get("ok"):
            continue
        for url in parse_duckduckgo_results(payload.get("markup", ""), search_url):
            if is_skipped_host(url):
                continue
            page = fetch_page(cache, url)
            score = score_search_candidate(professor, url, page)
            results.append(
                {
                    "professorId": professor.get("id", ""),
                    "name": name,
                    "department": department,
                    "url": url,
                    "source": "duckduckgo",
                    "query": query,
                    "score": score,
                    "kind": site_kind_for_professor(url, name, department),
                    "title": page.get("title", ""),
                    "accepted": score >= 70,
                    "reason": page.get("reason", ""),
                }
            )
        if len(results) >= max_results:
            break
        time.sleep(0.2)
    return sorted(results, key=lambda item: item.get("score", 0), reverse=True)[:max_results]


def score_search_candidate(professor: dict[str, Any], url: str, page: dict[str, Any]) -> int:
    name = str(professor.get("name", ""))
    department = str(professor.get("department", ""))
    email = str(professor.get("email", ""))
    kind = site_kind_for_professor(url, name, department)
    if kind in {"skip", "profile", "broad_research_area"}:
        return 0
    score = 0
    if kind in {"personal_site", "research_group"}:
        score += 30
    host = host_for(url)
    if host.endswith("ucsd.edu") or "sites.google.com" in host or host.endswith("github.io"):
        score += 15
    if page.get("ok"):
        text = f"{page.get('title', '')} {' '.join(page.get('headings', []))} {page.get('text', '')}".lower()
        tokens = name_tokens(name)
        if tokens and " ".join(tokens) in text:
            score += 35
        elif len(tokens) >= 2 and tokens[0] in text and tokens[-1] in text:
            score += 25
        if email and email.lower() in text:
            score += 20
        if "ucsd" in text or "uc san diego" in text:
            score += 10
        if department.lower() in text:
            score += 10
        if any(token in text for token in ["research", "publication", "preprint", "students", "group", "lab"]):
            score += 15
    return min(score, 100)


def merge_lab_records(existing: dict[str, Any] | None, incoming: dict[str, Any]) -> dict[str, Any]:
    if not existing:
        return incoming
    merged = dict(existing)
    for key, value in incoming.items():
        if key == "sourceUrls":
            merged[key] = unique(list(existing.get(key, [])) + list(value or []))
        elif key == "researchAreas":
            merged[key] = unique(list(existing.get(key, [])) + list(value or []))
        elif key == "recruitingStatus":
            evidence = incoming.get("recruitingEvidence") or {}
            if value != UNKNOWN and evidence.get("text") and evidence.get("url"):
                merged[key] = value
                merged["recruitingEvidence"] = evidence
        elif key == "recruitingEvidence":
            continue
        elif not is_known(merged.get(key)) and is_known(value):
            merged[key] = value
        elif key in {"description", "contactEmail", "recordSubtype", "legacyKind"}:
            if key == "description" and len(str(value)) > len(str(merged.get(key, ""))):
                merged[key] = value
            elif key != "description" and not is_known(merged.get(key)):
                merged[key] = value
    return merged


def clean_recruiting_claim(record: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(record)
    evidence = cleaned.get("recruitingEvidence") or {}
    if cleaned.get("recruitingStatus") in {"Recruiting", "Not recruiting"} and not (
        isinstance(evidence, dict) and evidence.get("text") and normalize_url(str(evidence.get("url", "")))
    ):
        cleaned["recruitingStatus"] = UNKNOWN
        cleaned["recruitingEvidence"] = {"text": "", "url": ""}
    return cleaned


def canonical_url_key(url: str) -> str:
    normalized = normalize_url(url).lower().rstrip("/")
    parsed = urllib.parse.urlparse(normalized)
    if not parsed.netloc:
        return ""
    host = parsed.netloc.removeprefix("www.")
    path = parsed.path.rstrip("/")
    return f"{host}{path}"


def professor_quality(record: dict[str, Any]) -> tuple[int, int, int, int]:
    profile = str(record.get("officialProfileUrl", ""))
    return (
        1 if is_known(record.get("email")) else 0,
        1 if is_known(record.get("personalWebsiteUrl")) else 0,
        1 if profile and "catalog.ucsd.edu" not in profile else 0,
        len(str(record.get("researchSummary", ""))),
    )


def merge_professor_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    best = max(records, key=professor_quality)
    merged = dict(best)
    for record in sorted(records, key=professor_quality, reverse=True):
        for field in [
            "officialProfileUrl",
            "personalWebsiteUrl",
            "email",
            "googleScholarUrl",
            "googleScholarSearchUrl",
            "linkedinSearchUrl",
            "possibleScholarSourceUrl",
            "labAffiliation",
            "labAffiliationUrl",
        ]:
            if not is_known(merged.get(field)) and is_known(record.get(field)):
                merged[field] = record[field]
        if not isinstance(merged.get("academicProfile"), dict) and isinstance(record.get("academicProfile"), dict):
            merged["academicProfile"] = record["academicProfile"]
        elif isinstance(record.get("academicProfile"), dict):
            current_url = str((merged.get("academicProfile") or {}).get("openAlexUrl", ""))
            incoming_url = str(record["academicProfile"].get("openAlexUrl", ""))
            if not is_known(current_url) and is_known(incoming_url):
                merged["academicProfile"] = record["academicProfile"]
        if len(str(record.get("researchSummary", ""))) > len(str(merged.get("researchSummary", ""))):
            merged["researchSummary"] = record["researchSummary"]

    merged["researchAreas"] = unique([area for record in records for area in record.get("researchAreas", [])])
    merged["sourceUrls"] = unique([url for record in records for url in record.get("sourceUrls", []) if normalize_url(str(url))])
    if any(record.get("recruitingStatus") == "Recruiting" for record in records):
        recruiting = next(record for record in records if record.get("recruitingStatus") == "Recruiting")
        merged["recruitingStatus"] = "Recruiting"
        merged["recruitingEvidence"] = recruiting.get("recruitingEvidence", {"text": "", "url": ""})
    return merged


def professor_group_key(record: dict[str, Any]) -> str:
    if record.get("department") not in TARGET_DEPARTMENTS:
        return f"id:{record.get('id', '')}"
    email = str(record.get("email", "")).lower()
    if is_known(email):
        return f"email:{record.get('department', '')}:{email}"
    tokens = name_tokens(str(record.get("name", "")))
    if len(tokens) >= 2:
        return f"name:{record.get('department')}:{tokens[0]}:{tokens[-1]}"
    return f"id:{record.get('id', '')}"


def consolidate_target_professors(professors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for professor in professors:
        groups.setdefault(professor_group_key(professor), []).append(professor)

    consolidated = []
    seen_ids: dict[str, int] = {}
    for group in groups.values():
        merged = merge_professor_records(group) if len(group) > 1 else dict(group[0])
        record_id = str(merged.get("id", ""))
        if record_id in seen_ids:
            seen_ids[record_id] += 1
            merged["id"] = f"{record_id}-{seen_ids[record_id]}"
        else:
            seen_ids[record_id] = 1
        consolidated.append(merged)
    return consolidated


def remove_bad_target_professors(professors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for professor in professors:
        if professor.get("department") in TARGET_DEPARTMENTS and professor.get("name") in BAD_PROFESSOR_NAMES:
            continue
        official = str(professor.get("officialProfileUrl", ""))
        if professor.get("department") == "Physics" and "/people/administrative-staff" in official:
            continue
        out.append(professor)
    return out


def update_dataset(data: dict[str, Any], args: argparse.Namespace, cache: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    professors = consolidate_target_professors(
        [clean_recruiting_claim(record) for record in remove_bad_target_professors(list(data.get("professors") or []))]
    )
    by_name, by_email = build_professor_indexes(professors)
    candidates: list[dict[str, Any]] = []

    source_records = []
    source_records.extend(load_math_records(cache))
    source_records.extend(load_physics_records(cache, args.workers))

    for source_record in source_records:
        professor = ensure_professor(professors, by_name, by_email, source_record)
        apply_source_record(professor, source_record, cache, candidates)

    if args.use_search:
        missing = [
            professor
            for professor in professors
            if professor.get("department") in TARGET_DEPARTMENTS and not is_known(professor.get("personalWebsiteUrl"))
        ][: args.search_limit]
        for index, professor in enumerate(missing, start=1):
            print(f"[search {index}/{len(missing)}] {professor.get('name')}", flush=True)
            found = search_candidates(professor, cache, max_results=5)
            candidates.extend(found)
            accepted = next((candidate for candidate in found if candidate.get("accepted")), None)
            if accepted:
                url = accepted["url"]
                professor["personalWebsiteUrl"] = url
                professor["labAffiliationUrl"] = url
                professor["labAffiliation"] = research_site_name(str(professor.get("name", "")), str(accepted.get("kind", "personal_site")))
                professor["sourceUrls"] = unique(list(professor.get("sourceUrls") or []) + [url])

    professors = consolidate_target_professors(professors)
    lab_by_id = {
        lab.get("id"): clean_recruiting_claim(lab)
        for lab in data.get("labs") or []
        if lab.get("legacyKind") != "physical_sciences_personal_site"
    }
    lab_by_url = {
        (str(lab.get("department", "")), canonical_url_key(str(lab.get("labWebsiteUrl", "")))): lab.get("id")
        for lab in lab_by_id.values()
        if canonical_url_key(str(lab.get("labWebsiteUrl", "")))
    }
    for professor in professors:
        if professor.get("department") not in TARGET_DEPARTMENTS:
            continue
        website = normalize_url(str(professor.get("labAffiliationUrl") or professor.get("personalWebsiteUrl") or ""))
        if not website:
            continue
        page = fetch_page(cache, website)
        publish, kind = should_publish_research_site(professor, website, page, "final")
        if not publish:
            continue
        lab = make_lab_record(professor, website, cache, kind)
        url_key = canonical_url_key(website)
        existing_id = lab_by_url.get((str(professor.get("department", "")), url_key))
        if existing_id:
            lab_by_id[existing_id] = merge_lab_records(lab_by_id.get(existing_id), lab)
        else:
            lab_by_id[lab["id"]] = merge_lab_records(lab_by_id.get(lab["id"]), lab)
            lab_by_url[(str(professor.get("department", "")), url_key)] = lab["id"]

    data["professors"] = sorted(professors, key=lambda item: (item.get("department", ""), item.get("name", "")))
    data["labs"] = sorted(lab_by_id.values(), key=lambda item: (item.get("department", ""), item.get("labName", "")))
    data["generatedAt"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    return data, candidates


def load_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schemaVersion": 1, "api": {}, "pages": {}, "search": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"schemaVersion": 1, "api": {}, "pages": {}, "search": {}}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_ATLAS)
    parser.add_argument("--out", type=Path, default=DEFAULT_ATLAS)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--candidates-out", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--use-search", action="store_true")
    parser.add_argument("--search-limit", type=int, default=40)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    cache = load_cache(args.cache)
    updated, candidates = update_dataset(data, args, cache)
    cache["generatedAt"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    write_json(args.out, updated)
    write_json(args.cache, cache)
    write_json(
        args.candidates_out,
        {
            "schemaVersion": 1,
            "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
            "candidates": sorted(candidates, key=lambda item: (item.get("department", ""), item.get("name", ""), item.get("url", ""))),
        },
    )

    target_professors = [p for p in updated["professors"] if p.get("department") in TARGET_DEPARTMENTS]
    target_labs = [lab for lab in updated["labs"] if lab.get("department") in TARGET_DEPARTMENTS]
    personal_count = sum(1 for p in target_professors if is_known(p.get("personalWebsiteUrl")))
    print(
        f"Wrote {len(updated['professors'])} professors and {len(updated['labs'])} labs. "
        f"Math/Physics personal sites: {personal_count}/{len(target_professors)}; "
        f"Math/Physics lab-like records: {len(target_labs)}."
    )


if __name__ == "__main__":
    main()
