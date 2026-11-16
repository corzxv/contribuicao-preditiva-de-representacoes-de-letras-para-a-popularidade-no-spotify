"""Descrição inicial do catálogo completo, sem sorteio, letras ou modelo preditivo."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import yaml
from scipy.stats import rankdata
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/raw/spotify/spotify_data.csv"
OUTPUT = ROOT / "reports/descritiva_catalogo_completo_v1"
RULES = ROOT / "configs/quality_rules.yaml"
EXPECTED_HASH = "42fff9e85d1b26c3653b4668959d1be395fab8956848f0478bf28f726b3d5897"
VERSION = "1.0"
ACOUSTIC = (
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
NUMERIC = ("popularity", "year", *ACOUSTIC)
CATEGORICAL = ("genre", "year", "periodo", "key", "mode", "time_signature")
LABELS = {
    "popularity": "Popularidade",
    "year": "Ano informado",
    "danceability": "Dançabilidade",
    "energy": "Energia",
    "loudness": "Intensidade sonora (dB)",
    "speechiness": "Presença de fala",
    "acousticness": "Caráter acústico",
    "instrumentalness": "Instrumentalidade",
    "liveness": "Indício de execução ao vivo",
    "valence": "Valência",
    "tempo": "Andamento (BPM)",
    "duration_ms": "Duração (s)",
    "genre": "Gênero",
    "periodo": "Período informado",
    "key": "Classe de altura musical",
    "mode": "Modo",
    "time_signature": "Assinatura de tempo",
}
DEFINITIONS = {
    "artist_name": (
        "texto",
        "Crédito de artista da fonte; não é uma identidade pessoal desambiguada.",
        "identificação",
    ),
    "track_name": (
        "texto",
        "Título informado; títulos iguais podem corresponder a gravações diferentes.",
        "identificação",
    ),
    "track_id": (
        "texto",
        "Identificador de faixa Spotify; não é identificador universal de composição.",
        "identificação",
    ),
    "genre": (
        "categoria nominal",
        "Rótulo de gênero fornecido, mantido inteiro e sem recodificação musical.",
        "perfil",
    ),
    "popularity": (
        "escore inteiro",
        "Popularidade observada de 0 a 100; data de medição não confirmada.",
        "resposta descritiva",
    ),
    "year": (
        "ano inteiro",
        "Ano informado no CSV; não se presume primeiro lançamento da composição.",
        "tempo",
    ),
    "danceability": ("escore 0–1", "Adequação estimada à dança.", "PCA"),
    "energy": ("escore 0–1", "Intensidade e atividade percebidas estimadas pelo provedor.", "PCA"),
    "key": (
        "categoria musical",
        "Classe de altura de 0 a 11; -1 indica não identificação.",
        "perfil",
    ),
    "loudness": (
        "decibéis",
        "Intensidade sonora média informada; sem limite rígido adicional.",
        "PCA",
    ),
    "mode": ("categoria binária", "Codificação de modo menor (0) ou maior (1).", "perfil"),
    "speechiness": ("escore 0–1", "Presença estimada de fala.", "PCA"),
    "acousticness": ("escore 0–1", "Confiança estimada de caráter acústico.", "PCA"),
    "instrumentalness": (
        "escore 0–1",
        "Estimativa de ausência de voz; não comprova ausência de letra.",
        "PCA",
    ),
    "liveness": ("escore 0–1", "Indícios acústicos estimados de execução ao vivo.", "PCA"),
    "valence": (
        "escore 0–1",
        "Positividade musical estimada; não é sentimento validado da letra.",
        "PCA",
    ),
    "tempo": (
        "batidas/minuto",
        "Andamento global estimado; zero é sinalizado pela regra local.",
        "PCA",
    ),
    "duration_ms": (
        "milissegundos",
        "Duração original; coluna descritiva nova é expressa em segundos.",
        "PCA",
    ),
    "time_signature": (
        "categoria musical",
        "Assinatura de tempo estimada; números são tratados como categorias.",
        "perfil",
    ),
}


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save_json(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def save_rows(path, rows):
    if rows:
        pl.DataFrame(rows, infer_schema_length=None).write_csv(path)


def clean(name):
    value = pl.col(name).str.strip_chars()
    return pl.when(value.is_in(["", "NA", "N/A", "null", "None"])).then(None).otherwise(value)


def derived(name):
    return "_desc_duration_s" if name == "duration_ms" else "_desc_" + name


def unit(name):
    return {
        "duration_ms": "segundos",
        "tempo": "BPM",
        "loudness": "dB",
        "year": "ano informado",
        "popularity": "pontos de popularidade",
    }.get(name, "escore 0–1")


def domain(name, x, rules):
    if name == "popularity":
        return x.is_between(0, 100) & (x == x.floor())
    if name == "year":
        return x.is_between(*rules["year"]) & (x == x.floor())
    if name in rules["unit_interval"]:
        return x.is_between(0, 1)
    if name + "_values" in rules:
        return x.is_in(rules[name + "_values"])
    if name + "_min_exclusive" in rules:
        return x > rules[name + "_min_exclusive"]
    return pl.lit(True)


def prepare_frame(frame, rules):
    """Cria colunas adicionais; os campos originais não são sobrescritos."""
    quality, dictionary = [], []
    originals = frame.columns
    numeric_codes = (*NUMERIC, "key", "mode", "time_signature")
    for name in originals:
        raw = clean(name)
        missing = int(frame.select(raw.is_null().sum()).item())
        if name in numeric_codes:
            parsed = raw.cast(pl.Float64, strict=False)
            finite = parsed.is_finite().fill_null(False)
            valid = finite & domain(name, parsed, rules).fill_null(False)
            counts = frame.select(
                (raw.is_not_null() & ~finite).sum().alias("parse"),
                (finite & ~valid).sum().alias("domain"),
            ).row(0)
            factor = 0.001 if name == "duration_ms" else 1.0
            frame = frame.with_columns(
                pl.when(valid).then(parsed * factor).otherwise(None).alias(derived(name)),
                pl.when(finite).then(parsed * factor).otherwise(None).alias("_finite_" + name),
            )
        else:
            counts = (0, 0)
        dtype, definition, use = DEFINITIONS.get(
            name,
            (
                "índice da fonte",
                "Índice exportado no CSV; não é atributo musical.",
                "não analítico",
            ),
        )
        quality.append(
            {
                "variavel": name,
                "n_total": frame.height,
                "n_ausentes": missing,
                "n_nao_numericos_ou_nao_finitos": int(counts[0]),
                "n_fora_regra_local": int(counts[1]),
                "n_distintos_nao_ausentes": frame.select(raw.drop_nulls().n_unique()).item(),
            }
        )
        dictionary.append(
            {
                "variavel_original": name or "[coluna sem nome]",
                "tipo_e_unidade_original": dtype,
                "definicao": definition,
                "papel_descritivo": use,
                "coluna_nova": derived(name) if name in numeric_codes else "",
                "unidade_nova": "segundos" if name == "duration_ms" else dtype,
            }
        )
    frame = frame.with_columns(
        clean("genre").fill_null("[ausente]").alias("_grupo_genre"),
        pl.col(derived("year"))
        .cast(pl.Int64)
        .cast(pl.String)
        .fill_null("[ausente/inválido]")
        .alias("_grupo_year"),
        pl.when(pl.col(derived("year")).is_between(2000, 2009))
        .then(pl.lit("2000–2009"))
        .when(pl.col(derived("year")).is_between(2010, 2019))
        .then(pl.lit("2010–2019"))
        .when(pl.col(derived("year")).is_between(2020, 2023))
        .then(pl.lit("2020–2023"))
        .when(pl.col(derived("year")).is_not_null())
        .then(pl.lit("Outros anos"))
        .otherwise(pl.lit("[ausente/inválido]"))
        .alias("_grupo_periodo"),
    )
    for name in ("key", "mode", "time_signature"):
        frame = frame.with_columns(
            pl.col(derived(name))
            .cast(pl.Int64)
            .cast(pl.String)
            .fill_null("[ausente/inválido]")
            .alias("_grupo_" + name)
        )
    return frame, quality, dictionary


def numeric_summary(values):
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return {"n": 0}
    mean = float(values.mean())
    centered = values - mean
    variance = float(np.mean(centered**2))
    quantiles = np.quantile(values, [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
    return {
        "n": len(values),
        "media": mean,
        "dp_populacional": float(np.sqrt(variance)),
        "variancia_divisor_n_menos_1": float(np.var(values, ddof=1)) if len(values) > 1 else None,
        "minimo": float(values.min()),
        "maximo": float(values.max()),
        **dict(
            zip(
                ("p01", "p05", "p25", "mediana", "p75", "p95", "p99"),
                map(float, quantiles),
                strict=True,
            )
        ),
        "n_zeros": int(np.count_nonzero(values == 0)),
        "assimetria_momentos": float(np.mean(centered**3) / variance**1.5)
        if variance > 0
        else None,
        "curtose_excesso_momentos": float(np.mean(centered**4) / variance**2 - 3)
        if variance > 0
        else None,
    }


def numerical_tables(frame):
    summaries, histograms = [], []
    for name in NUMERIC:
        for scope, prefix in (("todos_finitos", "_finite_"), ("regra_local", "_desc_")):
            column = "_finite_" + name if prefix == "_finite_" else derived(name)
            values = frame[column].drop_nulls().to_numpy()
            summaries.append(
                {
                    "variavel": name,
                    "unidade": unit(name),
                    "escopo": scope,
                    **numeric_summary(values),
                }
            )
        values = frame[derived(name)].drop_nulls().to_numpy()
        if len(values):
            if name == "popularity":
                edges = np.arange(-0.5, 101.5)
            elif name == "year":
                edges = np.arange(values.min() - 0.5, values.max() + 1.5)
            elif name in (
                "danceability",
                "energy",
                "speechiness",
                "acousticness",
                "instrumentalness",
                "liveness",
                "valence",
            ):
                edges = np.linspace(0, 1, 41)
            else:
                edges = np.histogram_bin_edges(values, bins=60)
            counts, edges = np.histogram(values, bins=edges)
            histograms.extend(
                {
                    "variavel": name,
                    "unidade": unit(name),
                    "limite_inferior": float(left),
                    "limite_superior": float(right),
                    "n": int(n),
                    "fracao": float(n / len(values)),
                    "n_validos": len(values),
                    "ultimo_intervalo_fechado": i == len(counts) - 1,
                }
                for i, (left, right, n) in enumerate(
                    zip(edges[:-1], edges[1:], counts, strict=True)
                )
            )
    return summaries, histograms


def group_tables(frame):
    frequencies, grouped, associations = [], [], []
    for group in CATEGORICAL:
        column = "_grupo_" + group
        counts = frame.group_by(column).len().sort(["len", column], descending=[True, False])
        frequencies.extend(
            {
                "variavel": group,
                "categoria": row[column],
                "n": row["len"],
                "fracao": row["len"] / frame.height,
            }
            for row in counts.to_dicts()
        )
        if group not in ("genre", "year", "periodo"):
            continue
        for variable in NUMERIC:
            x = pl.col(derived(variable))
            table = (
                frame.group_by(column)
                .agg(
                    pl.len().alias("n_grupo"),
                    x.count().alias("n_validos"),
                    x.mean().alias("media"),
                    x.std(ddof=0).alias("dp_populacional"),
                    x.quantile(0.05, interpolation="linear").alias("p05"),
                    x.quantile(0.25, interpolation="linear").alias("p25"),
                    x.median().alias("mediana"),
                    x.quantile(0.75, interpolation="linear").alias("p75"),
                    x.quantile(0.95, interpolation="linear").alias("p95"),
                )
                .sort(column)
            )
            rows = table.to_dicts()
            grouped.extend(
                {
                    "agrupamento": group,
                    "categoria": row.pop(column),
                    "variavel": variable,
                    "unidade": unit(variable),
                    **row,
                }
                for row in rows
            )
            values = frame[derived(variable)].drop_nulls().to_numpy()
            if len(values):
                mean = float(values.mean())
                total = float(np.sum((values - mean) ** 2))
                between = sum(
                    row["n_validos"] * (row["media"] - mean) ** 2
                    for row in rows
                    if row["n_validos"]
                )
                associations.append(
                    {
                        "agrupamento": group,
                        "variavel": variable,
                        "n_validos": len(values),
                        "eta_quadrado_descritivo": min(1.0, max(0.0, between / total))
                        if total > 0
                        else None,
                        "interpretacao": "Fração da variação entre médias de categorias; associação sem causalidade ou teste.",
                    }
                )
    cross = (
        frame.group_by("_grupo_genre", "_grupo_periodo")
        .len()
        .sort(["_grupo_genre", "_grupo_periodo"])
    )
    return (
        frequencies,
        grouped,
        associations,
        cross.rename({"_grupo_genre": "genero", "_grupo_periodo": "periodo", "len": "n"}),
    )


def correlation_tables(frame):
    complete = frame.select([derived(name) for name in NUMERIC]).drop_nulls()
    values = complete.to_numpy()
    kept = np.std(values, axis=0, ddof=1) > 0 if len(values) > 1 else np.zeros(len(NUMERIC), bool)
    names = [name for name, use in zip(NUMERIC, kept, strict=True) if use]
    if len(values) < 3 or len(names) < 2:
        return [], {"n_casos_completos": len(values), "n_excluidos": frame.height - len(values)}
    x = values[:, kept]
    with threadpool_limits(limits=2):
        matrices = {
            "Pearson": np.corrcoef(x, rowvar=False),
            "Spearman": np.corrcoef(rankdata(x, axis=0, method="average"), rowvar=False),
        }
    rows = [
        {
            "metodo": method,
            "variavel_1": a,
            "variavel_2": b,
            "correlacao": float(matrix[i, j]),
            "n_casos_completos": len(values),
        }
        for method, matrix in matrices.items()
        for i, a in enumerate(names)
        for j, b in enumerate(names)
    ]
    return rows, {
        "n_casos_completos": len(values),
        "n_excluidos": frame.height - len(values),
        "variaveis": names,
        "constantes_fora_da_matriz": [n for n in NUMERIC if n not in names],
        "observacao": "Mesmos casos completos válidos em todas as correlações; Spearman usa postos médios nos empates.",
    }


def pca_values(matrix, names):
    """PCA exata das dez contínuas, pela matriz de correlação dos casos completos."""
    if len(matrix) < 3:
        raise ValueError("PCA precisa de pelo menos três casos completos.")
    means, scales = matrix.mean(axis=0), matrix.std(axis=0, ddof=1)
    keep = scales > 0
    if keep.sum() < 2:
        raise ValueError("PCA precisa de pelo menos duas variáveis não constantes.")
    standardized = (matrix[:, keep] - means[keep]) / scales[keep]
    with threadpool_limits(limits=2):
        correlation = standardized.T @ standardized / (len(matrix) - 1)
        eigenvalues, vectors = np.linalg.eigh(correlation)
        eigenvalues, vectors = eigenvalues[::-1].clip(0), vectors[:, ::-1]
        for j in range(vectors.shape[1]):
            if vectors[np.abs(vectors[:, j]).argmax(), j] < 0:
                vectors[:, j] *= -1
        scores = standardized @ vectors[:, : min(3, len(eigenvalues))]
    retained = [name for name, use in zip(names, keep, strict=True) if use]
    fractions = eigenvalues / eigenvalues.sum()
    summary = {
        "n_casos_completos": len(matrix),
        "variaveis": retained,
        "variaveis_constantes": [name for name, use in zip(names, keep, strict=True) if not use],
        "medias": dict(zip(names, map(float, means), strict=True)),
        "desvios_divisor_n_menos_1": dict(zip(names, map(float, scales), strict=True)),
        "autovalores": eigenvalues.tolist(),
        "fracao_variancia": fractions.tolist(),
        "fracao_acumulada": fractions.cumsum().tolist(),
        "componentes_para_80_porcento": int(np.searchsorted(fractions.cumsum(), 0.80) + 1),
        "componentes_para_95_porcento": int(np.searchsorted(fractions.cumsum(), 0.95) + 1),
        "padronizacao": "z=(x-media)/desvio com divisor n-1; duração em segundos",
        "metodo": "Autodecomposição da matriz de correlação; casos completos, sem imputação.",
        "interpretacao": "Eixos de covariação; não são clusters, causas ou variância explicada da popularidade.",
        "genero_ano_popularidade_fora_da_pca": True,
    }
    rows = [
        {
            "componente": j + 1,
            "variavel": name,
            "coeficiente_eixo": float(vectors[i, j]),
            "correlacao_variavel_componente": float(vectors[i, j] * np.sqrt(eigenvalues[j])),
        }
        for j in range(len(eigenvalues))
        for i, name in enumerate(retained)
    ]
    return summary, rows, scores


def pca_tables(frame):
    selected = frame.select(
        *[derived(name) for name in ACOUSTIC], "_grupo_genre", "_grupo_periodo"
    ).drop_nulls(subset=[derived(name) for name in ACOUSTIC])
    summary, coefficients, scores = pca_values(
        selected.select([derived(n) for n in ACOUSTIC]).to_numpy(), ACOUSTIC
    )
    summary["n_excluidos_somente_desta_analise"] = frame.height - selected.height
    summary["ausencias_ou_invalidos_por_variavel_nao_somaveis"] = {
        name: frame[derived(name)].null_count() for name in ACOUSTIC
    }
    score_frame = selected.select("_grupo_genre", "_grupo_periodo").with_columns(
        [pl.Series(f"CP{j + 1}", scores[:, j]) for j in range(scores.shape[1])]
    )
    profiles = []
    for group in ("genre", "periodo"):
        rows = (
            score_frame.group_by("_grupo_" + group)
            .agg(
                pl.len().alias("n"),
                *[
                    pl.col(f"CP{j + 1}").mean().alias(f"media_CP{j + 1}")
                    for j in range(scores.shape[1])
                ],
            )
            .sort("_grupo_" + group)
            .to_dicts()
        )
        profiles.extend(
            {"agrupamento": group, "categoria": row.pop("_grupo_" + group), **row} for row in rows
        )
    return summary, coefficients, scores, profiles


def save_figure(output, name, figure):
    for extension in ("png", "svg"):
        figure.savefig(output / "figuras" / f"{name}.{extension}", dpi=300, bbox_inches="tight")
    plt.close(figure)


def draw_heatmap(axis, matrix, xlabels, ylabels, title, limit=1):
    picture = axis.imshow(matrix, cmap="RdBu_r", vmin=-limit, vmax=limit, aspect="auto")
    axis.set_xticks(range(len(xlabels)), xlabels, rotation=60, ha="right", fontsize=8)
    axis.set_yticks(range(len(ylabels)), ylabels, fontsize=8)
    axis.set_title(title)
    return picture


def density(values, bins=60):
    count, xedges, yedges = np.histogram2d(values[:, 0], values[:, 1], bins=bins)
    return count, xedges, yedges


def density_plot(axis, result, xlabel, ylabel, title):
    count, xedges, yedges = result
    picture = axis.pcolormesh(
        xedges,
        yedges,
        np.ma.masked_where(count.T == 0, np.log10(count.T + 1)),
        cmap="viridis",
        shading="auto",
        rasterized=True,
    )
    axis.set(xlabel=xlabel, ylabel=ylabel, title=title)
    return picture


def plot_distributions(frame, output, frequencies):
    fig, axes = plt.subplots(5, 2, figsize=(10.8, 13.6), layout="constrained")
    for name, axis in zip(ACOUSTIC, axes.flat, strict=True):
        x = frame[derived(name)].drop_nulls().to_numpy()
        if len(x):
            axis.hist(
                x, bins=50, weights=np.full(len(x), 100 / len(x)), color="#315e7a", edgecolor="none"
            )
        axis.set(
            xlabel=LABELS[name],
            ylabel="Faixas (%)",
            title=f"n válido = {len(x):,}".replace(",", "."),
        )
    save_figure(output, "01_distribuicoes_metadados", fig)
    popularity = frame[derived("popularity")].drop_nulls().to_numpy()
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.8), layout="constrained")
    for values, axis, label, bins in (
        (popularity, axes[0], "Popularidade original", np.arange(-0.5, 101.5)),
        (np.log1p(popularity), axes[1], "log(1 + popularidade)", 40),
    ):
        axis.hist(
            values, bins=bins, weights=np.full(len(values), 100 / len(values)), color="#315e7a"
        )
        axis.set(xlabel=label, ylabel="Faixas (%)")
    fig.suptitle("Mesmas faixas nas duas escalas; zeros preservados")
    save_figure(output, "02_popularidade_original_log1p", fig)
    genres = [r for r in frequencies if r["variavel"] == "genre"][:20][::-1]
    fig, axis = plt.subplots(figsize=(8.5, 6), layout="constrained")
    axis.barh(
        [r["categoria"] for r in genres], [100 * r["fracao"] for r in genres], color="#315e7a"
    )
    axis.set(
        xlabel="Faixas do catálogo (%)", title="Vinte gêneros mais frequentes; tabela contém todos"
    )
    save_figure(output, "03_generos", fig)
    years = sorted(
        [r for r in frequencies if r["variavel"] == "year"], key=lambda r: r["categoria"]
    )
    fig, axis = plt.subplots(figsize=(9.5, 3.8), layout="constrained")
    axis.bar([r["categoria"] for r in years], [r["n"] for r in years], color="#477c75")
    axis.set(xlabel="Campo year da fonte", ylabel="Número de faixas")
    axis.tick_params(axis="x", rotation=65)
    save_figure(output, "04_anos", fig)
    fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.5), layout="constrained")
    for name, axis in zip(("key", "mode", "time_signature"), axes, strict=True):
        rows = sorted(
            [r for r in frequencies if r["variavel"] == name],
            key=lambda r: (
                int(r["categoria"]) if r["categoria"].lstrip("-").isdigit() else float("inf")
            ),
        )
        axis.bar([r["categoria"] for r in rows], [100 * r["fracao"] for r in rows], color="#477c75")
        axis.set(xlabel=LABELS[name], ylabel="Faixas (%)")
        axis.tick_params(axis="x", rotation=45)
    save_figure(output, "05_categorias_musicais", fig)


def plot_correlations(output, rows, summary):
    if not rows:
        return
    names = summary["variaveis"]
    labels = [LABELS[n] for n in names]
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.3), layout="constrained")
    for method, axis in zip(("Pearson", "Spearman"), axes, strict=True):
        lookup = {
            (r["variavel_1"], r["variavel_2"]): r["correlacao"]
            for r in rows
            if r["metodo"] == method
        }
        matrix = np.array([[lookup[(a, b)] for b in names] for a in names])
        pic = draw_heatmap(axis, matrix, labels, labels, method)
    fig.colorbar(pic, ax=axes, label="Correlação", shrink=0.75)
    fig.suptitle(
        f"Mesmos {summary['n_casos_completos']:,} casos completos válidos".replace(",", ".")
    )
    save_figure(output, "06_correlacoes", fig)


def plot_groups(output, frequencies, grouped, summaries):
    global_stats = {r["variavel"]: r for r in summaries if r["escopo"] == "regra_local"}
    names = list(ACOUSTIC)
    for group, filename in (("genre", "07_perfis_generos"), ("periodo", "08_perfis_periodos")):
        categories = [r["categoria"] for r in frequencies if r["variavel"] == group]
        lookup = {
            (r["categoria"], r["variavel"]): r["media"]
            for r in grouped
            if r["agrupamento"] == group
        }
        matrix = np.array(
            [
                [
                    (
                        (lookup.get((c, n)) - global_stats[n]["media"])
                        / global_stats[n]["dp_populacional"]
                    )
                    if lookup.get((c, n)) is not None
                    and global_stats[n].get("dp_populacional", 0) > 0
                    else np.nan
                    for n in names
                ]
                for c in categories
            ]
        )
        height = max(3.3, 0.23 * len(categories) + 2)
        fig, axis = plt.subplots(figsize=(10.5, height), layout="constrained")
        pic = draw_heatmap(
            axis,
            matrix,
            [LABELS[n] for n in names],
            categories,
            "Médias dos grupos em relação à média do catálogo",
            limit=2,
        )
        fig.colorbar(pic, ax=axis, label="Diferença / DP global (cor limitada a ±2)")
        save_figure(output, filename, fig)
    genres = [r["categoria"] for r in frequencies if r["variavel"] == "genre"][:10]
    variables = (
        "danceability",
        "energy",
        "acousticness",
        "instrumentalness",
        "tempo",
        "duration_ms",
    )
    fig, axes = plt.subplots(3, 2, figsize=(11, 12), layout="constrained")
    lookup = {(r["categoria"], r["variavel"]): r for r in grouped if r["agrupamento"] == "genre"}
    for name, axis in zip(variables, axes.flat, strict=True):
        boxes = []
        for genre in genres:
            row = lookup[(genre, name)]
            if row["n_validos"]:
                boxes.append(
                    {
                        "label": genre,
                        "med": row["mediana"],
                        "q1": row["p25"],
                        "q3": row["p75"],
                        "whislo": row["p05"],
                        "whishi": row["p95"],
                        "fliers": [],
                    }
                )
        axis.bxp(boxes, orientation="horizontal", showfliers=False)
        axis.set_xlabel(LABELS[name])
    fig.suptitle("Dez gêneros mais frequentes: mediana, P25–P75 e hastes P5–P95")
    save_figure(output, "09_distribuicoes_por_genero", fig)


def plot_relationships(frame, output):
    pairs = (
        ("danceability", "energy"),
        ("energy", "loudness"),
        ("energy", "acousticness"),
        ("tempo", "danceability"),
        ("valence", "danceability"),
        ("duration_ms", "instrumentalness"),
    )
    fig, axes = plt.subplots(3, 2, figsize=(11, 10.5), layout="constrained")
    cells = []
    for (a, b), axis in zip(pairs, axes.flat, strict=True):
        values = frame.select(derived(a), derived(b)).drop_nulls().to_numpy()
        if not len(values):
            continue
        result = density(values)
        pic = density_plot(
            axis, result, LABELS[a], LABELS[b], f"n = {len(values):,}".replace(",", ".")
        )
        fig.colorbar(pic, ax=axis, label="log10(1 + contagem)")
        count, xedges, yedges = result
        for i, j in np.argwhere(count > 0):
            cells.append(
                {
                    "variavel_x": a,
                    "variavel_y": b,
                    "x_inferior": float(xedges[i]),
                    "x_superior": float(xedges[i + 1]),
                    "y_inferior": float(yedges[j]),
                    "y_superior": float(yedges[j + 1]),
                    "n": int(count[i, j]),
                    "n_validos_par": len(values),
                    "ultima_celula_x": bool(i == count.shape[0] - 1),
                    "ultima_celula_y": bool(j == count.shape[1] - 1),
                }
            )
    save_rows(output / "densidades_relacoes.csv", cells)
    save_figure(output, "10_relacoes_metadados", fig)


def plot_pca(output, summary, rows, scores):
    fractions = np.array(summary["fracao_variancia"])
    indices = np.arange(1, len(fractions) + 1)
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.6), layout="constrained")
    axes[0].bar(indices, fractions * 100, color="#315e7a")
    axes[0].set(xlabel="Componente", ylabel="Variância (%)", xticks=indices)
    axes[1].plot(indices, fractions.cumsum() * 100, marker="o", color="#477c75")
    axes[1].axhline(95, color="gray", linestyle="--", linewidth=0.8)
    axes[1].set(
        xlabel="Número de componentes",
        ylabel="Variância acumulada (%)",
        xticks=indices,
        ylim=(0, 102),
    )
    save_figure(output, "11_pca_variancia", fig)
    names = summary["variaveis"]
    lookup = {(r["variavel"], r["componente"]): r["coeficiente_eixo"] for r in rows}
    first = min(3, len(fractions))
    matrix = np.array([[lookup[(name, j)] for j in range(1, first + 1)] for name in names])
    fig, axis = plt.subplots(figsize=(6.8, 5), layout="constrained")
    pic = draw_heatmap(
        axis,
        matrix,
        [f"CP{j}: {100 * fractions[j - 1]:.1f}%" for j in range(1, first + 1)],
        [LABELS[n] for n in names],
        "Coeficientes dos eixos sobre variáveis padronizadas",
    )
    for i in range(len(names)):
        for j in range(first):
            axis.text(
                j,
                i,
                f"{matrix[i, j]:.2f}",
                ha="center",
                va="center",
                fontsize=9,
                color="white" if abs(matrix[i, j]) > 0.65 else "black",
            )
    fig.colorbar(pic, ax=axis, label="Coeficiente do autovetor")
    save_figure(output, "12_pca_coeficientes", fig)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), layout="constrained")
    low, high = np.quantile(scores[:, :2], [0.005, 0.995], axis=0)
    central = ((scores[:, :2] >= low) & (scores[:, :2] <= high)).all(axis=1)
    maps = [("amplitude_completa", scores[:, :2]), ("regiao_central", scores[central, :2])]
    cells = []
    for (scope, values), axis in zip(maps, axes, strict=True):
        result = density(values, bins=80)
        pic = density_plot(
            axis,
            result,
            "CP1",
            "CP2",
            (
                "Amplitude completa"
                if scope == "amplitude_completa"
                else "Região P0,5–P99,5 em cada eixo"
            )
            + "\nn = "
            + f"{len(values):,}".replace(",", "."),
        )
        fig.colorbar(pic, ax=axis, label="log10(1 + contagem)")
        count, xedges, yedges = result
        for i, j in np.argwhere(count > 0):
            cells.append(
                {
                    "visao": scope,
                    "cp1_inferior": float(xedges[i]),
                    "cp1_superior": float(xedges[i + 1]),
                    "cp2_inferior": float(yedges[j]),
                    "cp2_superior": float(yedges[j + 1]),
                    "n": int(count[i, j]),
                    "n_visiveis": len(values),
                }
            )
    summary["mapa_central_n_visiveis"] = int(central.sum())
    summary["mapa_central_n_fora_apenas_da_figura"] = int((~central).sum())
    save_rows(output / "densidade_pca.csv", cells)
    save_figure(output, "13_pca_mapa", fig)


def write_report(output, summary, pca):
    text = f"""# Descrição do catálogo completo — {summary["n_faixas"]:,} faixas

