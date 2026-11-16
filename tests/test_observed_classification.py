import sqlite3

import numpy as np
import polars as pl
import pytest
from sklearn.metrics import log_loss

from tcc_music_popularity import observed_classification as mod


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    import socket

    monkeypatch.setattr(socket.socket, "connect", lambda *args: pytest.fail("Rede proibida"))
    monkeypatch.setattr(mod.regression, "E5", tuple(f"e5_{i:03d}" for i in range(4)))
    rng = np.random.default_rng(20261105)
    n = 90
    groups = np.repeat(np.arange(45), 2)
    labels = groups % 3
    columns = {
        "track_id": [f"faixa{i:03d}" for i in range(n)],
        "text_component_id": [f"grupo{g:03d}" for g in groups],
        mod.regression.data.TARGET: np.array([5.0, 25.0, 55.0])[labels],
        "sampling_weight": [1.0, 3.0, 8.0] * 30,
        **{"model_" + c: rng.normal(size=n) for c in mod.regression.data.NUMERIC},
        **{"model_" + c: [str(i % 3) for i in range(n)] for c in mod.regression.data.CATEGORICAL},
        **{c: rng.normal(size=n) for c in mod.regression.data.descriptors.FEATURES},
        **{c: rng.normal(size=n) for c in mod.regression.E5},
    }
    columns["model_year"] = labels + rng.normal(scale=0.3, size=n)
    frame = pl.DataFrame(columns)
    folds = frame.select("track_id", "text_component_id").with_columns(
        pl.Series("outer_fold", groups % 5),
        *[
            pl.Series(f"inner_outer_{outer}", np.where(groups % 5 == outer, -1, groups // 15))
            for outer in range(5)
        ],
    )
    source = tmp_path / "fonte.json"
    mod.common.atomic_json(source, {"fixture": True})
    monkeypatch.setattr(mod.regression, "load_sources", lambda *args: (frame, folds, [source]))
    configuration = tmp_path / "config.json"
    settings = mod.common.read_json(mod.CONFIG)
    settings.update(alphas=[0.1], expected_tracks=n, expected_components=45)
    mod.common.atomic_json(configuration, settings)
    readiness = tmp_path / "readiness.json"
    mod.common.atomic_json(
        readiness,
        {"completed": True, "observed_tracks": n, "operational_support_all_partitions": True},
    )
    pilot = tmp_path / "pilot.json"
    triage = tmp_path / "triage.json"
    for path in (pilot, triage):
        mod.common.atomic_json(path, {"completed": True})
    arguments = {
        "workspace": tmp_path / "privado",
        "output": tmp_path / "publico",
        "configuration": configuration,
        "readiness": readiness,
        "pilot": pilot,
        "triage": triage,
        "expected": n,
    }
    return frame, folds, arguments


def test_metricas_probabilisticas_e_sensibilidade():
    truth = np.array([0, 1, 2, 0])
    probabilities = np.array([[0.8, 0.1, 0.1], [0.2, 0.6, 0.2], [0.3, 0.5, 0.2], [0.2, 0.2, 0.6]])
    weights = np.array([1.0, 1.0, 9.0, 9.0])
    first, _ = mod.metrics(truth, probabilities)
    second, _ = mod.metrics(truth, probabilities, weights)
    assert first["log_loss"] == pytest.approx(log_loss(truth, probabilities))
    assert second["log_loss"] == pytest.approx(
        log_loss(truth, probabilities, sample_weight=weights)
    )
    assert first["accuracy"] != second["accuracy"]
    with pytest.raises(ValueError, match="Probabilidades"):
        mod.metrics(truth, probabilities * 2)


def test_pca_e_vocabulario_aprendidos_so_no_treino(bundle):
    frame, _, _ = bundle
    train = frame.head(60)
    valid = frame.tail(30).with_columns(
        pl.lit(1e10).alias("model_year"), pl.lit("inedito").alias("model_genre")
    )
    pipeline = mod.preprocessor("baseline", "pca95")
    pipeline.fit_transform(train.select(mod.regression.columns_for("baseline")))
    pipeline.transform(valid.select(mod.regression.columns_for("baseline")))
    transformers = pipeline.named_steps["columns"].named_transformers_
    numeric = transformers["metadata_numeric"]
    assert numeric.named_steps["scale"].mean_[0] == pytest.approx(train["model_year"].mean())
    assert numeric.named_steps["pca"].n_samples_ == 60
    assert "inedito" not in transformers["categorical"].named_steps["encode"].categories_[0]


def test_smoke_lote_retomada_e_metricas_reproduzidas(bundle, monkeypatch):
    _, _, arguments = bundle
    with pytest.raises(ValueError, match="smoke completo"):
        mod.run("all", **arguments)
    assert mod.run("smoke", **arguments) == 0
    smoke = mod.common.read_json(arguments["output"] / "smoke/resumo_classificacao.json")
    assert smoke["completed"] and not smoke["global_metrics_available"]
    assert smoke["reload_max_abs_difference"] == 0
    assert mod.run("all", limit_outer_blocks=1, **arguments) == 2
    partial = mod.common.read_json(arguments["output"] / "integral/resumo_classificacao.json")
    assert not partial["completed"] and not partial["global_metrics_available"]
    assert partial["completed_outer_blocks"] == 1
    assert mod.run("all", **arguments) == 0
    complete = mod.common.read_json(arguments["output"] / "integral/resumo_classificacao.json")
    assert complete["completed"] and complete["reused_outer_blocks"] == 1
    assert complete["models_evaluated"] == 5 and complete["prediction_rows"] == 90
    predicted = pl.read_parquet(arguments["workspace"] / "integral/probabilidades_externas.parquet")
    published = pl.read_csv(arguments["output"] / "integral/metricas_externas.csv")
    for block in (*mod.BLOCKS, mod.REFERENCE):
        probabilities = predicted.select(
            [block + "_probability_" + str(i) for i in range(3)]
        ).to_numpy()
        result, _ = mod.metrics(predicted["observed_class"].to_numpy(), probabilities)
        row = published.filter(
            (pl.col("model") == block)
            & (pl.col("weighting") == "equal_tracks")
            & (pl.col("outer_fold") == -1)
        ).row(0, named=True)
        assert row["balanced_accuracy"] == pytest.approx(result["balanced_accuracy"])
        assert row["log_loss"] == pytest.approx(result["log_loss"])
    digest = complete["prediction_sha256"]
    monkeypatch.setattr(mod, "fit_model", lambda *args: pytest.fail("Reajuste indevido"))
    assert mod.run("all", **arguments) == 0
    assert (
        mod.common.read_json(arguments["output"] / "integral/resumo_classificacao.json")[
            "prediction_sha256"
        ]
        == digest
    )


def test_interrupcao_preserva_ajustes_confirmados(bundle, monkeypatch):
    _, _, arguments = bundle
    original = mod.fit_model
    calls = 0

    def interrupted(*args):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise KeyboardInterrupt()
        return original(*args)

    monkeypatch.setattr(mod, "fit_model", interrupted)
    with pytest.raises(KeyboardInterrupt):
        mod.run("smoke", **arguments)
    with sqlite3.connect(arguments["workspace"] / "state.sqlite") as database:
        assert database.execute("SELECT count(*) FROM tuning").fetchone()[0] == 2
    summary = mod.common.read_json(arguments["output"] / "smoke/resumo_classificacao.json")
    assert not summary["completed"] and summary["error_type"] == "KeyboardInterrupt"
    monkeypatch.setattr(mod, "fit_model", original)
    assert mod.run("smoke", **arguments) == 0


def test_parte_corrompida_nao_e_refeita_silenciosamente(tmp_path):
    frame = pl.DataFrame({"track_id": ["a", "b"]})
    probabilities = np.array([[0.5, 0.3, 0.2], [0.1, 0.1, 0.8]])
    mod.save_part(
        tmp_path, "assinatura", 0, "baseline", {"fixture": True}, frame, probabilities, {}
    )
    assert mod.read_part(tmp_path, "assinatura", 0, "baseline", frame) is not None
    path = tmp_path / "outer0_baseline.joblib"
    path.write_bytes(b"arquivo alterado")
    with pytest.raises(ValueError, match="corrompida"):
        mod.read_part(tmp_path, "assinatura", 0, "baseline", frame)
    assert path.read_bytes() == b"arquivo alterado"
