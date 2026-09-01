"""Revisão incremental e não destrutiva dos artefatos da Base v0.1.1."""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from typing import Any

import polars as pl

from .config import project_path
from .io import git_commit, read_json, sha256_file, utc_now, write_json

VERSION = "v0.1.1-revision"
TOTAL_MATCHES = 111_758
IMPLAUSIBLE_YEAR_MIN = 1850
IMPLAUSIBLE_YEAR_MAX = 2030
HUMAN_FIELDS = [
    "human_match_label",
    "human_version_label",
    "human_notes",
    "reviewed_by",
    "reviewed_at",
]

IMMUTABLE_ARTIFACTS = [
    "data/processed/modeling_base_lfm_v0_1.parquet",
    "data/processed/modeling_base_lfm_v0_1_1.parquet",
    "data/processed/split_assignments_v0_1_1.parquet",
    "data/processed/matching_audit_v0_1_1.parquet",
    "reports/feature_manifest_v0_1_1.csv",
    "reports/match_review_sample_v0_1_1.xlsx",
]

REVISION_OUTPUTS = [
    "reports/matching_temporal_audit_v0_1_1_revision.md",
    "reports/feature_manifest_v0_1_1_revision.csv",
    "reports/match_review_sample_v0_1_1_revision.xlsx",
    "reports/modeling_protocol_v0_1_1_revision.md",
    "reports/handoff_base_v0_1_1_revision.md",
    "reports/run_summary_v0_1_1_revision.json",
]

COMPRESSION_SOURCE = (
    "https://github.com/MaximilianMayerl/CorrelatesOfSongLyrics/blob/"
    "cefbfbf1e70823b50f644924bf6ac48151d8cf93/feature_extraction/"
    "features_compression.py"
)
EXTRACTOR_SOURCE = (
    "https://github.com/MaximilianMayerl/CorrelatesOfSongLyrics/blob/"
    "cefbfbf1e70823b50f644924bf6ac48151d8cf93/feature_extraction/__init__.py"
)
LFM_SOURCE = "https://zenodo.org/records/10938615"
SPOTIFY_SOURCE = "https://www.kaggle.com/datasets/amitanshjoshi/spotify-1million-tracks"


def _write_text(path: str | Path, text: str) -> None:
    destination = project_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=destination.parent, delete=False, suffix=".tmp"
    ) as handle:
        handle.write(text.rstrip() + "\n")
        temporary = Path(handle.name)
    os.replace(temporary, destination)


def _write_csv(frame: pl.DataFrame, path: str | Path) -> None:
    destination = project_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f"{destination.stem}.tmp.csv")
    frame.write_csv(temporary)
    os.replace(temporary, destination)


