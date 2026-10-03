# Research Atlas

A static UC San Diego research finder with faculty profiles, labs, contacts, teaching schedules, PI Review mentoring ratings, Rate My Professors teaching ratings, and public REAL Portal opportunities.

The served dataset uses **schema v3**. Each newly asserted field includes its source, supporting text, extraction method, and actual observation time. A successful page request does not verify every fact on the page. Current counts and unresolved gaps are generated in [the data quality report](docs/DATA_QUALITY_REPORT.md); machine-readable coverage by department is in `data/quality/refresh-report.json`.

## Run locally

Python 3.11+ is required for the collection scripts. The website itself needs only a static server.

```bash
python3 scripts/validate_data.py
python3 -m http.server 8000
```

Open http://localhost:8000. Search accepts professor names, research text, and course codes such as `CSE151A`. Filters include courses, both rating platforms, and records with field evidence. Details show dates, sample sizes, all confirmed lab associations, and original sources. Former and emeritus faculty retain their source-reported category.

## Refresh public data

Collectors produce evidence files; the offline builder merges them into the website dataset. Failed requests remain distinguishable from missing matches. Existing values do not acquire a new verification date merely because the builder ran.

```bash
# Official lab directories and professor profiles; personal sites are one additional hop.
python3 scripts/refresh_labs.py --personal-sites --personal-site-limit 0
python3 scripts/refresh_faculty_directories.py
python3 scripts/refresh_source_checks.py

# Add newly discovered faculty before matching courses and ratings.
python3 scripts/rebuild_verified_atlas.py

# Official departmental schedules. PDF sources require pdftotext and pdfplumber.
python3 scripts/refresh_teaching.py --refresh

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

### Rate limits, caches, and continuation

UCSD Profiles publishes a **10-second crawl delay**. The default lab refresh defers uncached slow-host profiles rather than ignoring that rule. Complete them in resumable batches:

```bash
python3 scripts/refresh_labs.py --include-slow-profiles --slow-profile-limit 60 --personal-sites --personal-site-limit 0
```

Fresh cached pages do not consume the slow-host budget; later runs advance to remaining pages. Lab and rating caches have a default 30-day maximum age. `--refresh` forces new requests; cache reuse preserves the original `observedAt`. Collector cache paths can be placed under `.cache/atlas` for durable local or CI runs. Never clear the cache between continuation batches.

The existing Monday update workflow now runs the evidence pipeline, tests, validation, and a guard against unexplained record loss. It retains caches across runs and budgets slow-host requests. Workflow changes take effect only after the repository changes are pushed.

## What the data means

- `fieldEvidence`: field-specific source URL, observation timestamp, supporting text, and method.
- `verification`: partial source checks, latest attempt, and fields with evidence. `source_checked` is not a guarantee of current employment or a completely verified profile.
- `lastVerified`: retained historical field from the legacy schema; the UI uses actual evidence timestamps for new claims.
- `appointmentStatus`, `directoryListings`, `departmentAffiliations`: directory-reported roles and affiliations; undated catalog entries do not prove a current appointment.
- `labAffiliations`: multiple sourced links. A faculty link to a lab is not by itself proof that the person is its PI.
- `teaching.courses`: explicit instructor assignments, course code/title, advertised term, source, and identity match. Scheduled courses may change. Historical schedules are not proof the teaching occurred. Surname-only matches stay under `teaching.candidates`.
- `ratings.rateMyPI`: **PI Review** (`pi-review.com`), the mentoring-review source used here. `ratings.rateMyProfessors`: the separate teaching-review platform. Scores are not combined; missing/ambiguous/inaccessible/no-review cases never become zero scores. Sample sizes and collection dates are shown.
- `researchAreas`: explicit research labels from official directory entries, supplemented by controlled phrases in sourced research paragraphs. Empty lists mean no supported tags have been captured.
- REAL includes co-curricular listings as well as research/internship opportunities; a public listing does not establish an active opening.

See [the architecture](docs/ARCHITECTURE.md) and [the JSON schema](data/schema.json).

## Legacy correction and preservation

The old collector matched navigation links and whole-page keywords. This assigned support mailboxes, department pages, and unrelated research labels to many professors. The v3 migration removes those unsupported values and saves the originals in `data/quality/legacy-remediation.json`. Personal research sites incorrectly counted as labs, and same-person catalog duplicates, are preserved in `data/quality/quarantined-records.json`.

The old UCSD index and old collectors remain for historical discovery. They refuse to overwrite a v3 served dataset. To investigate them, write to a separate candidate file and review the evidence. Do not run the old build/migration sequence over the new dataset.

## Files

- `index.html`, `assets/app.js`, `assets/styles.css`: static search and details UI.
- `data/research-atlas.json`: served professor and lab records.
- `data/ucsd/*-evidence.json`: independent captures and unresolved identity candidates.
- `data/ucsd/lab-identity-review.json`: sourced decisions about duplicate lab websites, incorrect directory destinations, and research-group membership.
- `data/ucsd/source-checks.json`: URL checks and undated catalog listings.
- `data/ucsd/real-portal-resources.json`: complete public REAL snapshot and page receipts.
- `data/quality/`: coverage report and preserved corrections.
- `scripts/refresh_*.py`, `scripts/rebuild_verified_atlas.py`: refresh and merge pipeline.
- `tests/`: extraction, identity, pagination-content, and provenance regressions.
