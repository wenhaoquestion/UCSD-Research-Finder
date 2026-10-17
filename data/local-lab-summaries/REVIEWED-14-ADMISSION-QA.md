# Reviewed14 admission QA

**PASS** — independent QA completed `2026-10-16T04:46:38+00:00`. No material defects found. Network requests: **0**. Only this QA report pair was written; no raw, packet, network receipt, collector or shared state changed.

Actual strict importer load returned exactly **14 frozen IDs**, verified **26 raw cached captures and original queue timestamps**, and **86 exact field-proof instances**. It used the new approved snapshot SHA `60ff319a0528908097ce5d53955017a04fab5e3a12e2cd1385349e2ffaed6155` with decisions SHA `f472eafcf8619c081550b37ba22a39f38d19972cfe6d23369322f5e3a922ab83`. Thirty aliases and eight updates were ignored; the incremental handoff remains non-final.

## New summaries and evidence

- **880 — ucsd-live-lab-eb3be693359889**: supported whole-lab scientific scope, exact raw evidence, confirmed identity/page binding and `source_matches_fetch` all pass; verified lab/group URL is true. Root capture `2026-10-16T02:12:42+00:00`, SHA `4b224a6fff23b9f6b4f8634ba1045cc1b4f26730f2aa38fb55b3b9d82ab2618b`; source dates remain distinct from preparedAt `2026-10-16T04:42:24+00:00` and record review `2026-10-16T04:43:25+00:00`. PASS: sole method is explicitly stated synchrony modeling in the whole-lab coordination section. No inferred clinical procedure, efficacy or extra modeling technique.
- **881 — ucsd-live-lab-9c13d3e2e45efe**: supported whole-lab scientific scope, exact raw evidence, confirmed identity/page binding and `source_matches_fetch` all pass; verified lab/group URL is true. Root capture `2026-10-16T02:13:51+00:00`, SHA `e8fe46d21e89a77f15b74d6f17938a147366fd99533849e6dda7ad192174a3ff`; source dates remain distinct from preparedAt `2026-10-16T04:42:24+00:00` and record review `2026-10-16T04:43:25+00:00`. PASS: sole method is normative-data development, explicitly supported at that broad level. Sampling/statistical details remain unknown. Lumbar puncture, imaging and brain donation are participation contexts and do not appear in methods.

Ten unique cache-backed sources in the two packets were independently checked against actual raw bytes, exact queue capture tuples and full visible extraction; ten new raw evidence instances are exact. Healthcare synchrony modeling and its coordination purpose are explicitly in the lab’s own coordination-methods paragraph. MILPAS research/ gives the named-lab cultural/linguistic and U.S./Latin-America scope; its method stays at the explicitly stated normative-data-development level. Source-reported PI names, absent PI profile fields and appointment/content-date uncertainty are preserved.

## Old880 and append-only behavior

Compared to Git `7ddc7b291e1202635754ffe8e7480f91fb6ec90f`: **880/880 old packets and 880/880 old raw records have zero changed paths**. The old 880 manifest entries are an exactly equal prefix, retaining IDs/ordinals; the old 12 import-provenance objects are also exactly preserved. Thiemens remains ordinal 879; Healthcare and MILPAS append at 880/881 even though the new handoff puts them before Thiemens. Thus old packet source dates, preparedAt, scientific review dates and import receipts remain byte-identical.

The append-only implementation was read: it reconstructs old order from the prior manifest, checks stable name/URI/existence/ordinal, preserves prior imports, and continues before extraction or packet writes for each old ID. A separately mocked in-memory scenario supplied loader order `new-c, old-b, old-a`; output was `old-a, old-b, new-c`, with old manifest/import dates unchanged, zero old-packet write calls and one new-packet write call. That scenario made zero filesystem writes and mocked checkpoint; production prepare/checkpoint was not invoked by QA.

## Offline checks

The focused handoff test file independently passed **26/26 unittest tests**, plus the separate in-memory append-only scenario. Command: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p test_local_lab_handoff.py -v`. Full evidence/source tuples, code hashes and actual load counts are in the JSON report.
