"""Deterministic decision-rule fixtures, not empirical evidence of effectiveness."""
from copy import deepcopy
from pathlib import Path
import json

import pytest

from src.control_attestation import adjudicate, attest, validate_attestation
from src.evidence_digest import evidence_digest

ROOT = Path(__file__).resolve().parents[1]


def control():
    return json.loads((ROOT / 'experiments/control_attestation/control.json').read_text())


def receipt(*, decision='DENY', effect=False, adequate=True, ambiguity=False, status='VERIFIED', **changes):
    facts = {
        'governance': {'evidence_ref':'sha256:g','decision':decision,
                       'actor':{'namespace':'agent','id':'fixture-agent'},'action':'read',
                       'resource_id':'complaint-789','resource_type':'employee_complaint',
                       'observed_at':'2026-09-05T12:00:00Z'},
        'reconciliation_result':'CONTRADICTION' if effect else 'CONSISTENT',
        'consistent_with_blocking':not effect,
        'target_contract_verified':True,
        'prohibited_effect_established':effect,
        'relevant_correlation_ambiguous':ambiguity,
        'undermining_uncertainty':False,
        'supporting_effect_refs':['sha256:o'] if effect else [],
        'supporting_correlation_refs':['sha256:link'] if effect else [],
        'source_refs':['sha256:g','sha256:o'] if effect else ['sha256:g'],
    } | changes
    r = {'schema_version':'1.0','rule_version':'m6-attestation-verification/1','status':status,
         'control_digest':evidence_digest(control()),'reconciliation_ref':'sha256:m6',
         'archive_digest':'sha256:archive','facts':facts,
         'coverage_assessment':{'control_digest':evidence_digest(control()),'result':'ADEQUATE' if adequate else 'UNKNOWN',
              'basis_codes':['BOUNDED_TARGET_COVERAGE_ADEQUATE'] if adequate else ['TARGET_COVERAGE_UNKNOWN'],
              'interval':{'start':'2026-09-05T12:00:00Z','end':'2026-09-05T12:00:10Z'},
              'support_ref':None,'coverage_ref':None},
         'basis_codes':[], 'dependency_refs':[],
         'limitations':['Fixture verification receipt; demonstrates adjudication semantics only.']}
    r['receipt_id'] = evidence_digest(r)
    return r


@pytest.mark.parametrize('r,status,finding', [
    (receipt(),'EVALUATED','CONTROL_EFFECTIVE'),
    (receipt(effect=True,adequate=False),'EVALUATED','CONTROL_EFFECTIVENESS_EXCEPTION'),
    (receipt(adequate=False),'INSUFFICIENT_EVIDENCE','CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED'),
    (receipt(effect=True,ambiguity=True),'INSUFFICIENT_EVIDENCE','CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED'),
    (receipt(ambiguity=True),'INSUFFICIENT_EVIDENCE','CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED'),
    (receipt(status='EVIDENCE_DEFECT'),'NOT_EVALUABLE',None),
    (receipt(decision='ALLOW'),'NOT_APPLICABLE',None),
    (receipt(undermining_uncertainty=True),'INSUFFICIENT_EVIDENCE','CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED'),
    (receipt(target_contract_verified=False),'INSUFFICIENT_EVIDENCE','CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED'),
])
def test_fixed_rule(r,status,finding):
    a=adjudicate(control(),r)
    assert (a['evaluation_status'],a['finding'])==(status,finding)
    assert a['scope']['cardinality']=='SINGLE_ACTION'
    assert any('consumption' in s for s in a['limitations'])
    validate_attestation(a)


def test_m6_contradiction_or_divergence_is_not_mechanical_exception():
    for state in ['CONTRADICTION','UNEXPLAINED_DIVERGENCE','EXPLAINED_DIVERGENCE']:
        r=receipt(reconciliation_result=state,consistent_with_blocking=False)
        assert adjudicate(control(),r)['finding']=='CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED'


def test_no_execution_success_or_delegation_input_needed_for_exception():
    r=receipt(effect=True)
    assert 'execution' not in r['facts'] and 'delegation' not in r['facts']
    assert adjudicate(control(),r)['finding']=='CONTROL_EFFECTIVENESS_EXCEPTION'


def test_changed_receipt_and_unknown_ground_truth_fields_are_rejected():
    r=receipt();r['facts']['prohibited_effect_established']=True
    assert adjudicate(control(),r)['evaluation_status']=='NOT_EVALUABLE'
    r=receipt();r['facts']['bypass']=True
    r['receipt_id']=evidence_digest({k:v for k,v in r.items() if k!='receipt_id'})
    assert adjudicate(control(),r)['evaluation_status']=='NOT_EVALUABLE'


def test_control_mismatch_invalid_control_and_no_mutation():
    c=control();r=receipt();before=deepcopy((c,r))
    adjudicate(c,r);assert (c,r)==before
    c['control_version']='2'
    assert adjudicate(c,r)['evaluation_status']=='NOT_EVALUABLE'
    c['control_type']='OTHER'
    assert adjudicate(c,r)['evaluation_status']=='NOT_EVALUABLE'
