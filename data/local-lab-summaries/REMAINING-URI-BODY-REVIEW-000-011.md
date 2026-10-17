# 剩余原HTTP正文审阅：索引000–011

实际审阅：2026-10-16T05:00:35+00:00。**只写建议；0网络请求；raw/packet/receipt修改0。**

12条：8个新200正文缓存（其中4个为空meta壳），2个robots前置阻塞、2个404。实际读取/重提取8个新body，7个与旧根完整可见文本相同；Hampton出现新的具名whole-lab正文。

目的页身份建议：confirmed4（Bennett、Goldrath、Hampton、Yanofsky），uncertain8，mismatch0。Bennett仅title；Yanofsky仅既有title身份且继续partial/frames障碍；Murre继续uncertain。若父代理按身份建议追加引文，hypothetical hydrate可恢复accepted lab/group原URL3条；本报告实际应用0条。

## 逐条建议

### 000 · ucsd-lab-from-faculty-sung-lab-eng-ucsd-edu

- `robots_unavailable`；sourceId `None`；目的页身份 **uncertain**；决定 `keep_actual_robots_blocker`。
- 原literal <http://sung-lab.eng.ucsd.edu/>；实际meta URI <http://sung-lab.eng.ucsd.edu/>；actualPageRequestMade `False`。
- observedAt `2026-10-16T04:56:09+00:00`；liveCheckedAt `None`；final `None`；body SHA `None`。
- sameFullVisibleText `None`；正文字符 `None`；空正文 `False`。
- 原 HTTP 仅完成 robots 前置检查，robots 从 HTTP 跳 HTTPS 后出现 curl35 TLS 错误；没有页面请求、页面正文、sourceId 或正文hash。保留既有官方研究证据，不补本次目的页身份。
- 本次没有可建议追加的充分身份quote；失败/空壳不借用旧source引用日期或外站正文。
- 旧raw `supported`、科学reviewedAt `2026-10-16T01:45:38+00:00`及全部旧证据/不确定性原样保留。
- 本条模型审阅 `2026-10-16T05:00:35+00:00`；packet SHA `c2e05b2c3d77d9532ca55fdeb40cc6e60a483672563d102657346005e2bc7a10`；raw SHA `0cb8e21d465b7cecf28a99fd048165b3ae6af959291e06e2e89f08818a6e40a5`。

### 001 · ucsd-biology-topic-lab-bennett-lab

- `ok`；sourceId `src-cebe2dbe044b27a0`；目的页身份 **confirmed**；决定 `recommend_identity_title_binding_only`。
- 原literal <http://labs.biology.ucsd.edu/bennett>；实际meta URI <http://labs.biology.ucsd.edu/bennett>；actualPageRequestMade `True`。
- observedAt `2026-10-16T04:56:11+00:00`；liveCheckedAt `2026-10-16T04:56:10+00:00`；final `http://labs.biology.ucsd.edu/bennett/`；body SHA `ddcae5a4c30a5849a59532c949cbcdabdd1dbb58bd846178abaea4e35ecd2c1b`。
- sameFullVisibleText `True`；正文字符 `0`；空正文 `True`。
- 新根是meta refresh壳页，正文为空，无新研究；literal title直接具名，且同旧根整页字节/文本，既有meta目标已独立核实具名实验室。仅可将本次源的title支持identity；meta属性不是HTTP重定向，也不采纳新规范URL。
- 建议exact身份引文：`src-cebe2dbe044b27a0` / `title`：“Bennett Lab”；supports仅identity。
- 旧raw `supported`、科学reviewedAt `2026-10-16T03:23:19+00:00`及全部旧证据/不确定性原样保留。
- 本条模型审阅 `2026-10-16T05:00:35+00:00`；packet SHA `d4aad98426844aaaa93cbfff0d0c2641141e0a39a12867eeee4ab6f9aa3fbe74`；raw SHA `fa93e9d259830ee980d5067405163144563db60e90985259d79ff6c4519bc774`。

### 002 · ucsd-biology-topic-lab-bier

