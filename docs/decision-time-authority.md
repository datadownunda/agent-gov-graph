# M4: decision-time authority binding

M4 resolves temporally versioned authority records at an explicit time and
reconstructs that resolution from a preserved, digest-verified registry revision.
It is a deterministic complaint-domain experiment, not full bitemporality or
control-effectiveness attestation. No model calls are necessary for these tests.

## Decision path

1. A valid proposal supplies the action and resource unchanged (including M3's
   model-selected proposals). Invalid proposals remain rejected before governance.
2. Capture `authority_resolution_at` immediately before loading authority. This
   is **not** a claim about the exact OPA decision instant.
3. Validate the current registry, preserve its complete collection of temporal
   records in `authority_history/<sha256>.json` beside the governance log, and
   reload and verify those bytes. Existing artifacts are never overwritten.
4. Resolve the principal's records at `authority_resolution_at`. Missing,
   conflicting, or defective authority prevents OPA evaluation and execution.
5. Derive policy input from the resolved roles and the permission scope for the
   proposed action/resource type. Do not rewrite the action or resource. OPA
   remains responsible for permission ALLOW/DENY under the existing policy.
6. Preserve the native OPA record, including its `timestamp`. Resolve again
   against the same preserved registry at that timestamp, recorded separately as
   `opa_decision_at`. A change in applicable record versions, roles, permissions,
   or resolution status produces `TEMPORAL_BOUNDARY_AMBIGUITY`. Neither state is
   silently preferred, and execution is prevented even on the legacy bypass path.
7. An absent/malformed native timestamp or one earlier than resolution time
   produces `EVIDENCE_DEFECT` and prevents execution. No timestamp is invented.
8. Record authority evidence independently in `authority_resolution.jsonl`,
   the governance event's `context.authority_binding`, and M3's
   `AUTHORITY_RESOLUTION` lifecycle event. Governance event `timestamp` remains
   recording time. OPA's permission result is preserved even if dispatch is
   blocked by authority ambiguity. If authority fails before OPA, no fabricated
   governance decision is written and `policy_decision` is null.

The M3 runner returns `AUTHORITY_NOT_EVALUABLE` for unresolved authority, distinct
from `DENIED`, `INVALID_PROPOSAL`, and provider/runtime failures. An effective
record with empty permission scope is still resolved authority: a well-formed
unauthorized proposal reaches OPA and receives DENY.

## Temporal records

`schemas/authority_registry.schema.json` defines source ID/revision and records
with `authority_record_id`, `authority_version`, `principal`, `roles`,
`permitted_scopes` (action, resource type, resource IDs), `valid_from`, and
nullable `valid_to`. A record describes a **complete principal authority state**,
not an additive grant. No wildcard, delegation, precedence, or grant-union
semantics are introduced.

Intervals are half-open: `valid_from <= time < valid_to`; null means open-ended.
Dates must include a timezone. Comparisons preserve up to nine fractional digits
so OPA nanoseconds are not truncated at validity boundaries. Invalid dates,
nonpositive intervals, invalid record fields, and conflicting contents for the
same ID/version are defects. Validation covers the entire revision.

Resolution reports the rule version, principal, timestamp, applicable record
references, candidate records (effective, future, expired), normalized authority
basis, and one of:

- `RESOLVED`: one state, or equivalent overlapping states with all supporting
  references retained. Exact duplicate records are deduplicated.
- `CONFLICT`: overlapping complete states differ in roles or permissions. They
  are not combined or resolved by input order/version recency.
- `INSUFFICIENT_EVIDENCE`: no effective principal record. Expired/future records
  cannot supply authority. Absence alone is not proof of a policy denial.
- `EVIDENCE_DEFECT`: invalid or unverifiable evidence.

An explicit empty-scope successor record represents revoked permission while
retaining evaluable authority evidence. Closing an open-ended interval requires
a new record version and registry revision; preserve the earlier revision. This
experiment does not offer retroactive corrections or transaction-time queries.
Equivalent scopes are normalized as sets; a transition to a different supporting
record version remains a conservative boundary ambiguity even if its permissions
are identical.

