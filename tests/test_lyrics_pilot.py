from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import polars as pl
import pytest

from tcc_music_popularity.config import PROJECT_ROOT, load_yaml
from tcc_music_popularity.lyrics_pilot import (
    EXPECTED_FROZEN_HASHES,
    LRCLIBClient,
    _allocate_proportional,
    _candidate_diagnostics,
    _frozen_state,
    _git_tracked_private_files,
    _sample_records,
    milliseconds_to_seconds,
    pilot_base_title,
    prepare_lyrics_pilot,
    process_lookup_response,
    run_lyrics_smoke,
)


def _query(**overrides):
    base = {
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
    return {**base, **overrides}


def _candidate(identifier=1, **overrides):
    base = {
        "id": identifier,
        "trackName": "Song",
        "artistName": "Artist",
        "albumName": "Synthetic Album",
        "duration": 181.0,
        "instrumental": False,
        "plainLyrics": "SYNTHETIC_A\nSYNTHETIC_B",
        "syncedLyrics": None,
    }
    return {**base, **overrides}


def _envelope(get_status=404, get_payload=None, search_status=200, search_payload=None):
    return {
        "queried_at": "2026-09-04T00:00:00+00:00",
        "cache_hit": False,
        "requests": [
            {
                "endpoint": "/api/get",
                "http_status": get_status,
                "payload": get_payload,
                "attempts": [{"attempt": 1, "http_status": get_status, "error_type": None}],
            },
            {
                "endpoint": "/api/search",
                "http_status": search_status,
                "payload": [] if search_payload is None else search_payload,
                "attempts": [{"attempt": 1, "http_status": search_status, "error_type": None}],
            },
        ],
    }


def test_hamilton_allocation_is_exact_and_capacity_bounded():
    allocation = _allocate_proportional({"a": 1, "b": 4, "c": 5}, 7)
    assert sum(allocation.values()) == 7
    assert all(allocation[key] <= capacity for key, capacity in {"a": 1, "b": 4, "c": 5}.items())
    assert allocation == _allocate_proportional({"a": 1, "b": 4, "c": 5}, 7)


def test_sampling_is_deterministic_unique_and_diverse():
    records = []
    for index in range(200):
        records.append(
            {
                "composition_key": f"artist-{index}|||song-{index}",
                "period": ("2000-2005", "2006-2011", "2012-2017", "2018-2023")[index % 4],
                "popularity_quintile": f"Q{index % 5 + 1}",
                "genre_sampling": f"genre-{index % 3}",
                "match_method": ("raw_exact", "strict_normalized")[index % 2],
                "version_profile": ("original_sem_flag", "remaster")[index % 2],
            }
        )
    first = _sample_records(records, 100, 20260901, hash_label="test")
    second = _sample_records(records, 100, 20260901, hash_label="test")
    assert [row["composition_key"] for row in first] == [row["composition_key"] for row in second]
    assert len(first) == len({row["composition_key"] for row in first}) == 100
    assert len({(row["period"], row["popularity_quintile"]) for row in first}) == 20


def test_duration_conversion_and_title_normalization():
    assert milliseconds_to_seconds(181234) == 181.234
    assert milliseconds_to_seconds(None) is None
    assert pilot_base_title("Song (Karaoke Version)") == "Song"
    assert pilot_base_title("Song - Live") == "Song"


def test_exact_rules_reject_duration_and_version_mismatch():
    query = _query()
    assert _candidate_diagnostics(query, _candidate(duration=189.9), 10.0)["accepted_by_rules"]
    assert not _candidate_diagnostics(query, _candidate(duration=190.1), 10.0)["accepted_by_rules"]
    assert not _candidate_diagnostics(query, _candidate(trackName="Song - Live"), 10.0)[
        "accepted_by_rules"
    ]


def test_fuzzy_candidate_is_never_accepted():
    result = process_lookup_response(
        _query(),
        _envelope(search_payload=[_candidate(trackName="Songs", artistName="The Artist")]),
    )
    assert result["final_status"] == "needs_review"
    assert result["lrclib_id"] is None


def test_multiple_exact_candidates_are_ambiguous():
    result = process_lookup_response(
        _query(),
        _envelope(search_payload=[_candidate(1), _candidate(2, duration=182.0)]),
    )
    assert result["final_status"] == "ambiguous"
    assert result["lrclib_id"] is None


def test_instrumental_and_empty_results_have_distinct_statuses():
    instrumental = process_lookup_response(
        _query(),
        _envelope(search_payload=[_candidate(instrumental=True, plainLyrics=None)]),
    )
    empty = process_lookup_response(_query(), _envelope(search_payload=[]))
    assert instrumental["final_status"] == "instrumental"
    assert empty["final_status"] == "not_found"


def test_processed_result_has_hash_and_counts_but_no_text_columns():
    result = process_lookup_response(_query(), _envelope(search_payload=[_candidate()]))
    assert result["final_status"] == "accepted_exact"
    assert result["lyrics_character_count"] == len("SYNTHETIC_A\nSYNTHETIC_B")
    assert result["lyrics_line_count"] == 2
    assert len(result["lyrics_sha256"]) == 64
    assert not {"plainLyrics", "syncedLyrics", "lyricsfile"} & set(result)


def test_private_cache_is_idempotent_and_dry_run_has_no_network(tmp_path: Path):
    calls = []

    def transport(url, headers, timeout):
        calls.append((urlparse(url).path, headers["User-Agent"], timeout))
        return (404, {}) if urlparse(url).path == "/api/get" else (200, [])

    config = {
        "base_url": "https://lrclib.invalid",
        "cache_dir": str(tmp_path / "private"),
        "user_agent": "academic-test-client",
        "timeout_seconds": 1,
        "max_attempts": 2,
        "backoff_seconds": 0,
        "minimum_delay_seconds": 0,
    }
    client = LRCLIBClient(config, transport=transport, sleep_fn=lambda _: None)
    dry = client.lookup(_query(), dry_run=True)
    assert dry["dry_run"] and calls == []
    first = client.lookup(_query())
    second = client.lookup(_query())
    assert len(calls) == 2
    assert not first["cache_hit"]
    assert not second["cache_hit"]
    assert second["cache_reused_current_run"]
    cached = json.loads(next((tmp_path / "private").glob("*.json")).read_text(encoding="utf-8"))
    assert len(cached["requests"]) == 2


def test_retry_and_timeout_are_bounded(tmp_path: Path):
    calls = 0

    def transport(url, headers, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("synthetic timeout")
        return (404, {}) if urlparse(url).path == "/api/get" else (200, [])

    config = {
        "base_url": "https://lrclib.invalid",
        "cache_dir": str(tmp_path / "private"),
        "user_agent": "academic-test-client",
        "timeout_seconds": 1,
        "max_attempts": 2,
        "backoff_seconds": 0,
        "minimum_delay_seconds": 0,
    }
    envelope = LRCLIBClient(config, transport=transport, sleep_fn=lambda _: None).lookup(_query())
    assert calls == 3
    assert len(envelope["requests"][0]["attempts"]) == 2


def test_exhausted_timeout_becomes_request_error(tmp_path: Path):
    def transport(url, headers, timeout):
        raise TimeoutError("synthetic timeout")

    config = {
        "base_url": "https://lrclib.invalid",
        "cache_dir": str(tmp_path / "private"),
        "user_agent": "academic-test-client",
        "timeout_seconds": 1,
        "max_attempts": 1,
        "backoff_seconds": 0,
        "minimum_delay_seconds": 0,
    }
    envelope = LRCLIBClient(config, transport=transport, sleep_fn=lambda _: None).lookup(_query())
    result = process_lookup_response(_query(), envelope)
    assert result["final_status"] == "request_error"
    assert result["attempts"] == 2
    assert "TimeoutError" in result["technical_error"]


def test_real_cohort_and_frozen_checkpoint_are_valid():
    missing = [
        relative for relative in EXPECTED_FROZEN_HASHES if not (PROJECT_ROOT / relative).exists()
    ]
    if missing:
        pytest.skip(f"Artefatos locais não disponíveis: {missing}")
    summary = prepare_lyrics_pilot()
    assert summary["cohort_rows"] == summary["unique_compositions"] == 2000
    assert summary["smoke_rows"] == 100
    assert not summary["lookup_forbidden_success_fields"]
    lookup = pl.read_parquet(PROJECT_ROOT / "data/processed/lyrics_pilot_lookup_input_v0_1.parquet")
    cohort = pl.read_parquet(PROJECT_ROOT / "data/processed/lyrics_pilot_cohort_v0_1.parquet")
    assert lookup.height == cohort.height == 2000
    assert lookup.get_column("composition_key").null_count() == 0
    assert not {
        "spotify_popularity",
        "genius_lyrics_views",
        "lfm_playcount",
        "popularity_quintile",
    } & set(lookup.columns)
    assert cohort.filter(pl.col("smoke_selected")).height == 100
    split = pl.read_parquet(PROJECT_ROOT / "data/processed/split_assignments_v0_1_1.parquet")
    cohort_split = cohort.join(
        split.select(["spotify_row_id", "split"]),
        left_on="representative_spotify_row_id",
        right_on="spotify_row_id",
        how="left",
        validate="1:1",
    )
    assert cohort_split.get_column("split").unique().to_list() == ["development_train"]
    frozen = _frozen_state()
    assert frozen["all_hashes_identical"]
    assert frozen["split_counts"] == {"development_train": 83817, "holdout_test": 27941}
    assert frozen["development_holdout_id_overlap"] == 0
    assert _git_tracked_private_files() == []


def test_cli_dry_run_does_not_call_network():
    config = load_yaml("configs/lyrics_pilot_v0_1.yaml")
    summary = run_lyrics_smoke(limit=3, dry_run=True)
    assert summary["status"] == "dry_run"
    assert summary["network_requests_planned"] == 0
    assert len(summary["composition_keys"]) == 3
    assert Path(config["outputs"]["lookup_parquet"]).suffix == ".parquet"
