"""Synthetic boundaries for the read-only diagnosis; no scientific target files."""

import ast
import inspect

import numpy as np
import polars as pl
import pytest

from tcc_music_popularity import diagnostics_v070 as diag


def test_fixed_bins_include_boundaries_and_keep_raw_outside_predictions():
    values = np.array([-1, 0, 9.999, 10, 89.9, 90, 100, 100.1])
    assert diag.bins10(values).tolist() == [
        "<0",
        "[0,10)",
        "[0,10)",
        "[10,20)",
        "[80,90)",
        "[90,100]",
        "[90,100]",
        ">100",
    ]
    assert len(diag.BIN_LABELS) == 12


def test_nonfinite_values_rejected():
    with pytest.raises(AssertionError, match="Nonfinite"):
        diag.bins10(np.array([np.nan]))
    with pytest.raises(AssertionError, match="Nonfinite"):
        diag.metrics([1, 2], [1, np.inf])


def test_metrics_residual_sign_quantiles_and_thresholds():
    result = diag.metrics([0, 10, 50, 100], [5, 0, 30, 70])
    assert result["mae"] == 16.25
    assert result["mean_residual"] == 13.75
    assert result["rmse"] == pytest.approx(np.sqrt(1425 / 4))
    assert result["ae_median"] == 15
    assert result["ae_p75"] == 22.5
    assert result["ae_p90"] == 27
    assert result["ae_p95"] == pytest.approx(28.5)
    assert [result[f"prop_ae_le_{cut}"] for cut in (5, 10, 20)] == [0.25, 0.5, 0.75]
    assert result["prop_ae_gt_20"] == 0.25
    assert result["count_ae_gt_20"] == 1


def test_empty_constant_and_small_groups_are_explicit():
    assert diag.metrics([], []) == {"n": 0, "small_group": True}
    assert diag.metrics([1, 1], [0, 2])["r2"] is None
    assert diag.metrics([1], [1])["small_group"] is True
    assert diag.metrics(np.arange(30), np.arange(30))["small_group"] is False


@pytest.mark.parametrize("forbidden", sorted(diag.FORBIDDEN_METADATA) + ["embedding_000"])
def test_metadata_rejects_target_proxy_and_embedding_before_file_access(forbidden):
    with pytest.raises(AssertionError):
        diag.metadata("this-file-must-not-be-opened.parquet", ["track_id", forbidden])


def test_metadata_requires_projection_and_reads_only_requested_columns(tmp_path, monkeypatch):
    monkeypatch.setattr(diag, "ROOT", tmp_path)
    pl.DataFrame({"track_id": ["synthetic"], "spotify_popularity": [12345]}).write_parquet(
        tmp_path / "synthetic.parquet"
    )
    with pytest.raises(AssertionError, match="explicit projection"):
        diag.metadata("synthetic.parquet", [])
    read = diag.metadata("synthetic.parquet", ["track_id"])
    assert read.to_dicts() == [{"track_id": "synthetic"}]
    assert diag.READS[-1]["columns"] == ["track_id"]
    assert diag.READS[-1]["target_loaded"] is False
    assert len(diag.READS[-1]["sha256_before"]) == 64


def test_stage_counts_distinguish_rows_tracks_compositions_artists():
    frame = pl.DataFrame(
        {
            "track_id": ["a", "b", "c"],
            "composition_key": ["x", "x", "y"],
            "artist_group_id": ["one"] * 3,
        }
    )
    counts = diag.stage_counts(frame, "synthetic")[0]
    assert (counts["rows"], counts["tracks"], counts["compositions"], counts["artists"]) == (
        3,
        3,
        2,
        1,
    )


def test_diagnostic_source_has_no_fit_tune_or_collection_calls():
    source = ast.parse(inspect.getsource(diag))
    blocked = {
        "fit",
        "fit_transform",
        "partial_fit",
        "train",
        "tune",
        "encode",
        "request",
        "urlopen",
        "create_folds",
    }
    names = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(source)
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute))
    }
    # Encoding a JSON digest is not model embedding generation.
    assert not ((names - {"encode"}) & blocked)
