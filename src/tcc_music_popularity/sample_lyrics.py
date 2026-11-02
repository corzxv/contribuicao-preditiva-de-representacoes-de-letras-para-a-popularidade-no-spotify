"""Adaptador da busca local existente para a amostra fixa, com estado independente."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import sqlite3
import sys
import time
from contextlib import ExitStack, closing
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from . import local_lyrics as local
from .catalog_audit import ACOUSTIC, ROOT, markdown_table, sha256
from .catalog_sampling import Comparison, numeric_values, text_column, weighted_summary
from .io import utc_now
from .lyrics_ambiguity_v011 import _representative_sort_key, strict_plain_text_metrics
from .lyrics_embeddings_v020 import detect_language
from .lyrics_pilot import (
    VERSION_FLAGS,
    _candidate_diagnostics,
    _text_present,
    _version_flags,
    pilot_base_title,
)
from .manual_lyrics import (
    atomic_frame,
    atomic_json,
    exclusive,
    fingerprint,
    meta_get,
    meta_put,
    require,
)
from .normalization import conservative_normalize

VERSION = "sample-local-200k-v1"
SAMPLE_DIR = ROOT / "reports/amostra_spotify_200k_20261031"
WORKSPACE = ROOT / "data/derived/private_sample_lyrics_200k_v1"
OUTPUT = ROOT / "reports/busca_local_200k_20261031"
INDEX = local.DEFAULT_DESTINATION / "tcc_lookup_sample_200k_v1"
PROTOCOL = ROOT / "docs/protocolo_busca_local_200k.md"
STATUSES = [
    "accepted",
    "ambiguous",
    "not_found",
    "no_text",
    "instrumental",
    "insufficient_metadata",
    "technical_error",
    "pending",
]
MATCH_FIELDS = {
    "artist_name_query",
    "track_name_query",
    "title_base_query",
    "duration_seconds",
    *VERSION_FLAGS,
}
TOLERANCE = 10.0
STATE_SQL = """
CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE queries(query_id TEXT PRIMARY KEY,data TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',
 attempts INTEGER NOT NULL DEFAULT 0,result TEXT,elapsed_seconds REAL);
