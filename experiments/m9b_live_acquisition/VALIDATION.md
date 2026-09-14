# Validation record

- Protocol commit: bf4c78c; implementation freeze: 851026e66dccde4383d36dcb4e17f9859368817e. The tree was clean before the single capture.
- Pre-capture focused checks: 25 passed (23 acquisition tests, 2 CI-history tests). Independent implementation review found the revised runner ready for bounded capture.
- Exactly one live acquisition ran. Result: ACQUISITION_COMPLETED; coverage NOT_DEMONSTRATED. No recorded acquisition failures, no forced cleanup, no retry.
- Read-only replay with `python -B -m experiments.m9b_live_acquisition.run_acquisition verify experiments/m9b_live_acquisition/results/v1` matched the original result byte-for-byte. Requires original filesystem paths as documented in README.
- Independent review checked all 185 archive hashes, actual OPA/governance identity, native probe linkage and lifecycle ordering. Both kernel diagnostics reported UNSYNC. No contradictory evidence found.
- All 5,891 files in baseline 1ee92c58a6bee4a86379bcd7ea4473136aba9fe5 remain unchanged. Frozen protocol, runner and tests still match the pre-capture execution lock. Formatting check passed.
- Initial full local test attempt: 35 failed, 551 passed, 5 skipped. Existing integration tests lacked Docker access and some subprocesses could not resolve `python`. Preserved in [initial-local-tests.txt](validation/initial-local-tests.txt). The environment was corrected without changing code or evidence, and regression tests rerun; this is not a live acquisition retry.
- Corrected full local regression suite: **586 passed, 5 skipped** in 168.78 seconds; [record](validation/corrected-local-tests.txt). No implementation changes were needed.
- OPA policy tests: 6/6 passed; [record](validation/opa-tests.txt).
- Prior source-gate PR #3: CI run 34874589967 failed four shallow-history harness tests; additive exact-history fix at 0dbb548946e24b2e0d0e42c40eb2c6edaacb6974 passed CI run 34875498016 (563 passed, 5 skipped; OPA 6/6). Both runs retained and PR updated. The live branch includes the same fix as e513615.
- Live checkpoint CI: not run; new public findings await the owner review required by the standing milestone instructions. Earlier PR CI does not validate this later checkpoint.