## Historical reconstruction

Run the read-only audit with:

```sh
python -m src.authority_reconstruction PATH_TO_GOVERNANCE_JSONL \
  --history-directory PATH_TO_AUTHORITY_HISTORY
```

The audit verifies the exact archived bytes against the bound SHA-256 digest,
checks source metadata, reruns temporal resolution at both recorded times, and
compares the resulting record sets, candidate populations, basis, status, and
subject roles with the binding. It never consults the current registry or uses
an embedded basis as a substitute for archived records. `VERIFIED` means the
recorded authority binding agrees with reconstruction, not that the policy result
or source authenticity has been independently attested. A differing binding is
`CONTRADICTED`; missing archives/legacy bindings are `INSUFFICIENT_EVIDENCE`;
malformed/tampered evidence is `EVIDENCE_DEFECT`. A verified boundary ambiguity
remains `TEMPORAL_BOUNDARY_AMBIGUITY`, not a verified authorization.

Export governance logs together with their adjacent authority history. The
reference is a digest filename, not a private absolute machine path. Keep archive
retention at least as long as decision evidence. The current registry is never a
recovery fallback.

## Migration and scope

The synthetic registry migrates to schema/source version 2.0, preserving current
roles and read permissions. Its existing 2026-08-31 validity start remains a
**synthetic fixture assertion**, not evidence of an actual historical grant.
The seed revision is also checked into `runtime_resources/authority/history`.
Runtime decisions preserve their own referenced revisions beside their logs.

New runtime events require a binding. The governance schema still accepts legacy
events without it. Existing M1/M2 benchmarks and M3 live-v1/live-v3 evidence are
unchanged and are not retroactively assigned temporal bindings. Legacy replay
and synthetic runners that supply policy inputs directly do not demonstrate M4.
The resolver now requires explicit `effective_at` and `registry_revision`.

## Validation and claim limits

Deterministic tests cover effective/expired/future/missing authority, revocation,
equivalent and conflicting overlaps, malformed records/timestamps, offset and
nanosecond boundaries, changed current registries, missing/tampered archives,
contradictory bindings, scope isolation, and execution prevention on ambiguous
boundaries. M3 tests retain exact model-proposal propagation and distinguish
unauthorized valid proposals from invalid ones. Docker/OPA integration checks
exercise the native timestamp path without new live model calls.

The critical test creates a decision, mutates the current registry, and proves
reconstruction is unchanged; removing the preserved revision then makes
reconstruction explicitly insufficient despite the embedded event metadata.

This demonstrates consistency against the **supplied preserved revision**. The
registry and workload remain synthetic and cooperatively supplied. Hashes do not
authenticate the authority source, prove completeness, or prevent a party from
rewriting both archive and binding. No independent trust root is added.

The experiment assumes sufficiently aligned runtime/OPA clocks and a registry
revision that accurately describes the applicable authority. A revocation absent
from that revision, including a concurrent update while OPA runs, cannot be
inferred. Endpoint comparison is not continuous monitoring between timestamps.
No claim is made about authority at execution time, retroactive corrections,
clock uncertainty bounds, delegation, or control effectiveness.

Evidence of fallback to current state, accepted digest mismatch, arbitrary
conflict selection, execution across a detected boundary, or conflation of
missing authority with policy DENY would invalidate the implemented claim.
Evidence that the preserved revision omits a real effective revocation would
invalidate a stronger claim about actual enterprise authority; this experiment
cannot rule that out.

## Implementation validation

Final validation on 2026-09-05:

- Full Python suite, with the virtual environment on PATH and
  `RUN_FOREIGN_OPA=1`: **175 passed**, including real OPA native-timestamp
  reconstruction after current-registry mutation/removal.
- OPA 1.19.0 policy suite: **6/6 passed**.
- `git diff --check`: passed.
- No new live language-model calls. Prior benchmark and live-run artifacts were
  not changed. No correlation, delegation, database, or later-milestone work was
  introduced.
