# Existing-deployment evidence qualification

[Canonical roadmap](../../ROADMAP.md)

**Status: APPROVED — awaiting named deployment/export.** The owner approved publication of feasibility checkpoint 285893e and this bounded next step. Approval does not supply missing evidence or accept unspecified trust assumptions.

## Objective and proposed claim

Qualify one already-operated deployment's existing evidence export for interval timing applicability and target logging completeness under an explicit trust contract. Determine whether its ordinary records justify a separate positive-coverage experiment; do not infer CONTROL_EFFECTIVE from qualification.

The [offline falsification proposal](../coverage-evidence-feasibility/FALSIFICATION_PROPOSAL.md) supplies the method. Before execution, freeze the actual deployment, versions, clock domains, action population, historical interval, numerical timing bounds/expiry rules, logging path, finalization semantics and source-native evidence inventory. The deployment-specific claim is not yet frozen because the source is not identified.

## Required source handoff

Identify an existing deployment and export location or responsible evidence owner. Request only the relevant interval and scope:

- OPA and target process/host placement and lifecycle records;
- already-retained clock configuration and measurement/update/disruption history;
- original target logs, applicable configuration history and required rotation segments;
- existing collector loss/backlog/recovery/retention records for the actual logging path;
- source ownership, administrative boundaries and export custody.

Read-only access or a supplied export is sufficient; credentials must not be embedded in the milestone record. A contact name alone is not authorization to send outreach. Missing records remain missing; no new telemetry or reconstructed historical filler.

## Criteria and boundaries

Qualification is demonstrated only if both dimensions have evidence-backed applicability and reviewable trust assumptions for the fixed interval, and the preregistered challenges detect the affected insufficiencies. If the original export or authentic fault evidence is absent, say so; scratch omission views demonstrate sensitivity only. Missing source support yields NOT_DEMONSTRATED; acquisition/verification failure is recorded separately as NOT_EVALUABLE where applicable.

No live fault injection, source changes, adapter expansion, new technology, relaxed five-second standard or M9a-ii work. Consequential trust/claim-boundary changes require owner review. Preserve all originals and prior negative results.

## Decisions, result and checkpoint

Owner approved this next step after the scoped feasibility review remained NOT_DEMONSTRATED. **Result:** pending source identification; no qualification test executed. **Evidence baseline:** 285893e47d2f8281503791b9039cac6206ef4b42. Approval/roadmap record is included in the subsequent publication checkpoint; final SHA and CI are recorded in the PR/owner briefing. **Uncertainty:** actual source availability, timing applicability, full-path completeness and acquisition cost. At close update this record and ROADMAP.md together when warranted.
