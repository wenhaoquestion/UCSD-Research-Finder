# Cached gap review: inventory records 000–022

Review completed 2026-10-16T03:05:51+00:00 (UTC); model record reviews recorded at 2026-10-16T03:03:28+00:00. Scope: the first 23 inventory records with nonempty candidates, ordinals 6–273. No network requests, collector writes, prepare/checkpoint, aggregate writes, code edits, URL renames, merges or aliases.

23 raw records were individually reviewed and hydrated. Nine have research-content changes: eight became supported; named Kolodner remains partial with provisional laboratory research. Fourteen are semantically unchanged with a new actual review timestamp. Final statuses: {'partial': 6, 'supported': 8, 'unresolved': 9}. Fourteen supplemental source objects were added to nine own-ID packets, with exact original observations/hashes and explicit identityReview.

The 303 inventory relationships contain 129 distinct URL/time/hash captures across 128 URLs. All cached bytes were hash-checked and all 129 original observation/hash tuples independently matched collection queue or existing gap-result metadata. ContentDOM/decode_cached_html was used; titles, explicit named subjects and localized entity references were checked for every candidate. Relevant potentially matching pages were read in full; other named persons/labs were excluded by their actual page subjects, never promoted from navigation/co-author/similar-person links. The extra cached pages below are existing captures, not observations made by this review.

All 13 reviewed mismatches remain nonaccepted. The two owned reviewed mismatches (named Kolodner and Malinow) remain partial with their previous acceptance states. No identity-decisions JSON/Markdown was written. Source-reported affiliation is distinct from a dated current affiliation claim; missing current-date confirmation remains explicit.

## Individual decisions

### 000. Ordinal 6: Patel lab
`ucsd-anesthesiology-lab-patel-lab` — partial → partial

**保留 partial。** 目的成员页只列 Hemal Patel 等成员。候选 Head、Shubayev、Yaksh 是其他具名实验室；Mandyam、Meier、Zemljic-Harpf Profiles 是其他个人。Our Research Faculty 中 Hemal Patel 段确实有 Patel Lab 锚点，但研究句写其个人专业与过往应用，没有明确的实验室整体研究计划，故不升级或把其他实验室的方法移入。额外读取同站根页（原观测 2026-10-16T02:39:59+00:00），标题虽为 Cardiac & Neuro Protection Laboratories，正文却是 Études 建筑模板（“A passion for creating spaces”），不能提供研究支持。

Inventory candidate decisions: C001, C002, C003, C004, C005, C006, C007. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

### 001. Ordinal 7: Shubayev Lab
`ucsd-anesthesiology-lab-shubayev-lab` — unresolved → supported

**unresolved → supported。** 官方 Basic Research 目录实际 HTML 的 Shubayev Lab 锚点指向专属 Shubayev Research Laboratory 缓存页；正文明确负责人 Veronica Shubayev 和“At the Shubayev Lab, we explore interactions between the immune and nervous systems.” 可以概括免疫—神经相互作用、外周再生与疼痛、细胞外基质和神经屏障。正文没有明确实验方法，methods 保持空。只将专属实验室页作为研究证据；其他候选各属其他团队，Faculty 总览虽有 Veronica 段但不需要用于代替更明确的实验室页。旧 shubayev-lab URL 的404检查保持。

Inventory candidate decisions: C001, C002, C003, C004, C005, C006, C007. C002 is used for this Shubayev record; all remaining references are rejected as replacement research for this entity.

