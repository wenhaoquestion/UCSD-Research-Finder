# 不同日期 Profile 字面链接的 Route 边界

完成时间 `2026-10-16T07:06:20.327815+00:00`，最终静态复核 `2026-10-16T07:07:36.878891+00:00`。**10 IDs / 10 个精确 request keys 已全部判定；仅 Chang634 与 Ginsberg636 是未观察的新关联 HTTP route，均未准入或请求。** 0 网络；只写本报告 pair，不调用 plan/execute，不读回全体旧科研正文，不改 active entries、records、packets、代码或 collector。

证据语义沿用已完整阅读的 `DIFFERENT-TIME-PROFILE-PRIMARY-REVIEW.json`（SHA `c9ebcf87352c0e28279b7bdf7e5f44a2e88bc46870458015289a7ba3a90d5138`）。本轮只校验来源 sidecar/hash/date 和请求元数据，不产生新科研结论。旧10/03字段观察与实际10/07或10/08捕获日期明确并列，9份独立profile对应10 IDs，不改旧field日期。

| ordinal / 稳定 ID | 实际 literal href | 原字段时间 → 独立实际捕获时间 | 判定 |
|---|---|---|---|

| 221 `ucsd-lab-from-faculty-raidivision-ucsd-edu-research-corr-lab-pages-default-aspx` | `http://raidivision.ucsd.edu/research/corr-lab/Pages/default.aspx` | 2026-10-03T02:51:07+00:00 → 2026-10-07T22:57:29+00:00 | HTTP-origin robots302 unavailable，blocked；未见原HTTP page响应 |

| 621 `ucsd-live-lab-48e8d895726620` | `http://cmm.ucsd.edu/cleveland/home.html` | 2026-10-03T01:44:19+00:00 → 2026-10-07T22:04:19+00:00 | 已有单次原HTTP301→HTTPS404，禁止重复 |

| 634 `ucsd-live-lab-c0c0ce3c3b0e1e` | `http://changlab.ucsd.edu/Pages/default.aspx` | 2026-10-03T02:36:03+00:00 → 2026-10-07T22:45:38+00:00 | 未观察的HTTP关联route；需独立日期合同，未准入 |

| 636 `ucsd-live-lab-7c03bec7416f6a` | `http://ginsberglab.ucsd.edu` | 2026-10-03T02:49:37+00:00 → 2026-10-07T22:56:09+00:00 | 未观察的HTTP关联route；需独立日期合同，未准入 |

| 643 `ucsd-live-lab-5ead21eb34ab92` | `http://bryanlabsite.edu` | 2026-10-03T03:07:19+00:00 → 2026-10-07T23:08:49+00:00 | 既有HTTP robots DNS失败；外域不自动准入 |

| 647 `ucsd-live-lab-dd753ba8b2058b` | `https://medschool.ucsd.edu/som/neurosciences/research/labs/zheng/pages/default.aspx` | 2026-10-03T03:31:25+00:00 → 2026-10-07T23:27:20+00:00 | 同精确HTTPS地址已返回404；非新route |

| 648 `ucsd-live-lab-f2d8cdd2c719f1` | `https://medschool.ucsd.edu/som/neurosciences/research/labs/graves/Pages/default.aspx` | 2026-10-03T03:36:53+00:00 → 2026-10-07T23:31:20+00:00 | 同精确HTTPS地址已返回404；非新route |

| 650 `ucsd-live-lab-b692982c2795e9` | `https://medschool.ucsd.edu/som/neurosciences/centers/neural-repair/pages/default.aspx` | 2026-10-03T03:39:52+00:00 → 2026-10-07T23:34:21+00:00 | 同精确HTTPS地址已返回404；非新route |

| 652 `ucsd-live-lab-1ac4a68f729918` | `https://medschool.ucsd.edu/som/neurosciences/research/labs/hnasko/Pages/default.aspx` | 2026-10-03T03:45:31+00:00 → 2026-10-08T04:45:50+00:00 | 旧medschool HTTPS已404，保留独立ID |

