from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

SEGMENTS = [
    "Loyal high value",
    "High value at risk",
    "Growth potential",
    "Engaged low conversion",
    "Discount-led frequent",
    "Dormant low value",
]
SEGMENT_PROBS = np.array([0.16, 0.12, 0.21, 0.19, 0.14, 0.18])
CATEGORIES = np.array(["Beauty", "Electronics", "Fashion", "Grocery", "Home", "Sports"])


@dataclass(frozen=True)
class SyntheticBundle:
    customer_state: pd.DataFrame
    segmentation_scores: pd.DataFrame
    clv_scores: pd.DataFrame
    churn_scores: pd.DataFrame
    purchase_scores: pd.DataFrame
    uplift_scores: pd.DataFrame
    evaluator_truth: pd.DataFrame


def _segment_numeric(segment: np.ndarray, mapping: dict[str, float]) -> np.ndarray:
    return np.array([mapping[str(value)] for value in segment], dtype=float)


def _rank_tiers(values: np.ndarray) -> np.ndarray:
    rank = pd.Series(values).rank(method="first", ascending=False, pct=True).to_numpy()
    return np.select(
        [rank <= 0.10, rank <= 0.30, rank <= 0.70],
        ["protect", "grow", "nurture"],
        default="low_touch",
    )


def generate_synthetic_bundle(
    n_customers: int = 3000,
    seed: int = 42,
    score_date: str = "2026-08-01",
) -> SyntheticBundle:
    """Generate one unified synthetic customer universe and upstream score contracts."""
    rng = np.random.default_rng(seed)
    customer_id = np.array([f"SYN-{idx:06d}" for idx in range(1, n_customers + 1)])
    segment = rng.choice(SEGMENTS, size=n_customers, p=SEGMENT_PROBS)

    aov_center = _segment_numeric(
        segment,
        {
            "Loyal high value": 165,
            "High value at risk": 175,
            "Growth potential": 95,
            "Engaged low conversion": 80,
            "Discount-led frequent": 78,
            "Dormant low value": 62,
        },
    )
    margin_center = _segment_numeric(
        segment,
        {
            "Loyal high value": 0.29,
            "High value at risk": 0.25,
            "Growth potential": 0.23,
            "Engaged low conversion": 0.20,
            "Discount-led frequent": 0.13,
            "Dormant low value": 0.16,
        },
    )
    purchase_center = _segment_numeric(
        segment,
        {
            "Loyal high value": 0.72,
            "High value at risk": 0.34,
            "Growth potential": 0.53,
            "Engaged low conversion": 0.35,
            "Discount-led frequent": 0.68,
            "Dormant low value": 0.17,
        },
    )
    churn_center = _segment_numeric(
        segment,
        {
            "Loyal high value": 0.18,
            "High value at risk": 0.78,
            "Growth potential": 0.34,
            "Engaged low conversion": 0.46,
            "Discount-led frequent": 0.30,
            "Dormant low value": 0.83,
        },
    )
    window_center = _segment_numeric(
        segment,
        {
            "Loyal high value": 0.42,
            "High value at risk": 0.88,
            "Growth potential": 0.58,
            "Engaged low conversion": 0.62,
            "Discount-led frequent": 0.47,
            "Dormant low value": 0.93,
        },
    )
    expected_orders_180d = _segment_numeric(
        segment,
        {
            "Loyal high value": 5.7,
            "High value at risk": 3.1,
            "Growth potential": 4.0,
            "Engaged low conversion": 2.3,
            "Discount-led frequent": 5.0,
            "Dormant low value": 1.1,
        },
    )
    discount_affinity = _segment_numeric(
        segment,
        {
            "Loyal high value": 0.18,
            "High value at risk": 0.35,
            "Growth potential": 0.40,
            "Engaged low conversion": 0.30,
            "Discount-led frequent": 0.88,
            "Dormant low value": 0.52,
        },
    )
    service_failure = np.clip(
        _segment_numeric(
            segment,
            {
                "Loyal high value": 0.10,
                "High value at risk": 0.42,
                "Growth potential": 0.16,
                "Engaged low conversion": 0.24,
                "Discount-led frequent": 0.18,
                "Dormant low value": 0.28,
            },
        )
        + rng.normal(0, 0.09, n_customers),
        0,
        1,
    )

    expected_order_value = np.clip(aov_center * rng.lognormal(0, 0.22, n_customers), 25, 500)
    margin_rate = np.clip(margin_center + rng.normal(0, 0.035, n_customers), 0.06, 0.42)
    expected_order_margin = expected_order_value * margin_rate

    latent_activity = rng.normal(0, 0.10, n_customers)
    purchase_probability = np.clip(purchase_center + latent_activity, 0.03, 0.96)
    churn_probability = np.clip(
        churn_center - 0.20 * latent_activity + rng.normal(0, 0.07, n_customers),
        0.02,
        0.98,
    )
    window_progress = np.clip(window_center + rng.normal(0, 0.12, n_customers), 0.10, 1.25)
    personalized_window_days = np.clip(rng.normal(48, 17, n_customers), 14, 120).round().astype(int)
    days_to_deadline = np.rint(personalized_window_days * (1 - window_progress)).astype(int)

    expected_orders = np.clip(expected_orders_180d * rng.lognormal(0, 0.16, n_customers), 0.2, 10)
    true_clv = expected_orders * expected_order_margin
    predicted_clv = np.clip(true_clv * rng.lognormal(0, 0.18, n_customers), 1, None)
    uncertainty_width = np.clip(
        _segment_numeric(
            segment,
            {
                "Loyal high value": 0.32,
                "High value at risk": 0.50,
                "Growth potential": 0.55,
                "Engaged low conversion": 0.72,
                "Discount-led frequent": 0.45,
                "Dormant low value": 0.95,
            },
        )
        + rng.normal(0, 0.08, n_customers),
        0.20,
        1.25,
    )
    clv_lower = np.clip(predicted_clv * (1 - uncertainty_width / 2), 0, None)
    clv_upper = predicted_clv * (1 + uncertainty_width / 2)
    service_tier = _rank_tiers(predicted_clv)
    tier_caps = pd.Series(service_tier).map(
        {"protect": 24.0, "grow": 14.0, "nurture": 7.0, "low_touch": 2.0}
    ).to_numpy()
    investment_ceiling = np.minimum(0.08 * clv_lower, tier_caps)
    high_uncertainty = ((clv_upper - clv_lower) / np.maximum(predicted_clv, 1)) > 0.70

    true_category = rng.choice(CATEGORIES, size=n_customers)
    accuracy = np.clip(
        0.58 + 0.25 * purchase_probability + rng.normal(0, 0.05, n_customers),
        0.55,
        0.90,
    )
    predicted_category = true_category.copy()
    wrong = rng.random(n_customers) > accuracy
    for idx in np.flatnonzero(wrong):
        alternatives = CATEGORIES[CATEGORIES != true_category[idx]]
        predicted_category[idx] = rng.choice(alternatives)
    category_probability = np.clip(
        np.where(wrong, rng.normal(0.47, 0.08, n_customers), rng.normal(0.76, 0.09, n_customers)),
        0.25,
        0.97,
    )

    email_consent = rng.random(n_customers) < 0.90
    push_consent = rng.random(n_customers) < 0.78
    call_consent = rng.random(n_customers) < 0.72
    email_engagement = np.clip(rng.beta(2.4, 2.2, n_customers), 0, 1)
    push_engagement = np.clip(rng.beta(2.0, 2.0, n_customers), 0, 1)
    preferred_owned_channel = np.where(push_engagement > email_engagement, "push", "email")
    preferred_owned_channel = np.where(
        (preferred_owned_channel == "push") & ~push_consent & email_consent,
        "email",
        preferred_owned_channel,
    )
    preferred_owned_channel = np.where(
        (preferred_owned_channel == "email") & ~email_consent & push_consent,
        "push",
        preferred_owned_channel,
    )
    no_owned = ~email_consent & ~push_consent
    preferred_owned_channel = np.where(no_owned, "none", preferred_owned_channel)

    contact_count_30d = np.clip(rng.poisson(1.1, n_customers), 0, 6)
    days_since_last_contact = np.where(
        contact_count_30d == 0,
        rng.integers(31, 120, n_customers),
        rng.integers(1, 31, n_customers),
    )

    category_match = (predicted_category == true_category).astype(float)
    overcontact = np.clip((contact_count_30d - 1) / 4, 0, 1)
    loyal = (segment == "Loyal high value").astype(float)
    high_value_at_risk = (segment == "High value at risk").astype(float)
    discount_led = (segment == "Discount-led frequent").astype(float)
    dormant = (segment == "Dormant low value").astype(float)
    high_value_signal = np.clip(true_clv / np.quantile(true_clv, 0.80), 0, 1.5)

    true_uplift_reminder = (
        0.008
        + 0.075 * churn_probability * (1 - purchase_probability)
        + 0.020 * high_value_at_risk
        + 0.010 * dormant
        - 0.010 * discount_led
        - 0.020 * overcontact
    )
    true_uplift_voucher_5 = (
        0.005
        + 0.085 * discount_affinity
        + 0.040 * churn_probability
        + 0.035 * high_value_at_risk
        + 0.030 * category_match
        - 0.035 * purchase_probability
        - 0.012 * loyal
        - 0.018 * overcontact
    )
    true_uplift_voucher_10 = (
        true_uplift_voucher_5
        + 0.025 * discount_affinity
        + 0.035 * high_value_at_risk
        + 0.012 * churn_probability
        - 0.018 * loyal
        - 0.008
    )
    true_uplift_service_call = (
        -0.006
        + 0.160 * high_value_at_risk
        + 0.070 * churn_probability * np.clip(high_value_signal, 0, 1)
        + 0.040 * service_failure
        - 0.018 * (1 - np.clip(high_value_signal, 0, 1))
        - 0.020 * overcontact
    )

    true_uplifts = {
        "reminder": np.clip(true_uplift_reminder, -0.04, 0.18),
        "voucher_5": np.clip(true_uplift_voucher_5, -0.04, 0.22),
        "voucher_10": np.clip(true_uplift_voucher_10, -0.04, 0.25),
        "service_call": np.clip(true_uplift_service_call, -0.05, 0.25),
    }
    predicted_uplifts: dict[str, np.ndarray] = {}
    noise = {"reminder": 0.018, "voucher_5": 0.023, "voucher_10": 0.026, "service_call": 0.025}
    for action, truth in true_uplifts.items():
        predicted_uplifts[action] = np.clip(
            0.88 * truth + rng.normal(0, noise[action], n_customers),
            -0.06,
            0.25,
        )

    customer_state = pd.DataFrame(
        {
            "customer_id": customer_id,
            "expected_order_value": expected_order_value,
            "margin_rate": margin_rate,
            "expected_order_margin": expected_order_margin,
            "email_consent": email_consent,
            "push_consent": push_consent,
            "call_consent": call_consent,
            "preferred_owned_channel": preferred_owned_channel,
            "days_since_last_contact": days_since_last_contact,
            "contact_count_30d": contact_count_30d,
        }
    )
    segmentation_scores = pd.DataFrame({"customer_id": customer_id, "segment_name": segment})
    clv_scores = pd.DataFrame(
        {
            "customer_id": customer_id,
            "predicted_clv_180d": predicted_clv,
            "active_probability_180d": np.clip(purchase_probability + 0.12, 0.05, 0.99),
            "clv_lower_80": clv_lower,
            "clv_upper_80": clv_upper,
            "service_tier": service_tier,
            "investment_ceiling": investment_ceiling,
            "high_uncertainty": high_uncertainty,
        }
    )
    score_timestamp = pd.Timestamp(score_date)
    personalized_deadline = score_timestamp + pd.to_timedelta(days_to_deadline, unit="D")
    churn_scores = pd.DataFrame(
        {
            "customer_id": customer_id,
            "score_date": score_timestamp.date().isoformat(),
            "personalized_deadline": personalized_deadline.date.astype(str),
            "personalized_window_days": personalized_window_days,
            "churn_probability": churn_probability,
            "value_at_risk": churn_probability * predicted_clv,
        }
    )
    purchase_scores = pd.DataFrame(
        {
            "customer_id": customer_id,
            "recommended_category": predicted_category,
            "category_probability": category_probability,
            "purchase_readiness_30d": purchase_probability,
            "expected_category_margin": expected_order_margin,
        }
    )
    uplift_scores = pd.DataFrame(
        {
            "customer_id": customer_id,
            "uplift_reminder": predicted_uplifts["reminder"],
            "uplift_voucher_5": predicted_uplifts["voucher_5"],
            "uplift_voucher_10": predicted_uplifts["voucher_10"],
            "uplift_service_call": predicted_uplifts["service_call"],
        }
    )
    evaluator_truth = pd.DataFrame(
        {
            "customer_id": customer_id,
            "true_clv_180d": true_clv,
            "true_preferred_category": true_category,
            "true_uplift_reminder": true_uplifts["reminder"],
            "true_uplift_voucher_5": true_uplifts["voucher_5"],
            "true_uplift_voucher_10": true_uplifts["voucher_10"],
            "true_uplift_service_call": true_uplifts["service_call"],
        }
    )
    return SyntheticBundle(
        customer_state=customer_state,
        segmentation_scores=segmentation_scores,
        clv_scores=clv_scores,
        churn_scores=churn_scores,
        purchase_scores=purchase_scores,
        uplift_scores=uplift_scores,
        evaluator_truth=evaluator_truth,
    )
