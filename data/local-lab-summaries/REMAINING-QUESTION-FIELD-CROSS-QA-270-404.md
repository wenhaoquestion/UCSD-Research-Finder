# 空白问题字段交叉QA：270–404

结论：PASS，必须同时采用已固定的3处独立最小修订。实际完成：2026-10-16T08:38:10+00:00。原草案与生产记录均未改动。

135/135完成：60条新增90问，75条unchanged。135组raw/packet SHA与inventory均一致；482个来源ID/原日期绑定通过，90条引文逐字且位于草案记录的已读范围。

| reviewIndex | 已解决的最小修订 |
|---|---|
| 306 | early/late proximal tubule应为解剖早段/晚段，非时间早期/晚期。 固定addendum改为近端肾小管早段与晚段，并忠实保留代谢及表达谱。 |
| 309 | 通路实验位于KMF卵巢癌模型语境，原问缺少模型限定。 固定addendum加入KMF卵巢癌模型并将同source连续引文扩展覆盖模型命名与通路目标。 |
| 380 | 原问缺少原文动物及具体疾病模型限定。 固定addendum仅第二问加入创伤性脑损伤/精神分裂症啮齿类模型，第一第三问及所有引文不变。 |

修订addendum SHA：`df38a162df6e98571d914706d8f0a8207345ae320b609a1b8933dd42285131d4`。原草案SHA：`589791856d29e6800ba30629da2ebc60ec53a5424d60424c1b9d7a2d4ba03c1e`。3修订不新增source、不改原capture日期或其他字段。

独立阅读范围：全部问题引文与局部语境、实体介绍及若干重点完整研究块；75条不变项核具体排除理由。JSON逐来源记录实际QA字符范围，未列范围不声称全文复核。未打开的HTML原bytes不冒称重新核算，bodySHA与冻结packet元数据核对。

历史来源边界：277 Serra、295 Muotri、375 Evans、376 Hook共4个引文的packet原bodySHA为null，原草案明确说明只保留历史官方摘录；保留其真实旧日期和null，不伪造原HTML验证。

全部观察与可能疗效的问法保持为待解问题；个人、新闻、教学、招募和邻近实验室材料不自动转给whole lab。原草案5个方法字段候选留待单独审核。

0网络请求，0PS，0raw/packet/code/collector/shared写入。

