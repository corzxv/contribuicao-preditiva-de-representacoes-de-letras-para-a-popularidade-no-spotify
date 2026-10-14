from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from tcc_music_popularity.embeddings_scale_v040 import _vectors_for_records
from tcc_music_popularity.lyrics_embeddings_v020 import (
    build_embedding_frame,
    build_embedding_index,
    build_token_chunks,
    validate_embedding_frame,
    weighted_chunk_aggregate,
)


def _config():
    return {
        "model": {
            "id": "sentence-transformers/all-MiniLM-L6-v2",
            "revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
            "embedding_dimension": 384,
        }
    }


def _records(split: str, rows: int):
    return [
        {
            "composition_key": f"{split}-{index}",
            "track_id": f"track-{split}-{index}",
            "lyrics_sha256": f"hash-{split}-{index}",
            "token_count": 254,
            "chunk_count": 1,
            "detected_language": "en",
            "language_status": "english",
            "language_confidence": 0.99,
            "split": split,
        }
        for index in range(rows)
    ]


def test_chunk_protocol_uses_254_content_tokens_and_overlap_32():
    chunks = build_token_chunks(list(range(600)), content_limit=254, overlap=32)
    assert len(chunks) == 3
    assert chunks[0]["end"] == 254
    assert chunks[1]["start"] == 222


def test_weighted_embedding_is_float32_finite_and_l2_normalized():
    vectors = np.eye(2, 384, dtype=np.float32)
    result = weighted_chunk_aggregate(vectors, [254, 100])
    assert result.dtype == np.float32
    assert np.isfinite(result).all()
    assert np.linalg.norm(result) == pytest.approx(1.0, abs=1e-6)


def test_development_and_holdout_frames_are_separate_and_target_free():
    development = _records("development_train", 3)
    holdout = _records("holdout_test", 2)
    vectors = {
        row["lyrics_sha256"]: np.ones(384, dtype=np.float32) / np.sqrt(384)
        for row in development + holdout
    }
    development_frame = build_embedding_frame(development, vectors, _config())
    holdout_frame = build_embedding_frame(holdout, vectors, _config())
    assert development_frame.height == 3
    assert holdout_frame.height == 2
    assert "spotify_popularity" not in holdout_frame.columns
    validate_embedding_frame(development_frame, expected_rows=3, dimension=384, tolerance=1e-5)
    validate_embedding_frame(holdout_frame, expected_rows=2, dimension=384, tolerance=1e-5)


def test_split_index_receives_only_vectors_from_that_split():
    development = _records("development_train", 3)
    holdout = _records("holdout_test", 2)
    vectors = {
        row["lyrics_sha256"]: np.ones(384, dtype=np.float32) / np.sqrt(384)
        for row in development + holdout
    }
    development_vectors = _vectors_for_records(development, vectors)
    assert set(development_vectors) == {row["lyrics_sha256"] for row in development}
    assert not set(development_vectors) & {row["lyrics_sha256"] for row in holdout}
    assert build_embedding_index(development, development_vectors).height == 3


def test_numeric_validation_rejects_nan():
    records = _records("holdout_test", 1)
    vector = np.ones(384, dtype=np.float32) / np.sqrt(384)
    vector[0] = np.nan
    frame = build_embedding_frame(records, {records[0]["lyrics_sha256"]: vector}, _config())
    with pytest.raises(AssertionError, match="validação numérica"):
        validate_embedding_frame(frame, expected_rows=1, dimension=384, tolerance=1e-5)


def test_embedding_schema_has_exactly_384_float32_values():
    records = _records("development_train", 1)
    vector = np.ones(384, dtype=np.float32) / np.sqrt(384)
    frame = build_embedding_frame(records, {records[0]["lyrics_sha256"]: vector}, _config())
    assert frame.schema["embedding"] == pl.Array(pl.Float32, 384)
