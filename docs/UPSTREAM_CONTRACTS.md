# Upstream Contracts

The engine consumes six standardized CSV artifacts through contract version `1.0`. A JSON manifest records each file's producer, artifact version, relative path, and SHA-256 checksum. The loader rejects missing files, changed bytes, unsupported contracts, duplicate or mismatched customer keys, invalid booleans, out-of-range probabilities, and inconsistent score dates before policy logic runs.

This is a file boundary, not a package dependency: upstream systems export governed scores, while this repository owns action economics, guardrails, and portfolio optimization. The committed fixture demonstrates the executable boundary; it does not claim that independently generated demo customer IDs can be joined.

| Portfolio repository | Capability reused | Harmonized fields used here |
|---|---|---|
| `customer-segmentation-decision-system` | Behavioral and value context | `customer_id`, `segment_name` |
| `customer-lifetime-value-decision-system` | Expected value, uncertainty, service tier, investment guardrail | `predicted_clv_180d`, `active_probability_180d`, `clv_lower_80`, `clv_upper_80`, `service_tier`, `investment_ceiling`, `high_uncertainty` |
| `customer-churn-personalized-window` | Customer-specific retention timing | `score_date`, `personalized_deadline`, `personalized_window_days`, `churn_probability`, `value_at_risk` |
| `next-purchase-recommendation` | Near-term purchase readiness and category relevance | `recommended_category`, `category_probability`, `purchase_readiness_30d`, `expected_category_margin` |
| `retention-treatment-uplift` | Heterogeneous treatment response and the principle of comparing action value to control | action-level uplift scores for reminder, voucher, and service actions |
| `marketing-budget-allocation-optimizer` | Constrained optimization discipline | shared budget and capacity constraints; no customer-level scores are imported |

## Manifest

```json
{
  "contract_version": "1.0",
  "score_date": "2026-08-01",
  "artifacts": {
    "clv_scores": {
      "path": "clv_scores.csv",
      "producer": "customer-lifetime-value-decision-system",
      "artifact_version": "2026-08-01.v1",
      "sha256": "<64 lowercase hexadecimal characters>"
    }
  }
}
```

The complete manifest must define exactly these artifacts:

- `customer_state`
- `segmentation_scores`
- `clv_scores`
- `churn_scores`
- `purchase_scores`
- `uplift_scores`

All six files must contain the same unique `customer_id` universe. `churn_scores.score_date` must contain one date equal to the manifest's `score_date`. See [`data/fixtures/upstream-v1`](../data/fixtures/upstream-v1) for the runnable shape and [`contracts.py`](../src/next_best_action/contracts.py) for exact required columns.

## Execute an artifact bundle

```bash
next-best-action --project-root . \
  --input-dir /path/to/versioned-export \
  --output-dir artifacts/external-run
```

External mode never expects `evaluator_truth.csv`. It writes `decisions.csv`, constraint utilization, action allocation, source-version metadata, and predicted policy comparisons. Observed incremental value still requires a randomized holdout.

## Why the contracts are harmonized

The existing causal project evaluates reminder, voucher, and service-call treatments on a 60-day contribution outcome. This repository needs a common action-value horizon and an explicit voucher subsidy calculation, so the export adapter must expose action-level purchase-probability uplift and the engine recomputes economics consistently for every candidate.

That is an intentional integration contract, not a claim that every upstream repository already emits this exact export without an adapter.

## Systems not directly used in version 1

`pdp-content-uplift-decision-system` is not a required input to the first engine version. It is a natural future source of evidence for a `content_enrichment` or onsite-guidance action, but adding it now would mix a page-level experiment with the customer-level action policy without a clean shared treatment contract.
