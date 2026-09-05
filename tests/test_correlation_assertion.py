import copy

import pytest
import jsonschema

from src.correlation_assertion import composite_assertions, native_assertions, validate_assertion


def record(ref, **extra):
    return {"evidence_ref": ref, "actor": "alice", "action": "read", "resource_id": "c1",
            "resource_type": "complaint", "observed_at": "2026-09-05T12:00:00Z", **extra}


def native(left, right, **kwargs):
    return native_assertions(left, right, identifier_field="decision_id", namespace="opa.example",
                             issuer="OPA instance A (caller declaration)", **kwargs)


def test_composite_link_is_reviewable_and_valid():
    assertions = composite_assertions([record("o")], [record("j")], window_seconds=2)
    a = assertions[0]
    validate_assertion(a)
    assert a["result"]["state"] == "LINKED"
    assert a["correlation_method"] == "EXACT_COMPOSITE_LINKAGE"
    assert a["candidate_population"]["scope"] == "SUPPLIED_SNAPSHOT_ONLY"
    assert a["evidence_coverage"]["completeness"] == "UNKNOWN"
    assert a["time_assumptions"]["clock_skew_verified"] is False
    assert len(a["signals_used"]) == 5
    assert a["limitations"]


def test_many_to_one_exposes_reverse_competitors():
    a = composite_assertions([record("o1"), record("o2")], [record("j")], window_seconds=2)[0]
    assert a["result"]["state"] == "AMBIGUOUS"
    assert len(a["competing_candidates"][0]["reverse_candidate_refs"]) == 2


def test_unmatched_is_not_contradicted_and_defect_is_insufficient():
    assertions = composite_assertions([record("o")], [record("j", actor="bob")], window_seconds=2)
    assert {a["result"]["state"] for a in assertions} == {"UNMATCHED"}
    assertions = composite_assertions([record("o", observed_at="bad")], [], window_seconds=2)
    assert assertions[0]["result"]["state"] == "INSUFFICIENT_EVIDENCE"


def test_native_link_and_explicit_invariant_contradiction():
    left, right = record("o", decision_id="native-1"), record("j", decision_id="native-1", actor="bob")
    assert native([left], [right])[0]["result"]["state"] == "LINKED"
    a = native([left], [right], required_equal_fields=("actor",))[0]
    assert a["result"]["state"] == "CONTRADICTED"
    assert a["result"]["conflicts"][0]["field"] == "actor"
    validate_assertion(a)


def test_native_missing_and_duplicate_are_not_links():
    assert native([record("o")], [record("j")])[0]["result"]["state"] == "INSUFFICIENT_EVIDENCE"
    a = native([record("o", decision_id="d")],
               [record("j1", decision_id="d"), record("j2", decision_id="d")])[0]
    assert a["result"]["state"] == "AMBIGUOUS"


def test_stable_assertion_identity_and_no_mutation():
    left, right = [record("o1"), record("o2")], [record("j")]
    before = copy.deepcopy((left, right))
    a = composite_assertions(left, right, window_seconds=2)
    assert a == composite_assertions(left[::-1], right * 2, window_seconds=2)
    assert (left, right) == before
    assert a[0]["assertion_id"] != composite_assertions(left, right, window_seconds=3)[0]["assertion_id"]


def test_schema_rejects_missing_review_context_and_scores():
    a = composite_assertions([record("o")], [], window_seconds=2)[0]
    del a["time_assumptions"]
    with pytest.raises(jsonschema.ValidationError):
        validate_assertion(a)
    a = composite_assertions([record("o")], [], window_seconds=2)[0]
    a["confidence"] = 0.99
    with pytest.raises(jsonschema.ValidationError):
        validate_assertion(a)


def test_method_output_preserves_baseline_and_declared_coverage():
    from src.evidence_correlation import correlate
    left, right = [record("o")], [record("j")]
    coverage = {"completeness": "PARTIAL", "basis": "Operator reports dropped journal records",
                "interval_start": None, "interval_end": None}
    assertions = composite_assertions(left, right, window_seconds=2, coverage=coverage)
    assert [a["method_output"] for a in assertions] == correlate(left, right, window_seconds=2)
    assert assertions[0]["evidence_coverage"] == coverage


def test_native_missing_invariant_is_insufficient_not_contradiction():
    a = native([{"evidence_ref": "o", "decision_id": "d"}],
               [{"evidence_ref": "j", "decision_id": "d"}], required_equal_fields=("actor",))[0]
    assert a["result"]["state"] == "INSUFFICIENT_EVIDENCE"


def test_unresolved_reference_and_modified_assertion_are_rejected():
    a = composite_assertions([record("o")], [], window_seconds=2)[0]
    a["focus"]["evidence_ref"] = "absent"
    with pytest.raises(ValueError, match="unresolved"):
        validate_assertion(a)
    a = composite_assertions([record("o")], [], window_seconds=2)[0]
    a["limitations"].append("edited")
    with pytest.raises(ValueError, match="assertion_id"):
        validate_assertion(a)
