"""Dump de nove linhas e checkpoints sintéticos; sem rede ou SSD real."""

import hashlib
import json
import socket
import sqlite3
from pathlib import Path

import polars as pl
import pytest

from tcc_music_popularity import new_sample_local as mod


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("Rede proibida nos testes")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(mod.recovery.local, "space", lambda *args: None)


def metadata(track, artist, title):
    return {
        "track_id": track,
        "artist_name": artist,
        "track_name": title,
        "duration_ms": "180000",
        "genre": "rock",
        "year": "2010",
        "popularity": "30",
        "_nova_peso": 10.0,
    }


def candidate(identifier, artist, title, text, instrumental=False, synced=None):
    return {
        "id": identifier,
        "artistName": artist,
        "trackName": title,
        "albumName": "Álbum sintético",
        "duration": 180.0,
        "plainLyrics": text,
        "syncedLyrics": synced,
        "instrumental": instrumental,
        "local_lyrics_id": identifier,
    }


def setup(tmp_path):
    dump_dir = tmp_path / "dump"
    dump_dir.mkdir()
    dump = dump_dir / "dump.sqlite"
    db = sqlite3.connect(dump)
    db.executescript("""
        CREATE TABLE tracks(id INTEGER PRIMARY KEY,name TEXT,artist_name TEXT,album_name TEXT,duration REAL,last_lyrics_id INTEGER);
        CREATE TABLE lyrics(id INTEGER PRIMARY KEY,track_id INTEGER,plain_lyrics TEXT,synced_lyrics TEXT,instrumental INTEGER);
    """)
    candidates = [
        candidate(1, "Known", "Cached", "Letra já aceita"),
        candidate(2, "Known", "Instrumental", None, True),
        candidate(3, "Known", "Existing", "Nova letra do índice existente"),
        candidate(4, "New", "Extra", None, synced="[00:01.00]Verso novo\n[00:02.00]Outra linha"),
        candidate(5, "Known", "Ambiguous", "Primeira letra"),
        candidate(6, "Known", "Ambiguous", "Segunda letra incompatível"),
        candidate(7, "Known", "No text", None),
        candidate(8, "Known", "Other - Live", "Versão ao vivo"),
        candidate(9, "Known", "Other", "Versão de estúdio"),
    ]
    for c in candidates:
        db.execute(
            "INSERT INTO tracks VALUES (?,?,?,?,?,?)",
            (c["id"], c["trackName"], c["artistName"], c["albumName"], c["duration"], c["id"]),
        )
        db.execute(
            "INSERT INTO lyrics VALUES (?,?,?,?,?)",
            (c["id"], c["id"], c["plainLyrics"], c["syncedLyrics"], c["instrumental"]),
        )
    db.commit()
    db.close()
    mod.atomic_json(
        dump_dir / "dump_progress.json",
        {
            "status": "ready",
            "sqlite_quick_check": "ok",
            "gzip_crc_verified": True,
            "database_path": str(dump.resolve()),
            "extracted_bytes": dump.stat().st_size,
            "database_sha256": mod.design.sha256(dump),
            "source": {"filename": "sintetico"},
        },
    )
    identity = mod.recovery.local.checked_dump(dump)
    primary_dir = tmp_path / "primary"
    mod.recovery.build_index(dump, primary_dir, ["known"], identity)
    recovery_state = tmp_path / "old_recovery.sqlite"
    db = sqlite3.connect(recovery_state)
    db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT)")
    mod.meta_put(db, "lookup_artists", ["known"])
    db.commit()
    db.close()
    rows = [
        metadata("a", "Known", "Cached"),
        metadata("b", "Known", "Instrumental"),
        metadata("c", "Known", "Existing"),
        metadata("d", "New", "Extra"),
        metadata("e", "Known", "Ambiguous"),
        metadata("f", "Known", "No text"),
        metadata("g", "Known", "Absent"),
        metadata("h", "Known", "Other - Live"),
        metadata("i", "Known", "Old negative"),
    ]
    sample = pl.DataFrame(rows)
    sample_path = tmp_path / "sample.parquet"
    sample.write_parquet(sample_path)
    source_workspace = tmp_path / "41"
    source_workspace.mkdir()
    state = sqlite3.connect(source_workspace / "state.sqlite")
    mod.cache.init_state(state, {"fixture": True}, {})
    queries, tracks = mod.recovery.make_queries(sample)
    for n, row in enumerate(rows):
        query = mod.recovery.recovery_query(
            {k: row[k] for k in ["track_id", "artist_name", "track_name", "duration_ms"]}
        )
        key = mod.fingerprint(query)
        lyric = None
        if n < 2:
            r, lyric = mod.recovery.classify(query, [candidates[n]], origin="controlled_lookup")
            value = {
                "status": r["status"],
                "reason": "exact_cached",
                "previous_result": r,
                "rules_version": mod.recovery.VERSION,
                "source_state": str(recovery_state.resolve()),
                "previous_status": r["status"],
            }
        elif n == 8:
            r, _ = mod.recovery.classify(query, [], origin="controlled_lookup")
            value = {
                "status": "pending_search",
                "reason": "historical_negative",
                "previous_result": r,
                "rules_version": mod.recovery.VERSION,
                "source_state": str(recovery_state.resolve()),
                "previous_status": r["status"],
            }
        else:
            value = {
                "status": "pending_search",
                "reason": "query_not_in_cache",
                "previous_result": {},
            }
        state.execute(
            "INSERT INTO decisions VALUES (?,?,?,?)",
            (key, json.dumps(query), json.dumps(value), json.dumps(lyric) if lyric else None),
        )
    state.commit()
    previous, _ = mod.cache.export_private(state, sample, tracks, source_workspace)
    state.close()
    source_summary = tmp_path / "summary41.json"
    mod.atomic_json(
        source_summary,
        {
            "concluido": True,
            "n_faixas": len(sample),
            "status_por_faixa": {
                "accepted": 1,
                "instrumental": 1,
                "pending_search": 7,
                "cache_error": 0,
                "insufficient_metadata": 0,
            },
            "fontes": {"sample_sha256": mod.design.sha256(sample_path), "code_hashes": {}},
            "arquivos_privados_sha256": {
                name: mod.design.sha256(source_workspace / name)
                for name in [
                    "resultados_faixas.parquet",
                    "letras_aceitas.parquet",
                    "pendencias_busca.parquet",
                ]
            },
        },
    )
    old_report = tmp_path / "old_report.json"
    mod.atomic_json(
        old_report,
        {
            "completed": True,
            "source": identity,
            "code_hashes": {"lyrics_recovery.py": mod.design.sha256(Path(mod.recovery.__file__))},
        },
    )
    return (
        {
            "sample": sample_path,
            "source_summary": source_summary,
            "source_workspace": source_workspace,
            "dump": dump,
            "primary": primary_dir / "lookup.sqlite",
            "recovery_state": recovery_state,
            "supplement": tmp_path / "extra",
            "workspace": tmp_path / "local",
            "output": tmp_path / "output",
            "previous_report": old_report,
        },
        sample,
        previous,
    )


