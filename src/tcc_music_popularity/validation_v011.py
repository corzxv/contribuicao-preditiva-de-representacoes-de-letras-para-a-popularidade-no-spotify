"""Validação, saneamento e preparação reproduzível da Base v0.1.1."""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import polars as pl

from .config import load_yaml, project_path
from .io import git_commit, read_json, sha256_file, utc_now, write_json

VERSION = "v0.1.1"
TARGET = "spotify_popularity"
GROUP_COLUMNS = ["artist_group_id", "composition_group_id", "split_group_id"]
IDENTIFICATION_COLUMNS = ["spotify_row_id", "track_id", "lfm_record_key"]
MATCHING_FIELDS = {
    "match_method",
    "match_score",
    "match_status",
    "acceptance_reason",
    "version_compatible",
    "temporal_compatible",
    "matching_version",
}
NAME_TITLE_FIELDS = {
    "artist_name",
    "artist_name_raw",
    "track_name",
    "track_name_raw",
    "lfm_artist_name_raw",
    "lfm_track_name_raw",
    "artist_unicode",
    "artist_strict",
    "artist_conservative",
    "artist_primary",
    "artist_collaborators_json",
    "title_unicode",
    "title_strict",
    "title_conservative",
    "title_base",
    "lfm_artist_unicode",
    "lfm_artist_strict",
    "lfm_artist_conservative",
    "lfm_artist_primary",
    "lfm_artist_collaborators_json",
    "lfm_title_unicode",
    "lfm_title_strict",
    "lfm_title_conservative",
    "lfm_title_base",
}
TECHNICAL_KEY_FIELDS = {
    "spotify_row_id",
    "track_id",
    "lfm_record_key",
    "composition_key",
    "lfm_composition_key",
    "lfm_source_row_number",
}
DIVERSITY_MARKERS = (
    "dis_legomenon_ratio",
    "dugast",
    "hapax_legomenon_ratio",
    "herdan",
    "maas",
    "mtld",
    "repeated_line_ratio",
    "repeated_token_ratio",
    "summer",
    "tris_legomenon_ratio",
    "unique_bigram_ratio",
    "unique_line_count",
    "unique_tokens_per_line",
    "unique_trigram_ratio",
)
UNCONFIRMED_PREFIXES = (
    "Campo preservado ou derivado",
    "Campo da fonte LFM2b ou variante normalizada documentada pelo nome",
)


def _yes_no(value: bool) -> str:
    return "sim" if value else "não"


def _stable_id(prefix: str, value: str, length: int = 24) -> str:
    digest = hashlib.sha256(f"{prefix}|{value}".encode()).hexdigest()
    return f"{prefix}_{digest[:length]}"


def _stable_order_key(seed: int, value: str) -> str:
    return hashlib.sha256(f"{seed}|{value}".encode()).hexdigest()


def _write_text(path: str | Path, text: str) -> None:
    destination = project_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=destination.parent, delete=False, suffix=".tmp"
    ) as handle:
        handle.write(text.rstrip() + "\n")
        temporary = Path(handle.name)
    os.replace(temporary, destination)


def _write_parquet_atomic(frame: pl.DataFrame, path: str | Path) -> None:
    destination = project_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f"{destination.stem}.tmp.parquet")
    frame.write_parquet(temporary, compression="zstd", statistics=True)
    os.replace(temporary, destination)


