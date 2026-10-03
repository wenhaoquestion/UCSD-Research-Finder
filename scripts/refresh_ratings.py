#!/usr/bin/env python3
"""Refresh public aggregate ratings, keeping platform, identity and provenance separate.

Only ordinary public HTML is requested; no login, private API or challenge bypass.
The RMP search budget is explicit, so an unsearched professor is never 'not found'.
Raw HTML is cached outside the dataset; review text is never exported.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import threading
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
UCSD = "University of California San Diego"
PI_URL = "https://pi-review.com/universities/158"
RMP_SEARCH = "https://www.ratemyprofessors.com/search/professors/1079?q="
USER_AGENT = "ResearchAtlas/2.0 (public academic directory research)"


def normalize(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char)).replace("'", "").replace("’", "")
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def name_key(value):
    parts = normalize(value).split()
    # A leading initial is part of the first name, not an ignorable middle
    # initial: A. C. Chen and S. Chen must never collapse into 'chen'.
    return " ".join(x for index, x in enumerate(parts) if index in (0, len(parts) - 1) or len(x) > 1)


def matched_records(rating, name_index):
    candidates = name_index.get(name_key(rating["matchedName"]), [])
    if len(candidates) < 2:
        return candidates
    exact = [p for p in candidates if normalize(p["name"]) == normalize(rating["matchedName"])]
    if exact:
        return exact
    # When middle initials differ, require a compatible department rather than
    # assigning one teaching score to every same-name person at the university.
    stopwords = {"and", "of", "the", "department", "science", "sciences", "engineering", "studies"}
    tokens = set(normalize(rating.get("matchedDepartment", "")).split()) - stopwords
    if tokens:
        compatible = [p for p in candidates if tokens & (set(normalize(p.get("department", "")).split()) - stopwords)]
        if len(compatible) == 1 or (compatible and len({normalize(p["name"]) for p in compatible}) == 1):
            return compatible
    return []


def plain(value):
    value = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", value, flags=re.S | re.I)
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", value)).split())


def relay_store(source):
    match = re.search(r"window\.__RELAY_STORE__\s*=\s*", source)
    if not match:
        raise ValueError("Public HTML contains no Relay dataset; rendering or access may have changed")
    return json.JSONDecoder().raw_decode(source[match.end():])[0]


def rmp_teachers(source):
    store = relay_store(source)
    result = []
    for item in store.values():
        if item.get("__typename") != "Teacher":
            continue
        school = store.get(item.get("school", {}).get("__ref"), {})
        if school.get("legacyId") not in (None, 1079):
            continue
        if school.get("legacyId") is None and normalize(school.get("name")) != normalize(UCSD):
            continue
        if "avgRating" not in item or "numRatings" not in item:
            continue
        score, count = item.get("avgRating"), item.get("numRatings")
        if not isinstance(count, int) or count < 0:
            continue
        if count and (not isinstance(score, (float, int)) or not 0 < score <= 5):
            continue
        percent = item.get("wouldTakeAgainPercent")
        difficulty = item.get("avgDifficulty")
        result.append({
            "platform": "Rate My Professors", "status": "verified" if count else "no_reviews",
            "score": score if count else None, "scale": 5, "reviewCount": count,
            "sourceUrl": f"https://www.ratemyprofessors.com/professor/{item['legacyId']}",
            "matchedName": f"{item.get('firstName', '')} {item.get('lastName', '')}".strip(),
            "matchedInstitution": school.get("name", UCSD), "matchedDepartment": item.get("department"),
            "matchMethod": "name_and_ucsd_school_id_1079",
            "difficulty": difficulty if isinstance(difficulty, (int, float)) and 0 < difficulty <= 5 else None,
            "wouldTakeAgainPercent": round(percent, 1) if isinstance(percent, (int, float)) and 0 <= percent <= 100 else None,
            "latestReviewAt": None,
        })
    return result


class PublicFetcher:
    def __init__(self, cache_dir, refresh=False, max_cache_age_days=30):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.refresh = refresh
        self.max_cache_age_days = max_cache_age_days
        self.events = []
        self.blocked_hosts = set()
        self.lock = threading.Lock()

    def get(self, url):
        key = hashlib.sha256(url.encode()).hexdigest()
        body_path = self.cache_dir / (key + ".html")
        meta_path = self.cache_dir / (key + ".json")
        if not self.refresh and body_path.exists() and meta_path.exists():
            meta = json.loads(meta_path.read_text())
            observed = datetime.fromisoformat(meta["observedAt"])
            age_days = (datetime.now(timezone.utc) - observed).total_seconds() / 86400
            if age_days <= self.max_cache_age_days:
                source = body_path.read_text()
                meta.setdefault("contentSha256", hashlib.sha256(source.encode()).hexdigest())
                self.events.append({**meta, "cached": True})
                return source, meta["observedAt"]
        observed = datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(timespec="seconds")
        meta = {"url": url, "observedAt": observed, "method": "public_html"}
        host = urllib.parse.urlsplit(url).netloc
        if host in self.blocked_hosts:
            meta.update(status="skipped", error="Host refused or rate-limited this run; no further network request attempted")
            self.events.append(meta)
            raise RuntimeError(meta["error"])
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=25) as response:
                source = response.read(5_000_000).decode("utf-8", errors="replace")
                meta.update(status="ok", httpStatus=response.status, finalUrl=response.url, contentSha256=hashlib.sha256(source.encode()).hexdigest())
            body_path.write_text(source)
            meta_path.write_text(json.dumps(meta))
            self.events.append(meta)
            return source, observed
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (403, 429):
                with self.lock:
                    self.blocked_hosts.add(host)
            meta.update(status="unavailable", error=str(exc)[:240])
            self.events.append(meta)
            raise


def pi_ratings(fetcher, include_unreviewed=False):
    ratings, university = [], {}
    # The source sorts by review count. Stop as soon as an unreviewed profile appears.
    for page in range(1, 501 if include_unreviewed else 11):
        url = PI_URL if page == 1 else PI_URL + f"?page={page}"
        source, observed = fetcher.get(url)
        text = plain(source)
        for key, label in [("listedReviewCount", "Total Reviews"), ("listedPICount", "Total PIs")]:
            match = re.search(label + r":\s*(\d+)", text)
            if match and page == 1:
                university[key] = int(match[1])
        blocks = re.split(r'<div class="d-flex mb-sm-3 mb-2 shadow border">', source)[1:]
        if not blocks:
            raise ValueError("PI Review public directory markup changed")
        end = False
        for block in blocks:
            link = re.search(r'href="(/pis/\d+)"[^>]*>(.*?)</a>', block, re.S)
            if not link:
                continue
            text = plain(block.split('<!-- pagination')[0])
            score = re.search(r'(\d+(?:\.\d+)?)\s*/\s*5', text)
            count = re.search(r'\b(\d+)\s+reviews\b', text, re.I)
            department = re.search(r'<li class="text-muted">(.*?)</li>', block, re.S)
            if not score or not count:
                end = True
                if not include_unreviewed:
                    continue
            ratings.append({
                "platform": "PI Review", "status": "verified" if score and count else "no_reviews", "score": float(score[1]) if score and count else None, "scale": 5,
                "reviewCount": int(count[1]) if score and count else 0, "sourceUrl": "https://pi-review.com" + link[1],
                "observedAt": observed, "matchedName": plain(link[2]), "matchedInstitution": UCSD,
                "matchedDepartment": plain(department[1]) if department else None,
                "matchMethod": "name_and_ucsd_directory_158", "latestReviewAt": None,
                "evidenceUrl": url, "method": "public_directory_aggregate",
                "note": "PI Review is a separate mentoring-review platform; it is not ratemypi.com or a teaching score.",
            })
        if (end and not include_unreviewed) or (include_unreviewed and page * 10 >= university.get("listedPICount", 5000)):
            break
        if include_unreviewed and page % 25 == 0:
            print(f"PI Review: {page} directory pages checked", flush=True)
    university["observedProfiles"] = len(ratings)
    university["distinctObservedProfiles"] = len({r["sourceUrl"] for r in ratings})
    university["observedRatedProfiles"] = sum(r["status"] == "verified" for r in ratings)
    university["observedReviews"] = sum(r["reviewCount"] for r in ratings)
    return ratings, university


def priority(professor):
    department = professor.get("department", "").lower()
    return (
        not bool(professor.get("teaching", {}).get("courses")),
        not any(x in department for x in ["computer", "electrical", "cognitive", "nano", "bioengineering"]),
        not (professor.get("labAffiliationUrl") or "").startswith("https://"),
        professor["name"],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/research-atlas.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/ucsd/ratings-evidence.json")
    parser.add_argument("--cache-dir", default="/tmp/research-atlas-ratings-cache")
    parser.add_argument("--rmp-limit", type=int, default=300, help="Maximum distinct names to search; 0 disables RMP")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--max-cache-age-days", type=float, default=30, help="Reuse cached source responses for at most this many days, keeping their original observation time")
    parser.add_argument("--pi-all", action="store_true", help="Also match all unreviewed PI Review profiles (221 current directory pages)")
    args = parser.parse_args()
    professors = json.loads(args.input.read_text())["professors"]
    name_index = {}
    for p in professors:
        keys = {name_key(name) for name in [p["name"], *(p.get("aliasNames") or [])]}
        for key in keys:
            if key:
                name_index.setdefault(key, []).append(p)
    fetcher = PublicFetcher(args.cache_dir, args.refresh, args.max_cache_age_days)
    by_id, unmatched, platform_info = {}, [], []
    discovered_rmp = {}

    try:
        values, coverage = pi_ratings(fetcher, args.pi_all)
        for rating in values:
            matches = matched_records(rating, name_index)
            if matches:
                for p in matches:
                    by_id.setdefault(p["id"], {})["rateMyPI"] = rating
            else:
                unmatched.append({"platformKey": "rateMyPI", **rating})
        if args.pi_all and coverage.get("distinctObservedProfiles") == coverage.get("listedPICount"):
            directory_date = max(r["observedAt"] for r in values)
            directory_keys = {name_key(r["matchedName"]) for r in values}
            for p in professors:
                if "rateMyPI" in by_id.get(p["id"], {}):
                    continue
                keys = {name_key(name) for name in [p["name"], *(p.get("aliasNames") or [])]}
                ambiguous = bool(keys & directory_keys)
                by_id.setdefault(p["id"], {})["rateMyPI"] = {
                    "platform": "PI Review", "status": "needs_review" if ambiguous else "not_found",
                    "score": None, "scale": 5, "reviewCount": None, "sourceUrl": PI_URL,
                    "observedAt": directory_date, "method": "complete_public_directory_identity_search",
                    "note": "A name variant appears in the directory, but identity could not be assigned unambiguously." if ambiguous else "No exact identity match in the complete public UCSD directory checked in this run. Name variants may exist; this does not establish absence from the platform.",
                }
        platform_info.append({"key": "rateMyPI", "platform": "PI Review", "status": "ok", "sourceUrl": PI_URL, **coverage})
    except Exception as exc:
        platform_info.append({"key": "rateMyPI", "platform": "PI Review", "status": "unavailable", "sourceUrl": PI_URL, "error": str(exc)[:240]})

    candidates, seen = [], set()
    for p in sorted(professors, key=priority):
        key = name_key(p["name"])
        if key in seen:
            continue
        seen.add(key)
        candidates.append(p)
    candidates = candidates[:args.rmp_limit]

    def collect(professor):
        url = RMP_SEARCH + urllib.parse.quote(professor["name"])
        try:
            source, observed = fetcher.get(url)
            teachers = rmp_teachers(source)
            for rating in teachers:
                rating.update(observedAt=observed, evidenceUrl=url, method="public_search_embedded_aggregate")
            matches = [r for r in teachers if name_key(r["matchedName"]) == name_key(professor["name"])]
            if len(matches) == 1:
                result = matches[0]
                result.update(observedAt=observed, evidenceUrl=url, method="public_search_embedded_aggregate")
            else:
                result = {"platform": "Rate My Professors", "status": "needs_review" if matches else "not_found",
                          "score": None, "scale": 5, "reviewCount": None, "sourceUrl": url, "observedAt": observed,
                          "note": "Multiple exact-name matches" if matches else "No exact identity match in this public search response; this does not prove no profile exists."}
            return professor, result, teachers
        except Exception as exc:
            if isinstance(exc, ValueError):
                with fetcher.lock:
                    fetcher.blocked_hosts.add("www.ratemyprofessors.com")
            return professor, {"platform": "Rate My Professors", "status": "unavailable", "score": None,
                               "scale": 5, "reviewCount": None, "sourceUrl": url, "observedAt": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(timespec="seconds"),
                               "note": str(exc)[:180]}, []

    with ThreadPoolExecutor(max_workers=min(max(args.workers, 1), 4)) as executor:
        futures = [executor.submit(collect, p) for p in candidates]
        for index, future in enumerate(as_completed(futures), 1):
            professor, result, discovered = future.result()
            targets = matched_records(result, name_index) if result["status"] in ("verified", "no_reviews") else name_index[name_key(professor["name"])]
            for p in targets:
                by_id.setdefault(p["id"], {})["rateMyProfessors"] = result
            for rating in discovered:
                key = name_key(rating["matchedName"])
                if key in name_index:
                    discovered_rmp.setdefault(key, {})[rating["sourceUrl"]] = rating
            if index % 25 == 0:
                print(f"RMP: {index}/{len(candidates)} names checked", flush=True)
    # A search can expose additional full public aggregates. Reuse only exact
    # dataset identities, and refuse names that resolve to multiple profile IDs.
    for key, profiles in discovered_rmp.items():
        if len(profiles) == 1:
            rating = next(iter(profiles.values()))
        else:
            rating = {"platform": "Rate My Professors", "status": "needs_review", "score": None,
                      "scale": 5, "reviewCount": None, "sourceUrl": RMP_SEARCH + urllib.parse.quote(name_index[key][0]["name"]),
                      "observedAt": max(r["observedAt"] for r in profiles.values()),
                      "note": "Multiple matching public profile IDs; no aggregate selected."}
        for p in matched_records(rating, name_index) if len(profiles) == 1 else name_index[key]:
            by_id.setdefault(p["id"], {})["rateMyProfessors"] = rating
    # A query shared by middle-initial variants may verify only one directory
    # record. The other record was checked but unresolved, not 'not_checked'.
    selected_by_key = {name_key(p["name"]): p for p in candidates}
    events_by_url = {event["url"]: event for event in fetcher.events}
    for p in professors:
        if "rateMyProfessors" in by_id.get(p["id"], {}):
            continue
        selected = selected_by_key.get(name_key(p["name"]))
        if not selected:
            continue
        url = RMP_SEARCH + urllib.parse.quote(selected["name"])
        event = events_by_url.get(url, {})
        by_id.setdefault(p["id"], {})["rateMyProfessors"] = {
            "platform": "Rate My Professors", "status": "needs_review" if event.get("status") == "ok" else "unavailable",
            "score": None, "scale": 5, "reviewCount": None, "sourceUrl": url,
            "observedAt": event.get("observedAt"),
            "note": "A public query was checked, but profiles could not be unambiguously assigned to this directory record.",
        }
    search_events = [e for e in fetcher.events if e["url"].startswith(RMP_SEARCH)]
    successful_searches = sum(e["status"] == "ok" for e in search_events)
    platform_info.append({"key": "rateMyProfessors", "platform": "Rate My Professors", "status": "search_complete" if successful_searches == len(seen) else "partial",
                          "sourceUrl": RMP_SEARCH + "*", "namesSelected": len(candidates), "namesSearched": successful_searches,
                          "failedOrSkippedSearches": len(search_events) - successful_searches,
                          "totalDistinctDatasetNames": len(seen), "matchedNamesObserved": len(discovered_rmp),
                          "notes": "First publicly rendered response for each selected exact-name query; not an exhaustive platform-directory export. Unsearched names are not_checked; failed requests are unavailable. No exact match does not prove no profile exists. Scores refer to teaching."})
    result = {"schemaVersion": "1.0", "generatedAt": datetime.now(timezone.utc).isoformat(),
              "platforms": platform_info, "byProfessorId": by_id, "unmatched": unmatched,
              "fetches": sorted(fetcher.events, key=lambda e: e["url"]),
              "interpretation": "Anonymous aggregate ratings are source-reported opinions, not verified claims about mentoring or teaching quality. Check sample size and original dates."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = args.output.with_name(args.output.name + ".tmp")
    temporary_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    temporary_output.replace(args.output)
    print(json.dumps({"output": str(args.output), "professorRecords": len(by_id), "unmatched": len(unmatched), "platforms": platform_info}, indent=2))


if __name__ == "__main__":
    main()
