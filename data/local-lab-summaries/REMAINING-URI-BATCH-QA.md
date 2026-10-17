# Remaining original-URI batch QA

**PASS**, reviewed 2026-10-16T05:17:28+00:00; 0 requests by this QA. Raw/packet snapshot read from **2026-10-16T05:15:50+00:00 through 2026-10-16T05:15:52+00:00**, Git base `a63a20802708fffd1004346761e20e96dd72dfc7`. No actionable issue found. Only this report and its JSON companion were written.

Exactly 34 original baseline literal HTTP URIs were checked. Their completed one-shot journals and wire ranges show **32 actual page attempts, 27 successful bodies, 5 HTTP errors and 2 robots-only checks**. The batch occupies wire indices **[241,320)**: 79 wires = 24 robots + 55 page/redirect wires. Each of the 32 actual original-request keys occurs once in its lifecycle; trailing-slash redirects remain distinct wire targets. Original literal URI bindings, actual request keys/live times and final destinations match the root receipts. The 27 successful root cache byte hashes, original metadata observation times, actual source URIs and final URLs all match packet sources; all 34 packet root metadata objects match their batch receipt.

All 79 wires record `fcntl-host-clock-v2`, the correct `originalObservationUrl`, and returned transport evidence. All 34 one-shot journals are complete, match their exact wire intervals and are excluded as page proof by themselves. The offline one-shot key helper closes admission for all 34, including both robots-only outcomes. The Sung robots chain stops at the HTTPS TLS error; Firtel stops at the non-robots redirect boundary. Neither is counted as a page request or body. The five actual page failures are 404s (Subramani, Kleinfeld, Wuerthwein, Goodkind and O’Neil), with no successful source/hash manufactured.

Exactly two page wires used the separately hash-bound 8,000,000-byte exception; 53 other page/redirect wires retain 2,000,000, and all 24 robots wires retain 300,000. The helper validates each exception against its exact reviewed old size-error binding:

| Lab | Original observedAt | Actual body bytes | SHA256 |
|---|---|---:|---|
| Stauber | 2026-10-16T04:57:41+00:00 | 2,299,410 | `5b62ea538e3ccb4e1638756fa37a7ddacc241d9f05efe1fa2816fe5396454915` |
| Ferguson | 2026-10-16T04:57:44+00:00 | 2,042,994 | `599359907591ac6336bd3c0363d04a3914e80f58b3b96a3bbfe4a1e9617499c5` |

Old source objects and old evidence objects remain exact prefixes for **all 34** compared with `a63a208`; the source IDs in the immediate before-observation snapshot are also all retained. This preserves old text, dates and hashes. All 34 raw records hydrate and all quotes are literal at the specified body/title location. Six records have deliberate new scientific values, reviewed below. The other **28** keep summary/questions/topics/methods unchanged; **27** also keep scientific `reviewedAt` unchanged. Sinha is the sole identity-mismatch-review exception: new review time is separate from its preserved `priorScientificReviewedAt`, and its scientific fields remain null/empty.

- **Hampton — PASS:** New named Hampton home prose adds regulated HMGR/ER degradation and an explicitly stated budding-yeast model. Preserved official overview explicitly says Our group and Hampton lab; its older topics remain attributable. Only the stated model organism; no unmentioned assay or imaging technique.
- **Kim — PASS:** The Kim group paragraph itself describes the whole group's protein-dynamics research, the three topics and optical tools; Judy Kim contact plus literal title connects the entity. All three listed optical methods appear literally; no faculty-wide fields are used to synthesize the new research claims.
- **Tezcan — PASS:** Actual HTTP root title binds Tezcan Lab; the independent Research request redirects to its research page. Work by the Tezcan Group and the three named research headings support the Chinese summary. Named toolbox is literal. Affiliation remains uncertain. Research-page redirect is separate from root canonical provenance.
- **Stauber — PASS:** STAUBER LAB and Our research program explicitly scope bioinspired inorganic/organometallic chemistry, recognition, reactive species and catalysts to the named lab. Only synthetic inorganic chemistry is represented as a method. The record retains the prospective-language caveat; no completed biological or catalytic outcome is asserted.
- **Ferguson — PASS:** Research in the Ferguson laboratory explicitly describes its techniques, chemically induced proximity tool compounds, disease signaling and therapeutic goals. It is Fleur Ferguson's lab rather than another Ferguson entity. No unstated protein-degradation technique or clinical efficacy; oncology/neurodegeneration are goals, not established treatment outcomes.
- **Hermann — PASS:** Hermann Lab Home, its real Research.html anchor, Hermann Lab Research title and Our lab/We prose establish whole-lab scope. The 2/2019 statement is preserved as history in summary, uncertainty and sourceContentDates. Biophysical, synthetic organic, crystallographic, structure-guided design/screening and additive/subtractive methods all appear in the full body. No 2026-current project, PI appointment or institutional affiliation inferred.

