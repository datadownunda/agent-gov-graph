import json
from pathlib import Path

from src.governance_event import evaluate_policy, build_event, validate_event


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_PATH = ROOT / "evals" / "complaint_access_scenarios.json"


def load_scenarios():
    with open(SCENARIOS_PATH) as f:
        return json.load(f)


def evaluate_scenario(scenario):
    decision = evaluate_policy(scenario["input"])
    event = build_event(scenario["input"], decision)
    validate_event(event)

    expected = scenario["expected"]

    decision_correct = event["decision"]["status"] == expected["decision"]

    policy_correct = event["policy"]["name"] == expected["policy"]

    reason_correct = True

    if "reason_contains" in expected:
        reason_correct = any(
            expected["reason_contains"] in reason
            for reason in event["decision"]["reasons"]
        )

    evidence_complete = all(
        [
            event.get("event_id"),
            event.get("timestamp"),
            event.get("subject"),
            event.get("action"),
            event.get("resource"),
            event.get("policy"),
            event.get("decision"),
        ]
    )

    overall_pass = all(
        [
            decision_correct,
            policy_correct,
            reason_correct,
            evidence_complete,
        ]
    )

    return {
        "scenario_id": scenario["scenario_id"],
        "description": scenario["description"],
        "decision_correct": decision_correct,
        "policy_correct": policy_correct,
        "reason_correct": reason_correct,
        "evidence_complete": evidence_complete,
        "overall_pass": overall_pass,
    }


def main():
    scenarios = load_scenarios()

    for scenario in scenarios:
        result = evaluate_scenario(scenario)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()