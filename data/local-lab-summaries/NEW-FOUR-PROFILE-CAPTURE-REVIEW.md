# Four new profile-capture review

Reviewed at 2026-10-16T08:59:59+00:00. Offline reuse only;0 network/PS requests; no raw, packet, collector, code or receipt edits.

Input delta SHA-256: `32e3cfad55fcc5683503ebb7759eb8cb5d49a3c08146e35ad92819e6f67e3c8c`. The report preserves the input’s frozen08:55:31 queue snapshot; it did not reread the live queue.

All four successful HTML bodies were read in full under the existing local ContentDOM.main boundary; each actual body hash and original sidecar URI/status/final URL/time/hash matches the delta. No whole-lab scientific improvement or new entity acceptance is proposed.

| Capture | Actual observedAt | Target decision |
|---|---|---|
| https://cogsci.ucsd.edu/people/faculty/lara-rangel.html | 2026-10-16T08:32:12+00:00 | personal_profile_or_associated_link_only_no_whole_lab_science |
| https://www.ece.ucsd.edu/faculty-research/Ultrafast%20and%20Nanoscale%20Optics%20Group%20(Professor%20Shaya%20Fainman) | 2026-10-16T08:38:00+00:00 | http404_no_scientific_body |
| https://linguistics.ucsd.edu/people/faculty/profiles/rachel-mayberry.html | 2026-10-16T08:34:12+00:00 | same_bytes_and_visible_text_new_observation_no_science_delta |
| https://profiles.ucsd.edu/Arpi.Minassian | 2026-10-16T08:34:06+00:00 | personal_profile_or_associated_link_only_no_whole_lab_science |
| https://linguistics.ucsd.edu/people/faculty/profiles/andrew-kehler.html | 2026-10-16T08:34:18+00:00 | same_bytes_and_visible_text_new_observation_no_science_delta |

## Individual findings

### 0 — https://cogsci.ucsd.edu/people/faculty/lara-rangel.html

Body SHA-256: `6c2a58857001a5815396cb2294c41614f515529d136b533c6b8e65bb5e29a1b7`; metadata SHA-256: `0ea9d6f8b23078b89a4b1190c65076b2ac71ad173af401c04a30109240466eac`.
该正式教师页给Lara Rangel个人研究兴趣；Personal Website字面指向HTTP Neural Crossroads站点，可保留个人与站点关联。没有Our lab/具名Neural Crossroads整体研究声明，不能将个人方向搬到该lab或补whole-lab科学字段。

> Lara Rangel Associate Professor

> Rhythmic coordination of brain activity, information processing in neural networks, dynamic interactions between neurons, learning, memory, neuromodulation.

- Actual main-content anchor `Personal Website` → `http://neuralcrossroads.ucsd.edu/`. Association only; no target request, redirect or canonical acceptance implied.
### 1 — https://www.ece.ucsd.edu/faculty-research/Ultrafast%20and%20Nanoscale%20Optics%20Group%20(Professor%20Shaya%20Fainman)

Body SHA-256: `None`; metadata SHA-256: `dd77a38acadcd2b6f1013f220a05c438d50f3c797c67cfd6078e24de493abbfb`.
此次真实原URI检查返回HTTP404且没有保存成功HTML正文；不提供科研/当前实体接受证据，也不据404推断实验室关闭或不存在。

### 2 — https://linguistics.ucsd.edu/people/faculty/profiles/rachel-mayberry.html

Body SHA-256: `541c10497e82fd8e25f7f4de2f3c632a9222b3370a7d1939285952c88ed1451a`; metadata SHA-256: `8e0ad4d27f87d99f3e9c8d0e13fe476de4759db65cd4f8dc4af207cad428459f`.
页内仅Rachel Mayberry个人联系信息及Personal Website；实际目标为grammar.ucsd.edu/mayberrylab/RachelMayberry.html，与LLP语言学习设施不同。不得将姓名、个人网站或共享导航Language Lab链接作为该设施的PI/科研绑定。

> Rachel Mayberry Professor

- Actual main-content anchor `Personal Website` → `http://grammar.ucsd.edu/mayberrylab/RachelMayberry.html`. Association only; no target request, redirect or canonical acceptance implied.
- Actual main-content anchor `Personal website` → `http://grammar.ucsd.edu/mayberrylab/RachelMayberry.html`. Association only; no target request, redirect or canonical acceptance implied.
- Exact same prior body/full visible text: `src-ab17fbcbf6a3f0f0`, original observedAt `2026-10-16T00:59:54+00:00`. New `2026-10-16T08:34:12+00:00` is a separate collector observation and must not replace that old source date.
### 3 — https://profiles.ucsd.edu/Arpi.Minassian

Body SHA-256: `5eaa87c191a93da2753a44ddf73494e2685af598777f2bb93d6552d205e17030`; metadata SHA-256: `87705653a83f7bbb112a2e27a2416009bb525480f7933adc6ced2571c68792b3`.
个人简介有研究计划、方法及未具名research laboratory地点，并有Featured Content中的TRIPEC lab website精确旧href。这只能确认档案关联该网址，不能自动认定个人研究计划或未具名lab地点就是TRIPEC整体研究/机构隶属；不提升目标identity或affiliation。

> Dr. Minassian’s research program is focused upon understanding the relationship between biology and behavior in mental illness, medical illness, and substance abuse.

> Her research laboratory is located at the UCSD Medical Center in Hillcrest.

> Much of her research has implemented physiological and cognitive paradigms to understand brain dysfunction in psychiatric populations such as bipolar disorder, schizophrenia, PTSD, and substance addiction as well as neuromedical conditions such as HIV.

> TRIPEC lab website

- Actual main-content anchor `TRIPEC lab website` → `https://medschool.ucsd.edu/som/psychiatry/research/TRIPEC/Pages/default.aspx`. Association only; no target request, redirect or canonical acceptance implied.
### 4 — https://linguistics.ucsd.edu/people/faculty/profiles/andrew-kehler.html

Body SHA-256: `5854b582fa3b7926e030cbb97f15e8637782a1af5ae47b3cdcf5b88142e52782`; metadata SHA-256: `f3d741da0ac90fb42d69f7f869caec56be25de68335efb63dbe99ed0352c1c45`.
页内仅Andrew Kehler个人联系信息及Personal Website，实际目标为akehler.github.io；无LLP语言设施研究、PI或机构归属声明。

> Andrew Kehler Professor

- Actual main-content anchor `Personal Website` → `https://akehler.github.io/`. Association only; no target request, redirect or canonical acceptance implied.
- Actual main-content anchor `Personal Website` → `https://akehler.github.io/`. Association only; no target request, redirect or canonical acceptance implied.
- Exact same prior body/full visible text: `src-db933ba8884cfdbb`, original observedAt `2026-10-16T00:59:51+00:00`. New `2026-10-16T08:34:18+00:00` is a separate collector observation and must not replace that old source date.

Rangel remains a confirmed named lab with insufficient whole-lab research prose; the new page adds only personal interests and a literal HTTP personal-site association. TRIPEC keeps its uncertain entity/affiliation and original root404; the personal research-laboratory location is not accepted as TRIPEC’s lab-level affiliation. LLP keeps its teaching-facility classification and its existing explicit temporary-closure notice. No current appointment, affiliation, reopening or closure inference is added.

These captures are excluded from the current434-record frozen question migration. Any later source append or field change requires its own explicit entity-scope review; this report performs none.
