# 历史 profile 字面 Lab 链接有限准入独立审阅

实际审阅时间：2026-10-16T06:44:20.066599+00:00；0 网络请求。结论：**PASS，仅三条单次关联观察候选**；Firestein 排除。此次只写本报告 pair，未运行 plan/execute，未修改原根、packet、raw、队列或 readiness receipt。

当前 adapter SHA `76d7631f8235c540023841c0cdb41c9d59e0c2c83892f3a261de8406dc1e6bbf`；独立测试源 SHA `09961c30ebe701640877bb842b35438ab00c507ce6c062fb7b90d681f857773a`。固定 baseline SHA `ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e`，初始库存 SHA `5c5f4cf5e14f69a44af66f6f29aab0649889b35f22b797fe862a36074f2b46ba`，最终三条 curated entries SHA `c239a8e63f0aa3fd37804970caf9568dafec3db98e7dec5d1839437097d78a05`。

| 实体 | 稳定 ID | 实际历史来源与原观察时间 | 本轮判断 |
|---|---|---|---|
| Aaron Carlin Lab (294) | `ucsd-pathology-lab-aaron-carlin-lab` | [Carlin Lab Website](https://profiles.ucsd.edu/aaron.carlin) — 2026-10-07T22:17:28+00:00 | 单次关联观察候选 |
| Firestein Lab (223) | `ucsd-lab-from-faculty-raidivision-ucsd-edu-research-firestein-lab-pages-default-aspx` | [Firestein Lab](https://profiles.ucsd.edu/gary.firestein) — 2026-10-07T22:37:39+00:00 | 排除：HTTP-origin robots 不可用 |
| Alexandrov Lab (447) | `ucsd-live-lab-c53a46a8ac4496` | [Alexandrov Lab](https://profiles.ucsd.edu/ludmil.alexandrov) — 2026-10-07T22:09:38+00:00 | 单次关联观察候选 |
| Lab Site (621) | `ucsd-live-lab-48e8d895726620` | [Lab Site](https://profiles.ucsd.edu/don.cleveland) — 2026-10-07T22:04:19+00:00 | 单次关联观察候选 |

这三条源自真实旧 HTML 的 HTTP href，与 baseline 中保留的 HTTPS 同 host/path/query。它们是独立的 `reviewed_profile_lab_link_gap`，`observationOnly=true`、`notAnOriginalListedURLCheck=true`；不得当作对原 HTTPS listed URL 的实际请求，也不得自动接受身份、科研、别名或迁移 URL。

### Aaron Carlin Lab

原 listed URL：`https://homer.ucsd.edu/CarlinLab/index.html`；历史实际锚点：`<a href="http://homer.ucsd.edu/CarlinLab/index.html">Carlin Lab Website</a>`。原 profile body SHA：`7489a5991ca6230a27e2051274abd7ad56014a37dbc5f090cb8f0fd57f4861cc`；原 sidecar SHA：`ff236a6a55d38647a78622e2ac6cea5ab082f8e9ac74942665a75f19bad477f3`。同次字段证明方法为 `official_profile_explicit_lab_link`，完整 canonical JSON SHA：`c2ee6b2eaa7362ca6dafbc8d2e57597d3cdb0b08cc840038a5ed4b9dda3819bb`。

已独立核对原始 HTML/sidecar 与 own 不可变快照逐字相同，当前 packet/raw 全字节 SHA 及完整原根 fetch dict 与准入项一致。

原根状态：`robots_unavailable`，实际原观察时间 `2026-10-16T01:05:11+00:00`。HTTP-origin robots 实际 2026-10-16T05:33:45+00:00，status=not_found，HTTP=404，error=空；sidecar SHA `4229148f21e1436b4a875f470eb843dfe09f1196f0b9a3435587ddc278e813ae`。

### Firestein Lab

原 listed URL：`https://raidivision.ucsd.edu/research/firestein-lab/Pages/default.aspx`；历史实际锚点：`<a href="http://raidivision.ucsd.edu/research/firestein-lab/Pages/default.aspx">Firestein Lab</a>`。原 profile body SHA：`9c8875188e995dd867ca0ddf0b58c0bf2329ce37d72914c6335f9b0845b0e9fb`；原 sidecar SHA：`14a8ed809f1f0f388eb9611f79b9562575590cf66bc4b6deaf591e061bc11c1a`。同次字段证明方法为 `official_profile_explicit_lab_link`，完整 canonical JSON SHA：`6df9968cf818a43fda275eb9f97783ccf68cfcc3a2975ab956d8a5f235f9d606`。

原始锚点真实且字段证明有效，但它不解除 robots 障碍。

原根状态：`robots_unavailable`，实际原观察时间 `2026-10-16T01:19:44+00:00`。HTTP-origin robots 实际 2026-10-16T06:18:43+00:00，status=unavailable，HTTP=302，error=robots_redirect_is_not_a_robots_file；sidecar SHA `57eed9cb10267e44b3e53bbe65b0733ff664f5377255889688e086e94cb914d1`。

### Alexandrov Lab

原 listed URL：`https://alexandrov.ucsd.edu/`；历史实际锚点：`<a href="http://alexandrov.ucsd.edu/">Alexandrov Lab</a>`。原 profile body SHA：`9a009a30e1850d53bda9e9430268ccae158f0d1afe86767ca09d4abbe8874f38`；原 sidecar SHA：`667f20ab0602d97be5cc50f9a7cfa363364ba08d0c737f96d8b056a8924dc3a7`。同次字段证明方法为 `official_profile_explicit_lab_link`，完整 canonical JSON SHA：`b397097c29947997da5b54906adef4b1ab8936ddd0c828c4aefa6f47914cd9c5`。

已独立核对原始 HTML/sidecar 与 own 不可变快照逐字相同，当前 packet/raw 全字节 SHA 及完整原根 fetch dict 与准入项一致。

原根状态：`robots_unavailable`，实际原观察时间 `2026-10-16T01:06:25+00:00`。未见该 HTTP origin 的既有 robots 结果；这不表示允许，执行时仍须正常 robots 检查。

### Lab Site

原 listed URL：`https://cmm.ucsd.edu/cleveland/home.html`；历史实际锚点：`<a href="http://cmm.ucsd.edu/cleveland/home.html">Lab Site</a>`。原 profile body SHA：`f29fb590ced0dfa0e19df60bf0fbeaefabd6ccc7238fdab3568e33e9a5429f43`；原 sidecar SHA：`0793be8babf83fb878947b2de9a9e95ca4b49f80f716611d15657d3a9da5088e`。同次字段证明方法为 `official_profile_generic_lab_link`，完整 canonical JSON SHA：`85d513feb648380af2f996cc6f5b23414728f19089e22f539d8d223b039efc64`。

已独立核对原始 HTML/sidecar 与 own 不可变快照逐字相同，当前 packet/raw 全字节 SHA 及完整原根 fetch dict 与准入项一致。

原根状态：`http_error`，实际原观察时间 `2026-10-16T01:06:44+00:00`。未见该 HTTP origin 的既有 robots 结果；这不表示允许，执行时仍须正常 robots 检查。

## 最终准入与代码边界

在冻结读取的 collector queue（更新 2026-10-16T06:44:13+00:00，19240 项，SHA `c49818f7cadc0a11d5da75045490eb3b480ab1137be949f5b7b9a64184c311b1`）与 own ledger（SHA `af7c4da100b9d831b691f65c5109024fb16b8e0b7b229f6e1c420f77b459bf23`）上直接调用只读 helper，结果精确为 Carlin、Alexandrov、Cleveland 三条，每条 2,000,000 字节页面上限；Firestein 的已知 HTTP-origin robots unavailable 为 true。复核期间所有被观察的本地 packet/raw、entries 和 ledger 字节保持不变。

- Exact baseline bytes/ID/listedHTTPS and related professor officialProfileUrl are required; target must be the original captured HTTP href, same exact hostname/effective path/query and no port, credential, fragment, whitespace or control repair.
- Own preserved profile HTML and original sidecar must both hash-match; source/final URL and original observedAt must match a verified same-capture baseline labWebsiteUrl field proof with canonical full-proof SHA.
- Exact label/href must occur in an actual visible DOM anchor inside explicit profile main and Featured Content webpage ancestors; script/comment/style/template/navigation/hidden anchors cannot discover.
- Full packet and raw byte SHA and complete latestDestinationFetch dict remain frozen; raw status partial/unresolved only; reviewed mismatches, supported records, identity mismatch and unresolved mismatch flags are excluded.
- Exact target pending/running/actual attempts/returned final responses and durable start/orphan-wire footprints close one-shot admission; no fabricated original-page proof from a journal or robots-only wire.
- Explicit denial/auth/challenge in packet, related checks, captures or historical attempts blocks. Known HTTP-origin robots unavailable blocks; no bypass of HTTPS TLS/robots errors by guessing alternate routes.
- Default page cap exactly 2000000 only; normal robots 300000, shared v2 gate/cooldown, redirect checks/TLS and loaded-source receipt verification remain unchanged.
- New kind is related historical profile observation only; no original listed-HTTPS check, canonical migration, alias/ID merge, current PI, lab identity or scientific acceptance follows from admission or transport success.

与 Git HEAD 比较，新增四个 helper：`profile_link_access_boundary`、`profile_link_origin_unavailable`、`profile_lab_anchor`、`reviewed_historical_profile_links`。既有函数仅 `plan` 与 `execute` AST 改变。plan 增加独立调用及严格 request-key 分类；execute 去掉两个新 journal 上下文字段后与旧 AST 完全相同。原 `reviewed_original_uri_observations`、`original_uri_page_limit`、`load_fetcher`、`instrumented_fetcher`、coordination 与 page-proof/retry 函数 AST 均未变。journal 仍在 robots/page 前持久化；开始意图不作为原 page 已请求证据。

## 反例修复与验证

1. **resolved** — Legacy HTTP200 authentication destinations and transportStatus could evade status-only boundaries. Dedicated recursive URL/status/history/robots access boundary now includes audited authentication hosts and login.aspx/OAuth/Shibboleth route forms.
2. **resolved** — Fallback DOM main could admit Featured Content outside the explicit profile main. Actual anchor must descend from all three literal profile main/FeaturedContent/webpage IDs, with excluded/template/hidden ancestors rejected.
3. **resolved** — Known HTTP-origin robots unavailable needed a separate boundary from Disallow rules. Own/collector sidecars and actual capture histories checked; timestamps compared as instants; newest conflicts fail closed. Firestein remains excluded.
4. **resolved** — Observed final responses must close repeats, whereas bare redirect.to is discovery only. Actual response final URL with integer HTTP status closes the target; bare redirect target does not prove its page was requested.
5. **resolved** — URI parser normalization could remove literal whitespace/control bytes or an empty fragment. Final helper explicitly rejects any whitespace, C0, DEL, and any # before request_key comparison; independent rebound-fixture negatives pass.

本人独立重跑 focused suite：**35 tests PASS，0.348 秒，0 网络**，上述最终 adapter/test SHA 对应。另核验 owner 实际全套 receipt：**409 tests PASS，2.557 秒**，2026-10-16T06:42:39+00:00 至 2026-10-16T06:42:42+00:00；全 scripts/tests 前后 hash 相同，0 网络，receipt SHA `df62a6dc11a38e4100ceeec56a1b5137c32d6f2edd5be19508ad3574de0b1ea9`，日志 SHA `2f8588ae07ed0dc67617d80442036612783ef73f427233545f5fbb0b0df7a7e0`。此全套运行由 owner 执行，本人核对 receipt 与代码绑定。

无新增未解决漏洞。后续仅由 owner 更新实际进程/七源/adapter readiness 后执行上述三条有限正常 gate 观察。传输结果仍需逐正文实体/科研判定，Firestein 不安排页面请求。
