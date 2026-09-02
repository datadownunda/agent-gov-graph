import copy
import json

from src.complaint_runtime import governed_read
from src.complaint_store import read_complaint
from src.runtime_reconciler import (
    load_json,
    load_jsonl,
    reconcile_runtime,
    COVERAGE_CONTRACT_PATH,
)


def run_reconciliation(
    governance_log,
    execution_log,
):
    return reconcile_runtime(
        load_jsonl(governance_log),
        load_jsonl(execution_log),
        load_json(COVERAGE_CONTRACT_PATH),
    )


def classifications_by_run(results):
    return {
        result["run_id"]:
            result["classification"]
        for result in results
    }


def test_runtime_reconciliation_detects_five_cases(
    tmp_path,
):
    governance_log = (
        tmp_path
        / "governance.jsonl"
    )

    execution_log = (
        tmp_path
        / "execution.jsonl"
    )

    governed_read(
        "complaint-456",
        run_id="run-a-allow",
        step_id="step-001",
        actor_id="complaint-review-agent",
        governance_log_path=governance_log,
        execution_log_path=execution_log,
    )

    governed_read(
        "complaint-789",
        run_id="run-b-deny-block",
        step_id="step-001",
        actor_id="complaint-review-agent",
        governance_log_path=governance_log,
        execution_log_path=execution_log,
    )

    governed_read(
        "complaint-789",
        run_id="run-c-deny-bypass",
        step_id="step-001",
        actor_id="complaint-review-agent",
        bypass_enforcement=True,
        governance_log_path=governance_log,
        execution_log_path=execution_log,
    )

    read_complaint(
        "complaint-789",
        run_id="run-d-no-governance",
        step_id="step-001",
        actor_id="complaint-review-agent",
        log_path=execution_log,
    )

    governed_read(
        "complaint-456",
        run_id="run-e-manager-role-deny",
        step_id="step-001",
        actor_id="manager-agent",
        governance_log_path=governance_log,
        execution_log_path=execution_log,
    )

    results = run_reconciliation(
        governance_log,
        execution_log,
    )

    classifications = (
        classifications_by_run(results)
    )

    assert classifications[
        "run-a-allow"
    ] == "GOVERNED_ALLOWED_EXECUTION"

    assert classifications[
        "run-b-deny-block"
    ] == "DENY_EFFECT_NOT_OBSERVED"

    assert classifications[
        "run-c-deny-bypass"
    ] == "ENFORCEMENT_FAILURE"

    assert classifications[
        "run-d-no-governance"
    ] == "COVERAGE_FAILURE"

    assert classifications[
        "run-e-manager-role-deny"
    ] == "DENY_EFFECT_NOT_OBSERVED"

    results_by_run = {
        result["run_id"]: result
        for result in results
    }

    allow_result = results_by_run[
        "run-a-allow"
    ]

    assert (
        allow_result["coverage_status"]
        == "COVERED"
    )
    assert (
        allow_result["decision_status"]
        == "ALLOW"
    )
    assert (
        allow_result["enforcement_status"]
        == "PROCEEDED"
    )
    assert (
        allow_result["outcome_status"]
        == "RESOURCE_READ"
    )

    deny_result = results_by_run[
        "run-b-deny-block"
    ]

    assert (
        deny_result["coverage_status"]
        == "COVERED"
    )
    assert (
        deny_result["decision_status"]
        == "DENY"
    )
    assert (
        deny_result["enforcement_status"]
        == "CONSISTENT_WITH_BLOCKING"
    )
    assert (
        deny_result["outcome_status"]
        == "NO_EFFECT_OBSERVED"
    )

    enforcement_failure = results_by_run[
        "run-c-deny-bypass"
    ]

    assert (
        enforcement_failure[
            "coverage_status"
        ]
        == "COVERED"
    )
    assert (
        enforcement_failure[
            "decision_status"
        ]
        == "DENY"
    )
    assert (
        enforcement_failure[
            "enforcement_status"
        ]
        == "FAILED"
    )
    assert (
        enforcement_failure[
            "outcome_status"
        ]
        == "RESOURCE_READ"
    )

    coverage_failure = results_by_run[
        "run-d-no-governance"
    ]

    assert (
        coverage_failure[
            "coverage_status"
        ]
        == "COVERAGE_MISSING"
    )
    assert (
        coverage_failure[
            "decision_status"
        ]
        == "NO_DECISION"
    )
    assert (
        coverage_failure[
            "enforcement_status"
        ]
        == "NOT_EVALUABLE"
    )
    assert (
        coverage_failure[
            "outcome_status"
        ]
        == "RESOURCE_READ"
    )

    manager_denial = results_by_run[
        "run-e-manager-role-deny"
    ]

    assert (
        manager_denial["coverage_status"]
        == "COVERED"
    )
    assert (
        manager_denial["decision_status"]
        == "DENY"
    )
    assert (
        manager_denial[
            "enforcement_status"
        ]
        == "CONSISTENT_WITH_BLOCKING"
    )
    assert (
        manager_denial["outcome_status"]
        == "NO_EFFECT_OBSERVED"
    )
    assert (
        allow_result["evidence"][
            "governance_event_id"
        ]
        is not None
    )
    assert (
        allow_result["evidence"][
            "execution_event_id"
        ]
        is not None
    )

    assert (
        deny_result["evidence"][
            "governance_event_id"
        ]
        is not None
    )
    assert (
        deny_result["evidence"][
            "execution_event_id"
        ]
        is None
    )

    assert (
        coverage_failure["evidence"][
            "governance_event_id"
        ]
        is None
    )
    assert (
        coverage_failure["evidence"][
            "execution_event_id"
        ]
        is not None
    )

    governance_events = load_jsonl(
        governance_log
    )

    manager_event = next(
        event
        for event in governance_events
        if event["context"]["run_id"]
        == "run-e-manager-role-deny"
    )

    assert manager_event[
        "subject"
    ]["roles"] == ["manager"]

    provenance = manager_event[
        "context"
    ]["authority_provenance"]

    assert (
        provenance["source_id"]
        == "synthetic-agent-authority-registry"
    )
    assert (
        provenance["source_version"]
        == "1.0"
    )
    assert provenance["valid_from"]
    assert provenance["resolved_at"]


