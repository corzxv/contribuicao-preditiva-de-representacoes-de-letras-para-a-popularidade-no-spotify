"""Piloto de revisão de vínculos a partir de caches locais, sem consultar LRCLIB."""

import argparse
import hashlib
import json
import sqlite3
from contextlib import ExitStack, closing
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow.parquet as pq

from . import popularity_levels as levels

ROOT = levels.ROOT
SOURCE = ROOT / "data/derived/private_sample_lyrics_200k_v2/resultados_faixas_200k.parquet"
CACHES = (
    ROOT / "data/derived/private_sample_lyrics_200k_v2/state.sqlite",
    ROOT / "data/derived/private_sample_lyrics_200k_v1/state.sqlite",
)
WORKSPACE = ROOT / "data/derived/private_linkage_review_200k_v1_1"
OUTPUT = ROOT / "reports/piloto_vinculacao_200k_v1_1"
PROTOCOL = ROOT / "docs/protocolo_piloto_vinculacao_200k_v1.md"
SEED = 20261104
PER_CELL = 20
MAX_PAYLOAD = 2 * 1024**2
STATUSES = (
    "accepted",
    "ambiguous",
    "not_found",
    "instrumental",
    "no_text",
    "insufficient_metadata",
)
COLUMNS = (
    "track_id",
    "artist_name",
    "track_name",
    "duration_ms",
    "popularity",
    "lyrics_query_id",
    "lyrics_status",
    "lyrics_reason",
    "v1_lyrics_query_id",
    "lyrics_selected_lrclib_id",
)


def select_queries(frame, per_cell=PER_CELL):
    levels.require(1 <= per_cell <= 20, "Limite de vinte consultas por célula.")
    # O Parquet conserva o campo bruto como texto. Validar e derivar uma coluna
    # numérica antes tanto da ordenação quanto da comparação, sem mudar o original.
    try:
        numeric = frame["popularity"].cast(pl.Float64, strict=True)
    except pl.exceptions.InvalidOperationError as exc:
        raise ValueError("Popularidade não convertível para número; fonte preservada.") from exc
    levels.categories(numeric, [20, 40], observed=True)
    frame = frame.with_columns(numeric.alias("review_popularity_numeric"))
    levels.require(frame["track_id"].n_unique() == frame.height, "IDs Spotify repetidos.")
    levels.require(set(frame["lyrics_status"].to_list()) <= set(STATUSES), "Status desconhecido.")
    missing = frame.filter(pl.col("lyrics_query_id").is_null())
    eligible = frame.filter(pl.col("lyrics_query_id").is_not_null())
    levels.require(
        eligible.group_by("lyrics_query_id")
        .agg(pl.col("lyrics_status").n_unique())["lyrics_status"]
        .max()
        == 1,
        "Consulta com status conflitantes.",
    )
    # Uma consulta pode representar várias faixas. Representante: maior escore,
    # depois menor ID; popularidade só estratifica a revisão, não julga vínculos.
    representatives = eligible.sort(
        ["lyrics_query_id", "review_popularity_numeric", "track_id"],
        descending=[False, True, False],
    ).unique("lyrics_query_id", keep="first", maintain_order=True)
    representatives = representatives.with_columns(
        (pl.col("review_popularity_numeric") >= 80).alias("extreme_tail")
    )
    rng = np.random.Generator(np.random.PCG64(SEED))
    selected, allocation = [], []
    for status in STATUSES:
        for tail in (False, True):
            cell = representatives.filter(
                (pl.col("lyrics_status") == status) & (pl.col("extreme_tail") == tail)
            ).sort("lyrics_query_id")
            population = cell.height
            if not population:
                continue
            n = min(per_cell, population)
            positions = sorted(rng.choice(population, n, replace=False).tolist())
            allocation.append(
                {
                    "status": status,
                    "extreme_tail": tail,
                    "population_queries": population,
                    "selected_queries": n,
                    "review_inclusion_probability": n / population,
                }
            )
            for row in cell[positions].to_dicts():
                row.update(
                    review_population_queries=population,
                    review_selected_queries=n,
                    review_inclusion_probability=n / population,
                    case_id=hashlib.sha256(
                        (str(SEED) + "|" + row["lyrics_query_id"]).encode()
                    ).hexdigest()[:16],
                )
                selected.append(row)
    levels.require(bool(selected), "Nenhuma consulta elegível para revisão.")
    return selected, allocation, missing.height, representatives.height


