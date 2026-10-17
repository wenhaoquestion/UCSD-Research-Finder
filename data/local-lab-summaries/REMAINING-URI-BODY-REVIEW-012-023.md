# Remaining original URI body review — indices12–23

Reviewed 2026-10-16T05:00:43+00:00. Read all9 new successful packet bodies (18661 visible characters) plus their titles/contexts. Three actual requests ended404 and have no successful body source. This is content review, not metadata-only QA. Zero network requests, no raw/packet/receipt change, and no automatic navigation/meta-refresh/frame following.

**Identity result:6 confirmed at their actual type (5 facilities +1 personal site),5 uncertain,1 mismatch. No new lab/group URL or whole-lab science upgrade is recommended.** All8 successful non-Sinha bodies equal prior full text and title (and bodySHA). Preserve old scientific fields, old evidence and scientific reviewedAt.

**Sinha is a current destination mismatch:** direct originalHTTP200 served titleAllen Lab and explicitly names Monica Allen. Do not assign Allen research to Sunil K. Sinha, rename/merge records, or infer an alias. Parent should record a mismatch gate and replace the stale robots-only blocker with current identity mismatch. The earlier13 mismatch gates were not edited.

## 12 · ordinal360 · ucsd-physics-research-site-frank-wuerthwein

Actual status `http_error` / HTTP `404`. Listed `http://www.t2.ucsd.edu/twiki2/bin/view/HEPProjects/FkwsGroup`; requested `http://www.t2.ucsd.edu/twiki2/bin/view/HEPProjects/FkwsGroup`; final `http://www.t2.ucsd.edu/twiki2/bin/view/HEPProjects/FkwsGroup`. Original observedAt `2026-10-16T04:56:33+00:00`, liveCheckedAt `2026-10-16T04:56:33+00:00`. Actual redirect chain `[]`.
Source `None`; SHA256 `None`; cache SHA/source-fetch match `False`. Full text/title same as prior `False`.
Page identity **uncertain** / `unconfirmed`: 原HTTP直接返回404，无成功正文来源；既有教师资料不能确认这个TWiki组实体，失败不表示关闭。

No new successful body/title evidence is available; do not fabricate an identity quote.

Recommendation `retain_failed_target_unresolved`. Raw remains `unresolved` pending parent application; preserve scientific reviewedAt `2026-10-16T01:47:27+00:00`. Scientific diff `[]`; no method or affiliation expansion. Blockers: `["destination_http_error:404", "no_target_entity_local_body_source"]`.

## 13 · ordinal364 · ucsd-physics-research-site-john-m-goodkind

Actual status `http_error` / HTTP `404`. Listed `http://physics.ucsd.edu/research/condensed_matter/`; requested `http://physics.ucsd.edu/research/condensed_matter/`; final `https://physics.ucsd.edu/research/condensed_matter/`. Original observedAt `2026-10-16T04:56:35+00:00`, liveCheckedAt `2026-10-16T04:56:34+00:00`. Actual redirect chain `[{"from": "http://physics.ucsd.edu/research/condensed_matter/", "to": "https://physics.ucsd.edu/research/condensed_matter/", "httpStatus": 301}]`.
Source `None`; SHA256 `None`; cache SHA/source-fetch match `False`. Full text/title same as prior `False`.
Page identity **uncertain** / `unconfirmed`: 实际HTTP301至同路径HTTPS，最终404；condensed_matter学科路径没有新具名Goodkind组正文。

No new successful body/title evidence is available; do not fabricate an identity quote.

Recommendation `retain_failed_target_unresolved`. Raw remains `unresolved` pending parent application; preserve scientific reviewedAt `2026-10-16T01:47:27+00:00`. Scientific diff `[]`; no method or affiliation expansion. Blockers: `["destination_http_error:404", "no_target_entity_local_body_source"]`.

## 14 · ordinal371 · ucsd-physics-research-site-lu-j-sham

