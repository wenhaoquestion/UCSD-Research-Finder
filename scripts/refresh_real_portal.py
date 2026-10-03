#!/usr/bin/env python3
"""Refresh public REAL opportunity cards through the page's own paginated search.

No login or account action. Only the loadCardsAjax read operation is used. Replace
the snapshot only after every advertised record is collected; never publish partial pages.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import http.cookiejar
import json
import re
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path
from refresh_labs import DOM, Node, clean
from refresh_source_checks import write_json

ROOT = Path(__file__).resolve().parents[1]
URL = "https://realportal.ucsd.edu/home.htm"
UA = "ResearchAtlas/3.0 (public academic directory verification)"
TYPES = {"236": "Co-curricular", "237": "Academic Internship Program", "238": "Experiential Learning Opportunity", "239": "Experiential Learning Opportunity"}


def description_text(node):
    if isinstance(node, str):
        return node
    if node.excluded() or node.tag == "label" or "grd" in node.attrs.get("class", "").split():
        return ""
    return " ".join(description_text(n) for n in node.children)


def parse_cards(markup, observed):
    resources = []
    for card in DOM(markup).root.walk():
        match = re.fullmatch(r"card(\d+)_(\d+)", card.attrs.get("id", ""))
        if not match or card.tag != "li":
            continue
        rid, config = match.groups()
        nodes = list(card.walk())
        header = next((n for n in nodes if "crd--more__header" in n.attrs.get("class", "").split()), None)
        if header is None:
            raise ValueError(f"Missing detail header for {rid}/{config}")
        title = next((n.text() for n in header.walk() if n.tag == "h3"), "")
        organization = next((n.text() for n in header.walk() if n.tag == "h4"), "Not found")
        fields = {}
        for n in nodes:
            if n.tag == "label" and n.parent:
                siblings = n.parent.children
                idx = siblings.index(n)
                value = next((s for s in siblings[idx+1:] if isinstance(s, Node)), None)
                if value and value.tag == "p":
                    fields[n.text()] = value.text()
        heading = next((n for n in nodes if n.tag == "h3" and n.text() == "Description"), None)
        description = "Not found"
        if heading and heading.parent:
            siblings = heading.parent.children
            idx = siblings.index(heading)
            description = clean(" ".join(description_text(n) for n in siblings[idx+1:])) or "Not found"
        fields["Description"] = description
        text = " ".join(fields.values())
        links = set()
        for n in nodes:
            href = n.attrs.get("href", "")
            if href.startswith(("https://", "http://")) and "orbis" not in href:
                links.add(href)
        links.update(re.findall(r"https?://[^\s<>\"']+", fields.get("Website", "")))
        if not title:
            raise ValueError("Empty REAL title")
        resources.append({"id": f"real-{config}-{rid}", "title": title, "organization": organization,
                          "resourceType": TYPES.get(config, "Public opportunity"), "portalRecordId": rid,
                          "portalConfigId": config, "description": description,
                          "yearOfActivity": fields.get("Year of Activity", "Not found"),
                          "applicationProcedure": fields.get("Application Procedure", "Not found"),
                          "contactEmails": sorted(set(re.findall(r"[\w.+%-]+@[\w.-]+\.[a-zA-Z]{2,}", text))),
                          "externalUrls": sorted(links), "detailFields": fields, "sourceUrl": URL,
                          "lastVerified": observed[:10], "observedAt": observed,
                          "verification": {"status": "source_checked", "scope": "Public opportunity card; availability and deadlines are not inferred.",
                                           "lastAttemptedAt": observed},
                          "fieldEvidence": {"listing": [{"sourceUrl": URL, "observedAt": observed,
                                                         "evidence": f"Public card {config}/{rid}: {title}",
                                                         "method": "public_portal_card"}]}})
    return resources


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "data/ucsd/real-portal-resources.json")
    ap.add_argument("--max-pages", type=int, default=100)
    args = ap.parse_args()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    opener.addheaders = [("User-Agent", UA)]
    def read(url, data=None):
        with opener.open(url, data, timeout=30) as r:
            return r.read(3000000).decode(r.headers.get_content_charset() or "utf-8", "replace")
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(read("https://realportal.ucsd.edu/robots.txt").splitlines())
    if not rp.can_fetch(UA, URL):
        raise SystemExit("REAL Portal disallows automated reads; existing snapshot preserved.")
    initial = read(URL)
    action = re.search(r"function loadCardsAjax[\s\S]+?action:\s*'([^']+)'", initial)
    if not action:
        raise SystemExit("Public search markup changed; existing snapshot preserved.")
    counts, records, pages = "{}", {}, []
    total = None
    for page in range(args.max_pages):
        body = urllib.parse.urlencode({"action": action[1], "resultCounts": counts, "filterGroups": "[]", "seed": "3141"}).encode()
        markup = read(URL, body)
        observed = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        match = re.search(r'js--total-record-count[^\n]+\.text\("(\d+)"', markup)
        cursor = re.search(r"resultCounts\s*=\s*'([^']+)'", markup)
        if not match or not cursor:
            raise SystemExit("Missing public pagination metadata; existing snapshot preserved.")
        reported = int(match[1])
        if total is not None and total != reported:
            raise SystemExit("Portal count changed during pagination; retry to obtain a consistent snapshot.")
        total = reported
        cards = parse_cards(markup, observed)
        for c in cards:
            if c["id"] in records:
                raise SystemExit("Duplicate pagination item; existing snapshot preserved.")
            records[c["id"]] = c
        pages.append({"page": page + 1, "sourceUrl": URL, "observedAt": observed,
                      "sha256": hashlib.sha256(markup.encode()).hexdigest(), "records": len(cards)})
        print(f"REAL {len(records)}/{total}", flush=True)
        if len(records) == total:
            break
        if not cards or cursor[1] == counts or len(records) > total:
            raise SystemExit("Pagination stalled; existing snapshot preserved.")
        counts = cursor[1]
        time.sleep(max(.4, rp.crawl_delay(UA) or rp.crawl_delay("*") or 0))
    if len(records) != total:
        raise SystemExit("Incomplete REAL collection; existing snapshot preserved.")
    output = {"schemaVersion": "2.0", "generatedAt": observed, "sourceName": "UC San Diego REAL Portal", "sourceUrl": URL,
              "totalOpportunitiesReportedByPortal": total, "importedCount": len(records),
              "note": "Fresh public cards, including co-curricular listings. A listed opportunity is not confirmation that applications are currently open.",
              "resources": sorted(records.values(), key=lambda x: x["id"]), "sourcePages": pages}
    write_json(args.out, output)


if __name__ == "__main__":
    main()
