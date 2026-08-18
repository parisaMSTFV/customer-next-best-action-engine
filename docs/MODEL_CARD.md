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

A hidden evaluator table contains the synthetic counterfactual action effects. Deployable candidate tables contain no evaluator fields. Truth is joined only after policy selection to calculate simulator-known policy value, constrained-oracle value, and regret.

The deployable optimizer maximizes predicted incremental net value and cannot access hidden truth.

## Policy sensitivity

The committed run evaluates 19 scenarios: separate budget and all-channel-capacity multipliers
from 0.6x to 1.4x, plus a 3x3 grid crossing expected-margin and voucher-subsidy multipliers.
All scenarios use the same synthetic customer state and pass budget, channel, and
one-action-per-customer constraints.

In the committed setup, increasing total budget beyond the base point has little value because
channel capacities bind. Increasing channel capacity from 0.6x to 1.4x moves synthetic true
policy value from 1,016.87 to 1,388.43 and changes 9.8% of customer actions at the low-capacity
point. The low-margin/high-subsidy stress value is 971.50; the high-margin/low-subsidy value is
1,560.30. These results diagnose policy behavior under simulator assumptions and are not
production forecasts.

## Key limitations

- Synthetic behavior is simpler than production customer behavior.
- Upstream scores are simulated to match portfolio contracts; the engine does not run the upstream repositories as services.
- Treatment effects assume stable treatment definitions and no interference between customers.
- Voucher economics omit taxes, supplier funding, returns, partial redemption, and long-term habituation.
- The sensitivity grid is deterministic and sparse; it does not assign probabilities to scenarios or quantify parameter uncertainty.
- Timing does not model inventory, live price, channel deliverability, or campaign collision beyond simple frequency controls.
- Channel choice uses consent and engagement preference rather than a causal channel-treatment model.
- Fairness across protected groups is not evaluated because protected characteristics are deliberately absent.
- Real deployment would need experiment holdouts, model monitoring, policy monitoring, and governance review.