Actual status `ok` / HTTP `200`. Listed `http://ljssst.physics.ucsd.edu`; requested `http://ljssst.physics.ucsd.edu/`; final `https://ljssst.physics.ucsd.edu/`. Original observedAt `2026-10-16T04:56:39+00:00`, liveCheckedAt `2026-10-16T04:56:38+00:00`. Actual redirect chain `[{"from": "http://ljssst.physics.ucsd.edu/", "to": "https://ljssst.physics.ucsd.edu/", "httpStatus": 301}]`.
Source `src-5254714b0005f61c`; SHA256 `99836205cf76360ffd678ff2396e5e525a60a1ac04fb993c1be7ab95b6e0d569`; cache SHA/source-fetch match `True`. Full text/title same as prior `True`.
Page identity **confirmed** / `personal_research_site`: 当前目的页明确Lu Jeu Sham且第一人称My specialty/My current interest；确认个人研究站作用域，未确认独立lab/group，不提升实验室实体。

- body (`src-5254714b0005f61c`, identity_personal_site): `Lu Jeu Sham Distinguished Professor Emeritus of Physics`
- body (`src-5254714b0005f61c`, personal_scope): `The opinion expressed in this website is entirely my own and does not reflect the official positions of the funding agencies.`

Prior equivalent source(s): `src-77ef95a623e4afc8` (https://ljssst.physics.ucsd.edu/, 2026-10-16T01:05:26+00:00).

Recommendation `append_identity_only_keep_personal_type`. Raw remains `partial` pending parent application; preserve scientific reviewedAt `2026-10-16T01:55:29+00:00`. Scientific diff `[]`; no method or affiliation expansion. Blockers: `["personal_research_site_not_independent_lab_group"]`.

## 15 · ordinal376 · ucsd-physics-research-site-shelley-wright

Actual status `ok` / HTTP `200`. Listed `http://oirlab.ucsd.edu`; requested `http://oirlab.ucsd.edu/`; final `https://oirlab.ucsd.edu/`. Original observedAt `2026-10-16T04:56:43+00:00`, liveCheckedAt `2026-10-16T04:56:42+00:00`. Actual redirect chain `[{"from": "http://oirlab.ucsd.edu/", "to": "https://oirlab.ucsd.edu/", "httpStatus": 301}]`.
Source `src-23b5d4ff05200932`; SHA256 `92a3b5a77991171ad13605f0665ae30437fea09d8cffce5d3c9d778e83b3ad68`; cache SHA/source-fetch match `True`. Full text/title same as prior `True`.
Page identity **uncertain** / `lab`: HTTP301只到HTTPS根；新根正文仅This page has moved to index.php并有HTML meta-refresh。没有具名OIR/Shelley身份字面引文；保持根pageIdentity uncertain，既有团队/概述科学supported不动。

- body (`src-23b5d4ff05200932`, navigation_only_not_identity): `This page has moved to index.php .`

Prior equivalent source(s): `src-6c0a5af04a439d91` (https://oirlab.ucsd.edu/, 2026-10-16T01:05:27+00:00).

Recommendation `keep_root_identity_uncertain_and_preserve_existing_science`. Raw remains `supported` pending parent application; preserve scientific reviewedAt `2026-10-16T03:26:20+00:00`. Scientific diff `[]`; no method or affiliation expansion. Blockers: `["root_is_navigation_document_without_named_entity_identity", "html_meta_refresh_not_an_observed_HTTP_redirect_to_index_php"]`.

## 16 · ordinal378 · ucsd-physics-research-site-sunil-k-sinha

Actual status `ok` / HTTP `200`. Listed `http://sinhagroup.ucsd.edu/`; requested `http://sinhagroup.ucsd.edu/`; final `http://sinhagroup.ucsd.edu/`. Original observedAt `2026-10-16T04:56:45+00:00`, liveCheckedAt `2026-10-16T04:56:45+00:00`. Actual redirect chain `[]`.
Source `src-7da5f97add4fcfac`; SHA256 `35b50cf6304cafc42e6f4ccbd258eaabf7cf130e132d9541eb379740145c97eb`; cache SHA/source-fetch match `True`. Full text/title same as prior `False`.
Page identity **mismatch** / `unconfirmed`: 实际HTTP200无redirect，但titleAllen Lab且正文联系Monica Allen；没有Sunil K. Sinha与该团队的显式关系。当前目的页与目标Sinha记录身份错配，Allen研究不得归入Sinha。

- title (`src-7da5f97add4fcfac`, conflicting_identity): `Allen Lab`
- body (`src-7da5f97add4fcfac`, conflicting_named_contact): `If you are interested, please contact Monica Allen .`

Recommendation `record_mismatch_and_hold_Sinha_unaccepted`. Raw remains `unresolved` pending parent application; preserve scientific reviewedAt `2026-10-16T01:47:27+00:00`. Scientific diff `[]`; no method or affiliation expansion. Blockers: `["destination_identity_mismatch:Allen_Lab_Monica_Allen_instead_of_Sunil_K_Sinha", "no_target_Sinha_scoped_research", "requires_parent_identity_decision_no_silent_alias"]`.

## 17 · ordinal380 · ucsd-physics-research-site-thomas-m-o-neil

Actual status `http_error` / HTTP `404`. Listed `http://physics.ucsd.edu/research/plasma/`; requested `http://physics.ucsd.edu/research/plasma/`; final `https://physics.ucsd.edu/research/plasma/`. Original observedAt `2026-10-16T04:56:47+00:00`, liveCheckedAt `2026-10-16T04:56:45+00:00`. Actual redirect chain `[{"from": "http://physics.ucsd.edu/research/plasma/", "to": "https://physics.ucsd.edu/research/plasma/", "httpStatus": 301}]`.
Source `None`; SHA256 `None`; cache SHA/source-fetch match `False`. Full text/title same as prior `False`.
Page identity **uncertain** / `unconfirmed`: 实际HTTP301至同路径HTTPS，最终404；plasma学科路径没有新具名O’Neil组正文。

No new successful body/title evidence is available; do not fabricate an identity quote.

Recommendation `retain_failed_target_unresolved`. Raw remains `unresolved` pending parent application; preserve scientific reviewedAt `2026-10-16T01:48:07+00:00`. Scientific diff `[]`; no method or affiliation expansion. Blockers: `["destination_http_error:404", "no_target_entity_local_body_source"]`.

## 18 · ordinal432 · ucsd-structural-engineering-lab-composite-structures-laboratory

Actual status `ok` / HTTP `200`. Listed `http://se.ucsd.edu/facilities/composite-structures-laboratory`; requested `http://se.ucsd.edu/facilities/composite-structures-laboratory`; final `https://se.ucsd.edu/facilities/composite-structures-laboratory`. Original observedAt `2026-10-16T04:56:50+00:00`, liveCheckedAt `2026-10-16T04:56:49+00:00`. Actual redirect chain `[{"from": "http://se.ucsd.edu/facilities/composite-structures-laboratory", "to": "https://se.ucsd.edu/facilities/composite-structures-laboratory", "httpStatus": 301}]`.
Source `src-4d8d0952c44bd2c8`; SHA256 `d58101b63bec9b85ab3f6cc2d6f4caa6e4661a1451c66dcf34b2a9494d60687a`; cache SHA/source-fetch match `True`. Full text/title same as prior `True`.
Page identity **confirmed** / `facility`: 具名Composite Structures Laboratory正文只描述反力墙/强地板/空间及Inquiry联系人，确认facility，不是lab/group科研升级。

- body (`src-4d8d0952c44bd2c8`, facility_identity): `Composite Structures Laboratory`

Prior equivalent source(s): `src-f93474e8e9e61386` (https://se.ucsd.edu/facilities/composite-structures-laboratory, 2026-10-16T01:06:10+00:00).

Recommendation `append_identity_only_keep_facility_type`. Raw remains `partial` pending parent application; preserve scientific reviewedAt `2026-10-16T01:49:24+00:00`. Scientific diff `[]`; no method or affiliation expansion. Blockers: `["facility_description_only_no_research_question"]`.

## 19 · ordinal433 · ucsd-structural-engineering-lab-geotechnical-laboratories

Actual status `ok` / HTTP `200`. Listed `http://se.ucsd.edu/facilities/geotechnical-facilities`; requested `http://se.ucsd.edu/facilities/geotechnical-facilities`; final `https://se.ucsd.edu/facilities/geotechnical-facilities`. Original observedAt `2026-10-16T04:56:52+00:00`, liveCheckedAt `2026-10-16T04:56:51+00:00`. Actual redirect chain `[{"from": "http://se.ucsd.edu/facilities/geotechnical-facilities", "to": "https://se.ucsd.edu/facilities/geotechnical-facilities", "httpStatus": 301}]`.
Source `src-25ef0d806015bf06`; SHA256 `6d8ce30f9f6487e3ea16241beab76cc6650ef046f0c5f41c18c8a3d923358676`; cache SHA/source-fetch match `True`. Full text/title same as prior `True`.
Page identity **confirmed** / `facility`: 具名Geotechnical Facilities及UCSD geotechnical laboratory设备/测试叙述确认岩土设施；同旧全文，不扩展为独立PI研究组。

- body (`src-25ef0d806015bf06`, facility_identity): `Geotechnical Facilities`
- body (`src-25ef0d806015bf06`, facility_scope): `The UCSD geotechnical laboratory is fully equipped for standard soil classification and characterization.`

Prior equivalent source(s): `src-4ee98098754bd15b` (https://se.ucsd.edu/facilities/geotechnical-facilities, 2026-10-16T01:06:11+00:00).

Recommendation `append_identity_only_keep_facility_type`. Raw remains `supported` pending parent application; preserve scientific reviewedAt `2026-10-16T01:55:29+00:00`. Scientific diff `[]`; no method or affiliation expansion. Blockers: `[]`.

## 20 · ordinal434 · ucsd-structural-engineering-lab-srmd-laboratory

Actual status `ok` / HTTP `200`. Listed `http://se.ucsd.edu/facilities/laboratory-listing/srmd`; requested `http://se.ucsd.edu/facilities/laboratory-listing/srmd`; final `https://se.ucsd.edu/facilities/laboratory-listing/srmd`. Original observedAt `2026-10-16T04:56:54+00:00`, liveCheckedAt `2026-10-16T04:56:53+00:00`. Actual redirect chain `[{"from": "http://se.ucsd.edu/facilities/laboratory-listing/srmd", "to": "https://se.ucsd.edu/facilities/laboratory-listing/srmd", "httpStatus": 301}]`.
Source `src-9abf6474a6335d0a`; SHA256 `1c3fa24be16b9889fcb3458e26b8d84f8ca5046250dcf4b6c58ef9653cffb82a`; cache SHA/source-fetch match `True`. Full text/title same as prior `True`.
Page identity **confirmed** / `facility`: 正文完整具名SRMD Test Facility并描述全尺度装置测试系统，确认facility；保留1999/2003历史时间边界。

- body (`src-9abf6474a6335d0a`, facility_identity): `Caltrans Seismic Response Modification Device (SRMD) Test Facility`

Prior equivalent source(s): `src-ae3553870519d80a` (https://se.ucsd.edu/facilities/laboratory-listing/srmd, 2026-10-16T01:06:12+00:00).

Recommendation `append_identity_only_keep_facility_type`. Raw remains `supported` pending parent application; preserve scientific reviewedAt `2026-10-16T01:55:29+00:00`. Scientific diff `[]`; no method or affiliation expansion. Blockers: `[]`.

## 21 · ordinal435 · ucsd-structural-engineering-lab-structural-components-laboratory

Actual status `ok` / HTTP `200`. Listed `http://se.ucsd.edu/facilities/structural-components-laboratory`; requested `http://se.ucsd.edu/facilities/structural-components-laboratory`; final `https://se.ucsd.edu/facilities/structural-components-laboratory`. Original observedAt `2026-10-16T04:56:56+00:00`, liveCheckedAt `2026-10-16T04:56:55+00:00`. Actual redirect chain `[{"from": "http://se.ucsd.edu/facilities/structural-components-laboratory", "to": "https://se.ucsd.edu/facilities/structural-components-laboratory", "httpStatus": 301}]`.
Source `src-a5fc160a948272fd`; SHA256 `c46ce91075044ed9211fb998b8ded8b0b77e25ded2828eb83bb0e5f1664d8475`; cache SHA/source-fetch match `True`. Full text/title same as prior `True`.
Page identity **confirmed** / `facility`: 正文具名Structural Components Laboratory并介绍其强地板/反力墙/振动台；保持facility，历史1994震后测试不改写为全部当前项目。

- body (`src-a5fc160a948272fd`, facility_identity): `Structural Components Laboratory`

Prior equivalent source(s): `src-6fc7d92ea2e87080` (https://se.ucsd.edu/facilities/structural-components-laboratory, 2026-10-16T01:06:13+00:00).

Recommendation `append_identity_only_keep_facility_type`. Raw remains `supported` pending parent application; preserve scientific reviewedAt `2026-10-16T01:55:29+00:00`. Scientific diff `[]`; no method or affiliation expansion. Blockers: `[]`.

## 22 · ordinal436 · ucsd-lab-from-faculty-se-ucsd-edu-facilities-structural-systems-laboratory

Actual status `ok` / HTTP `200`. Listed `http://se.ucsd.edu/facilities/structural-systems-laboratory`; requested `http://se.ucsd.edu/facilities/structural-systems-laboratory`; final `https://se.ucsd.edu/facilities/structural-systems-laboratory`. Original observedAt `2026-10-16T04:56:58+00:00`, liveCheckedAt `2026-10-16T04:56:57+00:00`. Actual redirect chain `[{"from": "http://se.ucsd.edu/facilities/structural-systems-laboratory", "to": "https://se.ucsd.edu/facilities/structural-systems-laboratory", "httpStatus": 301}]`.
Source `src-55982eaf3e74e880`; SHA256 `3745328ed1259d4896258609dc9697e8fa554068b1a7a13d8f6543d3103aeb07`; cache SHA/source-fetch match `True`. Full text/title same as prior `True`.
Page identity **confirmed** / `facility`: 正文具名Structural Systems Laboratory与反力墙/强地板系统，保持facility；1986/1989/1999历史信息不等于新当前项目。

- body (`src-55982eaf3e74e880`, facility_identity): `Structural Systems Laboratory`

Prior equivalent source(s): `src-18a0900c2b0878e4` (https://se.ucsd.edu/facilities/structural-systems-laboratory, 2026-10-16T01:06:15+00:00).

Recommendation `append_identity_only_keep_facility_type`. Raw remains `supported` pending parent application; preserve scientific reviewedAt `2026-10-16T01:55:29+00:00`. Scientific diff `[]`; no method or affiliation expansion. Blockers: `[]`.

## 23 · ordinal693 · ucsd-chemistry-biochemistry-lab-hermann-lab

Actual status `ok` / HTTP `200`. Listed `http://tch.ucsd.edu`; requested `http://tch.ucsd.edu/`; final `http://tch.ucsd.edu/`. Original observedAt `2026-10-16T04:57:00+00:00`, liveCheckedAt `2026-10-16T04:57:00+00:00`. Actual redirect chain `[]`.
Source `src-6b3d477e4eb8109d`; SHA256 `1a1f4a851a89ce5ef69c1bb5324e132308a3f2ca4e380af0f8d0e0a9de138610`; cache SHA/source-fetch match `True`. Full text/title same as prior `True`.
Page identity **uncertain** / `lab`: 标题Hermann Lab Home与目标名称相符，但实际缓存HTML正文全为无alt图片和导航，未提供可读具名PI/实验室研究说明。标题可作名称线索，当前实体范围仍uncertain，不自动提升partial。

- title (`src-6b3d477e4eb8109d`, identity_name_only_insufficient_current_entity_scope): `Hermann Lab Home`

Prior equivalent source(s): `src-6882240f2c380608` (https://tch.ucsd.edu/, 2026-10-16T01:07:09+00:00).

Recommendation `retain_partial_title_only_entity_uncertainty`. Raw remains `partial` pending parent application; preserve scientific reviewedAt `2026-10-16T01:48:38+00:00`. Scientific diff `[]`; no method or affiliation expansion. Blockers: `["only_named_title_and_image_navigation_no_readable_entity_or_research_body"]`.

Cached HTML contains literal `<a href="Research.html">` with an image `images/Research.gif` and empty alt, resolving to `http://tch.ucsd.edu/Research.html`. This is a real discovery candidate only; it was not requested/read as a research page or treated as research evidence.
