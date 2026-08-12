from next_best_action.pipeline import run_pipeline


def test_pipeline_smoke(project_root):
    metadata = run_pipeline(project_root, customers=350, seed=11, write_outputs=False)
    assert metadata["customers"] == 350
    assert metadata["all_constraints_pass"] is True
    assert metadata["oracle_true_incremental_net_value"] >= metadata[
        "engine_true_incremental_net_value"
    ] - 1e-9
