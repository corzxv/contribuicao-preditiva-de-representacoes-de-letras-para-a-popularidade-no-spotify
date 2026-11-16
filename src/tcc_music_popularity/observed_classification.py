"""Classificação ordinal pareada, PCA interna e retomada, sem alterar a regressão."""

import argparse
import importlib.metadata
import json
import sqlite3
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_limits

from . import observed_regression as regression
from . import ordinal_classifier as ordinal
from . import popularity_levels as common
from .manual_lyrics import atomic_frame, exclusive

ROOT = common.ROOT
WORKSPACE = ROOT / "data/derived/private_ordinal_classification_200k_v1"
OUTPUT = ROOT / "reports/classificacao_ordinal_200k_v1"
PROTOCOL = ROOT / "docs/protocolo_classificacao_ordinal_200k_v1.md"
CONFIG = ROOT / "configs/classificacao_ordinal_200k_v1.json"
READINESS = common.OUTPUT / "previsoes/resumo_niveis.json"
PILOT = ROOT / "reports/piloto_vinculacao_200k_v1_1/resumo_piloto.json"
TRIAGE = ROOT / "reports/triagem_piloto_vinculacao_200k_v1/resumo_triagem.json"
BLOCKS = regression.BLOCKS
REFERENCE = "class_prior"


def preprocessor(block, option):
    common.require(option in ("none", "pca95"), "Pré-processamento desconhecido.")
    columns = regression.columns_for(block)
    numeric = ["model_" + c for c in regression.data.NUMERIC]
    categorical = ["model_" + c for c in regression.data.CATEGORICAL]
    extra = [c for c in columns if c not in numeric + categorical]
    steps = [
        ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scale", StandardScaler()),
    ]
    if option == "pca95":
        steps.append(("pca", PCA(n_components=0.95, svd_solver="full")))
    transformers = [
        ("metadata_numeric", Pipeline(steps), numeric),
        (
            "categorical",
            Pipeline(
                [
                    (
                        "impute",
                        SimpleImputer(
                            missing_values=None,
                            strategy="constant",
                            fill_value="__MISSING__",
                            keep_empty_features=True,
                        ),
                    ),
                    ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                ]
            ),
            categorical,
        ),
    ]
    if extra:
        transformers.append(
            (
                "text",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
                        ("scale", StandardScaler()),
                    ]
                ),
                extra,
            )
        )
    return Pipeline(
        [
            ("columns", ColumnTransformer(transformers, remainder="drop", sparse_threshold=0)),
            ("constants", VarianceThreshold(0)),
        ]
    )


def validate_probabilities(probabilities, n):
    probabilities = np.asarray(probabilities, dtype=float)
    common.require(
        probabilities.shape == (n, 3)
        and np.isfinite(probabilities).all()
        and (probabilities >= 0).all()
        and (probabilities <= 1 + 1e-12).all()
        and np.allclose(probabilities.sum(axis=1), 1, rtol=0, atol=1e-12),
        "Probabilidades inválidas.",
    )
    return probabilities


def metrics(y, probabilities, weights=None):
    probabilities = validate_probabilities(probabilities, len(y))
    predicted = probabilities.argmax(axis=1)
    result, matrix, _, _ = common.scores(y, predicted, weights)
    result.update(
        log_loss=float(
            np.average(
                -np.log(np.maximum(probabilities[np.arange(len(y)), y], 1e-15)), weights=weights
            )
        ),
        brier_multiclass=float(
            np.average(np.sum((probabilities - np.eye(3)[y]) ** 2, axis=1), weights=weights)
        ),
    )
    return result, matrix


def fit_model(x, y, alpha, settings):
    started = time.monotonic()
    model = ordinal.OrdinalLogit(
        alpha=alpha,
        max_iter=settings["max_iter"],
        gradient_tolerance=settings["gradient_tolerance"],
    )
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        model.fit(x, y)
    common.require(
        not captured, "Aviso numérico no ajuste ordinal; diagnosticar antes de prosseguir."
    )
    return model, {
        "fit_seconds": time.monotonic() - started,
        "iterations": int(model.n_iter_),
        "max_abs_gradient": model.max_abs_gradient_,
        "features": x.shape[1],
        "warnings": 0,
    }


