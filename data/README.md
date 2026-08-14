# Data

Two data paths are intentionally separated.

## Versioned upstream input

`fixtures/upstream-v1/` is a small, checksummed integration fixture for contract version `1.0`. It exercises the same loader used for external score exports. The fixture values are illustrative and have no evaluator truth.

Run it with:

```bash
next-best-action --project-root . \
  --input-dir data/fixtures/upstream-v1 \
  --output-dir artifacts/external-run
```

## Synthetic benchmark

The full row-level benchmark is regenerated locally and excluded from Git.

Running the pipeline creates these files under `data/generated/`:

- `customer_state.csv`
- `segmentation_scores.csv`
- `clv_scores.csv`
- `churn_scores.csv`
- `purchase_scores.csv`
- `uplift_scores.csv`
- `evaluator_truth.csv`

Only aggregate reports and a small deployable decision sample are committed. See [`DATA_PROVENANCE.md`](../DATA_PROVENANCE.md) for the two input modes and leakage boundary.
