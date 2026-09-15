# Enterprise Evidence Availability Qualification — decision

[Milestone](MILESTONE.md) · [Evidence matrix and primary sources](EVIDENCE_MATRIX.md) · [Canonical roadmap](../../ROADMAP.md)

## Result

**NOT_DEMONSTRATED.** Documentation for the three frozen patterns does not establish one complete native retained evidence arrangement satisfying all seven prerequisites. This is a bounded documentation qualification, not an empirical finding about all enterprises. No customer export was examined. Ordinary evidence may exist beyond the documented interfaces; neither universal unavailability nor necessary additional instrumentation has been established.

| Frozen pattern | Useful native components | Essential unresolved requirements |
|---|---|---|
| Kubernetes/Linux, OPA → NGINX | Container/node identifiers, configurable audit and request logs | Historical actual timestamp-producer binding; applicable interval clock bound; complete emission-to-retention path; native authorization/execution linkage |
| AWS EC2/Linux, OPA → S3 | Instance/boot components, configurable clock logs and API records | Actual producer binding; applicable guest and service endpoint timing; event-generation and late-arrival closure; authorization/request linkage |
| Dynamics 365 → Dataverse | Principal/transaction attribution and configured change history | Managed process/host/clock lineage and history; channel closure; agent/governance linkage. Read/export outcomes are outside the selected native audit source |

The frozen hypothesis is **not substantiated**, rather than globally falsified. A single ordinary existing deployment could still supply the missing evidence. Positive feasibility, including the conditional outcome, would require resolving essential semantics, not merely enabling retention. ADDITIONAL_INSTRUMENTATION_REQUIRED would overstate what the reviewed documentation proves.

## Minimum viable enterprise evidence contract

This is an acceptance contract for a future candidate, not a demonstrated available package or a new implementation requirement. Each item must be satisfied by already-existing ordinary native evidence or an explicit, defensible source contract; unsupported assumptions remain grounds for abstention.

1. **Bounded claim and inventory.** Identify the action, target outcome boundary, assurance interval, versions and complete relevant producer/channel inventory. Preserve the frozen M9b UTC/applicability requirement; a common clock cannot silently replace it.
2. **Actual producer lineage.** Retain source-origin evidence connecting each relevant timestamp-producing evaluation/request to its process lifetime, container/task where applicable, node/VM and boot identity. Address PID reuse, restarts, placement changes and namespace membership. Managed-provider evidence must support equivalent applicability; principal identity alone is insufficient.
3. **Applicable historical timing.** Identify timestamp implementation and clock domain. Retain applicable synchronization/error history and configuration plus sufficient lifecycle/discontinuity evidence to bound the entire interval under explicit reference, rate and sampling assumptions. Shared-domain evidence may reduce relative-clock uncertainty, but must still meet the frozen UTC criterion. Separate domains need bounded agreement against a common reference.
4. **Governance and native linkage.** Preserve the decision, applicable authority/policy revision, inputs and relevant native identifier semantics. Demonstrate scoped adjacent-system joins to execution and target evidence; no universal AGG-generated ID is required. A decision ID is not execution evidence.
5. **Scoped outcome semantics.** Preserve native target records whose documented semantics support the precise claimed outcome. Distinguish accepted requests, committed changes, served representations and client receipt. Unsupported operations are excluded explicitly; absence cannot establish nonoccurrence without coverage.
6. **Channel coverage and closure.** Retain applicable capture/filter/sampling settings, lifecycle and loss/recovery evidence, segment/rotation/delivery history and a defensible interval-finalization rule. Distinguish generation, transport and storage completeness. Prefer independently produced failure evidence; disclose common producer, collector and administrator failure modes. Digests or acknowledgements alone do not establish upstream emission completeness.
7. **Custody, retention and access.** Record producer, custodian, export method, retention settings, deletion privileges and integrity checks for every source. Preserve original records and provenance through review. Grant least-privilege scoped read/export access. Same-operator custody is an explicit trust limitation, not independent enterprise assurance.

A reviewable package must map every requirement to exact records or a bounded applicable guarantee, label inference separately, and disclose unresolved edges. No weak dimension may compensate for another. Stop a future record test at its first essential unsupported edge.

## Adoption friction and commercial implications

The matrix provides per-item planning ranges; they overlap and must not be summed into a delivery promise. They exclude procurement, missing-history recovery and provider negotiations. No interviews, prevalence estimates or customer-cost measurements were performed.

- **Kubernetes: medium-to-high friction.** Cluster, node, security and target owners must provide compatible historical records. Native fields lower collection complexity, but deleted workloads and disparate retention may prevent retrospective qualification. It is the best next candidate for a bounded test because more of the relevant runtime boundary is operator-accessible; this is an engineering judgment, not proven feasibility.
- **AWS: high friction.** Guest and cloud audit ownership must align, with data-event scope and timing across a provider boundary resolved. Attractive API evidence does not eliminate the host-to-service timing and completeness requirements.
- **Managed application/ERP: high and potentially blocking friction.** Accessible business audit records can provide useful positive observations, while required infrastructure applicability may depend on provider clarification. The selected source does not cover every operation.

Time to first assurance depends on pre-existing evidence, not adapter speed. A transparent evidence-readiness assessment may help a control owner understand a gap, but willingness to pay and recurring attestation value remain unvalidated. Do not package this review as demonstrated control effectiveness or expand AGG into telemetry ownership to improve onboarding.

## Recommended next technical milestone and roadmap

**Conditional Kubernetes/Linux retained-package contract qualification.** Proceed only when a real, already-retained export is available with a plausible native association from the actual OPA timestamp producer to container/task and host/boot. No such export is currently identified. First falsification test: attempt that exact join using original log-origin/runtime/placement records; stop at the first missing edge. Only after it passes evaluate namespace/clock applicability, interval timing, then channel completeness and remaining contract items. Do not launch a new capture or broad clock-history search to fill the first gap.

This milestone closes the three-pattern documentation review. The roadmap now holds at the missing eligible-package dependency; the recommended test is conditional and has not begun. Later M9b positive coverage, M9a-ii and attestation milestones remain gated. No product-thesis or product-boundary change is proposed, so the owner's special pause condition is not triggered.

M9b remains **CLAIM_NOT_DEMONSTRATED**. Historical timing remains **NOT_DEMONSTRATED**, logging remains **NOT_TESTED_AFTER_TIMING_STOP**, and the retained-process-binding branch remains **NOT_DEMONSTRATED**. No implementation, new telemetry, live acquisition or historical-source acquisition occurred in this milestone.
