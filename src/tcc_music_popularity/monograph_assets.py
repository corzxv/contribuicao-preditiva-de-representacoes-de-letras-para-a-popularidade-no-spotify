"""Tabelas/figuras da monografia a partir de agregados existentes, sem dados individuais."""

import argparse
import csv
import hashlib
import json
import re
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROJECT = ROOT / "reports/monografia_consolidada_200k_v1"
LABELS = {
    "baseline": "Baseline",
    "traditional": "Tradicional",
    "deep": "Profundo",
    "combined": "Combinado",
    "mean": "Média do treino",
    "median": "Mediana do treino",
}
ORDER = ("baseline", "traditional", "deep", "combined")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def tex(value):
    translations = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "–": "--",
        "−": "-",
        "—": "---",
    }
    return "".join(translations.get(c, c) for c in str(value))


def number(value, digits=4):
    return f"{float(value):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def csv_rows(path):
    if path.stat().st_size > 12 * 1024 * 1024:
        raise ValueError("Agregado excede orçamento leve")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        result = list(csv.DictReader(stream))
    if len(result) > 70000:
        raise ValueError("Agregado excede limite de linhas")
    return result


def write_table(path, caption, label, headers, rows, note="", widths=None):
    columns = widths or ("l" + "r" * (len(headers) - 1))
    content = [
        r"\begin{table}[htbp]",
        r"\centering\small",
        r"\caption{" + caption + "}",
        r"\label{" + label + "}",
        r"\begin{tabular}{" + columns + "}",
        r"\toprule",
        " & ".join(tex(h) for h in headers) + r" \\",
        r"\midrule",
    ]
    content += [" & ".join(tex(c) for c in row) + r" \\" for row in rows]
    content += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\fonte{Elaboração própria a partir dos agregados auditados do estudo.}",
    ]
    if note:
        content += [r"\nota{" + note + "}"]
    content += [r"\end{table}"]
    path.write_text("\n".join(content) + "\n", encoding="utf-8")


