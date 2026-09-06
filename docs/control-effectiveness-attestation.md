# M7: bounded single-action control-effectiveness attestation

M7 derives an attestation from a verified M6 reconciliation. It does not add correlation, reconciliation, policy enforcement, root-cause analysis or graph behavior. All M1–M6 implementation and preserved evidence remain unchanged.

## What is demonstrated

The deterministic positive fixture demonstrates the **positive decision rule**. It is newly authored synthetic evidence: no live OPA or NGINX process produced it.

Preserved live M6 evidence demonstrates the **exception and abstention paths**. **Live CONTROL_EFFECTIVE has not been demonstrated.** The existing blocked coverage interval ends approximately 113 ms after the OPA timestamp and lacks substantiated capture/clock assurances for the M7 bounded objective. It is not upgraded into adequate observation evidence.

NGINX was an independent producing process in the live experiment, within a synthetic, operator-controlled deployment. REPRESENTATION_SERVED means that the configured static target reports serving representation bytes at its observation boundary. It does not establish downstream client consumption, interpretation or use. The critical client received 168 bytes before finalization failed; null client success is not absence of receipt.

## Fixed control contract

`experiments/control_attestation/control.json` specifies the sole supported type:

```text
DENY_PREVENTS_TARGET_EFFECT
  governance condition: DENY
  prohibited effect: REPRESENTATION_SERVED
  target: complaints-static-v1, with pinned target-contract digest
  scope: read / employee_complaint
  observation boundary: target-reported representation serving
  minimum post-decision observation horizon: 5 seconds
```

The five-second horizon is an explicit bounded **experiment control requirement**, not an empirical estimate of target latency, a production recommendation, or a universal safe timeout. Positive attestations retain the actual observation interval. Effects after that interval are outside the positive conclusion. Merely shortening this requirement cannot make the live case adequate: it still lacks affirmative capture and clock support.

A sufficiently linked observed violation can establish an exception without complete negative observation coverage. No execution success field is required. Execution evidence that supports a G–E–O path cannot, however, be withheld while retaining that path: the preserved execution-withheld view remains insufficient.

The control-definition schema is strict and supports no expressions, generic policy language, multiple controls or population scope. Each attestation applies to one governance focus and one M6 assertion.

## Verification boundary

The flow is:

1. Preserved M6 reconciliation and archive.
2. Integrity/replay verification plus a control-specific coverage assessment.
3. Allowlisted adjudication facts with opaque content references.
4. Fixed DENY_PREVENTS_TARGET_EFFECT rule.
5. New M7 attestation and verification receipt.

`src/m6_attestation_evidence.py` supports the existing complaint M6 archive format. It verifies archive member digests, invokes the unchanged M6 audit and replay, selects the exact assertion by content ID, checks that it replays, and verifies the pinned static-target configuration/contract. The M6 audit re-ingests source bytes, validates original locations, replays existing correlations and reconstructs preserved M4 authority. There is no current-state authority lookup or fallback to an event snapshot.

This first verification adapter is deliberately **archive-format-specific**. It is not a general verifier for arbitrary M6 producers or arbitrary historical delegation archives. Unknown/unreplayable assertions fail explicitly; they are not reconstructed through a new matching path. Historical explanations remain M6's responsibility; M7 does not need to resolve a new delegation to interpret this control, and delegation cannot override DENY.

The adjudicator receives only a fixed set of facts: governance identity/tuple/decision/time; M6 result and relevant uncertainty; whether a linked target effect satisfies the pinned semantics; support references; and a control-specific coverage assessment. It never receives raw records, scenario names, filenames, run IDs, bypass/failure-injection flags or ground-truth labels. The unchanged archive adapter still uses its existing M6 experiment layout internally for replay. Presentation labels stay outside the adjudicator and outside the attestation.

The original archive's manifest can cover ground-truth content for inventory integrity. Changing its labels and updating that inventory does not change adjudication, because no ground-truth value is a decision input. Hash references may change when inputs change; conclusions do not follow those labels.

`attest()` is the evidence-backed entry point. `adjudicate()` is a pure function for locally produced verification receipts and deterministic unit tests. A receipt digest is **not a signature**: an externally supplied receipt cannot authenticate itself. `reconstruct_attestation()` re-verifies the source archive and recomputes the receipt and finding instead of trusting a saved receipt.

## Control-specific coverage

