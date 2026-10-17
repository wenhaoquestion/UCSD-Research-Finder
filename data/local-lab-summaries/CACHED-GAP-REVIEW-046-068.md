# Cached gap review 046–068

审阅时间：2026-10-16T03:04:01+00:00。范围为候选非空记录索引46:69：23个稳定ID、107条候选关系、59个原始缓存采集。没有网络请求，没有修改采集器、代码、聚合输出，没有应用别名或合并ID。

结果：1条更新（752 Frank Powell，partial → supported），22条保持。仅为Powell追加一个经人工实体审阅的缓存来源到该ID的supplemental-sources和packet；原证据、原observedAt及原始字节hash保留。23条当前raw/packet均通过hydrate。

候选HTML使用ContentDOM/decode_cached_html读取；59个采集的实际字节SHA-256和原queue时间/hash均核对一致。导航、个人主题、书目及相邻实验室不是目标实验室研究证据。采集时间不等于内容日期或当前运营/任职确认。

## Per-ID decisions

| 候选索引 | ordinal / labId | 结论 | 原始候选 | 判定理由与剩余blocker |
|---|---|---|---|---|
| 46 | 544 / ucsd-live-lab-1b6658ea7dfbc7 | unchanged：unresolved；拒用1 | [C01](#c01) | MAE教师目录只列Michael Frazier及Lab Website，没有具名实验室研究正文；不能解决目的页robots不可用及实验室作用域缺口。 剩余：destination_robots_unavailable；no_entity_local_research_text |
| 47 | 549 / ucsd-live-lab-79f8d7df25e8a2 | unchanged：partial；拒用2 | [C01](#c01), [C02](#c02) | MAE和ECE课程目录只列Miroslav Krstic个人职务或跨系身份，没有独立实验室或团队研究声明；不能与个人主页著作方向拼成lab研究。 剩余：destination_encoding_corruption；no_explicit_lab_identity |
| 48 | 557 / ucsd-live-lab-5dba8659c4ddd7 | unchanged：partial；拒用1 | [C03](#c03) | 认知科学名单只列Lara Rangel职务、邮箱与网站；不是Neural Crossroads Laboratory研究纲领，原首页新闻仍不足以概括全组。 剩余：news_publication_only_no_lab_research_scope |
| 49 | 574 / ucsd-live-lab-55424aea242e83 | unchanged：partial；拒用1 | [C01](#c01) | MAE目录只列Raymond de Callafon及Lab Website，没有实验室团队或方法正文。 剩余：目标 robots 获取失败，无目标站研究正文。 |
| 50 | 575 / ucsd-live-lab-5387f4ac5dd057 | unchanged：partial；拒用1 | [C01](#c01) | MAE目录只列Alexey Arefiev，不解释其个人user/28页与Relativistic Laser-Plasma Simulation Group的研究作用域。 剩余：当前目标为个人简介；研究组名称仅历史链接，缺少当前研究组身份说明。 |
| 51 | 580 / ucsd-live-lab-a3503249b3a0dd | unchanged：unresolved；拒用21 | [C04](#c04), [C05](#c05), [C06](#c06), [C07](#c07), [C08](#c08), [C09](#c09), [C10](#c10), [C11](#c11), [C12](#c12), [C13](#c13), [C14](#c14), [C15](#c15), [C16](#c16), [C17](#c17), [C18](#c18), [C19](#c19), [C20](#c20), [C21](#c21), [C22](#c22), [C23](#c23), [C24](#c24) | 21候选中20条采集属于Grossfeld、Feldstein、Schwimmer、Briganti、Cherqui、Muotri、Joshi、Zage、Nizet、Rivera-Chávez、Liu、Spector（两次）、Leibel、Neonatal Health Services Research、Nigam、Haddad、Quinton、Pediatric Pharmacology、Sajti等其他单位；另一个是Jianhua Shao个人基金档案。Shao不等于Sahoo，缺少同一实体或别名证明，全部拒用。 剩余：目标页面 HTTP 错误；缺少实验室研究正文。 |
| 52 | 583 / ucsd-live-lab-d2d234fc0f3eba | unchanged：partial；拒用1 | [C25](#c25) | Bioengineering目录仅列Geert Schmid-Schoenbein与Research链接，没有解释Microcirculation Laboratory、Schmid-Schoenbein Lab和Center for Autodigestion Innovation的更名或继承关系；mismatch与未接受标记保留。 剩余：Microcirculation Laboratory、Schmid-Schoenbein Lab与Center for Autodigestion Innovation之间的更名、继承或共同实体关系仍缺少明确官方正文，不能接受ID迁移或把中心研究归入历史实验室。 |
| 53 | 593 / ucsd-live-lab-11396e2a4edb16 | unchanged：unresolved；拒用2 | [C03](#c03), [C26](#c26) | 认知科学名单和课程目录只确认Douglas Nitz个人名称，无Systems Neuroscience Lab研究内容。 剩余：目标 robots 获取失败；缺少研究正文。 |
| 54 | 596 / ucsd-live-lab-0944d3c6e80b01 | unchanged：partial；拒用2 | [C27](#c27), [C28](#c28) | 两个ECE目录只列Nicholas Antipa与Lab Web，无Computational Imaging Systems Lab研究纲领，不能替代需认证的目的页。 剩余：目标站要求认证，未捕获公开实验室正文。 |
| 55 | 600 / ucsd-live-lab-11b4e52b3e903e | unchanged：unresolved；拒用1 | [C29](#c29) | 视觉艺术名单只列Brett Stalbaum及ICAM/Speculative Design教学分类，无Walkingtools Laboratory研究正文。 剩余：目标 robots_denied；缺少实验室研究正文。 |
| 56 | 603 / ucsd-live-lab-bf194dbf29f17f | unchanged：partial；拒用2 | [C27](#c27), [C28](#c28) | 两个ECE教师目录只列Tse Nga Ng职务和联系信息，无实验室团队或项目描述；不把个人柔性电子研究转为组级研究。 剩余：目标 robots 获取失败。 |
| 57 | 608 / ucsd-live-lab-647875c86ee945 | unchanged：unresolved；拒用1 | [C25](#c25) | Bioengineering目录仅列John Watson Professor Emeritus与Watson Research链接，无Watson Lab研究问题或方法。 剩余：目标 robots 获取失败；缺少研究正文。 |
| 58 | 611 / ucsd-live-lab-0f62740a3eaf3f | unchanged：partial；拒用3 | [C30](#c30), [C25](#c25), [C02](#c02) | CNE、Bioengineering、ECE目录只列Sheng Xu个人任职、affiliate及Lab Website/Research标签；不能补足当前根页的领域标语。 剩余：当前正文仅领域标语，未给出实验室具体研究问题和方法。 |
| 59 | 615 / ucsd-live-lab-ca0f4105fff103 | unchanged：partial；拒用2 | [C25](#c25), [C31](#c31) | Bioengineering目录只有Huilin Zhou与Research链接；Profiles搜索页只有全站入口和网络更新，无新的lab研究或旧Ludwig/候选站别名关系。mismatch、provisional与候选未接受状态保留。 剩余：原实验室具名路径的既有目的页是Ludwig机构主页；新官方档案仍给出同一旧链接，未解决独立实验室网址与实体映射。；候选实验室网站与旧ID之间缺少明确别名或继承说明，候选纠正尚未接受。 |
| 60 | 624 / ucsd-live-lab-61e490319a4560 | unchanged：partial；拒用1 | [C31](#c31) | Profiles搜索页是入口、统计和他人动态，无Karen Oegema或Oegema Lab研究；不解除旧Ludwig目的页mismatch，不合并Desai/Oegema稳定ID。 剩余：原实验室具名路径的既有目的页是Ludwig机构主页；新官方档案仍给出同一旧链接，未解决独立实验室网址与实体映射。；候选实验室网站与旧ID之间缺少明确别名或继承说明，候选纠正尚未接受。 |
| 61 | 627 / ucsd-live-lab-421d1a9d198202 | unchanged：partial；拒用1 | [C32](#c32) | Biological Sciences课程目录只列Takaki Komiyama姓名，不能证明空正文目的页的实验室身份或研究。 剩余：当前目标可达但提取正文为空。 |
| 62 | 628 / ucsd-live-lab-93bd07f93724ab | unchanged：partial；拒用1 | [C33](#c33) | Laura Crotty Alexander档案属于另一位研究者，列她自身基金和LCA Lab；不是Chantal Darquenne Lab，相似肺部/电子烟主题不能移用。 剩余：当前是个人研究简介，实验室名称仅历史链接，缺少独立实验室实体说明。 |
| 63 | 748 / ucsd-medicine-lab-bazhenov-lab | unchanged：unresolved；拒用19 | [C34](#c34), [C35](#c35), [C36](#c36), [C37](#c37), [C38](#c38), [C39](#c39), [C40](#c40), [C41](#c41), [C42](#c42), [C43](#c43), [C44](#c44), [C45](#c45), [C46](#c46), [C47](#c47), [C48](#c48), [C33](#c33), [C49](#c49), [C50](#c50), [C51](#c51) | 19候选均为其他肺科实验室、P-CHEW教育工作组或其他教师档案；sleep等相邻主题不等于Maksim Bazhenov Lab作用域，全部拒用。 剩余：目标 robots 获取失败；只有目录宽泛研究主题。 |
| 64 | 752 / ucsd-medicine-lab-frank-powell-lab | changed：partial → supported；接受1，拒用17 | [C50](#c50), [C34](#c34), [C35](#c35), [C36](#c36), [C37](#c37), [C38](#c38), [C40](#c40), [C41](#c41), [C42](#c42), [C43](#c43), [C44](#c44), [C45](#c45), [C46](#c46), [C47](#c47), [C48](#c48), [C33](#c33), [C49](#c49), [C51](#c51) | 接受Frank Powell官方Profiles：直接描述our laboratory及Experimental models in our laboratory，并列Powell Lab真实链接；与既有具名目录及目的页Frank Powell身份一致，补足lab研究作用域。其余17个其他实体候选拒用；旧healthsciences链接不作为当前pulmonary URL已核验alias/redirect。 无研究内容blocker；未声称当前运营或接受网址别名。 |
| 65 | 755 / ucsd-medicine-lab-west-lab | unchanged：partial；拒用19 | [C52](#c52), [C34](#c34), [C35](#c35), [C36](#c36), [C37](#c37), [C38](#c38), [C39](#c39), [C40](#c40), [C41](#c41), [C42](#c42), [C43](#c43), [C45](#c45), [C46](#c46), [C47](#c47), [C48](#c48), [C33](#c33), [C49](#c49), [C50](#c50), [C51](#c51) | John West Profiles只有个人关键词、历年基金与讲座/NASA链接，无West Lab整体研究说明；其余18个是其他实验室或教师。历史基金与个人履历不足以确认lab当前项目或方法。 剩余：当前只有个人历史研究，实验室当前实体与活动未核实。 |
| 66 | 770 / ucsd-orthopaedic-surgery-lab-hughes-austin-lab-epidemiology-bone-and-vascular-calcification | unchanged：partial；拒用2 | [C53](#c53), [C54](#c54) | Skeletal Translational Research介绍Koichi Masuda，Hughes-Austin仅为一篇文献合著者；Spine Neuromuscular Physiology Laboratory属于Bahar Shahidi。合著及同系邻接不能成为Hughes-Austin独立lab证据。 剩余：当前页面未明确独立实验室实体。 |
| 67 | 798 / ucsd-pharmacy-and-pharmaceutical-sciences-lab-chang-lab-geoffrey-chang | unchanged：unresolved；拒用1 | [C55](#c55) | Roger Sunahara档案属于另一研究者；其GPCR关键词和基金不是Geoffrey Chang Lab证据，药理学邻接不构成同一实体关系。 剩余：目标 HTTP 错误；院系列表只有个人任职，缺少实验室研究正文。 |
| 68 | 856 / ucsd-anthropology-lab-human-comparative-neuroanatomy-laboratory | unchanged：partial；拒用4 | [C56](#c56), [C57](#c57), [C58](#c58), [C59](#c59) | 总目录只列设施类别；其余为考古、心理/医学人类学及气候变化单位，均非Human Comparative Neuroanatomy Laboratory。不把其他单位的脑、健康或环境主题归入Semendeferi实验室。 剩余：目前列示网址为负责人官方个人资料；已捕获资料未明确区分其个人历史工作与该实验室当前整体研究纲领。 |

## Powell accepted evidence

新增来源src-d21368150cb26c7b，role=reviewed_cached_followup_requires_entity_match，原始observedAt=2026-10-16T02:09:49+00:00。来源为[Frank Powell官方档案](https://profiles.ucsd.edu/frank.powell)，不是本轮在线观察。

> The primary objective or our laboratory in the Division of Physiology is to determine the mechanisms of neural plasticity with hypoxia, which occurs with lung disease and sleep disordered breathing.

> Experimental models in our laboratory include:

同段明确列出高海拔健康人、慢性肺病及阻塞性睡眠呼吸暂停患者、大鼠和转基因小鼠、遥测与慢性生理记录、神经生理制备与活体成像、呼吸功能计算模型。raw保留完整逐字方法引文。

实际Powell Lab锚点指向[旧healthsciences具名路径](https://healthsciences.ucsd.edu/som/medicine/divisions/physiology/research/labs/powell/)。它支持对实验室的明确指认；没有替换listedWebsite，也没有把两个URL认定为已核验alias/redirect。

只写入records/ucsd-medicine-lab-frank-powell-lab.json、对应packet及supplemental-sources/ucsd-medicine-lab-frank-powell-lab.json。新source保存原缓存路径、完整hash、原时间、deterministic sourceId和identityReview理由。

## Original cached source ledger

C编号是本报告引用编号，不是新增packet sourceId。同一URL的不同原始采集分别列出，未借用其他URL或较晚采集的时间。

### C01

[Faculty | Mechanical and Aerospace Engineering](https://mae.ucsd.edu/people/faculty-profiles) — 原始observedAt：2026-10-16T00:57:23+00:00；hash/time核验通过。
- requestedUrl: https://mae.ucsd.edu/people/faculty-profiles
- SHA-256: 902b7ca8298d5d6e112fb089519f011d6ba7cb6ba3779493c991d1f5a324bb9b
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/bbd5d40f3dc38f1876763998f59cc29041ba6384a207781637a5cbc68f093de9.html

### C02

[Electrical and Computer Engineering](https://catalog.ucsd.edu/faculty/ECE.html) — 原始observedAt：2026-10-16T00:59:54+00:00；hash/time核验通过。
- requestedUrl: https://catalog.ucsd.edu/faculty/ECE.html
- SHA-256: 82db476e6625bc685a406c913316c5a8f200c219312aafcd82bdc40671341d89
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/1edd7c17da77544dc9afb076b47507d572c068893617497ef62a82984ddb0b73.html

### C03

[Faculty](https://cogsci.ucsd.edu/people/faculty/index.html) — 原始observedAt：2026-10-16T00:57:36+00:00；hash/time核验通过。
- requestedUrl: https://cogsci.ucsd.edu/people/faculty/index.html
- SHA-256: 276612c2e768d4032392f9bd89fc4687980f91de10c409e65ab6acecbdc8cfe1
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/e54e833e49c9f36f268440388aea1886b221c53e3c9ac006516ba1eaa4eb1407.html

### C04

[Grossfeld Lab](https://pediatrics.ucsd.edu/research/faculty-labs/grossfeld-lab/index.html) — 原始observedAt：2026-10-16T01:02:55+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/grossfeld-lab/index.html
- SHA-256: e8de2f6d3e743686b1d53425a8d7379d268a501fb9210cb83919a7fa25bd5e6a
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/6139bdc434e1126b265c367def26cb99eaaadff8e6370f7b6b987dfed6ccc765.html

### C05

[Feldstein Lab](https://pediatrics.ucsd.edu/research/faculty-labs/feldstein-lab/index.html) — 原始observedAt：2026-10-16T01:02:54+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/feldstein-lab/index.html
- SHA-256: 44f24c67cbd5688b125236fbc9c7ecd1db9a7cab05a2537bcd54706b64eded3c
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/97a4508eb564206af708b2edf87818364bf218c857a4d9defc5074b466b3508a.html

### C06

[Schwimmer Lab](https://pediatrics.ucsd.edu/research/faculty-labs/schwimmer-lab/index.html) — 原始observedAt：2026-10-16T01:03:05+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/schwimmer-lab/index.html
- SHA-256: f8836669cd09100264eb74164bd11ceed63f49a70354f9a7a8aa6d8c9c9fdc5e
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/3ff82af18d4fe3c06732e6f23edde3efe35ba53df6d0096cbbd934397e82ae71.html

### C07

[Briganti Lab](https://pediatrics.ucsd.edu/research/faculty-labs/briganti-lab/index.html) — 原始observedAt：2026-10-16T01:02:50+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/briganti-lab/index.html
- SHA-256: c03aa704376acc1ca4c167fe8f2fbc3b445bb594a0a15766f8fe57df4fefb8ba
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/63c964a031aa7d48690473ac96c08107389f7cb0ab7453c92b37a5ae2e95af4d.html

### C08

[Cherqui Lab](https://pediatrics.ucsd.edu/research/faculty-labs/cherqui-lab/index.html) — 原始observedAt：2026-10-16T01:02:52+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/cherqui-lab/index.html
- SHA-256: a44596290ec31cab88eda059054d97bc2ce5493571c385292edd6dce1b410395
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/95a02a82a3f197863a540c3e5329032ae4e5f438060431b0177c62a7cfcddd10.html

### C09

[Muotri Lab](https://pediatrics.ucsd.edu/research/faculty-labs/muotri-lab/index.html) — 原始observedAt：2026-10-16T01:02:59+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/muotri-lab/index.html
- SHA-256: 34b63f3346ae6bc675f64539f15c0775ea36e1d7415f450f37ac9f412c3191ec
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/76b2b6ac9896afe2fa423f6b834e186a65ad1f4e49a05590a9016dfaaa74f823.html

### C10

[Joshi Lab](https://pediatrics.ucsd.edu/research/faculty-labs/joshi-lab/index.html) — 原始observedAt：2026-10-16T01:03:25+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/joshi-lab/index.html
- SHA-256: 8f219ecd5f43378412c77f362ae5943804cb8f533ed596822701e1a8d332d17e
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/bb3f5990a220c32352228c37fb9567575eaabc1dae4d57aa627e35d126b67d18.html

### C11

[Zage Lab](https://pediatrics.ucsd.edu/research/faculty-labs/zage-lab/index.html) — 原始observedAt：2026-10-16T01:03:08+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/zage-lab/index.html
- SHA-256: ac1421369c25de3cdedd38d4a4ceb40632011906fbd4d4ce3918ccc0c5ca064b
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/476eae84dafabddfe882b98527d14fe1e450d160610fbb334cea616d43ed46d5.html

### C12

[Nizet Lab](https://pediatrics.ucsd.edu/research/faculty-labs/nizet-lab/index.html) — 原始observedAt：2026-10-16T01:03:02+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/nizet-lab/index.html
- SHA-256: 962b5363db445ab8bca5543a0f35556073189b0764723b799bbb707201cccc51
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/08123e1aef386a5c6d5017427154672ad60f42e5a6e6652ced39ac653c06e909.html

### C13

[Rivera-Chavez Lab](https://pediatrics.ucsd.edu/research/faculty-labs/rivera-chavez-lab/index.html) — 原始observedAt：2026-10-16T01:03:04+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/rivera-chavez-lab/index.html
- SHA-256: 685873ce1fa98ac3eef7d01212d07eb4195090dc9ad26561349646c2dbd7ad9d
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/a537c36d837280281e41c2ecfbc92844cbb01a2334a6df95d602738578bcf0d0.html

### C14

[Liu Lab](https://pediatrics.ucsd.edu/research/faculty-labs/liu-lab/index.html) — 原始observedAt：2026-10-16T01:02:58+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/liu-lab/index.html
- SHA-256: 81c5eace8d16cb9ba624981598a467710b3481c7b27b8feca21afc45b579ce79
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/d25c319d87f35f45563665300a527635efa0f43e5349bcf9692d4b45f49cc807.html

### C15

[Spector Lab](https://pediatrics.ucsd.edu/research/faculty-labs/spector-lab/index.html) — 原始observedAt：2026-10-16T01:03:06+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/spector-lab/index.html
- SHA-256: d8d8933e7e38127fa191703f9b8469effba41f1870a73c5ff1c1776e35fd4c8f
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/a62a0b675ad764d8f85fad7f6f75a0375cdf571e83e5200d5d83468ade41cdbc.html

### C16

[Spector Lab](https://pediatrics.ucsd.edu/research/faculty-labs/spector-lab/index.html) — 原始observedAt：2026-10-16T01:34:17+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/spector-lab/contact.html
- SHA-256: d8d8933e7e38127fa191703f9b8469effba41f1870a73c5ff1c1776e35fd4c8f
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/ba139f5257b64553600ec592169feb1445db16dde43da22f83394116a798ce2f.html

### C17

[Leibel Lab](https://pediatrics.ucsd.edu/research/faculty-labs/leibel-lab/index.html) — 原始observedAt：2026-10-16T01:02:57+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/leibel-lab/index.html
- SHA-256: e50510cf9781fb3a7bd1b5707d4a79bd1da399df4da34cee64e76329adf8fa41
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/38d1477f7d17e701672caaebe67fe43040f6504ebe1c0120accb10e55bf43b8a.html

### C18

[Neonatal Health Services Research Lab](https://pediatrics.ucsd.edu/research/faculty-labs/neo-hsr-lab/index.html) — 原始observedAt：2026-10-16T01:03:00+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/neo-hsr-lab/index.html
- SHA-256: 87d91c4ba36c38bbc8d83115a37fdac8a5c9b0c1e9f6098a50088ce55e8b68bd
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/30c26af90d7c95fa5b13518a811b9da6f5a94156d6495f55a8bc269d0b5ffa7e.html

### C19

[Nigam Lab](https://pediatrics.ucsd.edu/research/faculty-labs/nigam-lab/index.html) — 原始observedAt：2026-10-16T01:03:01+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/nigam-lab/index.html
- SHA-256: f1a0926b7ea38c95792c1b01d616dd0de25f63c92c1ec6d85adabd06a2c209e9
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/5bbebddce14a07e99270121a54df21dc535c813a27dd75868eb3bd6adf548cc9.html

### C20

[Haddad Lab](https://pediatrics.ucsd.edu/research/faculty-labs/haddad-lab/index.html) — 原始observedAt：2026-10-16T01:02:56+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/haddad-lab/index.html
- SHA-256: 3eda204dcc86ddd9859286d6155eec3e93cd5e933706e43606931374b16d0202
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/cac670c89ae2a3e37c1f96c138154cbb241051ca779a2957372e3cb99b5ee2e8.html

### C21

[Quinton Lab](https://pediatrics.ucsd.edu/research/faculty-labs/quinton-lab/index.html) — 原始observedAt：2026-10-16T01:03:03+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/quinton-lab/index.html
- SHA-256: 7dcd0687380dacd354829669e5993fb7d1cb036189a5ce613e8cd7825a202c3c
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/407b3c046623af6174e6b971b55b6aa9f9ca8f8ebf5dda27eb59b01efcb7a155.html

### C22

[Pediatric Pharmacology Laboratory (PPL)](https://pediatrics.ucsd.edu/research/faculty-labs/pediatric-pharmacology-laboratory/index.html) — 原始observedAt：2026-10-16T01:05:20+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/pediatric-pharmacology-laboratory/index.html
- SHA-256: bdf0c32493e02996744257ea112eac685bf21430278106fbc6e73ffd794809bb
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/edd94633716ee1d090499bc34d13b475268dcaa15bef8bacb1d47ee7965ba07b.html

### C23

[Sajti Lab](https://pediatrics.ucsd.edu/research/faculty-labs/sajti-lab/index.html) — 原始observedAt：2026-10-16T01:05:22+00:00；hash/time核验通过。
- requestedUrl: https://pediatrics.ucsd.edu/research/faculty-labs/sajti-lab/index.html
- SHA-256: 778377a607cbcb0fca5c021f3bb97303ae48c371085a05f5ab13ce6b289dad1f
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/0d72f4c3086dc37d538b18c3bb99b2007821eee5e3d1396726f1d2e7aee8e2a7.html

### C24

[Jianhua Shao | UCSD Profiles](https://profiles.ucsd.edu/jianhua.shao) — 原始observedAt：2026-10-16T02:11:29+00:00；hash/time核验通过。
- requestedUrl: https://profiles.ucsd.edu/jianhua.shao
- SHA-256: 7f95f99b41f0bf8ea15e39f3c422a1544567c5d595419e65b65bc503cc066ed2
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/0e0aeb5f915ad476a149b39d012feca1e3fb87dbd155d541aff46594020ace6b.html

### C25

[Faculty Profiles | Shu Chien - Gene Lay Department of Bioengineering](https://be.ucsd.edu/faculty) — 原始observedAt：2026-10-16T00:57:23+00:00；hash/time核验通过。
- requestedUrl: https://be.ucsd.edu/faculty
- SHA-256: 1f62c2b41b7d970d7e0f39679c2374c11aea40db436afda4e14e42e07afcd4e3
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/54e2bb1bcdf5eb32189e5fcfc7d6eecfd0b70ef1f784ce99f2ff10f6cecaecf8.html

### C26

[Cognitive Science](https://catalog.ucsd.edu/faculty/COGS.html) — 原始observedAt：2026-10-16T00:59:42+00:00；hash/time核验通过。
- requestedUrl: https://catalog.ucsd.edu/faculty/COGS.html
- SHA-256: ccf7a43d723670587972f5ad86c35cf88b105cd009acf7bd7e91a0da8b2ef7b6
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/38f6070d6dc73f60b0067187dbf33c1cf096fa7a92730ddab009c68cb7805a94.html

### C27

[Faculty | Electrical and Computer Engineering](https://www.ece.ucsd.edu/people/faculty) — 原始observedAt：2026-10-16T00:57:23+00:00；hash/time核验通过。
- requestedUrl: https://www.ece.ucsd.edu/people/faculty
- SHA-256: f5629bc29ed986e4c919eb573b90f770dabae18cb2db3c10ab47863875260166
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/78c128809362f1039e71d1d60e9ddec26605b6e914b71413779db2f1c5f57ad1.html

### C28

[Faculty | Electrical and Computer Engineering](https://ece.ucsd.edu/people/faculty) — 原始observedAt：2026-10-16T00:57:34+00:00；hash/time核验通过。
- requestedUrl: https://ece.ucsd.edu/people/faculty
- SHA-256: 0c2706a274955c8921dbee9f2daba02d1a12b32193df88e630d3d85f82e7995a
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/37d5d15bfa9244578ceea228a29d86889ea95678c30112611460a1df2cebd697.html

### C29

[Faculty](https://visarts.ucsd.edu/people/faculty/index.html) — 原始observedAt：2026-10-16T00:57:38+00:00；hash/time核验通过。
- requestedUrl: https://visarts.ucsd.edu/people/faculty/index.html
- SHA-256: 5479018a33079c31db779ef3268544d71b2da9d9892ed0e16a5ba643fd2c3b2e
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/b1c89eead1e80a7df2d98566964efc2ebe2dfc749fcefeb85985a3dc6351685d.html

### C30

[Faculty | Aiiso Yufeng Li Family Department of Chemical and Nano Engineering](https://cne.ucsd.edu/fac) — 原始observedAt：2026-10-16T00:57:35+00:00；hash/time核验通过。
- requestedUrl: https://cne.ucsd.edu/fac
- SHA-256: 2e5902cc4005690caf9d05cdc83807c50cb2a4c5f170a5bcb610440252e42e08
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/1673c7651206eb7144e4717c0a3154a2b15e8bec8a4cb7b9312e708e99aaafbc.html

### C31

[UCSD Profiles • Find/collaborate with leading health researchers](https://profiles.ucsd.edu/search/) — 原始observedAt：2026-10-16T01:28:24+00:00；hash/time核验通过。
- requestedUrl: https://profiles.ucsd.edu/
- SHA-256: d4b8f6f279df44d366e39f3600bab0c531e2c165685d828a7895d4b3878c9f6b
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/481ffb4a6d37c518c43413d6d4172460608541e8107d1b8a5a90f1a8ade57675.html

### C32

[Biological Sciences](https://catalog.ucsd.edu/faculty/BIOL.html) — 原始observedAt：2026-10-16T00:59:04+00:00；hash/time核验通过。
- requestedUrl: https://catalog.ucsd.edu/faculty/BIOL.html
- SHA-256: 79c3c737b97c7521eea0cecd6254e5c744c0f5d55ebcd0ada793ca05a3545074
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/9c19c05c793f1a2a2263f0a4de4b7d297bdcd002637de1b6765b777081cb37e9.html

### C33

[Laura Crotty Alexander | UCSD Profiles](https://profiles.ucsd.edu/laura.crottyalexander) — 原始observedAt：2026-10-16T02:06:22+00:00；hash/time核验通过。
- requestedUrl: https://profiles.ucsd.edu/laura.crottyalexander
- SHA-256: c74c3e051f032ed7de1f40f244bf4eebd994507ccd6e310903de030eccff0190
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/2cdfed19f4e1a9b9892fc7fc80a66ce8374c12fa960c24f99bd4bcb72cb7cf31.html

### C34

[Ramnath Lab](https://pulmonary.ucsd.edu/research/labs-centers/akuthota/index.html) — 原始observedAt：2026-10-16T01:03:16+00:00；hash/time核验通过。
- requestedUrl: https://pulmonary.ucsd.edu/research/labs-centers/akuthota/index.html
- SHA-256: e9da2f7584aaa96aaccd62fefb074fc575148357a598bb9607c68de06c1e1157
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/9d8767ac844c10df894d5b8bab7eafd898520366abc0a7a9b148c11e9ca75756.html

### C35

[Breen Lab](https://pulmonary.ucsd.edu/research/labs-centers/breen/index.html) — 原始observedAt：2026-10-16T01:03:17+00:00；hash/time核验通过。
- requestedUrl: https://pulmonary.ucsd.edu/research/labs-centers/breen/index.html
- SHA-256: 1daf9d912f682d6b44d91a9b58c19eb89f0565dcde0cc4ed5e73be53160e2203
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/e39485415165f709deab85a721b7865e81fd8060c3c9bacdae50bc0168b76758.html

### C36

[Crotty Alexander Lab](https://pulmonary.ucsd.edu/research/labs-centers/crotty-alexander/index.html) — 原始observedAt：2026-10-16T01:03:18+00:00；hash/time核验通过。
- requestedUrl: https://pulmonary.ucsd.edu/research/labs-centers/crotty-alexander/index.html
- SHA-256: 5f6365e94eb416b28cf878016009c1c0eec255e89029840c3c558e0603c85932
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/ad2611d578d8dd55c1611160529f7c1e1d3ae40e1e4f0713c760d0c2d2a52a66.html

### C37

[Chantal Darquenne Lab](https://pulmonary.ucsd.edu/research/labs-centers/darquenne/index.html) — 原始observedAt：2026-10-16T01:03:14+00:00；hash/time核验通过。
- requestedUrl: https://pulmonary.ucsd.edu/research/labs-centers/darquenne/index.html
- SHA-256: fa2f9bd82a1a662b0684d3e452d92b0f869fdb05c17c5ebc0ef2c3dece5d784b
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/93bd07f93724abc4bc1c8bd9e05ba5920fce295ebca5c68c3b37f5849b5d23b9.html

### C38

[Owens Lab](https://pulmonary.ucsd.edu/research/labs-centers/owens/index.html) — 原始observedAt：2026-10-16T01:03:19+00:00；hash/time核验通过。
- requestedUrl: https://pulmonary.ucsd.edu/research/labs-centers/owens/index.html
- SHA-256: 295842b717a40364f32fc9b9a0ecd45142a12035616f1c5c714867dba6e953bb
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/838fb48d0c9dde06d107dd63fb5d0ee1e525841464336e9142472ec577b732e8.html

### C39

[Frank Powell Lab](https://pulmonary.ucsd.edu/research/labs-centers/powell/index.html) — 原始observedAt：2026-10-16T01:03:20+00:00；hash/time核验通过。
- requestedUrl: https://pulmonary.ucsd.edu/research/labs-centers/powell/index.html
- SHA-256: ebbe703debf589bfba9bd29042e60e40fd17453c207725ff37116c32f26a6189
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/ed030364841cfd24e3df926d7b7761db714f8c11b579c623908b670da625a88b.html

### C40

[Simonson Lab](https://pulmonary.ucsd.edu/research/labs-centers/simonson/index.html) — 原始observedAt：2026-10-16T01:03:21+00:00；hash/time核验通过。
- requestedUrl: https://pulmonary.ucsd.edu/research/labs-centers/simonson/index.html
- SHA-256: c328b526a779c6ef0d168f87fc6cd954689dcc3a2440efea60a3bf4747bb4412
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/16d290b5d0d5b78e38a833b100fdd3c203f9827361904aba351b0761f73c6725.html

### C41

[Wardi Lab](https://pulmonary.ucsd.edu/research/labs-centers/wardi/index.html) — 原始observedAt：2026-10-16T01:03:22+00:00；hash/time核验通过。
- requestedUrl: https://pulmonary.ucsd.edu/research/labs-centers/wardi/index.html
- SHA-256: 6ee68b3fc6fb4c3a9d3344988ad04057290649adfe721256cd98cd5ff2c63083
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/3f93bd92a9d7dc9430384f5f3d529cc8b717e80b5d2ccb34c0a13f155101a8c9.html

### C42

[Hogan Lab](https://pulmonary.ucsd.edu/research/labs-centers/hogan/index.html) — 原始observedAt：2026-10-16T01:07:23+00:00；hash/time核验通过。
- requestedUrl: https://pulmonary.ucsd.edu/research/labs-centers/hogan/index.html
- SHA-256: 08919abf0111d6f44ebeca564cf5c1717d7fb871d158d49df17bf0a894cc435b
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/5b096171c496ea8f3ada57515c6e057aa4c7ddcc7b1b029271e8988e72204472.html

### C43

[Ramnath Lab](https://pulmonary.ucsd.edu/research/labs-centers/ramnath/index.html) — 原始observedAt：2026-10-16T01:07:25+00:00；hash/time核验通过。
- requestedUrl: https://pulmonary.ucsd.edu/research/labs-centers/ramnath/index.html
- SHA-256: d6dc3fbdb87101b452e5682484ebd95f6db45d9bfe3b94b60f3d613dc0cd1a08
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/1b18d0bdcca445d9ee1732d869befaec08b39c2f3b4241ef1c479fa13577497e.html

### C44

[West Lab](https://pulmonary.ucsd.edu/research/labs-centers/west/index.html) — 原始observedAt：2026-10-16T01:07:26+00:00；hash/time核验通过。
- requestedUrl: https://pulmonary.ucsd.edu/research/labs-centers/west/index.html
- SHA-256: bc356ca75c4ff230761662b36ace4a4b775b5c614138094dbd568d5d46c1fef8
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/10a3b8615898b282bc76ac7a5de1364ff2dd910608295ada8997a0ff86309a8c.html

### C45

[P-CHEW](https://pulmonary.ucsd.edu/research/labs-centers/pchew/index.html) — 原始observedAt：2026-10-16T02:06:24+00:00；hash/time核验通过。
- requestedUrl: https://pulmonary.ucsd.edu/research/labs-centers/pchew/index.html
- SHA-256: c13f0c8a2232fdd4aaed91285cb3ffa337dfa67c06e0d821717c632d235684a7
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/64225dc2c88c11150a6cc60b14ea1e9ae93ed4cbd1f4d87b19bae123b3fdf76e.html

### C46

[Mona Alotaibi | UCSD Profiles](https://profiles.ucsd.edu/mona.alotaibi) — 原始observedAt：2026-10-16T02:04:32+00:00；hash/time核验通过。
- requestedUrl: https://profiles.ucsd.edu/mona.alotaibi
- SHA-256: 0c5ad29cbc93a22ac04066dc8977b6384cc3431565e762d3dcd9b1a11877251f
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/21653213e112583d8adab551b4823bdf1333127eada9016a462f6aa2cf731692.html

### C47

[Ellen Breen | UCSD Profiles](https://profiles.ucsd.edu/ellen.breen) — 原始observedAt：2026-10-16T02:05:32+00:00；hash/time核验通过。
- requestedUrl: https://profiles.ucsd.edu/ellen.breen
- SHA-256: f546b7266ae9188e679e6dd02cc3bc9bf42f478376d0643ce8bdec6aae2d6635
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/627ae79f7bf3cda60990e36e44d7791972f7e43ac6faa6d3d5206aa058f0de9e.html

### C48

[Antonino Catanzaro | UCSD Profiles](https://profiles.ucsd.edu/antonino.catanzaro) — 原始observedAt：2026-10-16T02:05:52+00:00；hash/time核验通过。
- requestedUrl: https://profiles.ucsd.edu/antonino.catanzaro
- SHA-256: 69e7829ba81b4eea20580d87d814396c8c4705cb25737568ff9844deba1a1ed4
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/a051c66b08b47c92b305cc065f2de473c093cef503d965fd74d325df86088edd.html

### C49

[Mazen Odish | UCSD Profiles](https://profiles.ucsd.edu/mazen.odish) — 原始observedAt：2026-10-16T02:08:42+00:00；hash/time核验通过。
- requestedUrl: https://profiles.ucsd.edu/mazen.odish
- SHA-256: d47ab1b2ba830853a53bc6dfe22f6c4e8f1e58aae167f91e09bc8e98163912e0
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/d33c6770685c8ffb295c854702ae71b3107042088e33a20b55d729ee6f12d736.html

### C50

[Frank Powell | UCSD Profiles](https://profiles.ucsd.edu/frank.powell) — 原始observedAt：2026-10-16T02:09:49+00:00；hash/time核验通过。
- requestedUrl: https://profiles.ucsd.edu/frank.powell
- SHA-256: 0d6a8a8b1abf5817d3e2cc65702aa8b9ca60bdb903517941f51383eeb1c29c9e
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/0ac12efd1c145ad90f4db59ce90145abe1fbaff18584e8b2cf79e8c148dd944b.html

### C51

[Jenny Yang | UCSD Profiles](https://profiles.ucsd.edu/jenny.yang) — 原始observedAt：2026-10-16T02:11:09+00:00；hash/time核验通过。
- requestedUrl: https://profiles.ucsd.edu/jenny.yang
- SHA-256: db42145f5c178e5d57651e361960cc2fcee44dd400c0d84e21ea6e07cb757742
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/f2a23ad0d277bcc80333a445733ca233705ce95bdf8c848f56aa5c96cd8ea4f8.html

### C52

[John West | UCSD Profiles](https://profiles.ucsd.edu/john.west) — 原始observedAt：2026-10-16T02:10:59+00:00；hash/time核验通过。
- requestedUrl: https://profiles.ucsd.edu/john.west
- SHA-256: 5d749ad3bcbc92a83ab1e505002f556767a578869d57ba35981758c2abb31845
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/a7e548dc83f398361e4fe2597cafdb130b44b453f0933f00999eeed849bc2959.html

### C53

[Skeletal Translational Research](https://ortho.ucsd.edu/research/skeletal-translational-research.html) — 原始observedAt：2026-10-16T00:59:07+00:00；hash/time核验通过。
- requestedUrl: https://ortho.ucsd.edu/research/skeletal-translational-research.html
- SHA-256: ed1b540f7308249ee0f5826ed54aa770c7b1625d748ccd1aa93491339bc78b1b
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/1a191c144e248056c23802ea0a9eae96bce6a913bb75a753cab622388ae26a63.html

### C54

[Spine Neuromuscular Physiology Laboratory](https://ortho.ucsd.edu/research/spine-neuromuscular-physiology.html) — 原始observedAt：2026-10-16T01:05:13+00:00；hash/time核验通过。
- requestedUrl: https://ortho.ucsd.edu/research/spine-neuromuscular-physiology.html
- SHA-256: d963fa9aaf569685f8da73076696e490e1c8f0d7d8622a4ea98fc527fe0af4b7
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/e9fd396bcb28977dd6551e2084f4cde140c709a237a83faf703ee3a5f4889b86.html

### C55

[Roger Sunahara | UCSD Profiles](https://profiles.ucsd.edu/roger.sunahara) — 原始observedAt：2026-10-16T02:11:59+00:00；hash/time核验通过。
- requestedUrl: https://profiles.ucsd.edu/roger.sunahara
- SHA-256: 7b7a60058b36d3bf1ba3de180bb2e996ae898ea439a3457cd244d8bce06ad640
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/66fd164df00d2b375f7890cb20998bba6b1db671dfde97708c73feb6259c2c3f.html

### C56

[Laboratories and Interest Groups](https://anthropology.ucsd.edu/research/index.html) — 原始observedAt：2026-10-16T01:03:17+00:00；hash/time核验通过。
- requestedUrl: https://anthropology.ucsd.edu/research/index.html
- SHA-256: d5f0207d5aa307ed0851b49d366d7a3e5700e17e069745c632acf429fbb77f9c
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/dd74ae1cb62caf2b5193809d614c30496bfd8ceab6da5a398e69163153a4cae5.html

### C57

[Anthropological Archaeology Labs](https://anthropology.ucsd.edu/research/arch-labs.html) — 原始observedAt：2026-10-16T01:07:43+00:00；hash/time核验通过。
- requestedUrl: https://anthropology.ucsd.edu/research/arch-labs.html
- SHA-256: 55eba895fbf28c357c33bcc6d987ede3229232a5cd651d70335328c6ffbb7427
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/241c61abf506d6648f6b0f14ef880895aad2cf36fa1452d04f79f0aeb8b24eb5.html

### C58

[Psychological-Medical Anthropology Labs](https://anthropology.ucsd.edu/research/psych-anthro-labs/index.html) — 原始observedAt：2026-10-16T00:59:15+00:00；hash/time核验通过。
- requestedUrl: https://anthropology.ucsd.edu/research/psych-anthro-labs/index.html
- SHA-256: d9b8f86eb0282188952ae58e0e4f34951d1ba99c3e4bc95d5b3e884931ccdfe2
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/9de7b3b44a5999ef43663f32eefd31ef7ee07fe8937696068b7cc71f0d280cf0.html

### C59

[Climate Change Interest Group](https://anthropology.ucsd.edu/research/climate-change-group.html) — 原始observedAt：2026-10-16T01:03:44+00:00；hash/time核验通过。
- requestedUrl: https://anthropology.ucsd.edu/research/climate-change-group.html
- SHA-256: 122217e55d4deb712f6554d15f4065dbea689e6cf55e4c13183fecfe83bc723e
- 原始缓存: /tmp/ucsd-research-20261016/.cache/coverage-20261016/responses/be8be1252c1a12198f6e8f5cc4500b988ffeaabefbf81f1fd3e578dbd64dbcae.html

## Validation

- 23条raw/packet hydrate通过；本范围当前状态：{'unresolved': 7, 'partial': 15, 'supported': 1}。
- 只为752新增来源及更新raw；其余22条raw与packet未因被拒候选而改写。
- 583、615、624的mismatch、acceptanceStatus、proposedCorrections及禁止静默迁移标记保留。
- 106条候选关系拒作目标研究证据，1条Powell关系接受；同一缓存作为其他ID候选时仍按该ID作用域拒用。
- 研究更新由模型逐项撰写，没有按关键词自动生成研究总结。
