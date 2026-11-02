import hashlib
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from tcc_music_popularity import observed_results as mod


@pytest.fixture
def bundle(tmp_path):
    reg = mod.reg
    n = 40
    y = 10.0 + np.arange(n) % 20
    weights = np.ones(n)
    weights[0] = 10
    common = pl.DataFrame(
        {
            "track_id": [f"t{i:03d}" for i in range(n)],
            "text_component_id": [f"g{i // 2:03d}" for i in range(n)],
            reg.data.TARGET: y,
            "sampling_weight": weights,
        }
    )
    folds = reg.data.make_folds(common)
    frame = common.with_columns(folds["outer_fold"])
    for model, offset in zip(reg.BLOCKS, (4.0, 3.9, 3.5, 3.4), strict=True):
        prediction = y + offset
        if model == "combined":
            prediction[0] = -1
        frame = frame.with_columns(pl.Series("prediction_" + model, prediction))
    for name in reg.REFERENCES:
        prediction = np.empty(n)
        for outer in range(5):
            train = y[folds["outer_fold"].to_numpy() != outer]
            value = np.mean(train) if name == "mean" else np.median(train)
            prediction[folds["outer_fold"].to_numpy() == outer] = value
        frame = frame.with_columns(pl.Series("prediction_" + name, prediction))
    metadata = common.with_columns(
        pl.Series("lyrics_language_status", ["english"] * 20 + ["non_english"] * 20),
        pl.Series("lyrics_detected_language", ["en"] * 20 + ["pt"] * 20),
        pl.Series("sampling_popularity_band", ["0_19" if v < 20 else "20_39" for v in y]),
        pl.lit("2000_2009").alias("sampling_period"),
        pl.Series("model_genre", ["rare"] + ["main"] * (n - 1)),
        *[pl.Series(c, [True] + [False] * (n - 1)) for c in mod.HISTORY],
        pl.Series(mod.UNKNOWN_HISTORY, [False, False, True] + [False] * (n - 3)),
    )
    base = tmp_path / "base"
    base.mkdir()
    metadata.write_parquet(base / "coorte_modelagem.parquet")
    folds.write_parquet(base / "folds_5x3.parquet")
    base_report = tmp_path / "base_report.json"
    reg.atomic_json(
        base_report,
        {
            "completed": True,
            "cohort_rows": n,
            "seal": {
                "code": reg.data.embeddings.base.sha256(Path(reg.data.__file__)),
                "protocol": reg.data.embeddings.base.sha256(reg.data.PROTOCOL),
            },
        },
    )
    work = tmp_path / "models"
    work.mkdir()
    pred_file = work / "predicoes_externas.parquet"
    frame.write_parquet(pred_file)
    public = tmp_path / "model_reports"
    public.mkdir()
    metrics = [
        {"model": name, **reg.metrics(y, frame["prediction_" + name], weights)}
        for name in mod.MODELS
    ]
    reg.data.write_csv(public / "metricas_externas.csv", metrics)
    by_name = {r["model"]: r for r in metrics}
    delta = [
        {
            "block": b,
            "reference": r,
            "delta_mae": by_name[b]["mae"] - by_name[r]["mae"],
            "delta_mae_original_weight": by_name[b]["mae_original_weight"]
            - by_name[r]["mae_original_weight"],
        }
        for b, r in mod.PAIRS
    ]
    reg.data.write_csv(public / "incrementos_pareados.csv", delta)
    alphas = [{"outer_fold": o, "block": b, "alpha": 1.0} for o in range(5) for b in reg.BLOCKS]
    reg.data.write_csv(public / "alphas_selecionados.csv", alphas)
    seal = {
        "inputs": {
            str(p.resolve()): reg.data.embeddings.base.sha256(p)
            for p in (base / "coorte_modelagem.parquet", base / "folds_5x3.parquet", base_report)
        },
        "code": {
            p.name: reg.data.embeddings.base.sha256(p)
            for p in (
                Path(reg.__file__),
                Path(reg.__file__).with_name("cohort_regression.py"),
                Path(reg.__file__).with_name("manual_lyrics.py"),
            )
        },
        "protocol": reg.data.embeddings.base.sha256(reg.PROTOCOL),
    }
    signature = mod.fingerprint(seal)
    parts = work / "parts"
    parts.mkdir()
    for outer in range(5):
        valid = frame.filter(pl.col("outer_fold") == outer)
        for name in mod.MODELS:
            stem = parts / f"outer{outer}_{name}"
            stem.with_suffix(".joblib").write_bytes(b"synthetic, not executable")
            predicted = valid.select("track_id", pl.col("prediction_" + name).alias("prediction"))
            predicted.write_parquet(stem.with_suffix(".parquet"))
            reg.atomic_json(
                stem.with_suffix(".json"),
                {
                    "signature": signature,
                    "outer": outer,
                    "block": name,
                    "details": {
                        "train_rows": n - valid.height,
                        "valid_rows": valid.height,
                        "selected_alpha": 1.0,
                    },
                    "model_sha256": reg.data.embeddings.base.sha256(stem.with_suffix(".joblib")),
                    "predictions_sha256": reg.data.embeddings.base.sha256(
                        stem.with_suffix(".parquet")
                    ),
                },
            )
    reg.atomic_json(
        public / "resumo_modelagem.json",
        {
            "completed": True,
            "mode": "all",
            "global_metrics_available": True,
            "completed_outer_blocks": 20,
            "pending_outer_blocks": 0,
            "prediction_rows": n,
            "source_rows": n,
            "seal": seal,
            "signature": signature,
            "predictions_sha256": reg.data.embeddings.base.sha256(pred_file),
        },
    )
    return frame, dict(
        base_workspace=base,
        base_report=base_report,
        regression_workspace=work,
        regression_output=public,
        workspace=tmp_path / "private",
        output=tmp_path / "public",
        expected=n,
    )


