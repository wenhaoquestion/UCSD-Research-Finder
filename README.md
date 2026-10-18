# Research Atlas

<!-- recovery-integration:start -->
当前本地正式数据：**6,182 位教授、902 个实验室**。Claude 与网站统一读取 `data/research-atlas.json`。

恢复批次存档与证据在 `data/ucsd/recovery-backfill-20261017/`；同步来源、SHA 和批次状态见 `docs/operations/desktop-recovery-integration-20261017.json`。历史来源日期保留；恢复数量不代表所有字段均已重新核验。
<!-- recovery-integration:end -->

A static UC San Diego research finder with faculty profiles, labs, contacts, teaching schedules, PI Review mentoring ratings, Rate My Professors teaching ratings, and public REAL Portal opportunities.

The served dataset uses **schema v3**. Each newly asserted field includes its source, supporting text, extraction method, and actual observation time. A successful page request does not verify every fact on the page. Current counts and unresolved gaps are generated in [the data quality report](docs/DATA_QUALITY_REPORT.md); machine-readable coverage by department is in `data/quality/refresh-report.json`.

## Run locally

Python 3.11+ is required for the collection scripts. The website itself needs only a static server.

```bash
python3 scripts/validate_data.py
python3 -m http.server 8000
```

Open http://localhost:8000. Search accepts professor names, research text, and course codes such as `CSE151A`. It tolerates typos (`nueroscience`), expands common abbreviations (`ml`, `nlp`, `hci`, `stats`) and Chinese field names (`机器学习`, `神经科学`), and falls back to records matching most words when none match all of them; the results say when either happened. Suggestions under the search box jump straight to a research field, department, or record. Research fields and departments are both two-level: a broad group (e.g. "Computing & AI", "Engineering") with optional detailed entries (e.g. "Machine learning & AI", "Electrical and Computer Engineering"). A strip above the results shows how the current results split across fields. Filters include courses, both rating platforms, and records with field evidence. Details show dates, sample sizes, all confirmed lab associations, and original sources. Former and emeritus faculty retain their source-reported category.

## Refresh public data

Collectors produce evidence files; the offline builder merges them into the website dataset. Failed requests remain distinguishable from missing matches. Existing values do not acquire a new verification date merely because the builder ran.

```bash
# Official lab directories and professor profiles; personal sites are one additional hop.
python3 scripts/refresh_labs.py --personal-sites --personal-site-limit 0
python3 scripts/refresh_faculty_directories.py
python3 scripts/refresh_source_checks.py

# Add newly discovered faculty before matching courses and ratings.
python3 scripts/rebuild_verified_atlas.py

# Official departmental schedules plus the campus Schedule of Classes.
# PDF sources require pdftotext and pdfplumber.
python3 scripts/refresh_teaching.py --refresh --cache-dir .cache/atlas/teaching

# PI Review's public directory and exact-name RMP searches.
python3 scripts/refresh_ratings.py --pi-all --rmp-limit 10000

# Replace REAL only after all advertised public cards are collected.
python3 scripts/refresh_real_portal.py

python3 scripts/rebuild_verified_atlas.py
python3 scripts/validate_data.py
python3 scripts/audit_research_atlas.py
python3 -m unittest discover -s tests -v
```

For the two PDF schedules, install `poppler`/`poppler-utils` for `pdftotext` and `pdfplumber` in the chosen Python environment, or pass `--pdf-python /path/to/python-with-pdfplumber`. Other teaching sources use the standard library and system `curl`. A failed PDF source is recorded as a coverage gap. To rebind already captured courses after the faculty roster changes, without requesting pages or changing observation timestamps:

```bash
python3 scripts/refresh_teaching.py --rematch
python3 scripts/rebuild_verified_atlas.py
```

### Campus Schedule of Classes

`refresh_teaching.py` also reads the registrar's public Schedule of Classes (`act.ucsd.edu`), which lists the instructor of record for every section. By default it collects the three latest published quarters for the departments mapped in `SOC_DEPARTMENTS`, one request per second, caching each department/quarter so an interrupted run resumes. Independent study, internships, exams, and review sessions are excluded; interdisciplinary programs and colleges are not mapped, because instructors are matched only within the owning department.

