# Identifier provenance evidence comparison

Decision baseline: `1c555013e7140135075e9deebedcd1dc9da47dd7`. Frozen protocol: `62019d0dec227cb25494a3206f93dfa0e883ee33`, `docs/identifier-provenance-decision/PROTOCOL.md`. This is a read-only analysis of that baseline, with one additive document. No new producer observation, historical rescoring, or production implementation is represented here.

**Recommendation: CONTEXT_NEEDED_PRODUCTION_DEFERRED.** Producer and observation semantics change what equal values support. Existing evidence plus a bounded interpretation note can express those distinctions for the present investigation. No concrete current or next protected operation has been demonstrated to require a new production representation. This does not establish that documentation changes user behavior or make current automated assurance generally safe.

## Source key and actual preservation boundary

All file references below are repository-relative and refer to the decision baseline unless explicitly identified as the frozen decision protocol. Line references identify the inspected text, not independent authentication of it.

- **N1:** `experiments/nginx_producer_conformance/results/v1/nginx.conf:6-19` maps incoming `$http_x_request_id` separately from native `$request_id`, logs both, and returns the latter as `X-Request-ID`. The captured effective configuration agrees at `experiments/nginx_producer_conformance/results/v1/nginx-T.txt:7-20`.
- **N2:** `experiments/nginx_producer_conformance/results/v1/native/access.jsonl:1-8` records eight requests. Lines 1, 2, 7 and 8 reuse incoming `SAME-VALUE` while native IDs differ. `experiments/nginx_producer_conformance/results/v1/requests/007.http:4` supplies `SAME-VALUE`; `experiments/nginx_producer_conformance/results/v1/responses/007.http:9` returns `d652669eea3a0cd5326302654b72afb1`, equal to native log line 7. Full finite comparison: `experiments/nginx_producer_conformance/results/v1/REPORT.md:9-22`.
- **N3:** `experiments/target_outcome/http_client.py:25-28` records the response header and receipt metrics. `src/action_evidence.py:48-50,92-103` retains parsed raw execution records and exposes `request_id`; `src/target_outcome_evidence.py:9-19` retains the parsed raw outcome record and target contract and exposes native `request_id`. Outcome meaning has explicit conditions and limits at `src/target_outcome_evidence.py:30-39`. Ingestion retains file/line/byte custody at `src/action_evidence.py:20-33`. It does not automatically encode the generation/observation distinction in the normalized identifier field. Raw preservation does not recreate an incoming header never collected by the original integration; see `experiments/nginx_producer_conformance/results/v1/REPORT.md:28-30`.
- **O1:** `experiments/opa_producer_conformance/results/v1/invocations/001/invocation.json:2-18` records the image and stock exec arguments. `experiments/opa_producer_conformance/results/v1/invocations/001/stdout.bin:4` and `experiments/opa_producer_conformance/results/v1/invocations/001/stderr.bin:1` contain the same `ba745148-8494-4c5f-9c41-eaef347028f5` decision ID. `experiments/opa_producer_conformance/results/v1/result.json:3-82` records all eight checks and sample limitations; `experiments/opa_producer_conformance/README.md:25-35` summarizes observations and limits.
- **O2:** `experiments/opa_producer_conformance/SOURCE_REVIEW.md:7-19` records the pinned v1.19.0 source chain and exact upstream line references: stock reporter omits SDK DecisionID, SDK generates only when empty, nonempty SDK values bypass generation, and a custom runtime can supply a factory. This is a preserved source review, not a live SDK/custom-runtime campaign. Binary correspondence remains limited by the reported dirty build (`SOURCE_REVIEW.md:33-35`).
- **O3:** `src/governance_event.py:48-72,75-118` invokes stock exec, selects the first native log and compares output/log IDs and results. It does not retain full original streams or prove unique log cardinality. `src/complaint_runtime.py:60-79` serializes the log object; `src/foreign_opa_evidence.py:52-100` preserves a subsequently ingested file's location, byte offsets, digests, raw parsed record and ingestion timestamp. The OPA ID remains available in `raw_record`; it is not promoted among the normalized fields at lines 93-97. None of those custody fields binds an arbitrary historical record to a verified generation mode.
- **O4:** `src/complaint_runtime.py:217-218` emits governance ID, input and decision without the OPA ID. `experiments/opa_producer_conformance/SOURCE_REVIEW.md:29-31` explicitly bounds the current execution relationship. The hypothetical execution recording case below is not a claim that this runtime currently records returned OPA IDs against execution.
- **M1:** `src/correlation_assertion.py:144-203` accepts a selected identifier field, declared issuer/namespace and optional equal-field invariants. Candidate selection is exact identifier equality (159-163); mutual uniqueness and invariants determine LINKED (169-185). Issuer/namespace are retained in rule parameters (195-198); scope/non-reuse/authentication and causal limits are explicit (194-203). No generation-path verification occurs there.
- **M0:** `src/m6_attestation_evidence.py:573-606` already reads per-record, per-field `identifier_declarations` with exactly `issuer` and `namespace`, checks compatibility, and considers `request_namespace_observation` where present. These are existing machine-readable declarations, not verified generation provenance. Alternative C therefore means additional generation/observation/evidence semantics, not the first machine-readable identifier representation.
- **M2:** `src/action_reconciliation.py:19-51` replays supplied correlations and consumes LINKED edges. `src/m6_attestation_evidence.py:663-697` consumes cited native LINKED governance-execution-outcome paths, checks namespaces and governance scope, and reports declared compatibility. These downstream consumers exist; this analysis does not rely on any older statement that correlations never feed assurance. The examined path qualification does not verify producer generation provenance. The two producer campaigns do not demonstrate a new current false-positive control-effectiveness defect or establish that their finite successes repair historical Strong-Link Assurance Falsification, which remains FAILED.

