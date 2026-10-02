# Public benchmark evidence study

Owner-directed research experiment, 2 October 2026. This is separate from the protected External Evidence Readiness Qualification. It does not qualify a deployment, change historical findings, or establish coverage/control effectiveness. See the repository ROADMAP.md and milestones/external-evidence-readiness/MILESTONE.md.

## Scope

Inspect MasDrift, Interbolt/AgentDojo, ITSMBench, CounselBench, Modus Financial Audit Bench trajectories and HealthAdminBench. Preserve native formats before introducing any collection change. Source revisions are fixed in `sources.lock.json`.

Measured results from the initial run:

- 12,843 Interbolt calls and decision events across 20 bundles; call records omit decision IDs and event timestamps. 5,752 call records have competition under a run/tool-only candidate key. This is not a measured vendor error rate.
- 5,850 Modus ATIF trajectories parsed; 213,828 tool observations. One call ID appears at two steps in one trace. Native step scoping resolves both. 8,261 nonzero command exits occur across 3,670 trajectories; those are not task-failure verdicts.
- 30 scripted native-tool workflow replays across five ITSM tasks and five Counsel matters, 1,378 calls. Separate client and target-process collectors retain their single-administrator limitation. No new model-driven run occurred.
- All five Counsel references pass its native verifier; all ten altered workflows fail. ITSM retries preserve final state but produce five failed duplicate calls.
- Four MasDrift native-monitor cases, nine record-ambiguity cases, five Health state/evaluator cases and a targeted Modus join probe pass. The Interbolt patch's exact recorder method is tested, but the complete live enforcement runtime is not rerun.
- 12,843 envelopes validate against existing AGG `action_evidence`; existing AGG assertion methods detect missing Interbolt IDs and correctly distinguish Modus session-level ambiguity from step-scoped linkage. The existing ten correlation-assertion tests pass at AGG revision `32500dc0725bc759f58810e273321f88220f1ac6`.

## Reproduction

Requires Python 3.12+, Git, Git LFS, network access for public source/dependency downloads and roughly 2 GB of working space. No model API key is needed. Run from this experiment directory:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
.venv/bin/python fetch_sources.py
.venv/bin/python inspect_records.py
.venv/bin/python collect_workflows.py
.venv/bin/python contract_probes.py
.venv/bin/python agg_compatibility.py --agg-root ../..
.venv/bin/python verify_outputs.py
```

The AGG root argument must point at a checkout with the existing correlation assertion module and schemas. For an exact reproduction, use the recorded AGG revision in a separate checkout. `inspect_records.py` scans the complete downloaded Modus corpus. No vendor model runs or LLM grading are invoked. Scripted replay uses reference actions intentionally; it must not be reported as an agent solving the tasks.

## Files and evidence boundaries

- `inspect_records.py`: native JSONL/gzip inventory and source byte references; no control finding inferred from benchmark outcomes.
- `evidence_adapter.py`: conservative record interpretation. Modus joins retain session and step context.
- `collect_workflows.py`: native tool replays in a separate target process; client attempts, target observations, policy snapshots, states and evaluator-only pairings remain distinct. The target snapshot collector is AGG-added instrumentation, not native enterprise telemetry. Counsel snapshots use internal world state.
- `contract_probes.py`: synthetic cases based on native formats. Experimental added identifiers remain labeled as added and are never presented as original published evidence.
- `agg_compatibility.py`: calls the unchanged AGG linker/validator. Missing actor, resource, execution time and outcome are not invented to force a record into the execution-event schema.
- `patches/interbolt-decision-reference.patch`: retains the already-existing decision ID in the call export. It is not applied to upstream or historical data. It improves a harness relationship, not independent assurance.
- `verify_outputs.py`: checks exact provenance bytes, state continuity, expected outcomes and generated Counsel compatibility.

Result paths distinguish native evidence, scripted observations, synthetic probes and AGG assertions. `oracle_pairings.jsonl` is evaluation-only and is never read by the matching adapter. Positive native linkage remains conditional on issuer/namespace declarations, exactly as existing AGG documents specify.

## Limits and remaining work

No model credentials were configured for new runs. HealthAdminBench is tested at schema/native-evaluator level, not through a browser agent. Modus grading reports and delivered workpapers were not joined, so task correctness is not inferred from traces. No independently administered target audit evidence, continuous clock applicability, logging completeness, live revocation/expiry, or actual overlapping-client experiment is demonstrated. Process separation and source hashes do not establish independent custody.

No protected roadmap status changes. A genuinely eligible external package and operator custody/coverage evidence are still required for the existing readiness milestone.

## Source rights

Public sources are fetched separately and retain their original licenses. No full third-party repositories or Modus trace corpus are checked into AGG. Derived Interbolt records originate from its Apache-2.0 repository; Counsel synthetic content is CC BY 4.0 and its code Apache-2.0. ITSMBench and HealthAdminBench repositories are Apache-2.0; MasDrift is MIT. Modus code is MIT, but this study does not infer the trajectory dataset's license from the code license or redistribute that corpus. Use source URLs and revisions for attribution and verify terms for any new use.
