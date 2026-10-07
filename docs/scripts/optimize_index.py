"""Slim research-index.json for faster page loads.

The build crawler emits a verbose index (discovery metadata, full enrichment
payloads, confidence flags, etc.) that the UI never reads. This script
rewrites the file in place with only the fields the front-end consumes,
minified, and with empty values stripped. On the current dataset this cuts
~12 MB to ~4 MB without changing any UI-visible field.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "ucsd" / "research-index.json"

# Fields kept on every record (in roughly the order the UI reads them).
KEEP_FIELDS = {
    "id",
    "kind",
    "name",
    "title",
    "department",
    "departments",
    "affiliations",
    "summary",
    "interests",
    "methods",
    "researchDirections",
    "audiences",
    "people",
    "contacts",
    "links",
    "linkedinSearchUrl",
}


def _enriched(record: dict) -> bool:
    enrichment = record.get("enrichment") or {}
    personal = enrichment.get("personalSite") or {}
    profile = enrichment.get("profile") or {}
    return bool(personal.get("checked") or profile.get("checked"))


def _slim_link(link: dict) -> dict | None:
    if not isinstance(link, dict):
        return None
    label = link.get("label")
    url = link.get("url")
    if not url:
        return None
    out = {"label": label or "Link", "url": url}
    return out


def _dedupe_links(links):
    seen = set()
    out = []
    for raw in links or []:
        slim = _slim_link(raw)
        if not slim:
            continue
        key = (slim["label"], slim["url"])
        if key in seen:
            continue
        seen.add(key)
        out.append(slim)
    return out


def _slim_contact(contact: dict) -> dict | None:
    if not isinstance(contact, dict):
        return None
    value = contact.get("value")
    if not value:
        return None
    out = {"type": contact.get("type") or "contact", "value": value}
    href = contact.get("href")
    if href and href != f"mailto:{value}":
        out["href"] = href
    return out


def slim_record(record: dict) -> dict:
    out: dict = {}
    for key in KEEP_FIELDS:
        if key not in record:
            continue
        value = record[key]
        if value in (None, "", [], {}):
            continue
        if key == "links":
            value = _dedupe_links(value)
            if not value:
                continue
        elif key == "contacts":
            value = [c for c in (_slim_contact(c) for c in value) if c]
            if not value:
                continue
        elif key == "departments":
            # If the only entry equals `department`, drop it.
            primary = record.get("department")
            value = [d for d in value if d]
            if value == [primary] or not value:
                continue
        elif key == "affiliations":
            value = [a for a in value if isinstance(a, dict) and a.get("department")]
            if not value:
                continue
        out[key] = value
    if _enriched(record):
        out["enriched"] = 1
    return out


def slim_index(payload: dict) -> dict:
    records = [slim_record(r) for r in payload.get("records", [])]
    return {
        "schemaVersion": payload.get("schemaVersion", 1),
        "generatedAt": payload.get("generatedAt"),
        "university": payload.get("university"),
        # `sources` is referenced from coverage entries but the UI does not
        # list raw source entries, so we drop them to save ~3 KB.
        "coverage": payload.get("coverage", []),
        "facets": payload.get("facets", {}),
        "records": records,
    }


def main() -> int:
    if not DATA_PATH.exists():
        print(f"missing: {DATA_PATH}", file=sys.stderr)
        return 1
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    slim = slim_index(raw)
    DATA_PATH.write_text(
        json.dumps(slim, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    before = sum(1 for _ in raw.get("records", []))
    after = len(slim["records"])
    size = DATA_PATH.stat().st_size
    print(f"wrote {DATA_PATH} ({size:,} bytes, {after}/{before} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
