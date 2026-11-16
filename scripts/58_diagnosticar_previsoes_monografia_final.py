"""Produz agregados e figuras da avaliação externa para a monografia."""

import csv
import json
from argparse import ArgumentParser
from hashlib import file_digest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/classificacao_9526_v1"
PREDICTIONS = ROOT / "data/derived/private_classificacao_9526_v1/probabilidades_externas.parquet"
OUT = ROOT / "reports/monografia_template_overleaf"
MODELS = ("baseline", "traditional", "deep", "combined")
LABELS = ("Baseline", "Tradicional", "Profundo", "Combinado")
CLASSES = ("Baixa", "Média", "Alta")
PAIRS = ((1, 0), (2, 0), (3, 0), (3, 2))
SEED = 42
N_REPLICATES = 8000


def save_figure(fig, name, output):
    for extension in ("png", "svg"):
        fig.savefig(output / "images" / f"{name}.{extension}", dpi=170, bbox_inches="tight")
    plt.close(fig)


def conditional_differences(totals, hits):
    recall = hits / totals[..., None, :]
    # Cada contraste usa os mesmos componentes, classes e multiplicidades.
    differences = np.stack(
        [recall[..., first, :] - recall[..., second, :] for first, second in PAIRS]
    )
    return np.stack([differences.mean(axis=-1), differences[..., 2]], axis=-1)


def bootstrap(totals, hits, seed):
    rng = np.random.default_rng(seed)
    n_groups = len(totals)
    draws = []
    for begin in range(0, N_REPLICATES, 100):
        size = min(100, N_REPLICATES - begin)
        selected = rng.integers(n_groups, size=(size, n_groups))
        counts = totals[selected].sum(axis=1)
        if (counts == 0).any():
            raise ValueError("Uma réplica perdeu pelo menos uma classe.")
        draws.append(conditional_differences(counts, hits[selected].sum(axis=1)))
    return np.quantile(np.concatenate(draws, axis=1), [0.025, 0.975], axis=1)


def write_intervals(point, intervals, output):
    columns = ("contraste", "metrica", "diferenca", "percentil_025", "percentil_975")
    with (output / "material_complementar" / "contrastes_condicionais.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(stream, columns)
        writer.writeheader()
        for i, (first, second) in enumerate(PAIRS):
            for j, metric in enumerate(("acuracia_balanceada", "sensibilidade_alta")):
                writer.writerow(
                    dict(
                        zip(
                            columns,
                            [
                                f"{LABELS[first]} menos {LABELS[second]}",
                                metric,
                                point[i, j],
                                intervals[0, i, j],
                                intervals[1, i, j],
                            ],
                            strict=True,
                        )
                    )
                )


def plot_intervals(point, intervals, output):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.15), layout="constrained")
    positions = np.arange(len(PAIRS))
    labels = [f"{LABELS[a]} − {LABELS[b]}" for a, b in PAIRS]
    for j, (ax, title) in enumerate(
        zip(axes, ("Acurácia balanceada", "Sensibilidade da classe alta"), strict=True)
    ):
        ax.axvline(0, color="0.45", linestyle="--", linewidth=1)
        ax.hlines(positions, intervals[0, :, j] * 100, intervals[1, :, j] * 100, color="#23677b")
        ax.scatter(point[:, j] * 100, positions, color="#184654", zorder=3)
        ax.set(
            yticks=positions,
            yticklabels=labels if j == 0 else [""] * len(labels),
            title=title,
            xlabel="Diferença (pontos percentuais)",
        )
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=0.2)
    save_figure(fig, "contrastes_condicionais", output)


def plot_confusion(matrices, output):
    fig, axes = plt.subplots(2, 2, figsize=(8, 6.5), layout="constrained")
    for ax, label, matrix in zip(axes.flat, LABELS, matrices, strict=True):
        values = matrix / matrix.sum(axis=1, keepdims=True)
        ax.imshow(values, vmin=0, vmax=1, cmap="Blues")
        for i, j in np.ndindex(matrix.shape):
            ax.text(
                j,
                i,
                f"{matrix[i, j]:,}\n{values[i, j]:.1%}".replace(",", "."),
                ha="center",
                va="center",
                color="white" if values[i, j] > 0.55 else "#192b35",
            )
        ax.set(
            xticks=range(3),
            xticklabels=CLASSES,
            yticks=range(3),
            yticklabels=CLASSES,
            title=label,
            xlabel="Classe prevista",
            ylabel="Classe observada",
        )
    save_figure(fig, "confusao_classificacao_final", output)


def plot_calibration(output):
    data = pl.read_csv(REPORT / "calibracao_descritiva.csv")
    fig, axes = plt.subplots(
        1, 3, figsize=(10, 3.4), layout="constrained", sharex=True, sharey=True
    )
    for k, ax in enumerate(axes):
        for name, label, style in zip(MODELS, LABELS, ("o-", "s--", "^:", "D-."), strict=True):
            subset = data.filter(
                (pl.col("model") == name) & (pl.col("class_index") == k) & (pl.col("n") > 0)
            )
            ax.plot(
                subset["mean_predicted_probability"],
                subset["observed_fraction"],
                style,
                markersize=3,
                linewidth=1,
                label=label,
            )
        ax.plot([0, 1], [0, 1], "--", color="0.65", linewidth=0.8)
        ax.set(title=CLASSES[k], xlabel="Prob. prevista média", xlim=(0, 1), ylim=(0, 1))
        ax.set_aspect("equal")
    axes[0].set_ylabel("Frequência observada")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center", ncol=4)
    save_figure(fig, "calibracao_classificacao_final", output)


