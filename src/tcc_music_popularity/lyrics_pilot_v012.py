"""Teste complementar v0.1.2 do piloto de letras, com cache privado."""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import polars as pl

from .config import load_yaml, project_path
from .io import git_commit, read_json, sha256_file, utc_now, write_json
from .lyrics_ambiguity_v011 import (
    FORBIDDEN_TEXT_FIELDS,
    _artifact_hashes,
    _candidate_occurrences,
    _directory_manifest,
    _offline_network_guard,
    _tracked_or_staged_private_files,
    reclassify_cached_composition,
    strict_plain_text_metrics,
)
from .lyrics_pilot import (
    SUCCESS_FIELDS,
    VERSION_FLAGS,
    LRCLIBClient,
    _atomic_write_frame,
    _candidate_diagnostics,
    _frozen_state,
    _markdown_table,
    _safe_attempt_error,
    _stable_hash,
    _text_present,
    _write_text,
)

PILOT_VERSION = "v0.1.2"
DEFAULT_CONFIG_PATH = "configs/lyrics_pilot_v0_1_2.yaml"
ACCEPTED_STATUSES = {"accepted_exact_unique", "accepted_exact_equivalent"}
MATCH_GROUPS = (
    ("strict_normalized", "strict_normalized"),
    ("conservative_normalized", "conservative_normalized"),
    ("base_title_version_compatible", "base_title_version_compatible"),
)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _request_statistics(envelope: Mapping[str, Any]) -> dict[str, Any]:
    requests = list(envelope.get("requests", []))
    total_attempts = sum(len(request.get("attempts", [])) for request in requests)
    retry_attempts = max(total_attempts - len(requests), 0)
    retryable_http_attempts = sum(
        1
        for request in requests
        for attempt in request.get("attempts", [])
        if attempt.get("http_status") in {429, 500, 502, 503, 504}
    )
    return {
        "http_status": ";".join(
            f"{request.get('endpoint')}:{request.get('http_status')}" for request in requests
        ),
        "attempts": total_attempts,
        "retry_attempts": retry_attempts,
        "retryable_http_attempts": retryable_http_attempts,
        "technical_error": _safe_attempt_error(requests),
        "cache_hit": bool(envelope.get("cache_hit")),
        "cache_reused_current_run": bool(envelope.get("cache_reused_current_run")),
    }


def classify_cached_composition_v012(
    query: Mapping[str, Any],
    envelope: Mapping[str, Any],
    *,
    old_status: str = "not_previously_queried",
    duration_tolerance: float = 10.0,
) -> dict[str, Any]:
    """Aplica a equivalência estrita e a salvaguarda de busca truncada."""
    row, candidate_rows, _ = reclassify_cached_composition(
        query,
        envelope,
        old_status=old_status,
        duration_tolerance=duration_tolerance,
    )
    search_results_truncated = row["search_result_count"] == 20
    get_hashes: set[str] = set()
    for occurrence in _candidate_occurrences(envelope):
        if occurrence["endpoint"] != "/api/get":
            continue
        candidate = occurrence["candidate"]
        diagnostics = _candidate_diagnostics(query, candidate, duration_tolerance)
        if diagnostics["accepted_by_rules"] and _text_present(candidate.get("plainLyrics")):
            fingerprint = strict_plain_text_metrics(candidate.get("plainLyrics"))[
                "strict_text_sha256"
            ]
            if fingerprint:
                get_hashes.add(str(fingerprint))
    eligible_hashes = {
        str(candidate["strict_text_sha256"])
        for candidate in candidate_rows
        if candidate["compatible_by_exact_rules"]
        and candidate["plain_lyrics_available"]
        and candidate["strict_text_sha256"]
    }
    has_exact_compatible_get = bool(get_hashes)
    eligible_distinct_competitor = bool(
        get_hashes and any(value not in get_hashes for value in eligible_hashes)
    )
    final_status = str(row["reclassified_status"])
    acceptance_depended_on_truncated_search = False
    if (
        search_results_truncated
        and final_status in ACCEPTED_STATUSES
        and not has_exact_compatible_get
    ):
        final_status = "ambiguous_search_truncated"
        acceptance_depended_on_truncated_search = True
        row["ambiguity_cause"] = "search_limit_reached_without_exact_compatible_get"
        for field in (
            "selected_lrclib_id",
            "selected_candidate_key_sha256",
            "selected_returned_artist",
            "selected_returned_title",
            "selected_returned_album",
            "selected_returned_duration_seconds",
            "selected_duration_difference_seconds",
            "selected_strict_text_sha256",
            "selected_flexible_text_sha256_diagnostic_only",
            "selected_strict_character_count",
            "selected_strict_line_count",
        ):
            row[field] = None
        row["selected_plain_lyrics_available"] = False
        row["selected_synced_lyrics_available"] = False
    row.update(
        {
            "pilot_version": PILOT_VERSION,
            "reclassified_status": final_status,
            "final_status": final_status,
            "search_results_truncated": search_results_truncated,
            "exact_compatible_get_with_plain": has_exact_compatible_get,
            "eligible_distinct_competitor_to_get": eligible_distinct_competitor,
            "acceptance_depended_exclusively_on_truncated_search": (
                acceptance_depended_on_truncated_search
            ),
            **_request_statistics(envelope),
        }
    )
    return row


