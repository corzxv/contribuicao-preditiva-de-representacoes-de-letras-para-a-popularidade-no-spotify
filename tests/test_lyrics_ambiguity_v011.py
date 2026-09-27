from __future__ import annotations

import urllib.request
from contextlib import suppress

import polars as pl

from tcc_music_popularity.config import PROJECT_ROOT
from tcc_music_popularity.lyrics_ambiguity_v011 import (
    FORBIDDEN_TEXT_FIELDS,
    _offline_network_guard,
    audit_lyrics_ambiguity_v011,
    deduplicate_candidates,
    flexible_plain_text_metrics,
    reclassify_cached_composition,
    strict_plain_text_metrics,
)
from tcc_music_popularity.lyrics_pilot import _frozen_state


def _query(**overrides):
    row = {
        "composition_key": "artist|||song",
        "representative_spotify_row_id": 1,
        "representative_track_id": "track-1",
        "artist_name_query": "Artist",
        "track_name_query": "Song",
        "title_base_query": "Song",
        "album_name_query": None,
        "duration_seconds": 180.0,
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
    return {**row, **overrides}


def _candidate(identifier: int, text: str | None = "TOKEN_A\nTOKEN_B", **overrides):
    row = {
        "id": identifier,
        "name": "Song",
        "trackName": "Song",
        "artistName": "Artist",
        "albumName": "Synthetic Album",
        "duration": 181.0,
        "instrumental": False,
        "plainLyrics": text,
        "syncedLyrics": None,
        "lyricsfile": None,
    }
    return {**row, **overrides}


def _envelope(get_candidate=None, search_candidates=None):
    return {
        "queried_at": "2026-09-04T00:00:00+00:00",
        "requests": [
            {
                "endpoint": "/api/get",
                "http_status": 200 if get_candidate is not None else 404,
                "payload": get_candidate if get_candidate is not None else {"code": 404},
                "attempts": [],
            },
            {
                "endpoint": "/api/search",
                "http_status": 200,
                "payload": search_candidates or [],
                "attempts": [],
            },
        ],
    }


def test_strict_fingerprint_normalizes_only_allowed_whitespace():
    first = strict_plain_text_metrics("\ufeff\r\nTOKEN_A   TOKEN_B  \r\n\r\n")
    second = strict_plain_text_metrics("TOKEN_A TOKEN_B")
    assert first == second


def test_duplicate_between_get_and_search_is_one_candidate():
    candidate = _candidate(7)
    result = deduplicate_candidates(_envelope(candidate, [candidate]))
    assert result["candidate_count_before_dedup"] == 2
    assert result["candidate_count_after_within_endpoint_id_dedup"] == 2
    assert result["candidate_count_after_endpoint_union"] == 1
    assert len(result["repeated_identities_between_endpoints"]) == 1
    row, candidates, _ = reclassify_cached_composition(
        _query(), _envelope(candidate, [candidate]), old_status="ambiguous"
    )
    assert row["reclassified_status"] == "accepted_exact_unique"
    assert row["resolved_exclusively_by_id_dedup"]
    assert candidates[0]["source_endpoints"] == "/api/get|/api/search"


def test_different_ids_with_strictly_equivalent_text_are_accepted():
    get_candidate = _candidate(10, "\r\nTOKEN_A   TOKEN_B \r\n", duration=181.0)
    search_candidate = _candidate(2, "TOKEN_A TOKEN_B", duration=181.0)
    row, _, private = reclassify_cached_composition(
        _query(),
        _envelope(get_candidate, [search_candidate]),
        old_status="ambiguous",
    )
    assert row["reclassified_status"] == "accepted_exact_equivalent"
    assert row["selected_lrclib_id"] == 10
    assert private["equivalent_lrclib_ids"] == [10, 2]


def test_representative_uses_duration_before_endpoint():
    get_candidate = _candidate(10, duration=184.0)
    search_candidate = _candidate(20, duration=180.5)
    row, _, _ = reclassify_cached_composition(
        _query(),
        _envelope(get_candidate, [search_candidate]),
        old_status="ambiguous",
    )
    assert row["reclassified_status"] == "accepted_exact_equivalent"
    assert row["selected_lrclib_id"] == 20


def test_distinct_strict_text_remains_ambiguous_even_if_flexible_matches():
    first = _candidate(1, "TOKEN!")
    second = _candidate(2, "token")
    assert (
        strict_plain_text_metrics(first["plainLyrics"])["strict_text_sha256"]
        != (strict_plain_text_metrics(second["plainLyrics"])["strict_text_sha256"])
    )
    assert (
        flexible_plain_text_metrics(first["plainLyrics"])["flexible_text_sha256"]
        == (flexible_plain_text_metrics(second["plainLyrics"])["flexible_text_sha256"])
    )
    row, _, _ = reclassify_cached_composition(
        _query(), _envelope(first, [second]), old_status="ambiguous"
    )
    assert row["reclassified_status"] == "ambiguous_distinct_lyrics"
    assert row["selected_lrclib_id"] is None


def test_popularity_never_changes_candidate_decision():
    envelope = _envelope(_candidate(1), [_candidate(2)])
    low, _, _ = reclassify_cached_composition(
        _query(spotify_popularity=0), envelope, old_status="ambiguous"
    )
    high, _, _ = reclassify_cached_composition(
        _query(spotify_popularity=100), envelope, old_status="ambiguous"
    )
    compared = ["reclassified_status", "selected_lrclib_id", "ambiguity_cause"]
    assert {key: low[key] for key in compared} == {key: high[key] for key in compared}


def test_reclassification_performs_no_network_request():
    with _offline_network_guard() as counter:
        row, _, _ = reclassify_cached_composition(
            _query(), _envelope(_candidate(1), []), old_status="accepted_exact"
        )
    assert row["reclassified_status"] == "accepted_exact_unique"
    assert counter["blocked_attempts"] == 0


def test_offline_guard_blocks_accidental_http():
    with _offline_network_guard() as counter, suppress(RuntimeError):
        urllib.request.urlopen("https://example.invalid")
    assert counter["blocked_attempts"] == 1


def test_real_audit_is_idempotent_private_and_preserves_frozen_artifacts():
    before = _frozen_state()
    first = audit_lyrics_ambiguity_v011()
    first_reclassified = pl.read_parquet(
        PROJECT_ROOT / "data/processed/lyrics_pilot_smoke_reclassified_v0_1_1.parquet"
    )
    first_candidates = pl.read_parquet(
        PROJECT_ROOT / "data/processed/lyrics_candidate_audit_v0_1_1.parquet"
    )
    second = audit_lyrics_ambiguity_v011()
    second_reclassified = pl.read_parquet(
        PROJECT_ROOT / "data/processed/lyrics_pilot_smoke_reclassified_v0_1_1.parquet"
    )
    second_candidates = pl.read_parquet(
        PROJECT_ROOT / "data/processed/lyrics_candidate_audit_v0_1_1.parquet"
    )
    assert first["network_requests_made"] == second["network_requests_made"] == 0
    assert first["smoke_split_values"] == ["development_train"]
    assert first["privacy"]["success_fields_used_in_decision"] == []
    assert first["recommendation"] == "realizar um pequeno teste complementar"
    assert first["cache_before"] == first["cache_after"] == second["cache_after"]
    assert first["after_status_counts"] == second["after_status_counts"]
    assert first_reclassified.equals(second_reclassified)
    assert first_candidates.equals(second_candidates)
    assert first_reclassified.height == 100
    assert not FORBIDDEN_TEXT_FIELDS & set(first_reclassified.columns)
    assert not FORBIDDEN_TEXT_FIELDS & set(first_candidates.columns)
    assert first["privacy"]["tracked_private_files"] == []
    assert first["privacy"]["staged_private_files"] == []
    assert first["immutable_hashes_preserved"]
    assert before == _frozen_state()
