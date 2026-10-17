# Frame/followup full-body and final-raw review

Reviewed 2026-10-16T05:20:55+00:00. **PASS.** Independently read all4 staged sources (8,694 visible characters), verified original time/URI/hash against actual cache and ledger, and compared the final3 supported raw records after parent evidence completion. All32 current raw evidence quotes are literal; all3 hydrate checks pass. Zero requests and no code/raw/packet/receipt edits by this reviewer.

## Source partition and content boundaries

### `src-0bdc9a2cf67f6aa7` · named_lab_research_body

[http://jenningslab.ucsd.edu/research.html](http://jenningslab.ucsd.edu/research.html); observedAt `2026-10-16T05:16:21+00:00`, liveCheckedAt `2026-10-16T05:16:21+00:00`, SHA256 `43f162576b348d66ad21d6c455a9004810e29fdd3a558d8ba4d91bb6827375c1`. Full ContentDOM body `1851` characters, no truncation; actual followup HTTP200 with no redirects.

Literal Jennings Lab title plus Our/We research prose supports the named lab. Combined experimental/theoretical tools and in-vitro/in-vivo/in-silico contexts are explicit; no NMR or other unstated instrument may be inferred. No dated full-content update or current PI/affiliation statement is established.

### `src-bcab5ff0dfd33434` · named_lab_main_frame_scientific_body

[http://kummelgroup.ucsd.edu/home.htm](http://kummelgroup.ucsd.edu/home.htm); observedAt `2026-10-16T05:16:22+00:00`, liveCheckedAt `2026-10-16T05:16:21+00:00`, SHA256 `77f5e011bf5f28b9d121a9da8fdc8fb4f9f87c0dc9831425532bd8b476589f1c`. Full ContentDOM body `1961` characters, no truncation; actual followup HTTP200 with no redirects.

Main frame directly names Kummel Lab and UC San Diego; research and own primary microelectronics tools are explicit. Liposomal oncolytic-virus coating is a development topic, not validated clinical efficacy. Cancer Researchers in Nanotechnology is separately described training/administrative context. Last updated10/16/2025 is a page update self-report, not a2026 PI/current-project verification.

### `src-3626de29c7f61579` · image_navigation_only_no_research_body

[http://kummelgroup.ucsd.edu/side.htm](http://kummelgroup.ucsd.edu/side.htm); observedAt `2026-10-16T05:16:23+00:00`, liveCheckedAt `2026-10-16T05:16:23+00:00`, SHA256 `69030e3850045ea5aa732347dc0d8c5da32161b985db079cc1af39eb980ebcb0`. Full ContentDOM body `0` characters, no truncation; actual followup HTTP200 with no redirects.

Full ContentDOM text/title are empty. Actual HTML contains image navigation links including research.htm; it is discovery/navigation, not lab research evidence. Basic lab science already appears in home.htm, so no additional research.htm request is needed for this task.

### `src-0de7802df1ac58fb` · named_research_group_body_with_general_field_context

[http://shm.ucsd.edu/Site/Home.html](http://shm.ucsd.edu/Site/Home.html); observedAt `2026-10-16T05:16:24+00:00`, liveCheckedAt `2026-10-16T05:16:23+00:00`, SHA256 `1b4e9cbb73cfab12830a535e4ed0948125ec7987651de148c696e8a7d05a2843`. Full ContentDOM body `4882` characters, no truncation; actual followup HTTP200 with no redirects.

Named SHM laboratory/group and UCSD affiliation are explicit. Group-scoped research is SHM/DP solutions and enabling technologies such as energy harvesting. The sensing/mining/statistical-modeling passage is any-SHM/DP general framework, not evidence that this lab implemented those specific methods. News2013 and award2014 do not date the whole page or establish a2026 director/current personnel.

The Kummel side frame is image navigation only: it has a real research.htm anchor, but no scientific body. It is not cited by the final raw. home.htm already contains the basic whole-lab research and explicit tools; an additional Kummelresearch request is unnecessary.

## Final raw comparison and resolved evidence coverage

### ucsd-chemistry-biochemistry-lab-jennings-lab

Raw scientific reviewedAt `2026-10-16T05:17:49+00:00`; status `supported`; identity `confirmed`/`lab`; affiliation `uncertain`. 12 exact quotes validated. Summary/questions/topics/methods support PASS; no open finding.

Jennings 实验室研究蛋白质折叠与组装如何影响信号传导，探索折叠、误折叠和功能的能量景观。以IL-1β、蛋白激酶、GFP及mitoNEET家族等体系，结合实验与理论研究分子识别、变构调节和活性。

### ucsd-chemistry-biochemistry-lab-kummel-lab

Raw scientific reviewedAt `2026-10-16T05:17:49+00:00`; status `supported`; identity `confirmed`/`lab`; affiliation `source_reported`. 11 exact quotes validated. Summary/questions/topics/methods support PASS; no open finding.

Kummel 实验室标注2025-10-16更新的页面介绍微电子加工化学与抗癌药物包覆，研究薄膜结构和电性能的关系，并开发溶瘤病毒脂质体包覆。方法包括ALD、CVD、双极溅射、原位XPS、TEM及离位电学测量。

### ucsd-structural-engineering-lab-ucsd-structural-health-monitoring-shm-group

Raw scientific reviewedAt `2026-10-16T05:17:49+00:00`; status `supported`; identity `confirmed`/`research_group`; affiliation `source_reported`. 9 exact quotes validated. Summary/questions/topics/methods support PASS; no open finding.

UCSD SHM 研究组的页面介绍结构健康监测与损伤预测：用原位测量评估结构状态，结合未来载荷、失效模式及不确定性预测剩余寿命。研究涵盖智能结构的SHM/DP方案与能量采集等使能技术，并介绍传感、特征提取和统计建模的通用框架。

The parent completed the missing literal coverage during QA: Jennings molecular-biophysics, energy landscape, example systems, recognition/allostery/activity and folding/function unification; Kummel microelectronic/drug-coating and selective-deposition/low-K project sentences; SHM assessment, design function, remaining useful life and risk-informed-decision context. All added quotes were checked against the actual source text. No scientific rewrite was needed for those coverage completions.

SHM's six generic framework quotes now have only general_field_context support and methods is empty. The group's own research quote remains developingSHM/DP solutions and enabling technologies such as energy harvesting. The final summary explicitly labels the general framework, and its uncertainty states no actual group-implemented specific method was established.

## Dates, affiliation and root provenance

Kummel explicitly states `Last updated: 10/16/2025`; the normalized2025-10-16 page update does not establish2026 PI/current-project status. Its main body explicitly places the lab at the University of California, San Diego. Jennings has no full-content update date or entity-local affiliation statement in the new body; current PI/affiliation remains uncertain.

SHM has dated2011–2013 news and a2014 award statement. These are news/award references, not a homepage update date or proof that Mike Todd is director in2026. The source names the SHM laboratory/group and its UCSD structural-engineering department, so source-reported affiliation is supported with the stated time limits.

The actual Jennings root anchor, Kummel side/main frame attributes and SHM literal meta-refresh remain navigation evidence, separately captured from their child-body observations. They were not converted into HTTP redirects or root canonical changes. Hydrated original-root verification remains true for Jennings/Kummel and false for the blank SHM root; the SHM target's group identity does not silently verify its root. The JSON retains source bodies/time/hash, final raw hashes and field-level review results.
