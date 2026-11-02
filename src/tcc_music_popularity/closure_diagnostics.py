"""Fechamento leve: resíduos, clipping separado e incerteza de avaliação condicional.

Não treina, não reamostra a pipeline, não carrega encoder ou letras. Os intervalos
são aproximações sob um modelo auxiliar de componentes independentes, fold a fold;
não quantificam a incerteza integral da validação cruzada.
"""

import argparse
import hashlib
import json
import time
from pathlib import Path
from statistics import NormalDist

import numpy as np
import polars as pl
import pyarrow.parquet as pq

from . import observed_results as previous
from .manual_lyrics import atomic_json, require

ROOT = previous.ROOT
OUTPUT = ROOT / "reports/fechamento_metodologico_200k_v1"
PREDICTIONS = ROOT / "data/derived/private_regression_200k_v1/integral/predicoes_externas.parquet"
COMPONENTS = previous.WORKSPACE / "perdas_componentes.parquet"
DIAGNOSTICS = previous.OUTPUT / "resumo_diagnosticos.json"
PROTOCOL = ROOT / "docs/protocolo_fechamento_metodologico_200k_v1.md"
MODELS = tuple(previous.reg.BLOCKS)
REFERENCES = ("baseline", "deep")
MAX_ROWS = 80000
MAX_BYTES = 32 * 1024 * 1024


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def cluster_ratio(difference_sums, denominators):
    """Linearização de razão de totais, preservando o estimando por faixa.

    D_g é a soma PAREADA das diferenças de perdas no componente, N_g seu
    tamanho (ou soma dos pesos). Não calcula a média simples dos MAEs de grupos.
    """
    d, n = np.asarray(difference_sums, float), np.asarray(denominators, float)
    require(
        d.ndim == n.ndim == 1
        and d.shape == n.shape
        and len(n) > 1
        and np.isfinite(d).all()
        and np.isfinite(n).all()
        and (n > 0).all(),
        "Componentes inválidos para linearização da razão.",
    )
    total = float(n.sum())
    estimate = float(d.sum() / total)
    scores = d - estimate * n
    variance = float(len(n) / (len(n) - 1) * np.dot(scores, scores) / total**2)
    return {
        "delta_mae": estimate,
        "se_cluster_conditional": variance**0.5,
        "denominator": total,
        "components": len(n),
        "max_component_share": float(n.max() / total),
    }


def conditional_intervals(components, alpha=0.05):
    """Por fold; combinação conservadora de extremos via união de Bonferroni.

    Família: dois contrastes × cinco folds, separada para cada ponderação.
    Não divide desvio dos folds por sqrt(5), nem supõe sua independência.
    A cobertura nominal depende da validade das aproximações marginais por fold.
    """
    require(0 < alpha < 1, "Alpha inválido.")
    require(
        components["text_component_id"].n_unique() == components.height,
        "Componentes repetidos, possivelmente cruzando folds.",
    )
    folds = sorted(components["outer_fold"].unique().to_list())
    require(folds == list(range(5)), "Exigir cinco folds externos existentes.")
    family_size = len(REFERENCES) * len(folds)
    z_point = NormalDist().inv_cdf(1 - alpha / 2)
    z_family = NormalDist().inv_cdf(1 - alpha / (2 * family_size))
    individual, aggregate = [], []
    for weighting, prefix, denominator in (
        ("equal_tracks", "abs_", "n"),
        ("original_weights_sensitivity", "weighted_abs_", "weight_sum"),
    ):
        for reference in REFERENCES:
            rows = []
            for fold in folds:
                cell = components.filter(pl.col("outer_fold") == fold)
                result = cluster_ratio(
                    cell[prefix + "combined"].to_numpy() - cell[prefix + reference].to_numpy(),
                    cell[denominator].to_numpy(),
                )
                center, se = result["delta_mae"], result["se_cluster_conditional"]
                row = {
                    "weighting": weighting,
                    "contrast": "combined_minus_" + reference,
                    "outer_fold": fold,
                    **result,
                    "nominal_pointwise_95_lower": center - z_point * se,
                    "nominal_pointwise_95_upper": center + z_point * se,
                    "bonferroni_family_lower": center - z_family * se,
                    "bonferroni_family_upper": center + z_family * se,
                    "family_size": family_size,
                    "nominal_family_alpha": alpha,
                    "full_training_uncertainty": False,
                }
                rows.append(row)
                individual.append(row)
            denominator_sum = sum(r["denominator"] for r in rows)

            def average(key, parts=rows, total=denominator_sum):
                return sum(r[key] * r["denominator"] for r in parts) / total

            aggregate.append(
                {
                    "weighting": weighting,
                    "contrast": "combined_minus_" + reference,
                    "delta_mae": average("delta_mae"),
                    "conditional_bonferroni_lower": average("bonferroni_family_lower"),
                    "conditional_bonferroni_upper": average("bonferroni_family_upper"),
                    "nominal_family_alpha": alpha,
                    "fold_independence_assumed": False,
                    "full_training_uncertainty": False,
                }
            )
    return individual, aggregate


