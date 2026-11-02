"""Auditoria das previsões e diagnósticos descritivos; sem novos ajustes ou IC."""

import argparse
import time
from pathlib import Path

import numpy as np
import polars as pl

from . import observed_regression as reg
from .manual_lyrics import atomic_frame, atomic_json, exclusive, fingerprint, require

ROOT = reg.ROOT
WORKSPACE = ROOT / "data/derived/private_results_diagnostics_200k_v1"
OUTPUT = ROOT / "reports/diagnosticos_modelagem_200k_v1"
PROTOCOL = ROOT / "docs/protocolo_diagnosticos_modelagem_200k_v1.md"
MODELS = (*reg.BLOCKS, *reg.REFERENCES)
PAIRS = (
    ("traditional", "baseline"),
    ("deep", "baseline"),
    ("combined", "baseline"),
    ("combined", "traditional"),
    ("combined", "deep"),
)
DIMENSIONS = (
    "lyrics_language_status",
    "lyrics_detected_language",
    "sampling_popularity_band",
    "sampling_period",
    "model_genre",
    "evaluation_component_history_status",
)
HISTORY = (
    "readiness_v06_evaluated_track",
    "readiness_v06_composition_collision",
    "readiness_v06_artist_collision",
)
UNKNOWN_HISTORY = "readiness_unknown_group"


def compare_metrics(frame, published):
    require(
        published.height == len(MODELS) and set(published["model"]) == set(MODELS),
        "Variantes das métricas públicas incompatíveis.",
    )
    recomputed = []
    for model in MODELS:
        row = {
            "model": model,
            **reg.metrics(
                frame[reg.data.TARGET], frame["prediction_" + model], frame["sampling_weight"]
            ),
        }
        source = published.filter(pl.col("model") == model).row(0, named=True)
        for key, value in row.items():
            if key == "model":
                continue
            require(
                (value is None and source[key] is None)
                or (
                    value is not None
                    and source[key] is not None
                    and abs(value - source[key]) <= 1e-9
                ),
                "Métrica pública não reproduzida.",
            )
        recomputed.append(row)
    return recomputed


def part_audit(frame, directory, signature, published_alphas):
    selections, total = [], 0
    for outer in range(5):
        valid = frame.filter(pl.col("outer_fold") == outer).sort("track_id")
        train = frame.filter(pl.col("outer_fold") != outer)
        for model in MODELS:
            stored = reg.read_part(directory, signature, outer, model, valid)
            require(stored is not None, "Parte externa ausente.")
            record, predicted = stored
            require(
                record["details"]["train_rows"] == train.height
                and record["details"]["valid_rows"] == valid.height,
                "Contagem de treino/avaliação da parte divergiu.",
            )
            require(
                np.array_equal(
                    predicted["prediction"].to_numpy(), valid["prediction_" + model].to_numpy()
                ),
                "Previsões globais divergem das partes externas.",
            )
            if model in reg.BLOCKS:
                alpha = record["details"]["selected_alpha"]
                require(alpha in reg.ALPHAS, "Alpha externo fora da grade congelada.")
                selections.append({"outer_fold": outer, "block": model, "alpha": float(alpha)})
            else:
                y = train[reg.data.TARGET].to_numpy()
                reference = np.mean(y) if model == "mean" else np.median(y)
                require(
                    np.allclose(predicted["prediction"].to_numpy(), reference, atol=1e-10, rtol=0),
                    "Referência não corresponde à resposta do treino externo.",
                )
            total += 1
    selected = pl.DataFrame(selections)
    require(
        selected.sort("outer_fold", "block").equals(
            published_alphas.select(selected.columns)
            .with_columns(pl.col("alpha").cast(pl.Float64))
            .sort("outer_fold", "block")
        ),
        "Alphas publicados divergem das partes seladas.",
    )
    return total, int(selected["alpha"].is_in([min(reg.ALPHAS), max(reg.ALPHAS)]).sum())


def component_losses(frame):
    result = (
        frame.group_by("text_component_id")
        .agg(
            pl.col("outer_fold").first(),
            pl.len().alias("n"),
            pl.col("sampling_weight").sum().alias("weight_sum"),
            *[
                (pl.col(reg.data.TARGET) - pl.col("prediction_" + model))
                .abs()
                .sum()
                .alias("abs_" + model)
                for model in MODELS
            ],
            *[
                (
                    (pl.col(reg.data.TARGET) - pl.col("prediction_" + model)).abs()
                    * pl.col("sampling_weight")
                )
                .sum()
                .alias("weighted_abs_" + model)
                for model in MODELS
            ],
        )
        .sort("text_component_id")
    )
    return result


