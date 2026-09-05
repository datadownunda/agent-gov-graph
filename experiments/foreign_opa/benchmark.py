"""Synthetic reliability benchmark; the production correlator is unchanged."""

import argparse
import csv
import hashlib
import json
import random
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SECOND = 1_000_000_000


def _timestamp(ns):
    seconds, fraction = divmod(ns, SECOND)
    base = datetime(2026, 9, 5, tzinfo=timezone.utc) + timedelta(seconds=seconds)
    return base.strftime("%Y-%m-%dT%H:%M:%S") + f".{fraction:09d}Z"


def build_case(name, *, groups=20, repetitions=1, separation_ns=5 * SECOND,
               skew_ns=0, missing_fraction=0, missing_side="journal",
               impostor_fraction=0, seed=20260905):
    """Return observation-only inputs and a separate evaluator manifest.

    Each group has a different actor; within a group, the four matching fields
    are identical. OPA timestamps have constant skew relative to request time.
    Impostors are distinct synthetic actions with identical observed fields/time.
    """
    if groups < 1 or repetitions < 1 or separation_ns < 0:
        raise ValueError("positive group/repetition counts and nonnegative separation required")
    if missing_side not in ("opa", "journal"):
        raise ValueError("invalid missing side")
    if not 0 <= missing_fraction <= 1 or not 0 <= impostor_fraction <= 1:
        raise ValueError("fractions must be in [0, 1]")
    rng = random.Random(f"{seed}:{name}")
    used_refs = set()

    def fresh_ref():
        while True:
            ref = f"{rng.getrandbits(128):032x}"
            if ref not in used_refs:
                used_refs.add(ref)
                return ref

    opa, journal, true_pairs = [], [], []
    for group in range(groups):
        for occurrence in range(repetitions):
            instant = occurrence * separation_ns
            fields = {"actor": f"synthetic-actor-{group}", "action": "read",
                      "resource_id": "complaint-456", "resource_type": "employee_complaint"}
            left = {**fields, "evidence_ref": fresh_ref(), "observed_at": _timestamp(instant + skew_ns)}
            right = {**fields, "evidence_ref": fresh_ref(), "observed_at": _timestamp(instant)}
            opa.append(left)
            journal.append(right)
            true_pairs.append((left["evidence_ref"], right["evidence_ref"]))
    count = len(true_pairs)
    # A fixed shuffled selection is used for both removals and injections: when
    # fractions agree, impostors replace the removed counterparts exactly.
    positions = list(range(count))
    rng.shuffle(positions)
    removed_positions = set(positions[:int(count * missing_fraction)])
    injected_positions = positions[:int(count * impostor_fraction)]
    affected = opa if missing_side == "opa" else journal
    impostors = [{**affected[i], "evidence_ref": fresh_ref()} for i in injected_positions]
    removed_refs = {affected[i]["evidence_ref"] for i in removed_positions}
    replaced = [record for record in affected if record["evidence_ref"] not in removed_refs] + impostors
    if missing_side == "opa":
        opa = replaced
    else:
        journal = replaced
    rng.shuffle(opa)
    rng.shuffle(journal)
    present_left, present_right = {r["evidence_ref"] for r in opa}, {r["evidence_ref"] for r in journal}
    observable = [(left, right) for left, right in true_pairs
                  if left in present_left and right in present_right]
    inputs = {"opa": opa, "journal": journal, "window_seconds": 2}
    truth = {"true_pairs": true_pairs, "observable_true_pairs": observable,
             "removed_refs": sorted(removed_refs),
             "impostor_refs": sorted(r["evidence_ref"] for r in impostors)}
    return inputs, truth


def run_matcher(inputs):
    # Only observation lists and an explicit window cross the matcher interface.
    from src.evidence_correlation import correlate

    return correlate(inputs["opa"], inputs["journal"], window_seconds=inputs["window_seconds"])


