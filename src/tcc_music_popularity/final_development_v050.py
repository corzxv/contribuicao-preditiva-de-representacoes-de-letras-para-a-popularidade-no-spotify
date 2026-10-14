"""Final development v0.5: verified joins, nested grouped CV and frozen pipelines."""

from __future__ import annotations

import argparse
import csv
import importlib.metadata
import json
import sys
import time
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import polars as pl
from joblib import Parallel, delayed, parallel_config
from sklearn.dummy import DummyRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from .config import load_yaml, project_path
from .final_study_v040 import _atomic_write_frame, _git_private_files
from .io import git_commit, read_json, sha256_file, utc_now, write_json
from .modeling_pilot_v030 import (
    FeatureBlocks,
    _expand_embeddings,
    _period_label,
    assert_no_group_leakage,
    grouped_paired_bootstrap,
    load_feature_blocks,
    make_grouped_folds,
    regression_metrics,
)
from .modeling_recalibration_v031 import (
    ELASTIC_NET_ALPHAS,
    ELASTIC_NET_L1_RATIOS,
    RIDGE_ALPHAS,
    Representation,
    _components,
    _feature_groups,
    build_representation_transformer,
    coefficient_diagnostics,
)

CONFIG = "configs/final_development_v0_5.yaml"
ROOT = "data/derived/private_final_development_v0_5"
SEAL = f"{ROOT}/execution_seal.json"
MANIFEST = "reports/final_model_manifest_v0_5.json"
SUMMARY = "reports/run_summary_final_development_v0_5.json"
FORBIDDEN = {"spotify_popularity", "genius_lyrics_views", "lfm_playcount", "lfm_entropy"}


