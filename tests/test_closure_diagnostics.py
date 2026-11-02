import json

import numpy as np
import polars as pl
import pytest

from tcc_music_popularity import closure_diagnostics as mod


def fixture_frame():
    n = 30
    y = np.tile([0.0, 10.0, 30.0, 60.0, 80.0, 100.0], 5)
    baseline = y - np.tile([4.0, 2.0, -1.0, 3.0, 20.0, 40.0], 5)
    return pl.DataFrame(
        {
            "track_id": [f"synthetic_{i}" for i in range(n)],
            "text_component_id": [f"g_{i // 2}" for i in range(n)],
            "outer_fold": np.repeat(np.arange(5), 6),
            "spotify_popularity": y,
            "sampling_weight": np.tile([1.0, 2.0, 3.0, 1.0, 1.0, 1.0], 5),
            "prediction_baseline": baseline,
            "prediction_traditional": baseline + 0.1,
            "prediction_deep": baseline + 0.2,
            "prediction_combined": baseline + 0.3,
        }
    )


def test_cluster_ratio_preserves_track_estimand_not_equal_group_mean():
    result = mod.cluster_ratio([2.0, 18.0, -3.0], [1.0, 9.0, 3.0])
    theta = 17 / 13
    scores = np.array([2.0, 18.0, -3.0]) - theta * np.array([1.0, 9.0, 3.0])
    assert result["delta_mae"] == pytest.approx(theta)
    assert theta != pytest.approx(np.mean([2.0, 2.0, -1.0]))
    assert result["se_cluster_conditional"] == pytest.approx(np.sqrt(1.5 * sum(scores**2) / 13**2))
    assert mod.cluster_ratio([4.0, 36.0, -6.0], [2.0, 18.0, 6.0]) == pytest.approx(
        {
            **result,
            "denominator": 26.0,
        }
    )
    with pytest.raises(ValueError, match="Componentes"):
        mod.cluster_ratio([1.0], [1.0])


def test_bonferroni_combines_bounds_without_independent_fold_variances():
    f = fixture_frame().with_columns(
        *[pl.lit(0.0).alias("prediction_" + m) for m in mod.previous.reg.REFERENCES]
    )
    groups = mod.previous.component_losses(f)
    rows, combined = mod.conditional_intervals(groups)
    assert len(rows) == 20 and len(combined) == 4
    assert all(r["family_size"] == 10 for r in rows)
    for out in combined:
        parts = [
            r
            for r in rows
            if r["weighting"] == out["weighting"] and r["contrast"] == out["contrast"]
        ]
        weights = [r["denominator"] for r in parts]
        assert out["conditional_bonferroni_lower"] == pytest.approx(
            np.average([r["bonferroni_family_lower"] for r in parts], weights=weights)
        )
        assert not out["fold_independence_assumed"] and not out["full_training_uncertainty"]
    with pytest.raises(ValueError, match="repetidos"):
        mod.conditional_intervals(pl.concat([groups, groups.head(1)]))


def test_residual_sign_clipping_and_global_contribution_identity():
    original = fixture_frame()
    report = mod.prediction_diagnostics(original)
    tail = next(r for r in report["tail_residuals"] if r["model"] == "combined")
    assert tail["underpredictions"] == 10 and tail["overpredictions"] == 0
    assert tail["residual_mean"] == pytest.approx(-29.7)
    assert tail["residual_q50"] == pytest.approx(-29.7)
    assert tail["contribution_to_global_mae"] == pytest.approx(10 * 29.7 / 30)
    assert tail["mae_original"] == tail["mae_clipped_sensitivity"]
    metrics = next(
        r
        for r in report["metrics_and_clipping"]
        if r["model"] == "combined" and r["scope"] == "all"
    )
    assert metrics["mae_clipped_sensitivity"] < metrics["mae_original"]
    assert (tail["mae_outside_tail"] * 20 + tail["absolute_error_sum"]) / 30 == pytest.approx(
        metrics["mae_original"]
    )
    bad = original.with_columns(pl.lit(101).alias("spotify_popularity"))
    with pytest.raises(ValueError, match="Resposta"):
        mod.prediction_diagnostics(bad)


def test_light_runner_is_separate_and_preserves_inputs(tmp_path):
    predictions = tmp_path / "pred.parquet"
    components = tmp_path / "groups.parquet"
    diagnostics = tmp_path / "diagnostics.json"
    f = fixture_frame()
    f.write_parquet(predictions)
    mod.previous.component_losses(
        f.with_columns(*[pl.lit(0.0).alias("prediction_" + m) for m in mod.previous.reg.REFERENCES])
    ).write_parquet(components)
    diagnostics.write_text(
        json.dumps(
            {
                "completed": True,
                "cohort_rows": 30,
                "seal": {"inputs": {str(predictions.resolve()): mod.digest(predictions)}},
                "component_losses_sha256": mod.digest(components),
            }
        ),
        encoding="utf-8",
    )
    before = {p: mod.digest(p) for p in (predictions, components, diagnostics)}
    output = tmp_path / "output"
    assert (
        mod.run(
            predictions=predictions,
            components=components,
            diagnostics=diagnostics,
            output=output,
            expected=30,
        )
        == 0
    )
    assert before == {p: mod.digest(p) for p in before}
    summary = json.loads((output / "resumo_fechamento.json").read_text())
    assert summary["completed"] and not summary["models_trained"]
    assert not summary["individual_outputs_written"] and not summary["full_training_uncertainty"]
    for path in output.iterdir():
        assert "synthetic_" not in path.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="preservado"):
        mod.run(
            predictions=predictions,
            components=components,
            diagnostics=diagnostics,
            output=output,
            expected=30,
        )
