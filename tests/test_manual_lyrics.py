"""Testes offline: somente arquivos sintéticos; nenhuma coleta/embedding real."""

import copy
import hashlib
import json
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import polars as pl
import pytest

from tcc_music_popularity import manual_embeddings as emb
from tcc_music_popularity import manual_lyrics as manual


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Acesso à rede proibido nos testes")

    monkeypatch.setattr(urllib.request, "urlopen", denied)


@pytest.fixture
def source():
    rows = []
    for index in range(5):
        rows.append(
            {
                "track_id": f"synthetic_track_{index}",
                "spotify_row_id": index,
                "lfm_record_key": f"lfm_{index}",
                "composition_key": "artist|||song"
                if index < 3
                else "other|||song"
                if index == 3
                else None,
                "artist_group_id": "artist" if index < 3 else "other",
                "composition_group_id": "c1" if index < 3 else "c2",
                "split_group_id": "s1" if index < 3 else "s2",
                "split": "development_train" if index < 3 else "holdout_test",
                "split_random_state": 1,
                "split_version": "synthetic",
                "year": 2000,
                "genre": "rock",
                "duration_ms": 200000,
                "artist_name_raw": "Artist" if index < 3 else "Other",
                "track_name_raw": "Song (Live)" if index == 1 else "Song",
                "match_method": "raw_exact",
                "match_score": 1.0,
                "match_status": "accepted_high_confidence",
                "version_compatible": True,
                "matching_version": "synthetic",
                **{flag: flag == "live" and index == 1 for flag in manual.VERSION_FLAGS},
            }
        )
    return pl.DataFrame(rows)


def envelope(query, *, text="Synthetic line one\nSynthetic line two", status=200):
    candidate = {
        "id": 123,
        "artistName": query["artist_name_query"],
        "trackName": query["track_name_query"],
        "duration": query["duration_seconds"],
        "albumName": None,
        "instrumental": False,
        "plainLyrics": text,
        "syncedLyrics": None,
    }
    shared = {
        "artist_name": query["artist_name_query"],
        "track_name": query["track_name_query"],
        "album_name": None,
    }
    return {
        "cache_version": "v0.4",
        "composition_key": query["composition_key"],
        "cache_key": hashlib.sha256(query["composition_key"].encode()).hexdigest(),
        "requests": [
            {
                "endpoint": "/api/get",
                "parameters": {**shared, "duration": query["duration_seconds"]},
                "http_status": status,
                "payload": candidate if status == 200 else None,
                "attempts": [{"http_status": status}],
            },
            {
                "endpoint": "/api/search",
                "parameters": shared,
                "http_status": 200 if status == 404 else status,
                "payload": [candidate] if status == 200 else [] if status == 404 else None,
                "attempts": [{"http_status": status}],
            },
        ],
    }


def fake_client(status=200, calls=None, interrupt_after_write=False):
    class Client:
        def __init__(self, config):
            self.cache_dir = Path(config["cache_dir"])

        def lookup(self, query):
            if calls is not None:
                calls.append(manual.query_identity(query))
            value = envelope(query, status=status)
            manual.atomic_json(self.cache_dir / f"{value['cache_key']}.json", value)
            if interrupt_after_write:
                raise KeyboardInterrupt
            return value

    return Client


@pytest.fixture
def prepared(tmp_path, source, monkeypatch):
    monkeypatch.setattr(manual, "load_target_free_source", lambda _: source)
    monkeypatch.setattr(manual, "scientific_signature", lambda _: {"synthetic": True})
    monkeypatch.setattr(manual, "discover_history", lambda *args: ([], []))
    workspace = tmp_path / "private"
    manual.prepare(workspace)
    return workspace


def test_universe_all_versions_no_target_and_same_query_dedup(source):
    tracks, queries, audit = manual.build_universe(source)
    assert len(tracks) == 5 and len(queries) == 3
    assert tracks[0]["query_id"] == tracks[2]["query_id"]
    assert tracks[0]["query_id"] != tracks[1]["query_id"]
    assert tracks[4]["ineligibility_reason"] == "missing_composition_key"
    assert audit["eligible_unique_compositions"] == 2
    assert {q["split"] for q in queries.values()} == {"development_train", "holdout_test"}
    with pytest.raises(ValueError, match="alvo"):
        manual.build_universe(source.with_columns(pl.lit(99).alias("spotify_popularity")))


