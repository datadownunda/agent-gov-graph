# Provenance-gate design falsification — result

**PROVENANCE_RULE_NOT_DEMONSTRATED. Do not change production v2 on this result.**

[Preregistered P1](PROTOCOL.md) was committed at `acee5bd` before the assessment ledger and scoring were created. [Exact edge ledger and results](RESULTS.json); [offline assessment](assess.py). Baseline `32500dc0725bc759f58810e273321f88220f1ac6`. Prior audit outcomes were already known; this is not a blinded or novel empirical experiment. No producer was run, no original evidence was edited, and no facts were injected into an M7 receipt. The canonical roadmap is unchanged.

## Proposed rule, unchanged after registration

For every existing supporting linkage edge require: episode-specific producer identity; source-bound observation role; established generated/received/forwarded origin; producer-defined relationship semantics; retained evidence tying the producer/configuration/code contract to the episode; explicit custody/trust assumptions; and completed bounded contradiction review with no unresolved contradictory evidence. Require all existing scope, integrity, effect and correlation prerequisites as well. No new links or alternative matching are constructed.

The rule accepts any evidence representation that establishes those premises. It does not require per-record AGG namespace fields, but it also does not accept self-authenticating declarations. Product names, field syntax, equal identifiers, tuple similarity, compatible outputs and source co-location in a Git commit do not establish contract applicability. Trusting faithful records is distinct from assuming a missing executed-code binding.

## Results and rates

| Cohort | Original exception findings | Current v2 exceptions | P1 design exception candidates | P1 ineligible |
|---|---:|---:|---:|---:|
| Retained live 168-byte case | 1/1 (100%, v1) | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) |
| Historical legitimate exceptions | 12/12 (100%) | 0/12 (0%) | 0/12 (0%) | 12/12 (100%) |
| Historical false substantive exceptions | 18/18 (100%) | 0/18 (0%) | 0/18 (0%) | 18/18 (100%) |
| Other false links: copied/different | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 3/3 (100%) |

Historical cohorts are four, six and one scenario variants respectively, each in three presentations, not independent replications. The two required edges per selected case produce 68 assessed edges across 34 cases, including the live case. Zero edges qualify. All 21 historical false accepted M6 links are covered by the selected corpus. They remain M6 links: P1 only assesses proposed assurance eligibility, and does not repair, delete or rerun matching.

The safety half of the success criterion is met (zero false substantive exceptions restored), but the live restoration half fails. The conjunction is not supported. Zero true and false exception acceptance is abstention, not improved discrimination. Exception precision is undefined because there are zero positive predictions. Selecting real-versus-synthetic provenance would in any event not prove discrimination among genuine enterprise records with misleading identifiers.

## Per-edge classification and exact basis

### Live case

| Edge | Namespace evidence classification | Supported basis | Essential missing premise | P1 result |
|---|---|---|---|---|
| Governance → execution, action_attempt_id | NAMESPACE_ESTABLISHED_ONLY_BY_EXTERNAL_PRODUCER_CONTRACT | Original runtime code generates one UUID, supplies it to policy/governance and the executor; original client records the argument. Original governance/OPA/runtime/execution records retain the value | No retained execution/deployment receipt binds the runtime/client actually executing this episode to that source contract | Ineligible: origin and semantics CONTRACT_ONLY; episode applicability MISSING |
| Execution → target, request_id | NAMESPACE_ESTABLISHED_ONLY_BY_EXTERNAL_PRODUCER_CONTRACT for full edge; target occurrence has conditional native configuration provenance | Archived NGINX config puts $request_id in native log and response header; original client reads X-Request-ID. Image/config metadata and the native access record are retained | Client implementation applicability is unbound; original raw response-header transcript is absent. Target configuration/image evidence is a partial basis, not a complete client-to-server binding | Ineligible: origin and semantics CONTRACT_ONLY; episode applicability MISSING |

Attempt: `b2f8d489-4e70-4a7b-a703-75d5291b9552`. Request: `e83c73681f3012feb2875363cce218f5`. Occurrences: governance.jsonl:2, opa.jsonl:2, runtime.jsonl:7–12, execution.jsonl:2, native/access.jsonl:2 in `experiments/target_outcome/results/v1`. The original config lines 7 and 18 bind the NGINX variable to logging and the outgoing header. The original `src/complaint_runtime.py` and `experiments/target_outcome/http_client.py` at `7da026265b75b36ebd7e3e41eb88788e6815f48d` are unchanged today. The later capture-runner changes are audit error typing, not capture behavior. None of this supplies an executed-source revision binding absent from the 15-file native manifest.

