"""Flags de qualidade; registros inválidos são preservados."""

from __future__ import annotations

import polars as pl


def add_spotify_quality_flags(frame: pl.DataFrame) -> pl.DataFrame:
    unit_columns = [
        "danceability",
        "energy",
        "speechiness",
        "acousticness",
        "instrumentalness",
        "liveness",
        "valence",
    ]
    expressions: list[pl.Expr] = []
    if "track_id" in frame.columns:
        expressions.append(
            (
                pl.col("track_id").is_null()
                | ~pl.col("track_id").cast(pl.String).str.contains(r"^[A-Za-z0-9]{22}$")
            ).alias("qf_track_id_invalid")
        )
    if "spotify_popularity" in frame.columns:
        expressions.append(
            (~pl.col("spotify_popularity").cast(pl.Float64, strict=False).is_between(0, 100))
            .fill_null(True)
            .alias("qf_spotify_popularity_out_of_range")
        )
    if "year" in frame.columns:
        expressions.append(
            (~pl.col("year").cast(pl.Int64, strict=False).is_between(1900, 2030))
            .fill_null(True)
            .alias("qf_year_implausible")
        )
    if "duration_ms" in frame.columns:
        expressions.append(
            (pl.col("duration_ms").cast(pl.Float64, strict=False) <= 0)
            .fill_null(True)
            .alias("qf_duration_nonpositive")
        )
    if "tempo" in frame.columns:
        expressions.append(
            (pl.col("tempo").cast(pl.Float64, strict=False) <= 0)
            .fill_null(True)
            .alias("qf_tempo_nonpositive")
        )
    for name in unit_columns:
        if name in frame.columns:
            expressions.append(
                (~pl.col(name).cast(pl.Float64, strict=False).is_between(0, 1))
                .fill_null(True)
                .alias(f"qf_{name}_out_of_range")
            )
    categories = {
        "key": list(range(-1, 12)),
        "mode": [0, 1],
        "time_signature": list(range(0, 8)),
    }
    for name, valid in categories.items():
        if name in frame.columns:
            expressions.append(
                (~pl.col(name).cast(pl.Int64, strict=False).is_in(valid))
                .fill_null(True)
                .alias(f"qf_{name}_invalid")
            )
    result = frame.with_columns(expressions)
    flags = [name for name in result.columns if name.startswith("qf_")]
    return result.with_columns(pl.any_horizontal(flags).alias("qf_any")) if flags else result


def quality_summary(frame: pl.DataFrame) -> dict[str, int]:
    flags = [name for name in frame.columns if name.startswith("qf_")]
    if not flags:
        return {}
    row = frame.select([pl.col(name).sum().cast(pl.Int64).alias(name) for name in flags]).row(0)
    return dict(zip(flags, row, strict=True))
