# Coverage-evidence feasibility — findings

**Result: NOT_DEMONSTRATED.** The review identified useful ordinary-source candidates, but did not establish an available, applicable arrangement supporting both M9b dimensions. This is a scoped feasibility result, not proof that enterprise coverage evidence is impossible or universally unavailable. No new episode was acquired.

[Milestone](MILESTONE.md) · [Review protocol](REVIEW_PROTOCOL.md) · [Roadmap](../../ROADMAP.md)

## What was reviewed

Baseline af980b9; review protocol committed at a7bcd7c before detailed assessment, after initial source discovery. The M9b archive still verifies all 185 retained hashes. Its twelve clock observations, two UNSYNC kernel reports, target configuration, lifecycle and two native probe records remain unchanged. `chronyc` and `aws` did not resolve on the current shell PATH; this says nothing about accounts, installations elsewhere or enterprise source availability. No private account/configuration directories were inspected.

The inventory covers the retained local environment plus prospective Linux/EC2 time and native logging/audit sources. Enterprise deployment prevalence and actual customer access were not measured. Documentation describes possible semantics; no enterprise export was obtained. Primary sources below were reviewed on 2026-09-14; mutable vendor pages must be rechecked and matched to deployed versions before a future test.

## Candidate inventory and bounded support

| Candidate and availability | What it could contribute | Unresolved dimension / disposition |
|---|---|---|
| Existing M9b NGINX + Docker + bracketed date/adjtimex; actually retained | Endpoint configuration, native request rows, lifecycle, point timing observations and finalized byte inventory | Neither continuous cross-process timing nor complete event generation/capture follows. Retained local package is insufficient. [M9b source inventory](../../experiments/m9b_live_acquisition/SOURCE_INVENTORY.md) |
| Already-retained chrony configuration, tracking/measurement histories and host lifecycle; prospective, not acquired | Conditional clock uncertainty and synchronization history | Requires correct reference, rate-error assumptions, complete history and mapping from OPA/NGINX timestamp processes to the disciplined clock. No target log completeness. Candidate only. [chrony configuration](https://chrony-project.org/doc/4.8/chrony.conf.html), [chronyc](https://chrony-project.org/doc/4.8/chronyc.html) |
| Already-operated EC2 Time Sync/PHC or ClockBound with retained histories; prospective | Potential bounded-time/disruption observations for that host | Direct PHC needs its additional error contribution; current bounds cannot recover missing history. ClockBound version/architecture and OPA clock mapping must be established. No installation proposed. [AWS bounds](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/compare-timestamps-with-clockbound.html), [daemon](https://github.com/aws/clock-bound/blob/main/docs/clockbound-daemon.md) |
| Already-retained Linux journal/collector/configuration/rotation histories; prospective | Some loss, service and retention indicators for messages entering the configured channel | Journald can drop rate-limited messages and emit loss counts; absence of a warning cannot prove no loss before entry or loss of the warning itself. Must first prove the target uses this channel. M9b writes directly to a file. [systemd source documentation](https://github.com/systemd/systemd/blob/main/man/journald.conf.xml) |
| Existing CloudTrail log/digest chain, historical selectors/configuration/status and account/Region scope; prospective | Validation of delivered files and chain continuity under provider/key/custody trust | Does not cover local NGINX file-serving; using it as the target changes the environment/observation boundary. Delivered-file integrity does not establish all relevant events were produced and delivered or bind OPA time. Not an M9b repair. [Integrity](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-intro.html) |

Chrony documents a conditional error calculation including remaining system-clock correction, root dispersion and half root delay, assuming the reference is correct. `maxclockerror` supplies an assumed inter-update rate limit. Applying this over an interval also requires excluding or detecting clock changes/disruptions and proving process placement; those are reviewer requirements, not guarantees supplied by the manual.

NGINX supports conditional/disabled logging and buffering; effective path/configuration must therefore be demonstrated for the interval, not inferred from a producer name. Its request timestamp is at log write. M9b's preserved configuration has no configured access-log buffer, but that alone does not prove every relevant write succeeded. [NGINX log semantics](https://nginx.org/en/docs/http/ngx_http_log_module.html)

Docker documents limited historical event retrieval (last 256 events). A fresh query cannot be assumed to reconstruct an arbitrarily old interval. This is not a claim that the archived M9b live stream lost events. Lifecycle evidence is not a count of target requests. [Docker events](https://docs.docker.com/reference/cli/docker/system/events/)

CloudTrail data events are not enabled by default; historical selectors and resource/Region/account coverage matter. Its `eventTime` comes from the service endpoint host; the reviewed field description supplies no numerical OPA-to-endpoint uncertainty bound. [Event selection](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html), [timestamp semantics](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-record-contents.html)

An empty digest supports a statement about files delivered during its interval, not an independent proof that no relevant target effect occurred. Typical CloudTrail delivery latency is not guaranteed; an arbitrary waiting period cannot close late delivery under the unchanged standard. Observation horizon and collection finalization are separate. [Digest semantics](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-digest-file-structure.html), [delivery](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/get-and-view-cloudtrail-log-files.html)

## Explicit trust contracts still requiring substantiation

These are proposed review requirements, not established assumptions or assurances.

| Candidate | Producer / clock trust | Collector / custody trust | Lifecycle / completeness / administrator boundary |
|---|---|---|---|
| Local retained package | OPA and NGINX behave as configured; sampled clocks only | Operator retains all supplied bytes; hashes detect later changes only | Docker observations and config endpoints; no complete-path guarantee; same administrator throughout |
| Chrony or already-operated bounded-time service | Correct upstream reference and deployed implementation; justified rate/disruption bound; exact application-clock mapping | Authentic, complete update/configuration exports and retention; bound freshness | Clock changes, daemon restarts and VM/process moves accounted for; privileged administrators cannot silently defeat the asserted contract |
| Journal/ordinary collector plus direct native logs | Target actually emits every scoped record into the mapped path | Loss/retry/queue/rotation states and all finalized segments retained; collector receipt is not producer completeness | No unexplained rate limits, drops, scope exclusions or uncovered intervals; trust and independence of target, collector and export administrators stated separately |
| CloudTrail package | Correct provider event-generation semantics and timestamp behavior for selected APIs; no inherited OPA clock guarantee | Provider keys, original object metadata, complete digest/log inventory and custodian export trusted | Historical selectors, trail changes and delivery state; no unjustified lateness cutoff; AWS trust domain distinct from customer trail/bucket administrators |

## Acquisition and adoption cost

Engineering ranges below are planning judgments for an already-operated source, not measured estimates, prices or validated customer commitments. They exclude unknown access/security-review lead time.

| Candidate | Read access needed | Initial review effort | Ongoing burden / friction |
|---|---|---|---|
| Local archive | Repository evidence files | Under half a day for this limited review; not a logged time measurement | Low access friction; cannot close either gap without additional support |
| Linux time histories + placement | Export access to time-daemon config/logs and relevant host/process lifecycle | 0.5–1 engineer-day if version-known and complete; several days if retention/identity unclear | Track configuration, clock-domain and retention changes; infrastructure-owner involvement |
| EC2 bounded-time histories | Existing retained bounds/disruption/configuration and instance placement exports | 1–3 engineer-days if already retained; otherwise not presently acquirable as historical proof | Hardware/version differences and cross-team ownership; installing a new daemon is outside scope |
| Existing logging channel evidence | Relevant native segments, effective/historical config, retention/rotation and collector loss/state exports | 1–3 engineer-days for one known path | Highest uncertainty: loss before the collector may be invisible; recurring scope/retention review |
| Existing CloudTrail trail export | Read trail configuration/selectors/status, scoped S3 log/digest objects and signature metadata/public keys; decryption permission if needed | 1–3 engineer-days for one scoped existing trail export | Account/Region/selector changes, retained metadata and late delivery; prerequisite event recording may not already exist |

These are access categories, not a ready-to-apply IAM policy. No access was granted or tested. If a customer must enable new logs solely for AGG, that is a separate adoption/architecture decision, not evidence already operated. No new collector, signing infrastructure or telemetry was built.

## Conclusion and owner decision

The local evidence remains insufficient. Documented enterprise components make further qualification plausible, but no concrete accessible package with both dimensions was demonstrated. Therefore neither positive feasibility status nor universal COVERAGE_EVIDENCE_NOT_AVAILABLE is warranted.

**Recommend one next step:** qualify one already-operated Linux target/OPA deployment's existing evidence export under a named trust contract. The [smallest proposed test](FALSIFICATION_PROPOSAL.md) is read-only and offline. It must first establish that both timing and target-channel evidence actually exist; no new capture or adapter work should start from mere documentation plausibility.

This is a consequential evidence-boundary decision for the owner: approve a named existing-source qualification with explicitly reviewable trust assumptions, or reconsider the claim if no such source is obtainable. The present review does not relax the five-second standard, equate operational trust with measured coverage, or advance M9a-ii. Publication of this new conclusion and selection of the next protected task await owner review.

## Plain-English impact

We tested the feasibility of obtaining evidence, not whether the control worked. The useful discovery is where ordinary sources help and where their guarantees stop: timing history, collector loss indicators and delivered-file integrity address different parts of the problem. None should be promoted into whole-path completeness.

Technically this is documentation-only. Commercially, the likely adoption constraint is obtaining a coherent evidence package across infrastructure and control owners, rather than adding one integration. That is a hypothesis to validate with a real export; buyer demand, willingness to pay and time-to-value remain unknown. The product can identify why assurance is unavailable, but this review does not yet demonstrate useful positive enterprise assurance.
