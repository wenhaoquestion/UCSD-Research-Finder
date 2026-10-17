# Reviewed incremental handoff revision audit

Audited 2026-10-16T03:13:35+00:00 (UTC). This audit made zero network requests and no collector, guard, code, raw-record, packet, prepare/checkpoint or aggregate changes. The only writes are this report and two exact hash-verified approved snapshots.

**Finding: the current handoff contains the same approved twelve lab objects and evidence. Exactly three top-level metadata fields changed: generatedAt, queueCheckpointAt and queueStates. No new accepted lab ID, entity rename, URL change, subtype change, field-proof change, source capture change, alias/update change, PI inference or date-boundary promotion was found.** The existing hash guard correctly refused the changed producer artifact during the audit; this report itself does not admit the mutable revision.

## Exact artifact hashes

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| [Current mutable handoff](/tmp/ucsd-research-20261016/data/ucsd/coverage-20261016-reviewed-lab-handoff.json) | `3da7e44e96c40670285f7e22f5990c282329ebff6285f49b1936295a0aec6fe5` | 105901 |
| [Approved original handoff snapshot](/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/approved-handoff-snapshots/coverage-20261016-reviewed-lab-handoff-4e67f9bb4e7f4272932a22d262f36fc5818721fa51321c49c4bbb25080b1f726.json) | `4e67f9bb4e7f4272932a22d262f36fc5818721fa51321c49c4bbb25080b1f726` | 105874 |
| [Current bound decisions](/tmp/ucsd-research-20261016/data/ucsd/coverage-20261016-decisions.json) | `823f5b7c2f144e0906e31a69296f35b09f3e6e9ebbe9a4f88f220ccd1c6327d6` | 217190 |
| [Approved decisions snapshot](/private/tmp/ucsd-lab-summaries-20261016/data/local-lab-summaries/approved-handoff-snapshots/coverage-20261016-decisions-823f5b7c2f144e0906e31a69296f35b09f3e6e9ebbe9a4f88f220ccd1c6327d6.json) | `823f5b7c2f144e0906e31a69296f35b09f3e6e9ebbe9a4f88f220ccd1c6327d6` | 217190 |
| Served baseline atlas (collector and summary copies) | `ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e` | unchanged |

Current handoff decisionArtifactSha256 equals the exact bound decisions hash; servedAtlasSha256 equals the unchanged baseline hash. schemaVersion is 1, recordCount is 12, collectionState is reviewed_incremental, isFinalExport is false, servedAtlasModified is false. The frozen baseline remains 868 labs and the existing prepared manifest remains 880 eligible records with exactly 12 imports.

## Exact old-byte recovery

Read-only collector Git inspection returned no history for the handoff path; git status reports it untracked, and git ls-files has no handoff entry. The decisions path is tracked and locally modified relative to collector HEAD, but its current bytes exactly match the originally approved decision pin. Git history therefore did not supply the old handoff.

The original receipt and all twelve packet importProvenance objects preserve generatedAt=2026-10-16T02:35:08+00:00, queueCheckpointAt=2026-10-16T02:34:53+00:00 and the original handoffQueueCounts. In memory, the current JSON was restored to only those three metadata values, with its existing key order and exact two-space/UTF-8 JSON formatting plus terminal newline. The 105,874 candidate bytes matched the full original approved SHA-256 above **before any snapshot was written**, and the written bytes were hashed again. reviewedAliasCount stayed 30; testing 24 did not match and was discarded. This is a cryptographically exact approved-byte recovery, not an accepted approximate reconstruction.

The unchanged decisions bytes were separately hash-verified against the full 823f… pin before and after saving. Both approved files now live in the summary-owned approved-handoff-snapshots directory; no mutable collector file was restored or altered.

## Only changes in the mutable revision

| Field | Approved original | Current revision |
|---|---|---|
| generatedAt | 2026-10-16T02:35:08+00:00 | 2026-10-16T03:00:56+00:00 |
| queueCheckpointAt | 2026-10-16T02:34:53+00:00 | 2026-10-16T02:56:53+00:00 |
| queueStates | `{"done":3670,"unresolved":719,"retained_prior_evidence":1859,"pending":11496}` | `{"done":3689,"unresolved":699,"scope_excluded":377,"retained_prior_evidence":1859,"pending":11470}` |

All other top-level values, including the complete ordered labs array, labAliases, labUpdates, sourceManifest, recordCount, reviewedAliasCount, decisionArtifactSha256, servedAtlasSha256 and policy are deeply equal. The entire decisions artifact is byte-for-byte unchanged: 516 URL decisions, including exactly twelve accepts bound to the same frozen stable IDs and accepted URL keys. No additional accepted ID requires individual review for this revision. Other decision actions do not authorize summary imports.

