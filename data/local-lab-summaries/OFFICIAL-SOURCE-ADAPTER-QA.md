# Official-source adapter QA

Reviewed 2026-10-16T05:51:55+00:00. **PASS: no actionable findings.13focused offline tests passed (0.108s);0network requests.** No actualplan execution or existing code/receipt/raw/packet/collector/shared-state writes. Tests used cleaned temporary fixtures.

Compared current adapter SHA256 `dfb07eda989ff223884a112af882586b9e506c6047984bda0cbde93f54e5c8fe` with `641fd9abbcdc2cc3382847acb241695384a0faec` (adapter SHA256 `2e691409cab7ec3dff70b9876bc98b9260c2c4af19d9532b65cb4944433a4aea`). AST proves all15existing non-plan definitions unchanged, including `load_fetcher`, `coordination_snapshot/ready`, `instrumented_fetcher`, `retry_pauses` and `execute`. New definition is `reviewed_official_source_gaps`; only existing `plan` changed. Its prior preload/map admission additions are separately reviewed.

## Binding and execution boundaries

- `scripts/local_lab_summary_gaps.py:172–205`: actual baseline bytes must match fixed SHA; curated lab/field/purpose/reviewtime validated; URL must literally equal original full proof URL. Exact original observedAt and SHA of the complete proof bind the historical evidence, including extra fields.
- `:193–205`: HTTPS UCSD host only, userinfo/nonstandardport/fragment/auth-path rejected; exacttarget or robots prior403/auth/challenge/history and cached robot rules remain blocking. Unrelated-path refusal does not fabricate target refusal.
- `:207–213`: constructs historical-reference-only metadata with2MB cap; injected8MB/observationOnly/sourceId are dropped. No source retiming, new observation/page-proof, canonical or identity acceptance.
- `:269,:361–368`: existing plan dedupe, successful-cache reuse, pending wait and robots filtering still apply. Network functions/shared-v2/robots/redirect waits/TLS/caps are unchanged.

## Actual one-URL proof

Saved plan at2026-10-16T05:51:12+00:00 has exactly1live candidate: [https://astro.ucsd.edu/research/labs/index.html](https://astro.ucsd.edu/research/labs/index.html) for `ucsd-astronomy-and-astrophysics-lab-space-weather-laboratory`. Pure helper (read-only) independently returned the same one entry.

Baseline bytes SHA256 `ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e`; complete original `labName` proof SHA256 `74e71f60f921a0af88fc88e317f93a36dd967f4d122b021817dc673f57fb7d9d`; original observation `2026-10-07T22:55:23+00:00`. This remains a historical reference, not a new source observation. Modern page/entity/science still requires actual response review.

## Validation

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_local_lab_official_source_gaps.py -v` —13/13PASS. Coverage includes baseline tampering, full-proof mutation, strictliteral URL/time binding, official/auth boundaries, missing/current raw eligibility, prior refusals/history, cached robots, success/pending reuse, cap/sourceId injection, raw/packet/queue immutability and no hydrate identity promotion.

Tests SHA256 `b79b982371862850ddc36f9a5f9205d562aacc1257dde10d2337724a4c552f5b`; curated review JSON SHA256 `b236b68b7b803cae4617dca7a692b8def2f40a8dfb0092539a86dae939cbcb25`. Full hashes, definition names and exactsource-line references are in companionJSON. Parent runs fullsuite and future execution guards separately.
