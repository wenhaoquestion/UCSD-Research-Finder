# UCSD Profiles cloud handoff

## Completed capture and local import — October 3, 2026

The original 1,572 deferred profiles were processed in ChatGPT's cloud runtime:
1,373 identity matches, 56 identity cases needing review, and 143 failed fetches
(130 HTTP 404, two HTTP 504, and 11 responses above the size limit). No profiles
remain deferred in this capture. Queue completion does not mean every profile
was verified.

The complete evidence was imported locally after verifying the transfer archive
and checking all professor IDs, prior lab IDs, non-target evidence, directories,
personal-site observations, teaching assignments, and both rating platforms.
An offline local rebuild exactly matched the cloud atlas before editorial review.
Four news articles misclassified as labs were then moved to the quarantine
archive, with incorrect professor relationships cleared. The reviewed dataset
contains **4,392 professor records and 686 labs/research groups**, compared with
616 labs before the cloud backfill. The raw capture is retained unchanged.

- `data/quality/cloud-backfill/result-summary.json`: original cloud-run results.
- `data/quality/cloud-backfill/profile-outcomes.json`: all 1,572 profile outcomes.
- `data/quality/cloud-backfill/failed-and-review.json`: 199 unresolved outcomes.
- `data/quality/cloud-backfill/import-receipt.json`: archive and file hashes,
  preservation checks, and the final lab review decisions.
- `data/ucsd/profile-backfill-checkpoint.json` and
  `profile-backfill-progress.json`: resumable cloud checkpoints.

The original cloud archive SHA256 is
`1851f9e80379b282d312b3f2aceb38a8caf04f952fb74d7af5ff96efc03820ae`.
The compact transfer archive SHA256 is
`f8590b2b6b40a29e39d5c38764210c5d2933bc6a4fa1b6b72de12501b723ddca`.

## Original execution instructions

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
