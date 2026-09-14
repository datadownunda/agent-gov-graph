# NGINX producer conformance

**PRODUCER_CONTRACT_SUPPORTED**

Baseline: 435d15f4c705e9cbd55f28baee7c4e1136867b07

Protocol SHA-256: f5da0eefad4f7d3e818b027a4894001d55d8d9973142b86a489c2d0f1f89b9df

|Request|URI|Incoming (native observation)|Native ID|Returned ID|Equals incoming|Other requests with native ID|
|---|---|---|---|---|---|---|
|1|/complaints/complaint-789.json|'SAME-VALUE'|762a616db388341ab1f75a0e4da4a7fe|['762a616db388341ab1f75a0e4da4a7fe']|False|[]|
|2|/complaints/complaint-789.json|'SAME-VALUE'|ddd49b4560f3297e9a011ae048656b9b|['ddd49b4560f3297e9a011ae048656b9b']|False|[]|
|3|/complaints/complaint-789.json|''|0cf60616db20dc9cdf35725232eeefca|['0cf60616db20dc9cdf35725232eeefca']|None|[]|
|4|/complaints/complaint-789.json|''|07399c2e9d5fb684093c69e949137ff3|['07399c2e9d5fb684093c69e949137ff3']|None|[]|
|5|/complaints/complaint-789.json|'VALUE-A'|c1453c873e899facc99937d89beccde3|['c1453c873e899facc99937d89beccde3']|False|[]|
|6|/complaints/complaint-789.json|'VALUE-B'|6ca64f6e4b690f7928d21bb375c26130|['6ca64f6e4b690f7928d21bb375c26130']|False|[]|
|7|/complaints/complaint-456.json|'SAME-VALUE'|d652669eea3a0cd5326302654b72afb1|['d652669eea3a0cd5326302654b72afb1']|False|[]|
|8|/complaints/complaint-456.json|'SAME-VALUE'|7e43f8968beefa9853fb1fbd1242677c|['7e43f8968beefa9853fb1fbd1242677c']|False|[]|

No duplicate native $request_id values observed across the eight captured requests.

Checks and failures: {"request_1": true, "request_2": true, "request_3": true, "request_4": true, "request_5": true, "request_6": true, "request_7": true, "request_8": true, "capture_complete": true, "no_duplicate_native_ids_observed": true, "pair_1_2_equal_incoming_distinct_native": true, "pair_7_8_equal_incoming_distinct_native": true, "supplied_incoming_distinct_from_native": true}

Errors: []

## Repository representation analysis

The existing target_outcome/nginx.conf logs $request_id and returns it as X-Request-ID. http_client.py reads that response header and sends no selected request ID. Existing raw logs plus preserved code/configuration identify that meaning, but do not record incoming request-ID headers. This campaign preserves both fields independently.

src/action_evidence.py retains raw records while exposing execution request_id. src/target_outcome_evidence.py retains raw records and target contract while exposing outcome request_id. Normalization omits structured generation/observation semantics; it does not destructively discard raw fields. src/correlation_assertion.py uses a caller-selected field and declared issuer/namespace, not verified generation provenance. schemas/action_evidence.schema.json retains raw evidence but does not require identifier provenance. A minimal field annotation referencing the producer field, observation direction and preserved configuration could suffice for this fixed chain; no generic subsystem or matcher change is justified by this campaign alone.

## Historical implications

If the producer contract is supported, deliberate copied/recycled native IDs in copied/different, copied/removed, copied/identical and reuse/period are not demonstrated behavior of this stock NGINX contract. This does not rule out random collisions, false client records, collector faults or altered producers. Runtime action_attempt_id reuse, namespace loss and aggregate-outcome semantics are not tested here. Incoming/forwarded identifier reuse remains possible, as the repeated incoming values demonstrate. No historical inputs, scorer truth, scores, protocol or FAILED verdict are changed. If this campaign is not supported, these implications remain conditional and require investigation of the preserved unexpected evidence.

No authentication, cryptographic uniqueness, general error-frequency, governance coverage or control-effectiveness claim follows.
