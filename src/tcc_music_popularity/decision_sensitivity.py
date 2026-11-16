"""Sensibilidade exploratória da regra de decisão, sem ajustar probabilidades/modelos."""

import argparse
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow.parquet as pq

from . import observed_classification as model
from . import popularity_levels as common

ROOT = common.ROOT
SOURCE = model.WORKSPACE / "integral/probabilidades_externas.parquet"
REPORT = model.OUTPUT / "integral/resumo_classificacao.json"
METRICS = model.OUTPUT / "integral/metricas_externas.csv"
OUTPUT = ROOT / "reports/sensibilidade_decisao_ordinal_200k_v1"
PROTOCOL = ROOT / "docs/protocolo_sensibilidade_decisao_ordinal_v1.md"
RULES = ("argmax_original", "inverse_training_prior")


def decisions(probabilities, priors, rule):
    probabilities = model.validate_probabilities(probabilities, len(probabilities))
    common.require(rule in RULES, "Regra desconhecida.")
    if rule == "argmax_original":
        return probabilities.argmax(axis=1)
    priors = np.asarray(priors, dtype=float)
    common.require(
        priors.shape == probabilities.shape
        and np.isfinite(priors).all()
        and (priors > 0).all()
        and np.allclose(priors.sum(axis=1), 1, rtol=0, atol=1e-12),
        "Proporções do treino inválidas.",
    )
    # São escores para decidir, não novas probabilidades na distribuição observada.
    return (probabilities / priors).argmax(axis=1)


def validate_frame(frame, expected=77535, expected_components=21893):
    common.require(frame.height == frame["track_id"].n_unique() == expected, "Faixas não são 1:1.")
    common.require(
        frame["text_component_id"].n_unique() == expected_components, "Componentes incompatíveis."
    )
    common.require(
        frame.group_by("text_component_id").agg(pl.col("outer_fold").n_unique())["outer_fold"].max()
        == 1,
        "Componente cruza folds.",
    )
    folds = frame["outer_fold"].to_numpy()
    common.require(set(folds) == set(range(5)), "Exigir cinco folds externos.")
    y = common.categories(frame[model.regression.data.TARGET], [20, 40], observed=True)
    common.require(
        np.array_equal(y, frame["observed_class"].to_numpy()), "Classe difere dos limites 20/40."
    )
    priors = model.validate_probabilities(
        frame.select(["class_prior_probability_" + str(i) for i in range(3)]).to_numpy(), expected
    )
    for outer in range(5):
        train = y[folds != outer]
        expected_prior = np.bincount(train, minlength=3) / len(train)
        common.require(
            (expected_prior > 0).all()
            and np.allclose(priors[folds == outer], expected_prior, rtol=0, atol=1e-12),
            "Proporções não correspondem exclusivamente ao treino externo.",
        )
    return y, folds, priors


