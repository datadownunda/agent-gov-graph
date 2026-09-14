"""Read-only adapters for separately persisted evidence, not authenticity checks."""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from src.evidence_digest import evidence_digest


FIELDS = ("actor", "action", "resource_id", "resource_type")
NATIVE_TYPE = "openpolicyagent.org/decision_logs"
RFC3339 = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,9}))?(Z|[+-]\d{2}:\d{2})$"
)


def timestamp_ns(value):
    """Parse timezone-aware RFC3339 without losing OPA nanosecond precision."""
    match = RFC3339.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise ValueError("timestamp must be RFC3339 with timezone and <=9 fractional digits")
    base, fraction, offset = match.groups()
    if offset != "Z" and (int(offset[1:3]) > 23 or int(offset[4:]) > 59):
        raise ValueError("invalid timezone offset")
    instant = datetime.fromisoformat(base + ("+00:00" if offset == "Z" else offset))
    delta = instant.astimezone(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 1_000_000_000 + int((fraction or "").ljust(9, "0"))


def correlation_defects(record):
    defects = list(record.get("defects", []))
    for field in FIELDS:
        if not isinstance(record.get(field), str) or not record[field].strip():
            defects.append(f"invalid {field}")
    try:
        timestamp_ns(record.get("observed_at"))
    except ValueError as error:
        defects.append(str(error))
    return sorted(set(defects))


def _sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _reject_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def _ingest(path, source, ingested_at):
    path = Path(path).resolve()
    # Only read handles are opened; no normalized copy is written into custody.
    with path.open("rb") as stream:
        raw_file = stream.read()
    file_digest = _sha(raw_file)
    ingested_at = ingested_at or datetime.now(timezone.utc).isoformat()
    events = []
    offset = 0
    for line_number, raw_line in enumerate(raw_file.splitlines(keepends=True), 1):
        location = {"path": str(path), "file_digest": file_digest, "line": line_number,
                    "byte_offset": offset, "byte_length": len(raw_line)}
        offset += len(raw_line)
        if not raw_line.strip():
            continue
        defects = []
        try:
            raw_record = json.loads(raw_line, parse_constant=_reject_constant)
            if not isinstance(raw_record, dict):
                raise ValueError("record is not an object")
        except (ValueError, UnicodeDecodeError) as error:
            raw_record = None
            defects.append(f"invalid JSON record: {error}")
        if source == "opa" and raw_record is not None and raw_record.get("type") != NATIVE_TYPE:
            # Valid console diagnostics are not decision evidence. Unparseable lines
            # remain defects: we cannot safely determine whether they were decisions.
            continue
        event = {"source": source, "location": location, "raw_record": raw_record,
                 "raw_line_digest": _sha(raw_line), "ingested_at": ingested_at,
                 "evidence_ref": evidence_digest({"source": source, **location}),
                 "defects": defects}
        if raw_record is not None:
            try:
                event["content_digest"] = evidence_digest(raw_record)
            except (ValueError, OverflowError) as error:
                defects.append(f"non-canonicalizable content: {error}")
            if source == "opa":
                policy_input = raw_record.get("input")
                policy_input = policy_input if isinstance(policy_input, dict) else {}
                user = policy_input.get("user")
                resource = policy_input.get("resource")
                event.update(actor=user.get("id") if isinstance(user, dict) else None,
                             action=policy_input.get("action"),
                             resource_id=resource.get("id") if isinstance(resource, dict) else None,
                             resource_type=resource.get("type") if isinstance(resource, dict) else None,
                             observed_at=raw_record.get("timestamp"))
            else:
                event.update({field: raw_record.get(field) for field in (*FIELDS, "observed_at")})
        event["defects"] = correlation_defects(event)
        events.append(event)
    return events


def ingest_opa(path, *, ingested_at=None):
    return _ingest(path, "opa", ingested_at)


def ingest_journal(path, *, ingested_at=None):
    return _ingest(path, "journal", ingested_at)
