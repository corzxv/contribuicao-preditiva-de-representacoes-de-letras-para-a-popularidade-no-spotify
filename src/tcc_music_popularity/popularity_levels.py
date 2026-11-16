"""Diagnósticos de níveis operacionais; reutiliza previsões, sem ajuste ou letras."""

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/niveis_popularidade_200k_v1.json"
PROTOCOL = ROOT / "docs/protocolo_niveis_popularidade_200k_v1.md"
OUTPUT = ROOT / "reports/niveis_popularidade_200k_v1"
PREDICTIONS = ROOT / "data/derived/private_regression_200k_v1/integral/predicoes_externas.parquet"
FOLDS = ROOT / "data/derived/private_modeling_200k_v1/folds_5x3.parquet"
REGRESSION = ROOT / "reports/modelagem_200k_v1/integral/resumo_modelagem.json"
ALLOCATION = ROOT / "reports/amostra_spotify_200k_20261031/alocacao_amostra_200k.csv"
COVERAGE = ROOT / "reports/parecer_letras_v2/cobertura_por_estrato.csv"
FROZEN = ROOT / "reports/publicacao_github_20261102.json"
MODELS = ("baseline", "traditional", "deep", "combined", "mean", "median")
PAIRS = (("combined", "baseline"), ("combined", "deep"))
TARGET = "spotify_popularity"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def write_csv(path, rows):
    require(bool(rows), "Tabela agregada vazia.")
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def config(path=CONFIG):
    result = read_json(path)
    require(result["primary_scheme"] in result["schemes"], "Esquema principal ausente.")
    for cuts in result["schemes"].values():
        require(
            len(cuts) == 2 and 0 < cuts[0] < cuts[1] <= 100,
            "Exigir dois limites ordenados dentro da escala.",
        )
    return result


def categories(values, cuts, *, observed=False):
    values = np.asarray(values, dtype=float)
    require(values.ndim == 1 and np.isfinite(values).all(), "Valores inválidos nos níveis.")
    if observed:
        require(
            ((values >= 0) & (values <= 100) & (values == np.floor(values))).all(),
            "Resposta observada fora do domínio inteiro 0..100.",
        )
    # Intervalos [0,c1), [c1,c2), [c2,100]; previsões não são arredondadas.
    return np.searchsorted(cuts, values, side="right")


def scores(truth, predicted, weights=None):
    truth, predicted = np.asarray(truth), np.asarray(predicted)
    require(
        truth.ndim == 1 and truth.shape == predicted.shape and len(truth) > 0,
        "Observações incompatíveis na classificação.",
    )
    require(
        np.isin(truth, [0, 1, 2]).all() and np.isin(predicted, [0, 1, 2]).all(),
        "Classe fora de 0,1,2.",
    )
    weights = np.ones(len(truth)) if weights is None else np.asarray(weights, dtype=float)
    require(
        weights.shape == truth.shape and np.isfinite(weights).all() and (weights > 0).all(),
        "Pesos de avaliação inválidos.",
    )
    matrix = np.zeros((3, 3), dtype=float)
    np.add.at(matrix, (truth, predicted), weights)
    support, predicted_support = matrix.sum(axis=1), matrix.sum(axis=0)
    recall = np.divide(np.diag(matrix), support, out=np.zeros(3), where=support > 0)
    precision = np.divide(
        np.diag(matrix), predicted_support, out=np.zeros(3), where=predicted_support > 0
    )
    denominator = support + predicted_support
    f1 = np.divide(2 * np.diag(matrix), denominator, out=np.zeros(3), where=denominator > 0)
    present = bool((support > 0).all())
    return (
        {
            "n": len(truth),
            "accuracy": float(np.trace(matrix) / matrix.sum()),
            "balanced_accuracy": float(recall.mean()) if present else None,
            "macro_f1": float(f1.mean()) if present else None,
            "extreme_error_rate": float((matrix[0, 2] + matrix[2, 0]) / matrix.sum()),
            "all_true_classes_present": present,
        },
        matrix,
        precision,
        recall,
    )


