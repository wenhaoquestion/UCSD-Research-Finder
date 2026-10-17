# Remaining original URI scope review — indices 24–34

Metadata review completed 2026-10-16T04:37:40+00:00; 11 records, zero requests, zero HTML/scientific-body reads, zero record/packet changes. **8 original HTTP route-check candidates; 3 deferred for specific cap/DNS blockers.**

All 11 literal HTTP URLs and stable IDs match baseline `data/research-atlas.json` SHA256 `ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e`, the manifest and current packets. Current actual request metadata and original timestamps match the read-only collector queue snapshot `2026-10-16T04:37:27+00:00` (SHA256 `f160d02bd53277309b8909820e5462be3f7bb58d9a29aff7ddc941c893e13af6`). All current actual addresses are HTTPS; no actual original-HTTP page request was found in stored queue/own-gap capture metadata. Undated historical websiteCheck fields are not fresh page-request proof.

This review admits only proposed route-check scope. It does not execute checks, confirm a lab identity, promote a partial record, change accepted canonical URLs, apply aliases, or relax the 13 mismatch gates.

For each candidate: start with the exact baseline HTTP URI and its HTTP-origin robots under the shared v2 gate. Reused HTTPS robots does not authorize HTTP. Keep existing cooldown/retry limits and the 2,000,000-byte page cap; do not disable TLS, log in, bypass robots/challenges, split a large body, or raise the cap. Every actual HTTPS redirect remains subject to normal TLS and robots checks. Retain actual request/final URI/time/redirect evidence, including the possibility of no redirect. A metadata-review timestamp is not a source observation.

Kim/Tezcan are distinct protocol/port cases: existing HTTPS TLS/443 failures remain explicit blockers if an actual route reaches HTTPS, but do not establish an original-HTTP result. Stauber/Ferguson retain the cap blocker under the current full-body adapter; no claim is made that their unrequested HTTP response has the same size. Saygin has repeated host DNS failure, so an immediate scheme-only repeat offers no new basis for success.

## 24 · ordinal 694 · ucsd-chemistry-biochemistry-lab-jennings-lab

Decision: `candidate_once_original_literal_http`. baseline原地址明确为HTTP；最新HTTPS页面200且robots checked，无访问边界错误。可仅为补齐原URI路由证据检查一次HTTP原地址；raw仍partial，正文不足与身份未知不会因此自动解决。

