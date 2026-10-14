"""Coleta LRCLIB escalada v0.4, privada, retomável e sem target do holdout."""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import polars as pl

from .config import load_yaml, project_path
from .final_study_v040 import (
    DEFAULT_CONFIG_PATH,
    EXPECTED_FROZEN_HASHES,
    FORBIDDEN_SAMPLING_COLUMNS,
    PROTOCOL_VERSION,
    SCALE_VERSION,
    _git_private_files,
)
from .io import read_json, sha256_file, utc_now, write_json
from .lyrics_pilot import VERSION_FLAGS, LRCLIBClient, _atomic_write_frame, _write_text
from .lyrics_pilot_v012 import ACCEPTED_STATUSES, classify_cached_composition_v012
from .lyrics_pilot_v013 import circuit_breaker_reason, validate_lrclib_envelope

COMPATIBLE_RAW_CACHE_VERSIONS = {"v0.1", "v0.1.3", "v0.4"}
PUBLIC_FORBIDDEN_MARKERS = (
    "plainLyrics",
    "syncedLyrics",
    "lyrics_sha256",
    "selected_strict_text_sha256",
    "selected_candidate_key_sha256",
    "data/raw/lyrics_private",
    "data/derived/private_final_study",
)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _cache_path(directory: Path, composition_key: str) -> Path:
    return directory / f"{_sha256(composition_key)}.json"


