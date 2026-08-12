from __future__ import annotations

from typing import Any

import pandas as pd


def policy_metrics(
    name: str,
    assignments: pd.DataFrame,
    total_customers: int,
    oracle_true_value: float,
) -> dict[str, float | int | str]:
    """Summarize a policy using hidden synthetic truth only for evaluation."""
    contacts = len(assignments)
    budget_used = float(assignments["expected_cost"].sum()) if contacts else 0.0
    predicted = float(assignments["predicted_net_value"].sum()) if contacts else 0.0
    true_value = float(assignments["true_net_value"].sum()) if contacts else 0.0
    regret = (oracle_true_value - true_value) / oracle_true_value if oracle_true_value > 0 else 0.0
    return {
        "policy": name,
        "customers_contacted": contacts,
        "contact_rate": contacts / total_customers,
        "no_action_rate": 1 - contacts / total_customers,
        "budget_used": budget_used,
        "predicted_net_value": predicted,
        "true_incremental_net_value": true_value,
        "true_value_per_contact": true_value / contacts if contacts else 0.0,
        "regret_vs_oracle": regret,
    }


def constraint_summary(assignments: pd.DataFrame, policy: dict[str, Any]) -> pd.DataFrame:
    """Report budget and channel capacity utilization."""
    budget = float(policy["portfolio"]["total_budget"])
    rows: list[dict[str, float | int | str | bool]] = [
        {
            "constraint": "total_budget",
            "used": float(assignments["expected_cost"].sum()),
            "limit": budget,
            "within_limit": float(assignments["expected_cost"].sum()) <= budget + 1e-9,
        }
    ]
    for channel, limit in policy["portfolio"]["channel_capacity"].items():
        used = int((assignments["channel"] == channel).sum())
        rows.append(
            {
                "constraint": f"channel_{channel}",
                "used": used,
                "limit": int(limit),
                "within_limit": used <= int(limit),
            }
        )
    duplicated = int(assignments["customer_id"].duplicated().sum())
    rows.append(
        {
            "constraint": "one_action_per_customer",
            "used": duplicated,
            "limit": 0,
            "within_limit": duplicated == 0,
        }
    )
    return pd.DataFrame(rows)
