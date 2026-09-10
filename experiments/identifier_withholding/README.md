# M9a-i: identifier withholding — claim not demonstrated

The frozen experiment rejects using this contextual candidate rule to support downstream assurance. It accepted 47 edges: 25 correct and 22 false. Of 19 complete proposed governance–execution–outcome paths, 16 contained an incorrect association. All 39 governance focuses abstained at the assurance gate. No new M6 reconciliation or M7 attestation was issued. The implementation and matcher were not modified after results were observed.

## Frozen protocol and inspection

Protocol SHA-256: `3c166973460fe8111d4aa7fec411f32989eb1dde8458cf60dcdaa69e36807224`. Frozen at `2026-09-10T21:46:15.273094+00:00`, before implementation and experiment execution. See [PROTOCOL.md](PROTOCOL.md) and [freeze.json](freeze.json). The freeze is a local chronological record, not an independently authenticated timestamp.

Actual baseline HEAD: `b585c548a3b68e6611c1f7545f63e7bcfd05d845`. This differs from the conversation preview; this checkout has 291 tracked files and 15 schemas. The pre-existing untracked `tests/test_runtime_reconciler.py.save` was inventoried and left untouched.

Inspected M2 correlation/assertion code and reliability/ordinary-feature benchmarks, M6 ingestion/native correlation/reconciliation and audit paths, M7 verification/adjudication/experiment paths, their tests, and CI commands. M6 uses action-attempt IDs for G–E and NGINX request IDs for E–O. M6 replays full candidate populations; M7 verifies the preserved native archive before adjudication. Existing M2 results already expose replacement and skew failures, so this is an adversarial replication on M6-derived observations, not a blinded holdout claim.

## Method and evidence boundary

Reused the two complete M6 triples and the complete seven-record native population. The worker receives only actor, action, resource ID/type, observation timestamp, and an opaque source-local address. It calls the unchanged M2 correlator with exact fields, mutual uniqueness, and an inclusive one-second window on G–E and E–O separately. The existing operator identity mapping is explicitly applied before comparison; this is a favorable experimental assumption, not independently verified identity.

The preserved-population case only withholds fields and projects actors. The other eleven cases transform timestamps, replicate observations, omit counterparts or introduce identical-observation impostors. They are synthetic perturbations of existing evidence, not independently generated new events. Native IDs reconstruct scorer truth only in the evaluator. A separate worker receives unlabelled arrays over stdin; scorer truth is written only after worker exit. No labels, native IDs, raw envelopes, policy outcomes, source paths or truth enter decision inputs. Process isolation protects against accidental leakage, not hostile code.

## Results

The table pools the two edge types within each scenario; exact per-edge counts, observable recall and denominators are in [results.json](results/v1/results.json). False links count accepted edges once. Recall includes original pairs whose counterparts were removed. Correlation abstention counts non-MATCHED observations across each edge population; execution observations therefore appear on both edges. Undefined precision is not perfect precision.

| Scenario | Accepted | Wrong | Precision | Recall | False-link rate | Correlation abstention | Complete paths / wrong |
|---|---:|---:|---:|---:|---:|---:|---:|
| preserved_population | 3 | 0 | 100.00% | 75.00% | 0.00% | 33.33% | 1 / 0 |
| isolated | 4 | 0 | 100.00% | 100.00% | 0.00% | 0.00% | 2 / 0 |
| repetition | 0 | 0 | undefined | 0.00% | undefined | 100.00% | 0 / 0 |
| clock_skew_execution | 8 | 8 | 0.00% | 0.00% | 100.00% | 33.33% | 4 / 4 |
| clock_skew_outcome | 10 | 4 | 60.00% | 50.00% | 40.00% | 16.67% | 4 / 4 |
| clock_skew_outcome_negative | 10 | 4 | 60.00% | 50.00% | 40.00% | 16.67% | 4 / 4 |
| impostor_execution | 4 | 4 | 0.00% | 0.00% | 100.00% | 0.00% | 2 / 2 |
| impostor_outcome | 4 | 2 | 50.00% | 50.00% | 50.00% | 0.00% | 2 / 2 |
| missing_execution | 0 | 0 | undefined | 0.00% | undefined | 100.00% | 0 / 0 |
| missing_outcome | 2 | 0 | 100.00% | 50.00% | 0.00% | 33.33% | 0 / 0 |
| ambiguous_execution | 0 | 0 | undefined | 0.00% | undefined | 100.00% | 0 / 0 |
| ambiguous_outcome | 2 | 0 | 100.00% | 50.00% | 0.00% | 60.00% | 0 / 0 |

