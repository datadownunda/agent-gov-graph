# Ordinary evidence feature measurements

See the [8,560 measured outcomes](results/ordinary-features-v2/README.md) and
[full metrics](results/ordinary-features-v2/metrics.csv). This is a measurement-only
extension: the production correlator, ingestion, original generator, and original
107-scenario results remain unchanged. Every new baseline finding is checked for
exact equality with the saved original findings.

## Question and selection rule

Which smallest subset of four ordinary fields eliminates false accepted links
while still accepting some correct links in the controlled suite? All 16 subsets
are measured, including the empty baseline. Selection prioritizes zero false
accepted links across scenarios, then field count; recall does not compensate for
false links. A qualifying subset in one synthetic profile is not a universal
minimum. No subset can distinguish actions that have identical observed values.

## Candidate evidence and plausibility

These are hypothetical observations that separate enterprise components could
record, not fields already supported by the current native OPA adapter:

| Field | Possible independent observations | Limitations |
|---|---|---|
| `client_app` | Application identity observed by a gateway/auth layer and recorded by a requesting application; optionally supplied to OPA | Identifies a reusable application, not an action; aliases and intermediary identities may disagree |
| `source_ip` | Network peer observed by a gateway and client egress recorded by another system; optionally supplied to OPA | NAT/proxies aggregate clients; the two systems must mean the same address |
| `request_parameters` | Actual request arguments recorded by requester and receiver, represented here as view/locale parameters | Ordinary content, not a generated fingerprint; repeated requests can be identical; encoding/defaults may differ |
| `resource_version` | An explicitly requested document revision recorded by caller and resource gateway; optionally supplied to OPA | Must describe the same requested revision, not request-time versus response-time versions; revisions are reused |

OPA cannot invent these observations. Any real use would require the caller or
integration to supply them and each source to retain comparable semantics. No
enterprise source integration or normalization has been implemented in this task.

The finite pools are 4 applications, 4 documentation-range IPs, 4 literal view/locale
parameter combinations, and 3 reusable revisions. There are only 192 possible
four-field combinations. Values are sampled by a separate fixed-seed generator,
not derived from event position, timestamp, filenames, record IDs, or ground truth.
No feature is intended to be unique. Revision sampling models explicit reads of
different historical revisions, not random mutation of one current document.

## Controlled profiles

Each profile reruns all 107 existing scenarios: repetition, separation, positive
and negative clock skew, missing counterparts on either source, replacement/extra
impostors, and combined stressors. All 16 feature subsets see exactly the same
observations within a case, allowing direct comparison.

- `varied`: latent actions draw independent values from the small pools; synthetic
  observers agree on those values. Impostors independently draw from the same pools.
- `same_context`: all actions and impostors share all four values. Models recurring
  identical requests from one application/egress reading the same revision.
- `colliding_impostors`: original actions vary, but impostors share every ordinary
  value of the record they shadow. Tests genuinely indistinguishable replacements.
- `missing25`: starts from varied context; each journal feature is independently
  omitted with probability 25% using a fixed seed. Requiring all four reduces
  expected journal feature completeness to about 32%. Realized metrics are reported.
- `disagree25`: starts from varied context; each journal feature independently has
  a 25% chance of being changed to another pool value. Tests semantic/source mismatch.

Feature values are synthetic and their independence/uniformity is optimistic.
Client application, IP, parameters, and revision are often correlated; the
same-context profile tests one extreme. Neither the probabilities nor this grid
are an empirical enterprise distribution. No confidence intervals or production
error rates are inferred from the 20 controlled actor groups.

## Experimental deterministic variants

The experiment partitions observations by exact equality of the selected extra
fields, then invokes the unchanged baseline matcher in each partition. This is
equivalent to adding conjunctive equality requirements to candidate edges. The
original actor/action/resource requirements, two-second inclusive window, and
mutual uniqueness rule still apply. Missing selected fields abstain as `UNMATCHED`;
there is no fallback to fewer fields, nearest timestamp, or weighted score.

Extra requirements can remove false candidates but can also remove a true candidate
whose field is inconsistent, leaving an impostor uniquely eligible. Candidate
pruning is therefore not guaranteed to reduce false accepted links. A regression
test demonstrates ambiguity turning into a false accepted link after disagreement.

The only allowed extra matching fields are the four listed above. Attempt IDs,
trace IDs, new shared identifiers, sequence, filenames, labels, and evaluator
truth are not matching features. Evidence references only address observations.

## Truth isolation and metrics

The generator creates two observations of a latent action and separately records
their causal relationship. It never reads an evaluator manifest to assign features.
That shared synthetic latent context is an assumption, not proof of independent
real-world observation. Impostor construction is controlled stimulus; its identity
as an impostor is never exposed to the matcher.

A separate worker receives only observation records/window and the configured
feature subsets. It cannot receive truth through its interface. Ground truth is
written after the worker exits and used only for scoring in the parent. Profile
and case names group experiments but do not enter `match_features`. Isolation is
logical/process separation, not an adversarial security boundary.

Per-feature/per-scenario CSV and JSON include precision, end-to-end recall,
observable recall, false accepted link count/rate, ambiguity and unmatched rates,
and denominator counts. Definitions match the original benchmark: recall includes
planned pairs lost through missing evidence; observable recall includes only
original pairs with both records present. Ambiguous/unmatched rates count observations
across both sources, and accepted links are counted once. Zero accepted links yield
undefined precision, not 100%. Summed false-link counts in the report are a stress
screen only; no average production precision is inferred.

## Reproduce and audit

```sh
.venv/bin/python -B -m experiments.foreign_opa.feature_benchmark \
  --output /tmp/ordinary-evidence-features-new
.venv/bin/python -B -m pytest -p no:cacheprovider tests/test_feature_benchmark.py
```

Choose a fresh output directory. Results retain compressed inputs, raw findings,
and evaluator truth, plus CSV, JSON, hashes, and a readable report. The first
eight-subset screening run is retained in `results/ordinary-features-v1`; the
complete all-subsets measurement is `results/ordinary-features-v2`.

## Interpretation boundary

Simple deterministic constraints are useful when fields agree and distinguish
actions. This experiment does not establish any ordinary field set that prevents
silent false links across all profiles. In particular, equality cannot resolve
observationally identical replacements for missing originals. Independent evidence
that actually distinguishes actions, justified clock/completeness assumptions, or
more conservative abstention would be needed before claiming zero silent errors.

This does not show that probabilistic/ML matching is necessary. Such a model cannot
recover absent information merely by assigning scores. No probabilistic scoring,
production matcher change, or real-agent milestone is implemented here.
