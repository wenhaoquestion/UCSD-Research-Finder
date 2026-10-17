# Remaining original URI adapter independent QA

Reviewed 2026-10-16T04:46:31+00:00. **Two reproducible admission/one-shot defects require repair before live execution.** Both were reported immediately to the parent and adapter owner. The existing60 relevant tests pass; they do not cover the two demonstrated storage/exception cases. No live request or code/receipt/record edit was made; only this QA report pair was created. Offline fixtures were isolated and cleaned.

## Reviewed snapshot and test results

- [Adapter](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summary_gaps.py) SHA256 `19a92ccd594e4632d38e302bae8dbdf5b12b1ffe3e058ad1376140f3568685f4`.
- [Original URI tests](/tmp/ucsd-lab-summaries-20261016/tests/test_local_lab_original_uri_scope.py) SHA256 `c98c65963acc92f201a307c71d41fe7ca8c52cfbc917bd33b0a6a2fed95a34ae`.
- Exact pinned collector `6a5d3c3b8739ad4ae2b9abeaaaa0c9e545bd677f680779691c44e94fa8e0aa82`.
- Actual offline test runs: original-URI21 PASS (0.277s); shared-v2 cooldown39 PASS (0.768s). Two additional fake-transport counterexamples reproduced the findings below. No real transport was called.

The saved plan at2026-10-16T04:43:47+00:00 contains62 total entries and34 live candidates:32×2,000,000 and2×8,000,000 bytes. Targeted metadata inspection found **no currently triggered top-level refusal or orphan-page-wire case among those34**. These are executable counterexamples, not claims that the current batch already encountered either failure.

## URIQA-1 · P1 · Real queue top-level refusal history is omitted

[reviewed_original_uri_observations](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summary_gaps.py:116) consumes top-level capture `attemptHistory` only while collecting already-observed original URIs. Its refusal gate at133 checks `explicit_access_boundary(binding)`, which recurses through the bound fetch object's own nested history/robots but never checks a related HTTPS capture's real top-level historical refusal. The existing earlier-denial test places history inside packet.latestDestinationFetch, rather than the actual queue shape.

Exact offline fixture: use `OriginalURIObservationTests.setUp()`, set `t.capture['attemptHistory']=[{'sourceUrl':t.meta['sourceUrl'],'status':'authentication_required','httpStatus':403,'observedAt':'2026-10-16T00:30:00+00:00'}]`, then call `t.plan()`. Actual liveCandidateCount=1; expected0 under the intended prior-refusal policy. The related capture remains the standard fixture's HTTPS root; no original HTTP has been attempted.

Repair: retain explicit refusals from relevant captures' top-level histories, not merely fetch-nested histories. Scope the check to the same original/related root and robots relationship. Add the exact queue-shape regression.

## URIQA-2 · P1 · An orphan wire event allows the once-only request again

[TrackedFetcher._transport](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summary_gaps.py:376) durably records a wire event before the real transport and closes it in finally. [execute](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summary_gaps.py:432) catches RetryAfterDeferred only; a generic transport exception escapes before the completed item is stored (445). `plan` builds captures from queue and ledger.items (158); it ignores ledger.wireEvents-only footprints.

Exact offline fixture: call `size_proof()` and obtain the8M candidate. Use the same mocked coordination/load_fetcher setup as the existing per-fetch cap test. FakePublicFetcher.fetch calls self._wire(originalURL), its _wire delegates to self._transport, and _transport raises RuntimeError. `execute(1)` propagates the exception. The isolated ledger has1 wire event and0 completed items; the next real fixture `plan()` again has liveCandidateCount=1, expected0. The8M cap **does correctly reset to2,000,000 in finally**, including this failure path.

Repair: save an accurate exception receipt when possible and close once-only admission from a durable attempt/wire footprint even after a hard interrupt. A transport-started/response-incomplete receipt must not invent a final URI, successful response, or completed actual-page-request proof. Add generic-exception and wire-only hard-interrupt regressions.

## Checks that passed in the reviewed code

Literal baseline URI/stable-ID/hash checks, strict full-fetch metadata binding including JSON types, mismatch exclusion,8M proof-file hash and per-item matching, and integer cap limits are present. The cap wrapper delegates to the pinned shared-v2 `_wire`; explicit300,000-byte robots calls are preserved and normal TLS remains in the pinned transport. Identity/scientific acceptance is unchanged. The normal success path scopes8M to its fetch and restores2M; the added exception counterexample verifies that restoration too.

Parent and adapter owner have the reproduction details. This report preserves the original snapshot and open defects; any repaired-version QA will be appended with new hashes and actual test results.
