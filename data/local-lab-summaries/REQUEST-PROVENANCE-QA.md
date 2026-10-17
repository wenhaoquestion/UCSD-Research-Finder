# Request provenance QA

审阅时间：2026-10-16T03:43:16+00:00；保存投影checkpoint时间：2026-10-16T03:40:19+00:00。只读元数据，未读HTML、未重读研究、未运行prepare或测试。

结论：通过；错误0，未发现新的虚假请求来源或计数问题。

## All-row scope and count guard

- 880个唯一ID在manifest、summary及URL projection完整对应；797条评估target URI匹配原listed URL，83条target URI为相关变体；这是此前URI目标分类，未区分页面尝试与访问前置检查，不能解读为页面wire次数。
- 491条verified listed lab/group URL均具备：原地址实际请求匹配、accepted lab/group身份、confirmed当前捕获身份，以及同一实际请求URL/字节hash/原观察时间/HTTP终点的identity证据。83条related-target URI均不得计入verified listed URL。
- 692条lab/group研究支持摘要保持；研究内容是否受支持与原listed URL是否实际检查分开计数。
- 48条原计作verified的related捕获正确退出计数；另6条direct捕获缺所选捕获的identity绑定，保守退出计数，正由另一独立审阅处理。
- 全部checked/requested URL、listed URL、checkScope、canonicalBasis、lastCheckedAt和HTTP redirectChain均与packet所选原始fetch元数据一致；followup的discovery/request差异标记正确。

## Named selection samples

- 84：listed https://komiyamalab.biosci.ucsd.edu；实际选中https://komiyamalab.biosci.ucsd.edu/，原observedAt 2026-10-16T01:04:11+00:00；direct 1、related 2，优先direct。
- 123：listed http://www.elephantresearch.net/index.html；实际选中http://www.elephantresearch.net/index.html，原observedAt 2026-10-16T01:04:43+00:00；direct 1、related 1，优先direct。
- 349：listed https://pediatrics.ucsd.edu/research/faculty-labs/spector-lab/index.html；实际选中https://pediatrics.ucsd.edu/research/faculty-labs/spector-lab/index.html，原observedAt 2026-10-16T01:03:06+00:00；direct 1、related 1，优先direct。
- 467：listed https://isn.ucsd.edu/index.php；实际选中https://isn.ucsd.edu/index.php，原observedAt 2026-10-16T01:03:09+00:00；direct 1、related 1，优先direct。
- 606：listed https://www.ece.ucsd.edu/faculty-research/Ultrafast%20and%20Nanoscale%20Optics%20Group%20(Professor%20Shaya%20Fainman)；实际选中https://www.ece.ucsd.edu/faculty-research/Ultrafast%20and%20Nanoscale%20Optics%20Group%20%28Professor%20Shaya%20Fainman%29，原observedAt 2026-10-16T02:16:23+00:00；direct 1、related 0，优先direct。
- 860：listed https://pages.ucsd.edu/~scoulson/laboratory.htm；实际选中https://pages.ucsd.edu/~scoulson/laboratory.htm，原observedAt 2026-10-16T01:00:52+00:00；direct 1、related 1，优先direct。

606的literal parentheses与实际%28/%29编码归于同一请求；scheme、www及非根路径尾斜线不会被content reuse key折叠成直接请求。

## Modern seed / actual-wire separation

- 549：discovery/queue seed为http://flyingv.ucsd.edu/krstic/Research.html，source.requestedUrl/checkedUrl及followup.requestedUrl为https://flyingv.ucsd.edu/krstic/Research.html。原observedAt 2026-10-16T03:18:32+00:00、body SHA-256 d5b21bd94b4ef00ed2e143e395cab305b1d20cff58510349691d24ab0713f212均匹配gap receipt；checkMatchesDiscoveryUrl=false，HTTP redirectChain仍为空，没有虚构http→https重定向。
- 879：discovery/queue seed为http://thiemensgroup.ucsd.edu/research.html，source.requestedUrl/checkedUrl及followup.requestedUrl为https://thiemensgroup.ucsd.edu/research.html。原observedAt 2026-10-16T03:18:36+00:00、body SHA-256 344881ab9009ef2303b699e386abe133db4b0736429fff61e9cec4948e82d37d均匹配gap receipt；checkMatchesDiscoveryUrl=false，HTTP redirectChain仍为空，没有虚构http→https重定向。

