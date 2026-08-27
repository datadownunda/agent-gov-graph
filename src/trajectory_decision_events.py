import json

from src.governance_event import (
    build_event,
    evaluate_policy,
    validate_event,
)

from src.trajectory_eval import (
    MULTIAGENT_EXPECTATIONS_PATH,
    MULTIAGENT_TRAJECTORY_PATH,
    load_json,
)


def authorized_resource_ids_for_actor(
    expectations,
    actor_id,
):
    actor_expectations = expectations["actors"][actor_id]

    return [
        resource["id"]
        for resource in actor_expectations["allowed_resources"]
    ]


def build_policy_input(
    step,
    expectations,
):
    actor = step["actor"]

    authorized_resource_ids = (
        authorized_resource_ids_for_actor(
            expectations,
            actor["id"],
        )
    )

    return {
        "user": {
            "id": actor["id"],
            "roles": actor["roles"],
        },
        "authorized_resource_ids": authorized_resource_ids,
        "action": step["action"],
        "resource": {
            "id": step["resource"]["id"],
            "type": step["resource"]["type"],
            "classification": step["resource"]["classification"],
        },
    }


def generate_trajectory_decision_events(
    trajectory,
    expectations,
):
    results = []

    for step in trajectory["steps"]:

        if step["event_type"] != "resource_access":
            continue

        policy_input = build_policy_input(
            step,
            expectations,
        )

        decision = evaluate_policy(
            policy_input,
        )

        context = {
            "workflow_id": trajectory["workflow"],
            "run_id": trajectory["run_id"],
            "step_id": step["step_id"],
            "agent_id": step["actor"]["id"],
        }

        event = build_event(
            policy_input,
            decision,
            context=context,
        )

        validate_event(event)

        outcome_matches_observation = (
            event["decision"]["status"]
            == step["observed_outcome"]
        )

        results.append(
            {
                "step_id": step["step_id"],
                "observed_outcome": step["observed_outcome"],
                "outcome_matches_observation":
                    outcome_matches_observation,
                "decision_event": event,
            }
        )

    return results


def main():
    trajectory = load_json(
        MULTIAGENT_TRAJECTORY_PATH
    )

    expectations = load_json(
        MULTIAGENT_EXPECTATIONS_PATH
    )

    results = generate_trajectory_decision_events(
        trajectory,
        expectations,
    )

    print(
        json.dumps(
            results,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()