"""Aplica a elegibilidade antes do teto textual nos casos barrados por volume."""

import argparse
import json
import sqlite3
import time
from collections import Counter
from contextlib import ExitStack, closing
from pathlib import Path

import polars as pl

from . import lyrics_artist_review as artist
from . import lyrics_online_pilot as online
from .manual_lyrics import (
    atomic_frame,
    atomic_json,
    exclusive,
    fingerprint,
    meta_get,
    meta_put,
    require,
)

local, design, revision, recovery = artist.local, artist.design, artist.revision, artist.recovery
VERSION = "nova-amostra-metadados-antes-do-limite-v1"
WORKSPACE = design.ROOT / "data/derived/private_revisao_limites_nova_amostra_v1"
OUTPUT = design.ROOT / "reports/revisao_limites_nova_amostra_v1"
TARGET = (
    "q.status='ambiguous' AND json_extract(q.result,'$.reason')='operational_limit:candidate_limit'"
)
METADATA_LIMIT, TIME_LIMIT = 2500, 30
SQL = """
SELECT id,name,artist_name,album_name,duration,last_lyrics_id
FROM catalog WHERE artist_key=? AND title_key=? ORDER BY id LIMIT ?
"""


def lookup(dump, index, query):
    profile = recovery.profile(query["artist_name_query"], query["track_name_query"])
    deadline = time.monotonic() + TIME_LIMIT
    for db in (dump, index):
        db.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
    try:
        rows = index.execute(
            SQL, (profile["artist"], profile["title"], METADATA_LIMIT + 1)
        ).fetchall()
        details = {"metadata_rows": len(rows)}
        if len(rows) > METADATA_LIMIT:
            return {**details, "outcome": "limite_de_metadados"}, None
        candidates = []
        for identifier, title, name, album, duration, lyric_id in rows:
            candidate = {
                "id": identifier,
                "trackName": title,
                "artistName": name,
                "albumName": album,
                "duration": duration,
                "local_lyrics_id": lyric_id,
            }
            if revision.compatible(query, candidate):
                candidates.append(candidate)
        details["compatible"] = len(candidates)
        if len(candidates) > recovery.local.MAX_CANDIDATES:
            return {**details, "outcome": "limite_de_candidatos_compativeis"}, None
        if not candidates:
            return {**details, "outcome": "sem_candidato_compativel"}, None
        total = 0
        for candidate in candidates:
            if time.monotonic() >= deadline:
                raise TimeoutError
            text = (None, None, False)
            identifier = candidate["local_lyrics_id"]
            if identifier is not None:
                sizes = dump.execute(
                    "SELECT track_id,length(plain_lyrics),length(synced_lyrics) FROM lyrics WHERE id=?",
                    (identifier,),
                ).fetchone()
                require(
                    sizes is not None and sizes[0] == candidate["id"],
                    "Referência LRCLIB divergente.",
                )
                chars = (sizes[1] or 0) + (sizes[2] or 0)
                total += chars
                if (
                    chars > recovery.local.MAX_TEXT_CHARACTERS
                    or total > recovery.local.MAX_TOTAL_CHARACTERS
                ):
                    return {**details, "outcome": "limite_de_texto"}, None
                text = dump.execute(
                    "SELECT plain_lyrics,synced_lyrics,instrumental FROM lyrics WHERE id=?",
                    (identifier,),
                ).fetchone()
            candidate.update(plainLyrics=text[0], syncedLyrics=text[1], instrumental=bool(text[2]))
        outcome, lyric = artist.review_text(query, candidates)
        if lyric is not None:
            outcome = "accepted_after_metadata_filter"
            lyric["rules_version"] = VERSION
            details["selected_lrclib_id"] = lyric["lrclib_id"]
        return {**details, "outcome": outcome}, lyric
    except (TimeoutError, sqlite3.OperationalError) as exc:
        if isinstance(exc, sqlite3.OperationalError) and "interrupted" not in str(exc).lower():
            raise
        return {"outcome": "limite_de_tempo"}, None
    finally:
        for db in (dump, index):
            db.set_progress_handler(None, 0)


