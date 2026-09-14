"""Explicit context routing for the unchanged M9 historical-custody tests."""
from pathlib import Path

import pytest


@pytest.fixture(scope='session')
def m9_historical_root(tmp_path_factory):
    from experiments.identifier_withholding_verification import reconstruct_history

    return reconstruct_history(tmp_path_factory.mktemp('m9-custody') / 'baseline')


@pytest.fixture(autouse=True)
def m9_historical_test_context(request, monkeypatch):
    historical_tests = {
        'test_frozen_protocol_and_population',
        'test_process_truth_isolation_and_replay',
        'test_protocol_and_baseline_tamper_fail_before_execution',
    }
    if (Path(str(request.node.path)) != Path(__file__).parent / 'test_identifier_withholding.py'
            or request.node.originalname not in historical_tests):
        return
    from experiments.identifier_withholding import run_experiment as exp

    root = request.getfixturevalue('m9_historical_root')
    # Only filesystem context changes. The exact verifier and all assertions run;
    # the worker subprocess loads the reconstructed historical source modules.
    monkeypatch.setattr(exp, 'ROOT', root)
    monkeypatch.setattr(exp, 'HERE', root / 'experiments/identifier_withholding')
    monkeypatch.setattr(exp, 'LIVE', root / 'experiments/target_outcome/results/v1')


@pytest.fixture(scope='session')
def strong_link_historical_root(tmp_path_factory):
    from experiments.m7_scope_gate.run_conformance import historical_checkout
    return historical_checkout(tmp_path_factory.mktemp('strong-link-custody') / 'baseline')


@pytest.fixture(autouse=True)
def strong_link_historical_test_context(request, monkeypatch):
    historical_tests = {'test_frozen_protocol_and_exact_population',
                        'test_actual_m7_control_paths', 'test_scoring_truth_does_not_enter_worker'}
    if (Path(str(request.node.path)) != Path(__file__).parent / 'test_strong_link_assurance.py'
            or request.node.originalname not in historical_tests):
        return
    from experiments.strong_link_assurance import run_experiment as exp
    root = request.getfixturevalue('strong_link_historical_root')
    # Original baseline hash checks and worker execute in exact b809378 context.
    # Current v2 behavior is tested separately by test_m7_scope_gate_conformance.
    monkeypatch.setattr(exp, 'ROOT', root)
    monkeypatch.setattr(exp, 'HERE', root / 'experiments/strong_link_assurance')
