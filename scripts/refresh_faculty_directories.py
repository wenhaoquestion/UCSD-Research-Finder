#!/usr/bin/env python3
"""Refresh explicit public faculty-directory listings without changing the atlas.

Names come from faculty cards or the same filtered public feeds used by the
official directory. Students, staff, and postdocs are not promoted to faculty.
Existing identities are reused using individual profile links, professional
email, full names, or unambiguous full first/last names. A surname alone never
creates or merges a person. Directory observation is not a guarantee of current
employment. Math's public employee feed is immediately filtered and minimized;
unrelated personnel data is never cached or included in the output.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import functools
import hashlib
import json
import re
import ssl
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from refresh_labs import DOM, Fetcher, canonical_url, clean, evidence, links, normalized, now

ROOT = Path(__file__).resolve().parents[1]
MISSING = "Not found"
MATH_JOB_TITLES = {
    "001100": "Professor", "001143": "Professor",
    "001200": "Associate Professor", "001243": "Associate Professor",
    "001300": "Assistant Professor", "001343": "Assistant Professor",
    "001603": "Teaching Professor (Senior Lecturer SOE)",
    "001607": "Associate Teaching Professor (Lecturer SOE)",
    "001680": "Assistant Teaching Professor (Lecturer PSOE)",
    "001096": "Department Chair",
}
MATH_FEED = "https://soeapp.ucsd.edu/tools/eah/department.php"
MATH_PROFILES = "https://math.ucsd.edu/export/people/faculty"
MATH_FACULTY = "https://www.math.ucsd.edu/people/faculty"
MATH_EMERITI = "https://www.math.ucsd.edu/people/emeriti-faculty"
PHYSICS_FEED = "https://physics.ucsd.edu/api/profiles/faculty/000220"
PHYSICS_DIRECTORY = "https://physics.ucsd.edu/people/faculty"
BIOLOGY_PROFILES_FEED = "https://public.biology.ucsd.edu/api/prod/website-data/v1/profiles"
BIOLOGY_DEPARTMENT = "Biological Sciences"

SOURCES = [
    ("astronomy", "Astronomy and Astrophysics", "https://astro.ucsd.edu/people/faculty/index.html", "profile-listing-card", "astronomy"),
    ("chemistry", "Chemistry & Biochemistry", "https://chemistry.ucsd.edu/faculty/index.shtml", "profile-container", "chemistry"),
    ("chemistry-emeritus", "Chemistry & Biochemistry", "https://chemistry.ucsd.edu/faculty/emeritus", "profile-container", "chemistry"),
    ("ece", "Electrical and Computer Engineering", "https://ece.ucsd.edu/people/faculty", "faculty-member", "ece"),
    ("ece-emeritus", "Electrical and Computer Engineering", "https://ece.ucsd.edu/people/faculty/emeritus", "faculty-member", "ece"),
    ("mae", "Mechanical & Aerospace Engineering", "https://mae.ucsd.edu/people/faculty-profiles", "profile-window", "engineering"),
    ("nano", "NanoEngineering", "https://cne.ucsd.edu/fac", "faculty-profile", "engineering"),
    ("bioengineering", "Bioengineering", "https://be.ucsd.edu/faculty", "faculty-profile", "engineering"),
    ("structural", "Structural Engineering", "https://se.ucsd.edu/people/faculty/professors", "col-md-3", "structural"),
    # Departments on the shared campus CMS template (profile-listing-card).
    ("economics", "Economics", "https://economics.ucsd.edu/faculty-and-research/faculty-profiles/index.html", "profile-listing-card", "cascade"),
    ("history", "History", "https://history.ucsd.edu/people/faculty/index.html", "profile-listing-card", "cascade"),
    ("communication", "Communication", "https://communication.ucsd.edu/people/faculty/index.html", "profile-listing-card", "cascade"),
    ("cognitive-science", "Cognitive Science", "https://cogsci.ucsd.edu/people/faculty/index.html", "profile-listing-card", "cascade"),
    ("sociology", "Sociology", "https://sociology.ucsd.edu/people/faculty/index.html", "profile-listing-card", "cascade"),
    ("linguistics", "Linguistics", "https://linguistics.ucsd.edu/people/faculty/index.html", "profile-listing-card", "cascade"),
    ("visual-arts", "Visual Arts", "https://visarts.ucsd.edu/people/faculty/index.html", "profile-listing-card", "cascade"),
    ("education-studies", "Education Studies", "https://eds.ucsd.edu/people/faculty/index.html", "profile-listing-card", "cascade"),
]


class DirectoryFetcher(Fetcher):
    """Use the OS certificate store when Python lacks a site's intermediate CA."""
    def _request(self, url, max_bytes=1_500_000):
        try:
            return super()._request(url, max_bytes)
        except urllib.error.URLError as error:
            if not isinstance(error.reason, ssl.SSLCertVerificationError):
                raise
            # No -k / insecure bypass; curl verifies using the system trust store.
            result = subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error", "--max-time", str(self.timeout), "--max-filesize", str(max_bytes), "--user-agent", "ResearchAtlasEvidenceBot/2.0", url], capture_output=True, check=True)
            body = result.stdout
            if len(body) > max_bytes:
                raise ValueError("response_exceeds_size_limit")
            return body.decode("utf-8", "replace"), url, 200, "text/html"