- `ok`；sourceId `src-c5baf2d450d79f22`；目的页身份 **uncertain**；决定 `keep_meta_only_root_blocker`。
- 原literal <http://bierlab.ucsd.edu>；实际meta URI <http://bierlab.ucsd.edu/>；actualPageRequestMade `True`。
- observedAt `2026-10-16T04:56:13+00:00`；liveCheckedAt `2026-10-16T04:56:13+00:00`；final `http://bierlab.ucsd.edu/`；body SHA `9a971c153ad99cc72353cd30b03dbcd398bf6b705f9784c769e70ded6425c8a1`。
- sameFullVisibleText `True`；正文字符 `0`；空正文 `True`。
- 新根无title、headings或正文，只有指向bierlab.weebly.com的HTML meta。旧独立目标的科研/身份继续支持实体，但不能冒充此次原根的具名正文引证。
- 本次没有可建议追加的充分身份quote；失败/空壳不借用旧source引用日期或外站正文。
- 旧raw `supported`、科学reviewedAt `2026-10-16T03:23:19+00:00`及全部旧证据/不确定性原样保留。
- 本条模型审阅 `2026-10-16T05:00:35+00:00`；packet SHA `7dd73f342981641459a1c6ddbd4f482794ebed303d211233e288522499b7ae79`；raw SHA `ae4c8d8b147c854ea493ec1784d2f34e4b10cc37c85b9c5762ae10d2f2e74a6d`。

### 003 · ucsd-biology-topic-lab-firtel

- `robots_unavailable`；sourceId `None`；目的页身份 **uncertain**；决定 `keep_actual_robots_blocker`。
- 原literal <http://people.biology.ucsd.edu/firtel>；实际meta URI <http://people.biology.ucsd.edu/firtel>；actualPageRequestMade `False`。
- observedAt `2026-10-16T04:56:14+00:00`；liveCheckedAt `None`；final `None`；body SHA `None`。
- sameFullVisibleText `None`；正文字符 `None`；空正文 `False`。
- 原HTTP robots返回301，但目标不满足现有robots文件规则，error=robots_redirect_is_not_a_robots_file；没有页面请求。不能把旧HTTPS Lab Members页或faculty科研材料转记为此次目的页身份。
- 本次没有可建议追加的充分身份quote；失败/空壳不借用旧source引用日期或外站正文。
- 旧raw `supported`、科学reviewedAt `2026-10-16T01:47:04+00:00`及全部旧证据/不确定性原样保留。
- 本条模型审阅 `2026-10-16T05:00:35+00:00`；packet SHA `34d79f946ad51651f282145bfb0fbca7b4c5876f0e1c8e6ffe3db5afbb8dd347`；raw SHA `3e482a3d5577cb942e99d27576eae4630fd44ef805eab598243dd151750e03fa`。

### 004 · ucsd-biology-topic-lab-goldrath

- `ok`；sourceId `src-6cf67ff1ffd79d15`；目的页身份 **confirmed**；决定 `recommend_identity_title_binding_only`。
- 原literal <http://biology.ucsd.edu/labs/goldrath>；实际meta URI <http://biology.ucsd.edu/labs/goldrath>；actualPageRequestMade `True`。
- observedAt `2026-10-16T04:56:17+00:00`；liveCheckedAt `2026-10-16T04:56:14+00:00`；final `https://goldrathlab.com/`；body SHA `7414a2497b82e92f26d7fe2289596a32e5402eb60ce43faad80ed0c941140e46`。
- sameFullVisibleText `True`；正文字符 `1219`；空正文 `False`。
- 新目的页与已审旧根同字节、同完整可见正文。title明确Goldrath Lab，正文Our research与旧科研完全一致；只建议追加本次源的title身份引文，原科研字段/方法未知/科学reviewedAt保持。
- 建议exact身份引文：`src-6cf67ff1ffd79d15` / `title`：“The Goldrath Lab, UCSD”；supports仅identity。
- 旧raw `supported`、科学reviewedAt `2026-10-16T01:47:04+00:00`及全部旧证据/不确定性原样保留。
- 本条模型审阅 `2026-10-16T05:00:35+00:00`；packet SHA `43a8b5d8aae69c394393bcaaf90d2c11e89a223433e745b732eef764b8060220`；raw SHA `860014e284947c14a6b83a260b823cbf9a0cab747fea9c37a73ab49d5f23cdb4`。

### 005 · ucsd-biology-topic-lab-hampton

