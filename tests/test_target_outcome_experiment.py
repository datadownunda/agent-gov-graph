import ast
import json
from pathlib import Path
import pytest
from src import complaint_runtime as runtime

ROOT=Path(__file__).resolve().parents[1]


def test_client_does_not_import_agg_or_manufacture_native_id():
    p=ROOT/'experiments/target_outcome/http_client.py'
    tree=ast.parse(p.read_text())
    imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert not any(x.startswith('src') for x in imports)
    assert "getheader('X-Request-ID')" in p.read_text()
    assert '/evidence/' not in p.read_text()


@pytest.mark.parametrize('allowed',[True,False])
def test_optional_executor_obeys_existing_gate(tmp_path,monkeypatch,allowed):
    called=[]
    def opa(data):
        decision={'allowed':allowed,'decision':'ALLOW' if allowed else 'DENY','policy':'employee_complaint_access','policy_version':'1.0','reasons':[]}
        return decision,{'timestamp':data['authority_resolution_at'],'result':decision,'input':data}
    monkeypatch.setattr(runtime,'evaluate_policy_with_decision_log',opa)
    def execute(resource_id,**kw):
        called.append((resource_id,kw));return {'id':resource_id}
    runtime.governed_action('complaint-789',action='read',actor_id='complaint-review-agent',run_id='r',step_id='s',
        emit=lambda *a:None,governance_log_path=tmp_path/'g.jsonl',execution_log_path=tmp_path/'e.jsonl',
        opa_decision_log_path=tmp_path/'opa.jsonl',executor=execute)
    assert [c[0] for c in called]==(['complaint-789'] if allowed else [])


def test_preserved_live_experiment_replays_and_ground_truth_is_not_input(tmp_path):
    import shutil
    from experiments.target_outcome.run_experiment import audit,derive
    source=ROOT/'experiments/target_outcome/results/v1'
    result=audit(source)
    assert result['status']=='VERIFIED'
    assert result['results']['critical-deny']=='CONTRADICTION'
    assert result['results']['execution-withheld']=='INSUFFICIENT_EVIDENCE'
    shutil.copytree(source,tmp_path/'copy')
    before=derive(tmp_path/'copy')[2]
    (tmp_path/'copy/ground_truth.json').write_text('{"false_ground_truth":true}')
    assert derive(tmp_path/'copy')[2]==before


def test_live_manifest_detects_tamper(tmp_path):
    import shutil
    from experiments.target_outcome.run_experiment import audit
    shutil.copytree(ROOT/'experiments/target_outcome/results/v1',tmp_path/'copy')
    (tmp_path/'copy/native/access.jsonl').write_text('{}\n')
    with pytest.raises(ValueError,match='Changed evidence'):
        audit(tmp_path/'copy')
