"""Pre-capture harness tests use a mocked public API; no empirical campaign."""
from copy import deepcopy
import json

import pytest

from experiments.m9b_coverage_substantiation import run_diagnostic as d


def differences(before, after, path=''):
    if isinstance(before, dict) and isinstance(after, dict):
        assert before.keys() == after.keys()
        result = []
        for key in before:
            result.extend(differences(before[key], after[key], path + '/' + key))
        return result
    return [] if before == after else [path]


@pytest.mark.parametrize('case', d.CASES)
def test_one_mutation_preserves_reconciliation_native_and_manifest_integrity(tmp_path, case):
    before = d.inventory(d.SOURCE)
    archive = tmp_path / case
    row = d.prepare_case(d.SOURCE, archive, case)
    assert d.inventory(d.SOURCE) == before
    manifest = json.loads((archive / 'manifest.json').read_text())
    assert all(d.digest(archive / name) == value for name, value in manifest['files'].items())
    original = json.loads((d.SOURCE / d.SUPPORT).read_text())
    supplied = json.loads((archive / d.SUPPORT).read_text())
    if row['mutation']['operation'] == 'replace':
        assert differences(original, supplied) == [row['mutation']['path']]
        assert row['changed_archive_members'] == sorted([d.SUPPORT, 'manifest.json'])
    else:
        assert d.inventory(archive) == before
    assert row['request']['coverage_support'] == (None if case == 'missing_support' else d.SUPPORT)
    if case == 'short_capture':
        records = json.loads((archive / 'reconciliation.json').read_text())
        assertion = next(a for a in records.values() if a['assertion_id'] == supplied['reconciliation_ref'])
        assert supplied['capture']['through'] == assertion['claims']['governance'][0]['observed_at']
    if case == 'snapshot_mismatch':
        assert supplied['capture']['native_file_digest'] != manifest['files']['native/access.jsonl']
    if case == 'unmeasured_clock_basis':
        assert supplied['clocks']['maximum_offset_seconds'] == '0'
        assert supplied['clocks']['basis'] == d.UNMEASURED_BASIS


def fake_attest(calls):
    def fake(archive, assertion_id, control, *, coverage_support, rule_version):
        # Only documented public parameters; no scenario labels passed as input.
        calls.append((archive, assertion_id, deepcopy(control), coverage_support, rule_version))
        return ({'evaluation_status': 'TEST_STUB', 'finding': None},
                {'status': 'TEST_STUB', 'basis_codes': [], 'coverage_assessment': None})
    return fake


def test_request_capture_replay_and_overwrite_refusal(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(d, 'attest', fake_attest(calls))
    output = tmp_path / 'capture'
    result = d.run(output)
    assert len(calls) == 7
    assert [r['case'] for r in result['cases']] == list(d.CASES)
    assert result['empirical_coverage_substantiated'] is False
    assert d.audit(output)['case_count'] == 7
    assert len(calls) == 14
    assert {str(c[0].parents[2]) for c in calls[:7]}.isdisjoint(
        {str(c[0].parents[2]) for c in calls[7:]})
    with pytest.raises(FileExistsError):
        d.run(output)
    with pytest.raises(ValueError, match='inventory changed'):
        (output / 'cases/baseline/receipt.json').write_text('{}')
        d.audit(output)


def test_replay_detects_semantic_disagreement_after_valid_inventory(tmp_path, monkeypatch):
    monkeypatch.setattr(d, 'attest', fake_attest([]))
    output = tmp_path / 'capture'
    d.run(output)
    def changed(*args, **kwargs):
        return ({'evaluation_status': 'DIFFERENT', 'finding': None},
                {'status': 'TEST_STUB', 'basis_codes': [], 'coverage_assessment': None})
    monkeypatch.setattr(d, 'attest', changed)
    with pytest.raises(ValueError, match='replay disagrees'):
        d.audit(output)


def test_failed_capture_preserves_partial_requests_and_does_not_overwrite(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError('test infrastructure failure')
    monkeypatch.setattr(d, 'attest', fail)
    output = tmp_path / 'partial'
    with pytest.raises(RuntimeError):
        d.run(output)
    assert (output / 'cases/baseline/request.json').is_file()
    assert (output / 'manifest.json').exists()
    assert json.loads((output / 'run_status.json').read_text())['status'] == 'NOT_EVALUABLE'
    with pytest.raises(FileExistsError):
        d.run(output)


def test_inventory_rejects_external_symlink(tmp_path):
    (tmp_path / 'escape').symlink_to(d.CONTROL)
    with pytest.raises(ValueError, match='Symlinks'):
        d.inventory(tmp_path)


def test_replay_rejects_execution_freeze_drift(tmp_path, monkeypatch):
    monkeypatch.setattr(d, 'attest', fake_attest([]))
    output = tmp_path / 'capture'
    d.run(output)
    original_lock = d.execution_lock
    monkeypatch.setattr(d, 'execution_lock', lambda: {**original_lock(), 'implementation_hashes': {}})
    with pytest.raises(ValueError, match='execution freeze'):
        d.audit(output)
