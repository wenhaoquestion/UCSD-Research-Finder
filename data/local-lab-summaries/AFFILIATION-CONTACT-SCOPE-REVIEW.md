# 实验室联系地址机构范围复核

原四项范围复核与首次应用QA观察时间：2026-10-16T06:12:10+00:00。追加项及最终应用复核：2026-10-16T06:15:37+00:00。0网络请求；只写本报告对。基准 `5f9a28e3cd523c3bd69e84f8de4e45b13622dff5`。

| 实体 | 原捕获 observedAt（UTC） | 应用的原文机构/位置证据 | 决定 |
|---|---|---|---|
| 709 [Tezcan](http://tezcan.ucsd.edu/index.php/contact-2/) | 2026-10-16T05:36:00+00:00 | Find Us Here University of California, San Diego Department of Chemistry and Biochemistry | `source_reported`，仅机构/位置 |
| 100 [Hao](http://haolab.ucsd.edu/contact.html) | 2026-10-16T05:36:19+00:00 | Lab mailing address The Hao Lab University of California San Diego | `source_reported`，仅机构/位置 |
| 710 [Theodorakis](http://theodorakisgroup.ucsd.edu/page4.html) | 2026-10-16T05:37:00+00:00 | Shipping/Laboratory Location: University of California, San Diego Department of Chemistry | `source_reported`，仅机构/位置 |
| 713 [Yang](http://yanglab.ucsd.edu/page1.html) | 2026-10-16T05:37:13+00:00 | Shipping Address University of California, San Diego Dept. of Chemistry & Biochemistry | `source_reported`，仅机构/位置 |
| 629 [Benner](http://homer.ucsd.edu/BennerLab/) | 2026-10-16T05:33:46+00:00 | The Benner Lab is located at the UCSD School of Medicine, in La Jolla, CA. | `source_reported`，仅机构/位置 |

四个联系页的完整主文分别707、356、704、447字符，均已阅读。Hao明确列The Hao Lab的Lab mailing address；Theodorakis的实验室运输地址与个人办公室分列；Yang具名研究组并有同站Contact锚点。Tezcan实际请求 `http://tezcan.ucsd.edu/?page_id=868`，真实一次301到 `http://tezcan.ucsd.edu/index.php/contact-2/` 后200。四项均与已确认具名实体的同站字面联系锚点对应，不以域名或个人履历独立推断。

Benner为追加第五项，仅独立核查title及 `div#about.about-text > p` 完整实验室介绍语境。句子直接说Benner Lab位于UCSD School of Medicine；51722字符全文只作保存一致性核验，未重读全部科研/论文主体。原HTTPS robots TLS失败保留；HTTP成功以独立related check保存，不证明HTTPS恢复。

追加第六候选（2026-10-16T06:15:37+00:00）：[Burkart成员页](http://burkartlab.ucsd.edu/page2.html)完整8570字符已读。“The Boss Prof. Michael D. Burkart Department of Chemistry and Biochemistry University of California, San Diego Pacific Hall 6100D”把机构/房间附在具名个人The Boss联系块下，未出现wholelab机构或Lab mailing/shipping/location表述。建议保留lab affiliation uncertain，不准入为wholelab机构证据。个人关联可记录，但成员学位、个人研究、former members和年份不能补足实验室层面的机构/专用地址结论。

实际应用QA（2026-10-16T06:15:37+00:00）5/5 PASS，保留原四项复核时间。核验原始HTML/sidecar SHA、queue fetch/attemptHistory、requested/final URI、原始observedAt、sourceId及literal affiliation quote。immutable HTML与原sidecar副本逐字节相同。五条hydrate通过；科学字段、main scientific reviewedAt、旧evidence/source前缀、原根请求与preparedAt均未变。旧affiliation有完整历史；Benner更新的旧uncertainty也完整保留。根投影未提升：Benner和Theodorakis仍未verified，其余三项既有状态不变。

以上仅支持来源报告的机构联系地址/位置，不提供带日期的当前任职、PI、2026运行或地址持续有效保证。本次不扩展科研、方法或全站更新时间。JSON保留各capture元组、body/sidecar SHA、精确引文、fingerprint、应用后raw/packet SHA及逐项检查。
