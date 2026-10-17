# Original HTTP identity binding review — gap items 30–47

Review completed 2026-10-16T04:27:36+00:00. All 18 new destination identity bindings were reviewed and each saved record passed hydrate. **18 canCountAsVerifiedLabGroupURL values recovered from false to true.**

Each actual request URI, original observedAt, body SHA256, final URI and redirect chain was matched against the original gap fetch receipt and current packet; all 18 actual cache files also matched their SHA256. Every final URI in this assignment remains HTTP and every redirect chain is empty. This is not an inferred HTTP-to-HTTPS migration.

Only literal identity evidence and a separate `identityBindingReviewedAt` were appended. Scientific summary/questions/topics/methods, affiliation, identity type/acceptance, stable IDs, old evidence and `raw.reviewedAt` were preserved exactly. No alias, packet/projection/code/collector/shared-state edit or network request was performed. The 13 mismatch gates were not touched.

Seventeen bodies match a prior source SHA256. M2DO has a different body SHA256 but an identical full extracted text and title; Kadonaga matches the prior body SHA256 despite the older extracted text being capped/different. Actual prior source IDs and times are recorded below and in JSON; URI schemes are kept distinct. The review reuses prior scientific semantics after this equality check and reads the title and enough lab/group context for the new identity binding.

## 30 · ordinal 711 · ucsd-chemistry-biochemistry-lab-tor-lab

