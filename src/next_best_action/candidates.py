from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

ACTIONS = ("reminder", "voucher_5", "voucher_10", "service_call")


def _resolved_channel(row: pd.Series, action: str) -> str:
    if action == "service_call":
        return "call"
    return str(row["preferred_owned_channel"])


def build_candidates(
    frame: pd.DataFrame,
    policy: dict[str, Any],
    offer_config: dict[str, Any],
    evaluator_truth: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Create economically comparable customer-action candidates."""
    truth = None
    if evaluator_truth is not None:
        truth = evaluator_truth.set_index("customer_id")

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
            if action == "service_call":
                if not bool(customer["call_consent"]):
                    continue
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
            discount_rate = float(offer["discount_rate"])
            contact_cost = float(offer["fixed_action_cost"]) + float(channel_cost[channel])
            expected_subsidy = (
                treated_probability * discount_rate * float(customer["expected_order_value"])
            )
            expected_cost = contact_cost + expected_subsidy
            gross_incremental_margin = uplift * float(customer["expected_order_margin"])
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
                "predicted_treated_probability": treated_probability,
                "expected_cost": expected_cost,
                "predicted_net_value": predicted_net_value,
                "churn_probability": float(customer["churn_probability"]),
                "purchase_readiness_30d": baseline_probability,
                "predicted_clv_180d": float(customer["predicted_clv_180d"]),
                "investment_ceiling": float(customer["investment_ceiling"]),
                "segment_name": str(customer["segment_name"]),
                "service_tier": str(customer["service_tier"]),
            }

            if truth is not None:
                truth_row = truth.loc[str(customer["customer_id"])]
                true_uplift = float(truth_row[f"true_uplift_{action}"])
                true_treated_probability = float(np.clip(baseline_probability + true_uplift, 0, 1))
                true_subsidy = (
                    true_treated_probability
                    * discount_rate
                    * float(customer["expected_order_value"])
                )
                true_net_value = (
                    true_uplift * float(customer["expected_order_margin"])
                    - contact_cost
                    - true_subsidy
                )
                row["true_net_value"] = true_net_value
                row["true_uplift"] = true_uplift
            rows.append(row)

    return pd.DataFrame(rows)
