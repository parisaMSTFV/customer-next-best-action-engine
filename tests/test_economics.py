import pandas as pd
import pytest

from next_best_action.candidates import build_candidates


def test_voucher_cost_includes_subsidy_on_all_treated_purchases(project_root):
    from next_best_action.config import load_configs

    policy, offers = load_configs(project_root)
    frame = pd.DataFrame(
        {
            "customer_id": ["SYN-1"],
            "timing_status": ["act_now"],
            "preferred_owned_channel": ["email"],
            "email_consent": [True],
            "push_consent": [False],
            "call_consent": [False],
            "service_tier": ["protect"],
            "high_uncertainty": [False],
            "churn_probability": [0.8],
            "purchase_readiness_30d": [0.5],
            "expected_order_value": [100.0],
            "expected_order_margin": [25.0],
            "investment_ceiling": [100.0],
            "recommended_category": ["Beauty"],
            "category_probability": [0.8],
            "predicted_clv_180d": [300.0],
            "segment_name": ["High value at risk"],
            "uplift_reminder": [0.05],
            "uplift_voucher_5": [0.10],
            "uplift_voucher_10": [0.12],
            "uplift_service_call": [0.10],
        }
    )
    candidates = build_candidates(frame, policy, offers)
    voucher = candidates.loc[candidates["action"] == "voucher_5"].iloc[0]
    expected_subsidy = (0.5 + 0.10) * 0.05 * 100.0
    expected_fixed = 0.08 + 0.06
    assert voucher["expected_cost"] == pytest.approx(expected_subsidy + expected_fixed)
    assert voucher["predicted_net_value"] == pytest.approx(
        0.10 * 25.0 - expected_subsidy - expected_fixed
    )
