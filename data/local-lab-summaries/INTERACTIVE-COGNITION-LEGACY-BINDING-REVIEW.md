# Interactive Cognition legacy binding review

独立审阅：2026-10-16T06:26:05+00:00。仅核验ordinal179（`ucsd-cogsci-interactive-cognition-lab`）的缓存导航、具名实体和历史PI关系，复用511既有同一正文的科研审阅。0请求、0脚本执行；只新增本报告及JSON，未应用数据。

**结论：可以独立支持179为Interactive Cognition Lab并承载已审阅的全实验室研究，仍须保留原根页身份uncertain、原网址verified=false。** 这不要求或授权合并179与511，也不形成alias。

| 步骤 | 已核验的实际证据 | 原始observedAt / SHA-256 |
|---|---|---|
| 根页 | [原根页](https://adrenaline.ucsd.edu/)真实106字节HTML含`<script> location = "/Kirsh/index.html"; </script>`；不是注释。title为Welcome，正文为空。 | 2026-10-16T01:04:54+00:00 / `5242b30e2cd51bb89b846254466123f17f06c3d73ed4923f6a4d154aac63dfce` |
| PI索引 | [David Kirsh索引](https://adrenaline.ucsd.edu/Kirsh/index.html)实际title David Kirsh，真实`href="lab.html"`锚点标签My Lab，解析到下行地址。 | 2026-10-16T01:06:32+00:00 / `4f3584b5a1dd0bf3cd87653fb0a3e0e04360f453651f7312e9a9ec269a3b438a` |
| 具名lab | [My Lab](https://adrenaline.ucsd.edu/Kirsh/lab.html)实际title David Kirsh : My Lab，正文以“Interactive Cognition Lab We do basic research…”明确lab集体作用域。 | 2026-10-16T00:59:42+00:00 / `20b3e6c0d807908b8343c31fd3d27df5e32f709eab5e6ed103412187a20de73b` |

对应sourceId依次为`src-d53ccd72f82f752b`、`src-fb3e73c0cd9cdfb7`、`src-0f9dc0f52a2b63d1`。三者均对照实际缓存HTML、原sidecar及精确queue capture重建：字节SHA、请求/final URI、original observedAt、sourceId、全文及title全部相符，均HTTP200、redirects=[]、无meta-refresh。原robots记录为00:59:41的404 not_found；本次没有新的robots或页面观测。

根script仅作**字面导航发现**，没有执行，也不是HTTP redirect、meta-refresh或canonical。原根page正文为空，不能把script放成raw的body quote或identity证据。实际索引/实验室页是独立完成的既有capture；三个时间不同，不声称按本次导航重新访问。

[官方认知科学实验室目录](https://cogsci.ucsd.edu/research/research-labs.html)的已保存历史字段证据（`src-37ad1b363039a6a9`，2026-10-02T22:42:09+00:00，official_directory_main_content）为“Interactive Cognition Lab Principal Investigator: David Kirsh Website | SSRB 100”。它与上述实际个人索引→My Lab→具名lab链一致。本次核验的是保留字段证据，未声称重新取得目录HTML或当前任职。179自身baseline PI/description原为unverified，fieldEvidence为空，不能以裸baseline字段替代这条链。

科研判断复用[既有03:04:21人工审阅](group-cache-review-parent.json)及[03:09:28独立QA](PARENT-GROUP-CACHE-QA.md)，同一lab正文SHA/全文/title保持精确一致。可沿用其基础研究摘要、问题、主题和三条字面科研引文；不得移入个人索引中的研究兴趣/履历。方法保持`[]`，项目名及增强视频不构成具体实验/计算方法。JSON保留可复用字段及精确quotes供parent审阅，未直接更改179。

隶属只可在实际附上上述官方历史目录证据后有限记为historical source_reported；若未附则保持uncertain。不能把采集日期当作页面更新时间、2026在任PI、持续运营或当前隶属的证明；无页面更新日期。实验室页的interactivity.ucsd.edu外链不在本次范围，未跟随。

应用边界：保留179的stable ID、listedWebsite、root source、latestDestinationFetch、preparedAt及旧raw完整历史；新附索引用reviewed followup角色而不是179的listed destination。保留所有sourceId和原时间、SHA。只用具名lab页/历史目录支持entity identity，根页不加identity quote。实际根final/canonical观察仍只能是`https://adrenaline.ucsd.edu/`，不得换成Kirsh地址或补造redirect。

仅内存的候选hydrate已通过：entity identity confirmed；root pageIdentity uncertain；canCountAsVerifiedLabGroupURL=false；root actualRequestedUrl/final保持原根，redirectChain=[]。未写候选packet/raw。当前14个mismatch决策未涉及179/511，也未改动。剩余实质问题：0；数据应用由parent决定。
