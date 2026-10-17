# Remaining original-URI scope review — indices 12–23

Actual review completed `2026-10-16T04:37:59+00:00`. **12/12 route-only candidates allowed for one finite original-URI public check**; **0** excluded by an existing access boundary in these metadata. This review made **0 network requests** and read **metadata only**. No raw, packet, scientific conclusion, code, collector or shared state was changed.

Each stable ID and exact original HTTP URI was verified against the pinned baseline atlas (SHA-256 `ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e`) and current packet. All 12 related current captures are the same host/effective path and query with only HTTP/HTTPS scheme difference. No current-round original HTTP source URI, observed redirect `from` hop, or exact page wire event was found in the collector queue and summary ledger. The baseline already contains older original-URI checks: those historical checks are preserved below and are **not** replaced by current-round dates or described as never having existed.

Admission concerns only the literal request route. It does not imply lab identity acceptance; personal sites, facilities, partial/unresolved entities and all 13 mismatch acceptance gates stay unchanged.

Conditions for any later dispatcher:

- Check only the baseline literal HTTP URI, preserving scheme/www/path/query; no invented protocol variants, aliases or alternate research paths.
- Evaluate the original HTTP-origin robots rules first using the existing fetcher; a cached HTTPS success or robots result is not permission to skip this boundary.
- Use the existing shared fcntl-host-clock-v2 gate for every robots, page and observed HTTP redirect transport, retaining host timing, Retry-After and cooldown policy.
- Retain normal HTTPS TLS verification on every observed redirect, including Sinha; stop on certificate failure, never use insecure TLS or a substitute route.
- Retain the existing 2,000,000-byte response cap, 300,000-byte robots cap, bounded redirect counts and existing timeouts; do not raise limits or add retries to overcome an error.
- Stop on robots denial/unavailability, authentication, login target or access challenge; no login or bypass. HTML meta refresh does not become an observed HTTP redirect.
- Eligibility is request-scope-only: do not change stable ID, summary, entity type, acceptance, canonical identity or any of the 13 mismatch gates. Any returned identity or research prose requires separate model review.

## 12 — ucsd-physics-research-site-frank-wuerthwein

