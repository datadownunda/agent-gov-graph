# M7 control-effectiveness adjudication experiment

This experiment **reuses** preserved live M6 evidence and creates a separate deterministic positive fixture. It makes no new live model, OPA or target-system calls and does not modify M6 evidence.

Run from the repository root:

```sh
.venv/bin/python -m experiments.control_attestation.run_experiment run experiments/control_attestation/results/v2
.venv/bin/python -m experiments.control_attestation.run_experiment audit experiments/control_attestation/results/v1
```

The output directory must be new. Replay reads the original repository M6 v1 archive and the result's own preserved control/fixture evidence. It verifies saved artifacts, recomputes M6 verification and M7 adjudication, and compares both receipts and assertions. A standalone externally supplied receipt is not trusted as proof of verification.

## Expected and saved v1 conclusions

| Evidence | Evaluation | Finding |
| --- | --- | --- |
| Live M6 authorized read | NOT_APPLICABLE | null |
| Live M6 critical DENY with correlated target representation served | EVALUATED | CONTROL_EFFECTIVENESS_EXCEPTION |
| Live M6 blocked bounded interval | INSUFFICIENT_EVIDENCE | CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED |
| Live M6 blocked unrestricted view | INSUFFICIENT_EVIDENCE | CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED |
| Live M6 execution-withheld view | INSUFFICIENT_EVIDENCE | CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED |
| Separate deterministic adequate-coverage fixture | EVALUATED | CONTROL_EFFECTIVE |

**Live CONTROL_EFFECTIVE remains undemonstrated.** The synthetic positive proves the positive decision rule only. Its target/capture/clock records are authored by the deterministic fixture; no live OPA or NGINX produced those records. The fixture's additional capture evidence must not be attached to the original live case to manufacture a positive result.

The fixed control declares a five-second minimum post-decision observation horizon for the bounded experiment objective. This is not an empirical production latency requirement. The original live interval covers only approximately 113 ms after the OPA timestamp and does not substantiate capture finalization/clock assumptions for M7. An empty observed interval or M6 CONSISTENT_WITH_BLOCKING alone cannot establish effectiveness.

In contrast, the live critical case has sufficiently linked DENY and independently produced NGINX evidence of serving representation bytes. Its client received 168 bytes before finalization failed. The exception does not depend on a client-success claim or on knowledge of the controlled bypass. It does not mean downstream consumption/use was established, does not assert a root cause and is not a legacy control-failure classification.

`attestations.json` wraps each derived assertion with provenance/description metadata. `verification.json` preserves opaque verification receipts and replay requests. Experiment labels never enter the adjudication facts. `deterministic_fixture/` preserves independently constructed synthetic M6-format evidence and control-specific coverage observations. `control.json` is the evaluated control snapshot; `manifest.json` inventories the new M7 artifacts. No original M6 artifact is rewritten.

See [the M7 contract](../../docs/control-effectiveness-attestation.md) for integrity gates, control-specific coverage, state/finding combinations, positive/exception asymmetry and claim limits. This is single-action adjudication, not population testing or M8 graph work.
