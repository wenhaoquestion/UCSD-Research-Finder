# 8个URL候选：身份绑定的最小下一步

结论：8项均可按现有规则，仅补原根capture的身份引文；无需换根、改代码或新请求。本报告只是设计，未应用、未声称恢复验证计数。

`hydrate` 的canCount需要：实际直接请求原listed URI、accepted lab/group、与选定根fetch精确匹配的identity引文，以及无mismatch。8项现有selected root已各自实际请求原listed HTTPS并取得200；false仅因为现有identity引文来自其他官方/关联source，未匹配该根的actual requested URI、原observedAt、64位bodySHA和final URI。[精确source匹配](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summaries.py:101)、[hydrate](/tmp/ucsd-lab-summaries-20261016/scripts/local_lab_summaries.py:513)无需放松。

我核对8个原HTTPS缓存HTML的title/具名lab局部语境、实际bodySHA和原metadata sidecar的URI/time/hash。以下source均已source_matches_fetch=true；只对深拷贝raw追加该项identity证据，8次pure hydrate的counterfactual均为true。实际raw/packet/projection全部未写。

| 对象 | 原root sourceId / UTC原观察时间 | 拟追加身份quote（位置） |
|---|---|---|
| Süel | `src-c4ba244c6440b828` / 2026-10-16T01:06:31+00:00 | Süel Lab（title） |
| Coimbra | `src-8d8c600e7abe1be8` / 2026-10-16T01:00:13+00:00 | Coimbra Research Group（title） |
| ARMOR | `src-97b310b478bf8a4d` / 2026-10-16T01:00:50+00:00 | ARMOR Lab（title） |
| MACRO | `src-2b4ad061e661bf3c` / 2026-10-16T00:59:39+00:00 | MACRO Lab – MACRO Lab（title） |
| Acevedo/F² | `src-0cc9bbd11053e1c5` / 2026-10-16T01:00:06+00:00 | FRACTURE AND FATIGUE OF SKELETAL TISSUES LABORATORY F² LAB（body） |
| iPower3Es | `src-254ea865b6464cde` / 2026-10-16T01:00:27+00:00 | integrated Power Electronics and Energy-Efficient Systems Lab – Create and Supply Integrated/Miniaturized Power for All（title） |
| Zhong | `src-223296c9545f4eae` / 2026-10-16T01:01:20+00:00 | Welcome to Zhong Lab of Systems Biology（title） |
| Frazer | `src-e9e0fdc0ea4aa75a` / 2026-10-16T01:00:18+00:00 | Home Page \| Frazer Lab（title） |

Süel、Zhong、Frazer三条新HTTP body与已有HTTPS root byte-identical，确实只缺root-bound identity证据；使用原sourceId和原时间即可。其余五条新HTTP body不同，也无需引入新body：原HTTPS root自己的title/具名正文已经明确，仍须引用各自旧source。Süel原root可见主文为空，必须显式quoteLocation=title，不能伪称正文。

iPower3Es原HTTPS请求已有真实HTTPS→eng域名301链，照原metadata保留；新HTTP→HTTPS→eng的独立链不能覆盖它。其余新HTTP初始URI及05时段观察同样保持原样，不能改称HTTPS初始请求或据final相同伪造direct-check。

建议父代理应用：先复核每项冻结hash；仅append表中identity evidence，保留全部旧引文/原source/date、scientific fields和main reviewedAt；另记实际identityBindingReviewedAt。packet的preparedAt/listedWebsite/latestDestinationFetch/source prefix无需变动。逐条hydrate并validate后才更新计数。当前569未变，8只是待应用验证的候选；14 mismatch门禁不涉及且不放宽。

输入FULL884报告SHA `9ecf4ebef8974da1fff6dd584d4b9a2d967cfea8ba1a0ee1e91713f37b79d972`；hydrate源码SHA `e0a254c2c749f4cceb69b0ebc307380e69427542760a43e72562ff2404326c6b`。完整8项actual旧root tuple、原body/sidecar proof、原identity source为何不匹配、以及新HTTP观察的独立URI/time/hash见同名JSON。0网络、0PS、0plan、0生产/数据/collector写入。

审阅时间：2026-10-16T07:51:26+00:00。
