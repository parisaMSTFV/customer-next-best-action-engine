# Analysis Plan

## Portfolio role

This is an orchestration and decision-policy project. The upstream portfolio projects demonstrate individual analytical capabilities; this repository demonstrates how those signals can be combined into one customer-level operating decision.

Primary audience: Decision Science, Customer Analytics, CRM Analytics, and Data Science hiring teams.

## Business question

For each eligible customer at a decision date:

1. Is this a good time to act?
2. Which action has the highest expected incremental net value?
3. Which category should contextualize the message or offer?
4. Which customers should be left untreated?
5. How should decisions change when budget and channel capacity are limited?

## Decision unit

One row in the final deployable artifact represents one customer at one score date.

The active action set is:

- no action;
- reminder;
- 5% voucher;
- 10% voucher;
- service call.

The recommended category comes from the next-purchase contract and is attached as message or offer context. Channel is resolved from consent and owned-channel preference; service calls require call consent.

## Evidence layers

- Behavioral segment: customer context.
- CLV: value tier, uncertainty, and an individual investment ceiling.
- Personalized churn window: timing and retention urgency.
- Purchase readiness and next category: near-term relevance.
- Treatment uplift: action-specific incremental response.
- Offer economics: subsidy and contact cost.
- Portfolio optimization: budget and channel capacity.

## Baselines

The final engine is compared with:

- do nothing;
- churn-risk-only reminder targeting;
- a reminder-only economic optimizer;
- CLV-first 5% voucher targeting;
- purchase-readiness 5% voucher targeting;
- segment-rule targeting;
- a constrained synthetic oracle that sees hidden counterfactual truth only within the deployable candidate set.

The constrained oracle is evaluation-only and cannot influence the deployable policy.

## Primary evaluation metric

Simulator-known incremental net value under hidden synthetic counterfactual truth.

Secondary metrics:

- value per contact;
- regret versus the constrained synthetic oracle;
- budget used;
- channel utilization;
- contact rate and no-action rate;
- constraint violations.

## Completion criteria

The project is complete when:

- deployable features and evaluator truth are separated and tested;
- all policies are evaluated under the same constraints;
- the engine is compared with strong non-oracle baselines;
- the optimizer can choose no action;
- all configured portfolio constraints and customer eligibility guardrails pass;
- results are reproducible from a fixed seed;
- public files pass the sensitive-content scan;
- CI runs lint, tests, safety checks, and a smoke pipeline.