População acessível do CSV Spotify, anterior à amostragem e à recuperação de letras.
Esta análise é a parte inicial de caracterização dos dados. Não redefine amostra,
população analítica ou resultados preditivos anteriores.

## Conteúdo para a redação

1. dicionario_variaveis.csv: todos os campos originais, definições e unidades.
2. qualidade_campos.csv: ausências, falhas numéricas e regras locais por variável.
3. resumo_numerico.csv e histogramas.csv: distribuição, quantis, dispersão,
   assimetria e zeros; escopos todos_finitos e regra_local explicitados.
4. frequencias_categoricas.csv e genero_periodo.csv: todos os gêneros, anos,
   períodos e categorias musicais. Figuras de barras mostram recortes identificados.
5. perfis_grupos.csv: médias, dispersões e quantis por gênero, ano e período.
   associacoes_grupos.csv: eta² descritivo, sem testes ou afirmações causais.
6. correlacoes.csv: Pearson e Spearman nos mesmos casos completos válidos,
   com denominador informado. densidades_relacoes.csv contém células agregadas.
7. pca_variancia.csv, pca_coeficientes.csv, pca_perfis_grupos.csv e resumo_pca.json:
   PCA exploratória dos atributos acústicos contínuos e duração, sem o alvo.
8. popularidade_log1p.csv: descrição de log(1+popularidade), preservando os zeros,
   sem transformação do alvo para ajuste de modelos.