Actual requested/final URI: [http://torgroup.ucsd.edu/](http://torgroup.ucsd.edu/); observedAt `2026-10-16T04:23:31+00:00`, liveCheckedAt `2026-10-16T04:23:31+00:00`; redirects `[]`.
New source `src-4ff55423c2b5fa89`; body SHA256 `66dcf35d601d7224ab6394333d2896f18776662be76187ad81b5e40c1de91338`. Exact fetch match and cache hash verified.
Identity: 具名Tor Lab欢迎语与具名Tor Group正文相互一致。
- body: `Welcome to the Tor Lab Home.` (supports identity only)
Prior equivalent source(s): `src-61dc67c7eacda35e` (https://torgroup.ucsd.edu/, 2026-10-16T01:07:16+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:49:25+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 31 · ordinal 713 · ucsd-chemistry-biochemistry-lab-yang-research-group-jerry-yang

Actual requested/final URI: [http://yanglab.ucsd.edu/](http://yanglab.ucsd.edu/); observedAt `2026-10-16T04:23:33+00:00`, liveCheckedAt `2026-10-16T04:23:33+00:00`; redirects `[]`.
New source `src-600adb3d83e83c74`; body SHA256 `b9a06236cb24647384bacb2621f18d33fa51523a54de143cce74c3a3fa975508`. Exact fetch match and cache hash verified.
Identity: 具名Yang Research Group页脚与Yang lab新闻上下文一致；新闻原日期不作为当前成员证明。
- body: `© Yang Research Group` (supports identity only)
Prior equivalent source(s): `src-590567ddd5d224f3` (https://yanglab.ucsd.edu/, 2026-10-16T01:07:16+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T02:21:55+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 32 · ordinal 715 · ucsd-chemistry-biochemistry-lab-yuen-zhou-group

Actual requested/final URI: [http://yuenzhougroup.ucsd.edu/](http://yuenzhougroup.ucsd.edu/); observedAt `2026-10-16T04:23:35+00:00`, liveCheckedAt `2026-10-16T04:23:35+00:00`; redirects `[]`.
New source `src-8f4b0bcbe54014dc`; body SHA256 `b2193df8ca453d1afa766ebdd5cd56a9ac6af80e45bc47611f7a687fe833e10b`. Exact fetch match and cache hash verified.
Identity: 根页直接欢迎Yuen Zhou Group，名称与既有实体一致。
- body: `Welcome to the Yuen Zhou Group` (supports identity only)
Prior equivalent source(s): `src-88f78b8886230e7d` (https://yuenzhougroup.ucsd.edu/, 2026-10-16T01:07:17+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T02:19:16+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 33 · ordinal 724 · ucsd-biochemistry-and-molecular-biophysics-lab-joseph-lab

Actual requested/final URI: [http://josephgroup.ucsd.edu/](http://josephgroup.ucsd.edu/); observedAt `2026-10-16T04:23:37+00:00`, liveCheckedAt `2026-10-16T04:23:37+00:00`; redirects `[]`.
New source `src-e177ca77f7906e58`; body SHA256 `840b278ced95c4d48d9320ae340ac2d1bc55d1dae406983b7a3251ebaf3b1b9d`. Exact fetch match and cache hash verified.
Identity: 标题明确Welcome to the Joseph Lab，正文招募信息具名Dr. Simpson Joseph。
- title: `Welcome to the Joseph Lab` (supports identity only)
Prior equivalent source(s): `src-2138cbb72c206404` (https://josephgroup.ucsd.edu/, 2026-10-16T01:06:15+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:49:25+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 34 · ordinal 726 · ucsd-biochemistry-and-molecular-biophysics-lab-komor-lab

Actual requested/final URI: [http://komorlab.ucsd.edu/](http://komorlab.ucsd.edu/); observedAt `2026-10-16T04:23:38+00:00`, liveCheckedAt `2026-10-16T04:23:38+00:00`; redirects `[]`.
New source `src-239aafc0f490bcff`; body SHA256 `24c5afa6a2c7680a58e07de9728643698a66263e5bc5bbc5312b356d2edbcdc8`. Exact fetch match and cache hash verified.
Identity: 正文直接标识The Komor Lab，随后是同一实验室的研究说明。
- body: `The Komor Lab` (supports identity only)
Prior equivalent source(s): `src-883854c66b939959` (https://komorlab.ucsd.edu/, 2026-10-16T01:06:15+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:49:25+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 35 · ordinal 732 · ucsd-biochemistry-and-molecular-biophysics-lab-toor-lab

Actual requested/final URI: [http://rna.ucsd.edu/](http://rna.ucsd.edu/); observedAt `2026-10-16T04:23:40+00:00`, liveCheckedAt `2026-10-16T04:23:40+00:00`; redirects `[]`.
New source `src-63a8a61dea803852`; body SHA256 `4447365309ee9c4c9d665fb8dd3722452eddfe7610b08dcd08689a428b495c76`. Exact fetch match and cache hash verified.
Identity: 正文直接欢迎Toor Lab，并继续用We描述同一团队。
- body: `Welcome to the Toor Lab!` (supports identity only)
Prior equivalent source(s): `src-0e9ac488b86bbd8d` (https://rna.ucsd.edu/, 2026-10-16T01:07:22+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:50:12+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 36 · ordinal 733 · ucsd-biochemistry-and-molecular-biophysics-lab-zid-lab

Actual requested/final URI: [http://zidlab.ucsd.edu/](http://zidlab.ucsd.edu/); observedAt `2026-10-16T04:23:42+00:00`, liveCheckedAt `2026-10-16T04:23:42+00:00`; redirects `[]`.
New source `src-48c0d91aedf817a4`; body SHA256 `1da49bd884a8fcd0d48820c9587f42a29f55dfc64624a4c8aed236e57d6837e6`. Exact fetch match and cache hash verified.
Identity: 正文直接标识The Zid Lab at UC San Diego。
- body: `The Zid Lab at UC San Diego` (supports identity only)
Prior equivalent source(s): `src-eb99cdce3c82573c` (https://zidlab.ucsd.edu/, 2026-10-16T01:06:18+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:50:12+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 37 · ordinal 807 · ucsd-biological-sciences-lab-kadonaga-lab

Actual requested/final URI: [http://biology.ucsd.edu/research/faculty/jkadonaga](http://biology.ucsd.edu/research/faculty/jkadonaga); observedAt `2026-10-16T04:23:43+00:00`, liveCheckedAt `2026-10-16T04:23:43+00:00`; redirects `[]`.
New source `src-2705f44bd0668fde`; body SHA256 `50e353e68862f62e8cabdfdbd639a965e2779ed6d55213759858a3c6c41e835e`. Exact fetch match and cache hash verified.
Identity: James T. Kadonaga具名标题与正文In my lab范围共同确认其实验室；个人姓名本身未单独当作实验室证明。
- title: `James T. Kadonaga` (supports identity only)
- body: `In my lab, we study the regulation of transcription by RNA polymerase II.` (supports identity only)
Prior equivalent source(s): `src-4cdf2e8fbc6dcb8c` (https://biology.ucsd.edu/research/faculty/jkadonaga, 2026-10-16T01:07:32+00:00; SHA equal=true, full text/title equal=false).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:52:41+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 38 · ordinal 808 · ucsd-biological-sciences-lab-yelon-lab

Actual requested/final URI: [http://biology.ucsd.edu/research/faculty/dyelon](http://biology.ucsd.edu/research/faculty/dyelon); observedAt `2026-10-16T04:23:44+00:00`, liveCheckedAt `2026-10-16T04:23:44+00:00`; redirects `[]`.
New source `src-f453e78376250534`; body SHA256 `17c11774a5c71811d1991c03d25864e46fcefd029d6376adec9e857f7f9f12ec`. Exact fetch match and cache hash verified.
Identity: Deborah Yelon具名标题与our laboratory正文共同确认实验室作用域。
- title: `Deborah Yelon` (supports identity only)
- body: `The goal of our laboratory's research is to understand the molecular mechanisms that specify the size, shape, and attributes of each cardiac chamber.` (supports identity only)
Prior equivalent source(s): `src-413a97ec229e1fc0` (https://biology.ucsd.edu/research/faculty/dyelon, 2026-10-16T01:07:33+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:52:41+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 39 · ordinal 809 · ucsd-biological-sciences-lab-lykke-andersen-lab

Actual requested/final URI: [http://biology.ucsd.edu/research/faculty/jlykkeandersen](http://biology.ucsd.edu/research/faculty/jlykkeandersen); observedAt `2026-10-16T04:23:45+00:00`, liveCheckedAt `2026-10-16T04:23:45+00:00`; redirects `[]`.
New source `src-11b4f50c5487577f`; body SHA256 `5dc45263a47ae3c5a61adc1b10bb97e6edf7c42dca2f6a2a17ca7e076046db32`. Exact fetch match and cache hash verified.
Identity: Jens Lykke-Andersen具名标题与Our laboratory研究正文共同确认实验室作用域。
- title: `Jens Lykke-Andersen` (supports identity only)
- body: `Our laboratory studies the mechanisms of regulation of translation and mRNA turnover in human gene expression.` (supports identity only)
Prior equivalent source(s): `src-322a2ca2584566c6` (https://biology.ucsd.edu/research/faculty/jlykkeandersen, 2026-10-16T01:07:34+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:52:41+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 40 · ordinal 810 · ucsd-biological-sciences-lab-kryazhimskiy-lab

Actual requested/final URI: [http://biology.ucsd.edu/research/faculty/skryazhimskiy](http://biology.ucsd.edu/research/faculty/skryazhimskiy); observedAt `2026-10-16T04:23:46+00:00`, liveCheckedAt `2026-10-16T04:23:46+00:00`; redirects `[]`.
New source `src-73d585e359a77307`; body SHA256 `034ec901b57297103a367c071ddb059ef4c825a41ab132f451dc09594318a3e0`. Exact fetch match and cache hash verified.
Identity: Sergey Kryazhimskiy具名标题与Our lab正文共同确认实验室作用域；旧传记日期未提升为当前任职证明。
- title: `Sergey Kryazhimskiy` (supports identity only)
- body: `Our lab has three complementary themes.` (supports identity only)
Prior equivalent source(s): `src-a9e2cce5f55b42cf` (https://biology.ucsd.edu/research/faculty/skryazhimskiy, 2026-10-16T01:07:35+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:53:25+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 41 · ordinal 811 · ucsd-biological-sciences-lab-jackrel-lab

Actual requested/final URI: [http://biology.ucsd.edu/research/faculty/sjackrel](http://biology.ucsd.edu/research/faculty/sjackrel); observedAt `2026-10-16T04:23:47+00:00`, liveCheckedAt `2026-10-16T04:23:47+00:00`; redirects `[]`.
New source `src-a79d5b12162bf295`; body SHA256 `92189ecf4dd2764710c54fe1396f6b4bdcf6a80467807a90967728835962d0e7`. Exact fetch match and cache hash verified.
Identity: 正文明确命名Jackrel lab，非仅凭faculty页姓名。
- body: `Research in the Jackrel lab focuses on understanding when and how biological diversity at multiple scales regulates ecosystem functions.` (supports identity only)
Prior equivalent source(s): `src-544b5d38b78800fb` (https://biology.ucsd.edu/research/faculty/sjackrel, 2026-10-16T01:07:37+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:53:25+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 42 · ordinal 812 · ucsd-biological-sciences-lab-halpain-lab

Actual requested/final URI: [http://biology.ucsd.edu/research/faculty/shalpain](http://biology.ucsd.edu/research/faculty/shalpain); observedAt `2026-10-16T04:23:48+00:00`, liveCheckedAt `2026-10-16T04:23:48+00:00`; redirects `[]`.
New source `src-e0f7e4468c2b4014`; body SHA256 `bce0f4059a773d4f9bcbc32304e82d4ca592d450298fe919f22c60d57a888719`. Exact fetch match and cache hash verified.
Identity: Shelley Halpain具名标题与Dr. Halpain/Her laboratory段落共同确认实验室作用域。
- title: `Shelley Halpain` (supports identity only)
- body: `Dr. Halpain’s research concerns the molecular basis for neural development. Her laboratory uses advanced light microscopy and quantitative cellular imaging methods to investigate neurite outgrowth and synapse formation.` (supports identity only)
Prior equivalent source(s): `src-a76f19d10cdb5236` (https://biology.ucsd.edu/research/faculty/shalpain, 2026-10-16T01:07:38+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:53:25+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 43 · ordinal 813 · ucsd-biological-sciences-lab-posakony-lab

Actual requested/final URI: [http://biology.ucsd.edu/research/faculty/jposakony](http://biology.ucsd.edu/research/faculty/jposakony); observedAt `2026-10-16T04:23:49+00:00`, liveCheckedAt `2026-10-16T04:23:49+00:00`; redirects `[]`.
New source `src-3ddd44182e682269`; body SHA256 `566bbad5d570de13e4fe9ec3ae30dac04c0fd8c735c4d2479a7ae6745cec8c94`. Exact fetch match and cache hash verified.
Identity: James W. Posakony标题、Jim Posakony正文姓名与our lab段落共同确认同一实验室。
- title: `James W. Posakony` (supports identity only)
- body: `The driving interest of our lab is in the mechanisms by which cell-cell signaling pathways and transcriptional regulatory networks act to specify cell fates during animal development.` (supports identity only)
Prior equivalent source(s): `src-900c1b5e62983021` (https://biology.ucsd.edu/research/faculty/jposakony, 2026-10-16T01:07:39+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:53:25+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 44 · ordinal 814 · ucsd-biological-sciences-lab-reinagel-lab

Actual requested/final URI: [http://biology.ucsd.edu/research/faculty/preinagel](http://biology.ucsd.edu/research/faculty/preinagel); observedAt `2026-10-16T04:23:50+00:00`, liveCheckedAt `2026-10-16T04:23:50+00:00`; redirects `[]`.
New source `src-df39d9c8aa84eee7`; body SHA256 `d914a30ba9c9208b910655d648dc5dea8ee4aecc2a2059d87754b61fa6407e26`. Exact fetch match and cache hash verified.
Identity: 正文明确命名Reinagel lab，非仅凭faculty页姓名。
- body: `The Reinagel lab studies perceptually guided selection of action in the visually behaving rat.` (supports identity only)
Prior equivalent source(s): `src-2a37e9a7f413e90d` (https://biology.ucsd.edu/research/faculty/preinagel, 2026-10-16T01:07:39+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:53:25+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 45 · ordinal 820 · ucsd-electrical-and-computer-engineering-lab-ndao-lab

Actual requested/final URI: [http://ndao.ucsd.edu/](http://ndao.ucsd.edu/); observedAt `2026-10-16T04:23:52+00:00`, liveCheckedAt `2026-10-16T04:23:52+00:00`; redirects `[]`.
New source `src-05e3439d91255ff8`; body SHA256 `8e9d750bc17e80588c4ed968650d6082543008a149a47a0655d80991d25b487d`. Exact fetch match and cache hash verified.
Identity: 实际根页HTML标题字面为UCSD Ndao Lab，与既有已核验同站研究/成员证据一致；根正文出版简介不用于扩展科研内容。
- title: `UCSD Ndao Lab` (supports identity only)
Prior equivalent source(s): `src-1a3908f4fa43a1a8` (https://ndao.ucsd.edu/, 2026-10-16T01:07:34+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T03:21:31+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 46 · ordinal 826 · ucsd-structural-engineering-lab-m2do-multiscale-multiphysics-design-optimization-laboratory

Actual requested/final URI: [http://m2do.ucsd.edu/](http://m2do.ucsd.edu/); observedAt `2026-10-16T04:23:54+00:00`, liveCheckedAt `2026-10-16T04:23:54+00:00`; redirects `[]`.
New source `src-e7c58d10633a3d09`; body SHA256 `36c10b6dd4a7e4cd58ef0399d2242a26b9a8f5cf5e749976bcbc8e498a5f2b86`. Exact fetch match and cache hash verified.
Identity: 标题具名M2DO及正文Welcome to M2DO/We are a team共同确认目的页；只绑定已有实体，未改变实体类型。
- title: `Homepage | M2DO - Multiscale, Multiphysics Design Optimization` (supports identity only)
- body: `Welcome to M2DO! We are a team of interdisciplinary scientists and engineers with enthusiasm for computational modeling and optimization of engineering designs.` (supports identity only)
Prior equivalent source(s): `src-2f593178d7ed58f7` (https://m2do.ucsd.edu/, 2026-10-16T01:00:49+00:00; SHA equal=false, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:54:02+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.

## 47 · ordinal 833 · ucsd-structural-engineering-lab-fluid-effects-on-structural-systems-research-group-fessrg

Actual requested/final URI: [http://fessrg.ucsd.edu/](http://fessrg.ucsd.edu/); observedAt `2026-10-16T04:23:56+00:00`, liveCheckedAt `2026-10-16T04:23:55+00:00`; redirects `[]`.
New source `src-787541b8969257d3`; body SHA256 `53e1c2f1115ebeacb2b791a317746bd3361326f7ca033a50c4e229d3455fcd52`. Exact fetch match and cache hash verified.
Identity: 正文完整命名Fluid Effects on Structural Systems Research Group并以同一group连续描述。
- body: `Welcome to the research site of the Fluid Effects on Structural Systems Research Group from the University of California, San Diego.` (supports identity only)
Prior equivalent source(s): `src-be62b6c92d27644c` (https://fessrg.ucsd.edu/, 2026-10-16T01:00:51+00:00; SHA equal=true, full text/title equal=true).
Hydrate PASS; canCount false → true; scientific reviewedAt retained `2026-10-16T01:54:02+00:00`; identity binding reviewed `2026-10-16T04:27:36+00:00`. No blocker.
