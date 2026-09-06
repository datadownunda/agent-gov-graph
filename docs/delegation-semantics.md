# M5: delegation semantics

M5 reconstructs direct and delegated authority for an explicit proposed actor,
action, resource type/ID, and historical timestamp using preserved evidence.
Every accepted path must independently establish the entire proposed tuple.
There is no grant merging, preferred path, role inheritance, OPA integration,
execution-identity reconciliation, or M6 behavior.

## Building on M4

M5 reuses M4's authority schema, preserved authority revisions, digest verifier,
explicit-time resolver, UTC/nanosecond comparisons, and half-open validity
intervals. M4 still decides whether direct/root authority is resolved, conflicting,
missing, or defective. Pinning a root record cannot bypass M4's conflicting
complete principal states.

The sole extension to the direct-authority schema is optional boolean
`delegation_permitted`. Absence means false. It is an all-or-nothing capability
for the scopes in **one complete authority state**, not a per-scope delegation
policy. Setting it does not enlarge resource scope, change roles, or alter M4
permission input. No existing registry records are changed to enable delegation.

M4 continues to treat equivalent direct authority records as compatible. M5
retains each effective supporting record as a direct basis. Equivalent states
that disagree about delegation capability cannot support a delegated path;
that capability conflict does not invalidate their direct resource scope.

## Record and query contracts

`schemas/delegation_registry.schema.json` defines an envelope with schema version,
source ID/version, an exact `authority_revision` reference, and raw `records`.
Each delegation is checked independently against the schema's `$defs.record`:

```json
{
  "delegation_id": "review-to-specialist",
  "delegation_version": "1",
  "delegator": "complaint-review-agent",
  "delegate": "specialist-agent",
  "parent": {
    "kind": "authority",
    "record_id": "complaint-review-agent-authority",
    "version": "2"
  },
  "delegated_scopes": [
    {
      "action": "read",
      "resource_type": "employee_complaint",
      "resource_ids": ["complaint-456"]
    }
  ],
  "valid_from": "2026-09-05T00:00:00Z",
  "valid_to": null,
  "onward_delegation": false
}
```

For another hop, `parent.kind` is `delegation`; its record ID/version must identify
an exact parent in the preserved collection. A record has exactly one parent.
No task step, graph edge, input order, or matching actor name substitutes for it.

The query contains `actor`, `action`, `resource_type`, `resource_id`, and
`effective_at`. All must be explicit and nonempty; the timestamp must be valid
and timezone-aware. Invalid query arguments are validation errors, not permission
denials. The CLI reports malformed input as `EVIDENCE_DEFECT`.

The envelope intentionally preserves raw malformed entries. Per-record defects
are reported rather than erasing an entire otherwise usable delegation
collection. An unassignable record appears in `evidence_issues` with its content
digest. An assignable malformed link is also a rejected actor candidate.

## Independent path validation

For the actor's direct authority and each incoming delegation candidate:

1. Resolve direct/root authority through M4 at the exact query timestamp.
2. Walk each delegation's exact parent reference, preserving the ordered chain.
3. Verify identity continuity: terminal delegate equals proposed actor, parent
   delegate equals child delegator, and root principal equals the first delegator.
4. Require an explicit root `delegation_permitted: true` capability.
5. Require every link/root to be effective at that timestamp.
6. Check every child scope is a subset of its one parent's scope. Comparison
   operates on complete `(action, resource_type, resource_id)` tuples.
7. Check the child's entire validity interval is contained in its parent's.
   Open-ended child validity exceeds a finite parent interval. No interval is
   clipped and no expanded record is repaired, even if the particular proposal
   happens to fit a legitimate subset.
8. Require each parent delegation used for a further hop to permit onward
   delegation. The terminal link need not permit another hop.
9. Detect repeated references and returns to an ancestor identity, including
   self-delegation. Traversal is iterative and bounded by visited records.
10. Only a fully valid path is eligible for a scope-membership decision.

Each accepted basis preserves `authority_kind` (`DIRECT` or `DELEGATED`),
`proposed_actor`, `root_principal`, terminal reference, ordered chain, effective
scopes, path status, and permission result. Delegator roles are not assigned to
the proposed actor. For rejected candidates the chain describes the attempted
ancestry, not a proven chain, and no usable effective scope is returned.

## Multiple bases and conflicts

