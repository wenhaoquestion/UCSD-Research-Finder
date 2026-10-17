# Reviewed16 handoff delta review

**Source-supported delta; no admission performed.** Actual review: 2026-10-16T04:58:03+00:00. Network requests: **0**.

Mutable handoff SHA `49c5aa9c7864e67553ec8c4f6273e57284dd204ab13d42dc1f8c98197ae24776`, generated `2026-10-16T04:46:40+00:00`: **16 entities /28 sources /100 field-proof instances**. Decisions SHA `780a47cabd7b2c6b21b126927244d1fecb5fb3705100ae872d43f0fed5a116c1` matches its binding. Both remain schema1; handoff is reviewed_incremental, isFinalExport=false, with 10899 pending at checkpoint.

Old14 lab objects, old26 manifest entries,30 aliases and8 updates are exactly unchanged. All28 raw hashes/original queue tuples were checked; only the2 new primary bodies were semantically read in full. All14 new field-proof instances match literally. Prior86 proof semantics are reused after unchanged records/hash verification; no16 importer load was claimed.

## Named entities and shared resource

The parent decision remains URL-keyed at `https://www.ucsdrobotics.org/`, with new action accept_shared_entities and two nested sharedEntities keyed by stableLabId. Effective importer entity binding must use (parent URL, stableLabId), not URL alone. The exact shared groupId is `ucsd-shared-homepage-802bc4f0642435`.

- **Flow Control Lab — `ucsd-live-lab-802bc4f0642435`**: 流体系统分析、估计、预测、优化与控制；原文明示高级分析工具和数值方法。不能将另一个实验室的机器人制作技术并入。
  Exact whole-lab prose: “The UCSD Flow Control Lab , founded in 1998, investigates a range of questions ranging from fundamental to applied, including the development of advanced analysis tools and numerical methods to better understand, optimize, estimate, forecast, and control fluid systems.”
- **Coordinated Robotics Lab — `ucsd-live-lab-7df54236890322`**: 低成本机器人车辆的机动性与协调；原文明示动力学模型、反馈控制及手机级/IoT、定制PCB、3D打印原型。不能将流体系统目标并入。
  Exact whole-lab prose: “The UCSD Coordinated Robotics Lab , founded in 2004, investigates the mobility and coordination of low-cost robotic vehicles, leveraging dynamic models and feedback control, with prototypes built using cellphone-grade and IoT technologies, custom PCBs, and 3D printing.”

The official Jacobs profile labels and links both labs to the same homepage, then says “He directs two distinct research laboratories .” The root separately describes them and explicitly says “The two labs collaborate closely”. They are two entities sharing one resource. Individual fluid-control versus robotic-mobility research must stay scoped; shared swarm collaborations do not merge their identities.

| Official primary source | Original observedAt | Raw SHA-256 |
| --- | --- | --- |
| [https://www.ucsdrobotics.org/](https://www.ucsdrobotics.org/) | `2026-10-16T01:08:35+00:00` | `a961afcb796d1106489b68ff10a961d03b982af4205ff1e502994669f546ba1e` |
| [https://jacobsschool.ucsd.edu/faculty/profile?id=64](https://jacobsschool.ucsd.edu/faculty/profile?id=64) | `2026-10-16T01:08:32+00:00` | `7e99fe9808e5db5c8a352d65482a160fc147d24510dce430b35fd21a4f38d1bd` |

These are old actual cached captures newly included in a semantic handoff revision, not new live observations. Both named /flow-control-lab and /coordinated-robotics-lab anchors were observed, not fetched. The public homepage states publication PDFs require signup/login; no PDF/login was accessed.

## Fields and professor boundary

No new stable ID or lab URL collides with baseline868 or frozen14. Only the reviewed pair duplicates a within-batch URL:16 entities use15 unique batch URLs. Schema and combined references pass. Both records preserve PI/profile Not found and professorIds=[].

Jacobs primary prose says Thomas Bewley Professor, MAE and directs/links the two labs, supporting the reviewed MAE association. Baseline contains ucsd-faculty-thomas-bewley labelled CSE and ucsd-mechanical-aerospace-engineering-t-bewley labelled MAE. Neither professor ID may be inferred; no baseline person fields are repaired here.

## Minimum safe16 importer gates

1. **Exact frozen16 artifact scope**: Pin the reviewed 49c5aa... handoff and 780a47... decisions in new approved snapshots. Require exact16 IDs/count, schema1, baseline868/hash, reviewed_incremental/non-final/servedAtlasModified=false; retain old snapshots and completed-export gate.
2. **Explicit nested entity bindings**: Keep ordinary accept processing unchanged. Recognize accept_shared_entities only at the exact reviewed URL/groupId. Flatten sharedEntities with (parent URL, stableLabId), require exact two IDs/names/reasons and nonempty unique per-entity identityEvidence, and require accepted ID set exactly frozen16. No synthetic source URLs or fragment identities.
3. **Finite URL collision exception**: Continue rejecting every baseline URL collision unconditionally. Allow only the duplicate among these two exact new-batch IDs at https://www.ucsdrobotics.org/ and fixed groupId after all pair checks. No unrelated pair, third member, alternate alias or other URL gets an exception.
4. **Complete identical websiteSharing**: Both records must carry identical fixed kind/groupId/exact unique two-member set/evidence. Require parent sharingEvidence == each websiteSharing.evidence == each fieldEvidence.websiteSharing; each own distinct named identityEvidence must equal that record fieldEvidence.labName. Reject one-sided/incomplete sharing, swapped ID/name or broad shared prose used instead of own identity.
5. **Keep actual source validation**: Keep safe cache paths/filename, actual requested/final URL, original observedAt, body SHA and exact quotes for all28 sources/100 field-proof instances. Validate the extra parent/top-level sharing proof arrays too. Shared-root tuple is 01:08:35/a961af... and Jacobs tuple 01:08:32/7e99fe...; these are old captures newly included, not new wire observations.
6. **No person, alias or acceptance inference**: For this pair preserve PI/profile Not found and professorIds=[]; do not adopt the inconsistent baseline professor CSE department. Retain primary-source MAE/UCSD statements, ignore30 aliases/8 updates and preserve all13 mismatch gates.
7. **Append only2 after explicit authorization**: After guard/tests approval append only these2 IDs with existing append-only prepare. Preserve old882 raw/packet bytes, order, IDs, dates and provenance. Baseline868+16 means884 records. Shared source provenance may match in both packets, but each identity/scientific summary must remain separately named and scoped.
8. **Entity count distinct from URL count**: Reviewed batch contains16 entities but15 unique normalized lab URLs. Two labs share one web resource; do not claim16 unique endpoints or resolve a URL-only faculty link to an arbitrary member.

Focused tests before enabling16:

- Positive exact frozen pair accepted; all other duplicate URL groups rejected.
- Wrong pins/count/ID, missing or extra member, third member or wrong URL/groupId fails closed.
- Missing own identity, swapped ID/name, different sharing evidence, incomplete membership or unilateral websiteSharing fails.
- Stale source time/hash, altered raw body, missing actual queue capture or nonliteral parent sharing proof fails.
- Baseline URL collision remains a hard failure, including with a sharing object.
- PI/professor links silently added or alias/update application fails.
- Append-only old882 order/bytes/dates preserved and exactly2 appended.

The current stable14 guard remains untouched at 60ff319a0528908097ce5d53955017a04fab5e3a12e2cd1385349e2ffaed6155. New frozen snapshots, a finite pair-aware exception and tests require explicit implementation/authorization. Removing URL-collision validation generally is unsupported.
