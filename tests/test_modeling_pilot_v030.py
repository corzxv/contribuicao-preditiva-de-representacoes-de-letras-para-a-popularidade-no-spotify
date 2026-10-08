from __future__ import annotations

from dataclasses import replace

import numpy as np
import polars as pl
import pytest

from tcc_music_popularity.modeling_pilot_v030 import (
    FeatureBlocks,
    ModelingPilotError,
    assert_no_group_leakage,
    audit_public_outputs,
    build_estimator_pipeline,
    grouped_paired_bootstrap,
    load_feature_blocks,
    make_grouped_folds,
    regression_metrics,
    run_dummy,
    validate_feature_blocks,
    validate_modeling_matrix,
)


def test_manifest_builds_the_four_expected_blocks():
    blocks = load_feature_blocks()
    assert len(blocks.columns("baseline")) == 23
    assert len(blocks.columns("traditional")) == 219
    assert len(blocks.columns("deep")) == 407
    assert len(blocks.columns("combined")) == 603
    assert len(blocks.traditional) == 196
    assert len(blocks.embeddings) == 384
    assert "lfm_entropy" not in blocks.traditional
    assert "lfm_compression_ratio" in blocks.traditional


def test_forbidden_predictor_is_rejected_even_with_expected_count():
    blocks = load_feature_blocks()
    invalid = replace(
        blocks,
        baseline=("spotify_popularity", *blocks.baseline[1:]),
    )
    with pytest.raises(ModelingPilotError, match="proibidas"):
        validate_feature_blocks(invalid)


def _synthetic_blocks() -> FeatureBlocks:
    return FeatureBlocks(
        baseline=("year", "genre", "key", "time_signature", "audio"),
        traditional=("lfm_structural",),
        embeddings=("embedding_000", "embedding_001"),
        traditional_families={"estrutura": ("lfm_structural",)},
    )


def _synthetic_matrix() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "composition_key": ["c1", "c2", "c3"],
            "track_id": ["t1", "t2", "t3"],
            "artist_group_id": ["a1", "a1", "a2"],
            "split": ["development_train"] * 3,
            "spotify_popularity": [10.0, 50.0, 80.0],
            "language_status": ["english", "english", "non_english"],
            "year": [2000, 2001, 2002],
            "genre": ["rock", "pop", "rock"],
            "key": [0, 1, 2],
            "time_signature": [4, 4, 3],
            "audio": [0.1, 0.2, 0.3],
            "lfm_structural": [1.0, None, 3.0],
            "embedding_000": [0.1, 0.2, 0.3],
            "embedding_001": [0.4, 0.5, 0.6],
        }
    )


def test_common_matrix_requires_one_row_per_composition_and_no_holdout():
    matrix = _synthetic_matrix()
    audit = validate_modeling_matrix(matrix, _synthetic_blocks(), expected_rows=3)
    assert audit["rows"] == 3
    assert audit["unique_composition_keys"] == 3
    assert audit["unique_embeddings"] == 3
    assert audit["holdout_rows"] == 0

    duplicated = pl.concat([matrix, matrix.head(1)])
    with pytest.raises(ModelingPilotError, match="uma linha por composição"):
        validate_modeling_matrix(duplicated, _synthetic_blocks(), expected_rows=4)

    holdout = matrix.with_columns(
        pl.when(pl.col("composition_key") == "c3")
        .then(pl.lit("holdout_test"))
        .otherwise(pl.col("split"))
        .alias("split")
    )
    with pytest.raises(ModelingPilotError, match="fora de development_train"):
        validate_modeling_matrix(holdout, _synthetic_blocks(), expected_rows=3)


def test_embedding_correspondence_rejects_duplicate_vectors():
    matrix = _synthetic_matrix().with_columns(
        pl.when(pl.col("composition_key") == "c3")
        .then(pl.lit(0.1))
        .otherwise(pl.col("embedding_000"))
        .alias("embedding_000"),
        pl.when(pl.col("composition_key") == "c3")
        .then(pl.lit(0.4))
        .otherwise(pl.col("embedding_001"))
        .alias("embedding_001"),
    )
    with pytest.raises(ModelingPilotError, match="vetorialmente duplicados"):
        validate_modeling_matrix(matrix, _synthetic_blocks(), expected_rows=3)


