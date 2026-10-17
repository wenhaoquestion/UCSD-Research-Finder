# Identity mismatch decisions

Current reviewed IDs: **14**, accepted: **0**. The later original-URI observation identified the Sinha/Allen mismatch; its separate evidence and actual dates appear in the final section. The following13-ID counters and table retain their historical scope.

Historical 13-ID checkpoint (before the original-URI batch): reviewed 13 stable IDs: the initial 11 page mismatches, the historical-entity Kolodner outside that list, and one additional previously supported Kolodner ID. Accepted: 0. Identity follow-up source URL checks: 6; identity-related wire requests: 7; original mismatching destination requests: 0.

| Stable ID | Observed page type | Decision / acceptance | Follow-up source liveCheckedAt |
|---|---|---|---|
| ucsd-biology-topic-lab-not-in-a-biology-group | lab | needs_name_correction | — (no new wire) |
| ucsd-chemistry-biochemistry-lab-lab-safety-videos | educational_resource | rejected_non_lab | — (no new wire) |
| ucsd-neurosciences-lab-malinow-lab | domain_sale | provisional_historical_lab | 2026-10-16T02:14:27+00:00 |
| ucsd-pathology-lab-laboratory-genomic-medicine | departmental_division | rejected_non_lab | — (no new wire) |
| ucsd-lab-from-faculty-philosophy-ucsd-edu-research-groups-research-groups-overview-html | research_group_directory | unresolved_identity | — (no new wire) |
| ucsd-physics-biological-physics | research_field_directory | rejected_non_lab | — (no new wire) |
| ucsd-live-lab-c47793a464ccdc | course | rejected_non_lab | — (no new wire) |
| ucsd-live-lab-48032dc33264ea | clinical_trials_overview | rejected_non_lab | — (no new wire) |
| ucsd-live-lab-d2d234fc0f3eba | center_or_institute | unresolved_entity_relationship | 2026-10-16T02:14:29+00:00 |
| ucsd-live-lab-ca0f4105fff103 | institutional_homepage | provisional_historical_lab | 2026-10-16T02:21:49+00:00 |
| ucsd-live-lab-61e490319a4560 | institutional_homepage | provisional_historical_lab | 2026-10-16T02:22:09+00:00 |
| ucsd-cellular-molecular-medicine-lab-kolodner-lab | institutional_homepage | provisional_historical_lab | 2026-10-16T02:14:30+00:00 |
| ucsd-live-lab-d38261da50a200 | institutional_homepage | provisional_historical_lab | 2026-10-16T02:22:30+00:00 |

## Not in a Biology group Lab

`ucsd-biology-topic-lab-not-in-a-biology-group`

旧名称是错误类别标签；目的页明确为 Kendrick lab。仅保留该目的页的候选研究描述，旧ID与该实验室的身份映射未接受。 后续来源复核：复用的UCSD教师页于2026-10-16T01:07:45+00:00捕获，正文仅导航及“Aga Kendrick”，没有实验室映射说明。Kendrick目的页研究只支持候选实体，旧类别标签的更名仍未接受；本轮无新页面请求。

Research content: supported_for_candidate_entity_only. Entity accepted: false. Original check: `2026-10-16T01:04:19+00:00`; model review: `2026-10-16T02:17:52+00:00`.