Decision `allow_single_original_uri_public_check`; actual metadata review `2026-10-16T04:37:58+00:00`.
Original literal baseline URI: [http://www.t2.ucsd.edu/twiki2/bin/view/HEPProjects/FkwsGroup](http://www.t2.ucsd.edu/twiki2/bin/view/HEPProjects/FkwsGroup).
Current actual related URI `https://www.t2.ucsd.edu/twiki2/bin/view/HEPProjects/FkwsGroup`; original capture `2026-10-16T01:05:23+00:00`; status `http_error`; HTTP `404`; final `https://www.t2.ucsd.edu/twiki2/bin/view/HEPProjects/FkwsGroup`; body SHA `None` (null means no successful hashed body, not a fabricated digest).
Original metadata: `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json` → item key `https://www.t2.ucsd.edu/twiki2/bin/view/HEPProjects/FkwsGroup`. Current packet/raw hashes and full robots/error metadata are retained in JSON.
Baseline historical websiteCheck: `{"sourceUrl": "http://www.t2.ucsd.edu/twiki2/bin/view/HEPProjects/FkwsGroup", "status": "http_error", "observedAt": "2026-10-03T00:04:04+00:00", "httpStatus": 404}`.

baseline 原文明确保存该 HTTP TWiki 组页 URI，当前只请求了同主机同路径 HTTPS，返回 404；这不是登录、robots 拒绝或 challenge。可安排一次原 URI 公共检查，仍须先执行该 HTTP origin 的 robots 检查；404 或新的身份占位内容不得当作实验室关闭或接受依据。

Existing status/entity/acceptance retained: `unresolved` / `unconfirmed` / `provisional_or_unresolved`.
Original HTTP-origin robots `http://www.t2.ucsd.edu/robots.txt`: no cached explicit denial; normal robots evaluation remains required before any page request.
Assessment fingerprint `3ca9927bef7342f8f8ddf5b7bd4fb3c8af3ed609f0746a99ce9c0cd418ad847a`.

## 13 — ucsd-physics-research-site-john-m-goodkind

Decision `allow_single_original_uri_public_check`; actual metadata review `2026-10-16T04:37:58+00:00`.
Original literal baseline URI: [http://physics.ucsd.edu/research/condensed_matter/](http://physics.ucsd.edu/research/condensed_matter/).
Current actual related URI `https://physics.ucsd.edu/research/condensed_matter/`; original capture `2026-10-16T01:05:23+00:00`; status `http_error`; HTTP `404`; final `https://physics.ucsd.edu/research/condensed_matter/`; body SHA `None` (null means no successful hashed body, not a fabricated digest).
Original metadata: `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json` → item key `https://physics.ucsd.edu/research/condensed_matter`. Current packet/raw hashes and full robots/error metadata are retained in JSON.
Baseline historical websiteCheck: `{"sourceUrl": "http://physics.ucsd.edu/research/condensed_matter/", "status": "http_error", "observedAt": "2026-10-03T00:04:04+00:00", "httpStatus": 404}`.

baseline 原文 HTTP 地址和本轮 HTTPS 地址同主机同路径；本轮 HTTPS 是 404，没有已知访问控制边界。允许一次原地址 route-only 检查以补本轮请求范围；该路径属于 condensed_matter 区域，即使可达也不能自动确认 Goodkind 研究组。

Existing status/entity/acceptance retained: `unresolved` / `unconfirmed` / `provisional_or_unresolved`.
Original HTTP-origin robots `http://physics.ucsd.edu/robots.txt`: no cached explicit denial; normal robots evaluation remains required before any page request.
Assessment fingerprint `0b303fe52b9c21c7f1b59b83efcbab8f5386034cb59dc30fcf202870ace614e2`.

## 14 — ucsd-physics-research-site-lu-j-sham

Decision `allow_single_original_uri_public_check`; actual metadata review `2026-10-16T04:37:58+00:00`.
Original literal baseline URI: [http://ljssst.physics.ucsd.edu](http://ljssst.physics.ucsd.edu).
Current actual related URI `https://ljssst.physics.ucsd.edu/`; original capture `2026-10-16T01:05:26+00:00`; status `ok`; HTTP `200`; final `https://ljssst.physics.ucsd.edu/`; body SHA `99836205cf76360ffd678ff2396e5e525a60a1ac04fb993c1be7ab95b6e0d569` (null means no successful hashed body, not a fabricated digest).
Original metadata: `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json` → item key `https://ljssst.physics.ucsd.edu/`. Current packet/raw hashes and full robots/error metadata are retained in JSON.
Baseline historical websiteCheck: `{"sourceUrl": "http://ljssst.physics.ucsd.edu", "status": "reachable", "observedAt": "2026-10-02T22:41:13+00:00", "httpStatus": 200, "finalUrl": "https://ljssst.physics.ucsd.edu/", "title": "UC San Diego Physics - Lu Jeu Sham - Professor of Physics"}`.

baseline 存储原 HTTP 根 URI，本轮只有 HTTPS 捕获；当前记录属于个人研究站而非已确认研究组。没有 robots 拒绝、登录、challenge、DNS 或大小上限错误，可安排一次原 URI 检查；个人站实体和 provisional 接受状态不因此改变。

Existing status/entity/acceptance retained: `partial` / `personal_research_site` / `provisional_or_unresolved`.
Original HTTP-origin robots `http://ljssst.physics.ucsd.edu/robots.txt`: no cached explicit denial; normal robots evaluation remains required before any page request.
Identity limit: Existing entity is a personal_research_site and remains provisional.
Assessment fingerprint `90abbbb6f73381fcfd60afd14e8f88a720fc5ae5e87ae0e518e5d8a136aa61d7`.

## 15 — ucsd-physics-research-site-shelley-wright

Decision `allow_single_original_uri_public_check`; actual metadata review `2026-10-16T04:37:58+00:00`.
Original literal baseline URI: [http://oirlab.ucsd.edu](http://oirlab.ucsd.edu).
Current actual related URI `https://oirlab.ucsd.edu/`; original capture `2026-10-16T01:05:27+00:00`; status `ok`; HTTP `200`; final `https://oirlab.ucsd.edu/`; body SHA `92a3b5a77991171ad13605f0665ae30437fea09d8cffce5d3c9d778e83b3ad68` (null means no successful hashed body, not a fabricated digest).
Original metadata: `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json` → item key `https://oirlab.ucsd.edu/`. Current packet/raw hashes and full robots/error metadata are retained in JSON.
Baseline historical websiteCheck: `{"sourceUrl": "http://oirlab.ucsd.edu", "status": "reachable", "observedAt": "2026-10-02T22:41:13+00:00", "httpStatus": 200, "finalUrl": "https://oirlab.ucsd.edu/", "title": "Redirecting..."}`.

baseline 原 HTTP OIR 根 URI 与当前 HTTPS 捕获只有协议差异；没有已知访问边界。可安排一次原 URI 检查，但该根页的旧标题是 Redirecting...、只记录 HTML meta refresh；不将它伪装为 HTTP 重定向，不把另页的团队身份引用自动绑定新根捕获。

Existing status/entity/acceptance retained: `supported` / `lab` / `accepted_lab_group`.
Original HTTP-origin robots `http://oirlab.ucsd.edu/robots.txt`: no cached explicit denial; normal robots evaluation remains required before any page request.
Identity limit: Latest root is a meta-refresh stub; accepted lab identity from separate team/about sources does not automatically confirm the root capture.
Assessment fingerprint `3991b0a61e5547a7b3f201a57a782dfe11f651846adf931e9bd1e7d521aa9a62`.

## 16 — ucsd-physics-research-site-sunil-k-sinha

Decision `allow_single_original_uri_public_check`; actual metadata review `2026-10-16T04:37:58+00:00`.
Original literal baseline URI: [http://sinhagroup.ucsd.edu/](http://sinhagroup.ucsd.edu/).
Current actual related URI `https://sinhagroup.ucsd.edu/`; original capture `2026-10-16T01:05:27+00:00`; status `robots_unavailable`; HTTP `None`; final `None`; body SHA `None` (null means no successful hashed body, not a fabricated digest).
Original metadata: `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json` → item key `https://sinhagroup.ucsd.edu/`. Current packet/raw hashes and full robots/error metadata are retained in JSON.
Baseline historical websiteCheck: `{"sourceUrl": "http://sinhagroup.ucsd.edu/", "status": "reachable", "observedAt": "2026-10-02T22:41:15+00:00", "httpStatus": 200, "finalUrl": "http://sinhagroup.ucsd.edu/", "title": "Allen Lab"}`.

原 HTTP URI 在 baseline 中确已存在，并非为绕过 HTTPS 错误临时生成。本轮仅 HTTPS robots 前置检查失败，错误为 certificate has expired，没有页面请求证明或显式 robots 拒绝。允许一次正常原 HTTP-origin robots 先行的有限检查；任何 HTTPS robots/page 跳转仍必须校验 TLS，证书错误必须停止，不许关闭 TLS 或改走其他临时地址。baseline 历史标题 Allen Lab 与 Sinha 列表名不同，须保留身份不确定性。

Existing status/entity/acceptance retained: `unresolved` / `unconfirmed` / `provisional_or_unresolved`.
Original HTTP-origin robots `http://sinhagroup.ucsd.edu/robots.txt`: no cached explicit denial; normal robots evaluation remains required before any page request.
Exact existing error: `curl: (60) SSL certificate problem: certificate has expired More details here: https://curl.se/docs/sslcerts.html curl failed to verify the legitimacy of the server and therefore could not establish a secure connection t`.
Identity limit: Historical baseline HTTP title Allen Lab differs from Sinha listed name; route eligibility provides no identity acceptance.
Assessment fingerprint `510af2872104b7d166012dd2bfacd212321f218db7186f1e962b45ec6301ce94`.

## 17 — ucsd-physics-research-site-thomas-m-o-neil

Decision `allow_single_original_uri_public_check`; actual metadata review `2026-10-16T04:37:58+00:00`.
Original literal baseline URI: [http://physics.ucsd.edu/research/plasma/](http://physics.ucsd.edu/research/plasma/).
Current actual related URI `https://physics.ucsd.edu/research/plasma/`; original capture `2026-10-16T01:05:28+00:00`; status `http_error`; HTTP `404`; final `https://physics.ucsd.edu/research/plasma/`; body SHA `None` (null means no successful hashed body, not a fabricated digest).
Original metadata: `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json` → item key `https://physics.ucsd.edu/research/plasma`. Current packet/raw hashes and full robots/error metadata are retained in JSON.
Baseline historical websiteCheck: `{"sourceUrl": "http://physics.ucsd.edu/research/plasma/", "status": "http_error", "observedAt": "2026-10-03T00:04:04+00:00", "httpStatus": 404}`.

baseline HTTP plasma 路径与本轮 HTTPS 实际请求同主机同路径，HTTPS 返回 404，不是访问控制拒绝。允许一次原 URI 的公开只读检查以补本轮请求范围；该路径是学科页，成功也不能自动确认 O'Neil 研究组。

Existing status/entity/acceptance retained: `unresolved` / `unconfirmed` / `provisional_or_unresolved`.
Original HTTP-origin robots `http://physics.ucsd.edu/robots.txt`: no cached explicit denial; normal robots evaluation remains required before any page request.
Assessment fingerprint `d35278db825e5a4a8b6a516cb454f36cf2f37ff2937d6b5f9fe4ea1515c31022`.

## 18 — ucsd-structural-engineering-lab-composite-structures-laboratory

Decision `allow_single_original_uri_public_check`; actual metadata review `2026-10-16T04:37:59+00:00`.
Original literal baseline URI: [http://se.ucsd.edu/facilities/composite-structures-laboratory](http://se.ucsd.edu/facilities/composite-structures-laboratory).
Current actual related URI `https://se.ucsd.edu/facilities/composite-structures-laboratory`; original capture `2026-10-16T01:06:10+00:00`; status `ok`; HTTP `200`; final `https://se.ucsd.edu/facilities/composite-structures-laboratory`; body SHA `d58101b63bec9b85ab3f6cc2d6f4caa6e4661a1451c66dcf34b2a9494d60687a` (null means no successful hashed body, not a fabricated digest).
Original metadata: `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json` → item key `https://se.ucsd.edu/facilities/composite-structures-laboratory`. Current packet/raw hashes and full robots/error metadata are retained in JSON.
Baseline historical websiteCheck: `{"sourceUrl": "http://se.ucsd.edu/facilities/composite-structures-laboratory", "status": "reachable", "observedAt": "2026-10-02T22:41:15+00:00", "httpStatus": 200, "finalUrl": "https://se.ucsd.edu/facilities/composite-structures-laboratory", "title": "Composite Structures Laboratory | Structural Engineering"}`.

原 HTTP facilities 路径在 baseline 中字面保存，目前仅有 HTTPS 捕获，后者无已知访问错误。允许一次原 URI 检查；实体仍是 facility，且当前只有设施描述、缺实验室科研问题，不能因 route 成功升级或计为研究组。

Existing status/entity/acceptance retained: `partial` / `facility` / `provisional_or_unresolved`.
Original HTTP-origin robots `http://se.ucsd.edu/robots.txt`: no cached explicit denial; normal robots evaluation remains required before any page request.
Identity limit: Facility classification must remain; request-scope evidence does not create an accepted lab/group.
Assessment fingerprint `0c3dccc1ef9c217f5340b4e6a7ac8fcbd2743656bf68e0a66e165a14344ddd7d`.

## 19 — ucsd-structural-engineering-lab-geotechnical-laboratories

Decision `allow_single_original_uri_public_check`; actual metadata review `2026-10-16T04:37:59+00:00`.
Original literal baseline URI: [http://se.ucsd.edu/facilities/geotechnical-facilities](http://se.ucsd.edu/facilities/geotechnical-facilities).
Current actual related URI `https://se.ucsd.edu/facilities/geotechnical-facilities`; original capture `2026-10-16T01:06:11+00:00`; status `ok`; HTTP `200`; final `https://se.ucsd.edu/facilities/geotechnical-facilities`; body SHA `6d8ce30f9f6487e3ea16241beab76cc6650ef046f0c5f41c18c8a3d923358676` (null means no successful hashed body, not a fabricated digest).
Original metadata: `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json` → item key `https://se.ucsd.edu/facilities/geotechnical-facilities`. Current packet/raw hashes and full robots/error metadata are retained in JSON.
Baseline historical websiteCheck: `{"sourceUrl": "http://se.ucsd.edu/facilities/geotechnical-facilities", "status": "reachable", "observedAt": "2026-10-02T22:41:15+00:00", "httpStatus": 200, "finalUrl": "https://se.ucsd.edu/facilities/geotechnical-facilities", "title": "Geotechnical Facilities | Structural Engineering"}`.

baseline 字面保存该 HTTP geotechnical facilities 路径，本轮只有同主机同路径 HTTPS 成功捕获且没有已知访问边界。允许一次原 URI 检查；保持 facility / source_supported_other_entity 分类，不自动加入 accepted lab/group。

Existing status/entity/acceptance retained: `supported` / `facility` / `source_supported_other_entity`.
Original HTTP-origin robots `http://se.ucsd.edu/robots.txt`: no cached explicit denial; normal robots evaluation remains required before any page request.
Identity limit: Facility classification must remain; request-scope evidence does not create an accepted lab/group.
Assessment fingerprint `b25bd02af59070ab2772ad9b4049d07a1411237fac4993174722eb45823b6ea8`.

## 20 — ucsd-structural-engineering-lab-srmd-laboratory

Decision `allow_single_original_uri_public_check`; actual metadata review `2026-10-16T04:37:59+00:00`.
Original literal baseline URI: [http://se.ucsd.edu/facilities/laboratory-listing/srmd](http://se.ucsd.edu/facilities/laboratory-listing/srmd).
Current actual related URI `https://se.ucsd.edu/facilities/laboratory-listing/srmd`; original capture `2026-10-16T01:06:12+00:00`; status `ok`; HTTP `200`; final `https://se.ucsd.edu/facilities/laboratory-listing/srmd`; body SHA `1c3fa24be16b9889fcb3458e26b8d84f8ca5046250dcf4b6c58ef9653cffb82a` (null means no successful hashed body, not a fabricated digest).
Original metadata: `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json` → item key `https://se.ucsd.edu/facilities/laboratory-listing/srmd`. Current packet/raw hashes and full robots/error metadata are retained in JSON.
Baseline historical websiteCheck: `{"sourceUrl": "http://se.ucsd.edu/facilities/laboratory-listing/srmd", "status": "reachable", "observedAt": "2026-10-02T22:41:15+00:00", "httpStatus": 200, "finalUrl": "https://se.ucsd.edu/facilities/laboratory-listing/srmd", "title": "Caltrans Seismic Response Modification Device (SRMD) Test Facility | Structural Engineering"}`.

baseline 字面保存该 HTTP SRMD test-facility 路径，本轮只有同主机同路径 HTTPS 成功捕获且没有已知访问边界。允许一次原 URI 检查；设施身份与其他实体接受状态保留，检查本身不是研究组接受。

Existing status/entity/acceptance retained: `supported` / `facility` / `source_supported_other_entity`.
Original HTTP-origin robots `http://se.ucsd.edu/robots.txt`: no cached explicit denial; normal robots evaluation remains required before any page request.
Identity limit: Facility classification must remain; request-scope evidence does not create an accepted lab/group.
Assessment fingerprint `6fae2a8370d1316f03f420d4cc6334d26cef8d077064bbcf12d7b1ae0bdb11de`.

## 21 — ucsd-structural-engineering-lab-structural-components-laboratory

Decision `allow_single_original_uri_public_check`; actual metadata review `2026-10-16T04:37:59+00:00`.
Original literal baseline URI: [http://se.ucsd.edu/facilities/structural-components-laboratory](http://se.ucsd.edu/facilities/structural-components-laboratory).
Current actual related URI `https://se.ucsd.edu/facilities/structural-components-laboratory`; original capture `2026-10-16T01:06:13+00:00`; status `ok`; HTTP `200`; final `https://se.ucsd.edu/facilities/structural-components-laboratory`; body SHA `c46ce91075044ed9211fb998b8ded8b0b77e25ded2828eb83bb0e5f1664d8475` (null means no successful hashed body, not a fabricated digest).
Original metadata: `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json` → item key `https://se.ucsd.edu/facilities/structural-components-laboratory`. Current packet/raw hashes and full robots/error metadata are retained in JSON.
Baseline historical websiteCheck: `{"sourceUrl": "http://se.ucsd.edu/facilities/structural-components-laboratory", "status": "reachable", "observedAt": "2026-10-02T22:41:15+00:00", "httpStatus": 200, "finalUrl": "https://se.ucsd.edu/facilities/structural-components-laboratory", "title": "Structural Components Laboratory | Structural Engineering"}`.

baseline 字面保存该 HTTP structural-components facility 路径，本轮只有对应 HTTPS 成功捕获且没有已知访问边界。允许一次原 URI 检查；保持 facility 分类、历史研究实例与当前项目的不确定性。

Existing status/entity/acceptance retained: `supported` / `facility` / `source_supported_other_entity`.
Original HTTP-origin robots `http://se.ucsd.edu/robots.txt`: no cached explicit denial; normal robots evaluation remains required before any page request.
Identity limit: Facility classification must remain; request-scope evidence does not create an accepted lab/group.
Assessment fingerprint `aa4d0a85bded0563f96d6a8d863ceccc931ee01c7c6237c0e1746e81277dbbba`.

## 22 — ucsd-lab-from-faculty-se-ucsd-edu-facilities-structural-systems-laboratory

Decision `allow_single_original_uri_public_check`; actual metadata review `2026-10-16T04:37:59+00:00`.
Original literal baseline URI: [http://se.ucsd.edu/facilities/structural-systems-laboratory](http://se.ucsd.edu/facilities/structural-systems-laboratory).
Current actual related URI `https://se.ucsd.edu/facilities/structural-systems-laboratory`; original capture `2026-10-16T01:06:15+00:00`; status `ok`; HTTP `200`; final `https://se.ucsd.edu/facilities/structural-systems-laboratory`; body SHA `3745328ed1259d4896258609dc9697e8fa554068b1a7a13d8f6543d3103aeb07` (null means no successful hashed body, not a fabricated digest).
Original metadata: `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json` → item key `https://se.ucsd.edu/facilities/structural-systems-laboratory`. Current packet/raw hashes and full robots/error metadata are retained in JSON.
Baseline historical websiteCheck: `{"sourceUrl": "http://se.ucsd.edu/facilities/structural-systems-laboratory", "status": "reachable", "observedAt": "2026-10-02T22:41:15+00:00", "httpStatus": 200, "finalUrl": "https://se.ucsd.edu/facilities/structural-systems-laboratory", "title": "Structural Systems Laboratory | Structural Engineering"}`.

baseline 稳定 ID 及字面 HTTP structural-systems facility 地址与当前 packet 一致，本轮仅有 HTTPS 成功捕获。允许一次原 URI 检查，无须改 ID 或套用教师邻接资料；实体仍是 facility，不据请求成功接受为 lab/group。

Existing status/entity/acceptance retained: `supported` / `facility` / `source_supported_other_entity`.
Original HTTP-origin robots `http://se.ucsd.edu/robots.txt`: no cached explicit denial; normal robots evaluation remains required before any page request.
Identity limit: Facility classification must remain; request-scope evidence does not create an accepted lab/group.
Assessment fingerprint `09523aff00247af4939d25cc10e6da802eb118ab57bf632747cd0c4ab4a05b8f`.

## 23 — ucsd-chemistry-biochemistry-lab-hermann-lab

Decision `allow_single_original_uri_public_check`; actual metadata review `2026-10-16T04:37:59+00:00`.
Original literal baseline URI: [http://tch.ucsd.edu](http://tch.ucsd.edu).
Current actual related URI `https://tch.ucsd.edu/`; original capture `2026-10-16T01:07:09+00:00`; status `ok`; HTTP `200`; final `https://tch.ucsd.edu/`; body SHA `1a1f4a851a89ce5ef69c1bb5324e132308a3f2ca4e380af0f8d0e0a9de138610` (null means no successful hashed body, not a fabricated digest).
Original metadata: `/tmp/ucsd-research-20261016/.cache/coverage-20261016/queue.json` → item key `https://tch.ucsd.edu/`. Current packet/raw hashes and full robots/error metadata are retained in JSON.
Baseline historical websiteCheck: `{"url": "http://tch.ucsd.edu", "httpStatus": 200, "finalUrl": "http://tch.ucsd.edu", "title": "Hermann Lab Home", "status": "ok"}`.

baseline 已保存原 HTTP tch 根 URI，本轮仅有同主机同路径 HTTPS 成功捕获且无已知访问边界。允许一次原 URI 检查，但当前 Hermann 记录是 partial、正文不足；HTTP 200、历史标题或负责人宽泛领域均不自动补足实验室整体科研证据。

Existing status/entity/acceptance retained: `partial` / `lab` / `provisional_or_unresolved`.
Original HTTP-origin robots `http://tch.ucsd.edu/robots.txt`: no cached explicit denial; normal robots evaluation remains required before any page request.
Identity limit: Hermann remains partial with insufficient lab-local scientific body; route success cannot fill the content gap.
Assessment fingerprint `a1d6d82cd019727225d9e36791700b650f9fb4292629e088fa6fa4af6ee3b366`.
