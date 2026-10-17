# B30 loaded 快照补充审阅

**PASS：两组完整exact7来源组合，限当前5条干净literal URI；不自动ready。** 审阅 `2026-10-16T07:23:57.899357+00:00`，0网络/collector/shared写。

Owner的07:20:14实际PS/来源快照显示PID57744仍loaded B30七pins，working已有collector `bb82e0992e6bc25561e7a8a2de9d260a1124ad51971f049b4bf28db11f5ea143`、scope `a6374e96f3d6e862f7a6e65a9d701f3dfe34a04b00e1ccd0df4c7fe80d9182cd`；本轮未声称再次PS探测。全部loaded7与future7都有owned exact snapshot，逐SHA复核。完整两map、reviewedWorkingHashes、两full diffs在JSON。

完整diff只新增：safe_url非str/whitespace拒绝；Queue.add将无效literal/source原时间与hash记入invalidSourceUris且不请求；ScopePolicy.request_reason在排队边界拒绝whitespace。去掉这些新增段后相应函数AST与B30相同；PublicFetcher整体、另5依赖、TLS/robots300k/默认page2MB/redirect/sharedgate/cooldown均不变。

两个actual load_fetcher离线smoke均通过，compile拦截逐项记录7payload SHA，完全等于所选完整map，没有混入working源码。B30 smoke读取真实process receipt，future smoke只用内存prospective receipt，不证明未来组已运行。两组均0fetcher/gate实例、0subprocess、0网络/collector/shared写。

当前5条分别Esko、Kaufman、Ghosh、Chang、Ginsberg；每条literal URI均无whitespace/C0/DEL/fragment，能通过两组validator。现profile准入在解析前已拒绝这些invalid bytes，强于future whitespace-only新增限制，不存在借loaded旧代码绕过这项新限制的当前输入。无尾斜杠原输入保留，有效根path不是redirect观察。

允许complete-map名单是JSON中 `allowedLoadedSourceMaps=[B30LoadedMap, ReviewedFutureWhitespaceGuardMap]`，working同样只能完整等于这两组之一；`reviewedWorkingHashes`精确为future组。**不得按每文件允许值拼混合组，不得忽略未知第三版本。** Owner后续须fresh实际livePID/process loaded完整map、working完整map及owned7payload SHA全部匹配再执行有限5项；future激活还必须被实际PS/pins证明。旧D1/D2限制与补偿、所有once/robots/TLS/cap/sharedgate/14mismatch门禁保持；本报告不扩大scope。
