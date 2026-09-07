# M8 Gate A results

GRAPH_SEMANTIC_VALUE = **NOT_DEMONSTRATED**

GRAPH_DATABASE_VALUE = **NOT_TESTED**

Frozen protocol SHA-256: `c9d6cbd538303fdab07731490ce6d986c81ae56b4919593ae8c130dbe015f501`

These timing/resource thresholds are experimental offline acceptability limits, not product SLOs.

## Decision basis

- Graph-owned topology/query/projector code did not meet the frozen 30% reduction threshold; non-LOC improvements alone cannot pass.

## Correctness

Gate A: 51 tests, 0 failures, 0 errors, 0 skipped.
Regression: 321 tests, 0 failures, 0 errors, 5 skipped.

## Benchmark

| Tier | Actual relationships | Arm/query | Warm p50 / p95 (s) | Cold max (s) | Index build p50 (s) |
|---|---:|---|---:|---:|---:|
| reference | 1039 | baseline/Q1 | 0.0394 / 0.0428 | 4.547 | 0.0062 |
| reference | 1039 | baseline/Q2 | 0.0010 / 0.0019 | 6.290 | 0.0060 |
| reference | 1039 | baseline/Q3 | 0.0011 / 0.0013 | 6.257 | 0.0062 |
| reference | 1039 | baseline/Q4 | 0.0003 / 0.0004 | 4.500 | 0.0060 |
| reference | 1039 | graph/Q1 | 0.0400 / 0.0457 | 4.526 | 0.0198 |
| reference | 1039 | graph/Q2 | 0.0011 / 0.0021 | 6.226 | 0.0195 |
| reference | 1039 | graph/Q3 | 0.0011 / 0.0014 | 6.172 | 0.0200 |
| reference | 1039 | graph/Q4 | 0.0003 / 0.0003 | 4.484 | 0.0192 |
| 10000 | 10841 | baseline/Q1 | 0.0399 / 0.0425 | 5.114 | 0.0732 |
| 10000 | 10841 | baseline/Q2 | 0.0010 / 0.0018 | 6.762 | 0.0725 |
| 10000 | 10841 | baseline/Q3 | 0.0010 / 0.0014 | 6.732 | 0.0752 |
| 10000 | 10841 | baseline/Q4 | 0.0074 / 0.0087 | 5.098 | 0.0943 |
| 10000 | 10841 | graph/Q1 | 0.0397 / 0.0430 | 5.343 | 0.2355 |
| 10000 | 10841 | graph/Q2 | 0.0011 / 0.0019 | 6.999 | 0.2332 |
| 10000 | 10841 | graph/Q3 | 0.0011 / 0.0014 | 7.022 | 0.2562 |
| 10000 | 10841 | graph/Q4 | 0.0077 / 0.0105 | 5.311 | 0.2317 |
| 100000 | 100944 | baseline/Q1 | 0.0392 / 0.2068 | 14.076 | 0.6924 |
| 100000 | 100944 | baseline/Q2 | 0.0010 / 0.0019 | 15.709 | 0.6792 |
| 100000 | 100944 | baseline/Q3 | 0.0011 / 0.0011 | 15.934 | 0.8756 |
| 100000 | 100944 | baseline/Q4 | 0.0870 / 0.2663 | 14.326 | 0.8859 |
| 100000 | 100944 | graph/Q1 | 0.0385 / 0.2135 | 15.608 | 2.2062 |
| 100000 | 100944 | graph/Q2 | 0.0011 / 0.0021 | 17.289 | 2.4182 |
| 100000 | 100944 | graph/Q3 | 0.0011 / 0.0013 | 17.267 | 2.4030 |
| 100000 | 100944 | graph/Q4 | 0.0841 / 0.2681 | 15.737 | 2.3766 |
| 1000000 | — | SKIPPED_RESOURCE_PREFLIGHT | — | — | — |

Full raw timings, CPU, memory, footprints, output cardinalities and stop conditions are in benchmark.json.

## Complexity

Whole-arm logical statements: baseline 137; graph 157.
Graph reduction: -14.6%; required: 30%. Shared new code: 258.
Total new implementation: 552 logical statements. Non-LOC measures improved: 3.

| Non-LOC measure | Baseline | Graph |
|---|---:|---:|
| custom_recursion | 0 | 0 |
| traversal_routines | 2 | 1 |
| cycle_handling | 2 | 1 |
| path_state_management | 2 | 1 |
| topology_specific_lookups_joins | 2 | 3 |
| inverse_query_changed_lines_functions | 0 | 0 |
| variable_depth_changed_lines_functions | 0 | 0 |

