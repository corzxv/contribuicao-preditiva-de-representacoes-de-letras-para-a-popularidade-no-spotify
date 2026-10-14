from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from tcc_music_popularity import final_holdout_v060 as evaluator


class PredictOnlySynthetic:
    def __init__(self, scale=1.0, invalid=False):
        self.scale = scale
        self.invalid = invalid

    def predict(self, x):
        values = x["feature"].to_numpy() if isinstance(x, pl.DataFrame) else x[:, 0]
        return np.full(len(values), np.nan) if self.invalid else values * self.scale

    def fit(self, *_args, **_kwargs):
        raise AssertionError("Synthetic model must never be refitted")

    def fit_transform(self, *_args, **_kwargs):
        raise AssertionError("Synthetic transform must never be refitted")

    def partial_fit(self, *_args, **_kwargs):
        raise AssertionError("Synthetic model must never be updated")


def synthetic_features():
    return pl.DataFrame(
        {
            "composition_key": ["synthetic-c2", "synthetic-c0", "synthetic-c1"],
            "track_id": ["synthetic-t2", "synthetic-t0", "synthetic-t1"],
            "spotify_row_id": [12, 10, 11],
            "artist_group_id": ["synthetic-a2", "synthetic-a0", "synthetic-a1"],
            "feature": [-2.0, 12.0, 110.0],
        }
    )


def synthetic_manifest():
    return {
        "models": [
            {"model": "synthetic", "algorithm": "ridge", "input_columns": ["feature"]},
            {"model": "dummy", "algorithm": "dummy", "input_columns": ["feature"]},
        ]
    }


def test_evaluator_only_predicts_preserves_order_and_raw_outside_range():
    features = synthetic_features()
    model = PredictOnlySynthetic()
    result = evaluator.predict_frozen(features, synthetic_manifest(), loader=lambda _: model)
    assert result.select(evaluator.KEYS).equals(features.select(evaluator.KEYS))
    np.testing.assert_array_equal(result["prediction__synthetic"].to_numpy(), [-2, 12, 110])
    np.testing.assert_array_equal(result["prediction__dummy"].to_numpy(), [-2, 12, 110])


def test_prediction_rejects_any_target_before_loading_models():
    features = synthetic_features().with_columns(pl.lit(50).alias("spotify_popularity"))
    with pytest.raises(AssertionError, match="anteceder"):
        evaluator.predict_frozen(
            features, synthetic_manifest(), loader=lambda _: pytest.fail("must not load model")
        )


def test_prediction_rejects_nonfinite_vector():
    with pytest.raises(AssertionError, match="não finito"):
        evaluator.predict_frozen(
            synthetic_features(),
            synthetic_manifest(),
            loader=lambda _: PredictOnlySynthetic(invalid=True),
        )


def test_target_join_uses_keys_and_restores_sealed_order():
    predictions = evaluator.predict_frozen(
        synthetic_features(), synthetic_manifest(), loader=lambda _: PredictOnlySynthetic()
    )
    target = pl.DataFrame(
        {
            "track_id": ["synthetic-t0", "synthetic-t1", "synthetic-t2"],
            "spotify_row_id": [10, 11, 12],
            "spotify_popularity": [0, 10, 100],
        }
    )
    joined, audit = evaluator.align_target(predictions, target)
    assert joined["spotify_popularity"].to_list() == [100, 0, 10]
    assert audit["keys_and_order_preserved"] and audit["multiplied_rows"] == 0


def test_mismatched_representative_or_invalid_target_blocks_evaluation():
    predictions = synthetic_features()
    bad = pl.DataFrame(
        {
            "track_id": ["synthetic-t0", "synthetic-t1", "wrong"],
            "spotify_row_id": [10, 11, 12],
            "spotify_popularity": [0, 10, 100],
        }
    )
    with pytest.raises(AssertionError, match="ausente"):
        evaluator.align_target(predictions, bad)
    invalid = bad.with_columns(
        pl.Series("track_id", ["synthetic-t0", "synthetic-t1", "synthetic-t2"]),
        pl.Series("spotify_popularity", [0, 10, 101]),
    )
    with pytest.raises(AssertionError, match="inválido"):
        evaluator.align_target(predictions, invalid)


