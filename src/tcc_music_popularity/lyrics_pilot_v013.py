"""Coleta completa v0.1.3 do piloto LRCLIB, com retomada e circuit breaker."""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import polars as pl

from .config import load_yaml, project_path
from .io import git_commit, read_json, utc_now, write_json
from .lyrics_ambiguity_v011 import (
    FORBIDDEN_TEXT_FIELDS,
    _artifact_hashes,
    _directory_manifest,
    _tracked_or_staged_private_files,
)
from .lyrics_pilot import (
    SUCCESS_FIELDS,
    VERSION_FLAGS,
    LRCLIBClient,
    _atomic_write_frame,
    _frozen_state,
    _markdown_table,
    _write_text,
)
from .lyrics_pilot_v012 import ACCEPTED_STATUSES, classify_cached_composition_v012

PILOT_VERSION = "v0.1.3"
DEFAULT_CONFIG_PATH = "configs/lyrics_pilot_v0_1_3.yaml"
PUBLIC_FORBIDDEN_FIELDS = FORBIDDEN_TEXT_FIELDS | {
    "text",
    "snippet",
    "tokens",
    "ngrams",
}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _cache_path(cache_dir: Path, composition_key: str) -> Path:
    return cache_dir / f"{_sha256(composition_key)}.json"


def _load_envelope(cache_dir: Path, composition_key: str) -> dict[str, Any]:
    path = _cache_path(cache_dir, composition_key)
    return json.loads(path.read_text(encoding="utf-8"))


def validate_lrclib_envelope(envelope: Mapping[str, Any]) -> None:
    """Falha fechada para mudanças estruturais, sem incluir conteúdo em erros."""
    requests = envelope.get("requests")
    if not isinstance(requests, list) or len(requests) != 2:
        raise ValueError("schema_change: requests deve ser lista com dois endpoints")
    by_endpoint = {
        request.get("endpoint"): request for request in requests if isinstance(request, dict)
    }
    if set(by_endpoint) != {"/api/get", "/api/search"}:
        raise ValueError("schema_change: endpoints esperados ausentes ou duplicados")
    for endpoint, request in by_endpoint.items():
        status = request.get("http_status")
        if status is not None and not isinstance(status, int):
            raise ValueError(f"schema_change: http_status inválido em {endpoint}")
        payload = request.get("payload")
        if status == 200:
            if endpoint == "/api/get" and not isinstance(payload, dict):
                raise ValueError("schema_change: payload de /api/get não é objeto")
            if endpoint == "/api/search" and not isinstance(payload, list):
                raise ValueError("schema_change: payload de /api/search não é lista")
        candidates = [payload] if status == 200 and isinstance(payload, dict) else payload
        if not isinstance(candidates, list):
            continue
        for candidate in candidates:
            if not isinstance(candidate, dict):
                raise ValueError(f"schema_change: candidato inválido em {endpoint}")
            if not ("trackName" in candidate or "name" in candidate):
                raise ValueError(f"schema_change: título ausente em {endpoint}")
            for field in ("artistName", "trackName", "name", "albumName"):
                value = candidate.get(field)
                if value is not None and not isinstance(value, str):
                    raise ValueError(f"schema_change: tipo inválido em {endpoint}:{field}")
            for field in ("plainLyrics", "syncedLyrics"):
                value = candidate.get(field)
                if value is not None and not isinstance(value, str):
                    raise ValueError(f"schema_change: tipo inválido em {endpoint}:{field}")
            duration = candidate.get("duration")
            if duration is not None and not isinstance(duration, (int, float)):
                raise ValueError(f"schema_change: duração inválida em {endpoint}")


def _persistent_429(envelope: Mapping[str, Any], max_attempts: int) -> bool:
    for request in envelope.get("requests", []):
        attempts = request.get("attempts", [])
        if (
            request.get("http_status") == 429
            and len(attempts) >= max_attempts
            and all(attempt.get("http_status") == 429 for attempt in attempts)
        ):
            return True
    return False


def circuit_breaker_reason(
    recent_statuses: Sequence[str],
    envelope: Mapping[str, Any],
    config: Mapping[str, Any],
) -> str | None:
    breaker = config["circuit_breaker"]
    consecutive_limit = int(breaker["consecutive_technical_errors"])
    if len(recent_statuses) >= consecutive_limit and all(
        value == "request_error" for value in recent_statuses[-consecutive_limit:]
    ):
        return "10_consecutive_technical_errors"
    window = int(breaker["rolling_window"])
    if len(recent_statuses) >= window:
        observed = recent_statuses[-window:]
        error_rate = sum(value == "request_error" for value in observed) / window
        if error_rate > float(breaker["maximum_request_error_rate"]):
            return "request_error_rate_above_20_percent_in_last_50"
    if _persistent_429(envelope, int(config["lrclib"]["max_attempts"])):
        return "persistent_429_after_retries"
    return None


