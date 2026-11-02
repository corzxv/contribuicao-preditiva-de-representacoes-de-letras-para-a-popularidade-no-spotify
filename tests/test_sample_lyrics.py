"""SQLite/letras/amostra sintéticos; nunca acessar o SSD real ou a rede."""

import json
import socket
import sqlite3
from contextlib import closing

import polars as pl
import pytest

from tcc_music_popularity import sample_lyrics as mod
from tcc_music_popularity.catalog_audit import ACOUSTIC, sha256


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("Rede proibida nos testes")

    monkeypatch.setattr(socket.socket, "connect", deny)


def query(title="Song", artist="Old Artist"):
    return mod.query_for_metadata(
        {"track_id": "test", "artist_name": artist, "track_name": title, "duration_ms": "200000"}
    )


def candidate(identifier=1, title="Song", text="Synthetic line one\nSynthetic line two", **extra):
    return {
        "id": identifier,
        "trackName": title,
        "artistName": "Old Artist",
        "albumName": "Album",
        "duration": 200,
        "plainLyrics": text,
        "syncedLyrics": None,
        "instrumental": False,
        "local_lyrics_id": identifier,
        **extra,
    }


def test_unique_equivalent_conflicting_and_representative():
    result, lyric = mod.classify(query(), [candidate()])
    assert result["status"] == "accepted" and lyric["lrclib_id"] == 1
    equivalent = candidate(2, text="\ufeffSynthetic  line one\r\nSynthetic line two\n")
    result, lyric = mod.classify(query(), [equivalent, candidate()])
    assert result["status"] == "accepted" and result["equivalent_count"] == 2
    assert lyric["plain_text_source"] == candidate()["plainLyrics"]
    assert lyric["equivalent_lrclib_ids"] == [1, 2]
    assert (
        mod.classify(query(), [candidate(), candidate(2, text="Another synthetic text")])[0][
            "reason"
        ]
        == "distinct_strict_texts"
    )
    # Diferença somente de caixa não é equivalência estrita.
    assert (
        mod.classify(query(), [candidate(), candidate(2, text=candidate()["plainLyrics"].lower())])[
            0
        ]["status"]
        == "ambiguous"
    )
    assert (
        mod.classify(query(), [candidate(), candidate(text="Conflict same ID")])[0]["reason"]
        == "same_id_payload_conflict"
    )


def test_versions_instrumental_no_text_incomplete():
    assert (
        mod.classify(query(), [candidate(title="Song - Live")])[0]["reason"] == "version_conflict"
    )
    assert (
        mod.classify(query("Song - Live Paris"), [candidate(title="Song - Live London")])[0][
            "status"
        ]
        == "ambiguous"
    )
    assert (
        mod.classify(query("Song - Live"), [candidate(title="Song - Live")])[0]["status"]
        == "accepted"
    )
    assert (
        mod.classify(query(), [candidate(text=None, instrumental=True)])[0]["status"]
        == "instrumental"
    )
    assert (
        mod.classify(query(), [candidate(instrumental=True)])[0]["reason"]
        == "instrumental_text_conflict"
    )
    result, lyric = mod.classify(
        query(), [candidate(text=None, syncedLyrics="[00:01] Synthetic only sync")]
    )
    assert (
        result["status"] == "no_text"
        and result["text_present"]
        and result["synced_present"]
        and lyric is None
    )
    assert mod.classify(query(), [candidate(), candidate(2, text=None)])[0]["status"] == "ambiguous"
    result, _ = mod.classify(query(), [], "candidate_limit")
    assert (
        result["status"] == "ambiguous"
        and result["candidate_present"] is True
        and result["text_present"] is None
    )
    result, _ = mod.classify(query(), [])
    assert result["status"] == "not_found" and result["candidate_present"] is False


def test_metadata_projection_and_missing():
    assert query("") is None
    assert query(artist="NA") is None
    with pytest.raises(ValueError, match="não autorizados"):
        mod.query_for_metadata({"artist_name": "A", "track_name": "S", "popularity": 100})
    assert (
        mod.query_for_metadata({"artist_name": "A", "track_name": "S", "duration_ms": "NaN"})[
            "duration_seconds"
        ]
        is None
    )


