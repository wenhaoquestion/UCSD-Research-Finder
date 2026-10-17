# Parent group-cache QA

独立审阅时间：2026-10-16T03:09:28+00:00。范围：105、131、381、511、717、820、864、875。只写本报告；无网络、无raw/packet/supplemental/代码/聚合/采集器修改。

未发现否定5项研究升级的实体或研究作用域问题。Tongyan Lin、Ndao保持partial与Kendrick保留mismatch合理。

## Actionable concern

此前Budin应用目标引文覆盖缺口已由parent修复；raw现已在src-c6deef290f2cbc9e下包含精确子句“which we then apply for fundamental discovery and applications in health and biotechnology.”，raw reviewedAt为2026-10-16T03:08:19+00:00。本次独立重读已确认；没有剩余问题。

## Per-ID findings

| ordinal / stable ID | 状态 / 类型 | 独立判定 |
|---|---|---|
| 105 / ucsd-biology-topic-lab-not-in-a-biology-group | partial / unconfirmed | 保留partial/mismatch正确。Team页标题仍是Kendrick Lab/Salk，Aga的UCSD经历明确是过去博士后；成员含UCSD学生不构成原错误类别标签到Kendrick lab的身份接受。 |
| 131 / ucsd-biology-topic-lab-suel-gurol | supported / lab | 支持升级。官方Matsci正文直接写Dr. Süel’s lab，并将quantitative biology和跨尺度mathematical modeling用于该lab；同站People页列Gürol M. Süel，Contact写UC San Diego Suel Lab，官方Lab Website真实指向同一根站。 |
| 381 / ucsd-physics-research-site-tongyan-lin | partial / research_group | 保留partial正确。People页直接确认Current research group at UCSD；研究主题仍来自Tongyan本人第一人称简介，未把个人兴趣或会议/成员名单变成全组方法。 |
| 511 / ucsd-live-lab-272c61c8e40a29 | supported / lab | 支持升级。David Kirsh根页My Lab真实链接lab.html；页面明确Interactive Cognition Lab及We do basic research，官方历史目录同时给出同名lab和David Kirsh。methods空且保留未明确方法限制。 |
| 717 / ucsd-biochemistry-and-molecular-biophysics-lab-budin-lab-laboratory-of-lipid-biology-and-cell-membrane-biophysics | supported / lab | 支持升级。根页完整标题具名Budin Lab，正文We使用实验室集体作用域；People明确PI Itay Budin，官方BMB名录的Website真实指向其具名站。2019/2024根页日期与2026 People修改元数据被区分。原应用目标引文覆盖缺口已修复，见下文；本次无剩余问题。 |
| 820 / ucsd-electrical-and-computer-engineering-lab-ndao-lab | partial / lab | 保留partial正确。Members明确UCSD Ndao Lab及PI Abdoulaye Ndao/ECE关系；研究兴趣是His，首页为论文集合。未将个人兴趣、论文标题、旧BU文字概括为全组研究或迁移历史。 |
| 864 / ucsd-cognitive-science-lab-mooshagian-lab | supported / lab | 支持升级。People页标题和PI行明确Mooshagian Lab/Eric Mooshagian；My lab/We直接说明感觉运动、眼臂协调及顶叶决策。methods空，未把Charles Holmes过去博士阶段非人灵长类研究移为当前组方法；Salk人员文字保留为不确定性。 |
| 875 / ucsd-live-lab-f2a96ed0a66637 | supported / lab | 支持升级。Team页将Pokorski’s laboratory/The Pokorski lab作为两段研究声明的明确主语；化学合成取自该lab段而非PI博士/博后履历。原handoff PI仍Not found，department及导入时间边界完整保留。 |

## Original source checks

下列11个receipt sourceId均通过source_from_capture重建：原始queue URL、observedAt、字节SHA-256、提取正文及deterministic sourceId一致。

### 105

