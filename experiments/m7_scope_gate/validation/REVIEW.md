# M7 v2 scope-gate patch review

Implemented from main `b8093786311fb2bd3a7c6ef45faefe5d64c69852`. This review records the validated patch prepared for checkpoint. This task does not include M9b or generation-provenance re-analysis.

## Accounting saved before implementation

The complete ledger is in `../accounting/v4-reconciliation.md` and its JSON
companion. It ties all 21 false accepted identity links to 21 false merged
components and 18 false substantive exceptions, including exact assertion IDs,
evidence paths and scorer-truth coverage. All three truth-based scope-overreach
acceptances occur in `reuse/replacement` (012–014).

The previously stated 15 indistinguishable evaluations are identical at the
source-row boundary. Nine are identical at the complete worker-input boundary.
The remaining six contain namespace observations omitted by the old primary
M6/M7 path. Three additional false exceptions have differing timestamps without
a declared identifier lifetime rule. The three `copied/different` false links
already fail the target-effect resource check and cause no exception.

## Production behavior

Fresh attestations use `control-attestation/2`, schema `1.2`, with version-2
verification receipts. Minimal scope evidence remains in preserved source rows;
the existing receipt/attestation representation carries the computed path
assessments and exact evidence references. No separate scope-support schema was
created.

The new predicate is checked only at the substantive exception gate. It supports
single-action identity, literal bounded envelopes, and explicit retry bindings.
The positive `CONTROL_EFFECTIVE` gate is unchanged. M6 matching, candidate
populations and reconciliation are unchanged.

Envelope matching is literal, finite and bounded. No wildcard matching, action
classes, inferred groups, hierarchy, expressions or policy language is supported.
These predicates qualify already-supported M6 paths; they do not create links or
resolve existing M6 ambiguity. Synthetic predicate tests cover multiple envelope
members, and archived verification tests exercise all three scope forms.

Native-link qualification requires issuer/namespace declarations scoped to the
source records and identifier fields, with compatible declarations at both ends.
Generic caller namespace strings do not qualify a link. This is **declaration
checking only**, not independent authentication or proof of producer enforcement.
Missing declarations in the frozen cases are never manufactured.

## Separate conformance result

The campaign at `../results/v1` uses all 26 frozen base cases and all three
presentations. Input and scorer-truth files are byte-identical to strong-link v4.
The unchanged scorer is used, and M6 records, correlations, reconciliation and
verification results remain identical.

| Measure | Before | After |
|---|---:|---:|
| False substantive exceptions | 18 | 0 |
| False accepted identity links | 21 | 21 |
| False merges | 21 | 21 |
| Legitimate exception findings | 12 | 0 |
| CONTROL_EFFECTIVE findings | 78 | 78 |
| False CONTROL_EFFECTIVE findings | 0 | 0 |

All 18 previously false exceptions now abstain. Twelve legitimate exceptions
also become abstentions: 003–005 (`controls/deny_effect`), 042–044
(`retry/governed`), 051–053 (`fanout/governed`), and 069–071 (`parent/governed`).
Thus three legitimate-control evaluations and nine legitimate stress-case
evaluations lose findings. These are 12 newly missed legitimate exceptions via
abstention, not 12 findings that the effects were prevented.

The scope predicate was evaluated and passed as `SINGLE_ACTION` for every one of
the 30 pre-patch exception candidates. It was not skipped after an earlier
namespace failure. Namespace qualification caused all 30 new abstentions; scope
qualification independently prevented none. Holding namespace qualification
aside leaves all 30 scope checks passing; holding scope aside leaves all 30
namespace checks failing. All 30 lack required declarations, and three
(`namespace/pooled`, 021–023) additionally contain conflicting namespace
observations.

The conformance corpus demonstrates **no independent reduction in false
exceptions attributable to the scope gate**. Among the 18 false exceptions,
namespace-only rejection accounts for 18; scope-only, both-gate and neither-gate
rejection each account for zero. All 12 lost legitimate exceptions fail namespace
only. Scope acceptance is exercised, but scope rejection is demonstrated only by
focused synthetic tests, not by the frozen strong-link corpus. The corpus does
not exercise `BOUNDED_ENVELOPE` or `RETRY_OF` qualification; scenario names are not
scope declarations.

