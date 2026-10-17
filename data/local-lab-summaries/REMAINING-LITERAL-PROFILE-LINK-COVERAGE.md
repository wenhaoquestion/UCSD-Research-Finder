# 剩余历史 profile 字面 Lab 链接覆盖审阅

审阅完成：2026-10-16T06:56:12.037933+00:00。**全 146 条当前 partial/unresolved 已扫描，发现 3 条新的字面 HTTP 关联候选：Esko、Kaufman、Ghosh；均未准入、未请求。** 本轮 0 网络，只新增本报告 pair。原 ID、listed URL、根失败、身份与科研状态均未改。

冻结范围为 56 partial、90 unresolved；所有目标都存在于原 baseline 868 中。逐条扫描其全部 **118 个 verified `fieldEvidence.labWebsiteUrl`**；其中 48 IDs 的 49 个字段符合 `official_profile_explicit_lab_link` / `official_profile_generic_lab_link` 与精确官方 Profiles 来源要求，98 IDs 无此类字段。读查主 checkout 全部 695 份 profile sidecar，没有沿用先前 900 字片段限制。

49 字段中，**10 个同 sourceURL、同 observedAt 的原 HTML/sidecar 元组匹配成功**，全部通过 body SHA/status200/finalURL 校验，完整解析实际 DOM 的显式 profile main → FeaturedContent → webpage 锚点。39 个没有同日期原元组：其中 **10 个字段有同 URL 的不同日期 primary bytes**（逐项保留真实新旧时间、body/sidecar SHA）；其余 29 个在此缓存目录没有精确同 sourceURL sidecar。后者不代表全局不存在历史来源。不同日期快照未替代旧字段观察、未计作匹配或本轮候选。

| ordinal / 原名称 | 实际旧 HTML href | 当前判断 |
|---|---|---|
| 150 Esko Lab | `http://eskolab.ucsd.edu/` | 新字面关联候选；未准入 |
| 223 Firestein Lab | `http://raidivision.ucsd.edu/research/firestein-lab/Pages/default.aspx` | known robots unavailable；blocked |
| 233 Schnabl Lab | `http://gastro.ucsd.edu/schnabl-lab` | 已有 target attempt/journal；排除；HTTP robots unavailable |
| 520 Kaufman Lab Site | `http://kaufmanlab.ucsd.edu` | 新字面关联候选；未准入 |
| 621 Lab Site | `http://cmm.ucsd.edu/cleveland/home.html` | 已有 target attempt/journal；排除 |
| 625 Ghosh Lab | `http://ghoshlab.ucsd.edu/Pages/default.aspx` | 新字面关联候选；未准入 |

## 三条新候选的原始证明

### 150 Esko Lab

