"""Carregamento de configuração e caminhos do projeto."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(os.getenv("TCC_PROJECT_ROOT", Path(__file__).resolve().parents[2])).resolve()


def load_yaml(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_pipeline_config() -> dict[str, Any]:
    config = load_yaml("configs/pipeline.yaml")
    config["root"] = str(PROJECT_ROOT)
    return config


def load_sources_config() -> dict[str, Any]:
    local = PROJECT_ROOT / "configs/data_sources.yaml"
    source = local if local.exists() else PROJECT_ROOT / "configs/data_sources.example.yaml"
    config = load_yaml(source)
    env_overrides = {
        "spotify": os.getenv("TCC_SPOTIFY_PATH"),
        "lfm2b": os.getenv("TCC_LFM2B_PATH"),
    }
    for name, override in env_overrides.items():
        if override:
            config[name]["local_path"] = override
    return config


def project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def ensure_directories() -> None:
    config = load_pipeline_config()
    for value in config["paths"].values():
        project_path(value).mkdir(parents=True, exist_ok=True)
    for value in ("reports/figures", "reports/tables", "data/raw/spotify", "data/raw/lfm2b"):
        project_path(value).mkdir(parents=True, exist_ok=True)
