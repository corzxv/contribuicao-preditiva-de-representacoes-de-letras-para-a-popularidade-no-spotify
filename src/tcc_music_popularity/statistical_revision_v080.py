"""Bounded, development-only exploratory nested evaluation (V0.8).

No old artifact is written; the three permitted tables are an explicit allowlist.
Run as a module: prepare, benchmark, run, verify. No network or holdout reader.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import platform
import subprocess
import time
import warnings
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import polars as pl
import sklearn
from joblib import Parallel, delayed, parallel_config
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler
from threadpoolctl import threadpool_limits

from tcc_music_popularity.modeling_pilot_v030 import FeatureBlocks
from tcc_music_popularity.modeling_recalibration_v031 import (
    Representation,
    _components,
    build_representation_transformer,
)

ROOT = Path(__file__).resolve().parents[2]
OLD = Path("data/derived/private_final_development_v0_5")
PRIVATE = Path("data/derived/private_statistical_revision_v0_8")
PROTOCOL = Path("reports/protocolo_revisao_v0_8.md")
MANIFEST = Path("reports/final_model_manifest_v0_5.json")
OLD_SUMMARY = Path("reports/run_summary_final_development_v0_5.json")
CODE = Path("src/tcc_music_popularity/statistical_revision_v080.py")
REPORT_CODE = Path("src/tcc_music_popularity/statistical_revision_report_v080.py")
PUBLIC = {
    PROTOCOL,
    Path("reports/revisao_estatistica_v0_8.md"),
    Path("reports/revisao_estatistica_metricas_v0_8.csv"),
    Path("reports/revisao_estatistica_comparacoes_v0_8.csv"),
    Path("reports/run_summary_revisao_v0_8.json"),
}
TABLES = frozenset(
    OLD / name
    for name in (
        "development_matrix.parquet",
        "fold_assignments.parquet",
        "oof_predictions.parquet",
    )
)
BLOCKS = ("baseline", "traditional", "deep", "combined")
FAMILIES = ("spline_en", "hist_gb")
FLAGS = (
    "remaster",
    "remix",
    "live",
    "acoustic",
    "radio_edit",
    "mono_stereo",
    "instrumental",
    "demo",
)
TARGET = "spotify_popularity"
SEED = 20261013
WORKERS = 4
REFERENCE_NAMES = tuple(f"elastic_net__{b}" for b in BLOCKS) + ("dummy__baseline",)


def ensure(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.now(UTC).isoformat()


def digest(path):
    with (ROOT / path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def output_path(path):
    resolved = (ROOT / path).resolve()
    relative = resolved.relative_to(ROOT)
    ensure(
        relative in PUBLIC or relative.is_relative_to(PRIVATE),
        f"Escrita fora das saídas V0.8: {relative}",
    )
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_json(path, value):
    destination = output_path(path)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    temporary.replace(destination)


def read_development_table(path, *, columns=None):
    relative = (ROOT / path).resolve().relative_to(ROOT)
    ensure(relative in TABLES, f"Leitura tabular não autorizada: {relative}")
    return pl.read_parquet(ROOT / relative, columns=columns)


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True)
    return result.stdout.decode("utf-8")


def grids(family):
    if family == "spline_en":
        return [
            {"n_knots": k, "alpha": a, "l1_ratio": r}
            for k, a, r in itertools.product((3, 5), (0.003, 0.03, 0.3), (0.8, 0.95))
        ]
    ensure(family == "hist_gb", "Família desconhecida")
    return [
        {"loss": loss, "max_leaf_nodes": leaves, "l2_regularization": penalty}
        for loss, leaves, penalty in itertools.product(
            ("squared_error", "absolute_error"), (15, 31), (1, 10)
        )
    ]


def model_factory(family, params):
    if family == "spline_en":
        return ElasticNet(
            alpha=params["alpha"],
            l1_ratio=params["l1_ratio"],
            fit_intercept=True,
            max_iter=50000,
            tol=0.001,
            selection="cyclic",
            precompute=True,
            random_state=SEED,
        )
    ensure(family == "hist_gb", "Família desconhecida")
    return HistGradientBoostingRegressor(
        **params,
        learning_rate=0.05,
        max_iter=200,
        min_samples_leaf=20,
        early_stopping=False,
        random_state=SEED,
        categorical_features=None,
    )


def transformer_factory(blocks, block, n_knots=None):
    transformer = build_representation_transformer(
        Representation(block, "raw" if block == "baseline" else "pca90"), blocks
    )
    if n_knots is not None:
        preprocess = transformer.named_steps["preprocess"]
        changed = []
        for name, step, columns in preprocess.transformers:
            changed.append((name, step, [c for c in columns if c != "year"]))
        year = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                (
                    "spline",
                    SplineTransformer(
                        n_knots=n_knots,
                        degree=3,
                        knots="uniform",
                        include_bias=False,
                        extrapolation="constant",
                    ),
                ),
                ("scaler", StandardScaler()),
            ]
        )
        preprocess.transformers = [*changed, ("year_spline", year, ["year"])]
    return transformer


def validate_alignment(dev, folds, refs, expected=7648):
    for name, frame in (("dev", dev), ("folds", folds), ("references", refs)):
        ensure(frame.height == expected, f"Número de linhas diferente: {name}")
        ensure(frame["composition_key"].null_count() == 0, "Composição ausente")
        ensure(frame["composition_key"].n_unique() == expected, f"Composição duplicada: {name}")
        ensure(frame["artist_group_id"].null_count() == 0, "Grupo ausente")
    # Explicit identity equality after deterministic joins, not a positional assumption.
    for frame in (folds, refs):
        for key in ("composition_key", "artist_group_id"):
            ensure(dev[key].equals(frame[key]), f"Desalinhamento: {key}")
    for key in ("track_id", TARGET):
        ensure(dev[key].equals(refs[key]), f"Desalinhamento referência: {key}")
    ensure(dev["track_id"].n_unique() == expected, "Representante duplicado")
    ensure(folds["outer_fold"].equals(refs["outer_fold"]), "Folds OOF divergentes")
    ensure(np.isfinite(dev[TARGET].to_numpy()).all(), "Alvo não finito")
    ensure(
        dev["split"].unique().to_list() == ["development_train"], "Coorte fora do desenvolvimento"
    )
    ensure(dev["year"].null_count() == 0, "Year passou a ter ausentes")


def validate_folds(dev, folds):
    outer = folds["outer_fold"].to_numpy()
    ensure(set(outer.tolist()) == set(range(5)), "Cinco folds externos exigidos")
    audit = []
    for fold in range(5):
        inner = folds[f"inner_outer_{fold}"].to_numpy()
        train, valid = np.flatnonzero(outer != fold), np.flatnonzero(outer == fold)
        ensure(np.all(inner[valid] == -1), "Validação externa presente no treino interno")
        ensure(set(inner[train].tolist()) == {0, 1, 2}, "Três folds internos exigidos")
        partitions = [("outer", train, valid)]
        partitions += [
            (f"inner_{i}", np.flatnonzero((inner >= 0) & (inner != i)), np.flatnonzero(inner == i))
            for i in range(3)
        ]
        for scope, ti, vi in partitions:
            ensure(len(set(ti) & set(vi)) == 0, "Sobreposição de linhas")
            for key in ("artist_group_id", "composition_key"):
                values = dev[key].to_numpy()
                ensure(not set(values[ti]) & set(values[vi]), f"Sobreposição de {key}")
            audit.append(
                {
                    "outer_fold": fold,
                    "scope": scope,
                    "train_n": len(ti),
                    "valid_n": len(vi),
                    "artist_overlap": 0,
                    "composition_overlap": 0,
                }
            )
    return audit


def load_inputs():
    manifest = read_json(MANIFEST)
    allowed = manifest["allowed_features"]
    blocks = FeatureBlocks(
        tuple(allowed["baseline"]), tuple(allowed["lfm"]), tuple(allowed["minilm"]), {}
    )
    ensure(
        tuple(map(len, (blocks.baseline, blocks.traditional, blocks.embeddings))) == (23, 196, 384),
        "Lista V0.5 divergente",
    )
    for block in BLOCKS:
        spec = next(m for m in manifest["models"] if m["model"] == f"elastic_net__{block}")
        ensure(blocks.columns(block) == spec["input_columns"], "Ordem de inputs mudou")
    ensure(TARGET not in blocks.columns("combined"), "Alvo em X")
    keys = ["composition_key", "track_id", "artist_group_id", "spotify_row_id", "split", TARGET]
    dev = read_development_table(
        OLD / "development_matrix.parquet", columns=keys + blocks.columns("combined")
    )
    folds_original = read_development_table(OLD / "fold_assignments.parquet")
    reference_columns = ["composition_key", "track_id", "artist_group_id", TARGET, "outer_fold"]
    reference_columns += [f"prediction__{model}" for model in REFERENCE_NAMES]
    refs_original = read_development_table(
        OLD / "oof_predictions.parquet", columns=reference_columns
    )
    ensure(
        folds_original.height == dev.height and refs_original.height == dev.height,
        "Linhas extras nas referências",
    )
    keys_frame = dev.select("composition_key")
    folds = keys_frame.join(
        folds_original, on="composition_key", how="left", validate="1:1", maintain_order="left"
    )
    refs = keys_frame.join(
        refs_original, on="composition_key", how="left", validate="1:1", maintain_order="left"
    )
    validate_alignment(dev, folds, refs)
    audit = validate_folds(dev, folds)
    return dev, folds, refs, blocks, audit


def metrics(y, prediction):
    y, prediction = np.asarray(y, float), np.asarray(prediction, float)
    ensure(y.shape == prediction.shape, "Forma da previsão divergente")
    ensure(np.isfinite(y).all() and np.isfinite(prediction).all(), "Métrica com valor não finito")
    names = (
        "mae",
        "rmse",
        "r2",
        "median_abs_error",
        "p90_abs_error",
        "p95_abs_error",
        "prop_abs_le5",
        "prop_abs_le10",
        "prop_abs_le20",
        "prop_abs_gt20",
    )
    if not len(y):
        return {
            "n": 0,
            **dict.fromkeys(names),
            "n_abs_gt20": 0,
            "n_prediction_lt0": 0,
            "n_prediction_gt100": 0,
        }
    error = np.abs(y - prediction)
    denominator = np.sum((y - y.mean()) ** 2)
    return {
        "n": len(y),
        "mae": float(error.mean()),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "r2": float(1 - np.sum(error**2) / denominator) if denominator > 0 else None,
        "median_abs_error": float(np.quantile(error, 0.5)),
        "p90_abs_error": float(np.quantile(error, 0.9)),
        "p95_abs_error": float(np.quantile(error, 0.95)),
        **{f"prop_abs_le{v}": float(np.mean(error <= v)) for v in (5, 10, 20)},
        "prop_abs_gt20": float(np.mean(error > 20)),
        "n_abs_gt20": int(np.sum(error > 20)),
        "n_prediction_lt0": int(np.sum(prediction < 0)),
        "n_prediction_gt100": int(np.sum(prediction > 100)),
    }


def reproduce_references(dev, folds, refs):
    old = read_json(OLD_SUMMARY)
    result = []
    for name in REFERENCE_NAMES:
        prediction = refs[f"prediction__{name}"].to_numpy()
        for fold in [None, *range(5)]:
            mask = (
                np.ones(dev.height, bool)
                if fold is None
                else folds["outer_fold"].to_numpy() == fold
            )
            measured = metrics(dev[TARGET].to_numpy()[mask], prediction[mask])
            saved = next(
                row
                for row in old["metrics"]
                if row["model"] == name
                and row["scope"] == ("overall_oof" if fold is None else "fold")
                and (fold is None or row["fold"] == fold)
            )
            for metric in ("mae", "rmse", "r2"):
                ensure(
                    np.isclose(measured[metric], saved[metric], atol=1e-10, rtol=0),
                    f"Referência não reproduzida: {name}/{fold}/{metric}",
                )
            result.append(
                {
                    "model": name,
                    "fold": fold,
                    "maximum_absolute_difference": max(
                        abs(measured[m] - saved[m]) for m in ("mae", "rmse", "r2")
                    ),
                }
            )
    return result


def preservation_snapshot():
    excluded = PUBLIC | {CODE, REPORT_CODE, Path("tests/test_statistical_revision_v080.py")}
    known = git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0")
    paths = {Path(p) for p in known if p}
    paths.update(p.relative_to(ROOT) for p in (ROOT / "reports").rglob("*") if p.is_file())
    paths.update(p.relative_to(ROOT) for p in (ROOT / OLD / "models").glob("*.joblib"))
    paths.update(TABLES)
    hashes = {p.as_posix(): digest(p) for p in sorted(paths - excluded) if (ROOT / p).is_file()}
    # Metadata only: never open any other data table, holdout, cache, or lyric file.
    metadata = {}
    for path in (ROOT / "data").rglob("*"):
        if path.is_file() and not path.is_relative_to(ROOT / PRIVATE):
            stat = path.stat()
            metadata[path.relative_to(ROOT).as_posix()] = [stat.st_size, stat.st_mtime_ns]
    return {
        "created_at": now(),
        "sha256": hashes,
        "data_metadata": metadata,
        "head": git("rev-parse", "HEAD").strip(),
        "stage": git("diff", "--cached", "--binary"),
        "status_before": git("status", "--short"),
    }


def verify_preservation():
    before = read_json(PRIVATE / "preservation_before.json")
    changed_hashes = [
        p for p, value in before["sha256"].items() if not (ROOT / p).is_file() or digest(p) != value
    ]
    changed_metadata = []
    for p, expected in before["data_metadata"].items():
        path = ROOT / p
        if not path.is_file() or [path.stat().st_size, path.stat().st_mtime_ns] != expected:
            changed_metadata.append(p)
    ensure(not changed_hashes and not changed_metadata, "Artefatos anteriores modificados")
    ensure(git("rev-parse", "HEAD").strip() == before["head"], "HEAD mudou")
    ensure(git("diff", "--cached", "--binary") == before["stage"], "Stage mudou")
    tracked = [p for p in git("ls-files", "-z").split("\0") if p]
    forbidden = [
        p
        for p in tracked
        if (p.startswith("data/") and not p.endswith(".gitkeep"))
        or p.endswith((".parquet", ".joblib", ".npz", ".pkl"))
    ]
    ensure(not forbidden, "Dados/modelos privados rastreados")
    ignored = git("check-ignore", (PRIVATE / "oof_predictions.parquet").as_posix()).strip()
    ensure(bool(ignored), "Saídas privadas não ignoradas")
    return {
        "old_hashes_verified": len(before["sha256"]),
        "old_data_metadata_verified": len(before["data_metadata"]),
        "changed_hashes": changed_hashes,
        "changed_metadata": changed_metadata,
        "head_unchanged": True,
        "stage_unchanged": True,
        "tracked_private_files": forbidden,
        "private_output_ignored": True,
        "holdout_or_other_data_deserialized": False,
        "scope_note": "SHA-256: arquivos públicos/pessoais, modelos V0.5 e três entradas; demais dados: tamanho/mtime_ns, sem abrir holdout/letras.",
    }


def prepare():
    ensure(not (ROOT / PRIVATE / "seal.json").exists(), "Selo V0.8 já existe; não sobrescrever")
    ensure((ROOT / PROTOCOL).is_file(), "Protocolo obrigatório antes de ajustar")
    dev, folds, refs, blocks, audit = load_inputs()
    reference_check = reproduce_references(dev, folds, refs)
    manifest, old_summary = read_json(MANIFEST), read_json(OLD_SUMMARY)
    expected = {
        OLD / "development_matrix.parquet": manifest["training_matrix_sha256"],
        OLD / "fold_assignments.parquet": manifest["fold_assignments_sha256"],
        OLD / "oof_predictions.parquet": old_summary["oof_file_sha256"],
    }
    for path, sha in expected.items():
        ensure(digest(path) == sha, f"Hash da entrada V0.5 divergente: {path}")
    preserved = preservation_snapshot()
    write_json(PRIVATE / "preservation_before.json", preserved)
    code_paths = [
        CODE,
        REPORT_CODE,
        Path("src/tcc_music_popularity/modeling_recalibration_v031.py"),
        Path("src/tcc_music_popularity/modeling_pilot_v030.py"),
    ]
    seal = {
        "created_before_fitting_at": now(),
        "status": "sealed_before_technical_test",
        "protocol_sha256": digest(PROTOCOL),
        "inputs_sha256": {
            p.as_posix(): digest(p) for p in [*sorted(TABLES), MANIFEST, OLD_SUMMARY]
        },
        "code_sha256": {p.as_posix(): digest(p) for p in code_paths},
        "preservation_snapshot_sha256": digest(PRIVATE / "preservation_before.json"),
        "rows": dev.height,
        "artists": dev["artist_group_id"].n_unique(),
        "fold_audit": audit,
        "reference_reproduction": reference_check,
        "features": {b: len(blocks.columns(b)) for b in BLOCKS},
        "grids": {f: grids(f) for f in FAMILIES},
        "seed": SEED,
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "polars": pl.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "workers": WORKERS,
        "numerical_threads_per_worker": 1,
        "estimator_defaults": {f: model_factory(f, grids(f)[0]).get_params() for f in FAMILIES},
        "holdout_loaded": False,
        "new_targets_loaded": False,
    }
    seal["seal_id"] = fingerprint(seal)
    write_json(PRIVATE / "seal.json", seal)
    print(
        json.dumps(
            {
                "status": seal["status"],
                "protocol_sha256": seal["protocol_sha256"],
                "rows": seal["rows"],
                "reference_checks": len(reference_check),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return seal


def verify_seal():
    seal = read_json(PRIVATE / "seal.json")
    ensure(digest(PROTOCOL) == seal["protocol_sha256"], "Protocolo mudou após selo")
    for p, sha in {**seal["inputs_sha256"], **seal["code_sha256"]}.items():
        ensure(digest(p) == sha, f"Entrada/código mudou após selo: {p}")
    ensure(
        digest(PRIVATE / "preservation_before.json") == seal["preservation_snapshot_sha256"],
        "Snapshot mudou",
    )
    ensure(
        fingerprint({k: v for k, v in seal.items() if k != "seal_id"}) == seal["seal_id"],
        "Selo inconsistente",
    )
    return seal


def warn_records(caught, context, max_iter=None):
    return [
        {
            "context": context,
            "category": w.category.__name__,
            "message": str(w.message),
            "max_iter": max_iter,
        }
        for w in caught
    ]


class FitFailure(RuntimeError):
    def __init__(self, message, events):
        super().__init__(message)
        self.events = events


def fit_model(family, params, x, y, context):
    started = time.perf_counter()
    events = []
    limits = (50000, 200000, 500000) if family == "spline_en" else (200,)
    model = model_factory(family, params)
    for attempt, limit in enumerate(limits, 1):
        model.set_params(max_iter=limit)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                model.fit(x, y)
            except Exception as exc:
                events.extend(warn_records(caught, context, limit))
                raise FitFailure(f"{type(exc).__name__}: {exc}", events) from exc
        events.extend(warn_records(caught, context, limit))
        if not any(issubclass(w.category, ConvergenceWarning) for w in caught):
            return model, {
                "warnings": events,
                "fit_attempts": attempt,
                "fit_seconds": time.perf_counter() - started,
            }
    raise FitFailure("Não convergiu dentro dos limites autorizados", events)


def prepare_partition(dev, blocks, block, train, valid, n_knots, context):
    columns = blocks.columns(block)
    ensure(TARGET not in columns, "Alvo presente no input")
    ensure(not set(train) & set(valid), "Cache com linhas sobrepostas")
    xtrain = dev[train.tolist()].select(columns)
    xvalid = dev[valid.tolist()].select(columns)
    transformer = transformer_factory(blocks, block, n_knots)
    started = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        xt = np.asarray(transformer.fit_transform(xtrain), dtype=np.float64)
        xv = np.asarray(transformer.transform(xvalid), dtype=np.float64)
    ensure(np.isfinite(xt).all() and np.isfinite(xv).all(), "Transformação não finita")
    named = transformer.named_steps["preprocess"].named_transformers_
    audit = {
        "context": context,
        "n_knots": n_knots,
        "train_indices": train.tolist(),
        "valid_indices": valid.tolist(),
        "train_index_sha256": fingerprint(train.tolist()),
        "valid_index_sha256": fingerprint(valid.tolist()),
        "input_columns": columns,
        "train_n": len(train),
        "valid_n": len(valid),
        "features_out": xt.shape[1],
        "pca_components": _components(transformer),
        "seconds": time.perf_counter() - started,
        "warnings": warn_records(caught, context),
        "target_in_input": False,
    }
    if n_knots is not None:
        spline = named["year_spline"].named_steps["spline"]
        knots = spline.bsplines_[0].t
        bounds = [float(knots[spline.degree]), float(knots[-spline.degree - 1])]
        expected = [float(xtrain["year"].min()), float(xtrain["year"].max())]
        ensure(bounds == expected, "Nós da spline não correspondem somente ao treino")
        audit["spline_bounds"] = bounds
    for name in ("traditional", "embedding"):
        if name in named:
            ensure(named[name].named_steps["pca"].n_samples_ == len(train), "PCA fora do treino")
    return {
        "transformer": transformer,
        "train": xt,
        "valid": xv,
        "ytrain": dev[TARGET].to_numpy()[train],
        "yvalid": dev[TARGET].to_numpy()[valid],
        "audit": audit,
    }


def evaluate_candidate(family, params, partitions, context):
    result = {
        "params": params,
        "fold_mae": [],
        "warnings": [],
        "fit_attempts": 0,
        "fit_seconds": 0.0,
        "prediction_seconds": 0.0,
        "failure": None,
    }
    for inner, part in enumerate(partitions):
        try:
            model, fitted = fit_model(
                family, params, part["train"], part["ytrain"], f"{context}/inner{inner}"
            )
            result["warnings"].extend(fitted["warnings"])
            result["fit_attempts"] += fitted["fit_attempts"]
            result["fit_seconds"] += fitted["fit_seconds"]
            start = time.perf_counter()
            prediction = model.predict(part["valid"])
            result["prediction_seconds"] += time.perf_counter() - start
            ensure(np.isfinite(prediction).all(), "Previsão interna não finita")
            result["fold_mae"].append(float(np.mean(np.abs(prediction - part["yvalid"]))))
        except Exception as exc:
            result["warnings"].extend(getattr(exc, "events", []))
            result["failure"] = {"inner_fold": inner, "error": str(exc), "type": type(exc).__name__}
            break
    result["mean_mae"] = float(np.mean(result["fold_mae"])) if result["failure"] is None else None
    return result


def choose_candidate(evaluated):
    eligible = [
        i
        for i, item in enumerate(evaluated)
        if item["failure"] is None and len(item["fold_mae"]) == 3 and np.isfinite(item["mean_mae"])
    ]
    ensure(bool(eligible), "Nenhuma configuração elegível; grade não será ampliada")
    return min(eligible, key=lambda i: (evaluated[i]["mean_mae"], i))


def benchmark():
    seal = verify_seal()
    ensure(not (ROOT / PRIVATE / "benchmark.json").exists(), "Teste técnico já existe; preservá-lo")
    dev, folds, _, blocks, _ = load_inputs()
    inner = folds["inner_outer_0"].to_numpy()
    train, valid = np.flatnonzero((inner >= 0) & (inner != 0)), np.flatnonzero(inner == 0)
    cases = [("spline_en", {"n_knots": 5, "alpha": 0.003, "l1_ratio": 0.8})]
    cases += [
        ("hist_gb", {"loss": loss, "max_leaf_nodes": 31, "l2_regularization": 1})
        for loss in ("squared_error", "absolute_error")
    ]
    records, prep_cache = [], {}
    with threadpool_limits(limits=1):
        for family, params in cases:
            knot = params.get("n_knots")
            if knot not in prep_cache:
                prep_cache[knot] = prepare_partition(
                    dev, blocks, "combined", train, valid, knot, f"benchmark/{family}"
                )
            part = prep_cache[knot]
            model, fitted = fit_model(
                family, params, part["train"], part["ytrain"], f"benchmark/{family}"
            )
            ensure(np.isfinite(model.predict(part["valid"])).all(), "Benchmark não finito")
            records.append(
                {
                    "family": family,
                    "params": params,
                    **fitted,
                    "train_n": len(train),
                    "valid_n": len(valid),
                    "features_out": part["train"].shape[1],
                    "preprocess_seconds": part["audit"]["seconds"],
                    "preprocess_warnings": part["audit"]["warnings"],
                }
            )
    sequential = 720 * records[0]["fit_seconds"] + 240 * sum(r["fit_seconds"] for r in records[1:])
    value = {
        "created_at": now(),
        "seal_id": seal["seal_id"],
        "cases": records,
        "grid_changed": False,
        "performance_metrics_used": False,
        "rough_sequential_inner_fit_seconds": sequential,
        "rough_four_worker_inner_fit_seconds": sequential / WORKERS,
        "estimate_excludes": "preprocessamento, refits externos, overhead; bloco Combinado com árvores maiores é aproximação, não garantia",
    }
    write_json(PRIVATE / "benchmark.json", value)
    print(json.dumps(value, ensure_ascii=False), flush=True)
    return value


def part_paths(name, fold):
    stem = PRIVATE / "parts" / f"{name}__fold{fold}"
    return stem.with_suffix(".joblib"), stem.with_suffix(".json")


def fit_outer(dev, folds, blocks, seal, family, block, fold):
    name = f"{family}__{block}"
    model_path, meta_path = part_paths(name, fold)
    if (ROOT / meta_path).exists():
        meta = read_json(meta_path)
        ensure(
            meta["seal_id"] == seal["seal_id"] and digest(model_path) == meta["model_file_sha256"],
            "Checkpoint inválido",
        )
        print(f"REUTILIZADO {name} fold {fold}", flush=True)
        return meta
    ensure(not (ROOT / model_path).exists(), "Checkpoint incompleto; preservar para investigação")
    started = time.perf_counter()
    inner, outer = folds[f"inner_outer_{fold}"].to_numpy(), folds["outer_fold"].to_numpy()
    all_params = grids(family)
    cache = {}
    for knot in (3, 5) if family == "spline_en" else (None,):
        cache[knot] = []
        for i in range(3):
            ti, vi = np.flatnonzero((inner >= 0) & (inner != i)), np.flatnonzero(inner == i)
            cache[knot].append(
                prepare_partition(dev, blocks, block, ti, vi, knot, f"{name}/outer{fold}/inner{i}")
            )
    prep_seconds = time.perf_counter() - started
    tune_start = time.perf_counter()
    # Process isolation makes warnings.catch_warnings deterministic and thread-safe.
    with parallel_config(
        backend="loky",
        n_jobs=WORKERS,
        inner_max_num_threads=1,
        temp_folder=str(ROOT / PRIVATE / "parallel_tmp"),
    ):
        evaluated = Parallel(max_nbytes="1M")(
            delayed(evaluate_candidate)(
                family, params, cache[params.get("n_knots")], f"{name}/outer{fold}/config{index}"
            )
            for index, params in enumerate(all_params)
        )
    tuning_seconds = time.perf_counter() - tune_start
    # Persist ALL scores/failures/warnings before attempting selection or refit.
    write_json(
        PRIVATE / "tuning" / f"{name}__fold{fold}.json",
        {"seal_id": seal["seal_id"], "candidates": evaluated},
    )
    selected = choose_candidate(evaluated)
    params = all_params[selected]
    train, valid = np.flatnonzero(outer != fold), np.flatnonzero(outer == fold)
    part = prepare_partition(
        dev, blocks, block, train, valid, params.get("n_knots"), f"{name}/outer{fold}/refit"
    )
    model, fitted = fit_model(
        family, params, part["train"], part["ytrain"], f"{name}/outer{fold}/refit"
    )
    prediction_start = time.perf_counter()
    prediction = model.predict(part["valid"])
    prediction_seconds = time.perf_counter() - prediction_start
    ensure(prediction.shape == (len(valid),) and np.isfinite(prediction).all(), "OOF inválida")
    pipeline = Pipeline([("representation", part["transformer"]), ("model", model)])
    audit = [p["audit"] for parts in cache.values() for p in parts] + [part["audit"]]
    events = (
        [w for a in audit for w in a["warnings"]]
        + [w for c in evaluated for w in c["warnings"]]
        + fitted["warnings"]
    )
    payload = {
        "pipeline": pipeline,
        "prediction": prediction,
        "train_indices": train,
        "valid_indices": valid,
        "input_columns": blocks.columns(block),
        "audit": audit,
        "seal_id": seal["seal_id"],
        "params": params,
    }
    joblib.dump(payload, output_path(model_path), compress=3)
    meta = {
        "model": name,
        "family": family,
        "block": block,
        "outer_fold": fold,
        "seal_id": seal["seal_id"],
        "selected_params": params,
        "selected_inner_mae": evaluated[selected]["mean_mae"],
        "candidate_count": len(evaluated),
        "failed_configurations": sum(c["failure"] is not None for c in evaluated),
        "inner_fit_attempts": sum(c["fit_attempts"] for c in evaluated),
        "outer_fit_attempts": fitted["fit_attempts"],
        "inner_fit_task_seconds": sum(c["fit_seconds"] for c in evaluated),
        "tuning_wall_seconds": tuning_seconds,
        "preprocessing_seconds": prep_seconds + part["audit"]["seconds"],
        "outer_fit_seconds": fitted["fit_seconds"],
        "outer_prediction_seconds": prediction_seconds,
        "total_wall_seconds": time.perf_counter() - started,
        "warnings": events,
        "warning_count": len(events),
        "transformed_features": part["train"].shape[1],
        "pca_components": part["audit"]["pca_components"],
        "validation_metrics": metrics(part["yvalid"], prediction),
        "model_file_sha256": digest(model_path),
        "completed_at": now(),
    }
    write_json(meta_path, meta)
    print(
        f"CONCLUÍDO {name} fold {fold} / 4; {meta['total_wall_seconds']:.1f}s; warnings={len(events)}; falhas={meta['failed_configurations']}",
        flush=True,
    )
    return meta


def collect_parts(dev, folds, seal, *, reproduce=False):
    predictions, records, checks = {}, [], []
    outer = folds["outer_fold"].to_numpy()
    for family, block in itertools.product(FAMILIES, BLOCKS):
        name = f"{family}__{block}"
        vector, counts = np.full(dev.height, np.nan), np.zeros(dev.height, int)
        for fold in range(5):
            model_path, meta_path = part_paths(name, fold)
            meta = read_json(meta_path)
            ensure(
                meta["seal_id"] == seal["seal_id"]
                and digest(model_path) == meta["model_file_sha256"],
                "Modelo/checkpoint mudou",
            )
            payload = joblib.load(ROOT / model_path)
            valid, train = payload["valid_indices"], payload["train_indices"]
            ensure(np.array_equal(valid, np.flatnonzero(outer == fold)), "Índices OOF mudaram")
            ensure(np.array_equal(train, np.flatnonzero(outer != fold)), "Índices treino mudaram")
            ensure(TARGET not in payload["input_columns"], "Alvo no modelo")
            ensure(payload["seal_id"] == seal["seal_id"], "Modelo não pertence ao selo")
            for audit in payload["audit"]:
                ti, vi = np.array(audit["train_indices"]), np.array(audit["valid_indices"])
                ensure(not set(ti) & set(vi), "Transformação com treino/validação sobrepostos")
                ensure(
                    audit["train_index_sha256"] == fingerprint(ti.tolist()), "Hash treino incorreto"
                )
                ensure(
                    audit["valid_index_sha256"] == fingerprint(vi.tolist()),
                    "Hash validação incorreto",
                )
                ensure(
                    set(ti).issubset(set(train)), "Transformação treinada fora do treino externo"
                )
                ensure(
                    not audit["target_in_input"] and TARGET not in audit["input_columns"],
                    "Alvo na transformação",
                )
                if "inner" in audit["context"]:
                    inner_fold = int(audit["context"].split("inner")[-1])
                    inner = folds[f"inner_outer_{fold}"].to_numpy()
                    ensure(
                        np.array_equal(ti, np.flatnonzero((inner >= 0) & (inner != inner_fold))),
                        "Fit interno fora do treino",
                    )
                    ensure(
                        np.array_equal(vi, np.flatnonzero(inner == inner_fold)),
                        "Validação interna incorreta",
                    )
                else:
                    ensure(
                        np.array_equal(ti, train) and np.array_equal(vi, valid),
                        "Fit externo incorreto",
                    )
            if reproduce:
                fresh = payload["pipeline"].predict(
                    dev[valid.tolist()].select(payload["input_columns"])
                )
                difference = float(np.max(np.abs(fresh - payload["prediction"])))
                ensure(
                    np.allclose(fresh, payload["prediction"], rtol=0, atol=1e-10),
                    "Pipeline não reproduz OOF",
                )
                checks.append(
                    {"model": name, "fold": fold, "maximum_absolute_difference": difference}
                )
            vector[valid] = payload["prediction"]
            counts[valid] += 1
            records.append(meta)
        ensure(np.isfinite(vector).all() and np.all(counts == 1), "OOF incompleta/duplicada")
        predictions[name] = vector
    return predictions, records, checks


def run():
    seal = verify_seal()
    technical = read_json(PRIVATE / "benchmark.json")
    ensure(technical["seal_id"] == seal["seal_id"], "Teste técnico não corresponde ao selo")
    dev, folds, refs, blocks, _ = load_inputs()
    started = time.perf_counter()
    try:
        with threadpool_limits(limits=1):
            for complete, (family, block, fold) in enumerate(
                itertools.product(FAMILIES, BLOCKS, range(5))
            ):
                write_json(
                    PRIVATE / "progress.json",
                    {
                        "status": "running",
                        "updated_at": now(),
                        "completed": complete,
                        "planned": 40,
                        "family": family,
                        "block": block,
                        "outer_fold": fold,
                    },
                )
                fit_outer(dev, folds, blocks, seal, family, block, fold)
            predictions, records, _ = collect_parts(dev, folds, seal)
            result = dev.select(
                "composition_key", "track_id", "spotify_row_id", "artist_group_id", TARGET
            ).with_columns(folds["outer_fold"])
            result = result.with_columns(
                [pl.Series(f"prediction__{name}", vector) for name, vector in predictions.items()]
            )
            result.write_parquet(output_path(PRIVATE / "oof_predictions.parquet"))
            write_json(
                PRIVATE / "run.json",
                {
                    "seal_id": seal["seal_id"],
                    "completed_at": now(),
                    "wall_seconds_this_invocation": time.perf_counter() - started,
                    "oof_sha256": digest(PRIVATE / "oof_predictions.parquet"),
                    "models": records,
                },
            )
            from tcc_music_popularity.statistical_revision_report_v080 import deliver

            deliver(dev, folds, refs, predictions, records, seal, verify_preservation())
            write_json(
                PRIVATE / "progress.json",
                {
                    "status": "complete_pending_verification",
                    "completed": 40,
                    "planned": 40,
                    "updated_at": now(),
                },
            )
    except Exception as exc:
        write_json(
            PRIVATE / "failure.json",
            {
                "at": now(),
                "type": type(exc).__name__,
                "error": str(exc),
                "warnings": getattr(exc, "events", []),
            },
        )
        raise


def verify():
    seal = verify_seal()
    dev, folds, refs, _, audit = load_inputs()
    reference = reproduce_references(dev, folds, refs)
    with threadpool_limits(limits=1):
        predictions, records, checks = collect_parts(dev, folds, seal, reproduce=True)
    saved = pl.read_parquet(ROOT / PRIVATE / "oof_predictions.parquet")
    ensure(
        saved.select(
            "composition_key", "track_id", "spotify_row_id", "artist_group_id", TARGET
        ).equals(
            dev.select("composition_key", "track_id", "spotify_row_id", "artist_group_id", TARGET)
        ),
        "Arquivo OOF desalinhado",
    )
    for name, values in predictions.items():
        ensure(
            np.array_equal(saved[f"prediction__{name}"].to_numpy(), values),
            "Arquivo OOF divergente",
        )
    preservation = verify_preservation()
    result = {
        "verified_at": now(),
        "rows": dev.height,
        "new_predictions": len(predictions),
        "new_fold_models": len(records),
        "fold_audit": audit,
        "reference_reproduction": reference,
        "pipeline_prediction_checks": checks,
        "tolerance_absolute": 1e-10,
        "tolerance_relative": 0,
        "all_oof_finite_complete_once": True,
        "target_excluded_from_inputs": True,
        "transform_train_indices_verified": True,
        "preservation": preservation,
    }
    write_json(PRIVATE / "verification.json", result)
    from tcc_music_popularity.statistical_revision_report_v080 import deliver

    deliver(dev, folds, refs, predictions, records, seal, preservation, result)
    write_json(
        PRIVATE / "progress.json",
        {"status": "complete_verified", "completed": 40, "planned": 40, "updated_at": now()},
    )
    print(
        json.dumps(
            {
                "status": "complete_verified",
                "rows": dev.height,
                "pipelines": len(predictions),
                "models_verified": len(checks),
                "max_prediction_difference": max(c["maximum_absolute_difference"] for c in checks),
                "preservation": preservation,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "benchmark", "run", "verify"))
    args = parser.parse_args()
    {"prepare": prepare, "benchmark": benchmark, "run": run, "verify": verify}[args.stage]()


if __name__ == "__main__":
    main()