def prediction_diagnostics(frame):
    """Resíduo = previsão - observado; negativo indica subestimação."""
    y, w = (frame[c].to_numpy() for c in ("spotify_popularity", "sampling_weight"))
    require(
        len(y) > 0
        and np.isfinite(y).all()
        and np.isfinite(w).all()
        and (w > 0).all()
        and ((y >= 0) & (y <= 100)).all(),
        "Resposta/pesos inválidos; clipping só é avaliado para alvo em [0,100].",
    )
    masks = {"all": np.ones(len(y), bool), "popularity_80_100": y >= 80}
    metrics, tails, histogram, negative = [], [], [], []
    for model in MODELS:
        p = frame["prediction_" + model].to_numpy()
        require(np.isfinite(p).all(), "Previsão inválida.")
        error, clipped = p - y, np.clip(p, 0, 100)
        abs_error = np.abs(error)
        for label, mask in masks.items():
            if not mask.any():
                continue
            n = int(mask.sum())
            raw_mae = float(abs_error[mask].mean())
            raw_wmae = float(np.average(abs_error[mask], weights=w[mask]))
            clip_abs = np.abs(clipped[mask] - y[mask])
            require((clip_abs <= abs_error[mask] + 1e-12).all(), "Clipping elevou erro absoluto.")
            row = {
                "model": model,
                "scope": label,
                "n": n,
                "mae_original": raw_mae,
                "mae_clipped_sensitivity": float(clip_abs.mean()),
                "delta_mae_clipped_minus_original": float(clip_abs.mean()) - raw_mae,
                "mae_original_weights": raw_wmae,
                "mae_clipped_original_weights": float(np.average(clip_abs, weights=w[mask])),
                "rmse_original": float(np.mean(error[mask] ** 2) ** 0.5),
                "rmse_clipped_sensitivity": float(np.mean((clipped[mask] - y[mask]) ** 2) ** 0.5),
                "below_zero": int((p[mask] < 0).sum()),
                "above_100": int((p[mask] > 100).sum()),
            }
            metrics.append(row)
            if label == "all":
                continue
            selected = frame.filter(pl.Series(mask))
            residuals = error[mask]
            record = {
                **row,
                "components": selected["text_component_id"].n_unique(),
                "observed_mean": float(y[mask].mean()),
                "prediction_mean": float(p[mask].mean()),
                "prediction_min": float(p[mask].min()),
                "prediction_max": float(p[mask].max()),
                "residual_mean": float(residuals.mean()),
                "residual_std_population": float(residuals.std(ddof=0)),
                "underpredictions": int((residuals < 0).sum()),
                "overpredictions": int((residuals > 0).sum()),
                "under_by_at_least_20": int((residuals <= -20).sum()),
                "under_by_at_least_40": int((residuals <= -40).sum()),
                "observation_share": n / len(y),
                "absolute_error_sum": float(abs_error[mask].sum()),
                "share_global_absolute_error": float(abs_error[mask].sum() / abs_error.sum()),
                "contribution_to_global_mae": float(abs_error[mask].sum() / len(y)),
                "share_global_squared_error": float(np.sum(residuals**2) / np.sum(error**2)),
                "contribution_to_weighted_global_mae": float(
                    np.sum(w[mask] * abs_error[mask]) / w.sum()
                ),
                "mae_outside_tail": float(abs_error[~mask].mean()) if (~mask).any() else None,
                **{
                    f"residual_q{q:02}": float(np.quantile(residuals, q / 100))
                    for q in (0, 10, 25, 50, 75, 90, 100)
                },
            }
            tails.append(record)
            edges = [-np.inf, -60, -40, -30, -20, -10, 0, 10, np.inf]
            counts, _ = np.histogram(residuals, bins=edges)
            for left, right, count in zip(edges[:-1], edges[1:], counts, strict=True):
                histogram.append(
                    {
                        "model": model,
                        "bin_left": str(left),
                        "bin_right": str(right),
                        "n": int(count),
                    }
                )
        mask = p < 0
        if mask.any():
            negative.append(
                {
                    "model": model,
                    "n": int(mask.sum()),
                    "components": frame.filter(pl.Series(mask))["text_component_id"].n_unique(),
                    "minimum_prediction": float(p[mask].min()),
                    "median_prediction": float(np.median(p[mask])),
                    "observed_mean": float(y[mask].mean()),
                    "observed_median": float(np.median(y[mask])),
                    "observed_max": float(y[mask].max()),
                    "n_observed_zero": int((y[mask] == 0).sum()),
                    "n_observed_at_least_40": int((y[mask] >= 40).sum()),
                    "clipping_reduction_sum": float(-p[mask].sum()),
                    "share_global_absolute_error": float(abs_error[mask].sum() / abs_error.sum()),
                }
            )
    fold_counts = [
        {"outer_fold": int(f), "tail_tracks": int((g["spotify_popularity"] >= 80).sum())}
        for (f,), g in frame.partition_by("outer_fold", as_dict=True).items()
    ]
    return {
        "metrics_and_clipping": metrics,
        "tail_residuals": tails,
        "tail_residual_histogram": histogram,
        "negative_predictions": negative,
        "tail_counts_by_fold": sorted(fold_counts, key=lambda r: r["outer_fold"]),
    }


