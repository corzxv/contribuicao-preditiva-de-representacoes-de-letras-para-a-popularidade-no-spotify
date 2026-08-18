"""Catálogo DuckDB da base analítica."""

from __future__ import annotations

from typing import Any

import duckdb

from .config import project_path
from .io import utc_now, write_json

DATASETS = {
    "spotify_tracks": ("data/processed/spotify_tracks.parquet", "uma linha por registro Spotify"),
    "lfm2b_tracks": ("data/processed/lfm2b_tracks.parquet", "uma linha por registro LFM2b"),
    "spotify_lfm_all_candidates": (
        "data/processed/spotify_lfm_all_candidates.parquet",
        "uma linha por par candidato",
    ),
    "spotify_lfm_matches": (
        "data/processed/spotify_lfm_matches.parquet",
        "uma linha por par aceito",
    ),
    "spotify_lfm_ambiguous": (
        "data/processed/spotify_lfm_ambiguous.parquet",
        "uma linha por par ambíguo",
    ),
    "spotify_lfm_candidates_review": (
        "data/processed/spotify_lfm_candidates_review.parquet",
        "uma linha por candidato fuzzy pendente",
    ),
    "spotify_lfm_rejected": (
        "data/processed/spotify_lfm_rejected.parquet",
        "uma linha por candidato rejeitado",
    ),
    "spotify_lfm_unmatched": (
        "data/processed/spotify_lfm_unmatched.parquet",
        "uma linha por registro Spotify sem candidato",
    ),
    "spotify_tracks_with_match_status": (
        "data/processed/spotify_tracks_with_match_status.parquet",
        "uma linha por registro Spotify",
    ),
    "modeling_base_lfm_v0_1": (
        "data/processed/modeling_base_lfm_v0_1.parquet",
        "uma linha por par Spotify-LFM2b aceito",
    ),
}


def _quote(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def build_database() -> dict[str, Any]:
    output = project_path("data/processed/music_tcc.duckdb")
    output.parent.mkdir(parents=True, exist_ok=True)
    available: dict[str, Any] = {}
    connection = duckdb.connect(str(output))
    try:
        for table, (relative_path, grain) in DATASETS.items():
            path = project_path(relative_path)
            if not path.exists():
                available[table] = {"status": "missing", "path": relative_path, "grain": grain}
                continue
            sql_path = path.as_posix().replace("'", "''")
            connection.execute(
                f"CREATE OR REPLACE VIEW {_quote(table)} AS SELECT * FROM read_parquet('{sql_path}')"
            )
            rows = connection.execute(f"SELECT count(*) FROM {_quote(table)}").fetchone()[0]
            available[table] = {
                "status": "view_created",
                "path": relative_path,
                "grain": grain,
                "rows": rows,
            }
        connection.execute("""
            CREATE TABLE IF NOT EXISTS dataset_catalog (
                dataset_name VARCHAR PRIMARY KEY,
                relative_path VARCHAR,
                grain VARCHAR,
                row_count BIGINT,
                updated_at TIMESTAMP
            )
        """)
        for table, metadata in available.items():
            if metadata["status"] != "view_created":
                continue
            connection.execute("DELETE FROM dataset_catalog WHERE dataset_name = ?", [table])
            connection.execute(
                "INSERT INTO dataset_catalog VALUES (?, ?, ?, ?, current_timestamp)",
                [table, metadata["path"], metadata["grain"], metadata["rows"]],
            )
    finally:
        connection.close()
    result = {"generated_at": utc_now(), "database": str(output), "datasets": available}
    write_json("reports/tables/duckdb_catalog.json", result)
    return result
