import numpy as np
import polars as pl
import pytest

from tcc_music_popularity import decision_sensitivity as mod


def test_regra_de_decisao_nao_muda_probabilidades():
    probability = np.array([[0.5, 0.3, 0.2], [0.1, 0.2, 0.7]])
    priors = np.array([[0.7, 0.2, 0.1]] * 2)
    original = probability.copy()
    assert mod.decisions(probability, priors, "argmax_original").tolist() == [0, 2]
    assert mod.decisions(probability, priors, "inverse_training_prior").tolist() == [2, 2]
    assert np.array_equal(probability, original)
    with pytest.raises(ValueError, match="Proporções"):
        mod.decisions(probability, np.array([[1, 0, 0]] * 2), "inverse_training_prior")


def test_prior_usa_somente_treino_e_metricas_principais_sao_reproduzidas():
    groups = np.repeat(np.arange(45), 2)
    y = groups % 3
    folds = groups % 5
    prior = np.empty((90, 3))
    for fold in range(5):
        train = y[folds != fold]
        prior[folds == fold] = np.bincount(train, minlength=3) / len(train)
    probability = np.eye(3)[y] * 0.6 + 0.4 / 3
    values = {
        "track_id": [f"faixa{i}" for i in range(90)],
        "text_component_id": [f"grupo{i}" for i in groups],
        "outer_fold": folds,
        "observed_class": y,
        "spotify_popularity": np.array([5, 25, 55])[y],
        "sampling_weight": np.ones(90),
    }
    for name in (*mod.model.BLOCKS, mod.model.REFERENCE):
        for index in range(3):
            values[name + "_probability_" + str(index)] = (
                prior[:, index] if name == mod.model.REFERENCE else probability[:, index]
            )
    frame = pl.DataFrame(values)
    published = []
    for name in (*mod.model.BLOCKS, mod.model.REFERENCE):
        current = prior if name == mod.model.REFERENCE else probability
        for fold in (-1, 0, 1, 2, 3, 4):
            mask = np.ones(90, dtype=bool) if fold == -1 else folds == fold
            for weighting in ("equal_tracks", "original_weight_sensitivity"):
                result, _ = mod.model.metrics(y[mask], current[mask])
                published.append(
                    {"model": name, "outer_fold": fold, "weighting": weighting, **result}
                )
    metrics, confusion, _ = mod.diagnose(frame, published, expected=90, expected_components=45)
    assert len(metrics) == 120
    assert len(confusion) == 1080
    first = [
        r
        for r in metrics
        if r["model"] == "combined" and r["weighting"] == "equal_tracks" and r["outer_fold"] == -1
    ]
    assert (
        first[0]["log_loss_original_probabilities"] == first[1]["log_loss_original_probabilities"]
    )
    broken = frame.with_columns(
        pl.lit(0.6).alias("class_prior_probability_0"),
        pl.lit(0.2).alias("class_prior_probability_1"),
        pl.lit(0.2).alias("class_prior_probability_2"),
    )
    with pytest.raises(ValueError, match="exclusivamente ao treino"):
        mod.validate_frame(broken, expected=90, expected_components=45)
    published[0]["accuracy"] = 0
    with pytest.raises(ValueError, match="não reproduzida"):
        mod.diagnose(frame, published, expected=90, expected_components=45)