def deletion_diagnostics(components):
    """Remove cada componente da avaliação; mantém modelos/previsões fixos."""
    n, weight = components["n"].to_numpy(), components["weight_sum"].to_numpy()
    require(
        len(n) > 1 and (np.sum(n) > n).all() and (np.sum(weight) > weight).all(),
        "Componentes insuficientes para diagnóstico de remoção.",
    )
    rows = []
    for block, reference in PAIRS:
        delta = components["abs_" + block].to_numpy() - components["abs_" + reference].to_numpy()
        weighted = (
            components["weighted_abs_" + block].to_numpy()
            - components["weighted_abs_" + reference].to_numpy()
        )
        removed = (np.sum(delta) - delta) / (np.sum(n) - n)
        weighted_removed = (np.sum(weighted) - weighted) / (np.sum(weight) - weight)
        rows.append(
            {
                "block": block,
                "reference": reference,
                "delta_mae": float(np.sum(delta) / np.sum(n)),
                "min_delta_after_component_deletion": float(np.min(removed)),
                "max_delta_after_component_deletion": float(np.max(removed)),
                "delta_mae_original_weight": float(np.sum(weighted) / np.sum(weight)),
                "min_weighted_delta_after_component_deletion": float(np.min(weighted_removed)),
                "max_weighted_delta_after_component_deletion": float(np.max(weighted_removed)),
                "conditional_on_fixed_predictions": True,
            }
        )
    return rows


def subgroup_metrics(frame, min_rows=100, min_components=20):
    rows, withheld = [], []
    dimensions = ("outer_fold", *DIMENSIONS)
    for name in dimensions:
        levels = frame[name].cast(pl.String).fill_null("__MISSING__")
        for level in sorted(levels.unique().to_list()):
            cell = frame.filter(levels == level)
            counts = {
                "dimension": name,
                "level": level,
                "n": cell.height,
                "components": cell["text_component_id"].n_unique(),
            }
            if name != "outer_fold" and (
                counts["n"] < min_rows or counts["components"] < min_components
            ):
                withheld.append({**counts, "reason": "n_below_100_or_components_below_20"})
                continue
            for model in MODELS:
                rows.append(
                    {
                        **counts,
                        "model": model,
                        **reg.metrics(
                            cell[reg.data.TARGET],
                            cell["prediction_" + model],
                            cell["sampling_weight"],
                        ),
                    }
                )
    return rows, withheld


