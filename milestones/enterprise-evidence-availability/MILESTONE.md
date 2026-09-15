# Enterprise Evidence Availability Qualification

[Canonical roadmap](../../ROADMAP.md)

Status: CLOSED — NOT_DEMONSTRATED. Baseline 39895d3490c0f4dc7406b923caf0bf38de211c01. Owner closes retained-process-binding at NOT_DEMONSTRATED and authorizes this next protected milestone. Documentation research only; no implementation, telemetry, account queries or deployment acquisition.

## Frozen hypothesis and scope

At least one common enterprise deployment pattern exposes sufficient native retained evidence to support AGG's minimum assurance prerequisites without AGG-specific telemetry.

Fixed representative patterns (not claims of measured deployment prevalence):
1. Upstream Kubernetes on Linux, containerized agent/OPA, HTTP target with native NGINX logging.
2. AWS EC2 Linux agent/OPA acting on S3, with native CloudTrail records. No substitution with another compute/audit product to obtain a pass.
3. Microsoft Dynamics 365 application agent operating on Dataverse records, using native Dataverse auditing. Managed internal runtime/host evidence is explicitly evaluated from the customer-access boundary. No switch to another ERP vendor to obtain a pass.

Review seven required dimensions for each: runtime attribution; host/VM/boot identity; clock-domain applicability; historical clock state; logging continuity/completeness; governance/correlation identifiers; target outcomes. Existing AGG minimum requires applicable process lineage and interval timing plus defensible scoped evidence completeness; identifier equality, healthy status, delivery acknowledgements and product names do not substitute. Preserve M9b and all historical negative results.

## Classification and decision rules

Use exactly NATIVELY_AVAILABLE_AND_RETAINED, NATIVELY_AVAILABLE_BUT_RETENTION_DEPENDS_ON_CONFIGURATION, AVAILABLE_ONLY_WITH_ADDITIONAL_INSTRUMENTATION, NOT_AVAILABLE or UNKNOWN for each required item. Classify the complete requirement, not just a related field. Split subcomponents explicitly where necessary. AND_RETAINED requires documented retention at the stated scope, not assumed customer practice; configuration-dependent storage is not actual acquired evidence. NOT_AVAILABLE requires explicit evidence about the selected customer boundary. UNKNOWN is appropriate when documentation does not establish sufficient scope. Additional instrumentation must be concrete, not an inference from absent documentation.

ENTERPRISE_EVIDENCE_FEASIBLE requires all seven requirements supported by documented native retention and coherent applicability under an explicit trust contract. FEASIBLE_WITH_ENTERPRISE_EVIDENCE_REQUIREMENTS requires all seven supportable through specified ordinary native configuration/retention and trust requirements, without unresolved essential semantics. ADDITIONAL_INSTRUMENTATION_REQUIRED requires evidence of an indispensable missing capability and a demonstrated need for instrumentation, not mere uncertainty. Otherwise NOT_DEMONSTRATED. No population prevalence or real-deployment assertion follows from documentation alone.

Missing timing or completeness defeats a pattern's positive qualification; review all three fixed patterns without adding vendors. Record source, direct proposition, retention, access, mutability/trust, completeness assessability, estimated effort and friction for every matrix row. Costs are judgments unless directly sourced; no invented prices or enterprise measurements.

## Deliverables and closure

Official primary-source matrix; minimum viable evidence contract; adoption friction; falsification outcome; one recommended next technical milestone; roadmap implications. Freeze this protocol before source review. No live falsification is implied by a documentation test. Update roadmap/milestone together at close and publish documentation checkpoint with CI. Pause only for a material product-thesis/boundary change per latest owner instruction. Final result: NOT_DEMONSTRATED. See [assessment and minimum evidence contract](ASSESSMENT.md) and [seven-dimension matrix for all three patterns](EVIDENCE_MATRIX.md). No complete documented native arrangement was established; this does not prove universal enterprise unavailability or necessity of additional instrumentation. Next test is conditional on an eligible already-retained Kubernetes/Linux package. No implementation or acquisition occurred.