def tune(frame, folds, outer, block, db, mode, settings):
    column = "inner_outer_" + str(outer)
    y = common.categories(frame[regression.data.TARGET], settings["cutpoints"], observed=True)
    records = []
    for inner in range(3):
        train = np.flatnonzero(
            (folds["outer_fold"].to_numpy() != outer) & (folds[column].to_numpy() != inner)
        )
        valid = np.flatnonzero(folds[column].to_numpy() == inner)
        common.require(len(train) and len(valid), "Partição interna vazia.")
        for option in settings["preprocessing"]:
            prepare, x_train, x_valid = None, None, None
            for alpha in settings["alphas"]:
                key = f"{mode}/{outer}/{block}/{inner}/{option}/{alpha:g}"
                stored = db.execute(
                    "SELECT payload,sha256 FROM tuning WHERE key=?", (key,)
                ).fetchone()
                if stored:
                    record = json.loads(stored[0])
                    common.require(
                        common.fingerprint(record) == stored[1] and record["n"] == len(valid),
                        "Checkpoint interno incompatível.",
                    )
                    matrix = np.asarray(record["confusion"], float)
                    common.require(
                        matrix.shape == (3, 3)
                        and (matrix >= 0).all()
                        and matrix.sum() == len(valid),
                        "Matriz interna corrompida.",
                    )
                else:
                    if prepare is None:
                        prepare = preprocessor(block, option)
                        x_train = prepare.fit_transform(
                            frame[train].select(regression.columns_for(block))
                        )
                        x_valid = prepare.transform(
                            frame[valid].select(regression.columns_for(block))
                        )
                    model, details = fit_model(x_train, y[train], alpha, settings)
                    result, matrix = metrics(y[valid], model.predict_proba(x_valid))
                    common.require(
                        result["all_true_classes_present"], "Validação interna sem as três classes."
                    )
                    record = {
                        "outer": outer,
                        "inner": inner,
                        "block": block,
                        "option": option,
                        "alpha": alpha,
                        "n": len(valid),
                        "confusion": matrix.tolist(),
                        **details,
                    }
                    with db:
                        db.execute(
                            "INSERT INTO tuning VALUES (?,?,?)",
                            (key, json.dumps(record), common.fingerprint(record)),
                        )
                    print(
                        json.dumps(
                            {
                                "stage": "inner_fit",
                                "mode": mode,
                                **{
                                    k: record[k]
                                    for k in (
                                        "outer",
                                        "block",
                                        "inner",
                                        "option",
                                        "alpha",
                                        "fit_seconds",
                                        "iterations",
                                    )
                                },
                            }
                        ),
                        flush=True,
                    )
                records.append(record)
    candidates = []
    for option in settings["preprocessing"]:
        for alpha in settings["alphas"]:
            pooled = sum(
                np.asarray(r["confusion"])
                for r in records
                if r["option"] == option and r["alpha"] == alpha
            )
            common.require((pooled.sum(axis=1) > 0).all(), "Classes ausentes na seleção interna.")
            candidates.append(
                {
                    "option": option,
                    "alpha": alpha,
                    "balanced_accuracy": float(np.mean(np.diag(pooled) / pooled.sum(axis=1))),
                }
            )
    best = max(r["balanced_accuracy"] for r in candidates)
    eligible = [r for r in candidates if best - r["balanced_accuracy"] <= settings["tie_tolerance"]]
    selected = sorted(eligible, key=lambda r: (-r["alpha"], r["option"] != "none"))[0]
    return selected, candidates


def save_part(directory, signature, outer, block, model, valid, probabilities, details):
    directory.mkdir(parents=True, exist_ok=True)
    stem = directory / f"outer{outer}_{block}"
    temp = stem.with_suffix(".joblib.tmp")
    joblib.dump(model, temp)
    temp.replace(stem.with_suffix(".joblib"))
    probabilities = validate_probabilities(probabilities, valid.height)
    frame = valid.select("track_id").with_columns(
        [pl.Series("probability_" + str(i), probabilities[:, i]) for i in range(3)]
    )
    atomic_frame(stem.with_suffix(".parquet"), frame)
    common.atomic_json(
        stem.with_suffix(".json"),
        {
            "signature": signature,
            "outer": outer,
            "block": block,
            "details": details,
            "model_sha256": common.digest(stem.with_suffix(".joblib")),
            "prediction_sha256": common.digest(stem.with_suffix(".parquet")),
        },
    )


