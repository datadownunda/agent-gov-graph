import pytest

from experiments.foreign_opa.feature_benchmark import build_case, match_features, FEATURES, FEATURE_SETS, PROFILES
from experiments.foreign_opa.benchmark import build_case as baseline_case, evaluate, run_matcher


@pytest.mark.parametrize("profile", PROFILES)
def test_baseline_projection_and_findings_are_unchanged(profile):
    options = dict(repetitions=5, missing_fraction=0.5, impostor_fraction=0.5)
    original, truth = baseline_case("test", **options)
    enriched, enriched_truth = build_case("test", profile=profile, **options)
    projected = {side: [{k: v for k, v in r.items() if k not in FEATURES} for r in enriched[side]]
                 for side in ("opa", "journal")}
    assert projected == {side: original[side] for side in ("opa", "journal")}
    assert enriched_truth == truth
    assert match_features(enriched, ()) == run_matcher(original)


def test_shared_context_impostors_defeat_every_extra_feature():
    inputs, truth = build_case("collision", profile="same_context", groups=4,
                               missing_fraction=1, impostor_fraction=1)
    score = evaluate(match_features(inputs, FEATURES), truth)
    assert score["false_accepted_links"] == 4
    assert score["precision"] == 0


def test_missing_features_abstain_without_fallback():
    inputs, _ = build_case("missing", profile="varied", groups=1)
    del inputs["journal"][0]["client_app"]
    results = match_features(inputs, ("client_app",))
    assert {r["state"] for r in results} == {"UNMATCHED"}


def test_forbidden_features_are_rejected():
    for feature in ("action_attempt_id", "evidence_ref", "sequence", "truth", "filename"):
        with pytest.raises(ValueError):
            match_features({"opa": [], "journal": [], "window_seconds": 2}, (feature,))


def test_extra_field_can_remove_impostor_without_using_truth():
    inputs, truth = build_case("remove", profile="same_context", groups=1,
                               impostor_fraction=1)
    # Change a supplied ordinary observation; truth is used only for evaluation.
    inputs["journal"][0]["client_app"] = "other-client"
    assert {r["state"] for r in match_features(inputs, ())} == {"AMBIGUOUS"}
    assert sum(r["state"] == "MATCHED" for r in match_features(inputs, ("client_app",))) == 2


def test_shuffle_invariance():
    inputs, _ = build_case("shuffle", profile="varied", repetitions=5)
    expected = match_features(inputs, FEATURES)
    inputs["opa"].reverse()
    inputs["journal"].reverse()
    assert match_features(inputs, FEATURES) == expected


def test_all_subsets_are_measured():
    assert len(FEATURE_SETS) == 2 ** len(FEATURES)
    assert len({frozenset(fields) for fields in FEATURE_SETS.values()}) == 16


def test_disagreement_can_turn_ambiguity_into_a_silent_false_link():
    inputs, truth = build_case("disagreement", profile="same_context", groups=1,
                               impostor_fraction=1)
    original_ref = truth["true_pairs"][0][1]
    for request in inputs["journal"]:
        if request["evidence_ref"] == original_ref:
            request["client_app"] = "inconsistent-client"
    assert evaluate(match_features(inputs, ()), truth)["false_accepted_links"] == 0
    assert evaluate(match_features(inputs, ("client_app",)), truth)["false_accepted_links"] == 1
