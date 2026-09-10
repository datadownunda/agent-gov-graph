"""Deterministic decision-rule fixtures, not empirical evidence of effectiveness."""

from copy import deepcopy
from pathlib import Path
import json

import pytest

from src.control_attestation import adjudicate, attest, validate_attestation
from src.evidence_digest import evidence_digest

ROOT = Path(__file__).resolve().parents[1]


def control():
    return json.loads(
        (ROOT / "experiments/control_attestation/control.json").read_text()
    )


def receipt(
    *,
    decision="DENY",
    effect=False,
    adequate=True,
    ambiguity=False,
    status="VERIFIED",
    **changes
):
    facts = {
        "governance": {
            "evidence_ref": "sha256:g",
            "decision": decision,
            "actor": {"namespace": "agent", "id": "fixture-agent"},
            "action": "read",
            "resource_id": "complaint-789",
            "resource_type": "employee_complaint",
            "observed_at": "2026-09-05T12:00:00Z",
        },
        "reconciliation_result": "CONTRADICTION" if effect else "CONSISTENT",
        "consistent_with_blocking": not effect,
        "target_contract_verified": True,
        "prohibited_effect_established": effect,
        "relevant_correlation_ambiguous": ambiguity,
        "undermining_uncertainty": False,
        "supporting_effect_refs": ["sha256:o"] if effect else [],
        "supporting_correlation_refs": ["sha256:link"] if effect else [],
        "source_refs": ["sha256:g", "sha256:o"] if effect else ["sha256:g"],
    } | changes
    r = {
        "schema_version": "1.0",
        "rule_version": "m6-attestation-verification/1",
        "status": status,
        "control_digest": evidence_digest(control()),
        "reconciliation_ref": "sha256:m6",
        "archive_digest": "sha256:archive",
        "facts": facts,
        "coverage_assessment": {
            "control_digest": evidence_digest(control()),
            "result": "ADEQUATE" if adequate else "UNKNOWN",
            "basis_codes": (
                ["BOUNDED_TARGET_COVERAGE_ADEQUATE"]
                if adequate
                else ["TARGET_COVERAGE_UNKNOWN"]
            ),
            "interval": {
                "start": "2026-09-05T12:00:00Z",
                "end": "2026-09-05T12:00:10Z",
            },
            "support_ref": None,
            "coverage_ref": None,
        },
        "basis_codes": [],
        "dependency_refs": [],
        "limitations": [
            "Fixture verification receipt; demonstrates adjudication semantics only."
        ],
    }
    r["receipt_id"] = evidence_digest(r)
    return r


@pytest.mark.parametrize(
    "r,status,finding",
    [
        (receipt(), "EVALUATED", "CONTROL_EFFECTIVE"),
        (
            receipt(effect=True, adequate=False),
            "EVALUATED",
            "CONTROL_EFFECTIVENESS_EXCEPTION",
        ),
        (
            receipt(adequate=False),
            "INSUFFICIENT_EVIDENCE",
            "CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED",
        ),
        (
            receipt(effect=True, ambiguity=True),
            "INSUFFICIENT_EVIDENCE",
            "CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED",
        ),
        (
            receipt(ambiguity=True),
            "INSUFFICIENT_EVIDENCE",
            "CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED",
        ),
        (receipt(status="EVIDENCE_DEFECT"), "NOT_EVALUABLE", None),
        (receipt(decision="ALLOW"), "NOT_APPLICABLE", None),
        (
            receipt(undermining_uncertainty=True),
            "INSUFFICIENT_EVIDENCE",
            "CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED",
        ),
        (
            receipt(target_contract_verified=False),
            "INSUFFICIENT_EVIDENCE",
            "CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED",
        ),
    ],
)
def test_fixed_rule(r, status, finding):
    a = adjudicate(control(), r)
    assert (a["evaluation_status"], a["finding"]) == (status, finding)
    assert a["scope"]["cardinality"] == "SINGLE_ACTION"
    assert any("consumption" in s for s in a["limitations"])
    validate_attestation(a)


def test_m6_contradiction_or_divergence_is_not_mechanical_exception():
    for state in ["CONTRADICTION", "UNEXPLAINED_DIVERGENCE", "EXPLAINED_DIVERGENCE"]:
        r = receipt(reconciliation_result=state, consistent_with_blocking=False)
        assert (
            adjudicate(control(), r)["finding"]
            == "CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED"
        )


def test_no_execution_success_or_delegation_input_needed_for_exception():
    r = receipt(effect=True)
    assert "execution" not in r["facts"] and "delegation" not in r["facts"]
    assert adjudicate(control(), r)["finding"] == "CONTROL_EFFECTIVENESS_EXCEPTION"


def test_changed_receipt_and_unknown_ground_truth_fields_are_rejected():
    r = receipt()
    r["facts"]["prohibited_effect_established"] = True
    assert adjudicate(control(), r)["evaluation_status"] == "NOT_EVALUABLE"
    r = receipt()
    r["facts"]["bypass"] = True
    r["receipt_id"] = evidence_digest({k: v for k, v in r.items() if k != "receipt_id"})
    assert adjudicate(control(), r)["evaluation_status"] == "NOT_EVALUABLE"


def test_control_mismatch_invalid_control_and_no_mutation():
    c = control()
    r = receipt()
    before = deepcopy((c, r))
    adjudicate(c, r)
    assert (c, r) == before
    c["control_version"] = "2"
    assert adjudicate(c, r)["evaluation_status"] == "NOT_EVALUABLE"
    c["control_type"] = "OTHER"
    assert adjudicate(c, r)["evaluation_status"] == "NOT_EVALUABLE"