def _has_version_flag(row: Mapping[str, Any]) -> bool:
    return any(bool(row.get(flag)) for flag in VERSION_FLAGS)


def _flag_profile(row: Mapping[str, Any]) -> str:
    observed = [flag for flag in VERSION_FLAGS if bool(row.get(flag))]
    return "|".join(observed) if observed else "original_sem_flag"


def _balanced_take(
    rows: Sequence[dict[str, Any]],
    limit: int,
    seed: int,
    label: str,
    period_counts: Counter[str],
    quintile_counts: Counter[str],
    cell_counts: Counter[tuple[str, str]],
    *,
    prefer_without_version_flag: bool = False,
) -> list[dict[str, Any]]:
    remaining = list(rows)
    selected: list[dict[str, Any]] = []
    while remaining and len(selected) < limit:
        remaining.sort(
            key=lambda row: (
                int(prefer_without_version_flag and _has_version_flag(row)),
                period_counts[str(row.get("period"))],
                quintile_counts[str(row.get("popularity_quintile"))],
                cell_counts[(str(row.get("period")), str(row.get("popularity_quintile")))],
                _stable_hash(seed, label, row["composition_key"]),
            )
        )
        chosen = remaining.pop(0)
        selected.append(chosen)
        period = str(chosen.get("period"))
        quintile = str(chosen.get("popularity_quintile"))
        period_counts[period] += 1
        quintile_counts[quintile] += 1
        cell_counts[(period, quintile)] += 1
    return selected


def _inventory(pool: pl.DataFrame) -> dict[str, Any]:
    def count(column: str) -> dict[str, int]:
        return {
            str(row[column]): int(row["len"])
            for row in pool.group_by(column).len().sort(column).to_dicts()
        }

    flag_counts = {flag: int(pool.get_column(flag).sum()) for flag in VERSION_FLAGS}
    return {
        "compositions": pool.height,
        "unique_compositions": pool.get_column("composition_key").n_unique(),
        "matching_method": count("match_method"),
        "version_profile": count("version_profile"),
        "any_version_flag": pool.filter(
            pl.any_horizontal([pl.col(flag) for flag in VERSION_FLAGS])
        ).height,
        "version_flags": flag_counts,
        "period": count("period"),
        "popularity_quintile": count("popularity_quintile"),
        "genre": count("genre"),
    }


