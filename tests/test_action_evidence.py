import json
import pytest
from src.target_outcome_evidence import ingest_nginx
from src.action_evidence import verify_location

CONFIG = {'target_id':'complaints-static-v1', 'identity_namespace':'nginx-basic:complaints',
          'basic_auth_required':True, 'resources':{'/complaints/complaint-456.json':
          {'id':'complaint-456','type':'employee_complaint'}}}


def native(**changes):
    return dict(request_id='abc', request_method='GET', request_uri='/complaints/complaint-456.json',
                status=200, body_bytes_sent=120, request_completion='OK', remote_user='reader',
                msec='1788609601.000', request_time='0.001', **changes)


def ingest(tmp_path, record):
    p = tmp_path/'access.jsonl'
    p.write_text(json.dumps(record)+'\n')
    return ingest_nginx(p, root=tmp_path, target=CONFIG)[0]


def test_native_effect_and_original_bytes(tmp_path):
    r = ingest(tmp_path, native())
    assert r['target_outcome'] == 'REPRESENTATION_SERVED'
    assert r['actor'] == {'namespace':'nginx-basic:complaints','id':'reader'}
    assert r['observed_at'] != r['ingested_at']
    assert verify_location(r, tmp_path)
    assert ingest_nginx(tmp_path/'access.jsonl', root=tmp_path, target=CONFIG)[0]['evidence_ref'] == r['evidence_ref']
    (tmp_path/'access.jsonl').write_text('{}\n')
    assert not verify_location(r, tmp_path)


@pytest.mark.parametrize('change', [dict(request_method='HEAD'), dict(status=201), dict(status=401),
    dict(body_bytes_sent=0), dict(request_completion=''), dict(remote_user=''),
    dict(request_uri='/unknown'), dict(request_uri='/complaints/complaint-456.json?x=1')])
def test_generic_http_success_is_not_effect(tmp_path, change):
    raw = native(); raw.update(change)
    assert ingest(tmp_path, raw)['target_outcome'] != 'REPRESENTATION_SERVED'


@pytest.mark.parametrize('change', [dict(msec='bad'), dict(body_bytes_sent=-1), dict(status='garbage')])
def test_native_defect(tmp_path, change):
    raw=native(); raw.update(change)
    assert ingest(tmp_path, raw)['defects']


def test_malformed_governance_and_execution_are_defects(tmp_path):
    from src.action_evidence import ingest_governance,ingest_execution
    p=tmp_path/'bad.jsonl';p.write_text('{"subject":7,"context":8,"decision":false}\nnot json\n')
    assert all(r['defects'] for r in ingest_governance(p,root=tmp_path))
    assert all(r['defects'] for r in ingest_execution(p,root=tmp_path))
