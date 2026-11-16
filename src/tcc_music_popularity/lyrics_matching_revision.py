"""Revisão dirigida de dois bloqueios, sem alterar faixas ou resultados anteriores."""

import argparse
import json
import sqlite3
import sys
import time
from contextlib import ExitStack, closing
from pathlib import Path

import polars as pl

from . import new_sample_local as local
from . import sample_cache_reuse as cache
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

recovery = local.recovery
base = local.base
ROOT = design.ROOT
VERSION = "nova-amostra-matching-v2"
WORKSPACE = ROOT / "data/derived/private_nova_amostra_matching_v2"
OUTPUT = ROOT / "reports/revisao_matching_nova_amostra_v2"


def whitespace_equal(left, right):
    """Igualdade exata após tipografia existente e uniformização de whitespace."""
    return recovery.typography_hash(" ".join(left.split())) == recovery.typography_hash(
        " ".join(right.split())
    )


def compatible(query, candidate):
    q = recovery.profile(query["artist_name_query"], query["track_name_query"])
    c = recovery.profile(candidate.get("artistName"), candidate.get("trackName"))
    delta = recovery.duration_delta(query, candidate)
    return (
        not q["credit_conflict"]
        and not c["credit_conflict"]
        and all(q[k] == c[k] for k in ("artist", "title", "guests", "versions"))
        and (delta is None or delta <= base.TOLERANCE)
    )


def classify(query, candidates, incomplete=None):
    require(set(query) <= base.MATCH_FIELDS, "Campo proibido na vinculação.")
    raw = {}
    for candidate in candidates:
        if candidate["id"] in raw and raw[candidate["id"]] != candidate:
            return recovery.classify(query, candidates, incomplete)
        raw[candidate["id"]] = candidate
    eligible = [c for c in candidates if compatible(query, c)]
    # Sem candidato plenamente compatível, mantém a rejeição anterior.
    selected = eligible if eligible and not incomplete else candidates
    views, layout_ids = [], []
    for candidate in selected:
        view = dict(candidate)
        plain, synced = candidate.get("plainLyrics"), candidate.get("syncedLyrics")
        if plain and plain.strip() and synced:
            extracted, error = recovery.synced_text(synced)
            if error is None and whitespace_equal(plain, extracted):
                # O texto principal continua intacto. A representação sincronizada
                # já foi verificada como redundante; conserva-se o original abaixo.
                view["syncedLyrics"] = None
                layout_ids.append(candidate["id"])
        views.append(view)
    result, lyric = recovery.classify(
        query, views, incomplete, origin="controlled_lookup_layout_revision"
    )
    result.update(
        rules_version=VERSION,
        candidate_count=len(candidates) if not incomplete else None,
        layout_equivalent_ids=sorted(set(layout_ids)),
        incompatible_candidates_excluded=len(candidates) - len(selected),
        plain_present=any(bool(c.get("plainLyrics")) for c in selected),
        synced_present=any(bool(c.get("syncedLyrics")) for c in selected),
        new_sample_origin="targeted_matching_revision",
    )
    if lyric:
        original = raw[lyric["lrclib_id"]]
        lyric.update(
            source_plain_original=original.get("plainLyrics"),
            synced_text_source=original.get("syncedLyrics"),
            rules_version=VERSION,
        )
        local.check_text(lyric, result)
    return result, lyric


def needs_revision(status, result):
    return status == "ambiguous" and (
        result.get("reason") == "plain_synced_conflict"
        or (
            result.get("reason") == "positive_version_conflict"
            and result.get("eligible_count", 0) > 0
        )
    )


def initialize(db, old, seal):
    exists = db.execute("SELECT 1 FROM sqlite_schema WHERE name='meta'").fetchone()
    if exists and meta_get(db, "seal") is not None:
        require(meta_get(db, "seal") == seal, "Código/fontes alterados; preservar checkpoint.")
        return
    if not exists:
        require(
            not db.execute("SELECT 1 FROM sqlite_schema WHERE type='table'").fetchone(),
            "Workspace desconhecido.",
        )
        db.executescript("BEGIN IMMEDIATE;" + base.STATE_SQL + "COMMIT;")
    else:
        for table in ("queries", "lyrics", "tracks", "evidence"):
            require(
                db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0,
                "Checkpoint não vazio sem selo.",
            )
    targets = []
    with db:
        for key, data, status, raw in old.execute(
            "SELECT query_id,data,status,result FROM queries"
        ):
            result = json.loads(raw) if raw else {}
            target = needs_revision(status, result)
            if target:
                targets.append(key)
                db.execute("INSERT INTO queries(query_id,data) VALUES (?,?)", (key, data))
            else:
                result["new_sample_origin"] = "preserved_local_42"
                db.execute(
                    "INSERT INTO queries(query_id,data,status,result) VALUES (?,?,?,?)",
                    (key, data, status, json.dumps(result, ensure_ascii=False)),
                )
                if status == "accepted":
                    row = old.execute("SELECT data FROM lyrics WHERE query_id=?", (key,)).fetchone()
                    require(row is not None, "Letra anterior ausente.")
                    local.check_text(json.loads(row[0]), result)
                    db.execute("INSERT INTO lyrics VALUES (?,?)", (key, row[0]))
            db.execute(
                "INSERT INTO evidence VALUES (?,?)",
                (
                    key,
                    json.dumps(
                        {
                            "origin": "stage42_reference",
                            "query_id": key,
                            "source_state_sha256": seal["state42_sha256"],
                            "revision_target": target,
                        }
                    ),
                ),
            )
        db.executemany(
            "INSERT INTO tracks VALUES (?,?)", old.execute("SELECT track_id,query_id FROM tracks")
        )
        meta_put(db, "targets", sorted(targets))
        meta_put(db, "seal", seal)