def _hashes(paths: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for relative in paths:
        path = project_path(relative)
        result[relative] = {
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256_file(path) if path.exists() else None,
        }
    return result


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    def clean(value: Any) -> str:
        return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(clean(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def _temporal_statistics(frame: pl.DataFrame, *, ignore_implausible: bool) -> dict[str, Any]:
    lfm_year = pl.col("lfm_release_year")
    missing_label = "ano ausente"
    if ignore_implausible:
        lfm_year = (
            pl.when(pl.col("lfm_qf_release_year_implausible").fill_null(False))
            .then(None)
            .otherwise(pl.col("lfm_release_year"))
        )
        missing_label = "ano ausente ou implausível"
    audited = frame.with_columns(lfm_year.alias("_lfm_year_for_statistics")).with_columns(
        pl.when(pl.col("year").is_null() | pl.col("_lfm_year_for_statistics").is_null())
        .then(None)
        .otherwise((pl.col("year") - pl.col("_lfm_year_for_statistics")).abs())
        .alias("_difference")
    )
    audited = audited.with_columns(
        pl.when(pl.col("_difference").is_null())
        .then(pl.lit(missing_label))
        .when(pl.col("_difference") == 0)
        .then(pl.lit("diferença 0"))
        .when(pl.col("_difference") <= 2)
        .then(pl.lit("1–2 anos"))
        .when(pl.col("_difference") <= 5)
        .then(pl.lit("3–5 anos"))
        .when(pl.col("_difference") <= 10)
        .then(pl.lit("6–10 anos"))
        .when(pl.col("_difference") <= 20)
        .then(pl.lit("11–20 anos"))
        .otherwise(pl.lit("mais de 20 anos"))
        .alias("_band")
    )
    differences = audited["_difference"].drop_nulls()
    bands = (
        audited.group_by("_band")
        .len()
        .with_columns((100 * pl.col("len") / frame.height).alias("percent"))
        .to_dicts()
    )
    order = {
        "diferença 0": 0,
        "1–2 anos": 1,
        "3–5 anos": 2,
        "6–10 anos": 3,
        "11–20 anos": 4,
        "mais de 20 anos": 5,
        "ano ausente": 6,
        "ano ausente ou implausível": 6,
    }
    bands.sort(key=lambda item: order[item["_band"]])
    return {
        "statistics": {
            "non_null": differences.len(),
            "missing": frame.height - differences.len(),
            "mean": float(differences.mean()),
            "median": float(differences.median()),
            "standard_deviation": float(differences.std(ddof=1)),
            "minimum": int(differences.min()),
            "maximum": int(differences.max()),
            "quantiles": {
                str(value): float(differences.quantile(value, interpolation="linear"))
                for value in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)
            },
        },
        "bands": [
            {"temporal_band": item["_band"], "count": item["len"], "percent": item["percent"]}
            for item in bands
        ],
    }


def build_special_cases(frame: pl.DataFrame, source: pl.DataFrame) -> pl.DataFrame:
    """Constrói a união deduplicada dos dois grupos sem alterar os matches."""
    enriched = frame.join(
        source.select(
            "spotify_row_id",
            "track_id",
            "lfm_record_key",
            "genre",
            "spotify_popularity",
            "temporal_cohort",
            "lfm_temporal_cohort",
        ),
        on=["spotify_row_id", "track_id", "lfm_record_key"],
        how="left",
        validate="1:1",
    )
    flag_year = pl.col("lfm_qf_release_year_implausible").fill_null(False)
    flag_key = pl.col("composition_key").is_null()
    special = (
        enriched.filter(flag_year | flag_key)
        .with_columns(
            flag_year.alias("flag_ano_lfm_implausivel"),
            flag_key.alias("flag_composition_key_ausente"),
            pl.when(flag_year & flag_key)
            .then(pl.lit("ano LFM implausível; composition_key ausente"))
            .when(flag_year)
            .then(pl.lit("ano LFM implausível"))
            .otherwise(pl.lit("composition_key ausente"))
            .alias("motivo_inclusao"),
            pl.when(flag_year)
            .then(None)
            .otherwise(pl.col("lfm_release_year"))
            .alias("lfm_release_year_para_estatistica"),
            pl.when(flag_year | pl.col("year").is_null() | pl.col("lfm_release_year").is_null())
            .then(None)
            .otherwise((pl.col("year") - pl.col("lfm_release_year")).abs())
            .alias("diferenca_temporal_valida_abs"),
            *[pl.lit("").alias(column) for column in HUMAN_FIELDS],
        )
        .sort(
            ["flag_ano_lfm_implausivel", "flag_composition_key_ausente", "spotify_row_id"],
            descending=[True, True, False],
        )
        .with_row_index("caso_especial_id", offset=1)
    )
    columns = [
        "caso_especial_id",
        "motivo_inclusao",
        "flag_ano_lfm_implausivel",
        "flag_composition_key_ausente",
        "spotify_row_id",
        "track_id",
        "lfm_record_key",
        "split",
        "artist_name_raw",
        "track_name_raw",
        "lfm_artist_name_raw",
        "lfm_track_name_raw",
        "year",
        "lfm_release_year",
        "lfm_release_year_para_estatistica",
        "temporal_year_difference_abs",
        "diferenca_temporal_valida_abs",
        "temporal_compatible",
        "temporal_cohort",
        "lfm_temporal_cohort",
        "genre",
        "spotify_popularity",
        "composition_key",
        "lfm_composition_key",
        "match_method",
        "match_score",
        "match_status",
        "acceptance_reason",
        "version_compatible",
        "matching_version",
        "remaster",
        "remix",
        "live",
        "acoustic",
        "radio_edit",
        "mono_stereo",
        "instrumental",
        "demo",
        "lfm_remaster",
        "lfm_remix",
        "lfm_live",
        "lfm_acoustic",
        "lfm_radio_edit",
        "lfm_mono_stereo",
        "lfm_instrumental",
        "lfm_demo",
        "genius_lyrics_views",
        "lfm_playcount",
        *HUMAN_FIELDS,
    ]
    return special.select(columns)


def revise_manifest() -> tuple[pl.DataFrame, dict[str, Any]]:
    manifest = pl.read_csv(project_path("reports/feature_manifest_v0_1_1.csv"))
    additions = {
        "decisão na revisão v0.1.1": "sem alteração",
        "autorizada como preditora na revisão": pl.when(
            pl.col("papel").is_in(["preditora", "controle"])
            & (pl.col("modelo em que poderá entrar") != "nenhum")
        )
        .then(pl.lit("sim"))
        .otherwise(pl.lit("não")),
        "definição ou fórmula na revisão": "não aplicável",
        "unidade ou escala na revisão": "não aplicável",
        "interpretação na revisão": "não aplicável",
        "influência provável do tamanho da letra": "não aplicável",
        "fonte documental exata": "não aplicável",
    }
    manifest = manifest.with_columns(
        *[
            value.alias(name) if isinstance(value, pl.Expr) else pl.lit(value).alias(name)
            for name, value in additions.items()
        ]
    )

    replacements: dict[str, dict[str, str]] = {
        "lfm_compression_ratio": {
            "descrição confirmada": (
                "Razão entre o tamanho em memória dos bytes UTF-8 da letra e o tamanho em memória "
                "dos mesmos bytes comprimidos com zlib."
            ),
            "semântica confirmada": "sim",
            "transformação sugerida": (
                "avaliar assimetria e dependência residual do comprimento; qualquer decisão será "
                "ajustada somente em development_train"
            ),
            "decisão na revisão v0.1.1": "mantida como preditora autorizada; sem transformação executada",
            "autorizada como preditora na revisão": "sim",
            "definição ou fórmula na revisão": (
                "sys.getsizeof(text.encode('utf-8')) / "
                "sys.getsizeof(zlib.compress(text.encode('utf-8')))"
            ),
            "unidade ou escala na revisão": "razão adimensional",
            "interpretação na revisão": (
                "valor maior indica saída comprimida menor em relação ao original e, por inferência "
                "direta da fórmula, maior compressibilidade/repetição"
            ),
            "influência provável do tamanho da letra": (
                "provável influência residual: sys.getsizeof inclui overhead fixo e a eficiência do "
                "zlib varia com o comprimento; avaliar no treino"
            ),
            "fonte documental exata": f"{LFM_SOURCE}; {COMPRESSION_SOURCE}",
        },
        "lfm_entropy": {
            "descrição confirmada": "semântica não confirmada",
            "semântica confirmada": "não",
            "papel": "auditoria",
            "modelo em que poderá entrar": "nenhum",
            "transformação sugerida": "nenhuma; não entra como preditora",
            "tratamento de ausência sugerido": "não aplicável para modelagem",
            "necessidade de padronização": "não",
            "risco de leakage": (
                "não avaliar como feature; fórmula, tokenização, base logarítmica e escala não confirmadas"
            ),
            "justificativa da decisão": (
                "Coluna preservada fisicamente na Base v0.1.1 apenas para auditoria e removida das "
                "listas autorizadas de preditoras; semântica não confirmada no código/documentação oficial."
            ),
            "decisão na revisão v0.1.1": (
                "mantida fisicamente para auditoria; retirada das listas autorizadas de preditoras"
            ),
            "autorizada como preditora na revisão": "não",
            "definição ou fórmula na revisão": "semântica não confirmada",
            "unidade ou escala na revisão": "semântica não confirmada",
            "interpretação na revisão": "semântica não confirmada",
            "influência provável do tamanho da letra": "semântica não confirmada",
            "fonte documental exata": (
                f"{LFM_SOURCE}; {EXTRACTOR_SOURCE}; busca no histórico do repositório oficial até "
                "cefbfbf1e70823b50f644924bf6ac48151d8cf93 sem fórmula ou procedimento"
            ),
        },
        "year": {
            "descrição confirmada": (
                "Ano associado à faixa no campo year da fonte Spotify_1Million_Tracks; neste recorte "
                "há valores de 2000 a 2023. A fonte não confirma se representa lançamento original, "
                "álbum ou versão específica."
            ),
            "semântica confirmada": "parcial",
            "transformação sugerida": (
                "variável temporal; avaliar forma linear e não linear somente em development_train"
            ),
            "decisão na revisão v0.1.1": (
                "tratar como temporal; nenhuma transformação executada nesta revisão"
            ),
            "fonte documental exata": SPOTIFY_SOURCE,
        },
        "genre": {
            "descrição confirmada": (
                "Rótulo categórico da coluna genre da fonte Spotify_1Million_Tracks; o mecanismo exato "
                "de atribuição ou curadoria do rótulo não é documentado pela fonte."
            ),
            "semântica confirmada": "parcial",
            "transformação sugerida": (
                "variável categórica; codificação escolhida e ajustada somente em development_train"
            ),
            "decisão na revisão v0.1.1": (
                "tratar como categórica; nenhuma transformação executada nesta revisão"
            ),
            "fonte documental exata": SPOTIFY_SOURCE,
        },
        "key": {
            "transformação sugerida": (
                "variável categórica nominal ou representação circular; escolher somente em "
                "development_train; não tratar como contínua ordinal"
            ),
            "decisão na revisão v0.1.1": (
                "tratamento categórico nominal ou circular adiado ao treino; não ordinal"
            ),
        },
        "time_signature": {
            "transformação sugerida": (
                "variável categórica; codificação escolhida e ajustada somente em development_train"
            ),
            "decisão na revisão v0.1.1": (
                "tratar como categórica; nenhuma transformação executada nesta revisão"
            ),
        },
        "mode": {
            "transformação sugerida": "variável binária; preservar codificação 0/1",
            "decisão na revisão v0.1.1": (
                "tratar como binária; nenhuma transformação executada nesta revisão"
            ),
        },
    }
    for name, values in replacements.items():
        manifest = manifest.with_columns(
            *[
                pl.when(pl.col("nome") == name)
                .then(pl.lit(value))
                .otherwise(pl.col(column))
                .alias(column)
                for column, value in values.items()
            ]
        )

    old_spec = read_json("reports/tables/model_spec_v0_1_1.json", {})
    revised_spec = dict(old_spec)
    for key in (
        "traditional_descriptor_features",
        "traditional_features",
        "combined_features_current",
    ):
        revised_spec[key] = [name for name in old_spec[key] if name != "lfm_entropy"]
    revised_spec["revision_decisions"] = {
        "lfm_entropy": "audit_only_semantics_unconfirmed",
        "lfm_compression_ratio": "authorized_semantics_confirmed",
        "transformations_executed": False,
    }
    counts = {
        "baseline_before": len(old_spec["baseline_features"]),
        "baseline_after": len(revised_spec["baseline_features"]),
        "traditional_descriptors_before": len(old_spec["traditional_descriptor_features"]),
        "traditional_descriptors_after": len(revised_spec["traditional_descriptor_features"]),
        "traditional_before": len(old_spec["traditional_features"]),
        "traditional_after": len(revised_spec["traditional_features"]),
        "deep_current_before": len(old_spec["deep_features_current"]),
        "deep_current_after": len(revised_spec["deep_features_current"]),
        "combined_current_before": len(old_spec["combined_features_current"]),
        "combined_current_after": len(revised_spec["combined_features_current"]),
    }
    return manifest, {"counts": counts, "authorized_feature_lists": revised_spec}


def _matching_report(
    special: pl.DataFrame,
    raw: dict[str, Any],
    valid: dict[str, Any],
) -> str:
    implausible = special.filter(pl.col("flag_ano_lfm_implausivel"))
    raw_stats = raw["statistics"]
    valid_stats = valid["statistics"]
    case_rows = [
        [
            row["caso_especial_id"],
            row["spotify_row_id"],
            row["track_id"],
            row["artist_name_raw"],
            row["track_name_raw"],
            row["year"],
            row["lfm_record_key"],
            row["lfm_artist_name_raw"],
            row["lfm_track_name_raw"],
            row["lfm_release_year"],
            row["match_method"],
            row["match_status"],
            row["split"],
        ]
        for row in implausible.to_dicts()
    ]

    def stats_rows(stats: dict[str, Any]) -> list[list[Any]]:
        return [
            ["diferenças válidas", stats["non_null"]],
            ["ausentes para estatística", stats["missing"]],
            ["média", f"{stats['mean']:.6f}"],
            ["mediana", f"{stats['median']:.6f}"],
            ["desvio-padrão amostral", f"{stats['standard_deviation']:.6f}"],
            ["mínimo", stats["minimum"]],
            ["máximo", stats["maximum"]],
            *[[f"quantil {key}", f"{value:.6f}"] for key, value in stats["quantiles"].items()],
        ]

    raw_bands = [
        [row["temporal_band"], row["count"], f"{row['percent']:.6f}%"] for row in raw["bands"]
    ]
    valid_bands = [
        [row["temporal_band"], row["count"], f"{row['percent']:.6f}%"] for row in valid["bands"]
    ]
    return f"""# Auditoria temporal revisada — Base v0.1.1

## Escopo e decisão

Esta revisão é incremental e não destrutiva. Os {TOTAL_MATCHES:,} pares aceitos foram preservados; nenhum ano Spotify foi alterado e nenhum match foi automaticamente classificado como incorreto. Anos LFM implausíveis continuam registrados no dado e são tratados como ausentes **somente nas estatísticas temporais válidas**.

Critério operacional já implementado em `src/tcc_music_popularity/lfm2b.py`: `lfm_release_year < {IMPLAUSIBLE_YEAR_MIN}` ou `lfm_release_year > {IMPLAUSIBLE_YEAR_MAX}`. O critério detectou **{implausible.height}** casos no conjunto matched.

## Estatísticas brutas

{_markdown_table(["métrica", "valor"], stats_rows(raw_stats))}

### Faixas brutas

{_markdown_table(["faixa", "n", "% de 111.758"], raw_bands)}

## Estatísticas válidas após desconsiderar anos implausíveis

{_markdown_table(["métrica", "valor"], stats_rows(valid_stats))}

### Faixas válidas

{_markdown_table(["faixa", "n", "% de 111.758"], valid_bands)}

## Lista integral dos 16 anos LFM implausíveis

{_markdown_table(["caso", "spotify_row_id", "track_id", "artista Spotify", "faixa Spotify", "ano Spotify", "lfm_record_key", "artista LFM2b", "faixa LFM2b", "ano LFM", "método", "status", "split"], case_rows)}

## Interpretação

- Os valores implausíveis são problemas do campo temporal LFM2b, não evidência suficiente de match incorreto.
- `temporal_compatible` e os demais campos históricos foram preservados; a revisão introduz apenas a visão estatística válida.
- A planilha revisada contém estes 16 casos e os 22 casos sem `composition_key`, sem duplicação.
""".replace(f"{TOTAL_MATCHES:,}", f"{TOTAL_MATCHES:,}".replace(",", "."))


def _protocol_report(model_info: dict[str, Any]) -> str:
    counts = model_info["counts"]
    return f"""# Protocolo revisado dos quatro modelos — Base v0.1.1

## Escopo

Esta revisão apenas documenta decisões futuras de transformação. Nenhuma transformação foi executada, nenhum modelo foi treinado e o split 75%/25% permaneceu idêntico.

## Tratamento futuro das variáveis acústicas e metadados

- `key`: variável categórica nominal ou representação circular; a escolha será feita somente em `development_train`. É proibido tratá-la como contínua ordinal.
- `time_signature`: variável categórica; a codificação será ajustada somente em `development_train`.
- `mode`: variável binária, preservando a codificação 0/1.
- `genre`: variável categórica; a codificação será escolhida e ajustada somente em `development_train`.
- `year`: variável temporal; formas linear e não linear serão comparadas somente no treino.

## Semântica dos descritores revisados

- `lfm_compression_ratio`: semântica confirmada no extrator oficial; continua autorizada.
- `lfm_entropy`: semântica não confirmada; permanece fisicamente na Base v0.1.1 apenas para auditoria e foi removida das listas autorizadas de preditoras.

## Contagens autorizadas

- Baseline: **{counts["baseline_after"]}** (sem alteração).
- Descritores tradicionais: **{counts["traditional_descriptors_before"]} → {counts["traditional_descriptors_after"]}**.
- Modelo tradicional atual: **{counts["traditional_before"]} → {counts["traditional_after"]}**.
- Modelo profundo atual: **{counts["deep_current_after"]}** (baseline; embeddings ainda não coletados).
- Modelo combinado atual: **{counts["combined_current_before"]} → {counts["combined_current_after"]}** antes de embeddings futuros.

## Comparabilidade e leakage

Todos os modelos futuros deverão usar os mesmos `track_id`, `artist_group_id`, `composition_group_id`, `split_group_id` e partições existentes. Seleção, imputação, codificação, padronização, forma funcional e tuning ocorrerão exclusivamente em `development_train`.
"""


def _handoff_report(summary: dict[str, Any]) -> str:
    temporal = summary["temporal"]
    special = summary["special_cases"]
    counts = summary["model_spec_revision"]["counts"]
    valid = temporal["valid_after_ignoring_implausible"]["statistics"]
    return f"""# Handoff da revisão incremental — Base v0.1.1

## Resultado

A revisão foi concluída sem alterar bases, pares aceitos, IDs ou split. Foram identificados **{special["total_unique"]} casos especiais**: {special["implausible_years"]} anos LFM implausíveis e {special["missing_composition_key"]} chaves de composição ausentes, com interseção **{special["intersection"]}**.

## Auditoria temporal válida

Ao tratar os {special["implausible_years"]} anos implausíveis como ausentes apenas para estatística, restaram **{valid["non_null"]}** diferenças válidas e **{valid["missing"]}** ausentes. A média passou a **{valid["mean"]:.6f}**, a mediana permaneceu **{valid["median"]:.6f}**, o desvio-padrão amostral passou a **{valid["standard_deviation"]:.6f}** e o máximo válido passou a **{valid["maximum"]}** anos. Estatísticas brutas e válidas completas estão em `matching_temporal_audit_v0_1_1_revision.md`.

## Semântica

- `lfm_compression_ratio`: confirmada. O extrator oficial calcula `sys.getsizeof(UTF-8) / sys.getsizeof(zlib.compress(UTF-8))`; razão adimensional. A possível dependência residual do comprimento deverá ser avaliada somente no treino.
- `lfm_entropy`: não confirmada. A coluna foi preservada fisicamente apenas para auditoria e removida das listas autorizadas de preditoras.
- `year` e `genre`: descrições revisadas de modo conservador conforme o schema/data card da fonte Spotify; detalhes não documentados pela fonte não foram inferidos.

## Mudança na autorização de preditoras

Os descritores tradicionais autorizados passaram de **{counts["traditional_descriptors_before"]} para {counts["traditional_descriptors_after"]}** e o conjunto tradicional/combinado atual passou de **{counts["traditional_before"]} para {counts["traditional_after"]}**. O baseline permaneceu em **{counts["baseline_after"]}**.

## Planilha de revisão

A nova aba `casos_especiais` contém a união deduplicada dos dois grupos e cinco campos humanos vazios. A aba `revisao_matches` preserva os 225 registros existentes. Nenhuma linha recebeu rótulo automático.

## Integridade

- Base v0.1 original: hash preservado.
- Base v0.1.1 e matching audit: hashes preservados.
- Split: hash preservado, mesmos IDs e mesma alocação 75%/25%.
- Pares aceitos: {TOTAL_MATCHES:,}, sem alteração.
- Letras coletadas: não.
- Modelos treinados: não.

Os comandos e códigos de saída finais são registrados em `run_summary_v0_1_1_revision.json` após a verificação.
""".replace(f"{TOTAL_MATCHES:,}", f"{TOTAL_MATCHES:,}".replace(",", "."))


def prepare_revision_v011() -> dict[str, Any]:
    """Gera artefatos de revisão, preservando todos os artefatos v0.1.1 existentes."""
    started = time.perf_counter()
    immutable_before = _hashes(IMMUTABLE_ARTIFACTS)
    audit = pl.read_parquet(project_path("data/processed/matching_audit_v0_1_1.parquet"))
    source = pl.read_parquet(project_path("data/processed/modeling_base_lfm_v0_1.parquet"))
    if audit.height != TOTAL_MATCHES or source.height != TOTAL_MATCHES:
        raise ValueError("A revisão exige exatamente 111.758 pares preservados.")

    special = build_special_cases(audit, source)
    implausible_count = special.filter(pl.col("flag_ano_lfm_implausivel")).height
    missing_key_count = special.filter(pl.col("flag_composition_key_ausente")).height
    intersection = special.filter(
        pl.col("flag_ano_lfm_implausivel") & pl.col("flag_composition_key_ausente")
    ).height
    if (implausible_count, missing_key_count) != (16, 22):
        raise ValueError(
            f"Contagens inesperadas: anos implausíveis={implausible_count}, "
            f"chaves ausentes={missing_key_count}."
        )
    if special.height != implausible_count + missing_key_count - intersection:
        raise AssertionError("A união dos casos especiais contém duplicações.")
    for column in HUMAN_FIELDS:
        if special[column].ne("").any():
            raise AssertionError(f"O campo humano {column} deve permanecer vazio.")

    raw_temporal = _temporal_statistics(audit, ignore_implausible=False)
    valid_temporal = _temporal_statistics(audit, ignore_implausible=True)
    manifest, model_info = revise_manifest()
    _write_csv(manifest, "reports/feature_manifest_v0_1_1_revision.csv")
    _write_text(
        "reports/matching_temporal_audit_v0_1_1_revision.md",
        _matching_report(special, raw_temporal, valid_temporal),
    )
    _write_text("reports/modeling_protocol_v0_1_1_revision.md", _protocol_report(model_info))

    immutable_after = _hashes(IMMUTABLE_ARTIFACTS)
    split_before = immutable_before["data/processed/split_assignments_v0_1_1.parquet"]["sha256"]
    split_after = immutable_after["data/processed/split_assignments_v0_1_1.parquet"]["sha256"]
    immutable_unchanged = immutable_before == immutable_after
    split_unchanged = split_before == split_after
    if not immutable_unchanged or not split_unchanged:
        raise AssertionError("Um artefato v0.1.1 protegido foi alterado durante a revisão.")

    summary: dict[str, Any] = {
        "generated_at": utc_now(),
        "version": VERSION,
        "code_version": "0.1.1",
        "git_commit": git_commit(),
        "status": "revision_artifacts_generated",
        "duration_seconds": round(time.perf_counter() - started, 6),
        "scope": {
            "split_changed": False,
            "training_ids_changed": False,
            "holdout_ids_changed": False,
            "base_v0_1_changed": False,
            "accepted_pairs_changed": False,
            "lyrics_collected": False,
            "models_trained": False,
            "transformations_executed": False,
        },
        "immutable_artifacts": {
            "before": immutable_before,
            "after": immutable_after,
            "all_hashes_unchanged": immutable_unchanged,
        },
        "split_verification": {
            "rows": TOTAL_MATCHES,
            "sha256_before": split_before,
            "sha256_after": split_after,
            "identical": split_unchanged,
        },
        "special_cases": {
            "implausible_years": implausible_count,
            "missing_composition_key": missing_key_count,
            "intersection": intersection,
            "total_unique": special.height,
            "criteria": {
                "expression": (
                    f"lfm_release_year < {IMPLAUSIBLE_YEAR_MIN} or "
                    f"lfm_release_year > {IMPLAUSIBLE_YEAR_MAX}"
                ),
                "records_deleted": 0,
                "spotify_year_changed": False,
                "matches_reclassified": False,
            },
            "columns": special.columns,
            "rows": special.to_dicts(),
            "human_fields_blank": True,
        },
        "temporal": {
            "raw": raw_temporal,
            "valid_after_ignoring_implausible": valid_temporal,
        },
        "semantics": {
            "lfm_compression_ratio": {
                "confirmed": True,
                "definition": (
                    "Razão entre o tamanho em memória dos bytes UTF-8 originais e o tamanho em "
                    "memória desses bytes comprimidos com zlib."
                ),
                "formula": (
                    "sys.getsizeof(text.encode('utf-8')) / "
                    "sys.getsizeof(zlib.compress(text.encode('utf-8')))"
                ),
                "unit_or_scale": "razão adimensional",
                "interpretation": (
                    "valor maior implica saída comprimida menor relativamente ao original; maior "
                    "compressibilidade é inferência direta da fórmula"
                ),
                "probable_length_influence": (
                    "provável influência residual devido ao overhead de sys.getsizeof e à eficiência "
                    "do zlib dependente do comprimento; avaliar em development_train"
                ),
                "exact_sources": [LFM_SOURCE, COMPRESSION_SOURCE],
            },
            "lfm_entropy": {
                "confirmed": False,
                "definition": "semântica não confirmada",
                "formula": "semântica não confirmada",
                "unit_or_scale": "semântica não confirmada",
                "interpretation": "semântica não confirmada",
                "probable_length_influence": "semântica não confirmada",
                "decision": "audit_only_removed_from_authorized_predictors",
                "exact_sources_searched": [LFM_SOURCE, EXTRACTOR_SOURCE],
                "repository_commit_searched": "cefbfbf1e70823b50f644924bf6ac48151d8cf93",
            },
            "spotify_year_genre": {
                "source": SPOTIFY_SOURCE,
                "year_semantics": "partial_source_schema_only",
                "genre_semantics": "partial_source_schema_only",
            },
        },
        "model_spec_revision": model_info,
        "workbook": {
            "source_rows_preserved": 225,
            "special_rows": special.height,
            "expected_sheets": ["instrucoes", "revisao_matches", "casos_especiais"],
            "path": "reports/match_review_sample_v0_1_1_revision.xlsx",
        },
        "outputs": _hashes(REVISION_OUTPUTS[:-1]),
        "verification": {"commands": [], "status": "pending_final_verification"},
        "warnings": [
            "lfm_entropy permanece fisicamente na Base v0.1.1, mas não está autorizada como preditora.",
            "As estatísticas válidas ignoram anos LFM implausíveis sem alterar os campos originais.",
            "A aprovação técnica não substitui a revisão humana dos matches.",
        ],
    }
    _write_text("reports/handoff_base_v0_1_1_revision.md", _handoff_report(summary))
    summary["outputs"] = _hashes(REVISION_OUTPUTS[:-1])
    write_json("reports/run_summary_v0_1_1_revision.json", summary)
    return summary


def finalize_revision_verification(commands: list[dict[str, Any]]) -> dict[str, Any]:
    """Registra verificação final após a geração e inspeção da planilha."""
    summary = read_json("reports/run_summary_v0_1_1_revision.json", {})
    if not summary:
        raise FileNotFoundError("Execute prepare_revision_v011 antes da finalização.")
    immutable_now = _hashes(IMMUTABLE_ARTIFACTS)
    unchanged = immutable_now == summary["immutable_artifacts"]["before"]
    workbook = project_path("reports/match_review_sample_v0_1_1_revision.xlsx")
    summary["immutable_artifacts"]["after_final_verification"] = immutable_now
    summary["immutable_artifacts"]["all_hashes_unchanged"] = unchanged
    summary["split_verification"]["sha256_after"] = immutable_now[
        "data/processed/split_assignments_v0_1_1.parquet"
    ]["sha256"]
    summary["split_verification"]["identical"] = (
        summary["split_verification"]["sha256_before"]
        == summary["split_verification"]["sha256_after"]
    )
    summary["workbook"]["exists"] = workbook.exists()
    summary["workbook"]["size_bytes"] = workbook.stat().st_size if workbook.exists() else None
    summary["workbook"]["sha256"] = sha256_file(workbook) if workbook.exists() else None
    summary["outputs"] = _hashes(REVISION_OUTPUTS[:-1])
    commands_as_expected = all(
        item["exit_code"] == item.get("expected_exit_code", 0) for item in commands
    )
    summary["verification"] = {
        "commands": commands,
        "status": "approved"
        if unchanged and workbook.exists() and commands_as_expected
        else "failed",
    }
    summary["status"] = "complete" if summary["verification"]["status"] == "approved" else "failed"
    summary["generated_at"] = utc_now()
    write_json("reports/run_summary_v0_1_1_revision.json", summary)
    return summary
