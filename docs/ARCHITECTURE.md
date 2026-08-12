# Architecture

```text
Unified synthetic customer universe
        |
        +--> segmentation contract ---------+
        +--> CLV contract ------------------+
        +--> churn timing contract ---------+--> decision frame
        +--> next-purchase contract --------+
        +--> uplift contract ---------------+
                                              |
                                              v
                                      timing guardrails
                                              |
                                              v
                                      candidate actions
                                              |
                         +--------------------+--------------------+
                         |                                         |
                         v                                         v
                  action economics                         eligibility checks
                         |                                         |
                         +--------------------+--------------------+
                                              |
                                              v
                                    constrained optimizer
                                              |
                                              v
                                  explainable customer policy
                                              |
                                              v
                               hidden-truth policy evaluation
```

## Module responsibilities

- `simulation.py`: clean-room unified synthetic universe and hidden evaluator truth.
- `contracts.py`: schema, key, and leakage-boundary validation.
- `timing.py`: contact-frequency and personalized purchase-window routing.
- `candidates.py`: eligible customer-action rows and comparable economics.
- `policy.py`: mixed-integer portfolio optimization and constrained greedy baselines.
- `baselines.py`: non-oracle comparison policies.
- `explain.py`: one-row-per-customer decision output and reason codes.
- `evaluation.py`: policy value and constraint checks.
- `reporting.py`: reproducible reports and figures.
- `pipeline.py`: end-to-end orchestration.

## Separation of concerns

The engine does not retrain CLV, churn, recommendation, or causal models. Those are upstream analytical responsibilities. The engine consumes their score contracts, applies operating rules, compares actions economically, and solves the portfolio decision.

This separation keeps the capstone from becoming a second copy of every earlier project.
