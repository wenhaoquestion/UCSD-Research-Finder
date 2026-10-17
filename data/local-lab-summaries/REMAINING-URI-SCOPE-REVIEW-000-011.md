# 剩余原 URI 范围审阅：索引 000–011

实际复核时间：2026-10-16T04:37:28+00:00。**metadataOnly；0 network requests。** 仅新增本 Markdown 与同名 JSON，未改 records、packets、projections、代码或 collector/shared 状态。

12/12 条均与原 baseline 的稳定 ID 和 literal HTTP 地址一致；按严格 URI 去重为 12 个。与 13 条身份争议记录交集为 0。当前 collector queue/attemptHistory 和 summary gap ledger 均没有这 12 个原 HTTP URI 的实际请求或前置检查；旧历史 websiteCheck 仍保留，不宣称历史从未检查。

**决定：12 条可列为一次原 literal HTTP 的公共只读路由核验 candidate，全部仍受正常 robots/access/TLS/共享 gate/2MB 等规则约束。** 这里不授予跳过 robots 的页面访问，也不接受实体、升级科研或确认别名。Sung 应特别标为“HTTP-origin robots 前置结果可能即终点”；既有 HTTPS robots 的三次 TLS35 失败不得清除或绕过。

现有 HTTPS 元数据：9 条 status=ok；2 条 HTTP404；1 条（Sung）robots_unavailable，未请求页面。既有实体接受状态：8 accepted_lab_group，4 provisional_or_unresolved。获准观察原地址不取决于当前科学接受状态；成功传输更不能使 unresolved/partial 或 root identity uncertain 自动接受。

## 必须维持的执行范围

- 初始 URI 只能取原 baseline literal HTTP；保留 host/path/query。空 path 与 `/` 仅表示相同根请求目标，不发明新 path、域名或错误后改协议的备用地址。
- 先依既有策略检查 HTTP 原点 robots（可用合法同原点缓存规则）；HTTPS robots 不能代替。遇 robots refusal/unavailable、认证或 challenge，应停止并记录访问前置结果。
- 仅沿真实 HTTP Location 跳转，逐跳 public-origin、认证及目标 robots 检查；HTTPS 继续正常 TLS 验证。HTML meta、frames 和导航链接不自动触发请求。
- 保留共享 v2 host gate、延迟/并发/cooldown/Retry-After、正常机器人及传输重试预算、redirect limit 与 **2,000,000-byte cap**；不 reset 次数、不提上限、不禁用 TLS、不登录、不绕拒绝。
- 一次原 URI fetch lifecycle 可能包含 robots/真实跳转多条 wire，不应把 12 candidates 当作12 wires。真实原请求时间/状态/raw Location/chain/final/hash 与仅前置失败都须如实保留。
- 新内容与实体身份须后续独立审阅；13 mismatch 接受 gate 不变，不能据 HTTP200、meta提示或个人 API 自动接受。

## 逐项决定

### 000 · ucsd-lab-from-faculty-sung-lab-eng-ucsd-edu

