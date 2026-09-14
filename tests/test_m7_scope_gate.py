"""Synthetic predicate/rule tests plus genuine archived v2 verification tests."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from experiments.strong_link_assurance.generate import build
from experiments.m7_scope_gate.run_conformance import worker
from src.control_attestation import adjudicate, attest, reconstruct_attestation, validate_attestation
from src.evidence_digest import evidence_digest
from src.m6_attestation_evidence import _scope_predicate, _namespace_codes, _exception_paths

ROOT = Path(__file__).resolve().parents[1]
DECL = json.loads((ROOT/'tests/fixtures/m7_scope_gate/evidence.json').read_text())
CONTROL = json.loads((ROOT/'experiments/control_attestation/control.json').read_text())


def declared_evidence():
    evidence, _ = build('controls', 'deny_effect')
    for row in evidence['rows']['governance']:
        row['context']['identifier_declarations'] = {'action_attempt_id':deepcopy(DECL['attempt_declaration'])}
    for row in evidence['rows']['execution']:
        row['identifier_declarations'] = {'action_attempt_id':deepcopy(DECL['attempt_declaration']), 'request_id':deepcopy(DECL['request_declaration'])}
    for row in evidence['rows']['outcome']:
        row['identifier_declarations'] = {'request_id':deepcopy(DECL['request_declaration'])}
    return evidence


@pytest.fixture(scope='module')
def verified(tmp_path_factory):
    archive=tmp_path_factory.mktemp('scope')/'archive'
    output=worker(declared_evidence(),archive)
    view=output['reconciliation']['critical-deny']
    return archive,output,view,output['attestations'][view['assertion_id']]


def pair(verified):
    _,output,view,_=verified
    lookup={r['evidence_ref']:deepcopy(r) for r in output['records']}
    g=lookup[view['claims']['governance'][0]['evidence_ref']]
    e=lookup[view['claims']['execution'][0]['evidence_ref']]
    return g,e


def synthetic_rule(verified, g, e):
    """Pure rule fixture: explicitly bypasses archive verification, never empirical evidence."""
    _,output,view,saved=verified
    records=[g if r['evidence_ref']==g['evidence_ref'] else e if r['evidence_ref']==e['evidence_ref'] else r for r in output['records']]
    r=deepcopy(saved['receipt'])
    r['facts']['exception_paths']=_exception_paths(view,records,r['facts'])
    r['receipt_id']=evidence_digest({k:v for k,v in r.items() if k!='receipt_id'})
    return adjudicate(CONTROL,r)


def test_declared_single_action_actual_verified_exception_and_replay(verified):
    archive,_,_,saved=verified
    a=saved['attestation']
    assert a['finding']=='CONTROL_EFFECTIVENESS_EXCEPTION'
    assert a['rule_version']=='control-attestation/2' and a['schema_version']=='1.2'
    assert saved['receipt']['status']=='VERIFIED'
    assert all(p['scope_established'] and p['namespace_declared_compatible'] for p in a['exception_paths'])
    assert reconstruct_attestation(a,archive,CONTROL)['status']=='VERIFIED'


@pytest.mark.parametrize('context',['transaction_id','parent_request_id','session_id','task_id','tuple_only'])
def test_correlated_child_tuple_and_parent_do_not_establish_scope(verified,context):
    g,e=pair(verified)
    e['action_attempt_id']=None
    e['raw']['action_attempt_id']=None
    g['raw']['context'][context]='shared'
    e['raw'][context]='shared'
    result=synthetic_rule(verified,g,e)
    assert result['finding']=='CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED'
    assert result['basis_codes']==['GOVERNANCE_SCOPE_NOT_ESTABLISHED']
    assert result['correlation_assertion_refs']


def test_explicit_decision_identity_binding(verified):
    g,e=pair(verified)
    e['action_attempt_id']=None
    e['raw']['authorizing_decision_id']=g['raw']['event_id']
    g['raw']['context']['identifier_declarations']['event_id']=DECL['attempt_declaration']
    e['raw']['identifier_declarations']['authorizing_decision_id']=DECL['attempt_declaration']
    assert _scope_predicate(g,e)==('SINGLE_ACTION',True,[])


def test_literal_envelope_covers_multiple_without_execution_authorization(verified):
    g,e=pair(verified)
    g['raw']['context']['governance_scope']=deepcopy(DECL['envelope'])
    for resource in DECL['envelope']['resource_ids']:
        child=deepcopy(e)
        child.update(action_attempt_id=None,resource_id=resource)
        child['raw'].pop('action_attempt_id',None)
        assert _scope_predicate(g,child)==('BOUNDED_ENVELOPE',True,[])
    e['action_attempt_id']=None
    assert synthetic_rule(verified,g,e)['finding']=='CONTROL_EFFECTIVENESS_EXCEPTION'


@pytest.mark.parametrize('change',[
    {'resource_id':'outside'}, {'action':'export'}, {'resource_type':'other'},
    {'actor':{'namespace':'agent','id':'other'}}, {'observed_at':'2026-09-05T12:00:10Z'},
    {'observed_at':'2026-09-05T11:59:59Z'}])
def test_outside_envelope_abstains(verified,change):
    g,e=pair(verified)
    g['raw']['context']['governance_scope']=deepcopy(DECL['envelope'])
    e.update(change)
    assert synthetic_rule(verified,g,e)['basis_codes']==['GOVERNANCE_SCOPE_NOT_ESTABLISHED']


@pytest.mark.parametrize('change',[
    {'resource_ids':['*']}, {'resource_ids':['complaint-*']}, {'resource_ids':[]}, {'resource_ids':['complaint-789','complaint-789']},
    {'action':'*'}, {'action_class':'read'}, {'predicate':'true'}, {'resource_group':'complaints'},
    {'valid_to':'bad'}, {'valid_to':'2026-09-05T12:00:00Z'}])
def test_no_wildcards_classes_groups_expressions_or_unbounded_envelopes(verified,change):
    g,e=pair(verified)
    g['raw']['context']['governance_scope']=deepcopy(DECL['envelope'])|change
    assert not _scope_predicate(g,e)[1]


def test_retry_requires_explicit_producer_binding(verified):
    g,e=pair(verified)
    g['raw']['context']['governance_scope']={'kind':'RETRY_OF'}
    assert not _scope_predicate(g,e)[1]
    e['raw']['retry_of']=g['action_attempt_id']
    e['raw']['identifier_declarations']['retry_of']=deepcopy(DECL['attempt_declaration'])
    assert synthetic_rule(verified,g,e)['finding']=='CONTROL_EFFECTIVENESS_EXCEPTION'
    e['raw']['retry_of']='other-attempt'
    assert synthetic_rule(verified,g,e)['basis_codes']==['GOVERNANCE_SCOPE_NOT_ESTABLISHED']


@pytest.mark.parametrize('declaration',[None,{}, {'issuer':'fixture-runtime','namespace':'*'}, {'issuer':'*','namespace':'runtime-attempts'}, {'issuer':'','namespace':'runtime-attempts'}, {'issuer':'fixture-runtime','namespace':''}, {'issuer':'fixture-runtime','namespace':'other'}])
def test_missing_or_conflicting_namespace_prevents_assurance_grade_use(verified,declaration):
    g,e=pair(verified)
    e['raw']['identifier_declarations']['action_attempt_id']=declaration
    a=synthetic_rule(verified,g,e)
    assert a['finding']=='CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED'
    assert any(code.startswith('NATIVE_IDENTIFIER_NAMESPACE_') for code in a['basis_codes'])


def test_declarations_do_not_claim_authentication(verified):
    a=verified[3]['attestation']
    assert any('neither independent authentication nor producer enforcement' in text for text in a['limitations'])


def test_default_v2_abstains_on_legacy_archive_but_v1_replays():
    archive=ROOT/'experiments/target_outcome/results/v1'
    view=json.loads((archive/'reconciliation.json').read_text())['critical-deny']
    old,_=attest(archive,view['assertion_id'],CONTROL,rule_version='control-attestation/1')
    new,_=attest(archive,view['assertion_id'],CONTROL)
    assert old['finding']=='CONTROL_EFFECTIVENESS_EXCEPTION'
    assert new['finding']=='CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED'
    assert 'NATIVE_IDENTIFIER_NAMESPACE_NOT_ESTABLISHED' in new['basis_codes']
    assert reconstruct_attestation(old,archive,CONTROL)['status']=='VERIFIED'


def test_v2_internal_failure_distinct_from_abstention(verified,monkeypatch):
    import src.m6_attestation_evidence as adapter
    def fail(*args): raise ArithmeticError('scope processing defect')
    monkeypatch.setattr(adapter,'_exception_paths',fail)
    archive,_,view,_=verified
    a,r=attest(archive,view['assertion_id'],CONTROL)
    assert a['schema_version']=='1.2' and r['schema_version']=='1.2'
    assert a['evaluation_status']==r['status']=='INTERNAL_ERROR'
    assert a['finding'] is None and a['coverage_assessment'] is None
    assert a['exception_paths']==[]
    validate_attestation(a)


def test_unrelated_execution_cannot_supply_scope(verified):
    r=deepcopy(verified[3]['receipt'])
    r['facts']['exception_paths'][0]['execution_ref']='unrelated'
    r['receipt_id']=evidence_digest({k:v for k,v in r.items() if k!='receipt_id'})
    assert adjudicate(CONTROL,r)['evaluation_status']=='NOT_EVALUABLE'


def test_raw_declaration_tamper_is_evidence_defect(verified,tmp_path):
    import shutil
    archive,_,view,_=verified
    copied=tmp_path/'archive'
    shutil.copytree(archive,copied)
    p=copied/'execution.jsonl'
    p.write_text(p.read_text().replace('fixture-runtime','different-issuer'))
    a,r=attest(copied,view['assertion_id'],CONTROL)
    assert r['status']=='EVIDENCE_DEFECT' and a['finding'] is None


def test_explicit_retry_binding_under_default_single_action(verified):
    g,e=pair(verified)
    e['action_attempt_id']='new-retry-attempt'
    e['raw']['retry_of']=g['action_attempt_id']
    e['raw']['identifier_declarations']['retry_of']=DECL['attempt_declaration']
    assert _scope_predicate(g,e)==('RETRY_OF',True,[])


@pytest.mark.parametrize('kind',['BOUNDED_ENVELOPE','RETRY_OF'])
def test_declared_scope_through_real_archive_verification(tmp_path,kind):
    evidence=declared_evidence()
    g=evidence['rows']['governance'][1]['context']
    if kind=='BOUNDED_ENVELOPE':
        g['governance_scope']=deepcopy(DECL['envelope'])
    else:
        e=evidence['rows']['execution'][0]
        e['retry_of']=g['action_attempt_id']
        e['identifier_declarations']['retry_of']=DECL['attempt_declaration']
    output=worker(evidence,tmp_path/'archive')
    view=output['reconciliation']['critical-deny']
    saved=output['attestations'][view['assertion_id']]
    assert saved['receipt']['status']=='VERIFIED'
    assert saved['attestation']['finding']=='CONTROL_EFFECTIVENESS_EXCEPTION'
    assert saved['attestation']['exception_paths'][0]['scope_kind']==kind


@pytest.mark.parametrize('saved',[None,[],{},'invalid'])
def test_malformed_saved_attestation_is_evidence_defect(saved,tmp_path):
    assert reconstruct_attestation(saved,tmp_path,CONTROL)['status']=='EVIDENCE_DEFECT'


def test_v2_schema_cannot_claim_exception_without_qualified_path(verified):
    from src.evidence_errors import EvidenceValidationError
    value=deepcopy(verified[3]['attestation'])
    value['exception_paths']=[]
    value['assertion_id']=evidence_digest({k:v for k,v in value.items() if k!='assertion_id'})
    with pytest.raises(EvidenceValidationError):
        validate_attestation(value)
