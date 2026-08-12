from next_best_action.candidates import build_candidates
from next_best_action.evaluation import constraint_summary
from next_best_action.policy import optimize_policy


def test_optimizer_respects_constraints(small_setup):
    policy, offers, bundle, frame = small_setup
    candidates = build_candidates(frame, policy, offers, evaluator_truth=bundle.evaluator_truth)
    selected = optimize_policy(candidates, policy)
    constraints = constraint_summary(selected, policy)
    assert constraints["within_limit"].all()
    assert not selected["customer_id"].duplicated().any()


def test_optimizer_never_needs_negative_value_action(small_setup):
    policy, offers, bundle, frame = small_setup
    candidates = build_candidates(frame, policy, offers, evaluator_truth=bundle.evaluator_truth)
    selected = optimize_policy(candidates, policy)
    assert (selected["predicted_net_value"] > -1e-9).all()
