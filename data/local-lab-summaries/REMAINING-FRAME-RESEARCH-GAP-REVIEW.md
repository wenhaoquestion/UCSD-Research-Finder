# 残余frame/科研链接缺口审阅

审阅完成：2026-10-16T05:05:32+00:00。**0网络请求；仅新增本报告及同名JSON。**

**建议四个有限新目标，不重试原根：Jennings `research.html`；Kummel 主frame `home.htm`及导航frame `side.htm`；SHM `Site/Home.html`。** 当前没有这些目标的queue/gap捕获、尝试或HTTP/HTTPS精确缓存文件；没有明确访问拒绝记录。目标可读性/实体/研究仍未知，须正常访问规则及后续正文审阅。

另外Jennings `researchteam.html` 是真实可选身份链接，先延期，待Research页仍不能说明实体时再单独决定。MMRL没有可推荐的同站frame/main/research路径；不从个人档案或论文拼凑实验室研究。

## 四根逐项依据

### Jennings · ucsd-chemistry-biochemistry-lab-jennings-lab

- 原HTTP源 `src-28f455c9c1ad8216`：<http://jenningslab.ucsd.edu/>；observedAt `2026-10-16T04:57:02+00:00`；SHA `67f95d3c0b382d5be686b78781e693f00d42ccc881c40b3a6e987be872d29afa`。
- 实际Research锚点没有可见文字也没有image alt；class=research_button、href=research.html和flask图像仅用于发现，不能当研究内容。优先只读research.html；不请求图片/CSS/script，不因空首页重试根。
- **recommend_finite_followup**：`<a class="research_button" href="research.html" >` → <http://jenningslab.ucsd.edu/research.html>；request_key `['http', 'jenningslab.ucsd.edu', None, '/research.html', '']`。
  robots：<http://jenningslab.ucsd.edu/robots.txt>，原时间 `2026-10-16T04:57:01+00:00`，`checked_rules`；目标无已有捕获/尝试或拒绝。
  图片属性：[{"src": "Images/flask.png", "alt": null, "altAttributePresent": false, "attrs": {"class": "nav_img", "src": "Images/flask.png", "height": "90", "width": "70"}}]；无alt文本，不把图像当科研证据。
- **defer_until_research_page_identity_insufficient**：`<a class="people_button" href="researchteam.html" >` → <http://jenningslab.ucsd.edu/researchteam.html>；request_key `['http', 'jenningslab.ucsd.edu', None, '/researchteam.html', '']`。
  robots：<http://jenningslab.ucsd.edu/robots.txt>，原时间 `2026-10-16T04:57:01+00:00`，`checked_rules`；目标无已有捕获/尝试或拒绝。
  图片属性：[{"src": "Images/people_button.png", "alt": null, "altAttributePresent": false, "attrs": {"class": "people_nav_img", "src": "Images/people_button.png", "height": "50", "width": "110"}}]；无alt文本，不把图像当科研证据。
- 旧cached69 inventory该条candidates为空，未分派到69个非空审阅；旧ADDITIONAL与cached报告没有该ID/hostname的目标条目。这里是新actual HTML属性核验，不是重试已拒目标。
- 原raw仍为 `partial`，科学reviewedAt `2026-10-16T01:48:38+00:00`；未修改。

### Kummel · ucsd-chemistry-biochemistry-lab-kummel-lab

- 原HTTP源 `src-4eed6cd432ff1acd`：<http://kummelgroup.ucsd.edu/>；observedAt `2026-10-16T04:57:05+00:00`；SHA `568e6a760a2416fb3ac385f66df55208453b3ee8dc9669415c8f4213f8effeeb`。
- 根页实际frameset指定main=home.htm、side=side.htm；main是展示正文候选，side只用于取得真实导航。当前没有Research href，不能凭习惯发明research.htm等路径；不得把frame当HTTP redirect。
- **recommend_finite_followup**：`<frame src="home.htm" name="main" frameborder="NO">` → <http://kummelgroup.ucsd.edu/home.htm>；request_key `['http', 'kummelgroup.ucsd.edu', None, '/home.htm', '']`。
  robots：<http://kummelgroup.ucsd.edu/robots.txt>，原时间 `2026-10-16T04:57:04+00:00`，`checked_rules`；目标无已有捕获/尝试或拒绝。
- **recommend_finite_followup_discovery_only**：`<frame src="side.htm" name="side" frameborder="NO">` → <http://kummelgroup.ucsd.edu/side.htm>；request_key `['http', 'kummelgroup.ucsd.edu', None, '/side.htm', '']`。
  robots：<http://kummelgroup.ucsd.edu/robots.txt>，原时间 `2026-10-16T04:57:04+00:00`，`checked_rules`；目标无已有捕获/尝试或拒绝。
