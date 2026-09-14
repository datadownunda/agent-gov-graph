"""Current v2 conformance is separate from the unchanged historical experiment."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from experiments.m7_scope_gate.accounting import reconcile, render
from experiments.m7_scope_gate.run_conformance import run_worker, FROZEN, ROOT
from experiments.strong_link_assurance.generate import build
from experiments.strong_link_assurance.score import score


def test_accounting_reproduces_saved_ledger_without_mutation():
    directory=ROOT/'experiments/m7_scope_gate/accounting'
    data=reconcile()
    assert data==json.loads((directory/'v4-reconciliation.json').read_text())
    assert render(data)==(directory/'v4-reconciliation.md').read_text()


@pytest.mark.parametrize('variant,expected',[('allow',None),('deny_effect','CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED'),('blocked','CONTROL_EFFECTIVE')])
def test_current_v2_control_paths(tmp_path,variant,expected):
    evidence,truth=build('controls',variant)
    output,stderr=run_worker(evidence,tmp_path/'archive')
    assert output.get('status')!='INTERNAL_ERROR',stderr
    measured=score(output,truth)
    assert measured['focus_finding']==expected
    assert measured['counts']['internal_errors']==0
    if variant=='deny_effect':
        view=output['reconciliation']['critical-deny']
        a=output['attestations'][view['assertion_id']]['attestation']
        assert a['basis_codes']==['NATIVE_IDENTIFIER_NAMESPACE_NOT_ESTABLISHED']
        assert all(p['scope_established'] for p in a['exception_paths'])


def test_identical_worker_inputs_still_produce_identical_decisions(tmp_path):
    a,ta=build('controls','deny_effect')
    b,tb=build('copied','removed')
    assert a==b and ta!=tb
    first,_=run_worker(a,tmp_path/'a')
    second,_=run_worker(b,tmp_path/'b')
    assert first==second
    before=deepcopy(first)
    score(first,ta);score(first,tb)
    assert first==before


def test_namespace_observations_reach_primary_as_declarations_only(tmp_path):
    evidence,truth=build('namespace','pooled')
    output,_=run_worker(evidence,tmp_path/'archive')
    view=output['reconciliation']['critical-deny']
    a=output['attestations'][view['assertion_id']]['attestation']
    assert 'NATIVE_IDENTIFIER_NAMESPACE_CONFLICT' in a['basis_codes']
    assert 'NATIVE_IDENTIFIER_NAMESPACE_NOT_ESTABLISHED' in a['basis_codes']
    assert json.loads((tmp_path/'archive/namespace_observations.json').read_text())==evidence['namespace_observations']


def test_saved_conformance_inputs_truth_scores_and_m6_preserved():
    directory=ROOT/'experiments/m7_scope_gate/results/v1'
    for name in ('decision-inputs.json','scorer-only-truth.json'):
        assert (directory/name).read_bytes()==(FROZEN/name).read_bytes()
    outputs=json.loads((directory/'decisions.json').read_text())
    baseline=json.loads((FROZEN/'decisions.json').read_text())
    truth=json.loads((directory/'scorer-only-truth.json').read_text())
    metrics=json.loads((directory/'metrics.json').read_text())['cases']
    assert len(outputs)==78
    for key,out in outputs.items():
        assert score(out,truth[key])==metrics[key]
        for field in ('records','correlations','reconciliation','verification'):
            assert out[field]==baseline[key][field]
    c=json.loads((directory/'comparison.json').read_text())
    assert c['historical_result']=='FAILED'
    assert c['false_exceptions_before']==18
    assert c['internal_errors']==0
