"""Read-only replay of temporal authority from a verified preserved revision."""
import argparse
import json

import jsonschema

from src.authority_resolver import (
    PROJECT_ROOT, RULE_VERSION, boundary_status, instant, load_authority_source,
    load_preserved_revision, resolve_authority,
)


def reconstruct_authority(event, history_directory):
    binding = event.get("context", {}).get("authority_binding")
    if not binding or not binding.get("revision"):
        return {"status": "INSUFFICIENT_EVIDENCE", "reason": "No preserved authority revision binding"}
    try:
        schema = load_authority_source(PROJECT_ROOT / "schemas/authority_resolution.schema.json")
        jsonschema.validate(binding, schema, format_checker=jsonschema.FormatChecker())
        revision = load_preserved_revision(binding["revision"], history_directory)
        actor = event["subject"]["id"]
        first = resolve_authority(actor, effective_at=binding["authority_resolution_at"], registry_revision=revision)
        second = resolve_authority(actor, effective_at=binding["opa_decision_at"], registry_revision=revision)
        status = boundary_status(first, second)
        if second["status"] != "EVIDENCE_DEFECT" and instant(binding["opa_decision_at"]) < instant(binding["authority_resolution_at"]):
            status = "EVIDENCE_DEFECT"
        if (binding["rule_version"] != RULE_VERSION or first != binding["at_resolution"]
                or second != binding["at_opa_decision"] or status != binding["status"]
                or first["basis"] is None or sorted(set(event["subject"]["roles"])) != first["basis"]["roles"]):
            return {"status": "CONTRADICTED", "reason": "Recorded binding differs from temporal reconstruction"}
        return {"status": "VERIFIED" if status == "RESOLVED" else status,
                "authority_status": status, "at_resolution": first, "at_opa_decision": second,
                "revision": binding["revision"], "rule_version": RULE_VERSION}
    except FileNotFoundError:
        return {"status": "INSUFFICIENT_EVIDENCE", "reason": "Preserved authority revision is missing"}
    except (OSError, ValueError, TypeError, KeyError, jsonschema.ValidationError):
        return {"status": "EVIDENCE_DEFECT", "reason": "Invalid binding or unverifiable authority revision"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("governance_jsonl")
    parser.add_argument("--history-directory", required=True)
    args = parser.parse_args()
    with open(args.governance_jsonl, encoding="utf-8") as stream:
        for line in stream:
            print(json.dumps(reconstruct_authority(json.loads(line), args.history_directory)))


if __name__ == "__main__":
    main()
