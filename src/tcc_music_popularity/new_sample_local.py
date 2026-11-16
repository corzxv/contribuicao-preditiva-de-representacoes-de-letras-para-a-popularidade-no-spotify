"""Busca local da nova amostra com índice v2 e complemento só quando necessário."""

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
from . import sample_cache_reuse as cache
from . import sample_lyrics as base
from . import sample_redesign as design
from .manual_lyrics import (
    atomic_frame,
    atomic_json,
    exclusive,
    fingerprint,
    meta_get,
    meta_put,
    require,
)

ROOT = design.ROOT
SOURCE_WORKSPACE = cache.WORKSPACE
SOURCE_SUMMARY = cache.OUTPUT / "resumo_reaproveitamento.json"
SAMPLE = design.PRIVATE / "amostra_spotify.parquet"
DUMP = recovery.local.DEFAULT_DESTINATION / "lrclib-db-dump-20261012T090639Z.sqlite3"
PRIMARY = recovery.INDEX / "lookup.sqlite"
SUPPLEMENT = recovery.local.DEFAULT_DESTINATION / "tcc_lookup_nova_amostra_v1"
WORKSPACE = ROOT / "data/derived/private_nova_amostra_local_v1"
OUTPUT = ROOT / "reports/busca_local_nova_amostra_v1"
VERSION = "nova-amostra-local-v1"
NEGATIVE = {"ambiguous", "no_text", "not_found"}


def primary_metadata(dump, primary, recovery_state):
    identity = recovery.local.checked_dump(dump)
    with closing(base.stable_readonly(primary)) as index:
        seal, progress = meta_get(index, "seal"), meta_get(index, "progress")
        require(
            progress["complete"] and seal["dump"] == identity,
            "Índice principal incompleto ou de outro dump.",
        )
        require(
            seal["rules"] == design.sha256(Path(recovery.__file__)), "Código do índice v2 mudou."
        )
        plan = " ".join(
            str(tuple(r))
            for r in index.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM catalog WHERE artist_key=? AND title_key=? ORDER BY id LIMIT 501",
                ("fixture", "fixture"),
            )
        )
        require(
            "SEARCH" in plan.upper() and "SCAN" not in plan.upper(),
            "Índice sem acesso pontual por artista/título.",
        )
    with closing(base.stable_readonly(recovery_state)) as state:
        artists = meta_get(state, "lookup_artists")
    require(
        isinstance(artists, list) and fingerprint(sorted(artists)) == seal["artists"],
        "Lista de artistas não corresponde ao índice v2.",
    )
    return (
        identity,
        set(artists),
        {"seal": seal, "progress": progress, "stamp": cache.stamp(primary)},
    )


def can_reuse_negative(value, previous_source, identity):
    result = value.get("previous_result", {})
    return (
        value.get("source_state") == str(previous_source.resolve())
        and value.get("previous_status") in NEGATIVE
        and result.get("status") == value.get("previous_status")
        and result.get("rules_version") == recovery.VERSION
        and result.get("method") == "controlled_lookup"
        and not result.get("operational_limit", True)
        and identity is not None
    )


def check_text(lyric, result):
    text = lyric.get("plain_text_source")
    require(isinstance(text, str) and bool(text.strip()), "Letra protegida vazia.")
    require(
        hashlib.sha256(text.encode()).hexdigest() == lyric["text_sha256"] == result["text_sha256"],
        "Hash da letra protegida diverge.",
    )
    require(
        cache.strict_plain_text_metrics(text)["strict_text_sha256"]
        == lyric["strict_text_sha256"]
        == result["strict_text_sha256"],
        "Fingerprint da letra protegida diverge.",
    )
    require(
        lyric["lrclib_id"] == result["selected_lrclib_id"], "Vínculo da letra protegida diverge."
    )


