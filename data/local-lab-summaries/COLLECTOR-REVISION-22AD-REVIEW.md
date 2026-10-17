# Collector22ad 精确版本复核

复核：2026-10-16T04:55:21+00:00。**0 网络请求；0 collector/shared 状态写入。**

**结论：相对6a5d，未发现实质网络行为变化。** 全部PublicFetcher方法、网络helper、import以及其余六份依赖相同。新精确七源fixture12测试通过；相关173测试、完整Python295测试均通过。

PS观察文件：`collector-process-observation-remaining34-verified.json`，原checkedAt `2026-10-16T04:51:16+00:00`，PID `16324`，start `2026-10-16T04:46:34+00:00`，文件SHA `f7800bf87236d0e56b427ae4982ffec538dd2378e09ef2028faff456cfae12b3`。本审阅未重复PS或改ready回执。

旧collector `6a5d3c3b8739ad4ae2b9abeaaaa0c9e545bd677f680779691c44e94fa8e0aa82`；新collector `22ad544185024a96f0bde83a7f43b275c2424b4cafbf157327bfb9677b398d9c`。

| 精确加载源 | SHA |
|---|---|
| lab_destinations.py | `d5c0578a3135e344ec59391468d8511f1fe1ef549f2f0ff2462ec70ddfb5aecd` |
| refresh_labs.py | `cdbd7832f6d6e7baeb1988da0535b85c8abcd7e06a6b62d740b81dc670237ead` |
| refresh_faculty_directories.py | `29757f294a7b8cc576d211c4dd3089c17b64553189c4e5cb4956d9d959c36896` |
| collection_lock.py | `06b3b4968f62e32f259c723c02637c701261b778814e387e5ad810b7afc72056` |
| collection_scope.py | `6f589d2673f44c5cbbe7681b60655c460b4f196bd8decf47373b452a44483029` |
| network_coordination.py | `3cec5f78dff65ff19fe49e5f2e394bf98c12c6a843e3e4fecd102c176894938c` |
| collect_ucsd_coverage.py | `22ad544185024a96f0bde83a7f43b275c2424b4cafbf157327bfb9677b398d9c` |

AST只改变已有 `audit_queue_scope`、`collect`，新增 `reassess_scope`；`main`未变。去掉这三个队列维护定义后整个模块AST相同，其他26个旧定义相同。逐定义/方法AST hash、行号、完整import列表及七源编译顺序已记入JSON。

新重评估只读取已缓存成功HTML、调用原有有界同站identity-navigation发现并保存队列历史，不调用transport/fetch。collector主循环起止接入该流程，可能恢复此前具有关联的队列项；摘要适配器只导入定义，不运行Queue/main/collect。

网络路径复核：PublicFetcher构造、缓存路径、_wire/_transport/_rules/fetch整个AST相同；normal curl TLS/public-origin/auth、HTTP-origin robots、300KB robots/default2MB page、逐跳target规则、Retry-After目标defer、v2共享flock/cooldown、返回及抛出错误记录、Profiles10秒未改变。原发现用safe_url/canonical_url仍会规范化，摘要preserve-wire-URI隔离包装仍必要，本轮未改。六依赖与6a5d相同，无隐含新helper版本。

新增 `Collector22ADSharedCooldownAdapterTests` 及22ad/all7 pins常量，沿用全部12场景；移除新增定义后，测试文件AST与git HEAD原文件相同，旧fixture未改。

- 精确22ad fixture：12 PASS，0.180s。
- 全test_local_lab_*.py：173 PASS，1.932s。
- 完整Python unittest discovery：295 PASS，1.856s。
- 覆盖429、全部5xx含501/599、transport返回错误/异常、独立消费者共享cooldown、robots HTTP-date、page/robots跳转的目标先等Retry-After、Profiles10秒、robots恢复/三次停止和challenge拒绝。真实gate文件仅写测试私有临时目录，transport/time假实现，禁止真实transport子进程。
- 测试文件SHA `6919115a1e9b11e59ab9719f10c2f33cb8bad07415c9d21e7b9833da451a322a`；只读适配器SHA `34ebac1ceaf1ba5eae5773b59099b34d993d40aa0135b9698c360a766f3ff02c`。

仅扩展一个测试文件并新增本报告/同名JSON；无adapter、records、packets、身份/科学门禁或实际网络回执修改。结论只适用于上述精确七源；执行前fresh PS/hash和ready回执由父代理完成，原观察时间与审阅时间分别保留。
