# 恢复根页面正文复核：033、035、036

实际复核时间：2026-10-16T04:09:27+00:00（UTC）。仅复核父代理恢复包中的三个 newSourceId；完整正文均未截断，已逐一核对原始缓存字节哈希、队列原观测时间、实际请求 URI、最终 URL 和 sourceId。3 条记录均由 unresolved 升为 supported，hydrate 全部通过。复核网络请求为 0；只改三条 raw records 与本 Markdown/JSON 报告，未改包、代码、聚合、共享状态或收集器。

## 33 — Muroyama Lab

新增正文明确 Muroyama Lab、We are a group 和 Our Research，支持植物细胞位置、组织/器官形成及途径保守性的实验室整体研究；字面方法为 live-imaging、genetics、proteomics。新摘要没有从名称或学科常识补方法。研究正文没有明确机构隶属句，故 affiliation 保持 uncertain；UCSD 站点页头与域名不替代带日期的实验室归属声明。

## 35 — Axel Nimmerjahn

这是 Salk 人物页，但 The Approach 不只是本人兴趣：正文明确 his lab 将显微镜微型化为可穿戴设备，they 开发细胞类型特异性染色、遗传操控和大规模成像分析工具，并据此研究健康/患病 CNS 中胶质细胞作用；另有明确 Nimmerjahn’s lab 句。因此实验室身份与上述整体研究范围有支持。未将背景章节罗列的全部疾病、本人过去发现或单一项目概括为当前全实验室研究。机构记 external，依据 Salk Institute / Waitt Center 的字面任职及团队语境，不当作当前 UCSD 实验室；现任日期仍未确认。

## 36 — GrantLab

新正文明确 GrantLab、Our research、The Grant lab，支持生物大分子结构/功能/演化、分子马达/开关、计算模拟、结构生物信息学与药物设计，也明确 Bio3D 软件开发。UCSD Molecular Biology / Biological Sciences 归属有字面陈述，记 source_reported 而非带日期的当前机构确认。HTML canonical 的 localhost:4000 是页面自声明元数据，未作为公共网址迁移、别名或 HTTP 重定向接受。

## 原始来源与时间

| Ordinal / ID | 新原始来源 | observedAt（UTC） | sourceId | SHA-256 |
|---|---|---|---|---|
| 33 `ucsd-biology-topic-lab-andrew-muroyama` | [https://muroyamalab.biosci.ucsd.edu/](https://muroyamalab.biosci.ucsd.edu/) | 2026-10-16T03:47:25+00:00 | `src-4c17d2b53a3645c1` | `2e42414e3523defcf0d2fe402a9e1b401af9c8bfb501dfd83b84a5d4adfb8e04` |
| 35 `ucsd-biology-topic-lab-axel-nimmerjahn` | [https://www.salk.edu/scientist/axel-nimmerjahn/](https://www.salk.edu/scientist/axel-nimmerjahn/) | 2026-10-16T03:47:25+00:00 | `src-f8b1728f4e2e382c` | `ec64fa28143f9b2198a0ba1e281a65d2c927dce6242db41755daff52ba000ea8` |
| 36 `ucsd-biology-topic-lab-barry-grant` | [http://thegrantlab.org/](http://thegrantlab.org/) | 2026-10-16T03:47:24+00:00 | `src-a53c90d169459382` | `59dc80ee1c4ddb428edcc6e299d108caab7fb0dc1afa36ad9e595b1036c8dc9f` |

原三条 records 没有旧引文可丢失；原访问失败历史与“失败不能证明关闭”的限制保留。新增正文使原“无正文/方法未知”判断失效，因此以新精确证据替换，并将完整 beforeUncertainty 作为历史写入 JSON。采集时间不当作正文更新时间、机构或任职生效日。三条稳定 ID、原列出 URL、真实请求/HTTP链和 packet preparedAt 均未编辑，没有应用别名。JSON 逐 ID 包含 before/after、原来源 tuple、精确引文、scope/身份/机构理由、实际复核时间、0 requests 与语义内容指纹。
