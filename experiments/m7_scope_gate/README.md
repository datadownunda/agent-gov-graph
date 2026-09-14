# M7 v2 scope-gate conformance

This is a narrow production gate and a separate regression/conformance campaign.
It is not a new preregistered falsification result. Strong-link v1–v4 remain
unchanged, and the historical verdict remains **FAILED**. No M9b or generation
provenance re-analysis is included.

The accounting was saved before the production patch. `accounting.py` reads
frozen v4 inputs, truth, metrics and witnesses without running the experiment.
`accounting/v4-reconciliation.md` gives the complete link/merge/exception ledger;
the corresponding JSON retains exact evidence and assertion references.

The source-row equivalence count is 15, while complete-worker-input equivalence
is nine. Six namespace evaluations are distinguishable in observations supplied
to the worker but omitted by the old primary adapter. Three period evaluations
have a different timestamp without an applicable identifier lifetime rule.
A missing-declaration abstention must not be presented as selective discrimination.

The new worker receives the identical saved evidence object, never scorer truth.
It uses the frozen worker's unchanged M6 construction, preserves existing namespace
observations in the archive manifest, then obtains genuine v2 M7 receipts and
attestations. No issuer, scope envelope or retry declaration is manufactured for
the frozen cases. Tests with additional declarations are explicitly synthetic
conformance fixtures, separate from the frozen campaign.

Run into a new directory only:

```sh
python -B -m experiments.m7_scope_gate.run_conformance run experiments/m7_scope_gate/results/v1
python -B -m experiments.m7_scope_gate.run_conformance audit experiments/m7_scope_gate/results/v1
```

Each campaign preserves original input/truth bytes, raw outputs, unchanged-scorer
metrics, per-evaluation comparison, report, an implementation lock made before
execution, and an exact output inventory. Audit reproduces all 78 outputs.

Historical custody uses `historical_checkout()` to reconstruct exact git commit
`b8093786311fb2bd3a7c6ef45faefe5d64c69852` in a temporary directory. A pinned whole-checkout
inventory verifies all 4,516 original file hashes. Seven changed source files are
supplied by `tests/fixtures/m7_scope_gate/b809378-sources.json`, captured directly
from that git commit; other files must still match their original hashes. This
works in shallow CI checkouts without fetching history. Original frozen
baseline checks and the original worker then execute there. Nothing is removed
from their inventories, and current production files are not accepted as frozen
historical files. The existing `.save` fixture for the unrelated M9a-i historical
custody remains unchanged in that commit.

`tests/conftest.py` routes only tests asserting original strong-link baseline
behavior to that context. Current-code behavior has separate focused and saved
conformance tests. One existing M6/M7 test now explicitly requests its original
version-1 rule; the new suite tests default v2 behavior on the same old archive.

All producer-declaration checks remain conditional: compatible declarations are
not authenticated provenance and do not establish that producers enforced them.
