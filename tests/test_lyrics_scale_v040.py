from __future__ import annotations

import json

import pytest

from tcc_music_popularity.lyrics_pilot_v012 import (
    ACCEPTED_STATUSES,
    classify_cached_composition_v012,
)
from tcc_music_popularity.lyrics_scale_v040 import (
    activate_reserve_batches,
    audit_public_scale_outputs,
    cache_is_compatible,
    locate_compatible_cache,
)


def _query(key: str = "artist|||song"):
    return {
        "composition_key": key,
        "representative_spotify_row_id": 1,
        "representative_track_id": "track",
        "artist_name_query": "Artist",
        "track_name_query": "Song",
        "title_base_query": "Song",
        "album_name_query": None,
        "duration_seconds": 200.0,
        "remaster": False,
        "remix": False,
        "live": False,
        "acoustic": False,
        "radio_edit": False,
        "mono_stereo": False,
        "instrumental": False,
        "demo": False,
        "karaoke": False,
    }


def _envelope(key: str = "artist|||song"):
    candidate = {
        "id": 123,
        "artistName": "Artist",
        "trackName": "Song",
        "albumName": None,
        "duration": 200.0,
        "instrumental": False,
        "plainLyrics": "First line\nSecond line",
        "syncedLyrics": None,
    }
    return {
        "cache_version": "v0.4",
        "cache_key": __import__("hashlib").sha256(key.encode()).hexdigest(),
        "composition_key": key,
        "requests": [
            {
                "endpoint": "/api/get",
                "parameters": {
                    "artist_name": "Artist",
                    "track_name": "Song",
                    "album_name": None,
                    "duration": 200.0,
                },
                "http_status": 200,
                "payload": candidate,
                "attempts": [{"http_status": 200}],
            },
            {
                "endpoint": "/api/search",
                "parameters": {
                    "artist_name": "Artist",
                    "track_name": "Song",
                    "album_name": None,
                },
                "http_status": 200,
                "payload": [candidate],
                "attempts": [{"http_status": 200}],
            },
        ],
    }


def test_cache_reuse_requires_exact_query_and_integrity():
    query = _query()
    envelope = _envelope()
    assert cache_is_compatible(query, envelope)
    envelope["requests"][0]["parameters"]["duration"] = 199.0
    assert not cache_is_compatible(query, envelope)


def test_cache_outside_cohort_is_ignored(tmp_path):
    current = tmp_path / "current"
    legacy = tmp_path / "legacy"
    current.mkdir()
    legacy.mkdir()
    outside = _envelope("outside|||song")
    outside_path = current / f"{outside['cache_key']}.json"
    outside_path.write_text(json.dumps(outside), encoding="utf-8")
    envelope, source = locate_compatible_cache(_query(), current, legacy)
    assert envelope is None and source is None


def test_exact_unique_acceptance_rule_is_preserved():
    row = classify_cached_composition_v012(_query(), _envelope())
    assert row["final_status"] in ACCEPTED_STATUSES


def test_reserve_activates_complete_batches_sequentially():
    assert activate_reserve_batches(10000, {}) == []
    assert activate_reserve_batches(9800, {1: 300, 2: 300}) == [1]
    assert activate_reserve_batches(9000, {1: 200, 2: 200, 3: 200, 4: 200}) == [1, 2, 3, 4]


def test_public_audit_rejects_lyrics_and_private_paths(tmp_path):
    report = tmp_path / "report.md"
    report.write_text("plainLyrics", encoding="utf-8")
    with pytest.raises(AssertionError, match="Marcadores privados"):
        audit_public_scale_outputs([report])
