"""Cruzamento em camadas, sem aceitação automática de fuzzy."""

from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import duckdb
import polars as pl
from rapidfuzz import fuzz, process

from .config import load_yaml, project_path
from .io import read_json, utc_now, write_json

VERSION_FLAGS = [
    "remaster",
    "remix",
    "live",
    "acoustic",
    "radio_edit",
    "mono_stereo",
    "instrumental",
    "demo",
]


def _sql_path(path: Path) -> str:
    return path.as_posix().replace("'", "''")


def _version_compatibility_sql() -> str:
    return " AND ".join(
        f"coalesce(s.{flag}, false) = coalesce(l.lfm_{flag}, false)" for flag in VERSION_FLAGS
    )


def _candidate_select(method: str, priority: int, condition: str, extra: str = "TRUE") -> str:
    compatibility = _version_compatibility_sql()
    return f"""
        SELECT
            s.track_id AS spotify_track_id,
            s.spotify_row_id,
            l.lfm_record_key,
            '{method}' AS match_method,
            {priority} AS method_priority,
            CAST(NULL AS DOUBLE) AS match_score,
            ({compatibility}) AS version_compatible,
            CASE WHEN l.lfm_release_year IS NULL OR s.year IS NULL THEN NULL
                 ELSE abs(s.year - l.lfm_release_year) <= 2 END AS temporal_compatible,
            'artist_and_title' AS candidate_reason
        FROM spotify s
        JOIN lfm l ON {condition}
        WHERE {extra}
    """


def _write_fuzzy_candidates(
    connection: duckdb.DuckDBPyConnection, destination: Path, config: dict[str, Any]
) -> int:
    fuzzy_config = config["fuzzy"]
    schema = {
        "spotify_track_id": pl.String,
        "spotify_row_id": pl.UInt32,
        "lfm_record_key": pl.String,
        "match_method": pl.String,
        "method_priority": pl.Int64,
        "match_score": pl.Float64,
        "version_compatible": pl.Boolean,
        "temporal_compatible": pl.Boolean,
        "candidate_reason": pl.String,
        "match_status": pl.String,
        "acceptance_reason": pl.String,
        "spotify_candidate_count": pl.Int64,
        "lfm_spotify_count": pl.Int64,
        "ambiguity_flag": pl.Boolean,
        "matching_version": pl.String,
    }
    if not fuzzy_config.get("enabled", True):
        pl.DataFrame(schema=schema).write_parquet(destination)
        return 0

    lfm_rows = connection.execute(
        "SELECT lfm_record_key, lfm_artist_conservative, lfm_title_conservative, "
        "lfm_release_year, "
        + ", ".join(f"lfm_{flag}" for flag in VERSION_FLAGS)
        + " FROM lfm WHERE lfm_artist_conservative IS NOT NULL AND lfm_title_conservative IS NOT NULL"
    ).fetchall()
    lfm_by_artist: dict[str, dict[str, str]] = defaultdict(dict)
    lfm_metadata: dict[str, tuple[Any, ...]] = {}
    for row in lfm_rows:
        key, artist, title, *metadata = row
        lfm_by_artist[artist][key] = title
        lfm_metadata[key] = tuple(metadata)

    limit = int(fuzzy_config.get("max_tracks", 50_000))
    spotify_rows = connection.execute(
        "SELECT s.track_id, s.spotify_row_id, s.artist_conservative, s.title_conservative, s.year, "
        + ", ".join(f"s.{flag}" for flag in VERSION_FLAGS)
        + " FROM spotify s LEFT JOIN deterministic_candidates d ON s.track_id = d.spotify_track_id "
        "WHERE d.spotify_track_id IS NULL AND s.artist_conservative IS NOT NULL "
        "AND s.title_conservative IS NOT NULL ORDER BY hash(s.track_id) LIMIT ?",
        [limit],
    ).fetchall()
    candidates: list[dict[str, Any]] = []
    threshold = float(fuzzy_config.get("minimum_score", 88.0))
    maximum = int(fuzzy_config.get("max_candidates_per_track", 3))
    for row in spotify_rows:
        track_id, row_id, artist, title, spotify_year, *spotify_flags = row
        choices = lfm_by_artist.get(artist)
        if not choices:
            continue
        matches = process.extract(
            title, choices, scorer=fuzz.WRatio, limit=maximum, score_cutoff=threshold
        )
        for _choice, score, lfm_key in matches:
            lfm_year, *lfm_flags = lfm_metadata[lfm_key]
            version_compatible = all(
                bool(left) == bool(right)
                for left, right in zip(spotify_flags, lfm_flags, strict=True)
            )
            temporal = (
                None
                if lfm_year is None or spotify_year is None
                else abs(spotify_year - lfm_year) <= 2
            )
            candidates.append(
                {
                    "spotify_track_id": str(track_id),
                    "spotify_row_id": row_id,
                    "lfm_record_key": str(lfm_key),
                    "match_method": "fuzzy_candidate",
                    "method_priority": 5,
                    "match_score": float(score),
                    "version_compatible": version_compatible,
                    "temporal_compatible": temporal,
                    "candidate_reason": "same_conservative_artist_and_fuzzy_title",
                    "match_status": "candidate_for_review",
                    "acceptance_reason": "fuzzy_never_auto_accepted",
                    "spotify_candidate_count": 0,
                    "lfm_spotify_count": 0,
                    "ambiguity_flag": False,
                    "matching_version": config["version"],
                }
            )
    if candidates:
        frame = (
            pl.DataFrame(candidates, schema_overrides=schema)
            .with_columns(
                pl.len().over("spotify_track_id").alias("spotify_candidate_count"),
                pl.len().over("lfm_record_key").alias("lfm_spotify_count"),
            )
            .with_columns(
                ((pl.col("spotify_candidate_count") > 1) | (pl.col("lfm_spotify_count") > 1)).alias(
                    "ambiguity_flag"
                )
            )
        )
    else:
        frame = pl.DataFrame(schema=schema)
    frame.write_parquet(destination, compression="zstd")
    return frame.height


