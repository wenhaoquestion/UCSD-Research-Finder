#!/usr/bin/env python3
"""Refresh public UCSD faculty/lab evidence without modifying the canonical atlas.

Network reads are cached, robots-aware, size/time bounded and rate limited per
host. Only the page's main content can support a faculty relationship. Discovery
is deliberately separate from proof: navigation links and URL-name guesses never
establish a PI/lab relationship. A fetch timestamp does not mean a page's content
was recently authored, nor does an official profile establish current employment.
An existing --out is the complete incremental baseline: partial refreshes retain
unattempted observations and independently sourced evidence, including backfills.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import copy
import datetime as dt
import hashlib
import json
import os
import re
import tempfile
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

from lab_destinations import nonlab_destination_reason

ROOT = Path(__file__).resolve().parents[1]
UA = "ResearchAtlasEvidenceBot/2.0 (public academic directory verification)"
MISSING = "Not found"
LAB_RE = re.compile(r"\b(?:lab(?:orator(?:y|ies))?|(?:research )?group)\b", re.I)
GENERIC_LAB = re.compile(r"^(?:research |faculty |our |all |department )?(?:labs?|laboratory|laboratories|(?:research )?groups?)(?: directory| websites?)?$", re.I)
GENERIC_LAB_LINK = re.compile(r"(?:my |our |the |visit |view )?(?:research )?(?:lab(?:oratory)?|research group)(?: (?:web ?site|site|homepage|page))?", re.I)
EMAIL_RE = re.compile(r"[\w.+%-]+@[\w.-]+\.[a-zA-Z]{2,}")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


def clean(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def normalized(s):
    return clean(re.sub(r"[^a-z0-9 ]", " ", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()))


def now():
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def observed_date(timestamp):
    """Date-only UI fields follow UC San Diego's local calendar, not UTC."""
    return dt.datetime.fromisoformat(timestamp).astimezone(ZoneInfo("America/Los_Angeles")).date().isoformat()


def canonical_url(s):
    p = urllib.parse.urlsplit(s)
    if p.scheme not in {"http", "https"}:
        return ""
    # UCSD supports TLS; old crawls contain many obsolete http links.
    scheme = "https" if (p.hostname or "").endswith("ucsd.edu") else p.scheme
    host = p.netloc.lower()
    if host in {"www.cogsci.ucsd.edu", "www.jacobsschool.ucsd.edu"}:
        host = host.removeprefix("www.")
    return urllib.parse.urlunsplit((scheme, host, p.path or "/", p.query, ""))


class Node:
    def __init__(self, tag="document", attrs=None, parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs or []), parent, []
        self._text_cache = None

    def excluded(self):
        # ASP.NET profile sites wrap the entire page in a form. Exclude search
        # controls, not all form descendants, or their biographies disappear.
        if self.tag in {"script", "style", "nav", "footer", "aside", "noscript", "button", "select", "option"}:
            return True
        if self.attrs.get("role") in {"navigation", "complementary", "contentinfo", "search"}:
            return True
        classes = (self.attrs.get("class", "") + " " + self.attrs.get("id", "")).lower()
        if "propertygroupbibliographic" in classes:
            return True
        # Layout classes such as body.layout-one-sidebar describe the page,
        # not a sidebar subtree. Never discard that entire document.
        return self.tag not in {"html", "body"} and any(re.match(r"^(?:navbar|sidebar|breadcrumb|menu|footer|cookie|site-footer)(?:$|[_-])", c) or re.search(r"(?:--footer|masterpagefooter)", c) for c in classes.split())

    def walk(self):
        if self.excluded():
            return
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()

    def text(self):
        if self.excluded():
            return ""
        if self._text_cache is None:
            self._text_cache = clean(" ".join(x.text() if isinstance(x, Node) else x for x in self.children))
        return self._text_cache


class DOM(HTMLParser):
    def __init__(self, markup):
        super().__init__(convert_charrefs=True)
        self.root = self.current = Node()
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, [(k, v or "") for k, v in attrs], self.current)
        self.current.children.append(node)
        if tag not in VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        p = self.current
        while p.parent and p.tag != tag:
            p = p.parent
        if p.tag == tag and p.parent:
            self.current = p.parent

    def handle_data(self, data):
        self.current.children.append(data)

    def main(self):
        nodes = list(self.root.walk())
        for predicate in [
            lambda n: n.attrs.get("id") == "ctl00_divProfilesContentMain",
            lambda n: "main-section" in n.attrs.get("class", "").split(),
            lambda n: n.tag == "main" or n.attrs.get("role") == "main",
            lambda n: n.attrs.get("id") in {"content", "main-content", "mainContent", "content-main"},
            lambda n: "profile-content" in n.attrs.get("class", "").split(),
        ]:
            matches = [n for n in nodes if predicate(n) and len(n.text()) > 30]
            if matches:
                return max(matches, key=lambda n: len(n.text()))
        # Old faculty pages may lack semantic landmarks. Shared chrome is still
        # excluded. Identity must separately match a heading or document title.
        return next((n for n in nodes if n.tag == "body"), self.root)


def links(node, base):
    return [(n, clean(n.text()), canonical_url(urllib.parse.urljoin(base, n.attrs.get("href", ""))))
            for n in node.walk() if n.tag == "a" and n.attrs.get("href")]


