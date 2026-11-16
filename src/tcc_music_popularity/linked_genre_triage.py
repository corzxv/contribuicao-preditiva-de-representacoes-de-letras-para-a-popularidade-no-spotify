"""Mede a capacidade dos índices existentes nos gêneros com cota insuficiente."""

import argparse
import json
from collections import Counter
from contextlib import closing

import polars as pl

from . import lyrics_historical_revalidation as historical
from .manual_lyrics import atomic_frame, atomic_json, exclusive, fingerprint, meta_get, require
from .sample_lyrics import stable_readonly

sample = historical.sample
design = sample.design
limit = sample.links.limit
local = limit.local
recovery = limit.recovery
WORKSPACE = design.ROOT / "data/derived/private_triagem_generos_deficitarios_v1"
OUTPUT = design.ROOT / "reports/triagem_generos_deficitarios_v1"


def prepare():
    report = design.read_json(historical.OUTPUT / "resumo_revalidacao.json")
    require(report["completed"], "Revalidação histórica ainda incompleta.")
    deficit = {r["genre"]: r for r in report["remaining_genre_deficits"]}
    require(bool(deficit), "Quadro sem gêneros deficitários.")
    original, frame, _, origins = sample.input_frame()
    extended = pl.read_parquet(
        sample.links.verified(
            historical.WORKSPACE / "vinculos_revalidados.parquet",
            report["private_sha256"]["vinculos_revalidados.parquet"],
        )
    )
    require(
        origins["original_lyrics_manifest_sha256"]
        == report["source_hashes"]["original_lyrics_manifest_sha256"]
        and frame.height + extended.height == report["capacity_after"],
        "A revalidação se refere a outro quadro.",
    )
    stage = design.read_json(limit.OUTPUT / "resumo_revisao_limites.json")
    primary = stage["seal"]["primary"]["seal"]
    supplement = stage["seal"]["supplement"]["seal"]
    with closing(stable_readonly(recovery.WORKSPACE / "state.sqlite")) as db:
        primary_artists = set(meta_get(db, "lookup_artists"))
    with closing(stable_readonly(local.WORKSPACE / "state.sqlite")) as db:
        extra_artists = set(meta_get(db, "extra_artists"))
    require(
        fingerprint(sorted(primary_artists)) == primary["artists"]
        and fingerprint(sorted(extra_artists)) == supplement["artists"],
        "Listas de artistas divergentes dos índices selados.",
    )
    catalog = design.read_json(design.DESCRIPTION / "resumo_descritiva.json")
    sample.links.verified(design.SOURCE, catalog["fontes"]["csv_sha256"])
    columns = [*sample.COLUMNS, "artist_name", "track_name"]
    population = (
        pl.scan_csv(design.SOURCE, infer_schema=False)
        .filter(pl.col("genre").is_in(list(deficit)))
        .select(columns)
        .collect()
    )
    require(population.height == population["track_id"].n_unique(), "IDs duplicados no catálogo.")
    known = pl.concat([frame.select("track_id"), extended.select("track_id")])
    readiness = design.read_json(
        design.ROOT / "reports/prontidao_dados_200k_v1/resumo_prontidao.json"
    )
    historical_draw = (
        design.ROOT / "reports/amostra_spotify_200k_20261031/amostra_spotify_200k.parquet"
    )
    tested = pl.read_parquet(
        sample.links.verified(historical_draw, readiness["inputs"]["inputs"][str(historical_draw)]),
        columns=["track_id"],
    )
    prior_ids = set(tested["track_id"]) | set(original["track_id"])
    rows = population.join(known, on="track_id", how="anti").sort("track_id")
    counts = Counter()
    planned = []
    for row in rows.iter_rows(named=True):
        if row["track_id"] in prior_ids:
            counts[row["genre"], "already_drawn"] += 1
            continue
        query = recovery.recovery_query(
            {k: row[k] for k in ("track_id", "artist_name", "track_name", "duration_ms")}
        )
        category = "consulta_inviavel"
        if query is not None:
            profile = recovery.profile(query["artist_name_query"], query["track_name_query"])
            if (
                profile["artist"]
                and profile["title"]
                and not profile["credit_conflict"]
                and query["duration_seconds"] is not None
            ):
                name = profile["artist"]
                category = (
                    "principal"
                    if name in primary_artists
                    else "complementar"
                    if name in extra_artists
                    else "fora_dos_indices"
                )
        counts[row["genre"], category] += 1
        if category in {"principal", "complementar"}:
            planned.append(
                {
                    **row,
                    "query_id": fingerprint(query),
                    "query_json": json.dumps(query, ensure_ascii=False),
                    "index_kind": category,
                }
            )
    return planned, counts, deficit, population, stage["seal"], catalog["fontes"]["csv_sha256"]


def run():
    planned, counts, deficit, population, seal, catalog_hash = prepare()
    with exclusive(WORKSPACE):
        path = WORKSPACE / "consultas_indexadas.parquet"
        schema = {
            **population.schema,
            "query_id": pl.String,
            "query_json": pl.String,
            "index_kind": pl.String,
        }
        atomic_frame(path, pl.DataFrame(planned, schema=schema))
        results = []
        for genre, row in sorted(deficit.items()):
            results.append(
                {
                    "genre": genre,
                    "target": row["target"],
                    "verified_before": row["capacity_after"],
                    "deficit": row["deficit_after"],
                    "catalog_tracks": population.filter(pl.col("genre") == genre).height,
                    **{
                        kind: counts[genre, kind]
                        for kind in (
                            "principal",
                            "complementar",
                            "fora_dos_indices",
                            "consulta_inviavel",
                            "already_drawn",
                        )
                    },
                }
            )
        report = {
            "completed": True,
            "pending_lookup_tracks": len(planned),
            "pending_lookup_queries": len({r["query_id"] for r in planned}),
            "by_genre": results,
            "catalog_sha256": catalog_hash,
            "private_sha256": design.sha256(path),
            "index_seals": {key: seal[key] for key in ("dump", "primary", "supplement")},
        }
        atomic_json(OUTPUT / "resumo_triagem.json", report)
    print(
        json.dumps(
            {
                key: report[key]
                for key in ("pending_lookup_tracks", "pending_lookup_queries", "by_genre")
            },
            ensure_ascii=False,
        )
    )
    return report


def cli(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    run()
    return 0
