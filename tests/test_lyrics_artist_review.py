"""A confirmação da grafia não elimina o controle de texto e versão."""

import pytest
from test_lyrics_matching_revision import candidate, query

from tcc_music_popularity import lyrics_artist_review as mod


def test_preserva_texto_e_recusa_concorrencia_real():
    original = candidate(synced="[00:01.00]PRIMEIRO VERSO SEGUNDO VERSO")
    outcome, lyric = mod.review_text(query(), [original])
    assert outcome == "accepted_after_catalog_review"
    assert lyric["accepted_text"] == original["plainLyrics"]
    assert lyric["synced_text_source"] == original["syncedLyrics"]
    assert mod.review_text(query(), [original, candidate(2, plain="Outro texto")])[1] is None
    with pytest.raises(ValueError, match="versão"):
        mod.review_text(query(), [candidate(title="Song - Live")])