class Fetcher:
    def __init__(self, cache, timeout=10, delay=.18, refresh=False, max_cache_age_days=30):
        self.cache = cache
        cache.mkdir(parents=True, exist_ok=True)
        self.timeout, self.delay, self.refresh = timeout, delay, refresh
        self.max_cache_age_days = max_cache_age_days
        self.lock = threading.Lock()
        self.host_locks, self.robot_locks, self.robots, self.next_request = {}, {}, {}, {}
        self.results = {}

    def cached_observed_at(self, url):
        meta_path = self.cache / (hashlib.sha256(canonical_url(url).encode()).hexdigest() + ".json")
        try:
            meta = json.loads(meta_path.read_text())
            return dt.datetime.fromisoformat(meta["observedAt"])
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def cached_fresh(self, url):
        if self.refresh or self.max_cache_age_days <= 0:
            return False
        observed = self.cached_observed_at(url)
        if not observed or not observed.tzinfo:
            return False
        age = dt.datetime.now(dt.UTC) - observed
        return dt.timedelta(days=-1) <= age <= dt.timedelta(days=self.max_cache_age_days)

    def _host_lock(self, host):
        with self.lock:
            self.robot_locks.setdefault(host, threading.Lock())
            return self.host_locks.setdefault(host, threading.BoundedSemaphore(4))

    def _request(self, url, max_bytes=1_500_000):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            payload = r.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise ValueError("response_exceeds_size_limit")
            return payload.decode(r.headers.get_content_charset() or "utf-8", "replace"), r.geturl(), r.status, r.headers.get("Content-Type", "")

    def fetch(self, url):
        url = canonical_url(url)
        key = hashlib.sha256(url.encode()).hexdigest()
        meta_path, body_path = self.cache / (key + ".json"), self.cache / (key + ".html")
        if self.cached_fresh(url):
            meta = json.loads(meta_path.read_text())
            self.results[url] = meta
            return meta, body_path.read_text() if body_path.exists() else ""
        host = urllib.parse.urlsplit(url).netloc
        meta = {"sourceUrl": url, "observedAt": now(), "status": "error"}
        body = ""
        with self._host_lock(host):
            with self.robot_locks[host]:
                if host not in self.robots:
                    robots_url = urllib.parse.urlunsplit((urllib.parse.urlsplit(url).scheme, host, "/robots.txt", "", ""))
                    rp = urllib.robotparser.RobotFileParser(robots_url)
                    try:
                        txt, _, _, _ = self._request(robots_url, 300_000)
                        rp.parse(txt.splitlines())
                        self.robots[host] = (rp, "checked")
                    except urllib.error.HTTPError as exc:
                        self.robots[host] = (None, "not_found" if exc.code in {404, 410} else "unavailable")
                    except Exception:
                        self.robots[host] = (None, "unavailable")
            rp, robots_status = self.robots[host]
            meta["robotsStatus"] = robots_status
            if robots_status == "unavailable":
                meta["status"] = "robots_unavailable"
            elif rp and not rp.can_fetch(UA, url):
                meta["status"] = "robots_denied"
            else:
                crawl_delay = max(self.delay, (rp.crawl_delay(UA) or rp.crawl_delay("*") or 0) if rp else 0)
                with self.lock:
                    scheduled = max(time.monotonic(), self.next_request.get(host, 0))
                    self.next_request[host] = scheduled + crawl_delay
                time.sleep(max(0, scheduled - time.monotonic()))
                try:
                    body, final, status, content_type = self._request(url)
                    meta.update(status="ok", httpStatus=status, finalUrl=final, contentType=content_type, sha256=hashlib.sha256(body.encode()).hexdigest())
                    if not any(x in content_type.lower() for x in ["html", "text/plain", "json"]):
                        meta["status"] = "unsupported_content"
                        body = ""
                except urllib.error.HTTPError as exc:
                    meta.update(status="http_error", httpStatus=exc.code, error=str(exc))
                except Exception as exc:
                    meta.update(status="fetch_error", error=type(exc).__name__ + ": " + str(exc)[:180])
            meta["observedAt"] = now()
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
            if body:
                body_path.write_text(body)
        self.results[url] = meta
        return meta, body


def evidence(meta, method, text):
    return {"sourceUrl": meta.get("finalUrl", meta["sourceUrl"]), "observedAt": meta["observedAt"], "method": method, "evidence": clean(text)[:900], "status": "verified"}


def person_matches(name, text):
    tokens = normalized(re.sub(r"\([^)]*\)", "", name)).split()
    hay = normalized(text)
    if len(tokens) < 2:
        return False
    # Both endpoints must occur as whole words, accommodating middle initials.
    return all(re.search(r"\b" + re.escape(t) + r"\b", hay) for t in [tokens[0], tokens[-1]])


def valid_lab_label(label):
    return bool(LAB_RE.search(label) and not re.fullmatch(r"(?:(?:research|faculty|all|our|department) )?(?:labs|laboratories|research groups)(?: directory| websites?)?", clean(label), re.I) and len(label) <= 150
                and not re.search(r"\b(?:laboratory safety|lab safety|lab coat|clinical laboratory|lab resources|laboratory services|teaching laboratory|undergraduate laboratory|laboratory study|lab study|journal|editor|reading group|working group|workshop|conference|seminar|proceedings|publications?|articles?|papers?)\b|^(?:about|join|support|donate|contact|between|I |we )\b|[“”\"]", label, re.I))


def is_lab_destination(url):
    """Publication titles may contain 'lab'; their links are not lab websites."""
    if nonlab_destination_reason(url):
        return False
    parsed = urllib.parse.urlsplit(url)
    host, path = (parsed.hostname or "").lower(), urllib.parse.unquote(parsed.path).lower()
    if host in {"profiles.ucsd.edu", "catalog.ucsd.edu", "courses.ucsd.edu"}:
        return False
    publication_hosts = {"doi.org", "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov", "scholar.google.com", "sciencedirect.com", "nature.com", "springer.com", "springerlink.com", "tandfonline.com", "wiley.com", "sagepub.com", "acm.org", "ieee.org", "jstor.org", "researchgate.net", "semanticscholar.org", "mitpress.mit.edu", "press.princeton.edu", "amazon.com", "cambridge.org", "oup.com"}
    if any(host == d or host.endswith("." + d) for d in publication_hosts):
        return False
    if "urldefense" in host or host in {"bit.ly", "t.co", "tinyurl.com"}:
        return False
    return not bool(re.search(r"\.(?:pdf|docx?|pptx?|bib)(?:$|/)|/(?:doi|articles?|publications?|papers?|pubs|books?|catalog|search)(?:/|\.|$)", path) or re.search(r"(?:format|type)=pdf|(?:searchfor|searchtype)=", parsed.query, re.I))


def make_lab(label, url, dept, meta, context, professor=None):
    label = clean(label)
    generic = bool(GENERIC_LAB_LINK.fullmatch(label))
    if generic:
        label = f"{professor['name']} — lab website" if professor else label
    method = "official_profile_explicit_lab_link" if professor else "official_directory_main_content"
    if generic:
        method = "official_profile_generic_lab_link" if professor else "official_directory_generic_lab_link"
    e = evidence(meta, method, context)
    host = urllib.parse.urlsplit(url).hostname or ""
    university_hosts = {"cam.ac.uk": "University of Cambridge", "stanford.edu": "Stanford University", "harvard.edu": "Harvard University", "berkeley.edu": "University of California Berkeley", "ox.ac.uk": "University of Oxford", "mit.edu": "Massachusetts Institute of Technology"}
    external_institution = next((institution for domain, institution in university_hosts.items() if host == domain or host.endswith("." + domain)), None)
    institution = "University of California San Diego" if host == "ucsd.edu" or host.endswith(".ucsd.edu") else external_institution or "Unknown"
    record = {"id": "ucsd-live-lab-" + hashlib.sha256(url.encode()).hexdigest()[:14], "labName": label,
              "institution": institution, "department": dept, "labWebsiteUrl": url,
              "principalInvestigator": MISSING,
              "principalInvestigatorProfileUrl": MISSING,
              "researchAreas": [], "description": "Lab website linked from an official UC San Diego faculty profile." if professor else "Lab listed in an official UC San Diego directory.",
              "contactEmail": MISSING, "recruitingStatus": "Unknown", "recruitingEvidence": {"text": "", "url": ""},
              "sourceUrls": [e["sourceUrl"], url], "lastVerified": observed_date(meta["observedAt"]), "recordSubtype": "lab",
              "fieldEvidence": {"labName": e, "labWebsiteUrl": e}, "professorIds": [professor["id"]] if professor else [],
              "relationshipScope": "external_institution" if external_institution else "ucsd_hosted" if institution != "Unknown" else "institution_not_confirmed"}
    if professor:
        record["relatedProfessorNames"] = [professor["name"]]
        record["relationshipType"] = "external_research_group_link" if external_institution else "faculty_lab_link"  # Does not imply sole leadership.
    return record


