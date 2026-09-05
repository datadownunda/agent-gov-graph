import json

from src.foreign_opa_evidence import ingest_journal, ingest_opa
from src.evidence_correlation import correlate


def native():
    return {"type": "openpolicyagent.org/decision_logs", "decision_id": "native-id",
            "timestamp": "2026-09-05T12:00:00.123456789Z",
            "input": {"user": {"id": "alice"}, "action": "read",
                      "resource": {"id": "c1", "type": "complaint"}},
            "result": {"decision": "ALLOW"}}


def test_native_selection_locations_timestamps_and_read_only(tmp_path):
    path = tmp_path / "native.jsonl"
    diagnostic = b'{"level":"info","msg":"startup"}\n'
    raw = json.dumps(native()).encode() + b"\n"
    path.write_bytes(diagnostic + raw)
    path.chmod(0o444)
    before = path.stat()
    first = ingest_opa(path, ingested_at="2026-09-05T13:00:00Z")
    second = ingest_opa(path, ingested_at="2026-09-05T14:00:00Z")
    assert path.read_bytes() == diagnostic + raw
    assert path.stat().st_mtime_ns == before.st_mtime_ns
    assert len(first) == 1
    event = first[0]
    assert event["raw_record"] == native()
    assert event["observed_at"] == native()["timestamp"]
    assert event["ingested_at"] != event["observed_at"]
    assert event["evidence_ref"] == second[0]["evidence_ref"]
    assert event["location"]["line"] == 2
    assert event["location"]["byte_offset"] == len(diagnostic)
    assert event["location"]["byte_length"] == len(raw)
    assert event["location"]["path"] == str(path.resolve())
    assert event["content_digest"].startswith("sha256:")


def test_malformed_lines_and_native_fields_are_visible_defects(tmp_path):
    path = tmp_path / "bad.jsonl"
    bad = native()
    bad["input"] = None
    path.write_text("broken json\n" + json.dumps(bad) + "\n")
    events = ingest_opa(path)
    assert len(events) == 2
    assert all(e["defects"] for e in events)


def test_journal_ingestion_uses_request_observation_time(tmp_path):
    path = tmp_path / "journal.jsonl"
    path.write_text(json.dumps({"actor": "alice", "action": "read", "resource_id": "c1",
                               "resource_type": "complaint", "observed_at": "2026-09-05T12:00:00Z"}) + "\n")
    assert ingest_journal(path)[0]["actor"] == "alice"


def test_duplicate_native_lines_remain_distinct_observations(tmp_path):
    path = tmp_path / "native.jsonl"
    path.write_text((json.dumps(native()) + "\n") * 2)
    events = ingest_opa(path)
    assert events[0]["content_digest"] == events[1]["content_digest"]
    assert events[0]["evidence_ref"] != events[1]["evidence_ref"]
    journal = [{"evidence_ref": "request", "actor": "alice", "action": "read",
                "resource_id": "c1", "resource_type": "complaint",
                "observed_at": native()["timestamp"]}]
    assert {r["state"] for r in correlate(events, journal, window_seconds=2)} == {"AMBIGUOUS"}
