import json
from pathlib import Path

from src.trajectory_decision_events import (
    generate_trajectory_decision_events,
)

from src.trajectory_eval import (
    MULTIAGENT_EXPECTATIONS_PATH,
)


ROOT = Path(__file__).resolve().parents[1]

TRAJECTORY_PATH = (
    ROOT
    / "trajectories"
    / "complaint_review_multiagent_trajectory.json"
)

INVESTIGATION_PATH = (
    ROOT
    / "investigations"
    / "complaint_review_investigation.json"
)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def add_node(nodes, node_id, node_type, properties=None):
    nodes[node_id] = {
        "id": node_id,
        "type": node_type,
        "properties": properties or {},
    }


def add_edge(edges, source, relationship, target, properties=None):
    edges.append(
        {
            "source": source,
            "relationship": relationship,
            "target": target,
            "properties": properties or {},
        }
    )


def project_trajectory(trajectory, nodes, edges):
    run_node_id = f"run:{trajectory['run_id']}"

    add_node(
        nodes,
        run_node_id,
        "Run",
        {
            "workflow": trajectory["workflow"],
            "goal": trajectory["goal"],
        },
    )

    for step in trajectory["steps"]:
        step_node_id = f"step:{step['step_id']}"

        add_node(
            nodes,
            step_node_id,
            "Step",
            {
                "sequence": step["sequence"],
                "event_type": step["event_type"],
                "observed_outcome": step["observed_outcome"],
            },
        )

        add_edge(
            edges,
            run_node_id,
            "CONTAINS_STEP",
            step_node_id,
        )

        actor = step["actor"]
        actor_node_id = f"actor:{actor['id']}"

        add_node(
            nodes,
            actor_node_id,
            "Actor",
            {
                "actor_type": actor["type"],
            },
        )

        add_edge(
            edges,
            actor_node_id,
            "PERFORMED",
            step_node_id,
        )

        if "parent_step_id" in step:
            parent_node_id = f"step:{step['parent_step_id']}"

            add_edge(
                edges,
                parent_node_id,
                "PRECEDES",
                step_node_id,
            )

        if "resource" in step:
            resource = step["resource"]

            resource_node_id = (
                f"resource:{resource['type']}:{resource['id']}"
            )

            add_node(
                nodes,
                resource_node_id,
                "Resource",
                {
                    "resource_id": resource["id"],
                    "resource_type": resource["type"],
                },
            )

            add_edge(
                edges,
                step_node_id,
                "ACCESSED",
                resource_node_id,
            )

        if "tool" in step:
            tool_node_id = f"tool:{step['tool']}"

            add_node(
                nodes,
                tool_node_id,
                "Tool",
                {
                    "name": step["tool"],
                },
            )

            add_edge(
                edges,
                step_node_id,
                "CALLED",
                tool_node_id,
            )

        if step["event_type"] == "agent_delegation":
            target_actor = step["target_actor"]

            target_actor_node_id = (
                f"actor:{target_actor['id']}"
            )

            add_node(
                nodes,
                target_actor_node_id,
                "Actor",
                {
                    "actor_type": target_actor["type"],
                },
            )

            add_edge(
                edges,
                actor_node_id,
                "DELEGATED_TO",
                target_actor_node_id,
                {
                    "step_id": step["step_id"],
                },
            )


