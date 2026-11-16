import json

import numpy as np
import polars as pl
import pytest
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score

from tcc_music_popularity import popularity_levels as mod


def test_limites_sem_arredondar_ou_descartar_extrapolacoes():
    assert mod.categories([-10, 0, 19.999, 20, 39.999, 40, 110], [20, 40]).tolist() == [
        0,
        0,
        0,
        1,
        1,
        2,
        2,
    ]
    for values in ([np.nan], [np.inf], [0.5], [-1], [101]):
        with pytest.raises(ValueError):
            mod.categories(values, [20, 40], observed=True)


@pytest.mark.parametrize("weighted", [False, True])
def test_metricas_conferem_com_biblioteca_independente(weighted):
    truth = np.array([0, 0, 0, 1, 1, 2])
    predicted = np.array([0, 0, 2, 1, 2, 2])
    weights = np.array([1, 1, 3, 2, 1, 4]) if weighted else None
    result, matrix, _, _ = mod.scores(truth, predicted, weights)
    assert result["accuracy"] == pytest.approx(
        accuracy_score(truth, predicted, sample_weight=weights)
    )
    assert result["balanced_accuracy"] == pytest.approx(
        balanced_accuracy_score(truth, predicted, sample_weight=weights)
    )
    assert result["macro_f1"] == pytest.approx(
        f1_score(truth, predicted, average="macro", sample_weight=weights)
    )
    assert matrix.sum() == (6 if weights is None else weights.sum())


def test_ausencia_de_classe_nao_e_omitida_da_media():
    result, _, _, _ = mod.scores([0, 0], [0, 0])
    assert result["accuracy"] == 1
    assert result["balanced_accuracy"] is None
    assert result["macro_f1"] is None
    assert result["all_true_classes_present"] is False
    with pytest.raises(ValueError, match="Pesos"):
        mod.scores([0, 1, 2], [0, 1, 2], [1, 0, 1])


