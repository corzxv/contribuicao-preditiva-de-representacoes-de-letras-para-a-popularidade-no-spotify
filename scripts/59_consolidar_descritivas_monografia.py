"""Consolida agregados leves para o corpo da monografia revisada."""

import json
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUT = REPORTS / "monografia_template_revisada"
MATERIAL = OUT / "material_complementar"
CATALOG = REPORTS / "descritiva_catalogo_completo_v1"
PROCESSED = ROOT / "data/processed"
PRIVATE = ROOT / "data/derived/private_vinculos_consolidados_nova_amostra_v1"
SIZES = [5548, 2919, 1059]


def report(folder, name):
    return json.loads((REPORTS / folder / name).read_text(encoding="utf-8"))


def verified(path, expected):
    if sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"Selo divergente em {path.name}.")
    return path


def save(fig, name, output=OUT):
    for suffix in ("png", "svg"):
        fig.savefig(output / "images" / f"{name}.{suffix}", dpi=180, bbox_inches="tight")
    plt.close(fig)


def pt(value, digits=0):
    return f"{value:,.{digits}f}".translate(str.maketrans(".,", ",."))


def note(stream, caption, label, columns, head):
    stream.write(
        r"\begin{table}[H]\centering\small"
        + "\n"
        + r"\caption{"
        + caption
        + r"}\label{"
        + label
        + "}\n"
        + r"\begin{tabular}{"
        + columns
        + r"}\toprule"
        + "\n"
        + " & ".join(head)
        + r" \\\midrule"
        + "\n"
    )


def row(stream, cells):
    stream.write(" & ".join(cells) + r" \\" + "\n")


def finish(stream, source):
    stream.write(r"\bottomrule\end{tabular}\fonte{" + source + "}\n" + r"\end{table}" + "\n")


