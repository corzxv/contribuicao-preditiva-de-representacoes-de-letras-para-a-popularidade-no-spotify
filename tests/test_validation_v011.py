from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest

from tcc_music_popularity.config import PROJECT_ROOT
from tcc_music_popularity.validation_v011 import (
    GROUP_COLUMNS,
    TARGET,
    build_group_assignments,
    deterministic_group_split,
    profile_frame,
)

SOURCE = PROJECT_ROOT / "data/processed/modeling_base_lfm_v0_1.parquet"
MODELING = PROJECT_ROOT / "data/processed/modeling_base_lfm_v0_1_1.parquet"
SPLITS = PROJECT_ROOT / "data/processed/split_assignments_v0_1_1.parquet"
MANIFEST = PROJECT_ROOT / "reports/feature_manifest_v0_1_1.csv"
MODEL_SPEC = PROJECT_ROOT / "reports/tables/model_spec_v0_1_1.json"


def _small_group_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "spotify_row_id": [1, 2, 3, 4],
            "track_id": ["t1", "t2", "t3", "t4"],
            "lfm_record_key": ["l1", "l2", "l3", "l4"],
            "artist_conservative": ["a", "a", "b", "c"],
            "artist_strict": ["a", "a", "b", "c"],
            "artist_primary": ["A", "A", "B", "C"],
            "artist_name_raw": ["A", "A", "B", "C"],
            "composition_key": ["shared", "a|other", "shared", None],
            "lfm_composition_key": ["shared", "a|other", "shared", None],
        }
    )


def test_group_assignments_are_deterministic_and_connect_artist_and_composition() -> None:
    frame = _small_group_frame()
    first = build_group_assignments(frame)
    second = build_group_assignments(frame)
    assert first.equals(second)
    assert first["artist_group_id"][0] == first["artist_group_id"][1]
    assert first["composition_group_id"][0] == first["composition_group_id"][2]
    assert first["split_group_id"][0] == first["split_group_id"][1]
    assert first["split_group_id"][0] == first["split_group_id"][2]
    assert first["composition_group_id"][3] is not None


def test_deterministic_group_split_is_reproducible_and_near_target() -> None:
    sizes = {f"g{index}": size for index, size in enumerate([9, 8, 7, 6, 5, 4, 3, 2, 1])}
    first = deterministic_group_split(sizes, 0.25, 42)
    second = deterministic_group_split(sizes, 0.25, 42)
    assert first == second
    selected = sum(sizes[group] for group in first)
    assert abs(selected / sum(sizes.values()) - 0.25) <= max(sizes.values()) / sum(sizes.values())


def test_profile_detects_constant_and_does_not_treat_missing_as_zero() -> None:
    frame = pl.DataFrame({"constant": [1.0, 1.0, None], "varying": [0.0, None, 2.0]})
    profile = profile_frame(frame, 1e-12)
    assert profile["constant"]["constant"] is True
    assert profile["constant"]["missing"] == 1
    assert profile["varying"]["constant"] is False
    assert profile["varying"]["missing"] == 1


def test_parquet_roundtrip(tmp_path: Path) -> None:
    frame = pl.DataFrame({"track_id": ["a", "b"], TARGET: [10.0, 20.0]})
    path = tmp_path / "roundtrip.parquet"
    frame.write_parquet(path)
    assert pl.read_parquet(path).equals(frame)


@pytest.mark.skipif(
    not all(path.exists() for path in (SOURCE, MODELING, SPLITS, MANIFEST, MODEL_SPEC)),
    reason="Artefatos locais volumosos da Base v0.1.1 não estão disponíveis.",
)
def test_generated_v011_integrity_and_no_group_overlap() -> None:
    source_rows = pl.scan_parquet(SOURCE).select(pl.len()).collect().item()
    matrix = pl.read_parquet(MODELING)
    splits = pl.read_parquet(SPLITS)
    assert matrix.height == source_rows == splits.height
    assert matrix["track_id"].n_unique() == matrix.height
    assert matrix["lfm_record_key"].n_unique() == matrix.height
    assert matrix[TARGET].null_count() == 0
    fraction = (matrix["split"] == "holdout_test").mean()
    assert 0.20 <= fraction <= 0.30
    for column in GROUP_COLUMNS:
        development = set(matrix.filter(pl.col("split") == "development_train")[column].unique())
        holdout = set(matrix.filter(pl.col("split") == "holdout_test")[column].unique())
        assert development.isdisjoint(holdout)


@pytest.mark.skipif(
    not all(path.exists() for path in (MODELING, MANIFEST, MODEL_SPEC)),
    reason="Artefatos locais volumosos da Base v0.1.1 não estão disponíveis.",
)
def test_manifest_matches_matrix_and_features_exclude_target_and_prohibited() -> None:
    schema = set(pl.read_parquet_schema(MODELING))
    manifest = pl.read_csv(MANIFEST)
    included = set(manifest.filter(pl.col("incluída na matriz v0.1.1") == "sim")["nome"].to_list())
    assert included == schema
    spec = json.loads(MODEL_SPEC.read_text(encoding="utf-8"))
    feature_lists = [
        spec["baseline_features"],
        spec["traditional_features"],
        spec["deep_features_current"],
        spec["combined_features_current"],
    ]
    prohibited = set(spec["prohibited_features"])
    for features in feature_lists:
        assert TARGET not in features
        assert prohibited.isdisjoint(features)
        assert set(features).issubset(schema)
    assert spec["traditional_features"] == [
        *spec["baseline_features"],
        *spec["traditional_descriptor_features"],
    ]
    assert prohibited.isdisjoint(spec["traditional_features"])