def text_name(raw):
    name = clean(re.sub(r",?\s*(?:Ph\.?D\.?|M\.?D\.?)\s*$", "", raw))
    if "," in name:
        last, first = name.split(",", 1)
        name = clean(first + " " + last)
    return name


@functools.lru_cache(maxsize=50_000)
def identity_name(raw):
    """Normalize display punctuation, never infer a missing given name."""
    name = text_name(raw)
    name = re.sub(r"^(?:(?:adjunct|distinguished|emeritus|assistant|associate|professor|dr)\.?\s+)+", "", name, flags=re.I)
    name = re.sub(r"\([^)]*\)|[\"'‘’“”][^\"'‘’“”]+[\"'‘’“”]", "", name)
    return normalized(name.replace("'", "").replace("’", ""))


def valid_person_name(name):
    tokens = normalized(re.sub(r"\([^)]*\)", "", name)).split()
    return (2 <= len(tokens) <= 8 and any(len(t) > 1 for t in tokens[:-1])
            and not re.search(r"\d|\b(?:faculty|directory|research|staff|student|emeritus|professor|contact|website|chair|lecturer|profile)\b", name, re.I))


@functools.lru_cache(maxsize=50_000)
def individual_profile(url):
    if not url or url == MISSING:
        return False
    parsed = urllib.parse.urlsplit(url)
    host, path = parsed.hostname or "", parsed.path.rstrip("/")
    if not host.endswith("ucsd.edu") or host == "catalog.ucsd.edu":
        return False
    if host == "profiles.ucsd.edu":
        return bool(path and path.count("/") == 1)
    if host == "providers.ucsd.edu":
        return bool(re.match(r"/details/\d+/", path))
    if re.search(r"/(?:people/)?profiles?/[^/]+$|/faculty-profiles/[^/]+$|/profile$|/faculty_bios/index\.sfe$", path):
        return not path.endswith(("/profile", "/index.sfe")) or bool(parsed.query)
    leaf = path.rsplit("/", 1)[-1].lower().split(".")[0]
    generic = {"", "index", "faculty", "faculty-members", "faculty-profiles", "emeritus", "emeriti", "emeritus-faculty", "emeriti-faculty", "professors", "affiliated", "affiliate-faculty", "faculty-bios", "faculty_bios"}
    return leaf not in generic and ("/people/" in path or "/faculty/" in path)


@functools.lru_cache(maxsize=50_000)
def profile_identity(url):
    """Normalize only documented aliases of the same Jacobs profile id."""
    url = canonical_url(url)
    parsed = urllib.parse.urlsplit(url)
    if parsed.hostname == "www.math.ucsd.edu":
        url = urllib.parse.urlunsplit((parsed.scheme, "math.ucsd.edu", parsed.path, parsed.query, ""))
    if parsed.hostname in {"jacobsschool.ucsd.edu", "www.jacobsschool.ucsd.edu"}:
        query = urllib.parse.parse_qs(parsed.query)
        record = query.get("fmp_recid", query.get("id", []))
        if record:
            return "jacobs-profile:" + record[0]
    return url if individual_profile(url) else ""


def safe_link(url):
    parsed = urllib.parse.urlsplit(canonical_url(url))
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, urllib.parse.quote(parsed.path, safe="/%:@-._~"), parsed.query, "")) if parsed.scheme else ""


def appointment_status(role, section=""):
    value = role + " " + section
    for pattern, status in [(r"deceased|memoriam", "deceased"), (r"former|alumni", "former"), (r"emerit", "emeritus"), (r"adjunct", "adjunct"), (r"affiliat", "affiliate")]:
        if re.search(pattern, value, re.I):
            return status
    if re.search(r"lecturer", role, re.I) and not re.search(r"professor", role, re.I):
        return "lecturer"
    return "listed_faculty"


