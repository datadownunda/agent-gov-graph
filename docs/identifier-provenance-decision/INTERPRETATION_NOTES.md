# Bounded field interpretation notes — review artifact, not a production contract

These notes demonstrate alternative B from the frozen protocol: the known distinctions can be expressed with references to existing evidence, without adding producer fields or altering matching. They do not demonstrate that human reviewers make fewer errors. Applicability is limited to the named archived integrations; missing context stays unknown.

## NGINX request identifiers

Observation: the campaign separately captured incoming `X-Request-ID`, native access-log `request_id`, and outgoing response `X-Request-ID`. The archived configuration maps the incoming value to `$http_x_request_id`, and the native/returned value to `$request_id`. See [campaign report](../../experiments/nginx_producer_conformance/results/v1/REPORT.md) and [protocol](../../experiments/nginx_producer_conformance/PROTOCOL.md).

Generation/supply: the request sender supplies the incoming value. The tested server produces the native value; repeated incoming values did not cause duplicate native values in eight requests. This does not establish universal uniqueness. The response and log record the same server request identifier; they are not two independently generated identifiers or independent corroborations of control effectiveness.

Applicability/namespace: use the archived configuration and campaign image/invocation records as the bounded basis. Neither the product name NGINX nor an issuer string establishes a global namespace or proves that another server used this configuration. The ordinary [HTTP client](../../experiments/target_outcome/http_client.py) records the returned header and does not supply a chosen request ID. That is code evidence about this client, not proof that every execution record is truthful.

Permitted interpretation: within the captured process/request custody, response/log equality associates the observations with one tested request. Reused incoming values do not establish same-request identity. A historical synthetic copied native ID is not thereby demonstrated behavior of the tested server. Unknown: authenticity outside this custody, configuration applicability elsewhere, hidden duplicates, and execution/authorization relationships not separately evidenced.

## OPA decision identifiers

Observation: `opa exec` stdout `result[0].decision_id` and console decision-log `decision_id`; policy input is separate. See [source review](../../experiments/opa_producer_conformance/SOURCE_REVIEW.md) and [eight-case result](../../experiments/opa_producer_conformance/results/v1/result.json).

Generation/supply: tagged stock exec passes no SDK DecisionID option, so the SDK generates a random UUID. The archived eight evaluations emitted distinct values matching between output and log; none copied input sentinels. A custom SDK caller can instead supply DecisionID. That alternate path was source-reviewed, not captured in a live SDK experiment.

Applicability/namespace: the archived image/configuration and process custody bound this interpretation. The image's dirty build suffix leaves binary-to-tag correspondence unproven. A version label or the text `OPA` cannot establish which invocation mode supplied an arbitrary ID. Namespace/non-reuse declarations remain declarations.

Permitted interpretation: output/log agreement supports one evaluation under the stated custody. Both are views of that evaluation. A caller recording the returned value against execution supplies an assertion about execution; it is not independent proof of execution, enforcement, authenticated identity, target outcome or valid delegation. The current runtime does not itself emit this OPA ID as the execution binding under examination. Without invocation/configuration evidence, generation mode and supported relationship remain unknown.

## Use boundary

These are consumer-side analysis notes referencing ordinary retained records and configuration. They do not require OPA, NGINX or other producing systems to emit AGG-specific fields. Do not inject these conclusions into the existing `identifier_declarations` or upgrade an automated finding with them. Any machine-enforced interpretation would need a separately approved protocol specifying the consumer, source applicability, missing-evidence behavior and adversarial tests.
