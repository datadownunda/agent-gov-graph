# Milestone 3: single model-selected complaint proposal

## Implementation and claim status

This experiment places a single model call before the existing complaint
governance path. The [third live run](../experiments/model_agent/results/live-v3/README.md)
attempted 20 calls and obtained 17 valid model proposals: 12 ALLOW/executed and
5 unauthorized selections DENY/blocked. Three calls failed with HTTP 429.
The audited successful trials demonstrate the controlled model-selection and
governance path. Stubbed provider tests are not evidence of live model choice.

The first [live run](../experiments/model_agent/results/live-v1/README.md) attempted
all 20 scheduled calls, but the provider rejected them with HTTP 429. A separate
diagnostic reported `credit_balance_exhausted` / `insufficient_quota`. No model
proposals were obtained in that run. These failures are not policy denials or
invalid proposals.

A subsequent [rerun](../experiments/model_agent/results/live-v2/README.md), after
credits were reported added, also received HTTP 429 on all 20 calls. Its separate
diagnostic again reported `credit_balance_exhausted` / `insufficient_quota` for the
configured key. Neither run produced live model-choice evidence.

In the third run the returned model was `gpt-5.4-mini-2026-03-17`. Every successful
proposal selected read; both resource alternatives were selected across scenarios.
Within-scenario action/resource variation was not observed, though reason wording
varied. No live invalid proposal or export choice was observed. Rejection and
export enforcement remain demonstrated by injected-output tests, not live behavior.
The 17 proposals were forwarded unchanged to governance, and all 5 denied proposals
had no execution attempt. See the saved audit for exact outcome counts and checks.

The proposed claim is: a language model chooses an action and target complaint
from alternatives, then OPA evaluates that exact proposal and the application
executes or blocks it while preserving separate proposal, governance, dispatch,
and outcome evidence.

## Flow and authorization boundary

`build_request` presents at least two distinct complaint candidates. A single
replaceable callable (`propose_openai` by default) returns response text and model
metadata. It uses the OpenAI Responses API directly through Python's standard
library, without an SDK, framework, tools, delegation, or autonomous loop.

The runner records the request before calling the provider and preserves the raw
response before parsing. Structured output requires `action`, `resource_id`, and
`reason`. The reason is a model-provided explanation, not verified reasoning.

**Validation is not authorization:**

- A known complaint outside the actor's scope is a valid proposal. It reaches OPA
  unchanged, which decides whether to DENY.
- `read` and `export` are supported proposal names. `export` is valid, reaches
  OPA unchanged, and is denied by the existing read-only policy.
- Malformed/duplicate-key JSON, missing fields, invalid types, unsupported names
  such as `delete`, and resource IDs not in the presented catalog are rejected
  before governance. There is no normalization, fallback ID, or repair call.
- Refusal, incomplete response, and provider failure are distinct recorded states;
  they are not unauthorized selections or policy denials.

The runtime now has `governed_action`, backed by the same policy input, OPA call,
governance builder, and complaint-store path as the compatible `governed_read`
wrapper. The selected action is copied into policy input instead of hardcoded to
read. The selected ID is used for both policy evaluation and resource dispatch.
Only read has an executor. An unexpected ALLOW for export fails closed with an
integration error; export is never silently rewritten into read.

The new entry point offers no bypass flag. The legacy bypass facility remains
only for existing regression tests. No policy, authority source, execution schema,
correlation assertion model, or benchmark algorithm/result is changed.

## Evidence

Each trial directory can contain:

- `agent.jsonl`: versioned request, raw proposal, accepted/rejected validation,
  governance reference/input, execution disposition, attempt, and observed outcome.
- `opa.jsonl`: existing OPA native decision-log capture for valid proposals.
- `governance.jsonl`: existing normalized governance evidence.
- `execution.jsonl`: existing complaint-store evidence after successful reads.