def assets(project=DEFAULT_PROJECT):
    if not (project / "main.tex").exists():
        raise ValueError("Criar primeiro o projeto LaTeX dedicado")
    for name in ("tables", "images", "source_data"):
        (project / name).mkdir(exist_ok=True)
    manifest = project / "PROVENIENCIA_AGREGADOS.json"
    if manifest.exists():
        old = json.loads(manifest.read_text(encoding="utf-8"))
        for name, digest in old["generated_files"].items():
            if sha(project / name) != digest:
                raise ValueError(f"Artefato editado manualmente: {name}; preservar")
    used = {}

    def load(name, is_json=False):
        path = ROOT / name
        used[name] = sha(path)
        return json.loads(path.read_text(encoding="utf-8")) if is_json else csv_rows(path)

    global_metrics = load("reports/modelagem_200k_v1/integral/metricas_externas.csv")
    contrasts = load("reports/modelagem_200k_v1/integral/incrementos_pareados.csv")
    subgroups = load("reports/diagnosticos_modelagem_200k_v1/diagnosticos_subgrupos.csv")
    clip = load("reports/fechamento_metodologico_200k_v1/metrics_and_clipping.csv")
    tail = load("reports/fechamento_metodologico_200k_v1/tail_residuals.csv")
    intervals = load(
        "reports/fechamento_metodologico_200k_v1/intervalos_condicionais_combinados.csv"
    )
    hist = load("reports/fechamento_metodologico_200k_v1/tail_residual_histogram.csv")
    deletion = load("reports/diagnosticos_modelagem_200k_v1/sensibilidade_remocao_componente.csv")
    alphas = load("reports/modelagem_200k_v1/integral/alphas_selecionados.csv")
    reference = load("reports/parecer_letras_v2/catalogo_amostra_referencia.csv")
    distribution = load("reports/parecer_letras_v2/distribuicoes_quantis_qualidade.csv")
    recovery = load("reports/recuperacao_letras_200k_v2/resumo_recuperacao_letras_200k.json", True)
    sample = load("reports/amostra_spotify_200k_20261031/resumo_amostra_200k.json", True)
    for name in (
        "reports/prontidao_dados_200k_v1/resumo_prontidao.json",
        "reports/descritores_textuais_200k_v1/resumo_descritores.json",
        "reports/embeddings_multilingues_200k_v1/integral/resumo_embeddings.json",
        "reports/base_modelagem_200k_v1/resumo_base_modelagem.json",
        "reports/fechamento_metodologico_200k_v1/auditoria_representacoes.json",
        "reports/fechamento_metodologico_200k_v1/desvio_prefixo_sintetico.json",
    ):
        load(name, True)
    if (
        sum(recovery["status_counts"].values()) != 200000
        or recovery["status_counts"]["accepted"] != 77535
    ):
        raise ValueError("Contagens divergem da coorte congelada")
    table = project / "tables"
    write_table(
        table / "metricas.tex",
        "Desempenho nas previsões externas reunidas ($n=77.535$).",
        "tab:metricas",
        ["Configuração", "MAE", "RMSE", "R²", "MAE ponderado"],
        [
            [
                LABELS[r["model"]],
                *[number(r[c]) for c in ("mae", "rmse", "r2", "mae_original_weight")],
            ]
            for r in global_metrics
        ],
        "Pesos iguais no ajuste e na avaliação principal. Última coluna: sensibilidade com pesos originais nas mesmas previsões; não houve retreino ponderado.",
    )
    write_table(
        table / "contrastes.tex",
        "Diferenças pareadas de MAE entre configurações.",
        "tab:contrastes",
        ["Contraste", "Pesos iguais", "Pesos originais"],
        [
            [
                LABELS[r["block"]] + " - " + LABELS[r["reference"]],
                number(r["delta_mae"], 5),
                number(r["delta_mae_original_weight"], 5),
            ]
            for r in contrasts
        ],
        "Diferença negativa favorece a primeira configuração; são contrastes observados, sem inferência integral de treinamento.",
    )
    write_table(
        table / "folds.tex",
        "MAE por avaliação externa nos mesmos componentes.",
        "tab:folds",
        ["Fold", *[LABELS[m] for m in ORDER]],
        [
            [
                str(f + 1),
                *[
                    number(
                        next(
                            r["mae"]
                            for r in subgroups
                            if r["dimension"] == "outer_fold"
                            and r["level"] == str(f)
                            and r["model"] == m
                        )
                    )
                    for m in ORDER
                ],
            ]
            for f in range(5)
        ],
        "A numeração 1--5 corresponde a 0--4 nos arquivos. Folds não são réplicas independentes.",
    )
    write_table(
        table / "incerteza.tex",
        "Limites auxiliares condicionais para os contrastes de interesse.",
        "tab:incerteza",
        ["Contraste", "Avaliação", "Delta", "Inferior", "Superior"],
        [
            [
                "C - " + ("B" if r["contrast"].endswith("baseline") else "P"),
                "Iguais" if r["weighting"] == "equal_tracks" else "Originais",
                *[
                    number(r[k], 5)
                    for k in (
                        "delta_mae",
                        "conditional_bonferroni_lower",
                        "conditional_bonferroni_upper",
                    )
                ],
            ]
            for r in intervals
        ],
        "C: Combinado; B: Baseline; P: Profundo. 95\\% nominais sob modelo auxiliar de componentes, com Bonferroni por família de dez marginais. Não são ICs da pipeline integral.",
    )
    write_table(
        table / "clipping.tex",
        "Projeção de suporte como sensibilidade pós-resultado.",
        "tab:clipping",
        ["Configuração", "Abaixo de 0", "Acima de 100", "MAE original", "MAE projetado"],
        [
            [
                LABELS[r["model"]],
                r["below_zero"],
                r["above_100"],
                number(r["mae_original"], 5),
                number(r["mae_clipped_sensitivity"], 5),
            ]
            for r in clip
            if r["scope"] == "all"
        ],
        "Projeção fixa em [0,100], sem substituir as previsões ou métricas principais.",
    )
    write_table(
        table / "cauda.tex",
        "Previsões nas 128 faixas com popularidade observada de 80 a 100.",
        "tab:cauda",
        ["Configuração", "Previsão média", "MAE", "RMSE", "Subestimadas"],
        [
            [
                LABELS[r["model"]],
                number(r["prediction_mean"]),
                number(r["mae_original"]),
                number(r["rmse_original"]),
                r["underpredictions"],
            ]
            for r in tail
        ],
        "Média observada: 81,8125. Há 96 componentes; a faixa efetivamente observada vai de 80 a 96.",
    )
    status_labels = {
        "accepted": "Aceitas",
        "not_found": "Não encontradas",
        "ambiguous": "Ambíguas",
        "instrumental": "Instrumentais",
        "no_text": "Sem texto",
        "insufficient_metadata": "Metadados insuficientes",
    }
    write_table(
        table / "cobertura.tex",
        "Destino das faixas da amostra após a recuperação textual v2.",
        "tab:cobertura",
        ["Situação", "Faixas", "Percentual da amostra"],
        [
            [
                label,
                number(recovery["status_counts"][s], 0),
                number(recovery["status_counts"][s] / 2000, 4) + "%",
            ]
            for s, label in status_labels.items()
        ],
        "Total de 200.000 registros; zero erro técnico ou pendência. As não aceitas permanecem na base de cobertura.",
    )

    def value(rows, scope, metric):
        matches = [
            r
            for r in rows
            if r["scope"] == scope
            and r["variable"] == "popularity"
            and r["section"] == "numeric_all_finite"
            and r["metric"] == metric
        ]
        if len(matches) != 1:
            raise ValueError("Métrica descritiva ausente/ambígua")
        return matches[0]["value"]

    descriptive = []
    for rows, scope, label, n in (
        (reference, "catalogo", "Catálogo", 1159764),
        (reference, "amostra_sem_pesos", "Amostra, sem pesos", 200000),
        (reference, "amostra_com_pesos", "Amostra, ponderada", 200000),
        (distribution, "accepted|unweighted", "Aceitas, sem pesos", 77535),
        (distribution, "accepted|weighted", "Aceitas, ponderadas", 77535),
    ):
        descriptive.append(
            [
                label,
                number(n, 0),
                number(value(rows, scope, "mean"), 4),
                *[number(value(rows, scope, m), 0) for m in ("q25", "q50", "q75")],
            ]
        )
    write_table(
        table / "descritivas.tex",
        "Popularidade observada: catálogo, amostra e domínio com letras aceitas.",
        "tab:descritivas",
        ["Universo / avaliação", "n", "Média", "P25", "Mediana", "P75"],
        descriptive,
        "Quantis pela inversa da distribuição empírica, ponderada quando indicado. n conta faixas, não soma de pesos.",
    )
    languages = (
        ("english", "Inglês estimado"),
        ("non_english", "Não inglês estimado"),
        ("uncertain", "Idioma incerto"),
    )
    write_table(
        table / "idiomas.tex",
        "Desempenho por status do idioma estimado.",
        "tab:idiomas",
        ["Status", "n", "Baseline", "Profundo", "Combinado"],
        [
            [
                label,
                number(
                    next(
                        r["n"]
                        for r in subgroups
                        if r["dimension"] == "lyrics_language_status" and r["level"] == code
                    ),
                    0,
                ),
                *[
                    number(
                        next(
                            r["mae"]
                            for r in subgroups
                            if r["dimension"] == "lyrics_language_status"
                            and r["level"] == code
                            and r["model"] == m
                        )
                    )
                    for m in ("baseline", "deep", "combined")
                ],
            ]
            for code, label in languages
        ],
        "Idioma automático não é rótulo humano. Diagnóstico exploratório sem excluir casos.",
    )
    write_table(
        table / "alphas.tex",
        "Parâmetro de penalização selecionado internamente.",
        "tab:alphas",
        ["Fold", *[LABELS[m] for m in ORDER]],
        [
            [
                str(f + 1),
                *[
                    number(
                        next(
                            r["alpha"]
                            for r in alphas
                            if r["outer_fold"] == str(f) and r["block"] == m
                        ),
                        1,
                    )
                    for m in ORDER
                ],
            ]
            for f in range(5)
        ],
        "A grade foi fixada antes dos resultados externos; não foi expandida após observar escolhas no extremo.",
    )
    write_table(
        table / "remocao.tex",
        "Influência da retirada de um componente apenas da avaliação.",
        "tab:remocao",
        ["Contraste", "Delta", "Menor delta", "Maior delta"],
        [
            [
                LABELS[r["block"]] + " - " + LABELS[r["reference"]],
                *[
                    number(r[k], 5)
                    for k in (
                        "delta_mae",
                        "min_delta_after_component_deletion",
                        "max_delta_after_component_deletion",
                    )
                ],
            ]
            for r in deletion
        ],
        "Modelos e previsões fixos. Extremos não são limites de confiança nem validação com refit.",
    )
    # Dados efetivamente usados ficam junto ao manuscrito, sem incluir tabelas individuais.
    for name, rows in {
        "metricas": global_metrics,
        "contrastes": contrasts,
        "subgrupos": subgroups,
        "clipping": clip,
        "cauda": tail,
        "intervalos": intervals,
        "histograma_residuos_cauda": hist,
    }.items():
        with (project / "source_data" / (name + ".csv")).open(
            "w", encoding="utf-8", newline=""
        ) as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    # Reusar somente as figuras do domínio recente, sem alterações no pacote original.
    for name in ("comparacao_global", "estabilidade_folds", "erro_popularidade", "erro_idioma"):
        for suffix in (".png", ".svg"):
            source = ROOT / "reports/overleaf_dominio_observado_200k_v1/images" / (name + suffix)
            used[str(source.relative_to(ROOT))] = sha(source)
            shutil.copy2(source, project / "images" / source.name)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )

    def save(fig, name):
        fig.savefig(project / "images" / (name + ".png"), dpi=300, bbox_inches="tight")
        fig.savefig(project / "images" / (name + ".svg"), bbox_inches="tight")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.1))
    for rows, scope, label, color in (
        (reference, "catalogo", "Catálogo", "#68737f"),
        (reference, "amostra_com_pesos", "Amostra ponderada", "#235f93"),
        (distribution, "accepted|unweighted", "Aceitas sem pesos", "#be5e2f"),
    ):
        points = sorted(
            (int(r["category"]), float(r["value"]))
            for r in rows
            if r["scope"] == scope
            and r["section"] == "distribution"
            and r["variable"] == "_s_pop"
            and r["metric"] == "fraction"
        )
        total = 0.0
        ys = []
        for _, fraction in points:
            total += fraction
            ys.append(total)
        ax.step([x for x, _ in points], ys, where="post", label=label, color=color, lw=1.8)
    ax.set(
        xlabel="Popularidade observada",
        ylabel="Frequência relativa acumulada",
        xlim=(0, 100),
        ylim=(0, 1.015),
    )
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: number(x, 1)))
    ax.legend(loc="lower right", frameon=False)
    ax.grid(alpha=0.16)
    fig.tight_layout()
    save(fig, "distribuicao_popularidade")
    complete = {
        r["category"]: float(r["value"])
        for r in distribution
        if r["scope"] == "complete|unweighted"
        and r["section"] == "distribution"
        and r["variable"] == "_s_band"
        and r["metric"] == "n_observed"
    }
    accepted = {
        r["category"]: float(r["value"])
        for r in distribution
        if r["scope"] == "accepted|unweighted"
        and r["section"] == "distribution"
        and r["variable"] == "_s_band"
        and r["metric"] == "n_observed"
    }
    bands = sorted(complete, key=lambda s: int(re.search(r"\d+", s)[0]))
    rates = [100 * accepted.get(b, 0) / complete[b] for b in bands]
    fig, ax = plt.subplots(figsize=(8, 3.7))
    ax.bar([b.replace("–", "-") for b in bands], rates, color="#235f93", width=0.65)
    ax.set(
        xlabel="Banda da popularidade observada",
        ylabel="Letras aceitas (%)",
        ylim=(0, max(rates) * 1.22),
    )
    for i, _band in enumerate(bands):
        ax.text(i, rates[i] + 0.8, number(rates[i], 1) + "%", ha="center", fontsize=10)
    fig.tight_layout()
    save(fig, "cobertura_bandas")
    chosen = [r for r in hist if r["model"] == "combined" and int(r["n"]) > 0]
    fig, ax = plt.subplots(figsize=(8, 3.7))
    ax.bar(range(len(chosen)), [int(r["n"]) for r in chosen], color="#be5e2f", width=0.7)
    ax.set_xticks(
        range(len(chosen)),
        [f"[{int(float(r['bin_left']))}, {int(float(r['bin_right']))})" for r in chosen],
    )
    ax.set(xlabel="Intervalo do resíduo: previsão - observado", ylabel="Faixas", ylim=(0, 47))
    for i, r in enumerate(chosen):
        ax.text(i, int(r["n"]) + 0.7, r["n"], ha="center")
    fig.tight_layout()
    save(fig, "residuos_cauda")
    fig, ax = plt.subplots(figsize=(8, 3.4))
    positions = list(range(4))
    for i, r in enumerate(intervals):
        center = float(r["delta_mae"])
        lo = float(r["conditional_bonferroni_lower"])
        hi = float(r["conditional_bonferroni_upper"])
        ax.errorbar(
            center,
            i,
            xerr=[[center - lo], [hi - center]],
            fmt="o",
            color="#235f93" if i < 2 else "#be5e2f",
            capsize=4,
        )
    ax.set_yticks(
        positions,
        [
            "C - Baseline, iguais",
            "C - Profundo, iguais",
            "C - Baseline, originais",
            "C - Profundo, originais",
        ],
    )
    ax.axvline(0, color="#6b737b", lw=1)
    ax.set_xlabel("Diferença de MAE e limites auxiliares condicionais")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: number(x, 2)))
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.16)
    fig.tight_layout()
    save(fig, "limites_condicionais")
    # Manifesto de todos os arquivos gerados; não controla a escrita autoral dos capítulos.
    generated = {
        str(p.relative_to(project)).replace("\\", "/"): sha(p)
        for sub in ("tables", "images", "source_data")
        for p in (project / sub).iterdir()
        if p.is_file()
    }
    manifest.write_text(
        json.dumps(
            {
                "inputs": used,
                "generated_files": generated,
                "individual_data_read": False,
                "models_trained": False,
                "generator_sha256": sha(Path(__file__)),
                "sample_allocation_strata": sample["allocation_summary"]["strata"],
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
                "completed": True,
                "tables": len(list(table.glob("*.tex"))),
                "figures": len(list((project / "images").glob("*.png"))),
                "models_trained": False,
            }
        )
    )


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    args = parser.parse_args()
    assets(args.project)


if __name__ == "__main__":
    cli()
