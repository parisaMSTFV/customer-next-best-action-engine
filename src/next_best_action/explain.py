from __future__ import annotations

import pandas as pd


def add_reason_codes(
    decision_frame: pd.DataFrame,
    assignments: pd.DataFrame,
    candidates: pd.DataFrame,
) -> pd.DataFrame:
    """Return one explainable decision row per customer."""
    selected = assignments.set_index("customer_id") if not assignments.empty else pd.DataFrame()
    positive_candidates = (
        candidates.loc[candidates["predicted_net_value"] > 0]
        .groupby("customer_id")
        .size()
        .to_dict()
        if not candidates.empty
        else {}
    )
    rows: list[dict[str, object]] = []

    for _, customer in decision_frame.iterrows():
        customer_id = str(customer["customer_id"])
        timing = str(customer["timing_status"])
        if not selected.empty and customer_id in selected.index:
            action = selected.loc[customer_id]
            codes = ["positive_incremental_value", "within_customer_investment_ceiling"]
            if customer["churn_probability"] >= 0.70:
                codes.append("high_churn_risk")
            if customer["purchase_readiness_30d"] >= 0.65:
                codes.append("purchase_ready")
            if customer["category_probability"] >= 0.70:
                codes.append("high_category_confidence")
            if customer["service_tier"] in {"protect", "grow"}:
                codes.append("high_value_tier")
            rows.append(
                {
                    "customer_id": customer_id,
                    "timing_status": timing,
                    "next_review_days": int(customer["next_review_days"]),
                    "recommended_action": str(action["action"]),
                    "channel": str(action["channel"]),
                    "recommended_category": str(action["recommended_category"]),
                    "predicted_incremental_net_value": float(action["predicted_net_value"]),
                    "expected_action_cost": float(action["expected_cost"]),
                    "reason_codes": ";".join(codes),
                }
            )
            continue

        if timing == "suppressed":
            code = "contact_frequency_or_consent_guardrail"
        elif timing == "review_soon":
            code = "wait_for_better_timing"
        elif timing == "monitor":
            code = "outside_action_window"
        elif positive_candidates.get(customer_id, 0) > 0:
            code = "positive_candidate_not_selected_under_portfolio_constraints"
        else:
            code = "no_positive_incremental_value"
        rows.append(
            {
                "customer_id": customer_id,
                "timing_status": timing,
                "next_review_days": int(customer["next_review_days"]),
                "recommended_action": "no_action",
                "channel": "none",
                "recommended_category": str(customer["recommended_category"]),
                "predicted_incremental_net_value": 0.0,
                "expected_action_cost": 0.0,
                "reason_codes": code,
            }
        )

    result = pd.DataFrame(rows)
    context = decision_frame[
        [
            "customer_id",
            "segment_name",
            "service_tier",
            "churn_probability",
            "purchase_readiness_30d",
            "category_probability",
            "predicted_clv_180d",
            "investment_ceiling",
        ]
    ]
    return result.merge(context, on="customer_id", how="left", validate="one_to_one")
