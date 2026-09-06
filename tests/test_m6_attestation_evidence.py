"""Verification of preserved evidence; fixtures are explicitly synthetic."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from src.control_attestation import attest, reconstruct_attestation
from src.m6_attestation_evidence import verify_m6
from src.evidence_digest import evidence_digest

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / 'experiments/target_outcome/results/v1'


def control():
    return json.loads((ROOT / 'experiments/control_attestation/control.json').read_text())


def assertion_ref(name):
    return json.loads((LIVE / 'reconciliation.json').read_text())[name]['assertion_id']


def test_live_exception_and_abstention_and_not_applicable():
    expected={'critical-deny':'CONTROL_EFFECTIVENESS_EXCEPTION',
              'blocked-bounded':'CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED',
              'blocked-deny':'CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED',
              'execution-withheld':'CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED', 'allow':None}
    for name,finding in expected.items():
        a,r=attest(LIVE,assertion_ref(name),control())
        assert r['status']=='VERIFIED'
        assert a['finding']==finding
        if name=='allow':assert a['evaluation_status']=='NOT_APPLICABLE'
        if name=='blocked-bounded':
            assert r['coverage_assessment']['result']=='INADEQUATE'
            assert 'CONTROL_OBSERVATION_HORIZON_INADEQUATE' in r['coverage_assessment']['basis_codes']
        assert reconstruct_attestation(a,LIVE,control())['status']=='VERIFIED'


def test_no_scenario_ground_truth_bypass_or_filenames_in_adjudication_facts():
    r=verify_m6(LIVE,assertion_ref('critical-deny'),control())
    payload=json.dumps(r)
    for forbidden in ('critical-deny','ground_truth','CLIENT_FINALIZATION_FAILED','run_id','bypass','native/access','response_body_bytes_received'):
        assert forbidden not in payload


@pytest.mark.parametrize('member,remove', [('native/access.jsonl',False),('native/access.jsonl',True),
    ('identity_mapping.json',False),('blocked_coverage.json',False),('nginx.conf',False),
    ('authority_history/601887eae502d25c9e049bd6458719785e376bb82c253a4abb656e2e387232ca.json',False)])
def test_tamper_and_unavailable_evidence(tmp_path,member,remove):
    shutil.copytree(LIVE,tmp_path/'archive');p=tmp_path/'archive'/member
    if remove:p.unlink()
    else:p.write_text('{}\n')
    a,_=attest(tmp_path/'archive',assertion_ref('critical-deny'),control())
    assert a['evaluation_status']==('INSUFFICIENT_EVIDENCE' if remove else 'NOT_EVALUABLE')


def test_rehashed_forged_m6_finding_rejected_by_replay(tmp_path):
    shutil.copytree(LIVE,tmp_path/'archive');p=tmp_path/'archive'
    data=json.loads((p/'reconciliation.json').read_text())
    a=data['blocked-bounded'];a['result']='CONTRADICTION'
    a['assertion_id']=evidence_digest({k:v for k,v in a.items() if k!='assertion_id'})
    (p/'reconciliation.json').write_text(json.dumps(data))
    m=json.loads((p/'manifest.json').read_text())
    m['files']['reconciliation.json']='sha256:'+hashlib.sha256((p/'reconciliation.json').read_bytes()).hexdigest()
    (p/'manifest.json').write_text(json.dumps(m))
    assert attest(p,a['assertion_id'],control())[0]['evaluation_status']=='NOT_EVALUABLE'


def test_attestation_tamper_and_source_no_mutation():
    before={p:p.read_bytes() for p in LIVE.rglob('*') if p.is_file()}
    a,_=attest(LIVE,assertion_ref('critical-deny'),control())
    a['finding']='CONTROL_EFFECTIVE'
    assert reconstruct_attestation(a,LIVE,control())['status']=='EVIDENCE_DEFECT'
    assert all(p.read_bytes()==b for p,b in before.items())


def test_changed_ground_truth_cannot_change_adjudication(tmp_path):
    shutil.copytree(LIVE,tmp_path/'archive');p=tmp_path/'archive'
    before=attest(p,assertion_ref('critical-deny'),control())[0]
    (p/'ground_truth.json').write_text('{"bypass":false,"expected":"CONTROL_EFFECTIVE"}\n')
    m=json.loads((p/'manifest.json').read_text())
    m['files']['ground_truth.json']='sha256:'+hashlib.sha256((p/'ground_truth.json').read_bytes()).hexdigest()
    (p/'manifest.json').write_text(json.dumps(m))
    after=attest(p,assertion_ref('critical-deny'),control())[0]
    assert (after['evaluation_status'],after['finding'],after['basis_codes'])==(
            before['evaluation_status'],before['finding'],before['basis_codes'])
