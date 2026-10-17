# 方法字段应用计划独立QA

结论：PASS。实际完成：2026-10-16T08:58:40+00:00。方法尚未应用；本报告验证固定8记录计划，不是落盘后QA。
planSha256：`a00853c9513b21ee8c6a51f7f12dc017494f6ad7dfe71d84c8bdf21087fb2c0b`。
helperSha256：`02d1244346a7044ab607e741ae61cc36ac3296c89a5baa9f3b8632e65288729e`。

8条计划oldRecord全部与434问已应用后的当前raw及question plan newRecord一致。全部884 raw/packet SHA均与方法plan的before快照一致，packet亦与问题计划before一致。

仅methods、必要summary/uncertainty、evidence、methodFieldReview与reviewedAt变化。9个已有问题及完整questionFieldReview不变；Coimbra和Experimental Cosmology两条negative availability与两条原“研究问题待核”尾部逐字保留。身份、隶属、PI、topics、stable ID、既有root绑定等其他字段逐对象不变。

9个追加proof均只有supports=[methods]，methodIndices覆盖全部15个方法条目；逐字quote/sourceID与scope提案一致，原captured日期/bodySHA/URI未变。旧证据保留顺序及完整内容，仅3处已批准supports按原索引精确重分类。225摘要正确采用随机学习addendum。

纯hydrate对8条新旧记录的URL投影，除evidence/reviewedAt外逐字段一致，原canCountAsVerifiedLabGroupURL全部不变（7 true、1 false）。

纯内存模拟3例通过：8旧记录正常完成；首记录已写但journal缺失时恢复（不重写首记录）；首记录含未批准hash时在任何模拟写入前拒绝。第一次模拟适配漏处理journal digest，修复QA内存适配后重跑全3例通过；未改helper。

| reviewIndex | 保留问题数 | 旧→新methods数 | 新proof / supports重分类 | URL验证状态 |
|---|---|---|---|---|
| 120 | 1 | 0→3 | 1 / 1 | True→True |
| 190 | 1 | 4→0 | 0 / 1 | True→True |
| 225 | 0 | 3→0 | 0 / 1 | True→True |
| 349 | 2 | 0→2 | 1 / 0 | True→True |
| 364 | 0 | 0→2 | 1 / 0 | True→True |
| 377 | 1 | 0→4 | 1 / 0 | True→True |
| 379 | 3 | 0→3 | 3 / 0 | False→False |
| 382 | 1 | 0→1 | 2 / 0 | True→True |

方法scope项目/历史边界沿用已通过的固定提案与addendum：负责人项目、小鼠/遗传/神经解剖；按需动物模型；BICEP历史年份；中心分项目方法；2020既有SVR工作。

0网络、0PS、0raw/packet/code/collector/shared写入。仅更新本QA pair；未实际执行CLI plan/apply。
