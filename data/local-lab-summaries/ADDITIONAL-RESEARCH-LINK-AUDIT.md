# Additional research-link discovery audit

Actual review completed: 2026-10-16T03:06:55+00:00. Network requests: **0**.

Inspected the original 207 IDs from `unpacketized-cache-candidates.json`. Ninety had a readable current `listed_lab_destination` HTML capture; all 90 matched original cached bytes, SHA-256, and queue/gap capture time. The other 117 had no current destination HTML to inspect. This audit reads actual anchor/meta attributes, including text, aria-label, title, and image-alt label checks; it does not generate URLs from names.

**Findings:** 20 concrete additional targets: 12 anchors and 8 literal meta-refresh targets. One target (Gymrek) was already captured and its full body was read; 19 remain uncaptured. Twelve other matches were rejected as funding, global directories, blog/tag archives, administrative, people/publication, or clinical-service links. No code, raw, packet, supplemental, collector, or aggregate was changed.

The two actual scientific-label grammar omissions are **Greenspan “Projects”** and **Lab3 “Explore Our Projects”**. Other retained Research links are already accepted by the existing grammar but have no cached target to packetize. VLSI Projects is already recognized from its `/Research/` path; an anchor does not remove the existing robots-denied research-path boundary.

All anchor targets stay on the same scoped site path. Google Sites were kept within their site ID; no extra scientific route was found there. Five cross-site literal meta targets are separately flagged, including the previously known Language and Cognition redirect. A literal meta instruction is not an observed HTTP redirect and does not establish a new canonical lab URL.

Parent-owned 15 group-anchor IDs are untouched. Extra research paths found for those IDs are Greenspan `projects.html`, HDSI Lab3 `/projects`, Interactive Cognition `Kirsh/research.html`, and Thiemens `research.html`.

## Captured target with explicit named-lab research