- **可安排原 URI 规则内核验**：<http://sung-lab.eng.ucsd.edu/>；HTTP robots 原点 <http://sung-lab.eng.ucsd.edu/robots.txt>。
- 实际既有请求：<https://sung-lab.eng.ucsd.edu/>，observedAt `2026-10-16T03:49:32+00:00`；status `robots_unavailable`，HTTP `未请求页面`，final `None`。
- Robots：`https://sung-lab.eng.ucsd.edu/robots.txt`；原时间 `2026-10-16T03:49:32+00:00`；status `unavailable`，HTTP `0`，attempts `3`。
- 既有 error：`curl: (35) LibreSSL SSL_connect: SSL_ERROR_SYSCALL in connection to sung-lab.eng.ucsd.edu:443`。
- 原 baseline 已存 Sung HTTP 根地址。相关 HTTPS 尚未请求页面：robots.txt 三次尝试均为 curl 35 TLS 错误。仅可按原 HTTP 原点执行正常 robots 前置检查；前置规则不满足即停，不重置/抹除 HTTPS 三次失败，不禁用 TLS。后续真实页面若跳 HTTPS 仍正常验证 TLS，失败即保留失败。路由核验不等于接受 Sung 别名或现时网站身份。
- 当前 raw `supported`；pageIdentity `uncertain`；entity acceptance `accepted_lab_group`，全部保持。
- 复核 `2026-10-16T04:37:27+00:00`，metadataOnly=true，0 requests；原 meta 位于 `packets/ucsd-lab-from-faculty-sung-lab-eng-ucsd-edu.json#/latestDestinationFetch`。
- Packet SHA `c0e555ff2f56362b0ce230d5bd4d5d5a2693ecdf053283b8b8fd501adc08678f`；record SHA `0cb8e21d465b7cecf28a99fd048165b3ae6af959291e06e2e89f08818a6e40a5`。

### 001 · ucsd-biology-topic-lab-bennett-lab

- **可安排原 URI 规则内核验**：<http://labs.biology.ucsd.edu/bennett>；HTTP robots 原点 <http://labs.biology.ucsd.edu/robots.txt>。
- 实际既有请求：<https://labs.biology.ucsd.edu/bennett>，observedAt `2026-10-16T01:03:53+00:00`；status `ok`，HTTP `200`，final `https://labs.biology.ucsd.edu/bennett/`。
- Robots：`https://labs.biology.ucsd.edu/robots.txt`；原时间 `2026-10-16T00:59:35+00:00`；status `checked`，HTTP `200`，attempts `未单列`。
- 既有 error：`无`。
- 原 baseline 已存 Bennett HTTP 地址。相关 HTTPS 根页成功，但根页主要为 HTML meta refresh，既有实验室研究来自已分别审阅的目标页。可独立核验原 HTTP，不能自动执行 HTML meta refresh、补写成 HTTP redirect 或接受规范网址迁移；新根目的页身份仍须另审。
- 当前 raw `supported`；pageIdentity `uncertain`；entity acceptance `accepted_lab_group`，全部保持。
- 复核 `2026-10-16T04:37:27+00:00`，metadataOnly=true，0 requests；原 meta 位于 `packets/ucsd-biology-topic-lab-bennett-lab.json#/latestDestinationFetch`。
- Packet SHA `86f13db982b3c09932c5b936af573c8c6e789b77e1062c9dea533fef3d8bb6a4`；record SHA `fa93e9d259830ee980d5067405163144563db60e90985259d79ff6c4519bc774`。

### 002 · ucsd-biology-topic-lab-bier

- **可安排原 URI 规则内核验**：<http://bierlab.ucsd.edu>；HTTP robots 原点 <http://bierlab.ucsd.edu/robots.txt>。
- 实际既有请求：<https://bierlab.ucsd.edu/>，observedAt `2026-10-16T01:03:54+00:00`；status `ok`，HTTP `200`，final `https://bierlab.ucsd.edu/`。
- Robots：`https://bierlab.ucsd.edu/robots.txt`；原时间 `2026-10-16T01:03:53+00:00`；status `not_found`，HTTP `404`，attempts `未单列`。
- 既有 error：`无`。
- 原 baseline 已存 Bier HTTP 根地址（空 path 的有效请求目标为 /）。相关 HTTPS 为 HTML meta refresh 壳页，已审研究来自另一个独立跟进来源。可做原 HTTP 路由观察；不把 meta 当服务器跳转，不预先接受目的页身份。
- 当前 raw `supported`；pageIdentity `uncertain`；entity acceptance `accepted_lab_group`，全部保持。
- 复核 `2026-10-16T04:37:28+00:00`，metadataOnly=true，0 requests；原 meta 位于 `packets/ucsd-biology-topic-lab-bier.json#/latestDestinationFetch`。
- Packet SHA `4cdfa68778a8c199f22049a0706ffee9cc788829a8fdb751b19601007c382a5e`；record SHA `ae4c8d8b147c854ea493ec1784d2f34e4b10cc37c85b9c5762ae10d2f2e74a6d`。

