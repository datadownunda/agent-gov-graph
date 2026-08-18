import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]

SCHEMA_PATH = ROOT / "schemas" / "governance_decision_event.schema.json"
VALID_EVENT_PATH = ROOT / "schemas" / "governance_decision_event.example.json"
INVALID_EVENT_PATH = ROOT / "tests" / "fixtures" / "governance_decision_event.invalid.json"


def load_json(path):
    with open(path) as f:
        return json.load(f)


def test_valid_governance_event():
    schema = load_json(SCHEMA_PATH)
    event = load_json(VALID_EVENT_PATH)

    jsonschema.validate(instance=event, schema=schema)


def test_invalid_governance_event_missing_policy_version():
    schema = load_json(SCHEMA_PATH)
    event = load_json(INVALID_EVENT_PATH)

    try:
        jsonschema.validate(instance=event, schema=schema)
        raise AssertionError("Invalid governance event unexpectedly passed validation")
    except jsonschema.ValidationError as error:
        assert "'version' is a required property" in str(error)