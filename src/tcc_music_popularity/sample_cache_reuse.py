"""Reaproveita decisões exatas do cache para a nova amostra, sem busca ou índice."""

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from contextlib import ExitStack, closing
from pathlib import Path

import polars as pl

from . import lyrics_recovery as recovery
from . import sample_lyrics as base
from . import sample_redesign as design
from .lyrics_ambiguity_v011 import strict_plain_text_metrics
from .manual_lyrics import atomic_frame, atomic_json, exclusive, fingerprint, require

ROOT = design.ROOT
SAMPLE = design.PRIVATE / "amostra_spotify.parquet"
SAMPLE_SUMMARY = design.REPORT / "resumo_sorteio.json"
CACHES = (recovery.WORKSPACE / "state.sqlite", base.WORKSPACE / "state.sqlite")
WORKSPACE = ROOT / "data/derived/private_nova_amostra_cache_v1"
OUTPUT = ROOT / "reports/reaproveitamento_nova_amostra_v1"
VERSION = "nova-amostra-cache-v1"
MAX_PAYLOAD = 2 * 1024**2
STATES = ("accepted", "instrumental", "pending_search", "insufficient_metadata", "cache_error")


def stamp(path):
    path = Path(path).resolve()
    require(path.is_file(), f"Cache ausente: {path}")
    wal = Path(str(path) + "-wal")
    require(
        not wal.exists() or wal.stat().st_size == 0,
        "Cache com WAL ativo; encerre o escritor, sem apagar WAL.",
    )
    info = path.stat()
    return {"path": str(path), "bytes": info.st_size, "mtime_ns": info.st_mtime_ns}


def readonly(path):
    stamp(path)
    db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    db.execute("PRAGMA query_only=ON")
    try:
        for table in ("queries", "lyrics"):
            plan = " ".join(
                str(r)
                for r in db.execute(
                    f"EXPLAIN QUERY PLAN SELECT data FROM {table} WHERE query_id=?", ("fixture",)
                )
            )
            require(
                "SEARCH" in plan.upper() and "SCAN" not in plan.upper(),
                f"Cache sem acesso por chave: {table}",
            )
    except Exception:
        db.close()
        raise
    return db


def bounded_query(db, key):
    row = db.execute(
        "SELECT length(CAST(data AS BLOB)),length(CAST(result AS BLOB)),status "
        "FROM queries WHERE query_id=?",
        (key,),
    ).fetchone()
    if row is None:
        return None
    require(
        row[0] is not None and row[0] <= MAX_PAYLOAD and (row[1] or 0) <= MAX_PAYLOAD,
        "Metadados de cache excedem limite ou estão vazios.",
    )
    data, result, status = db.execute(
        "SELECT data,result,status FROM queries WHERE query_id=?", (key,)
    ).fetchone()
    return json.loads(data), json.loads(result) if result else {}, status


def validate_lyric(db, key, result):
    size = db.execute(
        "SELECT length(CAST(data AS BLOB)) FROM lyrics WHERE query_id=?", (key,)
    ).fetchone()
    require(
        size is not None and size[0] is not None and size[0] <= MAX_PAYLOAD,
        "Texto aceito ausente ou acima do limite.",
    )
    lyric = json.loads(db.execute("SELECT data FROM lyrics WHERE query_id=?", (key,)).fetchone()[0])
    text = lyric.get("plain_text_source")
    require(isinstance(text, str) and bool(text.strip()), "Texto aceito vazio.")
    value = hashlib.sha256(text.encode()).hexdigest()
    strict = strict_plain_text_metrics(text)["strict_text_sha256"]
    require(
        value == lyric.get("text_sha256") == result.get("text_sha256"),
        "SHA do texto aceito diverge.",
    )
    require(
        strict == lyric.get("strict_text_sha256") == result.get("strict_text_sha256"),
        "Fingerprint do texto aceito diverge.",
    )
    require(
        lyric.get("lrclib_id") is not None
        and lyric["lrclib_id"] == result.get("selected_lrclib_id"),
        "ID selecionado não corresponde ao texto aceito.",
    )
    if result.get("selected_lyrics_id") is not None:
        require(
            lyric.get("lrclib_lyrics_id") == result["selected_lyrics_id"],
            "ID interno da letra diverge.",
        )
    return lyric


