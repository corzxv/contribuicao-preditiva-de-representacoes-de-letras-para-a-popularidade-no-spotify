"""Texto, tabelas e figuras da comparação recente, somente a partir de agregados."""

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "reports/overleaf_dominio_observado_200k_v1"
PDF = ROOT / "output/pdf/resultados_dominio_observado_200k_v1.pdf"
MODELS = ("baseline", "traditional", "deep", "combined")
LABELS = {
    "baseline": "Baseline",
    "traditional": "Tradicional",
    "deep": "Profundo",
    "combined": "Combinado",
    "mean": "Média",
    "median": "Mediana",
}
COLORS = ("#607080", "#287F83", "#7955A1", "#B65532")
DATE = "02/11/2026"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def display(text):
    return str(text).replace("\u2013", "-").replace("\u2014", "-").replace("\u2011", "-")


def number(value, decimals=4):
    return f"{float(value):.{decimals}f}".replace(".", ",")


def integer(value):
    return f"{int(value):,}".replace(",", ".")


def tex(text):
    mapping = {
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
    }
    return "".join(mapping.get(c, c) for c in display(text))


def inputs():
    models = ROOT / "reports/modelagem_200k_v1/integral"
    diagnostics = ROOT / "reports/diagnosticos_modelagem_200k_v1"
    paths = [
        models / "resumo_modelagem.json",
        diagnostics / "resumo_diagnosticos.json",
        models / "metricas_externas.csv",
        models / "incrementos_pareados.csv",
        diagnostics / "diagnosticos_subgrupos.csv",
        diagnostics / "sensibilidade_remocao_componente.csv",
        diagnostics / "previsoes_fora_intervalo.csv",
        diagnostics / "celulas_pequenas.csv",
    ]
    a, b = (json.loads(p.read_text(encoding="utf-8")) for p in paths[:2])
    if not (
        a["completed"]
        and a["prediction_rows"] == 77535
        and b["completed"]
        and b["metrics_reproduced"]
        and b["verified_parts"] == 30
    ):
        raise ValueError("Exigir resultados e diagnósticos concluídos.")
    metrics = {r["model"]: r for r in read_csv(paths[2])}
    subgroups = read_csv(paths[4])
    if set(metrics) != set((*MODELS, "mean", "median")) or len(subgroups) > 2000:
        raise ValueError("Agregados incompatíveis com a publicação leve.")
    return paths, metrics, subgroups, read_csv(paths[5]), read_csv(paths[6]), read_csv(paths[7]), b


def cells(rows, dimension):
    result = {}
    for row in rows:
        if row["dimension"] == dimension:
            result.setdefault(row["level"], {})[row["model"]] = row
    return result


