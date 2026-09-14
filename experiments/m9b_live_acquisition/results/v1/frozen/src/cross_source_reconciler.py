from src.evidence_digest import (
    evidence_digest,
)


RECONCILER_VERSION = "1.0"

def reconcile_opa_governance(
    opa_event,
    governance_event,
):
    opa_attempt_id = (
        opa_event
        .get("input", {})
        .get("action_attempt_id")
    )

    governance_attempt_id = (
        governance_event
        .get("context", {})
        .get("action_attempt_id")
    )

    opa_digest = evidence_digest(
        opa_event
    )

    governance_digest = evidence_digest(
        governance_event
    )

    if (
        not opa_attempt_id
        or not governance_attempt_id
        or opa_attempt_id
        != governance_attempt_id
    ):
        return {
            "classification":
                "UNCORRELATABLE",
            "action_attempt_id": None,
            "mismatches": [],
            "evidence": {
                "opa_decision_id":
                    opa_event.get(
                        "decision_id"
                    ),
                "opa_digest":
                    opa_digest,
                "governance_event_id":
                    governance_event.get(
                        "event_id"
                    ),
                "governance_digest":
                    governance_digest,
            },
            "reconciler_version":
                RECONCILER_VERSION,
        }

    comparisons = {
        "decision": (
            opa_event["result"][
                "decision"
            ],
            governance_event[
                "decision"
            ]["status"],
        ),
        "actor_id": (
            opa_event["input"][
                "user"
            ]["id"],
            governance_event[
                "subject"
            ]["id"],
        ),
        "action": (
            opa_event["input"][
                "action"
            ],
            governance_event[
                "action"
            ],
        ),
        "resource_id": (
            opa_event["input"][
                "resource"
            ]["id"],
            governance_event[
                "resource"
            ]["id"],
        ),
        "resource_type": (
            opa_event["input"][
                "resource"
            ]["type"],
            governance_event[
                "resource"
            ]["type"],
        ),
        "policy": (
            opa_event["result"][
                "policy"
            ],
            governance_event[
                "policy"
            ]["name"],
        ),
        "policy_version": (
            opa_event["result"][
                "policy_version"
            ],
            governance_event[
                "policy"
            ]["version"],
        ),
    }

    mismatches = []

    for field, values in comparisons.items():
        opa_value, governance_value = values

        if opa_value != governance_value:
            mismatches.append({
                "field": field,
                "opa_value": opa_value,
                "governance_value":
                    governance_value,
            })

    classification = (
        "MATCH"
        if not mismatches
        else "MISMATCH"
    )

    return {
        "classification": classification,
        "action_attempt_id":
            opa_attempt_id,
        "mismatches": mismatches,
        "evidence": {
            "opa_decision_id":
                opa_event["decision_id"],
            "opa_digest":
                opa_digest,
            "governance_event_id":
                governance_event[
                    "event_id"
                ],
            "governance_digest":
                governance_digest,
        },
        "reconciler_version":
            RECONCILER_VERSION,
    }