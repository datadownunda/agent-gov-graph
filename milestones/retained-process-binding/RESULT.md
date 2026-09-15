# Retained process-binding result

**NOT_DEMONSTRATED — stopped at step 1.** [Protocol/milestone](MILESTONE.md) · [Roadmap](../../ROADMAP.md) · [Approved lineage review](../historical-coverage-qualification/CLOCK_LINEAGE_REVIEW.md)

## Exact findings

- Shared clock domain is plausible but not demonstrated.
- Different clock domains are also not demonstrated.
- Timing remains `NOT_DEMONSTRATED`.
- The first unresolved requirement is binding the actual timestamp-producing OPA and NGINX processes to a specific host/boot/clock domain.
- Do not search broadly for time-service history until that process/host binding is established.
- Do not use shared-clock plausibility to weaken the frozen M9b UTC/applicability requirement.

| Ordered step | Result |
|---|---|
| Actual OPA container/task identity bound to the timestamp-producing process | NOT_DEMONSTRATED; stop |
| OPA host/boot binding | NOT_TESTED_AFTER_BINDING_STOP |
| Compare with NGINX host/boot evidence | NOT_TESTED_AFTER_BINDING_STOP |
| Timestamp-producing process namespace membership | NOT_TESTED_AFTER_BINDING_STOP |

## Retained records inspected

Scope: the existing [185-file M9b archive](../../experiments/m9b_live_acquisition/results/v1/manifest.json), not current Docker state, other episodes or host time-service records. Hashes all matched before review.

- `opa.jsonl`: contains decision ID `0c007666-e8dc-441d-b658-01d43dc8689a`, input action-attempt ID `1195538b-4570-47f1-b94a-b4145bf15a86`, and `labels.id` `e8216359-db9d-4428-91b2-d22b7bca556b`. None has a retained association with an actual Docker container/task/PID. A producer label is not silently relabelled as runtime identity.
- `runtime.jsonl`, `governance.jsonl`, `authority_resolution.jsonl`, `capture.json` and `execution-lock.json`: retain the episode, invocation context and authority/evaluation relationships. They do not supply the missing OPA runtime binding. `execution.jsonl` is empty as expected for blocked execution, not a receipt identifying the OPA process.
- `commands/001`–`033` command metadata: OPA-specific inspection `004` is image inspection. Container inspection and lifecycle commands concern the NGINX target. Image identity is not running container identity.
- `events.stdout`: retained actor identity is only NGINX container `5b2e78f600d1560ce8b8f8f4de2cf50b137edc6692a96218966077ec76b83f63`; `capture.json` records the target-name filter. It cannot identify the OPA container.
- `frozen/src/governance_event.py`, `evaluate_policy_with_decision_log`: intended invocation is unnamed `docker run --rm ... opa exec`. It parses and reserializes the decision record; no OPA container-ID/task/PID receipt is preserved. Intended invocation and automatic removal explain the record gap but do not prove that no such source exists elsewhere.

The identification search stopped when these candidate sources failed to bind the actual OPA process. No downstream host/boot or namespace test, fresh runtime query, clock-history search, new telemetry or acquisition was performed. This is missing evidence, not an observed distinct-clock counterexample.

## Missing evidence a future real deployment would need to retain

1. **OPA evaluation → runtime instance:** an ordinary process/container/task record linking the actual timestamp-producing OPA instance to its container/task ID and PID plus lifetime/start identity. It must associate this evaluation or its native log stream with that instance; an unrelated task ID is insufficient. Native runtime log-stream attribution or existing container/task logging metadata may supply the association where actually retained.
2. **Instance → host and boot:** deployment/runtime placement plus immutable node/VM identity and boot/lifetime identity applicable to the decision. Preserve provenance across daemon restarts or migration. The same is required for the actual NGINX timestamp-producing worker, not merely a helper process or image.
3. **Process → clock domain:** applicable process namespace/runtime configuration and clock semantics, including historical worker/helper relationships if helper observations are used. Zero offsets alone are not namespace identity. Records must apply during the interval rather than merely describe current state.

Candidate sources are existing Docker/containerd task lifecycle and inspection records, OCI/runtime configurations, native log-stream attribution, node/VM placement/boot records and already-retained process namespace evidence. They are retention requirements, not an instruction to add instrumentation. Availability and adequacy in any future deployment remain to be demonstrated. Only after these bindings are established should the minimum interval discontinuity/rate/reference evidence be reconsidered under the unchanged criterion.

## Trust, cost and validation

OPA records are producer-derived and reserialized; Docker records and collector receipts share one operator's custody. Hashes establish supplied-byte integrity, not completeness/authenticity. No inference of enterprise independence follows. A future binding needs authentic applicable runtime records with complete lifetimes and defensible process identity across PID reuse/restarts.

Planning judgment: about 0.5–2 engineer-days to qualify one already-exported, version-known runtime/placement package; access lead time and missing-retention recovery are unknown. Read-only access to scoped runtime/log-attribution and infrastructure records is needed. No retained association means more analysis cannot reconstruct it reliably.

Validation: all 185 source hashes preserved; evidence references, local document links, formatting and documentation-only change scope checked. Protocol commit `c4a03d5` precedes inspection. Milestone and roadmap close together. Final commit and new CI are recorded in the publication PR/owner briefing; no new runtime test is implied by documentation validation.

M9b remains `CLAIM_NOT_DEMONSTRATED`. Historical logging qualification remains `NOT_TESTED_AFTER_TIMING_STOP`. This closes the process-binding inquiry as `NOT_DEMONSTRATED`; it does not request acquisition, merge a PR or change the coverage standard.