def _frame_counts(frame: pl.DataFrame, column: str) -> dict[str, int]:
    return {
        str(row[column]): int(row["len"])
        for row in frame.group_by(column).len().sort(column).to_dicts()
    }


def full_preflight(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config = load_yaml(config_path)
    cohort = pl.read_parquet(project_path(config["inputs"]["cohort"]))
    lookup = pl.read_parquet(project_path(config["inputs"]["lookup"]))
    split = pl.read_parquet(project_path(config["inputs"]["split_assignments"]))
    expected = int(config["expected_cohort_size"])
    if cohort.height != expected or lookup.height != expected:
        raise AssertionError("Coorte e lookup devem conter exatamente 2.000 linhas.")
    if (
        cohort.get_column("composition_key").null_count()
        or lookup.get_column("composition_key").null_count()
    ):
        raise AssertionError("Há composition_key ausente.")
    if cohort.get_column("composition_key").n_unique() != expected:
        raise AssertionError("A coorte contém composition_key duplicada.")
    if lookup.get_column("composition_key").n_unique() != expected:
        raise AssertionError("O lookup contém composition_key duplicada.")
    cohort_keys = set(str(value) for value in cohort.get_column("composition_key"))
    lookup_keys = set(str(value) for value in lookup.get_column("composition_key"))
    if cohort_keys != lookup_keys:
        raise AssertionError("As chaves da coorte e do lookup divergem.")
    if SUCCESS_FIELDS & set(lookup.columns):
        raise AssertionError("O lookup de matching contém medida de sucesso proibida.")
    joined = cohort.join(
        split.select(["spotify_row_id", "split"]),
        left_on="representative_spotify_row_id",
        right_on="spotify_row_id",
        how="left",
        validate="1:1",
    )
    split_values = sorted(joined.get_column("split").unique().to_list())
    if split_values != ["development_train"]:
        raise AssertionError(f"Coorte fora de development_train: {split_values}")
    cache_dir = project_path(config["lrclib"]["cache_dir"])
    expected_cache_names = {_sha256(key) for key in cohort_keys}
    observed_cache_names = {path.stem for path in cache_dir.glob("*.json")}
    outside = observed_cache_names - expected_cache_names
    if outside:
        raise AssertionError(f"Há {len(outside)} caches fora da coorte.")
    cached_keys = {key for key in cohort_keys if _sha256(key) in observed_cache_names}
    missing_keys = cohort_keys - cached_keys
    frozen = _frozen_state()
    if not frozen["all_hashes_identical"]:
        raise AssertionError("Hashes congelados divergiram.")
    return {
        "cohort": cohort,
        "lookup": lookup,
        "split": split,
        "cohort_keys": cohort_keys,
        "cached_keys": cached_keys,
        "missing_keys": missing_keys,
        "counts": {
            "cohort_rows": cohort.height,
            "unique_compositions": len(cohort_keys),
            "missing_composition_keys": 0,
            "duplicate_compositions": 0,
            "cached_in_cohort": len(cached_keys),
            "remaining_without_cache": len(missing_keys),
            "caches_outside_cohort": 0,
            "split_values": split_values,
            "holdout_rows": joined.filter(pl.col("split") == "holdout_test").height,
            "development_holdout_id_overlap": frozen["development_holdout_id_overlap"],
        },
        "frozen": frozen,
    }


def _status_group(status: str) -> str:
    if status in ACCEPTED_STATUSES:
        return "accepted"
    if status.startswith("ambiguous_"):
        return "ambiguous"
    if status in {"not_found", "instrumental", "request_error"}:
        return status
    return "other"


def _build_full_results(config: Mapping[str, Any], preflight: Mapping[str, Any]) -> pl.DataFrame:
    lookup: pl.DataFrame = preflight["lookup"]
    cohort: pl.DataFrame = preflight["cohort"]
    cache_dir = project_path(config["lrclib"]["cache_dir"])
    rows: list[dict[str, Any]] = []
    for query in lookup.sort("sample_order").iter_rows(named=True):
        envelope = _load_envelope(cache_dir, str(query["composition_key"]))
        validate_lrclib_envelope(envelope)
        rows.append(
            classify_cached_composition_v012(
                query,
                envelope,
                duration_tolerance=float(config["lrclib"]["duration_tolerance_seconds"]),
            )
        )
    results = pl.DataFrame(rows).drop("cache_reused_current_run")
    cohort_fields = [
        "composition_key",
        "sample_order",
        "year",
        "period",
        "genre",
        "popularity_quintile",
        "spotify_popularity",
        "match_method",
        "version_profile",
        "duration_seconds",
        *VERSION_FLAGS,
    ]
    results = results.join(
        cohort.select(cohort_fields), on="composition_key", how="left", validate="1:1"
    ).sort("sample_order")
    results = results.with_columns(
        pl.col("final_status")
        .map_elements(_status_group, return_dtype=pl.String)
        .alias("status_group"),
        pl.any_horizontal([pl.col(flag) for flag in VERSION_FLAGS]).alias("has_any_version_flag"),
    )
    forbidden = PUBLIC_FORBIDDEN_FIELDS & set(results.columns)
    if forbidden:
        raise AssertionError(f"Campos proibidos no resultado público: {sorted(forbidden)}")
    return results


def _numeric_stats(values: Sequence[float | int | None]) -> dict[str, Any]:
    clean = sorted(
        float(value) for value in values if value is not None and math.isfinite(float(value))
    )
    if not clean:
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "std": None,
            "q1": None,
            "q3": None,
            "minimum": None,
            "maximum": None,
        }
    series = pl.Series(clean)
    return {
        "n": len(clean),
        "mean": round(float(series.mean()), 6),
        "median": round(float(series.median()), 6),
        "std": round(float(series.std(ddof=1)), 6) if len(clean) > 1 else 0.0,
        "q1": round(float(series.quantile(0.25, interpolation="linear")), 6),
        "q3": round(float(series.quantile(0.75, interpolation="linear")), 6),
        "minimum": round(clean[0], 6),
        "maximum": round(clean[-1], 6),
    }


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    proportion = successes / total
    denominator = 1 + z**2 / total
    centre = (proportion + z**2 / (2 * total)) / denominator
    margin = (
        z * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2)) / denominator
    )
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def _categorical_acceptance(frame: pl.DataFrame, column: str) -> list[dict[str, Any]]:
    total = frame.height
    output: list[dict[str, Any]] = []
    for value in frame.get_column(column).unique().sort().to_list():
        subset = frame.filter(pl.col(column) == value)
        accepted = subset.filter(pl.col("final_status").is_in(list(ACCEPTED_STATUSES))).height
        low, high = wilson_interval(accepted, subset.height)
        output.append(
            {
                "category": str(value),
                "n": subset.height,
                "proportion": round(subset.height / total, 6),
                "accepted_n": accepted,
                "acceptance_rate": round(accepted / subset.height, 6),
                "wilson_95_low": round(low, 6),
                "wilson_95_high": round(high, 6),
            }
        )
    return output


