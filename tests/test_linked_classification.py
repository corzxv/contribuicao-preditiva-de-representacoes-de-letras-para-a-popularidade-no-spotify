"""Exercita o ajuste e a retomada da classificação das quatro representações."""

import sqlite3
from contextlib import closing

import numpy as np
import polars as pl

from tcc_music_popularity import linked_classification as mod


def test_compare_covers_all_rows_and_resumes(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "WORKSPACE", tmp_path / "privado")
    monkeypatch.setattr(mod, "OUTPUT", tmp_path / "publico")
    mod.WORKSPACE.mkdir()
    mod.OUTPUT.mkdir()
    monkeypatch.setitem(mod.SETTINGS, "alphas", [0.1])
    monkeypatch.setattr(mod.regression, "E5", ("e5_000", "e5_001"))
    rng = np.random.default_rng(73)
    n = 90
    ids = np.arange(n)
    y = ids // 15 % 3
    frame = pl.DataFrame(
        {
            "track_id": [f"faixa{i:03d}" for i in ids],
            "text_component_id": [f"grupo{i:03d}" for i in ids],
            mod.data.TARGET: np.array([10.0, 25.0, 50.0])[y],
            "sampling_weight": np.ones(n),
            **{"model_" + c: rng.normal(size=n) for c in mod.data.NUMERIC},
            **{"model_" + c: [str(i % 3) for i in ids] for c in mod.data.CATEGORICAL},
            **{c: rng.normal(size=n) for c in (*mod.descriptors.FEATURES, *mod.regression.E5)},
        }
    )
    outer = ids % 5
    folds = frame.select("track_id", "text_component_id").with_columns(
        pl.Series("outer_fold", outer),
        *[pl.Series(f"inner_outer_{o}", np.where(outer == o, -1, ids // 5 % 3)) for o in range(5)],
    )
    with closing(sqlite3.connect(":memory:")) as db:
        result = mod.compare(frame, folds, y, db, "fixture")
        assert result["prediction_rows"] == n and result["models_evaluated"] == 5

        def already_trained(*args, **kwargs):
            raise AssertionError("A retomada deve ler as partes concluídas.")

        monkeypatch.setattr(mod.ordinal, "fit_model", already_trained)
        assert mod.compare(frame, folds, y, db, "fixture") == result
