from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def add_evaluator_values(
    assignments: pd.DataFrame,
    evaluator_truth: pd.DataFrame,
    offer_config: dict[str, Any],
) -> pd.DataFrame:
    """Attach simulator-known values after deployable policy selection."""
    if any(column.startswith("true_") for column in assignments.columns):
        raise ValueError("Deployable assignments must not contain evaluator-truth columns")

    evaluated = assignments.copy()
    if evaluated.empty:
        evaluated["true_uplift"] = pd.Series(dtype=float)
        evaluated["effective_true_uplift"] = pd.Series(dtype=float)
        evaluated["true_net_value"] = pd.Series(dtype=float)
        return evaluated

    truth = evaluator_truth.set_index("customer_id")
    missing = sorted(set(evaluated["customer_id"].astype(str)) - set(truth.index.astype(str)))
    if missing:
        raise ValueError(f"Evaluator truth is missing customer IDs: {missing[:5]}")

    true_uplift = np.array(
        [
            float(truth.loc[str(row.customer_id), f"true_uplift_{row.action}"])
            for row in evaluated.itertuples(index=False)
        ],
        dtype=float,
    )
    baseline = evaluated["purchase_readiness_30d"].to_numpy(dtype=float)
    treated = np.clip(baseline + true_uplift, 0, 1)
    effective_uplift = treated - baseline
    discount_rate = np.array(
        [float(offer_config["offers"][action]["discount_rate"]) for action in evaluated["action"]]
    )
    contact_cost = np.array(
        [
            float(offer_config["offers"][row.action]["fixed_action_cost"])
            + float(offer_config["channel_cost"][row.channel])
            for row in evaluated.itertuples(index=False)
        ]
    )
    true_subsidy = treated * discount_rate * evaluated["expected_order_value"].to_numpy(dtype=float)
    evaluated["true_uplift"] = true_uplift
    evaluated["effective_true_uplift"] = effective_uplift
    evaluated["true_net_value"] = (
        effective_uplift * evaluated["expected_order_margin"].to_numpy(dtype=float)
        - contact_cost
        - true_subsidy
    )
    return evaluated


def predicted_policy_metrics(
    name: str,
    assignments: pd.DataFrame,
    total_customers: int,
) -> dict[str, float | int | str]:
    """Summarize a deployable policy when counterfactual truth is unavailable."""
    contacts = len(assignments)
    budget_used = float(assignments["expected_cost"].sum()) if contacts else 0.0
    predicted = float(assignments["predicted_net_value"].sum()) if contacts else 0.0
    return {
        "policy": name,
        "customers_contacted": contacts,
        "contact_rate": contacts / total_customers if total_customers else 0.0,
        "no_action_rate": 1 - contacts / total_customers if total_customers else 1.0,
        "budget_used": budget_used,
        "predicted_net_value": predicted,
        "predicted_value_per_contact": predicted / contacts if contacts else 0.0,
    }


def policy_metrics(
    name: str,
    assignments: pd.DataFrame,
    total_customers: int,
    oracle_true_value: float,
) -> dict[str, float | int | str]:
    """Summarize a policy using hidden synthetic truth only for evaluation."""
    contacts = len(assignments)
    budget_used = float(assignments["expected_cost"].sum()) if contacts else 0.0
    predicted = float(assignments["predicted_net_value"].sum()) if contacts else 0.0
    true_value = float(assignments["true_net_value"].sum()) if contacts else 0.0
    regret = (oracle_true_value - true_value) / oracle_true_value if oracle_true_value > 0 else 0.0
    return {
        "policy": name,
        "customers_contacted": contacts,
        "contact_rate": contacts / total_customers,
        "no_action_rate": 1 - contacts / total_customers,
        "budget_used": budget_used,
        "predicted_net_value": predicted,
        "true_incremental_net_value": true_value,
        "true_value_per_contact": true_value / contacts if contacts else 0.0,
        "regret_vs_oracle": regret,
    }


def constraint_summary(assignments: pd.DataFrame, policy: dict[str, Any]) -> pd.DataFrame:
    """Report budget and channel capacity utilization."""
    budget = float(policy["portfolio"]["total_budget"])
    rows: list[dict[str, float | int | str | bool]] = [
        {
            "constraint": "total_budget",
            "used": float(assignments["expected_cost"].sum()),
            "limit": budget,
            "within_limit": float(assignments["expected_cost"].sum()) <= budget + 1e-9,
        }
    ]
    for channel, limit in policy["portfolio"]["channel_capacity"].items():
        used = int((assignments["channel"] == channel).sum())
        rows.append(
            {
                "constraint": f"channel_{channel}",
                "used": used,
                "limit": int(limit),
                "within_limit": used <= int(limit),
            }
        )
    duplicated = int(assignments["customer_id"].duplicated().sum())
    rows.append(
        {
            "constraint": "one_action_per_customer",
            "used": duplicated,
            "limit": 0,
            "within_limit": duplicated == 0,
        }
    )
    return pd.DataFrame(rows)


def eligibility_summary(
    assignments: pd.DataFrame,
    decision_frame: pd.DataFrame,
    policy: dict[str, Any],
) -> pd.DataFrame:
    """Audit selected actions against customer-level eligibility guardrails."""
    audit_names = [
        "channel_consent",
        "act_now_timing",
        "investment_ceiling",
        "positive_predicted_value",
        "service_call_eligibility",
    ]
    if assignments.empty:
        return pd.DataFrame(
            {
                "guardrail": audit_names,
                "violations": [0] * len(audit_names),
                "limit": [0] * len(audit_names),
                "within_limit": [True] * len(audit_names),
            }
        )

    context_columns = [
        "customer_id",
        "timing_status",
        "email_consent",
        "push_consent",
        "call_consent",
        "service_tier",
        "churn_probability",
        "high_uncertainty",
    ]
    selected = assignments.merge(
        decision_frame[context_columns],
        on="customer_id",
        how="left",
        validate="many_to_one",
        suffixes=("", "_context"),
    )
    if selected["timing_status"].isna().any():
        raise ValueError("Selected assignments contain unknown customer IDs")

    channel_consent = (
        ((selected["channel"] == "email") & ~selected["email_consent"])
        | ((selected["channel"] == "push") & ~selected["push_consent"])
        | ((selected["channel"] == "call") & ~selected["call_consent"])
    )
    timing = selected["timing_status"] != "act_now"
    investment = selected["expected_cost"] > selected["investment_ceiling"] + 1e-9
    positive_value = selected["predicted_net_value"] <= 1e-12

    service_cfg = policy["service_call"]
    service_rows = selected["action"] == "service_call"
    service_violation = service_rows & (
        ~selected["call_consent"]
        | ~selected["service_tier"].isin(set(service_cfg["eligible_tiers"]))
        | (selected["churn_probability"] < float(service_cfg["minimum_churn_probability"]))
        | (
            bool(policy["uncertainty"].get("suppress_high_uncertainty_service_call", True))
            & selected["high_uncertainty"]
        )
    )
    violations = [
        int(channel_consent.sum()),
        int(timing.sum()),
        int(investment.sum()),
        int(positive_value.sum()),
        int(service_violation.sum()),
    ]
    return pd.DataFrame(
        {
            "guardrail": audit_names,
            "violations": violations,
            "limit": [0] * len(audit_names),
            "within_limit": [value == 0 for value in violations],
        }
    )
