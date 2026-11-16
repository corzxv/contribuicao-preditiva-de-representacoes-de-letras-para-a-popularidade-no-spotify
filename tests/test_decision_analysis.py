import numpy as np
import polars as pl
import pytest

from tcc_music_popularity import decision_analysis as mod


def test_mapeamento_de_matrizes_e_regras_bloqueia_divergencias():
    key = {
        "model": "combined",
        "outer_fold": "-1",
        "weighting": "equal_tracks",
        "decision_rule": "argmax_original",
    }
    matrix = np.array([[4, 2, 1], [1, 5, 2], [1, 1, 3]])
    cells = [
        {
            **key,
            "observed_class": str(i),
            "predicted_class": str(j),
            "count_or_weight": str(matrix[i, j]),
        }
        for i in range(3)
        for j in range(3)
    ]
    row = {
        **key,
        "accuracy": 12 / 20,
        "balanced_accuracy": (4 / 7 + 5 / 8 + 3 / 5) / 3,
        "macro_f1": (8 / 13 + 10 / 16 + 6 / 11) / 3,
        "extreme_error_rate": 2 / 20,
    }
    mod.reconcile([row], cells)
    with pytest.raises(ValueError, match="duplicada"):
        mod.reconcile([row], cells + cells[:1])
    with pytest.raises(ValueError, match="não reproduzida"):
        mod.reconcile([{**row, "accuracy": 1}], cells)


def test_inspecao_da_cauda_e_limitada_e_nao_detecta_hit_binario(tmp_path):
    values = {"spotify_popularity": [5.0, 80.0, 95.0], "text_component_id": ["a", "b", "c"]}
    for model in (*mod.sensitivity.model.BLOCKS, mod.sensitivity.model.REFERENCE):
        probabilities = (
            [[0.5, 0.3, 0.2]] * 3
            if model == mod.sensitivity.model.REFERENCE
            else [[0.8, 0.1, 0.1], [0.45, 0.3, 0.25], [0.1, 0.2, 0.7]]
        )
        for cls in range(3):
            values[f"{model}_probability_{cls}"] = [r[cls] for r in probabilities]
    path = tmp_path / "probabilidades.parquet"
    pl.DataFrame(values).write_parquet(path)
    before = path.read_bytes()
    rows = mod.bounded_tail(path, expected_rows=2, expected_components=2, expected_source_rows=3)
    combined = [r for r in rows if r["model"] == "combined"]
    assert [r["fraction_predicted_ge40"] for r in combined] == [0.5, 1.0]
    assert all(not r["is_binary_hit_detection"] for r in rows)
    with pytest.raises(ValueError, match="Cauda"):
        mod.bounded_tail(path, expected_rows=1, expected_components=1, expected_source_rows=3)
    assert path.read_bytes() == before
