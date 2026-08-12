import pandas as pd

from next_best_action.timing import add_timing_status


def test_contact_guardrail_suppresses_recent_contact(project_root):
    from next_best_action.config import load_configs

    policy, _ = load_configs(project_root)
    frame = pd.DataFrame(
        {
            "customer_id": ["SYN-1"],
            "score_date": ["2026-08-01"],
            "personalized_deadline": ["2026-08-02"],
            "personalized_window_days": [20],
            "purchase_readiness_30d": [0.90],
            "churn_probability": [0.90],
            "days_since_last_contact": [2],
            "contact_count_30d": [1],
            "preferred_owned_channel": ["email"],
        }
    )
    result = add_timing_status(frame, policy)
    assert result.loc[0, "timing_status"] == "suppressed"
