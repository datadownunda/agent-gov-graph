# Stage 1 evidence eligibility review

Decision: **NOT_DEMONSTRATED** on the four frozen evidence families. No real episode substantiates every required coverage dimension. This is a source-eligibility result, separate from the public-API diagnostic. No replacement native evidence was generated.

The unchanged [control](../control_attestation/control.json) requires five seconds after DENY for `complaints-static-v1`, `read`, `employee_complaint`, at `TARGET_REPORTED_REPRESENTATION_SERVING`. It does not establish client receipt or downstream use. Paths below identify existing preserved artifacts and producer implementations; none were edited.

## Eligibility matrix

| Required dimension | Live target_outcome v1 | Deterministic control_attestation fixture | NGINX conformance v1 | OPA conformance v1 |
| --- | --- | --- | --- | --- |
| Actual control/target/resource/action episode | Real blocked DENY for complaint-789 and matching target contract; operator-controlled scenario | Exact declared binding, wholly synthetic | Real requests to complaint resources; no governance DENY episode | Policy evaluations only; last two DENY complaint-456; no target episode |
| Decision plus five-second horizon | Fails: declared interval ends 0.113120417 seconds after native OPA decision | Declared 12-second capture includes five-second horizon, with invented fixture timestamps | No decision; complete recorded campaign lasts only 1.428437 seconds | No target capture or post-DENY target horizon |
| All target identities | Config logs server requests without identity filter; coverage declaration and identity mapping are actor-scoped; no independently substantiated full-population capture | `ALL_TARGET_IDENTITIES` is fixture author assertion | Config logs all server requests; eight controlled requests from one identity do not substantiate all-identity continuity | Inapplicable to target capture |
| Snapshot binding | Native file hash in manifest and ingestion locations; no control-specific support capture binding | Support digest matches authored empty native file | Native file inventory digest and row byte references | Native stdout/stderr inventory digests |
| Availability, continuity, finalization | Two native outcomes; capture/flush prose and runner stop sequence, no archived lifecycle/collector continuity evidence for required horizon | Booleans and finalization time authored by fixture | Per-request row counts and quit/wait sequence support finite request capture; no required control interval | Eight completed subprocess captures, not target coverage |
| Clock bound and source | Cross-system synchronization explicitly unproven; no measured maximum offset | Zero declared; basis explicitly says no measured live synchronization | Host capture times and NGINX timestamps; no measured bound | Host invocation times and OPA timestamps; no measured bound to target |
| Gaps and candidate ambiguity | Bounded view has no outcomes; supplied-snapshot completeness UNKNOWN; unknown omissions remain | False flags authored by fixture | Eight-row agreement for planned requests; no control candidate population | Evaluation cardinality only; no target population |
| Independence and trust | OPA and NGINX produce native records separately from client, all under experiment operator control | No native producer ran | NGINX is native producer; response and access row are same transaction | OPA is native producer; response and decision log are same evaluation |
| Eligible | **No** | **No — semantic fixture** | **No — different campaign and purpose** | **No — different campaign and purpose** |

## Live target_outcome: exact horizon failure

[governance.jsonl](../target_outcome/results/v1/governance.jsonl), line 3, binds blocked-deny to complaint-789 and records native `opa_decision_at = 2026-09-06T01:08:11.175841583Z`. The [reconciliation](../target_outcome/results/v1/reconciliation.json) uses that value as `blocked-bounded.claims.governance[0].observed_at`; the later event-recorded timestamp is not the decision time.

[blocked_coverage.json](../target_outcome/results/v1/blocked_coverage.json) declares `01:08:11.043651` through `01:08:11.288962` UTC. Exact subtraction of recorded timestamp values gives the following nominal durations. These are not verified physical elapsed times: cross-clock offsets and even host wall-clock jumps are unbounded in the preserved evidence. All other calculated durations in this review have the same limitation.

- Total declared interval: **0.245311 seconds**.
- Declared post-decision coverage: **0.113120417 seconds**.
- Required endpoint: **01:08:16.175841583 UTC**.
- Missing duration after declared endpoint: **4.886879583 seconds**, before considering clock uncertainty.

Even the [manifest](../target_outcome/results/v1/manifest.json) completion timestamp, `01:08:11.519274`, is only **0.343432417 seconds** after decision. Completion is not an observation endpoint and cannot extend coverage; it also cannot rescue the five-second requirement.

[native/access.jsonl](../target_outcome/results/v1/native/access.jsonl) contains two rows, ending at NGINX `msec=1788656890.985`, before the blocked decision. They provide positive outcome observations from earlier scenarios, not evidence that subsequent silence is complete. [target.json](../target_outcome/results/v1/target.json) maps paths to complaint resources. [nginx.conf](../target_outcome/results/v1/nginx.conf) configures an unfiltered server access log; [identity_mapping.json](../target_outcome/results/v1/identity_mapping.json) maps one synthetic account to one agent. Neither proves absence across other identities, endpoints or missing records throughout the required interval.

