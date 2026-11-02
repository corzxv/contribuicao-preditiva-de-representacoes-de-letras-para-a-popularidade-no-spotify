import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from tcc_music_popularity import observed_modeling_data as mod


def metadata():
    rows = []
    for i in range(30):
        group = i // 2
        digest = hashlib.sha256(f"synthetic {group}".encode()).hexdigest()
        rows.append(
            {
                "track_id": f"t{i:03d}",
                "artist_name": f"Artist {group}",
                "track_name": f"Song {group}",
                "popularity": str(i % 101),
                "year": "2000",
                "genre": " Teste ",
                "danceability": "0.5",
                "energy": "0.6",
                "loudness": "-8",
                "speechiness": "0.1",
                "acousticness": "0.2",
                "instrumentalness": "0",
                "liveness": "0.3",
                "valence": "0.4",
                "tempo": "100",
                "duration_ms": "120000",
                "key": "-1",
                "mode": "1",
                "time_signature": "4",
                "sampling_weight": 2.0,
                "inclusion_probability": 0.5,
                "lyrics_status": "accepted",
                "lyrics_text_ref": f"q{group}",
                "lyrics_strict_text_sha256": digest,
                "text_input_sha256": digest,
                "lyrics_detected_language": "pt",
                "lyrics_language_status": "non_english",
                "readiness_v06_evaluated_track": i < 2,
                **{
                    c: 0 if c == "text_no_lexical_segments" else 1 for c in mod.descriptors.FEATURES
                },
            }
        )
    frame = pl.DataFrame(rows)
    return frame.join(mod.descriptors.grouping(frame), on="track_id", validate="1:1")


def test_metadata_preserves_originals_and_records_invalid_cells():
    frame = metadata().with_columns(
        pl.when(pl.col("track_id") == "t000")
        .then(pl.lit("NaN"))
        .otherwise(pl.col("energy"))
        .alias("energy"),
        pl.when(pl.col("track_id") == "t001")
        .then(pl.lit("2"))
        .otherwise(pl.col("mode"))
        .alias("mode"),
        pl.when(pl.col("track_id") == "t002")
        .then(pl.lit(" "))
        .otherwise(pl.col("tempo"))
        .alias("tempo"),
    )
    result, quality, invalid = mod.prepare_metadata(frame)
    assert result.select(frame.columns).equals(frame)
    assert result["spotify_popularity"].to_list() == [float(i) for i in range(30)]
    assert result["model_key"].unique().to_list() == ["-1"]
    assert result["model_genre"].unique().to_list() == ["Teste"]
    assert result["model_energy"].null_count() == result["model_mode"].null_count() == 1
    assert invalid.select("track_id", "source_column").rows() == [
        ("t000", "energy"),
        ("t001", "mode"),
    ]
    assert next(r for r in quality if r["source"] == "tempo")["source_missing"] == 1
    with pytest.raises(ValueError, match="Popularidade inválida"):
        mod.prepare_metadata(frame.with_columns(pl.lit("101").alias("popularity")))


def test_folds_ignore_target_row_order_and_keep_nested_test_outside():
    frame = metadata()
    original = mod.make_folds(frame)
    shuffled = mod.make_folds(frame.reverse().with_columns(pl.lit(999).alias("popularity")))
    assert original.sort("track_id").equals(shuffled.sort("track_id"))
    for outer in range(5):
        test = original.filter(pl.col("outer_fold") == outer)
        train = original.filter(pl.col("outer_fold") != outer)
        assert not set(test["text_component_id"]) & set(train["text_component_id"])
        assert set(test[f"inner_outer_{outer}"]) == {-1}
        for inner in range(3):
            valid = train.filter(pl.col(f"inner_outer_{outer}") == inner)
            inner_train = train.filter(pl.col(f"inner_outer_{outer}") != inner)
            assert not set(valid["text_component_id"]) & set(inner_train["text_component_id"])
    bad = original.with_columns(
        pl.when(pl.col("outer_fold") == 0)
        .then(0)
        .otherwise(pl.col("inner_outer_0"))
        .alias("inner_outer_0")
    )
    with pytest.raises(ValueError, match="Teste externo entrou"):
        mod.audit_folds(bad)
    with pytest.raises(ValueError, match="Componentes insuficientes"):
        mod.balanced_assignment({"a": 9, "b": 1}, 5, mod.SEED)


