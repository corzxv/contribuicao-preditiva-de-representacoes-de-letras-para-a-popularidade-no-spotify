"""One frozen holdout evaluation: prediction is sealed before target access."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import polars as pl
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, r2_score
from threadpoolctl import threadpool_limits

from .config import PROJECT_ROOT, project_path
from .final_study_v040 import _atomic_write_frame
from .io import read_json, sha256_file, utc_now, write_json

MODEL_COMMIT = "9c6d16e1eb5c7c8d6b86559f5ac40ac7f7fda4db"
MODEL_TAG = "final-models-pre-holdout-v0.5"
MANIFEST = "reports/final_model_manifest_v0_5.json"
DEVELOPMENT_SUMMARY = "reports/run_summary_final_development_v0_5.json"
PLAN = "reports/final_holdout_evaluation_plan_v0_5.md"
EVALUATOR = "src/tcc_music_popularity/final_holdout_v060.py"
ROOT = "data/derived/private_final_holdout_v0_6"
DEVELOPMENT_ROOT = "data/derived/private_final_development_v0_5"
SUMMARY = "reports/run_summary_final_holdout_v0_6.json"
SEED = 20261013
REPETITIONS = 2000
ADJUSTED_QUANTILES = (0.008333333, 0.991666667)
PREDICTOR_TARGETS = {"spotify_popularity", "genius_lyrics_views", "lfm_playcount"}
KEYS = ["composition_key", "track_id", "spotify_row_id"]
BLOCKS = ["baseline", "traditional", "deep", "combined"]
EXPECTED_MODELS = {
    f"{algorithm}__{block}" for algorithm in ("elastic_net", "ridge") for block in BLOCKS
} | {"dummy__baseline"}


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def private(name: str) -> Path:
    path = project_path(f"{ROOT}/{name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def existing_private(name: str) -> Path:
    return project_path(f"{DEVELOPMENT_ROOT}/{name}")


def code_has_no_training_calls(path: str | Path = EVALUATOR) -> dict:
    path = project_path(str(path)) if not Path(path).is_absolute() else Path(path)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = {"fit", "fit_transform", "partial_fit", "train", "tune", "tuning"}
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = (
                func.attr
                if isinstance(func, ast.Attribute)
                else func.id
                if isinstance(func, ast.Name)
                else ""
            )
            if name in forbidden:
                found.append({"line": node.lineno, "call": name})
    ensure(not found, "Avaliador contém chamada de treinamento proibida.")
    return {"forbidden_training_calls": 0}


def privacy_audit() -> dict:
    def entries(arguments):
        return subprocess.run(
            ["git", *arguments], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True
        ).stdout.splitlines()

    def forbidden(value):
        return (
            value.startswith(
                ("data/derived/", "data/raw/lyrics_private/", "data/interim/lyrics_private/")
            )
            or value.endswith((".parquet", ".joblib", ".npz", ".npy", ".pkl"))
            or value in (".env", "exp_base.py")
        )

    tracked, staged = entries(["ls-files"]), entries(["diff", "--cached", "--name-only"])
    ensure(not any(forbidden(value) for value in tracked), "Arquivo privado tracked.")
    ensure(not any(forbidden(value) for value in staged), "Arquivo privado staged.")
    return {"private_tracked": 0, "private_staged": 0}


def current_versions() -> dict:
    names = ("numpy", "polars", "pyarrow", "scikit-learn", "scipy", "joblib", "threadpoolctl")
    return {name: importlib.metadata.version(name) for name in names} | {
        "python": sys.version.split()[0]
    }


def frozen_hashes() -> dict[str, str]:
    seal = read_json(f"{DEVELOPMENT_ROOT}/execution_seal.json")
    development = read_json(DEVELOPMENT_SUMMARY)
    manifest = read_json(MANIFEST)
    ensure(
        development["status"] == "complete_models_frozen_pre_holdout",
        "Desenvolvimento não concluído.",
    )
    hashes = dict(seal["input_hashes"])
    hashes.update(
        {f"{DEVELOPMENT_ROOT}/{name}": value for name, value in seal["data_hashes"].items()}
    )
    hashes.update(seal["code_hashes"])
    hashes[f"{DEVELOPMENT_ROOT}/oof_predictions.parquet"] = development["oof_file_sha256"]
    hashes[f"{DEVELOPMENT_ROOT}/execution_seal.json"] = development["private_integrity_hashes"][
        "execution_seal"
    ]
    ensure(
        sha256_file(project_path("configs/final_development_v0_5.yaml"))
        == seal["configuration_sha256"],
        "Configuração congelada mudou.",
    )
    hashes["configs/final_development_v0_5.yaml"] = seal["configuration_sha256"]
    for item in manifest["models"]:
        hashes[f"{DEVELOPMENT_ROOT}/models/{item['model']}.joblib"] = item["model_sha256"]
    for path, expected in hashes.items():
        ensure(
            sha256_file(project_path(path)) == expected,
            f"Artefato congelado divergente: {Path(path).name}.",
        )
    return hashes


def validate_keys(frame: pl.DataFrame, expected: int) -> None:
    ensure(frame.height == expected, "Cardinalidade divergente.")
    for key in KEYS:
        ensure(
            frame[key].null_count() == 0 and frame[key].n_unique() == expected,
            "Chaves ausentes/duplicadas.",
        )


def preflight() -> dict:
    tag_commit = subprocess.run(
        ["git", "rev-parse", f"{MODEL_TAG}^{{}}"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    ensure(tag_commit == MODEL_COMMIT, "Tag de modelos aponta para outro checkpoint.")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", MODEL_COMMIT, "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
    )
    # Compare authorities with the committed blobs, not just another mutable local file.
    for path in (
        MANIFEST,
        PLAN,
        DEVELOPMENT_SUMMARY,
        "reports/final_analysis_protocol_v1_0.md",
        "reports/final_sampling_protocol_v1_0.md",
        "reports/final_matrix_audit_v0_5.md",
        "reports/final_development_report_v0_5.md",
    ):
        blob = subprocess.run(
            ["git", "show", f"{MODEL_COMMIT}:{path}"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        actual = project_path(path).read_bytes().replace(b"\r\n", b"\n")
        ensure(
            blob.replace(b"\r\n", b"\n") == actual, "Autoridade documental divergiu do checkpoint."
        )
    manifest = read_json(MANIFEST)
    ensure(manifest["candidate"] == "elastic_net__traditional", "Candidato principal mudou.")
    ensure(manifest["prediction_policy"] == "raw_unclipped", "Política de previsão mudou.")
    ensure(
        {item["model"] for item in manifest["models"]} == EXPECTED_MODELS
        and len(manifest["models"]) == 9,
        "Modelos congelados divergentes.",
    )
    ensure(current_versions() == manifest["versions"], "Ambiente difere do desenvolvimento.")
    hashes = frozen_hashes()
    hold = pl.read_parquet(existing_private("holdout_features.parquet"))
    ensure(not PREDICTOR_TARGETS & set(hold.columns), "Features do holdout contêm alvo/proxy.")
    validate_keys(hold, 2592)
    ensure(
        set(hold["split"]) == {"holdout_test"} and hold["artist_group_id"].n_unique() == 1308,
        "Split/artistas do holdout divergentes.",
    )
    dev = pl.read_parquet(
        existing_private("development_matrix.parquet"),
        columns=["composition_key", "artist_group_id", "lyrics_sha256"],
    )
    overlap = {name: len(set(hold[name]) & set(dev[name])) for name in dev.columns}
    ensure(not any(overlap.values()), "Sobreposição entre desenvolvimento e holdout.")
    # Only keys and assignments are loaded from the original split and representative list.
    assignment = pl.read_parquet(
        project_path("data/processed/split_assignments_v0_1_1.parquet"),
        columns=[*KEYS, "artist_group_id", "split"],
    )
    assigned = hold.select([*KEYS, "artist_group_id", "split"]).join(
        assignment, on=KEYS, how="left", validate="1:1", suffix="_sealed"
    )
    ensure(
        assigned.height == 2592 and assigned["split_sealed"].null_count() == 0,
        "Representante ausente no split.",
    )
    ensure(
        (assigned["split"] == assigned["split_sealed"]).all()
        and (assigned["artist_group_id"] == assigned["artist_group_id_sealed"]).all(),
        "Atribuição divergente.",
    )
    index = (
        pl.read_parquet(
            project_path("data/derived/private_final_study/final_lyrics_index_v0_4.parquet"),
            columns=["composition_key", "representative_track_id", "split"],
        )
        .filter(pl.col("split") == "holdout_test")
        .rename({"representative_track_id": "track_id"})
    )
    checked = hold.select("composition_key", "track_id").join(
        index, on=["composition_key", "track_id"], how="left", validate="1:1"
    )
    ensure(
        checked["split"].null_count() == 0 and checked.height == 2592,
        "Representantes diferem das letras aceitas.",
    )
    for item in manifest["models"]:
        ensure(not set(item["input_columns"]) & PREDICTOR_TARGETS, "Alvo/proxy como preditor.")
        ensure(set(item["input_columns"]).issubset(hold.columns), "Feature exigida ausente.")
        if item.get("input_schema"):
            ensure(
                all(
                    str(hold.schema[name]) == dtype for name, dtype in item["input_schema"].items()
                ),
                "Schema incompatível.",
            )
    code_audit = code_has_no_training_calls()
    previous = read_json(SUMMARY, {})
    opening = read_json(private("holdout_opening_record.json"), {})
    if not previous and not opening:
        other = [
            path
            for path in project_path("reports").glob("*holdout*v0_6*")
            if path.name != Path(SUMMARY).name
        ]
        ensure(not other, "Resultado V0.6 anterior sem registro correspondente.")
    return {
        "model_checkpoint_commit": MODEL_COMMIT,
        "model_checkpoint_tag": MODEL_TAG,
        "models": 9,
        "rows": 2592,
        "artists": 1308,
        "overlap_counts": overlap,
        "frozen_hashes": hashes,
        "versions": current_versions(),
        "schema_compatible": True,
        "holdout_features_target_free": True,
        "candidate": manifest["candidate"],
        "evaluator_sha256": sha256_file(project_path(EVALUATOR)),
        "evaluation_plan_sha256": sha256_file(project_path(PLAN)),
        "model_manifest_sha256": sha256_file(project_path(MANIFEST)),
        "privacy": privacy_audit(),
        "training_calls": code_audit,
        "previous_completed_evaluation": previous.get("status") == "complete",
        "target_already_opened": bool(opening),
        "ordered_keys_sha256": hashlib.sha256(
            hold.select(KEYS).write_csv().encode("utf-8")
        ).hexdigest(),
    }


def predict_frozen(
    frame: pl.DataFrame, manifest: dict, loader: Any = joblib.load, model_root: Path | None = None
) -> pl.DataFrame:
    ensure(not PREDICTOR_TARGETS & set(frame.columns), "Predição deve anteceder o alvo.")
    result = frame.select([*KEYS, "artist_group_id"])
    root = model_root or existing_private("models")
    for item in manifest["models"]:
        model = loader(root / f"{item['model']}.joblib")
        x = frame.select(item["input_columns"])
        prediction = np.asarray(
            model.predict(x.to_numpy() if item["algorithm"] == "dummy" else x), dtype=np.float64
        )
        ensure(
            prediction.shape == (frame.height,) and np.isfinite(prediction).all(),
            "Vetor de previsões incompleto/não finito.",
        )
        result = result.with_columns(pl.Series(f"prediction__{item['model']}", prediction))
    ensure(
        result.select(KEYS).equals(frame.select(KEYS)),
        "Ordem das chaves alterada durante previsão.",
    )
    return result


def verify_prediction_seal(seal: dict) -> None:
    ensure(seal["status"] == "predictions_sealed_before_target", "Selo de previsões inválido.")
    ensure(
        seal["evaluator_sha256"] == sha256_file(project_path(EVALUATOR)),
        "Avaliador mudou após selo.",
    )
    ensure(
        seal["evaluation_plan_sha256"] == sha256_file(project_path(PLAN)), "Plano mudou após selo."
    )
    ensure(
        seal["model_manifest_sha256"] == sha256_file(project_path(MANIFEST)),
        "Manifesto mudou após selo.",
    )
    ensure(
        sha256_file(private("predictions_pre_target.parquet")) == seal["predictions_sha256"],
        "Previsões seladas mudaram.",
    )
    ensure(frozen_hashes() == seal["frozen_hashes"], "Artefatos congelados mudaram.")


def save_predictions_before_target() -> dict:
    audit = preflight()
    existing = read_json(private("prediction_seal.json"))
    if existing:
        verify_prediction_seal(existing)
        return {**existing, "idempotent_reuse": True}
    ensure(not audit["target_already_opened"], "Alvo já aberto sem selo: interromper.")
    path = private("predictions_pre_target.parquet")
    ensure(not path.exists(), "Arquivo de previsões sem selo; não sobrescrever.")
    hold = pl.read_parquet(existing_private("holdout_features.parquet"))
    with threadpool_limits(limits=2):
        prediction = predict_frozen(hold, read_json(MANIFEST))
    _atomic_write_frame(prediction, path)
    persisted = pl.read_parquet(path)
    ensure(persisted.equals(prediction), "Persistência das previsões divergente.")
    ensure(frozen_hashes() == audit["frozen_hashes"], "Modelo/entrada mudou durante predict.")
    seal = {
        **audit,
        "status": "predictions_sealed_before_target",
        "sealed_at": utc_now(),
        "predictions_sha256": sha256_file(path),
        "target_opened_at_sealing": False,
        "prediction_policy": "raw_unclipped",
        "outside_range": {
            item["model"]: {
                "below_zero": int((prediction[f"prediction__{item['model']}"] < 0).sum()),
                "above_100": int((prediction[f"prediction__{item['model']}"] > 100).sum()),
            }
            for item in read_json(MANIFEST)["models"]
        },
    }
    write_json(private("prediction_seal.json"), seal)
    return seal


def align_target(predictions: pl.DataFrame, target: pl.DataFrame) -> tuple[pl.DataFrame, dict]:
    ensure(
        set(target.columns) == {"track_id", "spotify_row_id", "spotify_popularity"},
        "Projeção do alvo inválida.",
    )
    ensure(
        target.height == predictions.height,
        "Cardinalidade do alvo divergiu; não excluir registros.",
    )
    ensure(
        target.select("track_id", "spotify_row_id").unique().height == target.height,
        "Chaves do alvo duplicadas.",
    )
    # Explicit ordinal restores exactly the sealed prediction-key order after the join.
    joined = (
        predictions.with_row_index("_sealed_order")
        .join(target, on=["track_id", "spotify_row_id"], how="left", validate="1:1")
        .sort("_sealed_order")
        .drop("_sealed_order")
    )
    ensure(
        joined.height == predictions.height
        and joined.select(KEYS).equals(predictions.select(KEYS)),
        "Join alterou linhas/chaves.",
    )
    ensure(joined["spotify_popularity"].null_count() == 0, "Alvo ausente; não imputar/excluir.")
    y = joined["spotify_popularity"].to_numpy().astype(float)
    ensure(
        np.isfinite(y).all() and np.all((y >= 0) & (y <= 100)),
        "Alvo inválido; não corrigir/substituir.",
    )
    return joined, {
        "rows": joined.height,
        "join": "1:1 por track_id e spotify_row_id",
        "missing_target": 0,
        "lost_rows": 0,
        "multiplied_rows": 0,
        "finite_target": True,
        "target_in_0_100": True,
        "keys_and_order_preserved": True,
    }


def open_target_once() -> tuple[pl.DataFrame, dict]:
    seal = read_json(private("prediction_seal.json"))
    ensure(seal is not None, "Salvar/selar previsões antes de abrir o alvo.")
    verify_prediction_seal(seal)
    opening = read_json(private("holdout_opening_record.json"))
    if opening is None:
        opening = {
            "status": "target_access_started",
            "opened_at": utc_now(),
            "prediction_sealed_at": seal["sealed_at"],
            "predictions_sha256": seal["predictions_sha256"],
            "evaluator_sha256": seal["evaluator_sha256"],
            "evaluation_plan_sha256": seal["evaluation_plan_sha256"],
            "model_manifest_sha256": seal["model_manifest_sha256"],
            "authorization": "user V0.6 request",
            "method_changes_allowed": False,
        }
        write_json(private("holdout_opening_record.json"), opening)
    ensure(
        opening["predictions_sha256"] == seal["predictions_sha256"],
        "Abertura registrada para outras previsões.",
    )
    predictions = pl.read_parquet(private("predictions_pre_target.parquet"))
    path = private("holdout_target_raw.parquet")
    try:
        if path.exists():
            ensure(
                opening.get("target_sha256") == sha256_file(path),
                "Alvo privado não corresponde ao registro de abertura.",
            )
            target = pl.read_parquet(path)
        else:
            target = (
                pl.scan_parquet(project_path("data/processed/modeling_base_lfm_v0_1_1.parquet"))
                .select("track_id", "spotify_row_id", "spotify_popularity")
                .filter(
                    pl.col("track_id").is_in(predictions["track_id"].to_list())
                    & pl.col("spotify_row_id").is_in(predictions["spotify_row_id"].to_list())
                )
                .collect()
            )
            _atomic_write_frame(target, path)
            opening["target_sha256"] = sha256_file(path)
            write_json(private("holdout_opening_record.json"), opening)
        joined, audit = align_target(predictions, target)
        opening.update(
            {"status": "target_validated", "validated_at": utc_now(), "join_audit": audit}
        )
        write_json(private("holdout_opening_record.json"), opening)
        return joined, opening
    except Exception as error:
        opening.update(
            {
                "status": "target_access_failed",
                "failure_type": type(error).__name__,
                "failure_at": utc_now(),
            }
        )
        write_json(private("holdout_opening_record.json"), opening)
        raise


def metrics(y: np.ndarray, predicted: np.ndarray) -> dict:
    y, predicted = np.asarray(y, dtype=float), np.asarray(predicted, dtype=float)
    ensure(
        y.shape == predicted.shape and y.ndim == 1 and len(y) > 1,
        "Métricas exigem vetores alinhados.",
    )
    ensure(np.isfinite(y).all() and np.isfinite(predicted).all(), "Vetor não finito.")
    rho = float(spearmanr(y, predicted).statistic) if np.ptp(y) and np.ptp(predicted) else None
    return {
        "n": len(y),
        "mae": float(mean_absolute_error(y, predicted)),
        "rmse": float(np.sqrt(np.mean((y - predicted) ** 2))),
        "r2": float(r2_score(y, predicted)),
        "spearman": rho,
        "mean_residual": float(np.mean(y - predicted)),
        "predictions_below_zero": int(np.sum(predicted < 0)),
        "predictions_above_100": int(np.sum(predicted > 100)),
        "predictions_outside_0_100": int(np.sum((predicted < 0) | (predicted > 100))),
    }


def bootstrap_weights(
    groups: np.ndarray, *, repetitions: int = REPETITIONS, seed: int = SEED
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    unique, inverse = np.unique(groups, return_inverse=True)
    ensure(len(unique) > 1, "Bootstrap exige mais de um artista.")
    weights = np.random.default_rng(seed).multinomial(
        len(unique), np.full(len(unique), 1 / len(unique)), size=repetitions
    )
    ensure(np.all(weights.sum(axis=1) == len(unique)), "Multiplicidade dos sorteios inválida.")
    return unique, inverse, weights


def paired_draws(
    y: np.ndarray,
    reference: np.ndarray,
    candidate: np.ndarray,
    inverse: np.ndarray,
    weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    counts = np.bincount(inverse, minlength=weights.shape[1])
    denominator = weights @ counts
    ensure(np.all(denominator > 0), "Sorteio sem composições.")
    ref_abs = np.bincount(inverse, weights=np.abs(y - reference), minlength=weights.shape[1])
    cand_abs = np.bincount(inverse, weights=np.abs(y - candidate), minlength=weights.shape[1])
    ref_sq = np.bincount(inverse, weights=(y - reference) ** 2, minlength=weights.shape[1])
    cand_sq = np.bincount(inverse, weights=(y - candidate) ** 2, minlength=weights.shape[1])
    mae = (weights @ cand_abs - weights @ ref_abs) / denominator
    rmse = np.sqrt((weights @ cand_sq) / denominator) - np.sqrt((weights @ ref_sq) / denominator)
    return mae, rmse


def comparison(
    y: np.ndarray,
    reference: np.ndarray,
    candidate: np.ndarray,
    inverse: np.ndarray,
    weights: np.ndarray,
    *,
    primary: bool,
) -> tuple[dict, np.ndarray, np.ndarray]:
    mae, rmse = paired_draws(y, reference, candidate, inverse, weights)
    rm, cm = metrics(y, reference), metrics(y, candidate)
    descriptive_mae, descriptive_rmse = (
        np.quantile(mae, [0.025, 0.975]),
        np.quantile(rmse, [0.025, 0.975]),
    )
    adjusted = np.quantile(mae, ADJUSTED_QUANTILES) if primary else [None, None]
    delta = cm["mae"] - rm["mae"]
    confirmed = bool(adjusted[1] < 0) if primary else None
    out = {
        "mae_difference": delta,
        "mae_relative_percent": 100 * delta / rm["mae"] if rm["mae"] else None,
        "rmse_difference": cm["rmse"] - rm["rmse"],
        "mae_ci95_low": float(descriptive_mae[0]),
        "mae_ci95_high": float(descriptive_mae[1]),
        "rmse_ci95_low": float(descriptive_rmse[0]),
        "rmse_ci95_high": float(descriptive_rmse[1]),
        "mae_bonferroni_low": float(adjusted[0]) if primary else None,
        "mae_bonferroni_high": float(adjusted[1]) if primary else None,
        "primary": primary,
        "gain_confirmed_by_frozen_rule": confirmed,
        "repetitions": len(weights),
        "seed": SEED,
        "artist_groups": weights.shape[1],
        "composition_weighted": True,
    }
    return out, mae, rmse


def period(year: int) -> str:
    if year < 2000:
        return "antes de 2000"
    if year < 2010:
        return "2000–2009"
    if year < 2020:
        return "2010–2019"
    return "2020 ou posterior"


def aggregate_diagnostics(frame: pl.DataFrame, hold: pl.DataFrame, model_names: list[str]) -> dict:
    # Keyed join: never depend on holdout matrix and prediction positional equivalence.
    checked = frame.join(hold.select([*KEYS, "year", "genre"]), on=KEYS, how="left", validate="1:1")
    ensure(
        checked.height == frame.height and checked["year"].null_count() == 0,
        "Diagnósticos não alinham por chaves.",
    )
    y = checked["spotify_popularity"].to_numpy()
    out = {
        "minimum_cell_size": 30,
        "subgroups_exploratory": True,
        "period": [],
        "genre": [],
        "observed_predicted_bins": [],
        "residual_histograms": [],
        "absolute_error_quantiles": [],
    }
    for dimension, labels in (
        ("period", np.array([period(int(value)) for value in checked["year"]])),
        ("genre", checked["genre"].to_numpy()),
    ):
        for label in sorted(set(labels), key=str):
            mask = labels == label
            if mask.sum() < 30:
                continue
            for name in model_names:
                out[dimension].append(
                    {
                        "category": str(label),
                        "model": name,
                        **metrics(y[mask], checked[f"prediction__{name}"].to_numpy()[mask]),
                    }
                )
    for name in model_names:
        pred = checked[f"prediction__{name}"].to_numpy()
        errors = y - pred
        abs_errors = np.abs(errors)
        out["absolute_error_quantiles"].append(
            {
                "model": name,
                "q25": float(np.quantile(abs_errors, 0.25)),
                "q50": float(np.quantile(abs_errors, 0.5)),
                "q75": float(np.quantile(abs_errors, 0.75)),
                "q90": float(np.quantile(abs_errors, 0.9)),
                "q95": float(np.quantile(abs_errors, 0.95)),
            }
        )
        histogram = np.histogram(
            errors, bins=[-np.inf, -40, -30, -20, -10, -5, 0, 5, 10, 20, 30, 40, np.inf]
        )[0]
        out["residual_histograms"].append(
            {
                "model": name,
                "bins": [
                    "<−40",
                    "−40 a −30",
                    "−30 a −20",
                    "−20 a −10",
                    "−10 a −5",
                    "−5 a 0",
                    "0 a 5",
                    "5 a 10",
                    "10 a 20",
                    "20 a 30",
                    "30 a 40",
                    "≥40",
                ],
                "counts": histogram.tolist(),
            }
        )
        for start in range(0, 100, 10):
            mask = (y >= start) & ((y < start + 10) if start < 90 else (y <= 100))
            if mask.sum() >= 30:
                out["observed_predicted_bins"].append(
                    {
                        "model": name,
                        "observed_bin": f"{start}–{start + 10}",
                        "n": int(mask.sum()),
                        "mean_observed": float(y[mask].mean()),
                        "mean_predicted": float(pred[mask].mean()),
                        "mae": float(abs_errors[mask].mean()),
                    }
                )
    return out


def clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(item) for item in value]
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        return None
    return value


def write_csv(name: str, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with project_path(f"reports/{name}").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: Any, digits: int = 4) -> str:
    return (
        "não definida"
        if value is None
        else f"{value:.{digits}f}"
        if isinstance(value, (float, np.floating))
        else str(value)
    )


def table(headers: list[str], rows: list[list]) -> str:
    return (
        "| "
        + " | ".join(headers)
        + " |\n|"
        + "---|" * len(headers)
        + "\n"
        + "\n".join("| " + " | ".join(fmt(value) for value in row) + " |" for row in rows)
    )


def conclusion(item: dict) -> str:
    if item["gain_confirmed_by_frozen_rule"]:
        return "Ganho incremental confirmado pelo critério congelado nesta amostra."
    if item["mae_bonferroni_low"] > 0:
        return "O intervalo ajustado indica erro maior que o Baseline nesta amostra; ganho incremental não confirmado."
    return "Ganho incremental não confirmado; o intervalo ajustado inclui zero. Isso não demonstra equivalência nem ausência universal de contribuição das letras."


def create_figures(summary: dict) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    root = project_path("reports/figures/final_holdout_v0_6")
    root.mkdir(parents=True, exist_ok=True)
    paths = []

    def save(fig, name):
        fig.tight_layout()
        path = root / name
        fig.savefig(path, dpi=160)
        plt.close(fig)
        paths.append(path.relative_to(PROJECT_ROOT).as_posix())

    main = [row for row in summary["metrics"] if row["algorithm"] == "elastic_net"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, metric in zip(axes, ("mae", "rmse"), strict=True):
        ax.bar([row["block"] for row in main], [row[metric] for row in main], color="#276a91")
        ax.set_ylabel(metric.upper())
        ax.set_title("Holdout: Elastic Net congelado")
        ax.tick_params(axis="x", rotation=15)
    save(fig, "elastic_net_metrics.png")
    primary = [row for row in summary["comparisons"] if row["primary"]]
    fig, ax = plt.subplots(figsize=(8, 4))
    centers = np.array([row["mae_difference"] for row in primary])
    lows = np.array([row["mae_bonferroni_low"] for row in primary])
    highs = np.array([row["mae_bonferroni_high"] for row in primary])
    ax.hlines(np.arange(3), lows, highs, color="#276a91", linewidth=2)
    ax.scatter(centers, np.arange(3), color="#276a91", zorder=3)
    ax.set_yticks(np.arange(3), [row["block"] for row in primary])
    ax.axvline(0, color="gray", linestyle="--")
    ax.set_xlabel("ΔMAE textual − Baseline (negativo favorece textual)")
    ax.set_title("Bootstrap por artista: IC Bonferroni 98,333333%")
    save(fig, "primary_mae_adjusted_intervals.png")
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, row in zip(axes.flat, main, strict=True):
        histogram = next(
            r for r in summary["diagnostics"]["residual_histograms"] if r["model"] == row["model"]
        )
        ax.bar(range(len(histogram["counts"])), histogram["counts"], color="#276a91")
        ax.set_xticks(range(len(histogram["bins"])), histogram["bins"], rotation=75, fontsize=7)
        ax.set_title(row["block"])
        ax.set_ylabel("Composições")
    save(fig, "residual_distributions.png")
    fig, ax = plt.subplots(figsize=(7, 5))
    for row in main:
        bins = [
            r
            for r in summary["diagnostics"]["observed_predicted_bins"]
            if r["model"] == row["model"]
        ]
        ax.plot(
            [r["mean_observed"] for r in bins],
            [r["mean_predicted"] for r in bins],
            "o-",
            label=row["block"],
        )
    ax.plot([0, 100], [0, 100], "--", color="gray")
    ax.set_xlabel("Popularidade observada média por bin (n≥30)")
    ax.set_ylabel("Popularidade prevista média por bin")
    ax.legend()
    save(fig, "observed_predicted_aggregated.png")
    return paths


LIMITATIONS = """A inferência se restringe à amostra com letras aceitas, condicionada à disponibilidade, às regras de matching e à coleta. Falhas HTTP e ambiguidades podem gerar seleção. Há predominância do inglês; MiniLM pode representar outros idiomas com qualidade diferente. Os descritores LFM2b e os embeddings LRCLIB podem derivar de versões distintas da letra. Uma faixa Spotify representa cada composição, com chave operacional que não é identificador universal. As escolhas metodológicas foram orientadas pelos pilotos. O teste agrupado por artista avalia popularidade observada no snapshot da fonte; não é validação prospectiva de sucesso comercial nem demonstra previsão de sucesso futuro de lançamentos. As conclusões são preditivas e associativas, sem interpretação causal."""


def write_reports(summary: dict) -> None:
    values = summary["metrics"]
    metrics_table = table(
        ["Modelo", "MAE", "RMSE", "R²", "Spearman", "Resíduo médio", "<0", ">100"],
        [
            [
                r["model"],
                *[
                    r[name]
                    for name in (
                        "mae",
                        "rmse",
                        "r2",
                        "spearman",
                        "mean_residual",
                        "predictions_below_zero",
                        "predictions_above_100",
                    )
                ],
            ]
            for r in values
        ],
    )
    comparisons_table = table(
        [
            "Modelo − Baseline",
            "Primária",
            "ΔMAE",
            "ΔMAE %",
            "IC95% ΔMAE",
            "IC98,333333% ΔMAE",
            "ΔRMSE",
            "IC95% ΔRMSE",
        ],
        [
            [
                r["model"],
                r["primary"],
                r["mae_difference"],
                r["mae_relative_percent"],
                f"[{fmt(r['mae_ci95_low'])}; {fmt(r['mae_ci95_high'])}]",
                f"[{fmt(r['mae_bonferroni_low'])}; {fmt(r['mae_bonferroni_high'])}]"
                if r["primary"]
                else "secundária; sem ajuste",
                r["rmse_difference"],
                f"[{fmt(r['rmse_ci95_low'])}; {fmt(r['rmse_ci95_high'])}]",
            ]
            for r in summary["comparisons"]
        ],
    )
    methods = """Foram avaliados nove estimadores congelados no desenvolvimento: quatro Elastic Net primários, quatro Ridge secundários e DummyRegressor pela média de desenvolvimento. As configurações correspondem a metadados/áudio (Baseline), Baseline e 196 descritores LFM2b (Tradicional), Baseline e 384 dimensões MiniLM (Profundo), e os dois blocos textuais (Combinado). PCAs de 90% foram ajustadas separadamente dentro do desenvolvimento; nenhum pré-processamento foi ajustado no teste. O candidato predefinido elastic_net__traditional permanece inalterado.

