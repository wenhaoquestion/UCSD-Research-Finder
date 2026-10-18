# 摘要工作树恢复记录

本次恢复检查时间：2026-10-17T15:42:23-07:00。

原 `/private/tmp/ucsd-lab-summaries-20261016` 目录确实缺失，持久 Git 注册、索引和提交仍在。按原索引在原路径恢复了 5,815 个已跟踪文件（Git blob 合计 262,357,961 字节），没有 reset、prune 或覆盖后续提交。恢复基础为 `5917f0a7c4b5e3feb0cae13e44baa3fe7053dfe9`；它包含旧 `d5cd11e`，因此恢复的是后续 916 条版本。无法仅凭现存文件确认删除原因和准确时刻。

## 当前能使用的结果

916 条摘要、916 条 URL 记录及对应 raw/packet 均可加载。执行了本次新的离线 schema、ID/顺序、字面引用和现有 hydrate 加载检查：全部与已提交导出一致。恢复后读取到的历史分类是 766 supported、60 partial、90 unresolved；其中 752 个支持的实验室/研究组、600 个历史原网址验证。来源日期、ID、请求/重定向信息和这些历史判断均未改写。

最后已批准 handoff 为 `deb1ef551008b7a9a00f38197d66271241ff608217af3a657b25b9c776ef4b25`，48 条审核新增与 868 条基线构成 916 条记录；其冻结快照和全部引用的决策文件均已恢复并核对哈希。采集工作树的 mutable handoff 当前为 `27418018af775f931c8b747b43cbd9bacc9a79aa7714b5675cb3e33a5e4376bc`，保持原样，没有自动导入或回退。

## 证据与缺失边界

Git 恢复了 1,560 个 HTML 快照文件。现有引用中 223 个原始路径可直接读取且哈希匹配；另有 64 个实验室—来源关联可由已提交的同字节副本解析，映射单独保存在 `RESTORED-EVIDENCE-RESOLUTION-20261017.json`，没有修改旧 cachePath 或采集日期。

仍有 942 个实验室—来源关联无法找到原始正文副本，涉及 846 个原文件引用、823 种不同的正文 SHA256，影响 712 条记录的部分原始证据。对应 packet 文本、引文、URL、原观察时间和预期哈希仍保存在提交中；这不等于原 HTML 全量可重放。最后 handoff 的 93 个正文引用中，62 个有可用字节副本、31 个缺失。

持久主仓库缓存的 712 个 HTML 和其他已提交的 10 个 HTML/ZIP blob 已按缺失的预期 SHA256 做一次有限匹配，没有新增匹配副本。Desktop、Documents、Downloads 的相关文件名搜索未找到独立验收 ZIP 或备份。该搜索不代表检查了系统 Time Machine、外接磁盘或所有其他备份位置。

原 `/tmp/ucsd-final-acceptance-20261017/UCSD-Local-Accepted-Subset-20261017.zip` 未恢复；历史 45,731,712 字节、SHA256 `3cd3c2e3439efbb328d382bec99568eb336906bb0eaddd3d39e6042cab882528` 和 CRC 通过记录仅为消失前收据，本次没有重建该 ZIP 或复验其 CRC。采集器完整原始 responses 缓存仍缺失。未提交、被忽略且没有独立备份的文件不能仅由本次 Git 索引恢复。

## 本次没有重做的工作

没有重采、重发请求、启动采集或网络 worker、绕过 robots，或修改采集工作树/共享调度。旧 PID、lease 和协调收据没有被当作当前活动状态。没有重新运行历史 Python、浏览器或 17,201 个采集正文校验；历史 `validation.json` 及验收收据保留原时间与字节。没有推断任何实验室关闭，也没有 push、合并或部署。

可用结果：[逐条摘要](REVIEW.md)、[摘要 JSONL](summaries.jsonl)、[URL JSONL](url-verification.jsonl)。本次记录：[恢复检查 JSON](TEMP-DIRECTORY-RECOVERY-20261017.json)、[证据副本解析](RESTORED-EVIDENCE-RESOLUTION-20261017.json)、[持久副本匹配记录](PERSISTENT-EVIDENCE-BYTE-RECOVERY-20261017.json)。