def test_component_audit_rejects_text_leakage_and_modified_guest_identity():
    frame = metadata()
    mod.audit_components(frame)
    bad = frame.with_columns(
        pl.when(pl.col("track_id") == "t002")
        .then(pl.lit(frame["text_input_sha256"][0]))
        .otherwise(pl.col("text_input_sha256"))
        .alias("text_input_sha256")
    )
    with pytest.raises(ValueError, match="Identidade cruza componentes"):
        mod.audit_components(bad)
    bad = frame.with_columns(
        pl.when(pl.col("track_id") == "t000")
        .then(pl.lit("Artist 0 feat. Artist 1"))
        .otherwise(pl.col("artist_name"))
        .alias("artist_name")
    )
    with pytest.raises(ValueError, match="Componentes divergem"):
        mod.audit_components(bad)


@pytest.fixture
def paths(tmp_path, monkeypatch):
    import socket

    monkeypatch.setattr(socket.socket, "connect", lambda *args: pytest.fail("Rede proibida"))
    frame = metadata()
    cohort = tmp_path / "cohort.parquet"
    frame.write_parquet(cohort)
    previous = tmp_path / "descriptors.json"
    mod.atomic_json(
        previous,
        {
            "completed": True,
            "cohort_rows": 30,
            "unique_input_texts": 15,
            "features": list(mod.descriptors.FEATURES),
            "seal": {
                "code": mod.embeddings.base.sha256(Path(mod.descriptors.__file__)),
                "protocol": mod.embeddings.base.sha256(mod.descriptors.PROTOCOL),
            },
        },
    )
    store = tmp_path / "embeddings"
    store.mkdir()
    frame.select(mod.INDEX_COLUMNS).write_parquet(store / "indice_embeddings.parquet")
    keys = sorted(frame["text_input_sha256"].unique().to_list())
    vectors = np.eye(384, dtype=np.float32)[: len(keys)]
    hashes = [hashlib.sha256(v.tobytes()).hexdigest() for v in vectors]
    pq.write_table(
        pa.table(
            {
                "text_input_sha256": keys,
                "embedding": pa.FixedSizeListArray.from_arrays(pa.array(vectors.ravel()), 384),
                "vector_sha256": hashes,
            }
        ),
        store / "embeddings.parquet",
    )
    code = [
        Path(mod.embeddings.__file__),
        mod.embeddings.PROTOCOL,
        Path(mod.embeddings.__file__).with_name("lyrics_embeddings_v020.py"),
        Path(mod.embeddings.__file__).with_name("manual_embeddings.py"),
    ]
    seal = {
        "settings": mod.embeddings.SETTINGS,
        "source_sha256": mod.embeddings.base.sha256(cohort),
        "descriptor_report": mod.embeddings.base.sha256(previous),
        "code": {p.name: mod.embeddings.base.sha256(p) for p in code},
    }
    signature = mod.fingerprint(seal)
    with sqlite3.connect(store / "state.sqlite") as db:
        db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT)")
        db.executemany(
            "INSERT INTO meta VALUES (?,?)",
            [("seal", json.dumps(seal)), ("smoke_verified", "true")],
        )
        db.execute(
            "CREATE TABLE vectors(lyrics_sha256 TEXT PRIMARY KEY,vector_sha256 TEXT,config_sha256 TEXT)"
        )
        db.executemany(
            "INSERT INTO vectors VALUES (?,?,?)",
            [(key, digest, signature) for key, digest in zip(keys, hashes, strict=True)],
        )
    report = tmp_path / "embeddings.json"
    mod.atomic_json(
        report,
        {
            "completed": True,
            "mode": "all",
            "unencoded_unique_texts": 0,
            "private_index_rows": 30,
            "source_rows": 30,
            "dimension": 384,
            "max_input_tokens": 512,
            "new_vectors": 15,
            "reused_vectors": 0,
            "settings": mod.embeddings.SETTINGS,
            "requested_unique_texts": 15,
            "seal_sha256": signature,
        },
    )
    return dict(
        cohort_path=cohort,
        descriptor_report=previous,
        embedding_workspace=store,
        embedding_report=report,
        workspace=tmp_path / "private",
        output=tmp_path / "public",
        expected=30,
    )


