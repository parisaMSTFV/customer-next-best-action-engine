from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

ACTIONS = ("reminder", "voucher_5", "voucher_10", "service_call")
CANDIDATE_COLUMNS = [
    "customer_id",
    "action",
    "channel",
    "recommended_category",
    "category_probability",
    "predicted_uplift",
    "effective_predicted_uplift",
    "predicted_treated_probability",
    "expected_order_value",
    "expected_order_margin",
    "expected_cost",
    "predicted_net_value",
    "churn_probability",
    "purchase_readiness_30d",
    "predicted_clv_180d",
    "investment_ceiling",
    "segment_name",
    "service_tier",
]


def _resolved_channel(row: pd.Series, action: str) -> str:
    if action == "service_call":
        return "call"
    return str(row["preferred_owned_channel"])


def _has_channel_consent(row: pd.Series, channel: str) -> bool:
    consent_column = {
        "email": "email_consent",
        "push": "push_consent",
        "call": "call_consent",
    }.get(channel)
    return bool(consent_column and row[consent_column])


def build_candidates(
    frame: pd.DataFrame,
    policy: dict[str, Any],
    offer_config: dict[str, Any],
) -> pd.DataFrame:
    """Create economically comparable customer-action candidates."""
    rows: list[dict[str, float | str | bool]] = []
    service_cfg = policy["service_call"]
    suppress_uncertain_service = bool(
        policy["uncertainty"].get("suppress_high_uncertainty_service_call", True)
    )
    channel_cost = offer_config["channel_cost"]

    for _, customer in frame.loc[frame["timing_status"] == "act_now"].iterrows():
        for action in ACTIONS:
            channel = _resolved_channel(customer, action)
            if channel == "none":
                continue
            if not _has_channel_consent(customer, channel):
                continue
            if action == "service_call":
                if str(customer["service_tier"]) not in set(service_cfg["eligible_tiers"]):
                    continue
                if customer["churn_probability"] < float(service_cfg["minimum_churn_probability"]):
                    continue
                if suppress_uncertain_service and bool(customer["high_uncertainty"]):
                    continue

            offer = offer_config["offers"][action]
            uplift = float(customer[f"uplift_{action}"])
            baseline_probability = float(customer["purchase_readiness_30d"])
            treated_probability = float(np.clip(baseline_probability + uplift, 0, 1))
            effective_uplift = treated_probability - baseline_probability
            discount_rate = float(offer["discount_rate"])
            contact_cost = float(offer["fixed_action_cost"]) + float(channel_cost[channel])
            expected_subsidy = (
                treated_probability * discount_rate * float(customer["expected_order_value"])
            )
            expected_cost = contact_cost + expected_subsidy
            gross_incremental_margin = effective_uplift * float(customer["expected_order_margin"])
            predicted_net_value = gross_incremental_margin - expected_cost

            if expected_cost > float(customer["investment_ceiling"]) + 1e-12:
                continue

            row: dict[str, float | str | bool] = {
                "customer_id": str(customer["customer_id"]),
                "action": action,
                "channel": channel,
                "recommended_category": str(customer["recommended_category"]),
                "category_probability": float(customer["category_probability"]),
                "predicted_uplift": uplift,
                "effective_predicted_uplift": effective_uplift,
                "predicted_treated_probability": treated_probability,
                "expected_order_value": float(customer["expected_order_value"]),
                "expected_order_margin": float(customer["expected_order_margin"]),
                "expected_cost": expected_cost,
                "predicted_net_value": predicted_net_value,
                "churn_probability": float(customer["churn_probability"]),
                "purchase_readiness_30d": baseline_probability,
                "predicted_clv_180d": float(customer["predicted_clv_180d"]),
                "investment_ceiling": float(customer["investment_ceiling"]),
                "segment_name": str(customer["segment_name"]),
                "service_tier": str(customer["service_tier"]),
            }

            rows.append(row)

    if not rows:
        return pd.DataFrame(columns=CANDIDATE_COLUMNS)
    return pd.DataFrame(rows)
