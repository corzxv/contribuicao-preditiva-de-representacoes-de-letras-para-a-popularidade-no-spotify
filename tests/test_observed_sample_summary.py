"""Médias condicionais e unidades em metadados sintéticos pequenos."""

import numpy as np
import polars as pl
import pytest

from tcc_music_popularity.observed_sample_summary import summarize_metadata


def test_pesos_condicionais_duracao_e_original_intacto():
    frame = pl.DataFrame(
        {
            "lyrics_status": ["accepted", "accepted", "not_found", "not_found"],
            "_nova_peso": [1.0, 3.0, 2.0, 2.0],
            "duration_ms": ["100000", "200000", "300000", "400000"],
        }
    )
    original = frame.clone()
    rows = summarize_metadata(
        frame,
        [
            {
                "variavel": "duration_ms",
                "unidade": "segundos",
                "media": "250",
                "dp_populacional": "100",
            }
        ],
    )
    row = rows[0]
    assert row["media_aceitas_nao_ponderada"] == 150
    assert row["media_aceitas_ponderada_condicional"] == 175
    assert row["media_sorteio_ponderada"] == 262.5
    assert row["desvio_aceitas_em_dp_catalogo"] == -1
    assert row["dp_aceitas_nao_ponderado"] == pytest.approx(np.std([100, 200], ddof=1))
    assert frame.equals(original)


def test_nao_exclui_valores_invalidos_silenciosamente():
    frame = pl.DataFrame(
        {
            "lyrics_status": ["accepted", "accepted"],
            "_nova_peso": [1.0, 1.0],
            "tempo": ["100", "NaN"],
        }
    )
    with pytest.raises(ValueError, match="não finito"):
        summarize_metadata(
            frame,
            [{"variavel": "tempo", "unidade": "BPM", "media": "100", "dp_populacional": "10"}],
        )
