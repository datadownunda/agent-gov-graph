# M9a-i baseline investigation

The accepted result remains **CLAIM_NOT_DEMONSTRATED**. The raw result continues
to contain `claim_status: NOT_DEMONSTRATED` and `claim_demonstrated: false`.
No matcher, protocol, threshold, scenario, assurance gate, conclusion or original
result artifact was changed. Nothing was committed or pushed. M9a-ii was not begun.

Protocol SHA-256:
`3c166973460fe8111d4aa7fec411f32989eb1dde8458cf60dcdaa69e36807224`.

## Exact baseline and execution provenance

Both protocol freezing and result generation used the standalone local clone at
`/Users/jamesnanscawen/agent-gov-graph`, on local `main` at
`b585c548a3b68e6611c1f7545f63e7bcfd05d845`. This was not the clone used for the M8
checkpoint at `/Users/jamesnanscawen/Documents/ChatGPT/agent_gov_graph`.

The original clone's HEAD reflog last advanced on September 6 at 19:30:24 EDT,
to `b585c54`. Its local `origin/main` was also stale. The M9 task used that actual
checkout despite the supplied conversation describing newer main; it explicitly
recorded the discrepancy but did not update the checkout before freezing. Thus
`b585c54` is an accurate record of the experiment's baseline, not a typo to replace.

The task's launch directory was the ChatGPT project mirror, but its freeze and
execution commands explicitly ran in `/Users/jamesnanscawen/agent-gov-graph`.
The freeze script also used that absolute repository path. The recorded freeze
time is `2026-09-10T21:46:15.273094+00:00`. Its inventory contains 291 tracked
baseline files and the pre-existing untracked `tests/test_runtime_reconciler.py.save`.

Result generation used the same checkout plus the uncommitted M9 implementation.
The successful command was:

```sh
.venv/bin/python -B -m experiments.identifier_withholding.run_experiment run experiments/identifier_withholding/results/v1
```

An earlier invocation failed at import for missing `rfc8785`; it produced no
experiment decisions. The saved execution lock's modification time is
`2026-09-10T21:51:32.180685+00:00`, and `results.json` is
`2026-09-10T21:51:32.315993+00:00`. The lock binds the freeze digest, the two M9
implementation files and six reused source dependencies. All eight still match.
There is no committed M9 implementation SHA: its exact identity is the baseline
commit plus the frozen dependency hashes and preserved additions.

Local task history, the freeze inventory, reflog and artifact times corroborate
this chronology. They are not independently authenticated timestamps. See
[provenance receipt](m9a-i-baseline-review/provenance.json).

GitHub main was verified at `6ebdcd598eebd52507c8646378b6b134386babbe`. Its intervening
commits are M8 `8c514f99b4f2702e627153dcaed830d082b10152` and M7 hardening `6ebdcd5`.
Neither was present in the original M9 checkout.

## Compatibility with current main

The exact 14 M9 additions were copied without collisions into an isolated checkout
of `6ebdcd5` at `/private/tmp/m9-baseline-investigation-20260910/current-main`.
No existing current-main file was modified. Textual application is clean and the
frozen experiment's substantive behavior is compatible.

However, unchanged historical replay is intentionally checkout-specific.
`verify_frozen()` compares every entry in the old baseline inventory, including
documentation and tests. Current main has nine legitimately changed inventoried
files from M7 hardening, plus a new non-inventoried `src/evidence_errors.py`.
It also lacks the original untracked `.save` file. The first rejection is:

```
Preserved baseline changed: docs/control-effectiveness-attestation.md
```

Consequently, simply copying all additions is **not a green checkpoint**:
33 of the 35 unchanged M9 tests pass on current main; these two stop at the guard:

- `test_frozen_protocol_and_population`
- `test_process_truth_isolation_and_replay`

No guard, assertion or frozen inventory was relaxed to make them pass. The normal
historical M9 audit succeeds in the original checkout.

For a separately labelled compatibility check, an external driver first verified
the original result manifest, both protocol copies, freeze digest, all eight
execution dependencies, and all 169 old result/artifact hashes. It then called the
unchanged `build`, `run_worker` and `score` functions against current-main sources.
It did not call `run`, alter `verify_frozen`, monkeypatch the gate or overwrite
the original output directory. Copies of the four regenerated data files are
**byte-identical** to the originals:

- permitted decision inputs;
- scorer-only truth;
- decisions, candidate paths and assurance abstentions;
- all scenario metrics and the complete result.

The result remains 47 accepted links, 25 correct and 22 false; 19 complete
candidate paths, 16 false; and 39/39 assurance abstentions with no M6/M7 calls.
This is compatibility evidence, not a new preregistered experiment or revised score.
See the [compatibility receipt](m9a-i-baseline-review/compatibility/receipt.json).

## Effect of M7 hardening

