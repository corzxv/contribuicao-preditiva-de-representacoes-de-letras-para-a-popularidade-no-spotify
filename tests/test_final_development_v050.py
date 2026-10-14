from __future__ import annotations

import numpy as np
import polars as pl
import pytest
from sklearn.linear_model import ElasticNet

from tcc_music_popularity.config import load_yaml
from tcc_music_popularity.final_development_v050 import (
    assert_unique,
    cached_transform,
    create_folds,
    split_overlap,
    tune_fold,
)
from tcc_music_popularity.modeling_pilot_v030 import FeatureBlocks, load_feature_blocks


def synthetic(rows=60):
    rng = np.random.default_rng(2)
    return pl.DataFrame(
        {
            "composition_key": [f"synthetic-c{i}" for i in range(rows)],
            "track_id": [f"synthetic-t{i}" for i in range(rows)],
            "artist_group_id": [f"synthetic-a{i // 2}" for i in range(rows)],
            "lyrics_sha256": [f"synthetic-h{i}" for i in range(rows)],
            "spotify_popularity": rng.uniform(0, 100, rows),
            "year": rng.uniform(2000, 2020, rows),
            "genre": ["rock", "pop"] * (rows // 2),
            "key": np.arange(rows) % 12,
            "time_signature": np.arange(rows) % 2 + 3,
            "lfm_a": [None if i % 7 == 0 else float(i) for i in range(rows)],
            "lfm_b": rng.normal(size=rows),
            **{f"embedding_{i:03d}": rng.normal(size=rows) for i in range(6)},
        }
    )


def blocks():
    return FeatureBlocks(
        ("year", "genre", "key", "time_signature"),
        ("lfm_a", "lfm_b"),
        tuple(f"embedding_{i:03d}" for i in range(6)),
        {"synthetic": ("lfm_a", "lfm_b")},
    )


def test_nested_folds_exclude_external_validation_and_artist_overlap():
    data = synthetic()
    folds, _ = create_folds(data, load_yaml("configs/final_development_v0_5.yaml"))
    outer = folds["outer_fold"].to_numpy()
    groups = data["artist_group_id"].to_numpy()
    for fold in range(5):
        inner = folds[f"inner_outer_{fold}"].to_numpy()
        assert np.all(inner[outer == fold] == -1)
        for internal in range(3):
            ti, vi = (inner >= 0) & (inner != internal), inner == internal
            assert not set(groups[ti]) & set(groups[vi])
            assert not set(groups[ti]) & set(groups[outer == fold])
    again, _ = create_folds(data, load_yaml("configs/final_development_v0_5.yaml"))
    assert folds.equals(again)


def test_separate_pca_and_imputation_fit_only_on_training_rows(tmp_path):
    data = synthetic()
    output = cached_transform(
        data, np.arange(48), np.arange(48, 60), "combined", blocks(), tmp_path
    )
    named = output["transformer"].named_steps["preprocess"].named_transformers_
    assert named["traditional"].named_steps["pca"].n_samples_ == 48
    assert named["embedding"].named_steps["pca"].n_samples_ == 48
    assert named["traditional"].named_steps["imputer"].statistics_[0] == np.median(
        data.head(48)["lfm_a"].drop_nulls()
    )
    assert output["train"].shape[1] == output["valid"].shape[1]
    assert np.isfinite(output["train"]).all()


def test_transformation_cache_refuses_different_train_sets(tmp_path):
    data = synthetic()
    cached_transform(data, np.arange(48), np.arange(48, 60), "combined", blocks(), tmp_path)
    with pytest.raises(AssertionError, match="outro conjunto"):
        cached_transform(data, np.arange(40), np.arange(40, 60), "combined", blocks(), tmp_path)


def test_overlap_of_artists_blocks_training():
    dev, hold = synthetic().head(30), synthetic().tail(30)
    hold = hold.with_columns(pl.lit(dev["artist_group_id"][0]).alias("artist_group_id"))
    with pytest.raises(AssertionError, match="Leakage"):
        split_overlap(dev, hold)


def test_identical_lyrics_across_splits_blocks_training_for_diagnosis():
    dev, hold = synthetic().head(30), synthetic().tail(30)
    hold = hold.with_columns(pl.lit(dev["lyrics_sha256"][0]).alias("lyrics_sha256"))
    with pytest.raises(AssertionError, match="Letras idênticas"):
        split_overlap(dev, hold)


def test_duplicate_composition_or_track_is_refused():
    data = synthetic().head(4).with_columns(pl.lit("same").alias("track_id"))
    with pytest.raises(AssertionError, match="Chave inválida"):
        assert_unique(data, "synthetic", 4)


def test_gram_optimization_preserves_elastic_net_objective_and_intercept():
    rng = np.random.default_rng(6)
    x = rng.normal(size=(50, 5)) + 4
    y = x[:, 0] * 2 + 20 + rng.normal(size=50)
    config = load_yaml("configs/final_development_v0_5.yaml")
    config["elastic_net"]["alpha"] = [0.1]
    config["elastic_net"]["l1_ratio"] = [0.5]
    _, scores, events = tune_fold("elastic_net", (x[:40], y[:40], x[40:], y[40:]), config)
    direct = ElasticNet(alpha=0.1, l1_ratio=0.5, tol=0.001, max_iter=50000).fit(x[:40], y[:40])
    assert scores[0] == pytest.approx(np.mean(np.abs(y[40:] - direct.predict(x[40:]))), abs=1e-9)
    assert events == []


def test_exact_allowed_feature_names_are_taken_from_definitive_manifest():
    features = load_feature_blocks()
    assert len(features.baseline) == 23
    assert len(features.traditional) == 196
    assert len(features.embeddings) == 384
    assert "live" in features.baseline and "remaster" in features.baseline
    assert not {
        "lfm_entropy",
        "spotify_popularity",
        "genre_sampling",
        "artist_group_id",
        "detected_language",
    } & set(features.columns("combined"))
