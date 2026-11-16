"""O teto de candidatos deve incidir após a elegibilidade de metadados."""

import sqlite3
from contextlib import closing

from test_lyrics_matching_revision import query

from tcc_music_popularity import lyrics_limit_revision as mod


def fill(index, dump, durations):
    index.row_factory = sqlite3.Row
    index.execute(
        "CREATE TABLE catalog(id INTEGER PRIMARY KEY,name,artist_name,album_name,duration,last_lyrics_id,artist_key,title_key)"
    )
    index.execute("CREATE INDEX key_lookup ON catalog(artist_key,title_key,id)")
    dump.execute(
        "CREATE TABLE lyrics(id INTEGER PRIMARY KEY,track_id,plain_lyrics,synced_lyrics,instrumental)"
    )
    for key, duration in enumerate(durations, start=1):
        index.execute(
            "INSERT INTO catalog VALUES(?,'Song','Artist','Album',?,?,'artist','song')",
            (key, duration, key),
        )
        if duration <= 190:
            dump.execute("INSERT INTO lyrics VALUES(?,?,?,NULL,0)", (key, key, "Texto original"))


def test_volume_de_incompativeis_nao_veta_letra_elegivel():
    with closing(sqlite3.connect(":memory:")) as ix, closing(sqlite3.connect(":memory:")) as dump:
        fill(ix, dump, [250] * 500 + [180])
        assert mod.recovery.lookup(dump, ix, query()) == ([], "candidate_limit")
        decision, lyric = mod.lookup(dump, ix, query())
        assert decision == {
            "metadata_rows": 501,
            "compatible": 1,
            "selected_lrclib_id": 501,
            "outcome": "accepted_after_metadata_filter",
        }
        assert lyric["accepted_text"] == "Texto original"
        assert lyric["rules_version"] == mod.VERSION


def test_teto_dos_compativeis_e_truncamento_de_metadados_barram_aceitacao(monkeypatch):
    with closing(sqlite3.connect(":memory:")) as ix, closing(sqlite3.connect(":memory:")) as dump:
        fill(ix, dump, [180] * 501)
        result, lyric = mod.lookup(dump, ix, query())
        assert result["outcome"] == "limite_de_candidatos_compativeis"
        assert lyric is None
        monkeypatch.setattr(mod, "METADATA_LIMIT", 500)
        result, lyric = mod.lookup(dump, ix, query())
        assert result["outcome"] == "limite_de_metadados"
        assert lyric is None


def test_textos_elegiveis_incompativeis_seguem_ambiguos():
    with closing(sqlite3.connect(":memory:")) as ix, closing(sqlite3.connect(":memory:")) as dump:
        fill(ix, dump, [180, 181])
        dump.execute("UPDATE lyrics SET plain_lyrics='Texto diferente' WHERE id=2")
        result, lyric = mod.lookup(dump, ix, query())
        assert result["outcome"] == "different_after_case_normalization"
        assert lyric is None
