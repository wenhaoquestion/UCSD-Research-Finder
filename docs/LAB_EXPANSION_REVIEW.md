# October 2026 UCSD lab expansion review

The served atlas adds **182 reviewed lab/research-group records**, increasing lab records from **686 to 868**. It fills verified principal-investigator fields in **19 existing records** and appends **4 sourced professor-record affiliations** (three distinct people; the baseline has two Brian Keating records). No existing lab or professor record was removed. The professor count remains **4,432**.

The baseline is commit `a3b8225f687b32f1fc5a7fe1f932ae8bc1cfe51c`. Research was captured on October 7, 2026. This is a bounded discovery pass, not a claim of exhaustive campus coverage or full verification of the legacy dataset.

## Evidence decisions

Lab identity, UCSD affiliation, PI leadership, website availability and recruiting are separate claims. Every accepted entity has an official UCSD source naming it or a reviewed link from an official page. A documented two-hop link chain supports SciMinds. Names on faculty rosters, contact lines and website links do not by themselves verify PI leadership.

Of the new records, **41 have explicit reviewed leadership evidence** and **141 retain `Not found` for PI**. The latter remain valid lab entities. There are **19 profile-only sources**, **2 shared department lab pages**, **3 personal-site lab pages**, and **158 lab websites**. Source-kind metadata and caveats prevent profile or shared-directory URLs from being represented as independently verified lab homepages. Three sites were unavailable (Bazhenov, ACES and Saygin); their UCSD directory evidence is retained along with the failed website status. No recruiting claims were inferred.

| Delivered discovery group | Accepted new labs |
| --- | ---: |
| chemistry | 48 |
| clinical | 40 |
| coordinator-neurosurgery-ophthalmology-astronomy | 14 |
| health-basic | 27 |
| physics-ece-se | 23 |
| social | 30 |

The candidate inventory contains **430 records**: **182 accepted new**, **19 accepted enrichments**, **136 duplicate/no new verified field**, **47 excluded**, and **46 unresolved**. Some rejected or unresolved candidate rows bundle multiple leads; these totals must not be interpreted as distinct-lab counts.

Cross-group repeats (Jinich, Ferguson, Schöneberg, Susan Taylor, Kummel and Cosmology) are counted once. DigiHealth is deferred pending comparison with the baseline Biosignals Processing Lab. Lukas Chavez is deferred because a current UCSD lab affiliation is not established against newer Sanford Burnham Prebys information. Unsupported name/URL changes and PI profile links were not applied.

## Scope and remaining gaps

Claude Code produced six discovery batches before its session quota stopped the research at approximately 23:13 UTC. GPT Codex independently reviewed the sources, corrected identity and leadership claims, completed the data pipeline, and ran validation. The original separate professor collection was not interrupted. Raw capture caches and task-session records were preserved locally and are not part of the public repository payload.

The Scripps and dedicated Jacobs CSE/MAE/Nanoengineering/Bioengineering batches were not delivered. Biology directories had access failures, and faculty personal pages were not exhaustively searched. The slow `profiles.ucsd.edu` domain was deliberately avoided to protect the separate collector. This pass therefore leaves further discovery work available.

Legacy identity issues remain outside the added-record count: Interactive Cognition/Kirsh has three baseline records, Joshi has unresolved aliases, and other baseline directory artifacts need separate review. The audit detects one same-PI multi-record group after the new leadership enrichment; it has no newly added member. A zero duplicate-URL result does not imply zero semantic aliases in the legacy data.

The rebuild also applies eight pre-existing professor identity-evidence timestamps from the already committed capture file. These update provenance only; they add no professor, change no biography, and do not read the concurrently running collector's latest output. Four other professor records gain the reviewed lab affiliations described above.

## Reproduction and validation

The canonical input is [lab-expansion-review.json](../data/ucsd/lab-expansion-review.json), with decisions and unresolved leads in [lab-expansion-candidates.json](../data/ucsd/lab-expansion-candidates.json). The offline builder is the only path from that review input to the served atlas. It rejects duplicate destinations, unsupported page types and unsourced claims; it preserves existing non-placeholder fields and multiple affiliations.

```sh
python3 scripts/rebuild_verified_atlas.py
python3 scripts/validate_data.py
python3 scripts/audit_research_atlas.py
python3 -m unittest discover -s tests -v
node tests/test_frontend_data.cjs
```

Validation completed locally: **122 Python tests passed**, frontend data checks passed, all **4,432 professors and 868 labs** passed schema/reference validation, **zero missing lab URLs**, **zero duplicate URL groups**, **zero suspicious URL-pattern matches**, and an in-memory full rebuild was identical. Baseline comparison confirmed **182 added / 0 removed / 19 changed lab records**.

Only the task branch `claude-lab-expansion-20261007` is intended for push. No workflow file is changed. Existing Pages deployment triggers on `main` or manual dispatch; the scheduled data-update workflow does not trigger on this task branch. Local checks do not imply GitHub CI ran or the website was deployed.