For these six, 14 cited source/capture associations were independently checked against actual raw cache bytes, full ContentDOM extraction and original sidecar observation time/hash. Every check passes. The detailed JSON records each exact tuple. New methods come from whole-lab research prose, not the old faculty-wide topic listings. Historical evidence is retained as history rather than retimed.

**Sinha:** actual root `http://sinhagroup.ucsd.edu/` returned title `Allen Lab` and “If you are interested, please contact Monica Allen .” at 04:56:45 UTC, SHA `35b50cf6304cafc42e6f4ccbd258eaabf7cf130e132d9541eb379740145c97eb`. It is the new 14th unresolved mismatch, not an accepted alias. Old 13 decision objects are unchanged; total accepted mismatches remains **0**. Sinha’s summary is null, questions/topics/methods are empty, and verified lab/group URL count remains false. Personal/facility rows likewise retain their entity types; success alone has not promoted them to accepted lab/groups. Eight of these 34 snapshot rows meet the full accepted-group plus direct-root identity count.

The four frame/anchor followups that began at 05:16:21 UTC, their later applications and later checkpoint counts are **excluded**. Tezcan’s Research/Team and Hermann’s Research are earlier separate followups at [320,325), checked as scientific sources but not added to the 34 root lifecycle count. Saygin remains the deferred DNS-blocked 35th candidate outside this batch. This is a finite snapshot audit, not a claim about later concurrent changes.

