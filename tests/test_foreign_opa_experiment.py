"""Producer contract tests plus an opt-in real Docker/OPA custody-path test."""

import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from src.evidence_correlation import correlate
from src.foreign_opa_evidence import ingest_journal, ingest_opa


ROOT = Path(__file__).resolve().parents[1]
PRODUCER = ROOT / "experiments/foreign_opa/produce.py"


def test_producer_uses_inherited_stderr_and_no_shared_ids(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("standalone_producer", PRODUCER)
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    calls = []
    journal = tmp_path / "journal.jsonl"

    def fake_run(command, **kwargs):
        # Journal is persisted before each request, independently of OPA output.
        rows = journal.read_text().splitlines()
        assert len(rows) == len(calls) + 1
        assert set(json.loads(rows[-1])) == {"actor", "action", "resource_id", "resource_type", "observed_at"}
        assert "stderr" not in kwargs and "capture_output" not in kwargs
        assert "--set=decision_logs.console=true" in command
        assert kwargs["stdout"] == subprocess.DEVNULL
        assert set(json.loads(kwargs["input"])) == {"user", "action", "authorized_resource_ids", "resource"}
        calls.append(command)

    monkeypatch.setattr(producer.subprocess, "run", fake_run)
    producer.produce(journal, ROOT / "policies", count=2)
    assert len(calls) == 2
    tree = ast.parse(PRODUCER.read_text())
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
    assert not any(name == "src" or name.startswith("src.") for name in imports)


@pytest.mark.skipif(os.environ.get("RUN_FOREIGN_OPA") != "1", reason="requires local Docker OPA image")
def test_real_separately_persisted_opa_consumed_later(tmp_path):
    journal, native_log = tmp_path / "journal.jsonl", tmp_path / "native.jsonl"
    # The external test operator owns the file descriptor. The producer inherits
    # it, and passes it through untouched to Docker/OPA.
    with native_log.open("xb") as stderr:
        subprocess.run([sys.executable, "-I", "-B", str(PRODUCER), "--journal", str(journal),
                        "--policy-dir", str(ROOT / "policies"), "--count", "2"],
                       stderr=stderr, check=True, cwd=tmp_path)
    snapshots = {path: path.read_bytes() for path in (journal, native_log)}
    for path in snapshots:
        path.chmod(0o444)
    opa, requests = ingest_opa(native_log), ingest_journal(journal)
    assert len(opa) == len(requests) == 2
    assert all(not r["defects"] for r in opa + requests)
    assert all("action_attempt_id" not in r["raw_record"]["input"] for r in opa)
    assert all(r["raw_record"]["decision_id"] for r in opa)
    # A generous explicit window accommodates container startup in this custody
    # test and ensures repeated observations compete. It is not a production bound.
    findings = correlate(opa, requests, window_seconds=60)
    assert {r["state"] for r in findings} == {"AMBIGUOUS"}
    assert {r["state"] for r in correlate(opa[:1], requests[:1], window_seconds=60)} == {"MATCHED"}
    assert correlate(ingest_opa(native_log) * 2, ingest_journal(journal) * 2,
                     window_seconds=60) == findings
    assert all(path.read_bytes() == raw for path, raw in snapshots.items())
