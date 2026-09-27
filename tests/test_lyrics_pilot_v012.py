from __future__ import annotations

import json

import polars as pl
import pytest

from tcc_music_popularity.config import PROJECT_ROOT, load_yaml
from tcc_music_popularity.io import sha256_file
from tcc_music_popularity.lyrics_ambiguity_v011 import flexible_plain_text_metrics
from tcc_music_popularity.lyrics_pilot import SUCCESS_FIELDS, _frozen_state
from tcc_music_popularity.lyrics_pilot_v012 import (
    ACCEPTED_STATUSES,
    VERSION_FLAGS,
    classify_cached_composition_v012,
    prepare_supplemental_v012,
    run_supplemental_v012,
    select_supplemental_sample,
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
        **{flag: False for flag in VERSION_FLAGS},
    }
    return {**base, **overrides}


def _candidate(identifier: int, text: str = "TOKEN_A\nTOKEN_B", **overrides):
    base = {
        "id": identifier,
        "name": "Song",
        "trackName": "Song",
        "artistName": "Artist",
        "albumName": "Synthetic Album",
        "duration": 180.0,
        "instrumental": False,
        "plainLyrics": text,
        "syncedLyrics": None,
    }
    return {**base, **overrides}


def _envelope(get_candidate=None, search_candidates=None):
    return {
        "queried_at": "2026-09-26T00:00:00+00:00",
        "cache_hit": False,
        "cache_reused_current_run": False,
        "requests": [
            {
                "endpoint": "/api/get",
                "http_status": 200 if get_candidate else 404,
                "payload": get_candidate if get_candidate else {"code": 404},
                "attempts": [{"attempt": 1, "http_status": 200 if get_candidate else 404}],
            },
            {
                "endpoint": "/api/search",
                "http_status": 200,
                "payload": search_candidates or [],
                "attempts": [{"attempt": 1, "http_status": 200}],
            },
        ],
    }


def test_twenty_equivalent_search_results_without_get_are_not_accepted():
    search = [_candidate(index) for index in range(1, 21)]
    row = classify_cached_composition_v012(_query(), _envelope(None, search))
    assert row["search_results_truncated"]
    assert not row["exact_compatible_get_with_plain"]
    assert row["final_status"] == "ambiguous_search_truncated"
    assert row["acceptance_depended_exclusively_on_truncated_search"]


def test_twenty_equivalent_search_results_with_exact_get_remain_accepted():
    get = _candidate(100)
    search = [_candidate(index) for index in range(1, 21)]
    row = classify_cached_composition_v012(_query(), _envelope(get, search))
    assert row["search_results_truncated"]
    assert row["exact_compatible_get_with_plain"]
    assert row["final_status"] in ACCEPTED_STATUSES
    assert not row["acceptance_depended_exclusively_on_truncated_search"]


def test_strict_equivalence_is_in_main_v012_collector():
    first = _candidate(1, "TOKEN_A   TOKEN_B\r\n")
    second = _candidate(2, "TOKEN_A TOKEN_B\n")
    row = classify_cached_composition_v012(_query(), _envelope(first, [second]))
    assert row["final_status"] == "accepted_exact_equivalent"


def test_flexible_equivalence_never_accepts_distinct_strict_text():
    first = _candidate(1, "TOKEN!")
    second = _candidate(2, "token")
    assert (
        flexible_plain_text_metrics(first["plainLyrics"])["flexible_text_sha256"]
        == flexible_plain_text_metrics(second["plainLyrics"])["flexible_text_sha256"]
    )
    row = classify_cached_composition_v012(_query(), _envelope(first, [second]))
    assert row["final_status"] == "ambiguous_distinct_lyrics"


def test_real_supplemental_sampling_is_deterministic_and_safe():
    config = load_yaml("configs/lyrics_pilot_v0_1_2.yaml")
    cohort = pl.read_parquet(PROJECT_ROOT / config["inputs"]["cohort"])
    split = pl.read_parquet(PROJECT_ROOT / config["inputs"]["split_assignments"])
    first, first_meta = select_supplemental_sample(cohort, split)
    second, second_meta = select_supplemental_sample(cohort, split)
    assert first.equals(second)
    assert first_meta == second_meta
    assert first.height <= 60
    assert first.get_column("composition_key").n_unique() == first.height
    old_keys = set(cohort.filter(pl.col("smoke_selected")).get_column("composition_key"))
    assert not old_keys & set(first.get_column("composition_key"))
    assert first.get_column("split").unique().to_list() == ["development_train"]
    assert not SUCCESS_FIELDS & set(first.columns)
    assert "raw_exact" not in first.get_column("supplemental_sampling_reason").to_list()


