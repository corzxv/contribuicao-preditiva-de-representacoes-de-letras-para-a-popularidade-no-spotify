import hashlib
import sqlite3
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from tcc_music_popularity import observed_regression as mod


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    import socket

    monkeypatch.setattr(socket.socket, "connect", lambda *args: pytest.fail("Rede proibida"))
    monkeypatch.setattr(mod, "ALPHAS", (1.0, 100.0))
    rng = np.random.default_rng(20261101)
    n = 40
    numeric = rng.normal(size=(n, len(mod.data.NUMERIC)))
    source = {
        "track_id": [f"t{i:03d}" for i in range(n)],
        "text_component_id": [f"g{i // 2:03d}" for i in range(n)],
        "text_input_sha256": [
            hashlib.sha256(f"text{i // 2}".encode()).hexdigest() for i in range(n)
        ],
        mod.data.TARGET: 40 + numeric[:, 0] * 5 + numeric[:, 1] * 2,
        "sampling_weight": [1.0, 3.0, 5.0, 10.0] * 10,
        **{"model_" + name: numeric[:, j] for j, name in enumerate(mod.data.NUMERIC)},
        **{"model_" + name: [str(i % 3) for i in range(n)] for name in mod.data.CATEGORICAL},
        **{
            name: np.zeros(n) if name == "text_no_lexical_segments" else rng.normal(size=n)
            for name in mod.data.descriptors.FEATURES
        },
    }
    frame = pl.DataFrame(source)
    folds = mod.data.make_folds(frame)
    base = tmp_path / "base"
    base.mkdir()
    frame.write_parquet(base / "coorte_modelagem.parquet")
    folds.write_parquet(base / "folds_5x3.parquet")
    vectors = rng.normal(size=(20, 384)).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    store = tmp_path / "vectors.parquet"
    pq.write_table(
        pa.table(
            {
                "text_input_sha256": frame["text_input_sha256"]
                .unique(maintain_order=True)
                .to_list(),
                "embedding": pa.FixedSizeListArray.from_arrays(pa.array(vectors.ravel()), 384),
            }
        ),
        store,
    )
    mod.atomic_json(base / "blocos.json", {**mod.data.blocks_manifest(), "embeddings": str(store)})
    report = tmp_path / "base_report.json"
    outputs = {
        name: mod.data.embeddings.base.sha256(base / name)
        for name in ("coorte_modelagem.parquet", "folds_5x3.parquet", "blocos.json")
    }
    mod.atomic_json(
        report,
        {
            "completed": True,
            "cohort_rows": n,
            "leakage_checks_passed": True,
            "outer_folds": 5,
            "inner_folds": 3,
            "outputs_sha256": outputs,
            "seal": {
                "code": mod.data.embeddings.base.sha256(Path(mod.data.__file__)),
                "protocol": mod.data.embeddings.base.sha256(mod.data.PROTOCOL),
                "support_code": {
                    name: mod.data.embeddings.base.sha256(Path(mod.data.__file__).with_name(name))
                    for name in ("manual_lyrics.py", "normalization.py", "lyrics_recovery.py")
                },
                "inputs": {str(store.resolve()): mod.data.embeddings.base.sha256(store)},
            },
        },
    )
    args = dict(
        base_workspace=base,
        base_report=report,
        workspace=tmp_path / "private",
        output=tmp_path / "public",
        expected=n,
    )
    return frame, folds, args


def test_metrics_distinguish_weights_and_constant_r2():
    values = mod.metrics([0, 10], [0, 0], [1, 9])
    assert values["mae"] == 5 and values["mae_original_weight"] == 9
    assert values["rmse"] == pytest.approx(np.sqrt(50)) and values["r2"] == -1
    assert mod.metrics([1, 1], [1, 2], [1, 1])["r2"] is None
    with pytest.raises(ValueError, match="pesos inválidos"):
        mod.metrics([0, 1], [0, 1], [1, 0])


def test_preprocessing_learns_only_training_values_and_ignores_unknown_category(fixture):
    frame, _, _ = fixture
    train, valid = (
        frame.head(30),
        frame.tail(10).with_columns(
            pl.lit(1e10).alias("model_year"), pl.lit("unseen-category").alias("model_genre")
        ),
    )
    prepare = mod.preprocessor("traditional")
    transformed = prepare.fit_transform(train.select(mod.columns_for("traditional")))
    again = prepare.transform(valid.select(mod.columns_for("traditional")))
    numeric = prepare.named_transformers_["numeric"]
    assert numeric["scale"].mean_[0] == pytest.approx(train["model_year"].mean())
    assert (
        "unseen-category" not in prepare.named_transformers_["categorical"]["encode"].categories_[0]
    )
    constant_position = [
        c
        for c in mod.columns_for("traditional")
        if c not in {"model_" + c for c in mod.data.CATEGORICAL}
    ].index("text_no_lexical_segments")
    assert np.all(transformed[:, constant_position] == 0)
    assert np.isfinite(again).all()


