import json
import os

import pytest

from src.model_agent_runner import run_trial
from src import complaint_runtime as runtime


CANDIDATES = [{"resource_id": "complaint-456", "priority": "normal"},
              {"resource_id": "complaint-789", "priority": "high"}]


def model(raw):
    def respond(request):
        assert len(json.loads(request["input"])["candidates"]) == 2
        return {"status": "COMPLETED", "output_text": raw, "provider": "test-double",
                "model": "stub", "raw_response": {"output_text": raw}}
    return respond


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


@pytest.mark.parametrize("resource,action,allowed", [
    ("complaint-456", "read", True), ("complaint-789", "read", False),
    ("complaint-456", "export", False),
])
def test_exact_proposal_through_governance_and_execution(tmp_path, monkeypatch, resource, action, allowed):
    proposal = {"action": action, "resource_id": resource, "reason": "model choice"}
    seen, executed = [], []

    def evaluate(policy_input):
        seen.append(policy_input)
        evidence = records(tmp_path / "agent.jsonl")
        assert [e["event_type"] for e in evidence][-2:] == ["MODEL_PROPOSAL", "PROPOSAL_ACCEPTED"]
        decision = {"allowed": allowed, "decision": "ALLOW" if allowed else "DENY",
                    "policy": "employee_complaint_access", "policy_version": "1.0", "reasons": []}
        return decision, {"input": policy_input, "result": decision, "decision_id": "test"}

    def read(resource_id, **kwargs):
        assert records(tmp_path / "agent.jsonl")[-1]["event_type"] == "EXECUTION_ATTEMPT"
        executed.append(resource_id)
        return {"id": resource_id}

    monkeypatch.setattr(runtime, "evaluate_policy_with_decision_log", evaluate)
    monkeypatch.setattr(runtime, "read_complaint", read)
    result = run_trial("task", CANDIDATES, output_dir=tmp_path, propose=model(json.dumps(proposal)), model="stub")
    assert seen[0]["resource"]["id"] == resource
    assert seen[0]["action"] == action
    assert executed == ([resource] if allowed else [])
    assert result["status"] == ("EXECUTED" if allowed else "DENIED")
    events = records(tmp_path / "agent.jsonl")
    assert next(e for e in events if e["event_type"] == "MODEL_PROPOSAL")["data"]["raw_output"] == json.dumps(proposal)
    assert any(e["event_type"] == "GOVERNANCE_DECISION" for e in events)
    assert any(e["event_type"] == "OBSERVED_OUTCOME" for e in events)
    assert sum(e["event_type"] == "EXECUTION_ATTEMPT" for e in events) == int(allowed)


@pytest.mark.parametrize("raw", ["bad", '{"action":"read"}',
    '{"action":"read","resource_id":"unknown","reason":"x"}',
    '{"action":"delete","resource_id":"complaint-456","reason":"x"}'])
def test_invalid_never_reaches_governance(tmp_path, monkeypatch, raw):
    def forbidden(*args, **kwargs):
        pytest.fail("invalid proposal reached governance or execution")
    monkeypatch.setattr(runtime, "evaluate_policy_with_decision_log", forbidden)
    monkeypatch.setattr(runtime, "read_complaint", forbidden)
    result = run_trial("task", CANDIDATES, output_dir=tmp_path, propose=model(raw), model="stub")
    assert result["status"] == "INVALID_PROPOSAL"
    assert not (tmp_path / "governance.jsonl").exists()