def evaluate(findings, truth):
    accepted = {(r["evidence_ref"], r["candidate_refs"][0]) for r in findings
                if r["source"] == "opa" and r["state"] == "MATCHED"}
    planned = {tuple(pair) for pair in truth["true_pairs"]}
    observable = {tuple(pair) for pair in truth["observable_true_pairs"]}
    correct = len(accepted & planned)
    false = len(accepted - planned)
    total = len(findings)
    counts = {state: sum(r["state"] == state for r in findings)
              for state in ("MATCHED", "AMBIGUOUS", "UNMATCHED", "EVIDENCE_DEFECT")}
    return {"planned_true_pairs": len(planned), "observable_true_pairs": len(observable),
            "observations": total, "accepted_links": len(accepted),
            "correct_accepted_links": correct, "false_accepted_links": false,
            "precision": correct / len(accepted) if accepted else None,
            "recall": correct / len(planned) if planned else None,
            "observable_recall": correct / len(observable) if observable else None,
            "false_link_rate": false / len(accepted) if accepted else None,
            "ambiguity_rate": counts["AMBIGUOUS"] / total if total else None,
            "unmatched_rate": counts["UNMATCHED"] / total if total else None,
            "evidence_defects": counts["EVIDENCE_DEFECT"],
            "removed_records": len(truth["removed_refs"]),
            "impostor_records": len(truth["impostor_refs"])}


