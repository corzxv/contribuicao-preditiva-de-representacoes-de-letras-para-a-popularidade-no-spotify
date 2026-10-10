"""Congelamento target-free do protocolo e da coorte final v0.4."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import polars as pl

from .config import PROJECT_ROOT, load_yaml, project_path
from .io import git_commit, sha256_file, utc_now, write_json
from .lyrics_pilot import (
    VERSION_FLAGS,
    _atomic_write_frame,
    _stable_hash,
    _text_present,
    _version_flags,
    _version_profile,
    _write_text,
    pilot_base_title,
)

PROTOCOL_VERSION = "final-study-protocol-v1.0"
SCALE_VERSION = "v0.4"
DEFAULT_CONFIG_PATH = "configs/final_scale_v0_4.yaml"
SEED = 20261010
FORBIDDEN_SAMPLING_COLUMNS = {
    "spotify_popularity",
    "genius_lyrics_views",
    "lfm_playcount",
    "lrclib_status",
    "lyrics_available",
    "pilot_success",
}
EXPECTED_FROZEN_HASHES = {
    "data/processed/modeling_base_lfm_v0_1_1.parquet": (
        "1c28f31e9b466b76d7e0180b769ba7ac51c46d2590ad7b1ba1ed21eaebdd1c5c"
    ),
    "data/processed/split_assignments_v0_1_1.parquet": (
        "4b0ff5a0e9be21af15607b9bbced423c99247c7d1aaa9615635baf134b86856b"
    ),
}
IDENTIFIERS = ["spotify_row_id", "track_id", "lfm_record_key"]
SPLITS = ("development_train", "holdout_test")


def _period(value: int | None) -> str:
    if value is None:
        return "ausente"
    if value <= 1999:
        return "até 1999"
    if value <= 2005:
        return "2000-2005"
    if value <= 2011:
        return "2006-2011"
    if value <= 2017:
        return "2012-2017"
    if value <= 2023:
        return "2018-2023"
    return "2024+"


def _hash_frame(frame: pl.DataFrame) -> str:
    payload = json.dumps(
        frame.to_dicts(), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _source_columns() -> tuple[list[str], list[str], list[str]]:
    base = [
        *IDENTIFIERS,
        "year",
        "genre",
        "duration_ms",
        "remaster",
        "remix",
        "live",
        "acoustic",
        "radio_edit",
        "mono_stereo",
        "instrumental",
        "demo",
    ]
    split = [
        *IDENTIFIERS,
        "composition_key",
        "artist_group_id",
        "composition_group_id",
        "split_group_id",
        "split",
        "split_random_state",
        "split_version",
    ]
    audit = [
        *IDENTIFIERS,
        "artist_name_raw",
        "track_name_raw",
        "match_method",
        "match_score",
        "match_status",
        "version_compatible",
        "matching_version",
    ]
    return base, split, audit


def load_target_free_source(config: Mapping[str, Any]) -> pl.DataFrame:
    """Carrega apenas campos explicitamente permitidos; nunca projeta o alvo."""

    base_columns, split_columns, audit_columns = _source_columns()
    selected = set(base_columns) | set(split_columns) | set(audit_columns)
    forbidden = sorted(FORBIDDEN_SAMPLING_COLUMNS & selected)
    if forbidden:
        raise AssertionError(f"Campos proibidos solicitados na amostragem: {forbidden}")
    inputs = config["inputs"]
    base = pl.scan_parquet(project_path(inputs["modeling_base"])).select(base_columns).collect()
    split = (
        pl.scan_parquet(project_path(inputs["split_assignments"])).select(split_columns).collect()
    )
    audit = pl.scan_parquet(project_path(inputs["matching_audit"])).select(audit_columns).collect()
    source = base.join(split, on=IDENTIFIERS, how="left", validate="1:1").join(
        audit, on=IDENTIFIERS, how="left", validate="1:1"
    )
    if source.height != base.height:
        raise AssertionError("Junções target-free alteraram a cardinalidade da base.")
    if FORBIDDEN_SAMPLING_COLUMNS & set(source.columns):
        raise AssertionError("Fonte da amostragem contém variável resposta ou proxy proibido.")
    if sorted(source.get_column("split").unique().to_list()) != sorted(SPLITS):
        raise AssertionError("Split congelado ausente ou inesperado.")
    return source


def select_representatives_without_target(
    source: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Replica a escolha do piloto, removendo toda dependência de popularidade."""

    forbidden = sorted(FORBIDDEN_SAMPLING_COLUMNS & set(source.columns))
    if forbidden:
        raise AssertionError(f"Representante recebeu campos proibidos: {forbidden}")
    rows: list[dict[str, Any]] = []
    missing_key = 0
    for source_row in source.iter_rows(named=True):
        if not _text_present(source_row.get("composition_key")):
            missing_key += 1
            continue
        row = dict(source_row)
        flags = _version_flags(row.get("track_name_raw"))
        row["karaoke"] = flags["karaoke"]
        row["title_base_query"] = pilot_base_title(row.get("track_name_raw"))
        row["period"] = _period(row.get("year"))
        row["genre_sampling"] = str(row.get("genre") or "(ausente)")
        row["version_profile"] = _version_profile(row)
        row["has_any_version_flag"] = any(bool(row.get(name)) for name in VERSION_FLAGS)
        row["_preferred_original"] = int(
            not any(bool(row.get(name)) for name in ("live", "remix", "acoustic", "karaoke"))
        )
        row["_status_rank"] = {
            "accepted_high_confidence": 2,
            "accepted_with_rules": 1,
        }.get(str(row.get("match_status")), 0)
        row["_method_rank"] = {
            "raw_exact": 4,
            "strict_normalized": 3,
            "conservative_normalized": 2,
            "base_title_version_compatible": 1,
        }.get(str(row.get("match_method")), 0)
        row["_completeness"] = sum(
            (
                _text_present(row.get("artist_name_raw")),
                _text_present(row.get("track_name_raw")),
                row.get("duration_ms") is not None,
            )
        )
        rows.append(row)
    ordered = sorted(
        rows,
        key=lambda row: (
            str(row["composition_key"]),
            -int(row["_preferred_original"]),
            -int(row["_status_rank"]),
            -int(row["_method_rank"]),
            -(float(row["match_score"]) if row.get("match_score") is not None else -1.0),
            -int(row["_completeness"]),
            int(row["spotify_row_id"]),
            str(row["track_id"]),
        ),
    )
    representatives: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in ordered:
        key = str(row["composition_key"])
        if key not in seen:
            representatives.append(row)
            seen.add(key)
    clean = [
        {key: value for key, value in row.items() if not key.startswith("_")}
        for row in representatives
    ]
    frame = pl.DataFrame(clean).sort("composition_key")
    crossing = (
        source.filter(pl.col("composition_key").is_not_null())
        .group_by("composition_key")
        .agg(pl.col("split").n_unique().alias("n_splits"))
        .filter(pl.col("n_splits") > 1)
        .height
    )
    if crossing:
        raise AssertionError("Há composition_key atravessando o split congelado.")
    group_sizes = frame.group_by("artist_group_id").len().rename({"len": "artist_group_size"})
    frame = frame.join(group_sizes, on="artist_group_id", how="left", validate="m:1")
    return frame, {
        "source_rows": source.height,
        "missing_composition_key_rows": missing_key,
        "eligible_unique_compositions": frame.height,
        "duplicate_rows_collapsed": len(rows) - frame.height,
        "composition_keys_crossing_split": crossing,
        "target_columns_loaded": [],
    }