@pytest.fixture
def frames():
    group = np.repeat(np.arange(45), 2)
    y = np.array([5, 25, 55])[group % 3]
    predictions = pl.DataFrame(
        {
            "track_id": [f"faixa{i:03d}" for i in range(90)],
            "text_component_id": [f"grupo{g:03d}" for g in group],
            mod.TARGET: y.astype(float),
            "sampling_weight": np.linspace(1, 4, 90),
            "outer_fold": group % 5,
            **{
                "prediction_" + model: y.astype(float) + offset
                for model, offset in zip(mod.MODELS, (10, 9, 8, 7, 12, 11), strict=True)
            },
        }
    )
    folds = predictions.select("track_id", "text_component_id", "outer_fold").with_columns(
        [
            pl.Series("inner_outer_" + str(outer), np.where(group % 5 == outer, -1, group // 15))
            for outer in range(5)
        ]
    )
    return predictions, folds


def test_alinhamento_por_id_e_bloqueio_de_vazamento(frames):
    predictions, folds = frames
    result, _ = mod.validate_frames(predictions.reverse(), folds, 90)
    assert result["track_id"].to_list() == predictions["track_id"].to_list()
    broken = (
        folds.with_row_index()
        .with_columns(
            pl.when(pl.col("index") == 0)
            .then(4)
            .otherwise(pl.col("outer_fold"))
            .alias("outer_fold")
        )
        .drop("index")
    )
    with pytest.raises(ValueError, match="cruza folds"):
        mod.validate_frames(predictions, broken, 90)
    broken = (
        folds.with_row_index()
        .with_columns(
            pl.when(pl.col("index") == 2)
            .then(2)
            .otherwise(pl.col("inner_outer_0"))
            .alias("inner_outer_0")
        )
        .drop("index")
    )
    with pytest.raises(ValueError, match="cruza folds internos"):
        mod.validate_frames(predictions, broken, 90)


def test_suporte_todas_as_particoes_e_referencia_so_no_treino(frames):
    predictions, folds = frames
    settings = mod.config()
    counts = mod.partition_counts(predictions, folds, settings)
    assert len(counts) == 2 * 5 * 8 * 3
    assert all(r["n"] > 0 for r in counts if r["scheme"] == "principal_20_40")
    metrics, confusion, _, _ = mod.prediction_diagnostics(predictions, settings)
    majority = next(
        r
        for r in metrics
        if r["scheme"] == "principal_20_40"
        and r["model"] == "majority_outer_train"
        and r["outer_fold"] == -1
        and r["weighting"] == "equal_tracks"
    )
    assert majority["balanced_accuracy"] == pytest.approx(1 / 3)
    assert (
        sum(
            r["count_or_weight"]
            for r in confusion
            if r["scheme"] == "principal_20_40"
            and r["model"] == "combined"
            and r["outer_fold"] == -1
            and r["weighting"] == "equal_tracks"
        )
        == 90
    )


def test_agregacao_nao_interpola_banda_cortada():
    settings = mod.config()
    allocation = [{"N_h": "1159764", "n_h": "200000", "popularity_band": "0–100"}]
    coverage = [
        {
            "observed_n": "200000",
            "accepted_n": "77535",
            "accepted_weight": "400000",
            "sampling_popularity_band": "0–100",
        }
    ]
    with pytest.raises(ValueError, match="corta banda"):
        mod.aggregate_counts(allocation, coverage, settings)


def test_execucao_completa_sintetica_preserva_fontes_e_selo(tmp_path, frames):
    predictions, folds = frames
    for path, frame in ((mod.PREDICTIONS, predictions), (mod.FOLDS, folds)):
        target = tmp_path / path.relative_to(mod.ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        frame.write_parquet(target)
    settings = mod.config()
    settings.update(expected_tracks=90, expected_components=45)
    for path, value in ((mod.CONFIG, settings), (mod.FROZEN, {"fontes_seladas_preservadas": {}})):
        mod.atomic_json(tmp_path / path.relative_to(mod.ROOT), value)
    protocol = tmp_path / mod.PROTOCOL.relative_to(mod.ROOT)
    protocol.parent.mkdir(parents=True, exist_ok=True)
    protocol.write_text("Protocolo sintético", encoding="utf-8")
    pred_path = tmp_path / mod.PREDICTIONS.relative_to(mod.ROOT)
    fold_path = tmp_path / mod.FOLDS.relative_to(mod.ROOT)
    seal = {"inputs": {str(fold_path.resolve()): mod.digest(fold_path)}}
    report = {
        "completed": True,
        "mode": "all",
        "prediction_rows": 90,
        "seal": seal,
        "signature": mod.fingerprint(seal),
        "predictions_sha256": mod.digest(pred_path),
    }
    mod.atomic_json(tmp_path / mod.REGRESSION.relative_to(mod.ROOT), report)
    before = {p: mod.digest(p) for p in (pred_path, fold_path)}
    result = mod.run("previsoes", root=tmp_path, output=tmp_path / "saida")
    assert result["completed"]
    assert result["models_trained"] is False
    assert result["operational_support_all_partitions"] is False
    assert before == {p: mod.digest(p) for p in before}
    mod.run("previsoes", root=tmp_path, output=tmp_path / "saida")
    config_path = tmp_path / mod.CONFIG.relative_to(mod.ROOT)
    changed = json.loads(config_path.read_text(encoding="utf-8"))
    changed["schemes"]["principal_20_40"] = [20, 60]
    mod.atomic_json(config_path, changed)
    with pytest.raises(ValueError, match="outra versão"):
        mod.run("previsoes", root=tmp_path, output=tmp_path / "saida")
    assert (tmp_path / "saida/previsoes/metricas_categorizadas.csv").exists()


def test_diretorio_existente_nao_e_sobrescrito(tmp_path):
    (tmp_path / "anotacao.txt").write_text("Preservar", encoding="utf-8")
    with pytest.raises(ValueError, match="sem selo"):
        mod.prepare_output(tmp_path, {"a": 1}, [])
    assert (tmp_path / "anotacao.txt").read_text(encoding="utf-8") == "Preservar"
