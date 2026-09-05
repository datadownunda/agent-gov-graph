# Deterministic matcher reliability benchmark

The [executed results](results/reliability-v1/README.md) characterize the existing
two-second-window matcher without changing its algorithm or adding matching fields.
This benchmark generates synthetic normalized observations at the correlator API
boundary. It does not generate new native OPA logs or replace the separate real-OPA
custody-path experiment.

## Reproduce

From the repository root, choose a new output directory:

```sh
.venv/bin/python -B -m experiments.foreign_opa.benchmark \
  --output /tmp/foreign-opa-reliability-new --groups 20
.venv/bin/python -B -m pytest -p no:cacheprovider \
  tests/test_correlation_benchmark.py tests/test_evidence_correlation.py \
  tests/test_foreign_opa_evidence.py -q
```

The runner refuses to overwrite an existing output directory. It stores the
complete observations, findings, evaluator truth, CSV metrics, JSON results, and
a readable report. Fixed seed, inputs, source hashes, and Python version are
recorded for reproducibility. No Docker or extra dependencies are needed.

## Workload design

All scenarios use actor, action, resource ID/type, observation time, and opaque
source-local evidence references. References are distinct across sources. Request
ordering is shuffled deterministically. No causal labels or sequence numbers are
included in correlator input. There is no policy-result filter or scoring feature.

Each scenario contains 20 actor groups by default. Actors differ between groups;
within a group all identity fields are equal, and there are 1, 2, or 5 successive
attempts. The actor groups isolate repeated-action patterns without adding fields.
They are controlled replicas, not 20 independently sampled production workloads.

The 107 scenarios consist of:

- **75 density/skew combinations:** repetitions {1, 2, 5}, timestamp separation
  {0, 0.5s, 2s, 2s + 1ns, 5s}, and OPA clock offset {-5s, -2s, 0, +2s, +5s}.
- **4 boundary probes:** isolated pairs with offset ±2s and ±(2s + 1ns).
- **24 evidence-loss/impostor combinations:** remove {0%, 25%, 50%, 100%} of
  one source, inject {0%, 50%, 100%} impostors on that source, and test both source
  directions. Fractions apply to the original number of attempts.
- **4 combined stressors:** five repetitions at five-second separation, 50% loss
  plus 50% replacement impostors, zero/five-second skew, in both source directions.

Removals use a seeded shuffled selection. Injections use the same selection order:
equal loss/injection fractions replace the missing counterparts. With injection
exceeding loss, some impostors compete with intact true counterparts. Impostors
have the same observed identity and timestamp as the corresponding original
record, but represent a different synthetic action according to evaluator truth.
This deliberately tests observational indistinguishability, not an empirical
estimate of how often such collisions occur. All generated fields are valid;
malformed ingestion is covered by the earlier tests, not this reliability sweep.

The model uses a constant source clock offset and zero evaluation latency.
It does not sample clock drift, jitter, latency distributions, burst distributions,
or simultaneous loss of both sources. Some grid cells are deliberately redundant
(e.g. separation has no effect with one attempt). Do not pool them into a claimed
production score. Fractions are rounded down to whole records for custom group
counts; actual removed/injected counts are included in every metric row.

## Ground truth and denominators

The generator keeps original causal pairs separately from observed records.
The benchmark launches a separate worker with only observations and the window.
The truth file is written after that worker exits. Scoring runs in the parent,
after matching; it never supplies truth to the correlator. This is interface and
process isolation, not a hostile-process security boundary.

- Precision: correct accepted links / accepted links.
- Recall: correct accepted links / all originally planned true pairs, including
  those whose counterparts were removed (end-to-end pair recovery).
- Observable recall: correct accepted links / true pairs whose two original
  records are both present (correlation performance conditional on availability).
- False accepted links: count of accepted pairs not in ground truth.
- False-link rate: false accepted links / accepted links.
- Ambiguity/unmatched rate: observations in that state / all supplied observations
  across both sources. Links are counted once; observations are counted per source.

Undefined ratios are JSON null / blank CSV / an em dash in the report. In
particular, abstaining on everything does not get assigned 100% precision. No
true-negative accuracy is used: its denominator could be inflated with irrelevant
cross-pairs. Counts, including defects, accompany rates.

## Interpretation and stopping point

Correct matches in separated complete workloads show that the implementation
works under its assumptions. Dense repetition shows its abstention boundary.
Clock aliasing and replacement impostors falsify any interpretation of mutual
uniqueness as proof of common identity: both can create false accepted links
with no ambiguity warning. Evidence loss separately limits end-to-end recovery.

The results do not establish production precision, authenticity, custody,
execution, enforcement, or real-agent behavior. This increment only measures
the current deterministic algorithm. It adds no probabilistic scoring, fields,
tie-breakers, or algorithm changes.
