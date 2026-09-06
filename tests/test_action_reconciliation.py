from copy import deepcopy
import pytest
from src.correlation_assertion import native_assertions
from src.evidence_digest import evidence_digest
from src.action_reconciliation import reconcile

TIME='2026-09-05T12:00:01Z'


def record(role, **changes):
    return dict(schema_version='1.0', evidence_ref=role, role=role,
                actor={'namespace':'agent','id':'root'}, action='read', resource_id='complaint-456',
                resource_type='employee_complaint', observed_at=TIME, ingested_at=TIME,
                action_attempt_id='attempt', request_id='native', defects=[], **changes)


def sample(decision='ALLOW'):
    return [record('governance', governance_decision=decision),
            record('execution', execution_disposition='SUBMITTED', client_success=True),
            record('outcome', target_outcome='REPRESENTATION_SERVED')]


def links(records):
    result=[]
    for a,b,field in [('governance','execution','action_attempt_id'), ('execution','outcome','request_id')]:
        left=[r for r in records if r['role']==a]; right=[r for r in records if r['role']==b]
        result.append({'roles':{'left':a,'right':b}, 'assertions':native_assertions(left,right,
            identifier_field=field, namespace=field, issuer='test', relationship_type='SAME_ACTION')})
    return result


def assess(records=None, **kw):
    records=sample() if records is None else records
    return reconcile(records, links(records), governance_ref='governance', **kw)


def test_allow_full_triple():
    a=assess()
    assert a['result']=='CONSISTENT'
    assert len(a['source_evidence'])==3
    assert a['correlation_paths']


def test_critical_deny_submitted_client_failure_native_effect():
    r=sample('DENY'); r[1]['client_success']=None; r[1]['failure_stage']='CLIENT_FINALIZATION_FAILED'
    a=assess(r)
    assert a['result']=='CONTRADICTION'
    assert 'GOVERNANCE_OUTCOME_CONTRADICTION' in a['issue_codes']
    assert 'EXECUTION_OUTCOME_CONTRADICTION' not in a['issue_codes']
    assert a['claims']['execution'][0]['client_success'] is None


def test_withheld_execution_does_not_force_contradiction():
    r=sample('DENY'); del r[1]
    a=assess(r)
    assert a['result']=='INSUFFICIENT_EVIDENCE'
    assert 'GOVERNANCE_OUTCOME_CONTRADICTION' not in a['issue_codes']


def test_independently_linked_outcome_deny_even_when_execution_missing():
    r=sample('DENY'); del r[1]
    c={'roles':{'left':'governance','right':'outcome'},'assertions':native_assertions(r[:1],r[1:],
        identifier_field='request_id', namespace='test-only-known-native', issuer='fixture',relationship_type='SAME_ACTION')}
    a=reconcile(r,[c],governance_ref='governance')
    assert a['result']=='CONTRADICTION'
    assert 'EXECUTION_EVIDENCE_MISSING' in a['issue_codes']


@pytest.mark.parametrize('dimension,value', [('action','export'),('resource_id','complaint-789')])
def test_divergent_dimension(dimension,value):
    r=sample();r[1][dimension]=value;r[2][dimension]=value
    a=assess(r)
    assert a['result']=='UNEXPLAINED_DIVERGENCE'
    assert any(d['dimension']==dimension and d['relation']=='DIFFERENT' for d in a['comparisons'])


def test_no_actor_namespace_equivalence_without_mapping():
    r=sample();r[2]['actor']={'namespace':'nginx-basic','id':'root'}
    assert assess(r)['result']=='INSUFFICIENT_EVIDENCE'
    mapping={'version':'1','entries':[{'source':r[2]['actor'],'target':r[1]['actor']}]}
    assert assess(r,identity_mapping=mapping)['result']=='CONSISTENT'
    assert r[2]['actor']['namespace']=='nginx-basic'


def test_actor_difference_without_historical_evidence_is_insufficient():
    r=sample();r[1]['actor']['id']='other';r[2]['actor']['id']='other'
    assert assess(r)['result']=='INSUFFICIENT_EVIDENCE'


def test_missing_outcome_and_explicit_not_submitted_contradiction():
    r=sample(); assert assess(r[:2])['result']=='INSUFFICIENT_EVIDENCE'
    r[1]['execution_disposition']='NOT_SUBMITTED'
    assert assess(r)['result']=='CONTRADICTION'


def test_deny_absence_coverage_is_bounded():
    r=sample('DENY')[:1]
    assert assess(r)['result']=='INSUFFICIENT_EVIDENCE'
    coverage={'schema_version':'1.0','interval_start':'2026-09-05T12:00:00Z','interval_end':'2026-09-05T12:00:05Z',
              'roles':{'execution':'CAPTURED','outcome':'CAPTURED'},'basis':'fixture capture',
              'scope':{'actor':r[0]['actor'],'action':'read','resource_id':'complaint-456','resource_type':'employee_complaint'}}
    a=assess(r,coverage=coverage)
    assert a['result']=='CONSISTENT'
    assert 'CONSISTENT_WITH_BLOCKING' in a['issue_codes']
    coverage['interval_end']='2026-09-05T11:59:59Z'
    assert assess(r,coverage=coverage)['result']=='INSUFFICIENT_EVIDENCE'


def test_ambiguous_population_and_order():
    r=sample();r.append(dict(r[-1],evidence_ref='second-outcome'))
    assert assess(r)['result']=='INSUFFICIENT_EVIDENCE'
    assert assess(r)==assess(list(reversed(r)))