def run():
    prior_path = artist.OUTPUT / "resumo_revisao_variantes_artista.json"
    online_path = online.OUTPUT / "resumo_piloto_online.json"
    s43_path = revision.OUTPUT / "resumo_revisao_matching.json"
    prior, pilot, s43 = map(design.read_json, (prior_path, online_path, s43_path))
    old_path = revision.WORKSPACE / "state.sqlite"
    old42_path = local.WORKSPACE / "state.sqlite"
    additional = local.SUPPLEMENT / "lookup.sqlite"
    identity, artists, index_info = local.primary_metadata(
        local.DUMP, local.PRIMARY, recovery.WORKSPACE / "state.sqlite"
    )
    seal = {
        "version": VERSION,
        "code_sha256": design.sha256(Path(__file__)),
        "state43_sha256": design.sha256(old_path),
        "summary43_sha256": design.sha256(s43_path),
        "summary48_sha256": design.sha256(prior_path),
        "summary49_sha256": design.sha256(online_path),
        "dump": identity,
        "primary": index_info,
        "supplement": s43["seal"]["supplement"],
    }
    require(
        s43["completed"]
        and prior["completed"]
        and pilot["completed"]
        and pilot["new_confirmed_tracks"] == 0
        and identity == s43["seal"]["dump"] == prior["seal"]["dump"]
        and index_info == s43["seal"]["primary"]
        and seal["state43_sha256"] == prior["seal"]["source43_state_sha256"]
        and design.sha256(old42_path) == s43["seal"]["state42_sha256"],
        "Fontes locais divergentes.",
    )
    with exclusive(WORKSPACE), ExitStack() as stack:
        old = stack.enter_context(closing(local.base.stable_readonly(old_path)))
        old42 = stack.enter_context(closing(local.base.stable_readonly(old42_path)))
        dump = stack.enter_context(closing(local.base.stable_readonly(local.DUMP)))
        primary = stack.enter_context(closing(local.base.stable_readonly(local.PRIMARY)))
        supplement = stack.enter_context(closing(local.base.stable_readonly(additional)))
        extra = set(meta_get(old42, "extra_artists", []))
        require(
            meta_get(supplement, "progress")["complete"]
            and local.cache.stamp(additional) == seal["supplement"]["stamp"]
            and meta_get(supplement, "seal") == seal["supplement"]["seal"]
            and fingerprint(sorted(extra)) == seal["supplement"]["seal"]["artists"],
            "Complemento do índice divergente.",
        )
        targets = dict(
            old.execute(f"SELECT query_id,data FROM queries q WHERE {TARGET} ORDER BY query_id")
        )
        require(bool(targets), "Nenhuma consulta com limite de candidatos.")
        tracks = {}
        for track, key in old.execute(
            f"SELECT track_id,query_id FROM tracks JOIN queries q USING(query_id) WHERE {TARGET}"
        ):
            tracks.setdefault(key, []).append(track)
        require(set(tracks) == set(targets), "Alvos sem vínculo com a amostra.")
        db = stack.enter_context(closing(sqlite3.connect(WORKSPACE / "state.sqlite")))
        db.executescript("""
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS decisions(query_id TEXT PRIMARY KEY,result TEXT NOT NULL,lyric TEXT);
        """)
        stored = {key for (key,) in db.execute("SELECT query_id FROM decisions")}
        if meta_get(db, "seal") is None:
            require(not stored, "Checkpoint sem selo.")
            with db:
                meta_put(db, "seal", seal)
        require(meta_get(db, "seal") == seal and stored <= targets.keys(), "Checkpoint divergente.")
        print(
            f"Revisão local de {len(targets)} consultas. {len(stored)} reaproveitadas.", flush=True
        )
        for key in sorted(targets.keys() - stored):
            query = json.loads(targets[key])
            require(fingerprint(query) == key, "Consulta alterada.")
            name = recovery.profile(query["artist_name_query"], query["track_name_query"])["artist"]
            require(name in artists or name in extra, "Artista fora dos índices selados.")
            result, lyric = lookup(dump, primary if name in artists else supplement, query)
            with db:
                db.execute(
                    "INSERT INTO decisions VALUES (?,?,?)",
                    (
                        key,
                        json.dumps(result),
                        json.dumps(lyric, ensure_ascii=False) if lyric else None,
                    ),
                )
            stored.add(key)
            if len(stored) % 10 == 0:
                print(f"{len(stored)}/{len(targets)} consultas concluídas.", flush=True)
        require(
            local.cache.stamp(local.PRIMARY) == index_info["stamp"]
            and local.cache.stamp(additional) == seal["supplement"]["stamp"]
            and recovery.local.checked_dump(local.DUMP) == identity,
            "Fonte alterada durante a revisão.",
        )
        counts, texts, links = Counter(), [], []
        for key, raw_result, raw_lyric in db.execute(
            "SELECT query_id,result,lyric FROM decisions ORDER BY query_id"
        ):
            counts[json.loads(raw_result)["outcome"]] += len(tracks[key])
            if raw_lyric:
                texts.append({"query_id": key, **json.loads(raw_lyric)})
                links.extend({"track_id": track, "query_id": key} for track in tracks[key])
        atomic_frame(
            WORKSPACE / "novas_letras_aceitas.parquet",
            pl.DataFrame(texts, schema=artist.synced.LYRIC_SCHEMA),
        )
        atomic_frame(
            WORKSPACE / "novos_vinculos.parquet",
            pl.DataFrame(links, schema={"track_id": pl.String, "query_id": pl.String}),
        )
        report = {
            "completed": True,
            "targets": len(targets),
            "outcomes_by_track": dict(counts),
            "new_accepted_tracks": len(links),
            "new_accepted_queries": len(texts),
            "accepted_tracks_with_overlays": prior["accepted_tracks_with_overlays"] + len(links),
            "seal": seal,
            "private_sha256": {
                name: design.sha256(WORKSPACE / name)
                for name in (
                    "state.sqlite",
                    "novas_letras_aceitas.parquet",
                    "novos_vinculos.parquet",
                )
            },
        }
        atomic_json(OUTPUT / "resumo_revisao_limites.json", report)
    return report


def cli(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    try:
        report = run()
    except KeyboardInterrupt:
        print("Interrompido. Repita o comando para retomar as consultas pendentes.")
        return 2
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "completed",
                    "targets",
                    "new_accepted_tracks",
                    "accepted_tracks_with_overlays",
                    "outcomes_by_track",
                )
            }
        )
    )
    return 0
