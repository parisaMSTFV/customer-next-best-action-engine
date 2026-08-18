from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pandas as pd

from next_best_action.baselines import (
    clv_first_voucher,
    purchase_readiness_voucher,
    risk_only_reminder,
    segment_rule_policy,
)
from next_best_action.candidates import build_candidates
from next_best_action.config import load_configs
from next_best_action.contracts import build_decision_frame
from next_best_action.evaluation import (
    add_evaluator_values,
    constraint_summary,
    eligibility_summary,
    policy_metrics,
    predicted_policy_metrics,
)
from next_best_action.explain import add_reason_codes
from next_best_action.inputs import load_external_bundle
from next_best_action.policy import optimize_policy
from next_best_action.reporting import write_operational_reports, write_reports
from next_best_action.sensitivity import run_sensitivity
from next_best_action.simulation import generate_synthetic_bundle
from next_best_action.timing import add_timing_status


def _fingerprint(frame: pd.DataFrame) -> str:
    payload = frame.sort_values("customer_id").to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def run_pipeline(
    project_root: Path,
    customers: int | None = None,
    seed: int | None = None,
    write_outputs: bool = True,
    input_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the engine on synthetic data or versioned upstream artifacts."""
    policy, offers = load_configs(project_root)
    external_manifest: dict[str, Any] | None = None
    if input_dir is None:
        n_customers = int(customers if customers is not None else policy["customers"])
        run_seed = int(seed if seed is not None else policy["seed"])
        bundle = generate_synthetic_bundle(
            n_customers=n_customers,
            seed=run_seed,
            score_date=str(policy["score_date"]),
        )
        evaluator_truth = bundle.evaluator_truth
    else:
        if customers is not None or seed is not None:
            raise ValueError("customers and seed cannot be used with input_dir")
        bundle, external_manifest = load_external_bundle(input_dir)
        n_customers = len(bundle.customer_state)
        run_seed = None
        evaluator_truth = None

    frame = build_decision_frame(bundle)
    frame = add_timing_status(frame, policy)
    candidates = build_candidates(frame, policy, offers)

    engine = optimize_policy(candidates, policy, value_column="predicted_net_value")
    baselines = {
        "risk_only_reminder": risk_only_reminder(candidates, policy),
        "reminder_only_economic_optimizer": optimize_policy(
            candidates.loc[candidates["action"] == "reminder"], policy
        ),
        "clv_first_voucher": clv_first_voucher(candidates, policy),
        "purchase_readiness_voucher": purchase_readiness_voucher(candidates, policy),
        "segment_rules": segment_rule_policy(candidates, policy),
    }

    constraints = constraint_summary(engine, policy)
    eligibility = eligibility_summary(engine, frame, policy)
    if not constraints["within_limit"].all() or not eligibility["within_limit"].all():
        raise RuntimeError("Selected policy failed post-solve constraint or eligibility audit")
    decisions = add_reason_codes(frame, engine, candidates)
    if evaluator_truth is None:
        comparison = pd.DataFrame(
            [
                predicted_policy_metrics("do_nothing", candidates.iloc[0:0], n_customers),
                *[
                    predicted_policy_metrics(name, assignments, n_customers)
                    for name, assignments in baselines.items()
                ],
                predicted_policy_metrics("next_best_action_engine", engine, n_customers),
            ]
        )
        source_artifacts = {
            name: {
                "producer": entry["producer"],
                "artifact_version": entry["artifact_version"],
                "sha256": entry["sha256"],
            }
            for name, entry in external_manifest["artifacts"].items()
        }
        run_metadata: dict[str, object] = {
            "input_mode": "external",
            "input_contract_version": external_manifest["contract_version"],
            "customers": n_customers,
            "score_date": str(frame["score_date"].iloc[0]),
            "deployable_frame_fingerprint": _fingerprint(
                frame.drop(columns=["timing_status", "next_review_days"])
            ),
            "candidates": int(len(candidates)),
            "act_now_customers": int((frame["timing_status"] == "act_now").sum()),
            "engine_contacts": int(len(engine)),
            "engine_predicted_incremental_net_value": float(engine["predicted_net_value"].sum()),
            "all_portfolio_constraints_pass": bool(constraints["within_limit"].all()),
            "all_eligibility_guardrails_pass": bool(eligibility["within_limit"].all()),
            "all_constraints_pass": bool(
                constraints["within_limit"].all() and eligibility["within_limit"].all()
            ),
            "source_artifacts": source_artifacts,
        }
        if write_outputs:
            target = output_dir or project_root / "artifacts" / "external_run"
            write_operational_reports(
                target,
                comparison,
                engine,
                decisions,
                constraints,
                eligibility,
                run_metadata,
            )
        return run_metadata

    evaluated_candidates = add_evaluator_values(candidates, evaluator_truth, offers)
    evaluated_engine = add_evaluator_values(engine, evaluator_truth, offers)
    evaluated_baselines = {
        name: add_evaluator_values(assignments, evaluator_truth, offers)
        for name, assignments in baselines.items()
    }
    oracle = optimize_policy(
        evaluated_candidates,
        policy,
        value_column="true_net_value",
    )
    oracle_true_value = float(oracle["true_net_value"].sum())
    metrics = [
        policy_metrics("do_nothing", candidates.iloc[0:0], n_customers, oracle_true_value),
        *[
            policy_metrics(name, assignments, n_customers, oracle_true_value)
            for name, assignments in evaluated_baselines.items()
        ],
        policy_metrics(
            "next_best_action_engine",
            evaluated_engine,
            n_customers,
            oracle_true_value,
        ),
        policy_metrics(
            "constrained_synthetic_oracle",
            oracle,
            n_customers,
            oracle_true_value,
        ),
    ]
    comparison = pd.DataFrame(metrics)
    run_metadata: dict[str, object] = {
        "seed": run_seed,
        "customers": n_customers,
        "score_date": str(policy["score_date"]),
        "deployable_frame_fingerprint": _fingerprint(
            frame.drop(columns=["timing_status", "next_review_days"])
        ),
        "candidates": int(len(candidates)),
        "act_now_customers": int((frame["timing_status"] == "act_now").sum()),
        "engine_contacts": int(len(engine)),
        "engine_true_incremental_net_value": float(evaluated_engine["true_net_value"].sum()),
        "oracle_true_incremental_net_value": oracle_true_value,
        "engine_regret_vs_oracle": float(
            (oracle_true_value - float(evaluated_engine["true_net_value"].sum()))
            / oracle_true_value
            if oracle_true_value > 0
            else 0.0
        ),
        "all_portfolio_constraints_pass": bool(constraints["within_limit"].all()),
        "all_eligibility_guardrails_pass": bool(eligibility["within_limit"].all()),
        "all_constraints_pass": bool(
            constraints["within_limit"].all() and eligibility["within_limit"].all()
        ),
    }
    if write_outputs:
        target_root = output_dir or project_root
        sensitivity_summary, sensitivity_allocation = run_sensitivity(
            frame,
            bundle.evaluator_truth,
            policy,
            offers,
        )
        base_sensitivity = sensitivity_summary.loc[
            (sensitivity_summary["dimension"] == "budget")
            & (sensitivity_summary["budget_multiplier"] == 1.0)
        ].iloc[0]
        run_metadata["sensitivity_scenarios"] = int(len(sensitivity_summary))
        run_metadata["base_assignment_change_rate"] = float(
            base_sensitivity["assignment_change_rate_vs_base"]
        )
        run_metadata["all_sensitivity_constraints_pass"] = bool(
            sensitivity_summary["all_constraints_pass"].all()
        )
        write_reports(
            target_root,
            comparison,
            engine,
            decisions,
            constraints,
            eligibility,
            sensitivity_summary,
            sensitivity_allocation,
            run_metadata,
        )

        data_dir = target_root / "data" / "generated"
        data_dir.mkdir(parents=True, exist_ok=True)
        bundle.customer_state.to_csv(data_dir / "customer_state.csv", index=False)
        bundle.segmentation_scores.to_csv(data_dir / "segmentation_scores.csv", index=False)
        bundle.clv_scores.to_csv(data_dir / "clv_scores.csv", index=False)
        bundle.churn_scores.to_csv(data_dir / "churn_scores.csv", index=False)
        bundle.purchase_scores.to_csv(data_dir / "purchase_scores.csv", index=False)
        bundle.uplift_scores.to_csv(data_dir / "uplift_scores.csv", index=False)
        bundle.evaluator_truth.to_csv(data_dir / "evaluator_truth.csv", index=False)

    return run_metadata
