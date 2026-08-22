from src.governance_eval import load_scenarios, evaluate_scenario


def test_governance_eval_scenarios_pass():
    scenarios = load_scenarios()

    for scenario in scenarios:
        result = evaluate_scenario(scenario)

        assert result["decision_correct"] is True
        assert result["policy_correct"] is True
        assert result["reason_correct"] is True
        assert result["evidence_complete"] is True
        assert result["overall_pass"] is True