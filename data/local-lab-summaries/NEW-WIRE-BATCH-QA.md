# New wire batch QA

审阅时间：2026-10-16T03:27:56+00:00。只读核验本地原始receipt、缓存与7个固定source快照；未发请求、未重跑测试、未导入fetcher，也未写raw/packet/code/聚合/collector/shared状态。

结论：通过；没有需要处理的问题。

## Counts and bounds

- 结果70 → 98，新增28：首批27加OIR team1一条。实际wire71 → 114，新增43，恰为零基半开区间[71,114)，各item区间无遗漏、重叠或越界。
- 新增43次包含33个page/redirect wire及10个robots wire；HTTP结果为35个200、8个301。28个最终页面均HTTP200/ok。
- 首个wire始于2026-10-16T03:17:51+00:00，最后wire结束于2026-10-16T03:24:31+00:00；最后OIR结果observedAt为2026-10-16T03:24:31+00:00。
- 28个actualPageRequestMade=true均关联本item范围内的初始page wire及相同liveCheckedAt；每个最终URL、页面重定向和robots重定向均有对应真实wire记录。全部43个事件时间有时区、与epoch一致、结束不早于开始，protocol均为fcntl-host-clock-v2。

## Hash and storage proof

- 28个现代receipt的loadedRequiredSourceHashes均逐字等于当前process.networkCoordination.requiredSourceFiles完整7项；collector/gate及scopePolicyCodeSha256一致。下列7个owned快照的实际字节SHA-256均等于声明值：

- collect_ucsd_coverage.py：aee6c49634e619c2e7f3f6369dee843604b71647e6a20ec77130e0bac7fcc11c
- network_coordination.py：3cec5f78dff65ff19fe49e5f2e394bf98c12c6a843e3e4fecd102c176894938c
- collection_lock.py：06b3b4968f62e32f259c723c02637c701261b778814e387e5ad810b7afc72056
- collection_scope.py：6f589d2673f44c5cbbe7681b60655c460b4f196bd8decf47373b452a44483029
- refresh_labs.py：cdbd7832f6d6e7baeb1988da0535b85c8abcd7e06a6b62d740b81dc670237ead
- refresh_faculty_directories.py：012184fb455602fc21d57fad477487dc4f815ba75888806c8d37e69e3199a8f8
- lab_destinations.py：d5c0578a3135e344ec59391468d8511f1fe1ef549f2f0ff2462ec70ddfb5aecd

- 28个页面body hash均与原始保存缓存相符；response元数据仅多出任务添加的liveCheckedAt/actualPageRequestMade，原fetch字段均保持。
- 24次最终robots元数据使用既有缓存，owned副本与只读collector源字节一致且原observedAt保持；4个最终robots记录为新观察，另有重定向产生额外robots wire，故总robots wire为10。
- 共享目录只见915个host状态JSON和915个host锁；没有响应HTML、robots cache或页面临时文件。adapter代码将页面/robots副本及wire-tmp留在summary gap-cache，collector仅被读取。

## Original URL boundaries

- 涉及23个唯一lab的packet.listedWebsite仍与冻结manifest一致；所有原listed目的页观察均早于本批，新页面仅为followup角色。没有把新followup的finalUrl/采集时间提升为原root canonical/lastCheckedAt。
- Language and Cognition、OIR、Bertrand等HTML导航目标独立抓取；HTML meta refresh不计作原HTTP redirect。ebennett、Bier、Spitzer外部候选的真实HTTP重定向只属于被抓取候选；原listed root元数据仍保留。
- http FlyingV/Thiemens候选被已有safe_url规范化为https后发wire；receipt没有虚构一次http→https HTTP重定向。

## Limits

- collector工作树后续版本与已加载collector快照不同；本批证明依据为process加载hash及owned准确快照，而不是可变工作树。此差异未造成receipt/source不一致。
- 本次为已有wire ledger与缓存的一致性QA，没有额外PID探测、协议测试或网络重放；来源加载/协议行为测试沿用父任务已完成的87项验证，不重复声称本次运行。