def deterministic_main_and_reserve(
    representatives: pl.DataFrame,
    *,
    seed: int,
    main_counts: Mapping[str, int],
    reserve_counts: Mapping[str, int],
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Produz uma permutação única por split; reserva é a continuação da ordem."""

    forbidden = sorted(FORBIDDEN_SAMPLING_COLUMNS & set(representatives.columns))
    if forbidden:
        raise AssertionError(f"Amostragem recebeu campos proibidos: {forbidden}")
    main_rows: list[dict[str, Any]] = []
    reserve_rows: list[dict[str, Any]] = []
    for split in SPLITS:
        rows = representatives.filter(pl.col("split") == split).to_dicts()
        ordered = sorted(
            rows,
            key=lambda row: (
                _stable_hash(seed, "final-sampling-v1.0", split, row["composition_key"]),
                str(row["composition_key"]),
            ),
        )
        main_n = int(main_counts[split])
        reserve_n = int(reserve_counts[split])
        if len(ordered) < main_n + reserve_n:
            raise AssertionError(f"Universo insuficiente no split {split}.")
        for index, row in enumerate(ordered[:main_n], 1):
            main_rows.append(
                {
                    **row,
                    "sampling_role": "main",
                    "sampling_order_within_split": index,
                    "sampling_hash": _stable_hash(
                        seed, "final-sampling-v1.0", split, row["composition_key"]
                    ),
                }
            )
        for index, row in enumerate(ordered[main_n : main_n + reserve_n], 1):
            reserve_rows.append(
                {
                    **row,
                    "sampling_role": "reserve",
                    "sampling_order_within_split": index,
                    "sampling_hash": _stable_hash(
                        seed, "final-sampling-v1.0", split, row["composition_key"]
                    ),
                }
            )
    main = pl.DataFrame(main_rows).sort(["split", "sampling_order_within_split"])
    reserve = pl.DataFrame(reserve_rows).sort(["split", "sampling_order_within_split"])
    main_keys = set(main.get_column("composition_key"))
    reserve_keys = set(reserve.get_column("composition_key"))
    if main_keys & reserve_keys:
        raise AssertionError("Coorte principal e reserva se sobrepõem.")
    if main.get_column("composition_key").n_unique() != main.height:
        raise AssertionError("Coorte principal contém composição duplicada.")
    if reserve.get_column("composition_key").n_unique() != reserve.height:
        raise AssertionError("Reserva contém composição duplicada.")
    return main, reserve


def _safe_standardized_difference(sample_p: float, population_p: float) -> float:
    denominator = math.sqrt((sample_p * (1 - sample_p) + population_p * (1 - population_p)) / 2)
    if denominator == 0:
        return 0.0
    return (sample_p - population_p) / denominator


def categorical_representativity(
    population: pl.DataFrame, sample: pl.DataFrame, field: str
) -> list[dict[str, Any]]:
    categories = sorted(
        set(str(value) for value in population.get_column(field).fill_null("(ausente)"))
        | set(str(value) for value in sample.get_column(field).fill_null("(ausente)"))
    )
    population_values = Counter(
        str(value) for value in population.get_column(field).fill_null("(ausente)")
    )
    sample_values = Counter(str(value) for value in sample.get_column(field).fill_null("(ausente)"))
    rows = []
    for category in categories:
        population_p = population_values[category] / population.height
        sample_p = sample_values[category] / sample.height
        rows.append(
            {
                "field": field,
                "category": category,
                "population_n": population_values[category],
                "sample_n": sample_values[category],
                "population_proportion": population_p,
                "sample_proportion": sample_p,
                "difference_percentage_points": 100 * (sample_p - population_p),
                "standardized_difference": _safe_standardized_difference(sample_p, population_p),
            }
        )
    return rows


def _numeric_summary(frame: pl.DataFrame, field: str) -> dict[str, Any]:
    series = frame.get_column(field).cast(pl.Float64).drop_nulls()
    return {
        "n": series.len(),
        "mean": float(series.mean()) if series.len() else None,
        "std": float(series.std(ddof=1)) if series.len() > 1 else 0.0,
        "median": float(series.median()) if series.len() else None,
        "minimum": float(series.min()) if series.len() else None,
        "maximum": float(series.max()) if series.len() else None,
    }


def numeric_representativity(
    population: pl.DataFrame, sample: pl.DataFrame, field: str
) -> dict[str, Any]:
    population_stats = _numeric_summary(population, field)
    sample_stats = _numeric_summary(sample, field)
    pooled = math.sqrt((float(population_stats["std"]) ** 2 + float(sample_stats["std"]) ** 2) / 2)
    difference = (
        float(sample_stats["mean"]) - float(population_stats["mean"])
        if sample_stats["mean"] is not None and population_stats["mean"] is not None
        else None
    )
    return {
        "field": field,
        "population": population_stats,
        "sample": sample_stats,
        "standardized_mean_difference": difference / pooled if pooled and difference else 0.0,
    }


def build_representativity(population: pl.DataFrame, sample: pl.DataFrame) -> dict[str, Any]:
    categorical_fields = ["split", "period", "year", "genre_sampling", "match_method"]
    categorical_fields.extend(VERSION_FLAGS)
    categorical = {
        field: categorical_representativity(population, sample, field)
        for field in categorical_fields
    }
    maximum = {
        field: max((abs(row["standardized_difference"]) for row in rows), default=0.0)
        for field, rows in categorical.items()
    }
    population_groups = population.group_by("artist_group_id").len()
    sample_groups = sample.group_by("artist_group_id").len()
    artist = {
        "population_unique_groups": population_groups.height,
        "sample_unique_groups": sample_groups.height,
        "population_group_size": _numeric_summary(population_groups, "len"),
        "sample_group_size": _numeric_summary(sample_groups, "len"),
        "population_singleton_proportion": population_groups.filter(pl.col("len") == 1).height
        / population_groups.height,
        "sample_singleton_proportion": sample_groups.filter(pl.col("len") == 1).height
        / sample_groups.height,
    }
    return {
        "categorical": categorical,
        "maximum_absolute_standardized_difference": maximum,
        "numeric": {
            "year": numeric_representativity(population, sample, "year"),
            "duration_ms": numeric_representativity(population, sample, "duration_ms"),
            "artist_group_size_at_composition_level": numeric_representativity(
                population, sample, "artist_group_size"
            ),
        },
        "artist_groups": artist,
    }


def _table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    head = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    return "\n".join([head, separator, *body])


def _analysis_protocol() -> str:
    return """# Protocolo final de análise — v1.0

## Pergunta e interpretação

Avaliar se descritores tradicionais e embeddings das letras acrescentam capacidade preditiva à popularidade Spotify além de metadados e características acústicas. As conclusões serão preditivas e associativas, nunca causais.

## Unidade e resposta

Uma composição musical, representada por exatamente um `track_id` Spotify escolhido deterministicamente sem popularidade. A resposta é `spotify_popularity`, contínua entre 0 e 100. O alvo do holdout permanecerá selado até uma avaliação final única.

## Blocos congelados

1. Baseline: 23 variáveis permitidas, sem PCA.
2. Tradicional: Baseline + 196 descritores LFM2b; PCA de 90% somente no bloco LFM2b e ajustada no treino.
3. Profundo: Baseline + 384 dimensões MiniLM; PCA de 90% somente no MiniLM e ajustada no treino.
4. Combinado: Baseline + PCAs separadas de 90% para LFM2b e MiniLM, concatenadas após os ajustes no treino.

## Algoritmos e métricas

Elastic Net é o algoritmo primário, com a grade ampliada v0.3.1: alpha em {0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30} e l1_ratio em {0.05, 0.1, 0.25, 0.5, 0.8, 0.95}. Ridge é secundária, com alpha em {0.0001, 0.001, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000}. HistGradientBoosting não será modelo final principal. A análise residual fica restrita ao piloto/apêndice.

MAE é a métrica primária. RMSE, R² e Spearman são secundárias. Diferenças de MAE e RMSE serão avaliadas por bootstrap pareado agrupado por artista, conforme protocolo congelado antes da abertura do holdout.

## Holdout

O split permanece 75% `development_train` e 25% `holdout_test`. O holdout pode receber coleta e features congeladas, mas sua popularidade não será carregada, descrita, usada para ajuste, usada em métricas ou utilizada para decisões metodológicas. Os quatro modelos serão comparados na mesma amostra comum de composições com letras aceitas.
"""


def _sampling_protocol(summary: Mapping[str, Any]) -> str:
    counts = summary["sampling"]
    return f"""# Protocolo final de amostragem — v1.0

## Regra congelada

- Seed: `{summary["seed"]}`.
- Coorte principal: {counts["main_total"]} composições, sendo {counts["main_by_split"]["development_train"]} de desenvolvimento e {counts["main_by_split"]["holdout_test"]} de holdout.
- Reserva ordenada: {counts["reserve_total"]} composições, sendo {counts["reserve_by_split"]["development_train"]} de desenvolvimento e {counts["reserve_by_split"]["holdout_test"]} de holdout.
- A ordenação é o SHA-256 determinístico de seed, versão, split e `composition_key`. A reserva é a continuação da mesma permutação em cada split.
- Nenhuma popularidade, proxy de sucesso, disponibilidade de letra, cache ou resultado do piloto participa da seleção.

## Representante por composição

Regra idêntica ao piloto e sem popularidade: preferência por registros sem flags live/remix/acoustic/karaoke; maior confiança por status, método e score de matching congelados; maior completude de artista, título e duração; menor `spotify_row_id` e depois menor `track_id` como desempate estável.

## Reserva

A reserva somente será consultada se a coorte principal produzir menos de 10.000 letras aceitas. A ativação ocorrerá em até quatro lotes fixos de 500, cada um com 375 desenvolvimento e 125 holdout, interrompendo ao atingir 10.000 aceitas ou esgotar 2.000 casos. Não haverá substituição individual.

## Integridade

- Hash SHA-256 do arquivo completo da coorte: `{summary["private_artifact_hashes"]["cohort_sha256"]}`.
- Hash SHA-256 do arquivo completo da reserva: `{summary["private_artifact_hashes"]["reserve_sha256"]}`.
- Hash lógico target-free da coorte: `{summary["private_artifact_hashes"]["cohort_logical_sha256"]}`.
- Hash lógico target-free da reserva: `{summary["private_artifact_hashes"]["reserve_logical_sha256"]}`.
"""


def _sampling_report(summary: Mapping[str, Any]) -> str:
    representative = summary["representativity"]
    numeric_rows = []
    for field, item in representative["numeric"].items():
        numeric_rows.append(
            [
                field,
                round(item["population"]["mean"], 4),
                round(item["sample"]["mean"], 4),
                round(item["standardized_mean_difference"], 4),
            ]
        )
    categorical_rows = [
        [field, round(value, 4)]
        for field, value in representative["maximum_absolute_standardized_difference"].items()
    ]
    return "\n".join(
        [
            "# Relatório da amostragem final — v1.0",
            "",
            "A seleção foi concluída antes de qualquer consulta nova ao LRCLIB e sem carregar `spotify_popularity`, `genius_lyrics_views`, `lfm_playcount`, disponibilidade de letras ou resultados do piloto.",
            "",
            f"Universo elegível: {summary['universe']['eligible_unique_compositions']} composições; coorte: {summary['sampling']['main_total']}; reserva: {summary['sampling']['reserve_total']}; sobreposição: 0.",
            "",
            "## Diferenças numéricas",
            "",
            _table(
                ["Campo", "Média universo", "Média coorte", "Diferença padronizada"], numeric_rows
            ),
            "",
            "## Maior diferença padronizada por variável categórica",
            "",
            _table(["Campo", "Máximo absoluto"], categorical_rows),
            "",
            "## Grupos de artista",
            "",
            f"Universo: {representative['artist_groups']['population_unique_groups']} grupos; coorte: {representative['artist_groups']['sample_unique_groups']} grupos. Proporção de grupos singleton: {representative['artist_groups']['population_singleton_proportion']:.4f} no universo e {representative['artist_groups']['sample_singleton_proportion']:.4f} na coorte.",
            "",
            "As listas individuais permanecem em área privada ignorada pelo Git. Este relatório contém apenas agregados.",
            "",
        ]
    )


def _git_private_files() -> dict[str, list[str]]:
    prefixes = (
        "data/derived/private_final_study/",
        "data/raw/lyrics_private/",
        "data/interim/lyrics_private/",
        "data/derived/private_embeddings/",
    )
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True
    ).stdout.splitlines()
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    return {
        "tracked": [value for value in tracked if value.replace("\\", "/").startswith(prefixes)],
        "staged": [value for value in staged if value.replace("\\", "/").startswith(prefixes)],
    }


def prepare_final_protocol_v040(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    if int(config["seed"]) != SEED:
        raise AssertionError("Seed divergente do protocolo final.")
    frozen = {path: sha256_file(project_path(path)) for path in EXPECTED_FROZEN_HASHES}
    if frozen != EXPECTED_FROZEN_HASHES:
        raise AssertionError("Base v0.1.1 ou split divergiram dos hashes congelados.")
    source = load_target_free_source(config)
    representatives, universe_audit = select_representatives_without_target(source)
    sampling = config["sampling"]
    main_counts = {
        "development_train": int(sampling["main_development"]),
        "holdout_test": int(sampling["main_holdout"]),
    }
    reserve_counts = {
        "development_train": int(sampling["reserve_development"]),
        "holdout_test": int(sampling["reserve_holdout"]),
    }
    main, reserve = deterministic_main_and_reserve(
        representatives,
        seed=SEED,
        main_counts=main_counts,
        reserve_counts=reserve_counts,
    )
    batch_development = int(sampling["reserve_batch_development"])
    batch_holdout = int(sampling["reserve_batch_holdout"])
    reserve = reserve.with_columns(
        pl.when(pl.col("split") == "development_train")
        .then(((pl.col("sampling_order_within_split") - 1) // batch_development) + 1)
        .otherwise(((pl.col("sampling_order_within_split") - 1) // batch_holdout) + 1)
        .cast(pl.Int64)
        .alias("reserve_batch")
    )
    lookup_columns = [
        "sampling_role",
        "sampling_order_within_split",
        "reserve_batch",
        "split",
        "composition_key",
        "spotify_row_id",
        "track_id",
        "artist_name_raw",
        "track_name_raw",
        "title_base_query",
        "duration_ms",
        *VERSION_FLAGS,
    ]
    main = main.with_columns(pl.lit(None, dtype=pl.Int64).alias("reserve_batch"))
    combined = pl.concat([main, reserve], how="diagonal_relaxed")
    lookup = (
        combined.select(lookup_columns)
        .rename(
            {
                "spotify_row_id": "representative_spotify_row_id",
                "track_id": "representative_track_id",
                "artist_name_raw": "artist_name_query",
                "track_name_raw": "track_name_query",
            }
        )
        .with_columns(
            pl.lit(None, dtype=pl.String).alias("album_name_query"),
            (pl.col("duration_ms").cast(pl.Float64) / 1000).alias("duration_seconds"),
        )
    )
    if FORBIDDEN_SAMPLING_COLUMNS & set(lookup.columns):
        raise AssertionError("Lookup final contém alvo ou proxy proibido.")
    outputs = config["private_outputs"]
    _atomic_write_frame(main, outputs["cohort"])
    _atomic_write_frame(reserve, outputs["reserve"])
    _atomic_write_frame(lookup, outputs["lookup"])
    representativity = build_representativity(representatives, main)
    cohort_path = project_path(outputs["cohort"])
    reserve_path = project_path(outputs["reserve"])
    summary: dict[str, Any] = {
        "status": "protocol_prepared_collection_not_started",
        "protocol_version": PROTOCOL_VERSION,
        "scale_version": SCALE_VERSION,
        "timestamp": utc_now(),
        "git_parent_before_protocol_checkpoint": git_commit(),
        "planned_checkpoint_tag": "final-study-protocol-v1.0",
        "seed": SEED,
        "target_loaded_for_sampling": False,
        "holdout_target_loaded": False,
        "collection_started": False,
        "first_request_at": None,
        "representative_uses_popularity": False,
        "sampling_uses_popularity_or_success_proxy": False,
        "universe": universe_audit,
        "sampling": {
            "main_total": main.height,
            "main_by_split": {
                row["split"]: row["len"]
                for row in main.group_by("split").len().sort("split").to_dicts()
            },
            "reserve_total": reserve.height,
            "reserve_by_split": {
                row["split"]: row["len"]
                for row in reserve.group_by("split").len().sort("split").to_dicts()
            },
            "main_reserve_overlap": len(
                set(main.get_column("composition_key")) & set(reserve.get_column("composition_key"))
            ),
            "reserve_batches": {
                str(row["reserve_batch"]): int(row["len"])
                for row in reserve.group_by("reserve_batch").len().sort("reserve_batch").to_dicts()
            },
        },
        "private_artifact_hashes": {
            "cohort_sha256": sha256_file(cohort_path),
            "reserve_sha256": sha256_file(reserve_path),
            "cohort_logical_sha256": _hash_frame(main),
            "reserve_logical_sha256": _hash_frame(reserve),
        },
        "representativity": representativity,
        "frozen_hashes": frozen,
        "privacy": {
            "individual_lists_public": False,
            "target_columns_loaded": [],
            "private_files": _git_private_files(),
        },
    }
    if summary["sampling"] != {
        **summary["sampling"],
        "main_total": 14000,
        "reserve_total": 2000,
    }:
        raise AssertionError("Cardinalidades finais inesperadas.")
    if summary["sampling"]["main_by_split"] != main_counts:
        raise AssertionError("Cardinalidade da coorte por split divergente.")
    if summary["sampling"]["reserve_by_split"] != reserve_counts:
        raise AssertionError("Cardinalidade da reserva por split divergente.")
    private = summary["privacy"]["private_files"]
    if private["tracked"] or private["staged"]:
        raise AssertionError("Arquivo privado tracked ou staged.")
    public = config["public_outputs"]
    _write_text(public["analysis_protocol"], _analysis_protocol())
    _write_text(public["sampling_protocol"], _sampling_protocol(summary))
    _write_text(public["sampling_report"], _sampling_report(summary))
    write_json(public["protocol_summary"], summary)
    return summary


def seal_precollection_checkpoint_v040(
    checkpoint_commit: str,
    checkpoint_tag: str,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    """Registra o estado imediatamente anterior à primeira requisição, em área privada."""

    config = load_yaml(config_path)
    summary = json.loads(
        project_path(config["public_outputs"]["protocol_summary"]).read_text(encoding="utf-8")
    )
    cohort = project_path(config["private_outputs"]["cohort"])
    reserve = project_path(config["private_outputs"]["reserve"])
    if sha256_file(cohort) != summary["private_artifact_hashes"]["cohort_sha256"]:
        raise AssertionError("Hash da coorte mudou antes da coleta.")
    if sha256_file(reserve) != summary["private_artifact_hashes"]["reserve_sha256"]:
        raise AssertionError("Hash da reserva mudou antes da coleta.")
    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    seal = {
        "protocol_version": PROTOCOL_VERSION,
        "sealed_at": utc_now(),
        "checkpoint_commit": checkpoint_commit,
        "checkpoint_tag": checkpoint_tag,
        "cohort_sha256": sha256_file(cohort),
        "reserve_sha256": sha256_file(reserve),
        "git_status_entries": status,
        "first_request_at": None,
        "holdout_target_loaded": False,
    }
    write_json(config["private_outputs"]["precollection_seal"], seal)
    return seal
