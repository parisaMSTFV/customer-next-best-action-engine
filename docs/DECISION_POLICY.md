# Decision Policy

## 1. Timing

A customer is suppressed when the configured contact-frequency or consent guardrail fails.

Otherwise, timing uses the personalized purchase window together with purchase readiness and churn probability to route the customer to:

- `act_now`;
- `review_soon`;
- `monitor`.

Only `act_now` customers enter active action optimization. Thresholds are synthetic case-study configuration, not universal CRM rules.

## 2. Candidate eligibility

Every `act_now` customer can be considered for reminder, 5% voucher, and 10% voucher actions when an owned channel is available.

Service calls additionally require:

- call consent;
- Protect or Grow CLV tier;
- minimum churn probability;
- acceptable CLV uncertainty.

Every candidate must fit inside the customer's CLV-based `investment_ceiling`.

## 3. Incremental economics

For customer `i` and action `a`, the engine calculates:

```text
predicted_treated_probability = clip(purchase_readiness_30d + predicted_uplift, 0, 1)

gross_incremental_margin
    = predicted_uplift * expected_order_margin

expected_action_cost
    = fixed_action_cost
    + channel_cost
    + predicted_treated_probability * discount_rate * expected_order_value

predicted_incremental_net_value
    = gross_incremental_margin - expected_action_cost
```

The voucher subsidy is charged on **all expected treated purchases**, not only on incremental purchases. This deliberately penalizes offers that mostly subsidize customers who were already likely to buy.

The 180-day CLV estimate is not added to the 30-day action value. CLV is used as an investment and service guardrail so that different time horizons are not double counted.

## 4. Portfolio optimization

The mixed-integer policy maximizes total predicted incremental net value subject to:

- at most one active action per customer;
- a shared expected-action-cost budget;
- separate push, email, and call capacities;
- customer-level eligibility and investment ceilings applied before optimization.

No action is always feasible. The optimizer is never required to spend budget or fill capacity with a negative-value action.

## 5. Reason codes

The deployable decision table records concise reason codes such as:

- `positive_incremental_value`;
- `high_churn_risk`;
- `purchase_ready`;
- `high_category_confidence`;
- `high_value_tier`;
- `wait_for_better_timing`;
- `contact_frequency_or_consent_guardrail`;
- `no_positive_incremental_value`;
- `positive_candidate_not_selected_under_portfolio_constraints`.

Reason codes explain the policy path. They are not causal explanations of individual behavior.