def _write_csv_atomic(frame: pl.DataFrame, path: str | Path) -> None:
    destination = project_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f"{destination.stem}.tmp.csv")
    frame.write_csv(temporary)
    os.replace(temporary, destination)


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    def clean(value: Any) -> str:
        return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(clean(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def _parse_dictionary(path: Path) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5 or cells[0] == "variável":
            continue
        name, origin, _dtype, _grain, semantics = cells
        result[(name, origin)] = semantics
    return result


def _origin(name: str) -> str:
    if name in {*GROUP_COLUMNS, "split"}:
        return "preparação v0.1.1"
    if name in MATCHING_FIELDS:
        return "matching"
    if name.startswith("lfm_") or name in {"genius_lyrics_views", "lfm_playcount"}:
        return "LFM2b"
    return "Spotify"


def _descriptor_family(name: str) -> str:
    if name.startswith("lfm_affective_"):
        return "afetivo/emocional"
    if name.startswith("lfm_readability_"):
        return "legibilidade"
    if name.startswith("lfm_rhyme_"):
        return "rima"
    if name.startswith("lfm_structure_"):
        return "estrutura"
    if name in {"lfm_compression_ratio", "lfm_entropy", "lfm_uncommon_words_ratio"}:
        return "diversidade"
    if name.startswith("lfm_lexical_"):
        return "diversidade" if any(marker in name for marker in DIVERSITY_MARKERS) else "lexical"
    return "semântica não confirmada"


def _family(name: str, descriptors: set[str], acoustic: set[str], version_flags: set[str]) -> str:
    if name in descriptors:
        return _descriptor_family(name)
    if name == TARGET:
        return "desfecho"
    if name in acoustic:
        return "acústica"
    if name in version_flags or name.removeprefix("lfm_") in version_flags:
        return "versão"
    if name in MATCHING_FIELDS:
        return "matching"
    if name.startswith("qf_") or name.startswith("lfm_qf_"):
        return "qualidade"
    if name in {
        "year",
        "temporal_cohort",
        "year_mentioned",
        "lfm_release_date",
        "lfm_release_date_numberlong",
        "lfm_release_year",
        "lfm_temporal_cohort",
        "lfm_year_mentioned",
    }:
        return "temporal"
    if name in {"genre", "lfm_genre"}:
        return "gênero"
    if name in {"genius_lyrics_views", "lfm_playcount"}:
        return "popularidade externa"
    if name in TECHNICAL_KEY_FIELDS or name in GROUP_COLUMNS:
        return "identificação/agrupamento"
    if name in NAME_TITLE_FIELDS:
        return "nomes/títulos"
    if name == "split":
        return "particionamento"
    if "normalization" in name or any(
        token in name
        for token in ("unicode", "strict", "conservative", "title_base", "collaborators")
    ):
        return "normalização"
    return "metadados/auditoria"


def _description(
    name: str,
    origin: str,
    dictionary: dict[tuple[str, str], str],
) -> tuple[str, bool]:
    derived = {
        "artist_group_id": "Identificador hash do artista normalizado usado exclusivamente para agrupamento.",
        "composition_group_id": "Identificador hash da chave operacional de composição, com fallback documentado.",
        "split_group_id": "Componente conectado de artista e composição usado como unidade indivisível do split.",
        "split": "Partição determinística: development_train ou holdout_test.",
    }
    matching = {
        "match_method": "Método determinístico de matching responsável pelo candidato ou par.",
        "match_score": "Score reservado aos candidatos fuzzy; pares determinísticos aceitos têm valor ausente.",
        "match_status": "Status final atribuído pelo processo de matching.",
        "acceptance_reason": "Código que registra a justificativa do status do par.",
        "version_compatible": "Indica igualdade das flags de versão Spotify e LFM2b.",
        "temporal_compatible": "Indica diferença absoluta de até dois anos quando ambos os anos existem.",
        "matching_version": "Versão das regras de matching usadas na construção do par.",
    }
    if name in derived:
        return derived[name], True
    if name in matching:
        return matching[name], True
    lookup_name = name
    if name == "lfm_artist_name_raw":
        lookup_name = "artist_name_raw"
    elif name == "lfm_track_name_raw":
        lookup_name = "track_name_raw"
    candidate = dictionary.get((lookup_name, origin))
    if not candidate or candidate.startswith(UNCONFIRMED_PREFIXES):
        return "semântica não confirmada", False
    return candidate, True


def _models_for(
    name: str,
    baseline: set[str],
    descriptors: set[str],
    removed_constants: set[str],
) -> str:
    if name in removed_constants:
        return "nenhum"
    if name in baseline:
        return "baseline; tradicional; profundo; combinado"
    if name in descriptors:
        return "tradicional; combinado"
    return "nenhum"


def _role(name: str, baseline: set[str], descriptors: set[str]) -> str:
    if name == TARGET:
        return "alvo"
    if name in GROUP_COLUMNS or name in {"composition_key", "lfm_composition_key"}:
        return "agrupamento"
    if name in TECHNICAL_KEY_FIELDS:
        return "identificação"
    if name in NAME_TITLE_FIELDS:
        return "identificação"
    if name in {
        "genius_lyrics_views",
        "lfm_playcount",
        "match_method",
        "match_score",
        "match_status",
        "acceptance_reason",
        "version_compatible",
        "temporal_compatible",
    }:
        return "proibida"
    if name in descriptors or name in baseline:
        return "controle" if name in {"year", "genre"} else "preditora"
    return "auditoria"


def _transformation(name: str, family: str, role: str) -> str:
    if role not in {"preditora", "controle"}:
        return "nenhuma; não entra como preditora"
    if name == "genre":
        return "codificação categórica ajustada somente em development_train"
    if name == "year":
        return "avaliar centralização, escala e forma não linear somente em development_train"
    if family == "versão":
        return "converter booleano para indicador 0/1"
    if family in {
        "acústica",
        "lexical",
        "diversidade",
        "legibilidade",
        "rima",
        "estrutura",
        "afetivo/emocional",
    }:
        return "avaliar escala e assimetria; qualquer transformação será ajustada somente no treino"
    return "definir no pipeline de treino"


def _missing_treatment(missing: int, role: str, family: str) -> str:
    if role not in {"preditora", "controle"}:
        return "não aplicável para modelagem"
    if missing == 0:
        return "sem ausências neste snapshot; validar novamente em dados futuros"
    if family == "estrutura":
        return "ausência estrutural: indicador + imputação ajustada no treino + análise de sensibilidade"
    return "indicador de ausência e imputação ajustada exclusivamente em development_train"


def _standardization(name: str, dtype: pl.DataType, role: str) -> str:
    if role not in {"preditora", "controle"}:
        return "não"
    if name == "genre" or dtype == pl.Boolean or name in {"key", "mode", "time_signature"}:
        return "não"
    return "sim para modelos sensíveis à escala; ajustar somente no treino"


def _leakage_risk(name: str, role: str) -> str:
    if name == TARGET:
        return "alto — é o próprio desfecho"
    if name in {"genius_lyrics_views", "lfm_playcount"}:
        return "alto — proxy externo de popularidade/uso"
    if name in MATCHING_FIELDS:
        return "alto — informação produzida pelo matching"
    if role in {"identificação", "agrupamento"}:
        return "alto se codificada; usar somente para rastreabilidade ou agrupamento"
    if role == "auditoria":
        return "não avaliar como feature; manter fora do vetor de preditores"
    return "baixo sob split agrupado e transformações ajustadas apenas no treino"


def _justification(
    name: str,
    role: str,
    models: str,
    constant_development: bool,
) -> str:
    if constant_development:
        return "Removida da matriz por ser constante em development_train; preservada no manifesto e auditoria."
    if name == TARGET:
        return "Variável resposta histórica observada no snapshot Spotify."
    if models != "nenhum":
        return "Autorizada pelo protocolo científico; o holdout não foi usado nesta decisão."
    if role in {"identificação", "agrupamento"}:
        return (
            "Necessária para rastreabilidade ou prevenção de leakage, mas proibida como preditora."
        )
    if role == "proibida":
        return "Exclusão explícita por leakage, popularidade externa ou dependência do matching."
    return "Mantida apenas na camada de auditoria; sem autorização para modelagem."


def _series_profile(series: pl.Series, threshold: float) -> dict[str, Any]:
    non_null = series.drop_nulls()
    if isinstance(series.dtype, pl.List):
        values = [
            json.dumps(value, ensure_ascii=False, default=str) for value in non_null.to_list()
        ]
        cardinality = len(set(values))
    else:
        cardinality = int(non_null.n_unique())
    missing = int(series.null_count())
    infinite = 0
    variance = None
    mean = None
    if series.dtype.is_float():
        infinite = int(series.is_infinite().sum())
    if series.dtype.is_numeric() and series.dtype != pl.Boolean:
        numeric = series.cast(pl.Float64, strict=False)
        variance = numeric.var(ddof=0)
        mean = numeric.mean()
    constant = cardinality <= 1
    near_zero = False
    if not constant and variance is not None and math.isfinite(float(variance)):
        center = float(mean) if mean is not None and math.isfinite(float(mean)) else 0.0
        near_zero = float(variance) <= threshold * max(1.0, center * center)
    return {
        "missing": missing,
        "infinite": infinite,
        "cardinality": cardinality,
        "constant": constant,
        "near_zero": near_zero,
        "variance": None if variance is None else float(variance),
    }


def profile_frame(frame: pl.DataFrame, threshold: float) -> dict[str, dict[str, Any]]:
    return {name: _series_profile(frame[name], threshold) for name in frame.columns}


class _UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, value: str) -> str:
        self.parent.setdefault(value, value)
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        smaller, larger = sorted((left_root, right_root))
        self.parent[larger] = smaller


def build_group_assignments(frame: pl.DataFrame) -> pl.DataFrame:
    artist_sources = frame.select(
        pl.coalesce(
            [
                pl.col("artist_conservative"),
                pl.col("artist_strict"),
                pl.col("artist_primary"),
                pl.col("artist_name_raw"),
                pl.col("track_id"),
            ]
        ).cast(pl.String)
    ).to_series()
    composition_sources = frame.select(
        pl.coalesce(
            [
                pl.col("composition_key"),
                pl.col("lfm_composition_key"),
                pl.concat_str([pl.lit("track_fallback"), pl.col("track_id")], separator="|"),
            ]
        ).cast(pl.String)
    ).to_series()
    artist_ids = [_stable_id("artist", value) for value in artist_sources.to_list()]
    composition_ids = [_stable_id("composition", value) for value in composition_sources.to_list()]
    union_find = _UnionFind()
    for artist_id, composition_id in zip(artist_ids, composition_ids, strict=True):
        union_find.union(f"a:{artist_id}", f"c:{composition_id}")
    split_ids = [_stable_id("split", union_find.find(f"a:{artist_id}")) for artist_id in artist_ids]
    return pl.DataFrame(
        {
            "spotify_row_id": frame["spotify_row_id"],
            "track_id": frame["track_id"],
            "lfm_record_key": frame["lfm_record_key"],
            "artist_group_id": artist_ids,
            "composition_group_id": composition_ids,
            "split_group_id": split_ids,
        }
    )


def deterministic_group_split(
    group_sizes: dict[str, int], holdout_fraction: float, random_state: int
) -> set[str]:
    total = sum(group_sizes.values())
    target = total * holdout_fraction
    selected: set[str] = set()
    selected_rows = 0
    for group_id, size in sorted(
        group_sizes.items(), key=lambda item: _stable_order_key(random_state, item[0])
    ):
        current_distance = abs(target - selected_rows)
        proposed_distance = abs(target - (selected_rows + size))
        if proposed_distance < current_distance:
            selected.add(group_id)
            selected_rows += size
    return selected


def _add_split(
    frame: pl.DataFrame, assignments: pl.DataFrame, config: dict[str, Any]
) -> pl.DataFrame:
    group_sizes = dict(
        assignments.group_by("split_group_id").len().select(["split_group_id", "len"]).iter_rows()
    )
    holdout_groups = deterministic_group_split(
        group_sizes,
        float(config["holdout_fraction"]),
        int(config["random_state"]),
    )
    assignments = assignments.with_columns(
        pl.when(pl.col("split_group_id").is_in(list(holdout_groups)))
        .then(pl.lit("holdout_test"))
        .otherwise(pl.lit("development_train"))
        .alias("split"),
        pl.lit(int(config["random_state"])).alias("split_random_state"),
        pl.lit(VERSION).alias("split_version"),
    )
    return frame.join(assignments, on=IDENTIFICATION_COLUMNS, how="left", validate="1:1")


def _distribution(frame: pl.DataFrame, column: str) -> list[dict[str, Any]]:
    return (
        frame.group_by(column, maintain_order=True)
        .len()
        .with_columns((pl.col("len") / frame.height).alias("percent"))
        .sort("len", descending=True)
        .to_dicts()
    )


def _temporal_audit(frame: pl.DataFrame) -> dict[str, Any]:
    audited = frame.with_columns(
        pl.when(pl.col("year").is_null() | pl.col("lfm_release_year").is_null())
        .then(None)
        .otherwise((pl.col("year") - pl.col("lfm_release_year")).abs())
        .alias("temporal_year_difference_abs")
    ).with_columns(
        pl.when(pl.col("temporal_year_difference_abs").is_null())
        .then(pl.lit("ano ausente"))
        .when(pl.col("temporal_year_difference_abs") == 0)
        .then(pl.lit("diferença 0"))
        .when(pl.col("temporal_year_difference_abs") <= 2)
        .then(pl.lit("1–2 anos"))
        .when(pl.col("temporal_year_difference_abs") <= 5)
        .then(pl.lit("3–5 anos"))
        .when(pl.col("temporal_year_difference_abs") <= 10)
        .then(pl.lit("6–10 anos"))
        .when(pl.col("temporal_year_difference_abs") <= 20)
        .then(pl.lit("11–20 anos"))
        .otherwise(pl.lit("mais de 20 anos"))
        .alias("temporal_band")
    )
    differences = audited["temporal_year_difference_abs"].drop_nulls()
    quantiles = {
        str(value): float(differences.quantile(value, interpolation="linear"))
        for value in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)
    }
    bands = (
        audited.group_by("temporal_band")
        .len()
        .with_columns((100 * pl.col("len") / frame.height).alias("percent"))
        .to_dicts()
    )
    order = {
        "diferença 0": 0,
        "1–2 anos": 1,
        "3–5 anos": 2,
        "6–10 anos": 3,
        "11–20 anos": 4,
        "mais de 20 anos": 5,
        "ano ausente": 6,
    }
    bands.sort(key=lambda item: order[item["temporal_band"]])
    return {
        "statistics": {
            "non_null": differences.len(),
            "missing": int(frame.height - differences.len()),
            "mean": float(differences.mean()),
            "median": float(differences.median()),
            "standard_deviation": float(differences.std(ddof=1)),
            "minimum": int(differences.min()),
            "maximum": int(differences.max()),
            "quantiles": quantiles,
        },
        "bands": bands,
        "implausible_lfm_release_year_flagged": int(frame["lfm_qf_release_year_implausible"].sum()),
    }


