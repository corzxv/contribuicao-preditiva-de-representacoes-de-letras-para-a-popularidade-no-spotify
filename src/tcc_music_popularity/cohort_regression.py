"""Regressões pareadas na coorte aceita: CV aninhada, checkpoints e reprodução."""

from __future__ import annotations

import argparse
import itertools
import json
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from scipy import stats
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, LinearRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, SplineTransformer, StandardScaler
from threadpoolctl import threadpool_limits

from .cohort_statistics import (
    CATEGORIES,
    DEFAULT,
    SEED,
    TARGET,
    check_seal,
    read_json,
    require,
    save_json,
    validate_plan,
    workspace,
)
from .io import sha256_file, utc_now
from .manual_lyrics import exclusive
from .modeling_pilot_v030 import FORBIDDEN_PREDICTORS
from .statistical_revision_v080 import metrics

FAMILIES = ["ols", "ridge", "elastic_net", "additive_ridge"]
BLOCKS = ["baseline", "traditional"]
SMOOTH = [
    "year",
    "danceability",
    "energy",
    "loudness",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "duration_ms",
]


class AsinhTransform(TransformerMixin, BaseEstimator):
    """Transformação monotônica definida também para zero e valores negativos."""

    def fit(self, x, y=None):
        return self

    def transform(self, x):
        return np.arcsinh(np.asarray(x, float))


class StableSplines(TransformerMixin, BaseEstimator):
    """Remove constantes somente na base de ajuste; cinco nós uniformes, sem interações."""

    def fit(self, x, y=None):
        x = np.asarray(x, float)
        self.active_ = np.ptp(x, axis=0) > 0
        self.spline_ = None
        if self.active_.any():
            self.spline_ = SplineTransformer(
                n_knots=5,
                degree=3,
                knots="uniform",
                extrapolation="linear",
                include_bias=False,
            ).fit(x[:, self.active_])
        return self

    def transform(self, x):
        x = np.asarray(x, float)
        return self.spline_.transform(x[:, self.active_]) if self.spline_ else np.zeros((len(x), 1))


def input_matrix(frame, columns):
    require(not set(columns) & FORBIDDEN_PREDICTORS, "Input contém alvo, ID ou variável proibida.")
    require(len(set(columns)) == len(columns), "Input duplicado.")
    matrix = np.empty((frame.height, len(columns)), dtype=object)
    for i, name in enumerate(columns):
        if name in CATEGORIES:
            matrix[:, i] = [
                "__MISSING__" if v is None or str(v) == "" else str(v)
                for v in frame[name].to_list()
            ]
        else:
            values = frame[name].cast(pl.Float64).to_numpy().copy()
            values[~np.isfinite(values)] = np.nan
            matrix[:, i] = values
    return matrix


def candidates(family, block):
    transform = (
        ["identity", "asinh"] if block == "traditional" and family != "ols" else ["identity"]
    )
    if family == "ols":
        return [{"lfm_transform": "identity"}]
    if family in ("ridge", "additive_ridge"):
        return [
            {"alpha": a, "lfm_transform": t}
            for a, t in itertools.product((1.0, 100.0, 1000.0), transform)
        ]
    if family == "elastic_net":
        return [
            {"alpha": a, "l1_ratio": ratio, "lfm_transform": t}
            for a, ratio, t in itertools.product((0.03, 0.3), (0.1, 0.8), transform)
        ]
    raise ValueError(f"Família desconhecida: {family}")