```bash
# Refresh only the Schedule of Classes; other sources keep their saved rows and dates.
python3 scripts/refresh_teaching.py --soc-only --cache-dir .cache/atlas/teaching
python3 scripts/refresh_teaching.py --soc-only --soc-terms FA25,WI26,SP26
```

### Re-scanning official profile pages

When the profile parser learns a new field, re-fetch already verified pages instead of only deferred ones. UCSD Profiles contributes its Overview section and Research keywords; Scripps profiles contribute their contact-card email, Research Topics, and research-profile link. A failed re-scan keeps the earlier verification and is recorded as `lastRescanAttempt`.

```bash
cd scripts
python3 run_profile_backfill.py --rescan-before 2026-10-07T00:00:00+00:00 --max-seconds 6900 --cache ../.cache/atlas/profiles
python3 run_profile_backfill.py --host scripps.ucsd.edu --rescan-before 2026-10-07T00:00:00+00:00 --cache ../.cache/atlas/profiles
```

Repeat a command until its `remainingDeferredProfiles` reaches 0. Both hosts are spaced at 10 seconds per request.

### Rate limits, caches, and continuation

UCSD Profiles publishes a **10-second crawl delay**. The default lab refresh defers uncached slow-host profiles rather than ignoring that rule. Complete them in resumable batches:

```bash
python3 scripts/refresh_labs.py --include-slow-profiles --slow-profile-limit 60 --personal-sites --personal-site-limit 0
```

Fresh cached pages do not consume the slow-host budget; later runs advance to remaining pages. Lab and rating caches have a default 30-day maximum age. `--refresh` forces new requests; cache reuse preserves the original `observedAt`. Collector cache paths can be placed under `.cache/atlas` for durable local or CI runs. Never clear the cache between continuation batches.

The lab collector also retains the complete existing output as its incremental baseline. A limited refresh or a missing local HTML cache does not erase cloud evidence for unattempted profiles. New failures update the latest check while keeping historical field evidence and its original dates. Keep `data/ucsd/lab-evidence.json` when moving a completed capture between computers.

### Broad UCSD coverage queue

The October 2026 expansion has a separate resumable public queue. It starts from
the 59 saved departments, discovered official directory links, campus institute
directories, existing lab destinations, and the prior unresolved candidates, and public person pages in the official UCSD
Profiles sitemap. Person pages are candidates; only their explicit appointment
table can establish a new faculty listing. The full profile pass takes roughly
30–40 hours at the published rate, with recent verified evidence retained.
Directory discovery follows two explicit link hops; lab identity pages and new
faculty profile links are checked separately. This is a documented source scope,
not a claim that every UCSD entity has a public page or has been verified.

```bash
python3 scripts/collect_ucsd_coverage.py --workers 8
python3 scripts/review_ucsd_coverage.py
# Review per-URL decisions in data/ucsd/coverage-20261016-decisions.json.
python3 scripts/apply_ucsd_coverage.py
python3 scripts/rebuild_verified_atlas.py
python3 scripts/validate_data.py
```

The collector uses system `curl` with TLS verification and no automatic redirects.
It checks target robots at every redirect and persists per-host request clocks;
UCSD Profiles has a ten-second minimum. Retries are bounded and honor Retry-After.
The ignored `.cache/coverage-20261016` directory holds responses and atomic queue
checkpoints. Creating a `STOP` file there requests a graceful checkpoint; remove
it before resuming. Recent identity-verified profile evidence can be retained
with its original observation time. Counts distinguish those retained records,
successful requests, unresolved checks, and pending work.

Review output separates centers/institutes, possible lab aliases, unsupported
personnel cards, and accepted additions. Export refuses an incomplete eligible
queue. Accepted evidence is saved in `coverage-expansion-evidence.json`; original
captures remain available. An unavailable website never means the lab closed.

