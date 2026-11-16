"""Seleção conservadora e retomada do piloto com resposta HTTP simulada."""

import json
import sqlite3
from contextlib import closing

from test_lyrics_matching_revision import candidate, query

from tcc_music_popularity import lyrics_online_pilot as mod


def test_candidato_provisorio_requer_duracao_e_metadados_compativeis():
    found = candidate(synced="[00:01.00]PRIMEIRO VERSO SEGUNDO VERSO")
    result, text = mod.classify_response(query(), [found])
    assert result["outcome"] == "candidata_provisoria"
    assert text["accepted_text"] == found["plainLyrics"]
    assert text["synced_text_source"] == found["syncedLyrics"]
    assert text["lrclib_id"] == found["id"] and text["lrclib_lyrics_id"] is None
    for wrong in (
        {**found, "duration": 182.1},
        {**found, "duration": 0},
        {**found, "artistName": "Another artist"},
        {**found, "trackName": "Song - Live"},
    ):
        result, text = mod.classify_response(query(), [wrong])
        assert result["outcome"] == "sem_candidato_compativel"
        assert text is None


def test_conflito_textual_e_resultado_truncado_seguem_pendentes():
    a = candidate()
    b = candidate(2, plain="Outra letra")
    result, text = mod.classify_response(query(), [a, b])
    assert result["outcome"] == "different_after_case_normalization"
    assert text is None
    result, text = mod.classify_response(query(), [a] * mod.RESPONSE_LIMIT)
    assert result["outcome"] == "limite_da_busca"
    assert text is None


def test_pausa_http_respeita_retry_after_e_retoma_sem_reconsultar(monkeypatch):
    now = [1_000.0]
    monkeypatch.setattr(mod.time, "time", lambda: now[0])
    monkeypatch.setattr(mod.time, "sleep", lambda _: None)
    first, second = query(), query("Other")
    manifest = {
        "sample_tracks": 2,
        "jobs": {"a": {"query": first}, "b": {"query": second}},
    }
    responses = iter([(200, None, b"[]"), (429, "120", None), (200, None, b"[]")])
    sent = []

    def fetch(q):
        sent.append(q)
        return next(responses)

    with closing(sqlite3.connect(":memory:")) as db:
        stored, pause = mod.collect(db, manifest, fetch)
        assert list(stored) == ["a"]
        assert pause == {"reason": "HTTP 429", "retry_at": 1120.0}
        assert mod.collect(db, manifest, fetch)[0] == stored
        now[0] = 1_121.0
        stored, pause = mod.collect(db, manifest, fetch)
        assert set(stored) == {"a", "b"}
        assert pause is None
        assert sent == [first, second, second]


def test_falha_de_formato_nao_conta_como_resposta_negativa():
    decision, text, pause = mod.query_once(query(), lambda _: (200, None, json.dumps({}).encode()))
    assert decision is None and text is None
    assert pause == ("ValueError", 60)