def factory(columns, lyrics, family, params):
    require(not set(columns) & FORBIDDEN_PREDICTORS, "Alvo em X.")
    categorical = [i for i, n in enumerate(columns) if n in CATEGORIES]
    smooth = [i for i, n in enumerate(columns) if n in SMOOTH and family == "additive_ridge"]
    lfm = [i for i, n in enumerate(columns) if n in lyrics]
    other = [i for i in range(len(columns)) if i not in categorical + smooth + lfm]

    def numeric(*steps):
        return Pipeline(
            [
                ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
                *steps,
                ("scale", StandardScaler()),
            ]
        )

    transforms = []
    if other:
        transforms.append(("numeric", numeric(), other))
    if smooth:
        transforms.append(("smooth", numeric(("splines", StableSplines())), smooth))
    if lfm:
        steps = [("asinh", AsinhTransform())] if params.get("lfm_transform") == "asinh" else []
        transforms.append(("lfm", numeric(*steps), lfm))
    if categorical:
        transforms.append(
            (
                "categories",
                OneHotEncoder(handle_unknown="ignore", drop="first", sparse_output=False),
                categorical,
            )
        )
    if family == "ols":
        model = LinearRegression()
    elif family in ("ridge", "additive_ridge"):
        model = Ridge(alpha=params["alpha"], solver="svd")
    elif family == "elastic_net":
        model = ElasticNet(
            alpha=params["alpha"],
            l1_ratio=params["l1_ratio"],
            max_iter=20000,
            tol=1e-4,
            selection="cyclic",
        )
    else:
        raise ValueError(family)
    return Pipeline(
        [
            ("prepare", ColumnTransformer(transforms, remainder="drop", sparse_threshold=0)),
            ("model", model),
        ]
    )


def fit_checked(model, x, y):
    start = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model.fit(x, y)
    logs = [{"category": w.category.__name__, "message": str(w.message)} for w in caught]
    require(
        not any(issubclass(w.category, ConvergenceWarning) for w in caught), "Ajuste não convergiu."
    )
    return time.perf_counter() - start, logs