- Follow-up: [source](https://biology.ucsd.edu/research/faculty/akendrick) · reviewed_reused_capture_insufficient_entity_text · source observedAt 2026-10-16T01:07:45+00:00 · actual liveCheckedAt None · original destination rechecked: false
- Welcome to the Kendrick lab — [source](https://kendrick.salk.edu/) · 2026-10-16T01:04:19+00:00
- Home | Kendrick Lab - Salk Institute for Biological Studies — [source](https://kendrick.salk.edu/) · 2026-10-16T01:04:19+00:00
- Aga Kendrick — [source](https://biology.ucsd.edu/research/faculty/akendrick) · 2026-10-16T01:07:45+00:00

Correction candidates only (not applied): [{"field": "labName", "value": "Kendrick Lab", "status": "candidate_only_not_applied"}]

## Lab Safety Videos

`ucsd-chemistry-biochemistry-lab-lab-safety-videos`

正文与标题均为实验室安全教学视频资源；明确排除为独立研究lab或group。 后续来源复核：复读已存正文与标题，仍明确是实验室安全教学视频资源，没有独立研究实体；没有为此资源发起新的身份请求。

Research content: not_applicable_to_lab. Entity accepted: false. Original check: `2026-10-16T01:04:54+00:00`; model review: `2026-10-16T02:17:52+00:00`.

- Follow-up: [source](https://chemistry.ucsd.edu/safety/Lab-Safety-Videos.html) · reviewed_existing_capture_non_lab_classification_unchanged · source observedAt 2026-10-16T01:04:54+00:00 · actual liveCheckedAt None · original destination rechecked: false
- UCSD Lab Safety Videos Chem/Biochem - Lab Safety Videos — [source](https://chemistry.ucsd.edu/safety/Lab-Safety-Videos) · 2026-10-16T01:04:54+00:00
- UCSD Lab Safety Videos | Department of Chemistry — [source](https://chemistry.ucsd.edu/safety/Lab-Safety-Videos) · 2026-10-16T01:04:54+00:00

Correction candidates only (not applied): [{"field": "entityClassification", "value": "educational_resource", "status": "candidate_only_not_applied"}]

## Malinow Lab – Center for Neural Circuits & Behavior (CNCB)

`ucsd-neurosciences-lab-malinow-lab`

历史官方目录列出 Malinow Lab；当前地址转为域名出售页面，不能核实原实验室官网，更不能据此推断实验室关闭。 后续来源复核：共享适配器实际重取的神经科学目录于2026-10-16T02:14:28+00:00仍列Malinow Lab，并在HTML中仍链接http://webaxon.com/index.html。这补强官方目录条目存在的证据，但没有修复旧网址的域名出售错配；旧目的网址本轮未重新请求。

Research content: insufficient_lab_research. Entity accepted: false. Original check: `2026-10-16T01:05:08+00:00`; model review: `2026-10-16T02:17:52+00:00`.

- Follow-up: [source](https://neurosciences.ucsd.edu/research/labs/index.html) · reviewed_live_directory_old_link_unresolved · source observedAt 2026-10-16T02:14:28+00:00 · actual liveCheckedAt 2026-10-16T02:14:27+00:00 · original destination rechecked: false
  - HTML anchor `Malinow Lab – Center for Neural Circuits & Behavior (CNCB)` → `http://webaxon.com/index.html` · src-d81f1215c84293b2 · 2026-10-16T02:14:28+00:00 · parsed cached HTML attribute, not literal page prose
- Malinow Lab – Center for Neural Circuits & Behavior (CNCB) — [source](https://neurosciences.ucsd.edu/research/labs/index.html) · 2026-10-02T22:42:05+00:00
- WebAxon.com This domain is for sale — [source](https://www.hugedomains.com/domain_profile.cfm?d=webaxon.com) · 2026-10-16T01:05:08+00:00
- WebAxon.com is for sale | HugeDomains — [source](https://www.hugedomains.com/domain_profile.cfm?d=webaxon.com) · 2026-10-16T01:05:08+00:00
- Malinow Lab – Center for Neural Circuits & Behavior (CNCB) — [source](https://neurosciences.ucsd.edu/research/labs/index.html) · 2026-10-16T02:14:28+00:00

## Laboratory & Genomic Medicine

`ucsd-pathology-lab-laboratory-genomic-medicine`

页面明确为由 Division Chief 负责、包含多位教师及临床检验服务的院系分部，不是单一研究实验室。 后续来源复核：复读已存分部页面，Division Chief、临床服务和多位教师仍支持院系分部分类；不能作为单一lab接受，本轮无新请求。

Research content: not_applicable_to_lab. Entity accepted: false. Original check: `2026-10-16T00:57:27+00:00`; model review: `2026-10-16T02:17:52+00:00`.

- Follow-up: [source](https://pathology.ucsd.edu/divisions/laboratory-genomic-medicine/index.html) · reviewed_existing_capture_non_lab_classification_unchanged · source observedAt 2026-10-16T00:57:27+00:00 · actual liveCheckedAt None · original destination rechecked: false
- Division of Laboratory and Genomic Medicine — [source](https://pathology.ucsd.edu/divisions/laboratory-genomic-medicine/index.html) · 2026-10-16T00:57:27+00:00
- Laboratory & Genomic Medicine — [source](https://pathology.ucsd.edu/divisions/laboratory-genomic-medicine/index.html) · 2026-10-16T00:57:27+00:00

Correction candidates only (not applied): [{"field": "entityClassification", "value": "departmental_division", "status": "candidate_only_not_applied"}]

## Field Lab

`ucsd-lab-from-faculty-philosophy-ucsd-edu-research-groups-research-groups-overview-html`

目的页为多组研究活动总览；完整捕获正文未见 Field Lab。保持该旧ID身份未解决，不把别的小组或整个目录迁移为此ID。 后续来源复核：复用的完整研究小组目录捕获仍未出现Field Lab，其他小组内容不能替代该旧ID；本轮未重新请求此目录。

Research content: insufficient_lab_research. Entity accepted: false. Original check: `2026-10-16T01:05:20+00:00`; model review: `2026-10-16T02:17:52+00:00`.

- Follow-up: [source](https://philosophy.ucsd.edu/research-groups/research-groups-overview.html) · reviewed_reused_directory_no_entity_match · source observedAt 2026-10-16T01:05:20+00:00 · actual liveCheckedAt None · original destination rechecked: false
- Research Groups History of Philosophy Roundtable — [source](https://philosophy.ucsd.edu/research-groups/research-groups-overview.html) · 2026-10-16T01:05:20+00:00
- Research Groups Homepage — [source](https://philosophy.ucsd.edu/research-groups/research-groups-overview.html) · 2026-10-16T01:05:20+00:00

## UCSD Biological Physics Lab

`ucsd-physics-biological-physics`

页面是 Physics of Life 研究领域及多个教师实验室的目录，列有 Hwa、Jun、Kleinfeld 等组；不接受为一个独立 UCSD Biological Physics Lab。 后续来源复核：复读已存Physics of Life页面，它列出多个教师实验室；领域目录分类不变，本轮无新请求。

Research content: not_applicable_to_lab. Entity accepted: false. Original check: `2026-10-16T01:05:29+00:00`; model review: `2026-10-16T02:17:52+00:00`.

- Follow-up: [source](https://biophysics.physics.ucsd.edu) · reviewed_existing_capture_non_lab_classification_unchanged · source observedAt 2026-10-16T01:05:29+00:00 · actual liveCheckedAt None · original destination rechecked: false
- UCSD Biological Physics Physics of Life — [source](https://biophysics.physics.ucsd.edu/) · 2026-10-16T01:05:29+00:00
- UCSD Biological Physics — [source](https://biophysics.physics.ucsd.edu/) · 2026-10-16T01:05:29+00:00

Correction candidates only (not applied): [{"field": "entityClassification", "value": "research_field_directory", "status": "candidate_only_not_applied"}]

## CSE-198 - Directed Group Study.

`ucsd-live-lab-c47793a464ccdc`

正文明确列出课程编号、学分、先修要求与选课安排；小组学习课程不构成固定研究lab/group。 后续来源复核：复读已存CSE-198页面，课程编号、学分、先修与选课规则明确；课程不能作为固定科研团队接受，本轮无新请求。

Research content: not_applicable_to_lab. Entity accepted: false. Original check: `2026-10-16T01:06:30+00:00`; model review: `2026-10-16T02:17:52+00:00`.

- Follow-up: [source](https://cse.ucsd.edu/undergraduate/courses/course-descriptions/cse198-directed-group-study) · reviewed_existing_capture_non_lab_classification_unchanged · source observedAt 2026-10-16T01:06:30+00:00 · actual liveCheckedAt None · original destination rechecked: false
- CSE-198 - Directed Group Study Units: 2-4 — [source](https://cse.ucsd.edu/undergraduate/cse-198-directed-group-study) · 2026-10-16T01:06:30+00:00
- CSE-198 - Directed Group Study | Computer Science — [source](https://cse.ucsd.edu/undergraduate/cse-198-directed-group-study) · 2026-10-16T01:06:30+00:00

Correction candidates only (not applied): [{"field": "entityClassification", "value": "course", "status": "candidate_only_not_applied"}]

## National Cooperative Group Clinical Trials

`ucsd-live-lab-48032dc33264ea`

页面概述多个全国合作组及多位研究者的临床试验活动，未定义名为 National Cooperative Group Clinical Trials 的独立实验室。 后续来源复核：复读已存临床试验总览，它描述多个全国合作组和研究者；没有独立同名实验室，本轮无新请求。

Research content: not_applicable_to_lab. Entity accepted: false. Original check: `2026-10-16T01:06:36+00:00`; model review: `2026-10-16T02:17:52+00:00`.

- Follow-up: [source](https://radonc.ucsd.edu/research/clinical-trials.html) · reviewed_existing_capture_non_lab_classification_unchanged · source observedAt 2026-10-16T01:06:36+00:00 · actual liveCheckedAt None · original destination rechecked: false
- Our researchers are national leaders in multiple national cooperative groups, including the NRG and Alliance Groups — [source](https://radonc.ucsd.edu/research/clinical-trials.html) · 2026-10-16T01:06:36+00:00
- Clinical Trials — [source](https://radonc.ucsd.edu/research/clinical-trials.html) · 2026-10-16T01:06:36+00:00

Correction candidates only (not applied): [{"field": "entityClassification", "value": "clinical_trials_overview", "status": "candidate_only_not_applied"}]

## Microcirculation Laboratory

`ucsd-live-lab-d2d234fc0f3eba`

当前正文为 Center for Autodigestion Innovation，HTML标题仍为 Microcirculation Laboratory；历史目录关联 Schmid-Schoenbein Lab。缺少解释更名/继承/共同实体关系的正文，禁止把旧ID静默迁移到中心。 后续来源复核：共享适配器于2026-10-16T02:14:30+00:00取得的生物工程目录正文仍列Schmid-Schoenbein Lab及Geert Schmid-Schoenbein；缓存HTML的Website锚点仍指向同一Google Site。目录关联因此有新证据，但没有解释旧Microcirculation Laboratory与Center for Autodigestion Innovation的更名、继承或共同实体关系；Google目的页本轮未重取。

Research content: provisional_identity_mismatch_research. Entity accepted: false. Original check: `2026-10-16T01:06:40+00:00`; model review: `2026-10-16T03:25:41+00:00`.

- Follow-up: [source](https://bioengineering.ucsd.edu/research-focus) · reviewed_live_directory_entity_relationship_unresolved · source observedAt 2026-10-16T02:14:30+00:00 · actual liveCheckedAt 2026-10-16T02:14:29+00:00 · original destination rechecked: false
  - HTML anchor `Schmid-Schoenbein Lab` → `https://sites.google.com/ucsd.edu/microcirculation-autodigestion/home` · src-619879218642aac1 · 2026-10-16T02:14:30+00:00 · parsed cached HTML attribute, not literal page prose
  - HTML anchor `Website` → `https://sites.google.com/ucsd.edu/microcirculation-autodigestion/home` · src-619879218642aac1 · 2026-10-16T02:14:30+00:00 · parsed cached HTML attribute, not literal page prose
  - HTML anchor `Schmid-Schoenbein Lab` → `https://microcirculation.eng.ucsd.edu/` · src-619879218642aac1 · 2026-10-16T02:14:30+00:00 · parsed cached HTML attribute, not literal page prose
- Center for Autodigestion Innovation — [source](https://sites.google.com/ucsd.edu/microcirculation-autodigestion/home) · 2026-10-16T01:06:40+00:00
- [保存的人工审阅记录；非官方页面逐字原文] The destination returns a public page titled Microcirculation Laboratory, without an authentication redirect. — [source](https://sites.google.com/ucsd.edu/microcirculation-autodigestion/home) · 2026-10-03T00:05:51+00:00
- Microcirculation Laboratory — [source](https://sites.google.com/ucsd.edu/microcirculation-autodigestion/home) · 2026-10-16T01:06:40+00:00
- [历史官方目录原文] Schmid-Schoenbein Lab Principal Investigator: Geert Schmid-Schoenbein Website | gschmid@ucsd.edu — [source](https://bioengineering.ucsd.edu/research-focus) · 2026-10-02T22:42:07+00:00
- [保存的人工审阅记录；非官方页面逐字原文] One Schmid-Schoenbein Lab card names Geert Schmid-Schoenbein as principal investigator, links the lab name to microcirculation.eng.ucsd.edu, and links Website to the Google Site at microcirculation-autodigestion/home. — [source](https://bioengineering.ucsd.edu/research-focus) · 2026-10-02T22:42:07+00:00
- Schmid-Schoenbein Lab Principal Investigator: Geert Schmid-Schoenbein Website | gschmid@ucsd.edu — [source](https://bioengineering.ucsd.edu/research-focus) · 2026-10-16T02:14:30+00:00
- AUTODIGESTION Schmid-Schoenbein Lab Principal Investigator: Geert Schmid-Schoenbein — [source](https://bioengineering.ucsd.edu/research-focus) · 2026-10-16T02:14:30+00:00
- Microcirculation Laboratory Center for Autodigestion Innovation — [source](https://sites.google.com/ucsd.edu/microcirculation-autodigestion/home) · 2026-10-16T01:06:40+00:00
- The Microcirculation Laboratory at UC San Diego was founded in 1967 by the late Benjamin W. Zweifach, one of the imminent teachers of Bioengineering and Microcirculation in the twentieth century. In 1979, Geert W. Schmid-Schönbein assumed the directorship of the laboratory. — [source](https://sites.google.com/ucsd.edu/microcirculation-autodigestion/people/about-microcirculation) · 2026-10-16T03:18:08+00:00

Correction candidates only (not applied): [{"field": "observedEntityNameCandidate", "value": "Center for Autodigestion Innovation", "status": "candidate_only_not_applied"}]

## Zhou Lab

`ucsd-live-lab-ca0f4105fff103`

原具名Ludwig实验室路径在既有捕获中跳到机构主页，网址身份仍不匹配。 后续来源复核：共享适配器于2026-10-16T02:21:50+00:00取得Huilin Zhou的UCSD Profiles完整正文，仍明确描述my laboratory的基因组完整性、DNA损伤检查点、SUMO化/泛素化及酵母与遗传、生化、蛋白质组方法。HTML中Zhou Lab仍链接旧Ludwig的huilin-zhou-lab路径，没有链接或说明huilinzhoulab.org候选站与旧ID的别名或继承关系；旧目的页本轮未重取，mismatch与候选未接受状态不变。

Research content: fresh_official_lab_content_supported. Entity accepted: false. Original check: `2026-10-16T01:06:44+00:00`; model review: `2026-10-16T02:24:35+00:00`.

- Follow-up: [source](https://profiles.ucsd.edu/huilin.zhou) · reviewed_live_profile_old_link_identity_unresolved · source observedAt 2026-10-16T02:21:50+00:00 · actual liveCheckedAt 2026-10-16T02:21:49+00:00 · original destination rechecked: false
  - HTML anchor `Zhou Lab` → `http://www.ludwigcancerresearch.org/location/san-diego-branch/huilin-zhou-lab` · src-0365d23bdcef412b · 2026-10-16T02:21:50+00:00 · parsed cached HTML attribute, not literal page prose
- Follow-up: [source](https://www.huilinzhoulab.org/) · reviewed_reused_candidate_identity_unaccepted · source observedAt 2026-10-16T01:04:53+00:00 · actual liveCheckedAt None · original destination rechecked: false
- Zhou Lab → http://www.ludwigcancerresearch.org/location/san-diego-branch/huilin-zhou-lab — [source](https://profiles.ucsd.edu/huilin.zhou) · 2026-10-07T22:07:07+00:00
- Our Research Programs Tumor biology Tumor microenvironment — [source](https://www.ludwigcancerresearch.org/) · 2026-10-16T01:06:44+00:00
- Ludwig Cancer Research — [source](https://www.ludwigcancerresearch.org/) · 2026-10-16T01:06:44+00:00
- Huilin Zhou Lab — [source](https://www.huilinzhoulab.org/) · 2026-10-16T01:04:53+00:00
- Featured Content webpage Department of Cellular and Molecular Medicine Zhou Lab — [source](https://profiles.ucsd.edu/huilin.zhou) · 2026-10-16T02:21:50+00:00

Correction candidates only (not applied): [{"field": "labWebsiteUrl", "value": "https://www.huilinzhoulab.org/", "status": "candidate_only_not_applied", "sourceRecordLabId": "ucsd-cellular-molecular-medicine-lab-zhou-lab", "sourceUrl": "https://www.huilinzhoulab.org/", "sourceObservedAt": "2026-10-16T01:04:53+00:00", "sourceEvidence": "Huilin Zhou Lab", "evidenceLocation": "title", "reason": "A separately stored named lab website is a correction candidate. Do not merge IDs or assume the old path has this identity without an explicit alias/full-person match review."}]

## Oegema Lab

`ucsd-live-lab-61e490319a4560`

原具名Ludwig实验室路径在既有捕获中跳到机构主页，网址身份仍不匹配。 后续来源复核：共享适配器于2026-10-16T02:22:10+00:00取得Karen Oegema的UCSD Profiles完整正文，直接描述The Oegema lab以哺乳动物细胞和C. elegans胚胎平行研究细胞分裂与胚胎发育。HTML中Oegema Lab仍链接旧Ludwig的karen-oegema-lab路径，而非oegemadesailab.org；没有明确说明联合候选站是旧ID的别名或继承实体。旧目的页本轮未重取，mismatch保留，Desai/Oegema稳定ID不合并。

Research content: fresh_official_lab_content_supported. Entity accepted: false. Original check: `2026-10-16T01:06:47+00:00`; model review: `2026-10-16T02:24:35+00:00`.

- Follow-up: [source](https://profiles.ucsd.edu/karen.oegema) · reviewed_live_profile_old_link_identity_unresolved · source observedAt 2026-10-16T02:22:10+00:00 · actual liveCheckedAt 2026-10-16T02:22:09+00:00 · original destination rechecked: false
  - HTML anchor `Oegema Lab` → `http://www.ludwigcancerresearch.org/location/san-diego-branch/karen-oegema-lab` · src-a117e246013e032e · 2026-10-16T02:22:10+00:00 · parsed cached HTML attribute, not literal page prose
- Follow-up: [source](http://www.oegemadesailab.org/) · reviewed_reused_candidate_identity_unaccepted · source observedAt 2026-10-16T00:57:54+00:00 · actual liveCheckedAt None · original destination rechecked: false
- Oegema Lab → http://www.ludwigcancerresearch.org/location/san-diego-branch/karen-oegema-lab — [source](https://profiles.ucsd.edu/karen.oegema) · 2026-10-07T22:08:37+00:00
- The Oegema lab takes parallel approaches in mammalian cells and using the C. elegans embryo as a metazoan model system to study cell division and embryonic development. — [source](https://profiles.ucsd.edu/karen.oegema) · 2026-10-07T22:08:37+00:00
- Our Research Programs Tumor biology Tumor microenvironment — [source](https://www.ludwigcancerresearch.org/) · 2026-10-16T01:06:47+00:00
- Ludwig Cancer Research — [source](https://www.ludwigcancerresearch.org/) · 2026-10-16T01:06:47+00:00
- Oegema and Desai Labs — [source](http://www.oegemadesailab.org/) · 2026-10-16T00:57:54+00:00
- The Oegema lab takes parallel approaches in mammalian cells and using the C. elegans embryo as a metazoan model system to study cell division and embryonic development. — [source](https://profiles.ucsd.edu/karen.oegema) · 2026-10-16T02:22:10+00:00
- Featured Content webpage Department of Cellular and Molecular Medicine Oegema Lab — [source](https://profiles.ucsd.edu/karen.oegema) · 2026-10-16T02:22:10+00:00

Correction candidates only (not applied): [{"field": "labWebsiteUrl", "value": "http://www.oegemadesailab.org/", "status": "candidate_only_not_applied", "sourceRecordLabId": "ucsd-biology-topic-lab-arshad-desai", "sourceUrl": "http://www.oegemadesailab.org/", "sourceObservedAt": "2026-10-16T00:57:54+00:00", "sourceEvidence": "Oegema and Desai Labs", "evidenceLocation": "title", "reason": "A separately stored named lab website is a correction candidate. Do not merge IDs or assume the old path has this identity without an explicit alias/full-person match review."}]

## Kolodner Lab

`ucsd-cellular-molecular-medicine-lab-kolodner-lab`

此前 entityIdentity 为 mismatch、pageIdentity 为 uncertain；当前主抓取标题和内容明确为 Ludwig 机构主页。另列审核，不能用机构癌症研究方向补作 Kolodner lab 研究或当前身份。 后续来源复核：共享适配器于2026-10-16T02:14:31+00:00取得的CMM目录仍列Kolodner Lab，HTML链接仍为原Ludwig scientist/richard-d-kolodner路径。该目录只确认官方条目及旧链接，未提供专属研究或修复机构主页跳转；原Ludwig网址本轮未重取。

Research content: provisional_explicit_named_lab_research_supported. Entity accepted: false. Original check: `2026-10-16T01:04:50+00:00`; model review: `2026-10-16T02:17:52+00:00`.

- Follow-up: [source](https://cmm.ucsd.edu/research/labs/) · reviewed_live_directory_old_link_unresolved · source observedAt 2026-10-16T02:14:31+00:00 · actual liveCheckedAt 2026-10-16T02:14:30+00:00 · original destination rechecked: false
  - HTML anchor `Kolodner Lab` → `https://www.ludwigcancerresearch.org/scientist/richard-d-kolodner/` · src-1c6df0a57807721b · 2026-10-16T02:14:31+00:00 · parsed cached HTML attribute, not literal page prose
- Kolodner Lab — [source](https://cmm.ucsd.edu/research/labs/) · 2026-10-02T22:42:07+00:00
- Ludwig Cancer Research is an international community of distinguished scientists dedicated to preventing and controlling cancer. — [source](https://www.ludwigcancerresearch.org/about/) · 2026-10-16T01:30:39+00:00
- Ludwig Cancer Research — [source](https://www.ludwigcancerresearch.org/) · 2026-10-16T01:04:50+00:00
- Kolodner Lab — [source](https://cmm.ucsd.edu/research/labs/) · 2026-10-16T02:14:31+00:00
- The Kolodner lab also has research interests in the area of investigating the genetics of cancer susceptibility and development — [source](https://profiles.ucsd.edu/richard.kolodner) · 2026-10-16T02:22:30+00:00

## Kolodner Lab

`ucsd-live-lab-d38261da50a200`

原具名Ludwig实验室路径在既有捕获中跳到机构主页，网址身份仍不匹配。 后续来源复核：共享适配器于2026-10-16T02:22:30+00:00取得Richard Kolodner的UCSD Profiles完整正文，明确提供Our laboratory与The Kolodner lab的DNA修复、重组、突变抑制、染色体重排及癌症易感性研究，并明确酿酒酵母模型。HTML中的Kolodner Lab仍链接旧Ludwig的richard-kolodner-lab路径；本次取得的是官方教师档案，不是该旧目的页的重取。研究支持得到刷新，但Ludwig机构主页错配不变，第二个Kolodner稳定ID仍partial/provisional且不与具名ID合并。

Research content: fresh_official_lab_content_supported. Entity accepted: false. Original check: `2026-10-16T01:06:36+00:00`; model review: `2026-10-16T02:24:35+00:00`.

- Follow-up: [source](https://profiles.ucsd.edu/richard.kolodner) · reviewed_live_profile_old_link_identity_unresolved · source observedAt 2026-10-16T02:22:30+00:00 · actual liveCheckedAt 2026-10-16T02:22:30+00:00 · original destination rechecked: false
  - HTML anchor `Kolodner Lab` → `http://www.ludwigcancerresearch.org/location/san-diego-branch/richard-kolodner-lab` · src-8b07c4927ae2b0ce · 2026-10-16T02:22:30+00:00 · parsed cached HTML attribute, not literal page prose
- Kolodner lab — [source](https://profiles.ucsd.edu/richard.kolodner) · 2026-10-07T21:46:36+00:00
- Ludwig Cancer Research — [source](https://www.ludwigcancerresearch.org/) · 2026-10-16T01:06:36+00:00
- The Kolodner lab also has research interests in the area of investigating the genetics of cancer susceptibility and development — [source](https://profiles.ucsd.edu/richard.kolodner) · 2026-10-16T02:22:30+00:00
- Featured Content webpage Department of Cellular and Molecular Medicine Kolodner Lab — [source](https://profiles.ucsd.edu/richard.kolodner) · 2026-10-16T02:22:30+00:00


## Sunil K. Sinha — 新观察的第14项错配

`ucsd-physics-research-site-sunil-k-sinha`

原始 HTTP 地址于 2026-10-16T04:56:45+00:00 实际返回200，页面标题为 **Allen Lab**，正文仅明确联系 Monica Allen。HTTP重定向链为空；没有解释该页面与 Sunil K. Sinha 的共同实体、别名或继承关系。保留原ID和输入网址，Allen页面的研究不归入Sinha，摘要保持unresolved，身份mismatch/provisional，未接受更名、合并或网址迁移。

- [原始来源](http://sinhagroup.ucsd.edu/) · `src-7da5f97add4fcfac` · observedAt `2026-10-16T04:56:45+00:00` · title: `Allen Lab` · body: `please contact Monica Allen`
- Body SHA256: `35b50cf6304cafc42e6f4ccbd258eaabf7cf130e132d9541eb379740145c97eb`；raw Location headers未另行保存，不能补作重定向证据。
- 原13项逐项对象及日期未改，精确历史文件保存在 `identity-decisions-before-sinha-13.json`。当前共14项错配决策、accepted0；本节模型复核时间 `2026-10-16T05:05:34+00:00`。