@pytest.fixture
def setup(tmp_path, monkeypatch, request):
    directories = {
        key: tmp_path / key
        for key in ["sample", "dump", "old_index", "old_state", "new_index", "workspace", "reports"]
    }
    for key in ("sample", "dump", "old_index", "old_state"):
        directories[key].mkdir()
    dump = directories["dump"] / "dump.sqlite"
    source_rows = [
        candidate(1),
        candidate(2, title="Equivalent", text="Equal text"),
        candidate(3, title="Equivalent", text="Equal  text\n"),
        candidate(4, title="Conflict", text="First"),
        candidate(5, title="Conflict", text="Second"),
        candidate(6, title="Version - Live"),
        candidate(7, title="Instrumental", text=None, instrumental=True),
        candidate(8, title="Sync", text=None, syncedLyrics="[00:01] Synthetic"),
        candidate(9, title="Broken"),
        candidate(10, title="New song", artistName="New Artist"),
    ]
    with sqlite3.connect(dump) as db:
        db.executescript(
            "CREATE TABLE tracks(id INTEGER PRIMARY KEY,name TEXT,artist_name TEXT,album_name TEXT,duration REAL,last_lyrics_id INTEGER);"
            "CREATE TABLE lyrics(id INTEGER PRIMARY KEY,track_id INTEGER,plain_lyrics TEXT,synced_lyrics TEXT,instrumental INTEGER);"
        )
        for c in source_rows:
            db.execute(
                "INSERT INTO tracks VALUES (?,?,?,?,?,?)",
                (c["id"], c["trackName"], c["artistName"], c["albumName"], c["duration"], c["id"]),
            )
            db.execute(
                "INSERT INTO lyrics VALUES (?,?,?,?,?)",
                (
                    c["id"],
                    999 if c["id"] == 9 and not getattr(request, "param", False) else c["id"],
                    c["plainLyrics"],
                    c["syncedLyrics"],
                    c["instrumental"],
                ),
            )
    identity = {
        "path": str(dump.resolve()),
        "size": dump.stat().st_size,
        "mtime_ns": dump.stat().st_mtime_ns,
        "verified_sha256": sha256(dump),
        "source": "synthetic",
    }
    monkeypatch.setattr(mod.local, "checked_dump", lambda path: identity)
    monkeypatch.setattr(mod.local, "space", lambda *args: None)
    monkeypatch.setattr(
        mod, "language_detector", lambda: (None, {"available": False, "status": "not_evaluated"})
    )
    # O checkpoint antigo tem consultas com split; só seu conjunto de artistas é lido.
    with sqlite3.connect(directories["old_state"] / "state.sqlite") as db:
        db.executescript(
            "CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);CREATE TABLE queries(data TEXT);"
        )
        db.execute(
            "INSERT INTO queries VALUES (?)",
            (json.dumps({**query(), "split": "development_train"}),),
        )
    artists = ["old artist"]
    mod.local.build_index(
        dump,
        directories["old_index"],
        mod.local.index_seal(identity, artists),
        artists,
        batch_size=3,
    )
    titles = [
        "Song",
        "Song",
        "Equivalent",
        "Conflict",
        "Version",
        "Instrumental",
        "Sync",
        "Missing",
        "Broken",
        "New song",
        "",
    ]
    rows = []
    for i, title in enumerate(titles):
        high = i in (2, 9)
        rows.append(
            {
                "": str(i),
                "track_id": f"id{i:02d}",
                "artist_name": "New Artist" if i == 9 else "Old Artist",
                "track_name": title,
                **{c: "0.5" for c in ACOUSTIC},
                "duration_ms": "200000",
                "tempo": "120",
                "key": "1",
                "mode": "1",
                "time_signature": "4",
                "loudness": "-10",
                "popularity": "85" if i == 2 else "95" if i == 9 else "20",
                "year": "2021",
                "genre": "rock",
                "stratum_id": "high" if high else "low",
                "N_h": 2 if high else 18,
                "n_h": 2 if high else 9,
                "inclusion_probability": 1.0 if high else 0.5,
                "sampling_weight": 1.0 if high else 2.0,
                "certainty_selection": high,
                "seed": 20261031,
                "sampling_period": "2020–2023",
                "sampling_popularity_band": "80–100" if high else "20–39",
            }
        )
    sample = directories["sample"] / "amostra_spotify_200k.parquet"
    pl.DataFrame(rows).write_parquet(sample)
    allocation = directories["sample"] / "alocacao_amostra_200k.csv"
    pl.DataFrame({"stratum_id": ["high", "low"], "N_h": [2, 18], "n_h": [2, 9]}).write_csv(
        allocation
    )
    summary = directories["sample"] / "resumo_amostra_200k.json"
    summary.write_text(
        json.dumps(
            {
                "completed": True,
                "output_hashes": {sample.name: sha256(sample), allocation.name: sha256(allocation)},
                "catalog_counts": {"rows": 20, "popularity_ge_80": 2},
            }
        ),
        encoding="utf-8",
    )
    return {
        "sample_path": sample,
        "summary_path": summary,
        "allocation_path": allocation,
        "dump": dump,
        "old_index": directories["old_index"],
        "old_workspace": directories["old_state"],
        "index_dir": directories["new_index"],
        "workspace": directories["workspace"],
        "output": directories["reports"],
        "expected": len(rows),
    }


