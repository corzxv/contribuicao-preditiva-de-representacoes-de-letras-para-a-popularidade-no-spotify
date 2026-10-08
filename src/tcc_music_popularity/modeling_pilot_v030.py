"""Modelagem piloto v0.3 sem acesso ao holdout oficial."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import matplotlib
import numpy as np
import polars as pl
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import PROJECT_ROOT, project_path
from .io import git_commit, read_json, sha256_file, utc_now, write_json

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PROTOCOL_VERSION = "modeling-pilot-v0.3"
SEED = 20261007
OUTER_FOLDS = 5
INNER_FOLDS = 3
BOOTSTRAP_REPETITIONS = 2000
MIN_DIAGNOSTIC_CELL = 30

BASE_PATH = "data/processed/modeling_base_lfm_v0_1_1.parquet"
SPLIT_PATH = "data/processed/split_assignments_v0_1_1.parquet"
EMBEDDING_PATH = "data/derived/private_embeddings/lyrics_embeddings_minilm_v0_2.parquet"
MANIFEST_PATH = "reports/feature_manifest_v0_1_1_revision.csv"
PRIVATE_DIRECTORY = "data/derived/private_modeling"
MATRIX_NAME = "modeling_pilot_matrix_v0_3.parquet"
FOLDS_NAME = "modeling_pilot_fold_assignments_v0_3.parquet"
OOF_NAME = "modeling_pilot_oof_predictions_v0_3.parquet"

REPORT_PATH = "reports/modeling_pilot_report_v0_3.md"
METRICS_PATH = "reports/modeling_pilot_metrics_v0_3.csv"
PCA_REPORT_PATH = "reports/modeling_pilot_pca_sensitivity_v0_3.md"
BLOCKS_REPORT_PATH = "reports/modeling_pilot_feature_blocks_v0_3.md"
SUMMARY_PATH = "reports/run_summary_modeling_pilot_v0_3.json"
FIGURE_DIRECTORY = "reports/figures/modeling_pilot_v0_3"

EXPECTED_ROWS = 1441
EXPECTED_BASELINE = 23
EXPECTED_TRADITIONAL = 196
EXPECTED_EMBEDDINGS = 384

CATEGORICAL_FEATURES = ("genre", "key", "time_signature")
FORBIDDEN_PREDICTORS = {
    "spotify_popularity",
    "genius_lyrics_views",
    "lfm_playcount",
    "spotify_row_id",
    "track_id",
    "composition_key",
    "lfm_record_key",
    "artist_group_id",
    "composition_group_id",
    "split_group_id",
    "split",
    "lyrics_sha256",
    "detected_language",
    "language_status",
    "language_confidence",
    "model_id",
    "model_revision",
    "protocol_version",
}

ELASTIC_NET_GRID = {
    "model__alpha": [0.03, 0.3],
    "model__l1_ratio": [0.1, 0.8],
}
HIST_GRADIENT_BOOSTING_GRID = [
    {"model__learning_rate": [0.05], "model__max_leaf_nodes": [15]},
    {"model__learning_rate": [0.1], "model__max_leaf_nodes": [31]},
]


class ModelingPilotError(RuntimeError):
    """Erro que exige interromper a modelagem antes do treino."""


@dataclass(frozen=True)
class FeatureBlocks:
    """Listas autorizadas pelo manifesto revisado."""

    baseline: tuple[str, ...]
    traditional: tuple[str, ...]
    embeddings: tuple[str, ...]
    traditional_families: dict[str, tuple[str, ...]]

    def columns(self, block: str) -> list[str]:
        if block == "baseline":
            return list(self.baseline)
        if block == "traditional":
            return [*self.baseline, *self.traditional]
        if block == "deep":
            return [*self.baseline, *self.embeddings]
        if block == "combined":
            return [*self.baseline, *self.traditional, *self.embeddings]
        raise ValueError(f"Bloco desconhecido: {block}")


def _project(relative: str) -> Path:
    return project_path(relative)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _clean_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clean_json(item) for item in value]
    if isinstance(value, tuple):
        return [_clean_json(item) for item in value]
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        return None
    return value


def load_feature_blocks(path: str | Path = MANIFEST_PATH) -> FeatureBlocks:
    """Carrega apenas preditoras explicitamente autorizadas na revisão v0.1.1."""

    manifest_path = _project(str(path)) if not Path(path).is_absolute() else Path(path)
    with manifest_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    authorized = [
        row for row in rows if row["autorizada como preditora na revisão"].strip() == "sim"
    ]
    baseline = tuple(
        row["nome"]
        for row in authorized
        if row["modelo em que poderá entrar"] == "baseline; tradicional; profundo; combinado"
    )
    traditional_rows = [
        row for row in authorized if row["modelo em que poderá entrar"] == "tradicional; combinado"
    ]
    traditional = tuple(row["nome"] for row in traditional_rows)
    embeddings = tuple(f"embedding_{index:03d}" for index in range(EXPECTED_EMBEDDINGS))
    families: dict[str, tuple[str, ...]] = {}
    for family in sorted({row["família"] for row in traditional_rows}):
        families[family] = tuple(
            row["nome"] for row in traditional_rows if row["família"] == family
        )
    blocks = FeatureBlocks(baseline, traditional, embeddings, families)
    validate_feature_blocks(blocks)
    return blocks


def validate_feature_blocks(blocks: FeatureBlocks) -> None:
    """Interrompe antes do treino se manifesto e contagens esperadas divergirem."""

    observed = {
        "baseline": len(blocks.baseline),
        "traditional_descriptors": len(blocks.traditional),
        "embedding_dimensions": len(blocks.embeddings),
        "traditional_total": len(blocks.columns("traditional")),
        "deep_total": len(blocks.columns("deep")),
        "combined_total": len(blocks.columns("combined")),
    }
    expected = {
        "baseline": EXPECTED_BASELINE,
        "traditional_descriptors": EXPECTED_TRADITIONAL,
        "embedding_dimensions": EXPECTED_EMBEDDINGS,
        "traditional_total": 219,
        "deep_total": 407,
        "combined_total": 603,
    }
    if observed != expected:
        raise ModelingPilotError(
            f"Contagens do manifesto divergentes; observado={observed}; esperado={expected}"
        )
    all_features = blocks.columns("combined")
    duplicates = [name for name, count in Counter(all_features).items() if count > 1]
    forbidden = sorted(set(all_features) & FORBIDDEN_PREDICTORS)
    if duplicates or forbidden or "lfm_entropy" in all_features:
        raise ModelingPilotError(
            f"Blocos inválidos; duplicadas={duplicates}; proibidas={forbidden}"
        )
    if "lfm_compression_ratio" not in blocks.traditional:
        raise ModelingPilotError("lfm_compression_ratio deveria estar autorizada.")


def _expand_embeddings(frame: pl.DataFrame) -> pl.DataFrame:
    dimensions = [
        pl.col("embedding").arr.get(index).cast(pl.Float64).alias(f"embedding_{index:03d}")
        for index in range(EXPECTED_EMBEDDINGS)
    ]
    return frame.with_columns(dimensions).drop("embedding")


def validate_modeling_matrix(
    matrix: pl.DataFrame,
    blocks: FeatureBlocks,
    *,
    expected_rows: int = EXPECTED_ROWS,
) -> dict[str, Any]:
    """Valida cardinalidade, cobertura, unicidade e ausência de holdout."""

    if matrix.height != expected_rows or matrix["composition_key"].n_unique() != expected_rows:
        raise ModelingPilotError("A matriz comum não tem exatamente uma linha por composição.")
    if matrix["track_id"].n_unique() != expected_rows:
        raise ModelingPilotError("O representante Spotify não é único por composição.")
    split_counts = {row["split"]: row["len"] for row in matrix.group_by("split").len().to_dicts()}
    if split_counts != {"development_train": expected_rows}:
        raise ModelingPilotError(
            f"A seleção tocaria dados fora de development_train: {split_counts}"
        )
    missing_columns = sorted(set(blocks.columns("combined")) - set(matrix.columns))
    if missing_columns:
        raise ModelingPilotError(f"Colunas autorizadas ausentes: {missing_columns}")
    if matrix["spotify_popularity"].null_count() != 0:
        raise ModelingPilotError("O alvo contém ausências.")
    unique_embeddings = matrix.select(blocks.embeddings).unique().height
    if unique_embeddings != expected_rows:
        raise ModelingPilotError("Há embeddings vetorialmente duplicados na matriz comum.")
    return {
        "rows": matrix.height,
        "unique_composition_keys": matrix["composition_key"].n_unique(),
        "unique_representative_track_ids": matrix["track_id"].n_unique(),
        "unique_embeddings": unique_embeddings,
        "holdout_rows": matrix.filter(pl.col("split") != "development_train").height,
        "duplicate_rows": matrix.height - matrix["composition_key"].n_unique(),
        "artist_groups": matrix["artist_group_id"].n_unique(),
        "non_english_rows": matrix.filter(pl.col("language_status") == "non_english").height,
        "representative_rule": "track_id representante persistido no artefato de embeddings v0.2",
    }


def build_modeling_matrix(blocks: FeatureBlocks) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Monta uma linha por composição usando somente representantes com embeddings."""

    embedding = pl.read_parquet(
        _project(EMBEDDING_PATH),
        columns=[
            "composition_key",
            "track_id",
            "embedding",
            "detected_language",
            "language_status",
        ],
    )
    if embedding.height != EXPECTED_ROWS:
        raise ModelingPilotError(f"Embeddings: {embedding.height}, esperado: {EXPECTED_ROWS}.")
    if embedding["composition_key"].n_unique() != EXPECTED_ROWS:
        raise ModelingPilotError("composition_key não é única nos embeddings.")
    if embedding["track_id"].n_unique() != EXPECTED_ROWS:
        raise ModelingPilotError("track_id representante não é único nos embeddings.")

    selected = [
        "track_id",
        "artist_group_id",
        "composition_group_id",
        "split_group_id",
        "split",
        "spotify_popularity",
        *blocks.baseline,
        *blocks.traditional,
    ]
    representative_ids = embedding["track_id"].to_list()
    base = (
        pl.scan_parquet(_project(BASE_PATH))
        .filter(pl.col("track_id").is_in(representative_ids))
        .select(selected)
        .collect()
    )
    if base.height != EXPECTED_ROWS or base["track_id"].n_unique() != EXPECTED_ROWS:
        raise ModelingPilotError(
            "A correspondência entre representantes e Base v0.1.1 não é integral e 1:1."
        )
    matrix = embedding.join(base, on="track_id", how="inner", validate="1:1")
    matrix = _expand_embeddings(matrix).sort("composition_key")
    return matrix, validate_modeling_matrix(matrix, blocks)


