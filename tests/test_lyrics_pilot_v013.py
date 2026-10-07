from __future__ import annotations

import json

import polars as pl
import pytest

from tcc_music_popularity.config import PROJECT_ROOT, load_yaml
from tcc_music_popularity.io import sha256_file
from tcc_music_popularity.lyrics_pilot import _frozen_state
from tcc_music_popularity.lyrics_pilot_v013 import (
    PUBLIC_FORBIDDEN_FIELDS,
    circuit_breaker_reason,
    full_preflight,
    run_full_pilot_v013,
    validate_lrclib_envelope,
    wilson_interval,
)


def _config():
    return load_yaml("configs/lyrics_pilot_v0_1_3.yaml")


def _candidate(identifier: int = 1):
    return {
        "id": identifier,
        "trackName": "Synthetic Song",
        "artistName": "Synthetic Artist",
        "albumName": "Synthetic Album",
        "duration": 180.0,
        "instrumental": False,
        "plainLyrics": "SYNTHETIC_ONLY",
        "syncedLyrics": None,
    }


def _envelope(*, get_status=200, search_status=200, attempts=1):
    return {
        "requests": [
            {
                "endpoint": "/api/get",
                "http_status": get_status,
                "payload": _candidate() if get_status == 200 else {},
                "attempts": [
                    {"attempt": index + 1, "http_status": get_status} for index in range(attempts)
                ],
            },
            {
                "endpoint": "/api/search",
                "http_status": search_status,
                "payload": [_candidate()] if search_status == 200 else {},
                "attempts": [
                    {"attempt": index + 1, "http_status": search_status}
                    for index in range(attempts)
                ],
            },
        ]
    }


def test_schema_guard_accepts_expected_shape_and_rejects_change():
    validate_lrclib_envelope(_envelope())
    malformed = _envelope()
    malformed["requests"][1]["payload"] = {"unexpected": True}
    with pytest.raises(ValueError, match="schema_change"):
        validate_lrclib_envelope(malformed)


def test_circuit_breaker_stops_after_ten_consecutive_errors():
    reason = circuit_breaker_reason(["request_error"] * 10, _envelope(), _config())
    assert reason == "10_consecutive_technical_errors"


def test_circuit_breaker_stops_above_twenty_percent_in_last_fifty():
    error_positions = set(range(0, 44, 4))
    statuses = [
        "request_error" if index in error_positions else "accepted_exact_unique"
        for index in range(50)
    ]
    reason = circuit_breaker_reason(statuses, _envelope(), _config())
    assert reason == "request_error_rate_above_20_percent_in_last_50"


def test_circuit_breaker_stops_on_persistent_429():
    reason = circuit_breaker_reason(
        ["request_error"], _envelope(get_status=429, attempts=3), _config()
    )
    assert reason == "persistent_429_after_retries"


def test_wilson_interval_is_bounded_and_contains_observed_rate():
    low, high = wilson_interval(70, 100)
    assert 0 <= low < 0.70 < high <= 1
    assert wilson_interval(0, 0) == (0.0, 0.0)


def test_real_preflight_recalculates_scope_without_network():
    before = _frozen_state()
    preflight = full_preflight()
    counts = preflight["counts"]
    assert counts["cohort_rows"] == counts["unique_compositions"] == 2000
    assert counts["missing_composition_keys"] == counts["duplicate_compositions"] == 0
    assert counts["cached_in_cohort"] >= 147
    assert counts["cached_in_cohort"] + counts["remaining_without_cache"] == 2000
    assert counts["caches_outside_cohort"] == counts["holdout_rows"] == 0
    assert counts["split_values"] == ["development_train"]
    assert before == _frozen_state()


def test_dry_run_has_no_network_and_exact_real_scope():
    plan = run_full_pilot_v013(dry_run=True)
    assert plan["network_requests_made"] == 0
    assert plan["preflight"]["cohort_rows"] == 2000
    assert plan["new_compositions_planned"] == plan["preflight"]["remaining_without_cache"]


def test_final_outputs_are_complete_private_and_idempotent():
    config = _config()
    summary_path = PROJECT_ROOT / config["outputs"]["run_summary"]
    if not summary_path.exists():
        pytest.skip("Coleta completa v0.1.3 ainda não concluída.")
    stored = json.loads(summary_path.read_text(encoding="utf-8"))
    if stored.get("status") != "complete":
        pytest.skip("Coleta completa v0.1.3 ainda não concluída.")
    first = run_full_pilot_v013()
    first_hashes = {
        key: sha256_file(PROJECT_ROOT / config["outputs"][key])
        for key in ("full_results", "full_report", "selection_bias_report")
    }
    second = run_full_pilot_v013()
    second_hashes = {
        key: sha256_file(PROJECT_ROOT / config["outputs"][key])
        for key in ("full_results", "full_report", "selection_bias_report")
    }
    frame = pl.read_parquet(PROJECT_ROOT / config["outputs"]["full_results"])
    assert first["result_rows"] == second["result_rows"] == frame.height == 2000
    assert first["cache_after"]["file_count"] == second["cache_after"]["file_count"] == 2000
    assert first["collection"]["queried_current_run"] == 0
    assert second["collection"]["queried_current_run"] == 0
    assert first_hashes == second_hashes
    assert not PUBLIC_FORBIDDEN_FIELDS & set(frame.columns)
    assert first["network_scope"]["holdout_queried"] is False
    assert first["privacy"]["tracked_private_files"] == []
    assert first["privacy"]["staged_private_files"] == []
