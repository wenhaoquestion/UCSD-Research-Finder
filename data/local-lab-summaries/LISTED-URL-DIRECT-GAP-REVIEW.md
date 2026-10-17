# 原列表 HTTP 地址直接请求缺口复核

复核时间：2026-10-16T04:17:07+00:00。本轮离线请求数 **0**；仅新增本报告及同名 JSON。

48/48 条元数据审阅通过，包含 37 个 lab、11 个 research_group；与 13 条身份争议决策的交集为 0。原始 HTTP 地址按 literal 字符串和保留 scheme 的严格请求键去重，均为 **48 个唯一 URI**，无可合并请求。所有条目的既有身份接受状态保持不变。

逐条对照原 baseline、manifest、当前 packet/raw record 和两份 projection：稳定 ID 与 literal listedUrl 一致；现有成功请求均是同 hostname、同有效请求 path、同 query、scheme 为 HTTPS 的相关地址，HTTP 200、status=ok、身份确认，且无登录地址、access boundary 或 collector challenge pattern。缓存正文 SHA、原 observedAt、真实 checkedUrl/finalUrl 与来源 tuple 全部匹配。其中 17 条原 URL 的 literal path 为空，相关 HTTPS URL 将默认根路径写为 `/`；它们的 HTTP 请求目标均是 `/`。其余 31 条字面上仅 scheme 不同。此处沿用既有科研语义审核，不重新综合科研方向。

这些捕获不能证明原 HTTP 响应，也不能证明 HTTP→HTTPS 跳转。本轮 queue/attemptHistory/gap-results 中没有匹配原 HTTP URI 的页面请求证据。旧 baseline 的历史 websiteCheck 仍保留，不能表述为“从未检查”；当前 projection 正确维持 related_url_request_only、listedUrlDirectlyChecked=false、canCountAsVerifiedLabGroupURL=false。

## 精确加载代码的原因与适配要求

- Collector snapshot SHA：`edaacebf859c73b14b76b41673b4c30089b65c987c41baf2d4294015bae9d439`。`safe_url` 第68–79行先调用 `canonical_url(raw)`（第70行）。
- 其精确 refresh_labs 依赖 SHA：`cdbd7832f6d6e7baeb1988da0535b85c8abcd7e06a6b62d740b81dc670237ead`。`canonical_url` 第64–74行中，第69行把 UCSD hostname 的 scheme 强制设为 HTTPS；这发生在网络请求前。
- `PublicFetcher.fetch` 第337行起，先经 safe_url，再建立缓存键和 meta.sourceUrl、做 robots 和页面请求。仅把原 HTTP 传给现有 fetch 并不能恢复真实 HTTP 请求；这也不是观察到的 HTTP redirect。
- 仅 AST 编译上述纯函数及 summary 严格请求校验函数、无整模块加载/Fetcher/网络 gate 实例化，48/48 输入均确定性地变成 inventory 中的 actualCheckedUrl。
- 当前 coordination receipt checkedAt：2026-10-16T04:03:52+00:00，protocol `fcntl-host-clock-v2`，receipt SHA `5bfeb79ec1d3af035544ab2e4c7324abbd700c40194d3593e2daf9469b582c70`。本报告以 receipt 指定的加载 snapshot 为准，不混用 mutable working file 或较早 live ledger 的源码 hash。

适配层必须保留原始 HTTP scheme 及 host/path/query，并在直接请求的缓存、去重和 `page_live_event` 中使用保留 scheme 的请求身份；内容复用用的 `key()` 会折叠 scheme，不能作为直接请求证明。保留现有 public-origin、凭据/端口/IP/local 限制、认证地址阻断、HTTP 原点 robots、每次真实 redirect 的目标 robots/auth、v2 shared gates/cooldown、429/5xx/error、Retry-After 传播、Profiles 最低10秒和源码 hash/race guards。不要绕过 fetcher 直接调用 transport。

实际原 HTTP 请求可能是 200、真实 Location 重定向、错误、challenge 或 robots refusal，须如实观察。必须新增真实原 URI/时间/状态/链/正文 hash；不得把 HTTPS 的时间、正文或重定向链改标为 HTTP。完成适配器离线验证后由父代理决定有界请求；此清单本身不执行请求。

