# 晚到采集缓存关联来源增量审阅（0524）

实际语义审阅：2026-10-16T05:26:12+00:00。结论：**无需要应用的新关联缺口**。只新增本Markdown及同名JSON；0网络请求，0既有文件改动。

主队列只读快照updatedAt `2026-10-16T05:23:59+00:00`，原字节数 `36457773`，SHA256 `116aa5c13164f54a4475afff44e830992c7304458815dddf48b90f260e5a2f16`；扫描latest fetch observedAt自`2026-10-16T04:06:39+00:00`起的484条，其中475条成功。884个eligible ID取既有baseline与精确冻结16条handoff，不应用别名或扩大实体。

按baseline/handoff教授ID、显式PI/profile/来源URL、既有packet来源URL及从这些URL实际记录的单步queue context关联：4个成功capture命中，2个已是packet同最终URL/同正文SHA，只剩2个真正新关联正文，均完整读取。两条既有raw均为supported；partial/unresolved新来源0，科学/隶属变更建议0。

补充检查关联教授的全部sourceURLs：319条professor–lab关系、1274个URL键；独立队列 `2026-10-16T05:24:39+00:00` / SHA `8137522857831f360ec1a6a10d373e443b5443f2e3b1130b727969d0e0d450c1`，进一步命中0。该补充快照单独记录，不把时间偷换成主快照。

baseline SHA `ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e`；frozen handoff SHA `49c5aa9c7864e67553ec8c4f6273e57284dd204ab13d42dc1f8c98197ae24776`；旧候选清单SHA `702159d034e677be3b898132b4b24f5497374d8390d66fbf5783094f5008bef2`。同URL/正文仅观察时间变化、已审候选和已知正文均不记新科研。

## 191 · Mesirov Lab

