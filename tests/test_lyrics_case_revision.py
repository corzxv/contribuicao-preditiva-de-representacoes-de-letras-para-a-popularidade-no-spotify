"""Equivalência de caixa com fontes intactas e passagem sintética retomável."""

import socket

import polars as pl
import pytest
from test_lyrics_matching_revision import candidate, query
from test_new_sample_local import setup

from tcc_music_popularity import lyrics_case_revision as mod


def test_caixa_e_espacos_preservam_texto_sincronizado_e_original():
    original = candidate(synced="[00:01.00]Primeiro verso\n[00:02.00]Segundo verso")
    upper = candidate(2, plain="PRIMEIRO VERSO\n SEGUNDO VERSO")
    upper["duration"] = 181
    assert (
        mod.revision.classify(query(), [original, upper])[0]["reason"]
        == "substantively_distinct_texts"
    )
    result, lyric = mod.compare_case(query(), [original, upper], None)
    assert result["outcome"] == "accepted_case_equivalent"
    assert lyric["lrclib_id"] == 1
    assert lyric["accepted_text"] == original["plainLyrics"]
    assert lyric["synced_text_source"] == original["syncedLyrics"]
    mod.local.check_text(
        {**lyric, "plain_text_source": lyric["accepted_text"]},
        {
            "text_sha256": lyric["text_sha256"],
            "strict_text_sha256": lyric["strict_text_sha256"],
            "selected_lrclib_id": lyric["lrclib_id"],
        },
    )


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("Primeiro, segundo", "PRIMEIRO SEGUNDO"),
        ("Café", "CAFE"),
        ("Maße", "MASSE"),
        ("Primeiro segundo", "SEGUNDO PRIMEIRO"),
    ],
)
def test_diferencas_de_pontuacao_acentos_palavras_e_ordem_continuam_ambiguas(left, right):
    result, lyric = mod.compare_case(
        query(), [candidate(1, plain=left), candidate(2, plain=right)], None
    )
    assert result["outcome"] == "different_after_case_normalization"
    assert lyric is None


def test_incompletude_e_conflito_plain_lrc_nao_passam():
    cs = [candidate(1, plain="Texto um"), candidate(2, plain="TEXTO UM")]
    assert mod.compare_case(query(), cs, "candidate_limit")[1] is None
    cs[0]["syncedLyrics"] = "[00:01.00]Texto diferente"
    assert mod.compare_case(query(), cs, None)[1] is None


def test_fluxo_retoma_e_preserva_estados_e_indices(tmp_path, monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("Rede proibida")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(mod.local.recovery.local, "space", lambda *args: None)
    args, _, _ = setup(tmp_path)
    mod.local.run(**args)
    revision_args = {
        "sample": args["sample"],
        "source_workspace": args["workspace"],
        "source_summary": args["output"] / "resumo_busca_local.json",
        "dump": args["dump"],
        "primary": args["primary"],
        "supplement": args["supplement"],
        "recovery_state": args["recovery_state"],
        "workspace": tmp_path / "stage43",
        "output": tmp_path / "report43",
    }
    old = mod.revision.run(**revision_args)
    source = revision_args["workspace"] / "state.sqlite"
    before = mod.design.sha256(source)
    primary_before = mod.design.sha256(args["primary"])
    monkeypatch.setattr(mod.local.recovery, "build_index", deny)
    new_args = {
        "source_workspace": revision_args["workspace"],
        "source_summary": revision_args["output"] / "resumo_revisao_matching.json",
        "source42_workspace": args["workspace"],
        "dump": args["dump"],
        "primary": args["primary"],
        "supplement": args["supplement"],
        "recovery_state": args["recovery_state"],
        "workspace": tmp_path / "stage46",
        "output": tmp_path / "report46",
    }
    report = mod.run(**new_args)
    assert report["completed"] and report["targets"] == 1
    assert report["new_accepted_tracks"] == 0
    assert report["accepted_tracks_with_overlay"] == old["status_counts"]["accepted"]
    assert pl.read_parquet(new_args["workspace"] / "novos_vinculos.parquet").is_empty()
    assert mod.run(**new_args)["private_sha256"] == report["private_sha256"]
    assert mod.design.sha256(source) == before
    assert mod.design.sha256(args["primary"]) == primary_before
