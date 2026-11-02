"""Diagnóstico de domínio e equivalência: somente arquivos locais de resultados/agregados."""

import argparse
import json
import math
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import t

from . import lyrics_recovery as reuse
from . import sample_lyrics as base
from .manual_lyrics import atomic_json, require

PROTOCOL = base.ROOT / "docs/protocolo_parecer_estatistico_letras.md"
NUMERIC = [
    "popularity",
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
    "year",
]


def design_arrays(frame):
    _, first, inverse = np.unique(
        frame["stratum_id"].to_numpy(), return_index=True, return_inverse=True
    )
    N, n = frame["N_h"].to_numpy()[first], frame["n_h"].to_numpy()[first]
    require(
        np.array_equal(np.bincount(inverse), n),
        "Variância exige amostra integral dentro de cada estrato.",
    )
    return inverse, N, n


def domain_ratio(y, domain, frame, weighted=True, design=None):
    """Taylor de razão, todos os n_h originais; z=I_D I_valido(y-R)."""
    valid = domain & np.isfinite(y)
    weights = frame["sampling_weight"].to_numpy() if weighted else np.ones(frame.height)
    denominator = float(weights[valid].sum())
    if not denominator:
        return {
            "estimate": None,
            "se": None,
            "df": None,
            "n": 0,
            "denominator": 0,
            "variance_supported": False,
        }
    estimate = float(np.sum(weights[valid] * y[valid]) / denominator)
    z = np.where(valid, np.nan_to_num(y) - estimate, 0)
    inverse, N, n = design if design is not None else design_arrays(frame)
    noncensus = n < N
    supported, census = not np.any(noncensus & (n < 2)), not np.any(noncensus)
    active = noncensus & (n >= 2)
    sums, squares = np.bincount(inverse, weights=z), np.bincount(inverse, weights=z * z)
    s2 = np.maximum(0, squares[active] - sums[active] ** 2 / n[active]) / (n[active] - 1)
    factor = N[active] if weighted else n[active]
    components = factor**2 * (1 - n[active] / N[active]) * s2 / n[active] / denominator**2
    dfs = n[active] - 1
    variance = float(components.sum())
    df = (
        variance**2 / sum(c * c / d for c, d in zip(components, dfs, strict=True))
        if variance > 0
        else math.inf
    )
    supported &= census or variance > 0  # zero estimado fora de censo não é certeza
    return {
        "estimate": estimate,
        "se": math.sqrt(variance) if supported else None,
        "df": df,
        "n": int(valid.sum()),
        "denominator": denominator,
        "variance_supported": supported,
    }


def equivalence(stats, reference, margin, family_size=1):
    result = {
        "catalog_estimate": reference,
        "margin": margin,
        "difference": None,
        "ci90_low": None,
        "ci90_high": None,
        "ci95_low": None,
        "ci95_high": None,
        "family_low": None,
        "family_high": None,
        "p_tost": None,
        "conclusion": "inconclusive",
        "family_relevant": False,
    }
    if stats["estimate"] is None:
        return result
    d = stats["estimate"] - reference
    result["difference"] = d
    if stats["se"] is None or stats["n"] < 20 or margin <= 0:
        return result
    se, df = stats["se"], stats["df"]
    for label, alpha in (("ci90", 0.10), ("ci95", 0.05), ("family", 0.05 / family_size)):
        half = float(t.ppf(1 - alpha / 2, df)) * se
        result[label + "_low"], result[label + "_high"] = d - half, d + half
    result["p_tost"] = (
        max(float(t.sf((d + margin) / se, df)), float(t.cdf((d - margin) / se, df)))
        if se
        else (0.0 if abs(d) < margin else 1.0)
    )
    if result["ci90_low"] > -margin and result["ci90_high"] < margin:
        result["conclusion"] = "equivalent"
    elif result["ci95_low"] > margin or result["ci95_high"] < -margin:
        result["conclusion"] = "relevant_difference"
    result["family_relevant"] = result["family_low"] > margin or result["family_high"] < -margin
    return result


