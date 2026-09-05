# Ordinary evidence feature benchmark

8,560 measurements: 107 existing scenarios × 5 evidence profiles × 16 feature sets.
20 actor groups per scenario, fixed two-second window, fixed seed. Baseline code and results are preserved.

## False-link-first screen

Counts below sum the deliberately selected stress scenarios, not a production distribution.
A zero-false-link feature set must also accept at least one correct link to qualify.

| Profile | Feature set | False accepted links | Scenarios with false links | Correct accepted links |
|---|---|---:|---:|---:|
| varied | baseline | 580 | 20 | 1150 |
| varied | client_app | 191 | 23 | 2028 |
| varied | source_ip | 236 | 23 | 2065 |
| varied | request_parameters | 222 | 24 | 2036 |
| varied | resource_version | 267 | 24 | 1854 |
| varied | client+ip | 65 | 18 | 2555 |
| varied | parameters+version | 83 | 20 | 2509 |
| varied | all-four | 5 | 5 | 2786 |
| varied | client_app+request_parameters | 50 | 15 | 2562 |
| varied | client_app+resource_version | 68 | 17 | 2511 |
| varied | source_ip+request_parameters | 66 | 19 | 2574 |
| varied | source_ip+resource_version | 94 | 20 | 2501 |
| varied | client_app+source_ip+request_parameters | 18 | 12 | 2735 |
| varied | client_app+source_ip+resource_version | 22 | 11 | 2726 |
| varied | client_app+request_parameters+resource_version | 19 | 11 | 2742 |
| varied | source_ip+request_parameters+resource_version | 24 | 10 | 2730 |
| same_context | baseline | 580 | 20 | 1150 |
| same_context | client_app | 580 | 20 | 1150 |
| same_context | source_ip | 580 | 20 | 1150 |
| same_context | request_parameters | 580 | 20 | 1150 |
| same_context | resource_version | 580 | 20 | 1150 |
| same_context | client+ip | 580 | 20 | 1150 |
| same_context | parameters+version | 580 | 20 | 1150 |
| same_context | all-four | 580 | 20 | 1150 |
| same_context | client_app+request_parameters | 580 | 20 | 1150 |
| same_context | client_app+resource_version | 580 | 20 | 1150 |
| same_context | source_ip+request_parameters | 580 | 20 | 1150 |
| same_context | source_ip+resource_version | 580 | 20 | 1150 |
| same_context | client_app+source_ip+request_parameters | 580 | 20 | 1150 |
| same_context | client_app+source_ip+resource_version | 580 | 20 | 1150 |
| same_context | client_app+request_parameters+resource_version | 580 | 20 | 1150 |
| same_context | source_ip+request_parameters+resource_version | 580 | 20 | 1150 |
| colliding_impostors | baseline | 580 | 20 | 1150 |
| colliding_impostors | client_app | 365 | 24 | 1944 |
| colliding_impostors | source_ip | 381 | 24 | 1965 |
| colliding_impostors | request_parameters | 377 | 24 | 1943 |
| colliding_impostors | resource_version | 416 | 24 | 1774 |
| colliding_impostors | client+ip | 271 | 23 | 2443 |
| colliding_impostors | parameters+version | 278 | 24 | 2400 |
| colliding_impostors | all-four | 224 | 18 | 2666 |
| colliding_impostors | client_app+request_parameters | 261 | 22 | 2451 |
| colliding_impostors | client_app+resource_version | 272 | 23 | 2400 |
| colliding_impostors | source_ip+request_parameters | 267 | 24 | 2458 |
| colliding_impostors | source_ip+resource_version | 287 | 23 | 2390 |
| colliding_impostors | client_app+source_ip+request_parameters | 234 | 22 | 2617 |
| colliding_impostors | client_app+source_ip+resource_version | 237 | 21 | 2607 |
| colliding_impostors | client_app+request_parameters+resource_version | 235 | 21 | 2625 |
| colliding_impostors | source_ip+request_parameters+resource_version | 240 | 21 | 2612 |
| missing25 | baseline | 580 | 20 | 1150 |
| missing25 | client_app | 146 | 24 | 1559 |
| missing25 | source_ip | 189 | 23 | 1578 |
| missing25 | request_parameters | 166 | 23 | 1558 |
| missing25 | resource_version | 199 | 24 | 1410 |
| missing25 | client+ip | 35 | 16 | 1449 |
| missing25 | parameters+version | 45 | 16 | 1409 |
| missing25 | all-four | 0 | 0 | 897 |
| missing25 | client_app+request_parameters | 25 | 11 | 1457 |
| missing25 | client_app+resource_version | 30 | 12 | 1419 |
| missing25 | source_ip+request_parameters | 42 | 17 | 1457 |
| missing25 | source_ip+resource_version | 52 | 18 | 1425 |
| missing25 | client_app+source_ip+request_parameters | 4 | 4 | 1171 |
| missing25 | client_app+source_ip+resource_version | 5 | 5 | 1173 |
| missing25 | client_app+request_parameters+resource_version | 4 | 4 | 1146 |
| missing25 | source_ip+request_parameters+resource_version | 13 | 7 | 1146 |
| disagree25 | baseline | 580 | 20 | 1150 |
| disagree25 | client_app | 237 | 43 | 1444 |
| disagree25 | source_ip | 259 | 40 | 1505 |
| disagree25 | request_parameters | 245 | 41 | 1459 |
| disagree25 | resource_version | 305 | 40 | 1354 |
| disagree25 | client+ip | 91 | 33 | 1395 |
| disagree25 | parameters+version | 112 | 35 | 1347 |
| disagree25 | all-four | 11 | 9 | 850 |
| disagree25 | client_app+request_parameters | 86 | 29 | 1370 |
| disagree25 | client_app+resource_version | 116 | 40 | 1390 |
| disagree25 | source_ip+request_parameters | 97 | 34 | 1376 |
| disagree25 | source_ip+resource_version | 127 | 36 | 1382 |
| disagree25 | client_app+source_ip+request_parameters | 31 | 18 | 1104 |
| disagree25 | client_app+source_ip+resource_version | 41 | 23 | 1153 |
| disagree25 | client_app+request_parameters+resource_version | 36 | 18 | 1111 |
| disagree25 | source_ip+request_parameters+resource_version | 39 | 25 | 1095 |