def readonly_cache(path):
    path = Path(path).resolve()
    levels.require(path.is_file(), "Cache local ausente; não será recriado: " + path.name)
    wal = Path(str(path) + "-wal")
    levels.require(
        not wal.exists() or wal.stat().st_size == 0,
        "Cache com WAL ativo; encerre o processo que escreve nele.",
    )
    db = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
    db.execute("PRAGMA query_only=ON")
    # Impede que uma consulta pequena se transforme em varredura de um banco grande.
    plan = " ".join(
        str(row)
        for row in db.execute(
            "EXPLAIN QUERY PLAN SELECT length(payload) FROM evidence WHERE query_id=?", ("fixture",)
        )
    )
    if "SEARCH" not in plan:
        db.close()
        raise ValueError("Cache sem índice para consulta pontual; nenhuma varredura permitida.")
    return db


def cached_metadata(databases, row):
    keys = list(
        dict.fromkeys(k for k in (row["lyrics_query_id"], row.get("v1_lyrics_query_id")) if k)
    )
    for database in databases:
        for key in keys:
            size = database.execute(
                "SELECT length(CAST(payload AS BLOB)) FROM evidence WHERE query_id=?", (key,)
            ).fetchone()
            if size is None:
                continue
            if size[0] is None or size[0] > MAX_PAYLOAD:
                return {
                    "cache_status": "payload_above_bound_or_null",
                    "candidate_count": None,
                    "candidates": [],
                    "candidate_list_truncated": False,
                }
            value = json.loads(
                database.execute(
                    "SELECT payload FROM evidence WHERE query_id=?", (key,)
                ).fetchone()[0]
            )
            if "candidates" not in value:
                continue
            candidates = value["candidates"]
            metadata = []
            for candidate in candidates[:50]:
                metadata.append(
                    {
                        **{
                            field: candidate.get(field)
                            for field in (
                                "id",
                                "lyrics_id",
                                "artistName",
                                "trackName",
                                "albumName",
                                "duration",
                                "instrumental",
                            )
                        },
                        "plain_text_present": bool(candidate.get("plainLyrics")),
                        "synced_text_present": bool(candidate.get("syncedLyrics")),
                    }
                )
            return {
                "cache_status": "cached_candidates",
                "candidate_count": len(candidates),
                "candidates": metadata,
                "candidate_list_truncated": len(candidates) > 50,
                "source_incomplete_reason": value.get("incomplete_reason"),
            }
    return {
        "cache_status": "evidence_not_cached",
        "candidate_count": None,
        "candidates": [],
        "candidate_list_truncated": False,
    }


