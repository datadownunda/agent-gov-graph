# Retained clock-domain lineage review

[Roadmap](../../ROADMAP.md) · [Frozen M9b protocol](../../experiments/m9b_live_acquisition/PROTOCOL.md) · [Historical qualification](RESULT.md)

**Finding: a common OPA/NGINX clock domain is plausible but NOT_DEMONSTRATED from the retained evidence.** Distinct domains are not demonstrated either. No new source query, telemetry, capture or experiment was performed for this review. M9b remains CLAIM_NOT_DEMONSTRATED; logging remains NOT_TESTED_AFTER_TIMING_STOP.

ESTABLISHED means directly supported at the stated scope by supplied records, subject to their same-operator custody. ASSUMED means a plausible interpretation requiring unverified applicability. MISSING means the required historical binding/record is not supplied. Code intent is not runtime placement; a sampled offset is not namespace identity.

All archive paths below are relative to [the retained archive](../../experiments/m9b_live_acquisition/results/v1/manifest.json).

## Evidence-lineage matrix

| Process / edge | Status | Exact retained evidence and limit |
|---|---|---|
| OPA decision → intended OPA invocation | ESTABLISHED, supplied-record/code scope | `opa.jsonl`; `frozen/src/governance_event.py`, `evaluate_policy_with_decision_log`: `docker run --rm -i ... openpolicyagent/opa:1.19.0 exec`. Native record is parsed/reserialized; original OPA stdout/stderr and per-invocation container receipt absent. |
| OPA timestamp-producing process → actual container ID/PID | MISSING | No OPA container inspect, runtime task/PID receipt or create/start event binding. `commands/004` inspects an image, not the executed container. `events.stdout` is target-filtered and contains only the NGINX container ID. |
| OPA process/container → time namespace | MISSING | No OPA process namespace identifiers or runtime namespace binding retained. Frozen invocation contains no explicit time-namespace option; absence of an option is not observed namespace identity. |
| OPA container/namespace → Linux VM host/boot | ASSUMED | Frozen Docker call plus `commands/002.stdout` showing desktop-linux/linux server make common routing plausible. No historical OPA container-to-daemon/VM/boot identity binding. |
| OPA VM/process → actual timestamp clock/read semantics | ASSUMED | A UTC-shaped OPA timestamp does not establish the deployed clock API, clock substitution absence or read/caching uncertainty. No timestamp-call trace or applicable binary/kernel clock binding retained. |
| NGINX serving process → target container | ESTABLISHED, container-level | `commands/005`, `007`, `008`, `009`, `026`, `027`, `030` bind startup/config/version/lifecycle to container `5b2e78f600d1560ce8b8f4de2cf50b137edc6692a96218966077ec76b83f63`. Initial inspect records PID 9912, but this is not a complete worker-PID genealogy. |
| NGINX timestamp worker → time namespace | MISSING | `commands/012.stdout` and `025.stdout` show zero monotonic/boottime offsets for `cat /proc/self/timens_offsets` exec helpers. They do not contain worker namespace inode/identity, a CLOCK_REALTIME identifier or a historical worker/helper equivalence binding. Equal/zero offsets do not prove equal domains. |
| NGINX container → queried Docker server | ESTABLISHED, supplied command-stream scope | Target ID, inspect and events match; version receipt identifies a Linux Docker Desktop server. This identifies the observed daemon interface, not an immutable VM/boot identity. |
| NGINX container/server → continuous VM host/boot | ASSUMED | No retained VM boot-ID/placement/disruption lineage. Target lifecycle endpoints alone do not prove the VM clock domain stayed unchanged. |
| NGINX process/VM → actual timestamp clock/read semantics | ASSUMED | `nginx.conf` binds native fields `$msec`/`$request_time` to rows. No retained timestamp-clock implementation/cache-age bound or process-to-kernel clock binding. Ordinary expected behavior is not demonstrated historical applicability. |
| Both putative clocks → governing time service/reference | MISSING | `commands/011.stdout` and `024.stdout` report UNSYNC; zero offsets are not reference identity. No applicable service/reference history. The previously retained narrow macOS timed lookup returned `[]`, not evidence of Linux VM time discipline. |
| Collector wall/monotonic observations → target/OPA clocks | ASSUMED for sampled target relation; MISSING for continuous OPA relation | `capture.json` and date command brackets relate local collector readings to target helper observations at samples. Client platform is Darwin while server is Linux (`002.stdout`). Do not treat collector monotonic time as the Linux VM clock or transfer its >10-second hold directly into an OPA/NGINX clock proof. |

## Exact unresolved bindings