All candidates remain visible. `valid_bases` contains **every** independently
valid path covering the full proposal. It is never a union of partial scopes.

- One full basis: overall `RESOLVED`, permission `PERMITTED`.
- Several full bases: `MULTIPLE_VALID_BASES`, permission `PERMITTED`. Direct and
  delegated bases can coexist. No preferred path is selected.
- Resolved paths all exclude the proposal, with no unresolved candidate defects:
  `RESOLVED`, permission `NOT_PERMITTED`.
- No full basis and broken/conflicting/defective candidates: permission remains
  `NOT_EVALUABLE`. Their issue codes remain explicit. Missing evidence cannot
  establish a negative permission conclusion.
- No direct authority or incoming delegation evidence: `INSUFFICIENT_EVIDENCE`,
  permission `NOT_EVALUABLE`.

A separate rejected path does not invalidate an independently valid full basis.
For example, an empty direct scope does not override a valid delegated basis,
and a broken delegation does not override a valid direct basis. Diagnostic
sorting is for stable serialization, not priority or preference.

Different delegation IDs may represent independent grants from different parents,
with different scopes, without conflicting. Exact duplicate records do not
manufacture additional bases. Equivalent overlapping versions also retain their
supporting references without a false conflict.

`DELEGATION_CONFLICT` means contradictory evidence: different contents for the
same delegation ID/version; overlapping versions of one logical delegation that
disagree about parties, parent, scope, or onward permission; unresolved M4 root
states; or disagreement about the root's delegation capability. A descendant
cannot bypass contradictory evidence by pinning one of the conflicting versions.
Only paths depending on that evidence are rejected. Different M4 complete direct
states remain an `AUTHORITY_CONFLICT`, as required by M4.

Path issues include `DELEGATION_CHAIN_BROKEN`, `DELEGATION_SCOPE_EXCEEDED`,
`DELEGATION_VALIDITY_EXCEEDED`, `ONWARD_DELEGATION_NOT_PERMITTED`,
`DELEGATION_NOT_PERMITTED`, `DELEGATION_EXPIRED`, `DELEGATION_NOT_YET_VALID`,
`DELEGATION_CONFLICT`, `DELEGATION_CYCLE`, `INSUFFICIENT_EVIDENCE`, and
`EVIDENCE_DEFECT`. Multiple issues are retained under `DELEGATION_REJECTED`.

Global failures are distinct from link-level rejection. A missing/tampered archive
or invalid envelope prevents verification of that assertion's evidence set.
Malformed authority collections retain M4's collection-level validation behavior;
M5 does not bypass it by extracting a convenient root record.

`PERMITTED` is explicit authority-scope membership, not an OPA ALLOW or proof
that execution is authorized. Existing role-based OPA policy may deny a tuple
inside the recorded scope. M5 never manufactures, alters, or enforces an OPA
result. `NOT_PERMITTED` is likewise separate from authority-evidence failure.

## Preserved evidence and reconstruction

Use M4's `preserve_revision` for the authority collection and
`preserve_delegation_revision` for the whole delegation collection. Both produce
content-addressed references containing filename, SHA-256, and source ID/version.
No private absolute paths are embedded. Existing archive bytes are never
overwritten. Parent references resolve only within this bound pair of revisions.

`create_assertion` loads both archives, verifies their digests/source metadata,
checks that the delegation collection binds the same authority revision, then
runs the resolver. The low-level `resolve_delegation` function accepts explicit
in-memory inputs for deterministic tests; it makes no archive-integrity claim.

`reconstruct_delegation` reloads and verifies both archives, repeats resolution,
and compares it with the saved assertion. Embedded chains/results are comparison
targets only. Missing archives yield `INSUFFICIENT_EVIDENCE`; altered archives or
invalid references yield `EVIDENCE_DEFECT`; changed assertion results yield
`CONTRADICTED`. There is no lookup of current authority/delegation registries.
An unchanged assertion yields `VERIFIED`, which verifies reconstruction agreement,
not permission: inspect its separate resolution and permission fields.

Revocation/expiry must be represented in the bound temporal records. New decisions
must use a new evidence pair reflecting an upstream change. Closed intervals or
missing exact parent versions invalidate unsupported downstream paths. Earlier
archives remain unchanged and reconstruct earlier decisions. No last-write-wins
or fallback to another version is permitted.

## Optional M4 governance context