### 003 · ucsd-biology-topic-lab-firtel

- **可安排原 URI 规则内核验**：<http://people.biology.ucsd.edu/firtel>；HTTP robots 原点 <http://people.biology.ucsd.edu/robots.txt>。
- 实际既有请求：<https://people.biology.ucsd.edu/firtel>，observedAt `2026-10-16T01:04:03+00:00`；status `ok`，HTTP `200`，final `https://people.biology.ucsd.edu/firtel/`。
- Robots：`https://people.biology.ucsd.edu/robots.txt`；原时间 `2026-10-16T01:04:02+00:00`；status `not_found`，HTTP `404`，attempts `未单列`。
- 既有 error：`无`。
- 原 baseline 已存 Firtel HTTP 地址。相关 HTTPS 是可访问的 Lab Members 页面，当前 pageIdentity 仍 uncertain；身份/研究既有结论不等于这次目的页已绑定。可检查原 HTTP，之后依据真实来源另审，不在本元数据审阅追加 title 身份引文。
- 当前 raw `supported`；pageIdentity `uncertain`；entity acceptance `accepted_lab_group`，全部保持。
- 复核 `2026-10-16T04:37:28+00:00`，metadataOnly=true，0 requests；原 meta 位于 `packets/ucsd-biology-topic-lab-firtel.json#/latestDestinationFetch`。
- Packet SHA `960ff1183096e07a5496f763d0e133e9d478d714cf02f55a1c7aece068fa4542`；record SHA `3e482a3d5577cb942e99d27576eae4630fd44ef805eab598243dd151750e03fa`。

### 004 · ucsd-biology-topic-lab-goldrath

- **可安排原 URI 规则内核验**：<http://biology.ucsd.edu/labs/goldrath>；HTTP robots 原点 <http://biology.ucsd.edu/robots.txt>。
- 实际既有请求：<https://biology.ucsd.edu/labs/goldrath>，observedAt `2026-10-16T00:59:53+00:00`；status `ok`，HTTP `200`，final `https://goldrathlab.com/`。
- Robots：`https://goldrathlab.com/robots.txt`；原时间 `2026-10-16T00:59:51+00:00`；status `checked`，HTTP `200`，attempts `未单列`。
- 既有 error：`无`。
- 原 baseline 已存 Goldrath HTTP 地址。相关 HTTPS 已观测到一条后续实际请求目标链，最终页面虽成功，当前 root pageIdentity 未具备匹配引用。可核验原 HTTP；旧 collector 未留原始 Location 头，不把旧 normalized to 值当 HTTP 原地址服务器跳转证明。
- 当前 raw `supported`；pageIdentity `uncertain`；entity acceptance `accepted_lab_group`，全部保持。
- 复核 `2026-10-16T04:37:28+00:00`，metadataOnly=true，0 requests；原 meta 位于 `packets/ucsd-biology-topic-lab-goldrath.json#/latestDestinationFetch`。
- Packet SHA `2bc33d95e34b40107491363d7b51d870d4fa469d1919cce85c3928e41f08f2a8`；record SHA `860014e284947c14a6b83a260b823cbf9a0cab747fea9c37a73ab49d5f23cdb4`。

### 005 · ucsd-biology-topic-lab-hampton