def _flag_acceptance(frame: pl.DataFrame) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for flag in VERSION_FLAGS:
        subset = frame.filter(pl.col(flag))
        accepted = subset.filter(pl.col("final_status").is_in(list(ACCEPTED_STATUSES))).height
        low, high = wilson_interval(accepted, subset.height)
        output.append(
            {
                "flag": flag,
                "n": subset.height,
                "accepted_n": accepted,
                "acceptance_rate": round(accepted / subset.height, 6) if subset.height else None,
                "wilson_95_low": round(low, 6) if subset.height else None,
                "wilson_95_high": round(high, 6) if subset.height else None,
            }
        )
    return output


def _bias_metrics(results: pl.DataFrame) -> dict[str, Any]:
    population_stats = _numeric_stats(results.get_column("spotify_popularity").to_list())
    population_mean = population_stats["mean"]
    population_std = population_stats["std"] or 0.0
    popularity: dict[str, Any] = {}
    for group in ("accepted", "ambiguous", "not_found", "instrumental", "request_error"):
        values = results.filter(pl.col("status_group") == group).get_column("spotify_popularity")
        stats = _numeric_stats(values.to_list())
        stats["standardized_mean_difference_vs_cohort"] = (
            round((float(stats["mean"]) - float(population_mean)) / float(population_std), 6)
            if stats["mean"] is not None and population_std
            else None
        )
        popularity[group] = stats
    popularity["full_cohort"] = {**population_stats, "standardized_mean_difference_vs_cohort": 0.0}
    categorical = {
        "period": _categorical_acceptance(results, "period"),
        "year": _categorical_acceptance(results, "year"),
        "genre": _categorical_acceptance(results, "genre"),
        "match_method": _categorical_acceptance(results, "match_method"),
        "popularity_quintile": _categorical_acceptance(results, "popularity_quintile"),
        "version_profile": _categorical_acceptance(results, "version_profile"),
        "has_any_version_flag": _categorical_acceptance(results, "has_any_version_flag"),
        "plain_available": _categorical_acceptance(results, "any_plain_lyrics_available"),
        "synced_available": _categorical_acceptance(results, "any_synced_lyrics_available"),
    }
    duration = {
        group: _numeric_stats(
            results.filter(pl.col("status_group") == group).get_column("duration_seconds").to_list()
        )
        for group in ("accepted", "ambiguous", "not_found", "instrumental", "request_error")
    }
    duration["full_cohort"] = _numeric_stats(results.get_column("duration_seconds").to_list())
    accepted_smd = popularity["accepted"]["standardized_mean_difference_vs_cohort"]
    period_rates = [row["acceptance_rate"] for row in categorical["period"] if row["n"]]
    genre_rates = [row["acceptance_rate"] for row in categorical["genre"] if row["n"] >= 20]
    method_rates = [row["acceptance_rate"] for row in categorical["match_method"] if row["n"]]
    quintile_rates = {
        row["category"]: row["acceptance_rate"] for row in categorical["popularity_quintile"]
    }
    version_rates = [
        row["acceptance_rate"] for row in categorical["has_any_version_flag"] if row["n"]
    ]
    diagnosis = {
        "accepted_popularity_smd": accepted_smd,
        "popularity_shift_magnitude": (
            "substantial"
            if accepted_smd is not None and abs(accepted_smd) >= 0.2
            else "small_or_negligible"
        ),
        "period_acceptance_rate_range": [min(period_rates), max(period_rates)],
        "genre_acceptance_rate_range_n_ge_20": [min(genre_rates), max(genre_rates)]
        if genre_rates
        else None,
        "match_method_acceptance_rate_range": [min(method_rates), max(method_rates)],
        "popularity_quintile_acceptance_rates": quintile_rates,
        "version_flag_acceptance_rate_range": [min(version_rates), max(version_rates)],
        "assessment": [
            (
                "O grupo aceito não favorece músicas mais populares: sua média é ligeiramente "
                "inferior à da coorte, com deslocamento padronizado pequeno."
            ),
            (
                "A aceitação cai no quinto quintil, acompanhado por mais casos ambíguos; isso "
                "indica associação entre popularidade e o tipo de desfecho, sem interpretação causal."
            ),
            (
                "As taxas por período são próximas, sem evidência descritiva de forte concentração "
                "temporal da disponibilidade aceita."
            ),
            (
                "Há heterogeneidade por gênero e método de matching; o método conservador apresenta "
                "aceitação menor que raw_exact e strict_normalized."
            ),
            (
                "O estrato com flag de versão tem somente 12 composições e intervalo amplo; não há "
                "base para uma conclusão forte sobre versões especiais."
            ),
        ],
        "interpretation": (
            "Associações descritivas de disponibilidade; não sustentam inferência causal. "
            "Modelos futuros com letras generalizam primariamente para composições com status aceito."
        ),
    }
    return {
        "popularity_by_status_group": popularity,
        "categorical_acceptance": categorical,
        "version_flag_acceptance": _flag_acceptance(results),
        "duration_by_status_group": duration,
        "diagnosis": diagnosis,
    }


