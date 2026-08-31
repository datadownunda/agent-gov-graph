import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

COMPLAINT_DIR = (
    PROJECT_ROOT
    / "runtime_resources"
    / "complaints"
)

DEFAULT_EXECUTION_LOG = (
    PROJECT_ROOT
    / "artifacts"
    / "runtime_execution_events.jsonl"
)


def utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def append_execution_event(
    event,
    log_path=DEFAULT_EXECUTION_LOG,
):
    log_path = Path(log_path)

    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with log_path.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(event)
            + "\n"
        )


def read_complaint(
    resource_id,
    *,
    run_id,
    step_id,
    actor_id,
    action_attempt_id=None,
    log_path=DEFAULT_EXECUTION_LOG,
):
    if action_attempt_id is None:
        action_attempt_id = str(
            uuid.uuid4()
        )

    resource_path = (
        COMPLAINT_DIR
        / f"{resource_id}.json"
    )

    with resource_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        complaint = json.load(file)

    execution_event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": utc_now(),
        "action_attempt_id":
            action_attempt_id,
        "run_id": run_id,
        "step_id": step_id,
        "actor_id": actor_id,
        "action": "read",
        "resource": {
            "id": complaint["id"],
            "type": complaint["type"],
            "classification":
                complaint[
                    "classification"
                ],
        },
        "effect": "RESOURCE_READ",
        "source": "complaint_store",
    }

    append_execution_event(
        execution_event,
        log_path,
    )

    return complaint