def initialize(db, old, sample, previous, seal, identity, previous_source, source_state):
    queries, tracks = recovery.make_queries(sample)
    expected = dict(tracks)
    require(
        expected == dict(previous.select("track_id", "lyrics_query_id").iter_rows()),
        "Consultas de 41 não correspondem à amostra.",
    )
    stored_seal = db.execute("SELECT 1 FROM sqlite_schema WHERE name='meta'").fetchone()
    if stored_seal and meta_get(db, "seal") is not None:
        require(
            meta_get(db, "seal") == seal,
            "Fontes/código mudaram; preservar checkpoint e investigar.",
        )
    else:
        if not stored_seal:
            require(
                not db.execute("SELECT 1 FROM sqlite_schema WHERE type='table'").fetchone(),
                "Workspace desconhecido.",
            )
            db.executescript("BEGIN IMMEDIATE;" + base.STATE_SQL + "COMMIT;")
        else:
            for table in ("queries", "tracks", "lyrics", "evidence"):
                require(
                    db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0,
                    "Checkpoint não vazio sem selo; preservar e investigar.",
                )
        source = {
            key: (data, result, lyric)
            for key, data, result, lyric in old.execute(
                "SELECT query_id,data,result,lyric FROM decisions"
            )
        }
        require(
            set(source) == set(queries), "Consultas do checkpoint 41 incompletas ou excedentes."
        )
        prior_status = {}
        for key, status in previous.select("lyrics_query_id", "lyrics_status").iter_rows():
            if key:
                require(
                    key not in prior_status or prior_status[key] == status,
                    "Status conflitantes por consulta.",
                )
                prior_status[key] = status
        with db:
            for key, query in queries.items():
                data, raw, raw_lyric = source[key]
                require(
                    json.loads(data) == query and fingerprint(query) == key,
                    "Metadados completos divergentes.",
                )
                value = json.loads(raw)
                require(value["status"] == prior_status[key], "Status de 41 diverge do checkpoint.")
                protected = value["status"] in {"accepted", "instrumental"}
                negative = can_reuse_negative(value, previous_source, identity)
                if protected or negative:
                    result = dict(value["previous_result"])
                    result["rules_version"] = value["rules_version"]
                    result["new_sample_origin"] = (
                        "protected_cache_41" if protected else "reused_controlled_negative"
                    )
                    status = result["status"]
                    require(
                        status == (value["status"] if protected else value["previous_status"]),
                        "Status histórico incompatível.",
                    )
                    if status == "accepted":
                        require(raw_lyric is not None, "Aceitação de 41 sem texto.")
                        check_text(json.loads(raw_lyric), result)
                    db.execute(
                        "INSERT INTO queries(query_id,data,status,result) VALUES (?,?,?,?)",
                        (key, data, status, json.dumps(result, ensure_ascii=False)),
                    )
                    if status == "accepted":
                        db.execute("INSERT INTO lyrics VALUES (?,?)", (key, raw_lyric))
                else:
                    db.execute("INSERT INTO queries(query_id,data) VALUES (?,?)", (key, data))
                db.execute(
                    "INSERT INTO evidence VALUES (?,?)",
                    (
                        key,
                        json.dumps(
                            {
                                "origin": "stage_41",
                                "source_state": str(source_state),
                                "previous_cache_status": value["status"],
                                "previous_matching_status": value.get("previous_status"),
                            },
                            ensure_ascii=False,
                        ),
                    ),
                )
            db.executemany("INSERT INTO tracks VALUES (?,?)", tracks)
            meta_put(db, "seal", seal)
    require(
        dict(db.execute("SELECT track_id,query_id FROM tracks")) == expected,
        "Vínculos de checkpoint alterados.",
    )
    for key, raw in db.execute("SELECT query_id,data FROM queries"):
        require(
            key in queries and json.loads(raw) == queries[key],
            "Consulta incompatível no checkpoint.",
        )
    return queries


