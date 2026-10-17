# Collector B30 精确来源审阅

**PASS：B30 七源组合可离线加载，网络边界与 A071 相同；既有 D1/D2 限制保留。** 实际审阅 2026-10-16T07:17:21.742743+00:00。0 网络、0 collector/shared 写，未更新 readiness。

Owner 的 2026-10-16T07:15:28+00:00 实际 PS 证明 PID57744；本轮只读取该 receipt，未伪装为新 PS 探测。完整七pin与source origins见 COLLECTOR-B30-SOURCE-SNAPSHOTS.json，完整diff、AST哈希及smoke证明见本报告JSON。

| 来源 | SHA256 | 与 A071 |
|---|---|---|
| lab_destinations.py | `d5c0578a3135e344ec59391468d8511f1fe1ef549f2f0ff2462ec70ddfb5aecd` | 同字节 |
| refresh_labs.py | `063ae6effe54c5a6543c09a952800cbc859461bc897a19ef0e66e4aaf5eaa59b` | 同字节 |
| refresh_faculty_directories.py | `29757f294a7b8cc576d211c4dd3089c17b64553189c4e5cb4956d9d959c36896` | 同字节 |
| collection_lock.py | `06b3b4968f62e32f259c723c02637c701261b778814e387e5ad810b7afc72056` | 同字节 |
| collection_scope.py | `6f589d2673f44c5cbbe7681b60655c460b4f196bd8decf47373b452a44483029` | 同字节 |
| network_coordination.py | `3cec5f78dff65ff19fe49e5f2e394bf98c12c6a843e3e4fecd102c176894938c` | 同字节 |
| collect_ucsd_coverage.py | `b30b506404870fff8eac436efeb61a5700598b77f9aea6dc638c3ecd0c8c7674` | 唯一变化 |

Collector A071 `a07158ed32b17f11819f1ae468d7e63c459ca6bc2cc923c2ba4f27497c30360b` → B30 `b30b506404870fff8eac436efeb61a5700598b77f9aea6dc638c3ecd0c8c7674` 的完整diff已读。所有7份own精确快照及当时collector working bytes逐项匹配runtime loaded pins；另6依赖与A071逐字相同。

## 完整差异与 AST

- **Queue.add**：An explicit profile_identity_review reopens only retained_prior_evidence as pending. The retained receipt moves to retainedEvidenceHistory; identityReviewRequestedAt is scheduling metadata, never source observedAt. Allows actual existing profile-response/cache review under normal lease/fetch path; no response/identity acceptance is synthesized. retain_recent_profiles excludes this new context from automatic retention.
- **replay_literal_uri_discovery**：Adds profile_identity_review to the existing replay kind set; successful preserved captures and matching cache body hashes are still required, and profile main remains discovery scope. No new URL generation, HTTP call, URI replay policy or source-date rewrite is introduced by the diff.
- **analyze**：Excludes profile_identity_review from the generic official-directory lab parser, alongside lab_destination/profile/identity_page. Reduces inappropriate directory parsing of explicit profile identity reviews; other existing profile appointment/link discovery paths are unchanged.
- **collect**：Assigns profile_identity_review priority4, uses priority.get(...,8) and min(...,default=8), and sorts explicit profile identity reviews ahead of other Profiles candidates. Scheduling only: still one busy host per collector worker set, same Profiles reserve, unchanged shared gate/10-second floor, scope request_reason, max-pages and fetcher calls.

changedDefinitions 为 Queue、Queue.add、replay_literal_uri_discovery、analyze、collect。Queue类仅因add改变；没有增删定义，模块级imports/assignments/main guard全同。实际处理函数名analyze，调度在collect，main未改。

PublicFetcher整体及7方法、WireHeaders、safe_url、official、url_key、authentication_target、transient_response、retryable_fetch、robots_retry_at、reusable_robots AST全部相同。curl协议限制/系统TLS、认证前置、公共origin检查、robots300k/page默认2MB、共享v2 slot与10秒Profiles最小间隔、Retry-After及redirect目标defer、目标robots、cache日期/hash路径未改变。六依赖同字节也保留其间接scope/lease/gate/canonical行为。

## 离线七源组合

实际调用 g.load_fetcher(expected_hashes=3字段, expected_sources=完整7pins) 成功，读取的process receipt SHA `1d385df1e73724ac6d9b5ff4f537ee5a02fcec60bac4cda2bc54a7ac4657ad6d`，PID57744。全7先验证再编译；未触发main，未实例化PublicFetcher或HostRequestGate，fetch/transport未调用。subprocess.run断言拦截，实际0调用；网络、collector/shared写均0。

Smoke绑定当时adapter SHA `bb120e073854ce2b18230cf1b7cf0861dec61c2fd4953bb91b9aa59bd244c7b2`，仅验证组合，不审批新独立日期helper。pure URL检查保留Chang literalHTTP路径；Ginsberg无path输入得到有效根path `/`，属于wire URI处理，不是HTTPredirect观察；IP literal/credentials/file URL拒绝。此轮未运行全suite或新增测试，owner负责新代码QA/全test。

## 已知限制与执行边界

- **D1：robots404/410 challenge classified not_found**。上游仍可将access_challenge归not_found；现有summary TrackedFetcher._rules以unavailable副本阻止page且不改原磁盘metadata/date。B30未修复上游问题。
- **D2：mixed503/curl63 transient priority**。RETRY503仍先于curl63 hard-error判断，collector既有最多3次重试行为保留；summary不实例化Queue自动重试，候选一次与cap/once未变。不声称此混合响应实际发生。

没有发现B30新增network边界风险。新排队/priority行为只影响collector自己的发现进度，不会在summary import时执行，不自动接受lab身份/科研/current affiliation/canonical/alias，不扩大有限5项scope。Source review不自动ready；owner仍须完成新admission code QA、全test和新鲜实际PID/七pin/adapter receipt核验。未改active/records/packets/代码/队列/ready receipt。
