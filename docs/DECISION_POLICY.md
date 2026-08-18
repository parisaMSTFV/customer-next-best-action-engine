# Decision Policy

## 1. Timing

A customer is suppressed when the configured contact-frequency guardrail fails or no consented owned or call channel is available. Preferred email and push channels must have matching consent in the input contract and are checked again during candidate creation.

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

effective_predicted_uplift = predicted_treated_probability - purchase_readiness_30d

gross_incremental_margin
    = effective_predicted_uplift * expected_order_margin

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

After optimization, a separate eligibility audit rechecks channel consent, `act_now` timing, customer investment ceilings, positive predicted value, and service-call eligibility. Any violation fails the run.

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

## 6. Sensitivity review

The committed stress test varies budget, channel capacity, expected order margin, and voucher
subsidy assumptions. Reviewers should inspect three outputs before approving an operating change:

1. predicted and evaluator-only true value versus the matched reminder baseline;
2. assignment change rate versus the base policy;
3. budget, channel, one-action-per-customer, and customer eligibility-guardrail status.

The base synthetic run is more sensitive to channel capacity than to additional budget. This is
configuration-specific evidence, not a general rule about CRM operations. The policy should be
recomputed whenever its approved constraints or economics change.
