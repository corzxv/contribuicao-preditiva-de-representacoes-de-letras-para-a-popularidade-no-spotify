"""Utilidades de I/O rastreável e idempotente."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT, project_path


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def sha256_file(path: str | Path, block_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while block := handle.read(block_size):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: str | Path, payload: Any) -> None:
    destination = project_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=destination.parent, delete=False, suffix=".tmp"
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
        temporary = Path(handle.name)
    os.replace(temporary, destination)


def read_json(path: str | Path, default: Any = None) -> Any:
    source = project_path(path)
    if not source.exists():
        return default
    with source.open(encoding="utf-8") as handle:
        return json.load(handle)


def update_manifest(logical_name: str, metadata: dict[str, Any]) -> dict[str, Any]:
    manifest_path = project_path("data/raw/manifest.json")
    manifest = read_json(manifest_path, {"manifest_version": "0.1", "sources": {}})
    manifest["updated_at"] = utc_now()
    manifest["sources"][logical_name] = metadata
    write_json(manifest_path, manifest)
    return manifest


def git_commit() -> str | None:
    try:
        result = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={PROJECT_ROOT.as_posix()}",
                "rev-parse",
                "HEAD",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