def test_metrics_calculations_residual_convention_and_range_counts():
    result = evaluator.metrics(np.array([0, 10, 100]), np.array([-2, 12, 110]))
    assert result["mae"] == pytest.approx(14 / 3)
    assert result["rmse"] == pytest.approx(np.sqrt(108 / 3))
    assert result["mean_residual"] == pytest.approx(-10 / 3)
    assert result["predictions_below_zero"] == 1
    assert result["predictions_above_100"] == 1
    assert result["spearman"] == pytest.approx(1.0)
    y = np.array([0, 10, 100])
    assert result["r2"] == pytest.approx(1 - 108 / np.sum((y - y.mean()) ** 2))


def test_constant_dummy_spearman_is_undefined():
    assert evaluator.metrics(np.arange(5), np.ones(5))["spearman"] is None


def test_artist_bootstrap_preserves_multiplicity_and_composition_weighting():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    reference, candidate = np.array([0.0, 0.0, 0.0, 0.0]), np.array([1.0, 1.0, 4.0, 2.0])
    inverse, weights = np.array([0, 0, 1, 2]), np.array([[2, 0, 1], [0, 3, 0]])
    actual_mae, actual_rmse = evaluator.paired_draws(y, reference, candidate, inverse, weights)
    for index, multiplicities in enumerate(weights):
        sampled = np.concatenate(
            [
                np.tile(np.flatnonzero(inverse == group), count)
                for group, count in enumerate(multiplicities)
            ]
        )
        expected_mae = np.mean(np.abs(y[sampled] - candidate[sampled])) - np.mean(
            np.abs(y[sampled] - reference[sampled])
        )
        expected_rmse = np.sqrt(np.mean((y[sampled] - candidate[sampled]) ** 2)) - np.sqrt(
            np.mean((y[sampled] - reference[sampled]) ** 2)
        )
        assert actual_mae[index] == pytest.approx(expected_mae)
        assert actual_rmse[index] == pytest.approx(expected_rmse)


def test_bootstrap_seed_draws_and_bonferroni_quantiles_are_frozen():
    groups = np.array(["synthetic-a", "synthetic-a", "synthetic-b", "synthetic-c"])
    unique, inverse, weights = evaluator.bootstrap_weights(groups)
    again = evaluator.bootstrap_weights(groups)
    assert len(unique) == 3 and weights.shape == (2000, 3)
    np.testing.assert_array_equal(weights, again[2])
    assert np.all(weights.sum(axis=1) == 3)
    y, reference, candidate = np.arange(4.0), np.zeros(4), np.ones(4)
    result, mae, _ = evaluator.comparison(y, reference, candidate, inverse, weights, primary=True)
    expected = np.quantile(mae, [0.008333333, 0.991666667])
    assert result["mae_bonferroni_low"] == expected[0]
    assert result["mae_bonferroni_high"] == expected[1]
    assert result["gain_confirmed_by_frozen_rule"] == bool(expected[1] < 0)


def test_static_audit_refuses_training_calls_in_evaluator(tmp_path):
    assert evaluator.code_has_no_training_calls()["forbidden_training_calls"] == 0
    bad = tmp_path / "bad.py"
    bad.write_text("model.fit(x, y)\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="treinamento"):
        evaluator.code_has_no_training_calls(bad)


def test_target_access_requires_prediction_seal(monkeypatch, tmp_path):
    monkeypatch.setattr(evaluator, "private", lambda name: tmp_path / name)
    monkeypatch.setattr(
        evaluator.pl,
        "scan_parquet",
        lambda *_args, **_kwargs: pytest.fail("target read before seal"),
    )
    with pytest.raises(AssertionError, match="antes de abrir"):
        evaluator.open_target_once()
