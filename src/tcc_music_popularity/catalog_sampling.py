"""Amostragem estratificada do CSV auditado, sem letras, grupos ou modelagem."""

from __future__ import annotations

import argparse
import csv
import hashlib
import inspect
import json
import math
import platform
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import polars as pl
import pyarrow
import yaml

from .catalog_audit import ACOUSTIC, QUANTILES, ROOT, markdown_table, sha256

VERSION = "1.0.0"
TOTAL = 200_000
SEED = 20261031
CERTAINTY = "C|popularity>=80"
MISSING = ["", "NA", "N/A", "null", "None"]
PERIODS = ["2000–2009", "2010–2019", "2020–2023"]
BANDS = ["0–19", "20–39", "40–59", "60–69", "70–79", "80–100"]
SCOPES = ["catalogo", "amostra_sem_pesos", "amostra_com_pesos"]
DESIGN_COLUMNS = [
    "stratum_id",
    "N_h",
    "n_h",
    "inclusion_probability",
    "sampling_weight",
    "certainty_selection",
    "seed",
    "sampling_track_id",
    "sampling_genre",
    "sampling_period",
    "sampling_popularity_band",
]
PROTOCOL = ROOT / "docs/plano_amostral_200k.md"
SUMMARY_NAME = "resumo_amostra_200k.json"


