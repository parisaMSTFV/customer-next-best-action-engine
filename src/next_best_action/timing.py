from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def add_timing_status(frame: pd.DataFrame, policy: dict[str, Any]) -> pd.DataFrame:
    """Apply contact-frequency and personalized timing guardrails."""
    cfg = policy["timing"]
    result = frame.copy()
    score_date = pd.to_datetime(result["score_date"])
    deadline = pd.to_datetime(result["personalized_deadline"])
    result["days_to_deadline"] = (deadline - score_date).dt.days
    result["window_progress"] = 1 - (
        result["days_to_deadline"] / result["personalized_window_days"].clip(lower=1)
    )
    suppressed = (
        (result["days_since_last_contact"] < int(cfg["minimum_days_between_contacts"]))
        | (result["contact_count_30d"] >= int(cfg["max_contacts_30d"]))
        | ((result["preferred_owned_channel"] == "none") & ~result["call_consent"])
    )
    act_now = (
        (result["window_progress"] >= float(cfg["act_now_window_progress"]))
        | (result["purchase_readiness_30d"] >= float(cfg["act_now_purchase_probability"]))
        | (result["churn_probability"] >= float(cfg["act_now_churn_probability"]))
    ) & ~suppressed
    review = (
        (
            (result["window_progress"] >= float(cfg["review_window_progress"]))
            | (result["purchase_readiness_30d"] >= float(cfg["review_purchase_probability"]))
            | (result["churn_probability"] >= float(cfg["review_churn_probability"]))
        )
        & ~suppressed
        & ~act_now
    )

    result["timing_status"] = np.select(
        [suppressed, act_now, review],
        ["suppressed", "act_now", "review_soon"],
        default="monitor",
    )
    review_days = np.clip(result["days_to_deadline"] - 3, 1, 14)
    result["next_review_days"] = np.where(result["timing_status"] == "review_soon", review_days, 0)
    return result