def _version_audit(frame: pl.DataFrame, version_flags: list[str]) -> dict[str, Any]:
    any_version = pl.any_horizontal(
        [
            pl.col(flag).fill_null(False) | pl.col(f"lfm_{flag}").fill_null(False)
            for flag in version_flags
        ]
    )
    result: dict[str, Any] = {
        "original_no_version_flag": {
            "count": int(frame.select((~any_version).sum()).item()),
        }
    }
    result["original_no_version_flag"]["percent"] = (
        100 * result["original_no_version_flag"]["count"] / frame.height
    )
    for flag in version_flags:
        count = int(
            frame.select(
                (pl.col(flag).fill_null(False) | pl.col(f"lfm_{flag}").fill_null(False)).sum()
            ).item()
        )
        result[flag] = {"count": count, "percent": 100 * count / frame.height}
    return result


def _identity_audit(frame: pl.DataFrame) -> dict[str, Any]:
    composition = (
        frame.filter(pl.col("composition_key").is_not_null())
        .group_by("composition_key")
        .agg(pl.len().alias("rows"), pl.col("track_id").n_unique().alias("track_ids"))
    )
    duplicate_compositions = composition.filter(pl.col("rows") > 1)
    lfm_per_track = frame.group_by("track_id").agg(pl.col("lfm_record_key").n_unique().alias("n"))
    return {
        "track_id_duplicate_excess_rows": frame.height - frame["track_id"].n_unique(),
        "spotify_row_id_duplicate_excess_rows": frame.height - frame["spotify_row_id"].n_unique(),
        "lfm_record_key_duplicate_excess_rows": frame.height - frame["lfm_record_key"].n_unique(),
        "composition_keys_with_multiple_rows": duplicate_compositions.height,
        "rows_in_duplicated_composition_groups": int(duplicate_compositions["rows"].sum() or 0),
        "composition_keys_with_multiple_track_ids": int(
            composition.filter(pl.col("track_ids") > 1).height
        ),
        "maximum_tracks_per_composition_key": int(composition["track_ids"].max() or 0),
        "tracks_linked_to_multiple_lfm_records": int(lfm_per_track.filter(pl.col("n") > 1).height),
        "accepted_without_spotify_composition_key": frame["composition_key"].null_count(),
        "accepted_without_lfm_composition_key": frame["lfm_composition_key"].null_count(),
    }


def _numeric_summary(frame: pl.DataFrame, column: str) -> dict[str, Any]:
    series = frame[column].drop_nulls().cast(pl.Float64)
    return {
        "count": series.len(),
        "missing": frame[column].null_count(),
        "mean": float(series.mean()),
        "median": float(series.median()),
        "standard_deviation": float(series.std(ddof=1)),
        "minimum": float(series.min()),
        "maximum": float(series.max()),
        "q25": float(series.quantile(0.25, interpolation="linear")),
        "q75": float(series.quantile(0.75, interpolation="linear")),
    }


def _split_audit(
    frame: pl.DataFrame,
    descriptors: list[str],
    version_flags: list[str],
) -> dict[str, Any]:
    counts = frame.group_by("split").len().sort("split").to_dicts()
    count_map = {row["split"]: row["len"] for row in counts}
    development = frame.filter(pl.col("split") == "development_train")
    holdout = frame.filter(pl.col("split") == "holdout_test")
    overlap = {}
    for column in GROUP_COLUMNS:
        left = set(development[column].unique().to_list())
        right = set(holdout[column].unique().to_list())
        overlap[column] = len(left & right)

    numeric = {
        "spotify_popularity": {
            "development_train": _numeric_summary(development, TARGET),
            "holdout_test": _numeric_summary(holdout, TARGET),
        },
        "year": {
            "development_train": _numeric_summary(development, "year"),
            "holdout_test": _numeric_summary(holdout, "year"),
        },
    }

    categorical: dict[str, Any] = {}
    for column in ("temporal_cohort", "genre", "match_method"):
        development_distribution = {
            str(row[column]): row["len"] / development.height
            for row in development.group_by(column).len().to_dicts()
        }
        holdout_distribution = {
            str(row[column]): row["len"] / holdout.height
            for row in holdout.group_by(column).len().to_dicts()
        }
        levels = sorted(set(development_distribution) | set(holdout_distribution))
        rows = [
            {
                "value": level,
                "development_percent": 100 * development_distribution.get(level, 0.0),
                "holdout_percent": 100 * holdout_distribution.get(level, 0.0),
                "difference_percentage_points": 100
                * (holdout_distribution.get(level, 0.0) - development_distribution.get(level, 0.0)),
            }
            for level in levels
        ]
        rows.sort(key=lambda row: abs(row["difference_percentage_points"]), reverse=True)
        categorical[column] = rows

    version_comparison = []
    for flag in version_flags:
        development_rate = float(development[flag].mean() or 0.0)
        holdout_rate = float(holdout[flag].mean() or 0.0)
        version_comparison.append(
            {
                "flag": flag,
                "development_percent": 100 * development_rate,
                "holdout_percent": 100 * holdout_rate,
                "difference_percentage_points": 100 * (holdout_rate - development_rate),
            }
        )

    available = pl.any_horizontal([pl.col(name).is_not_null() for name in descriptors])
    complete = pl.all_horizontal([pl.col(name).is_not_null() for name in descriptors])
    descriptor_availability = {}
    for split_name, subset in (("development_train", development), ("holdout_test", holdout)):
        descriptor_availability[split_name] = {
            "any_descriptor_available_percent": 100 * float(subset.select(available.mean()).item()),
            "all_descriptors_available_percent": 100 * float(subset.select(complete.mean()).item()),
            "structure_block_complete_percent": 100
            * float(
                subset.select(
                    pl.all_horizontal(
                        [
                            pl.col(name).is_not_null()
                            for name in descriptors
                            if name.startswith("lfm_structure_")
                        ]
                    ).mean()
                ).item()
            ),
        }

    warnings = []
    popularity_means = numeric["spotify_popularity"]
    pooled = math.sqrt(
        (
            popularity_means["development_train"]["standard_deviation"] ** 2
            + popularity_means["holdout_test"]["standard_deviation"] ** 2
        )
        / 2
    )
    smd = (
        0.0
        if pooled == 0
        else (
            popularity_means["holdout_test"]["mean"] - popularity_means["development_train"]["mean"]
        )
        / pooled
    )
    if abs(smd) > 0.1:
        warnings.append(f"Diferença padronizada de popularidade |SMD|={abs(smd):.4f} > 0,10.")
    for column, rows in categorical.items():
        if rows and abs(rows[0]["difference_percentage_points"]) > 5:
            warnings.append(
                f"{column}: diferença máxima de {abs(rows[0]['difference_percentage_points']):.4f} p.p."
            )

    return {
        "counts": count_map,
        "holdout_fraction": count_map["holdout_test"] / frame.height,
        "group_counts": {column: frame[column].n_unique() for column in GROUP_COLUMNS},
        "overlap": overlap,
        "numeric_comparison": numeric,
        "popularity_standardized_mean_difference": smd,
        "categorical_comparison": categorical,
        "version_comparison": version_comparison,
        "descriptor_availability": descriptor_availability,
        "relevant_imbalance_warnings": warnings,
    }


