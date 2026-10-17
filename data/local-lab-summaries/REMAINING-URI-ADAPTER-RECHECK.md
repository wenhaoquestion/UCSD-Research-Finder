# Remaining original URI adapter — stable-version recheck

Reviewed 2026-10-16T04:52:57+00:00. **PASS: both prior defects are resolved, and the existing34-candidate scope can proceed through its normal pinned-source/receipt startup guards.** No new actionable finding remains in this bounded review. No real network request, code/receipt/record/packet change or scientific-body reread was made. Only this new report pair was created; the original [QA defect report](/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/REMAINING-URI-ADAPTER-QA.md) and JSON remain byte-for-byte unchanged.

## Exact snapshot and actual tests

- [Adapter](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summary_gaps.py) SHA256 `34ebac1ceaf1ba5eae5773b59099b34d993d40aa0135b9698c360a766f3ff02c`.
- [30 original-URI tests](/tmp/ucsd-lab-summaries-20261016/tests/test_local_lab_original_uri_scope.py) SHA256 `a74ff8b91cb26be2d5cbe69b2927369d0aa58537efc27299908e6635d18b1856`.
- Pinned collector remains `6a5d3c3b8739ad4ae2b9abeaaaa0c9e545bd677f680779691c44e94fa8e0aa82`.
- Independently ran `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_local_lab*.py'`: **161/161 PASS**,1.516s. All use offline fixtures/fake transport. Additionally replayed both original counterexamples and three isolated hard-stop footprints.

## Original findings resolved

**URIQA-1:** [admission/refusal collection](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summary_gaps.py:130) now reads explicit refusal state from actual capture top-level histories and matches it to the same original/related root or same-origin robots. The exact original fixture with an earlier related HTTPS `authentication_required`/403 record now returns liveCandidateCount=0 (previously1). Tests also keep an unrelated-path refusal from blocking the selected route and retain a separately captured same-origin robots refusal.

**URIQA-2:** [durable attempt-key extraction](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summary_gaps.py:81) consumes the start journal and wire footprints, including robots events owned by `originalObservationUrl`. [execute start journal](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summary_gaps.py:461) atomically records intent before any robots/page transport. The exact original RuntimeError fixture now saves1 wire event plus1 accurate exception item and returns0 next-plan candidates. The cap resets to2,000,000 and originalObservationUrl resets toNone.

The isolated orphan-original-page, orphan-robots-with-owner, and journal-only-with-zero-wire cases all close admission while hydrated listed-page proof stays false. A hard interrupt can therefore close the once-only lifecycle without pretending the page was requested.

## Exception and page-proof boundaries

[transport outcome recording](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summary_gaps.py:392) distinguishes a returned HTTP/error tuple from transport-started/response-indeterminate. Ordinary exceptions save `fetch_exception`, exception type/error and incomplete lifecycle state, then are re-raised after the receipt is saved. `KeyboardInterrupt` is not swallowed; the durable journal still closes admission. Both candidate cap and ownership context reset in finally.

[page proof gate](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summary_gaps.py:488) requires a returned original-page transport HTTP code, including returned curl code0. A start/orphan alone gets `actualPageRequestMade=false` and `liveCheckedAt=null`; an incomplete exception does not invent HTTP status, final URL, redirect chain or SHA. A returned original redirect may still prove the initial attempt if a later robots/redirect stage fails, without inventing a final destination. The suite actually exercises RuntimeError/TimeoutExpired at before-wire, robots and page stages; KeyboardInterrupt at all three; returned code0; later-stage exception; and zero-wire RetryAfterDeferred.

Normal TLS, root/target robots, the shared-v2 gate,300,000-byte robots and the default2,000,000-byte page cap remain intact. The reviewed8M proof file/hash/per-item binding is still required for the two allowlisted size exceptions. No identity/scientific acceptance or mismatch gate is relaxed.

## Actual34-candidate metadata check

Called only the read-only admission helper, without running plan or writing its receipt: all34 reviewed entries remain admitted, **32×2,000,000 and2×8,000,000 bytes**. Cached original-HTTP robots refusal count is0; no selected entry already has a matching journal/wire footprint. This matches saved plan2026-10-16T04:51:17+00:00, live count34. Gap-results SHA256 remains `1daeca1e92e076a394d7e10b8e3a88c3c77c84b2d38ed3af1d22f10b6e9387f0`, unchanged by this review. The route-review SHA256 is `022c3ccda49ad3db58330988ee8616342b43a3ab2b1f45e12482f12f0c00981f`.

The original defect snapshot and its test outcomes remain preserved chronologically in the earlier QA report; this report covers only stable SHA `34ebac1ceaf1ba5eae5773b59099b34d993d40aa0135b9698c360a766f3ff02c` and introduces no new route or live authorization.