def parse_profile(p, meta, markup):
    patch = {"verification": {"status": meta["status"], "sourceUrl": meta["sourceUrl"], "observedAt": meta["observedAt"], "identityMatched": False}, "fieldEvidence": {}, "labAffiliations": []}
    if meta["status"] != "ok":
        return patch, []
    dom = DOM(markup)
    main = dom.main()
    headings = [n.text() for n in main.walk() if n.tag == "h1" or "faculty_profile_name" in n.attrs.get("class", "")]
    titles = [n.text() for n in dom.root.walk() if n.tag == "title"]
    identity = next((s for s in headings + titles if len(s) < 250 and person_matches(p["name"], s)), "")
    if not identity:
        patch["verification"]["status"] = "identity_not_confirmed"
        return patch, []
    patch["verification"].update(status="verified", identityMatched=True, identityEvidence=identity)
    patch["fieldEvidence"]["name"] = evidence(meta, "official_profile_heading_identity", identity)
    patch["officialProfileUrl"] = canonical_url(meta.get("finalUrl", meta["sourceUrl"]))
    patch["fieldEvidence"]["officialProfileUrl"] = evidence(meta, "official_profile_heading_identity", identity)
    page_links = links(main, meta.get("finalUrl", meta["sourceUrl"]))
    emails = []
    lab_links = [(n, label, url) for n, label, url in page_links if url and valid_lab_label(label)]
    # A profile redirecting to a departmental directory must not associate the
    # professor with every lab on that page, even if their name appears there.
    if len({u for _, _, u in lab_links}) > 6:
        lab_links = []
    for n, label, url in page_links:
        href = n.attrs.get("href", "")
        if href.startswith("mailto:"):
            emails.extend(EMAIL_RE.findall(href))
        if "scholar.google." in urllib.parse.urlsplit(url).netloc and "/citations" in url and "user=" in url:
            patch["googleScholarUrl"] = url
            patch["fieldEvidence"]["googleScholarUrl"] = evidence(meta, "official_profile_main_link", label + " " + url)
        if re.fullmatch(r"(?:personal |research |faculty |visit )?(?:web\s?site|home\s?page)(?:\s*[:→»]\s*)?", label, re.I) and url:
            if not re.search(r"(?:catalog|scholar|profiles)\.ucsd\.edu|scholar.google", url):
                patch["personalWebsiteUrl"] = url
                patch["fieldEvidence"]["personalWebsiteUrl"] = evidence(meta, "official_profile_main_link", label + " " + url)
    if not emails:
        # Plain-text contact blocks are common on Jacobs faculty profiles.
        emails = EMAIL_RE.findall(main.text())
    emails = list(dict.fromkeys(e for e in emails if e.split("@")[0].lower() not in {"info", "support", "webmaster", "feedback", "ctri-support", "communication", "advising"}))
    if len(emails) == 1:
        patch["email"] = emails[0]
        patch["fieldEvidence"]["email"] = evidence(meta, "identity_matched_profile_unique_contact", emails[0])
    paragraphs = [n.text() for n in main.walk() if n.tag == "p" and 90 <= len(n.text()) <= 3500]
    summary = next((s for s in paragraphs if re.search(r"\bresearch (?:interests?|focus|examines|aims|explores|investigates|on|in)|\b(?:my|our|his|her) research\b", s, re.I)
                    and not re.search(r"copyright|all rights reserved|faculty profiles|privacy policy|profiles is managed|we use cookies|website terms of use|site is running", s, re.I)), "")
    if summary:
        patch["researchSummary"] = summary[:1000]
        patch["fieldEvidence"]["researchSummary"] = evidence(meta, "official_profile_research_paragraph_excerpt", summary)
    labs = []
    for n, label, url in lab_links:
        if not url or url == canonical_url(p["officialProfileUrl"]) or not valid_lab_label(label) or not is_lab_destination(url):
            continue
        if re.search(r"(?:/labs/(?:index\.[a-z]+)?$|/research-labs(?:\.html)?$|/lab-directory)", urllib.parse.urlsplit(url).path):
            continue
        lab = make_lab(label, url, p["department"], meta, label + " → " + url, p)
        context = n.parent.text() if n.parent else label
        if re.search(r"\b(?:formerly|previously|former|prior to|past affiliation)\b", context, re.I):
            lab["relationshipType"] = "historical_research_group_link"
        labs.append(lab)
        patch["labAffiliations"].append({"labId": lab["id"], "labName": lab["labName"], "url": url, "relationship": lab["relationshipType"], "relationshipScope": lab["relationshipScope"], "fieldEvidence": lab["fieldEvidence"]["labWebsiteUrl"]})
    primary_labs = [l for l in labs if l["relationshipType"] not in {"external_research_group_link", "historical_research_group_link"}]
    if primary_labs:
        patch["labAffiliation"], patch["labAffiliationUrl"] = primary_labs[0]["labName"], primary_labs[0]["labWebsiteUrl"]
        patch["fieldEvidence"]["labAffiliation"] = primary_labs[0]["fieldEvidence"]["labName"]
        patch["fieldEvidence"]["labAffiliationUrl"] = primary_labs[0]["fieldEvidence"]["labWebsiteUrl"]
    return patch, labs


def block_for_link(node):
    # Prefer structural directory records over a heading's short paragraph.
    ancestors = []
    p = node.parent
    while p and p.tag != "document":
        ancestors.append(p)
        if p.tag in {"li", "td"} or "profile-listing-card" in p.attrs.get("class", ""):
            return p
        p = p.parent
    for p in ancestors:
        if p.tag in {"p", "div", "section"} and 40 <= len(p.text()) <= 1300:
            # Keep climbing through tiny wrappers to the record's common block.
            if p.parent and p.parent.tag in {"li", "tr"}:
                return p.parent
            return p
    return node.parent or node