def catalog_targets(aggregates):
    rows = aggregates.filter(pl.col("scope") == "catalogo").to_dicts()
    lookup = {
        (r["section"], r["variable"], r["metric"]): float(r["value"])
        for r in rows
        if r["section"] == "numeric_all_finite" and r["value"] is not None
    }
    targets = []
    for name in NUMERIC:
        if name == "year":
            years = [
                r
                for r in rows
                if r["section"] == "distribution"
                and r["variable"] == "_s_year"
                and r["metric"] == "count"
            ]
            x, w = (
                np.array([float(r["category"]) for r in years]),
                np.array([float(r["value"]) for r in years]),
            )
            mean = float(np.average(x, weights=w))
            sd = float(np.sqrt(np.average((x - mean) ** 2, weights=w)))
        else:
            mean, sd = (
                lookup[("numeric_all_finite", name, key)] for key in ("mean", "std_population")
            )
        targets.append(
            (name, "mean", "all_finite", mean, 1.0 if name == "popularity" else 0.1 * sd, sd)
        )
    for field in ("_s_genre", "_s_period", "_s_band"):
        categories = [
            (r["category"], float(r["value"]))
            for r in rows
            if r["section"] == "distribution"
            and r["variable"] == field
            and r["metric"] == "fraction"
        ]
        if field == "_s_band":
            categories = [(c, p) for c, p in categories if not str(c).startswith(("80", "90"))]
            pop = [
                (float(r["category"]), float(r["value"]))
                for r in rows
                if r["section"] == "distribution"
                and r["variable"] == "_s_pop"
                and r["metric"] == "fraction"
            ]
            categories += [
                ("80–89", sum(p for x, p in pop if 80 <= x < 90)),
                ("90–100", sum(p for x, p in pop if x >= 90)),
            ]
        for category, proportion in categories:
            targets.append(
                (field, "proportion", category, proportion, min(0.01, 0.2 * proportion), None)
            )
    return targets


def diagnose(frame, aggregates):
    targets = catalog_targets(aggregates)
    design = design_arrays(frame)
    accepted = (frame["lyrics_status"] == "accepted").to_numpy()
    bands = frame.with_columns(
        pl.when(pl.col("popularity").cast(pl.Float64) >= 90)
        .then(pl.lit("90–100"))
        .when(pl.col("popularity").cast(pl.Float64) >= 80)
        .then(pl.lit("80–89"))
        .otherwise(pl.col("sampling_popularity_band"))
        .alias("band")
    )["band"]
    categorical = {
        "_s_genre": frame["genre"],
        "_s_period": frame["sampling_period"],
        "_s_band": bands,
    }
    rows = []
    for variable, kind, category, reference, margin, sd in targets:
        y = (
            frame[variable].cast(pl.Float64, strict=False).to_numpy()
            if kind == "mean"
            else (categorical[variable].fill_null("__MISSING__") == category)
            .to_numpy()
            .astype(float)
        )
        for group, domain in (
            ("sample", np.ones(frame.height, dtype=bool)),
            ("accepted", accepted),
            ("not_accepted", ~accepted),
        ):
            for weighted in (False, True):
                stats = domain_ratio(y, domain, frame, weighted, design)
                tests = equivalence(stats, reference, margin, len(targets))
                positives = int(np.sum(y[domain])) if kind == "proportion" else None
                if (
                    positives is not None
                    and positives < 5
                    and not (frame["N_h"] == frame["n_h"]).all()
                ):
                    tests.update(conclusion="inconclusive", family_relevant=False)
                rows.append(
                    {
                        "group": group,
                        "weighted": weighted,
                        "variable": variable,
                        "kind": kind,
                        "category": category,
                        **stats,
                        **tests,
                        "standardized_difference": tests["difference"] / sd
                        if sd and tests["difference"] is not None
                        else None,
                        "relative_difference": tests["difference"] / reference
                        if reference and tests["difference"] is not None
                        else None,
                        "positive_n": positives,
                    }
                )
    return rows