def frozen_hashes(root=ROOT):
    published = read_json(root / FROZEN.relative_to(ROOT))
    result = {}
    for name, expected in published["fontes_seladas_preservadas"].items():
        current = digest(root / name)
        require(current == expected, "Fonte científica selada alterada: " + name)
        result[name] = current
    # Preserva também as duas entradas acadêmicas anteriores e seus pacotes locais.
    for name in (
        "reports/modelagem_200k_v1/integral/resumo_modelagem.json",
        "reports/monografia_template_200k_v2/main.tex",
        "reports/monografia_template_200k_v2.zip",
        "output/pdf/monografia_template_200k_v2.pdf",
        "output/pdf/monografia_consolidada_200k_v1.pdf",
    ):
        if (root / name).exists():
            result[name] = digest(root / name)
    return result


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def aggregate_counts(allocation, coverage, settings):
    require(sum(int(r["N_h"]) for r in allocation) == 1159764, "Total do catálogo divergiu.")
    require(sum(int(r["n_h"]) for r in allocation) == 200000, "Total da amostra divergiu.")
    require(sum(int(r["observed_n"]) for r in coverage) == 200000, "Cobertura não reconcilia.")
    require(
        sum(int(r["accepted_n"]) for r in coverage) == settings["expected_tracks"],
        "Contagem aceita divergiu.",
    )
    result = []
    for scheme, cuts in settings["schemes"].items():
        counts = {name: np.zeros(3) for name in ("catalogo", "amostra", "aceitas", "aceitas_pesos")}
        for rows, field, targets in (
            (allocation, "popularity_band", (("catalogo", "N_h"), ("amostra", "n_h"))),
            (
                coverage,
                "sampling_popularity_band",
                (("aceitas", "accepted_n"), ("aceitas_pesos", "accepted_weight")),
            ),
        ):
            for row in rows:
                band = row[field].replace("–", "-").replace("—", "-")
                low, high = map(int, band.split("-"))
                indexes = categories([low, high], cuts, observed=True)
                require(indexes[0] == indexes[1], "Limite corta banda agregada; não interpolar.")
                for target, value in targets:
                    counts[target][indexes[0]] += float(row[value])
        for scope, values in counts.items():
            for index, value in enumerate(values):
                result.append(
                    {
                        "scheme": scheme,
                        "scope": scope,
                        "class_index": index,
                        "label": settings["labels"][index],
                        "count_or_weight": float(value),
                        "fraction": float(value / values.sum()),
                    }
                )
    return result


def validate_frames(predictions, folds, expected):
    predictions, folds = predictions.sort("track_id"), folds.sort("track_id")
    for frame in (predictions, folds):
        require(frame.height == frame["track_id"].n_unique() == expected, "IDs não são 1:1.")
        require(frame["track_id"].null_count() == 0, "ID ausente.")
        require(frame["text_component_id"].null_count() == 0, "Componente ausente.")
        require(
            frame.group_by("text_component_id")
            .agg(pl.col("outer_fold").n_unique())["outer_fold"]
            .max()
            == 1,
            "Componente cruza folds externos.",
        )
    common = ["track_id", "text_component_id", "outer_fold"]
    require(
        predictions.select(common).equals(folds.select(common)), "IDs/grupos/folds desalinhados."
    )
    categories(predictions[TARGET], [20, 40], observed=True)
    weights = predictions["sampling_weight"].to_numpy()
    require(np.isfinite(weights).all() and (weights > 0).all(), "Pesos originais inválidos.")
    require(sorted(folds["outer_fold"].unique().to_list()) == list(range(5)), "Exigir cinco folds.")
    for outer in range(5):
        column = "inner_outer_" + str(outer)
        inside = folds.filter(pl.col("outer_fold") != outer)
        outside = folds.filter(pl.col("outer_fold") == outer)
        require(
            outside[column].to_list() == [-1] * outside.height, "Teste externo entrou no interno."
        )
        require(sorted(inside[column].unique().to_list()) == [0, 1, 2], "Folds internos inválidos.")
        require(
            inside.group_by("text_component_id").agg(pl.col(column).n_unique())[column].max() == 1,
            "Componente cruza folds internos.",
        )
    for model in MODELS:
        categories(predictions["prediction_" + model], [20, 40])
    return predictions, folds


def partition_counts(predictions, folds, settings):
    result = []
    outer_values = folds["outer_fold"].to_numpy()
    for scheme, cuts in settings["schemes"].items():
        labels = categories(predictions[TARGET], cuts, observed=True)
        for outer in range(5):
            internal = folds["inner_outer_" + str(outer)].to_numpy()
            partitions = [
                ("outer_train", -1, outer_values != outer),
                ("outer_test", -1, outer_values == outer),
            ]
            for inner in range(3):
                partitions.extend(
                    [
                        ("inner_train", inner, (outer_values != outer) & (internal != inner)),
                        ("inner_valid", inner, (outer_values != outer) & (internal == inner)),
                    ]
                )
            for role, inner, mask in partitions:
                for index in range(3):
                    cell = predictions.filter(pl.Series(mask & (labels == index)))
                    components = cell["text_component_id"].n_unique()
                    result.append(
                        {
                            "scheme": scheme,
                            "outer_fold": outer,
                            "inner_fold": inner,
                            "partition": role,
                            "class_index": index,
                            "n": cell.height,
                            "components": components,
                            "operational_support": cell.height
                            >= settings["minimum_partition_tracks_per_class"]
                            and components >= settings["minimum_partition_components_per_class"],
                        }
                    )
    return result