## Comparison method

A uses the retained evidence, existing declarations and existing limitations directly. B adds a bounded human-readable field interpretation note pointing to that same evidence and explicitly marking unknowns; the review candidate is `docs/identifier-provenance-decision/INTERPRETATION_NOTES.md`. C is a proposed machine-readable production representation, evaluated for what it could encode using the same evidence; no particular new schema or consumer is assumed to exist. C is not given stronger authentication, additional independent observations, or an implementation benefit by assumption.

For each case the six questions are answered once in the factual envelope; every alternative is then assessed against that entire envelope. “Sufficient” means sufficient for this bounded investigation to state the supported relationship and withhold stronger conclusions, not sufficient for universal automated control attestation.

## 1. NGINX incoming header versus native request ID — empirical

| Question | Evidenced answer |
|---|---|
| Where observed? | Incoming request header and the access log's `incoming_x_request_id`; separately the access log's `request_id` (N1, N2). |
| Who generated/supplied? | Test caller supplies incoming sentinels. Preserved configuration and observations support native NGINX generation for the tested request IDs; incoming values are not substituted into them. |
| Namespace/configuration? | The captured NGINX configuration and its incoming/native variable mapping, within this eight-request campaign. A generic field name or arbitrary declared namespace cannot substitute for this mapping. |
| Relationship? | Repeated incoming `SAME-VALUE` establishes repeated supplied content across distinct requests, not one request. Native IDs distinguish these eight observations. No universal uniqueness claim follows. |
| Supporting evidence? | N1 configuration plus N2 request bytes and native log lines; report checks cover all eight requests. |
| Unknown? | Authenticity beyond retained custody, collision behavior outside the sample, unobserved deployments and missing historical incoming headers. |

| Alternative | Assessment against all six answers |
|---|---|
| A | Sufficient: the two raw field names, captured configuration and requests disclose observation point, supplier, scope and supported relationship; ordinary limitations preserve the listed unknowns. An analyst must follow the references. |
| B | Sufficient and recommended: a note explicitly maps each raw field to incoming/native meaning, references N1/N2, bounds scope and repeats unknowns. It adds retrieval convenience, not evidence. |
| C | Can encode the same mapping, scope and evidence references, with unknowns explicit; cannot establish absent historical incoming values or global uniqueness. No current consumer requirement has been demonstrated that A/B cannot satisfy. |

This observed reuse is materially different from reuse of a purported native request identifier. The latter interpretation would require evidence about generation, reuse or recording failure. The campaign did not observe native reuse; do not turn that counterfactual into a producer failure.

## 2. NGINX response header versus access-log ID — empirical

| Question | Evidenced answer |
|---|---|
| Where observed? | Returned HTTP `X-Request-ID` and native access-log `request_id` (N2). Existing execution adapter exposes the client's recorded response ID (N3). |
| Who generated/supplied? | Under N1 the server puts native `$request_id` in the response; the caller observes/records it. A client-recorded value is not thereby client-generated. |
| Namespace/configuration? | This captured static-target configuration and request/response exchange, conditional on custody and configuration applicability. |
| Relationship? | Supports association of the captured response and log with the request under this configuration. Both ID appearances derive from the same server request; they do not create two independent attestations of control effectiveness. |
| Supporting evidence? | N1 response mapping; N2 exact matching value in response 007 and log line 7; eight-pair report; N3 identifies the ordinary recording path. |
| Unknown? | Authenticity of an arbitrary client record, configuration applicability outside capture, client use of returned data and all-agent governance/enforcement coverage. Outcome conclusions require separate native status/bytes/contract evidence, not ID equality alone. |