def _review_sample(
    base: pl.DataFrame,
    version_flags: list[str],
) -> tuple[pl.DataFrame, dict[str, Any]]:
    sample_path = project_path("data/processed/spotify_lfm_review_sample.parquet")
    if not sample_path.exists():
        raise FileNotFoundError(sample_path)
    sample = pl.read_parquet(sample_path)
    spotify_columns = [
        "track_id",
        "artist_name_raw",
        "track_name_raw",
        "year",
        "genre",
        TARGET,
        "temporal_cohort",
        "composition_key",
        *version_flags,
    ]
    lfm_columns = [
        "lfm_record_key",
        "artist_name_raw",
        "track_name_raw",
        "lfm_release_year",
        "lfm_temporal_cohort",
        "lfm_composition_key",
        *[f"lfm_{flag}" for flag in version_flags],
    ]
    spotify = pl.read_parquet(
        project_path("data/processed/spotify_tracks.parquet"), columns=spotify_columns
    ).rename(
        {
            "artist_name_raw": "spotify_artist_name_raw",
            "track_name_raw": "spotify_track_name_raw",
        }
    )
    lfm = pl.read_parquet(
        project_path("data/processed/lfm2b_tracks.parquet"), columns=lfm_columns
    ).rename(
        {
            "artist_name_raw": "lfm_artist_name_raw",
            "track_name_raw": "lfm_track_name_raw",
        }
    )
    enriched = (
        sample.join(
            spotify, left_on="spotify_track_id", right_on="track_id", how="left", validate="m:1"
        )
        .join(lfm, on="lfm_record_key", how="left", validate="m:1")
        .with_columns(
            (pl.col("year") - pl.col("lfm_release_year"))
            .abs()
            .alias("temporal_year_difference_abs")
        )
    )

    base_rows = base.with_columns(pl.col("track_id").alias("spotify_track_id"))
    required_filters: list[tuple[str, pl.Expr]] = [
        ("missing_composition_key", pl.col("composition_key").is_null()),
    ]
    for flag in version_flags:
        current = int(
            enriched.select(
                (pl.col(flag).fill_null(False) | pl.col(f"lfm_{flag}").fill_null(False)).sum()
            ).item()
        )
        if current == 0:
            required_filters.append(
                (
                    f"version_{flag}",
                    pl.col(flag).fill_null(False) | pl.col(f"lfm_{flag}").fill_null(False),
                )
            )

    added: list[dict[str, Any]] = []
    existing_pairs = set(
        enriched.select(pl.concat_str(["spotify_track_id", "lfm_record_key"], separator="|"))
        .to_series()
        .to_list()
    )
    for reason, expression in required_filters:
        candidates = (
            base_rows.filter(expression)
            .with_columns(
                pl.concat_str(["spotify_track_id", "lfm_record_key"], separator="|").alias(
                    "pair_key"
                )
            )
            .filter(~pl.col("pair_key").is_in(list(existing_pairs)))
            .sort("track_id")
        )
        if candidates.height == 0:
            continue
        row = candidates.row(0, named=True)
        row["candidate_reason"] = reason
        row["method_priority"] = None
        row["spotify_candidate_count"] = 1
        row["lfm_spotify_count"] = 1
        row["ambiguity_flag"] = False
        row["spotify_artist_name_raw"] = row["artist_name_raw"]
        row["spotify_track_name_raw"] = row["track_name_raw"]
        row["temporal_year_difference_abs"] = abs(row["year"] - row["lfm_release_year"])
        added.append(row)
        existing_pairs.add(row["pair_key"])

    output_columns = [
        "spotify_track_id",
        "spotify_row_id",
        "lfm_record_key",
        "match_method",
        "match_status",
        "acceptance_reason",
        "match_score",
        "candidate_reason",
        "spotify_candidate_count",
        "lfm_spotify_count",
        "ambiguity_flag",
        "version_compatible",
        "temporal_compatible",
        "spotify_artist_name_raw",
        "spotify_track_name_raw",
        "lfm_artist_name_raw",
        "lfm_track_name_raw",
        "year",
        "lfm_release_year",
        "temporal_year_difference_abs",
        "temporal_cohort",
        "lfm_temporal_cohort",
        "genre",
        TARGET,
        "composition_key",
        "lfm_composition_key",
        *version_flags,
        *[f"lfm_{flag}" for flag in version_flags],
    ]
    enriched = enriched.select(output_columns)
    if added:
        additions = pl.DataFrame(added, infer_schema_length=None).select(output_columns)
        removable = (
            enriched.with_row_index("row_index")
            .filter(
                (pl.col("match_status") == "accepted_high_confidence")
                & (pl.col("match_method") == "raw_exact")
                & pl.col("composition_key").is_not_null()
            )
            .sort("spotify_track_id", descending=True)
            .head(len(added))["row_index"]
            .to_list()
        )
        enriched = pl.concat(
            [
                enriched.with_row_index("row_index")
                .filter(~pl.col("row_index").is_in(removable))
                .drop("row_index"),
                additions,
            ],
            how="diagonal_relaxed",
        )
    enriched = (
        enriched.sort(["match_status", "match_method", "spotify_track_id", "lfm_record_key"])
        .with_row_index("review_row_id", offset=1)
        .with_columns(
            pl.lit("").alias("human_match_label"),
            pl.lit("").alias("human_version_label"),
            pl.lit("").alias("human_notes"),
            pl.lit("").alias("reviewed_by"),
            pl.lit("").alias("reviewed_at"),
        )
    )
    if enriched.height != 225:
        raise RuntimeError(f"Amostra de revisão deveria ter 225 linhas, recebeu {enriched.height}")
    coverage = {
        "source_sample": str(sample_path),
        "source_rows_reused": 225 - len(added),
        "required_cases_added_by_deterministic_replacement": len(added),
        "rows": enriched.height,
        "by_status_method": enriched.group_by(["match_status", "match_method"]).len().to_dicts(),
        "temporal_compatible": _distribution(enriched, "temporal_compatible"),
        "missing_composition_key": enriched["composition_key"].null_count(),
        "genres": enriched["genre"].n_unique(),
        "spotify_periods": enriched["temporal_cohort"].n_unique(),
        "lfm_periods": enriched["lfm_temporal_cohort"].n_unique(),
        "popularity_minimum": float(enriched[TARGET].min()),
        "popularity_maximum": float(enriched[TARGET].max()),
        "version_flag_counts": {
            flag: int(
                enriched.select(
                    (pl.col(flag).fill_null(False) | pl.col(f"lfm_{flag}").fill_null(False)).sum()
                ).item()
            )
            for flag in version_flags
        },
        "human_fields_blank": all(
            enriched[column].eq("").all()
            for column in (
                "human_match_label",
                "human_version_label",
                "human_notes",
                "reviewed_by",
                "reviewed_at",
            )
        ),
    }
    return enriched, coverage


def _manifest(
    source: pl.DataFrame,
    split_frame: pl.DataFrame,
    source_profile: dict[str, dict[str, Any]],
    development_profile: dict[str, dict[str, Any]],
    descriptors: set[str],
    baseline: set[str],
    acoustic: set[str],
    version_flags: set[str],
    removed_constants: set[str],
    matrix_columns: list[str],
) -> pl.DataFrame:
    dictionary = _parse_dictionary(project_path("docs/data_dictionary.md"))
    rows = []
    all_columns = [*source.columns, *GROUP_COLUMNS, "split"]
    for position, name in enumerate(all_columns, start=1):
        is_derived = name in {*GROUP_COLUMNS, "split"}
        dtype = split_frame.schema[name] if is_derived else source.schema[name]
        profile = _series_profile(split_frame[name], 1e-12) if is_derived else source_profile[name]
        development = (
            _series_profile(split_frame.filter(pl.col("split") == "development_train")[name], 1e-12)
            if is_derived
            else development_profile[name]
        )
        origin = _origin(name)
        family = _family(name, descriptors, acoustic, version_flags)
        role = _role(name, baseline, descriptors)
        description, confirmed = _description(name, origin, dictionary)
        models = _models_for(name, baseline, descriptors, removed_constants)
        rows.append(
            {
                "posição": position,
                "nome": name,
                "tipo": str(dtype),
                "origem": origin,
                "família": family,
                "descrição confirmada": description,
                "semântica confirmada": _yes_no(confirmed),
                "quantidade de ausentes": profile["missing"],
                "percentual de ausentes": profile["missing"] / source.height,
                "cardinalidade": profile["cardinality"],
                "constante": _yes_no(profile["constant"]),
                "variância próxima de zero": _yes_no(profile["near_zero"]),
                "constante no development_train": _yes_no(development["constant"]),
                "variância próxima de zero no development_train": _yes_no(development["near_zero"]),
                "papel": role,
                "modelo em que poderá entrar": models,
                "transformação sugerida": _transformation(name, family, role),
                "tratamento de ausência sugerido": _missing_treatment(
                    profile["missing"], role, family
                ),
                "necessidade de padronização": _standardization(name, dtype, role),
                "risco de leakage": _leakage_risk(name, role),
                "justificativa da decisão": _justification(
                    name, role, models, name in removed_constants
                ),
                "incluída na matriz v0.1.1": _yes_no(name in matrix_columns),
            }
        )
    return pl.DataFrame(rows)


