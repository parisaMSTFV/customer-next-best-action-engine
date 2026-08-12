from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def write_reports(
    project_root: Path,
    policy_comparison: pd.DataFrame,
    engine_assignments: pd.DataFrame,
    decisions: pd.DataFrame,
    constraints: pd.DataFrame,
    run_metadata: dict[str, object],
) -> None:
    """Write machine-readable reports, samples, and figures."""
    reports = project_root / "reports"
    figures = reports / "figures"
    reports.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    policy_comparison.to_csv(reports / "policy_comparison.csv", index=False)
    constraints.to_csv(reports / "constraint_summary.csv", index=False)
    engine_assignments.groupby(["action", "channel"], observed=True).agg(
        customers=("customer_id", "size"),
        predicted_net_value=("predicted_net_value", "sum"),
        expected_cost=("expected_cost", "sum"),
    ).reset_index().to_csv(reports / "action_allocation.csv", index=False)

    sample = decisions.sort_values("predicted_incremental_net_value", ascending=False).head(40)
    sample.to_csv(reports / "decision_sample.csv", index=False)
    with (reports / "run_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(run_metadata, handle, indent=2, sort_keys=True)
    _write_run_summary(reports / "run_summary.md", policy_comparison, run_metadata)

    _plot_policy_value(policy_comparison, figures / "policy_value_comparison.png")
    _plot_action_mix(engine_assignments, figures / "action_mix.png")


def _plot_policy_value(frame: pd.DataFrame, path: Path) -> None:
    values = frame["true_incremental_net_value"].to_numpy(dtype=float)
    label_map = {
        "do_nothing": "Do nothing",
        "risk_only_reminder": "Risk-only reminder",
        "uplift_reminder_only": "Uplift reminder only",
        "clv_first_voucher": "CLV-first voucher",
        "purchase_readiness_voucher": "Purchase-ready voucher",
        "segment_rules": "Segment rules",
        "next_best_action_engine": "NBA engine",
        "synthetic_oracle": "Synthetic oracle",
    }
    labels = [label_map.get(value, value) for value in frame["policy"]]
    positions = np.arange(len(values))
    fig, ax = plt.subplots(figsize=(10, 5.2))
    bars = ax.bar(positions, values)
    ax.set_xticks(positions, labels, rotation=25, ha="right")
    ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=8)
    ax.set_ylabel("Synthetic true incremental net value")
    ax.set_title("Policy value under hidden synthetic counterfactual truth")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_action_mix(assignments: pd.DataFrame, path: Path) -> None:
    counts = assignments["action"].value_counts().sort_index()
    label_map = {
        "reminder": "Reminder",
        "service_call": "Service call",
        "voucher_5": "5% voucher",
        "voucher_10": "10% voucher",
    }
    labels = [label_map.get(value, value) for value in counts.index]
    positions = np.arange(len(counts))
    fig, ax = plt.subplots(figsize=(7.5, 4.7))
    bars = ax.bar(positions, counts.to_numpy())
    ax.set_xticks(positions, labels, rotation=15, ha="right")
    ax.bar_label(bars, padding=3, fontsize=9)
    ax.set_ylabel("Customers")
    ax.set_title("Next-best-action allocation")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _write_run_summary(
    path: Path,
    comparison: pd.DataFrame,
    metadata: dict[str, object],
) -> None:
    engine = comparison.loc[comparison["policy"] == "next_best_action_engine"].iloc[0]
    oracle = comparison.loc[comparison["policy"] == "synthetic_oracle"].iloc[0]
    baseline_rows = comparison.loc[
        ~comparison["policy"].isin(["do_nothing", "next_best_action_engine", "synthetic_oracle"])
    ]
    best_baseline = baseline_rows.sort_values("true_incremental_net_value", ascending=False).iloc[0]
    baseline_value = float(best_baseline["true_incremental_net_value"])
    engine_value = float(engine["true_incremental_net_value"])
    improvement = engine_value / baseline_value - 1 if baseline_value > 0 else 0.0

    lines = [
        "# Reproducible Run Summary",
        "",
        (
            "> All values below come from hidden synthetic counterfactual truth "
            "and are not production claims."
        ),
        "",
        f"- Seed: `{metadata['seed']}`",
        f"- Customers: `{metadata['customers']}`",
        f"- Engine contacts: `{int(engine['customers_contacted'])}`",
        f"- Engine synthetic true incremental net value: **{engine_value:,.2f}**",
        (
            f"- Strongest non-oracle baseline: `{best_baseline['policy']}` "
            f"at **{baseline_value:,.2f}**"
        ),
        f"- Improvement over strongest baseline: **{improvement:.1%}**",
        f"- Regret versus synthetic oracle: **{float(engine['regret_vs_oracle']):.1%}**",
        f"- Synthetic oracle value: **{float(oracle['true_incremental_net_value']):,.2f}**",
        f"- All configured portfolio constraints passed: **{metadata['all_constraints_pass']}**",
        "",
        (
            "The oracle uses hidden synthetic action values only for evaluation. "
            "The deployable engine never sees them."
        ),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
