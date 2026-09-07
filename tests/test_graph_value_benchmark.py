import json
from copy import deepcopy
from pathlib import Path
import pytest
from experiments.graph_value.benchmark import protocol,percentile
from experiments.graph_value.generate import make_source,prepare
from src.graph_value.baseline import Baseline
from src.graph_value.queries import GraphQueries


def test_protocol_frozen_and_no_database_requirement():
    p=protocol()
    assert p['success']['bespoke_query_topology_reduction_minimum']==.30
    assert p['graph_database_value']=='NOT_TESTED'
    assert not any('neo4j' in line.lower() for line in Path('experiments/graph_value/requirements.txt').read_text().splitlines())


def test_deterministic_source_and_population_integrity():
    source=make_source(2,seed=80,depth=6)
    assert source==make_source(2,seed=80,depth=6)
    assert source!=make_source(2,seed=800,depth=6)
    before=deepcopy(source);b=prepare(source)
    assert source==before
    assert 'expected' not in json.dumps(source)
    broken=deepcopy(source);broken['components'][0]['action_records'][0]['raw']['actor']='changed'
    with pytest.raises(ValueError):prepare(broken)


def test_quantiles():
    assert percentile(list(range(1,101)),.95)==95
    assert percentile(list(range(1,101)),.50)==50


def test_q4_shared_dependency_crosses_components():
    b=prepare(make_source(3,depth=6));a,g=Baseline(b),GraphQueries(b)
    from src.evidence_digest import evidence_digest
    from src.graph_value.canonical import ident
    contract={'target_id':'deterministic-complaint-target','effect':'REPRESENTATION_SERVED',
              'boundary':'synthetic target observation; no live process or client-consumption claim'}
    key=ident('artifacts','EvidenceArtifact',evidence_digest(contract))
    left,right=a.q4(key),g.q4(key)
    assert left==right and left['complete']
    assert len(left['conclusions'])==3


def test_population_growth_and_competing_candidate_not_hidden():
    from experiments.graph_value.generate import action_source,correlations
    from src.action_reconciliation import reconcile
    from src.graph_value.canonical import Catalog,add_reconciliation
    from src.evidence_digest import evidence_digest
    for count in (2,8):
        records=action_source('actor','source')
        for i in range(count-1):
            extra=deepcopy(records[2]);extra['evidence_ref']='candidate-'+str(i)
            records.append(extra)
        corr=correlations(records)
        assertion=reconcile(records,corr,governance_ref=records[0]['evidence_ref'])
        assert assertion['result']=='INSUFFICIENT_EVIDENCE'
        assert any(a['result']['state']=='AMBIGUOUS' for b in corr for a in b['assertions'])
        c=Catalog();key,_=add_reconciliation(c,assertion,'view')
        bundle=c.freeze();a,g=Baseline(bundle),GraphQueries(bundle)
        assert a.dependencies(key)==g.dependencies(key)
        assert sum(r['type']=='EvidenceRecord' for r in bundle['records'])==count+2
