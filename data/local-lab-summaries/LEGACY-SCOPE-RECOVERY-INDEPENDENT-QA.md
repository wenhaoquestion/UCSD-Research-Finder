# Legacy scope recovery independent QA

独立审阅：2026-10-16T06:30:11+00:00。基准`be761922b9308a3a097950367f0beb848a36c701`。只读核验Hamilton619/620、Kravets526及Interactive Cognition179；0网络、0数据应用、0采集器/共享状态写入。

**四条本地完整性与科研作用域检查PASS，未发现待修问题。初稿06:30:11保留当时待parent finalize状态；下方06:31最终绑定已完成。**

| 记录 | 科研及实体范围 | 方法/问题/隶属边界 | 原根页 |
|---|---|---|---|
| Hamilton619/620 | [Bruce Hamilton官方历史profile](https://profiles.ucsd.edu/bruce.hamilton)中明确His laboratory的整组研究句；两个Hamilton Lab真实锚点分别精确匹配各ID原URL及大小写。 | 仅神经发育遗传调控、修饰基因网络、血压神经调控遗传变异；methods及questions均空，affiliation uncertain。没有把训练经历、基金或论文移入全组方法。 | robots前置检查失败保留；requestedUrl/canonical仍null，pageIdentity uncertain，verified false。 |
| Kravets526 | [具名实验室页](https://kravetslab.ucsd.edu/)Our goal/We aim与Selected projects支持全部摘要、问题和主题；原[Vira Kravets官方个人页](https://jacobsschool.ucsd.edu/people/profile/vira-kravets)有真实Website链接指向该根站。 | 五项方法分别由Approaches及胰岛电生理simulation字面支持；无疗效或额外技术推断。UCSD来自具名lab正文，source_reported但无当前日期。 | 保留原个人profile URL，未改成lab站或捏造redirect；pageIdentity uncertain，verified false。 |
| Interactive179 | [David Kirsh索引](https://adrenaline.ucsd.edu/Kirsh/index.html)My Lab真实链接至[Interactive Cognition Lab正文](https://adrenaline.ucsd.edu/Kirsh/lab.html)，复用已有相同正文语义审阅；根script只存导航审阅metadata。 | methods空；历史官方目录同名lab/PI证据与be76192中511原source精确一致，原2026-10-02观察时间保留，明确不确认当前隶属或负责人。 | 根Welcome正文仍空，没有加根identity quote；仍原HTTPS根、redirects=[]、pageIdentity uncertain、verified false。无alias/ID merge。 |

Hamilton唯一科研句为“His laboratory is interested in genetic control of neural development, modifier gene networks, and genetic variation in neural control of blood pressure.”；它的主语明确是laboratory。新profile源`src-f36a14458458298d`原观察2026-10-07T22:02:57+00:00，SHA `9ff4279cc7fc83c9302f07bbc24e292b62203511d203713182da21ef0950382e`。没有把复制快照时间06:24/应用时间06:27当作新观测。

Kravets源`src-61e86406fc714b07`原观察2026-10-16T01:00:26+00:00，SHA `8db5335d76e59f4b1257fa3498e08fb34f27d5cecb5c0172f4548c42c5e3afad`。正文明确“Laboratory of Dr. Vira Kravets at UCSD”；五项方法来自Targeted 2-photon laser ablation、Confocal microscopy、Fluorescence Lifetime Imaging、Computational models/胰岛electrophysiology simulations及Network (graph) theory。Page updated仅文字无日期；不推断当年项目或在任状态。

完整性逐条比对均通过：application记录的旧raw/packet SHA匹配git旧字节；`previousReviewedRecordBeforeLegacyScopeRecovery`为完整旧raw精确副本；旧evidence/source数组前缀逐项相等；preparedAt、listedWebsite、latestDestinationFetch及除追加sources/cachedScopeReviews外的全部packet字段保持不变。四条旧/新raw分别hydrate共8次均通过，所有当前证据quote在对应body/title/headings逐字存在。

新增6个source对象、5个独立sourceId，其中4份独立HTML快照。4份snapshot HTML及original sidecar均与其原路径逐字节相同，SHA与receipt、源body hash相符；新source的实际request/final URI、original observedAt、HTTP状态均绑定原sidecar；重提取全文/title及deterministic sourceId一致。3份collector sidecar明确redirects=[]；Hamilton旧profile sidecar仅保留原final URI，未额外声称新跳转检查。Interactive既有正文SHA与此前报告完全相同；其历史目录摘录按历史字段证据保留，没有伪造HTML哈希。

网络台账`gap-results.json`整字节等于be76192：344 actual wires、202 receipts，SHA `af7c4da100b9d831b691f65c5109024fb16b8e0b7b229f6e1c420f77b459bf23`。`identity-decisions.json`整字节同基准，14个未解决mismatch不变，SHA `d03f63cfc224974df2951ebbc152619fc05289431dbcb69781c888df5874362a`。没有新增ID、接受alias或放宽这些门禁。

5个实现文件加11个测试文件共16份逐字节等于be76192，且与既有local-validation-tests.json哈希全部相符；因此复用该receipt记录的252项PASS、0网络结果。本次没有重跑全套测试，也未把receipt中的历史测试计数当作本次新实绩。各文件SHA与逐条source/record证明均见JSON。

## Final projection binding

独立绑定核验：2026-10-16T06:31:05+00:00，parent validation生成于06:30:10。四条当前raw重新hydrate均与summaries.jsonl及url-verification.jsonl各自完整序列化行精确相等。其余880条summary及880条URL行分别与be76192对象精确相同，全部884个stable ID及顺序保持；manifest884个sourceCount逐项等于实际packet source数，stale=0。

Parent于06:30:08仅将Kravets uncertainty[1]澄清为“正文列出有无糖尿病条件的活胰腺组织作为研究材料；不据此推断临床疗效、体内实验或额外实验技术。” 本次以字面逆替换重建初始raw SHA，确认这是唯一变化，摘要/问题/主题/方法/证据/科研reviewedAt全部未变；最终Kravets raw SHA为`07dc7fd1374c597de0880602bca14e1daa648a304abb66ddecc623ce5547114c`。初始旧术语hash单独留在JSON chronology；4个packet SHA及其他3个raw SHA均未变化。

最终884/884 processed：736 supported、56 partial、92 unresolved；722 supported lab/group；569 verified original URLs（本批增加0）。outputsAreComplete仍false。Parent validation的1054 unique evidence cache检查、errors=[]、digestWarnings=[]、14个mismatch accepted=0均已读取，projection哈希全部独立重算匹配；本次未重跑其全量validator或科研全文复核。

最终projection SHA-256：

- summaries.jsonl：`3e65eaef1aacb039c6ab8948a72f3f3e3d2bc4495e04ea9b739c700f267f2c88`
- url-verification.jsonl：`8bd3d9d2e2635d523cf4448a0e4c4810fd98cd88b93b72b028b09413a41fb6bf`
- queue.json：`58023dc075925fe01dd8292720f654b4806835ffe887af709c9113b4d03951c3`
- checkpoint.json：`976aef9ff414bff9adb8678b412b2fe0da5ba7715e1bcc08cb8230437d9d382f`
- validation.json：`e3266a4ad3fd4ec341ca5a3dceb1a7e5cf12b1ede41bea9c45a2614a4bbf59bb`

当前application receipt SHA：`9ff0bd501afb6294edc7120fc571d732bd9450f2556da8ba8a57dc7272c80a47`。344/202网络台账和14门禁最终再核hash仍不变。未完成的本次独立QA项：0。
