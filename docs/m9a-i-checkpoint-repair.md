# M9a-i checkpoint repair — pending review

**CLAIM_NOT_DEMONSTRATED remains unchanged. Nothing is committed or pushed.**

The repair is applied to current main
`6ebdcd598eebd52507c8646378b6b134386babbe`. Historical source baseline remains
`b585c548a3b68e6611c1f7545f63e7bcfd05d845`; protocol SHA-256 remains
`3c166973460fe8111d4aa7fec411f32989eb1dde8458cf60dcdaa69e36807224`.

All 14 original M9 files were copied byte-for-byte from the original clone into
this checkout. This includes the original test file, runner, matcher, protocol,
freeze inventory, report, validation record and every raw result. None was edited.
The preceding [baseline investigation](m9a-i-baseline-review.md) is retained as a
historical review record; this repair resolves its two test-context failures.

## Exact implementation and fixture additions

| File | Purpose |
|---|---|
| `experiments/identifier_withholding_verification.py` | Separate historical reconstruction/audit and current-checkout compatibility commands. |
| `tests/conftest.py` | Route only original historical-inventory tests to their pinned filesystem context; preserve their assertions and verifier. |
| `tests/test_identifier_withholding_verification.py` | Seven additional custody, tamper-rejection and compatibility cases. |
| `tests/fixtures/identifier_withholding_history/b585c54.tar.gz` | Exact 291-file Git snapshot of the frozen baseline, approximately 19.8 MiB compressed. |
| `tests/fixtures/identifier_withholding_history/test_runtime_reconciler.py.save` | Explicit historical untracked-file bytes bound by the original freeze. |
| `tests/fixtures/identifier_withholding_history/provenance.json` | Commit/tree, archive/save checksums and unchanged 14-file M9 inventory. |
| `tests/fixtures/identifier_withholding_history/README.md` | Fixture provenance, boundaries and reproduction commands. |

The [complete file inventory](m9a-i-checkpoint-repair/files.json) enumerates these,
the 14 unchanged M9 additions, the prior review material and new validation receipts.
No existing tracked current-main file is modified. No M6/M7 semantics, matcher,
scenarios, thresholds, scoring, protocol, original baseline or conclusion changed.

## Historical custody

Reconstruction uses a checked-in `git archive` snapshot of `b585c54`. It requires
neither network access nor a full Git history, so shallow CI checkouts can run it.
Before materializing files, the helper verifies the archive checksum, exact member
set and each file's SHA-256 against the unchanged original freeze inventory. It
rejects links, non-file entries and unsafe paths. It copies the 14 original M9
files only after checking their pre-repair hashes.

The original `.save` file genuinely appears in `freeze.json`. Its 2,271 exact
bytes are stored as an explicit fixture, verified against that same frozen hash,
and copied to its original path only inside the temporary historical context.
There is no fallback to a developer checkout. The active repository has no
incidental `tests/test_runtime_reconciler.py.save` file.

The original runner's whole-checkout verifier and audit then execute in a fresh
process rooted at the historical fixture. All 292 original inventory entries
remain mandatory. Tests confirm that changed baseline documentation, matcher code
or `.save` bytes still fail custody verification.

For the unchanged original test file, a narrowly scoped fixture redirects only
`ROOT`, `HERE` and `LIVE` for the two custody-dependent tests and the original
parameterized tamper tests. No digest function, inventory entry, assertion, gate
or verifier is replaced. Other tests remain in the current-main context.

Historical custody result: **VERIFIED**, 12 scenarios, claim not demonstrated.

## Current-main compatibility

The separate compatibility command checks the frozen protocol, freeze digest,
result manifest, execution-dependency hashes and preserved source artifacts. It
then runs the unchanged build, worker and scorer functions against current-main
sources. The four serialized files are byte-identical to the frozen experiment:
`decision-inputs.json`, `scorer-only-truth.json`, `decisions.json`, `results.json`.

This does not certify current main as the historical checkout. The original
blanket verifier still rejects current-main baseline differences, and an explicit
test requires that rejection. No differences have become hash exemptions or
ignored files. Original outputs are never overwritten.

The original result remains 25 correct and 22 false accepted links, 16 false
complete paths out of 19, and 39/39 assurance abstentions with no M6/M7 invocation.

## Validation

| Check | Result |
|---|---|
| Full M9 focused suite | **42 passed**, no skips: 35 original + 7 repair cases. |
| Full current-main regression | **429 passed**, no skips, 107.50 seconds; Docker integrations enabled. |
| OPA 1.19.0 policy tests | **6/6 passed** in Docker. |
| M6 audit | **VERIFIED**; original seven records and three authority reconstructions. |
| M7 replay | **VERIFIED**; all six saved assertions/receipts/content identities agree. |
| Historical M9 custody | **VERIFIED** in reconstructed `b585c54`. |
| Current-main M9 compatibility | All four serialized files **byte-identical**. |
| Schema validation | **17 schema definitions valid**, six saved M7 attestations valid. |
| Frozen M9 preservation | **14/14 files byte-identical**, including raw results and protocol. |
| Current-main preservation | **360 tracked files**, including **211 result/artifact files**, byte-identical. |
| Original clone preservation | **292 original inventory files** and all 14 M9 additions unchanged. |
| Whitespace | `git diff --check` and checks of untracked additions passed. |

Machine-readable receipts and JUnit results are in
[validation.json](m9a-i-checkpoint-repair/validation.json) and its sibling files.
The 429 total is 387 existing current-main tests + 35 frozen M9 tests + 7 repair
tests. Historical-context tests are explicitly distinguished from current-main
compatibility; no historical experiment is relabelled as newly run on main.

Reproduction, using the existing activated Python environment:

```sh
python -B -m experiments.identifier_withholding_verification historical
python -B -m experiments.identifier_withholding_verification compatibility
python -B -m pytest -q -p no:cacheprovider tests/test_identifier_withholding.py tests/test_identifier_withholding_verification.py
RUN_FOREIGN_OPA=1 python -B -m pytest -q -p no:cacheprovider
```

Git status at handoff: local `main` is at `6ebdcd5`, matching fetched `origin/main`;
all proposed changes are untracked additions, with no staged changes or modified
tracked files. The original stale clone remains untouched. Commit/push awaits
review. No M9a-ii work was added.
