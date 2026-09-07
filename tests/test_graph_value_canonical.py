from copy import deepcopy
from pathlib import Path
import json
import hashlib
import pytest
from src.graph_value.canonical import Catalog,load_pair,load_reference,digest_file
from src.authority_resolver import preserve_revision
from src.delegation_evidence import preserve_delegation_revision
from test_graph_value_queries import authority_fixture


def test_exact_pair_integrity_current_state_ignored(tmp_path):
    pair=authority_fixture()['contexts']['pair']
    a=preserve_revision(pair['authority'],tmp_path)
    d=preserve_delegation_revision({'schema_version':'1.0','source_id':'d','source_version':'1',
         'authority_revision':a,'records':pair['delegations']},tmp_path)
    before=load_pair(a,d,tmp_path)
    (tmp_path/'current.json').write_text('{}')
    assert load_pair(a,d,tmp_path)==before
    (tmp_path/a['file']).write_text('{}')
    with pytest.raises(ValueError):load_pair(a,d,tmp_path)
    (tmp_path/a['file']).unlink()
    with pytest.raises(FileNotFoundError):load_pair(a,d,tmp_path)


def test_conflicting_variants_retained_and_pair_isolation():
    pair=authority_fixture()['contexts']['pair']
    variant=deepcopy(pair['delegations'][0]);variant['onward_delegation']=False
    c=Catalog();c.authority_pair('one',pair['authority'],pair['delegations']+[variant])
    c.authority_pair('two',pair['authority'],pair['delegations'])
    nodes=c.freeze()['records']
    assert len([r for r in nodes if r['context']=='one' and r['type']=='DelegationRecord'])==6
    assert len([r for r in nodes if r['context']=='two' and r['type']=='DelegationRecord'])==5
    for r in nodes:
        for ref in r['references']:
            target=c.records.get(ref['target'])
            if target: assert target['context'] in (r['context'],'artifacts','sources')


def test_no_legacy_graph_or_database_imports():
    import ast
    root=Path(__file__).resolve().parents[1]
    for path in list((root/'src/graph_value').glob('*.py'))+list((root/'experiments/graph_value').glob('*.py')):
        for n in ast.walk(ast.parse(path.read_text())):
            if isinstance(n,ast.ImportFrom):
                assert n.module not in ('src.graph_projection','src.graph_export','src.neo4j_store','neo4j')
            if isinstance(n,ast.Import):assert all(a.name!='neo4j' for a in n.names)


def test_reference_read_only_and_labels_not_in_canonical_input():
    root=Path(__file__).resolve().parents[1]
    files=[p for p in (root/'experiments/control_attestation/results/v1').rglob('*') if p.is_file()]
    before={str(p):digest_file(p) for p in files}
    bundle=load_reference(root)
    after={str(p):digest_file(p) for p in files}
    assert before==after
    for r in bundle['records']:
        assert r['origin'] is not None and r['reference'] is not None
        assert not set(r['properties'] if isinstance(r['properties'],dict) else ()) & {'label','evidence_kind','ground_truth','bypass_enforcement','scenario_design','run_id'}
    assert len([r for r in bundle['records'] if r['type']=='Attestation'])==6
