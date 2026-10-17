# Regained root provenance QA

第一阶段审阅时间：2026-10-16T04:08:29+00:00。刷新receipt：04:06:46，queue快照标记04:06:39；本次只核验30条的JSON请求元数据、旧材料保持情况和7个新body的字节SHA-256。

元数据结论：通过，错误0。 30/30 latestFetch与collector原始fetch或保留attemptHistory全字典精确匹配；23条robots_unavailable仅为访问前置检查，未证明page request，不是本任务新live，不计verified。7条新HTTP200 capture的原始时间、实际请求URI、HTTP跳转与响应hash一致。

- 与刷新前Git85b7fbd逐字节/结构比较：30条raw均未改，30个preparedAt均保持；旧sources均为未改动的精确前缀。仅7个ok包各新增1个source，23个precheck包未生成正文来源。
- 13条权威unresolved mismatch接受数保持0；本次没有把相关实体研究或新HTTP200当成身份接受。
- 科研内容model审阅数0：新body只用于字节hash，不解读正文；来源准确并不等于研究摘要正确。等待7条作者结果后，再作有限独立摘要/身份范围复核。

## Thirty metadata results

- 32 / ucsd-lab-from-faculty-sung-lab-eng-ucsd-edu：robots_unavailable；target https://sung-lab.eng.ucsd.edu/；observedAt 2026-10-16T03:49:32+00:00；scope related_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 33 / ucsd-biology-topic-lab-andrew-muroyama：ok；target https://muroyamalab.biosci.ucsd.edu/；observedAt 2026-10-16T03:47:25+00:00；scope listed_url_direct_request；原body SHA-256 2e42414e3523defcf0d2fe402a9e1b401af9c8bfb501dfd83b84a5d4adfb8e04；科研审阅待完成。
- 35 / ucsd-biology-topic-lab-axel-nimmerjahn：ok；target https://www.salk.edu/scientist/axel-nimmerjahn；observedAt 2026-10-16T03:47:25+00:00；scope listed_url_direct_request；原body SHA-256 ec64fa28143f9b2198a0ba1e281a65d2c927dce6242db41755daff52ba000ea8；科研审阅待完成。
- 36 / ucsd-biology-topic-lab-barry-grant：ok；target http://thegrantlab.org/；observedAt 2026-10-16T03:47:24+00:00；scope listed_url_direct_request；原body SHA-256 59dc80ee1c4ddb428edcc6e299d108caab7fb0dc1afa36ad9e595b1036c8dc9f；科研审阅待完成。
- 69 / ucsd-biology-topic-lab-hwa-lab：robots_unavailable；target https://matisse.ucsd.edu/；observedAt 2026-10-16T03:49:19+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 116 / ucsd-biology-topic-lab-roy：ok；target https://roylab.biosci.ucsd.edu/；observedAt 2026-10-16T03:47:25+00:00；scope listed_url_direct_request；原body SHA-256 f0b9a5e7227ede34eba608353888b3b011735d67599f5e76830b37c5aa8ce8d5；科研审阅待完成。
- 117 / ucsd-lab-from-faculty-russell-lab-com：ok；target https://www.russell-lab.com/；observedAt 2026-10-16T03:47:26+00:00；scope listed_url_direct_request；原body SHA-256 d3cf5b1d3c7b7eb8fa3d888748672f702c7ef106074ece36579996a29e73b673；科研审阅待完成。
- 119 / ucsd-biology-topic-lab-saier：ok；target https://saierlab.biosci.ucsd.edu/；observedAt 2026-10-16T03:47:27+00:00；scope listed_url_direct_request；原body SHA-256 8a9f9dbdd9de8075ddcdc43f9c46c49eb7690051fb6f4a0741e9b845272abebf；科研审阅待完成。
- 121 / ucsd-biology-topic-lab-scott-biering：ok；target https://bieringlab.biosci.ucsd.edu/；observedAt 2026-10-16T03:57:30+00:00；scope listed_url_direct_request；原body SHA-256 eb0b7187acc7d3a927b4300f204db61671103e1920e477c0f30196b5e68ddb88；科研审阅待完成。
- 134 / ucsd-biology-topic-lab-traver：robots_unavailable；target https://traverlab.biosci.ucsd.edu/；observedAt 2026-10-16T03:49:49+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 173 / ucsd-lab-from-faculty-web-mac-com-molinski-lab-molinski-lab：robots_unavailable；target http://web.mac.com/molinski_lab/Molinski_Lab；observedAt 2026-10-16T03:49:35+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 197 / ucsd-electrical-and-computer-engineering-lab-statistical-visual-computing-laboratory：robots_unavailable；target https://www.svcl.ucsd.edu/；observedAt 2026-10-16T03:49:20+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 198 / ucsd-electrical-and-computer-engineering-lab-translational-neuroengineering-lab：robots_unavailable；target https://neuro.eng.ucsd.edu/；observedAt 2026-10-16T03:49:00+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 317 / ucsd-pediatrics-lab-barshop-lab：robots_unavailable；target https://biochemgen.ucsd.edu/；observedAt 2026-10-16T03:49:00+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 318 / ucsd-pediatrics-lab-bode-lab：robots_unavailable；target http://www.bodelab.com/；observedAt 2026-10-16T03:54:58+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 323 / ucsd-pediatrics-lab-croker-lab：robots_unavailable；target https://www.crokerlab.com/；observedAt 2026-10-16T03:49:37+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 365 / ucsd-physics-research-site-julio-barreiro：robots_unavailable；target https://barreirolab.ucsd.edu/；observedAt 2026-10-16T03:49:39+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 401 / ucsd-psychiatry-lab-nievergelt-maihofer-psychiatric-genomics-lab：robots_unavailable；target https://nievergeltlab.ucsd.edu/；observedAt 2026-10-16T03:49:22+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 518 / ucsd-live-lab-98174ce75b39b1：robots_unavailable；target https://juchenlab.ucsd.edu/homepage.htm；observedAt 2026-10-16T03:49:45+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 527 / ucsd-live-lab-5c058fcd61d15f：robots_unavailable；target https://genome-tech.ucsd.edu/ZhangLab/；observedAt 2026-10-16T03:49:28+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 574 / ucsd-live-lab-55424aea242e83：robots_unavailable；target https://sicl.ucsd.edu/；observedAt 2026-10-16T03:49:23+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 593 / ucsd-live-lab-11396e2a4edb16：robots_unavailable；target http://dnitz.com/；observedAt 2026-10-16T03:49:45+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 620 / ucsd-live-lab-cd8819aec34b38：robots_unavailable；target https://edithealthsciences.ucsd.edu/som/cmm/research/labs/hamilton/Pages/default.aspx；observedAt 2026-10-16T03:49:45+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 636 / ucsd-live-lab-7c03bec7416f6a：robots_unavailable；target https://ginsberglab.ucsd.edu/；observedAt 2026-10-16T03:49:45+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 643 / ucsd-live-lab-5ead21eb34ab92：robots_unavailable；target http://bryanlabsite.edu/；observedAt 2026-10-16T03:49:45+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 673 / ucsd-live-lab-4de94a86bcdd38：robots_unavailable；target https://nievergelt.ucsd.edu/；observedAt 2026-10-16T03:50:01+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 676 / ucsd-live-lab-c4c7878f997535：robots_unavailable；target http://www.bipolar-aging.com/home；observedAt 2026-10-16T03:49:47+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 709 / ucsd-chemistry-biochemistry-lab-tezcan-lab：robots_unavailable；target https://tezcan.ucsd.edu/；observedAt 2026-10-16T03:49:28+00:00；scope related_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 748 / ucsd-medicine-lab-bazhenov-lab：robots_unavailable；target https://www.bazhlab.ucsd.edu/；observedAt 2026-10-16T03:49:09+00:00；scope listed_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。
- 861 / ucsd-cognitive-science-lab-cognitive-neuroscience-and-neuropsychology-lab：robots_unavailable；target https://sayginlab.ucsd.edu/；observedAt 2026-10-16T03:49:47+00:00；scope related_url_access_precheck_only；requestedUrl=null；无page/new-live/verified。