稳定 ID：`ucsd-cellular-molecular-medicine-lab-esko-lab`。来源 [https://profiles.ucsd.edu/jeffrey.esko](https://profiles.ucsd.edu/jeffrey.esko)，原 observedAt `2026-10-07T21:45:57+00:00`，source/final 均为该 URL，HTTP200/ok。实际可见锚点标签 **Esko Lab**，原始 start tag：`<a href="http://eskolab.ucsd.edu/">`。未将其它个人/部门链接当 Lab 目标。

listed HTTPS：`https://eskolab.ucsd.edu/`；原字面 HTTP：`http://eskolab.ucsd.edu/`。两者严格 request key 除 scheme 外相同，Kaufman 的原 href 保持无尾斜杠，比较只使用有效根路径 `/`，未创造新 href。

原 HTML：`/Users/question/Desktop/research web/.cache/atlas/profiles/11d562a6eecc313d36e4c801785d514c56cae7598205409290c6601f81eebd8d.html`；SHA `0da0ed727c6709cf595af64828ae43bb3eca97d613727f50e5be07b1852c9833`。原 sidecar：`/Users/question/Desktop/research web/.cache/atlas/profiles/11d562a6eecc313d36e4c801785d514c56cae7598205409290c6601f81eebd8d.json`；SHA `81b606c6e483b84383f49fcaee4a02179938b8a63afd013e4af2a56259d5b4f5`。完整 verified 字段证明为 `official_profile_explicit_lab_link`，evidence `Esko Lab → https://eskolab.ucsd.edu/`，与原 profile 同次日期，canonical 完整字段 SHA `352f53fb19ad3e167f9df1f71ebed70b50fe66ce579065a7b124292e81c505c9`；完整字段对象与原 metadata 均保存在 JSON。baseline professor 官方 profile 关联亦逐项匹配；不据此推断当前 PI 或 lab 现时 affiliation。

当前 raw `unresolved`，raw SHA `2c22f900815a260a1d75338289b30a641f71319c6df805a3b39c8694626ef7f8`；packet SHA `fae558201935b6b7e1cc346ce49067dc5d1a135d075985fd3a68c36184cf766d`，完整旧根 fetch 已保留。旧 HTTPS 仍是 `robots_unavailable`，原时间 `2026-10-16T01:19:39+00:00`、robots302。精确 HTTP 在当前 queue/capture history/own wire/journal 无既有尝试，不属于 14 mismatch，未发现原/相关地址明确 access refusal。HTTP-origin robots 尚无观察，这不是允许证明；若另行准入，须正常 robots/shared v2 gate/TLS/2MB/一次性 journal，不能为避错改协议或重试原根。

### 520 Kaufman Lab Site

稳定 ID：`ucsd-live-lab-ebefe055ae9fce`。来源 [https://profiles.ucsd.edu/dan.kaufman](https://profiles.ucsd.edu/dan.kaufman)，原 observedAt `2026-10-07T21:44:17+00:00`，source/final 均为该 URL，HTTP200/ok。实际可见锚点标签 **Kaufman Lab Site**，原始 start tag：`<a href="http://kaufmanlab.ucsd.edu">`。未将其它个人/部门链接当 Lab 目标。

listed HTTPS：`https://kaufmanlab.ucsd.edu/`；原字面 HTTP：`http://kaufmanlab.ucsd.edu`。两者严格 request key 除 scheme 外相同，Kaufman 的原 href 保持无尾斜杠，比较只使用有效根路径 `/`，未创造新 href。

原 HTML：`/Users/question/Desktop/research web/.cache/atlas/profiles/6f1c8dcd93b16620b217bec429b9d8383a54873db167eb900fef77b7189d7437.html`；SHA `c849db11030f9478cfa79f06ec7edec64229862e38102f2c2a1e355aa71e6a78`。原 sidecar：`/Users/question/Desktop/research web/.cache/atlas/profiles/6f1c8dcd93b16620b217bec429b9d8383a54873db167eb900fef77b7189d7437.json`；SHA `53aab280399a4c587aae5a4824304c0d31a0b321e5e37effadee605add3340fa`。完整 verified 字段证明为 `official_profile_explicit_lab_link`，evidence `Kaufman Lab Site → https://kaufmanlab.ucsd.edu/`，与原 profile 同次日期，canonical 完整字段 SHA `b3bf34b68eb3106d17582b756a265542e1d1e39e3c3f3e444b593c2444f1f91c`；完整字段对象与原 metadata 均保存在 JSON。baseline professor 官方 profile 关联亦逐项匹配；不据此推断当前 PI 或 lab 现时 affiliation。

当前 raw `unresolved`，raw SHA `358fb28ae1dbadf66490f6b2da415c16c19c903bc2a855bde2eddf55dd436be8`；packet SHA `cf466826c061ad8d2a4b094eafc724245de4cf5eb067326d34240ec5c53b213d`，完整旧根 fetch 已保留。旧 HTTPS 仍是 `robots_unavailable`，原时间 `2026-10-16T01:19:41+00:00`、robots302。精确 HTTP 在当前 queue/capture history/own wire/journal 无既有尝试，不属于 14 mismatch，未发现原/相关地址明确 access refusal。HTTP-origin robots 尚无观察，这不是允许证明；若另行准入，须正常 robots/shared v2 gate/TLS/2MB/一次性 journal，不能为避错改协议或重试原根。

### 625 Ghosh Lab

稳定 ID：`ucsd-live-lab-eb8a5809f8da0f`。来源 [https://profiles.ucsd.edu/pradipta.ghosh](https://profiles.ucsd.edu/pradipta.ghosh)，原 observedAt `2026-10-07T22:11:28+00:00`，source/final 均为该 URL，HTTP200/ok。实际可见锚点标签 **Ghosh Lab**，原始 start tag：`<a href="http://ghoshlab.ucsd.edu/Pages/default.aspx">`。未将其它个人/部门链接当 Lab 目标。

listed HTTPS：`https://ghoshlab.ucsd.edu/Pages/default.aspx`；原字面 HTTP：`http://ghoshlab.ucsd.edu/Pages/default.aspx`。两者严格 request key 除 scheme 外相同，Kaufman 的原 href 保持无尾斜杠，比较只使用有效根路径 `/`，未创造新 href。

原 HTML：`/Users/question/Desktop/research web/.cache/atlas/profiles/0f9dbae61d761a7608527c6e2bfbde0b1a089a2ec64a793a0d87b4c1668afbc1.html`；SHA `039993a71478a4184622c817944caa672db948e0a4b90d1bd36ee538470f7cc3`。原 sidecar：`/Users/question/Desktop/research web/.cache/atlas/profiles/0f9dbae61d761a7608527c6e2bfbde0b1a089a2ec64a793a0d87b4c1668afbc1.json`；SHA `54562aea4a596a73f3fd8ecbfc2e19d9a55972f338c8de6f62b69f351f2cfbfc`。完整 verified 字段证明为 `official_profile_explicit_lab_link`，evidence `Ghosh Lab → https://ghoshlab.ucsd.edu/Pages/default.aspx`，与原 profile 同次日期，canonical 完整字段 SHA `be25bc6f776089269ce353dc666e146186b5ad1adfaaf2d0b9076c7dfa59418d`；完整字段对象与原 metadata 均保存在 JSON。baseline professor 官方 profile 关联亦逐项匹配；不据此推断当前 PI 或 lab 现时 affiliation。

当前 raw `unresolved`，raw SHA `e0eb0c6e82fd8a5ba164b94bf0005f0e11aa7a0e401b067eca34f180f3a5ac1a`；packet SHA `bc394684b331697670fceb652f1c4ec5def23c7ad29c387ae224e8d746a1a49b`，完整旧根 fetch 已保留。旧 HTTPS 仍是 `robots_unavailable`，原时间 `2026-10-16T01:19:43+00:00`、robots302。精确 HTTP 在当前 queue/capture history/own wire/journal 无既有尝试，不属于 14 mismatch，未发现原/相关地址明确 access refusal。HTTP-origin robots 尚无观察，这不是允许证明；若另行准入，须正常 robots/shared v2 gate/TLS/2MB/一次性 journal，不能为避错改协议或重试原根。

## 已有尝试与阻塞

Schnabl 的原 HTTP 于 **2026-10-16T05:30:38+00:00** 已做 robots 前置；HTTP-origin `/robots.txt` 返回302、`unavailable` / `robots_redirect_is_not_a_robots_file`。这不是 page 已请求证明，但已关闭本轮新路由候选，且必须单列 known robots blocked。Firestein 的 HTTP-origin robots 在 **06:18:43** 同样302/unavailable，继续 blocked，不安排页面。

Cleveland 于 **06:45:57** 实际原 HTTP 页面返回301，随后 HTTPS 页面在 **06:45:58** 返回404；已有 durable journal 与4 wires，不能重排。这里的301来自真实 wire，非从 HTML/meta 或规范化推断。前一批 Carlin/Alexandrov/Cleveland 三条的实际 receipt、journal 和 wires 另存 JSON；前两条已 supported，不在本轮146中，仍明确排除重复请求。

另4个同日成功字段的实际 website anchor 为：Jamieson 本来就是 HTTPS；Kolodner、Zhou、Oegema 的旧 Ludwig 锚点未形成 HTTP 对 listedHTTPS 的本合同缺口，并受既有 mismatch 审阅门禁约束。14项 mismatch gate 全部保留，未接受候选别名/新URL。

## 39 个旧日期未匹配字段

下表逐字段列原 observedAt 及目录中精确同 sourceURL 的其它真实观察；所有对应 sidecar/body 路径和完整 SHA 在 JSON `fieldReviews.sameURLCacheObservations` 中。不将后日期观察写成旧日期。

| ordinal / 稳定 ID | 原字段 observedAt | 实际不同日期原缓存 observedAt / sidecar SHA |
|---|---|---|

| 161 `ucsd-cellular-molecular-medicine-lab-sander-lab` | 2026-10-03T04:41:56+00:00 | 此目录无精确同 sourceURL sidecar |

| 221 `ucsd-lab-from-faculty-raidivision-ucsd-edu-research-corr-lab-pages-default-aspx` | 2026-10-03T02:51:07+00:00 | 2026-10-07T22:57:29+00:00 / `2d8278d637fa7919518480eee3d17fd1c67deadbe764d69fd457aa2792d8a1cd` |

| 290 `ucsd-lab-from-faculty-moorescancercenter-ucsd-edu-research-centers-and-labs-guo-lab` | 2026-10-03T04:04:47+00:00 | 此目录无精确同 sourceURL sidecar |

| 318 `ucsd-pediatrics-lab-bode-lab` | 2026-10-03T04:40:26+00:00 | 此目录无精确同 sourceURL sidecar |

| 323 `ucsd-pediatrics-lab-croker-lab` | 2026-10-03T04:22:38+00:00 | 此目录无精确同 sourceURL sidecar |

| 415 `ucsd-lab-from-faculty-medschool-ucsd-edu-som-fmph-research-centers-integrativehealth-pages-biomarker-laboratory-aspx` | 2026-10-03T05:54:06+00:00 | 此目录无精确同 sourceURL sidecar |

| 621 `ucsd-live-lab-48e8d895726620` | 2026-10-03T01:44:19+00:00 | 2026-10-07T22:04:19+00:00 / `0793be8babf83fb878947b2de9a9e95ca4b49f80f716611d15657d3a9da5088e` |

| 634 `ucsd-live-lab-c0c0ce3c3b0e1e` | 2026-10-03T02:36:03+00:00 | 2026-10-07T22:45:38+00:00 / `9a1fc557c209dd4b02f974e2321bbc65468787dab66a64fa119996dc4e311be3` |

| 636 `ucsd-live-lab-7c03bec7416f6a` | 2026-10-03T02:49:37+00:00 | 2026-10-07T22:56:09+00:00 / `9a894945cd4b1cb55d129d3d42d7bf3d16b90c7c18c0368c4263ed3da0e1bdac` |

| 643 `ucsd-live-lab-5ead21eb34ab92` | 2026-10-03T03:07:19+00:00 | 2026-10-07T23:08:49+00:00 / `b1df9fa3bb86663b7f85906295af4ea2f62e74f3f8558300aa7da84a067525af` |

| 647 `ucsd-live-lab-dd753ba8b2058b` | 2026-10-03T03:31:25+00:00 | 2026-10-07T23:27:20+00:00 / `993276fa3f3fa7b6f9f873c84229e513851ba5f2e8e31c1112c79e2cb37213a2` |

| 648 `ucsd-live-lab-f2d8cdd2c719f1` | 2026-10-03T03:36:53+00:00 | 2026-10-07T23:31:20+00:00 / `75f10adbc60f60e4f1cf9af11c9bdd442e71ae24bc1501f52b8d8157292a7e1f` |

| 650 `ucsd-live-lab-b692982c2795e9` | 2026-10-03T03:39:52+00:00 | 2026-10-07T23:34:21+00:00 / `5e3ef3951558a731ad00cab3135c05af7f59b671657ae8b1c6c2bdbec6c73502` |

| 652 `ucsd-live-lab-1ac4a68f729918` | 2026-10-03T03:45:31+00:00 | 2026-10-08T04:45:50+00:00 / `67bbe642d604bef9bcaf8f5ff6227275b1f175e608d78a5766da8f91354322ef` |

| 653 `ucsd-live-lab-806c5bae5fcb86` | 2026-10-03T03:45:31+00:00 | 2026-10-08T04:45:50+00:00 / `67bbe642d604bef9bcaf8f5ff6227275b1f175e608d78a5766da8f91354322ef` |

| 657 `ucsd-live-lab-421e1ee2de60d0` | 2026-10-03T03:52:48+00:00 | 此目录无精确同 sourceURL sidecar |

| 658 `ucsd-live-lab-8004e73e9a1683` | 2026-10-03T04:00:27+00:00 | 此目录无精确同 sourceURL sidecar |

| 659 `ucsd-live-lab-f56eccf57ff247` | 2026-10-03T04:08:47+00:00 | 此目录无精确同 sourceURL sidecar |

| 660 `ucsd-live-lab-367b3b32a1d6be` | 2026-10-03T04:09:47+00:00 | 此目录无精确同 sourceURL sidecar |

| 661 `ucsd-live-lab-a55100e4af5859` | 2026-10-03T04:10:17+00:00 | 此目录无精确同 sourceURL sidecar |

| 662 `ucsd-live-lab-ef852dd7eab9b8` | 2026-10-03T04:12:56+00:00 | 此目录无精确同 sourceURL sidecar |

| 663 `ucsd-live-lab-7976bbb628cbc8` | 2026-10-03T04:31:07+00:00 | 此目录无精确同 sourceURL sidecar |

| 664 `ucsd-live-lab-fbaafce1c05912` | 2026-10-03T04:43:36+00:00 | 此目录无精确同 sourceURL sidecar |

| 665 `ucsd-live-lab-5461a6896cd917` | 2026-10-03T04:49:28+00:00 | 此目录无精确同 sourceURL sidecar |

| 667 `ucsd-live-lab-cba3d84d5d130f` | 2026-10-03T04:53:34+00:00 | 此目录无精确同 sourceURL sidecar |

| 669 `ucsd-live-lab-e6b730cb5e6d50` | 2026-10-03T04:58:34+00:00 | 此目录无精确同 sourceURL sidecar |

| 670 `ucsd-live-lab-8e21407776c12e` | 2026-10-03T05:01:14+00:00 | 此目录无精确同 sourceURL sidecar |

| 671 `ucsd-live-lab-b0f6255f45cfa4` | 2026-10-03T05:02:15+00:00 | 此目录无精确同 sourceURL sidecar |

| 673 `ucsd-live-lab-4de94a86bcdd38` | 2026-10-03T05:03:45+00:00 | 此目录无精确同 sourceURL sidecar |

| 674 `ucsd-live-lab-ad92a532c161cb` | 2026-10-03T05:08:05+00:00 | 此目录无精确同 sourceURL sidecar |

| 676 `ucsd-live-lab-c4c7878f997535` | 2026-10-03T05:10:24+00:00 | 此目录无精确同 sourceURL sidecar |

| 677 `ucsd-live-lab-87862cab434405` | 2026-10-03T05:20:52+00:00 | 此目录无精确同 sourceURL sidecar |

| 678 `ucsd-live-lab-e8682d0a5d0674` | 2026-10-03T05:24:50+00:00 | 此目录无精确同 sourceURL sidecar |

| 679 `ucsd-live-lab-9e924c08b4a95e` | 2026-10-03T05:27:51+00:00 | 此目录无精确同 sourceURL sidecar |

| 680 `ucsd-live-lab-036a8bb04d25f4` | 2026-10-03T05:27:51+00:00 | 此目录无精确同 sourceURL sidecar |

| 681 `ucsd-live-lab-a187c3da0c31c8` | 2026-10-03T05:29:40+00:00 | 此目录无精确同 sourceURL sidecar |

| 682 `ucsd-live-lab-533d73eca38244` | 2026-10-03T05:32:39+00:00 | 此目录无精确同 sourceURL sidecar |

| 683 `ucsd-live-lab-a8015574dbe788` | 2026-10-03T05:39:54+00:00 | 此目录无精确同 sourceURL sidecar |

| 685 `ucsd-live-lab-1286bb8dae1aec` | 2026-10-03T06:04:23+00:00 | 此目录无精确同 sourceURL sidecar |


不同日期 bytes 仅列入独立 source/date binding 审阅库存，**未扩大当前候选或请求范围**。JSON 保存146条 target trace、49个完整字段 proof 及每项处置、全部10份成功原捕获的实际 tuple、6个字面链接的完整边界证据。无有限覆盖审阅队列遗留。

## 输入冻结与写入范围


- `/private/tmp/ucsd-lab-summaries-20261016/data/research-atlas.json`，SHA `ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e`。

- `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json`，SHA `96b45147d6de7ab9b99bc4fe3137389cb87f48ad87a5082fff695dca7729911b`；原更新 `2026-10-16T06:55:03+00:00`。

- `/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/gap-results.json`，SHA `61f839b5b9ab88dde85345c415714e86c62cbcd60519e23d861d4e1ca7c3655b`；原更新 `2026-10-16T06:45:58+00:00`。

- `/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/identity-decisions.json`，SHA `d03f63cfc224974df2951ebbc152619fc05289431dbcb69781c888df5874362a`。

- `/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/reviewed-profile-lab-links.json`，SHA `c239a8e63f0aa3fd37804970caf9568dafec3db98e7dec5d1839437097d78a05`。


原baseline SHA `ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e`。全部146 raw bytes 与本轮初始记录哈希复核一致。0新增 entries、0网络；未改代码、records、packets、主checkout、collector、队列、shared clocks 或实际 network receipts。
