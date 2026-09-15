# Validation record

- Baseline GitHub CI: success, https://github.com/datadownunda/agent-gov-graph/actions/runs/34866681236.
- Initial environment run: 35 failed, 487 passed, 5 skipped. Docker socket access was denied; subprocess `python` was absent from PATH. These are retained as validation failures, not producer-campaign results. No production code was changed to suppress failures.
- Corrected full suite, existing virtual environment activated and Docker access enabled: 540 passed, 5 skipped in 179.73 seconds. Collection occurred before final test additions.
- Final experiment tests: 27 passed in 1.04 seconds, including incomplete/ambiguous native evidence, caller substitution, ID disagreement, repeated IDs, malformed IDs, input/result mismatch precedence, tamper detection and read-only replay.
- Existing OPA policy suite: PASS 6/6 under openpolicyagent/opa:1.19.0.
- Live producer campaign: one run, eight invocations, all checks true, no errors; PRODUCER_CONTRACT_SUPPORTED. Frozen runner and protocol were not edited after capture.
- Baseline preservation: all 5,683 tracked baseline files match the archived Git content. Production and historical results remain unchanged.

Exact local test summaries are retained in `validation/`. Raw live evidence and the manifest are in `results/v1/`; synthetic test fixtures are not producer evidence. GitHub CI for the final committed tree is recorded in the delivery briefing and pull request rather than assuming local success implies remote success.
