# Proposed existing-source qualification test — not executed

[Milestone](MILESTONE.md) · [Findings](FINDINGS.md) · [Roadmap](../../ROADMAP.md)

Select one already-operated Linux deployment with OPA and a defined target logging path. Do not provision a new environment or substitute AWS API outcomes for NGINX outcomes within M9b. An owner must identify the deployment/export and approve any consequential trust assumptions first.

Before execution, freeze: actual versions and clock domains; exact action/target/identity population; one historical interval containing an actual decision plus the unchanged five-second horizon; source manifest and source-native finalization semantics; quantitative clock-bound derivation and freshness/expiry rules; each required trust assumption. If any cannot be specified from existing records, stop at NOT_DEMONSTRATED before testing. This proposal is not a fabricated complete protocol for an unknown deployment.

Required export: native clock update/measurement history and effective configuration; OPA/target placement/lifecycle evidence; original target logs and all required rotation segments; mapped collector histories, loss/queue/retention indicators and configuration history. Source ownership and custody must be named. A journal is relevant only if the scoped evidence actually traverses it.

Assess the original export first. Prefer an already-recorded synchronization-loss or logging interruption within the selected scope; no live fault injection. Then use labelled scratch copies/views:

| Challenge | Required response |
|---|---|
| Remove a clock update or make its bound stale | Timing support expires or is explicitly insufficient; no interpolation beyond justified rate/disruption assumptions |
| Withhold OPA placement or clock-domain mapping | OPA timing applicability is insufficient even if the host clock is healthy |
| Omit PHC uncertainty where applicable | Refuse the understated bound; not applicable for non-PHC sources |
| Remove a required native/rotation segment, leave collector health intact | Completeness is insufficient; healthy collector status cannot replace the segment |
| Retain a real loss/restart/backlog indication without demonstrated recovery | Interval remains uncovered until ordinary evidence establishes recovery/finalization |
| Restrict target identity or location scope | Reject all-identity/whole-target coverage unless the fixed control explicitly permits that scope |

Each challenge must identify the affected dimension even if the original export already abstains. These modified views test review sensitivity, not real fault detection; only authentic retained incident evidence can support the latter. All originals remain untouched. Hash validity proves supplied-byte integrity only.

Stop conditions: no ordinary source for either dimension; circular use of the same transaction as independent confirmation; unbounded late arrival or clock uncertainty; unverifiable configuration/clock applicability; or an assumption that changes the protected claim. Return the precise gap to the owner. Success in this qualification would justify proposing a separate real positive-coverage test, not declaring CONTROL_EFFECTIVE or automatically starting M9a-ii.
