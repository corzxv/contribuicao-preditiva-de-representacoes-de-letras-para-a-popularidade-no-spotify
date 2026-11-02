import hashlib
import json
import sqlite3

import numpy as np
import polars as pl
import pyarrow.parquet as pq
import pytest

from tcc_music_popularity import multilingual_embeddings as mod


class Tokenizer:
    def encode(self, text, **kwargs):
        assert kwargs == {"add_special_tokens": False, "truncation": False}
        return [8, 9] if text == "query: " else [ord(c) % 97 + 10 for c in text]

    def num_special_tokens_to_add(self, pair):
        assert pair is False
        return 2

    def build_inputs_with_special_tokens(self, ids):
        return [1, *ids, 2]


class Encoder:
    def __init__(self):
        self.tokenizer = Tokenizer()
        self.inputs = []

    def forward(self, inputs):
        self.inputs.extend(inputs)
        vectors = np.zeros((len(inputs), 384), dtype=np.float32)
        for i, ids in enumerate(inputs):
            vectors[i, 0] = len(ids)
            vectors[i, 1] = sum(ids) % 101 + 1
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def test_windows_reserve_prefix_and_special_tokens():
    engine = Encoder()
    result, details = mod.encode_text("Ω" * 1001, engine, batch_size=2)
    assert result.shape == (384,) and np.linalg.norm(result) == pytest.approx(1, abs=1e-5)
    assert details["content_tokens"] == details["token_weight_sum"] == 1001
    assert details["chunks"] == 3 and details["max_input_tokens"] == 512
    assert all(ids[:3] == [1, 8, 9] and ids[-1] == 2 and len(ids) <= 512 for ids in engine.inputs)
    again, _ = mod.encode_text("Ω" * 1001, Encoder(), batch_size=1)
    assert np.allclose(result, again, atol=1e-5)
    with pytest.raises(ValueError, match="apenas texto"):
        mod.encode_text({"spotify_popularity": 100}, engine)


def test_invalid_encoder_dimension_or_norm():
    class Wrong(Encoder):
        def forward(self, inputs):
            return np.zeros((len(inputs), 383))

    with pytest.raises(ValueError, match="dimensão"):
        mod.encode_text("synthetic", Wrong())

    class Nonfinite(Encoder):
        def forward(self, inputs):
            return np.full((len(inputs), 384), np.nan)

    with pytest.raises(ValueError, match="NaN"):
        mod.encode_text("synthetic", Nonfinite())


def test_snapshot_hash_validation_no_network(tmp_path):
    snapshot = tmp_path / mod.REVISION
    snapshot.mkdir()
    for name in mod.FILES:
        (snapshot / name).write_bytes(b"synthetic file")
    manifest = {
        "model": mod.MODEL,
        "revision": mod.REVISION,
        "snapshot": str(snapshot),
        "files": {name: mod.base.sha256(snapshot / name) for name in mod.FILES},
    }
    (tmp_path / "snapshot.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert mod.checked_snapshot(tmp_path)[0] == snapshot
    (snapshot / "tokenizer.json").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="alterado"):
        mod.checked_snapshot(tmp_path)


def test_download_only_pinned_allowlisted_model_files(tmp_path, monkeypatch):
    import huggingface_hub

    snapshot = tmp_path / "cache" / mod.REVISION
    snapshot.mkdir(parents=True)
    for name in mod.FILES:
        (snapshot / name).write_bytes(b"synthetic public model file")
    calls = []

    def fake_download(**kwargs):
        calls.append(kwargs)
        return str(snapshot)

    monkeypatch.setattr(huggingface_hub, "snapshot_download", fake_download)
    mod.download(tmp_path / "cache", tmp_path / "state")
    assert calls[0]["repo_id"] == mod.MODEL and calls[0]["revision"] == mod.REVISION
    assert calls[0]["allow_patterns"] == list(mod.FILES)
    assert not any(
        name.endswith(".bin") or name.startswith(("onnx", "openvino"))
        for name in calls[0]["allow_patterns"]
    )
    assert mod.checked_snapshot(tmp_path / "state")[0] == snapshot


