# Literal historical profile link: independent test plan and result

审阅完成：2026-10-16T06:43:20+00:00。仅新增`tests/test_local_lab_profile_link_gaps.py`与本报告。没有修改production、真实records/packets、源快照、网络receipt、采集器或共享状态；0网络。测试仅在独立临时worktree运行，真实subprocess transport、fetcher加载及PID探测均被fixture禁止；执行测试复用实际summary journal/instrumenter，transport为离线fake。

**最终35 tests PASS，0 failures、0 errors；无本轮测试发现的剩余问题。** 这只证明离线准入/plan/journal判据，不代替parent的独立代码审阅、真实七pin/进程/冷却核验或新响应的人工身份/科研审阅。

## Frozen real-source oracles

固定baseline SHA为`ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e`。三条目标的source URL、原时间、HTML与sidecar SHA在本次独立读取中与own immutable snapshot精确相符；这里的profile是发现关系的历史来源，不是新获取的研究正文。

| stable ID / official historical profile | original observedAt | 实际href / 标签 | 绑定的labWebsiteUrl完整proof SHA |
|---|---|---|---|
| `ucsd-pathology-lab-aaron-carlin-lab` / [Aaron Carlin](https://profiles.ucsd.edu/aaron.carlin) | 2026-10-07T22:17:28+00:00 | `http://homer.ucsd.edu/CarlinLab/index.html` / Carlin Lab Website | `c2ee6b2eaa7362ca6dafbc8d2e57597d3cdb0b08cc840038a5ed4b9dda3819bb` |
| `ucsd-live-lab-c53a46a8ac4496` / [Ludmil Alexandrov](https://profiles.ucsd.edu/ludmil.alexandrov) | 2026-10-07T22:09:38+00:00 | `http://alexandrov.ucsd.edu/` / Alexandrov Lab | `b397097c29947997da5b54906adef4b1ab8936ddd0c828c4aefa6f47914cd9c5` |
| `ucsd-live-lab-48e8d895726620` / [Don Cleveland](https://profiles.ucsd.edu/don.cleveland) | 2026-10-07T22:04:19+00:00 | `http://cmm.ucsd.edu/cleveland/home.html` / Lab Site | `85d513feb648380af2f996cc6f5b23414728f19089e22f539d8d223b039efc64` |

原HTML SHA依次为：

- Carlin `7489a5991ca6230a27e2051274abd7ad56014a37dbc5f090cb8f0fd57f4861cc`；original sidecar `ff236a6a55d38647a78622e2ac6cea5ab082f8e9ac74942665a75f19bad477f3`。
- Alexandrov `9a009a30e1850d53bda9e9430268ccae158f0d1afe86767ca09d4abbe8874f38`；sidecar `667f20ab0602d97be5cc50f9a7cfa363364ba08d0c737f96d8b056a8924dc3a7`。
- Cleveland `f29fb590ced0dfa0e19df60bf0fbeaefabd6ccc7238fdab3568e33e9a5429f43`；sidecar `0793be8babf83fb878947b2de9a9e95ca4b49f80f716611d15657d3a9da5088e`。

三条listedWebsite仍是对应同host/path/query的HTTPS地址。旧字段证据中HTTPS不被改写；actual href HTTP独立保存。Cleveland必须绑定10/07的`official_profile_generic_lab_link` labWebsiteUrl proof；不能把10/03的labName proof日期借给10/07 capture。通用Lab Site只提供路由线索，不自动命名实验室、补PI、认定alias或接受科研。三条源快照复制时间也不成为新的source observedAt。

实际`reviewed-profile-lab-links.json`读取快照SHA为`c239a8e63f0aa3fd37804970caf9568dafec3db98e7dec5d1839437097d78a05`，三项均为2,000,000字节。该manifest仅作本次数据绑定事实，不由本测试写入或重新plan。

**Firestein明确排除**：[历史官方profile](https://profiles.ucsd.edu/gary.firestein)虽有HTTP Firestein Lab锚点，但实际HTTP-origin robots缓存已在2026-10-16T06:18:43+00:00记录302 / unavailable / robots_redirect_is_not_a_robots_file。不得因另一profile锚点再次探测目标。Carlin/Alexandrov冻结的HTTPS robots TLS失败要原样保留；它们不等于已经请求过独立字面HTTP URI，也不意味着HTTP机器人已允许。Carlin HTTP robots已有05:33:45的404 not_found；后续能否复用、需要正常获取robots或退让由正常fetcher/gate决定。

本次queue快照时间06:36:22，未见上述三个HTTP精确target的实际尝试；没有宣称未来仍无相同target排队、无同host其他工作或不需fresh preflight。

## Independent admission oracles

| 组 | 必须通过的正例 | 必须拒绝/关闭的关键反例 |
|---|---|---|
| 独立合同 | 新kind `reviewed_profile_lab_link_gap`，observationScope=related_historical_profile_link_only，notAnOriginalListedURLCheck=true，2M；baseline未查明PI保留。 | 不能借新条目放松旧reviewed_original_uri_observations；listedHTTPS仍非“原列出HTTP检查”，不得伪装listed_url_direct_provenance_gap。 |
| 冻结记录 | labId、baseline SHA、raw/packet整字节SHA及完整latestDestinationFetch全部相符。 | 缺字段、错purpose、无时区reviewedAt、bool代替True、未知ID、raw/packet被改、nested fetch/robots字段被改，即使只重算raw/packet hash也不代替原fetch冻结。 |
| 来源链 | baseline lab.professorIds包含该professorId、其officialProfileUrl为该精确HTTPS profile；verified labWebsiteUrl fullproof的source URL/time/method/label/列出URL及完整JSON SHA一致。 | 无professor关系、另一PI profile、unverified proof、research overview代替link proof、过时日期、重新hash但错误status/method/evidence/sourceURL、漏掉proof额外字段均拒绝。 |
| capture | OUT内真实immutable body/sidecar，两个字节hash、原source/final URL、original observedAt、body SHA、HTTP200及ok一致。 | 篡改字节但沿用旧hash、source URL/time/HTTP状态变化、bool HTTP200、另一个profile、OUT外真实文件/指向OUT外的解析路径拒绝；不允许用review时间替代观察时间。 |
| DOM | 实际`ctl00_divProfilesContentMain`中FeaturedContent→webpage范围内的visible真实a，href和label精确相符。 | 缺main wrapper、缺FeaturedContent/webpage层、script/comment/template/nav/hidden/aria-hidden/display:none/visibility:hidden中的伪anchor、错标签、猜href、只有文本URL均不得发现。 |
| URI | actual anchor HTTP与冻结listed HTTPS仅scheme不同；同exact host、path（含大小写/非根尾slash）、query。 | www或其他host、大小写不同path、query变更、非根尾slash、其它协议、port、fragment（含空#）、UCSD伪后缀、任意空白/C0/DEL均拒绝；不能先strip/urlsplit修复。 |
| 实际尝试 | queue标签写HTTP但actual fetch只做HTTPS时，不据normalized key误关闭HTTP；bare redirect.to也不伪造已请求证明。 | 精确HTTP checked/blocked URI、redirect.from、含真实HTTP100..599状态的final URI、pending/running精确target、top-level attemptHistory、durable start/orphan wire均关闭一次性准入。 |
| 拒绝优先 | 原HTTPS纯TLS失败不自动变成跨scheme访问拒绝；404 robots not_found与拒绝区分。 | 401/403、auth/challenge/robots-denied、HTTP200登录final/blocked/redirect、transportStatus投影分类，以及nested robots登录均关闭；不能借另一个scheme绕过。覆盖Google/Microsoft、shibboleth.ucsd.edu、/oauth2/authorize及/login.aspx。 |
| HTTP robots | 正常checked/not_found观察可进入后续正常fetch判定。 | exact HTTP-origin unavailable无论来自sidecar还是capture metadata均关闭；explicit denial/challenge优先，较新非拒绝不得抹去；时区按实际时刻比较，同时间冲突failclosed。 |
| 资源 | 固定page/redirect 2M、robots300k。 | 8M、float/bool cap或其它扩大值均拒绝；不得借旧两项8M例外扩到本合同；TLS验证、robots、共享v2流程保持正常。 |

## Plan and execution journal oracles

实际`plan()`在临时worktree运行：HTTPS关联capture不使HTTP candidate误变成captured；新kind采用精确request lookup；不会自动改root/source/identity/affiliation/PI或原preparedAt。成功、返回curl code0、普通Exception、KeyboardInterrupt、初始HTTP301后robots异常均使用实际summary execute/instrumented journal流程，只有transport被fake。

- robots/page前先持久写start，journalContextKind为新kind、notAnOriginalListedURLCheck=true、journalIsNotPageRequestProof=true；一次性关闭可复用旧journal，但语义不成为“原HTTPS已查”。
- 普通Exception保存fetch_exception并重抛；无响应时不得伪造httpStatus/finalUrl/body hash/actualPageRequestMade/liveCheckedAt。KeyboardInterrupt不吞掉，durable start与orphan event足以阻止重排。
- 返回code0能证明一次实际页面transport尝试，但不是成功或身份接受；只有开始event未返回tuple不能证明页面。
- 初始HTTP301已返回，而后redirect目标robots失败，仍可证明初始HTTP页面尝试；不得编造成功final URL或HTTP重定向终点。
- 每个生命周期finally恢复page cap=2M和currentOriginalObservationUrl=None，robots维持300k。raw/packet/profile bytes原样，重复plan不重新live。

这些fake-transport测试不能声称本次重新验证了真实fcntl锁互斥或真实TLS握手；它们验证新合同进入既有执行流程后journal/大小限制/元数据语义。真实共享v2与七pin仍须沿用已审代码及parent的fresh gate检查。

## Actual test runs and final hash binding

首轮开发中30 tests出现3个subtest失败：前导空格、前导换行、path TAB在request_key/urlsplit归一后错误准入；已即时报告parent。首轮源码与并行修改未冻结，不将后续hash追溯赋给该首轮。Parent加入URI解析前显式拒绝后，33 tests通过。随后补齐旧original_uri合同隔离及完全重新hash后的unverified/non-link fieldproof拒绝，最终固定为35 tests。

最终实际运行：2026-10-16T06:42:03+00:00；`unittest.defaultTestLoader.discover('tests', pattern='test_local_lab_profile_link_gaps.py')` + TextTestRunner；35 tests，0.356秒，0 failure/error。运行前后下列两个SHA精确相同：

- adapter `scripts/local_lab_summary_gaps.py`：`76d7631f8235c540023841c0cdb41c9d59e0c2c83892f3a261de8406dc1e6bbf`
- 独立测试`tests/test_local_lab_profile_link_gaps.py`：`09961c30ebe701640877bb842b35438ab00c507ce6c062fb7b90d681f857773a`

复现命令：`python3 -B -m unittest discover -s tests -p 'test_local_lab_profile_link_gaps.py' -q`。本次没有运行真实plan、execute、collector或任何网络，也未重跑其它测试套件。当前35项判据无剩余失败；parent的后续真实响应、身份/研究接受及当前状态审阅不属于本报告。
