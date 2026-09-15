import json
from pathlib import Path

from src.graph_projection import build_graph


ROOT = Path(__file__).resolve().parents[1]

ONTOLOGY_PATH = (
    ROOT
    / "schemas"
    / "agent_governance_ontology.json"
)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def validate_graph_ontology(graph, ontology):
    errors = []

    node_types = ontology["node_types"]
    relationship_types = ontology["relationship_types"]

    nodes_by_id = {}

    for node in graph["nodes"]:
        node_id = node["id"]
        node_type = node["type"]

        if node_id in nodes_by_id:
            errors.append(
                {
                    "type": "duplicate_node_id",
                    "node_id": node_id,
                }
            )

        nodes_by_id[node_id] = node

        if node_type not in node_types:
            errors.append(
                {
                    "type": "unknown_node_type",
                    "node_id": node_id,
                    "node_type": node_type,
                }
            )

    for edge in graph["edges"]:
        source_id = edge["source"]
        target_id = edge["target"]
        relationship = edge["relationship"]

        if source_id not in nodes_by_id:
            errors.append(
                {
                    "type": "unknown_source_node",
                    "source": source_id,
                    "relationship": relationship,
                }
            )
            continue

        if target_id not in nodes_by_id:
            errors.append(
                {
                    "type": "unknown_target_node",
                    "target": target_id,
                    "relationship": relationship,
                }
            )
            continue

        if relationship not in relationship_types:
            errors.append(
                {
                    "type": "unknown_relationship_type",
                    "relationship": relationship,
                }
            )
            continue

        relationship_definition = (
            relationship_types[relationship]
        )

        source_type = nodes_by_id[source_id]["type"]
        target_type = nodes_by_id[target_id]["type"]

        allowed_source_types = (
            relationship_definition["source"]
        )

        allowed_target_types = (
            relationship_definition["target"]
        )

        if source_type not in allowed_source_types:
            errors.append(
                {
                    "type": "invalid_relationship_source",
                    "relationship": relationship,
                    "source_id": source_id,
                    "source_type": source_type,
                    "allowed_source_types":
                        allowed_source_types,
                }
            )

        if target_type not in allowed_target_types:
            errors.append(
                {
                    "type": "invalid_relationship_target",
                    "relationship": relationship,
                    "target_id": target_id,
                    "target_type": target_type,
                    "allowed_target_types":
                        allowed_target_types,
                }
            )

    return errors


def main():
    graph = build_graph()
    ontology = load_json(ONTOLOGY_PATH)

    errors = validate_graph_ontology(
        graph,
        ontology,
    )

    result = {
        "status": "PASS" if not errors else "FAIL",
        "ontology_version": ontology["ontology_version"],
        "node_count": len(graph["nodes"]),
        "edge_count": len(graph["edges"]),
        "errors": errors,
    }

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()