@pytest.mark.parametrize(
    "error",
    [
        KeyError("debug-marker"),
        TypeError("debug-marker"),
        ArithmeticError("debug-marker"),
    ],
)
def test_internal_validation_failure_is_not_evidentiary(monkeypatch, caplog, error):
    import src.control_attestation as module

    def fail(_):
        raise error

    monkeypatch.setattr(module, "validate_control", fail)
    result = module.adjudicate(control(), receipt())
    assert result["evaluation_status"] == "INTERNAL_ERROR"
    assert result["finding"] is None
    assert result["schema_version"] == "1.1"
    assert result["coverage_assessment"] is None
    assert result["basis_codes"] == ["ADJUDICATOR_INTERNAL_ERROR"]
    assert "debug-marker" not in json.dumps(result)
    assert "debug-marker" in caplog.text
    validate_attestation(result)


def test_generated_output_failure_uses_fresh_state(monkeypatch):
    import src.control_attestation as module

    original = module.validate_attestation
    seen = []

    def fail_once(value):
        seen.append(deepcopy(value))
        if len(seen) == 1:
            raise ValueError("Generated output validation failed")
        original(value)

    monkeypatch.setattr(module, "validate_attestation", fail_once)
    result = module.adjudicate(control(), receipt(effect=True))
    assert result["evaluation_status"] == "INTERNAL_ERROR"
    assert result["finding"] is None
    assert result["source_evidence_refs"] == []
    assert result["scope"] == {"cardinality": "SINGLE_ACTION"}
    assert result["assertion_id"] == evidence_digest(
        {k: v for k, v in result.items() if k != "assertion_id"}
    )
    assert len(seen) == 2


def test_unconstructable_internal_artifact_raises_typed_error(monkeypatch):
    import src.control_attestation as module
    from src.evidence_errors import InternalProcessingError

    def fail(_):
        raise TypeError("Persistent validator failure")

    monkeypatch.setattr(module, "validate_attestation", fail)
    with pytest.raises(InternalProcessingError) as caught:
        module.adjudicate(control(), receipt())
    assert caught.value.__cause__ is not None


def test_malformed_supplied_receipt_is_still_evidentiary():
    for value in ({}, {"status": "VERIFIED"}, None):
        result = adjudicate(control(), value)
        assert result["evaluation_status"] == "NOT_EVALUABLE"
        assert result["finding"] is None
        assert result["schema_version"] == "1.0"


@pytest.mark.parametrize("stage", ["initial_digest", "output_digest"])
def test_hashing_failure_is_internal_and_fallback_is_fresh(monkeypatch, stage):
    import src.control_attestation as module

    real_digest = module.evidence_digest
    supplied_control, supplied_receipt = control(), receipt()
    failed = False

    def fail_once(value):
        nonlocal failed
        is_output = isinstance(value, dict) and "evaluation_status" in value
        should_fail = stage == "initial_digest" or is_output
        if should_fail and not failed:
            failed = True
            raise TypeError("hashing defect")
        return real_digest(value)

    monkeypatch.setattr(module, "evidence_digest", fail_once)
    result = module.adjudicate(supplied_control, supplied_receipt)
    assert failed
    assert result["evaluation_status"] == "INTERNAL_ERROR"
    assert result["finding"] is None
    assert result["coverage_assessment"] is None
    assert result["assertion_id"] == real_digest(
        {key: value for key, value in result.items() if key != "assertion_id"}
    )


def test_persistent_hash_failure_cannot_manufacture_artifact(monkeypatch):
    import src.control_attestation as module
    from src.evidence_errors import InternalProcessingError

    supplied_control, supplied_receipt = control(), receipt()

    def fail(_):
        raise ArithmeticError("persistent hashing defect")

    monkeypatch.setattr(module, "evidence_digest", fail)
    with pytest.raises(InternalProcessingError):
        module.adjudicate(supplied_control, supplied_receipt)


def test_unexpected_library_validation_failure_is_internal(monkeypatch):
    import src.control_attestation as module
    import jsonschema

    def fail(_):
        raise jsonschema.ValidationError("Unexpected failure on validated input")

    monkeypatch.setattr(module, "validate_control", fail)
    result = module.adjudicate(control(), receipt())
    assert result["evaluation_status"] == "INTERNAL_ERROR"
    assert result["finding"] is None


def test_internal_representation_is_additive_and_cannot_carry_a_finding():
    from src.control_attestation import _internal_attestation
    from src.evidence_errors import EvidenceValidationError

    original = _internal_attestation()
    for change in (
        {"finding": "CONTROL_EFFECTIVE"},
        {"schema_version": "1.0"},
        {"coverage_assessment": {"result": "UNKNOWN"}},
        {"basis_codes": ["EVIDENCE_DEFECT"]},
    ):
        changed = original | change
        changed["assertion_id"] = evidence_digest(
            {key: value for key, value in changed.items() if key != "assertion_id"}
        )
        with pytest.raises(EvidenceValidationError):
            validate_attestation(changed)
    old = adjudicate(control(), receipt())
    old["schema_version"] = "1.1"
    old["assertion_id"] = evidence_digest(
        {key: value for key, value in old.items() if key != "assertion_id"}
    )
    with pytest.raises(EvidenceValidationError):
        validate_attestation(old)