def run(
    *,
    base_workspace=reg.data.WORKSPACE,
    base_report=reg.data.OUTPUT / "resumo_base_modelagem.json",
    regression_workspace=reg.WORKSPACE / "integral",
    regression_output=reg.OUTPUT / "integral",
    workspace=WORKSPACE,
    output=OUTPUT,
    expected=77535,
):
    started = time.monotonic()
    workspace, output = workspace.resolve(), output.resolve()
    require(
        workspace.is_relative_to(ROOT / "data/derived") or expected != 77535,
        "Workspace privado inválido.",
    )
    require(
        not workspace.is_relative_to(output) and not output.is_relative_to(workspace),
        "Separar saídas públicas/privadas.",
    )
    report_path = regression_output / "resumo_modelagem.json"
    cohort_path = base_workspace / "coorte_modelagem.parquet"
    fold_path = base_workspace / "folds_5x3.parquet"
    prediction_path = regression_workspace / "predicoes_externas.parquet"
    paths = [
        report_path,
        cohort_path,
        fold_path,
        prediction_path,
        base_report,
        *[
            regression_output / name
            for name in (
                "metricas_externas.csv",
                "incrementos_pareados.csv",
                "alphas_selecionados.csv",
            )
        ],
    ]
    require(
        all(
            not p.resolve().is_relative_to(workspace) and not p.resolve().is_relative_to(output)
            for p in paths
        ),
        "Saídas sobrepõem fontes.",
    )
    print("[1/5] Conferindo conclusão, fontes e protocolo; sem treino ou encoder...", flush=True)
    report = reg.data.read_json(report_path)
    base = reg.data.read_json(base_report)
    require(
        base["completed"]
        and base["cohort_rows"] == expected
        and reg.data.embeddings.base.sha256(Path(reg.data.__file__)) == base["seal"]["code"]
        and reg.data.embeddings.base.sha256(reg.data.PROTOCOL) == base["seal"]["protocol"],
        "Base ou código/protocolo dos folds incompatíveis.",
    )
    require(
        report["completed"]
        and report["mode"] == "all"
        and report["global_metrics_available"]
        and report["completed_outer_blocks"] == 20
        and report["pending_outer_blocks"] == 0
        and report["prediction_rows"] == report["source_rows"] == expected,
        "Modelagem integral incompleta.",
    )
    require(fingerprint(report["seal"]) == report["signature"], "Assinatura do resultado divergiu.")
    for name, digest in report["seal"]["code"].items():
        require(
            reg.data.embeddings.base.sha256(Path(reg.__file__).with_name(name)) == digest,
            "Código da modelagem mudou; preservar versão selada.",
        )
    require(
        reg.data.embeddings.base.sha256(reg.PROTOCOL) == report["seal"]["protocol"],
        "Protocolo da modelagem mudou.",
    )
    hashes = {str(p.resolve()): reg.data.embeddings.base.sha256(p) for p in paths}
    for p in (cohort_path, fold_path, base_report):
        require(
            hashes[str(p.resolve())] == report["seal"]["inputs"].get(str(p.resolve())),
            "Fontes de base/folds mudaram.",
        )
    require(
        hashes[str(prediction_path.resolve())] == report["predictions_sha256"],
        "Arquivo global de previsões mudou.",
    )
    seal = {
        "version": "observed-results-diagnostics-v1",
        "inputs": hashes,
        "regression_signature": report["signature"],
        "code": reg.data.embeddings.base.sha256(Path(__file__)),
        "protocol": reg.data.embeddings.base.sha256(PROTOCOL),
        "runtime": {"polars": pl.__version__, "numpy": np.__version__},
    }
    owner = {"seal": fingerprint(seal)}
    with exclusive(workspace):
        for folder in (workspace, output):
            if (folder / "owner.json").exists():
                require(
                    reg.data.read_json(folder / "owner.json") == owner,
                    "Saída incompatível; preservada.",
                )
            else:
                require(
                    not any(p.name != "execution.lock" for p in folder.iterdir())
                    if folder.exists()
                    else True,
                    "Diretório sem proprietário; preservado.",
                )
                folder.mkdir(parents=True, exist_ok=True)
                atomic_json(folder / "owner.json", owner)
        summary = {
            "completed": False,
            "seal": seal,
            "models_trained": False,
            "confidence_intervals_computed": False,
            "predictions_recomputed": False,
        }
        atomic_json(output / "resumo_diagnosticos.json", summary)
        try:
            frame = pl.read_parquet(prediction_path).sort("track_id")
            require(
                frame.height == frame["track_id"].n_unique() == expected,
                "Previsões não cobrem uma linha por faixa.",
            )
            projection = [
                "track_id",
                "text_component_id",
                reg.data.TARGET,
                "sampling_weight",
                *DIMENSIONS[:-1],
                *HISTORY,
                UNKNOWN_HISTORY,
            ]
            metadata = pl.read_parquet(cohort_path, columns=projection).sort("track_id")
            require(
                all(
                    metadata[c].dtype == pl.Boolean and metadata[c].null_count() == 0
                    for c in (*HISTORY, UNKNOWN_HISTORY)
                ),
                "Flags históricas ausentes/indeterminadas; não tratar como ausência de colisão.",
            )
            folds = pl.read_parquet(fold_path).sort("track_id")
            reg.data.audit_folds(folds)
            common = ["track_id", "text_component_id", reg.data.TARGET, "sampling_weight"]
            require(
                frame.select(common).equals(metadata.select(common))
                and frame.select("track_id", "text_component_id", "outer_fold").equals(
                    folds.select("track_id", "text_component_id", "outer_fold")
                ),
                "IDs/grupos/alvos/pesos/folds das previsões divergem da base.",
            )
            print("[2/5] Conferindo as 30 partes e reproduzindo métricas globais...", flush=True)
            published = pl.read_csv(regression_output / "metricas_externas.csv")
            metrics = compare_metrics(frame, published)
            parts, boundary = part_audit(
                frame,
                regression_workspace / "parts",
                report["signature"],
                pl.read_csv(regression_output / "alphas_selecionados.csv"),
            )
            for model in MODELS:
                frame = frame.with_columns(
                    (pl.col(reg.data.TARGET) - pl.col("prediction_" + model))
                    .abs()
                    .alias("abs_" + model)
                )
            print("[3/5] Resumindo perdas por componente; sem reamostragem ou refit...", flush=True)
            components = component_losses(frame)
            deletion = deletion_diagnostics(components)
            contrasts = pl.read_csv(regression_output / "incrementos_pareados.csv")
            require(contrasts.height == len(PAIRS), "Número de contrastes publicados divergiu.")
            for row in deletion:
                original = contrasts.filter(
                    (pl.col("block") == row["block"]) & (pl.col("reference") == row["reference"])
                )
                require(original.height == 1, "Contraste ausente/repetido.")
                for c in ("delta_mae", "delta_mae_original_weight"):
                    require(
                        abs(original[c][0] - row[c]) <= 1e-9, "Contraste publicado não reproduzido."
                    )
            frame = frame.join(
                metadata.select("track_id", *DIMENSIONS[:-1], *HISTORY, UNKNOWN_HISTORY),
                on="track_id",
                validate="1:1",
                maintain_order="left",
            )
            frame = frame.with_columns(
                pl.any_horizontal([pl.col(c) for c in HISTORY]).alias("_row_history_any")
            )
            exposure = frame.group_by("text_component_id").agg(
                pl.col("_row_history_any").any().alias("_component_collision"),
                pl.col(UNKNOWN_HISTORY).any().alias("_component_unknown"),
            )
            exposure = exposure.with_columns(
                pl.when(pl.col("_component_collision"))
                .then(pl.lit("detected_collision"))
                .when(pl.col("_component_unknown"))
                .then(pl.lit("unknown_key"))
                .otherwise(pl.lit("no_detected_collision"))
                .alias(DIMENSIONS[-1])
            ).select("text_component_id", DIMENSIONS[-1])
            frame = frame.join(
                exposure, on="text_component_id", validate="m:1", maintain_order="left"
            )
            print(
                "[4/5] Diagnósticos descritivos por fold/idioma/metadados/exposição...", flush=True
            )
            subgroup, small = subgroup_metrics(frame)
            bounds = [
                {
                    "model": model,
                    "below_zero": int((frame["prediction_" + model] < 0).sum()),
                    "above_100": int((frame["prediction_" + model] > 100).sum()),
                    "min_prediction": float(frame["prediction_" + model].min()),
                    "max_prediction": float(frame["prediction_" + model].max()),
                }
                for model in MODELS
            ]
            require(
                all(reg.data.embeddings.base.sha256(p) == hashes[str(p.resolve())] for p in paths),
                "Uma fonte mudou durante os diagnósticos.",
            )
            atomic_frame(workspace / "perdas_componentes.parquet", components)
            reg.data.write_csv(output / "metricas_reproduzidas.csv", metrics)
            reg.data.write_csv(output / "diagnosticos_subgrupos.csv", subgroup)
            reg.data.write_csv(output / "sensibilidade_remocao_componente.csv", deletion)
            reg.data.write_csv(output / "previsoes_fora_intervalo.csv", bounds)
            if small:
                reg.data.write_csv(output / "celulas_pequenas.csv", small)
            summary.update(
                completed=True,
                cohort_rows=expected,
                models=len(MODELS),
                verified_parts=parts,
                components=components.height,
                folds_verified=True,
                metrics_reproduced=True,
                published_cells=len(subgroup) // len(MODELS),
                withheld_cells=len(small),
                alpha_boundary_selections=boundary,
                component_losses_sha256=reg.data.embeddings.base.sha256(
                    workspace / "perdas_componentes.parquet"
                ),
                seconds=time.monotonic() - started,
            )
            (output / "relatorio_diagnosticos.md").write_text(
                "# Diagnósticos das previsões externas fixas\n\n"
                + f"{expected} faixas, {parts} partes, métricas/contrastes reproduzidos; "
                + f"{components.height} componentes. Nenhum modelo ajustado.\n\n"
                + "Subgrupos são exploratórios/descritivos; células com menos de 100 faixas "
                + "ou 20 componentes omitem métricas públicas, sem excluir observações da análise principal. "
                + "Idiomas são estimados e colisões históricas não restauram independência.\n\n"
                + "Remover um componente da avaliação mantém previsões/modelos fixos: "
                + "não é leave-one-group-out com retreino, intervalo de confiança ou teste. "
                + "Dependência dos ajustes da CV e incerteza do treinamento não são resolvidas aqui.\n\n"
                + f"{boundary}/20 escolhas de alpha nos extremos da grade são diagnóstico de resolução; "
                + "não autoriza expandir grade após ver teste. Previsões fora de 0..100 preservadas, sem clipping.\n",
                encoding="utf-8",
            )
            atomic_json(output / "resumo_diagnosticos.json", summary)
            print(f"[5/5] Concluído; sem treino/IC; agregados em {output}", flush=True)
            return 0
        except BaseException as exc:
            summary.update(completed=False, error_type=type(exc).__name__, error=str(exc))
            atomic_json(output / "resumo_diagnosticos.json", summary)
            raise


def cli():
    argparse.ArgumentParser(description=__doc__).parse_args()
    return run()