| Boundary | Finding |
|---|---|
| Permitted correlation input | No change. M6 source bytes, identity mapping, target contract and ingestion dependencies match; regenerated allowlisted inputs are byte-identical. |
| Matcher and scorer input | No change. M2 correlator, M9 worker/evaluator, truth and decisions match their saved identities and outputs. |
| Assurance gate | No change. It remains closed for absent substantiated clock and population guarantees. Current-main boundary tests confirm no downstream invocation. |
| M6/M7 successful replay | Verified. All six original M7 assertions, receipts and content identities agree; original M6 audit results agree. |
| M7 failure behavior | Changed intentionally: unexpected processing failures produce a distinct `INTERNAL_ERROR` with null finding/coverage, or raise an internal-processing error if safe artifact construction fails. These are not evidentiary or control findings. No such processing failure occurred in this compatibility replay. |
| Historical M9 audit | Rejects current main's whole-checkout differences before matching. This is a custody-context mismatch, not a changed correlation result. |

Hardening therefore matters to operational error semantics and the old blanket
hash check, but does not affect this frozen experiment's permitted inputs, scoring,
closed assurance gate or observed result. It must not be reverted for M9.

## Regression-count reconciliation and new validation

Pytest collection, with the same Docker opt-in, gives this exact accounting:

| Scope | Tests |
|---|---:|
| Old `b585c54` baseline | 311 |
| M9 additions | 35 |
| Original reported full M9 suite | **346** |
| M8 tests absent from that baseline | 51 |
| Net M7-hardening tests absent from that baseline | 25 |
| Current main without M9 | **387** |
| Current main plus the unchanged M9 additions | **422** |

The 25-test net increase is +11 adjudication tests, +11 verification tests and
+3 M7 experiment tests. The difference between 346 and 387 is therefore 41:
the original run included 35 new M9 tests but omitted 76 current-main tests.
This is a source-tree difference, not a skip-count difference. The original
346-test run enabled `RUN_FOREIGN_OPA=1` and reported no skips.

Fresh validation on isolated current main:

- **387 passed, no skips**, Docker/OPA integrations enabled, 102.12 seconds.
  Command: `RUN_FOREIGN_OPA=1 python -B -m pytest -q -p no:cacheprovider
  --ignore=tests/test_identifier_withholding.py --tb=short`, with JUnit output.
- Unchanged M9 suite separately: **33 passed, 2 failed**, solely at the historical
  inventory guard described above. Across these two runs this is 420 passes and
  two custody-test failures; no combined green 422-test run is claimed.
- Normal Docker OPA policy tests: **6/6 passed**, using existing OPA 1.19.0.
- M6 audit and six-case M7 replay: **VERIFIED**.
- Current-main JSON Schema definitions: **17 valid**.

See [collection accounting](m9a-i-baseline-review/collection-comparison.json),
[current-main regression log](m9a-i-baseline-review/current-main-regression.log)
and [M9 test failures](m9a-i-baseline-review/current-m9-tests.xml).

## Preservation and checkpoint recommendation

All 14 original M9 files, including every raw result, retain their exact bytes.
All 292 old inventoried files, including the `.save` file, remain unchanged in
the original clone. All 360 current-main tracked files and all 211 tracked
result/artifact files remain unchanged in the compatibility checkout. M8 evidence
is included in this current-main check; it was absent from the original M9 run.
See [preservation receipt](m9a-i-baseline-review/preservation.json).

The baseline discrepancy is resolved. Before a checkpoint on current main:

1. Preserve `b585c54` as the historical source baseline in the protocol/freeze/raw
   results. Add this compatibility report as separate provenance; never relabel
   the original experiment as having run on `6ebdcd5`.
2. Apply only the 14 M9 additions and reviewed provenance material to a fresh
   branch from current main. Preserve M8 and M7 hardening. Do not merge or reset
   the stale clone over main, and do not add its unrelated `.save` file as an
   active source/test file.
3. Make a narrowly scoped test/reproduction-context change: run the two historical
   custody tests against an explicitly reconstructed `b585c54` fixture containing
   the exact frozen M9 additions. Preserve the hash-bound `.save` bytes as a named
   historical custody fixture and materialize them only there. Verify all hashes
   rather than editing the inventory or bypassing the guard. This integration
   change has not been implemented in this investigation.
4. Keep separate current-main compatibility tests for the unchanged decision and
   scoring functions, while running all normal current-main regressions. A
   historical fixture pass must not be described as current-main replay.
5. Require a green combined suite with that explicit context separation, repeat
   artifact/protocol preservation and whitespace checks, then review the exact
   staged additions before committing. Leave matcher, gate and frozen results
   untouched throughout.

Only this additive review and its receipts were written in the active workspace.
The original M9 clone and current-main product files were not edited. No commit,
push, history rewrite or M9a-ii work was performed.
