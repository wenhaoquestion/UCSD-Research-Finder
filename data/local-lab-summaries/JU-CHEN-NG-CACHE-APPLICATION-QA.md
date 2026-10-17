# Ju Chen / Ng cache application QA

Reviewed 2026-10-16T06:09:16+00:00; compared with `5f9a28e3cd523c3bd69e84f8de4e45b13622dff5`. **PASS. Three actual complete bodies read; both records hydrate; zero requests or existing-file edits.**

| Source | Actual HTTP capture / original observation | SHA256 |
| --- | --- | --- |
| `src-d75e35630ead60fd` | [http://juchenlab.ucsd.edu/homepage.htm](http://juchenlab.ucsd.edu/homepage.htm) — 2026-10-16T05:34:24+00:00 | `e37e3262438b0821cd012c26ae9e08b042a7d4df225c989441e0c0a26291f29a` |
| `src-dcaabae720d63562` | [http://juchenlab.ucsd.edu/about.htm](http://juchenlab.ucsd.edu/about.htm) — 2026-10-16T05:35:51+00:00 | `3c7c3cf747a74b2be83b1244d69595448e5e463bc522f6401ede63daf3e45e76` |
| `src-15280fa2dd979d81` | [http://flexible-electronics.ucsd.edu/](http://flexible-electronics.ucsd.edu/) — 2026-10-16T05:32:31+00:00 | `7640df40dd31d09bb282523e91b8e51de00d4594ca6f026879539f53666c28fc` |

All three original cache/sidecar/queue/staging/packet tuples agree: HTTP200, no redirects, exact original time/hash/actual URI, full extraction. Both packets preserve the complete old source prefix, preparedAt and original HTTPS fetch. Entire old raw objects remain exact in history. Baseline IDs/HTTPS listed URLs and unknown PI fields remain unchanged.

**Ju Chen:** official baseline directory/profile links explicitly name Ju Chen Laboratory; actual homepage has full Ju Chen name, lab heading and UCSD School of Medicine. About Lab directly states whole-lab myopathy mechanisms and cardiac-hypertrophy/heart-failure pathways, plus engineered mice, patient iPSCs, physiological measurements and molecular/cell techniques. All four methods are explicit. The added homepage whole-lab overview quote now directly covers cardiac/skeletal myopathy and heart failure. No paper-specific assay, protected Dropbox procedure or therapy benefit is inferred. November/December2025 dates are news, not research/current-appointment dates.

**Ng:** retained official profile and HTTP page both spell Tse Nga (Tina) Ng; the official actual `Lab Website` anchor is exactly `http://flexible-electronics.ucsd.edu/`. Named lab welcome and its plural “We engineer...” sentence support the concise basic summary. `methods=[]` correctly excludes individual vision, bio, prior work and publication examples; faculty evidence is reclassified as personal context while its full old raw is retained. Affiliation remains uncertain. Award/publication years and dynamic copyright do not date the lab programme.

**Original URLs remain failed/uncertain:** Ju Chen HTTPS robots connection failure at03:49:45 and Ng HTTPS robots certificate mismatch at01:01:10 are unchanged; both root identities remain uncertain, requestedUrl=null, canonicalUrl=null and verified=false. The related HTTP successes are separate captures, not HTTPS recovery or cross-protocol redirects.

A cachePath-only relocation to byte-identical own snapshots does not change source ID, URI, observation time/hash or capture count. The report records paths as observed; any later relocation must retain those exact bytes/provenance. No alias, migration, ID merge, PI import or new request was accepted.