稳定ID `ucsd-lab-from-faculty-healthsciences-ucsd-edu-som-medicine-divisions-med-genetics-research-pages-mesirov-lab-aspx`。新实际请求 [https://profiles.ucsd.edu/jill.mesirov](https://profiles.ucsd.edu/jill.mesirov)，最终 [https://profiles.ucsd.edu/jill.mesirov](https://profiles.ucsd.edu/jill.mesirov)；observedAt `2026-10-16T04:24:46+00:00`；SHA `56f4a8767aaa877b394cef674f470a08aae8642b39559ef40477fe6a23fe2c30`，实际缓存核验通过。完整正文 `3303` 字符，title `Jill Mesirov | UCSD Profiles`。
决定 `no_lab_science_or_affiliation_change_personal_profile_only`。新版官方Profiles仅列Jill Mesirov个人Emeritus Professor, Medicine及funding项目/Role PI，未描述Mesirov lab整体研究或其当前机构。个人校内emeritus头衔不覆盖实验室第一方Sanford Burnham Prebys地址与机构自述；项目日期不是任职或实验室隶属日期。现raw已有明确whole-lab科研与机构冲突说明，维持external/当前待核实，不据此改source_reported。
- body / `personal_identity,personal_source_reported_affiliation`：Jill Mesirov Title(s) Emeritus Professor, Medicine School Vc-health Sciences-schools Address 9500 Gilman Drive # La Jolla CA 92093
- body / `personal_dated_funding_only`：The Molecular Signatures Database: A knowledgebase for gene set based analysis of genomic data NIH U24CA295532 Apr 1, 2024 - Mar 31, 2030 Role: Principal Investigator
- 保留既有实验室机构原文 `src-000f31c75a1d2e7a` · [https://mesirovlab.org/about/](https://mesirovlab.org/about/) · 原observedAt `2026-10-16T02:43:07+00:00`：Principal Investigator Jill P. Mesirov, PhD Distinguished Professor and Senior Vice President for Computational Science; Sanford Burnham Prebys Discovery Institute
- 保留既有实验室机构原文 `src-000f31c75a1d2e7a` · [https://mesirovlab.org/about/](https://mesirovlab.org/about/) · 原observedAt `2026-10-16T02:43:07+00:00`：Lab Location Sanford Burnham Prebys 10901 North Torrey Pines Road La Jolla, CA 92037
当前raw `supported`、affiliation `external`和scientific reviewedAt `2026-10-16T03:03:28+00:00`全部保留；新来源未追加到packet，不生成已接受身份/别名/当前PI或任职日期。
raw SHA `ce1e9bbd884512130caafd4ab9a797ae3f7116aa6359e9c4920eeb643b4d3894`；packet SHA `400e32ea72e6859ab80a87ec1a117fded47006a0e42ff6ea1b8b90d9376150cb`。

## 613 · Zheng Chen — lab website

稳定ID `ucsd-live-lab-3ecd40fc6caea9`。新实际请求 [https://sites.google.com/a/eng.ucsd.edu/chen-nanoe/home](https://sites.google.com/a/eng.ucsd.edu/chen-nanoe/home)，最终 [https://sites.google.com/a/eng.ucsd.edu/chen-nanoe/home](https://sites.google.com/a/eng.ucsd.edu/chen-nanoe/home)；observedAt `2026-10-16T04:46:36+00:00`；SHA `92bc0e47351bc772e0ebbf8ce6eacfcce730868ac6ee0d90ef3ac4d37cfba825`，实际缓存核验通过。完整正文 `5909` 字符，title `Z.Chen LAB@NanoEngineering`。
决定 `corroborates_named_lab_older_site_no_needed_revision`。该Google主页正文明确SMEL及UCSD NanoEngineering，whole-lab研究范围可归同名既有实验室；并含具名Our lab过氧化氢电合成项目正文。现raw和已引smelab.org首页已有更完整材料表征/纳米制造方法及电池方向、明确source_reported机构。此页代表性论文/视频参考2020–2022，未给整页更新日期；只作既有范围旁证，不能替换现有部门全称、推现时PI或把SPEC中心/论文题目借作该lab方法。非partial/unresolved缺口，无需科学或隶属升级。
- body / `identity,affiliation`：We are the Sustainable Materials and Energy Laboratory (SMEL) in the NanoEngineering department at UC San Diego.
- body / `research,topics`：Our research group focuses on designing and understanding novel materials and chemical processes for energy and environmental applications. We are particularly interested in the following topics: (1) Energy storage and conversion materials and devices; (2) Batteries for extreme environments; (3) Next-generation battery recycling; (4) Porous materials for charge separation and storage.
- body / `research,project_specific_method`：Our lab has developed a portable, more environmentally friendly method to produce H 2 O 2 . W e reported that direct metal-oxygen coordination can create unique active sites that enable efficient and more practical catalyst for electrosynthesis of H 2 O 2 .
当前raw `supported`、affiliation `source_reported`和scientific reviewedAt `2026-10-16T01:46:21+00:00`全部保留；新来源未追加到packet，不生成已接受身份/别名/当前PI或任职日期。
raw SHA `2aaae037ed206467303914ab83dff462e759f0a61768200475cd4ed0ecf0d34b`；packet SHA `ab5265ebba426a12aa17f7eff9c6112f1d423284b550e315a2dd73d2354ec35e`。

## 排除的相同科研正文

- `ucsd-electrical-and-computer-engineering-lab-advanced-robotics-and-controls-lab-arclab`：实际 `http://www.ucsdarclab.com/` → `https://ucsdarclab.com/`，原observedAt `2026-10-16T05:13:14+00:00`，SHA `ad1855dfa32082a4e355e82f667e5c7fa3e083cffac2a85fd9d0cfc94a981e8c`；正文已由`src-7148f67d11a7b404`（原`2026-10-16T01:07:34+00:00`）保存。新捕获的不同实际请求URI不构成新研究内容；不在此任务应用原地址身份绑定或改root metadata。
- `ucsd-live-lab-788dffcb20dbbc`：实际 `http://www.gutkindlab.org/%20` → `https://gutkindlab.org/`，原observedAt `2026-10-16T05:17:55+00:00`，SHA `318c0eee3c51443f724194d6c979043a968eec53a1f20647feaf1c068f4f773e`；正文已由`src-e8ca9eeccacfc463`（原`2026-10-16T01:03:11+00:00`）保存。新捕获的不同实际请求URI不构成新研究内容；不在此任务应用原地址身份绑定或改root metadata。

其余471个成功capture未满足本轮明确目标关系，不以名字相似、网页导航、目录邻组或个人论文猜配给既有实验室。此报告覆盖一个明确冻结时间窗，不无限追逐仍运行采集器；新的后续快照需另列增量。
