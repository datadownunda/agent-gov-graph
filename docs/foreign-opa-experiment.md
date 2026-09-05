# Foreign OPA evidence correlation experiment

## Scope and demonstrated boundary

Agent Gov Graph can consume separately persisted native OPA console decision
logs and correlate them with a separately recorded synthetic request journal
without a shared correlation identifier. The standalone producer is experiment
instrumentation, not the Agent Gov Graph consumer: it imports no `src` modules,
does not inspect OPA output, and does not invoke the existing governance runtime.

The producer records each request before starting OPA. The operator opens the
native evidence destination; the producer and Docker/OPA inherit that stderr
descriptor. OPA uses `decision_logs.console: true` through the CLI setting
`--set=decision_logs.console=true`. Native output is not parsed or rewritten on
this custody path. Stdout decision results are discarded.

The consumer runs after production completes and only opens evidence for reading.
It does not invoke OPA. Production and consumption use separate processes; the
automated integration test launches the producer in Python isolated mode outside
the repository working directory. This is a process/persistence separation, not
an independently administered trust domain.

## Run locally

Use the existing Python environment and Docker OPA image. From the repository
root, choose a new external evidence directory (the example uses `/tmp`):

```sh
mkdir /tmp/foreign-opa-example
python -I -B experiments/foreign_opa/produce.py \
  --policy-dir "$PWD/policies" \
  --journal /tmp/foreign-opa-example/requests.jsonl \
  --count 3 --interval-seconds 0 \
  2> /tmp/foreign-opa-example/native-opa.jsonl
chmod a-w /tmp/foreign-opa-example/*.jsonl
.venv/bin/python -B -m src.evidence_correlation \
  --opa-log /tmp/foreign-opa-example/native-opa.jsonl \
  --journal /tmp/foreign-opa-example/requests.jsonl \
  --window-seconds 2 > /tmp/foreign-opa-findings.json
```

Use a fresh directory for each run; shell redirection otherwise truncates an
existing native log. The journal uses exclusive creation. If Docker fails, a
journal observation may exist without decision evidence; do not treat it as a
completed evaluation. Console diagnostics are retained in the original file.

`chmod` protects against accidental writes, not a user who can change permissions.
For an enforced consumer boundary, supply these files through a read-only mount
or a separate read-only account. No collector service is required by this increment.

The producer intentionally repeats identical requests. A one-request run is the
isolated baseline; `--interval-seconds 5` separates repetitions for a two-second
window under normal local timing. Container startup is included between request
observation and OPA decision time. A two-second window is an experimental parameter,
not a calibrated production bound. Inspect actual deltas and vary the window;
do not silently enlarge it until the desired matches appear.

## Evidence representation

`src/foreign_opa_evidence.py` selects JSON objects with native type
`openpolicyagent.org/decision_logs`. Valid non-decision console records are ignored.
Unparseable nonblank lines are emitted as defects because their type cannot be
established. Missing/invalid correlation fields also produce defects. This is
validation of the correlation projection, not a complete OPA decision-log schema.

Each emitted envelope retains the parsed original record, absolute source path,
whole-file SHA-256, one-based line number, zero-based byte offset, byte length,
raw-line SHA-256, and canonical JSON content digest where possible. Raw bytes
remain in the original file. The original OPA `timestamp` becomes `observed_at`;
ingestion time is separately recorded as `ingested_at`. The console `time` field
and filesystem times are not substitutes for decision time.

These hashes identify content. They do not authenticate who wrote it or prove
integrity before ingestion. File references describe a completed snapshot: repeat
ingestion of the same path/content yields the same references despite a different
ingestion timestamp. Correlation deduplicates those references. Identical records
at different line locations remain distinct observations and can be ambiguous.
Moving a file or appending to it creates a different snapshot identity; this is
not an incremental tailer or cross-copy deduplication system. Conflicting projected
content supplied under one evidence reference is rejected rather than arbitrarily
selected.

## Correlation contract

Candidate edges require exact nonblank string equality for actor, action,
resource ID, and resource type, plus:

`abs(OPA decision timestamp - request observation timestamp) <= window`

