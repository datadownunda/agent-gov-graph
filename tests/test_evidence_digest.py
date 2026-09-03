from src.evidence_digest import (
    evidence_digest,
)


def test_evidence_digest_is_order_independent():
    first = {
        "decision": "ALLOW",
        "resource_id": "complaint-456",
    }

    second = {
        "resource_id": "complaint-456",
        "decision": "ALLOW",
    }

    assert (
        evidence_digest(first)
        == evidence_digest(second)
    )


def test_evidence_digest_changes_with_evidence():
    allow = {
        "decision": "ALLOW",
        "resource_id": "complaint-456",
    }

    deny = {
        "decision": "DENY",
        "resource_id": "complaint-456",
    }

    assert (
        evidence_digest(allow)
        != evidence_digest(deny)
    )