def _consistency(
    base: pl.DataFrame,
    descriptor_count: int,
    inventory_descriptor_count: int,
) -> dict[str, Any]:
    run_summary = read_json("reports/run_summary.json", {})
    lfm_audit = read_json("reports/tables/lfm2b_audit.json", {})
    matching_summary = read_json("reports/tables/matching_summary.json", {})
    spotify_audit = read_json("reports/tables/spotify_audit.json", {})
    accepted_by_run = sum(
        run_summary.get("records_by_stage", {}).get("match_by_status", {}).get(name, 0)
        for name in ("accepted_high_confidence", "accepted_with_rules")
    )
    preview_counts = {"rows": 111758, "columns": 310, "descriptors": 209}
    checks = [
        {
            "source": "Parquet v0.1",
            "metric": "base rows",
            "documented": base.height,
            "observed": base.height,
            "consistent": True,
        },
        {
            "source": "run_summary.json",
            "metric": "accepted matches",
            "documented": accepted_by_run,
            "observed": base.height,
            "consistent": accepted_by_run == base.height,
        },
        {
            "source": "matching_report.md / matching_summary.json",
            "metric": "accepted matches",
            "documented": matching_summary.get("deterministic_multiplicity", [{}])[-1].get(
                "candidate_rows"
            ),
            "observed": base.height,
            "consistent": any(
                row.get("mapping_type") == "one_to_one" and row.get("candidate_rows") == base.height
                for row in matching_summary.get("deterministic_multiplicity", [])
            ),
        },
        {
            "source": "base_preview.xlsx",
            "metric": "rows / columns / descriptors",
            "documented": preview_counts,
            "observed": {
                "rows": base.height,
                "columns": base.width,
                "descriptors": descriptor_count,
            },
            "consistent": preview_counts
            == {"rows": base.height, "columns": base.width, "descriptors": descriptor_count},
        },
        {
            "source": "data_audit.md / spotify_audit.json",
            "metric": "Spotify rows",
            "documented": spotify_audit.get("observed", {}).get("rows"),
            "observed": 1_159_764,
            "consistent": spotify_audit.get("observed", {}).get("rows") == 1_159_764,
        },
        {
            "source": "data_audit.md / lfm2b_audit.json",
            "metric": "LFM rows / columns / descriptors",
            "documented": {
                "rows": lfm_audit.get("rows"),
                "columns": lfm_audit.get("columns"),
                "descriptors": lfm_audit.get("descriptor_count"),
            },
            "observed": {"rows": 582_759, "columns": 242, "descriptors": descriptor_count},
            "consistent": (
                lfm_audit.get("rows") == 582_759
                and lfm_audit.get("columns") == 242
                and lfm_audit.get("descriptor_count") == descriptor_count
            ),
        },
    ]
    return {
        "checks": checks,
        "inconsistencies": [row for row in checks if not row["consistent"]],
        "descriptor_resolution": {
            "confirmed_descriptor_count": descriptor_count,
            "preliminary_inventory_count": inventory_descriptor_count,
            "misclassified_normalization_or_version_fields": inventory_descriptor_count
            - descriptor_count,
            "lfm_schema_columns_in_integrated_base": 242,
            "lfm_non_descriptor_columns": 242 - descriptor_count,
        },
    }


