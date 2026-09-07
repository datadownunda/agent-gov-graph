from copy import deepcopy
import pytest
from test_graph_value_queries import topology
from src.graph_value.projection import Projection
from src.graph_value.baseline import Baseline
from src.graph_value.queries import GraphQueries


def test_projection_preserves_parallel_origins_and_source_catalog():
    b=topology();before=deepcopy(b)
    b['records'][0]['references'].append({'field':'reconciliation_reference','target':'R','category':'verification','origin':'other-receipt','pointer':'/verification'})
    graph=Projection(b)
    assert len(graph.outgoing['A'])==2
    assert {e['origin'] for e in graph.outgoing['A']}=={'A','other-receipt'}
    assert all(e['pointer'] for e in graph.edges)
    assert graph.serialize()==Projection(b).serialize()
    assert Baseline(b).q1('A')==GraphQueries(b).q1('A')


def test_duplicate_identity_rejected():
    b=topology();b['records'].append(deepcopy(b['records'][0]))
    with pytest.raises(ValueError):Projection(b)


def test_projection_and_result_schemas():
    import json
    import jsonschema
    from pathlib import Path
    b=topology()
    for r in b['records']:r['rule']='investigation-projection/1'
    graph=Projection(b)
    schema=json.loads(Path('schemas/investigation_projection.schema.json').read_text())
    jsonschema.validate({'nodes':list(graph.nodes.values()),'edges':graph.edges},schema)
    result_schema=json.loads(Path('schemas/investigation_query_result.schema.json').read_text())
    for engine in (Baseline(b),GraphQueries(b)):
        jsonschema.validate(engine.q1('A'),result_schema)
        jsonschema.validate(engine.q4('D'),result_schema)
