from __future__ import annotations

from dataclasses import fields

import pandas as pd

from next_best_action.simulation import SyntheticBundle

REQUIRED_COLUMNS = {
    "customer_state": {
        "customer_id",
        "expected_order_value",
        "margin_rate",
        "expected_order_margin",
        "email_consent",
        "push_consent",
        "call_consent",
        "preferred_owned_channel",
        "days_since_last_contact",
        "contact_count_30d",
    },
    "segmentation_scores": {"customer_id", "segment_name"},
    "clv_scores": {
        "customer_id",
        "predicted_clv_180d",
        "active_probability_180d",
        "clv_lower_80",
        "clv_upper_80",
        "service_tier",
        "investment_ceiling",
        "high_uncertainty",
    },
    "churn_scores": {
        "customer_id",
        "score_date",
        "personalized_deadline",
        "personalized_window_days",
        "churn_probability",
        "value_at_risk",
    },
    "purchase_scores": {
        "customer_id",
        "recommended_category",
        "category_probability",
        "purchase_readiness_30d",
        "expected_category_margin",
    },
    "uplift_scores": {
        "customer_id",
        "uplift_reminder",
        "uplift_voucher_5",
        "uplift_voucher_10",
        "uplift_service_call",
    },
}


def validate_bundle(bundle: SyntheticBundle) -> None:
    """Validate upstream contracts and customer-key integrity."""
    expected_names = {field.name for field in fields(bundle) if field.name != "evaluator_truth"}
    if expected_names != set(REQUIRED_COLUMNS):
        raise ValueError("Contract registry is out of sync with SyntheticBundle")

    base_ids: set[str] | None = None
    for name, required in REQUIRED_COLUMNS.items():
        frame = getattr(bundle, name)
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{name} is missing required columns: {sorted(missing)}")
        if frame["customer_id"].duplicated().any():
            raise ValueError(f"{name} contains duplicate customer_id values")
        ids = set(frame["customer_id"].astype(str))
        if base_ids is None:
            base_ids = ids
        elif ids != base_ids:
            raise ValueError(f"{name} does not contain the same customer universe")

    if bundle.evaluator_truth["customer_id"].duplicated().any():
        raise ValueError("evaluator_truth contains duplicate customer_id values")
    if set(bundle.evaluator_truth["customer_id"].astype(str)) != base_ids:
        raise ValueError("evaluator_truth does not match the deployable customer universe")


def build_decision_frame(bundle: SyntheticBundle) -> pd.DataFrame:
    """Join deployable upstream outputs without evaluator truth."""
    validate_bundle(bundle)
    frame = bundle.customer_state.copy()
    for name in [
        "segmentation_scores",
        "clv_scores",
        "churn_scores",
        "purchase_scores",
        "uplift_scores",
    ]:
        frame = frame.merge(
            getattr(bundle, name), on="customer_id", how="inner", validate="one_to_one"
        )
    truth_markers = [column for column in frame.columns if column.startswith("true_")]
    if truth_markers:
        raise ValueError(f"Evaluator truth leaked into decision frame: {truth_markers}")
    return frame