**637 · Gymrek Lab Homepage** — the [original GitHub root](https://gymreklab.github.io/) contains exact meta `content="0; URL=https://gymreklab.com"`. Its original capture is 2026-10-16T01:06:51+00:00, root SHA-256 `5e828152b72acb419b2de999724370c7153cd800fb88d69cda903fab1a2db72e`.

The [target homepage](https://gymreklab.com/) was independently captured at **2026-10-16T01:03:11+00:00**, SHA-256 `88113141cce0b0786054c57087ac435245012b754d8ef43a9953443e25545d10`; source ID from full recovered text is `src-45a858d307a0463d`. The full 5,797-character body was read. Use the target’s own original time, which is earlier than the redirect-stub capture, rather than copying the stub time.

Exact body evidence suitable for a separate raw/packet review:

> The Gymrek Lab is located at the University of California San Diego.

Supports: identity, affiliation.

> Our overall goal is to understand genetic variants that underlie human disease and how their effects vary across different populations.

Supports: research, topics.

> We are particularly interested in repetitive DNA variants known as tandem repeats (TRs).

Supports: topics.

> Major research areas include (1) developing computational tools for analyzing TR variation in biobank-scale genomic datasets, (2) identifying TRs contributing to both rare and complex traits, (3) studying mutation and selection processes at TRs within and across species, (4) understanding how the effects of TRs and other genetic variants differ across human populations, and (5) using high-throughput experimental techniques to study the impacts of TR and other variants on molecular and cellcular phenotypes in healthy and disease states.

Supports: research, topics, methods.

These quotes precede the Featured publications section; individual paper findings are not used to define the whole lab. The named target identity, explicit literal root relation, and lab-scoped research justify recommending source reuse for the generated Gymrek ID. The original GitHub listed URL and observed HTTP history must remain unchanged; this is evidence reuse, not an automatic URL migration or ID merge.

## Actual attributes and target boundaries

### A01 · 37 · Bennett Lab

ID: `ucsd-biology-topic-lab-bennett-lab`. [Root](https://labs.biology.ucsd.edu/bennett/), captured 2026-10-16T01:03:53+00:00; SHA-256 `ddcae5a4c30a5849a59532c949cbcdabdd1dbb58bd846178abaea4e35ecd2c1b`; source `src-9e979d00395b0a70`.

Actual meta_refresh: `content="0; url=http://ebennettlab.com/"`. Resolved target: [http://ebennettlab.com/](http://ebennettlab.com/).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Literal cross-site refresh only; requires access and same-entity review before importing any destination claims.

### A02 · 38 · Bier Lab

ID: `ucsd-biology-topic-lab-bier`. [Root](https://bierlab.ucsd.edu/), captured 2026-10-16T01:03:54+00:00; SHA-256 `9a971c153ad99cc72353cd30b03dbcd398bf6b705f9784c769e70ded6425c8a1`; source `src-fcd2a788e03afab1`.

Actual meta_refresh: `content="0; url=http://bierlab.weebly.com/"`. Resolved target: [http://bierlab.weebly.com/](http://bierlab.weebly.com/).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Literal cross-site refresh only; requires access and same-entity review before importing any destination claims.

### A03 · 82 · Kiger Lab

ID: `ucsd-biology-topic-lab-kiger`. [Root](https://labs.biology.ucsd.edu/kiger/), captured 2026-10-16T00:59:45+00:00; SHA-256 `492e32ddcc79db4d57b8f99e5563fd8bc747379b24a1189a7c10ee5a0842cd0d`; source `src-f56ebff58b7e8a49`.

Actual meta_refresh: `content="0;url= Amy_Kiger_Lab_at_UCSD/Home.html"`. Resolved target: [https://labs.biology.ucsd.edu/kiger/Amy_Kiger_Lab_at_UCSD/Home.html](https://labs.biology.ucsd.edu/kiger/Amy_Kiger_Lab_at_UCSD/Home.html).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Literal relative refresh stays under /kiger/; no target capture exists yet. Do not invent research from the Amy_Kiger_Lab path.

### A04 · 113 · Ralph Greenspan Lab

ID: `ucsd-biology-topic-lab-ralph-greenspan`. [Root](https://greenspanlab.ucsd.edu/), captured 2026-10-16T01:04:21+00:00; SHA-256 `230c9049ee1ba88ba86300d5aa2fa1e4b17f1cdd1821692b0290f39f07e256f6`; source `src-4e637dc9baddae1f`.

Actual anchor: `Projects` → `href="projects.html"`. Resolved target: [https://greenspanlab.ucsd.edu/projects.html](https://greenspanlab.ucsd.edu/projects.html).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Exact lab-site Projects anchor omitted by label grammar. Extra research path for a parent-owned group-anchor ID; not fetched.

### A05 · 126 · Spitzer Lab

ID: `ucsd-biology-topic-lab-spitzer`. [Root](https://labs.biology.ucsd.edu/spitzer/), captured 2026-10-16T00:59:54+00:00; SHA-256 `d2bf0b44a3e77666df4f903c873468e9c93bff09f5ffc7bd0250d6f5480894ff`; source `src-d064f0b5261fc28f`.

Actual meta_refresh: `content="0; url=http://www.nickspitzerlab.org/"`. Resolved target: [http://www.nickspitzerlab.org/](http://www.nickspitzerlab.org/).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Literal cross-site refresh only; requires access and same-entity review before importing any destination claims.

### A06 · 199 · VLSI CAD Lab

ID: `ucsd-electrical-and-computer-engineering-lab-vlsi-cad-lab`. [Root](https://vlsicad.ucsd.edu/), captured 2026-10-16T00:59:44+00:00; SHA-256 `285a23f99c1498902234939f7587c4d238b6fc63080b20f2deafbdf79de45735`; source `src-e019db031a5d2f86`.

Actual anchor: `Projects` → `href="/Research/Projects/index.html"`. Resolved target: [https://vlsicad.ucsd.edu/Research/Projects/index.html](https://vlsicad.ucsd.edu/Research/Projects/index.html).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Concrete Projects anchor, already accepted by research_links because /Research/ is in the path. Still no cached target; existing robots-denied Research path boundary remains. No new page request is implied or authorized by this audit.

### A07 · 210 · HDSI Lab 3.0

ID: `ucsd-hdsi-lab-3`. [Root](https://lab3.ucsd.edu/), captured 2026-10-16T01:04:59+00:00; SHA-256 `5ddd3e5f7bce313c4826fd5453a417b618a98d265db6762f2f48e61b0cc89d8c`; source `src-91b6960617dbd9f9`.

Actual anchor: `Explore Our Projects` → `href="/projects"`. Resolved target: [https://lab3.ucsd.edu/projects](https://lab3.ucsd.edu/projects).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Exact Explore Our Projects anchor omitted by label grammar. Extra path for parent-owned Lab3 ID; current entity is a facility and projects must not automatically become whole-lab research.

### A08 · 376 · Shelley Wright Research Group

ID: `ucsd-physics-research-site-shelley-wright`. [Root](https://oirlab.ucsd.edu/), captured 2026-10-16T01:05:27+00:00; SHA-256 `92a3b5a77991171ad13605f0665ae30437fea09d8cffce5d3c9d778e83b3ad68`; source `src-6c0a5af04a439d91`.

Actual meta_refresh: `content="0; url=index.php"`. Resolved target: [https://oirlab.ucsd.edu/index.php](https://oirlab.ucsd.edu/index.php).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Literal same-site relative refresh to index.php; no target capture. May contain content distinct from the root stub, but identity/research remain unreviewed.

### A09 · 511 · Interactive Cognition Lab

ID: `ucsd-live-lab-272c61c8e40a29`. [Root](https://adrenaline.ucsd.edu/Kirsh/index.html), captured 2026-10-16T01:06:32+00:00; SHA-256 `4f3584b5a1dd0bf3cd87653fb0a3e0e04360f453651f7312e9a9ec269a3b438a`; source `src-fb3e73c0cd9cdfb7`.

Actual anchor: `Research` → `href="research.html"`. Resolved target: [https://adrenaline.ucsd.edu/Kirsh/research.html](https://adrenaline.ucsd.edu/Kirsh/research.html).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Concrete same-personal-site Research link, already recognized by grammar but uncaptured. Extra path for parent-owned Interactive Cognition ID; named-lab scope must be checked on target.

### A10 · 531 · Language and Cognition Lab

ID: `ucsd-live-lab-a463fe964995c8`. [Root](https://pages.ucsd.edu/~bkbergen/lcl/), captured 2026-10-16T01:06:35+00:00; SHA-256 `36429d2c73b35b9aedaf9ade93ed5e759ccb15e184fae7684c590ba53e34897b`; source `src-59321ed511274590`.

Actual meta_refresh: `content="0; url='https://langcoglab.ucsd.edu/'"`. Resolved target: [https://langcoglab.ucsd.edu/](https://langcoglab.ucsd.edu/).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Literal cross-host meta refresh from the listed UCSD personal-path stub. No target cache; not an observed HTTP redirect or established new canonical lab URL.

### A11 · 535 · Long Lab

ID: `ucsd-live-lab-6c899e2fd695ff`. [Root](https://www.brialong.com/), captured 2026-10-16T01:03:13+00:00; SHA-256 `a5d9817797f203d1ef1d9aebe2da263baad8b30acf975dac46b09941e839d86b`; source `src-58face51fcece39f`.

Actual anchor: `research` → `href="https://www.brialong.com/research"`. Resolved target: [https://www.brialong.com/research](https://www.brialong.com/research).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Same-site personal Research page; uncaptured. Bria Long personal research cannot automatically establish the named Long Lab or its scope.

### A12 · 549 · Miroslav Krstic — lab website

ID: `ucsd-live-lab-79f8d7df25e8a2`. [Root](https://flyingv.ucsd.edu/), captured 2026-10-16T01:00:31+00:00; SHA-256 `d9999d17a4052d57599960bf4267c11e58819e89d9d09cb55f785694a7e08e66`; source `src-d6dea8d6234991d5`.

Actual anchor: `Research` → `href="http://flyingv.ucsd.edu/krstic/Research.html"`. Resolved target: [http://flyingv.ucsd.edu/krstic/Research.html](http://flyingv.ucsd.edu/krstic/Research.html).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Same-site personal Research path under /krstic/; uncaptured. Requires explicit lab/group scope rather than faculty topics.

### A13 · 599 · The SWAG Lab

ID: `ucsd-live-lab-dc77b90e91d80c`. [Root](https://dickenson.ucsd.edu/), captured 2026-10-16T01:06:42+00:00; SHA-256 `73389a0e06271b8ae5cf8dc75fcc4ea01566e91497509e9808ea88976e89cabd`; source `src-0f573363be8a3abb`.

Actual anchor: `Research` → `href="/research"`. Resolved target: [https://dickenson.ucsd.edu/research](https://dickenson.ucsd.edu/research).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Same-site personal Research path; uncaptured. Requires explicit SWAG lab identity/scope before any lab-level claims.

### A14 · 611 · Xu Research Group

ID: `ucsd-live-lab-0f62740a3eaf3f`. [Root](https://xugroup.eng.ucsd.edu/), captured 2026-10-16T01:00:45+00:00; SHA-256 `44030f235000eb37d1356cdaa3698b2b701a4a9e8f5da454aba429b730f39158`; source `src-52320b58391d599f`.

Actual anchor: `Learn about our research` → `href="/research-overview/"`. Resolved target: [https://xugroup.eng.ucsd.edu/research-overview/](https://xugroup.eng.ucsd.edu/research-overview/).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Same scoped Xu group site research-overview anchor; uncaptured. Suitable discovery candidate only, not evidence yet.

### A15 · 628 · The Darquenne Lab

ID: `ucsd-live-lab-93bd07f93724ab`. [Root](https://pulmonary.ucsd.edu/research/labs-centers/darquenne/index.html), captured 2026-10-16T01:03:14+00:00; SHA-256 `fa2f9bd82a1a662b0684d3e452d92b0f869fdb05c17c5ebc0ef2c3dece5d784b`; source `src-73c179acf0c3e0f9`.

Actual anchor: `Research` → `href="research/index.html"`. Resolved target: [https://pulmonary.ucsd.edu/research/labs-centers/darquenne/research/index.html](https://pulmonary.ucsd.edu/research/labs-centers/darquenne/research/index.html).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Same Darquenne scoped lab folder research/index.html; uncaptured. Target must confirm named-lab scope rather than personal faculty interests.

### A16 · 637 · Gymrek Lab Homepage

ID: `ucsd-live-lab-af83b7a0d3289e`. [Root](https://gymreklab.github.io/), captured 2026-10-16T01:06:51+00:00; SHA-256 `5e828152b72acb419b2de999724370c7153cd800fb88d69cda903fab1a2db72e`; source `src-2c04c671c06fb89f`.

Actual meta_refresh: `content="0; URL=https://gymreklab.com"`. Resolved target: [https://gymreklab.com](https://gymreklab.com).

Target: captured and full body read; details above.

Literal refresh plus already captured target explicitly names Gymrek Lab and gives lab-scoped research. Recommend reusing target capture for this ID; retain actual target date and original GitHub listed URL/HTTP history.

### A17 · 686 · Bertrand Group

ID: `ucsd-chemistry-biochemistry-lab-bertrand-group`. [Root](https://bertrandgroup.ucsd.edu/), captured 2026-10-16T01:07:06+00:00; SHA-256 `2de24217448333bb01dd7c904e7a49328c594979e6e251a725bd299984b79033`; source `src-54a12c81f418154e`.

Actual meta_refresh: `content="0;url= Bertrands_group.html"`. Resolved target: [https://bertrandgroup.ucsd.edu/Bertrands_group.html](https://bertrandgroup.ucsd.edu/Bertrands_group.html).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Literal same-site relative refresh to Bertrands_group.html; uncaptured. Root currently has personal-site classification; do not assume group identity until target is reviewed.

### A18 · 752 · Frank Powell Lab

ID: `ucsd-medicine-lab-frank-powell-lab`. [Root](https://pulmonary.ucsd.edu/research/labs-centers/powell/index.html), captured 2026-10-16T01:03:20+00:00; SHA-256 `ebbe703debf589bfba9bd29042e60e40fd17453c207725ff37116c32f26a6189`; source `src-adb80fa4dae215d1`.

Actual anchor: `Research` → `href="research/index.html"`. Resolved target: [https://pulmonary.ucsd.edu/research/labs-centers/powell/research/index.html](https://pulmonary.ucsd.edu/research/labs-centers/powell/research/index.html).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Same Powell scoped lab folder research/index.html; uncaptured. Suitable discovery candidate only.

### A19 · 785 · Konopacky Group

ID: `ucsd-astronomy-and-astrophysics-lab-konopacky-group`. [Root](https://konopackygroup.ucsd.edu/), captured 2026-10-16T01:07:31+00:00; SHA-256 `7ce8f2bc2200dc6017d87abf2692cc97ef1e039aad9e509168a5c585318adae1`; source `src-7734bc55d31603ec`.

Actual anchor: `Research` → `href="https://konopackygroup.ucsd.edu/research/"`. Resolved target: [https://konopackygroup.ucsd.edu/research/](https://konopackygroup.ucsd.edu/research/).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Same Konopacky group site Research link; uncaptured. Target needs explicit group rather than solely personal research scope.

### A20 · 879 · Mark H. Thiemens Research Group

ID: `ucsd-live-lab-176619ff4af12d`. [Root](https://thiemensgroup.ucsd.edu/), captured 2026-10-16T00:59:03+00:00; SHA-256 `67015d450ceea3b3172f53126ee5016fb2658f7baaca4a28370c1e21cb27a6b7`; source `src-d2f343b09f7f3c78`.

Actual anchor: `Research` → `href="http://thiemensgroup.ucsd.edu/research.html"`. Resolved target: [http://thiemensgroup.ucsd.edu/research.html](http://thiemensgroup.ucsd.edu/research.html).

Target: not present in actual queue or gap-results; candidate only, no target body or new request.

Same Thiemens scoped research.html anchor; uncaptured. Extra path for parent-owned group-anchor ID; retain historical 2019 root-content boundary and original dates.

## Rejected matches

| Ordinal | Actual label / target | Rejection |
|---|---|---|
| 273 | Discover "BEST" Research Study → https://obgyn.ucsd.edu/research/clinical-studies-obgyn/best-research-study.html | Generic departmental clinical-study recruitment page; not a named Jacobs lab research page. |
| 356 | Reading and Research Groups → https://philosophy.ucsd.edu/research-groups/reading-research-groups.html | Generic philosophy reading/research-group directory; not an entity-local Field Lab source. |
| 400 | Support Our Work → https://psychiatry.ucsd.edu/give/index.html | Donation/funding destination: Support Our Work -> give/index.html. |
| 680 | we are happy to once again respond to the request of the taxpayers to generate scientific information → https://tlneuro.wordpress.com/2025/06/26/i-work-for-you-as-you-have-repeatedly-requested/ | Dated blog/political funding commentary, not a laboratory research overview. |
| 680 | science → https://tlneuro.wordpress.com/tag/science/ | Blog tag archive, not a named-lab research overview. |
| 680 | “An entire institute that does nothing more than DEI research at NIH.” → https://tlneuro.wordpress.com/2025/07/28/an-entire-institute-that-does-nothing-more-than-dei-research-at-nih/ | Dated blog/political commentary, not a laboratory research overview. |
| 680 | research → https://tlneuro.wordpress.com/tag/research/ | Blog tag archive, not a named-lab research overview. |
| 549 | As Sr. Assoc. Vice Chancellor for Research, Professor Krstic oversees the following UCSD units: → http://flyingv.ucsd.edu/krstic/students+postdocs.html | Anchor title repeats an administrative research-oversight description but href is students+postdocs; not scientific research content. |
| 549 | As Sr. Assoc. Vice Chancellor for Research, Professor Krstic oversees the following UCSD units: → http://flyingv.ucsd.edu/krstic/SAVCR.html | Administrative senior vice-chancellor oversight role page; not lab research. |
| 599 | Clinical Work → https://dickenson.ucsd.edu/clinical-work | Clinical Work service page; not explicit scientific research. |
| 611 | Sheng Xu group research → https://xugroup.eng.ucsd.edu/publications/ | Publication index; generic anchor title does not make it a research overview. |
| 611 | Sheng Xu group research → https://xugroup.eng.ucsd.edu/people/ | People page; generic anchor title does not make it a research overview. |

## Coverage and provenance boundary

No current root HTML by latest destination status: `{"http_error": 46, "robots_unavailable": 62, "robots_denied": 5, "authentication_required": 2, "fetch_error": 2}`. Failures are evidence/access gaps, not evidence of closure. Per-ID coverage, exact raw attributes, original root times/hashes/cache paths, target lookup state, and the Gymrek target evidence are retained in `additional-research-link-audit-inventory.json`.

Input inventory SHA-256: `702159d034e677be3b898132b4b24f5497374d8390d66fbf5783094f5008bef2`. Queue snapshot SHA-256: `7ed1ad7b26b9a4e19a082a3cdb5d1bef496c7ec86fc1dfaa0a7e4a52e3a899ba`. Gap-results snapshot SHA-256: `760eafc0ee29023a24bffe5fce291661a0de97ed3ea57b9b92bdb1741e47a0e3`.

No target already in that ID’s packet was retained as an additional finding. No root with a hash/time mismatch was used. All results remain evidence/discovery recommendations; acceptance gates and existing mismatches remain untouched.