def test_grouped_folds_are_reproducible_and_have_no_artist_overlap():
    target = np.linspace(0, 100, 50)
    groups = np.array([f"artist-{index // 2}" for index in range(50)])
    first = make_grouped_folds(target, groups, n_splits=5, seed=123)
    second = make_grouped_folds(target, groups, n_splits=5, seed=123)
    np.testing.assert_array_equal(first, second)
    assert set(first) == set(range(5))
    assert_no_group_leakage(first, groups)


def test_preprocessing_fits_imputation_ohe_and_variance_on_train_only():
    train = pl.DataFrame(
        {
            "num": [1.0, None, 3.0, 5.0, 7.0, 9.0],
            "constant": [2.0] * 6,
            "genre": ["rock", "rock", "pop", "pop", None, "jazz"],
            "key": [0, 0, 1, 1, 2, 2],
            "time_signature": [4, 4, 4, 3, 3, 3],
        }
    )
    validation = pl.DataFrame(
        {
            "num": [999.0, None],
            "constant": [2.0, 2.0],
            "genre": ["unknown", "rock"],
            "key": [11, 0],
            "time_signature": [5, 4],
        }
    )
    columns = train.columns
    pipeline = build_estimator_pipeline(
        columns,
        (),
        algorithm="elastic_net",
        pca_embeddings=False,
        seed=1,
    )
    pipeline.fit(train, np.arange(train.height, dtype=float))
    transformed_train = pipeline[:-1].transform(train)
    transformed_validation = pipeline[:-1].transform(validation)
    assert transformed_validation.shape[0] == 2
    assert transformed_validation.shape[1] == transformed_train.shape[1]
    assert np.all(np.var(transformed_train, axis=0) > 0)
    numeric = pipeline.named_steps["preprocess"].named_transformers_["numeric"]
    assert numeric.named_steps["imputer"].statistics_[0] == 5.0
    assert numeric.named_steps["imputer"].indicator_.features_.tolist() == [0]


def test_pca_is_fit_only_on_training_embeddings_and_not_categoricals():
    rng = np.random.default_rng(7)
    train = pl.DataFrame(
        {
            "genre": ["rock", "pop"] * 10,
            "key": [0, 1] * 10,
            "time_signature": [4] * 20,
            "audio": rng.normal(size=20),
            **{f"embedding_{index:03d}": rng.normal(size=20) for index in range(8)},
        }
    )
    validation = train.head(3).with_columns(
        [pl.col(f"embedding_{index:03d}") + 1000 for index in range(8)]
    )
    embedding_columns = tuple(f"embedding_{index:03d}" for index in range(8))
    pipeline = build_estimator_pipeline(
        train.columns,
        embedding_columns,
        algorithm="elastic_net",
        pca_embeddings=True,
        seed=2,
    )
    pipeline.fit(train, rng.normal(size=20))
    embedding_pipe = pipeline.named_steps["preprocess"].named_transformers_["embedding"]
    assert embedding_pipe.named_steps["pca"].n_samples_ == train.height
    assert 1 <= embedding_pipe.named_steps["pca"].n_components_ <= 8
    assert pipeline[:-1].transform(validation).shape[0] == 3
    assert "categorical" in pipeline.named_steps["preprocess"].named_transformers_


def test_metrics_and_dummy_oof_are_complete():
    target = np.arange(25, dtype=float)
    groups = np.array([f"a{index}" for index in range(25)])
    folds = np.arange(25) % 5
    predictions, rows = run_dummy(target, folds, groups)
    assert not np.isnan(predictions).any()
    assert len(rows) == 6
    assert rows[-1]["scope"] == "overall_oof"
    metrics = regression_metrics(target, predictions)
    assert set(metrics) == {"mae", "rmse", "r2", "spearman"}


def test_grouped_bootstrap_is_paired_and_reproducible():
    observed = np.arange(12, dtype=float)
    reference = observed + 2.0
    candidate = observed + 1.0
    groups = np.array([f"a{index // 2}" for index in range(12)])
    first = grouped_paired_bootstrap(
        observed, reference, candidate, groups, repetitions=200, seed=4
    )
    second = grouped_paired_bootstrap(
        observed, reference, candidate, groups, repetitions=200, seed=4
    )
    assert first == second
    assert first["mae_difference"] == -1.0
    assert first["direction"] == "melhora do candidato"


def test_public_report_privacy_rejects_individual_lyrics_markers(tmp_path):
    report = tmp_path / "bad_public_report.md"
    report.write_text("campo proibido: lyrics_sha256", encoding="utf-8")
    with pytest.raises(ModelingPilotError, match="privacidade pública"):
        audit_public_outputs([str(report)])
