"""Revisão de textos concorrentes equivalentes após uniformização de caixa."""

import argparse
import hashlib
import json
import sqlite3
import time
from contextlib import ExitStack, closing
from pathlib import Path

import polars as pl

from . import lyrics_matching_revision as revision
from . import new_sample_local as local
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

VERSION = "nova-amostra-caixa-v1"
WORKSPACE = design.ROOT / "data/derived/private_revisao_caixa_nova_amostra_v1"
OUTPUT = design.ROOT / "reports/revisao_caixa_nova_amostra_v1"
TARGET = "status='ambiguous' AND json_extract(result,'$.reason')='substantively_distinct_texts'"


def compare_case(query, candidates, incomplete):
    baseline, _ = revision.classify(query, candidates, incomplete)
    if baseline.get("reason") != "substantively_distinct_texts":
        return {"outcome": "outside_case_revision", "current_reason": baseline.get("reason")}, None

    texts = {}
    for candidate in candidates:
        if not revision.compatible(query, candidate):
            continue
        plain, synced = candidate.get("plainLyrics"), candidate.get("syncedLyrics")
        text = plain if plain and plain.strip() else None
        if text is None and synced:
            text, error = local.recovery.synced_text(synced)
            require(error is None, "Formato LRC diverge da classificação de origem.")
        if not text or not text.strip():
            continue
        texts[candidate["id"]] = {
            "text": text,
            "candidate": candidate,
            "diagnostics": {
                "duration_difference_seconds": local.recovery.duration_delta(query, candidate)
            },
            "endpoints": ["sqlite"],
            "candidate_key_sha256": fingerprint(candidate["id"]),
        }
    signatures = {
        local.recovery.typography_hash(" ".join(item["text"].lower().split()))
        for item in texts.values()
    }
    if len(texts) < 2 or len(signatures) != 1:
        return {
            "outcome": "different_after_case_normalization",
            "distinct_signatures": len(signatures),
        }, None

    item = min(texts.values(), key=local.recovery._representative_sort_key)
    chosen = item["candidate"]
    text = item["text"]
    lyric = {
        "accepted_text": text,
        "plain_text_source": chosen.get("plainLyrics"),
        "synced_text_source": chosen.get("syncedLyrics"),
        "lrclib_id": chosen["id"],
        "lrclib_lyrics_id": chosen.get("local_lyrics_id"),
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "strict_text_sha256": local.cache.strict_plain_text_metrics(text)["strict_text_sha256"],
        "rules_version": VERSION,
    }
    result = {
        "outcome": "accepted_case_equivalent",
        "equivalent_candidate_ids": sorted(texts),
        "comparison_sha256": next(iter(signatures)),
    }
    return result, lyric