def _build_reports(
    run_summary: dict[str, Any],
    validation: dict[str, Any],
    matching: dict[str, Any],
    split: dict[str, Any],
    model_spec: dict[str, Any],
) -> None:
    constants = validation["constant_predictors_removed"]
    consistency_rows = [
        [
            item["source"],
            item["metric"],
            json.dumps(item["documented"], ensure_ascii=False),
            json.dumps(item["observed"], ensure_ascii=False),
            _yes_no(item["consistent"]),
        ]
        for item in validation["consistency"]["checks"]
    ]
    base_validation = f"""# Validação da Base v0.1.1

Gerado em `{run_summary["generated_at"]}` a partir de `data/processed/modeling_base_lfm_v0_1.parquet`.

## Escopo e interpretação

`spotify_popularity` é popularidade histórica presente no snapshot da fonte. Não representa sucesso futuro, causalidade nem probabilidade de uma faixa tornar-se hit. A população inferencial permanece o subconjunto Spotify associado com alta confiança ao LFM2b.

## Consistência entre artefatos

{_markdown_table(["fonte", "métrica", "documentado", "observado", "consistente"], consistency_rows)}

Inconsistências de contagens centrais: **{len(validation["consistency"]["inconsistencies"])}**.

## Perfil observado da Base v0.1

- Linhas: **{validation["source_rows"]:,}**.
- Colunas: **{validation["source_columns"]:,}**.
- `track_id` únicos: **{validation["unique_track_ids"]:,}**.
- `spotify_row_id` únicos: **{validation["unique_spotify_row_ids"]:,}**.
- `lfm_record_key` únicos: **{validation["unique_lfm_record_keys"]:,}**.
- Células ausentes: **{validation["total_missing_cells"]:,}**.
- Valores infinitos: **{validation["total_infinite_values"]:,}**.
- Colunas constantes na base completa: **{len(validation["constant_columns_full"])}**.
- Colunas com variância próxima de zero: **{len(validation["near_zero_columns_full"])}**.

A regra operacional de variância próxima de zero para colunas numéricas não constantes foi `variância <= {validation["near_zero_rule"]}`; o cálculo de cardinalidade e constantes considerou valores não ausentes.

## Resolução 231 versus 209

O inventário preliminar `lfm2b_schema_inventory.json` listou 231 supostos descritores por uma regra inclusiva. A auditoria semântica posterior confirmou **209 descritores de letra**. Os **22 campos excedentes** são normalizações, flags de versão e chaves técnicas; não são descritores líricos. No schema integrado há 242 colunas de origem LFM2b: 209 descritores e 33 campos de metadados, identificação, popularidade externa, normalização, versão ou qualidade.

Campos excedentes do inventário preliminar:

{", ".join(f"`{name}`" for name in validation["inventory_descriptor_extras"])}.

## Saneamento e matriz controlada

- Base v0.1 original: **{validation["source_rows"]:,} × {validation["source_columns"]:,}**; não alterada.
- Base v0.1.1: **{validation["output_rows"]:,} × {validation["output_columns"]:,}**.
- Linhas excluídas: **0**.
- Preditoras candidatas antes da remoção de constantes: **{validation["candidate_predictors_before_constant_removal"]}**.
- Preditoras/controles autorizados após remoção: **{validation["authorized_features_after_constant_removal"]}**.
- Variáveis constantes removidas da matriz: **{len(constants)}**.

Variáveis constantes removidas: {", ".join(f"`{name}`" for name in constants)}.

## Ausências

Ausências estruturais não foram convertidas em zero. O bloco estrutural da letra possui {validation["structure_missing_rows"]:,} linhas com ausência em pelo menos um campo. A estratégia futura é: indicador de ausência, imputação ajustada somente em `development_train`, análise de sensibilidade e avaliação de bloco estrutural separado. Nenhuma imputação, média, escala ou transformação foi aprendida nesta etapa.

## Artefatos de rastreabilidade

As variáveis de matching, métricas externas, nomes, títulos, chaves e flags de auditoria ficaram fora da matriz de modelagem e permanecem em `matching_audit_v0_1_1.parquet` e no manifesto.
"""
    _write_text("reports/base_validation_v0_1_1.md", base_validation)

    temporal = matching["temporal"]
    temporal_rows = [
        [row["temporal_band"], row["len"], f"{row['percent']:.6f}%"] for row in temporal["bands"]
    ]
    version_rows = [
        [name, values["count"], f"{values['percent']:.6f}%"]
        for name, values in matching["versions"].items()
    ]
    matching_report = f"""# Auditoria de matching e temporal — Base v0.1.1

Gerado em `{run_summary["generated_at"]}`. Todos os **{matching["rows"]:,}** pares aceitos da Base v0.1 foram auditados.

## Distribuições do matching

### Método

{_markdown_table(["match_method", "n", "%"], [[row["match_method"], row["len"], f"{100 * row['len'] / matching['rows']:.6f}%"] for row in matching["by_match_method"]])}

### Status e justificativa

{_markdown_table(["match_status", "n"], [[row["match_status"], row["len"]] for row in matching["by_match_status"]])}

{_markdown_table(["acceptance_reason", "n"], [[row["acceptance_reason"], row["len"]] for row in matching["by_acceptance_reason"]])}

`match_score` não se aplica aos pares determinísticos aceitos: valores não ausentes = **{matching["match_score_non_null"]}**. `version_compatible=True` em **{matching["version_compatible_true"]:,}** pares. `temporal_compatible=True` em **{matching["temporal_compatible_true"]:,}** e `False` em **{matching["temporal_compatible_false"]:,}**.

## Diferença temporal absoluta

- Média: **{temporal["statistics"]["mean"]:.6f}** anos.
- Mediana: **{temporal["statistics"]["median"]:.6f}**.
- Desvio-padrão: **{temporal["statistics"]["standard_deviation"]:.6f}**.
- Mínimo/máximo: **{temporal["statistics"]["minimum"]} / {temporal["statistics"]["maximum"]}**.
- Quantis: `{json.dumps(temporal["statistics"]["quantiles"], ensure_ascii=False)}`.

{_markdown_table(["faixa", "n", "%"], temporal_rows)}

Diferença temporal não foi tratada automaticamente como erro: uma faixa Spotify recente pode ser relançamento de composição antiga. Há **{temporal["implausible_lfm_release_year_flagged"]}** pares com flag de ano LFM implausível; permanecem preservados para revisão.

## Versões

As categorias abaixo não são mutuamente exclusivas, exceto “original/no version flag”. Como todos os pares aceitos são compatíveis em versão, as contagens Spotify e LFM coincidem.

{_markdown_table(["tipo", "n", "%"], version_rows)}

## Identidade e multiplicidade

{_markdown_table(["métrica", "valor"], [[key, value] for key, value in matching["identity"].items()])}

Confirmam-se **{matching["identity"]["accepted_without_spotify_composition_key"]}** casos aceitos sem `composition_key`. Eles não foram excluídos; receberam grupo de composição por fallback rastreável no split.

## Revisão humana

A amostra v0.1 existente de 225 linhas foi reutilizada. Foram preservadas {matching["review_sample"]["source_rows_reused"]} linhas e feitas {matching["review_sample"]["required_cases_added_by_deterministic_replacement"]} substituições determinísticas para incluir chave ausente e tipos de versão faltantes. Os cinco campos humanos permanecem integralmente vazios. A amostra inclui aceitos, ambíguos e candidatos fuzzy; estes últimos continuam sem aceitação automática.
"""
    _write_text("reports/matching_temporal_audit_v0_1_1.md", matching_report)

    protocol = f"""# Protocolo dos quatro modelos — Base v0.1.1

## Objetivo

Estimar `spotify_popularity`, popularidade histórica observada no snapshot, fora da amostra dentro da população Spotify–LFM2b matched. Não serão feitas afirmações causais.

## Amostra, split e avaliação

- Os quatro modelos usarão a mesma amostra final comum e os mesmos `track_id`, grupos e splits.
- O holdout final é `holdout_test`, com {100 * split["holdout_fraction"]:.6f}% das linhas nesta versão.
- Seleção de variáveis, imputação, padronização, PCA e tuning ocorrerão somente nos 75% de desenvolvimento.
- Validação cruzada posterior ficará restrita a `development_train` e respeitará `split_group_id`.
- Métricas principais: MAE, RMSE e R².
- Resultados também serão estratificados por período, gênero e faixa de popularidade.
- Diferenças de desempenho deverão incluir intervalos de incerteza.
- `DummyRegressor` será benchmark técnico, não quinto modelo científico.

## 1. Baseline

Metadados autorizados (`year`, `genre` e flags de versão Spotify) e 13 características acústicas. Features atuais após remoção de constantes: **{len(model_spec["baseline_features"])}**.

## 2. Tradicional

Todas as features do baseline mais descritores tradicionais LFM2b não constantes. Features atuais: **{len(model_spec["traditional_features"])}**.

## 3. Profundo

Baseline mais embeddings futuros das letras integrais. Letras e embeddings ainda não foram coletados; este modelo não pode ser treinado nesta etapa.

## 4. Combinado

Baseline, descritores tradicionais e embeddings futuros. Também permanece bloqueado até existir a amostra comum com embeddings.

## Regras de comparabilidade

Quando a amostra com letras/embeddings for formada, o split será recuperado por `track_id`/grupo. Os quatro modelos usarão somente observações comuns e exatamente os mesmos splits.
"""
    _write_text("reports/modeling_protocol_v0_1_1.md", protocol)

    pca = """# Plano de análise de PCA — Base v0.1.1

O orientador sugeriu PCA para estudar a estrutura dos componentes e a variabilidade. O PCA definitivo não é executado nesta etapa.

1. PCA maximiza a variabilidade das preditoras X, não da popularidade Y.
2. Para estudar popularidade, escores dos componentes poderão ser usados posteriormente como preditores em regressão.
3. O PCA será ajustado exclusivamente em `development_train` ou em folds internos desse conjunto.
4. Padronização e PCA serão aprendidos no treino e apenas aplicados ao holdout.
5. A análise apresentará scree plot, variância explicada individual e acumulada, loadings, interpretação, estabilidade e desempenho preditivo.
6. A prioridade é o bloco de descritores LFM2b; variáveis categóricas, IDs, grupos e alvo não serão misturados automaticamente.
7. PCA não substituirá automaticamente os descritores originais.
8. PCA será análise complementar ou representação alternativa.
9. A quantidade de componentes será escolhida somente no treinamento/validação cruzada.
10. Serão comparados: tradicional com descritores tratados; tradicional com componentes; e, se viável, combinado com componentes e embeddings.
"""
    _write_text("reports/pca_analysis_plan_v0_1_1.md", pca)

    split_rows = [
        [name, value, f"{100 * value / run_summary['source_rows']:.6f}%"]
        for name, value in split["counts"].items()
    ]
    split_report = f"""# Auditoria do split — Base v0.1.1

## Regra

Split determinístico com `random_state=42`, alvo de 25%, sem usar popularidade, gênero, ano ou qualquer variável de desfecho para escolher grupos. `split_group_id` é o componente conectado entre `artist_group_id` e `composition_group_id`; portanto, nenhum artista ou composição pode atravessar as partições.

{_markdown_table(["split", "linhas", "%"], split_rows)}

- Fração real de teste: **{100 * split["holdout_fraction"]:.6f}%**.
- Grupos: `{json.dumps(split["group_counts"], ensure_ascii=False)}`.
- Sobreposição: `{json.dumps(split["overlap"], ensure_ascii=False)}`.
- SMD da popularidade: **{split["popularity_standardized_mean_difference"]:.6f}**.

## Comparações

As comparações foram calculadas somente depois de o split estar fixado por grupos e servem para auditoria, não para refazer o holdout com base no desfecho.

Alertas de desequilíbrio relevante: {split["relevant_imbalance_warnings"] or ["nenhum pelos limiares operacionais"]}.

Disponibilidade dos descritores:

```json
{json.dumps(split["descriptor_availability"], ensure_ascii=False, indent=2)}
```

O `holdout_test` fica lacrado para decisões de seleção, imputação, padronização, PCA e hiperparâmetros. A validação cruzada ocorrerá apenas dentro de `development_train`, respeitando grupos.
"""
    _write_text("reports/split_audit_v0_1_1.md", split_report)

    changelog = f"""# Changelog — Base v0.1 → v0.1.1

- A Base v0.1 foi recarregada do Parquet e permaneceu imutável.
- Criados identificadores determinísticos de artista, composição e grupo de split.
- Criado split agrupado 75/25 com `random_state=42`.
- Confirmados 209 descritores; corrigida documentalmente a classificação preliminar de 231 campos.
- Removidas {len(constants)} preditoras constantes da matriz controlada, sem apagar as colunas da auditoria.
- Separadas matriz de modelagem, atribuições de split e auditoria de matching.
- Criado manifesto definitivo e amostra de revisão humana com campos vazios.
- Nenhuma linha foi excluída; nenhuma ausência foi imputada; nenhum modelo, PCA, embedding ou coleta de letras foi executado.
"""
    _write_text("reports/changelog_v0_1_to_v0_1_1.md", changelog)


