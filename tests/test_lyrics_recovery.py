"""Riscos concretos da rodada v2; apenas fontes sintéticas, sem rede/SSD real."""

import json
import socket
import sqlite3
from contextlib import closing

import polars as pl
import pytest
from test_sample_lyrics import candidate, query
from test_sample_lyrics import setup as baseline_setup  # noqa: F401

from tcc_music_popularity import lyrics_recovery as mod
from tcc_music_popularity.catalog_audit import sha256


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("Rede proibida")

    monkeypatch.setattr(socket.socket, "connect", deny)


def test_collaboration_band_names_and_homonyms():
    q = query("Song", "Old Artist feat. Guest")
    c = candidate(title="Song (ft. Guest)")
    result, _ = mod.classify(q, [c])
    assert result["status"] == "accepted"
    assert "explicit_feat_layout" in result["recovery_rule"]
    for band in ("Simon & Garfunkel", "Earth, Wind & Fire", "Kairon; IRSE!", "Band and Friends"):
        assert mod.profile(band, "Song")["artist"] == mod.metadata_key(band)
        assert mod.profile(band, "Song")["guests"] == []
    assert (
        mod.classify(query("Song", "Band & Guest"), [candidate(artistName="Band")])[0]["status"]
        != "accepted"
    )
    assert mod.classify(q, [candidate(title="Song (ft. Someone Else)")])[0]["status"] != "accepted"
    assert (
        mod.classify(query(), [candidate(), candidate(2, text="Other recording", duration=205)])[0][
            "reason"
        ]
        == "substantively_distinct_texts"
    )
    assert mod.classify(query(), [candidate(artistName="Someone Else")])[0]["status"] != "accepted"
    with pytest.raises(ValueError, match="proibido"):
        mod.classify({**query(), "popularity": 100}, [candidate()])


def test_contextual_versions_symbols_duration():
    assert mod.profile("A", "Live Forever")["versions"] == []
    assert mod.profile("A", "Radio Ga Ga")["versions"] == []
    assert (
        mod.classify(query("Live Forever"), [candidate(title="Live Forever")])[0]["status"]
        == "accepted"
    )
    assert (
        mod.classify(query("Song (Live in Paris)"), [candidate(title="Song - Live in Paris")])[0][
            "status"
        ]
        == "accepted"
    )
    for title in (
        "Song - Live London",
        "Song",
        "Song - Remix",
        "Song - Demo",
        "Song - Karaoke",
        "Song - Radio Edit",
    ):
        assert (
            mod.classify(query("Song (Live in Paris)"), [candidate(title=title)])[0]["status"]
            != "accepted"
        )
    assert (
        mod.classify(query("Song (Clean)"), [candidate(title="Song (Explicit)")])[0]["status"]
        != "accepted"
    )
    assert mod.classify(query(), [candidate(duration=211)])[0]["status"] != "accepted"
    assert (
        mod.classify(query(), [candidate(), candidate(2, title="Song - Live")])[0]["reason"]
        == "positive_version_conflict"
    )
    q = mod.recovery_query(
        {"track_id": "x", "artist_name": "!!!", "track_name": "$$$$", "duration_ms": "200000"}
    )
    assert mod.classify(q, [candidate(title="$$$$", artistName="!!!")])[0]["status"] == "accepted"
    assert mod.classify(q, [candidate(title="????", artistName="!!!")])[0]["status"] != "accepted"
    assert mod.metadata_key("Beyoncé") != mod.metadata_key("Beyonce")


def test_empty_typography_substantive_and_instrumental():
    result, lyric = mod.classify(
        query(),
        [
            candidate(text="I’m here…\nAgain"),
            candidate(2, text="I'm here...\nAgain"),
            candidate(3, text=None),
        ],
    )
    assert result["status"] == "accepted" and result["empty_ignored"] == 1
    assert "typographic_equivalence" in result["recovery_rule"]
    assert lyric["plain_text_source"] == "I’m here…\nAgain"
    for altered in (
        "I'm gone...\nAgain",
        "I'm here...\nAgain\nAgain",
        "I'M HERE...\nAgain",
        "I'm here\nAgain",
        "Je suis ici...\nEncore",
    ):
        assert (
            mod.classify(query(), [candidate(text="I’m here…\nAgain"), candidate(2, text=altered)])[
                0
            ]["status"]
            == "ambiguous"
        )
    assert (
        mod.classify(query(), [candidate(), candidate(2, text=None, instrumental=True)])[0][
            "reason"
        ]
        == "instrumental_text_conflict"
    )
    assert mod.classify(query(), [candidate(text=None)])[0]["status"] == "no_text"
    assert (
        mod.classify(query(), [candidate(text=None, instrumental=True)])[0]["status"]
        == "instrumental"
    )
    assert (
        mod.classify(query(), [candidate(), candidate(text="ID conflict")])[0]["reason"]
        == "same_id_payload_conflict"
    )
    assert mod.classify(query(), [], "candidate_limit")[0]["operational_limit"]


