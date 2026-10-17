# 方法字段作用域审阅提案（未应用）

实际审阅时间：2026-10-16T08:46:04.756Z。8项完成：6项建议补充有明确采用语境的方法，2项建议撤下仅由兴趣清单支撑的方法；共15个拟议方法条目、9条新方法引文、3处旧证据标签重分类。

本次仅审指定字段及相关primary缓存全文/局部语境。未请求网络、未运行PS，未改raw、packet、代码、collector或共享状态。JSON保存每条冻结SHA、完整旧raw、字面引文、局部位置、原时间/体哈希、实际阅读范围和字段级应用要求。

| reviewIndex / 实体 | 建议 | 关键作用域与修订 |
|---|---|---|
| 120 Breen Church | 小鼠模型（负责人研究项目）；遗传学操作（负责人研究项目）；神经解剖学操作（负责人研究项目） | 具名实验室成员页明确负责人研究项目employs遗传与神经解剖操作及小鼠模型，足以补全实际方法。早期生命编程是研究主题，不能支持methods。保留原拼写chemogenic但不翻译成未证实的chemogenetic。摘要将原“男女”改为中性生殖表述，避免把跨模型来源限定为人类。 |
| 190 de Guglielmo | methods置空 | 原4方法仅见Interests清单；Overview明确问题范围，但不叙述这4方法的采用。已读同页新闻段，报道和生物库资源简介不被机械转换为原4方法的采用证据。保留整段旧literal quote，只移除其methods标签。 |
| 225 Coimbra | methods置空 | 已完整读3704字About：组/PI介绍、出版主题、履历、编辑经历和成员名单，没有补足3方法的实际采用。Faculty profile明确Interests for Coimbra’s research group，不以出版主题或兴趣清单认定实际方法；旧引文保留并由methods改topics。 |
| 349 Zuraw | 人类研究；动物模型（按需使用） | About页直接描述实际研究模式；仅采基本类别，不添加临床试验设计、动物种属或技术。 |
| 364 Experimental Cosmology | 宇宙微波背景偏振测量（BICEP1：2006–2008；BICEP2：2010–2012）；火箭载近红外背景测量（CIBER项目；观测年份未明） | 实际项目仪器与测量用途可补基本方法；历史年份必须进入方法和摘要，不把Current Projects标题当2026在用证明。Simons拟部署描述未转为已采用方法。 |
| 377 Jin Zhang | 遗传编码荧光生物传感器；超分辨率成像；靶向生化扰动；数学建模 | 正文具名Zhang laboratory与实际结合的4方法直接绑定，应补方法并移除摘要中方法未知说明。保留原文Combing拼写，不作为术语新增。 |
| 379 Al-Rousan center | Google Earth Engine回溯暴露量化（气候暴露与心血管健康项目）；随机对照试验（BPCARE难民高血压自我管理项目）；社区参与的定性研究（加州痴呆移民照护项目） | 中心完整项目语境分别明示实际采用方法，按项目收录而不把它们推广到中心所有研究。保留现center_or_institute类型，未改为lab。 |
| 382 Kadonaga | 支持向量回归（SVR）建模（已报告的人类DPR和TATA盒研究） | 明确we generated的既有SVR工作足以支持方法，必须限定已报告项目。采用原已接受HTTPS科研source及原时间，不借同body较晚HTTP来源重计日期。 |

需要同时修订的证据标签：120的“Early life programming of delayed or deficient fertility.”保留research/topics、去掉methods；190的完整旧首页引文保留research/topics、去掉methods；225的完整旧faculty引文由methods改为topics。引文与sourceId不删除或改写。

原始来源核验：17个相关source对象中，16个有原HTML及sidecar，实际SHA256、原observedAt及URI全部匹配；Breen历史目录摘录缺原HTML，仅用于移除错误methods标签，不充当新方法证据。8个raw及8个packet的冻结SHA在写报告前再次一致。

主要方法证据来源（日期是原始采集时间，不是研究发生时间）：

- 120 [src-aa57c545809ceb23](https://obgyn.ucsd.edu/research/labs/breen-church/people.html)，2026-10-16T02:40:25+00:00。Breen Church Lab Members的Current Lab Members段，明确标作Kellie Breen Church Professor的本人研究项目；不扩张为所有成员均采用。
- 190 [src-61dd53e008e3f7b0](https://www.deguglielmolab.com/)，2026-10-16T01:03:03+00:00。仅兴趣语境，不作为方法采用证明。
- 225 [src-c568ff8ba8100d18](https://jacobsschool.ucsd.edu/faculty/profile?id=324)，2026-10-16T01:00:15+00:00。仅兴趣语境，不作为方法采用证明。
- 349 [src-2c7cc431b7bd43c2](https://allergyimmunology.ucsd.edu/research/faculty-labs/zuraw/about/index.html)，2026-10-16T01:36:01+00:00。Zuraw实验室自身About页直接描述the laboratory的主要研究方式及按需采用的动物模型。
- 364 [src-f6888c5fa8e5266d](https://cosmology.ucsd.edu/projects.php)，2026-10-16T02:41:45+00:00。组成员参与项目页明示BICEP1/2偏振仪及CIBER火箭测量；方法只限所列项目。
- 377 [src-271c791f9dc5e0fe](https://pharmacology.ucsd.edu/faculty/department-faculty1/jin-zhang.html)，2026-10-16T01:00:45+00:00。虽位于faculty的Research Interests栏，正文明确the Zhang laboratory is investigating并列出组合采用的方法，具备实验室作用域；不只是PI兴趣清单。
- 379 [src-d2c5472cd723bb1f](https://hwsph.ucsd.edu/research/programs-groups/al-rousan-lab.html)，2026-10-16T01:07:32+00:00。中心项目Climate-Related Exposures and Cardiovascular Health的team使用Google Earth Engine回溯迁移轨迹暴露。
- 382 [src-4cdf2e8fbc6dcb8c](https://biology.ucsd.edu/research/faculty/jkadonaga)，2026-10-16T01:07:32+00:00。In my lab所述核心启动子研究的已报告工作，we generated明确实际建模。
- 225另完整读取[About页](https://coimbra.ucsd.edu/about)，3704字符，原采集2026-10-16T01:34:35+00:00；出版主题、履历和成员介绍未补足3项实际方法采用。

120只收小鼠、遗传、神经解剖3项，不把原文chemogenic改写为chemogenetic。364将BICEP1/2分别限定2006–2008和2010–2012历史观测，CIBER年份未知；377由具名Zhang laboratory实际结合方法的句子支持。379按3个具体中心项目收录，不宣称整个中心统一采用，也不声称RCT疗效已经证实。382限定已报告的人类DPR/TATA盒SVR工作及2020年文献语境，不宣称当前唯一方法或新发现。

应用须保存完整旧raw及SHA；按字段重基，保留问题批次中新问题及所有科学/URL身份历史。只替换拟议methods、必要摘要/不确定性，追加新方法证据，并实施列明的3处supports重分类。实体、身份、隶属、PI、topics、questions、root/fetch/canonical与来源日期均不变。此报告没有应用任何提案。
