from __future__ import annotations

import json

import polars as pl
import pytest

from tcc_music_popularity.config import PROJECT_ROOT
from tcc_music_popularity.revision_v011 import (
    HUMAN_FIELDS,
    _temporal_statistics,
    build_special_cases,
)

AUDIT = PROJECT_ROOT / "data/processed/matching_audit_v0_1_1.parquet"
SOURCE = PROJECT_ROOT / "data/processed/modeling_base_lfm_v0_1.parquet"
SPLIT = PROJECT_ROOT / "data/processed/split_assignments_v0_1_1.parquet"
SUMMARY = PROJECT_ROOT / "reports/run_summary_v0_1_1_revision.json"
MANIFEST = PROJECT_ROOT / "reports/feature_manifest_v0_1_1_revision.csv"


def test_valid_temporal_statistics_ignore_implausible_year_without_mutating_raw() -> None:
    frame = pl.DataFrame(
        {
            "year": [2000, 2000, 2000],
            "lfm_release_year": [2000, -18, 1998],
            "lfm_qf_release_year_implausible": [False, True, False],
        }
    )
    raw = _temporal_statistics(frame, ignore_implausible=False)
    valid = _temporal_statistics(frame, ignore_implausible=True)
    assert raw["statistics"]["non_null"] == 3
    assert raw["statistics"]["maximum"] == 2018
    assert valid["statistics"]["non_null"] == 2
    assert valid["statistics"]["missing"] == 1
    assert valid["statistics"]["maximum"] == 2
    assert frame["lfm_release_year"].to_list() == [2000, -18, 1998]


@pytest.mark.skipif(
    not all(path.exists() for path in (AUDIT, SOURCE)),
    reason="Artefatos locais da Base v0.1.1 não estão disponíveis.",
)
def test_special_cases_are_complete_deduplicated_and_blank() -> None:
    special = build_special_cases(pl.read_parquet(AUDIT), pl.read_parquet(SOURCE))
    assert special.filter(pl.col("flag_ano_lfm_implausivel")).height == 16
    assert special.filter(pl.col("flag_composition_key_ausente")).height == 22
    assert (
        special.filter(
            pl.col("flag_ano_lfm_implausivel") & pl.col("flag_composition_key_ausente")
        ).height
        == 0
    )
    assert special.height == 38
    assert special["spotify_row_id"].n_unique() == 38
    assert special["track_id"].n_unique() == 38
    for field in HUMAN_FIELDS:
        assert special[field].to_list() == [""] * 38


@pytest.mark.skipif(
    not all(path.exists() for path in (SUMMARY, MANIFEST, SPLIT)),
    reason="Artefatos revisados ainda não foram gerados.",
)
def test_revision_manifest_and_summary_preserve_split_and_exclude_entropy() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    manifest = pl.read_csv(MANIFEST)
    entropy = manifest.filter(pl.col("nome") == "lfm_entropy").row(0, named=True)
    compression = manifest.filter(pl.col("nome") == "lfm_compression_ratio").row(0, named=True)
    assert entropy["papel"] == "auditoria"
    assert entropy["modelo em que poderá entrar"] == "nenhum"
    assert entropy["autorizada como preditora na revisão"] == "não"
    assert entropy["incluída na matriz v0.1.1"] == "sim"
    assert compression["semântica confirmada"] == "sim"
    assert compression["autorizada como preditora na revisão"] == "sim"
    revised = summary["model_spec_revision"]["authorized_feature_lists"]
    assert "lfm_entropy" not in revised["traditional_descriptor_features"]
    assert "lfm_entropy" not in revised["traditional_features"]
    assert summary["model_spec_revision"]["counts"]["traditional_before"] == 220
    assert summary["model_spec_revision"]["counts"]["traditional_after"] == 219
    assert summary["split_verification"]["identical"] is True