def figures(project, metrics, subgroups):
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.unicode_minus": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.fonttype": "none",
        }
    )
    target = project / "images"
    target.mkdir(exist_ok=True)

    def save(fig, name):
        for axis in fig.axes:
            if name == "comparacao_global":
                axis.xaxis.set_major_formatter(
                    FuncFormatter(lambda x, pos: f"{x:g}".replace(".", ","))
                )
            else:
                axis.yaxis.set_major_formatter(
                    FuncFormatter(lambda x, pos: f"{x:g}".replace(".", ","))
                )
        fig.savefig(target / f"{name}.png", dpi=300, bbox_inches="tight", facecolor="white")
        fig.savefig(target / f"{name}.svg", bbox_inches="tight", facecolor="white")
        plt.close(fig)

    fig, (left, right) = plt.subplots(1, 2, figsize=(8.2, 3.8), layout="constrained")
    names = (*MODELS, "mean", "median")
    for i, model in enumerate(names):
        left.scatter(float(metrics[model]["mae"]), i - 0.10, color="#234F78", marker="o", s=30)
        left.scatter(
            float(metrics[model]["mae_original_weight"]),
            i + 0.10,
            color="#BA6038",
            marker="s",
            s=27,
        )
    left.set_yticks(range(6), [LABELS[m] for m in names])
    left.invert_yaxis()
    left.set_xlim(0, 14)
    left.set_xlabel("MAE (pontos)")
    left.set_title("Erro global", loc="left", fontsize=11, weight="bold")
    left.grid(axis="x", alpha=0.18)
    for i, model in enumerate(MODELS[1:]):
        delta = float(metrics[model]["mae"]) - float(metrics["baseline"]["mae"])
        weighted = float(metrics[model]["mae_original_weight"]) - float(
            metrics["baseline"]["mae_original_weight"]
        )
        right.scatter(
            delta, i - 0.10, color="#234F78", label="Pesos iguais" if i == 0 else None, s=30
        )
        right.scatter(
            weighted,
            i + 0.10,
            color="#BA6038",
            marker="s",
            label="Pesos originais" if i == 0 else None,
            s=27,
        )
    right.axvline(0, color="#888888", lw=0.8)
    right.set_yticks(range(3), [LABELS[m] for m in MODELS[1:]])
    right.invert_yaxis()
    right.set_xlim(-0.27, 0.015)
    right.set_xlabel("Delta MAE frente ao Baseline")
    right.set_title("Incremento observado", loc="left", fontsize=11, weight="bold")
    right.legend(loc="lower right", fontsize=10.5, frameon=False)
    right.grid(axis="x", alpha=0.18)
    save(fig, "comparacao_global")

    folds = cells(subgroups, "outer_fold")
    levels = sorted(folds, key=int)
    fig, ax = plt.subplots(figsize=(7.2, 3.3), layout="constrained")
    for model, color in zip(MODELS, COLORS, strict=True):
        ax.plot(
            range(5),
            [float(folds[k][model]["mae"]) for k in levels],
            marker="o",
            label=LABELS[model],
            color=color,
            lw=1.5,
        )
    ax.set_xticks(range(5), [f"Fold {int(k) + 1}" for k in levels])
    ax.set_ylabel("MAE (pontos)")
    ax.grid(axis="y", alpha=0.18)
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.19), frameon=False, fontsize=9)
    save(fig, "estabilidade_folds")

    bands = cells(subgroups, "sampling_popularity_band")
    levels = sorted(bands, key=lambda k: int(re.match(r"\d+", k).group()))
    fig, ax = plt.subplots(figsize=(7.2, 3.3), layout="constrained")
    for model, color in (("baseline", COLORS[0]), ("combined", COLORS[3])):
        ax.plot(
            range(len(levels)),
            [float(bands[k][model]["mae"]) for k in levels],
            marker="o",
            label=LABELS[model],
            color=color,
            lw=1.6,
        )
    ax.set_xticks(
        range(len(levels)),
        [f"{display(k)}\nn={integer(bands[k]['baseline']['n'])}" for k in levels],
        fontsize=9,
    )
    ax.set_ylim(0, 35)
    ax.set_ylabel("MAE (pontos)")
    ax.set_xlabel("Popularidade observada no snapshot")
    ax.grid(axis="y", alpha=0.18)
    ax.legend(frameon=False)
    save(fig, "erro_popularidade")

    language = cells(subgroups, "lyrics_language_status")
    levels = ["english", "non_english", "uncertain"]
    labels = {"english": "Inglês estimado", "non_english": "Outros idiomas", "uncertain": "Incerto"}
    fig, ax = plt.subplots(figsize=(7.2, 3.3), layout="constrained")
    x = np.arange(3)
    for model, offset, color in (("baseline", -0.18, COLORS[0]), ("combined", 0.18, COLORS[3])):
        ax.bar(
            x + offset,
            [float(language[k][model]["mae"]) for k in levels],
            width=0.34,
            color=color,
            label=LABELS[model],
        )
    ax.set_xticks(x, [f"{labels[k]}\nn={integer(language[k]['baseline']['n'])}" for k in levels])
    ax.set_ylabel("MAE (pontos)")
    ax.set_ylim(0, 12)
    ax.grid(axis="y", alpha=0.16)
    ax.set_axisbelow(True)
    ax.legend(frameon=False)
    save(fig, "erro_idioma")


