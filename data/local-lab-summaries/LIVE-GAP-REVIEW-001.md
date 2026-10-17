# Live gap review 001

实际离线审阅时间：2026-10-16T03:23:29+00:00。仅审阅共享适配器已取得的10个新来源；本审阅没有网络请求，也未改packet、ID、listed URL、HTTP重定向链、原始观察时间或身份决策。

结果：7条完成；6条raw更新、1条不重写；1条partial→supported（531）；最终1 supported、6 partial；7条hydrate通过。

源语义指纹使用完整可见正文与标题的规范化SHA-256，排除sourceId/观察时间/字节hash等采集元数据；JSON另存原始hash、sourceId与每条字段引文。后续同URL语义不变的捕获可据指纹跳过重复内容合成。

## 381 — Tongyan Lin Research Group

ID：ucsd-physics-research-site-tongyan-lin。决定：changed；partial → partial；实体类型：research_group → research_group。

新增暗物质研究正文，完善PI个人背景；没有全组研究声明，维持partial。

成员页确认 Tongyan Lin 在 UCSD 的研究组。新抓取的个人 Research 页以暗物质的粒子性质为核心，关注暗扇区、隐藏扇区和早期宇宙宇宙学，并寻找检验暗物质理论的新实验与观测探针；这些第一人称研究陈述尚不能作为全组研究概述。

新来源（原始观察时间与字节hash）：

