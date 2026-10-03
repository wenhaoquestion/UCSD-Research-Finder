# UCSD Profiles cloud handoff

The user requested **ChatGPT's cloud computer**, not GitHub Actions. This branch
is a source/data handoff. No cloud workflow is needed or authorized by this guide.

The October 2, 2026 (America/Los_Angeles) snapshot contains 4,392 professor records
and 616 labs. `data/ucsd/lab-evidence.json` has 1,572 profile observations marked
`deferred_crawl_delay`. They are resumable independently of the original local
HTML cache. The public UCSD Profiles host requires a 10-second interval; allow
roughly 4.5–5 hours for the whole queue, potentially longer for retries.

## Check the actual cloud runtime first

Confirm that a cloud terminal can reach `https://profiles.ucsd.edu/robots.txt`,
run Python, and preserve files between calls. Establish its real execution and
session limits before choosing batch sizes. If cloud terminal networking or
long-lived execution is unavailable, report that limitation explicitly; do not
claim a background job is running. Do not substitute local execution or GitHub
Actions without the user's instruction.

```bash
python3 -m unittest discover -s tests -q
python3 scripts/run_profile_backfill.py --dry-run
python3 scripts/run_profile_backfill.py --max-profiles 1 --max-seconds 120
python3 scripts/rebuild_verified_atlas.py
python3 scripts/validate_data.py
```

After a successful real observation, continue sequentially in batches fitting
the runtime. For example, a ten-minute execution window can use:

```bash
python3 scripts/run_profile_backfill.py --max-profiles 40 --max-seconds 480
python3 scripts/rebuild_verified_atlas.py
python3 scripts/validate_data.py
```

For a confirmed long-running terminal, batches of 500 profiles with the default
5,700-second budget are supported. Repeat while `--dry-run` reports remaining
eligible records. Never run parallel workers against this host.

## State and results

- `data/ucsd/lab-evidence.json` is the full merged checkpoint. It is saved after
  every completed profile; it retains other departments, directories, exported
  faculty, and personal-site observations.
- `data/ucsd/profile-backfill-checkpoint.json` records attempted IDs and resume
  instructions. `profile-backfill-progress.json` contains compact progress.
- Exit **75** means HTTP 429 or an unavailable/disallowed robots policy stopped
  the host. Preserve state and stop subsequent batches; do not bypass or restart
  immediately. Exit **130** means interruption with completed observations saved.
- DNS/HTTP/identity failures remain failures, never fabricated successful data.
- Rebuild and validate after batches. The complete evidence artifact must be
  retained even if a newly encountered parser case prevents final validation.

Return a downloadable archive containing the complete evidence JSON,
checkpoint/progress files, updated `data/research-atlas.json`, `data/quality/`,
`docs/DATA_QUALITY_REPORT.md`, and collection logs. Show processed, verified,
failed/ambiguous, and remaining counts separately. Do not publish to `main` or
deploy the website. Preserve the cloud checkpoint before ending the task.