A caller may supply an original M4 governance event. Its authority revision must
match the delegation evidence pair; the query's actor/action/resource must match
the event, and `effective_at` must equal OPA's native decision timestamp.

M5 first runs M4 reconstruction unchanged. It preserves
`authority_resolution_at` and `opa_decision_at` separately, and assesses M5 at
both times against the same evidence pair. A change in the valid basis set or
overall resolution/permission conclusion yields `TEMPORAL_BOUNDARY_AMBIGUITY`.
Changes to a rejected path's diagnostics alone cannot poison a stable valid
basis. M4's own temporal-boundary ambiguity remains authoritative and cannot be
bypassed. Both time-specific results remain available; the audit's permission
result is `NOT_EVALUABLE` on ambiguity. No state is silently preferred.

The assertion binds the original event's content digest. Replaying a bound
assertion requires the original event again; an embedded M4 result is not a
substitute. A standalone query is explicitly just a query at the supplied time,
not proof that a governance decision actually occurred then.

## Running the read-only experiment

A request JSON contains `query`, `authority_revision`, and `delegation_revision`.
The referenced archive files must already exist in the history directory.

```sh
python -m src.delegation_reconstruction assess request.json \
  --history-directory authority-history > assertion.json
python -m src.delegation_reconstruction reconstruct assertion.json \
  --history-directory authority-history
```

For M4-bound assessment/replay, supply `--governance-event event.json` to both
commands. This accepts one original event JSON object. Output is JSON on stdout;
the commands do not mutate registries or execute resources.

## Acceptance and regression coverage

Deterministic tests cover the required scenarios:

1. Existing direct authority, including absence of delegation capability.
2. Valid one-hop delegation with separate actor/root identities.
3. Valid two-hop narrowing.
4. Action expansion rejected.
5. Resource and resource-type expansion rejected.
6. Child validity expansion rejected.
7. Forbidden onward delegation rejected.
8. Expired/revoked upstream authority invalidates descendants.
9. Missing exact middle/root links rejected without inference.
10. Contradictory delegation records rejected locally.
11. Reference/identity cycles rejected.
12. No direct authority or delegation evidence is insufficient.
13. Current-registry mutation leaves historical reconstruction unchanged.
14. Missing/tampered authority or delegation archives fail explicitly.

Further tests cover multiple delegated bases, coexisting direct/delegated bases,
valid bases alongside defective/conflicting candidates, absence of scope merging,
equivalent versions, deterministic order/deduplication, timezone/nanosecond
boundaries, unchanged M4 direct behavior, original-event binding, temporal-boundary
ambiguity, and the read-only CLI. No new live model calls are required.

## Claim limits and exclusions

These are synthetic, cooperatively supplied authority/delegation records. Digests
establish content identity, not source authenticity, legitimate issuance, record
completeness, or a cryptographic credential. Rewriting both evidence and assertion
is outside this integrity check. An absent real-world revocation cannot be
inferred from a stale preserved revision. Source/version maintenance and archive
retention remain producer responsibilities.

Clock alignment and accurate valid-time records retain M4's limits. Two endpoint
checks are not continuous monitoring, and scope membership does not prove OPA
permission, actor role membership, or authority at execution time.

Existing trajectory `agent_delegation`, `allowed_delegations`, `parent_step_id`,
and graph `DELEGATED_TO` describe task handoffs. They do not establish M5 authority
and are not migrated into delegation grants. M1-M4 results and prior archives are
unchanged. No changes to complaint runtime, policies, correlation, graph/Neo4j,
execution identity, or model providers are included.

No per-scope delegation capability, delegation merging, group/role inheritance,
full bitemporality, cryptographic credentials, control-effectiveness attestation,
or governed-versus-executed actor reconciliation is implemented. This stops at M5.

## Implementation validation

Validation on 2026-09-05:

- Full Python suite with the virtual environment on PATH and
  `RUN_FOREIGN_OPA=1`: **241 passed**, including existing native OPA integrations.
- Focused delegation resolver/reconstruction and authority compatibility suite:
  **86 passed** (included in the full suite).
- Unchanged OPA 1.19.0 policy suite: **6/6 passed**.
- `git diff --check`: passed.
- All **136** prior experiment result files were byte-compared with the M4
  checkpoint and remained unchanged. The M4 seed archive digest still verifies.
- No live language-model calls, no delegated OPA enforcement, and no M6 changes.
