# M9b validation

- Baseline: `6f765ebe6f5452d8b9ee85bd609771b301bd503f`.
- Preregistration: `67d45d6`; implementation/source-review freeze: `f954d28d3037e87f12e17c2d2896246925fc328f`. Working tree was clean before the first real public-API diagnostic invocation. Harness tests before freeze mocked attest; they were not the campaign.
- Existing attestation tests before campaign: 46 passed in 12.78 seconds. Harness tests: 12 passed in 1.52 seconds.
- Final targeted suite: **58 passed in 12.41 seconds** across `test_m9b_coverage_substantiation.py`, `test_m6_attestation_evidence.py` and `test_control_attestation.py`.
- One seven-case campaign completed with no operational error; all cases are explicitly synthetic. The five required negative cases prevented CONTROL_EFFECTIVE. Baseline and unmeasured-clock-basis cases were accepted as conditional semantic positives. Neither substantiates empirical coverage.
- Fresh-copy audit: **VERIFIED**, seven cases, full request/archive/output comparison. No native producers were run. Archived raw bytes and the frozen implementation were not edited after capture.
- The execution lock checks baseline tracked-file preservation and hashes protocol, runner, tests, control, source code, schemas, M6 replay code and the complete original synthetic archive. Audit checks that the freeze commit remains an ancestor and dependency hashes agree.
- Relative artifact links are validated and the complete baseline diff is restricted to additive M9b experiment files and its test. Formatting checks preserve any pre-existing whitespace inside copied historical evidence; native/source bytes are never reformatted to satisfy a style check.
- Full CI has not run on this unpublished checkpoint. Baseline CI was green at https://github.com/datadownunda/agent-gov-graph/actions/runs/34872553466; that does not imply new checkpoint CI success. Publishing the new conclusion requires owner review. The branch builds on unmerged PR #2, which builds on PR #1.

Test summaries and replay result are retained in `validation/`. The source-gate decision is **NOT_DEMONSTRATED**, independently of diagnostic completion. No live CONTROL_EFFECTIVE result, enterprise authenticity, continuous collection, or clock measurement is claimed.