| Batch index | Stable ID | Literal baseline | Result | Original observedAt | Root source | Page scope |
|---:|---|---|---|---|---|---|
| 0 | ucsd-lab-from-faculty-sung-lab-eng-ucsd-edu | [original URI](http://sung-lab.eng.ucsd.edu/) | robots_unavailable | 2026-10-16T04:56:09+00:00 | none | uncertain/research_group |
| 1 | ucsd-biology-topic-lab-bennett-lab | [original URI](http://labs.biology.ucsd.edu/bennett) | ok | 2026-10-16T04:56:11+00:00 | src-cebe2dbe044b27a0 | confirmed/lab |
| 2 | ucsd-biology-topic-lab-bier | [original URI](http://bierlab.ucsd.edu) | ok | 2026-10-16T04:56:13+00:00 | src-c5baf2d450d79f22 | uncertain/lab |
| 3 | ucsd-biology-topic-lab-firtel | [original URI](http://people.biology.ucsd.edu/firtel) | robots_unavailable | 2026-10-16T04:56:14+00:00 | none | uncertain/lab |
| 4 | ucsd-biology-topic-lab-goldrath | [original URI](http://biology.ucsd.edu/labs/goldrath) | ok | 2026-10-16T04:56:17+00:00 | src-6cf67ff1ffd79d15 | confirmed/lab |
| 5 | ucsd-biology-topic-lab-hampton | [original URI](http://hamptonlab.ucsd.edu) | ok | 2026-10-16T04:56:18+00:00 | src-079b069f7c694d83 | confirmed/research_group |
| 6 | ucsd-biology-topic-lab-kiger | [original URI](http://www.biology.ucsd.edu/labs/kiger) | ok | 2026-10-16T04:56:21+00:00 | src-76abe8c329b73470 | uncertain/lab |
| 7 | ucsd-biology-topic-lab-murre | [original URI](http://labs.biology.ucsd.edu/murre) | ok | 2026-10-16T04:56:23+00:00 | src-1e9370a1c7cac8eb | uncertain/unconfirmed |
| 8 | ucsd-biology-topic-lab-spitzer | [original URI](http://www.biology.ucsd.edu/labs/spitzer) | ok | 2026-10-16T04:56:26+00:00 | src-e0224176cdecd4ab | uncertain/lab |
| 9 | ucsd-biology-topic-lab-subramani | [original URI](http://www.biology.ucsd.edu/labs/subramani) | http_error | 2026-10-16T04:56:27+00:00 | none | uncertain/unconfirmed |
| 10 | ucsd-biology-topic-lab-yanofsky | [original URI](http://labs.biology.ucsd.edu/yanofsky/home.html) | ok | 2026-10-16T04:56:28+00:00 | src-89f0f296045c7f5f | confirmed/lab |
| 11 | ucsd-physics-research-site-david-kleinfeld | [original URI](http://physics.ucsd.edu/neurophysics) | http_error | 2026-10-16T04:56:31+00:00 | none | uncertain/unconfirmed |
| 12 | ucsd-physics-research-site-frank-wuerthwein | [original URI](http://www.t2.ucsd.edu/twiki2/bin/view/HEPProjects/FkwsGroup) | http_error | 2026-10-16T04:56:33+00:00 | none | uncertain/unconfirmed |
| 13 | ucsd-physics-research-site-john-m-goodkind | [original URI](http://physics.ucsd.edu/research/condensed_matter/) | http_error | 2026-10-16T04:56:35+00:00 | none | uncertain/unconfirmed |
| 14 | ucsd-physics-research-site-lu-j-sham | [original URI](http://ljssst.physics.ucsd.edu) | ok | 2026-10-16T04:56:39+00:00 | src-5254714b0005f61c | confirmed/personal_research_site |
| 15 | ucsd-physics-research-site-shelley-wright | [original URI](http://oirlab.ucsd.edu) | ok | 2026-10-16T04:56:43+00:00 | src-23b5d4ff05200932 | uncertain/lab |
| 16 | ucsd-physics-research-site-sunil-k-sinha | [original URI](http://sinhagroup.ucsd.edu/) | ok | 2026-10-16T04:56:45+00:00 | src-7da5f97add4fcfac | mismatch/unconfirmed |
| 17 | ucsd-physics-research-site-thomas-m-o-neil | [original URI](http://physics.ucsd.edu/research/plasma/) | http_error | 2026-10-16T04:56:47+00:00 | none | uncertain/unconfirmed |
| 18 | ucsd-structural-engineering-lab-composite-structures-laboratory | [original URI](http://se.ucsd.edu/facilities/composite-structures-laboratory) | ok | 2026-10-16T04:56:50+00:00 | src-4d8d0952c44bd2c8 | confirmed/facility |
| 19 | ucsd-structural-engineering-lab-geotechnical-laboratories | [original URI](http://se.ucsd.edu/facilities/geotechnical-facilities) | ok | 2026-10-16T04:56:52+00:00 | src-25ef0d806015bf06 | confirmed/facility |
| 20 | ucsd-structural-engineering-lab-srmd-laboratory | [original URI](http://se.ucsd.edu/facilities/laboratory-listing/srmd) | ok | 2026-10-16T04:56:54+00:00 | src-9abf6474a6335d0a | confirmed/facility |
| 21 | ucsd-structural-engineering-lab-structural-components-laboratory | [original URI](http://se.ucsd.edu/facilities/structural-components-laboratory) | ok | 2026-10-16T04:56:56+00:00 | src-a5fc160a948272fd | confirmed/facility |
| 22 | ucsd-lab-from-faculty-se-ucsd-edu-facilities-structural-systems-laboratory | [original URI](http://se.ucsd.edu/facilities/structural-systems-laboratory) | ok | 2026-10-16T04:56:58+00:00 | src-55982eaf3e74e880 | confirmed/facility |
| 23 | ucsd-chemistry-biochemistry-lab-hermann-lab | [original URI](http://tch.ucsd.edu) | ok | 2026-10-16T04:57:00+00:00 | src-6b3d477e4eb8109d | confirmed/lab |
| 24 | ucsd-chemistry-biochemistry-lab-jennings-lab | [original URI](http://jenningslab.ucsd.edu) | ok | 2026-10-16T04:57:02+00:00 | src-28f455c9c1ad8216 | uncertain/lab |
| 25 | ucsd-chemistry-biochemistry-lab-kim-group-judy-kim | [original URI](http://galileo.ucsd.edu) | ok | 2026-10-16T04:57:03+00:00 | src-8958d5c5bb90cf1a | confirmed/research_group |
| 26 | ucsd-chemistry-biochemistry-lab-kummel-lab | [original URI](http://kummelgroup.ucsd.edu) | ok | 2026-10-16T04:57:05+00:00 | src-4eed6cd432ff1acd | confirmed/lab |
| 27 | ucsd-chemistry-biochemistry-lab-romero-research-group-erik-romero | [original URI](http://r2g.ucsd.edu) | ok | 2026-10-16T04:57:07+00:00 | src-04a051aebaebcc7c | confirmed/research_group |
| 28 | ucsd-chemistry-biochemistry-lab-tezcan-lab | [original URI](http://tezcan.ucsd.edu) | ok | 2026-10-16T04:57:09+00:00 | src-f01bfbff3e573fae | confirmed/lab |
| 29 | ucsd-chemistry-biochemistry-lab-theodorakis-group | [original URI](http://theodorakisgroup.ucsd.edu) | ok | 2026-10-16T04:57:13+00:00 | src-3372ef1abcf939e2 | uncertain/research_group |
| 30 | ucsd-structural-engineering-lab-ucsd-structural-health-monitoring-shm-group | [original URI](http://shm.ucsd.edu/) | ok | 2026-10-16T04:57:37+00:00 | src-78fc5f4fd64950d0 | uncertain/research_group |
| 31 | ucsd-structural-engineering-lab-multifunctional-materials-research-laboratory-mmrl | [original URI](http://mmrl.ucsd.edu/) | ok | 2026-10-16T04:57:39+00:00 | src-3bf96383b726f054 | confirmed/lab |
| 32 | ucsd-chemistry-biochemistry-lab-stauber-lab | [original URI](http://stauberlab.ucsd.edu/) | ok | 2026-10-16T04:57:41+00:00 | src-27301218356c2999 | confirmed/lab |
| 33 | ucsd-biochemistry-and-molecular-biophysics-lab-ferguson-lab-fleur-ferguson | [original URI](http://fergusonlab.ucsd.edu) | ok | 2026-10-16T04:57:44+00:00 | src-989b7fedff9fa338 | confirmed/lab |