def reuse_query(databases, query):
    require(set(query) <= base.MATCH_FIELDS, "Campo proibido no matching.")
    key = fingerprint(query)
    for db, path, fallback_version in databases:
        cached = bounded_query(db, key)
        if cached is None:
            continue
        metadata, old_result, old_status = cached
        require(
            metadata == query and fingerprint(metadata) == key,
            "Consulta de cache não corresponde aos metadados completos.",
        )
        require(
            not old_result.get("status") or old_result["status"] == old_status,
            "Status interno do cache diverge.",
        )
        effective = old_result.get("rules_version") or (
            base.VERSION if old_result.get("recovery_rule") == "preserved_v1" else fallback_version
        )
        result = {
            "status": "pending_search",
            "reason": "cached_nonaccepted_requires_followup",
            "source_state": str(path),
            "source_query_id": key,
            "previous_status": old_status,
            "previous_reason": old_result.get("reason"),
            "previous_result": old_result,
            "rules_version": effective,
            "reuse_version": VERSION,
        }
        # A decisão v2 exata tem prioridade. Não usar v1 para contornar uma
        # decisão v2 existente; status negativos são evidência histórica apenas.
        if old_status == "accepted":
            lyric = validate_lyric(db, key, old_result)
            result.update(status="accepted", reason="exact_cached_acceptance_with_verified_text")
            return result, lyric
        if old_status == "instrumental":
            result.update(status="instrumental", reason="exact_cached_instrumental_decision")
        return result, None
    return {
        "status": "pending_search",
        "reason": "query_not_in_cache",
        "source_state": None,
        "source_query_id": None,
        "previous_status": None,
        "previous_reason": None,
        "previous_result": {},
        "rules_version": None,
        "reuse_version": VERSION,
    }, None


def source_seal(sample, summary_path, caches):
    summary = design.read_json(summary_path)
    require(summary["concluido"], "Sorteio não concluído.")
    require(
        design.sha256(sample) == summary["parquet_sha256"], "Amostra difere do sorteio congelado."
    )
    return summary, {
        "version": VERSION,
        "sample_sha256": summary["parquet_sha256"],
        "summary_sha256": design.sha256(summary_path),
        "caches": [stamp(p) for p in caches],
        "code_hashes": {
            str(p.relative_to(ROOT)): design.sha256(p)
            for p in [
                Path(__file__),
                Path(recovery.__file__),
                Path(base.__file__),
                ROOT / "src/tcc_music_popularity/normalization.py",
                ROOT / "src/tcc_music_popularity/lyrics_ambiguity_v011.py",
                ROOT / "src/tcc_music_popularity/manual_lyrics.py",
                ROOT / "src/tcc_music_popularity/lyrics_pilot.py",
                ROOT / "src/tcc_music_popularity/lyrics_pilot_v012.py",
            ]
        },
    }