- `ok`；sourceId `src-079b069f7c694d83`；目的页身份 **confirmed**；决定 `recommend_explicit_new_lab_science_revision`。
- 原literal <http://hamptonlab.ucsd.edu>；实际meta URI <http://hamptonlab.ucsd.edu/>；actualPageRequestMade `True`。
- observedAt `2026-10-16T04:56:18+00:00`；liveCheckedAt `2026-10-16T04:56:18+00:00`；final `http://hamptonlab.ucsd.edu/`；body SHA `33cc226c71a0d2ef77d4f07910a7c1b72e6e81d14e3bff5c2f4af16323345342`。
- sameFullVisibleText `False`；正文字符 `581`；空正文 `False`。
- 原HTTP取得真正Hampton实验室正文，区别旧HTTPS Gadsby占位页。正文直接陈述实验室研究、酿酒酵母模型和UCSD Biology位置；可补具名whole-lab科研/方法与来源报告隶属。新观察不证明正文计划更新日期。
- 建议exact身份引文：`src-079b069f7c694d83` / `body`：“Welcome to the Hampton lab webpage!”；supports仅identity。
- 旧raw `supported`、科学reviewedAt `2026-10-16T01:47:04+00:00`及全部旧证据/不确定性原样保留。
- 本条模型审阅 `2026-10-16T05:00:35+00:00`；packet SHA `44334a7bcc5a5ac3a38a638f6edbe44d6de5e4f9eed44d3d5664d7cabe51cd3c`；raw SHA `416fde01d5e662acabfaeca998913d6d45a41dceffdd653cf0988668d461166e`。

**Hampton完整科学补充建议（未应用）：**

Hampton 研究组研究细胞如何选择性降解蛋白质，包括 HMGCoA 还原酶（HMGR）的受调控降解和内质网蛋白降解，并以酿酒酵母（出芽酵母）为模型。既有官方介绍还将研究与胆固醇合成调节、错误折叠蛋白处理、脂质信号及细胞器动态相联系。

- questions：保持空列表；topics新增 ['HMGR 的受调控降解', '内质网蛋白降解']。
- methods：['酿酒酵母（出芽酵母）模型']，仅明确模型，不推断未提技术。
- affiliation建议source_reported：新body字面说明UCSD Biology位置；现时生效日期仍不确认。
- 原科学reviewedAt `2026-10-16T01:47:04+00:00`保存在历史；若应用实质补充，新的科学审阅时间为 `2026-10-16T05:00:35+00:00`。旧Gadsby/未列方法限制作为被更新的历史记录保存。

- `src-079b069f7c694d83` / `body`：“Welcome to the Hampton lab webpage!” → identity。
- `src-079b069f7c694d83` / `body`：“We are located in the Biology department at the University of California, San Diego.” → affiliation。
- `src-079b069f7c694d83` / `body`：“Our research interests lie in the regulated degradation of HMGCoA-reductase (HMGR) and in ER protein degradation in general.” → research, topics。
- `src-079b069f7c694d83` / `body`：“Our model organism is Saccharomyces cerevisiae , or budding yeast.” → methods。
- `src-61468db9b28284b9` / `body`：“This work started with understanding how these sorts of mechanisms are employed to allow regulation of cellular cholesterol synthesis.” → research, topics。

### 006 · ucsd-biology-topic-lab-kiger

- `ok`；sourceId `src-76abe8c329b73470`；目的页身份 **uncertain**；决定 `keep_meta_only_root_blocker`。
- 原literal <http://www.biology.ucsd.edu/labs/kiger>；实际meta URI <http://www.biology.ucsd.edu/labs/kiger>；actualPageRequestMade `True`。
- observedAt `2026-10-16T04:56:21+00:00`；liveCheckedAt `2026-10-16T04:56:19+00:00`；final `http://labs.biology.ucsd.edu/kiger/`；body SHA `492e32ddcc79db4d57b8f99e5563fd8bc747379b24a1189a7c10ee5a0842cd0d`。
- sameFullVisibleText `True`；正文字符 `0`；空正文 `True`。
- 新根无title、headings或正文，仅有同站Amy_Kiger_Lab_at_UCSD/Home.html的meta。相对URL现在以实际HTTP final为基址，不能改标为已请求该HTTP目标；旧已请求HTTPS目标不替代本次根身份。
- 本次没有可建议追加的充分身份quote；失败/空壳不借用旧source引用日期或外站正文。
- 旧raw `supported`、科学reviewedAt `2026-10-16T03:23:19+00:00`及全部旧证据/不确定性原样保留。
- 本条模型审阅 `2026-10-16T05:00:35+00:00`；packet SHA `c05fa98af9f43519174cce31b77c5e98f09124f18153d2a42894175ebe170dec`；raw SHA `0ab55c17af5466d3eb840d9bdc22aa33f687659118e71eb532eebbb9b89c66d1`。

### 007 · ucsd-biology-topic-lab-murre