def private(name: str) -> Path:
    path = project_path(f"{ROOT}/{name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_report(name: str, text: str) -> None:
    project_path(f"reports/{name}").write_text(text, encoding="utf-8")


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def versions() -> dict[str, str]:
    return {
        name: importlib.metadata.version(name)
        for name in (
            "numpy",
            "polars",
            "pyarrow",
            "scikit-learn",
            "scipy",
            "joblib",
            "threadpoolctl",
        )
    } | {"python": sys.version.split()[0]}


def input_hashes() -> dict[str, str]:
    scale = load_yaml("configs/final_scale_v0_4.yaml")
    summary = read_json(scale["public_outputs"]["scale_summary"])
    integrity = read_json(scale["private_outputs"]["integrity_manifest"])
    ensure(summary["status"] == "complete", "A v0.4 deve estar concluída.")
    expected = dict(summary["frozen_hashes"])
    expected.update(
        {scale["private_outputs"][k]: v for k, v in integrity["private_artifact_hashes"].items()}
    )
    for path, digest in expected.items():
        ensure(sha256_file(project_path(path)) == digest, "Hash congelado divergente.")
    paths = [
        "reports/feature_manifest_v0_1_1_revision.csv",
        "reports/final_analysis_protocol_v1_0.md",
        "reports/final_sampling_protocol_v1_0.md",
        "data/derived/private_final_study/final_lookup_v1_0.parquet",
    ]
    return expected | {path: sha256_file(project_path(path)) for path in paths}


def assert_unique(frame: pl.DataFrame, name: str, expected: int) -> None:
    ensure(frame.height == expected, f"Cardinalidade divergente: {name}.")
    for key in ("composition_key", "track_id"):
        ensure(
            frame[key].null_count() == 0 and frame[key].n_unique() == expected,
            f"Chave inválida: {name}.",
        )


def split_overlap(dev: pl.DataFrame, hold: pl.DataFrame) -> dict[str, int]:
    counts = {
        name: len(set(dev[name]) & set(hold[name]))
        for name in ("composition_key", "artist_group_id", "lyrics_sha256")
    }
    ensure(
        not counts["composition_key"] and not counts["artist_group_id"],
        "Leakage entre splits: treinamento bloqueado.",
    )
    ensure(
        not counts["lyrics_sha256"],
        "Letras idênticas entre splits: diagnóstico e decisão necessários antes do treino.",
    )
    return counts


def build_matrices(blocks: FeatureBlocks) -> tuple[pl.DataFrame, pl.DataFrame, dict]:
    scale = load_yaml("configs/final_scale_v0_4.yaml")
    index = pl.read_parquet(
        project_path(scale["private_outputs"]["lyrics_index"]),
        columns=[
            "composition_key",
            "representative_track_id",
            "split",
        ],
    ).rename({"representative_track_id": "track_id", "split": "accepted_split"})
    cohort = pl.concat(
        [
            pl.read_parquet(
                project_path(scale["private_outputs"][name]),
                columns=[
                    "composition_key",
                    "track_id",
                    "spotify_row_id",
                    "artist_group_id",
                    "split",
                ],
            )
            for name in ("cohort", "reserve")
        ]
    )
    metadata = index.join(cohort, on=["composition_key", "track_id"], how="left", validate="1:1")
    ensure(
        metadata.height == 10240 and metadata["split"].null_count() == 0,
        "Representantes congelados ausentes.",
    )
    ensure((metadata["accepted_split"] == metadata["split"]).all(), "Split divergente no índice.")
    split = pl.read_parquet(
        project_path(scale["inputs"]["split_assignments"]),
        columns=[
            "track_id",
            "spotify_row_id",
            "composition_key",
            "artist_group_id",
            "split",
        ],
    ).rename(
        {
            "composition_key": "assigned_composition",
            "artist_group_id": "assigned_artist",
            "split": "assigned_split",
        }
    )
    joined = metadata.join(split, on=["track_id", "spotify_row_id"], how="left", validate="1:1")
    ensure(
        (joined["composition_key"] == joined["assigned_composition"]).all(),
        "Composição divergente no split.",
    )
    ensure(
        (joined["artist_group_id"] == joined["assigned_artist"]).all(),
        "Artista divergente no split.",
    )
    ensure((joined["split"] == joined["assigned_split"]).all(), "Atribuição de split divergente.")
    selected = ["track_id", "spotify_row_id", *blocks.baseline, *blocks.traditional]
    ensure(not set(selected) & FORBIDDEN, "Leitura de features contém alvo/proxy.")
    # Projection precedes collection; the holdout is never loaded with a target.
    feature_base = (
        pl.scan_parquet(project_path(scale["inputs"]["modeling_base"]))
        .select(selected)
        .filter(pl.col("track_id").is_in(metadata["track_id"].to_list()))
        .collect()
    )
    ensure(feature_base.height == 10240, "Ausência de dados na base.")
    result = []
    for name, expected in (("development", 7648), ("holdout", 2592)):
        emb = pl.read_parquet(
            project_path(scale["private_outputs"][f"embeddings_{name}"]),
            columns=[
                "composition_key",
                "track_id",
                "lyrics_sha256",
                "embedding",
                "token_count",
                "chunk_count",
            ],
        )
        assert_unique(emb, name, expected)
        meta = metadata.filter(
            pl.col("split") == ("development_train" if name == "development" else "holdout_test")
        )
        frame = emb.join(
            meta.drop("accepted_split"),
            on=["composition_key", "track_id"],
            how="left",
            validate="1:1",
        )
        frame = frame.join(
            feature_base, on=["track_id", "spotify_row_id"], how="left", validate="1:1"
        )
        assert_unique(frame, name, expected)
        ensure(frame["artist_group_id"].null_count() == 0, "Grupo ausente.")
        arr = np.asarray(frame["embedding"].to_list(), dtype=np.float32)
        ensure(arr.shape == (expected, 384) and np.isfinite(arr).all(), "Embedding inválido.")
        ensure(float(np.max(np.abs(np.linalg.norm(arr, axis=1) - 1))) <= 1e-5, "Norma L2 inválida.")
        frame = _expand_embeddings(frame).sort("composition_key")
        for col in (*blocks.baseline, *blocks.traditional):
            if frame.schema[col].is_numeric():
                ensure(np.isfinite(frame[col].drop_nulls().to_numpy()).all(), "Feature não finita.")
        empty_lfm = frame.select(
            pl.all_horizontal([pl.col(c).is_null() for c in blocks.traditional]).sum()
        ).item()
        ensure(empty_lfm == 0, "Registro sem bloco LFM2b: treinamento bloqueado.")
        result.append(frame)
    dev, hold = result
    overlap = split_overlap(dev, hold)
    # Target projection is filtered to the frozen development representatives only.
    target = (
        pl.scan_parquet(project_path(scale["inputs"]["modeling_base"]))
        .filter(pl.col("track_id").is_in(dev["track_id"].to_list()))
        .select("track_id", "spotify_popularity")
        .collect()
    )
    dev = dev.join(target, on="track_id", how="left", validate="1:1")
    ensure(dev["spotify_popularity"].null_count() == 0, "Target ausente no desenvolvimento.")
    ensure(dev["spotify_popularity"].is_between(0, 100).all(), "Target inválido.")
    ensure(not set(hold.columns) & FORBIDDEN, "Target/proxy no holdout.")
    audit = {
        "development_rows": dev.height,
        "holdout_rows": hold.height,
        "development_artists": dev["artist_group_id"].n_unique(),
        "holdout_artists": hold["artist_group_id"].n_unique(),
        "overlap_counts": overlap,
        "row_multiplication": 0,
        "missing_embeddings": 0,
        "representatives_verified": True,
        "joins": "1:1 por composição, track_id e spotify_row_id",
        "feature_dimensions": {"baseline": 23, "lfm": 196, "embedding": 384},
        "holdout_target_loaded": False,
        "holdout_target_columns": [],
        "missing_by_feature_development": {
            c: dev[c].null_count() for c in blocks.columns("combined") if dev[c].null_count()
        },
        "missing_by_feature_holdout": {
            c: hold[c].null_count() for c in blocks.columns("combined") if hold[c].null_count()
        },
    }
    return dev, hold, audit


def create_folds(dev: pl.DataFrame, config: dict) -> tuple[pl.DataFrame, dict]:
    y, groups = dev["spotify_popularity"].to_numpy(), dev["artist_group_id"].to_numpy()
    seed = config["seed"]
    outer = make_grouped_folds(y, groups, n_splits=5, seed=seed)
    frame = dev.select("composition_key", "artist_group_id").with_columns(
        pl.Series("outer_fold", outer)
    )
    summary = {
        "outer_counts": np.bincount(outer).tolist(),
        "artist_overlap": [0] * 5,
        "composition_overlap": [0] * 5,
        "inner": [],
    }
    for fold in range(5):
        ids = np.flatnonzero(outer != fold)
        assignments = make_grouped_folds(y[ids], groups[ids], n_splits=3, seed=seed + 1000 + fold)
        all_values = np.full(dev.height, -1, dtype=int)
        all_values[ids] = assignments
        frame = frame.with_columns(pl.Series(f"inner_outer_{fold}", all_values))
        summary["inner"].append(
            {
                "outer_fold": fold,
                "counts": np.bincount(assignments).tolist(),
                "artist_overlap": [0] * 3,
            }
        )
    full = make_grouped_folds(y, groups, n_splits=3, seed=seed + 2000)
    return frame.with_columns(pl.Series("final_selection_fold", full)), summary


def prepare() -> dict:
    config = load_yaml(CONFIG)
    ensure(tuple(config["elastic_net"]["alpha"]) == ELASTIC_NET_ALPHAS, "Grade EN divergente.")
    ensure(
        tuple(config["elastic_net"]["l1_ratio"]) == ELASTIC_NET_L1_RATIOS, "Grade EN divergente."
    )
    ensure(tuple(config["ridge"]["alpha"]) == RIDGE_ALPHAS, "Grade Ridge divergente.")
    ensure(config["seed"] == 20261013, "Seed divergente.")
    hashes = input_hashes()
    blocks = load_feature_blocks()
    dev, hold, audit = build_matrices(blocks)
    for name, frame in (("development_matrix.parquet", dev), ("holdout_features.parquet", hold)):
        ensure(
            not private(name).exists(), "Preparação já existente; preservar e reutilizar o selo."
        )
        _atomic_write_frame(frame, private(name))
    folds, fold_audit = create_folds(dev, config)
    _atomic_write_frame(folds, private("fold_assignments.parquet"))
    data_hashes = {
        name: sha256_file(private(name))
        for name in (
            "development_matrix.parquet",
            "holdout_features.parquet",
            "fold_assignments.parquet",
        )
    }
    config_hash = sha256_file(project_path(CONFIG))
    text = f"""# Plano de execução de desenvolvimento v0.5

Registrado antes da primeira execução: {utc_now()}. Seed 20261013; SHA-256 da configuração completa: `{config_hash}`. Autoridade científica: final-study-protocol-v1.0. Matriz comum: 7648 desenvolvimento e 2592 holdout sem alvo. Hash público do arquivo completo de folds: `{data_hashes["fold_assignments.parquet"]}`.

Baseline: 23 features, sem PCA. Tradicional: 23 + 196, PCA90 somente LFM2b. Profundo: 23 + 384, PCA90 somente MiniLM. Combinado: 23 + 196 + 384, PCAs90 separadas dos blocos textuais. Listas autorizadas reconciliadas com o manifesto definitivo.

Baseline (ordem): `{", ".join(blocks.baseline)}`.

LFM2b (ordem): `{", ".join(blocks.traditional)}`.

MiniLM: embedding_000 até embedding_383, 384 dimensões congeladas. Flags semânticas de versão do manifesto são permitidas. Identificadores, artistas/títulos, hashes, matching, coleta, idioma, alvo e popularidades externas ficam fora dos preditores.

Validação: cinco folds externos agrupados por artist_group_id; três internos dentro de cada treino externo. Reutiliza-se o algoritmo de folds dos pilotos (StratifiedGroupKFold sobre quintis por postos do alvo de desenvolvimento). Seeds: externa 20261013; interna 20261013+1000+fold; seleção final no desenvolvimento completo 20261013+2000. Mesmas atribuições entre blocos e algoritmos, persistidas privadamente. Nenhuma composição ou artista cruza treino/validação.

Pré-processamento exato v0.3.1: numéricas Baseline → imputação mediana com indicadores de ausência e keep_empty_features → StandardScaler; categóricas genre/key/time_signature → imputação moda → one-hot com categorias desconhecidas ignoradas. Mode e flags semânticas são binárias; year mantém a forma linear validada no piloto. Cada bloco textual → imputação mediana (indicadores no LFM2b; sem indicadores no MiniLM) → remoção de constantes → StandardScaler → PCA full SVD até 90% → StandardScaler dos scores. Depois da concatenação aplica-se remoção de constantes. Baseline não recebe PCA. Ausências estruturais não são diretamente convertidas em zero; inteiramente ausentes no treino recebem o comportamento keep_empty_features documentado e indicador. Todos os ajustes ocorrem dentro do treino pertinente.

Elastic Net: alpha {config["elastic_net"]["alpha"]}; l1_ratio {config["elastic_net"]["l1_ratio"]}. Ridge: alpha {config["ridge"]["alpha"]}. Seleção: menor MAE médio nos três folds internos com pesos iguais por fold e desempate pela ordem fixa da grade dos pilotos. DummyRegressor mean. Métricas secundárias: RMSE, R² OOF e Spearman. Previsões brutas, sem clipping.

Elastic Net tol=0.001, max_iter=50000; retries de convergência em 200000 e 500000 autorizados e registrados. Persistir warnings, recusar solução ainda não convergida. Warm-start somente na trajetória de alpha descendente dentro de um treino e l1_ratio. Cache privado por configuração/hash da matriz/bloco/conjunto de treino. Duas tarefas internas em processos loky com dois threads numéricos cada; nenhuma transformação ajustada em outro conjunto de treino é reutilizada.

Inferência descritiva de desenvolvimento: 2000 bootstraps pareados de grupos de artista, seed 20261013, diferenças candidato menos Baseline do mesmo algoritmo, IC95%. Os intervalos condicionam-se às predições OOF e não incluem toda a incerteza de repetir treinamento. Os resultados não confirmam independentemente escolhas feitas no piloto. Diagnósticos por período/gênero somente com n≥30; não mudar modelos em função deles.

Candidato da demonstração: menor MAE OOF entre os quatro Elastic Net, desempate pela ordem baseline/traditional/deep/combined. Preservar os oito modelos para comparação final. Selecionar hiperparâmetros finais em três folds agrupados do desenvolvimento completo e ajustar cada pipeline completo com dados de desenvolvimento. Dummy separado.

Avaliação futura: três comparações primárias Elastic Net textual versus Baseline; MAE primária, RMSE secundária, R²/Spearman descritivas; bootstrap pareado por artista com 2000 reamostragens e seed 20261013. Multiplicidade: Bonferroni para a família das três comparações de MAE, intervalos percentis bilaterais 98.333333% (quantis 0.008333333 e 0.991666667), além dos IC95% descritivos. Ganho confirmado apenas com limite superior ajustado de ΔMAE abaixo de zero. Previsões brutas fora de 0–100 mantidas e contadas. Não retunar, fazer clipping ou modificar pré-processamento após abertura do alvo do teste.
"""
    write_report("final_development_execution_plan_v0_5.md", text)
    write_report(
        "final_holdout_evaluation_plan_v0_5.md",
        "# Avaliação futura única do holdout — plano v0.5\n\n"
        + text[text.index("Avaliação futura:") :],
    )
    write_report(
        "final_matrix_audit_v0_5.md",
        "# Auditoria da matriz comum v0.5\n\n```json\n"
        + json.dumps(audit, ensure_ascii=False, indent=2)
        + "\n```\n\nHashes completos das matrizes e folds no selo agregado da execução. Joins usam chaves congeladas, sem mudar representantes. Ausências documentadas são tratadas no treino.\n",
    )
    seal = {
        "status": "prepared_before_training",
        "created_at": utc_now(),
        "git_checkpoint_v04": git_commit(),
        "configuration_sha256": config_hash,
        "input_hashes": hashes,
        "data_hashes": data_hashes,
        "code_hashes": {
            name: sha256_file(project_path(name))
            for name in (
                "src/tcc_music_popularity/final_development_v050.py",
                "src/tcc_music_popularity/modeling_recalibration_v031.py",
                "src/tcc_music_popularity/modeling_pilot_v030.py",
            )
        },
        "matrix_audit": audit,
        "fold_audit": fold_audit,
        "versions": versions(),
        "holdout_target_loaded": False,
        "holdout_metrics_calculated": False,
    }
    write_json(SEAL, seal)
    write_json(SUMMARY, seal)
    return seal


def fit_checked(model: Any, x: np.ndarray, y: np.ndarray, config: dict) -> tuple[Any, list[dict]]:
    events = []
    limits = (
        [config["elastic_net"]["max_iter"], *config["elastic_net"]["convergence_retry_max_iter"]]
        if isinstance(model, ElasticNet)
        else [None]
    )
    for limit in limits:
        if limit is not None:
            model.set_params(max_iter=limit)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model.fit(x, y)
        for item in caught:
            events.append(
                {
                    "category": item.category.__name__,
                    "max_iter": limit,
                    "message": str(item.message),
                }
            )
        if not any(issubclass(item.category, ConvergenceWarning) for item in caught):
            return model, events
    raise RuntimeError("Elastic Net não convergiu; resultado recusado.")


def model_from_params(algorithm: str, params: dict, config: dict, **kwargs: Any) -> Any:
    if algorithm == "ridge":
        return Ridge(**params, **kwargs)
    return ElasticNet(
        **params,
        tol=config["elastic_net"]["tol"],
        max_iter=config["elastic_net"]["max_iter"],
        random_state=config["seed"],
        **kwargs,
    )


def tune_fold(
    algorithm: str, data: tuple, config: dict
) -> tuple[list[dict], list[float], list[dict]]:
    train, y, valid, yvalid = data
    events = []
    params_list, scores = [], []
    if algorithm == "ridge":
        for alpha in config["ridge"]["alpha"]:
            params = {"alpha": alpha}
            model, emitted = fit_checked(
                model_from_params(algorithm, params, config), train, y, config
            )
            events.extend(emitted)
            params_list.append(params)
            scores.append(float(np.mean(np.abs(yvalid - model.predict(valid)))))
    else:
        # Center once, cache the Gram matrix, and preserve the intercept analytically.
        # This is the same Elastic Net objective as fit_intercept=True.
        center_x, center_y = train.mean(axis=0), float(y.mean())
        x = np.asfortranarray(train - center_x, dtype=np.float64)
        yc = y - center_y
        gram = np.ascontiguousarray(x.T @ x)
        for ratio in config["elastic_net"]["l1_ratio"]:
            model = model_from_params(
                algorithm,
                {"alpha": max(config["elastic_net"]["alpha"]), "l1_ratio": ratio},
                config,
                warm_start=True,
                precompute=gram,
                fit_intercept=False,
            )
            for alpha in reversed(config["elastic_net"]["alpha"]):
                model.set_params(alpha=alpha)
                model, emitted = fit_checked(model, x, yc, config)
                events.extend(emitted)
                params_list.append({"alpha": alpha, "l1_ratio": ratio})
                pred = model.predict(valid - center_x) + center_y
                scores.append(float(np.mean(np.abs(yvalid - pred))))
    return params_list, scores, events


def tune(algorithm: str, data: list[tuple], config: dict) -> tuple[dict, dict]:
    workers = config["execution"]["tuning_workers"]
    with parallel_config(
        backend="loky",
        n_jobs=workers,
        inner_max_num_threads=config["execution"]["numerical_threads_per_worker"],
    ):
        evaluated = Parallel()(delayed(tune_fold)(algorithm, part, config) for part in data)
    params = evaluated[0][0]
    ensure(all(item[0] == params for item in evaluated), "Grade inconsistente entre folds.")
    scores = np.mean([item[1] for item in evaluated], axis=0)
    best = int(np.argmin(scores))
    return params[best], {
        "selected_inner_mae": float(scores[best]),
        "candidate_count": len(params),
        "warnings": [event for item in evaluated for event in item[2]],
        "all_candidates": [
            {"params": p, "mean_mae": float(s)} for p, s in zip(params, scores, strict=True)
        ],
    }


def cached_transform(
    frame: pl.DataFrame,
    train: np.ndarray,
    valid: np.ndarray,
    block: str,
    blocks: FeatureBlocks,
    directory: Path,
) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    cols = blocks.columns(block)
    representation = Representation(block, "raw" if block == "baseline" else "pca90")
    transformer = build_representation_transformer(representation, blocks)
    # The caller isolates directories by matrix/config hash, block and exact train set.
    signature = {"columns": cols, "train": train.tolist(), "valid": valid.tolist()}
    meta = directory / "indices.json"
    arrays = directory / "transformed.npz"
    serialized = directory / "transformer.joblib"
    if meta.exists() and arrays.exists() and serialized.exists():
        ensure(
            json.loads(meta.read_text()) == signature, "Cache pertence a outro conjunto de treino."
        )
        with np.load(arrays) as values:
            xt, xv = values["train"], values["valid"]
        transformer = joblib.load(serialized)
    else:
        xt = transformer.fit_transform(frame[train.tolist()].select(cols))
        xv = (
            transformer.transform(frame[valid.tolist()].select(cols))
            if len(valid)
            else np.empty((0, xt.shape[1]))
        )
        ensure(np.isfinite(xt).all() and np.isfinite(xv).all(), "Transformação não finita.")
        np.savez_compressed(arrays, train=xt, valid=xv)
        joblib.dump(transformer, serialized, compress=3)
        meta.write_text(json.dumps(signature), encoding="utf-8")
    return {
        "transformer": transformer,
        "train": xt,
        "valid": xv,
        "components": _components(transformer),
        "feature_groups": _feature_groups(transformer),
    }


def verify_seal() -> dict:
    seal = read_json(SEAL)
    ensure(seal is not None, "Preparar matriz/plano/selo antes do treinamento.")
    ensure(
        sha256_file(project_path(CONFIG)) == seal["configuration_sha256"],
        "Configuração mudou após o selo.",
    )
    ensure(input_hashes() == seal["input_hashes"], "Entradas mudaram após o selo.")
    for name, expected in seal["data_hashes"].items():
        ensure(sha256_file(private(name)) == expected, "Matriz/folds mudou após o selo.")
    for name, expected in seal["code_hashes"].items():
        ensure(sha256_file(project_path(name)) == expected, "Código mudou após o selo.")
    return seal


def nested_evaluation(
    dev: pl.DataFrame, folds: pl.DataFrame, blocks: FeatureBlocks, config: dict, seal: dict
) -> tuple[dict, list]:
    y = dev["spotify_popularity"].to_numpy().astype(float)
    groups = dev["artist_group_id"].to_numpy()
    outer = folds["outer_fold"].to_numpy()
    predictions = {
        f"{alg}__{block}": np.full(dev.height, np.nan)
        for alg in config["algorithms"]
        for block in config["blocks"]
    }
    predictions["dummy__baseline"] = np.full(dev.height, np.nan)
    rows = []
    cache_root = (
        private("transformations")
        / seal["configuration_sha256"]
        / seal["data_hashes"]["development_matrix.parquet"]
    )
    for block in config["blocks"]:
        for outer_fold in range(5):
            train, valid = np.flatnonzero(outer != outer_fold), np.flatnonzero(outer == outer_fold)
            assert_no_group_leakage(outer, groups)
            pending = [
                alg
                for alg in config["algorithms"]
                if not private(f"oof_parts/{alg}_{block}_{outer_fold}.joblib").exists()
            ]
            if pending:
                started_prep = time.perf_counter()
                inner = folds[f"inner_outer_{outer_fold}"].to_numpy()
                ensure(
                    np.all(inner[valid] == -1), "Validation externe présente dans folds internes."
                )
                data = []
                for inner_fold in range(3):
                    ti, vi = (
                        np.flatnonzero((inner >= 0) & (inner != inner_fold)),
                        np.flatnonzero(inner == inner_fold),
                    )
                    ensure(not set(groups[ti]) & set(groups[vi]), "Leakage interne.")
                    prep = cached_transform(
                        dev,
                        ti,
                        vi,
                        block,
                        blocks,
                        cache_root / block / f"outer{outer_fold}_inner{inner_fold}",
                    )
                    data.append((prep["train"], y[ti], prep["valid"], y[vi]))
                prep = cached_transform(
                    dev, train, valid, block, blocks, cache_root / block / f"outer{outer_fold}"
                )
                prep_seconds = time.perf_counter() - started_prep
            for alg in config["algorithms"]:
                path = private(f"oof_parts/{alg}_{block}_{outer_fold}.joblib")
                if path.exists():
                    part = joblib.load(path)
                else:
                    started = time.perf_counter()
                    selected, tuned = tune(alg, data, config)
                    model, events = fit_checked(
                        model_from_params(alg, selected, config), prep["train"], y[train], config
                    )
                    train_pred, val_pred = (
                        model.predict(prep["train"]),
                        model.predict(prep["valid"]),
                    )
                    tm, vm = (
                        regression_metrics(y[train], train_pred),
                        regression_metrics(y[valid], val_pred),
                    )
                    row = {
                        "model": f"{alg}__{block}",
                        "algorithm": alg,
                        "block": block,
                        "scope": "fold",
                        "fold": outer_fold,
                        "n": len(valid),
                        "train_n": len(train),
                        "artists": len(set(groups[valid])),
                        **vm,
                        "train_mae": tm["mae"],
                        "train_rmse": tm["rmse"],
                        "train_r2": tm["r2"],
                        "train_spearman": tm["spearman"],
                        "gap_mae": vm["mae"] - tm["mae"],
                        "selected_params": selected,
                        "pca_components": prep["components"],
                        "transformed_features": int(prep["train"].shape[1]),
                        "coefficients": coefficient_diagnostics(
                            model.coef_, prep["feature_groups"]
                        ),
                        "tuning_seconds": time.perf_counter() - started,
                        "preprocessing_seconds": prep_seconds,
                        "warnings": [*tuned["warnings"], *events],
                        "selected_inner_mae": tuned["selected_inner_mae"],
                    }
                    part = {
                        "validation_indices": valid,
                        "predictions": val_pred,
                        "row": row,
                        "tuning": tuned,
                    }
                    joblib.dump(part, path, compress=3)
                ensure(
                    np.array_equal(part["validation_indices"], valid), "Checkpoint de outro fold."
                )
                predictions[f"{alg}__{block}"][valid] = part["predictions"]
                rows.append(part["row"])
                print(f"V0.5 OOF: {alg} / {block} / fold {outer_fold + 1}/5", flush=True)
            if block == "baseline":
                dummy = DummyRegressor(strategy="mean").fit(np.zeros((len(train), 1)), y[train])
                pred = dummy.predict(np.zeros((len(valid), 1)))
                predictions["dummy__baseline"][valid] = pred
                tm, vm = (
                    regression_metrics(y[train], dummy.predict(np.zeros((len(train), 1)))),
                    regression_metrics(y[valid], pred),
                )
                rows.append(
                    {
                        "model": "dummy__baseline",
                        "algorithm": "dummy",
                        "block": "baseline",
                        "scope": "fold",
                        "fold": outer_fold,
                        "n": len(valid),
                        **vm,
                        "train_mae": tm["mae"],
                        "train_rmse": tm["rmse"],
                        "gap_mae": vm["mae"] - tm["mae"],
                        "selected_params": {"strategy": "mean"},
                        "pca_components": {"lfm": None, "embedding": None},
                        "warnings": [],
                    }
                )
    for key, pred in predictions.items():
        ensure(np.isfinite(pred).all(), "Predições OOF incompletas/não finitas.")
        matches = [row for row in rows if row["model"] == key]
        rows.append(
            {
                "model": key,
                "algorithm": key.split("__")[0],
                "block": key.split("__")[1],
                "scope": "overall_oof",
                "fold": None,
                "n": dev.height,
                **regression_metrics(y, pred),
                "train_mae": float(
                    np.average(
                        [row["train_mae"] for row in matches],
                        weights=[row.get("train_n", dev.height - row["n"]) for row in matches],
                    )
                ),
                "train_rmse": float(
                    np.average(
                        [row["train_rmse"] for row in matches],
                        weights=[row.get("train_n", dev.height - row["n"]) for row in matches],
                    )
                ),
                "warnings_count": sum(len(row["warnings"]) for row in matches),
                "out_of_range_predictions": int(np.sum((pred < 0) | (pred > 100))),
                "tuning_seconds": sum(row.get("tuning_seconds", 0) for row in matches),
                "preprocessing_seconds": sum(
                    row.get("preprocessing_seconds", 0) for row in matches
                ),
            }
        )
    return predictions, rows


def freeze_models(
    dev: pl.DataFrame, folds: pl.DataFrame, blocks: FeatureBlocks, config: dict, seal: dict
) -> list[dict]:
    y = dev["spotify_popularity"].to_numpy().astype(float)
    groups = dev["artist_group_id"].to_numpy()
    assignments = folds["final_selection_fold"].to_numpy()
    assert_no_group_leakage(assignments, groups)
    models = []
    cache_root = (
        private("transformations")
        / seal["configuration_sha256"]
        / seal["data_hashes"]["development_matrix.parquet"]
    )
    for block in config["blocks"]:
        data = []
        for fold in range(3):
            ti, vi = np.flatnonzero(assignments != fold), np.flatnonzero(assignments == fold)
            prep = cached_transform(
                dev, ti, vi, block, blocks, cache_root / block / f"final_inner{fold}"
            )
            data.append((prep["train"], y[ti], prep["valid"], y[vi]))
        all_idx = np.arange(dev.height)
        prep = cached_transform(
            dev, all_idx, np.array([], dtype=int), block, blocks, cache_root / block / "final_full"
        )
        for alg in config["algorithms"]:
            key = f"{alg}__{block}"
            path = private(f"models/{key}.joblib")
            meta = private(f"models/{key}.json")
            if path.exists() and meta.exists():
                model_info = json.loads(meta.read_text())
                ensure(
                    sha256_file(path) == model_info["model_sha256"], "Modelo privado divergente."
                )
            else:
                started = time.perf_counter()
                selected, tuned = tune(alg, data, config)
                model, emitted = fit_checked(
                    model_from_params(alg, selected, config), prep["train"], y, config
                )
                pipeline = Pipeline([("representation", prep["transformer"]), ("model", model)])
                train_pred = pipeline.predict(dev.select(blocks.columns(block)))
                joblib.dump(pipeline, path, compress=3)
                restored = joblib.load(path)
                np.testing.assert_allclose(
                    restored.predict(dev.head(10).select(blocks.columns(block))),
                    train_pred[:10],
                    atol=1e-10,
                )
                model_info = {
                    "model": key,
                    "algorithm": alg,
                    "block": block,
                    "params": selected,
                    "pca_components": prep["components"],
                    "training_metrics": regression_metrics(y, train_pred),
                    "selection_mae": tuned["selected_inner_mae"],
                    "model_sha256": sha256_file(path),
                    "input_columns": blocks.columns(block),
                    "input_schema": {c: str(dev.schema[c]) for c in blocks.columns(block)},
                    "coefficients": coefficient_diagnostics(model.coef_, prep["feature_groups"]),
                    "seconds": time.perf_counter() - started,
                    "warnings": [*tuned["warnings"], *emitted],
                }
                meta.write_text(
                    json.dumps(model_info, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            models.append(model_info)
            print(f"V0.5 modelo congelado: {key}", flush=True)
    dummy = DummyRegressor(strategy="mean").fit(dev.select(blocks.baseline).to_numpy(), y)
    joblib.dump(dummy, private("models/dummy__baseline.joblib"), compress=3)
    models.append(
        {
            "model": "dummy__baseline",
            "algorithm": "dummy",
            "block": "baseline",
            "params": {"strategy": "mean"},
            "input_columns": list(blocks.baseline),
            "model_sha256": sha256_file(private("models/dummy__baseline.joblib")),
            "warnings": [],
        }
    )
    return models


def diagnostics(dev: pl.DataFrame, predictions: dict, config: dict) -> dict:
    y = dev["spotify_popularity"].to_numpy()
    result = {
        "minimum_cell_size": config["minimum_diagnostic_cell"],
        "period": [],
        "genre": [],
        "residuals": [],
    }
    periods = np.array([_period_label(int(value)) for value in dev["year"]])
    genres = dev["genre"].to_numpy()
    for name, labels in (("period", periods), ("genre", genres)):
        for label in sorted(set(labels), key=str):
            mask = labels == label
            if int(mask.sum()) < config["minimum_diagnostic_cell"]:
                continue
            for key, pred in predictions.items():
                result[name].append(
                    {
                        "category": str(label),
                        "model": key,
                        "n": int(mask.sum()),
                        **regression_metrics(y[mask], pred[mask]),
                        "mean_residual": float(np.mean(y[mask] - pred[mask])),
                    }
                )
    for key, pred in predictions.items():
        residual = y - pred
        result["residuals"].append(
            {
                "model": key,
                "n": len(y),
                "mean": float(np.mean(residual)),
                "std": float(np.std(residual)),
                "quantiles": dict(
                    zip(
                        ["q05", "q25", "q50", "q75", "q95"],
                        np.quantile(residual, [0.05, 0.25, 0.5, 0.75, 0.95]).tolist(),
                        strict=True,
                    )
                ),
            }
        )
    return result


def public_audit(paths: list[str]) -> dict:
    for path in paths:
        text = project_path(path).read_text(encoding="utf-8")
        ensure(
            not any(
                marker in text
                for marker in (
                    "plainLyrics",
                    "syncedLyrics",
                    "private_lyrics",
                    "token_ids_private",
                    'lyrics_sha256": "',
                    "prediction__",
                )
            ),
            "Conteúdo individual em artefato público.",
        )
    private_git = _git_private_files()
    ensure(not private_git["tracked"] and not private_git["staged"], "Artefatos privados no Git.")
    return {"public_violations": 0, "private_tracked": 0, "private_staged": 0}


def report_results(summary: dict) -> None:
    rows = summary["metrics"]
    fields = sorted({key for row in rows for key in row})
    with project_path("reports/final_development_metrics_v0_5.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                    for k, v in row.items()
                }
            )

    def table(headers: list, values: list) -> str:
        return (
            "| "
            + " | ".join(headers)
            + " |\n|"
            + "---|" * len(headers)
            + "\n"
            + "\n".join("| " + " | ".join(str(x) for x in row) + " |" for row in values)
        )

    overall = [row for row in rows if row["scope"] == "overall_oof"]
    text = "# Modelagem final — desenvolvimento v0.5\n\n"
    text += "Uma amostra comum de 7.648 composições; validação aninhada agrupada por artista, cinco folds externos e três internos. Alvo do holdout permanece selado. Previsões e modelos completos permanecem privados.\n\n"
    text += table(
        ["Modelo", "MAE", "RMSE", "R² OOF", "Spearman", "MAE treino", "Tempo tuning s", "Warnings"],
        [
            [
                r["model"],
                *[
                    f"{r[k]:.5f}" if r[k] is not None else "—"
                    for k in ("mae", "rmse", "r2", "spearman", "train_mae", "tuning_seconds")
                ],
                r["warnings_count"],
            ]
            for r in overall
        ],
    )
    text += "\n\n## Resultados por fold\n\n"
    text += table(
        [
            "Modelo",
            "Fold",
            "n",
            "MAE",
            "RMSE",
            "R²",
            "Spearman",
            "MAE treino",
            "Parâmetros",
            "PCA LFM/MiniLM",
            "Coef. não nulos",
            "Warnings",
        ],
        [
            [
                r["model"],
                r["fold"],
                r["n"],
                *[
                    f"{r[k]:.5f}" if r[k] is not None else "—"
                    for k in ("mae", "rmse", "r2", "spearman", "train_mae")
                ],
                json.dumps(r["selected_params"]),
                json.dumps(r["pca_components"]),
                r.get("coefficients", {}).get("nonzero_total", "—"),
                len(r["warnings"]),
            ]
            for r in rows
            if r["scope"] == "fold"
        ],
    )
    text += "\n\n## Incremento versus Baseline do mesmo algoritmo\n\n"
    text += table(
        ["Modelo", "ΔMAE", "IC95% ΔMAE", "ΔRMSE", "IC95% ΔRMSE"],
        [
            [
                r["model"],
                f"{r['mae_difference']:.5f}",
                f"[{r['mae_ci95_low']:.5f}, {r['mae_ci95_high']:.5f}]",
                f"{r['rmse_difference']:.5f}",
                f"[{r['rmse_ci95_low']:.5f}, {r['rmse_ci95_high']:.5f}]",
            ]
            for r in summary["comparisons"]
        ],
    )
    text += "\n\nDiferenças negativas favorecem o bloco textual. ICs descritivos por 2.000 bootstraps pareados por artista; condicionam-se às predições OOF e não incluem toda a incerteza de repetir o treinamento. Desenvolvimento não é confirmação independente das escolhas dos pilotos.\n\n"
    text += f"Candidato principal da demonstração: `{summary['candidate']}` pelo menor MAE OOF Elastic Net. Todos os quatro Elastic Net, quatro Ridge e Dummy foram preservados. Grades e representações permaneceram congeladas.\n\n"
    text += "## Modelos completos congelados\n\n" + table(
        ["Modelo", "Parâmetros", "PCA", "Coef. não nulos", "Tempo s"],
        [
            [
                r["model"],
                json.dumps(r["params"]),
                json.dumps(r.get("pca_components", {})),
                r.get("coefficients", {}).get("nonzero_total", "—"),
                f"{r.get('seconds', 0):.2f}",
            ]
            for r in summary["final_models"]
        ],
    )
    text += "\n\n## Diagnósticos agregados\n\n"
    for dimension in ("period", "genre"):
        text += (
            f"### {dimension} (n≥30)\n\n"
            + table(
                ["Categoria", "Modelo", "n", "MAE", "RMSE", "Resíduo médio"],
                [
                    [
                        r["category"],
                        r["model"],
                        r["n"],
                        f"{r['mae']:.4f}",
                        f"{r['rmse']:.4f}",
                        f"{r['mean_residual']:.4f}",
                    ]
                    for r in summary["diagnostics"][dimension]
                ],
            )
            + "\n\n"
        )
    text += "### Resíduos\n\n" + table(
        ["Modelo", "Média", "Desvio", "Quantis 5/25/50/75/95%"],
        [
            [r["model"], f"{r['mean']:.4f}", f"{r['std']:.4f}", json.dumps(r["quantiles"])]
            for r in summary["diagnostics"]["residuals"]
        ],
    )
    text += "\n\n## Limitações\n\nCoorte condicionada à disponibilidade de letras aceitas e matching anterior; descritores LFM2b podem referir-se a outra versão da letra em relação à LRCLIB. Os IDs operacionais não são universais. MiniLM é predominantemente validado para inglês e a coleta inclui outros idiomas. Não há interpretação causal. Escolhas dos pilotos e sobreposição da amostra com o piloto limitam a independência do desenvolvimento. Nenhum diagnóstico alterou os modelos.\n"
    write_report("final_development_report_v0_5.md", text)


def create_figures(summary: dict) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory = project_path("reports/figures/final_development_v0_5")
    directory.mkdir(parents=True, exist_ok=True)
    rows = [r for r in summary["metrics"] if r["scope"] == "overall_oof"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh([r["model"] for r in rows], [r["mae"] for r in rows])
    ax.set_xlabel("MAE OOF — desenvolvimento")
    fig.tight_layout()
    path = directory / "oof_mae.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return [str(path.relative_to(project_path("."))).replace("\\", "/")]


def train() -> dict:
    seal = verify_seal()
    ensure(not project_path(MANIFEST).exists(), "Modelos já congelados; verificar, sem retunar.")
    config, blocks = load_yaml(CONFIG), load_feature_blocks()
    dev = pl.read_parquet(private("development_matrix.parquet"))
    folds = pl.read_parquet(private("fold_assignments.parquet"))
    ensure(
        dev["composition_key"].to_list() == folds["composition_key"].to_list(),
        "Atribuições não alinham por chave.",
    )
    ensure(set(dev["split"]) == {"development_train"}, "Treino contém holdout.")
    started = time.perf_counter()
    with threadpool_limits(limits=config["execution"]["numerical_threads_per_worker"]):
        predictions, rows = nested_evaluation(dev, folds, blocks, config, seal)
        oof = dev.select(
            "composition_key", "track_id", "artist_group_id", "spotify_popularity"
        ).with_columns(folds["outer_fold"])
        for key, pred in predictions.items():
            oof = oof.with_columns(pl.Series(f"prediction__{key}", pred))
        _atomic_write_frame(oof, private("oof_predictions.parquet"))
        y, groups = dev["spotify_popularity"].to_numpy(), dev["artist_group_id"].to_numpy()
        comparisons = [
            {
                "model": f"{alg}__{block}",
                **grouped_paired_bootstrap(
                    y,
                    predictions[f"{alg}__baseline"],
                    predictions[f"{alg}__{block}"],
                    groups,
                    repetitions=config["bootstrap_repetitions"],
                    seed=config["seed"],
                ),
            }
            for alg in config["algorithms"]
            for block in config["blocks"]
            if block != "baseline"
        ]
        models = freeze_models(dev, folds, blocks, config, seal)
    overall = {r["model"]: r for r in rows if r["scope"] == "overall_oof"}
    candidate = min(
        (f"elastic_net__{block}" for block in config["blocks"]), key=lambda key: overall[key]["mae"]
    )
    manifest = {
        "status": "frozen_pre_holdout",
        "version": "v0.5",
        "created_at": utc_now(),
        "configuration": config,
        "configuration_sha256": seal["configuration_sha256"],
        "training_matrix_sha256": seal["data_hashes"]["development_matrix.parquet"],
        "fold_assignments_sha256": seal["data_hashes"]["fold_assignments.parquet"],
        "source_file_hashes": {Path(k).name: v for k, v in seal["input_hashes"].items()},
        "allowed_features": {
            "baseline": list(blocks.baseline),
            "lfm": list(blocks.traditional),
            "minilm": list(blocks.embeddings),
        },
        "versions": versions(),
        "models": models,
        "oof_metrics": list(overall.values()),
        "candidate": candidate,
        "candidate_rule": "menor MAE OOF Elastic Net; empate pela ordem de blocos congelada",
        "prediction_policy": "raw_unclipped",
        "holdout_target_loaded": False,
        "holdout_metrics_calculated": False,
    }
    summary = {
        "status": "models_frozen_verification_pending",
        "version": "v0.5",
        "completed_at": utc_now(),
        "configuration_sha256": seal["configuration_sha256"],
        "source_file_hashes": manifest["source_file_hashes"],
        "data_hashes": seal["data_hashes"],
        "matrix_audit": seal["matrix_audit"],
        "fold_audit": seal["fold_audit"],
        "metrics": rows,
        "comparisons": comparisons,
        "final_models": models,
        "candidate": candidate,
        "diagnostics": diagnostics(dev, predictions, config),
        "seconds": time.perf_counter() - started,
        "versions": versions(),
        "oof_file_sha256": sha256_file(private("oof_predictions.parquet")),
        "holdout_target_loaded": False,
        "holdout_metrics_calculated": False,
        "tests": {"status": "pending"},
    }
    write_json(MANIFEST, manifest)
    report_results(summary)
    summary["figures"] = create_figures(summary)
    summary["privacy"] = public_audit(
        [
            MANIFEST,
            "reports/final_development_report_v0_5.md",
            "reports/final_development_metrics_v0_5.csv",
            "reports/final_development_execution_plan_v0_5.md",
            "reports/final_matrix_audit_v0_5.md",
        ]
    )
    verify_seal()
    write_json(SUMMARY, summary)
    return {
        "status": summary["status"],
        "candidate": candidate,
        "oof_metrics": list(overall.values()),
    }


def verify() -> dict:
    seal = verify_seal()
    manifest = read_json(MANIFEST)
    dev = pl.read_parquet(private("development_matrix.parquet"))
    hold = pl.read_parquet(private("holdout_features.parquet"))
    folds = pl.read_parquet(private("fold_assignments.parquet"))
    oof = pl.read_parquet(private("oof_predictions.parquet"))
    ensure(
        dev.height == 7648 and hold.height == 2592 and oof.height == 7648,
        "Cardinalidade divergente.",
    )
    ensure(not set(hold.columns) & FORBIDDEN, "Holdout com target.")
    overlap = split_overlap(dev, hold)
    ensure(
        set(dev["composition_key"]) == set(oof["composition_key"]), "OOF não cobre desenvolvimento."
    )
    for column in folds.columns:
        if column in ("composition_key", "artist_group_id"):
            continue
        assigned = folds[column].to_numpy()
        mask = assigned >= 0
        assert_no_group_leakage(assigned[mask], folds["artist_group_id"].to_numpy()[mask])
    for column in oof.columns:
        if column.startswith("prediction__"):
            ensure(np.isfinite(oof[column].to_numpy()).all(), "OOF não finito.")
    for model in manifest["models"]:
        path = private(f"models/{model['model']}.joblib")
        ensure(sha256_file(path) == model["model_sha256"], "Modelo serializado mudou.")
        restored = joblib.load(path)
        prediction = restored.predict(
            dev.head(8).select(model["input_columns"]).to_numpy()
            if model["algorithm"] == "dummy"
            else dev.head(8).select(model["input_columns"])
        )
        ensure(np.isfinite(prediction).all(), "Modelo serializado não produz valores finitos.")
    privacy = public_audit(
        [
            MANIFEST,
            SUMMARY,
            "reports/final_development_report_v0_5.md",
            "reports/final_development_metrics_v0_5.csv",
        ]
    )
    return {
        "status": "passed",
        "models_verified": len(manifest["models"]),
        "oof_complete": True,
        "folds_grouped": True,
        "overlap_counts": overlap,
        "hashes_preserved": True,
        "holdout_target_loaded": False,
        "holdout_metrics_calculated": False,
        "training_hash": seal["data_hashes"]["development_matrix.parquet"],
        "privacy": privacy,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "train", "verify"])
    command = parser.parse_args().command
    result = {"prepare": prepare, "train": train, "verify": verify}[command]()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
