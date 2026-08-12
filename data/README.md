# Data

The full row-level synthetic run is regenerated locally and intentionally excluded from Git.

Running the pipeline creates these files under `data/generated/`:

- `customer_state.csv`
- `segmentation_scores.csv`
- `clv_scores.csv`
- `churn_scores.csv`
- `purchase_scores.csv`
- `uplift_scores.csv`
- `evaluator_truth.csv`

Only aggregate reports and a small deployable decision sample are committed. See [`DATA_PROVENANCE.md`](../DATA_PROVENANCE.md) for the generation and leakage boundary.
