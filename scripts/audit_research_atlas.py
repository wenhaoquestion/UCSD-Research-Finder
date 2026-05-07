#!/usr/bin/env python3
"""Print quality checks for the Research Atlas dataset."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "research-atlas.json"
LAB_TOKEN_RE = re.compile(r"(^|[^a-z])lab(orator(?:y|ies))?([^a-z]|$)|research[-_\s]?group|research[-_\s]?lab", re.I)

SUSPICIOUS_URL_PARTS = [
    "urldefense.com",
    "research/research-topics/index",
    "research/academic-departments",
    "facilities-resources",
    "undergraduate/faq",
    "amazon.com",
    "sio_auth",
    "github.com/",
    "/publications",
    "/publication",
    "/project/",
    "/projects/",
    "faculty-and-research/index",
]


def url_key(url: str) -> str:
    value = (url or "").lower().split("#", 1)[0].split("?", 1)[0].rstrip("/")
    value = re.sub(r"^https?://", "", value)
    value = re.sub(r"^www\.", "", value)
    value = value.replace("/index.html", "").replace("/index.htm", "").replace("/index.php", "")
    host = value.split("/", 1)[0]
    if LAB_TOKEN_RE.search(host):
        return host
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_path", nargs="?", type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()

    data = json.loads(args.data_path.read_text(encoding="utf-8"))
    professors = data.get("professors", [])
    labs = data.get("labs", [])
    departments = sorted({item["department"] for item in professors + labs})
    lab_departments = sorted({item["department"] for item in labs})

    print(f"Professors: {len(professors)}")
    print(f"Labs: {len(labs)}")
    print(f"Departments with professor/lab records: {len(departments)}")
    print(f"Departments with labs: {len(lab_departments)}")

    missing = [lab for lab in labs if lab.get("labWebsiteUrl") in {"", "Not found", "Unknown"}]
    print(f"Missing lab URLs: {len(missing)}")

    by_url = defaultdict(list)
    for lab in labs:
        by_url[url_key(lab.get("labWebsiteUrl", ""))].append(lab)
    duplicate_urls = [items for items in by_url.values() if len(items) > 1]
    print(f"Duplicate URL groups: {len(duplicate_urls)}")

    by_pi = defaultdict(list)
    for lab in labs:
        pi = lab.get("principalInvestigator")
        if pi and pi not in {"Not found", "Unknown"}:
            by_pi[(lab["department"], pi)].append(lab)
    duplicate_pi = [items for items in by_pi.values() if len(items) > 1]
    print(f"Same-PI multi-lab groups: {len(duplicate_pi)}")

    print("\nTop lab departments:")
    for department, count in Counter(lab["department"] for lab in labs).most_common(20):
        print(f"  {count:4d}  {department}")

    print("\nSuspicious lab URL matches:")
    suspicious_total = 0
    for part in SUSPICIOUS_URL_PARTS:
        hits = [lab for lab in labs if part in lab.get("labWebsiteUrl", "").lower()]
        suspicious_total += len(hits)
        print(f"  {part}: {len(hits)}")
    print(f"Total suspicious matches: {suspicious_total}")

    if duplicate_urls:
        print("\nDuplicate URL examples:")
        for group in duplicate_urls[:10]:
            print(f"  {url_key(group[0].get('labWebsiteUrl', ''))}")
            for lab in group:
                print(f"    - {lab['department']}: {lab['labName']}")

    if duplicate_pi:
        print("\nSame-PI multi-lab examples:")
        for group in duplicate_pi[:10]:
            print(f"  {group[0]['department']}: {group[0]['principalInvestigator']}")
            for lab in group:
                print(f"    - {lab['labName']} | {lab['labWebsiteUrl']}")


if __name__ == "__main__":
    main()
