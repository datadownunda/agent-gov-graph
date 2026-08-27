from src.graph_projection import build_graph


def get_nodes_by_type(graph, node_type):
    return [
        node
        for node in graph["nodes"]
        if node["type"] == node_type
    ]


def has_edge(graph, source, relationship, target):
    return any(
        edge["source"] == source
        and edge["relationship"] == relationship
        and edge["target"] == target
        for edge in graph["edges"]
    )


def test_graph_contains_unique_actor_nodes():
    graph = build_graph()

    actors = get_nodes_by_type(
        graph,
        "Actor",
    )

    actor_ids = {
        actor["id"]
        for actor in actors
    }

    assert "actor:complaint-review-agent" in actor_ids
    assert "actor:policy-review-agent" in actor_ids

    assert len(actor_ids) == 2


def test_graph_represents_multiagent_delegation():
    graph = build_graph()

    assert has_edge(
        graph,
        "actor:complaint-review-agent",
        "DELEGATED_TO",
        "actor:policy-review-agent",
    )


def test_graph_connects_prohibited_step_to_finding():
    graph = build_graph()

    finding_id = (
        "finding:"
        "actor_prohibited_resource_attempt:"
        "step-004"
    )

    assert has_edge(
        graph,
        "step:step-004",
        "PRODUCED_FINDING",
        finding_id,
    )


def test_graph_connects_finding_to_investigation():
    graph = build_graph()

    finding_id = (
        "finding:"
        "actor_prohibited_resource_attempt:"
        "step-004"
    )

    assert has_edge(
        graph,
        finding_id,
        "INVESTIGATED_BY",
        "investigation:inv-complaint-001",
    )


def test_graph_connects_hypotheses_experiments_and_evidence():
    graph = build_graph()

    assert has_edge(
        graph,
        "investigation:inv-complaint-001",
        "HAS_HYPOTHESIS",
        "hypothesis:hyp-001",
    )

    assert has_edge(
        graph,
        "hypothesis:hyp-001",
        "TESTED_BY",
        "experiment:exp-001",
    )

    assert has_edge(
        graph,
        "experiment:exp-001",
        "PRODUCED_EVIDENCE",
        "evidence:evidence-001",
    )

    assert has_edge(
        graph,
        "evidence:evidence-001",
        "SUPPORTS",
        "hypothesis:hyp-001",
    )


def test_graph_connects_step_to_governance_decision():
    graph = build_graph()

    assert has_edge(
        graph,
        "step:step-001",
        "PRODUCED_DECISION",
        (
            "decision:"
            "run-complaint-multiagent-001:"
            "step-001"
        ),
    )

    assert has_edge(
        graph,
        "step:step-004",
        "PRODUCED_DECISION",
        (
            "decision:"
            "run-complaint-multiagent-001:"
            "step-004"
        ),
    )


def test_graph_connects_decision_to_policy():
    graph = build_graph()

    policy_id = (
        "policy:"
        "employee_complaint_access:"
        "1.0"
    )

    assert has_edge(
        graph,
        (
            "decision:"
            "run-complaint-multiagent-001:"
            "step-001"
        ),
        "APPLIED_POLICY",
        policy_id,
    )

    assert has_edge(
        graph,
        (
            "decision:"
            "run-complaint-multiagent-001:"
            "step-004"
        ),
        "APPLIED_POLICY",
        policy_id,
    )


def test_graph_preserves_allow_and_deny_decision_evidence():
    graph = build_graph()

    decisions = {
        node["id"]: node
        for node in graph["nodes"]
        if node["type"] == "Decision"
    }

    allow_decision = decisions[
        (
            "decision:"
            "run-complaint-multiagent-001:"
            "step-001"
        )
    ]

    deny_decision = decisions[
        (
            "decision:"
            "run-complaint-multiagent-001:"
            "step-004"
        )
    ]

    assert allow_decision["properties"]["status"] == "ALLOW"
    assert allow_decision["properties"]["allowed"] is True

    assert deny_decision["properties"]["status"] == "DENY"
    assert deny_decision["properties"]["allowed"] is False

    assert (
        deny_decision["properties"][
            "outcome_matches_observation"
        ]
        is True
    )