def test_component_deletion_equals_direct_recalculation_and_preserves_weighting(bundle):
    frame, _ = bundle
    components = mod.component_losses(frame)
    diagnostics = mod.deletion_diagnostics(components)
    row = next(r for r in diagnostics if r["block"] == "combined" and r["reference"] == "baseline")
    deltas, weighted = [], []
    for group in frame["text_component_id"].unique():
        rest = frame.filter(pl.col("text_component_id") != group)
        models = {
            m: mod.reg.metrics(
                rest[mod.reg.data.TARGET], rest["prediction_" + m], rest["sampling_weight"]
            )
            for m in ("combined", "baseline")
        }
        deltas.append(models["combined"]["mae"] - models["baseline"]["mae"])
        weighted.append(
            models["combined"]["mae_original_weight"] - models["baseline"]["mae_original_weight"]
        )
    assert row["min_delta_after_component_deletion"] == pytest.approx(min(deltas))
    assert row["max_delta_after_component_deletion"] == pytest.approx(max(deltas))
    assert row["min_weighted_delta_after_component_deletion"] == pytest.approx(min(weighted))
    assert row["max_weighted_delta_after_component_deletion"] == pytest.approx(max(weighted))
    assert row["delta_mae"] < 0 < row["delta_mae_original_weight"]


def test_full_audit_diagnostics_no_training_no_deserialization_or_source_changes(
    bundle, monkeypatch
):
    frame, paths = bundle
    monkeypatch.setattr(
        mod.reg.joblib, "load", lambda *args: pytest.fail("Não desserializar modelos")
    )
    monkeypatch.setattr(mod.reg.Ridge, "fit", lambda *args: pytest.fail("Não ajustar modelos"))
    source = paths["regression_workspace"] / "predicoes_externas.parquet"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    assert mod.run(**paths) == 0
    summary = mod.reg.data.read_json(paths["output"] / "resumo_diagnosticos.json")
    assert summary["completed"] and summary["cohort_rows"] == 40
    assert summary["verified_parts"] == 30 and summary["components"] == 20
    assert summary["metrics_reproduced"] and summary["published_cells"] == 5
    assert not summary["models_trained"] and not summary["confidence_intervals_computed"]
    assert not summary["predictions_recomputed"]
    small = pl.read_csv(paths["output"] / "celulas_pequenas.csv")
    exposed = small.filter(
        (pl.col("dimension") == "evaluation_component_history_status")
        & (pl.col("level") == "detected_collision")
    )
    assert exposed["n"][0] == 2  # propaga a exposição ao componente, não só à linha.
    unknown = small.filter(
        (pl.col("dimension") == "evaluation_component_history_status")
        & (pl.col("level") == "unknown_key")
    )
    assert unknown["n"][0] == 2
    bounds = pl.read_csv(paths["output"] / "previsoes_fora_intervalo.csv")
    assert bounds.filter(pl.col("model") == "combined")["below_zero"][0] == 1
    assert before == hashlib.sha256(source.read_bytes()).hexdigest()
    loss = pl.read_parquet(paths["workspace"] / "perdas_componentes.parquet")
    assert loss["n"].sum() == frame.height


def test_audit_rejects_modified_weight_even_with_updated_prediction_hash(bundle):
    _, paths = bundle
    file = paths["regression_workspace"] / "predicoes_externas.parquet"
    frame = pl.read_parquet(file).with_columns(
        (pl.col("sampling_weight") + 1).alias("sampling_weight")
    )
    frame.write_parquet(file)
    report = paths["regression_output"] / "resumo_modelagem.json"
    payload = mod.reg.data.read_json(report)
    payload["predictions_sha256"] = mod.reg.data.embeddings.base.sha256(file)
    mod.atomic_json(report, payload)
    with pytest.raises(ValueError, match="alvos/pesos/folds"):
        mod.run(**paths)


def test_audit_rejects_public_metric_corruption_and_incomplete_modeling(bundle):
    frame, paths = bundle
    file = paths["regression_output"] / "metricas_externas.csv"
    public = pl.read_csv(file).with_columns((pl.col("mae") + 1).alias("mae"))
    with pytest.raises(ValueError, match="Métrica pública não reproduzida"):
        mod.compare_metrics(frame, public)
    report = paths["regression_output"] / "resumo_modelagem.json"
    payload = mod.reg.data.read_json(report)
    mod.atomic_json(report, {**payload, "completed": False})
    with pytest.raises(ValueError, match="Modelagem integral incompleta"):
        mod.run(**paths)
