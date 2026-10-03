# UCSD 数据更新与质量报告

构建时间：2026-10-03T00:08:07+00:00。具体字段以各自 `observedAt` 为准。

## 记录覆盖

| 项目 | 原始快照 | 当前数据 |
|---|---:|---:|
| 教授记录 | 4335 | 4392 |
| Lab / research group | 545 | 616 |
| 有至少一个字段证据的教授 | 0 | 2748 |
| 有明确姓名匹配课程的教授 | 0 | 482 |
| 课程来源记录（可能同课多来源） | 0 | 1429 |
| 去重教授 × 课程 × 学期 | 0 | 1428 |
| 有 PI Review 分数的教授记录 | 0 | 16 |
| 有 Rate My Professors 分数的教授记录 | 0 | 1243 |

同一个人可能有多个院系任职记录；教授数和有分数记录数不是独立自然人数。部分字段得到核实不代表整个档案或现任职务得到核实。

## 字段证据覆盖

| 字段 | 教授记录数 |
|---|---:|
| name | 1793 |
| email | 1173 |
| personalWebsiteUrl | 722 |
| googleScholarUrl | 124 |
| researchSummary | 495 |
| researchAreas | 358 |
| labAffiliationUrl | 169 |
| catalogListing | 1088 |

## 清理的旧数据

所有被替换值见 `data/quality/legacy-remediation.json`，移出 lab 的个人研究主页和重复记录见 `quarantined-records.json`。

- researchAreas：4779 处修正。
- researchSummary：4023 处修正。
- labAffiliation：2244 处修正。
- labAffiliationUrl：2246 处修正。
- googleScholarUrl：67 处修正。
- email：1915 处修正。
- personalWebsiteUrl：125 处修正。
- recruitingStatus：1 处修正。
- recruitingEvidence：1 处修正。
- description：259 处修正。
- contactEmail：21 处修正。

## 来源检查与缺口

- `data/ucsd/lab-evidence.json`：官方教授主页、lab 目录、逐条抓取状态与证据。
- `data/ucsd/faculty-evidence.json`：当前院系目录、任职类别和交叉任职。
- `data/ucsd/teaching-evidence.json`：官方排课表、原文、来源日期、未匹配及仅姓候选。
- `data/ucsd/ratings-evidence.json`：两个平台的检索范围、样本数、身份匹配及失败状态。
- `data/ucsd/source-checks.json`：旧 lab URL 和 catalog 的 HTTP/robots 检查；HTTP 200 不证明网页内容最新。
- `data/ucsd/real-portal-resources.json`：完整公开分页列表，每页附实际抓取时间及 SHA-256。

- 来源可达性 `reachable`：766 个 URL。
- 来源可达性 `unavailable`：60 个 URL。
- 来源可达性 `http_error`：45 个 URL。
- 来源可达性 `robots_disallowed`：9 个 URL。
- `data/ucsd/lab-identity-review.json`：人工复核的新旧网址合并、研究所错误链接和研究组成员身份；Chien lab 的 Google 页面需要登录，不能把其 HTTP 200 当作公开可用。

## 本轮采集范围

- 官方个人页面：尝试 1784 条，确认姓名身份 1515 条；1572 条因网站限速等待后续采集。其余身份不符、HTTP 或 robots 失败逐条保留。
- 院系名册：9 个系、620 条目录记录，观察到 570 个教授档案；其中新增 31 条。
- 课程：34 个官方来源、0 个抓取失败；1429 条明确姓名匹配，735 条待核实候选，792 条未匹配。未覆盖院系或未匹配教授不代表没有授课。
- Rate My Professors：完成 4360 个不同姓名检索，1229 个独立有分页面。使用各精确姓名查询首个公开响应，不能保证平台内部所有同名页面均被返回。
- PI Review：读取 2202 个公开档案，其中 16 个有评价，共 17 条评价。
- REAL Portal：完整读取本次公开目录的 948 条记录，包括 co-curricular 项目。

各系覆盖数字和完整状态统计见 `data/quality/refresh-report.json`；原始来源、内容摘要与采集回执见上列证据文件。

## 如何解读

- UCSD Profiles 公开 robots 要求每请求间隔 10 秒。未完成的慢域页面标记 deferred，不能声称全部教授资料已重新核实。采集器支持缓存续跑及每轮预算。
- Catalog 页可能仍包含历史职务。`listed_undated` 只确认公开目录列名，不确认目前仍在职。
- `scheduled` 是来源公布的排课安排，可能改变；`historical` 是历史学期排课证据，不证明实际完成授课。仅姓匹配不进入已核实课程列表。
- PI Review 是科研导师评价来源，Rate My Professors 是授课评价来源。它们是匿名主观评价，不合并打分；没查到、无评价和抓取失败各自记录，分数缺失不是 0。
- 老的公共邮箱、导航 lab 关系、关键词推测和 Scholar 假链接已移除。保留但没有字段证据的旧值仍待核验。
- REAL 的 co-curricular 项目与研究机会保留独立类型；目录列出不等于正在招人。

## 复现

运行顺序和参数见 [README](../README.md)。核心逻辑检查：`python3 -m unittest discover -s tests -v`；完整数据检查：`python3 scripts/validate_data.py`。报告由离线合并器生成。