- Reused [Shubayev Research Laboratory](https://anesthesia.ucsd.edu/research/basic-science/shubayev-research-laboratory/index.html), original observedAt `2026-10-16T01:03:13+00:00`, sourceId `src-bc4d28835d54a851`; body SHA-256 `fd70f54a0cd24c20d8038b445236d30e80e9641f720feeeda53f53598a5d1f3a`.

### 002. Ordinal 150: Esko Lab
`ucsd-cellular-molecular-medicine-lab-esko-lab` — unresolved → unresolved

**保留 unresolved。** CMM 五个候选分别是 Don Cleveland、Susan Ferro-Novick、Ghosh、Hamilton、Ajit Varki 的页面，均不提供 Esko 实验室研究。官方 CMM 目录仍有 Esko Lab，历史 Jeffrey Esko 档案仍有实验室链接；它们仅支持身份关联。没有可用 Esko 研究正文，原 robots 不可用不等于实验室关闭。

Inventory candidate decisions: C008, C009, C010, C011, C012. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

### 003. Ordinal 155: Kolodner Lab
`ucsd-cellular-molecular-medicine-lab-kolodner-lab` — partial → partial

**保留 partial / mismatch / provisional_historical_lab。** 五个 CMM 候选不是 Kolodner 研究。额外复读已取得的 Richard Kolodner 官方 Profiles 完整缓存（原观测 2026-10-16T02:22:30+00:00），其“Our laboratory”和“The Kolodner lab”明确支持 DNA 修复、重组、突变/染色体重排抑制、癌症易感性和酿酒酵母模型。只补充暂定的具名实验室研究；原 Ludwig 具名路径落至机构主页的错配不变，不使用 Ludwig 总站癌症方向，也不接受新 URL、别名或与生成 Kolodner ID 合并。本 ID 未发生新请求，另一 ID 的现场检查时间不归为此 ID 的目的页重查。identity-decisions 文件未改；其原身份结论仍有效，研究内容补充另见 raw。

Inventory candidate decisions: C008, C009, C010, C011, C012. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

- Reused [Richard Kolodner | UCSD Profiles](https://profiles.ucsd.edu/richard.kolodner), original observedAt `2026-10-16T02:22:30+00:00`, sourceId `src-8b07c4927ae2b0ce`; body SHA-256 `6f6931e3f32295747c6602877e338475536144ee9ef01752f2c44afe690a70af`.

### 004. Ordinal 157: Muotri Lab
`ucsd-cellular-molecular-medicine-lab-muotri-lab` — unresolved → supported

**unresolved → supported。** 本记录的直接候选五个 CMM 页面均属其他实验室。跨本批已审缓存发现 UCSD Pediatrics 的 Muotri Lab 专页：标题、Alysson R. Muotri 全名、Pediatrics/CMM 单位和具名 Muotri lab 研究相符。全文支持大脑演化/发育、自闭症与社会脑研究，明确人多能干细胞、脑类器官、培养组织药物测试及基因组编辑。该页在 Sander 的目录候选中被发现，但研究只归 Muotri 稳定 ID；旧 Pediatrics 404 保留，未自动采纳新网址。

Inventory candidate decisions: C008, C009, C010, C011, C012. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

- Reused [Muotri Lab](https://pediatrics.ucsd.edu/research/faculty-labs/muotri-lab/index.html), original observedAt `2026-10-16T01:02:59+00:00`, sourceId `src-15d953271be72e2f`; body SHA-256 `34b63f3346ae6bc675f64539f15c0775ea36e1d7415f450f37ac9f412c3191ec`.

### 005. Ordinal 158: Novick Lab
`ucsd-cellular-molecular-medicine-lab-novick-lab` — unresolved → unresolved

**保留 unresolved。** 关键排除：Ferro-Novick 页面明确负责人 Susan Ferro-Novick；实际 CMM 目录将 Novick Lab 链到 faculty_detail?f=245，将 Ferro-Novick Lab 另链 ferro-novick/index.html。两个条目并列，缺少同一实体关系，不可用 ER-phagy 研究补给 Novick。其余 Cleveland、Ghosh、Hamilton、Varki 也属其他实验室。

Inventory candidate decisions: C008, C009, C010, C011, C012. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

### 006. Ordinal 160: Reck-Peterson Lab
`ucsd-cellular-molecular-medicine-lab-reck-peterson-lab` — unresolved → unresolved

**保留 unresolved。** 五个 CMM 缓存页各有其他具名研究主体，未见 Reck-Peterson lab 的研究说明。现存 CMM 目录条目只支持身份线索；原目的站 robots 不可用保留，不推断关闭。

Inventory candidate decisions: C008, C009, C010, C011, C012. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

### 007. Ordinal 161: Sander Lab
`ucsd-cellular-molecular-medicine-lab-sander-lab` — unresolved → unresolved

**保留 unresolved。** 五个 CMM 和二十一个 Pediatrics/Profiles 捕获全部排除为 Sander 研究：页面分别标识其他实验室；Jianhua Shao 页面是个人课题，不是 Maike Sander 的实验室。两份 Spector 捕获为同一正文但保留各自原日期。Muotri 专页仅移用到本批 Muotri ID，不给 Sander。Pediatrics 目录未给出 Sander 研究正文，旧 msanderlab.org robots 不可用保持。

Inventory candidate decisions: C008, C009, C010, C011, C012, C013, C014, C015, C016, C017, C018, C019, C020, C021, C022, C023, C024, C025, C026, C027, C028, C029, C030, C031, C032, C033. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

### 008. Ordinal 191: Mesirov Lab
`ucsd-lab-from-faculty-healthsciences-ucsd-edu-som-medicine-divisions-med-genetics-research-pages-mesirov-lab-aspx` — unresolved → supported

**unresolved → supported。** 八个目录锚点候选都是其他个人。额外发现 GPM 的 Jill Mesirov Laboratory 官方缓存，明确“Research in the Mesirov lab”并在 HTML 链到 mesirovlab.org；该第一方站首页、Contact 完整标识 Jill P. Mesirov 和实验室，支持癌症基因组学、机器学习/统计、肿瘤分层与软件开发。第一方联系页报告 Sanford Burnham Prebys 实验室地址，故 affiliation 记 external 来源声明，同时明确 UCSD 页任职与之不同、无带日期的当前隶属确认、不推断迁移时间。旧 Healthsciences URL 和 robots 不可用观察不变。

Inventory candidate decisions: C034, C035, C036, C037, C038, C039, C040, C041. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

- Reused [Jill Mesirov Laboratory](https://gpm.ucsd.edu/research/mesirov/index.html), original observedAt `2026-10-16T01:05:02+00:00`, sourceId `src-a296f660787a5adf`; body SHA-256 `ee9aea0ec444fd71a413d1251f73b2343577257ebb7ee41ae0c07584744d8a06`.
- Reused [Home | Mesirov Lab](https://mesirovlab.org/), original observedAt `2026-10-16T01:36:57+00:00`, sourceId `src-412ac09ced37b8ce`; body SHA-256 `344fdf407b32579d19e3bfbe015394f82ee3a03c3e64f2816543338ae4bc875c`.
- Reused [Contact | Mesirov Lab](https://mesirovlab.org/about/), original observedAt `2026-10-16T02:43:07+00:00`, sourceId `src-000f31c75a1d2e7a`; body SHA-256 `86d14a0b84f48ce1f299e1978460a0e1a92228812cf51edcb709a7d6ec15acfd`.

### 009. Ordinal 220: Aceves Lab
`ucsd-lab-from-faculty-raidivision-ucsd-edu-research-aceves-lab-pages-default-aspx` — unresolved → supported

**unresolved → supported。** 64个候选的主体是其他教师，Profiles 的共同作者/相似人物列表出现 Aceves 仅是关系导航（如 Jackson Vane、Andrew Dickerson），不能转成实验室研究。额外读取 UCSD Allergy/Immunology 的 Aceves 首页与 About；Seema S. Aceves 全名与历史来源匹配，正文“The Aceves lab conducts…”和“The Aceves Lab uses…”明确支持 EoE 组织重塑与原代人食管细胞/组织体外模型。旧 raidivision URL 检查保留。

Inventory candidate decisions: C034, C035, C036, C037, C038, C039, C040, C041, C042, C043, C044, C045, C046, C047, C048, C049, C050, C051, C052, C053, C054, C055, C033, C056, C057, C058, C059, C060, C061, C062, C063, C064, C065, C066, C067, C068, C069, C070, C071, C072, C073, C074, C075, C076, C077, C078, C079, C080, C081, C082, C083, C084, C085, C086, C087, C088, C089, C090, C091, C092, C093, C094, C095, C096. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

- Reused [Aceves Lab](https://allergyimmunology.ucsd.edu/research/faculty-labs/aceves/index.html), original observedAt `2026-10-16T01:03:04+00:00`, sourceId `src-cc5c90fb3544de4e`; body SHA-256 `7ad30306f770fde7672e64f8a5a959a30f62f9492f915265b6d0176c2dc78f50`.
- Reused [About](https://allergyimmunology.ucsd.edu/research/faculty-labs/aceves/about/index.html), original observedAt `2026-10-16T01:03:43+00:00`, sourceId `src-fdbda7b32a186cc6`; body SHA-256 `5e4ba1f8a0b0c43ae24feb392c4ebbcf091b94742a324f81f82bacd82bc71f5b`.

### 010. Ordinal 221: Mary P. Corr — lab website
`ucsd-lab-from-faculty-raidivision-ucsd-edu-research-corr-lab-pages-default-aspx` — unresolved → unresolved

**保留 unresolved。** 八个候选分别为 Chris Longhurst、Elliot McVeigh、Cristina Llorente、Christina Schultz、James Templeman、Steffanie Strathdee、Trey Ideker、Alison Potok 的 Profiles，均不是 Mary P. Corr 或 Corr lab。完整 Medicine 教师目录有 Corr 个人条目但无其实验室研究；不能以同系其他研究补齐。旧 robots 不可用保持。

Inventory candidate decisions: C034, C035, C036, C037, C038, C039, C040, C041. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

### 011. Ordinal 222: Doherty Lab
`ucsd-lab-from-faculty-raidivision-ucsd-edu-research-doherty-lab-pages-default-aspx` — unresolved → supported

**unresolved → supported。** 八个目录候选均是其他个人，不能当 Doherty lab 研究。额外读取 UCSD Allergy/Immunology 的 Doherty 首页与 About，完整 Taylor A. Doherty 与原记录匹配，正文“The Doherty lab”明确肺部固有2型反应、哮喘/过敏性气道疾病、ILC2，并明确动物模型和人类样本。摘要/方法不使用论文标题或仅历史初期目标推断当前技术。旧 raidivision robots 检查保持。

Inventory candidate decisions: C034, C035, C036, C037, C038, C039, C040, C041. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

- Reused [Doherty Lab](https://allergyimmunology.ucsd.edu/research/faculty-labs/doherty/index.html), original observedAt `2026-10-16T01:03:44+00:00`, sourceId `src-cbe150d50c61e87d`; body SHA-256 `0d288d276a602d27fa790d28dc8ed9977b3cab0d5006b910a744a5c4a4ebe741`.
- Reused [About](https://allergyimmunology.ucsd.edu/research/faculty-labs/doherty/about/index.html), original observedAt `2026-10-16T01:03:51+00:00`, sourceId `src-31feb76373ba0ad9`; body SHA-256 `fa646d15e62008bd196b06b6accd1f0b3fe7a2ec8abafc4479b91bcb724e34da`.

### 012. Ordinal 223: Firestein Lab
`ucsd-lab-from-faculty-raidivision-ucsd-edu-research-firestein-lab-pages-default-aspx` — partial → partial

**保留 partial。** 八个候选均属其他个人。Gary Firestein 的现有历史个人简介只支持类风湿关节炎的负责人研究兴趣；没有新增明确 Firestein lab 范围的研究正文。完整教师目录的个人/单位条目也不能替代实验室计划。

Inventory candidate decisions: C034, C035, C036, C037, C038, C039, C040, C041. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

### 013. Ordinal 224: Furnari Lab
`ucsd-lab-from-faculty-regenmed-ucsd-edu-research-furnari-lab` — unresolved → supported

**unresolved → supported。** 八个目录候选均是其他个人；完整 Medicine 目录有 Frank Furnari / Regenerative Medicine，但目录本身不提供 lab 研究。额外读取第一方 Furnari Laboratory 首页及团队页，后者明确 Principal Investigator Frank Furnari、UCSD Medicine/Division of Regenerative Medicine 和“My lab’s research program”，与原记录完整PI和具体单位一致。可使用实验室整体的恶性脑肿瘤/GBM、异质性/治疗耐受，以及患者来源和基因工程 iPSC 来源模型。没有把成员此前其他实验室经历或论文目录当本 lab 方法。旧 regenmed 404 不变，新站不自动成为已接受规范 URL。

Inventory candidate decisions: C034, C035, C036, C037, C038, C039, C040, C041. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

- Reused [Home | Furnari Lab](https://www.furnarilab.com/), original observedAt `2026-10-16T01:07:14+00:00`, sourceId `src-9124efef4641f0bd`; body SHA-256 `d3254f3855dd634243dfaef43393a0b9fddbdacb4304b1369a387c765a7e670a`.
- Reused [Team | Furnari Lab](https://www.furnarilab.com/team-1), original observedAt `2026-10-16T01:35:24+00:00`, sourceId `src-0e55c06f66ce0108`; body SHA-256 `c031b890e2505d75761f17965589adaf3bae940619271198f49996eb366d28e6`.

### 014. Ordinal 227: Jamieson Lab
`ucsd-lab-from-faculty-medschool-ucsd-edu-som-medicine-divisions-regenmed-research-jamieson-lab-pages-default-aspx` — partial → partial

**保留 partial。** 八个目录候选均属其他个人。额外核查现成 Urology Jamieson 缓存：其首页明确负责人 **Christina Jamieson**，不是此记录的 **Catriona H.M. Jamieson**；因此全部拒用其骨转移前列腺癌、PDX和3D模型。现有 Catriona 个人突变干细胞研究仍限负责人范围，不能借同姓实验室升为 supported。

Inventory candidate decisions: C034, C035, C036, C037, C038, C039, C040, C041. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

### 015. Ordinal 233: Schnabl Lab
`ucsd-lab-from-faculty-gastro-ucsd-edu-schnabl-lab` — unresolved → unresolved

**保留 unresolved。** 八个候选均属其他个人；尤其 Cristina Llorente 页面不能因研究领域接近或共同作者而转作 Bernd Schnabl lab 计划。完整 Medicine 目录只列 Schnabl 个人/单位，未补出实验室研究。旧 gastro 目的网址 robots 不可用保持。

Inventory candidate decisions: C034, C035, C036, C037, C038, C039, C040, C041. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

### 016. Ordinal 243: Cleveland Lab – Ludwig Cancer Research
`ucsd-neurosciences-lab-cleveland-lab` — unresolved → supported

**unresolved → supported。** 17个 Neurosciences 候选均为其他实验室。额外使用已审 CMM 的 Don Cleveland Lab 缓存：原记录旧路径含 donclevelandlab，专页明确 Don W. Cleveland、About the Lab、Ludwig Institute 联系地址，匹配同一具名主体。只写其明确的两大方向：癌症基因组重排、人类神经退行性疾病机制与治疗。未从 Qalsody 获批新闻推断实验方法；methods 为空。旧404与URL不变。

Inventory candidate decisions: C097, C098, C099, C100, C101, C102, C103, C104, C105, C106, C107, C108, C109, C110, C111, C112, C113. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

- Reused [Don Cleveland Lab](https://cmm.ucsd.edu/research/labs/don-cleveland/index.html), original observedAt `2026-10-16T01:04:46+00:00`, sourceId `src-6a283252e0fbe413`; body SHA-256 `8150f497fb2345f2d2430457dbbfcb6abef5864a6785fe2760f5980c14930310`.

### 017. Ordinal 248: Ellisman Lab – Center for Research in Biological Systems (CRBS)
`ucsd-neurosciences-lab-ellisman-lab` — unresolved → unresolved

**保留 unresolved。** 17个 Neurosciences 候选分别为 Brewer、Campbell、Neurovascular Imaging、Dore、Gholipour、Gleeson、Graves、Hnasko、Kim-McManus、Mobley、Raju、Autism & Development、Ung、Zheng、Reas、Banks、Looger，没有 Ellisman/CRBS 专属研究。历史 Ellisman Lab–CRBS 名称不授权把中心或其他团队的研究借来；CRBS robots/TLS失败只反映访问问题。

Inventory candidate decisions: C097, C098, C099, C100, C101, C102, C103, C104, C105, C106, C107, C108, C109, C110, C111, C112, C113. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

### 018. Ordinal 253: Komiyama Lab – a systems neuroscience laboratory
`ucsd-neurosciences-lab-komiyama-lab` — partial → supported

**partial → supported。** 17个目录候选均是其他团队。另查同站已缓存 /home/，标题和正文明确 Komiyama Lab，正文直接列出神经元群体/行为、经验、学习、记忆及疾病的问题，以及行为、遗传、成像和电生理技术。根页空白原观察保持，不将 /home/ 作为新观察或已采纳别名。

Inventory candidate decisions: C097, C098, C099, C100, C101, C102, C103, C104, C105, C106, C107, C108, C109, C110, C111, C112, C113. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

- Reused [Home | Komiyama Lab](https://komiyamalab.biosci.ucsd.edu/home/), original observedAt `2026-10-16T02:40:05+00:00`, sourceId `src-ed1a3b9e0c08c68e`; body SHA-256 `2f2fd496e3de1dc27a23b8efe239bddf551740d7c31d42cc4a011ef3734313e9`.

### 019. Ordinal 255: Malinow Lab – Center for Neural Circuits & Behavior (CNCB)
`ucsd-neurosciences-lab-malinow-lab` — partial → partial

**保留 partial / mismatch / provisional_historical_lab。** 17个候选都属其他团队，没有 Malinow 研究。官方目录保留旧 WebAxon 链接；既有域名出售错配继续单列。不得以其他 CNCB/Neurosciences 小组的研究修复身份或推断关闭。

Inventory candidate decisions: C097, C098, C099, C100, C101, C102, C103, C104, C105, C106, C107, C108, C109, C110, C111, C112, C113. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

### 020. Ordinal 259: Rich Lab
`ucsd-neurosciences-lab-rich-lab` — unresolved → unresolved

**保留 unresolved。** 17个候选均非 Rich lab，目录中的邻近神经科学研究不能归给该ID。原 Rich 具名目的网址404与历史身份线索保持；没有把 Furnari/其他脑肿瘤研究移入。

Inventory candidate decisions: C097, C098, C099, C100, C101, C102, C103, C104, C105, C106, C107, C108, C109, C110, C111, C112, C113. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

### 021. Ordinal 266: Wu Lab
`ucsd-neurosciences-lab-wu-lab` — unresolved → unresolved

**保留 unresolved。** 17个候选均非 Wu lab，未发现解释其研究的具名正文。旧 Weebly robots denied 保留，不绕过限制、不由邻近团队推断研究或关闭。

Inventory candidate decisions: C097, C098, C099, C100, C101, C102, C103, C104, C105, C106, C107, C108, C109, C110, C111, C112, C113. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

### 022. Ordinal 273: Jacobs Lab
`ucsd-obstetrics-gynecology-reproductive-sciences-lab-jacobs-lab` — partial → partial

**保留 partial / unconfirmed。** 16个候选分别是其他教师或具名实验室，均不确认独立 Jacobs Lab。额外检查完整 Clinical Studies（36592字符）后，Marni Jacobs 仅在某项研究的 Collaborators 中列为 MPI；这证明其项目参与，不能把全系临床试验或项目团队改作 Jacobs lab。现有 Research Labs 目录的 Marni 个人兴趣范围保持，不把生殖/妊娠领域相近的其他实验室研究移入。

Inventory candidate decisions: C114, C115, C116, C117, C118, C119, C120, C121, C122, C123, C124, C125, C126, C127, C128, C129. All listed references are rejected as replacement research for this entity; separately identified same-entity cached sources, where any, are documented above and below.

## Supplemental evidence and observation boundaries

Every source below has role `reviewed_cached_followup_requires_entity_match`, a deterministic sourceId, and an explicit identityReview. Its observation, hash and content are the original capture. Supplementation does not change listedWebsite, latestDestinationFetch, attempt history, redirects, preparedAt, or identity-followup request accounting. Named Kolodner retains the original cached `summary_gap_live_fetch` provenance; this review makes zero new requests.

| Inventory row | Source | Original observedAt | SourceId |
|---|---|---|---|
| 001 | [Shubayev Research Laboratory](https://anesthesia.ucsd.edu/research/basic-science/shubayev-research-laboratory/index.html) | 2026-10-16T01:03:13+00:00 | `src-bc4d28835d54a851` |
| 003 | [Richard Kolodner | UCSD Profiles](https://profiles.ucsd.edu/richard.kolodner) | 2026-10-16T02:22:30+00:00 | `src-8b07c4927ae2b0ce` |
| 004 | [Muotri Lab](https://pediatrics.ucsd.edu/research/faculty-labs/muotri-lab/index.html) | 2026-10-16T01:02:59+00:00 | `src-15d953271be72e2f` |
| 008 | [Jill Mesirov Laboratory](https://gpm.ucsd.edu/research/mesirov/index.html) | 2026-10-16T01:05:02+00:00 | `src-a296f660787a5adf` |
| 008 | [Home | Mesirov Lab](https://mesirovlab.org/) | 2026-10-16T01:36:57+00:00 | `src-412ac09ced37b8ce` |
| 008 | [Contact | Mesirov Lab](https://mesirovlab.org/about/) | 2026-10-16T02:43:07+00:00 | `src-000f31c75a1d2e7a` |
| 009 | [Aceves Lab](https://allergyimmunology.ucsd.edu/research/faculty-labs/aceves/index.html) | 2026-10-16T01:03:04+00:00 | `src-cc5c90fb3544de4e` |
| 009 | [About](https://allergyimmunology.ucsd.edu/research/faculty-labs/aceves/about/index.html) | 2026-10-16T01:03:43+00:00 | `src-fdbda7b32a186cc6` |
| 011 | [Doherty Lab](https://allergyimmunology.ucsd.edu/research/faculty-labs/doherty/index.html) | 2026-10-16T01:03:44+00:00 | `src-cbe150d50c61e87d` |
| 011 | [About](https://allergyimmunology.ucsd.edu/research/faculty-labs/doherty/about/index.html) | 2026-10-16T01:03:51+00:00 | `src-31feb76373ba0ad9` |
| 013 | [Home | Furnari Lab](https://www.furnarilab.com/) | 2026-10-16T01:07:14+00:00 | `src-9124efef4641f0bd` |
| 013 | [Team | Furnari Lab](https://www.furnarilab.com/team-1) | 2026-10-16T01:35:24+00:00 | `src-0e55c06f66ce0108` |
| 016 | [Don Cleveland Lab](https://cmm.ucsd.edu/research/labs/don-cleveland/index.html) | 2026-10-16T01:04:46+00:00 | `src-6a283252e0fbe413` |
| 018 | [Home | Komiyama Lab](https://komiyamalab.biosci.ucsd.edu/home/) | 2026-10-16T02:40:05+00:00 | `src-ed1a3b9e0c08c68e` |

## Rejected-candidate capture catalogue

References in the individual decisions resolve to this table. Titles are read from the actual decoded cached HTML, not guessed from URL paths. Body digests are verified against bytes and original queue/gap metadata; two Spector observations are preserved separately even though the body is identical. A page may be rejected for one entity and used for its explicitly named entity elsewhere (notably Shubayev, Muotri and Don Cleveland).

| Ref | Actual page title / official source URL | Original observedAt (UTC) | Main text characters | Body SHA-256 |
|---|---|---|---:|---|
| C001 | [Brian Head Lab](https://anesthesia.ucsd.edu/research/basic-science/head-lab/index.html) | 2026-10-16T00:57:38+00:00 | 5617 | `6a378464a4ca413b818652f9a007f20ae4ab73b33d32e5e8b1d3ebd1f35c081b` |
| C002 | [Shubayev Research Laboratory](https://anesthesia.ucsd.edu/research/basic-science/shubayev-research-laboratory/index.html) | 2026-10-16T01:03:13+00:00 | 1896 | `fd70f54a0cd24c20d8038b445236d30e80e9641f720feeeda53f53598a5d1f3a` |
| C003 | [Anesthesiology Research Laboratory (ARL)](https://anesthesia.ucsd.edu/research/basic-science/yaksh-lab/index.html) | 2026-10-16T00:57:40+00:00 | 5442 | `c060bf467e2e2f1412920415cc8390c288a0a79a3f1d5fbd8bfccc1b62e90686` |
| C004 | [Our Research Faculty](https://anesthesia.ucsd.edu/research/basic-science/basic-research-faculty/index.html) | 2026-10-16T00:59:08+00:00 | 15851 | `3db60d81d3e5e2558b041cc9f2e7b6b2a3795b00c11be6cd80e079a9e00768f2` |
| C005 | [Chitra Mandyam / UCSD Profiles](https://profiles.ucsd.edu/chitra.mandyam) | 2026-10-16T01:02:09+00:00 | 2146 | `407e8aa251ea3ff6f257ace898fc264532d3f109af1eb3cf9472941b5166694f` |
| C006 | [Angela Meier / UCSD Profiles](https://profiles.ucsd.edu/angela.meier) | 2026-10-16T01:02:19+00:00 | 1238 | `98e5f5b9755476a1d86ccc2aa81d9cf1d157922d8c4161bc2d5b294fcba8cf11` |
| C007 | [Alice Zemljic-harpf / UCSD Profiles](https://profiles.ucsd.edu/alice.zemljic-harpf) | 2026-10-16T01:02:29+00:00 | 1444 | `8805e075d34f4c650d3dd9dc2fb272e3e31849a0d53637d569cee9fd2333d6b3` |
| C008 | [Don Cleveland Lab](https://cmm.ucsd.edu/research/labs/don-cleveland/index.html) | 2026-10-16T01:04:46+00:00 | 784 | `8150f497fb2345f2d2430457dbbfcb6abef5864a6785fe2760f5980c14930310` |
| C009 | [Ferro-Novick Lab](https://cmm.ucsd.edu/research/labs/ferro-novick/index.html) | 2026-10-16T01:04:48+00:00 | 2670 | `86a5a89c76d7d3a365d3cf37fc2a49d14fceeb51baecf41f092b724a46fd303c` |
| C010 | [Ghosh Lab](https://cmm.ucsd.edu/research/labs/ghosh/index.html) | 2026-10-16T01:04:49+00:00 | 5422 | `f3072186d92d2255d824cb803975f046aa2d118346f5fb2e72f416fe69514922` |
| C011 | [Hamilton Lab](https://cmm.ucsd.edu/research/labs/hamilton/index.html) | 2026-10-16T01:02:45+00:00 | 2496 | `5d0fea4ff21fa3d5c39a79b72dc3279d3f11ad34cb7322c28a39344c62ea52ad` |
| C012 | [Ajit Varki](https://cmm.ucsd.edu/research/labs/varki/index.html) | 2026-10-16T01:04:50+00:00 | 3430 | `57d74d2c724b60b8fe27f3e99b9edfdc9dae29b9b475b70d65141762cab2ac5e` |
| C013 | [Grossfeld Lab](https://pediatrics.ucsd.edu/research/faculty-labs/grossfeld-lab/index.html) | 2026-10-16T01:02:55+00:00 | 1120 | `e8de2f6d3e743686b1d53425a8d7379d268a501fb9210cb83919a7fa25bd5e6a` |
| C014 | [Feldstein Lab](https://pediatrics.ucsd.edu/research/faculty-labs/feldstein-lab/index.html) | 2026-10-16T01:02:54+00:00 | 811 | `44f24c67cbd5688b125236fbc9c7ecd1db9a7cab05a2537bcd54706b64eded3c` |
| C015 | [Schwimmer Lab](https://pediatrics.ucsd.edu/research/faculty-labs/schwimmer-lab/index.html) | 2026-10-16T01:03:05+00:00 | 1783 | `f8836669cd09100264eb74164bd11ceed63f49a70354f9a7a8aa6d8c9c9fdc5e` |
| C016 | [Briganti Lab](https://pediatrics.ucsd.edu/research/faculty-labs/briganti-lab/index.html) | 2026-10-16T01:02:50+00:00 | 820 | `c03aa704376acc1ca4c167fe8f2fbc3b445bb594a0a15766f8fe57df4fefb8ba` |
| C017 | [Cherqui Lab](https://pediatrics.ucsd.edu/research/faculty-labs/cherqui-lab/index.html) | 2026-10-16T01:02:52+00:00 | 1022 | `a44596290ec31cab88eda059054d97bc2ce5493571c385292edd6dce1b410395` |
| C018 | [Muotri Lab](https://pediatrics.ucsd.edu/research/faculty-labs/muotri-lab/index.html) | 2026-10-16T01:02:59+00:00 | 5162 | `34b63f3346ae6bc675f64539f15c0775ea36e1d7415f450f37ac9f412c3191ec` |
| C019 | [Joshi Lab](https://pediatrics.ucsd.edu/research/faculty-labs/joshi-lab/index.html) | 2026-10-16T01:03:25+00:00 | 2862 | `8f219ecd5f43378412c77f362ae5943804cb8f533ed596822701e1a8d332d17e` |
| C020 | [Zage Lab](https://pediatrics.ucsd.edu/research/faculty-labs/zage-lab/index.html) | 2026-10-16T01:03:08+00:00 | 882 | `ac1421369c25de3cdedd38d4a4ceb40632011906fbd4d4ce3918ccc0c5ca064b` |
| C021 | [Nizet Lab](https://pediatrics.ucsd.edu/research/faculty-labs/nizet-lab/index.html) | 2026-10-16T01:03:02+00:00 | 1722 | `962b5363db445ab8bca5543a0f35556073189b0764723b799bbb707201cccc51` |
| C022 | [Rivera-Chavez Lab](https://pediatrics.ucsd.edu/research/faculty-labs/rivera-chavez-lab/index.html) | 2026-10-16T01:03:04+00:00 | 4540 | `685873ce1fa98ac3eef7d01212d07eb4195090dc9ad26561349646c2dbd7ad9d` |
| C023 | [Liu Lab](https://pediatrics.ucsd.edu/research/faculty-labs/liu-lab/index.html) | 2026-10-16T01:02:58+00:00 | 710 | `81c5eace8d16cb9ba624981598a467710b3481c7b27b8feca21afc45b579ce79` |
| C024 | [Spector Lab](https://pediatrics.ucsd.edu/research/faculty-labs/spector-lab/index.html) | 2026-10-16T01:03:06+00:00 | 1670 | `d8d8933e7e38127fa191703f9b8469effba41f1870a73c5ff1c1776e35fd4c8f` |
| C025 | [Spector Lab](https://pediatrics.ucsd.edu/research/faculty-labs/spector-lab/index.html) | 2026-10-16T01:34:17+00:00 | 1670 | `d8d8933e7e38127fa191703f9b8469effba41f1870a73c5ff1c1776e35fd4c8f` |
| C026 | [Leibel Lab](https://pediatrics.ucsd.edu/research/faculty-labs/leibel-lab/index.html) | 2026-10-16T01:02:57+00:00 | 778 | `e50510cf9781fb3a7bd1b5707d4a79bd1da399df4da34cee64e76329adf8fa41` |
| C027 | [Neonatal Health Services Research Lab](https://pediatrics.ucsd.edu/research/faculty-labs/neo-hsr-lab/index.html) | 2026-10-16T01:03:00+00:00 | 816 | `87d91c4ba36c38bbc8d83115a37fdac8a5c9b0c1e9f6098a50088ce55e8b68bd` |
| C028 | [Nigam Lab](https://pediatrics.ucsd.edu/research/faculty-labs/nigam-lab/index.html) | 2026-10-16T01:03:01+00:00 | 1853 | `f1a0926b7ea38c95792c1b01d616dd0de25f63c92c1ec6d85adabd06a2c209e9` |
| C029 | [Haddad Lab](https://pediatrics.ucsd.edu/research/faculty-labs/haddad-lab/index.html) | 2026-10-16T01:02:56+00:00 | 1238 | `3eda204dcc86ddd9859286d6155eec3e93cd5e933706e43606931374b16d0202` |
| C030 | [Quinton Lab](https://pediatrics.ucsd.edu/research/faculty-labs/quinton-lab/index.html) | 2026-10-16T01:03:03+00:00 | 1283 | `7dcd0687380dacd354829669e5993fb7d1cb036189a5ce613e8cd7825a202c3c` |
| C031 | [Pediatric Pharmacology Laboratory (PPL)](https://pediatrics.ucsd.edu/research/faculty-labs/pediatric-pharmacology-laboratory/index.html) | 2026-10-16T01:05:20+00:00 | 3401 | `bdf0c32493e02996744257ea112eac685bf21430278106fbc6e73ffd794809bb` |
| C032 | [Sajti Lab](https://pediatrics.ucsd.edu/research/faculty-labs/sajti-lab/index.html) | 2026-10-16T01:05:22+00:00 | 2952 | `778377a607cbcb0fca5c021f3bb97303ae48c371085a05f5ab13ce6b289dad1f` |
| C033 | [Jianhua Shao / UCSD Profiles](https://profiles.ucsd.edu/jianhua.shao) | 2026-10-16T02:11:29+00:00 | 2071 | `7f95f99b41f0bf8ea15e39f3c422a1544567c5d595419e65b65bc503cc066ed2` |
| C034 | [Chris Longhurst / UCSD Profiles](https://profiles.ucsd.edu/christopher.longhurst) | 2026-10-16T01:13:13+00:00 | 15420 | `5916e30ad6808bb88ec716b51140b1f45ee119d239c20cdb6b20c6ba98b576e0` |
| C035 | [Elliot Mcveigh / UCSD Profiles](https://profiles.ucsd.edu/elliot.mcveigh) | 2026-10-16T02:02:52+00:00 | 1266 | `1057b6f75e23891b9bd352a5c2dd0b41427b0bfa29e243353e7929d8b0915d69` |
| C036 | [Cristina Llorente / UCSD Profiles](https://profiles.ucsd.edu/ana.llorenteizquierdo) | 2026-10-16T01:10:43+00:00 | 5977 | `80437303cd1358bba1464c178de81e275be94af31f9b8055639ec3c4c5e3cf89` |
| C037 | [Christina Schultz / UCSD Profiles](https://profiles.ucsd.edu/christina.le) | 2026-10-16T01:12:43+00:00 | 156 | `29cf3fa45ab3e4b0ab5cb7760772af21f393d744b85a15093418a58b4cb748e7` |
| C038 | [James Templeman / UCSD Profiles](https://profiles.ucsd.edu/james.templeman) | 2026-10-16T01:16:28+00:00 | 237 | `10e98cb6fbdcd0767fb55bab22b2e535ba1b1ac9836cbd4bc31f43544ddda0ac` |
| C039 | [Steffanie Strathdee / UCSD Profiles](https://profiles.ucsd.edu/steffanie.strathdee) | 2026-10-16T01:35:47+00:00 | 7415 | `fe5c143cfe9d7ca5d97dee142a38fe7d88fb92e2807a714b4d3869a67ffec252` |
| C040 | [Trey Ideker / UCSD Profiles](https://profiles.ucsd.edu/trey.ideker) | 2026-10-16T02:04:02+00:00 | 4996 | `425934c0b4e558681ec3b324ae21bdd3c7ccb851711bad1fe2c3e4a481f13e14` |
| C041 | [Alison Potok / UCSD Profiles](https://profiles.ucsd.edu/olivia.potok) | 2026-10-16T01:30:54+00:00 | 1137 | `84e67a70a7d505128bad46460e76d8b748001e4569160b48202654310b520703` |
| C042 | [Karsten Zengler / UCSD Profiles](https://profiles.ucsd.edu/karsten.zengler) | 2026-10-16T02:15:59+00:00 | 1018 | `912064a2003c10dd6e50435f2c4884d34967f6e17fb9717676bf96e8c9301e46` |
| C043 | [Helena Yu / UCSD Profiles](https://profiles.ucsd.edu/helena.yu) | 2026-10-16T02:16:09+00:00 | 1341 | `953bdd7e0889e7e837b5fbaefa669a6798b1e084e55a2f287277c904b1d92a4e` |
| C044 | [Vanessa Wong / UCSD Profiles](https://profiles.ucsd.edu/vanessa.wong) | 2026-10-16T02:16:19+00:00 | 763 | `c957806ea4306e3aaa39842a8b8fdc68b48647f48b84964742a6a93721185d52` |
| C045 | [Eric Won / UCSD Profiles](https://profiles.ucsd.edu/eric.won) | 2026-10-16T02:16:29+00:00 | 873 | `4e6549a09dd3157f5134f2ad7b19ef0220f8c0caf13327542a8798db3f18d539` |
| C046 | [Kristen Wigby / UCSD Profiles](https://profiles.ucsd.edu/kristen.wigby) | 2026-10-16T02:16:39+00:00 | 1758 | `b6421930e6c231d6146968003d8610a891da5e91245bed49ad84e5fe5ddbc7cb` |
| C047 | [Elizabeth Wang-giuffre / UCSD Profiles](https://profiles.ucsd.edu/elizabeth.wang-giuffre) | 2026-10-16T02:16:49+00:00 | 825 | `6fa17f072e5e5441872c0b185d091da06182f014662cad33555bde2fbb68dede` |
| C048 | [Vincent Wang / UCSD Profiles](https://profiles.ucsd.edu/vincent.wang) | 2026-10-16T02:16:59+00:00 | 921 | `e9da0f123a7eb08c35847a4ecd51db24bf4280bac4b1274cce12ae782c411400` |
| C049 | [Stephannie Voller / UCSD Profiles](https://profiles.ucsd.edu/stephannie.voller) | 2026-10-16T02:17:09+00:00 | 755 | `659e7cb82a53f66ec7e15dea1417fbe7a5ab62f1d8a7fe051fe063f4a041541c` |
| C050 | [Carolina Vega / UCSD Profiles](https://profiles.ucsd.edu/carolina.vega) | 2026-10-16T02:17:19+00:00 | 744 | `39c437289b8eb692515defcd670faa19080903fd3b5aa2a11572cf0be4eebddb` |
| C051 | [Jackson Vane / UCSD Profiles](https://profiles.ucsd.edu/jackson.vane) | 2026-10-16T02:17:29+00:00 | 917 | `c906659b85642b317583e861211a119c119e6f91f8c5708802be42c552d33f65` |
| C052 | [Ronald Teufel / UCSD Profiles](https://profiles.ucsd.edu/ronald.teufel) | 2026-10-16T02:17:39+00:00 | 934 | `1134f42146d9da205ce288da069a95dafe30c1fc6169782555205139ff2b8ff4` |
| C053 | [Laurie Stover / UCSD Profiles](https://profiles.ucsd.edu/laurie.stover) | 2026-10-16T02:17:59+00:00 | 896 | `73a013c0d6d0d718519700d73ed8b891df7b9467630255833769773c4fdb5fdf` |
| C054 | [Jose Silva Sepulveda / UCSD Profiles](https://profiles.ucsd.edu/jose.silvasepulveda) | 2026-10-16T02:18:09+00:00 | 1192 | `945912eeebeb9f02733a3dbfe1b23876d3c5f2f8cf2ba9cec31404db8e8435d7` |
| C055 | [Anita Sharma / UCSD Profiles](https://profiles.ucsd.edu/anita.sharma) | 2026-10-16T02:18:19+00:00 | 163 | `b04156ce278ae02a7a0531f72bf7e11c0797e26ba54de421de4e52e2bead126c` |
| C056 | [Jaime Sellers / UCSD Profiles](https://profiles.ucsd.edu/jaime.sellers) | 2026-10-16T02:18:29+00:00 | 370 | `a94b9f9dc59566a283c91ec96e682d2021d4ee9ecd3b886b525855b0b927c254` |
| C057 | [Stephanie Schmitt / UCSD Profiles](https://profiles.ucsd.edu/stephanie.schmitt) | 2026-10-16T02:18:39+00:00 | 894 | `6f9655070847fba4d7df9162ff300c53889e72a19ee333ee3d2f64bfc4f795ed` |
| C058 | [Debashis Sahoo / UCSD Profiles](https://profiles.ucsd.edu/debashis.sahoo) | 2026-10-16T02:18:50+00:00 | 1324 | `275fa22b0f3440b2ec88335a657d516d5a365946ec7fc649c834351a29cd6330` |
| C059 | [Cale Roberts / UCSD Profiles](https://profiles.ucsd.edu/cale.roberts) | 2026-10-16T02:18:59+00:00 | 163 | `f65ac39b176df8df315b223f08032f99527384733d9aa18edffb400ffa1fbd3b` |
| C060 | [Robin Raschke / UCSD Profiles](https://profiles.ucsd.edu/robin.miller) | 2026-10-16T02:19:09+00:00 | 935 | `5f43d0cbcccc5a92658cc530356cfa3e39abe484bb686b6245c407afd7f61d6c` |
| C061 | [Sayali Ranadive / UCSD Profiles](https://profiles.ucsd.edu/sayali.ranadive) | 2026-10-16T02:19:19+00:00 | 166 | `4e0509c50669fe3f719614185d76905da37c71d9c447cc4a37e2efb07f75ca7b` |
| C062 | [Alice Pong O'donnell / UCSD Profiles](https://profiles.ucsd.edu/alice.pongodonnell) | 2026-10-16T02:19:29+00:00 | 161 | `d2631e93d850a6f8c90c2498d4fb17373f7dde20c878953b76c1efa348d2b002` |
| C063 | [Betty Pham / UCSD Profiles](https://profiles.ucsd.edu/betty.pham) | 2026-10-16T02:19:39+00:00 | 1620 | `fb88a7dccedf651f9894e0c6f19390ce03222064cec2319678fefe762c2f4826` |
| C064 | [Katherine Nyman / UCSD Profiles](https://profiles.ucsd.edu/katherine.nyman) | 2026-10-16T02:19:49+00:00 | 785 | `e84f8271d38bf0f58af603d39629c396500bfd2ad5d40c0ba13382e2b8c4cb8a` |
| C065 | [Victor Nizet / UCSD Profiles](https://profiles.ucsd.edu/victor.nizet) | 2026-10-16T01:43:37+00:00 | 8686 | `dbf1cb2c1d8558768fedf93083cf91328206bb4bd5d00b128bcead53f19dce06` |
| C066 | [Lisa Mondzelewski / UCSD Profiles](https://profiles.ucsd.edu/lisa.mondzelewski) | 2026-10-16T02:19:59+00:00 | 851 | `583c2b107c3e23d583df0d6f2a4f7b0465a9708d9efb639d68366ecc4307ff6e` |
| C067 | [Tatyana Mills / UCSD Profiles](https://profiles.ucsd.edu/tatyana.mills) | 2026-10-16T02:20:10+00:00 | 939 | `006071ad76e3f42c228c27c01829c4e07491d9629078db046135f13fd7ace9e1` |
| C068 | [Edmund Milder / UCSD Profiles](https://profiles.ucsd.edu/edmund.milder) | 2026-10-16T02:20:19+00:00 | 919 | `968bb5bb49920ea7fcb028171952919dae1171f9dadb1c0c8724c5f75bc9beea` |
| C069 | [Annie Mcevoy / UCSD Profiles](https://profiles.ucsd.edu/annie.mcevoy) | 2026-10-16T02:20:29+00:00 | 163 | `1ddc4864cf30868bc9ddf5786e12fee5412343f3702684b69ce9bccacbbf765c` |
| C070 | [Ximena Lopez / UCSD Profiles](https://profiles.ucsd.edu/ximena.lopez) | 2026-10-16T02:20:39+00:00 | 903 | `34d6c69d1e29ce5196fd0d172cc4ddd61c51e4cafaa5fe0bf1c91569534ce6e3` |
| C071 | [Tom Lin / UCSD Profiles](https://profiles.ucsd.edu/tom.lin) | 2026-10-16T02:20:50+00:00 | 974 | `4f572d3b8d32b7e51c97b92e55350b14bcddab51f405e4425df62a882fe3e1a9` |
| C072 | [Kincheon Li / UCSD Profiles](https://profiles.ucsd.edu/kincheon.li) | 2026-10-16T02:21:00+00:00 | 3218 | `9b48757dc299168a566fc1671e827988f02aad9665c50701c469377aa8c44709` |
| C073 | [Hojun Li / UCSD Profiles](https://profiles.ucsd.edu/hojun.li) | 2026-10-16T02:21:10+00:00 | 1259 | `6aed433971eab6c142648d2d2497f58ca0d1f82aee875836931e054cef56fbd0` |
| C074 | [Aviya Levy / UCSD Profiles](https://profiles.ucsd.edu/aviya.levy) | 2026-10-16T02:21:20+00:00 | 3734 | `ac471000677300b072b2226a933f707a742b7a7f0ab1750023e888d2f686bca8` |
| C075 | [Danielle Leverone / UCSD Profiles](https://profiles.ucsd.edu/danielle.munce) | 2026-10-16T02:21:29+00:00 | 954 | `b303707b1ce455c8a1e4d700a3d8c59a6e5815c6c78b57c5e0e66826b0cf43b5` |
| C076 | [Chloe Kupelian / UCSD Profiles](https://profiles.ucsd.edu/chloe.kupelian) | 2026-10-16T02:21:39+00:00 | 925 | `e4a115490fd834489b0071ae6927f4c1c12c0ce32286f9ae90c8a62b30440dce` |
| C077 | [Vira Kravets / UCSD Profiles](https://profiles.ucsd.edu/vira.kravets) | 2026-10-16T02:21:59+00:00 | 925 | `1223e9f77f71d9bd5d03563c70f3825724ba6bdbc3ae07a73e81381688ff19c9` |
| C078 | [Tyler Kingdon / UCSD Profiles](https://profiles.ucsd.edu/tyler.kingdon) | 2026-10-16T02:22:40+00:00 | 919 | `6ab45fef7a1f31e13ba227bfe8c12c3c9e15a94d2d456eb6fcf15bd3e3a28e7b` |
| C079 | [Sujung Kim / UCSD Profiles](https://profiles.ucsd.edu/sujung.kim) | 2026-10-16T02:22:49+00:00 | 161 | `440c4f7a44795ece8fa882904ea917c312f91d593b9414c7413fcebcacedff2c` |
| C080 | [David Katibian / UCSD Profiles](https://profiles.ucsd.edu/david.katibian) | 2026-10-16T02:23:00+00:00 | 956 | `1be65d05d13baea437ab6f14888b4b936ff4a270ced9da1e4fee18db97f6c96a` |
| C081 | [Amir Jazayeri / UCSD Profiles](https://profiles.ucsd.edu/amir.jazayeri) | 2026-10-16T02:23:10+00:00 | 864 | `16b43a9d3d6522414a01a19d398539800a32a5c5af3331a626a93b9117875361` |
| C082 | [Jordan Wen Ing / UCSD Profiles](https://profiles.ucsd.edu/jordanwen.ing) | 2026-10-16T02:23:20+00:00 | 165 | `1bb8a98b0a3ec495fc5337b851c0f328ccb500795fb1c6c4bc8f8eaf0386722e` |
| C083 | [Manju Hurvitz / UCSD Profiles](https://profiles.ucsd.edu/manju.hurvitz) | 2026-10-16T02:23:39+00:00 | 907 | `87d2e76e8206e51c61ae22224907a0ab8f4af7bc61f4c0d525434da319dac0c0` |
| C084 | [Yue Huang / UCSD Profiles](https://profiles.ucsd.edu/yue.huang) | 2026-10-16T02:23:49+00:00 | 160 | `91fd820df845bd72976f5bb220b10201970379063521839a0f57cca4443f2fdc` |
| C085 | [Jack Gilbert / UCSD Profiles](https://profiles.ucsd.edu/jack.gilbert) | 2026-10-16T02:24:02+00:00 | 1465 | `0a5761fe739d960e7d1ffeba93e3e4d0d9a7740c78a9da77d1fd080e408b8c55` |
| C086 | [Katrina Epperson / UCSD Profiles](https://profiles.ucsd.edu/katrina.epperson) | 2026-10-16T02:24:12+00:00 | 501 | `ae22c59aa993b99bf2c267ade2265bd45b9bf290c6d074c9f3615ffd791d78d9` |
| C087 | [Amanda Dube / UCSD Profiles](https://profiles.ucsd.edu/amanda.dube) | 2026-10-16T02:24:22+00:00 | 922 | `14be7f8b32f0b9e2682dc7683534cf0d7ceda9cc7c370ec4b363b5642d3e1ebd` |
| C088 | [Andrew Dickerson / UCSD Profiles](https://profiles.ucsd.edu/andrew.dickerson) | 2026-10-16T02:24:32+00:00 | 926 | `0d8db62a5535221121c01fab115b3dd46348e8ee3cfcc85355dc89211e6f0f4d` |
| C089 | [Clarkson Crane / UCSD Profiles](https://profiles.ucsd.edu/clarkson.crane) | 2026-10-16T02:24:42+00:00 | 969 | `4a13dafd2d01e09193078b2f33c43e1584070a3c512501551e3066ac3b2c7294` |
| C090 | [Victoria Cartwright / UCSD Profiles](https://profiles.ucsd.edu/victoria.cartwright) | 2026-10-16T02:24:52+00:00 | 160 | `39d8ab94818ab56246dfc44b0de8f2223ba4d9e772ff2de589b6a8ae5262417c` |
| C091 | [Carrie Byington / UCSD Profiles](https://profiles.ucsd.edu/carrie.byington) | 2026-10-16T02:25:02+00:00 | 1804 | `0a08b7190230ffe1212f2fe3d411062dd5aac2a611e24215d570c9418216e07d` |
| C092 | [Francesca Briganti / UCSD Profiles](https://profiles.ucsd.edu/francesca.briganti) | 2026-10-16T02:25:12+00:00 | 1729 | `4f463362f7faae4febbc3de2884f4327817a59cc67ffa48e0be085d70542dfc8` |
| C093 | [Vikas Bansal / UCSD Profiles](https://profiles.ucsd.edu/vikas.bansal) | 2026-10-16T02:25:22+00:00 | 1317 | `ed3006678926fcd6c1c39071a5827ca234b0519ed9c276c123b38445774c8e5c` |
| C094 | [Deema Arafah / UCSD Profiles](https://profiles.ucsd.edu/deema.arafah) | 2026-10-16T02:25:32+00:00 | 163 | `4c77ea404d4822ca7849d30ea700e467df20d5619914ea23dca72832420a93bf` |
| C095 | [Angels Almenar / UCSD Profiles](https://profiles.ucsd.edu/angels.alhenar) | 2026-10-16T02:25:52+00:00 | 1405 | `2b94c8f96be65e6feb83ee15f55fef612ac76c876294fc39ce987362204c70c0` |
| C096 | [Amethyst Alayari / UCSD Profiles](https://profiles.ucsd.edu/amethyst.alayari) | 2026-10-16T02:26:02+00:00 | 891 | `19497d0c2d41ee70e5277c334db451c8a1be40ad1b92874956f36db16760ca5c` |
| C097 | [Brewer Lab](https://neurosciences.ucsd.edu/research/labs/brewer/index.html) | 2026-10-16T01:05:05+00:00 | 1030 | `3ce2379a90c77e4724396d4cb23728d0b5dde7a55923bb2695e70a5743ed7b1b` |
| C098 | [Campbell Lab](https://neurosciences.ucsd.edu/research/labs/campbell/index.html) | 2026-10-16T01:05:06+00:00 | 2355 | `b77c04ef7fe63e6d81cedb7901e5b94d49a8ea0208d834b5828c4432f7e2d9b1` |
| C099 | [Neurovascular Imaging Lab](https://neurosciences.ucsd.edu/research/labs/neurovascular-imaging/index.html) | 2026-10-16T01:05:07+00:00 | 1577 | `e9e1a7f226b970c67a2ebfd96a7c01f056b643ab200a2f09dffe1f1ec0672938` |
| C100 | [Dore Lab](https://neurosciences.ucsd.edu/research/labs/dore/index.html) | 2026-10-16T01:05:09+00:00 | 917 | `1ea6d3db82406e265a12cdbd49c4e3919e2ddf67e41d0d8790c8099f2ed5fc88` |
| C101 | [CITRUS: Gholipour Lab](https://neurosciences.ucsd.edu/research/labs/gholipour/index.html) | 2026-10-16T01:03:47+00:00 | 1185 | `c839e547bda70793f2e1273a9a29ba2217ddb37b6c60d0a6e899a95a9f3e1106` |
| C102 | [Gleeson Lab](https://neurosciences.ucsd.edu/research/labs/gleeson/index.html) | 2026-10-16T01:05:10+00:00 | 4264 | `217d83a7032198eed3eba7ff6510d0e28ec271b1adf14784b4997e62bbec680a` |
| C103 | [Graves Neuroimmunology Research Group: UC San Diego Multiple Sclerosis and Related Diseases Research Center](https://neurosciences.ucsd.edu/research/labs/graves/index.html) | 2026-10-16T01:02:48+00:00 | 3924 | `2e9cad9f407ef8968c4f65c3fa3d0870878d7266efc8674a61d83799b1854577` |
| C104 | [Hnasko Lab](https://neurosciences.ucsd.edu/research/labs/hnasko/index.html) | 2026-10-16T01:05:12+00:00 | 1706 | `962258327cb56c74848c38c75d695525565ae36e3a05f41df9b82bdcff9401b1` |
| C105 | [Kim-McManus Lab Home](https://neurosciences.ucsd.edu/research/labs/kim-mcmanus/index.html) | 2026-10-16T01:06:34+00:00 | 985 | `89f891645f718b72864c4039e155a0a7045b97c35c44b2a3db2e44f9388febb8` |
| C106 | [Mobley Lab - Neurosciences](https://neurosciences.ucsd.edu/research/labs/mobley/index.html) | 2026-10-16T01:05:15+00:00 | 691 | `40b433b261f3ba76c6f50455a9d98ecdd36b12ef23ec42de0459fb5e2878bfd5` |
| C107 | [Praveen Raju Lab Website Homepage](https://neurosciences.ucsd.edu/research/labs/raju/index.html) | 2026-10-16T01:05:16+00:00 | 189 | `17f1230543f2cbada57a105972a888de7faae92712752833272cf8def0e71496` |
| C108 | [Autism & Development](https://neurosciences.ucsd.edu/research/labs/autism-development/index.html) | 2026-10-16T01:05:18+00:00 | 1291 | `75ea827959039578d1c3449b20fca6959ab162ea305f65e5efc67b657d0d2915` |
| C109 | [Ung Lab](https://neurosciences.ucsd.edu/research/labs/ung/index.html) | 2026-10-16T01:05:19+00:00 | 528 | `ebd76ad7d3937bc3f4bc872027fe19e36d90dacbaca1dbf0ef117bce6e052ebd` |
| C110 | [Zheng Lab](https://neurosciences.ucsd.edu/research/labs/zheng/index.html) | 2026-10-16T01:05:21+00:00 | 1640 | `28f00273dccb6b816a1da495cd234460c3d5e4414e523aa38e102f4640a535c8` |
| C111 | [Reas Lab](https://neurosciences.ucsd.edu/research/labs/reas/index.html) | 2026-10-16T01:05:17+00:00 | 846 | `22a56361f6f8d04d7418d3564c2809dba5b10c1c64e3a9368b2398ab0cabce70` |
| C112 | [Banks Lab](https://neurosciences.ucsd.edu/research/labs/banks/index.html) | 2026-10-16T01:05:04+00:00 | 1011 | `5cf93f9670a58db87371e6c2be477b65ccdd8d6e7bc79d186edd47486271083a` |
| C113 | [Looger Lab](https://neurosciences.ucsd.edu/research/labs/looger/index.html) | 2026-10-16T01:05:12+00:00 | 133 | `da95069bb8d7a1e7b6ed654e6771be87b7a072da5ca769c9914afc6188f71fe7` |
| C114 | [Gladys Ramos / UCSD Profiles](https://profiles.ucsd.edu/gladys.ramos) | 2026-10-16T01:41:37+00:00 | 998 | `fdf8c53303d68289fa77da4b472bb3d2a2cfed51fbe9cba6288a8d6f15324d5d` |
| C115 | [Hui-chun Irene Su / UCSD Profiles](https://profiles.ucsd.edu/hui-chunirene.su) | 2026-10-16T01:40:57+00:00 | 5071 | `59ce3525480e19c10a2b5a58ac9ba3a3951581ed229dd611b96abf6e049b2afc` |
| C116 | [Breen Church Lab](https://obgyn.ucsd.edu/research/labs/breen-church/index.html) | 2026-10-16T01:02:48+00:00 | 1081 | `3cb2d8cf0faa08d456eb3bdad8dfc6e57253b5a7ddbeb809ec6105941942beeb` |
| C117 | [Burnett Lab](https://obgyn.ucsd.edu/research/labs/burnett/index.html) | 2026-10-16T01:02:48+00:00 | 1431 | `e981018e6b7767138f476fe3a289217adb16683cb41a698511480f819a6b4ba1` |
| C118 | [Fisch Lab](https://obgyn.ucsd.edu/research/labs/fisch/index.html) | 2026-10-16T01:02:50+00:00 | 1428 | `01c5152ec4ede336674c9e4393dabad9ca4a1e806360b256a7f08b44f77a7f87` |
| C119 | [Kauffman Lab](https://obgyn.ucsd.edu/research/labs/kauffman/index.html) | 2026-10-16T01:02:51+00:00 | 1188 | `1b21f31f59e46f82f3b394fd042d452be9dd90fcb146ef1f409f4ee57e953196` |
| C120 | [Laurent Lab](https://obgyn.ucsd.edu/research/labs/laurent/index.html) | 2026-10-16T01:02:52+00:00 | 2394 | `5492125945623f1d47337e7c0fce8db114aee8694f453b2845b7d4fb69c0a0b2` |
| C121 | [Lawson Lab](https://obgyn.ucsd.edu/research/labs/lawson/index.html) | 2026-10-16T01:02:53+00:00 | 1538 | `b1fa30b1d63344f6732075fd3ca99f20c868f0a75ba8f63790bba7163d2f01ff` |
| C122 | [Mellon Lab](https://obgyn.ucsd.edu/research/labs/mellon/index.html) | 2026-10-16T01:02:54+00:00 | 616 | `91a550ffcb26cd4014e1a6028705c7a2d6fd4f974884938366e67c09aaf657e0` |
| C123 | [Pantham Lab](https://obgyn.ucsd.edu/research/labs/pantham/index.html) | 2026-10-16T01:02:55+00:00 | 1305 | `10c30f4fee05e59eeb01151eafc0949d3c3104b758dc8c162c1ad76bcefec3ab` |
| C124 | [Schlaepfer Lab](https://obgyn.ucsd.edu/research/labs/schlaepfer/index.html) | 2026-10-16T01:02:57+00:00 | 3896 | `1353c21d852699ae43d435355bf27702cfbb3c319c1859a34941981194506ca8` |
| C125 | [Thackray Lab](https://obgyn.ucsd.edu/research/labs/thackray/index.html) | 2026-10-16T01:02:59+00:00 | 3919 | `8c96c9dbc1c187e4c1d5ec3b74df73bcf68a5e5fa69c612964462392b2e00750` |
| C126 | [Wilkinson Lab](https://obgyn.ucsd.edu/research/labs/wilkinson/index.html) | 2026-10-16T01:03:00+00:00 | 698 | `fe75aa4facc110dcb9266fd5656982f2cb21fdd82c3a9fde7c44d79e6a01975c` |
| C127 | [Su Lab](https://obgyn.ucsd.edu/research/labs/su/index.html) | 2026-10-16T01:02:58+00:00 | 1580 | `e4ba163019237a4931e1fb70bf575ee396954023337c208e0121f2ab2d2d8e8f` |
| C128 | [Tan Lab](https://obgyn.ucsd.edu/research/labs/tan/index.html) | 2026-10-16T01:05:10+00:00 | 665 | `11bcc921e265b2a65b13867f1381d1e098ee39bf5fa11c12c940481e702afa15` |
| C129 | [Scott Harvey / UCSD Profiles](https://profiles.ucsd.edu/scott.harvey) | 2026-10-16T01:27:44+00:00 | 971 | `79b2d0a3786d9f04d9d35bfa4223bb1b51af3bbe36c99dd91d61321c795c8dff` |

## Additional rejected pages read

- [Cardiac & Neuro Protection Laboratories root](https://cardiacneuroprotection.com/), observedAt `2026-10-16T02:39:59+00:00`, body SHA-256 `2d01d2c4c2196ed754be7aaadfff0272ca0443e3442d706fa3fbc7264c66ca13`: architecture template content, rejected as Patel lab research.
- [Urology Jamieson Lab](https://urology.ucsd.edu/research/jamieson-lab/index.html), observedAt `2026-10-16T01:06:24+00:00`, body SHA-256 `f2b10e7213a98a93a8e6c3f7ed31e445f8ed952681a23c65c28c83d8b14ae97d`: explicitly Christina Jamieson, rejected for the Catriona Jamieson ID.
- [Urology About Our Research](https://urology.ucsd.edu/research/jamieson-lab/about.html), observedAt `2026-10-16T01:06:25+00:00`, body SHA-256 `f8bf51601f7a248c20ff30b6cddfa916bfa60bb264df67394de09464e09f9f5e`: prostate/bone metastasis PDX and 3D models belong to that different laboratory, not Catriona Jamieson.
- [Medicine Faculty Directory](https://med.ucsd.edu/about/faculty-directory.html), observedAt `2026-10-16T00:57:26+00:00`: full cached 30,794-character visible body examined beyond the 18,000-character packet prefix; relevant entries supply person/unit names only, no named laboratory research statements.
- [OBGYN Clinical Studies](https://obgyn.ucsd.edu/research/clinical-studies.html), observedAt `2026-10-16T01:05:09+00:00`: full cached 36,592-character visible body examined beyond the packet prefix; Marni Jacobs appears as a project collaborator/MPI, without an independent Jacobs Lab definition.

Static validation: hydrate passed for all 23 final raw records; all 14 appended sources match exact ContentDOM text, deterministic IDs, original cached body hashes and queue/gap observation times. All 13 mismatch records remain nonaccepted. No generic department topic, other laboratory program, publication-only technique or personal-only research description was used to upgrade a lab.
