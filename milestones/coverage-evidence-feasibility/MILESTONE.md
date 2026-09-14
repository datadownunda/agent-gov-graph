# Coverage-evidence feasibility decision following M9b

[Canonical roadmap](../../ROADMAP.md)

**Status: CLOSED REVIEW — NOT_DEMONSTRATED; owner decision/publication pending.** This record establishes the decision scope from the owner's 2026-09-14 instructions. Candidate-specific falsification plans must be recorded before acquisition/testing; this is not a claim that such tests have already been frozen or run.

## Objective, claim and significance

Determine whether ordinary operational evidence, already available or realistically common in target enterprises, plus an explicit trust contract can support both unresolved M9b dimensions over a bounded assurance interval:

1. **Timing applicability and continuity:** a defensible bound applicable to the relevant evidence timestamps/processes throughout the interval, including OPA. Healthy point samples do not supply this.
2. **Evidence-channel completeness:** defensible availability and completeness of the relevant logging path throughout the interval. Successful probes, service uptime and endpoint configurations do not supply this.

The feasibility claim is that at least one concrete existing-source arrangement can address both dimensions under stated assumptions without AGG creating new telemetry. This tests adoption feasibility as well as technical support; it does not itself demonstrate CONTROL_EFFECTIVE.

## Required decision evidence and smallest test

Start with the [M9b protocol](../../experiments/m9b_live_acquisition/PROTOCOL.md), [result](../../experiments/m9b_live_acquisition/RESULT.json) and [existing source inventory](../../experiments/m9b_live_acquisition/SOURCE_INVENTORY.md). Retained Docker lifecycle/configuration/log snapshots and bracketed clocks are available but already insufficient by themselves; they are not new candidates that silently repair M9b.

For each candidate, document native source/fields, applicable interval and population, known failure modes, accessibility and evidence for its semantics. Explicitly enumerate trust in producer, collector, custody, clock source, lifecycle source, completeness indicators and operator/admin boundary. Distinguish a locally obtainable source from a documented enterprise possibility that has not been acquired.

Estimate permissions, source availability, initial integration effort, ongoing burden and likely enterprise adoption friction. State whether the customer already operates the evidence or would need to manufacture it for AGG; unknown cost stays unknown.

Before testing a candidate, specify the smallest bounded test that could falsify its claimed timing/completeness support, including what a clock step, missing segment, collector interruption or scope mismatch would look like in that source's ordinary evidence. Require observable rejection or explicit insufficiency for the chosen failure, not an assumed healthy result. Freeze the concrete test and its limits before acquisition. Do not introduce faults into external systems without authorized scope.

## Decision criteria and stopping rules

- **COVERAGE_EVIDENCE_FEASIBLE:** concrete existing sources support both dimensions with documented applicability and an actionable bounded falsification plan; record all baseline trust assumptions.
- **COVERAGE_EVIDENCE_FEASIBLE_WITH_EXPLICIT_TRUST_ASSUMPTIONS:** support depends on additional named, reviewable trust assumptions. Separate what is observed from what is trusted and take consequential claim-boundary assumptions to the owner.
- **COVERAGE_EVIDENCE_NOT_AVAILABLE:** the scoped inventory establishes the required evidence is unavailable for the chosen environment; do not generalize to every enterprise.
- **NOT_DEMONSTRATED:** semantics, access, applicability, completeness or feasibility remain unresolved. Documentation-only plausibility must not become empirical proof.

A source that cannot expose or bound the relevant failure does not substantiate that dimension. If no credible ordinary source addresses both dimensions, stop for an owner claim-boundary/product decision. A feasible outcome only permits proposing/preregistering the conditional positive-coverage milestone; it does not relax M9b or automatically authorize M9a-ii.

## Protected boundaries and current record

No new technology, observability platform, producer-specific telemetry requirement, generic scope engine, production adapter change or historical rescue. Preserve all frozen M9b evidence. No public/enterprise effectiveness or commercial validation claim follows from this feasibility record.

**Consequential decision:** owner selected this milestone after M9b; population coverage and periodic attestation remain conditional on action-level evidence prerequisites. **Final result:** [scoped source review](FINDINGS.md) found ordinary candidates but no available, applicable package substantiating both dimensions. Not a universal unavailability claim. **Checkpoint:** review baseline `af980b9`, review protocol `a7bcd7c`; result checkpoint recorded in the owner briefing. No new native campaign or production change. **Remaining uncertainty:** which ordinary source can support the two dimensions, under what trust boundary, and at what acquisition and operational cost. At close, record evidence, decision, final commit, tests/CI and update the roadmap in the same checkpoint.


## Close record

[Review protocol](REVIEW_PROTOCOL.md) · [Findings and cost/trust matrix](FINDINGS.md) · [Proposed falsification test](FALSIFICATION_PROPOSAL.md) · [Validation](VALIDATION.md)

The roadmap now records this negative feasibility review and the owner decision gate; it does not promote a new protected milestone without approval. Recommended next decision: identify one already-operated deployment/export for bounded source qualification under explicit trust assumptions. No enterprise export was acquired, no new capture ran and no coverage standard changed. Public checkpoint CI is pending owner-approved publication; baseline CI is not a substitute.
