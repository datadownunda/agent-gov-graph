"""Measurement-only exact-feature variants; no production matcher changes."""

import argparse
import csv
import gzip
import hashlib
import json
import random
import subprocess
import sys
from itertools import combinations
from pathlib import Path

from experiments.foreign_opa.benchmark import ROOT, SECOND, _timestamp, evaluate, scenarios
from src.evidence_correlation import correlate


POOLS = {
    "client_app": ("hr-portal", "case-review", "compliance-export", "support-console"),
    "source_ip": ("192.0.2.10", "192.0.2.11", "192.0.2.12", "192.0.2.13"),
    "request_parameters": ("view=summary&locale=en", "view=full&locale=en",
                           "view=summary&locale=fr", "view=full&locale=fr"),
    "resource_version": ("revision-7", "revision-8", "revision-9"),
}
FEATURES = tuple(POOLS)
FEATURE_SETS = {
    "baseline": (),
    **{feature: (feature,) for feature in FEATURES},
    "client+ip": ("client_app", "source_ip"),
    "parameters+version": ("request_parameters", "resource_version"),
    "all-four": FEATURES,
}
for size in (2, 3):
    for fields in combinations(FEATURES, size):
        if fields not in FEATURE_SETS.values():
            FEATURE_SETS["+".join(fields)] = fields
PROFILES = ("varied", "same_context", "colliding_impostors", "missing25", "disagree25")


def build_case(name, *, profile, groups=20, repetitions=1, separation_ns=5 * SECOND,
               skew_ns=0, missing_fraction=0, missing_side="journal",
               impostor_fraction=0, seed=20260905):
    """Generate observations from latent actions, never from an evaluator manifest.

    Baseline RNG operations are preserved exactly. A separate RNG samples ordinary
    context from small reusable pools, not from sequence, time, refs, or truth.
    """
    if profile not in PROFILES:
        raise ValueError("unknown profile")
    rng = random.Random(f"{seed}:{name}")
    context_rng = random.Random(f"ordinary-context:{seed}:{name}")
    degradation_rng = random.Random(f"source-quality:{seed}:{name}")
    used_refs = set()

    def fresh_ref():
        while True:
            ref = f"{rng.getrandbits(128):032x}"
            if ref not in used_refs:
                used_refs.add(ref)
                return ref

    def context():
        return {field: values[0] if profile == "same_context" else context_rng.choice(values)
                for field, values in POOLS.items()}

    opa, journal, true_pairs = [], [], []
    for group in range(groups):
        for occurrence in range(repetitions):
            instant = occurrence * separation_ns
            ordinary = context()
            fields = {"actor": f"synthetic-actor-{group}", "action": "read",
                      "resource_id": "complaint-456", "resource_type": "employee_complaint"}
            # Two synthetic observers see the latent action's context. This ideal
            # agreement assumption is explicitly relaxed by source-quality profiles.
            left = {**fields, **ordinary, "evidence_ref": fresh_ref(),
                    "observed_at": _timestamp(instant + skew_ns)}
            right = {**fields, **ordinary, "evidence_ref": fresh_ref(),
                     "observed_at": _timestamp(instant)}
            opa.append(left)
            journal.append(right)
            true_pairs.append((left["evidence_ref"], right["evidence_ref"]))
    count = len(true_pairs)
    positions = list(range(count))
    rng.shuffle(positions)
    removed_positions = set(positions[:int(count * missing_fraction)])
    injected_positions = positions[:int(count * impostor_fraction)]
    affected = opa if missing_side == "opa" else journal
    impostors = []
    for position in injected_positions:
        original = affected[position]
        ordinary = ({field: original[field] for field in FEATURES}
                    if profile == "colliding_impostors" else context())
        impostors.append({**original, **ordinary, "evidence_ref": fresh_ref()})
    removed_refs = {affected[i]["evidence_ref"] for i in removed_positions}
    replaced = [r for r in affected if r["evidence_ref"] not in removed_refs] + impostors
    if missing_side == "opa":
        opa = replaced
    else:
        journal = replaced
    rng.shuffle(opa)
    rng.shuffle(journal)
    for record in journal:
        for field, values in POOLS.items():
            if degradation_rng.random() < 0.25:
                if profile == "missing25":
                    del record[field]
                elif profile == "disagree25":
                    record[field] = degradation_rng.choice([v for v in values if v != record[field]])
    present_left = {r["evidence_ref"] for r in opa}
    present_right = {r["evidence_ref"] for r in journal}
    truth = {"true_pairs": true_pairs,
             "observable_true_pairs": [(a, b) for a, b in true_pairs
                                       if a in present_left and b in present_right],
             "removed_refs": sorted(removed_refs),
             "impostor_refs": sorted(r["evidence_ref"] for r in impostors)}
    return {"opa": opa, "journal": journal, "window_seconds": 2}, truth