def test_offline_preparation_is_idempotent_and_preserves_frozen_hashes():
    config = load_yaml("configs/lyrics_pilot_v0_1_2.yaml")
    before = _frozen_state()
    first = prepare_supplemental_v012()
    first_hashes = {
        key: sha256_file(PROJECT_ROOT / config["outputs"][key])
        for key in ("supplemental_sample", "smoke_final")
    }
    second = prepare_supplemental_v012()
    second_hashes = {
        key: sha256_file(PROJECT_ROOT / config["outputs"][key])
        for key in ("supplemental_sample", "smoke_final")
    }
    assert first["network_requests_made"] == second["network_requests_made"] == 0
    assert first_hashes == second_hashes
    assert before == _frozen_state()


def test_dry_run_never_queries_network_and_reports_exact_scope():
    plan = run_supplemental_v012(dry_run=True)
    assert plan["network_requests_made"] == 0
    assert plan["supplemental_sample_size"] <= 60
    assert plan["previous_smoke_overlap"] == 0
    assert plan["split_values"] == ["development_train"]


def test_final_public_outputs_have_no_lyrics_or_success_fields():
    config = load_yaml("configs/lyrics_pilot_v0_1_2.yaml")
    result_path = PROJECT_ROOT / config["outputs"]["supplemental_results"]
    if not result_path.exists():
        pytest.skip("Resultado complementar ainda não executado.")
    for key in ("supplemental_sample", "supplemental_results", "smoke_final"):
        frame = pl.read_parquet(PROJECT_ROOT / config["outputs"][key])
        assert not {"plainLyrics", "syncedLyrics", "lyricsfile"} & set(frame.columns)
    sample = pl.read_parquet(PROJECT_ROOT / config["outputs"]["supplemental_sample"])
    assert not SUCCESS_FIELDS & set(sample.columns)


def test_final_cache_count_and_scope_match_sample():
    config = load_yaml("configs/lyrics_pilot_v0_1_2.yaml")
    summary_path = PROJECT_ROOT / config["outputs"]["run_summary"]
    if not summary_path.exists():
        pytest.skip("Execução complementar ainda não concluída.")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["cache_after"]["file_count"] == summary["expected_cache_count"]
    assert summary["expected_cache_count"] <= 160
    assert summary["network_scope"]["original_smoke_requeried"] is False
    assert summary["network_scope"]["holdout_queried"] is False
    assert summary["recommendation"] == "escalar para o restante da coorte de 2.000"


def test_completed_run_is_idempotent_and_uses_only_cache():
    config = load_yaml("configs/lyrics_pilot_v0_1_2.yaml")
    summary_path = PROJECT_ROOT / config["outputs"]["run_summary"]
    if not summary_path.exists():
        pytest.skip("Execução complementar ainda não concluída.")
    public_keys = ("supplemental_sample", "supplemental_results", "smoke_final", "report")
    first = run_supplemental_v012()
    first_hashes = {key: sha256_file(PROJECT_ROOT / config["outputs"][key]) for key in public_keys}
    second = run_supplemental_v012()
    second_hashes = {key: sha256_file(PROJECT_ROOT / config["outputs"][key]) for key in public_keys}
    assert first["network_scope"]["new_compositions_queried_current_run"] == 0
    assert second["network_scope"]["new_compositions_queried_current_run"] == 0
    assert first["supplemental"]["all_results_reused_from_cache_current_run"]
    assert second["supplemental"]["all_results_reused_from_cache_current_run"]
    assert first_hashes == second_hashes


def test_original_smoke_truncation_audit_preserves_safe_acceptances():
    prepared = prepare_supplemental_v012()
    audit = prepared["truncation_audit"]
    assert audit["search_results_truncated_cases"] == 16
    assert audit["accepted_preserved"] == audit["previously_accepted"] == 66
    assert audit["accepted_reclassified"] == 0
    assert audit["truncated_acceptance_depended_exclusively_on_search"] == 0
