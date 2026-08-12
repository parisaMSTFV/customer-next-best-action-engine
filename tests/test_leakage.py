from dataclasses import replace

import pandas as pd

from next_best_action.candidates import build_candidates
from next_best_action.contracts import build_decision_frame
from next_best_action.policy import optimize_policy
from next_best_action.timing import add_timing_status


def test_hidden_truth_cannot_change_deployable_policy(small_setup):
    policy, offers, bundle, frame = small_setup
    candidates = build_candidates(frame, policy, offers, evaluator_truth=bundle.evaluator_truth)
    selected = optimize_policy(candidates, policy)[["customer_id", "action"]].sort_values(
        "customer_id"
    )

    mutated_truth = bundle.evaluator_truth.copy()
    truth_columns = [column for column in mutated_truth if column.startswith("true_uplift_")]
    mutated_truth.loc[:, truth_columns] = mutated_truth[truth_columns] * -10
    mutated_bundle = replace(bundle, evaluator_truth=mutated_truth)
    deployable = add_timing_status(build_decision_frame(mutated_bundle), policy)
    mutated_candidates = build_candidates(
        deployable,
        policy,
        offers,
        evaluator_truth=mutated_bundle.evaluator_truth,
    )
    mutated_selected = optimize_policy(mutated_candidates, policy)[
        ["customer_id", "action"]
    ].sort_values("customer_id")
    pd.testing.assert_frame_equal(
        selected.reset_index(drop=True), mutated_selected.reset_index(drop=True)
    )