def read_part(directory, signature, outer, block, valid):
    stem = directory / f"outer{outer}_{block}"
    if not stem.with_suffix(".json").exists():
        return None
    record = common.read_json(stem.with_suffix(".json"))
    common.require(
        record["signature"] == signature and record["outer"] == outer and record["block"] == block,
        "Parte de outra versão; preservada.",
    )
    common.require(
        common.digest(stem.with_suffix(".joblib")) == record["model_sha256"]
        and common.digest(stem.with_suffix(".parquet")) == record["prediction_sha256"],
        "Parte externa corrompida; não refazer silenciosamente.",
    )
    frame = pl.read_parquet(stem.with_suffix(".parquet"))
    common.require(
        frame.select("track_id").equals(valid.select("track_id")), "IDs de previsão desalinhados."
    )
    probabilities = validate_probabilities(
        frame.select("probability_0", "probability_1", "probability_2").to_numpy(), valid.height
    )
    return record, probabilities


def evaluate(frame, folds, directory, signature, private, output, settings):
    y = common.categories(frame[regression.data.TARGET], settings["cutpoints"], observed=True)
    tables, confusion, selections, calibrations, class_metrics = [], [], [], [], []
    predictions = frame.select(
        "track_id", "text_component_id", regression.data.TARGET, "sampling_weight"
    ).with_columns(folds["outer_fold"], pl.Series("observed_class", y))
    for block in (*BLOCKS, REFERENCE):
        probabilities = np.empty((frame.height, 3))
        for outer in range(5):
            mask = folds["outer_fold"].to_numpy() == outer
            valid = frame.filter(pl.Series(mask))
            record, predicted = read_part(directory, signature, outer, block, valid)
            probabilities[mask] = predicted
            if block != REFERENCE:
                selections.append(
                    {
                        "outer_fold": outer,
                        "block": block,
                        **record["details"]["selected"],
                        "iterations": record["details"]["iterations"],
                        "max_abs_gradient": record["details"]["max_abs_gradient"],
                    }
                )
        predictions = predictions.with_columns(
            [pl.Series(block + "_probability_" + str(i), probabilities[:, i]) for i in range(3)]
        )
        for weighting in ("equal_tracks", "original_weight_sensitivity"):
            weights = None if weighting == "equal_tracks" else frame["sampling_weight"].to_numpy()
            result, matrix = metrics(y, probabilities, weights)
            tables.append({"model": block, "weighting": weighting, "outer_fold": -1, **result})
            _, _, precision, recall = common.scores(y, probabilities.argmax(axis=1), weights)
            for index in range(3):
                class_metrics.append(
                    {
                        "model": block,
                        "weighting": weighting,
                        "class_index": index,
                        "precision": float(precision[index]),
                        "recall": float(recall[index]),
                    }
                )
            for outer in range(5):
                mask = folds["outer_fold"].to_numpy() == outer
                cell_weights = None if weights is None else weights[mask]
                cell, _ = metrics(y[mask], probabilities[mask], cell_weights)
                tables.append({"model": block, "weighting": weighting, "outer_fold": outer, **cell})
            for truth in range(3):
                for predicted in range(3):
                    confusion.append(
                        {
                            "model": block,
                            "weighting": weighting,
                            "observed_class": truth,
                            "predicted_class": predicted,
                            "count_or_weight": float(matrix[truth, predicted]),
                        }
                    )
        # Calibração descritiva com intervalos fixos, sem refit do calibrador.
        for target in range(3):
            bins = np.minimum((probabilities[:, target] * 10).astype(int), 9)
            for index in range(10):
                mask = bins == index
                calibrations.append(
                    {
                        "model": block,
                        "class_index": target,
                        "probability_bin": index,
                        "n": int(mask.sum()),
                        "mean_predicted_probability": float(probabilities[mask, target].mean())
                        if mask.any()
                        else None,
                        "observed_fraction": float((y[mask] == target).mean())
                        if mask.any()
                        else None,
                    }
                )
    atomic_frame(private / "probabilidades_externas.parquet", predictions)
    for name, rows in (
        ("metricas_externas", tables),
        ("matrizes_confusao", confusion),
        ("selecoes_internas", selections),
        ("calibracao_descritiva", calibrations),
        ("metricas_por_classe", class_metrics),
    ):
        common.write_csv(output / (name + ".csv"), rows)
    return {
        "prediction_rows": frame.height,
        "models_evaluated": len(BLOCKS) + 1,
        "prediction_sha256": common.digest(private / "probabilidades_externas.parquet"),
    }


