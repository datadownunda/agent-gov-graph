# NGINX identifier generation producer conformance — protocol v1

Baseline: 435d15f4c705e9cbd55f28baee7c4e1136867b07.

Claim: Under the archived NGINX configuration with additive logging, incoming caller-supplied identifiers and native $request_id values are distinct. Repeating an incoming identifier does not cause the tested requests to share a native $request_id. This finite experiment does not establish cryptographic uniqueness or impossibility of random collision.

Use the existing pinned NGINX image, static complaint resources, synthetic Basic authentication and loopback-only binding. Copy the existing configuration, adding only incoming_x_request_id sourced from $http_x_request_id to its JSON access log. Preserve request_id sourced from $request_id and the response directive add_header X-Request-ID $request_id always. Do not invoke governance, matching or assurance logic.

Issue exactly eight sequential GET requests on fresh connections, with no automatic retry:

| Number | URI | Incoming X-Request-ID |
|---|---|---|
|1|/complaints/complaint-789.json|SAME-VALUE|
|2|/complaints/complaint-789.json|SAME-VALUE|
|3|/complaints/complaint-789.json|absent|
|4|/complaints/complaint-789.json|absent|
|5|/complaints/complaint-789.json|VALUE-A|
|6|/complaints/complaint-789.json|VALUE-B|
|7|/complaints/complaint-456.json|SAME-VALUE|
|8|/complaints/complaint-456.json|SAME-VALUE|

Capture raw response bytes and native access-log bytes. Request captures redact only the ephemeral Authorization value. Associate requests to log rows by sequential issuance, waiting for exactly one new row before the next request; IDs are not association keys. Preserve absent incoming header representation exactly as logged. Preserve sequence and timestamps outside native rows. Ground truth contains request sequence and sent headers only, never generated IDs.

Preregistered checks: eight complete 200 responses, eight complete native rows, correct URI/method/status and incoming-header observation, native IDs matching 32 hexadecimal characters, exactly one response X-Request-ID equal to its native ID, native IDs different from supplied incoming values, and no duplicate native $request_id values observed across the eight captured requests. Explicitly check requests 1–2 and 7–8 each retain equal incoming SAME-VALUE while producing different native IDs within each pair. Absent headers may be logged as empty string or NGINX's '-' absence marker. matching_generated_id_requests lists all OTHER captured request numbers sharing the native value and is authoritative; omit the redundant boolean.

Decision precedence: incomplete or ambiguous capture, configuration mismatch or unresolved checks => NOT_EVALUABLE. With complete evidence, actual substitution/conflation of incoming and native IDs => FORWARDED_AND_GENERATED_IDS_CONFLATED. Otherwise repeated incoming IDs accompanied by repeated native IDs => PRODUCER_CONTRACT_CONTRADICTED. Describe the observed violation without claiming copying caused it rather than random collision. All checks pass => PRODUCER_CONTRACT_SUPPORTED. Unexpected duplicate IDs outside repeated-input pairs or other unresolved mismatches => NOT_EVALUABLE. Generic normalized field names alone do not establish conflation.

Freeze this protocol and an execution lock containing baseline, protocol, implementation, test, schema, effective configuration, resource and original tracked-file hashes before any HTTP request. Record resolved image identity/version and effective configuration before requests. Refuse output-directory overwrite. Preserve unexpected outcomes without retrying into a pass. A failed campaign is retained; this run never resumes requests.

After capture, compare the current HTTP client, NGINX configuration, action/target adapters, matcher and relevant schema. Keep source-config provenance, raw retention and normalized semantics distinct. Do not rescore historical scenarios. Preserve all tracked baseline files, including strong-link v1–v4. Validate result schema, manifest and preservation inventory. Report only 'no duplicate native $request_id values observed across the eight captured requests' when that check passes.
