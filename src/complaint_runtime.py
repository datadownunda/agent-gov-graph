import json
from pathlib import Path

from src.complaint_store import (
    DEFAULT_EXECUTION_LOG,
    read_complaint,
)
from src.governance_event import (
    build_event,
    evaluate_policy,
    validate_event,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_GOVERNANCE_LOG = (
    PROJECT_ROOT
    / "artifacts"
    / "runtime_governance_events.jsonl"
)


def append_governance_event(
    event,
    log_path=DEFAULT_GOVERNANCE_LOG,
):
    log_path = Path(log_path)

    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with log_path.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(event)
            + "\n"
        )


def build_policy_input(
    resource_id,
    *,
    actor_id,
):
    return {
        "user": {
            "id": actor_id,
            "roles": [
                "hr_investigator",
            ],
        },
        "action": "read",
        "authorized_resource_ids": [
            "complaint-456",
        ],
        "resource": {
            "id": resource_id,
            "type": "employee_complaint",
            "classification": "restricted",
        },
    }


def governed_read(
    resource_id,
    *,
    run_id,
    step_id,
    actor_id,
    bypass_enforcement=False,
    governance_log_path=DEFAULT_GOVERNANCE_LOG,
    execution_log_path=DEFAULT_EXECUTION_LOG,
):
    policy_input = build_policy_input(
        resource_id,
        actor_id=actor_id,
    )

    decision = evaluate_policy(
        policy_input
    )

    decision_event = build_event(
        policy_input,
        decision,
        context={
            "run_id": run_id,
            "step_id": step_id,
            "agent_id": actor_id,
        },
    )

    validate_event(
        decision_event
    )

    append_governance_event(
        decision_event,
        governance_log_path,
    )

    complaint = None

    if (
        decision["allowed"]
        or bypass_enforcement
    ):
        complaint = read_complaint(
            resource_id,
            run_id=run_id,
            step_id=step_id,
            actor_id=actor_id,
            log_path=execution_log_path,
        )

    return {
        "run_id": run_id,
        "policy_decision": decision["decision"],
        "resource_returned": complaint is not None,
    }