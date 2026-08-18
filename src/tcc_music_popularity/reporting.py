"""Relatórios Markdown e figuras descritivas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .config import project_path
from .io import read_json, utc_now


def _read(path: str) -> dict[str, Any] | None:
    return read_json(path, None)


def _markdown_table(
    rows: list[dict[str, Any]], columns: list[str], limit: int | None = None
) -> str:
    selected = rows[:limit] if limit else rows
    if not selected:
        return "_Sem resultados observados._"
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(str(row.get(column, "")).replace("|", "\\|") for column in columns) + " |"
        for row in selected
    ]
    return "\n".join([header, separator, *body])


def _save_bar(
    labels: list[str], values: list[float], title: str, ylabel: str, path: Path, source: str
) -> None:
    fig, axis = plt.subplots(figsize=(10, 6.8))
    safe_values = [float("nan") if value is None else value for value in values]
    axis.bar(labels, safe_values, color="#31688e")
    axis.set_title(title)
    axis.set_ylabel(ylabel)
    axis.tick_params(axis="x", rotation=45)
    fig.text(0.08, 0.02, f"Fonte: {source}", fontsize=8)
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.savefig(path, dpi=160)
    plt.close(fig)


def generate_figures() -> list[str]:
    figures_dir = project_path("reports/figures")
    figures_dir.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []
    spotify = project_path("data/processed/spotify_tracks.parquet")
    if spotify.exists():
        connection = duckdb.connect()
        relation = f"read_parquet('{spotify.as_posix()}')"
        try:
            years = connection.execute(
                f"SELECT year, count(*) FROM {relation} GROUP BY 1 ORDER BY 1"
            ).fetchall()
            path = figures_dir / "spotify_tracks_by_year.png"
            _save_bar(
                [str(row[0]) for row in years],
                [row[1] for row in years],
                "Músicas Spotify por ano",
                "Número de registros",
                path,
                "Spotify_1Million_Tracks; arquivo observado",
            )
            generated.append(str(path))

            cohorts = connection.execute(
                f"SELECT temporal_cohort, count(*) FROM {relation} GROUP BY 1 ORDER BY 1"
            ).fetchall()
            path = figures_dir / "spotify_tracks_by_cohort.png"
            _save_bar(
                [str(row[0]) for row in cohorts],
                [row[1] for row in cohorts],
                "Músicas Spotify por coorte temporal",
                "Número de registros",
                path,
                "Spotify_1Million_Tracks; arquivo observado",
            )
            generated.append(str(path))

            zero_rates = connection.execute(
                f"SELECT temporal_cohort, 100.0 * avg((spotify_popularity = 0)::INT) "
                f"FROM {relation} GROUP BY 1 ORDER BY 1"
            ).fetchall()
            path = figures_dir / "spotify_zero_popularity_by_cohort.png"
            _save_bar(
                [str(row[0]) for row in zero_rates],
                [row[1] for row in zero_rates],
                "Popularidade Spotify igual a zero por coorte",
                "Percentual de registros (%)",
                path,
                "Spotify_1Million_Tracks; arquivo observado",
            )
            generated.append(str(path))

            popularity = connection.execute(
                f"SELECT floor(spotify_popularity / 5) * 5 bin, count(*) FROM {relation} GROUP BY 1 ORDER BY 1"
            ).fetchall()
            path = figures_dir / "spotify_popularity_distribution.png"
            _save_bar(
                [str(int(row[0])) if row[0] is not None else "ausente" for row in popularity],
                [row[1] for row in popularity],
                "Distribuição da popularidade Spotify observada",
                "Número de registros (bins de 5 pontos)",
                path,
                "Spotify_1Million_Tracks; arquivo observado",
            )
            generated.append(str(path))

            genres = connection.execute(
                f"SELECT genre, count(*) n FROM {relation} GROUP BY 1 ORDER BY n DESC LIMIT 20"
            ).fetchall()
            path = figures_dir / "spotify_top_genres.png"
            _save_bar(
                [str(row[0]) for row in genres],
                [row[1] for row in genres],
                "Vinte gêneros mais frequentes",
                "Número de registros",
                path,
                "Spotify_1Million_Tracks; arquivo observado",
            )
            generated.append(str(path))
        finally:
            connection.close()

        spotify_audit = read_json("reports/tables/spotify_audit.json", {})
        missing_rows = sorted(
            (
                (name, values["percent"])
                for name, values in spotify_audit.get("missing", {}).items()
                if values["count"] > 0
            ),
            key=lambda item: item[1],
            reverse=True,
        )[:20]
        if missing_rows:
            path = figures_dir / "spotify_missingness.png"
            _save_bar(
                [row[0] for row in missing_rows],
                [row[1] for row in missing_rows],
                "Missingness: vinte campos Spotify com maior percentual",
                "Valores ausentes (%)",
                path,
                "Camada normalizada Spotify v0.1",
            )
            generated.append(str(path))

    status = project_path("data/processed/spotify_tracks_with_match_status.parquet")
    if status.exists():
        connection = duckdb.connect()
        relation = f"read_parquet('{status.as_posix()}')"
        matched = "match_status IN ('accepted_high_confidence', 'accepted_with_rules')"
        try:
            funnel = connection.execute(
                f"SELECT match_status, count(*) n FROM {relation} GROUP BY 1 ORDER BY n DESC"
            ).fetchall()
            path = figures_dir / "matching_funnel.png"
            _save_bar(
                [str(row[0]) for row in funnel],
                [row[1] for row in funnel],
                "Funil de status do cruzamento",
                "Número de faixas Spotify",
                path,
                "Cruzamento Spotify × LFM2b v0.1",
            )
            generated.append(str(path))

            temporal = connection.execute(
                f"SELECT temporal_cohort, CASE WHEN {matched} THEN 'matched' ELSE 'não aceito' END grupo, "
                f"count(*) n FROM {relation} GROUP BY 1, 2 ORDER BY 1, 2"
            ).fetchall()
            cohorts = sorted({str(row[0]) for row in temporal})
            x = list(range(len(cohorts)))
            fig, axis = plt.subplots(figsize=(9, 5.5))
            for offset, group in ((-0.2, "matched"), (0.2, "não aceito")):
                values = {str(row[0]): row[2] for row in temporal if str(row[1]) == group}
                axis.bar(
                    [position + offset for position in x],
                    [values.get(cohort, 0) for cohort in cohorts],
                    width=0.4,
                    label=group,
                )
            axis.set_xticks(x, cohorts)
            axis.set_title("Distribuição temporal: matched × não aceito")
            axis.set_ylabel("Número de faixas Spotify")
            axis.legend()
            axis.text(
                0,
                -0.18,
                "Fonte: Spotify_1Million_Tracks e cruzamento LFM2b v0.1",
                transform=axis.transAxes,
                fontsize=8,
            )
            fig.tight_layout()
            path = figures_dir / "temporal_matched_unmatched.png"
            fig.savefig(path, dpi=160)
            plt.close(fig)
            generated.append(str(path))

            rates = connection.execute(
                f"SELECT year, 100.0 * count(*) FILTER (WHERE {matched}) / count(*) rate "
                f"FROM {relation} GROUP BY 1 ORDER BY 1"
            ).fetchall()
            path = figures_dir / "match_rate_by_year.png"
            _save_bar(
                [str(row[0]) for row in rates],
                [row[1] for row in rates],
                "Taxa de match aceito por ano",
                "Percentual de faixas (%)",
                path,
                "Cruzamento Spotify × LFM2b v0.1",
            )
            generated.append(str(path))

            genres = connection.execute(
                f"SELECT genre, 100.0 * count(*) FILTER (WHERE {matched}) / count(*) rate, count(*) n "
                f"FROM {relation} GROUP BY 1 ORDER BY n DESC LIMIT 20"
            ).fetchall()
            path = figures_dir / "match_rate_by_genre.png"
            _save_bar(
                [str(row[0]) for row in genres],
                [row[1] for row in genres],
                "Taxa de match nos vinte gêneros mais frequentes",
                "Percentual de faixas (%)",
                path,
                "Cruzamento Spotify × LFM2b v0.1",
            )
            generated.append(str(path))

            distributions = connection.execute(
                f"SELECT CASE WHEN {matched} THEN 'matched' ELSE 'unmatched' END grupo, "
                "floor(spotify_popularity / 5) * 5 bin, count(*) n FROM "
                f"{relation} GROUP BY 1, 2 ORDER BY 1, 2"
            ).fetchall()
            fig, axis = plt.subplots(figsize=(10, 5.5))
            for group in ("matched", "unmatched"):
                rows = [row for row in distributions if row[0] == group and row[1] is not None]
                total = sum(row[2] for row in rows) or 1
                axis.plot(
                    [row[1] for row in rows],
                    [100 * row[2] / total for row in rows],
                    marker="o",
                    label=group,
                )
            axis.set_title("Popularidade Spotify: matched × unmatched")
            axis.set_xlabel("Popularidade Spotify observada (bins de 5 pontos)")
            axis.set_ylabel("Percentual dentro do grupo (%)")
            axis.legend()
            axis.text(
                0,
                -0.18,
                "Fonte: Spotify_1Million_Tracks e cruzamento LFM2b v0.1",
                transform=axis.transAxes,
                fontsize=8,
            )
            fig.tight_layout()
            path = figures_dir / "popularity_matched_unmatched.png"
            fig.savefig(path, dpi=160)
            plt.close(fig)
            generated.append(str(path))
        finally:
            connection.close()
    return generated


def write_data_audit() -> Path:
    manifest = _read("data/raw/manifest.json") or {"sources": {}}
    spotify = _read("reports/tables/spotify_audit.json")
    lfm = _read("reports/tables/lfm2b_audit.json")
    lines = [
        "# Auditoria de dados — Base v0.1",
        "",
        f"Gerado em: `{utc_now()}`.",
        "",
        "> Resultados abaixo são observados nos arquivos efetivamente processados. Benchmarks fornecidos são mostrados apenas como referência comparativa.",
        "",
        "## Proveniência das entradas",
        "",
    ]
    source_rows = []
    for name, source in manifest.get("sources", {}).items():
        source_rows.append(
            {
                "fonte": name,
                "arquivo": source.get("local_path"),
                "bytes": source.get("size_bytes"),
                "sha256": source.get("sha256"),
                "licença": source.get("license_observed"),
                "status": source.get("verification_status"),
            }
        )
    lines.extend(
        [
            _markdown_table(
                source_rows, ["fonte", "arquivo", "bytes", "sha256", "licença", "status"]
            ),
            "",
        ]
    )
    lines.extend(["## Spotify", ""])
    if spotify:
        observed = spotify["observed"]
        lines.extend(
            [
                f"Foram observadas **{observed['rows']:,}** linhas e **{observed['columns']}** colunas; "
                f"{observed['track_ids_distinct']:,} IDs, {observed['artists_distinct']:,} artistas e "
                f"anos de {observed['year_min']} a {observed['year_max']}.",
                "",
                f"`spotify_popularity`: média {spotify['popularity']['mean']:.4f}, mediana "
                f"{spotify['popularity']['median']:.4f}, zeros {spotify['popularity']['zero_count']:,} "
                f"({spotify['popularity']['zero_percent']:.4f}%).",
                "",
                "### Coortes observadas",
                "",
                _markdown_table(spotify["by_cohort"], ["temporal_cohort", "len"]),
                "",
                "### Divergência frente aos benchmarks fornecidos",
                "",
                "```json",
                json.dumps(
                    spotify["benchmark_differences_observed_minus_benchmark"],
                    indent=2,
                    ensure_ascii=False,
                ),
                "```",
                "",
                "### Flags e problemas",
                "",
                "```json",
                json.dumps(spotify["quality_flags"], indent=2, ensure_ascii=False),
                "```",
                "",
                f"Sinal heurístico de balanceamento artificial por gênero: **{spotify['genre_balance_investigation']['possible_artificial_balance_signal']}**. "
                "A heurística não comprova o mecanismo de coleta e a base não deve ser descrita como amostra representativa de todo o Spotify.",
                "",
            ]
        )
    else:
        lines.extend(
            ["_Auditoria não executada: arquivo Spotify indisponível ou etapa bloqueada._", ""]
        )
    lines.extend(["## LFM2b", ""])
    if lfm:
        lines.extend(
            [
                f"Foram observados **{lfm['rows']:,}** registros, **{lfm['columns']}** colunas e **{lfm['descriptor_count']}** colunas classificadas como descritores LFM2b.",
                "",
                f"Excesso de duplicatas da chave operacional: {lfm['duplicate_original_key_excess_rows']:,}; "
                f"excesso de artista+título: {lfm['duplicate_artist_title_excess_rows']:,}.",
                "",
                "O campo original `popularity` foi preservado semanticamente como `genius_lyrics_views`; `lfm_playcount` permanece separado. O arquivo contém descritores derivados e não é tratado como corpus de letras integrais.",
                "",
                "### Coortes observadas",
                "",
                _markdown_table(lfm["by_cohort"], ["cohort", "count"]),
                "",
            ]
        )
    else:
        lines.extend(
            ["_Auditoria não executada: arquivo LFM2b indisponível ou etapa bloqueada._", ""]
        )
    lines.extend(
        [
            "## Figuras",
            "",
            "- [Músicas Spotify por ano](figures/spotify_tracks_by_year.png)",
            "- [Músicas Spotify por coorte](figures/spotify_tracks_by_cohort.png)",
            "- [Popularidade Spotify](figures/spotify_popularity_distribution.png)",
            "- [Popularidade zero por coorte](figures/spotify_zero_popularity_by_cohort.png)",
            "- [Principais gêneros](figures/spotify_top_genres.png)",
            "- [Missingness](figures/spotify_missingness.png)",
            "",
            "## Limitações",
            "",
            "As métricas são snapshots das respectivas fontes. Não se combinam `spotify_popularity`, `genius_lyrics_views` e `lfm_playcount`. Correlações e comparações são descritivas e não causais.",
        ]
    )
    path = project_path("reports/data_audit.md")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_matching_report() -> Path:
    summary = _read("reports/tables/matching_summary.json")
    bias = _read("reports/tables/selection_bias.json")
    lines = ["# Relatório de matching — Spotify × LFM2b", "", f"Gerado em: `{utc_now()}`.", ""]
    if not summary:
        lines.extend(
            [
                "## Status",
                "",
                "Matching não executado porque uma ou ambas as camadas normalizadas estão indisponíveis.",
            ]
        )
    else:
        lines.extend(
            [
                "## Funil por método e status",
                "",
                _markdown_table(
                    summary["by_method_and_status"],
                    [
                        "method",
                        "status",
                        "candidate_rows",
                        "spotify_tracks",
                        "percent_of_spotify_tracks",
                    ],
                ),
                "",
                "## Multiplicidades determinísticas",
                "",
                _markdown_table(
                    summary.get("deterministic_multiplicity", []),
                    ["mapping_type", "candidate_rows", "spotify_tracks", "lfm_records"],
                ),
                "",
                "A amostra estratificada para revisão permanece pendente em `data/processed/spotify_lfm_review_sample.parquet`.",
                "",
                "Matches fuzzy permanecem `candidate_for_review`; nenhum foi aceito automaticamente. Mapeamentos não únicos permanecem ambíguos e não entram na base analítica.",
                "",
                "## Diagnóstico de seleção",
                "",
            ]
        )
        if bias:
            lines.extend(
                [
                    f"Cobertura aceita: **{bias['matched']:,} / {bias['total_spotify']:,} ({bias['match_rate_percent']:.4f}%)**.",
                    "",
                    f"Popularidade Spotify média — matched: {bias['numeric_comparison']['spotify_popularity']['matched_mean']:.4f}; "
                    f"unmatched: {bias['numeric_comparison']['spotify_popularity']['unmatched_mean']:.4f}.",
                    "",
                    f"Popularidade Spotify mediana — matched: {bias['numeric_comparison']['spotify_popularity']['matched_median']:.4f}; "
                    f"unmatched: {bias['numeric_comparison']['spotify_popularity']['unmatched_median']:.4f}.",
                    "",
                    f"> {bias['warning']}",
                    "",
                ]
            )
        lines.extend(
            [
                "## Riscos e uso futuro",
                "",
                "Os principais riscos são colisões de nomes normalizados, versões incompatíveis, múltiplas gravações da mesma composição e diferenças temporais. Apenas pares únicos aceitos entram em `modeling_base_lfm_v0_1`; a granularidade é um par Spotify–LFM2b aceito, não uma composição universal.",
                "",
                "A comparação de cobertura não permite concluir que descritores de letras expliquem popularidade.",
                "",
                "## Figuras",
                "",
                "- [Funil de matching](figures/matching_funnel.png)",
                "- [Taxa de match por ano](figures/match_rate_by_year.png)",
                "- [Taxa de match por gênero](figures/match_rate_by_genre.png)",
                "- [Popularidade matched × unmatched](figures/popularity_matched_unmatched.png)",
                "- [Distribuição temporal matched × não aceito](figures/temporal_matched_unmatched.png)",
            ]
        )
    path = project_path("reports/matching_report.md")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _variable_semantics(name: str) -> str:
    exact = {
        "track_id": "Identificador de faixa fornecido na fonte Spotify.",
        "spotify_popularity": "Popularidade Spotify observada no snapshot da coleta; escala 0–100.",
        "artist_name_raw": "Artista original, preservado sem normalização.",
        "track_name_raw": "Título original, preservado sem normalização.",
        "genius_lyrics_views": "Campo original LFM2b `popularity`: visualizações da letra no Genius.",
        "lfm_playcount": "Número de eventos de escuta na base LFM-2b.",
        "lfm_record_key": "Hash operacional do registro LFM2b; não é identificador universal.",
        "composition_key": "Chave operacional artista principal+título-base; não é identificador universal.",
        "lfm_composition_key": "Chave operacional artista principal+título-base; não é identificador universal.",
        "match_status": "Status final do cruzamento conservador.",
        "match_method": "Primeiro método determinístico que gerou o par candidato.",
        "match_score": "Similaridade fuzzy quando aplicável; nulo para métodos determinísticos.",
    }
    if name in exact:
        return exact[name]
    if name.startswith("qf_") or name.startswith("lfm_qf_"):
        return "Flag de qualidade; o registro é preservado."
    if name.startswith("lfm_affective_"):
        return "Descritor afetivo/emocional derivado das letras pelo LFM2b."
    if name.startswith("lfm_lexical_"):
        return "Descritor lexical derivado das letras pelo LFM2b."
    if name.startswith("lfm_readability_"):
        return "Descritor de legibilidade derivado das letras pelo LFM2b."
    if name.startswith("lfm_rhyme_"):
        return "Descritor de rima/aliteração derivado das letras pelo LFM2b."
    if name.startswith("lfm_structure_"):
        return "Descritor estrutural derivado das letras pelo LFM2b."
    if name.startswith("lfm_"):
        return "Campo da fonte LFM2b ou variante normalizada documentada pelo nome."
    if name in {
        "danceability",
        "energy",
        "speechiness",
        "acousticness",
        "instrumentalness",
        "liveness",
        "valence",
    }:
        return "Descritor acústico Spotify na faixa esperada [0, 1]."
    if name in {"tempo", "loudness", "duration_ms", "key", "mode", "time_signature"}:
        return "Descritor acústico/metadado fornecido pela fonte Spotify."
    if any(token in name for token in ("strict", "conservative", "unicode", "base", "primary")):
        return "Variante normalizada não destrutiva para matching."
    if name in VERSION_NAMES:
        return "Flag de versão inferida do título; informação original preservada."
    return "Campo preservado ou derivado; regra detalhada em docs/methodology_log.md."


VERSION_NAMES = {
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
}


def write_data_dictionary() -> Path:
    spotify = _read("reports/tables/spotify_audit.json") or {}
    lfm = _read("reports/tables/lfm2b_audit.json") or {}
    rows: list[dict[str, Any]] = []
    for origin, audit, grain in (
        ("Spotify", spotify, "registro de faixa Spotify"),
        ("LFM2b", lfm, "registro de descritores LFM2b"),
    ):
        for name, dtype in audit.get("schema", {}).items():
            rows.append(
                {
                    "variável": name,
                    "origem": origin,
                    "tipo": dtype,
                    "granularidade": grain,
                    "semântica": _variable_semantics(name),
                }
            )
    lines = [
        "# Dicionário de dados — Base v0.1",
        "",
        "Gerado do schema observado. A base de modelagem tem uma linha por par Spotify–LFM2b aceito; campos Spotify e LFM2b preservam suas granularidades de origem.",
        "",
        _markdown_table(rows, ["variável", "origem", "tipo", "granularidade", "semântica"]),
        "",
        "`spotify_popularity`, `genius_lyrics_views` e `lfm_playcount` são métricas distintas e não devem ser combinadas como um único desfecho.",
    ]
    path = project_path("docs/data_dictionary.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_reports() -> dict[str, Any]:
    figures = generate_figures()
    data_audit = write_data_audit()
    matching_report = write_matching_report()
    data_dictionary = write_data_dictionary()
    return {
        "figures": figures,
        "data_audit": str(data_audit),
        "matching_report": str(matching_report),
        "data_dictionary": str(data_dictionary),
    }
