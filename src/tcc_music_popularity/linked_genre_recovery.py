"""Busca letras nos gêneros deficitários pelos índices locais existentes."""

import argparse
import json
import sqlite3
from collections import Counter
from contextlib import closing
from pathlib import Path

import polars as pl

from . import linked_genre_triage as triage
from .manual_lyrics import (
    atomic_frame,
    atomic_json,
    exclusive,
    fingerprint,
    meta_get,
    meta_put,
    require,
)
from .sample_lyrics import stable_readonly

design, local, limit = triage.design, triage.local, triage.limit
WORKSPACE = design.ROOT / "data/derived/private_recuperacao_generos_deficitarios_v1"
OUTPUT = design.ROOT / "reports/recuperacao_generos_deficitarios_v1"
RULES = "generos-deficitarios-v1"


def process(db, tracks, dump, indices, seal, max_queries, *, lookup=limit.lookup):
    jobs = tracks.select("query_id", "query_json", "index_kind").unique().sort("query_id")
    require(jobs.height == jobs["query_id"].n_unique(), "Consulta com metadados divergentes.")
    db.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    db.execute(
        "CREATE TABLE IF NOT EXISTS decisions (query_id TEXT PRIMARY KEY, outcome TEXT NOT NULL, lyric TEXT)"
    )
    stored = {row[0] for row in db.execute("SELECT query_id FROM decisions")}
    if meta_get(db, "seal") is None:
        require(not stored, "Checkpoint sem selo de origem.")
        with db:
            meta_put(db, "seal", seal)
    require(
        meta_get(db, "seal") == seal and stored <= set(jobs["query_id"]),
        "Checkpoint de outra origem.",
    )
    selected = jobs.filter(~pl.col("query_id").is_in(sorted(stored)))
    if max_queries is not None:
        selected = selected.head(max_queries)
    print(f"{jobs.height} consultas no plano, {len(stored)} já verificadas.", flush=True)
    for done, (key, raw, kind) in enumerate(selected.iter_rows(), start=len(stored) + 1):
        query = json.loads(raw)
        require(fingerprint(query) == key, "Chave da consulta divergente.")
        result, lyric = lookup(dump, indices[kind], query)
        if lyric:
            lyric["rules_version"] = RULES
        with db:
            db.execute(
                "INSERT INTO decisions VALUES (?,?,?)",
                (key, result["outcome"], json.dumps(lyric, ensure_ascii=False) if lyric else None),
            )
        if done % 250 == 0 or done == jobs.height:
            print(f"{done}/{jobs.height} consultas verificadas.", flush=True)
    return jobs.height


def publish(db, tracks, targets, before, seal):
    decisions = db.execute(
        "SELECT query_id,outcome,lyric FROM decisions ORDER BY query_id"
    ).fetchall()
    outcomes = Counter(row[1] for row in decisions)
    lyrics = [{"query_id": key, **json.loads(raw)} for key, _, raw in decisions if raw]
    texts = pl.DataFrame(lyrics, schema=limit.artist.synced.LYRIC_SCHEMA)
    extra = tracks.drop("query_json", "index_kind").join(
        texts.select("query_id", "text_sha256"), on="query_id", how="inner", validate="m:1"
    )
    require(
        texts.height == outcomes["accepted_after_metadata_filter"], "Aceites e letras divergentes."
    )
    additions = Counter(extra["genre"])
    by_genre = [
        {
            "genre": row["genre"],
            "target": row["target"],
            "verified_before": row["verified_before"],
            "new_links": additions[row["genre"]],
            "verified_after": row["verified_before"] + additions[row["genre"]],
            "deficit_after": max(0, row["deficit"] - additions[row["genre"]]),
        }
        for row in before
    ]
    atomic_frame(WORKSPACE / "letras_aceitas.parquet", texts)
    atomic_frame(WORKSPACE / "vinculos_aceitos.parquet", extra)
    report = {
        "completed": len(decisions) == targets,
        "queries_reviewed": len(decisions),
        "queries_planned": targets,
        "new_tracks_with_lyrics": extra.height,
        "outcomes_by_query": dict(outcomes),
        "by_genre": by_genre,
        "seal": seal,
        "private_sha256": {
            name: design.sha256(WORKSPACE / name)
            for name in ("letras_aceitas.parquet", "vinculos_aceitos.parquet")
        },
    }
    atomic_json(OUTPUT / "resumo_recuperacao.json", report)
    print(
        json.dumps(
            {
                key: report[key]
                for key in ("completed", "queries_reviewed", "new_tracks_with_lyrics", "by_genre")
            }
        ),
        flush=True,
    )
    return report


def run(max_queries=None):
    triage_path = triage.OUTPUT / "resumo_triagem.json"
    report = design.read_json(triage_path)
    require(report["completed"], "Triagem ainda incompleta.")
    tracks = pl.read_parquet(
        triage.sample.links.verified(
            triage.WORKSPACE / "consultas_indexadas.parquet", report["private_sha256"]
        )
    )
    require(
        tracks.height == tracks["track_id"].n_unique() == report["pending_lookup_tracks"],
        "Faixas divergentes da triagem.",
    )
    dump = local.DUMP
    primary = local.PRIMARY
    supplement = local.SUPPLEMENT / "lookup.sqlite"
    require(dump.is_file(), "Conecte o SSD em D: com o dump selado do LRCLIB.")
    identity, _, primary_info = local.primary_metadata(
        dump, primary, limit.recovery.WORKSPACE / "state.sqlite"
    )
    index_seals = report["index_seals"]
    require(
        identity == index_seals["dump"] and primary_info == index_seals["primary"],
        "Dump ou índice principal divergente da triagem.",
    )
    seal = {
        "triage_sha256": design.sha256(triage_path),
        "code_sha256": design.sha256(Path(__file__)),
        "lookup_code_sha256": design.sha256(Path(limit.__file__)),
    }
    with (
        exclusive(WORKSPACE),
        closing(stable_readonly(dump)) as db_dump,
        closing(stable_readonly(primary)) as db_primary,
        closing(stable_readonly(supplement)) as db_extra,
        closing(sqlite3.connect(WORKSPACE / "state.sqlite")) as db,
    ):
        require(
            local.cache.stamp(supplement) == index_seals["supplement"]["stamp"]
            and meta_get(db_extra, "seal") == index_seals["supplement"]["seal"]
            and meta_get(db_extra, "progress")["complete"],
            "Índice complementar divergente da triagem.",
        )
        targets = process(
            db,
            tracks,
            db_dump,
            {"principal": db_primary, "complementar": db_extra},
            seal,
            max_queries,
        )
        return publish(db, tracks, targets, report["by_genre"], seal)


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-queries", type=int, help="Limita o número de novas consultas desta execução."
    )
    args = parser.parse_args(argv)
    if args.max_queries is not None and args.max_queries <= 0:
        parser.error("--max-queries precisa ser positivo")
    try:
        run(args.max_queries)
    except KeyboardInterrupt:
        print("Progresso salvo. Repita o comando para retomar.", flush=True)
        return 2
    return 0