def run_matching(force: bool = False) -> dict[str, Any]:
    spotify_path = project_path("data/processed/spotify_tracks.parquet")
    lfm_path = project_path("data/processed/lfm2b_tracks.parquet")
    if not spotify_path.exists() or not lfm_path.exists():
        missing = [str(path) for path in (spotify_path, lfm_path) if not path.exists()]
        raise FileNotFoundError(f"Camadas normalizadas ausentes: {missing}")
    outputs = {
        "all": project_path("data/processed/spotify_lfm_all_candidates.parquet"),
        "matches": project_path("data/processed/spotify_lfm_matches.parquet"),
        "ambiguous": project_path("data/processed/spotify_lfm_ambiguous.parquet"),
        "review": project_path("data/processed/spotify_lfm_candidates_review.parquet"),
        "rejected": project_path("data/processed/spotify_lfm_rejected.parquet"),
        "unmatched": project_path("data/processed/spotify_lfm_unmatched.parquet"),
        "status": project_path("data/processed/spotify_tracks_with_match_status.parquet"),
        "modeling": project_path("data/processed/modeling_base_lfm_v0_1.parquet"),
        "sample": project_path("data/processed/spotify_lfm_review_sample.parquet"),
    }
    if outputs["matches"].exists() and outputs["status"].exists() and not force:
        cached = read_json("reports/tables/matching_summary.json", {})
        return {
            **cached,
            "status": "reused",
            "outputs": {key: str(value) for key, value in outputs.items()},
        }
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    config = load_yaml("configs/matching.yaml")
    connection = duckdb.connect()
    try:
        connection.execute(
            f"CREATE VIEW spotify AS SELECT * FROM read_parquet('{_sql_path(spotify_path)}')"
        )
        connection.execute(
            f"CREATE VIEW lfm AS SELECT * FROM read_parquet('{_sql_path(lfm_path)}')"
        )
        base_condition = (
            "s.composition_key = l.lfm_composition_key AND "
            "s.composition_key IS NOT NULL AND l.lfm_composition_key IS NOT NULL"
        )
        unions = [
            _candidate_select(
                "raw_exact",
                1,
                "s.artist_name_raw = l.artist_name_raw AND s.track_name_raw = l.track_name_raw",
                "s.artist_name_raw IS NOT NULL AND s.track_name_raw IS NOT NULL",
            ),
            _candidate_select(
                "strict_normalized",
                2,
                "s.artist_strict = l.lfm_artist_strict AND s.title_strict = l.lfm_title_strict",
                "s.artist_strict IS NOT NULL AND s.title_strict IS NOT NULL",
            ),
            _candidate_select(
                "conservative_normalized",
                3,
                "s.artist_conservative = l.lfm_artist_conservative AND s.title_conservative = l.lfm_title_conservative",
                "s.artist_conservative IS NOT NULL AND s.title_conservative IS NOT NULL",
            ),
            _candidate_select(
                "base_title_version_compatible",
                4,
                base_condition,
                f"s.artist_conservative IS NOT NULL AND ({_version_compatibility_sql()})",
            ),
        ]
        connection.execute("CREATE TEMP TABLE candidate_union AS " + " UNION ALL ".join(unions))
        connection.execute("""
            CREATE TEMP TABLE deterministic_candidates AS
            SELECT * EXCLUDE (pair_rank) FROM (
                SELECT *, row_number() OVER (
                    PARTITION BY spotify_track_id, lfm_record_key ORDER BY method_priority
                ) pair_rank
                FROM candidate_union
            ) WHERE pair_rank = 1
        """)
        connection.execute(
            """
            CREATE TEMP TABLE classified_candidates AS
            WITH counted AS (
                SELECT *,
                    count(*) OVER (PARTITION BY spotify_track_id) AS spotify_candidate_count,
                    count(*) OVER (PARTITION BY lfm_record_key) AS lfm_spotify_count
                FROM deterministic_candidates
            )
            SELECT *,
                CASE
                    WHEN NOT version_compatible THEN 'rejected'
                    WHEN spotify_candidate_count > 1 OR lfm_spotify_count > 1 THEN 'ambiguous'
                    WHEN match_method IN ('raw_exact', 'strict_normalized') THEN 'accepted_high_confidence'
                    WHEN match_method IN ('conservative_normalized', 'base_title_version_compatible') THEN 'accepted_with_rules'
                    ELSE 'candidate_for_review'
                END AS match_status,
                CASE
                    WHEN NOT version_compatible THEN 'version_incompatible'
                    WHEN spotify_candidate_count > 1 OR lfm_spotify_count > 1 THEN 'non_unique_mapping'
                    WHEN match_method IN ('raw_exact', 'strict_normalized') THEN 'unique_exact_or_strict_pair'
                    ELSE 'unique_conservative_pair_with_compatible_version'
                END AS acceptance_reason,
                (spotify_candidate_count > 1 OR lfm_spotify_count > 1) AS ambiguity_flag,
                ? AS matching_version
            FROM counted
        """,
            [config["version"]],
        )
        fuzzy_temp = project_path("data/interim/fuzzy_candidates.parquet")
        fuzzy_count = _write_fuzzy_candidates(connection, fuzzy_temp, config)
        connection.execute(
            f"CREATE VIEW fuzzy_candidates AS SELECT * FROM read_parquet('{_sql_path(fuzzy_temp)}')"
        )
        all_path = _sql_path(outputs["all"])
        connection.execute(
            f"COPY (SELECT * FROM classified_candidates UNION ALL BY NAME SELECT * FROM fuzzy_candidates) "
            f"TO '{all_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        connection.execute(
            f"COPY (SELECT * FROM classified_candidates WHERE match_status LIKE 'accepted%') "
            f"TO '{_sql_path(outputs['matches'])}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        for key, status in (("ambiguous", "ambiguous"), ("rejected", "rejected")):
            connection.execute(
                f"COPY (SELECT * FROM classified_candidates WHERE match_status = '{status}') "
                f"TO '{_sql_path(outputs[key])}' (FORMAT PARQUET, COMPRESSION ZSTD)"
            )
        connection.execute(
            f"COPY (SELECT * FROM fuzzy_candidates) TO '{_sql_path(outputs['review'])}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        connection.execute("""
            CREATE TEMP TABLE spotify_status AS
            WITH deterministic_status AS (
                SELECT spotify_track_id,
                    CASE
                        WHEN count(*) FILTER (WHERE match_status = 'accepted_high_confidence') > 0 THEN 'accepted_high_confidence'
                        WHEN count(*) FILTER (WHERE match_status = 'accepted_with_rules') > 0 THEN 'accepted_with_rules'
                        WHEN count(*) FILTER (WHERE match_status = 'ambiguous') > 0 THEN 'ambiguous'
                        WHEN count(*) FILTER (WHERE match_status = 'rejected') > 0 THEN 'rejected'
                        ELSE NULL
                    END AS status
                FROM classified_candidates GROUP BY 1
            ), fuzzy_status AS (
                SELECT DISTINCT spotify_track_id FROM fuzzy_candidates
            )
            SELECT s.track_id,
                coalesce(d.status,
                    CASE WHEN f.spotify_track_id IS NOT NULL THEN 'candidate_for_review' ELSE 'unmatched' END
                ) AS match_status
            FROM spotify s
            LEFT JOIN deterministic_status d ON s.track_id = d.spotify_track_id
            LEFT JOIN fuzzy_status f ON s.track_id = f.spotify_track_id
        """)
        connection.execute(
            f"COPY (SELECT s.* EXCLUDE (track_id), s.track_id, st.match_status FROM spotify s "
            f"JOIN spotify_status st ON s.track_id = st.track_id) TO '{_sql_path(outputs['status'])}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        connection.execute(
            f"COPY (SELECT s.* FROM spotify s JOIN spotify_status st ON s.track_id = st.track_id "
            f"WHERE st.match_status = 'unmatched') TO '{_sql_path(outputs['unmatched'])}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        connection.execute(
            f"COPY (SELECT s.*, l.* EXCLUDE (artist_name_raw, track_name_raw), "
            "l.artist_name_raw AS lfm_artist_name_raw, l.track_name_raw AS lfm_track_name_raw, "
            "m.match_method, m.match_score, m.match_status, m.acceptance_reason, m.version_compatible, "
            "m.temporal_compatible, m.matching_version FROM classified_candidates m "
            "JOIN spotify s ON m.spotify_track_id = s.track_id "
            "JOIN lfm l ON m.lfm_record_key = l.lfm_record_key "
            f"WHERE m.match_status LIKE 'accepted%') TO '{_sql_path(outputs['modeling'])}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)"
        )
        sample_size = int(config.get("review_sample_size_per_stratum", 25))
        connection.execute(
            f"COPY (SELECT * EXCLUDE (sample_rank) FROM (SELECT *, row_number() OVER "
            "(PARTITION BY match_status, match_method ORDER BY hash(spotify_track_id, lfm_record_key)) sample_rank "
            f"FROM read_parquet('{all_path}')) WHERE sample_rank <= {sample_size}) "
            f"TO '{_sql_path(outputs['sample'])}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        counts = dict(
            connection.execute(
                "SELECT match_status, count(DISTINCT spotify_track_id) FROM read_parquet(?) GROUP BY 1",
                [str(outputs["all"])],
            ).fetchall()
        )
        methods = [
            dict(zip(("method", "status", "candidate_rows", "spotify_tracks"), row, strict=True))
            for row in connection.execute(
                "SELECT match_method, match_status, count(*), count(DISTINCT spotify_track_id) "
                "FROM read_parquet(?) GROUP BY 1, 2 ORDER BY 1, 2",
                [str(outputs["all"])],
            ).fetchall()
        ]
        total_spotify = connection.execute("SELECT count(*) FROM spotify").fetchone()[0]
        for row in methods:
            row["percent_of_spotify_tracks"] = round(100 * row["spotify_tracks"] / total_spotify, 6)
        multiplicities = [
            dict(
                zip(
                    ("mapping_type", "candidate_rows", "spotify_tracks", "lfm_records"),
                    row,
                    strict=True,
                )
            )
            for row in connection.execute(
                "SELECT CASE WHEN spotify_candidate_count = 1 AND lfm_spotify_count = 1 "
                "THEN 'one_to_one' WHEN spotify_candidate_count > 1 AND lfm_spotify_count = 1 "
                "THEN 'one_spotify_to_many_lfm' WHEN spotify_candidate_count = 1 "
                "AND lfm_spotify_count > 1 THEN 'many_spotify_to_one_lfm' ELSE 'many_to_many' END, "
                "count(*), count(DISTINCT spotify_track_id), count(DISTINCT lfm_record_key) "
                "FROM classified_candidates GROUP BY 1 ORDER BY 1"
            ).fetchall()
        ]
        result = {
            "status": "created",
            "generated_at": utc_now(),
            "spotify_rows": total_spotify,
            "fuzzy_candidate_rows": fuzzy_count,
            "unique_spotify_tracks_by_candidate_status": counts,
            "by_method_and_status": methods,
            "deterministic_multiplicity": multiplicities,
            "outputs": {key: str(value) for key, value in outputs.items()},
        }
        write_json("reports/tables/matching_summary.json", result)
        return result
    finally:
        connection.close()


def analyze_selection_bias() -> dict[str, Any]:
    path = project_path("data/processed/spotify_tracks_with_match_status.parquet")
    if not path.exists():
        raise FileNotFoundError("Execute o matching antes do diagnóstico de seleção.")
    source = _sql_path(path)
    relation = f"read_parquet('{source}')"
    matched = "match_status IN ('accepted_high_confidence', 'accepted_with_rules')"
    connection = duckdb.connect()
    try:
        total, matched_count = connection.execute(
            f"SELECT count(*), count(*) FILTER (WHERE {matched}) FROM {relation}"
        ).fetchone()
        dimensions = {}
        for name in ("year", "temporal_cohort", "genre"):
            rows = connection.execute(
                f"SELECT {name}, count(*) total, count(*) FILTER (WHERE {matched}) matched_count, "
                f"100.0 * count(*) FILTER (WHERE {matched}) / count(*) match_rate_percent "
                f"FROM {relation} GROUP BY 1 ORDER BY 1"
            ).fetchall()
            dimensions[name] = [
                {name: row[0], "total": row[1], "matched": row[2], "match_rate_percent": row[3]}
                for row in rows
            ]
        popularity_bands = connection.execute(
            f"SELECT CASE WHEN spotify_popularity = 0 THEN 'zero' "
            "WHEN spotify_popularity BETWEEN 1 AND 10 THEN '01-10' "
            "WHEN spotify_popularity BETWEEN 11 AND 25 THEN '11-25' "
            "WHEN spotify_popularity BETWEEN 26 AND 50 THEN '26-50' "
            "WHEN spotify_popularity BETWEEN 51 AND 75 THEN '51-75' "
            "WHEN spotify_popularity > 75 THEN '76-100' ELSE 'missing' END band, "
            f"count(*) total, count(*) FILTER (WHERE {matched}) matched_count, "
            f"100.0 * count(*) FILTER (WHERE {matched}) / count(*) rate FROM {relation} GROUP BY 1 ORDER BY 1"
        ).fetchall()
        numeric_columns = [
            "spotify_popularity",
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
        ]
        numeric = {}
        for name in numeric_columns:
            values = connection.execute(
                f"SELECT avg({name}) FILTER (WHERE {matched}), median({name}) FILTER (WHERE {matched}), "
                f"var_samp({name}) FILTER (WHERE {matched}), avg({name}) FILTER (WHERE NOT ({matched})), "
                f"median({name}) FILTER (WHERE NOT ({matched})), var_samp({name}) FILTER (WHERE NOT ({matched})) "
                f"FROM {relation}"
            ).fetchone()
            mean_m, median_m, var_m, mean_u, median_u, var_u = values
            pooled = (
                math.sqrt((var_m + var_u) / 2)
                if var_m is not None and var_u is not None and (var_m + var_u) > 0
                else None
            )
            numeric[name] = {
                "matched_mean": mean_m,
                "matched_median": median_m,
                "unmatched_mean": mean_u,
                "unmatched_median": median_u,
                "standardized_mean_difference": (mean_m - mean_u) / pooled if pooled else None,
            }
        zero = connection.execute(
            f"SELECT 100.0 * avg((spotify_popularity = 0)::INT) FILTER (WHERE {matched}), "
            f"100.0 * avg((spotify_popularity = 0)::INT) FILTER (WHERE NOT ({matched})) FROM {relation}"
        ).fetchone()
        result = {
            "generated_at": utc_now(),
            "total_spotify": total,
            "matched": matched_count,
            "match_rate_percent": 100 * matched_count / total if total else 0,
            "by_dimension": dimensions,
            "by_popularity_band": [
                {"band": row[0], "total": row[1], "matched": row[2], "match_rate_percent": row[3]}
                for row in popularity_bands
            ],
            "numeric_comparison": numeric,
            "spotify_popularity_zero_percent": {"matched": zero[0], "unmatched": zero[1]},
            "warning": (
                "O subconjunto encontrado não deve ser tratado como aleatório ou representativo. "
                "As diferenças descrevem cobertura do cruzamento e não sustentam explicação nem causalidade."
            ),
        }
        write_json("reports/tables/selection_bias.json", result)
        return result
    finally:
        connection.close()