def manuscript(metrics, subgroups, deletion, bounds, small, diagnostic):
    folds = cells(subgroups, "outer_fold")
    bands = cells(subgroups, "sampling_popularity_band")
    language = cells(subgroups, "lyrics_language_status")
    history = cells(subgroups, "evaluation_component_history_status")
    gain = (
        100
        * (float(metrics["baseline"]["mae"]) - float(metrics["combined"]["mae"]))
        / float(metrics["baseline"]["mae"])
    )
    weighted_gain = (
        100
        * (
            float(metrics["baseline"]["mae_original_weight"])
            - float(metrics["combined"]["mae_original_weight"])
        )
        / float(metrics["baseline"]["mae_original_weight"])
    )
    fold_gains = [float(v["combined"]["mae"]) - float(v["baseline"]["mae"]) for v in folds.values()]
    genres = cells(subgroups, "model_genre")
    genre_improved = sum(
        float(v["combined"]["mae"]) < float(v["baseline"]["mae"]) for v in genres.values()
    )
    all_negative = all(
        float(r["max_delta_after_component_deletion"]) < 0
        and float(r["max_weighted_delta_after_component_deletion"]) < 0
        for r in deletion
    )
    if not all_negative:
        raise ValueError(
            "Revisar a redação: algum contraste mudou de sinal na remoção condicional."
        )

    def table(caption, headers, rows, note):
        return dict(caption=caption, headers=headers, rows=rows, note=note)

    tables = {
        "global": table(
            "Desempenho externo nas mesmas 77.535 faixas.",
            ["Configuração", "MAE", "RMSE", "R²", "MAE pond."],
            [
                [
                    LABELS[m],
                    *[number(metrics[m][c]) for c in ("mae", "rmse", "r2", "mae_original_weight")],
                ]
                for m in (*MODELS, "mean", "median")
            ],
            "MAE principal com pesos iguais. Ponderação original somente na avaliação, sem retreino. Menor MAE/RMSE indica menor erro.",
        ),
        "folds": table(
            "MAE por partição externa.",
            ["Fold", "n", "Baseline", "Trad.", "Prof.", "Comb."],
            [
                [
                    str(int(k) + 1),
                    integer(v["baseline"]["n"]),
                    *[number(v[m]["mae"]) for m in MODELS],
                ]
                for k, v in sorted(folds.items(), key=lambda kv: int(kv[0]))
            ],
            "Folds numerados de 1 a 5 para apresentação; equivalem aos índices 0 a 4 dos arquivos. Não são réplicas independentes.",
        ),
        "component": table(
            "Influência da retirada de um componente da avaliação.",
            ["Contraste", "Delta MAE", "Mín. remoção", "Máx. remoção"],
            [
                [
                    LABELS[r["block"]] + " - " + LABELS[r["reference"]],
                    number(r["delta_mae"]),
                    number(r["min_delta_after_component_deletion"]),
                    number(r["max_delta_after_component_deletion"]),
                ]
                for r in deletion
            ],
            "Modelos e previsões fixos. Estes extremos não são intervalos de confiança, nem validação com retreino.",
        ),
        "bands": table(
            "Erro por faixa de popularidade observada.",
            ["Faixa", "n", "Baseline", "Combinado", "Delta MAE"],
            [
                [
                    display(k),
                    integer(v["baseline"]["n"]),
                    number(v["baseline"]["mae"]),
                    number(v["combined"]["mae"]),
                    number(float(v["combined"]["mae"]) - float(v["baseline"]["mae"])),
                ]
                for k, v in sorted(
                    bands.items(), key=lambda kv: int(re.match(r"\d+", kv[0]).group())
                )
            ],
            "Faixas definidas no desenho amostral original. Diagnóstico por resposta observada; não caracteriza desempenho em futuros lançamentos.",
        ),
        "language": table(
            "Erro por status de idioma estimado.",
            ["Status", "n", "Baseline", "Combinado", "Delta MAE"],
            [
                [
                    {"english": "Inglês", "non_english": "Não inglês", "uncertain": "Incerto"}[k],
                    integer(language[k]["baseline"]["n"]),
                    number(language[k]["baseline"]["mae"]),
                    number(language[k]["combined"]["mae"]),
                    number(
                        float(language[k]["combined"]["mae"])
                        - float(language[k]["baseline"]["mae"])
                    ),
                ]
                for k in ("english", "non_english", "uncertain")
            ],
            "Idioma automático não é verdade humana; subconjuntos diferem também em composição e popularidade. Nenhum idioma foi excluído.",
        ),
        "history": table(
            "Diagnóstico de colisão com avaliação histórica por componente.",
            ["Status histórico", "n", "Baseline", "Combinado"],
            [
                [
                    label,
                    integer(history[k]["baseline"]["n"]),
                    number(history[k]["baseline"]["mae"]),
                    number(history[k]["combined"]["mae"]),
                ]
                for k, label in (
                    ("detected_collision", "Colisão detectada"),
                    ("no_detected_collision", "Sem detecção"),
                )
            ]
            + [["Chave indeterminada", "4", "omitido", "omitido"]],
            "Quatro casos de um componente permanecem no resultado global. Ausência de colisão detectada não garante independência histórica.",
        ),
    }
    sections = [
        {
            "title": "Métodos e domínio de análise",
            "paragraphs": [
                "A análise compara a contribuição preditiva incremental de informações textuais para a popularidade Spotify observada no snapshot da fonte. O domínio analítico contém 77.535 faixas com letras aceitas, provenientes da amostra estratificada original de 200.000 faixas. A disponibilidade das letras não assegura representatividade do catálogo ou de todas as músicas com letras; por isso, as conclusões se referem ao domínio observado.",
                "As quatro configurações usam as mesmas observações: Baseline, com 15 campos de metadados e acústicas; Tradicional, acrescentando 21 descritores lexicais e estruturais; Profundo, acrescentando embeddings multilingues de 384 dimensões; e Combinado, reunindo as duas representações textuais. Descritores e embeddings derivam do mesmo texto aceito padronizado. O encoder intfloat/multilingual-e5-small permaneceu congelado, sem ajuste pela resposta.",
                "A avaliação empregou validação cruzada aninhada agrupada, com cinco folds externos e três internos. Os 21.893 componentes operacionais, maior com 186 faixas, unem artistas, participações explícitas, composições e textos iguais segundo regras documentadas. Cada faixa recebeu uma previsão externa de ajuste que não utilizou seu componente. Chaves operacionais não são identificadores universais.",
                "A família Ridge foi mantida entre blocos, com alpha em 0,1; 1; 10; 100; 1.000; 10.000 e seleção por MAE interno não ponderado. Imputação, escala e categorias foram aprendidas apenas em cada treino. Foram executados 360 ajustes internos, 20 refits externos e dez referências média/mediana. Não houve PCA, ajuste do encoder, clipping ou expansão da grade após resultados externos. Esse cuidado distingue seleção e avaliação, conforme Cawley e Talbot (2010).",
                "O ajuste e as métricas principais atribuem pesos iguais às faixas. MAE é a métrica primária, com RMSE e R² complementares calculados sobre previsões externas reunidas. A sensibilidade usa os pesos amostrais originais apenas no MAE, nas mesmas previsões. Esses pesos não corrigem automaticamente a disponibilidade textual. O teste histórico v0.6 já havia sido aberto em 14/10/2026; nova CV não restaura confirmação independente.",
            ],
            "tables": [],
            "figures": [],
            "after": [],
        },
        {
            "title": "Resultados globais e sensibilidade aos pesos",
            "paragraphs": [
                f"O Combinado apresentou o menor MAE observado: {number(metrics['combined']['mae'])}, frente a {number(metrics['baseline']['mae'])} no Baseline. A redução foi de {number(float(metrics['baseline']['mae']) - float(metrics['combined']['mae']))} ponto, ou {number(gain, 3)}%. Com pesos originais, a redução relativa foi de {number(weighted_gain, 3)}%, mantendo a ordenação dos quatro blocos.",
                "O Profundo capturou a maior parte do incremento observado. Acrescentar os descritores tradicionais ao Profundo reduziu o MAE em apenas 0,0134 ponto. A comparação é entre representações na família Ridge: não demonstra superioridade de toda abordagem profunda, nem permite atribuição causal do incremento a elementos isolados das letras.",
            ],
            "tables": ["global"],
            "figures": [
                (
                    "comparacao_global",
                    "MAE global e deltas frente ao Baseline; pontos estimados, sem intervalos de confiança.",
                )
            ],
            "after": [
                "As referências média e mediana tiveram MAE de 12,5621 e 12,4786. O desempenho melhor das configurações com atributos confirma utilidade preditiva neste procedimento, mas o ganho textual adicional permanece modesto na escala da resposta. Não foi definido um limiar de equivalência prática ou calculado teste de significância."
            ],
        },
        {
            "title": "Estabilidade entre folds e influência dos componentes",
            "paragraphs": [
                f"O Combinado teve menor MAE que o Baseline nos cinco folds. Os deltas variaram de {number(min(fold_gains))} a {number(max(fold_gains))}. Cada teste externo contém 15.507 faixas; sua estabilidade de direção é descritiva e não autoriza tratar os cinco resultados como réplicas independentes.",
            ],
            "tables": ["folds", "component"],
            "figures": [
                (
                    "estabilidade_folds",
                    "MAE por fold externo, com as mesmas observações entre blocos em cada partição.",
                )
            ],
            "after": [
                "Os cinco contrastes mantiveram delta negativo quando qualquer componente foi retirado da avaliação, tanto com pesos iguais quanto com pesos originais. Isso indica que o sinal observado não depende de um único componente avaliado, condicionando aos modelos e previsões fixos. A operação não retreina modelos e não quantifica incerteza do treinamento; seus extremos não são IC."
            ],
        },
        {
            "title": "Erro na cauda de popularidade",
            "paragraphs": [
                "O erro não é uniforme ao longo da resposta. Embora o Combinado melhore o MAE frente ao Baseline em todas as faixas de popularidade publicadas, o erro absoluto cresce na cauda superior. Nas 128 faixas com popularidade entre 80 e 100, o MAE foi 29,3711, contra 30,9294 no Baseline. Esse comportamento deve acompanhar a divulgação do MAE global de 8,1151.",
            ],
            "tables": ["bands"],
            "figures": [
                (
                    "erro_popularidade",
                    "MAE por faixa da resposta observada e número de casos; células pequenas na cauda exigem cautela.",
                )
            ],
            "after": [
                "As previsões externas máximas do Profundo e do Combinado foram aproximadamente 78 pontos; no Combinado, a mínima foi -32,7066. O protocolo preservou previsões lineares sem clipping: 615 das 77.535 ficaram abaixo de zero. Não se propõe transformá-las retrospectivamente para substituir o resultado principal. Esses diagnósticos não definem um classificador de hits nem avaliação prospectiva de lançamentos."
            ],
        },
        {
            "title": "Heterogeneidade por idioma e outros subgrupos",
            "paragraphs": [
                "O incremento do Combinado frente ao Baseline foi de 0,1561 ponto nas 56.908 faixas de inglês estimado e 0,4693 nas 20.447 classificadas como não inglês. Nas 180 de status incerto, o MAE aumentou de 9,4360 para 9,8564. Portanto, o benefício médio não é uniforme. Essas diferenças descrevem subconjuntos com composição própria, sem identificar um efeito causal do idioma.",
            ],
            "tables": ["language"],
            "figures": [
                (
                    "erro_idioma",
                    "MAE por status de idioma automático; o grupo incerto foi mantido na análise principal.",
                )
            ],
            "after": [
                f"Entre os {len(genres)} gêneros com métricas publicadas, {genre_improved} apresentaram redução do MAE no Combinado frente ao Baseline. Há exceções, e as comparações são exploratórias, sem testes múltiplos. O diagnóstico publicou {diagnostic['published_cells']} células e omitiu métricas de {diagnostic['withheld_cells']} células com menos de 100 faixas ou 20 componentes, mantendo apenas suas contagens. Esses limiares não asseguram poder estatístico."
            ],
        },
        {
            "title": "Limites e conclusão descritiva",
            "paragraphs": [
                "O ganho do Combinado também aparece em componentes com colisão histórica detectada e nos sem colisão detectada. Essa separação não constitui novo holdout independente. Os quatro casos de chave histórica indeterminada, pertencentes a um componente, continuam na avaliação global; suas métricas isoladas foram omitidas pelos limiares predefinidos.",
                "A análise sustenta contribuição preditiva incremental observada de letras na comparação Ridge: o bloco de embeddings responde pelo maior incremento, enquanto a adição dos descritores tradicionais a ele produz ganho pequeno. A ordenação global é estável à ponderação e os sinais são preservados nos folds e na retirada condicional de um componente da avaliação.",
                "O alcance permanece limitado ao domínio observado. A integridade técnica não certifica precisão semântica de todos os pares Spotify-LRCLIB; idiomas e identidades são operacionais. As conclusões não são causais, não representam automaticamente o catálogo e não avaliam sucesso comercial futuro. Hipóteses adicionais seriam necessárias para ampliar a inferência.",
                "Não foram calculados IC ou p-valores. Bengio e Grandvalet (2004) mostram por que ignorar correlações na CV pode subestimar a variância. Os resultados apresentados não estabelecem significância estatística. Qualquer análise inferencial adicional deverá declarar seu estimando, hipóteses e tratamento da dependência dos ajustes.",
            ],
            "tables": ["history"],
            "figures": [],
            "after": [
                "Esta consolidação é um trecho parcial de métodos, resultados e discussão para a monografia. Não substitui introdução, revisão bibliográfica, caracterização completa das fontes, revisão dirigida de matching ou adequação ao template institucional. Os dados, modelos, pesos e folds anteriores permanecem preservados."
            ],
        },
    ]
    references = [
        "BENGIO, Y.; GRANDVALET, Y. No Unbiased Estimator of the Variance of K-Fold Cross-Validation. Journal of Machine Learning Research, v. 5, p. 1089-1105, 2004. https://www.jmlr.org/papers/v5/grandvalet04a.html",
        "CAWLEY, G. C.; TALBOT, N. L. C. On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation. Journal of Machine Learning Research, v. 11, p. 2079-2107, 2010. https://www.jmlr.org/papers/v11/cawley10a.html",
        "SCIKIT-LEARN. Ridge. Documentação da versão 1.9.1. https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html. Acesso em 02/11/2026.",
        "INTFLOAT. multilingual-e5-small: model card. Revisão 614241f622f53c4eeff9890bdc4f31cfecc418b3. https://huggingface.co/intfloat/multilingual-e5-small. Revisão congelada na extração local.",
    ]
    return dict(
        title="Representações de letras e popularidade no domínio observado",
        subtitle="Métodos, resultados e discussão - comparação Ridge",
        author="Felipe Macedo Cordeiro",
        date=DATE,
        sections=sections,
        tables=tables,
        references=references,
    )


