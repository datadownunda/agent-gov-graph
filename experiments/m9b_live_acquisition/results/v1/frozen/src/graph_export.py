import json
from pathlib import Path

import jsonschema

from src.graph_projection import build_graph


ROOT = Path(__file__).resolve().parents[1]

GRAPH_SCHEMA_PATH = (
    ROOT
    / "schemas"
    / "agent_governance_graph.schema.json"
)

DEFAULT_EXPORT_PATH = (
    ROOT
    / "artifacts"
    / "agent_governance_graph.json"
)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def validate_graph(graph):
    schema = load_json(
        GRAPH_SCHEMA_PATH
    )

    jsonschema.validate(
        instance=graph,
        schema=schema,
    )


def export_graph(path=DEFAULT_EXPORT_PATH):
    graph = build_graph()

    validate_graph(graph)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(path, "w") as f:
        json.dump(
            graph,
            f,
            indent=2,
        )

    return graph


def main():
    graph = export_graph()

    print(
        json.dumps(
            {
                "status": "SUCCESS",
                "graph_version": graph["graph_version"],
                "node_count": len(graph["nodes"]),
                "edge_count": len(graph["edges"]),
                "output_path": str(DEFAULT_EXPORT_PATH),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()