def match_features(inputs, features):
    """Exact conjunctive requirements before unchanged mutual-uniqueness matching.

    Partitioning by equal extra values is equivalent to adding equality predicates
    to candidate edges. No weights, confidence, nearest-time choice, or fallback.
    """
    if any(feature not in FEATURES for feature in features):
        raise ValueError("only the declared ordinary features may be used")
    if not features:
        return correlate(inputs["opa"], inputs["journal"], window_seconds=inputs["window_seconds"])
    buckets = {}
    missing = {"opa": [], "journal": []}
    for side in ("opa", "journal"):
        for record in inputs[side]:
            if any(not isinstance(record.get(f), str) or not record[f].strip() for f in features):
                missing[side].append(record)
                continue
            key = tuple(record[f] for f in features)
            buckets.setdefault(key, {"opa": [], "journal": []})[side].append(record)
    findings = []
    for records in buckets.values():
        findings.extend(correlate(records["opa"], records["journal"],
                                  window_seconds=inputs["window_seconds"]))
    for side in ("opa", "journal"):
        findings.extend(correlate(missing[side] if side == "opa" else [],
                                  missing[side] if side == "journal" else [],
                                  window_seconds=inputs["window_seconds"]))
    return sorted(findings, key=lambda r: (0 if r["source"] == "opa" else 1, r["evidence_ref"]))


