# Identifier provenance necessity decision

Decision: **CONTEXT_NEEDED_PRODUCTION_DEFERRED**.

Producer and observation context is necessary to interpret identifier equality. The two campaigns do not yet establish that a new production representation is necessary. Preserve the existing evidence and make the bounded field interpretations explicit; do not add a schema, producer requirement or matching rule now.

Baseline: `1c555013e7140135075e9deebedcd1dc9da47dd7`. [Protocol](PROTOCOL.md) preregistered at `62019d0` before delegated comparison. See the [six-case evidence matrix](EVIDENCE_MATRIX.md) and the concrete [interpretation notes](INTERPRETATION_NOTES.md).

## Decision against frozen criteria

The context-necessity criterion is met. Repeated NGINX incoming identifiers represent caller-supplied values and do not identify one server request across repetitions. A native/returned identifier instead represents a server request under the archived configuration and custody. For OPA, the same decision_id field can contain stock-generated or SDK-supplied values; the second possibility is source-reviewed, not empirically captured here. Equal text and producer brand alone do not determine the defensible relationship.

The production-necessity criterion is not met. Existing raw evidence and retained code/configuration allow a reviewer to reconstruct the tested distinctions (A). The interpretation notes (B) make those distinctions and unresolved cases explicit without replacing the evidence. A machine-readable extension (C) can encode the same statements but would not independently substantiate them. No concrete operation has been demonstrated that requires C and cannot use A/B for this bounded review. This is a negative result for necessity now, not proof that production provenance will never be valuable.

The criteria do not require A/B to resolve missing evidence: they must preserve the unknown. Neither notes nor a new representation establishes authenticity, universal uniqueness, configuration applicability to a foreign record, or an execution/authorization binding. No experiment measured whether notes reduce reviewer mistakes or whether an automated consumer could safely rely on them.

## Existing machinery and remaining gap

AGG is not starting from zero provenance metadata. Action envelopes retain raw records and location/digests. Target ingestion retains its target contract and digest. `native_assertions` takes issuer/namespace declarations and emits limitations. `m6_attestation_evidence._declaration` already reads per-record/per-field `identifier_declarations` with issuer and namespace; `_namespace_codes` checks compatibility. These are explicitly declarations, not authenticated generation evidence.

Downstream code does consume native correlation paths: `action_reconciliation` replays them and `_exception_paths` in `m6_attestation_evidence` checks their scope/namespace conditions. The older `docs/correlation-assertions.md` statement that assertions do not feed control-effectiveness is therefore not a complete description of the current repository. This review follows code and does not edit that historical document. The existence of those consumers does not by itself prove that adding generation fields would repair their assurance boundary. Historical Strong-Link Assurance Falsification remains **FAILED**; no scenarios were rescored.

The possible future gap is an evidence-backed binding between a particular identifier observation, applicable producer configuration/invocation mode and permitted relationship. A label such as `producer_generated=true` would merely add an assertion unless its basis and applicability were established. Do not duplicate current issuer/namespace fields or require native producers to manufacture AGG-specific annotations.

## Recommendation and reopening trigger

Retain the two integration-specific interpretation notes as analysis artifacts. Do not promote them into automated attestation prerequisites or require them as new producer output. No production change is recommended in this milestone.

Recommend **M9b coverage substantiation** as the next milestone to preregister. Its exact claim still needs to be frozen; this review did not find a ready M9b protocol or demonstrate its result. Existing `_coverage` checks in `m6_attestation_evidence` distinguish missing finalization and clock support from identifier linkage. Generation provenance does not supply those missing facts. M9a-ii remains later in the protected sequence.

Reopen representation work only when a named protected operation requires machine-enforced interpretation, a concrete failure/ambiguity shows why existing evidence plus explicit notes is inadequate, the ordinary sources can substantiate applicable generation/observation semantics, and a bounded extension demonstrably improves that operation without converting missing evidence to confidence. At that point propose the smallest consumer-side extension and its falsification tests for approval. Do not preselect a general provenance subsystem.

## Plain-English briefing

**Goal:** Decide whether the two producer studies justify building identifier provenance now, rather than merely show that context matters.

**Accomplished:** Compared the six fixed cases across existing evidence, explicit interpretation notes, and a potential production representation. Prepared actual NGINX and OPA notes demonstrating what the smaller alternative can express, including unknowns.

**Challenges:** Existing provenance-related fields and downstream consumers made a simple “missing provenance” diagnosis inaccurate. We also found an older documentation statement that no longer captures the code's downstream use. SDK behavior and execution-ID recording must remain source-only and hypothetical evidence respectively.

**Technical impact:** Additive decision documents only. No producer campaigns, production changes, new technologies or historical rescoring. Baseline files and prior verdicts are preserved.

**Product impact:** Interpret identifier equality through evidenced relationships and applicability. A new field is not new evidence. The necessity of a production extension remains unproven.

**GTM/commercial impact:** A potential benefit is more defensible assurance explanations; a potential cost of premature implementation is integration-specific configuration collection and maintenance. Buyer demand, error reduction, differentiation and time-to-value were not measured. This is scope discipline, not a validated market conclusion.

**Unknowns:** Whether reviewers use the notes correctly; which future automated operation needs structured generation context; whether ordinary enterprise evidence can reliably bind an observation to its applicable configuration; and the empirical effect on assurance findings. Deferral does not certify current production assurance as safe.

**Next:** Preregister M9b coverage substantiation. Do not start its experiment or M9a-ii as part of this decision.

**Checkpoint:** The delivery briefing supplies the final local commit and publication/CI status. Validation is recorded separately in [VALIDATION.md](VALIDATION.md). Publication of this new decision is subject to the owner's significant-public-claim review boundary; prior approval covered the OPA PR only.
