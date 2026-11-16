"""A equivalência plain/LRC exige concordância de todos os candidatos elegíveis."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import polars as pl
import pytest
from test_lyrics_matching_revision import candidate, query

from tcc_music_popularity import lyrics_synced_revision as mod


def test_corrige_caixa_plain_lrc_e_preserva_originais():
    original = candidate(synced="[00:01.00]PRIMEIRO VERSO\n[00:02.00]SEGUNDO VERSO")
    alternative = candidate(2, plain="PRIMEIRO VERSO SEGUNDO VERSO")
    wrong_version = candidate(3, title="Song - Live", plain="Outro conteúdo")
    result, lyric = mod.compare_synced(query(), [original, alternative, wrong_version])
    assert result["outcome"] == "accepted_plain_lrc_case_equivalent"
    assert result["resolved_plain_lrc_ids"] == [1]
    assert result["equivalent_candidate_ids"] == [1, 2]
    assert lyric["accepted_text"] == lyric["plain_text_source"] == original["plainLyrics"]
    assert lyric["synced_text_source"] == original["syncedLyrics"]


@pytest.mark.parametrize("different", ["Outro verso", "Primeiro verso, segundo verso"])
def test_um_par_equivalente_nao_oculta_outro_conflito(different):
    original = candidate(synced="[00:01.00]PRIMEIRO VERSO SEGUNDO VERSO")
    alternate = candidate(2, synced=f"[00:01.00]{different}")
    result, lyric = mod.compare_synced(query(), [original, alternate])
    assert result["outcome"] == "plain_synced_conflict"
    assert lyric is None


def test_fluxo_por_ids_confere_hashes_e_preserva_entradas(tmp_path, monkeypatch):
    dump = tmp_path / "dump.sqlite"
    state = tmp_path / "state.sqlite"
    q = query()
    key = mod.fingerprint(q)
    source = {"fixture": True}
    monkeypatch.setattr(mod.recovery.local, "checked_dump", lambda _: source)
    c = candidate(synced="[00:01.00]PRIMEIRO VERSO SEGUNDO VERSO")
    with closing(sqlite3.connect(dump)) as db, db:
        db.execute(
            "CREATE TABLE lyrics(id INTEGER PRIMARY KEY,track_id,plain_lyrics,synced_lyrics,instrumental)"
        )
        db.execute("INSERT INTO lyrics VALUES(1,1,?,?,0)", (c["plainLyrics"], c["syncedLyrics"]))
    evidence = mod.local.evidence_metadata(q, [c], source, "indice-sintetico", None)
    with closing(sqlite3.connect(state)) as db, db:
        db.executescript(mod.local.base.STATE_SQL)
        db.execute(
            "INSERT INTO queries(query_id,data,status,result) VALUES(?,?,'ambiguous',?)",
            (key, json.dumps(q), json.dumps({"reason": "plain_synced_conflict"})),
        )
        db.execute("INSERT INTO tracks VALUES('faixa',?)", (key,))
        db.execute("INSERT INTO evidence VALUES(?,?)", (key, json.dumps(evidence)))
    s43, s46 = tmp_path / "43.json", tmp_path / "46.json"
    mod.atomic_json(
        s43,
        {
            "completed": True,
            "seal": {"dump": source, "code_sha256": mod.design.sha256(Path(mod.revision.__file__))},
        },
    )
    prior_links = tmp_path / "novos_vinculos.parquet"
    pl.DataFrame({"track_id": ["outra-faixa"], "query_id": ["outra-chave"]}).write_parquet(
        prior_links
    )
    mod.atomic_json(
        s46,
        {
            "completed": True,
            "accepted_tracks_with_overlay": 1,
            "seal": {
                "source_summary_sha256": mod.design.sha256(s43),
                "source_state_sha256": mod.design.sha256(state),
                "dump": source,
                "code_sha256": mod.design.sha256(Path(mod.case.__file__)),
            },
            "private_sha256": {prior_links.name: mod.design.sha256(prior_links)},
        },
    )
    inputs = [dump, state, s43, s46, prior_links]
    hashes = [mod.design.sha256(p) for p in inputs]
    workspace = tmp_path / "private47"
    result = mod.run(
        old_workspace=tmp_path,
        old_summary=s43,
        case_workspace=tmp_path,
        case_summary=s46,
        dump=dump,
        workspace=workspace,
        output=tmp_path / "public47",
    )
    assert result["new_accepted_tracks"] == 1
    assert result["accepted_tracks_with_overlays"] == 2
    assert pl.read_parquet(workspace / "novos_vinculos.parquet").rows() == [("faixa", key)]
    assert [mod.design.sha256(p) for p in inputs] == hashes
    with closing(sqlite3.connect(dump)) as db, db:
        db.execute("UPDATE lyrics SET plain_lyrics='inconsistente' WHERE id=1")
    with closing(sqlite3.connect(dump)) as db, pytest.raises(ValueError, match="diverge"):
        list(mod.restore_candidates(db, evidence))