## Pending separate identity bindings

- 1 / ucsd-anesthesiology-lab-case-lab：所选https://www.caselaboratory.org/，原observedAt 2026-10-16T00:57:39+00:00；本快照verified=false，待独立身份绑定审阅。
- 171 / ucsd-lab-from-faculty-bethel-lab-org：所选http://bethel-lab.org/，原observedAt 2026-10-16T01:04:58+00:00；本快照verified=false，待独立身份绑定审阅。
- 225 / ucsd-lab-from-faculty-goren-lab-github-io：所选http://goren-lab.github.io/，原observedAt 2026-10-16T01:05:04+00:00；本快照verified=false，待独立身份绑定审阅。
- 261 / ucsd-neurosciences-lab-shtrahman-lab：所选http://shtrahmanlab.org/，原observedAt 2026-10-16T01:05:11+00:00；本快照verified=false，待独立身份绑定审阅。
- 467 / ucsd-live-lab-572dea7b979dc2：所选https://isn.ucsd.edu/index.php，原observedAt 2026-10-16T01:03:09+00:00；本快照verified=false，待独立身份绑定审阅。
- 668 / ucsd-live-lab-f426b74f514b6d：所选http://www.palmerlab.org/，原observedAt 2026-10-16T01:07:02+00:00；本快照verified=false，待独立身份绑定审阅。

本报告不替该6条接受新身份引文；后续checkpoint可能反映其完成结果。JSON保存本次全部投影字节hash、样本详情、计数与错误。仅写本QA的Markdown/JSON。

## Final delta — six direct identity bindings resolved

独立delta审阅时间：2026-10-16T03:46:32+00:00；新投影checkpoint时间：2026-10-16T03:44:57+00:00。此前03:40:19投影的491 verified / 6 pending仍作为上文历史快照保留；本节为完成6条独立身份绑定后的增量。

结果：通过，错误0。 880 processed、692 lab/group研究支持、797 listed-target URI + 83 related-target URI（历史URI分类，非页面wire计数）保持；verified listed lab/group URL从491增至497。6 pending全部解决，48条related-only退出计数仍全部为false。

逐条检查所选实际请求URL、原observedAt、final URL与缓存字节hash一致；新quote只支持identity。通过与修复前Git 02609f9逐字段比较，6条科学摘要/问题/主题/方法/既有身份结论/不确定性/旧reviewedAt保持，旧evidence是逐字不变的前缀；每条仅新增1条identity引用及独立binding review元数据。

