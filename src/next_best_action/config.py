from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML configuration file."""
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def load_configs(project_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load policy and offer configuration."""
    policy = load_yaml(project_root / "configs" / "policy.yml")
    offers = load_yaml(project_root / "configs" / "offers.yml")
    return policy, offers
