import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "input.json"
SCHEMA_PATH = ROOT / "schemas" / "governance_decision_event.schema.json"


def load_json(path):
    with open(path) as f:
        return json.load(f)


def evaluate_policy(input_data):
    opa_result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-i",
            "-v",
            f"{ROOT}:/workspace",
            "openpolicyagent/opa:1.19.0",
            "eval",
            "--format=json",
            "--stdin-input",
            "--data",
            "/workspace/policies/complaints.rego",
            "data.agentgov.complaints.decision",
        ],
        input=json.dumps(input_data),
        text=True,
        capture_output=True,
        check=True,
    )

    opa_output = json.loads(opa_result.stdout)

    return opa_output["result"][0]["expressions"][0]["value"]


def build_event(input_data, decision, context=None, telemetry=None):
    event = {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "subject": {
            "id": input_data["user"]["id"],
            "roles": input_data["user"]["roles"],
        },
        "action": input_data["action"],
        "resource": {
            "id": input_data["resource"]["id"],
            "type": input_data["resource"]["type"],
            "classification": input_data["resource"]["classification"],
        },
        "policy": {
            "name": decision["policy"],
            "version": decision["policy_version"],
        },
        "decision": {
            "allowed": decision["allowed"],
            "status": decision["decision"],
            "reasons": decision["reasons"],
        },
    }
    if context is not None:
        event["context"] = context

    if telemetry is not None:
        event["telemetry"] = telemetry

    return event

def validate_event(event):
    schema = load_json(SCHEMA_PATH)
    jsonschema.validate(instance=event, schema=schema)


def main():
    input_data = load_json(INPUT_PATH)
    decision = evaluate_policy(input_data)
    event = build_event(input_data, decision)
    validate_event(event)

    print(json.dumps(event, indent=2))


if __name__ == "__main__":
    main()

