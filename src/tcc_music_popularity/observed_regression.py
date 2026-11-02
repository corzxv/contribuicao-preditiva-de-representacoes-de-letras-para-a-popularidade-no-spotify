"""Ridge pareada nos quatro blocos: CV 5x3, checkpoints e sensibilidade de pesos."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sqlite3
import time
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_limits

from . import observed_modeling_data as data
from .cohort_regression import fit_checked, predict_checked
from .manual_lyrics import atomic_frame, atomic_json, exclusive, fingerprint, require

ROOT = data.ROOT
WORKSPACE = ROOT / "data/derived/private_regression_200k_v1"
OUTPUT = ROOT / "reports/modelagem_200k_v1"
PROTOCOL = ROOT / "docs/protocolo_regressao_200k_v1.md"
BLOCKS = ("baseline", "traditional", "deep", "combined")
REFERENCES = ("mean", "median")
ALPHAS = (0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0)
MAX_ITER = 10000
TOL = 1e-5
E5 = tuple(f"e5_{i:03d}" for i in range(384))


def metrics(y, prediction, weights):
    y, prediction, weights = (np.asarray(v, dtype=float) for v in (y, prediction, weights))
    require(
        y.ndim == 1 and y.shape == prediction.shape == weights.shape and len(y) > 0,
        "Métricas com observações incompatíveis.",
    )
    require(
        all(np.isfinite(v).all() for v in (y, prediction, weights)) and (weights > 0).all(),
        "Valores não finitos/pesos inválidos nas métricas.",
    )
    error = y - prediction
    total = float(np.sum((y - np.mean(y)) ** 2))
    return {
        "n": len(y),
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "r2": float(1 - np.sum(error**2) / total) if total > 0 else None,
        "mae_original_weight": float(np.average(np.abs(error), weights=weights)),
        "predictions_outside_0_100": int(((prediction < 0) | (prediction > 100)).sum()),
    }


def columns_for(block):
    require(block in BLOCKS, "Bloco desconhecido.")
    manifest = data.blocks_manifest()["blocks"][block]
    return manifest["columns"] + (list(E5) if manifest["embedding"] else [])


def preprocessor(block):
    columns = columns_for(block)
    categorical = ["model_" + c for c in data.CATEGORICAL]
    numeric = [c for c in columns if c not in categorical]
    return ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
                        ("scale", StandardScaler()),
                    ]
                ),
                numeric,
            ),
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
        ],
        remainder="drop",
        sparse_threshold=0,
    )


def ridge(alpha):
    return Ridge(alpha=alpha, solver="lsqr", tol=TOL, max_iter=MAX_ITER, fit_intercept=True)


def fit_ridge(x, y, alpha):
    require(np.isfinite(x).all(), "Matriz de treino não finita após preparação.")
    model = ridge(alpha)
    seconds, warnings = fit_checked(model, x, y)
    iterations = int(np.max(model.n_iter_))
    require(iterations < MAX_ITER, "LSQR atingiu limite; diagnosticar sem mudar a grade.")
    return model, {"fit_seconds": seconds, "iterations": iterations, "warnings": warnings}


def smoke_subset(frame, folds):
    """Componentes inteiros; <=20 componentes/240 faixas por fold, sem usar alvo."""
    sizes = (
        frame.select("text_component_id")
        .with_columns(folds["outer_fold"])
        .group_by("text_component_id", "outer_fold")
        .len()
    )
    selected = set()
    for outer in range(5):
        groups = sizes.filter(pl.col("outer_fold") == outer).to_dicts()
        groups.sort(
            key=lambda r: hashlib.sha256(
                f"{data.SEED}\0{r['text_component_id']}".encode()
            ).hexdigest()
        )
        count, rows = 0, 0
        for group in groups:
            if count < 20 and rows + group["len"] <= 240:
                selected.add(group["text_component_id"])
                count += 1
                rows += group["len"]
        require(count > 0, "Smoke sem componente completo no fold externo.")
    mask = frame["text_component_id"].is_in(sorted(selected))
    sample, assignments = frame.filter(mask), folds.filter(mask)
    data.audit_folds(assignments)
    require(sample.height <= 1200, "Smoke excedeu limite de observações.")
    return sample, assignments


def tune(frame, folds, outer, block, db, mode):
    """Apenas treinos/validações internos; checkpoint por ajuste concluído."""
    records = []
    column = f"inner_outer_{outer}"
    for inner in range(3):
        train = np.flatnonzero(
            (folds["outer_fold"].to_numpy() != outer) & (folds[column].to_numpy() != inner)
        )
        valid = np.flatnonzero(folds[column].to_numpy() == inner)
        require(len(train) > 0 and len(valid) > 0, "Partição interna vazia.")
        prepare, x_train, x_valid = None, None, None
        for alpha in ALPHAS:
            key = f"{mode}/{outer}/{block}/{inner}/{alpha:g}"
            stored = db.execute("SELECT payload,sha256 FROM tuning WHERE key=?", (key,)).fetchone()
            if stored:
                record = json.loads(stored[0])
                require(
                    fingerprint(record) == stored[1]
                    and record["n"] == len(valid)
                    and np.isfinite(record["sum_abs_error"])
                    and record["sum_abs_error"] >= 0,
                    "Checkpoint interno incompatível/corrompido.",
                )
            else:
                if prepare is None:
                    prepare = preprocessor(block)
                    x_train = prepare.fit_transform(frame[train].select(columns_for(block)))
                    x_valid = prepare.transform(frame[valid].select(columns_for(block)))
                    require(np.isfinite(x_valid).all(), "Validação interna não finita.")
                model, details = fit_ridge(x_train, frame[data.TARGET].to_numpy()[train], alpha)
                prediction, predict_logs = predict_checked(model, x_valid)
                record = {
                    "outer": outer,
                    "inner": inner,
                    "block": block,
                    "alpha": alpha,
                    "n": len(valid),
                    "sum_abs_error": float(
                        np.sum(np.abs(frame[data.TARGET].to_numpy()[valid] - prediction))
                    ),
                    "transformed_features": x_train.shape[1],
                    **details,
                    "predict_warnings": predict_logs,
                }
                with db:
                    db.execute(
                        "INSERT INTO tuning VALUES (?,?,?)",
                        (key, json.dumps(record), fingerprint(record)),
                    )
                print(
                    json.dumps(
                        {
                            "stage": "inner_fit",
                            "mode": mode,
                            "outer": outer,
                            "block": block,
                            "inner": inner,
                            "alpha": alpha,
                            "fit_seconds": details["fit_seconds"],
                        }
                    ),
                    flush=True,
                )
            records.append(record)
    scores = [
        {
            "alpha": alpha,
            "mae": sum(r["sum_abs_error"] for r in records if r["alpha"] == alpha)
            / sum(r["n"] for r in records if r["alpha"] == alpha),
        }
        for alpha in ALPHAS
    ]
    best = min(scores, key=lambda r: (r["mae"], -r["alpha"]))
    return best["alpha"], scores


def fit_outer(frame, folds, outer, block, db, mode):
    alpha, scores = tune(frame, folds, outer, block, db, mode)
    train = np.flatnonzero(folds["outer_fold"].to_numpy() != outer)
    valid = np.flatnonzero(folds["outer_fold"].to_numpy() == outer)
    prepare = preprocessor(block)
    x_train = prepare.fit_transform(frame[train].select(columns_for(block)))
    model, details = fit_ridge(x_train, frame[data.TARGET].to_numpy()[train], alpha)
    fitted = Pipeline([("prepare", prepare), ("model", model)])
    prediction, logs = predict_checked(fitted, frame[valid].select(columns_for(block)))
    return (
        fitted,
        prediction,
        {
            "selected_alpha": alpha,
            "inner_scores": scores,
            "train_rows": len(train),
            "valid_rows": len(valid),
            "transformed_features": x_train.shape[1],
            **details,
            "predict_warnings": logs,
        },
    )


def save_part(directory, signature, outer, block, model, prediction, valid, details):
    directory.mkdir(parents=True, exist_ok=True)
    stem = directory / f"outer{outer}_{block}"
    path = stem.with_suffix(".joblib")
    temporary = stem.with_suffix(".joblib.tmp")
    joblib.dump(model, temporary)
    temporary.replace(path)
    predictions = stem.with_suffix(".parquet")
    atomic_frame(
        predictions, valid.select("track_id").with_columns(pl.Series("prediction", prediction))
    )
    atomic_json(
        stem.with_suffix(".json"),
        {
            "signature": signature,
            "outer": outer,
            "block": block,
            "details": details,
            "model_sha256": data.embeddings.base.sha256(path),
            "predictions_sha256": data.embeddings.base.sha256(predictions),
        },
    )


def read_part(directory, signature, outer, block, valid):
    stem = directory / f"outer{outer}_{block}"
    if not stem.with_suffix(".json").exists():
        return None
    record = data.read_json(stem.with_suffix(".json"))
    require(
        record["signature"] == signature and record["outer"] == outer and record["block"] == block,
        "Parte de outro experimento.",
    )
    require(
        data.embeddings.base.sha256(stem.with_suffix(".joblib")) == record["model_sha256"]
        and data.embeddings.base.sha256(stem.with_suffix(".parquet"))
        == record["predictions_sha256"],
        "Parte concluída corrompida; preservar e diagnosticar.",
    )
    prediction = pl.read_parquet(stem.with_suffix(".parquet"))
    require(
        prediction.select("track_id").equals(valid.select("track_id"))
        and prediction["prediction"].null_count() == 0
        and prediction["prediction"].is_finite().all(),
        "Previsões desalinhadas/não finitas.",
    )
    return record, prediction


def evaluate_complete(frame, folds, directory, signature, workspace, output):
    result = frame.select(
        "track_id", "text_component_id", data.TARGET, "sampling_weight"
    ).with_columns(folds["outer_fold"])
    selections = []
    for block in (*BLOCKS, *REFERENCES):
        pieces = []
        for outer in range(5):
            valid = frame.filter(folds["outer_fold"] == outer)
            stored = read_part(directory, signature, outer, block, valid)
            require(stored is not None, "Avaliação global sem todas as partes.")
            record, predictions = stored
            pieces.append(predictions.rename({"prediction": "prediction_" + block}))
            if block in BLOCKS:
                selections.append(
                    {
                        "outer_fold": outer,
                        "block": block,
                        "alpha": record["details"]["selected_alpha"],
                    }
                )
        result = result.join(
            pl.concat(pieces), on="track_id", validate="1:1", maintain_order="left"
        )
    require(
        result.height == result["track_id"].n_unique() == frame.height,
        "Previsões externas não cobrem a mesma coorte.",
    )
    rows = [
        {
            "model": block,
            **metrics(
                result[data.TARGET], result["prediction_" + block], result["sampling_weight"]
            ),
        }
        for block in (*BLOCKS, *REFERENCES)
    ]
    by_name = {r["model"]: r for r in rows}
    differences = []
    for block, reference in (
        ("traditional", "baseline"),
        ("deep", "baseline"),
        ("combined", "baseline"),
        ("combined", "traditional"),
        ("combined", "deep"),
    ):
        differences.append(
            {
                "block": block,
                "reference": reference,
                "delta_mae": by_name[block]["mae"] - by_name[reference]["mae"],
                "delta_mae_original_weight": by_name[block]["mae_original_weight"]
                - by_name[reference]["mae_original_weight"],
            }
        )
    atomic_frame(workspace / "predicoes_externas.parquet", result)
    data.write_csv(output / "metricas_externas.csv", rows)
    data.write_csv(output / "incrementos_pareados.csv", differences)
    data.write_csv(output / "alphas_selecionados.csv", selections)
    return rows, differences


def load_sources(base_workspace, base_report, mode, expected):
    summary = data.read_json(base_report)
    require(
        summary["completed"]
        and summary["cohort_rows"] == expected
        and summary["leakage_checks_passed"]
        and summary["outer_folds"] == 5
        and summary["inner_folds"] == 3,
        "Base/folds incompletos.",
    )
    require(
        data.embeddings.base.sha256(Path(data.__file__)) == summary["seal"]["code"]
        and data.embeddings.base.sha256(data.PROTOCOL) == summary["seal"]["protocol"],
        "Código/protocolo da base mudou.",
    )
    for name, digest in summary["seal"]["support_code"].items():
        require(
            data.embeddings.base.sha256(Path(data.__file__).with_name(name)) == digest,
            "Utilitário selado da base mudou.",
        )
    sources = [base_report, *[base_workspace / name for name in summary["outputs_sha256"]]]
    for name, digest in summary["outputs_sha256"].items():
        require(
            data.embeddings.base.sha256(base_workspace / name) == digest, "Derivado da base mudou."
        )
    manifest = data.read_json(base_workspace / "blocos.json")
    specification = data.blocks_manifest()
    require(
        all(manifest[k] == v for k, v in specification.items()),
        "Manifesto dos blocos incompatível.",
    )
    store = Path(manifest["embeddings"])
    require(
        data.embeddings.base.sha256(store) == summary["seal"]["inputs"].get(str(store.resolve())),
        "Armazenamento de vetores mudou.",
    )
    sources.append(store)
    columns = [
        "track_id",
        "text_component_id",
        "text_input_sha256",
        data.TARGET,
        "sampling_weight",
        *data.BASELINE,
        *data.descriptors.FEATURES,
    ]
    frame = pl.read_parquet(base_workspace / "coorte_modelagem.parquet", columns=columns).sort(
        "track_id"
    )
    folds = pl.read_parquet(base_workspace / "folds_5x3.parquet").sort("track_id")
    require(
        frame.height == frame["track_id"].n_unique() == expected
        and frame.select("track_id", "text_component_id").equals(
            folds.select("track_id", "text_component_id")
        ),
        "Base/folds desalinhados.",
    )
    data.audit_folds(folds)
    if mode == "smoke":
        frame, folds = smoke_subset(frame, folds)
    vectors = pl.read_parquet(store)
    lookup = {key: i for i, key in enumerate(vectors["text_input_sha256"].to_list())}
    require(len(lookup) == vectors.height, "Vetor repetido no armazenamento.")
    array = vectors["embedding"].to_arrow()
    require(array.type.list_size == 384, "Schema de embedding incompatível.")
    matrix = array.values.to_numpy(zero_copy_only=False).reshape(vectors.height, 384)
    require(
        matrix.shape == (vectors.height, 384) and np.isfinite(matrix).all(), "Vetores inválidos."
    )
    require(set(frame["text_input_sha256"]) <= set(lookup), "Vetor ausente para a coorte.")
    aligned = matrix[[lookup[key] for key in frame["text_input_sha256"].to_list()]]
    frame = frame.hstack(pl.DataFrame(aligned, schema=list(E5), orient="row"))
    return frame, folds, sources


def seal_for(sources):
    return {
        "version": "observed-ridge-v1",
        "inputs": {str(p.resolve()): data.embeddings.base.sha256(p) for p in sources},
        "protocol": data.embeddings.base.sha256(PROTOCOL),
        "code": {
            name: data.embeddings.base.sha256(Path(__file__).with_name(name))
            for name in ("observed_regression.py", "cohort_regression.py", "manual_lyrics.py")
        },
        "alpha_grid": list(ALPHAS),
        "solver": "lsqr",
        "tol": TOL,
        "max_iter": MAX_ITER,
        "threads": 2,
        "versions": {
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
        },
        "python": platform.python_version(),
    }


def run(
    mode,
    *,
    base_workspace=data.WORKSPACE,
    base_report=data.OUTPUT / "resumo_base_modelagem.json",
    workspace=WORKSPACE,
    output=OUTPUT,
    expected=77535,
    limit_outer_blocks=None,
):
    require(mode in {"smoke", "all"}, "Modo inválido.")
    require(limit_outer_blocks is None or limit_outer_blocks > 0, "Limite deve ser positivo.")
    require(mode == "all" or limit_outer_blocks is None, "Limite disponível somente no modo all.")
    started = time.monotonic()
    workspace, output = workspace.resolve(), output.resolve()
    require(
        workspace.is_relative_to(ROOT / "data/derived") or expected != 77535,
        "Workspace deve ser privado.",
    )
    require(
        not workspace.is_relative_to(output) and not output.is_relative_to(workspace),
        "Separar saídas privadas/públicas.",
    )
    require(
        not base_workspace.resolve().is_relative_to(workspace)
        and not base_report.resolve().is_relative_to(output),
        "Saídas sobrepõem fontes.",
    )
    print("[1/4] Validando base/folds selados e alinhando vetores existentes...", flush=True)
    frame, folds, sources = load_sources(base_workspace, base_report, mode, expected)
    seal = seal_for(sources)
    signature = fingerprint(seal)
    destination = output / ("smoke" if mode == "smoke" else "integral")
    private = workspace / ("smoke" if mode == "smoke" else "integral")
    directory = private / "parts"
    summary = {
        "completed": False,
        "mode": mode,
        "seal": seal,
        "signature": signature,
        "source_rows": expected,
        "used_rows": frame.height,
        "new_outer_blocks": 0,
        "reused_outer_blocks": 0,
        "expected_outer_blocks": 4 if mode == "smoke" else 20,
        "training_weight_policy": "equal_track_weights",
        "selection": "unweighted_MAE",
        "sensitivity": "original_sampling_weights_same_predictions",
        "global_metrics_available": False,
    }
    with exclusive(workspace), threadpool_limits(limits=2):
        for folder in (workspace, destination):
            owner = folder / "owner.json"
            if owner.exists():
                require(
                    data.read_json(owner) == {"signature": signature},
                    "Saída de outro protocolo; preservada.",
                )
            else:
                require(
                    not any(p.name != "execution.lock" for p in folder.iterdir())
                    if folder.exists()
                    else True,
                    "Diretório sem proprietário; preservado.",
                )
                folder.mkdir(parents=True, exist_ok=True)
                atomic_json(owner, {"signature": signature})
        private.mkdir(parents=True, exist_ok=True)
        gate = workspace / "smoke_verified.json"
        if mode == "all":
            require(
                gate.exists()
                and data.read_json(gate) == {"signature": signature, "verified": True},
                "Execute smoke completo e revise o resultado antes da escala.",
            )
        else:
            atomic_json(gate, {"signature": signature, "verified": False})
        atomic_json(destination / "resumo_modelagem.json", summary)
        with sqlite3.connect(workspace / "state.sqlite") as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS tuning(key TEXT PRIMARY KEY,payload TEXT,sha256 TEXT)"
            )
            try:
                print(
                    f"[2/4] {mode}: Ridge nos quatro blocos; checkpoints por ajuste interno/parte...",
                    flush=True,
                )
                stopped = False
                for outer in [0] if mode == "smoke" else range(5):
                    valid = frame.filter(folds["outer_fold"] == outer)
                    train = frame.filter(folds["outer_fold"] != outer)
                    for reference in REFERENCES:
                        if read_part(directory, signature, outer, reference, valid) is None:
                            model = DummyRegressor(strategy=reference)
                            model.fit(np.zeros((train.height, 1)), train[data.TARGET].to_numpy())
                            prediction = model.predict(np.zeros((valid.height, 1)))
                            save_part(
                                directory,
                                signature,
                                outer,
                                reference,
                                model,
                                prediction,
                                valid,
                                {"train_rows": train.height, "valid_rows": valid.height},
                            )
                    # Primeiro lote mede o bloco com maior número de entradas.
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
                        fitted, prediction, details = fit_outer(
                            frame, folds, outer, block, db, mode
                        )
                        save_part(
                            directory, signature, outer, block, fitted, prediction, valid, details
                        )
                        summary["new_outer_blocks"] += 1
                        progress = {
                            "stage": "outer_block",
                            "mode": mode,
                            "outer": outer,
                            "block": block,
                            "new_outer_blocks": summary["new_outer_blocks"],
                            "reused_outer_blocks": summary["reused_outer_blocks"],
                            "seconds": time.monotonic() - started,
                        }
                        atomic_json(workspace / "progress.json", progress)
                        print(json.dumps(progress), flush=True)
                    if stopped:
                        break
                completed = summary["new_outer_blocks"] + summary["reused_outer_blocks"]
                summary.update(
                    completed_outer_blocks=completed,
                    pending_outer_blocks=summary["expected_outer_blocks"] - completed,
                )
                summary["completed"] = not stopped and summary["pending_outer_blocks"] == 0
                print("[3/4] Conferindo partes concluídas e cobertura das previsões...", flush=True)
                require(
                    all(
                        data.embeddings.base.sha256(p) == seal["inputs"][str(p.resolve())]
                        for p in sources
                    ),
                    "Uma fonte mudou durante a modelagem.",
                )
                if mode == "smoke" and summary["completed"]:
                    errors = []
                    valid = frame.filter(folds["outer_fold"] == 0).head(5)
                    for block in BLOCKS:
                        # Somente artefatos próprios, com hashes conferidos por read_part.
                        _, predictions = read_part(
                            directory, signature, 0, block, frame.filter(folds["outer_fold"] == 0)
                        )
                        model = joblib.load(directory / f"outer0_{block}.joblib")
                        repeated, _ = predict_checked(model, valid.select(columns_for(block)))
                        errors.append(
                            float(
                                np.max(
                                    np.abs(repeated - predictions["prediction"].head(5).to_numpy())
                                )
                            )
                        )
                    require(max(errors) <= 1e-8, "Reprodução das previsões do smoke falhou.")
                    summary["reload_max_abs_difference"] = max(errors)
                    atomic_json(gate, {"signature": signature, "verified": True})
                elif mode == "all" and summary["completed"]:
                    rows, differences = evaluate_complete(
                        frame, folds, directory, signature, private, destination
                    )
                    summary.update(
                        global_metrics_available=True,
                        prediction_rows=frame.height,
                        models_evaluated=len(rows),
                        paired_comparisons=len(differences),
                        predictions_sha256=data.embeddings.base.sha256(
                            private / "predicoes_externas.parquet"
                        ),
                    )
                summary["seconds_this_invocation"] = time.monotonic() - started
                atomic_json(destination / "resumo_modelagem.json", summary)
                (destination / "relatorio_modelagem.md").write_text(
                    "# Ridge no domínio observado\n\n"
                    + f"Modo {mode}; concluído: {summary['completed']}; "
                    + f"partes externas {completed}/{summary['expected_outer_blocks']}.\n\n"
                    + "CV agrupada aninhada 5x3; treino com pesos iguais, seleção por MAE não ponderado. "
                    + "RMSE/R² complementares e MAE ponderado apenas na avaliação das mesmas previsões. "
                    + "Quatro blocos Ridge, referências média/mediana; grade e protocolo fixos.\n\n"
                    + (
                        "Smoke é teste técnico em subconjunto; não é estimativa científica de desempenho. "
                        if mode == "smoke"
                        else "Métricas globais somente com todas as partes e mesmas faixas. "
                    )
                    + "Diferenças são descritivas, sem intervalos/p-valores nesta etapa. Não generalizar ao catálogo "
                    + "ou alegar confirmação independente após exposição do teste histórico.\n",
                    encoding="utf-8",
                )
                print(
                    f"[4/4] {'Concluído' if summary['completed'] else 'Parcial; retomar'}; agregados em {destination}",
                    flush=True,
                )
                return 0 if summary["completed"] else 2
            except BaseException as exc:
                summary.update(
                    completed=False,
                    error_type=type(exc).__name__,
                    error=str(exc),
                    seconds_this_invocation=time.monotonic() - started,
                )
                atomic_json(destination / "resumo_modelagem.json", summary)
                raise


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("smoke", "all"))
    parser.add_argument("--limit-outer-blocks", type=int)
    args = parser.parse_args()
    return run(args.mode, limit_outer_blocks=args.limit_outer_blocks)