def parse_directory(dept, meta, markup, professors):
    if meta["status"] != "ok":
        return []
    main = DOM(markup).main()
    out = []
    base = meta.get("finalUrl", meta["sourceUrl"])
    professor_urls = {canonical_url(p["officialProfileUrl"]): p for p in professors}
    for n, label, url in links(main, base):
        if not url or url == canonical_url(base) or not valid_lab_label(label) or GENERIC_LAB.fullmatch(label) or not is_lab_destination(url):
            continue
        if re.search(r"\b(?:research labs|faculty labs|lab directory|laboratories and centers)\b", label, re.I):
            continue
        block = block_for_link(n)
        context = block.text()
        lab = make_lab(label, url, dept, meta, context)
        people = []
        block_links = links(block, base)
        # Multiple separate labs in a row/container cannot share every PI.
        lab_targets = {u for _, t, u in block_links if valid_lab_label(t)}
        if len(lab_targets) > 1:
            out.append(lab)
            continue
        for _, plabel, purl in block_links:
            person = professor_urls.get(purl)
            if person and person_matches(person["name"], plabel):
                people.append(person)
        if not people and re.search(r"principal investigator|director|\bPI\b|led by", context, re.I):
            # Full normalized names, never surname-only guesses.
            people = [p for p in professors if p["department"] == dept and normalized(p["name"]) in normalized(context)]
        people = list({p["id"]: p for p in people}.values())
        if people:
            lab.update(professorIds=[p["id"] for p in people], relatedProfessorNames=[p["name"] for p in people], relationshipType="external_research_group_link" if lab["relationshipScope"] == "external_institution" else "official_directory_same_record")
            if re.search(r"principal investigators?|(?:co[ -]?)?directors?|\bPI\b|led by", context, re.I):
                lab.update(principalInvestigator="; ".join(p["name"] for p in people), principalInvestigatorProfileUrl=people[0]["officialProfileUrl"])
                lab["fieldEvidence"]["principalInvestigator"] = evidence(meta, "official_directory_same_record", context)
        out.append(lab)
    return out


def directory_seeds(data):
    seeds = {}
    candidates = json.loads((ROOT / "data/ucsd/source-candidates.json").read_text())
    for d in candidates.get("departments", []):
        for c in d.get("candidates", []):
            if c.get("kind") == "labs" and c.get("discovered"):
                seeds[canonical_url(c["url"])] = d["department"]
    for lab in data["labs"]:
        for u in lab.get("sourceUrls", []):
            if canonical_url(u) != canonical_url(lab["labWebsiteUrl"]) and (urllib.parse.urlsplit(u).hostname or "").endswith("ucsd.edu") and re.search(r"research|labs|laboratories|groups", u):
                seeds[canonical_url(u)] = lab["department"]
    seeds.update({
        "https://cogsci.ucsd.edu/research/research-labs.html": "Cognitive Science",
        "https://psychology.ucsd.edu/research/index.html": "Psychology",
        "https://neurosciences.ucsd.edu/research/labs/index.html": "Neurosciences",
        "https://biology.ucsd.edu/research/faculty/index.html": "Biological Sciences",
        "https://hwsph.ucsd.edu/research/faculty-research-labs/index.html": "Public Health",
    })
    return {u: d for u, d in seeds.items() if u}


def discover_faculty(fetcher, professors):
    """Discover explicit person links, then let the profile verify their identity.

    Directory inclusion is retained as a listing, never asserted as proof of
    current employment. Existing cross-department names are reused, not cloned.
    """
    new, alternative, listings = [], {}, {}
    known_names = {normalized(p["name"]): p for p in professors}
    known_urls = {canonical_url(p["officialProfileUrl"]): p for p in professors}
    names_first_last = {}
    for p in professors:
        bits = normalized(p["name"]).split()
        if len(bits) > 1:
            names_first_last.setdefault((bits[0], bits[-1]), []).append(p)
    sources = [
        ("https://cse.ucsd.edu/people/faculty-profiles", "Computer Science and Engineering", "/people/faculty-profiles/"),
        ("https://datascience.ucsd.edu/faculty/", "Halicioğlu Data Science Institute", "/people/"),
        ("https://cogsci.ucsd.edu/people/faculty/index.html", "Cognitive Science", "/people/faculty/"),
        ("https://psychology.ucsd.edu/people/profiles/faculty/index.html", "Psychology", "/people/profiles/")
    ]
    for url, department, marker in sources:
        meta, markup = fetcher.fetch(url)
        if meta["status"] != "ok":
            continue
        main = DOM(markup).main()
        sections, section = {}, "Faculty directory"
        for node in main.walk():
            if node.tag in {"h1", "h2", "h3", "h4"} and re.search(r"faculty|emerit|former|memoriam|deceased|lecturers|researchers|adjunct|affiliated|alumni|leadership", node.text(), re.I):
                section = node.text()
            sections[id(node)] = section
        for link, name, profile_url in links(main, meta.get("finalUrl", url)):
            if marker not in profile_url or profile_url == canonical_url(url):
                continue
            name = re.sub(r",?\s*(?:Ph\.?D\.?|M\.?D\.?)\s*$", "", name).strip()
            if not 2 <= len(name.split()) <= 6 or re.search(r"\d|\b(?:faculty|profile|directory|research|staff|student|emeriti|lecturers|professors|people|contact|view|more|chair|leadership)\b", name, re.I):
                continue
            if not all(token[0].isupper() or token.lower() in {"de", "van", "von", "da", "la", "del"} for token in name.split()):
                continue
            existing = known_urls.get(profile_url) or known_names.get(normalized(name))
            if not existing:
                bits = normalized(name).split()
                candidates = names_first_last.get((bits[0], bits[-1]), [])
                if len(candidates) == 1:
                    existing = candidates[0]
            section = sections[id(link)]
            category = "former" if re.search(r"former|alumni", section, re.I) else "emeritus" if re.search(r"emerit", section, re.I) else "deceased" if re.search(r"memoriam|deceased", section, re.I) else "listed_in_official_directory"
            e = evidence(meta, "official_faculty_directory_person_link", section + ": " + name + " → " + profile_url)
            if existing:
                listings[existing["id"]] = {"facultyStatus": category, "directorySection": section, "evidence": e}
                if "catalog.ucsd.edu" in existing["officialProfileUrl"]:
                    alternative[existing["id"]] = {**existing, "officialProfileUrl": profile_url, "directoryEvidence": e}
                continue
            p = {"id": "ucsd-faculty-live-" + normalized(name).replace(" ", "-"), "name": name,
                 "institution": "University of California San Diego", "department": department,
                 "officialProfileUrl": profile_url, "personalWebsiteUrl": MISSING, "email": MISSING,
                 "researchAreas": [], "researchSummary": MISSING, "googleScholarUrl": MISSING,
                 "labAffiliation": MISSING, "labAffiliationUrl": MISSING, "recruitingStatus": "Unknown",
                 "recruitingEvidence": {"text": "", "url": ""}, "sourceUrls": [url, profile_url],
                 "lastVerified": observed_date(meta["observedAt"]), "fieldEvidence": {"name": e, "officialProfileUrl": e, "department": e},
                 "facultyStatus": category, "directorySection": section, "directoryEvidence": e}
            new.append(p)
            listings[p["id"]] = {"facultyStatus": category, "directorySection": section, "evidence": e}
            known_names[normalized(name)], known_urls[profile_url] = p, p
    return new, alternative, listings