As previsões brutas foram persistidas e seladas antes do acesso ao alvo. A popularidade foi projetada exclusivamente para os representantes congelados e unida por track_id e spotify_row_id, com join 1:1. MAE é primária; RMSE, R² e Spearman são secundárias/descritivas. Resíduo = observado − previsto; valor positivo indica subestimação. Spearman é não definida quando o vetor previsto é constante (Dummy). Previsões fora de 0–100 foram mantidas.

O bootstrap pareado por artista utiliza 2.000 reamostragens com seed 20261013. Sorteiam-se 1.308 grupos com reposição em cada reamostragem, incluindo todas as composições de cada grupo e preservando sua multiplicidade. Os mesmos sorteios são usados em todas as comparações; métricas permanecem ponderadas por composição. IC95% são descritivos. Nas três comparações primárias de MAE, usa-se Bonferroni: intervalos bilaterais de 98,333333% nos quantis 0,008333333 e 0,991666667. Ganho confirmado exige limite superior ajustado menor que zero. Os intervalos avaliam a incerteza do teste para modelos congelados e não toda a variabilidade de repetir o treinamento. Intervalo contendo zero não demonstra equivalência, ausência universal de efeito ou inutilidade das letras.
"""
    conclusions = "\n".join(
        f"- {r['block']}: ΔMAE={fmt(r['mae_difference'])} ({fmt(r['mae_relative_percent'])}%); {conclusion(r)}"
        for r in summary["comparisons"]
        if r["primary"]
    )
    development_table = table(
        [
            "Modelo",
            "MAE OOF desenvolvimento",
            "MAE teste",
            "Diferença teste−OOF",
            "RMSE OOF",
            "RMSE teste",
        ],
        [
            [
                r["model"],
                r["development_mae"],
                r["mae"],
                r["test_minus_development_mae"],
                r["development_rmse"],
                r["rmse"],
            ]
            for r in values
        ],
    )
    text = f"# Avaliação final do holdout — v0.6\n\n## Método e integridade\n\n{methods}\n\nAmostra: 2592 composições, 1308 artistas. Zero sobreposição de composição/artista/hash normalizado de letra com desenvolvimento. Zero perda/multiplicação de linhas ou alvo ausente. Os nove pipelines e todos os artefatos congelados preservam seus hashes. Checkpoint: {MODEL_COMMIT}; tag {MODEL_TAG}.\n\n"
    text += f"Previsões seladas em {summary['prediction_sealed_at']}; SHA-256 completo `{summary['predictions_sha256']}`. Abertura do alvo iniciada em {summary['holdout_opened_at']}. Hash do avaliador `{summary['evaluator_sha256']}`; plano `{summary['evaluation_plan_sha256']}`; manifesto `{summary['model_manifest_sha256']}`. Registro privado de abertura preservado.\n\n"
    text += f"## Nove modelos no teste\n\n{metrics_table}\n\n## Comparações incrementais\n\n{comparisons_table}\n\n## Conclusões primárias\n\n{conclusions}\n\n"
    text += f"## Desenvolvimento versus teste\n\n{development_table}\n\nOOF de desenvolvimento e holdout são amostras diferentes, com estimadores também ajustados em tamanhos de treino diferentes; diferenças entre essas métricas não constituem isoladamente prova de overfitting. O teste não selecionou novamente o candidato.\n\n"
    text += "## Diagnósticos exploratórios\n\nAs tabelas por período/gênero abaixo incluem apenas grupos com n≥30. Não implicam modelos de subgrupo, exclusões ou alterações do protocolo. Histogramas usam resíduo observado−previsto; observado versus previsto usa bins fixos de 10 pontos com n≥30.\n\n"
    for dimension in ("period", "genre"):
        text += (
            f"### {dimension}\n\n"
            + table(
                ["Categoria", "Modelo", "n", "MAE", "RMSE", "R²", "Spearman", "Resíduo médio"],
                [
                    [
                        r["category"],
                        r["model"],
                        r["n"],
                        *[r[name] for name in ("mae", "rmse", "r2", "spearman", "mean_residual")],
                    ]
                    for r in summary["diagnostics"][dimension]
                ],
            )
            + "\n\n"
        )
    text += "### Quantis do erro absoluto\n\n" + table(
        ["Modelo", "Q25", "Mediana", "Q75", "Q90", "Q95"],
        [
            [r["model"], *[r[name] for name in ("q25", "q50", "q75", "q90", "q95")]]
            for r in summary["diagnostics"]["absolute_error_quantiles"]
        ],
    )
    text += f"\n\n## Limitações\n\n{LIMITATIONS}\n\nNão houve treinamento, retuning, clipping, calibração, exclusão ou substituição de registros. Alvo, previsões, resíduos e sorteios individuais permanecem privados. Códigos de saída, testes e auditorias são registrados no run summary.\n"
    project_path("reports/final_holdout_report_v0_6.md").write_text(text, encoding="utf-8")
    monograph = f"# Resultados finais para a monografia — v0.6\n\n## Método\n\n{methods}\n\nA avaliação final compreendeu 2592 composições e 1308 grupos de artista, sem interseção desses grupos com desenvolvimento. O alvo corresponde à popularidade Spotify observada no snapshot, na escala de 0 a 100.\n\n## Resultados\n\n{metrics_table}\n\n## Contribuição incremental\n\n{comparisons_table}\n\n{conclusions}\n\n## Relação com desenvolvimento\n\n{development_table}\n\nAs diferenças entre desenvolvimento e teste refletem amostras e tamanhos de ajuste diferentes, não estabelecendo por si só overfitting. Os descritores LFM2b e as representações profundas MiniLM devem ser discutidos separadamente. As magnitudes absolutas e percentuais apresentadas precisam ser consideradas conjuntamente com os intervalos, para distinguir evidência estatística de relevância prática.\n\n## Limites de generalização\n\n{LIMITATIONS}\n\nNenhuma referência bibliográfica foi acrescentada nesta síntese. Todas as quantidades derivam dos artefatos reais desta execução.\n"
    project_path("reports/final_results_for_monograph_v0_6.md").write_text(
        monograph, encoding="utf-8"
    )
    write_csv("final_holdout_metrics_v0_6.csv", values)
    write_csv("final_holdout_comparisons_v0_6.csv", summary["comparisons"])


def public_audit(paths: list[str], predictions: pl.DataFrame | None = None) -> dict:
    prohibited = (
        "plainLyrics",
        "syncedLyrics",
        "private_lyrics",
        "token_ids_private",
        "prediction__",
        "data/derived/private_",
    )
    texts = []
    for path in paths:
        content = project_path(path).read_text(encoding="utf-8")
        ensure(
            not any(marker in content for marker in prohibited),
            "Marcadores privados em relatório público.",
        )
        texts.append(content)
    if predictions is not None:
        for name in ("composition_key", "track_id", "artist_group_id"):
            ensure(
                not any(str(value) in text for value in predictions[name] for text in texts),
                "Identificador individual em relatório público.",
            )
    return {"public_individual_records": 0, "private_markers": 0, **privacy_audit()}


def evaluate() -> dict:
    previous = read_json(SUMMARY, {})
    if previous.get("status") == "complete":
        audit = verify_completed()
        return {"status": "complete", "idempotent_reuse": True, "verification": audit}
    started = time.perf_counter()
    audit = preflight()
    seal = save_predictions_before_target()
    frame, opening = open_target_once()
    hold = pl.read_parquet(existing_private("holdout_features.parquet"))
    manifest, development = read_json(MANIFEST), read_json(DEVELOPMENT_SUMMARY)
    model_names = [r["model"] for r in manifest["models"]]
    y, groups = frame["spotify_popularity"].to_numpy(), frame["artist_group_id"].to_numpy()
    ensure(frame.height == 2592 and len(set(groups)) == 1308, "Amostra mudou após abertura.")
    values = []
    dev_metrics = {
        row["model"]: row for row in development["metrics"] if row["scope"] == "overall_oof"
    }
    for item in manifest["models"]:
        pred = frame[f"prediction__{item['model']}"].to_numpy()
        result = metrics(y, pred)
        dm = dev_metrics[item["model"]]
        values.append(
            {
                "model": item["model"],
                "algorithm": item["algorithm"],
                "block": item["block"],
                **result,
                "development_mae": dm["mae"],
                "development_rmse": dm["rmse"],
                "development_r2": dm["r2"],
                "development_spearman": dm["spearman"],
                "test_minus_development_mae": result["mae"] - dm["mae"],
                "test_minus_development_rmse": result["rmse"] - dm["rmse"],
            }
        )
        frame = frame.with_columns(pl.Series(f"residual__{item['model']}", y - pred))
    _atomic_write_frame(frame, private("evaluated_predictions_and_residuals.parquet"))
    unique, inverse, weights = bootstrap_weights(groups)
    np.savez_compressed(
        private("bootstrap_artist_draws.npz"),
        artist_groups=unique.astype(str),
        inverse=inverse,
        multiplicities=weights,
    )
    comparisons, draw_columns = [], {"replicate": np.arange(REPETITIONS)}
    for algorithm in ("elastic_net", "ridge"):
        reference = frame[f"prediction__{algorithm}__baseline"].to_numpy()
        for block in BLOCKS[1:]:
            name = f"{algorithm}__{block}"
            comp, mae_draws, rmse_draws = comparison(
                y,
                reference,
                frame[f"prediction__{name}"].to_numpy(),
                inverse,
                weights,
                primary=algorithm == "elastic_net",
            )
            comparisons.append(
                {
                    "model": name,
                    "reference": f"{algorithm}__baseline",
                    "algorithm": algorithm,
                    "block": block,
                    **comp,
                }
            )
            draw_columns[f"mae__{name}"], draw_columns[f"rmse__{name}"] = mae_draws, rmse_draws
    _atomic_write_frame(pl.DataFrame(draw_columns), private("bootstrap_comparison_draws.parquet"))
    summary = {
        "status": "evaluation_complete_verification_pending",
        "version": "v0.6",
        "evaluated_at": utc_now(),
        "model_checkpoint_commit": MODEL_COMMIT,
        "model_checkpoint_tag": MODEL_TAG,
        "candidate_predefined": "elastic_net__traditional",
        "candidate_changed": False,
        "compositions": 2592,
        "artist_groups": 1308,
        "join_audit": opening["join_audit"],
        "overlap_counts": audit["overlap_counts"],
        "versions": audit["versions"],
        "source_artifact_hashes": {
            Path(name).name: value for name, value in audit["frozen_hashes"].items()
        },
        "model_hashes": {item["model"]: item["model_sha256"] for item in manifest["models"]},
        "evaluator_sha256": seal["evaluator_sha256"],
        "evaluation_plan_sha256": seal["evaluation_plan_sha256"],
        "model_manifest_sha256": seal["model_manifest_sha256"],
        "prediction_sealed_at": seal["sealed_at"],
        "holdout_opened_at": opening["opened_at"],
        "predictions_sha256": seal["predictions_sha256"],
        "predictions_saved_before_target": seal["sealed_at"] < opening["opened_at"],
        "residual_convention": "observado menos previsto; positivo indica subestimação",
        "prediction_policy": "raw_unclipped",
        "metrics": values,
        "comparisons": comparisons,
        "diagnostics": aggregate_diagnostics(frame, hold, model_names),
        "bootstrap": {
            "repetitions": REPETITIONS,
            "seed": SEED,
            "sampled_artists_per_replicate": 1308,
            "paired_same_draws": True,
            "preserve_group_multiplicity": True,
            "weighting": "composition",
            "descriptive_quantiles": [0.025, 0.975],
            "bonferroni_mae_quantiles": list(ADJUSTED_QUANTILES),
            "primary_family_comparisons": 3,
        },
        "private_artifact_hashes": {
            name: sha256_file(private(name))
            for name in (
                "predictions_pre_target.parquet",
                "prediction_seal.json",
                "holdout_target_raw.parquet",
                "holdout_opening_record.json",
                "evaluated_predictions_and_residuals.parquet",
                "bootstrap_artist_draws.npz",
                "bootstrap_comparison_draws.parquet",
            )
        },
        "models_retrained": False,
        "retuning": False,
        "clipping": False,
        "excluded_records": 0,
        "training_calls": code_has_no_training_calls(),
        "seconds": time.perf_counter() - started,
        "tests": {"status": "pending"},
    }
    ensure(summary["predictions_saved_before_target"], "Previsões não antecedem abertura.")
    summary = clean_json(summary)
    write_reports(summary)
    summary["figures"] = create_figures(summary)
    ensure(frozen_hashes() == seal["frozen_hashes"], "Artefatos mudaram durante avaliação.")
    write_json(SUMMARY, summary)
    paths = [
        SUMMARY,
        "reports/final_holdout_report_v0_6.md",
        "reports/final_results_for_monograph_v0_6.md",
        "reports/final_holdout_metrics_v0_6.csv",
        "reports/final_holdout_comparisons_v0_6.csv",
    ]
    summary["privacy"] = public_audit(paths, frame)
    summary["public_artifact_hashes"] = {
        Path(name).name: sha256_file(project_path(name)) for name in paths if name != SUMMARY
    }
    summary["figure_hashes"] = {
        Path(name).name: sha256_file(project_path(name)) for name in summary["figures"]
    }
    write_json(SUMMARY, summary)
    return {"status": summary["status"], "metrics": values, "comparisons": comparisons}


def verify_completed() -> dict:
    summary = read_json(SUMMARY)
    ensure(summary is not None and summary.get("metrics"), "Avaliação concluída não encontrada.")
    audit = preflight()
    seal = read_json(private("prediction_seal.json"))
    verify_prediction_seal(seal)
    for name, expected in summary["private_artifact_hashes"].items():
        ensure(sha256_file(private(name)) == expected, "Artefato privado V0.6 mudou.")
    for name, expected in summary["public_artifact_hashes"].items():
        ensure(sha256_file(project_path(f"reports/{name}")) == expected, "Resultado público mudou.")
    for name, expected in summary["figure_hashes"].items():
        ensure(
            sha256_file(project_path(f"reports/figures/final_holdout_v0_6/{name}")) == expected,
            "Gráfico mudou.",
        )
    frame = pl.read_parquet(private("evaluated_predictions_and_residuals.parquet"))
    validate_keys(frame, 2592)
    target = pl.read_parquet(private("holdout_target_raw.parquet"))
    predictions = pl.read_parquet(private("predictions_pre_target.parquet"))
    aligned, _ = align_target(predictions, target)
    ensure(
        aligned.select([*KEYS, "spotify_popularity"]).equals(
            frame.select([*KEYS, "spotify_popularity"])
        ),
        "Alvo/previsões desalinhados.",
    )
    y = frame["spotify_popularity"].to_numpy()
    for row in summary["metrics"]:
        pred = frame[f"prediction__{row['model']}"].to_numpy()
        recalculated = metrics(y, pred)
        for key, value in recalculated.items():
            ensure(value == row[key], "Métrica armazenada divergiu.")
    with np.load(private("bootstrap_artist_draws.npz")) as draws:
        inverse, weights = draws["inverse"], draws["multiplicities"]
        ensure(weights.shape == (2000, 1308), "Dimensão dos sorteios divergente.")
        actual_unique, actual_inverse, actual_weights = bootstrap_weights(
            frame["artist_group_id"].to_numpy()
        )
        ensure(
            np.array_equal(inverse, actual_inverse) and np.array_equal(weights, actual_weights),
            "Sorteios diferem da seed congelada.",
        )
        ensure(
            np.array_equal(draws["artist_groups"], actual_unique.astype(str)),
            "Índice dos artistas divergiu.",
        )
        records = pl.read_parquet(private("bootstrap_comparison_draws.parquet"))
        for row in summary["comparisons"]:
            result, mae, rmse = comparison(
                y,
                frame[f"prediction__{row['reference']}"].to_numpy(),
                frame[f"prediction__{row['model']}"].to_numpy(),
                inverse,
                weights,
                primary=row["primary"],
            )
            for key, value in result.items():
                ensure(value == row[key], "Intervalo/comparação armazenada divergiu.")
            ensure(
                np.array_equal(mae, records[f"mae__{row['model']}"].to_numpy())
                and np.array_equal(rmse, records[f"rmse__{row['model']}"].to_numpy()),
                "Bootstrap privado divergiu.",
            )
    paths = [SUMMARY, *[f"reports/{name}" for name in summary["public_artifact_hashes"]]]
    ensure(
        summary["candidate_predefined"] == "elastic_net__traditional"
        and not summary["candidate_changed"],
        "Candidato mudou.",
    )
    return {
        "status": "passed",
        "model_hashes_preserved": True,
        "original_artifacts_preserved": True,
        "predictions_saved_before_target": seal["sealed_at"] < summary["holdout_opened_at"],
        "alignment_verified": True,
        "metrics_recalculated_exactly": True,
        "bootstrap_same_draws_verified": True,
        "bonferroni_quantiles_verified": True,
        "rows": 2592,
        "artists": 1308,
        "training_calls": code_has_no_training_calls(),
        "privacy": public_audit(paths, frame),
        "overlap_counts": audit["overlap_counts"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["preflight", "predict", "evaluate", "verify"])
    command = parser.parse_args().command
    result = {
        "preflight": preflight,
        "predict": save_predictions_before_target,
        "evaluate": evaluate,
        "verify": verify_completed,
    }[command]()
    if command in ("preflight", "predict"):
        result = {key: value for key, value in result.items() if key != "frozen_hashes"}
    print(json.dumps(clean_json(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