@pytest.fixture
def setup(tmp_path, monkeypatch):
    import socket

    monkeypatch.setattr(
        socket.socket, "connect", lambda *args: pytest.fail("Rede proibida nos testes")
    )
    descriptors = tmp_path / "descriptors"
    descriptors.mkdir()
    source = tmp_path / "texts.parquet"
    strings = ["Private synthetic phrase", "\ufeffTexto em português\r\nRepetição", "長い" * 501]
    hashes = [hashlib.sha256(mod.normalize_lyrics_text(t).encode()).hexdigest() for t in strings]
    pl.DataFrame({"query_id": ["q0", "q1", "q2"], "accepted_text": strings}).write_parquet(source)
    metadata = pl.DataFrame(
        {
            "track_id": ["t0", "t1", "t2", "t3"],
            "lyrics_text_ref": ["q0", "q1", "q2", "q0"],
            "text_input_sha256": [*hashes, hashes[0]],
            "text_component_id": ["g0", "g1", "g2", "g0"],
            "text_characters": [len(mod.normalize_lyrics_text(t)) for t in strings]
            + [len(strings[0])],
            "lyrics_detected_language": ["en", "pt", "ja", "en"],
            "lyrics_language_status": ["english", "non_english", "uncertain", "english"],
            "spotify_popularity": [99, 0, 45, 20],
        }
    )
    metadata.write_parquet(descriptors / "coorte_descritores.parquet")
    report = tmp_path / "previous.json"
    report.write_text(
        json.dumps(
            {
                "completed": True,
                "cohort_rows": 4,
                "unique_input_texts": 3,
                "seal": {"texts": mod.base.sha256(source)},
            }
        ),
        encoding="utf-8",
    )
    return dict(
        descriptors=descriptors,
        texts=source,
        descriptor_report=report,
        workspace=tmp_path / "private",
        output=tmp_path / "reports",
        expected=4,
        encoder=Encoder(),
        snapshot_info=(tmp_path, {"synthetic": True}),
    )


def test_smoke_plan_is_deterministic_and_ignores_target(setup):
    frame = pl.read_parquet(setup["descriptors"] / "coorte_descritores.parquet")
    assert mod.smoke_plan(frame) == mod.smoke_plan(
        frame.reverse().with_columns(pl.lit(-999).alias("spotify_popularity"))
    )
    assert len(mod.smoke_plan(frame)) == 3


def test_runner_checkpoint_gate_full_join_and_private_outputs(setup):
    paths = setup
    originals = {
        p: mod.base.sha256(p)
        for p in [paths["texts"], paths["descriptors"] / "coorte_descritores.parquet"]
    }
    assert mod.run("smoke", limit=1, **paths) == 2
    with pytest.raises(ValueError, match="smoke"):
        mod.run("all", **paths)
    assert mod.run("smoke", **paths) == 0
    report = json.loads((paths["output"] / "smoke/resumo_embeddings.json").read_text())
    assert (
        report["completed"]
        and report["reused_vectors"] == 1
        and report["repeat_max_abs_difference"] <= 1e-5
    )
    with sqlite3.connect(paths["workspace"] / "state.sqlite") as db:
        before = dict(db.execute("SELECT lyrics_sha256,vector_sha256 FROM vectors"))
    assert mod.run("all", **paths) == 0
    with sqlite3.connect(paths["workspace"] / "state.sqlite") as db:
        assert before == dict(db.execute("SELECT lyrics_sha256,vector_sha256 FROM vectors"))
    vectors = pl.read_parquet(paths["workspace"] / "embeddings.parquet")
    index = pl.read_parquet(paths["workspace"] / "indice_embeddings.parquet")
    assert vectors.height == 3 and index.height == index["track_id"].n_unique() == 4
    assert "spotify_popularity" not in index.columns
    assert (
        pq.read_schema(paths["workspace"] / "embeddings.parquet").field("embedding").type.list_size
        == 384
    )
    summary = json.loads((paths["output"] / "integral/resumo_embeddings.json").read_text())
    assert summary["reused_vectors"] == 3 and summary["new_vectors"] == 0
    for p, digest in originals.items():
        assert mod.base.sha256(p) == digest
    for p in paths["output"].rglob("*"):
        if p.suffix in (".json", ".md"):
            content = p.read_text(encoding="utf-8")
            assert "Private synthetic phrase" not in content and "t0" not in content


def test_interrupted_inference_preserves_completed_vectors(setup):
    class Interrupted(Encoder):
        def forward(self, inputs):
            if self.inputs:
                raise KeyboardInterrupt()
            return super().forward(inputs)

    paths = dict(setup, encoder=Interrupted())
    with pytest.raises(KeyboardInterrupt):
        mod.run("smoke", **paths)
    partial = json.loads((paths["output"] / "smoke/resumo_embeddings.json").read_text())
    assert not partial["completed"] and partial["error_type"] == "KeyboardInterrupt"
    paths["encoder"] = Encoder()
    assert mod.run("smoke", **paths) == 0
    resumed = json.loads((paths["output"] / "smoke/resumo_embeddings.json").read_text())
    assert resumed["reused_vectors"] >= 1


def test_failed_repeat_revokes_smoke_gate(setup):
    assert mod.run("smoke", **setup) == 0

    class Changed(Encoder):
        def forward(self, inputs):
            result = np.zeros((len(inputs), 384), dtype=np.float32)
            result[:, 10] = 1
            return result

    paths = dict(setup, encoder=Changed())
    with pytest.raises(ValueError, match="Reprodução"):
        mod.run("smoke", **paths)
    with pytest.raises(ValueError, match="smoke"):
        mod.run("all", **setup)
