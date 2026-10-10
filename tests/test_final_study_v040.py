from __future__ import annotations

import polars as pl

from tcc_music_popularity.final_study_v040 import (
    FORBIDDEN_SAMPLING_COLUMNS,
    SEED,
    _source_columns,
    build_representativity,
    deterministic_main_and_reserve,
    select_representatives_without_target,
)


def _representatives(rows: int = 40) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "composition_key": [f"composition-{index}" for index in range(rows)],
            "split": ["development_train"] * (rows // 2) + ["holdout_test"] * (rows // 2),
            "artist_group_id": [f"artist-{index // 2}" for index in range(rows)],
            "spotify_row_id": list(range(rows)),
            "track_id": [f"track-{index}" for index in range(rows)],
            "lfm_record_key": [f"lfm-{index}" for index in range(rows)],
            "year": [2000 + index % 20 for index in range(rows)],
            "genre": ["rock" if index % 2 else "pop" for index in range(rows)],
            "genre_sampling": ["rock" if index % 2 else "pop" for index in range(rows)],
            "period": ["2000-2005"] * rows,
            "duration_ms": [180000 + index for index in range(rows)],
            "match_method": ["raw_exact"] * rows,
            "artist_group_size": [2] * rows,
            "remaster": [False] * rows,
            "remix": [False] * rows,
            "live": [False] * rows,
            "acoustic": [False] * rows,
            "radio_edit": [False] * rows,
            "mono_stereo": [False] * rows,
            "instrumental": [False] * rows,
            "demo": [False] * rows,
            "karaoke": [False] * rows,
        }
    )


def test_sampling_projection_never_requests_target_or_success_proxy():
    columns = set().union(*_source_columns())
    assert not (FORBIDDEN_SAMPLING_COLUMNS & columns)
    assert "spotify_popularity" not in columns


def test_main_and_reserve_are_exact_disjoint_and_idempotent():
    frame = _representatives()
    arguments = {
        "seed": SEED,
        "main_counts": {"development_train": 10, "holdout_test": 6},
        "reserve_counts": {"development_train": 4, "holdout_test": 2},
    }
    first_main, first_reserve = deterministic_main_and_reserve(frame, **arguments)
    second_main, second_reserve = deterministic_main_and_reserve(frame, **arguments)
    assert first_main.equals(second_main)
    assert first_reserve.equals(second_reserve)
    assert first_main.height == 16
    assert first_reserve.height == 6
    assert not (set(first_main["composition_key"]) & set(first_reserve["composition_key"]))
    assert first_main.group_by("split").len().sort("split")["len"].to_list() == [10, 6]
    assert first_reserve.group_by("split").len().sort("split")["len"].to_list() == [4, 2]


def test_representative_rule_does_not_receive_popularity_and_prefers_original():
    source = pl.DataFrame(
        [
            {
                "spotify_row_id": 2,
                "track_id": "live",
                "lfm_record_key": "l2",
                "composition_key": "artist|||song",
                "artist_group_id": "artist",
                "composition_group_id": "composition",
                "split_group_id": "split-group",
                "split": "development_train",
                "split_random_state": 1,
                "split_version": "v1",
                "year": 2010,
                "genre": "rock",
                "duration_ms": 200000,
                "artist_name_raw": "Artist",
                "track_name_raw": "Song (Live)",
                "match_method": "raw_exact",
                "match_score": 1.0,
                "match_status": "accepted_high_confidence",
                "version_compatible": True,
                "matching_version": "v1",
                "remaster": False,
                "remix": False,
                "live": True,
                "acoustic": False,
                "radio_edit": False,
                "mono_stereo": False,
                "instrumental": False,
                "demo": False,
            },
            {
                "spotify_row_id": 1,
                "track_id": "original",
                "lfm_record_key": "l1",
                "composition_key": "artist|||song",
                "artist_group_id": "artist",
                "composition_group_id": "composition",
                "split_group_id": "split-group",
                "split": "development_train",
                "split_random_state": 1,
                "split_version": "v1",
                "year": 2010,
                "genre": "rock",
                "duration_ms": 200000,
                "artist_name_raw": "Artist",
                "track_name_raw": "Song",
                "match_method": "raw_exact",
                "match_score": 1.0,
                "match_status": "accepted_high_confidence",
                "version_compatible": True,
                "matching_version": "v1",
                "remaster": False,
                "remix": False,
                "live": False,
                "acoustic": False,
                "radio_edit": False,
                "mono_stereo": False,
                "instrumental": False,
                "demo": False,
            },
        ]
    )
    representatives, audit = select_representatives_without_target(source)
    assert representatives.height == 1
    assert representatives["track_id"].item() == "original"
    assert audit["target_columns_loaded"] == []


def test_representativity_is_aggregate_and_target_free():
    frame = _representatives()
    report = build_representativity(frame, frame.head(20))
    assert "numeric" in report and "categorical" in report
    assert "spotify_popularity" not in str(report)
