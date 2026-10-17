# 原HTTPS根身份绑定：8项planned patch

未应用。以基点 `19be64a` 的完整oldRecord/oldSHA为审阅基准；JSON同时给出newRecordPreview及独立append操作spec，**禁止用preview覆盖当前raw**。仅追加已审旧root的精确identity引文，并记录实际reviewedAt和rootIdentityBindingReview；status、entity identity、affiliation、所有科学字段及packet/root metadata不改。

8个preview经pure hydrate均canCount=true；这是内存反事实检查，当前验证计数未变化。

| ordinal | labId | sourceId / 原观察时间 | identity位置 |
|---:|---|---|---|
| 496 | ucsd-live-lab-f3a5edc06ada6b | `src-c4ba244c6440b828` / 2026-10-16T01:06:31+00:00 | title |
| 466 | ucsd-live-lab-c8c17d1c3b0cd2 | `src-8d8c600e7abe1be8` / 2026-10-16T01:00:13+00:00 | title |
| 828 | ucsd-structural-engineering-lab-armor-lab-active-responsive-multifunctional-and-ordered-materials-research | `src-97b310b478bf8a4d` / 2026-10-16T01:00:50+00:00 | title |
| 181 | ucsd-communication-lab-macro-lab | `src-2b4ad061e661bf3c` / 2026-10-16T00:59:39+00:00 | title |
| 442 | ucsd-live-lab-d926518929ccab | `src-0cc9bbd11053e1c5` / 2026-10-16T01:00:06+00:00 | body |
| 502 | ucsd-live-lab-ce0b313a22d83d | `src-254ea865b6464cde` / 2026-10-16T01:00:27+00:00 | title |
| 614 | ucsd-live-lab-0958eb5e1d52b6 | `src-223296c9545f4eae` / 2026-10-16T01:01:20+00:00 | title |
| 490 | ucsd-live-lab-3fb493ff6136bb | `src-e9e0fdc0ea4aa75a` / 2026-10-16T01:00:18+00:00 | title |

每项rootIdentityBindingReview保存previousRecordReviewedAt、原source实际时间/请求/final URI、root bodySHA及完整root metadata hash。源时间与sourceId不可改为本次review时间。原HTTP相关观察的initial URI、真实redirect/time独立保留，不换成HTTPS，不改canonical。

Süel/Frazer等可能先由问题字段批次更新：实施时读最新raw，先核对授权question-application journal的预期newRecord，再仅append身份证据；previousRecordReviewedAt动态保存实施前当前值。若SHA变化无法由该已审应用journal解释，应停止并fresh review；不得复写旧questions/evidence/history。既有rootIdentityBindingReview如存在也先留history。source/packet/root immutable tuple仍须逐字匹配本计划。

本计划只保存可审操作，不执行raw/packet/production更改，0网络/PS；应用后的逐条hydrate和全量validate由父代理负责。

计划审阅时间：2026-10-16T07:53:22+00:00。
