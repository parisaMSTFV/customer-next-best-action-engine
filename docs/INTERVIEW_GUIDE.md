# Interview Guide

## One-minute explanation

The earlier portfolio projects answer separate customer questions: who the customer is, how valuable they may be, whether they are nearing a personalized churn window, what they are likely to buy next, and whether a treatment changes behavior. This project creates one synthetic customer universe with compatible score contracts and turns those signals into a single operating policy.

For every customer, the engine first decides whether this is an appropriate time to act. It then compares eligible reminder, voucher, and service-call candidates on expected incremental net value, applies a CLV-based investment ceiling, and solves the final assignment under shared budget and channel capacity. No action is a valid result. Hidden synthetic counterfactual truth is used only after selection to evaluate policy value and regret against an oracle.

## Why not train one large model?

The outputs answer different statistical questions. CLV is a future-value prediction, churn is a timing/risk prediction, next category is a relevance ranking, and treatment uplift is causal. Combining their raw targets into one opaque score would make evaluation and governance harder and could double count information or economics.

## Why is churn risk not enough?

A customer can have high churn risk and still be unresponsive to a treatment. Risk-only targeting answers who may leave; uplift answers whose outcome may change because of an action.

## Why can a voucher have negative value even with positive uplift?

The discount is paid on purchases that would have happened without the offer as well as on incremental purchases. A voucher can therefore raise conversion and still destroy contribution margin.

## Why use CLV as a guardrail instead of adding CLV to the action score?

The action objective is short-horizon incremental value. CLV is a longer-horizon estimate. Adding both would mix horizons and risk double counting. The lower CLV bound instead limits how much the policy is willing to invest in one customer.

## Why keep an oracle?

Synthetic data lets the generator retain counterfactual truth. The oracle shows the best possible policy under the same constraints and makes regret measurable. It is evaluation-only; a leakage test confirms that changing oracle truth cannot change the deployable policy.

## What changes in production?

Replace synthetic score tables with governed model outputs, use real offer economics and redemption rules, add inventory and campaign-collision checks, calibrate treatment effects from randomized experiments, maintain a persistent holdout, monitor drift and policy value, and complete privacy, consent, fairness, and legal reviews.