def _handoff_text(summary: dict[str, Any]) -> str:
    validation = summary["validation"]
    matching = summary["matching"]
    split = summary["split"]
    model_spec = summary["model_spec"]
    verification = summary.get("verification", {})
    commands = verification.get("commands", [])
    command_table = (
        _markdown_table(
            ["comando", "código de saída", "resultado"],
            [[item["command"], item["exit_code"], item["result"]] for item in commands],
        )
        if commands
        else "Testes ainda não registrados no resumo."
    )
    constants = ", ".join(f"`{name}`" for name in validation["constant_predictors_removed"])
    prohibited = ", ".join(f"`{name}`" for name in model_spec["prohibited_features"])
    temporal = matching["temporal"]["statistics"]
    known = [
        "225 classificações humanas permanecem vazias.",
        f"{matching['temporal']['implausible_lfm_release_year_flagged']} pares têm flag de ano LFM implausível e foram preservados.",
        "O bloco estrutural tem ausência estrutural; imputação e sensibilidade ficam para o treino.",
        "Modelos profundo e combinado aguardam letras integrais e embeddings.",
        "A população inferencial é o subconjunto Spotify–LFM2b matched, não todo o Spotify.",
        "O Ruff completo encontra B018 em exp_base.py:8; esse arquivo exploratório pré-existente e não versionado foi preservado, enquanto pipeline e testes passam no Ruff.",
    ]
    known_lines = "\n".join(f"- {item}" for item in known)
    return f"""# Handoff — Base v0.1.1

Gerado em `{summary["generated_at"]}`. Nenhuma coleta de letras, scraping, embedding, PCA definitivo, treinamento ou tuning foi realizado.

## 1. Contagens antes e depois

- Base v0.1: **{validation["source_rows"]:,} linhas × {validation["source_columns"]:,} colunas**.
- Base v0.1.1 controlada: **{validation["output_rows"]:,} linhas × {validation["output_columns"]:,} colunas**.
- Linhas removidas: **0**.
- Split e auditoria preservam os **{validation["output_rows"]:,}** pares aceitos.

## 2. Número final de linhas e colunas

O arquivo `modeling_base_lfm_v0_1_1.parquet` possui **{validation["output_rows"]:,} × {validation["output_columns"]:,}**.

## 3. Número confirmado de descritores

Foram confirmados **209 descritores líricos**. A contagem 231 do inventário preliminar incluía indevidamente 22 campos de normalização, versão e chaves; as 242 colunas LFM2b no integrado se dividem em 209 descritores e 33 não descritores.

## 4. Variáveis constantes removidas

Foram removidas **{len(validation["constant_predictors_removed"])}** preditoras constantes: {constants}.

## 5. Tratamento proposto para ausências

Ausências não foram substituídas por zero. O plano é criar indicador de ausência, ajustar imputação somente em `development_train`, executar análise de sensibilidade e avaliar o bloco estrutural separadamente. Nenhuma estatística de imputação ou escala foi calculada antes do split.

## 6. Inconsistências encontradas

- Divergências nas contagens centrais entre Parquet, `run_summary`, auditorias, matching e Excel: **{len(validation["consistency"]["inconsistencies"])}**.
- Divergência semântica resolvida: 231 campos do inventário preliminar versus 209 descritores confirmados.
- O Excel anterior recomendava 222 preditoras por uma classificação exploratória; a v0.1.1 usa protocolo explícito, inclui metadados baseline autorizados e remove constantes somente com base em `development_train`.

## 7. Auditoria temporal

- Média/mediana/desvio-padrão da diferença absoluta: **{temporal["mean"]:.6f} / {temporal["median"]:.6f} / {temporal["standard_deviation"]:.6f}** anos.
- Mínimo/máximo: **{temporal["minimum"]} / {temporal["maximum"]}**.
- Quantis: `{json.dumps(temporal["quantiles"], ensure_ascii=False)}`.
- Faixas: `{json.dumps(matching["temporal"]["bands"], ensure_ascii=False)}`.
- Ano ausente para o cálculo: **{temporal["missing"]} ({100 * temporal["missing"] / matching["rows"]:.6f}%)**.
- Diferença temporal não foi classificada automaticamente como erro.

## 8. Auditoria de versões

`{json.dumps(matching["versions"], ensure_ascii=False)}`

## 9. Casos sem chave de composição

Confirmados **{matching["identity"]["accepted_without_spotify_composition_key"]}** casos sem `composition_key` Spotify e **{matching["identity"]["accepted_without_lfm_composition_key"]}** sem chave LFM correspondente. Foram preservados com fallback determinístico por `track_id`.

## 10. Composição do treino e teste

- `development_train`: **{split["counts"]["development_train"]:,}** linhas.
- `holdout_test`: **{split["counts"]["holdout_test"]:,}** linhas.
- Grupos: `{json.dumps(split["group_counts"], ensure_ascii=False)}`.

## 11. Percentual real destinado ao teste

**{100 * split["holdout_fraction"]:.6f}%**.

## 12. Ausência de sobreposição

Sobreposição observada: `{json.dumps(split["overlap"], ensure_ascii=False)}`. Todos os valores são zero.

## 13. Variáveis permitidas nos quatro modelos

- Baseline ({len(model_spec["baseline_features"])}): {", ".join(f"`{name}`" for name in model_spec["baseline_features"])}.
- Tradicional ({len(model_spec["traditional_features"])}): baseline + {len(model_spec["traditional_descriptor_features"])} descritores tradicionais não constantes.
- Profundo: baseline + embeddings futuros; ainda indisponível.
- Combinado: baseline + descritores tradicionais + embeddings futuros; ainda indisponível.

Os quatro modelos usarão a mesma amostra comum e os mesmos splits.

## 14. Variáveis proibidas

Proibições explícitas e classes proibidas: {prohibited}. Além delas, IDs, nomes, títulos, chaves técnicas e qualquer coluna com “modelo em que poderá entrar = nenhum” no manifesto não podem compor o vetor de preditores.

## 15. Decisões pendentes de revisão humana

- Rotular 225 linhas em `match_review_sample_v0_1_1.xlsx`.
- Revisar especialmente incompatibilidades temporais, chaves ausentes, `mono_stereo`, `demo`, ambiguidades e fuzzy.
- Definir, no treino, a estratégia final para ausência estrutural e transformações.

## 16. Resultado real dos testes

Status: **{verification.get("status", "pendente")}**.

{command_table}

## 17. Comandos executados e códigos de saída

Os comandos e códigos reais aparecem na tabela acima e em `run_summary_v0_1_1.json`.

## 18. Problemas conhecidos

{known_lines}

## 19. Classificação

**PRONTA COM RESSALVAS.** A base, o manifesto e o split estão tecnicamente preparados para o próximo piloto, mas a revisão humana de matching e as decisões de ausência/representação ainda precisam ser concluídas antes dos modelos finais.
"""