def card_records(source, meta, body):
    key, department, url, card_class, parser = source
    main = DOM(body).main()
    records = []
    section = "Emeritus Faculty" if "emeritus" in key else "Faculty directory"
    for node in main.walk():
        if node.tag in {"h1", "h2"} and re.search(r"faculty|emerit|affiliat|memoriam|former|lecturer", node.text(), re.I) and len(node.text()) < 100:
            section = node.text()
        if card_class not in node.attrs.get("class", "").split():
            continue
        children = list(node.walk())
        if parser in {"astronomy", "cascade"}:
            headings = [n for n in children if n.tag == "p" and "h3" in n.attrs.get("class", "").split()]
            if parser == "cascade" and not headings:
                headings = [n for n in children if n.tag in {"h2", "h3", "h4"}]
        elif parser == "structural":
            headings = [n for n in children if "views-field-field-last-name" in n.attrs.get("class", "").split()]
        else:
            headings = [n for n in children if n.tag in {"h2", "h3", "h4"}]
        if not headings:
            continue
        heading = headings[0]
        name = text_name(heading.text())
        if not valid_person_name(name):
            continue
        card_links = links(node, meta.get("finalUrl", url))
        name_links = links(heading, meta.get("finalUrl", url))
        named_url = name_links[0][2] if name_links else ""
        if not named_url:
            # Chemistry wraps the heading in the anchor, not the reverse.
            named_url = next((u for _, label, u in card_links if identity_name(label) == identity_name(name)), "")
        if parser == "structural":
            named_url = next((u for _, label, u in card_links if label == "Faculty Profile"), "")
        named_url = safe_link(named_url)
        card_text = node.text()
        if parser == "chemistry":
            match = re.search(r"Titles\s+(.+?)(?:\s+Research Areas|$)", card_text)
            role = match[1] if match else "Faculty directory listing"
        elif parser == "astronomy":
            description = next((n.text() for n in children if n.tag == "p" and re.search(r"professor", n.text(), re.I)), "")
            match = re.match(r"((?:(?:Physics|Assistant|Associate|Distinguished|Emeritus)\s+)*Professor(?:\s+Emeritus)?)\b", description)
            role = match[1] if match else section
        elif parser == "structural":
            role = "Faculty listed in Professors directory"
        else:
            role_tags = {"h4", "h5", "h6", "p"} if parser == "cascade" else {"h5", "h6", "p"}
            role_lines = [n.text() for n in children if n.tag in role_tags and n is not heading and re.search(r"professor|lecturer|affiliate|chair|chancellor|provost|dean", n.text(), re.I) and len(n.text()) < 350]
            role = " | ".join(dict.fromkeys(role_lines))
            if not role and parser == "cascade":
                # Some departments print the title as bare text after the degree line.
                match = re.search(r"\b((?:(?:Distinguished|Associate|Assistant|Teaching|Adjunct|Visiting|Research|Clinical|Senior)\s+)*(?:Professor|Lecturer)(?:\s+Emerit(?:us|a))?)\b", card_text.replace(heading.text(), ""))
                role = match[1] if match else ""
            if parser == "cascade":
                # Titles share a paragraph with office and email on some cards.
                role = clean(re.split(r"\s+(?=[\w.+%-]+@|(?:[A-Z]{2,6}|Room)\s+\d)", role)[0])
            role = role or "Faculty directory listing"
        email_links = [n.attrs.get("href", "")[7:].split("?", 1)[0] for n in children if n.tag == "a" and n.attrs.get("href", "").startswith("mailto:")]
        email = next((e for e in email_links if e.lower().endswith("ucsd.edu")), "")
        if not email:
            email = next(iter(re.findall(r"[\w.+%-]+@(?:[\w-]+\.)*ucsd\.edu", card_text)), "")
        profile = named_url if individual_profile(named_url) else ""
        personal = next((u for _, label, u in card_links if re.search(r"^(?:lab web(?:site)?|website|web page|.+ research)$", label, re.I) and urllib.parse.urlsplit(u).scheme in {"http", "https"}), "")
        if parser == "astronomy" and named_url and not profile and "inspirehep.net" not in named_url:
            personal = named_url
        if "scholar.google." in personal or "providers.ucsd.edu" in personal:
            personal = ""
        scholar = next((u for _, _, u in card_links if "scholar.google." in u and "/citations?" in u and "user=" in u), "")
        areas = [clean(s) for s in node.attrs.get("data-research-areas", "").split(",") if clean(s)]
        if parser == "cascade":
            # Only labels linked to the department's own research-group index.
            areas += [label for _, label, u in card_links if "research-groups" in urllib.parse.urlsplit(u).path and label]
        e = evidence(meta, "official_faculty_directory_card", f"{section} | {name} | {role}")
        records.append({"name": name, "department": department, "listedRole": role, "appointmentStatus": appointment_status(role, section), "directorySection": section,
            "sourceUrl": meta.get("finalUrl", url), "observedAt": meta["observedAt"], "evidence": e,
            "profileUrl": profile, "namedLinkUrl": named_url, "email": email, "personalWebsiteUrl": personal, "googleScholarUrl": scholar, "researchAreas": areas})
    return records