- `ok`；sourceId `src-1e9370a1c7cac8eb`；目的页身份 **uncertain**；决定 `keep_insufficient_entity_relation`。
- 原literal <http://labs.biology.ucsd.edu/murre>；实际meta URI <http://labs.biology.ucsd.edu/murre>；actualPageRequestMade `True`。
- observedAt `2026-10-16T04:56:23+00:00`；liveCheckedAt `2026-10-16T04:56:22+00:00`；final `http://labs.biology.ucsd.edu/murre/`；body SHA `45e2f5ca841118cc40a4646a5bc45b8a1622cbae80a6abb9a3b48ea005ecfee5`。
- sameFullVisibleText `True`；正文字符 `31`；空正文 `False`。
- literal title虽含murre lab，正文仍只有Arthur He更新时间，没有明确PI/团队/研究说明，也无可核实的实体关联链。仅记录有限名称线索，维持本条实体未确认及无科研正文；不靠200或姓氏title接受。
- 有限观察（不作新科研）：`title`：“Welcome to murre lab!”；limited_name_only_not_a_sufficient_identity_binding。
- 有限观察（不作新科研）：`body`：“updated 8th Apr, 2020 Arthur He”；update_attribution_not_lab_research_or_affiliation。
- 本次没有可建议追加的充分身份quote；失败/空壳不借用旧source引用日期或外站正文。
- 旧raw `unresolved`、科学reviewedAt `2026-10-16T01:48:34+00:00`及全部旧证据/不确定性原样保留。
- 本条模型审阅 `2026-10-16T05:00:35+00:00`；packet SHA `37e4c14ebef80c1cb2f178352b5d7976bd92570d9734cc43264abbca7081a49f`；raw SHA `c8e90867d5694a324430ccff6d8e2e226b0f394103f098b5f5729aa9b1c19c43`。

### 008 · ucsd-biology-topic-lab-spitzer

- `ok`；sourceId `src-e0224176cdecd4ab`；目的页身份 **uncertain**；决定 `keep_meta_only_root_blocker`。
- 原literal <http://www.biology.ucsd.edu/labs/spitzer>；实际meta URI <http://www.biology.ucsd.edu/labs/spitzer>；actualPageRequestMade `True`。
- observedAt `2026-10-16T04:56:26+00:00`；liveCheckedAt `2026-10-16T04:56:24+00:00`；final `http://labs.biology.ucsd.edu/spitzer/`；body SHA `d2bf0b44a3e77666df4f903c873468e9c93bff09f5ffc7bd0250d6f5480894ff`。
- sameFullVisibleText `True`；正文字符 `0`；空正文 `True`。
- 新根无title、headings或正文，只有nickspitzerlab.org的meta。旧独立跟进页研究仍有效，但不能把HTML meta当作本次根HTTP redirect或目的页身份quote。
- 本次没有可建议追加的充分身份quote；失败/空壳不借用旧source引用日期或外站正文。
- 旧raw `supported`、科学reviewedAt `2026-10-16T03:23:19+00:00`及全部旧证据/不确定性原样保留。
- 本条模型审阅 `2026-10-16T05:00:35+00:00`；packet SHA `8f2317ff3931b6ba503e7e8bfa0ba350e601e02472996f208058139ed3c1b920`；raw SHA `ccd2f4e6579a6cbfcec36e9bbf099929edfa54279844fb6895435cb37d26ad9f`。

### 009 · ucsd-biology-topic-lab-subramani

- `http_error`；sourceId `None`；目的页身份 **uncertain**；决定 `keep_actual_404_blocker`。
- 原literal <http://www.biology.ucsd.edu/labs/subramani>；实际meta URI <http://www.biology.ucsd.edu/labs/subramani>；actualPageRequestMade `True`。
- observedAt `2026-10-16T04:56:27+00:00`；liveCheckedAt `2026-10-16T04:56:26+00:00`；final `http://labs.biology.ucsd.edu/subramani`；body SHA `None`。
- sameFullVisibleText `None`；正文字符 `None`；空正文 `False`。
- 本次实际原HTTP请求经已记录链到目标返回404；没有可归属的新正文source/hash。保留unresolved，不推断实验室关闭、不从URL或他人方向补研究。
- 本次没有可建议追加的充分身份quote；失败/空壳不借用旧source引用日期或外站正文。
- 旧raw `unresolved`、科学reviewedAt `2026-10-16T01:49:16+00:00`及全部旧证据/不确定性原样保留。
- 本条模型审阅 `2026-10-16T05:00:35+00:00`；packet SHA `8a0ff9d37666b3f273fa0a51007a95d56e3250db98e591b44897101de55943dc`；raw SHA `593061fbef3cef37b5c4f0229f93cdf677640e46cb77ec82daad18462672ec04`。