def test_synced_extraction_preserves_words_lines_repetition():
    synced = "[ar:Artist]\n[ti:Song]\n[offset:-50]\n[00:01.00]First line\n[00:02.30]Again\n[00:03.00]Again"
    text, error = mod.synced_text(synced)
    assert text == "First line\nAgain\nAgain" and error is None
    result, lyric = mod.classify(query(), [candidate(text=None, syncedLyrics=synced)])
    assert result["status"] == "accepted" and result["text_origin"] == "derived_synced"
    assert lyric["synced_text_source"] == synced and lyric["source_plain_original"] is None
    assert (
        mod.classify(query(), [candidate(text="Different", syncedLyrics=synced)])[0]["reason"]
        == "plain_synced_conflict"
    )
    for invalid in (
        "untimed lyrics",
        "[00:99]Invalid",
        "[00:01][00:02]Repeated",
        "[00:02]B\n[00:01]A",
        "[00:01]<00:01.1>Word",
        "[ar:A]",
    ):
        assert mod.synced_text(invalid)[1] is not None
        assert (
            mod.classify(query(), [candidate(text=None, syncedLyrics=invalid)])[0]["status"]
            != "accepted"
        )


@pytest.fixture
def recovery_setup(request):
    paths = dict(request.getfixturevalue("baseline_setup"))
    # Modificações somente na fixture, antes da criação da baseline sintética.
    with sqlite3.connect(paths["dump"]) as db:
        db.execute("UPDATE lyrics SET track_id=9 WHERE id=9")
        db.execute("UPDATE lyrics SET plain_lyrics=NULL WHERE id=3")
        db.execute("UPDATE lyrics SET plain_lyrics=? WHERE id=4", ("I’m here…\nAgain",))
        db.execute("UPDATE lyrics SET plain_lyrics=? WHERE id=5", ("I'm here...\nAgain",))
        for identifier, title in ((11, "Missing (ft. Guest)"), (12, "$$$$")):
            db.execute(
                "INSERT INTO tracks VALUES (?,?,?,?,?,?)",
                (identifier, title, "Old Artist", "Album", 200, identifier),
            )
            db.execute(
                "INSERT INTO lyrics VALUES (?,?,?,?,?)",
                (identifier, identifier, "New synthetic text", None, 0),
            )
    identity = mod.local.checked_dump(paths["dump"])
    identity.update(
        size=paths["dump"].stat().st_size,
        mtime_ns=paths["dump"].stat().st_mtime_ns,
        verified_sha256=sha256(paths["dump"]),
    )
    paths["old_index"] = paths["old_index"].with_name("old_index_rebuilt_fixture")
    paths["old_index"].mkdir()
    mod.local.build_index(
        paths["dump"],
        paths["old_index"],
        mod.local.index_seal(identity, ["old artist"]),
        ["old artist"],
    )
    frame = pl.read_parquet(paths["sample_path"]).with_columns(
        pl.when(pl.col("track_id") == "id07")
        .then(pl.lit("Old Artist feat. Guest"))
        .otherwise(pl.col("artist_name"))
        .alias("artist_name"),
        pl.when(pl.col("track_id") == "id10")
        .then(pl.lit("$$$$"))
        .otherwise(pl.col("track_name"))
        .alias("track_name"),
    )
    frame.write_parquet(paths["sample_path"])
    summary = json.loads(paths["summary_path"].read_text())
    summary["output_hashes"][paths["sample_path"].name] = sha256(paths["sample_path"])
    paths["summary_path"].write_text(json.dumps(summary), encoding="utf-8")
    assert mod.base.execute(**paths) == 0
    root = paths["workspace"].parent
    return dict(
        sample_path=paths["sample_path"],
        sample_summary=paths["summary_path"],
        allocation=paths["allocation_path"],
        baseline=paths["workspace"],
        baseline_report=paths["output"] / "resumo_busca_local_200k.json",
        dump=paths["dump"],
        old_indexes=(paths["old_index"], paths["index_dir"]),
        workspace=root / "recovery_private",
        output=root / "recovery_public",
        index_dir=root / "recovery_index",
        expected=11,
    )