def minimized_math_feed(fetcher):
    """Execute the directory's exact public POST, retaining rendered fields only."""
    cache = fetcher.cache / "math-faculty-minimized.json"
    if cache.exists() and not fetcher.refresh:
        try:
            cached = json.loads(cache.read_text())
            observed = dt.datetime.fromisoformat(cached["meta"]["observedAt"])
            if observed.tzinfo and fetcher.max_cache_age_days > 0:
                age = dt.datetime.now(dt.UTC) - observed
                if dt.timedelta(days=-1) <= age <= dt.timedelta(days=fetcher.max_cache_age_days):
                    return cached
        except (OSError, ValueError, KeyError, TypeError):
            pass
    # Check this endpoint's robots policy through the shared fetcher first.
    gate, _ = fetcher.fetch(MATH_FEED)
    meta = {"sourceUrl": MATH_FEED, "observedAt": now(), "status": "error", "requestMethod": "POST", "requestScope": "department_code[]=000212", "rawResponsePersisted": False}
    if gate["status"] in {"robots_denied", "robots_unavailable"}:
        meta["status"] = gate["status"]
        return {"meta": meta, "rows": []}
    try:
        request = urllib.request.Request(MATH_FEED, data=urllib.parse.urlencode({"department_code[]": "000212"}).encode(), headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "ResearchAtlasEvidenceBot/2.0"})
        with urllib.request.urlopen(request, timeout=fetcher.timeout) as response:
            raw = response.read(1_500_001)
        if len(raw) > 1_500_000:
            raise ValueError("response_exceeds_size_limit")
        rows = []
        for person in json.loads(raw):
            category = person.get("employee_class")
            state = person.get("employee_status")
            if state in {"Retired", "Terminated", "Deceased"}:
                continue
            if category == "Academic: Emeriti":
                role = "Professor Emeritus"
            elif category == "Academic: Faculty" and person.get("job_code") in MATH_JOB_TITLES:
                role = MATH_JOB_TITLES[person["job_code"]]
            else:
                continue
            rows.append({"name": clean(person.get("employee_preferred_first_name_current", "") + " " + person.get("employee_preferred_last_name_current", "")), "email": person.get("identity_email_address_current", ""), "role": role})
        meta.update(status="ok", sha256=hashlib.sha256(raw).hexdigest(), displayedFacultyAssociationCount=len(rows), filterEvidenceUrls=["https://www.math.ucsd.edu/sites/www.math.ucsd.edu/themes/bootstrap_math/js/faculty_list.js", "https://www.math.ucsd.edu/sites/www.math.ucsd.edu/themes/bootstrap_math/js/emeriti_list.js"])
        result = {"meta": meta, "rows": rows}
        cache.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        return result
    except Exception as error:
        meta.update(status="fetch_error", error=str(error)[:300])
        return {"meta": meta, "rows": []}


def math_records(feed, profile_meta, body):
    if feed["meta"]["status"] != "ok":
        return []
    profiles = json.loads(body) if profile_meta["status"] == "ok" and body else []
    by_email = {r.get("field_work_email", "").lower(): r for r in profiles if r.get("field_work_email")}
    records = []
    for person in feed["rows"]:
        if not valid_person_name(person["name"]):
            continue
        profile = by_email.get(person["email"].lower(), {})
        url = canonical_url(urllib.parse.urljoin(MATH_FACULTY, profile.get("view_node_1", ""))) if profile.get("view_node_1") else ""
        status = appointment_status(person["role"])
        directory = MATH_EMERITI if status == "emeritus" else MATH_FACULTY
        e = evidence(feed["meta"], "official_directory_public_feed_rendering_rules", f"Mathematics directory | {person['name']} | {person['role']}")
        e["directoryUrl"] = directory
        records.append({"name": person["name"], "department": "Mathematics", "listedRole": person["role"], "appointmentStatus": status,
            "directorySection": "Emeriti Faculty" if status == "emeritus" else "Faculty", "sourceUrl": directory, "observedAt": feed["meta"]["observedAt"], "evidence": e,
            "profileUrl": url, "namedLinkUrl": url, "email": person["email"], "personalWebsiteUrl": canonical_url(profile.get("field_website", "")),
            "googleScholarUrl": "", "researchAreas": [profile["field_primary_research_area"]] if profile.get("field_primary_research_area") else [],
            "metadataSourceUrl": MATH_PROFILES if profile else None,
            "metadataEvidence": evidence(profile_meta, "official_directory_profile_metadata_feed", f"{person['name']} | profile metadata joined on explicit public professional email") if profile else None})
    return records


