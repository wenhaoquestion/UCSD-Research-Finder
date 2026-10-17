# 剩余原HTTP根正文审阅：索引024–033

实际审阅：2026-10-16T05:17:36+00:00。只新增本Markdown及同名JSON；0网络请求，0 raw/packet/receipt/code修改。

10条均实际HTTP200，完整读取10个新缓存根正文及title/headings/必要HTML；SHA、source-fet​​ch和原请求URI绑定均通过。6条与旧根完整提取正文相同；具体比较来源和原日期在JSON逐条保存。

身份判断7 confirmed（Kim、Kummel、Romero、Tezcan、MMRL、Stauber、Ferguson），3 uncertain（Jennings、Theodorakis、SHM），0 mismatch。Jennings仅有具名标题且当前实体范围仍provisional；不是HTTP成功便接受。

根正文直接恢复whole-lab科研3条：Kim、Stauber、Ferguson。Tezcan的具体方法来自独立Research捕获，不来自根页。父代理已应用这4条科学恢复及Kummel/Romero/MMRL身份绑定；本报告核验当前字段，不重复编辑。当前只读hydrate确认4条accepted lab/group原URL，实际应用数0。

所有根fetch.redirects均为[]。HTML frame/meta与实际后续页面请求分别记录，不当作根HTTPredirect或canonical迁移。13个既有mismatch门禁及新增Sinha门禁均未更改。

## 024 · ucsd-chemistry-biochemistry-lab-jennings-lab

