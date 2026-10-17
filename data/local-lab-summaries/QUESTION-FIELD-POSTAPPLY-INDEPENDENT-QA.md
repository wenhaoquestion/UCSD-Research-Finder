# 问题字段应用后独立QA

PASS。实际核验区间：2026-10-16T08:56:00+00:00至2026-10-16T08:56:02+00:00；全部884份raw只读取一次，冻结快照时间2026-10-16T08:56:00+00:00。全部884份packet也只读取一次。

- 434份实际raw与plan.newRecord的解析对象、序列化字节和newSHA逐条精确一致；journal恰好434个ID、各SHA一致，state为complete。
- 450份其他raw及全部884份packet与应用前SHA逐字节一致。
- 全884条old/new内存hydrate的URL核心逐项相同：原URL、root身份、canonical、redirect、lastCheckedAt、请求证明和verified均未升级。
- 194条新增273问，240条追加限本轮已审材料的具体待核理由；旧evidence与uncertainty前缀精确保留。只变化RQ、对应证据、不确定性、questionFieldReview和实际模型reviewedAt。
- 273条新问题引文字面匹配，source observedAt及bodySHA均与原packet匹配；packet字节冻结保证全部旧source对象和日期原样。

Plan SHA256：`58d1eed9436f742a0a37c6a3cba0592c2869b6287cecc803c0d23345ae5ee2cf`。Journal SHA256：`2ee52a3981367bd7fd0515c5350235516d0b1b66cc1b4b9105b00d5eaf377c05`，实际应用记录2026-10-16T08:55:13+00:00至2026-10-16T08:55:14+00:00。

Raw快照SHA：`e0550cbb45b67e63fe27a626baba0bab17fd2f5127b9b824b3e61a6519da98ac`；packet快照SHA：`7aa7dafcf8642c6f971eba33b4c9029d6c15168cf0cfa837e3a2a2d416e23370`。算法为按labId排序、紧凑JSON编码的文件SHA映射再取SHA256，JSON报告已说明。

导出尚未重建，本报告未核导出，也不声称其与raw匹配。0网络、0PS、0真实数据/代码/collector写入；仅新增此报告pair。