def physics_records(meta, body):
    records = []
    for row in json.loads(body):
        if row.get("employee_class") not in {"Academic: Faculty", "Academic: Emeriti"}:
            continue
        name = clean(row.get("first_name", "") + " " + row.get("last_name", ""))
        if not valid_person_name(name):
            continue
        role = clean(row.get("emeritus_title") or row.get("display_title") or row.get("employee_class"))
        status = "emeritus" if row.get("employee_class") == "Academic: Emeriti" else appointment_status(role)
        email = row.get("identity_email_address_current") or row.get("email") or ""
        # This is the exact link construction in the official directory's JS.
        profile = "https://physics.ucsd.edu/people/profile?id=" + urllib.parse.quote(email.replace("@ucsd.edu", "")) if email else ""
        e = evidence(meta, "official_faculty_directory_public_feed", f"{name} | {role} | {row.get('employee_class')}")
        e["directoryUrl"] = PHYSICS_DIRECTORY
        records.append({"name": name, "department": "Physics", "listedRole": role, "appointmentStatus": status,
            "directorySection": "Faculty Profiles", "sourceUrl": PHYSICS_DIRECTORY, "observedAt": meta["observedAt"], "evidence": e,
            "profileUrl": profile, "namedLinkUrl": profile, "email": email, "personalWebsiteUrl": "", "googleScholarUrl": "", "researchAreas": []})
    return records


def biology_profile_patches(meta, body, professors):
    """The Biology website's public profile feed carries no names. Each entry's
    profile path is the person's UCSD username, so it is linked only when that
    username already identifies exactly one Biological Sciences professor, by
    the same profile URL or as the local part of their @ucsd.edu address. The
    feed never creates people and never overrides a field with its own evidence."""
    by_username = defaultdict(list)
    for professor in professors:
        if professor.get("department") != BIOLOGY_DEPARTMENT:
            continue
        keys = set()
        match = re.search(r"biology\.ucsd\.edu/research/faculty/([^/?#]+)", str(professor.get("officialProfileUrl", "")).lower())
        if match:
            keys.add(match[1])
        email = str(professor.get("email", "")).lower()
        if email.endswith("@ucsd.edu"):
            keys.add(email.split("@")[0])
        for key in keys:
            by_username[key].append(professor)
    patches, unmatched = {}, 0
    for row in json.loads(body):
        profile = "https:" + row["profileURL"] if str(row.get("profileURL", "")).startswith("//") else str(row.get("profileURL", ""))
        username = profile.rstrip("/").rsplit("/", 1)[-1].lower()
        people = by_username.get(username, [])
        if not row.get("hasProfile") or len(people) != 1:
            unmatched += 1
            continue
        person = people[0]
        known = (person.get("fieldEvidence") or {})
        sections = [clean(s.get("title", "")) for s in row.get("sections", []) if clean(s.get("title", ""))]
        base = {**evidence(meta, "biology_profile_feed_username_link", f"{profile} | sections: {', '.join(sections)}"), "identityMatchConfidence": "medium"}
        patch = {"fieldEvidence": {}}
        if not individual_profile(person.get("officialProfileUrl", "")) and individual_profile(profile):
            patch["officialProfileUrl"] = profile
            patch["fieldEvidence"]["officialProfileUrl"] = {**base, "evidence": f"Profile feed entry → {profile}"}
        summary = clean(row.get("researchSummary", ""))
        if len(summary) >= 30 and not known.get("researchSummary"):
            patch["researchSummary"] = summary[:1000]
            patch["fieldEvidence"]["researchSummary"] = {**base, "method": "biology_profile_feed_research_summary", "evidence": summary}
        lab = str(row.get("labURL", "")).strip()
        if re.match(r"https?://", lab) and not known.get("personalWebsiteUrl") and person.get("personalWebsiteUrl") in {None, "", MISSING}:
            patch["personalWebsiteUrl"] = canonical_url(lab)
            patch["fieldEvidence"]["personalWebsiteUrl"] = {**base, "method": "biology_profile_feed_lab_url", "evidence": f"Lab URL: {lab}"}
        if sections:
            patch["researchAreasFromDirectory"] = sections
            patch["fieldEvidence"]["researchAreasFromDirectory"] = {**base, "method": "biology_profile_feed_sections", "evidence": "Sections: " + ", ".join(sections)}
        if patch["fieldEvidence"]:
            patches[person["id"]] = patch
    return patches, unmatched


