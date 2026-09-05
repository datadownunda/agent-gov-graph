"""Twenty one-shot calls; no selection repair, retries, or autonomous loops."""

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess

from src.model_agent_runner import run_trial
from src.model_proposal import DEFAULT_MODEL


ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = Path(__file__).with_name("scenarios.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    if not os.environ.get("OPENAI_API_KEY"):
        parser.error("OPENAI_API_KEY must be configured before live trials")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    scenarios = json.loads(SCENARIOS.read_text())
    metadata = {"requested_model": args.model, "provider": "openai", "calls_planned": 20,
                "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [
                    ROOT / "src/model_proposal.py", ROOT / "src/model_agent_runner.py",
                    ROOT / "src/complaint_runtime.py", ROOT / "policies/complaints.rego",
                    ROOT / "runtime_resources/authority/agent_authority.json", SCENARIOS]},
                "candidate_metadata": "synthetic pre-governance descriptors; no complaint bodies in model input",
                "reproducibility": "Context is preserved; identical future outputs are not guaranteed."}
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    rows = []
    for scenario in scenarios:
        for repetition in range(5):
            trial = output / f"{scenario['name']}-{repetition + 1}"
            result = run_trial(scenario["task"], scenario["candidates"], output_dir=trial, model=args.model)
            row = {"scenario": scenario["name"], "repetition": repetition + 1, **result}
            rows.append(row)
            (output / "results.json").write_text(json.dumps(rows, indent=2) + "\n")
            print(json.dumps(row), flush=True)
    lines = ["# Model-driven complaint experiment", "",
             f"Requested model: `{args.model}`. Twenty scheduled calls; failures and refusals are retained.", "",
             "| Scenario | Outcomes | Selected action/resource frequencies |", "|---|---|---|"]
    for scenario in scenarios:
        selected = [r for r in rows if r["scenario"] == scenario["name"]]
        choices = Counter(f"{r['proposal']['action']} / {r['proposal']['resource_id']}" for r in selected if "proposal" in r)
        statuses = Counter(r["status"] for r in selected)
        lines.append(f"| {scenario['name']} | {dict(statuses)} | {dict(choices)} |")
    lines += ["", "All five repetitions within a scenario received identical task/candidate ordering. Choice differences are observed output variation, not an estimate of production reliability. Lack of variation is not proof of determinism.",
              "Invalid proposals are rejected before governance. Known unauthorized proposals reach OPA and may be denied. These categories must not be pooled.",
              "These calls use synthetic complaints and cooperating application evidence. They do not establish independent custody, agent intent, policy completeness, or exact replay reproducibility.", ""]
    (output / "README.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
