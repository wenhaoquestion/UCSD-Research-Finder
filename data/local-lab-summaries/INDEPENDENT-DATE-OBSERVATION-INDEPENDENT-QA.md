# 独立日期关联 URI 观察：独立 QA

PASS，未发现需修复的问题。本批实际新增 5 个 wire event、5 份 receipt、5 个一次性 journal；全部是普通 robots 前置检查，没有页面请求、页面正文或新科学/身份接受。

| 目标 | robots HTTP | robots 原观察时间（UTC） | 页面证明 |
|---|---:|---|---|
| eskolab.ucsd.edu | 302 | 2026-10-16T07:24:21+00:00 | false；liveCheckedAt=null |
| kaufmanlab.ucsd.edu | 302 | 2026-10-16T07:24:22+00:00 | false；liveCheckedAt=null |
| ghoshlab.ucsd.edu | 302 | 2026-10-16T07:24:23+00:00 | false；liveCheckedAt=null |
| changlab.ucsd.edu | 302 | 2026-10-16T07:24:24+00:00 | false；liveCheckedAt=null |
| ginsberglab.ucsd.edu | 301 | 2026-10-16T07:24:26+00:00 | false；liveCheckedAt=null |

五项均在 robots 返回 301/302 后以 `robots_redirect_is_not_a_robots_file` / `unavailable` 停止。其 receipt 的页面 redirectChain 为空；不能把 robots 的状态当作网站 HTTP 重定向。Kaufman、Ginsberg 的 literal URL 保留无末尾 `/`，checked effective URI 的根 `/` 只是默认根路径。每个实际 wire 为 300000 字节 cap、v2 shared protocol，页面生命周期上限仍 2000000；没有页面 wire，也没有 body/source SHA 或页面 finalUrl。

逐项核对旧 353 个 event、205 份 receipt、全部旧 journal 的类型敏感 JSON 精确前缀。五个新 journal 均 `receipt_saved` 且明确不是 page proof，自有台账现为 358/210，不能再次排列同项。

884 份 raw 全部与执行前 SHA 一致，879 份其他 packet 未变。五份 packet 仅在 relatedDestinationChecks 追加一项；旧 checks、sources、preparedAt、listedURL、latestDestinationFetch 全部精确保留。五行 URL 投影只改变 relatedDestinationChecks：原根身份仍 uncertain、verified=false；完整科学投影字节不变。14 个 mismatch 决策及旧六项 registry 精确不变，mismatch 接受数仍 0。

Chang/Ginsberg 的历史字段观察分别仍为 10月3日02:36:03 / 02:49:37 UTC，真实 profile capture 分别仍为 10月7日22:45:38 / 22:56:09 UTC；独立日期 contract、原 body/sidecar hash 和原时间没有混同。未重读或接受科研正文。

五份 receipt 的 loadedRequiredSourceHashes 均与 B30 七项完整 map 相同，属于已审 addendum 的允许组合。逐一复算 own immutable payload SHA，network receipt 的 addendum SHA/verified pins、保存的 activation 七 pins 均匹配；没有把不同的 working future revision 混入实际 loaded map。共享 gate/robots/limits 的代码依据复用已审精确快照，本 QA 不实例化 fetcher、不访问 shared state、不发网络请求。

最终 validation PASS（884/884，738 supported、56 partial、90 unresolved；724 lab/group research，569 原 URL verified，1058 evidence caches），errors/warnings 为空，sourceCount 0 stale、imports 不变、离线 plan liveCandidateCount=0。现有 430-test receipt 的全部 46 个当前 source/test SHA 与日志 SHA 复算一致；未重复运行测试。

保存的最终 runtime 观察为 07:26:07：PID 57744 的实际 PS exit0，loaded7 属于已审组合；这是原观察凭据，本 QA 没有再探测进程。queue07:25:57 done6122、pending10175，outputsAreComplete=false，不能因有限 plan 为0宣称全局采集完成。

另以 hash 引用两份有限 metadata 覆盖报告：438 旧 tuple 全等、0新 tuple/binding；教授上下文扩展覆盖146目标/67教授/81官方字段URL keys，33成功关联均已在旧 inventory，0新增。此处仅核对报告元数据和 SHA，没有再次扫 queue 或读取旧正文。

| 最终绑定 | SHA256 |
|---|---|
| ledger | `73d2573f544bbcbb78da464ef388f7d0f11f40b74989788726b683f4112a36a5` |
| application | `34a518b4617ef01da4a745ae04e2586ff4869fce7c069acf4fa47879a0225320` |
| final invariant | `206d37a475d3778dceef387702d3a4daa26b8d07366163e78402dfd4895e08b7` |
| validation | `7bb388bdd2b422a2e670e56bca3fea2179b29425f66db586e5ed2706cb366141` |
| manifest | `fe71c45d57cee5fe120adb0a61154cf856f000be34534d9f49e0f7cb32655aa0` |
| checkpoint | `02c4817e56df7c48606cd9b5d86ef90388fe60ac02a9aa31c8a65a4a08a2bf0e` |
| final runtime | `7944dcea1f6881c2defc9c54bc6d96581fd592e62148d342f310df0ea9f8aaef` |
| professor context metadata delta | `3d60399df33fca83a12e4adf5897815fbcef78e3255532715ce3e4f1dadf21b5` |

完整每项 literal/checked URL、robots 原时间、wire ranges、body/metadata snapshot 校验、七 pins 与所有投影 hash 见同名 JSON。仅写本报告 pair；0 网络、0 PS、0 raw/packet/production/collector/shared 写入。

审阅时间：2026-10-16T07:28:47+00:00。
