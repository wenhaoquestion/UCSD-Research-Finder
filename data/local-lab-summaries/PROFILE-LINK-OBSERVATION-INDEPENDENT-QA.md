# Profile-link observation independent QA

独立审阅：2026-10-16T06:55:23+00:00。基准`14e4a1de7a8d7e9e3d359d22cc70d803192fc760`。范围仅Carlin294、Alexandrov447、Cleveland621及本批9个实际事件。只新增本报告及JSON；0网络、0raw/packet/code/collector/shared修改。

**来源、科研范围、网络delta及最终projection绑定全部PASS；未发现待修问题。** 两条研究升级、Cleveland raw不变；3条原HTTPS根身份仍uncertain，原网址verified增加0。

| 记录 | 独立科研/身份结论 | 实际关联观察 |
|---|---|---|
| Carlin294 | [具名实验室正文](http://homer.ucsd.edu/CarlinLab/index.html)明确Dr. Carlin's lab，Research各节We使用实验室集体作用域；摘要/问题/主题及四组方法均有字面支持。UCSD School of Medicine来自本实体正文。 | HTTP200，无redirect；原HTTPS robots TLS失败完全保留，不声称原HTTPS成功。 |
| Alexandrov447 | [新具名首页](https://alexandrov.cloud.ucsd.edu/)的真实nav a href=/research及/research/research-focus只用于发现；[Research](https://alexandrov.cloud.ucsd.edu/research)及[Research Focus](https://alexandrov.cloud.ucsd.edu/research/research-focus)的Our research/Our Lab支持组级研究、实验/计算与SigProfiler机器学习。 | 原字面HTTP实际302到cloud首页，非HTML跳转。研究两body沿用02:15:08/09旧capture，没有新抓或retime；原HTTPS TLS失败保留。 |
| Cleveland621 | 无新科研正文或实体接受；raw整字节等于基准，无source对象新增。 | 字面HTTP实际301到原HTTPS后404；仅新增related检查，不改原HTTPS根fetch日期/状态或身份。 |

Carlin完整Research范围已实际读取，并核对后续Publications/Team边界。其主语“Dr. Carlin's lab investigates transcriptional mechanisms that determine the outcome of host-pathogen interactions.”与各Research节We一致；CRISPR、transcriptomics、epigenomics位于该lab系统方法小节，后续We study/We are developing/We work closely明确生物信息学、数据整合与NGS协议开发。未把成员兴趣、个人训练、论文动物模型或临床疗效移入methods。无页面研究更新时间，论文/履历日期也没有充当更新或现任日期。

Alexandrov新首页只有具名lab/UCSD正文，nav链接本身不作科研证据；其真实a锚点与script payload区分。实验/计算来自Our research，SigProfiler来自Our Lab。原文consortium采样、计划性癌前样本数未变成该lab已完成结果或当前数量；“will reveal”仍按研究问题理解。未添加具体湿实验方法、个人科研归纳、alias/ID merge、当前PI或原HTTPS canonical迁移。两个旧科研source的全部scientific payload、sourceId、原URI/time/hash与基准donor packet精确相同。

四个新增source对象均对实际snapshot HTML重提取全文/title并重算deterministic sourceId一致；所有raw引文在对应body/title/headings逐字存在。四snapshot body与original sidecar均与原own-cache字节相同，hash、original observedAt、request/final URI逐项绑定：

| sourceId | 原观察时间 | 原始body SHA-256 |
|---|---|---|
| src-81dbfc5311a1ccab | 06:45:51，Carlin HTTP | `d095bcfe69a5a1bfcdbd177138d0172dcf756446fd6e62d973761c64f67f793b` |
| src-7e288f2d49761026 | 06:45:54，Alex HTTP→cloud | `467c341ec63369592130bc93d81c9baaca617cb9ad3be0ab8a0ef1a9ee4e07f5` |
| src-ba617541487c7584 | 02:15:08，旧Research | `13de8e0fc17c848bda09b003e12f7d86c996a32d936d84a4bf87748480c4b464` |
| src-9d02dfeba70a3fd7 | 02:15:09，旧Research Focus | `15584eac4081d9308b4a6d23a85e2a5e734de08112f086e42457bcf3b3f29afb` |

以上时间均为2026-10-16 UTC，不是06:49复制/应用时间。2个raw的previousReviewedRecordBeforeProfileLinkObservation完整等于旧raw；所有旧evidence/source/related数组前缀、preparedAt、listedWebsite、latestDestinationFetch及packet其余字段精确不变。3个新related fetch与own receipt绑定，明确notAnOriginalListedURLCheck；new source匹配related fetch而不匹配原HTTPS根fetch。3条旧/新hydrate及最终当前hydrate均通过。

网络由344 wires/202 receipts变为353/205。旧344 events、202 receipts及全部旧journal项的typed序列化逐项精确相同。新range为Carlin[344,345)、Alex[345,349)、Cleveland[349,353)，合计5 page/hop+4 robots；每个事件均有真实开始/结束时间、返回HTTP状态、v2标记及originalObservationUrl。3个once start标注新kind和related-only范围，liveCheckedAt准确对应初始实际HTTP page event，不是journal开始或最终页面完成时间。

所有page/hop cap=2,000,000，robots=300,000。Carlin HTTP robots05:33:45、cloud HTTPS robots00:57:40及CMM HTTPS robots00:57:15缓存与基准字节相同；新HTTP-origin robots的302/301→robots.txt404事件另有06:45:52..56真实记录，未将旧缓存日期重置为新wire日期。Firestein本批0请求。无登录、challenge或robots拒绝绕过证据。

3 receipts的loadedRequiredSourceHashes均含完整7pins，与实际process.requiredSourceFiles及own只读源快照SHA逐项一致；collector A071、gate3cec及scope6f589保持。只读检查[pinned PublicFetcher._wire](/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/network-adapter-sources/collect_ucsd_coverage-a07158ed32b17f11819f1ae468d7e63c459ca6bc2cc923c2ba4f27497c30360b.py:308)仍在network_gate.request_slot内调用transport并记录response；[gate request_slot](/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/network-adapter-sources/network_coordination-3cec5f78dff65ff19fe49e5f2e394bf98c12c6a843e3e4fecd102c176894938c.py:100)锁覆盖响应期。批次preflight记录06:45:48 PID44266实际探测；本QA未重新探测进程或访问共享锁。14个mismatch决策整字节不变，接受数0。

当前适用测试凭据为PROFILE-LINK-ACTUAL-FULL-TEST-RUN.json：06:42:42完成409 PASS、0网络；44个testedSources SHA及完整log hash独立复核仍匹配。adapter `76d7631f8235c540023841c0cdb41c9d59e0c2c83892f3a261de8406dc1e6bbf`、独立测试`09961c30ebe701640877bb842b35438ab00c507ce6c062fb7b90d681f857773a`均保持。旧local-validation-tests.json的252条receipt仅保留历史，不用于证明当前adapter；本次未重跑测试。

最终绑定06:52:51核验parent06:50:25 validation：884/884，738 supported、56 partial、90 unresolved；724 lab/group；569 verified original URLs；outputsAreComplete=false。三当前hydrate与两份serialized projection行精确相等；其余882 summary、881 URL行与基准精确相同，884 IDs及顺序保持。all884 packet SHA与prepare前快照一致、sourceCount stale0、manifest items/imports语义hash匹配。1058证据cache检查为parent validator实绩，本QA读取其PASS/errors[]/digestWarnings[]并独立绑定下列实际projection hash：

- summaries.jsonl `fc26ed5e25844751f6f8c09707ae6fe78143aaaaf0d1fefe939bb4e628fddcd8`
- url-verification.jsonl `9f67f08960db72ba5204fc96c09067837cf337361e1b4b884488bb37537ab4e4`
- queue.json `eb023bc2ab5d25cb4bb6a59f07e85e056261f2363eb8a8da333a68c3a50b774f`
- checkpoint.json `968386f945ff4b9e40219d2668daf05efc6693d7620eebb96f82685521241d7d`

当前finite plan liveCandidateCount=0。本次独立QA剩余事项0，未扩展到其他记录或新请求。
