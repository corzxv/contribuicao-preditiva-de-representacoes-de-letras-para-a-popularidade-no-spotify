import numpy as np
import pytest
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score

from tcc_music_popularity import classification_diagnostics as mod


def test_matriz_reproduz_metricas_sem_ler_observacoes():
    truth = np.array([0, 0, 0, 1, 1, 2, 2])
    predicted = np.array([0, 0, 2, 0, 1, 1, 2])
    matrix = np.zeros((3, 3))
    np.add.at(matrix, (truth, predicted), 1)
    result = mod.from_confusion(matrix)
    assert result["accuracy"] == pytest.approx(accuracy_score(truth, predicted))
    assert result["balanced_accuracy"] == pytest.approx(balanced_accuracy_score(truth, predicted))
    assert result["macro_f1"] == pytest.approx(f1_score(truth, predicted, average="macro"))
    assert result["extreme_error_rate"] == pytest.approx(1 / 7)


def test_divergencia_agregada_interrompe_diagnostico():
    rows = [
        {
            "model": "combined",
            "weighting": "equal_tracks",
            "observed_class": str(i),
            "predicted_class": str(j),
            "count_or_weight": 1,
        }
        for i in range(3)
        for j in range(3)
    ]
    metric = {
        "model": "combined",
        "weighting": "equal_tracks",
        "outer_fold": -1,
        "accuracy": 1,
        "balanced_accuracy": 1,
        "macro_f1": 1,
        "extreme_error_rate": 0,
    }
    with pytest.raises(ValueError, match="diverge"):
        mod.reconcile([metric], rows)


def test_desvio_de_calibracao_pondera_tamanho_de_celula():
    rows = []
    for model in (*mod.model.BLOCKS, mod.model.REFERENCE):
        for cls in range(3):
            for index in range(10):
                rows.append(
                    {
                        "model": model,
                        "class_index": cls,
                        "n": 9 if index == 0 else 1 if index == 1 else 0,
                        "mean_predicted_probability": 0.1
                        if index == 0
                        else 0.8
                        if index == 1
                        else "",
                        "observed_fraction": 0.2 if index == 0 else 0.5 if index == 1 else "",
                    }
                )
    result = mod.calibration_summary(rows)
    assert all(r["weighted_absolute_bin_deviation"] == pytest.approx(0.12) for r in result)