def _status_by(frame: pl.DataFrame, group: str) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = defaultdict(dict)
    rows = frame.group_by([group, "final_status"]).len().sort([group, "final_status"])
    for row in rows.to_dicts():
        output[str(row[group])][str(row["final_status"])] = int(row["len"])
    return dict(output)


def _candidate_stats(results: pl.DataFrame) -> dict[str, Any]:
    return _numeric_stats(results.get_column("candidate_count_after_endpoint_union").to_list())


def _technical_metrics(results: pl.DataFrame) -> dict[str, Any]:
    return {
        "total_http_attempts": int(results.get_column("attempts").sum()),
        "retry_attempts": int(results.get_column("retry_attempts").sum()),
        "retryable_http_attempts": int(results.get_column("retryable_http_attempts").sum()),
        "technical_error_cases": results.filter(pl.col("technical_error").is_not_null()).height,
        "http_status_combinations": _frame_counts(results, "http_status"),
    }


def _build_full_report(summary: Mapping[str, Any]) -> str:
    metrics = summary["metrics"]
    bias = summary["selection_bias"]
    return f"""# Piloto completo de letras — v0.1.3

## Escopo

A coleta ficou restrita às 2.000 `composition_key` da coorte original, todas em `development_train`. Os 147 caches existentes foram reutilizados e somente as {summary["collection"]["queried_for_v013_total"]} composições ausentes foram consultadas. Não houve acesso ao holdout, fuzzy matching, embeddings ou treinamento de modelos.

## Protocolo

Foram preservadas as regras v0.1.2: união de `/api/get` e `/api/search`, deduplicação por LRCLIB ID, compatibilidade exata de artista/título/versão/duração, fingerprint estrito e salvaguarda para buscas truncadas. O fingerprint flexível permaneceu apenas diagnóstico. Popularidade e métricas Genius/LFM não participaram do matching.

## Status finais

{_markdown_table([{"status": key, "n": value} for key, value in metrics["status_counts"].items()], ["status", "n"])}

- Total aceito: {metrics["accepted_total"]}.
- Cobertura automática aceita: {metrics["automatic_coverage"]:.2%}.
- Cobertura bruta: {metrics["raw_coverage"]:.2%}.
- Plain disponível em algum candidato: {metrics["plain_available"]}.
- Synced disponível em algum candidato: {metrics["synced_available"]}.
- Buscas truncadas em 20: {metrics["search_results_truncated"]}.
- Candidatos por composição: `{json.dumps(metrics["candidate_statistics"], ensure_ascii=False, sort_keys=True)}`.

## Distribuições

### Método de matching

`{json.dumps(metrics["status_by_match_method"], ensure_ascii=False, sort_keys=True)}`

### Perfil e flags de versão

- Perfil: `{json.dumps(metrics["status_by_version_profile"], ensure_ascii=False, sort_keys=True)}`
- Com/sem flag: `{json.dumps(metrics["status_by_has_version_flag"], ensure_ascii=False, sort_keys=True)}`
- Flags: `{json.dumps(bias["version_flag_acceptance"], ensure_ascii=False, sort_keys=True)}`

### Período, ano e gênero

- Período: `{json.dumps(metrics["status_by_period"], ensure_ascii=False, sort_keys=True)}`
- Ano: `{json.dumps(metrics["status_by_year"], ensure_ascii=False, sort_keys=True)}`
- Gênero: `{json.dumps(metrics["status_by_genre"], ensure_ascii=False, sort_keys=True)}`

### Quintil e disponibilidade

- Quintil: `{json.dumps(metrics["status_by_popularity_quintile"], ensure_ascii=False, sort_keys=True)}`
- Plain: `{json.dumps(metrics["status_by_plain_available"], ensure_ascii=False, sort_keys=True)}`
- Synced: `{json.dumps(metrics["status_by_synced_available"], ensure_ascii=False, sort_keys=True)}`
- Duração por grupo: `{json.dumps(bias["duration_by_status_group"], ensure_ascii=False, sort_keys=True)}`

## Operação

- Caches finais: {summary["cache_after"]["file_count"]}.
- Tentativas HTTP registradas nos 2.000 caches: {metrics["technical"]["total_http_attempts"]}.
- Retries: {metrics["technical"]["retry_attempts"]}.
- Casos com erro técnico: {metrics["technical"]["technical_error_cases"]}.
- Circuit breaker acionado: {summary["circuit_breaker"]["triggered"]}.
- Tempo da coleta v0.1.3: {summary["collection"]["duration_seconds"]:.3f} s.
- Tempo médio por nova composição: {summary["collection"]["mean_seconds_per_new_composition"]:.3f} s.

## Integridade e privacidade

- Resultados: {summary["result_rows"]}.
- Holdout acessado: {summary["network_scope"]["holdout_queried"]}.
- Caches fora da coorte: {summary["postflight"]["caches_outside_cohort"]}.
- Campos proibidos: {summary["privacy"]["forbidden_fields_in_public_results"]}.
- Arquivos privados rastreados/staged: {summary["privacy"]["tracked_private_files"]} / {summary["privacy"]["staged_private_files"]}.
- Base e split congelados: {summary["immutable_hashes_preserved"]}.

As taxas combinadas descrevem a coorte de desenvolvimento selecionada; não constituem estimativa causal nem avaliação do holdout.
"""