- [People | Kendrick Lab - Salk Institute for Biological Studies](https://kendrick.salk.edu/people/)：src-db3e7f6fdb650376；原始observedAt 2026-10-16T01:30:21+00:00；SHA-256 8aa41fb01f853316f682568fcbc109825f20deb8b5dab57a2d9628665f226593。

### 131

- [Süel Lab](https://suellab.github.io/people/)：src-38d9006f4b462c03；原始observedAt 2026-10-16T01:30:29+00:00；SHA-256 069510b7cef5b40364802e748be95750e03912702130816ce673d77cf15c1e42。
- [Gürol Süel | Program in Materials Science and Engineering](https://matsci.ucsd.edu/faculty/gurol-suel)：src-a0972a46c86d2337；原始observedAt 2026-10-16T01:00:21+00:00；SHA-256 16155577e9cb1745eb4922515b9914e6d9b20efd6fcc483017e7f6741876c0e4。
- [Contact - Süel Lab](https://suellab.github.io/contact/)：src-df8ac209b018d0fd；原始observedAt 2026-10-16T01:30:32+00:00；SHA-256 66061adb6ea0a17adab965f089b3b22e70b133055d89b726aab65a946ca66860。
- [Süel Lab](https://suellab.github.io/)：src-f9939fa33bedba63；原始observedAt 2026-10-16T01:04:42+00:00；SHA-256 75b4078c791038448f4d0a77c34e6f4dcf5c299bbbe3ab588c01b233e2b12930。

### 381

- [People – Tongyan Lin](https://tongyan.physics.ucsd.edu/people/)：src-c669deab53e72181；原始observedAt 2026-10-16T01:33:48+00:00；SHA-256 ffcd5066d1325289f4e56b3d1dc296a17018cc4cec8e193fac8b549ed40c417f。

### 511

- [David Kirsh : My Lab](https://adrenaline.ucsd.edu/Kirsh/lab.html)：src-0f9dc0f52a2b63d1；原始observedAt 2026-10-16T00:59:42+00:00；SHA-256 20b3e6c0d807908b8343c31fd3d27df5e32f709eab5e6ed103412187a20de73b。

### 717

- [People – Budin Lab](https://budinlab.com/people/)：src-22387c5b36ed6272；原始observedAt 2026-10-16T01:35:45+00:00；SHA-256 3e4f1c7bafcb7eade621cd2a131d1ff390cbee5b1cf6fae5d7883d80776e0749。

### 820

- [UCSD Ndao Lab](https://ndao.ucsd.edu/members.html)：src-f6df30e3b783d83f；原始observedAt 2026-10-16T01:36:10+00:00；SHA-256 b67545d3141373d4b759f63d58d06e89eb401594c279f55daad61d05d3538f7a。

### 864

- [Mooshagian Lab - PEOPLE](https://mooshagianlab.ucsd.edu/people)：src-41da4d939dc1f9c1；原始observedAt 2026-10-16T01:36:30+00:00；SHA-256 37258b31f53ae30b89b5011db72178e0a921b282ab2025196888c43b10c49453。

### 875

- [TEAM | Pokorski Lab](https://www.pokorskilab.com/team)：src-665ee9da468401e4；原始observedAt 2026-10-16T02:43:19+00:00；SHA-256 6a700a6318d1166c76ff939011b6fe6eaf7dc7356569137e4890cf4aa8fe91a6。

## Scope and anchor evidence

- 131：官方[Matsci教师页](https://matsci.ucsd.edu/faculty/gurol-suel)直接写“Dr. Süel’s lab”，并给出该lab的定量生物学及跨分子/单细胞/群体尺度建模方法。Lab Website真实指向https://suellab.github.io/；目的页原采集保存从https://labs.biology.ucsd.edu/suel到该根站的301。People同站列Gürol M. Süel；Contact明确UC San Diego Suel Lab。
- 511：David Kirsh原根页的My Lab实际链接https://adrenaline.ucsd.edu/Kirsh/lab.html。该页明确“Interactive Cognition Lab We do basic research…”；methods仍为空，没有从项目名补实验技术。
- 717：根页标题完整具名Lab；We研究正文与People页PI Itay Budin及官方BMB名录相符。实际官方Website是http://www.budinlab.com，原listedWebsite为https://budinlab.com/；此处确认同名PI/实体一致性，不额外声称新在线www/http重定向核验。根页2019/2024日期与People的2019 published、2026 modified元数据已被区分。
- 864：People的Eric Mooshagian, Ph.D. PI段直接写“My lab studies how sensory information is used to drive motor behavior.”，随后We段明确眼臂协调及顶叶决策。非人灵长类模型出现在Charles Holmes过去博士阶段，raw未把它当作全组当前方法；Salk成员文字也保留不确定性。
- 875：化学合成取自“Pokorski’s laboratory works to bridge chemical synthesis, molecular biology, and materials science…”这一lab段，不是前方PI博士/博后的肽模拟物或病毒纳米颗粒经历。
- 381的People与820的Members只用于确认组/PI及来源报告机构关系；未把第一人称/His研究兴趣或论文清单自动提升为全组研究。
- 105的Team页仍是Kendrick Lab/Salk。UCSD博士后经历及UCSD本科生参与都未被当作当前UCSD lab归属或错误类别标签更名的证据。

根页实际发现的同站锚点：105 Team → /people/；131 People → /people/；381 People → /people/；511 My Lab → /Kirsh/lab.html；717 People → /people/；820 Members → /members.html；864 PEOPLE → /people；875 TEAM → /team。全部按实际缓存HTML读取，未猜测路径。

## Frozen fields and time boundaries

- 8条raw均通过hydrate；8个labId与packet.listedWebsite与868基线或冻结handoff逐字一致。
- 共20个实际原始capture完成URL/time/字节hash复核；receipt列出的11个sourceId精确重建一致。
- 875 importedUnknownsAndDateBoundaries在raw与packet中完全一致，PI仍Not found、department仍NanoEngineering；没有从Team中的Jon Pokorski自动回填冻结PI。
- 105仍partial/mismatch，hasUnresolvedMismatch=true，acceptanceStatus=needs_name_correction，silentIdMigrationAllowed=false，proposedCorrections仍candidate_only_not_applied。
- 未把采集时间改成当前任职、持续运营或整个实验室统一更新时间；没有套用其他页面的日期。

- 保留旧引文兼容说明：105的src-e81f02cf99116722保留714字符的较早导航提取；同一原字节当前重建为136字符的src-f7e0bb9679418836。字节hash/time一致，raw只引“Aga Kendrick”，该文字仍在重建正文中。未改写旧sourceId，也未由此接受新研究或身份。

结果：8条完成；阻断性问题0；待处理非阻断引文建议0。