- **可安排原 URI 规则内核验**：<http://hamptonlab.ucsd.edu>；HTTP robots 原点 <http://hamptonlab.ucsd.edu/robots.txt>。
- 实际既有请求：<https://hamptonlab.ucsd.edu/>，observedAt `2026-10-16T01:04:03+00:00`；status `ok`，HTTP `200`，final `https://hamptonlab.ucsd.edu/`。
- Robots：`https://hamptonlab.ucsd.edu/robots.txt`；原时间 `2026-10-16T01:04:02+00:00`；status `checked`，HTTP `200`，attempts `未单列`。
- 既有 error：`无`。
- 原 baseline 已存 Hampton HTTP 根地址。相关 HTTPS 返回 Gadsby Website 占位页，实验室研究取自独立官方资料，不能以该占位页接受原网址身份。可做原 HTTP 公共路由观察；若仍为占位/无关内容，应保留身份未知，不扩展研究结论。
- 当前 raw `supported`；pageIdentity `uncertain`；entity acceptance `accepted_lab_group`，全部保持。
- 复核 `2026-10-16T04:37:28+00:00`，metadataOnly=true，0 requests；原 meta 位于 `packets/ucsd-biology-topic-lab-hampton.json#/latestDestinationFetch`。
- Packet SHA `f43025975f5ba6318e44d0cebd21d397b105a4d38e7e86a590b81dd210f108f2`；record SHA `416fde01d5e662acabfaeca998913d6d45a41dceffdd653cf0988668d461166e`。

### 006 · ucsd-biology-topic-lab-kiger

- **可安排原 URI 规则内核验**：<http://www.biology.ucsd.edu/labs/kiger>；HTTP robots 原点 <http://www.biology.ucsd.edu/robots.txt>。
- 实际既有请求：<https://www.biology.ucsd.edu/labs/kiger>，observedAt `2026-10-16T00:59:45+00:00`；status `ok`，HTTP `200`，final `https://labs.biology.ucsd.edu/kiger/`。
- Robots：`https://labs.biology.ucsd.edu/robots.txt`；原时间 `2026-10-16T00:59:35+00:00`；status `checked`，HTTP `200`，attempts `未单列`。
- 既有 error：`无`。
- 原 baseline 已存 Kiger HTTP 地址。相关 HTTPS 原根页是 HTML meta refresh 壳页，同站目标已独立审阅，但不等于原根 URI 已请求或 HTTP 重定向得到证明。可核验原 HTTP；不自动跟随 HTML meta、改 path 或接受别名。
- 当前 raw `supported`；pageIdentity `uncertain`；entity acceptance `accepted_lab_group`，全部保持。
- 复核 `2026-10-16T04:37:28+00:00`，metadataOnly=true，0 requests；原 meta 位于 `packets/ucsd-biology-topic-lab-kiger.json#/latestDestinationFetch`。
- Packet SHA `a955591373a1028890b4181cdaee530e4640b15ba4e14d2ec331012ee5b415b1`；record SHA `0ab55c17af5466d3eb840d9bdc22aa33f687659118e71eb532eebbb9b89c66d1`。

### 007 · ucsd-biology-topic-lab-murre

- **可安排原 URI 规则内核验**：<http://labs.biology.ucsd.edu/murre>；HTTP robots 原点 <http://labs.biology.ucsd.edu/robots.txt>。
- 实际既有请求：<https://labs.biology.ucsd.edu/murre>，observedAt `2026-10-16T01:04:16+00:00`；status `ok`，HTTP `200`，final `https://labs.biology.ucsd.edu/murre/`。
- Robots：`https://labs.biology.ucsd.edu/robots.txt`；原时间 `2026-10-16T00:59:35+00:00`；status `checked`，HTTP `200`，attempts `未单列`。
- 既有 error：`无`。
- 原 baseline 已存 Murre HTTP 地址。相关 HTTPS 200 可见正文不足，现有实体仍 unresolved/unconfirmed。原地址核验是独立的可观测路由问题，不要求预先接受实体；不能把成功请求或页面 title 自动升级为 lab 身份/科研。
- 当前 raw `unresolved`；pageIdentity `uncertain`；entity acceptance `provisional_or_unresolved`，全部保持。
- 复核 `2026-10-16T04:37:28+00:00`，metadataOnly=true，0 requests；原 meta 位于 `packets/ucsd-biology-topic-lab-murre.json#/latestDestinationFetch`。
- Packet SHA `028a6f31b86e28d211dae9cd1f17540e4e920e6b4aec47d3945196ca5578b125`；record SHA `c8e90867d5694a324430ccff6d8e2e226b0f394103f098b5f5729aa9b1c19c43`。