## PCA

Casos completos: {pca["n_casos_completos"]:,}; fora somente desta análise:
{pca["n_excluidos_somente_desta_analise"]:,}. Todas as faixas permanecem na descrição
do catálogo; não houve exclusão da população, imputação ou eliminação de outliers.
Variáveis: {", ".join(pca["variaveis"])}. Duração em segundos. Padronização por
média e desvio com divisor n−1; autodecomposição da matriz de correlação.
São necessários {pca["componentes_para_80_porcento"]} componentes para 80% e
{pca["componentes_para_95_porcento"]} para 95% da variância dos preditores.
Isso não é variância explicada da popularidade. Gênero/período apenas descrevem
os escores; não há agrupamento automático de músicas ou uso preditivo dos eixos.
O sinal é orientado pelo maior coeficiente absoluto positivo, sem mudar a PCA.
O mapa mostra amplitude completa e uma ampliação central; o resumo registra
quantas faixas ficam fora apenas da ampliação. Nenhum escore individual é exportado.

## Convenções e alcance

- Todas as linhas são descritas; nenhum peso amostral é necessário para esse catálogo.
- Quantis por interpolação linear; DP descritivo usa divisor n. Variância com
  divisor n−1 também é fornecida como insumo de planejamento.
- Regras de domínio vêm de configs/quality_rules.yaml, não de uma certificação
  externa. Valores finitos fora delas continuam no escopo todos_finitos.
