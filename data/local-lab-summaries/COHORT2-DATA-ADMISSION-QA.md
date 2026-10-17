# Cohort2 data-admission independent QA

独立审阅：2026-10-16T07:05:46+00:00；基准`920f81f085ea8cf6d01e19fbb4eb3557c4550df5`。**三条数据准入合同PASS，无待修问题。此结论不是实际HTTP观察、robots许可、页面身份或科研接受。** 本QA 0网络，未调用会写文件的plan，未修改production/active entries/raw/packet/collector/shared；只写本报告及JSON。

active现6项，SHA `60f8917c3216e47c6441c5ee945d926c8a46138f89745d9f436964d387daf140`；旧前三完整typed objects与基准相同，后三精确等于PROFILE-LINK-COHORT2-DRAFT.json（SHA `a55c5350efe1339edb3aa493bea3f6b981d42b71e9d684700b76217ed73c2b67`）。未通过其它合同扩展URL。

| ordinal / stable ID | 历史official profile / 原observedAt | actual literal HTTP href | 完整verified labWebsiteUrl proof SHA |
|---|---|---|---|
|150 / ucsd-cellular-molecular-medicine-lab-esko-lab|[Jeffrey Esko](https://profiles.ucsd.edu/jeffrey.esko) / 2026-10-07T21:45:57+00:00|`http://eskolab.ucsd.edu/`，Esko Lab|`352f53fb19ad3e167f9df1f71ebed70b50fe66ce579065a7b124292e81c505c9`|
|520 / ucsd-live-lab-ebefe055ae9fce|[Dan Kaufman](https://profiles.ucsd.edu/dan.kaufman) / 2026-10-07T21:44:17+00:00|`http://kaufmanlab.ucsd.edu`，Kaufman Lab Site|`b3bf34b68eb3106d17582b756a265542e1d1e39e3c3f3e444b593c2444f1f91c`|
|625 / ucsd-live-lab-eb8a5809f8da0f|[Pradipta Ghosh](https://profiles.ucsd.edu/pradipta.ghosh) / 2026-10-07T22:11:28+00:00|`http://ghoshlab.ucsd.edu/Pages/default.aspx`，Ghosh Lab|`be25bc6f776089269ce353dc666e146186b5ad1adfaaf2d0b9076c7dfa59418d`|

三份own immutable HTML与original sidecar逐字节等于原profile缓存；实际body/metadata SHA、source/final URL、capture observedAt与同日baseline完整verified fieldproof均匹配。选用professorId均在该lab冻结professorIds内且officialProfileUrl精确相符。实际DOM锚点在ctl00_divProfilesContentMain的FeaturedContent/webpage层，label/href精确匹配，不取script/comment/template或个人科研段。三份body SHA分别为：

- Esko `0da0ed727c6709cf595af64828ae43bb3eca97d613727f50e5be07b1852c9833`
- Kaufman `c849db11030f9478cfa79f06ec7edec64229862e38102f2c2a1e355aa71e6a78`
- Ghosh `039993a71478a4184622c817944caa672db948e0a4b90d1bd36ee538470f7cc3`

各metadata SHA与逐字段检查保存在JSON。没有借同URL其它日期的capture，不改source时间，不以复制/审阅时间代表当前任职、隶属、运营或研究更新。

**Kaufman原href确实没有末尾斜线，active.url和literalAnchor.href保留该字面值。** 既有safe_url对空根path预期序列化为`http://kaufmanlab.ucsd.edu/`，request_key视空根与/等价；这是请求URI的根路径编码，尚未发生请求，更不是HTTP redirect。原listedWebsite仍`https://kaufmanlab.ucsd.edu/`；不能据此补写301/302、canonical迁移或原HTTPS已查。未来真实receipt须分别保留literal admission URL和实际wire URL。

三条raw及packet整字节与基准相同，hash等于entry冻结值；完整latestDestinationFetch typed相等，preparedAt/listed URL/旧sources均未动。原HTTPS robots_unavailable及01:19:39/41/43原观测保持，三原根pageIdentity仍uncertain、verified=false。三目标均不在14个mismatch门禁内；全部14决策hash仍`d03f63cfc224974df2951ebbc152619fc05289431dbcb69781c888df5874362a`，接受数0。当前未见三literal HTTP target尝试、own once记录、HTTP-origin robots unavailable或明确拒绝；这些是07:04:38检查时的记录事实，不是未来许可保证。

仅调用read-only `reviewed_historical_profile_links(captures)`：使用07:03:04完整queue快照中所有可能影响新三host的captured fetch/history投影（3条）及全部own receipts；原三已观察cohort由既有journal/状态关闭。结果恰为Esko/Kaufman/Ghosh三项，kind=reviewed_profile_lab_link_gap、notAnOriginalListedURLCheck=true、maxPageBytes=2,000,000。helper调用前后3raw/packet、active及ledger字节不变。own ledger保持353 wires/205 receipts，SHA `61f839b5b9ab88dde85345c415714e86c62cbcd60519e23d861d4e1ca7c3655b`；本次没有新增wire或start。

正常执行仍须parent逐项使用既有共享v2门、正常HTTP robots、HTTPS redirect TLS验证和2M/300K上限，遇拒绝/挑战/不可用即停止；不得通过本数据QA放大cap、关闭TLS或重开已尝试URI。

## Frozen remaining-source delta

固定queue：updatedAt2026-10-16T07:03:04+00:00，读取07:03:11；SHA `940449ba05aeab00f638f10a279834031dfcbba0baa926eaf1dfbaa29f8afb92`，43,999,807字节、19,241项。没有持续轮询queue。

覆盖NEW-CACHE-DELTA-AFTER-LEGACY-SCOPE.json的原441 tuples/148 IDs，排除已supported的Carlin/Alex后全部146个当前partial/unresolved IDs，并加入RELATED-URI-REMAINING-GAP-REVIEW-0620.json各target knownURLBindings与当前packet实际root/related/followup/source URL。包括98个没有合格official-profile字段的IDs；未仅凭profile coverage做缩小抽样。597个内容查找key对应438个保留的关联tuple，**438/438 exact request/final URL、observedAt、body SHA、status/HTTP状态相同**，0新增/变化tuple、0新增target binding、0可复用新正文；旧tuple遗漏0。内容lookup折叠scheme/www/尾slash只为发现关系，不据此证明实际请求等价、redirect或canonical。

因此没有重读旧相同正文/title或重新进行科研总结。全部146 ID及冻结记录集semantic hash与覆盖inventory hash见JSON；当前snapshot之后的collector变化不在本报告内。

## Existing test receipt

PROFILE-LINK-ACTUAL-FULL-TEST-RUN.json SHA `df62a6dc11a38e4100ceeec56a1b5137c32d6f2edd5be19508ad3574de0b1ea9`：409 PASS，06:42:42完成；44份tested source SHA及log hash当前全部匹配。adapter `76d7631f8235c540023841c0cdb41c9d59e0c2c83892f3a261de8406dc1e6bbf`，独立测试`09961c30ebe701640877bb842b35438ab00c507ce6c062fb7b90d681f857773a`未改。本次复用凭据，没有重跑测试，也没有将数据准入或fake-transport测试说成这三条已发生的真实transport证明。
