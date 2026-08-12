from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

import pandas as pd

from next_best_action.candidates import build_candidates
from next_best_action.evaluation import constraint_summary
from next_best_action.policy import optimize_policy


@dataclass(frozen=True)
class SensitivityScenario:
    """One controlled change to portfolio constraints or action economics."""

    scenario_id: str
    dimension: str
    budget_multiplier: float = 1.0
    capacity_multiplier: float = 1.0
    margin_multiplier: float = 1.0
    voucher_subsidy_multiplier: float = 1.0


def default_scenarios() -> list[SensitivityScenario]:
    """Return the committed one-at-a-time and two-way economics stress grid."""
    scenarios = [
        SensitivityScenario(f"budget_{value:.1f}", "budget", budget_multiplier=value)
        for value in [0.6, 0.8, 1.0, 1.2, 1.4]
    ]
    scenarios.extend(
        SensitivityScenario(f"capacity_{value:.1f}", "capacity", capacity_multiplier=value)
        for value in [0.6, 0.8, 1.0, 1.2, 1.4]
    )
    scenarios.extend(
        SensitivityScenario(
            f"economics_margin_{margin:.1f}_subsidy_{subsidy:.2f}",
            "economics",
            margin_multiplier=margin,
            voucher_subsidy_multiplier=subsidy,
        )
        for margin in [0.8, 1.0, 1.2]
        for subsidy in [0.75, 1.0, 1.25]
    )
    return scenarios


def _scenario_inputs(
    frame: pd.DataFrame,
    policy: dict[str, Any],
    offers: dict[str, Any],
    scenario: SensitivityScenario,
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    scenario_frame = frame.copy()
    scenario_frame["expected_order_margin"] *= scenario.margin_multiplier

    scenario_policy = deepcopy(policy)
    base_portfolio = policy["portfolio"]
    scenario_policy["portfolio"]["total_budget"] = round(
        float(base_portfolio["total_budget"]) * scenario.budget_multiplier,
        6,
    )
    scenario_policy["portfolio"]["channel_capacity"] = {
        channel: max(0, round(int(limit) * scenario.capacity_multiplier))
        for channel, limit in base_portfolio["channel_capacity"].items()
    }

    scenario_offers = deepcopy(offers)
    for action in ["voucher_5", "voucher_10"]:
        base_rate = float(offers["offers"][action]["discount_rate"])
        scenario_offers["offers"][action]["discount_rate"] = min(
            1.0,
            base_rate * scenario.voucher_subsidy_multiplier,
        )
    return scenario_frame, scenario_policy, scenario_offers


def _action_map(assignments: pd.DataFrame) -> dict[str, str]:
    return assignments.set_index("customer_id")["action"].astype(str).to_dict()


def _assignment_change_rate(
    base_assignments: pd.DataFrame,
    scenario_assignments: pd.DataFrame,
    customer_ids: pd.Series,
) -> float:
    base = _action_map(base_assignments)
    scenario = _action_map(scenario_assignments)
    changed = sum(
        base.get(str(customer_id), "no_action") != scenario.get(str(customer_id), "no_action")
        for customer_id in customer_ids
    )
    return changed / len(customer_ids) if len(customer_ids) else 0.0


def run_sensitivity(
    frame: pd.DataFrame,
    evaluator_truth: pd.DataFrame,
    policy: dict[str, Any],
    offers: dict[str, Any],
    scenarios: list[SensitivityScenario] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Evaluate policy stability under explicit constraints and economics scenarios."""
    selected_scenarios = scenarios if scenarios is not None else default_scenarios()
    if not selected_scenarios:
        raise ValueError("At least one sensitivity scenario is required")

    base_scenario = SensitivityScenario("base", "base")
    base_frame, base_policy, base_offers = _scenario_inputs(
        frame,
        policy,
        offers,
        base_scenario,
    )
    base_candidates = build_candidates(
        base_frame,
        base_policy,
        base_offers,
        evaluator_truth=evaluator_truth,
    )
    base_assignments = optimize_policy(base_candidates, base_policy)

    result_cache: dict[tuple[float, float, float, float], tuple[pd.DataFrame, ...]] = {}
    summary_rows: list[dict[str, Any]] = []
    allocation_rows: list[dict[str, Any]] = []

    for scenario in selected_scenarios:
        cache_key = (
            scenario.budget_multiplier,
            scenario.capacity_multiplier,
            scenario.margin_multiplier,
            scenario.voucher_subsidy_multiplier,
        )
        if cache_key not in result_cache:
            scenario_frame, scenario_policy, scenario_offers = _scenario_inputs(
                frame,
                policy,
                offers,
                scenario,
            )
            candidates = build_candidates(
                scenario_frame,
                scenario_policy,
                scenario_offers,
                evaluator_truth=evaluator_truth,
            )
            engine = optimize_policy(candidates, scenario_policy)
            reminder = optimize_policy(
                candidates.loc[candidates["action"] == "reminder"], scenario_policy
            )
            oracle = optimize_policy(candidates, scenario_policy, value_column="true_net_value")
            constraints = constraint_summary(engine, scenario_policy)
            result_cache[cache_key] = (
                scenario_policy,
                engine,
                reminder,
                oracle,
                constraints,
            )

        scenario_policy, engine, reminder, oracle, constraints = result_cache[cache_key]
        engine_true_value = float(engine["true_net_value"].sum())
        reminder_true_value = float(reminder["true_net_value"].sum())
        oracle_true_value = float(oracle["true_net_value"].sum())
        summary_rows.append(
            {
                "scenario_id": scenario.scenario_id,
                "dimension": scenario.dimension,
                "budget_multiplier": scenario.budget_multiplier,
                "capacity_multiplier": scenario.capacity_multiplier,
                "margin_multiplier": scenario.margin_multiplier,
                "voucher_subsidy_multiplier": scenario.voucher_subsidy_multiplier,
                "total_budget": float(scenario_policy["portfolio"]["total_budget"]),
                "push_capacity": int(scenario_policy["portfolio"]["channel_capacity"]["push"]),
                "email_capacity": int(scenario_policy["portfolio"]["channel_capacity"]["email"]),
                "call_capacity": int(scenario_policy["portfolio"]["channel_capacity"]["call"]),
                "customers_contacted": int(len(engine)),
                "budget_used": float(engine["expected_cost"].sum()),
                "predicted_net_value": float(engine["predicted_net_value"].sum()),
                "true_incremental_net_value": engine_true_value,
                "reminder_baseline_true_net_value": reminder_true_value,
                "improvement_vs_reminder": (
                    engine_true_value / reminder_true_value - 1 if reminder_true_value > 0 else 0.0
                ),
                "oracle_true_net_value": oracle_true_value,
                "regret_vs_oracle": (
                    (oracle_true_value - engine_true_value) / oracle_true_value
                    if oracle_true_value > 0
                    else 0.0
                ),
                "assignment_change_rate_vs_base": _assignment_change_rate(
                    base_assignments,
                    engine,
                    frame["customer_id"],
                ),
                "all_constraints_pass": bool(constraints["within_limit"].all()),
            }
        )
        counts = engine["action"].value_counts()
        for action in ["reminder", "voucher_5", "voucher_10", "service_call"]:
            allocation_rows.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "dimension": scenario.dimension,
                    "action": action,
                    "customers": int(counts.get(action, 0)),
                }
            )

    return pd.DataFrame(summary_rows), pd.DataFrame(allocation_rows)