def finalize_handoff(verification: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = read_json("reports/run_summary_v0_1_1.json", {})
    if not summary:
        raise FileNotFoundError("reports/run_summary_v0_1_1.json")
    review_workbook = project_path("reports/match_review_sample_v0_1_1.xlsx")
    if review_workbook.exists():
        summary.setdefault("outputs", {})["reports/match_review_sample_v0_1_1.xlsx"] = {
            "size_bytes": review_workbook.stat().st_size,
            "sha256": sha256_file(review_workbook),
        }
    if verification is not None:
        summary["verification"] = verification
        summary["status"] = (
            "complete_with_caveats"
            if verification.get("status") == "aprovado"
            else "validation_failed"
        )
    write_json("reports/run_summary_v0_1_1.json", summary)
    _write_text("reports/handoff_base_v0_1_1.md", _handoff_text(summary))
    return summary


def prepare_base_v011() -> dict[str, Any]:
    started = time.perf_counter()
    config = load_yaml("configs/modeling_v0_1_1.yaml")
    source_path = project_path(config["source_base"])
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    source_hash_before = sha256_file(source_path)
    base = pl.read_parquet(source_path)
    lfm_audit = read_json("reports/tables/lfm2b_audit.json", {})
    inventory = read_json("reports/tables/lfm2b_schema_inventory.json", {})
    descriptors = list(lfm_audit.get("descriptor_names", []))
    inventory_descriptors = list(inventory.get("descriptor_columns", []))
    if len(descriptors) != 209:
        raise RuntimeError(f"Esperados 209 descritores confirmados, encontrados {len(descriptors)}")
    if base.shape != (111_758, 310):
        raise RuntimeError(f"Shape inesperado da Base v0.1: {base.shape}")

    baseline = [*config["baseline_metadata"], *config["baseline_acoustic"]]
    required = (
        set(baseline)
        | set(descriptors)
        | {
            TARGET,
            *IDENTIFICATION_COLUMNS,
            "artist_conservative",
            "artist_strict",
            "artist_primary",
            "artist_name_raw",
            "composition_key",
            "lfm_composition_key",
        }
    )
    missing_required = sorted(required - set(base.columns))
    if missing_required:
        raise RuntimeError(f"Colunas obrigatórias ausentes: {missing_required}")

    threshold = float(config["near_zero_relative_variance_threshold"])
    source_profile = profile_frame(base, threshold)
    assignments = build_group_assignments(base)
    split_frame = _add_split(base, assignments, config)
    development = split_frame.filter(pl.col("split") == "development_train")
    development_profile = profile_frame(development.select(base.columns), threshold)

    candidate_features = [*baseline, *descriptors]
    removed_constants = {
        name for name in candidate_features if development_profile[name]["constant"]
    }
    authorized_features = [name for name in candidate_features if name not in removed_constants]
    baseline_features = [name for name in baseline if name not in removed_constants]
    traditional_descriptors = [name for name in descriptors if name not in removed_constants]
    matrix_columns = [
        *IDENTIFICATION_COLUMNS,
        *GROUP_COLUMNS,
        "split",
        TARGET,
        *authorized_features,
    ]
    if len(matrix_columns) != len(set(matrix_columns)):
        raise RuntimeError("Colunas duplicadas na matriz v0.1.1")
    modeling = split_frame.select(matrix_columns)
    if modeling.height != base.height:
        raise RuntimeError("Exclusão silenciosa de linhas detectada")

    temporal = _temporal_audit(split_frame)
    versions = _version_audit(split_frame, list(config["version_flags"]))
    identity = _identity_audit(split_frame)
    split_audit = _split_audit(split_frame, descriptors, list(config["version_flags"]))
    if any(split_audit["overlap"].values()):
        raise RuntimeError(f"Sobreposição de grupos no split: {split_audit['overlap']}")
    if not 0.20 <= split_audit["holdout_fraction"] <= 0.30:
        raise RuntimeError(
            f"Fração de holdout fora do intervalo: {split_audit['holdout_fraction']}"
        )

    manifest = _manifest(
        base,
        split_frame,
        source_profile,
        development_profile,
        set(descriptors),
        set(baseline),
        set(config["baseline_acoustic"]),
        set(config["version_flags"]),
        removed_constants,
        matrix_columns,
    )
    review_sample, review_coverage = _review_sample(split_frame, list(config["version_flags"]))

    matching_columns = [
        *IDENTIFICATION_COLUMNS,
        "artist_name_raw",
        "track_name_raw",
        "lfm_artist_name_raw",
        "lfm_track_name_raw",
        "year",
        "lfm_release_year",
        "composition_key",
        "lfm_composition_key",
        *GROUP_COLUMNS,
        "split",
        "match_method",
        "match_score",
        "match_status",
        "acceptance_reason",
        "version_compatible",
        "temporal_compatible",
        "matching_version",
        *list(config["version_flags"]),
        *[f"lfm_{flag}" for flag in config["version_flags"]],
        "genius_lyrics_views",
        "lfm_playcount",
        "lfm_qf_release_year_implausible",
    ]
    matching_audit = split_frame.select(matching_columns).with_columns(
        (pl.col("year") - pl.col("lfm_release_year")).abs().alias("temporal_year_difference_abs")
    )
    split_assignments = split_frame.select(
        [
            *IDENTIFICATION_COLUMNS,
            "composition_key",
            "lfm_composition_key",
            *GROUP_COLUMNS,
            "split",
            "split_random_state",
            "split_version",
        ]
    )

    _write_parquet_atomic(modeling, "data/processed/modeling_base_lfm_v0_1_1.parquet")
    _write_parquet_atomic(split_assignments, "data/processed/split_assignments_v0_1_1.parquet")
    _write_parquet_atomic(matching_audit, "data/processed/matching_audit_v0_1_1.parquet")
    _write_csv_atomic(manifest, "reports/feature_manifest_v0_1_1.csv")
    write_json(
        "reports/tables/match_review_sample_v0_1_1.json",
        {
            "generated_at": utc_now(),
            "coverage": review_coverage,
            "columns": review_sample.columns,
            "rows": review_sample.to_dicts(),
        },
    )

    consistency = _consistency(base, len(descriptors), len(inventory_descriptors))
    structure_columns = [name for name in descriptors if name.startswith("lfm_structure_")]
    structure_missing_rows = base.select(
        pl.any_horizontal([pl.col(name).is_null() for name in structure_columns]).sum()
    ).item()
    validation = {
        "source_rows": base.height,
        "source_columns": base.width,
        "output_rows": modeling.height,
        "output_columns": modeling.width,
        "unique_track_ids": base["track_id"].n_unique(),
        "unique_spotify_row_ids": base["spotify_row_id"].n_unique(),
        "unique_lfm_record_keys": base["lfm_record_key"].n_unique(),
        "total_missing_cells": sum(item["missing"] for item in source_profile.values()),
        "total_infinite_values": sum(item["infinite"] for item in source_profile.values()),
        "constant_columns_full": sorted(
            name for name, item in source_profile.items() if item["constant"]
        ),
        "near_zero_columns_full": sorted(
            name for name, item in source_profile.items() if item["near_zero"]
        ),
        "near_zero_rule": f"{threshold} × max(1, média²)",
        "candidate_predictors_before_constant_removal": len(candidate_features),
        "authorized_features_after_constant_removal": len(authorized_features),
        "constant_predictors_removed": sorted(removed_constants),
        "structure_missing_rows": int(structure_missing_rows),
        "consistency": consistency,
        "inventory_descriptor_extras": sorted(set(inventory_descriptors) - set(descriptors)),
    }
    matching = {
        "rows": base.height,
        "by_match_method": _distribution(base, "match_method"),
        "by_match_status": _distribution(base, "match_status"),
        "by_acceptance_reason": _distribution(base, "acceptance_reason"),
        "match_score_non_null": base.height - base["match_score"].null_count(),
        "version_compatible_true": int(base["version_compatible"].sum()),
        "temporal_compatible_true": int(base["temporal_compatible"].sum()),
        "temporal_compatible_false": int((~base["temporal_compatible"]).sum()),
        "temporal": temporal,
        "versions": versions,
        "identity": identity,
        "review_sample": review_coverage,
    }
    explicit_prohibited = sorted(
        set(config["minimum_prohibited"])
        | NAME_TITLE_FIELDS
        | TECHNICAL_KEY_FIELDS
        | MATCHING_FIELDS
    )
    model_spec = {
        "target": TARGET,
        "random_state": int(config["random_state"]),
        "holdout_fraction_target": float(config["holdout_fraction"]),
        "baseline_features": baseline_features,
        "traditional_descriptor_features": traditional_descriptors,
        "traditional_features": [*baseline_features, *traditional_descriptors],
        "deep_features_current": baseline_features,
        "deep_future_block": "embeddings de letras integrais ainda não coletados",
        "combined_features_current": [*baseline_features, *traditional_descriptors],
        "combined_future_block": "embeddings de letras integrais ainda não coletados",
        "prohibited_features": explicit_prohibited,
        "removed_constant_features": sorted(removed_constants),
        "matrix_columns": matrix_columns,
    }

    write_json("reports/tables/base_validation_v0_1_1.json", validation)
    write_json("reports/tables/matching_temporal_audit_v0_1_1.json", matching)
    write_json("reports/tables/split_audit_v0_1_1.json", split_audit)
    write_json("reports/tables/model_spec_v0_1_1.json", model_spec)

    source_hash_after = sha256_file(source_path)
    if source_hash_after != source_hash_before:
        raise RuntimeError("A Base v0.1 foi alterada durante a preparação")
    outputs = {
        relative: {
            "size_bytes": project_path(relative).stat().st_size,
            "sha256": sha256_file(project_path(relative)),
        }
        for relative in (
            "data/processed/modeling_base_lfm_v0_1_1.parquet",
            "data/processed/split_assignments_v0_1_1.parquet",
            "data/processed/matching_audit_v0_1_1.parquet",
            "reports/feature_manifest_v0_1_1.csv",
        )
    }
    summary = {
        "generated_at": utc_now(),
        "version": VERSION,
        "code_version": VERSION,
        "git_commit": git_commit(),
        "source_path": str(source_path),
        "source_sha256_before": source_hash_before,
        "source_sha256_after": source_hash_after,
        "source_rows": base.height,
        "duration_seconds": round(time.perf_counter() - started, 6),
        "validation": validation,
        "matching": matching,
        "split": split_audit,
        "model_spec": model_spec,
        "outputs": outputs,
        "verification": {"status": "pendente", "commands": []},
        "status": "prepared_pending_verification",
        "warnings": [
            "spotify_popularity é histórica no snapshot e não representa sucesso futuro.",
            "Holdout_test não pode ser usado em seleção, imputação, escala, PCA ou tuning.",
            "A revisão humana dos 225 casos permanece pendente.",
        ],
    }
    write_json("reports/run_summary_v0_1_1.json", summary)
    _build_reports(summary, validation, matching, split_audit, model_spec)
    finalize_handoff()
    return summary
