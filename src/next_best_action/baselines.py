from __future__ import annotations

from typing import Any

import pandas as pd

from next_best_action.policy import greedy_assign


def risk_only_reminder(candidates: pd.DataFrame, policy: dict[str, Any]) -> pd.DataFrame:
    """Rank churn risk and use a reminder, ignoring treatment heterogeneity."""
    rows = candidates.loc[candidates["action"] == "reminder"].copy()
    order = rows.sort_values(["churn_probability", "predicted_clv_180d"], ascending=False).index
    return greedy_assign(rows, policy, order)


def clv_first_voucher(candidates: pd.DataFrame, policy: dict[str, Any]) -> pd.DataFrame:
    """Target the highest CLV customers with the smaller voucher."""
    rows = candidates.loc[candidates["action"] == "voucher_5"].copy()
    order = rows.sort_values("predicted_clv_180d", ascending=False).index
    return greedy_assign(rows, policy, order)


def purchase_readiness_voucher(candidates: pd.DataFrame, policy: dict[str, Any]) -> pd.DataFrame:
    """Rank near-term purchase readiness and category confidence with a voucher."""
    rows = candidates.loc[candidates["action"] == "voucher_5"].copy()
    rows["baseline_score"] = rows["purchase_readiness_30d"] * rows["category_probability"]
    order = rows.sort_values("baseline_score", ascending=False).index
    return greedy_assign(rows, policy, order)


def segment_rule_policy(candidates: pd.DataFrame, policy: dict[str, Any]) -> pd.DataFrame:
    """Apply a transparent segment-action lookup before portfolio constraints."""
    action_map = {
        "Loyal high value": "reminder",
        "High value at risk": "service_call",
        "Growth potential": "reminder",
        "Engaged low conversion": "reminder",
        "Discount-led frequent": "voucher_5",
        "Dormant low value": "reminder",
    }
    rows = candidates.copy()
    rows["rule_action"] = rows["segment_name"].map(action_map)
    rows = rows.loc[rows["action"] == rows["rule_action"]].copy()
    rows["baseline_score"] = rows["churn_probability"] * rows["predicted_clv_180d"]
    order = rows.sort_values("baseline_score", ascending=False).index
    return greedy_assign(rows, policy, order)