def test_duplicate_governance_attempt_is_evidence_conflict(
    tmp_path,
):
    governance_log = (
        tmp_path
        / "governance.jsonl"
    )

    execution_log = (
        tmp_path
        / "execution.jsonl"
    )

    governed_read(
        "complaint-789",
        run_id="run-evidence-conflict",
        step_id="step-001",
        actor_id="complaint-review-agent",
        bypass_enforcement=True,
        governance_log_path=governance_log,
        execution_log_path=execution_log,
    )

    governance_events = load_jsonl(
        governance_log
    )

    original_event = (
        governance_events[0]
    )

    conflicting_event = copy.deepcopy(
        original_event
    )

    conflicting_event[
        "event_id"
    ] = "conflicting-event"

    conflicting_event[
        "decision"
    ]["allowed"] = True

    conflicting_event[
        "decision"
    ]["status"] = "ALLOW"

    conflicting_event[
        "decision"
    ]["reasons"] = []

    with governance_log.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                conflicting_event
            )
            + "\n"
        )

    results = run_reconciliation(
        governance_log,
        execution_log,
    )

    result = next(
        result
        for result in results
        if result["run_id"]
        == "run-evidence-conflict"
    )

    assert (
        result["classification"]
        == "EVIDENCE_CONFLICT"
    )
    assert (
        result["coverage_status"]
        == "COVERED"
    )
    assert (
        result["decision_status"]
        == "CONFLICT"
    )
    assert (
        result["enforcement_status"]
        == "NOT_EVALUABLE"
    )
    assert (
        result["outcome_status"]
        == "RESOURCE_READ"
    )

    assert len(
        result["evidence"][
            "governance_event_ids"
        ]
    ) == 2

    assert len(
        result["evidence"][
            "execution_event_ids"
        ]
    ) == 1


def test_duplicate_execution_attempt_is_evidence_conflict(
    tmp_path,
):
    governance_log = (
        tmp_path
        / "governance.jsonl"
    )

    execution_log = (
        tmp_path
        / "execution.jsonl"
    )

    governed_read(
        "complaint-456",
        run_id="run-execution-conflict",
        step_id="step-001",
        actor_id="complaint-review-agent",
        governance_log_path=governance_log,
        execution_log_path=execution_log,
    )

    execution_events = load_jsonl(
        execution_log
    )

    original_event = (
        execution_events[0]
    )

    duplicate_event = copy.deepcopy(
        original_event
    )

    duplicate_event[
        "event_id"
    ] = "duplicate-execution-event"

    with execution_log.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                duplicate_event
            )
            + "\n"
        )

    results = run_reconciliation(
        governance_log,
        execution_log,
    )

    result = next(
        result
        for result in results
        if result["run_id"]
        == "run-execution-conflict"
    )

    assert (
        result["classification"]
        == "EVIDENCE_CONFLICT"
    )

    assert (
        result["coverage_status"]
        == "COVERED"
    )
    assert (
        result["decision_status"]
        == "ALLOW"
    )
    assert (
        result["enforcement_status"]
        == "NOT_EVALUABLE"
    )
    assert (
        result["outcome_status"]
        == "CONFLICT"
    )

    assert len(
        result["evidence"][
            "governance_event_ids"
        ]
    ) == 1

    assert len(
        result["evidence"][
            "execution_event_ids"
        ]
    ) == 2