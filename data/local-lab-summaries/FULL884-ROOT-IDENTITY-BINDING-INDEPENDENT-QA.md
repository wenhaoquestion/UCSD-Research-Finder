# 原 HTTPS 根身份绑定独立 QA

审阅时间：2026-10-16T07:59:50+00:00。**PASS：8项均适合仅追加身份引文。**

计划 SHA256：`a2e7524f675df41620c02966f661269996fb16657a7ae0e1db23f34a484c119f`。8组原HTML/bodySHA、原sidecar字节哈希、请求与最终URI、原观察时间全部核验，7项title和1项body引文与缓存原文相符。

以当前raw深拷贝进行8次pure hydrate，均由canCount=false变为true；pageIdentity从uncertain变为confirmed。其余URL/root/canonical/redirect/source-time、身份实体、隶属及科研字段完全一致。这是反事实检查，实际恢复数仍为0。

**实施必须读最新raw，只追加批准的identity evidence和reviewmetadata，禁止用newRecordPreview覆盖。** Süel和Frazer已应用问题字段更新，其当前raw与已授权question journal的newRecord精确相同，新增问题及全部证据须保留；其余6条仍为plan oldSHA。新review字段应保存实施前真实current reviewedAt，来源时间不可改写。

| ordinal | 实验室 | 原请求 / 原观察时间 | 精确身份引文 | QA范围 |
|---:|---|---|---|---|
| 496 | Gurol M. Suel — lab website | https://suellab.github.io/ / 2026-10-16T01:06:31+00:00 | Süel Lab (title) | 原HTTPS捕获的字面标题 Süel Lab 与已接受官方Gürol Süel页面及其精确 Lab Website → https://suellab.github.io/ 对应。该根捕获可见研究正文为空，仅用具名title作identity，不转为研究或任职证据。 |
| 466 | Carlos Coimbra — lab website | https://coimbra.ucsd.edu/ / 2026-10-16T01:00:13+00:00 | Coimbra Research Group (title) | 标题 Coimbra Research Group、正文同名group及Carlos F. M. Coimbra明确对应现有Coimbra研究组，不是仅凭个人姓名或HTTP成功。 |
| 828 | ARMOR Lab (Active, Responsive, Multifunctional, and Ordered-materials Research) | https://armor.ucsd.edu/ / 2026-10-16T01:00:50+00:00 | ARMOR Lab (title) | 标题 ARMOR Lab 与正文完整缩写释义、UC San Diego laboratory及负责人Prof. Ken Loh一致，匹配现有稳定ID。 |
| 181 | MACRO Lab | https://macrolab.ucsd.edu/ / 2026-10-16T00:59:39+00:00 | MACRO Lab – MACRO Lab (title) | 标题 MACRO Lab – MACRO Lab 与正文MACRO Lab任务和co-directors描述一致，匹配包内既有MACRO实验室身份材料。 |
| 442 | Acevedo Lab website | https://acevedo.ucsd.edu/ / 2026-10-16T01:00:06+00:00 | FRACTURE AND FATIGUE OF SKELETAL TISSUES LABORATORY F² LAB (body) | 正文完整 F² LAB 名称与下文该实验室由Dr. Claire Acevedo领导的明确关系，解决Acevedo列出名称与F²实际实体名的绑定；不重命名稳定ID。 |
| 502 | Hanh-Phuc Le — lab website | https://ipower3es.ucsd.edu/ / 2026-10-16T01:00:27+00:00 | integrated Power Electronics and Energy-Efficient Systems Lab – Create and Supply Integrated/Miniaturized Power for All (title) | 原HTTPS请求确实跳至已捕获eng子域；具名iPower3Es实验室title与官方Jacobs页完整实验室名及Prof. Hanh-Phuc Le关系一致，正文group/Prof. Le上下文再次对应。保留旧301及旧collector Location限制。 |
| 614 | Zhong Lab | https://systemsbio.ucsd.edu/ / 2026-10-16T01:01:20+00:00 | Welcome to Zhong Lab of Systems Biology (title) | 标题明确Zhong Lab of Systems Biology；本地About the PI将Sheng Zhong与后续About the lab连接，匹配当前Zhong Lab。标题证据不受后续研究文本截断影响，不借此扩展科研。 |
| 490 | Frazer Lab | https://frazer.ucsd.edu/ / 2026-10-16T01:00:18+00:00 | Home Page / Frazer Lab (title) | 原HTTPS根标题 Home Page | Frazer Lab 与该实验室iPSCORE/our lab正文一致。HTML canonical-link的http://frazer.ucsd.edu/home只保留为提示，不当作HTTP跳转或替换原HTTPS实际请求。 |

Süel原根正文为空，只取具名title且由既有官方Lab Website精确关联支持；Zhong不以截断后的正文扩展科学。iPower3Es保留原实际301及旧collector对Location未完整保留的限制；Frazer的HTTP canonical-link不当作HTTP重定向。

0网络请求、0PS检查；仅写本报告对，不改raw/packet/source/代码/collector。实施后由父代理逐条hydrate及全量validate。

## 已冻结应用计划的补充 QA

复核时间：2026-10-16T08:01:07+00:00。**PASS，无必改项。**初始来源审阅时间保持 `2026-10-16T07:59:50+00:00`。

helper SHA256：`71beaf7deaaa534554ecfd59d87b8b72e7429c9f48c15f518e8d7df3623a74fc`；planned journal SHA256：`8b9ecebb2a3bbee51cc2ec6af226b1cbf9f8848b7b99e09e9453a5097b03d4d6`。本次未运行helper或`--apply`。

8条newRecord均从当前已授权raw构建，实际只变evidence、reviewedAt、rootIdentityBindingReview三个字段；全部旧证据为精确前缀，Süel/Frazer已补的新questions及questionFieldReview完整保留。实际binding验证时间为07:59:14UTC，previousRecordReviewedAt取各条当前值；sourceActualObservedAt保持原捕获时间。

逐条验证8组当前raw/packet冻结哈希及8组old/new hydrate，均false→true，其他请求、final、canonical、redirect和来源日期完全不变。完整oldRecord可重建原字节SHA；原子写入和中断后精确newRecord识别可恢复。仅修改八条records及进度journal，无packet/source/network写入。计划569→577为总数预期，本QA未进行正式应用或全量聚合。
