# 独立日期 Profile 合同代码 QA

PASS，未发现需修复的门禁漏洞。以 `92d5377` 为基线，本次只新增独立测试与此报告；没有修改 production、raw、packet、collector 或共享状态，0 网络请求。

旧合同仍使用实际 capture 的 `observedAt` 与 baseline proof 作严格字符串匹配；新 registry/purpose 不会回退到旧合同。新合同另外绑定历史 proof/date 与真实 profile body、sidecar/date，并拒绝时区写法不同但实际同一瞬间的来源。见 [独立日期核验](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summary_gaps.py:248)、[两个 wrapper](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summary_gaps.py:295)、[共同门禁](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summary_gaps.py:305)。

两个 own-path/hash 报告要求唯一 lab 行、完整旧 proof、真实 source/time/body/metadata/full-main SHA、教授关系与 frozen raw/packet/root。当前 pending/once/orphan wire、访问拒绝、robots unavailable、mismatch 及 2MB 仍由共同门禁重新检查，不能凭旧“clean”报告绕过。新 kind 进入 EXACT_REQUEST_KINDS，保留 HTTP/HTTPS 区别；空根路径的默认 `/` 不被称作重定向。

AST 对比仅改变旧 wrapper 与 plan，新增三项日期/共同 helper；coordination、load_fetcher、instrumented_fetcher、execute、cap validator 及既有 robots/access/DOM helper 定义均与基线一致。因此本改动没有改变共享锁、robots/redirect/TLS传输或缓存原时间逻辑；这不等于真实 transport 证明。

实际离线结果：旧合同 35、新日期 11、新增独立反例 10，共 56 项 PASS。新增反例覆盖当前 projected 拒绝与历史 HTTP200 login、orphan wire/robots journal、challenge 优先级、8MB 拒绝、registry 隔离、负时区同瞬间、sidecar 日期、报告 symlink 逃逸，以及 hard interruption 无 page proof/finally 复位。父代理实际全套 430 项 PASS（07:16:45–07:16:48）；本 QA 独立核对其全部 46 个当前源码/测试 SHA 与完整日志 SHA，未重跑全套。

实际数据绑定于 07:16:49：新 registry 两项 Chang/Ginsberg 被新 helper 接受；相同新项换成旧 purpose 仍被旧合同拒绝。旧六项 registry SHA 不变，当前可准入旧合同三项。已保存的离线 plan 为 38 项/5 finite（旧3+新2），状态 `awaiting_verified_shared_coordinator`；全部只作关联 URI 观察、2MB、非 root/canonical/identity 接受。未作新的实际进程探测，也不由 queue 更新推断 live collector。

| 绑定对象 | SHA256 |
|---|---|
| adapter | `bb120e073854ce2b18230cf1b7cf0861dec61c2fd4953bb91b9aa59bd244c7b2` |
| 新日期测试11 | `dae9b907608c7f2de32b6d73a23edd5c0ca36767c015def0cf5b8c497b5a1b05` |
| 独立反例测试10 | `a9d93a2b7bbea2ab0f52fa6f000d449c2f3992dc29748562daaefef81adc370c` |
| 新 registry | `3d266f783982f82d6475791700f76e82d812a9acc99ca74a9a80f0bd32193c17` |
| 旧 registry | `60f8917c3216e47c6441c5ee945d926c8a46138f89745d9f436964d387daf140` |
| 全套430 receipt | `00cb842405e759e7620638f7a00e8898c74e9b6057fd22a673f86cabba12ab04` |
| 全套日志 | `b3c06f0a3b94b6951cce3cc1587cf64af1d07c5fd55947fe59a29e5acf828ca1` |

报告完整引用、46 个 source hashes、实际原 profile 日期与 source hashes、离线计划时间/hash 见同名 JSON。程序绑定检查没有替代 primary 审阅者的全文来源判断，也没有产生科学/身份或已验证原 URL 结论。新 collector 版本独立审计与 fresh runtime gate 不在此代码 QA 范围。

审阅时间：2026-10-16T07:18:06+00:00。