Projection, indexes and generic traversal are fully charged; function-level attribution and reused M4–M7 code are in gate-a-report.json.
No controlled developer-productivity claim is made. Engineering effort and defects are disclosed in the JSON inventory.

## Commercial usefulness — non-scoring

| Query | Likely enterprise user | Decision supported | Assessment |
|---|---|---|---|
| Q1 | Assurance investigator, internal audit or incident reviewer | Determine which evidence supports an exception and whether further evidence or review is needed. | Plausibly meaningful: reduces manual evidence assembly. This experiment does not establish willingness to pay or graph-specific advantage. |
| Q2 | IAM architect, agent-platform owner or access reviewer | Understand dependencies and alternative authority bases before reviewing a delegation relationship. | Plausibly meaningful where delegated authority is complex; value depends on usable preserved source records and revision coverage. |
| Q3 | Change approver, security architect or governance operations lead | Review the scope and collateral authority-support loss of a proposed relationship change. | Plausibly meaningful for change-risk review. No intervention recommendation, prevention estimate or remediation-effectiveness claim is supported. |
| Q4 | Internal audit, evidence custodian, compliance assurance or data-governance owner | Identify assurance records needing review/reverification when an evidence source, revision or artifact is questioned. | Plausibly meaningful even without intervention analysis; transitive evidence dependencies can be valuable independently. No enterprise demand validation was performed. |

## Limits

- Synthetic scale observations and preserved cooperative evidence do not establish enterprise volume, authenticity or market demand.
- Q1 is the fixed preserved live exception at every tier. Synthetic scale adds M5 authority topology and M6 dependency conclusions, not arbitrary M7 attestations.
- M5 semantic traversal is reused by both arms and its cost remains shared; graph discovery does not replace semantic validation.
- Removing a relationship filters demonstrated support paths. Historical findings and outcomes are unchanged; prevention is never inferred.
- No Neo4j installation/configuration or Gate B work. Existing legacy graph code is excluded from Gate A execution.
- Warm measurements include immutable semantic caching equally in both arms; cold figures include common validation and empty query-class caches.
- CPU measures are cumulative worker user/system time at query completion, not independent per-query CPU deltas.

## Additional evidence and validation scope

Thirty paired workers (10 repetitions × 3 measured tiers), with four query classes each, produced 120 matching paired query results from identical per-pair inputs. Each arm/query/tier has 100 warm observations and 10 cold repetitions.

The core correctness checks passed within their evaluated scope. **The full Docker-backed regression suite did not complete.** A pinned-image OPA version command timed out after 20 seconds; the detailed completed/excluded test scope is in validation-scope.json. No full integration pass is claimed.

The million-relationship tier was not executed: its conservative preflight estimate was about 23 GiB, beyond the frozen 4 GiB cap. It is untested, not a failed query.

| Query/result case | Records | Paths | Affected actors | Assurance conclusions |
|---|---:|---:|---:|---:|
| Q1 | 53 | 993 | 0 | 0 |
| Q2 | 8 | 4 | 4 | 0 |
| Q3 | 8 | 4 | 4 | 0 |
| Q4 | 1065 | 1862 | 0 | 266 |
| independent_counterfactual_case | 7 | 5 | 3 | 0 |

Q2/Q3 return assurance connections inside each actor/tuple result; the top-level conclusion count above is the Q4-specific endpoint list. The independent Q3 case retains alternative bases for middle and worker, while leaf loses all demonstrated support. Neither finding nor outcome prevention is inferred. Full results are in query-results.json.

| Query-specific method logical statements | Baseline | Graph |
|---|---:|---:|
| Q1 | 9 | 9 |
| Q2 | 34 | 35 |
| Q3 | 31 | 31 |
| Q4 | 8 | 8 |

No individual query method met the 30% reduction either. Shared helpers, projector and generic traversal are additionally counted in the whole-arm totals; method LOC alone is not the decision.

Full new core + harness: **887 logical statements**. Including tests and result-reproduction scripts: **1291**. Core-only comparison remains 137 baseline + 157 graph + 258 shared = 552. Active development time per arm was not instrumented; elapsed lab time and limitations are disclosed rather than invented.

Supplementary full-root chains at depths 8, 16 and 32, plus competing populations of 2, 8 and 32, passed paired-result checks. Those are bounded supplementary measurements, not replacements for the main workload or new live evidence.

Cold source-to-answer is timed from worker preparation through result serialization; the separately recorded launch-to-exit measure includes process startup. Per-query CPU is cumulative worker CPU, and per-query RSS is worker high-water RSS; tier peak memory includes the controller.

Measured source code still matches the benchmark-start digests. The frozen protocol, original evidence archives and all pre-existing tracked files remain unchanged. No graph database was installed, configured, queried or modified.
