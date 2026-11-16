"""Consolida agregados de decisão e inspeciona apenas a cauda delimitada de 128 faixas."""

from pathlib import Path

import numpy as np
import polars as pl
import pyarrow.parquet as pq

from . import classification_diagnostics as diagnostics
from . import decision_sensitivity as sensitivity
from . import popularity_levels as common

ROOT = common.ROOT
OUTPUT = ROOT / "reports/analise_sensibilidade_decisao_ordinal_v1"


def reconcile(rows, confusion):
    matrices = {}
    cells = set()
    for row in confusion:
        key = tuple(str(row[k]) for k in ("model", "outer_fold", "weighting", "decision_rule"))
        position = int(row["observed_class"]), int(row["predicted_class"])
        common.require(
            (key, position) not in cells and all(0 <= i <= 2 for i in position),
            "Célula duplicada ou inválida.",
        )
        cells.add((key, position))
        matrices.setdefault(key, np.full((3, 3), np.nan))[position] = float(row["count_or_weight"])
    seen = set()
    for row in rows:
        key = tuple(str(row[k]) for k in ("model", "outer_fold", "weighting", "decision_rule"))
        common.require(key not in seen and key in matrices, "Métrica repetida ou matriz ausente.")
        seen.add(key)
        for metric, result in diagnostics.from_confusion(matrices[key]).items():
            common.require(
                abs(result - float(row[metric])) <= 1e-10, "Métrica não reproduzida da matriz."
            )
    common.require(seen == set(matrices), "Matrizes/métricas não reconciliam.")


def comparison(metrics):
    lookup = {
        (r["model"], r["decision_rule"], r["weighting"]): r
        for r in metrics
        if int(r["outer_fold"]) == -1
    }
    result = []
    for name in (*sensitivity.model.BLOCKS, sensitivity.model.REFERENCE):
        for weighting in ("equal_tracks", "original_weight_sensitivity"):
            first = lookup[(name, "argmax_original", weighting)]
            second = lookup[(name, "inverse_training_prior", weighting)]
            for field in ("log_loss_original_probabilities", "brier_original_probabilities"):
                common.require(
                    first[field] == second[field],
                    "Regra de decisão alterou métrica probabilística.",
                )
            result.append(
                {
                    "model": name,
                    "weighting": weighting,
                    **{
                        rule + "_" + metric: float(row[metric])
                        for rule, row in (("original", first), ("alternative", second))
                        for metric in (
                            "accuracy",
                            "balanced_accuracy",
                            "macro_f1",
                            "extreme_error_rate",
                        )
                    },
                    **{
                        "delta_" + metric + "_pp": 100
                        * (float(second[metric]) - float(first[metric]))
                        for metric in (
                            "accuracy",
                            "balanced_accuracy",
                            "macro_f1",
                            "extreme_error_rate",
                        )
                    },
                }
            )
    return result


def bounded_tail(path, expected_rows=128, expected_components=96, expected_source_rows=77535):
    path = Path(path)
    common.require(
        path.stat().st_size <= 16 * 1024**2
        and pq.ParquetFile(path).metadata.num_rows == expected_source_rows,
        "Fonte fora do orçamento da inspeção.",
    )
    columns = [
        "spotify_popularity",
        "text_component_id",
        *[
            f"{name}_probability_{i}"
            for name in (*sensitivity.model.BLOCKS, sensitivity.model.REFERENCE)
            for i in range(3)
        ],
    ]
    # Seleção delimitada antes de materializar; não carregar a coorte completa.
    frame = (
        pl.scan_parquet(path)
        .filter(pl.col("spotify_popularity") >= 80)
        .select(columns)
        .head(expected_rows + 1)
        .collect()
    )
    common.require(
        frame.height == expected_rows
        and frame["text_component_id"].n_unique() == expected_components,
        "Cauda excedeu ou divergiu do domínio esperado.",
    )
    priors = frame.select([f"class_prior_probability_{i}" for i in range(3)]).to_numpy()
    rows = []
    for name in sensitivity.model.BLOCKS:
        probability = frame.select([f"{name}_probability_{i}" for i in range(3)]).to_numpy()
        for rule in sensitivity.RULES:
            labels = sensitivity.decisions(probability, priors, rule)
            rows.append(
                {
                    "model": name,
                    "decision_rule": rule,
                    "n_observed_ge80": expected_rows,
                    "components": expected_components,
                    **{
                        f"predicted_operational_class_{i}": int((labels == i).sum())
                        for i in range(3)
                    },
                    "fraction_predicted_ge40": float(np.mean(labels == 2)),
                    "is_binary_hit_detection": False,
                }
            )
    return rows