def evidence_metadata(query, candidates, identity, index, incomplete):
    # Mantém IDs e hashes de todos os candidatos. Textos integrais apenas para
    # aceitos; candidatos rejeitados são recuperáveis do dump imutável por ID.
    records = []
    for candidate in candidates:
        row = {
            name: candidate.get(name)
            for name in (
                "id",
                "local_lyrics_id",
                "trackName",
                "artistName",
                "albumName",
                "duration",
                "instrumental",
            )
        }
        for name in ("plainLyrics", "syncedLyrics"):
            text = candidate.get(name)
            row[name + "_sha256"] = (
                hashlib.sha256(text.encode()).hexdigest() if text is not None else None
            )
            row[name + "_characters"] = len(text) if text is not None else 0
        records.append(row)
    return {
        "query": query,
        "source": identity,
        "index": str(index),
        "candidates_metadata": records,
        "incomplete_reason": incomplete,
        "rules_version": recovery.VERSION,
    }


def search(
    db,
    source,
    primary,
    supplement,
    primary_artists,
    extra_artists,
    identity,
    *,
    retry=False,
    limit=None,
    primary_path=PRIMARY,
    supplement_path=SUPPLEMENT / "lookup.sqlite",
    progress_path=None,
):
    condition = (
        "status='pending' OR (status='technical_error' AND attempts<3)"
        if retry
        else "status='pending'"
    )
    jobs = db.execute(
        f"SELECT query_id,data FROM queries WHERE {condition} ORDER BY query_id LIMIT ?",
        (limit if limit is not None else -1,),
    ).fetchall()
    started, last = time.monotonic(), 0.0
    for number, (key, raw) in enumerate(jobs, start=1):
        query = json.loads(raw)
        artist = recovery.profile(query["artist_name_query"], query["track_name_query"])["artist"]
        with db:
            db.execute("UPDATE queries SET attempts=attempts+1 WHERE query_id=?", (key,))
        tick = time.monotonic()
        try:
            covered = artist in primary_artists
            require(
                covered or (artist in extra_artists and supplement is not None),
                "Artista sem índice completo.",
            )
            index = primary if covered else supplement
            candidates, incomplete = recovery.lookup(source, index, query)
            result, lyric = recovery.classify(
                query, candidates, incomplete, origin="controlled_lookup"
            )
            result["new_sample_origin"] = (
                "existing_v2_index" if covered else "new_artist_supplement"
            )
            result["absence_scope"] = "controlled_metadata_keys_in_fixed_local_snapshot"
            if lyric:
                check_text(lyric, result)
                lyric.update(query_id=key, source_dump=identity, rules_version=recovery.VERSION)
            evidence = evidence_metadata(
                query,
                candidates,
                identity,
                primary_path if covered else supplement_path,
                incomplete,
            )
            with db:
                db.execute(
                    "UPDATE queries SET status=?,result=?,elapsed_seconds=? WHERE query_id=?",
                    (
                        result["status"],
                        json.dumps(result, ensure_ascii=False),
                        time.monotonic() - tick,
                        key,
                    ),
                )
                if lyric:
                    db.execute(
                        "INSERT OR REPLACE INTO lyrics VALUES (?,?)",
                        (key, json.dumps(lyric, ensure_ascii=False)),
                    )
                db.execute(
                    "INSERT OR REPLACE INTO evidence VALUES (?,?)",
                    (key, json.dumps(evidence, ensure_ascii=False)),
                )
        except (ValueError, TypeError, KeyError, OSError, sqlite3.Error) as exc:
            with db:
                db.execute(
                    "UPDATE queries SET status='technical_error',result=? WHERE query_id=?",
                    (
                        json.dumps(
                            {
                                "status": "technical_error",
                                "reason": type(exc).__name__,
                                "error": str(exc),
                                "rules_version": recovery.VERSION,
                                "new_sample_origin": "technical_error",
                            }
                        ),
                        key,
                    ),
                )
        if time.monotonic() - last >= 10:
            value = {
                "etapa": "busca_local",
                "novas_consultas": number,
                "pendentes_nesta_execucao": len(jobs) - number,
                "segundos": time.monotonic() - started,
            }
            print(json.dumps(value), flush=True)
            if progress_path is not None:
                atomic_json(progress_path, value)
            last = time.monotonic()
    return len(jobs)


