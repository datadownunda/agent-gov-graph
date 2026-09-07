from copy import deepcopy
import pytest
from test_graph_value_queries import ENGINES,authority_fixture,topology
from src.graph_value.canonical import Catalog
from experiments.graph_value.generate import AT,delegation,root_record


@pytest.mark.parametrize('engine',ENGINES)
@pytest.mark.parametrize('changes,code',[
    ({'valid_to':AT},'DELEGATION_EXPIRED'),
    ({'valid_from':'2026-09-05T13:00:00Z'},'DELEGATION_NOT_YET_VALID'),
    ({'valid_to':None},'DELEGATION_VALIDITY_EXCEEDED'),
    ({'delegated_scopes':[{'action':'export','resource_type':'employee_complaint','resource_ids':['complaint-456']}]},'DELEGATION_SCOPE_EXCEEDED'),
    ({'delegator':'worker'},'DELEGATION_CYCLE'),
    ({'parent':{'kind':'delegation','record_id':'missing','version':'1'}},'DELEGATION_CHAIN_BROKEN'),
])
def test_m5_rejected_paths_preserved(engine,changes,code):
    pair=authority_fixture()['contexts']['pair']
    pair['delegations'][2].update(changes)
    c=Catalog();c.authority_pair('pair',pair['authority'],pair['delegations'])
    out=engine(c.freeze()).q3('pair',{'kind':'delegation','record_id':'d3','version':'1'},AT,requested=['read','employee_complaint','complaint-456'])
    worker=next(x for x in out['affected'] if x['actor']=='worker')
    assert worker['lost']==[] and len(worker['remaining'])==1
    assert code in {i['code'] for p in worker['resolution']['candidates'] for i in p['issues']}
    assert not out['prevention_inferred']


@pytest.mark.parametrize('engine',ENGINES)
def test_conflict_not_healed_by_removal(engine):
    pair=authority_fixture()['contexts']['pair']
    bad=deepcopy(pair['delegations'][0]);bad['onward_delegation']=False
    pair['delegations'].append(bad)
    c=Catalog();c.authority_pair('pair',pair['authority'],pair['delegations'])
    out=engine(c.freeze()).q3('pair',{'kind':'delegation','record_id':'d1','version':'1'},AT)
    for r in out['affected']:
        assert r['lost']==[]
        assert 'DELEGATION_CONFLICT' in {i['code'] for p in r['resolution']['candidates'] for i in p['issues']}


@pytest.mark.parametrize('engine',ENGINES)
def test_nanoseconds_and_no_revision_fallback(engine):
    pair=authority_fixture()['contexts']['pair']
    pair['delegations'][4]['valid_to']='2026-09-05T12:00:00.000000002Z'
    c=Catalog();c.authority_pair('pair',pair['authority'],pair['delegations'])
    e=engine(c.freeze());s={'kind':'delegation','record_id':'d5','version':'1'}
    assert e.q3('pair',s,'2026-09-05T08:00:00.000000001-04:00')['affected'][0]['lost']
    assert not e.q3('pair',s,'2026-09-05T12:00:00.000000002Z')['affected'][0]['lost']
    with pytest.raises(KeyError):e.q3('different-revision',s,AT)


@pytest.mark.parametrize('engine',ENGINES)
def test_cycles_and_explicit_truncation(engine):
    b=topology()
    b['records'][5]['references'].append({'field':'dependency_refs','target':'R','category':'verification','origin':'D','pointer':'/dependency_refs'})
    out=engine(b).q4('D')
    assert out['cycles'] and out['complete']
    limited=engine(b).q4('D',limit=2)
    assert not limited['complete']
    b['records'][5]['references'].append({'field':'dependency_refs','target':'missing','category':'verification','origin':'D','pointer':'/dependency_refs/1'})
    missing=engine(b).dependencies('D')
    assert not missing['complete'] and 'missing' in missing['unresolved']