def _expected_request_parameters(query: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    shared = {
        "artist_name": query.get("artist_name_query"),
        "track_name": query.get("track_name_query"),
        "album_name": query.get("album_name_query"),
    }
    return {
        "/api/get": {**shared, "duration": query.get("duration_seconds")},
        "/api/search": shared,
    }


def cache_is_compatible(query: Mapping[str, Any], envelope: Mapping[str, Any]) -> bool:
    """Aceita cache legado apenas com chave, schema e consulta exatamente compatíveis."""

    try:
        validate_lrclib_envelope(envelope)
    except (ValueError, TypeError):
        return False
    if envelope.get("cache_version") not in COMPATIBLE_RAW_CACHE_VERSIONS:
        return False
    key = str(query["composition_key"])
    if envelope.get("composition_key") != key or envelope.get("cache_key") != _sha256(key):
        return False
    requests = {
        str(request.get("endpoint")): request
        for request in envelope.get("requests", [])
        if isinstance(request, dict)
    }
    expected = _expected_request_parameters(query)
    for endpoint, parameters in expected.items():
        observed = requests.get(endpoint, {}).get("parameters")
        if not isinstance(observed, dict):
            return False
        if set(observed) != set(parameters):
            return False
        for name, value in parameters.items():
            actual = observed.get(name)
            if name == "duration" and value is not None and actual is not None:
                if abs(float(value) - float(actual)) > 1e-9:
                    return False
            elif actual != value:
                return False
    return True


def locate_compatible_cache(
    query: Mapping[str, Any], current_dir: Path, legacy_dir: Path
) -> tuple[dict[str, Any] | None, str | None]:
    key = str(query["composition_key"])
    for label, directory in (("current", current_dir), ("legacy", legacy_dir)):
        path = _cache_path(directory, key)
        if not path.exists():
            continue
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if cache_is_compatible(query, envelope):
            return envelope, label
    return None, None


def activate_reserve_batches(
    accepted_main: int,
    accepted_by_batch: Mapping[int, int],
    *,
    threshold: int = 10000,
    maximum_batches: int = 4,
) -> list[int]:
    """Ativa lotes completos sequencialmente; nunca seleciona reposições individuais."""

    if accepted_main >= threshold:
        return []
    activated: list[int] = []
    accepted = accepted_main
    for batch in range(1, maximum_batches + 1):
        activated.append(batch)
        accepted += int(accepted_by_batch.get(batch, 0))
        if accepted >= threshold:
            break
    return activated


def _read_private_inputs(config: Mapping[str, Any]) -> dict[str, pl.DataFrame]:
    private = config["private_outputs"]
    cohort = pl.read_parquet(project_path(private["cohort"]))
    reserve = pl.read_parquet(project_path(private["reserve"]))
    lookup = pl.read_parquet(project_path(private["lookup"]))
    if cohort.height != 14000 or reserve.height != 2000 or lookup.height != 16000:
        raise AssertionError("Cardinalidade dos artefatos privados de amostragem divergente.")
    if FORBIDDEN_SAMPLING_COLUMNS & set(cohort.columns):
        raise AssertionError("Coorte privada contém target ou proxy proibido.")
    if FORBIDDEN_SAMPLING_COLUMNS & set(reserve.columns):
        raise AssertionError("Reserva privada contém target ou proxy proibido.")
    if FORBIDDEN_SAMPLING_COLUMNS & set(lookup.columns):
        raise AssertionError("Lookup privado contém target ou proxy proibido.")
    cohort_keys = set(cohort.get_column("composition_key"))
    reserve_keys = set(reserve.get_column("composition_key"))
    if cohort_keys & reserve_keys:
        raise AssertionError("Coorte e reserva se sobrepõem.")
    if set(lookup.get_column("composition_key")) != cohort_keys | reserve_keys:
        raise AssertionError("Lookup não corresponde à coorte e reserva congeladas.")
    return {"cohort": cohort, "reserve": reserve, "lookup": lookup}


def collection_preflight_v040(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    inputs = _read_private_inputs(config)
    protocol = read_json(config["public_outputs"]["protocol_summary"])
    if not isinstance(protocol, dict) or not str(protocol.get("status", "")).startswith(
        "protocol_prepared"
    ):
        raise AssertionError("Resumo do protocolo congelado ausente.")
    if (
        sha256_file(project_path(config["private_outputs"]["cohort"]))
        != protocol["private_artifact_hashes"]["cohort_sha256"]
    ):
        raise AssertionError("Hash da coorte principal divergiu.")
    if (
        sha256_file(project_path(config["private_outputs"]["reserve"]))
        != protocol["private_artifact_hashes"]["reserve_sha256"]
    ):
        raise AssertionError("Hash da reserva divergiu.")
    for path, expected in EXPECTED_FROZEN_HASHES.items():
        if sha256_file(project_path(path)) != expected:
            raise AssertionError(f"Artefato congelado divergiu: {Path(path).name}")
    seal = read_json(config["private_outputs"]["precollection_seal"])
    if not isinstance(seal, dict) or seal.get("checkpoint_tag") != "final-study-protocol-v1.0":
        raise AssertionError("Selo pré-coleta ausente ou inválido.")
    private_git = _git_private_files()
    if private_git["tracked"] or private_git["staged"]:
        raise AssertionError("Há arquivo privado tracked ou staged.")
    return {
        **inputs,
        "protocol": protocol,
        "seal": seal,
        "holdout_target_loaded": False,
        "private_git": private_git,
    }


def _save_seal_first_request(config: Mapping[str, Any]) -> str:
    path = config["private_outputs"]["precollection_seal"]
    seal = read_json(path)
    if not isinstance(seal, dict):
        raise AssertionError("Selo pré-coleta inválido.")
    value = seal.get("first_request_at") or utc_now()
    seal["first_request_at"] = value
    write_json(path, seal)
    return str(value)


def _breaker_config(collection: Mapping[str, Any]) -> dict[str, Any]:
    return {"circuit_breaker": collection["circuit_breaker"], "lrclib": collection}


def _current_run_circuit_breaker_reason(
    recent_network_statuses: list[str],
    *,
    source: str,
    status: str,
    envelope: Mapping[str, Any],
    collection: Mapping[str, Any],
) -> str | None:
    """Evaluate the breaker only for network requests made in this process."""
    if source != "network":
        return None
    recent_network_statuses.append(status)
    return circuit_breaker_reason(
        recent_network_statuses,
        envelope,
        _breaker_config(collection),
    )


def _write_progress(
    config: Mapping[str, Any],
    *,
    phase: str,
    processed: int,
    planned: int,
    source_counts: Counter[str],
    status_counts: Counter[str],
    started: float,
    breaker: str | None = None,
) -> None:
    write_json(
        config["private_outputs"]["collection_progress"],
        {
            "status": "stopped_by_circuit_breaker" if breaker else "running",
            "phase": phase,
            "processed": processed,
            "planned": planned,
            "cache_sources": dict(sorted(source_counts.items())),
            "status_counts": dict(sorted(status_counts.items())),
            "elapsed_seconds": time.perf_counter() - started,
            "circuit_breaker_reason": breaker,
            "updated_at": utc_now(),
        },
    )


def _collect_queries(
    queries: pl.DataFrame,
    config: Mapping[str, Any],
    *,
    phase: str,
    client: LRCLIBClient,
    progress: Callable[[str, int, int], None] | None,
) -> dict[str, Any]:
    collection = config["collection"]
    current_dir = project_path(collection["cache_dir"])
    legacy_dir = project_path(config["inputs"]["legacy_cache"])
    current_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    source_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    recent_network_statuses: list[str] = []
    queried_current = 0
    first_request_at: str | None = None
    checkpoint = int(collection["checkpoint_every"])
    ordered = queries.sort(["split", "sampling_order_within_split"])
    for processed, query in enumerate(ordered.iter_rows(named=True), 1):
        envelope, source = locate_compatible_cache(query, current_dir, legacy_dir)
        if envelope is None:
            if first_request_at is None:
                first_request_at = _save_seal_first_request(config)
            envelope = client.lookup(query)
            validate_lrclib_envelope(envelope)
            source = "network"
            queried_current += 1
        source_counts[str(source)] += 1
        classified = classify_cached_composition_v012(
            query,
            envelope,
            duration_tolerance=float(collection["duration_tolerance_seconds"]),
        )
        status = str(classified["final_status"])
        status_counts[status] += 1
        reason = _current_run_circuit_breaker_reason(
            recent_network_statuses,
            source=str(source),
            status=status,
            envelope=envelope,
            collection=collection,
        )
        if processed % checkpoint == 0 or processed == ordered.height or reason:
            _write_progress(
                config,
                phase=phase,
                processed=processed,
                planned=ordered.height,
                source_counts=source_counts,
                status_counts=status_counts,
                started=started,
                breaker=reason,
            )
            if progress:
                progress(phase, processed, ordered.height)
        if reason:
            return {
                "status": "stopped_by_circuit_breaker",
                "reason": reason,
                "processed": processed,
                "planned": ordered.height,
                "cache_sources": dict(source_counts),
                "status_counts": dict(status_counts),
                "queried_current_run": queried_current,
                "duration_seconds": time.perf_counter() - started,
                "first_request_at": first_request_at,
            }
    return {
        "status": "complete",
        "processed": ordered.height,
        "planned": ordered.height,
        "cache_sources": dict(source_counts),
        "status_counts": dict(status_counts),
        "queried_current_run": queried_current,
        "duration_seconds": time.perf_counter() - started,
        "first_request_at": first_request_at,
    }


def _classify_queries(queries: pl.DataFrame, config: Mapping[str, Any]) -> pl.DataFrame:
    collection = config["collection"]
    current_dir = project_path(collection["cache_dir"])
    legacy_dir = project_path(config["inputs"]["legacy_cache"])
    rows: list[dict[str, Any]] = []
    for query in queries.sort(["split", "sampling_order_within_split"]).iter_rows(named=True):
        envelope, source = locate_compatible_cache(query, current_dir, legacy_dir)
        if envelope is None:
            raise AssertionError("Cache compatível ausente durante consolidação.")
        row = classify_cached_composition_v012(
            query,
            envelope,
            duration_tolerance=float(collection["duration_tolerance_seconds"]),
        )
        rows.append(
            {
                **row,
                "split": query["split"],
                "sampling_role": query["sampling_role"],
                "sampling_order_within_split": query["sampling_order_within_split"],
                "reserve_batch": query.get("reserve_batch"),
                "cache_source": source,
            }
        )
    return pl.DataFrame(rows)


def _aggregate_counts(frame: pl.DataFrame, fields: Sequence[str]) -> list[dict[str, Any]]:
    return frame.group_by(list(fields)).len().sort(list(fields)).to_dicts()


def _technical_metrics(results: pl.DataFrame) -> dict[str, Any]:
    return {
        "attempts": int(results.get_column("attempts").sum()),
        "retry_attempts": int(results.get_column("retry_attempts").sum()),
        "retryable_http_attempts": int(results.get_column("retryable_http_attempts").sum()),
        "technical_errors": results.get_column("technical_error").drop_nulls().len(),
        "http_status_counts": _aggregate_counts(results, ["http_status"]),
    }


def _collection_metrics(results: pl.DataFrame) -> dict[str, Any]:
    accepted = results.filter(pl.col("final_status").is_in(sorted(ACCEPTED_STATUSES)))
    return {
        "planned_and_processed": results.height,
        "accepted_total": accepted.height,
        "acceptance_rate": accepted.height / results.height,
        "accepted_by_split": {
            row["split"]: int(row["len"])
            for row in accepted.group_by("split").len().sort("split").to_dicts()
        },
        "processed_by_split": {
            row["split"]: int(row["len"])
            for row in results.group_by("split").len().sort("split").to_dicts()
        },
        "status_counts": _aggregate_counts(results, ["final_status"]),
        "status_by_split": _aggregate_counts(results, ["split", "final_status"]),
        "cache_sources": _aggregate_counts(results, ["cache_source"]),
        "technical": _technical_metrics(results),
    }


def _build_private_index(results: pl.DataFrame) -> pl.DataFrame:
    return results.filter(pl.col("final_status").is_in(sorted(ACCEPTED_STATUSES))).select(
        "composition_key",
        "representative_track_id",
        "split",
        "sampling_role",
        "reserve_batch",
        "selected_lrclib_id",
        "selected_candidate_key_sha256",
        "selected_strict_text_sha256",
        "final_status",
        "cache_source",
    )


def _lyrics_report(summary: Mapping[str, Any]) -> str:
    metrics = summary["collection"]
    rows = [[row["final_status"], row["len"]] for row in metrics["status_counts"]]
    status_table = "\n".join(
        [
            "| Status | N |",
            "|---|---:|",
            *[f"| {status} | {count} |" for status, count in rows],
        ]
    )
    return f"""# Coleta escalada de letras — v0.4

## Escopo

Foram processadas {metrics["planned_and_processed"]} composições da coorte congelada e dos lotes de reserva eventualmente ativados. O pipeline aplicou exclusivamente `accepted_exact_unique` e `accepted_exact_equivalent`. Nenhuma popularidade do holdout foi carregada ou descrita.

## Resultado

- Aceitas: {metrics["accepted_total"]} ({100 * metrics["acceptance_rate"]:.2f}%).
- Desenvolvimento: {metrics["accepted_by_split"].get("development_train", 0)} aceitas.
- Holdout: {metrics["accepted_by_split"].get("holdout_test", 0)} aceitas.
- Reserva ativada: {summary["reserve"]["used"]}.
- Lotes de reserva: {summary["reserve"]["activated_batches"]}.
- Caches legados reutilizados: {summary["network"]["legacy_caches_reused"]}.
- Caches v0.4 existentes/reutilizados: {summary["network"]["current_caches_reused"]}.
- Novas composições consultadas: {summary["network"]["new_compositions_queried"]}.
- Tentativas HTTP registradas: {metrics["technical"]["attempts"]}; retries: {metrics["technical"]["retry_attempts"]}; erros técnicos: {metrics["technical"]["technical_errors"]}.

## Status finais

{status_table}

Resultados individuais, candidatos, hashes, IDs e textos permanecem em área privada ignorada pelo Git. Nenhum texto ou trecho de letra aparece neste relatório.
"""


def audit_public_scale_outputs(paths: Sequence[str | Path]) -> dict[str, Any]:
    violations: list[str] = []
    for value in paths:
        path = project_path(value)
        if not path.exists() or path.suffix.lower() not in {".md", ".json", ".csv"}:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in PUBLIC_FORBIDDEN_MARKERS:
            if marker in text:
                violations.append(f"{path.name}:{marker}")
    if violations:
        raise AssertionError(f"Marcadores privados em artefatos públicos: {violations}")
    private = _git_private_files()
    if private["tracked"] or private["staged"]:
        raise AssertionError("Arquivos privados tracked ou staged.")
    return {"violations": 0, "private_tracked": 0, "private_staged": 0}


def run_lyrics_scale_v040(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    client: LRCLIBClient | None = None,
    progress: Callable[[str, int, int], None] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    config = load_yaml(config_path)
    preflight = collection_preflight_v040(config_path)
    lookup: pl.DataFrame = preflight["lookup"]
    main_queries = lookup.filter(pl.col("sampling_role") == "main")
    collection_config = config["collection"]
    active_client = client or LRCLIBClient(collection_config)
    main_run = _collect_queries(
        main_queries,
        config,
        phase="main",
        client=active_client,
        progress=progress,
    )
    if main_run["status"] != "complete":
        return main_run
    main_results = _classify_queries(main_queries, config)
    accepted_main = main_results.filter(
        pl.col("final_status").is_in(sorted(ACCEPTED_STATUSES))
    ).height
    threshold = int(config["sampling"]["minimum_accepted_before_reserve_stop"])
    activated: list[int] = []
    reserve_results: list[pl.DataFrame] = []
    reserve_runs: list[dict[str, Any]] = []
    accepted_total = accepted_main
    if accepted_total < threshold:
        for batch in range(1, 5):
            batch_queries = lookup.filter(
                (pl.col("sampling_role") == "reserve") & (pl.col("reserve_batch") == batch)
            )
            if batch_queries.height != 500:
                raise AssertionError("Lote de reserva não contém exatamente 500 composições.")
            run = _collect_queries(
                batch_queries,
                config,
                phase=f"reserve_batch_{batch}",
                client=active_client,
                progress=progress,
            )
            reserve_runs.append(run)
            if run["status"] != "complete":
                return run
            batch_results = _classify_queries(batch_queries, config)
            reserve_results.append(batch_results)
            activated.append(batch)
            accepted_total += batch_results.filter(
                pl.col("final_status").is_in(sorted(ACCEPTED_STATUSES))
            ).height
            if accepted_total >= threshold:
                break
    results = pl.concat([main_results, *reserve_results], how="diagonal_relaxed")
    sampling_fields = [
        "composition_key",
        "period",
        "year",
        "genre_sampling",
        "match_method",
        "version_profile",
        "has_any_version_flag",
        *VERSION_FLAGS,
    ]
    metadata = pl.concat([preflight["cohort"], preflight["reserve"]], how="diagonal_relaxed")
    results = results.join(
        metadata.select(sampling_fields), on="composition_key", how="left", validate="1:1"
    )
    _atomic_write_frame(results, config["private_outputs"]["collection_results"])
    index = _build_private_index(results)
    _atomic_write_frame(index, config["private_outputs"]["lyrics_index"])
    metrics = _collection_metrics(results)
    cache_counts = Counter(str(value) for value in results.get_column("cache_source").to_list())
    current_dir = project_path(collection_config["cache_dir"])
    v04_envelopes = []
    active_keys = set(results.get_column("composition_key"))
    for key in active_keys:
        path = _cache_path(current_dir, str(key))
        if path.exists():
            v04_envelopes.append(json.loads(path.read_text(encoding="utf-8")))
    current_attempts = sum(
        len(request.get("attempts", []))
        for envelope in v04_envelopes
        for request in envelope.get("requests", [])
    )
    current_retries = sum(
        max(len(request.get("attempts", [])) - 1, 0)
        for envelope in v04_envelopes
        for request in envelope.get("requests", [])
    )
    summary: dict[str, Any] = {
        "status": "collection_complete_embeddings_pending",
        "scale_version": SCALE_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "timestamp": utc_now(),
        "checkpoint_commit": preflight["seal"]["checkpoint_commit"],
        "checkpoint_tag": preflight["seal"]["checkpoint_tag"],
        "seed": int(config["seed"]),
        "holdout_target_loaded": False,
        "holdout_target_statistics_calculated": False,
        "models_trained": False,
        "collection": metrics,
        "reserve": {
            "used": bool(activated),
            "activated_batches": activated,
            "stopped_after_threshold": accepted_total >= threshold,
            "exhausted": activated == [1, 2, 3, 4],
        },
        "network": {
            "legacy_caches_reused": int(cache_counts.get("legacy", 0)),
            "current_caches_reused": int(cache_counts.get("current", 0)),
            "new_compositions_queried": len(v04_envelopes),
            "http_attempts_current_scale": current_attempts,
            "retry_attempts_current_scale": current_retries,
            "first_request_at": read_json(config["private_outputs"]["precollection_seal"])[
                "first_request_at"
            ],
        },
        "aggregates": {
            "status_by_period": _aggregate_counts(results, ["period", "final_status"]),
            "status_by_genre": _aggregate_counts(results, ["genre_sampling", "final_status"]),
            "status_by_match_method": _aggregate_counts(results, ["match_method", "final_status"]),
            "status_by_version_profile": _aggregate_counts(
                results, ["version_profile", "final_status"]
            ),
            "status_by_has_version_flag": _aggregate_counts(
                results, ["has_any_version_flag", "final_status"]
            ),
        },
        "duration_seconds": time.perf_counter() - started,
        "private_artifact_hashes": {
            "collection_results_sha256": sha256_file(
                project_path(config["private_outputs"]["collection_results"])
            ),
            "lyrics_index_sha256": sha256_file(
                project_path(config["private_outputs"]["lyrics_index"])
            ),
        },
        "frozen_hashes": {path: sha256_file(project_path(path)) for path in EXPECTED_FROZEN_HASHES},
        "privacy": _git_private_files(),
        "embeddings": None,
        "tests": {"status": "pending"},
    }
    if summary["frozen_hashes"] != EXPECTED_FROZEN_HASHES:
        raise AssertionError("Base ou split mudaram durante a coleta.")
    if summary["privacy"]["tracked"] or summary["privacy"]["staged"]:
        raise AssertionError("Arquivo privado tracked ou staged após a coleta.")
    _write_text(config["public_outputs"]["lyrics_report"], _lyrics_report(summary))
    write_json(config["public_outputs"]["scale_summary"], summary)
    audit_public_scale_outputs(
        [config["public_outputs"]["lyrics_report"], config["public_outputs"]["scale_summary"]]
    )
    return summary