### 010 · ucsd-biology-topic-lab-yanofsky

- `ok`；sourceId `src-89f0f296045c7f5f`；目的页身份 **confirmed**；决定 `recommend_limited_existing_identity_binding_keep_partial`。
- 原literal <http://labs.biology.ucsd.edu/yanofsky/home.html>；实际meta URI <http://labs.biology.ucsd.edu/yanofsky/home.html>；actualPageRequestMade `True`。
- observedAt `2026-10-16T04:56:28+00:00`；liveCheckedAt `2026-10-16T04:56:28+00:00`；final `http://labs.biology.ucsd.edu/yanofsky/home.html`；body SHA `8e8a126cca71a66e423ac6220cbdee79aa4dfab65730d3ccc359ac58f0634912`。
- sameFullVisibleText `True`；正文字符 `106`；空正文 `False`。
- 新捕获与已审frames fallback同字节/全文，title可绑定既有confirmed Yanofsky Lab身份；status仍partial，frames研究缺失障碍保留，不能据title接受科研/verified lab URL或追踪frame子页。
- 建议exact身份引文：`src-89f0f296045c7f5f` / `title`：“Yanofsky Lab - Welcome”；supports仅identity。
- 有限观察（不作新科研）：`body`：“This page uses frames, but your browser doesn't support them.”；research_unavailable_frames_fallback。
- 旧raw `partial`、科学reviewedAt `2026-10-16T01:50:04+00:00`及全部旧证据/不确定性原样保留。
- 本条模型审阅 `2026-10-16T05:00:35+00:00`；packet SHA `182e6512b21cfc8bb5393fdb3bde101b0e522279b77d99bc36f2362085f22018`；raw SHA `ef4778f8272245e964dbfdf32b57f4ccff205a20b688d4c7decd3adf30e58594`。

### 011 · ucsd-physics-research-site-david-kleinfeld

- `http_error`；sourceId `None`；目的页身份 **uncertain**；决定 `keep_actual_404_blocker`。
- 原literal <http://physics.ucsd.edu/neurophysics>；实际meta URI <http://physics.ucsd.edu/neurophysics>；actualPageRequestMade `True`。
- observedAt `2026-10-16T04:56:31+00:00`；liveCheckedAt `2026-10-16T04:56:30+00:00`；final `https://physics.ucsd.edu/neurophysics`；body SHA `None`。
- sameFullVisibleText `None`；正文字符 `None`；空正文 `False`。
- 实际原HTTP已观察到301至HTTPS，再返回404；无新正文source/hash。旧profile加载占位/教师API不能补成lab身份或科研，不删除原unknown边界。
- 本次没有可建议追加的充分身份quote；失败/空壳不借用旧source引用日期或外站正文。
- 旧raw `unresolved`、科学reviewedAt `2026-10-16T01:46:40+00:00`及全部旧证据/不确定性原样保留。
- 本条模型审阅 `2026-10-16T05:00:35+00:00`；packet SHA `8c4055eb2afcb5f15a44b2df0f6d7b5d414e4726b75df5f6ed1bf0968c6bc51a`；raw SHA `811f9059bc10263537f3fef1260488f1459baf13ce455e76e8719d33ce88b726`。

## 审计范围

- JSON记录每个真实source URI/时间/hash/完整比较对象、原HTTP真实redirect链、robots错误、quoteLocation与逐条建议。Sung HTTP robots301→HTTPS TLS35；Firtel HTTP robots301非robots文件；两者没有原页面请求或新body。
- Subramani、Kleinfeld真实404只有元数据，没有新归属正文/source/hash；不推断关闭。
- Bier/Kiger/Spitzer当前meta正文无字面身份quote，既有外站研究仍是各自独立来源，不能搬到本次source。
- Goldrath科学内容/方法未知声明保持；Hampton只使用whole-lab正文和旧官方group研究段，未从publication/navigation/个人经历补科学。
- 没有应用任何建议；13 mismatch门禁、stable ID及listed URL均不改。

最终逐条静态复核：全部quote均位于指定source及body/title/headings位置；JSON另附所有旧/新引用源的原sourceURL、observedAt、hash、role和extraction版本。12条packet/raw SHA仍与审阅时一致。