[Producer code](../target_outcome/run_experiment.py), lines 141–166, writes interval start before the governed action and interval end immediately after it, then stops NGINX. There is no five-second post-decision wait. Lines 133–140 author [target_runtime.json](../target_outcome/results/v1/target_runtime.json), including the custody/flush prose; lines 180–183 author the manifest, explicitly limiting it to unauthenticated content integrity. No native stop receipt, logging-error stream, time-synchronization measurement or collector continuity record is preserved in this family. A successful stop call in source code supports the intended capture procedure, not independently authenticated completion.

The reconciliation already states that completeness is unknown, content digests do not authenticate producers or prove completeness, and absent records do not prove absent activity. Its empty bounded outcome population cannot resolve omitted candidates. The native producer boundary is real; independent administration of the evidence custody is not demonstrated.

## Deterministic fixture: explicit semantic positive

[coverage_observations.json](../control_attestation/results/v1/deterministic_fixture/coverage_observations.json) declares capture from `12:00:01` through `12:00:13`, finalized at `12:00:14`, all identities, no gaps, no ambiguity and zero offset. [governance.jsonl](../control_attestation/results/v1/deterministic_fixture/governance.jsonl), line 3, places the decision at `12:00:02`: the declared capture has **11 seconds** after decision, while [blocked_coverage.json](../control_attestation/results/v1/deterministic_fixture/blocked_coverage.json) declares **10 seconds** after decision. Both fit the five-second rule numerically.

The native digest is the SHA-256 of an empty file. [Producer code](../control_attestation/run_experiment.py), lines 37–99, authors every timestamp, empty native file, capture flag, scope and clock value. [target_runtime.json](../control_attestation/results/v1/deterministic_fixture/target_runtime.json) explicitly says `DETERMINISTIC_FIXTURE_NO_TARGET_PROCESS`. This is suitable for testing semantic acceptance, never evidence that a real capture was available, continuous, complete or synchronized.

## NGINX producer conformance: finite positive requests

[capture.json](../nginx_producer_conformance/results/v1/capture.json) spans `15:58:39.369374` through `15:58:40.797811` UTC on September 14: **1.428437 seconds**, including setup and shutdown. Eight [native rows](../nginx_producer_conformance/results/v1/native/access.jsonl) correspond to eight captured responses and increasing per-request row counts. [nginx.conf](../nginx_producer_conformance/results/v1/nginx.conf) and [nginx-T.txt](../nginx_producer_conformance/results/v1/nginx-T.txt) support the configured log contract; [manifest.json](../nginx_producer_conformance/results/v1/manifest.json) binds preserved bytes.

[Producer code](../nginx_producer_conformance/run_experiment.py), lines 126–163, launches the target, captures effective configuration, waits for each expected row, then requests quit and waits. This supports the eight-request identifier experiment under its custody assumptions. It supplies no governance decision for this episode, measured clock offset, five-second negative observation, or independent capture-continuity source. Combining it with the September 6 target_outcome decision would invent one episode from separate campaigns.

## OPA producer conformance: evaluations, no target observation

[capture.json](../opa_producer_conformance/results/v1/capture.json) records eight completed invocations without errors. Preserved [invocation 001](../opa_producer_conformance/results/v1/invocations/001/invocation.json) shows stock `opa exec` with console decision logs, network disabled, and captured process times; its [stderr](../opa_producer_conformance/results/v1/invocations/001/stderr.bin) is native decision evidence. Invocations [007](../opa_producer_conformance/results/v1/invocations/007/stderr.bin) and [008](../opa_producer_conformance/results/v1/invocations/008/stderr.bin) deny complaint-456; none runs or observes the NGINX target.

The [frozen producer code](../opa_producer_conformance/results/v1/frozen/run_experiment.py), lines 224–273, captures independent invocations and inventories outputs. It supplies no all-identity target log, target snapshot, target clock bound or target finalization. As its [result](../opa_producer_conformance/results/v1/result.json) states, output and log are two representations of one evaluation, and hashes establish custody consistency rather than authentication. Producer conformance cannot substitute for coverage evidence.

## Consequence

Stage 1 stops at **NOT_DEMONSTRATED**. The existing live episode's declared interval falls short of the frozen horizon even before accounting for its unsubstantiated clock uncertainty; other coverage dimensions also remain unsubstantiated. This neither changes historical results nor falsifies the general assurance thesis. The [acquisition proposal](ACQUISITION_PROPOSAL.md) is a separately reviewable follow-on scope, not authorization to create replacement evidence within M9b.
