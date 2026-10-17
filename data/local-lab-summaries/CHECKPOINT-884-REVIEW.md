# 884条本地研究摘要检查点

截至 2026-10-16T05:21:34+00:00，868条基线与16条经独立审阅的增量输入均已处理。科研支持725条、partial61条、unresolved98条；其中711条属于有具名科研支持的实验室/研究组，568条通过原始网址与实体身份核验。其余已审实体类型单列。14项错配接受数为0；159条partial/unresolved均有具体逐条阻碍。

本批核查34个原始HTTP地址：32次页面尝试（27成功、5个404）及2次robots-only，共79次wire请求。后续7个经审阅的正文路径增加9次wire请求。当前总账329次wire/187个捕获回执；所有新请求使用共享v2节流，正常robots、TLS及访问边界。

新增8条基线实验室的充分科研支持，并更新Hampton既有摘要；另分别追加Flow Control和Coordinated Robotics两个共享主页ID。共享通用段落不归入各自研究，PI未知与空professorIds保留。Hermann2019、Kummel2025内容日期明确；SHM通用方法仅为背景，methods为空。Sinha原地址展示Allen Lab，保留错配，未迁移ID或引入Allen科研。

199项本地离线测试通过；完整投影校验通过，检查1036个证据缓存文件，0错误。独立复核见 `REMAINING-URI-BATCH-QA.md`、`FRAME-FOLLOWUP-BODY-REVIEW.md` 和 `SHARED-ENTITY-UNKNOWN-METADATA-RECHECK.md`。原13项错配对象、既有来源/证据及科学历史均保留。

当前经审有限新请求计划余量为0。这不表示全局完成：采集快照 2026-10-16T05:19:29+00:00 的pending=10703、unresolved=712；`outputsAreComplete=false`，正式Goal保持active。后续仅审核新语义增量或具体所需新来源，不因队列时间更新重复采集。全部改动仅在本地工作树，没有推送、合并或发布。