1. The actual OPA process/container and its daemon/VM/boot placement.
2. Each timestamp-producing process's applicable clock domain/API; worker/helper namespace equivalence cannot be inferred from zero offsets. For ordinary Linux semantics, wall-clock and namespace-offset behavior must be distinguished; an identical time namespace alone is not the whole proof.
3. Historical continuity of that domain and a quantitative bound on relevant steps, rate/slew, pause/resume or clock substitution across the interval.
4. Timestamp representation/read/caching uncertainty and applicability of the collection endpoint to the interval.
5. Any reference/UTC support required by the frozen criterion; the common-domain hypothesis cannot silently remove it.

## If a common domain were established

A shared constant offset cancels in a difference between two clock readings; a shared clock change between those readings does not. Thus two independent synchronization histories need not necessarily be the minimal way to bound *relative* timing. But common-domain membership alone is insufficient for this M9b record.

Minimum historical support would be: both process-to-clock bindings over their relevant lifetimes; domain/boot continuity; a justified interval bound on rate error and relevant discontinuities; bounded timestamp read/representation/cache effects; and a defensible link from the observation endpoint to that same domain. A guarantee about simultaneous agreement is not a guarantee that five recorded seconds represent five elapsed seconds.

For reasoning only, let `C(t)=t+b+e(t)` and timestamp read errors be `q1,q2`. The recorded difference is elapsed time plus `e(t2)-e(t1)+q2-q1`; the constant `b` cancels. The retained evidence must bound the remaining terms. No numerical bound is supplied by this review; absence of observed jumps between point samples cannot supply it. Paired opposite steps between samples remain a counterexample.

**Frozen-criterion limit:** M9b explicitly requires justified interval-wide timing and OPA applicability and rejects host-monotonic/endpoint-only support. A relative-clock argument could address part of that obligation if substantiated; it cannot be substituted for any required UTC/reference or finalization support. If satisfying the claim requires replacing the frozen UTC-bound requirement with elapsed-only semantics, that is a claim change requiring separate owner review, not a passing interpretation here.

## If the domains are distinct

For each domain require applicable retained synchronization/error history against an identified common reference, complete enough to bound uncertainty throughout the interval, plus each process's placement/read semantics. Bound the relative uncertainty conservatively from the two domain bounds and read effects; do not presume cancellation or statistical independence. Shared reference error may cancel only where that dependence is itself justified. Steps, migration and discontinuities remain relevant even with a common reference.

This is the conditional requirement, not a finding that the episode actually used distinct clocks.

## Candidate ordinary sources and trust

No candidates were queried or acquired in this review. Potential already-retained sources are:

- Docker/containerd task/create/start/delete records and OCI runtime configuration tying the actual OPA and NGINX PIDs to container IDs; retained process namespace links where available.
- VM/host boot and placement records, kernel lifecycle and already-operated hypervisor pause/resume/disruption records; these may establish shared host continuity independently of target access logging.
- Applicable deployed timestamp implementation/configuration evidence tying each field to its clock and bounding resolution/read/cache effects. General version labels alone are insufficient.
- Existing system clock discipline/change records, chrony/NTP updates and configuration, and already-retained kernel/hypervisor disruption evidence. Their completeness and reference/rate assumptions must be explicit; status snapshots alone are insufficient.

Trust must cover authentic and complete exported placement/lifecycle/clock records, applicable implementation behavior, correct rate/reference assumptions and no unobserved privileged changes. A common host creates shared failure modes. Same-operator custody remains; an infrastructure log delivered through the impaired target collector is not independent evidence of that channel's health. Capabilities/restart settings restrict some mechanisms but do not prove host administrators or hypervisor could not change time.

## Smallest proposed falsification test — not executed

First, perform an offline binding check on a single already-retained interval: can actual OPA and NGINX timestamp-producing processes be tied to the same immutable host/boot and relevant clock semantics? **Missing OPA container/process binding stops that test in the present package.** No new source or capture should be created to fill it.

Only if that gate passes, freeze the claimed relative/UTC bound and use already-retained authentic clock-change/disruption evidence to test whether it rejects or bounds the interval appropriately. Separately labelled scratch views can withhold an OPA placement edge, substitute a different boot/domain, or remove required clock-change coverage; each must become insufficient. A proposed jump-and-reversal between healthy samples challenges any sample-only reasoning. Such a thought/scratch challenge is not an observed clock event, and an absent authentic disruption record cannot be described as demonstrated fault detection.

Recommendation: preserve NOT_DEMONSTRATED and the missing-edge inventory. Do not seek another synchronization source as though separate clocks were already proven, and do not presume a common clock merely because both commands used Docker. First prerequisite is retained OPA process/container/host binding; it is missing here. This review neither reopens logging qualification nor proposes live acquisition.