def select_slow_profiles(selected, fetcher, include_slow=False, budget=0):
    """Fresh cache costs no budget; never-seen pages precede oldest stale pages.

    Prioritizing missing pages avoids starving the tail of a large directory when
    a small weekly budget cannot refresh every page within the cache TTL.
    """
    pending = []
    for p in selected:
        u = canonical_url(p["officialProfileUrl"])
        if urllib.parse.urlsplit(u).hostname == "profiles.ucsd.edu" and not fetcher.cached_fresh(u):
            observed = fetcher.cached_observed_at(u)
            pending.append((bool(observed), observed.isoformat() if observed else "", p["id"]))
    pending.sort()
    chosen = {pid for _, _, pid in (pending[:budget] if budget else pending)} if include_slow else set()
    deferred = {pid for _, _, pid in pending} - chosen
    kept = [p for p in selected if p["id"] not in deferred]
    return kept, deferred


def parse_personal_site(person, meta, markup, profile_evidence):
    """A person-linked homepage is not itself a lab: require on-page evidence."""
    result = {"professorId": person["id"], "sourceUrl": meta["sourceUrl"], "observedAt": meta["observedAt"], "status": meta["status"], "labDetected": False}
    if meta["status"] != "ok":
        return result, {}, None
    if not is_lab_destination(meta.get("finalUrl", meta["sourceUrl"])):
        result["status"] = "not_a_lab_destination"
        return result, {}, None
    dom = DOM(markup)
    main = dom.main()
    headings = [n.text() for n in main.walk() if n.tag in {"h1", "h2", "h3"} and len(n.text()) <= 200]
    titles = [n.text() for n in dom.root.walk() if n.tag == "title"]
    primary = [n.text() for n in main.walk() if n.tag == "h1"] + titles
    lab_name = next((s for s in titles + headings if valid_lab_label(s) and not GENERIC_LAB.fullmatch(s) and not re.search(r"publications|news|course|members|alumni|joining|awards|graduates|students", s, re.I)), "")
    full_text = main.text()
    owner = next((s for s in primary if person_matches(person["name"], s) and len(s) < 250), "")
    explicit_pi = ""
    tokens = normalized(person["name"]).split()
    person_span = re.escape(tokens[0]) + r" (?:[a-z]+ ){0,3}" + re.escape(tokens[-1])
    roles = r"(?:principal investigator|(?:co )?director|(?:led|headed|run|founded) by|our pi|(?:lab|laboratory|group) of)"
    pi_pattern = re.compile(r"\b(?:" + roles + r" (?:professor |prof |dr )?" + person_span + r"|" + person_span + r" (?:is (?:the |a )?)?(?:principal investigator|(?:co )?director))\b")
    role_candidates = []
    for n in main.walk():
        if n.tag not in {"p", "li", "td", "div", "h1", "h2", "h3", "section"}:
            continue
        s = n.text()
        if len(s) > 1600:
            continue
        if pi_pattern.search(normalized(s)):
            role_candidates.append(s)
    if role_candidates:
        explicit_pi = min(role_candidates, key=len)
    if not owner and not explicit_pi:
        result["status"] = "identity_not_confirmed"
        return result, {}, None
    result.update(status="verified_personal_site", identityEvidence=explicit_pi or owner)
    patch = {"fieldEvidence": {}}
    for _, label, url in links(main, meta.get("finalUrl", meta["sourceUrl"])):
        if "scholar.google." in urllib.parse.urlsplit(url).netloc and "/citations" in url and "user=" in url:
            patch["googleScholarUrl"] = url
            patch["fieldEvidence"]["googleScholarUrl"] = evidence(meta, "identity_matched_personal_site_link", label + " " + url)
            break
    paragraphs = [n.text() for n in main.walk() if n.tag == "p" and 100 <= len(n.text()) <= 2000]
    summary = next((s for s in paragraphs if re.search(r"\b(?:my|our) (?:research|lab|group)|research (?:focus|interests|aims)|\bwe (?:study|develop|investigate|explore)\b", s, re.I)), "")
    if summary:
        patch["researchSummary"] = summary[:1000]
        patch["fieldEvidence"]["researchSummary"] = evidence(meta, "identity_matched_personal_site_research_excerpt", summary)
    if not lab_name:
        result["status"] = "verified_personal_site_not_lab"
        return result, patch, None
    url = canonical_url(meta.get("finalUrl", meta["sourceUrl"]))
    lab = make_lab(lab_name, url, person["department"], meta, lab_name + ": " + (explicit_pi or owner), person)
    e = evidence(meta, "personal_site_lab_heading_and_owner_identity", lab_name + ": " + (explicit_pi or owner))
    lab.update(description=summary[:1000] if summary else "Research lab identified on the personal website linked by an official UC San Diego profile.", sourceUrls=list(dict.fromkeys([profile_evidence["sourceUrl"], meta["sourceUrl"], url])), fieldEvidence={"labName": e, "labWebsiteUrl": e})
    if summary:
        lab["fieldEvidence"]["description"] = patch["fieldEvidence"]["researchSummary"]
    if explicit_pi:
        lab.update(principalInvestigator=person["name"], principalInvestigatorProfileUrl=person["officialProfileUrl"], relationshipType="personal_site_explicit_pi")
        lab["fieldEvidence"]["principalInvestigator"] = evidence(meta, "personal_site_explicit_pi_name", explicit_pi)
    result.update(status="verified_lab_site", labDetected=True, labName=lab_name)
    return result, patch, lab


def unique_values(items):
    """Preserve heterogeneous historical fetch/check records without coercion."""
    seen, result = set(), []
    for item in items:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            result.append(copy.deepcopy(item))
    return result


