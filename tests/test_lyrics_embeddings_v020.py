from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from tcc_music_popularity.io import write_json
from tcc_music_popularity.lyrics_embeddings_v020 import (
    _reuse_complete_run,
    build_embedding_frame,
    build_embedding_index,
    build_token_chunks,
    classify_language_status,
    detect_language,
    normalize_lyrics_text,
    public_payload_is_aggregate,
    validate_embedding_frame,
    validate_token_coverage,
    weighted_chunk_aggregate,
)
from tcc_music_popularity.lyrics_pilot import _atomic_write_frame


def _config() -> dict:
    return {
        "expected_accepted_compositions": 2,
        "model": {
            "id": "synthetic/model",
            "revision": "a" * 40,
            "embedding_dimension": 384,
        },
        "execution": {"numeric_tolerance": 1e-5},
    }


def _audited_rows() -> list[dict]:
    return [
        {
            "composition_key": "synthetic-1",
            "track_id": "track-1",
            "lyrics_sha256": "hash-a",
            "token_count": 4,
            "chunk_count": 1,
            "detected_language": "en",
            "language_status": "english",
            "language_confidence": 0.99,
        },
        {
            "composition_key": "synthetic-2",
            "track_id": "track-2",
            "lyrics_sha256": "hash-b",
            "token_count": 7,
            "chunk_count": 2,
            "detected_language": "pt",
            "language_status": "non_english",
            "language_confidence": 0.98,
        },
    ]


def test_authorized_normalization_only():
    value = "\ufeff\r\n  [Verse]  \t\r\nCafé   stays!\r\n\r\n"
    assert normalize_lyrics_text(value) == "  [Verse]\nCafé   stays!"


def test_single_chunk_preserves_every_token():
    tokens = list(range(12))
    chunks = build_token_chunks(tokens, content_limit=254, overlap=32)
    assert len(chunks) == 1
    assert chunks[0]["token_ids"] == tokens
    assert chunks[0]["new_token_count"] == len(tokens)
    validate_token_coverage(tokens, chunks)


def test_multiple_chunks_overlap_and_tail_without_truncation():
    tokens = list(range(600))
    chunks = build_token_chunks(tokens, content_limit=254, overlap=32)
    assert len(chunks) == 3
    assert chunks[1]["start"] == chunks[0]["end"] - 32
    assert chunks[-1]["end"] == len(tokens)
    assert sum(chunk["new_token_count"] for chunk in chunks) == len(tokens)
    validate_token_coverage(tokens, chunks)


def test_weighted_aggregation_and_l2_normalization():
    vectors = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    output = weighted_chunk_aggregate(vectors, [3, 1])
    expected = np.asarray([0.75, 0.25])
    expected = expected / np.linalg.norm(expected)
    assert output.dtype == np.float32
    assert np.allclose(output, expected, atol=1e-7)
    assert np.isclose(np.linalg.norm(output), 1.0, atol=1e-7)


def test_language_is_deterministic_and_status_threshold_is_explicit():
    first = detect_language(
        "This synthetic sentence is written in English for a deterministic unit test.",
        threshold=0.8,
    )
    second = detect_language(
        "This synthetic sentence is written in English for a deterministic unit test.",
        threshold=0.8,
    )
    assert first == second
    assert first["detected_language"] == "en"
    assert first["language_status"] == "english"
    assert classify_language_status("en", 0.4, 0.8) == "uncertain"
    assert classify_language_status("pt", 0.9, 0.8) == "non_english"


def test_one_row_per_composition_dimension_dtype_and_finite_values():
    config = _config()
    unit = np.ones(384, dtype=np.float32)
    unit /= np.linalg.norm(unit)
    vectors = {"hash-a": unit, "hash-b": -unit}
    frame = build_embedding_frame(_audited_rows(), vectors, config)
    result = validate_embedding_frame(frame, expected_rows=2, dimension=384, tolerance=1e-5)
    assert result["rows"] == 2
    assert result["dimensions"] == 384
    assert result["dtype"] == "float32"
    assert result["nan_count"] == result["infinite_count"] == 0
    assert "spotify_popularity" not in frame.columns
    assert "plainLyrics" not in frame.columns


def test_duplicate_hash_reuses_identical_vector_without_deduplicating_rows():
    config = _config()
    rows = _audited_rows()
    rows[1]["lyrics_sha256"] = "hash-a"
    vector = np.arange(1, 385, dtype=np.float32)
    vector /= np.linalg.norm(vector)
    frame = build_embedding_frame(rows, {"hash-a": vector}, config)
    index = build_embedding_index(rows, {"hash-a": vector})
    matrix = np.asarray(frame["embedding"].to_list(), dtype=np.float32)
    assert frame.height == 2
    assert index.height == 1
    assert np.array_equal(matrix[0], matrix[1])
    assert index["reuse_count"].to_list() == [2]


def test_public_payload_rejects_ids_text_hashes_and_private_paths():
    assert public_payload_is_aggregate({"counts": {"english": 2}, "mean": 0.5})
    assert not public_payload_is_aggregate({"composition_key": "synthetic-1"})
    assert not public_payload_is_aggregate({"lyrics_sha256": "hash-a"})
    assert not public_payload_is_aggregate({"artifact": "data/raw/lyrics_private/cache"})


def test_completed_run_is_reused_without_rewriting(tmp_path: Path):
    config = _config()
    outputs = {
        "embeddings": str(tmp_path / "embeddings.parquet"),
        "index": str(tmp_path / "index.parquet"),
        "manifest": str(tmp_path / "manifest.json"),
        "audit": str(tmp_path / "audit.md"),
        "pca": str(tmp_path / "pca.md"),
        "run_summary": str(tmp_path / "summary.json"),
    }
    config["outputs"] = outputs
    unit = np.ones(384, dtype=np.float32)
    unit /= np.linalg.norm(unit)
    frame = build_embedding_frame(_audited_rows(), {"hash-a": unit, "hash-b": -unit}, config)
    _atomic_write_frame(frame, outputs["embeddings"])
    Path(outputs["index"]).write_bytes(b"private-index-placeholder")
    Path(outputs["manifest"]).write_text("{}", encoding="utf-8")
    Path(outputs["audit"]).write_text("aggregate only", encoding="utf-8")
    Path(outputs["pca"]).write_text("aggregate only", encoding="utf-8")
    write_json(
        outputs["run_summary"],
        {
            "status": "complete",
            "input_dataset_fingerprint": "fingerprint",
            "model": {"revision": "a" * 40},
        },
    )
    before = Path(outputs["embeddings"]).stat().st_mtime_ns
    reused = _reuse_complete_run(config, "fingerprint")
    after = Path(outputs["embeddings"]).stat().st_mtime_ns
    assert reused is not None
    assert before == after


def test_synthetic_public_json_contains_no_target_holdout_or_text():
    payload = {
        "status": "complete",
        "target_provided_to_encoder": False,
        "holdout_accessed": False,
        "aggregate_counts": {"accepted": 2},
    }
    serialized = json.dumps(payload)
    assert "spotify_popularity" not in serialized
    assert "plainLyrics" not in serialized
    assert public_payload_is_aggregate(payload)