- 旧cached69 inventory该条candidates为空，未分派到69个非空审阅；旧ADDITIONAL与cached报告没有该ID/hostname的目标条目。这里是新actual HTML属性核验，不是重试已拒目标。
- 原raw仍为 `partial`，科学reviewedAt `2026-10-16T01:48:38+00:00`；未修改。

### SHM · ucsd-structural-engineering-lab-ucsd-structural-health-monitoring-shm-group

- 原HTTP源 `src-78fc5f4fd64950d0`：<http://shm.ucsd.edu/>；observedAt `2026-10-16T04:57:37+00:00`；SHA `3f8230dc8b243bf8ee4d8fde603d812f6935f9425e972e3495057c525bbbb5c5`。
- 实际字面meta给出同host /Site/Home.html，根HTTP本身200无redirect。Home仅为待观察的展示内容，不能视为已有研究组身份或科研；绝不改写原根HTTP链。
- **recommend_finite_followup**：`<meta http-equiv="refresh" content="0;url= http://shm.ucsd.edu/Site/Home.html" />` → <http://shm.ucsd.edu/Site/Home.html>；request_key `['http', 'shm.ucsd.edu', None, '/Site/Home.html', '']`。
  robots：<http://shm.ucsd.edu/robots.txt>，原时间 `2026-10-16T04:57:36+00:00`，`not_found_no_explicit_refusal_under_existing_fetcher_policy`；目标无已有捕获/尝试或拒绝。
- 旧cached69 inventory该条candidates为空，未分派到69个非空审阅；旧ADDITIONAL与cached报告没有该ID/hostname的目标条目。这里是新actual HTML属性核验，不是重试已拒目标。
- 原raw仍为 `partial`，科学reviewedAt `2026-10-16T01:53:25+00:00`；未修改。

### MMRL · ucsd-structural-engineering-lab-multifunctional-materials-research-laboratory-mmrl

- 原HTTP源 `src-3bf96383b726f054`：<http://mmrl.ucsd.edu/>；observedAt `2026-10-16T04:57:39+00:00`；SHA `9eeb38742f2f5d6b90b866022f7af2024241a4ff6c7fca6d69b1b3b5972f34b7`。
- 没有frame/iframe/refresh或同站Research锚点。当前正文是Yu Qiao联系/履历、Research Interests列表及Selected Publications；方法不能从单篇论文标题推断。两个here链接是跨host个人档案，机构主页/邮箱/论文均不自动扩张为实验室研究路径。
- 实际here链接的[Yu Qiao Jacobs档案](https://jacobsschool.ucsd.edu/faculty/profile?id=256)已有缓存：2026-10-16T01:01:33+00:00，SHA `c156e786ed14a1b8db5f1c78e52312b55b82bdb3940688520e0c99af814d19fe`，全文936字符已读。只列个人宽泛领域和履历，未给出具名whole-lab研究问题/方法；无需为此再请求，也不据它升级实验室科研。
- 另一MATS Yu Qiao个人档案未捕获，但跨host个人资料不是本次frame/research缺口所必需，暂不推荐新请求。机构主页、mailto与5篇单篇论文链接均不作科研扩展路径。
- 旧cached69 inventory该条candidates为空，未分派到69个非空审阅；旧ADDITIONAL与cached报告没有该ID/hostname的目标条目。这里是新actual HTML属性核验，不是重试已拒目标。
- 原raw仍为 `partial`，科学reviewedAt `2026-10-16T01:54:02+00:00`；未修改。

## 访问边界与审计范围

- Jennings/Kummel HTTP robots为实际200 `User-agent: * / Disallow:` 空拒绝，已按目标路径解析允许。SHM实际HTTP robots404，error为空且无challenge；按既有fetcher的not_found规则处理，不能把404正文当有效robots规则或目标成功证明。原robots时间/hash保存在JSON。
- HTML frame/src和meta/content仅用于发现；四个原HTTP根都实际200、没有HTTPredirect链。不得将frame/meta写入根redirect或采纳canonical/alias。
- 每目标均按actual final HTTP根解析，精确request_key保留协议/host/path大小写/query；对HTTPS同路径的缓存探测仅用于查已有证据，不发明后备请求URL。
- 后续若由父代理安排，保留robots、auth/challenge、正常TLS、v2共享gate/cooldown/Retry-After、2MB page和300KB robots规则；不从导航/按钮/个人领域/单篇论文推断研究。
- 仅本Markdown/JSON写入；无code、raw、packet、receipt、collector/shared写入。根body、raw、packet SHA最终复核未变。