def run(
    *,
    source_workspace=revision.WORKSPACE,
    source_summary=revision.OUTPUT / "resumo_revisao_matching.json",
    source42_workspace=local.WORKSPACE,
    dump=local.DUMP,
    primary=local.PRIMARY,
    supplement=local.SUPPLEMENT,
    recovery_state=local.recovery.WORKSPACE / "state.sqlite",
    workspace=WORKSPACE,
    output=OUTPUT,
    limit=None,
):
    require(
        workspace.resolve() not in {source_workspace.resolve(), source42_workspace.resolve()},
        "Use uma pasta própria para a revisão.",
    )
    summary = design.read_json(source_summary)
    require(summary["completed"], "Revisão 43 incompleta.")
    require(
        summary["seal"]["code_sha256"] == design.sha256(Path(revision.__file__)),
        "Código de origem alterado.",
    )
    for name, value in summary["private_sha256"].items():
        require(design.sha256(source_workspace / name) == value, f"Resultado 43 alterado: {name}")
    identity, artists, index_info = local.primary_metadata(dump, primary, recovery_state)
    require(
        identity == summary["seal"]["dump"] and index_info == summary["seal"]["primary"],
        "Índice ou dump difere de 43.",
    )
    source_path = source_workspace / "state.sqlite"
    source_stamp = local.cache.stamp(source_path)
    source42_path = source42_workspace / "state.sqlite"
    require(
        design.sha256(source42_path) == summary["seal"]["state42_sha256"],
        "Estado 42 difere da origem registrada.",
    )
    seal = {
        "version": VERSION,
        "code_sha256": design.sha256(Path(__file__)),
        "source_summary_sha256": design.sha256(source_summary),
        "source_state_sha256": design.sha256(source_path),
        "dump": identity,
        "primary": index_info,
    }
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with exclusive(workspace), ExitStack() as stack:
        old = stack.enter_context(closing(local.base.stable_readonly(source_path)))
        old42 = stack.enter_context(closing(local.base.stable_readonly(source42_path)))
        source = stack.enter_context(closing(local.base.stable_readonly(dump)))
        index = stack.enter_context(closing(local.base.stable_readonly(primary)))
        extra_artists = set(meta_get(old42, "extra_artists", []))
        additional = None
        if extra_artists:
            additional_path = supplement / "lookup.sqlite"
            additional = stack.enter_context(closing(local.base.stable_readonly(additional_path)))
            expected = summary["seal"]["supplement"]
            require(meta_get(additional, "progress")["complete"], "Complemento incompleto.")
            require(
                meta_get(additional, "seal") == expected["seal"]
                and local.cache.stamp(additional_path) == expected["stamp"],
                "Complemento difere de 43.",
            )
            require(
                fingerprint(sorted(extra_artists)) == expected["seal"]["artists"],
                "Universo do complemento alterado.",
            )
            seal["supplement"] = expected

        targets = dict(
            old.execute(f"SELECT query_id,data FROM queries WHERE {TARGET} ORDER BY query_id")
        )
        require(bool(targets), "Nenhuma ambiguidade textual elegível.")
        tracks = {}
        for track_id, query_id in old.execute(
            f"SELECT track_id,query_id FROM tracks JOIN queries USING(query_id) WHERE {TARGET}"
        ):
            tracks.setdefault(query_id, []).append(track_id)
        require(set(tracks) == set(targets), "Consultas sem vínculo ao sorteio.")
        db = stack.enter_context(closing(sqlite3.connect(workspace / "state.sqlite")))
        db.executescript("""
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS decisions(query_id TEXT PRIMARY KEY,result TEXT NOT NULL,lyric TEXT);
        """)
        if meta_get(db, "seal") is None:
            require(
                db.execute("SELECT count(*) FROM decisions").fetchone()[0] == 0,
                "Checkpoint sem selo.",
            )
            with db:
                meta_put(db, "seal", seal)
        else:
            require(meta_get(db, "seal") == seal, "Fontes ou código alterados desde o checkpoint.")
        stored = {key for (key,) in db.execute("SELECT query_id FROM decisions")}
        require(stored <= set(targets), "Checkpoint inclui consultas fora da revisão.")
        jobs = [key for key in targets if key not in stored][:limit]
        print(
            f"Revisão de caixa em {len(jobs)} consultas. {len(stored)} resultados reaproveitados do checkpoint.",
            flush=True,
        )
        last = 0.0
        for number, key in enumerate(jobs, start=1):
            query = json.loads(targets[key])
            require(fingerprint(query) == key, "Consulta alterada.")
            artist = local.recovery.profile(query["artist_name_query"], query["track_name_query"])[
                "artist"
            ]
            require(
                artist in artists or (artist in extra_artists and additional is not None),
                "Consulta fora dos índices conferidos.",
            )
            candidates, incomplete = local.recovery.lookup(
                source, index if artist in artists else additional, query
            )
            result, lyric = compare_case(query, candidates, incomplete)
            with db:
                db.execute(
                    "INSERT INTO decisions VALUES (?,?,?)",
                    (
                        key,
                        json.dumps(result),
                        json.dumps(lyric, ensure_ascii=False) if lyric else None,
                    ),
                )
            if time.monotonic() - last >= 10:
                atomic_json(
                    workspace / "progress.json",
                    {"concluidas": len(stored) + number, "total": len(targets)},
                )
                print(f"{len(stored) + number}/{len(targets)} consultas revisadas.", flush=True)
                last = time.monotonic()

        require(
            local.cache.stamp(source_path) == source_stamp, "Estado 43 alterado durante a revisão."
        )
        require(local.cache.stamp(primary) == index_info["stamp"], "Índice principal alterado.")
        require(
            local.recovery.local.checked_dump(dump) == identity, "Dump alterado durante a revisão."
        )
        if extra_artists:
            require(
                local.cache.stamp(supplement / "lookup.sqlite") == seal["supplement"]["stamp"],
                "Complemento alterado.",
            )
        counts, lyrics, links = {}, [], []
        for key, raw_result, raw_lyric in db.execute(
            "SELECT query_id,result,lyric FROM decisions ORDER BY query_id"
        ):
            decision = json.loads(raw_result)
            outcome = decision["outcome"]
            counts[outcome] = counts.get(outcome, 0) + 1
            if raw_lyric:
                lyric = json.loads(raw_lyric)
                lyrics.append({"query_id": key, **lyric})
                links.extend({"track_id": track_id, "query_id": key} for track_id in tracks[key])
        lyric_schema = {
            "query_id": pl.String,
            "accepted_text": pl.String,
            "plain_text_source": pl.String,
            "synced_text_source": pl.String,
            "lrclib_id": pl.Int64,
            "lrclib_lyrics_id": pl.Int64,
            "text_sha256": pl.String,
            "strict_text_sha256": pl.String,
            "rules_version": pl.String,
        }
        atomic_frame(
            workspace / "novas_letras_aceitas.parquet", pl.DataFrame(lyrics, schema=lyric_schema)
        )
        atomic_frame(
            workspace / "novos_vinculos.parquet",
            pl.DataFrame(links, schema={"track_id": pl.String, "query_id": pl.String}),
        )
        completed = sum(counts.values()) == len(targets)
        report = {
            "completed": completed,
            "targets": len(targets),
            "outcomes": counts,
            "previous_accepted_tracks": summary["status_counts"]["accepted"],
            "new_accepted_tracks": len(links),
            "accepted_tracks_with_overlay": summary["status_counts"]["accepted"] + len(links),
            "new_accepted_queries": len(lyrics),
            "seconds": time.monotonic() - started,
            "seal": seal,
            "private_sha256": {
                name: design.sha256(workspace / name)
                for name in ["novas_letras_aceitas.parquet", "novos_vinculos.parquet"]
            },
        }
        atomic_json(output / "resumo_revisao_caixa.json", report)
        atomic_json(
            workspace / "progress.json",
            {"concluidas": sum(counts.values()), "total": len(targets), "completed": completed},
        )
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "completed",
                    "targets",
                    "new_accepted_tracks",
                    "accepted_tracks_with_overlay",
                )
            }
        ),
        flush=True,
    )
    return report


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", action="store_true", help="Lê o progresso local.")
    parser.add_argument("--limit-queries", type=int, help="Limita o lote desta execução.")
    args = parser.parse_args(argv)
    if args.status:
        path = WORKSPACE / "progress.json"
        print(path.read_text(encoding="utf-8") if path.exists() else "Revisão ainda não iniciada.")
        return 0
    if args.limit_queries is not None and args.limit_queries < 1:
        parser.error("O limite deve ser positivo.")
    try:
        result = run(limit=args.limit_queries)
    except KeyboardInterrupt:
        print("Interrompido. Repita o comando para retomar as consultas restantes.")
        return 2
    return 0 if result["completed"] else 2