def test_execution_failure_has_attempt_and_failed_outcome(tmp_path, monkeypatch):
    def evaluate(data):
        decision = {"allowed": True, "decision": "ALLOW", "policy": "employee_complaint_access",
                    "policy_version": "1.0", "reasons": []}
        return decision, {"input": data, "result": decision}
    monkeypatch.setattr(runtime, "evaluate_policy_with_decision_log", evaluate)
    def fail(*args, **kwargs):
        raise OSError("synthetic read failure")
    monkeypatch.setattr(runtime, "read_complaint", fail)
    result = run_trial("task", CANDIDATES, output_dir=tmp_path,
                       propose=model('{"action":"read","resource_id":"complaint-456","reason":"x"}'), model="stub")
    assert result["status"] == "RUNTIME_ERROR"
    events = records(tmp_path / "agent.jsonl")
    assert any(e["event_type"] == "EXECUTION_ATTEMPT" for e in events)
    assert any(e["event_type"] == "OBSERVED_OUTCOME" and e["data"]["status"] == "EXECUTION_FAILED" for e in events)


@pytest.mark.skipif(os.environ.get("RUN_FOREIGN_OPA") != "1", reason="requires Docker/OPA")
@pytest.mark.parametrize("resource,action,status", [
    ("complaint-456", "read", "EXECUTED"), ("complaint-789", "read", "DENIED"),
    ("complaint-456", "export", "DENIED")])
def test_real_opa_enforces_exact_valid_proposal(tmp_path, resource, action, status):
    result = run_trial("task", CANDIDATES, output_dir=tmp_path,
                       propose=model(json.dumps({"action": action, "resource_id": resource, "reason": "test"})), model="stub")
    assert result["status"] == status
    opa = records(tmp_path / "opa.jsonl")[0]
    assert opa["input"]["resource"]["id"] == resource
    assert opa["input"]["action"] == action
    assert (tmp_path / "execution.jsonl").exists() == (status == "EXECUTED")


def test_unexpected_allow_for_export_fails_closed(tmp_path, monkeypatch):
    def evaluate(data):
        decision = {"allowed": True, "decision": "ALLOW", "policy": "employee_complaint_access",
                    "policy_version": "1.0", "reasons": []}
        return decision, {"input": data, "result": decision}
    monkeypatch.setattr(runtime, "evaluate_policy_with_decision_log", evaluate)
    monkeypatch.setattr(runtime, "read_complaint", lambda *a, **k: pytest.fail("export rewritten to read"))
    result = run_trial("task", CANDIDATES, output_dir=tmp_path,
                       propose=model('{"action":"export","resource_id":"complaint-456","reason":"x"}'), model="stub")
    assert result["status"] == "RUNTIME_ERROR"
    assert not any(e["event_type"] == "EXECUTION_ATTEMPT" for e in records(tmp_path / "agent.jsonl"))


def test_governance_error_is_not_recorded_as_deny(tmp_path, monkeypatch):
    def fail(data):
        raise RuntimeError("OPA unavailable")
    monkeypatch.setattr(runtime, "evaluate_policy_with_decision_log", fail)
    result = run_trial("task", CANDIDATES, output_dir=tmp_path,
                       propose=model('{"action":"read","resource_id":"complaint-456","reason":"x"}'), model="stub")
    assert result["status"] == "RUNTIME_ERROR"
    events = records(tmp_path / "agent.jsonl")
    assert events[-1]["event_type"] == "OBSERVED_OUTCOME"
    assert events[-1]["data"]["resource_read"] is False
    assert not any(e["event_type"] == "EXECUTION_ATTEMPT" for e in events)


def test_successive_provider_choices_are_not_cached_or_rewritten(tmp_path, monkeypatch):
    seen = []
    def evaluate(data):
        seen.append(data["resource"]["id"])
        decision = {"allowed": False, "decision": "DENY", "policy": "employee_complaint_access",
                    "policy_version": "1.0", "reasons": []}
        return decision, {"input": data, "result": decision}
    monkeypatch.setattr(runtime, "evaluate_policy_with_decision_log", evaluate)
    for i, resource in enumerate(("complaint-789", "complaint-456", "complaint-789")):
        run_trial("task", CANDIDATES, output_dir=tmp_path / str(i),
                  propose=model(json.dumps({"action": "read", "resource_id": resource, "reason": "x"})), model="stub")
    assert seen == ["complaint-789", "complaint-456", "complaint-789"]
