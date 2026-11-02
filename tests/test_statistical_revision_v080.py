"""Synthetic tests only: no project data, targets or fitted old pipelines."""

import json
import warnings

import numpy as np
import polars as pl
import pytest
from sklearn.exceptions import ConvergenceWarning

from tcc_music_popularity import statistical_revision_report_v080 as report
from tcc_music_popularity import statistical_revision_v080 as revision
from tcc_music_popularity.modeling_pilot_v030 import FeatureBlocks


@pytest.fixture
def toy():
    rng = np.random.default_rng(42)
    n = 90
    group = np.repeat(np.arange(30), 3)
    outer = group % 5
    frame = pl.DataFrame(
        {
            "composition_key": [f"synthetic_composition_{i}" for i in range(n)],
            "track_id": [f"synthetic_track_{i}" for i in range(n)],
            "artist_group_id": [f"synthetic_group_{i}" for i in group],
            "spotify_row_id": range(n),
            "split": ["development_train"] * n,
            "year": 2000 + np.arange(n) % 24,
            "genre": np.where(np.arange(n) % 2, "a", "b"),
            "key": np.arange(n) % 12,
            "time_signature": np.where(np.arange(n) % 2, 3, 4),
            "energy": rng.normal(size=n),
            "mode": np.arange(n) % 2,
            "lfm_0": rng.normal(size=n),
            "lfm_1": rng.normal(size=n),
            "embedding_0": rng.normal(size=n),
            "embedding_1": rng.normal(size=n),
            revision.TARGET: rng.normal(20, 3, size=n),
            **{flag: (np.arange(n) % (i + 2) == 0) for i, flag in enumerate(revision.FLAGS)},
        }
    )
    folds = frame.select("composition_key", "artist_group_id").with_columns(
        pl.Series("outer_fold", outer),
        *[pl.Series(f"inner_outer_{f}", np.where(outer == f, -1, group % 3)) for f in range(5)],
    )
    refs = frame.select(
        "composition_key", "track_id", "artist_group_id", revision.TARGET
    ).with_columns(pl.Series("outer_fold", outer))
    blocks = FeatureBlocks(
        ("year", "genre", "key", "time_signature", "energy", "mode", *revision.FLAGS),
        ("lfm_0", "lfm_1"),
        ("embedding_0", "embedding_1"),
        {},
    )
    return frame, folds, refs, blocks


def test_closed_grids_and_fixed_estimators():
    en, gb = revision.grids("spline_en"), revision.grids("hist_gb")
    assert len(en) == 12 and len(gb) == 8
    assert len({json.dumps(p, sort_keys=True) for p in en}) == 12
    assert len({json.dumps(p, sort_keys=True) for p in gb}) == 8
    assert {p["n_knots"] for p in en} == {3, 5}
    assert {p["loss"] for p in gb} == {"squared_error", "absolute_error"}
    for params in gb:
        model = revision.model_factory("hist_gb", params)
        assert model.max_iter == 200 and model.min_samples_leaf == 20
        assert model.learning_rate == 0.05 and model.early_stopping is False
        assert model.categorical_features is None and model.random_state == 20261013
    model = revision.model_factory("spline_en", en[0])
    assert model.tol == 0.001 and model.max_iter == 50000 and model.precompute is True


