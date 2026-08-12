# Upstream Contracts

The engine is designed around outputs already represented in the portfolio. It does not import model packages or join row-level files from those repositories because each project has an independent synthetic customer universe.

The integration pattern is therefore **contract reuse, not synthetic-ID reuse**.

| Portfolio repository | Capability reused | Harmonized fields used here |
|---|---|---|
| `customer-segmentation-decision-system` | Behavioral and value context | `customer_id`, `segment_name` |
| `customer-lifetime-value-decision-system` | Expected value, uncertainty, service tier, investment guardrail | `predicted_clv_180d`, `active_probability_180d`, `clv_lower_80`, `clv_upper_80`, `service_tier`, `investment_ceiling`, `high_uncertainty` |
| `customer-churn-personalized-window` | Customer-specific retention timing | `score_date`, `personalized_deadline`, `personalized_window_days`, `churn_probability`, `value_at_risk` |
| `next-purchase-recommendation` | Near-term purchase readiness and category relevance | `recommended_category`, `category_probability`, `purchase_readiness_30d`, `expected_category_margin` |
| `retention-treatment-uplift` | Heterogeneous treatment response and the principle of comparing action value to control | action-level uplift scores for reminder, voucher, and service actions |
| `marketing-budget-allocation-optimizer` | Constrained optimization discipline | shared budget and capacity constraints; no customer-level scores are imported |

## Why the contracts are harmonized

The existing causal project evaluates reminder, voucher, and service-call treatments on a 60-day contribution outcome. This repository needs a common action-value horizon and an explicit voucher subsidy calculation, so the synthetic integration layer exposes action-level purchase-probability uplift and recomputes economics consistently for every candidate.

That is an intentional integration contract, not a claim that the upstream repository currently exports the exact same columns.

## Systems not directly used in version 1

`pdp-content-uplift-decision-system` is not a required input to the first engine version. It is a natural future source of evidence for a `content_enrichment` or onsite-guidance action, but adding it now would mix a page-level experiment with the customer-level action policy without a clean shared treatment contract.