def prediction_diagnostics(predictions, settings):
    metrics, confusion, per_class, tails = [], [], [], []
    outer_values = predictions["outer_fold"].to_numpy()
    for scheme, cuts in settings["schemes"].items():
        truth = categories(predictions[TARGET], cuts, observed=True)
        majority = np.empty(len(truth), dtype=int)
        for outer in range(5):
            majority[outer_values == outer] = np.argmax(
                np.bincount(truth[outer_values != outer], minlength=3)
            )
        for model in (*MODELS, "majority_outer_train"):
            predicted = (
                majority
                if model == "majority_outer_train"
                else categories(predictions["prediction_" + model], cuts)
            )
            for outer in (-1, 0, 1, 2, 3, 4):
                mask = np.ones(len(truth), dtype=bool) if outer == -1 else outer_values == outer
                for weighting in ("equal_tracks", "original_weight_sensitivity"):
                    weights = (
                        None
                        if weighting == "equal_tracks"
                        else predictions["sampling_weight"].to_numpy()[mask]
                    )
                    result, matrix, precision, recall = scores(
                        truth[mask], predicted[mask], weights
                    )
                    keys = {
                        "scheme": scheme,
                        "model": model,
                        "outer_fold": outer,
                        "weighting": weighting,
                    }
                    metrics.append({**keys, **result})
                    for observed in range(3):
                        per_class.append(
                            {
                                **keys,
                                "class_index": observed,
                                "precision": float(precision[observed]),
                                "recall": float(recall[observed])
                                if matrix[observed].sum() > 0
                                else None,
                            }
                        )
                        for estimated in range(3):
                            confusion.append(
                                {
                                    **keys,
                                    "observed_class": observed,
                                    "predicted_class": estimated,
                                    "count_or_weight": float(matrix[observed, estimated]),
                                }
                            )
            mask = predictions[TARGET].to_numpy() >= settings["extreme_tail_minimum"]
            tails.append(
                {
                    "scheme": scheme,
                    "model": model,
                    "n_tail": int(mask.sum()),
                    **{
                        "predicted_class_" + str(i): int((predicted[mask] == i).sum())
                        for i in range(3)
                    },
                }
            )
    return metrics, confusion, per_class, tails


def prepare_output(output, seal, sources):
    output = Path(output).resolve()
    require(
        all(not Path(p).resolve().is_relative_to(output) for p in sources), "Saída sobrepõe fonte."
    )
    owner = {"signature": fingerprint(seal)}
    if output.exists() and any(p.name != "execution.lock" for p in output.iterdir()):
        require((output / "owner.json").exists(), "Diretório existente sem selo; preservado.")
        require(read_json(output / "owner.json") == owner, "Saída de outra versão; preservada.")
    output.mkdir(parents=True, exist_ok=True)
    atomic_json(output / "owner.json", owner)