- year é o ano da fonte, sem pressupor lançamento original; o escore de
  instrumentalidade não prova que uma faixa não tenha letra.
- Chaves musicais e assinatura de tempo são categorias. Gênero não é codificado
  como número para PCA. Não há normalidade assumida ou causalidade inferida.
- O catálogo acessível não é um censo de toda a plataforma Spotify.

## Referências

- Jolliffe (2002), Principal Component Analysis, 2ª ed., Springer.
  https://link.springer.com/book/10.1007/b98835
- Spotify, documentação de atributos acústicos:
  https://developer.spotify.com/documentation/web-api/reference/get-audio-features
- Fonte do catálogo:
  https://www.kaggle.com/datasets/amitanshjoshi/spotify-1million-tracks

## Próxima etapa

Interpretar esta descrição; depois pesquisar e definir dimensionamento/alocação
de uma amostra menor com referência e critérios de precisão explícitos. A busca
de letras começa apenas depois dessa definição. Nenhum tamanho foi fixado aqui.
"""
    (output / "LEIA_PRIMEIRO.md").write_text(
        text.replace("1,159,764", "1.159.764"), encoding="utf-8"
    )


def run(input_path=SOURCE, output=OUTPUT):
    input_path, output = Path(input_path).resolve(), Path(output).resolve()
    started = time.perf_counter()
    print("[1/5] Lendo o catálogo original e preparando dicionário e descrição...", flush=True)
    source_hash = digest(input_path)
    if input_path == SOURCE.resolve() and source_hash != EXPECTED_HASH:
        raise ValueError(
            "O CSV mudou em relação ao catálogo anterior; verificar a fonte antes de continuar."
        )
    rules = yaml.safe_load(RULES.read_text(encoding="utf-8"))["spotify"]
    with input_path.open(encoding="utf-8-sig", newline="") as stream:
        original_header = next(csv.reader(stream))
    header = [name or "_indice_fonte" for name in original_header]
    required = {*DEFINITIONS}
    if missing := required - set(header):
        raise ValueError("Campos necessários ausentes: " + ", ".join(sorted(missing)))
    if input_path == output or input_path.is_relative_to(output):
        raise ValueError("A pasta de saída não pode conter a fonte.")
    signature = {
        "csv_sha256": source_hash,
        "codigo_sha256": digest(Path(__file__)),
        "regras_sha256": digest(RULES),
        "versao": VERSION,
    }
    manifest = output / "resumo_descritiva.json"
    if manifest.exists():
        previous = json.loads(manifest.read_text(encoding="utf-8"))
        if previous["fontes"] != signature:
            raise ValueError(
                "Saída de outra versão; use outra pasta para preservar o trabalho anterior."
            )
        if previous.get("concluido"):
            print(f"Descrição já concluída nesta versão: {output}", flush=True)
            return previous
    output.mkdir(parents=True, exist_ok=True)
    (output / "figuras").mkdir(exist_ok=True)
    summary = {
        "concluido": False,
        "fontes": signature,
        "iniciado_em": datetime.now(UTC).isoformat(),
        "source_path": str(input_path),
        "source_bytes": input_path.stat().st_size,
        "linguagem": "Python",
        "numpy": np.__version__,
        "polars": pl.__version__,
        "matplotlib": matplotlib.__version__,
        "novo_sorteio": False,
        "busca_letras": False,
        "modelo_preditivo": False,
    }
    save_json(manifest, summary)
    frame = pl.read_csv(input_path, infer_schema=False, new_columns=header)
    if frame.height < 3:
        raise ValueError(
            "O catálogo precisa conter pelo menos três linhas para a análise multivariada."
        )
    summary.update(
        {
            "n_faixas": frame.height,
            "n_campos_originais": len(header),
            "campos_originais": original_header,
            "n_ids_distintos_nao_ausentes": frame.select(
                clean("track_id").drop_nulls().n_unique()
            ).item(),
            "n_ids_ausentes": frame.select(clean("track_id").is_null().sum()).item(),
            "n_creditos_artista_distintos": frame.select(
                clean("artist_name").drop_nulls().n_unique()
            ).item(),
            "n_titulos_distintos": frame.select(clean("track_name").drop_nulls().n_unique()).item(),
        }
    )
    frame, quality, dictionary = prepare_frame(frame, rules)
    if original_header[0] == "":
        dictionary[0]["variavel_original"] = "[coluna sem nome]"
    summary["n_generos_nao_ausentes"] = frame.select(clean("genre").drop_nulls().n_unique()).item()
    save_rows(output / "qualidade_campos.csv", quality)
    save_rows(output / "dicionario_variaveis.csv", dictionary)
    count_label = f"{frame.height:,}".replace(",", ".")
    print(f"[2/5] {count_label} faixas: distribuições, gêneros e períodos...", flush=True)
    numerical, histograms = numerical_tables(frame)
    frequencies, grouped, associations, cross = group_tables(frame)
    save_rows(output / "resumo_numerico.csv", numerical)
    save_rows(output / "histogramas.csv", histograms)
    save_rows(output / "frequencias_categoricas.csv", frequencies)
    save_rows(output / "perfis_grupos.csv", grouped)
    save_rows(output / "associacoes_grupos.csv", associations)
    cross.write_csv(output / "genero_periodo.csv")
    log_values = np.log1p(frame[derived("popularity")].drop_nulls().to_numpy())
    save_rows(
        output / "popularidade_log1p.csv",
        [{"transformacao": "log1p", **numeric_summary(log_values)}],
    )
    print("[3/5] Relações entre metadados e PCA descritiva; sem modelo preditivo...", flush=True)
    correlations, correlation_summary = correlation_tables(frame)
    pca, coefficients, scores, profiles = pca_tables(frame)
    save_rows(output / "correlacoes.csv", correlations)
    save_json(output / "resumo_correlacoes.json", correlation_summary)
    save_rows(output / "pca_coeficientes.csv", coefficients)
    save_rows(output / "pca_perfis_grupos.csv", profiles)
    save_rows(
        output / "pca_variancia.csv",
        [
            {
                "componente": i + 1,
                "autovalor": eigenvalue,
                "fracao_variancia": fraction,
                "fracao_acumulada": cumulative,
            }
            for i, (eigenvalue, fraction, cumulative) in enumerate(
                zip(
                    pca["autovalores"],
                    pca["fracao_variancia"],
                    pca["fracao_acumulada"],
                    strict=True,
                )
            )
        ],
    )
    print("[4/5] Salvando figuras e tabelas agregadas para interpretação...", flush=True)
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    plot_distributions(frame, output, frequencies)
    plot_correlations(output, correlations, correlation_summary)
    plot_groups(output, frequencies, grouped, numerical)
    plot_relationships(frame, output)
    plot_pca(output, pca, coefficients, scores)
    save_json(output / "resumo_pca.json", pca)
    write_report(output, summary, pca)
    summary.update(
        {
            "concluido": True,
            "finalizado_em": datetime.now(UTC).isoformat(),
            "segundos": time.perf_counter() - started,
            "pca_n": pca["n_casos_completos"],
            "pca_componentes_95": pca["componentes_para_95_porcento"],
            "correlacoes_n": correlation_summary["n_casos_completos"],
            "arquivos": {
                str(path.relative_to(output)).replace("\\", "/"): digest(path)
                for path in output.rglob("*")
                if path.is_file() and path != manifest
            },
        }
    )
    save_json(manifest, summary)
    print(f"[5/5] Concluído. Resultados em {output}", flush=True)
    return summary


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    run(args.input, args.output)
    return 0