def test_end_to_end_reuse_resume_transitions_weights(recovery_setup):
    paths = recovery_setup
    originals = {
        p: sha256(p)
        for p in (
            paths["dump"],
            paths["sample_path"],
            paths["baseline"] / "state.sqlite",
            paths["baseline"] / "resultados_faixas_200k.parquet",
            paths["baseline"] / "letras_aceitas_200k.parquet",
        )
    }
    assert mod.execute(**paths, limit=1) == 2
    with closing(mod.base.state_connection(paths["workspace"])) as db:
        attempts = dict(db.execute("SELECT query_id,attempts FROM queries WHERE status='accepted'"))
    assert mod.execute(**paths) == 0
    assert mod.execute(**paths) == 0
    final = pl.read_parquet(paths["workspace"] / "resultados_faixas_200k.parquet")
    original = pl.read_parquet(paths["sample_path"])
    assert final.height == final["track_id"].n_unique() == 11
    assert final.select(original.columns).sort("track_id").equals(original.sort("track_id"))
    assert final.filter(pl.col("v1_lyrics_status") == "instrumental")[
        "lyrics_status"
    ].to_list() == ["instrumental"]
    assert (
        final.filter(pl.col("track_id").is_in(["id02", "id03", "id06", "id07", "id10"]))[
            "lyrics_status"
        ].to_list()
        == ["accepted"] * 5
    )
    with closing(mod.base.state_connection(paths["workspace"])) as db:
        assert all(
            db.execute("SELECT attempts FROM queries WHERE query_id=?", (k,)).fetchone()[0] == n
            for k, n in attempts.items()
        )
    texts = pl.read_parquet(paths["workspace"] / "letras_aceitas_200k.parquet")
    derived = texts.filter(pl.col("plain_text_source").is_null())
    assert derived.height == 1 and derived["accepted_text"][0] == " Synthetic"
    assert derived["synced_text_source"][0] == "[00:01] Synthetic"
    summary = json.loads((paths["output"] / "resumo_recuperacao_letras_200k.json").read_text())
    assert summary["completed"] and summary["recovered_tracks"] == 5
    assert sum(row["n_tracks"] for row in summary["recovered_by_rule"]) == 5
    transitions = pl.read_csv(paths["output"] / "transicoes_status_200k.csv")
    assert transitions["n_tracks"].sum() == 11 and transitions["sum_weights"].sum() == 20
    comparison = pl.read_csv(paths["output"] / "comparacao_cobertura_recuperacao_200k.csv")
    rate = comparison.filter(
        (pl.col("phase") == "after")
        & (pl.col("scope") == "weighted")
        & (pl.col("section") == "coverage_status")
        & (pl.col("variable") == "all")
        & (pl.col("metric") == "accepted_rate")
    )
    assert rate["value"][0] == pytest.approx(16 / 20)
    review = json.loads(
        (paths["workspace"] / "amostra_inspecao_novas_aceitacoes.json").read_text(encoding="utf-8")
    )
    assert {r["rule"] for r in review} == {r["recovery_rule"] for r in summary["recovered_by_rule"]}
    for path, digest in originals.items():
        assert sha256(path) == digest
    for path in paths["output"].iterdir():
        if path.suffix in (".json", ".md", ".csv"):
            content = path.read_text(encoding="utf-8-sig")
            assert "New synthetic text" not in content and texts["text_sha256"][0] not in content
            assert "id00" not in content


def test_disconnect_retry_and_incompatible_state(recovery_setup, monkeypatch):
    paths = recovery_setup
    original = mod.lookup
    calls = 0

    def fail_once(*args):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise sqlite3.OperationalError("synthetic disconnected SSD")
        return original(*args)

    monkeypatch.setattr(mod, "lookup", fail_once)
    assert mod.execute(**paths) == 2
    with closing(mod.base.state_connection(paths["workspace"])) as db:
        assert (
            db.execute("SELECT count(*) FROM queries WHERE status='technical_error'").fetchone()[0]
            == 1
        )
    assert mod.execute(**paths, retry=True) == 0
    before = sha256(paths["workspace"] / "state.sqlite")
    (paths["output"] / "owner.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="incompatível"):
        mod.execute(**paths)
    assert sha256(paths["workspace"] / "state.sqlite") == before


def test_index_checkpoint_resumes_without_duplicate_scan(tmp_path, monkeypatch):
    dump = tmp_path / "synthetic.sqlite"
    with sqlite3.connect(dump) as db:
        db.execute(
            "CREATE TABLE tracks(id INTEGER PRIMARY KEY,name TEXT,artist_name TEXT,album_name TEXT,duration REAL,last_lyrics_id INTEGER)"
        )
        db.execute("INSERT INTO tracks VALUES (1,'Song (ft. Guest)','Artist','Album',200,NULL)")
        db.execute("INSERT INTO tracks VALUES (2,'Song','Unrelated','Album',200,NULL)")
    calls = 0

    def interruption(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic index interruption after first commit")

    monkeypatch.setattr(mod.local, "space", interruption)
    index = tmp_path / "index"
    with pytest.raises(OSError):
        mod.build_index(dump, index, ["artist"], {"synthetic": True})
    monkeypatch.setattr(mod.local, "space", lambda *args: None)
    result = mod.build_index(dump, index, ["artist"], {"synthetic": True})
    assert result["complete"] and result["scanned"] == 2 and result["indexed"] == 1
    with closing(mod.base.stable_readonly(index / "lookup.sqlite")) as db:
        assert db.execute("SELECT count(*) FROM catalog").fetchone()[0] == 1
