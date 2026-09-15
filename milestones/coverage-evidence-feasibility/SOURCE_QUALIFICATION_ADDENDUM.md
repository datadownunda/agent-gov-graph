# Ordinary-source qualification following owner clarification

[Milestone](MILESTONE.md) · [Original findings](FINDINGS.md) · [Roadmap](../../ROADMAP.md)

The owner confirms that no enterprise/design-partner deployment, external operator contact or separate evidence export is available. Only the existing same-operator local OPA/NGINX environment and preserved M9b artifacts are concrete. New acquisition remains pending. This clarification expands source research; it does not amend or rerun either M9b campaign.

**Verdict remains NOT_DEMONSTRATED.** Required interval-wide timing/applicability and logging completeness evidence is not available in the identified local package. This scoped availability statement is not a claim that ordinary enterprise evidence cannot support assurance. No deployment prevalence survey was conducted; the table describes documented operating characteristics, not a measured claim that most enterprises retain them.

## Source roles, retention and independence

Read this table with the original findings' explicit trust/access/cost matrix. Independence has three separate aspects: generating process, transport/failure path and administrator. Another dashboard or index of the same underlying logs is not independent evidence.

| Ordinary source | What it supports, and does not | Deployment/retention and trust requirement |
|---|---|---|
| Chrony/NTP or system time-service history | Conditional timing estimates; not application placement or unexplained inter-update steps | Native histories/configuration must already be enabled and retained across the interval; current status is not history. Trust reference/rate model and privileged clock-change controls. Separate process from NGINX, often same host/admin; exporting through the target collector creates shared loss risk. |
| Infrastructure/VM time status | Clock/disruption observations within the documented scope; not OPA-to-target agreement by itself | Version, VM identity, hardware uncertainty and historical samples needed. Existing provider records can diversify the process boundary, but do not imply independent custody or retained interval bounds. |
| OS service lifecycle/restart records | Observed service transitions/errors; not every request's log emission | Retention/boot identity and loss policy matter; journal rate limiting or volatile storage can remove evidence. Prefer retained OS/infra evidence outside the target collector; otherwise failure paths overlap. |
| Container lifecycle events | Observed target start/stop/exec events; not complete target logging | Docker historical retrieval is bounded. M9b's retained stream is actual evidence, not proof of universally complete lifecycle history. Same Docker/operator boundary. |
| Native file, rotation and offset evidence | Continuity of supplied file bytes and reader progress; not requests never written | Need all file identities/segments, rotation policy, retained state and cutoff semantics. Filebeat documents rotation/deletion/inode-reuse loss risks; an offset is not an independent expected-event count. [Rotation](https://www.elastic.co/docs/reference/beats/filebeat/file-log-rotation) |
| Collector acknowledgements/sequence state | Progress for messages accepted into that collector/transport; not producer emission | Filebeat retries unacknowledged output and may duplicate events; registry state is operational state, not automatically a retained audit history. RELP adds application acknowledgements but does not eliminate producer or persistence failure. Trust both endpoints and retained state semantics. [Filebeat](https://www.elastic.co/docs/reference/beats/filebeat/how-filebeat-works), [rsyslog](https://docs.rsyslog.com/doc/whitepapers/reliable_logging.html) |
| Infrastructure/service health records | A reported outage or health check at its observation boundary; not complete logging during healthy periods | Prefer already-operated infrastructure records collected separately from the target channel. Monitoring interval, retention and missing-data behavior must be documented. No AGG-created probe/heartbeat qualifies as ordinary evidence. |
| Independent error/outage records | Positive evidence of a relevant failure, if scope/timing match; silence is not evidence of no failure | A separate OS/storage/infra path is preferable. Records shipped through the impaired collector are not independent of that failure; separate admin control must be established, not assumed. |
| Logging-platform ingestion metadata | Received/uploaded event volume and scoped delivery/error observations; not all target effects | CloudWatch IncomingLogEvents counts uploaded events. Counts need population/interval alignment and do not supply a pre-emission denominator. Metric retention/granularity and native record retention must be checked separately. [CloudWatch metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch-Logs-Monitoring-CloudWatch-Metrics.html) |

Clock/system/container characteristics and source links are in [the original review](FINDINGS.md). No current-state source reconstructs unretained history. An integrity chain, byte offset, acknowledgement or ingestion count only becomes a completeness argument after its covered population, failure assumptions and upstream boundary are established.

## Access, cost and friction supplement

Planning judgments only, assuming an already-operated source and authorized exports; access lead time and actual enterprise retention remain unknown. No installation or policy change is included.

- File/rotation/collector state: read native segments, effective collector/input configuration, persisted registry/queue state and destination receipts. About 1–3 engineer-days for one known path; recurring version/rotation/retention mapping. Main friction: state may not be historical or exportable, and sender/receiver ownership differs.
- Infrastructure health and independent outage evidence: read scoped service/host/storage history from its existing owner or API. About 0.5–2 engineer-days for one correlated interval; recurring clock/population alignment. Main friction: separate teams, coarse aggregation and shared collection failures.
- Platform ingestion metadata: read scoped native metrics, log-stream metadata, retention configuration and receiver records. About 0.5–2 engineer-days for one platform; recurring granularity/retention checks. Main friction: access boundaries and aggregates that cannot distinguish missing events from low traffic.
- Time, OS lifecycle and Docker review retain the original matrix's effort assumptions. The same-host source combination does not acquire enterprise independence merely because collection crosses processes.

## Credible combination and smallest real-source test

**One combination is credible enough for conditional qualification, not yet proven sufficient:** already-retained clock history plus OPA/target clock-domain placement; original target segments and applicable configuration/rotation history; ordinary collector delivery state and receiver evidence; separately collected OS/infrastructure failure/lifecycle records. The independent records help challenge shared-channel failures. Residual producer non-emission and privileged changes still require explicit, defensible trust assumptions.

This combination is not currently established in the local environment. Do not install chrony, a collector or a monitor to manufacture it. Collector receipts and infrastructure histories cannot be inferred from Docker availability.

**Recommended smallest real-source test, before any new capture:** an offline comparison for one existing historical interval, using only source-native records already retained. First inventory whether the local VM/host has applicable historical time and failure records for that interval and whether any existing delivery/rotation records genuinely apply to the direct NGINX file path. Record absent components and stop if either dimension lacks support. No synthetic replacement records.

If the required records actually exist, freeze the exact interval, domains, quantitative bound and expiry rules, paths and independent-source mapping; compare producer bytes, native reader/delivery state and receiver evidence where those sources exist. Prefer an already-recorded outage or synchronization loss as a real falsifier. The prior [omission proposal](FALSIFICATION_PROPOSAL.md) remains a separate sensitivity check, never evidence of authentic fault detection. No eligible interval/source combination means NOT_DEMONSTRATED without a live retry.

The original M9b archive alone cannot pass this test. This document proposes the test; it does not claim to have searched private system history, acquired an export or run it. Acquisition remains pending per owner instruction. No further deployment request is needed now.