def init_state(db, seal, queries):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS decisions(
            query_id TEXT PRIMARY KEY, data TEXT NOT NULL, result TEXT NOT NULL,
            lyric TEXT);
    """)
    stored = db.execute("SELECT value FROM meta WHERE key='seal'").fetchone()
    if stored is None:
        require(
            db.execute("SELECT count(*) FROM decisions").fetchone()[0] == 0, "Checkpoint sem selo."
        )
        with db:
            db.execute(
                "INSERT INTO meta VALUES ('seal',?)",
                (json.dumps(seal, ensure_ascii=False, sort_keys=True),),
            )
    else:
        require(
            json.loads(stored[0]) == seal,
            "Fontes/código mudaram; preservar checkpoint e investigar.",
        )
    for key, data in db.execute("SELECT query_id,data FROM decisions"):
        require(
            key in queries and json.loads(data) == queries[key],
            "Checkpoint contém consulta incompatível.",
        )


def export_private(db, sample, tracks, workspace):
    results = {
        key: json.loads(raw) for key, raw in db.execute("SELECT query_id,result FROM decisions")
    }
    records = []
    for track, key in tracks:
        r = (
            results[key]
            if key
            else {"status": "insufficient_metadata", "reason": "missing_artist_or_title"}
        )
        previous = r.get("previous_result", {})
        records.append(
            {
                "track_id": track,
                "lyrics_query_id": key,
                "lyrics_status": r["status"],
                "lyrics_reason": r["reason"],
                "lyrics_source_state": r.get("source_state"),
                "lyrics_previous_status": r.get("previous_status"),
                "lyrics_rules_version": r.get("rules_version"),
                "lyrics_selected_lrclib_id": previous.get("selected_lrclib_id"),
                "lyrics_text_sha256": previous.get("text_sha256"),
                "lyrics_strict_text_sha256": previous.get("strict_text_sha256"),
                "lyrics_text_ref": key if r["status"] == "accepted" else None,
            }
        )
    final = sample.join(
        pl.DataFrame(records, infer_schema_length=None),
        on="track_id",
        how="left",
        validate="1:1",
        maintain_order="left",
    )
    require(
        final.height == sample.height and final.select(sample.columns).equals(sample),
        "Campos/desenho da amostra alterados.",
    )
    require(final["lyrics_status"].is_in(STATES).all(), "Status desconhecido.")
    atomic_frame(workspace / "resultados_faixas.parquet", final)
    atomic_frame(
        workspace / "pendencias_busca.parquet",
        final.filter(~pl.col("lyrics_status").is_in(["accepted", "instrumental"])),
    )
    schema = {
        "query_id": pl.String,
        "accepted_text": pl.String,
        "plain_text_source": pl.String,
        "synced_text_source": pl.String,
        "lrclib_id": pl.Int64,
        "lrclib_lyrics_id": pl.Int64,
        "text_sha256": pl.String,
        "strict_text_sha256": pl.String,
        "source_state": pl.String,
        "provenance_json": pl.String,
    }
    lyrics = []
    for key, raw, result in db.execute(
        "SELECT query_id,lyric,result FROM decisions WHERE lyric IS NOT NULL"
    ):
        lyric, r = json.loads(raw), json.loads(result)
        require(r["status"] == "accepted", "Texto ligado a decisão não aceita.")
        lyrics.append(
            {
                "query_id": key,
                "accepted_text": lyric["plain_text_source"],
                "plain_text_source": lyric.get("source_plain_original", lyric["plain_text_source"]),
                "synced_text_source": lyric.get("synced_text_source"),
                "lrclib_id": lyric["lrclib_id"],
                "lrclib_lyrics_id": lyric.get("lrclib_lyrics_id"),
                "text_sha256": lyric["text_sha256"],
                "strict_text_sha256": lyric["strict_text_sha256"],
                "source_state": r["source_state"],
                "provenance_json": json.dumps(
                    {
                        k: v
                        for k, v in lyric.items()
                        if k
                        not in {"plain_text_source", "source_plain_original", "synced_text_source"}
                    },
                    ensure_ascii=False,
                ),
            }
        )
    require(
        {r["query_id"] for r in lyrics} == set(final["lyrics_text_ref"].drop_nulls().to_list()),
        "Textos e referências não reconciliados.",
    )
    atomic_frame(workspace / "letras_aceitas.parquet", pl.DataFrame(lyrics, schema=schema))
    return final, len(lyrics)


def publish(final, output):
    # Popularidade e gênero entram somente depois das decisões de cache.
    enriched = final.with_columns(
        pl.col("year").cast(pl.Int32).alias("_cache_year"),
        pl.col("popularity").cast(pl.Float64).alias("_cache_pop"),
    ).with_columns(
        pl.when(pl.col("_cache_year") <= 2009)
        .then(pl.lit("2000–2009"))
        .when(pl.col("_cache_year") <= 2019)
        .then(pl.lit("2010–2019"))
        .otherwise(pl.lit("2020–2023"))
        .alias("periodo"),
        pl.when(pl.col("_cache_pop") < 20)
        .then(pl.lit("0–19"))
        .when(pl.col("_cache_pop") < 40)
        .then(pl.lit("20–39"))
        .when(pl.col("_cache_pop") < 60)
        .then(pl.lit("40–59"))
        .when(pl.col("_cache_pop") < 80)
        .then(pl.lit("60–79"))
        .otherwise(pl.lit("80–100"))
        .alias("faixa_popularidade"),
    )
    tables = []
    for group in ["genre", "periodo", "faixa_popularidade"]:
        tables.append(
            enriched.group_by(group, "lyrics_status")
            .agg(pl.len().alias("n"), pl.col("_nova_peso").sum().alias("soma_pesos"))
            .rename({group: "categoria"})
            .with_columns(pl.lit(group).alias("agrupamento"))
        )
    pl.concat(tables).sort(["agrupamento", "categoria", "lyrics_status"]).write_csv(
        output / "cobertura_cache.csv"
    )
    enriched.group_by("lyrics_status").agg(
        pl.len().alias("n"), pl.col("_nova_peso").sum().alias("soma_pesos")
    ).sort("lyrics_status").write_csv(output / "status_cache.csv")


def run(
    *,
    sample=SAMPLE,
    summary_path=SAMPLE_SUMMARY,
    caches=CACHES,
    workspace=WORKSPACE,
    output=OUTPUT,
    retry_errors=False,
):
    sample, summary_path, workspace, output = map(Path, [sample, summary_path, workspace, output])
    caches = tuple(Path(p).resolve() for p in caches)
    print("[1/4] Conferindo a nova amostra e os caches locais; sem SSD ou rede...", flush=True)
    summary, seal = source_seal(sample, summary_path, caches)
    frame = pl.read_parquet(sample)
    require(
        frame.height == summary["n"] and frame["track_id"].n_unique() == frame.height,
        "Tamanho/IDs da amostra divergentes.",
    )
    queries, tracks = recovery.make_queries(frame)
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with exclusive(workspace), ExitStack() as stack:
        db = stack.enter_context(closing(sqlite3.connect(workspace / "state.sqlite")))
        init_state(db, seal, queries)
        databases = [
            (stack.enter_context(closing(readonly(p))), p, version)
            for p, version in zip(caches, [recovery.VERSION, base.VERSION], strict=True)
        ]
        stored = {
            key: json.loads(raw) for key, raw in db.execute("SELECT query_id,result FROM decisions")
        }
        pending = [
            key
            for key in sorted(queries)
            if key not in stored or (retry_errors and stored[key]["status"] == "cache_error")
        ]
        print(
            f"[2/4] {len(pending)} consultas por chave; {len(queries) - len(pending)} checkpoints reutilizados...",
            flush=True,
        )
        last = 0.0
        for number, key in enumerate(pending, start=1):
            query = queries[key]
            try:
                result, lyric = reuse_query(databases, query)
            except (ValueError, TypeError, KeyError, OSError, sqlite3.Error) as exc:
                result, lyric = (
                    {"status": "cache_error", "reason": type(exc).__name__, "error": str(exc)},
                    None,
                )
            with db:
                db.execute(
                    "INSERT OR REPLACE INTO decisions VALUES (?,?,?,?)",
                    (
                        key,
                        json.dumps(query, ensure_ascii=False),
                        json.dumps(result, ensure_ascii=False),
                        json.dumps(lyric, ensure_ascii=False) if lyric else None,
                    ),
                )
            if time.monotonic() - last >= 10:
                progress = {
                    "etapa": "cache",
                    "novas_consultas": number,
                    "consultas_pendentes": len(pending) - number,
                    "segundos": time.monotonic() - started,
                }
                atomic_json(workspace / "progress.json", progress)
                print(json.dumps(progress), flush=True)
                last = time.monotonic()
        print("[3/4] Exportando textos privados reutilizados e fila de pendências...", flush=True)
        require(
            seal["caches"] == [stamp(p) for p in caches], "Cache foi alterado durante a leitura."
        )
        final, accepted_queries = export_private(db, frame, tracks, workspace)
        publish(final, output)
        result = {
            "concluido": True,
            "etapa": "reaproveitamento_cache",
            "version": VERSION,
            "recuperacao_integral_concluida": False,
            "n_faixas": frame.height,
            "n_consultas": len(queries),
            "n_textos_reutilizados": accepted_queries,
            "status_por_faixa": {
                s: final.filter(pl.col("lyrics_status") == s).height for s in STATES
            },
            "fontes": seal,
            "segundos": time.monotonic() - started,
            "dump_acessado": False,
            "indices_criados": 0,
            "rede": False,
            "treino": False,
            "textos_ou_metadados_no_relatorio_publico": False,
            "arquivos_privados_sha256": {
                name: design.sha256(workspace / name)
                for name in [
                    "resultados_faixas.parquet",
                    "pendencias_busca.parquet",
                    "letras_aceitas.parquet",
                ]
            },
            "agregados_sha256": {
                name: design.sha256(output / name)
                for name in ["status_cache.csv", "cobertura_cache.csv"]
            },
            "limite": "Ausência/rejeição no cache permanece pendência de busca; aceitações anteriores não são revisão humana.",
        }
        require(
            design.sha256(sample) == seal["sample_sha256"], "Amostra mudou durante o processamento."
        )
        atomic_json(output / "resumo_reaproveitamento.json", result)
        atomic_json(
            workspace / "progress.json",
            {
                "etapa": "concluido",
                "n_faixas": frame.height,
                "status_por_faixa": result["status_por_faixa"],
            },
        )
    print(
        json.dumps({"etapa": "resumo_cache", "status_por_faixa": result["status_por_faixa"]}),
        flush=True,
    )
    print(
        f"[4/4] Cache concluído; buscas restantes ainda pendentes. Agregados em {output}",
        flush=True,
    )
    return result


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--status", action="store_true", help="Lê somente o último progresso local."
    )
    parser.add_argument(
        "--retry-errors",
        action="store_true",
        help="Reavalia somente erros de cache, mantendo decisões concluídas.",
    )
    args = parser.parse_args(argv)
    if args.status:
        path = WORKSPACE / "progress.json"
        print(
            path.read_text(encoding="utf-8")
            if path.exists()
            else "Reaproveitamento ainda não iniciado."
        )
        return 0
    try:
        result = run(retry_errors=args.retry_errors)
    except KeyboardInterrupt:
        print("Interrompido; retome com o mesmo comando, preservando checkpoints.", file=sys.stderr)
        return 2
    return 2 if result["status_por_faixa"]["cache_error"] else 0
