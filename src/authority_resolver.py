import json
from pathlib import Path
from datetime import datetime, timezone


PROJECT_ROOT = Path(__file__).resolve().parents[1]

AUTHORITY_SOURCE_PATH = (
    PROJECT_ROOT
    / "runtime_resources"
    / "authority"
    / "agent_authority.json"
)

def utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def load_authority_source(
    path=AUTHORITY_SOURCE_PATH,
):
    with Path(path).open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def resolve_authority(
    actor_id,
    path=AUTHORITY_SOURCE_PATH,
):
    source = load_authority_source(path)

    principals = source["principals"]

    if actor_id not in principals:
        raise ValueError(
            f"No authority record found "
            f"for actor: {actor_id}"
        )

    principal = principals[actor_id]

    return {
        "actor_id": actor_id,
        "roles": principal["roles"],
        "authorized_resource_ids":
            principal[
                "authorized_resource_ids"
            ],
        "provenance": {
    "source_id":
        source["source_id"],
    "source_version":
        source["source_version"],
    "valid_from":
        source["valid_from"],
    "resolved_at":
        utc_now(),
},
    }