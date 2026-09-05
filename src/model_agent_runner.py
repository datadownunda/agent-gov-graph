"""Single model proposal followed by existing governance and at most one dispatch."""

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import jsonschema

from src import complaint_runtime
from src.complaint_store import COMPLAINT_DIR
from src.evidence_digest import evidence_digest
from src.model_proposal import DEFAULT_MODEL, InvalidProposal, build_request, propose_openai, validate_proposal


SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "schemas/model_agent_evidence.schema.json").read_text())


def run_trial(task, candidates, *, output_dir, model=DEFAULT_MODEL, propose=propose_openai,
              actor_id="complaint-review-agent", run_id=None):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    run_id = run_id or str(uuid4())
    # Validate catalog membership using filenames only, never protected contents.
    catalog = {p.stem for p in COMPLAINT_DIR.glob("*.json")}
    request = build_request(task, candidates, model)
    presented = {c["resource_id"] for c in candidates}
    if not presented <= catalog:
        raise ValueError("Scenario catalog contains a nonexistent complaint")
    emitted_types = []

    def emit(event_type, data):
        event = {"schema_version": "1.0", "event_id": str(uuid4()),
                 "timestamp": datetime.now(timezone.utc).isoformat(), "run_id": run_id,
                 "event_type": event_type, "data": data, "data_digest": evidence_digest(data)}
        jsonschema.validate(event, SCHEMA)
        with (output / "agent.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event) + "\n")
        emitted_types.append(event_type)

    emit("MODEL_REQUEST", {"provider": "openai" if propose is propose_openai else "injected-adapter",
                           "requested_model": model, "request": request, "actor_id": actor_id})
    try:
        response = propose(request)
    except Exception as error:
        emit("MODEL_UNAVAILABLE", {"error_type": type(error).__name__, "message": str(error)})
        emit("EXECUTION_DISPOSITION", {"status": "NOT_ATTEMPTED_MODEL_UNAVAILABLE"})
        emit("OBSERVED_OUTCOME", {"status": "MODEL_UNAVAILABLE", "resource_read": False})
        return {"run_id": run_id, "status": "MODEL_UNAVAILABLE"}
    emit("MODEL_PROPOSAL", {"provider": response.get("provider"), "model": response.get("model"),
                            "provider_status": response["status"], "raw_output": response["output_text"],
                            "raw_response": response["raw_response"]})
    if response["status"] != "COMPLETED":
        emit("PROPOSAL_REJECTED", {"code": response["status"]})
        emit("EXECUTION_DISPOSITION", {"status": "NOT_ATTEMPTED_NO_PROPOSAL"})
        emit("OBSERVED_OUTCOME", {"status": "NO_VALID_PROPOSAL", "resource_read": False})
        return {"run_id": run_id, "status": response["status"]}
    try:
        proposal = validate_proposal(response["output_text"], presented)
    except InvalidProposal as error:
        emit("PROPOSAL_REJECTED", {"code": error.code, "message": str(error)})
        emit("EXECUTION_DISPOSITION", {"status": "NOT_ATTEMPTED_INVALID_PROPOSAL"})
        emit("OBSERVED_OUTCOME", {"status": "INVALID_PROPOSAL", "resource_read": False})
        return {"run_id": run_id, "status": "INVALID_PROPOSAL", "validation_code": error.code}
    emit("PROPOSAL_ACCEPTED", {"proposal": proposal, "authorization": "NOT_YET_EVALUATED"})
    try:
        result = complaint_runtime.governed_action(
            proposal["resource_id"], action=proposal["action"], actor_id=actor_id,
            run_id=run_id, step_id="proposal-1", emit=emit,
            governance_log_path=output / "governance.jsonl", execution_log_path=output / "execution.jsonl",
            opa_decision_log_path=output / "opa.jsonl")
    except Exception as error:
        emit("RUNTIME_ERROR", {"error_type": type(error).__name__, "message": str(error), "proposal": proposal})
        if "OBSERVED_OUTCOME" not in emitted_types:
            attempted = "EXECUTION_ATTEMPT" in emitted_types
            if not attempted:
                emit("EXECUTION_DISPOSITION", {"status": "NOT_ATTEMPTED_RUNTIME_ERROR"})
            emit("OBSERVED_OUTCOME", {"status": "RUNTIME_ERROR", "resource_read": None if attempted else False})
        return {"run_id": run_id, "status": "RUNTIME_ERROR", "proposal": proposal}
    status = ("AUTHORITY_NOT_EVALUABLE" if result["authority_status"] != "RESOLVED"
              else "EXECUTED" if result["resource_returned"] else "DENIED")
    return {"run_id": run_id, "status": status,
            "proposal": proposal, **result}
