# Agent Gov Graph — canonical technical roadmap

Decision baseline: approved M9b checkpoint [`54b18b6`](https://github.com/datadownunda/agent-gov-graph/pull/4), CI #39 green. Updated 2026-09-14 from the owner's roadmap/sequence instructions and the subsequent scoped feasibility review (publication and bounded source qualification approved). Closed means the bounded milestone is resolved; it does not imply a positive claim or a merged PR. Historical verdicts and evidence remain authoritative at their recorded scope.

## Closed milestones

| Milestone | Final status | Bounded conclusion / evidence |
|---|---|---|
| M1 — independent foreign evidence | CLOSED — demonstrated, bounded | Separately running OPA writes evidence consumed read-only later; process/persistence independence, not enterprise custody independence. [Record](docs/foreign-opa-experiment.md) |
| M2 — correlation without shared identifiers | CLOSED — identity/reliability claim materially falsified | Candidate matching exists, but contextual matching fails under repetition, skew and impostors. Mutual uniqueness does not establish identity; categorical assertions preserve assumptions and ambiguity. [Evidence](docs/foreign-opa-experiment.md), [assertions](docs/correlation-assertions.md) |
| M2 — ordinary-feature extension | CLOSED — no generally sufficient tested feature set | Extra fields reduced some collisions across 8,560 synthetic measurements but did not resolve observationally identical replacements. [Record](experiments/foreign_opa/results/ordinary-features-v2/README.md) |
| M3 — real model-driven agent | CLOSED — demonstrated, bounded | Live model selected authorized and unauthorized resources; governance denied unauthorized selections. Two earlier quota-failed runs remain preserved; successful third run had 17 valid proposals and 3 HTTP 429 failures. [Record](docs/model-agent-experiment.md) |
| M4 — decision-time authority | CLOSED — demonstrated, bounded | Reconstruct authority against the supplied preserved revision at explicit times; current state is insufficient, and revision completeness/authenticity is not established. Not full bitemporality. [Record](docs/decision-time-authority.md) |
| M5 — delegation semantics | CLOSED — demonstrated, conceptual/bounded | Historical reconstruction works with explicit authority-bearing delegation records. No proof mainstream runtimes emit those records. [Record](docs/delegation-semantics.md) |
| M6 — governed/executed/target-outcome reconciliation | CLOSED — demonstrated, bounded | Independent NGINX process evidence supports a DENY/target-effect contradiction. Client received 168 bytes before client-side failure; that failure cannot prove no effect. [Record](docs/action-reconciliation.md) |
| M7 — single-action attestation | CLOSED — demonstrated, narrowed | Positive rule demonstrated with synthetic evidence; live evidence supports exception/abstention, not live CONTROL_EFFECTIVE. Adjudicator blinded to experiment truth. Scope and coverage assumptions remain material. [Record](docs/control-effectiveness-attestation.md) |
| M7 — internal-error hardening | CLOSED — implemented/validated | Internal processing faults are distinct from evidence states and control findings. [Record](docs/control-effectiveness-attestation.md) |
| M8 — graph-value Gate A | CLOSED — GRAPH_SEMANTIC_VALUE NOT_DEMONSTRATED; GRAPH_DATABASE_VALUE NOT_TESTED | Derived graph did not meet frozen value criteria against fair indexed Python baseline. Database Gate B never opened; no claim a graph database was tested and failed. [Checkpoint](docs/m8-gate-a-checkpoint.md) |
| M9a-i — identifier withholding | CLOSED — CLAIM_NOT_DEMONSTRATED | Contextual linkage yielded unacceptable false links; investigation-grade candidate leads only, not assurance-grade under tested conditions; investigation utility remains unvalidated. Original stale-baseline provenance and later compatibility checks retained. [Record](experiments/identifier_withholding/README.md), [baseline review](docs/m9a-i-baseline-review.md) |
| Strong-link assurance falsification | CLOSED — historical FAILED | Synthetic copied/reused-ID and scope cases exposed failures; later producer qualification narrows interpretation. Does not show native producer-generated identifiers are inherently ambiguous. [Record](experiments/strong_link_assurance/README.md) |
| M7 v2 — scope/namespace assurance gates | CLOSED — implemented/validated | Stricter gates reduced false substantive exceptions 18→0 through abstention, but lost 12 legitimate exception evaluations; 21 false links and 21 merges remained. Separate conformance, not a rescue of FAILED. [Record](experiments/m7_scope_gate/README.md) |
| Producer-qualification review | CLOSED — interpretation narrowed | Several apparent hard limits reflect synthetic scenario/producer-contract mismatch. Preserve the original failures and distinguish received/forwarded IDs from native generated IDs. [Accounting](experiments/m7_scope_gate/accounting/v4-reconciliation.md), [interpretation](docs/identifier-provenance-decision/INTERPRETATION_NOTES.md) |
| NGINX producer conformance | CLOSED — PRODUCER_CONTRACT_SUPPORTED | Eight archived requests had distinct native IDs; supplied caller IDs were not copied, and repetition did not repeat native IDs. No global/cryptographic uniqueness claim. [Record](experiments/nginx_producer_conformance/README.md) |
| OPA producer conformance | CLOSED — PRODUCER_CONTRACT_SUPPORTED | Eight stock exec evaluations had agreeing result/log IDs, no observed reuse or copying of submitted sentinels. SDK-supplied IDs remain a source-reviewed alternative; response/log are one evaluation, not independent execution proof. [Record](experiments/opa_producer_conformance/README.md) |
| Identifier-provenance necessity decision | CLOSED — CONTEXT_NEEDED_PRODUCTION_DEFERRED | Producer/observation semantics matter; no operation demonstrated that requires a new production representation beyond existing evidence plus explicit notes. [Decision](docs/identifier-provenance-decision/README.md) |
| M9b — source eligibility and declared-input diagnostic | CLOSED — NOT_DEMONSTRATED | Four prior source families do not substantiate real five-second coverage. Seven-case synthetic API diagnostic exposes reliance on declared support, not empirical coverage. [Record](experiments/m9b_coverage_substantiation/README.md) |
| M9b — bounded live acquisition | CLOSED — CLAIM_NOT_DEMONSTRATED | ACQUISITION_COMPLETED; coverage NOT_DEMONSTRATED. 185 files, >10-second hold and 12 successful samples do not establish continuous timing applicability or uninterrupted logging completeness. No live CONTROL_EFFECTIVE. [Milestone](milestones/m9b-coverage-substantiation/MILESTONE.md) |
| Coverage-evidence feasibility review | CLOSED REVIEW — NOT_DEMONSTRATED; next step approved | Ordinary source candidates identified, but no available applicable package substantiates both dimensions. Not evidence of universal unavailability. [Findings](milestones/coverage-evidence-feasibility/FINDINGS.md) |

## Current protected sequence

1. **Next: existing-evidence research/qualification — owner approved; acquisition pending.** Owner confirms only local same-operator M9b evidence is available. Compare ordinary enterprise source combinations and return the smallest real-source test first; no external deployment or live capture is requested. See the [expanded assessment](milestones/coverage-evidence-feasibility/SOURCE_QUALIFICATION_ADDENDUM.md). Freeze deployment-specific criteria before execution; approval does not establish source availability or accept unspecified assumptions. If no such source is obtainable, return for a claim-boundary/product decision. [Milestone record](milestones/existing-source-qualification/MILESTONE.md)
2. **Conditional M9b positive coverage demonstration:** only if feasibility identifies a credible existing source. Preregister a real bounded episode using it; retain the prior standard and negative results.
3. **Conditional M9a-ii:** only after the coverage prerequisite is demonstrated. Candidate OPA → runtime → AWS API → CloudTrail; naturally available adjacent-system links, qualified producer semantics, no universal end-to-end ID requirement.
4. **Conditional population assurance coverage:** only after action-level prerequisites. For a defined population/period, distinguish evaluability, effectiveness, exceptions and reasons for insufficiency. Assurance coverage and control performance are separate denominators.
5. **Conditional periodic control-level attestation:** a bounded report a control owner/risk/audit function can inspect and challenge. Recurring commercial-use-case hypothesis, not validated demand.

If existing evidence cannot address either M9b dimension, stop for an owner claim-boundary/product decision. Do not advance because a later milestone is convenient, relax the standard, or build telemetry to obtain a pass.

## Parked items and reopening conditions

| Item | Why parked / explicit reopening condition |
|---|---|
| Live delegated-authority assurance | M5 used explicit records, not evidence from mainstream runtimes. First inspect 3–4 real frameworks for authority-bearing handoff artifacts versus tasks using separately provisioned credentials. If absent, document the gap and remove the live claim from the active thesis until evidence changes. Not automatically in the sequence. |
| Neo4j / graph database Gate B | Gate A did not demonstrate incremental graph value. Reopen only for a real assurance/investigation query with material traversal value over a fair simpler representation. |
| Production identifier-provenance extension | Necessity unproven; new labels do not create evidence. Reopen for a named protected consumer operation, concrete failure of evidence-plus-notes, and substantiated applicable producer semantics. |
| Generic scope engine, DSL or policy language | No real evidence requirement establishes necessity. Transaction membership must not be promoted to authorization scope. |
| Cross-enterprise metrics/intelligence network | No demonstrated willingness to contribute anonymized metrics. Validate participation before implementation. |
| Full bitemporality | No demonstrated requirement; deferred indefinitely pending new evidence. |
| Broad observability, new telemetry, agent frameworks and other infrastructure | Outside the current proof and normally outside the product boundary. Existing ordinary evidence is preferred; any necessary new technology requires owner review. |

GTM validation remains parallel: AI Agent Assurance; recurring control-effectiveness attestation; secondary incident reconstruction; financial services preferred early vertical. Buyer value, existing-source availability, adoption friction, time-to-value, distribution, packaging, monetization and differentiation must be challenged at material milestones. No buyer validation is inferred from technical success.

## Evidence-driven roadmap changes

- M8 Gate A kept Neo4j off the critical path; graph-database value remains untested.
- Identifier withholding retained weak linkage as investigation-grade candidate leads under tested conditions, without validating investigation utility. Producer qualification narrowed the historical strong-link interpretation without changing FAILED or its metrics.
- NGINX + OPA review established context necessity, but deferred a production provenance extension; M9b remained the next proof.
- M9b source review and live acquisition failed to substantiate coverage. Owner instructions of 2026-09-14 now place **coverage-evidence feasibility before any further capture or M9a-ii**. Longer collection/probes cannot substitute for substantiated coverage. Population/period reporting stays conditional on action-level proof.

- Subsequent scoped feasibility review found useful prospective time/logging/audit sources but no substantiated combined arrangement. The current step is an owner decision gate; the recommended existing-source qualification is **not** silently promoted into the protected sequence. Prior M9b results and conditional later milestones are unchanged.

- Owner subsequently approved publication of the feasibility checkpoint and bounded existing-deployment evidence qualification. That step is now protected, with execution awaiting a named existing source; no coverage claim or trust standard changed.

- Owner clarified that no enterprise export/contact exists and directed continued source research, with acquisition pending. The ordinary-source assessment is expanded; a hypothetical combination does not qualify the local environment or change NOT_DEMONSTRATED.

## Maintenance rule

Update this file only for milestone evidence or an owner-approved decision that changes status, conclusion or sequence. Preserve historical negative results and explicitly record later narrowed interpretations. At close, update the milestone's `MILESTONE.md`, update this roadmap when warranted, include both in the checkpoint commit, and summarize the roadmap change in the owner briefing. Every milestone-specific `MILESTONE.md` links here. This is a decision record, not a feature backlog.
