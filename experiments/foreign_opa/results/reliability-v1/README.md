# Correlation reliability benchmark results

Executed 107 deterministic scenarios, with 20 distinct actor groups per scenario.
The matcher is unchanged; the inclusive window is fixed at 2 seconds.

| Workload | True pairs | Accepted | False links | Precision | Recall | Observable recall | Ambiguous | Unmatched |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Isolated, no skew | 20 | 20 | 0 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| Five simultaneous repetitions | 100 | 0 | 0 | — | 0.0% | 0.0% | 100.0% | 0.0% |
| Five repetitions, separation 2s | 100 | 0 | 0 | — | 0.0% | 0.0% | 100.0% | 0.0% |
| Five repetitions, separation 2s + 1ns | 100 | 100 | 0 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| Isolated, skew +2s | 20 | 20 | 0 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| Isolated, skew +2s + 1ns | 20 | 0 | 0 | — | 0.0% | 0.0% | 0.0% | 100.0% |
| Five repetitions, gap 5s, skew +5s | 100 | 80 | 80 | 0.0% | 0.0% | 0.0% | 0.0% | 20.0% |
| 25% journal loss | 20 | 15 | 0 | 100.0% | 75.0% | 100.0% | 0.0% | 14.3% |
| 50% journal loss | 20 | 10 | 0 | 100.0% | 50.0% | 100.0% | 0.0% | 33.3% |
| 50% journal replacement by impostors | 20 | 20 | 10 | 50.0% | 50.0% | 100.0% | 0.0% | 0.0% |
| 100% journal replacement by impostors | 20 | 20 | 20 | 0.0% | 0.0% | — | 0.0% | 0.0% |
| Complete evidence plus 100% journal impostors | 20 | 0 | 0 | — | 0.0% | 0.0% | 100.0% | 0.0% |

## Findings

- Complete, isolated observations match correctly. With zero skew, identical repetitions separated by at most the window become ambiguous; separation just above the window restores unique links.
- Isolated true pairs match at exactly ±2 seconds of skew and are unmatched one nanosecond beyond that boundary.
- Clock skew equal to the repetition interval can alias each event to the adjacent request. These wrong links are mutually unique: ambiguity is not a reliable warning signal.
- Missing evidence reduces end-to-end recall even when every observable true pair is recovered.
- Replacement impostors produce false accepted links without ambiguity. Extra impostors alongside intact true evidence instead cause abstention through ambiguity.

## Metrics and reproducibility

Precision = correct accepted links / all accepted links. Recall = correct accepted links / all planned true pairs, including missing counterparts. Observable recall uses only true pairs with both original records present. Undefined ratios are shown as — (JSON null).
Ambiguity and unmatched rates use all supplied observations across both sources as denominator. Each accepted link is counted once, from the OPA side. No pairwise true-negative accuracy is reported.

See [all scenario metrics](metrics.csv), [machine-readable results](results.json), [matcher-only inputs](matcher-inputs.json), [raw findings](findings.json), and [evaluator-only truth](ground-truth.json).

Inputs are synthetic normalized observations, not newly emitted native OPA logs. This benchmark characterizes the matching algorithm, not OPA, ingestion, custody, or production accuracy. Actor groups are controlled strata, not independent empirical samples. No confidence intervals or deployment thresholds are inferred.

Ground truth is held by the parent evaluator and written only after a separate matcher process exits. The worker receives only observation inputs and the window. It cannot consume truth through its interface; this is logical/process isolation, not an adversarial OS sandbox.

Matcher SHA-256 before and after: `1e89fc7276b000f29822791c57e8e8ca94904f33b374c59ed4b11457770cbdd0`.
No aggregate production precision is inferred by averaging arbitrarily selected scenarios.