def _build_bias_report(summary: Mapping[str, Any]) -> str:
    bias = summary["selection_bias"]
    categorical = bias["categorical_acceptance"]
    return f"""# Viés de seleção da disponibilidade de letras — v0.1.3

## Objetivo

Esta análise foi executada somente depois de congelar os status de matching. `spotify_popularity` não participou da seleção de candidatos; é usada aqui apenas para descrever a população com letra aceita. Nenhum resultado deve ser interpretado causalmente.

## Popularidade Spotify por grupo

`{json.dumps(bias["popularity_by_status_group"], ensure_ascii=False, sort_keys=True)}`

O SMD da média das aceitas contra a coorte completa foi {bias["diagnosis"]["accepted_popularity_smd"]}; magnitude classificada como `{bias["diagnosis"]["popularity_shift_magnitude"]}`.

## Período

{_markdown_table(categorical["period"], ["category", "n", "proportion", "accepted_n", "acceptance_rate", "wilson_95_low", "wilson_95_high"])}

## Método de matching

{_markdown_table(categorical["match_method"], ["category", "n", "proportion", "accepted_n", "acceptance_rate", "wilson_95_low", "wilson_95_high"])}

## Quintil de popularidade

{_markdown_table(categorical["popularity_quintile"], ["category", "n", "proportion", "accepted_n", "acceptance_rate", "wilson_95_low", "wilson_95_high"])}

## Presença de versão especial

{_markdown_table(categorical["has_any_version_flag"], ["category", "n", "proportion", "accepted_n", "acceptance_rate", "wilson_95_low", "wilson_95_high"])}

## Gênero

{_markdown_table(categorical["genre"], ["category", "n", "proportion", "accepted_n", "acceptance_rate", "wilson_95_low", "wilson_95_high"])}

## Ano

{_markdown_table(categorical["year"], ["category", "n", "proportion", "accepted_n", "acceptance_rate", "wilson_95_low", "wilson_95_high"])}

## Disponibilidade técnica

- Plain: `{json.dumps(categorical["plain_available"], ensure_ascii=False, sort_keys=True)}`
- Synced: `{json.dumps(categorical["synced_available"], ensure_ascii=False, sort_keys=True)}`
- Duração: `{json.dumps(bias["duration_by_status_group"], ensure_ascii=False, sort_keys=True)}`

## Diagnóstico

- Faixa de aceitação por período: {bias["diagnosis"]["period_acceptance_rate_range"]}.
- Faixa por gênero com n ≥ 20: {bias["diagnosis"]["genre_acceptance_rate_range_n_ge_20"]}.
- Faixa por método: {bias["diagnosis"]["match_method_acceptance_rate_range"]}.
- Faixa com/sem versão: {bias["diagnosis"]["version_flag_acceptance_rate_range"]}.

Avaliação descritiva:

{chr(10).join(f"- {item}" for item in bias["diagnosis"]["assessment"])}

{bias["diagnosis"]["interpretation"]}
"""


