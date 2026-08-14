import json
import shutil

import pytest

from next_best_action.inputs import load_external_bundle
from next_best_action.pipeline import run_pipeline


def test_versioned_fixture_runs_without_evaluator_truth(project_root, tmp_path):
    fixture = project_root / "data" / "fixtures" / "upstream-v1"
    bundle, manifest = load_external_bundle(fixture)

    assert len(bundle.customer_state) == 8
    assert bundle.evaluator_truth is None
    assert manifest["contract_version"] == "1.0"

    output = tmp_path / "external-output"
    metadata = run_pipeline(project_root, input_dir=fixture, output_dir=output)

    assert metadata["input_mode"] == "external"
    assert metadata["customers"] == 8
    assert metadata["all_constraints_pass"] is True
    assert metadata["engine_contacts"] > 0
    assert (output / "decisions.csv").is_file()
    assert (output / "run_summary.md").is_file()
    assert "true_incremental" not in (output / "run_summary.md").read_text(encoding="utf-8")


def test_manifest_checksum_rejects_changed_artifact(project_root, tmp_path):
    source = project_root / "data" / "fixtures" / "upstream-v1"
    fixture = tmp_path / "tampered"
    shutil.copytree(source, fixture)
    path = fixture / "uplift_scores.csv"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Checksum mismatch for uplift_scores"):
        load_external_bundle(fixture)


def test_manifest_requires_supported_contract(project_root, tmp_path):
    source = project_root / "data" / "fixtures" / "upstream-v1"
    fixture = tmp_path / "future-contract"
    shutil.copytree(source, fixture)
    manifest_path = fixture / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["contract_version"] = "2.0"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported upstream contract version"):
        load_external_bundle(fixture)