def export(db, sample, previous, workspace):
    final, accepted_queries = base.export_private(db, sample, workspace)
    extras = []
    for key, raw in db.execute("SELECT query_id,result FROM queries"):
        value = json.loads(raw) if raw else {}
        extras.append(
            {
                "lyrics_query_id": key,
                "effective_rules": value.get("rules_version", recovery.VERSION),
                "lyrics_new_sample_origin": value.get("new_sample_origin", "pending"),
            }
        )
    final = (
        final.join(
            pl.DataFrame(extras),
            on="lyrics_query_id",
            how="left",
            validate="m:1",
            maintain_order="left",
        )
        .with_columns(
            pl.col("effective_rules").fill_null(recovery.VERSION).alias("lyrics_rules_version")
        )
        .drop("effective_rules")
    )
    protected = previous.filter(pl.col("lyrics_status").is_in(["accepted", "instrumental"]))
    check = protected.select(
        "track_id",
        "lyrics_status",
        "lyrics_selected_lrclib_id",
        "lyrics_text_sha256",
        "lyrics_strict_text_sha256",
    )
    require(
        final.join(check.select("track_id"), on="track_id", how="semi")
        .select(check.columns)
        .sort("track_id")
        .to_dicts()
        == check.sort("track_id").to_dicts(),
        "Status/texto/vínculo protegido de 41 mudou.",
    )
    final = final.join(
        previous.select("track_id", pl.col("lyrics_status").alias("cache41_lyrics_status")),
        on="track_id",
        how="left",
        validate="1:1",
        maintain_order="left",
    )
    # O exportador legado recebe o texto efetivo em plain_text_source. Na saída
    # nova, separa-o das representações originais, inclusive plain ausente em LRC.
    import pyarrow as pa
    import pyarrow.parquet as pq

    path = workspace / "letras_aceitas_200k.parquet"
    schema = pq.read_schema(path).append(pa.field("accepted_text", pa.string()))
    temporary = workspace / "letras_aceitas.parquet.tmp"
    with pq.ParquetWriter(temporary, schema, compression="zstd") as writer:
        for batch in pq.ParquetFile(path).iter_batches(batch_size=128):
            rows = []
            for row in batch.to_pylist():
                provenance = json.loads(row["provenance_json"])
                row["accepted_text"] = row["plain_text_source"]
                row["plain_text_source"] = provenance.pop(
                    "source_plain_original", row["plain_text_source"]
                )
                row["provenance_json"] = json.dumps(provenance, ensure_ascii=False)
                rows.append(row)
            writer.write_table(pa.Table.from_pylist(rows, schema=schema))
    temporary.replace(workspace / "letras_aceitas.parquet")
    # Arquivos intermediários pertencem exclusivamente a este workspace novo.
    path.unlink()
    (workspace / "resultados_faixas_200k.parquet").unlink()
    atomic_frame(workspace / "resultados_faixas.parquet", final)
    atomic_frame(
        workspace / "pendencias_revisao.parquet",
        final.filter(~pl.col("lyrics_status").is_in(["accepted", "instrumental"])),
    )
    return final, accepted_queries