The 12 lost legitimate exceptions reflect legacy-fixture incompatibility with
the v2 namespace declaration requirement. The required declarations are absent
from the supplied archived records, so abstention follows the new evidence
contract. These fixtures predate that representation: their omissions establish
nothing about real enterprise evidence availability. Declaration compatibility
also does not establish independent authentication or actual producer enforcement.
Counts pool equivalent presentations, not independent trials.

Nine false evaluations (012–014, 033–035, 060–062) remain informationally
indistinguishable from legitimate controls. They are suppressed alongside their
legitimate counterparts; the patch has not resolved that ambiguity. Timestamp
reuse also remains unsupported by any newly declared lifetime or non-reuse rule.

This is conservative gating with a material loss of evaluability. It does not
demonstrate improved discrimination or repair the original falsification result.
The historical strong-link verdict remains **FAILED**.

## Preservation and validation receipts

`artifact-preservation.json` checks all 4,516 baseline tracked files: only the seven
approved source/test/documentation files differ; all 4,306 historical result files
are unchanged. Original protocols, raw results, matchers and scorers remain
unchanged. The M9a-i result and protocol digest are preserved.

Historical strong-link replay verified all 78 evaluations and reproduced FAILED.
The compact historical fixture contains exact original bytes for the seven changed
files; the pinned whole-checkout inventory verifies every reconstructed file.
Original baseline and implementation verification is not relaxed. Reconstruction
works without Git history or network access in shallow CI checkouts.

`replay-audits.json` records verified M6 audit, all six saved M7 attestations, M9
historical custody and byte-identical M9 current-main compatibility. The preserved
M9 `.save` fixture remains explicit and unchanged; no incidental developer file
is needed.

`opa.json` records Docker OPA 6/6 passing. `schemas.json` records all 18 production
schemas valid. All 381 saved v2 attestation objects validate. Focused and full-suite
logs and the independent 78-evaluation conformance replay receipt accompany this
review.

## Exact source/test changes

Modified:

- `src/control_attestation.py`
- `src/m6_attestation_evidence.py`
- `src/graph_value/canonical.py` — saved-rule selection for historical M7 replay only.
- `experiments/control_attestation/run_experiment.py`
- `docs/control-effectiveness-attestation.md`
- `tests/conftest.py`
- `tests/test_m6_attestation_evidence.py`

Full regression exposed two graph reference-reader failures because that reader
used the new default rule when replaying saved v1 M7 artifacts. Its one-line
saved-rule selection preserves M8 semantics; no graph query or frozen result
changes. The initial run had 518 passes and these two failures.

The last test explicitly selects its historical v1 rule; separate tests verify
fresh v2 abstention on the same legacy archive. Historical strong-link tests run
unchanged in the exact historical context, while current-v2 tests are separate.

Added:

- `schemas/control_attestation_v2.schema.json`
- `tests/test_m7_scope_gate.py`
- `tests/test_m7_scope_gate_conformance.py`
- `tests/fixtures/m7_scope_gate/evidence.json`
- `tests/fixtures/m7_scope_gate/b809378-sources.json`
- `experiments/m7_scope_gate/accounting.py`
- `experiments/m7_scope_gate/run_conformance.py`
- `experiments/m7_scope_gate/README.md`
- `experiments/m7_scope_gate/accounting/` — read-only reconciliation artifacts.
- `experiments/m7_scope_gate/results/v1/` — separate conformance campaign.
- `experiments/m7_scope_gate/validation/` — review and validation receipts.

Final validation: **520 passed, no skips**, including Docker/OPA integration;
OPA policy tests **6/6**; historical and current 78-evaluation replays **VERIFIED**;
18 production schemas valid; `git diff --check` passes. See
`final-validation.json` and `changed-files.json` for the exact receipts and file list.

Checkpoint rerun: **144 focused tests passed; 520 full regression tests passed,
no skips; Docker OPA 6/6 passed**. Both 78-evaluation replays verified again,
including the historical FAILED verdict. See `checkpoint-test-results.json`
and `checkpoint-replays.json` for the final pre-commit receipts.