Pooled stress diagnostic: precision **53.19%** (25/47), recall **32.89%** (25/76), observable recall **39.06%** (25/64), false-link rate **46.81%** (22/47), correlation abstention **38.56%** (59/153). These are not estimated production rates.

The preserved population itself produces ambiguous G–E correlation for the two DENY observations sharing the same ordinary fields near the execution timestamp. Only the ALLOW triple forms a complete contextual path. Isolated cases recover both triples, but that does not distinguish them from identical-observation replacements. Skew aliases sequential actions into wrong mutually unique candidates. Repetition and competing impostors cause ambiguity; missing counterparts reduce recovery.

## Downstream outcome and stopping decision

All 39/39 governance focuses produce `ABSTAIN`, `finding=null`, with no M6 or M7 calls. Assurance abstention is 100%; assurance precision is undefined because there are no supported assertions. These are M9 gate decisions, not M7 `CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED` attestations or new verification receipts.

The fixed gate requires evidence of applicable clock/latency bounds and population coverage/non-replacement as well as mutually unique candidate edges. The fixed evidence set supplies no such guarantees. This implementation is explicitly a closed gate for the frozen corpus, not a general-purpose assurance-eligibility verifier. There is no scorer flag to enable adjudication.

The necessary candidate-quality screen failed because false accepted links occurred. The separate non-vacuity criterion—at least one eligible DENY path reaching genuine verified M7 adjudication—also was not satisfied. Therefore the preregistered claim is **NOT_DEMONSTRATED**. Safe abstention does not prove downstream assurance capability. No threshold adjustment, additional heuristic, M9a-ii work, or expanded infrastructure followed the failure.

## Reproduce

From the repository root, using its activated existing environment and a new output directory:

```sh
source .venv/bin/activate
python -B -m experiments.identifier_withholding.run_experiment run /tmp/agg-m9-new
python -B -m experiments.identifier_withholding.run_experiment audit experiments/identifier_withholding/results/v1
python -B -m pytest -p no:cacheprovider tests/test_identifier_withholding.py -q
RUN_FOREIGN_OPA=1 python -B -m pytest -p no:cacheprovider -q -rs
```

The runner refuses to overwrite existing outputs, verifies frozen baseline bytes, records implementation digests before the worker runs, and preserves the exact decision inputs/outputs and scorer truth. Audit regenerates inputs and truth and replays decisions and scores. Modifying a baseline file or frozen execution dependency invalidates this historical replay; use the baseline checkout plus these additions.

## Validation

Final validation evidence is recorded in [validation.json](validation.json). The first execution attempt stopped at import because the local environment lacked the already-pinned `rfc8785==0.1.4`; restoring that dependency required no requirements or code change and produced no experiment decisions. The first full regression attempt lacked Docker access and an activated `python` executable. These environment failures are recorded separately from completed checks.

## Exact additions

No existing tracked file was edited. New files:

```text
experiments/identifier_withholding/PROTOCOL.md
experiments/identifier_withholding/freeze.json
experiments/identifier_withholding/worker.py
experiments/identifier_withholding/run_experiment.py
experiments/identifier_withholding/README.md
experiments/identifier_withholding/validation.json
experiments/identifier_withholding/results/v1/PROTOCOL.md
experiments/identifier_withholding/results/v1/execution-lock.json
experiments/identifier_withholding/results/v1/decision-inputs.json
experiments/identifier_withholding/results/v1/decisions.json
experiments/identifier_withholding/results/v1/scorer-only-truth.json
experiments/identifier_withholding/results/v1/results.json
experiments/identifier_withholding/results/v1/manifest.json
tests/test_identifier_withholding.py
```

## Limits

This small, controlled corpus does not establish enterprise collision frequency or falsify every possible identifier-free correlation method. Synthetic construction is not new independent corroboration. Ordinary identity mapping remains cooperative; digests do not authenticate producers or prove completeness. No decision-time authority reconstruction or downstream control effectiveness is newly demonstrated here. Existing M6/M7 native-ID findings are preserved audit controls and must not be reported as M9 successes.
