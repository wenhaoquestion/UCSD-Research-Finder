# Original URI response-cap review — Stauber and Ferguson

Reviewed 2026-10-16T04:40:21+00:00. This read-only review sent **zero requests**, changed no code/runtime cap, and read no scientific page bodies. Saygin's same-host DNS failure remains a separate actual network obstacle.

## Finding and recommendation

`2,000,000` bytes is the pinned implementation's default page-response resource cap. The reviewed persisted user objective contains no numerical page-size cap. The previous delegation explicitly prohibited increasing 2MB for that run; that instruction was followed. This follow-up is a reassessment, not a silent runtime exception or execution authorization. The absence-of-user-cap conclusion is limited to the persisted goal/setup and instructions available in this review.

The two recorded failures are **HTTP200/text-html plus `curl: (63) Maximum file size exceeded`**, with robots404 and no robots error. That is evidence of a local size/resource stop, rather than recorded authentication, robots denial, or challenge refusal. No complete body was saved, so challenge text inside an unobserved body cannot be ruled out.

A parent-adopted exception limited to these two exact original baseline HTTP addresses, with **one fixed8,000,000-byte hard cap per page response**, is a reasonable bounded resource retry within the reviewed collection objective. A fixed4–8MB cap could help; prefer a single8MB attempt over repeated4MB then8MB escalation. Neither fit nor success is known: actual Content-Length and complete response headers were not persisted. Preserve HTTP-origin robots first, normal TLS on every actual HTTPS hop, target robots, shared v2 host lock/cooldowns, timeouts/redirect limits, and the local404/410 challenge compensation. Keep robots at300,000 bytes. Do not log in, bypass challenges/robots/TLS, stitch body chunks, retry automatically at still larger caps, or change upstream collector/shared-state code. If still too large, retain the new observed size blocker. Transport success still requires separate lab identity/research reading.

This refines the preceding `REMAINING-URI-SCOPE-REVIEW-024-034` recommendation: deferral was appropriate under its fixed2MB run rule; it should not be described as an immutable user boundary or a server access prohibition. The original HTTP targets remain unrequested as of the reviewed metadata.

## Exact source call chain

The exact source is [collector6a5d snapshot](/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/network-adapter-sources/collect_ucsd_coverage-6a5d3c3b8739ad4ae2b9abeaaaa0c9e545bd677f680779691c44e94fa8e0aa82.py), SHA256 `6a5d3c3b8739ad4ae2b9abeaaaa0c9e545bd677f680779691c44e94fa8e0aa82`, matching the recorded active collector pin.

- [PublicFetcher._wire](/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/network-adapter-sources/collect_ucsd_coverage-6a5d3c3b8739ad4ae2b9abeaaaa0c9e545bd677f680779691c44e94fa8e0aa82.py:257) (257–273) defaults `max_bytes=2_000_000`, enters the host/shared gate, and forwards that value to `_transport`.
- [PublicFetcher.fetch page call](/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/network-adapter-sources/collect_ucsd_coverage-6a5d3c3b8739ad4ae2b9abeaaaa0c9e545bd677f680779691c44e94fa8e0aa82.py:380) calls `_wire(current, delay)` without `max_bytes`; therefore the page/redirect response uses that default.
- [PublicFetcher._rules robots call](/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/network-adapter-sources/collect_ucsd_coverage-6a5d3c3b8739ad4ae2b9abeaaaa0c9e545bd677f680779691c44e94fa8e0aa82.py:317) explicitly passes `max_bytes=300_000`; this separate bound should remain unchanged.
- [PublicFetcher._transport](/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/network-adapter-sources/collect_ucsd_coverage-6a5d3c3b8739ad4ae2b9abeaaaa0c9e545bd677f680779691c44e94fa8e0aa82.py:275) (275–298) passes the bound to curl `--max-filesize` (281), also rejects `len(content)>max_bytes` (286–288), parses headers only in a temporary directory, and returns the header dictionary. No explicit insecure/TLS bypass flag is used.
- [PublicFetcher.fetch classification/persistence](/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/network-adapter-sources/collect_ucsd_coverage-6a5d3c3b8739ad4ae2b9abeaaaa0c9e545bd677f680779691c44e94fa8e0aa82.py:391) stores HTTP status/content type/error but not Content-Length/full headers. Only `status=ok` generates a bodySHA and saves `.html` (400–402,419–425). A curl63 error is classified before body challenge matching (392–399).
- [Task TrackedFetcher._transport](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summary_gaps.py:266) forwards its `max_bytes` argument unchanged to the pinned transport. Existing code therefore remains2MB; any scoped exception requires an explicit task-adapter implementation and offline validation, while keeping these access checks.

## Actual metadata and usable cache evidence

### 708 · ucsd-chemistry-biochemistry-lab-stauber-lab