def _rank_bins(values: np.ndarray, bins: int = 5) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    result = np.empty(values.size, dtype=np.int64)
    result[order] = np.minimum(np.arange(values.size) * bins // values.size, bins - 1)
    return result


def make_grouped_folds(
    target: np.ndarray,
    groups: np.ndarray,
    *,
    n_splits: int,
    seed: int,
) -> np.ndarray:
    """Cria folds estratificados por postos do alvo e inteiramente agrupados."""

    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    fold = np.full(target.size, -1, dtype=np.int64)
    strata = _rank_bins(np.asarray(target, dtype=float))
    for fold_index, (_, validation) in enumerate(
        splitter.split(np.zeros((target.size, 1)), strata, groups)
    ):
        fold[validation] = fold_index
    if np.any(fold < 0):
        raise ModelingPilotError("Nem todas as observações receberam fold.")
    assert_no_group_leakage(fold, groups)
    return fold


def assert_no_group_leakage(folds: np.ndarray, groups: np.ndarray) -> None:
    """Garante que nenhum grupo cruza treino e validação em cada fold."""

    for fold in np.unique(folds):
        train_groups = set(groups[folds != fold])
        validation_groups = set(groups[folds == fold])
        overlap = train_groups & validation_groups
        if overlap:
            raise ModelingPilotError(
                f"Leakage de grupos no fold {int(fold)}: {len(overlap)} grupos."
            )


def fold_assignment_hash(matrix: pl.DataFrame, folds: np.ndarray) -> str:
    """Hash estável das atribuições individuais, sem publicá-las."""

    rows = zip(matrix["composition_key"].to_list(), folds, strict=True)
    payload = "\n".join(f"{key}\t{int(fold)}" for key, fold in rows).encode("utf-8")
    return _sha256_bytes(payload)


def _numeric_pipeline(*, scale: bool) -> Pipeline:
    steps: list[tuple[str, Any]] = [
        (
            "imputer",
            SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
        )
    ]
    if scale:
        steps.append(("scaler", StandardScaler()))
    return Pipeline(steps)


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


def build_estimator_pipeline(
    columns: list[str],
    embedding_columns: tuple[str, ...],
    *,
    algorithm: Literal["elastic_net", "hist_gradient_boosting"],
    pca_embeddings: bool,
    seed: int,
    memory: str | None = None,
) -> Pipeline:
    """Pipeline cujos ajustes ocorrem exclusivamente nos dados entregues a fit()."""

    categorical = [name for name in CATEGORICAL_FEATURES if name in columns]
    embeddings = [name for name in embedding_columns if name in columns]
    numeric = [name for name in columns if name not in categorical and name not in embeddings]
    scale = algorithm == "elastic_net"
    transformers: list[tuple[str, Any, list[str]]] = []
    if numeric:
        transformers.append(("numeric", _numeric_pipeline(scale=scale), numeric))
    if categorical:
        transformers.append(("categorical", _categorical_pipeline(), categorical))
    if embeddings:
        if pca_embeddings:
            embedding_steps: list[tuple[str, Any]] = [
                (
                    "imputer",
                    SimpleImputer(strategy="median", add_indicator=False, keep_empty_features=True),
                ),
                ("variance", VarianceThreshold()),
                ("pca", PCA(n_components=0.90, svd_solver="full")),
            ]
            if scale:
                embedding_steps.append(("post_pca_scaler", StandardScaler()))
            embedding_transformer: Any = Pipeline(embedding_steps)
        else:
            embedding_transformer = _numeric_pipeline(scale=scale)
        transformers.append(("embedding", embedding_transformer, embeddings))
    preprocess = ColumnTransformer(transformers, sparse_threshold=0.0)
    if algorithm == "elastic_net":
        model: Any = ElasticNet(max_iter=20_000, tol=1e-3, random_state=seed)
    elif algorithm == "hist_gradient_boosting":
        model = HistGradientBoostingRegressor(
            max_iter=100,
            min_samples_leaf=20,
            l2_regularization=1.0,
            early_stopping=False,
            random_state=seed,
        )
    else:
        raise ValueError(algorithm)
    return Pipeline(
        [
            ("preprocess", preprocess),
            ("variance", VarianceThreshold()),
            ("model", model),
        ],
        memory=memory,
    )


def regression_metrics(observed: np.ndarray, predicted: np.ndarray) -> dict[str, Any]:
    """Métricas do protocolo; Spearman constante é registrada como ausente."""

    observed = np.asarray(observed, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    rho = (
        None
        if np.ptp(observed) == 0 or np.ptp(predicted) == 0
        else float(spearmanr(observed, predicted).statistic)
    )
    return {
        "mae": float(mean_absolute_error(observed, predicted)),
        "rmse": float(np.sqrt(np.mean(np.square(observed - predicted)))),
        "r2": float(r2_score(observed, predicted)),
        "spearman": rho,
    }


def _parameter_grid(algorithm: str) -> Any:
    if algorithm == "elastic_net":
        return ELASTIC_NET_GRID
    if algorithm == "hist_gradient_boosting":
        return HIST_GRADIENT_BOOSTING_GRID
    raise ValueError(algorithm)


def _inner_splits(
    target: np.ndarray, groups: np.ndarray, *, seed: int
) -> list[tuple[np.ndarray, np.ndarray]]:
    folds = make_grouped_folds(target, groups, n_splits=INNER_FOLDS, seed=seed)
    return [
        (np.flatnonzero(folds != fold), np.flatnonzero(folds == fold))
        for fold in range(INNER_FOLDS)
    ]


def _take_rows(frame: pl.DataFrame, indices: np.ndarray) -> pl.DataFrame:
    return frame[indices.tolist()]


def run_nested_model(
    matrix: pl.DataFrame,
    folds: np.ndarray,
    groups: np.ndarray,
    target: np.ndarray,
    blocks: FeatureBlocks,
    *,
    block: str,
    algorithm: Literal["elastic_net", "hist_gradient_boosting"],
    pca_embeddings: bool,
    progress: Any = None,
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    """Executa validação externa 5-fold e tuning interno agrupado 3-fold."""

    columns = blocks.columns(block)
    predictors = matrix.select(columns)
    oof = np.full(matrix.height, np.nan, dtype=float)
    rows: list[dict[str, Any]] = []
    variant = "pca90" if pca_embeddings else "raw"
    cache_root = _project(PRIVATE_DIRECTORY) / "pipeline_cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    for fold in range(OUTER_FOLDS):
        train_index = np.flatnonzero(folds != fold)
        validation_index = np.flatnonzero(folds == fold)
        train_groups = groups[train_index]
        validation_groups = groups[validation_index]
        if set(train_groups) & set(validation_groups):
            raise ModelingPilotError(f"Artistas compartilhados no fold externo {fold}.")
        inner = _inner_splits(target[train_index], train_groups, seed=SEED + 1000 + fold)
        cache = cache_root / f"{algorithm}_{block}_{variant}_fold_{fold}"
        pipeline = build_estimator_pipeline(
            columns,
            blocks.embeddings,
            algorithm=algorithm,
            pca_embeddings=pca_embeddings,
            seed=SEED + fold,
            memory=str(cache),
        )
        search = GridSearchCV(
            pipeline,
            _parameter_grid(algorithm),
            scoring="neg_mean_absolute_error",
            cv=inner,
            refit=True,
            n_jobs=1,
            error_score="raise",
        )
        started = time.perf_counter()
        train_x = _take_rows(predictors, train_index)
        validation_x = _take_rows(predictors, validation_index)
        search.fit(train_x, target[train_index])
        train_prediction = search.predict(train_x)
        validation_prediction = search.predict(validation_x)
        duration = time.perf_counter() - started
        oof[validation_index] = validation_prediction
        train_metrics = regression_metrics(target[train_index], train_prediction)
        validation_metrics = regression_metrics(target[validation_index], validation_prediction)
        transformed_features = int(search.best_estimator_[:-1].transform(train_x[:1]).shape[1])
        pca_components: int | None = None
        if pca_embeddings:
            embedding_pipeline = search.best_estimator_.named_steps[
                "preprocess"
            ].named_transformers_["embedding"]
            pca_components = int(embedding_pipeline.named_steps["pca"].n_components_)
        rows.append(
            {
                "algorithm": algorithm,
                "block": block,
                "variant": variant,
                "scope": "fold",
                "fold": fold,
                "n": validation_index.size,
                "groups": len(set(validation_groups)),
                **validation_metrics,
                "train_mae": train_metrics["mae"],
                "validation_minus_train_mae": validation_metrics["mae"] - train_metrics["mae"],
                "duration_seconds": duration,
                "selected_params": _json_text(search.best_params_),
                "transformed_features": transformed_features,
                "pca_components": pca_components,
            }
        )
        if progress is not None:
            progress(algorithm, block, variant, fold + 1, OUTER_FOLDS)
    if np.isnan(oof).any():
        raise ModelingPilotError(f"Predições OOF incompletas: {algorithm}/{block}/{variant}.")
    overall = regression_metrics(target, oof)
    fold_rows = list(rows)
    rows.append(
        {
            "algorithm": algorithm,
            "block": block,
            "variant": variant,
            "scope": "overall_oof",
            "fold": None,
            "n": matrix.height,
            "groups": len(set(groups)),
            **overall,
            "train_mae": float(np.mean([row["train_mae"] for row in fold_rows])),
            "validation_minus_train_mae": float(
                np.mean([row["validation_minus_train_mae"] for row in fold_rows])
            ),
            "duration_seconds": float(np.sum([row["duration_seconds"] for row in fold_rows])),
            "selected_params": _json_text(
                [json.loads(row["selected_params"]) for row in fold_rows]
            ),
            "transformed_features": int(
                round(np.mean([row["transformed_features"] for row in fold_rows]))
            ),
            "pca_components": (
                int(round(np.mean([row["pca_components"] for row in fold_rows])))
                if pca_embeddings
                else None
            ),
        }
    )
    return oof, rows


def run_dummy(
    target: np.ndarray, folds: np.ndarray, groups: np.ndarray
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    oof = np.full(target.size, np.nan, dtype=float)
    rows: list[dict[str, Any]] = []
    for fold in range(OUTER_FOLDS):
        train = np.flatnonzero(folds != fold)
        validation = np.flatnonzero(folds == fold)
        started = time.perf_counter()
        model = DummyRegressor(strategy="mean").fit(np.zeros((train.size, 1)), target[train])
        train_prediction = model.predict(np.zeros((train.size, 1)))
        validation_prediction = model.predict(np.zeros((validation.size, 1)))
        duration = time.perf_counter() - started
        oof[validation] = validation_prediction
        train_metrics = regression_metrics(target[train], train_prediction)
        validation_metrics = regression_metrics(target[validation], validation_prediction)
        rows.append(
            {
                "algorithm": "dummy_mean",
                "block": "reference",
                "variant": "raw",
                "scope": "fold",
                "fold": fold,
                "n": validation.size,
                "groups": len(set(groups[validation])),
                **validation_metrics,
                "train_mae": train_metrics["mae"],
                "validation_minus_train_mae": validation_metrics["mae"] - train_metrics["mae"],
                "duration_seconds": duration,
                "selected_params": '{"strategy": "mean"}',
                "transformed_features": 0,
                "pca_components": None,
            }
        )
    overall = regression_metrics(target, oof)
    rows.append(
        {
            "algorithm": "dummy_mean",
            "block": "reference",
            "variant": "raw",
            "scope": "overall_oof",
            "fold": None,
            "n": target.size,
            "groups": len(set(groups)),
            **overall,
            "train_mae": float(np.mean([row["train_mae"] for row in rows])),
            "validation_minus_train_mae": float(
                np.mean([row["validation_minus_train_mae"] for row in rows])
            ),
            "duration_seconds": float(np.sum([row["duration_seconds"] for row in rows])),
            "selected_params": '{"strategy": "mean"}',
            "transformed_features": 0,
            "pca_components": None,
        }
    )
    return oof, rows


COMPARISONS = (
    ("baseline", "traditional"),
    ("baseline", "deep"),
    ("baseline", "combined"),
    ("traditional", "deep"),
    ("traditional", "combined"),
    ("deep", "combined"),
)


def grouped_paired_bootstrap(
    observed: np.ndarray,
    reference: np.ndarray,
    candidate: np.ndarray,
    groups: np.ndarray,
    *,
    repetitions: int = BOOTSTRAP_REPETITIONS,
    seed: int = SEED,
) -> dict[str, Any]:
    """Bootstrap pareado por artista; diferenças negativas indicam menor erro candidato."""

    unique_groups, inverse = np.unique(groups, return_inverse=True)
    n_groups = unique_groups.size
    counts = np.bincount(inverse).astype(float)
    ref_abs = np.bincount(inverse, weights=np.abs(observed - reference))
    cand_abs = np.bincount(inverse, weights=np.abs(observed - candidate))
    ref_sq = np.bincount(inverse, weights=np.square(observed - reference))
    cand_sq = np.bincount(inverse, weights=np.square(observed - candidate))
    rng = np.random.default_rng(seed)
    weights = rng.multinomial(n_groups, np.full(n_groups, 1.0 / n_groups), size=repetitions)
    sampled_n = weights @ counts
    mae_diff = (weights @ cand_abs) / sampled_n - (weights @ ref_abs) / sampled_n
    rmse_diff = np.sqrt((weights @ cand_sq) / sampled_n) - np.sqrt((weights @ ref_sq) / sampled_n)
    reference_metrics = regression_metrics(observed, reference)
    candidate_metrics = regression_metrics(observed, candidate)
    return {
        "repetitions": repetitions,
        "groups": n_groups,
        "mae_difference": candidate_metrics["mae"] - reference_metrics["mae"],
        "mae_percent_difference": 100
        * (candidate_metrics["mae"] - reference_metrics["mae"])
        / reference_metrics["mae"],
        "mae_ci95_low": float(np.quantile(mae_diff, 0.025)),
        "mae_ci95_high": float(np.quantile(mae_diff, 0.975)),
        "rmse_difference": candidate_metrics["rmse"] - reference_metrics["rmse"],
        "rmse_ci95_low": float(np.quantile(rmse_diff, 0.025)),
        "rmse_ci95_high": float(np.quantile(rmse_diff, 0.975)),
        "r2_difference": candidate_metrics["r2"] - reference_metrics["r2"],
        "direction": (
            "melhora do candidato"
            if candidate_metrics["mae"] < reference_metrics["mae"]
            else "piora do candidato"
        ),
    }


def _period_label(year: int) -> str:
    if year < 1980:
        return "antes de 1980"
    if year < 1990:
        return "1980–1989"
    if year < 2000:
        return "1990–1999"
    if year < 2010:
        return "2000–2009"
    if year < 2020:
        return "2010–2019"
    return "2020 ou posterior"


def aggregate_diagnostics(
    matrix: pl.DataFrame,
    target: np.ndarray,
    predictions: dict[str, np.ndarray],
) -> dict[str, Any]:
    """Diagnósticos agregados; células pequenas são suprimidas."""

    result: dict[str, Any] = {"minimum_cell_size": MIN_DIAGNOSTIC_CELL}
    years = matrix["year"].to_numpy()
    periods = np.array([_period_label(int(value)) for value in years], dtype=object)
    genres = matrix["genre"].cast(pl.String).to_numpy()
    order = np.argsort(target, kind="mergesort")
    quintiles = np.empty(target.size, dtype=int)
    quintiles[order] = np.minimum(np.arange(target.size) * 5 // target.size, 4) + 1

    for dimension, labels in (
        ("period", periods),
        ("genre", genres),
        ("observed_quintile", quintiles),
    ):
        rows: list[dict[str, Any]] = []
        for label in sorted(set(labels), key=str):
            mask = labels == label
            n = int(np.sum(mask))
            if n < MIN_DIAGNOSTIC_CELL:
                continue
            for model_key, prediction in predictions.items():
                rows.append(
                    {
                        dimension: str(label),
                        "model": model_key,
                        "n": n,
                        **regression_metrics(target[mask], prediction[mask]),
                    }
                )
        result[dimension] = rows
    english_mask = matrix["language_status"].to_numpy() == "english"
    result["language_sensitivity"] = {
        "english_rows": int(np.sum(english_mask)),
        "non_english_rows_removed": int(np.sum(~english_mask)),
        "method": "recalculo das métricas OOF após excluir casos não ingleses; modelos e folds não foram reescolhidos",
        "models": [
            {
                "model": key,
                **regression_metrics(target[english_mask], prediction[english_mask]),
                "full_sample_mae": regression_metrics(target, prediction)["mae"],
                "mae_change_after_removal": regression_metrics(
                    target[english_mask], prediction[english_mask]
                )["mae"]
                - regression_metrics(target, prediction)["mae"],
            }
            for key, prediction in predictions.items()
        ],
    }
    return result


def _fold_audit(matrix: pl.DataFrame, folds: np.ndarray) -> list[dict[str, Any]]:
    target = matrix["spotify_popularity"].to_numpy()
    years = matrix["year"].to_numpy()
    genres = matrix["genre"].cast(pl.String).to_numpy()
    artists = matrix["artist_group_id"].to_numpy()
    result = []
    for fold in range(OUTER_FOLDS):
        mask = folds == fold
        genre_counts = Counter(genres[mask])
        result.append(
            {
                "fold": fold,
                "observations": int(np.sum(mask)),
                "artist_groups": len(set(artists[mask])),
                "target_mean": float(np.mean(target[mask])),
                "target_median": float(np.median(target[mask])),
                "target_std": float(np.std(target[mask])),
                "year_minimum": int(np.min(years[mask])),
                "year_median": float(np.median(years[mask])),
                "year_maximum": int(np.max(years[mask])),
                "genre_distribution": dict(sorted(genre_counts.items())),
            }
        )
    return result


def _write_metrics(rows: list[dict[str, Any]]) -> None:
    path = _project(METRICS_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "algorithm",
        "block",
        "variant",
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
        "duration_seconds",
        "selected_params",
        "transformed_features",
        "pca_components",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, float) and not np.isfinite(value):
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    top = "| " + " | ".join(headers) + " |"
    separator = "|" + "|".join("---" for _ in headers) + "|"
    body = ["| " + " | ".join(_fmt(value) for value in row) + " |" for row in rows]
    return "\n".join([top, separator, *body])


def _overall_rows(metrics: list[dict[str, Any]], *, variant: str = "raw") -> list[dict[str, Any]]:
    return [row for row in metrics if row["scope"] == "overall_oof" and row["variant"] == variant]


def _write_feature_blocks(blocks: FeatureBlocks) -> None:
    lines = [
        "# Blocos de variáveis — Modelagem piloto v0.3",
        "",
        "As listas abaixo foram reconciliadas com `feature_manifest_v0_1_1_revision.csv` antes do treinamento.",
        "As contagens são anteriores a imputação, indicadores de ausência, one-hot encoding e remoção de variância zero.",
        "",
        "## Contagens",
        "",
        _table(
            ["Bloco", "Baseline", "LFM2b", "MiniLM", "Total"],
            [
                ["Baseline", 23, 0, 0, 23],
                ["Tradicional", 23, 196, 0, 219],
                ["Profundo", 23, 0, 384, 407],
                ["Combinado", 23, 196, 384, 603],
            ],
        ),
        "",
        "## Baseline — 23 variáveis",
        "",
        ", ".join(f"`{name}`" for name in blocks.baseline),
        "",
        "## Descritores tradicionais autorizados — 196 variáveis",
        "",
    ]
    for family, names in blocks.traditional_families.items():
        lines.extend(
            [
                f"### {family} — {len(names)}",
                "",
                ", ".join(f"`{name}`" for name in names),
                "",
            ]
        )
    lines.extend(
        [
            "## Embeddings MiniLM — 384 variáveis",
            "",
            "Dimensões `embedding_000` a `embedding_383`, derivadas exclusivamente das letras aceitas na v0.2.",
            "",
            "## Exclusões e papéis auxiliares",
            "",
            "`spotify_popularity` é somente o alvo. `artist_group_id` é somente a chave de agrupamento. "
            "`composition_key`, `track_id`, `composition_group_id` e `split_group_id` são somente auditoria. "
            "`detected_language` e `language_status` são somente sensibilidade. `lfm_entropy`, "
            "`genius_lyrics_views`, `lfm_playcount`, textos, hashes, IDs LRCLIB e campos de matching/coleta não entram como preditores.",
            "",
        ]
    )
    _project(BLOCKS_REPORT_PATH).write_text("\n".join(lines), encoding="utf-8")


def _write_pca_report(metrics: list[dict[str, Any]]) -> None:
    rows = [
        row
        for row in metrics
        if row["scope"] == "overall_oof"
        and row["block"] in {"deep", "combined"}
        and row["algorithm"] != "dummy_mean"
    ]
    comparison = []
    for algorithm in ("elastic_net", "hist_gradient_boosting"):
        for block in ("deep", "combined"):
            raw = next(
                row
                for row in rows
                if row["algorithm"] == algorithm
                and row["block"] == block
                and row["variant"] == "raw"
            )
            pca = next(
                row
                for row in rows
                if row["algorithm"] == algorithm
                and row["block"] == block
                and row["variant"] == "pca90"
            )
            comparison.append(
                [
                    algorithm,
                    block,
                    raw["mae"],
                    pca["mae"],
                    pca["mae"] - raw["mae"],
                    raw["rmse"],
                    pca["rmse"],
                    pca["pca_components"],
                ]
            )
    text = "\n".join(
        [
            "# Sensibilidade PCA 90% — Modelagem piloto v0.3",
            "",
            "A análise principal usa as 384 dimensões. A PCA foi ajustada separadamente no treino de cada fold, somente sobre o bloco de embeddings, sem alvo e sem variáveis categóricas. O percentual de 90% foi fixado antes dos resultados externos.",
            "",
            _table(
                [
                    "Algoritmo",
                    "Bloco",
                    "MAE raw",
                    "MAE PCA",
                    "Δ MAE PCA−raw",
                    "RMSE raw",
                    "RMSE PCA",
                    "Componentes PCA médios",
                ],
                comparison,
            ),
            "",
            "Componentes não são interpretados causalmente. A contagem exibida é a média arredondada dos cinco ajustes externos; a contagem por fold está no CSV agregado de métricas.",
            "",
        ]
    )
    _project(PCA_REPORT_PATH).write_text(text, encoding="utf-8")


def _comparison_rows(comparisons: list[dict[str, Any]]) -> list[list[Any]]:
    return [
        [
            row["algorithm"],
            f"{row['candidate']} vs {row['reference']}",
            row["mae_difference"],
            row["mae_percent_difference"],
            f"[{row['mae_ci95_low']:.3f}, {row['mae_ci95_high']:.3f}]",
            row["rmse_difference"],
            f"[{row['rmse_ci95_low']:.3f}, {row['rmse_ci95_high']:.3f}]",
            row["r2_difference"],
        ]
        for row in comparisons
    ]


def _modeling_recommendation(metrics: list[dict[str, Any]]) -> dict[str, str]:
    raw = [
        row
        for row in metrics
        if row["scope"] == "overall_oof"
        and row["variant"] == "raw"
        and row["algorithm"] != "dummy_mean"
    ]
    best = min(raw, key=lambda row: row["mae"])
    if best["block"] == "baseline":
        return {
            "choice": "revisar os blocos de variáveis",
            "basis": (
                "O baseline obteve o menor MAE OOF nos dois algoritmos; os blocos com letras "
                "não produziram ganho incremental nesta amostra. Antes de ampliar a coleta, "
                "convém revisar representação, regularização e redundância dos blocos de letras."
            ),
        }
    return {
        "choice": "ajustar o modelo",
        "basis": (
            "Ao menos um bloco com letras melhorou o MAE interno; o próximo passo prudente é "
            "avaliar a estabilidade do ajuste antes de ampliar a coleta."
        ),
    }


def _write_main_report(summary: dict[str, Any]) -> None:
    metrics = summary["metrics"]
    overall = _overall_rows(metrics)
    dummy = next(row for row in overall if row["algorithm"] == "dummy_mean")
    fold_audit = summary["folds"]["audit"]
    model_tables: list[str] = []
    for algorithm in ("elastic_net", "hist_gradient_boosting"):
        rows = [
            row for row in overall if row["algorithm"] == algorithm and row["block"] != "reference"
        ]
        rows.sort(
            key=lambda row: ("baseline", "traditional", "deep", "combined").index(row["block"])
        )
        model_tables.extend(
            [
                f"### {algorithm}",
                "",
                _table(
                    [
                        "Bloco",
                        "MAE",
                        "RMSE",
                        "R²",
                        "Spearman",
                        "MAE treino",
                        "Gap val−treino",
                        "Tempo (s)",
                    ],
                    [
                        [
                            row["block"],
                            row["mae"],
                            row["rmse"],
                            row["r2"],
                            row["spearman"],
                            row["train_mae"],
                            row["validation_minus_train_mae"],
                            row["duration_seconds"],
                        ]
                        for row in rows
                    ],
                ),
                "",
            ]
        )
    language_rows = summary["diagnostics"]["language_sensitivity"]["models"]
    best_raw = min(
        [row for row in overall if row["algorithm"] != "dummy_mean"],
        key=lambda row: row["mae"],
    )
    best_key = f"{best_raw['algorithm']}__{best_raw['block']}__raw"
    diagnostic_tables: list[str] = []
    for dimension, label in (
        ("period", "Período"),
        ("genre", "Gênero (n ≥ 30)"),
        ("observed_quintile", "Quintil observado"),
    ):
        rows = [row for row in summary["diagnostics"][dimension] if row["model"] == best_key]
        diagnostic_tables.extend(
            [
                f"### {label}",
                "",
                _table(
                    [label, "n", "MAE", "RMSE", "R²", "Spearman"],
                    [
                        [
                            row[dimension],
                            row["n"],
                            row["mae"],
                            row["rmse"],
                            row["r2"],
                            row["spearman"],
                        ]
                        for row in rows
                    ],
                ),
                "",
            ]
        )
    report = [
        "# Modelagem piloto da popularidade musical — v0.3",
        "",
        "## Escopo e interpretação",
        "",
        "Validação interna preditiva de `spotify_popularity` (0–100), sem interpretação causal, sem acesso ao holdout oficial e sem treinamento de modelo final. A unidade é uma composição aceita na v0.2, representada por uma única observação Spotify. Isso evita múltiplas versões na matriz, mas limita a generalização para outras gravações da mesma composição.",
        "",
        "## Universo comum",
        "",
        f"- Linhas/composições/embeddings: {summary['matrix_audit']['rows']} / {summary['matrix_audit']['unique_composition_keys']} / {summary['matrix_audit']['unique_embeddings']}.",
        f"- Artistas agrupadores: {summary['matrix_audit']['artist_groups']}.",
        f"- Holdout acessado: não; linhas fora de `development_train`: {summary['matrix_audit']['holdout_rows']}.",
        f"- Casos não ingleses: {summary['matrix_audit']['non_english_rows']}.",
        "",
        "## Validação e pré-processamento",
        "",
        f"Cinco folds externos agrupados por `artist_group_id`, com três folds internos agrupados para tuning; seed {SEED}. Os folds são idênticos entre blocos e algoritmos. Imputação, indicadores de ausência, one-hot encoding, padronização linear, `VarianceThreshold` e PCA foram ajustados exclusivamente no treino pertinente. Hash das atribuições: `{summary['folds']['assignment_sha256']}`.",
        "",
        "Grade pré-definida: Elastic Net com `alpha` em [0.03, 0.3] e `l1_ratio` em [0.1, 0.8]; HistGradientBoosting com pares (`learning_rate`, `max_leaf_nodes`) (0.05, 15) e (0.1, 31), `max_iter=100`, `min_samples_leaf=20` e `l2_regularization=1`. Seleção interna por MAE.",
        "",
        "## Auditoria dos folds",
        "",
        _table(
            [
                "Fold",
                "n",
                "Artistas",
                "Alvo médio",
                "Alvo mediano",
                "Ano mín.",
                "Ano med.",
                "Ano máx.",
            ],
            [
                [
                    row["fold"],
                    row["observations"],
                    row["artist_groups"],
                    row["target_mean"],
                    row["target_median"],
                    row["year_minimum"],
                    row["year_median"],
                    row["year_maximum"],
                ]
                for row in fold_audit
            ],
        ),
        "",
        "## Referência ingênua",
        "",
        _table(
            ["Modelo", "MAE", "RMSE", "R²", "Spearman"],
            [
                [
                    "DummyRegressor (média do treino)",
                    dummy["mae"],
                    dummy["rmse"],
                    dummy["r2"],
                    dummy["spearman"],
                ]
            ],
        ),
        "",
        "## Modelos principais — embeddings raw",
        "",
        *model_tables,
        "## Comparações pareadas",
        "",
        "Diferenças são candidato menos referência; valores negativos de MAE/RMSE indicam melhora. IC95% por 2.000 reamostragens pareadas e agrupadas por artista.",
        "",
        _table(
            [
                "Algoritmo",
                "Comparação",
                "Δ MAE",
                "Δ MAE %",
                "IC95% Δ MAE",
                "Δ RMSE",
                "IC95% Δ RMSE",
                "Δ R²",
            ],
            _comparison_rows(summary["bootstrap_comparisons"]),
        ),
        "",
        "## Diagnósticos agregados da melhor configuração interna",
        "",
        f"A configuração de menor MAE OOF foi `{best_key}`. As tabelas abaixo são diagnósticos posteriores, não critérios para reescolher o modelo. Células com menos de {MIN_DIAGNOSTIC_CELL} observações foram suprimidas.",
        "",
        *diagnostic_tables,
        "## Sensibilidade de idioma",
        "",
        "As métricas foram recalculadas nas 1.421 observações classificadas como inglesas, retirando 20 casos não ingleses sem reajustar modelos, folds ou escolha de configuração.",
        "",
        _table(
            [
                "Modelo",
                "MAE amostra completa",
                "MAE só inglês",
                "Δ após remoção",
                "RMSE",
                "R²",
                "Spearman",
            ],
            [
                [
                    row["model"],
                    row["full_sample_mae"],
                    row["mae"],
                    row["mae_change_after_removal"],
                    row["rmse"],
                    row["r2"],
                    row["spearman"],
                ]
                for row in language_rows
            ],
        ),
        "",
        "## Diagnóstico de overfitting",
        "",
        "O campo `Gap val−treino` compara MAE de validação externa com MAE de treino após o tuning interno. Gaps positivos e grandes sugerem overfitting; não constituem teste formal. Parâmetros por fold e métricas por fold estão no CSV agregado.",
        "",
        "## Limitações",
        "",
        "Resultados restritos às 1.441 composições com letras aceitas, sujeitos a viés de seleção da disponibilidade de letras e à escolha de uma versão Spotify representante. O bootstrap reflete incerteza interna por artista, não incerteza de um holdout independente. A popularidade é a observada no snapshot e não mede causalidade nem sucesso futuro.",
        "",
        "## Recomendação",
        "",
        f"**{summary['recommendation']['choice']}**. {summary['recommendation']['basis']}",
        "",
        "## Privacidade e preservação",
        "",
        "Matriz, folds e predições individuais permanecem em área ignorada pelo Git. Relatórios e figuras contêm somente agregados. A Base v0.1.1 e o split congelado permaneceram byte a byte idênticos.",
        "",
        "## Verificação final",
        "",
        "Pendente até a execução pós-modelagem da suíte completa, testes específicos, lint, formatação, hashes e auditoria de privacidade.",
        "",
    ]
    _project(REPORT_PATH).write_text("\n".join(report), encoding="utf-8")


def _create_figures(
    matrix: pl.DataFrame,
    target: np.ndarray,
    predictions: dict[str, np.ndarray],
    metrics: list[dict[str, Any]],
) -> list[str]:
    directory = _project(FIGURE_DIRECTORY)
    directory.mkdir(parents=True, exist_ok=True)
    created: list[str] = []

    def save(name: str) -> None:
        path = directory / name
        plt.tight_layout()
        plt.savefig(path, dpi=160, bbox_inches="tight")
        plt.close()
        created.append(name)

    plt.figure(figsize=(7, 4.5))
    plt.hist(target, bins=np.arange(0, 105, 5), color="#4472C4", edgecolor="white")
    plt.xlabel("Spotify popularity")
    plt.ylabel("Composições")
    plt.title("Distribuição agregada do alvo — development_train")
    save("target_distribution.png")

    overall = [
        row
        for row in metrics
        if row["scope"] == "overall_oof"
        and row["variant"] == "raw"
        and row["algorithm"] != "dummy_mean"
    ]
    best = min(overall, key=lambda row: row["mae"])
    best_key = f"{best['algorithm']}__{best['block']}__raw"
    best_prediction = predictions[best_key]

    plt.figure(figsize=(6, 5))
    plt.hexbin(target, best_prediction, gridsize=16, mincnt=3, cmap="Blues")
    plt.plot([0, 100], [0, 100], linestyle="--", color="black", linewidth=1)
    plt.xlabel("Observado")
    plt.ylabel("Predito OOF")
    plt.title(f"Observado vs predito — {best['algorithm']} / {best['block']}")
    plt.colorbar(label="Contagem por célula (mín. 3)")
    save("observed_vs_predicted_hexbin.png")

    residuals = target - best_prediction
    plt.figure(figsize=(6, 5))
    plt.hexbin(best_prediction, residuals, gridsize=16, mincnt=3, cmap="Purples")
    plt.axhline(0, linestyle="--", color="black", linewidth=1)
    plt.xlabel("Predito OOF")
    plt.ylabel("Resíduo (observado − predito)")
    plt.title(f"Resíduos vs predito — {best['algorithm']} / {best['block']}")
    plt.colorbar(label="Contagem por célula (mín. 3)")
    save("residuals_vs_predicted_hexbin.png")

    plt.figure(figsize=(7, 4.5))
    plt.hist(residuals, bins=25, color="#8064A2", edgecolor="white")
    plt.xlabel("Resíduo OOF")
    plt.ylabel("Composições")
    plt.title(f"Distribuição agregada dos resíduos — {best['algorithm']} / {best['block']}")
    save("residual_distribution.png")

    raw_fold = [
        row
        for row in metrics
        if row["scope"] == "fold" and row["variant"] == "raw" and row["algorithm"] != "dummy_mean"
    ]
    plt.figure(figsize=(9, 5))
    for algorithm in ("elastic_net", "hist_gradient_boosting"):
        for block in ("baseline", "traditional", "deep", "combined"):
            chosen = [
                row for row in raw_fold if row["algorithm"] == algorithm and row["block"] == block
            ]
            plt.plot(
                [row["fold"] for row in chosen],
                [row["mae"] for row in chosen],
                marker="o",
                label=f"{algorithm} / {block}",
            )
    plt.xlabel("Fold externo")
    plt.ylabel("MAE")
    plt.title("MAE agregado por fold")
    plt.xticks(range(OUTER_FOLDS))
    plt.legend(fontsize=7, ncol=2)
    save("mae_by_fold.png")

    labels = [f"{row['algorithm']}\n{row['block']}" for row in overall]
    values = [row["mae"] for row in overall]
    plt.figure(figsize=(10, 5))
    plt.bar(np.arange(len(labels)), values, color="#70AD47")
    plt.xticks(np.arange(len(labels)), labels, rotation=35, ha="right", fontsize=8)
    plt.ylabel("MAE OOF")
    plt.title("Comparação agregada dos quatro blocos")
    save("model_comparison_mae.png")

    pca_rows = [
        row
        for row in metrics
        if row["scope"] == "overall_oof"
        and row["block"] in {"deep", "combined"}
        and row["algorithm"] != "dummy_mean"
    ]
    labels = [f"{row['algorithm']}\n{row['block']}\n{row['variant']}" for row in pca_rows]
    plt.figure(figsize=(10, 5))
    plt.bar(
        np.arange(len(labels)),
        [row["mae"] for row in pca_rows],
        color=["#5B9BD5" if row["variant"] == "raw" else "#ED7D31" for row in pca_rows],
    )
    plt.xticks(np.arange(len(labels)), labels, rotation=35, ha="right", fontsize=8)
    plt.ylabel("MAE OOF")
    plt.title("Sensibilidade: embeddings raw versus PCA 90%")
    save("raw_vs_pca_mae.png")
    return created


def _git_private_files() -> dict[str, list[str]]:
    prefixes = (
        "data/derived/private_modeling/",
        "data/derived/private_embeddings/",
        "data/raw/lyrics_private/",
        "data/interim/lyrics_private/",
    )
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
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
    """Impede texto, hashes/IDs de letras e caminhos privados nos resultados públicos."""

    forbidden_markers = (
        "lyrics_sha256",
        "syncedLyrics",
        "plainLyrics",
        "data/derived/private_modeling",
        "data/derived/private_embeddings",
        "data/raw/lyrics_private",
    )
    violations: list[str] = []
    for relative in paths:
        path = _project(relative)
        if path.suffix.lower() not in {".md", ".json", ".csv"}:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in forbidden_markers:
            if marker in text:
                violations.append(f"{relative}: marcador {marker}")
    if violations:
        raise ModelingPilotError(f"Violação de privacidade pública: {violations}")
    private_git = _git_private_files()
    if private_git["tracked"] or private_git["staged"]:
        raise ModelingPilotError(f"Arquivo privado tracked/staged: {private_git}")
    return {
        "public_files_scanned": len(paths),
        "forbidden_marker_occurrences": 0,
        "tracked_private_files": [],
        "staged_private_files": [],
    }


def _private_output_hashes() -> dict[str, str]:
    directory = _project(PRIVATE_DIRECTORY)
    return {name: sha256_file(directory / name) for name in (MATRIX_NAME, FOLDS_NAME, OOF_NAME)}


def _public_hashes(paths: list[str]) -> dict[str, str]:
    return {
        Path(path).name: sha256_file(_project(path)) for path in paths if _project(path).is_file()
    }


def _write_private_outputs(
    matrix: pl.DataFrame,
    folds: np.ndarray,
    predictions: dict[str, np.ndarray],
) -> None:
    directory = _project(PRIVATE_DIRECTORY)
    directory.mkdir(parents=True, exist_ok=True)
    matrix.write_parquet(directory / MATRIX_NAME, compression="zstd")
    matrix.select(
        "composition_key",
        "track_id",
        "artist_group_id",
        "composition_group_id",
        "split_group_id",
    ).with_columns(pl.Series("outer_fold", folds)).write_parquet(
        directory / FOLDS_NAME, compression="zstd"
    )
    oof = matrix.select(
        "composition_key",
        "track_id",
        "artist_group_id",
        "composition_group_id",
        "spotify_popularity",
        "language_status",
    ).with_columns(pl.Series("outer_fold", folds))
    oof = oof.with_columns(
        [pl.Series(f"prediction__{key}", value) for key, value in predictions.items()]
    )
    oof.write_parquet(directory / OOF_NAME, compression="zstd")


def run_modeling_pilot_v030(progress: Any = None) -> dict[str, Any]:
    """Executa integralmente a modelagem piloto v0.3 e gera apenas agregados públicos."""

    started = time.perf_counter()
    frozen_before = {
        Path(BASE_PATH).name: sha256_file(_project(BASE_PATH)),
        Path(SPLIT_PATH).name: sha256_file(_project(SPLIT_PATH)),
    }
    blocks = load_feature_blocks()
    matrix, matrix_audit = build_modeling_matrix(blocks)
    target = matrix["spotify_popularity"].to_numpy().astype(float)
    groups = matrix["artist_group_id"].to_numpy()
    folds = make_grouped_folds(target, groups, n_splits=OUTER_FOLDS, seed=SEED)
    assignment_sha = fold_assignment_hash(matrix, folds)
    fold_audit = _fold_audit(matrix, folds)

    predictions: dict[str, np.ndarray] = {}
    metric_rows: list[dict[str, Any]] = []
    dummy_prediction, dummy_rows = run_dummy(target, folds, groups)
    predictions["dummy_mean__reference__raw"] = dummy_prediction
    metric_rows.extend(dummy_rows)

    for algorithm in ("elastic_net", "hist_gradient_boosting"):
        for block in ("baseline", "traditional", "deep", "combined"):
            prediction, rows = run_nested_model(
                matrix,
                folds,
                groups,
                target,
                blocks,
                block=block,
                algorithm=algorithm,
                pca_embeddings=False,
                progress=progress,
            )
            predictions[f"{algorithm}__{block}__raw"] = prediction
            metric_rows.extend(rows)
    for algorithm in ("elastic_net", "hist_gradient_boosting"):
        for block in ("deep", "combined"):
            prediction, rows = run_nested_model(
                matrix,
                folds,
                groups,
                target,
                blocks,
                block=block,
                algorithm=algorithm,
                pca_embeddings=True,
                progress=progress,
            )
            predictions[f"{algorithm}__{block}__pca90"] = prediction
            metric_rows.extend(rows)

    comparisons: list[dict[str, Any]] = []
    for algorithm_index, algorithm in enumerate(("elastic_net", "hist_gradient_boosting")):
        for comparison_index, (reference, candidate) in enumerate(COMPARISONS):
            bootstrap = grouped_paired_bootstrap(
                target,
                predictions[f"{algorithm}__{reference}__raw"],
                predictions[f"{algorithm}__{candidate}__raw"],
                groups,
                seed=SEED + algorithm_index * 100 + comparison_index,
            )
            comparisons.append(
                {
                    "algorithm": algorithm,
                    "reference": reference,
                    "candidate": candidate,
                    **bootstrap,
                }
            )

    main_predictions = {
        key: value
        for key, value in predictions.items()
        if key.endswith("__raw") and not key.startswith("dummy_mean")
    }
    diagnostics = aggregate_diagnostics(matrix, target, main_predictions)
    _write_private_outputs(matrix, folds, predictions)
    _write_metrics(metric_rows)
    _write_feature_blocks(blocks)
    _write_pca_report(metric_rows)
    figures = _create_figures(matrix, target, predictions, metric_rows)

    frozen_after = {
        Path(BASE_PATH).name: sha256_file(_project(BASE_PATH)),
        Path(SPLIT_PATH).name: sha256_file(_project(SPLIT_PATH)),
    }
    if frozen_before != frozen_after:
        raise ModelingPilotError("Base v0.1.1 ou split congelado foram alterados.")

    block_counts = {
        "baseline": len(blocks.columns("baseline")),
        "traditional": len(blocks.columns("traditional")),
        "deep": len(blocks.columns("deep")),
        "combined": len(blocks.columns("combined")),
    }
    summary: dict[str, Any] = {
        "status": "modeling_complete_verification_pending",
        "protocol_version": PROTOCOL_VERSION,
        "timestamp": utc_now(),
        "git_checkpoint_commit": git_commit(),
        "git_checkpoint_tag": "lyrics-embeddings-v0.2",
        "seed": SEED,
        "target": "spotify_popularity",
        "grouping_key": "artist_group_id",
        "matrix_audit": matrix_audit,
        "feature_blocks": {
            "counts_before_transformations": block_counts,
            "baseline_features": list(blocks.baseline),
            "traditional_feature_count": len(blocks.traditional),
            "embedding_feature_range": "embedding_000..embedding_383",
            "forbidden_predictors_in_blocks": [],
        },
        "validation_design": {
            "outer_folds": OUTER_FOLDS,
            "inner_folds": INNER_FOLDS,
            "outer_grouped_by": "artist_group_id",
            "same_outer_folds_all_models": True,
            "selection_metric": "MAE",
            "holdout_accessed": False,
        },
        "algorithms": {
            "dummy": {"strategy": "mean"},
            "elastic_net": {"grid": ELASTIC_NET_GRID, "max_iter": 20_000, "tol": 0.001},
            "hist_gradient_boosting": {
                "grid": HIST_GRADIENT_BOOSTING_GRID,
                "max_iter": 100,
                "min_samples_leaf": 20,
                "l2_regularization": 1.0,
            },
        },
        "folds": {
            "assignment_sha256": assignment_sha,
            "audit": fold_audit,
            "artist_overlap_counts": [0] * OUTER_FOLDS,
            "composition_overlap_counts": [0] * OUTER_FOLDS,
        },
        "metrics": metric_rows,
        "bootstrap_comparisons": comparisons,
        "diagnostics": diagnostics,
        "recommendation": _modeling_recommendation(metric_rows),
        "pca": {
            "retained_variance": 0.90,
            "fit_inside_each_training_fold": True,
            "applied_only_to_embeddings": True,
        },
        "privacy": {
            "individual_outputs_public": False,
            "private_output_basenames": [MATRIX_NAME, FOLDS_NAME, OOF_NAME],
            "tracked_private_files": [],
            "staged_private_files": [],
        },
        "frozen_hashes_before": frozen_before,
        "frozen_hashes_after": frozen_after,
        "frozen_hashes_preserved": True,
        "private_output_hashes": _private_output_hashes(),
        "figures": figures,
        "duration_seconds": time.perf_counter() - started,
        "verification": {"status": "pending", "checks": []},
    }
    _write_main_report(summary)
    public_paths = [
        REPORT_PATH,
        METRICS_PATH,
        PCA_REPORT_PATH,
        BLOCKS_REPORT_PATH,
        *[f"{FIGURE_DIRECTORY}/{name}" for name in figures],
    ]
    summary["privacy"].update(audit_public_outputs(public_paths))
    summary["public_output_hashes"] = _public_hashes(public_paths)
    clean_summary = _clean_json(summary)
    write_json(SUMMARY_PATH, clean_summary)
    return clean_summary


def finalize_modeling_verification_v030(checks: list[dict[str, Any]]) -> dict[str, Any]:
    """Registra verificações pós-execução sem regenerar modelos ou predições."""

    summary = read_json(SUMMARY_PATH)
    if not isinstance(summary, dict):
        raise ModelingPilotError("Run summary v0.3 ausente.")
    frozen_after = {
        Path(BASE_PATH).name: sha256_file(_project(BASE_PATH)),
        Path(SPLIT_PATH).name: sha256_file(_project(SPLIT_PATH)),
    }
    private_git = _git_private_files()
    passed = all(int(check["exit_code"]) == 0 for check in checks)
    passed = passed and not private_git["tracked"] and not private_git["staged"]
    passed = passed and frozen_after == summary["frozen_hashes_before"]
    summary["frozen_hashes_after"] = frozen_after
    summary["frozen_hashes_preserved"] = frozen_after == summary["frozen_hashes_before"]
    summary["privacy"]["tracked_private_files"] = private_git["tracked"]
    summary["privacy"]["staged_private_files"] = private_git["staged"]
    summary["verification"] = {
        "status": "passed" if passed else "failed",
        "checks": checks,
    }
    summary["status"] = "complete" if passed else "verification_failed"
    summary["recommendation"] = _modeling_recommendation(summary["metrics"])
    summary = _clean_json(summary)
    _write_metrics(summary["metrics"])
    _write_main_report(summary)

    report_path = _project(REPORT_PATH)
    report = report_path.read_text(encoding="utf-8")
    heading = "## Verificação final"
    prefix = report.partition(heading)[0]
    verification_rows = [
        [check["command"], check["exit_code"], check.get("result", "")] for check in checks
    ]
    verification = "\n".join(
        [
            heading,
            "",
            _table(["Comando/verificação", "Código", "Resultado"], verification_rows),
            "",
            f"Status: **{'aprovado' if passed else 'falhou'}**. Arquivos privados tracked/staged: {len(private_git['tracked'])}/{len(private_git['staged'])}. Hashes congelados preservados: {summary['frozen_hashes_preserved']}.",
            "",
        ]
    )
    report_path.write_text(prefix + verification, encoding="utf-8")
    public_paths = [
        REPORT_PATH,
        METRICS_PATH,
        PCA_REPORT_PATH,
        BLOCKS_REPORT_PATH,
        *[f"{FIGURE_DIRECTORY}/{name}" for name in summary["figures"]],
    ]
    summary["privacy"].update(audit_public_outputs(public_paths))
    summary["public_output_hashes"] = _public_hashes(public_paths)
    clean_summary = _clean_json(summary)
    write_json(SUMMARY_PATH, clean_summary)
    return clean_summary
