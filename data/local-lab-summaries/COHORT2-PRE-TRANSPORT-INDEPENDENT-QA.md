# Cohort2 执行前未启动独立 QA

结论：PASS，无需修复的问题。此次是协调器运行门禁前未启动；不是 HTTP 失败，也没有页面请求或新页面证明。

- 独立核对执行前冻结值：884 份 raw、884 份 packet 的 SHA256 全部一致；科学及 URL 投影各 884 个对象与 HEAD `920f81f` 相同。未重读科研正文。
- 自有台账仍为 353 个 wire event、205 份 receipt；完整字节与执行前副本一致，旧 wire/receipt/journal 三子树精确不变。新增 event、receipt、journal start 均为 0。14 个 mismatch 决策完整不变，接受数为 0。
- Esko、Kaufman、Ghosh 三项在自有台账及所读冻结 collector queue 中均无精确目标实际尝试或待执行冲突，仍为未尝试。Kaufman 保留无末尾斜杠的 literal URL；本次没有请求或重定向可据以更改它。
- 已读保存的 07:06:58 未启动凭据及 07:08:17 运行观察：PID 55354 的 PS exit 1，实际 collector 行为空。本 QA 未再次探测 PS。当前协调状态 `waiting_for_live_collector`，`liveRequestsEnabled=false`；06:45:45 的旧 ready 时间仅属历史。
- wrapper 的 `coordination_snapshot()` 在该执行路径的 plan、receipt、journal、transport 之前。父代理后来于 07:08:09 保存的离线计划共 36 项、3 项 finite candidate，`executionStarted=false`、请求数 0；悬挂计划与 `gap-plan.json` 除三个明确的未执行字段外完全一致。
- 07:07:20 validation PASS：884/884，738 supported、56 partial、90 unresolved，724 lab/group research、569 原 URL verified，errors/warnings 为空；manifest 884 个 sourceCount 全部匹配。`outputsAreComplete=false`，队列尚有 10273 pending，不能据此宣称全局采集完成。
- 现有 409 测试凭据的全部 44 个 source SHA 及日志 SHA 仍匹配；本次未重跑测试。这是数据/运行凭据 QA，不是 transport 测试。

最终绑定（完整其余 SHA 见同名 JSON）：

| 文件 | SHA256 |
|---|---|
| 未启动凭据 | `03839625a73447ec78da6b7f4cc685226c80dcded79c0e528d34c9dcb8d637fa` |
| 最终 validation | `7bd23f7b3d77a6b5190751c3e5f9b18c2ff39eb434ea575903122bf9a27e628d` |
| manifest | `befccd15d0c87dba93f0ede454dd1653dab973a3cd02f832428b6cc2dbb082e8` |
| checkpoint | `760265adb0aa04da327805c121f81333f2c4951ff042b73b5bb1603d1e609fbc` |
| suspended finite plan | `de98b7a74b0048b7c808aa1ddb0ff58a0201b8c270bfdb35bd9a00232bb587dd` |
| gap-plan | `fa83aa7c3a5569c7b2196880cf389ef7f4bb9668973b4ca8db0abe427789aaee` |
| 最终运行观察 | `99dc291bba8b5e21ca1cd2bc28a2d420a8684359c8f67c5ebcb2ae17fc1742ba` |

本次 QA 仅写此报告及同名 JSON，0 网络请求、0 raw/packet/code/collector/shared 写入。没有新增科学、身份或根 URL 接受。上述运行观察仅表示当时未启动；未来若实际确认新的 live collector，可重新正常预检。本报告没有作永久 blocked 判断。

审阅时间：2026-10-16T07:10:45+00:00。
