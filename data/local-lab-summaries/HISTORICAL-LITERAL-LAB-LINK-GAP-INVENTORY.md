# 历史字面 Lab Website 协议差异缺口清单

实际元数据复核：2026-10-16T06:32:49+00:00。0网络请求；未改代码、records、packets、collector、主checkout、计划或准入receipt。四条均为后续候选，均非本次已抓取或已准入。

| 条目 | 原HTML字面HTTP href | profile原始capture UTC | baseline sourceUrls原含HTTP | 当前边界/决定 |
|---|---|---|---|---|
| 294 Aaron Carlin Lab | [Carlin Lab Website](http://homer.ucsd.edu/CarlinLab/index.html) | 2026-10-07T22:17:28+00:00 | 是 | 目标无实际请求证据；另行有限准入审阅候选 |
| 223 Firestein Lab | [Firestein Lab](http://raidivision.ucsd.edu/research/firestein-lab/Pages/default.aspx) | 2026-10-07T22:37:39+00:00 | 是 | HTTP-origin robots实际302不可用；暂不安排页面请求 |
| 447 Alexandrov Lab | [Alexandrov Lab](http://alexandrov.ucsd.edu/) | 2026-10-07T22:09:38+00:00 | 否 | 目标无实际请求证据；另行有限准入审阅候选 |
| 621 Lab Site | [Lab Site](http://cmm.ucsd.edu/cleveland/home.html) | 2026-10-07T22:04:19+00:00 | 否 | 目标无实际请求证据；另行有限准入审阅候选 |

四个原始HTML锚点均逐字核验，来源URL/原observedAt/bodySHA/sidecarSHA与已审历史缓存匹配，不从HTTPS改写生成HTTP。collector当前queue及response缓存、own gap-results/items/wireEvents/one-shot journal均未见这四个精确HTTP目标的实际请求；四个目标亦无401、403、challenge或明确robots deny证据。这里只报告所查记录范围，不宣称不存在未留存的全球历史请求。

Firestein有具体同源前置边界：collector检查同HTTP origin另一条Terkeltaub路径时，`http://raidivision.ucsd.edu/robots.txt` 于2026-10-16T06:18:43+00:00实际302，error=`robots_redirect_is_not_a_robots_file`，状态unavailable。它不是明确robots规则拒绝，但当前正常gate无法继续页面请求，不能换路径或把302 HTML当robots规则。Carlin同HTTP origin robots于05:33:45为404；Alexandrov/Cleveland未找到HTTP-origin robots缓存，未来仍须正常前置检查。

四者baseline列出URL和当前packet列出URL均为HTTPS。Carlin与Firestein的baseline sourceUrls原已精确含HTTP；四者fieldEvidence文本都没有精确HTTP目标，旧字段多为HTTPS。Alexandrov/Cleveland仅由实际历史profile原HTML锚点补足HTTP发现证明。Firestein另有旧baseline HTTP websiteCheck=unavailable，只有历史状态和时间，不能当本轮目标实际请求证明。所有旧事实继续保留。

现有reviewed-original-uri contract要求baseline listed本来精确为HTTP，entry.url、baseline.labWebsiteUrl和packet.listedWebsite一致，因此四项均不能直接套用。若下一步考虑观察，须单独冻结有限literal-profile-link合同，锁稳定ID、原HTTPS listed、精确HTTP原href/label、profile原始capture元组、sidecar SHA及现根fetch；观察不改变canonical URL、研究/身份接受或mismatch门槛。

后续若另行准入，正常HTTP robots和共享host gate先行，保留拒绝、challenge、cap、DNS边界；不得禁TLS、登录或绕过，不增2M默认上限、不自动重试。实际redirect到HTTPS仍正常校验TLS及目标robots。Cleveland原标签只是Lab Site，观察地址不确认实验室命名或整体研究。Jamieson227及Hamilton619/620已读锚点均为HTTPS精确匹配，未产生其他协议差异候选。

JSON含逐项原HTML字面anchor、profile原元组、baseline字段证明、当前HTTPS fetch/attempt历史、HTTP缓存/ledger检索结果、robots证据及fingerprint。
