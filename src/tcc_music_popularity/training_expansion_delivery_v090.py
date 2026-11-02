"""Presentation-only V0.9 publication from existing aggregate metrics; no fitting."""

from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl

from .training_expansion_v090 import (
    BLOCKS,
    FIGURES,
    ROOT,
    SEEDS,
    digest,
    ensure,
    output,
    read_json,
    verify_seal,
    write_json,
)


def figures_from_aggregates(rows):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter

    overall = [r for r in rows if r["scope"] == "oof"]
    paths = []
    for metric, label in (
        ("mae", "MAE (pontos)"),
        ("rmse", "RMSE (pontos)"),
        ("p95_abs_error", "P95 do erro absoluto (pontos)"),
        ("prop_abs_gt20", "Erros acima de 20 pontos (%)"),
    ):
        fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), sharey=True)
        factor = 100 if metric == "prop_abs_gt20" else 1
        for ax, block in zip(axes, BLOCKS, strict=True):
            chosen = [r for r in overall if r["block"] == block]
            original = next(r for r in chosen if r["size_label"] == "original")
            maximum = next(r for r in chosen if r["size_label"] == "maximum")
            ax.axhline(
                factor * original[metric],
                color="black",
                ls=":",
                lw=1.6,
                label="Comum original (fixo)",
            )
            for universe, title, color in (
                ("common", "Comum", "#9457a3"),
                ("expanded", "Ampliado", "#007c91"),
            ):
                for index, seed in enumerate(SEEDS):
                    points = sorted(
                        [r for r in chosen if r["universe"] == universe and r["seed"] == seed],
                        key=lambda r: r["train_n_mean"],
                    )
                    if universe == "expanded":
                        points += [maximum]
                    ax.plot(
                        [r["train_n_mean"] for r in points],
                        [factor * r[metric] for r in points],
                        marker="o",
                        ms=4,
                        lw=1.3,
                        color=color,
                        ls="-" if index == 0 else "--",
                        alpha=0.85,
                        label=f"{title}; semente {seed}",
                    )
                grouped = defaultdict(list)
                for row in chosen:
                    if row["universe"] == universe and row["seed"] is not None:
                        grouped[row["size_label"]].append(row)
                means = sorted(
                    (
                        np.mean([r["train_n_mean"] for r in values]),
                        factor * np.mean([r[metric] for r in values]),
                    )
                    for values in grouped.values()
                )
                ax.scatter(
                    [point[0] for point in means],
                    [point[1] for point in means],
                    color=color,
                    marker="x",
                    s=45,
                    zorder=4,
                    label=f"{title}: média das sementes",
                )
            ax.scatter(
                [original["train_n_mean"]],
                [factor * original[metric]],
                color="black",
                marker="s",
                s=35,
                zorder=5,
            )
            ax.set_xscale("log")
            ax.xaxis.set_major_locator(FixedLocator([2000, 5000, 10000, 20000, 70000]))
            ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:g} mil"))
            ax.xaxis.set_minor_formatter(NullFormatter())
            ax.set_xlabel("n efetivo médio de treino por fold (escala log)")
            ax.set_title("Baseline" if block == "baseline" else "Tradicional (PCA90 LFM2b)")
            ax.grid(alpha=0.2)
        axes[0].set_ylabel(label)
        handles, labels = axes[1].get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            loc="lower center",
            ncol=3,
            fontsize=8,
            bbox_to_anchor=(0.5, 0.055),
        )
        fig.suptitle("V0.9 exploratória — mesma validação de 7.648 composições", fontsize=12)
        fig.text(
            0.5,
            0.025,
            "Máximo treinado uma vez; médias entre sementes são descritivas, sem intervalo de confiança.",
            ha="center",
            fontsize=8,
        )
        fig.tight_layout(rect=(0.015, 0.23, 1, 0.95))
        path = FIGURES / f"curva_{metric}_v0_9.png"
        fig.savefig(output(path), dpi=170, bbox_inches="tight", pad_inches=0.15)
        plt.close(fig)
        paths.append(path.as_posix())
    return paths


def main():
    # The sealed scientific implementation is never edited by this publication step.
    verify_seal()
    path = Path("reports/run_summary_ampliacao_v0_9.json")
    summary = read_json(path)
    ensure(summary["status"] == "complete_verified", "Verificação científica pendente")
    csv = Path("reports/curvas_aprendizagem_v0_9.csv")
    before = digest(csv)
    rows = pl.read_csv(ROOT / csv, infer_schema_length=None).to_dicts()
    figures = figures_from_aggregates(rows)
    ensure(digest(csv) == before, "Métricas agregadas mudaram")
    summary["figures"] = figures
    summary["public_artifact_sha256"].update({p: digest(p) for p in figures})
    summary["presentation_revision"] = {
        "source": csv.as_posix(),
        "source_sha256_unchanged": before,
        "code_sha256": digest(Path(__file__).relative_to(ROOT)),
        "change": "Somente rótulos/eixos/legenda/espaçamento; todas as condições e métricas preservadas.",
        "sealed_scientific_code_unchanged": True,
        "new_fits": 0,
    }
    write_json(path, summary)
    print("4 gráficos publicados; métricas e código científico selado inalterados.")


if __name__ == "__main__":
    main()
