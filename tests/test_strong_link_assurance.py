from copy import deepcopy
import json
from pathlib import Path
import pytest
from experiments.strong_link_assurance.generate import build, CASES
from experiments.strong_link_assurance.run_experiment import run_worker, verify_frozen
from experiments.strong_link_assurance.score import score


def test_frozen_protocol_and_exact_population():
    assert sum(map(len, CASES.values())) == 26
    assert len(verify_frozen()['tracked_file_hashes']) == 410


@pytest.mark.parametrize('presentation', ['canonical', 'reversed', 'renamed'])
def test_indistinguishable_pair(presentation):
    a, ta = build('controls', 'deny_effect', presentation)
    b, tb = build('copied', 'removed', presentation)
    assert a == b
    assert ta['attempts'] != tb['attempts']


@pytest.mark.parametrize('family,variant', [(f, v) for f, vs in CASES.items() for v in vs])
def test_generator_blinding_and_truth_locations(family, variant):
    evidence, truth = build(family, variant)
    assert set(evidence) == {'rows', 'namespace_observations'}
    assert set(evidence['rows']) == {'governance', 'execution', 'outcome'}
    for pair in truth['covered']:
        assert all(address in truth['attempts'] for address in pair)
    assert 'family' not in evidence and 'expected_control' not in evidence


@pytest.mark.parametrize('variant,expected', [('allow', None), ('deny_effect', 'CONTROL_EFFECTIVENESS_EXCEPTION'), ('blocked', 'CONTROL_EFFECTIVE')])
def test_actual_m7_control_paths(tmp_path, variant, expected):
    evidence, truth = build('controls', variant)
    output, stderr = run_worker(evidence, tmp_path / 'archive')
    assert output.get('status') != 'INTERNAL_ERROR', stderr
    metrics = score(output, truth)
    assert metrics['focus_finding'] == expected
    assert metrics['counts']['false_links'] == 0
    assert metrics['counts']['false_effective'] == 0
    assert metrics['counts']['false_exception'] == 0
    selected = next(v for name, v in output['reconciliation'].items()
                    if name == {'allow': 'allow', 'deny_effect': 'critical-deny', 'blocked': 'blocked-bounded'}[variant])
    assert output['attestations'][selected['assertion_id']]['receipt']['status'] == 'VERIFIED'


def test_scoring_truth_does_not_enter_worker(tmp_path):
    evidence, truth = build('controls', 'deny_effect')
    output, stderr = run_worker(evidence, tmp_path / 'archive')
    assert output.get('status') != 'INTERNAL_ERROR', stderr
    _, replacement_truth = build('copied', 'removed')
    before = deepcopy(output)
    assert score(output, truth)['counts']['false_exception'] == 0
    assert score(output, replacement_truth)['counts']['false_exception'] == 1
    assert output == before
