import json
import uuid
from pathlib import Path

from src.complaint_store import (
    DEFAULT_EXECUTION_LOG,
    read_complaint,
)
from src.governance_event import (
    build_event,
    evaluate_policy,
    validate_event,
    evaluate_policy_with_decision_log,
)
from src.authority_resolver import (
    resolve_authority,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_GOVERNANCE_LOG = (
    PROJECT_ROOT
    / "artifacts"
    / "runtime_governance_events.jsonl"
)

DEFAULT_OPA_DECISION_LOG = (
    PROJECT_ROOT
    / "artifacts"
    / "runtime_opa_decision_events.jsonl"
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


def append_opa_decision_event(
    event,
    log_path=DEFAULT_OPA_DECISION_LOG,
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
    authority,
    action_attempt_id,
    action="read",
):
    return {
         "action_attempt_id":
            action_attempt_id,
        "user": {
            "id": actor_id,
            "roles": authority["roles"],
        },
        "action": action,
        "authorized_resource_ids":
            authority[
                "authorized_resource_ids"
            ],
        "resource": {
            "id": resource_id,
            "type": "employee_complaint",
            "classification": "restricted",
        },
    }


def _governed_action(
    resource_id,
    *,
    run_id,
    step_id,
    actor_id,
    bypass_enforcement=False,
    governance_log_path=DEFAULT_GOVERNANCE_LOG,
    execution_log_path=DEFAULT_EXECUTION_LOG,
    opa_decision_log_path=DEFAULT_OPA_DECISION_LOG,
    action="read",
    emit=None,
):
    emit = emit or (lambda event_type, data: None)
    action_attempt_id = str(uuid.uuid4())

    authority = resolve_authority(
    actor_id
    )

    policy_input = build_policy_input(
    resource_id,
    actor_id=actor_id,
    authority=authority,
    action_attempt_id=
        action_attempt_id,
    action=action,
    )

    decision, opa_decision_event = (
    evaluate_policy_with_decision_log(
        policy_input
    )
    )

    append_opa_decision_event(
    opa_decision_event,
    opa_decision_log_path,
    )
    
    decision_event = build_event(
        policy_input,
        decision,
    context={
    "run_id": run_id,
    "step_id": step_id,
    "action_attempt_id": action_attempt_id,
    "agent_id": actor_id,
    "authority_provenance":
        authority["provenance"],
},
    )

    validate_event(
        decision_event
    )

    append_governance_event(
        decision_event,
        governance_log_path,
    )

    identity = {"action": action, "resource_id": resource_id, "action_attempt_id": action_attempt_id}
    emit("GOVERNANCE_DECISION", {**identity, "governance_event_id": decision_event["event_id"],
                                 "policy_input": policy_input, "decision": decision})

    complaint = None

    if (
        decision["allowed"]
        or bypass_enforcement
    ):
        if action != "read":
            emit("EXECUTION_DISPOSITION", {**identity, "status": "NOT_ATTEMPTED_NO_EXECUTOR"})
            emit("OBSERVED_OUTCOME", {**identity, "status": "INTEGRATION_ERROR", "resource_read": False})
            raise ValueError("Policy allowed an action with no registered executor")
        emit("EXECUTION_DISPOSITION", {**identity, "status": "DISPATCHING"})
        emit("EXECUTION_ATTEMPT", identity)
        try:
            complaint = read_complaint(
                resource_id, run_id=run_id, step_id=step_id, actor_id=actor_id,
                action_attempt_id=action_attempt_id, log_path=execution_log_path)
        except Exception as error:
            emit("OBSERVED_OUTCOME", {**identity, "status": "EXECUTION_FAILED", "error_type": type(error).__name__,
                                      "resource_read": None})
            raise
        emit("OBSERVED_OUTCOME", {**identity, "status": "RESOURCE_RETURNED", "resource_read": True,
                                  "returned_resource_id": complaint["id"]})
    else:
        emit("EXECUTION_DISPOSITION", {**identity, "status": "BLOCKED_BY_GOVERNANCE"})
        emit("OBSERVED_OUTCOME", {**identity, "status": "DENIED_NO_EXECUTION", "resource_read": False})

    return {
        "run_id": run_id,
        "policy_decision": decision["decision"],
        "resource_returned": complaint is not None,
    }


def governed_read(resource_id, *, run_id, step_id, actor_id, bypass_enforcement=False,
                  governance_log_path=DEFAULT_GOVERNANCE_LOG, execution_log_path=DEFAULT_EXECUTION_LOG,
                  opa_decision_log_path=DEFAULT_OPA_DECISION_LOG):
    """Compatibility path, including the existing explicit bypass test facility."""
    return _governed_action(resource_id, run_id=run_id, step_id=step_id, actor_id=actor_id,
                            bypass_enforcement=bypass_enforcement, governance_log_path=governance_log_path,
                            execution_log_path=execution_log_path, opa_decision_log_path=opa_decision_log_path)


def governed_action(resource_id, *, action, run_id, step_id, actor_id, emit,
                    governance_log_path=DEFAULT_GOVERNANCE_LOG, execution_log_path=DEFAULT_EXECUTION_LOG,
                    opa_decision_log_path=DEFAULT_OPA_DECISION_LOG):
    """Model proposal entry point. There is deliberately no enforcement bypass."""
    if action not in ("read", "export"):
        raise ValueError("Unsupported proposal action")
    return _governed_action(resource_id, action=action, run_id=run_id, step_id=step_id, actor_id=actor_id,
                            emit=emit, governance_log_path=governance_log_path,
                            execution_log_path=execution_log_path, opa_decision_log_path=opa_decision_log_path)
