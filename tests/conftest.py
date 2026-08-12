from pathlib import Path

import pytest

from next_best_action.config import load_configs
from next_best_action.contracts import build_decision_frame
from next_best_action.simulation import generate_synthetic_bundle
from next_best_action.timing import add_timing_status


@pytest.fixture()
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture()
def small_setup(project_root: Path):
    policy, offers = load_configs(project_root)
    bundle = generate_synthetic_bundle(500, seed=7, score_date=str(policy["score_date"]))
    frame = add_timing_status(build_decision_frame(bundle), policy)
    return policy, offers, bundle, frame
