import json
import uuid
from copy import deepcopy
from pathlib import Path

import jsonschema

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
    AUTHORITY_SOURCE_PATH, RULE_VERSION, boundary_status, instant, load_authority_source,
    load_preserved_revision, policy_authority, preserve_revision, resolve_authority, utc_now,
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
    authority_path=AUTHORITY_SOURCE_PATH,
):
    emit = emit or (lambda event_type, data: None)
    action_attempt_id = str(uuid.uuid4())

    identity = {"action": action, "resource_id": resource_id, "action_attempt_id": action_attempt_id}
    authority_resolution_at = utc_now()
    history = Path(governance_log_path).parent / "authority_history"
    revision_ref = None
    try:
        revision = load_authority_source(authority_path)
        revision_ref = preserve_revision(revision, history)
        # Evaluate the preserved bytes, not a subsequent read of the current registry.
        revision = load_preserved_revision(revision_ref, history)
        first = resolve_authority(actor_id, effective_at=authority_resolution_at, registry_revision=revision)
    except (OSError, ValueError, TypeError, KeyError, jsonschema.ValidationError) as error:
        first = {"status": "INSUFFICIENT_EVIDENCE" if isinstance(error, FileNotFoundError) else "EVIDENCE_DEFECT",
                 "principal": actor_id, "effective_at": authority_resolution_at, "rule_version": RULE_VERSION,
                 "record_refs": [], "candidates": [], "basis": None}
    binding = {"rule_version": RULE_VERSION, "authority_resolution_at": authority_resolution_at,
               "opa_decision_at": None, "revision": revision_ref, "at_resolution": first,
               "at_opa_decision": None, "status": first["status"]}

    def record_authority():
        schema = load_authority_source(PROJECT_ROOT / "schemas/authority_resolution.schema.json")
        jsonschema.validate(binding, schema, format_checker=jsonschema.FormatChecker())
        snapshot = deepcopy(binding)
        append_governance_event({"run_id": run_id, "step_id": step_id, **identity,
                                 "recorded_at": utc_now(), "authority_binding": snapshot},
                                Path(governance_log_path).parent / "authority_resolution.jsonl")
        emit("AUTHORITY_RESOLUTION", {**identity, "authority_binding": snapshot})

    def not_evaluable(policy_decision=None):
        emit("EXECUTION_DISPOSITION", {**identity, "status": "NOT_ATTEMPTED_AUTHORITY", "authority_status": binding["status"]})
        emit("OBSERVED_OUTCOME", {**identity, "status": "AUTHORITY_NOT_EVALUABLE", "resource_read": False})
        return {"run_id": run_id, "authority_status": binding["status"],
                "policy_decision": policy_decision, "resource_returned": False}

    record_authority()
    if first["status"] != "RESOLVED":
        return not_evaluable()
    authority = policy_authority(first, action, "employee_complaint")

    policy_input = build_policy_input(
    resource_id,
    actor_id=actor_id,
    authority=authority,
    action_attempt_id=
        action_attempt_id,
    action=action,
    )

    policy_input["authority_resolution_at"] = authority_resolution_at

    decision, opa_decision_event = (
    evaluate_policy_with_decision_log(
        policy_input
    )
    )

    append_opa_decision_event(
    opa_decision_event,
    opa_decision_log_path,
    )
    
    native_timestamp = opa_decision_event.get("timestamp")
    binding["opa_decision_at"] = native_timestamp if isinstance(native_timestamp, str) else None
    second = resolve_authority(actor_id, effective_at=binding["opa_decision_at"], registry_revision=revision)
    binding["at_opa_decision"] = second
    binding["status"] = boundary_status(first, second)
    if second["status"] != "EVIDENCE_DEFECT" and instant(binding["opa_decision_at"]) < instant(authority_resolution_at):
        binding["status"] = "EVIDENCE_DEFECT"
    record_authority()

    decision_event = build_event(
        policy_input,
        decision,
    context={
    "run_id": run_id,
    "step_id": step_id,
    "action_attempt_id": action_attempt_id,
    "agent_id": actor_id,
    "authority_binding": binding,
},
    )

    validate_event(
        decision_event
    )

    append_governance_event(
        decision_event,
        governance_log_path,
    )

    emit("GOVERNANCE_DECISION", {**identity, "governance_event_id": decision_event["event_id"],
                                 "policy_input": policy_input, "decision": decision})

    if binding["status"] != "RESOLVED":
        return not_evaluable(decision["decision"])

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
        "authority_status": binding["status"],
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
