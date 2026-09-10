# M9a-i preregistered protocol v1

Question: Can Agent Gov Graph support a defensible downstream assurance conclusion
when the cooperative native identifiers used in M6 are unavailable?

## Inspection and scope
Baseline is the actual local checkout recorded in freeze.json, not the conversation's
reported commit. Reuse M6 v1 governance/execution/native NGINX evidence, target contract,
and explicit operator identity mapping. Reuse M2 src.evidence_correlation.correlate.
M6 replays full candidate populations before deriving claims. Its existing composite
adapter expects string actors whereas M6 has namespaced actors. M7 verifies the native
M6 archive and projects allowlisted facts; do not bypass this verifier or fabricate
receipts to force an identifier-free result. No changes to existing M1-M8 paths.
M2 already documents false unique links under skew and replacement; this is a
preregistered stress replication on M6-derived observations, not an unseen benchmark.

## Inputs and transformation
Separate an evaluator process from a decision worker. The evaluator may use original
native IDs solely to reconstruct scoring truth and select the two original complete
triples; it does not transmit IDs, labels, truth, source locations, raw payloads,
content-derived references, sequence numbers, policy decisions, or outcomes to the
worker. The worker receives an unlabelled list of cases, each with exactly governance,
execution, outcome arrays. Each record has exactly evidence_ref, actor, action,
resource_id, resource_type, observed_at. References are opaque seeded source-local
addresses, disjoint across all observations, never matching features. Shuffle each
population deterministically. Seed: 90101. Actor is canonical JSON of namespace/id;
apply only the existing explicit identity_mapping.json before projection. This is
an operator assumption and an intentional favorable condition, not identity proof.
Unknown identities retain their namespace; no inferred equivalence.

Keep the unmodified seven-record M6 population as preserved_population, only projecting
and withholding fields. Stress cases reuse the two complete native-linked triples.
For stress construction set each governance time to 2026-09-06T00:00:00Z plus repetition
offset, preserve each original execution/outcome time delta from its governance time
at nanosecond precision. These are synthetic transformations of existing evidence,
not new independently produced observations. Keep ordinary actor/action/resource
values. No new native evidence, telemetry, dependencies, or foreign formats.

Fixed cases (both original complete triples in every stress case):
- isolated: one copy, zero skew, all records.
- repetition: two copies separated by 0.1 seconds, all records.
- clock_skew_execution: three copies separated by 5 seconds; execution +5 seconds.
- clock_skew_outcome: three copies separated by 5 seconds; outcome +5 seconds.
- clock_skew_outcome_negative: same, outcome -5 seconds.
- impostor_execution: isolated, replace each execution with a different latent event
  with identical permitted observations and a fresh source-local address.
- impostor_outcome: same replacement on outcome.
- missing_execution: isolated, remove both execution counterparts.
- missing_outcome: isolated, remove both outcome counterparts.
- ambiguous_execution: isolated, add one identical-observation execution impostor
  beside each intact original.
- ambiguous_outcome: isolated, add one outcome impostor beside each intact original.
Together with preserved_population this is exactly 12 cases. No adaptive cases.

## Frozen matcher and downstream gate
Run unchanged M2 exact actor/action/resource_id/resource_type equality and inclusive
absolute one-second time window, mutually unique in both directions. Compare G-E and
E-O independently over their full supplied role populations. No G-O shortcut, nearest
neighbor, confidence scores, fitted offsets, or post-result feature/threshold tuning.
MATCHED means a conditional candidate only; AMBIGUOUS, UNMATCHED and EVIDENCE_DEFECT
always abstain. Report pair states and complete candidate sets.

A downstream assurance path requires both mutually unique edges, plus independently
substantiated population coverage/non-replacement and cross-source clock/latency
bounds applicable to that path. Neither the M6 native-ID archive nor synthetic
construction labels substantiate those guarantees for this experiment. Thus no
candidate in this fixed evidence set is assurance eligible: emit an M9 ABSTAIN with
finding=null and do not invoke M6 reconcile or M7 attest/adjudicate. This is an
explicit closed gate, not a newly implemented general-purpose evidence verifier.
There is no caller-provided boolean or scorer override to open it. Keep original
M6/M7 audits separate; their native-ID findings are preservation checks only.
Even perfect stress precision cannot substitute for missing evidence assumptions.

## Scoring and preregistered claim criteria
Score after the decision worker exits. Write scorer truth only after worker exit.
Compute per-case, per-edge and pooled counts (pooled values are stress diagnostics,
not production estimates). Count each accepted edge once:
precision = correct accepted / accepted; recall = correct accepted / planned true
pairs including removed originals; observable recall = correct / true pairs whose
original endpoints remain; false-link rate = false accepted / accepted.
Correlation abstention = non-MATCHED source observations / all observations for that
edge. Pooled rates weight these denominators; an execution appears on both edges.
Also count complete proposed G-E-O paths and false complete paths, plus assurance
abstention = blocked governance focuses / governance focuses. Zero denominators are
null, never perfect precision. Preserve numerator and denominator counts.

Necessary candidate-quality screen: zero false links in every case and every complete
path, and isolated recall exactly 1 on both edges. Failure falsifies treating this
candidate rule as assurance-grade. Overall claim demonstration additionally requires
at least one eligible DENY path yielding a genuine verified M7 adjudication, with no
wrong supported conclusions. All-abstain is safe but does not demonstrate the claim.
Given the known evidence gap, report NOT_DEMONSTRATED rather than claiming success
from abstention. Distinguish candidate-quality failure from absent gate evidence.
Stop after the frozen run and required validation. No repairs to heuristics based on
results, no M9a-ii, and no claim that every possible correlation method is falsified.

## Verification and custody
freeze.json records the SHA-256 of these exact protocol bytes, UTC freeze time, HEAD,
and a SHA-256 inventory of all pre-existing tracked files and the known untracked
save file. Freeze before implementation or any experiment execution. Pin the digest
in code and reject changed protocol/source inputs. Before first execution, save an
implementation/input dependency digest inventory into the result manifest. Fresh
output directories only. Preserve decision-inputs, decisions, scorer-only truth,
metrics, protocol copy, implementation digests and result inventory. Audit regenerates
all cases and replays decisions and scoring; digest agreement does not authenticate
provenance. Do not put source paths or scenario names in worker input.

Tests: exact allowlists at worker boundary (including nested/value type checks),
prohibited identifiers/labels/raw payload poisoning, reference renaming and order
invariance, worker/scorer separation, no downstream calls on blocked paths, metric
zero denominators and loss denominators, fixed-window boundaries, result/source/
protocol tamper rejection, deterministic replay. Run focused and full regression,
OPA policy tests, original M6 audit/M7 replay, all original schema checks, full
baseline byte inventory preservation, and git diff --check. Do not overwrite results.

Limitations: small controlled corpus, synthetic repetition/skew/impostors, cooperative
operator identity mapping, no empirical enterprise rates, no authentication proof,
no clock/completeness attestation and no independent new evidence collection. Process
separation is an accidental-leakage boundary, not a hostile-code security sandbox.