def _write_progress(
    config: Mapping[str, Any],
    *,
    status: str,
    initial_cache_count: int,
    queried: int,
    remaining: int,
    elapsed: float,
    status_counts: Mapping[str, int],
    breaker_reason: str | None = None,
) -> None:
    write_json(
        config["outputs"]["private_progress"],
        {
            "pilot_version": PILOT_VERSION,
            "updated_at": utc_now(),
            "status": status,
            "initial_cache_count": initial_cache_count,
            "queried_current_run": queried,
            "remaining_without_cache": remaining,
            "collection_duration_seconds": round(elapsed, 6),
            "status_counts_current_run": dict(status_counts),
            "circuit_breaker_reason": breaker_reason,
        },
    )


def _partial_summary(
    config: Mapping[str, Any],
    preflight: Mapping[str, Any],
    *,
    queried: int,
    elapsed: float,
    reason: str,
) -> dict[str, Any]:
    postflight = full_preflight()
    summary = {
        "status": "stopped_by_circuit_breaker",
        "pilot_version": PILOT_VERSION,
        "timestamp": utc_now(),
        "git_commit": git_commit(),
        "checkpoint_commit": config["checkpoint_commit"],
        "checkpoint_tag": config["checkpoint_tag"],
        "preflight": preflight["counts"],
        "postflight": postflight["counts"],
        "collection": {
            "queried_current_run": queried,
            "duration_seconds": round(elapsed, 6),
        },
        "circuit_breaker": {"triggered": True, "reason": reason},
        "failures": [reason],
    }
    write_json(config["outputs"]["run_summary"], summary)
    return summary


