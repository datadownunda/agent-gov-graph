"""Custody-context repair and separately labelled current-source compatibility."""
import json
from pathlib import Path
import subprocess

import pytest

from experiments import identifier_withholding_verification as verification


def test_historical_custody_runs_original_audit(m9_historical_root):
    receipt = verification.historical_custody(m9_historical_root)
    assert receipt['verification_kind'] == 'HISTORICAL_CUSTODY'
    assert receipt['audit']['status'] == 'VERIFIED'
    assert receipt['audit']['claim_demonstrated'] is False
    freeze = json.loads((m9_historical_root / 'experiments/identifier_withholding/freeze.json').read_text())
    assert len(freeze['baseline_files']) == 292
    assert all(verification.digest(m9_historical_root / name) == expected
               for name, expected in freeze['baseline_files'].items())
    assert not (m9_historical_root / '.git').exists()


@pytest.mark.parametrize('member', ['docs/control-effectiveness-attestation.md',
                                   'src/evidence_correlation.py',
                                   'tests/test_runtime_reconciler.py.save'])
def test_historical_inventory_still_rejects_changes(m9_historical_root, member):
    path = m9_historical_root / member
    original = path.read_bytes()
    try:
        path.write_bytes(original + b'\nchanged\n')
        with pytest.raises(subprocess.CalledProcessError) as error:
            verification.historical_custody(m9_historical_root)
        assert 'Preserved baseline changed: ' + member in error.value.stderr
    finally:
        path.write_bytes(original)


def test_current_compatibility_is_separate_from_custody():
    from experiments.identifier_withholding import run_experiment as exp

    assert exp.ROOT == verification.ROOT
    with pytest.raises(ValueError, match='Preserved baseline changed'):
        exp.verify_frozen()
    receipt = verification.current_compatibility()
    assert receipt['verification_kind'] == 'CURRENT_CHECKOUT_COMPATIBILITY_ONLY'
    assert set(receipt['byte_identical_files']) == {
        'decision-inputs.json', 'scorer-only-truth.json', 'decisions.json', 'results.json'}
    assert not receipt['claim_demonstrated']


def test_compatibility_rejects_dependency_change(monkeypatch):
    original = verification.digest
    target = verification.ROOT / 'src/evidence_correlation.py'
    monkeypatch.setattr(verification, 'digest', lambda p: 'changed' if p == target else original(p))
    with pytest.raises(ValueError, match='Current execution dependency differs'):
        verification.current_compatibility()


def test_fixture_rejects_changed_save_before_reconstruction(tmp_path, monkeypatch):
    original = verification.digest
    target = verification.FIXTURE / 'test_runtime_reconciler.py.save'
    monkeypatch.setattr(verification, 'digest', lambda p: 'changed' if p == target else original(p))
    with pytest.raises(ValueError, match='Historical save file changed'):
        verification.reconstruct_history(tmp_path / 'baseline')