### 008 · ucsd-biology-topic-lab-spitzer

- **可安排原 URI 规则内核验**：<http://www.biology.ucsd.edu/labs/spitzer>；HTTP robots 原点 <http://www.biology.ucsd.edu/robots.txt>。
- 实际既有请求：<https://www.biology.ucsd.edu/labs/spitzer>，observedAt `2026-10-16T00:59:54+00:00`；status `ok`，HTTP `200`，final `https://labs.biology.ucsd.edu/spitzer/`。
- Robots：`https://labs.biology.ucsd.edu/robots.txt`；原时间 `2026-10-16T00:59:35+00:00`；status `checked`，HTTP `200`，attempts `未单列`。
- 既有 error：`无`。
- 原 baseline 已存 Spitzer HTTP 地址。相关 HTTPS 根页 meta refresh 与后来独立跟进站点的真实 HTTP 链分开保存；当前 root pageIdentity 未绑定。可检查原 HTTP，不把已知外站替换成本轮原 URI，不自动跟 meta 或接受迁移。
- 当前 raw `supported`；pageIdentity `uncertain`；entity acceptance `accepted_lab_group`，全部保持。
- 复核 `2026-10-16T04:37:28+00:00`，metadataOnly=true，0 requests；原 meta 位于 `packets/ucsd-biology-topic-lab-spitzer.json#/latestDestinationFetch`。
- Packet SHA `431dbee13223e4d0c66479ee1b19e2a2718e46361c04c48803d225b515b6aa0f`；record SHA `ccd2f4e6579a6cbfcec36e9bbf099929edfa54279844fb6895435cb37d26ad9f`。

### 009 · ucsd-biology-topic-lab-subramani

- **可安排原 URI 规则内核验**：<http://www.biology.ucsd.edu/labs/subramani>；HTTP robots 原点 <http://www.biology.ucsd.edu/robots.txt>。
- 实际既有请求：<https://www.biology.ucsd.edu/labs/subramani>，observedAt `2026-10-16T00:59:56+00:00`；status `http_error`，HTTP `404`，final `https://labs.biology.ucsd.edu/subramani`。
- Robots：`https://labs.biology.ucsd.edu/robots.txt`；原时间 `2026-10-16T00:59:35+00:00`；status `checked`，HTTP `200`，attempts `未单列`。
- 既有 error：`无`。
- 原 baseline 已存 Subramani HTTP 地址；相关 HTTPS 经旧记录链到目的路径返回 404，且没有研究来源。404 是已有相关地址结果，不是 robots/认证拒绝；可核验原 HTTP，若仍 404 就保留失败，不猜新 path、不据此判实验室关闭。
- 当前 raw `unresolved`；pageIdentity `uncertain`；entity acceptance `provisional_or_unresolved`，全部保持。
- 复核 `2026-10-16T04:37:28+00:00`，metadataOnly=true，0 requests；原 meta 位于 `packets/ucsd-biology-topic-lab-subramani.json#/latestDestinationFetch`。
- Packet SHA `e53c447d42859a6f71c718c8b29fe4651ee5739576ed333b289aaea46cdc8dcd`；record SHA `593061fbef3cef37b5c4f0229f93cdf677640e46cb77ec82daad18462672ec04`。

### 010 · ucsd-biology-topic-lab-yanofsky

