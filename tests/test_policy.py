from next_best_action.candidates import build_candidates
from next_best_action.evaluation import constraint_summary, eligibility_summary
from next_best_action.policy import optimize_policy


def test_optimizer_respects_constraints(small_setup):
    policy, offers, bundle, frame = small_setup
    candidates = build_candidates(frame, policy, offers)
    selected = optimize_policy(candidates, policy)
    constraints = constraint_summary(selected, policy)
    eligibility = eligibility_summary(selected, frame, policy)
    assert constraints["within_limit"].all()
    assert eligibility["within_limit"].all()
    assert not selected["customer_id"].duplicated().any()


def test_optimizer_never_needs_negative_value_action(small_setup):
    policy, offers, bundle, frame = small_setup
    candidates = build_candidates(frame, policy, offers)
    selected = optimize_policy(candidates, policy)
    assert (selected["predicted_net_value"] > 0).all()


def test_eligibility_audit_detects_revoked_channel_consent(small_setup):
    policy, offers, _, frame = small_setup
    candidates = build_candidates(frame, policy, offers)
    selected = optimize_policy(candidates, policy)
    target = selected.iloc[0]
    broken_frame = frame.copy()
    consent_column = f"{target['channel']}_consent"
    broken_frame.loc[
        broken_frame["customer_id"] == target["customer_id"],
        consent_column,
    ] = False

    audit = eligibility_summary(selected, broken_frame, policy)
    violation = audit.loc[audit["guardrail"] == "channel_consent", "violations"].iat[0]
    assert violation == 1
