# Correlation as an evidentiary assertion

`src/correlation_assertion.py` emits versioned review records validated against
`schemas/correlation_assertion.schema.json`. This is an additive layer: the
deterministic matcher, ingestion, benchmark generators, and saved benchmark results
are unchanged. No assertions feed control-effectiveness or execution findings.

## Meaning

Three concepts are separate:

- **Relationship type:** the proposition under review, such as
  `REQUEST_DECISION_ASSOCIATION` or `SAME_POLICY_EVALUATION`. This names a proposed
  relationship; its presence alone does not assert that the relationship holds.
- **Correlation method:** `EXACT_COMPOSITE_LINKAGE` or `NATIVE_IDENTIFIER_LINKAGE`.
- **Result:** `LINKED`, `AMBIGUOUS`, `UNMATCHED`, `CONTRADICTED`, or
  `INSUFFICIENT_EVIDENCE`. Results are categorical, with no confidence scores.

`LINKED` means the declared rule supports linkage within its supplied population
and assumptions. It is not a claim of proven causal identity. The reliability
benchmarks demonstrate why that distinction matters.

`AMBIGUOUS` means either endpoint has competing candidates. The assertion retains
all forward candidates and each candidate's reverse candidate references, so a
many-to-one conflict remains visible even when the focus has only one candidate.

`UNMATCHED` means no eligible counterpart was found in the supplied snapshot. It
does not mean no counterpart exists, or that the proposed relationship is false.

`CONTRADICTED` is emitted by the native method when a mutually unique identifier
candidate violates a caller-declared required equality invariant. For example,
the same native decision ID with conflicting actor values can contradict the
declared same-evaluation rule. The conflict records both values. It does not
establish which source is correct. Known conflicts take precedence over missing
additional invariants; both conflicts and defects remain recorded.

`INSUFFICIENT_EVIDENCE` means required evidence is absent or malformed. Composite
`EVIDENCE_DEFECT` results map here. Missing native identifiers or required native
invariants also map here. Missing evidence is not converted into contradiction.

## Assertion contents

Every assertion records:

| Field | Review purpose |
|---|---|
| `schema_version`, `assertion_id` | Format version and canonical SHA-256 identity of the assertion body |
| `relationship_type`, `correlation_method` | Proposed relationship and supporting method |
| `focus` | Source-qualified observation being assessed |
| `source_evidence` | Supplied references, envelope content digests, source locations when available, and actual observed signal values |
| `signals_used` | Field paths, operators, and whether each is used to select candidates or check an invariant |
| `candidate_population` | Counts and references for both supplied sources, plus snapshot digest |
| `competing_candidates` | Eligible counterparts and their reverse candidates |
| `result` | State, reason, linked counterpart if any, defects, and explicit conflicts |
| `evidence_coverage` | Declared completeness, its basis, and optional declared interval |
| `time_assumptions` | Time field/window, inclusive boundary, clock verification status, and applied offset |
| `rule` | Named rule/version, adapter version, and parameters |
| `limitations` | Conditions and unsupported interpretations |
| `method_output` | Original method finding, retained for audit |

Evidence references are always qualified by source: identical strings on opposite
sides are not merged. Repeated ingestion of the same reference/content is
deduplicated. Conflicting content under one source reference is rejected.
`ingested_at` is omitted from the hashed envelope so a later ingestion does not
change an otherwise identical assertion. Original file/line/byte locations are
retained when present. Signal values remain available even for rejected candidates
through the supplied population's evidence manifest.

Each assertion includes its complete supplied population for portable review.
This duplicates manifests and is intended for the current small snapshots, not
a large-scale evidence store. Missing locations stay null; no custody information
is invented. Digests identify supplied content, not authenticity or completeness.

## Existing exact-composite method

```python
from src.correlation_assertion import composite_assertions

assertions = composite_assertions(opa_records, journal_records, window_seconds=2)
```

This calls the existing `correlate()` unchanged: exact actor, action, resource ID,
resource type, and an explicit inclusive timestamp window, with mutual uniqueness.
The original finding is preserved as `method_output`. Composite field/time
disagreement remains `UNMATCHED`; there is no independent linkage on which to
base a contradiction.

The wrapper records comparable decision/request clocks as an unverified
assumption. It applies no clock correction and does not claim measured skew.
Coverage defaults to `UNKNOWN`. A caller can declare `PARTIAL` or
`COMPLETE_FOR_DECLARED_SCOPE` with a nonblank basis and interval fields; this is
not automatically verified and does not change the matcher result. Scope remains
`SUPPLIED_SNAPSHOT_ONLY` even when the caller declares completeness.

For existing foreign files, a separate CLI emits assertions without changing the
existing matcher CLI:

```sh
.venv/bin/python -B -m src.correlation_assertion \
  --opa-log /tmp/foreign-opa-example/native-opa.jsonl \
  --journal /tmp/foreign-opa-example/requests.jsonl \
  --window-seconds 2 > /tmp/correlation-assertions.json
```

## Native identifier method

```python
from src.correlation_assertion import native_assertions

assertions = native_assertions(
    left_records, right_records,
    identifier_field="decision_id",
    namespace="opa.example/instance-a",
    issuer="OPA instance A, as declared by the evidence provider",
    required_equal_fields=("actor", "action"),
)
```

The caller explicitly declares a pre-existing source-native identifier path,
common namespace, and issuer. Dotted paths such as `raw_record.decision_id` are
supported when both records retain that path. Namespace and non-reuse are
assumptions requiring review, not properties inferred from equal strings. The
method never generates identifiers or adds them to source evidence. It must not
be used to relabel an experiment-generated shared key as native evidence.

Equal native identifiers create candidates; only mutually unique candidates can
support linkage. Explicit equality invariants are checked after selection and
cannot be used to choose between duplicate identifier candidates. No timestamp
window applies to this method; this is recorded explicitly. Unknown namespace,
issuer, or field declarations are rejected rather than silently inferred.

This method does not participate in or alter the identifier-free reliability
benchmarks. It supports review of a different evidentiary method when genuine
native identifiers are available. Equal IDs can still be copied, reused, or
misrecorded, so linkage remains conditional.

## Validation and examples

`validate_assertion()` checks schema shape, required context, allowed method/result
states, source-reference resolution, population counts, and snapshot/assertion
digests. Unknown top-level fields (including confidence scores) are rejected.
These checks establish record consistency, not truth of caller declarations.

`schemas/correlation_assertion.examples.json` contains complete examples of both
linkage methods and all non-linkage states. Generate a new assertion after any
evidence or rule change; do not reuse its prior content identity.

```sh
.venv/bin/python -B -m pytest -p no:cacheprovider tests/test_correlation_assertion.py
```

The adapter emits one assertion per supplied focus observation, as the existing
matcher does. Two linked endpoints therefore produce two review assertions about
the same pair; they are not two independent confirmations. Empty input yields
no assertions. No runtime reconciliation, execution schema, Neo4j projection, or
control-effectiveness integration is added.
