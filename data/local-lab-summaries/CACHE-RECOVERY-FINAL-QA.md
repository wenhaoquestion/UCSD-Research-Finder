# Cache-recovery final integrity QA

Reviewed 2026-10-16T06:16:18+00:00; baseline `5f9a28e3cd523c3bd69e84f8de4e45b13622dff5`. **PASS. Zero QA requests; only this report pair written.**

10 existing records/packets changed: five scientific recoveries and five affiliation-only updates. No lab IDs were added. The 10 collector-source snapshots plus the already captured HighEnergy donor source account for 11 appended source objects.

**Snapshot provenance:** all 10 HTML bodies and original metadata copies are byte-identical to their collector originals. Body/metadata SHA256, actual requested/final URI, original observation time and source ID match packet bindings. Source.cachePath moved only for newly appended sources; originalCollectionCachePath remains explicit. Snapshot creation time is not a new observation. Tezcan’s recorded redirect remains tied to its actual request.

**Preservation:** all 10 packets keep the complete old source prefix, listed URL, original root fetch, preparedAt, root canonical/redirect fields and original last-check time. All 10 hydrate and every current evidence quote is a literal source-text substring.

| Existing-record change | Integrity result |
| --- | --- |
| `ucsd-astronomy-and-astrophysics-lab-high-energy-astrophysics-laboratory` — scientific_recovery | Complete original raw object preserved in history; old packet source prefix and root retained. |
| `ucsd-biology-topic-lab-nan-hao` — affiliation_only | Scientific core, identity, status, main reviewedAt and old evidence prefix exact; old affiliation retained. |
| `ucsd-chemistry-biochemistry-lab-tezcan-lab` — affiliation_only | Scientific core, identity, status, main reviewedAt and old evidence prefix exact; old affiliation retained. |
| `ucsd-chemistry-biochemistry-lab-theodorakis-group` — affiliation_only | Scientific core, identity, status, main reviewedAt and old evidence prefix exact; old affiliation retained. |
| `ucsd-chemistry-biochemistry-lab-yang-research-group-jerry-yang` — affiliation_only | Scientific core, identity, status, main reviewedAt and old evidence prefix exact; old affiliation retained. |
| `ucsd-linguistics-lab-mayberry-lab-for-multimodal-language-development` — scientific_recovery | Complete original raw object preserved in history; old packet source prefix and root retained. |
| `ucsd-linguistics-lab-phonetics-lab` — scientific_recovery | Complete original raw object preserved in history; old packet source prefix and root retained. |
| `ucsd-live-lab-98174ce75b39b1` — scientific_recovery | Complete original raw object preserved in history; old packet source prefix and root retained. |
| `ucsd-live-lab-bf194dbf29f17f` — scientific_recovery | Complete original raw object preserved in history; old packet source prefix and root retained. |
| `ucsd-live-lab-8faf85a74eb832` — affiliation_only | Scientific core, identity, status, main reviewedAt and old evidence prefix exact; old affiliation retained. |

Benner is the fifth affiliation-only update: its 51,722-character source was checked for extraction/hash/quote integrity; original affiliation and uncertainty are retained. The outdated truncated-summary uncertainty was clarified without changing scientific fields or their original review time. The separate HTTP success does not repair the original HTTPS failure.

**Final manifest proof:** parent refresh checked 2026-10-16T06:14:32+00:00. Independently verified all **884/884** sourceCounts against packets and all **884/884** current packet SHA256 values against the before/after receipt. Nine stale rows were refreshed in the final prepare; 10 sourceCount rows changed since 5f9. There are **zero stale rows**. Other item fields, IDs, ordinals, listed URLs, order and imports remain unchanged. All 10 audited packet/record hashes still match their phase-one checks.

**No network delta:** the entire own ledger is byte-identical to 5f9: **344 wires / 202 receipts**. All **14 mismatch decision objects** are unchanged. Cache reuse and snapshot copying introduced no wire, alias, migration or identity-gate override.

Phase-one snapshots/root/history checks occurred at 2026-10-16T06:11:58+00:00; Benner was added at 2026-10-16T06:13:53+00:00. The then-pending 8/9 stale sourceCounts were explicitly provisional and are now closed by the final proof. Parent performs final projection validation separately.
