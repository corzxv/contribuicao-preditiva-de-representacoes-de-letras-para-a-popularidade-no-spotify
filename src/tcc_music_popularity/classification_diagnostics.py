"""Síntese de agregados ordinais e parâmetros pequenos de PCA, sem novo ajuste."""

from collections import Counter
from pathlib import Path

import joblib
import numpy as np

from . import observed_classification as model
from . import popularity_levels as common

ROOT = common.ROOT
SOURCE = model.OUTPUT / "integral"
OUTPUT = ROOT / "reports/diagnosticos_classificacao_ordinal_200k_v1"
LABELS = {
    "baseline": "Baseline",
    "traditional": "Tradicional",
    "deep": "Profundo",
    "combined": "Combinado",
    "class_prior": "Referência",
}


def from_confusion(matrix):
    matrix = np.asarray(matrix, float)
    common.require(
        matrix.shape == (3, 3)
        and np.isfinite(matrix).all()
        and (matrix >= 0).all()
        and (matrix.sum(axis=1) > 0).all(),
        "Matriz agregada inválida.",
    )
    support = matrix.sum(axis=1)
    predicted = matrix.sum(axis=0)
    return {
        "accuracy": float(np.trace(matrix) / matrix.sum()),
        "balanced_accuracy": float(np.mean(np.diag(matrix) / support)),
        "macro_f1": float(np.mean(2 * np.diag(matrix) / (support + predicted))),
        "extreme_error_rate": float((matrix[0, 2] + matrix[2, 0]) / matrix.sum()),
    }


def reconcile(metrics, confusion):
    for record in metrics:
        if int(record["outer_fold"]) != -1:
            continue
        selected = [
            r
            for r in confusion
            if r["model"] == record["model"] and r["weighting"] == record["weighting"]
        ]
        common.require(len(selected) == 9, "Matriz de confusão não contém nove células.")
        matrix = np.empty((3, 3))
        common.require(
            len({(r["observed_class"], r["predicted_class"]) for r in selected}) == 9,
            "Células duplicadas.",
        )
        for row in selected:
            matrix[int(row["observed_class"]), int(row["predicted_class"])] = float(
                row["count_or_weight"]
            )
        for name, value in from_confusion(matrix).items():
            common.require(
                abs(float(record[name]) - value) <= 1e-10,
                "Métrica agregada diverge da matriz: " + name,
            )


def calibration_summary(rows):
    result = []
    for name in (*model.BLOCKS, model.REFERENCE):
        for target in range(3):
            cells = [r for r in rows if r["model"] == name and int(r["class_index"]) == target]
            common.require(len(cells) == 10, "Exigir dez intervalos fixos por classe.")
            n = sum(int(r["n"]) for r in cells)
            common.require(n > 0, "Calibração sem observações.")
            deviation = (
                sum(
                    int(r["n"])
                    * abs(float(r["mean_predicted_probability"]) - float(r["observed_fraction"]))
                    for r in cells
                    if int(r["n"]) > 0
                )
                / n
            )
            result.append(
                {
                    "model": name,
                    "class_index": target,
                    "n": n,
                    "weighted_absolute_bin_deviation": deviation,
                    "confidence_interval_computed": False,
                }
            )
    return result


def pca_parameters(selection, directory, signature):
    rows = []
    for record in selection:
        if record["option"] != "pca95":
            continue
        stem = directory / f"outer{record['outer_fold']}_{record['block']}"
        seal = common.read_json(stem.with_suffix(".json"))
        common.require(seal["signature"] == signature, "Parte PCA de outra execução.")
        path = stem.with_suffix(".joblib")
        common.require(
            path.stat().st_size < 2 * 1024**2 and common.digest(path) == seal["model_sha256"],
            "Modelo local incompatível para inspeção de PCA.",
        )
        # Arquivos próprios da execução já conferida; extrai só matrizes 11×9.
        fitted = joblib.load(path)
        pca = (
            fitted.named_steps["prepare"]
            .named_steps["columns"]
            .named_transformers_["metadata_numeric"]
            .named_steps["pca"]
        )
        common.require(
            pca.components_.shape[1] == len(model.regression.data.NUMERIC),
            "Variáveis de PCA incompatíveis.",
        )
        for component, original in enumerate(pca.components_):
            vector = original.copy()
            if vector[np.argmax(np.abs(vector))] < 0:
                vector *= -1
            for variable, value in zip(model.regression.data.NUMERIC, vector, strict=True):
                rows.append(
                    {
                        "model": record["block"],
                        "outer_fold": int(record["outer_fold"]),
                        "component": component + 1,
                        "variable": variable,
                        "standardized_component_coefficient": float(value),
                        "explained_variance_ratio": float(pca.explained_variance_ratio_[component]),
                        "retained_components": int(pca.n_components_),
                        "total_retained_variance_ratio": float(pca.explained_variance_ratio_.sum()),
                    }
                )
        common.require(
            common.digest(path) == seal["model_sha256"], "Inspeção não preservou modelo."
        )
    return rows


