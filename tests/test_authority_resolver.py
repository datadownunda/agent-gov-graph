"""Deterministic valid-time tests; no model/provider calls."""
from copy import deepcopy

import pytest

from src.authority_resolver import resolve_authority, preserve_revision, load_preserved_revision

T = "2026-09-05T12:00:00Z"


def record(**overrides):
    value = {"authority_record_id": "grant", "authority_version": "1", "principal": "agent",
             "roles": ["hr_investigator"], "permitted_scopes": [
                 {"action": "read", "resource_type": "employee_complaint", "resource_ids": ["complaint-456"]}],
             "valid_from": "2026-09-05T00:00:00Z", "valid_to": None}
    return value | overrides


def registry(*records):
    return {"schema_version": "2.0", "source_id": "test-registry", "source_version": "1", "records": list(records)}


def resolve(*records, at=T):
    return resolve_authority("agent", effective_at=at, registry_revision=registry(*records))


@pytest.mark.parametrize("start,end,status", [
    ("2026-09-05T00:00:00Z", None, "RESOLVED"),
    (T, None, "RESOLVED"),
    ("2026-09-05T00:00:00Z", T, "INSUFFICIENT_EVIDENCE"),
    ("2026-09-06T00:00:00Z", None, "INSUFFICIENT_EVIDENCE"),
])
def test_validity_boundaries(start, end, status):
    assert resolve(record(valid_from=start, valid_to=end))["status"] == status


def test_future_grant_expiry_missing_and_revocation():
    assert resolve()["status"] == "INSUFFICIENT_EVIDENCE"
    old = record(valid_to="2026-09-06T00:00:00Z")
    revoked = record(authority_version="2", valid_from="2026-09-06T00:00:00Z", permitted_scopes=[])
    assert resolve(old, revoked)["basis"]["permitted_scopes"]
    assert resolve(old, revoked, at="2026-09-06T00:00:00Z")["basis"]["permitted_scopes"] == []


def test_equivalent_overlap_retains_all_support_and_order_is_irrelevant():
    a, b = record(), record(authority_record_id="other")
    result = resolve(a, b)
    assert result["status"] == "RESOLVED"
    assert len(result["record_refs"]) == 2
    assert result == resolve(b, a)
    assert len(resolve(a, deepcopy(a))["record_refs"]) == 1


def test_conflicting_overlap_and_identity_collision():
    assert resolve(record(), record(authority_record_id="other", permitted_scopes=[]))["status"] == "CONFLICT"
    assert resolve(record(), record(permitted_scopes=[]))["status"] == "EVIDENCE_DEFECT"


@pytest.mark.parametrize("overrides", [
    {"valid_from": "bad"}, {"valid_from": "2026-09-05T00:00:00"},
    {"valid_to": "2026-09-04T00:00:00Z"}, {"principal": ""}, {"roles": "admin"},
])
def test_bad_record_is_not_permission_denial(overrides):
    assert resolve(record(**overrides))["status"] == "EVIDENCE_DEFECT"


def test_offsets_and_nanosecond_boundary():
    assert resolve(record(), at="2026-09-05T08:00:00-04:00") == resolve(record()) | {"effective_at": "2026-09-05T08:00:00-04:00"}
    a = record(valid_to="2026-09-05T12:00:00.000000002Z")
    assert resolve(a, at="2026-09-05T12:00:00.000000001Z")["status"] == "RESOLVED"
    assert resolve(a, at="2026-09-05T12:00:00.000000002Z")["status"] == "INSUFFICIENT_EVIDENCE"


def test_preservation_idempotence_and_integrity(tmp_path):
    source = registry(record())
    ref = preserve_revision(source, tmp_path)
    assert preserve_revision(source, tmp_path) == ref
    assert load_preserved_revision(ref, tmp_path) == source
    path = tmp_path / ref["file"]
    path.write_text('{}')
    with pytest.raises(ValueError, match="digest"):
        load_preserved_revision(ref, tmp_path)
    with pytest.raises(ValueError):
        preserve_revision(source, tmp_path)


def test_scope_adapter_does_not_cross_action_or_resource_type():
    from src.authority_resolver import policy_authority
    a = record(permitted_scopes=[
        {"action": "read", "resource_type": "employee_complaint", "resource_ids": ["complaint-456"]},
        {"action": "export", "resource_type": "employee_complaint", "resource_ids": ["complaint-789"]},
        {"action": "read", "resource_type": "other", "resource_ids": ["other-id"]}])
    assert policy_authority(resolve(a), 'read', 'employee_complaint')['authorized_resource_ids'] == ['complaint-456']
    assert policy_authority(resolve(a), 'export', 'employee_complaint')['authorized_resource_ids'] == ['complaint-789']
    with pytest.raises(ValueError):
        policy_authority(resolve(), 'read', 'employee_complaint')


@pytest.mark.parametrize('timestamp', ['bad', '2026-09-05T00:00:00', None, 42])
def test_bad_effective_at_is_explicit_defect(timestamp):
    assert resolve(record(), at=timestamp)['status'] == 'EVIDENCE_DEFECT'


def test_archive_rejects_reference_path_and_source_substitution(tmp_path):
    ref = preserve_revision(registry(record()), tmp_path)
    for changed in [ref | {'file': '../registry.json'}, ref | {'source_version': 'other'}]:
        with pytest.raises(ValueError):
            load_preserved_revision(changed, tmp_path)
