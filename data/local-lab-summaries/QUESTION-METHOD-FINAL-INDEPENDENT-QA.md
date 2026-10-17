# 问题与方法字段最终独立QA

PASS。实际核验区间：2026-10-16T09:01:28+00:00至2026-10-16T09:01:31+00:00，raw/packet冻结快照均为2026-10-16T09:01:28+00:00。

8条方法变更都是434条问题迁移的子集：method plan的oldRecord逐条等于question plan的newRecord，实际raw字节和SHA精确等于方法plan。8条researchQuestions及questionFieldReview完整保留，240条待核说明中的相关说明也保留。6条新增15个限定方法条目，2条撤下7个仅兴趣支撑条目；9条方法证明的sourceId、literal quote、原observedAt/bodySHA/URI与未变packet一致。旧证据仅3处按明确提案重分类supports，所有旧引文/来源保留，完整旧raw在immutable plan中。

共434份raw改变、450份原样；全部884份packet与两plan冻结SHA相同。884份摘要及URL导出逐条等于最新内存hydrate，canonical JSONL序列化字节也匹配；manifest全部884个sourceCount准确，0 stale。全884条URL核心与迁移前完全一致，包含原URL、root身份、canonical、redirect、lastCheckedAt、实际请求证明和verified，来源日期没有重写。

最终状态：738 supported、56 partial、90 unresolved；724个lab/group摘要，577个已验证原URL。498条supported有问题、240条问题明确待核；168条methods为空，其中2条本轮已审、166条尚待后续字段审阅。

两plan及两journal的SHA和approved ID/newSHA精确绑定，均complete。父保存audit、validation和最终投影SHA与实际文件匹配；validation passed，errors及digest warnings均空。基点b548801的atlas、gap ledger、14 mismatch decisions和network coordination逐字节原样；358个wire events/210 receipts未增加，14个mismatch接受仍0。

真实430测试receipt仍适用：46个源码/测试文件SHA逐个一致，本轮未重跑测试；owned迁移helpers不在该suite覆盖内。未重复审读全部273问科研正文，无网络、PS或数据/代码写入。

关键绑定：

- question plan：`58d1eed9436f742a0a37c6a3cba0592c2869b6287cecc803c0d23345ae5ee2cf`
- question journal：`2ee52a3981367bd7fd0515c5350235516d0b1b66cc1b4b9105b00d5eaf377c05`
- method plan：`a00853c9513b21ee8c6a51f7f12dc017494f6ad7dfe71d84c8bdf21087fb2c0b`
- method journal：`901440f2a06d580670e8fe6197ee729b9967581976e48cfa85e77b15604a5720`
- audit：`2e8761a2fa2a036be9580db2d54c600f669a70bee1387e2ba1b86c75fbd5076e`
- validation：`bb02ebaa7ef077c579fd51a7d9cf7d48f78a02728c1bc8875fdda9e52f76e16f`

完整投影、manifest、checkpoint、测试receipt、原样基线文件及冻结快照hash见JSON。`outputsAreComplete=false`；此结论限于本次里程碑保存完整性。
