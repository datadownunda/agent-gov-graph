import json
from pathlib import Path

import jsonschema

from src.complaint_store import (
    read_complaint,
)


ROOT = Path(__file__).resolve().parents[1]

SCHEMA_PATH = (
    ROOT
    / "schemas"
    / "execution_evidence_event.schema.json"
)


def load_json(path):
    with open(path) as file:
        return json.load(file)


def test_valid_execution_evidence_event():
    schema = load_json(
        SCHEMA_PATH
    )

    event = {
        "schema_version": "1.0",
        "event_id": "event-001",
        "timestamp":
            "2026-09-03T20:00:00+00:00",
        "action_attempt_id":
            "attempt-001",
        "run_id": "run-001",
        "step_id": "step-001",
        "actor_id":
            "complaint-review-agent",
        "action": "read",
        "resource": {
            "id": "complaint-456",
            "type":
                "employee_complaint",
            "classification":
                "restricted",
        },
        "effect": "RESOURCE_READ",
        "source": "complaint_store",
    }

    jsonschema.validate(
        instance=event,
        schema=schema,
    )


def test_runtime_execution_event_matches_schema(
    tmp_path,
):
    schema = load_json(
        SCHEMA_PATH
    )

    execution_log = (
        tmp_path
        / "execution.jsonl"
    )

    read_complaint(
        "complaint-456",
        run_id="run-schema-test",
        step_id="step-001",
        actor_id=
            "complaint-review-agent",
        action_attempt_id=
            "attempt-schema-test",
        log_path=execution_log,
    )

    with execution_log.open(
        "r",
        encoding="utf-8",
    ) as file:
        event = json.loads(
            file.readline()
        )

    jsonschema.validate(
        instance=event,
        schema=schema,
    )


def test_invalid_execution_evidence_event_missing_attempt_id():
    schema = load_json(
        SCHEMA_PATH
    )

    event = {
        "schema_version": "1.0",
        "event_id": "event-001",
        "timestamp":
            "2026-09-03T20:00:00+00:00",
        "run_id": "run-001",
        "step_id": "step-001",
        "actor_id":
            "complaint-review-agent",
        "action": "read",
        "resource": {
            "id": "complaint-456",
            "type":
                "employee_complaint",
            "classification":
                "restricted",
        },
        "effect": "RESOURCE_READ",
        "source": "complaint_store",
    }

    try:
        jsonschema.validate(
            instance=event,
            schema=schema,
        )
        raise AssertionError(
            "Invalid execution evidence "
            "unexpectedly passed validation"
        )
    except jsonschema.ValidationError as error:
        assert (
            "'action_attempt_id' is a required property"
            in str(error)
        )


def test_execution_evidence_event_rejects_unknown_schema_version():
    schema = load_json(
        SCHEMA_PATH
    )

    event = {
        "schema_version": "2.0",
        "event_id": "event-001",
        "timestamp":
            "2026-09-03T20:00:00+00:00",
        "action_attempt_id":
            "attempt-001",
        "run_id": "run-001",
        "step_id": "step-001",
        "actor_id":
            "complaint-review-agent",
        "action": "read",
        "resource": {
            "id": "complaint-456",
            "type":
                "employee_complaint",
            "classification":
                "restricted",
        },
        "effect": "RESOURCE_READ",
        "source": "complaint_store",
    }

    try:
        jsonschema.validate(
            instance=event,
            schema=schema,
        )
        raise AssertionError(
            "Unknown schema version "
            "unexpectedly passed validation"
        )
    except jsonschema.ValidationError as error:
        assert "1.0" in str(error)