The current queue is a separate later scope-audit snapshot: updatedAt `2026-10-16T03:13:27+00:00`, SHA-256 `ce21a8d3ccdf1a207c7d3cdb246881d27cf87df9e556c439a610e8e08782bb67`, counts `{"done":3804,"unresolved":700,"scope_excluded":301,"retained_prior_evidence":1859,"pending":11462,"running":1}`; the count of actual item states matches those counts. These later queue counts are not expected to equal either older handoff queue checkpoint. No queue checkpoint or generatedAt was substituted for a page observedAt, and neither handoff declares global completion.

## Twelve frozen objects and packet boundaries

| Stable lab ID | Name and accepted URL | Subtype | Department | PI / identity boundary | Literal field proofs matched |
|---|---|---|---|---|---:|
| `ucsd-live-lab-a8e8602372ef78` | [Democracy Lab](https://democracylab.ucsd.edu/) | research_group | Communication | Not found | 5 |
| `ucsd-live-lab-2982fe38ebc5a0` | [Howell Lab](https://moorescancercenter.ucsd.edu/about/centers-and-labs/howell-lab/index.html) | lab | Unknown (Moores Cancer Center; department not stated on fetched pages) | Not found | 5 |
| `ucsd-live-lab-8627bc69d4ee7d` | [Environmental Fluid Dynamics Lab](https://efdlab.ucsd.edu/home) | lab | Mechanical & Aerospace Engineering | G. Pawlak Tejada; initials_as_published; full-person identity unresolved | 6 |
| `ucsd-live-lab-33e60c6bf35e2b` | [Nemati Lab](https://www.nematilab.info/) | lab | Medicine | Not found | 5 |
| `ucsd-live-lab-d4a949e47ec3f3` | [The Herzik Research Group](https://herziklab.com/) | research_group | Chemistry & Biochemistry | Not found | 6 |
| `ucsd-live-lab-6244ff07b175a9` | [The Safe Autonomous Systems Lab](http://sylviaherbert.com/) | lab | Mechanical & Aerospace Engineering | Not found | 6 |
| `ucsd-live-lab-da307b4f0f98b5` | [Computational Phonology Research Group](https://sites.ucsd.edu/compphon/) | research_group | Linguistics | Not found | 6 |
| `ucsd-live-lab-f2a96ed0a66637` | [Pokorski Lab](https://www.pokorskilab.com/) | lab | NanoEngineering | Not found | 6 |
| `ucsd-live-lab-27d33fcd1710ce` | [Xtreme Materials Laboratory](https://graeve.ucsd.edu/) | lab | Mechanical & Aerospace Engineering | Not found | 6 |
| `ucsd-live-lab-f78bf84fc19eef` | [The Dutton Lab](http://www.theduttonlab.com/) | lab | Biological Sciences | Not found | 6 |
| `ucsd-live-lab-848c82d9aba60e` | [The Kit Pogliano Lab](https://kitpogliano.ucsd.edu/) | lab | Unknown | Not found | 5 |
| `ucsd-live-lab-176619ff4af12d` | [Mark H. Thiemens Research Group](https://thiemensgroup.ucsd.edu/) | research_group | Chemistry & Biochemistry | Not found | 6 |

All complete lab objects equal the approved original, including names, URLs, recordSubtype, sourceUrls, fieldEvidence, professor references, relationships, unknowns, assessments and contentDateNote. All twelve packets match the same original receipt and preserve the original approved sourceSha256; their listed name/URL/department/institution/subtype agree with the handoff, and importedUnknownsAndDateBoundaries exactly equal both the approved/current lab subset and the previous independent integration QA. All twelve packet preparedAt values remain 2026-10-16T02:49:32+00:00 and are separate from source observations.

- Eleven PI fields and all PI profile URLs remain Not found. Existing related faculty does not fill these unknowns.
- Environmental Fluid Dynamics preserves only “PI: G. Pawlak Tejada” and the exact scope initials_as_published; full-person identity unresolved. No expansion to a full person or professor ID was introduced.
- Herzik retains its existing Mark Herzik professor reference and relatedProfessorNames while its principalInvestigator remains Not found.
- Kit Pogliano department remains Unknown, with unresolved departmentAssessment and unverifiedFields including department; no department proof was added. Howell retains its complete unknown-department wording.
- Thiemens retains the explicit Last updated 01/05/2019 content-date note separate from its 2026 availability observation; no current operations claim is inferred.

## Source/raw/time/quotation consistency

Using the actual current collector queue, the unchanged guarded source validator independently verified all seventeen manifest captures: allowed cache path confinement and URL-derived filenames; exact raw-byte SHA-256; actual successful queue capture with original requested/final URL, observedAt and hash; valid UTC observations no later than handoff generation; and literal field quotation presence in the original legacy or visible-content extraction. All 68 field proofs point to a manifest URL/time and are exact substrings; no manifest entry is unreferenced.

Independently of that validator, all 68 original field proofs were located in the existing twelve packet sources with matching sourceUrl, original observedAt and exact text. All seventeen verified sourceManifest objects, including byteCount, equal the original import receipt. Original observation range remains 2026-10-16T00:57:22+00:00 through 2026-10-16T01:37:18+00:00. This verifies import provenance; it does not itself approve research summaries or convert directory navigation into research evidence.

| Official source | Original observedAt | Body SHA-256 |
|---|---|---|
| [https://communication.ucsd.edu/](https://communication.ucsd.edu/) | 2026-10-16T00:57:22+00:00 | `1e0af6c1395260d5b159d81d449b2bad4895e9bc0864e51fbe38482e023946f2` |
| [https://moorescancercenter.ucsd.edu/about/centers-and-labs/index.html](https://moorescancercenter.ucsd.edu/about/centers-and-labs/index.html) | 2026-10-16T00:59:03+00:00 | `d2c30417f359b01cc1a48d7e727b86aba6a75ab4fd6a41d3f36dc8ce8314395d` |
| [https://efdlab.ucsd.edu/](https://efdlab.ucsd.edu/) | 2026-10-16T01:01:24+00:00 | `3eaebeab7dd1501745b4309af2b7da0617eed6b129df0c0464e6a92334b7fa83` |
| [https://efdlab.ucsd.edu/home](https://efdlab.ucsd.edu/home) | 2026-10-16T01:02:28+00:00 | `bf1fb520197ffd6f1b673bc94a925d43f2af34ce6a0f90d6675349c3c11465a7` |
| [https://gpm.ucsd.edu/about/faculty.html](https://gpm.ucsd.edu/about/faculty.html) | 2026-10-16T01:01:40+00:00 | `31f5cb03f876e86b90ab7a83911bdb1a68870d19f1d04b7235404f155a5df4ee` |
| [https://mbtg.ucsd.edu/faculty/index.html](https://mbtg.ucsd.edu/faculty/index.html) | 2026-10-16T01:06:12+00:00 | `9fa0831d981fbedc7397c620c5843837c169f91bea37452bdf30a6b8923e1665` |
| [https://jacobsschool.ucsd.edu/faculty/profile?id=516](https://jacobsschool.ucsd.edu/faculty/profile?id=516) | 2026-10-16T01:08:34+00:00 | `61f8a3a21ba4ec267eacfd5deb6e83004425451c0006a2a194e5301e49b16ad8` |
| [https://sites.ucsd.edu/compphon/](https://sites.ucsd.edu/compphon/) | 2026-10-16T01:10:52+00:00 | `f9dfa37b19d860bd5fae4294120c5f826f86462be5d83c16905392ccea048090` |
| [https://linguistics.ucsd.edu/people/faculty/profiles/eric-bakovic.html](https://linguistics.ucsd.edu/people/faculty/profiles/eric-bakovic.html) | 2026-10-16T01:09:12+00:00 | `48b6d6c363cd96957a68ca2c668e7cc689d8cc80c87fd797236a0ac54f820e29` |
| [https://www.pokorskilab.com/](https://www.pokorskilab.com/) | 2026-10-16T01:37:07+00:00 | `7fff7e19656d86760f00c44b5f3e59114c82b247ced0be5d0aabe0129ca147ec` |
| [https://biomanufacturing.ucsd.edu/people](https://biomanufacturing.ucsd.edu/people) | 2026-10-16T01:29:05+00:00 | `f6d2664d4f159af80a185dcc0dfd20b332d13596c98cf59a16e6f97f3a750c12` |
| [https://graeve.ucsd.edu/](https://graeve.ucsd.edu/) | 2026-10-16T01:01:21+00:00 | `bad8b604a63c667331eccde839afac6dbacf750813a2fc61b32ca0d4ee406a39` |
| [https://imdd.ucsd.edu/faculty](https://imdd.ucsd.edu/faculty) | 2026-10-16T01:29:07+00:00 | `001ade6ee24529794147507d201a5b29c89c887017740b560f3a85a2cea26dd6` |
| [http://www.theduttonlab.com/](http://www.theduttonlab.com/) | 2026-10-16T01:37:10+00:00 | `8575d36e818620a018c0beaa5aa5b4b65a5b30bedee78e05f4139a8e5eb5fb0a` |
| [https://kitpogliano.ucsd.edu/](https://kitpogliano.ucsd.edu/) | 2026-10-16T01:37:18+00:00 | `14ae3848858bd04ce7d56c0ab022e4fbe13f8a22a262f94e5dd504d6f73acfc5` |
| [https://joepogliano.ucsd.edu/people/](https://joepogliano.ucsd.edu/people/) | 2026-10-16T01:30:23+00:00 | `d60a6b96968a54c98e288f8ef596a2bd7d2d9961bf577b331e8b62e655661096` |
| [https://thiemensgroup.ucsd.edu/](https://thiemensgroup.ucsd.edu/) | 2026-10-16T00:59:03+00:00 | `67015d450ceea3b3172f53126ee5016fb2658f7baaca4a28370c1e21cb27a6b7` |

## Scope and admission conclusion

The thirty alias objects and eight update objects are unchanged and remain ignored for these imports. Their canonical JSON hashes remain `1af0fc384fec38ceb5f6a30ba5cec00c781c734abb1b3fa19e3b59be650fc8b3` and `d752642a00cf4b86c1c0d6cfea3ff5ab55f9417064f41d61d3f72bb14c109548`, matching the prior integration audit. No baseline or faculty change was applied.

All thirteen reviewed identity mismatches remain nonaccepted; none of those IDs occurs in the frozen twelve. This audit leaves every mismatch gate and identity decision untouched.

The exact approved snapshots are suitable inputs for a parent-reviewed immutable admission path that retains all existing ID/decision/schema/raw-source/time/field-boundary checks and reports the mutable producer artifact hash separately. This report does not authorize additional IDs, aliases or updates from a future mutable artifact. Any changed decision set, lab payload, source proof or newly accepted ID still needs explicit individual review. The scope/queue metadata revision needs no new entity review for the already-approved twelve.

Read-only validation used the existing _validate_decisions and _validate_sources helpers without changing their pins or the guarded admission code. The original loader was also observed to fail closed on the mutable file with: Reviewed handoff SHA256 does not match audited pin. All audited collector handoff, decisions and queue bytes were unchanged across the validation pass.

## Addendum: independent frozen-snapshot loader review

Reviewed 2026-10-16T03:17:09+00:00 (UTC), read-only code/tests; this addendum is the only persistent edit. No actionable defect found. Reviewed module SHA-256 `eae6270918e7f975e5f93a8bde7f1774e2e281475477ee8dbae4c748d2da6272`, tests SHA-256 `6df3ed1fe69bde52ee12837768b4ba7b859696ae00ca285160e422a8d1c5aca1`.

Snapshot auto-selection is restricted to the production collection's resolved path; isolated fixture collections do not silently use production snapshots. Selection changes the input file only: handoff, decisions and baseline still undergo their original exact hash checks; duplicate-key/schema/non-final-state checks, the exact frozen ID/accept binding set, collision/PI/department guards, raw capture path/hash/original UTC-time checks and literal field-proof checks are unchanged. A selected corrupt or dangling snapshot fails closed without fallback. An absent snapshot can only fall back to a mutable file matching the original exact pin. Explicit snapshot-directory callers also remain bound to those same hashes and frozen IDs. All thirteen identity mismatch gates remain outside this twelve-ID batch.

`python -B -m unittest discover -s tests -p 'test_local_lab_handoff.py' -v` passed all **26 tests** offline. The new regeneration test changes both mutable labs and decisions to include an unreviewed ID; only the original fixture IDs return, and mutableRevisionAutomaticallyAdmitted stays false. Five additional ephemeral fixture checks passed: corrupt frozen decisions do not fall back, a dangling frozen handoff fails closed, frozen selection still rejects changed raw source bytes, a nonproduction collection ignores the production snapshot default, and absent snapshots retain only exact-pin mutable fallback. These checks wrote only their owned temporary fixture directories.

A production read-only load returned exactly twelve frozen IDs from the approved handoff/decision snapshots, verified seventeen raw sources and 68 exact field quotes, and retained sourceSha256 `4e67f9bb4e7f4272932a22d262f36fc5818721fa51321c49c4bbb25080b1f726`. The mutable producer SHA `3da7e44e96c40670285f7e22f5990c282329ebff6285f49b1936295a0aec6fe5` was reported separately; usesFrozenApprovedSnapshot was true and mutableRevisionAutomaticallyAdmitted was false. No prepare, projection, collection write or new network request was performed.
