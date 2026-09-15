# External Evidence Readiness Qualification

[Canonical roadmap](../../ROADMAP.md) · [Minimum enterprise evidence contract](../enterprise-evidence-availability/ASSESSMENT.md)

**Status: DEFINED — NOT_STARTED; BLOCKED_PENDING_EXTERNAL_EVIDENCE_ACCESS.** No eligible environment/package is currently available. Definition is not execution authorization or a positive readiness finding.

## Objective

Determine how much of AGG's minimum enterprise evidence contract is satisfied by one real, already-existing agent deployment before the operator changes instrumentation or produces AGG-specific evidence.

## Package eligibility

All criteria must be documented before qualification starts:

- Independently operated: the external operator controls normal deployment operations and source custody; AGG does not run the environment to generate its own demonstration evidence. Disclose relationships and shared custodians; separate producers do not automatically imply independent custody.
- Pre-existing: deployment and relevant retained records predate the readiness exercise; document dates and ordinary operational purpose.
- Not created to demonstrate AGG, including no synthetic or locally constructed replacement deployment.
- At least one actual agent/runtime.
- At least one governance/control mechanism applicable to that agent's actions.
- At least one target system.
- Ordinary retained evidence from those systems, generated for their existing operational purposes.
- Authorized read-only access or exports sufficient to inspect provenance and coverage; preserve source attribution, scope and any redaction limitations.

Eligibility does not require complete assurance evidence: a missing required dimension must remain observable as a result. Insufficient access is distinct from evidence never generated or no longer retained. An export may package existing records; it must not manufacture missing events, history or source guarantees.

## Bounded protocol — defined, not executed

1. Record the operator, deployment purpose, existing systems, custody, access permissions and evidence retention horizon. Fix one bounded action/period and the unchanged evidence/configuration baseline before inspecting assurance sufficiency. Do not select a different package simply to erase a negative result.
2. Inventory the seven contract dimensions: process/runtime attribution; host/VM/boot identity; clock-domain applicability; historical time-service/clock state; logging/channel continuity and completeness; native governance/correlation identifiers; target-system outcomes.
3. For each dimension, cite exact native records and source/version semantics; record producer, custody, retention, access, mutability, direct proof, inference, trust assumptions, completeness limits and observed acquisition/review effort. Distinguish absent evidence, inaccessible evidence, expired retention and unknown availability. Document dependencies; do not infer a clock bound for an unbound process.
4. Assess each requirement as supported, partially supported, absent or unknown at the stated scope. Missing evidence ends any positive sufficiency claim for the affected requirement; it does not prevent a read-only inventory of other independent dimensions. Do not combine weak dimensions into a positive result. This is readiness assessment, not a new M9b effectiveness test.
5. Return a contract-to-record matrix, exact gaps and access limitations, producer lineage, trust contract, operational/adoption friction and the smallest justified next decision. A readiness assessment can be useful even when no complete assurance claim is supportable. No positive coverage or control-effectiveness finding follows automatically.

## Stop and preservation rules

If eligibility or authorized access is not established, remain blocked and do not inspect an alternative constructed environment. If a required dimension is absent, record that result; do not enable logging, add a monitor, generate a heartbeat, rerun an action, extend a capture or create replacement evidence. No changes to operator instrumentation and no AGG-specific telemetry. Preserve the original absence even if a future separately approved exercise addresses it.

Frozen M9b UTC/applicability and completeness requirements remain unchanged. M9b remains CLAIM_NOT_DEMONSTRATED; historical logging remains NOT_TESTED_AFTER_TIMING_STOP. Enterprise Evidence Availability Qualification remains NOT_DEMONSTRATED without a universal-unavailability or necessary-instrumentation inference.

## Parallel commercial/design-partner work

Continue qualifying the assurance problem and potential partners while technical work is held. A discovery brief should establish: who owns the control and evidence; whether an independently operated pre-existing deployment exists; what native records are already retained; whether scoped read-only access/export is feasible; access/privacy approval lead time; the decision a readiness finding would improve; and interest in recurring assurance. Record actual answers separately from hypotheses. Do not promise control effectiveness or make instrumentation changes a prerequisite for participation.

No partner outreach, deployment access, export request or qualification execution is performed by this definition. When an eligible opportunity is available, record the concrete scope and access authority before execution. At close, update this record and the canonical roadmap together; absence remains a durable finding.