@pytest.mark.parametrize('engine',ENGINES)
def test_full_child_scope_not_repaired_and_root_conflict(engine):
    pair=authority_fixture()['contexts']['pair']
    pair['delegations'][2]['delegated_scopes'][0]['resource_ids'].append('complaint-789')
    c=Catalog();c.authority_pair('pair',pair['authority'],pair['delegations'])
    args=('pair',{'kind':'delegation','record_id':'d3','version':'1'},AT,['read','employee_complaint','complaint-456'])
    row=engine(c.freeze()).q3(*args)['affected'][0]
    assert not row['lost'] and row['remaining']
    pair=authority_fixture()['contexts']['pair']
    pair['authority']['records'].append(root_record('root')|{'authority_record_id':'conflict','permitted_scopes':[]})
    c=Catalog();c.authority_pair('pair',pair['authority'],pair['delegations'])
    out=engine(c.freeze()).q3('pair',{'kind':'authority','record_id':'root-authority','version':'1'},AT)
    assert all(not r['lost'] for r in out['affected'])


@pytest.mark.parametrize('engine',ENGINES)
def test_no_partial_scope_union_or_missing_parent_fallback(engine):
    pair=authority_fixture()['contexts']['pair']
    pair['delegations'][2]['delegated_scopes'][0]['resource_ids']=['complaint-789']
    pair['delegations'][3]['delegated_scopes'][0]['action']='export'
    c=Catalog();c.authority_pair('pair',pair['authority'],pair['delegations'])
    out=engine(c.freeze()).q2('pair',{'kind':'delegation','record_id':'d3','version':'1'},AT,['read','employee_complaint','complaint-456'])
    assert not out['affected'][0]['resolution']['valid_bases']
    pair=authority_fixture()['contexts']['pair']
    pair['delegations'][0]['parent']['version']='missing'
    c=Catalog();c.authority_pair('pair',pair['authority'],pair['delegations'])
    out=engine(c.freeze()).q3('pair',{'kind':'delegation','record_id':'d1','version':'1'},AT)
    assert all(not r['lost'] for r in out['affected'])


@pytest.mark.parametrize('engine',ENGINES)
def test_legitimate_action_loss_and_two_time_boundary(engine):
    c=Catalog();pair=authority_fixture()['contexts']['pair']
    c.authority_pair('pair',pair['authority'],pair['delegations'])
    # Synthetic unit observation: ALLOW remains separate from M5 membership.
    key=c.add('pair','EvidenceRecord','action',{'actor':{'namespace':'agent','id':'leaf'},
        'action':'read','resource_type':'employee_complaint','resource_id':'complaint-456',
        'governance_decision':'ALLOW','observed_at':AT,'authority_resolution_at':AT})
    out=engine(c.freeze()).q3('pair',{'kind':'delegation','record_id':'d1','version':'1'},AT)
    assert out['otherwise_legitimate_actions_losing_support']==[key]
    c.records[key]['properties']['authority_resolution_at']='2026-09-04T23:59:59Z'
    out=engine(c.freeze()).q3('pair',{'kind':'delegation','record_id':'d1','version':'1'},AT)
    assert out['otherwise_legitimate_actions_losing_support']==[]
    assert not out['prevention_inferred']


@pytest.mark.parametrize('engine',ENGINES)
def test_exception_associated_path_loss_never_means_prevention(engine):
    c=Catalog();pair=authority_fixture()['contexts']['pair']
    c.authority_pair('pair',pair['authority'],pair['delegations'])
    g=c.add('pair','EvidenceRecord','denied',{'actor':{'namespace':'agent','id':'leaf'},
        'action':'read','resource_type':'employee_complaint','resource_id':'complaint-456',
        'governance_decision':'DENY','observed_at':AT})
    r=c.add('pair','Reconciliation','r',{'result':'CONTRADICTION'})
    a=c.add('pair','Attestation','a',{'finding':'CONTROL_EFFECTIVENESS_EXCEPTION'})
    c.reference(r,'claims',g);c.reference(a,'reconciliation_reference',r)
    original=c.freeze();out=engine(original).q3('pair',{'kind':'delegation','record_id':'d1','version':'1'},AT)
    assert [p['attestation'] for p in out['exception_associated_paths_lost']]==[a]
    assert out['affected_assurance_conclusions']==sorted([a,r])
    assert out['otherwise_legitimate_actions_losing_support']==[]
    assert not out['prevention_inferred'] and out['historical_findings_unchanged']
    assert c.freeze()==original
