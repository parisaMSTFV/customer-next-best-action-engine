# Data Provenance

The repository supports two explicitly separated input modes.

## External artifact mode

The engine can consume six standardized score exports through a versioned, checksummed manifest. The loader validates provenance metadata, file integrity, schema, customer keys, probabilities, booleans, and score date before building a decision frame. External runs do not load evaluator truth and do not report observed causal value.

The committed `data/fixtures/upstream-v1/` bundle is an illustrative integration fixture, not customer data or an observed campaign result.

## Synthetic benchmark mode

Every customer, score, offer, constraint, cost, and outcome in the committed benchmark is generated from scratch by `src/next_best_action/simulation.py`.

The project does not copy row-level data from the upstream portfolio repositories. Their public evidence uses separate synthetic or licensed public datasets and does not share a joinable customer universe, so joining customer IDs would create a false integration. Instead, this project creates one new customer universe and reproduces compatible score contracts for segmentation, CLV, churn timing, next-purchase relevance, and treatment uplift.

### What is generated

- anonymous customer IDs prefixed with `SYN-`;
- behavioral segment assignments;
- 180-day CLV estimates, intervals, tiers, and investment ceilings;
- personalized purchase-window churn scores;
- 30-day purchase readiness and next-category recommendations;
- action-level heterogeneous treatment uplift scores;
- consent, contact-frequency, channel, and offer-cost inputs;
- hidden synthetic counterfactual truth for policy evaluation only.

### Evaluation boundary

`evaluator_truth.csv` contains hidden synthetic action effects used to calculate constrained-oracle value and policy regret. It is never merged into the deployable decision frame or candidate table. Evaluator values are joined only after deployable policy selection. The file is written only under `data/generated/`, which is excluded from version control.

A leakage test mutates the hidden truth and confirms that the selected deployable policy does not change.

## What is not included

No real customer, transaction, company schema, query, server, dashboard, credential, internal threshold, campaign result, or proprietary business rule is included. All committed benchmark metrics describe the controlled synthetic run only.
