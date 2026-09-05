# Model-driven complaint experiment

## Execution status

The 20 scheduled API calls all failed with HTTP 429 before any model proposal
was returned. A separate diagnostic request identified `credit_balance_exhausted`
with error type `insufficient_quota`; see `provider-diagnostic.json`.

There were zero model proposals, zero governance evaluations, and zero execution
attempts. These are provider-unavailability outcomes, not invalid proposals or
unauthorized selections. No model-choice variability could be measured. This run
does not demonstrate the Milestone 3 claim. It preserves the failed attempts for
audit; a new run is needed after API credits are available.

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