| reviewIndex | labId | QA |
|---|---|---|
| 270 | ucsd-live-lab-b86761fcdf0f8e | pass |
| 271 | ucsd-live-lab-f0c71cb8120b9f | pass |
| 272 | ucsd-live-lab-67708961680840 | pass |
| 273 | ucsd-live-lab-645dc3fc28a487 | pass |
| 274 | ucsd-live-lab-21f177ef8783df | pass |
| 275 | ucsd-live-lab-4fc6138e4ba4ec | pass |
| 276 | ucsd-live-lab-735fc644aa1d89 | pass |
| 277 | ucsd-live-lab-e927cea65b32ba | pass |
| 278 | ucsd-live-lab-d2b51912951305 | pass |
| 279 | ucsd-live-lab-43d5cbc6fe5e2a | pass |
| 280 | ucsd-live-lab-35ce4ed82d21ac | pass |
| 281 | ucsd-live-lab-0c7245ad11fac7 | pass |
| 282 | ucsd-live-lab-81abeaef71cf01 | pass |
| 283 | ucsd-live-lab-e0e4053bfb05e0 | pass |
| 284 | ucsd-live-lab-215e7df62b97f8 | pass |
| 285 | ucsd-live-lab-54f0ca446d4665 | pass |
| 286 | ucsd-live-lab-5db1834b7b663d | pass |
| 287 | ucsd-live-lab-a83d02395de2e9 | pass |
| 288 | ucsd-live-lab-f8efbf0bc12c5a | pass |
| 289 | ucsd-live-lab-92fa1b38b9541d | pass |
| 290 | ucsd-live-lab-a36c380ec359c5 | pass |
| 291 | ucsd-live-lab-c71c7e3b160200 | pass |
| 292 | ucsd-live-lab-94374f5e44bb8e | pass |
| 293 | ucsd-live-lab-3ecd40fc6caea9 | pass |
| 294 | ucsd-live-lab-0958eb5e1d52b6 | pass |
| 295 | ucsd-live-lab-977587ed98de04 | pass |
| 296 | ucsd-live-lab-4ee3ff2395c24d | pass |
| 297 | ucsd-live-lab-493c2d3c113de8 | pass |
| 298 | ucsd-live-lab-cd8819aec34b38 | pass |
| 299 | ucsd-live-lab-0fd0529e6aefbc | pass |
| 300 | ucsd-live-lab-89fc6b090f73fc | pass |
| 301 | ucsd-live-lab-6a2c26fd27d0cf | pass |
| 302 | ucsd-live-lab-ea11e11cc546c7 | pass |
| 303 | ucsd-live-lab-5f53b03a12eabf | pass |
| 304 | ucsd-live-lab-81890c1cb6a9e3 | pass |
| 305 | ucsd-live-lab-71fc1212f6a2cd | pass |
| 306 | ucsd-live-lab-4a70223ec89928 | pass_with_resolved_revision |
| 307 | ucsd-live-lab-bb12f4371563ae | pass |
| 308 | ucsd-live-lab-31d33ecb77aff1 | pass |
| 309 | ucsd-live-lab-42f190acde1ed8 | pass_with_resolved_revision |
| 310 | ucsd-live-lab-c28732356a85c1 | pass |
| 311 | ucsd-live-lab-f426b74f514b6d | pass |
| 312 | ucsd-live-lab-be884b2159a2f3 | pass |
| 313 | ucsd-live-lab-abd12eba39c46d | pass |
| 314 | ucsd-live-lab-86c289fa737e94 | pass |
| 315 | ucsd-chemistry-biochemistry-lab-burkart-laboratory | pass |
| 316 | ucsd-chemistry-biochemistry-lab-deshmukh-group | pass |
| 317 | ucsd-chemistry-biochemistry-lab-small-li-research-group-spectroscopy-and-microscopy-at-atomic-level-laboratory | pass |
| 318 | ucsd-chemistry-biochemistry-lab-mchugh-lab | pass |
| 319 | ucsd-chemistry-biochemistry-lab-paesani-research-group-laboratory-for-theoretical-and-computational-chemistry | pass |
| 320 | ucsd-chemistry-biochemistry-lab-ap-lab-applied-photochemistry-pun-lab | pass |
| 321 | ucsd-chemistry-biochemistry-lab-romero-polymer-lab | pass |
| 322 | ucsd-chemistry-biochemistry-lab-schimpf-lab | pass |
| 323 | ucsd-chemistry-biochemistry-lab-tor-lab | pass |
| 324 | ucsd-chemistry-biochemistry-lab-xiong-group | pass |
| 325 | ucsd-chemistry-biochemistry-lab-yong-lab | pass |
| 326 | ucsd-biochemistry-and-molecular-biophysics-lab-budin-lab-laboratory-of-lipid-biology-and-cell-membrane-biophysics | pass |
| 327 | ucsd-biochemistry-and-molecular-biophysics-lab-debelouchina-lab | pass |
| 328 | ucsd-biochemistry-and-molecular-biophysics-lab-devaraj-research-group | pass |
| 329 | ucsd-biochemistry-and-molecular-biophysics-lab-jinich-lab | pass |
| 330 | ucsd-biochemistry-and-molecular-biophysics-lab-joseph-lab | pass |
| 331 | ucsd-biochemistry-and-molecular-biophysics-lab-komives-lab | pass |
| 332 | ucsd-biochemistry-and-molecular-biophysics-lab-komor-lab | pass |
| 333 | ucsd-biochemistry-and-molecular-biophysics-lab-toor-lab | pass |
| 334 | ucsd-medicine-lab-amit-majithia-lab | pass |
| 335 | ucsd-medicine-lab-yury-miller-lab | pass |
| 336 | ucsd-medicine-lab-gupta-lab | pass |
| 337 | ucsd-medicine-lab-llorente-lab | pass |
| 338 | ucsd-medicine-lab-mittal-lab-neurogastroenterology-and-motility-laboratory | pass |
| 339 | ucsd-medicine-lab-yadlapati-lab | pass |
| 340 | ucsd-medicine-lab-singh-lab | pass |
| 341 | ucsd-medicine-lab-ziegler-lab | pass |
| 342 | ucsd-medicine-lab-akuthota-lab | pass |
| 343 | ucsd-medicine-lab-crotty-alexander-lab | pass |
| 344 | ucsd-medicine-lab-ramnath-lab | pass |
| 345 | ucsd-medicine-lab-bertin-lab | pass |
| 346 | ucsd-medicine-lab-kavanaugh-lab | pass |
| 347 | ucsd-medicine-lab-raz-lab | pass |
| 348 | ucsd-medicine-lab-broide-lab | pass |
| 349 | ucsd-medicine-lab-zuraw-lab | pass |
| 350 | ucsd-medicine-lab-tamayo-lab-computational-cancer-analysis-laboratory | pass |
| 351 | ucsd-medicine-lab-gerry-boss-laboratory | pass |
| 352 | ucsd-medicine-lab-golomb-research-group | pass |
| 353 | ucsd-orthopaedic-surgery-lab-muscle-biology-laboratory | pass |
| 354 | ucsd-unknown-moores-cancer-center-department-not-stated-on-fetched-pages-lab-carson-laboratory | pass |
| 355 | ucsd-medicine-lab-patel-lab-sandip-patel | pass |
| 356 | ucsd-surgery-lab-simeone-lab | pass |
| 357 | ucsd-ophthalmology-lab-afshari-lab | pass |
| 358 | ucsd-ophthalmology-lab-ayyagari-lab | pass |
| 359 | ucsd-ophthalmology-lab-baxter-lab | pass |
| 360 | ucsd-ophthalmology-lab-borooah-lab | pass |
| 361 | ucsd-ophthalmology-lab-shaw-lab | pass |
| 362 | ucsd-ophthalmology-lab-toomey-lab | pass |
| 363 | ucsd-ophthalmology-lab-wahlin-lab | pass |
| 364 | ucsd-astronomy-and-astrophysics-lab-experimental-cosmology-laboratory | pass |
| 365 | ucsd-astronomy-and-astrophysics-lab-high-energy-astrophysics-laboratory | pass |
| 366 | ucsd-astronomy-and-astrophysics-lab-ucsd-cool-star-lab | pass |
| 367 | ucsd-astronomy-and-astrophysics-lab-stellar-dynamics-compact-objects-group | pass |
| 368 | ucsd-astronomy-and-astrophysics-lab-galaxyhalo-group | pass |
| 369 | ucsd-pharmacy-and-pharmaceutical-sciences-lab-alle-et-al-lab | pass |
| 370 | ucsd-pharmacy-and-pharmaceutical-sciences-lab-gilson-lab | pass |
| 371 | ucsd-pharmacy-and-pharmaceutical-sciences-lab-kufareva-group | pass |
| 372 | ucsd-pharmacy-and-pharmaceutical-sciences-lab-lukowski-lab | pass |
| 373 | ucsd-pharmacy-and-pharmaceutical-sciences-lab-siegel-lab | pass |
| 374 | ucsd-pharmacy-and-pharmaceutical-sciences-lab-bandeira-lab | pass |
| 375 | ucsd-pharmacy-and-pharmaceutical-sciences-lab-evans-lab | pass |
| 376 | ucsd-pharmacy-and-pharmaceutical-sciences-lab-hook-laboratory | pass |
| 377 | ucsd-pharmacology-lab-jin-zhang-lab | pass |
| 378 | ucsd-pharmacology-lab-sunahara-lab | pass |
| 379 | ucsd-public-health-lab-tala-al-rousan-lab-displacement-and-health-research-center | pass |
| 380 | ucsd-psychiatry-lab-neural-engineering-and-translation-labs-neatlabs | pass_with_resolved_revision |
| 381 | ucsd-radiation-medicine-lab-daniel-simpson-lab | pass |
| 382 | ucsd-biological-sciences-lab-kadonaga-lab | pass |
| 383 | ucsd-biological-sciences-lab-yelon-lab | pass |
| 384 | ucsd-biological-sciences-lab-halpain-lab | pass |
| 385 | ucsd-biological-sciences-lab-posakony-lab | pass |
| 386 | ucsd-biological-sciences-lab-reinagel-lab | pass |
| 387 | ucsd-electrical-and-computer-engineering-lab-advanced-robotics-and-controls-lab-arclab | pass |
| 388 | ucsd-electrical-and-computer-engineering-lab-integrated-communication-circuits-lab-iccl | pass |
| 389 | ucsd-electrical-and-computer-engineering-lab-integrated-photonics-group-mookherjea-formerly-micro-nano-photonics-group | pass |
| 390 | ucsd-electrical-and-computer-engineering-lab-situational-awareness-laboratory | pass |
| 391 | ucsd-physics-lab-allen-lab-quantum-devices-and-imaging | pass |
| 392 | ucsd-physics-lab-shpyrko-research-group | pass |
| 393 | ucsd-structural-engineering-lab-m2do-multiscale-multiphysics-design-optimization-laboratory | pass |
| 394 | ucsd-structural-engineering-lab-lanza-di-scalea-s-group-experimental-mechanics-nde-shm-laboratory | pass |
| 395 | ucsd-structural-engineering-lab-mccartney-group | pass |
| 396 | ucsd-structural-engineering-lab-semnani-research-group | pass |
| 397 | ucsd-structural-engineering-lab-tehrani-group | pass |
| 398 | ucsd-structural-engineering-lab-tsampras-research-group | pass |
| 399 | ucsd-structural-engineering-lab-fluid-effects-on-structural-systems-research-group-fessrg | pass |
| 400 | ucsd-physics-lab-fusion-and-astrophysical-plasma-physics-group | pass |
| 401 | ucsd-electrical-and-computer-engineering-lab-wireless-communications-sensing-and-networking-group-wcsng | pass |
| 402 | ucsd-electrical-and-computer-engineering-lab-intelligence-control-and-adaptation-inception-research-laboratory | pass |
| 403 | ucsd-live-lab-a8e8602372ef78 | pass |
| 404 | ucsd-live-lab-da307b4f0f98b5 | pass |