def write_tex(project, document):
    (project / "sections").mkdir(exist_ok=True)
    (project / "tables").mkdir(exist_ok=True)
    (project / "references").mkdir(exist_ok=True)
    for name, table in document["tables"].items():
        lines = [
            r"\begin{table}[!htbp]\centering\small",
            r"\caption{" + tex(table["caption"]) + "}",
            r"\begin{tabularx}{\linewidth}{X" + "r" * (len(table["headers"]) - 1) + "}",
            r"\toprule",
            " & ".join(tex(c) for c in table["headers"]) + r" \\",
            r"\midrule",
        ]
        lines += [" & ".join(tex(c) for c in row) + r" \\" for row in table["rows"]]
        lines += [
            r"\bottomrule\end{tabularx}",
            r"\par\smallskip{\footnotesize " + tex(table["note"]) + "}",
            r"\end{table}",
        ]
        (project / "tables" / f"{name}.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    body = []
    for i, section in enumerate(document["sections"]):
        if i:
            body.append(r"\clearpage")
        body.append(r"\section{" + tex(section["title"]) + "}")
        body.extend(tex(p) + "\n" for p in section["paragraphs"])
        body.extend(r"\input{tables/" + name + "}" for name in section["tables"])
        for name, caption in section["figures"]:
            body += [
                r"\begin{figure}[!htbp]\centering",
                r"\includegraphics[width=\linewidth]{images/" + name + ".png}",
                r"\caption{" + tex(caption) + "}",
                r"\end{figure}",
            ]
        body.extend(tex(p) + "\n" for p in section["after"])
        body.append(r"\FloatBarrier")
    (project / "sections/trecho_observado.tex").write_text(
        "\n\n".join(body) + "\n", encoding="utf-8"
    )

    def reference_text(value):
        parts = re.split(r"(https?://\S+)", value)
        return "".join(
            r"\url{" + part.rstrip(".") + "}" + ("." if part.endswith(".") else "")
            if part.startswith("https://")
            else tex(part)
            for part in parts
        )

    refs = (
        [r"\begin{thebibliography}{9}"]
        + [
            r"\bibitem{obsref" + str(i) + "}" + reference_text(p)
            for i, p in enumerate(document["references"], 1)
        ]
        + [r"\end{thebibliography}"]
    )
    (project / "references/referencias.tex").write_text("\n\n".join(refs) + "\n", encoding="utf-8")
    main = r"""\documentclass[12pt,a4paper,oneside]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[brazil]{babel}
\usepackage[left=3cm,top=3cm,right=2cm,bottom=2cm]{geometry}
\usepackage{lmodern,microtype,indentfirst,graphicx,booktabs,tabularx,array,setspace,placeins}
\usepackage[hidelinks]{hyperref}
\onehalfspacing
\setlength{\parindent}{1.25cm}
\setlength{\emergencystretch}{2em}
\title{Representações de letras e popularidade no domínio observado}
\author{Felipe Macedo Cordeiro\\Departamento de Estatística - Universidade de Brasília}
\date{Trecho parcial para a monografia - 02/11/2026}
\begin{document}
\maketitle
\noindent Métodos, resultados e discussão da comparação Ridge. Não é a monografia completa nem um template institucional oficial.
\input{sections/trecho_observado}
\clearpage
\input{references/referencias}
\end{document}
"""
    (project / "main.tex").write_text(main, encoding="utf-8")


def run(project=PROJECT, pdf_python=None):
    paths, metrics, subgroups, deletion, bounds, small, diagnostic = inputs()
    project = project.resolve()
    if project.is_relative_to(ROOT / "data"):
        raise ValueError("Não escrever publicação nos diretórios de dados.")
    provenance = project / "PROVENIENCIA.json"
    if provenance.exists():
        previous = json.loads(provenance.read_text(encoding="utf-8"))
        if any(
            not (project / name).is_file() or digest(project / name) != value
            for name, value in previous["generated"].items()
        ):
            raise ValueError("Projeto contém edição manual; preservar e usar outro destino.")
    elif project.exists() and any(p.name != "main.tex" for p in project.iterdir()):
        raise ValueError("Destino não está vazio nem é o novo projeto LaTeX inicializado.")
    project.mkdir(parents=True, exist_ok=True)
    figures(project, metrics, subgroups)
    document = manuscript(metrics, subgroups, deletion, bounds, small, diagnostic)
    (project / "manuscrito.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_tex(project, document)
    readme = """# Trecho da linha recente do TCC

Projeto parcial de métodos, resultados e discussão do domínio observado de
77.535 faixas. Usa apenas agregados já concluídos; não inclui letras, bases,
modelos, previsões individuais ou credenciais. A integração Spotify-LFM2b antiga
permanece no pacote histórico separado; suas métricas não foram misturadas.

Upload do ZIP no Overleaf: main.tex como principal, pdfLaTeX/UTF-8, duas passagens.
Nenhum Python ou dado externo é necessário para compilar. Bibliografia incluída.
Para integrar ao TCC maior, copiar sections/tables/images/references e adaptar
apenas a hierarquia/pacotes; consolidar bibliografia, sem sobrescrever capítulos
anteriores. A aparência segue o trecho histórico, sem afirmar classe oficial UnB.

Quatro figuras em PNG 300 dpi e SVG editável. Dados agregados em source_data/,
proveniência/hashes em PROVENIENCIA.json. manuscrito.json é fonte compartilhada
para TeX e PDF de leitura. O PDF de leitura opcional é gerado por ReportLab;
não é exportação da compilação TeX e pode ter paginação diferente. O preview
LaTeX é verificado separadamente no editor integrado.

Gerador reproduzível: scripts/24_consolidar_resultados_monografia.py. Opera
somente em agregados públicos pequenos. Recusa sobrescrever projeto editado
manualmente: após revisar texto no editor, usar outro destino para regeneração.
Nenhum código/protocolo/modelo 19-23 foi modificado. Não é a monografia completa;
introdução, fundamentação/fontes completas, revisão dirigida de matching e
adequação ao template institucional ainda precisam ser integradas.
"""
    (project / "README.md").write_text(readme, encoding="utf-8")
    source_data = project / "source_data"
    source_data.mkdir(exist_ok=True)
    for path in paths:
        shutil.copyfile(path, source_data / (path.parent.name + "_" + path.name))
    generated = {
        str(p.relative_to(project)): digest(p)
        for p in project.rglob("*")
        if p.is_file() and p.name != "PROVENIENCIA.json"
    }
    provenance.write_text(
        json.dumps(
            {
                "date": DATE,
                "scope": "partial_observed_domain_chapter",
                "inputs": {str(p.resolve()): digest(p) for p in paths},
                "generator_sha256": digest(Path(__file__)),
                "generated": generated,
                "models_trained": False,
                "individual_data_read": False,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    archive = project.with_suffix(".zip")
    with zipfile.ZipFile(
        archive.with_suffix(".zip.tmp"), "w", compression=zipfile.ZIP_DEFLATED
    ) as zipped:
        for name in [*generated, "PROVENIENCIA.json"]:
            zipped.write(project / name, name)
    archive.with_suffix(".zip.tmp").replace(archive)
    if pdf_python:
        PDF.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                str(pdf_python),
                str(ROOT / "scripts/render_capitulo_modelagem_pdf.py"),
                str(project / "manuscrito.json"),
                str(PDF),
            ],
            check=True,
        )
    print(
        json.dumps(
            {
                "project": str(project),
                "zip": str(archive),
                "pdf": str(PDF) if pdf_python else None,
                "public_aggregate_rows": len(subgroups),
                "models_trained": False,
            },
            ensure_ascii=True,
        )
    )
    return 0


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT)
    parser.add_argument("--pdf-python", type=Path)
    args = parser.parse_args()
    return run(args.project, args.pdf_python)