def test_cache_compatibility_does_not_transfer_to_live(source, tmp_path):
    query = manual.query_for_track(source.row(0, named=True))
    live = manual.query_for_track(source.row(1, named=True))
    cache = tmp_path / "old.json"
    manual.atomic_json(cache, envelope(query))
    assert manual.classify_history(query, [cache])[0]["final_status"] in manual.ACCEPTED_STATUSES
    assert manual.classify_history(live, [cache]) is None
    changed_duration = {**query, "duration_seconds": 201.0}
    assert manual.classify_history(changed_duration, [cache]) is None


def test_conflicting_historical_lyrics_are_never_chosen(source, tmp_path):
    query = manual.query_for_track(source.row(0, named=True))
    first, second = tmp_path / "one.json", tmp_path / "two.json"
    manual.atomic_json(first, envelope(query))
    manual.atomic_json(second, envelope(query, text="A completely different synthetic text"))
    result, path, retryable = manual.classify_history(query, [first, second])
    assert result["final_status"] == "ambiguous_history_conflict" and path is None
    assert not retryable


def test_many_cache_directories_and_history_projection(tmp_path, monkeypatch, source):
    monkeypatch.setattr(manual, "ROOT", tmp_path)
    query = manual.query_for_track(source.row(0, named=True))
    first = tmp_path / "data/raw/a/lrclib_cache_v01/first.json"
    second = tmp_path / "data/interim/b/lrclib_cache_v04/nested/second.json"
    manual.atomic_json(first, envelope(query))
    manual.atomic_json(second, envelope(query))
    data = tmp_path / "data/processed/lyrics_smoke_reclassified_v011.parquet"
    data.parent.mkdir(parents=True)
    pl.DataFrame(
        {
            "composition_key": [query["composition_key"]],
            "final_status": ["accepted_exact_unique"],
            "spotify_popularity": [99],
            "plainLyrics": ["DO NOT LOAD"],
        }
    ).write_parquet(data)
    caches, results = manual.discover_history()
    assert set(caches) == {first, second} and results == [data]
    workspace = tmp_path / "work"
    workspace.mkdir()
    db = manual.connect(workspace)
    manual.init_db(db)
    counts = manual.inventory_history(db, caches, results)
    history = db.execute("SELECT data FROM history").fetchone()[0]
    assert "spotify_popularity" not in history and "plainLyrics" not in history
    assert counts["historical_result_rows"] == 1
    db.close()


def test_prepare_is_idempotent_and_does_not_run_network(prepared):
    assert (prepared / "manifest.parquet").is_file()
    result = manual.prepare(prepared)
    assert result["tracks"] == 5 and result["queries"] == 3
    assert result["accepted"] == 0 and result["not_queried"] == 3


def test_limit_resume_and_no_duplicate_requests(prepared):
    calls = []
    assert manual.collect(prepared, limit=1, client_factory=fake_client(calls=calls)) == 0
    assert len(calls) == 1
    assert manual.collect(prepared, client_factory=fake_client(calls=calls)) == 0
    assert len(calls) == 3
    manual.collect(prepared, client_factory=fake_client(calls=calls))
    assert len(calls) == 3
    with manual.connect(prepared) as db:
        assert manual.summary(db)["accepted"] == 3


def test_interruption_after_cache_write_recovers_without_query(prepared):
    calls = []
    assert (
        manual.collect(
            prepared, limit=1, client_factory=fake_client(calls=calls, interrupt_after_write=True)
        )
        == 2
    )
    assert len(calls) == 1
    manual.collect(prepared, limit=1, client_factory=fake_client(calls=calls))
    assert len(calls) == 1


def test_technical_retry_explicit_bounded_and_preserves_cache(prepared):
    calls = []
    manual.collect(prepared, client_factory=fake_client(503, calls))
    assert len(calls) == 3
    old = {p: p.read_bytes() for p in prepared.rglob("*.json") if "lrclib_cache_manual" in str(p)}
    manual.collect(prepared, client_factory=fake_client(503, calls))
    assert len(calls) == 3
    manual.collect(prepared, retry_errors=True, client_factory=fake_client(503, calls))
    manual.collect(prepared, retry_errors=True, client_factory=fake_client(503, calls))
    manual.collect(prepared, retry_errors=True, client_factory=fake_client(503, calls))
    assert len(calls) == 9
    assert all(p.read_bytes() == value for p, value in old.items())
    assert pl.read_parquet(prepared / "pending.parquet").is_empty()


