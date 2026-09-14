# Historical-record qualification result

**NOT_DEMONSTRATED — stopped at timing.** M9b remains CLAIM_NOT_DEMONSTRATED. No new telemetry, native episode, clock change or omission experiment was performed.

[Milestone and frozen stop rule](MILESTONE.md) · [Roadmap](../../ROADMAP.md) · [Machine-readable receipt](receipts/qualification.json)

## Interval, search boundary and stop

The archived OPA decision is `2026-09-14T17:42:01.508951584Z`; its unchanged five-second horizon ends at `17:42:06.508951584Z`. These are the reference interval labels, not an assertion of proven cross-clock alignment.

All 185 M9b archive hashes matched. A narrow immediate-filename inventory of existing host/VM log locations found no named chrony/NTP/clock-history source; it did find ordinary system log files, whose contents were not used as clock evidence. A retained macOS `timed` query for 17:41–17:43 UTC returned zero records, exit 0, empty stderr. The exact query and scope are in the receipts. It uses default log levels and is not an exhaustive search of unified logging, rotated/private histories or every possible synchronization source. Empty output proves neither no clock changes nor global absence of records.

The first query was sandbox-blocked. Escalation was then rejected by the usage limit before execution; after the owner reset usage and requested a rerun, the same read-only query completed. These are retrieval attempts, not new live acquisitions.

**Stop:** no retained evidence examined supports a quantitative uncertainty bound throughout the interval with demonstrated applicability to both OPA and target clocks. Healthy point samples cannot fill this gap. Qualification stopped immediately; logging qualification and challenge execution were not attempted. The logging account below is an inventory of previously preserved evidence, not a second qualified finding.

## 1. Timing applicability/continuity — NOT_DEMONSTRATED

**Exact evidence.** Under [M9b archive](../../experiments/m9b_live_acquisition/results/v1/manifest.json): `opa.jsonl`, `capture.json`, date command triplets `commands/010` and `013`–`023`, kernel triplets `011`, `012`, `024`, `025`, and `execution-lock.json`. Triplets include stdout, stderr and invocation metadata; exact hashes are in the qualification receipt. Additional historical lookup: [timed query](receipts/timed-query.json) and [location inventory](receipts/source-locations.json).

**Producer/custody.** OPA's parsed native decision was reserialized by the existing adapter. Docker-executed BusyBox/kernel interfaces supplied target time observations; the local Python collector recorded wall/monotonic brackets. macOS retained/query infrastructure produced the lookup response. One operator controls deployment and custody; query output is a present export of retained records, not original authenticated source bytes.

**Directly established.** The archived decision timestamp, twelve sampled readings/brackets and two kernel snapshots are present. Both kernel snapshots report UNSYNC / clock not synchronized. The historical query yielded no matching records within its stated scope. Neither UNSYNC nor an empty lookup proves clocks actually diverged.

**Required trust and residual inference.** Interval-wide use would require a correct time reference, justified inter-update rate/disruption bounds, complete applicable clock/configuration history and mapping of OPA/NGINX timestamps to those clocks. Those requirements are not established. Extending samples across gaps or assuming same-host clock identity would remain unsupported inference.

**Independence.** Clock commands and host lookup are separate from the NGINX access-log channel, but share operator/host infrastructure and are not independently administered. Separation does not create missing historical bounds or prove OPA applicability.

**Missing evidence / likely ordinary source.** Already-retained time-service update/configuration history plus host/VM disruption and process-placement records, with explicit reference/rate assumptions. Chrony/NTP or existing infrastructure time histories are candidates, not guaranteed sufficient. See the [source/trust review](../coverage-evidence-feasibility/FINDINGS.md).

**Enterprise cost, planning judgment.** About 0.5–1 engineer-day for a complete version-known export and mapping; several days if VM placement, retention or ownership is unclear. Requires read access to clock configuration/history and relevant lifecycle evidence. Security-review lead time and actual retention are unknown. No source was created to satisfy this requirement.

## 2. Logging/evidence-channel completeness — NOT_TESTED_AFTER_TIMING_STOP

**Exact inventoried evidence.** Same M9b archive: `native/access.jsonl`, `nginx.conf`, `events.stdout`, `events.stderr`, `capture.json`; command triplets `007` (initial inspect), `008`/`026` (configuration), `027`/`030` (running/final inspect), `028`/`029` (QUIT/wait), `031` (native logs). Existing [M9b result](../../experiments/m9b_live_acquisition/RESULT.json) retains their prior assessment. No new logging assessment was run.

**Producer/custody and direct observations.** NGINX produced two out-of-scope successful request rows. Docker produced lifecycle/inspection outputs; the same local collector/operator preserved them. The prior record contains endpoint configuration, probe linkage and graceful closure. It does not directly establish every relevant request produced a retained log row throughout the interval.

**Required trust and inference.** A complete-path claim requires applicable logging scope/configuration, successful emission/write/retention, all required segments and defensible finalization; applicable loss/recovery evidence must cover the actual direct-file path. Inferring completeness from two probes, silence in errors or service uptime is unsupported. No separate collector path or rotation segment is invented for M9b.

**Independence.** The target log cannot independently prove its own completeness. Docker events are a separate event stream but share operator/infrastructure and do not count target requests. OPA decisions and client probes do not establish the whole target-event population.

**Missing requirement / likely ordinary sources.** Retained source-native file/rotation continuity and applicable delivery/loss/recovery state, preferably challenged by separately collected OS/storage/infrastructure failure records. These are possible enterprise sources; none is newly established here. Delivery receipts cover accepted messages, not omitted producer events. See the [expanded source assessment](../coverage-evidence-feasibility/SOURCE_QUALIFICATION_ADDENDUM.md).

**Enterprise cost, planning judgment.** Roughly 1–3 engineer-days for one known native/collector path, plus 0.5–2 days if separate infrastructure evidence must be aligned; ranges overlap and are not a summed quote. Requires scoped native files, configuration/retention and relevant collector/infra read access. Shared-channel loss and missing historical state may make the evidence unobtainable despite access.

## Decision, impact and validation

This test does not substantiate a combined coverage contract, and does not combine weak evidence to obtain one. It also does not establish universal COVERAGE_EVIDENCE_NOT_AVAILABLE: the search is bounded and timing support remains unproven. No new live acquisition is proposed.

The next dependency is the missing already-retained timing history and clock-domain applicability evidence, not another capture. If such a source later becomes available, preregister qualification against its actual semantics before reconsidering logging. Until then retain NOT_DEMONSTRATED and the acquisition hold. Enterprise usefulness and willingness to supply this package remain unvalidated; the practical cost is evidence access and cross-owner reconstruction, not proof supplied by additional AGG fields.

Validation: independent review confirmed all 52 referenced hashes and all 185 original archive hashes match, the narrow query receipt, stop semantics and custody limits; exact relevant timing references and hashes retained; query stdout/stderr and limitations recorded; document links and formatting checked. No runtime change or new runtime test. Review protocol commit `e179afa`; result checkpoint in the owner briefing. Roadmap and milestone closure committed together. New-result CI/publication pending owner review; previous CI does not validate this finding.
