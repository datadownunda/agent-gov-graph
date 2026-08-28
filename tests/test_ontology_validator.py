from copy import deepcopy

from src.graph_projection import build_graph
from src.ontology_validator import (
    ONTOLOGY_PATH,
    load_json,
    validate_graph_ontology,
)


def test_current_graph_passes_ontology_validation():
    graph = build_graph()
    ontology = load_json(ONTOLOGY_PATH)

    errors = validate_graph_ontology(
        graph,
        ontology,
    )

    assert errors == []


def test_invalid_relationship_source_is_detected():
    graph = deepcopy(
        build_graph()
    )
    ontology = load_json(
        ONTOLOGY_PATH
    )

    graph["edges"].append(
        {
            "source": "policy:employee_complaint_access:1.0",
            "relationship": "PERFORMED",
            "target": "step:step-001",
            "properties": {},
        }
    )

    errors = validate_graph_ontology(
        graph,
        ontology,
    )

    assert any(
        error["type"]
        == "invalid_relationship_source"
        for error in errors
    )


def test_unknown_relationship_type_is_detected():
    graph = deepcopy(
        build_graph()
    )
    ontology = load_json(
        ONTOLOGY_PATH
    )

    graph["edges"][0]["relationship"] = "MAGICALLY_CAUSED"

    errors = validate_graph_ontology(
        graph,
        ontology,
    )

    assert any(
        error["type"]
        == "unknown_relationship_type"
        for error in errors
    )


def test_unknown_target_node_is_detected():
    graph = deepcopy(
        build_graph()
    )
    ontology = load_json(
        ONTOLOGY_PATH
    )

    graph["edges"][0]["target"] = (
        "step:does-not-exist"
    )

    errors = validate_graph_ontology(
        graph,
        ontology,
    )

    assert any(
        error["type"]
        == "unknown_target_node"
        for error in errors
    )