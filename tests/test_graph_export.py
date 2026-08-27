from copy import deepcopy

import jsonschema

from src.graph_export import (
    export_graph,
    validate_graph,
)

from src.graph_projection import build_graph


def test_generated_graph_passes_graph_contract():
    graph = build_graph()

    validate_graph(graph)


def test_export_writes_valid_graph(tmp_path):
    output_path = (
        tmp_path
        / "agent_governance_graph.json"
    )

    graph = export_graph(
        path=output_path
    )

    assert output_path.exists()

    assert graph["graph_version"] == "1.0"

    validate_graph(graph)


def test_graph_contract_rejects_invalid_relationship_name():
    graph = deepcopy(
        build_graph()
    )

    graph["edges"][0]["relationship"] = (
        "invalid relationship"
    )

    try:
        validate_graph(graph)
        assert False, "Expected graph validation to fail"

    except jsonschema.ValidationError:
        pass


def test_graph_contract_rejects_missing_graph_version():
    graph = deepcopy(
        build_graph()
    )

    del graph["graph_version"]

    try:
        validate_graph(graph)
        assert False, "Expected graph validation to fail"

    except jsonschema.ValidationError:
        pass