def plot_selection(output):
    reports = ROOT / "reports"
    coverage = pl.read_csv(
        reports / "recuperacao_consolidada_nova_amostra_v1/comparacao_metadados.csv"
    )
    linked = pl.read_csv(reports / "amostra_com_letras_candidata_v2/comparacao_metadados.csv")
    data = coverage.join(
        linked.select("variavel", "desvio_em_dp_catalogo"),
        on="variavel",
        validate="1:1",
        maintain_order="left",
    )
    columns = (
        "desvio_sorteio_em_dp_catalogo",
        "desvio_aceitas_em_dp_catalogo",
        "desvio_em_dp_catalogo",
    )
    labels = (
        "Popularidade",
        "Ano",
        "Dançabilidade",
        "Energia",
        "Intensidade sonora",
        "Fala",
        "Caráter acústico",
        "Instrumentalidade",
        "Vivacidade",
        "Valência",
        "Andamento",
        "Duração",
    )
    data.write_csv(output / "material_complementar" / "comparacao_etapas_selecao.csv")
    fig, ax = plt.subplots(figsize=(9, 4.6), layout="constrained")
    positions = np.arange(data.height)
    ax.axvline(0, color="0.55", linestyle="--", linewidth=1)
    for col, label, marker, color in zip(
        columns,
        ("Sorteio original", "Vínculos aceitos do sorteio", "Coorte com letras"),
        ("o", "s", "D"),
        ("#525763", "#b05b33", "#23677b"),
        strict=True,
    ):
        ax.scatter(data[col], positions, label=label, marker=marker, color=color)
    ax.set(yticks=positions, yticklabels=labels, xlabel="Diferença em desvios-padrão do catálogo")
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.2)
    fig.legend(*ax.get_legend_handles_labels(), loc="outside lower center", ncol=3)
    save_figure(fig, "selecao_metadados_final", output)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, default=OUT, help="Pasta dos agregados e figuras.")
    parser.add_argument("--semente", type=int, default=SEED, help="Semente do bootstrap.")
    parser.add_argument(
        "--somente-contrastes", action="store_true", help="Atualiza apenas o bootstrap."
    )
    args = parser.parse_args()
    report = json.loads((REPORT / "resumo_classificacao.json").read_text(encoding="utf-8"))
    with PREDICTIONS.open("rb") as stream:
        seal = file_digest(stream, "sha256").hexdigest()
    if not report["completed"] or seal != report["prediction_sha256"]:
        raise ValueError("Previsões externas sem selo válido.")
    data = pl.read_parquet(PREDICTIONS)
    by_group = data.group_by("text_component_id").agg(pl.col("outer_fold").n_unique())
    if (
        data.height != data["track_id"].n_unique()
        or data.height != report["sample_tracks"]
        or by_group.height != report["components"]
        or by_group["outer_fold"].max() != 1
    ):
        raise ValueError("Faixas ou componentes divergentes.")
    observed = data["observed_class"].to_numpy()
    if np.bincount(observed, minlength=3).tolist() != report["class_counts"]:
        raise ValueError("Contagens de classe divergentes.")
    groups = np.unique(data["text_component_id"].to_numpy(), return_inverse=True)[1]
    totals = np.zeros((by_group.height, 3), dtype=np.int32)
    np.add.at(totals, (groups, observed), 1)
    hits = np.zeros((by_group.height, len(MODELS), 3), dtype=np.int32)
    matrices = []
    for m, name in enumerate(MODELS):
        prob = data.select([f"{name}_probability_{i}" for i in range(3)]).to_numpy()
        if not np.isfinite(prob).all() or (prob < 0).any() or not np.allclose(prob.sum(axis=1), 1):
            raise ValueError(f"Probabilidades inválidas para {name}.")
        predicted = prob.argmax(axis=1)
        matrix = np.bincount(3 * observed + predicted, minlength=9).reshape(3, 3)
        matrices.append(matrix)
        np.add.at(hits, (groups, m, observed), observed == predicted)
    aggregate = hits.sum(axis=0)
    baseline_table = pl.read_csv(REPORT / "metricas_externas.csv").filter(
        (pl.col("outer_fold") == -1) & (pl.col("weighting") == "equal_tracks")
    )
    for m, name in enumerate(MODELS):
        expected = baseline_table.filter(pl.col("model") == name)["balanced_accuracy"].item()
        if not np.isclose(expected, (aggregate[m] / totals.sum(axis=0)).mean(), atol=1e-12, rtol=0):
            raise ValueError(f"Acurácia balanceada divergente para {name}.")
    (args.destino / "images").mkdir(parents=True, exist_ok=True)
    (args.destino / "material_complementar").mkdir(exist_ok=True)
    point = conditional_differences(totals.sum(axis=0), aggregate)
    intervals = bootstrap(totals, hits, args.semente)
    write_intervals(point, intervals, args.destino)
    plot_intervals(point, intervals, args.destino)
    if not args.somente_contrastes:
        plot_confusion(matrices, args.destino)
        plot_calibration(args.destino)
        plot_selection(args.destino)


if __name__ == "__main__":
    main()