def run(input_path, output, sample_dir=base.SAMPLE_DIR, expected=200000):
    sample, summary = base.validate_sample(
        sample_dir / "amostra_spotify_200k.parquet",
        sample_dir / "resumo_amostra_200k.json",
        sample_dir / "alocacao_amostra_200k.csv",
        expected=expected,
    )
    frame = pl.read_parquet(input_path)
    require(
        frame.height == expected
        and frame["track_id"].n_unique() == expected
        and frame.select(sample.columns).sort("track_id").equals(sample.sort("track_id")),
        "Resultado não preserva desenho original.",
    )
    path = sample_dir / "comparacao_catalogo_amostra_200k.csv"
    require(
        base.sha256(path) == summary["output_hashes"][path.name],
        "Agregados do catálogo divergiram.",
    )
    aggregate = pl.read_csv(path, infer_schema_length=0)
    seal = {
        "input_sha256": base.sha256(input_path),
        "aggregate_sha256": base.sha256(path),
        "protocol_sha256": base.sha256(PROTOCOL),
        "code_sha256": base.sha256(Path(__file__)),
        "sample_sha256": base.sha256(sample_dir / "amostra_spotify_200k.parquet"),
    }
    if output.exists():
        require(
            (output / "resumo.json").exists()
            and json.loads((output / "resumo.json").read_text())["seal"] == seal,
            "Parecer anterior incompatível; use pasta nova.",
        )
    output.mkdir(parents=True, exist_ok=True)
    rows = diagnose(frame, aggregate)
    reuse.write_csv(output / "diagnostico_equivalencia.csv", rows)
    coverage = (
        frame.with_columns((pl.col("lyrics_status") == "accepted").alias("accepted"))
        .group_by(
            "stratum_id",
            "N_h",
            "n_h",
            "genre",
            "sampling_period",
            "sampling_popularity_band",
        )
        .agg(
            pl.len().alias("observed_n"),
            pl.col("accepted").sum().alias("accepted_n"),
            pl.col("sampling_weight").sum().alias("total_weight"),
            pl.col("sampling_weight").filter(pl.col("accepted")).sum().alias("accepted_weight"),
        )
        .with_columns(
            (pl.col("accepted_n") / pl.col("observed_n")).alias("coverage"),
            (pl.col("accepted_n") == 0).alias("zero_coverage"),
            (pl.col("accepted_n") < 5).alias("few_accepted"),
            (pl.col("observed_n") < 20).alias("small_group"),
        )
    )
    reuse.write_csv(output / "cobertura_por_estrato.csv", coverage.sort("stratum_id").to_dicts())
    detailed = base.coverage_tables(frame)
    reuse.write_csv(output / "distribuicoes_quantis_qualidade.csv", detailed)
    aggregate.write_csv(output / "catalogo_amostra_referencia.csv")
    primary = [r for r in rows if r["group"] == "accepted" and r["weighted"]]
    complete = not frame["lyrics_status"].is_in(["pending", "technical_error"]).any()
    conclusion = (
        "compatível com os critérios observados, com limitações explicitadas"
        if all(r["conclusion"] == "equivalent" for r in primary)
        else "incompatível com os critérios observados"
        if any(r["family_relevant"] for r in primary)
        else "evidência insuficiente para concluir"
    )
    if not complete:
        conclusion = "evidência insuficiente para concluir"
    failures = [r for r in primary if r["conclusion"] != "equivalent"]
    status_reasons = reuse.counts(frame, ["lyrics_status", "lyrics_reason"])
    reuse.write_csv(output / "status_motivos.csv", status_reasons)
    accepted = frame.filter(pl.col("lyrics_status") == "accepted")
    result = {
        "seal": seal,
        "scope": str(input_path),
        "complete_input": complete,
        "conclusion": conclusion,
        "sample_n": frame.height,
        "accepted_n": accepted.height,
        "population_N": summary["catalog_counts"]["rows"],
        "weighted_acceptance_rate": float(
            accepted["sampling_weight"].sum() / frame["sampling_weight"].sum()
        ),
        "primary_comparisons": len(primary),
        "non_equivalent_or_inconclusive": len(failures),
        "zero_coverage_strata": coverage.filter(pl.col("zero_coverage")).height,
        "few_accepted_strata": coverage.filter(pl.col("few_accepted")).height,
        "design_checks_passed": True,
        "ssd_queries": 0,
    }
    atomic_json(output / "resumo.json", result)
    selection_answer = (
        "Há diferenças materiais apoiadas pelos intervalos simultâneos."
        if any(r["family_relevant"] for r in primary)
        else "As diferenças primárias são equivalentes dentro das margens."
        if all(r["conclusion"] == "equivalent" for r in primary)
        else "A evidência ainda não resolve se todas as alterações são toleráveis."
    )
    if not complete:
        selection_answer = (
            "A entrada ainda contém pendências/erros; não há conclusão sobre o domínio final."
        )
    opinion = f"""# Parecer estatístico — base completa disponível

**Conclusão: {conclusion}.** Escopo: {input_path.name}, hash registrado no resumo;
{frame.height:,} faixas, {accepted.height:,} aceitas. Catálogo de referência: {result["population_N"]:,}.
A avaliação pequena de busca não aprova esta base; este parecer usa seus resultados completos.

**A. Sorteio:** hashes, IDs, alocação, estratos, probabilidades e pesos conferem com
o desenho congelado. Isso verifica os artefatos registrados, sem repetir o sorteio.

**B. Seleção por letras:** {selection_answer} A tabela compara médias e proporções com o catálogo fixo,
com e sem pesos. {len(failures)} de {len(primary)} critérios primários ponderados
não demonstraram equivalência; {result["zero_coverage_strata"]} estratos têm cobertura
nula e {result["few_accepted_strata"]} têm menos de cinco aceitações. Falta de
equivalência não prova diferença; a conclusão de incompatibilidade exige intervalo
simultâneo fora da margem. Veja cada motivo/status e as distribuições nos CSVs.

**C. Tolerâncias:** ±1 ponto de popularidade; ±0,10 DP do catálogo para médias
contínuas/ano; min(1 pp,20% da proporção do catálogo) para categorias. Todas devem
ser atendidas conjuntamente. Limites fixados após conhecimento de resultados
anteriores: não é confirmação independente. Falhas/inconclusivos estão integralmente
em diagnostico_equivalencia.csv; primeiras comparações abaixo.

**D. Alcance:** os pesos estimam razões no domínio de aceitação sob este protocolo;
não corrigem disponibilidade seletiva de letras. Resultados permitem descrever o
subconjunto observado. Concordância nestas marginais não prova representatividade
global, equivalência multivariada, identificação correta da letra ou causalidade.

**E. Modelagem:** não se afirma suficiência preditiva pelo tamanho. Antes de avançar,
revisar correspondências propostas e regressões de matching, declarar o alcance
restrito ao domínio observado e planejar splits por artista/composição reconciliados
com o teste V0.6 exposto. Se a intenção for generalizar ao catálogo, as lacunas
listadas exigem avaliação específica de seleção e suporte; não se recomenda outra
busca integral automaticamente. Não recalibrar pesos para aprovar o diagnóstico.

TOST de Wald/Taylor a 5% (IC90%) por comparação; IC95% também informado.
Conclusão conjunta de equivalência por interseção de todos os testes primários,
sem escolher maioria. Para afirmar alguma diferença relevante na família, ICs
Bonferroni 95% simultâneos. Aproximação pode ser fraca em categorias raras: células
com <5 positivos, domínio válido <20 ou variância não estimável ficam inconclusivas.
Qualidade do matching e semelhança estatística são avaliações separadas.
"""
    opinion += "\n" + base.markdown_table(
        failures[:15], ["variable", "category", "difference", "margin", "conclusion"]
    )
    (output / "parecer_estatistico.md").write_text(opinion, encoding="utf-8")
    (output / PROTOCOL.name).write_text(PROTOCOL.read_text(encoding="utf-8"), encoding="utf-8")


def cli():
    p = argparse.ArgumentParser(description="Parecer estatístico sem acessar SSD/LRCLIB.")
    p.add_argument("--input", type=Path, default=reuse.WORKSPACE / "resultados_faixas_200k.parquet")
    p.add_argument("--output", type=Path, default=base.ROOT / "reports/parecer_letras_v2")
    a = p.parse_args()
    run(a.input, a.output)
