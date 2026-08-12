from next_best_action.sensitivity import (
    SensitivityScenario,
    default_scenarios,
    run_sensitivity,
)


def test_default_scenario_grid_is_explicit_and_unique():
    scenarios = default_scenarios()
    assert len(scenarios) == 19
    assert len({scenario.scenario_id for scenario in scenarios}) == len(scenarios)
    assert {scenario.dimension for scenario in scenarios} == {
        "budget",
        "capacity",
        "economics",
    }


def test_budget_and_capacity_sensitivity_respects_constraints(small_setup):
    policy, offers, bundle, frame = small_setup
    scenarios = [
        SensitivityScenario("budget_0.6", "budget", budget_multiplier=0.6),
        SensitivityScenario("budget_1.0", "budget", budget_multiplier=1.0),
        SensitivityScenario("budget_1.4", "budget", budget_multiplier=1.4),
        SensitivityScenario("capacity_0.6", "capacity", capacity_multiplier=0.6),
        SensitivityScenario("capacity_1.4", "capacity", capacity_multiplier=1.4),
    ]
    summary, allocation = run_sensitivity(
        frame,
        bundle.evaluator_truth,
        policy,
        offers,
        scenarios,
    )

    assert summary["all_constraints_pass"].all()
    assert len(allocation) == len(scenarios) * 4
    budget = summary.loc[summary["dimension"] == "budget"].sort_values("budget_multiplier")
    assert budget["predicted_net_value"].is_monotonic_increasing
    assert (
        budget.loc[budget["budget_multiplier"] == 1.0, "assignment_change_rate_vs_base"].iat[0]
        == 0.0
    )


def test_economics_scenario_reports_policy_and_baseline(small_setup):
    policy, offers, bundle, frame = small_setup
    scenario = SensitivityScenario(
        "economics_stress",
        "economics",
        margin_multiplier=0.8,
        voucher_subsidy_multiplier=1.25,
    )
    summary, _ = run_sensitivity(
        frame,
        bundle.evaluator_truth,
        policy,
        offers,
        [scenario],
    )
    row = summary.iloc[0]
    assert row["oracle_true_net_value"] >= row["true_incremental_net_value"] - 1e-9
    assert row["customers_contacted"] > 0
    assert "improvement_vs_reminder" in summary
