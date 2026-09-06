# Independent target outcome experiment (M6)

Run from the repository root using the existing Python environment and Docker:

```sh
.venv/bin/python -m experiments.target_outcome.run_experiment run experiments/target_outcome/results/v2
.venv/bin/python -m experiments.target_outcome.run_experiment audit experiments/target_outcome/results/v1
```

`run` requires a new output directory and will not overwrite existing evidence. It uses the stock NGINX image pinned in the runner, existing OPA 1.19.0 and the existing synthetic complaints. It binds only a loopback port, creates ephemeral synthetic Basic-auth credentials outside results, and stops/removes its container. No OpenAI credentials or live model calls are used.

NGINX writes `native/access.jsonl` directly. The client never accesses that file. Ingestion begins after graceful stop, preserving the complete original bytes. The manifest records a content inventory; it is self-authored and does not authenticate provenance. Only preserved portable file members appear in results; passwords, hashes, local host paths and ephemeral ports are excluded. Target usernames, image digests and synthetic resource identifiers are retained as relevant evidence.

## Preserved v1 results

The live run produced three OPA governance records, two response-side client execution records and two native NGINX access records. The two completed GETs reported 150 and 168 body bytes respectively. All three M4 bindings reconstruct from the preserved authority archive.

| Analysis | Result | Basis |
| --- | --- | --- |
| Authorized read | `CONSISTENT` | ALLOW, submitted request, client success, native completed GET/200 with 150 body bytes. |
| Critical denied read | `CONTRADICTION` | DENY, explicit test bypass submits GET, response-side native ID links to completed GET/200 with 168 bytes; client success remains null. |
| Denied request, unrestricted observation view | `INSUFFICIENT_EVIDENCE` | No accepted execution/target path and no bounded coverage declaration. |
| Denied request, bounded idle interval | `CONSISTENT` with `CONSISTENT_WITH_BLOCKING` | Neither channel has observations during the declared interval; not proof blocking occurred. |
| Critical case, execution evidence withheld from analysis | `INSUFFICIENT_EVIDENCE` | No independently established G–O link; original evidence retained. |

The critical client received the response body and native server ID before an intentionally injected finalization exception. The record preserves received bytes and `CLIENT_FINALIZATION_FAILED`; it does **not** claim no client receipt. Runtime evidence separately records EXECUTION_FAILED with unknown read outcome. The target record supplies the independently produced server claim. Missing client success is never fabricated as success.

`ground_truth.json` describes the controlled injection separately and is never read by the correlator or reconciliation derivation. `run_id` selects a governance focus for reports, not linkage candidates. All native matching assertions use complete role populations from the supplied snapshot. The bounded negative view explicitly restricts observation time; it is not a hidden matching rule.

The NGINX Basic-auth account maps to the runtime agent only through `identity_mapping.json`. The versioned mapping is an operator-authored experimental assumption, not identity attestation. The Basic-auth permission lets the HTTP target serve both complaints; OPA has the finer resource restriction. This controlled separation is why the explicit bypass can produce the prohibited representation. It is not evidence of a naturally occurring exploit.

The full derivation, source references, candidate populations, edge paths, dimension comparisons, coverage and limitations are in `reconciliation.json`. `correlations.json` preserves the unchanged native method outputs. The largest artifact deliberately repeats population references to keep each assertion reviewable; the entire v1 archive is approximately 0.5 MB.

The audit verifies file digests and byte locations, re-ingests source files, replays correlations and reconciliation, validates schemas, and reconstructs all M4 bindings. Tests additionally cover historical delegation explanations, conflicting and missing evidence, malformed source records, narrow target-effect negatives, invented/rehashed assertions, withheld evidence, duplicates and unchanged runtime gates. Those negative/delegation scenarios are fixture coverage, not live observations.

See [the M6 contract](../../docs/action-reconciliation.md) for result semantics and claim limits. Stop at reconciliation: no root-cause or control-effectiveness findings are produced.