| 653 `ucsd-live-lab-806c5bae5fcb86` | `https://hnaskolab.ucsd.edu` | 2026-10-03T03:45:31+00:00 → 2026-10-08T04:45:50+00:00 | 新站HTTPS robots302 unavailable，保留独立ID |


四条为真实 literal HTTP 对 listedHTTPS（Corr、Cleveland、Chang、Ginsberg）；其余六条与 listed 的严格 request key 相同。共有7 IDs 已有同 request key 的逻辑检查，其中5有真实页面/redirect返回证据，Bryan与新站Hnasko只有 robots 前置失败、无 page proof。无 exact pending，未见新增 explicit refusal/auth/challenge；3条 literal-origin robots unavailable 分别 Corr、Bryan、新站Hnasko。robots unavailable 是具体前置阻塞，不被改写为网站主动拒绝。

## 两条未观察关联地址

### 634 Chang Lab

原始 profile [https://profiles.ucsd.edu/john.chang](https://profiles.ucsd.edu/john.chang)，实际捕获 `2026-10-07T22:45:38+00:00`，body SHA `52896352079b1c406e800c7f12baf42c6148e72df3eb6aa4de26e94c858eea95`、原 sidecar SHA `9a1fc557c209dd4b02f974e2321bbc65468787dab66a64fa119996dc4e311be3`。原 literal HTML：`<a href="http://changlab.ucsd.edu/Pages/default.aspx">Chang Lab</a>`。旧字段 `2026-10-03T02:36:03+00:00`、完整旧field SHA `112e1864221e238e82919a332964a49cc3b544adbbfbfd51a1d6ec2f9a10e7d9` 单独保留。

新关联地址 `http://changlab.ucsd.edu/Pages/default.aspx`，listed `https://changlab.ucsd.edu/Pages/default.aspx`。冻结 queue+own ledger 与 packet root/history/related/followup 未发现精确 HTTP target 的实际检查、pending、wire、journal或明确拒绝；14 mismatch无交集。未见该HTTP origin robots结果，不能据此授权。原HTTPS根仍为 `robots_unavailable`，原时间 `2026-10-16T01:19:43+00:00`，其robots为 `unavailable` / HTTP`302` / `robots_redirect_is_not_a_robots_file`，不重试、不替换。

现有同次旧field日期合同不能直接接纳新日期；需要独立来源/时间绑定的单独审阅合同。Ginsberg原href无尾`/`须保持，URI根path比较不代表实际redirect。原root pageIdentity仍uncertain，实体acceptance仍provisional/unresolved。

### 636 Ginsberg Lab

原始 profile [https://profiles.ucsd.edu/mark.ginsberg](https://profiles.ucsd.edu/mark.ginsberg)，实际捕获 `2026-10-07T22:56:09+00:00`，body SHA `797aab74a21038675a7a363324554be24bfc88d7fa8c0393800b9333060b882a`、原 sidecar SHA `9a894945cd4b1cb55d129d3d42d7bf3d16b90c7c18c0368c4263ed3da0e1bdac`。原 literal HTML：`<a href="http://ginsberglab.ucsd.edu">Ginsberg Lab</a>`。旧字段 `2026-10-03T02:49:37+00:00`、完整旧field SHA `4c8a295cff881a5fdc9ee77e5fa79d962a7b6da238c9ffedf543afab272070cd` 单独保留。

新关联地址 `http://ginsberglab.ucsd.edu`，listed `https://ginsberglab.ucsd.edu/`。冻结 queue+own ledger 与 packet root/history/related/followup 未发现精确 HTTP target 的实际检查、pending、wire、journal或明确拒绝；14 mismatch无交集。未见该HTTP origin robots结果，不能据此授权。原HTTPS根仍为 `robots_unavailable`，原时间 `2026-10-16T03:49:45+00:00`，其robots为 `unavailable` / HTTP`0` / `curl: (35) LibreSSL/3.3.6: error:1404B458:SSL routines:ST_CONNECT:tlsv1 unrecognized name`，不重试、不替换。

现有同次旧field日期合同不能直接接纳新日期；需要独立来源/时间绑定的单独审阅合同。Ginsberg原href无尾`/`须保持，URI根path比较不代表实际redirect。原root pageIdentity仍uncertain，实体acceptance仍provisional/unresolved。

## 其余边界

- Corr221：HTTP raidivision `/robots.txt` 实际06:18:43返回302/unavailable，`robots_redirect_is_not_a_robots_file`；未见原Corr HTTP page响应，仍不探测。旧HTTPS失败保留。
- Cleveland621：已有journal及4 wires，原HTTP page在06:45:57实际301，随后HTTPS06:45:58返回404；本次不再执行。
- Bryan643：`http://bryanlabsite.edu` 与 listed带`/`是相同有效 request key；已有01:06:50、03:47:40、03:49:45逻辑前置，robots curl6 DNS失败，无page proof。且域名不在官方`*.ucsd.edu`，不自动准入或发明替代URL。
- Zheng647、Graves648、Tuszynski650、旧medschool Hnasko652：对应精确HTTPS已真实返回404，时间分别01:06:52、01:06:53、01:00:41、01:06:54；较晚profile重现相同地址不形成新route。
- 新站Hnasko653：`https://hnaskolab.ucsd.edu` 与 listed带`/`同key；既有多次robots前置，最新01:19:43为302/unavailable，无page proof。它与652使用同一10/08 profile的不同字面锚点，稳定ID、路径、失败与科研身份分别保留，不merge、不alias。

## 未来合同边界


- No current admission or entries are created. A separate reviewed branch would need explicit purpose and actual independent-date source identity; retain the10/03 baseline field proof and its hash as historical association rather than claiming exact-observation equivalence.

- Bind fixed baseline bytes/labID/listed HTTPS, full old verified field proof hash, existing exact officialProfiles professor relationship and exact profile source URL. Independently bind actual10/07 original body+sidecar hashes, full metadata/time/status/final and visible actual main FeaturedContent webpage literal label/href.

- For Chang/Ginsberg literal HTTP vs listedHTTPS, preserve original full URI (Ginsberg has no trailing slash); require strict same host/effective path/query, no guessed protocol/slug/alias/credentials/port/query repair. A parser effective root/ is not HTTP redirect evidence.

- Recheck exact queue pending/attempts, packet root/history/followups, actual final response, own wire and durable journal. Known refusals/challenge/robots unavailable and14mismatch gates must remain closed; no retry of already observed Cleveland or blocked Corr/Bryan/Hnasko.

- Normal public-origin validation, robots first, shared v2 gate/cooldown, redirect/TLS, default2MB cap and durable one-shot remain required. Missing HTTP robots result is not permission.

- No lab identity, canonicalURL, currentPI/affiliation or science acceptance follows from historical profile discovery or transport. Hnasko two stable IDs remain separate. External Bryan is outside automatic official.ucsd.edu route admission.


## 冻结输入与保护


- `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json`，SHA `617d8915995f022975503a14dfdaec134a22b94032d1ae3c30d0eee3d1e746b4`，原更新 `2026-10-16T07:05:22+00:00`。

- `/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/gap-results.json`，SHA `61f839b5b9ab88dde85345c415714e86c62cbcd60519e23d861d4e1ca7c3655b`，原更新 `2026-10-16T06:45:58+00:00`。

- `/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/identity-decisions.json`，SHA `d03f63cfc224974df2951ebbc152619fc05289431dbcb69781c888df5874362a`。


JSON逐ID保留literal/listed request key、真实新旧时间、原sidecar/source SHA、current root/identity projection、全匹配请求与attemptHistory、robots两协议sidecars、ownwire/journal、packet精确检查和边界。全部10 raw/packet bytes最终复核与本轮读取哈希一致。未触碰cohort2的3项执行。`openIssues=[]`，有限元数据审阅已完成。
