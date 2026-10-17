# 剩余 Profiles 概述范围复核

复核时间：2026-10-16T06:24:07+00:00。0网络请求；2份实际历史Profiles完整主文本已读，3个稳定ID逐项审阅。未编辑records、packets、代码或collector。

| 稳定实体 | 原始capture（UTC） | 结果 |
|---|---|---|
| 619 Hamilton Lab / `ucsd-live-lab-493c2d3c113de8` | 2026-10-07T22:02:57+00:00 | 完整1149字符概述含明确实验室主体；具名Hamilton Lab锚点精确对应原URL，可恢复实验室研究 |
| 620 Hamilton Lab / `ucsd-live-lab-cd8819aec34b38` | 同一实际capture | 另一具名Hamilton Lab锚点精确对应此编辑站原URL；独立ID保留，不合并 |
| 294 Aaron Carlin Lab | 2026-10-07T22:17:28+00:00 | 完整1177字符概述仍为个人研究主体，不能据此恢复wholelab研究；实际Lab Website锚点为HTTP |

[Hamilton Profiles](https://profiles.ucsd.edu/bruce.hamilton)的原始HTML SHA为 `9ff4279cc7fc83c9302f07bbc24e292b62203511d203713182da21ef0950382e`，sidecar SHA为 `e6fb145fca6a8b6b27a6f96db0bd0fc16f5c176c5d9a7c62e679966a2fac074f`。旧900字符是同一时间/URL完整overview的精确前缀，不是当时页面缺失正文。完整字面句：“His laboratory is interested in genetic control of neural development, modifier gene networks, and genetic variation in neural control of blood pressure.” 研究可简述为神经发育的遗传调控、修饰基因网络及血压神经调控的遗传变异。方法为空；前文博士/博士后经历的方法不归给实验室。未借经费、论文或个人任职补充科学或机构结论。

两条Hamilton Lab的实际href分别逐字对应两个原listedURL。来源支持实体与研究映射；原healthsciences robots重定向前置失败、edithealthsciences DNS前置失败继续保留。关联官方profile不能验证两个根页面，不能提升其URL verified，也不合并ID。候选完整v2 sourceId为 `src-f36a14458458298d`；parent授权的自有不可变HTML/sidecar副本逐字节核验，见JSON snapshot contract。

[Carlin Profiles](https://profiles.ucsd.edu/aaron.carlin)的原始HTML SHA为 `7489a5991ca6230a27e2051274abd7ad56014a37dbc5f090cb8f0fd57f4861cc`，sidecar SHA为 `ff236a6a55d38647a78622e2ac6cea5ab082f8e9ac74942665a75f19bad477f3`。旧900字符同样是完整概述的精确前缀，但完整主体仍是Dr. Carlin、His approach、Dr. Carlin aims；没有实验室整体科研段落。个人抗病毒/髓系细胞机制研究、关键词NGS及资助项目不能变成该实验室研究或方法。

Carlin Lab Website实际href为 `http://homer.ucsd.edu/CarlinLab/index.html`；旧字段是HTTPS。应保留旧字段历史并独立记录真实HTTP关联，不静默覆盖或推定重定向。原HTTPS robots TLS失败仍然独立有效；本文没有新的直接根请求或实验室页面身份证据。

完整overview均直接位于 `div[id="http://vivoweb.org/ontology/core#overview"]` 普通DOM文本，节点只有padding样式；没有ReadMore/Fulltext载荷需要执行，也未从script恢复科学内容。主文本分别3896/4057字符，bibliography未作为研究依据。当前collector二profile均为retained_prior_evidence、attempts=0，无本轮fetch；真实capture由原始sidecar证明，不用mtime、队列更新时间或报告时间替代。

既有assessment ledger只把三个根页面记录为无可用HTML，旧raw仅按900字符审阅；未发现这两份完整body的既有语义指纹。本次新指纹含稳定ID、exact listedURL、原始capture URL/time/SHA及实际决定。具体selector、全文overview、精确anchor、原始sidecar、候选证据和snapshot文件路径见同名JSON。
