"""CLI da pipeline reproduzível."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable
from typing import Any

from . import __version__
from .acquisition import acquire_all
from .config import PROJECT_ROOT, ensure_directories
from .database import build_database
from .io import git_commit, read_json, utc_now, write_json
from .lfm2b import audit_lfm2b, normalize_lfm2b
from .lyrics_ambiguity_v011 import audit_lyrics_ambiguity_v011
from .lyrics_pilot import prepare_lyrics_pilot, run_lyrics_smoke
from .lyrics_pilot_v012 import prepare_supplemental_v012, run_supplemental_v012
from .lyrics_pilot_v013 import run_full_pilot_v013
from .matching import analyze_selection_bias, run_matching
from .reporting import generate_reports
from .revision_v011 import prepare_revision_v011
from .spotify import audit_spotify, normalize_spotify
from .validation_v011 import prepare_base_v011


def _print_lyrics_progress(done: int, total: int) -> None:
    if done % 10 == 0 or done == total:
        print(f"Smoke LRCLIB: {done}/{total}", file=sys.stderr, flush=True)


def _print_supplemental_progress(done: int, total: int) -> None:
    if done % 5 == 0 or done == total:
        print(f"Complementar LRCLIB v0.1.2: {done}/{total}", file=sys.stderr, flush=True)


def _print_full_lyrics_progress(done: int, total: int) -> None:
    print(f"Piloto completo LRCLIB v0.1.3: {done}/{total}", file=sys.stderr, flush=True)


def _print_embeddings_progress(done: int, total: int) -> None:
    if done % 640 == 0 or done == total:
        print(f"Chunks MiniLM v0.2: {done}/{total}", file=sys.stderr, flush=True)


def _print_modeling_progress(
    algorithm: str, block: str, variant: str, done: int, total: int
) -> None:
    print(
        f"Modelagem v0.3: {algorithm} / {block} / {variant} — fold {done}/{total}",
        file=sys.stderr,
        flush=True,
    )


def _print_recalibration_progress(
    analysis: str,
    algorithm: str,
    representation: str,
    done: int,
    total: int,
) -> None:
    print(
        f"Recalibração v0.3.1: {analysis} / {algorithm} / {representation} — fold {done}/{total}",
        file=sys.stderr,
        flush=True,
    )


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
    if command == "prepare-v011":
        return prepare_base_v011()
    if command == "revise-v011":
        return prepare_revision_v011()
    if command == "prepare-lyrics-pilot":
        return prepare_lyrics_pilot()
    if command == "audit-lyrics-ambiguity-v011":
        return audit_lyrics_ambiguity_v011()
    if command == "prepare-lyrics-supplemental-v012":
        result = prepare_supplemental_v012()
        return {key: value for key, value in result.items() if key not in {"sample", "smoke_final"}}
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
        "command",
        choices=[
            "acquire",
            "audit",
            "normalize",
            "match",
            "report",
            "prepare-v011",
            "revise-v011",
            "prepare-lyrics-pilot",
            "lyrics-pilot",
            "audit-lyrics-ambiguity-v011",
            "prepare-lyrics-supplemental-v012",
            "lyrics-pilot-supplemental-v012",
            "lyrics-pilot-full-v013",
            "lyrics-embeddings-v020",
            "modeling-pilot-v030",
            "modeling-recalibration-v031",
            "all",
        ],
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Máximo de composições do smoke test (0 a 100; padrão: 100).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida e mostra o plano do piloto sem realizar requisições de rede.",
    )
    arguments = parser.parse_args(argv)
    if arguments.command == "lyrics-pilot":
        progress = None if arguments.dry_run else _print_lyrics_progress
        summary = run_lyrics_smoke(
            limit=arguments.limit,
            dry_run=arguments.dry_run,
            progress=progress,
        )
    elif arguments.command == "lyrics-pilot-supplemental-v012":
        if arguments.limit != 100:
            parser.error("--limit não se aplica ao teste complementar v0.1.2")
        progress = None if arguments.dry_run else _print_supplemental_progress
        summary = run_supplemental_v012(
            dry_run=arguments.dry_run,
            progress=progress,
        )
    elif arguments.command == "lyrics-pilot-full-v013":
        if arguments.limit != 100:
            parser.error("--limit não se aplica ao piloto completo v0.1.3")
        progress = None if arguments.dry_run else _print_full_lyrics_progress
        summary = run_full_pilot_v013(
            dry_run=arguments.dry_run,
            progress=progress,
        )
    elif arguments.command == "lyrics-embeddings-v020":
        if arguments.dry_run or arguments.limit != 100:
            parser.error("--limit e --dry-run não se aplicam ao piloto de embeddings v0.2")
        from .lyrics_embeddings_v020 import run_lyrics_embeddings_v020

        summary = run_lyrics_embeddings_v020(progress=_print_embeddings_progress)
    elif arguments.command == "modeling-pilot-v030":
        if arguments.dry_run or arguments.limit != 100:
            parser.error("--limit e --dry-run não se aplicam à modelagem piloto v0.3")
        from .modeling_pilot_v030 import run_modeling_pilot_v030

        summary = run_modeling_pilot_v030(progress=_print_modeling_progress)
    elif arguments.command == "modeling-recalibration-v031":
        if arguments.dry_run or arguments.limit != 100:
            parser.error("--limit e --dry-run não se aplicam à recalibração v0.3.1")
        from .modeling_recalibration_v031 import run_modeling_recalibration_v031

        summary = run_modeling_recalibration_v031(progress=_print_recalibration_progress)
    else:
        if arguments.dry_run or arguments.limit != 100:
            parser.error("--limit e --dry-run são exclusivos do comando lyrics-pilot")
        summary = _run_command(arguments.command)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0 if not summary.get("failures") else 1


if __name__ == "__main__":
    raise SystemExit(main())
