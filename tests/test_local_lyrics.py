"""Dump, manifesto e letras sintéticos; rede bloqueada e nenhuma escrita no SSD real."""

import json
import socket
import sqlite3
from contextlib import closing

import pytest

from tcc_music_popularity import local_lyrics as local
from tcc_music_popularity import manual_lyrics as manual
from tcc_music_popularity.io import sha256_file
from tcc_music_popularity.manual_embeddings import read_accepted_text


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("Rede não permitida")

    monkeypatch.setattr(socket.socket, "connect", deny)


def query(title="Song", artist="Artist", duration=200, split="development_train"):
    return manual.query_for_track(
        {
            "composition_key": f"{artist}|{title}",
            "split": split,
            "track_id": "synthetic-track",
            "spotify_row_id": 1,
            "artist_name_raw": artist,
            "track_name_raw": title,
            "duration_ms": duration * 1000,
            **{flag: False for flag in manual.VERSION_FLAGS},
        }
    )


def add_candidate(
    db,
    identifier,
    *,
    artist="Artist",
    title="Song",
    text="Synthetic first line\nSynthetic second line",
    duration=200,
    instrumental=False,
    track_reference=None,
):
    db.execute(
        "INSERT INTO tracks VALUES (?,?,?,?,?,?)",
        (identifier, title, artist, "Album", duration, identifier),
    )
    db.execute(
        "INSERT INTO lyrics VALUES (?,?,?,?,?)",
        (
            identifier,
            identifier if track_reference is None else track_reference,
            text,
            None,
            instrumental,
        ),
    )


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(local, "check_prepared", lambda *args: None)
    source, workspace, index_dir = (tmp_path / name for name in ("previous", "local", "index"))
    source.mkdir()
    workspace.mkdir()
    dump = tmp_path / "dump.sqlite"
    with sqlite3.connect(dump) as db:
        db.executescript("""CREATE TABLE tracks (id INTEGER PRIMARY KEY,name TEXT,artist_name TEXT,album_name TEXT,duration REAL,last_lyrics_id INTEGER);
            CREATE TABLE lyrics (id INTEGER PRIMARY KEY,track_id INTEGER,plain_lyrics TEXT,synced_lyrics TEXT,instrumental INTEGER);""")
        add_candidate(db, 1)
    with closing(manual.connect(source)) as db:
        manual.init_db(db)
        for key, status, title in [
            ("a", "not_queried", "Song"),
            ("b", "accepted_exact_unique", "Prior"),
            ("c", "ambiguous_distinct_lyrics", "Uncertain"),
            ("d", "not_found", "Absent"),
        ]:
            q = query(title=title, split="holdout_test" if key == "d" else "development_train")
            db.execute(
                "INSERT INTO queries(query_id,composition_key,data,status) VALUES (?,?,?,?)",
                (key, q["composition_key"], json.dumps(q), status),
            )
            db.execute(
                "INSERT INTO tracks VALUES (?,?,?)",
                (key, key, json.dumps({"track_id": key, "split": q["split"]})),
            )
        db.commit()
    config = {"collection": {"duration_tolerance_seconds": 10}}
    local.initialize_workspace(source, workspace, config)
    with closing(manual.connect(workspace, readonly=True)) as db:
        artists = local.artist_keys(db)
    seal = local.index_seal({"synthetic": True}, artists)
    return source, workspace, dump, index_dir, seal, artists, config


def indexed(setup):
    source, workspace, dump, index_dir, seal, artists, config = setup
    local.build_index(dump, index_dir, seal, artists, batch_size=1)
    return setup


def collect(setup, **kwargs):
    _, workspace, dump, index_dir, seal, _, config = setup
    return local.collect_local(workspace, dump, index_dir / "lookup.sqlite", seal, config, **kwargs)


def classify(setup, q=None):
    _, _, dump, index_dir, seal, _, _ = setup
    with (
        closing(local.readonly(dump)) as db,
        closing(local.readonly(index_dir / "lookup.sqlite")) as ix,
    ):
        q = q or query()
        candidates, incomplete = local.LocalLookup(db, ix).candidates(q)
        env = local.envelope_for(q, candidates, seal, incomplete)
        return local.classify_local(q, env, "not_queried", 10), env