## 逐条决策

所有条目结论均为：**原 HTTP 直接观察缺口确认，等待真实结果；不假定跳转；0 requests**。下表的时间和最终 URL 都属于已存的相关 HTTPS 捕获，绝非原 HTTP 新观察。逐项完整检查、缓存路径/正文 SHA、packet/raw hash 和历史 websiteCheck 见同名 JSON。

| ordinal / stable ID | 原 literal HTTP URI | 实际相关请求 URI | 相关捕获 final URL / 原 observedAt | 既有类别 |
|---|---|---|---|---|
| 46 `ucsd-biology-topic-lab-cleland` | <http://labs.biology.ucsd.edu/cleland> | <https://labs.biology.ucsd.edu/cleland> | <https://clelandlab.biosci.ucsd.edu/> · 2026-10-16T01:03:57+00:00 | lab |
| 47 `ucsd-biology-topic-lab-cory-root` | <http://rootlab.biosci.ucsd.edu> | <https://rootlab.biosci.ucsd.edu/> | <https://rootlab.biosci.ucsd.edu/> · 2026-10-16T01:03:57+00:00 | lab |
| 52 `ucsd-biology-topic-lab-david` | <http://www.biology.ucsd.edu/labs/david> | <https://www.biology.ucsd.edu/labs/david> | <https://labs.biology.ucsd.edu/david/> · 2026-10-16T00:59:39+00:00 | lab |
| 58 `ucsd-biology-topic-lab-estelle` | <http://www-biology.ucsd.edu/labs/estelle> | <https://www-biology.ucsd.edu/labs/estelle> | <https://labs.biology.ucsd.edu/estelle/> · 2026-10-16T00:59:37+00:00 | lab |
| 61 `ucsd-biology-topic-lab-forbes` | <http://www.biology.ucsd.edu/labs/forbes> | <https://www.biology.ucsd.edu/labs/forbes> | <https://labs.biology.ucsd.edu/forbes/> · 2026-10-16T00:59:42+00:00 | lab |
| 76 `ucsd-biology-topic-lab-justin-meyer` | <http://labs.biology.ucsd.edu/meyer> | <https://labs.biology.ucsd.edu/meyer> | <https://labs.biology.ucsd.edu/meyer/> · 2026-10-16T01:04:07+00:00 | lab |
| 89 `ucsd-biology-topic-lab-lin-chao` | <http://www.biology.ucsd.edu/labs/chao> | <https://www.biology.ucsd.edu/labs/chao> | <https://labs.biology.ucsd.edu/chao/> · 2026-10-16T00:59:48+00:00 | lab |
| 92 `ucsd-biology-topic-lab-markow` | <http://biology.ucsd.edu/labs/markow> | <https://biology.ucsd.edu/labs/markow> | <https://labs.biology.ucsd.edu/markow/> · 2026-10-16T00:59:57+00:00 | lab |
| 95 `ucsd-biology-topic-lab-mayfield` | <http://algae.ucsd.edu/mayfield/index.html> | <https://algae.ucsd.edu/mayfield/index.html> | <https://algae.ucsd.edu/mayfield/index.html> · 2026-10-16T01:02:04+00:00 | lab |
| 100 `ucsd-biology-topic-lab-nan-hao` | <http://haolab.ucsd.edu> | <https://haolab.ucsd.edu/> | <https://haolab.ucsd.edu/> · 2026-10-16T01:04:17+00:00 | lab |
| 103 `ucsd-biology-topic-lab-nieh` | <http://www.biology.ucsd.edu/labs/nieh/index.html> | <https://www.biology.ucsd.edu/labs/nieh/index.html> | <https://labs.biology.ucsd.edu/nieh/index.html> · 2026-10-16T00:59:50+00:00 | lab |
| 110 `ucsd-biology-topic-lab-pillus` | <http://biology.ucsd.edu/labs/pillus> | <https://biology.ucsd.edu/labs/pillus> | <https://labs.biology.ucsd.edu/pillus/> · 2026-10-16T01:00:01+00:00 | lab |
| 113 `ucsd-biology-topic-lab-ralph-greenspan` | <http://greenspanlab.ucsd.edu> | <https://greenspanlab.ucsd.edu/> | <https://greenspanlab.ucsd.edu/> · 2026-10-16T01:04:21+00:00 | lab |
| 114 `ucsd-biology-topic-lab-rifkin` | <http://www.biology.ucsd.edu/labs/rifkin/index.html> | <https://www.biology.ucsd.edu/labs/rifkin/index.html> | <https://labs.biology.ucsd.edu/rifkin/index.html> · 2026-10-16T00:59:52+00:00 | lab |
| 120 `ucsd-biology-topic-lab-schroeder` | <http://www-biology.ucsd.edu/labs/schroeder/index.html> | <https://www-biology.ucsd.edu/labs/schroeder/index.html> | <https://labs.biology.ucsd.edu/schroeder/index.html> · 2026-10-16T00:59:40+00:00 | lab |
| 131 `ucsd-biology-topic-lab-suel-gurol` | <http://labs.biology.ucsd.edu/suel> | <https://labs.biology.ucsd.edu/suel> | <https://suellab.github.io/> · 2026-10-16T01:04:42+00:00 | lab |
| 137 `ucsd-biology-topic-lab-villa-elizabeth` | <http://villalab.ucsd.edu> | <https://villalab.ucsd.edu/> | <https://villalab.ucsd.edu/> · 2026-10-16T01:04:46+00:00 | lab |
| 139 `ucsd-biology-topic-lab-wilhelm-lab` | <http://biology.ucsd.edu/labs/wilhelm/index.htm> | <https://biology.ucsd.edu/labs/wilhelm/index.htm> | <https://labs.biology.ucsd.edu/wilhelm/index.htm> · 2026-10-16T01:00:02+00:00 | lab |
| 146 `ucsd-biology-topic-lab-zuniga-lab` | <http://www.biology.ucsd.edu/labs/zuniga> | <https://www.biology.ucsd.edu/labs/zuniga> | <https://labs.biology.ucsd.edu/zuniga/> · 2026-10-16T01:00:00+00:00 | lab |
| 367 `ucsd-physics-research-site-kaixuan-ni` | <http://nigroup.ucsd.edu> | <https://nigroup.ucsd.edu/> | <https://nigroup.ucsd.edu/> · 2026-10-16T01:05:25+00:00 | research_group |
| 369 `ucsd-physics-research-site-leonid-v-butov` | <http://butovgroup.ucsd.edu> | <https://butovgroup.ucsd.edu/> | <https://butovgroup.ucsd.edu/> · 2026-10-16T01:05:25+00:00 | research_group |
| 372 `ucsd-physics-research-site-m-brian-maple` | <http://mbmlab.ucsd.edu> | <https://mbmlab.ucsd.edu/> | <https://mbmlab.ucsd.edu/> · 2026-10-16T01:05:26+00:00 | research_group |
| 373 `ucsd-physics-research-site-massimo-vergassola` | <http://vergassolalab.ucsd.edu> | <https://vergassolalab.ucsd.edu/> | <https://vergassolalab.ucsd.edu/> · 2026-10-16T01:05:27+00:00 | research_group |
| 551 `ucsd-live-lab-0cb7961b3add03` | <http://muscle.ucsd.edu/> | <https://muscle.ucsd.edu/> | <https://muscle.ucsd.edu/> · 2026-10-16T01:06:37+00:00 | lab |
| 687 `ucsd-chemistry-biochemistry-lab-burkart-laboratory` | <http://burkartlab.ucsd.edu> | <https://burkartlab.ucsd.edu/> | <https://burkartlab.ucsd.edu/> · 2026-10-16T01:07:06+00:00 | lab |
| 696 `ucsd-chemistry-biochemistry-lab-kubiak-research-group` | <http://kubiak.ucsd.edu> | <https://kubiak.ucsd.edu/> | <https://kubiak.ucsd.edu/> · 2026-10-16T01:07:10+00:00 | research_group |
| 700 `ucsd-chemistry-biochemistry-lab-o-connor-group` | <http://oconnorgroup.ucsd.edu/> | <https://oconnorgroup.ucsd.edu/> | <https://oconnorgroup.ucsd.edu/> · 2026-10-16T01:07:11+00:00 | research_group |
| 701 `ucsd-chemistry-biochemistry-lab-paesani-research-group-laboratory-for-theoretical-and-computational-chemistry` | <http://paesanigroup.ucsd.edu> | <https://paesanigroup.ucsd.edu/> | <https://paesanigroup.ucsd.edu/> · 2026-10-16T01:07:12+00:00 | research_group |
| 704 `ucsd-chemistry-biochemistry-lab-romero-polymer-lab` | <http://romeropolymerlab.ucsd.edu> | <https://romeropolymerlab.ucsd.edu/> | <https://romeropolymerlab.ucsd.edu/> · 2026-10-16T01:07:14+00:00 | lab |
| 706 `ucsd-chemistry-biochemistry-lab-schimpf-lab` | <http://schimpflab.ucsd.edu> | <https://schimpflab.ucsd.edu/> | <https://schimpflab.ucsd.edu/> · 2026-10-16T01:07:14+00:00 | lab |
| 711 `ucsd-chemistry-biochemistry-lab-tor-lab` | <http://torgroup.ucsd.edu> | <https://torgroup.ucsd.edu/> | <https://torgroup.ucsd.edu/> · 2026-10-16T01:07:16+00:00 | lab |
| 713 `ucsd-chemistry-biochemistry-lab-yang-research-group-jerry-yang` | <http://yanglab.ucsd.edu> | <https://yanglab.ucsd.edu/> | <https://yanglab.ucsd.edu/> · 2026-10-16T01:07:16+00:00 | research_group |
| 715 `ucsd-chemistry-biochemistry-lab-yuen-zhou-group` | <http://yuenzhougroup.ucsd.edu/> | <https://yuenzhougroup.ucsd.edu/> | <https://yuenzhougroup.ucsd.edu/> · 2026-10-16T01:07:17+00:00 | research_group |
| 724 `ucsd-biochemistry-and-molecular-biophysics-lab-joseph-lab` | <http://josephgroup.ucsd.edu/> | <https://josephgroup.ucsd.edu/> | <https://josephgroup.ucsd.edu/> · 2026-10-16T01:06:15+00:00 | research_group |
| 726 `ucsd-biochemistry-and-molecular-biophysics-lab-komor-lab` | <http://komorlab.ucsd.edu> | <https://komorlab.ucsd.edu/> | <https://komorlab.ucsd.edu/> · 2026-10-16T01:06:15+00:00 | lab |
| 732 `ucsd-biochemistry-and-molecular-biophysics-lab-toor-lab` | <http://rna.ucsd.edu/> | <https://rna.ucsd.edu/> | <https://rna.ucsd.edu/> · 2026-10-16T01:07:22+00:00 | lab |
| 733 `ucsd-biochemistry-and-molecular-biophysics-lab-zid-lab` | <http://zidlab.ucsd.edu> | <https://zidlab.ucsd.edu/> | <https://zidlab.ucsd.edu/> · 2026-10-16T01:06:18+00:00 | lab |
| 807 `ucsd-biological-sciences-lab-kadonaga-lab` | <http://biology.ucsd.edu/research/faculty/jkadonaga> | <https://biology.ucsd.edu/research/faculty/jkadonaga> | <https://biology.ucsd.edu/research/faculty/jkadonaga> · 2026-10-16T01:07:32+00:00 | lab |
| 808 `ucsd-biological-sciences-lab-yelon-lab` | <http://biology.ucsd.edu/research/faculty/dyelon> | <https://biology.ucsd.edu/research/faculty/dyelon> | <https://biology.ucsd.edu/research/faculty/dyelon> · 2026-10-16T01:07:33+00:00 | lab |
| 809 `ucsd-biological-sciences-lab-lykke-andersen-lab` | <http://biology.ucsd.edu/research/faculty/jlykkeandersen> | <https://biology.ucsd.edu/research/faculty/jlykkeandersen> | <https://biology.ucsd.edu/research/faculty/jlykkeandersen> · 2026-10-16T01:07:34+00:00 | lab |
| 810 `ucsd-biological-sciences-lab-kryazhimskiy-lab` | <http://biology.ucsd.edu/research/faculty/skryazhimskiy> | <https://biology.ucsd.edu/research/faculty/skryazhimskiy> | <https://biology.ucsd.edu/research/faculty/skryazhimskiy> · 2026-10-16T01:07:35+00:00 | lab |
| 811 `ucsd-biological-sciences-lab-jackrel-lab` | <http://biology.ucsd.edu/research/faculty/sjackrel> | <https://biology.ucsd.edu/research/faculty/sjackrel> | <https://biology.ucsd.edu/research/faculty/sjackrel> · 2026-10-16T01:07:37+00:00 | lab |
| 812 `ucsd-biological-sciences-lab-halpain-lab` | <http://biology.ucsd.edu/research/faculty/shalpain> | <https://biology.ucsd.edu/research/faculty/shalpain> | <https://biology.ucsd.edu/research/faculty/shalpain> · 2026-10-16T01:07:38+00:00 | lab |
| 813 `ucsd-biological-sciences-lab-posakony-lab` | <http://biology.ucsd.edu/research/faculty/jposakony> | <https://biology.ucsd.edu/research/faculty/jposakony> | <https://biology.ucsd.edu/research/faculty/jposakony> · 2026-10-16T01:07:39+00:00 | lab |
| 814 `ucsd-biological-sciences-lab-reinagel-lab` | <http://biology.ucsd.edu/research/faculty/preinagel> | <https://biology.ucsd.edu/research/faculty/preinagel> | <https://biology.ucsd.edu/research/faculty/preinagel> · 2026-10-16T01:07:39+00:00 | lab |
| 820 `ucsd-electrical-and-computer-engineering-lab-ndao-lab` | <http://ndao.ucsd.edu/> | <https://ndao.ucsd.edu/> | <https://ndao.ucsd.edu/> · 2026-10-16T01:07:34+00:00 | lab |
| 826 `ucsd-structural-engineering-lab-m2do-multiscale-multiphysics-design-optimization-laboratory` | <http://m2do.ucsd.edu/> | <https://m2do.ucsd.edu/> | <https://m2do.ucsd.edu/> · 2026-10-16T01:00:49+00:00 | lab |
| 833 `ucsd-structural-engineering-lab-fluid-effects-on-structural-systems-research-group-fessrg` | <http://fessrg.ucsd.edu/> | <https://fessrg.ucsd.edu/> | <https://fessrg.ucsd.edu/> · 2026-10-16T01:00:51+00:00 | research_group |

## 审计输入与边界

- Inventory SHA：`29116241ba3db1dbd29661cc9cedf28308acc860d5ecaa09220a197365c68da0`。
- 原 baseline SHA：`ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e`。
- Manifest SHA：`9724d5ab8abac1edd28234aa06094146a5d376efce89cd7d6a5f4d738c4113e0`。
- Identity decisions SHA：`4679d8fdce45060b170e47a821e1ea1f4b6ffebffbb9815e82c9d5c97c369ee1`。
- summaries.jsonl SHA：`e7c4b94c22acd1a7a870db3ee42b5f769096bd76e27d2709440c99f7b096825e`。
- url-verification.jsonl SHA：`13c721f59e7796a6fab36b73d23df3bb5e6c96006fbe15a665e07a0a39b2e14b`。
- JSON 列出全部输入 hash、逐 ID original/capture tuple、18 项检查、每条真实 reviewedAt 和 48 个唯一原 URI、17 条空根路径与 `/` 的等价表示。collector queue 仅作为只读瞬时快照，hash 记录所读取字节，不声称活动采集器之后不再变化。
- 无科研 record、packet、projection、代码、alias、collector 或 shared-clock 写入；13 条身份争议的接受边界未改变。
