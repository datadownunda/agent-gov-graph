import os

from neo4j import GraphDatabase

from src.graph_export import validate_graph
from src.graph_projection import build_graph
from src.ontology_validator import (
    ONTOLOGY_PATH,
    load_json,
    validate_graph_ontology,
)


NEO4J_URI = os.getenv(
    "NEO4J_URI",
    "neo4j://localhost:7687",
)

NEO4J_USER = os.getenv(
    "NEO4J_USER",
    "neo4j",
)

NEO4J_PASSWORD = os.getenv(
    "NEO4J_PASSWORD"
)


def get_driver():
    if not NEO4J_PASSWORD:
        raise ValueError(
            "NEO4J_PASSWORD environment variable is required"
        )

    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(
            NEO4J_USER,
            NEO4J_PASSWORD,
        ),
    )


def store_node(tx, node):
    tx.run(
        """
        MERGE (n:AgentGovNode {id: $id})
        SET n.type = $type
        SET n += $properties
        """,
        id=node["id"],
        type=node["type"],
        properties=node["properties"],
    )


def store_edge(tx, edge):
    tx.run(
        """
        MATCH (source:AgentGovNode {id: $source})
        MATCH (target:AgentGovNode {id: $target})
        MERGE (source)-[r:AGENT_GOV_RELATIONSHIP {
            relationship: $relationship
        }]->(target)
        SET r += $properties
        """,
        source=edge["source"],
        target=edge["target"],
        relationship=edge["relationship"],
        properties=edge["properties"],
    )


def store_graph(graph):
    validate_graph(graph)

    ontology = load_json(ONTOLOGY_PATH)

    ontology_errors = validate_graph_ontology(
        graph,
        ontology,
    )

    if ontology_errors:
        raise ValueError(
            f"Graph failed ontology validation: {ontology_errors}"
        )

    driver = get_driver()

    try:
        with driver.session() as session:
            for node in graph["nodes"]:
                session.execute_write(
                    store_node,
                    node,
                )

            for edge in graph["edges"]:
                session.execute_write(
                    store_edge,
                    edge,
                )

    finally:
        driver.close()


def main():
    graph = build_graph()

    store_graph(graph)

    print(
        f"Stored {len(graph['nodes'])} nodes "
        f"and {len(graph['edges'])} edges in Neo4j"
    )


if __name__ == "__main__":
    main()