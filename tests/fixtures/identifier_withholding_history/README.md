# M9a-i historical custody fixture

This is the original experiment context, not current-main source or new evidence.

- `b585c54.tar.gz` was produced by `git archive --format=tar.gz
  b585c548a3b68e6611c1f7545f63e7bcfd05d845`. It contains all 291 tracked baseline
  files, with no `.git`, environment, cache or later milestone additions.
- `test_runtime_reconciler.py.save` contains the exact previously untracked bytes
  explicitly included in the original frozen inventory. Reconstruction places it
  at `tests/test_runtime_reconciler.py.save` only inside the temporary historical
  context. It is neither an active test nor a dependency on a developer checkout.
- `provenance.json` records the source commit/tree, archive checksum, `.save`
  checksum and the pre-repair hashes of all 14 frozen M9 files.

The separate verification module checks the archive checksum, exact member set,
every member against the unchanged freeze inventory, and the `.save` checksum.
It then copies the hash-checked original M9 additions into the temporary context.
The original `verify_frozen()` and audit execute there without any hash exceptions.
No Git history, network fetch or local `.save` fallback is used at test time.

From an activated Python environment at repository root:

```sh
python -B -m experiments.identifier_withholding_verification historical
python -B -m experiments.identifier_withholding_verification compatibility
```

The second command operates on current-checkout sources and reports only
compatibility. It never presents current-main files as the historical baseline.
The original runner's blanket inventory guard still rejects current main.

`tests/conftest.py` routes only the unchanged historical-inventory tests to the
temporary fixture, including the original tamper tests. It changes filesystem
context, not verifier behavior or assertions. Other M9 tests and the explicit
compatibility test execute on current main. The historical audit command also
uses a fresh subprocess so its imports come from the reconstructed baseline.