## Boundaries

- 原collector后续重试可能推进latest；本报告以本次selected metadata及其真实保留attemptHistory为准，不借用更新日期。
- 仅新增本QA Markdown/JSON；没有网络请求、records/packets/projections/collector/shared写入，没有full prepare/checkpoint。
- Phase2 pending：33, 35, 36, 116, 117, 119, 121。

## Phase2 — full scientific and entity-scope review

独立审阅时间：2026-10-16T04:13:24+00:00。这一阶段已实际阅读7个恢复页面的完整科研可见正文，共16534字符；与Phase1仅核验元数据明确区分。原packet文本均等于完整新缓存提取，全部无截断。

结论：7/7通过，无未决内容问题。 7条unresolved→supported的研究摘要、问题、主题、方法及实体范围均获对应正文支持；7条hydrate通过。机构处理为3 uncertain、1 external Salk、3 source_reported；Biering方法留空。

### 33 — Andrew Muroyama Lab

具名Muroyama Lab及We are a group/Our Research明确全组植物细胞与发育范围；位置/器官形成与跨组织物种保守性问题、live-imaging/genetics/proteomics均来自正文。机构uncertain适当，不把UCSD页头/域名当实体局部声明。
已读完整正文563字符。源[src-4c17d2b53a3645c1](https://muroyamalab.biosci.ucsd.edu/)；实际请求https://muroyamalab.biosci.ucsd.edu/；原observedAt 2026-10-16T03:47:25+00:00；SHA-256 2e42414e3523defcf0d2fe402a9e1b401af9c8bfb501dfd83b84a5d4adfb8e04。
实体作用域引文：“Muroyama Lab Welcome! We are a group of cell and developmental biologists who are passionate about understanding how plants create tissues.”

### 35 — Axel Nimmerjahn Lab

虽为官方Salk人物页，但his lab、the team、they created tools及Nimmerjahn’s lab明确实验室作用域。摘要只采用实验室显微镜/染色/遗传操控/数据分析与胶质细胞问题，没有扩张个人既往发现或背景疾病列表。external Salk正确，不接受UCSD隶属或推断任职变动。
已读完整正文4389字符。源[src-f8b1728f4e2e382c](https://www.salk.edu/scientist/axel-nimmerjahn/)；实际请求https://www.salk.edu/scientist/axel-nimmerjahn；原observedAt 2026-10-16T03:47:25+00:00；SHA-256 ec64fa28143f9b2198a0ba1e281a65d2c927dce6242db41755daff52ba000ea8。
实体作用域引文：“To enable cellular-resolution measurements under naturalistic conditions, his lab has worked to shrink the size of microscopes to make them wearable.”

### 36 — Barry Grant Lab

GrantLab/Our research及三个计算研究方法段落明确整体lab范围；分子马达/开关、生物分子模拟、结构生物信息、药物设计和Bio3D均有字面依据。UCSD机构句为实体局部来源声明；localhost HTML canonical未作为实际HTTP终点或新别名。
已读完整正文1964字符。源[src-a53c90d169459382](http://thegrantlab.org/)；实际请求http://thegrantlab.org/；原observedAt 2026-10-16T03:47:24+00:00；SHA-256 59dc80ee1c4ddb428edcc6e299d108caab7fb0dc1afa36ad9e595b1036c8dc9f。
实体作用域引文：“Our research involves the use of computational approaches, based on both biophysics and bioinformatics , to study the structure, function and evolution of key biological macromolecules.”

### 116 — Roy Lab

Kaustuv Roy’s research group at UCSD及research in the lab/We多个项目段落明确组范围。问题与更新世/全新世记录、分子标记、地球化学、表型数据和模拟模型均被正文直接说明。biosci→biology是真实301，不由内容相似推测别名。
已读完整正文5530字符。源[src-ef21a4f6fd81f0a6](https://roylab.biology.ucsd.edu/)；实际请求https://roylab.biosci.ucsd.edu/；原observedAt 2026-10-16T03:47:25+00:00；SHA-256 f0b9a5e7227ede34eba608353888b3b011735d67599f5e76830b37c5aa8ce8d5。
实体作用域引文：“Welcome to Kaustuv Roy’s research group at the University of California San Diego.”

### 117 — Russell Lab

Russell laboratory标题和My lab studies/We use明确实验室整体病毒变异、先天免疫、干扰素和流感研究；四组方法逐字列出。旧个人名录不被用来确认当前PI或实验室机构，affiliation uncertain正确；治疗/候选疫苗只是研究目标。
已读完整正文1096字符。源[src-5e3a018cefd1f8a7](https://www.russell-lab.com/)；实际请求https://www.russell-lab.com/；原observedAt 2026-10-16T03:47:26+00:00；SHA-256 d3cf5b1d3c7b7eb8fa3d888748672f702c7ef106074ece36579996a29e73b673。
实体作用域引文：“My lab studies these rare events that define the subsequent immune response, particularly in the context of an important human pathogen, influenza.”

### 119 — Saier Lab

Saier Lab/Our laboratory/three primary research interests明确全组范围，方法和TCDB创建维护均直接表述。Milton Saier负责人的句子明确，但未以UCSD通用导航推断机构；后部论文新闻未外推为当前全组项目或正文更新时间。
已读完整正文2436字符。源[src-a122b7ee4c4707e9](https://saierlab.biosci.ucsd.edu/)；实际请求https://saierlab.biosci.ucsd.edu/；原observedAt 2026-10-16T03:47:27+00:00；SHA-256 8a9f9dbdd9de8075ddcdc43f9c46c49eb7690051fb6f4a0741e9b845272abebf。
实体作用域引文：“We have three primary research interests, one concerned with transcriptional and metabolic regulation in bacteria, a second with transport protein evolution, and a third with the recently identified process of transposon-mediated directed mutation.”

### 121 — Scott Biering Lab

短正文仍明确Biering Virology Lab、We are a virology research lab及UCSD系院，并直接说明病毒宿主互作/病毒致病机制。methods=[]正确；疫苗/治疗的背景意义未被升级为具体研究对象、项目或方法。
已读完整正文556字符。源[src-7f324059177c4a9a](https://bieringlab.biosci.ucsd.edu/)；实际请求https://bieringlab.biosci.ucsd.edu/；原observedAt 2026-10-16T03:57:30+00:00；SHA-256 eb0b7187acc7d3a927b4300f204db61671103e1920e477c0f30196b5e68ddb88。
实体作用域引文：“We are fascinated by the interactions between viruses and their hosts. We aim to discover the mechanisms that drive viral pathogenesis.”


### Exact evidence repair and retained boundaries

- 33 Muroyama唯一发现的引文覆盖缺口已由父代理补齐：The amazing diversity in plant form that we see around us arises from the collective actions of individual cells. 已独立确认在原src-4c17d2b53a3645c1正文和最终raw evidence中，supports research/topics，实际evidenceCoverageReviewedAt另记，原来源日期不变。
- Nimmerjahn的Salk人物页只有明确his lab/team/they工具与研究问题用于lab摘要；未把个人过往成果、广泛疾病背景或Salk页直接当作UCSD隶属。
- Grant的localhost canonical仅保留为HTML元数据；没有替换实际原请求/终点。Roy的biosci→biology为原捕获真实301；没有由相似正文编造新HTTP重定向。
- Russell与Saier未用个人姓名或UCSD通用导航推定当前lab机构；Biering未从新兴病毒/疫苗背景推导具体病毒或方法。新闻/论文年份没有当作全站研究更新时间。
- 原失败捕获保留历史；新200不是“过去关闭后恢复运营”的证据。两阶段都不变更ID、listed URL或13条权威mismatch接受门槛；接受数仍0。
- Phase1保存的30raw字节未变结论对应刷新当时；本阶段7raw已由作者合法更新，属于后续内容审阅，不是刷新步骤改写。独立QA没有改records/packets/projections/collector/shared，也没有网络请求。