def predict_checked(model, x):
    """Preserva avisos de categorias desconhecidas no relatório, sem inundar o terminal."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        prediction = model.predict(x)
    logs = [
        {"phase": "predict", "category": w.category.__name__, "message": str(w.message)}
        for w in caught
    ]
    require(np.isfinite(prediction).all(), "Previsões não finitas.")
    return prediction, logs


def tune(x, y, columns, lyrics, family, block, inner):
    records = []
    for params in candidates(family, block):
        record = {"params": params, "fold_mae": [], "seconds": 0.0, "warnings": []}
        try:
            for partition in inner:
                train, valid = np.asarray(partition["train"]), np.asarray(partition["valid"])
                model = factory(columns, lyrics, family, params)
                seconds, logs = fit_checked(model, x[train], y[train])
                prediction, prediction_logs = predict_checked(model, x[valid])
                require(np.isfinite(prediction).all(), "Previsões internas não finitas.")
                record["fold_mae"].append(float(np.mean(np.abs(y[valid] - prediction))))
                record["seconds"] += seconds
                record["warnings"].extend(logs)
                record["warnings"].extend(prediction_logs)
            record.update(status="ok", mean_mae=float(np.mean(record["fold_mae"])))
        except (ValueError, FloatingPointError, np.linalg.LinAlgError) as exc:
            record.update(status="failed", error=str(exc))
        records.append(record)
    valid = [r for r in records if r["status"] == "ok"]
    require(valid, f"Nenhuma configuração convergiu: {family}/{block}.")
    # Empate exato: ordem da grade fixada no protocolo, não validação externa.
    best = min(valid, key=lambda r: r["mean_mae"])
    return best, records


def load(output):
    seal = check_seal(output)
    frame = pl.read_parquet(output / "development.parquet")
    require(frame["split"].unique().to_list() == ["development_train"], "Matriz inclui holdout.")
    plan = read_json(output / "folds.json")
    validate_plan(frame, plan)
    return seal, frame, plan


def save_part(output, name, fold, model, prediction, details):
    directory = output / "models"
    directory.mkdir(exist_ok=True)
    stem = directory / f"{name}__fold{fold}"
    model_path = stem.with_suffix(".joblib")
    temporary = stem.with_suffix(".joblib.tmp")
    joblib.dump(model, temporary)
    temporary.replace(model_path)
    pred_path = stem.with_suffix(".npy")
    with pred_path.with_suffix(".npy.tmp").open("wb") as stream:
        np.save(stream, prediction, allow_pickle=False)
    pred_path.with_suffix(".npy.tmp").replace(pred_path)
    save_json(
        stem.with_suffix(".json"),
        {
            **details,
            "model_sha256": sha256_file(model_path),
            "prediction_sha256": sha256_file(pred_path),
            "seal_sha256": sha256_file(output / "seal.json"),
            "name": name,
            "fold": fold,
        },
    )


def part(output, name, fold):
    stem = output / "models" / f"{name}__fold{fold}"
    path = stem.with_suffix(".json")
    if not path.exists():
        return None
    meta = read_json(path)
    require(
        meta["seal_sha256"] == sha256_file(output / "seal.json"), "Checkpoint de outra preparação."
    )
    require(meta["name"] == name and meta["fold"] == fold, "Identidade do checkpoint diverge.")
    for suffix, key in ((".joblib", "model_sha256"), (".npy", "prediction_sha256")):
        require(sha256_file(stem.with_suffix(suffix)) == meta[key], "Checkpoint alterado.")
    return meta


def benchmark(output, threads):
    seal, frame, plan = load(output)
    require(not (output / "benchmark.json").exists(), "Benchmark já salvo; consulte --status.")
    outer = np.asarray(plan["outer"])
    pool = frame.filter(pl.Series(outer != 0))
    # Lote determinístico com grupos inteiros, sem estratificação pela resposta.
    chosen, n = [], 0
    for group, count in pool.group_by("analysis_group").len().sort("analysis_group").iter_rows():
        if n >= 3000:
            break
        chosen.append(group)
        n += count
    sample = pool.filter(pl.col("analysis_group").is_in(chosen))
    rows = []
    for block in BLOCKS:
        columns = seal["features"]["baseline"] + (
            seal["features"]["lfm"] if block == "traditional" else []
        )
        x, y = input_matrix(sample, columns), sample[TARGET].to_numpy()
        for family in FAMILIES:
            params = candidates(family, block)[0]
            model = factory(columns, seal["features"]["lfm"], family, params)
            with threadpool_limits(limits=threads):
                seconds, logs = fit_checked(model, x, y)
                start = time.perf_counter()
                _, prediction_logs = predict_checked(model, x[: min(len(x), 100)])
                logs.extend(prediction_logs)
                predict_seconds = time.perf_counter() - start
            rows.append(
                {
                    "block": block,
                    "family": family,
                    "n": len(y),
                    "seconds": seconds,
                    "predict_100_seconds": predict_seconds,
                    "params": params,
                    "warnings": logs,
                }
            )
            print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
    check_seal(output)
    save_json(
        output / "benchmark.json",
        {
            "rows": rows,
            "threads": threads,
            "purpose": "technical_only_no_metric_selection",
            "training_fits_planned": 530,
        },
    )


def run(output, threads):
    seal, frame, plan = load(output)
    require((output / "benchmark.json").exists(), "Execute --benchmark antes de --run.")
    outer = np.asarray(plan["outer"])
    y = frame[TARGET].to_numpy()
    started = time.perf_counter()
    for block in BLOCKS:
        columns = seal["features"]["baseline"] + (
            seal["features"]["lfm"] if block == "traditional" else []
        )
        x = input_matrix(frame, columns)
        for fold in range(5):
            train, valid = np.flatnonzero(outer != fold), np.flatnonzero(outer == fold)
            families = FAMILIES + (["dummy_mean", "dummy_median"] if block == "baseline" else [])
            for family in families:
                name = f"{family}__{block}"
                if part(output, name, fold) is not None:
                    continue
                save_json(
                    output / "progress.json",
                    {
                        "stage": "training",
                        "model": name,
                        "fold": fold,
                        "updated_at": utc_now(),
                        "threads": threads,
                    },
                )
                print(
                    f"Ajustando {name}, fold {fold + 1}/5; checkpoint após este ajuste externo.",
                    flush=True,
                )
                start = time.perf_counter()
                with threadpool_limits(limits=threads):
                    if family.startswith("dummy_"):
                        model = DummyRegressor(strategy=family.removeprefix("dummy_"))
                        best, search = {"params": {}, "mean_mae": None}, []
                    else:
                        best, search = tune(
                            x,
                            y,
                            columns,
                            seal["features"]["lfm"],
                            family,
                            block,
                            plan["inner"][str(fold)],
                        )
                        model = factory(columns, seal["features"]["lfm"], family, best["params"])
                    seconds, logs = fit_checked(model, x[train], y[train])
                    prediction, prediction_logs = predict_checked(model, x[valid])
                    logs.extend(prediction_logs)
                require(np.isfinite(prediction).all(), "Previsões externas não finitas.")
                save_part(
                    output,
                    name,
                    fold,
                    model,
                    prediction,
                    {
                        "columns": columns,
                        "params": best["params"],
                        "inner_mae": best["mean_mae"],
                        "search": search,
                        "fit_seconds": seconds,
                        "total_seconds": time.perf_counter() - start,
                        "warnings": logs,
                        "effective_estimator_params": model["model"].get_params()
                        if isinstance(model, Pipeline)
                        else model.get_params(),
                        "n_train": len(train),
                        "n_valid": len(valid),
                    },
                )
    check_seal(output)
    collect(output, reproduce=True, threads=threads)
    save_json(
        output / "progress.json",
        {
            "stage": "complete",
            "seconds_this_invocation": time.perf_counter() - started,
            "updated_at": utc_now(),
            "threads": threads,
        },
    )


def paired_interval(y, baseline, traditional, groups, repetitions=1000):
    """Bootstrap de componentes, pareado, condicionado às previsões OOF já ajustadas."""
    _, inverse = np.unique(groups, return_inverse=True)
    n = np.bincount(inverse)
    eb, et = np.abs(y - baseline), np.abs(y - traditional)
    arrays = [
        np.bincount(inverse, weights=v)
        for v in (et - eb, eb**2, et**2, (et > 20).astype(float) - (eb > 20))
    ]
    rng = np.random.default_rng(SEED)
    deltas = []
    for _ in range(repetitions):
        selected = rng.integers(0, len(n), len(n))
        total = n[selected].sum()
        a, b, c, d = [v[selected].sum() / total for v in arrays]
        deltas.append([a, np.sqrt(c) - np.sqrt(b), d])
    bounds = np.quantile(deltas, [0.025, 0.975], axis=0)
    return {
        f"{name}_{edge}": float(bounds[i, j])
        for j, name in enumerate(("delta_mae", "delta_rmse", "delta_prop_gt20"))
        for i, edge in enumerate(("lo", "hi"))
    }


def diagnostics(frame, predictions, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory = output / "diagnostics"
    directory.mkdir(exist_ok=True)
    y = frame[TARGET].to_numpy()
    calibration, residual_rows = [], []
    for name, pred in predictions.items():
        if name.startswith("dummy"):
            continue
        residual = y - pred
        fig, axes = plt.subplots(1, 3, figsize=(13, 4))
        axes[0].hexbin(pred, residual, gridsize=35, mincnt=1)
        axes[0].axhline(0, color="black", linewidth=1)
        axes[0].set(xlabel="Previsão OOF bruta", ylabel="Observado − previsto")
        stats.probplot(residual, dist="norm", plot=axes[1])
        axes[1].set_title("QQ dos resíduos OOF")
        axes[2].hexbin(pred, np.sqrt(np.abs(residual)), gridsize=35, mincnt=1)
        axes[2].set(xlabel="Previsão OOF", ylabel="Raiz do erro absoluto")
        fig.suptitle(name)
        fig.tight_layout()
        fig.savefig(directory / f"{name}.png", dpi=130)
        plt.close(fig)
        quantiles = np.unique(np.quantile(pred, np.linspace(0, 1, 11)))
        for i, (lo, hi) in enumerate(zip(quantiles[:-1], quantiles[1:], strict=True)):
            mask = (pred >= lo) & ((pred <= hi) if i == len(quantiles) - 2 else (pred < hi))
            if mask.any():
                calibration.append(
                    {
                        "model": name,
                        "bin": i,
                        "n": int(mask.sum()),
                        "mean_prediction": float(pred[mask].mean()),
                        "mean_observed": float(y[mask].mean()),
                        "mean_residual": float(residual[mask].mean()),
                    }
                )
        for variable in ("year", "genre"):
            values = frame[variable].cast(pl.String).fill_null("__MISSING__").to_numpy()
            for category in np.unique(values):
                mask = values == category
                residual_rows.append(
                    {
                        "model": name,
                        "variable": variable,
                        "category": category,
                        "n": int(mask.sum()),
                        "small_cell": bool(mask.sum() < 30),
                        "mae": float(np.abs(residual[mask]).mean()),
                        "mean_residual": float(residual[mask].mean()),
                    }
                )
    pl.DataFrame(calibration).write_csv(directory / "calibration_descriptive.csv")
    pl.DataFrame(residual_rows).write_csv(directory / "residual_by_year_genre.csv")


def collect(output, reproduce, threads):
    seal, frame, plan = load(output)
    outer = np.asarray(plan["outer"])
    y = frame[TARGET].to_numpy()
    predictions, metadata = {}, []
    max_difference = 0.0
    for block in BLOCKS:
        columns = seal["features"]["baseline"] + (
            seal["features"]["lfm"] if block == "traditional" else []
        )
        x = input_matrix(frame, columns)
        selected = np.empty(len(y))
        selections = []
        for family in FAMILIES + (["dummy_mean", "dummy_median"] if block == "baseline" else []):
            name = f"{family}__{block}"
            pred = np.empty(len(y))
            for fold in range(5):
                meta = part(output, name, fold)
                require(
                    meta is not None, f"Checkpoint faltando: {name}/{fold}. Use --run para retomar."
                )
                require(meta["columns"] == columns, "Inputs divergentes no checkpoint.")
                mask = outer == fold
                stem = output / "models" / f"{name}__fold{fold}"
                saved = np.load(stem.with_suffix(".npy"), allow_pickle=False)
                require(
                    saved.shape == (int(mask.sum()),) and np.isfinite(saved).all(),
                    "Vetor de previsões inválido.",
                )
                if reproduce:
                    with threadpool_limits(limits=threads):
                        recalculated, _ = predict_checked(
                            joblib.load(stem.with_suffix(".joblib")), x[mask]
                        )
                    difference = float(np.max(np.abs(saved - recalculated)))
                    max_difference = max(max_difference, difference)
                    require(
                        np.allclose(saved, recalculated, atol=1e-8, rtol=1e-10),
                        "Previsões não reproduzidas.",
                    )
                pred[mask] = saved
                metadata.append(
                    {
                        "model": name,
                        "fold": fold,
                        "params": json.dumps(meta["params"]),
                        "inner_mae": meta["inner_mae"],
                        "n_train": meta["n_train"],
                        "seconds": meta["total_seconds"],
                    }
                )
            predictions[name] = pred
        # Avalia também a ESCOLHA da família, sem escolhê-la pelo próprio OOF externo.
        for fold in range(5):
            family = min(FAMILIES, key=lambda f: part(output, f"{f}__{block}", fold)["inner_mae"])
            selected[outer == fold] = predictions[f"{family}__{block}"][outer == fold]
            selections.append({"fold": fold, "family": family})
        predictions[f"selected_inner__{block}"] = selected
        save_json(output / f"selected_families_{block}.json", selections)
    oof = frame.select("track_id", "composition_key", "analysis_group", TARGET).with_columns(
        pl.Series("outer_fold", outer), *[pl.Series(k, v) for k, v in predictions.items()]
    )
    if (output / "oof.parquet").exists():
        require(
            oof.equals(pl.read_parquet(output / "oof.parquet")),
            "OOF salvo diverge da reconstrução.",
        )
    else:
        oof.write_parquet(output / "oof.parquet")
    rows = []
    for name, pred in predictions.items():
        scopes = [("global", "all", np.ones(len(y), bool))]
        scopes += [("fold", str(f), outer == f) for f in range(5)]
        scopes += [
            (
                "target_band",
                f"[{a},{a + 10}{']' if a == 90 else ')'}",
                (y >= a) & ((y <= 100) if a == 90 else (y < a + 10)),
            )
            for a in range(0, 100, 10)
        ]
        for scope, level, mask in scopes:
            measured = metrics(y[mask], pred[mask])
            if scope == "target_band":
                measured["r2"] = None
            rows.append(
                {
                    "model": name,
                    "scope": scope,
                    "level": level,
                    "small_cell": bool(mask.sum() < 30),
                    **measured,
                    "prediction_min": float(pred[mask].min()) if mask.any() else None,
                    "prediction_max": float(pred[mask].max()) if mask.any() else None,
                }
            )
    pl.DataFrame(rows, infer_schema_length=None).write_csv(output / "metrics.csv")
    pl.DataFrame(metadata).write_csv(output / "selected_parameters.csv")
    comparisons = []
    for family in [*FAMILIES, "selected_inner"]:
        baseline, traditional = (
            predictions[f"{family}__baseline"],
            predictions[f"{family}__traditional"],
        )
        mb, mt = metrics(y, baseline), metrics(y, traditional)
        comparisons.append(
            {
                "family": family,
                "n": len(y),
                "delta_mae": mt["mae"] - mb["mae"],
                "delta_rmse": mt["rmse"] - mb["rmse"],
                "delta_r2": mt["r2"] - mb["r2"] if mb["r2"] is not None else None,
                "delta_p95": mt["p95_abs_error"] - mb["p95_abs_error"],
                "delta_n_gt20": mt["n_abs_gt20"] - mb["n_abs_gt20"],
                "folds_better_mae": sum(
                    np.abs(y[outer == f] - traditional[outer == f]).mean()
                    < np.abs(y[outer == f] - baseline[outer == f]).mean()
                    for f in range(5)
                ),
                **paired_interval(y, baseline, traditional, frame["analysis_group"].to_numpy()),
            }
        )
    pl.DataFrame(comparisons).write_csv(output / "paired_comparisons.csv")
    diagnostics(frame, predictions, output)
    global_rows = [r for r in rows if r["scope"] == "global"]
    lines = [
        "# Regressões na coorte aceita — exploração",
        "",
        "Nenhum alvo do holdout carregado. Comparações válidas somente nesta mesma coorte e nestes folds.",
        "",
        "| Modelo | n | MAE | RMSE | R² | P95 | Erros >20 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in global_rows:
        r2 = f"{r['r2']:.4f}" if r["r2"] is not None else "indefinido"
        lines.append(
            f"| {r['model']} | {r['n']} | {r['mae']:.4f} | {r['rmse']:.4f} | {r2} | {r['p95_abs_error']:.4f} | {r['n_abs_gt20']} |"
        )
    lines.extend(
        [
            "",
            "Leia paired_comparisons.csv: deltas Tradicional − Baseline. Negativos favorecem o Tradicional para erros; positivos para R². IC percentil 95%, 1.000 reamostragens pareadas por componente, condicionado aos modelos OOF; não inclui todo o processo de treino/seleção nem é confirmação independente. Não tratar cinco folds como cinco experimentos independentes.",
            "",
            "selected_inner avalia a escolha de família dentro do treino: a família pode diferir entre os blocos. Para isolar a contribuição das features, priorize comparações dentro da MESMA família. Não declare vencedor pelo menor MAE sem examinar RMSE, P95, erros >20 e estabilidade.",
            "",
            "diagnostics contém resíduos versus ajustados OOF, QQ e escala-localização, além de calibração descritiva e erros por ano/gênero. Não houve calibração, clipping, exclusão por erro, PCA, coleta ou embeddings. Este comando salva modelos de folds; não substitui o demonstrador nem ajusta modelo final em todo o desenvolvimento.",
        ]
    )
    (output / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    check_seal(output)
    result = {
        "stage": "verified",
        "n": frame.height,
        "saved_fold_models": 50,
        "max_prediction_difference": max_difference,
        "atol": 1e-8,
        "rtol": 1e-10,
        "inputs_unchanged": True,
        "holdout_targets_loaded": False,
        "updated_at": utc_now(),
    }
    save_json(output / "verification.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    for name in ("benchmark", "run", "verify", "status"):
        actions.add_argument(f"--{name}", action="store_true")
    parser.add_argument("--workspace", type=Path, default=DEFAULT)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    output = workspace(args.workspace)
    require(1 <= args.threads <= 16, "Use de 1 a 16 threads.")
    try:
        if args.status:
            value = {
                "workspace": str(output),
                "checkpoints_completed": len(list((output / "models").glob("*.json"))),
            }
            for name in ("summary", "progress", "benchmark", "verification"):
                if (output / f"{name}.json").exists():
                    value[name] = read_json(output / f"{name}.json")
            print(json.dumps(value, ensure_ascii=False, indent=2))
            return 0
        require((output / "seal.json").exists(), "Execute 09 --prepare primeiro.")
        with exclusive(output):
            if args.benchmark:
                benchmark(output, args.threads)
            elif args.run:
                run(output, args.threads)
            else:
                collect(output, reproduce=True, threads=args.threads)
        return 0
    except KeyboardInterrupt:
        save_json(
            output / "progress.json",
            {"stage": "interrupted", "updated_at": utc_now(), "resume": "--run"},
        )
        print("Interrompido. Checkpoints concluídos preservados; retome com --run.")
        return 2
    except (ValueError, OSError, KeyError) as exc:
        print(f"Interrompido: {exc}", flush=True)
        return 1
