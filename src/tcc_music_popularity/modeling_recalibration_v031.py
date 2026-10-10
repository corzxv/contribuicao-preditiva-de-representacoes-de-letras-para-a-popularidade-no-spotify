"""Recalibração dirigida v0.3.1 da modelagem piloto, sem acessar o holdout."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import time
import warnings
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import matplotlib
import numpy as np
import polars as pl
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import PROJECT_ROOT, project_path
from .io import git_commit, read_json, sha256_file, utc_now, write_json
from .modeling_pilot_v030 import (
    BOOTSTRAP_REPETITIONS,
    CATEGORICAL_FEATURES,
    EXPECTED_ROWS,
    INNER_FOLDS,
    OUTER_FOLDS,
    SEED,
    FeatureBlocks,
    ModelingPilotError,
    fold_assignment_hash,
    grouped_paired_bootstrap,
    load_feature_blocks,
    make_grouped_folds,
    regression_metrics,
)

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PROTOCOL_VERSION = "modeling-recalibration-v0.3.1"
V03_MATRIX = "data/derived/private_modeling/modeling_pilot_matrix_v0_3.parquet"
V03_FOLDS = "data/derived/private_modeling/modeling_pilot_fold_assignments_v0_3.parquet"
V03_OOF = "data/derived/private_modeling/modeling_pilot_oof_predictions_v0_3.parquet"
V03_SUMMARY = "reports/run_summary_modeling_pilot_v0_3.json"

PRIVATE_DIRECTORY = "data/derived/private_modeling"
OOF_NAME = "modeling_recalibration_oof_predictions_v0_3_1.parquet"
FOLD_RESULTS_NAME = "modeling_recalibration_fold_results_v0_3_1.parquet"

REPORT_PATH = "reports/modeling_recalibration_report_v0_3_1.md"
METRICS_PATH = "reports/modeling_recalibration_metrics_v0_3_1.csv"
RESIDUAL_REPORT_PATH = "reports/modeling_residual_analysis_v0_3_1.md"
SUMMARY_PATH = "reports/run_summary_modeling_v0_3_1.json"
FIGURE_DIRECTORY = "reports/figures/modeling_v0_3_1"

RIDGE_ALPHAS = (
    0.0001,
    0.001,
    0.01,
    0.03,
    0.1,
    0.3,
    1.0,
    3.0,
    10.0,
    30.0,
    100.0,
    300.0,
    1000.0,
    3000.0,
    10000.0,
)
ELASTIC_NET_ALPHAS = (0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0)
ELASTIC_NET_L1_RATIOS = (0.05, 0.1, 0.25, 0.5, 0.8, 0.95)
COEFFICIENT_TOLERANCE = 1e-10
OVERFITTING_GAP_FRACTION = 0.25
MINIMUM_INCREMENTAL_GAIN_PERCENT = 2.0

FROZEN_INPUTS = {
    "base": "data/processed/modeling_base_lfm_v0_1_1.parquet",
    "split": "data/processed/split_assignments_v0_1_1.parquet",
    "cohort": "data/processed/lyrics_pilot_cohort_v0_1.parquet",
    "lyrics_results": "data/processed/lyrics_pilot_full_results_v0_1_3.parquet",
    "embeddings": "data/derived/private_embeddings/lyrics_embeddings_minilm_v0_2.parquet",
    "embedding_index": "data/derived/private_embeddings/embedding_index_minilm_v0_2.parquet",
}


@dataclass(frozen=True)
class Representation:
    block: Literal["baseline", "traditional", "deep", "combined"]
    variant: Literal["raw", "pca90"]

    @property
    def key(self) -> str:
        return f"{self.block}__{self.variant}"


MAIN_REPRESENTATIONS = (
    Representation("baseline", "raw"),
    Representation("traditional", "raw"),
    Representation("deep", "raw"),
    Representation("combined", "raw"),
    Representation("traditional", "pca90"),
    Representation("deep", "pca90"),
    Representation("combined", "pca90"),
)
RESIDUAL_BLOCKS = ("traditional", "deep", "combined")


def _project(relative: str) -> Path:
    return project_path(relative)


def _take(frame: pl.DataFrame, indices: np.ndarray) -> pl.DataFrame:
    return frame[indices.tolist()]


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean_json(item) for item in value]
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        return None
    return value


def _hash_files(paths: dict[str, str]) -> dict[str, str]:
    return {name: sha256_file(_project(path)) for name, path in paths.items()}


def _directory_fingerprint(relative: str) -> dict[str, Any]:
    root = _project(relative)
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        relative_name = path.relative_to(root).as_posix()
        digest.update(relative_name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return {"files": len(files), "sha256": digest.hexdigest()}


def _inner_folds(target: np.ndarray, groups: np.ndarray, outer_fold: int) -> np.ndarray:
    return make_grouped_folds(
        target,
        groups,
        n_splits=INNER_FOLDS,
        seed=SEED + 1000 + outer_fold,
    )


def load_and_validate_v03_inputs() -> tuple[
    pl.DataFrame, np.ndarray, np.ndarray, np.ndarray, FeatureBlocks, dict[str, Any]
]:
    """Carrega exclusivamente a matriz/folds privados já congelados na v0.3."""

    summary = read_json(V03_SUMMARY)
    if not isinstance(summary, dict) or summary.get("status") != "complete":
        raise ModelingPilotError("Run summary v0.3 completo não encontrado.")
    expected_private_hashes = summary["private_output_hashes"]
    actual_matrix_hash = sha256_file(_project(V03_MATRIX))
    actual_folds_hash = sha256_file(_project(V03_FOLDS))
    if actual_matrix_hash != expected_private_hashes[Path(V03_MATRIX).name]:
        raise ModelingPilotError("A matriz v0.3 divergiu do hash congelado.")
    if actual_folds_hash != expected_private_hashes[Path(V03_FOLDS).name]:
        raise ModelingPilotError("Os folds v0.3 divergiram do hash congelado.")

    matrix = pl.read_parquet(_project(V03_MATRIX))
    assignments = pl.read_parquet(_project(V03_FOLDS))
    if matrix.height != EXPECTED_ROWS or assignments.height != EXPECTED_ROWS:
        raise ModelingPilotError("Cardinalidade divergente da v0.3.")
    if matrix["composition_key"].to_list() != assignments["composition_key"].to_list():
        raise ModelingPilotError("Ordem/composição divergiu entre matriz e folds v0.3.")
    if matrix["track_id"].to_list() != assignments["track_id"].to_list():
        raise ModelingPilotError("Representantes Spotify divergiram da v0.3.")
    if matrix.filter(pl.col("split") != "development_train").height:
        raise ModelingPilotError("A matriz contém holdout.")
    folds = assignments["outer_fold"].to_numpy().astype(int)
    groups = matrix["artist_group_id"].to_numpy()
    target = matrix["spotify_popularity"].to_numpy().astype(float)
    if fold_assignment_hash(matrix, folds) != summary["folds"]["assignment_sha256"]:
        raise ModelingPilotError("Hash lógico das atribuições divergiu da v0.3.")
    for fold in range(OUTER_FOLDS):
        if set(groups[folds == fold]) & set(groups[folds != fold]):
            raise ModelingPilotError(f"Leakage por artista no fold {fold}.")
    blocks = load_feature_blocks()
    audit = {
        "rows": matrix.height,
        "unique_compositions": matrix["composition_key"].n_unique(),
        "unique_tracks": matrix["track_id"].n_unique(),
        "artist_groups": matrix["artist_group_id"].n_unique(),
        "holdout_rows": 0,
        "matrix_sha256": actual_matrix_hash,
        "folds_sha256": actual_folds_hash,
        "assignment_sha256": summary["folds"]["assignment_sha256"],
        "expected_assignment_sha256": "eb37c9d19dbc298b585991f55e75158b7a3a0e0aeab70a0c33c184450830f940",
        "fold_counts": np.bincount(folds, minlength=OUTER_FOLDS).tolist(),
        "artist_overlap_counts": [0] * OUTER_FOLDS,
        "composition_overlap_counts": [0] * OUTER_FOLDS,
    }
    if audit["assignment_sha256"] != audit["expected_assignment_sha256"]:
        raise ModelingPilotError("Hash de folds não é o documentado na v0.3.")
    return matrix, folds, groups, target, blocks, audit


def _numeric_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "imputer",
                SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
            ),
            ("scaler", StandardScaler()),
        ]
    )


def _categorical_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(missing_values=None, strategy="most_frequent")),
            (
                "one_hot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=np.float64),
            ),
        ]
    )


def _pca_pipeline(*, add_indicator: bool) -> Pipeline:
    return Pipeline(
        [
            (
                "imputer",
                SimpleImputer(
                    strategy="median",
                    add_indicator=add_indicator,
                    keep_empty_features=True,
                ),
            ),
            ("variance", VarianceThreshold()),
            ("pre_pca_scaler", StandardScaler()),
            ("pca", PCA(n_components=0.90, svd_solver="full")),
            ("post_pca_scaler", StandardScaler()),
        ]
    )


def build_representation_transformer(
    representation: Representation,
    blocks: FeatureBlocks,
    *,
    include_baseline: bool = True,
) -> Pipeline:
    """Cria PCAs separadas e nunca mistura baseline, LFM2b e MiniLM."""

    transformers: list[tuple[str, Any, list[str]]] = []
    if include_baseline:
        baseline_categorical = [name for name in CATEGORICAL_FEATURES if name in blocks.baseline]
        baseline_numeric = [name for name in blocks.baseline if name not in baseline_categorical]
        transformers.append(("baseline_numeric", _numeric_pipeline(), baseline_numeric))
        transformers.append(("baseline_categorical", _categorical_pipeline(), baseline_categorical))
    if representation.block in {"traditional", "combined"}:
        traditional_transformer = (
            _pca_pipeline(add_indicator=True)
            if representation.variant == "pca90"
            else _numeric_pipeline()
        )
        transformers.append(("traditional", traditional_transformer, list(blocks.traditional)))
    if representation.block in {"deep", "combined"}:
        embedding_transformer = (
            _pca_pipeline(add_indicator=False)
            if representation.variant == "pca90"
            else _numeric_pipeline()
        )
        transformers.append(("embedding", embedding_transformer, list(blocks.embeddings)))
    preprocess = ColumnTransformer(transformers, sparse_threshold=0.0)
    return Pipeline([("preprocess", preprocess), ("variance", VarianceThreshold())])


def representation_columns(
    representation: Representation, blocks: FeatureBlocks, *, include_baseline: bool = True
) -> list[str]:
    columns: list[str] = list(blocks.baseline) if include_baseline else []
    if representation.block in {"traditional", "combined"}:
        columns.extend(blocks.traditional)
    if representation.block in {"deep", "combined"}:
        columns.extend(blocks.embeddings)
    return columns


def _components(transformer: Pipeline) -> dict[str, int | None]:
    named = transformer.named_steps["preprocess"].named_transformers_
    result: dict[str, int | None] = {"lfm": None, "embedding": None}
    if "traditional" in named and isinstance(named["traditional"], Pipeline):
        pca = named["traditional"].named_steps.get("pca")
        if pca is not None:
            result["lfm"] = int(pca.n_components_)
    if "embedding" in named and isinstance(named["embedding"], Pipeline):
        pca = named["embedding"].named_steps.get("pca")
        if pca is not None:
            result["embedding"] = int(pca.n_components_)
    return result


def _feature_groups(transformer: Pipeline) -> np.ndarray:
    names = transformer.named_steps["preprocess"].get_feature_names_out()
    support = transformer.named_steps["variance"].get_support()
    kept = names[support]
    result = []
    for name in kept:
        if name.startswith("baseline_"):
            result.append("baseline")
        elif name.startswith("traditional__"):
            result.append("lfm")
        elif name.startswith("embedding__"):
            result.append("embedding")
        else:
            result.append("other")
    return np.asarray(result, dtype=object)


def coefficient_diagnostics(coef: np.ndarray, feature_groups: np.ndarray) -> dict[str, Any]:
    coef = np.asarray(coef, dtype=float).ravel()
    result: dict[str, Any] = {
        "total": int(coef.size),
        "nonzero_total": int(np.sum(np.abs(coef) > COEFFICIENT_TOLERANCE)),
        "l2_norm_total": float(np.linalg.norm(coef)),
    }
    for group in ("baseline", "lfm", "embedding", "other"):
        mask = feature_groups == group
        if not np.any(mask):
            continue
        result[group] = {
            "features": int(np.sum(mask)),
            "nonzero": int(np.sum(np.abs(coef[mask]) > COEFFICIENT_TOLERANCE)),
            "l2_norm": float(np.linalg.norm(coef[mask])),
        }
    return result


def ridge_grid() -> list[dict[str, float]]:
    return [{"alpha": alpha} for alpha in RIDGE_ALPHAS]


def elastic_net_grid() -> list[dict[str, float]]:
    return [
        {"alpha": alpha, "l1_ratio": ratio}
        for ratio in ELASTIC_NET_L1_RATIOS
        for alpha in ELASTIC_NET_ALPHAS
    ]


def _fit_model(
    algorithm: Literal["ridge", "elastic_net"],
    params: dict[str, float],
    x: np.ndarray,
    y: np.ndarray,
    *,
    seed: int,
) -> Any:
    if algorithm == "ridge":
        return Ridge(alpha=params["alpha"]).fit(x, y)
    model = ElasticNet(
        alpha=params["alpha"],
        l1_ratio=params["l1_ratio"],
        max_iter=50_000,
        tol=1e-3,
        random_state=seed,
    )
    return _fit_elastic_net_checked(model, x, y)


def _fit_elastic_net_checked(
    model: ElasticNet,
    x: np.ndarray,
    y: np.ndarray,
) -> ElasticNet:
    """Ajusta Elastic Net com retries explícitos e nunca aceita não convergência."""

    iteration_limits = (int(model.max_iter), 200_000, 500_000)
    attempted: set[int] = set()
    for limit in iteration_limits:
        if limit in attempted:
            continue
        attempted.add(limit)
        model.set_params(max_iter=limit)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            model.fit(x, y)
        warned = any(issubclass(item.category, ConvergenceWarning) for item in caught)
        iterations = int(np.max(np.atleast_1d(model.n_iter_)))
        if not warned and iterations < limit:
            return model
    raise ModelingPilotError(
        "Elastic Net não convergiu após 500.000 iterações; resultado recusado."
    )


def tune_linear_model(
    algorithm: Literal["ridge", "elastic_net"],
    inner_data: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]],
    *,
    seed: int,
) -> tuple[dict[str, float], dict[str, float]]:
    """Avalia a grade fixa; warm-start acelera Elastic Net sem mudar candidatos."""

    if algorithm == "ridge":
        scores: dict[tuple[float, ...], list[float]] = defaultdict(list)
        for x_train, y_train, x_validation, y_validation in inner_data:
            for alpha in RIDGE_ALPHAS:
                model = Ridge(alpha=alpha).fit(x_train, y_train)
                prediction = model.predict(x_validation)
                scores[(alpha,)].append(regression_metrics(y_validation, prediction)["mae"])
        means = {key: float(np.mean(value)) for key, value in scores.items()}
        selected = min(means, key=lambda key: (means[key], -key[0]))
        return {"alpha": selected[0]}, {str(key[0]): value for key, value in means.items()}

    scores = defaultdict(list)
    descending_alphas = sorted(ELASTIC_NET_ALPHAS, reverse=True)
    for inner_index, (x_train, y_train, x_validation, y_validation) in enumerate(inner_data):
        for ratio in ELASTIC_NET_L1_RATIOS:
            model = ElasticNet(
                l1_ratio=ratio,
                max_iter=50_000,
                tol=1e-3,
                random_state=seed + inner_index,
                warm_start=True,
            )
            for alpha in descending_alphas:
                model.set_params(alpha=alpha)
                _fit_elastic_net_checked(model, x_train, y_train)
                prediction = model.predict(x_validation)
                scores[(alpha, ratio)].append(regression_metrics(y_validation, prediction)["mae"])
    means = {key: float(np.mean(value)) for key, value in scores.items()}
    selected = min(means, key=lambda key: (means[key], -key[0], -key[1]))
    return (
        {"alpha": selected[0], "l1_ratio": selected[1]},
        {f"{key[0]}|{key[1]}": value for key, value in means.items()},
    )


def parameter_on_boundary(algorithm: str, params: dict[str, float]) -> dict[str, bool]:
    if algorithm == "ridge":
        return {
            "alpha_lower": params["alpha"] == min(RIDGE_ALPHAS),
            "alpha_upper": params["alpha"] == max(RIDGE_ALPHAS),
        }
    return {
        "alpha_lower": params["alpha"] == min(ELASTIC_NET_ALPHAS),
        "alpha_upper": params["alpha"] == max(ELASTIC_NET_ALPHAS),
        "l1_ratio_lower": params["l1_ratio"] == min(ELASTIC_NET_L1_RATIOS),
        "l1_ratio_upper": params["l1_ratio"] == max(ELASTIC_NET_L1_RATIOS),
    }


def _prepare_nested_representation(
    matrix: pl.DataFrame,
    target: np.ndarray,
    groups: np.ndarray,
    folds: np.ndarray,
    outer_fold: int,
    representation: Representation,
    blocks: FeatureBlocks,
    *,
    include_baseline: bool = True,
) -> dict[str, Any]:
    outer_train = np.flatnonzero(folds != outer_fold)
    outer_validation = np.flatnonzero(folds == outer_fold)
    columns = representation_columns(representation, blocks, include_baseline=include_baseline)
    frame = matrix.select(columns)
    inner_fold = _inner_folds(target[outer_train], groups[outer_train], outer_fold)
    inner_data: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = []
    inner_indices: list[tuple[np.ndarray, np.ndarray]] = []
    for fold in range(INNER_FOLDS):
        train_local = np.flatnonzero(inner_fold != fold)
        validation_local = np.flatnonzero(inner_fold == fold)
        train_global = outer_train[train_local]
        validation_global = outer_train[validation_local]
        transformer = build_representation_transformer(
            representation, blocks, include_baseline=include_baseline
        )
        x_train = transformer.fit_transform(_take(frame, train_global))
        x_validation = transformer.transform(_take(frame, validation_global))
        inner_data.append((x_train, target[train_global], x_validation, target[validation_global]))
        inner_indices.append((train_global, validation_global))
    outer_transformer = build_representation_transformer(
        representation, blocks, include_baseline=include_baseline
    )
    x_outer_train = outer_transformer.fit_transform(_take(frame, outer_train))
    x_outer_validation = outer_transformer.transform(_take(frame, outer_validation))
    return {
        "outer_train": outer_train,
        "outer_validation": outer_validation,
        "inner_data": inner_data,
        "inner_indices": inner_indices,
        "transformer": outer_transformer,
        "x_train": x_outer_train,
        "x_validation": x_outer_validation,
        "components": _components(outer_transformer),
        "feature_groups": _feature_groups(outer_transformer),
        "transformed_features": int(x_outer_train.shape[1]),
    }


def run_main_recalibration(
    matrix: pl.DataFrame,
    folds: np.ndarray,
    groups: np.ndarray,
    target: np.ndarray,
    blocks: FeatureBlocks,
    *,
    progress: Any = None,
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    predictions = {
        f"{algorithm}__{representation.key}": np.full(matrix.height, np.nan)
        for algorithm in ("ridge", "elastic_net")
        for representation in MAIN_REPRESENTATIONS
    }
    rows: list[dict[str, Any]] = []
    for representation in MAIN_REPRESENTATIONS:
        for outer_fold in range(OUTER_FOLDS):
            started_preprocessing = time.perf_counter()
            prepared = _prepare_nested_representation(
                matrix,
                target,
                groups,
                folds,
                outer_fold,
                representation,
                blocks,
            )
            preprocessing_seconds = time.perf_counter() - started_preprocessing
            for algorithm in ("ridge", "elastic_net"):
                started = time.perf_counter()
                selected, _ = tune_linear_model(
                    algorithm, prepared["inner_data"], seed=SEED + outer_fold
                )
                model = _fit_model(
                    algorithm,
                    selected,
                    prepared["x_train"],
                    target[prepared["outer_train"]],
                    seed=SEED + outer_fold,
                )
                train_prediction = model.predict(prepared["x_train"])
                validation_prediction = model.predict(prepared["x_validation"])
                duration = time.perf_counter() - started
                key = f"{algorithm}__{representation.key}"
                predictions[key][prepared["outer_validation"]] = validation_prediction
                train_metrics = regression_metrics(
                    target[prepared["outer_train"]], train_prediction
                )
                validation_metrics = regression_metrics(
                    target[prepared["outer_validation"]], validation_prediction
                )
                rows.append(
                    {
                        "analysis": "main",
                        "algorithm": algorithm,
                        "block": representation.block,
                        "variant": representation.variant,
                        "model_key": key,
                        "scope": "fold",
                        "fold": outer_fold,
                        "n": int(prepared["outer_validation"].size),
                        "groups": len(set(groups[prepared["outer_validation"]])),
                        **validation_metrics,
                        "train_mae": train_metrics["mae"],
                        "validation_minus_train_mae": validation_metrics["mae"]
                        - train_metrics["mae"],
                        "selected_params": _json(selected),
                        "selection_boundary": _json(parameter_on_boundary(algorithm, selected)),
                        "coefficient_diagnostics": _json(
                            coefficient_diagnostics(model.coef_, prepared["feature_groups"])
                        ),
                        "lfm_pca_components": prepared["components"]["lfm"],
                        "embedding_pca_components": prepared["components"]["embedding"],
                        "transformed_features": prepared["transformed_features"],
                        "preprocessing_seconds": preprocessing_seconds,
                        "training_tuning_seconds": duration,
                    }
                )
                if progress is not None:
                    progress("main", algorithm, representation.key, outer_fold + 1, OUTER_FOLDS)
    for key, prediction in predictions.items():
        if np.isnan(prediction).any():
            raise ModelingPilotError(f"Predições OOF incompletas: {key}")
        algorithm, block, variant = key.split("__")
        fold_rows = [row for row in rows if row["model_key"] == key]
        rows.append(
            {
                "analysis": "main",
                "algorithm": algorithm,
                "block": block,
                "variant": variant,
                "model_key": key,
                "scope": "overall_oof",
                "fold": None,
                "n": matrix.height,
                "groups": len(set(groups)),
                **regression_metrics(target, prediction),
                "train_mae": float(np.mean([row["train_mae"] for row in fold_rows])),
                "validation_minus_train_mae": float(
                    np.mean([row["validation_minus_train_mae"] for row in fold_rows])
                ),
                "selected_params": _json([json.loads(row["selected_params"]) for row in fold_rows]),
                "selection_boundary": _json(
                    [json.loads(row["selection_boundary"]) for row in fold_rows]
                ),
                "coefficient_diagnostics": _json(
                    [json.loads(row["coefficient_diagnostics"]) for row in fold_rows]
                ),
                "lfm_pca_components": (
                    float(
                        np.mean(
                            [
                                row["lfm_pca_components"]
                                for row in fold_rows
                                if row["lfm_pca_components"] is not None
                            ]
                        )
                    )
                    if any(row["lfm_pca_components"] is not None for row in fold_rows)
                    else None
                ),
                "embedding_pca_components": (
                    float(
                        np.mean(
                            [
                                row["embedding_pca_components"]
                                for row in fold_rows
                                if row["embedding_pca_components"] is not None
                            ]
                        )
                    )
                    if any(row["embedding_pca_components"] is not None for row in fold_rows)
                    else None
                ),
                "transformed_features": float(
                    np.mean([row["transformed_features"] for row in fold_rows])
                ),
                "preprocessing_seconds": float(
                    np.sum([row["preprocessing_seconds"] for row in fold_rows])
                ),
                "training_tuning_seconds": float(
                    np.sum([row["training_tuning_seconds"] for row in fold_rows])
                ),
            }
        )
    return predictions, rows


def reproduce_v03_baseline(
    matrix: pl.DataFrame,
    folds: np.ndarray,
    target: np.ndarray,
    blocks: FeatureBlocks,
) -> np.ndarray:
    """Reajusta o Baseline v0.3 com os parâmetros originalmente selecionados."""

    frame = matrix.select(list(blocks.baseline))
    prediction = np.full(matrix.height, np.nan)
    for fold in range(OUTER_FOLDS):
        train = np.flatnonzero(folds != fold)
        validation = np.flatnonzero(folds == fold)
        transformer = build_representation_transformer(Representation("baseline", "raw"), blocks)
        x_train = transformer.fit_transform(_take(frame, train))
        x_validation = transformer.transform(_take(frame, validation))
        model = ElasticNet(
            alpha=0.03,
            l1_ratio=0.8,
            max_iter=20_000,
            tol=1e-3,
            random_state=SEED + fold,
        ).fit(x_train, target[train])
        prediction[validation] = model.predict(x_validation)
    if np.isnan(prediction).any():
        raise ModelingPilotError("Reprodução do Baseline v0.3 incompleta.")
    return prediction


def crossfit_fixed_baseline(
    matrix: pl.DataFrame,
    target: np.ndarray,
    groups: np.ndarray,
    outer_train: np.ndarray,
    outer_validation: np.ndarray,
    outer_fold: int,
    blocks: FeatureBlocks,
) -> tuple[np.ndarray, np.ndarray, list[dict[str, int]]]:
    """Baseline v0.3 fixo; cada resíduo de treino vem de modelo que não viu sua linha."""

    frame = matrix.select(list(blocks.baseline))
    local_folds = _inner_folds(target[outer_train], groups[outer_train], outer_fold)
    crossfit = np.full(outer_train.size, np.nan)
    audit: list[dict[str, int]] = []
    for inner_fold in range(INNER_FOLDS):
        train_local = np.flatnonzero(local_folds != inner_fold)
        validation_local = np.flatnonzero(local_folds == inner_fold)
        train_global = outer_train[train_local]
        validation_global = outer_train[validation_local]
        transformer = build_representation_transformer(Representation("baseline", "raw"), blocks)
        x_train = transformer.fit_transform(_take(frame, train_global))
        x_validation = transformer.transform(_take(frame, validation_global))
        model = ElasticNet(
            alpha=0.03,
            l1_ratio=0.8,
            max_iter=50_000,
            tol=1e-3,
            random_state=SEED + outer_fold,
        ).fit(x_train, target[train_global])
        crossfit[validation_local] = model.predict(x_validation)
        audit.append(
            {
                "inner_fold": inner_fold,
                "train_rows": int(train_global.size),
                "validation_rows": int(validation_global.size),
                "overlap": int(len(set(train_global) & set(validation_global))),
            }
        )
    if np.isnan(crossfit).any() or any(row["overlap"] for row in audit):
        raise ModelingPilotError("Cross-fitting do Baseline inválido.")
    outer_transformer = build_representation_transformer(Representation("baseline", "raw"), blocks)
    x_train = outer_transformer.fit_transform(_take(frame, outer_train))
    x_validation = outer_transformer.transform(_take(frame, outer_validation))
    final_model = ElasticNet(
        alpha=0.03,
        l1_ratio=0.8,
        max_iter=50_000,
        tol=1e-3,
        random_state=SEED + outer_fold,
    ).fit(x_train, target[outer_train])
    validation_prediction = final_model.predict(x_validation)
    return crossfit, validation_prediction, audit


def combine_baseline_and_correction(
    baseline_prediction: np.ndarray, residual_correction: np.ndarray
) -> np.ndarray:
    """Combinação aditiva definida previamente para a análise residual."""

    baseline_prediction = np.asarray(baseline_prediction, dtype=float)
    residual_correction = np.asarray(residual_correction, dtype=float)
    if baseline_prediction.shape != residual_correction.shape:
        raise ValueError("Baseline e correção residual devem ter a mesma dimensão.")
    return baseline_prediction + residual_correction


def run_residual_analysis(
    matrix: pl.DataFrame,
    folds: np.ndarray,
    groups: np.ndarray,
    target: np.ndarray,
    blocks: FeatureBlocks,
    *,
    progress: Any = None,
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]], dict[str, Any]]:
    predictions = {
        f"residual_ridge__{block}__pca90": np.full(matrix.height, np.nan)
        for block in RESIDUAL_BLOCKS
    }
    rows: list[dict[str, Any]] = []
    crossfit_audit: list[dict[str, Any]] = []
    for outer_fold in range(OUTER_FOLDS):
        outer_train = np.flatnonzero(folds != outer_fold)
        outer_validation = np.flatnonzero(folds == outer_fold)
        baseline_crossfit, baseline_validation, baseline_audit = crossfit_fixed_baseline(
            matrix,
            target,
            groups,
            outer_train,
            outer_validation,
            outer_fold,
            blocks,
        )
        residual_target = target[outer_train] - baseline_crossfit
        crossfit_audit.extend([{"outer_fold": outer_fold, **item} for item in baseline_audit])
        for block in RESIDUAL_BLOCKS:
            representation = Representation(block, "pca90")
            columns = representation_columns(representation, blocks, include_baseline=False)
            frame = matrix.select(columns)
            local_folds = _inner_folds(target[outer_train], groups[outer_train], outer_fold)
            inner_data: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = []
            fitted_inner: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = []
            for inner_fold in range(INNER_FOLDS):
                train_local = np.flatnonzero(local_folds != inner_fold)
                validation_local = np.flatnonzero(local_folds == inner_fold)
                train_global = outer_train[train_local]
                validation_global = outer_train[validation_local]
                transformer = build_representation_transformer(
                    representation, blocks, include_baseline=False
                )
                x_train = transformer.fit_transform(_take(frame, train_global))
                x_validation = transformer.transform(_take(frame, validation_global))
                inner_data.append(
                    (
                        x_train,
                        residual_target[train_local],
                        x_validation,
                        residual_target[validation_local],
                    )
                )
                fitted_inner.append((train_local, validation_local, x_train, x_validation))
            selected, _ = tune_linear_model("ridge", inner_data, seed=SEED + outer_fold)
            residual_crossfit = np.full(outer_train.size, np.nan)
            for train_local, validation_local, x_train, x_validation in fitted_inner:
                model = Ridge(alpha=selected["alpha"]).fit(x_train, residual_target[train_local])
                residual_crossfit[validation_local] = model.predict(x_validation)
            if np.isnan(residual_crossfit).any():
                raise ModelingPilotError("Correção residual cross-fitted incompleta.")
            outer_transformer = build_representation_transformer(
                representation, blocks, include_baseline=False
            )
            x_outer_train = outer_transformer.fit_transform(_take(frame, outer_train))
            x_outer_validation = outer_transformer.transform(_take(frame, outer_validation))
            residual_model = Ridge(alpha=selected["alpha"]).fit(x_outer_train, residual_target)
            correction_validation = residual_model.predict(x_outer_validation)
            validation_prediction = combine_baseline_and_correction(
                baseline_validation, correction_validation
            )
            train_crossfit_prediction = combine_baseline_and_correction(
                baseline_crossfit, residual_crossfit
            )
            key = f"residual_ridge__{block}__pca90"
            predictions[key][outer_validation] = validation_prediction
            validation_metrics = regression_metrics(target[outer_validation], validation_prediction)
            train_metrics = regression_metrics(target[outer_train], train_crossfit_prediction)
            components = _components(outer_transformer)
            rows.append(
                {
                    "analysis": "residual",
                    "algorithm": "residual_ridge",
                    "block": block,
                    "variant": "pca90",
                    "model_key": key,
                    "scope": "fold",
                    "fold": outer_fold,
                    "n": int(outer_validation.size),
                    "groups": len(set(groups[outer_validation])),
                    **validation_metrics,
                    "train_mae": train_metrics["mae"],
                    "validation_minus_train_mae": validation_metrics["mae"] - train_metrics["mae"],
                    "selected_params": _json(selected),
                    "selection_boundary": _json(parameter_on_boundary("ridge", selected)),
                    "coefficient_diagnostics": _json(
                        coefficient_diagnostics(
                            residual_model.coef_, _feature_groups(outer_transformer)
                        )
                    ),
                    "lfm_pca_components": components["lfm"],
                    "embedding_pca_components": components["embedding"],
                    "transformed_features": int(x_outer_train.shape[1]),
                    "preprocessing_seconds": None,
                    "training_tuning_seconds": None,
                    "baseline_crossfit_train_mae": regression_metrics(
                        target[outer_train], baseline_crossfit
                    )["mae"],
                    "correction_l2_norm_validation": float(np.linalg.norm(correction_validation)),
                }
            )
            if progress is not None:
                progress("residual", "ridge", block, outer_fold + 1, OUTER_FOLDS)
    for key, prediction in predictions.items():
        if np.isnan(prediction).any():
            raise ModelingPilotError(f"Predições residuais OOF incompletas: {key}")
        _, block, variant = key.split("__")
        fold_rows = [row for row in rows if row["model_key"] == key]
        rows.append(
            {
                "analysis": "residual",
                "algorithm": "residual_ridge",
                "block": block,
                "variant": variant,
                "model_key": key,
                "scope": "overall_oof",
                "fold": None,
                "n": matrix.height,
                "groups": len(set(groups)),
                **regression_metrics(target, prediction),
                "train_mae": float(np.mean([row["train_mae"] for row in fold_rows])),
                "validation_minus_train_mae": float(
                    np.mean([row["validation_minus_train_mae"] for row in fold_rows])
                ),
                "selected_params": _json([json.loads(row["selected_params"]) for row in fold_rows]),
                "selection_boundary": _json(
                    [json.loads(row["selection_boundary"]) for row in fold_rows]
                ),
                "coefficient_diagnostics": _json(
                    [json.loads(row["coefficient_diagnostics"]) for row in fold_rows]
                ),
                "lfm_pca_components": float(
                    np.mean(
                        [
                            row["lfm_pca_components"]
                            for row in fold_rows
                            if row["lfm_pca_components"] is not None
                        ]
                    )
                )
                if any(row["lfm_pca_components"] is not None for row in fold_rows)
                else None,
                "embedding_pca_components": float(
                    np.mean(
                        [
                            row["embedding_pca_components"]
                            for row in fold_rows
                            if row["embedding_pca_components"] is not None
                        ]
                    )
                )
                if any(row["embedding_pca_components"] is not None for row in fold_rows)
                else None,
                "transformed_features": float(
                    np.mean([row["transformed_features"] for row in fold_rows])
                ),
                "preprocessing_seconds": None,
                "training_tuning_seconds": None,
                "baseline_crossfit_train_mae": float(
                    np.mean([row["baseline_crossfit_train_mae"] for row in fold_rows])
                ),
                "correction_l2_norm_validation": float(
                    np.mean([row["correction_l2_norm_validation"] for row in fold_rows])
                ),
            }
        )
    return (
        predictions,
        rows,
        {
            "crossfit_rows": EXPECTED_ROWS * (OUTER_FOLDS - 1),
            "inner_audit": crossfit_audit,
            "in_sample_residual_rows": 0,
            "validation_residuals_used_for_training": False,
            "baseline_fixed_params": {"alpha": 0.03, "l1_ratio": 0.8},
        },
    )


def _fold_gain_count(
    candidate_key: str,
    baseline_key: str,
    metrics: list[dict[str, Any]],
) -> int:
    candidate = {
        row["fold"]: row["mae"]
        for row in metrics
        if row["scope"] == "fold" and row["model_key"] == candidate_key
    }
    baseline = {
        row["fold"]: row["mae"]
        for row in metrics
        if row["scope"] == "fold" and row["model_key"] == baseline_key
    }
    return sum(candidate[fold] < baseline[fold] for fold in range(OUTER_FOLDS))


def compare_to_baseline(
    target: np.ndarray,
    groups: np.ndarray,
    predictions: dict[str, np.ndarray],
    metrics: list[dict[str, Any]],
    baseline_key: str,
) -> list[dict[str, Any]]:
    baseline_prediction = predictions[baseline_key]
    comparisons = []
    for index, (key, candidate) in enumerate(sorted(predictions.items())):
        if key == baseline_key or key.startswith(("historical_", "reproduced_")):
            continue
        result = grouped_paired_bootstrap(
            target,
            baseline_prediction,
            candidate,
            groups,
            repetitions=BOOTSTRAP_REPETITIONS,
            seed=SEED + index,
        )
        overall = next(
            row for row in metrics if row["scope"] == "overall_oof" and row["model_key"] == key
        )
        severe_overfit = (
            overall["validation_minus_train_mae"] > OVERFITTING_GAP_FRACTION * overall["mae"]
        )
        comparisons.append(
            {
                "model_key": key,
                **result,
                "folds_improved": _fold_gain_count(key, baseline_key, metrics),
                "severe_overfitting": severe_overfit,
            }
        )
    return comparisons


def classify_incremental_evidence(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    """Aplica literalmente a regra registrada antes da observação dos resultados."""

    letter_models = [row for row in comparisons if "baseline__raw" not in row["model_key"]]
    qualifying = [
        row
        for row in letter_models
        if row["mae_percent_difference"] <= -MINIMUM_INCREMENTAL_GAIN_PERCENT
        and row["mae_ci95_high"] < 0
        and not row["severe_overfitting"]
        and row["folds_improved"] >= 4
    ]
    if qualifying:
        category = "evidência piloto de ganho incremental"
    elif any(row["mae_difference"] < 0 for row in letter_models):
        category = "sinal inconclusivo"
    else:
        category = "sem ganho incremental"
    return {
        "category": category,
        "qualifying_models": [row["model_key"] for row in qualifying],
        "minimum_gain_percent": MINIMUM_INCREMENTAL_GAIN_PERCENT,
        "required_folds_improved": 4,
        "severe_overfitting_definition": ("gap médio validação−treino maior que 25% do MAE OOF"),
    }


def _language_sensitivity(
    matrix: pl.DataFrame,
    target: np.ndarray,
    predictions: dict[str, np.ndarray],
) -> dict[str, Any]:
    english = matrix["language_status"].to_numpy() == "english"
    return {
        "english_rows": int(np.sum(english)),
        "non_english_rows_removed": int(np.sum(~english)),
        "method": "recalcular métricas OOF sem retunar ou reescolher modelos",
        "models": [
            {
                "model_key": key,
                **regression_metrics(target[english], prediction[english]),
                "full_mae": regression_metrics(target, prediction)["mae"],
                "mae_change": regression_metrics(target[english], prediction[english])["mae"]
                - regression_metrics(target, prediction)["mae"],
            }
            for key, prediction in sorted(predictions.items())
            if not key.startswith(("historical_", "reproduced_"))
        ],
    }


def _frequency_tables(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    keys = sorted({row["model_key"] for row in metrics if row["scope"] == "fold"})
    for key in keys:
        params = [
            row["selected_params"]
            for row in metrics
            if row["scope"] == "fold" and row["model_key"] == key
        ]
        boundaries = [
            json.loads(row["selection_boundary"])
            for row in metrics
            if row["scope"] == "fold" and row["model_key"] == key
        ]
        result[key] = {
            "selected_parameter_frequency": dict(Counter(params)),
            "boundary_selection_counts": {
                boundary: sum(bool(item.get(boundary)) for item in boundaries)
                for boundary in sorted({name for item in boundaries for name in item})
            },
        }
    return result


def _write_private_outputs(
    matrix: pl.DataFrame,
    folds: np.ndarray,
    target: np.ndarray,
    predictions: dict[str, np.ndarray],
    metrics: list[dict[str, Any]],
) -> None:
    directory = _project(PRIVATE_DIRECTORY)
    directory.mkdir(parents=True, exist_ok=True)
    frame = matrix.select(
        "composition_key",
        "track_id",
        "artist_group_id",
        "composition_group_id",
        "language_status",
    ).with_columns(
        pl.Series("outer_fold", folds),
        pl.Series("spotify_popularity", target),
    )
    frame = frame.with_columns(
        [pl.Series(f"prediction__{key}", value) for key, value in predictions.items()]
    )
    frame.write_parquet(directory / OOF_NAME, compression="zstd")
    fold_rows = [row for row in metrics if row["scope"] == "fold"]
    pl.DataFrame(fold_rows, strict=False).write_parquet(
        directory / FOLD_RESULTS_NAME, compression="zstd"
    )


METRIC_FIELDS = [
    "analysis",
    "algorithm",
    "block",
    "variant",
    "model_key",
    "scope",
    "fold",
    "n",
    "groups",
    "mae",
    "rmse",
    "r2",
    "spearman",
    "train_mae",
    "validation_minus_train_mae",
    "selected_params",
    "selection_boundary",
    "coefficient_diagnostics",
    "lfm_pca_components",
    "embedding_pca_components",
    "transformed_features",
    "preprocessing_seconds",
    "training_tuning_seconds",
]


def _write_metrics(metrics: list[dict[str, Any]]) -> None:
    path = _project(METRICS_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(metrics)


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "|" + "|".join("---" for _ in headers) + "|",
            *["| " + " | ".join(_fmt(value) for value in row) + " |" for row in rows],
        ]
    )


def _overall(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in metrics if row["scope"] == "overall_oof"]


def _write_main_report(summary: dict[str, Any]) -> None:
    overall = _overall(summary["metrics"])
    main = [row for row in overall if row["analysis"] == "main"]
    residual = [row for row in overall if row["analysis"] == "residual"]
    comparisons = summary["comparisons_to_baseline"]
    report = [
        "# Recalibração dirigida da modelagem piloto — v0.3.1",
        "",
        "## Escopo",
        "",
        "Teste dirigido de regularização, dimensionalidade e contribuição residual das letras. Nenhum algoritmo foi escolhido retrospectivamente, nenhuma nova letra foi consultada e o holdout oficial não foi acessado.",
        "",
        "## Reprodução da v0.3",
        "",
        f"Amostra: {summary['input_audit']['rows']} composições; chave: `artist_group_id`; folds: {summary['input_audit']['fold_counts']}; hash: `{summary['input_audit']['assignment_sha256']}`.",
        f"Baseline v0.3 reproduzido: MAE {_fmt(summary['baseline_reproduction']['reproduced_v03_mae'])}; histórico: {_fmt(summary['baseline_reproduction']['historical_mae'])}; diferença {_fmt(summary['baseline_reproduction']['reproduction_mae_difference'])}. O Baseline com grade ampliada obteve MAE {_fmt(summary['baseline_reproduction']['expanded_grid_baseline_mae'])}.",
        "",
        "## Modelos principais",
        "",
        _table(
            [
                "Algoritmo",
                "Bloco",
                "Representação",
                "MAE",
                "RMSE",
                "R²",
                "Spearman",
                "MAE treino",
                "Gap",
                "PCA LFM",
                "PCA MiniLM",
            ],
            [
                [
                    row["algorithm"],
                    row["block"],
                    row["variant"],
                    row["mae"],
                    row["rmse"],
                    row["r2"],
                    row["spearman"],
                    row["train_mae"],
                    row["validation_minus_train_mae"],
                    row["lfm_pca_components"],
                    row["embedding_pca_components"],
                ]
                for row in main
            ],
        ),
        "",
        "## Modelos residuais",
        "",
        _table(
            ["Bloco corretor", "MAE", "RMSE", "R²", "Spearman", "MAE treino cross-fit", "Gap"],
            [
                [
                    row["block"],
                    row["mae"],
                    row["rmse"],
                    row["r2"],
                    row["spearman"],
                    row["train_mae"],
                    row["validation_minus_train_mae"],
                ]
                for row in residual
            ],
        ),
        "",
        "## Comparações contra Baseline/Elastic Net recalculado",
        "",
        "Diferenças são candidato menos Baseline; valores negativos indicam melhora. IC95% por 2.000 bootstraps pareados e agrupados por artista.",
        "",
        _table(
            [
                "Modelo",
                "Δ MAE",
                "Δ MAE %",
                "IC95% Δ MAE",
                "Δ RMSE",
                "IC95% Δ RMSE",
                "Δ R²",
                "Folds melhores",
                "Overfit grave",
            ],
            [
                [
                    row["model_key"],
                    row["mae_difference"],
                    row["mae_percent_difference"],
                    f"[{row['mae_ci95_low']:.3f}, {row['mae_ci95_high']:.3f}]",
                    row["rmse_difference"],
                    f"[{row['rmse_ci95_low']:.3f}, {row['rmse_ci95_high']:.3f}]",
                    row["r2_difference"],
                    row["folds_improved"],
                    row["severe_overfitting"],
                ]
                for row in comparisons
            ],
        ),
        "",
        "## Hiperparâmetros e coeficientes",
        "",
        "Parâmetros, seleção em borda, coeficientes não nulos e normas L2 por bloco/fold estão no CSV agregado e no run summary. A grade Ridge contém 15 valores de 0,0001 a 10.000; a Elastic Net contém 60 combinações.",
        "",
        "## Casos não ingleses",
        "",
        f"Foram retirados apenas na reavaliação {summary['language_sensitivity']['non_english_rows_removed']} casos; nenhum idioma entrou como preditor e nenhum modelo foi reescolhido.",
        "",
        "## Regra de decisão",
        "",
        f"Classificação: **{summary['decision']['category']}**. Exigência registrada: redução de pelo menos 2%, IC95% de ΔMAE inteiramente abaixo de zero, ausência de overfitting grave e melhora em pelo menos quatro folds.",
        "",
        "## Limitações",
        "",
        "Validação interna em 1.441 composições com letras aceitas; uma observação Spotify representante por composição; múltiplas configurações previamente definidas; resultados não causais e ainda sem confirmação no holdout.",
        "",
        "## Privacidade e preservação",
        "",
        "Predições, folds, matrizes e resultados individuais permanecem na área ignorada. Relatórios públicos contêm apenas agregados. Base, split, coorte, resultados de letras e embeddings foram preservados byte a byte.",
        "",
        "## Verificação final",
        "",
        "Pendente até a execução pós-modelagem dos testes, lint, hashes e auditorias.",
        "",
    ]
    _project(REPORT_PATH).write_text("\n".join(report), encoding="utf-8")


def _write_residual_report(summary: dict[str, Any]) -> None:
    rows = [
        row
        for row in summary["metrics"]
        if row["analysis"] == "residual" and row["scope"] == "overall_oof"
    ]
    text = "\n".join(
        [
            "# Análise residual com cross-fitting — v0.3.1",
            "",
            "O Baseline fixo (`alpha=0.03`, `l1_ratio=0.8`) gerou predições cross-fitted no treino externo. Cada resíduo foi calculado para uma observação que não participou do ajuste que a predisse. Uma Ridge, ajustada sobre PCAs textuais dentro dos folds, estimou a correção somada ao Baseline na validação externa.",
            "",
            _table(
                ["Correção", "MAE", "RMSE", "R²", "Spearman", "Gap", "PCA LFM", "PCA MiniLM"],
                [
                    [
                        row["block"],
                        row["mae"],
                        row["rmse"],
                        row["r2"],
                        row["spearman"],
                        row["validation_minus_train_mae"],
                        row["lfm_pca_components"],
                        row["embedding_pca_components"],
                    ]
                    for row in rows
                ],
            ),
            "",
            f"Resíduos in-sample usados como alvo: {summary['residual_audit']['in_sample_residual_rows']}. Resíduos da validação externa usados no treino: {summary['residual_audit']['validation_residuals_used_for_training']}.",
            "",
            "Esta análise é secundária e não substitui os quatro blocos principais.",
            "",
        ]
    )
    _project(RESIDUAL_REPORT_PATH).write_text(text, encoding="utf-8")


def _create_figures(summary: dict[str, Any]) -> list[str]:
    directory = _project(FIGURE_DIRECTORY)
    directory.mkdir(parents=True, exist_ok=True)
    overall = _overall(summary["metrics"])
    comparisons = summary["comparisons_to_baseline"]
    created = []

    def save(name: str) -> None:
        plt.tight_layout()
        plt.savefig(directory / name, dpi=160, bbox_inches="tight")
        plt.close()
        created.append(name)

    labels = [row["model_key"] for row in overall]
    plt.figure(figsize=(14, 6))
    plt.bar(np.arange(len(labels)), [row["mae"] for row in overall], color="#4472C4")
    plt.axhline(
        summary["baseline_reproduction"]["expanded_grid_baseline_mae"],
        color="black",
        linestyle="--",
        label="Baseline Elastic Net",
    )
    plt.xticks(np.arange(len(labels)), labels, rotation=55, ha="right", fontsize=7)
    plt.ylabel("MAE OOF")
    plt.title("Recalibração dirigida — configurações predefinidas")
    plt.legend()
    save("mae_all_configurations.png")

    labels = [row["model_key"] for row in comparisons]
    estimates = np.array([row["mae_difference"] for row in comparisons])
    lower = estimates - np.array([row["mae_ci95_low"] for row in comparisons])
    upper = np.array([row["mae_ci95_high"] for row in comparisons]) - estimates
    plt.figure(figsize=(10, max(6, len(labels) * 0.38)))
    y = np.arange(len(labels))
    plt.errorbar(estimates, y, xerr=np.vstack([lower, upper]), fmt="o", color="#C00000")
    plt.axvline(0, color="black", linestyle="--")
    plt.yticks(y, labels, fontsize=7)
    plt.xlabel("Δ MAE candidato − Baseline (IC95%)")
    plt.title("Bootstrap pareado e agrupado por artista")
    save("mae_differences_bootstrap.png")

    pca_folds = [
        row for row in summary["metrics"] if row["scope"] == "fold" and row["variant"] == "pca90"
    ]
    model_keys = sorted({row["model_key"] for row in pca_folds})
    plt.figure(figsize=(12, 6))
    for key in model_keys:
        rows = [row for row in pca_folds if row["model_key"] == key]
        components = [
            (row["lfm_pca_components"] or 0) + (row["embedding_pca_components"] or 0)
            for row in rows
        ]
        plt.plot(range(OUTER_FOLDS), components, marker="o", label=key)
    plt.xticks(range(OUTER_FOLDS))
    plt.xlabel("Fold externo")
    plt.ylabel("Componentes PCA totais")
    plt.title("Dimensionalidade retida por bloco e fold")
    plt.legend(fontsize=6, ncol=2)
    save("pca_components_by_fold.png")

    fold_rows = [row for row in summary["metrics"] if row["scope"] == "fold"]
    plt.figure(figsize=(12, 6))
    for key in sorted({row["model_key"] for row in fold_rows}):
        rows = [row for row in fold_rows if row["model_key"] == key]
        plt.plot(
            [row["fold"] for row in rows],
            [row["mae"] for row in rows],
            marker="o",
            label=key,
        )
    plt.xticks(range(OUTER_FOLDS))
    plt.xlabel("Fold externo")
    plt.ylabel("MAE")
    plt.title("Desempenho por fold")
    plt.legend(fontsize=5, ncol=3)
    save("mae_by_fold.png")
    return created


def _git_private_files() -> dict[str, list[str]]:
    prefixes = (
        "data/derived/private_modeling/",
        "data/derived/private_embeddings/",
        "data/raw/lyrics_private/",
        "data/interim/lyrics_private/",
    )
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True
    ).stdout.splitlines()
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    return {
        "tracked": [path for path in tracked if path.replace("\\", "/").startswith(prefixes)],
        "staged": [path for path in staged if path.replace("\\", "/").startswith(prefixes)],
    }


def audit_public_outputs(paths: list[str]) -> dict[str, Any]:
    markers = (
        "lyrics_sha256",
        "plainLyrics",
        "syncedLyrics",
        "data/derived/private_modeling",
        "data/derived/private_embeddings",
        "data/raw/lyrics_private",
    )
    violations = []
    for relative in paths:
        path = _project(relative)
        if path.suffix.lower() not in {".md", ".csv", ".json"}:
            continue
        text = path.read_text(encoding="utf-8")
        violations.extend(f"{relative}:{marker}" for marker in markers if marker in text)
    if violations:
        raise ModelingPilotError(f"Violação de privacidade pública: {violations}")
    private = _git_private_files()
    if private["tracked"] or private["staged"]:
        raise ModelingPilotError(f"Arquivos privados tracked/staged: {private}")
    return {
        "forbidden_marker_occurrences": 0,
        "tracked_private_files": [],
        "staged_private_files": [],
    }


def run_modeling_recalibration_v031(progress: Any = None) -> dict[str, Any]:
    started = time.perf_counter()
    frozen_before = _hash_files(FROZEN_INPUTS)
    lyrics_cache_before = _directory_fingerprint("data/raw/lyrics_private/lrclib_cache_v0_1")
    matrix, folds, groups, target, blocks, input_audit = load_and_validate_v03_inputs()
    main_predictions, main_metrics = run_main_recalibration(
        matrix, folds, groups, target, blocks, progress=progress
    )
    residual_predictions, residual_metrics, residual_audit = run_residual_analysis(
        matrix, folds, groups, target, blocks, progress=progress
    )
    predictions = {**main_predictions, **residual_predictions}
    historical = pl.read_parquet(
        _project(V03_OOF),
        columns=["prediction__elastic_net__baseline__raw"],
    )["prediction__elastic_net__baseline__raw"].to_numpy()
    reproduced_v03 = reproduce_v03_baseline(matrix, folds, target, blocks)
    predictions["historical_v03__elastic_net__baseline"] = historical
    predictions["reproduced_v03__elastic_net__baseline"] = reproduced_v03
    metrics = [*main_metrics, *residual_metrics]
    baseline_key = "elastic_net__baseline__raw"
    comparisons = compare_to_baseline(target, groups, predictions, metrics, baseline_key)
    decision = classify_incremental_evidence(comparisons)
    recalibrated_baseline = predictions[baseline_key]
    baseline_reproduction = {
        "historical_mae": regression_metrics(target, historical)["mae"],
        "reproduced_v03_mae": regression_metrics(target, reproduced_v03)["mae"],
        "expanded_grid_baseline_mae": regression_metrics(target, recalibrated_baseline)["mae"],
        "reproduction_mae_difference": regression_metrics(target, reproduced_v03)["mae"]
        - regression_metrics(target, historical)["mae"],
        "expanded_grid_mae_difference_vs_v03": regression_metrics(target, recalibrated_baseline)[
            "mae"
        ]
        - regression_metrics(target, historical)["mae"],
        "reproduction_maximum_absolute_prediction_difference": float(
            np.max(np.abs(reproduced_v03 - historical))
        ),
    }
    language = _language_sensitivity(matrix, target, predictions)
    _write_private_outputs(matrix, folds, target, predictions, metrics)
    _write_metrics(metrics)

    frozen_after = _hash_files(FROZEN_INPUTS)
    lyrics_cache_after = _directory_fingerprint("data/raw/lyrics_private/lrclib_cache_v0_1")
    if frozen_before != frozen_after or lyrics_cache_before != lyrics_cache_after:
        raise ModelingPilotError("Artefatos congelados foram alterados durante a recalibração.")
    private_hashes = {
        OOF_NAME: sha256_file(_project(PRIVATE_DIRECTORY) / OOF_NAME),
        FOLD_RESULTS_NAME: sha256_file(_project(PRIVATE_DIRECTORY) / FOLD_RESULTS_NAME),
    }
    summary: dict[str, Any] = {
        "status": "recalibration_complete_verification_pending",
        "protocol_version": PROTOCOL_VERSION,
        "timestamp": utc_now(),
        "checkpoint_commit": git_commit(),
        "checkpoint_tag": "modeling-pilot-v0.3",
        "seed": SEED,
        "target": "spotify_popularity",
        "grouping_key": "artist_group_id",
        "input_audit": input_audit,
        "feature_blocks": {
            "baseline": len(blocks.baseline),
            "traditional_descriptors": len(blocks.traditional),
            "embedding_dimensions": len(blocks.embeddings),
            "traditional_total": len(blocks.columns("traditional")),
            "deep_total": len(blocks.columns("deep")),
            "combined_total": len(blocks.columns("combined")),
            "forbidden_predictors": [],
        },
        "grids": {
            "ridge_alphas": list(RIDGE_ALPHAS),
            "elastic_net_alphas": list(ELASTIC_NET_ALPHAS),
            "elastic_net_l1_ratios": list(ELASTIC_NET_L1_RATIOS),
        },
        "metrics": metrics,
        "parameter_frequencies": _frequency_tables(metrics),
        "comparisons_to_baseline": comparisons,
        "baseline_reproduction": baseline_reproduction,
        "residual_audit": residual_audit,
        "language_sensitivity": language,
        "decision": decision,
        "frozen_hashes_before": frozen_before,
        "frozen_hashes_after": frozen_after,
        "lyrics_cache_fingerprint_before": lyrics_cache_before,
        "lyrics_cache_fingerprint_after": lyrics_cache_after,
        "frozen_artifacts_preserved": True,
        "privacy": {
            "holdout_accessed": False,
            "individual_outputs_public": False,
            "private_output_basenames": [OOF_NAME, FOLD_RESULTS_NAME],
            "tracked_private_files": [],
            "staged_private_files": [],
        },
        "private_output_hashes": private_hashes,
        "duration_seconds": time.perf_counter() - started,
        "verification": {"status": "pending", "checks": []},
    }
    _write_main_report(summary)
    _write_residual_report(summary)
    figures = _create_figures(summary)
    summary["figures"] = figures
    public_paths = [
        REPORT_PATH,
        METRICS_PATH,
        RESIDUAL_REPORT_PATH,
        *[f"{FIGURE_DIRECTORY}/{name}" for name in figures],
    ]
    summary["privacy"].update(audit_public_outputs(public_paths))
    summary["public_output_hashes"] = {
        Path(path).name: sha256_file(_project(path)) for path in public_paths
    }
    clean = _clean_json(summary)
    write_json(SUMMARY_PATH, clean)
    return clean


def finalize_recalibration_verification_v031(
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = read_json(SUMMARY_PATH)
    if not isinstance(summary, dict):
        raise ModelingPilotError("Run summary v0.3.1 ausente.")
    frozen_after = _hash_files(FROZEN_INPUTS)
    cache_after = _directory_fingerprint("data/raw/lyrics_private/lrclib_cache_v0_1")
    private = _git_private_files()
    passed = all(int(check["exit_code"]) == 0 for check in checks)
    passed = passed and frozen_after == summary["frozen_hashes_before"]
    passed = passed and cache_after == summary["lyrics_cache_fingerprint_before"]
    passed = passed and not private["tracked"] and not private["staged"]
    summary["frozen_hashes_after"] = frozen_after
    summary["lyrics_cache_fingerprint_after"] = cache_after
    summary["frozen_artifacts_preserved"] = (
        frozen_after == summary["frozen_hashes_before"]
        and cache_after == summary["lyrics_cache_fingerprint_before"]
    )
    summary["privacy"]["tracked_private_files"] = private["tracked"]
    summary["privacy"]["staged_private_files"] = private["staged"]
    summary["verification"] = {
        "status": "passed" if passed else "failed",
        "checks": checks,
    }
    summary["status"] = "complete" if passed else "verification_failed"
    summary = _clean_json(summary)
    _write_metrics(summary["metrics"])
    _write_main_report(summary)
    _write_residual_report(summary)

    report_path = _project(REPORT_PATH)
    report = report_path.read_text(encoding="utf-8")
    heading = "## Verificação final"
    prefix = report.partition(heading)[0]
    verification = "\n".join(
        [
            heading,
            "",
            _table(
                ["Comando/verificação", "Código", "Resultado"],
                [
                    [check["command"], check["exit_code"], check.get("result", "")]
                    for check in checks
                ],
            ),
            "",
            f"Status: **{'aprovado' if passed else 'falhou'}**. Privados tracked/staged: {len(private['tracked'])}/{len(private['staged'])}. Congelados preservados: {summary['frozen_artifacts_preserved']}.",
            "",
        ]
    )
    report_path.write_text(prefix + verification, encoding="utf-8")
    public_paths = [
        REPORT_PATH,
        METRICS_PATH,
        RESIDUAL_REPORT_PATH,
        *[f"{FIGURE_DIRECTORY}/{name}" for name in summary["figures"]],
    ]
    summary["privacy"].update(audit_public_outputs(public_paths))
    summary["public_output_hashes"] = {
        Path(path).name: sha256_file(_project(path)) for path in public_paths
    }
    write_json(SUMMARY_PATH, _clean_json(summary))
    return summary