The finite nonnegative window must be supplied explicitly. RFC3339 timezone-aware
timestamps are normalized at nanosecond precision (up to nine fractional digits).
No nearest-time choice, ordering heuristic, or iterative elimination is used.
The complete candidate graph is evaluated before any classifications are emitted:

- `MATCHED`: exactly one candidate on each side of the same edge.
- `AMBIGUOUS`: candidates exist but either endpoint has multiple candidates.
- `UNMATCHED`: no candidate exists.
- `EVIDENCE_DEFECT`: invalid required fields or timestamp, or malformed evidence.

Every observation receives a result. IDs and locations only address evidence,
deduplicate repeated ingestion, and stabilize presentation. `action_attempt_id`,
OPA `decision_id`, trace IDs, sequence, policy decisions, filenames, ingestion
time, and other metadata never create, rank, or break ties between candidates.
An actor/resource discrepancy is therefore an unmatched observation, not proof
of a transcription mismatch.

The implementation uses an explicit all-pairs scan suitable for this small
experiment. It does not introduce a database or change runtime reconciliation,
execution schemas, Neo4j, or control-effectiveness classification.

## Tests and independent scoring

```sh
.venv/bin/python -B -m pytest -p no:cacheprovider \
  tests/test_evidence_correlation.py tests/test_foreign_opa_evidence.py \
  tests/test_foreign_opa_experiment.py tests/test_evidence_digest.py -q
RUN_FOREIGN_OPA=1 .venv/bin/python -B -m pytest -p no:cacheprovider \
  tests/test_foreign_opa_experiment.py -q
```

The real OPA test is opt-in because it requires Docker access. It produces two
requests in a separate process, closes the files, makes them read-only, and then
ingests them. Its explicit 60-second window accommodates container startup and
tests ambiguity/custody; it is not evidence that a 60-second production window
is appropriate. A single pair subset checks the adapter-to-matcher path; the
full repeated workload must remain ambiguous.

`score_links(findings, true_pairs)` is an evaluator-only function. Its ground
truth is a set of `(opa_evidence_ref, journal_evidence_ref)` pairs kept outside
the correlator. Establish truth from controlled experiment observations, not
from the matcher's own choices. Neither `correlate` nor the consumer CLI accepts
ground truth. The scorer counts accepted links once, from the OPA side, and reports:

- correct and false accepted links;
- false accepted links / all accepted links (undefined when none are accepted);
- recovered true pairs / all supplied true pairs;
- counts of matched, ambiguous, unmatched, and defective observations across both sources.

The synthetic impostor test deliberately removes the true counterpart and leaves
a plausible unique impostor. The matcher accepts that link and the separate
ground truth scores it as false. This is an expected counterexample to treating
mutual uniqueness as proof of identity. Synthetic unit tests also cover window
boundaries, clock offsets, malformed fields, repeated actions, asymmetrical
candidate sets, shuffled order, and identifier randomization.

## What remains unproven

The policy, identities, workload, request observer, and test truth are self-authored.
Both records still describe the same submitted request, and identity fields are
cooperatively supplied. OPA does not independently authenticate those actors.
The native log is genuinely emitted by OPA, but the journal is our instrumentation.
There is no independent organization, tamper-resistant collector, real agent, or
resource execution observer in this increment.

An unmatched request does not prove missing governance; logs may be incomplete,
late, or outside the window. A matched request does not prove execution or correct
enforcement. A unique candidate does not guarantee a true pair.

Evidence against the approach includes false accepted links under independent
truth (already demonstrated by the impostor test), unacceptable ambiguity under
realistic repetition, true pairs outside the declared window, clock skew or
identity inconsistencies, or results changing when only irrelevant IDs/order
change. Writes by the consumer into source evidence or dependence on a shared
identifier would falsify the stated implementation boundary itself.

This increment stops at foreign evidence correlation. It does not advance the
real-agent milestone or establish production accuracy thresholds.

## Reliability benchmark

The subsequent [controlled benchmark](../experiments/foreign_opa/BENCHMARK.md)
characterizes the unchanged matcher using synthetic observations. Its
[107-scenario results](../experiments/foreign_opa/results/reliability-v1/README.md)
cover repetition, timestamp separation, clock skew, missing counterparts, and
plausible impostors, with evaluator ground truth kept outside the matcher.
These results are algorithm experiments, not new native-log custody evidence.