def project_investigation(investigation, nodes, edges):
    investigation_node_id = (
        f"investigation:{investigation['investigation_id']}"
    )

    add_node(
        nodes,
        investigation_node_id,
        "Investigation",
        {
            "evidence_type": investigation[
                "investigation_context"
            ]["evidence_type"],
            "production_execution": investigation[
                "investigation_context"
            ]["production_execution"],
        },
    )

    source_finding = investigation["source_finding"]

    finding_node_id = (
        f"finding:"
        f"{source_finding['type']}:"
        f"{source_finding['step_id']}"
    )

    add_node(
        nodes,
        finding_node_id,
        "Finding",
        {
            "finding_type": source_finding["type"],
            "actor_id": source_finding["actor_id"],
        },
    )

    source_step_node_id = (
        f"step:{source_finding['step_id']}"
    )

    add_edge(
        edges,
        source_step_node_id,
        "PRODUCED_FINDING",
        finding_node_id,
    )

    add_edge(
        edges,
        finding_node_id,
        "INVESTIGATED_BY",
        investigation_node_id,
    )

    for hypothesis in investigation["hypotheses"]:
        hypothesis_node_id = (
            f"hypothesis:{hypothesis['hypothesis_id']}"
        )

        add_node(
            nodes,
            hypothesis_node_id,
            "Hypothesis",
            {
                "statement": hypothesis["statement"],
                "status": hypothesis["status"],
            },
        )

        add_edge(
            edges,
            investigation_node_id,
            "HAS_HYPOTHESIS",
            hypothesis_node_id,
        )

    for experiment in investigation["experiments"]:
        experiment_node_id = (
            f"experiment:{experiment['experiment_id']}"
        )

        hypothesis_node_id = (
            f"hypothesis:{experiment['hypothesis_id']}"
        )

        add_node(
            nodes,
            experiment_node_id,
            "Experiment",
            {
                "status": experiment["status"],
                "independent_variable":
                    experiment["independent_variable"],
                "outcome_metric":
                    experiment["outcome_metric"],
            },
        )

        add_edge(
            edges,
            hypothesis_node_id,
            "TESTED_BY",
            experiment_node_id,
        )

    for evidence in investigation["evidence"]:
        evidence_node_id = (
            f"evidence:{evidence['evidence_id']}"
        )

        experiment_node_id = (
            f"experiment:{evidence['experiment_id']}"
        )

        hypothesis_node_id = (
            f"hypothesis:{evidence['hypothesis_id']}"
        )

        add_node(
            nodes,
            evidence_node_id,
            "Evidence",
            {
                "evidence_type": evidence["evidence_type"],
                "relationship": evidence["relationship"],
                "observation": evidence["observation"],
            },
        )

        add_edge(
            edges,
            experiment_node_id,
            "PRODUCED_EVIDENCE",
            evidence_node_id,
        )

        add_edge(
            edges,
            evidence_node_id,
            evidence["relationship"],
            hypothesis_node_id,
        )

def project_decision_events(
    decision_results,
    nodes,
    edges,
):
    for result in decision_results:
        event = result["decision_event"]

        run_id = event["context"]["run_id"]
        step_id = event["context"]["step_id"]

        decision_node_id = (
            f"decision:{run_id}:{step_id}"
        )

        policy = event["policy"]

        policy_node_id = (
            f"policy:{policy['name']}:{policy['version']}"
        )

        add_node(
            nodes,
            decision_node_id,
            "Decision",
            {
                "event_id": event["event_id"],
                "timestamp": event["timestamp"],
                "status": event["decision"]["status"],
                "allowed": event["decision"]["allowed"],
                "reasons": event["decision"]["reasons"],
                "outcome_matches_observation":
                    result["outcome_matches_observation"],
            },
        )

        add_node(
            nodes,
            policy_node_id,
            "Policy",
            {
                "name": policy["name"],
                "version": policy["version"],
            },
        )

        step_node_id = f"step:{step_id}"

        add_edge(
            edges,
            step_node_id,
            "PRODUCED_DECISION",
            decision_node_id,
        )

        add_edge(
            edges,
            decision_node_id,
            "APPLIED_POLICY",
            policy_node_id,
        )

def build_graph():
    trajectory = load_json(TRAJECTORY_PATH)
    investigation = load_json(INVESTIGATION_PATH)

    expectations = load_json(
        MULTIAGENT_EXPECTATIONS_PATH
    )

    decision_results = (
        generate_trajectory_decision_events(
            trajectory,
            expectations,
        )
    )

    nodes = {}
    edges = []

    project_trajectory(
        trajectory,
        nodes,
        edges,
    )

    project_investigation(
        investigation,
        nodes,
        edges,
    )

    project_decision_events(
        decision_results,
        nodes,
        edges,
    )

    return {
    "graph_version": "1.0",
    "nodes": list(nodes.values()),
    "edges": edges,
    }


def main():
    graph = build_graph()

    print(
        json.dumps(
            graph,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()