class SamplingError(ValueError):
    """Erro de validação publicável, sem expor registros individuais."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SamplingError(message)


def text_column(name: str) -> pl.Expr:
    value = pl.col(name).str.strip_chars(" ")
    return pl.when(value.is_in(MISSING)).then(None).otherwise(value)


def json_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def read_original_csv(path: Path) -> pl.DataFrame:
    # Polars 1.43 renomeou a opção; manter compatibilidade com o ambiente do projeto.
    empty = (
        {"empty_string_is_null": False}
        if "empty_string_is_null" in inspect.signature(pl.read_csv).parameters
        else {"missing_utf8_is_empty_string": True}
    )
    return pl.read_csv(
        path, infer_schema=False, encoding="utf8", try_parse_dates=False, null_values=None, **empty
    )


def allocate(counts: dict[str, int], total: int) -> list[dict[str, Any]]:
    """Reservas + maiores restos por capacidade restante, sem erro de ponto flutuante."""
    require(
        all(isinstance(n, int) and n > 0 for n in counts.values()), "Estratos devem ser não vazios."
    )
    require(0 < total <= sum(counts.values()), "Total solicitado não cabe na população.")
    high = counts.get(CERTAINTY, 0)
    rest = {key: counts[key] for key in sorted(counts) if key != CERTAINTY}
    base = {key: min(2, n) for key, n in rest.items()}
    remaining = total - high - sum(base.values())
    require(
        remaining >= 0, "Orçamento insuficiente para inclusão integral ≥80 e reservas min(2, N_h)."
    )
    capacities = {key: rest[key] - base[key] for key in rest}
    capacity = sum(capacities.values())
    require(remaining <= capacity, "Vagas excedem capacidades restantes.")
    assigned = dict(base)
    residues = {}
    for key in rest:
        whole, residue = divmod(remaining * capacities[key], capacity) if capacity else (0, 0)
        assigned[key] += whole
        residues[key] = residue
    leftover = total - high - sum(assigned.values())
    order = sorted(rest, key=lambda key: (-residues[key], key))
    for key in order[:leftover]:
        assigned[key] += 1
    if high:
        assigned[CERTAINTY] = high
    result = []
    for key in sorted(counts):
        n, selected = counts[key], assigned[key]
        require(0 < selected <= n, "Alocação inválida; interrompido antes do sorteio.")
        genre, period, band = (None, None, "80–100") if key == CERTAINTY else json.loads(key[2:])
        result.append(
            {
                "stratum_id": key,
                "genre": genre,
                "period": period,
                "popularity_band": band,
                "N_h": n,
                "n_h": selected,
                "reserved": n if key == CERTAINTY else base[key],
                "remaining_capacity": 0 if key == CERTAINTY else capacities[key],
                "remainder_numerator": 0 if key == CERTAINTY else residues[key],
                "remainder_denominator": capacity,
                "inclusion_probability": selected / n,
                "sampling_weight": n / selected,
                "certainty_selection": selected == n,
                "seed": SEED,
            }
        )
    require(sum(row["n_h"] for row in result) == total, "Soma da alocação diverge do total.")
    return result


def load_catalog(
    path: Path, audit: dict[str, Any]
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Valida toda a população antes de atribuir estratos/sortear; não filtra casos."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        header = next(csv.reader(stream), [])
    expected_header = [row["original_header"] for row in audit["structure"]["schema"]]
    required = {"track_id", "track_name", "artist_name", "popularity", "genre", "year", *ACOUSTIC}
    require(
        len(header) == len(set(header)) and header == expected_header,
        "Schema/cabeçalhos divergem da auditoria; nenhuma correção automática.",
    )
    require(
        required <= set(header), "Faltam campos essenciais ou alguma das 13 variáveis acústicas."
    )
    require(
        not set(header).intersection(DESIGN_COLUMNS)
        and not any(c.startswith("_s_") for c in header),
        "Coluna original colide com campo reservado do desenho amostral.",
    )
    raw = read_original_csv(path)
    require(
        raw.columns == header, "Leitor alterou cabeçalhos originais; processamento interrompido."
    )
    frame = raw.select(
        text_column("track_id").alias("_s_id"),
        text_column("genre").alias("_s_genre"),
        text_column("artist_name").alias("_s_artist"),
        text_column("track_name").alias("_s_title"),
        text_column("popularity").cast(pl.Float64, strict=False).alias("_s_pop"),
        text_column("year").cast(pl.Float64, strict=False).alias("_s_year"),
        text_column("year").alias("_s_year_text"),
    ).with_row_index("_s_row")
    counts = {
        "rows": raw.height,
        "distinct_track_ids": frame["_s_id"].drop_nulls().n_unique(),
        "missing_track_ids": frame["_s_id"].null_count(),
    }
    counts["duplicate_id_excess_rows"] = (
        raw.height - counts["missing_track_ids"] - counts["distinct_track_ids"]
    )
    require(
        counts["missing_track_ids"] == 0 and counts["duplicate_id_excess_rows"] == 0,
        f"IDs ausentes/repetidos: {counts}. Duplicatas iguais ou conflitantes bloqueiam o sorteio; não deduplicar.",
    )
    pop = pl.col("_s_pop")
    valid_pop = (pop.is_finite() & pop.is_between(0, 100) & (pop == pop.floor())).fill_null(False)
    invalid_pop = frame.filter(~valid_pop).height
    require(
        invalid_pop == 0,
        f"Há {invalid_pop} popularidades ausentes/inválidas; nenhum sorteio realizado.",
    )
    counts["popularity_ge_80"] = frame.filter(pop >= 80).height
    observed = audit["scopes"]["linha"]
    require(
        counts["rows"] == audit["structure"]["rows"] == observed["n"]
        and counts["distinct_track_ids"] == audit["duplicates"]["distinct_ids"]
        and counts["popularity_ge_80"] == observed["popularity"]["thresholds_overlapping"]["80"],
        "Recontagem de linhas, IDs ou popularidade ≥80 diverge da auditoria; interrompido antes do sorteio.",
    )
    y = pl.col("_s_year")
    valid_year = (
        pl.col("_s_year_text").str.contains(r"^[0-9]{4}$")
        & y.is_finite()
        & y.is_between(2000, 2023)
        & (y == y.floor())
    ).fill_null(False)
    require(
        frame.filter(~valid_year).height == 0 and frame["_s_genre"].null_count() == 0,
        "Novidade material: year fora de 2000–2023/inválido ou gênero ausente. Não excluir; revisar protocolo.",
    )
    year_counts = {str(int(k)): v for k, v in frame.group_by("_s_year").len().iter_rows()}
    genre_counts = dict(frame.group_by("_s_genre").len().iter_rows())
    require(
        year_counts == {r["year"]: r["n"] for r in observed["time"]["year"]["annual"]},
        "Domínio/contagens anuais divergem da auditoria; revisar antes de sortear.",
    )
    require(
        genre_counts == {r["genre"]: r["n"] for r in observed["genres"]},
        "Domínio/contagens de gêneros divergem da auditoria; não reagrupar/excluir automaticamente.",
    )
    frame = frame.with_columns(
        pl.when(y <= 2009)
        .then(pl.lit(PERIODS[0]))
        .when(y <= 2019)
        .then(pl.lit(PERIODS[1]))
        .otherwise(pl.lit(PERIODS[2]))
        .alias("_s_period"),
        pl.when(pop < 20)
        .then(pl.lit(BANDS[0]))
        .when(pop < 40)
        .then(pl.lit(BANDS[1]))
        .when(pop < 60)
        .then(pl.lit(BANDS[2]))
        .when(pop < 70)
        .then(pl.lit(BANDS[3]))
        .when(pop < 80)
        .then(pl.lit(BANDS[4]))
        .otherwise(pl.lit(BANDS[5]))
        .alias("_s_band"),
    )
    # Codificar só combinações distintas, não executar função Python por faixa.
    keys = (
        frame.select("_s_genre", "_s_period", "_s_band")
        .unique()
        .sort(["_s_genre", "_s_period", "_s_band"])
    )
    stratum = [
        CERTAINTY
        if b == BANDS[5]
        else "S|" + json.dumps([g, p, b], ensure_ascii=False, separators=(",", ":"))
        for g, p, b in keys.iter_rows()
    ]
    keys = keys.with_columns(pl.Series("stratum_id", stratum))
    frame = frame.join(keys, on=["_s_genre", "_s_period", "_s_band"], how="left", validate="m:1")
    counts["identity"] = identity(frame)
    counts["genres"] = genre_counts
    counts["years"] = year_counts
    return raw, frame, counts


def identity(frame: pl.DataFrame) -> dict[str, int]:
    return {
        "rows": frame.height,
        "distinct_track_ids": frame["_s_id"].drop_nulls().n_unique(),
        "distinct_title_strings": frame["_s_title"].drop_nulls().n_unique(),
        "distinct_artist_credit_strings": frame["_s_artist"].drop_nulls().n_unique(),
        "distinct_complete_artist_title_pairs": frame.filter(
            pl.col("_s_artist").is_not_null() & pl.col("_s_title").is_not_null()
        )
        .select("_s_artist", "_s_title")
        .unique()
        .height,
        "missing_track_ids": frame["_s_id"].null_count(),
        "missing_titles": frame["_s_title"].null_count(),
        "missing_artist_credits": frame["_s_artist"].null_count(),
        "incomplete_artist_title_pairs": frame.filter(
            pl.col("_s_artist").is_null() | pl.col("_s_title").is_null()
        ).height,
    }


def draw(frame: pl.DataFrame, allocation: list[dict[str, Any]]) -> np.ndarray:
    """PCG64; ordem Unicode estável de estratos/IDs; uma AAS sem reposição por estrato."""
    ordered = frame.select("stratum_id", "_s_id", "_s_row").sort(["stratum_id", "_s_id"])
    require(ordered.height == sum(r["N_h"] for r in allocation), "Moldura e alocação divergem.")
    rng = np.random.Generator(np.random.PCG64(SEED))
    parts = []
    offset = 0
    for row in allocation:
        block = ordered.slice(offset, row["N_h"])
        require(
            block["stratum_id"].n_unique() == 1 and block["stratum_id"][0] == row["stratum_id"],
            "Ordenação/alocação de estratos inconsistente.",
        )
        indices = (
            np.arange(row["N_h"])
            if row["certainty_selection"]
            else rng.choice(row["N_h"], row["n_h"], replace=False)
        )
        parts.append(block["_s_row"].to_numpy()[indices])
        offset += row["N_h"]
    return np.concatenate(parts)


def weighted_summary(values: np.ndarray, weights: np.ndarray) -> dict[str, float | int | None]:
    """Momentos descritivos com divisor soma(w), não erro-padrão/variância do desenho."""
    finite = np.isfinite(values)
    x, w = values[finite], weights[finite]
    result: dict[str, Any] = {"n_observed": int(finite.sum()), "weight_observed": float(w.sum())}
    if not len(x):
        return {
            **result,
            "mean": None,
            "std_population": None,
            "min": None,
            "max": None,
            **{f"q{int(q * 100):02d}": None for q in QUANTILES},
        }
    mean = float(np.average(x, weights=w))
    order = np.argsort(x, kind="stable")
    cumulative = np.cumsum(w[order], dtype=np.float64)
    # Inversa da CDF empírica: menor x cuja soma acumulada de pesos atinge q*W.
    indices = np.searchsorted(cumulative, np.array(QUANTILES) * cumulative[-1], side="left")
    result.update(
        {
            "mean": mean,
            "std_population": float(np.sqrt(np.average((x - mean) ** 2, weights=w))),
            "min": float(x.min()),
            "max": float(x.max()),
            **{
                f"q{int(q * 100):02d}": float(x[order][i])
                for q, i in zip(QUANTILES, indices, strict=True)
            },
        }
    )
    return result


def numeric_values(frame: pl.DataFrame, name: str) -> tuple[np.ndarray, np.ndarray]:
    parsed = frame.select(text_column(name).alias("text"))
    missing = parsed["text"].is_null().to_numpy()
    x = parsed["text"].cast(pl.Float64, strict=False).to_numpy()
    return x, missing


def domain_mask(x: np.ndarray, field: str, rules: dict[str, Any]) -> tuple[np.ndarray, str]:
    if field in rules["unit_interval"]:
        return (x >= 0) & (x <= 1), "[0,1]"
    if field + "_values" in rules:
        return np.isin(x, rules[field + "_values"]), str(rules[field + "_values"])
    if field + "_min_exclusive" in rules:
        minimum = rules[field + "_min_exclusive"]
        return x > minimum, f">{minimum}"
    return np.ones(len(x), dtype=bool), "sem limite numérico documentado (somente finitude)"


class Comparison:
    def __init__(self):
        self.rows: list[dict[str, Any]] = []

    def emit(
        self,
        scope: str,
        section: str,
        variable: str,
        category: Any,
        metrics: dict[str, Any],
        denominator: float | None = None,
    ) -> None:
        for metric, value in metrics.items():
            self.rows.append(
                {
                    "scope": scope,
                    "section": section,
                    "variable": variable,
                    "category": category,
                    "metric": metric,
                    "value": value,
                    "denominator": denominator,
                }
            )

    def distributions(
        self, frame: pl.DataFrame, weights: np.ndarray, scope: str, domains: dict[str, list[Any]]
    ) -> None:
        for field, categories in domains.items():
            grouped = (
                frame.select(field)
                .with_columns(pl.Series("weight", weights))
                .group_by(field)
                .agg(pl.len().alias("n_observed"), pl.col("weight").sum().alias("count"))
            )
            lookup = {r[field]: r for r in grouped.to_dicts()}
            for category in categories:
                row = lookup.get(category, {"count": 0.0, "n_observed": 0})
                self.emit(
                    scope,
                    "distribution",
                    field,
                    category,
                    {
                        "n_observed": row["n_observed"],
                        "count": float(row["count"]),
                        "fraction": float(row["count"] / weights.sum()),
                    },
                    float(weights.sum()),
                )

    def describe(
        self,
        raw: pl.DataFrame,
        frame: pl.DataFrame,
        weights: np.ndarray,
        scope: str,
        rules: dict[str, Any],
        domains: dict[str, list[Any]],
    ) -> None:
        total = float(weights.sum())
        for field in ["popularity", *ACOUSTIC]:
            x, missing = numeric_values(raw, field)
            finite = np.isfinite(x)
            in_domain, _ = domain_mask(x, field, rules)
            if field == "popularity":
                in_domain = (x >= 0) & (x <= 100) & (x == np.floor(x))
            for category, mask in [
                ("missing", missing),
                ("invalid_parse_or_nonfinite", ~missing & ~finite),
                ("out_of_local_domain", finite & ~in_domain),
            ]:
                self.emit(
                    scope,
                    "quality",
                    field,
                    category,
                    {
                        "n_observed": int(mask.sum()),
                        "count": float(weights[mask].sum()),
                        "fraction": float(weights[mask].sum() / total),
                    },
                    total,
                )
            self.emit(scope, "numeric_all_finite", field, "", weighted_summary(x, weights), total)
            if field != "popularity":
                valid_x = np.where(in_domain & finite, x, np.nan)
                self.emit(
                    scope,
                    "numeric_valid_domain",
                    field,
                    "",
                    weighted_summary(valid_x, weights),
                    total,
                )
        self.distributions(frame, weights, scope, domains)
        for key, value in identity(frame).items():
            # Contagens distintas permanecem observadas, inclusive no escopo ponderado.
            self.emit(
                scope, "identity_observed_not_population_estimate", key, "", {"n_observed": value}
            )
        artist_rows = frame.select("_s_artist").with_columns(pl.Series("weight", weights))
        known = artist_rows.filter(pl.col("_s_artist").is_not_null())
        missing_weights = total - float(known["weight"].sum())
        self.emit(
            scope,
            "artist_credits",
            "missing",
            "",
            {"count": missing_weights, "fraction": missing_weights / total},
            total,
        )
        grouped = (
            known.group_by("_s_artist")
            .agg(pl.len().alias("n_observed"), pl.col("weight").sum().alias("count"))
            .sort(["count", "_s_artist"], descending=[True, False])
        )
        denominator = float(grouped["count"].sum())
        for top in (1, 10, 100, 1000):
            count = float(grouped.head(top)["count"].sum())
            self.emit(
                scope,
                "artist_concentration_observed_credits",
                "top",
                top,
                {
                    "credits_included": min(top, grouped.height),
                    "count": count,
                    "fraction_known_credits": count / denominator if denominator else None,
                    "fraction_all": count / total,
                },
                denominator,
            )
        # Histograma do número observado de faixas por crédito: não inflar riqueza com pesos.
        for frequency, credits in (
            grouped.group_by("n_observed").len().sort("n_observed").iter_rows()
        ):
            self.emit(
                scope,
                "artist_observed_frequency_not_population_estimate",
                "tracks_per_credit",
                frequency,
                {"observed_credits": credits},
            )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def comparison_plots(rows: list[dict[str, Any]], output: Path) -> list[str]:
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    lookup = {
        (r["scope"], r["variable"], str(r["category"]), r["metric"]): r["value"]
        for r in rows
        if r["section"] == "distribution"
    }
    genres = sorted(
        {
            str(r["category"])
            for r in rows
            if r["section"] == "distribution" and r["variable"] == "_s_genre"
        }
    )
    genres.sort(key=lambda g: (-lookup[(SCOPES[0], "_s_genre", g, "count")], g))
    plans = [
        ("popularidade", "_s_band", BANDS, "Popularidade: bandas do desenho"),
        ("genero", "_s_genre", genres[:20], "Gênero: 20 mais frequentes no catálogo"),
        ("periodo", "_s_period", PERIODS, "Período do campo year"),
    ]
    files = []
    colors = ["#406a8c", "#d58e38", "#3f886e"]
    for slug, field, categories, title in plans:
        fig, ax = plt.subplots(figsize=(13, 7), layout="constrained")
        x = np.arange(len(categories))
        for i, (scope, color) in enumerate(zip(SCOPES, colors, strict=True)):
            values = [
                100 * lookup.get((scope, field, category, "fraction"), 0) for category in categories
            ]
            ax.bar(x + (i - 1) * 0.25, values, width=0.25, color=color, label=scope)
        ax.set_xticks(
            x,
            categories,
            rotation=60 if slug == "genero" else 0,
            ha="right" if slug == "genero" else "center",
        )
        ax.set_ylabel("Percentual do total de faixas (ou soma dos pesos)")
        ax.set_title(title)
        ax.set_ylim(
            0,
            max(
                1,
                max(
                    100 * lookup.get((scope, field, category, "fraction"), 0)
                    for scope in SCOPES
                    for category in categories
                ),
            )
            * 1.25,
        )
        ax.legend(loc="upper right")
        if slug == "popularidade":
            lines = ["Faixa    Catálogo N    Amostra n    Estimativa ponderada"]
            for band, lower, upper in [
                ("60–69", 60, 69),
                ("70–79", 70, 79),
                ("80–89", 80, 89),
                ("90–100", 90, 100),
            ]:
                counts = [
                    sum(
                        lookup.get((scope, "_s_pop", str(value), "count"), 0)
                        for value in range(lower, upper + 1)
                    )
                    for scope in SCOPES
                ]
                lines.append(
                    f"{band}:    {counts[0]:,.0f}    |    {counts[1]:,.0f}    |    {counts[2]:,.2f}"
                )
            ax.text(
                0.98,
                0.64,
                "\n".join(lines),
                transform=ax.transAxes,
                ha="right",
                va="top",
                fontsize=9,
                bbox={"facecolor": "white", "edgecolor": "#aaaaaa", "alpha": 0.95},
            )
        filename = f"comparacao_{slug}_200k.png"
        fig.savefig(output / filename, dpi=150)
        plt.close(fig)
        files.append(filename)
    return files


def result_report(summary: dict[str, Any], comparison: list[dict[str, Any]]) -> str:
    counts = summary["catalog_counts"]
    selected = summary["sample_identity"]
    sections = [
        "# Relatório da amostra Spotify",
        f"Execução: {summary['started_at']}. Status final verificável no JSON.",
        f"Catálogo: {counts['rows']:,} faixas. Amostra: {selected['rows']:,} IDs. "
        f"Inclusão integral ≥80: {counts['popularity_ge_80']:,} faixas, já dentro do total.",
        "## Reconciliação antes do sorteio",
        markdown_table(
            [{"metric": k, "observed": v} for k, v in counts.items() if isinstance(v, int)],
            ["metric", "observed"],
        ),
        "SHA-256 do CSV conferido contra auditoria: `" + summary["input_sha256"] + "`. "
        "Contagens anuais e por gênero reconciliadas exatamente; nenhuma linha rejeitada/corrigida.",
        "## Complemento de identidade",
        markdown_table(
            [
                {"metric": k, "catalogo": v, "amostra_observada": selected[k]}
                for k, v in counts["identity"].items()
            ],
            ["metric", "catalogo", "amostra_observada"],
        ),
        "Strings: trim de espaços U+0020; tokens de ausência exatos '', NA, N/A, null, None. "
        "Sem normalização de caixa, acentos, aliases ou colaborações. Títulos distintos não são composições únicas; créditos textuais não identificam pessoas. Originais preservados no Parquet.",
        "## Alocação e verificações",
        markdown_table([summary["allocation_summary"]], list(summary["allocation_summary"])),
        markdown_table(
            [{"check": k, "value": v} for k, v in summary["checks"].items()], ["check", "value"]
        ),
        "## Comparação descritiva",
        "Resumo numérico: mesmos quantis por inversa da CDF e desvio-padrão descritivo com divisor soma(w) nos três escopos; não é erro-padrão do desenho. A auditoria anterior usou quantis interpolados/desvio n−1, portanto pequenas diferenças de convenção são esperadas.",
    ]
    for field in ["popularity", *ACOUSTIC]:
        rows = []
        for scope in SCOPES:
            metrics = {
                r["metric"]: r["value"]
                for r in comparison
                if r["scope"] == scope
                and r["section"] == "numeric_all_finite"
                and r["variable"] == field
            }
            rows.append({"scope": scope, **metrics})
        sections += [
            f"### {field}: todos os valores finitos",
            markdown_table(
                rows,
                [
                    "scope",
                    "n_observed",
                    "weight_observed",
                    "mean",
                    "std_population",
                    "q01",
                    "q05",
                    "q25",
                    "q50",
                    "q75",
                    "q95",
                    "q99",
                ],
            ),
        ]
    sections += [
        "## Qualidade e domínios locais",
        markdown_table(
            [r for r in comparison if r["section"] == "quality" and r["metric"] == "count"],
            ["scope", "variable", "category", "value", "denominator"],
        ),
        "O CSV também inclui frequências relativas, n observado, resumos restritos ao domínio local e todos os valores 0–100. Dados acústicos inválidos não excluem faixas; são omitidos somente do resumo numérico aplicável.",
        "## Créditos de artista e concentração",
        "Contagens distintas são observadas, sem extrapolação por soma de pesos. A concentração ponderada ordena créditos observados pela soma dos pesos de suas faixas; é um resumo plug-in, não estimativa não enviesada do ranking ou da riqueza de artistas.",
        markdown_table(
            [
                r
                for r in comparison
                if r["section"] == "artist_concentration_observed_credits"
                and r["metric"] in ("count", "fraction_known_credits")
            ],
            ["scope", "category", "metric", "value", "denominator"],
        ),
        "## Gráficos",
        *[f"![{name}]({name})" for name in summary["plots"]],
        "## Interpretação e limites",
        "Diferenças sem pesos são esperadas: inclusão integral da alta popularidade e reservas mínimas tornam a alocação desproporcional. Totais ponderados de gênero, período e bandas do desenho coincidem por construção, salvo arredondamento numérico; isso não prova validade externa. Anos individuais, valores pontuais de popularidade e atributos acústicos podem diferir.",
        "Inferência descritiva restrita ao catálogo identificado pelo hash; não a todo o Spotify. 200 mil é decisão operacional, não tamanho ótimo ou garantia de erro preditivo pequeno. Não há teste de significância como selo de representatividade.",
        "Letras futuras podem introduzir seleção adicional que os pesos não corrigem automaticamente. A amostra original é preservada mesmo sem letra e não haverá substituição automática. Splits e dependência entre artistas/versões serão tratados posteriormente; nenhum grupo de composição foi criado.",
        "O teste V0.6 já foi aberto em 14/10/2026; novo sorteio não apaga a exposição nem restaura independência. É necessária reconciliação futura com registros e grupos do estudo anterior.",
        "Regras, fórmulas e referências metodológicas estão em plano_amostral_200k.md. A amostra individual fica local e fora do Git; compartilhe somente agregados.",
    ]
    return "\n\n".join(sections) + "\n"


def run(
    input_path: Path,
    audit_path: Path,
    output: Path,
    *,
    total: int = TOTAL,
    command: list[str] | None = None,
) -> dict[str, Any]:
    """Total alternativo é apenas API para fixtures; CLI fixa 200k/seed, sem override."""
    started = time.perf_counter()
    input_path, audit_path, output = input_path.resolve(), audit_path.resolve(), output.resolve()
    require(
        input_path.is_file() and input_path.suffix.lower() == ".csv",
        "Entrada deve ser CSV existente.",
    )
    require(audit_path.is_file(), "Resumo JSON da auditoria não encontrado.")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    require(
        audit.get("completed") is True and audit.get("status") == "completed",
        "Auditoria não está completa.",
    )
    require(
        not output.is_relative_to(ROOT / "data") and output != input_path.parent,
        "Use pasta própria de relatórios, fora da pasta de entrada/data.",
    )
    print("[1/7] Conferindo hash do CSV e vínculo com a auditoria...", flush=True)
    actual_hash = sha256(input_path)
    require(
        actual_hash == audit["input"]["sha256"]
        and input_path.stat().st_size == audit["input"]["size_bytes"],
        "Arquivo diverge do SHA-256/tamanho registrado na auditoria. Sorteio bloqueado.",
    )
    rules_path = ROOT / "configs/quality_rules.yaml"
    rules = yaml.safe_load(rules_path.read_text(encoding="utf-8"))["spotify"]
    require(
        rules == audit["quality_rules"]["rules"],
        "Regras locais mudaram desde a auditoria; revisar antes de sortear.",
    )
    config = {
        "total": total,
        "seed": SEED,
        "version": VERSION,
        "input_sha256": actual_hash,
        "input_size_bytes": input_path.stat().st_size,
        "audit_sha256": sha256(audit_path),
        "rules_sha256": sha256(rules_path),
        "code_sha256": sha256(Path(__file__)),
        "audit_helpers_sha256": sha256(ROOT / "src/tcc_music_popularity/catalog_audit.py"),
        "wrapper_sha256": sha256(ROOT / "scripts/12_sortear_amostra_spotify_200k.py"),
        "protocol_sha256": sha256(PROTOCOL),
        "generator": "numpy.random.Generator(PCG64); choice(replace=False)",
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "polars": pl.__version__,
            "pyarrow": pyarrow.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "ordering": "estratos e IDs em ordem lexicográfica Unicode crescente",
        "allocation": "min(2,N_h), capacidade residual, maiores restos inteiros, desempate stratum_id",
        "periods": PERIODS,
        "popularity_bands": BANDS,
    }
    fingerprint = json_hash(config)
    if output.exists():
        previous_path = output / SUMMARY_NAME
        require(
            previous_path.is_file(),
            "Pasta de saída já existe sem resumo; nenhum arquivo será sobrescrito.",
        )
        previous = json.loads(previous_path.read_text(encoding="utf-8"))
        require(
            previous.get("status") == "completed"
            and previous.get("configuration_hash") == fingerprint,
            "Saída existente incompleta ou configuração/versões diferentes. Amostra preservada; não gerar alternativa automaticamente.",
        )
        for name, digest in previous["output_hashes"].items():
            require(Path(name).name == name, "Manifesto de saída contém nome incompatível.")
            require(
                (output / name).is_file() and sha256(output / name) == digest,
                f"Artefato existente alterado/ausente: {name}. Nenhuma sobrescrita ou novo sorteio.",
            )
        print(
            "Execução idêntica já concluída: hashes verificados; amostra preservada, sem novo sorteio.",
            flush=True,
        )
        return previous
    output.mkdir(parents=True, exist_ok=False)
    summary: dict[str, Any] = {
        "status": "incomplete",
        "completed": False,
        "started_at": datetime.now(UTC).isoformat(),
        "configuration": config,
        "configuration_hash": fingerprint,
        "input": str(input_path),
        "input_sha256": actual_hash,
        "audit": str(audit_path),
        "command_argv": command if command is not None else [sys.executable, *sys.argv],
        "originals_preserved": True,
        "rejected_rows": 0,
    }

    def save() -> None:
        summary["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        pending = output / (SUMMARY_NAME + ".tmp")
        pending.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8"
        )
        pending.replace(output / SUMMARY_NAME)

    save()
    try:
        print("[2/7] Recontando catálogo e validando domínios; nenhuma exclusão...", flush=True)
        raw, frame, counts = load_catalog(input_path, audit)
        summary["catalog_counts"] = counts
        save()
        print("[3/7] Calculando reservas e maiores restos...", flush=True)
        allocation = allocate(dict(frame.group_by("stratum_id").len().iter_rows()), total)
        allocation_frame = pl.DataFrame(allocation)
        summary["allocation_summary"] = {
            "strata": len(allocation),
            "certainty_strata": sum(r["certainty_selection"] for r in allocation),
            "reserved_units": sum(r["reserved"] for r in allocation),
            "population": sum(r["N_h"] for r in allocation),
            "sample": sum(r["n_h"] for r in allocation),
        }
        print(
            "[4/7] Sorteando sem reposição com seed fixa e verificando reprodução exata...",
            flush=True,
        )
        indices = draw(frame, allocation)
        require(
            np.array_equal(indices, draw(frame, allocation)), "Reprodução com a mesma seed falhou."
        )
        selected = frame.filter(pl.col("_s_row").is_in(indices)).sort("_s_id")
        metadata = selected.join(
            allocation_frame.select(
                "stratum_id",
                "N_h",
                "n_h",
                "inclusion_probability",
                "sampling_weight",
                "certainty_selection",
                "seed",
            ),
            on="stratum_id",
            how="left",
            validate="m:1",
        ).sort("_s_id")
        row_indices = metadata["_s_row"].to_numpy()
        sample_raw = raw[row_indices]
        sample = sample_raw.hstack(
            metadata.select(
                "stratum_id",
                "N_h",
                "n_h",
                "inclusion_probability",
                "sampling_weight",
                "certainty_selection",
                "seed",
                pl.col("_s_id").alias("sampling_track_id"),
                pl.col("_s_genre").alias("sampling_genre"),
                pl.col("_s_period").alias("sampling_period"),
                pl.col("_s_band").alias("sampling_popularity_band"),
            )
        )
        weights = metadata["sampling_weight"].to_numpy()
        realized = dict(metadata.group_by("stratum_id").len().iter_rows())
        checks = {
            "exact_total": sample.height == total,
            "unique_ids": metadata["_s_id"].n_unique() == total,
            "all_ids_in_catalog": metadata.join(
                frame.select("_s_id"), on="_s_id", how="anti"
            ).height
            == 0,
            "all_ge80_included": metadata.filter(pl.col("_s_pop") >= 80).height
            == counts["popularity_ge_80"],
            "allocation_matches": realized == {r["stratum_id"]: r["n_h"] for r in allocation},
            "probabilities_valid": bool(
                metadata["inclusion_probability"].is_between(0, 1, closed="right").all()
            ),
            "weights_finite_positive": bool(np.all(np.isfinite(weights) & (weights > 0))),
            "weight_sum_matches_population": math.isclose(
                math.fsum(weights), raw.height, rel_tol=1e-12, abs_tol=1e-6
            ),
            "same_seed_reproduced": True,
            "original_columns_preserved": sample.select(raw.columns).equals(sample_raw),
        }
        require(all(checks.values()), "Falha nas verificações do desenho; saída não concluída.")
        summary["checks"] = checks
        summary["weight_sum"] = math.fsum(weights)
        summary["weight_sum_tolerance"] = {"relative": 1e-12, "absolute": 1e-6}
        summary["sample_identity"] = identity(metadata)
        summary["selected_ids_sha256"] = json_hash(metadata["_s_id"].to_list())
        summary["original_schema"] = {name: str(dtype) for name, dtype in raw.schema.items()}
        summary["sample_schema"] = {name: str(dtype) for name, dtype in sample.schema.items()}
        save()
        print("[5/7] Comparando catálogo, amostra sem pesos e com pesos...", flush=True)
        # frame foi unido às chaves; restabelecer ordem do CSV antes de ligar pesos/valores.
        frame = frame.sort("_s_row")
        domains = {
            "_s_pop": list(range(101)),
            "_s_band": BANDS,
            "_s_genre": sorted(counts["genres"]),
            "_s_year": list(range(2000, 2024)),
            "_s_period": PERIODS,
        }
        comparison = Comparison()
        comparison.describe(raw, frame, np.ones(raw.height), SCOPES[0], rules, domains)
        comparison.describe(sample_raw, metadata, np.ones(sample.height), SCOPES[1], rules, domains)
        comparison.describe(sample_raw, metadata, weights, SCOPES[2], rules, domains)
        margins = {
            (r["scope"], r["variable"], str(r["category"])): r["value"]
            for r in comparison.rows
            if r["section"] == "distribution" and r["metric"] == "count"
        }
        calibrated = all(
            math.isclose(
                margins[(SCOPES[0], field, str(category))],
                margins[(SCOPES[2], field, str(category))],
                rel_tol=1e-12,
                abs_tol=1e-6,
            )
            for field in ("_s_band", "_s_genre", "_s_period")
            for category in domains[field]
        )
        require(calibrated, "Totais ponderados das margens do desenho não foram preservados.")
        summary["checks"]["weighted_design_margins_match"] = calibrated
        print("[6/7] Gravando amostra local, alocação, protocolo e agregados...", flush=True)
        sample_path = output / "amostra_spotify_200k.parquet"
        sample.write_parquet(sample_path, compression="zstd")
        readback = pl.read_parquet(sample_path)
        require(readback.equals(sample), "Parquet relido diverge dos campos originais/desenho.")
        del readback
        summary["checks"]["parquet_roundtrip_equal"] = True
        write_csv(output / "alocacao_amostra_200k.csv", allocation)
        write_csv(output / "comparacao_catalogo_amostra_200k.csv", comparison.rows)
        (output / "plano_amostral_200k.md").write_text(
            PROTOCOL.read_text(encoding="utf-8"), encoding="utf-8"
        )
        summary["plots"] = comparison_plots(comparison.rows, output)
        print("[7/7] Verificando integridade final e registrando hashes...", flush=True)
        require(
            sha256(input_path) == actual_hash,
            "Entrada mudou durante o processamento; resultado incompleto.",
        )
        summary["checks"]["input_hash_unchanged"] = True
        (output / "relatorio_amostra_200k.md").write_text(
            result_report(summary, comparison.rows), encoding="utf-8"
        )
        summary["output_hashes"] = {
            p.name: sha256(p)
            for p in sorted(output.iterdir())
            if p.is_file() and p.name != SUMMARY_NAME
        }
        summary["status"] = "completed"
        summary["completed"] = True
        summary["finished_at"] = datetime.now(UTC).isoformat()
    except BaseException as exc:
        summary["error_type"] = type(exc).__name__
        summary["error"] = (
            str(exc)
            if isinstance(exc, SamplingError)
            else "Falha de execução; verifique schema, memória, permissões e espaço. Dados individuais não são registrados no erro."
        )
        raise
    finally:
        save()
    print(f"Concluído: {output}", flush=True)
    return summary


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Amostra Spotify fixa: 200.000 IDs, seed 20261031; offline."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument(
        "--audit", required=True, type=Path, help="resumo_catalogo_spotify.json concluído"
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Pasta nova; reexecução idêntica só verifica/preserva",
    )
    args = parser.parse_args(argv)
    try:
        reference = json.loads(args.audit.read_text(encoding="utf-8"))
        require(
            reference["structure"]["rows"] == 1_159_764
            and reference["scopes"]["linha"]["popularity"]["thresholds_overlapping"]["80"] == 499,
            "Auditoria não corresponde à referência declarada (1.159.764 linhas; 499 ≥80). Revisar protocolo.",
        )
        run(
            args.input,
            args.audit,
            args.output,
            command=[sys.executable, sys.argv[0], *(argv if argv is not None else sys.argv[1:])],
        )
    except SamplingError as exc:
        print(f"Sorteio bloqueado: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print(
            "Interrompido; preserve os arquivos e confira status incompleto no JSON.",
            file=sys.stderr,
        )
        return 130
    except Exception as exc:
        print(
            f"Falha ({type(exc).__name__}); confira entrada, auditoria, permissões e espaço. Nenhum resultado deve ser usado sem status completed.",
            file=sys.stderr,
        )
        return 1
    return 0
