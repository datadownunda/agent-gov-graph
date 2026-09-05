import json
import os
from copy import deepcopy

import pytest

from src import complaint_runtime as runtime
from src.authority_reconstruction import reconstruct_authority
from test_authority_resolver import T, record, registry


def decide(tmp_path, monkeypatch, source, opa_at=T, bypass=False):
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps(source))
    monkeypatch.setattr(runtime, 'utc_now', lambda: T)
    def evaluate(data):
        allowed = 'complaint-456' in data['authorized_resource_ids']
        decision = {'allowed': allowed, 'decision': 'ALLOW' if allowed else 'DENY',
                    'policy': 'employee_complaint_access', 'policy_version': '1.0', 'reasons': []}
        return decision, {'input': data, 'result': decision, 'timestamp': opa_at, 'decision_id': 'test'}
    monkeypatch.setattr(runtime, 'evaluate_policy_with_decision_log', evaluate)
    monkeypatch.setattr(runtime, 'read_complaint', lambda resource_id, **kw: {'id': resource_id})
    result = runtime._governed_action('complaint-456', run_id='test', step_id='1', actor_id='agent',
        governance_log_path=tmp_path/'governance.jsonl', execution_log_path=tmp_path/'execution.jsonl',
        opa_decision_log_path=tmp_path/'opa.jsonl', authority_path=path, bypass_enforcement=bypass)
    events = [json.loads(s) for s in (tmp_path/'governance.jsonl').read_text().splitlines()] if (tmp_path/'governance.jsonl').exists() else []
    return result, events, path


def test_historical_reconstruction_ignores_mutated_current_registry(tmp_path, monkeypatch):
    result, events, path = decide(tmp_path, monkeypatch, registry(record()))
    assert result['resource_returned'] is True
    before = reconstruct_authority(events[0], tmp_path/'authority_history')
    assert before['status'] == 'VERIFIED'
    path.write_text(json.dumps(registry(record(authority_version='2', permitted_scopes=[]))))
    assert reconstruct_authority(events[0], tmp_path/'authority_history') == before
    # No embedded result can substitute for the independent archive.
    archive = tmp_path/'authority_history'/events[0]['context']['authority_binding']['revision']['file']
    archive.unlink()
    assert reconstruct_authority(events[0], tmp_path/'authority_history')['status'] == 'INSUFFICIENT_EVIDENCE'


@pytest.mark.parametrize('source,status', [
    (registry(), 'INSUFFICIENT_EVIDENCE'),
    (registry(record(), record(authority_record_id='other', permitted_scopes=[])), 'CONFLICT'),
])
def test_unresolved_authority_never_calls_policy(tmp_path, monkeypatch, source, status):
    path = tmp_path/'registry.json'
    path.write_text(json.dumps(source))
    monkeypatch.setattr(runtime, 'utc_now', lambda: T)
    monkeypatch.setattr(runtime, 'evaluate_policy_with_decision_log', lambda *a: pytest.fail('OPA called'))
    result = runtime._governed_action('complaint-456', run_id='test', step_id='1', actor_id='agent',
        authority_path=path, governance_log_path=tmp_path/'governance.jsonl')
    assert result['authority_status'] == status
    assert result['policy_decision'] is None
    assert result['resource_returned'] is False
    assert (tmp_path/'authority_resolution.jsonl').exists()


@pytest.mark.parametrize('later', [T, '2026-09-05T12:00:00.000000002Z'])
def test_boundary_change_blocks_even_legacy_bypass(tmp_path, monkeypatch, later):
    end = '2026-09-05T12:00:00.000000001Z'
    source = registry(record(valid_to=end), record(authority_version='2', valid_from=end, permitted_scopes=[]))
    result, events, _ = decide(tmp_path, monkeypatch, source, opa_at=later, bypass=True)
    changed = later != T
    assert result['authority_status'] == ('TEMPORAL_BOUNDARY_AMBIGUITY' if changed else 'RESOLVED')
    assert result['resource_returned'] is (not changed)
    assert result['policy_decision'] == 'ALLOW'
    audit = reconstruct_authority(events[0], tmp_path/'authority_history')
    assert audit['status'] == ('TEMPORAL_BOUNDARY_AMBIGUITY' if changed else 'VERIFIED')


def test_tampered_binding_and_archive(tmp_path, monkeypatch):
    _, events, _ = decide(tmp_path, monkeypatch, registry(record()))
    event = deepcopy(events[0])
    event['context']['authority_binding']['at_resolution']['record_refs'] = []
    assert reconstruct_authority(event, tmp_path/'authority_history')['status'] == 'CONTRADICTED'
    ref = events[0]['context']['authority_binding']['revision']
    (tmp_path/'authority_history'/ref['file']).write_text('{}')
    assert reconstruct_authority(events[0], tmp_path/'authority_history')['status'] == 'EVIDENCE_DEFECT'


def test_legacy_event_insufficient():
    assert reconstruct_authority({'context': {}}, 'nonexistent')['status'] == 'INSUFFICIENT_EVIDENCE'


@pytest.mark.parametrize('opa_at', [None, 'bad', 42, '2026-09-05T11:59:59Z'])
def test_missing_bad_or_regressing_opa_clock_blocks(tmp_path, monkeypatch, opa_at):
    result, events, _ = decide(tmp_path, monkeypatch, registry(record()), opa_at=opa_at)
    assert result['authority_status'] == 'EVIDENCE_DEFECT'
    assert result['policy_decision'] == 'ALLOW'
    assert result['resource_returned'] is False
    assert reconstruct_authority(events[0], tmp_path/'authority_history')['status'] == 'EVIDENCE_DEFECT'


