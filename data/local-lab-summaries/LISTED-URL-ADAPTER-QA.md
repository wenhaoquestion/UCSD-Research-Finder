# Listed URL adapter and planner QA

**PASS** — independent review at `2026-10-16T04:17:25+00:00`. No actionable issues found. **53/53 offline tests passed**; actual network requests: **0**. The parent-reported 118-test suite was not independently rerun.

The finite scope was the new code in `scripts/local_lab_summary_gaps.py` and the five new tests in the two specified test files. Scientific sources and the 48 per-record metadata decisions were outside this review.

- **exact source pins and isolated module** (`scripts/local_lab_summary_gaps.py:195`): All required pinned source bytes are verified into a complete list before the compile loop. Only the loaded summary-side module.safe_url is replaced after compilation; original collector files and shared coordinator code are unchanged.
- **public-origin validation plus literal request URI** (`scripts/local_lab_summary_gaps.py:224`): The retained pinned safe_url validator runs first. Valid requests preserve original scheme and www host, quote the raw path without introducing canonical aliases, preserve query, and remove fragment. file/local/IP/credentials/nonordinary ports remain rejected by the pinned validator.
- **robots and page redirects under shared lock** (`tests/test_local_lab_shared_adapter.py:29`): Mocked transport asserts held == [url] for each actual HTTP robots request, HTTPS robots redirect target, HTTP page, and HTTPS page redirect target. Source request remains HTTP; only observed 301 contributes the redirect chain and HTTPS final URL.
- **stable per-ID reviewed admission binding** (`scripts/local_lab_summary_gaps.py:89`): Admission requires exact packet.listedWebsite == reviewed url and a matching relatedCapture tuple for actual requested URI, final source URL, original observedAt and body SHA. Host/path/query are constrained; hydrate must succeed, page identity must be confirmed, transport must be ok, accepted_lab_group must hold, and listed URL must not already have been directly checked. Hydrate retains the unresolved mismatch exclusion.
- **actual request availability and denial boundary** (`scripts/local_lab_summary_gaps.py:68`): The literal-listed-gap namespace deduplicates by request_key, separately from content-folded discoveries. Availability uses meta.sourceUrl (through checked_url/request_key) rather than a capture dictionary URL or final-URL content key, so an HTTPS related capture cannot close an HTTP original request gap. An actual original-URI robots denial stays access_boundary_do_not_bypass with no live candidate.
- **new regression coverage** (`tests/test_local_lab_summaries.py:86`): The five added tests cover original HTTP/www preservation and public rejection, actual HTTP page/robots redirects with locks, supported research not closing an original-address gap, stale capture/mismatch rejection, and original-address access-denial no-retry behavior.

Independent test runs:

| Test file | Run | Passed | Failures/errors |
| --- | ---: | ---: | ---: |
| `test_local_lab_shared_adapter.py` | 11 | 11 | 0 |
| `test_local_lab_summaries.py` | 42 | 42 | 0 |

Both commands used `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p <file> -v`. The adapter tests replace the transport and gate; planner tests use temporary isolated files. Production `plan()` was not invoked, because it writes `gap-plan.json`. No code, raw record, packet, collector cache, or shared coordinator was edited. Only these two QA reports persist; temporary test fixtures were cleaned up.

Reviewed file hashes:

- `scripts/local_lab_summary_gaps.py`: `5c2121c2ab90481e8836e0230dafaf0b194453aa554a4e7f7ceaf62aa2948dfa`
- `tests/test_local_lab_shared_adapter.py`: `d95ae9170ff1b27271d67f3d19bf4f4c26b4d5fbaf89dfaa3045f9e26ac354ea`
- `tests/test_local_lab_summaries.py`: `15bf3e999c835d191c0bcaf60e8b33ed931ea05f87dadbef5dbfa57d4fafd514`

The current seven dependency pins are recorded in the JSON report. The real 48-association admission list remains the other agent’s review responsibility; this PASS does not claim per-record review of that list.
