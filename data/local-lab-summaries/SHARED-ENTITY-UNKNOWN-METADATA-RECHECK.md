# 共享实体未知元数据复核

实际复核：2026-10-16T05:20:20+00:00。结果：**PASS，原minor来源字段遗漏已修复**。0网络请求；只新增本报告及同名JSON。

冻结handoff `49c5aa9c7864e67553ec8c4f6273e57284dd204ab13d42dc1f8c98197ae24776` 与 decisions `780a47cabd7b2c6b21b126927244d1fecb5fb3705100ae872d43f0fed5a116c1` 实际文件hash均匹配；两个明确获准共享实体通过当前 `_shared_decision` / `_shared_record` 只读校验。

`scripts/local_lab_summaries.py:361` 的copy白名单已包含 `professorIds`。两packet、两summary投影及两URL投影均逐字段精确等于approved handoff所含未知/日期边界字段；checkpoint `2026-10-16T05:19:58+00:00` 为884/884、validationErrors=[]。

每个实体均明确保留 `professorIds: []`、`principalInvestigator: "Not found"`、`principalInvestigatorProfileUrl: "Not found"`。approved源未提供PI-scope/unverifiedFields，两packet与投影也保持字段缺席，不补默认推断。空professorIds仅表示未分配已审教授关联，不宣称现实中没有PI。

## 882 · Flow Control Lab

稳定ID `ucsd-live-lab-802bc4f0642435`。获准action `accept_shared_entities`，共享group `ucsd-shared-homepage-802bc4f0642435`，memberLabIds仅为已审的两个ID；websiteSharing包括原证据/时间，完整结构与源一致。
professorIds在handoff/packet/summary/URL投影均为显式 `[]`；PI与profile均为 `Not found`。scientific reviewedAt仍为 `2026-10-16T05:11:05+00:00`；状态 `supported`，canCount `True`，本次没有科学或接受状态变更。
原source `src-b4ab573dff1b4ca6`、observedAt `2026-10-16T01:08:35+00:00`、body SHA `a961afcb796d1106489b68ff10a961d03b982af4205ff1e502994669f546ba1e`均保持；未将元数据修补或复核时间变成页面观察时间。
packet SHA `b651735c76a7f98bd58fe3efd1240e3c3df43f53db752acba9aca54d898f44bf`；raw SHA `ed034d1ad504a924da715dccbd2137849077ba72b4ada499f0538cc328ca0c28`。

## 883 · Coordinated Robotics Lab

稳定ID `ucsd-live-lab-7df54236890322`。获准action `accept_shared_entities`，共享group `ucsd-shared-homepage-802bc4f0642435`，memberLabIds仅为已审的两个ID；websiteSharing包括原证据/时间，完整结构与源一致。
professorIds在handoff/packet/summary/URL投影均为显式 `[]`；PI与profile均为 `Not found`。scientific reviewedAt仍为 `2026-10-16T05:11:05+00:00`；状态 `supported`，canCount `True`，本次没有科学或接受状态变更。
原source `src-b4ab573dff1b4ca6`、observedAt `2026-10-16T01:08:35+00:00`、body SHA `a961afcb796d1106489b68ff10a961d03b982af4205ff1e502994669f546ba1e`均保持；未将元数据修补或复核时间变成页面观察时间。
packet SHA `9c6bc09c7e7e584a3a8f16ae017023357b45a7220d5da4fddb30116a70690fff`；raw SHA `a6a6f4c700fbeb046f216444016b8a4c473b61839716f5528187f351a03c9f60`。

## 原882快照及时间顺序

原快照 `2026-10-16T05:09:29+00:00`、882项完整保留，文件SHA `5e7e61e00f753c3616a911d6c8e18e6021ebc2cf65efbc4039cb91f4c5745a12`。当前879/882仍逐字节相同；3个独立差异对应父代理后续真实请求导入，不归因于professorIds修补：
- `ucsd-chemistry-biochemistry-lab-jennings-lab`：原SHA `9cf62ce067294c573b59b5ae603fe69e1728f34e1a85c823d53bd1c5b6ea7607` → 当前 `66261ab75d735bd691870c38982e71a473aa90c1bdd52927fc07dd4ed96a07e5`；该旧packet未新增professorIds边界字段。
  - 独立后续 `src-0bdc9a2cf67f6aa7` · http://jenningslab.ucsd.edu/research.html · observedAt `2026-10-16T05:16:21+00:00` · SHA `43f162576b348d66ad21d6c455a9004810e29fdd3a558d8ba4d91bb6827375c1`。
- `ucsd-chemistry-biochemistry-lab-kummel-lab`：原SHA `b196bc807940e5ff7590a09e79122baf2f84e102818fc33badcdbfd67c548311` → 当前 `ee6a440d29b0920274749244cc6d153d783532efcc1880c4831f35b5f61edc2d`；该旧packet未新增professorIds边界字段。
  - 独立后续 `src-bcab5ff0dfd33434` · http://kummelgroup.ucsd.edu/home.htm · observedAt `2026-10-16T05:16:22+00:00` · SHA `77f5e011bf5f28b9d121a9da8fdc8fb4f9f87c0dc9831425532bd8b476589f1c`。
  - 独立后续 `src-3626de29c7f61579` · http://kummelgroup.ucsd.edu/side.htm · observedAt `2026-10-16T05:16:23+00:00` · SHA `69030e3850045ea5aa732347dc0d8c5da32161b985db079cc1af39eb980ebcb0`。
- `ucsd-structural-engineering-lab-ucsd-structural-health-monitoring-shm-group`：原SHA `06e04dbe6ace3d9ddfbc561e437eb626b59f5e14f3bf9fcdabbacc377d3d3336` → 当前 `5dd891f7486628e4a1e8e0caf6fa116e713ff18a188ef6f41744a5cc6527595c`；该旧packet未新增professorIds边界字段。
  - 独立后续 `src-0de7802df1ac58fb` · http://shm.ucsd.edu/Site/Home.html · observedAt `2026-10-16T05:16:24+00:00` · SHA `1b4e9cbb73cfab12830a535e4ed0948125ec7987651de148c696e8a7d05a2843`。

原QA在05:14:05的882/882保全结论属于该时点；05:15:49仅修新共享对professorIds；05:16:21–24的4个后续页面随后改变上述3个旧packet。扫描旧882，未发现任何professorIds边界字段被本修补新增。

`REVIEWED-16-ADMISSION-QA.json` 原verdict `PASS_WITH_MINOR_PROVENANCE_OMISSION`、两条false遗漏发现和时间均未重写；JSON SHA `027767ffa94fb74e86498fee56e94072a86c63d97307f1083923e84f2b31661c`，Markdown SHA `46b34aec9fb448c3c078ebc22284130d333592745307e56b275781c90a225ae4`。本独立报告记录其后修复已验证，无其他行动项。
