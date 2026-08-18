"""CLI da pipeline reproduzível."""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Callable
from typing import Any

from . import __version__
from .acquisition import acquire_all
from .config import PROJECT_ROOT, ensure_directories
from .database import build_database
from .io import git_commit, read_json, utc_now, write_json
from .lfm2b import audit_lfm2b, normalize_lfm2b
from .matching import analyze_selection_bias, run_matching
from .reporting import generate_reports
from .spotify import audit_spotify, normalize_spotify


def _products() -> dict[str, dict[str, Any]]:
    paths = [
        "data/interim/spotify_normalized.parquet",
        "data/interim/lfm2b_normalized.parquet",
        "data/processed/spotify_tracks.parquet",
        "data/processed/lfm2b_tracks.parquet",
        "data/processed/spotify_lfm_matches.parquet",
        "data/processed/spotify_lfm_ambiguous.parquet",
        "data/processed/spotify_lfm_candidates_review.parquet",
        "data/processed/spotify_lfm_unmatched.parquet",
        "data/processed/modeling_base_lfm_v0_1.parquet",
        "data/processed/music_tcc.duckdb",
        "reports/data_audit.md",
        "reports/matching_report.md",
    ]
    products = {}
    for relative in paths:
        path = PROJECT_ROOT / relative
        products[relative] = {
            "status": "available" if path.exists() else "missing",
            "size_bytes": path.stat().st_size if path.exists() else None,
        }
    return products


def _run_stage(
    name: str, function: Callable[[], Any], stages: dict[str, Any], failures: list[dict[str, str]]
) -> Any:
    started = time.perf_counter()
    try:
        result = function()
        stages[name] = {
            "status": "completed",
            "duration_seconds": round(time.perf_counter() - started, 6),
            "result": result,
        }
        return result
    except Exception as exc:  # noqa: BLE001 - resumo deve registrar e continuar etapas independentes
        failure = {"stage": name, "type": type(exc).__name__, "message": str(exc)}
        failures.append(failure)
        stages[name] = {
            "status": "failed_or_blocked",
            "duration_seconds": round(time.perf_counter() - started, 6),
            "error": failure,
        }
        return None


def _write_run_summary(
    stages: dict[str, Any], failures: list[dict[str, str]], started: float
) -> dict[str, Any]:
    manifest = read_json("data/raw/manifest.json", {"sources": {}})
    records_by_stage: dict[str, Any] = {}
    for name, value in stages.items():
        result = value.get("result")
        if not isinstance(result, dict):
            records_by_stage[name] = None
            continue
        records_by_stage[name] = (
            result.get("rows")
            or result.get("observed", {}).get("rows")
            or result.get("spotify_rows")
            or result.get("valid_rows")
        )
        if "unique_spotify_tracks_by_candidate_status" in result:
            records_by_stage[f"{name}_by_status"] = result[
                "unique_spotify_tracks_by_candidate_status"
            ]
    summary = {
        "timestamp": utc_now(),
        "code_version": __version__,
        "git_commit": git_commit(),
        "input_hashes": {
            name: source.get("sha256") for name, source in manifest.get("sources", {}).items()
        },
        "records_by_stage": records_by_stage,
        "duration_seconds": round(time.perf_counter() - started, 6),
        "stages": stages,
        "warnings": [
            "Popularidade Spotify é observada no snapshot da fonte e não mede necessariamente sucesso futuro.",
            "genius_lyrics_views, lfm_playcount e spotify_popularity são métricas distintas.",
            "Matches fuzzy nunca são aceitos automaticamente.",
        ],
        "failures": failures,
        "status": "complete" if not failures else "partial_with_blockers",
        "products": _products(),
        "normalization_version": "v0.1.0",
        "matching_version": "v0.1.0",
    }
    write_json("reports/run_summary.json", summary)
    return summary


def run_all() -> dict[str, Any]:
    ensure_directories()
    started = time.perf_counter()
    stages: dict[str, Any] = {}
    failures: list[dict[str, str]] = []
    _run_stage("acquire", acquire_all, stages, failures)
    spotify = _run_stage("normalize_spotify", normalize_spotify, stages, failures)
    lfm = _run_stage("normalize_lfm2b", normalize_lfm2b, stages, failures)
    if spotify is not None:
        _run_stage("audit_spotify", audit_spotify, stages, failures)
    if lfm is not None:
        _run_stage("audit_lfm2b", audit_lfm2b, stages, failures)
    if spotify is not None and lfm is not None:
        matched = _run_stage("match", run_matching, stages, failures)
        if matched is not None:
            _run_stage("selection_bias", analyze_selection_bias, stages, failures)
    _run_stage("database", build_database, stages, failures)
    _run_stage("report", generate_reports, stages, failures)
    return _write_run_summary(stages, failures, started)


def _run_command(command: str) -> dict[str, Any]:
    ensure_directories()
    if command == "all":
        return run_all()
    started = time.perf_counter()
    stages: dict[str, Any] = {}
    failures: list[dict[str, str]] = []
    if command == "acquire":
        _run_stage("acquire", acquire_all, stages, failures)
    elif command == "normalize":
        _run_stage("normalize_spotify", normalize_spotify, stages, failures)
        _run_stage("normalize_lfm2b", normalize_lfm2b, stages, failures)
    elif command == "audit":
        _run_stage("audit_spotify", audit_spotify, stages, failures)
        _run_stage("audit_lfm2b", audit_lfm2b, stages, failures)
    elif command == "match":
        matched = _run_stage("match", run_matching, stages, failures)
        if matched is not None:
            _run_stage("selection_bias", analyze_selection_bias, stages, failures)
        _run_stage("database", build_database, stages, failures)
    elif command == "report":
        _run_stage("database", build_database, stages, failures)
        _run_stage("report", generate_reports, stages, failures)
    else:
        raise ValueError(command)
    return _write_run_summary(stages, failures, started)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["acquire", "audit", "normalize", "match", "report", "all"]
    )
    arguments = parser.parse_args(argv)
    summary = _run_command(arguments.command)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0 if not summary["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
