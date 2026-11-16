"""Interpreta agregados do sorteio 40; não lê linhas do catálogo ou da amostra."""

import matplotlib
import numpy as np

from tcc_music_popularity import sample_redesign as design

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

LABELS = {
    "popularity": "Popularidade",
    "year": "Ano",
    "danceability": "Dançabilidade",
    "energy": "Energia",
    "loudness": "Intensidade sonora",
    "speechiness": "Fala",
    "acousticness": "Caráter acústico",
    "instrumentalness": "Instrumentalidade",
    "liveness": "Presença de público",
    "valence": "Valência",
    "tempo": "BPM",
    "duration_ms": "Duração",
}


def run():
    root, output = design.ROOT, design.REPORT
    summary = design.read_json(output / "resumo_sorteio.json")
    plan = design.read_json(output / "plano_amostral.json")
    assert summary["concluido"] and summary["n"] == plan["n"] == 9526
    assert summary["plano_sha256"] == design.sha256(output / "plano_amostral.json")
    for name, value in summary["agregados_sha256"].items():
        assert design.sha256(output / name) == value, name
    metadata = design.read_csv(output / "comparacao_metadados.csv")
    categories = design.read_csv(output / "comparacao_categorias.csv")
    assert len(metadata) == 12
    grouped = {}
    for row in categories:
        grouped.setdefault(row["variavel"], []).append(row)
    for group in grouped.values():
        assert sum(int(r["n_amostra"]) for r in group) == summary["n"]
        assert sum(int(r["n_catalogo"]) for r in group) == summary["N"]
        assert np.isclose(sum(float(r["fracao_amostra_ponderada"]) for r in group), 1)
    labels = [LABELS[r["variavel"]] for r in metadata]
    difference = np.array([float(r["diferenca_medias_em_dp"]) for r in metadata])
    ratio = np.array(
        [float(r["dp_amostra_nao_ponderado"]) / float(r["dp_catalogo"]) for r in metadata]
    )
    y = np.arange(len(labels))
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.2), sharey=True, constrained_layout=True)
    axes[0].hlines(y, 0, difference, color="#a5bdcf")
    axes[0].scatter(difference, y, color="#176387", s=40)
    axes[0].axvline(0, color="#777777", linewidth=0.8)
    axes[0].set(
        xlabel="(Média ponderada da amostra − média do catálogo) / DP",
        title="Diferenças entre médias",
        yticks=y,
        yticklabels=labels,
        xlim=(-0.025, 0.025),
    )
    axes[0].invert_yaxis()
    axes[1].scatter(ratio, y, color="#397a56", s=40)
    axes[1].axvline(1, color="#777777", linewidth=0.8)
    axes[1].set(
        xlabel="DP não ponderado da amostra / DP do catálogo",
        title="Comparação de dispersões",
        xlim=(0.95, 1.02),
    )
    for ax in axes:
        ax.grid(axis="x", alpha=0.18)
        ax.spines[["right", "top"]].set_visible(False)
    fig.suptitle("Catálogo de 1.159.764 faixas e amostra probabilística de 9.526")
    for suffix in ["png", "svg"]:
        fig.savefig(output / f"comparacao_medias_dispersoes.{suffix}", dpi=220)
    plt.close(fig)

    periods = sorted(grouped["periodo"], key=lambda r: r["categoria"])
    x = np.arange(len(periods))
    fig, ax = plt.subplots(figsize=(8, 4.8), constrained_layout=True)
    for offset, column, label, color in [
        (-0.18, "fracao_catalogo", "Catálogo", "#7896a6"),
        (0.18, "fracao_amostra_ponderada", "Amostra ponderada", "#397a56"),
    ]:
        bars = ax.bar(
            x + offset, [100 * float(r[column]) for r in periods], 0.36, label=label, color=color
        )
        ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=10)
    ax.set(
        xticks=x,
        xticklabels=[r["categoria"] for r in periods],
        ylabel="Percentual de faixas (%)",
        title="Composição por período",
        ylim=(0, 52),
    )
    ax.legend(loc="upper right", frameon=False)
    ax.spines[["right", "top"]].set_visible(False)
    for suffix in ["png", "svg"]:
        fig.savefig(output / f"comparacao_periodos.{suffix}", dpi=220)
    plt.close(fig)

    table = [
        "| Variável | Média do catálogo | Média ponderada da amostra | Diferença em DP |",
        "|---|---:|---:|---:|",
    ]
    for row in metadata:
        table.append(
            f"| {LABELS[row['variavel']]} | {float(row['media_catalogo']):.5f} | "
            f"{float(row['media_amostra_ponderada']):.5f} | {float(row['diferenca_medias_em_dp']):+.5f} |"
        )
    text = (
        """# Interpretação da nova amostra — sorteio concluído em 06/11/2026

O pesquisador executou o script 40: **9.526 faixas**, provenientes de 1.159.764,
nos 82 gêneros e semente 20261106. Resumo de conclusão, selos do plano,
comparativos e Parquet conferidos. A análise abaixo usa apenas tabelas agregadas;
nenhuma linha individual foi reprocessada pelo agente.

## Parecer

**Manter o sorteio e avançar para a recuperação de letras.** As características
avaliadas ficaram próximas às do cadastro. Isso decorre do desenho probabilístico
e de um resultado favorável deste sorteio, sem ajustar a seleção posteriormente.
Não é comprovação de igualdade de todas as distribuições ou de ausência de
seleção na futura disponibilidade de letras.

A maior diferença absoluta entre as doze médias ponderadas foi **0,01901 DP**,
em liveness; em seguida speechiness, −0,01710 DP, e valence, +0,01390 DP.
As doze diferenças ficaram dentro das respectivas margens de planejamento para
a família de médias. Não se realizou teste de igualdade com o próprio cadastro.

## Médias e dispersões

"""
        + "\n".join(table)
        + """

Duração expressa em segundos. BPM inclui zeros, como na população do desenho.
A popularidade mediana não ponderada foi 15 em ambos; seus quartis foram 5 e
29 em ambos, e P95 foi 48 na amostra e 49 no catálogo. A mediana de duração foi
225,689 s contra 225,744 s, e P95 451,720 s contra 448,000 s.

As razões entre DP amostral **não ponderado** e DP populacional variaram de
0,9644 (duração) a 1,0057 (valência). A dispersão de speechiness foi 0,9647 da
populacional. Essas pequenas diferenças, inclusive nas caudas, devem ser
descritas; médias próximas não implicam distribuições idênticas. Quantis e DP
amostrais do comparativo são não ponderados, conforme o protocolo.

![Médias e dispersões](nova_amostra_catalogo_v1/comparacao_medias_dispersoes.png)

## Categorias

Todos os gêneros têm observações, de cinco a 179 por gênero. Suas proporções
ponderadas são iguais às do catálogo por construção: não usar essa igualdade
como teste independente de representatividade.

| Período | Catálogo (%) | Amostra ponderada (%) |
|---|---:|---:|
| 2000–2009 | 38,27 | 38,67 |
| 2010–2019 | 44,40 | 44,07 |
| 2020–2023 | 17,33 | 17,26 |

Maior diferença por período: +0,4050 ponto percentual em 2000–2009. Entre anos,
0,4252 ponto em 2006; entre tonalidades, −0,6158 ponto na categoria key=4.
Modo: maior diferença absoluta 0,1501 ponto; compasso: 0,1683 ponto.
São diferenças do sorteio, sem ressorteio para reduzi-las.

![Períodos](nova_amostra_catalogo_v1/comparacao_periodos.png)

## Próxima ação

Script 41 preparado para reaproveitar somente consultas exatas dos caches v2/v1:
mesmos metadados completos, duração e qualificadores; texto e vínculos conferidos
por hash. Aceitações anteriores continuam decisões automáticas, sem presumir
revisão humana. O script não acessa o SSD, varre o dump ou cria índices.

Os casos sem decisão reutilizável ficam pendentes, inclusive status negativos
antigos. Ausência no cache não significa inexistência de letra. A etapa seguinte
avaliará busca dirigida para essas pendências, aproveitando índices existentes.

A composição do subconjunto com letras deverá ser analisada novamente. Os
pesos de sorteio não corrigem automaticamente perdas e erros de vinculação.
Não se definiu ainda o domínio de modelagem da nova etapa.
"""
    )
    (root / "reports/interpretacao_nova_amostra_catalogo_v1.md").write_text(text, encoding="utf-8")
    print("Análise e duas figuras concluídas somente em agregados.")


if __name__ == "__main__":
    run()
