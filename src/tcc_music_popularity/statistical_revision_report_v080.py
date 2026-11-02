"""Aggregate-only reporting for the sealed V0.8 development experiment."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
import polars as pl

from tcc_music_popularity.statistical_revision_v080 import (
    BLOCKS,
    FAMILIES,
    FLAGS,
    PRIVATE,
    REFERENCE_NAMES,
    ROOT,
    TARGET,
    digest,
    metrics,
    now,
    output_path,
    read_json,
    write_json,
)


def compare(y, candidate, reference, folds, *, kind, name, reference_name):
    new, old = metrics(y, candidate), metrics(y, reference)
    folds_improved = sum(
        metrics(y[folds == f], candidate[folds == f])["mae"]
        < metrics(y[folds == f], reference[folds == f])["mae"]
        for f in range(5)
    )
    reductions = 100 * (old["mae"] - new["mae"]) / old["mae"]
    rmse_change = 100 * (new["rmse"] - old["rmse"]) / old["rmse"]
    p95_change = 100 * (new["p95_abs_error"] - old["p95_abs_error"]) / old["p95_abs_error"]
    # Evaluate ratios directly to avoid tiny percent cancellation at exact boundaries.
    mae_rule = new["mae"] <= old["mae"] * 0.98
    rmse_rule = new["rmse"] <= old["rmse"] * 1.02
    p95_rule = new["p95_abs_error"] <= old["p95_abs_error"] * 1.02
    result = {
        "comparison_kind": kind,
        "model": name,
        "reference": reference_name,
        "mae_reduction_percent": reductions,
        "rmse_change_percent": rmse_change,
        "p95_change_percent": p95_change,
        "folds_mae_improved": folds_improved,
        "mae_reduction_at_least_2_percent": mae_rule,
        "at_least_four_folds_better": folds_improved >= 4,
        "rmse_not_worse_over_2_percent": rmse_rule,
        "p95_not_worse_over_2_percent": p95_rule,
        "operational_rule_met": bool(mae_rule and folds_improved >= 4 and rmse_rule and p95_rule),
        "candidate_promising": bool(
            kind == "algorithm_vs_v05"
            and mae_rule
            and folds_improved >= 4
            and rmse_rule
            and p95_rule
        ),
        "mae_improved_but_tail_worse": bool(
            new["mae"] < old["mae"]
            and (
                new["p95_abs_error"] > old["p95_abs_error"]
                or new["prop_abs_gt20"] > old["prop_abs_gt20"]
            )
        ),
    }
    for metric in (
        "mae",
        "rmse",
        "r2",
        "median_abs_error",
        "p90_abs_error",
        "p95_abs_error",
        "prop_abs_le5",
        "prop_abs_le10",
        "prop_abs_le20",
        "prop_abs_gt20",
        "n_abs_gt20",
    ):
        result[f"new_{metric}"] = new[metric]
        result[f"reference_{metric}"] = old[metric]
        result[f"delta_{metric}"] = new[metric] - old[metric]
    return result


def strata(dev):
    y, years = dev[TARGET].to_numpy(), dev["year"].to_numpy()
    result = []
    for start in range(0, 100, 10):
        end = start + 10
        label = f"[{start},{end}{']' if end == 100 else ')'}"
        mask = (y >= start) & ((y <= end) if end == 100 else (y < end))
        result.append(("target_band", label, mask))
    periods = [
        ("<2000", -np.inf, 2000),
        ("2000-2004", 2000, 2005),
        ("2005-2009", 2005, 2010),
        ("2010-2014", 2010, 2015),
        ("2015-2019", 2015, 2020),
        ("2020-2023", 2020, 2024),
        (">=2024", 2024, np.inf),
    ]
    result.extend(("year_period", label, (years >= lo) & (years < hi)) for label, lo, hi in periods)
    any_version = np.zeros(dev.height, bool)
    for flag in FLAGS:
        any_version |= dev[flag].fill_null(False).to_numpy()
    for label, values in [
        ("any_version", any_version),
        *[(flag, dev[flag].fill_null(False).to_numpy()) for flag in FLAGS],
    ]:
        result.extend(
            ("version_flag", f"{label}={value}", values == value) for value in (False, True)
        )
    return result


def metric_rows(dev, folds, predictions, records):
    y, outer, artists = (
        dev[TARGET].to_numpy(),
        folds["outer_fold"].to_numpy(),
        dev["artist_group_id"].to_numpy(),
    )
    result = []
    for name, values in predictions.items():
        model_records = [row for row in records if row["model"] == name]
        selections = [("overall", "all", None, np.ones(dev.height, bool))]
        selections += [("fold", str(f), f, outer == f) for f in range(5)]
        selections += [(scope, label, None, mask) for scope, label, mask in strata(dev)]
        for scope, label, fold, mask in selections:
            row = {
                "model": name,
                "scope": scope,
                "stratum": label,
                "fold": fold,
                "artists": len(set(artists[mask].tolist())),
                "small_group_n_lt30": int(mask.sum()) < 30,
                **metrics(y[mask], values[mask]),
            }
            if scope not in {"overall", "fold"}:
                row["r2"] = None
            chosen = (
                model_records
                if scope == "overall"
                else [r for r in model_records if r["outer_fold"] == fold]
                if scope == "fold"
                else []
            )
            for key in (
                "total_wall_seconds",
                "preprocessing_seconds",
                "tuning_wall_seconds",
                "inner_fit_task_seconds",
                "outer_fit_seconds",
                "outer_prediction_seconds",
                "warning_count",
                "failed_configurations",
            ):
                row[key] = sum(r[key] for r in chosen) if chosen else None
            result.append(row)
    return result


def comparisons(dev, folds, predictions):
    y, outer = dev[TARGET].to_numpy(), folds["outer_fold"].to_numpy()
    result = []
    for family in FAMILIES:
        for block in BLOCKS:
            name, reference = f"{family}__{block}", f"elastic_net__{block}"
            result.append(
                compare(
                    y,
                    predictions[name],
                    predictions[reference],
                    outer,
                    kind="algorithm_vs_v05",
                    name=name,
                    reference_name=reference,
                )
            )
        for block in BLOCKS[1:]:
            name, reference = f"{family}__{block}", f"{family}__baseline"
            result.append(
                compare(
                    y,
                    predictions[name],
                    predictions[reference],
                    outer,
                    kind="lyrics_within_family",
                    name=name,
                    reference_name=reference,
                )
            )
    return result


def fmt(value, places=4):
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "sim" if value else "não"
    if isinstance(value, float):
        return f"{value:.{places}f}"
    return str(value)


def table(headers, rows):
    headers = [h.replace("|", "\\|") for h in headers]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def deliver(dev, folds, refs, new_predictions, records, seal, preservation, verification=None):
    predictions = {
        name: refs[f"prediction__{name}"].to_numpy() for name in REFERENCE_NAMES
    } | new_predictions
    rows, comp = metric_rows(dev, folds, predictions, records), comparisons(dev, folds, predictions)
    metrics_path = Path("reports/revisao_estatistica_metricas_v0_8.csv")
    comparisons_path = Path("reports/revisao_estatistica_comparacoes_v0_8.csv")
    pl.DataFrame(rows, infer_schema_length=None).write_csv(output_path(metrics_path))
    pl.DataFrame(comp, infer_schema_length=None).write_csv(output_path(comparisons_path))
    technical, execution = read_json(PRIVATE / "benchmark.json"), read_json(PRIVATE / "run.json")
    loss_counts = {
        block: dict(
            Counter(
                r["selected_params"]["loss"]
                for r in records
                if r["family"] == "hist_gb" and r["block"] == block
            )
        )
        for block in BLOCKS
    }
    summary = {
        "version": "v0.8",
        "status": "complete_verified" if verification else "complete_pending_verification",
        "completed_at": now(),
        "exploratory_post_holdout_motivation": True,
        "holdout_loaded": False,
        "new_targets_loaded": False,
        "demonstrator_changed": False,
        "scientific_authority": "pedido específico V0.8; proposta antiga V0.7 não utilizada",
        "rows": dev.height,
        "artists": dev["artist_group_id"].n_unique(),
        "protocol_sha256": seal["protocol_sha256"],
        "seal_id": seal["seal_id"],
        "sealed_at": seal["created_before_fitting_at"],
        "input_sha256": seal["inputs_sha256"],
        "code_sha256": seal["code_sha256"],
        "versions": seal["versions"],
        "seed": seal["seed"],
        "grids": seal["grids"],
        "features": seal["features"],
        "estimator_defaults": seal["estimator_defaults"],
        "technical_benchmark": technical,
        "fold_audit": seal["fold_audit"],
        "reference_reproduction": seal["reference_reproduction"],
        "metrics": rows,
        "comparisons": comp,
        "selected_models": records,
        "boosting_loss_selection_counts": loss_counts,
        "inner_fit_attempts": sum(r["inner_fit_attempts"] for r in records),
        "outer_fit_attempts": sum(r["outer_fit_attempts"] for r in records),
        "total_warning_count": sum(r["warning_count"] for r in records),
        "failed_configurations": sum(r["failed_configurations"] for r in records),
        "total_fold_wall_seconds": sum(r["total_wall_seconds"] for r in records),
        "run_wall_seconds_this_invocation": execution["wall_seconds_this_invocation"],
        "oof_sha256": execution["oof_sha256"],
        "preservation": preservation,
        "verification": verification,
        "confidence_intervals_computed": False,
        "limitations": [
            "Exploratória pós-abertura: OOF não restaura independência do holdout já consultado historicamente.",
            "Coorte selecionada por matching, amostragem e disponibilidade/aceite de letras; não representa todo o Spotify.",
            "Alvo do snapshot é da gravação representante, não sucesso futuro nem popularidade universal da composição.",
            "Suporte escasso de alta popularidade; nenhum desenvolvimento acima de 80; trocar algoritmo não amplia cobertura.",
            "Year/genre/flags preservam limitações semânticas da fonte; chaves operacionais não certificam obra ou versão.",
            "PCA90 preservada permite comparação controlada, mas não testa todas as representações possíveis.",
            "Sem intervalos/p-valores nesta rodada; regra de 2% é operacional, não confirmação estatística.",
        ],
        "artifact_sha256": {
            metrics_path.as_posix(): digest(metrics_path),
            comparisons_path.as_posix(): digest(comparisons_path),
        },
        "verification_commands": [],
    }
    previous = ROOT / "reports/run_summary_revisao_v0_8.json"
    if previous.is_file():
        summary["verification_commands"] = read_json(previous)["verification_commands"]
    write_json(Path("reports/run_summary_revisao_v0_8.json"), summary)
    overall = [r for r in rows if r["scope"] == "overall"]
    sections = [
        "# Revisão estatística exploratória — V0.8",
        "Rodada motivada pelo diagnóstico posterior ao teste V0.6. Não é confirmação independente. Foram usados exclusivamente 7.648 representantes do desenvolvimento, 3.749 grupos de artista e as mesmas atribuições dos cinco folds externos e três internos por treino. Nenhum holdout, previsão individual do holdout ou novo alvo foi carregado. A proposta científica antiga não foi usada.",
        "## Protocolo e execução",
        f"Protocolo selado antes do teste técnico em {seal['created_before_fitting_at']}. SHA-256: `{seal['protocol_sha256']}`. Código, manifesto, três entradas e versões selados. OOF Elastic Net/Dummy reproduzidas globalmente e nos folds, com tolerância absoluta 1e-10 e relativa zero. Nenhum modelo V0.5 foi ajustado novamente. As fábricas de transformações criam objetos novos em cada treino; as PCAs permanecem separadas e explicam pelo menos 90% da variância de cada bloco no respectivo treino.",
        "Spline altera somente year. Boosting recebe one-hot denso explícito, sem categorias nativas e sem informação nova. Seleção exclusivamente por MAE interno médio; os hiperparâmetros selecionados variam entre folds e não definem um novo modelo de produção. Não houve refit no desenvolvimento completo, clipping, calibração, pesos pelo alvo ou seleção de exemplos.",
        f"Execução: {summary['inner_fit_attempts']} tentativas internas e {summary['outer_fit_attempts']} externas; {summary['failed_configurations']} configurações malsucedidas; {summary['total_warning_count']} warnings. Tempo somado dos 40 folds: {summary['total_fold_wall_seconds'] / 60:.2f} minutos. Tempo desta invocação, incluindo montagem das previsões: {execution['wall_seconds_this_invocation'] / 60:.2f} minutos. Teste técnico adicional: três ajustes, sem selecionar por desempenho. Detalhes de tempo e todas as ocorrências estão no JSON; tarefas paralelas não somam tempo de parede.",
        "## Métricas OOF globais",
        "Erros em pontos da popularidade registrada; proporções nas tabelas abaixo são percentuais. MAE não representa intervalo individual nem porcentagem de acerto.",
        table(
            [
                "Pipeline",
                "MAE",
                "RMSE",
                "R²",
                "Mediana |e|",
                "P90",
                "P95",
                "≤5 %",
                "≤10 %",
                "≤20 %",
                ">20 %",
                "n >20",
            ],
            [
                [
                    r["model"],
                    r["mae"],
                    r["rmse"],
                    r["r2"],
                    r["median_abs_error"],
                    r["p90_abs_error"],
                    r["p95_abs_error"],
                    100 * r["prop_abs_le5"],
                    100 * r["prop_abs_le10"],
                    100 * r["prop_abs_le20"],
                    100 * r["prop_abs_gt20"],
                    r["n_abs_gt20"],
                ]
                for r in overall
            ],
        ),
        "## Comparações de algoritmo contra Elastic Net V0.5 correspondente",
        "Redução de MAE positiva indica melhora. ΔRMSE, ΔP95 e Δ proporção >20 positivos indicam piora. Promissor exige ≥2% de redução do MAE, melhora em ≥4/5 folds e não piorar RMSE/P95 em mais de 2%. O limiar é operacional, não universal.",
        table(
            [
                "Modelo",
                "Redução MAE %",
                "Folds melhores",
                "ΔRMSE %",
                "ΔP95 %",
                "Δ >20 (p.p.)",
                "Promissor",
            ],
            [
                [
                    r["model"],
                    r["mae_reduction_percent"],
                    r["folds_mae_improved"],
                    r["rmse_change_percent"],
                    r["p95_change_percent"],
                    100 * r["delta_prop_abs_gt20"],
                    r["candidate_promising"],
                ]
                for r in comp
                if r["comparison_kind"] == "algorithm_vs_v05"
            ],
        ),
        "## Contribuição incremental das letras dentro de cada família",
        "Cada comparação usa o Baseline da própria família, não o Elastic Net antigo. Ganho por trocar algoritmo não demonstra ganho das letras.",
        table(
            [
                "Modelo",
                "Baseline de referência",
                "Redução MAE %",
                "Folds melhores",
                "ΔRMSE %",
                "ΔP95 %",
                "Δ >20 (p.p.)",
            ],
            [
                [
                    r["model"],
                    r["reference"],
                    r["mae_reduction_percent"],
                    r["folds_mae_improved"],
                    r["rmse_change_percent"],
                    r["p95_change_percent"],
                    100 * r["delta_prop_abs_gt20"],
                ]
                for r in comp
                if r["comparison_kind"] == "lyrics_within_family"
            ],
        ),
        "## Trade-offs de cauda",
    ]
    tradeoffs = [
        r
        for r in comp
        if r["new_mae"] < r["reference_mae"]
        and (r["delta_rmse"] > 0 or r["delta_p95_abs_error"] > 0 or r["delta_prop_abs_gt20"] > 0)
    ]
    sections.append(
        "\n".join(
            f"- {r['model']} versus {r['reference']}: ΔMAE={r['delta_mae']:.6f}; ΔRMSE={r['delta_rmse']:.6f}; ΔP95={r['delta_p95_abs_error']:.6f}; Δ>20={100 * r['delta_prop_abs_gt20']:.4f} p.p."
            for r in tradeoffs
        )
        or "Nenhuma comparação com redução de MAE piorou RMSE, P95 ou proporção de erros >20."
    )
    sections += [
        "## Perdas selecionadas no boosting",
        table(
            ["Bloco", "squared_error (folds)", "absolute_error (folds)"],
            [
                [b, loss_counts[b].get("squared_error", 0), loss_counts[b].get("absolute_error", 0)]
                for b in BLOCKS
            ],
        ),
        "A perda foi escolhida apenas pelos três MAEs internos. Não se escolheu uma perda global pelo resultado OOF externo.",
        "## Resultados e hiperparâmetros por fold",
        table(
            ["Modelo", "Fold", "n", "MAE", "RMSE", "R²", "P95", ">20 %"],
            [
                [
                    r["model"],
                    r["fold"],
                    r["n"],
                    r["mae"],
                    r["rmse"],
                    r["r2"],
                    r["p95_abs_error"],
                    100 * r["prop_abs_gt20"],
                ]
                for r in rows
                if r["scope"] == "fold"
            ],
        ),
        table(
            [
                "Modelo",
                "Fold",
                "Parâmetros selecionados",
                "MAE interno",
                "PCA LFM/MiniLM",
                "Tempo fold s",
                "Warnings",
            ],
            [
                [
                    r["model"],
                    r["outer_fold"],
                    str(r["selected_params"]),
                    r["selected_inner_mae"],
                    str(r["pca_components"]),
                    r["total_wall_seconds"],
                    r["warning_count"],
                ]
                for r in records
            ],
        ),
        "## Estratos descritivos",
        "Faixas, períodos e flags foram predefinidos. n<30 marcado como grupo pequeno; n=0 também é mostrado. Não se calcula R² dentro dos estratos. Todas as métricas dos 13 modelos e de cada estrato estão no CSV; aqui são apresentados os oito novos pipelines. Nenhum estrato orientou tuning. Flags individuais sobrepõem-se; suas contagens não devem ser somadas. Year descreve o campo da fonte, não ano original certificado.",
    ]
    for scope, title in [
        ("target_band", "Faixas do alvo"),
        ("year_period", "Período"),
        ("version_flag", "Flags de versão"),
    ]:
        sections += [
            f"### {title}",
            table(
                ["Estrato", "Modelo", "n", "Artistas", "n<30", "MAE", "RMSE", "P95", ">20 %"],
                [
                    [
                        r["stratum"],
                        r["model"],
                        r["n"],
                        r["artists"],
                        r["small_group_n_lt30"],
                        r["mae"],
                        r["rmse"],
                        r["p95_abs_error"],
                        None if r["prop_abs_gt20"] is None else 100 * r["prop_abs_gt20"],
                    ]
                    for r in rows
                    if r["scope"] == scope and r["model"] in new_predictions
                ],
            ),
        ]
    promising = [r["model"] for r in comp if r["candidate_promising"]]
    sections += [
        "## Interpretação e limites",
        f"Candidatos que satisfazem a regra operacional contra a referência V0.5 correspondente: {', '.join(promising) if promising else 'nenhum'}. Isso autoriza discutir uma avaliação futura independente, não alterar o estudo encerrado ou reutilizar seu holdout como confirmação. O demonstrador continua com os modelos congelados e Tradicional predefinido.",
        "Não foram calculados intervalos ou p-valores. Os resultados OOF continuam exploratórios, pois a motivação veio após o diagnóstico do holdout. As análises são associativas/preditivas, sem causalidade.",
        "O diagnóstico V0.7 documenta 9,6363% de matching aceito na fonte Spotify e disponibilidade/aceite de letras não uniforme; esses denominadores são contexto histórico, não dados recarregados nesta rodada. Mudar o estimador não recupera faixas sem match, letras indisponíveis, gêneros/idiomas sub-representados, múltiplas versões ambíguas ou falhas semânticas de year/genre/flags. O alvo é um snapshot da faixa representante, não sucesso comercial futuro. O desenvolvimento continua sem valores acima de 80 e com poucos casos de alta popularidade. Não há garantia de desempenho fora deste suporte.",
        "## Integridade, privacidade e reprodução",
        f"Preservados por SHA-256: {preservation['old_hashes_verified']} arquivos preexistentes públicos/pessoais, modelos V0.5 e entradas autorizadas. Preservados por tamanho/mtime_ns: {preservation['old_data_metadata_verified']} arquivos de dados antigos; não foram abertos holdout/letras para essa auditoria. SHA-256 e metadados são verificações distintas. HEAD e stage inalterados; zero dados/modelos privados rastreados. Todas as escritas ficam nas saídas novas V0.8. Nenhuma alteração no demonstrador, dados, matching, flags, splits, embeddings, modelos ou resultados V0.5–V0.7.",
        (
            f"Verificação real concluída: 40 pipelines carregados dos checkpoints reproduzem suas OOF com diferença máxima {max(r['maximum_absolute_difference'] for r in verification['pipeline_prediction_checks']):.3g}, tolerância absoluta 1e-10. Cobertura 7.648×8 completa, finita e única; alinhamento, inputs sem alvo, índices de cada transformação e ausência de sobreposição de artistas/composições conferidos."
            if verification
            else "Verificação independente dos checkpoints pendente; consultar status no run summary."
        ),
        "CLI no ambiente existente (nenhuma dependência nova):\n\n```powershell\n.\\.venv\\Scripts\\python.exe -X utf8 -m tcc_music_popularity.statistical_revision_v080 prepare\n.\\.venv\\Scripts\\python.exe -X utf8 -m tcc_music_popularity.statistical_revision_v080 benchmark\n.\\.venv\\Scripts\\python.exe -X utf8 -m tcc_music_popularity.statistical_revision_v080 run\n.\\.venv\\Scripts\\python.exe -X utf8 -m tcc_music_popularity.statistical_revision_v080 verify\n```\n\nPrepare/benchmark recusam sobrescrever uma execução existente; em retomada, executar somente run após verificar o selo. Não apagar checkpoints antigos. Predições e 40 modelos estão no diretório privado V0.8. Relatórios contêm somente agregados; CSVs continuam ignorados pela regra preexistente. Comandos de teste/lint e seus códigos de saída são registrados no run summary na entrega.",
    ]
    output_path(Path("reports/revisao_estatistica_v0_8.md")).write_text(
        "\n\n".join(sections) + "\n", encoding="utf-8"
    )