CREATE TABLE tracks(track_id TEXT PRIMARY KEY,query_id TEXT REFERENCES queries(query_id));
CREATE INDEX tracks_query ON tracks(query_id);
CREATE TABLE evidence(query_id TEXT PRIMARY KEY REFERENCES queries(query_id),payload TEXT NOT NULL);
CREATE TABLE lyrics(query_id TEXT PRIMARY KEY REFERENCES queries(query_id),data TEXT NOT NULL);
CREATE TABLE runs(id INTEGER PRIMARY KEY,data TEXT NOT NULL);
"""


def stable_readonly(path: Path):
    """Não ignorar transações WAL pendentes ao usar immutable em índice/checkpoint antigo."""
    wal = Path(str(path) + "-wal")
    require(
        not wal.exists() or wal.stat().st_size == 0,
        "Há WAL não vazio na fonte/índice antigo. Encerre o escritor e aguarde checkpoint; não apague WAL.",
    )
    return local.readonly(path)


def query_for_metadata(row: dict[str, Any]) -> dict[str, Any] | None:
    require(
        set(row) <= {"track_id", "artist_name", "track_name", "duration_ms"},
        "Consulta recebeu campos não autorizados (alvo/gênero/peso não podem entrar).",
    )

    def clean(value):
        if value is None:
            return None
        value = str(value).strip(" ")
        return None if value in {"", "NA", "N/A", "null", "None"} else value

    artist, title = clean(row.get("artist_name")), clean(row.get("track_name"))
    if not conservative_normalize(artist) or not conservative_normalize(title):
        return None
    try:
        duration = float(row.get("duration_ms")) / 1000
        if not math.isfinite(duration) or duration <= 0:
            duration = None
    except (ValueError, TypeError):
        duration = None
    return {
        "artist_name_query": artist,
        "track_name_query": title,
        "title_base_query": pilot_base_title(title),
        "duration_seconds": duration,
        **_version_flags(title),
    }


def classify(query, candidates, incomplete=None):
    """Reutiliza diagnósticos/fingerprint; nenhum alvo, fuzzy ou fingerprint flexível."""
    require(set(query) <= MATCH_FIELDS, "Campo não autorizado no matching.")
    result = {
        "status": "ambiguous",
        "reason": incomplete,
        "method": "sqlite_snapshot_exact",
        "rules_version": VERSION,
        "candidate_count": len(candidates) if not incomplete else None,
        "candidate_present": bool(candidates) if not incomplete else True,
        "text_present": any(
            _text_present(c.get("plainLyrics")) or _text_present(c.get("syncedLyrics"))
            for c in candidates
        )
        if not incomplete
        else None,
        "plain_present": any(_text_present(c.get("plainLyrics")) for c in candidates)
        if not incomplete
        else None,
        "synced_present": any(_text_present(c.get("syncedLyrics")) for c in candidates)
        if not incomplete
        else None,
        "enumeration_complete": incomplete is None,
        "selected_lrclib_id": None,
        "selected_lyrics_id": None,
        "text_sha256": None,
        "strict_text_sha256": None,
        "eligible_count": 0,
        "equivalent_count": 0,
        "language_status": "not_evaluated",
    }
    if incomplete:
        return result, None
    if not candidates:
        return {**result, "status": "not_found", "reason": "no_normalized_metadata_candidate"}, None
    # Contradição de payload para o mesmo ID não pode ser apagada por deduplicação.
    identities = {}
    for candidate in candidates:
        value = fingerprint(candidate)
        if candidate["id"] in identities and identities[candidate["id"]] != value:
            return {**result, "reason": "same_id_payload_conflict"}, None
        identities[candidate["id"]] = value
    unique = {c["id"]: c for c in candidates}
    evaluated = []
    for candidate in unique.values():
        diag = _candidate_diagnostics(query, candidate, TOLERANCE)
        # Mesma flag live/remix não prova a identidade de qualificadores diferentes.
        qualified = any(query.get(flag) for flag in VERSION_FLAGS) or any(
            _version_flags(candidate.get("trackName")).values()
        )
        if qualified and not diag["title_exact"]:
            diag = {**diag, "accepted_by_rules": False, "version_compatible": False}
        evaluated.append(
            {
                "candidate": candidate,
                "diagnostics": diag,
                "endpoints": ["sqlite"],
                "candidate_key_sha256": fingerprint(candidate["id"]),
            }
        )
    eligible = [item for item in evaluated if item["diagnostics"]["accepted_by_rules"]]
    result["eligible_count"] = len(eligible)
    if not eligible:
        version_conflict = any(
            item["diagnostics"]["artist_compatible"]
            and item["diagnostics"]["title_compatible"]
            and not item["diagnostics"]["version_compatible"]
            for item in evaluated
        )
        return {
            **result,
            "reason": "version_conflict" if version_conflict else "metadata_conflict",
        }, None
    plain = [item for item in eligible if _text_present(item["candidate"].get("plainLyrics"))]
    instruments = [item for item in eligible if item["candidate"].get("instrumental")]
    if instruments:
        if (
            len(instruments) == len(eligible)
            and not plain
            and not any(_text_present(i["candidate"].get("syncedLyrics")) for i in eligible)
        ):
            representative = sorted(eligible, key=_representative_sort_key)[0]["candidate"]
            return {
                **result,
                "status": "instrumental",
                "reason": "compatible_source_instrumental_no_text",
                "selected_lrclib_id": representative["id"],
                "selected_lyrics_id": representative.get("local_lyrics_id"),
            }, None
        return {**result, "reason": "instrumental_text_conflict"}, None
    if not plain:
        return {
            **result,
            "status": "no_text",
            "reason": "compatible_without_plain_synced_not_converted",
        }, None
    if len(plain) != len(eligible):
        return {**result, "reason": "eligible_candidates_without_plain_prevent_equivalence"}, None
    hashes = {
        strict_plain_text_metrics(item["candidate"]["plainLyrics"])["strict_text_sha256"]
        for item in plain
    }
    if len(hashes) != 1:
        return {**result, "reason": "distinct_strict_texts"}, None
    representative = sorted(plain, key=_representative_sort_key)[0]["candidate"]
    text = representative["plainLyrics"]
    result.update(
        status="accepted",
        reason="unique_compatible_plain" if len(plain) == 1 else "all_eligible_strict_equivalent",
        selected_lrclib_id=representative["id"],
        selected_lyrics_id=representative.get("local_lyrics_id"),
        text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        strict_text_sha256=next(iter(hashes)),
        equivalent_count=len(plain),
    )
    lyric = {
        "plain_text_source": text,
        "synced_text_source": representative.get("syncedLyrics"),
        "lrclib_id": representative["id"],
        "lrclib_lyrics_id": representative.get("local_lyrics_id"),
        "text_sha256": result["text_sha256"],
        "strict_text_sha256": result["strict_text_sha256"],
        "equivalent_lrclib_ids": sorted(i["candidate"]["id"] for i in plain),
        "text_origin": "plain_lyrics_unmodified",
        "representative_rule": "duration_delta_then_metadata_completeness_then_id_within_equivalent_set",
    }
    return result, lyric


def language_detector():
    if importlib.util.find_spec("langid") is None:
        return None, {"available": False, "status": "not_evaluated", "threshold": 0.80}
    try:
        from langid.langid import LanguageIdentifier, model

        identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        version = importlib.metadata.version("langid")
    except Exception as exc:
        return None, {
            "available": False,
            "status": "not_evaluated",
            "error_type": type(exc).__name__,
            "threshold": 0.80,
        }
    return identifier, {
        "available": True,
        "version": version,
        "model_sha256": hashlib.sha256(model).hexdigest(),
        "threshold": 0.80,
        "uncertainty": "normalized model score, not calibrated probability",
    }


def validate_sample(sample_path, summary_path, allocation_path, *, expected=200_000):
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    require(summary.get("completed") is True, "Resumo amostral incompleto.")
    require(
        sha256(sample_path) == summary["output_hashes"]["amostra_spotify_200k.parquet"],
        "Hash da amostra diverge do resumo.",
    )
    require(
        sha256(allocation_path) == summary["output_hashes"]["alocacao_amostra_200k.csv"],
        "Hash da alocação diverge.",
    )
    sample = pl.read_parquet(sample_path)
    required = {
        "track_id",
        "artist_name",
        "track_name",
        "duration_ms",
        "popularity",
        "year",
        "genre",
        *ACOUSTIC,
        "stratum_id",
        "N_h",
        "n_h",
        "inclusion_probability",
        "sampling_weight",
        "certainty_selection",
        "seed",
        "sampling_period",
        "sampling_popularity_band",
    }
    require(
        required <= set(sample.columns)
        and not any(c.startswith("lyrics_") for c in sample.columns),
        "Schema da amostra incompatível.",
    )
    require(
        sample.height == expected
        and sample["track_id"].n_unique() == expected
        and sample["track_id"].null_count() == 0,
        "Cardinalidade/IDs da amostra incompatíveis.",
    )
    p, w = sample["inclusion_probability"].to_numpy(), sample["sampling_weight"].to_numpy()
    require(
        bool(np.all(np.isfinite(w) & (w > 0)))
        and bool(np.all(np.isfinite(p) & (p > 0) & (p <= 1)))
        and np.allclose(w * p, 1, rtol=1e-12),
        "Pesos/probabilidades inválidos.",
    )
    require(
        np.allclose(p, sample["n_h"].to_numpy() / sample["N_h"].to_numpy(), rtol=1e-12)
        and (sample["certainty_selection"] == (sample["n_h"] == sample["N_h"])).all(),
        "Desenho por faixa inconsistente.",
    )
    allocation = pl.read_csv(allocation_path)
    require(
        allocation["stratum_id"].n_unique() == allocation.height, "Alocação com estratos repetidos."
    )
    actual = sample.group_by("stratum_id").len().sort("stratum_id")
    require(
        actual["stratum_id"].to_list() == allocation.sort("stratum_id")["stratum_id"].to_list()
        and actual["len"].to_list() == allocation.sort("stratum_id")["n_h"].to_list(),
        "Alocação realizada diverge.",
    )
    design = sample.select("stratum_id", "N_h", "n_h").join(
        allocation.select(
            "stratum_id", pl.col("N_h").alias("expected_N"), pl.col("n_h").alias("expected_n")
        ),
        on="stratum_id",
        how="left",
        validate="m:1",
    )
    require(
        ((design["N_h"] == design["expected_N"]) & (design["n_h"] == design["expected_n"])).all()
        and sample["seed"].unique().to_list() == [20261031],
        "Campos de desenho/seed divergem da alocação.",
    )
    require(
        math.isclose(math.fsum(w), summary["catalog_counts"]["rows"], rel_tol=1e-12, abs_tol=1e-6),
        "Soma de pesos diverge do catálogo.",
    )
    require(
        sample.filter(pl.col("popularity").cast(pl.Float64) >= 80).height
        == summary["catalog_counts"]["popularity_ge_80"],
        "Cauda ≥80 diverge.",
    )
    high = sample.filter(pl.col("popularity").cast(pl.Float64) >= 80)
    require(
        (high["sampling_weight"] == 1).all() and (high["inclusion_probability"] == 1).all(),
        "Alta popularidade não é integral.",
    )
    if expected == 200_000:
        require(high.height == 499, "Amostra difere das 499 faixas ≥80 declaradas no protocolo.")
    return sample, summary


def make_queries(sample):
    queries, tracks = {}, []
    # Projeção fechada: os campos do desenho e o alvo nunca chegam ao matcher.
    for row in sample.select("track_id", "artist_name", "track_name", "duration_ms").iter_rows(
        named=True
    ):
        query = query_for_metadata(row)
        key = fingerprint(query) if query else None
        if query:
            queries[key] = query
        tracks.append((row["track_id"], key))
    return queries, tracks


def inspect_old_index(dump, old_index, old_workspace):
    identity = local.checked_dump(dump)
    with closing(stable_readonly(old_index / "lookup.sqlite")) as index:
        seal, progress = meta_get(index, "seal"), meta_get(index, "progress")
        require(
            progress["complete"] and seal["dump"] == identity,
            "Índice antigo incompleto ou de outro dump; não reutilizar.",
        )
        require(
            seal["code"] == local.implementation_signature(),
            "Código do índice antigo mudou; revisar compatibilidade.",
        )
    with closing(stable_readonly(old_workspace / "state.sqlite")) as state:
        artists = local.artist_keys(state)
    require(
        fingerprint(artists) == seal["artists_sha256"],
        "Universo de artistas antigo difere do selo do índice.",
    )
    return identity, set(artists), {"seal": seal, "progress": progress}


def state_connection(workspace):
    db = sqlite3.connect(workspace / "state.sqlite")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    return db


def initialize(db, seal, queries, tracks):
    if not db.execute("SELECT 1 FROM sqlite_schema WHERE name='meta'").fetchone():
        require(
            not db.execute("SELECT 1 FROM sqlite_schema WHERE type='table'").fetchone(),
            "Estado desconhecido; não sobrescrever.",
        )
        db.executescript("BEGIN IMMEDIATE;\n" + STATE_SQL)
        with db:
            meta_put(db, "seal", seal)
            db.executemany(
                "INSERT INTO queries(query_id,data) VALUES (?,?)",
                [(k, json.dumps(v, ensure_ascii=False)) for k, v in sorted(queries.items())],
            )
            db.executemany("INSERT INTO tracks VALUES (?,?)", tracks)
    require(
        meta_get(db, "seal") == seal,
        "Estado pertence a outra amostra/fonte/regras/idioma; preservado, revisão necessária.",
    )
    require(
        db.execute("SELECT count(*) FROM tracks").fetchone()[0] == len(tracks)
        and db.execute("SELECT count(*) FROM queries").fetchone()[0] == len(queries),
        "Estado inicial incompleto.",
    )
    require(
        dict(db.execute("SELECT track_id,query_id FROM tracks")) == dict(tracks),
        "Mapa faixa–consulta alterado.",
    )
    for stored in db.execute("SELECT query_id,data FROM queries"):
        require(
            stored["query_id"] in queries
            and json.loads(stored["data"]) == queries[stored["query_id"]],
            "Consulta privada diverge da projeção de metadados da amostra.",
        )
    require(not db.execute("PRAGMA foreign_key_check").fetchone(), "Referência SQLite inválida.")


def collect(
    db,
    dump,
    old_index,
    supplemental,
    old_artists,
    workspace,
    source_identity,
    detector,
    *,
    limit=None,
    retry_errors=False,
):
    start = time.monotonic()
    reused = db.execute(
        "SELECT count(*) FROM queries WHERE status NOT IN ('pending','technical_error')"
    ).fetchone()[0]
    condition = (
        "status='pending' OR (status='technical_error' AND attempts<3)"
        if retry_errors
        else "status='pending'"
    )
    jobs = db.execute(
        f"SELECT query_id,data FROM queries WHERE {condition} ORDER BY query_id LIMIT ?",
        (limit if limit is not None else -1,),
    ).fetchall()
    run = {
        "started_at": utc_now(),
        "new_queries": 0,
        "new_tracks": 0,
        "reused_queries": reused,
        "reused_tracks": db.execute(
            "SELECT count(*) FROM tracks JOIN queries USING(query_id) WHERE status NOT IN ('pending','technical_error')"
        ).fetchone()[0],
        "errors_this_run": 0,
        "old_cache_imports": 0,
        "stop_reason": None,
    }
    last_print = 0.0
    try:
        for stored in jobs:
            key, query = stored["query_id"], json.loads(stored["data"])
            started = time.monotonic()
            with db:
                db.execute("UPDATE queries SET attempts=attempts+1 WHERE query_id=?", (key,))
            try:
                local.space(workspace)
                index = (
                    old_index
                    if conservative_normalize(query["artist_name_query"]) in old_artists
                    else supplemental
                )
                require(index is not None, "Artista não coberto por índice completo.")
                candidates, incomplete = local.LocalLookup(dump, index).candidates(query)
                result, lyric = classify(query, candidates, incomplete)
                if lyric:
                    if detector is not None:
                        try:
                            result.update(
                                detect_language(
                                    lyric["plain_text_source"], threshold=0.80, identifier=detector
                                )
                            )
                        except Exception:
                            result["language_status"] = "not_evaluated_detector_error"
                    lyric.update(
                        {
                            "query_id": key,
                            "source_dump": source_identity,
                            "rules_version": VERSION,
                            "query_method": result["method"],
                        }
                    )
                evidence = {
                    "query": query,
                    "source": source_identity,
                    "rules_version": VERSION,
                    "candidates": candidates,
                    "incomplete_reason": incomplete,
                    "queried_at": utc_now(),
                }
                with db:
                    db.execute(
                        "INSERT OR REPLACE INTO evidence VALUES (?,?)",
                        (key, json.dumps(evidence, ensure_ascii=False)),
                    )
                    if lyric:
                        db.execute(
                            "INSERT OR REPLACE INTO lyrics VALUES (?,?)",
                            (key, json.dumps(lyric, ensure_ascii=False)),
                        )
                    db.execute(
                        "UPDATE queries SET status=?,result=?,elapsed_seconds=? WHERE query_id=?",
                        (result["status"], json.dumps(result), time.monotonic() - started, key),
                    )
                run["new_queries"] += 1
                run["new_tracks"] += db.execute(
                    "SELECT count(*) FROM tracks WHERE query_id=?", (key,)
                ).fetchone()[0]
            except (sqlite3.Error, OSError, ValueError, TypeError, KeyError, TimeoutError) as exc:
                result = {
                    "status": "technical_error",
                    "reason": type(exc).__name__,
                    "rules_version": VERSION,
                    "candidate_present": None,
                    "text_present": None,
                    "plain_present": None,
                    "synced_present": None,
                }
                with db:
                    db.execute(
                        "UPDATE queries SET status='technical_error',result=?,elapsed_seconds=? WHERE query_id=?",
                        (json.dumps(result), time.monotonic() - started, key),
                    )
                run["errors_this_run"] += 1
                run["stop_reason"] = "technical_error_resume_with_retry_errors"
                break
            if time.monotonic() - last_print >= 10:
                print(json.dumps({"stage": "searching", **run}, ensure_ascii=False), flush=True)
                last_print = time.monotonic()
    except KeyboardInterrupt:
        run["stop_reason"] = "interrupted_resume_same_command"
    finally:
        run["elapsed_seconds"] = time.monotonic() - start
        with db:
            db.execute("INSERT INTO runs(data) VALUES (?)", (json.dumps(run),))
        atomic_json(workspace / "progress.json", run)
    return run


def export_private(db, sample, workspace):
    records = []
    for row in db.execute(
        "SELECT t.track_id,t.query_id,q.status,q.result FROM tracks t LEFT JOIN queries q USING(query_id) ORDER BY t.track_id"
    ):
        result = json.loads(row["result"]) if row["result"] else {}
        status = row["status"] if row["query_id"] else "insufficient_metadata"
        records.append(
            {
                "track_id": row["track_id"],
                "lyrics_query_id": row["query_id"],
                "lyrics_status": status,
                "lyrics_reason": result.get(
                    "reason", "missing_artist_or_title" if not row["query_id"] else "not_processed"
                ),
                **{
                    "lyrics_" + k: result.get(k)
                    for k in [
                        "candidate_count",
                        "candidate_present",
                        "text_present",
                        "plain_present",
                        "synced_present",
                        "eligible_count",
                        "equivalent_count",
                        "selected_lrclib_id",
                        "selected_lyrics_id",
                        "text_sha256",
                        "strict_text_sha256",
                        "detected_language",
                        "language_confidence",
                        "language_status",
                    ]
                },
                "lyrics_rules_version": VERSION,
                "lyrics_method": result.get("method", "no_query"),
                "lyrics_text_ref": row["query_id"] if status == "accepted" else None,
            }
        )
    results = pl.DataFrame(records, infer_schema_length=None)
    final = sample.join(results, on="track_id", how="left", validate="1:1")
    require(
        final.height == sample.height
        and final["track_id"].n_unique() == sample.height
        and final["lyrics_status"].is_in(STATUSES).all(),
        "Join 1:1/status inválido.",
    )
    require(
        final.sort("track_id").select(sample.columns).equals(sample.sort("track_id")),
        "Campos originais/desenho alterados.",
    )
    # Arrow streaming mantém só uma letra em memória; aceita também tabela vazia.
    import pyarrow as pa
    import pyarrow.parquet as pq

    schema = pa.schema(
        [
            ("query_id", pa.string()),
            ("plain_text_source", pa.string()),
            ("synced_text_source", pa.string()),
            ("lrclib_id", pa.int64()),
            ("lrclib_lyrics_id", pa.int64()),
            ("text_sha256", pa.string()),
            ("strict_text_sha256", pa.string()),
            ("provenance_json", pa.string()),
        ]
    )
    destination = workspace / "letras_aceitas_200k.parquet"
    accepted_keys = set()
    with pq.ParquetWriter(
        destination.with_suffix(".parquet.tmp"), schema, compression="zstd"
    ) as writer:
        batch = []
        for stored in db.execute("SELECT query_id,data FROM lyrics ORDER BY query_id"):
            lyric = json.loads(stored["data"])
            require(
                hashlib.sha256(lyric["plain_text_source"].encode()).hexdigest()
                == lyric["text_sha256"],
                "Hash de letra privada diverge.",
            )
            require(
                strict_plain_text_metrics(lyric["plain_text_source"])["strict_text_sha256"]
                == lyric["strict_text_sha256"],
                "Fingerprint privado diverge.",
            )
            accepted_keys.add(stored["query_id"])
            batch.append(
                {
                    **{name: lyric.get(name) for name in schema.names if name != "provenance_json"},
                    "provenance_json": json.dumps(
                        {
                            k: v
                            for k, v in lyric.items()
                            if k not in {"plain_text_source", "synced_text_source"}
                        },
                        ensure_ascii=False,
                    ),
                }
            )
            if len(batch) >= 256:
                writer.write_table(pa.Table.from_pylist(batch, schema=schema))
                batch = []
        if batch:
            writer.write_table(pa.Table.from_pylist(batch, schema=schema))
    require(
        accepted_keys
        == set(final.filter(pl.col("lyrics_status") == "accepted")["lyrics_text_ref"].to_list()),
        "Referências de letras inconsistentes.",
    )
    for key, result in db.execute("SELECT query_id,result FROM queries WHERE status='accepted'"):
        result = json.loads(result)
        stored = json.loads(
            db.execute("SELECT data FROM lyrics WHERE query_id=?", (key,)).fetchone()[0]
        )
        require(
            result["text_sha256"] == stored["text_sha256"]
            and result["selected_lrclib_id"] == stored["lrclib_id"],
            "Vínculo aceito/texto diverge.",
        )
    destination.with_suffix(".parquet.tmp").replace(destination)
    atomic_frame(workspace / "resultados_faixas_200k.parquet", final)
    return final, len(accepted_keys)


def coverage_tables(final):
    frame = final.with_columns(
        text_column("track_id").alias("_s_id"),
        text_column("artist_name").alias("_s_artist"),
        text_column("track_name").alias("_s_title"),
        text_column("genre").alias("_s_genre"),
        pl.col("popularity").cast(pl.Float64).alias("_s_pop"),
        pl.col("year").cast(pl.Float64).alias("_s_year"),
        pl.col("sampling_period").alias("_s_period"),
        pl.col("sampling_popularity_band").alias("_s_band"),
    ).with_columns(
        pl.when(pl.col("_s_pop") >= 90)
        .then(pl.lit("90–100"))
        .when(pl.col("_s_pop") >= 80)
        .then(pl.lit("80–89"))
        .otherwise(pl.col("_s_band"))
        .alias("_s_coverage_band")
    )
    import yaml

    rules = yaml.safe_load((ROOT / "configs/quality_rules.yaml").read_text(encoding="utf-8"))[
        "spotify"
    ]
    groups = {
        "complete": frame,
        "accepted": frame.filter(pl.col("lyrics_status") == "accepted"),
        "not_accepted": frame.filter(pl.col("lyrics_status") != "accepted"),
    }
    groups.update(
        {s: frame.filter(pl.col("lyrics_status") == s) for s in STATUSES if s not in {"accepted"}}
    )
    domains = {
        "_s_pop": list(range(101)),
        "_s_band": sorted(frame["_s_coverage_band"].unique().to_list()),
        "_s_genre": sorted(frame["_s_genre"].drop_nulls().unique().to_list()),
        "_s_year": sorted(frame["_s_year"].unique().to_list()),
        "_s_period": sorted(frame["_s_period"].unique().to_list()),
    }
    comp = Comparison()
    # Comparações completas reutilizam o motor amostral; só entram campos analíticos.
    for group, subset in groups.items():
        if subset.is_empty():
            continue
        for weighted in (False, True):
            weights = subset["sampling_weight"].to_numpy() if weighted else np.ones(subset.height)
            scope = f"{group}|{'weighted' if weighted else 'unweighted'}"
            comp.describe(
                subset,
                subset.with_columns(pl.col("_s_coverage_band").alias("_s_band")),
                weights,
                scope,
                rules,
                domains,
            )
    for weighted in (False, True):
        scope = "weighted" if weighted else "unweighted"
        for field in [None, "_s_coverage_band", "_s_genre", "_s_year", "_s_period"]:
            partitions = (
                [("all", frame)]
                if field is None
                else [
                    (str(key[0]), sub)
                    for key, sub in frame.partition_by(field, as_dict=True).items()
                ]
            )
            for category, subset in partitions:
                w = subset["sampling_weight"].to_numpy() if weighted else np.ones(subset.height)
                for status in STATUSES:
                    mask = (subset["lyrics_status"] == status).to_numpy()
                    comp.emit(
                        scope,
                        "coverage_status",
                        field or "all",
                        category,
                        {
                            status + "_n": int(mask.sum()),
                            status + "_total": float(w[mask].sum()),
                            status + "_rate": float(w[mask].sum() / w.sum()),
                        },
                        float(w.sum()),
                    )
                for flag in [
                    "candidate_present",
                    "text_present",
                    "plain_present",
                    "synced_present",
                ]:
                    known = subset["lyrics_" + flag].is_not_null().to_numpy()
                    positive = subset["lyrics_" + flag].fill_null(False).cast(pl.Boolean).to_numpy()
                    comp.emit(
                        scope,
                        "coverage_evidence",
                        field or "all",
                        category,
                        {
                            flag + "_positive_n": int(positive.sum()),
                            flag + "_unknown_n": int((~known).sum()),
                            flag + "_positive_total": float(w[positive].sum()),
                            flag + "_known_denominator": float(w[known].sum()),
                            flag + "_rate_known": float(w[positive].sum() / w[known].sum())
                            if known.any()
                            else None,
                        },
                        float(w.sum()),
                    )
        a, b = groups["accepted"], groups["not_accepted"]
        if a.height and b.height:
            for variable in ["popularity", *ACOUSTIC]:
                stats = []
                for sub in (a, b):
                    w = sub["sampling_weight"].to_numpy() if weighted else np.ones(sub.height)
                    stats.append(weighted_summary(numeric_values(sub, variable)[0], w))
                left, right = stats
                if left["mean"] is None or right["mean"] is None:
                    continue
                pooled = math.sqrt((left["std_population"] ** 2 + right["std_population"] ** 2) / 2)
                comp.emit(
                    scope,
                    "accepted_minus_not_accepted",
                    variable,
                    "all_finite",
                    {
                        "mean_difference": left["mean"] - right["mean"],
                        "standardized_mean_difference": (left["mean"] - right["mean"]) / pooled
                        if pooled
                        else None,
                        "accepted_valid_weight": left["weight_observed"],
                        "not_accepted_valid_weight": right["weight_observed"],
                    },
                )
            for variable in ["_s_coverage_band", "_s_genre", "_s_year", "_s_period"]:
                for category in frame[variable].drop_nulls().unique().sort().to_list():
                    rates = []
                    for sub in (a, b):
                        w = sub["sampling_weight"].to_numpy() if weighted else np.ones(sub.height)
                        rates.append(
                            float(w[(sub[variable] == category).to_numpy()].sum() / w.sum())
                        )
                    comp.emit(
                        scope,
                        "accepted_minus_not_accepted",
                        variable,
                        category,
                        {"proportion_difference": rates[0] - rates[1]},
                    )
    # Idioma só agregado; nenhum texto/token/fingerprint aparece nas tabelas públicas.
    accepted = groups["accepted"]
    if accepted.height:
        for names, sub in accepted.partition_by(
            ["lyrics_detected_language", "lyrics_language_status"], as_dict=True
        ).items():
            comp.emit(
                "accepted",
                "estimated_language",
                str(names[0]),
                str(names[1]),
                {"n": sub.height, "weighted_total": float(sub["sampling_weight"].sum())},
                accepted.height,
            )
    return comp.rows


def public_plots(rows, output):
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    files = []
    for variable, slug in [
        ("_s_coverage_band", "popularidade"),
        ("_s_genre", "genero"),
        ("_s_period", "periodo"),
    ]:
        items = [
            r
            for r in rows
            if r["scope"] == "unweighted"
            and r["section"] == "coverage_status"
            and r["variable"] == variable
            and r["metric"] == "accepted_n"
        ]
        if variable == "_s_genre":
            items.sort(key=lambda r: (-r["denominator"], r["category"]))
            items = items[:20]
        else:
            items.sort(key=lambda r: r["category"])
        lookup = {
            (r["scope"], r["category"]): r["value"]
            for r in rows
            if r["section"] == "coverage_status"
            and r["variable"] == variable
            and r["metric"] == "accepted_rate"
        }
        fig, ax = plt.subplots(figsize=(13, 7), layout="constrained")
        x = np.arange(len(items))
        for i, scope in enumerate(("unweighted", "weighted")):
            ax.bar(
                x + (i - 0.5) * 0.35,
                [100 * lookup[(scope, r["category"])] for r in items],
                width=0.35,
                label=scope,
            )
        ax.set_xticks(
            x,
            [f"{r['category']}\n{int(r['value'])}/{int(r['denominator'])}" for r in items],
            rotation=60 if slug == "genero" else 0,
            ha="right" if slug == "genero" else "center",
        )
        ax.set_ylim(0, 115)
        ax.set_ylabel("Letras aceitas / todas as faixas (%)")
        ax.set_title(
            f"Cobertura por {slug}; rótulos: aceitas/total observado"
            + (" (20 gêneros mais frequentes)" if slug == "genero" else "")
        )
        ax.legend()
        name = f"cobertura_{slug}_200k.png"
        fig.savefig(output / name, dpi=150)
        plt.close(fig)
        files.append(name)
    return files


def publish(db, final, output, summary):
    rows = coverage_tables(final)
    path = output / "comparacao_cobertura_letras_200k.csv"
    temporary = path.with_suffix(".csv.tmp")
    import csv

    with temporary.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)
    summary["plots"] = public_plots(rows, output)
    summary["status_counts"] = dict(final.group_by("lyrics_status").len().iter_rows())
    summary["runs"] = [
        json.loads(row[0]) for row in db.execute("SELECT data FROM runs ORDER BY id")
    ]
    summary["execution_seconds_cumulative"] = sum(row["elapsed_seconds"] for row in summary["runs"])
    summary["queries_total"] = db.execute("SELECT count(*) FROM queries").fetchone()[0]
    summary["queries_ever_attempted"] = db.execute(
        "SELECT count(*) FROM queries WHERE attempts>0"
    ).fetchone()[0]
    summary["tracks_ever_attempted"] = db.execute(
        "SELECT count(*) FROM tracks t JOIN queries q USING(query_id) WHERE q.attempts>0"
    ).fetchone()[0]
    summary["completed"] = not summary["status_counts"].get("pending", 0) and not summary[
        "status_counts"
    ].get("technical_error", 0)
    summary["status"] = "completed" if summary["completed"] else "incomplete"
    summary["updated_at"] = utc_now()
    sections = [
        "# Busca LRCLIB local da amostra Spotify",
        f"Status: **{summary['status']}**. {final.height:,} faixas preservadas; resultados automáticos aceitos pelo protocolo, sem validação humana individual.",
        f"Consultas distintas: {summary['queries_total']:,}; já tentadas: {summary['queries_ever_attempted']:,}; faixas correspondentes já tentadas: {summary['tracks_ever_attempted']:,}.",
        "## Status e denominadores",
        markdown_table(
            [r for r in rows if r["section"] == "coverage_status" and r["variable"] == "all"],
            ["scope", "metric", "value", "denominator"],
        ),
        "## Candidato, texto e aceite são eventos distintos",
        markdown_table(
            [r for r in rows if r["section"] == "coverage_evidence" and r["variable"] == "all"],
            ["scope", "metric", "value", "denominator"],
        ),
        "Valores desconhecidos em erros/pendências não são convertidos em ausência. Taxa de aceite usa todas as faixas; disponibilidade de candidato/texto usa também denominador conhecido explicitado no CSV.",
        "## Alta popularidade: inclusão integral original",
        markdown_table(
            [
                r
                for r in rows
                if r["section"] == "coverage_status"
                and r["variable"] == "_s_coverage_band"
                and r["category"] in ("80–89", "90–100")
                and r["metric"].endswith(("_n", "_rate"))
            ],
            ["scope", "category", "metric", "value", "denominator"],
        ),
        "## Diferenças descritivas: aceitas menos não aceitas",
        markdown_table(
            [
                r
                for r in rows
                if r["section"] == "accepted_minus_not_accepted"
                and r["metric"] in ("mean_difference", "standardized_mean_difference")
            ],
            ["scope", "variable", "metric", "value"],
        ),
        "CSV contém médias, mediana/P50 e quantis, 13 atributos (incluindo duração), ausências/domínios, gênero/ano/período, créditos e concentração em amostra completa, aceitas, não aceitas e cada status, sem/com pesos. Contagens distintas de créditos são observadas, não estimativas por soma de pesos.",
        "## Execuções e retomadas",
        markdown_table(
            summary["runs"],
            [
                "started_at",
                "new_queries",
                "new_tracks",
                "reused_queries",
                "reused_tracks",
                "errors_this_run",
                "elapsed_seconds",
                "stop_reason",
            ],
        ),
        f"Tempo acumulado de consultas: {summary['execution_seconds_cumulative']:.2f} segundos; não inclui indexação nem geração dos relatórios. Reutilização refere-se a consultas concluídas deste workspace; importações de caches antigos: zero.",
        "## Limitações",
        "Taxa ponderada estima cobertura no catálogo sob este protocolo e snapshot. Pesos originais não corrigem automaticamente seleção por disponibilidade/aceitação de letras. Sem letra não implica instrumental. Nenhuma substituição, recalibração, filtro de idioma/gênero, split ou modelo foi aplicado. O teste V0.6 já aberto continua exposto.",
        "Diferenças de proporções e médias padronizadas são descritivas; sem p-valores como selo de representatividade. Resultados incompletos misturam pendências operacionais à não aceitação e devem ser interpretados como provisórios. Idioma estimado por langid quando disponível; score não é probabilidade calibrada e não decide aceite.",
        "## Gráficos",
        *[f"![{name}]({name})" for name in summary["plots"]],
    ]
    (output / "relatorio_busca_local_200k.md").write_text(
        "\n\n".join(sections) + "\n", encoding="utf-8"
    )
    (output / "protocolo_busca_local_200k.md").write_text(
        PROTOCOL.read_text(encoding="utf-8"), encoding="utf-8"
    )
    atomic_json(output / "resumo_busca_local_200k.json", summary)


def execute(
    sample_path=SAMPLE_DIR / "amostra_spotify_200k.parquet",
    summary_path=SAMPLE_DIR / "resumo_amostra_200k.json",
    allocation_path=SAMPLE_DIR / "alocacao_amostra_200k.csv",
    dump=local.DEFAULT_DESTINATION / "lrclib-db-dump-20261012T090639Z.sqlite3",
    old_index=local.DEFAULT_INDEX,
    old_workspace=local.DEFAULT_LOCAL,
    index_dir=INDEX,
    workspace=WORKSPACE,
    output=OUTPUT,
    *,
    limit=None,
    retry_errors=False,
    report_only=False,
    expected=200_000,
):
    invocation_start = time.monotonic()
    args = [
        sample_path,
        summary_path,
        allocation_path,
        dump,
        old_index,
        old_workspace,
        index_dir,
        workspace,
        output,
    ]
    (
        sample_path,
        summary_path,
        allocation_path,
        dump,
        old_index,
        old_workspace,
        index_dir,
        workspace,
        output,
    ) = [Path(p).resolve() for p in args]
    require(
        workspace.is_relative_to(ROOT / "data/derived") or expected != 200_000,
        "Workspace privado deve ficar sob data/derived, ignorado pelo Git.",
    )
    require(
        len(
            {
                old_workspace,
                old_index,
                index_dir,
                workspace,
                output,
                sample_path.parent,
                dump.parent,
            }
        )
        == 7,
        "Use diretórios separados para preservar entradas/execuções anteriores.",
    )
    print("[1/6] Validando amostra, pesos e proveniência...", flush=True)
    sample, sample_summary = validate_sample(
        sample_path, summary_path, allocation_path, expected=expected
    )
    queries, tracks = make_queries(sample)
    identity, old_artists, old_info = inspect_old_index(dump, old_index, old_workspace)
    artists = sorted({conservative_normalize(q["artist_name_query"]) for q in queries.values()})
    missing = sorted(set(artists) - old_artists)
    detector, language = language_detector()
    code_files = [
        Path(__file__),
        PROTOCOL,
        *[
            ROOT / f"src/tcc_music_popularity/{name}.py"
            for name in (
                "local_lyrics",
                "normalization",
                "lyrics_pilot",
                "lyrics_ambiguity_v011",
                "lyrics_embeddings_v020",
                "catalog_sampling",
                "catalog_audit",
                "manual_lyrics",
            )
        ],
    ]
    seal = {
        "version": VERSION,
        "sample_sha256": sha256(sample_path),
        "sample_summary_sha256": sha256(summary_path),
        "allocation_sha256": sha256(allocation_path),
        "source": identity,
        "old_index_seal": old_info["seal"],
        "old_artists_sha256": fingerprint(sorted(old_artists)),
        "additional_artists_sha256": fingerprint(missing),
        "code": {p.name: sha256(p) for p in code_files},
        "language": language,
        "duration_tolerance": TOLERANCE,
        "output": str(output),
        "index_dir": str(index_dir),
    }
    owner = {"version": VERSION, "workspace": str(workspace), "seal_sha256": fingerprint(seal)}
    if output.exists():
        require(
            (output / "owner.json").is_file()
            and json.loads((output / "owner.json").read_text()) == owner,
            "Pasta pública existente incompatível; não sobrescrever.",
        )
    else:
        output.mkdir(parents=True)
        atomic_json(output / "owner.json", owner)
    with exclusive(workspace), closing(state_connection(workspace)) as db:
        initialize(db, seal, queries, tracks)
        summary = {
            "status": "incomplete",
            "completed": False,
            "sample_rows": sample.height,
            "sample_sha256": seal["sample_sha256"],
            "sample_summary_sha256": seal["sample_summary_sha256"],
            "source": identity,
            "rules_version": VERSION,
            "code_hashes": seal["code"],
            "language": language,
            "index": {
                "previous_scanned": old_info["progress"]["scanned"],
                "previous_indexed": old_info["progress"]["indexed"],
                "filter": "normalized artists in prior manifest; no language/text filter",
                "sample_artists": len(artists),
                "additional_artists": len(missing),
            },
            "http_requests": 0,
            "old_cache_imports": 0,
            "command_argv": [sys.executable, *sys.argv],
            "last_invocation_started_at": utc_now(),
            "versions": {
                "python": sys.version,
                "numpy": np.__version__,
                "polars": pl.__version__,
                "sqlite": sqlite3.sqlite_version,
            },
            "expected_high_popularity_tracks": sample_summary["catalog_counts"]["popularity_ge_80"],
        }
        atomic_json(output / "resumo_busca_local_200k.json", summary)
        try:
            if not report_only:
                print(
                    f"[2/6] Índice antigo reutilizado; {len(missing)} artistas adicionais para índice separado...",
                    flush=True,
                )
                if missing:
                    index_dir.mkdir(parents=True, exist_ok=True)
                    index_started = time.monotonic()
                    progress = local.build_index(
                        dump, index_dir, local.index_seal(identity, missing), missing
                    )
                    summary["index"]["supplemental_progress"] = progress
                    summary["index"]["elapsed_seconds_this_invocation"] = (
                        time.monotonic() - index_started
                    )
                print(
                    "[3/6] Consultando pendências locais com checkpoints por consulta...",
                    flush=True,
                )
                with ExitStack() as stack:
                    source = stack.enter_context(closing(local.readonly(dump)))
                    previous = stack.enter_context(
                        closing(stable_readonly(old_index / "lookup.sqlite"))
                    )
                    extra = (
                        stack.enter_context(closing(stable_readonly(index_dir / "lookup.sqlite")))
                        if missing
                        else None
                    )
                    collect(
                        db,
                        source,
                        previous,
                        extra,
                        old_artists,
                        workspace,
                        identity,
                        detector,
                        limit=limit,
                        retry_errors=retry_errors,
                    )
            print("[4/6] Validando referências e exportando Parquets privados 1:1...", flush=True)
            final, texts = export_private(db, sample, workspace)
            summary["checks"] = {
                "sample_hash_unchanged": sha256(sample_path) == seal["sample_sha256"],
                "one_row_per_track": final.height == sample.height,
                "original_fields_weights_preserved": True,
                "text_references_hashes_valid": True,
            }
            require(all(summary["checks"].values()), "Integridade final falhou.")
            summary["private_text_rows"] = texts
            print("[5/6] Comparando cobertura com denominadores e pesos originais...", flush=True)
            publish(db, final, output, summary)
            summary["invocation_elapsed_seconds_including_reports"] = (
                time.monotonic() - invocation_start
            )
            atomic_json(output / "resumo_busca_local_200k.json", summary)
            with (output / "relatorio_busca_local_200k.md").open("a", encoding="utf-8") as report:
                report.write(
                    f"\nTempo total desta invocação, incluindo preparação/indexação quando necessária e relatórios: {summary['invocation_elapsed_seconds_including_reports']:.2f} segundos.\n"
                )
            print(
                f"[6/6] {summary['status']}; agregados em {output}; letras somente no workspace privado.",
                flush=True,
            )
            return 0 if summary["completed"] else 2
        except BaseException as exc:
            summary.update(
                status="incomplete",
                completed=False,
                error_type=type(exc).__name__,
                error="Execução interrompida; checkpoints privados preservados. Não interpretar como ausência de letra.",
            )
            atomic_json(output / "resumo_busca_local_200k.json", summary)
            raise


def cli(argv=None):
    parser = argparse.ArgumentParser(
        description="Busca LRCLIB offline da amostra 200k; índice suplementar e retomada automáticos."
    )
    parser.add_argument("--sample", type=Path, default=SAMPLE_DIR / "amostra_spotify_200k.parquet")
    parser.add_argument(
        "--sample-summary", type=Path, default=SAMPLE_DIR / "resumo_amostra_200k.json"
    )
    parser.add_argument("--allocation", type=Path, default=SAMPLE_DIR / "alocacao_amostra_200k.csv")
    parser.add_argument(
        "--dump",
        type=Path,
        default=local.DEFAULT_DESTINATION / "lrclib-db-dump-20261012T090639Z.sqlite3",
    )
    parser.add_argument("--old-index", type=Path, default=local.DEFAULT_INDEX)
    parser.add_argument("--old-workspace", type=Path, default=local.DEFAULT_LOCAL)
    parser.add_argument("--index-dir", type=Path, default=INDEX)
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--all", action="store_true")
    actions.add_argument("--limit", type=int)
    actions.add_argument("--report-only", action="store_true")
    actions.add_argument("--status", action="store_true")
    parser.add_argument("--retry-errors", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.status:
            path = args.output / "resumo_busca_local_200k.json"
            print(path.read_text(encoding="utf-8") if path.exists() else "Ainda não inicializado.")
            return 0
        require(args.limit is None or args.limit > 0, "--limit deve ser positivo.")
        return execute(
            args.sample,
            args.sample_summary,
            args.allocation,
            args.dump,
            args.old_index,
            args.old_workspace,
            args.index_dir,
            args.workspace,
            args.output,
            limit=args.limit,
            retry_errors=args.retry_errors,
            report_only=args.report_only,
        )
    except KeyboardInterrupt:
        print("Interrompido. Retome com o mesmo comando; não apague checkpoints.", file=sys.stderr)
        return 2
    except Exception as exc:
        print(
            f"Falha ({type(exc).__name__}): "
            + (
                str(exc)
                if isinstance(exc, ValueError)
                else "confira SSD, caminhos e espaço; arquivos preservados"
            ),
            file=sys.stderr,
        )
        return 1