- [Research – Tongyan Lin](https://tongyan.physics.ucsd.edu/research/)；observedAt 2026-10-16T03:17:53+00:00；sourceId src-aef169f692f44937；SHA-256 a6fd6c62867c2648a920fd1a6b4fc154e4c02781223530b58a016b8878ceb8f8；完整正文 1307 字符已读。

字段证据：

- limited_personal_research_context：[src-aef169f692f44937](https://tongyan.physics.ucsd.edu/research/) — “My research is at the interface of theoretical particle physics, cosmology, and particle astrophysics. A central theme of my work is understanding the particle physics of dark matter .”
- limited_personal_research_context：[src-aef169f692f44937](https://tongyan.physics.ucsd.edu/research/) — “I am interested in identifying new experimental and observational probes that can test the underlying theory of dark matter. More broadly, I am interested in the phenomenology of dark (or hidden) sectors, theoretical connections to other unresolved puzzles within the standard model, as well as early universe cosmology.”

具体边界：

- 方法未明确。
- 新 Research 页以 My research、my work 和 I am interested 表述；个人研究问题与目标不自动代表全组范围。
- 成员页确认组关系，但没有带日期的全组当前研究或任职声明；采集时间不等于任职生效时间。
- Blocker：no_group_scoped_research_overview_captured

新源语义指纹：5153a5c5f66964d190c859318389e0de7607d64b0f6436d0b47a744ef323b819。

## 515 — Jiun-Shyan Chen — lab website

ID：ucsd-live-lab-08c15f7b927bdd。决定：changed；partial → partial；实体类型：personal_research_site → personal_research_site。

完整阅读26587字符新Research正文（packet保留前18000字符）；采用引文全部在packet范围内。合作项目和PI兴趣未确立lab/group，维持partial。

Jiun-Shyan Chen 的个人 Research 页介绍计算固体力学、多尺度材料建模，以及把物理约束纳入数据驱动本构预测的计算研究。页面明确涉及有限元与无网格方法，并逐项介绍合作项目；仍未确认独立实验室或研究组实体。

新来源（原始观察时间与字节hash）：

- [Jiun-Shyan (JS) Chen - Research](https://jschen.eng.ucsd.edu/research)；observedAt 2026-10-16T03:17:54+00:00；sourceId src-2f85642974bf8594；SHA-256 3de2edcf04b440fda5927261cef85e2237066fca9366b85feab6e1663a9846eb；完整正文 26587 字符已读。

字段证据：

- limited_personal_research_context：[src-2f85642974bf8594](https://jschen.eng.ucsd.edu/research) — “Research Focus Chen's research interests are in computational solid mechanics and multiscale materials modeling .”
- limited_personal_research_context：[src-2f85642974bf8594](https://jschen.eng.ucsd.edu/research) — “We developed a physics-informed data-driven constitutive modeling approach by integrating physical constraints, such as energy convexity and objectivity, into data-driven constitutive modeling.”

具体边界：

- 研究页标题与开头明确以 Chen 的个人研究兴趣为范围；合作项目的 We 不单独确立实验室身份。
- 所列有限元、无网格方法及计算主题均为个人研究背景，不能当作已确认实验室的整体方法或方向。
- 页面未给出带日期的独立实验室当前归属声明。
- Blocker：personal_page_not_lab_identity

新源语义指纹：0472f8f37f889f60c9b08a107549106fe6ceaa00ea6a5ede7cd21305ec308c93。

## 531 — Language and Cognition Lab

ID：ucsd-live-lab-a463fe964995c8。决定：changed；partial → supported；实体类型：lab → lab。

具名新实验室正文提供明确全组研究问题及实验/计算/行为/统计方法，partial升级supported；HTML meta refresh与HTTP终点分别保存。

Language and Cognition Lab 研究语言知识与使用背后的认知过程，以及语言形式、意义及两者的关系，具体关注大语言模型、歧义消解和具身模拟。实验室采用实验与计算方法，并用行为和统计技术研究词汇、句法及语用歧义。

新来源（原始观察时间与字节hash）：

- [Language and Cognition Lab](https://langcoglab.ucsd.edu/)；observedAt 2026-10-16T03:18:31+00:00；sourceId src-8d7756e3f686b8e9；SHA-256 b9acc236ba1a366610e78a3f66bbe72962a89d8e596dc3ea0c3b49990039f522；完整正文 5118 字符已读。

字段证据：

- identity：[src-8d7756e3f686b8e9](https://langcoglab.ucsd.edu/) — “Language and Cognition Lab”
- research, topics, methods：[src-8d7756e3f686b8e9](https://langcoglab.ucsd.edu/) — “We study the cognitive processes that underlie language knowledge and use, using both experimental and computational approaches. Our research addresses linguistic meaning, form, and the relation between them.”
- research, topics：[src-8d7756e3f686b8e9](https://langcoglab.ucsd.edu/) — “Large Language Models Large computational language models are beginning to approach human competence in a variety of tasks. What do their successes and failures teach us about how humans learn and use language?”
- research, topics, methods：[src-8d7756e3f686b8e9](https://langcoglab.ucsd.edu/) — “Ambiguity Why is language so ambiguous? How do we resolve ambiguity when we encounter it? The lab conducts work on lexical, syntactic, and pragmatic ambiguity using behavioral and statistical techniques.”
- research, topics：[src-8d7756e3f686b8e9](https://langcoglab.ucsd.edu/) — “Embodied simulation for language comprehension How do comprehenders interpret and encode the meaning of the language they’re exposed to? Part of the answer might be that they use sensorimotor systems to activate and enact the sights, sounds, and actions that the language describes and implies. This is the embodied simulation hypothesis, explored in the work below, among many other papers from the lab.”

具体边界：

- 原listed URL的HTTP终点仍为 pages.ucsd.edu 的空正文HTML导航页；其中meta refresh仅用于发现新目标，不是到 langcoglab.ucsd.edu 的HTTP重定向。
- 新目标页以具名实验室、We及The lab明确描述研究；页面没有提供统一的当前研究生效日期，论文年份不等于全站更新时间。
- 官方历史名录将该实验室关联为Benjamin Bergen负责；没有据新页回填或重命名原始ID、listed URL。

新源语义指纹：8e1e6c62f2a74fb001fa206ed0a3df6bcea7c8b3e61aa8714e2037036320a8d7。

## 535 — Long Lab

ID：ucsd-live-lab-6c899e2fd695ff。决定：changed；partial → partial；实体类型：personal_research_site → personal_research_site。

新研究页支持个人项目概述，但没有Long Lab全组作用域；保持partial与个人研究站类型。

Bria Long 的个人 Research 页探讨儿童绘画如何反映视觉概念，以及婴儿日常视觉输入如何影响早期学习；其中举例分析儿童数字绘画和婴儿第一人称视频。该页混合个人既往与合作项目，尚不能确认为 Long Lab 当前的整体研究范围。

新来源（原始观察时间与字节hash）：

- [Research | brialong](https://www.brialong.com/research)；observedAt 2026-10-16T03:17:55+00:00；sourceId src-b7166b4a3a42b0c1；SHA-256 a190edf9ace98a6703f35c55469e1b70ec7a779ade19849efb35f8b7aec9425a；完整正文 10299 字符已读。

字段证据：

- limited_personal_research_context：[src-b7166b4a3a42b0c1](https://www.brialong.com/research) — “What might children’s drawings reveal about how they represent the visual concepts in the world around them?”
- limited_personal_research_context：[src-b7166b4a3a42b0c1](https://www.brialong.com/research) — “For this project, I collected over 37,000 digital children’s drawings behaviors via an iPad interface, and analyzed the category-diagnostic information in these drawings using both embeddings from deep neural networks and human annotations of the recognizable object parts in each stroke.”
- limited_personal_research_context：[src-b7166b4a3a42b0c1](https://www.brialong.com/research) — “This line of work records and analyzes videos taken from the infant perspective with modern computer vision models, aiming to understand the natural structure in the visual input and how this structure scaffolds early learning.”

具体边界：

- 新增页面为Bria Long个人Research记录，包含既往、硕士及合作研究；没有把这些项目自动归为Long Lab当前研究。
- 全组研究问题、主题及方法未明确，因此这些结构化字段留空。
- 原个人根页明确将实验室页面另指向vislearnlab.org；本次未读取新站，不能仅凭该链接接受其名称或实体关系。
- 个人任职和旧名录是来源报告关系，采集时间不构成带日期的当前实验室任职证明。
- Blocker：personal_page_not_lab_scope

新源语义指纹：0f5c39a1832cc1c336c9f926ece16d0a345fd7b83a36ffd746ac3e34acfcd2b1。

## 549 — Miroslav Krstic — lab website

ID：ucsd-live-lab-79f8d7df25e8a2。决定：unchanged；partial → partial；实体类型：personal_research_site → personal_research_site。

新Research页全文953字符，主要为个人论文、书籍、访谈、Wikipedia及学生链接；没有可用于确认具名lab/group或全组研究/方法的正文。旧编码损坏与身份边界仍适用，raw不重写。

缓存中可恢复的个人主页文字以非线性与自适应控制为主题，并列出非线性控制、极值寻优、偏微分方程与时滞控制、流动控制等著作方向；页面未明确界定独立实验室或团队的研究范围。

新来源（原始观察时间与字节hash）：

- [Miroslav Krstic - Nonlinear and Adaptive Control](https://flyingv.ucsd.edu/krstic/Research.html)；observedAt 2026-10-16T03:18:32+00:00；sourceId src-6524077b72d9311a；SHA-256 d5b21bd94b4ef00ed2e143e395cab305b1d20cff58510349691d24ab0713f212；完整正文 953 字符已读。

字段证据：

- 新来源没有可采用的实体范围正文，未新增证据；原有身份/研究边界保持。

具体边界：

- 原始缓存已被旧采集器重编码并含替换字符；仅恢复仍存的 ASCII HTML，损失的字形未重建，原始哈希与观察时间不变。
- 主页列出的著作与教师个人研究不能自动作为独立实验室主题或方法。
- 来源未提供带日期的现任任职声明；采集时间不等于任职生效时间。
- Blocker：destination_encoding_corruption；no_explicit_lab_identity

新源语义指纹：91028af5e9a22bfecb3e981eacdfc0f009fcb682d0be7cc315a940e57dc5e6a9。

## 583 — Microcirculation Laboratory

ID：ucsd-live-lab-d2d234fc0f3eba。决定：changed；partial → partial；实体类型：unconfirmed → unconfirmed。

新About正文明确历史实验室/UCSD及主任关系，新Research列出主题；保留全部mismatch/acceptanceStatus/proposed-correction门槛，维持partial，不宣称更名或继承。

新抓取的 About 页记述 UCSD Microcirculation Laboratory 于1967年创建，Geert W. Schmid-Schönbein 于1979年接任主任；其研究前提是疾病在临床显现前多年即可在微循环中出现。该站 Research 页列出自体消化与衰老、脓毒症和失血性休克、代谢病中的受体裂解，以及婴儿未成熟肠道等主题。这些信息仅暂记为该站研究背景，仍缺实验室与首页 Center for Autodigestion Innovation 的明确实体关系声明。

新来源（原始观察时间与字节hash）：

- [Microcirculation Laboratory - Research](https://sites.google.com/ucsd.edu/microcirculation-autodigestion/research)；observedAt 2026-10-16T03:18:07+00:00；sourceId src-2cfa0c7eb6f41856；SHA-256 d59fbc04b16d21c74841bfd9a40ad576b92168107c74ca69987d2191eeac1bcd；完整正文 551 字符已读。
- [Microcirculation Laboratory - About Microcirculation](https://sites.google.com/ucsd.edu/microcirculation-autodigestion/people/about-microcirculation)；observedAt 2026-10-16T03:18:08+00:00；sourceId src-f0daecda23e6613e；SHA-256 6a133493a88b67182ff086041c9169d03a624302457f784ecfc27c2c5ad520ec；完整正文 853 字符已读。

字段证据：

- identity, historical_affiliation：[src-f0daecda23e6613e](https://sites.google.com/ucsd.edu/microcirculation-autodigestion/people/about-microcirculation) — “The Microcirculation Laboratory at UC San Diego was founded in 1967 by the late Benjamin W. Zweifach, one of the imminent teachers of Bioengineering and Microcirculation in the twentieth century. In 1979, Geert W. Schmid-Schönbein assumed the directorship of the laboratory.”
- research：[src-f0daecda23e6613e](https://sites.google.com/ucsd.edu/microcirculation-autodigestion/people/about-microcirculation) — “A premise of the laboratory is that diseases are manifest in the microcirculation years before they become evident at the clinical level. The study of microcirculation is a cornerstone for the integration of molecular, genetic, and cellular phenomena with the dynamics in living tissue and whole organs. Microcirculation is a key to analyzing the origin and progression of disease.”
- provisional_research, topics：[src-2cfa0c7eb6f41856](https://sites.google.com/ucsd.edu/microcirculation-autodigestion/research) — “Microcirculation Laboratory Research Summary Aging by Autodigestion A Fundamental Mechanism for Loss of Cell and Tissue Function over a Lifetime Autodigestion in Sepsis and Hemorrhagic Shock Multiorgan Failure by Digestive Enzymes Metabolic Disease and Receptor Cleavage Loss of Receptor Signalling by Digestive Protease and Secondary Proteases. The Immature Intestine of Infants A Risk for Autodigestion & Potential Connection to Necrotizing Enterocolitis and Autism”

具体边界：

- About页明确1967年建所及1979年主任更替，这些是来源所述历史事件，不能据采集时间改写为2026年现任声明。
- Research/About正文提供暂定实验室研究背景，但没有解释该lab与首页Center for Autodigestion Innovation的更名、继承或共同实体关系。
- 方法未明确；分子、遗传、细胞与整体器官层次的概念说明不单独证明采用特定实验技术。
- 本次只读取共享适配器已抓取的Research/About缓存；原listed首页未在本轮重取，HTTP终点及旧观察时间保持。
- Blocker：Microcirculation Laboratory、Schmid-Schoenbein Lab与Center for Autodigestion Innovation之间的更名、继承或共同实体关系仍缺少明确官方正文；新增实验室历史与研究主题不解除不接受的身份门槛。

新源语义指纹：efbd236a55e536e057c078c4d94b7794812f6b044916dbc861dc82adc815968b。

## 599 — The SWAG Lab

ID：ucsd-live-lab-dc77b90e91d80c。决定：changed；partial → partial；实体类型：personal_research_site → lab。

同站具名成员页把SWAG Lab与Janna Dickenson PI明确关联，身份类型可从personal_research_site改为lab；新增研究页仍仅PI研究经历，维持partial。

新成员页明确确认 Sexual Wellbeing and Gender（SWAG）Lab，以 Janna Dickenson 为主要研究者。Research 与 SWAG Lab 页面叙述她对性取向及其变化、当下注意与性反应和愉悦的研究经历，但尚未给出明确属于全组的研究范围或方法概述。

新来源（原始观察时间与字节hash）：

- [Dr. Janna Dickenson - Research](https://dickenson.ucsd.edu/research)；observedAt 2026-10-16T03:18:33+00:00；sourceId src-676531a01f940034；SHA-256 5283d9434a4f9be38f24bc41c754575efb1e50fe09f04f99f3ffdf1771b3b3da；完整正文 2641 字符已读。
- [Dr. Janna Dickenson - SWAG Lab](https://dickenson.ucsd.edu/research/swag-lab)；observedAt 2026-10-16T03:18:02+00:00；sourceId src-260c1d753e0d5f5c；SHA-256 406965fe5ac97ea4d9acb58ef86174e36dae9fb4f3e7fd0806640621f851a732；完整正文 2641 字符已读。
- [Dr. Janna Dickenson - SWAG Lab Members](https://dickenson.ucsd.edu/research/swag-lab-members)；observedAt 2026-10-16T03:18:03+00:00；sourceId src-ae304e2bd358f93b；SHA-256 cb6567d8dc935cb20bc6605cd46ed069a5cf3d8eece100e721b2d3423dc38084；完整正文 6598 字符已读。

字段证据：

- identity：[src-ae304e2bd358f93b](https://dickenson.ucsd.edu/research/swag-lab-members) — “Sexual Wellbeing and Gender ( SWAG ) Lab Meet Our Team Janna Dickenson, PhD, LP Principal Investigator”
- limited_personal_research_context：[src-260c1d753e0d5f5c](https://dickenson.ucsd.edu/research/swag-lab) — “By using research to discover truths about sexuality, Dr. Dickenson has challenged the veracity of intuitive claims about sexuality (e.g., Sex during youth can be good! Sexual orientation exists! Sexual orientation can change, but you cannot control that change!) and has demonstrated just how important present-moment attention actually is for sexual response and pleasure.”

具体边界：

- 成员页确认具名lab及PI；Research/SWAG页的研究经历仍以Dr. Dickenson为主语，尚缺全组研究概述。
- 方法未明确；没有从成员个人兴趣、正念训练经历或所列论文题目推断全组方法。
- 成员页写明最后编辑于2025年12月19日；官方个人档案标注Updated October 2020，均与本次采集时间分开。
- 机构关系来自PI个人根页明确的UCSD心理学任职陈述，不据采集时间宣称2026年的现任或全组统一归属。
- Blocker：named_lab_and_PI_confirmed_but_research_prose_remains_PI_scoped

新源语义指纹：bde4eb9bdbd796a94900fb492f17e4188fbfce6e8e56fbcd0f24043302b8c8af。

## 保存边界

- 531的原listed URL只观测到HTTP 302至pages.ucsd.edu；该页的HTML meta refresh指向langcoglab.ucsd.edu，用于发现并单独读取新目标。未将meta refresh写成HTTP重定向，原listed URL不因此计作已核验lab URL。
- 583继续mismatch / unresolved_entity_relationship，silentIdMigrationAllowed=false；候选更名/继承关系未应用。新About页的1967/1979历史不能解除13条权威不接受门槛。
- 549新页主要为个人资源链接且仍有编码损坏；没有据此重写raw或猜测研究方法。
- 515完整缓存26587字符已逐段读完；packet仅保留前18000字符，本次所有采用引文均在packet中，无需借用未入packet的文本。
- 所有7条packet写入前后字节hash一致；没有prepare、checkpoint、聚合、collector或代码写入。
