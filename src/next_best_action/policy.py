from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix


def optimize_policy(
    candidates: pd.DataFrame,
    policy: dict[str, Any],
    value_column: str = "predicted_net_value",
) -> pd.DataFrame:
    """Maximize portfolio value with customer, budget, and channel constraints."""
    if candidates.empty:
        return candidates.copy()
    if value_column not in candidates:
        raise ValueError(f"Missing objective column: {value_column}")

    working = candidates.loc[candidates[value_column] > 1e-12].reset_index(drop=True).copy()
    if working.empty:
        return candidates.iloc[0:0].copy()
    n_vars = len(working)
    customer_groups = working.groupby("customer_id", sort=False).indices
    channel_capacity = policy["portfolio"]["channel_capacity"]
    channels = [channel for channel in ["push", "email", "call"] if channel in channel_capacity]

    n_constraints = len(customer_groups) + 1 + len(channels)
    matrix = lil_matrix((n_constraints, n_vars), dtype=float)
    upper = np.zeros(n_constraints, dtype=float)
    lower = np.full(n_constraints, -np.inf, dtype=float)

    row_idx = 0
    for indices in customer_groups.values():
        matrix[row_idx, list(indices)] = 1.0
        upper[row_idx] = 1.0
        row_idx += 1

    matrix[row_idx, :] = working["expected_cost"].to_numpy(dtype=float)
    upper[row_idx] = float(policy["portfolio"]["total_budget"])
    row_idx += 1

    for channel in channels:
        indices = np.flatnonzero(working["channel"].to_numpy() == channel)
        if len(indices):
            matrix[row_idx, indices] = 1.0
        upper[row_idx] = float(channel_capacity[channel])
        row_idx += 1

    objective = -working[value_column].to_numpy(dtype=float)
    result = milp(
        c=objective,
        integrality=np.ones(n_vars, dtype=int),
        bounds=Bounds(np.zeros(n_vars), np.ones(n_vars)),
        constraints=LinearConstraint(matrix.tocsr(), lower, upper),
        options={"time_limit": 30.0},
    )
    if not result.success or result.x is None:
        raise RuntimeError(f"Policy optimization failed: {result.message}")

    selected = working.loc[result.x > 0.5].copy()
    selected["solver_status"] = str(result.message)
    return selected.sort_values(value_column, ascending=False).reset_index(drop=True)


def greedy_assign(
    candidate_rows: pd.DataFrame,
    policy: dict[str, Any],
    priority_order: Iterable[int],
) -> pd.DataFrame:
    """Apply a ranked baseline while respecting the same portfolio constraints."""
    budget = float(policy["portfolio"]["total_budget"])
    capacities = {key: int(value) for key, value in policy["portfolio"]["channel_capacity"].items()}
    selected_indices: list[int] = []
    used_customers: set[str] = set()
    budget_used = 0.0
    channel_used = {key: 0 for key in capacities}

    for idx in priority_order:
        row = candidate_rows.loc[idx]
        customer_id = str(row["customer_id"])
        channel = str(row["channel"])
        cost = float(row["expected_cost"])
        if customer_id in used_customers:
            continue
        if budget_used + cost > budget + 1e-12:
            continue
        if channel_used[channel] >= capacities[channel]:
            continue
        selected_indices.append(int(idx))
        used_customers.add(customer_id)
        budget_used += cost
        channel_used[channel] += 1

    return candidate_rows.loc[selected_indices].copy().reset_index(drop=True)
