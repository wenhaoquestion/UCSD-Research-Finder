# 独立日期 Profile 准入数据审阅

**PASS，仅两条 inactive 数据草案；网络仍禁止。** 完成 `2026-10-16T07:14:24.408574+00:00`，最终静态复核 `2026-10-16T07:15:26.145939+00:00`，base `92d5377`。本轮0网络，不调用 plan/execute 或未存在的新helper，不改 active、raw、packet、代码、主checkout或collector。

草案 `INDEPENDENT-DATE-PROFILE-ADMISSION-DRAFT.json` SHA `5d023309c884c1095156c0260d57407a7604205dbf14480f9ec9cb318b96a9a2`，两条均沿用现有6entry common字段，保留完整原URL与root/raw/packet冻结。新加显式目的 `observe_literal_independently_dated_profile_lab_link`、`sourceDateContract=independent_original_profile_capture`、`historicalFieldObservedAt`；不是原 same-capture 合同的放宽。

全文 primary 审阅绑定：`/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/DIFFERENT-TIME-PROFILE-PRIMARY-REVIEW.json`，SHA `c9ebcf87352c0e28279b7bdf7e5f44a2e88bc46870458015289a7ba3a90d5138`；route边界绑定：`/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/DIFFERENT-TIME-PROFILE-ROUTE-BOUNDARIES.json`，SHA `af65dcdecf8eb7df8094f9dfcb3e074683274d1b0916fc77776823d556f10d18`。每条按唯一labId交叉核对完整旧proof SHA、实际sourceURL/time/bodySHA、literal label/href、prof关系与scope decision。它们支持发现关联来源，不支持wholelab科研或当前affiliation提升。

## 634 Chang Lab

稳定ID `ucsd-live-lab-c0c0ce3c3b0e1e`，listed HTTPS `https://changlab.ucsd.edu/Pages/default.aspx`；实际literal HTTP `http://changlab.ucsd.edu/Pages/default.aspx`。原HTML：`<a href="http://changlab.ucsd.edu/Pages/default.aspx">Chang Lab</a>`。有效request key除scheme外严格同host/path/query；Ginsberg字面href无末尾`/`，草案原样保留，根path比较`/`不是HTTPredirect证据。