原literal [http://jenningslab.ucsd.edu](http://jenningslab.ucsd.edu)；实际请求 [http://jenningslab.ucsd.edu/](http://jenningslab.ucsd.edu/)；最终 `http://jenningslab.ucsd.edu/`。状态 `ok` / HTTP `200`，redirects `[]`。
sourceId `src-28f455c9c1ad8216`；observedAt `2026-10-16T04:57:02+00:00`；liveCheckedAt `2026-10-16T04:57:01+00:00`；SHA256 `67f95d3c0b382d5be686b78781e693f00d42ccc881c40b3a6e987be872d29afa`。
完整提取正文 `0` 字符；与旧根sameFullVisibleText `True`，sameByteBody `True`；空文本 `True`。
身份 **uncertain**；决定 `title_name_only_pending_whole_lab_scope`。原HTTP根页只有 Jennings Lab 标题与图像导航，没有可见研究正文。标题可记录具名站点，但尚无本页具名负责人/whole-lab科研段落来解除既有身份范围不确定性；保留partial，等待已单独审阅的research.html后续捕获。
- `title` · `identity`：Jennings Lab
- 仅发现 `html_anchor` 字面 `research.html` → `http://jenningslab.ucsd.edu/research.html`；不是HTTPredirect或科研证据。
当前raw `partial`、原科学reviewedAt `2026-10-16T01:48:38+00:00`、既有身份绑定时间 `None`全部保留；本审阅不替换日期。
只读hydrate：pageIdentity `uncertain`，acceptance `provisional_or_unresolved`，canCount `False`。
packet SHA `66261ab75d735bd691870c38982e71a473aa90c1bdd52927fc07dd4ed96a07e5`；raw SHA `c4a70c7af749d5f6190ac115340c70e39300f3b6a6814d7246b09a0a73efaea7`；本条审阅 `2026-10-16T05:17:36+00:00`。

## 025 · ucsd-chemistry-biochemistry-lab-kim-group-judy-kim

原literal [http://galileo.ucsd.edu](http://galileo.ucsd.edu)；实际请求 [http://galileo.ucsd.edu/](http://galileo.ucsd.edu/)；最终 `http://galileo.ucsd.edu/`。状态 `ok` / HTTP `200`，redirects `[]`。
sourceId `src-8958d5c5bb90cf1a`；observedAt `2026-10-16T04:57:03+00:00`；liveCheckedAt `2026-10-16T04:57:03+00:00`；SHA256 `2d25977b236521d7f2e695c1fe32c06c22a26304f7d0ae2f166cece6afa3a208`。
完整提取正文 `788` 字符；与旧根sameFullVisibleText `False`，sameByteBody `False`；空文本 `False`。
身份 **confirmed**；决定 `retain_already_applied_root_science_and_identity`。根页明确 The Kim group 与 Judy Kim 联系信息；整组段落直接列蛋白动态、膜蛋白折叠、抗菌肽扰膜、自由基中间体及光谱/显微工具。当前raw已采用这些真实新正文，未发现需再改科学字段；正文使用Current projects但无完整内容发布日期。
- `title` · `identity,affiliation`：Kim Group Home - UCSD Chemistry and Biochemistry
- `body` · `identity,research,topics`：The Kim group is a diverse group of students, postdocs, and research staff with a strong interest in spectroscopic studies of protein dynamics.
- `body` · `research,topics`：Current projects include investigations of membrane protein folding, membrane disruption by antimicrobial peptides, and structure and dynamics of radical intermediates.
- `body` · `methods`：We utilize a host of powerful optical tools, including UV resonance Raman spectroscopy, transient absorption/emission spectroscopy, and microscopy.
- `body` · `identity`：Judy Kim

当前科学字段核验可保留：Kim 研究组以光谱学研究蛋白质动态，涉及膜蛋白折叠、抗菌肽引起的膜扰动及自由基中间体的结构与动态。方法包括紫外共振拉曼光谱、瞬态吸收/发射光谱和显微成像。
问题：如何用光谱学刻画蛋白质动态与膜蛋白折叠？；抗菌肽如何扰动膜，自由基中间体具有怎样的结构与动态？。
主题：蛋白质动态与膜蛋白折叠；抗菌肽与膜扰动；自由基中间体结构与动态。
方法：紫外共振拉曼光谱；瞬态吸收/发射光谱；显微成像。
当前raw `supported`、原科学reviewedAt `2026-10-16T05:11:05+00:00`、既有身份绑定时间 `None`全部保留；本审阅不替换日期。
只读hydrate：pageIdentity `confirmed`，acceptance `accepted_lab_group`，canCount `True`。
packet SHA `c5c0f24793816b32a7a8db0b1df25241bd2ccd01c69f74c729a55629a447780f`；raw SHA `44cd3847a76a43b371e253e0ebb8e8af01d6804380df2c72853a124f9312a6c4`；本条审阅 `2026-10-16T05:17:36+00:00`。

## 026 · ucsd-chemistry-biochemistry-lab-kummel-lab

原literal [http://kummelgroup.ucsd.edu](http://kummelgroup.ucsd.edu)；实际请求 [http://kummelgroup.ucsd.edu/](http://kummelgroup.ucsd.edu/)；最终 `http://kummelgroup.ucsd.edu/`。状态 `ok` / HTTP `200`，redirects `[]`。
sourceId `src-4eed6cd432ff1acd`；observedAt `2026-10-16T04:57:05+00:00`；liveCheckedAt `2026-10-16T04:57:05+00:00`；SHA256 `568e6a760a2416fb3ac385f66df55208453b3ee8dc9669415c8f4213f8effeeb`。
完整提取正文 `70` 字符；与旧根sameFullVisibleText `True`，sameByteBody `True`；空文本 `False`。
身份 **confirmed**；决定 `identity_only_frames_are_separate_documents`。具名Kummel Lab字面标题足以匹配既有confirmed实验室身份；根页只有欢迎标题和frameset/空fallback，没有整组研究。home.htm与side.htm是独立frame src发现，不是HTTP跳转、canonical或研究证据；保留原partial科学字段。
- `title` · `identity`：Welcome to the Kummel Lab Web Page!!!
- 仅发现 `html_frame_source` 字面 `side.htm` → `http://kummelgroup.ucsd.edu/side.htm`；不是HTTPredirect或科研证据。
- 仅发现 `html_frame_source` 字面 `home.htm` → `http://kummelgroup.ucsd.edu/home.htm`；不是HTTPredirect或科研证据。
当前raw `partial`、原科学reviewedAt `2026-10-16T01:48:38+00:00`、既有身份绑定时间 `None`全部保留；本审阅不替换日期。
只读hydrate：pageIdentity `confirmed`，acceptance `provisional_or_unresolved`，canCount `False`。
packet SHA `ee6a440d29b0920274749244cc6d153d783532efcc1880c4831f35b5f61edc2d`；raw SHA `c62cbcd2c1dc53d3678c09569dda5e729cf0d10b7cdea2774091fbad42dc2b3f`；本条审阅 `2026-10-16T05:17:36+00:00`。

## 027 · ucsd-chemistry-biochemistry-lab-romero-research-group-erik-romero

原literal [http://r2g.ucsd.edu](http://r2g.ucsd.edu)；实际请求 [http://r2g.ucsd.edu/](http://r2g.ucsd.edu/)；最终 `http://r2g.ucsd.edu/`。状态 `ok` / HTTP `200`，redirects `[]`。
sourceId `src-04a051aebaebcc7c`；observedAt `2026-10-16T04:57:07+00:00`；liveCheckedAt `2026-10-16T04:57:07+00:00`；SHA256 `25c774bbc43f61f0d282c3cd44b9a1f796bf24ba6e44c3a00b0aed43d355b707`。
完整提取正文 `43` 字符；与旧根sameFullVisibleText `True`，sameByteBody `True`；空文本 `False`。
身份 **confirmed**；决定 `identity_only_named_group_body`。正文与heading拼字呈现 The R omero R esearch G roup 与 @ UC San Diego，明确实验室组名及自述机构。现根页没有具体研究或方法；保留partial和旧负责人领域引用，不把Intro Animation标题当实验室名称或科研。
- `body` · `identity,affiliation`：The R omero R esearch G roup @ UC San Diego
当前raw `partial`、原科学reviewedAt `2026-10-16T01:48:38+00:00`、既有身份绑定时间 `None`全部保留；本审阅不替换日期。
只读hydrate：pageIdentity `confirmed`，acceptance `provisional_or_unresolved`，canCount `False`。
packet SHA `f3663821108984038cf43dea1b18108444b9d2da459343e7eb9c29702bf78068`；raw SHA `acaf430429504fa58aa92769ed940869fa849e665d9f17f72ba0f108d86358fc`；本条审阅 `2026-10-16T05:17:36+00:00`。

## 028 · ucsd-chemistry-biochemistry-lab-tezcan-lab

原literal [http://tezcan.ucsd.edu](http://tezcan.ucsd.edu)；实际请求 [http://tezcan.ucsd.edu/](http://tezcan.ucsd.edu/)；最终 `http://tezcan.ucsd.edu/`。状态 `ok` / HTTP `200`，redirects `[]`。
sourceId `src-f01bfbff3e573fae`；observedAt `2026-10-16T04:57:09+00:00`；liveCheckedAt `2026-10-16T04:57:09+00:00`；SHA256 `987fe31b27c95551726edb9c0cb799b8151c7a66a9372e072b678f79345ca78a`。
完整提取正文 `231` 字符；与旧根sameFullVisibleText `False`，sameByteBody `False`；空文本 `False`。
身份 **confirmed**；决定 `root_identity_separate_from_captured_research_followup`。根标题明确Tezcan Lab，正文只有金属生物学主题、欢迎语及导航。当前raw的具体主题/方法来自另行实际捕获Research页src-fd1ab018e68b72e8（observedAt05:00:15），不能归给04:57:09根页；该followup已具名Work by the Tezcan Group，当前完整科学字段可保留。
- `title` · `identity`：Tezcan Lab
- `body` · `topics`：Exploring, Expanding, and Evolving the Roles of Metals in Biology
另页Research：[http://tezcan.ucsd.edu/index.php/research-2/](http://tezcan.ucsd.edu/index.php/research-2/)；`src-fd1ab018e68b72e8`；原observedAt `2026-10-16T05:00:15+00:00`；SHA `f522f38819b86654df8d9c707299c40dd6f6b11dd56146a14d4f4a1c148138b1`。实际请求 `http://tezcan.ucsd.edu/?page_id=867` 后301至此Research路径，仅属于该独立请求。
- 独立Research body · `identity,research,methods`：Work by the Tezcan Group spans all areas of chemistry and utilizes a diverse array of tools ranging from molecular biology, chemical synthesis, polymer science, and computational chemistry to X-ray crystallography, electron microscopy, spectroscopy and advanced materials characterization techniques.
- 独立Research body · `topics`：Metalloprotein Design Nitrogenase Structure and Function Chemical Design of Functional Protein-Based Materials

当前科学字段核验可保留：Tezcan 研究组研究金属蛋白设计、固氮酶结构与功能，以及功能蛋白材料的化学设计。结合分子生物学、化学合成和计算化学，并使用X射线晶体学、电子显微镜、光谱及材料表征方法。
问题：如何设计具有功能的金属蛋白与蛋白基材料？；如何理解固氮酶的结构与功能？。
主题：金属蛋白设计；固氮酶结构与功能；功能蛋白基材料。
方法：分子生物学与化学合成；计算化学；X射线晶体学、电子显微镜、光谱及材料表征。
当前raw `supported`、原科学reviewedAt `2026-10-16T05:11:05+00:00`、既有身份绑定时间 `None`全部保留；本审阅不替换日期。
只读hydrate：pageIdentity `confirmed`，acceptance `accepted_lab_group`，canCount `True`。
packet SHA `dee27cb526e7eabb559f8c8fe3513428479bb2ed0cc3da74d6a11346ec4d0908`；raw SHA `accbdbdfa9329c96393edf46db996d9360411f712647cbe22a5347f936c7ac96`；本条审阅 `2026-10-16T05:17:36+00:00`。

## 029 · ucsd-chemistry-biochemistry-lab-theodorakis-group

原literal [http://theodorakisgroup.ucsd.edu](http://theodorakisgroup.ucsd.edu)；实际请求 [http://theodorakisgroup.ucsd.edu/](http://theodorakisgroup.ucsd.edu/)；最终 `http://theodorakisgroup.ucsd.edu/`。状态 `ok` / HTTP `200`，redirects `[]`。
sourceId `src-3372ef1abcf939e2`；observedAt `2026-10-16T04:57:13+00:00`；liveCheckedAt `2026-10-16T04:57:12+00:00`；SHA256 `c68cda4ff35c8c0f979ca06faff6004917a86f963ad92ca4484b9e07e5654a23`。
完整提取正文 `27` 字符；与旧根sameFullVisibleText `True`，sameByteBody `True`；空文本 `False`。
身份 **uncertain**；决定 `retain_supported_science_root_identity_unbound`。根标题仅Index，提取正文仅css templates Previous Next；nav中的Theodorakis Group及Research链接是站点发现上下文，未进入本source可引用body/title/headings。既有supported科学由独立具名研究页支持，但本次原HTTP根还没有可匹配本schema引文的位置；不为根页伪造科研/身份quote，不迁移URL。
本根没有足以追加到body/title/headings的实体身份/研究quote；不借邻页、个人论文或导航填补。
当前raw `supported`、原科学reviewedAt `2026-10-16T03:21:31+00:00`、既有身份绑定时间 `None`全部保留；本审阅不替换日期。
只读hydrate：pageIdentity `uncertain`，acceptance `accepted_lab_group`，canCount `False`。
packet SHA `08e3ba9a946e4b660e40e4f40d435cd8cf66220d96f00ce80c5df44d5c721c35`；raw SHA `51e5fe69ac1d5d5ffafa060dc947c2e80b2f290ac66aaea9951bdac5b4c73805`；本条审阅 `2026-10-16T05:17:36+00:00`。

## 030 · ucsd-structural-engineering-lab-ucsd-structural-health-monitoring-shm-group

原literal [http://shm.ucsd.edu/](http://shm.ucsd.edu/)；实际请求 [http://shm.ucsd.edu/](http://shm.ucsd.edu/)；最终 `http://shm.ucsd.edu/`。状态 `ok` / HTTP `200`，redirects `[]`。
sourceId `src-78fc5f4fd64950d0`；observedAt `2026-10-16T04:57:37+00:00`；liveCheckedAt `2026-10-16T04:57:37+00:00`；SHA256 `3f8230dc8b243bf8ee4d8fde603d812f6935f9425e972e3495057c525bbbb5c5`。
完整提取正文 `0` 字符；与旧根sameFullVisibleText `True`，sameByteBody `True`；空文本 `True`。
身份 **uncertain**；决定 `blank_root_meta_target_discovery_only`。根页title和body均空；只有指向Site/Home.html的literal HTML meta refresh。该指令不是HTTP跳转或实体/科研证据；实际fetch.redirects为空，继续partial与具体正文障碍，等已审后续独立捕获。
本根没有足以追加到body/title/headings的实体身份/研究quote；不借邻页、个人论文或导航填补。
- 仅发现 `html_meta_refresh` 字面 `0;url= http://shm.ucsd.edu/Site/Home.html` → `http://shm.ucsd.edu/Site/Home.html`；不是HTTPredirect或科研证据。
当前raw `partial`、原科学reviewedAt `2026-10-16T01:53:25+00:00`、既有身份绑定时间 `None`全部保留；本审阅不替换日期。
只读hydrate：pageIdentity `uncertain`，acceptance `provisional_or_unresolved`，canCount `False`。
packet SHA `5dd891f7486628e4a1e8e0caf6fa116e713ff18a188ef6f41744a5cc6527595c`；raw SHA `581ac0f1424edaf9579ca7dcb2373dd027e8ce45b2f97353d8433700ea42aecc`；本条审阅 `2026-10-16T05:17:36+00:00`。

## 031 · ucsd-structural-engineering-lab-multifunctional-materials-research-laboratory-mmrl

原literal [http://mmrl.ucsd.edu/](http://mmrl.ucsd.edu/)；实际请求 [http://mmrl.ucsd.edu/](http://mmrl.ucsd.edu/)；最终 `http://mmrl.ucsd.edu/`。状态 `ok` / HTTP `200`，redirects `[]`。
sourceId `src-3bf96383b726f054`；observedAt `2026-10-16T04:57:39+00:00`；liveCheckedAt `2026-10-16T04:57:39+00:00`；SHA256 `9eeb38742f2f5d6b90b866022f7af2024241a4ff6c7fca6d69b1b3b5972f34b7`。
完整提取正文 `2842` 字符；与旧根sameFullVisibleText `True`，sameByteBody `True`；空文本 `False`。
身份 **confirmed**；决定 `identity_only_personal_style_page_with_lab_name`。正文明确Multifunctional Materials Research Laboratory及Yu Qiao，身份足以对上既有lab；页面主体是负责人履历、宽泛Research Interests和Selected Publications。领域列表可保留为有限兴趣，不能把论文标题或个人任职表转换成整组研究问题/方法或带日期的当前隶属；保留partial。
- `body` · `identity`：Multifunctional Materials Research Laboratory Yu Qiao
当前raw `partial`、原科学reviewedAt `2026-10-16T01:54:02+00:00`、既有身份绑定时间 `None`全部保留；本审阅不替换日期。
只读hydrate：pageIdentity `confirmed`，acceptance `provisional_or_unresolved`，canCount `False`。
packet SHA `9bb311a18d4c26a37a74a1616366def15c95cabf97910d68acf265b3b08870fc`；raw SHA `8651a24b4070667dc372383235062df5ce54af217690780e3018cad212691c6f`；本条审阅 `2026-10-16T05:17:36+00:00`。

## 032 · ucsd-chemistry-biochemistry-lab-stauber-lab

原literal [http://stauberlab.ucsd.edu/](http://stauberlab.ucsd.edu/)；实际请求 [http://stauberlab.ucsd.edu/](http://stauberlab.ucsd.edu/)；最终 `http://stauberlab.ucsd.edu/`。状态 `ok` / HTTP `200`，redirects `[]`。
sourceId `src-27301218356c2999`；observedAt `2026-10-16T04:57:41+00:00`；liveCheckedAt `2026-10-16T04:57:41+00:00`；SHA256 `5b62ea538e3ccb4e1638756fa37a7ddacc241d9f05efe1fa2816fe5396454915`。
完整提取正文 `1182` 字符；与旧根sameFullVisibleText `False`，sameByteBody `False`；空文本 `False`。
身份 **confirmed**；决定 `retain_already_applied_root_science_with_future_scope`。STAUBER LAB及UC San Diego与Our research program整体段落直接相连，支持仿生无机/有机金属化学、蛋白识别、活性物种和仿生催化方向。Synthetic inorganic chemistry will guide与potential to lead为计划/潜力措辞，当前raw已保留此限制；方法仅合成无机化学，不能推仪器方法。
- `headings` · `identity`：STAUBER LAB
- `headings` · `affiliation`：UC San Diego
- `body` · `research,topics`：Our research program is focused on a bioinspired approach to fundamental inorganic and organometallic chemistry that is motivated by addressing current challenges in chemistry and chemical biology.
- `body` · `methods,topics`：Synthetic inorganic chemistry will guide the development of new well-defined molecular systems designed to interact with complex biological targets by engaging in important protein-protein and protein-saccharide recognition processes.
- `body` · `research,topics`：Other research efforts are dedicated to building new bioinspired synthetic platforms by merging organic, inorganic, and biological architectures that have the potential to lead to the isolation and stabilization of interesting and new highly reactive species as well as the discovery of new biomimetic catalysts.
- 仅发现 `html_frame_source` 字面 `https://maps-api-ssl.google.com/maps?hl=en&ll=32.87612,-117.241925&output=embed&q=32.876506,-117.241877+(Untitled+Location)&z=17` → `https://maps-api-ssl.google.com/maps?hl=en&ll=32.87612,-117.241925&output=embed&q=32.876506,-117.241877+(Untitled+Location)&z=17`；不是HTTPredirect或科研证据。

当前科学字段核验可保留：Stauber 实验室以仿生思路研究基础无机与有机金属化学，利用合成无机化学设计参与蛋白质和糖类识别的分子体系，并探索仿生合成平台、活性物种稳定化与仿生催化剂。
问题：如何设计能参与蛋白质与糖类识别的分子体系？；如何通过仿生合成平台稳定高活性物种并发展仿生催化剂？。
主题：仿生无机与有机金属化学；蛋白质与糖类分子识别；活性物种与仿生催化。
方法：合成无机化学。
当前raw `supported`、原科学reviewedAt `2026-10-16T05:11:05+00:00`、既有身份绑定时间 `None`全部保留；本审阅不替换日期。
只读hydrate：pageIdentity `confirmed`，acceptance `accepted_lab_group`，canCount `True`。
packet SHA `673ec7ad72f6b0d55fd66ff92a0251988dac38e692e96daede80e3b416e3ed13`；raw SHA `1bd73e66d5386fbf5df56c4a399ad2f0af5acce28e023622066dd79938dbd3d6`；本条审阅 `2026-10-16T05:17:36+00:00`。

## 033 · ucsd-biochemistry-and-molecular-biophysics-lab-ferguson-lab-fleur-ferguson

原literal [http://fergusonlab.ucsd.edu](http://fergusonlab.ucsd.edu)；实际请求 [http://fergusonlab.ucsd.edu/](http://fergusonlab.ucsd.edu/)；最终 `http://fergusonlab.ucsd.edu/`。状态 `ok` / HTTP `200`，redirects `[]`。
sourceId `src-989b7fedff9fa338`；observedAt `2026-10-16T04:57:44+00:00`；liveCheckedAt `2026-10-16T04:57:43+00:00`；SHA256 `599359907591ac6336bd3c0363d04a3914e80f58b3b96a3bbfe4a1e9617499c5`。
完整提取正文 `995` 字符；与旧根sameFullVisibleText `False`，sameByteBody `False`；空文本 `False`。
身份 **confirmed**；决定 `retain_already_applied_root_science_and_identity`。具名Ferguson laboratory整体段落直接列有机合成、药物化学、质谱和细胞生物学，以及化学诱导近邻工具化合物与疾病信号网络。肿瘤/神经退行性疾病治疗策略是目标，不能写已证临床疗效；当前raw表述和限制可保留。页面part of与affiliated with须保持区别，不由域名推现时任职。
- `title` · `identity`：FERGUSON LAB
- `body` · `identity,research,topics,methods`：Research in the Ferguson laboratory applies organic synthesis, medicinal chemistry , mass spectrome try and cell biology towards the goal of developing new therapeutic strategies in oncology and neurodegenerative disorders.
- `body` · `research,topics`：Our research seeks to enable dissection of the cellular signaling networks underlying disease, through development of selective tool compounds that act via chemically induced proximity .
- `body` · `affiliation`：The Ferguson lab is part of: The Department of Chemistry and Biochemistry The Skaggs School of Pharmacy and Pharmaceutical Sciences

当前科学字段核验可保留：Ferguson 实验室结合有机合成、药物化学、质谱与细胞生物学，开发利用化学诱导近邻作用的选择性工具化合物，以解析疾病相关细胞信号网络。其应用目标包括肿瘤和神经退行性疾病的新治疗策略。
问题：如何利用化学诱导近邻的选择性工具化合物解析疾病相关细胞信号网络？。
主题：化学诱导近邻与工具化合物；疾病相关细胞信号；肿瘤与神经退行性疾病。
方法：有机合成与药物化学；质谱；细胞生物学。
当前raw `supported`、原科学reviewedAt `2026-10-16T05:11:05+00:00`、既有身份绑定时间 `None`全部保留；本审阅不替换日期。
只读hydrate：pageIdentity `confirmed`，acceptance `accepted_lab_group`，canCount `True`。
packet SHA `045a165e809fe1be2eb24a62c23a40cf7f4c109bb11792625f53427e10040b36`；raw SHA `9200ad811d967069840a01f9fb0eb1b6febb4ed7f4b38581e60e4a3abd7f6bf7`；本条审阅 `2026-10-16T05:17:36+00:00`。

原文引用只支持各自明确的标签。方法均有实际方法原文；Stauber future/potential及Ferguson治疗目标限制保留。隶属仅自述机构文本且不宣称日期未给出的现时任职；正文捕获日期不等于内容更新日期。