def test_end_to_end_resume_error_join_and_public_privacy(setup):
    paths = setup
    originals = {
        name: sha256(paths[name])
        for name in ["dump", "sample_path", "summary_path", "allocation_path"]
    }
    assert mod.execute(**paths, limit=2) == 2
    assert mod.execute(**paths) == 2  # referência quebrada para; não vira ausência
    with closing(mod.state_connection(paths["workspace"])) as db:
        counts = dict(db.execute("SELECT status,count(*) FROM queries GROUP BY status"))
        assert counts["technical_error"] == 1
    # Retomada de pendências não repete consultas aceitas nem esconde erro anterior.
    assert mod.execute(**paths) == 2
    final = pl.read_parquet(paths["workspace"] / "resultados_faixas_200k.parquet")
    assert final.height == final["track_id"].n_unique() == 11
    original = pl.read_parquet(paths["sample_path"])
    assert final.select(original.columns).sort("track_id").equals(original.sort("track_id"))
    assert (
        final.filter(pl.col("track_id").is_in(["id00", "id01"]))["lyrics_query_id"].n_unique() == 1
    )
    assert final.filter(pl.col("track_id") == "id08")["lyrics_status"][0] == "technical_error"
    assert final.filter(pl.col("track_id") == "id07")["lyrics_status"][0] == "not_found"
    assert final.filter(pl.col("track_id") == "id10")["lyrics_status"][0] == "insufficient_metadata"
    assert final.filter(pl.col("track_id") == "id09")["lyrics_status"][0] == "accepted"
    texts = pl.read_parquet(paths["workspace"] / "letras_aceitas_200k.parquet")
    assert texts.height == 3
    public = json.loads(
        (paths["output"] / "resumo_busca_local_200k.json").read_text(encoding="utf-8")
    )
    assert public["index"]["additional_artists"] == 1 and public["old_cache_imports"] == 0
    assert public["runs"][-1]["reused_queries"] > 0
    assert public["checks"]["text_references_hashes_valid"]
    comparison = pl.read_csv(paths["output"] / "comparacao_cobertura_letras_200k.csv")
    rates = comparison.filter(
        (pl.col("section") == "coverage_status")
        & (pl.col("variable") == "all")
        & (pl.col("metric") == "accepted_rate")
    )
    assert rates.filter(pl.col("scope") == "unweighted")["value"][0] == pytest.approx(4 / 11)
    assert rates.filter(pl.col("scope") == "weighted")["value"][0] == pytest.approx(6 / 20)
    assert rates.filter(pl.col("scope") == "weighted")["denominator"][0] == 20
    high_rates = comparison.filter(
        (pl.col("section") == "coverage_status")
        & (pl.col("variable") == "_s_coverage_band")
        & pl.col("category").is_in(["80–89", "90–100"])
        & (pl.col("metric") == "accepted_rate")
    )
    assert high_rates.height == 4 and (high_rates["value"] == 1).all()
    with closing(mod.state_connection(paths["workspace"])) as db:
        before = dict(
            db.execute(
                "SELECT query_id,attempts FROM queries WHERE status NOT IN ('pending','technical_error')"
            )
        )
    mod.execute(**paths, retry_errors=True)
    with closing(mod.state_connection(paths["workspace"])) as db:
        assert before == dict(
            db.execute(
                "SELECT query_id,attempts FROM queries WHERE status NOT IN ('pending','technical_error')"
            )
        )
        assert (
            db.execute("SELECT attempts FROM queries WHERE status='technical_error'").fetchone()[0]
            == 2
        )
    for name, digest in originals.items():
        assert sha256(paths[name]) == digest
    for path in paths["output"].iterdir():
        if path.suffix in {".md", ".json", ".csv"}:
            value = path.read_text(encoding="utf-8-sig")
            assert "Synthetic line" not in value and "id00" not in value
            assert texts["text_sha256"][0] not in value
    assert len(list(paths["output"].glob("*.png"))) == 3


@pytest.mark.parametrize("setup", [True], indirect=True)
def test_technical_disconnect_and_retry_is_distinct(setup, monkeypatch):
    original = mod.local.LocalLookup.candidates
    calls = 0

    def fail_once(self, q):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise sqlite3.OperationalError("synthetic disconnection")
        return original(self, q)

    monkeypatch.setattr(mod.local.LocalLookup, "candidates", fail_once)
    assert mod.execute(**setup, limit=1) == 2
    with closing(mod.state_connection(setup["workspace"])) as db:
        assert (
            db.execute("SELECT count(*) FROM queries WHERE status='technical_error'").fetchone()[0]
            == 1
        )
        assert (
            db.execute("SELECT count(*) FROM queries WHERE status='not_found'").fetchone()[0] == 0
        )
    assert mod.execute(**setup, limit=1, retry_errors=True) == 2
    with closing(mod.state_connection(setup["workspace"])) as db:
        assert (
            db.execute("SELECT count(*) FROM queries WHERE status='technical_error'").fetchone()[0]
            == 0
        )
        assert db.execute("SELECT count(*) FROM queries WHERE attempts=2").fetchone()[0] == 1
    assert mod.execute(**setup) == 0
    summary = json.loads(
        (setup["output"] / "resumo_busca_local_200k.json").read_text(encoding="utf-8")
    )
    assert summary["completed"] and summary["tracks_ever_attempted"] == 10


def test_changed_sample_hash_blocks_before_state(setup):
    with setup["sample_path"].open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="Hash da amostra"):
        mod.execute(**setup)
    assert not setup["workspace"].exists()


def test_wal_nonempty_is_not_ignored(tmp_path):
    path = tmp_path / "db.sqlite"
    sqlite3.connect(path).close()
    (tmp_path / "db.sqlite-wal").write_bytes(b"pending")
    with pytest.raises(ValueError, match="WAL"):
        mod.stable_readonly(path)
