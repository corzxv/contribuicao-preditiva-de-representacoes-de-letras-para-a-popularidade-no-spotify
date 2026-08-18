"""Aquisição controlada das fontes e manifesto de proveniência."""

from __future__ import annotations

import json
import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from .config import ensure_directories, load_sources_config, project_path
from .io import read_json, sha256_file, update_manifest, utc_now

USER_AGENT = "tcc-popularidade-musical/0.1 (academic reproducibility pipeline)"


def _download(url: str, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return "reused_existing"
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as target:
        shutil.copyfileobj(response, target, length=8 * 1024 * 1024)
    temporary.replace(destination)
    return "downloaded"


def _extract_spotify(archive: Path, expected: Path) -> str:
    if expected.exists() and expected.stat().st_size > 0:
        return "reused_existing"
    with zipfile.ZipFile(archive) as bundle:
        csv_members = [
            member for member in bundle.infolist() if member.filename.lower().endswith(".csv")
        ]
        if not csv_members:
            raise FileNotFoundError("O arquivo Kaggle não contém CSV.")
        preferred = next(
            (member for member in csv_members if Path(member.filename).name == expected.name),
            csv_members[0] if len(csv_members) == 1 else None,
        )
        if preferred is None:
            names = ", ".join(member.filename for member in csv_members)
            raise RuntimeError(f"Mais de um CSV no ZIP e nenhum é {expected.name}: {names}")
        expected.parent.mkdir(parents=True, exist_ok=True)
        with bundle.open(preferred) as source, expected.open("wb") as target:
            shutil.copyfileobj(source, target)
    return f"extracted:{preferred.filename}"


def _record(name: str, source: dict[str, Any], path: Path, method: str) -> dict[str, Any]:
    existing = read_json("data/raw/manifest.json", {"sources": {}}).get("sources", {}).get(name, {})
    metadata = {
        **existing,
        "logical_name": source["logical_name"],
        "source_page": source["page_url"],
        "identifier": source["identifier"],
        "local_path": str(path.relative_to(project_path("."))).replace("\\", "/"),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "obtained_or_verified_at": utc_now(),
        "license_observed": source.get("license_observed", "not_verified"),
        "license_url": source.get("license_url"),
        "verification_status": "file_present_hash_computed",
        "acquisition_method": method,
    }
    metadata.setdefault("schema_observed", None)
    metadata.setdefault("record_count", None)
    update_manifest(name, metadata)
    return metadata


def acquire_spotify(source: dict[str, Any]) -> dict[str, Any]:
    target = project_path(source["local_path"])
    archive = project_path(source["archive_path"])
    if target.exists():
        method = "reused_existing_configured_file"
    else:
        download_method = _download(source["download_url"], archive)
        extraction_method = _extract_spotify(archive, target)
        method = f"public_kaggle_api:{download_method};{extraction_method}"
    return _record("spotify", source, target, method)


def acquire_lfm2b(source: dict[str, Any]) -> dict[str, Any]:
    target = project_path(source["local_path"])
    method = _download(source["download_url"], target)
    return _record("lfm2b", source, target, f"zenodo_direct:{method}")


def acquire_all(continue_on_error: bool = True) -> dict[str, Any]:
    ensure_directories()
    sources = load_sources_config()
    results: dict[str, Any] = {}
    for name, function in (("spotify", acquire_spotify), ("lfm2b", acquire_lfm2b)):
        try:
            results[name] = {"status": "available", "metadata": function(sources[name])}
        except Exception as exc:  # noqa: BLE001 - bloqueios externos devem ser registrados
            results[name] = {
                "status": "blocked",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "expected_path": sources[name]["local_path"],
                "source_page": sources[name]["page_url"],
            }
            if not continue_on_error:
                raise
    report = project_path("reports/acquisition_status.json")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    return results
