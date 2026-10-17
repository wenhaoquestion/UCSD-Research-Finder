# 8项原根身份绑定：应用后独立 QA

PASS，无需修复的问题。已独立核对实际8份raw与application journal的newRecord/newSHA完全一致；journal旧记录及oldSHA与基点 `190c445` 相符。

- 8条仅改变evidence、reviewedAt、rootIdentityBindingReview。每条旧evidence是精确完整前缀，仅append1条identity quote；summary/questions/topics/methods、status、identity、affiliation、uncertainty/blockers均与应用前相同。
- Süel与Frazer此前新补questions及其证据全部保留，previousRecordReviewedAt保存了问题字段审阅后的原值。
- 8个quote逐字匹配实际旧HTTPS根的title（7）或具名body（Acevedo）；原cache bodySHA、metadata sidecar SHA、actual request/final URI及原observedAt均匹配。新绑定review时间没有覆盖capture时间。
- 各root的actual source、lastCheckedAt、canonical、redirect、robots及其他历史/related/followup字段均与基点URL行相同。iPower3Es原HTTPS→eng跳转链未换成新HTTP链；未改任何initialHTTP观察。
- 对PREAPPLY不变量：其余876份raw、全部884份packet逐字SHA相同。ledger完整字节仍358events/210receipts；14decision与2registry全不变，mismatch接受0。
- 独立重新hydrate全部884份raw/packet：884摘要行及884URL行类型敏感对象完全等于当前投影。仅这8条canCount从false变true，569→577；876其他URL行与基点相同。manifest sourceCount全匹配。
- 当前validation PASS、errors/warnings为空，父验证检查1061个evidence cache files；738supported/56partial/90unresolved、724lab/group科学支持。outputsAreComplete仍false。
- 现有430-test receipt的46个当前源码/测试SHA及完整日志SHA复算匹配；没有重跑测试。此次增加是既有capture的身份proof绑定，不是新页面请求或科学/网址迁移。

| 最终绑定 | SHA256 |
|---|---|
| application journal | `a7d683d48b4a972abbb3ecf7e025b0857bdcb49458c32a36ea4b7cdcc96a7edf` |
| preapply invariants | `36379901912350c0065f1ee12bf0e923ce615ccc0be088d781af67e52e63eee3` |
| validation | `66808d1a5728171c227c7ead2d0eb528211a48a60e04f8b2509d5cd5f924a1f8` |
| manifest | `0643a2c285eb8055255c51b61a1487e5369c5fe80264f7617ff005917a5a5553` |
| checkpoint | `61b7f8a37c11da0bd9ee6c7e942cfaab27f722a57ff16a51239fc79be520019a` |
| summary projection | `e782b1ff9bf1b7a35fd771dfe562e95c50f5e7919f911644898ce61d4758d1ad` |
| URL projection | `b1510bd71608b50f329ee2061da6a8411de0d8c75ebe2e7cb4e506ef320bffe1` |
| ledger | `73d2573f544bbcbb78da464ef388f7d0f11f40b74989788726b683f4112a36a5` |

完整8项旧/新hash、精确引文、binding review、原source时间/hash/URL与46源码map见同名JSON。仅写此报告pair；0网络、0PS、0raw/packet/production/collector/shared写入，未重复科学正文审阅。

独立核验时间：2026-10-16T08:03:19+00:00；报告保存时间：2026-10-16T08:04:02+00:00。
