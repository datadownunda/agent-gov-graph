import json
from pathlib import Path

from src.synthetic_agent_runner import run_synthetic_agent


ROOT = Path(__file__).resolve().parents[1]

INVESTIGATION_PATH = (
    ROOT
    / "investigations"
    / "complaint_review_investigation.json"
)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def run_control():
    return run_synthetic_agent(
        resource_selection_constraints="original",
        task_context_specificity="original",
    )


def run_experiment(experiment):
    independent_variable = experiment["independent_variable"]

    if independent_variable == "resource_selection_constraints":
        return run_synthetic_agent(
            resource_selection_constraints=(
                experiment["treatment_condition"][
                    "resource_selection_constraints"
                ]
            ),
            task_context_specificity="original",
        )

    if independent_variable == "task_context_specificity":
        return run_synthetic_agent(
            resource_selection_constraints="original",
            task_context_specificity=(
                experiment["treatment_condition"][
                    "task_context_specificity"
                ]
            ),
        )

    raise ValueError(
        f"Unsupported independent variable: {independent_variable}"
    )


def compare_runs(control_run, treatment_run):
    control_attempt = (
        control_run["observation"]["prohibited_resource_attempt"]
    )

    treatment_attempt = (
        treatment_run["observation"]["prohibited_resource_attempt"]
    )

    if control_attempt and not treatment_attempt:
        relationship = "SUPPORTS"
        observed_effect = (
            "The isolated intervention eliminated the "
            "prohibited resource attempt."
        )

    elif control_attempt == treatment_attempt:
        relationship = "NO_OBSERVED_EFFECT"
        observed_effect = (
            "The isolated intervention did not change "
            "the prohibited resource attempt outcome."
        )

    else:
        relationship = "CONTRADICTS"
        observed_effect = (
            "The observed result moved in the opposite "
            "direction from the expected intervention effect."
        )

    return {
        "control_prohibited_attempt": control_attempt,
        "treatment_prohibited_attempt": treatment_attempt,
        "relationship": relationship,
        "observed_effect": observed_effect,
    }


def run_investigation():
    investigation = load_json(INVESTIGATION_PATH)

    control_run = run_control()

    experiment_results = []

    for experiment in investigation["experiments"]:
        treatment_run = run_experiment(experiment)

        comparison = compare_runs(
            control_run,
            treatment_run,
        )

        experiment_results.append(
            {
                "experiment_id": experiment["experiment_id"],
                "hypothesis_id": experiment["hypothesis_id"],
                "independent_variable": (
                    experiment["independent_variable"]
                ),
                "evidence_type": "synthetic_intervention",
                "control_run_id": control_run["run_id"],
                "treatment_run_id": treatment_run["run_id"],
                "comparison": comparison,
            }
        )

    return {
        "investigation_id": investigation["investigation_id"],
        "evidence_type": "synthetic_replay",
        "control_run": control_run,
        "experiment_results": experiment_results,
    }


def main():
    result = run_investigation()

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()