import copy

import pytest

from src.evidence_correlation import correlate, score_links


def record(ref, timestamp="2026-09-05T12:00:00Z", **changes):
    result = {"evidence_ref": ref, "actor": "alice", "action": "read",
              "resource_id": "complaint-1", "resource_type": "complaint",
              "observed_at": timestamp}
    result.update(changes)
    return result


def states(results):
    return {(r["source"], r["evidence_ref"]): r["state"] for r in results}


def test_unique_legitimate_match():
    results = correlate([record("o")], [record("j")], window_seconds=2)
    assert set(states(results).values()) == {"MATCHED"}
    assert results[0]["candidate_refs"] == ["j"]


def test_zero_candidates():
    results = correlate([record("o")], [record("j", actor="bob")], window_seconds=2)
    assert set(states(results).values()) == {"UNMATCHED"}


@pytest.mark.parametrize("field", ["action", "resource_id", "resource_type"])
def test_different_required_field_has_no_candidate(field):
    results = correlate([record("o")], [record("j", **{field: "different"})], window_seconds=2)
    assert set(states(results).values()) == {"UNMATCHED"}


@pytest.mark.parametrize("left,right", [(1, 2), (2, 1), (2, 2)])
def test_repeated_one_to_many_and_many_to_one(left, right):
    results = correlate([record(f"o{i}") for i in range(left)],
                        [record(f"j{i}") for i in range(right)], window_seconds=2)
    assert set(states(results).values()) == {"AMBIGUOUS"}


def test_shuffled_order_and_repeated_ingestion_are_idempotent():
    opa = [record("o1"), record("o2", actor="bob")]
    journal = [record("j1"), record("j2", actor="bob")]
    expected = correlate(opa, journal, window_seconds=2)
    assert correlate(opa[::-1], journal[::-1], window_seconds=2) == expected
    assert correlate(opa + copy.deepcopy(opa), journal * 2, window_seconds=2) == expected


@pytest.mark.parametrize("timestamp,state", [
    ("2026-09-05T12:00:02Z", "MATCHED"),
    ("2026-09-05T11:59:58Z", "MATCHED"),
    ("2026-09-05T12:00:02.000000001Z", "UNMATCHED"),
    ("2026-09-05T08:00:00-04:00", "MATCHED"),
])
def test_timestamp_boundary(timestamp, state):
    assert set(states(correlate([record("o")], [record("j", timestamp)],
                                window_seconds=2)).values()) == {state}


@pytest.mark.parametrize("changes", [
    {"observed_at": "yesterday"}, {"observed_at": "2026-09-05T12:00:00"},
    {"actor": ""}, {"resource_id": None}, {"action": []}, {"resource_type": 4},
])
def test_malformed_timestamp_or_fields(changes):
    results = correlate([record("o", **changes)], [record("j")], window_seconds=2)
    assert states(results)[("opa", "o")] == "EVIDENCE_DEFECT"
    assert states(results)[("journal", "j")] == "UNMATCHED"


def test_identifiers_never_influence_candidates():
    opa, journal = [record("o")], [record("j")]
    expected = correlate(opa, journal, window_seconds=2)
    for name in ("action_attempt_id", "decision_id", "trace_id", "sequence"):
        opa[0][name], journal[0][name] = "random-a", "conflicting-b"
    assert correlate(opa, journal, window_seconds=2) == expected


def test_plausible_impostor_is_scored_as_false_accepted_link():
    results = correlate([record("o")], [record("impostor")], window_seconds=2)
    assert set(states(results).values()) == {"MATCHED"}
    score = score_links(results, {("o", "removed-true-counterpart")})
    assert score["false_accepted_links"] == 1
    assert score["false_link_rate"] == 1
    assert score["true_pair_recovery"] == 0


@pytest.mark.parametrize("window", [-1, float("inf"), float("nan")])
def test_invalid_window(window):
    with pytest.raises(ValueError):
        correlate([], [], window_seconds=window)


def test_nearest_timestamp_does_not_resolve_ambiguity():
    results = correlate([record("o")], [record("near"), record("far", "2026-09-05T12:00:01Z")],
                        window_seconds=2)
    assert set(states(results).values()) == {"AMBIGUOUS"}


def test_repetitions_outside_overlapping_windows_match_separately():
    opa = [record("o1"), record("o2", "2026-09-05T12:00:10Z")]
    journal = [record("j1"), record("j2", "2026-09-05T12:00:10Z")]
    assert set(states(correlate(opa, journal, window_seconds=2)).values()) == {"MATCHED"}


def test_ground_truth_score_with_no_accepted_links():
    score = score_links(correlate([record("o")], [], window_seconds=2), {("o", "j")})
    assert score["false_link_rate"] is None
    assert score["true_pair_recovery"] == 0