def test_third_attempt_interrupted_after_cache_is_recovered_without_fourth(prepared):
    calls = []
    manual.collect(prepared, client_factory=fake_client(503, calls))
    manual.collect(prepared, retry_errors=True, client_factory=fake_client(503, calls))
    assert len(calls) == 6
    manual.collect(
        prepared,
        limit=1,
        retry_errors=True,
        client_factory=fake_client(calls=calls, interrupt_after_write=True),
    )
    assert len(calls) == 7
    manual.collect(prepared, limit=1, client_factory=fake_client(calls=calls))
    assert len(calls) == 7
    with manual.connect(prepared) as db:
        assert manual.summary(db)["accepted"] == 1


def test_circuit_breaker_stops_batch_and_keeps_remaining_unqueried(prepared, monkeypatch):
    config = manual.load_yaml(manual.CONFIG)
    config["collection"]["circuit_breaker"]["consecutive_technical_errors"] = 2
    monkeypatch.setattr(manual, "load_yaml", lambda _: config)
    calls = []
    assert manual.collect(prepared, client_factory=fake_client(503, calls)) == 2
    assert len(calls) == 2
    with manual.connect(prepared) as db:
        assert manual.summary(db)["not_queried"] == 1
    value = json.loads((prepared / "progress.json").read_text(encoding="utf-8"))
    assert value["stop_reason"].endswith("consecutive_technical_errors")


def test_prepare_reconciles_cache_but_does_not_accept_unverified_history(
    tmp_path, source, monkeypatch
):
    query = manual.query_for_track(source.row(0, named=True))
    cache = tmp_path / "old_cache/local.json"
    manual.atomic_json(cache, envelope(query))
    history = tmp_path / "old_results.parquet"
    pl.DataFrame(
        {"composition_key": ["other|||song"], "final_status": ["accepted_exact_unique"]}
    ).write_parquet(history)
    monkeypatch.setattr(manual, "load_target_free_source", lambda _: source)
    monkeypatch.setattr(manual, "scientific_signature", lambda _: {"synthetic": True})
    monkeypatch.setattr(manual, "discover_history", lambda *args: ([cache], [history]))
    workspace = tmp_path / "private"
    result = manual.prepare(workspace)
    assert result["accepted"] == 1 and result["not_queried"] == 2
    manifest = pl.read_parquet(workspace / "manifest.parquet")
    unverified = manifest.filter(pl.col("composition_key") == "other|||song").row(0, named=True)
    assert unverified["final_status"] == "not_queried"
    assert unverified["historical_rows"] == 1
    assert unverified["cache_evidence"] == "historical_without_selected_cache"


def test_not_found_is_not_retried_as_transient(prepared):
    calls = []
    manual.collect(prepared, client_factory=fake_client(404, calls))
    manual.collect(prepared, retry_errors=True, client_factory=fake_client(calls=calls))
    assert len(calls) == 3


def test_exclusive_lock_rejects_second_writer(tmp_path):
    with (
        manual.exclusive(tmp_path),
        pytest.raises(RuntimeError, match="Outro script"),
        manual.exclusive(tmp_path),
    ):
        pass


def test_vector_dimension_nonfinite_and_norm():
    valid = np.zeros(384, np.float32)
    valid[0] = 1
    assert emb.checked_vector(valid).shape == (384,)
    for invalid in (np.zeros(383), np.full(384, np.nan), np.zeros(384), np.full(384, np.inf)):
        with pytest.raises(ValueError):
            emb.checked_vector(invalid)


def test_encoder_signature_fixed_semantics_not_batch_size():
    config = manual.load_yaml(manual.CONFIG)
    first, second = emb.encoder_config(config, 1), emb.encoder_config(config, 64)
    assert emb.encoding_signature(first) == emb.encoding_signature(second)
    changed = copy.deepcopy(first)
    changed["execution"]["overlap_content_tokens"] = 0
    assert emb.encoding_signature(first) != emb.encoding_signature(changed)
    config = copy.deepcopy(config)
    config["model"]["revision"] = "not-the-frozen-revision"
    with pytest.raises(ValueError, match="revision"):
        emb.encoder_config(config, 64)