def run(
    *,
    predictions=PREDICTIONS,
    components=COMPONENTS,
    diagnostics=DIAGNOSTICS,
    output=OUTPUT,
    expected=77535,
):
    started = time.monotonic()
    require(not output.exists(), "Destino existente preservado; escolha outro --output.")
    audit = json.loads(diagnostics.read_text(encoding="utf-8"))
    require(audit["completed"] and audit["cohort_rows"] == expected, "Etapa 23 incompleta.")
    protected = {p: digest(p) for p in (predictions, components, diagnostics)}
    require(
        protected[predictions] == audit["seal"]["inputs"][str(predictions.resolve())]
        and protected[components] == audit["component_losses_sha256"],
        "Previsões/perdas mudaram desde a auditoria 23.",
    )
    for path in (predictions, components):
        require(
            path.stat().st_size <= MAX_BYTES and pq.ParquetFile(path).metadata.num_rows <= MAX_ROWS,
            "Diagnóstico excede limite leve; preparar execução manual antes de ampliar.",
        )
    print("[1/3] Conferindo previsões/perdas existentes; sem modelos ou encoder...", flush=True)
    columns = [
        "track_id",
        "text_component_id",
        "outer_fold",
        "spotify_popularity",
        "sampling_weight",
        *["prediction_" + m for m in MODELS],
    ]
    frame = pl.read_parquet(predictions, columns=columns)
    groups = pl.read_parquet(components)
    require(frame.height == frame["track_id"].n_unique() == expected, "IDs/contagem divergentes.")
    require(
        frame["text_component_id"].null_count() == 0
        and set(frame["outer_fold"].to_list()) == set(range(5))
        and frame.group_by("text_component_id")
        .agg(pl.col("outer_fold").n_unique())["outer_fold"]
        .max()
        == 1,
        "Grupos/folds inválidos.",
    )
    recomputed = previous.component_losses(
        frame.with_columns(*[pl.lit(0.0).alias("prediction_" + m) for m in previous.reg.REFERENCES])
    )
    checked_columns = [
        "text_component_id",
        "outer_fold",
        "n",
        "weight_sum",
        *[p + m for p in ("abs_", "weighted_abs_") for m in MODELS],
    ]
    for col in checked_columns:
        if col == "text_component_id":
            require(
                recomputed[col].equals(groups.sort("text_component_id")[col]), "Grupos divergentes."
            )
        else:
            require(
                np.allclose(
                    recomputed[col], groups.sort("text_component_id")[col], rtol=1e-12, atol=1e-9
                ),
                "Perdas/contagens divergentes.",
            )
    print("[2/3] Resíduos/clipping separado e intervalos condicionais por fold...", flush=True)
    individual, aggregate = conditional_intervals(groups)
    result = prediction_diagnostics(frame)
    frozen = {p: digest(p) for p in (predictions, components, diagnostics)}
    require(frozen == protected, "Fonte alterada durante diagnóstico.")
    output.mkdir(parents=True)
    for name, rows in {
        **result,
        "intervalos_condicionais_por_fold": individual,
        "intervalos_condicionais_combinados": aggregate,
    }.items():
        pl.DataFrame(rows).write_csv(output / (name + ".csv"))
    summary = {
        "completed": True,
        "version": "closure-diagnostics-v1",
        "cohort_rows": expected,
        "components": groups.height,
        "input_hashes": {str(p): v for p, v in protected.items()},
        "code_sha256": digest(Path(__file__)),
        "protocol_sha256": digest(PROTOCOL),
        "residual_definition": "prediction_minus_observed; negative_is_underprediction",
        "intervals": "auxiliary_asymptotic_foldwise_cluster_ratio_and_Bonferroni_envelope",
        "interval_families": "two_contrasts_times_five_folds_separate_for_each_weighting",
        "component_independence_is_assumption": True,
        "fold_independence_assumed": False,
        "full_training_uncertainty": False,
        "models_trained": False,
        "embeddings_generated": False,
        "lyrics_read": False,
        "individual_outputs_written": False,
        "original_inputs_unchanged": True,
        "runtime": {"numpy": np.__version__, "polars": pl.__version__},
        "seconds": time.monotonic() - started,
    }
    atomic_json(output / "resumo_fechamento.json", summary)
    print(f"[3/3] Concluído; somente diagnósticos auxiliares em {output}", flush=True)
    return 0


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    return run(output=args.output)