Use the commands above for v3 refreshes. The legacy scheduled workflow has not been upgraded in this branch; cloud backfill results are imported independently of GitHub Actions.

## What the data means

- `fieldEvidence`: field-specific source URL, observation timestamp, supporting text, and method.
- `verification`: partial source checks, latest attempt, and fields with evidence. `source_checked` is not a guarantee of current employment or a completely verified profile.
- `lastVerified`: retained historical field from the legacy schema; the UI uses actual evidence timestamps for new claims.
- `appointmentStatus`, `directoryListings`, `departmentAffiliations`: directory-reported roles and affiliations; undated catalog entries do not prove a current appointment.
- `labAffiliations`: multiple sourced links. A faculty link to a lab is not by itself proof that the person is its PI.
- `teaching.courses`: explicit instructor assignments, course code/title, advertised term, source, and identity match. Scheduled courses may change. Historical schedules are not proof the teaching occurred. Surname-only matches stay under `teaching.candidates`.
- `ratings.rateMyPI`: **PI Review** (`pi-review.com`), the mentoring-review source used here. `ratings.rateMyProfessors`: the separate teaching-review platform. Scores are not combined; missing/ambiguous/inaccessible/no-review cases never become zero scores. Sample sizes and collection dates are shown.
- `researchAreas`: explicit research labels from official directory entries, supplemented by controlled phrases in sourced research paragraphs or official profile keywords. Empty lists mean no supported tags have been captured.
- `researchKeywords`: the keywords or research topics a person lists on their official UCSD Profiles or Scripps profile. They are searchable; only controlled-vocabulary matches become `researchAreas`.
- REAL includes co-curricular listings as well as research/internship opportunities; a public listing does not establish an active opening.

See [the architecture](docs/ARCHITECTURE.md) and [the JSON schema](data/schema.json).

## Legacy correction and preservation

The old collector matched navigation links and whole-page keywords. This assigned support mailboxes, department pages, and unrelated research labels to many professors. The v3 migration removes those unsupported values and saves the originals in `data/quality/legacy-remediation.json`. Personal research sites incorrectly counted as labs, and same-person catalog duplicates, are preserved in `data/quality/quarantined-records.json`.

The old UCSD index and old collectors remain for historical discovery. They refuse to overwrite a v3 served dataset. To investigate them, write to a separate candidate file and review the evidence. Do not run the old build/migration sequence over the new dataset.

## Files

- `index.html`, `assets/app.js`, `assets/styles.css`: static search and details UI.
- `assets/taxonomy.js`: browse groupings (schools/divisions with their departments, broad research fields with detailed areas), query synonyms, and Chinese translations. Field membership is a browse aid inferred in the browser from a record's department and its sourced research text; it is not stored in the dataset or presented as a sourced claim.
- `data/research-atlas.json`: served professor and lab records.
- `data/ucsd/*-evidence.json`: independent captures and unresolved identity candidates.
- `data/ucsd/lab-identity-review.json`: sourced decisions about duplicate lab websites, incorrect directory destinations, and research-group membership.
- `data/ucsd/lab-expansion-review.json`: manually reviewed additions and missing-field enrichments, consumed by the offline builder; duplicate URLs and unsourced PI claims are rejected.
- `data/ucsd/lab-expansion-candidates.json`: dated discovery decisions, exclusions, and unresolved candidates for the lab expansion; candidate investigator names are leads unless supported by reviewed leadership evidence.
- `docs/LAB_EXPANSION_REVIEW.md`: scope, net changes, limitations, and validation of the October 2026 lab review.
- `data/ucsd/source-checks.json`: URL checks and undated catalog listings.
- `data/ucsd/real-portal-resources.json`: complete public REAL snapshot and page receipts.
- `data/quality/`: coverage report and preserved corrections.
- `scripts/refresh_*.py`, `scripts/rebuild_verified_atlas.py`: refresh and merge pipeline.
- `tests/`: extraction, identity, pagination-content, and provenance regressions.