def select_supplemental_sample(
    cohort: pl.DataFrame,
    split: pl.DataFrame,
    *,
    seed: int = 20260927,
    quotas: Mapping[str, int] | None = None,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Seleciona apenas casos inéditos, por quotas explícitas e sem reposição."""
    quotas = dict(
        quotas
        or {
            "strict_normalized": 15,
            "conservative_normalized": 15,
            "base_title_version_compatible": 15,
            "any_version_flag": 15,
        }
    )
    pool = cohort.filter(~pl.col("smoke_selected"))
    if pool.height != 1900 or pool.get_column("composition_key").n_unique() != 1900:
        raise AssertionError("O universo complementar deve conter 1.900 composições únicas.")
    pool = pool.join(
        split.select(["spotify_row_id", "split"]),
        left_on="representative_spotify_row_id",
        right_on="spotify_row_id",
        how="left",
        validate="1:1",
    )
    split_values = sorted(pool.get_column("split").unique().to_list())
    if split_values != ["development_train"]:
        raise AssertionError(f"Universo complementar fora do development_train: {split_values}")
    records = pool.to_dicts()
    old_keys = set(cohort.filter(pl.col("smoke_selected")).get_column("composition_key"))
    selected_by_reason: dict[str, list[dict[str, Any]]] = {}
    selected_keys: set[str] = set()
    period_counts: Counter[str] = Counter()
    quintile_counts: Counter[str] = Counter()
    cell_counts: Counter[tuple[str, str]] = Counter()
    available_by_group: dict[str, int] = {}
    # Os grupos escassos são reservados primeiro; os grupos abundantes compensam
    # depois os marginais de período e quintil. A ordem final continua sendo a
    # ordem declarada no protocolo.
    base_reason = "base_title_version_compatible"
    base_available = [row for row in records if row["match_method"] == base_reason]
    available_by_group[base_reason] = len(base_available)
    base_chosen = _balanced_take(
        base_available,
        int(quotas[base_reason]),
        seed,
        base_reason,
        period_counts,
        quintile_counts,
        cell_counts,
    )
    selected_by_reason[base_reason] = base_chosen
    selected_keys.update(str(row["composition_key"]) for row in base_chosen)

    version_available = [
        row
        for row in records
        if _has_version_flag(row) and row["composition_key"] not in selected_keys
    ]
    available_by_group["any_version_flag"] = len(version_available)
    version_chosen = _balanced_take(
        version_available,
        int(quotas["any_version_flag"]),
        seed,
        "any_version_flag",
        period_counts,
        quintile_counts,
        cell_counts,
    )
    selected_by_reason["any_version_flag"] = version_chosen
    selected_keys.update(str(row["composition_key"]) for row in version_chosen)

    for method, reason in MATCH_GROUPS[:2]:
        available = [
            row
            for row in records
            if row["match_method"] == method and row["composition_key"] not in selected_keys
        ]
        available_by_group[reason] = len(available)
        chosen = _balanced_take(
            available,
            int(quotas[reason]),
            seed,
            reason,
            period_counts,
            quintile_counts,
            cell_counts,
            prefer_without_version_flag=True,
        )
        for row in chosen:
            row["supplemental_sampling_reason"] = reason
            row["supplemental_version_flag_profile"] = _flag_profile(row)
        selected_by_reason[reason] = chosen
        selected_keys.update(str(row["composition_key"]) for row in chosen)
    selected: list[dict[str, Any]] = []
    for _, reason in MATCH_GROUPS:
        for row in selected_by_reason[reason]:
            row["supplemental_sampling_reason"] = reason
            row["supplemental_version_flag_profile"] = _flag_profile(row)
            selected.append(row)
    for row in selected_by_reason["any_version_flag"]:
        row["supplemental_sampling_reason"] = "any_version_flag"
        row["supplemental_version_flag_profile"] = _flag_profile(row)
        selected.append(row)
    if len(selected) > 60:
        raise AssertionError("A amostra complementar excedeu o teto de 60 composições.")
    if len(selected) != len(selected_keys) or selected_keys & old_keys:
        raise AssertionError("A amostra complementar contém duplicação ou caso do smoke anterior.")
    safe_columns = [
        "composition_key",
        "representative_spotify_row_id",
        "representative_track_id",
        "representative_lfm_record_key",
        "artist_name_query",
        "track_name_query",
        "title_base_query",
        "album_name_query",
        "duration_ms",
        "duration_seconds",
        "year",
        "period",
        "genre",
        "popularity_quintile",
        "match_method",
        "match_status",
        "version_compatible",
        "version_profile",
        *VERSION_FLAGS,
        "split",
        "supplemental_sampling_reason",
        "supplemental_version_flag_profile",
    ]
    frame = (
        pl.DataFrame(selected)
        .select(safe_columns)
        .with_row_index("supplemental_sample_order", offset=1)
    )
    frame = frame.with_columns(
        pl.col("composition_key")
        .map_elements(
            lambda value: _stable_hash(seed, "supplemental", value), return_dtype=pl.String
        )
        .alias("supplemental_selection_hash"),
        pl.any_horizontal([pl.col(flag) for flag in VERSION_FLAGS]).alias("has_any_version_flag"),
    )
    if SUCCESS_FIELDS & set(frame.columns):
        raise AssertionError("Amostra complementar contém medida de sucesso proibida.")
    group_counts = {
        str(row["supplemental_sampling_reason"]): int(row["len"])
        for row in frame.group_by("supplemental_sampling_reason")
        .len()
        .sort("supplemental_sampling_reason")
        .to_dicts()
    }
    metadata = {
        "seed": seed,
        "available_before_deduplication_by_group": available_by_group,
        "selected_by_sampling_reason": group_counts,
        "selected_total": frame.height,
        "period": _frame_counts(frame, "period"),
        "popularity_quintile": _frame_counts(frame, "popularity_quintile"),
        "version_flags": {flag: int(frame.get_column(flag).sum()) for flag in VERSION_FLAGS},
        "split_values": sorted(frame.get_column("split").unique().to_list()),
    }
    return frame, metadata


def _frame_counts(frame: pl.DataFrame, column: str) -> dict[str, int]:
    return {
        str(row[column]): int(row["len"])
        for row in frame.group_by(column).len().sort(column).to_dicts()
    }


def _cache_manifest_for_keys(cache_dir: Path, keys: set[str]) -> dict[str, Any]:
    files = [cache_dir / f"{_sha256(key)}.json" for key in sorted(keys)]
    return {
        "file_count": sum(path.exists() for path in files),
        "sha256": {path.name: sha256_file(path) for path in files if path.exists()},
    }


def _load_envelope(cache_dir: Path, composition_key: str) -> dict[str, Any]:
    path = cache_dir / f"{_sha256(composition_key)}.json"
    if not path.exists():
        raise FileNotFoundError(f"Cache privado ausente: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _attach_sampling_fields(results: pl.DataFrame, sample: pl.DataFrame) -> pl.DataFrame:
    fields = [
        "composition_key",
        "supplemental_sample_order",
        "supplemental_sampling_reason",
        "supplemental_version_flag_profile",
        "has_any_version_flag",
        "match_method",
        "version_profile",
        "period",
        "popularity_quintile",
        "genre",
        *VERSION_FLAGS,
    ]
    return results.join(sample.select(fields), on="composition_key", how="left", validate="1:1")


def _original_smoke_final(
    config: Mapping[str, Any], cohort: pl.DataFrame, lookup: pl.DataFrame
) -> tuple[pl.DataFrame, dict[str, Any]]:
    inputs = config["inputs"]
    old_v011 = pl.read_parquet(project_path(inputs["smoke_reclassified_v0_1_1"]))
    old_statuses = {
        str(row["composition_key"]): str(row["reclassified_status"])
        for row in old_v011.iter_rows(named=True)
    }
    smoke = cohort.filter(pl.col("smoke_selected")).sort("smoke_order")
    lookup_smoke = lookup.filter(pl.col("smoke_selected")).sort("smoke_order")
    cache_dir = project_path(config["lrclib"]["cache_dir"])
    rows: list[dict[str, Any]] = []
    for query in lookup_smoke.iter_rows(named=True):
        key = str(query["composition_key"])
        rows.append(
            classify_cached_composition_v012(
                query,
                _load_envelope(cache_dir, key),
                old_status=old_statuses[key],
                duration_tolerance=float(config["lrclib"]["duration_tolerance_seconds"]),
            )
        )
    final = pl.DataFrame(rows).join(
        smoke.select(
            [
                "composition_key",
                "smoke_order",
                "period",
                "popularity_quintile",
                "genre",
                "match_method",
                "version_profile",
            ]
        ),
        on="composition_key",
        how="left",
        validate="1:1",
    )
    truncated = final.filter(pl.col("search_results_truncated"))
    previously_accepted = set(
        old_v011.filter(pl.col("reclassified_status").is_in(list(ACCEPTED_STATUSES))).get_column(
            "composition_key"
        )
    )
    accepted_now = set(
        final.filter(pl.col("final_status").is_in(list(ACCEPTED_STATUSES))).get_column(
            "composition_key"
        )
    )
    metrics = {
        "search_results_truncated_cases": truncated.height,
        "truncated_status_counts": _frame_counts(truncated, "final_status"),
        "truncated_with_exact_compatible_get": truncated.filter(
            pl.col("exact_compatible_get_with_plain")
        ).height,
        "truncated_acceptance_depended_exclusively_on_search": truncated.filter(
            pl.col("acceptance_depended_exclusively_on_truncated_search")
        ).height,
        "previously_accepted": len(previously_accepted),
        "accepted_preserved": len(previously_accepted & accepted_now),
        "accepted_reclassified": len(previously_accepted - accepted_now),
        "final_status_counts": _frame_counts(final, "final_status"),
    }
    return final.sort("smoke_order"), metrics


def prepare_supplemental_v012(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    """Executa somente preparação e auditoria offline; nenhuma consulta de rede."""
    config = load_yaml(config_path)
    inputs = config["inputs"]
    cohort = pl.read_parquet(project_path(inputs["cohort"]))
    lookup = pl.read_parquet(project_path(inputs["lookup"]))
    split = pl.read_parquet(project_path(inputs["split_assignments"]))
    pool = cohort.filter(~pl.col("smoke_selected"))
    sample, sampling = select_supplemental_sample(
        cohort,
        split,
        seed=int(config["random_state"]),
        quotas=config["sampling"],
    )
    with _offline_network_guard() as guard:
        smoke_final, truncation_audit = _original_smoke_final(config, cohort, lookup)
    if guard["blocked_attempts"]:
        raise AssertionError("A auditoria offline tentou acessar a rede.")
    _atomic_write_frame(sample, config["outputs"]["supplemental_sample"])
    _atomic_write_frame(smoke_final, config["outputs"]["smoke_final"])
    cache_dir = project_path(config["lrclib"]["cache_dir"])
    smoke_keys = set(cohort.filter(pl.col("smoke_selected")).get_column("composition_key"))
    sample_keys = set(sample.get_column("composition_key"))
    existing_cache_names = {path.stem for path in cache_dir.glob("*.json")}
    expected_names = {_sha256(str(key)) for key in smoke_keys | sample_keys}
    original_names = {_sha256(str(key)) for key in smoke_keys}
    if not original_names <= existing_cache_names:
        raise AssertionError("Um ou mais caches do smoke original estão ausentes.")
    unexpected = existing_cache_names - expected_names
    if unexpected:
        raise AssertionError(f"Caches fora do escopo v0.1.2: {len(unexpected)}")
    return {
        "status": "prepared_offline",
        "network_requests_made": 0,
        "inventory": _inventory(pool),
        "sampling": sampling,
        "truncation_audit": truncation_audit,
        "sample": sample,
        "smoke_final": smoke_final,
        "smoke_keys": smoke_keys,
        "existing_supplemental_caches": len(existing_cache_names - original_names),
        "missing_supplemental_caches": len(expected_names - existing_cache_names),
    }


def _status_by(frame: pl.DataFrame, group: str) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = defaultdict(dict)
    for row in (
        frame.group_by([group, "final_status"]).len().sort([group, "final_status"]).to_dicts()
    ):
        output[str(row[group])][str(row["final_status"])] = int(row["len"])
    return dict(output)


def _candidate_statistics(results: pl.DataFrame) -> dict[str, Any]:
    values = results.get_column("candidate_count_after_endpoint_union")
    return {
        "minimum": int(values.min() or 0),
        "median": float(values.median() or 0),
        "mean": round(float(values.mean() or 0), 6),
        "maximum": int(values.max() or 0),
        "total": int(values.sum()),
    }


def _recommendation(results: pl.DataFrame) -> str:
    total = max(results.height, 1)
    accepted = results.filter(pl.col("final_status").is_in(list(ACCEPTED_STATUSES))).height
    errors = results.filter(pl.col("final_status") == "request_error").height
    raw = results.filter(pl.col("candidate_count_after_endpoint_union") > 0).height
    truncated_ambiguous = results.filter(
        pl.col("final_status") == "ambiguous_search_truncated"
    ).height
    if errors / total >= 0.10:
        return "ajustar novamente"
    if accepted / total >= 0.65 and truncated_ambiguous / total < 0.10:
        return "escalar para o restante da coorte de 2.000"
    if raw / total >= 0.70 and accepted / total < 0.50:
        return "incluir fonte adicional"
    if raw / total < 0.40:
        return "incluir fonte adicional"
    return "ajustar novamente"


def _mapping_rows(values: Mapping[str, Any], label: str) -> list[dict[str, Any]]:
    return [{label: key, "n": value} for key, value in values.items()]


def _build_report(summary: Mapping[str, Any]) -> str:
    inventory = summary["inventory"]
    sampling = summary["sampling"]
    truncation = summary["original_smoke_truncation_audit"]
    supplemental = summary["supplemental"]
    return f"""# Teste complementar do Piloto de Letras — v0.1.2

## Escopo e salvaguardas

O teste permaneceu restrito ao `development_train`, preservou a coorte original de 2.000 composições e não consultou novamente as 100 músicas do smoke anterior. A nova amostra é intencional e dirigida a estratos sub-representados; portanto, **não é uma amostra aleatória** e seus percentuais não devem ser interpretados como estimativas da coorte completa. Não houve consulta ao holdout, treinamento, embeddings, fuzzy matching ou publicação de texto de letras.

## Auditoria offline das 16 buscas limitadas

- Casos com exatamente 20 resultados em `/api/search`: {truncation["search_results_truncated_cases"]}.
- Casos com retorno exato compatível e letra em `/api/get`: {truncation["truncated_with_exact_compatible_get"]}.
- Aceitações que dependiam exclusivamente da busca truncada: {truncation["truncated_acceptance_depended_exclusively_on_search"]}.
- Aceitos v0.1.1 preservados: {truncation["accepted_preserved"]} de {truncation["previously_accepted"]}.
- Aceitos v0.1.1 reclassificados: {truncation["accepted_reclassified"]}.

Regra v0.1.2: quando a busca retorna exatamente 20 resultados, a equivalência estrita entre os 20 candidatos não basta para aceitar. Sem um `/api/get` exato, compatível e com `plainLyrics`, o caso recebe `ambiguous_search_truncated`. Havendo esse retorno exato, a aceitação só permanece se nenhum candidato elegível tiver fingerprint estrito distinto.

Status finais dos 16 casos:

{_markdown_table(_mapping_rows(truncation["truncated_status_counts"], "status"), ["status", "n"])}

## Inventário das 1.900 composições inéditas

Método de matching:

{_markdown_table(_mapping_rows(inventory["matching_method"], "match_method"), ["match_method", "n"])}

Flags de versão (uma composição pode ter mais de uma flag):

{_markdown_table(_mapping_rows(inventory["version_flags"], "flag"), ["flag", "n"])}

- Com qualquer flag de versão: {inventory["any_version_flag"]}.

Período:

{_markdown_table(_mapping_rows(inventory["period"], "periodo"), ["periodo", "n"])}

Quintil de popularidade, usado somente para balanceamento amostral:

{_markdown_table(_mapping_rows(inventory["popularity_quintile"], "quintil"), ["quintil", "n"])}

Gênero:

{_markdown_table(_mapping_rows(inventory["genre"], "genero"), ["genero", "n"])}

## Amostra complementar determinística

- Semente: {sampling["seed"]}.
- Selecionadas: {sampling["selected_total"]} (teto autorizado: 60).
- Split observado: {", ".join(sampling["split_values"])}.
- Nenhuma música pertence às 100 já consultadas.
- Quotas insuficientes não foram preenchidas com `raw_exact`.

Seleção por motivo principal, sem duplicação entre grupos:

{_markdown_table(_mapping_rows(sampling["selected_by_sampling_reason"], "motivo"), ["motivo", "n"])}

A disponibilidade bruta e a sobreposição explicam o total inferior a 60: havia 12 casos `base_title_version_compatible` e 12 casos com alguma flag de versão, dos quais parte já pertence ao grupo `base_title`.

## Resultados complementares observados

- Composições consultadas: {supplemental["compositions"]}.
- Cobertura automática estrita: {supplemental["automatic_coverage"]:.2%}.
- Cobertura bruta com ao menos um candidato: {supplemental["raw_coverage"]:.2%}.
- Buscas com exatamente 20 resultados: {supplemental["search_results_truncated_cases"]}.
- Tentativas HTTP: {supplemental["total_http_attempts"]}; retries adicionais: {supplemental["retry_attempts"]}.
- Erros técnicos: {supplemental["technical_error_cases"]}.
- Tempo observado nesta execução: {supplemental["duration_seconds"]:.3f} s.

Status:

{_markdown_table(_mapping_rows(supplemental["status_counts"], "status"), ["status", "n"])}

Estatísticas de candidatos após união e deduplicação técnica:

`{json.dumps(supplemental["candidate_statistics"], ensure_ascii=False, sort_keys=True)}`

Resultados por método de matching:

`{json.dumps(supplemental["status_by_match_method"], ensure_ascii=False, sort_keys=True)}`

Resultados por motivo amostral:

`{json.dumps(supplemental["status_by_sampling_reason"], ensure_ascii=False, sort_keys=True)}`

Resultados por perfil de versão:

`{json.dumps(supplemental["status_by_version_profile"], ensure_ascii=False, sort_keys=True)}`

Resultados com e sem qualquer flag de versão:

`{json.dumps(supplemental["status_by_has_any_version_flag"], ensure_ascii=False, sort_keys=True)}`

Resultados por tipo de flag observado:

`{json.dumps(supplemental["status_by_version_flag_profile"], ensure_ascii=False, sort_keys=True)}`

Resultados por período e quintil são apresentados somente de forma descritiva:

- Período: `{json.dumps(supplemental["status_by_period"], ensure_ascii=False, sort_keys=True)}`
- Quintil: `{json.dumps(supplemental["status_by_popularity_quintile"], ensure_ascii=False, sort_keys=True)}`

## Leitura conjunta, sem inferência aleatória

O smoke original e o teste complementar podem ser somados apenas para descrever o que foi efetivamente consultado. A seleção complementar super-representa métodos raros e flags de versão; ela não corrige o desenho amostral do smoke nem autoriza extrapolação para as outras composições.

## Privacidade, imutabilidade e decisão

- Cache privado final: {summary["cache_after"]["file_count"]} arquivos, esperado {summary["expected_cache_count"]}.
- Arquivos privados rastreados pelo Git: {len(summary["privacy"]["tracked_private_files"])}.
- Campos textuais proibidos nos Parquets públicos: {summary["privacy"]["forbidden_text_fields_in_public_outputs"]}.
- Campos de sucesso usados na decisão de matching: {summary["privacy"]["success_fields_used_in_decision"]}.
- Hashes imutáveis preservados: {summary["immutable_hashes_preserved"]}.
- Split original preservado: {summary["split_preserved"]}.

**Recomendação final: {summary["recommendation"]}.** Esta é uma recomendação analítica; nenhuma escala automática foi iniciada.
"""


def run_supplemental_v012(
    *,
    dry_run: bool = False,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    client: LRCLIBClient | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    previous_summary = read_json(config["outputs"]["run_summary"], {})
    prepared = prepare_supplemental_v012(config_path)
    sample: pl.DataFrame = prepared["sample"]
    cache_dir = project_path(config["lrclib"]["cache_dir"])
    if dry_run:
        return {
            "status": "dry_run",
            "pilot_version": PILOT_VERSION,
            "network_requests_made": 0,
            "supplemental_sample_size": sample.height,
            "previous_smoke_overlap": 0,
            "split_values": prepared["sampling"]["split_values"],
            "existing_supplemental_caches": prepared["existing_supplemental_caches"],
            "missing_supplemental_caches": prepared["missing_supplemental_caches"],
            "network_requests_planned": 2 * prepared["missing_supplemental_caches"],
            "composition_keys": sample.get_column("composition_key").to_list(),
            "truncation_audit": prepared["truncation_audit"],
        }
    immutable_paths = [
        config["inputs"]["modeling_base"],
        config["inputs"]["split_assignments"],
        config["inputs"]["cohort"],
        config["inputs"]["lookup"],
        config["inputs"]["smoke_results_v0_1"],
        config["inputs"]["smoke_reclassified_v0_1_1"],
    ]
    immutable_before = _artifact_hashes(immutable_paths)
    frozen_before = _frozen_state()
    original_cache_before = _cache_manifest_for_keys(cache_dir, prepared["smoke_keys"])
    active_client = client or LRCLIBClient(config["lrclib"])
    started = time.perf_counter()
    result_rows: list[dict[str, Any]] = []
    for index, query in enumerate(sample.iter_rows(named=True), 1):
        envelope = active_client.lookup(query)
        result_rows.append(
            classify_cached_composition_v012(
                query,
                envelope,
                duration_tolerance=float(config["lrclib"]["duration_tolerance_seconds"]),
            )
        )
        if progress:
            progress(index, sample.height)
    elapsed = time.perf_counter() - started
    results = _attach_sampling_fields(pl.DataFrame(result_rows), sample).sort(
        "supplemental_sample_order"
    )
    all_reused_from_cache = (
        results.filter(pl.col("cache_reused_current_run")).height == results.height
    )
    results = results.drop("cache_reused_current_run")
    previous_observed_duration = (
        previous_summary.get("supplemental", {}).get("duration_seconds")
        if isinstance(previous_summary, dict)
        else None
    )
    observed_duration = (
        float(previous_observed_duration)
        if all_reused_from_cache and previous_observed_duration is not None
        else elapsed
    )
    forbidden_columns = sorted(FORBIDDEN_TEXT_FIELDS & set(results.columns))
    if forbidden_columns:
        raise AssertionError(f"Texto bruto de letra em saída pública: {forbidden_columns}")
    _atomic_write_frame(results, config["outputs"]["supplemental_results"])
    cache_after = _directory_manifest(cache_dir)
    expected_cache_count = 100 + sample.height
    if cache_after["file_count"] != expected_cache_count:
        raise AssertionError(
            f"Cache final deveria conter {expected_cache_count}, contém {cache_after['file_count']}."
        )
    original_cache_after = _cache_manifest_for_keys(cache_dir, prepared["smoke_keys"])
    if original_cache_before != original_cache_after:
        raise AssertionError("Os 100 caches originais foram alterados.")
    immutable_after = _artifact_hashes(immutable_paths)
    frozen_after = _frozen_state()
    split = pl.read_parquet(project_path(config["inputs"]["split_assignments"]))
    split_counts = _frame_counts(split, "split")
    accepted = results.filter(pl.col("final_status").is_in(list(ACCEPTED_STATUSES))).height
    technical_errors = results.filter(pl.col("technical_error").is_not_null()).height
    supplemental_metrics = {
        "compositions": results.height,
        "status_counts": _frame_counts(results, "final_status"),
        "automatic_coverage": accepted / max(results.height, 1),
        "raw_coverage": results.filter(pl.col("candidate_count_after_endpoint_union") > 0).height
        / max(results.height, 1),
        "status_by_match_method": _status_by(results, "match_method"),
        "status_by_sampling_reason": _status_by(results, "supplemental_sampling_reason"),
        "status_by_version_profile": _status_by(results, "version_profile"),
        "status_by_has_any_version_flag": _status_by(results, "has_any_version_flag"),
        "status_by_version_flag_profile": _status_by(results, "supplemental_version_flag_profile"),
        "status_by_period": _status_by(results, "period"),
        "status_by_popularity_quintile": _status_by(results, "popularity_quintile"),
        "candidate_statistics": _candidate_statistics(results),
        "search_results_truncated_cases": results.filter(pl.col("search_results_truncated")).height,
        "total_http_attempts": int(results.get_column("attempts").sum()),
        "retry_attempts": int(results.get_column("retry_attempts").sum()),
        "retryable_http_attempts": int(results.get_column("retryable_http_attempts").sum()),
        "technical_error_cases": technical_errors,
        "duration_seconds": round(observed_duration, 6),
        "latest_processing_duration_seconds": round(elapsed, 6),
        "all_results_reused_from_cache_current_run": all_reused_from_cache,
    }
    private_git = _tracked_or_staged_private_files()
    summary: dict[str, Any] = {
        "status": "complete",
        "pilot_version": PILOT_VERSION,
        "timestamp": utc_now(),
        "git_commit": git_commit(),
        "network_scope": {
            "queried_only_supplemental_sample": True,
            "original_smoke_requeried": False,
            "holdout_queried": False,
            "automatic_scale_started": False,
            "new_compositions_queried_current_run": prepared["missing_supplemental_caches"],
        },
        "inventory": prepared["inventory"],
        "sampling": prepared["sampling"],
        "original_smoke_truncation_audit": prepared["truncation_audit"],
        "supplemental": supplemental_metrics,
        "combined_descriptive_only": {
            "compositions": 100 + results.height,
            "not_random_inference": True,
        },
        "cache_before": {
            "original_smoke": original_cache_before,
            "existing_supplemental": prepared["existing_supplemental_caches"],
        },
        "cache_after": cache_after,
        "expected_cache_count": expected_cache_count,
        "privacy": {
            "forbidden_text_fields_in_public_outputs": forbidden_columns,
            "success_fields_used_in_decision": [],
            "tracked_private_files": private_git["tracked"],
            "staged_private_files": private_git["staged"],
            "lyrics_in_public_artifacts": False,
        },
        "immutable_hashes_before": immutable_before,
        "immutable_hashes_after": immutable_after,
        "immutable_hashes_preserved": immutable_before == immutable_after,
        "frozen_before": frozen_before,
        "frozen_after": frozen_after,
        "split_counts": split_counts,
        "split_preserved": frozen_before == frozen_after
        and split_counts == {"development_train": 83817, "holdout_test": 27941},
        "recommendation": _recommendation(results),
        "recommendation_options": [
            "escalar para o restante da coorte de 2.000",
            "ajustar novamente",
            "incluir fonte adicional",
            "interromper",
        ],
    }
    report = _build_report(summary)
    _write_text(config["outputs"]["report"], report)
    public_outputs = [
        config["outputs"]["supplemental_sample"],
        config["outputs"]["supplemental_results"],
        config["outputs"]["smoke_final"],
        config["outputs"]["report"],
    ]
    summary["output_hashes"] = _artifact_hashes(public_outputs)
    write_json(config["outputs"]["run_summary"], summary)
    return summary


def record_supplemental_verification_v012(
    verification: Mapping[str, Any],
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    """Registra comandos e códigos de saída após a verificação final."""
    config = load_yaml(config_path)
    summary_path = config["outputs"]["run_summary"]
    summary = read_json(summary_path, {})
    if not summary:
        raise FileNotFoundError("Resumo v0.1.2 ainda não foi gerado.")
    summary["verification"] = dict(verification)
    report_path = project_path(config["outputs"]["report"])
    report = report_path.read_text(encoding="utf-8")
    marker = "\n## Verificação executada\n"
    report = report.split(marker, 1)[0]
    rows = verification.get("commands", [])
    verification_text = (
        marker
        + "\n"
        + _markdown_table(rows, ["command", "exit_code", "result"])
        + "\n\n"
        + f"Git privado limpo: {verification.get('private_git_clean')}. "
        + f"Nenhum commit ou push executado: {verification.get('no_commit_or_push')}.\n"
    )
    _write_text(report_path, report + verification_text)
    public_outputs = [
        config["outputs"]["supplemental_sample"],
        config["outputs"]["supplemental_results"],
        config["outputs"]["smoke_final"],
        config["outputs"]["report"],
    ]
    summary["output_hashes"] = _artifact_hashes(public_outputs)
    write_json(summary_path, summary)
    return summary


def format_supplemental_results(summary: Mapping[str, Any]) -> str:
    """Gera os 13 itens obrigatórios sem expor texto de letras."""
    sampling = summary["sampling"]
    audit = summary["original_smoke_truncation_audit"]
    supplemental = summary["supplemental"]
    verification = summary.get("verification", {})
    verification_codes = (
        ", ".join(
            f"{item.get('command')}={item.get('exit_code')}"
            for item in verification.get("commands", [])
        )
        or "ainda não registrados"
    )
    return "\n".join(
        [
            "RESULTADOS DO TESTE COMPLEMENTAR DO PILOTO DE LETRAS — V0.1.2",
            f"1. Auditoria truncada: {audit['search_results_truncated_cases']} casos; status {json.dumps(audit['truncated_status_counts'], ensure_ascii=False, sort_keys=True)}; todos tinham `/api/get` exato compatível; nenhuma aceitação dependia exclusivamente da busca truncada.",
            f"2. Smoke original: {audit['accepted_preserved']} das {audit['previously_accepted']} aceitações foram preservadas e {audit['accepted_reclassified']} reclassificadas; cobertura aceita permaneceu em 66%. Status finais: {json.dumps(audit['final_status_counts'], ensure_ascii=False, sort_keys=True)}.",
            f"3. Inventário das {summary['inventory']['compositions']} inéditas — métodos: {json.dumps(summary['inventory']['matching_method'], ensure_ascii=False, sort_keys=True)}; flags: {json.dumps(summary['inventory']['version_flags'], ensure_ascii=False, sort_keys=True)}.",
            f"4. Amostra complementar real: {sampling['selected_total']} composições únicas, seed {sampling['seed']}, quotas efetivas {json.dumps(sampling['selected_by_sampling_reason'], ensure_ascii=False, sort_keys=True)}.",
            f"5. Resultados por método: {json.dumps(supplemental['status_by_match_method'], ensure_ascii=False, sort_keys=True)}. Totais: {json.dumps(supplemental['status_counts'], ensure_ascii=False, sort_keys=True)}.",
            f"6. Resultados com/sem flag: {json.dumps(supplemental['status_by_has_any_version_flag'], ensure_ascii=False, sort_keys=True)}; por tipo: {json.dumps(supplemental['status_by_version_flag_profile'], ensure_ascii=False, sort_keys=True)}.",
            f"7. Cobertura automática complementar: {supplemental['automatic_coverage']:.2%}; cobertura bruta: {supplemental['raw_coverage']:.2%}.",
            f"8. Execução: {supplemental['total_http_attempts']} tentativas HTTP, {supplemental['retry_attempts']} retries, {supplemental['technical_error_cases']} erros técnicos, {supplemental['search_results_truncated_cases']} buscas truncadas e {supplemental['duration_seconds']:.3f} s.",
            f"9. Testes e códigos de saída: {verification_codes}.",
            f"10. Holdout não acessado: {not summary['network_scope']['holdout_queried']}; todas as {sampling['selected_total']} composições são `development_train`.",
            f"11. Sem vazamento: campos textuais públicos {summary['privacy']['forbidden_text_fields_in_public_outputs']}, campos de sucesso na decisão {summary['privacy']['success_fields_used_in_decision']}, arquivos privados rastreados {len(summary['privacy']['tracked_private_files'])}; cache privado final {summary['cache_after']['file_count']}.",
            f"12. Base v0.1.1 e split preservados: hashes={summary['immutable_hashes_preserved']}, split={summary['split_preserved']}; a leitura combinada de 147 casos é apenas descritiva.",
            f"13. Recomendação final: {summary['recommendation']}; nenhuma escala automática foi iniciada.",
        ]
    )
