# Late collector destination delta — 05:24 snapshot

**No actionable destination delta.** Reviewed 2026-10-16T05:25:18+00:00; 0 requests. Current 884 packets were read only, against collector queue snapshot **2026-10-16T05:24:10+00:00**, queue updated **2026-10-16T05:23:59+00:00**, SHA `116aa5c13164f54a4475afff44e830992c7304458815dddf48b90f260e5a2f16`. The queue has 18174 items (10676 pending), so this is a finite comparison, not collection completion. Base commit is `641fd9abbcdc2cc3382847acb241695384a0faec`.

The scan covered **1,168 per-record target associations / 1,140 distinct exact request keys**: literal listed roots, selected root request and observed final URIs, plus existing reviewed followup checks/source URIs. Scheme, `www`, path and query remain separate. Matching uses the actual `fetch.sourceUrl`, never a folded queue key or an assumed redirect. Existing summary-task original HTTP captures retain their primary role.

- 893 associations have no capture newer than the already imported actual-request metadata.
- 260 have no actual collector request at that exact target key; an alias or normalized HTTPS capture was not substituted.
- 13 unmatched request associations contain a body SHA already retained in that ID’s packet.
- 1 has different HTML bytes but identical complete visible text and title.
- 1 is an exact capture already scope-reviewed and rejected.
- **0 new useful scientific bodies; 0 material access-result deltas.**

All 15 candidate associations (14 distinct captures) were verified against actual raw cached bytes and original sidecar request URI, final URI, observedAt and SHA. Same-body sources were not scientifically reread. The JSON records every binding, existing primary-root tuple, source IDs and a fingerprint based on the actual capture tuple rather than global queue time.

**iPower3Es, ordinal 502.** [The separately captured final host](https://ipower3es.eng.ucsd.edu/) at 01:02:16 has HTML SHA `9d9d540d6e643b77668377929bbfc93086ed35a0ba4788eb74f49f2eef866b98`. I read its full 2,486-character ContentDOM body. Its title and entire visible text equal retained `src-254ea865b6464cde`, observed 01:00:27 via the original `https://ipower3es.ucsd.edu/` request (HTML SHA `15c721683da6faa37cbd4d55c02627d40f8f877f120459457eea6312441d01f6`). The mission and news are unchanged. No new scientific claim or method follows from the HTML-byte difference; preserve the existing root request and redirect provenance.

**Sallis, ordinal 417.** [The personal root](https://www.drjimsallis.com/) at 02:42:44, SHA `82c069840f63473662b9f8686746d2a93dee49feacd41455f26d5e4c54bef555`, exactly matches the 03:34:56 decision in [DELTA-ASSOCIATION-SCOPE-REVIEW.json](DELTA-ASSOCIATION-SCOPE-REVIEW.json). That body was already individually reviewed as personal career/publication/advocacy/blog content, insufficient for an independent lab programme. The exact body decision was reused; no second HTML read or lab acceptance was performed.

**Concrete next action:** keep current packets, raw summaries, identity decisions and primary HTTP bindings. This snapshot supplies no source for import or summary expansion. A new global `queue.updatedAt`, a different requested alias, or a new observation time alone is not new science. The reviewed frozen handoff remains 16 records at SHA `49c5aa9c7864e67553ec8c4f6273e57284dd204ab13d42dc1f8c98197ae24776`.

Only this report and its JSON companion were written. No code, collector, source, packet, raw record or shared artifact was changed.

| Ordinal | Stable ID | Actual queue request | Original observedAt | Decision |
|---:|---|---|---|---|
| 46 | ucsd-biology-topic-lab-cleland | [actual request](https://clelandlab.biosci.ucsd.edu/) | 2026-10-16T02:42:36+00:00 | same_body_hash_already_retained |
| 62 | ucsd-biology-topic-lab-goldrath | [actual request](https://goldrathlab.com/) | 2026-10-16T01:30:05+00:00 | same_body_hash_already_retained |
| 65 | ucsd-biology-topic-lab-hasty-lab | [actual request](https://synbio.ucsd.edu/biodynamics/) | 2026-10-16T02:41:55+00:00 | same_body_hash_already_retained |
| 97 | ucsd-biology-topic-lab-mikio-aoi | [actual request](https://aoilab.biosci.ucsd.edu/) | 2026-10-16T02:42:33+00:00 | same_body_hash_already_retained |
| 131 | ucsd-biology-topic-lab-suel-gurol | [actual request](https://suellab.github.io/) | 2026-10-16T01:06:31+00:00 | same_body_hash_already_retained |
| 209 | ucsd-hdsi-es-bioinformatics-ai-lab | [actual request](http://esbailab.org/) | 2026-10-16T02:42:37+00:00 | same_body_hash_already_retained |
| 627 | ucsd-live-lab-421d1a9d198202 | [actual request](https://komiyamalab.biosci.ucsd.edu/) | 2026-10-16T01:04:11+00:00 | same_body_hash_already_retained |
| 684 | ucsd-live-lab-86c289fa737e94 | [actual request](https://mentalhealthindesign.weebly.com/) | 2026-10-16T02:42:50+00:00 | same_body_hash_already_retained |
| 552 | ucsd-live-lab-b8a6c47fb14087 | [actual request](https://lewis.uga.edu/) | 2026-10-16T02:40:31+00:00 | same_body_hash_already_retained |
| 502 | ucsd-live-lab-ce0b313a22d83d | [actual request](https://ipower3es.eng.ucsd.edu/) | 2026-10-16T01:02:16+00:00 | same_complete_visible_text_different_html_hash |
| 554 | ucsd-live-lab-ed45a5a6e04fae | [actual request](https://pages.ucsd.edu/~desa/) | 2026-10-16T01:29:29+00:00 | same_body_hash_already_retained |
| 253 | ucsd-neurosciences-lab-komiyama-lab | [actual request](https://komiyamalab.biosci.ucsd.edu/) | 2026-10-16T01:04:11+00:00 | same_body_hash_already_retained |
| 333 | ucsd-pediatrics-lab-lewis-lab | [actual request](https://lewis.uga.edu/lab-members/) | 2026-10-16T02:41:07+00:00 | same_body_hash_already_retained |
| 400 | ucsd-psychiatry-lab-neurocognition-and-movement-lab | [actual request](https://psychiatry.ucsd.edu/index.html) | 2026-10-16T00:57:19+00:00 | same_body_hash_already_retained |
| 417 | ucsd-public-health-lab-visit-the-sallis-lab-website | [actual request](https://www.drjimsallis.com/) | 2026-10-16T02:42:44+00:00 | reuse_exact_previous_scope_rejection |

