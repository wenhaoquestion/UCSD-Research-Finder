# Cache candidate assessment ledger

账本构建时间：2026-10-16T03:21:06+00:00。本轮仅整理既有报告及当前 packet/raw 引文，没有重新读取来源 HTML，也没有网络请求。

已保存 `cache-candidate-assessment-ledger.json`，原候选清单保持不变。

- 69 个已审 ID、654 个原候选关系（跨 ID 去重为 208 个 URL/原日期/SHA 采集元组）。
- 2 个候选关系与当前 raw 的精确字段引文及 packet 原始采集元组匹配；652 个为 `scope_assessed_not_admitted`，沿用报告的逐 ID 决定，不编造逐来源理由。
- 另列报告明确采用、但不在该 ID 原候选列表中的 13 个来源关系，均与当前精确引文匹配，不并入 654。
- 原候选为空的 138 个 ID：61 个有独立链接发现审计的原根页元组，标记 `discovery_inspected_only`；77 个无当前根页 HTML，明确未作内容研究复核。
- 映射不确定项：0。所有 654 个候选与 69 个报告 ID 唯一对应，无重复语义键。

语义键为 labId + 精确 sourceUrl + 原 observedAt + 原 body SHA-256 + field-evidence 摘要的 SHA-256。字段证据摘要只包含精确 quote、quoteLocation 和排序后的 supports，去重并按规范 JSON 排序。全局队列更新时间、packet 生成时间、账本构建时间、raw reviewedAt 和单纯 sourceId 变化均不参与此键。

实际内容复核时间取自原报告：000–022 使用明示的模型记录复核时间 03:03:28 UTC（报告完成时间 03:05:51 不替代它）；023–045 为 03:01:59 UTC；046–068 为 03:04:01 UTC，均为 2026-10-16。当前引文匹配时间另列，未冒充新的科学内容审阅时间。

未来增量检查应比较原采集元组与字段证据语义键；相同键可跳过相同范围的复读。`discovery_inspected_only` 只说明曾检查实际链接/元跳转，不得当作已审实验室研究正文。三个报告只提供共享的逐 ID 排除决定时，账本通过报告路径、hash 和行号保留原决定，不额外推断单个来源的研究范围。