def run(
    *,
    sample=SAMPLE,
    source_summary=SOURCE_SUMMARY,
    source_workspace=SOURCE_WORKSPACE,
    dump=DUMP,
    primary=PRIMARY,
    recovery_state=recovery.WORKSPACE / "state.sqlite",
    supplement=SUPPLEMENT,
    workspace=WORKSPACE,
    output=OUTPUT,
    previous_report=ROOT / "reports/recuperacao_letras_200k_v2/resumo_recuperacao_letras_200k.json",
    retry=False,
    limit=None,
):
    (
        sample,
        source_summary,
        source_workspace,
        dump,
        primary,
        recovery_state,
        supplement,
        workspace,
        output,
    ) = map(
        Path,
        [
            sample,
            source_summary,
            source_workspace,
            dump,
            primary,
            recovery_state,
            supplement,
            workspace,
            output,
        ],
    )
    print("[1/5] Conferindo amostra, cache e índice v2 do SSD; sem rede...", flush=True)
    require(
        workspace.resolve() != source_workspace.resolve(),
        "Resultados novos exigem workspace separado de 41.",
    )
    require(
        supplement.resolve() != primary.parent.resolve(),
        "Complemento precisa de pasta separada do índice antigo.",
    )
    prior = design.read_json(source_summary)
    require(prior["concluido"], "Etapa 41 incompleta.")
    require(design.sha256(sample) == prior["fontes"]["sample_sha256"], "Amostra alterada.")
    for name, value in prior["arquivos_privados_sha256"].items():
        require(design.sha256(source_workspace / name) == value, f"Saída de 41 alterada: {name}")
    for name, value in prior["fontes"]["code_hashes"].items():
        require(design.sha256(ROOT / name) == value, "Código anterior selado mudou.")
    identity, artists, index_info = primary_metadata(dump, primary, recovery_state)
    old_report = design.read_json(previous_report)
    require(
        old_report["completed"] and old_report["source"] == identity,
        "Recuperação v2 não corresponde ao dump atual.",
    )
    require(
        old_report["code_hashes"]["lyrics_recovery.py"] == design.sha256(Path(recovery.__file__)),
        "Regras históricas não correspondem ao código congelado.",
    )
    frame = pl.read_parquet(sample)
    previous = pl.read_parquet(source_workspace / "resultados_faixas.parquet")
    require(
        frame.height == prior["n_faixas"] and previous.select(frame.columns).equals(frame),
        "Amostra/desenho de 41 divergente.",
    )
    source_state = source_workspace / "state.sqlite"
    source_stamp = cache.stamp(source_state)
    seal = {
        "version": VERSION,
        "sample_sha256": prior["fontes"]["sample_sha256"],
        "summary41_sha256": design.sha256(source_summary),
        "previous_report_sha256": design.sha256(previous_report),
        "state41_sha256": design.sha256(source_state),
        "dump": identity,
        "primary": index_info,
        "previous_state": cache.stamp(recovery_state),
        "supplement_path": str(supplement.resolve()),
        "code_sha256": design.sha256(Path(__file__)),
        "rules_sha256": design.sha256(Path(recovery.__file__)),
    }
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with exclusive(workspace), ExitStack() as stack:
        old = stack.enter_context(closing(base.stable_readonly(source_state)))
        db = stack.enter_context(closing(base.state_connection(workspace)))
        initialize(db, old, frame, previous, seal, identity, recovery_state, source_state)
        extra = meta_get(db, "extra_artists")
        if extra is None:
            extra = sorted(
                {
                    recovery.profile(
                        json.loads(r[0])["artist_name_query"], json.loads(r[0])["track_name_query"]
                    )["artist"]
                    for r in db.execute("SELECT data FROM queries WHERE status='pending'")
                }
                - artists
            )
            with db:
                meta_put(db, "extra_artists", extra)
        print(
            f"[2/5] Índice existente cobre {len(artists)} artistas; {len(extra)} artistas precisam de complemento...",
            flush=True,
        )
        atomic_json(
            workspace / "progress.json",
            {"etapa": "preparando_indices", "artistas_complemento": len(extra)},
        )
        if extra:
            print(
                "Complemento necessário: uma passagem de metadados do dump, com retomada; índices antigos preservados.",
                flush=True,
            )
            recovery.build_index(dump, supplement, extra, identity)
        source = stack.enter_context(closing(base.stable_readonly(dump)))
        index = stack.enter_context(closing(base.stable_readonly(primary)))
        additional = None
        if extra:
            additional = stack.enter_context(
                closing(base.stable_readonly(supplement / "lookup.sqlite"))
            )
            require(meta_get(additional, "progress")["complete"], "Complemento incompleto.")
        print(
            "[3/5] Buscando pendências por artista/título/duração/versão; checkpoints por consulta...",
            flush=True,
        )
        new_queries = search(
            db,
            source,
            index,
            additional,
            artists,
            set(extra),
            identity,
            retry=retry,
            limit=limit,
            primary_path=primary,
            supplement_path=supplement / "lookup.sqlite",
            progress_path=workspace / "progress.json",
        )
        require(
            source_stamp == cache.stamp(source_state), "Checkpoint 41 foi alterado durante a busca."
        )
        require(index_info["stamp"] == cache.stamp(primary), "Índice principal foi alterado.")
        require(
            identity == recovery.local.checked_dump(dump), "Dump mudou durante o processamento."
        )
        print(
            "[4/5] Conferindo preservação dos vínculos anteriores e exportando resultados...",
            flush=True,
        )
        final, n_texts = export(db, frame, previous, workspace)
        cache.publish(final, output)
        (output / "status_cache.csv").replace(output / "status_busca.csv")
        (output / "cobertura_cache.csv").replace(output / "cobertura_busca.csv")
        final.group_by("cache41_lyrics_status", "lyrics_status").agg(pl.len().alias("n")).sort(
            ["cache41_lyrics_status", "lyrics_status"]
        ).write_csv(output / "transicoes_status.csv")
        statuses = {s: final.filter(pl.col("lyrics_status") == s).height for s in base.STATUSES}
        finished = statuses["pending"] == 0 and statuses["technical_error"] == 0
        origins = dict(
            db.execute(
                "SELECT json_extract(result,'$.new_sample_origin'),count(*) FROM queries GROUP BY 1"
            )
        )
        result = {
            "completed": finished,
            "version": VERSION,
            "stage": "local_snapshot_search",
            "sample_rows": frame.height,
            "accepted_queries": n_texts,
            "status_counts": statuses,
            "new_queries_this_invocation": new_queries,
            "origins_query_counts": origins,
            "supplement_artists": len(extra),
            "protected_41_counts": prior["status_por_faixa"],
            "seconds": time.monotonic() - started,
            "seal": seal,
            "http_requests": 0,
            "new_embeddings": False,
            "models_trained": False,
            "sample_replaced": False,
            "scope": "Resultados sob chaves controladas e regras v2 no snapshot local; não ausência universal de letras ou validação humana.",
            "private_sha256": {
                name: design.sha256(workspace / name)
                for name in [
                    "resultados_faixas.parquet",
                    "letras_aceitas.parquet",
                    "pendencias_revisao.parquet",
                ]
            },
            "public_sha256": {
                name: design.sha256(output / name)
                for name in ["status_busca.csv", "cobertura_busca.csv", "transicoes_status.csv"]
            },
        }
        atomic_json(output / "resumo_busca_local.json", result)
        atomic_json(
            workspace / "progress.json",
            {"etapa": "concluido" if finished else "parcial", "status_counts": statuses},
        )
    print(json.dumps({"etapa": "resumo_local", "status_por_faixa": statuses}), flush=True)
    print(
        f"[5/5] {'Concluído' if finished else 'Parcial; retomar'}; resultados em {output}",
        flush=True,
    )
    return result


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--status", action="store_true", help="Lê o progresso da busca e do complemento."
    )
    parser.add_argument(
        "--retry-errors",
        action="store_true",
        help="Retoma erros técnicos, até três tentativas por consulta.",
    )
    parser.add_argument(
        "--limit-queries", type=int, help="Limita consultas novas, preservando retomada."
    )
    args = parser.parse_args(argv)
    if args.status:
        for path in [WORKSPACE / "progress.json", SUPPLEMENT / "progress.json"]:
            print(
                path.read_text(encoding="utf-8")
                if path.exists()
                else f"Ainda não iniciado: {path.parent.name}"
            )
        return 0
    if args.limit_queries is not None and args.limit_queries < 1:
        parser.error("--limit-queries precisa ser positivo.")
    try:
        result = run(retry=args.retry_errors, limit=args.limit_queries)
    except KeyboardInterrupt:
        print(
            "Interrompido; retome com o mesmo comando. Checkpoints e índices preservados.",
            file=sys.stderr,
        )
        return 2
    return 0 if result["completed"] else 2