def diagnose(frame, published, expected=77535, expected_components=21893):
    y, folds, priors = validate_frame(frame, expected, expected_components)
    all_metrics, confusion, per_class = [], [], []
    published = {(r["model"], r["weighting"], int(r["outer_fold"])): r for r in published}
    common.require(
        len(published) == (len(model.BLOCKS) + 1) * 2 * 6, "Métricas principais incompletas."
    )
    for name in (*model.BLOCKS, model.REFERENCE):
        probabilities = model.validate_probabilities(
            frame.select([name + "_probability_" + str(i) for i in range(3)]).to_numpy(), expected
        )
        for outer in (-1, 0, 1, 2, 3, 4):
            mask = np.ones(expected, dtype=bool) if outer == -1 else folds == outer
            for weighting in ("equal_tracks", "original_weight_sensitivity"):
                weights = (
                    None
                    if weighting == "equal_tracks"
                    else frame["sampling_weight"].to_numpy()[mask]
                )
                reproduced, _ = model.metrics(y[mask], probabilities[mask], weights)
                source = published[(name, weighting, outer)]
                for metric in (
                    "accuracy",
                    "balanced_accuracy",
                    "macro_f1",
                    "extreme_error_rate",
                    "log_loss",
                    "brier_multiclass",
                ):
                    common.require(
                        abs(reproduced[metric] - float(source[metric])) <= 1e-10,
                        "Métrica principal não reproduzida: " + metric,
                    )
                for rule in RULES:
                    predicted = decisions(probabilities[mask], priors[mask], rule)
                    result, matrix, precision, recall = common.scores(y[mask], predicted, weights)
                    keys = {
                        "model": name,
                        "outer_fold": outer,
                        "weighting": weighting,
                        "decision_rule": rule,
                    }
                    all_metrics.append(
                        {
                            **keys,
                            **result,
                            "log_loss_original_probabilities": reproduced["log_loss"],
                            "brier_original_probabilities": reproduced["brier_multiclass"],
                        }
                    )
                    for truth in range(3):
                        per_class.append(
                            {
                                **keys,
                                "class_index": truth,
                                "precision": float(precision[truth]),
                                "recall": float(recall[truth]),
                            }
                        )
                        for predicted_class in range(3):
                            confusion.append(
                                {
                                    **keys,
                                    "observed_class": truth,
                                    "predicted_class": predicted_class,
                                    "count_or_weight": float(matrix[truth, predicted_class]),
                                }
                            )
    return all_metrics, confusion, per_class


def run():
    from .manual_lyrics import exclusive

    report = common.read_json(REPORT)
    common.require(
        report["completed"]
        and report["global_metrics_available"]
        and report["prediction_rows"] == 77535,
        "Concluir produção antes da sensibilidade.",
    )
    common.require(
        SOURCE.stat().st_size <= 16 * 1024**2 and pq.ParquetFile(SOURCE).metadata.num_rows == 77535,
        "Fonte excede limites do diagnóstico.",
    )
    common.require(
        common.digest(SOURCE) == report["prediction_sha256"], "Probabilidades seladas mudaram."
    )
    sources = [SOURCE, REPORT, METRICS, PROTOCOL]
    seal = {
        "code": common.digest(Path(__file__)),
        "classification_code": common.digest(Path(model.__file__)),
        "inputs": {str(p.relative_to(ROOT)): common.digest(p) for p in sources},
        "rules": RULES,
    }
    preserved = common.frozen_hashes()
    print("[1/3] Conferindo probabilidades e protocolo; sem modelo ou encoder...", flush=True)
    with exclusive(OUTPUT):
        common.prepare_output(OUTPUT, seal, sources)
        summary = {
            "completed": False,
            "seal": seal,
            "models_trained": False,
            "probabilities_changed": False,
            "main_results_replaced": False,
            "hypothesis_tests_computed": False,
            "scope": "exploratory_conditional_on_existing_probabilities",
            "external_labels_used_to_tune_rule": False,
        }
        common.atomic_json(OUTPUT / "resumo_sensibilidade.json", summary)
        frame = pl.read_parquet(SOURCE)
        print("[2/3] Reproduzindo métricas e aplicando duas regras fixas de decisão...", flush=True)
        metrics, confusion, per_class = diagnose(frame, common.read_csv(METRICS))
        for name, rows in (
            ("metricas_regras", metrics),
            ("matrizes_confusao", confusion),
            ("metricas_por_classe", per_class),
        ):
            common.write_csv(OUTPUT / (name + ".csv"), rows)
        common.require(
            all(common.digest(ROOT / p) == h for p, h in seal["inputs"].items()),
            "Fonte mudou durante diagnóstico.",
        )
        common.require(common.frozen_hashes() == preserved, "Resultado anterior mudou.")
        summary.update(
            completed=True,
            observed_tracks=77535,
            components=21893,
            original_metrics_reproduced=True,
        )
        common.atomic_json(OUTPUT / "resumo_sensibilidade.json", summary)
    print("[3/3] Concluído; sensibilidade separada em " + str(OUTPUT), flush=True)
    return summary


def cli():
    argparse.ArgumentParser(description=__doc__).parse_args()
    run()
    return 0