- 1 / ucsd-anesthesiology-lab-case-lab：https://www.caselaboratory.org/ → https://www.caselaboratory.org/，observedAt 2026-10-16T00:57:39+00:00，SHA-256 a07cb1647f924f14249fa1b57d76505aabcd457a5d5dba613e867df37df095e0；title quote“CASE LAB”；新绑定reviewedAt 2026-10-16T03:44:21+00:00，原科学reviewedAt 2026-10-16T02:33:20+00:00保持。
- 171 / ucsd-lab-from-faculty-bethel-lab-org：http://bethel-lab.org/ → https://www.bethel-lab.org/，observedAt 2026-10-16T01:04:58+00:00，SHA-256 01d2495ed8b8f67645617f4bf7718b9ad7690be5612f2642ac867c8a492b8d47；body quote“The Bethel Lab”；新绑定reviewedAt 2026-10-16T03:44:21+00:00，原科学reviewedAt 2026-10-16T02:35:14+00:00保持。
- 225 / ucsd-lab-from-faculty-goren-lab-github-io：http://goren-lab.github.io/ → https://goren-lab.github.io/，observedAt 2026-10-16T01:05:04+00:00，SHA-256 206fd9fea8f03aa0cf62d635a8ae1a38e883185c3a7cafa7aeff7ca8643b2aea；body quote“Welcome to the Goren Lab”；新绑定reviewedAt 2026-10-16T03:44:21+00:00，原科学reviewedAt 2026-10-16T01:53:40+00:00保持。
- 261 / ucsd-neurosciences-lab-shtrahman-lab：http://shtrahmanlab.org/ → https://shtrahmanlab.org/，observedAt 2026-10-16T01:05:11+00:00，SHA-256 e521b4ab9962cd9b02563cdbc87ee38a135dafc03fc80fd3b204425060624388；title quote“Shtrahman Lab – UCSD DEPARTMENT OF NEUROSCIENCES”；新绑定reviewedAt 2026-10-16T03:44:21+00:00，原科学reviewedAt 2026-10-16T02:18:44+00:00保持。
- 467 / ucsd-live-lab-572dea7b979dc2：https://isn.ucsd.edu/index.php → https://isn.ucsd.edu/index.php，observedAt 2026-10-16T01:03:09+00:00，SHA-256 5c6c8fd62a5212f90ef10a6ceb914b25e5cd5642b8bc19a03befbb35a6aaf7e3；body quote“Integrated Systems Neuroengineering (ISN) Laboratory”；新绑定reviewedAt 2026-10-16T03:44:21+00:00，原科学reviewedAt 2026-10-16T01:55:29+00:00保持。
- 668 / ucsd-live-lab-f426b74f514b6d：http://www.palmerlab.org/ → https://palmerlab.org/，observedAt 2026-10-16T01:07:02+00:00，SHA-256 9cd864afd4d732b89f3bfc91fb7389db2e94c6da7fb0543142402287cf797b5a；title quote“PalmerLab.org -”；新绑定reviewedAt 2026-10-16T03:44:21+00:00，原科学reviewedAt 2026-10-16T02:37:26+00:00保持。

其中5条新旧捕获字节hash相同，复用既有内容审阅但绑定实际direct request；CASE的HTTPS旧捕获与之后HTTP捕获hash不同，仅采用该HTTPS捕获的明确CASE LAB文档标题，不冒充same-body复用。没有重读科学正文或HTML、没有新HTTP/prepare/checkpoint/测试；只读取原缓存字节计算6个hash并检查短身份引文。

JSON的original counts/pending列表属于491历史快照；finalDelta与latestAssessment明确记录497最终快照、对应新projection hash和resolvedPendingLabIds，避免覆盖审阅时间线。

## Final two delta — distinct Komiyama request bindings

独立审阅时间：2026-10-16T03:49:58+00:00；当前投影checkpoint时间：2026-10-16T03:48:17+00:00。只核验84/627新增根页title身份引文及实际request/time/hash/redirect元数据；没有全880重审或研究/HTML正文重读。

结果：通过，未决问题0。 verified listed URL由497增至499；880 processed、692 lab/group研究支持、797 listed-target URI + 83 related-target URI（历史URI分类，非页面wire计数）不变；48条former-related退出计数仍全部false。原491及497阶段的报告与投影hash保持为历史快照。

- 84 / ucsd-biology-topic-lab-komiyama-lab：实际请求https://komiyamalab.biosci.ucsd.edu/，HTTP终点https://komiyamalab.biosci.ucsd.edu/；observedAt 2026-10-16T01:04:11+00:00；原缓存SHA-256 24303545ccbdc9fd651405aee20691fb7c6e5fec5046e34fb37888ea2fdcfbe7；逐字title引用“Komiyama Lab |”。HTTP链：[]。
- 627 / ucsd-live-lab-421d1a9d198202：实际请求https://labs.biology.ucsd.edu/komiyama/html/Home.html，HTTP终点https://komiyamalab.biosci.ucsd.edu/；observedAt 2026-10-16T01:06:46+00:00；原缓存SHA-256 24303545ccbdc9fd651405aee20691fb7c6e5fec5046e34fb37888ea2fdcfbe7；逐字title引用“Komiyama Lab |”。HTTP链：[{"from": "https://labs.biology.ucsd.edu/komiyama/html/Home.html", "to": "https://komiyamalab.biosci.ucsd.edu/", "httpStatus": 301}]。

84采用01:04:11的直接root请求，没有借用旧Home路径的301；627采用01:06:46的旧Home实际请求及真实301到root。相同响应字节没有被当作相同请求。根页正文仍为空，title只支持身份，研究仍来自先前已审同站/home/链。

