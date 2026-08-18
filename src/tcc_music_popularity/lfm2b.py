"""Inspeção e transformação incremental do JSONL comprimido do LFM2b."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import duckdb
import polars as pl

from .config import load_pipeline_config, load_sources_config, project_path
from .io import read_json, sha256_file, update_manifest, utc_now, write_json
from .normalization import add_normalized_columns


def _walk_paths(value: Any, prefix: str = "") -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict):
        for key in sorted(value):
            child = f"{prefix}.{key}" if prefix else key
            yield from _walk_paths(value[key], child)
    else:
        yield prefix, value


def _sanitize(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z]+", "_", value).strip("_").lower()
    return re.sub(r"_+", "_", value)


def final_column_name(original: str) -> str:
    special = {
        "_id.artist": "artist_name_raw",
        "_id.track": "track_name_raw",
        "release.$date": "lfm_release_date",
        "release": "lfm_release_date",
        "popularity": "genius_lyrics_views",
        "lfm_playcount": "lfm_playcount",
        "genre": "lfm_genre",
    }
    if original in special:
        return special[original]
    if original.startswith("features."):
        return f"lfm_{_sanitize(original.removeprefix('features.'))}"
    return f"lfm_{_sanitize(original)}"


def _scalar(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def _release_year(value: Any) -> int | None:
    if value is None:
        return None
    match = re.search(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)", str(value))
    if match:
        return int(match.group(1))
    try:
        from datetime import UTC, datetime

        return datetime.fromtimestamp(int(value) / 1000, tz=UTC).year
    except (OverflowError, TypeError, ValueError):
        return None


def flatten_record(
    record: dict[str, Any], row_number: int
) -> tuple[dict[str, Any], dict[str, str]]:
    flat: dict[str, Any] = {}
    name_map: dict[str, str] = {}
    for original, value in _walk_paths(record):
        final = final_column_name(original)
        if final in flat and name_map.get(original) != final:
            suffix = hashlib.sha1(original.encode()).hexdigest()[:8]
            final = f"{final}_{suffix}"
        flat[final] = _scalar(value)
        name_map[original] = final
    artist = flat.get("artist_name_raw")
    title = flat.get("track_name_raw")
    release = flat.get("lfm_release_date") or flat.get("lfm_release_date_numberlong")
    identity = f"{artist}\0{title}\0{release}"
    flat["lfm_record_key"] = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    flat["lfm_source_row_number"] = row_number
    flat["lfm_release_year"] = _release_year(release)
    if flat.get("lfm_release_year") is not None:
        year = flat["lfm_release_year"]
        flat["lfm_temporal_cohort"] = (
            "2000-2009"
            if 2000 <= year <= 2009
            else "2010-2019"
            if 2010 <= year <= 2019
            else "2020-2023"
            if 2020 <= year <= 2023
            else "outside_main_period"
        )
    else:
        flat["lfm_temporal_cohort"] = "missing_release_year"
    return flat, name_map


def canonicalize_release_years(path: Path) -> None:
    """Deriva ano/coorte das duas representações MongoDB sem apagar os campos originais."""
    schema = pl.read_parquet_schema(path)
    temporary = path.with_suffix(".dates.tmp.parquet")
    source = path.as_posix().replace("'", "''")
    target = temporary.as_posix().replace("'", "''")
    year_expression = "lfm_release_year"
    if "lfm_release_date_numberlong" in schema:
        year_expression = (
            "coalesce(lfm_release_year, "
            "year(epoch_ms(try_cast(lfm_release_date_numberlong AS BIGINT))))"
        )
    star = (
        "* EXCLUDE (lfm_qf_release_year_implausible)"
        if "lfm_qf_release_year_implausible" in schema
        else "*"
    )
    connection = duckdb.connect()
    try:
        connection.execute(
            f"COPY (SELECT {star} REPLACE ({year_expression} AS lfm_release_year, "
            f"CASE WHEN {year_expression} BETWEEN 2000 AND 2009 THEN '2000-2009' "
            f"WHEN {year_expression} BETWEEN 2010 AND 2019 THEN '2010-2019' "
            f"WHEN {year_expression} BETWEEN 2020 AND 2023 THEN '2020-2023' "
            f"WHEN {year_expression} IS NULL THEN 'missing_release_year' "
            "ELSE 'outside_main_period' END AS lfm_temporal_cohort), "
            f"({year_expression} < 1850 OR {year_expression} > 2030) "
            "AS lfm_qf_release_year_implausible "
            f"FROM read_parquet('{source}')) TO '{target}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)"
        )
    finally:
        connection.close()
    temporary.replace(path)


def inspect_lfm2b(path: Path, sample_lines: int = 25) -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    paths: dict[str, set[str]] = defaultdict(set)
    invalid: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for row_number, line in enumerate(handle, start=1):
            if row_number > sample_lines:
                break
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                invalid.append({"row": row_number, "error": str(exc), "sample": line[:500]})
                continue
            if not isinstance(record, dict):
                invalid.append(
                    {"row": row_number, "error": "JSON não é objeto", "sample": line[:500]}
                )
                continue
            samples.append(record)
            for key, value in _walk_paths(record):
                paths[key].add(type(value).__name__)
    inspection = {
        "inspected_at": utc_now(),
        "sample_lines_requested": sample_lines,
        "valid_samples": len(samples),
        "invalid_samples": invalid,
        "observed_paths": {key: sorted(types) for key, types in sorted(paths.items())},
        "top_level_keys": sorted({key for sample in samples for key in sample}),
        "first_records": samples[:3],
    }
    write_json("reports/tables/lfm2b_schema_inspection.json", inspection)
    return inspection


def _write_chunk(records: list[dict[str, Any]], destination: Path) -> dict[str, str]:
    columns = sorted({key for record in records for key in record})
    aligned = [{key: record.get(key) for key in columns} for record in records]
    frame = pl.DataFrame(aligned, infer_schema_length=None, strict=False)
    frame = add_normalized_columns(frame, "artist_name_raw", "track_name_raw", prefix="lfm")
    frame.write_parquet(destination, compression="zstd", statistics=True)
    return {name: str(dtype) for name, dtype in frame.schema.items()}


def normalize_lfm2b(force: bool = False) -> dict[str, Any]:
    config = load_pipeline_config()
    source = load_sources_config()["lfm2b"]
    input_path = project_path(source["local_path"])
    output_path = project_path("data/interim/lfm2b_normalized.parquet")
    processed_path = project_path("data/processed/lfm2b_tracks.parquet")
    state_path = project_path("data/interim/lfm2b_state.json")
    chunks_dir = project_path("data/interim/lfm2b_chunks")
    if not input_path.exists():
        raise FileNotFoundError(f"LFM2b ausente em {input_path}")

    manifest = read_json("data/raw/manifest.json", {"sources": {}})
    input_hash = manifest.get("sources", {}).get("lfm2b", {}).get("sha256") or sha256_file(
        input_path
    )
    previous_state = read_json(state_path, {})
    if (
        not force
        and output_path.exists()
        and processed_path.exists()
        and previous_state.get("input_sha256") == input_hash
        and previous_state.get("status") == "complete"
    ):
        return {
            "status": "reused",
            "rows": previous_state.get("valid_rows"),
            "path": str(processed_path),
        }

    inspect_lfm2b(input_path)
    if chunks_dir.exists():
        resolved = chunks_dir.resolve()
        if resolved.parent != project_path("data/interim").resolve():
            raise RuntimeError(f"Recusa em limpar diretório inesperado: {resolved}")
        shutil.rmtree(chunks_dir)
    chunks_dir.mkdir(parents=True)
    rejected_path = project_path("data/rejected/lfm2b_invalid_json.jsonl")
    rejected_path.parent.mkdir(parents=True, exist_ok=True)

    chunk_size = int(config["chunk_size"])
    batch: list[dict[str, Any]] = []
    path_types: dict[str, Counter[str]] = defaultdict(Counter)
    name_map: dict[str, str] = {}
    schemas: list[dict[str, str]] = []
    valid_rows = 0
    invalid_rows = 0
    chunk_index = 0
    with (
        gzip.open(input_path, "rt", encoding="utf-8") as handle,
        rejected_path.open("w", encoding="utf-8") as rejected,
    ):
        for row_number, line in enumerate(handle, start=1):
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise TypeError("JSON não é objeto")
            except (json.JSONDecodeError, TypeError) as exc:
                invalid_rows += 1
                rejected.write(
                    json.dumps(
                        {"row": row_number, "error": str(exc), "sample": line[:500]},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                continue
            for key, value in _walk_paths(record):
                path_types[key][type(value).__name__] += 1
            flattened, current_map = flatten_record(record, row_number)
            name_map.update(current_map)
            batch.append(flattened)
            valid_rows += 1
            if len(batch) >= chunk_size:
                chunk_index += 1
                schemas.append(_write_chunk(batch, chunks_dir / f"part-{chunk_index:05d}.parquet"))
                batch.clear()
        if batch:
            chunk_index += 1
            schemas.append(_write_chunk(batch, chunks_dir / f"part-{chunk_index:05d}.parquet"))

    if valid_rows == 0:
        raise ValueError("Nenhum objeto JSON válido encontrado no LFM2b.")
    glob = (chunks_dir / "*.parquet").as_posix().replace("'", "''")
    out = output_path.as_posix().replace("'", "''")
    connection = duckdb.connect()
    try:
        connection.execute(
            f"COPY (SELECT * FROM read_parquet('{glob}', union_by_name=true)) TO '{out}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)"
        )
    finally:
        connection.close()
    canonicalize_release_years(output_path)
    shutil.copyfile(output_path, processed_path)
    final_schema = {name: str(dtype) for name, dtype in pl.read_parquet_schema(output_path).items()}
    inventory = {
        "generated_at": utc_now(),
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "chunks": chunk_index,
        "paths": {
            key: {"types": dict(counts), "final_name": name_map.get(key)}
            for key, counts in sorted(path_types.items())
        },
        "schema_changes": {
            key: sorted(counts) for key, counts in path_types.items() if len(counts) > 1
        },
        "final_schema": final_schema,
        "descriptor_columns": sorted(
            name
            for name in final_schema
            if name.startswith("lfm_")
            and not name.startswith("lfm_qf_")
            and name
            not in {
                "lfm_record_key",
                "lfm_source_row_number",
                "lfm_release_date",
                "lfm_release_date_numberlong",
                "lfm_release_year",
                "lfm_temporal_cohort",
                "lfm_genre",
                "lfm_playcount",
            }
        ),
    }
    write_json("reports/tables/lfm2b_schema_inventory.json", inventory)
    write_json("docs/lfm2b_original_to_final_map.json", name_map)
    state = {
        "status": "complete",
        "input_sha256": input_hash,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "chunks": chunk_index,
        "completed_at": utc_now(),
    }
    write_json(state_path, state)
    metadata = manifest.get("sources", {}).get("lfm2b", {})
    metadata.update(
        {
            "record_count": valid_rows,
            "invalid_record_count": invalid_rows,
            "schema_observed": final_schema,
            "verification_status": "audited_and_normalized",
            "verified_at": utc_now(),
        }
    )
    update_manifest("lfm2b", metadata)
    return {
        "status": "created",
        "rows": valid_rows,
        "invalid": invalid_rows,
        "path": str(processed_path),
    }


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def audit_lfm2b() -> dict[str, Any]:
    path = project_path("data/processed/lfm2b_tracks.parquet")
    if not path.exists():
        normalize_lfm2b()
    connection = duckdb.connect()
    source = path.as_posix().replace("'", "''")
    relation = f"read_parquet('{source}')"
    try:
        schema_rows = connection.execute(f"DESCRIBE SELECT * FROM {relation}").fetchall()
        columns = [row[0] for row in schema_rows]
        row_count = connection.execute(f"SELECT count(*) FROM {relation}").fetchone()[0]
        missing = {}
        for start in range(0, len(columns), 50):
            batch = columns[start : start + 50]
            sql = ", ".join(
                f"count(*) FILTER (WHERE {_quote(name)} IS NULL) AS {_quote(name)}"
                for name in batch
            )
            values = connection.execute(f"SELECT {sql} FROM {relation}").fetchone()
            missing.update({name: int(value) for name, value in zip(batch, values, strict=True)})
        duplicates = (
            connection.execute(
                f"SELECT sum(n - 1) FROM (SELECT count(*) n FROM {relation} GROUP BY lfm_record_key HAVING n > 1)"
            ).fetchone()[0]
            or 0
        )
        artist_title_duplicates = (
            connection.execute(
                f"SELECT sum(n - 1) FROM (SELECT count(*) n FROM {relation} "
                "GROUP BY artist_name_raw, track_name_raw HAVING n > 1)"
            ).fetchone()[0]
            or 0
        )
        by_cohort = connection.execute(
            f"SELECT lfm_temporal_cohort, count(*) n FROM {relation} GROUP BY 1 ORDER BY n DESC"
        ).fetchall()
        by_genre = (
            connection.execute(
                f"SELECT lfm_genre, count(*) n FROM {relation} GROUP BY 1 ORDER BY n DESC"
            ).fetchall()
            if "lfm_genre" in columns
            else []
        )
        numeric_audits = {}
        for name in ("genius_lyrics_views", "lfm_playcount"):
            if name not in columns:
                continue
            numeric_audits[name] = dict(
                zip(
                    ("non_null", "numeric", "negative", "minimum", "median", "mean", "maximum"),
                    connection.execute(
                        f"SELECT count({_quote(name)}), count(try_cast({_quote(name)} AS DOUBLE)), "
                        f"count(*) FILTER (WHERE try_cast({_quote(name)} AS DOUBLE) < 0), "
                        f"min(try_cast({_quote(name)} AS DOUBLE)), median(try_cast({_quote(name)} AS DOUBLE)), "
                        f"avg(try_cast({_quote(name)} AS DOUBLE)), max(try_cast({_quote(name)} AS DOUBLE)) FROM {relation}"
                    ).fetchone(),
                    strict=True,
                )
            )
        descriptor_columns = [
            name
            for name in columns
            if name.startswith("lfm_")
            and not name.startswith("lfm_qf_")
            and name
            not in {
                "lfm_record_key",
                "lfm_source_row_number",
                "lfm_release_date",
                "lfm_release_date_numberlong",
                "lfm_release_year",
                "lfm_temporal_cohort",
                "lfm_genre",
                "lfm_playcount",
                "lfm_artist_unicode",
                "lfm_artist_strict",
                "lfm_artist_conservative",
                "lfm_artist_primary",
                "lfm_artist_collaborators_json",
                "lfm_title_unicode",
                "lfm_title_strict",
                "lfm_title_conservative",
                "lfm_title_base",
                "lfm_composition_key",
                "lfm_normalization_version",
                "lfm_version_tags",
                "lfm_year_mentioned",
            }
            and not name.startswith(
                (
                    "lfm_remaster",
                    "lfm_remix",
                    "lfm_live",
                    "lfm_acoustic",
                    "lfm_radio_edit",
                    "lfm_mono_stereo",
                    "lfm_instrumental",
                    "lfm_demo",
                )
            )
        ]
        audit = {
            "generated_at": utc_now(),
            "rows": row_count,
            "columns": len(columns),
            "schema": {row[0]: row[1] for row in schema_rows},
            "missing": {
                name: {"count": count, "percent": round(100 * count / row_count, 6)}
                for name, count in missing.items()
            },
            "duplicate_original_key_excess_rows": int(duplicates),
            "duplicate_artist_title_excess_rows": int(artist_title_duplicates),
            "release_year_min_max": connection.execute(
                f"SELECT min(lfm_release_year), max(lfm_release_year) FROM {relation}"
            ).fetchone(),
            "by_cohort": [{"cohort": row[0], "count": row[1]} for row in by_cohort],
            "by_genre": [{"genre": row[0], "count": row[1]} for row in by_genre],
            "popularity_metrics": numeric_audits,
            "quality_flags": {
                "lfm_qf_release_year_implausible": connection.execute(
                    f"SELECT count(*) FILTER (WHERE lfm_qf_release_year_implausible) FROM {relation}"
                ).fetchone()[0]
            },
            "descriptor_count": len(descriptor_columns),
            "descriptor_names": descriptor_columns,
            "semantic_note": {
                "genius_lyrics_views": "Campo original popularity; visualizações da letra no Genius segundo Zenodo/artigo.",
                "lfm_playcount": "Contagem de eventos de escuta na base LFM-2b; mantida separada.",
            },
        }
        write_json("reports/tables/lfm2b_audit.json", audit)
        return audit
    finally:
        connection.close()
