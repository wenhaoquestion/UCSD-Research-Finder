#!/usr/bin/env python3
"""Re-fetch catalog listings and lab URLs without equating HTTP 200 with factual verification.

Standard-library only. Public GETs, robots-aware, bounded concurrency, per-host pacing,
and atomic evidence output. The catalog is an undated listing, not proof of employment.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "ResearchAtlas/3.0 (public academic directory verification)"


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


class ListingParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.in_title = False
        self.row = None
        self.role = "Faculty listing"
        self.rows = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag in {"p", "h4"} and "faculty-staff-listing" in a.get("class", ""):
            self.row = {"tag": tag, "parts": []}

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.row is not None:
            self.row["parts"].append(data)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if self.row and tag == self.row["tag"]:
            text = re.sub(r"\s+", " ", "".join(self.row["parts"])).strip()
            if tag == "h4":
                self.role = text
            elif text:
                name = re.split(r",|\b(?:PhD|Ph\.D\.|MD|M\.D\.)\b", text)[0].strip()
                if 2 <= len(name.split()) <= 7:
                    self.rows.append({"name": name, "listingRole": self.role,
                                      "evidence": text, "contentDate": None})
            self.row = None


class Fetcher:
    def __init__(self, timeout=12):
        self.timeout = timeout
        self.lock = threading.Lock()
        self.hosts = {}
        self.robots = {}
        self.times = {}

    def request(self, url, limit=1500000):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,text/plain;q=0.9"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            body = r.read(limit + 1)
            if len(body) > limit:
                raise ValueError("response_too_large")
            return r.status, r.url, r.headers, body

    def fetch(self, url):
        observed = now()
        out = {"sourceUrl": url, "observedAt": observed}
        p = urllib.parse.urlsplit(url)
        if p.scheme not in {"http", "https"} or not p.hostname or p.username or p.password:
            return {**out, "status": "invalid_url"}
        origin = f"{p.scheme}://{p.netloc}"
        with self.lock:
            lock = self.hosts.setdefault(p.netloc.lower(), threading.Lock())
        try:
            with lock:
                if origin not in self.robots:
                    robot_url = origin + "/robots.txt"
                    rp = urllib.robotparser.RobotFileParser(robot_url)
                    try:
                        _, _, _, body = self.request(robot_url, 200000)
                        rp.parse(body.decode("utf-8", "replace").splitlines())
                    except urllib.error.HTTPError as e:
                        if e.code in {404, 410}:
                            rp.parse([])
                        else:
                            raise
                    self.robots[origin] = rp
                rp = self.robots[origin]
                if not rp.can_fetch(UA, url):
                    return {**out, "status": "robots_disallowed"}
                delay = max(.2, rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)
                wait = delay - (time.monotonic() - self.times.get(p.netloc, 0))
                if wait > 0:
                    time.sleep(wait)
                self.times[p.netloc] = time.monotonic()
            code, final, headers, body = self.request(url)
            out.update(status="reachable", httpStatus=code, finalUrl=final,
                       sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
            if urllib.parse.urlsplit(final).hostname == "accounts.google.com":
                out["status"] = "authentication_required"
            if "html" in headers.get("Content-Type", ""):
                parser = ListingParser()
                parser.feed(body.decode(headers.get_content_charset() or "utf-8", "replace"))
                out["title"] = parser.title.strip()
                if p.hostname == "catalog.ucsd.edu":
                    out["catalogListings"] = parser.rows
                    out["scope"] = "Undated catalog listing; retrieval does not establish current appointment."
                if re.search(r"page not found|access denied|just a moment|site not found|404", parser.title, re.I):
                    out["status"] = "needs_review"
            return out
        except urllib.error.HTTPError as e:
            return {**out, "status": "http_error", "httpStatus": e.code, "error": str(e)}
        except Exception as e:
            return {**out, "status": "unavailable", "error": f"{type(e).__name__}: {e}"[:300]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--atlas", type=Path, default=ROOT / "data/research-atlas.json")
    ap.add_argument("--out", type=Path, default=ROOT / "data/ucsd/source-checks.json")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--timeout", type=int, default=12)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--max-age-hours", type=float, default=24)
    args = ap.parse_args()
    atlas = json.loads(args.atlas.read_text())
    urls = {u for p in atlas["professors"] for u in p["sourceUrls"] if "catalog.ucsd.edu/faculty/" in u}
    urls.update(p["labWebsiteUrl"] for p in atlas["labs"] if p["labWebsiteUrl"].startswith("http"))
    urls.add("https://realportal.ucsd.edu/home.htm")
    previous = json.loads(args.out.read_text()).get("checks", []) if args.out.exists() else []
    # Retain audit receipts for quarantined legacy sources, too.
    prior = {c["sourceUrl"]: c for c in previous}
    reused = []
    targets = []
    for u in sorted(urls):
        c = prior.get(u)
        age = None
        if c:
            try:
                age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(c["observedAt"])).total_seconds() / 3600
            except (ValueError, KeyError):
                pass
        if not args.refresh and c and c["status"] == "reachable" and age is not None and 0 <= age < args.max_age_hours:
            reused.append(c)
        else:
            targets.append(u)
    urls = targets
    if args.limit:
        urls = urls[:args.limit]
    result = {"schemaVersion": "1.0", "generatedAt": now(),
              "policy": "Reachability checks are not claim verification. Catalog listings may be outdated.",
              "checks": reused + [c for u, c in prior.items() if u not in set(targets) and u not in {r["sourceUrl"] for r in reused}]}
    fetcher = Fetcher(args.timeout)
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetcher.fetch, u): u for u in urls}
        for f in concurrent.futures.as_completed(futures):
            result["checks"].append(f.result())
            completed += 1
            if completed % 50 == 0:
                write_json(args.out, result)
                print(f"Checked {completed}/{len(urls)} source URLs ({len(reused)} recent receipts reused)", flush=True)
    result["checks"].sort(key=lambda c: c["sourceUrl"])
    result["generatedAt"] = now()
    write_json(args.out, result)
    from collections import Counter
    print(json.dumps(dict(Counter(c["status"] for c in result["checks"]))))


if __name__ == "__main__":
    main()
