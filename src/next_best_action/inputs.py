from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from next_best_action.contracts import REQUIRED_COLUMNS, validate_bundle

CONTRACT_VERSION = "1.0"


@dataclass(frozen=True)
class ExternalBundle:
    """Validated deployable inputs loaded from versioned upstream artifacts."""

    customer_state: pd.DataFrame
    segmentation_scores: pd.DataFrame
    clv_scores: pd.DataFrame
    churn_scores: pd.DataFrame
    purchase_scores: pd.DataFrame
    uplift_scores: pd.DataFrame
    evaluator_truth: None = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_artifact(input_dir: Path, relative_path: str) -> Path:
    path = (input_dir / relative_path).resolve()
    if not path.is_relative_to(input_dir):
        raise ValueError(f"Artifact path escapes input directory: {relative_path}")
    if not path.is_file():
        raise FileNotFoundError(f"Missing upstream artifact: {path}")
    return path


def _coerce_boolean(frame: pd.DataFrame, column: str, artifact: str) -> None:
    if column not in frame:
        return
    if pd.api.types.is_bool_dtype(frame[column]):
        return
    normalized = frame[column].astype(str).str.strip().str.lower()
    mapping = {"true": True, "false": False, "1": True, "0": False}
    invalid = sorted(set(normalized) - set(mapping))
    if invalid:
        raise ValueError(f"{artifact}.{column} contains invalid booleans: {invalid}")
    frame[column] = normalized.map(mapping).astype(bool)


def load_external_bundle(input_dir: str | Path) -> tuple[ExternalBundle, dict[str, Any]]:
    """Load six standardized score artifacts and verify their version manifest."""
    root = Path(input_dir).resolve()
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing upstream manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("contract_version") != CONTRACT_VERSION:
        raise ValueError(
            "Unsupported upstream contract version: "
            f"{manifest.get('contract_version')!r}; expected {CONTRACT_VERSION!r}"
        )

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("Manifest must contain an artifacts object")
    missing = set(REQUIRED_COLUMNS) - set(artifacts)
    extra = set(artifacts) - set(REQUIRED_COLUMNS)
    if missing or extra:
        raise ValueError(
            f"Manifest artifact mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )

    frames: dict[str, pd.DataFrame] = {}
    for name in REQUIRED_COLUMNS:
        entry = artifacts[name]
        if not isinstance(entry, dict):
            raise ValueError(f"Manifest entry {name!r} must be an object")
        for field in ("path", "producer", "artifact_version", "sha256"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise ValueError(f"Manifest entry {name!r} requires {field!r}")
        path = _resolve_artifact(root, entry["path"])
        actual_checksum = _sha256(path)
        if actual_checksum != entry["sha256"].lower():
            raise ValueError(
                f"Checksum mismatch for {name}: expected {entry['sha256']}, got {actual_checksum}"
            )
        frames[name] = pd.read_csv(path, dtype={"customer_id": "string"})

    for artifact, columns in {
        "customer_state": ["email_consent", "push_consent", "call_consent"],
        "clv_scores": ["high_uncertainty"],
    }.items():
        for column in columns:
            _coerce_boolean(frames[artifact], column, artifact)

    bundle = ExternalBundle(**frames)
    validate_bundle(bundle)
    manifest_score_date = manifest.get("score_date")
    if not isinstance(manifest_score_date, str) or not manifest_score_date:
        raise ValueError("Manifest requires a score_date")
    score_dates = set(bundle.churn_scores["score_date"].astype(str))
    if score_dates != {manifest_score_date}:
        raise ValueError(
            "churn_scores.score_date must match the single manifest score_date; "
            f"found {sorted(score_dates)}"
        )
    return bundle, manifest