| Alternative | Assessment against all six answers |
|---|---|
| A | Sufficient for the bounded association: raw response/log and retained client/server code identify observation, generation, scope and evidence. Existing limits bar promotion to independent execution/control proof. |
| B | Sufficient: note “server-generated, response-observed, caller-recorded” with N1-N3 references and request-scoped relationship; retain all listed unknowns. This prevents ambiguity in the written interpretation, without proving reader error reduction. |
| C | Can encode those roles and same-origin dependence; cannot authenticate caller recording or supply outcome evidence. No operation requiring machine consumption of that annotation has been established now. |

## 3. OPA stock exec output versus decision-log ID — empirical plus source interpretation

| Question | Evidenced answer |
|---|---|
| Where observed? | Exec stdout result `decision_id` and console decision-log `decision_id` (O1). |
| Who generated/supplied? | Stock exec omits SDK DecisionID per O2; tested output/log IDs are distinct across eight invocations and differ from supplied input sentinels (O1). Generation-path attribution combines source expectation and captured invocation; it is not a binary reproducibility proof. |
| Namespace/configuration? | Captured image/configuration, stock exec mode, decision logging, policy path and eight invocations. “OPA” or version alone is insufficient to generalize this attribution. |
| Relationship? | Two representations of the same authorization evaluation, conditional on trustworthy invocation custody. Neither representation independently proves execution, enforcement, caller identity or target outcome. |
| Supporting evidence? | O1 archived stdout/stderr, invocation and checks; O2 version-pinned source review; O3 actual integration path. |
| Unknown? | Universal uniqueness, untested integrations, dirty binary correspondence, pre-ingestion authenticity and generation mode of ordinary records without invocation binding. |

| Alternative | Assessment against all six answers |
|---|---|
| A | Sufficient for this sample: O1/O2/O3 and their limitations express the exact observation, generation expectation, scope, evaluation relationship and unknowns. Insufficient to establish the same generation mode for arbitrary ordinary logs; safe conclusion there is unknown. |
| B | Sufficient: a field note binds the interpretation to this sample and stock exec evidence, labels source versus observation, and repeats unknowns. It must not automatically apply sample provenance to ordinary logs. |
| C | Can encode sample-scoped generation expectation and same-evaluation relationship; ordinary records still lack evidenced mode. Representation alone cannot extend sample scope or prove execution. Production necessity is not demonstrated. |

## 4. SDK/custom-runtime supplied ID — source-reviewed only

| Question | Evidenced answer |
|---|---|
| Where observed? | No live SDK/custom-runtime capture in these campaigns. Relevant fields and options are described by pinned source review (O2). |
| Who generated/supplied? | SDK caller can supply a nonempty DecisionID; runtime embedding can customize its factory. Attribution for any actual unidentified record remains unknown. |
| Namespace/configuration? | Pinned v1.19.0 SDK/custom embedding code paths; actual invocation/options/configuration would be needed to apply that source result to a record. |
| Relationship? | Equality may reflect a supplied/reused value, not fresh producer generation. It can associate output/log within a known evaluation, but cannot by itself identify one evaluation across an unbounded population. |
| Supporting evidence? | O2 source review, especially lines 10 and 17-19; no new independent producer evidence. |
| Unknown? | Whether a particular record used a supplied value, actual reuse frequency, live custom-runtime behavior and producer authenticity. |

| Alternative | Assessment against all six answers |
|---|---|
| A | Sufficient to state the source-supported alternative interpretation and leave actual mode unknown. The review and existing limitations already do this. It cannot establish observed custom behavior. |
| B | Sufficient: mark source-only mode, option/factory path, possible relationship and unknown record attribution, referencing O2. No invented capture or attribution is needed. |
| C | Can encode source-reviewed possibility or unknown mode; cannot populate verified generation provenance for a record without additional ordinary evidence. Requiring a producer label to be authored by AGG would not resolve that evidential gap. |

This supplies an exact equal-value thought comparison grounded in reviewed code: a nonempty SDK option could contain the same UUID string seen in stock exec. The string then has a different origin even though its shape/value agrees. That source-supported possibility establishes a need for contextual interpretation; it is not an empirical collision/reuse result.

## 5. Caller records returned OPA ID against execution — hypothetical

| Question | Evidenced answer |
|---|---|
| Where observed? | Hypothetical execution record containing a previously returned OPA ID. O4 shows this is not the current governance emission. |
| Who generated/supplied? | OPA may generate the original ID under case 3; the caller supplies its later execution association. These are distinct assertions. |
| Namespace/configuration? | Would require the actual producer/invocation mode and caller recording path. Neither can be inferred from equal values in imagined records. |
| Relationship? | At most a caller assertion that execution corresponds to an authorization evaluation. Equality does not establish that execution happened or obeyed that decision. |
| Supporting evidence? | Conditional reasoning from O1-O4 and M1 limitations, not a captured execution experiment. |
| Unknown? | Whether such execution occurred, truth of the caller's association, execution details, enforcement and outcome. |

