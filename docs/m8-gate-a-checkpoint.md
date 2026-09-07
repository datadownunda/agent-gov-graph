# M8 Gate A review and checkpoint

The frozen result remains:

```
GRAPH_SEMANTIC_VALUE = NOT_DEMONSTRATED
GRAPH_DATABASE_VALUE = NOT_TESTED
```

Under the preregistered assurance-investigation and counterfactual-impact queries,
a derived graph representation preserved correctness but did not demonstrate
sufficient incremental analytical/engineering value over the fair indexed Python
baseline to justify advancing to a graph database.

This checkpoint adds review and validation receipts. It does not change the
protocol, implementation, original measurements, scoring thresholds or results.
The protocol SHA-256 remains
`c9d6cbd538303fdab07731490ce6d986c81ae56b4919593ae8c130dbe015f501`.
The original report is in
`experiments/graph_value/results/gate-a-v1/REPORT.md`; checkpoint receipts are in
`experiments/graph_value/results/checkpoint-2026-09-07/`.

## Meaning of the result

Relationship-aware Agent Gov Graph semantics remain the existing M1–M7 concepts:
exact authority/delegation references, historical revisions, evidence correlation,
reconciliation and control attestation. Their use does not require a graph engine.

Graph semantic value is the incremental analytical and engineering value of the
derived multigraph compared with the fair indexed Python implementation of the
same queries. Gate A did not demonstrate that value under its frozen rule.
Graph-owned implementation required 157 logical statements versus 137 baseline,
14.6% more, failing the required 30% reduction. Three secondary non-LOC improvements
cannot override that rule. Shared code and total engineering complexity remain
disclosed in the original report; no boundaries were rearranged during review.

Graph-database value concerns a database's additional benefits and costs. It was
not tested. Neither fast offline queries nor relationship-aware semantics justify
claiming database value. Gate B remains unopened.

## Scope and evidence review

- Every added implementation, schema, fixture, experiment and receipt belongs to
  M8 Gate A. No Gate B, M9, intervention engine, intelligence network or later
  milestone implementation is included. The excluded preliminary measurement
  batch is retained transparently and remains excluded from scoring.
- The graph is a disposable, derived projection. Original evidence, exact
  revisions, preserved assertions and unchanged M4–M7 replay remain authoritative
  within their existing evidence limits. No projected relationship writes back
  to evidence or changes a finding.
- The canonical adapter supplies identical allowlisted input to both arms.
  Ground-truth content and independent expected answers are not query input.
  Archive inventory digests may appear as verification dependencies; hashing an
  inventory artifact does not expose its ground-truth content to a query.
- The legacy graph builder is absent from the Gate A execution path. Its
  pre-existing regression tests are distinct from the Gate A experiment.
- Q3 removes demonstrated paths through an exact relationship while retaining
  historical findings, rejected candidates and conflicts. It does not infer
  prevented exceptions, prevented outcomes or remediation effectiveness.
- Q4 preserves conclusion support, assessment context and verification dependency
  as separate per-hop categories. A shared artifact can identify conclusions for
  review/reverification without establishing substantive support or changing them.
  Q4 remains independently eligible for strategic value under the frozen rule.
- Warm p95 of 5 seconds, cold source-to-answer of 120 seconds and resource caps
  are experimental offline guardrails, not Agent Gov Graph product SLOs.
- Commercial usefulness remains explicitly non-scoring. The Q1–Q4 enterprise
  users and decisions are plausible hypotheses, not validated buyer demand,
  willingness to pay or demonstrated graph-specific commercial advantage.

## Checkpoint validation

- Full Gate A suite: 51 passed.
- Completed broad M1–M8 subset: 319 passed, 5 skipped. Three additional independent
  tests from otherwise Docker-dependent modules passed, giving 322 distinct
  passing regression cases and 5 skipped. The original frozen regression result
  remains 316 passed, 5 skipped; later validation does not replace it.
- All 6 normal OPA policy tests passed independently with official native OPA
  1.19.0 (`opa test policies -v`). The downloaded Darwin amd64 binary's release
  checksum was verified as
  `a6bb096502d176a23b721e023f3ca615a0e4773fec69511143093a2281118f5c`.
  The binary resides only in temporary storage, outside the repository.
- All 120 saved paired benchmark results match. Recalculated aggregates, decision,
  checks and reasons match the saved report. Exact Q1–Q4 answers were replayed for
  both arms at 100,944 relationships; no new performance scoring was performed.
- All 17 JSON Schema documents pass schema validation. The full 33,191-node,
  100,944-edge projection and all five saved query result cases validate against
  their M8 schemas.
- All 12 measured implementation files match benchmark-start hashes. All 291
  pre-existing tracked files match M7 commit
  `b585c548a3b68e6611c1f7545f63e7bcfd05d845`; all 33 inventoried archive files match
  their saved SHA-256 values. The frozen-file inventory additionally identifies
  all 57 M8 files as they stood before this checkpoint's additive review receipts.

No Neo4j installation, configuration or use was performed. The existing unrelated
Neo4j container was not changed. No M8 semantics were modified to accommodate
local Docker failures.

## Docker limitation

The full suite was retried with `RUN_FOREIGN_OPA=1`, outside the filesystem
sandbox, and bounded to 180 seconds. It completed 54 tests successfully, then
was interrupted at 180.37 seconds while waiting on the legacy Docker OPA `exec`
subprocess. No completed test failed. The matching image is present and Docker
29.7.2 server inspection succeeds, but even
`docker run --rm --pull=never openpolicyagent/opa:1.19.0 version` timed out after
25 seconds. That minimal command uses neither repository code nor a mounted
evidence archive. Native OPA 1.19.0 and all policy tests succeed.

This isolates a local container-execution problem independent of M8. The internal
Docker failure mechanism was not established, and full Docker integration remains
unvalidated locally. Exact commands, timeout, image identity, logs and test scope
are retained in checkpoint `validation.json` and `full-suite.log`. GitHub CI is
checked separately after pushing and does not retroactively change the experiment.