Baseline literal: [http://jenningslab.ucsd.edu](http://jenningslab.ucsd.edu); actual checked `https://jenningslab.ucsd.edu/`; observedAt `2026-10-16T01:07:09+00:00`; final `https://jenningslab.ucsd.edu/`; status `ok`; page HTTP status `200`; error ``.
Robots: `https://jenningslab.ucsd.edu/robots.txt`, observedAt `2026-10-16T01:07:08+00:00`, status `checked`, HTTP `200`, attempts `not serialized`, error ``.
Raw remains `partial`; existing blockers: ["目标提取正文为空；仅负责人宽泛研究领域。"].
Destination source metadata: `src-5d1996b644f76fc1` (https://jenningslab.ucsd.edu/, 2026-10-16T01:07:09+00:00, SHA `67f95d3c0b382d5be686b78781e693f00d42ccc881c40b3a6e987be872d29afa`).
Metadata provenance: `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/packets/ucsd-chemistry-biochemistry-lab-jennings-lab.json` → `latestDestinationFetch`, exact queue `https://jenningslab.ucsd.edu/` → `fetch`; `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/records/ucsd-chemistry-biochemistry-lab-jennings-lab.json` status/blockers; baseline `/labs/694/labWebsiteUrl`. Actual reviewedAt `2026-10-16T04:37:36+00:00`; metadataOnly=true; requests=0.

## 25 · ordinal 695 · ucsd-chemistry-biochemistry-lab-kim-group-judy-kim

Decision: `candidate_once_original_literal_http`. baseline原HTTP地址未检查；旧失败发生在HTTPS robots证书验证（curl60），只证明443/TLS前置检查失败。可检查一次既存HTTP原地址及其HTTP robots，不禁用TLS；若实际跳转HTTPS则保留并遵守原证书失败边界。

Baseline literal: [http://galileo.ucsd.edu](http://galileo.ucsd.edu); actual checked `https://galileo.ucsd.edu/`; observedAt `2026-10-16T01:07:09+00:00`; final `None`; status `robots_unavailable`; page HTTP status `None`; error ``.
Robots: `https://galileo.ucsd.edu/robots.txt`, observedAt `2026-10-16T01:07:09+00:00`, status `unavailable`, HTTP `0`, attempts `not serialized`, error `curl: (60) SSL certificate problem: unable to get local issuer certificate More details here: https://curl.se/docs/sslcerts.html curl failed to verify the legitimacy of the server and therefore could not establish a secu`.
Raw remains `unresolved`; existing blockers: ["目标 robots 获取失败；只有个人宽泛学科领域。"].
No successful destination-body source is available for this failed/precheck capture; no body identity/research acceptance is inferred.
Retain: HTTPS robots TLS certificate verification failed: curl60 unable to get local issuer certificate; retain if actual route reaches HTTPS.
Metadata provenance: `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/packets/ucsd-chemistry-biochemistry-lab-kim-group-judy-kim.json` → `latestDestinationFetch`, exact queue `https://galileo.ucsd.edu/` → `fetch`; `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/records/ucsd-chemistry-biochemistry-lab-kim-group-judy-kim.json` status/blockers; baseline `/labs/695/labWebsiteUrl`. Actual reviewedAt `2026-10-16T04:37:37+00:00`; metadataOnly=true; requests=0.

## 26 · ordinal 697 · ucsd-chemistry-biochemistry-lab-kummel-lab

Decision: `candidate_once_original_literal_http`. baseline原地址明确为HTTP；最新HTTPS200且robots checked，无阻止一次原URI路由检查的访问错误。raw实验室身份确认但科研仍partial，本候选不提升科研接受。

Baseline literal: [http://kummelgroup.ucsd.edu](http://kummelgroup.ucsd.edu); actual checked `https://kummelgroup.ucsd.edu/`; observedAt `2026-10-16T01:07:10+00:00`; final `https://kummelgroup.ucsd.edu/`; status `ok`; page HTTP status `200`; error ``.
Robots: `https://kummelgroup.ucsd.edu/robots.txt`, observedAt `2026-10-16T01:07:09+00:00`, status `checked`, HTTP `200`, attempts `not serialized`, error ``.
Raw remains `partial`; existing blockers: ["实验室首页只有欢迎语；负责人资料仅列宽泛领域。"].
Destination source metadata: `src-2ebd0459514d0d6f` (https://kummelgroup.ucsd.edu/, 2026-10-16T01:07:10+00:00, SHA `568e6a760a2416fb3ac385f66df55208453b3ee8dc9669415c8f4213f8effeeb`).
Metadata provenance: `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/packets/ucsd-chemistry-biochemistry-lab-kummel-lab.json` → `latestDestinationFetch`, exact queue `https://kummelgroup.ucsd.edu/` → `fetch`; `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/records/ucsd-chemistry-biochemistry-lab-kummel-lab.json` status/blockers; baseline `/labs/697/labWebsiteUrl`. Actual reviewedAt `2026-10-16T04:37:37+00:00`; metadataOnly=true; requests=0.

## 27 · ordinal 705 · ucsd-chemistry-biochemistry-lab-romero-research-group-erik-romero

Decision: `candidate_once_original_literal_http`. baseline原地址明确为HTTP；最新HTTPS200、robots404且无challenge/error。可按HTTP本源robots规则做一次原URI路由检查；首页名称/动画与科研partial问题不在本次接受范围。

Baseline literal: [http://r2g.ucsd.edu](http://r2g.ucsd.edu); actual checked `https://r2g.ucsd.edu/`; observedAt `2026-10-16T01:07:13+00:00`; final `https://r2g.ucsd.edu/`; status `ok`; page HTTP status `200`; error ``.
Robots: `https://r2g.ucsd.edu/robots.txt`, observedAt `2026-10-16T01:07:12+00:00`, status `not_found`, HTTP `404`, attempts `not serialized`, error ``.
Raw remains `partial`; existing blockers: ["首页只有名称；教师资料只有宽泛研究领域。"].
Destination source metadata: `src-16348f4142c7262a` (https://r2g.ucsd.edu/, 2026-10-16T01:07:13+00:00, SHA `25c774bbc43f61f0d282c3cd44b9a1f796bf24ba6e44c3a00b0aed43d355b707`).
Metadata provenance: `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/packets/ucsd-chemistry-biochemistry-lab-romero-research-group-erik-romero.json` → `latestDestinationFetch`, exact queue `https://r2g.ucsd.edu/` → `fetch`; `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/records/ucsd-chemistry-biochemistry-lab-romero-research-group-erik-romero.json` status/blockers; baseline `/labs/705/labWebsiteUrl`. Actual reviewedAt `2026-10-16T04:37:37+00:00`; metadataOnly=true; requests=0.

## 28 · ordinal 708 · ucsd-chemistry-biochemistry-lab-stauber-lab

Decision: `defer_concrete_blocker`. 既有同host/effective-path的HTTPS页面HTTP200但curl63 Maximum file size exceeded，未形成可用正文。建议保留2MB cap具体阻塞，当前完整正文抓取适配器不再重复该主机正文获取；原HTTP仍未实测，不能声称其响应也已超限。不得提高cap、分块拼接或改用无限大小抓取。

Baseline literal: [http://stauberlab.ucsd.edu/](http://stauberlab.ucsd.edu/); actual checked `https://stauberlab.ucsd.edu/`; observedAt `2026-10-16T01:10:16+00:00`; final `https://stauberlab.ucsd.edu/`; status `fetch_error`; page HTTP status `200`; error `curl: (63) Maximum file size exceeded`.
Robots: `https://stauberlab.ucsd.edu/robots.txt`, observedAt `2026-10-16T01:07:14+00:00`, status `not_found`, HTTP `404`, attempts `not serialized`, error ``.
Raw remains `unresolved`; existing blockers: ["目标 fetch_error；无实验室研究正文。"].
No successful destination-body source is available for this failed/precheck capture; no body identity/research acceptance is inferred.
Retain: HTTPS page httpStatus=200 with curl63 Maximum file size exceeded; 2,000,000-byte cap remains binding; no usable captured body.
Metadata provenance: `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/packets/ucsd-chemistry-biochemistry-lab-stauber-lab.json` → `latestDestinationFetch`, exact queue `https://stauberlab.ucsd.edu/` → `fetch`; `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/records/ucsd-chemistry-biochemistry-lab-stauber-lab.json` status/blockers; baseline `/labs/708/labWebsiteUrl`. Actual reviewedAt `2026-10-16T04:37:38+00:00`; metadataOnly=true; requests=0.

## 29 · ordinal 709 · ucsd-chemistry-biochemistry-lab-tezcan-lab

Decision: `candidate_once_original_literal_http`. baseline原HTTP未实测；HTTPS robots已有3次curl7连接443失败，未发页面请求。端口443失败不证明端口80结果，可仅一次检查原HTTP及本源robots；保留HTTPS三次失败/冷却历史，若回跳HTTPS仍受现有边界与重试上限约束。

Baseline literal: [http://tezcan.ucsd.edu](http://tezcan.ucsd.edu); actual checked `https://tezcan.ucsd.edu/`; observedAt `2026-10-16T03:49:28+00:00`; final `None`; status `robots_unavailable`; page HTTP status `None`; error ``.
Robots: `https://tezcan.ucsd.edu/robots.txt`, observedAt `2026-10-16T03:49:28+00:00`, status `unavailable`, HTTP `0`, attempts `3`, error `curl: (7) Failed to connect to tezcan.ucsd.edu port 443 after 42 ms: Couldn't connect to server`.
Raw remains `unresolved`; existing blockers: ["目标 robots 获取失败；无实验室研究正文。"].
No successful destination-body source is available for this failed/precheck capture; no body identity/research acceptance is inferred.
Retain: HTTPS robots curl7 failed to connect port443, attempts=3; no page request; preserve original retry history/cooldown.
Metadata provenance: `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/packets/ucsd-chemistry-biochemistry-lab-tezcan-lab.json` → `latestDestinationFetch`, exact queue `https://tezcan.ucsd.edu/` → `fetch`; `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/records/ucsd-chemistry-biochemistry-lab-tezcan-lab.json` status/blockers; baseline `/labs/709/labWebsiteUrl`. Actual reviewedAt `2026-10-16T04:37:38+00:00`; metadataOnly=true; requests=0.

## 30 · ordinal 710 · ucsd-chemistry-biochemistry-lab-theodorakis-group

Decision: `candidate_once_original_literal_http`. baseline原地址明确为HTTP；HTTPS根200、robots404且无challenge/error，原HTTP仍未知。可做一次原URI路由检查；此前研究正文接受不替代此根地址的身份/地址绑定。

Baseline literal: [http://theodorakisgroup.ucsd.edu](http://theodorakisgroup.ucsd.edu); actual checked `https://theodorakisgroup.ucsd.edu/`; observedAt `2026-10-16T01:07:15+00:00`; final `https://theodorakisgroup.ucsd.edu/`; status `ok`; page HTTP status `200`; error ``.
Robots: `https://theodorakisgroup.ucsd.edu/robots.txt`, observedAt `2026-10-16T01:07:14+00:00`, status `not_found`, HTTP `404`, attempts `not serialized`, error ``.
Raw remains `supported`; existing blockers: [].
Destination source metadata: `src-c6710d54f8990201` (https://theodorakisgroup.ucsd.edu/, 2026-10-16T01:07:15+00:00, SHA `c68cda4ff35c8c0f979ca06faff6004917a86f963ad92ca4484b9e07e5654a23`).
Metadata provenance: `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/packets/ucsd-chemistry-biochemistry-lab-theodorakis-group.json` → `latestDestinationFetch`, exact queue `https://theodorakisgroup.ucsd.edu/` → `fetch`; `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/records/ucsd-chemistry-biochemistry-lab-theodorakis-group.json` status/blockers; baseline `/labs/710/labWebsiteUrl`. Actual reviewedAt `2026-10-16T04:37:38+00:00`; metadataOnly=true; requests=0.

## 31 · ordinal 720 · ucsd-biochemistry-and-molecular-biophysics-lab-ferguson-lab-fleur-ferguson

Decision: `defer_concrete_blocker`. 既有同host/effective-path的HTTPS页面HTTP200但curl63 Maximum file size exceeded，未保存有效正文SHA。建议保留2MB cap具体阻塞并暂不重复完整正文获取；原HTTP结果仍未知，不能推断HTTP已超限或以提高cap消除该阻塞。

Baseline literal: [http://fergusonlab.ucsd.edu](http://fergusonlab.ucsd.edu); actual checked `https://fergusonlab.ucsd.edu/`; observedAt `2026-10-16T01:09:15+00:00`; final `https://fergusonlab.ucsd.edu/`; status `fetch_error`; page HTTP status `200`; error `curl: (63) Maximum file size exceeded`.
Robots: `https://fergusonlab.ucsd.edu/robots.txt`, observedAt `2026-10-16T01:06:13+00:00`, status `not_found`, HTTP `404`, attempts `not serialized`, error ``.
Raw remains `unresolved`; existing blockers: ["目标 fetch_error；无实验室研究正文。"].
No successful destination-body source is available for this failed/precheck capture; no body identity/research acceptance is inferred.
Retain: HTTPS page httpStatus=200 with curl63 Maximum file size exceeded; 2,000,000-byte cap remains binding; no usable captured body.
Metadata provenance: `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/packets/ucsd-biochemistry-and-molecular-biophysics-lab-ferguson-lab-fleur-ferguson.json` → `latestDestinationFetch`, exact queue `https://fergusonlab.ucsd.edu/` → `fetch`; `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/records/ucsd-biochemistry-and-molecular-biophysics-lab-ferguson-lab-fleur-ferguson.json` status/blockers; baseline `/labs/720/labWebsiteUrl`. Actual reviewedAt `2026-10-16T04:37:39+00:00`; metadataOnly=true; requests=0.

## 32 · ordinal 824 · ucsd-structural-engineering-lab-ucsd-structural-health-monitoring-shm-group

Decision: `candidate_once_original_literal_http`. baseline literal root是http://shm.ucsd.edu/，HTTPS根200且robots404无错误，可一次检查原root。historicalWebsiteCheck的/Site/Home.html以及缓存HTML meta-refresh只是另一路径/导航，不是本轮root的HTTPredirect，不能先替换原root。

Baseline literal: [http://shm.ucsd.edu/](http://shm.ucsd.edu/); actual checked `https://shm.ucsd.edu/`; observedAt `2026-10-16T01:00:47+00:00`; final `https://shm.ucsd.edu/`; status `ok`; page HTTP status `200`; error ``.
Robots: `https://shm.ucsd.edu/robots.txt`, observedAt `2026-10-16T01:00:46+00:00`, status `not_found`, HTTP `404`, attempts `not serialized`, error ``.
Raw remains `partial`; existing blockers: ["目标HTTP200但提取正文为空；缺少研究组研究内容。"].
Destination source metadata: `src-a7325ccd6938272b` (https://shm.ucsd.edu/, 2026-10-16T01:00:47+00:00, SHA `3f8230dc8b243bf8ee4d8fde603d812f6935f9425e972e3495057c525bbbb5c5`).
Metadata provenance: `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/packets/ucsd-structural-engineering-lab-ucsd-structural-health-monitoring-shm-group.json` → `latestDestinationFetch`, exact queue `https://shm.ucsd.edu/` → `fetch`; `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/records/ucsd-structural-engineering-lab-ucsd-structural-health-monitoring-shm-group.json` status/blockers; baseline `/labs/824/labWebsiteUrl`. Actual reviewedAt `2026-10-16T04:37:39+00:00`; metadataOnly=true; requests=0.

## 33 · ordinal 825 · ucsd-structural-engineering-lab-multifunctional-materials-research-laboratory-mmrl

Decision: `candidate_once_original_literal_http`. baseline原HTTP明确且未实测；HTTPS根200、robots404无错误，可一次原URI路由检查。MMRL科研partial与个人首页范围问题仍保留，本次元数据审阅不接受实体或研究。

Baseline literal: [http://mmrl.ucsd.edu/](http://mmrl.ucsd.edu/); actual checked `https://mmrl.ucsd.edu/`; observedAt `2026-10-16T01:00:48+00:00`; final `https://mmrl.ucsd.edu/`; status `ok`; page HTTP status `200`; error ``.
Robots: `https://mmrl.ucsd.edu/robots.txt`, observedAt `2026-10-16T01:00:47+00:00`, status `not_found`, HTTP `404`, attempts `not serialized`, error ``.
Raw remains `partial`; existing blockers: ["页面只有领域列表及履历，具体实验室研究问题未展开。"].
Destination source metadata: `src-dce22ffee9c6fa41` (https://mmrl.ucsd.edu/, 2026-10-16T01:00:48+00:00, SHA `9eeb38742f2f5d6b90b866022f7af2024241a4ff6c7fca6d69b1b3b5972f34b7`).
Metadata provenance: `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/packets/ucsd-structural-engineering-lab-multifunctional-materials-research-laboratory-mmrl.json` → `latestDestinationFetch`, exact queue `https://mmrl.ucsd.edu/` → `fetch`; `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/records/ucsd-structural-engineering-lab-multifunctional-materials-research-laboratory-mmrl.json` status/blockers; baseline `/labs/825/labWebsiteUrl`. Actual reviewedAt `2026-10-16T04:37:39+00:00`; metadataOnly=true; requests=0.

## 34 · ordinal 861 · ucsd-cognitive-science-lab-cognitive-neuroscience-and-neuropsychology-lab

Decision: `defer_concrete_blocker`. 相同hostname的HTTPS robots在3次尝试中均curl6 Could not resolve host。DNS解析发生于协议/端口连接之前；建议保留host DNS blocker并避免立刻用HTTP对同host再作无益获取。原HTTP未请求；需实际DNS恢复或其他新证据再重新审阅，不推断网站关闭。

Baseline literal: [http://sayginlab.ucsd.edu/](http://sayginlab.ucsd.edu/); actual checked `https://sayginlab.ucsd.edu/`; observedAt `2026-10-16T03:49:47+00:00`; final `None`; status `robots_unavailable`; page HTTP status `None`; error ``.
Robots: `https://sayginlab.ucsd.edu/robots.txt`, observedAt `2026-10-16T03:49:47+00:00`, status `unavailable`, HTTP `0`, attempts `3`, error `curl: (6) Could not resolve host: sayginlab.ucsd.edu`.
Raw remains `unresolved`; existing blockers: ["https://sayginlab.ucsd.edu/robots.txt: curl (6) Could not resolve host；目的页请求因robots不可核验而停止。", "恢复的官方教师简介未将所列研究兴趣明确归于Cognitive Neuroscience and Neuropsychology Lab，仍缺少对应实验室研究正文。"].
No successful destination-body source is available for this failed/precheck capture; no body identity/research acceptance is inferred.
Retain: Same-host robots DNS resolution failed curl6 on all three recorded attempts; defer immediate HTTP repeat until new DNS recovery evidence.
Metadata provenance: `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/packets/ucsd-cognitive-science-lab-cognitive-neuroscience-and-neuropsychology-lab.json` → `latestDestinationFetch`, exact queue `https://sayginlab.ucsd.edu/` → `fetch`; `/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/records/ucsd-cognitive-science-lab-cognitive-neuroscience-and-neuropsychology-lab.json` status/blockers; baseline `/labs/861/labWebsiteUrl`. Actual reviewedAt `2026-10-16T04:37:39+00:00`; metadataOnly=true; requests=0.