def cache_stamp(path):
    stat = path.stat()
    wal = Path(str(path) + "-wal")
    levels.require(not wal.exists() or wal.stat().st_size == 0, "Cache com WAL ativo.")
    return {"bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def run(*, source=SOURCE, caches=CACHES, workspace=WORKSPACE, output=OUTPUT, expected=200000):
    from .manual_lyrics import exclusive

    source, workspace, output = (Path(p).resolve() for p in (source, workspace, output))
    caches = tuple(Path(p).resolve() for p in caches)
    levels.require(
        workspace.is_relative_to(ROOT / "data/derived") or expected != 200000,
        "Saída individual deve ficar em data/derived.",
    )
    levels.require(
        not workspace.is_relative_to(output) and not output.is_relative_to(workspace),
        "Separar saídas privadas e públicas.",
    )
    sources = [source, *caches, PROTOCOL, Path(__file__)]
    levels.require(
        all(not p.is_relative_to(workspace) and not p.is_relative_to(output) for p in sources),
        "Saída sobrepõe fonte.",
    )
    levels.require(pq.ParquetFile(source).metadata.num_rows == expected, "Amostra incompatível.")
    print("[1/4] Selando seleção do piloto; sem dump, rede ou novo índice...", flush=True)
    stamps = {str(p): cache_stamp(p) for p in caches}
    seal = {
        "version": "linkage-review-v1.1",
        "source_sha256": levels.digest(source),
        "code": levels.digest(Path(__file__)),
        "helpers": levels.digest(Path(levels.__file__)),
        "protocol": levels.digest(PROTOCOL),
        "cache_metadata": stamps,
        "seed": SEED,
        "per_cell": PER_CELL,
        "numpy": np.__version__,
    }
    with exclusive(workspace):
        levels.prepare_output(workspace, seal, sources)
        levels.prepare_output(output, seal, sources)
        if (workspace / "casos_revisao.csv").exists():
            summary = levels.read_json(output / "resumo_piloto.json")
            levels.require(
                summary["completed"], "Revisão existente sem conclusão; preservada para inspeção."
            )
            print("Piloto já preparado; anotações humanas preservadas.", flush=True)
            return summary
        summary = {
            "completed": False,
            "seal": seal,
            "new_lrclib_queries": 0,
            "indexes_built": 0,
            "human_review_completed": False,
            "precision_estimated": False,
            "recovery_recall_estimated": False,
            "existing_decisions_changed": False,
            "lyric_texts_exported": False,
        }
        levels.atomic_json(output / "resumo_piloto.json", summary)
        frame = pl.read_parquet(source, columns=COLUMNS)
        selected, allocation, missing, queries = select_queries(frame)
        print(
            "[2/4] Selecionadas "
            + str(len(selected))
            + " consultas únicas; lendo evidências por chave...",
            flush=True,
        )
        cases, review = [], []
        with ExitStack() as stack:
            databases = [stack.enter_context(closing(readonly_cache(p))) for p in caches]
            for row in selected:
                evidence = cached_metadata(databases, row)
                cases.append({**row, **evidence})
                review.append(
                    {
                        "case_id": row["case_id"],
                        "spotify_artist": row["artist_name"],
                        "spotify_title": row["track_name"],
                        "spotify_duration_seconds": float(row["duration_ms"]) / 1000
                        if row["duration_ms"] is not None
                        else None,
                        "cache_status": evidence["cache_status"],
                        "candidate_metadata_json": json.dumps(
                            evidence["candidates"], ensure_ascii=False
                        ),
                        "candidate_list_truncated": evidence["candidate_list_truncated"],
                        "source_incomplete_reason": evidence.get("source_incomplete_reason"),
                        "review_identity": "",
                        "review_version": "",
                        "review_decision": "",
                        "review_notes": "",
                    }
                )
        levels.require(
            stamps == {str(p): cache_stamp(p) for p in caches}, "Cache mudou durante o piloto."
        )
        levels.require(
            levels.digest(source) == seal["source_sha256"],
            "Resultado de origem mudou durante piloto.",
        )
        print(
            "[3/4] Exportando metadados privados; status e popularidade fora da ficha de revisão...",
            flush=True,
        )
        levels.atomic_json(workspace / "manifesto_privado.json", cases)
        levels.write_csv(workspace / "casos_revisao.csv", review)
        levels.write_csv(output / "alocacao_piloto.csv", allocation)
        summary.update(
            completed=True,
            source_tracks=expected,
            unique_query_population=queries,
            excluded_missing_query=missing,
            selected_queries=len(cases),
            cached_evidence=sum(r["cache_status"] == "cached_candidates" for r in cases),
            truncated_candidate_lists=sum(r["candidate_list_truncated"] for r in cases),
            metadata_review_only=True,
        )
        levels.atomic_json(output / "resumo_piloto.json", summary)
    print(
        "[4/4] Piloto preparado; revisão semântica ainda pendente. Agregados em " + str(output),
        flush=True,
    )
    return summary


def cli():
    argparse.ArgumentParser(description=__doc__).parse_args()
    run()
    return 0