两条affiliation仍uncertain，旧研究sourceId/原时间/hash及既有引文保持；03:34:40首次目标绑定历史仍保存在previousReviewedAt和原receipt中，新title身份审阅时间为03:47:48。原首次receipt字节hash与新receipt引用一致。仅写本QA Markdown/JSON，未作新HTTP、测试、prepare/checkpoint或任何代码/raw/packet/聚合更改。

## Final page-request proof boundary

元数据独立审阅时间：2026-10-16T03:55:56+00:00；当前checkpoint：2026-10-16T03:52:59+00:00。此前491→497→499的身份/来源证据时间线保留；此前797/83已改名为URI-target分类，不能当作实际页面wire次数。

结果：通过，错误/未决问题0。 880条记录精确拆分为715条listed页面尝试证明、78条related页面尝试证明、82条listed访问前置检查、5条related访问前置检查。这里统计lab URL receipt，不是去重的HTTP请求数，也不是本任务新wire次数。

- 87条precheck的requestedUrl全部为null；checkedUrl只表示已评估的target；pageRequestProven=false、listedUrlDirectlyChecked=false、verified=false，canonicalBasis=no_page_request_proven，均无新live页面声明。
- sourceUrl字段存在或robots.httpStatus有返回值均不能单独证明请求了页面。顶层页面HTTP状态（包括transport0）、有实际wire关联的explicit actualPageRequestMade，或从初始target发出的真实页面HTTP redirect，才构成页面尝试证明。
- 有缓存HTTP200的记录保留原capture证明与原时间，但没有因此标记新live页面请求；102条followup元数据均与原JSON capture的实际请求/观察时间/终点/redirect/status精确匹配。
- 3条先请求初始页面、再在redirect target被robots阻止的边界保留初始requestedUrl与pageRequestProven=true；仍不把blocked target当作已取得页面，也不计入verified实验室URL。

- 116 / ucsd-biology-topic-lab-roy：初始页面https://roylab.biosci.ucsd.edu/；原observedAt 2026-10-16T01:04:39+00:00；初始HTTP跳转[{"from": "https://roylab.biosci.ucsd.edu/", "to": "https://roylab.biology.ucsd.edu/", "httpStatus": 301}]；后续blocked target https://roylab.biology.ucsd.edu/，最终状态robots_unavailable，verified=false。
- 161 / ucsd-cellular-molecular-medicine-lab-sander-lab：初始页面http://msanderlab.org/；原observedAt 2026-10-16T01:19:41+00:00；初始HTTP跳转[{"from": "http://msanderlab.org/", "to": "https://msanderlab.org/", "httpStatus": 301}]；后续blocked target https://kemenagkabmanokwariselatan.com/，最终状态robots_unavailable，verified=false。
- 663 / ucsd-live-lab-7976bbb628cbc8：初始页面https://medschool.ucsd.edu/som/pediatrics/Divisions/infectious-diseases/research/liulab/Pages/default.aspx；原observedAt 2026-10-16T01:06:56+00:00；初始HTTP跳转[{"from": "https://medschool.ucsd.edu/som/pediatrics/Divisions/infectious-diseases/research/liulab/Pages/default.aspx", "to": "https://sites.medschool.ucsd.edu/som/pediatrics/divisions/infectious-diseases/research/liulab/pages/default.aspx", "httpStatus": 302}]；后续blocked target https://sites.medschool.ucsd.edu/som/pediatrics/divisions/infectious-diseases/research/liulab/pages/default.aspx，最终状态robots_unavailable，verified=false。

- 715+82=797、78+5=83，因此历史URI-target分类能与新的proof/precheck分类完整对账。499 verified listed lab/group URL及692研究支持保持；own fetch98、wire114保持，本次新请求0。
- 新增JSON snapshot保存当前投影hash、全部87个precheck元数据、3个redirect边界及历史字段更名记录。只更新本QA Markdown/JSON，没有HTML读取、科学正文重审、测试、prepare、checkpoint或代码/raw/packet/聚合/collector修改。

原JSON匹配包含保留的attemptHistory：collector当前latest fetch可能已推进，冻结packet仍使用原observedAt的真实历史attempt；不因最新queue状态不同而替换旧观察或借用新时间。