An actual dispatch has a pre-call `EXECUTION_ATTEMPT`. A denied proposal has
`BLOCKED_BY_GOVERNANCE` and `DENIED_NO_EXECUTION`, with no dispatch attempt or
store call. A read failure has an attempt and failed outcome; `resource_read` is
unknown because a failure may occur after reading but before logging/return.
Governance failure is `RUNTIME_ERROR`, not DENY. No execution is inferred merely
from ALLOW, and no fictional attempt is emitted for blocked actions.

Request bodies preserve the entire task, candidate list/order, output schema,
requested model, output limit, and explicitly sent API settings. Response bodies
preserve provider/model identifiers, response ID, status, output, and usage where
returned. Event payloads have canonical digests. Request authorization headers and
credentials are not logged. `store=false` is sent; this does not itself make claims
about provider-side retention rules.

The run manifest records source, policy, authority, and scenario hashes. Context
can be reconstructed, but hosted model outputs are not guaranteed reproducible.
Omitted sampling settings use provider defaults; no determinism is claimed.

## Twenty controlled live trials

```sh
# Configure OPENAI_API_KEY locally; never put its value in committed files.
.venv/bin/python -B -m experiments.model_agent.run_trials \
  --model gpt-5.4-mini --output /tmp/agent-gov-m3-trials
```

Choose a new output directory. The command schedules four scenarios with five
calls each, retaining all outcomes. It does not retry rejected proposals, continue
conversations, or reroll until a desired outcome occurs. A failed call is reported
as failed and is not counted as successful model choice.

Scenarios are: current-review-queue choice, urgent complaint outside the current
queue, equally plausible choices, and read/export reporting choice. Every request
contains both complaint alternatives. All five repetitions within a scenario use
identical prompts and candidate order, so order changes do not masquerade as model
variation. Scenario metadata affects task difficulty and preferences, but no
selector computes or injects an answer. The equally plausible case can still have
position/ID biases; this small experiment does not eliminate them.

`results.json` and `README.md` report actual action/resource frequencies, DENY,
execution, invalid output, and other failures. Absence of unauthorized selections
or variation must be reported honestly. No live result is replaced with a stub.
Malformed/unknown/unsupported proposal coverage is provided by explicitly injected
unit tests, whether or not the live model emits any such cases.

## Tests

```sh
PATH="$PWD/.venv/bin:$PATH" RUN_FOREIGN_OPA=1 \
  .venv/bin/python -B -m pytest -p no:cacheprovider -q
```

Tests cover multiple candidates, independent supplied model choices, exact action
and resource forwarding, proposal-before-governance ordering, explicit validation
errors, OPA DENY for unauthorized read and export, no dispatch on DENY, pre-dispatch
attempt recording, failed outcomes, and fail-closed handling of missing executors.
Docker integration tests use injected model outputs and real OPA. They test the
governance boundary, not real model selection. Existing runtime and prior milestone
tests remain part of the full suite.

## Remaining assumptions and falsifiers

The complaints, priorities, task descriptions, catalog, authority registry, and
resource store are synthetic/cooperative. Candidate descriptors are deliberately
provided as pre-governance metadata; protected complaint bodies are not read into
the prompt. Prior fixture summaries that label resources authorized/unauthorized
are not used as the candidate prompt. The synthetic selector, input fixture, and
preselected trajectories are not called.

Model provider output is external, but local runtime and execution evidence is
cooperating instrumentation. OPA logs in this experiment are persisted through
the existing runtime, not the earlier independently persisted custody experiment.
Run/attempt IDs address these local records; they are not proof of independent
cross-system correlation. There is no control-effectiveness attestation.

The milestone claim would be invalidated by a fixture choosing the target,
rewriting model output, evaluating before selection, dispatching a different
resource/action, executing a denied proposal, or reporting injected tests as live
model trials. A well-formed unauthorized selection is evidence of the model's
proposal plus enforcement, not a malformed-output failure. A rationale is not
proof of intent, and twenty trials are not a production reliability estimate.
