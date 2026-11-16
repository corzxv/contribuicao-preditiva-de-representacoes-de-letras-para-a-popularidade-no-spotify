"""Índices nativos em SQLite pequeno; diagnóstico sem letras ou aceitações."""

import json
import socket
import sqlite3
from pathlib import Path

import pytest

from tcc_music_popularity import native_lookup_audit as mod
from tcc_music_popularity.manual_lyrics import fingerprint


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("Rede proibida")

    monkeypatch.setattr(socket.socket, "connect", deny)


def query(title, artist, duration=180):
    return mod.local.recovery.recovery_query(
        {
            "track_id": "sintetico",
            "artist_name": artist,
            "track_name": title,
            "duration_ms": str(duration * 1000),
        }
    )


def fixture_dump(tmp_path):
    path = tmp_path / "dump.sqlite"
    db = sqlite3.connect(path)
    db.executescript("""
        CREATE TABLE tracks(id INTEGER PRIMARY KEY,name TEXT,name_lower TEXT,artist_name TEXT,artist_name_lower TEXT,album_name TEXT,duration REAL,last_lyrics_id INTEGER);
        CREATE INDEX idx_tracks_name_lower ON tracks(name_lower);
        CREATE INDEX idx_tracks_artist_name_lower ON tracks(artist_name_lower);
        CREATE VIRTUAL TABLE tracks_fts USING fts5(name_lower,album_name_lower,artist_name_lower);
    """)
    for ident, title, artist, duration in [
        (1, "Blonde Monster", "Secret and Whisper", 93.0),
        (2, "My Song", "Wrong Artist", 180.0),
        (3, "Another Title", "Known", 180.0),
        (4, "Song", "Many", 180.0),
        (5, "Song", "Many", 180.0),
        (6, "Song", "Many", 180.0),
    ]:
        db.execute(
            "INSERT INTO tracks VALUES (?,?,?,?,?,?,?,?)",
            (ident, title, title.lower(), artist, artist.lower(), "Álbum", duration, ident),
        )
        db.execute(
            "INSERT INTO tracks_fts(rowid,name_lower,album_name_lower,artist_name_lower) VALUES (?,?,?,?)",
            (ident, title.lower(), "álbum", artist.lower()),
        )
    db.commit()
    db.close()
    mod.atomic_json(
        tmp_path / "dump_progress.json",
        {
            "status": "ready",
            "sqlite_quick_check": "ok",
            "gzip_crc_verified": True,
            "database_path": str(path.resolve()),
            "extracted_bytes": path.stat().st_size,
            "database_sha256": mod.design.sha256(path),
            "source": {"filename": "sintetico"},
        },
    )
    return path


def test_alias_e_outro_artista_sao_apenas_indicios_sem_aceitacao(tmp_path):
    path = fixture_dump(tmp_path)
    with mod.local.base.stable_readonly(path) as source:
        plans = mod.validate_access(source)
        assert "VIRTUAL TABLE INDEX" in plans["fts"]
        result = mod.audit_query(source, query("Blonde Monster", "Secret & Whisper", 93))
        assert result["diagnostic_label"] == "artist_key_variant"
        assert result["flags"]["strict_profile_compatible"] is False
        assert result["new_acceptances"] == 0 and result["lyrics_read"] is False
        assert result["candidates"][0]["artist_name"] == "Secret and Whisper"
        result = mod.audit_query(source, query("My Song", "Desired Artist"))
        assert result["diagnostic_label"] == "same_title_other_artist"
        assert result["new_acceptances"] == 0
        result = mod.audit_query(source, query("Missing", "Known"))
        assert result["diagnostic_label"] == "same_artist_other_title"


def test_limites_e_sintaxe_fts_explicitos(tmp_path, monkeypatch):
    path = fixture_dump(tmp_path)
    with mod.local.base.stable_readonly(path) as source:
        monkeypatch.setattr(mod, "MAX_ROWS", 2)
        result = mod.audit_query(source, query("Song", "Many"))
        assert result["incomplete_methods"] is True
        assert result["new_acceptances"] == 0
        assert (
            mod.fts_expression('one" OR two', "Artist")
            == 'name_lower : "one or two" AND artist_name_lower : ("artist")'
        )
        assert mod.fts_expression(" ", "Artist") is None
        assert mod.fts_expression(" ".join(["word"] * 25), "Artist") is None
        monkeypatch.setattr(mod, "BUDGET_SECONDS", 0)
        result = mod.audit_query(source, query("Song", "Many"))
        assert result["incomplete_methods"] is True
        assert result["candidate_count_union_capped"] == 0


def test_checkpoint_parcial_retomada_sem_alterar_43(tmp_path):
    dump = fixture_dump(tmp_path)
    source_workspace = tmp_path / "old43"
    source_workspace.mkdir()
    state = source_workspace / "state.sqlite"
    db = sqlite3.connect(state)
    db.execute("CREATE TABLE queries(query_id TEXT PRIMARY KEY,data TEXT,status TEXT)")
    for title, artist, duration, status in [
        ("Blonde Monster", "Secret & Whisper", 93, "not_found"),
        ("My Song", "Desired Artist", 180, "not_found"),
        ("Accepted", "Other", 180, "accepted"),
    ]:
        q = query(title, artist, duration)
        db.execute("INSERT INTO queries VALUES (?,?,?)", (fingerprint(q), json.dumps(q), status))
    db.commit()
    db.close()
    source_hash = mod.design.sha256(state)
    summary = tmp_path / "summary43.json"
    mod.atomic_json(
        summary,
        {
            "completed": True,
            "private_sha256": {},
            "status_counts": {"accepted": 1},
            "seal": {
                "code_sha256": mod.design.sha256(Path(mod.revision.__file__)),
                "dump": mod.local.recovery.local.checked_dump(dump),
            },
        },
    )
    args = {
        "source_workspace": source_workspace,
        "source_summary": summary,
        "dump": dump,
        "workspace": tmp_path / "private_audit",
        "output": tmp_path / "public_audit",
    }
    partial = mod.run(**args, limit=1)
    assert partial["completed"] is False and partial["diagnosed"] == 1
    complete = mod.run(**args)
    assert complete["completed"] and complete["targets"] == complete["diagnosed"] == 2
    assert complete["new_accepted"] == 0 and complete["source_statuses_changed"] is False
    assert complete["diagnostic_counts"]["artist_key_variant"] == 1
    assert mod.design.sha256(state) == source_hash
    repeated = mod.run(**args)
    assert repeated["diagnostic_counts"] == complete["diagnostic_counts"]