| Alternative | Assessment against all six answers |
|---|---|
| A | Sufficient to identify the hypothetical observation, separate original generation from later supply, and withhold the execution claim under existing limitations. No factual execution relationship can be established. |
| B | Sufficient: note “caller-asserted association” and missing execution evidence, conditional on real future recording/context. A note cannot upgrade it. |
| C | Can encode original origin versus later assertion and unknowns; still cannot establish actual execution or enforcement. No available independent evidence makes C resolve the proposed stronger operation. |

## 6. Missing producer/configuration context — withholding thought experiment

| Question | Evidenced answer |
|---|---|
| Where observed? | Assume identifier-bearing records remain but their producer/configuration binding is withheld. Only retained field/location observations are known; unretained observation direction is unknown. |
| Who generated/supplied? | Unknown. O2 establishes multiple possible OPA modes; N1 shows why a header's direction matters. |
| Namespace/configuration? | Declared issuer/namespace can remain, but their truth and configuration applicability are not established. M1 already distinguishes declarations from authentication. |
| Relationship? | Equality under declared assumptions can be reported; stronger producer-native, causal, execution or control claims must be withheld. |
| Supporting evidence? | Remaining raw records and declarations, plus the explicit fact that context is withheld in this thought experiment; not a new campaign. |
| Unknown? | Actual generation mode, applicable configuration, trust in producer attribution and any relationship requiring those facts. |

| Alternative | Assessment against all six answers |
|---|---|
| A | Sufficient to report observations/declarations and the evidential boundary. Cannot recover missing facts, and must not infer them from LINKED. This is investigative restraint, not an implemented new automated gate. |
| B | Sufficient: note absent context explicitly, retain available references and bound relationship to declarations. Missing evidence remains missing. |
| C | Can represent unknown/context-absent; cannot resolve any missing fact with available evidence. Machine-readable unknowns could be useful to a future consumer, but no necessary current consumer/change is demonstrated. |

## Necessity decision and negative findings

Context necessity is supported by NGINX's observed repeated incoming values versus its independently generated native field semantics, together with the source-supported stock/SDK equal-value origin distinction. It is not based merely on field naming. NGINX response and OPA output/log cases also show why generation and observation roles must remain distinct and why multiple appearances are not independent source multiplication.

The concrete present operation is an investigator explaining what the preserved identifiers support, with source references and unknowns. A can do this; B makes the six answers explicit in one bounded note. This matrix demonstrates expressibility using existing artifacts, not improved user comprehension or fewer assurance errors. For arbitrary ordinary records lacking context, all three alternatives must withhold the same claims. Their inability to resolve those records is an evidence limitation, not a proof that C is necessary.

The strongest case for C is eventual automatic rejection of an unsupported relationship in downstream assurance. M2 confirms that downstream consumers exist and currently examine declared namespace/scope and native LINKED paths. However, this milestone has not demonstrated a specific current or next protected automated operation that A/B cannot support safely, an evidence source that would substantiate its new provenance inputs, and a consumer whose behavior C would change correctly. A schema without such a consumer would only store another declaration. No broader safety claim for downstream assurance is made here; the historical FAILED result and its implications remain unchanged.

Accordingly:

- Reject **NO_ADDITIONAL_CONTEXT_JUSTIFIED**: materially different defensible interpretations are evidenced/source-supported.
- Reject **PRODUCTION_REPRESENTATION_JUSTIFIED** now: A/B suffice for the named investigation; no necessary consuming operation, additional ordinary evidence, or unavoidable collection/maintenance cost is demonstrated.
- Prefer **CONTEXT_NEEDED_PRODUCTION_DEFERRED** over NOT_DEMONSTRATED: context need can be established while production necessity fails its separate criteria.
- Retain B as a bounded documentation recommendation, not a schema, runtime gate, assurance upgrade, or measured commercial benefit. No specific M9b/M9a-ii operation is invented and neither is started.
- Reopen C only with an explicitly scoped protected operation, a demonstrated A/B failure for it, ordinary evidence that C can use to resolve the failure, and an assessment of necessary collection and maintenance cost. Representation must preserve unknowns and source dependence.

No live experiments, new fixtures, tests, production edits or commits were performed for this comparison. Cited line locations were read directly from the repository. Checkpoint validation and any publication decision remain with the orchestrator/owner.