def run(
    *,
    sample=local.SAMPLE,
    source_workspace=local.WORKSPACE,
    source_summary=local.OUTPUT / "resumo_busca_local.json",
    dump=local.DUMP,
    primary=local.PRIMARY,
    supplement=local.SUPPLEMENT,
    recovery_state=recovery.WORKSPACE / "state.sqlite",
    workspace=WORKSPACE,
    output=OUTPUT,
    retry=False,
    limit=None,
):
    (
        sample,
        source_workspace,
        source_summary,
        dump,
        primary,
        supplement,
        recovery_state,
        workspace,
        output,
    ) = map(
        Path,
        [
            sample,
            source_workspace,
            source_summary,
            dump,
            primary,
            supplement,
            recovery_state,
            workspace,
            output,
        ],
    )
    require(workspace.resolve() != source_workspace.resolve(), "Revisão exige pasta separada.")
    print("[1/4] Preservando 42 e conferindo índices existentes; sem reconstrução...", flush=True)
    prior = design.read_json(source_summary)
    require(prior["completed"], "Etapa 42 não concluída.")
    require(
        design.sha256(Path(local.__file__)) == prior["seal"]["code_sha256"],
        "Código 42 selado mudou.",
    )
    require(design.sha256(sample) == prior["seal"]["sample_sha256"], "Amostra alterada.")
    for name, value in prior["private_sha256"].items():
        require(design.sha256(source_workspace / name) == value, "Resultado 42 alterado: " + name)
    identity, artists, index_info = local.primary_metadata(dump, primary, recovery_state)
    require(
        identity == prior["seal"]["dump"] and index_info == prior["seal"]["primary"],
        "Índice/dump não corresponde a 42.",
    )
    source_state = source_workspace / "state.sqlite"
    state_stamp = cache.stamp(source_state)
    seal = {
        "version": VERSION,
        "code_sha256": design.sha256(Path(__file__)),
        "summary42_sha256": design.sha256(source_summary),
        "state42_sha256": design.sha256(source_state),
        "sample_sha256": prior["seal"]["sample_sha256"],
        "dump": identity,
        "primary": index_info,
    }
    sample_frame = pl.read_parquet(sample)
    previous = pl.read_parquet(source_workspace / "resultados_faixas.parquet")
    require(previous.select(sample_frame.columns).equals(sample_frame), "Amostra de 42 divergente.")
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with exclusive(workspace), ExitStack() as stack:
        old = stack.enter_context(closing(base.stable_readonly(source_state)))
        extra = set(meta_get(old, "extra_artists", []))
        index = stack.enter_context(closing(base.stable_readonly(primary)))
        additional = None
        if extra:
            additional = stack.enter_context(
                closing(base.stable_readonly(supplement / "lookup.sqlite"))
            )
            require(
                meta_get(additional, "progress")["complete"], "Complemento anterior incompleto."
            )
            expected = {
                "dump": identity,
                "artists": fingerprint(sorted(extra)),
                "rules": design.sha256(Path(recovery.__file__)),
            }
            require(
                meta_get(additional, "seal") == expected,
                "Complemento não corresponde ao universo de 42.",
            )
            seal["supplement"] = {
                "seal": expected,
                "stamp": cache.stamp(supplement / "lookup.sqlite"),
            }
        source = stack.enter_context(closing(base.stable_readonly(dump)))
        db = stack.enter_context(closing(base.state_connection(workspace)))
        initialize(db, old, seal)
        expected_queries, expected_tracks = recovery.make_queries(sample_frame)
        require(
            dict(db.execute("SELECT track_id,query_id FROM tracks")) == dict(expected_tracks),
            "Vínculos fora da amostra.",
        )
        for key, raw in db.execute("SELECT query_id,data FROM queries"):
            require(
                key in expected_queries and json.loads(raw) == expected_queries[key],
                "Consulta incompatível com a amostra.",
            )
        condition = (
            "status='pending' OR (status='technical_error' AND attempts<3)"
            if retry
            else "status='pending'"
        )
        jobs = db.execute(
            f"SELECT query_id,data FROM queries WHERE {condition} ORDER BY query_id LIMIT ?",
            (limit if limit is not None else -1,),
        ).fetchall()
        print(
            f"[2/4] {len(jobs)} consultas dirigidas; texto original e critérios de artista/duração preservados...",
            flush=True,
        )
        last = 0.0
        for number, (key, raw) in enumerate(jobs, start=1):
            query = json.loads(raw)
            artist = recovery.profile(query["artist_name_query"], query["track_name_query"])[
                "artist"
            ]
            with db:
                db.execute("UPDATE queries SET attempts=attempts+1 WHERE query_id=?", (key,))
            try:
                covered = artist in artists
                require(
                    covered or (artist in extra and additional is not None),
                    "Artista sem cobertura completa.",
                )
                candidates, incomplete = recovery.lookup(
                    source, index if covered else additional, query
                )
                result, lyric = classify(query, candidates, incomplete)
                if lyric:
                    lyric.update(query_id=key, source_dump=identity)
                evidence = local.evidence_metadata(
                    query,
                    candidates,
                    identity,
                    primary if covered else supplement / "lookup.sqlite",
                    incomplete,
                )
                evidence["rules_version"] = VERSION
                with db:
                    db.execute(
                        "UPDATE queries SET status=?,result=? WHERE query_id=?",
                        (result["status"], json.dumps(result, ensure_ascii=False), key),
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
                                    "rules_version": VERSION,
                                }
                            ),
                            key,
                        ),
                    )
            if time.monotonic() - last >= 10:
                progress = {
                    "etapa": "revisao_matching",
                    "novas_consultas": number,
                    "restantes_nesta_execucao": len(jobs) - number,
                    "segundos": time.monotonic() - started,
                }
                print(json.dumps(progress), flush=True)
                atomic_json(workspace / "progress.json", progress)
                last = time.monotonic()
        print(
            "[3/4] Conferindo preservação das aceitas/instrumentais e exportando revisão separada...",
            flush=True,
        )
        require(cache.stamp(source_state) == state_stamp, "Checkpoint 42 mudou durante a revisão.")
        require(cache.stamp(primary) == index_info["stamp"], "Índice principal alterado.")
        require(recovery.local.checked_dump(dump) == identity, "Dump alterado durante a revisão.")
        if extra:
            require(
                cache.stamp(supplement / "lookup.sqlite") == seal["supplement"]["stamp"],
                "Complemento alterado.",
            )
        final, n_texts = local.export(db, sample_frame, previous, workspace)
        final = final.rename({"cache41_lyrics_status": "local42_lyrics_status"})
        atomic_frame(workspace / "resultados_faixas.parquet", final)
        atomic_frame(
            workspace / "pendencias_revisao.parquet",
            final.filter(~pl.col("lyrics_status").is_in(["accepted", "instrumental"])),
        )
        cache.publish(final, output)
        (output / "status_cache.csv").replace(output / "status_revisao.csv")
        (output / "cobertura_cache.csv").replace(output / "cobertura_revisao.csv")
        final.group_by("local42_lyrics_status", "lyrics_status").agg(pl.len().alias("n")).write_csv(
            output / "transicoes_status.csv"
        )
        statuses = {s: final.filter(pl.col("lyrics_status") == s).height for s in base.STATUSES}
        complete = statuses["pending"] == statuses["technical_error"] == 0
        summary = {
            "completed": complete,
            "version": VERSION,
            "sample_rows": final.height,
            "revision_targets": len(meta_get(db, "targets")),
            "new_queries_this_invocation": len(jobs),
            "status_counts": statuses,
            "accepted_queries": n_texts,
            "previous_status_counts": prior["status_counts"],
            "new_accepted_tracks": final.filter(
                (pl.col("local42_lyrics_status") != "accepted")
                & (pl.col("lyrics_status") == "accepted")
            ).height,
            "seal": seal,
            "seconds": time.monotonic() - started,
            "indices_built": 0,
            "http_requests": 0,
            "sample_replaced": False,
            "models_trained": False,
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
                for name in ["status_revisao.csv", "cobertura_revisao.csv", "transicoes_status.csv"]
            },
        }
        atomic_json(output / "resumo_revisao_matching.json", summary)
        atomic_json(
            workspace / "progress.json",
            {"etapa": "concluido" if complete else "parcial", "status_counts": statuses},
        )
    print(json.dumps({"etapa": "resumo_revisao", "status_por_faixa": statuses}), flush=True)
    print(
        f"[4/4] {'Concluído' if complete else 'Parcial; retomar'}; resultados em {output}",
        flush=True,
    )
    return summary


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", action="store_true", help="Lê somente o último progresso.")
    parser.add_argument(
        "--retry-errors", action="store_true", help="Retoma erros técnicos, até três tentativas."
    )
    parser.add_argument("--limit-queries", type=int, help="Limita consultas e preserva retomada.")
    args = parser.parse_args(argv)
    if args.status:
        path = WORKSPACE / "progress.json"
        print(path.read_text(encoding="utf-8") if path.exists() else "Revisão ainda não iniciada.")
        return 0
    if args.limit_queries is not None and args.limit_queries < 1:
        parser.error("Limite precisa ser positivo.")
    try:
        result = run(retry=args.retry_errors, limit=args.limit_queries)
    except KeyboardInterrupt:
        print("Interrompido; retome com o mesmo comando, preservando checkpoints.", file=sys.stderr)
        return 2
    return 0 if result["completed"] else 2
