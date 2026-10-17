# Remaining question-field application plan QA

Reviewed at 2026-10-16T08:55:00+00:00. **PASS — pre-apply only.**

Plan SHA-256: `58d1eed9436f742a0a37c6a3cba0592c2869b6287cecc803c0d23345ae5ee2cf`.
Helper SHA-256: `097076be5f33eeaa24136d0412d76f2a100e73e8a6e5a3424dbd1edcbce6e10d`.

The434-record immutable plan exactly covers the405 new-inventory items plus29 prior rechecks, with no duplicates or omissions.194 records add273 source-explicit questions;240 keep questions empty and append a bounded reason. The16 component hashes, all884 before-raw hashes and all884 packet hashes match current files. The450 non-target raw records remain outside the write set.

An independent reconstruction of the effective drafts and all addenda matches every planned question, proof, reason, actual review time, source coverage entry and review-component hash. Mesirov96 explicitly asks for cancer molecular markers; Lewis154/261 use the same existing primary source in separate packets;160/161/213 and306/309/380 incorporate their agreed translation/history/model constraints. The two prior29 report files cover0..8 and9..28 separately and exactly.

Only four fields change for the194 positive rows: researchQuestions, appended evidence, questionFieldReview, reviewedAt. Only uncertainty, questionFieldReview and reviewedAt change for the240 empty rows. Old evidence and uncertainty remain exact prefixes. Previous record review times are preserved in questionFieldReview.previousRecordReviewedAt. Identity, affiliation, PI boundaries, URL metadata, status, summary, methods, topics and blockers remain unchanged.

All273 proof excerpts are literal current-packet primary text with exact original source times and body hashes.192 distinct proof sources:181 actual cached HTML byte hashes independently match;11 historical sources retain their unknown body hashes and original dates.15 derived summary.observedAt sets gain existing cited-source dates; no capture is retimed or newly observed. All434 old/new hydrated URL semantic fields and all other scientific fields compare equal.

## Helper and recovery

The exact helper checks this gate’s passed flag plus plan/helper/component SHA pins,884 packet hashes and450 unaffected raw hashes. Each target record must have its planned old or new hash. Atomic writes use a same-directory temporary file, flush/fsync and os.replace; journal checkpointing follows the record write. A record already written before journal persistence is recovered by its planned new hash, while unexpected third hashes stop application. This is434 per-record atomic checkpoints, not a global transaction.

Nine exact-helper pure-memory scenarios passed: normal434 apply; RuntimeError and KeyboardInterrupt after a record before journal; RuntimeError after journal; stale target record, component, helper, packet and unaffected-record guards. No physical helper apply/journal write occurred. Independent560 helper QA also passes six memory scenarios, bound in JSON.

## Limits

- 本轮在已钉住的逐段独立语义QA基础上审应用组合、有效patch及全部字段不变量；没有冒称重新读完434条全部来源正文。midrange135条与prior29后20条此前为本审阅者逐项语义研究，Mesirov目标本轮再次完整读主文。
- 11个历史question proof原bodySha256=null，保留真实10/02或10/07日期，不伪造原HTML核验；其余181个独立question source的实际缓存字节hash均匹配，合计192个独立来源。
- 15条summary.observedAt引用日期集合因新增引用已存在的真实source而扩展；这是证据日期集合，非重写原捕获时间或产生新capture。packet/原根检查日期和原URL均冻结。
- 纯内存恢复模拟没有调用生产m.atomic、没有真实record/journal写入；只对exact helper apply控制流及guard作故障注入。此helper不在430生产suite内，独立模拟9项均通过，另560独立6项均通过。

No blocking findings.0 network/PS requests and0 raw, packet, plan, journal, code, collector or shared-state writes by this review. Parent owns application and final projection validation.
