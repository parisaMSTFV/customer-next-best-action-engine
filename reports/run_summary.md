# Reproducible Run Summary

> All values below come from hidden synthetic counterfactual truth and are not production claims.

- Seed: `42`
- Customers: `3000`
- Engine contacts: `700`
- Engine simulator-known incremental net value: **1,248.04**
- Strongest non-oracle baseline: `reminder_only_economic_optimizer` at **1,081.82**
- Improvement over strongest baseline: **15.4%**
- Regret versus constrained synthetic oracle: **5.6%**
- Constrained synthetic oracle value: **1,322.06**
- All configured portfolio constraints and customer eligibility guardrails passed: **True**

The constrained oracle uses hidden synthetic action values only for evaluation. The deployable engine never sees them.
