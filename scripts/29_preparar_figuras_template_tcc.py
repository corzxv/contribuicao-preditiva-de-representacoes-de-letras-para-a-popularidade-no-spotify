"""Prepara ilustrações editoriais limitadas, exclusivamente de agregados concluídos."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "reports/monografia_template_200k_v2"
PREVIOUS = ROOT / "reports/monografia_consolidada_200k_v1"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_aggregate(path):
    if path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("Entrada excede o orçamento editorial de 4 MiB")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def prepare(project=PROJECT):
    if not (project / "main.tex").is_file():
        raise ValueError("Criar primeiro o projeto LaTeX")
    for folder in ("images", "tables", "source_data"):
        (project / folder).mkdir(exist_ok=True)
    manifest = project / "proveniencia_figuras.json"
    if manifest.exists():
        previous = read_aggregate(manifest)
        for name, expected in previous["generated"].items():
            if digest(project / name) != expected:
                raise ValueError(f"Preservar edição manual em {name}")
    audit_path = ROOT / "reports/auditoria_catalogo_spotify_20261031/resumo_catalogo_spotify.json"
    sample_path = ROOT / "reports/amostra_spotify_200k_20261031/resumo_amostra_200k.json"
    audit, sample = read_aggregate(audit_path), read_aggregate(sample_path)
    scope = audit["scopes"]["linha"]
    genres, years = sample["catalog_counts"]["genres"], sample["catalog_counts"]["years"]
    total = audit["structure"]["rows"]
    if total != 1159764 or sum(genres.values()) != total or sum(years.values()) != total:
        raise ValueError("Totais agregados incompatíveis com o catálogo congelado")
    inputs = {str(p.relative_to(ROOT)): digest(p) for p in (audit_path, sample_path)}
    profile = {
        "n": total,
        "identity": scope["identity"],
        "popularity": scope["popularity"],
        "genres": genres,
        "years": years,
        "periods": scope["periods"],
        "artist_concentration": scope["artist_concentration"],
        "versions": scope["versions"],
        "acoustic": {k: v["all_finite_summary"] for k, v in scope["acoustic"].items()},
    }
    (project / "source_data/perfil_catalogo.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    def pt_number(value):
        return f"{value:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")

    acoustic_table = [
        r"\begin{table}[htbp]\centering\small",
        r"\caption{Atributos acústicos e duração no catálogo Spotify.}\label{tab:acusticas}",
        r"\begin{tabular}{lrrrrr}\toprule",
        r"Variável & Média & Desvio & P25 & Mediana & P75 \\\midrule",
    ]
    for key in (
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
    ):
        summary = profile["acoustic"][key]
        scale = 1000 if key == "duration_ms" else 1
        label = "Duração (s)" if key == "duration_ms" else key
        acoustic_table.append(
            label
            + " & "
            + " & ".join(
                pt_number(summary[metric] / scale)
                for metric in ("mean", "std_sample", "q25", "median", "q75")
            )
            + r" \\"
        )
    acoustic_table += [
        r"\bottomrule\end{tabular}",
        r"\fonte{Elaboração própria a partir da auditoria. $n=1.159.764$ por variável; valores finitos da fonte, incluindo tempo zero. Desvio com divisor $N-1$.}",
        r"\end{table}",
    ]
    (project / "tables/spotify_acusticas.tex").write_text(
        "\n".join(acoustic_table) + "\n", encoding="utf-8"
    )
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    bands = scope["popularity_bands"]
    if sum(row["n"] for row in bands) != total:
        raise ValueError("Bandas não reconciliam com o total do catálogo")
    labels = [str(r["band"]).replace("–", "-") for r in bands]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.55), layout="constrained")
    axes[0].bar(labels, [100 * r["n"] / total for r in bands], color="#315e7a")
    axes[0].set(
        xlabel="Popularidade observada",
        ylabel="Faixas (%)",
        title="(a) Distribuição da popularidade",
    )
    axes[0].tick_params(axis="x", rotation=55)
    ordered_years = sorted(years)
    axes[1].bar(
        [int(y) for y in ordered_years], [years[y] / 1000 for y in ordered_years], color="#477c75"
    )
    axes[1].set(
        xlabel="Campo year da fonte", ylabel="Faixas (mil)", title="(b) Distribuição do campo year"
    )
    axes[1].set_xticks([2000, 2005, 2010, 2015, 2020, 2023])
    for extension in ("png", "svg"):
        fig.savefig(project / f"images/spotify_panorama.{extension}", dpi=300)
    plt.close(fig)
    top = sorted(genres.items(), key=lambda pair: (-pair[1], pair[0]))[:12][::-1]
    fig, axis = plt.subplots(figsize=(8.4, 4), layout="constrained")
    axis.barh([k for k, _ in top], [100 * n / total for _, n in top], color="#315e7a")
    axis.set(xlabel="Participação no catálogo (%)")
    axis.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))
    for i, (_, count) in enumerate(top):
        axis.text(
            100 * count / total + 0.018, i, f"{count:,}".replace(",", "."), va="center", fontsize=8
        )
    axis.set_xlim(0, 2.12)
    for extension in ("png", "svg"):
        fig.savefig(project / f"images/spotify_generos.{extension}", dpi=300)
    plt.close(fig)
    for name in (
        "distribuicao_popularidade",
        "cobertura_bandas",
        "erro_popularidade",
    ):
        for extension in ("png", "svg"):
            source = PREVIOUS / f"images/{name}.{extension}"
            shutil.copyfile(source, project / f"images/{name}.{extension}")
            inputs[str(source.relative_to(ROOT))] = digest(source)
    for name in (
        "metricas",
        "incerteza",
        "clipping",
        "descritivas",
        "cobertura",
        "idiomas",
    ):
        source = PREVIOUS / f"tables/{name}.tex"
        content = (
            source.read_text(encoding="utf-8-sig")
            .replace("R²", "$R^2$")
            .replace("textual v2", "textual")
        )
        (project / f"tables/{name}.tex").write_text(content, encoding="utf-8")
        inputs[str(source.relative_to(ROOT))] = digest(source)
    generated = {
        str(p.relative_to(project)).replace("\\", "/"): digest(p)
        for folder in ("images", "tables", "source_data")
        for p in (project / folder).iterdir()
        if p.is_file() and p.name != "unb.png"
    }
    manifest.write_text(
        json.dumps(
            {
                "inputs": inputs,
                "generated": generated,
                "generator_sha256": digest(Path(__file__)),
                "individual_data_read": False,
                "new_model_fits": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "catalog_tracks": total,
                "genres": len(genres),
                "years": len(years),
                "new_figures": 2,
                "reused_figures": 3,
                "new_model_fits": 0,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT)
    prepare(parser.parse_args().project.resolve())
