# Strong-Link Assurance Falsification — frozen protocol v1

Fan-out and governed-action scope is the primary falsification target.

## Revised frozen claim

For one proposed governed action, native pairwise linkage may support downstream assurance only when evidence establishes both the relevant identifier conditions and the governance decision’s coverage of the particular execution. Correct transaction linkage does not establish governed-action scope. Retries, fan-out executions and child requests must not inherit governance coverage merely through shared identifiers or parent context. Unestablished scope requires abstention from coverage acceptance, while all existing M6/M7 gates remain applicable.

A fan-out scope-overreach acceptance is sufficient to fail the milestone, even if pairwise linkage precision and recall are perfect and no false M7 finding is emitted. Safe abstention on unsupported fan-out establishes a safety boundary, not support for governing fan-out.

## Revised scenario matrix

Retain 26 base cases and three equivalent presentations—canonical ordering, reversed ordering and consistent identifier renaming—for 78 evaluations. These are deterministic variants, not independent statistical samples.

| Class | Frozen variants | Required distinction |
|---|---|---|
| Fan-out — primary target | Multiple executions of the same tuple; a child execution changes action/resource; each child receives a separate governance decision | Transaction membership versus established coverage of each execution. Same-tuple repetition does not itself establish permission for additional executions. |
| Controls | Unique ALLOW triple; unique DENY with target effect; deterministic adequate-coverage blocked DENY | Genuine unchanged-pipeline operation and non-vacuity |
| Identifier reuse | Both transactions visible; counterpart omitted with reused-ID impostor remaining; reuse across observation periods | Snapshot uniqueness versus non-reuse |
| Namespace collision | Explicit namespaces; incorrectly pooled caller declaration; unavailable namespace evidence | Qualified identity versus textual equality |
| Copied/forwarded ID | Different tuple; identical tuple; identical copy after counterpart removal | Shared value versus execution identity |
| Retry | Repeated request ID; distinct request IDs under one action-attempt ID; separately governed retries | Attempt identity versus authority to retry |
| Fan-in | Two decisions competing for one execution; separate executions converging on one outcome; one governing branch withheld | Association versus attribution to a particular decision |
| Parent/child | Distinct children with explicit parent context; parent/session context only; separately governed children | Parent membership versus child identity and coverage |
| Missing bridge | Execution removed; bridge absent with coincidentally equal disconnected ID text | Established pairwise paths versus invented transitive identity |

Preserve the observationally indistinguishable copied-ID pair: identical permitted evidence but different scorer-only histories. The worker must produce identical outputs for that pair. Different outputs indicate leakage; an identical substantive finding that is false in one history exposes an assurance limitation.

## Diagnostic states

Keep the sidecar experiment-local. No production M6/M7 schema changes or new M7 findings.

| Diagnostic outcome | Meaning |
|---|---|
| LINKAGE_DEFENSIBLE_SCOPE_ESTABLISHED | Supplied evidence supports the declared linkage relationship and coverage of this particular execution. Coverage does not imply ALLOW. |
| LINKAGE_CORRECT_SCOPE_NOT_ESTABLISHED | Transaction association is defensible, but evidence does not establish that the decision covered this execution. No coverage acceptance is permitted. |
| LINKAGE_DEFENSIBLE_SCOPE_CONTRADICTED | Association is defensible, but explicit scope evidence excludes the execution. |
| LINKAGE_UNRESOLVED | Missing, ambiguous or contradictory linkage prevents a supported association. |
| NOT_EVALUABLE | Supplied evidence or an unsupported representation prevents the diagnostic assessment. |
| INTERNAL_ERROR | Processing failed; no evidentiary inference or coverage acceptance. |

In LINKAGE_CORRECT_SCOPE_NOT_ESTABLISHED, “correct” is not a worker claim of ground-truth knowledge. The sidecar records its evidence-based linkage assessment and relationship type; the scorer separately records actual linkage correctness. Transaction membership must never be reported as same-attempt identity.

The sidecar remains diagnostic. It must not repair correlations, suppress baseline failures, authorize executions or manufacture verification receipts. Preserve raw unchanged-pipeline outputs alongside diagnostics.

## Frozen thresholds

| Measure | Threshold |
|---|---|
| False substantive M7 findings, including false exceptions | Zero |
| False accepted identity links | Zero |
| False identity merges | Zero |
| Scope-overreach acceptances | Zero, including correctly linked fan-out executions |
| Governed-scope precision | 100% wherever coverage is accepted |
| Ambiguous or unsupported scope | 100% abstention from coverage acceptance |
| Unique controls | 100% observable pairwise recall, no false splits, expected genuine M7 outcomes |
| Presentation invariance | Equivalent substantive results across all three presentations |
| Internal errors | Report separately; never count as safe abstention |

Undefined denominators remain undefined. Abstaining on every control fails non-vacuity. No thresholds or heuristics may change after results are observed.

