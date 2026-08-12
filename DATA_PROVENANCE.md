# Data Provenance

Every customer, score, offer, constraint, cost, and outcome in this repository is synthetic and generated from scratch by `src/next_best_action/simulation.py`.

The project does not copy row-level data from the upstream portfolio repositories. Those repositories were built with separate synthetic customer universes, so joining their customer IDs would create a false integration. Instead, this project creates one new customer universe and reproduces compatible score contracts for segmentation, CLV, churn timing, next-purchase relevance, and treatment uplift.

## What is generated

- anonymous customer IDs prefixed with `SYN-`;
- behavioral segment assignments;
- 180-day CLV estimates, intervals, tiers, and investment ceilings;
- personalized purchase-window churn scores;
- 30-day purchase readiness and next-category recommendations;
- action-level heterogeneous treatment uplift scores;
- consent, contact-frequency, channel, and offer-cost inputs;
- hidden synthetic counterfactual truth for policy evaluation only.

## Evaluation boundary

`evaluator_truth.csv` contains hidden synthetic action effects used to calculate oracle value and policy regret. It is never merged into the deployable decision frame and is written only under `data/generated/`, which is excluded from version control.

A leakage test mutates the hidden truth and confirms that the selected deployable policy does not change.

## What is not included

No real customer, transaction, company schema, query, server, dashboard, credential, internal threshold, campaign result, or proprietary business rule is included. All public metrics describe this controlled synthetic run only.
