from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from tcc_music_popularity.modeling_pilot_v030 import (
    FeatureBlocks,
    make_grouped_folds,
    regression_metrics,
)
from tcc_music_popularity.modeling_recalibration_v031 import (
    ELASTIC_NET_ALPHAS,
    ELASTIC_NET_L1_RATIOS,
    RIDGE_ALPHAS,
    Representation,
    audit_public_outputs,
    build_representation_transformer,
    classify_incremental_evidence,
    coefficient_diagnostics,
    combine_baseline_and_correction,
    crossfit_fixed_baseline,
    elastic_net_grid,
    load_and_validate_v03_inputs,
    parameter_on_boundary,
    reproduce_v03_baseline,
    ridge_grid,
    run_residual_analysis,
    tune_linear_model,
)


def _blocks() -> FeatureBlocks:
    return FeatureBlocks(
        baseline=("year", "genre", "key", "time_signature", "audio"),
        traditional=("lfm_a", "lfm_b", "lfm_c", "lfm_d"),
        embeddings=tuple(f"embedding_{index:03d}" for index in range(6)),
        traditional_families={"synthetic": ("lfm_a", "lfm_b", "lfm_c", "lfm_d")},
    )


def _frame(rows: int = 36) -> pl.DataFrame:
    rng = np.random.default_rng(9)
    return pl.DataFrame(
        {
            "composition_key": [f"c{index}" for index in range(rows)],
            "track_id": [f"t{index}" for index in range(rows)],
            "artist_group_id": [f"a{index // 2}" for index in range(rows)],
            "split": ["development_train"] * rows,
            "spotify_popularity": np.linspace(5, 90, rows),
            "year": 2000 + np.arange(rows) % 20,
            "genre": ["rock", "pop", "jazz"] * (rows // 3),
            "key": np.arange(rows) % 12,
            "time_signature": 3 + np.arange(rows) % 2,
            "audio": rng.normal(size=rows),
            "lfm_a": rng.normal(size=rows),
            "lfm_b": rng.normal(size=rows),
            "lfm_c": [None if index % 7 == 0 else float(index) for index in range(rows)],
            "lfm_d": np.ones(rows),
            **{f"embedding_{index:03d}": rng.normal(size=rows) for index in range(6)},
        }
    )


def test_v03_sample_and_folds_are_reproduced_without_holdout():
    matrix, folds, _, _, _, audit = load_and_validate_v03_inputs()
    assert matrix.height == 1441
    assert audit["holdout_rows"] == 0
    assert audit["assignment_sha256"] == audit["expected_assignment_sha256"]
    assert np.bincount(folds).tolist() == [289, 289, 287, 289, 287]
    assert audit["artist_overlap_counts"] == [0] * 5


def test_historical_v03_baseline_predictions_are_reproduced():
    matrix, folds, _, target, blocks, _ = load_and_validate_v03_inputs()
    reproduced = reproduce_v03_baseline(matrix, folds, target, blocks)
    historical = pl.read_parquet(
        "data/derived/private_modeling/modeling_pilot_oof_predictions_v0_3.parquet",
        columns=["prediction__elastic_net__baseline__raw"],
    )["prediction__elastic_net__baseline__raw"].to_numpy()
    np.testing.assert_allclose(reproduced, historical, rtol=0, atol=1e-10)


def test_predefined_grids_are_exact_and_do_not_include_pure_ridge_in_elastic_net():
    assert len(ridge_grid()) == 15
    assert tuple(item["alpha"] for item in ridge_grid()) == RIDGE_ALPHAS
    assert len(elastic_net_grid()) == 60
    assert {item["alpha"] for item in elastic_net_grid()} == set(ELASTIC_NET_ALPHAS)
    assert {item["l1_ratio"] for item in elastic_net_grid()} == set(ELASTIC_NET_L1_RATIOS)
    assert 0 not in ELASTIC_NET_L1_RATIOS


def test_ridge_and_expanded_elastic_net_tuning_run_on_inner_splits():
    x = np.arange(60, dtype=float).reshape(20, 3) / 10
    y = x[:, 0] * 2 - x[:, 1] + 0.5
    inner = [
        (x[:12], y[:12], x[12:16], y[12:16]),
        (x[4:16], y[4:16], x[:4], y[:4]),
        (x[8:], y[8:], x[4:8], y[4:8]),
    ]
    ridge_params, ridge_scores = tune_linear_model("ridge", inner, seed=1)
    elastic_params, elastic_scores = tune_linear_model("elastic_net", inner, seed=1)
    assert ridge_params["alpha"] in RIDGE_ALPHAS
    assert elastic_params["alpha"] in ELASTIC_NET_ALPHAS
    assert elastic_params["l1_ratio"] in ELASTIC_NET_L1_RATIOS
    assert len(ridge_scores) == 15
    assert len(elastic_scores) == 60


def test_separate_pcas_are_fit_only_on_training_blocks():
    frame = _frame()
    blocks = _blocks()
    columns = [*blocks.baseline, *blocks.traditional, *blocks.embeddings]
    train = frame.head(30).select(columns)
    validation = (
        frame.tail(6)
        .select(columns)
        .with_columns([pl.col(name) + 1000 for name in blocks.embeddings])
    )
    transformer = build_representation_transformer(Representation("combined", "pca90"), blocks)
    train_output = transformer.fit_transform(train)
    validation_output = transformer.transform(validation)
    named = transformer.named_steps["preprocess"].named_transformers_
    assert named["traditional"].named_steps["pca"].n_samples_ == train.height
    assert named["embedding"].named_steps["pca"].n_samples_ == train.height
    assert "pca" not in named["baseline_numeric"].named_steps
    assert validation_output.shape[1] == train_output.shape[1]


def test_baseline_has_no_pca():
    transformer = build_representation_transformer(Representation("baseline", "raw"), _blocks())
    transformer.fit(_frame().select(list(_blocks().baseline)))
    named = transformer.named_steps["preprocess"].named_transformers_
    assert set(named) >= {"baseline_numeric", "baseline_categorical"}
    assert "traditional" not in named
    assert "embedding" not in named


def test_residual_baseline_predictions_are_cross_fitted_without_overlap():
    frame = _frame()
    target = frame["spotify_popularity"].to_numpy()
    groups = frame["artist_group_id"].to_numpy()
    outer_train = np.arange(30)
    outer_validation = np.arange(30, 36)
    crossfit, validation, audit = crossfit_fixed_baseline(
        frame,
        target,
        groups,
        outer_train,
        outer_validation,
        outer_fold=0,
        blocks=_blocks(),
    )
    assert crossfit.shape == (30,)
    assert validation.shape == (6,)
    assert not np.isnan(crossfit).any()
    assert all(item["overlap"] == 0 for item in audit)
    assert sum(item["validation_rows"] for item in audit) == 30


def test_baseline_plus_residual_correction_is_additive():
    baseline = np.array([10.0, 20.0, 30.0])
    correction = np.array([1.0, -2.0, 0.5])
    np.testing.assert_allclose(
        combine_baseline_and_correction(baseline, correction),
        np.array([11.0, 18.0, 30.5]),
    )
    with pytest.raises(ValueError, match="mesma dimensão"):
        combine_baseline_and_correction(baseline, correction[:2])


def test_residual_analysis_produces_complete_oof_without_in_sample_residuals():
    frame = _frame(60)
    target = frame["spotify_popularity"].to_numpy()
    groups = frame["artist_group_id"].to_numpy()
    folds = make_grouped_folds(target, groups, n_splits=5, seed=20261007)
    predictions, rows, audit = run_residual_analysis(frame, folds, groups, target, _blocks())
    assert len(predictions) == 3
    assert all(not np.isnan(values).any() for values in predictions.values())
    assert len(rows) == 18
    assert audit["in_sample_residual_rows"] == 0
    assert not audit["validation_residuals_used_for_training"]


def test_coefficient_diagnostics_report_nonzero_and_norm_by_block():
    coef = np.array([1.0, 0.0, 3.0, 4.0])
    groups = np.array(["baseline", "baseline", "lfm", "embedding"])
    result = coefficient_diagnostics(coef, groups)
    assert result["nonzero_total"] == 3
    assert result["baseline"]["nonzero"] == 1
    assert result["lfm"]["l2_norm"] == 3.0
    assert result["embedding"]["l2_norm"] == 4.0


def test_boundary_flags_cover_both_grids():
    assert parameter_on_boundary("ridge", {"alpha": min(RIDGE_ALPHAS)})["alpha_lower"]
    flags = parameter_on_boundary(
        "elastic_net",
        {"alpha": max(ELASTIC_NET_ALPHAS), "l1_ratio": max(ELASTIC_NET_L1_RATIOS)},
    )
    assert flags["alpha_upper"]
    assert flags["l1_ratio_upper"]


def _comparison(
    *, delta_percent: float, low: float, high: float, folds: int, overfit: bool
) -> dict[str, object]:
    return {
        "model_key": "ridge__deep__pca90",
        "mae_difference": -0.3 if delta_percent < 0 else 0.1,
        "mae_percent_difference": delta_percent,
        "mae_ci95_low": low,
        "mae_ci95_high": high,
        "folds_improved": folds,
        "severe_overfitting": overfit,
    }


def test_decision_rule_distinguishes_gain_inconclusive_and_no_gain():
    evidence = classify_incremental_evidence(
        [_comparison(delta_percent=-3.0, low=-0.5, high=-0.1, folds=4, overfit=False)]
    )
    inconclusive = classify_incremental_evidence(
        [_comparison(delta_percent=-1.0, low=-0.3, high=0.2, folds=3, overfit=False)]
    )
    no_gain = classify_incremental_evidence(
        [_comparison(delta_percent=1.0, low=-0.1, high=0.3, folds=1, overfit=False)]
    )
    assert evidence["category"] == "evidência piloto de ganho incremental"
    assert inconclusive["category"] == "sinal inconclusivo"
    assert no_gain["category"] == "sem ganho incremental"


def test_regression_metrics_remain_available_for_recalibration():
    observed = np.array([1.0, 2.0, 3.0, 4.0])
    predicted = np.array([1.1, 2.2, 2.8, 3.9])
    result = regression_metrics(observed, predicted)
    assert set(result) == {"mae", "rmse", "r2", "spearman"}
    assert result["mae"] > 0


def test_public_artifact_audit_rejects_individual_private_markers(tmp_path):
    report = tmp_path / "bad_report.md"
    report.write_text("individual field: lyrics_sha256", encoding="utf-8")
    with pytest.raises(Exception, match="privacidade pública"):
        audit_public_outputs([str(report)])
