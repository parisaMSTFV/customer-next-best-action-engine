from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

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

PROBABILITY_COLUMNS = {
    "customer_state": ["margin_rate"],
    "clv_scores": ["active_probability_180d"],
    "churn_scores": ["churn_probability"],
    "purchase_scores": ["category_probability", "purchase_readiness_30d"],
}
BOOLEAN_COLUMNS = {
    "customer_state": ["email_consent", "push_consent", "call_consent"],
    "clv_scores": ["high_uncertainty"],
}
NONNEGATIVE_COLUMNS = {
    "customer_state": [
        "expected_order_value",
        "margin_rate",
        "expected_order_margin",
        "days_since_last_contact",
        "contact_count_30d",
    ],
    "clv_scores": [
        "predicted_clv_180d",
        "clv_lower_80",
        "clv_upper_80",
        "investment_ceiling",
    ],
    "churn_scores": ["personalized_window_days", "value_at_risk"],
    "purchase_scores": ["expected_category_margin"],
}
UPLIFT_COLUMNS = [
    "uplift_reminder",
    "uplift_voucher_5",
    "uplift_voucher_10",
    "uplift_service_call",
]


def validate_bundle(bundle: Any) -> None:
    """Validate upstream contracts and customer-key integrity."""
    missing_artifacts = [name for name in REQUIRED_COLUMNS if not hasattr(bundle, name)]
    if missing_artifacts:
        raise ValueError(f"Bundle is missing artifacts: {missing_artifacts}")

    base_ids: set[str] | None = None
    for name, required in REQUIRED_COLUMNS.items():
        frame = getattr(bundle, name)
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{name} is missing required columns: {sorted(missing)}")
        if frame["customer_id"].duplicated().any():
            raise ValueError(f"{name} contains duplicate customer_id values")
        if frame["customer_id"].isna().any():
            raise ValueError(f"{name} contains null customer_id values")
        for column in PROBABILITY_COLUMNS.get(name, []):
            values = pd.to_numeric(frame[column], errors="coerce")
            if values.isna().any() or not np.isfinite(values).all():
                raise ValueError(f"{name}.{column} must contain finite numeric values")
            if not values.between(0, 1).all():
                raise ValueError(f"{name}.{column} must be between 0 and 1")
        for column in NONNEGATIVE_COLUMNS.get(name, []):
            values = pd.to_numeric(frame[column], errors="coerce")
            if values.isna().any() or not np.isfinite(values).all():
                raise ValueError(f"{name}.{column} must contain finite numeric values")
            if values.lt(0).any():
                raise ValueError(f"{name}.{column} cannot be negative")
        for column in BOOLEAN_COLUMNS.get(name, []):
            if not pd.api.types.is_bool_dtype(frame[column]):
                raise ValueError(f"{name}.{column} must contain boolean values")
        if name == "uplift_scores":
            for column in UPLIFT_COLUMNS:
                values = pd.to_numeric(frame[column], errors="coerce")
                if values.isna().any() or not np.isfinite(values).all():
                    raise ValueError(f"{name}.{column} must contain finite numeric values")
                if not values.between(-1, 1).all():
                    raise ValueError(f"{name}.{column} must be between -1 and 1")
        if name == "customer_state":
            invalid_channels = sorted(
                set(frame["preferred_owned_channel"].astype(str)) - {"push", "email", "none"}
            )
            if invalid_channels:
                raise ValueError(f"customer_state contains invalid channels: {invalid_channels}")
        if name == "clv_scores":
            if (frame["clv_lower_80"] > frame["predicted_clv_180d"]).any() or (
                frame["predicted_clv_180d"] > frame["clv_upper_80"]
            ).any():
                raise ValueError("clv_scores intervals must contain predicted_clv_180d")
        if name == "churn_scores" and frame["personalized_window_days"].le(0).any():
            raise ValueError("churn_scores.personalized_window_days must be positive")
        ids = set(frame["customer_id"].astype(str))
        if base_ids is None:
            base_ids = ids
        elif ids != base_ids:
            raise ValueError(f"{name} does not contain the same customer universe")

    evaluator_truth = getattr(bundle, "evaluator_truth", None)
    if evaluator_truth is None:
        return
    if evaluator_truth["customer_id"].duplicated().any():
        raise ValueError("evaluator_truth contains duplicate customer_id values")
    if set(evaluator_truth["customer_id"].astype(str)) != base_ids:
        raise ValueError("evaluator_truth does not match the deployable customer universe")


def build_decision_frame(bundle: Any) -> pd.DataFrame:
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
