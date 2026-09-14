# OPA producer source review, preregistration support

Scope: stock `opa exec` v1.19.0, as invoked by `src/governance_event.py` at AGG baseline 28c2523. This is a source finding, not a live behavioral result. No policy decisions were executed for this review.

## Verified stock exec chain

1. [`cmd/exec.go`](https://github.com/open-policy-agent/opa/blob/v1.19.0/cmd/exec.go#L129-L160) constructs an SDK OPA and calls `exec.Exec`.
2. [`cmd/internal/exec/exec.go`](https://github.com/open-policy-agent/opa/blob/v1.19.0/cmd/internal/exec/exec.go#L32-L67) binds the reporter's decision function to `opa.Decision`; stdin is parsed as the policy input and sent to `StoreDecision`.
3. [`json_reporter.go`](https://github.com/open-policy-agent/opa/blob/v1.19.0/cmd/internal/exec/json_reporter.go#L45-L59) constructs `sdk.DecisionOptions` with only Path, Now, and Input. It supplies no DecisionID. After successful evaluation it places `rs.ID` in output `decision_id`.
4. [`sdk/opa.go` Decision](https://github.com/open-policy-agent/opa/blob/v1.19.0/v1/sdk/opa.go#L304-L313) copies `options.DecisionID` into `server.Info.DecisionID`. [`executeTransaction`](https://github.com/open-policy-agent/opa/blob/v1.19.0/v1/sdk/opa.go#L363-L444) generates `uuid.New(rand.Reader)` only when that field is empty, assigns the resulting ID to `DecisionResult.ID`, and passes the same record to the configured logger. `rand` is `crypto/rand` (SDK source line 12).
5. [`internal/uuid/uuid.go`](https://github.com/open-policy-agent/opa/blob/v1.19.0/internal/uuid/uuid.go#L19-L30) reads 16 random bytes, sets UUID version 4 and variant bits, then formats the ID.

Therefore stock exec does not promote policy input fields named `decision_id`, `request_id`, `action_attempt_id`, or similar into the SDK DecisionID option. Repeated policy inputs follow the fresh generation path. A finite experiment can check emitted values in the tested sample; it cannot establish universal collision freedom. Stdout response and decision log are two representations of one OPA evaluation, not independent evidence sources.

## Other integration modes

The same SDK DecisionOptions has an explicit caller-supplied DecisionID option; nonempty values bypass generation. The API does not establish uniqueness or authenticity of a caller value. Therefore an unrestricted claim that every OPA decision_id is OPA-generated would be wrong.

For the standard REST runtime, [`decisionIDFactory`](https://github.com/open-policy-agent/opa/blob/v1.19.0/v1/runtime/runtime.go#L930-L937) first honors a custom runtime factory, otherwise generates an ID only when decision logging is configured, and otherwise returns an empty string. [`generateDecisionID`](https://github.com/open-policy-agent/opa/blob/v1.19.0/v1/runtime/runtime.go#L1127-L1132) uses the same random UUID function. [`server.go`](https://github.com/open-policy-agent/opa/blob/v1.19.0/v1/server/server.go) exposes WithDecisionIDFactory for custom embeddings. These customization hooks do not imply that stock exec accepts a caller ID from policy input or HTTP headers.

The [current REST documentation](https://www.openpolicyagent.org/docs/rest-api) describes decision_id in the Data API response when decision logging is enabled and its correspondence with the log. This documentation is supplemental and not version pinned. REST v1 Data response envelopes and exec's result array differ; REST behavior is not substituted for the actual exec integration.

## AGG preservation boundary

`src/governance_event.py:evaluate_policy_with_decision_log` launches the 1.19.0 image with exec, stdin input, a local bundle, and console JSON decision logging. It parses stdout, selects the first stderr record with the decision-log type, and checks response/log decision_id and result equality. It returns the log object. It does not currently enforce exactly one decision-log record or retain the full original stderr stream.

`src/complaint_runtime.py:append_opa_decision_event` serializes that object into JSONL. Fields including native decision_id are retained, but whitespace/order and the original byte stream are not preserved by that path. `src/foreign_opa_evidence.py` separately performs read-only file ingestion retaining original location, file/line digests, parsed raw_record and ingestion timestamp; these are provenance/integrity metadata, not producer authentication. The bounded experiment must preserve original stdout/stderr before normalization to support byte-level review.

The current runtime keeps run_id, step_id, action_attempt_id, agent_id and authority_binding in governance context; governance event_id is independently generated with uuid4. Its GOVERNANCE_DECISION emission includes governance_event_id, policy_input and decision, but does not emit the OPA ID. The OPA record is retained separately. This review does not claim that current execution is bound through a returned OPA decision_id.

Current AGG evidence alone is insufficient to distinguish stock exec generation from a caller-supplied SDK DecisionID. The checked-in invocation establishes the intended integration, and retained raw OPA fields can include producer/version labels, but those fields do not identify which invocation/API option generated a particular ID: both stock exec and SDK callers can produce the same decision-log shape. `native_assertions` requires issuer and namespace declarations and preserves them in rule parameters, while explicitly treating issuer, scope and non-reuse as unauthenticated caller assumptions; it does not verify the ID-generation path. File/line digests preserve custody relationships after capture, not a binding from an individual record to a verified binary, invocation configuration and absence of a supplied DecisionID. The new bounded experiment can supply invocation/image evidence for its own captured sample; existing ordinary records lack that substantiated distinction.

## Binary/source limitation

The orchestrator reports local image ID `sha256:8523599954435a3659954ad51ee0304d22bd97576f16cdb02e5e39f38ff3962a`, version 1.19.0 and build commit `1e32c796e8979b1bda2f768138500b1deb95ff24-dirty`. This review establishes the tagged source chain; it does not independently prove reproducible correspondence of that dirty-reported binary to the tag. Preserve image identity and version output, and phrase conclusions as source expectation plus observed behavior of that image/configuration. Do not generalize to custom builds, SDK callers, alternate configurations or all deployments.

Source pages were read from official GitHub v1.19.0 URLs; files unavailable to the web cache were read directly from raw.githubusercontent.com with the same tag. No repository implementation was changed during source inspection.
