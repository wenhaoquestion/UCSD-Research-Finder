#!/usr/bin/env python3
"""Enrich professor records with public contact and academic metadata.

The script is intentionally provenance-first:

- it only writes confirmed Google Scholar profile URLs when a public page
  explicitly links to scholar.google.com;
- it adds a Google Scholar author-search URL for every professor as a fallback;
- it uses OpenAlex for citation counts and recent publications;
- it fills missing UCSD emails from public UCSD pages or UCSD Profiles vCards.
"""

from __future__ import annotations

import argparse
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
DEFAULT_CACHE = ROOT / "data" / "ucsd" / "professor-enrichment-cache.json"

MISSING = "Not found"
UNKNOWN = "Unknown"
UCSD_OPENALEX_ID = "I36258959"
UCSD_ROR = "https://ror.org/0168r3w48"
USER_AGENT = "ResearchAtlas/1.0 (public metadata enrichment; contact: no-reply@example.org)"

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"^https?://", re.I)
GENERIC_EMAIL_LOCALS = {
    "ctri-support",
    "communication",
    "feedback",
    "info",
    "support",
    "webmaster",
}
PERSONAL_LABEL_RE = re.compile(
    r"\b(website|web site|home\s?page|homepage|personal|lab|laboratory|research group)\b",
    re.I,
)
SKIP_PERSONAL_HOSTS = {
    "catalog.ucsd.edu",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "profiles.ucsd.edu",
    "researcherprofiles.org",
    "scholar.google.com",
    "twitter.com",
    "x.com",
    "youtube.com",
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self._href = ""
        self._text_parts: list[str] = []
        self.title = ""
        self._in_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "a":
            self._href = attr.get("href", "")
            self._text_parts = []
        elif tag.lower() == "title":
            self._in_title = True
            self._title_parts = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text_parts.append(data)
        if self._in_title:
            self._title_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href:
            self.links.append(
                {
                    "href": self._href,
                    "text": clean_text(" ".join(self._text_parts)),
                }
            )
            self._href = ""
            self._text_parts = []
        elif tag.lower() == "title":
            self.title = clean_text(" ".join(self._title_parts))
            self._in_title = False


def clean_text(value: str) -> str:
    return html.unescape(str(value or "")).replace("\xa0", " ").strip()


def is_known(value: Any) -> bool:
    return bool(value and value not in {MISSING, UNKNOWN})


def normalize_person_name(name: str) -> str:
    name = re.sub(r"\([^)]*\)", " ", name)
    name = re.sub(r"\b(?:PhD|MD|M\.D\.|Dr\.|Professor|Prof\.)\b", " ", name, flags=re.I)
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^A-Za-z .'-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def name_tokens(name: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z]+", normalize_person_name(name))]


def name_slug_for_search(name: str) -> str:
    return " ".join(name_tokens(name))


def candidate_profile_slugs(name: str) -> list[str]:
    tokens = name_tokens(name)
    if len(tokens) < 2:
        return []

    parenthetical = re.findall(r"\(([^)]+)\)", name)
    first = tokens[0]
    last = tokens[-1]
    middle = tokens[1:-1]

    candidates = [
        f"{first}.{last}",
        f"{first}.{'.'.join(middle)}.{last}" if middle else "",
        f"{first}.{middle[0][0]}.{last}" if middle else "",
    ]
    for alias in parenthetical:
        alias_tokens = name_tokens(alias)
        if alias_tokens:
            candidates.append(f"{alias_tokens[0]}.{last}")

    return unique(value for value in candidates if value)


def unique(values: Any) -> list[Any]:
    seen = set()
    out = []
    for value in values:
        key = json.dumps(value, sort_keys=True) if isinstance(value, dict) else str(value)
        if not value or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def request_json(url: str, timeout: int = 20) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def request_text(url: str, timeout: int = 12, max_bytes: int = 700_000) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(max_bytes).decode("utf-8", "ignore")


def request_vcard_text(url: str, timeout: int = 12) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/vcard,text/x-vcard,text/plain,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(40_000).decode("utf-8", "ignore")


def absolute_url(base_url: str, url: str) -> str:
    return urllib.parse.urljoin(base_url, clean_text(url))


def host_for(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")


def allowed_email(email: str) -> bool:
    local, _, domain = email.lower().partition("@")
    if local in GENERIC_EMAIL_LOCALS:
        return False
    return domain.endswith("ucsd.edu")


def best_email_from_text(text: str) -> str:
    for email in unique(EMAIL_RE.findall(text)):
        if allowed_email(email):
            return email
    return ""


def likely_same_person(profile_name: str, professor_name: str) -> bool:
    profile_token_list = name_tokens(profile_name)
    professor_token_list = name_tokens(professor_name)
    profile_tokens = set(profile_token_list)
    professor_tokens = set(professor_token_list)
    if not profile_tokens or not professor_tokens:
        return False
    if profile_tokens == professor_tokens:
        return True
    first_last = {professor_token_list[0], professor_token_list[-1]}
    return bool(first_last <= profile_tokens or first_last <= professor_tokens)


def vcard_url_from_profile(profile_url: str, markup: str) -> str:
    match = re.search(r'href="([^"]*vcard\.aspx\?subject=[^"]+)"', markup, re.I)
    if not match:
        return ""
    return absolute_url(profile_url, match.group(1))


def parse_vcard(value: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in value.splitlines():
        if line.startswith("FN:"):
            out["name"] = clean_text(line.split(":", 1)[1])
        elif line.startswith("EMAIL"):
            out["email"] = clean_text(line.split(":", 1)[-1])
        elif line.startswith("TITLE:"):
            out["title"] = clean_text(line.split(":", 1)[1])
    return out


def profile_contact_from_url(professor: dict[str, Any], profile_url: str) -> dict[str, Any]:
    try:
        markup = request_text(profile_url)
    except Exception as exc:
        return {"checked": False, "url": profile_url, "reason": type(exc).__name__}

    parser = LinkParser()
    parser.feed(markup)
    profile_name = parser.title.split("|", 1)[0].replace("UCSD Profiles", "").strip()
    vcard_url = vcard_url_from_profile(profile_url, markup)
    vcard = {}
    if vcard_url:
        try:
            vcard = parse_vcard(request_vcard_text(vcard_url))
        except Exception:
            vcard = {}

    email = vcard.get("email") or best_email_from_text(markup)
    matched_name = vcard.get("name") or profile_name
    if matched_name and not likely_same_person(matched_name, str(professor.get("name", ""))):
        return {
            "checked": True,
            "matched": False,
            "url": profile_url,
            "matchedName": matched_name,
        }

    return {
        "checked": True,
        "matched": True,
        "url": profile_url,
        "vcardUrl": vcard_url,
        "matchedName": matched_name,
        "email": email if allowed_email(email) else "",
        "title": vcard.get("title", ""),
    }


def discover_profile_contact(professor: dict[str, Any], cache: dict[str, Any], delay: float) -> dict[str, Any]:
    record_id = str(professor.get("id"))
    if record_id in cache:
        return cache[record_id]

    urls = []
    official = str(professor.get("officialProfileUrl", ""))
    if "profiles.ucsd.edu/" in official:
        urls.append(official)
    for slug in candidate_profile_slugs(str(professor.get("name", ""))):
        urls.append(f"https://profiles.ucsd.edu/{slug}")

    for url in unique(urls):
        result = profile_contact_from_url(professor, url)
        if result.get("matched") and result.get("email"):
            cache[record_id] = result
            if delay:
                time.sleep(delay)
            return result
        if delay:
            time.sleep(delay)

    cache[record_id] = {"checked": True, "matched": False, "urlsTried": urls}
    return cache[record_id]


def parse_links_for_contact(url: str) -> dict[str, Any]:
    try:
        markup = request_text(url)
    except Exception as exc:
        return {"checked": False, "url": url, "reason": type(exc).__name__}

    parser = LinkParser()
    parser.feed(markup)
    scholar = ""
    personal = ""
    for link in parser.links:
        href = absolute_url(url, link["href"])
        label = link["text"]
        host = host_for(href)
        if "scholar.google." in host and not scholar:
            scholar = href
        if not personal and PERSONAL_LABEL_RE.search(label) and not any(host.endswith(skip) for skip in SKIP_PERSONAL_HOSTS):
            personal = href

    return {
        "checked": True,
        "url": url,
        "email": best_email_from_text(markup),
        "googleScholarUrl": scholar,
        "personalWebsiteUrl": personal,
    }


def page_can_support_person(professor: dict[str, Any], url: str) -> bool:
    if not is_known(url):
        return False
    url = str(url)
    if "catalog.ucsd.edu" in url:
        return False
    if "profiles.ucsd.edu/" in url:
        return True
    official = str(professor.get("officialProfileUrl") or "")
    if url == official and URL_RE.search(url):
        return True
    path = urllib.parse.urlparse(url).path.lower()
    tokens = name_tokens(str(professor.get("name", "")))
    if len(tokens) < 2:
        return False
    return tokens[0] in path and tokens[-1] in path


def openalex_author_search_url(name: str) -> str:
    params = urllib.parse.urlencode(
        {
            "search": name,
            "filter": f"last_known_institutions.id:{UCSD_OPENALEX_ID}",
            "per-page": "5",
            "select": "id,display_name,works_count,cited_by_count,summary_stats,last_known_institutions,ids",
        }
    )
    return f"https://api.openalex.org/authors?{params}"


def openalex_work_search_url(author_id: str) -> str:
    short_id = author_id.rsplit("/", 1)[-1]
    params = urllib.parse.urlencode(
        {
            "filter": f"authorships.author.id:{short_id}",
            "sort": "publication_date:desc",
            "per-page": "5",
            "select": "id,display_name,publication_year,publication_date,cited_by_count,primary_location,doi",
        }
    )
    return f"https://api.openalex.org/works?{params}"


def author_match_score(candidate: dict[str, Any], professor: dict[str, Any]) -> float:
    professor_tokens = set(name_tokens(str(professor.get("name", ""))))
    candidate_tokens = set(name_tokens(str(candidate.get("display_name", ""))))
    if not professor_tokens or not candidate_tokens:
        return 0.0
    overlap = len(professor_tokens & candidate_tokens) / max(len(professor_tokens), len(candidate_tokens))
    if name_tokens(str(professor.get("name", "")))[-1:] == name_tokens(str(candidate.get("display_name", "")))[-1:]:
        overlap += 0.2
    if any(inst.get("ror") == UCSD_ROR for inst in candidate.get("last_known_institutions", []) or []):
        overlap += 0.2
    return min(overlap, 1.0)


def publication_from_work(work: dict[str, Any]) -> dict[str, Any]:
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    return {
        "title": clean_text(work.get("display_name") or MISSING),
        "year": work.get("publication_year") or UNKNOWN,
        "publicationDate": work.get("publication_date") or UNKNOWN,
        "citationCount": work.get("cited_by_count", 0),
        "venue": clean_text(source.get("display_name") or UNKNOWN),
        "url": work.get("doi") or location.get("landing_page_url") or work.get("id") or MISSING,
        "source": "OpenAlex",
    }


def fetch_openalex_profile(professor: dict[str, Any], cache: dict[str, Any], delay: float) -> dict[str, Any]:
    record_id = str(professor.get("id"))
    if record_id in cache:
        return cache[record_id]

    name = str(professor.get("name", ""))
    try:
        authors = request_json(openalex_author_search_url(name)).get("results", [])
    except Exception as exc:
        cache[record_id] = {"checked": False, "source": "OpenAlex", "reason": type(exc).__name__}
        return cache[record_id]

    best = None
    best_score = 0.0
    for author in authors:
        score = author_match_score(author, professor)
        if score > best_score:
            best = author
            best_score = score

    if not best or best_score < 0.55:
        cache[record_id] = {
            "checked": True,
            "matched": False,
            "source": "OpenAlex",
            "matchConfidence": round(best_score, 3),
        }
        if delay:
            time.sleep(delay)
        return cache[record_id]

    if delay:
        time.sleep(delay)

    try:
        works = request_json(openalex_work_search_url(best["id"])).get("results", [])
    except Exception:
        works = []

    stats = best.get("summary_stats") or {}
    cache[record_id] = {
        "checked": True,
        "matched": True,
        "source": "OpenAlex",
        "openAlexAuthorId": best.get("id", ""),
        "openAlexUrl": best.get("id", ""),
        "matchedName": best.get("display_name", ""),
        "matchConfidence": round(best_score, 3),
        "worksCount": best.get("works_count", 0),
        "citationCount": best.get("cited_by_count", 0),
        "hIndex": stats.get("h_index", UNKNOWN),
        "i10Index": stats.get("i10_index", UNKNOWN),
        "recentPublications": [publication_from_work(work) for work in works],
        "lastVerified": dt.date.today().isoformat(),
    }
    if delay:
        time.sleep(delay)
    return cache[record_id]


def google_scholar_search_url(professor: dict[str, Any]) -> str:
    query = f"{professor.get('name', '')} {professor.get('institution', 'UC San Diego')}"
    params = urllib.parse.urlencode({"view_op": "search_authors", "mauthors": query, "hl": "en"})
    return f"https://scholar.google.com/citations?{params}"


def linkedin_search_url(professor: dict[str, Any]) -> str:
    query = f'site:linkedin.com/in "{professor.get("name", "")}" "UC San Diego"'
    return f"https://www.google.com/search?{urllib.parse.urlencode({'q': query})}"


def apply_enrichment(professor: dict[str, Any], contact: dict[str, Any], academic: dict[str, Any]) -> dict[str, Any]:
    updated = dict(professor)
    source_urls = list(updated.get("sourceUrls") or [])

    current_scholar = str(updated.get("googleScholarUrl", MISSING))
    if is_known(current_scholar) and "scholar.google." not in current_scholar:
        updated["possibleScholarSourceUrl"] = current_scholar
        source_urls.append(current_scholar)
        updated["googleScholarUrl"] = MISSING

    updated["googleScholarSearchUrl"] = google_scholar_search_url(updated)
    updated["linkedinSearchUrl"] = linkedin_search_url(updated)

    if contact.get("matched") or contact.get("pageMatched"):
        if not is_known(updated.get("email")) and contact.get("email"):
            updated["email"] = contact["email"]
            if contact.get("emailSourceUrl"):
                source_urls.append(contact["emailSourceUrl"])
        if not is_known(updated.get("personalWebsiteUrl")) and contact.get("personalWebsiteUrl"):
            updated["personalWebsiteUrl"] = contact["personalWebsiteUrl"]
            source_urls.append(contact["personalWebsiteUrl"])
        if contact.get("googleScholarUrl") and "scholar.google." in contact["googleScholarUrl"]:
            updated["googleScholarUrl"] = contact["googleScholarUrl"]
            source_urls.append(contact["googleScholarUrl"])

    if contact.get("matched"):
        if "profiles.ucsd.edu/" in contact.get("url", ""):
            source_urls.append(contact["url"])
            if not is_known(updated.get("officialProfileUrl")) or "catalog.ucsd.edu" in str(updated.get("officialProfileUrl")):
                updated["officialProfileUrl"] = contact["url"]

    if academic.get("matched"):
        updated["academicProfile"] = {
            "source": "OpenAlex",
            "openAlexAuthorId": academic.get("openAlexAuthorId", ""),
            "openAlexUrl": academic.get("openAlexUrl", ""),
            "matchedName": academic.get("matchedName", ""),
            "matchConfidence": academic.get("matchConfidence", 0),
            "worksCount": academic.get("worksCount", 0),
            "citationCount": academic.get("citationCount", 0),
            "hIndex": academic.get("hIndex", UNKNOWN),
            "i10Index": academic.get("i10Index", UNKNOWN),
            "recentPublications": academic.get("recentPublications", []),
            "lastVerified": academic.get("lastVerified", dt.date.today().isoformat()),
        }
        if academic.get("openAlexUrl"):
            source_urls.append(academic["openAlexUrl"])
    else:
        updated.setdefault(
            "academicProfile",
            {
                "source": "OpenAlex",
                "openAlexAuthorId": MISSING,
                "openAlexUrl": MISSING,
                "matchedName": MISSING,
                "matchConfidence": academic.get("matchConfidence", 0),
                "worksCount": UNKNOWN,
                "citationCount": UNKNOWN,
                "hIndex": UNKNOWN,
                "i10Index": UNKNOWN,
                "recentPublications": [],
                "lastVerified": dt.date.today().isoformat(),
            },
        )

    updated["sourceUrls"] = unique(url for url in source_urls if URL_RE.search(str(url)))
    return updated


def load_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schemaVersion": 1, "contacts": {}, "academic": {}, "profilePages": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def write_cache(path: Path, cache: dict[str, Any]) -> None:
    cache["generatedAt"] = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()
    path.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_ATLAS)
    parser.add_argument("--out", type=Path, default=DEFAULT_ATLAS)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--academic-limit", type=int, default=0, help="0 means all professors")
    parser.add_argument("--contact-limit", type=int, default=0, help="0 means all missing contacts")
    parser.add_argument("--missing-email-only", action="store_true", help="Only spend contact lookups on records missing email")
    parser.add_argument("--skip-openalex", action="store_true")
    parser.add_argument("--skip-contact", action="store_true")
    parser.add_argument("--delay", type=float, default=0.08)
    parser.add_argument("--save-every", type=int, default=50)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    cache = load_cache(args.cache)
    contacts_cache = cache.setdefault("contacts", {})
    academic_cache = cache.setdefault("academic", {})
    page_cache = cache.setdefault("profilePages", {})

    professors = data.get("professors", [])
    academic_remaining = args.academic_limit or len(professors)
    contact_remaining = args.contact_limit or len(professors)
    enriched = []

    for index, professor in enumerate(professors, start=1):
        contact: dict[str, Any] = {}
        academic: dict[str, Any] = {}

        if not args.skip_contact and contact_remaining > 0:
            if args.missing_email_only:
                needs_contact = not is_known(professor.get("email"))
            else:
                needs_contact = (
                    not is_known(professor.get("email"))
                    or not is_known(professor.get("personalWebsiteUrl"))
                    or not is_known(professor.get("googleScholarUrl"))
                )
            if needs_contact:
                urls = unique([professor.get("officialProfileUrl"), *(professor.get("sourceUrls") or [])])
                for url in urls[:4]:
                    if not page_can_support_person(professor, str(url)) or not str(url).startswith(("http://", "https://")):
                        continue
                    if url not in page_cache:
                        page_cache[url] = parse_links_for_contact(str(url))
                        if args.delay:
                            time.sleep(args.delay)
                    page_result = page_cache.get(url, {})
                    contact = {
                        **contact,
                        **{
                            key: value
                            for key, value in page_result.items()
                            if value and key in {"email", "googleScholarUrl", "personalWebsiteUrl"}
                        },
                    }
                    if any(contact.get(key) for key in {"email", "googleScholarUrl", "personalWebsiteUrl"}):
                        contact["pageMatched"] = True
                        contact["emailSourceUrl"] = str(url)
                if not contact.get("email") and not is_known(professor.get("email")):
                    profile_result = discover_profile_contact(professor, contacts_cache, args.delay)
                    contact = {**contact, **profile_result}
                contact_remaining -= 1

        if not args.skip_openalex and academic_remaining > 0:
            academic = fetch_openalex_profile(professor, academic_cache, args.delay)
            academic_remaining -= 1

        enriched.append(apply_enrichment(professor, contact, academic))

        if index % args.save_every == 0:
            write_cache(args.cache, cache)
            print(f"[{index}/{len(professors)}] cached enrichment", flush=True)

    data["professors"] = enriched
    data["generatedAt"] = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()
    write_cache(args.cache, cache)
    args.out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Enriched {len(enriched)} professors -> {args.out}")


if __name__ == "__main__":
    main()