def test_end_to_end_preserves_original_split_and_acceptance(setup, capsys):
    source, workspace, dump, _, _, _, _ = indexed(setup)
    original = sha256_file(source / "state.sqlite")
    dump_hash = sha256_file(dump)
    assert collect(setup, limit=1) == 0
    with closing(manual.connect(workspace, readonly=True)) as db:
        row = db.execute("SELECT * FROM queries WHERE query_id='a'").fetchone()
        assert row["status"] == "accepted_exact_unique"
        assert "Synthetic first" in read_accepted_text(row)["private_lyrics"]
        assert (
            dict(db.execute("SELECT query_id,status FROM queries"))["c"]
            == "ambiguous_distinct_lyrics"
        )
        assert db.execute("SELECT count(*) FROM local_jobs").fetchone()[0] == 2
        assert local.local_status(db)["local_pending"] == 1
        assert (
            json.loads(db.execute("SELECT data FROM queries WHERE query_id='d'").fetchone()[0])[
                "split"
            ]
            == "holdout_test"
        )
    assert collect(setup) == 0
    assert collect(setup) == 0
    with closing(manual.connect(workspace, readonly=True)) as db:
        assert (
            db.execute("SELECT status FROM queries WHERE query_id='d'").fetchone()[0] == "not_found"
        )
        assert db.execute("SELECT sum(attempts) FROM local_jobs").fetchone()[0] == 2
    assert sha256_file(source / "state.sqlite") == original
    assert sha256_file(dump) == dump_hash
    assert "Synthetic first" not in capsys.readouterr().out


def test_normalization_diacritics_title_base_and_version(setup):
    _, _, dump, _, _, _, _ = setup
    with sqlite3.connect(dump) as db:
        db.execute("DELETE FROM tracks")
        db.execute("DELETE FROM lyrics")
        add_candidate(db, 2, artist="Àrtist", title="Song (Remastered)")
    indexed(setup)
    row, _ = classify(setup)
    assert row["final_status"] == "ambiguous_metadata_conflict"  # versão diferente
    q = query(title="Song - Remastered")
    q["remaster"] = True
    row, _ = classify(setup, q)
    assert row["final_status"] == "accepted_exact_unique"


@pytest.mark.parametrize(
    "same_text,expected",
    [(True, "accepted_exact_equivalent"), (False, "ambiguous_distinct_lyrics")],
)
def test_equivalence_and_conflicting_lyrics(setup, same_text, expected):
    with sqlite3.connect(setup[2]) as db:
        add_candidate(
            db,
            2,
            text="Synthetic first line\nSynthetic second line" if same_text else "Different text",
        )
    indexed(setup)
    assert classify(setup)[0]["final_status"] == expected


def test_all_twenty_candidates_complete_not_api_truncation(setup):
    with sqlite3.connect(setup[2]) as db:
        for n in range(2, 21):
            add_candidate(db, n)
    indexed(setup)
    result, _ = classify(setup)
    assert result["final_status"] == "accepted_exact_equivalent"
    assert result["candidate_count_after_endpoint_union"] == 20
    assert result["api_limit_applicable"] is False


def test_limits_never_accept_partial_candidate_set(setup, monkeypatch):
    with sqlite3.connect(setup[2]) as db:
        add_candidate(db, 2)
    indexed(setup)
    monkeypatch.setattr(local, "MAX_CANDIDATES", 1)
    assert classify(setup)[0]["final_status"] == "ambiguous_local_incomplete"
    monkeypatch.setattr(local, "MAX_CANDIDATES", 500)
    monkeypatch.setattr(local, "MAX_TEXT_CHARACTERS", 1)
    assert classify(setup)[0]["final_status"] == "ambiguous_local_incomplete"


def test_duration_and_instrumental(setup):
    indexed(setup)
    assert classify(setup, query(duration=240))[0]["final_status"] == "ambiguous_metadata_conflict"
    with sqlite3.connect(setup[2]) as db:
        db.execute("UPDATE lyrics SET plain_lyrics=NULL,instrumental=1")
    assert classify(setup)[0]["final_status"] == "instrumental"


def test_latest_pointer_not_arbitrary_historical_revision(setup):
    with sqlite3.connect(setup[2]) as db:
        db.execute("INSERT INTO lyrics VALUES (99,1,'OLD conflicting text',NULL,0)")
    indexed(setup)
    result, envelope = classify(setup)
    assert result["final_status"] == "accepted_exact_unique"
    assert envelope["requests"][1]["payload"][0]["local_lyrics_id"] == 1


def test_bad_link_is_error_not_absence_and_retry_bounded(setup):
    with sqlite3.connect(setup[2]) as db:
        db.execute("UPDATE lyrics SET track_id=999")
    indexed(setup)
    assert collect(setup, limit=1) == 2
    assert collect(setup, limit=1, retry_errors=True) == 2
    assert collect(setup, limit=1, retry_errors=True) == 2
    assert collect(setup, limit=1, retry_errors=True) == 0
    with closing(manual.connect(setup[1], readonly=True)) as db:
        assert (
            db.execute("SELECT status FROM queries WHERE query_id='a'").fetchone()[0]
            == "not_queried"
        )
        assert local.local_status(db)["local_exhausted_errors"] == 1


def test_interruption_recovers_cache_without_duplicate_lookup(setup, monkeypatch):
    indexed(setup)
    actual = local.classify_local
    monkeypatch.setattr(
        local, "classify_local", lambda *args: (_ for _ in ()).throw(KeyboardInterrupt())
    )
    assert collect(setup, limit=1) == 2
    monkeypatch.setattr(local, "classify_local", actual)
    monkeypatch.setattr(
        local.LocalLookup,
        "candidates",
        lambda *args: (_ for _ in ()).throw(AssertionError("não buscar novamente")),
    )
    assert collect(setup, limit=1) == 0
    with closing(manual.connect(setup[1], readonly=True)) as db:
        assert db.execute("SELECT attempts FROM local_jobs WHERE query_id='a'").fetchone()[0] == 1


