"""Private development coverage, aggregate learning curves and V0.9 reports."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl

from .statistical_revision_v080 import FLAGS, metrics
from .training_expansion_v090 import (
    BLOCKS,
    FIGURES,
    PRIVATE,
    ROOT,
    SEEDS,
    TARGET,
    collect_predictions,
    digest,
    now,
    output,
    read_json,
    write_json,
)


def number(value):
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.5f}"
    return str(value)


def table(headers, rows):
    return (
        "\n".join(
            [
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join(["---"] * len(headers)) + " |",
                *[
                    "| " + " | ".join(number(v).replace("|", "\\|") for v in row) + " |"
                    for row in rows
                ],
            ]
        )
        + "\n"
    )


def population_stages(tracks, reps):
    return {
        "integrated_development_tracks": tracks,
        "eligible_development_compositions": reps,
        "v04_main_selected": reps.filter(pl.col("sampling_role") == "main"),
        "v04_reserve_available": reps.filter(pl.col("sampling_role") == "reserve"),
        "v04_actually_queried": reps.filter(pl.col("final_status") != "not_queried"),
        "v04_lyrics_accepted": reps.filter(pl.col("lyrics_accepted_v04")),
        "common_v05": reps.filter(pl.col("in_common_v05")),
        "additional_compositions": reps.filter(~pl.col("in_common_v05")),
    }


def distribution_summary(frame):
    y = frame[TARGET].drop_nulls().to_numpy()
    return {
        "n": frame.height,
        "artists": frame["artist_group_id"].n_unique(),
        "tracks": frame["track_id"].n_unique(),
        "compositions": frame["composition_key"].drop_nulls().n_unique(),
        "target_missing": frame[TARGET].null_count(),
        "mean_target": float(y.mean()) if len(y) else None,
        "median_target": float(np.median(y)) if len(y) else None,
        "p90_target": float(np.quantile(y, 0.9)) if len(y) else None,
        "minimum_target": float(y.min()) if len(y) else None,
        "maximum_target": float(y.max()) if len(y) else None,
    }


def coverage(tracks, reps):
    stages = population_stages(tracks, reps)
    artist_sizes = reps.group_by("artist_group_id").len().rename({"len": "eligible_artist_size"})
    rows, artist_rows, stage_stats = [], [], []
    for stage, original in stages.items():
        frame = original.join(
            artist_sizes, on="artist_group_id", how="left", validate="m:1"
        ).with_columns(pl.col("eligible_artist_size").fill_null(0))
        stage_stats.append(
            {
                "stage": stage,
                **distribution_summary(frame),
                **{f"n_ge{cut}": int((frame[TARGET] >= cut).sum()) for cut in (60, 70, 80)},
            }
        )
        y = frame[TARGET].to_numpy()
        groups = [("all", "all", np.ones(frame.height, bool))]
        for lo in range(0, 100, 10):
            groups.append(
                (
                    "popularity_band",
                    f"[{lo},{lo + 10}{']' if lo == 90 else ')'}",
                    (y >= lo) & ((y <= 100) if lo == 90 else (y < lo + 10)),
                )
            )
        groups += [("popularity_threshold", f">={cut}", y >= cut) for cut in (60, 70, 80)]
        for col in ("genre", "year", "final_status", "sampling_role"):
            for value in sorted(frame[col].drop_nulls().unique().to_list()):
                groups.append((col, str(value), (frame[col] == value).fill_null(False).to_numpy()))
            if frame[col].null_count():
                groups.append((col, "(ausente)", frame[col].is_null().to_numpy()))
        any_flag = np.zeros(frame.height, bool)
        for flag in FLAGS:
            values = frame[flag].fill_null(False).to_numpy()
            any_flag |= values
            groups += [
                ("version_flag", f"{flag}={value}", values == value) for value in (False, True)
            ]
        groups += [("any_version", str(value), any_flag == value) for value in (False, True)]
        sizes = frame["eligible_artist_size"].to_numpy()
        for label, lo, hi in (
            ("0", 0, 0),
            ("1", 1, 1),
            ("2-5", 2, 5),
            ("6-20", 6, 20),
            ("21-100", 21, 100),
            (">100", 101, np.inf),
        ):
            groups.append(("artist_group_size", label, (sizes >= lo) & (sizes <= hi)))
        for dimension, category, mask in groups:
            selected = frame.filter(pl.Series(mask))
            rows.append(
                {
                    "stage": stage,
                    "dimension": dimension,
                    "category": category,
                    "denominator": frame.height,
                    "proportion": selected.height / frame.height if frame.height else None,
                    "small_group_n_lt30": selected.height < 30,
                    **distribution_summary(selected),
                }
            )
        per_artist = (
            frame.group_by("artist_group_id")
            .agg(
                pl.len().alias("n"),
                pl.col("composition_key").drop_nulls().n_unique().alias("compositions"),
                pl.col(TARGET).mean().alias("mean_target"),
                pl.col(TARGET).max().alias("max_target"),
            )
            .with_columns(pl.lit(stage).alias("stage"))
        )
        artist_rows.append(per_artist)
    pl.concat(artist_rows, how="vertical_relaxed").write_parquet(
        output(PRIVATE / "coverage_artist_groups.parquet")
    )
    pl.DataFrame(rows, infer_schema_length=None).write_csv(
        output(Path("reports/cobertura_popularidade_v0_9.csv"))
    )
    return stage_stats, rows


def base_reports(tracks, reps, common, plan, audit):
    stage_stats, distributions = coverage(tracks, reps)
    summary = {"stage_counts": stage_stats, "coverage_rows": len(distributions), "audit": audit}
    write_json(PRIVATE / "coverage_summary.json", summary)
    statuses = (
        reps.filter(pl.col("final_status") != "not_queried")
        .group_by("final_status")
        .len()
        .sort("final_status")
        .to_dicts()
    )
    eligible = next(r for r in stage_stats if r["stage"] == "eligible_development_compositions")
    queried = next(r for r in stage_stats if r["stage"] == "v04_actually_queried")
    text = [
        "# Base analítica ampliada — V0.9",
        "Matriz exclusivamente de development_train original. Alvos do holdout não foram carregados, nem dos registros que ficaram fora da V0.6. Rodada exploratória, sem confirmação independente. Identificadores, alvos e detalhes por artista permanecem privados.",
        "## Granularidade, elegibilidade e preservação",
        f"Faixas Spotify: {tracks.height:,}; representantes por composição: {reps.height:,}; matriz comum: {common.height:,}; composições adicionais: {reps.height - common.height:,}. Cada target é unido à própria faixa por IDs; não transferido para outra versão. Track_id é faixa da fonte; composition_key é agrupamento operacional; flags são indícios de versão. Nenhuma linha é removida por popularidade ou erro e nenhum alvo é imputado.",
        f"Sem chave de composição: {audit['representative_audit']['missing_composition_key_rows']} faixas, preservadas na matriz por track_id; sem participação na visão por composição. Linhas adicionais colapsadas pela regra antiga de representante: {audit['representative_audit']['duplicate_rows_collapsed']}. IDs de faixa duplicados: {audit['duplicate_track_ids']}; alvo ausente: {audit['missing_target']}; alvo não finito: {audit['nonfinite_target']}; fora da escala nominal: {audit['target_outside_nominal_scale']} (não excluídos por valor).",
        "A regra V0.4 de representante foi reutilizada sem alvo, letra ou embedding. Os representantes da coorte/reserva V0.4 e os 7.648 comuns V0.5 foram reconciliados; grupos, inputs e alvos dos comuns coincidem. Indicadores de coleta/qualidade/matching não são preditores. Year é somente o ano informado pela fonte, não lançamento original certificado; genre não recebe semântica inferida.",
        "## Cobertura e faixas altas de popularidade",
        table(
            ["Etapa", "n", "Composições", "Artistas", "≥60", "≥70", "≥80", "Média", "Máximo"],
            [
                [
                    r["stage"],
                    r["n"],
                    r["compositions"],
                    r["artists"],
                    r["n_ge60"],
                    r["n_ge70"],
                    r["n_ge80"],
                    r["mean_target"],
                    r["maximum_target"],
                ]
                for r in stage_stats
            ],
        ),
        "Etapas não são parcelas aditivas: reserva disponível inclui registros não ativados; a consulta efetiva inclui principal e apenas reserva ativada. Limiares ≥60/≥70/≥80 se sobrepõem. O CSV contém faixas, gênero, cada ano, flags, status e tamanhos de grupo de artista, sempre com denominador. Distribuições por grupo individual estão em arquivo privado; nenhuma diferença é interpretada como causal.",
        f"Perda por não seleção/consulta na V0.4: {eligible['n'] - queried['n']:,} composições elegíveis. Entre as {queried['n']:,} consultadas, status abaixo. Ambiguidade não é ausência de letra; request_error é falha técnica, não rejeição científica da música.",
        table(["Status V0.4", "n"], [[r["final_status"], r["len"]] for r in statuses]),
        "## Ausências e qualidade",
        table(
            ["Identificador", "Ausentes", "Distintos", "Repetições"],
            [
                [name, row["missing"], row["distinct"], row["repeated_rows"]]
                for name, row in audit["identifier_audit"].items()
            ],
        ),
        f"Registros LFM ligados a mais de uma faixa Spotify: {audit['lfm_records_linked_to_multiple_tracks']}; composições ligadas a mais de um grupo de artista: {audit['compositions_linked_to_multiple_artists']}. Reutilização de um registro LFM não equivale automaticamente a duplicação de track_id; a visão experimental mantém um representante por composição operacional.",
        table(
            ["Campo preditor", "Ausentes nas faixas de desenvolvimento"],
            [[k, v] for k, v in audit["missing_predictors"].items() if v],
        ),
        f"Total de preditores com não finitos: {sum(v > 0 for v in audit['nonfinite_predictors'].values())}. Grupos ausentes: {audit['missing_groups']}. Multiplicidade máxima observada de faixas por composition_key: {audit['tracks_per_composition_max']}. Imputação não ocorre na matriz; será aprendida em cada treino. Zero novas letras ou embeddings foram produzidos.",
        "## Partições ampliadas auditadas antes dos ajustes",
        table(
            [
                "Fold",
                "Validação fixa",
                "Treino comum original",
                "Máximo ampliado",
                "Linhas com hash conhecido",
            ],
            [
                [
                    r["fold"],
                    r["validation_n"],
                    r["common_train_n"],
                    r["expanded_max_n"],
                    r["expanded_known_hash_rows"],
                ]
                for r in plan["fold_audit"]
            ],
        ),
        "Artistas, composition_key, composition_group_id, split_group_id e hashes documentados foram excluídos do treino quando presentes na validação ou holdout original. Os máximos contêm integralmente o treino comum original. A auditoria por hash usa fontes históricas, sem abrir letras/vetores e sem recalcular hashes. Hash desconhecido não significa texto distinto: contaminação textual não observável continua limitação.",
        "## Dicionário e proveniência dos novos artefatos privados",
        "`tracks.parquet`: uma linha por track_id; IDs de origem, grupos/split originais, alvo da faixa, 23+196 inputs congelados, metadados de origem, matching e qualidade. `composition_key_available`, `is_operational_representative` e `in_common_v05` indicam elegibilidade/representação/presença anterior. `sampling_role`, `reserve_batch`, `final_status`, `lyrics_accepted_v04` documentam seleção/coleta; `not_selected` e `not_queried` distinguem ausência de participação de fracasso de consulta. `known_hash_count` conta pares tipo/hash conhecidos, não quantidade de letras independentes. Nenhum desses indicadores documentais entra em X.",
        "`representatives.parquet`: subconjunto com representante anterior de cada composição, mesma popularidade da faixa selecionada. `common.parquet`: somente inputs Baseline/Tradicional, chaves, alvo já autorizado e folds V0.5, sem embeddings. `hash_catalog.parquet`: relações track/composição/tipo/hash/fonte/split, apenas metadados; namespaces não são intercambiáveis. `partition_plan.json`: índices privados, sementes, tamanhos, assinaturas e exclusões. `coverage_artist_groups.parquet`: estatísticas por artista, privadas. Predições/checkpoints serão escritos somente no diretório novo V0.9.",
        "Nenhuma normalização ou correção de year/genre/flags foi aplicada. Preservam-se imperfeições de identidade e possibilidade de descritores/textos representarem versões diferentes. A inclusão ampliada não depende de disponibilidade de letra integral.",
    ]
    output(Path("reports/base_analitica_ampliada_v0_9.md")).write_text(
        "\n\n".join(text) + "\n", encoding="utf-8"
    )
    return summary


def curve_metrics(common, predictions, records):
    y = common[TARGET].to_numpy()
    rows = []
    for key, vector in predictions.items():
        matching = [r for r in records if f"{r['condition']}__{r['block']}" == key]
        first = matching[0]
        base = {
            k: first[k]
            for k in ("condition", "block", "universe", "size_label", "seed", "requested_n")
        }
        sizes = [r["train_n"] for r in matching]
        training = {
            "train_n_mean": float(np.mean(sizes)),
            "train_n_min": min(sizes),
            "train_n_max": max(sizes),
            "train_artists_mean": float(np.mean([r["train_artists"] for r in matching])),
        }
        rows.append(
            {
                **base,
                "scope": "oof",
                "fold": None,
                "target_band": "all",
                **training,
                **metrics(y, vector),
                "small_group_n_lt30": False,
            }
        )
        for record in matching:
            mask = common["outer_fold"].to_numpy() == record["fold"]
            rows.append(
                {
                    **base,
                    "scope": "fold",
                    "fold": record["fold"],
                    "target_band": "all",
                    "train_n_mean": float(record["train_n"]),
                    "train_n_min": record["train_n"],
                    "train_n_max": record["train_n"],
                    "train_artists_mean": float(record["train_artists"]),
                    **metrics(y[mask], vector[mask]),
                    "small_group_n_lt30": False,
                }
            )
        for lo in range(0, 100, 10):
            mask = (y >= lo) & ((y <= 100) if lo == 90 else (y < lo + 10))
            measured = metrics(y[mask], vector[mask])
            measured["r2"] = None
            rows.append(
                {
                    **base,
                    "scope": "target_band",
                    "fold": None,
                    "target_band": f"[{lo},{lo + 10}{']' if lo == 90 else ')'}",
                    **training,
                    **measured,
                    "small_group_n_lt30": int(mask.sum()) < 30,
                }
            )
    return rows


def comparisons(rows):
    overall = [r for r in rows if r["scope"] == "oof"]
    result = []
    measures = (
        "mae",
        "rmse",
        "r2",
        "median_abs_error",
        "p90_abs_error",
        "p95_abs_error",
        "prop_abs_le5",
        "prop_abs_le10",
        "prop_abs_gt20",
        "n_abs_gt20",
    )
    for row in overall:
        reference = next(
            r
            for r in overall
            if r["universe"] == "common"
            and r["size_label"] == "original"
            and r["block"] == row["block"]
        )
        result.append(
            {
                "kind": "vs_original_common",
                "condition": row["condition"],
                "block": row["block"],
                "reference": reference["condition"],
                "train_n_mean": row["train_n_mean"],
                **{f"delta_{m}": row[m] - reference[m] for m in measures},
                "mae_change_percent": 100 * (row["mae"] / reference["mae"] - 1),
            }
        )
        if row["block"] == "traditional":
            baseline = next(
                r
                for r in overall
                if r["condition"] == row["condition"] and r["block"] == "baseline"
            )
            result.append(
                {
                    "kind": "traditional_vs_baseline_same_training",
                    "condition": row["condition"],
                    "block": "traditional",
                    "reference": "baseline",
                    "train_n_mean": row["train_n_mean"],
                    **{f"delta_{m}": row[m] - baseline[m] for m in measures},
                    "mae_change_percent": 100 * (row["mae"] / baseline["mae"] - 1),
                }
            )
        if row["universe"] == "expanded" and row["size_label"] in {"2000", "5000"}:
            matched = next(
                r
                for r in overall
                if r["universe"] == "common"
                and r["size_label"] == row["size_label"]
                and r["seed"] == row["seed"]
                and r["block"] == row["block"]
            )
            result.append(
                {
                    "kind": "expanded_vs_common_approximate_same_size",
                    "condition": row["condition"],
                    "block": row["block"],
                    "reference": matched["condition"],
                    "train_n_mean": row["train_n_mean"],
                    "reference_train_n_mean": matched["train_n_mean"],
                    **{f"delta_{m}": row[m] - matched[m] for m in measures},
                    "mae_change_percent": 100 * (row["mae"] / matched["mae"] - 1),
                }
            )
    return result


def create_figures(rows):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    overall = [r for r in rows if r["scope"] == "oof"]
    paths = []
    for metric, label in (
        ("mae", "MAE (pontos)"),
        ("rmse", "RMSE (pontos)"),
        ("p95_abs_error", "P95 do erro absoluto (pontos)"),
        ("prop_abs_gt20", "Erros acima de 20 pontos (%)"),
    ):
        fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), sharey=True)
        factor = 100 if metric == "prop_abs_gt20" else 1
        for ax, block in zip(axes, BLOCKS, strict=True):
            chosen = [r for r in overall if r["block"] == block]
            original = next(r for r in chosen if r["size_label"] == "original")
            maximum = next(r for r in chosen if r["size_label"] == "maximum")
            ax.axhline(
                factor * original[metric],
                color="black",
                ls=":",
                lw=1.6,
                label="Comum original (fixo)",
            )
            for universe, color in (("common", "#9457a3"), ("expanded", "#007c91")):
                for i, seed in enumerate(SEEDS):
                    points = sorted(
                        [r for r in chosen if r["universe"] == universe and r["seed"] == seed],
                        key=lambda r: r["train_n_mean"],
                    )
                    if universe == "expanded":
                        points = points + [maximum]
                    ax.plot(
                        [r["train_n_mean"] for r in points],
                        [factor * r[metric] for r in points],
                        marker="o",
                        ms=4,
                        lw=1.3,
                        color=color,
                        ls=("-" if i == 0 else "--"),
                        alpha=0.85,
                        label=f"{universe}; seed {seed}",
                    )
                grouped = defaultdict(list)
                for row in chosen:
                    if row["universe"] == universe and row["seed"] is not None:
                        grouped[row["size_label"]].append(row)
                means = sorted(
                    [
                        (
                            np.mean([r["train_n_mean"] for r in values]),
                            factor * np.mean([r[metric] for r in values]),
                        )
                        for values in grouped.values()
                    ]
                )
                ax.scatter(
                    [p[0] for p in means],
                    [p[1] for p in means],
                    color=color,
                    marker="x",
                    s=45,
                    zorder=4,
                    label=f"{universe}: média das sementes",
                )
            ax.scatter(
                [original["train_n_mean"]],
                [factor * original[metric]],
                color="black",
                marker="s",
                s=35,
                zorder=5,
            )
            ax.set_xscale("log")
            ax.set_xlabel("n efetivo médio de treino por fold (escala log)")
            ax.set_title("Baseline" if block == "baseline" else "Tradicional (PCA90 LFM2b)")
            ax.grid(alpha=0.2)
        axes[0].set_ylabel(label)
        handles, labels = axes[1].get_legend_handles_labels()
        fig.legend(
            handles, labels, loc="lower center", ncol=3, fontsize=8, bbox_to_anchor=(0.5, 0.055)
        )
        fig.suptitle("V0.9 exploratória — mesma validação de 7.648 composições", fontsize=12)
        fig.text(
            0.5,
            0.025,
            "Máximo treinado uma vez; médias entre sementes são descritivas, sem intervalo de confiança.",
            ha="center",
            fontsize=8,
        )
        fig.tight_layout(rect=(0, 0.23, 1, 0.95))
        path = FIGURES / f"curva_{metric}_v0_9.png"
        fig.savefig(output(path), dpi=170, bbox_inches="tight")
        plt.close(fig)
        paths.append(path.as_posix())
    return paths


def deliver(seal, preservation, verification=None):
    _, common, predictions, records, _ = collect_predictions(seal)
    rows = curve_metrics(common, predictions, records)
    comparison = comparisons(rows)
    curve_path = Path("reports/curvas_aprendizagem_v0_9.csv")
    pl.DataFrame(rows, infer_schema_length=None).write_csv(output(curve_path))
    private_oof = common.select(
        "track_id", "composition_key", "spotify_row_id", "artist_group_id", TARGET, "outer_fold"
    ).with_columns([pl.Series(f"prediction__{key}", vector) for key, vector in predictions.items()])
    private_oof.write_parquet(output(PRIVATE / "oof_predictions.parquet"))
    figures = create_figures(rows)
    coverage_data = read_json(PRIVATE / "coverage_summary.json")
    plan = read_json(PRIVATE / "partition_plan.json")
    old_summary = ROOT / "reports/run_summary_ampliacao_v0_9.json"
    commands = (
        read_json(old_summary).get("verification_commands", []) if old_summary.is_file() else []
    )
    summary = {
        "version": "v0.9",
        "status": "complete_verified" if verification else "complete_pending_verification",
        "completed_at": now(),
        "exploratory": True,
        "independent_confirmation": False,
        "holdout_targets_loaded": False,
        "protocol_sha256": seal["protocol_sha256"],
        "sealed_before_fitting_at": seal["sealed_before_any_fitting_at"],
        "seal_id": seal["seal_id"],
        "code_sha256": seal["code_sha256"],
        "inputs_sha256": seal["inputs_sha256"],
        "versions": seal["versions"],
        "configs": seal["configs"],
        "seeds": seal["seeds"],
        "coverage": coverage_data,
        "fold_audit": plan["fold_audit"],
        "metrics": rows,
        "comparisons": comparison,
        "model_records": records,
        "fit_attempts": sum(r["fit_attempts"] for r in records),
        "warning_count": sum(r["warning_count"] for r in records),
        "failed_configurations": 0,
        "technical_benchmark": read_json(PRIVATE / "benchmark.json"),
        "execution": read_json(PRIVATE / "execution.json"),
        "verification": verification,
        "preservation": preservation,
        "verification_commands": commands,
        "oof_sha256": digest(PRIVATE / "oof_predictions.parquet"),
        "figures": figures,
        "public_artifact_sha256": {
            p: digest(p)
            for p in [curve_path.as_posix(), "reports/cobertura_popularidade_v0_9.csv", *figures]
        },
        "limitations": [
            "Validação condicionada à disponibilidade de letras, não validação representativa de toda a base ampliada.",
            "Exploratória pós-holdout e com hiperparâmetros finais previamente escolhidos; não confirmação independente.",
            "Identidade operacional e flags/ano/gênero não certificam obra, versão ou lançamento original.",
            "Hashes ausentes não permitem excluir duplicação textual desconhecida.",
            "Amostras por grupos têm tamanhos aproximados; controles de tamanho não isolam causalmente composição.",
            "Duas sementes não formam intervalo de confiança nem justificam escolher a melhor.",
        ],
    }
    write_json(Path("reports/run_summary_ampliacao_v0_9.json"), summary)
    overall = [r for r in rows if r["scope"] == "oof"]
    max_results = [
        r for r in comparison if r["kind"] == "vs_original_common" and "maximum" in r["condition"]
    ]
    sections = [
        "# Experimento de ampliação do treinamento — V0.9",
        "Exploratório, sem confirmação independente. Mesmas 7.648 observações e cinco folds externos V0.5/V0.8 para todas as condições. Nenhum alvo do holdout original foi carregado. Modelos, splits, dados e resultados anteriores preservados; sem coleta, novos embeddings, interface, commit ou push.",
        "## Desenho e referência correta",
        f"SHA-256 do protocolo antes dos ajustes: `{seal['protocol_sha256']}`. Dois Elastic Net com alpha=0.003/l1_ratio=0.95, fixados a partir dos ajustes finais V0.5. Sem tuning. A referência 'common original' foi **reajustada com essa configuração fixa**, portanto não deve ser confundida com a OOF V0.5 produzida por tuning interno por fold. Todo pré-processamento e coeficientes foram reaprendidos em cada treino; PCA90 somente no bloco LFM2b.",
        f"Sementes dos subconjuntos: {SEEDS[0]} e {SEEDS[1]}. Grupos completos, ordenados por hash sem alvo ou resultados. Cada sequência é aninhada; máximo contém o treino comum original e é ajustado uma só vez. Comum com aproximadamente 2.000/5.000 oferece controle de tamanho versus ampliado; diferenças de composição e contagens efetivas não desaparecem. Não se escolheu a melhor semente.",
        "## Cobertura disponível",
        table(
            ["Etapa", "n", "Composições", "Artistas", "≥60", "≥70", "≥80"],
            [
                [
                    r["stage"],
                    r["n"],
                    r["compositions"],
                    r["artists"],
                    r["n_ge60"],
                    r["n_ge70"],
                    r["n_ge80"],
                ]
                for r in coverage_data["stage_counts"]
            ],
        ),
        "## Máximo ampliado versus treino comum original",
        table(
            ["Bloco", "ΔMAE", "ΔMAE %", "ΔRMSE", "ΔP95", "Δ >20 (n)"],
            [
                [
                    r["block"],
                    r["delta_mae"],
                    r["mae_change_percent"],
                    r["delta_rmse"],
                    r["delta_p95_abs_error"],
                    r["delta_n_abs_gt20"],
                ]
                for r in max_results
            ],
        ),
        "Deltas negativos de erro indicam melhora. Ganho de quantidade/composição não pode ser atribuído às letras. Os próximos resultados mostram todas as condições, sem exclusão retrospectiva.",
        "## Curvas OOF completas",
        "n de treino é a média efetiva entre os cinco folds (mínimo/máximo no CSV); não é soma de amostras independentes. OOF n=7.648 em cada linha. Proporções >20 abaixo são percentuais; no CSV são frações. Previsões brutas, sem clipping ou calibração.",
        table(
            [
                "Condição",
                "Bloco",
                "n treino médio",
                "MAE",
                "RMSE",
                "R²",
                "Mediana",
                "P90",
                "P95",
                ">20 %",
                "n >20",
            ],
            [
                [
                    r["condition"],
                    r["block"],
                    r["train_n_mean"],
                    r["mae"],
                    r["rmse"],
                    r["r2"],
                    r["median_abs_error"],
                    r["p90_abs_error"],
                    r["p95_abs_error"],
                    100 * r["prop_abs_gt20"],
                    r["n_abs_gt20"],
                ]
                for r in overall
            ],
        ),
        "## Controles de tamanho aproximado",
        table(
            ["Condição ampliada", "Bloco", "n ampliado", "n comum", "ΔMAE", "ΔRMSE", "ΔP95"],
            [
                [
                    r["condition"],
                    r["block"],
                    r["train_n_mean"],
                    r["reference_train_n_mean"],
                    r["delta_mae"],
                    r["delta_rmse"],
                    r["delta_p95_abs_error"],
                ]
                for r in comparison
                if r["kind"] == "expanded_vs_common_approximate_same_size"
            ],
        ),
        "Esses controles ajudam a distinguir quantidade e composição; não demonstram efeito causal e não tornam os universos intercambiáveis.",
        "## Tradicional versus Baseline com as mesmas linhas",
        table(
            ["Condição", "ΔMAE T−B", "ΔMAE %", "ΔRMSE", "ΔP95", "Δ >20 (n)"],
            [
                [
                    r["condition"],
                    r["delta_mae"],
                    r["mae_change_percent"],
                    r["delta_rmse"],
                    r["delta_p95_abs_error"],
                    r["delta_n_abs_gt20"],
                ]
                for r in comparison
                if r["kind"] == "traditional_vs_baseline_same_training"
            ],
        ),
        "## Gráficos agregados",
        "Linhas mostram as duas sementes e cruzes suas médias descritivas. O máximo compartilhado aparece nas duas trajetórias, mas foi treinado uma única vez. Não há IC a partir dessas duas sementes.",
    ]
    for path in figures:
        sections.append(
            f"![Curva exploratória {Path(path).stem}](figures/ampliacao_v0_9/{Path(path).name})"
        )
    sections += [
        "## Faixas do alvo e resultados por fold",
        "Todas as métricas por fold e por faixa estão em `curvas_aprendizagem_v0_9.csv`. Faixas com n<30 são marcadas; R² não é calculado nos estratos. A tabela abaixo compara as referências e os máximos; os denominadores permanecem exatamente iguais, pois não muda a validação.",
        table(
            ["Faixa", "Condição", "Bloco", "n", "n<30", "MAE", "RMSE", "P95", ">20 %"],
            [
                [
                    r["target_band"],
                    r["size_label"],
                    r["block"],
                    r["n"],
                    r["small_group_n_lt30"],
                    r["mae"],
                    r["rmse"],
                    r["p95_abs_error"],
                    None if r["prop_abs_gt20"] is None else 100 * r["prop_abs_gt20"],
                ]
                for r in rows
                if r["scope"] == "target_band" and r["size_label"] in {"original", "maximum"}
            ],
        ),
        "## Interpretação e limites",
        "Mais observações podem reduzir variância e melhorar suporte, mas as curvas variam também pela composição de artistas/faixas. Avaliar a sequência inteira, as duas sementes e erros de cauda; não declarar estabilização a partir de um único ponto nem promover candidato por uma semente favorável. Nenhuma das comparações é causal.",
        "A validação comum continua condicionada à disponibilidade de letras e tem somente 27 casos ≥70, um deles ≥80; não representa o universo ampliado. Melhorar nela não prova generalização a toda a base. Matching, chaves operacionais, versões alternativas, descritores LFM de outra versão e semântica limitada de year/genre/flags permanecem. Alvo é popularidade registrada no snapshot da faixa, não sucesso futuro. Nenhuma nova família de modelo foi introduzida.",
        "## Execução e verificações",
        f"Ajustes integrais: {len(records)}; tentativas de fit: {summary['fit_attempts']}; warnings: {summary['warning_count']}; configurações malsucedidas: 0. Benchmark adicional: dois ajustes. Tempo da execução integral: {summary['execution']['wall_seconds'] / 60:.2f} minutos. Configuração, tempos por condição, dimensões PCA e warnings estão no JSON.",
        f"Preservados {preservation['sha256_verified']} hashes de artefatos anteriores e metadados tamanho/mtime_ns de {preservation['old_data_metadata_verified']} arquivos de dados. Não confundir essas duas verificações. HEAD/stage inalterados, dados privados ignorados e nenhum dado/modelo privado rastreado. Alvos do holdout não foram carregados.",
        (
            f"Verificação real: {len(verification['model_checks'])} pipelines recarregados; diferença máxima de previsão {max(c['maximum_absolute_difference'] for c in verification['model_checks']):.3g}, atol=1e-10/rtol=0. Partições reconstruídas exatamente, zero sobreposição de grupos/hashes conhecidos, transformações train-only, input sem alvo e OOF completas/finitas."
            if verification
            else "Verificação independente dos modelos persistidos ainda pendente."
        ),
        "CLI no ambiente existente: `python -m tcc_music_popularity.training_expansion_v090 prepare`, depois `benchmark`, `run` e `verify`. Os dois primeiros recusam sobrescrever selos/testes existentes; para retomar, usar `run` com o mesmo selo. Comandos exatos de testes/lint e códigos de saída ficam no run summary após a entrega. Dicionário das matrizes e proveniência: `base_analitica_ampliada_v0_9.md`; arquivos individuais permanecem privados.",
    ]
    output(Path("reports/experimento_ampliacao_v0_9.md")).write_text(
        "\n\n".join(sections) + "\n", encoding="utf-8"
    )
    write_json(
        PRIVATE / "progress.json",
        {
            "status": summary["status"],
            "completed": len(records),
            "planned": seal["planned_model_fits"],
            "updated_at": now(),
        },
    )
