from pathlib import Path

import polars as pl

import tcc_music_popularity.config as config_module
from tcc_music_popularity.matching import run_matching
from tcc_music_popularity.normalization import add_normalized_columns


def _flags(frame: pl.DataFrame, prefix: str = "") -> pl.DataFrame:
    marker = f"{prefix}_" if prefix else ""
    missing = [
        f"{marker}{name}"
        for name in (
            "remaster",
            "remix",
            "live",
            "acoustic",
            "radio_edit",
            "mono_stereo",
            "instrumental",
            "demo",
        )
        if f"{marker}{name}" not in frame.columns
    ]
    return frame.with_columns([pl.lit(False).alias(name) for name in missing])


def test_exact_ambiguity_title_false_positive_and_idempotence(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(config_module, "PROJECT_ROOT", tmp_path)
    (tmp_path / "configs").mkdir()
    (tmp_path / "data/processed").mkdir(parents=True)
    (tmp_path / "data/interim").mkdir(parents=True)
    (tmp_path / "reports/tables").mkdir(parents=True)
    (tmp_path / "configs/matching.yaml").write_text(
        "version: v0.1.0\nfuzzy:\n  enabled: false\nreview_sample_size_per_stratum: 2\n",
        encoding="utf-8",
    )
    spotify = pl.DataFrame(
        {
            "spotify_row_id": [1, 2, 3],
            "track_id": ["A" * 22, "B" * 22, "C" * 22],
            "artist_name_raw": ["Artist", "Other", "Band"],
            "track_name_raw": ["Song", "Same", "Track (Live)"],
            "year": [2020, 2020, 2020],
        }
    )
    spotify = _flags(add_normalized_columns(spotify, "artist_name_raw", "track_name_raw"))
    spotify.write_parquet(tmp_path / "data/processed/spotify_tracks.parquet")
    lfm = pl.DataFrame(
        {
            "lfm_record_key": ["l1", "l2", "l3"],
            "artist_name_raw": ["Artist", "Different", "Band"],
            "track_name_raw": ["Song", "Same", "Track (Live)"],
            "lfm_release_year": [2020, 2020, 2020],
        }
    )
    lfm = _flags(
        add_normalized_columns(lfm, "artist_name_raw", "track_name_raw", prefix="lfm"), "lfm"
    )
    lfm = lfm.with_columns(
        pl.when(pl.col("lfm_record_key") == "l3")
        .then(False)
        .otherwise(pl.col("lfm_live"))
        .alias("lfm_live")
    )
    lfm.write_parquet(tmp_path / "data/processed/lfm2b_tracks.parquet")
    first = run_matching()
    assert first["status"] == "created"
    matches = pl.read_parquet(tmp_path / "data/processed/spotify_lfm_matches.parquet")
    assert matches["spotify_track_id"].to_list() == ["A" * 22]
    rejected = pl.read_parquet(tmp_path / "data/processed/spotify_lfm_rejected.parquet")
    assert rejected.filter(pl.col("spotify_track_id") == "C" * 22).height == 1
    status = pl.read_parquet(tmp_path / "data/processed/spotify_tracks_with_match_status.parquet")
    assert status.filter(pl.col("track_id") == "B" * 22)["match_status"][0] == "unmatched"
    assert run_matching()["status"] == "reused"