The current production receipt remains VERIFIED, M6 remains CONTRADICTION and SINGLE_ACTION scope passes. Current M7 returns CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED with NATIVE_IDENTIFIER_NAMESPACE_NOT_ESTABLISHED. P1 changes the diagnosed missing premise from declaration format to unestablished episode applicability; it does not restore the exception.

A contract-backed manual interpretation remains possible under an additional assumption that the preserved implementation actually ran. That is exactly the assumption P1 forbids using to replace an applicability requirement. Counting it as a pass after seeing the result would change the frozen rule. No conditional restored exception was scored.

### Historical cohorts

Both required edges have NAMESPACE_ESTABLISHED_ONLY_BY_AGG_DECLARATION **as simulated relationships**. The stronger native runtime/server provenance claim is NAMESPACE_NOT_ESTABLISHED. Actual fixture authorship is established and explicitly contradicts interpreting these as native runtime/server occurrences.

| Evaluation IDs | Scenario | Affected edge(s) / outcome |
|---|---|---|
| 003–005 | controls/deny_effect | Both proposed supporting edges ineligible; legitimate exception not restored |
| 042–044 | retry/governed | Both ineligible; legitimate exception not restored |
| 051–053 | fanout/governed | Both ineligible; legitimate exception not restored |
| 069–071 | parent/governed | Both ineligible; legitimate exception not restored |
| 012–014 | reuse/replacement | False governance→execution edge ineligible; no false exception restored |
| 015–017 | reuse/period | False execution→target edge ineligible; no new lifetime rule inferred |
| 021–023 | namespace/pooled | False execution→target edge ineligible; supplied conflicting namespace observations also retained |
| 024–026 | namespace/missing | False execution→target edge ineligible; missing namespace not supplied |
| 033–035 | copied/removed | False execution→target edge ineligible; no false exception restored |
| 060–062 | fanin/withheld | False execution→target edge ineligible; no false exception restored |
| 027–029 | copied/different | False execution→target edge ineligible; existing wrong-resource effect check already prevented exceptions |

Exact occurrence locations and correlation references for every edge are in RESULTS.json. Basis: original/paired decision inputs, original manifest provenance DETERMINISTIC_SYNTHETIC_FIXTURE_NO_TARGET_PROCESS, the retained generator/worker, and unchanged namespace_observations. The generator copies deterministic UUIDs and request literals; the worker writes the target-shaped rows. Native product documentation and later conformance cannot convert them into real producer evidence. Ground-truth labels are used only for cohort scoring, never as a qualification premise.

## Trust and applicability

P1 permits explicit trust in operator custody, faithful preserved records, normally functioning producers and the bounded supplied population. These do not provide external authentication or complete enterprise coverage. M6's local single-operator context remains disclosed; P1 does not recast it as independent enterprise custody.

No new factual assumption about executed runtime/client code, actual server configuration, identifier non-reuse or hidden records is introduced to obtain a pass. A source version present in the same repository is a candidate contract; an operational record tying it to the relevant episode is the missing evidence. No mandatory AGG record schema or cryptographic attestation is imposed. Ordinary retained deployment/execution records could potentially supply that association in a future eligible package, but none is acquired or manufactured here.

Later documentation explains general producer semantics only, and no later conformance record is used as original-episode evidence. Received and generated copies remain distinct observation roles, not independent producers. Producer namespace alone does not prove uniqueness, action scope, correct matching, clock applicability or channel completeness.

## Recommendation

Keep production v2 unchanged. This specific P1 rule did not meet its live-restoration requirement; it is not evidence that all provenance-based designs are impossible. Representation-neutral provenance remains a reasonable design direction, but this corpus does not yet justify a production change or a restored current-exception claim.

Maintain CURRENT_EXCEPTION_CAPABILITY_NOT_DEMONSTRATED for the tested current pipeline. Preserve the original v1 live exception and M6 contradiction at their recorded scope. Do not relabel the 12 synthetic exceptions as native successes, weaken applicability, or infer improved discrimination from zero outputs. Any changed trust boundary/rule requires owner review and a separately frozen test. No new capture, synthetic deployment, telemetry, schema change or roadmap change follows from this result.