There is no generic completeness flag. Each assessment has `ADEQUATE`, `INADEQUATE` or `UNKNOWN`, structured basis codes, control digest, original coverage digest, observation interval and optional support digest.

ADEQUATE requires all of the following for this control:

* Original M6 coverage applies to the exact governed tuple and contains the declared post-decision horizon.
* Affirmative preserved observation support binds to the control, reconciliation, target contract and exact action/resource scope.
* Observation covers all target identities for that resource/action; a different executing identity cannot be filtered out to obtain a positive finding.
* Target capture was available across the interval including the declared clock uncertainty, and was finalized through its end.
* The capture record identifies the native log snapshot being assessed.
* Clock bounds are supplied with a basis, and unresolved capture gaps/candidate ambiguity are absent.
* M6 itself supports blocking-compatible observations without an undermining contradiction or uncertainty.

The optional `coverage_observations.json` is affirmative control-specific evidence, not a request to declare adequate. Its scope, bounds, finalization, clock bounds and snapshot binding are checked independently. Malformed or incomplete support cannot yield adequate coverage. The positive fixture authors these observations under a deterministic clock; this demonstrates semantics only. Real use would require substantiated observations from the actual capture boundary. Digests cannot turn an operator declaration into independently authenticated assurance.

M6's original CAPTURED states remain unchanged. In particular, M7 does not infer adequate coverage from an empty log, a CONSISTENT result, or the CONSISTENT_WITH_BLOCKING issue code alone.

## Findings and precedence

| Condition | Evaluation status | Finding |
| --- | --- | --- |
| Invalid control, integrity defect, replay disagreement | NOT_EVALUABLE | null |
| Required archive evidence unavailable | INSUFFICIENT_EVIDENCE | CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED |
| ALLOW or control scope not applicable | NOT_APPLICABLE | null |
| DENY, verified semantics, sufficient correlation, observed prohibited effect | EVALUATED | CONTROL_EFFECTIVENESS_EXCEPTION |
| Required correlation ambiguous/contradicted/insufficient | INSUFFICIENT_EVIDENCE | CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED |
| DENY, adequate affirmative bounded coverage, blocking-compatible observations and no undermining uncertainty | EVALUATED | CONTROL_EFFECTIVE |
| Remaining incomplete gates | INSUFFICIENT_EVIDENCE | CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED |

Integrity and applicability precede interpretation. A sufficiently established prohibited effect does not require complete negative coverage. A positive effectiveness finding does. Missing runtime success does not negate a target observation; actor divergence or submitted execution alone does not establish a target-effect exception. UNEXPLAINED_DIVERGENCE and CONTRADICTION are not mechanically translated into findings.

An empty, adequately observed target interval has no positive target-event link to demand. This differs from ambiguous candidate target evidence, which requires abstention. The fixture demonstrates the former; the live withheld view demonstrates the latter linkage gap.

## Saved assertions and compatibility

Every attestation has its control/content identity, exact M6 assertion reference, verification receipt reference, single-action scope, target, observation interval where available, evidence/correlation references, coverage assessment, evaluation status, finding, structured basis codes, limitations and rule version. Schemas enforce valid state/finding combinations; content identities are recomputed during replay.

Saved results keep `PRESERVED_LIVE_M6` and `DETERMINISTIC_FIXTURE` provenance outside decision inputs. Audit rejects attempts to relabel the fixture archive as live evidence. The original M6 artifact files are neither edited nor copied into a purported improved live run. The fixture has its own newly constructed authority/governance records, empty target observations and explicit synthetic capture observations.

No legacy FAILED, ENFORCEMENT_FAILURE or NO_EFFECT_OBSERVED labels are imported into this rule. Missing target evidence never becomes proof of no effect. No new enforcement, authority/delegation semantics, root cause, workflows, remediation, population effectiveness or M8 graph work is added.

## Falsification boundaries

The claim fails if a finding depends on experimental labels; an unverified or rehashed forged reconciliation is accepted; target effects come from runtime claims; required linkage is bypassed; incomplete or mis-scoped capture yields effectiveness; changed current authority replaces preserved evidence; or a synthetic positive is represented as live empirical effectiveness.

The implementation remains conditional on the authenticity of supplied source/capture evidence and the declared issuer namespaces. The manifest and verification receipt prove deterministic agreement with supplied content, not adversarial provenance authenticity. Native IDs may be copied/reused, observations may be incomplete, clocks may violate their bounds and capture assurances may be false. Those are explicit limitations, not population-wide guarantees.
