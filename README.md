# Research Atlas

Research Atlas is a static, GitHub Pages-ready search platform for students looking for professors, research labs, emails, research areas, lab links, Google Scholar links, and explicit recruiting information.

The project was rebuilt from a UCSD-specific research finder into a cleaner static app with a canonical `professors` and `labs` data schema. The old UCSD crawler and cache remain in `data/ucsd/` and `scripts/build_ucsd_index.py` as legacy source material.

The current bundled UCSD dataset contains 4,304 professor records and 435 stricter lab records. Broad research-topic, academic-support, facility/resource, publication, project, FAQ, and directory pages are kept as sources when useful, but they are not shown as labs.

## What Changed

- New polished frontend in `index.html`, `assets/styles.css`, and `assets/app.js`.
- New canonical dataset at `data/research-atlas.json`.
- New JSON schema at `data/schema.json`.
- New source configuration at `data/sources.json`.
- New generic public-page collector at `scripts/collect_research_data.py`.
- New UCSD legacy migration script at `scripts/migrate_ucsd_index.py`.
- New strict validator at `scripts/validate_data.py`.
- GitHub Pages deployment workflow in `.github/workflows/deploy-pages.yml`.

## Local Run

Use a local server because browsers block `fetch()` for JSON files opened directly from disk.

```bash
python3 scripts/validate_data.py
python3 -m http.server 8000
```

Open `http://localhost:8000`.

## Data Collection

Edit `data/sources.json` with the target school, department, faculty directory pages, lab pages, and research group pages. Then run:

```bash
python3 scripts/collect_research_data.py --config data/sources.json --out data/research-atlas.json
python3 scripts/validate_data.py
```

Useful options:

```bash
python3 scripts/collect_research_data.py --max-pages 120 --max-depth 1
python3 scripts/collect_research_data.py --personal-limit 50
python3 scripts/collect_research_data.py --no-robots
python3 scripts/collect_research_data.py --write-empty
python3 scripts/validate_data.py /path/to/another-atlas.json
```

The collector is intentionally conservative. It only reads public pages, follows shallow faculty/lab/research links, optionally enriches the first page of discovered personal websites, and keeps `recruitingStatus` as `Unknown` unless it finds explicit public language such as “we are recruiting,” “open positions,” or “not accepting students.”

## Rebuild The Full UCSD Dataset

The new frontend reads `data/research-atlas.json`, while the old UCSD crawler writes `data/ucsd/research-index.json`. To preserve the full UCSD coverage, rebuild and migrate:

```bash
python3 scripts/build_ucsd_index.py
python3 scripts/migrate_ucsd_index.py --input data/ucsd/research-index.json --out data/research-atlas.json
python3 scripts/validate_data.py
python3 scripts/audit_research_atlas.py
```

## Data Schema

The app reads:

- `professors[]`: name, institution, department, faculty profile, personal site, email, research areas, summary, Google Scholar, lab affiliation, recruiting status, evidence, sources.
- `labs[]`: lab name, institution, department, lab website if found, PI, research areas, description, contact email, recruiting status, evidence, sources.

Research topic pages, such as Biology research-topic index pages, should be used to discover professors and their lab links. They should not be published as lab records unless the target page is an actual lab/laboratory/research-group page.

Rules enforced by `scripts/validate_data.py`:

- Every record must include at least one source URL.
- Missing fields must be `Not found` or `Unknown`.
- Recruiting claims require evidence text and an evidence URL.
- Evidence URLs must also appear in `sourceUrls`.

## Deploy To GitHub Pages

Option 1: Pages from branch

1. Push this repository to GitHub.
2. Go to Settings -> Pages.
3. Set the source to the main branch and root folder.
4. Save. GitHub Pages will serve `index.html`.

Option 2: GitHub Actions

1. Push to `main`.
2. Enable Pages with “GitHub Actions” as the source.
3. The `Deploy static site to GitHub Pages` workflow uploads the repository as a static Pages artifact.

## Project Structure

```text
.
├── index.html
├── assets/
│   ├── app.js
│   └── styles.css
├── data/
│   ├── research-atlas.json
│   ├── schema.json
│   ├── sources.json
│   └── ucsd/
├── scripts/
│   ├── collect_research_data.py
│   ├── migrate_ucsd_index.py
│   ├── audit_research_atlas.py
│   ├── validate_data.py
│   └── build_ucsd_index.py
├── docs/
│   └── ARCHITECTURE.md
└── .github/workflows/
    ├── deploy-pages.yml
    └── update-data.yml
```

## Future Improvements

- Add school-specific adapters for departments with unusual markup.
- Add a manual review UI for confirming auto-collected summaries before publishing.
- Store field-level provenance so each email, summary, and research area points to the exact supporting source.
- Add export to CSV for students building outreach lists.
- Add optional search-provider integration for discovering seed pages before crawling.