def evidence_items(value):
    return value if isinstance(value, list) else [value] if isinstance(value, dict) else []


def observation_time(proof):
    times = []
    for item in evidence_items(proof):
        try:
            stamp = dt.datetime.fromisoformat(item.get("observedAt") or "")
            if stamp.tzinfo:
                times.append(stamp.astimezone(dt.UTC))
        except (ValueError, TypeError):
            pass
    return max(times, default=dt.datetime.min.replace(tzinfo=dt.UTC))


def has_value(value):
    return value is not None and value not in ("", "Unknown", MISSING, [])


def generic_lab_name(value, proof):
    methods = [e.get("method", "") for e in evidence_items(proof)]
    return bool(methods) and (all(m.endswith("_generic_lab_link") for m in methods) or
        # Compatibility with captures made before generic labels had a method.
        ((str(value).endswith(" — lab website") or GENERIC_LAB_LINK.fullmatch(str(value))) and any(m == "official_profile_explicit_lab_link" for m in methods)))


def merge_observed_fields(previous, incoming):
    """Update positively observed fields, retaining independent older evidence.

    An absent field is not a retraction. Replaced values keep their own proof in
    history instead of misattributing that proof to the new value. Old cache
    replays cannot supersede newer observations from a cloud backfill.
    """
    merged = copy.deepcopy(previous)
    fields = merged.setdefault("fieldEvidence", {})
    for field, proof in incoming.get("fieldEvidence", {}).items():
        old_proof = fields.get(field)
        if field not in incoming:
            fields[field] = unique_values(evidence_items(old_proof) + evidence_items(proof))
            continue
        value = incoming[field]
        if not has_value(value):
            continue
        old_value = merged.get(field)
        if has_value(old_value) and old_value != value:
            url_field = {"labName": "labWebsiteUrl", "labAffiliation": "labAffiliationUrl"}.get(field)
            same_lab = url_field and canonical_url(previous.get(url_field, "")).rstrip("/") == canonical_url(incoming.get(url_field, "")).rstrip("/")
            old_generic, new_generic = generic_lab_name(old_value, old_proof), generic_lab_name(value, proof)
            if same_lab and new_generic and not old_generic:
                merged["additionalLabLinkObservations"] = unique_values(merged.get("additionalLabLinkObservations", []) + [{"field": field, "value": value, "fieldEvidence": evidence_items(proof)}])
                continue
            if observation_time(proof) < observation_time(old_proof) and not (same_lab and old_generic and not new_generic):
                continue
            # A profile's short bio must not erase a previously checked personal
            # site's research excerpt or Scholar link (also the backfill policy).
            if field in {"researchSummary", "googleScholarUrl"} and any("personal_site" in e.get("method", "") for e in evidence_items(old_proof)) and not any("personal_site" in e.get("method", "") for e in evidence_items(proof)):
                merged["additionalProfileObservations"] = unique_values(merged.get("additionalProfileObservations", []) + [{"field": field, "value": value, "fieldEvidence": evidence_items(proof)}])
                continue
            merged["previousFieldObservations"] = unique_values(merged.get("previousFieldObservations", []) + [{"field": field, "value": old_value, "fieldEvidence": evidence_items(old_proof)}])
            fields[field] = copy.deepcopy(proof)
        else:
            fields[field] = unique_values(evidence_items(old_proof) + evidence_items(proof)) if old_proof else copy.deepcopy(proof)
        merged[field] = copy.deepcopy(value)
    return merged


def merge_profile_observation(previous, incoming):
    verification = incoming.get("verification", {})
    old_verification = previous.get("verification", {})
    if not verification.get("observedAt") or observation_time(verification) < observation_time(old_verification):
        return copy.deepcopy(previous)
    merged = merge_observed_fields(previous, incoming) if verification.get("status") == "verified" else copy.deepcopy(previous)
    if old_verification and old_verification != verification:
        merged["verificationHistory"] = unique_values(merged.get("verificationHistory", []) + [old_verification])
    # A new fetch/identity failure is still the latest check. Historical field
    # evidence survives, but the person is no longer reported as just verified.
    merged["verification"] = copy.deepcopy(verification)
    affiliations = merged.setdefault("labAffiliations", [])
    by_url = {canonical_url(a["url"]).rstrip("/"): a for a in affiliations}
    for fresh in incoming.get("labAffiliations", []):
        key = canonical_url(fresh["url"]).rstrip("/")
        old = by_url.get(key)
        if old is None:
            old = copy.deepcopy(fresh)
            affiliations.append(old)
            by_url[key] = old
        else:
            old_proof = copy.deepcopy(old.get("fieldEvidence"))
            if observation_time(fresh.get("fieldEvidence")) >= observation_time(old_proof):
                preserved = {"labId": old.get("labId")}
                if generic_lab_name(fresh.get("labName"), fresh.get("fieldEvidence")) and not generic_lab_name(old.get("labName"), old_proof):
                    preserved["labName"] = old.get("labName")
                if old.get("relationship") in {"personal_site_explicit_pi", "official_directory_same_record"} and fresh.get("relationship") == "faculty_lab_link":
                    preserved["relationship"] = old["relationship"]
                old.update(copy.deepcopy(fresh))
                old.update({k: v for k, v in preserved.items() if v is not None})
            old["fieldEvidence"] = unique_values(evidence_items(old_proof) + evidence_items(fresh.get("fieldEvidence")))
    return merged


def load_previous_capture(path):
    if not path.exists():
        return {}
    capture = json.loads(path.read_text())
    for key, kind in [("byProfessorId", dict), ("labs", list), ("professors", list), ("fetches", list), ("personalSiteChecks", list), ("directoryListings", dict)]:
        if not isinstance(capture.get(key), kind):
            raise ValueError(f"Refusing to replace existing capture: {key} must be {kind.__name__}")
    expected = capture.get("stats", {}).get("professorRecords", 0)
    if isinstance(expected, int) and expected > len(capture["byProfessorId"]):
        raise ValueError("Refusing to replace an existing capture with an incomplete roster")
    return capture