def run(mode, *, output=OUTPUT, root=ROOT):
    started = time.monotonic()
    require(mode in ("agregados", "previsoes"), "Modo inválido.")
    settings = config(root / CONFIG.relative_to(ROOT))
    sources = [root / p.relative_to(ROOT) for p in (CONFIG, PROTOCOL)]
    print("[1/4] Conferindo fontes e preservação da primeira etapa...", flush=True)
    preservation = frozen_hashes(root)
    if mode == "agregados":
        sources.extend(root / p.relative_to(ROOT) for p in (ALLOCATION, COVERAGE))
    else:
        sources.extend(root / p.relative_to(ROOT) for p in (REGRESSION, PREDICTIONS, FOLDS))
        for path in sources[-2:]:
            require(path.stat().st_size <= 16 * 1024**2, "Arquivo excede orçamento do diagnóstico.")
            require(
                pq.ParquetFile(path).metadata.num_rows == settings["expected_tracks"],
                "Footer incompatível.",
            )
    seal = {
        "mode": mode,
        "inputs": {str(p.relative_to(root)): digest(p) for p in sources},
        "code": digest(Path(__file__)),
        "settings": settings,
        "preserved": preservation,
    }
    directory = Path(output) / mode
    # Bloqueio independente, sem abrir os workspaces congelados para escrita.
    from .manual_lyrics import exclusive

    with exclusive(directory):
        prepare_output(directory, seal, sources)
        summary = {
            "completed": False,
            "mode": mode,
            "seal": seal,
            "models_trained": False,
            "lrclib_queries": 0,
            "embeddings_generated": False,
            "catalog_inference": False,
            "classification_models_evaluated": False,
        }
        atomic_json(directory / "resumo_niveis.json", summary)
        if mode == "agregados":
            print("[2/4] Reagrupando somente contagens públicas já existentes...", flush=True)
            counts = aggregate_counts(read_csv(sources[-2]), read_csv(sources[-1]), settings)
            write_csv(directory / "distribuicao_niveis.csv", counts)
            summary.update(
                observed_tracks=settings["expected_tracks"],
                fold_support_checked=False,
                classification_performance_computed=False,
            )
        else:
            report = read_json(sources[-3])
            require(
                report["completed"]
                and report["mode"] == "all"
                and report["prediction_rows"] == settings["expected_tracks"],
                "Regressão incompleta.",
            )
            require(
                fingerprint(report["seal"]) == report["signature"],
                "Assinatura da regressão inválida.",
            )
            require(
                digest(sources[-2]) == report["predictions_sha256"], "Previsões seladas alteradas."
            )
            require(
                digest(sources[-1]) == report["seal"]["inputs"][str(sources[-1].resolve())],
                "Folds selados alterados.",
            )
            print("[2/4] Conferindo IDs, componentes e divisões 5x3 existentes...", flush=True)
            predictions, folds = validate_frames(
                pl.read_parquet(sources[-2]),
                pl.read_parquet(sources[-1]),
                settings["expected_tracks"],
            )
            require(
                predictions["text_component_id"].n_unique() == settings["expected_components"],
                "Total de componentes divergiu.",
            )
            support = partition_counts(predictions, folds, settings)
            write_csv(directory / "suporte_particoes.csv", support)
            print("[3/4] Categorizando previsões existentes; sem novos ajustes...", flush=True)
            metrics, confusion, per_class, tails = prediction_diagnostics(predictions, settings)
            for name, rows in (
                ("metricas_categorizadas", metrics),
                ("matrizes_confusao", confusion),
                ("metricas_por_classe", per_class),
                ("cauda_80", tails),
            ):
                write_csv(directory / (name + ".csv"), rows)
            paired = []
            global_rows = {
                (r["scheme"], r["model"], r["weighting"]): r
                for r in metrics
                if r["outer_fold"] == -1
            }
            for scheme in settings["schemes"]:
                for model, reference in PAIRS:
                    for weighting in ("equal_tracks", "original_weight_sensitivity"):
                        first, second = (
                            global_rows[(scheme, m, weighting)] for m in (model, reference)
                        )
                        paired.append(
                            {
                                "scheme": scheme,
                                "model": model,
                                "reference": reference,
                                "weighting": weighting,
                                **{
                                    "delta_" + metric: first[metric] - second[metric]
                                    if first[metric] is not None and second[metric] is not None
                                    else None
                                    for metric in ("accuracy", "balanced_accuracy", "macro_f1")
                                },
                                "conditional_on_existing_predictions": True,
                            }
                        )
            write_csv(directory / "contrastes_descritivos.csv", paired)
            primary_support = [r for r in support if r["scheme"] == settings["primary_scheme"]]
            summary.update(
                observed_tracks=predictions.height,
                components=predictions["text_component_id"].n_unique(),
                fold_support_checked=True,
                operational_support_all_partitions=all(
                    r["operational_support"] for r in primary_support
                ),
                minimum_primary_class_rows=min(r["n"] for r in primary_support),
                minimum_primary_class_components=min(r["components"] for r in primary_support),
                classification_performance_computed=True,
                inference_scope="exploratory_categorization_of_old_regression_predictions",
            )
        require(frozen_hashes(root) == preservation, "Fonte anterior mudou durante diagnóstico.")
        summary.update(completed=True, seconds=time.monotonic() - started)
        atomic_json(directory / "resumo_niveis.json", summary)
    print("[4/4] Concluído; agregados em " + str(directory), flush=True)
    return summary


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("agregados", "previsoes"))
    args = parser.parse_args()
    run(args.mode)
    return 0
