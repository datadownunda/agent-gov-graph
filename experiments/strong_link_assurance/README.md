# Strong-Link Assurance Falsification

Fan-out/governed-action scope is the primary target. PROTOCOL.md and freeze.json
were written before implementation. No production file or schema is changed.
The baseline is the current commit containing preserved M9a-i, not M9a-i's
historical experiment baseline. All 410 baseline tracked files are hash-checked.

The primary worker uses existing M6 ingestion, native correlation, reconciliation,
M4 reconstruction and M7 verification/adjudication. It evaluates all five existing
M6 reporting views and saves every raw result. Metrics count the three governance
focuses, using the bounded blocked view instead of its unbounded duplicate. The
execution-withheld view remains a separately preserved coverage test. Duplicate
content IDs in auxiliary empty views may be rejected as non-unique by the existing
M7 verifier; those rejections are preserved, not repaired.

The corpus has 26 deterministic cases and three equivalent presentations each.
Sources are synthetically constructed in the existing complaint governance,
client execution and native NGINX JSON-lines formats. No new OPA/NGINX process
produces them; no new live or independent corroboration is claimed. Existing M4
seed evidence is kept in each synthetic archive and verified by the existing audit.

The decision worker receives only unlabelled source rows and namespace observations.
Scorer-only event histories, labels and expected findings never enter the worker.
Separate source-local serialization locations are used by the scorer to address
outputs; they are not matching features. The worker is a separate process; this
is protection against accidental information flow, not an adversarial sandbox.

The diagnostic sidecar runs only after all primary outputs. Namespace probes use
existing required-equality invariants without filtering candidate populations.
Parent-context probes deliberately test TRANSACTION_MEMBERSHIP with the existing
M6 traverser; they cannot be replayed by the fixed native M7 archive adapter and
are labelled unsupported downstream evaluations. They never receive invented
verification receipts. No new production assurance gates exist.

Scope has two distinct measures: actual event-history coverage correctness, and
whether the available evidence establishes coverage. The initial corpus contains
no independently substantiated execution-specific cardinality/descendant binding;
the diagnostic cannot accept scope merely from a tuple and identifier. M7's actual
substantive reliance is preserved even when that diagnostic abstains. A correctly
associated execution can be truly covered in scorer history while coverage is
not established by the available evidence. Both are reported; missing evidence
is not relabelled as proof of unauthorized behavior.

The frozen copied-ID pair has identical decision inputs/outputs but different
scorer histories. A false exception means its cited prohibited target observation
belongs to a different action, even if an unobserved original effect might also
have occurred. Digests do not authenticate source honesty or uniqueness.

Run into a new directory (existing outputs are never overwritten):

```sh
python -B -m experiments.strong_link_assurance.run_experiment run experiments/strong_link_assurance/results/v1
python -B -m experiments.strong_link_assurance.run_experiment audit experiments/strong_link_assurance/results/v1
python -B -m pytest -p no:cacheprovider tests/test_strong_link_assurance.py tests/test_strong_link_assurance_boundaries.py -q
```


The execution lock captures implementation bytes before the first campaign worker.
Audit verifies frozen baseline/dependencies, regenerates all inputs/truth, replays
every worker, validates the local sidecar schema, and reproduces scores/report.
Protocol and implementation are not retuned after results. Raw outputs, including
failures, remain under the original run directory. Validation receipts are kept
outside the frozen run inventory, not appended into its immutable evidence.

Pre-campaign development check: the initial new suite had 38 passes and one failure
because it incorrectly required every auxiliary empty-view receipt to be VERIFIED.
The test was corrected to require the selected control view's genuine verification;
no production verifier or protocol gate was changed. This was not a campaign run.
