#!/usr/bin/env python3
"""Collect public professor and lab data into the Research Atlas schema.

This is a conservative static-site pipeline. It crawls seed URLs from
data/sources.json, follows a shallow set of faculty/lab/research links, and
marks recruiting as Unknown unless explicit public language is found.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "data" / "sources.json"
DEFAULT_OUTPUT = ROOT / "data" / "research-atlas.json"

USER_AGENT = "research-atlas/0.2 (+https://github.com/)"
MAX_PAGE_BYTES = 900_000
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
WHITESPACE_RE = re.compile(r"\s+")

BAD_TITLE_TERMS = {
    "about",
    "admissions",
    "alumni",
    "contact",
    "directory",
    "events",
    "faculty",
    "faculty profiles",
    "home",
    "jobs",
    "labs",
    "news",
    "people",
    "program",
    "research",
    "resources",
    "students",
}

RESEARCH_KEYWORDS = {
    "Artificial intelligence": ["artificial intelligence", " ai ", "large language model", "llm"],
    "Bioengineering": ["bioengineering", "biomedical engineering", "synthetic biology"],
    "Computer architecture": ["computer architecture", "processor", "hardware"],
    "Computer vision": ["computer vision", "image recognition", "vision"],
    "Cybersecurity": ["security", "cybersecurity", "privacy", "cryptography"],
    "Data science": ["data science", "data-driven", "analytics"],
    "Data systems": ["database", "data management", "data systems", "query processing"],
    "Digital health": ["digital health", "healthcare", "clinical", "medicine"],
    "Distributed systems": ["distributed systems", "cloud", "networked systems"],
    "Human-computer interaction": ["human-computer interaction", "hci", "social computing", "user experience"],
    "Machine learning": ["machine learning", "deep learning", "neural network"],
    "Networking": ["networking", "internet measurement", "wireless", "networked"],
    "Neuroscience": ["neuroscience", "brain", "cognition", "neural"],
    "Robotics": ["robotics", "robot", "autonomous"],
    "Systems": ["systems", "operating systems", "storage systems", "performance"],
}

RECRUITING_POSITIVE = [
    "we are recruiting",
    "is recruiting",
    "currently recruiting",
    "actively recruiting",
    "we are hiring",
    "open positions",
    "positions available",
    "join the lab",
    "apply to join",
    "looking for motivated",
    "seeking graduate students",
    "accepting graduate students",
    "accepting phd students",
    "recruiting phd students",
]

RECRUITING_NEGATIVE = [
    "not accepting students",
    "not accepting new students",
    "not recruiting",
    "no open positions",
    "no positions available",
]


class PageParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title_parts: List[str] = []
        self.meta_description = ""
        self.headings: List[str] = []
        self.text_parts: List[str] = []
        self.links: List[Tuple[str, str]] = []
        self._capture_title = False
        self._capture_heading = False
        self._current_anchor: Optional[Dict[str, List[str]]] = None

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr = {name.lower(): value or "" for name, value in attrs}
        if tag == "title":
            self._capture_title = True
        elif tag in {"h1", "h2"}:
            self._capture_heading = True
        elif tag == "meta":
            name = (attr.get("name") or attr.get("property") or "").lower()
            if name in {"description", "og:description"} and attr.get("content"):
                self.meta_description = clean_text(attr["content"])
        elif tag == "a" and attr.get("href"):
            href = urllib.parse.urljoin(self.base_url, attr["href"])
            self._current_anchor = {"href": [href], "text": []}

    def handle_data(self, data: str) -> None:
        text = clean_text(data)
        if not text:
            return
        if self._capture_title:
            self.title_parts.append(text)
        if self._capture_heading:
            self.headings.append(text)
        if self._current_anchor is not None:
            self._current_anchor["text"].append(text)
        self.text_parts.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._capture_title = False
        elif tag in {"h1", "h2"}:
            self._capture_heading = False
        elif tag == "a" and self._current_anchor is not None:
            href = self._current_anchor["href"][0]
            text = clean_text(" ".join(self._current_anchor["text"])) or href
            self.links.append((text, href))
            self._current_anchor = None

    @property
    def title(self) -> str:
        return clean_text(" ".join(self.title_parts))

    @property
    def text(self) -> str:
        return clean_text(" ".join(self.text_parts))


def clean_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", html.unescape(value or "")).strip()


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return value.strip("-") or "unknown"


def is_http_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def root_host(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def same_site(url: str, base_url: str) -> bool:
    host = root_host(url)
    base = root_host(base_url)
    return host == base or host.endswith("." + base) or base.endswith("." + host)


def fetch_html(url: str, timeout: float) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type.lower() and "text/" not in content_type.lower():
            return ""
        raw = response.read(MAX_PAGE_BYTES + 1)
        charset = response.headers.get_content_charset() or "utf-8"
    return raw[:MAX_PAGE_BYTES].decode(charset, errors="replace")


def robots_allowed(url: str, cache: Dict[str, urllib.robotparser.RobotFileParser], timeout: float) -> bool:
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    if robots_url not in cache:
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)
        try:
            raw = fetch_plain(robots_url, timeout)
            parser.parse(raw.splitlines())
        except Exception:
            parser.parse([])
        cache[robots_url] = parser
    return cache[robots_url].can_fetch(USER_AGENT, url)


def fetch_plain(url: str, timeout: float) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(200_000)
        charset = response.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def likely_person_name(value: str) -> bool:
    cleaned = clean_name(value)
    if not cleaned or cleaned.lower() in BAD_TITLE_TERMS:
        return False
    words = cleaned.split()
    if not 2 <= len(words) <= 5:
        return False
    capitalized = sum(1 for word in words if word[:1].isupper())
    return capitalized >= 2


def clean_name(value: str) -> str:
    value = re.split(r"[|–—-]\s*", value or "")[0]
    value = re.sub(r"\b(Ph\.?D\.?|Professor|Faculty|Profile|UC San Diego|University)\b", "", value, flags=re.I)
    return clean_text(value.strip(" ,:"))


def page_title(parser: PageParser) -> str:
    for heading in parser.headings:
        if clean_text(heading).lower() not in BAD_TITLE_TERMS:
            return clean_text(heading)
    return parser.title


def detect_recruitment(text: str) -> Dict[str, str]:
    lowered = f" {text.lower()} "
    for phrase in RECRUITING_NEGATIVE:
        if phrase in lowered:
            return {"status": "Not recruiting", "text": snippet_for(text, phrase)}
    for phrase in RECRUITING_POSITIVE:
        if phrase in lowered:
            return {"status": "Recruiting", "text": snippet_for(text, phrase)}
    return {"status": "Unknown", "text": ""}


def snippet_for(text: str, phrase: str) -> str:
    lowered = text.lower()
    pos = lowered.find(phrase)
    if pos < 0:
        return ""
    start = max(0, pos - 110)
    end = min(len(text), pos + len(phrase) + 130)
    return clean_text(text[start:end])


def research_areas(text: str, department: str) -> List[str]:
    haystack = f" {text.lower()} "
    areas = []
    for label, needles in RESEARCH_KEYWORDS.items():
        if any(needle in haystack for needle in needles):
            areas.append(label)
    if department and department not in areas:
        areas.append(department)
    return areas or [department or "Research"]


def summary_from(parser: PageParser, fallback: str) -> str:
    if parser.meta_description:
        return parser.meta_description[:280]
    sentences = re.split(r"(?<=[.!?])\s+", parser.text)
    for sentence in sentences:
        lower = sentence.lower()
        if 60 <= len(sentence) <= 260 and any(word in lower for word in ["research", "studies", "focus", "lab", "group"]):
            return clean_text(sentence)
    return fallback


def first_email(text: str) -> str:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else "Not found"


def find_link(parser: PageParser, terms: Iterable[str], external_to: Optional[str] = None) -> str:
    lowered_terms = [term.lower() for term in terms]
    for label, url in parser.links:
        if not is_http_url(url):
            continue
        text = f"{label} {url}".lower()
        if external_to and same_site(url, external_to):
            continue
        if any(term in text for term in lowered_terms):
            return url
    return "Not found"


def extract_professor(
    school_id: str,
    institution: str,
    department: str,
    url: str,
    parser: PageParser,
) -> Optional[Dict[str, object]]:
    title = page_title(parser)
    name = clean_name(title)
    text_lower = parser.text.lower()
    url_lower = url.lower()

    profile_signal = any(token in url_lower for token in ["/faculty", "/people", "/profile", "/profiles"])
    role_signal = any(token in text_lower for token in ["professor", "faculty", "principal investigator"])
    if not (profile_signal and role_signal and likely_person_name(name)):
        return None

    recruitment = detect_recruitment(parser.text)
    scholar = find_link(parser, ["scholar.google", "google scholar"])
    personal = find_link(parser, ["website", "homepage", "personal"], external_to=url)
    lab_url = find_link(parser, [" lab", "laboratory", "research group"])
    lab_affiliation = "Not found"
    if lab_url != "Not found":
        for label, link_url in parser.links:
            if link_url == lab_url:
                lab_affiliation = clean_text(label)
                break

    return {
        "id": f"{school_id}-prof-{slugify(name)}",
        "name": name,
        "institution": institution,
        "department": department,
        "officialProfileUrl": url,
        "personalWebsiteUrl": personal,
        "email": first_email(parser.text),
        "researchAreas": research_areas(parser.text, department),
        "researchSummary": summary_from(parser, f"Public faculty profile for {name}. Research summary needs manual review."),
        "googleScholarUrl": scholar,
        "labAffiliation": lab_affiliation,
        "labAffiliationUrl": lab_url,
        "recruitingStatus": recruitment["status"],
        "recruitingEvidence": {
            "text": recruitment["text"],
            "url": url if recruitment["text"] else "",
        },
        "sourceUrls": [url],
        "lastVerified": dt.date.today().isoformat(),
    }


def extract_lab(
    school_id: str,
    institution: str,
    department: str,
    url: str,
    parser: PageParser,
    intent: str,
) -> Optional[Dict[str, object]]:
    title = page_title(parser)
    text_lower = parser.text.lower()
    url_lower = url.lower()
    lab_signal = any(token in f"{title.lower()} {url_lower}" for token in ["lab", "laboratory", "research group", "center"])
    research_signal = any(token in text_lower for token in ["research", "principal investigator", "lab", "laboratory"])
    if not ((intent == "lab" or lab_signal) and research_signal):
        return None

    name = clean_text(title)
    if not name or name.lower() in BAD_TITLE_TERMS:
        name = "Research group"
    if len(name) > 90:
        name = name[:87].rstrip() + "..."

    recruitment = detect_recruitment(parser.text)
    pi = extract_pi(parser.text)
    pi_profile = find_link(parser, [pi]) if pi != "Not found" else "Not found"

    return {
        "id": f"{school_id}-lab-{slugify(name)}",
        "labName": name,
        "institution": institution,
        "department": department,
        "labWebsiteUrl": url,
        "principalInvestigator": pi,
        "principalInvestigatorProfileUrl": pi_profile,
        "researchAreas": research_areas(parser.text, department),
        "description": summary_from(parser, f"Public lab or research group page for {name}. Description needs manual review."),
        "contactEmail": first_email(parser.text),
        "recruitingStatus": recruitment["status"],
        "recruitingEvidence": {
            "text": recruitment["text"],
            "url": url if recruitment["text"] else "",
        },
        "sourceUrls": [url],
        "lastVerified": dt.date.today().isoformat(),
    }


def extract_pi(text: str) -> str:
    patterns = [
        r"(?:Principal Investigator|PI|Lab Director|Director)\s*:?\s+([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,3})",
        r"([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,3}),?\s+(?:Principal Investigator|PI)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return clean_name(match.group(1))
    return "Not found"


def should_follow(label: str, url: str, base_url: str) -> Optional[str]:
    if not is_http_url(url) or not same_site(url, base_url):
        return None
    combined = f"{label} {url}".lower()
    if any(skip in combined for skip in ["calendar", "facebook", "instagram", "linkedin", "youtube", ".pdf"]):
        return None
    if any(token in combined for token in ["faculty", "people", "profile", "professor"]):
        return "faculty"
    if any(token in combined for token in ["lab", "laboratory", "research-group", "research group", "center"]):
        return "lab"
    return None


def merge_record(existing: Dict[str, object], incoming: Dict[str, object]) -> Dict[str, object]:
    merged = dict(existing)
    for key, value in incoming.items():
        if key == "sourceUrls":
            merged[key] = sorted(set(existing.get(key, []) + incoming.get(key, [])))
        elif key == "researchAreas":
            merged[key] = sorted(set(existing.get(key, []) + incoming.get(key, [])))
        elif is_missing_value(merged.get(key)):
            merged[key] = value
    return merged


def is_missing_value(value: object) -> bool:
    return value is None or (isinstance(value, str) and value in {"Not found", "Unknown", ""})


def add_unique(values: Iterable[str], new_values: Iterable[str]) -> List[str]:
    return sorted(set([value for value in values if value] + [value for value in new_values if value]))


def enrich_personal_sites(
    professors: Dict[str, Dict[str, object]],
    robots_cache: Dict[str, urllib.robotparser.RobotFileParser],
    args: argparse.Namespace,
) -> None:
    if args.personal_limit <= 0:
        return

    enriched = 0
    for record in professors.values():
        if enriched >= args.personal_limit:
            return
        url = str(record.get("personalWebsiteUrl", ""))
        if is_missing_value(url) or not is_http_url(url):
            continue
        if args.respect_robots and not robots_allowed(url, robots_cache, args.timeout):
            continue

        try:
            markup = fetch_html(url, args.timeout)
        except (urllib.error.URLError, TimeoutError, ValueError):
            continue
        if not markup:
            continue

        parser = PageParser(url)
        parser.feed(markup)
        enriched += 1
        record["sourceUrls"] = add_unique(record.get("sourceUrls", []), [url])
        record["researchAreas"] = add_unique(record.get("researchAreas", []), research_areas(parser.text, str(record["department"])))

        email = first_email(parser.text)
        if is_missing_value(record.get("email")) and email != "Not found":
            record["email"] = email

        scholar = find_link(parser, ["scholar.google", "google scholar"])
        if is_missing_value(record.get("googleScholarUrl")) and scholar != "Not found":
            record["googleScholarUrl"] = scholar

        lab_url = find_link(parser, [" lab", "laboratory", "research group"])
        if is_missing_value(record.get("labAffiliationUrl")) and lab_url != "Not found":
            record["labAffiliationUrl"] = lab_url
            for label, link_url in parser.links:
                if link_url == lab_url:
                    record["labAffiliation"] = clean_text(label)
                    break

        summary = summary_from(parser, "")
        current_summary = str(record.get("researchSummary", ""))
        if summary and ("needs manual review" in current_summary.lower() or len(current_summary) < 80):
            record["researchSummary"] = summary

        recruitment = detect_recruitment(parser.text)
        if record.get("recruitingStatus") == "Unknown" and recruitment["status"] != "Unknown":
            record["recruitingStatus"] = recruitment["status"]
            record["recruitingEvidence"] = {"text": recruitment["text"], "url": url}


def crawl(config: Dict[str, object], args: argparse.Namespace) -> Dict[str, List[Dict[str, object]]]:
    robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}
    professors: Dict[str, Dict[str, object]] = {}
    labs: Dict[str, Dict[str, object]] = {}
    queue: List[Tuple[str, str, str, str, str, int]] = []

    for school in config.get("schools", []):
        school_id = school.get("id", "school")
        institution = school.get("name", school_id)
        base_url = school.get("baseUrl", "")
        for department in school.get("departments", []):
            department_name = department.get("name", "Unknown")
            for url in department.get("facultyUrls", []):
                queue.append((url, school_id, institution, department_name, base_url or url, 0))
            for url in department.get("labUrls", []):
                queue.append((url, school_id, institution, department_name, base_url or url, 0))

    seen = set()
    pages = 0
    while queue and pages < args.max_pages:
        url, school_id, institution, department, base_url, depth = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        if args.respect_robots and not robots_allowed(url, robots_cache, args.timeout):
            print(f"robots blocked {url}")
            continue

        try:
            markup = fetch_html(url, args.timeout)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            print(f"fetch failed {url}: {exc}")
            continue
        if not markup:
            continue

        pages += 1
        parser = PageParser(url)
        parser.feed(markup)

        professor = extract_professor(school_id, institution, department, url, parser)
        if professor:
            record_id = professor["id"]
            professors[record_id] = merge_record(professors.get(record_id, professor), professor)

        intent = "lab" if any(token in url.lower() for token in ["lab", "research", "group", "center"]) else "faculty"
        lab = extract_lab(school_id, institution, department, url, parser, intent)
        if lab:
            record_id = lab["id"]
            labs[record_id] = merge_record(labs.get(record_id, lab), lab)

        if depth < args.max_depth:
            for label, link_url in parser.links:
                next_intent = should_follow(label, link_url, base_url or url)
                if next_intent and link_url not in seen:
                    queue.append((link_url, school_id, institution, department, base_url or url, depth + 1))

        if args.delay:
            time.sleep(args.delay)

    enrich_personal_sites(professors, robots_cache, args)

    return {
        "professors": sorted(professors.values(), key=lambda item: item["name"]),
        "labs": sorted(labs.values(), key=lambda item: item["labName"]),
    }


def build_dataset(records: Dict[str, List[Dict[str, object]]]) -> Dict[str, object]:
    return {
        "schemaVersion": "2.0.0",
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "datasetName": "Research Atlas collected dataset",
        "description": "Generated from public source URLs by scripts/collect_research_data.py.",
        "collectionPolicy": {
            "publicPagesOnly": True,
            "recruitingClaimsRequireExplicitEvidence": True,
            "unknownMeansNoExplicitStatementCaptured": True,
            "studentPrivacyBoundary": "Do not collect private rosters, login-only pages, or non-public student information.",
        },
        "professors": records["professors"],
        "labs": records["labs"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-pages", type=int, default=80)
    parser.add_argument("--max-depth", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=8)
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument("--personal-limit", type=int, default=25)
    parser.add_argument("--no-robots", dest="respect_robots", action="store_false")
    parser.add_argument("--write-empty", action="store_true", help="Allow overwriting output with an empty dataset.")
    parser.set_defaults(respect_robots=True)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    records = crawl(config, args)
    count = len(records["professors"]) + len(records["labs"])
    if count == 0 and args.out.exists() and not args.write_empty:
        print("No records collected; keeping existing output to avoid breaking the static site.")
        return

    dataset = build_dataset(records)
    args.out.write_text(json.dumps(dataset, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(records['professors'])} professors and {len(records['labs'])} labs to {args.out}")


if __name__ == "__main__":
    main()