def write_json(path, value):
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def read_json(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def report(output, rows):
    lines = ["# Ordinary evidence feature benchmark", "",
             f"{len(rows):,} measurements: 107 existing scenarios × 5 evidence profiles × {len(FEATURE_SETS)} feature sets.",
             "20 actor groups per scenario, fixed two-second window, fixed seed. Baseline code and results are preserved.", "",
             "## False-link-first screen", "",
             "Counts below sum the deliberately selected stress scenarios, not a production distribution.",
             "A zero-false-link feature set must also accept at least one correct link to qualify.", "",
             "| Profile | Feature set | False accepted links | Scenarios with false links | Correct accepted links |",
             "|---|---|---:|---:|---:|"]
    for profile in PROFILES:
        for feature_set in FEATURE_SETS:
            selected = [r for r in rows if r["profile"] == profile and r["feature_set"] == feature_set]
            lines.append(f"| {profile} | {feature_set} | {sum(r['false_accepted_links'] for r in selected)} | "
                         f"{sum(r['false_accepted_links'] > 0 for r in selected)} | "
                         f"{sum(r['correct_accepted_links'] for r in selected)} |")
    lines += ["", "## Representative outcomes", "",
              "P = precision; R = end-to-end recall; A/U = ambiguous/unmatched observation rates. — means undefined.",
              "", "| Profile | Workload | Features | P | R | False links | A | U |",
              "|---|---|---|---:|---:|---:|---:|---:|"]
    probes = {"density-r5-gap5000000000-skew5000000000": "clock alias",
              "loss-journal-missing1-impostors1": "full replacement",
              "density-r5-gap0-skew0": "repetition",
              "loss-journal-missing0.5-impostors0": "50% loss"}
    def pct(value):
        return "—" if value is None else f"{value:.1%}"
    for r in rows:
        if r["scenario"] in probes and r["feature_set"] in ("baseline", "all-four"):
            lines.append(f"| {r['profile']} | {probes[r['scenario']]} | {r['feature_set']} | "
                         f"{pct(r['precision'])} | {pct(r['recall'])} | {r['false_accepted_links']} | "
                         f"{pct(r['ambiguity_rate'])} | {pct(r['unmatched_rate'])} |")
    lines += ["", "## Minimum sufficient set", ""]
    for profile in PROFILES:
        qualifying = []
        for label, fields in FEATURE_SETS.items():
            subset = [r for r in rows if r["profile"] == profile and r["feature_set"] == label]
            if sum(r["false_accepted_links"] for r in subset) == 0 and sum(r["correct_accepted_links"] for r in subset) > 0:
                qualifying.append((len(fields), label))
        if qualifying:
            size = min(n for n, _ in qualifying)
            lines.append(f"- {profile}: smallest tested qualifying sets: " + ", ".join(label for n, label in qualifying if n == size) + ". This is conditional on this finite workload.")
        else:
            lines.append(f"- {profile}: no tested feature set eliminates false accepted links across the sweep.")
    lines += ["", "No sufficient ordinary feature set is established across all profiles. Identical ordinary observations can belong to different actions. More exact fields can reduce collisions, but cannot prove identity when missing counterparts have observationally identical replacements.",
              "Stronger evidence or explicit abstention assumptions are needed for a zero-silent-error claim. This does not establish that ML/probabilistic matching is necessary or that it can solve indistinguishability.",
              "", "See [every metric row](metrics.csv), [results and hashes](results.json), and [methodology](../../FEATURE_BENCHMARK.md).",
              "Compressed matcher inputs, raw findings, and evaluator-only truth are retained alongside the report. These are synthetic contextual observations; enterprise availability, independence, and normalization have not been validated.", ""]
    (output / "README.md").write_text("\n".join(lines))


def benchmark(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    protected = [ROOT / "src/evidence_correlation.py", ROOT / "src/foreign_opa_evidence.py",
                 ROOT / "experiments/foreign_opa/benchmark.py"]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    cases, truths = {}, {}
    for profile in PROFILES:
        for name, options in scenarios():
            cases[f"{profile}/{name}"], truths[f"{profile}/{name}"] = build_case(name, profile=profile, **options)
    write_json(output / "matcher-inputs.json.gz", cases)
    subprocess.run([sys.executable, "-B", "-m", "experiments.foreign_opa.feature_benchmark",
                    "--worker", str(output)], cwd=ROOT, check=True)
    findings = read_json(output / "findings.json.gz")
    rows = []
    # Baseline findings must equal the pre-existing saved baseline, not just rates.
    baseline_findings = json.loads((ROOT / "experiments/foreign_opa/results/reliability-v1/findings.json").read_text())
    for case, variants in findings.items():
        profile, name = case.split("/", 1)
        if variants["baseline"] != baseline_findings[name]:
            raise AssertionError("baseline findings changed")
        for label, result in variants.items():
            rows.append({"profile": profile, "scenario": name, "feature_set": label,
                         **evaluate(result, truths[case])})
    for path in protected:
        if hashlib.sha256(path.read_bytes()).hexdigest() != hashes[str(path.relative_to(ROOT))]:
            raise AssertionError("protected baseline changed")
    write_json(output / "ground-truth.json.gz", truths)
    write_json(output / "results.json", {"metadata": {"baseline_hashes": hashes,
               "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "input_sha256": hashlib.sha256((output / "matcher-inputs.json.gz").read_bytes()).hexdigest(),
               "groups": 20, "seed": 20260905, "profiles": PROFILES, "feature_sets": FEATURE_SETS,
               "window_seconds": 2, "measurements": len(rows), "baseline_findings_equal": True}, "rows": rows})
    with (output / "metrics.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report(output, rows)
    print(f"Completed {len(rows)} measurements: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--output")
    choice.add_argument("--worker")
    args = parser.parse_args()
    if args.worker:
        output = Path(args.worker)
        inputs = read_json(output / "matcher-inputs.json.gz")
        write_json(output / "findings.json.gz", {
            case: {label: match_features(records, features) for label, features in FEATURE_SETS.items()}
            for case, records in inputs.items()})
    else:
        benchmark(args.output)


if __name__ == "__main__":
    main()