def test_saved_vector_hash_and_configuration_guard(tmp_path):
    db = manual.connect(tmp_path)
    manual.init_db(db)
    vector = np.zeros(384, np.float32)
    vector[0] = 1
    emb.save_vector(db, "synthetic_hash", vector, "config_one", {}, "synthetic")
    row = db.execute("SELECT * FROM vectors").fetchone()
    np.testing.assert_array_equal(emb.read_vector(row, "config_one"), vector)
    with pytest.raises(ValueError, match="configuração"):
        emb.read_vector(row, "config_two")
    corrupted = dict(row)
    corrupted["vector"] = b"corrupt"
    with pytest.raises(ValueError, match="corrompido"):
        emb.read_vector(corrupted, "config_one")
    db.close()


def fake_audit(records, tokenizer, config):
    return [
        {
            **r,
            "token_count": 8,
            "chunk_count": 1,
            "detected_language": "en",
            "language_status": "english",
            "language_confidence": 1.0,
        }
        for r in records
    ], {}


def fake_encode(records, model, config):
    vector = np.zeros(384, dtype=np.float32)
    vector[0] = 1
    return {r["lyrics_sha256"]: vector.copy() for r in records}


@pytest.fixture
def embedding_ready(prepared, monkeypatch):
    manual.collect(prepared, client_factory=fake_client())
    monkeypatch.setattr(emb, "import_legacy_vectors", lambda *args: None)
    monkeypatch.setattr(emb, "_set_determinism", lambda *args: None)
    return prepared


def test_embeddings_checkpoint_resume_links_all_tracks_and_splits(embedding_ready):
    workspace = embedding_ready
    calls = []

    def model_loader(config):
        calls.append(1)
        return SimpleNamespace(tokenizer=None)

    emb.generate(
        workspace,
        limit=1,
        checkpoint_every=1,
        model_loader=model_loader,
        tokenizer_audit=fake_audit,
        encoder=fake_encode,
    )
    assert len(calls) == 1
    emb.generate(
        workspace,
        checkpoint_every=1,
        model_loader=model_loader,
        tokenizer_audit=fake_audit,
        encoder=fake_encode,
    )
    assert len(calls) == 1  # Mesmo texto aceito independentemente; vetor já checkpointado.
    emb.generate(
        workspace, model_loader=model_loader, tokenizer_audit=fake_audit, encoder=fake_encode
    )
    assert len(calls) == 1
    index = pl.read_parquet(workspace / "embedding_index.parquet")
    vectors = pl.read_parquet(workspace / "vectors.parquet")
    assert index.height == 4 and index["track_id"].n_unique() == 4
    assert set(index["split"]) == {"development_train", "holdout_test"}
    assert vectors.height == 1 and vectors["embedding"].dtype == pl.Array(pl.Float32, 384)
    assert "spotify_popularity" not in index.columns


def test_embedding_invalid_batch_rolls_back_and_does_not_mark_complete(embedding_ready):
    def broken(records, model, config):
        return {r["lyrics_sha256"]: np.full(384, np.nan) for r in records}

    with pytest.raises(ValueError, match="NaN"):
        emb.generate(
            embedding_ready,
            model_loader=lambda _: SimpleNamespace(tokenizer=None),
            tokenizer_audit=fake_audit,
            encoder=broken,
        )
    with manual.connect(embedding_ready) as db:
        assert manual.summary(db)["embedding_queries_completed"] == 0
    value = json.loads((embedding_ready / "progress.json").read_text(encoding="utf-8"))
    assert value["stage"] == "embedding_failed"


def test_cache_hash_tampering_blocks_embedding(embedding_ready):
    with manual.connect(embedding_ready) as db:
        row = db.execute("SELECT * FROM queries WHERE status LIKE 'accepted%' LIMIT 1").fetchone()
        path = Path(row["cache_path"])
        value = json.loads(path.read_text())
        value["queried_at"] = "tampered"
        manual.atomic_json(path, value)
        with pytest.raises(ValueError, match="alterado"):
            emb.read_accepted_text(row)


def test_old_manifest_requires_normalization_and_revision():
    cfg = emb.encoder_config(manual.load_yaml(manual.CONFIG), 64)
    manifest = {
        "model": cfg["model"],
        "parameters": {
            "overlap_content_tokens": 32,
            "language_confidence_threshold": 0.8,
            "chunk_embedding_l2_normalized": True,
            "final_embedding_l2_normalized": True,
        },
        "environment": {"dtype": "float32"},
    }
    assert emb.compatible_legacy_manifest(manifest, cfg, "v02")
    manifest["parameters"]["chunk_embedding_l2_normalized"] = False
    assert not emb.compatible_legacy_manifest(manifest, cfg, "v02")