旧baseline字段原观察 `2026-10-03T02:36:03+00:00`，完整旧verified proof SHA `112e1864221e238e82919a332964a49cc3b544adbbfbfd51a1d6ec2f9a10e7d9`，对象原样保存在报告JSON；实际独立原capture [https://profiles.ucsd.edu/john.chang](https://profiles.ucsd.edu/john.chang) 的观察是 **`2026-10-07T22:45:38+00:00`**。两日期明确不同，均未改动。profile source/final URL、status200、body/原sidecar SHA及实际 main FeaturedContent网页锚点逐项验证。既有教授关系 `ucsd-medicine-john-tzu-yu-chang` 精确指向该官方profile，未推断当前PI、别名或实体接受。

原body SHA `52896352079b1c406e800c7f12baf42c6148e72df3eb6aa4de26e94c858eea95`；原sidecar SHA `9a1fc557c209dd4b02f974e2321bbc65468787dab66a64fa119996dc4e311be3`。own不可变body `/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/profile-link-admission-snapshots/52896352079b1c406e800c7f12baf42c6148e72df3eb6aa4de26e94c858eea95.html`、原sidecar `/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/profile-link-admission-snapshots/52896352079b1c406e800c7f12baf42c6148e72df3eb6aa4de26e94c858eea95.original.json`；模式 `new_byte_identical_immutable_copy_original_observation_unchanged`。Chang只新建这一对原字节副本；Ginsberg复用已存exact pair，原先有限历史迁移证据scope不升级。复制/复核日期不当capture日期。

当前 raw `unresolved`，identity `uncertain`，affiliation `uncertain`，全部保持原状。raw SHA `3ff0b5fdf161b5c926a85e82d29205741709edaf3e6b9cfc0a889533687406f9`，packet SHA `222acede563f229febf6838ed603b25ffffe083fd895826ea562bb2660e22558`，完整latestDestinationFetch与两份已提交报告一致，旧HTTPS根 `robots_unavailable`（原观察 `2026-10-16T01:19:43+00:00`）继续冻结。新鲜queue+ownledger+root/history/related检查未发现该HTTP精确target实际尝试、pending、wire、journal或拒绝；14mismatch不相交。HTTP-origin robots sidecar数 `0`，缺失不表示许可。

## 636 Ginsberg Lab

稳定ID `ucsd-live-lab-7c03bec7416f6a`，listed HTTPS `https://ginsberglab.ucsd.edu/`；实际literal HTTP `http://ginsberglab.ucsd.edu`。原HTML：`<a href="http://ginsberglab.ucsd.edu">Ginsberg Lab</a>`。有效request key除scheme外严格同host/path/query；Ginsberg字面href无末尾`/`，草案原样保留，根path比较`/`不是HTTPredirect证据。

旧baseline字段原观察 `2026-10-03T02:49:37+00:00`，完整旧verified proof SHA `4c8a295cff881a5fdc9ee77e5fa79d962a7b6da238c9ffedf543afab272070cd`，对象原样保存在报告JSON；实际独立原capture [https://profiles.ucsd.edu/mark.ginsberg](https://profiles.ucsd.edu/mark.ginsberg) 的观察是 **`2026-10-07T22:56:09+00:00`**。两日期明确不同，均未改动。profile source/final URL、status200、body/原sidecar SHA及实际 main FeaturedContent网页锚点逐项验证。既有教授关系 `ucsd-medicine-mark-howard-ginsberg` 精确指向该官方profile，未推断当前PI、别名或实体接受。

原body SHA `797aab74a21038675a7a363324554be24bfc88d7fa8c0393800b9333060b882a`；原sidecar SHA `9a894945cd4b1cb55d129d3d42d7bf3d16b90c7c18c0368c4263ed3da0e1bdac`。own不可变body `/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/different-time-profile-accepted-snapshots/797aab74a21038675a7a363324554be24bfc88d7fa8c0393800b9333060b882a.html`、原sidecar `/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/different-time-profile-accepted-snapshots/797aab74a21038675a7a363324554be24bfc88d7fa8c0393800b9333060b882a.original.json`；模式 `reused_existing_exact_Ginsberg_snapshot_no_scope_upgrade`。Chang只新建这一对原字节副本；Ginsberg复用已存exact pair，原先有限历史迁移证据scope不升级。复制/复核日期不当capture日期。

当前 raw `unresolved`，identity `uncertain`，affiliation `uncertain`，全部保持原状。raw SHA `c3d8a05c691bd3890b459ebcc407a36dedaecea4f44c5bb3f4f64c23d3ec6cbf`，packet SHA `5f303c3a15a8732015086a8fa83a020e00c77df5ba43a4a5019e59f33ec91685`，完整latestDestinationFetch与两份已提交报告一致，旧HTTPS根 `robots_unavailable`（原观察 `2026-10-16T03:49:45+00:00`）继续冻结。新鲜queue+ownledger+root/history/related检查未发现该HTTP精确target实际尝试、pending、wire、journal或拒绝；14mismatch不相交。HTTP-origin robots sidecar数 `0`，缺失不表示许可。

## 元数据冻结与运行边界


- baseline `data/research-atlas.json`，SHA `ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e`。

- primary review `/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/DIFFERENT-TIME-PROFILE-PRIMARY-REVIEW.json`，SHA `c9ebcf87352c0e28279b7bdf7e5f44a2e88bc46870458015289a7ba3a90d5138`。

- route review `/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/DIFFERENT-TIME-PROFILE-ROUTE-BOUNDARIES.json`，SHA `af65dcdecf8eb7df8094f9dfcb3e074683274d1b0916fc77776823d556f10d18`。

- active6 entries `/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/reviewed-profile-lab-links.json`，SHA `60f8917c3216e47c6441c5ee945d926c8a46138f89745d9f436964d387daf140`。

- queue `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json`，SHA `dadb420d54516426585dfd16f0bd698b01dc09b05b4690a103b8f8d7d12dcc0a`。

- ownledger `/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/gap-results.json`，SHA `61f839b5b9ab88dde85345c415714e86c62cbcd60519e23d861d4e1ca7c3655b`。


本次读取queue真实更新 `2026-10-16T07:14:16+00:00`，19257 captures；ownledger仍更新 `2026-10-16T06:45:58+00:00`，353 wires。这与owner提供的先前07:05:22状态不同，本报告保留真实新读取值，不伪装旧快照。`INDEPENDENT-DATE-PRE-WORK-RUNTIME.json`（SHA `4d0053409c726d80aefa27921b8b99d331cc731119ffde7376b122f4b2b27ca1`）记录07:12:12 PID55354当时PS缺失；本轮未执行新的PS，不从queue变化推断当前live进程。需owner重新核验实际进程、七源、helper与readiness才能解除网络限制。

两个旧字段与实际新capture日期不一致，**现有same-capture合同判定为不满足**。新草案只为owner单独实现/审阅显式日期合同提供数据，未声称生产helper已接纳，未重复跑未改动源码测试。2MB、HTTP-origin robots先行、公共origin验证、共享v2 gate/冷却、TLS/redirect、durable once、14mismatch与拒绝边界均须保持。旧HTTPS根不重试、不替换；普通成功响应也不自动接受实体、科研、canonical、当前PI或affiliation。

数据审阅问题为0；执行仍受真实runtime与新helper独立验证阻塞。无新wholelab科研结论，无当前affiliation提升，无active entries修改。
