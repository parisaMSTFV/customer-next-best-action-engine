# Reproducible Run Summary

> All values below come from hidden synthetic counterfactual truth and are not production claims.

- Seed: `42`
- Customers: `3000`
- Engine contacts: `700`
- Engine synthetic true incremental net value: **1,248.04**
- Strongest non-oracle baseline: `uplift_reminder_only` at **1,081.82**
- Improvement over strongest baseline: **15.4%**
- Regret versus synthetic oracle: **5.6%**
- Synthetic oracle value: **1,322.06**
- All configured portfolio constraints passed: **True**

The oracle uses hidden synthetic action values only for evaluation. The deployable engine never sees them.
