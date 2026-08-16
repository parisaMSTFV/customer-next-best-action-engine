from next_best_action.pipeline import run_pipeline


def test_pipeline_smoke(project_root):
    metadata = run_pipeline(project_root, customers=350, seed=11, write_outputs=False)
    assert metadata["customers"] == 350
    assert metadata["all_constraints_pass"] is True
    assert (
        metadata["oracle_true_incremental_net_value"]
        >= metadata["engine_true_incremental_net_value"] - 1e-9
    )


def test_pipeline_rejects_synthetic_options_with_external_inputs(project_root):
    fixture = project_root / "data" / "fixtures" / "upstream-v1"
    try:
        run_pipeline(project_root, customers=10, input_dir=fixture, write_outputs=False)
    except ValueError as exc:
        assert "customers and seed" in str(exc)
    else:
        raise AssertionError("Expected external-input option validation")


def test_synthetic_output_can_be_separated_from_repository(project_root, tmp_path):
    output = tmp_path / "run"
    run_pipeline(project_root, customers=350, seed=11, output_dir=output)

    assert (output / "reports" / "run_summary.md").exists()
    assert (output / "data" / "generated" / "customer_state.csv").exists()