def test_real_tables_have_a_closed_allowlist(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Reader must not be reached")

    monkeypatch.setattr(pl, "read_parquet", forbidden)
    for path in (
        revision.OLD / "holdout_features.parquet",
        "data/processed/modeling_base_lfm_v0_1_1.parquet",
        "data/derived/private_final_holdout_v0_6/predictions.parquet",
    ):
        with pytest.raises(ValueError, match="não autorizada"):
            revision.read_development_table(path)


def test_output_guard_rejects_old_files_and_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(revision, "ROOT", tmp_path)
    for path in (
        revision.OLD / "development_matrix.parquet",
        "apps/demo.py",
        "reports/final_holdout_report_v0_6.md",
        revision.PRIVATE / ".." / "old_model.joblib",
    ):
        with pytest.raises(ValueError, match="fora das saídas"):
            revision.output_path(path)
    assert revision.output_path(revision.PRIVATE / "toy.json").is_relative_to(tmp_path)


def test_alignment_and_grouped_folds(toy):
    dev, folds, refs, _ = toy
    revision.validate_alignment(dev, folds, refs, expected=90)
    assert len(revision.validate_folds(dev, folds)) == 20
    with pytest.raises(ValueError, match="Desalinhamento"):
        revision.validate_alignment(dev, folds, refs.reverse(), expected=90)
    with pytest.raises(ValueError, match="referência"):
        revision.validate_alignment(
            dev, folds, refs.with_columns(pl.col(revision.TARGET) + 1), expected=90
        )


def test_fold_validation_rejects_outer_leakage(toy):
    dev, folds, _, _ = toy
    broken = folds.with_columns(
        pl.when(pl.int_range(pl.len()) == 0)
        .then(1)
        .otherwise(pl.col("outer_fold"))
        .alias("outer_fold")
    )
    with pytest.raises(ValueError):
        revision.validate_folds(dev, broken)


def test_fold_validation_rejects_inner_leakage(toy):
    dev, folds, _, _ = toy
    broken = folds.with_columns(
        pl.when(pl.col("outer_fold") == 0)
        .then(0)
        .otherwise(pl.col("inner_outer_0"))
        .alias("inner_outer_0")
    )
    with pytest.raises(ValueError, match="externa"):
        revision.validate_folds(dev, broken)


@pytest.mark.parametrize("knots", [None, 3, 5])
def test_train_only_transformations_categories_pca_and_target_exclusion(toy, knots):
    dev, _, _, blocks = toy
    train, valid = np.arange(60), np.arange(60, 90)
    # Validation extremes and unseen categories cannot enter fitted statistics.
    changed = dev.with_columns(
        pl.when(pl.int_range(pl.len()) >= 60).then(5000).otherwise(pl.col("year")).alias("year"),
        pl.when(pl.int_range(pl.len()) >= 60)
        .then(pl.lit("never_seen"))
        .otherwise(pl.col("genre"))
        .alias("genre"),
        pl.when(pl.int_range(pl.len()) >= 60)
        .then(99999.0)
        .otherwise(pl.col("lfm_0"))
        .alias("lfm_0"),
    )
    part = revision.prepare_partition(changed, blocks, "combined", train, valid, knots, "synthetic")
    transformer = part["transformer"]
    named = transformer.named_steps["preprocess"].named_transformers_
    assert revision.TARGET not in part["audit"]["input_columns"]
    assert "never_seen" not in named["baseline_categorical"].named_steps["one_hot"].categories_[0]
    assert named["traditional"].named_steps["pca"].n_samples_ == 60
    assert named["embedding"].named_steps["pca"].n_samples_ == 60
    assert named["traditional"].named_steps["imputer"].statistics_[0] == pytest.approx(
        changed["lfm_0"][:60].median()
    )
    assert np.isfinite(part["valid"]).all()
    if knots is not None:
        year = named["year_spline"]
        spline = year.named_steps["spline"]
        assert spline.degree == 3 and spline.include_bias is False
        assert spline.knots == "uniform" and spline.extrapolation == "constant"
        np.testing.assert_allclose(
            year.transform(pl.DataFrame({"year": [3000]})),
            year.transform(pl.DataFrame({"year": [5000]})),
        )
        assert part["audit"]["spline_bounds"] == [2000, 2023]
    altered_target = changed.with_columns(pl.lit(-999.0).alias(revision.TARGET))
    second = transformer.transform(
        altered_target[valid.tolist()].select(blocks.columns("combined"))
    )
    np.testing.assert_allclose(part["valid"], second)


def test_cache_audit_depends_on_actual_train_indices(toy):
    dev, _, _, blocks = toy
    one = revision.prepare_partition(
        dev, blocks, "baseline", np.arange(50), np.arange(50, 60), 3, "one"
    )
    two = revision.prepare_partition(
        dev, blocks, "baseline", np.arange(1, 51), np.arange(51, 60), 3, "two"
    )
    assert one["audit"]["train_index_sha256"] != two["audit"]["train_index_sha256"]
    with pytest.raises(ValueError, match="sobrepostas"):
        revision.prepare_partition(
            dev, blocks, "baseline", np.arange(50), np.arange(49, 60), None, "bad"
        )


def test_selection_only_mean_inner_mae_and_stable_tie():
    rows = [
        {"failure": None, "fold_mae": [3, 2, 1], "mean_mae": 2},
        {"failure": None, "fold_mae": [1, 2, 3], "mean_mae": 2},
        {"failure": {"error": "failure"}, "fold_mae": [0], "mean_mae": None},
    ]
    assert revision.choose_candidate(rows) == 0
    with pytest.raises(ValueError, match="Nenhuma"):
        revision.choose_candidate(rows[2:])


def test_fit_failure_records_warnings(monkeypatch):
    def broken(*args):
        raise revision.FitFailure("synthetic failure", [{"category": "SyntheticWarning"}])

    monkeypatch.setattr(revision, "fit_model", broken)
    part = {
        "train": np.zeros((3, 1)),
        "ytrain": np.ones(3),
        "valid": np.zeros((2, 1)),
        "yvalid": np.ones(2),
    }
    result = revision.evaluate_candidate(
        "spline_en", revision.grids("spline_en")[0], [part] * 3, "synthetic"
    )
    assert result["failure"] and result["mean_mae"] is None
    assert result["warnings"][0]["category"] == "SyntheticWarning"


def test_convergence_retries_are_bounded_and_logged(monkeypatch):
    class NeverConverges:
        def set_params(self, **params):
            self.limit = params["max_iter"]

        def fit(self, x, y):
            warnings.warn("synthetic nonconvergence", ConvergenceWarning, stacklevel=2)

    monkeypatch.setattr(revision, "model_factory", lambda *args: NeverConverges())
    with pytest.raises(revision.FitFailure) as error:
        revision.fit_model("spline_en", {}, np.ones((3, 2)), np.ones(3), "synthetic")
    assert [event["max_iter"] for event in error.value.events] == [50000, 200000, 500000]


def test_metrics_thresholds_empty_and_nonfinite():
    metric = revision.metrics(np.zeros(5), np.array([0, 5, 10, 20, 21]))
    assert metric["prop_abs_le5"] == 0.4
    assert metric["prop_abs_le20"] == 0.8 and metric["n_abs_gt20"] == 1
    assert metric["r2"] is None
    assert revision.metrics([], [])["n"] == 0
    with pytest.raises(ValueError, match="não finito"):
        revision.metrics([0], [np.inf])


def test_operational_rule_and_reference_kind():
    y, folds = np.tile([10.0, 20.0, 30.0, 40.0, 50.0], 5), np.repeat(np.arange(5), 5)
    reference = y + 10
    result = report.compare(
        y,
        y + 9,
        reference,
        folds,
        kind="algorithm_vs_v05",
        name="synthetic",
        reference_name="synthetic_ref",
    )
    assert result["candidate_promising"] and result["folds_mae_improved"] == 5
    modest = report.compare(
        y,
        y + 9.9,
        reference,
        folds,
        kind="algorithm_vs_v05",
        name="synthetic",
        reference_name="synthetic_ref",
    )
    assert not modest["candidate_promising"]
    incremental = report.compare(
        y,
        y + 9,
        reference,
        folds,
        kind="lyrics_within_family",
        name="synthetic",
        reference_name="synthetic_ref",
    )
    assert incremental["operational_rule_met"] and not incremental["candidate_promising"]


def test_mae_gain_with_bad_tail_is_not_promising():
    y = np.arange(100, dtype=float)
    folds = np.arange(100) % 5
    reference = y + 10
    error = np.full(100, 1.0)
    error[-10:] = 40
    result = report.compare(
        y,
        y + error,
        reference,
        folds,
        kind="algorithm_vs_v05",
        name="synthetic",
        reference_name="synthetic_ref",
    )
    assert result["mae_reduction_percent"] > 2
    assert result["mae_improved_but_tail_worse"]
    assert not result["candidate_promising"]


def test_strata_are_exhaustive_without_narrow_r2(toy):
    dev, folds, refs, _ = toy
    rows = report.metric_rows(dev, folds, {"synthetic": refs[revision.TARGET].to_numpy()}, [])
    for scope in ("target_band", "year_period"):
        selected = [row for row in rows if row["scope"] == scope]
        assert sum(row["n"] for row in selected) == 90
        assert all(row["r2"] is None for row in selected)
        assert any(row["n"] == 0 and row["small_group_n_lt30"] for row in selected)


def test_seal_detects_protocol_change(tmp_path, monkeypatch):
    monkeypatch.setattr(revision, "ROOT", tmp_path)
    protocol = revision.output_path(revision.PROTOCOL)
    protocol.write_text("synthetic protocol", encoding="utf-8")
    revision.write_json(revision.PRIVATE / "preservation_before.json", {})
    seal = {
        "protocol_sha256": revision.digest(revision.PROTOCOL),
        "inputs_sha256": {},
        "code_sha256": {},
        "preservation_snapshot_sha256": revision.digest(
            revision.PRIVATE / "preservation_before.json"
        ),
    }
    seal["seal_id"] = revision.fingerprint(seal)
    revision.write_json(revision.PRIVATE / "seal.json", seal)
    assert revision.verify_seal()["seal_id"] == seal["seal_id"]
    protocol.write_text("changed synthetic protocol", encoding="utf-8")
    with pytest.raises(ValueError, match="Protocolo mudou"):
        revision.verify_seal()


def test_three_improved_folds_are_insufficient():
    y = np.arange(100, dtype=float)
    folds = np.repeat(np.arange(5), 20)
    candidate = y + np.where(folds < 3, 8.0, 10.1)
    result = report.compare(
        y,
        candidate,
        y + 10,
        folds,
        kind="algorithm_vs_v05",
        name="synthetic",
        reference_name="synthetic_ref",
    )
    assert result["mae_reduction_at_least_2_percent"]
    assert result["folds_mae_improved"] == 3
    assert not result["candidate_promising"]


@pytest.mark.parametrize("family", revision.FAMILIES)
def test_synthetic_pipeline_prediction_reproduces_transformed_prediction(toy, family):
    from sklearn.pipeline import Pipeline
    from threadpoolctl import threadpool_limits

    dev, _, _, blocks = toy
    params = revision.grids(family)[0]
    train, valid = np.arange(60), np.arange(60, 90)
    with threadpool_limits(limits=1):
        part = revision.prepare_partition(
            dev, blocks, "combined", train, valid, params.get("n_knots"), "synthetic"
        )
        model, audit = revision.fit_model(
            family, params, part["train"], part["ytrain"], "synthetic"
        )
        pipeline = Pipeline([("representation", part["transformer"]), ("model", model)])
        x = dev[valid.tolist()].select(blocks.columns("combined"))
        np.testing.assert_allclose(
            pipeline.predict(x), model.predict(part["valid"]), atol=1e-10, rtol=0
        )
        assert revision.TARGET not in x.columns
        assert audit["fit_attempts"] >= 1


def test_comparisons_keep_algorithm_and_lyric_increment_separate(toy):
    dev, folds, _, _ = toy
    y = dev[revision.TARGET].to_numpy()
    predictions = {f"elastic_net__{block}": y + 10 for block in revision.BLOCKS}
    predictions.update(
        {f"{family}__{block}": y + 9 for family in revision.FAMILIES for block in revision.BLOCKS}
    )
    results = report.comparisons(dev, folds, predictions)
    algorithms = [r for r in results if r["comparison_kind"] == "algorithm_vs_v05"]
    lyrics = [r for r in results if r["comparison_kind"] == "lyrics_within_family"]
    assert len(algorithms) == 8 and len(lyrics) == 6
    assert all(row["candidate_promising"] for row in algorithms)
    assert all(row["delta_mae"] == 0 for row in lyrics)


def test_aggregate_metric_output_has_no_individual_identifiers(toy):
    dev, folds, _, _ = toy
    rows = report.metric_rows(dev, folds, {"synthetic": dev[revision.TARGET].to_numpy()}, [])
    prohibited = {
        "composition_key",
        "track_id",
        "artist_group_id",
        "spotify_row_id",
        revision.TARGET,
    }
    assert all(not prohibited.intersection(row) for row in rows)
    exported = pl.DataFrame(rows, infer_schema_length=None).write_csv()
    assert "synthetic_composition" not in exported and "synthetic_track" not in exported
    assert len(rows) == 41


def test_report_markdown_escapes_absolute_error_header():
    rendered = report.table(["Model", "Mediana |e|"], [["synthetic", 2.0]])
    assert "Mediana \\|e\\|" in rendered
