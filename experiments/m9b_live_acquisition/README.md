# M9b bounded live acquisition

Result: **ACQUISITION_COMPLETED; coverage NOT_DEMONSTRATED.** This is one real local episode, not a control-effectiveness attestation.

## Goal
Test whether ordinary evidence from the existing OPA/NGINX environment can support all-identity target coverage through the unchanged five-second horizon. The claim and stop conditions were committed in [PROTOCOL.md](PROTOCOL.md) at bf4c78c before implementation; implementation was frozen at 851026e before the sole capture.

## What we accomplished
One real governed read of complaint-789 returned DENY with authority RESOLVED and no executor call. The target stayed active for 10.003730136 seconds after the governed call returned. Both out-of-scope complaint-456 probes returned 200 and match distinct native log records. The retained access file has those two rows and no in-scope served representation. This absence is bounded by the unresolved coverage limits below.

The 25.869556105-second acquisition retained 185 manifest-bound files: native access rows, Docker lifecycle events and command outputs, configuration and inspection endpoints, authority/governance records, and 12 bracketed clock samples. All samples and between-sample checks met the frozen thresholds. The sample offset intervals collectively span -0.984721 to +1.142597 seconds; this is an envelope of sampled uncertainty, not a continuous clock bound. Maximum sample latency was 0.229281789 seconds. Shutdown was graceful, with no forced cleanup or recorded acquisition failures.

[RESULT.json](RESULT.json) is derived from the untouched [capture archive](results/v1/manifest.json). Five labelled availability/metadata omission views each identify their independently missing requirement through the common source assessor; they do not detect authentic source omissions. These sensitivity checks do not demonstrate a positive assurance path.

## Challenges
Both native kernel clock diagnostics report UNSYNC and return value 5 (clock not synchronized), despite zero displayed adjustment and time-namespace offsets. Neither these diagnostics nor the successful bracketed samples justify continuous cross-process clock agreement or applicability to OPA. Endpoint configurations, successful probes and retained lifecycle events also fail to establish uninterrupted logging. These two missing dimensions preserve NOT_DEMONSTRATED.

Pre-capture review strengthened actual omission views, successive-sample clock checks, distinct probe/order checks, source command verification and lifecycle/finalization checks. No live capture was retried and no frozen runner, tests or protocol were changed after observations.

## Technical impact
Only experiment, verification and documentation artifacts were added. Production schemas, correlation, runtime behavior, target configuration and all baseline artifacts remain unchanged. The OPA adapter preserves its parsed decision record by reserialization; original OPA stdout/stderr bytes are not retained. One operator controls target and custody. Hashes bind retained bytes and do not prove source completeness or authenticity.

The unchanged public archive adapter requires three actual scenario focuses. This single episode is incompatible, so its status is PUBLIC_API_NOT_RUN_SINGLE_EPISODE_LAYOUT. No extra governance episodes were fabricated and no CONTROL_EFFECTIVE output is claimed.

## Product and commercial impact
The experiment makes the evidence shortfall inspectable: a longer collection interval and healthy samples do not themselves substantiate negative assurance. That supports explicit abstention as a product behavior, while exposing adoption friction around the evidence a control owner must supply. There is no new buyer validation, pricing evidence, measured customer time-to-value or demonstrated enterprise independence. The capture duration above is machine elapsed time, not total operator effort; total operator minutes were not instrumented. Acquisition needed local Docker access plus ephemeral synthetic target credentials; no practitioner outreach or new infrastructure was used.

## What remains unknown
Whether an existing operational source can support defensible interval-wide timing and logging completeness under explicit trust assumptions; whether practitioners can obtain that source economically; and whether a compatible positive live attestation will follow. This run neither demonstrates nor disproves the overall AI-agent assurance thesis.

## Next recommended milestone
Preregister a narrow coverage-evidence feasibility decision: identify an existing source and an explicit trust contract capable of addressing each remaining dimension, with a concrete falsification test and acquisition-cost estimate. If none is available, retain abstention and request a claim-boundary decision. Do not generalize the adapter or advance to M9a-ii merely to obtain an output. No new technology is proposed.

## Checkpoint and replay
See [VALIDATION.md](VALIDATION.md). Read-only replay produces exactly the original RESULT.json. Verification currently requires the original checkout/archive paths because mount-source paths are checked against them; relocating the archive can fail replay. This portability limit is explicit and was not repaired after capture.

Protocol baseline: 1ee92c58a6bee4a86379bcd7ea4473136aba9fe5. Full implementation freeze: 851026e66dccde4383d36dcb4e17f9859368817e. New live findings are retained locally pending owner approval for a significant public claim, as required by the standing milestone instructions. Prior source-gate PR #3 is published with successful CI and its initial failed CI retained.
