import pytest

from tcc_music_popularity import linkage_review_audit as mod


def test_triagem_limites_nao_sao_erro_semantico_ou_aceitacao():
    base = {
        "artist_name": "Artista",
        "track_name": "Faixa",
        "duration_ms": "180000",
        "lyrics_status": "accepted",
        "lyrics_selected_lrclib_id": "7",
        "extreme_tail": True,
        "cache_status": "cached_candidates",
        "candidate_list_truncated": False,
        "source_incomplete_reason": None,
    }
    rows = [
        {
            **base,
            "case_id": "um",
            "candidates": [
                {"id": 7, "artistName": "Artista", "trackName": "Faixa", "duration": 180}
            ],
        },
        {**base, "case_id": "dois", "candidates": [], "candidate_list_truncated": True},
        {
            **base,
            "case_id": "tres",
            "candidates": [{"id": 7, "artistName": "Outro", "trackName": "Faixa", "duration": 180}],
        },
    ]
    result = mod.triage(rows)
    assert result[0]["technical_status"] == "selected_metadata_consistent_under_v3_rules"
    assert result[1]["technical_status"] == "selected_candidate_not_available_in_sheet"
    assert result[2]["technical_status"] == "selected_metadata_requires_review_under_v3_rules"
    assert all(
        r["human_semantic_review"] == "pending" and not r["existing_decision_changed"]
        for r in result
    )
    with pytest.raises(ValueError, match="240"):
        mod.triage(rows * 81)