## Representative outcomes

P = precision; R = end-to-end recall; A/U = ambiguous/unmatched observation rates. — means undefined.

| Profile | Workload | Features | P | R | False links | A | U |
|---|---|---|---:|---:|---:|---:|---:|
| colliding_impostors | repetition | all-four | 100.0% | 96.0% | 0 | 4.0% | 0.0% |
| colliding_impostors | repetition | baseline | — | 0.0% | 0 | 100.0% | 0.0% |
| colliding_impostors | clock alias | all-four | 0.0% | 0.0% | 1 | 0.0% | 99.0% |
| colliding_impostors | clock alias | baseline | 0.0% | 0.0% | 80 | 0.0% | 20.0% |
| colliding_impostors | 50% loss | all-four | 100.0% | 50.0% | 0 | 0.0% | 33.3% |
| colliding_impostors | 50% loss | baseline | 100.0% | 50.0% | 0 | 0.0% | 33.3% |
| colliding_impostors | full replacement | all-four | 0.0% | 0.0% | 20 | 0.0% | 0.0% |
| colliding_impostors | full replacement | baseline | 0.0% | 0.0% | 20 | 0.0% | 0.0% |
| disagree25 | repetition | all-four | 96.7% | 29.0% | 1 | 3.0% | 67.0% |
| disagree25 | repetition | baseline | — | 0.0% | 0 | 100.0% | 0.0% |
| disagree25 | clock alias | all-four | — | 0.0% | 0 | 0.0% | 100.0% |
| disagree25 | clock alias | baseline | 0.0% | 0.0% | 80 | 0.0% | 20.0% |
| disagree25 | 50% loss | all-four | 100.0% | 25.0% | 0 | 0.0% | 66.7% |
| disagree25 | 50% loss | baseline | 100.0% | 50.0% | 0 | 0.0% | 33.3% |
| disagree25 | full replacement | all-four | — | 0.0% | 0 | 0.0% | 100.0% |
| disagree25 | full replacement | baseline | 0.0% | 0.0% | 20 | 0.0% | 0.0% |
| missing25 | repetition | all-four | 100.0% | 34.0% | 0 | 2.0% | 64.0% |
| missing25 | repetition | baseline | — | 0.0% | 0 | 100.0% | 0.0% |
| missing25 | clock alias | all-four | — | 0.0% | 0 | 0.0% | 100.0% |
| missing25 | clock alias | baseline | 0.0% | 0.0% | 80 | 0.0% | 20.0% |
| missing25 | 50% loss | all-four | 100.0% | 20.0% | 0 | 0.0% | 73.3% |
| missing25 | 50% loss | baseline | 100.0% | 50.0% | 0 | 0.0% | 33.3% |
| missing25 | full replacement | all-four | — | 0.0% | 0 | 0.0% | 100.0% |
| missing25 | full replacement | baseline | 0.0% | 0.0% | 20 | 0.0% | 0.0% |
| same_context | repetition | all-four | — | 0.0% | 0 | 100.0% | 0.0% |
| same_context | repetition | baseline | — | 0.0% | 0 | 100.0% | 0.0% |
| same_context | clock alias | all-four | 0.0% | 0.0% | 80 | 0.0% | 20.0% |
| same_context | clock alias | baseline | 0.0% | 0.0% | 80 | 0.0% | 20.0% |
| same_context | 50% loss | all-four | 100.0% | 50.0% | 0 | 0.0% | 33.3% |
| same_context | 50% loss | baseline | 100.0% | 50.0% | 0 | 0.0% | 33.3% |
| same_context | full replacement | all-four | 0.0% | 0.0% | 20 | 0.0% | 0.0% |
| same_context | full replacement | baseline | 0.0% | 0.0% | 20 | 0.0% | 0.0% |
| varied | repetition | all-four | 100.0% | 96.0% | 0 | 4.0% | 0.0% |
| varied | repetition | baseline | — | 0.0% | 0 | 100.0% | 0.0% |
| varied | clock alias | all-four | 0.0% | 0.0% | 1 | 0.0% | 99.0% |
| varied | clock alias | baseline | 0.0% | 0.0% | 80 | 0.0% | 20.0% |
| varied | 50% loss | all-four | 100.0% | 50.0% | 0 | 0.0% | 33.3% |
| varied | 50% loss | baseline | 100.0% | 50.0% | 0 | 0.0% | 33.3% |
| varied | full replacement | all-four | — | 0.0% | 0 | 0.0% | 100.0% |
| varied | full replacement | baseline | 0.0% | 0.0% | 20 | 0.0% | 0.0% |

## Minimum sufficient set

- varied: no tested feature set eliminates false accepted links across the sweep.
- same_context: no tested feature set eliminates false accepted links across the sweep.
- colliding_impostors: no tested feature set eliminates false accepted links across the sweep.
- missing25: smallest tested qualifying sets: all-four. This is conditional on this finite workload.
- disagree25: no tested feature set eliminates false accepted links across the sweep.

No sufficient ordinary feature set is established across all profiles. Identical ordinary observations can belong to different actions. More exact fields can reduce collisions, but cannot prove identity when missing counterparts have observationally identical replacements.
Stronger evidence or explicit abstention assumptions are needed for a zero-silent-error claim. This does not establish that ML/probabilistic matching is necessary or that it can solve indistinguishability.

See [every metric row](metrics.csv), [results and hashes](results.json), and [methodology](../../FEATURE_BENCHMARK.md).
Compressed matcher inputs, raw findings, and evaluator-only truth are retained alongside the report. These are synthetic contextual observations; enterprise availability, independence, and normalization have not been validated.