Baseline original: [http://stauberlab.ucsd.edu/](http://stauberlab.ucsd.edu/), stableID unchanged. Actual captured attempt: `https://stauberlab.ucsd.edu/`; last observedAt `2026-10-16T01:10:16+00:00`; queue attempts `3`. Recorded attempt times: `2026-10-16T01:07:15+00:00, 2026-10-16T01:08:15+00:00, 2026-10-16T01:10:16+00:00`. Each listed queue attempt has the same HTTP200/curl63 outcome.

Robots `https://stauberlab.ucsd.edu/robots.txt` was observed `2026-10-16T01:07:14+00:00` with404, `not_found`, empty error. This HTTPS robots observation is not permission for the unrequested HTTP origin.

[Exact response metadata](/tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/144251a1a955ad7bd0ec81b85acbc6030a11eb41b98c676a0c3b4f1bfc9276c3.json) SHA256 `a82511db6e0cc3a7d0b8eb5c8634a870448f8f312d116388583bac465694a65c` equals the queue and packet fetch. Content-Length/full response headers are **unavailable**, not zero; no response body `.html` exists, no usable destination SHA256 is recorded, and no successful destination-body source is in the current packet. Existing source metadata remains historical lab-name/directory or faculty evidence; it is not a recovered own lab body. Raw remains `unresolved` with its previous blockers.

- `src-c13984dacc78299f`: https://chemistry.ucsd.edu/faculty/alphabetical — observed `2026-10-07T22:53:04+00:00`, role `historical_field_labName`.
- `src-ad1952dbe19fb7d8`: https://chemistry.ucsd.edu/faculty/alphabetical — observed `2026-10-16T00:59:05+00:00`, role `listed_official_source_requires_entity_localization`.
- `src-cd23f174d5146eda`: https://chemistry.ucsd.edu/faculty/profiles/julia-stauber — observed `2026-10-16T01:01:55+00:00`, role `listed_official_source_requires_entity_localization`.

### 720 · ucsd-biochemistry-and-molecular-biophysics-lab-ferguson-lab-fleur-ferguson

Baseline original: [http://fergusonlab.ucsd.edu](http://fergusonlab.ucsd.edu), stableID unchanged. Actual captured attempt: `https://fergusonlab.ucsd.edu/`; last observedAt `2026-10-16T01:09:15+00:00`; queue attempts `3`. Recorded attempt times: `2026-10-16T01:06:14+00:00, 2026-10-16T01:07:15+00:00, 2026-10-16T01:09:15+00:00`. Each listed queue attempt has the same HTTP200/curl63 outcome.

Robots `https://fergusonlab.ucsd.edu/robots.txt` was observed `2026-10-16T01:06:13+00:00` with404, `not_found`, empty error. This HTTPS robots observation is not permission for the unrequested HTTP origin.

[Exact response metadata](/tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/f4aaa4bcba1b3a0f2c56c0cc13aeed1e9559415c3f3102cef6f0be9a82d713c0.json) SHA256 `070617045fa4b5d2b94ddacae18e3a6b4628f516852c116adb7a6626f0bef6db` equals the queue and packet fetch. Content-Length/full response headers are **unavailable**, not zero; no response body `.html` exists, no usable destination SHA256 is recorded, and no successful destination-body source is in the current packet. Existing source metadata remains historical lab-name/directory or faculty evidence; it is not a recovered own lab body. Raw remains `unresolved` with its previous blockers.

- `src-cc43b76023e496bf`: https://bmb.ucsd.edu/faculty — observed `2026-10-07T22:53:34+00:00`, role `historical_field_labName`.
- `src-adb12bae50dedef6`: https://bmb.ucsd.edu/faculty — observed `2026-10-16T00:59:03+00:00`, role `listed_official_source_requires_entity_localization`.

## Constraint and DNS provenance

The local objective is recorded in [summary-goal-receipt.jsonl](/tmp/ucsd-lab-summaries-20261016/docs/operations/summary-goal-receipt.jsonl): complete eligible local summaries and URL/entity verification, preserve original observation times/stable IDs, use collector caches read-only, avoid overlapping slow-host traffic, and make no push/deployment/paid API/contact/form/cloud changes. Those constraints remain intact. The baseline atlas hash is `ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e`.

Saygin remains `robots_unavailable` after3 attempts: `curl: (6) Could not resolve host: sayginlab.ucsd.edu`, latest observed `2026-10-16T03:49:47+00:00`. This is an actual same-host DNS obstacle before protocol/port connection, rather than a response-size default. No DNS lookup or HTTP repeat was performed or proposed for it here.

Parent scope adopted at 2026-10-16T04:40:38+00:00: exactly the two JSON item `url` values may each receive one logical original-URI check with `maxPageBytes=8000000`. Default pages remain2,000,000 bytes and robots remain300,000; no automatic retry or cap escalation. The JSON item decision is `bounded_original_uri_once_8mb` and retains a full deepcopy of the current packet fetch for pre-execution comparison. No check was executed by this reviewer.
