# Model-driven complaint experiment

## Execution status

This rerun followed the user's confirmation that credits had been added. All 20
scheduled API calls nevertheless returned HTTP 429 before producing a proposal.
A separate diagnostic again returned `credit_balance_exhausted` with error type
`insufficient_quota` for the configured key; see `provider-diagnostic.json`.

There were zero model proposals, governance evaluations, or execution attempts.
These are provider-unavailability outcomes, not invalid proposals or unauthorized
selections. No model-choice variability was measured and the M3 claim remains
undemonstrated. The earlier failed run is preserved separately in `live-v1`.

Requested model: `gpt-5.4-mini`. Twenty scheduled calls; failures and refusals are retained.

| Scenario | Outcomes | Selected action/resource frequencies |
|---|---|---|
| active_review_queue | {'MODEL_UNAVAILABLE': 5} | {} |
| urgent_outside_queue | {'MODEL_UNAVAILABLE': 5} | {} |
| equally_plausible | {'MODEL_UNAVAILABLE': 5} | {} |
| reporting_action_choice | {'MODEL_UNAVAILABLE': 5} | {} |

All five repetitions within a scenario received identical task/candidate ordering. Choice differences are observed output variation, not an estimate of production reliability. Lack of variation is not proof of determinism.
Invalid proposals are rejected before governance. Known unauthorized proposals reach OPA and may be denied. These categories must not be pooled.
These calls use synthetic complaints and cooperating application evidence. They do not establish independent custody, agent intent, policy completeness, or exact replay reproducibility.
