"""Valid-time authority states and content-verified registry revisions.

Records are complete principal states, not additive grants. No current-state
fallback is permitted by the resolver or historical archive loader.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import jsonschema

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_SOURCE_PATH = PROJECT_ROOT / "runtime_resources/authority/agent_authority.json"
RULE_VERSION = "temporal-authority/1"
TIMESTAMP = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d{1,9})?(Z|[+-]\d{2}:\d{2})$")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def instant(value):
    """RFC3339 instants, retaining OPA's nanoseconds; reject naive dates."""
    match = TIMESTAMP.fullmatch(value) if isinstance(value, str) else None
    if not match or not jsonschema.FormatChecker().conforms(value, "date-time"):
        raise ValueError("Invalid timezone-aware authority timestamp")
    base, fraction, offset = match.groups()
    parsed = datetime.fromisoformat(base + offset.replace("Z", "+00:00"))
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = parsed - epoch
    return Decimal(delta.days * 86400 + delta.seconds) + Decimal(fraction or "0")


def load_authority_source(path=AUTHORITY_SOURCE_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_revision(revision):
    schema = load_authority_source(PROJECT_ROOT / "schemas/authority_registry.schema.json")
    jsonschema.validate(revision, schema, format_checker=jsonschema.FormatChecker())
    identities = {}
    for record in revision["records"]:
        start = instant(record["valid_from"])
        end = instant(record["valid_to"]) if record["valid_to"] is not None else None
        if end is not None and end <= start:
            raise ValueError("Authority validity interval must have positive duration")
        key = (record["authority_record_id"], record["authority_version"])
        if key in identities and identities[key] != record:
            raise ValueError("Conflicting contents for authority record ID/version")
        identities[key] = record


def revision_bytes(revision):
    return json.dumps(revision, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def preserve_revision(revision, directory):
    """Create once; refuse to overwrite a mismatching existing artifact."""
    validate_revision(revision)
    payload = revision_bytes(revision)
    digest = hashlib.sha256(payload).hexdigest()
    name = digest + ".json"
    path = Path(directory) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise ValueError("Preserved authority revision digest mismatch")
    return {"file": name, "digest": "sha256:" + digest,
            "source_id": revision["source_id"], "source_version": revision["source_version"]}


def load_preserved_revision(reference, directory):
    digest = reference.get("digest", "")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("Invalid authority revision digest")
    if reference.get("file") != digest[7:] + ".json":
        raise ValueError("Authority filename must identify its digest")
    payload = (Path(directory) / reference["file"]).read_bytes()
    if "sha256:" + hashlib.sha256(payload).hexdigest() != digest:
        raise ValueError("Preserved authority revision digest mismatch")
    revision = json.loads(payload)
    validate_revision(revision)
    if any(reference.get(key) != revision[key] for key in ("source_id", "source_version")):
        raise ValueError("Authority source reference mismatch")
    return revision


def authority_basis(record):
    # Scope syntax permits separate entries; normalize equivalent permission sets.
    scopes = {}
    for scope in record["permitted_scopes"]:
        scopes.setdefault((scope["action"], scope["resource_type"]), set()).update(scope["resource_ids"])
    return {"roles": sorted(set(record["roles"])), "permitted_scopes": [
        {"action": action, "resource_type": kind, "resource_ids": sorted(ids)}
        for (action, kind), ids in sorted(scopes.items()) if ids]}


def resolve_authority(actor_id, *, effective_at, registry_revision):
    result = {"status": "INSUFFICIENT_EVIDENCE", "principal": actor_id,
              "effective_at": effective_at if isinstance(effective_at, str) else None, "rule_version": RULE_VERSION,
              "record_refs": [], "candidates": [], "basis": None}
    try:
        if not isinstance(actor_id, str) or not actor_id:
            raise ValueError("Authority principal must be a nonempty string")
        at = instant(effective_at)
        validate_revision(registry_revision)
        unique = {(r["authority_record_id"], r["authority_version"]): r
                  for r in registry_revision["records"] if r["principal"] == actor_id}
        active = []
        for key, record in sorted(unique.items()):
            ref = {"authority_record_id": key[0], "authority_version": key[1]}
            start = instant(record["valid_from"])
            end = instant(record["valid_to"]) if record["valid_to"] is not None else None
            eligibility = "FUTURE" if at < start else "EXPIRED" if end is not None and at >= end else "EFFECTIVE"
            result["candidates"].append({**ref, "eligibility": eligibility})
            if eligibility == "EFFECTIVE":
                result["record_refs"].append(ref)
                active.append(authority_basis(record))
        if active:
            if any(basis != active[0] for basis in active[1:]):
                result["status"] = "CONFLICT"
            else:
                result.update(status="RESOLVED", basis=active[0])
    except (ValueError, TypeError, KeyError, jsonschema.ValidationError):
        result.update(status="EVIDENCE_DEFECT", basis=None)
    return result


def boundary_status(first, second):
    if second["status"] == "EVIDENCE_DEFECT":
        return "EVIDENCE_DEFECT"
    # A changed supporting version is a boundary, even if permissions are equal.
    if any(first[key] != second[key] for key in ("status", "record_refs", "basis")):
        return "TEMPORAL_BOUNDARY_AMBIGUITY"
    return first["status"]


def policy_authority(resolution, action, resource_type):
    if resolution["status"] != "RESOLVED":
        raise ValueError("Unresolved authority cannot supply policy input")
    basis = resolution["basis"]
    return {"roles": basis["roles"], "authorized_resource_ids": sorted({
        resource for scope in basis["permitted_scopes"]
        if scope["action"] == action and scope["resource_type"] == resource_type
        for resource in scope["resource_ids"]})}
