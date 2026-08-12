# Decision System Card

## Intended use

Demonstrate how customer-level predictions and causal scores can be orchestrated into an auditable next-best-action policy under economic and operational constraints.

The project is suitable for portfolio review, method discussion, and controlled synthetic experimentation.

## Not intended for

- production customer targeting without governed real-world validation;
- individual pricing or credit decisions;
- protected-attribute targeting;
- claiming that the synthetic policy value is achievable in a real business;
- replacing consent, legal, brand, or customer-experience policy.

## Inputs

The deployable decision frame contains synthetic equivalents of segmentation, CLV, churn timing, purchase readiness, category recommendation, uplift, consent, contact history, and unit economics.

Protected characteristics are not generated or used.

## Evaluation

A hidden evaluator table contains the synthetic counterfactual action effects. It is used only after policy selection to calculate true synthetic policy value, oracle value, and regret.

The deployable optimizer maximizes predicted incremental net value and cannot access hidden truth.

## Key limitations

- Synthetic behavior is simpler than production customer behavior.
- Upstream scores are simulated to match portfolio contracts; the engine does not run the upstream repositories as services.
- Treatment effects assume stable treatment definitions and no interference between customers.
- Voucher economics omit taxes, supplier funding, returns, partial redemption, and long-term habituation.
- Timing does not model inventory, live price, channel deliverability, or campaign collision beyond simple frequency controls.
- Channel choice uses consent and engagement preference rather than a causal channel-treatment model.
- Fairness across protected groups is not evaluated because protected characteristics are deliberately absent.
- Real deployment would need experiment holdouts, model monitoring, policy monitoring, and governance review.