def legacy_initials_compatible(full_name, legacy_name):
    """Allow observed full names to expand compatible legacy initials only.

    The caller also requires the same department and an unambiguous directory
    given-name/surname combination. No full name is generated from initials.
    """
    full, old = identity_name(full_name).split(), identity_name(legacy_name).split()
    if len(full) < 2 or len(old) < 2 or len(full[0]) < 2:
        return False
    # Sources sometimes omit a leading initial, e.g. F. Thomas Bond.
    if len(old[0]) == 1 and old[1:] == full:
        return True
    suffix = 0
    while suffix < min(len(full), len(old)) - 1 and full[-1 - suffix] == old[-1 - suffix]:
        suffix += 1
    if not suffix:
        return False
    full_given, old_given = full[:-suffix], old[:-suffix]
    if not all(len(t) == 1 for t in old_given):
        return False
    return all(a[0] == b for a, b in zip(full_given, old_given))


def match_existing(record, professors, records=()):
    profile = profile_identity(record["profileUrl"])
    if profile:
        matches = [p for p in professors if profile_identity(p.get("officialProfileUrl", "")) == profile]
        if len(matches) == 1:
            return matches[0], "same_individual_profile"
    email = record.get("email", "").lower()
    if email:
        matches = [p for p in professors if p.get("email", "").lower() == email]
        # Same-department duplicates are retained for the main reconciliation;
        # use a full-name match to select a known ID, never create another.
        if len(matches) == 1:
            return matches[0], "same_public_professional_email"
    full = identity_name(record["name"])
    matches = [p for p in professors if identity_name(p["name"]) == full]
    if matches:
        return sorted(matches, key=lambda p: (p["department"] != record["department"], p["id"]))[0], "same_full_name"
    tokens = full.split()
    candidates = []
    for p in professors:
        other = identity_name(p["name"]).split()
        if len(other) >= 2 and tokens[0] == other[0] and tokens[-1] == other[-1] and len(tokens[0]) > 1:
            middle = [t for t in tokens[1:-1] if len(t) > 1]
            other_middle = [t for t in other[1:-1] if len(t) > 1]
            if not middle or not other_middle or all(t in other_middle for t in middle):
                candidates.append(p)
    if len(candidates) == 1:
        return candidates[0], "unique_full_first_last"
    initial_candidates = [p for p in professors if p["department"] == record["department"] and legacy_initials_compatible(record["name"], p["name"])]
    if len(initial_candidates) == 1:
        # Two different observed full names must not silently expand one H. Kim.
        rivals = {identity_name(r["name"]) for r in records if r["department"] == record["department"] and legacy_initials_compatible(r["name"], initial_candidates[0]["name"])}
        if len(rivals) <= 1:
            return initial_candidates[0], "same_department_unique_legacy_initials_expanded_by_directory"
    return None, "new_explicit_directory_person"