def figures(metrics, per_class, confusion, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    def get(rows, rule):
        return next(
            r
            for r in rows
            if r["model"] == "combined"
            and int(r["outer_fold"]) == -1
            and r["weighting"] == "equal_tracks"
            and r["decision_rule"] == rule
        )

    high = [r for r in per_class if int(r["class_index"]) == 2]
    labels = ["Acurácia balanceada", "Acurácia", "Sensibilidade elevada", "Precisão elevada"]
    fig, ax = plt.subplots(figsize=(7.1, 3.9))
    positions = np.arange(4)
    for offset, rule, color, name in (
        (-0.18, "argmax_original", "#195889", "Principal"),
        (0.18, "inverse_training_prior", "#cb7529", "Sensibilidade p/π"),
    ):
        overall, elevated = get(metrics, rule), get(high, rule)
        values = [
            float(overall["balanced_accuracy"]),
            float(overall["accuracy"]),
            float(elevated["recall"]),
            float(elevated["precision"]),
        ]
        bars = ax.barh(positions + offset, values, height=0.34, color=color, label=name)
        ax.bar_label(
            bars,
            labels=[f"{100 * v:.1f}%".replace(".", ",") for v in values],
            fontsize=8,
            padding=3,
        )
    ax.set(yticks=positions, yticklabels=labels, xlim=(0, 1))
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    fig.tight_layout()
    for suffix in ("png", "svg"):
        fig.savefig(
            Path(output) / ("compromisso_decisao_combinado." + suffix), dpi=300, facecolor="white"
        )
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.9), sharey=True)
    for ax, rule, title in zip(
        axes, sensitivity.RULES, ("Principal", "Sensibilidade p/π"), strict=True
    ):
        matrix = np.zeros((3, 3))
        for row in confusion:
            if (
                row["model"] == "combined"
                and int(row["outer_fold"]) == -1
                and row["weighting"] == "equal_tracks"
                and row["decision_rule"] == rule
            ):
                matrix[int(row["observed_class"]), int(row["predicted_class"])] = float(
                    row["count_or_weight"]
                )
        normalized = matrix / matrix.sum(axis=1)[:, None]
        ax.imshow(normalized, cmap="Blues", vmin=0, vmax=1)
        ax.set(
            title=title,
            xticks=range(3),
            yticks=range(3),
            xticklabels=["Baixo", "Interm.", "Elevado"],
            yticklabels=["Baixo", "Interm.", "Elevado"],
            xlabel="Nível previsto",
        )
        for i in range(3):
            for j in range(3):
                ax.text(
                    j,
                    i,
                    f"{100 * normalized[i, j]:.1f}%".replace(".", ",")
                    + "\n"
                    + f"n={int(matrix[i, j]):,}".replace(",", "."),
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white" if normalized[i, j] > 0.5 else "#111111",
                )
    axes[0].set_ylabel("Nível observado")
    fig.tight_layout()
    for suffix in ("png", "svg"):
        fig.savefig(Path(output) / ("confusao_duas_regras." + suffix), dpi=300, facecolor="white")
    plt.close(fig)


def run():
    from .manual_lyrics import exclusive

    source = sensitivity.OUTPUT
    report = common.read_json(source / "resumo_sensibilidade.json")
    common.require(
        report["completed"]
        and report["original_metrics_reproduced"]
        and not report["models_trained"]
        and not report["probabilities_changed"],
        "Concluir/verificar sensibilidade 36.",
    )
    paths = [
        source / name
        for name in (
            "resumo_sensibilidade.json",
            "metricas_regras.csv",
            "matrizes_confusao.csv",
            "metricas_por_classe.csv",
        )
    ]
    paths.append(sensitivity.SOURCE)
    seal = {
        "code": common.digest(Path(__file__)),
        "inputs": {str(p.relative_to(ROOT)): common.digest(p) for p in paths},
    }
    main = common.read_json(sensitivity.REPORT)
    common.require(
        common.digest(sensitivity.SOURCE) == main["prediction_sha256"],
        "Probabilidades principais alteradas.",
    )
    preserved = common.frozen_hashes()
    with exclusive(OUTPUT):
        common.prepare_output(OUTPUT, seal, paths)
        metrics = common.read_csv(source / "metricas_regras.csv")
        confusion = common.read_csv(source / "matrizes_confusao.csv")
        per_class = common.read_csv(source / "metricas_por_classe.csv")
        reconcile(metrics, confusion)
        common.write_csv(OUTPUT / "comparacao_regras.csv", comparison(metrics))
        common.write_csv(OUTPUT / "cauda_80_delimitada.csv", bounded_tail(sensitivity.SOURCE))
        figures(metrics, per_class, confusion, OUTPUT)
        common.require(
            all(common.digest(ROOT / p) == h for p, h in seal["inputs"].items()),
            "Fonte mudou durante análise.",
        )
        common.require(common.frozen_hashes() == preserved, "Artefato anterior mudou.")
        summary = {
            "completed": True,
            "seal": seal,
            "aggregate_metric_records_checked": len(metrics),
            "confusion_cells_checked": len(confusion),
            "individual_rows_inspected": 128,
            "tail_components": 96,
            "whole_cohort_individual_rows_reprocessed_by_agent": False,
            "models_trained": False,
            "main_results_replaced": False,
            "hypothesis_tests_computed": False,
        }
        common.atomic_json(OUTPUT / "resumo_analise.json", summary)
    print("Análise consolidada; sem novo treino. " + str(OUTPUT), flush=True)
    return summary


def cli():
    import argparse

    argparse.ArgumentParser(description=__doc__).parse_args()
    run()
    return 0