def test_run_common_cases_manifest_seals_and_deterministic_resume(paths):
    inputs = {
        p: mod.embeddings.base.sha256(p)
        for p in [paths["cohort_path"], paths["embedding_workspace"] / "embeddings.parquet"]
    }
    assert mod.run(**paths) == 0
    summary = mod.read_json(paths["output"] / "resumo_base_modelagem.json")
    assert summary["completed"] and summary["cohort_rows"] == 30
    assert summary["vectors"]["vectors"] == 15 and summary["leakage_checks_passed"]
    assert summary["splits_created"] and not summary["models_trained"]
    assert not summary["encoder_loaded"] and not summary["weights_applied"]
    result = pl.read_parquet(paths["workspace"] / "coorte_modelagem.parquet")
    source = pl.read_parquet(paths["cohort_path"])
    assert result.select(source.columns).equals(source)
    manifest = mod.read_json(paths["workspace"] / "blocos.json")
    for block in manifest["blocks"].values():
        assert not set(block["columns"]) & {
            mod.TARGET,
            "track_id",
            "sampling_weight",
            "readiness_v06_evaluated_track",
            "text_component_id",
            "lyrics_detected_language",
            "artist_name",
        }
    policy = manifest["weighting"]
    assert policy["training"] == "equal_track_weights"
    assert policy["selection"] == "unweighted_MAE"
    assert policy["sensitivity_weight_column"] == "sampling_weight"
    assert not policy["applied_in_data_preparation"]
    before = summary["outputs_sha256"]
    assert mod.run(**paths) == 0
    assert before == mod.read_json(paths["output"] / "resumo_base_modelagem.json")["outputs_sha256"]
    assert all(mod.embeddings.base.sha256(p) == digest for p, digest in inputs.items())
    public = (paths["output"] / "relatorio_base_modelagem.md").read_text(encoding="utf-8")
    assert "t000" not in public and "Artist 0" not in public


def test_run_rejects_incomplete_embeddings_and_misaligned_index(paths):
    report = mod.read_json(paths["embedding_report"])
    mod.atomic_json(paths["embedding_report"], {**report, "completed": False})
    with pytest.raises(ValueError, match="incompletos"):
        mod.run(**paths)
    mod.atomic_json(paths["embedding_report"], report)
    index_path = paths["embedding_workspace"] / "indice_embeddings.parquet"
    index = pl.read_parquet(index_path)
    pl.concat([index.head(29), index.head(1)]).write_parquet(index_path)
    with pytest.raises(ValueError, match="Índice de embeddings"):
        mod.run(**paths)
    assert not mod.read_json(paths["output"] / "resumo_base_modelagem.json")["completed"]


def test_vector_audit_detects_corruption_even_when_export_hash_is_replaced(paths):
    file = paths["embedding_workspace"] / "embeddings.parquet"
    frame = pq.read_table(file)
    keys = frame["text_input_sha256"].to_pylist()
    hashes = frame["vector_sha256"].to_pylist()
    checkpoint = dict(zip(keys, hashes, strict=True))
    vectors = np.asarray(frame["embedding"].to_pylist(), dtype=np.float32)
    vectors[0] = vectors[1]
    hashes[0] = hashlib.sha256(vectors[0].tobytes()).hexdigest()
    pq.write_table(
        pa.table(
            {
                "text_input_sha256": keys,
                "embedding": pa.FixedSizeListArray.from_arrays(pa.array(vectors.ravel()), 384),
                "vector_sha256": hashes,
            }
        ),
        file,
    )
    with pytest.raises(ValueError, match="Hash vetorial diverge"):
        mod.audit_vectors(file, set(keys), checkpoint)


def test_run_preserves_outputs_when_protocol_changes(paths, monkeypatch, tmp_path):
    protocol = tmp_path / "protocol.md"
    protocol.write_bytes(mod.PROTOCOL.read_bytes())
    monkeypatch.setattr(mod, "PROTOCOL", protocol)
    assert mod.run(**paths) == 0
    summary = paths["output"] / "resumo_base_modelagem.json"
    before = summary.read_bytes()
    protocol.write_text("changed protocol", encoding="utf-8")
    with pytest.raises(ValueError, match="Saída incompatível"):
        mod.run(**paths)
    assert summary.read_bytes() == before
