import json

import pytest

from src.model_proposal import InvalidProposal, validate_proposal, build_request, extract_response


@pytest.mark.parametrize("raw,code", [
    ("not json", "MALFORMED_OUTPUT"),
    ('{"action":"read"}', "MISSING_FIELDS"),
    ('{"action":"delete","resource_id":"complaint-456","reason":"x"}', "UNSUPPORTED_ACTION"),
    ('{"action":"read","resource_id":"invented","reason":"x"}', "UNKNOWN_RESOURCE"),
    ('{"action":"read","resource_id":"../secret","reason":"x"}', "UNKNOWN_RESOURCE"),
    ('{"action":"read","resource_id":"complaint-456","reason":null}', "INVALID_SCHEMA"),
    ('{"action":"read","action":"export","resource_id":"complaint-456","reason":"x"}', "MALFORMED_OUTPUT"),
])
def test_explicit_rejections(raw, code):
    with pytest.raises(InvalidProposal) as error:
        validate_proposal(raw, {"complaint-456", "complaint-789"})
    assert error.value.code == code


def test_known_unauthorized_resource_is_valid():
    proposal = {"action": "read", "resource_id": "complaint-789", "reason": "urgent"}
    assert validate_proposal(json.dumps(proposal), {"complaint-456", "complaint-789"}) == proposal


def test_request_contains_multiple_candidates_without_resource_enum():
    candidates = [{"resource_id": "complaint-456"}, {"resource_id": "complaint-789"}]
    request = build_request("Choose a complaint", candidates, "gpt-5.4-mini")
    assert json.loads(request["input"])["candidates"] == candidates
    assert "enum" not in request["text"]["format"]["schema"]["properties"]["resource_id"]
    with pytest.raises(ValueError):
        build_request("task", candidates[:1], "model")


def test_refusal_and_incomplete_response_are_not_proposals():
    assert extract_response({"status": "incomplete", "output": []})["status"] == "INCOMPLETE"
    assert extract_response({"status": "completed", "output": [{"type": "message", "content": [
        {"type": "refusal", "refusal": "No"}]}]})["status"] == "REFUSED"
