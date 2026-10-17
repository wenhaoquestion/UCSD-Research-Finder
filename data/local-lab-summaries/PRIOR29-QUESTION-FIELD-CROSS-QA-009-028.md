# 原29条后20项问题字段交叉QA

结论：PASS。完成于2026-10-16T08:40:39+00:00。仅覆盖recheckIndex9–28，未重复前9项。

20/20项：4条新增4问、16条保留空字段；78个来源绑定及20组冻结raw/packet SHA全部匹配。4问逐字引文、原observedAt与bodySHA元数据正确，团队范围明确，无疗效或当前状态扩写。

新增问题分别为Functional Neuroscience Lab的EEG神经反馈与工作记忆影响、George团队药物成瘾机制、Telese团队组织/细胞特异性基因调控机制，以及Poulikakos Lab机械/化学/热效应与光学性质。

16条unchanged具体理由与所列读取范围合理；个人My/I/PI研究、新闻或论文标题、FAQ和工具开发目标没有被机械转为whole-lab问题。Ribozymes完整team文字仍将生命起源设想归于个人，不恢复已收窄范围。

历史边界：Telese src-bf0d3d4d9d0da7c0是2026-10-07T22:05:47+00:00的官方关联研究摘要，原bodySHA为null。完整Our laboratory/Our approach/aim机制句可支持问题，保留null与旧时间，不冒称原HTML复核。

固定原草案SHA：`82ba1f2dd6d8dfcdc1fe0f1f8d7dce51a86fbb20030cdf79778a3008d37b9c6a`。inventory SHA：`d9c7ca4fb9fa09c29460d4c9549fc6f8296bf3ab1932cc730d43fa3ad2858e94`。

0网络、0PS、0生产数据写入。全部独立QA实际字符范围见JSON，未列范围不宣称全文阅读。

| recheckIndex | 实体 | QA |
|---|---|---|
| 9 | Duarte Lab | pass；已核对明确的实体科研介绍、原草案排除理由和实际覆盖元数据；未将新闻、个人兴趣、主题或工具开发机械转换为整体研究问题。 |
| 10 | M. Brian Maple Research Group | pass；已核对明确的实体科研介绍、原草案排除理由和实际覆盖元数据；未将新闻、个人兴趣、主题或工具开发机械转换为整体研究问题。 |
| 11 | CNS Laboratory of Memory and Brain | pass；个人My focus/I use/My goal未升级为whole-lab问题；目录只验证名称。 |
| 12 | Functional Neuroscience Lab | pass；EEG神经反馈影响的对象与两个人群均在当前研究主文明确；排除神经反馈定义FAQ和试验招募状态，不作疗效判断。 |
| 13 | Olivier George — lab website | pass；We identify neurobiological mechanisms为团队目标；未采用历史时间线和新闻标题。 |
| 14 | NSTAR Lab | pass；已核对明确的实体科研介绍、原草案排除理由和实际覆盖元数据；未将新闻、个人兴趣、主题或工具开发机械转换为整体研究问题。 |
| 15 | Telese Lab | pass；Our laboratory/Our interdisciplinary approach和aim to dissect完整承接，机制范围对应；历史bodySHA空值须如实保留。 |
| 16 | Twamley SMART Lab | pass；how为训练策略教学流程；开发和评价干预未明示具体假设，空字段理由合理。 |
| 17 | Moore Lab | pass；已核对明确的实体科研介绍、原草案排除理由和实际覆盖元数据；未将新闻、个人兴趣、主题或工具开发机械转换为整体研究问题。 |
| 18 | Sharabi Lab | pass；lab页仍以Dr. Sharabi/he个人研究叙述，未据其过往论文/临床PI身份转整体问题。 |
| 19 | Front Page / Mobile Systems Design Lab | pass；已核对明确的实体科研介绍、原草案排除理由和实际覆盖元数据；未将新闻、个人兴趣、主题或工具开发机械转换为整体研究问题。 |
| 20 | Goldenfeld Group | pass；Goldenfeld个人兴趣how与历史Group标题不自动构成整体问题。 |
| 21 | HXI Research Lab | pass；已核对明确的实体科研介绍、原草案排除理由和实际覆盖元数据；未将新闻、个人兴趣、主题或工具开发机械转换为整体研究问题。 |
| 22 | Kate Ricke ☁️ Ricke Lab @ UCSD | pass；已核对明确的实体科研介绍、原草案排除理由和实际覆盖元数据；未将新闻、个人兴趣、主题或工具开发机械转换为整体研究问题。 |
| 23 | Laboratory for Energy Storage and Conversion | pass；已核对明确的实体科研介绍、原草案排除理由和实际覆盖元数据；未将新闻、个人兴趣、主题或工具开发机械转换为整体研究问题。 |
| 24 | Lagrangian Drifter Laboratory | pass；已核对明确的实体科研介绍、原草案排除理由和实际覆盖元数据；未将新闻、个人兴趣、主题或工具开发机械转换为整体研究问题。 |
| 25 | Lisa Poulikakos — lab website | pass；具名Poulikakos Lab明确how及can模态，问题未外推诊断疗效。 |
| 26 | Machine Learning, Perception, and Cognition Lab | pass；已核对明确的实体科研介绍、原草案排除理由和实际覆盖元数据；未将新闻、个人兴趣、主题或工具开发机械转换为整体研究问题。 |
| 27 | S2ML lab | pass；已核对明确的实体科研介绍、原草案排除理由和实际覆盖元数据；未将新闻、个人兴趣、主题或工具开发机械转换为整体研究问题。 |
| 28 | Ribozymes | pass；完整team来源中I believe生命起源、地球化学及宇宙生物问题为PI设想；We段为治疗核酶开发和定向进化，未恢复先前被收窄的个人问题。 |