def test_rehashing_forged_link_is_not_replay():
    r=sample();c=links(r)
    a=c[0]['assertions'][0];a['result']['reason']='forged'
    a['assertion_id']=evidence_digest({k:v for k,v in a.items() if k!='assertion_id'})
    assert reconcile(r,c,governance_ref='governance')['result']=='NOT_EVALUABLE'


def test_changed_source_invalidates_correlation_and_no_mutation():
    r=sample();c=links(r);before=deepcopy(r)
    assess(r); assert r==before
    r[1]['action']='export'
    assert reconcile(r,c,governance_ref='governance')['result']=='NOT_EVALUABLE'


def historical(tmp_path, links_override=None, roots_override=None):
    from test_delegation_resolver import authority, authorities, delegation, query
    from test_delegation_reconstruction import m4_event
    from src.authority_resolver import preserve_revision
    from src.delegation_evidence import preserve_delegation_revision
    from src.delegation_reconstruction import create_assertion
    source=authorities(*(roots_override or [authority()]))
    ref=preserve_revision(source,tmp_path)
    dref=preserve_delegation_revision({'schema_version':'1.0','source_id':'test','source_version':'1',
        'authority_revision':ref,'records':links_override if links_override is not None else [delegation()]},tmp_path)
    event=m4_event(ref,source)
    assertion=create_assertion(query(effective_at=TIME),authority_reference=ref,delegation_reference=dref,history_directory=tmp_path)
    r=sample();r[0]['raw']=event;r[1]['actor']['id']='worker';r[2]['actor']['id']='worker'
    return r,assertion,dref


def test_multiple_bases_preserved_without_identity_rewrite(tmp_path):
    from test_delegation_resolver import delegation
    r,a,_=historical(tmp_path,[delegation(),delegation(delegation_id='second')])
    before=deepcopy(r)
    result=assess(r,delegation_assertion=a,history_directory=tmp_path)
    assert result['result']=='EXPLAINED_DIVERGENCE'
    assert len(result['authority_explanation']['valid_explanatory_bases'])==2
    assert r==before
    (tmp_path/'current.json').write_text('{}')
    assert assess(r,delegation_assertion=a,history_directory=tmp_path)==result


@pytest.mark.parametrize('tamper',[True,False])
def test_m5_archive_cannot_be_replaced_by_embedded_basis(tmp_path,tamper):
    r,a,ref=historical(tmp_path)
    if tamper:(tmp_path/ref['file']).write_text('{}')
    else:(tmp_path/ref['file']).unlink()
    result=assess(r,delegation_assertion=a,history_directory=tmp_path)
    assert result['result']=='INSUFFICIENT_EVIDENCE'


def test_explicitly_invalid_delegation_does_not_explain(tmp_path):
    from test_delegation_resolver import delegation, scope
    r,a,_=historical(tmp_path,[delegation(delegated_scopes=[scope('not-upstream')])])
    assert assess(r,delegation_assertion=a,history_directory=tmp_path)['result']=='UNEXPLAINED_DIVERGENCE'


def test_unrelated_direct_basis_is_not_delegation_explanation(tmp_path):
    from test_delegation_resolver import authority
    r,a,_=historical(tmp_path,[],[authority(),authority('worker')])
    assert assess(r,delegation_assertion=a,history_directory=tmp_path)['result']=='UNEXPLAINED_DIVERGENCE'


def test_delegation_crosses_two_time_boundary(tmp_path):
    from test_delegation_resolver import delegation
    r,a,_=historical(tmp_path,[delegation(valid_from='2026-09-05T12:00:00.5Z')])
    result=assess(r,delegation_assertion=a,history_directory=tmp_path)
    assert result['result']=='INSUFFICIENT_EVIDENCE'
    assert result['authority_explanation']['status']=='TEMPORAL_BOUNDARY_AMBIGUITY'


def test_malformed_assertion_returns_explicit_not_evaluable():
    r=sample();c=links(r);del c[0]['assertions'][0]['result']
    assert reconcile(r,c,governance_ref='governance')['result']=='NOT_EVALUABLE'


def test_duplicate_candidate_cannot_be_hidden_in_an_assertion_population():
    r=sample();c=links(r);r.append(dict(r[1],evidence_ref='duplicate-execution'))
    assert reconcile(r,c,governance_ref='governance')['result']=='NOT_EVALUABLE'


def test_explicit_correlation_invariant_contradiction_is_not_effect_contradiction():
    r=sample();r[1]['action']='export';c=links(r)
    c[0]['assertions']=native_assertions(r[:1],r[1:2],identifier_field='action_attempt_id',
        namespace='test',issuer='test',required_equal_fields=['action'])
    a=reconcile(r,c,governance_ref='governance')
    assert a['result']=='INSUFFICIENT_EVIDENCE'
    assert 'CORRELATION_CONTRADICTED' in a['issue_codes']
    assert 'GOVERNANCE_OUTCOME_CONTRADICTION' not in a['issue_codes']


def test_rejected_path_does_not_poison_independent_explanation(tmp_path):
    from test_delegation_resolver import delegation,parent
    r,a,_=historical(tmp_path,[delegation(),delegation(delegation_id='broken',parent=parent('delegation','missing'))])
    result=assess(r,delegation_assertion=a,history_directory=tmp_path)
    assert result['result']=='EXPLAINED_DIVERGENCE'
    assert len(result['authority_explanation']['m5']['resolution']['candidates'])==2


def test_missing_m4_archive_prevents_explanation(tmp_path):
    r,a,_=historical(tmp_path)
    (tmp_path/a['authority_revision']['file']).unlink()
    assert assess(r,delegation_assertion=a,history_directory=tmp_path)['result']=='INSUFFICIENT_EVIDENCE'