def sample_audit():
    sample = report("nova_amostra_catalogo_v1", "resumo_sorteio.json")
    cohort = report("amostra_com_letras_candidata_v2", "resumo_amostra_candidata.json")
    links = report("recuperacao_consolidada_nova_amostra_v1", "resumo_cobertura.json")
    fitted = report("classificacao_9526_v1", "resumo_classificacao.json")
    inputs = {
        "original": (
            PROCESSED / "nova_amostra_catalogo_v1/amostra_spotify.parquet",
            sample["parquet_sha256"],
        ),
        "coorte": (
            PROCESSED / "private_amostra_com_letras_candidata_v2/amostra_candidata_9526.parquet",
            cohort["private_sample_sha256"],
        ),
        "vinculos": (PRIVATE / "vinculos_e_status.parquet", links["private_manifest_sha256"]),
    }
    original, selected, manifest = [
        pl.read_parquet(verified(path, seal), columns=columns)
        for (path, seal), columns in zip(
            inputs.values(),
            (
                ["track_id", "popularity"],
                [
                    "track_id",
                    "popularity",
                    "source_stage",
                    "source_text_parquet",
                    "query_id",
                    "text_sha256",
                ],
                ["track_id", "lyrics_status"],
            ),
            strict=True,
        )
    ]
    accepted = manifest.filter(pl.col("lyrics_status") == "accepted")
    shared = selected.join(accepted.select("track_id"), on="track_id", how="semi").height
    assert (
        original.height == manifest.height == selected.height == fitted["prediction_rows"] == 9526
        and all(d["track_id"].n_unique() == d.height for d in (original, selected, manifest))
        and manifest.join(original.select("track_id"), on="track_id", how="anti").is_empty()
        and selected.join(original.select("track_id"), on="track_id", how="semi").height == shared
        and accepted.height == links["counts"]["accepted"] == 3869
    )
    data = {
        "catalogo": sample["N"],
        "sorteio_original": original.height,
        "letras_aceitas_do_sorteio": accepted.height,
        "quadro_com_letras": cohort["frame_tracks"],
        "coorte_classificada": selected.height,
        "faixas_do_sorteio_presentes_na_coorte": shared,
        "faixas_da_coorte_fora_do_sorteio": selected.height - shared,
        "faixas_da_coorte_historica": fitted["known_prior_cohort_overlap"],
        "class_counts": fitted["class_counts"],
    }
    (MATERIAL / "trajetoria_amostras.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(data)
    return original, selected, cohort


def plot_popularity(original, cohort):
    fig, axes = plt.subplots(2, 1, figsize=(8.4, 5.1), sharex=True, layout="constrained")
    for axis, data, title, color in zip(
        axes,
        (original, cohort),
        ("Sorteio do catálogo", "Coorte com letra"),
        ("#537783", "#315e7a"),
        strict=True,
    ):
        values = data["popularity"].cast(pl.Int64).to_numpy()
        assert ((values >= 0) & (values <= 100)).all()
        assert np.bincount(np.digitize(values, [20, 40]), minlength=3).tolist() == SIZES
        axis.bar(
            np.arange(101),
            np.bincount(values, minlength=101) / len(values) * 100,
            color=color,
            width=0.85,
        )
        for cutoff in (20, 40):
            axis.axvline(cutoff - 0.5, color="#a25336", linestyle="--", linewidth=1)
        axis.set(ylabel="Faixas (%)", title=title)
        axis.grid(axis="y", alpha=0.18)
    axes[1].set(xlabel="Escore observado de popularidade", xlim=(-1, 101))
    save(fig, "popularidade_sorteio_coorte")


def formats(selected, cohort):
    summaries = []
    for (source,), group in selected.partition_by("source_text_parquet", as_dict=True).items():
        path = verified(ROOT / source, cohort["text_sources_sha256"][source])
        indicators = (
            pl.scan_parquet(path)
            .filter(pl.col("query_id").is_in(group["query_id"].unique().implode()))
            .select(
                "query_id",
                "text_sha256",
                (pl.col("plain_text_source").fill_null("").str.strip_chars() != "").alias(
                    "simples"
                ),
                (pl.col("synced_text_source").fill_null("").str.strip_chars() != "").alias(
                    "sincronizada"
                ),
            )
            .collect()
        )
        joined = group.select("query_id", "text_sha256").join(
            indicators, on=["query_id", "text_sha256"], how="left", validate="m:1"
        )
        assert joined.height == group.height and not joined["simples"].has_nulls()
        summaries.append(joined.select("simples", "sincronizada"))
    counts = pl.concat(summaries).group_by("simples", "sincronizada").len()
    assert counts["len"].sum() == selected.height
    counts.sort("simples", "sincronizada").write_csv(MATERIAL / "formatos_lrclib_coorte.csv")
    names = {
        (True, False): "Somente simples",
        (False, True): "Somente sincronizada",
        (True, True): "Simples e sincronizada",
        (False, False): "Campos de origem vazios",
    }
    counts_by_type = {(plain, synced): n for plain, synced, n in counts.iter_rows()}
    print("Formatos nos vínculos:", counts_by_type)
    with (OUT / "tables/formatos_coorte.tex").open("w", encoding="utf-8") as stream:
        note(
            stream,
            "Formatos presentes nos registros de origem das letras usadas na modelagem.",
            "tab:formatos_coorte",
            "lrr",
            ("Formato registrado", "Faixas", r"Percentual (\%)"),
        )
        for key, label in names.items():
            n = counts_by_type.get(key, 0)
            if n or key != (False, False):
                row(stream, (label, pt(n), pt(100 * n / selected.height, 2)))
        row(stream, ("Total", pt(selected.height), "100,00"))
        finish(
            stream,
            "Elaboração própria a partir dos vínculos selados. Denominador por faixa Spotify.",
        )


def plot_genres(output=OUT, *, compact=False):
    variables = (
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
    )
    labels = (
        "Dançabilidade",
        "Energia",
        "Intensidade sonora",
        "Presença de fala",
        "Caráter acústico",
        "Instrumentalidade",
        "Indício ao vivo",
        "Valência",
        "Andamento",
        "Duração",
    )
    if compact:
        labels = (
            "Danç.",
            "Energia",
            "Intens.",
            "Fala",
            "Acúst.",
            "Instr.",
            "Ao vivo",
            "Valência",
            "BPM",
            "Duração",
        )
    profile = pl.read_csv(CATALOG / "perfis_grupos.csv").filter(pl.col("agrupamento") == "genre")
    stats = pl.read_csv(CATALOG / "resumo_numerico.csv").filter(pl.col("escopo") == "regra_local")
    scale = {
        v: (mean, sd)
        for v, mean, sd in stats.select("variavel", "media", "dp_populacional").iter_rows()
    }
    values = {
        (g, v): (mean - scale[v][0]) / scale[v][1]
        for g, v, mean in profile.select("categoria", "variavel", "media").iter_rows()
        if v in variables
    }
    genres = sorted(profile["categoria"].unique().to_list())
    assert len(genres) == 82
    for i in range(2):
        group = genres[i * 41 : (i + 1) * 41]
        matrix = np.array([[values[g, v] for v in variables] for g in group])
        size = (3.3, 5.4) if compact else (8.8, 8.8)
        font_size = 6.6 if compact else 9
        fig, ax = plt.subplots(figsize=size, layout="constrained")
        pic = ax.imshow(matrix, cmap="RdBu_r", vmin=-2, vmax=2, aspect="auto")
        ax.set_xticks(
            range(len(labels)),
            labels,
            rotation=55 if compact else 38,
            ha="right",
            fontsize=font_size,
        )
        ax.set_yticks(range(len(group)), group, fontsize=font_size)
        ax.tick_params(length=0)
        colorbar = fig.colorbar(
            pic,
            ax=ax,
            shrink=0.8,
            label="" if compact else "Diferença / desvio-padrão do catálogo",
            ticks=np.arange(-2, 3) if compact else None,
            format=FuncFormatter(lambda x, _: pt(x, 0 if compact else 1)),
        )
        if compact:
            colorbar.ax.tick_params(labelsize=font_size)
        save(fig, f"perfil_generos_{i + 1}", output)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paineis-compactos",
        type=Path,
        metavar="PASTA",
        help="Gera somente os dois painéis compactos no destino.",
    )
    args = parser.parse_args()
    if args.paineis_compactos:
        (args.paineis_compactos / "images").mkdir(parents=True, exist_ok=True)
        plot_genres(args.paineis_compactos, compact=True)
        return
    original, linked, summary = sample_audit()
    formats(linked, summary)
    plot_popularity(original, linked)
    plot_genres()


if __name__ == "__main__":
    main()
