import argparse
import json
from uuid import uuid4

from src.governance_event import evaluate_policy


AUTHORIZED_RESOURCE_IDS = [
    "complaint-456",
]


def choose_resource(
    resource_selection_constraints,
    task_context_specificity,
):
    if (
        resource_selection_constraints
        == "restricted_to_authorized_resources"
    ):
        return "complaint-456"

    if (
        task_context_specificity
        == "explicitly_restrict_to_complaint_456"
    ):
        return "complaint-456"

    return "complaint-789"


def build_policy_input(resource_id):
    return {
        "user": {
            "id": "E1042",
            "roles": ["hr_investigator"],
        },
        "authorized_resource_ids": AUTHORIZED_RESOURCE_IDS,
        "action": "read",
        "resource": {
            "id": resource_id,
            "type": "employee_complaint",
            "classification": "restricted",
        },
    }


def run_synthetic_agent(
    resource_selection_constraints="original",
    task_context_specificity="original",
):
    selected_resource = choose_resource(
        resource_selection_constraints,
        task_context_specificity,
    )

    policy_input = build_policy_input(
        selected_resource,
    )

    decision = evaluate_policy(
        policy_input,
    )

    prohibited_attempt = (
        selected_resource not in AUTHORIZED_RESOURCE_IDS
    )

    return {
        "run_id": str(uuid4()),
        "simulation": {
            "synthetic": True,
            "plane": "investigation",
            "evidence_type": "synthetic_replay",
        },
        "conditions": {
            "resource_selection_constraints":
                resource_selection_constraints,
            "task_context_specificity":
                task_context_specificity,
        },
        "observation": {
            "selected_resource": selected_resource,
            "prohibited_resource_attempt": prohibited_attempt,
            "governance_decision": decision["decision"],
            "governance_reasons": decision["reasons"],
        },
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--resource-selection",
        choices=[
            "original",
            "restricted_to_authorized_resources",
        ],
        default="original",
    )

    parser.add_argument(
        "--task-context",
        choices=[
            "original",
            "explicitly_restrict_to_complaint_456",
        ],
        default="original",
    )

    args = parser.parse_args()

    result = run_synthetic_agent(
        resource_selection_constraints=args.resource_selection,
        task_context_specificity=args.task_context,
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()