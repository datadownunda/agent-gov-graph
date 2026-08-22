import json
import subprocess
from pathlib import Path
from src.governance_event import build_event


ROOT = Path(__file__).resolve().parents[1]


def test_governance_event_generator_runs_successfully():
    result = subprocess.run(
        ["python", "src/governance_event.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    event = json.loads(result.stdout)

    assert event["resource"]["id"] == "complaint-456"
    assert event["policy"]["name"] == "employee_complaint_access"
    assert event["policy"]["version"] == "1.0"
    assert event["decision"]["status"] == "ALLOW"
    assert event["decision"]["allowed"] is True

def test_build_event_includes_context_and_telemetry():
    input_data = {
        "user": {
            "id": "E1042",
            "roles": ["hr_investigator"],
        },
        "action": "read",
        "resource": {
            "id": "complaint-456",
            "type": "employee_complaint",
            "classification": "restricted",
        },
    }

    decision = {
        "allowed": True,
        "decision": "ALLOW",
        "policy": "employee_complaint_access",
        "policy_version": "1.0",
        "reasons": [],
    }

    context = {
        "workflow_id": "workflow-123",
        "agent_id": "agent-research-01",
        "tool": "document_search",
    }

    telemetry = {
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
        "span_id": "00f067aa0ba902b7",
    }

    event = build_event(
        input_data,
        decision,
        context=context,
        telemetry=telemetry,
    )

    assert event["context"] == context
    assert event["telemetry"] == telemetry

def test_governance_event_generator_denies_manager():
    input_data = {
        "user": {
            "id": "E2001",
            "roles": ["manager"],
        },
        "action": "read",
        "resource": {
            "id": "complaint-789",
            "type": "employee_complaint",
            "classification": "restricted",
        },
    }

    from src.governance_event import evaluate_policy, build_event, validate_event

    decision = evaluate_policy(input_data)
    event = build_event(input_data, decision)

    validate_event(event)

    assert event["decision"]["status"] == "DENY"
    assert event["decision"]["allowed"] is False
    assert (
        "Restricted employee complaint data requires HR Investigator role"
        in event["decision"]["reasons"]
    )
    assert event["policy"]["name"] == "employee_complaint_access"
    assert event["policy"]["version"] == "1.0"