def test_fluxo_completo_reutiliza_indice_cria_so_complemento_e_preserva_41(tmp_path):
    args, sample, previous = setup(tmp_path)
    primary_hash = mod.design.sha256(args["primary"])
    source_hash = mod.design.sha256(args["source_workspace"] / "state.sqlite")
    result = mod.run(**args)
    assert result["completed"] is True
    assert result["status_counts"]["accepted"] == 3
    assert result["status_counts"]["instrumental"] == 1
    assert result["status_counts"]["ambiguous"] == 2
    assert result["status_counts"]["no_text"] == 1
    assert result["status_counts"]["not_found"] == 2
    assert result["supplement_artists"] == 1
    assert result["new_queries_this_invocation"] == 6
    assert result["origins_query_counts"]["reused_controlled_negative"] == 1
    final = pl.read_parquet(args["workspace"] / "resultados_faixas.parquet")
    # Preserva a regra v2: conflito positivo entre versões não é aceitação nova.
    assert final.filter(pl.col("track_id") == "h")["lyrics_status"][0] == "ambiguous"
    assert final.select(sample.columns).equals(sample)
    assert final.filter(pl.col("track_id").is_in(["a", "b"]))["lyrics_status"].to_list() == [
        "accepted",
        "instrumental",
    ]
    lyrics = pl.read_parquet(args["workspace"] / "letras_aceitas.parquet")
    lrc = lyrics.filter(pl.col("lrclib_id") == 4)
    assert lrc["accepted_text"][0] == "Verso novo\nOutra linha"
    assert lrc["plain_text_source"][0] is None
    assert mod.design.sha256(args["primary"]) == primary_hash
    assert mod.design.sha256(args["source_workspace"] / "state.sqlite") == source_hash
    again = mod.run(**args)
    assert again["new_queries_this_invocation"] == 0
    assert again["private_sha256"] == result["private_sha256"]


def test_retoma_consultas_parciais_sem_mudar_lista_complementar(tmp_path):
    args, _, _ = setup(tmp_path)
    partial = mod.run(**args, limit=1)
    assert partial["completed"] is False
    assert partial["status_counts"]["pending"] == 5
    complete = mod.run(**args)
    assert complete["completed"] and complete["new_queries_this_invocation"] == 5
    assert complete["supplement_artists"] == 1


def test_nao_aceita_artista_sem_cobertura_e_reusa_so_negativas_controladas(tmp_path):
    source = tmp_path / "recovery.sqlite"
    value = {
        "source_state": str(source.resolve()),
        "previous_status": "not_found",
        "previous_result": {
            "status": "not_found",
            "rules_version": mod.recovery.VERSION,
            "method": "controlled_lookup",
            "operational_limit": False,
        },
    }
    assert mod.can_reuse_negative(value, source, {"fixture": True})
    for changed in [
        dict(value["previous_result"], method="cache"),
        dict(value["previous_result"], operational_limit=True),
        dict(value["previous_result"], rules_version="outra"),
    ]:
        assert not mod.can_reuse_negative(
            dict(value, previous_result=changed), source, {"fixture": True}
        )
    q = mod.recovery.recovery_query(
        {"track_id": "x", "artist_name": "Missing", "track_name": "Song", "duration_ms": "180000"}
    )
    db = sqlite3.connect(tmp_path / "own.sqlite")
    db.row_factory = sqlite3.Row
    db.executescript(mod.base.STATE_SQL)
    key = mod.fingerprint(q)
    db.execute("INSERT INTO queries(query_id,data) VALUES (?,?)", (key, json.dumps(q)))
    db.commit()
    mod.search(db, None, None, None, set(), set(), {"fixture": True})
    assert db.execute("SELECT status FROM queries").fetchone()[0] == "technical_error"
    assert db.execute("SELECT count(*) FROM lyrics").fetchone()[0] == 0
    db.close()


def test_evidencia_guarda_ids_hashes_sem_copiar_textos_rejeitados():
    c = candidate(1, "A", "B", "Texto privado sintético")
    value = mod.evidence_metadata({}, [c], {"fixture": True}, Path("sintetico.sqlite"), None)
    assert (
        value["candidates_metadata"][0]["plainLyrics_sha256"]
        == hashlib.sha256(c["plainLyrics"].encode()).hexdigest()
    )
    assert c["plainLyrics"] not in json.dumps(value)
