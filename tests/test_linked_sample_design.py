"""A alocação respeita capacidades, suporte e o tamanho fixado por banda."""

import polars as pl
import pytest

from tcc_music_popularity import linked_sample_design as mod


def test_redistribui_deficit_preservando_suporte():
    assert mod.allocate([1, 4, 3, 0], [3, 0, 2, 1]) == [1, 3, 2, 0]
    assert mod.allocate([5, 2, 2], [3, 0, 0]) == [1, 1, 1]
    with pytest.raises(ValueError, match="suporte"):
        mod.allocate([1, 1], [1, 0])


def test_sorteio_fixo_sem_reposicao_e_com_probabilidades_conhecidas(monkeypatch):
    monkeypatch.setattr(mod, "SIZE", 4)
    frame = mod.bands(
        pl.DataFrame(
            {
                "track_id": ["a", "b", "c", "d", "e", "f", "g"],
                "genre": ["x", "x", "y", "y", "x", "x", "y"],
                "popularity": [1, 2, 3, 4, 85, 90, 91],
            }
        )
    )
    sample = frame.filter(pl.col("track_id").is_in(["a", "b", "c", "f"]))
    picked, plan = mod.draw(frame, sample)
    assert picked.height == picked["track_id"].n_unique() == 4
    assert picked.equals(mod.draw(frame, sample)[0])
    assert picked["linked_weight"].sum() == pytest.approx(frame.height)
    assert len(plan) == 3
