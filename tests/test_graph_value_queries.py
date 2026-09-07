"""Expected results are read by scorer/tests only, never passed to either arm."""
import json
from pathlib import Path
from copy import deepcopy
import pytest
from src.graph_value.baseline import Baseline
from src.graph_value.queries import GraphQueries
from src.graph_value.canonical import Catalog, load_reference
from src.graph_value.results import stable
from experiments.graph_value.generate import root_record, delegation, AT

FIXTURES = Path(__file__).parent/'fixtures/graph_value'
ENGINES = [Baseline,GraphQueries]


def topology():
    return json.loads((FIXTURES/'topologies.json').read_text())


def oracle():
    return json.loads((FIXTURES/'expected.json').read_text())


def authority_fixture():
    c=Catalog()
    authority={'schema_version':'2.0','source_id':'test','source_version':'1',
               'records':[root_record('root'),root_record('other')]}
    links=[delegation('d1','root','middle','authority','root-authority'),
           delegation('d2','other','middle','authority','other-authority'),
           delegation('d3','middle','worker','delegation','d1'),
           delegation('d4','middle','worker','delegation','d2'),
           delegation('d5','middle','leaf','delegation','d1')]
    c.authority_pair('pair',authority,links)
    return c.freeze()


@pytest.mark.parametrize('engine',ENGINES)
def test_q1_independent_oracle(engine):
    out=engine(topology()).q1('A')
    assert out['complete']
    assert out['records']==oracle()['q1_records']
    assert sorted(p['records'] for p in out['paths'])==sorted(oracle()['q1_paths'])
    assert all(p['origins']==p['records'] for p in out['paths'])


@pytest.mark.parametrize('engine',ENGINES)
def test_q4_independent_oracle_categories_and_view_isolation(engine):
    out=engine(topology()).q4('D')
    assert out['complete']
    assert out['records']==oracle()['q4_records']
    assert out['conclusions']==oracle()['q4_conclusions']
    assert sorted(p['records'] for p in out['paths'])==sorted(oracle()['q4_paths'])
    for p in out['paths']:
        assert p['categories'][0]==('verification' if p['records'][1]=='G' else 'support')
    assert 'U' not in out['records']


@pytest.mark.parametrize('engine',ENGINES)
@pytest.mark.parametrize('query',['q2','q3'])
def test_authority_independent_oracle(engine,query):
    before=authority_fixture()
    out=getattr(engine(before),query)('pair',{'kind':'delegation','record_id':'d1','version':'1'},AT)
    observed={r['actor']:{k:[[ref['record_id'] for ref in p['chain']] for p in r[k]] for k in ('lost','remaining')} for r in out['affected']}
    assert observed==oracle()['authority']
    assert [r['actor'] for r in out['affected'] if r['loses_all_demonstrated_support']]==['leaf']
    if query=='q3':
        assert out['historical_findings_unchanged'] and not out['prevention_inferred']
    assert before==authority_fixture()


@pytest.mark.parametrize('engine',ENGINES)
def test_inverse_and_variable_depth_variants(engine):
    e=engine(topology())
    assert e.dependencies('D',reverse=True,depth=1)['records']==['D','G','O']
    assert e.dependencies('A',depth=1)['records']==['A','R']
    assert e.dependencies('A')['records']==oracle()['q1_records']


@pytest.mark.parametrize('engine',ENGINES)
def test_permutation_duplicate_and_rebuild(engine):
    b=topology()
    first=engine(b).q1('A')
    b['records'].reverse()
    for r in b['records']: r['references'].reverse()
    assert engine(b).q1('A')==first
    assert engine(topology()).q1('A')==first
    a=authority_fixture()
    c=Catalog()
    pair=a['contexts']['pair']
    c.authority_pair('pair',pair['authority'],pair['delegations']+[deepcopy(pair['delegations'][0])])
    query=dict(context='pair',selected={'kind':'delegation','record_id':'d1','version':'1'},at=AT)
    assert engine(c.freeze()).q3(**query)['affected']==engine(a).q3(**query)['affected']


def test_reference_exception_and_withheld_view():
    bundle=load_reference(Path(__file__).resolve().parents[1])
    a,g=Baseline(bundle),GraphQueries(bundle)
    for r in bundle['records']:
        if r['type']=='Attestation' and r['properties']['finding']=='CONTROL_EFFECTIVENESS_EXCEPTION':
            left,right=a.q1(r['id']),g.q1(r['id'])
            assert left==right and left['complete']
            assert {x['properties']['role'] for x in left['details'] if x['type']=='EvidenceRecord'}=={'governance','execution','outcome'}
    for r in bundle['records']:
        if r['type']=='Reconciliation' and r['properties']['result']=='INSUFFICIENT_EVIDENCE':
            out=a.dependencies(r['id'])
            # Cross-view traversal cannot bring another reconciliation into this view.
            assert not any(a.records[k]['type']=='Reconciliation' and k!=r['id'] for k in out['records'])
