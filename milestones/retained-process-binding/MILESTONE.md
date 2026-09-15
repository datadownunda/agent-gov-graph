# Retained runtime process-binding qualification

[Canonical roadmap](../../ROADMAP.md)

Status: CLOSED — NOT_DEMONSTRATED; stopped at first binding. Owner authorized this retained-package-only test on 2026-09-15, after lineage review c0ff6a3e9726fcf20701b2091dd464356860a1c5. No new telemetry, acquisition, runtime queries or broad time-service search.

## Frozen test and stop rule

Use the 185 manifest-bound M9b archive files, including native/derived OPA and runtime records, command receipts, image/container inspections, Docker events and frozen invocation code. Hash verification confirms supplied-byte integrity only.

1. Look for an actual OPA container/task identity bound to the timestamp-producing process/evaluation. An image ID, evaluation/decision ID, intended command or unassociated container-shaped string is insufficient.
2. Only if established, bind that process/container to an actual host/boot identity.
3. Only if established, compare with retained NGINX host/boot evidence.
4. Only if established, determine applicable timestamp-producing process namespace membership.
5. Stop at the first missing required binding; mark subsequent steps NOT_TESTED_AFTER_BINDING_STOP. Do not fill missing identities from other episodes, current Docker state or assumptions about defaults.

Both common-domain and different-domain conclusions require evidence. A failed binding test returns NOT_DEMONSTRATED, not proof of distinct clocks. Preserve M9b CLAIM_NOT_DEMONSTRATED, timing NOT_DEMONSTRATED and logging NOT_TESTED_AFTER_TIMING_STOP. No shared-clock plausibility can weaken the frozen UTC/applicability requirement.

## Closure

Record exact retained sources, missing evidence, trust limits and future native retention requirements. Update this milestone and ROADMAP.md together. Owner authorized publication and CI if changes are documentation/analysis only. No new implementation or live experiment is authorized. Final result and checkpoint pending.


## Close record

[Result](RESULT.md) and [receipt](receipt.json): no actual OPA container/task/PID association found in the retained episode package. Steps 2–4 remain NOT_TESTED_AFTER_BINDING_STOP. All 185 archive hashes verified. No new telemetry, acquisition or broader time-service search. Owner authorized documentation/analysis publication and CI; exact final commit and CI are recorded in PR/briefing.