def test_explicit_revocation_reaches_policy_deny(tmp_path, monkeypatch):
    result, events, _ = decide(tmp_path, monkeypatch, registry(record(permitted_scopes=[])))
    assert result['authority_status'] == 'RESOLVED'
    assert result['policy_decision'] == 'DENY'
    assert result['resource_returned'] is False
    assert reconstruct_authority(events[0], tmp_path/'authority_history')['status'] == 'VERIFIED'


def test_equivalent_permissions_new_record_at_boundary_is_not_silently_selected(tmp_path, monkeypatch):
    end = '2026-09-05T12:00:00.000000001Z'
    result, events, _ = decide(tmp_path, monkeypatch,
        registry(record(valid_to=end), record(authority_version='2', valid_from=end)), opa_at=end)
    assert result['authority_status'] == 'TEMPORAL_BOUNDARY_AMBIGUITY'
    assert not result['resource_returned']


def test_future_grant_does_not_retroactively_fill_history(tmp_path, monkeypatch):
    source = registry(record(valid_from='2026-09-06T00:00:00Z'))
    result, events, path = decide(tmp_path, monkeypatch, source)
    assert result['authority_status'] == 'INSUFFICIENT_EVIDENCE'
    assert result['policy_decision'] is None
    assert not events


def test_binding_timestamps_preserved_separately_and_required(tmp_path, monkeypatch):
    import jsonschema
    from src.governance_event import validate_event
    later = '2026-09-05T12:00:01.123456789Z'
    _, events, _ = decide(tmp_path, monkeypatch, registry(record()), opa_at=later)
    event = events[0]
    binding = event['context']['authority_binding']
    assert binding['authority_resolution_at'] == T
    assert binding['opa_decision_at'] == later
    assert 'decision_effective_at' not in binding
    validate_event(event)
    for field in ['authority_resolution_at', 'opa_decision_at', 'revision', 'rule_version']:
        bad = deepcopy(event)
        del bad['context']['authority_binding'][field]
        with pytest.raises(jsonschema.ValidationError):
            validate_event(bad)


def test_later_closed_revision_does_not_replace_bound_open_revision(tmp_path, monkeypatch):
    from src.authority_resolver import preserve_revision, resolve_authority
    _, events, path = decide(tmp_path, monkeypatch, registry(record()))
    original = reconstruct_authority(events[0], tmp_path/'authority_history')
    new = registry(record(authority_version='2', valid_to='2026-09-06T00:00:00Z'),
                   record(authority_version='3', valid_from='2026-09-06T00:00:00Z', permitted_scopes=[]))
    new['source_version'] = '2'
    path.write_text(json.dumps(new))
    preserve_revision(new, tmp_path/'authority_history')
    assert resolve_authority('agent', effective_at='2026-09-06T00:00:00Z', registry_revision=new)['basis']['permitted_scopes'] == []
    assert reconstruct_authority(events[0], tmp_path/'authority_history') == original


def test_unknown_rule_is_not_verified(tmp_path, monkeypatch):
    _, events, _ = decide(tmp_path, monkeypatch, registry(record()))
    events[0]['context']['authority_binding']['rule_version'] = 'unknown-rule'
    assert reconstruct_authority(events[0], tmp_path/'authority_history')['status'] == 'EVIDENCE_DEFECT'


@pytest.mark.skipif(os.environ.get('RUN_FOREIGN_OPA') != '1', reason='requires Docker/OPA')
def test_native_opa_decision_reconstructs_after_current_registry_mutation(tmp_path):
    """Critical mutation test with a real native OPA decision timestamp."""
    source_path = tmp_path/'registry.json'
    source_path.write_text(json.dumps(registry(record(valid_from='2000-01-01T00:00:00Z'))))
    result = runtime._governed_action('complaint-456', run_id='native-m4', step_id='1', actor_id='agent',
        authority_path=source_path, governance_log_path=tmp_path/'governance.jsonl',
        execution_log_path=tmp_path/'execution.jsonl', opa_decision_log_path=tmp_path/'opa.jsonl')
    assert result['authority_status'] == 'RESOLVED'
    assert result['resource_returned'] is True
    event = json.loads((tmp_path/'governance.jsonl').read_text())
    opa = json.loads((tmp_path/'opa.jsonl').read_text())
    assert opa['type'] == 'openpolicyagent.org/decision_logs'
    assert event['context']['authority_binding']['opa_decision_at'] == opa['timestamp']
    before = reconstruct_authority(event, tmp_path/'authority_history')
    assert before['status'] == 'VERIFIED'
    source_path.write_text(json.dumps(registry(record(permitted_scopes=[], authority_version='2'))))
    assert reconstruct_authority(event, tmp_path/'authority_history') == before
    source_path.unlink()
    assert reconstruct_authority(event, tmp_path/'authority_history') == before


def test_embedded_governance_contract_matches_authority_contract():
    from src.authority_resolver import PROJECT_ROOT, load_authority_source
    event_schema = load_authority_source(PROJECT_ROOT/'schemas/governance_decision_event.schema.json')
    authority_schema = load_authority_source(PROJECT_ROOT/'schemas/authority_resolution.schema.json')
    assert event_schema['properties']['context']['properties']['authority_binding'] == authority_schema