def run(
    mode,
    *,
    base_workspace=regression.data.WORKSPACE,
    base_report=regression.data.OUTPUT / "resumo_base_modelagem.json",
    workspace=WORKSPACE,
    output=OUTPUT,
    configuration=CONFIG,
    readiness=READINESS,
    pilot=PILOT,
    triage=TRIAGE,
    expected=77535,
    limit_outer_blocks=None,
):
    common.require(mode in ("smoke", "all"), "Modo inválido.")
    common.require(
        limit_outer_blocks is None or (mode == "all" and limit_outer_blocks > 0),
        "Limite somente para produção.",
    )
    workspace, output = Path(workspace).resolve(), Path(output).resolve()
    common.require(
        workspace.is_relative_to(ROOT / "data/derived") or expected != 77535,
        "Modelos devem ficar privados.",
    )
    common.require(
        not workspace.is_relative_to(output) and not output.is_relative_to(workspace),
        "Separar modelos e agregados.",
    )
    settings = common.read_json(configuration)
    common.require(
        settings["cutpoints"] == [20, 40] and settings["training_weights"] == "equal_tracks",
        "Contrato de classificação incompatível.",
    )
    checked = common.read_json(readiness)
    common.require(
        checked["completed"]
        and checked["observed_tracks"] == expected
        and checked["operational_support_all_partitions"],
        "Concluir diagnóstico 31 antes de treinar.",
    )
    common.require(
        common.read_json(pilot)["completed"] and common.read_json(triage)["completed"],
        "Concluir preparo/triagem do piloto antes de treinar.",
    )
    print("[1/4] Conferindo base, folds e vetores existentes; sem encoder ou letras...", flush=True)
    preserved = common.frozen_hashes()
    frame, folds, sources = regression.load_sources(base_workspace, base_report, mode, expected)
    regression.data.audit_folds(folds)
    common.require(
        frame.select("track_id", "text_component_id").equals(
            folds.select("track_id", "text_component_id")
        ),
        "Base/folds desalinhados.",
    )
    sources = [
        *sources,
        Path(configuration),
        Path(readiness),
        Path(pilot),
        Path(triage),
        PROTOCOL,
        common.CONFIG,
    ]
    common.require(
        all(
            not Path(p).resolve().is_relative_to(workspace)
            and not Path(p).resolve().is_relative_to(output)
            for p in sources
        ),
        "Saída sobrepõe fonte.",
    )
    seal = {
        "version": settings["version"],
        "inputs": {str(Path(p).resolve()): common.digest(p) for p in sources},
        "code": {
            p.name: common.digest(p)
            for p in (
                Path(__file__),
                Path(ordinal.__file__),
                Path(common.__file__),
                Path(regression.__file__),
            )
        },
        "settings": settings,
        "preserved": preserved,
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("numpy", "scipy", "polars", "scikit-learn", "joblib")
        },
    }
    signature = common.fingerprint(seal)
    label = "smoke" if mode == "smoke" else "integral"
    private, destination = workspace / label, output / label
    directory = private / "parts"
    started = time.monotonic()
    with exclusive(workspace), threadpool_limits(limits=settings["threads"]):
        common.prepare_output(workspace, seal, sources)
        common.prepare_output(destination, seal, sources)
        private.mkdir(parents=True, exist_ok=True)
        gate = workspace / "smoke_verified.json"
        if mode == "all":
            common.require(
                gate.exists()
                and common.read_json(gate) == {"signature": signature, "verified": True},
                "Execute smoke completo antes da produção.",
            )
        else:
            common.atomic_json(gate, {"signature": signature, "verified": False})
        summary = {
            "completed": False,
            "mode": mode,
            "signature": signature,
            "seal": seal,
            "source_rows": expected,
            "used_rows": frame.height,
            "expected_outer_blocks": len(BLOCKS) * (1 if mode == "smoke" else 5),
            "new_outer_blocks": 0,
            "reused_outer_blocks": 0,
            "global_metrics_available": False,
            "semantic_linkage_review_completed": False,
            "catalog_inference_claimed": False,
        }
        common.atomic_json(destination / "resumo_classificacao.json", summary)
        y = common.categories(frame[regression.data.TARGET], settings["cutpoints"], observed=True)
        with sqlite3.connect(workspace / "state.sqlite") as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS tuning(key TEXT PRIMARY KEY,payload TEXT NOT NULL,sha256 TEXT NOT NULL)"
            )
            try:
                print(
                    "[2/4] "
                    + mode
                    + ": logística ordinal nos quatro blocos; checkpoints por ajuste...",
                    flush=True,
                )
                stopped = False
                for outer in [0] if mode == "smoke" else range(5):
                    mask = folds["outer_fold"].to_numpy() == outer
                    valid, train = frame.filter(pl.Series(mask)), frame.filter(pl.Series(~mask))
                    if read_part(directory, signature, outer, REFERENCE, valid) is None:
                        prior = np.bincount(y[~mask], minlength=3) / (~mask).sum()
                        save_part(
                            directory,
                            signature,
                            outer,
                            REFERENCE,
                            prior,
                            valid,
                            np.tile(prior, (valid.height, 1)),
                            {"train_rows": train.height, "valid_rows": valid.height},
                        )
                    for block in reversed(BLOCKS):
                        if read_part(directory, signature, outer, block, valid) is not None:
                            summary["reused_outer_blocks"] += 1
                            continue
                        if (
                            limit_outer_blocks is not None
                            and summary["new_outer_blocks"] >= limit_outer_blocks
                        ):
                            stopped = True
                            break
                        selected, candidates = tune(frame, folds, outer, block, db, mode, settings)
                        prepare = preprocessor(block, selected["option"])
                        x_train = prepare.fit_transform(train.select(regression.columns_for(block)))
                        model, details = fit_model(x_train, y[~mask], selected["alpha"], settings)
                        fitted = Pipeline([("prepare", prepare), ("ordinal", model)])
                        probabilities = fitted.predict_proba(
                            valid.select(regression.columns_for(block))
                        )
                        details.update(
                            selected=selected,
                            candidates=candidates,
                            train_rows=train.height,
                            valid_rows=valid.height,
                        )
                        save_part(
                            directory,
                            signature,
                            outer,
                            block,
                            fitted,
                            valid,
                            probabilities,
                            details,
                        )
                        summary["new_outer_blocks"] += 1
                        progress = {
                            "stage": "outer_block",
                            "mode": mode,
                            "outer": outer,
                            "block": block,
                            "new_outer_blocks": summary["new_outer_blocks"],
                            "seconds": time.monotonic() - started,
                        }
                        common.atomic_json(workspace / "progress.json", progress)
                        print(json.dumps(progress), flush=True)
                    if stopped:
                        break
                completed = summary["new_outer_blocks"] + summary["reused_outer_blocks"]
                summary.update(
                    completed_outer_blocks=completed,
                    pending_outer_blocks=summary["expected_outer_blocks"] - completed,
                )
                parts_complete = not stopped and summary["pending_outer_blocks"] == 0
                print("[3/4] Conferindo partes, recarga e preservação das fontes...", flush=True)
                common.require(
                    all(
                        common.digest(p) == seal["inputs"][str(Path(p).resolve())] for p in sources
                    ),
                    "Fonte mudou durante classificação.",
                )
                common.require(common.frozen_hashes() == preserved, "Artefato anterior mudou.")
                if parts_complete and mode == "smoke":
                    errors = []
                    valid = frame.filter(folds["outer_fold"] == 0)
                    for block in BLOCKS:
                        _, stored = read_part(directory, signature, 0, block, valid)
                        fitted = joblib.load(directory / ("outer0_" + block + ".joblib"))
                        reloaded = fitted.predict_proba(valid.select(regression.columns_for(block)))
                        errors.append(float(np.max(np.abs(stored - reloaded))))
                    common.require(max(errors) <= 1e-10, "Probabilidade mudou após recarga.")
                    summary["reload_max_abs_difference"] = max(errors)
                    common.atomic_json(gate, {"signature": signature, "verified": True})
                elif parts_complete:
                    summary.update(
                        evaluate(
                            frame, folds, directory, signature, private, destination, settings
                        ),
                        global_metrics_available=True,
                    )
                summary["completed"] = parts_complete
            except BaseException as exc:
                summary.update(completed=False, error_type=type(exc).__name__)
                raise
            finally:
                summary["seconds_this_invocation"] = time.monotonic() - started
                common.atomic_json(destination / "resumo_classificacao.json", summary)
    print(
        "[4/4] "
        + ("Concluído" if summary["completed"] else "Parcial; retomar")
        + "; agregados em "
        + str(destination),
        flush=True,
    )
    return 0 if summary["completed"] else 2


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("smoke", "all"))
    parser.add_argument("--limit-outer-blocks", type=int)
    args = parser.parse_args()
    return run(args.mode, limit_outer_blocks=args.limit_outer_blocks)
