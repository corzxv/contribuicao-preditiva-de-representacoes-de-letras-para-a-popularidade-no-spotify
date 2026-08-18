"""Leitura, normalização e auditoria da fonte Spotify."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl

from .config import load_sources_config, project_path
from .io import read_json, update_manifest, utc_now, write_json
from .normalization import add_normalized_columns
from .quality import add_spotify_quality_flags, quality_summary

EXPECTED_NUMERIC = [
    "popularity",
    "year",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "duration_ms",
    "time_signature",
]


def _read_spotify(path: Path) -> pl.DataFrame:
    frame = pl.read_csv(
        path,
        encoding="utf8-lossy",
        infer_schema_length=100_000,
        null_values=["", "NA", "N/A", "null", "None"],
        try_parse_dates=True,
        low_memory=True,
    )
    rename = {name: name.strip().lower() for name in frame.columns}
    return frame.rename(rename)


def normalize_spotify(force: bool = False) -> dict[str, Any]:
    source = load_sources_config()["spotify"]
    input_path = project_path(source["local_path"])
    output_path = project_path("data/interim/spotify_normalized.parquet")
    processed_path = project_path("data/processed/spotify_tracks.parquet")
    if not input_path.exists():
        raise FileNotFoundError(f"Spotify ausente em {input_path}")
    if output_path.exists() and processed_path.exists() and not force:
        return {"status": "reused", "path": str(processed_path)}

    raw = _read_spotify(input_path)
    source_schema = {name: str(dtype) for name, dtype in raw.schema.items()}
    index_columns = [
        name for name in raw.columns if not name or name.startswith("unnamed:") or name == "index"
    ]
    if index_columns:
        raw = raw.drop(index_columns)
    required = {"artist_name", "track_name", "track_id", "popularity", "year"}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"Schema Spotify incompatível; colunas ausentes: {missing}")

    casts = []
    for name in EXPECTED_NUMERIC:
        if name in raw.columns:
            dtype = (
                pl.Int64
                if name in {"year", "key", "mode", "duration_ms", "time_signature"}
                else pl.Float64
            )
            casts.append(pl.col(name).cast(dtype, strict=False))
    frame = (
        raw.with_columns(casts)
        .with_row_index("spotify_row_id", offset=1)
        .with_columns(
            pl.col("artist_name").alias("artist_name_raw"),
            pl.col("track_name").alias("track_name_raw"),
            pl.col("popularity").alias("spotify_popularity"),
        )
        .drop("popularity")
        .with_columns(
            pl.when(pl.col("year").is_between(2000, 2009))
            .then(pl.lit("2000-2009"))
            .when(pl.col("year").is_between(2010, 2019))
            .then(pl.lit("2010-2019"))
            .when(pl.col("year").is_between(2020, 2023))
            .then(pl.lit("2020-2023"))
            .otherwise(pl.lit("outside_main_period"))
            .alias("temporal_cohort")
        )
    )
    frame = add_normalized_columns(frame, "artist_name_raw", "track_name_raw")
    frame = add_spotify_quality_flags(frame).with_columns(
        pl.col("track_id").is_duplicated().alias("qf_track_id_duplicate")
    )
    current_flags = [name for name in frame.columns if name.startswith("qf_") and name != "qf_any"]
    frame = frame.with_columns(pl.any_horizontal(current_flags).alias("qf_any"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(output_path, compression="zstd", statistics=True)
    frame.write_parquet(processed_path, compression="zstd", statistics=True)

    manifest = read_json("data/raw/manifest.json", {"sources": {}})
    metadata = manifest.get("sources", {}).get("spotify", {})
    metadata.update(
        {
            "schema_observed": source_schema,
            "normalized_schema": {name: str(dtype) for name, dtype in frame.schema.items()},
            "record_count": frame.height,
            "verification_status": "audited_and_normalized",
            "verified_at": utc_now(),
            "dropped_index_columns_from_normalized_layer": index_columns,
        }
    )
    update_manifest("spotify", metadata)
    return {"status": "created", "rows": frame.height, "path": str(processed_path)}


def _value_counts(frame: pl.DataFrame, column: str) -> list[dict[str, Any]]:
    if column not in frame.columns:
        return []
    return frame.group_by(column).len().sort("len", descending=True).to_dicts()


def audit_spotify() -> dict[str, Any]:
    path = project_path("data/processed/spotify_tracks.parquet")
    if not path.exists():
        normalize_spotify()
    frame = pl.read_parquet(path)
    relevant = [name for name in frame.columns if name != "spotify_row_id"]
    missing = {
        name: {
            "count": int(frame[name].null_count()),
            "percent": round(100 * frame[name].null_count() / max(frame.height, 1), 6),
        }
        for name in frame.columns
    }
    cardinality = {name: int(frame[name].n_unique()) for name in frame.columns}
    popularity = frame["spotify_popularity"].drop_nulls()
    stats = {
        "count": len(popularity),
        "mean": float(popularity.mean()) if len(popularity) else None,
        "median": float(popularity.median()) if len(popularity) else None,
        "min": float(popularity.min()) if len(popularity) else None,
        "max": float(popularity.max()) if len(popularity) else None,
        "quantiles": {
            str(q): float(popularity.quantile(q, interpolation="linear"))
            for q in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)
        },
        "zero_count": int((popularity == 0).sum()),
        "zero_percent": round(100 * (popularity == 0).sum() / max(len(popularity), 1), 6),
    }
    acoustic = [
        name
        for name in (
            "danceability",
            "energy",
            "loudness",
            "speechiness",
            "acousticness",
            "instrumentalness",
            "liveness",
            "valence",
            "tempo",
            "duration_ms",
        )
        if name in frame.columns
    ]
    acoustic_summary = {}
    for name in acoustic:
        series = frame[name].drop_nulls().cast(pl.Float64)
        acoustic_summary[name] = {
            "mean": float(series.mean()) if len(series) else None,
            "median": float(series.median()) if len(series) else None,
            "min": float(series.min()) if len(series) else None,
            "max": float(series.max()) if len(series) else None,
        }
    numeric_for_corr = ["spotify_popularity", *acoustic]
    corr = frame.select(numeric_for_corr).corr().to_dicts()
    genres = _value_counts(frame, "genre")
    genre_counts = [row["len"] for row in genres]
    genre_cv = None
    repeated_share = None
    if genre_counts:
        count_series = pl.Series(genre_counts, dtype=pl.Float64)
        mean_count = count_series.mean()
        genre_cv = float(count_series.std() / mean_count) if mean_count else None
        modes = count_series.mode()
        repeated_share = (
            float((count_series == modes[0]).sum() / len(count_series)) if len(modes) else None
        )
    genre_balance = {
        "coefficient_of_variation": genre_cv,
        "share_categories_at_modal_count": repeated_share,
        "possible_artificial_balance_signal": bool(
            (genre_cv is not None and genre_cv < 0.05)
            or (repeated_share is not None and repeated_share >= 0.5)
        ),
        "interpretation": "Heurística descritiva; não comprova o mecanismo de amostragem.",
    }
    by_year = _value_counts(frame, "year")
    by_cohort = _value_counts(frame, "temporal_cohort")
    observed = {
        "rows": frame.height,
        "columns": frame.width,
        "artists_distinct": cardinality.get("artist_name_raw"),
        "titles_distinct": cardinality.get("track_name_raw"),
        "track_ids_distinct": cardinality.get("track_id"),
        "year_min": int(frame["year"].min()) if frame["year"].drop_nulls().len() else None,
        "year_max": int(frame["year"].max()) if frame["year"].drop_nulls().len() else None,
    }
    benchmarks = {
        "rows": 1_159_764,
        "track_ids_distinct": 1_159_764,
        "artists_distinct": 64_158,
        "genres_distinct": 82,
        "popularity_zero_percent": 13.66,
        "popularity_mean": 18.38,
        "popularity_median": 15.0,
    }
    comparisons = {
        "rows_difference": observed["rows"] - benchmarks["rows"],
        "track_ids_difference": observed["track_ids_distinct"] - benchmarks["track_ids_distinct"],
        "artists_difference": observed["artists_distinct"] - benchmarks["artists_distinct"],
        "genres_difference": cardinality.get("genre", 0) - benchmarks["genres_distinct"],
        "popularity_zero_percentage_points_difference": stats["zero_percent"]
        - benchmarks["popularity_zero_percent"],
        "popularity_mean_difference": stats["mean"] - benchmarks["popularity_mean"],
        "popularity_median_difference": stats["median"] - benchmarks["popularity_median"],
    }
    audit = {
        "generated_at": utc_now(),
        "observed": observed,
        "schema": {name: str(dtype) for name, dtype in frame.schema.items()},
        "safe_sample": frame.select(
            [
                c
                for c in [
                    "track_id",
                    "artist_name_raw",
                    "track_name_raw",
                    "year",
                    "genre",
                    "spotify_popularity",
                ]
                if c in frame.columns
            ]
        )
        .head(10)
        .to_dicts(),
        "missing": missing,
        "cardinality": cardinality,
        "duplicate_complete_rows_excluding_row_id": int(
            frame.select(relevant).is_duplicated().sum()
        ),
        "duplicate_track_id_rows": int(frame["track_id"].is_duplicated().sum()),
        "duplicate_artist_title_rows": int(
            frame.select(["artist_name_raw", "track_name_raw"]).is_duplicated().sum()
        ),
        "composition_keys_with_multiple_rows": int(
            frame.group_by("composition_key").len().filter(pl.col("len") > 1).height
        ),
        "by_year": by_year,
        "by_cohort": by_cohort,
        "by_genre": genres,
        "popularity": stats,
        "acoustic_summary": acoustic_summary,
        "descriptive_correlations_non_causal": corr,
        "quality_flags": quality_summary(frame),
        "genre_balance_investigation": genre_balance,
        "benchmarks_supplied_not_observed": benchmarks,
        "benchmark_differences_observed_minus_benchmark": comparisons,
    }
    write_json("reports/tables/spotify_audit.json", audit)
    frame.select(
        ["spotify_row_id", "track_id", *[name for name in frame.columns if name.startswith("qf_")]]
    ).filter(pl.col("qf_any")).write_csv(
        project_path("data/rejected/spotify_quality_exceptions.csv")
    )
    return audit