def test_index_resume_transactional(setup, monkeypatch):
    _, _, dump, index_dir, seal, artists, _ = setup
    with sqlite3.connect(dump) as db:
        add_candidate(db, 2)
    save = local.save_json

    def interrupt(*args):
        save(*args)
        raise KeyboardInterrupt

    monkeypatch.setattr(local, "save_json", interrupt)
    with pytest.raises(KeyboardInterrupt):
        local.build_index(dump, index_dir, seal, artists, batch_size=1)
    monkeypatch.setattr(local, "save_json", save)
    result = local.build_index(dump, index_dir, seal, artists, batch_size=1)
    assert result["scanned"] == 2 and result["indexed"] == 2 and result["complete"]
    assert local.build_index(dump, index_dir, seal, artists)["scanned"] == 2


def test_seal_mismatch_blocks(setup):
    indexed(setup)
    with pytest.raises(ValueError, match="outro dump"):
        local.build_index(setup[2], setup[3], {"changed": True}, setup[5])


def test_target_rejected_and_missing_private_files(tmp_path):
    with pytest.raises(ValueError, match="não autorizado"):
        local.safe_query(json.dumps({**query(), "spotify_popularity": 99}))
    with pytest.raises(ValueError, match="ausente"):
        local.readonly(tmp_path / "missing.sqlite")
    with pytest.raises(ValueError, match="não validado"):
        local.checked_dump(tmp_path / "missing.sqlite")


def test_preparation_cannot_overwrite_original(setup):
    with pytest.raises(ValueError, match="NOVO"):
        local.initialize_workspace(setup[0], setup[0], setup[6])


def test_index_filters_only_relevant_artists(setup):
    with sqlite3.connect(setup[2]) as db:
        add_candidate(db, 2, artist="Unrelated")
    indexed(setup)
    with closing(local.readonly(setup[3] / "lookup.sqlite")) as db:
        assert db.execute("SELECT count(*) FROM catalog").fetchone()[0] == 1
        plan = [
            r[3]
            for r in db.execute(
                "EXPLAIN QUERY PLAN SELECT id FROM catalog WHERE artist_key=? AND base_key=?",
                ("artist", "song"),
            )
        ]
        assert any("catalog_base" in p for p in plan)


def test_lookup_sqlite_is_readonly(setup):
    with closing(local.readonly(setup[2])) as db, pytest.raises(sqlite3.OperationalError):
        db.execute("DELETE FROM lyrics")


def test_timeout_does_not_become_not_found(setup):
    indexed(setup)
    with (
        closing(local.readonly(setup[2])) as db,
        closing(local.readonly(setup[3] / "lookup.sqlite")) as ix,
        pytest.raises((TimeoutError, sqlite3.OperationalError)),
    ):
        local.LocalLookup(db, ix, query_timeout=-1).candidates(query())


def test_low_disk_does_not_report_batch_complete(setup, monkeypatch):
    indexed(setup)

    def fail(*args):
        raise ValueError("Espaço insuficiente")

    monkeypatch.setattr(local, "space", fail)
    with pytest.raises(ValueError, match="Espaço"):
        collect(setup)
    state = local.load_json(setup[1] / "local_progress.json")
    assert state["stage"] == "stopped" and state["processed_this_run"] == 0


def test_checked_dump_requires_ready_size_and_path(setup):
    dump = setup[2]
    state = {
        "status": "ready",
        "sqlite_quick_check": "ok",
        "gzip_crc_verified": True,
        "database_path": str(dump),
        "extracted_bytes": dump.stat().st_size,
        "database_sha256": sha256_file(dump),
        "source": {"synthetic": True},
    }
    local.save_json(dump.parent / "dump_progress.json", state)
    identity = local.checked_dump(dump)
    assert identity["verified_sha256"] == sha256_file(dump)
    state["extracted_bytes"] += 1
    local.save_json(dump.parent / "dump_progress.json", state)
    with pytest.raises(ValueError, match="Tamanho"):
        local.checked_dump(dump)


def test_pending_manifest_is_not_mutated_on_repeat_initialization(setup):
    source, workspace, _, _, _, _, config = setup
    original = sha256_file(workspace / "state.sqlite")
    local.initialize_workspace(source, workspace, config)
    assert sha256_file(workspace / "state.sqlite") == original


def test_incomplete_index_cannot_be_used(setup):
    indexed(setup)
    with sqlite3.connect(setup[3] / "lookup.sqlite") as db:
        state = manual.meta_get(db, "progress")
        manual.meta_put(db, "progress", {**state, "complete": False})
    with pytest.raises(ValueError, match="prepare-index"):
        collect(setup)