## Final milestone verdict rules

The report must explicitly answer:

Did any correctly linked execution inherit governance coverage that was not actually established?

Report YES, NO IN THE EVALUATED CASES, or NOT EVALUABLE, with the numerator, denominator, affected executions and supporting assertion references.

- YES → milestone failed, regardless of aggregate linkage quality. A transaction association, CONSISTENT result or ALLOW label alone is not counted as coverage acceptance; the report must identify the actual output or downstream use that asserted or relied on coverage.
- Any other zero-tolerance breach → milestone failed. Successful diagnostics cannot erase an unchanged-pipeline failure.
- No breaches, but absent non-vacuity or unassessable coverage behavior → claim not demonstrated.
- No breaches and functioning controls, with safe scope abstention → the tested safety boundary is supported; fan-out assurance remains undemonstrated where scope is not established.
- Any stronger conditional conclusion must identify the supporting namespace, non-reuse and scope evidence. Synthetic observations demonstrate assessment semantics, not independently verified enterprise conditions.

Ground truth remains scoring-only throughout correlation, reconciliation, scope determination and adjudication.

## Frozen measurement and execution specification

This section makes the previously approved metrics executable without changing the claim or thresholds.

Use the unchanged complaint M6 archive adapter and genuine M7 attest() entry point for primary measurements. Preserve full candidate populations and all original assertions, receipts, findings and failures. The adapter's three fixed reporting focuses remain reporting selectors only. Measure each visible governance focus; the blocked control additionally uses the existing bounded view. Unsupported direct relationship probes never receive invented M7 receipts.

The independent diagnostic reads only supplied evidence and local declarations; missing scope evidence remains insufficient. References locate evidence, never create matching keys. Namespaces supplied by a caller are not authenticated. Scope tuples alone cannot distinguish same-tuple descendants or retries. Scope acceptance requires explicit supporting evidence binding the particular execution; the initial corpus does not invent such bindings. The diagnostic must not gate or modify primary execution.

Build scorer truth from the event history independently of native identifier values. Truth contains separate transaction, attempt, outcome, directed parent/retry and governed-scope relations. COVERED is not ALLOW. Sidecar membership context can support transaction association, never SAME_ACTION identity or scope. Unknown scope truth does not permit scope acceptance. The copied-ID pair shares exactly the same worker input and differs only in scorer truth.

Metrics are reported per case, edge type, class and pooled. Reciprocal assertions count once. Precision = correct accepted pairs / accepted pairs. Recall = correct accepted pairs / all true pairs, including withheld endpoints. Observable recall restricts true pairs to visible endpoints. False-link rate = incorrect accepted pairs / accepted pairs. Identity components include singleton records: false-merge rate = linked components containing different true attempts / all components with an accepted identity link. False-split rate = visible multi-record true-attempt groups split across components / visible multi-record true-attempt groups. Component scoring concerns attempt identity, not business-transaction membership.

Assurance abstention = applicable governance evaluations with no CONTROL_EFFECTIVE or CONTROL_EFFECTIVENESS_EXCEPTION finding / applicable evaluations. NOT_APPLICABLE, unsupported evaluations and internal errors are separately counted; internal/unsupported cases do not earn safe-abstention credit. Incorrect substantive findings are scored separately by finding type. An exception is false when its cited target effect does not belong to the particular denied action. A positive is false when the bounded declared control objective was violated or supplied coverage cannot substantiate it. NOT_APPLICABLE is not a positive coverage assertion.

Scope overreach = accepted governance/execution coverage where truth is NOT_COVERED or UNSPECIFIED. Scope precision = correct coverage acceptances / all coverage acceptances. Scope recall = correct coverage acceptances / true observable coverage relations. Count explicit sidecar acceptance separately from production coverage use. For production, cite actual M7 substantive reliance on an execution/outcome path as coverage use; do not infer acceptance from mere M6 association, CONSISTENT, or ALLOW. If production has no scope proposition for an execution, record it as unassessed, not correct acceptance. Report critical-question results both across explicit observed uses and across all correctly linked executions, with unassessed counts.

The three presentations are compared after removing content-address/location changes and applying the inverse identifier renaming. Correctness and all substantive decisions must agree. Ground-truth changes must not affect worker outputs. Scenario/fixture/failure names are reporting metadata only. The worker runs in a separate process without scorer truth. This isolates accidental leakage, not hostile code.

Freeze baseline commit, protocol SHA-256 and tracked-file SHA-256 inventory before implementation. Freeze implementation hashes before first execution. Refuse output overwrite; retain any failed run. Preserve all M1–M9a-i files and original historical replay contexts. No production changes, new dependencies, technologies, databases, matching heuristics, formats, UI, graph work or M9a-ii work. Generated native-format rows and supporting declarations are deterministic synthetic fixtures, not newly independent target observations. No live positive-effectiveness or enterprise authenticity claim is possible.