def test_outer_targets_do_not_change_alpha_or_model_predictions(fixture):
    frame, folds, _ = fixture
    with sqlite3.connect(":memory:") as db:
        db.execute("CREATE TABLE tuning(key TEXT PRIMARY KEY,payload TEXT,sha256 TEXT)")
        _, first, details = mod.fit_outer(frame, folds, 0, "baseline", db, "test")
    modified = frame.with_columns(
        pl.when(folds["outer_fold"] == 0)
        .then(pl.lit(99999.0))
        .otherwise(pl.col(mod.data.TARGET))
        .alias(mod.data.TARGET)
    )
    with sqlite3.connect(":memory:") as db:
        db.execute("CREATE TABLE tuning(key TEXT PRIMARY KEY,payload TEXT,sha256 TEXT)")
        _, second, other = mod.fit_outer(modified, folds, 0, "baseline", db, "test")
    assert details["selected_alpha"] == other["selected_alpha"]
    np.testing.assert_array_equal(first, second)


def test_runner_gate_partial_resume_common_oof_and_unweighted_fit(fixture, monkeypatch):
    _, _, args = fixture
    before = {
        p: mod.data.embeddings.base.sha256(p)
        for p in [args["base_workspace"] / "coorte_modelagem.parquet", args["base_report"]]
    }
    original_fit = mod.Ridge.fit
    calls = []

    def checked_fit(self, x, y, *positional, **kwargs):
        assert not positional and kwargs.get("sample_weight") is None
        calls.append(len(y))
        return original_fit(self, x, y, **kwargs)

    monkeypatch.setattr(mod.Ridge, "fit", checked_fit)
    with pytest.raises(ValueError, match="Execute smoke"):
        mod.run("all", **args)
    assert mod.run("smoke", **args) == 0
    smoke = mod.data.read_json(args["output"] / "smoke/resumo_modelagem.json")
    assert smoke["completed"] and not smoke["global_metrics_available"]
    assert smoke["reload_max_abs_difference"] <= 1e-8
    assert mod.run("all", limit_outer_blocks=1, **args) == 2
    partial = mod.data.read_json(args["output"] / "integral/resumo_modelagem.json")
    assert partial["new_outer_blocks"] == 1 and not partial["global_metrics_available"]
    assert (args["workspace"] / "integral/parts/outer0_combined.json").is_file()
    assert not (args["workspace"] / "integral/parts/outer0_baseline.json").exists()
    assert mod.run("all", **args) == 0
    summary = mod.data.read_json(args["output"] / "integral/resumo_modelagem.json")
    assert summary["completed"] and summary["reused_outer_blocks"] == 1
    assert summary["models_evaluated"] == 6 and summary["prediction_rows"] == 40
    assert summary["paired_comparisons"] == 5
    predictions = pl.read_parquet(args["workspace"] / "integral/predicoes_externas.parquet")
    metrics = pl.read_csv(args["output"] / "integral/metricas_externas.csv")
    for block in (*mod.BLOCKS, *mod.REFERENCES):
        recomputed = mod.metrics(
            predictions[mod.data.TARGET],
            predictions["prediction_" + block],
            predictions["sampling_weight"],
        )
        row = metrics.filter(pl.col("model") == block).row(0, named=True)
        assert row["n"] == 40 and row["mae"] == pytest.approx(recomputed["mae"])
        assert row["mae_original_weight"] == pytest.approx(recomputed["mae_original_weight"])
    assert all(mod.data.embeddings.base.sha256(p) == digest for p, digest in before.items())
    prediction_hash = summary["predictions_sha256"]
    calls_before = len(calls)
    assert mod.run("all", **args) == 0 and len(calls) == calls_before
    assert (
        mod.data.read_json(args["output"] / "integral/resumo_modelagem.json")["predictions_sha256"]
        == prediction_hash
    )


def test_interruption_reuses_confirmed_inner_adjustments(fixture, monkeypatch):
    _, _, args = fixture
    original = mod.fit_ridge
    count = 0

    def interrupt(x, y, alpha):
        nonlocal count
        count += 1
        if count == 3:
            raise KeyboardInterrupt()
        return original(x, y, alpha)

    monkeypatch.setattr(mod, "fit_ridge", interrupt)
    with pytest.raises(KeyboardInterrupt):
        mod.run("smoke", **args)
    with sqlite3.connect(args["workspace"] / "state.sqlite") as db:
        saved = dict(db.execute("SELECT key,payload FROM tuning"))
    assert len(saved) == 2
    assert not mod.data.read_json(args["workspace"] / "smoke_verified.json")["verified"]
    monkeypatch.setattr(mod, "fit_ridge", original)
    assert mod.run("smoke", **args) == 0
    with sqlite3.connect(args["workspace"] / "state.sqlite") as db:
        after = dict(db.execute("SELECT key,payload FROM tuning"))
    assert all(after[key] == value for key, value in saved.items())


def test_corrupt_completed_model_is_blocked_and_revokes_smoke_gate(fixture):
    _, _, args = fixture
    assert mod.run("smoke", **args) == 0
    model = args["workspace"] / "smoke/parts/outer0_baseline.joblib"
    model.write_bytes(b"corrupted artifact")
    with pytest.raises(ValueError, match="corrompida"):
        mod.run("smoke", **args)
    assert not mod.data.read_json(args["workspace"] / "smoke_verified.json")["verified"]