def figures(metrics, old_metrics, confusion, calibration, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    current = {
        r["model"]: r
        for r in metrics
        if r["weighting"] == "equal_tracks" and int(r["outer_fold"]) == -1
    }
    previous = {
        r["model"]: r
        for r in old_metrics
        if r["scheme"] == "principal_20_40"
        and r["weighting"] == "equal_tracks"
        and int(r["outer_fold"]) == -1
    }

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(output / (name + ".png"), dpi=300, facecolor="white")
        fig.savefig(output / (name + ".svg"), facecolor="white")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    x = np.arange(4)
    for offset, source, color, label in (
        (-0.19, previous, "#bac7d3", "Regressão categorizada"),
        (0.19, current, "#195889", "Logística ordinal"),
    ):
        values = [float(source[name]["balanced_accuracy"]) for name in model.BLOCKS]
        bars = ax.bar(x + offset, values, width=0.36, color=color, label=label)
        ax.bar_label(
            bars,
            labels=[f"{100 * v:.1f}".replace(".", ",") + "%" for v in values],
            fontsize=8,
            padding=3,
        )
    ax.axhline(1 / 3, color="#555555", linestyle="--", linewidth=1, label="Referência: 33,3%")
    ax.set(
        xticks=x,
        xticklabels=[LABELS[n] for n in model.BLOCKS],
        ylim=(0, 1),
        ylabel="Acurácia balanceada",
    )
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    save(fig, "comparacao_classificacao")

    cells = [r for r in confusion if r["model"] == "combined" and r["weighting"] == "equal_tracks"]
    matrix = np.zeros((3, 3))
    for row in cells:
        matrix[int(row["observed_class"]), int(row["predicted_class"])] = float(
            row["count_or_weight"]
        )
    normalized = matrix / matrix.sum(axis=1)[:, None]
    fig, ax = plt.subplots(figsize=(5.0, 4.1))
    ax.imshow(normalized, vmin=0, vmax=1, cmap="Blues")
    labels = ["Baixo\n0–19", "Intermediário\n20–39", "Elevado\n40–100"]
    ax.set(
        xticks=range(3),
        yticks=range(3),
        xticklabels=labels,
        yticklabels=labels,
        xlabel="Nível previsto",
        ylabel="Nível observado",
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
                color="white" if normalized[i, j] > 0.5 else "#111111",
                fontsize=10,
            )
    save(fig, "confusao_combinado")

    fig, axes = plt.subplots(1, 3, figsize=(9.2, 3.3), sharex=True, sharey=True)
    for target, ax in enumerate(axes):
        rows = [
            r
            for r in calibration
            if r["model"] == "combined" and int(r["class_index"]) == target and int(r["n"]) > 0
        ]
        ax.plot([0, 1], [0, 1], linestyle="--", color="#777777", linewidth=1)
        ax.plot(
            [float(r["mean_predicted_probability"]) for r in rows],
            [float(r["observed_fraction"]) for r in rows],
            "o-",
            color="#195889",
            markersize=4,
        )
        ax.set(
            title=labels[target].replace("\n", " "),
            xlim=(0, 1),
            ylim=(0, 1),
            xlabel="Probabilidade média prevista",
        )
        ax.xaxis.set_major_formatter(PercentFormatter(1))
        ax.yaxis.set_major_formatter(PercentFormatter(1))
    axes[0].set_ylabel("Fração observada")
    save(fig, "calibracao_combinado")


def run(output=OUTPUT):
    report_path = SOURCE / "resumo_classificacao.json"
    report = common.read_json(report_path)
    common.require(
        report["completed"]
        and report["completed_outer_blocks"] == 20
        and report["prediction_rows"] == 77535
        and report["global_metrics_available"],
        "Concluir classificação antes dos diagnósticos.",
    )
    previous_path = common.OUTPUT / "previsoes/metricas_categorizadas.csv"
    paths = [
        report_path,
        previous_path,
        *[
            SOURCE / (name + ".csv")
            for name in (
                "metricas_externas",
                "matrizes_confusao",
                "metricas_por_classe",
                "selecoes_internas",
                "calibracao_descritiva",
            )
        ],
    ]
    selections = common.read_csv(SOURCE / "selecoes_internas.csv")
    for selected in selections:
        if selected["option"] == "pca95":
            stem = (
                model.WORKSPACE
                / "integral/parts"
                / f"outer{selected['outer_fold']}_{selected['block']}"
            )
            paths.extend([stem.with_suffix(".json"), stem.with_suffix(".joblib")])
    seal = {
        "code": common.digest(Path(__file__)),
        "inputs": {str(p.relative_to(ROOT)): common.digest(p) for p in paths},
        "classification_signature": report["signature"],
    }
    from .manual_lyrics import exclusive

    output = Path(output)
    with exclusive(output):
        common.prepare_output(output, seal, paths)
        metrics = common.read_csv(SOURCE / "metricas_externas.csv")
        confusion = common.read_csv(SOURCE / "matrizes_confusao.csv")
        selections = common.read_csv(SOURCE / "selecoes_internas.csv")
        calibration = common.read_csv(SOURCE / "calibracao_descritiva.csv")
        old_metrics = common.read_csv(previous_path)
        reconcile(metrics, confusion)
        deviations = calibration_summary(calibration)
        common.write_csv(output / "desvios_calibracao.csv", deviations)
        components = pca_parameters(
            selections, model.WORKSPACE / "integral/parts", report["signature"]
        )
        if components:
            common.write_csv(output / "coeficientes_pca.csv", components)
        current = {
            r["model"]: r
            for r in metrics
            if r["weighting"] == "equal_tracks" and int(r["outer_fold"]) == -1
        }
        previous = {
            r["model"]: r
            for r in old_metrics
            if r["scheme"] == "principal_20_40"
            and r["weighting"] == "equal_tracks"
            and int(r["outer_fold"]) == -1
        }
        comparison = [
            {
                "model": name,
                "ordinal_balanced_accuracy": float(current[name]["balanced_accuracy"]),
                "regression_categorized_balanced_accuracy": float(
                    previous[name]["balanced_accuracy"]
                ),
                "delta_balanced_accuracy_pp": 100
                * (
                    float(current[name]["balanced_accuracy"])
                    - float(previous[name]["balanced_accuracy"])
                ),
            }
            for name in model.BLOCKS
        ]
        common.write_csv(output / "comparacao_regressao_categorizada.csv", comparison)
        figures(metrics, old_metrics, confusion, calibration, output)
        summary = {
            "completed": True,
            "seal": seal,
            "source_rows": 77535,
            "classification_models_trained": False,
            "individual_prediction_rows_read": 0,
            "confusion_metrics_reconciled": True,
            "selected_pca_parts": sum(r["option"] == "pca95" for r in selections),
            "total_outer_model_parts": len(selections),
            "selected_alpha_counts": dict(Counter(r["alpha"] for r in selections)),
            "selected_pca_model_files_read": len(
                {(r["model"], r["outer_fold"]) for r in components}
            ),
            "delta_combined_baseline_balanced_accuracy_pp": 100
            * (
                float(current["combined"]["balanced_accuracy"])
                - float(current["baseline"]["balanced_accuracy"])
            ),
            "delta_combined_deep_balanced_accuracy_pp": 100
            * (
                float(current["combined"]["balanced_accuracy"])
                - float(current["deep"]["balanced_accuracy"])
            ),
            "confidence_intervals_computed": False,
            "proportional_odds_formally_tested": False,
        }
        common.require(
            all(common.digest(ROOT / p) == digest for p, digest in seal["inputs"].items()),
            "Agregado de origem mudou.",
        )
        common.atomic_json(output / "resumo_diagnosticos.json", summary)
    print("Diagnósticos agregados concluídos; sem novos ajustes. " + str(output), flush=True)
    return summary


def cli():
    import argparse

    argparse.ArgumentParser(description=__doc__).parse_args()
    run()
    return 0