- **可安排原 URI 规则内核验**：<http://labs.biology.ucsd.edu/yanofsky/home.html>；HTTP robots 原点 <http://labs.biology.ucsd.edu/robots.txt>。
- 实际既有请求：<https://labs.biology.ucsd.edu/yanofsky/home.html>，observedAt `2026-10-16T01:04:45+00:00`；status `ok`，HTTP `200`，final `https://labs.biology.ucsd.edu/yanofsky/home.html`。
- Robots：`https://labs.biology.ucsd.edu/robots.txt`；原时间 `2026-10-16T00:59:35+00:00`；status `checked`，HTTP `200`，attempts `未单列`。
- 既有 error：`无`。
- 原 baseline 已存 Yanofsky HTTP home.html。相关 HTTPS 是 frames fallback，既有身份 limited/partial 且研究正文不足。可核验同一原 HTTP 文件路由，不自动跟 frame 子页，不借传输成功扩展研究或实体接受。
- 当前 raw `partial`；pageIdentity `confirmed`；entity acceptance `provisional_or_unresolved`，全部保持。
- 复核 `2026-10-16T04:37:28+00:00`，metadataOnly=true，0 requests；原 meta 位于 `packets/ucsd-biology-topic-lab-yanofsky.json#/latestDestinationFetch`。
- Packet SHA `d6c57e878097d634cb60c738b31d0e6dd12bf38d7fc6d1c66fe6ecc93a245d39`；record SHA `ef4778f8272245e964dbfdf32b57f4ccff205a20b688d4c7decd3adf30e58594`。

### 011 · ucsd-physics-research-site-david-kleinfeld

- **可安排原 URI 规则内核验**：<http://physics.ucsd.edu/neurophysics>；HTTP robots 原点 <http://physics.ucsd.edu/robots.txt>。
- 实际既有请求：<https://physics.ucsd.edu/neurophysics>，observedAt `2026-10-16T01:05:22+00:00`；status `http_error`，HTTP `404`，final `https://physics.ucsd.edu/neurophysics`。
- Robots：`https://physics.ucsd.edu/robots.txt`；原时间 `2026-10-16T00:57:20+00:00`；status `checked`，HTTP `200`，attempts `未单列`。
- 既有 error：`无`。
- 原 baseline 已存 Kleinfeld HTTP neurophysics 路径。相关 HTTPS 原路径返回 404，可用其他资料为加载占位/教师 API，未确认研究组正文。可核验原 HTTP 原路径，不能发明新地址、改路径或以 API 接受实验室；失败仍原样保留。
- 当前 raw `unresolved`；pageIdentity `uncertain`；entity acceptance `provisional_or_unresolved`，全部保持。
- 复核 `2026-10-16T04:37:28+00:00`，metadataOnly=true，0 requests；原 meta 位于 `packets/ucsd-physics-research-site-david-kleinfeld.json#/latestDestinationFetch`。
- Packet SHA `e1a4f82842e17e0161e12629de460f8bcb922a9985fa7617e04f683afb88fd2a`；record SHA `811f9059bc10263537f3fef1260488f1459baf13ce455e76e8719d33ce88b726`。

## 审计证明与限制

- Inventory SHA `c27b6f1d7953813c9e5a2b9fb78032000c5ff0a52a6ecfb041f3413a054d51d4`。
- 原 baseline SHA `ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e`。
- JSON 保存全部输入快照 SHA、逐 ID baseline literal 字段、原 fetch/robots 错误及时间、匹配缓存 sourceId/正文 SHA、raw 状态与 blocker、投影限制、具体条件和唯一 URI 清单。当前活动 queue 仅是读取时快照，后续变化不影响这里的历史记录。
- 对 9 条成功相关 HTTPS 捕获，严格 source request/body/time/final tuple 和缓存字节 SHA 已验证；其余 Sung 无目的页来源、两条404不伪造正文来源。
- 本组当前元数据未见 DNS/cap 错误或明确 robots_denied/authentication_required/access_challenge；这不保证未来原 HTTP 结果可读。Sung 已有真实 TLS/robots 阻塞，其既有记录和重试预算继续生效。
- route-only planner 可以据此列候选，但必须保留所有正常准入/拒绝逻辑；本报告不直接执行任何网络操作。
