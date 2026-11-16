"""Casos concretos dos dois bloqueios, com dados sintéticos e sem rede real."""

import copy
import socket

import polars as pl
import pytest
from test_new_sample_local import setup

from tcc_music_popularity import lyrics_matching_revision as mod


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("Rede proibida")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(mod.recovery.local, "space", lambda *args: None)


def query(title="Song"):
    return mod.recovery.recovery_query(
        {
            "track_id": "sintetico",
            "artist_name": "Artist",
            "track_name": title,
            "duration_ms": "180000",
        }
    )


def candidate(identifier=1, title="Song", plain="Primeiro verso\n\nSegundo verso", synced=None):
    return {
        "id": identifier,
        "trackName": title,
        "artistName": "Artist",
        "duration": 180.0,
        "albumName": "Álbum sintético",
        "plainLyrics": plain,
        "syncedLyrics": synced,
        "instrumental": False,
        "local_lyrics_id": identifier,
    }


def test_equivalencia_apenas_de_espacos_preserva_fontes_e_palavras():
    c = candidate(synced="[00:01.00]Primeiro verso\n[00:02.00]Segundo verso")
    original = copy.deepcopy(c)
    assert mod.recovery.classify(query(), [c])[0]["reason"] == "plain_synced_conflict"
    result, lyric = mod.classify(query(), [c])
    assert result["status"] == "accepted" and result["layout_equivalent_ids"] == [1]
    assert lyric["plain_text_source"] == original["plainLyrics"]
    assert lyric["synced_text_source"] == original["syncedLyrics"]
    assert result["synced_present"] is True
    assert c == original
    changed = candidate(synced="[00:01.00]Primeiro verso\n[00:02.00]Outro conteúdo")
    assert mod.classify(query(), [changed])[0]["reason"] == "plain_synced_conflict"
    assert not mod.whitespace_equal("primeiro segundo", "segundo primeiro")
    assert not mod.whitespace_equal("palavra", "PALAVRA")


def test_outra_versao_nao_veta_candidato_completamente_compativel():
    studio = candidate()
    live = candidate(2, title="Song - Live", plain="Letra da gravação ao vivo")
    assert (
        mod.recovery.classify(query(), [studio, live])[0]["reason"] == "positive_version_conflict"
    )
    result, lyric = mod.classify(query(), [studio, live])
    assert result["status"] == "accepted" and lyric["lrclib_id"] == 1
    assert mod.classify(query("Song - Live"), [studio, live])[1]["lrclib_id"] == 2
    assert mod.classify(query("Song - Remix"), [studio, live])[0]["status"] == "ambiguous"
    assert mod.classify(query(), [live])[0]["status"] == "ambiguous"


def test_incertezas_reais_e_limites_nao_sao_relaxados():
    assert (
        mod.classify(query(), [candidate(), candidate(2, plain="Outro texto")])[0]["status"]
        == "ambiguous"
    )
    assert (
        mod.classify(query(), [candidate(), candidate(1, plain="Outro payload")])[0]["reason"]
        == "same_id_payload_conflict"
    )
    assert mod.classify(query(), [candidate()], "candidate_limit")[0]["status"] == "ambiguous"
    wrong = candidate()
    wrong["duration"] = 300
    assert mod.classify(query(), [wrong])[0]["status"] != "accepted"
    wrong["duration"] = 180
    wrong["artistName"] = "Another artist"
    assert mod.classify(query(), [wrong])[0]["status"] != "accepted"
    with pytest.raises(ValueError, match="proibido"):
        mod.classify({**query(), "popularity": 80}, [candidate()])


def test_fluxo_dirigido_sem_indice_novo_preserva_42_e_retomada(tmp_path, monkeypatch):
    args, sample, _ = setup(tmp_path)
    old_result = mod.local.run(**args)
    source_hash = mod.design.sha256(args["workspace"] / "state.sqlite")
    primary_hash = mod.design.sha256(args["primary"])
    supplement_hash = mod.design.sha256(args["supplement"] / "lookup.sqlite")

    def deny_index(*args, **kwargs):
        raise AssertionError("Reconstrução de índice proibida na revisão")

    monkeypatch.setattr(mod.recovery, "build_index", deny_index)
    revised_args = {
        "sample": args["sample"],
        "source_workspace": args["workspace"],
        "source_summary": args["output"] / "resumo_busca_local.json",
        "dump": args["dump"],
        "primary": args["primary"],
        "supplement": args["supplement"],
        "recovery_state": args["recovery_state"],
        "workspace": tmp_path / "revised_private",
        "output": tmp_path / "revised_public",
    }
    result = mod.run(**revised_args)
    assert result["completed"] and result["revision_targets"] == 1
    assert result["status_counts"]["accepted"] == old_result["status_counts"]["accepted"] + 1
    assert result["status_counts"]["ambiguous"] == 1
    assert result["status_counts"]["instrumental"] == old_result["status_counts"]["instrumental"]
    assert result["status_counts"]["not_found"] == old_result["status_counts"]["not_found"]
    assert result["indices_built"] == 0
    final = pl.read_parquet(revised_args["workspace"] / "resultados_faixas.parquet")
    assert final.select(sample.columns).equals(sample)
    assert final.filter(pl.col("track_id") == "h")["lyrics_status"][0] == "accepted"
    assert "local42_lyrics_status" in final.columns
    assert mod.design.sha256(args["workspace"] / "state.sqlite") == source_hash
    assert mod.design.sha256(args["primary"]) == primary_hash
    assert mod.design.sha256(args["supplement"] / "lookup.sqlite") == supplement_hash
    again = mod.run(**revised_args)
    assert again["new_queries_this_invocation"] == 0
    assert again["private_sha256"] == result["private_sha256"]
