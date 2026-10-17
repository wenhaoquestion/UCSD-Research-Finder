# 空方法字段应用计划独立QA

PASS。实际完成时间：2026-10-16T09:32:16+00:00。0必改项，未在磁盘应用。

- Plan SHA：`7b56fd88e283ddd395e5a769508e8d1eaef844c0adc72403defe8c2bc8bbdd29`
- Helper SHA：`4194cf18c22bae571c83a42da1479c0f855c29592c156cbd3836413b3f96e161`
- Shared helper SHA：`097076be5f33eeaa24136d0412d76f2a100e73e8a6e5a3424dbd1edcbce6e10d`
- Scope addendum SHA：`2c84fb63628f35c86d7a83861a884ea9394e95a2de860fbab53417d57103f863`

独立从三份获准草案、Smarr统一修订与两条interest-only提案重建全部168个newRecord，逐字段精确一致。166项中23条补40方法、29条新引文，143条追加限定已读范围的方法待核；另2条撤3个兴趣方法，仅重分类3处旧supports。611个source关联的原URI/time/bodySHA/textSHA及引文实际已读范围核对通过。

旧evidence前缀对166条完整保留；两兴趣修订保留全部旧quote/sourceID顺序和文本，只撤指定methods标签。新增引文只supports methods。原questions/questionFieldReview、问题待核尾部、root binding、identity、affiliation和其他非许可字段均保留。方法未知替换未触及问题、隶属或任职限制；110的实际修订时间及addendum provenance pointer正确。

23个不同方法证据source中，22个实际HTML字节及原sidecar请求URI、observedAt、SHA匹配（Ng使用已保留的original sidecar，snapshot时间未冒充capture时间）。另一项为既有官方900字符历史片段，其完整方法句与原field日期保留；bodySHA仍null，不声称原HTML已核或全文已读。

| 884条纯内存hydrate | before | after |
|---|---:|---:|
| supported / partial / unresolved | 738 / 56 / 90 | 738 / 56 / 90 |
| accepted lab/group | 724 | 724 |
| verified lab/group URL | 577 | 577 |
| 非空methods记录 | 584 | 605 |

884条URL核心（除reviewedAt和evidence外全部字段）精确不变；716条范围外raw与全部884 packet真实字节保持冻结。

最终helper的apply实际函数已在严格内存适配器下演练8项：

| 场景 | 结果 |
|---|---|
| 正常168条应用 | PASS：168 raw、169 journal内存写；完整168项journal |
| 完成后再次resume | PASS：0新增raw写，无重复引文/条目 |
| 第84条raw写完、对应journal尚未写时中断并恢复 | PASS：中断时84 raw/83 journal；最终168，唯一该项recoveredAfterRecordWrite=true且新digest补齐 |
| 最后第168条未知raw hash | PASS：任何raw/journal写入前拒绝，前167条不变 |
| QA passed=false | PASS：0写拒绝 |
| QA plan SHA不符 | PASS：0写拒绝 |
| helper pin不符 | PASS：0写拒绝 |
| component bytes不符 | PASS：0写拒绝 |

静态门禁核验：最终helper绑定plan/helper/shared helper、所有components、三份cross-QA与统一addendum SHA；首次atomic前完整检查168个old/new/current hash及全部packet和范围外raw。journal绑定plan并校验已应用条目digest；固定newRecord恢复不重新叠加字段。原owned-root临时文件、fsync及os.replace写法保持。现有430项生产测试receipt不覆盖这个helper，本报告依据上述独立演练与数据重建。

最终复查plan/helper/components SHA和884 raw/884 packet仍一致；真实application journal尚不存在。0网络、0 PS、0生产数据/代码/collector/shared写入，仅保存本QA报告。
