import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_GOVERNANCE_LOG = (
    PROJECT_ROOT
    / "artifacts"
    / "runtime_governance_events.jsonl"
)

DEFAULT_EXECUTION_LOG = (
    PROJECT_ROOT
    / "artifacts"
    / "runtime_execution_events.jsonl"
)

COVERAGE_CONTRACT_PATH = (
    PROJECT_ROOT
    / "controls"
    / "runtime_coverage_contract.json"
)


def load_json(path):
    with Path(path).open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_jsonl(path):
    path = Path(path)

    if not path.exists():
        return []

    events = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if line:
                events.append(
                    json.loads(line)
                )

    return events


def governance_required(
    contract,
    action,
    resource_type,
):
    for rule in contract[
        "governed_actions"
    ]:
        if (
            rule["action"] == action
            and
            rule["resource_type"]
            == resource_type
        ):
            return rule[
                "governance_required"
            ]

    return False


def governance_key(event):
    return event["context"][
        "action_attempt_id"
    ]


def execution_key(event):
    return event[
        "action_attempt_id"
    ]


def reconcile_runtime(
    governance_events,
    execution_events,
    coverage_contract,
):
    governance_by_key = {
        governance_key(event): event
        for event in governance_events
    }

    execution_by_key = {
        execution_key(event): event
        for event in execution_events
    }

    all_keys = (
        set(governance_by_key)
        | set(execution_by_key)
    )

    results = []

    for key in sorted(all_keys):
        governance_event = (
            governance_by_key.get(key)
        )

        execution_event = (
            execution_by_key.get(key)
        )

        source_event = (
            governance_event
            or execution_event
        )

        if governance_event:
            run_id = governance_event[
                "context"
            ]["run_id"]

            step_id = governance_event[
                "context"
            ]["step_id"]

            actor_id = governance_event[
                "subject"
            ]["id"]

        else:
            run_id = execution_event["run_id"]
            step_id = execution_event["step_id"]
            actor_id = execution_event["actor_id"]

        action = source_event["action"]
        resource_id = source_event[
            "resource"
        ]["id"]

        resource_type = (
            source_event["resource"]["type"]
        )

        required = governance_required(
            coverage_contract,
            action,
            resource_type,
        )

        decision_status = None

        if governance_event:
            decision_status = (
                governance_event[
                    "decision"
                ]["status"]
            )

        effect_observed = (
            execution_event is not None
        )

        if required and not governance_event:
            coverage_status = (
                "COVERAGE_MISSING"
            )
        elif governance_event:
            coverage_status = "COVERED"
        else:
            coverage_status = (
                "NOT_REQUIRED"
            )

        if (
            decision_status == "DENY"
            and effect_observed
        ):
            enforcement_status = (
                "FAILED"
            )

        elif (
            decision_status == "DENY"
            and not effect_observed
        ):
            enforcement_status = (
                "CONSISTENT_WITH_BLOCKING"
            )

        elif (
            decision_status == "ALLOW"
            and effect_observed
        ):
            enforcement_status = (
                "PROCEEDED"
            )

        elif (
            decision_status == "ALLOW"
            and not effect_observed
        ):
            enforcement_status = (
                "NO_EFFECT_OBSERVED"
            )

        else:
            enforcement_status = (
                "NOT_EVALUABLE"
            )

        if (
            coverage_status
            == "COVERAGE_MISSING"
            and effect_observed
        ):
            classification = (
                "COVERAGE_FAILURE"
            )

        elif (
            decision_status == "DENY"
            and effect_observed
        ):
            classification = (
                "ENFORCEMENT_FAILURE"
            )

        elif (
            decision_status == "DENY"
            and not effect_observed
        ):
            classification = (
                "DENY_EFFECT_NOT_OBSERVED"
            )

        elif (
            decision_status == "ALLOW"
            and effect_observed
        ):
            classification = (
                "GOVERNED_ALLOWED_EXECUTION"
            )

        else:
            classification = (
                "UNRESOLVED"
            )

        results.append({
            "run_id": run_id,
            "step_id": step_id,
            "action_attempt_id": key,
            "actor_id": actor_id,
            "action": action,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "coverage_required": required,
            "coverage_status": coverage_status,
            "decision_status": (
                decision_status
                or "NO_DECISION"
            ),
            "enforcement_status":
                enforcement_status,
            "outcome_status": (
                execution_event["effect"]
                if execution_event
                else "NO_EFFECT_OBSERVED"
            ),
            "classification":
                classification,
            "evidence": {
                "governance_event_id": (
                    governance_event[
                        "event_id"
                    ]
                    if governance_event
                    else None
                ),
                "execution_event_id": (
                    execution_event[
                        "event_id"
                    ]
                    if execution_event
                    else None
                ),
            },
        })

    return results


def main():
    governance_events = load_jsonl(
        DEFAULT_GOVERNANCE_LOG
    )

    execution_events = load_jsonl(
        DEFAULT_EXECUTION_LOG
    )

    coverage_contract = load_json(
        COVERAGE_CONTRACT_PATH
    )

    results = reconcile_runtime(
        governance_events,
        execution_events,
        coverage_contract,
    )

    print(
        json.dumps(
            results,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()