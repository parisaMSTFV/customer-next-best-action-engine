# Policy Sensitivity Summary

> All values use hidden synthetic counterfactual truth for evaluation only.

## Base operating point

- Contacts: **700**
- Synthetic true incremental net value: **1,248.04**
- Regret versus synthetic oracle: **5.6%**

## Constraint sensitivity

- At 0.6x budget, value is **1,203.40**; at 1.4x, it is **1,246.09**.
- At 0.6x channel capacity, value is **1,016.87**; at 1.4x, it is **1,388.43**.

## Economics stress

- Low-margin / high-subsidy value: **971.50**.
- High-margin / low-subsidy value: **1,560.30**.
- Largest assignment change: **9.8%** in `capacity_0.6`.
- All scenario constraints passed: **True**.

## Interpretation boundary

These scenarios test the decision logic under explicit synthetic assumptions. They do not estimate how real customer response, margins, or redemption behavior would change after a policy intervention.
