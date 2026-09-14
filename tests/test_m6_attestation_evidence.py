"""Verification of preserved evidence; fixtures are explicitly synthetic."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from src.control_attestation import attest, reconstruct_attestation
from src.m6_attestation_evidence import verify_m6
from src.evidence_digest import evidence_digest

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "experiments/target_outcome/results/v1"


def control():
    return json.loads(
        (ROOT / "experiments/control_attestation/control.json").read_text()
    )


def assertion_ref(name):
    return json.loads((LIVE / "reconciliation.json").read_text())[name]["assertion_id"]


def test_saved_v1_live_exception_and_abstention_and_not_applicable():
    expected = {
        "critical-deny": "CONTROL_EFFECTIVENESS_EXCEPTION",
        "blocked-bounded": "CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED",
        "blocked-deny": "CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED",
        "execution-withheld": "CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED",
        "allow": None,
    }
    for name, finding in expected.items():
        a, r = attest(LIVE, assertion_ref(name), control(), rule_version="control-attestation/1")
        assert r["status"] == "VERIFIED"
        assert a["finding"] == finding
        if name == "allow":
            assert a["evaluation_status"] == "NOT_APPLICABLE"
        if name == "blocked-bounded":
            assert r["coverage_assessment"]["result"] == "INADEQUATE"
            assert (
                "CONTROL_OBSERVATION_HORIZON_INADEQUATE"
                in r["coverage_assessment"]["basis_codes"]
            )
        assert reconstruct_attestation(a, LIVE, control())["status"] == "VERIFIED"


def test_no_scenario_ground_truth_bypass_or_filenames_in_adjudication_facts():
    r = verify_m6(LIVE, assertion_ref("critical-deny"), control())
    payload = json.dumps(r)
    for forbidden in (
        "critical-deny",
        "ground_truth",
        "CLIENT_FINALIZATION_FAILED",
        "run_id",
        "bypass",
        "native/access",
        "response_body_bytes_received",
    ):
        assert forbidden not in payload


@pytest.mark.parametrize(
    "member,remove",
    [
        ("native/access.jsonl", False),
        ("native/access.jsonl", True),
        ("identity_mapping.json", False),
        ("blocked_coverage.json", False),
        ("nginx.conf", False),
        (
            "authority_history/601887eae502d25c9e049bd6458719785e376bb82c253a4abb656e2e387232ca.json",
            False,
        ),
    ],
)
def test_tamper_and_unavailable_evidence(tmp_path, member, remove):
    shutil.copytree(LIVE, tmp_path / "archive")
    p = tmp_path / "archive" / member
    if remove:
        p.unlink()
    else:
        p.write_text("{}\n")
    a, _ = attest(tmp_path / "archive", assertion_ref("critical-deny"), control())
    assert a["evaluation_status"] == (
        "INSUFFICIENT_EVIDENCE" if remove else "NOT_EVALUABLE"
    )


def test_rehashed_forged_m6_finding_rejected_by_replay(tmp_path):
    shutil.copytree(LIVE, tmp_path / "archive")
    p = tmp_path / "archive"
    data = json.loads((p / "reconciliation.json").read_text())
    a = data["blocked-bounded"]
    a["result"] = "CONTRADICTION"
    a["assertion_id"] = evidence_digest(
        {k: v for k, v in a.items() if k != "assertion_id"}
    )
    (p / "reconciliation.json").write_text(json.dumps(data))
    m = json.loads((p / "manifest.json").read_text())
    m["files"]["reconciliation.json"] = (
        "sha256:" + hashlib.sha256((p / "reconciliation.json").read_bytes()).hexdigest()
    )
    (p / "manifest.json").write_text(json.dumps(m))
    assert (
        attest(p, a["assertion_id"], control())[0]["evaluation_status"]
        == "NOT_EVALUABLE"
    )


def test_attestation_tamper_and_source_no_mutation():
    before = {p: p.read_bytes() for p in LIVE.rglob("*") if p.is_file()}
    a, _ = attest(LIVE, assertion_ref("critical-deny"), control())
    a["finding"] = "CONTROL_EFFECTIVE"
    assert reconstruct_attestation(a, LIVE, control())["status"] == "EVIDENCE_DEFECT"
    assert all(p.read_bytes() == b for p, b in before.items())


def test_changed_ground_truth_cannot_change_adjudication(tmp_path):
    shutil.copytree(LIVE, tmp_path / "archive")
    p = tmp_path / "archive"
    before = attest(p, assertion_ref("critical-deny"), control())[0]
    (p / "ground_truth.json").write_text(
        '{"bypass":false,"expected":"CONTROL_EFFECTIVE"}\n'
    )
    m = json.loads((p / "manifest.json").read_text())
    m["files"]["ground_truth.json"] = (
        "sha256:" + hashlib.sha256((p / "ground_truth.json").read_bytes()).hexdigest()
    )
    (p / "manifest.json").write_text(json.dumps(m))
    after = attest(p, assertion_ref("critical-deny"), control())[0]
    assert (after["evaluation_status"], after["finding"], after["basis_codes"]) == (
        before["evaluation_status"],
        before["finding"],
        before["basis_codes"],
    )


@pytest.mark.parametrize(
    "function,error",
    [
        ("_project", KeyError("projection bug")),
        ("instant", ArithmeticError("clock calculation bug")),
        ("audit", TypeError("audit bug")),
    ],
)
def test_verifier_internal_failures_are_not_evidence_defects(
    monkeypatch, function, error
):
    import src.m6_attestation_evidence as module

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(module, function, fail)
    result, verification = attest(LIVE, assertion_ref("blocked-bounded"), control())
    assert verification["status"] == "INTERNAL_ERROR"
    assert verification["facts"] is None
    assert verification["coverage_assessment"] is None
    assert result["evaluation_status"] == "INTERNAL_ERROR"
    assert result["finding"] is None


def test_replay_internal_failure_is_not_invalid_evidence(monkeypatch):
    import src.control_attestation as module

    saved, _ = attest(LIVE, assertion_ref("critical-deny"), control())

    def fail(*args, **kwargs):
        raise TypeError("Replay processing bug")

    monkeypatch.setattr(module, "attest", fail)
    result = module.reconstruct_attestation(saved, LIVE, control())
    assert result["status"] == "INTERNAL_ERROR"
    assert result["finding"] is None


def test_missing_local_schema_is_internal_not_missing_evidence(monkeypatch, tmp_path):
    import src.m6_attestation_evidence as module

    monkeypatch.setattr(module, "ROOT", tmp_path)
    result = module.verify_m6(LIVE, assertion_ref("critical-deny"), control())
    assert result["status"] == "INTERNAL_ERROR"
    assert result["basis_codes"] == ["M6_VERIFICATION_INTERNAL_ERROR"]
    assert result["coverage_assessment"] is None


def test_persistent_receipt_hash_failure_raises_typed_error(monkeypatch):
    import src.m6_attestation_evidence as module
    from src.evidence_errors import InternalProcessingError

    def fail(_):
        raise TypeError("cannot hash receipt")

    monkeypatch.setattr(module, "evidence_digest", fail)
    with pytest.raises(InternalProcessingError):
        module.verify_m6(LIVE, assertion_ref("critical-deny"), control())


@pytest.mark.parametrize("payload", ["invalid JSON", "[]", '{"files": []}'])
def test_malformed_supplied_manifest_is_evidentiary(tmp_path, payload):
    (tmp_path / "manifest.json").write_text(payload)
    result = verify_m6(tmp_path, assertion_ref("critical-deny"), control())
    assert result["status"] == "EVIDENCE_DEFECT"
    assert result["schema_version"] == "1.0"


def test_invalid_generated_receipt_is_internal(monkeypatch):
    import src.m6_attestation_evidence as module

    monkeypatch.setattr(
        module, "_project", lambda *args: {"incomplete": "generated facts"}
    )
    result, receipt = attest(LIVE, assertion_ref("critical-deny"), control())
    assert receipt["status"] == "INTERNAL_ERROR"
    assert receipt["facts"] is None
    assert result["evaluation_status"] == "INTERNAL_ERROR"
    assert result["finding"] is None


def test_replay_preserves_unconstructable_internal_failure(monkeypatch):
    import src.control_attestation as module
    from src.evidence_errors import InternalProcessingError

    saved, _ = attest(LIVE, assertion_ref("critical-deny"), control())

    def fail(*args, **kwargs):
        raise InternalProcessingError("Fresh internal artifact could not be validated")

    monkeypatch.setattr(module, "attest", fail)
    with pytest.raises(InternalProcessingError):
        module.reconstruct_attestation(saved, LIVE, control())
