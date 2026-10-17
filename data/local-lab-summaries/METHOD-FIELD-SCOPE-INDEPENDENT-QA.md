# 方法字段提案独立QA

结论：PASS；须同时采用固定225术语addendum。实际完成：2026-10-16T08:51:19+00:00。原文范围初审时间另保存在JSON，不覆盖初审时间。

8/8完成：6条新增有明确范围的方法，2条撤下仅兴趣支持的方法；15个方法条目、9条新引文、3处旧supports重分类均通过。8个旧raw快照逐对象一致，raw/packet冻结SHA一致。17个source对象中16个实际HTML及原sidecar的SHA、URI、finalURL和observedAt均匹配（15个不同HTML文件）；唯一历史目录摘录缺原bodySHA，只用于撤销methods标签。

| index | QA及边界 |
|---|---|
| 120 | pass。负责人当前research program明确采用mouse models、genetic及neuroanatomical manipulations；chemogenic为原拼写，不将其擅改为chemogenetic或外推为全员方法。 |
| 190 | pass。Interests仅列Optogenetics/Pharmacology/Physiology/Animal Models；不充分证明实际采用，可移除methods并保留为兴趣语境。 |
| 225 | pass_with_resolved_terminology_addendum。根页及About整体/个人/成员语境此前同体完整审阅；Jacobs内容明确Interests for the research group，未明确实际方法采用。 |
| 349 | pass。About明确主要human studies，animal models仅when appropriate，适当保持条件范围。 |
| 364 | pass。组成员参与项目中BICEP1 2006–2008、BICEP2 2010–2012历史观测，CIBER近红外背景火箭测量；不可断言2026各方法均在运行。 |
| 377 | pass。具名Zhang laboratory明确结合遗传编码荧光传感器、超分辨成像、靶向生化扰动和数学建模，whole-lab研究方法句。 |
| 379 | pass。GEE用于气候/迁移暴露项目；RCT为BPCARE；qualitative community-engaged为移民痴呆照护项目；成员个人履历方法不采。 |
| 382 | pass。We generated SVR model为2020已有工作（人DPR及TATA核心启动子），应作所述既有工作而非新增观察或全团队普遍方法。 |

已解决225术语：摘要仅将随机建模改为随机学习，贴合具名group的stochastic learning；methods仍为空。

proposalSha256：`3248021953a5483a17d1afc9189e626ffa0278209f6a5fb7462b6769d4cc2980`。
terminologyAddendumSha256：`7c2aabb5262160c10b4fcd4c5e8e2cea9a4ee741f29206123315d1d10a6ee9af`。

必要摘要与不确定性改动均仅修复方法状态/项目日期/人群范围；旧literal quotes和source IDs不删改，3处supports重分类索引、旧标签与完整旧引文逐字匹配。科研引文与来源原日期不变。

应用须保存完整旧记录并按字段重基；若问题批次先写入新问题，禁止用提案oldRecord覆盖。独立QA未运行应用helper。

0网络、0PS、0raw/packet/code/collector/shared写入。仅更新本QA报告pair。