def build_evidence(records, professors):
    known = list(professors)
    additions, patches, uncertain = [], {}, []
    seen = set()
    for row in records:
        key = (row["sourceUrl"], normalized(row["name"]), row["listedRole"])
        if key in seen:
            continue
        seen.add(key)
        person, method = match_existing(row, known, records)
        if not person:
            # Retain a possible alias for review instead of cloning a known name
            # when the exact same email belongs to multiple legacy records.
            email_matches = [p for p in known if row.get("email") and p.get("email", "").lower() == row["email"].lower()]
            if email_matches:
                uncertain.append({"listing": row, "reason": "professional_email_matches_multiple_legacy_records", "candidateProfessorIds": [p["id"] for p in email_matches]})
                continue
            name_tokens = identity_name(row["name"]).split()
            possible = []
            for old in known:
                old_tokens = identity_name(old["name"]).split()
                if old["department"] != row["department"] or len(old_tokens) < 2 or len(old_tokens[0]) != 1 or old_tokens[0] != name_tokens[0][0]:
                    continue
                if old_tokens[-1] == name_tokens[-1] or ("catalog.ucsd.edu" in old.get("officialProfileUrl", "") and old_tokens[-1] == name_tokens[-1] + "a"):
                    possible.append(old["id"])
            if possible:
                uncertain.append({"listing": row, "reason": "possible_legacy_alias_requires_identity_review", "candidateProfessorIds": possible})
                continue
            person = {"id": "ucsd-faculty-live-" + normalized(row["name"]).replace(" ", "-"), "name": row["name"], "institution": "University of California San Diego", "department": row["department"],
                "officialProfileUrl": row["profileUrl"] or row["sourceUrl"], "personalWebsiteUrl": row["personalWebsiteUrl"] or MISSING, "email": row["email"] or MISSING,
                "researchAreas": row["researchAreas"], "researchSummary": MISSING, "googleScholarUrl": row["googleScholarUrl"] or MISSING,
                "labAffiliation": MISSING, "labAffiliationUrl": MISSING, "recruitingStatus": "Unknown", "recruitingEvidence": {"text": "", "url": ""},
                "sourceUrls": list(dict.fromkeys([row["sourceUrl"], row["profileUrl"]] if row["profileUrl"] else [row["sourceUrl"]])),
                "lastVerified": row["observedAt"][:10], "verificationScope": "name, displayed directory appointment, and explicit directory links only", "legacyKind": "live_faculty_directory"}
            additions.append(person)
            known.append(person)
        patch = patches.setdefault(person["id"], {"directoryListings": [], "departmentAffiliations": [], "fieldEvidence": {}})
        listing = {k: row[k] for k in ["name", "department", "listedRole", "appointmentStatus", "directorySection", "sourceUrl", "observedAt", "evidence"]}
        listing["identityMatchMethod"] = method
        listing["identityMatchConfidence"] = "medium" if "initials" in method else "high"
        if row.get("namedLinkUrl"):
            listing["namedLinkUrl"] = row["namedLinkUrl"]
        patch["directoryListings"].append(listing)
        if row["department"] not in patch["departmentAffiliations"]:
            patch["departmentAffiliations"].append(row["department"])
        e = row["evidence"]
        patch["fieldEvidence"].setdefault("name", e)
        if "initials" in method or identity_name(person["name"]) != normalized(person["name"]) and identity_name(person["name"]) == identity_name(row["name"]):
            patch["name"] = row["name"]
        patch.setdefault("nameAliases", [])
        if row["name"] != person["name"] and row["name"] not in patch["nameAliases"]:
            patch["nameAliases"].append(row["name"])
        if "appointmentStatus" not in patch or row["appointmentStatus"] in {"emeritus", "former", "deceased"}:
            patch["appointmentStatus"] = row["appointmentStatus"]
            patch["fieldEvidence"]["appointmentStatus"] = e
        # Only replace an unknown, catalog-only, or generic directory URL.
        # A known individual official profile is never downgraded.
        if row["profileUrl"] and (person in additions or not individual_profile(person.get("officialProfileUrl", ""))):
            patch["officialProfileUrl"] = row["profileUrl"]
            patch["fieldEvidence"]["officialProfileUrl"] = {**(row.get("metadataEvidence") or e), "method": "explicit_individual_profile_link_from_directory", "evidence": f"{row['name']} → {row['profileUrl']}"}
        for field in ["email", "personalWebsiteUrl", "googleScholarUrl"]:
            # An official card fills a missing value, replaces a legacy value that
            # never had evidence, or corroborates an identical value. A value with
            # its own field evidence is never overwritten by a directory card.
            current = person.get(field)
            unverified = not (person.get("fieldEvidence") or {}).get(field)
            same = isinstance(current, str) and current.strip().lower() == str(row.get(field, "")).strip().lower()
            if row.get(field) and (person in additions or current in {None, "", MISSING} or unverified or same):
                patch[field] = row[field]
                patch["fieldEvidence"][field] = {**e, "method": "explicit_person_card_value", "evidence": f"{row['name']} | {field}: {row[field]}"}
        if row.get("researchAreas"):
            patch["researchAreasFromDirectory"] = row["researchAreas"]
            patch["fieldEvidence"]["researchAreasFromDirectory"] = {**(row.get("metadataEvidence") or e), "evidence": f"{row['name']} | Research Areas: {', '.join(row['researchAreas'])}"}
        if person in additions:
            if not row["profileUrl"]:
                patch["fieldEvidence"].setdefault("officialProfileUrl", {**e, "method": "official_directory_listing_no_individual_profile_link", "evidence": f"{row['name']} is listed on {row['sourceUrl']}; no individual official profile link was supplied."})
            # New records can be consumed directly without losing provenance.
            person.update({k: v for k, v in patch.items() if k not in {"directoryListings", "departmentAffiliations", "fieldEvidence"}})
            person["directoryListings"] = patch["directoryListings"]
            person["departmentAffiliations"] = patch["departmentAffiliations"]
            person["fieldEvidence"] = patch["fieldEvidence"]
    return additions, patches, uncertain


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--atlas", type=Path, default=ROOT / "data/research-atlas.json")
    cli.add_argument("--output", type=Path, default=ROOT / "data/ucsd/faculty-evidence.json")
    cli.add_argument("--cache-dir", type=Path, default=Path(tempfile.gettempdir()) / "research-atlas-faculty-cache")
    cli.add_argument("--refresh", action="store_true")
    cli.add_argument("--max-cache-age-days", type=float, default=30, help="Reuse observations no older than this many days; 0 forces re-fetch.")
    args = cli.parse_args()
    professors = json.loads(args.atlas.read_text())["professors"]
    fetcher = DirectoryFetcher(args.cache_dir, timeout=25, delay=.25, refresh=args.refresh, max_cache_age_days=args.max_cache_age_days)
    records, parse_report = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(lambda source: (source, *fetcher.fetch(source[2])), SOURCES))
    for source, meta, body in results:
        parsed = card_records(source, meta, body) if meta["status"] == "ok" and body else []
        records.extend(parsed)
        parse_report.append({"sourceId": source[0], "sourceUrl": source[2], "department": source[1], "listingCount": len(parsed), "status": "parsed" if parsed else meta["status"] if meta["status"] != "ok" else "no_explicit_faculty_cards"})
        print(source[0], meta["status"], len(parsed), flush=True)
    # Feeds are exposed by the two official public faculty-directory scripts.
    math_meta, math_body = fetcher.fetch(MATH_PROFILES)
    minimized = minimized_math_feed(fetcher)
    math = math_records(minimized, math_meta, math_body)
    records.extend(math)
    parse_report.append({"sourceId": "mathematics-public-directory", "department": "Mathematics", "sourceUrl": MATH_FACULTY, "listingCount": len(math), "status": "parsed" if math else minimized["meta"]["status"]})
    print("mathematics", minimized["meta"]["status"], len(math), flush=True)
    physics_meta, physics_body = fetcher.fetch(PHYSICS_FEED)
    physics = physics_records(physics_meta, physics_body) if physics_meta["status"] == "ok" and physics_body else []
    records.extend(physics)
    parse_report.append({"sourceId": "physics-public-directory", "department": "Physics", "sourceUrl": PHYSICS_DIRECTORY, "listingCount": len(physics), "status": "parsed" if physics else physics_meta["status"]})
    print("physics", physics_meta["status"], len(physics), flush=True)
    additions, patches, uncertain = build_evidence(records, professors)
    biology_meta, biology_body = fetcher.fetch(BIOLOGY_PROFILES_FEED)
    biology, biology_unmatched = biology_profile_patches(biology_meta, biology_body, professors) if biology_meta["status"] == "ok" and biology_body else ({}, 0)
    for pid, patch in biology.items():
        target = patches.setdefault(pid, {"directoryListings": [], "departmentAffiliations": [], "fieldEvidence": {}})
        for field, value in patch.items():
            if field == "fieldEvidence":
                for key, proof in value.items():
                    target["fieldEvidence"].setdefault(key, proof)
            else:
                target.setdefault(field, value)
    parse_report.append({"sourceId": "biology-public-profile-feed", "department": BIOLOGY_DEPARTMENT, "sourceUrl": BIOLOGY_PROFILES_FEED, "linkedProfiles": len(biology), "unlinkedFeedEntries": biology_unmatched, "status": "parsed" if biology else biology_meta["status"]})
    print("biology-profile-feed", biology_meta["status"], len(biology), "linked,", biology_unmatched, "unlinked", flush=True)
    fetches = list(fetcher.results.values()) + [minimized["meta"]]
    output = {"schemaVersion": "1.0.0", "generatedAt": now(), "professors": additions, "byProfessorId": patches, "fetches": fetches, "sources": parse_report, "uncertainListings": uncertain,
        "coverage": {"rawDirectoryListingCount": len(records), "directoryListingCount": sum(len(p["directoryListings"]) for p in patches.values()), "distinctProfessorsObserved": len(patches), "newProfessorCount": len(additions),
            "existingProfessorsUpdated": len(patches) - len(additions), "departmentsObserved": len({r["department"] for r in records}),
            "newProfessorsByDepartment": dict(Counter(p["department"] for p in additions)), "listingsByStatus": dict(Counter(r["appointmentStatus"] for p in patches.values() for r in p["directoryListings"])),
            "individualProfileUpgrades": sum("officialProfileUrl" in p and k not in {a["id"] for a in additions} for k, p in patches.items()), "uncertainListingCount": len(uncertain),
            "fetchFailures": sum(m["status"] != "ok" for m in fetches)},
        "warnings": ["A current directory observation does not prove current employment; exact listed roles and explicit emeritus/adjunct/affiliate labels are retained.",
            "Existing person IDs and primary departments are preserved; departmentAffiliations records additional directly observed directory memberships.",
            "Individual profile URLs are explicit directory links; their linked contents have not all been re-fetched by this collector.",
            "Names without full given-name evidence do not create new professors. Public staff, student, and postdoc feeds are excluded.",
            "The Mathematics endpoint is filtered using the public directory's own rules; raw employee data and unrelated personnel fields are not retained.",
            "Biology profile-feed entries have no names; they are linked only when their username matches exactly one existing Biological Sciences profile URL or @ucsd.edu address (medium confidence), and never create people.",
            "Absence from these directories is not evidence that an existing professor has left UCSD."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(output["coverage"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