def scenarios():
    for repetition in (1, 2, 5):
        for gap in (0, SECOND // 2, 2 * SECOND, 2 * SECOND + 1, 5 * SECOND):
            for skew in (-5 * SECOND, -2 * SECOND, 0, 2 * SECOND, 5 * SECOND):
                yield f"density-r{repetition}-gap{gap}-skew{skew}", {
                    "repetitions": repetition, "separation_ns": gap, "skew_ns": skew}
    for skew in (-2 * SECOND - 1, -2 * SECOND, 2 * SECOND, 2 * SECOND + 1):
        yield f"boundary-skew{skew}", {"skew_ns": skew}
    for side in ("opa", "journal"):
        for missing in (0, 0.25, 0.5, 1):
            for impostors in (0, 0.5, 1):
                yield f"loss-{side}-missing{missing}-impostors{impostors}", {
                    "missing_side": side, "missing_fraction": missing,
                    "impostor_fraction": impostors}
    # Combined stressors expose effects that one-factor sweeps can hide.
    for side in ("opa", "journal"):
        for skew in (0, 5 * SECOND):
            yield f"combined-{side}-skew{skew}", {
                "repetitions": 5, "separation_ns": 5 * SECOND, "skew_ns": skew,
                "missing_side": side, "missing_fraction": 0.5, "impostor_fraction": 0.5}


def _write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def _percent(value):
    return "—" if value is None else f"{value:.1%}"


def write_report(output, rows, metadata):
    by_name = {row["scenario"]: row for row in rows}
    selected = [
        ("Isolated, no skew", "density-r1-gap5000000000-skew0"),
        ("Five simultaneous repetitions", "density-r5-gap0-skew0"),
        ("Five repetitions, separation 2s", "density-r5-gap2000000000-skew0"),
        ("Five repetitions, separation 2s + 1ns", "density-r5-gap2000000001-skew0"),
        ("Isolated, skew +2s", "boundary-skew2000000000"),
        ("Isolated, skew +2s + 1ns", "boundary-skew2000000001"),
        ("Five repetitions, gap 5s, skew +5s", "density-r5-gap5000000000-skew5000000000"),
        ("25% journal loss", "loss-journal-missing0.25-impostors0"),
        ("50% journal loss", "loss-journal-missing0.5-impostors0"),
        ("50% journal replacement by impostors", "loss-journal-missing0.5-impostors0.5"),
        ("100% journal replacement by impostors", "loss-journal-missing1-impostors1"),
        ("Complete evidence plus 100% journal impostors", "loss-journal-missing0-impostors1"),
    ]
    lines = ["# Correlation reliability benchmark results", "",
             f"Executed {len(rows)} deterministic scenarios, with {metadata['groups']} distinct actor groups per scenario.",
             "The matcher is unchanged; the inclusive window is fixed at 2 seconds.", "",
             "| Workload | True pairs | Accepted | False links | Precision | Recall | Observable recall | Ambiguous | Unmatched |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for label, name in selected:
        r = by_name[name]
        values = [label, str(r["planned_true_pairs"]), str(r["accepted_links"]),
                  str(r["false_accepted_links"])] + [_percent(r[key]) for key in
                  ("precision", "recall", "observable_recall", "ambiguity_rate", "unmatched_rate")]
        lines.append("| " + " | ".join(values) + " |")
    lines += ["", "## Findings", "",
              "- Complete, isolated observations match correctly. With zero skew, identical repetitions separated by at most the window become ambiguous; separation just above the window restores unique links.",
              "- Isolated true pairs match at exactly ±2 seconds of skew and are unmatched one nanosecond beyond that boundary.",
              "- Clock skew equal to the repetition interval can alias each event to the adjacent request. These wrong links are mutually unique: ambiguity is not a reliable warning signal.",
              "- Missing evidence reduces end-to-end recall even when every observable true pair is recovered.",
              "- Replacement impostors produce false accepted links without ambiguity. Extra impostors alongside intact true evidence instead cause abstention through ambiguity.",
              "", "## Metrics and reproducibility", "",
              "Precision = correct accepted links / all accepted links. Recall = correct accepted links / all planned true pairs, including missing counterparts. Observable recall uses only true pairs with both original records present. Undefined ratios are shown as — (JSON null).",
              "Ambiguity and unmatched rates use all supplied observations across both sources as denominator. Each accepted link is counted once, from the OPA side. No pairwise true-negative accuracy is reported.",
              "", "See [all scenario metrics](metrics.csv), [machine-readable results](results.json), [matcher-only inputs](matcher-inputs.json), [raw findings](findings.json), and [evaluator-only truth](ground-truth.json).",
              "", "Inputs are synthetic normalized observations, not newly emitted native OPA logs. This benchmark characterizes the matching algorithm, not OPA, ingestion, custody, or production accuracy. Actor groups are controlled strata, not independent empirical samples. No confidence intervals or deployment thresholds are inferred.",
              "", "Ground truth is held by the parent evaluator and written only after a separate matcher process exits. The worker receives only observation inputs and the window. It cannot consume truth through its interface; this is logical/process isolation, not an adversarial OS sandbox.",
              "", f"Matcher SHA-256 before and after: `{metadata['matcher_sha256']}`.",
              "No aggregate production precision is inferred by averaging arbitrarily selected scenarios.", ""]
    (output / "README.md").write_text("\n".join(lines))


def benchmark(output, *, groups=20):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    matcher = ROOT / "src/evidence_correlation.py"
    before = hashlib.sha256(matcher.read_bytes()).hexdigest()
    inputs, truths, parameters = {}, {}, {}
    for name, options in scenarios():
        inputs[name], truths[name] = build_case(name, groups=groups, **options)
        parameters[name] = {"groups": groups, "repetitions": 1, "separation_ns": 5 * SECOND,
                            "skew_ns": 0, "missing_fraction": 0, "missing_side": "journal",
                            "impostor_fraction": 0, **options}
    input_path, finding_path = output / "matcher-inputs.json", output / "findings.json"
    _write_json(input_path, inputs)
    # The truth artifact does not exist while this worker executes. No truth or
    # scenario parameters enter its input; case names only group independent runs.
    subprocess.run([sys.executable, "-B", "-m", "experiments.foreign_opa.benchmark",
                    "--worker-input", str(input_path), "--worker-output", str(finding_path)],
                   cwd=ROOT, check=True)
    findings = json.loads(finding_path.read_text())
    rows = [{"scenario": name, **parameters[name], **evaluate(findings[name], truths[name])}
            for name in inputs]
    after = hashlib.sha256(matcher.read_bytes()).hexdigest()
    if before != after:
        raise RuntimeError("matcher changed during benchmark")
    metadata = {"matcher_sha256": before, "groups": groups, "seed": 20260905,
                "scenario_count": len(rows), "window_seconds": 2,
                "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
                "python_version": sys.version.split()[0], "synthetic": True}
    _write_json(output / "ground-truth.json", truths)
    _write_json(output / "results.json", {"metadata": metadata, "scenarios": rows})
    with (output / "metrics.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    write_report(output, rows, metadata)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output")
    parser.add_argument("--groups", type=int, default=20)
    parser.add_argument("--worker-input")
    parser.add_argument("--worker-output")
    args = parser.parse_args()
    if args.worker_input:
        if not args.worker_output or args.output:
            parser.error("worker requires only worker input/output")
        inputs = json.loads(Path(args.worker_input).read_text())
        _write_json(Path(args.worker_output), {name: run_matcher(case) for name, case in inputs.items()})
    elif args.output:
        rows = benchmark(args.output, groups=args.groups)
        print(f"Wrote {len(rows)} scenarios to {args.output}")
    else:
        parser.error("supply --output with a new directory")


if __name__ == "__main__":
    main()