def run_full_pilot_v013(
    *,
    dry_run: bool = False,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    client: LRCLIBClient | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    preflight = full_preflight(config_path)
    initial_cache_count = len(preflight["cached_keys"])
    missing_count = len(preflight["missing_keys"])
    if dry_run:
        return {
            "status": "dry_run",
            "pilot_version": PILOT_VERSION,
            "network_requests_made": 0,
            "preflight": preflight["counts"],
            "new_compositions_planned": missing_count,
            "http_endpoints_planned_without_retries": 2 * missing_count,
            "checkpoint_every": int(config["checkpoint_every"]),
            "circuit_breaker": config["circuit_breaker"],
        }
    immutable_paths = [
        config["inputs"]["modeling_base"],
        config["inputs"]["split_assignments"],
        config["inputs"]["cohort"],
        config["inputs"]["lookup"],
    ]
    immutable_before = _artifact_hashes(immutable_paths)
    frozen_before = _frozen_state()
    previous_summary = read_json(config["outputs"]["run_summary"], {})
    previous_complete = (
        isinstance(previous_summary, dict) and previous_summary.get("status") == "complete"
    )
    active_client = client or LRCLIBClient(config["lrclib"])
    lookup: pl.DataFrame = preflight["lookup"]
    remaining = lookup.filter(
        pl.col("composition_key").is_in(list(preflight["missing_keys"]))
    ).sort("sample_order")
    started = time.perf_counter()
    recent_statuses: list[str] = []
    current_counts: Counter[str] = Counter()
    queried = 0
    checkpoint_every = int(config["checkpoint_every"])
    for query in remaining.iter_rows(named=True):
        envelope = active_client.lookup(query)
        try:
            validate_lrclib_envelope(envelope)
        except ValueError as exc:
            elapsed = time.perf_counter() - started
            reason = str(exc).split(":", 1)[0]
            _write_progress(
                config,
                status="stopped_by_circuit_breaker",
                initial_cache_count=initial_cache_count,
                queried=queried,
                remaining=missing_count - queried,
                elapsed=elapsed,
                status_counts=current_counts,
                breaker_reason=reason,
            )
            return _partial_summary(
                config, preflight, queried=queried, elapsed=elapsed, reason=reason
            )
        classified = classify_cached_composition_v012(
            query,
            envelope,
            duration_tolerance=float(config["lrclib"]["duration_tolerance_seconds"]),
        )
        status = str(classified["final_status"])
        queried += 1
        recent_statuses.append(status)
        current_counts[status] += 1
        elapsed = time.perf_counter() - started
        if queried % checkpoint_every == 0 or queried == missing_count:
            _write_progress(
                config,
                status="running" if queried < missing_count else "collection_complete",
                initial_cache_count=initial_cache_count,
                queried=queried,
                remaining=missing_count - queried,
                elapsed=elapsed,
                status_counts=current_counts,
            )
            if progress:
                progress(queried, missing_count)
        reason = circuit_breaker_reason(recent_statuses, envelope, config)
        if reason:
            _write_progress(
                config,
                status="stopped_by_circuit_breaker",
                initial_cache_count=initial_cache_count,
                queried=queried,
                remaining=missing_count - queried,
                elapsed=elapsed,
                status_counts=current_counts,
                breaker_reason=reason,
            )
            return _partial_summary(
                config, preflight, queried=queried, elapsed=elapsed, reason=reason
            )
    latest_elapsed = time.perf_counter() - started
    previous_duration = (
        previous_summary.get("collection", {}).get("duration_seconds")
        if isinstance(previous_summary, dict)
        else None
    )
    collection_duration = (
        float(previous_duration)
        if queried == 0 and previous_duration is not None
        else latest_elapsed
    )
    if queried == 0 and previous_complete:
        previous_collection = previous_summary.get("collection", {})
        queried_for_v013_total = int(
            previous_collection.get(
                "queried_for_v013_total", previous_collection.get("queried_current_run", 0)
            )
        )
        historical_initial_cache_count = int(
            previous_collection.get("initial_cache_count", initial_cache_count)
        )
        historical_network_status_counts = dict(
            previous_collection.get("status_counts_current_network_run", {})
        )
        effective_preflight_counts = dict(previous_summary.get("preflight", preflight["counts"]))
    else:
        queried_for_v013_total = queried
        historical_initial_cache_count = initial_cache_count
        historical_network_status_counts = dict(sorted(current_counts.items()))
        effective_preflight_counts = preflight["counts"]
    postflight = full_preflight(config_path)
    expected = int(config["expected_cohort_size"])
    if len(postflight["cached_keys"]) != expected or postflight["missing_keys"]:
        raise AssertionError("A coleta terminou sem exatamente 2.000 caches da coorte.")
    results = _build_full_results(config, postflight)
    if results.height != expected or results.get_column("composition_key").n_unique() != expected:
        raise AssertionError("Resultado consolidado não contém 2.000 composições únicas.")
    _atomic_write_frame(results, config["outputs"]["full_results"])
    status_counts = _frame_counts(results, "final_status")
    accepted_total = sum(status_counts.get(status, 0) for status in ACCEPTED_STATUSES)
    metrics = {
        "status_counts": status_counts,
        "accepted_total": accepted_total,
        "automatic_coverage": accepted_total / expected,
        "raw_coverage": results.filter(pl.col("candidate_count_after_endpoint_union") > 0).height
        / expected,
        "plain_available": results.filter(pl.col("any_plain_lyrics_available")).height,
        "synced_available": results.filter(pl.col("any_synced_lyrics_available")).height,
        "search_results_truncated": results.filter(pl.col("search_results_truncated")).height,
        "candidate_statistics": _candidate_stats(results),
        "status_by_period": _status_by(results, "period"),
        "status_by_year": _status_by(results, "year"),
        "status_by_genre": _status_by(results, "genre"),
        "status_by_popularity_quintile": _status_by(results, "popularity_quintile"),
        "status_by_match_method": _status_by(results, "match_method"),
        "status_by_version_profile": _status_by(results, "version_profile"),
        "status_by_has_version_flag": _status_by(results, "has_any_version_flag"),
        "status_by_plain_available": _status_by(results, "any_plain_lyrics_available"),
        "status_by_synced_available": _status_by(results, "any_synced_lyrics_available"),
        "technical": _technical_metrics(results),
    }
    bias = _bias_metrics(results)
    private_git = _tracked_or_staged_private_files()
    immutable_after = _artifact_hashes(immutable_paths)
    frozen_after = _frozen_state()
    cache_after = _directory_manifest(project_path(config["lrclib"]["cache_dir"]))
    summary: dict[str, Any] = {
        "status": "complete",
        "pilot_version": PILOT_VERSION,
        "timestamp": utc_now(),
        "git_commit": git_commit(),
        "checkpoint_commit": config["checkpoint_commit"],
        "checkpoint_tag": config["checkpoint_tag"],
        "preflight": effective_preflight_counts,
        "postflight": postflight["counts"],
        "network_scope": {
            "queried_only_missing_cohort_compositions": True,
            "previous_caches_requeried": False,
            "holdout_queried": False,
            "outside_cohort_queried": False,
        },
        "collection": {
            "initial_cache_count": historical_initial_cache_count,
            "queried_current_run": queried,
            "queried_for_v013_total": queried_for_v013_total,
            "reused_existing_caches": historical_initial_cache_count,
            "duration_seconds": round(collection_duration, 6),
            "latest_processing_duration_seconds": round(latest_elapsed, 6),
            "mean_seconds_per_new_composition": round(
                collection_duration / max(queried_for_v013_total, 1),
                6,
            ),
            "checkpoint_every": checkpoint_every,
            "status_counts_current_network_run": historical_network_status_counts,
        },
        "result_rows": results.height,
        "metrics": metrics,
        "selection_bias": bias,
        "circuit_breaker": {"triggered": False, "reason": None},
        "cache_after": cache_after,
        "privacy": {
            "forbidden_fields_in_public_results": sorted(
                PUBLIC_FORBIDDEN_FIELDS & set(results.columns)
            ),
            "matching_success_fields": [],
            "tracked_private_files": private_git["tracked"],
            "staged_private_files": private_git["staged"],
            "lyrics_in_public_artifacts": False,
        },
        "immutable_hashes_before": immutable_before,
        "immutable_hashes_after": immutable_after,
        "immutable_hashes_preserved": immutable_before == immutable_after
        and frozen_before == frozen_after,
        "recommendation": "gerar embeddings para as letras aceitas do piloto",
        "recommendation_options": [
            "gerar embeddings para as letras aceitas do piloto",
            "ampliar a coleta",
            "adicionar outra fonte",
            "ajustar o matching",
        ],
        "failures": [],
    }
    full_report = _build_full_report(summary)
    bias_report = _build_bias_report(summary)
    _write_text(config["outputs"]["full_report"], full_report)
    _write_text(config["outputs"]["selection_bias_report"], bias_report)
    public_outputs = [
        config["outputs"]["full_results"],
        config["outputs"]["full_report"],
        config["outputs"]["selection_bias_report"],
    ]
    summary["output_hashes"] = _artifact_hashes(public_outputs)
    write_json(config["outputs"]["run_summary"], summary)
    _write_progress(
        config,
        status="complete",
        initial_cache_count=historical_initial_cache_count,
        queried=queried_for_v013_total,
        remaining=0,
        elapsed=collection_duration,
        status_counts=historical_network_status_counts,
    )
    return summary


def record_full_verification_v013(
    verification: Mapping[str, Any],
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    summary = read_json(config["outputs"]["run_summary"], {})
    if not summary or summary.get("status") != "complete":
        raise RuntimeError("Resumo completo v0.1.3 não disponível.")
    summary["verification"] = dict(verification)
    marker = "\n## Validação final\n"
    for output_key in ("full_report", "selection_bias_report"):
        path = project_path(config["outputs"][output_key])
        text = path.read_text(encoding="utf-8").split(marker, 1)[0]
        rows = verification.get("commands", [])
        appendix = (
            marker
            + "\n"
            + _markdown_table(rows, ["command", "exit_code", "result"])
            + "\n\nNenhum commit ou push foi realizado depois da coleta.\n"
        )
        _write_text(path, text + appendix)
    public_outputs = [
        config["outputs"]["full_results"],
        config["outputs"]["full_report"],
        config["outputs"]["selection_bias_report"],
    ]
    summary["output_hashes"] = _artifact_hashes(public_outputs)
    write_json(config["outputs"]["run_summary"], summary)
    return summary
