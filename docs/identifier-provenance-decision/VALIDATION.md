# Decision milestone validation

Baseline: `1c555013e7140135075e9deebedcd1dc9da47dd7`. Frozen protocol: `62019d0`. This is an evidence/alternatives review, not a new producer experiment or a claim of improved automated findings.

- Existing `tests/test_correlation_assertion.py`: 10 passed in 0.44 seconds. This validates existing correlation behavior only; it does not validate the effectiveness of the notes or a hypothetical production extension.
- Reviewed actual raw retention, request-ID observation, native assertion declarations and downstream per-field namespace checks in the baseline code. No synthetic behavioral diagnostic was required.
- Both archived producer campaign verdicts remain `PRODUCER_CONTRACT_SUPPORTED`, with their original finite-sample limitations. The historical strong-link v4 report remains `FAILED`.
- Only additive Markdown under `docs/identifier-provenance-decision/` is intended. Baseline preservation is checked by comparing the complete tracked diff against the baseline; no baseline files may appear as modified, deleted, renamed or type-changed.
- All 40 relative document/source path references resolved to existing files. Source line references were inspected against the baseline source. Formatting validation passed and excludes no new files. The final staged comparison contains only the five added Markdown files in this decision folder; no baseline file changed.
- No new Docker/OPA/NGINX campaign and no full-suite rerun: production code and tests are unchanged. The baseline has green CI (549 Python tests passed, 5 skipped; OPA 6/6), recorded at https://github.com/datadownunda/agent-gov-graph/actions/runs/34870803756. This does not imply CI ran on the new decision commit.
- New checkpoint CI is not run before publication approval. The owner-approved OPA draft PR remains a separate checkpoint; this decision branch is based on its head. Any subsequent decision PR must state that dependency explicitly.

Negative result preserved: the necessity of a new production identifier-provenance representation has not been demonstrated. No claim is made that documenting unknowns resolves them or that current automated assurance is proven safe.
