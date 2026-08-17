from dataclasses import replace

import pandas as pd
import pytest

from next_best_action.contracts import build_decision_frame, validate_bundle


def test_decision_frame_excludes_evaluator_truth(small_setup):
    _, _, bundle, _ = small_setup
    frame = build_decision_frame(bundle)
    assert not any(column.startswith("true_") for column in frame.columns)
    assert len(frame) == 500


def test_contract_rejects_duplicate_customer_ids(small_setup):
    _, _, bundle, _ = small_setup
    duplicated = pd.concat([bundle.clv_scores, bundle.clv_scores.iloc[[0]]], ignore_index=True)
    broken = replace(bundle, clv_scores=duplicated)
    with pytest.raises(ValueError, match="duplicate customer_id"):
        validate_bundle(broken)


@pytest.mark.parametrize(
    ("channel", "consent_column"),
    [("email", "email_consent"), ("push", "push_consent")],
)
def test_contract_rejects_preferred_channel_without_consent(
    small_setup,
    channel,
    consent_column,
):
    _, _, bundle, _ = small_setup
    customer_state = bundle.customer_state.copy()
    customer_state.loc[0, "preferred_owned_channel"] = channel
    customer_state.loc[0, consent_column] = False
    broken = replace(bundle, customer_state=customer_state)

    with pytest.raises(ValueError, match="requires matching channel consent"):
        validate_bundle(broken)