def atomic_capture(path, output):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(output, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run(args):
    data = json.loads(args.input.read_text())
    previous = load_previous_capture(args.out)
    professors = list(data["professors"])
    input_ids = {p["id"] for p in professors}
    professors += [p for p in previous.get("professors", []) if p["id"] not in input_ids]
    fetcher = Fetcher(args.cache, args.timeout, args.delay, args.refresh, args.max_cache_age_days)
    new_professors, alternative, directory_listings = discover_faculty(fetcher, professors)
    professors = professors + new_professors
    # Keep discovered records exportable after a previous merge, so rebuilding
    # from an original baseline plus this evidence does not silently lose them.
    export_professors = list(new_professors)
    new_ids = {p["id"] for p in new_professors}
    for person in professors:
        if person["id"].startswith("ucsd-faculty-live-") and person["id"] not in new_ids and person["id"] in directory_listings:
            listing = directory_listings[person["id"]]
            export_professors.append({**{k: person[k] for k in ["id", "name", "institution", "department", "officialProfileUrl"]},
                "personalWebsiteUrl": MISSING, "email": MISSING, "researchAreas": [], "researchSummary": MISSING, "googleScholarUrl": MISSING,
                "labAffiliation": MISSING, "labAffiliationUrl": MISSING, "recruitingStatus": "Unknown", "recruitingEvidence": {"text": "", "url": ""},
                "sourceUrls": [listing["evidence"]["sourceUrl"], person["officialProfileUrl"]], "lastVerified": observed_date(listing["evidence"]["observedAt"]),
                "fieldEvidence": {"name": listing["evidence"], "officialProfileUrl": listing["evidence"], "department": listing["evidence"]},
                "facultyStatus": listing["facultyStatus"], "directorySection": listing["directorySection"], "directoryEvidence": listing["evidence"]})
    selected = [alternative.get(p["id"], p) for p in professors if ("catalog.ucsd.edu" not in p.get("officialProfileUrl", "") or p["id"] in alternative) and canonical_url(p.get("officialProfileUrl", ""))]
    selected, slow_deferred = select_slow_profiles(selected, fetcher, args.include_slow_profiles, args.slow_profile_limit)
    if args.limit:
        selected = selected[:args.limit]
    output = copy.deepcopy(previous)
    output.update({"schemaVersion": 1, "generatedAt": now(), "collectionState": "in_progress", "collectionPolicy": {
        **previous.get("collectionPolicy", {}),
        "identity": "An official profile heading or title must match first and last name before extracting person fields.",
        "relationships": "Only main-content lab links or a lab-directory record can support a faculty/lab relationship. Shared navigation is excluded.",
        "missing": "Missing or failed verification means unknown, not no lab or no current affiliation.",
        "freshness": "observedAt is the actual UTC retrieval time, not the date the source was authored. Cache reuse preserves observedAt.",
        "robots": "Robots disallow and unavailable robots are skipped; requests are bounded and per-host rate limited.",
        "incrementalRefresh": "Unattempted records and independent historical evidence survive partial runs. Actual new failures update verification; older cache replays cannot replace newer observations."}})
    for key, default in [("labs", []), ("professors", []), ("directoryListings", {}), ("byProfessorId", {}), ("personalSiteChecks", []), ("fetches", []), ("stats", {})]:
        output.setdefault(key, default)
    exports = {p["id"]: p for p in output["professors"]}
    for person in export_professors:
        if person["id"] not in exports:
            exports[person["id"]] = copy.deepcopy(person)
        else:
            old = exports[person["id"]]
            merged = merge_observed_fields(old, person)
            merged["sourceUrls"] = unique_values(old.get("sourceUrls", []) + person.get("sourceUrls", []))
            for key in ["facultyStatus", "directorySection", "directoryEvidence", "lastVerified"]:
                if observation_time(person.get("directoryEvidence")) >= observation_time(old.get("directoryEvidence")) and key in person:
                    merged[key] = copy.deepcopy(person[key])
            exports[person["id"]] = merged
    output["professors"] = list(exports.values())
    for pid, listing in directory_listings.items():
        old = output["directoryListings"].get(pid)
        if not old or observation_time(listing.get("evidence")) >= observation_time(old.get("evidence")):
            output["directoryListings"][pid] = copy.deepcopy(listing)
    for p in professors:
        if p["id"] not in output["byProfessorId"]:
            output["byProfessorId"][p["id"]] = {"verification": {"status": "catalog_only" if "catalog.ucsd.edu" in p.get("officialProfileUrl", "") else "not_attempted", "sourceUrl": p.get("officialProfileUrl", ""), "observedAt": None, "identityMatched": False}, "fieldEvidence": {}, "labAffiliations": []}
        verification = output["byProfessorId"][p["id"]]["verification"]
        if p["id"] in slow_deferred and not verification.get("observedAt") and verification.get("status") != "verified":
            verification.update(status="deferred_crawl_delay", sourceUrl=p["officialProfileUrl"], reason="Official UCSD Profiles robots.txt requires Crawl-Delay: 10. This page is outside the current slow-host budget; resume with --include-slow-profiles and --slow-profile-limit.", robotsUrl="https://profiles.ucsd.edu/robots.txt", crawlDelaySeconds=10)
    labs = {canonical_url(lab["labWebsiteUrl"]).rstrip("/"): copy.deepcopy(lab) for lab in output["labs"]}
    baseline_fetches = copy.deepcopy(output["fetches"])
    baseline_attempts = output["stats"].get("profileAttempts", 0)
    output["refreshRun"] = {"startedAt": now(), "selectedProfiles": len(selected), "slowDeferredProfiles": len(slow_deferred), "completedProfileObservations": 0}
    completed_ids = set()

    def merge_lab(lab):
        key = canonical_url(lab["labWebsiteUrl"]).rstrip("/")
        if key not in labs:
            labs[key] = copy.deepcopy(lab)
        else:
            old = labs[key]
            merged = merge_observed_fields(old, lab)
            for field in ["sourceUrls", "professorIds", "relatedProfessorNames"]:
                if field in old or field in lab:
                    merged[field] = unique_values(old.get(field, []) + lab.get(field, []))
            if has_value(lab.get("principalInvestigator")) and merged.get("principalInvestigator") == lab["principalInvestigator"] and observation_time(lab.get("fieldEvidence", {}).get("principalInvestigator")) >= observation_time(old.get("fieldEvidence", {}).get("principalInvestigator")):
                for field in ["principalInvestigatorProfileUrl", "relationshipType"]:
                    if field in lab:
                        merged[field] = copy.deepcopy(lab[field])
            if lab.get("lastVerified", "") > old.get("lastVerified", ""):
                merged["lastVerified"] = lab["lastVerified"]
            labs[key] = merged

    def save():
        output["generatedAt"] = now()
        output["labs"] = sorted(labs.values(), key=lambda x: x["labName"].lower())
        output["fetches"] = unique_values(baseline_fetches + list(fetcher.results.values()))
        output["personalSiteChecks"] = unique_values(output["personalSiteChecks"])
        output["refreshRun"]["completedProfileObservations"] = len(completed_ids)
        output["refreshRun"]["updatedAt"] = output["generatedAt"]
        output["stats"].update({"professorRecords": len(output["byProfessorId"]), "profileAttempts": baseline_attempts + len(completed_ids), "profileAttemptsSemantics": "Cumulative completed profile observations across capture runs, including cached responses; current-run count is refreshRun.completedProfileObservations.", "professorsProcessed": len(output["byProfessorId"]), "verificationStatuses": dict(Counter(p.get("verification", {}).get("status", "unknown") for p in output["byProfessorId"].values())), "labs": len(labs), "labsWithProfessorMatch": sum(bool(l.get("professorIds")) for l in labs.values()), "fetchStatuses": dict(Counter(f.get("status", "unknown") for f in output["fetches"] if isinstance(f, dict)))})
        atomic_capture(args.out, output)

    seeds = directory_seeds(data)
    print(f"Fetching {len(seeds)} official lab/research directories and {len(selected)} faculty profiles", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetcher.fetch, u): (u, dept) for u, dept in seeds.items()}
        for future in concurrent.futures.as_completed(futures):
            u, dept = futures[future]
            meta, markup = future.result()
            for lab in parse_directory(dept, meta, markup, professors):
                merge_lab(lab)
        save()
        print(f"Directories done: {len(labs)} lab links", flush=True)
        futures = {pool.submit(fetcher.fetch, p["officialProfileUrl"]): p for p in selected}
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            p = futures[future]
            meta, markup = future.result()
            patch, new_labs = parse_profile(p, meta, markup)
            if p["id"] in alternative and patch["verification"]["identityMatched"]:
                patch["officialProfileUrl"] = p["officialProfileUrl"]
                patch["fieldEvidence"]["officialProfileUrl"] = p["directoryEvidence"]
            output["byProfessorId"][p["id"]] = merge_profile_observation(output["byProfessorId"][p["id"]], patch)
            completed_ids.add(p["id"])
            for lab in new_labs:
                merge_lab(lab)
            if index % 100 == 0:
                save()
                print(f"Profiles {index}/{len(selected)}; labs {len(labs)}; verified {output['stats']['verificationStatuses'].get('verified', 0)}", flush=True)
    if args.personal_sites:
        has_lab = {pid for lab in labs.values() for pid in lab["professorIds"]}
        candidates = []
        for person in professors:
            patch = output["byProfessorId"].get(person["id"], {})
            url = patch.get("personalWebsiteUrl")
            proof = patch.get("fieldEvidence", {}).get("personalWebsiteUrl")
            if url and proof and person["id"] in completed_ids and patch.get("verification", {}).get("status") == "verified" and person["id"] not in has_lab:
                candidates.append((person, url, max(evidence_items(proof), key=observation_time)))
        candidates = candidates[:args.personal_site_limit] if args.personal_site_limit else candidates
        print(f"Checking {len(candidates)} verified personal-site links for lab/owner evidence", flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(fetcher.fetch, url): (person, proof) for person, url, proof in candidates}
            for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
                person, proof = futures[future]
                meta, markup = future.result()
                check, fields, lab = parse_personal_site(person, meta, markup, proof)
                output["personalSiteChecks"].append(check)
                output["byProfessorId"][person["id"]] = merge_observed_fields(output["byProfessorId"][person["id"]], fields)
                if lab:
                    merge_lab(lab)
                if index % 50 == 0:
                    save()
                    print(f"Personal sites {index}/{len(candidates)}; labs {len(labs)}", flush=True)
    # Associate directory relationships with professors even when their individual
    # profile is inaccessible. This evidence has a different source/method.
    for lab in labs.values():
        for pid in lab["professorIds"]:
            patch = output["byProfessorId"].get(pid)
            if not patch:
                continue
            if not any(canonical_url(a["url"]).rstrip("/") == canonical_url(lab["labWebsiteUrl"]).rstrip("/") for a in patch["labAffiliations"]):
                e = lab["fieldEvidence"].get("principalInvestigator", lab["fieldEvidence"]["labWebsiteUrl"])
                patch["labAffiliations"].append({"labId": lab["id"], "labName": lab["labName"], "url": lab["labWebsiteUrl"], "relationship": lab.get("relationshipType", "faculty_lab_link"), "fieldEvidence": e})
            if not patch.get("labAffiliationUrl") and lab.get("relationshipScope") != "external_institution" and lab.get("relationshipType") not in {"external_research_group_link", "historical_research_group_link"}:
                patch["labAffiliation"], patch["labAffiliationUrl"] = lab["labName"], lab["labWebsiteUrl"]
                patch["fieldEvidence"]["labAffiliation"] = lab["fieldEvidence"].get("principalInvestigator", lab["fieldEvidence"]["labName"])
                patch["fieldEvidence"]["labAffiliationUrl"] = lab["fieldEvidence"]["labWebsiteUrl"]
            for affiliation in patch["labAffiliations"]:
                if canonical_url(affiliation["url"]).rstrip("/") == canonical_url(lab["labWebsiteUrl"]).rstrip("/"):
                    affiliation["labId"] = lab["id"]
    for pid, listing in output["directoryListings"].items():
        patch = output["byProfessorId"].get(pid)
        if patch:
            output["byProfessorId"][pid] = merge_observed_fields(patch, {"facultyStatus": listing["facultyStatus"], "directorySection": listing["directorySection"], "fieldEvidence": {"facultyStatus": listing["evidence"], "directorySection": listing["evidence"]}})
    output["collectionState"] = "completed"
    save()
    print(json.dumps(output["stats"], indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/research-atlas.json")
    parser.add_argument("--out", type=Path, default=ROOT / "data/ucsd/lab-evidence.json", help="Full capture to update atomically; existing evidence is retained for records not re-observed. Use a new path for a fresh capture.")
    parser.add_argument("--cache", type=Path, default=Path("/tmp/research-atlas-lab-cache"))
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--timeout", type=float, default=6)
    parser.add_argument("--delay", type=float, default=.18)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--max-cache-age-days", type=float, default=30, help="Expire cached responses after this many days (default: 30); 0 disables reuse. observedAt always retains the actual retrieval time.")
    parser.add_argument("--include-slow-profiles", action="store_true", help="Fetch uncached UCSD Profiles pages, respecting its 10-second crawl delay (a full run takes hours).")
    parser.add_argument("--slow-profile-limit", type=int, default=0, help="With --include-slow-profiles, budget uncached slow-host pages per run; 0 means all. Existing cache is always reused unless --refresh is passed.")
    parser.add_argument("--personal-sites", action="store_true", help="Follow identity-verified official profile website links once to discover explicitly named labs and owners.")
    parser.add_argument("--personal-site-limit", type=int, default=400, help="Budget personal-site lookups; 0 means all eligible links (default: 400).")
    run(parser.parse_args())
