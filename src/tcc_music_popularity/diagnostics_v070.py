"""Read-only V0.7 diagnosis: saved OOF/holdout predictions, explicit metadata projections.

Run with ``python -m tcc_music_popularity.diagnostics_v070``. No fitting, collection,
sampling, target loading outside the opened V0.5/V0.6 matrices, or UI mutation.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from .config import PROJECT_ROOT, load_sources_config, load_yaml
from .final_study_v040 import load_target_free_source, select_representatives_without_target
from .io import sha256_file, utc_now
from .local_demo import DEVELOPMENT, HOLDOUT, KEYS, MODELS, STUDY, DemoSession, FrozenDemo
from .local_demo_delivery import privacy_audit, scientific_hashes

ROOT = PROJECT_ROOT
PRIVATE = "data/derived/private_diagnostics_v0_7"
FIGURES = "reports/figures/diagnostico_v0_7"
SUMMARY = "reports/run_summary_diagnostico_v0_7.json"
MODEL_NAMES = [*MODELS, "dummy__baseline"]
TARGET = "spotify_popularity"
FLAGS = [
    "remaster",
    "remix",
    "live",
    "acoustic",
    "radio_edit",
    "mono_stereo",
    "instrumental",
    "demo",
]
ARTISTS = {"guns n roses", "adele", "alice in chains"}
FORBIDDEN_METADATA = {
    TARGET,
    "popularity",
    "genius_lyrics_views",
    "lfm_playcount",
    "popularity_quintile",
}
READS: list[dict] = []


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def json_write(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8"
    )


def metadata(path: str, columns: list[str]) -> pl.DataFrame:
    require(bool(columns), "An explicit projection is required")
    require(not FORBIDDEN_METADATA.intersection(columns), "Target/proxy in metadata projection")
    require(not any(c.startswith("embedding_") for c in columns), "Embeddings are not metadata")
    READS.append(
        {
            "path": path,
            "columns": columns,
            "target_loaded": False,
            "sha256_before": sha256_file(ROOT / path),
        }
    )
    return pl.scan_parquet(ROOT / path).select(columns).collect()


def git_state():
    def git(*args):
        result = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        )
        return result.stdout

    paths = git("ls-files", "-z").split("\0") + git(
        "ls-files", "--others", "--exclude-standard", "-z"
    ).split("\0")
    # Exclude only artifacts of this new diagnosis, not the pre-existing personal files.
    hashes = {
        path: sha256_file(ROOT / path)
        for path in paths
        if path and (ROOT / path).is_file() and "v0_7" not in path and "v070" not in path
    }
    return {
        "head": git("rev-parse", "HEAD").strip(),
        "branch": git("branch", "--show-current").strip(),
        "status": git("status", "--short"),
        "staged": git("diff", "--cached", "--name-only"),
        "preexisting_file_hashes": hashes,
    }


def bins10(values: np.ndarray) -> np.ndarray:
    """[0,10), ..., [90,100]; predictions below/above range remain separate."""
    values = np.asarray(values, dtype=float)
    require(np.isfinite(values).all(), "Nonfinite value")
    labels = np.array([f"[{x},{x + 10}{']' if x == 90 else ')'}" for x in range(0, 100, 10)])
    index = np.clip(np.floor(values / 10).astype(int), 0, 9)
    result = labels[index].astype(object)
    result[values < 0] = "<0"
    result[values > 100] = ">100"
    return result


BIN_LABELS = ["<0", *[f"[{x},{x + 10}{']' if x == 90 else ')'}" for x in range(0, 100, 10)], ">100"]


def metrics(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    require(y.shape == p.shape and y.ndim == 1, "Prediction alignment")
    require(np.isfinite(y).all() and np.isfinite(p).all(), "Nonfinite target/prediction")
    n = len(y)
    if not n:
        return {"n": 0, "small_group": True}
    residual, absolute = y - p, np.abs(y - p)
    denominator = float(np.sum((y - y.mean()) ** 2))
    result = {
        "n": n,
        "small_group": n < 30,
        "mae": float(absolute.mean()),
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "r2": float(1 - np.sum(residual**2) / denominator) if n > 1 and denominator else None,
        "mean_residual": float(residual.mean()),
        **{
            f"ae_{name}": float(np.quantile(absolute, q))
            for name, q in (("median", 0.5), ("p75", 0.75), ("p90", 0.9), ("p95", 0.95))
        },
        **{f"prop_ae_le_{cut}": float(np.mean(absolute <= cut)) for cut in (5, 10, 20)},
        "prop_ae_gt_20": float(np.mean(absolute > 20)),
        "count_ae_gt_20": int(np.sum(absolute > 20)),
    }
    for name, values in (("observed", y), ("predicted", p)):
        result.update(
            {
                f"{name}_mean": float(values.mean()),
                f"{name}_std_ddof0": float(values.std()),
                **{
                    f"{name}_{label}": float(np.quantile(values, q))
                    for label, q in (
                        ("min", 0),
                        ("p05", 0.05),
                        ("p25", 0.25),
                        ("p50", 0.5),
                        ("p75", 0.75),
                        ("p95", 0.95),
                        ("max", 1),
                    )
                },
            }
        )
    return result


def stage_counts(frame, stage, split=None):
    frames = (
        [(split or "all", frame)]
        if split
        else [("all", frame)]
        + [
            (s, frame.filter(pl.col("split") == s))
            for s in ("development_train", "holdout_test")
            if "split" in frame.columns
        ]
    )
    result = []
    for label, part in frames:
        row = {"stage": stage, "split": label, "rows": part.height}
        for column, name in (
            ("track_id", "tracks"),
            ("composition_key", "compositions"),
            ("artist_group_id", "artists"),
        ):
            row[name] = part[column].drop_nulls().n_unique() if column in part.columns else None
        row["special_versions"] = (
            int(
                part.select(
                    pl.any_horizontal([pl.col(f).fill_null(False) for f in FLAGS]).sum()
                ).item()
            )
            if all(f in part.columns for f in FLAGS)
            else None
        )
        result.append(row)
    return result


def add_groups(frame, artist_sizes):
    if "artist_group_size" not in frame.columns:
        frame = frame.join(artist_sizes, on="artist_group_id", how="left", validate="m:1")
    return frame.with_columns(
        pl.when(pl.col("year") < 2000)
        .then(pl.lit("<2000"))
        .when(pl.col("year") < 2010)
        .then(pl.lit("2000-2009"))
        .when(pl.col("year") < 2020)
        .then(pl.lit("2010-2019"))
        .otherwise(pl.lit("2020-2023"))
        .alias("period_diag"),
        pl.when(pl.col("artist_group_size") == 1)
        .then(pl.lit("1"))
        .when(pl.col("artist_group_size") <= 5)
        .then(pl.lit("2-5"))
        .when(pl.col("artist_group_size") <= 20)
        .then(pl.lit("6-20"))
        .otherwise(pl.lit("21+"))
        .alias("artist_size_bin"),
        pl.any_horizontal([pl.col(f).fill_null(False) for f in FLAGS]).alias("any_version"),
    )


def coverage():
    cfg = load_yaml(ROOT / "configs/final_scale_v0_4.yaml")
    source = load_target_free_source(cfg)
    for path, cols in zip(
        (
            cfg["inputs"]["modeling_base"],
            cfg["inputs"]["split_assignments"],
            cfg["inputs"]["matching_audit"],
        ),
        __import__(
            "tcc_music_popularity.final_study_v040", fromlist=["_source_columns"]
        )._source_columns(),
        strict=True,
    ):
        READS.append(
            {
                "path": path,
                "columns": cols,
                "target_loaded": False,
                "sha256_before": sha256_file(ROOT / path),
            }
        )
    reps, rep_audit = select_representatives_without_target(source)
    sizes = reps.select("artist_group_id", "artist_group_size").unique()
    source, reps = add_groups(source, sizes), add_groups(reps, sizes)
    sample_cols = KEYS + ["sampling_role", "reserve_batch", "sampling_order_within_split"]
    main = metadata(f"{STUDY}/final_cohort_v1_0.parquet", sample_cols)
    reserve = metadata(f"{STUDY}/final_reserve_v1_0.parquet", sample_cols)
    selected = pl.concat([main, reserve], how="vertical_relaxed")
    selected_meta = reps.join(selected, on=KEYS, how="inner", validate="1:1", suffix="_sample")
    require(selected_meta.height == 16000, "Sample/reps join")
    lyric_cols = [
        "composition_key",
        "representative_track_id",
        "representative_spotify_row_id",
        "final_status",
        "selected_lrclib_id",
        "selected_returned_artist",
        "selected_returned_title",
        "selected_returned_album",
        "selected_returned_duration_seconds",
        "selected_duration_difference_seconds",
        "selected_strict_text_sha256",
        "http_status",
        "attempts",
        "candidate_count_after_endpoint_union",
        "compatible_candidate_count",
    ]
    lyrics = metadata(f"{STUDY}/final_lyrics_results_v0_4.parquet", lyric_cols).rename(
        {"representative_track_id": "track_id", "representative_spotify_row_id": "spotify_row_id"}
    )
    queried = selected_meta.join(lyrics, on=KEYS, how="inner", validate="1:1")
    accepted = queried.filter(pl.col("final_status").str.starts_with("accepted"))
    dev_keys = metadata(
        f"{DEVELOPMENT}/development_matrix.parquet", KEYS + ["artist_group_id", "split"]
    )
    hold_keys = metadata(
        f"{DEVELOPMENT}/holdout_features.parquet", KEYS + ["artist_group_id", "split"]
    )
    matrix_keys = pl.concat([dev_keys, hold_keys])
    final = accepted.join(matrix_keys.select(KEYS), on=KEYS, how="inner", validate="1:1")
    require(
        (source.height, reps.height, queried.height, accepted.height, final.height)
        == (111758, 111422, 15000, 10240, 10240),
        "Frozen funnel mismatch",
    )
    stages = {
        "integrated": source,
        "eligible_representatives": reps,
        "main_selected": selected_meta.filter(pl.col("sampling_role") == "main"),
        "reserve_available": selected_meta.filter(pl.col("sampling_role") == "reserve"),
        "queried_main_and_reserve": queried,
        "lyrics_accepted": accepted,
        "final_matrix": final,
        "demo_catalog": final.filter(pl.col("split") == "holdout_test"),
    }
    counts = [row for name, frame in stages.items() for row in stage_counts(frame, name)]
    strata = []
    for stage, frame in stages.items():
        for group in (
            "genre",
            "period_diag",
            "match_method",
            "any_version",
            "artist_size_bin",
            *FLAGS,
        ):
            for row in frame.group_by("split", group).len().sort(["split", group]).to_dicts():
                strata.append(
                    {
                        "stage": stage,
                        "split": row["split"],
                        "dimension": group,
                        "group": str(row[group]),
                        "n": row["len"],
                    }
                )
    split_violations = {
        column: source.filter(pl.col(column).is_not_null())
        .group_by(column)
        .agg(pl.col("split").n_unique().alias("n"))
        .filter(pl.col("n") > 1)
        .height
        for column in ("artist_group_id", "composition_key", "split_group_id")
    }
    require(not any(split_violations.values()), "Cross-split groups")
    return (
        stages,
        {
            "funnel": counts,
            "representatives": rep_audit,
            "strata": strata,
            "lyrics_statuses": queried.group_by("split", "final_status")
            .len()
            .sort(["split", "final_status"])
            .to_dicts(),
            "cross_split_groups": split_violations,
        },
        matrix_keys,
    )


def source_trace(stages):
    cols = [
        "spotify_row_id",
        "track_id",
        "artist_name_raw",
        "track_name_raw",
        "artist_conservative",
        "artist_primary",
        "composition_key",
        "year",
        "genre",
        "match_status",
        *FLAGS,
    ]
    spotify = metadata("data/processed/spotify_tracks_with_match_status.parquet", cols)
    spotify = spotify.with_columns(
        pl.col("composition_key").count().over("composition_key").alias("source_versions_per_key")
    )
    raw_path = load_sources_config()["spotify"]["local_path"]
    raw_cols = ["artist_name", "track_name", "track_id", "year", "genre"]
    READS.append(
        {
            "path": raw_path,
            "columns": raw_cols,
            "target_loaded": False,
            "infer_schema": False,
            "sha256_before": sha256_file(ROOT / raw_path),
        }
    )
    raw = (
        pl.scan_csv(ROOT / raw_path, infer_schema=False)
        .select(raw_cols)
        .with_row_index("spotify_row_id", offset=1)
        .collect()
    )
    require(raw.height == spotify.height, "Source/normalized count mismatch")
    cases = spotify.filter(pl.col("artist_conservative").is_in(sorted(ARTISTS)))
    raw_cases = raw.filter(pl.col("spotify_row_id").is_in(cases["spotify_row_id"].implode()))
    raw_compare = raw_cases.join(cases, on=["spotify_row_id", "track_id"], validate="1:1")
    require(
        raw_compare.height == cases.height
        and raw_compare.filter(
            (pl.col("artist_name") != pl.col("artist_name_raw"))
            | (pl.col("track_name") != pl.col("track_name_raw"))
            | (pl.col("year").cast(pl.Int64) != pl.col("year_right"))
        ).height
        == 0,
        "Case raw metadata changed",
    )
    integrated = stages["integrated"]
    reps = stages["eligible_representatives"]
    sampled = pl.concat(
        [stages["main_selected"], stages["reserve_available"]], how="diagonal_relaxed"
    )
    queried = stages["queried_main_and_reserve"]
    final = stages["final_matrix"]
    app = stages["demo_catalog"]
    by_stage = {
        name: {row["spotify_row_id"]: row for row in frame.to_dicts()}
        for name, frame in (
            ("integrated", integrated),
            ("representative", reps),
            ("sampled", sampled),
            ("queried", queried),
            ("final", final),
            ("app", app),
        )
    }
    rows = []
    counts = []
    for artist in sorted(ARTISTS):
        artist_rows = cases.filter(pl.col("artist_conservative") == artist)
        original_count = stage_counts(artist_rows, "source")[0]
        original_count["artists"] = artist_rows["artist_conservative"].n_unique()
        counts.append({"artist": artist, **original_count})
        for stage, frame in stages.items():
            sub = frame.filter(
                pl.col("spotify_row_id").is_in(artist_rows["spotify_row_id"].implode())
            )
            counts.extend({"artist": artist, **row} for row in stage_counts(sub, stage))
    for row in cases.sort(["artist_conservative", "track_name_raw", "spotify_row_id"]).to_dicts():
        sid = row["spotify_row_id"]
        reason = ""
        if sid not in by_stage["integrated"]:
            reason = f"matching_{row['match_status']}; não entrou na base integrada"
        elif sid not in by_stage["representative"]:
            reason = (
                "sem composition_key"
                if not row["composition_key"]
                else "outro representante da mesma chave foi preferido"
            )
        elif sid not in by_stage["sampled"]:
            reason = "não selecionado pela ordem hash da amostra principal/reserva"
        elif sid not in by_stage["queried"]:
            reason = "reserva não ativada; nenhum alvo aberto neste diagnóstico"
        elif sid not in by_stage["final"]:
            reason = f"letra não aceita: {by_stage['queried'][sid]['final_status']}"
        elif sid not in by_stage["app"]:
            reason = "matriz de desenvolvimento; app só exibe holdout"
        else:
            reason = "presente no demonstrador"
        rows.append(
            {
                **row,
                **{f"in_{stage}": sid in mapping for stage, mapping in by_stage.items()},
                "reason": reason,
                "split": by_stage["integrated"].get(sid, {}).get("split"),
                "artist_group_id": by_stage["integrated"].get(sid, {}).get("artist_group_id"),
                "final_status": by_stage["queried"].get(sid, {}).get("final_status"),
            }
        )
    json_write(f"{PRIVATE}/artist_track_trace.json", rows)
    artist_groups = (
        integrated.filter(pl.col("spotify_row_id").is_in(cases["spotify_row_id"].implode()))
        .group_by("artist_name_raw")
        .agg(
            pl.col("artist_group_id").n_unique().alias("artist_groups"),
            pl.col("split").n_unique().alias("split_count"),
            pl.col("split").unique().alias("splits"),
        )
    )
    uncertain = spotify.filter(
        pl.col("track_name_raw").str.contains(r"(?i)\b(unplugged|recorded at|concert|session)\b")
        & ~pl.any_horizontal([pl.col(f).fill_null(False) for f in FLAGS])
    )
    json_write(f"{PRIVATE}/version_context_without_flag.json", uncertain.select(cols).to_dicts())
    artist_version_groups = []
    for key, part in cases.group_by("composition_key", maintain_order=True):
        if part.height > 1:
            artist_version_groups.append(
                {
                    "composition_key": key[0],
                    "source_versions": part.height,
                    "accepted_versions": part.filter(
                        pl.col("spotify_row_id").is_in(integrated["spotify_row_id"].implode())
                    ).height,
                    "representative": reps.filter(pl.col("composition_key") == key[0])
                    .select(
                        "spotify_row_id",
                        "track_id",
                        "track_name_raw",
                        "match_status",
                        "match_method",
                        "match_score",
                        "live",
                        "remix",
                        "acoustic",
                        "karaoke",
                    )
                    .to_dicts(),
                }
            )
    json_write(f"{PRIVATE}/artist_composition_version_groups.json", artist_version_groups)
    # JSON preserves flags and nullable metadata without embedding/lyric text.
    candidate_cols = [
        "spotify_track_id",
        "spotify_row_id",
        "lfm_record_key",
        "match_method",
        "match_score",
        "version_compatible",
        "temporal_compatible",
        "candidate_reason",
        "spotify_candidate_count",
        "lfm_spotify_count",
        "match_status",
        "acceptance_reason",
    ]
    candidates = metadata("data/processed/spotify_lfm_all_candidates.parquet", candidate_cols)
    json_write(
        f"{PRIVATE}/matching_candidates_artists.json",
        candidates.filter(
            pl.col("spotify_row_id").is_in(cases["spotify_row_id"].implode())
        ).to_dicts(),
    )
    audit_cols = KEYS + [
        "lfm_record_key",
        "lfm_artist_name_raw",
        "lfm_track_name_raw",
        "lfm_composition_key",
        "lfm_release_year",
        "temporal_compatible",
        "temporal_year_difference_abs",
        *[f"lfm_{f}" for f in FLAGS],
    ]
    audit = metadata("data/processed/matching_audit_v0_1_1.parquet", audit_cols)
    case_audit = integrated.filter(
        pl.col("spotify_row_id").is_in(cases["spotify_row_id"].implode())
    ).join(audit, on=KEYS, validate="1:1", suffix="_audit")
    json_write(f"{PRIVATE}/matched_artists_audio_lfm.json", case_audit.to_dicts())
    json_write(
        f"{PRIVATE}/artists_lrclib_metadata.json",
        queried.filter(
            pl.col("spotify_row_id").is_in(cases["spotify_row_id"].implode())
        ).to_dicts(),
    )
    # Lexical diagnostic only: version titles are not an adjudicated ground truth.
    signals = {
        "live_context": r"(?i)(?:\blive\s+(?:at|in|from|on)\b|\(live\)|-\s*live\b)",
        "remaster_context": r"(?i)\bremaster(?:ed)?\b",
        "remix_context": r"(?i)\bremix\b",
    }
    flag_audit = []
    for stage, frame in {"source": spotify, **stages}.items():
        for name, pattern in signals.items():
            flag = name.split("_")[0]
            match = pl.col("track_name_raw").str.contains(pattern).fill_null(False)
            flag_audit.append(
                {
                    "stage": stage,
                    "signal": name,
                    "n": frame.height,
                    "signal_count": frame.filter(match).height,
                    "signal_without_flag": frame.filter(
                        match & ~pl.col(flag).fill_null(False)
                    ).height,
                    "flag_without_specific_context": frame.filter(
                        ~match & pl.col(flag).fill_null(False)
                    ).height,
                }
            )
    special_cases = case_audit.filter(
        pl.col("track_name_raw")
        .str.to_lowercase()
        .str.contains("street of dreams|make you feel my love|junkhead")
    )
    candidate_special = cases.filter(
        pl.col("composition_key").is_in(special_cases["composition_key"].implode())
    )
    json_write(f"{PRIVATE}/case_representative_alternatives.json", candidate_special.to_dicts())
    # Original LFM metadata: examine version flags before integration without descriptors/proxies.
    lfm_cols = [
        "lfm_record_key",
        "artist_name_raw",
        "track_name_raw",
        "lfm_artist_conservative",
        "lfm_composition_key",
        "lfm_release_year",
        *[f"lfm_{f}" for f in FLAGS],
    ]
    lfm = metadata("data/processed/lfm2b_tracks.parquet", lfm_cols)
    lfm_case = lfm.filter(pl.col("lfm_artist_conservative").is_in(sorted(ARTISTS)))
    json_write(f"{PRIVATE}/original_lfm_artist_metadata.json", lfm_case.to_dicts())
    # Coverage association, not a causal effect: count original rows by number of versions.
    mult = spotify.with_columns(
        pl.when(pl.col("source_versions_per_key") == 1)
        .then(pl.lit("1"))
        .when(pl.col("source_versions_per_key") <= 5)
        .then(pl.lit("2-5"))
        .otherwise(pl.lit("6+"))
        .alias("versions_bin")
    )
    return (
        {
            "original_source_rows": raw.height,
            "source_unique_tracks": spotify["track_id"].n_unique(),
            "source_unique_compositions": spotify["composition_key"].drop_nulls().n_unique(),
            "source_normalized_artists": spotify["artist_conservative"].drop_nulls().n_unique(),
            "raw_year_min": int(raw["year"].cast(pl.Int64).min()),
            "raw_year_max": int(raw["year"].cast(pl.Int64).max()),
            "raw_outside_2000_2023": raw.filter(
                ~pl.col("year").cast(pl.Int64).is_between(2000, 2023)
            ).height,
            "source_matching_statuses": spotify.group_by("match_status")
            .len()
            .sort("match_status")
            .to_dicts(),
            "artist_stage_counts": counts,
            "artist_aliases": cases.select(
                "artist_name_raw", "artist_conservative", "artist_primary"
            )
            .unique()
            .sort("artist_name_raw")
            .to_dicts(),
            "flag_signals": flag_audit,
            "artist_group_fragmentation": artist_groups.to_dicts(),
            "version_context_without_any_flag": {
                "n_source": uncertain.height,
                "n_integrated": uncertain.join(
                    integrated.select("spotify_row_id"),
                    on="spotify_row_id",
                    how="inner",
                    validate="1:1",
                ).height,
                "n_final": uncertain.join(
                    final.select("spotify_row_id"), on="spotify_row_id", how="inner", validate="1:1"
                ).height,
                "definition": "title contains unplugged/recorded at/concert/session, all eight stored flags false; candidates for review, not confirmed errors",
            },
            "matching_by_version_count": mult.group_by("versions_bin", "match_status")
            .len()
            .sort(["versions_bin", "match_status"])
            .to_dicts(),
            "case_rows": special_cases.to_dicts(),
        },
        spotify,
        cases,
    )


def errors(stages):
    pred_cols = [f"prediction__{m}" for m in MODEL_NAMES]
    dev = pl.read_parquet(
        ROOT / DEVELOPMENT / "oof_predictions.parquet",
        columns=["composition_key", "track_id", TARGET, "outer_fold", *pred_cols],
    )
    dev_targets = pl.read_parquet(
        ROOT / DEVELOPMENT / "development_matrix.parquet",
        columns=["composition_key", "track_id", TARGET],
    )
    aligned = dev.select("composition_key", "track_id", TARGET).join(
        dev_targets,
        on=["composition_key", "track_id"],
        how="left",
        validate="1:1",
        suffix="_matrix",
    )
    require(
        aligned.height == dev.height
        and aligned[f"{TARGET}_matrix"].null_count() == 0
        and aligned.filter(pl.col(TARGET) != pl.col(f"{TARGET}_matrix")).height == 0,
        "OOF target key alignment",
    )
    hold = pl.read_parquet(
        ROOT / HOLDOUT / "predictions_pre_target.parquet", columns=[*KEYS, *pred_cols]
    ).join(
        pl.read_parquet(
            ROOT / HOLDOUT / "holdout_target_raw.parquet",
            columns=["track_id", "spotify_row_id", TARGET],
        ),
        on=["track_id", "spotify_row_id"],
        how="left",
        validate="1:1",
        maintain_order="left",
    )
    require(dev.height == 7648 and hold.height == 2592, "Saved prediction count")
    require(
        dev["outer_fold"].null_count() == 0 and dev["outer_fold"].n_unique() == 5,
        "OOF fold provenance",
    )
    meta_cols = [*KEYS, "genre", "period_diag", "any_version", *FLAGS, "artist_group_id"]
    meta = stages["final_matrix"].select(meta_cols)
    dev = dev.join(
        meta, on=["composition_key", "track_id"], how="left", validate="1:1", maintain_order="left"
    )
    hold = hold.join(meta, on=KEYS, how="left", validate="1:1", maintain_order="left")
    records, correlations, distributions, reconciliation = [], [], [], []
    summary06 = json.loads(
        (ROOT / "reports/run_summary_final_holdout_v0_6.json").read_text(encoding="utf-8")
    )
    official = {r["model"]: r for r in summary06["metrics"]}
    for name, frame in (("development_oof", dev), ("holdout_v0_6", hold)):
        require(
            frame[TARGET].null_count() == 0 and frame["genre"].null_count() == 0,
            "Target/metadata alignment",
        )
        y = frame[TARGET].to_numpy()
        for label in BIN_LABELS[1:-1]:
            distributions.append(
                {
                    "set": name,
                    "bin": label,
                    "n": int(np.sum(bins10(y) == label)),
                    "denominator": len(y),
                }
            )
        for cut in (40, 60, 80):
            distributions.append(
                {"set": name, "bin": f">{cut}", "n": int(np.sum(y > cut)), "denominator": len(y)}
            )
        for model in MODEL_NAMES:
            p = frame[f"prediction__{model}"].to_numpy()
            values = metrics(y, p)
            records.append(
                {"set": name, "model": model, "dimension": "overall", "group": "all", **values}
            )
            for metric in ("mae", "rmse", "r2"):
                expected = official[model][
                    metric if name == "holdout_v0_6" else f"development_{metric}"
                ]
                difference = abs(values[metric] - expected)
                require(difference <= 1e-10, f"Metric reconciliation {name} {model} {metric}")
                reconciliation.append(
                    {"set": name, "model": model, "metric": metric, "abs_difference": difference}
                )
            groups = {
                "target_bin": bins10(y),
                "prediction_bin": bins10(p),
                **{
                    c: np.asarray(frame[c].cast(pl.String).fill_null("ausente").to_list())
                    for c in ("genre", "period_diag", "any_version", *FLAGS)
                },
            }
            for dimension, labels in groups.items():
                levels = BIN_LABELS if dimension.endswith("_bin") else sorted(set(labels))
                for level in levels:
                    select = labels == level
                    records.append(
                        {
                            "set": name,
                            "model": model,
                            "dimension": dimension,
                            "group": str(level),
                            **metrics(y[select], p[select]),
                        }
                    )
        for a, b in itertools.combinations(MODEL_NAMES[:4], 2):
            pa, pb = frame[f"prediction__{a}"].to_numpy(), frame[f"prediction__{b}"].to_numpy()
            delta = np.abs(pa - pb)
            correlations.append(
                {
                    "set": name,
                    "a": a,
                    "b": b,
                    "n": len(pa),
                    "pearson": float(np.corrcoef(pa, pb)[0, 1]),
                    "mean_abs_difference": float(delta.mean()),
                    "median_abs_difference": float(np.median(delta)),
                    "p95_abs_difference": float(np.quantile(delta, 0.95)),
                    "max_abs_difference": float(delta.max()),
                    "prop_abs_difference_gt_5": float(np.mean(delta > 5)),
                }
            )
    frame = pl.from_dicts(records, infer_schema_length=None)
    (ROOT / FIGURES).mkdir(parents=True, exist_ok=True)
    create_plots(frame, {"development_oof": dev, "holdout_v0_6": hold})
    # Avoid releasing individual observations via n=1/very small aggregate cells.
    private_path = ROOT / PRIVATE / "all_group_metrics.json"
    json_write(private_path, records)
    numeric = [
        c
        for c in frame.columns
        if c not in ("set", "model", "dimension", "group", "n", "small_group")
    ]
    public = frame.with_columns(
        [pl.when(pl.col("small_group")).then(None).otherwise(pl.col(c)).alias(c) for c in numeric]
    )
    public.write_csv(ROOT / "reports/diagnostico_erros_agregados_v0_7.csv")
    return {
        "overall": frame.filter(pl.col("dimension") == "overall").to_dicts(),
        "target_distribution": distributions,
        "prediction_comparisons": correlations,
        "reconciliation": reconciliation,
        "small_group_policy": "n<30: n published, numeric metrics only in local private artifact; all bins retained",
        "quantile_method": "numpy linear",
        "std_ddof": 0,
        "public_group_metrics": public.filter(
            pl.col("dimension").is_in(
                ["target_bin", "prediction_bin", "period_diag", "any_version"]
            )
        ).to_dicts(),
    }


def create_plots(aggregated, frames):
    for kind in ("distribuicoes", "erro_acumulado", "erro_por_alvo", "observado_por_previsao"):
        fig, axes = plt.subplots(1, 2, figsize=(14, 5), layout="constrained")
        for ax, (set_name, frame) in zip(axes, frames.items(), strict=True):
            y = frame[TARGET].to_numpy()
            if kind == "distribuicoes":
                edges = np.arange(-10, 111, 10)
                ax.stairs(
                    np.histogram(y, bins=edges)[0] / len(y),
                    edges,
                    label="Observado",
                    color="black",
                    linewidth=2,
                )
            for model in MODEL_NAMES:
                p = frame[f"prediction__{model}"].to_numpy()
                label = MODELS.get(model, "Dummy")
                color = f"C{MODEL_NAMES.index(model)}"
                if kind == "distribuicoes":
                    ax.stairs(np.histogram(p, bins=edges)[0] / len(p), edges, label=label)
                elif kind == "erro_acumulado":
                    # Only aggregate grid percentages, not an individual-order ECDF export.
                    grid = np.arange(0, 101)
                    ax.plot(grid, [np.mean(np.abs(y - p) <= v) for v in grid], label=label)
                else:
                    dimension = "target_bin" if kind == "erro_por_alvo" else "prediction_bin"
                    data = aggregated.filter(
                        (pl.col("set") == set_name)
                        & (pl.col("model") == model)
                        & (pl.col("dimension") == dimension)
                        & (pl.col("n") >= 30)
                    )
                    rows = [r for r in data.to_dicts() if r["group"] in BIN_LABELS[1:-1]]
                    x = [BIN_LABELS.index(r["group"]) * 10 - 5 for r in rows]
                    if kind == "erro_por_alvo":
                        ax.plot(
                            x,
                            [r["mae"] for r in rows],
                            marker="o",
                            label=f"{label} MAE",
                            color=color,
                        )
                        if model == "elastic_net__baseline":
                            ax.set_xticks(
                                x, [f"{r['group']}\nn={r['n']}" for r in rows], fontsize=8
                            )
                        ax.plot(
                            x,
                            [r["mean_residual"] for r in rows],
                            linestyle=":",
                            label=f"{label} resíduo",
                            color=color,
                        )
                    else:
                        ax.plot(
                            [r["predicted_mean"] for r in rows],
                            [r["observed_mean"] for r in rows],
                            marker="o",
                            label=label,
                        )
                        if model == "elastic_net__traditional":
                            for row in rows:
                                ax.annotate(
                                    f"n={row['n']}",
                                    (row["predicted_mean"], row["observed_mean"]),
                                    fontsize=7,
                                    xytext=(2, 4),
                                    textcoords="offset points",
                                )
            if kind == "observado_por_previsao":
                ax.plot([0, 80], [0, 80], "--", color="gray", label="Identidade")
            if kind == "erro_por_alvo":
                ax.axhline(0, color="gray", linewidth=0.7)
            labels = {
                "distribuicoes": (
                    "Popularidade / previsão bruta",
                    "Fração no intervalo de 10 pontos",
                ),
                "erro_acumulado": ("Erro absoluto (pontos)", "Proporção ≤ limiar"),
                "erro_por_alvo": (
                    "Centro da faixa do alvo observado",
                    "MAE / resíduo médio (obs − prev)",
                ),
                "observado_por_previsao": (
                    "Previsão média na faixa de previsão",
                    "Observado médio na faixa de previsão",
                ),
            }
            ax.set(
                xlabel=labels[kind][0], ylabel=labels[kind][1], title=f"{set_name} · n={len(y):,}"
            )
            ax.grid(alpha=0.2)
            ax.legend(fontsize=7, ncol=2)
        note = (
            "células n<30 omitidas"
            if kind in ("erro_por_alvo", "observado_por_previsao")
            else "todas as observações; distribuições agregadas"
        )
        fig.suptitle(f"V0.7 · diagnóstico exploratório; não é nova avaliação · {note}")
        fig.savefig(ROOT / FIGURES / f"{kind}.png", dpi=150)
        plt.close(fig)


def case_inference(source_cases, stages):
    demo = FrozenDemo()
    case_keys = [
        row["composition_key"]
        for row in source_cases
        if any(
            term in row["track_name_raw"].lower()
            for term in ("street of dreams", "make you feel my love", "junkhead")
        )
    ]
    require(len(case_keys) == 3, "Expected three matched reported cases")
    all_features = list(
        dict.fromkeys(c for spec in demo.specs.values() for c in spec["input_columns"])
    )
    # Authorized development only; target deliberately excluded for support inspection.
    training = pl.read_parquet(
        ROOT / DEVELOPMENT / "development_matrix.parquet", columns=all_features
    )
    output, pipeline_audit = [], []
    state = DemoSession()
    for key in case_keys:
        row = demo.by_composition[key]
        state.select(key)
        require(
            state.predictions == {} and state.observed is None, "State not cleared on selection"
        )
        state.estimate(demo)
        require(state.observed is None, "Target revealed prematurely")
        state.reveal(demo)
        features = (
            pl.scan_parquet(demo.features_path)
            .filter(demo._filter(row))
            .select(KEYS + all_features)
            .collect()
        )
        baseline_lfm = [c for c in all_features if not c.startswith("embedding_")]
        frozen_base = (
            pl.scan_parquet(ROOT / "data/processed/modeling_base_lfm_v0_1_1.parquet")
            .select(["track_id", "spotify_row_id", *baseline_lfm])
            .filter(
                (pl.col("track_id") == row["track_id"])
                & (pl.col("spotify_row_id") == row["spotify_row_id"])
            )
            .collect()
        )
        require(
            frozen_base.height == 1
            and frozen_base.select(baseline_lfm).equals(features.select(baseline_lfm)),
            "Frozen features/base association",
        )
        saved = (
            pl.scan_parquet(demo.predictions_path)
            .filter(demo._filter(row))
            .select([f"prediction__{m}" for m in MODELS])
            .collect()
            .row(0, named=True)
        )
        item = {
            "metadata": row,
            "observed": state.observed,
            "predictions": state.predictions.copy(),
            "absolute_errors": {m: abs(state.observed - p) for m, p in state.predictions.items()},
            "difference_from_saved": {
                m: state.predictions[m] - saved[f"prediction__{m}"] for m in MODELS
            },
            "ui_two_decimals": {m: f"{p:.2f}" for m, p in state.predictions.items()},
            "state_clear_verified": True,
            "pipeline_diagnostics": {},
            "baseline_lfm_equal_frozen_base": True,
            "frozen_input_row_sha256": hashlib.sha256(
                features.select(all_features).write_json().encode()
            ).hexdigest(),
        }
        for name, spec in demo.specs.items():
            model = demo._models[name]
            inputs = features.select(spec["input_columns"])
            require(
                inputs.columns == spec["input_columns"]
                and all(str(inputs.schema[c]) == spec["input_schema"][c] for c in inputs.columns),
                "Input schema/order",
            )
            transformer = model.named_steps["representation"]
            pre = transformer.named_steps["preprocess"]
            unknown, imputed, outside, components = {}, [], [], {}
            embedding_outside = 0
            for block, pipe, columns in pre.transformers_:
                if block == "remainder":
                    continue
                steps = pipe.named_steps
                encoder = next(
                    (step for step in steps.values() if hasattr(step, "categories_")), None
                )
                if encoder is not None:
                    for column, categories in zip(columns, encoder.categories_, strict=True):
                        value = inputs[column][0]
                        if value is not None and value not in categories:
                            unknown[column] = str(value)
                pca = steps.get("pca")
                if pca is not None:
                    components[block] = {
                        "n_components": int(pca.n_components_),
                        "n_samples": int(pca.n_samples_),
                    }
                for column in columns:
                    value = inputs[column][0]
                    if value is None or (isinstance(value, float) and not np.isfinite(value)):
                        imputed.append(column)
                    elif column.startswith("embedding_"):
                        low, high = training[column].min(), training[column].max()
                        embedding_outside += int(value < low or value > high)
                    elif column not in ("genre", "key", "time_signature") and not column.startswith(
                        "embedding_"
                    ):
                        low, high = training[column].min(), training[column].max()
                        if low is not None and (value < low or value > high):
                            outside.append(
                                {
                                    "feature": column,
                                    "value": value,
                                    "train_min": low,
                                    "train_max": high,
                                }
                            )
            with threadpool_limits(limits=1):
                transformed = transformer.transform(inputs)
            names = np.asarray(pre.get_feature_names_out())[
                transformer.named_steps["variance"].get_support()
            ]
            coefficients = np.asarray(model.named_steps["model"].coef_)
            contributions = np.asarray(transformed)[0] * coefficients
            intercept = float(model.named_steps["model"].intercept_)
            reconstructed = float(contributions.sum() + intercept)
            require(abs(reconstructed - state.predictions[name]) < 1e-8, "Linear decomposition")
            require(
                len(names) == spec["coefficients"]["total"],
                "Transformed dimension differs from manifest",
            )
            for block, pca_data in components.items():
                expected = spec["pca_components"]["lfm" if block == "traditional" else "embedding"]
                require(
                    pca_data["n_components"] == expected and pca_data["n_samples"] == 7648,
                    "Frozen PCA differs from manifest",
                )
            contribution_rows = [
                {"transformed_feature": str(n), "contribution_points": float(c)}
                for n, c in zip(names, contributions, strict=True)
            ]
            contribution_rows.sort(key=lambda r: abs(r["contribution_points"]), reverse=True)
            details = {
                "input_features": len(inputs.columns),
                "input_schema_confirmed": True,
                "input_columns": inputs.columns,
                "unknown_categories": unknown,
                "imputed_features": imputed,
                "outside_training_numeric_range_excluding_embeddings": outside,
                "embedding_dimensions_outside_training_range_count": embedding_outside,
                "pca": components,
                "transformed_features": len(names),
                "intercept": intercept,
                "contribution_sum": float(contributions.sum()),
                "prediction_reconstructed": reconstructed,
                "contributions": contribution_rows,
                "block_contributions": {
                    block: float(
                        sum(
                            c
                            for n, c in zip(names, contributions, strict=True)
                            if str(n).startswith(block + "__")
                        )
                    )
                    for block in pre.named_transformers_
                    if block != "remainder"
                },
            }
            item["pipeline_diagnostics"][name] = details
            if key == case_keys[0]:
                pipeline_audit.append(
                    {
                        "model": name,
                        "input_features": len(inputs.columns),
                        "transformed_features": len(names),
                        "pca": components,
                        "blocks": [
                            {"name": block, "input_columns": columns}
                            for block, _, columns in pre.transformers_
                            if block != "remainder"
                        ],
                    }
                )
        output.append(item)
    state.select(None)
    require(not state.predictions and state.observed is None, "Selection None did not clear")
    require(
        {r["composition_key"] for r in demo.catalog}
        == set(stages["demo_catalog"]["composition_key"]),
        "Application subset changed",
    )
    json_write(f"{PRIVATE}/reported_cases_inference.json", output)
    return {
        "cases_checked": len(output),
        "state_clear_verified": True,
        "input_order_types_verified": True,
        "max_difference_saved": max(
            abs(d) for r in output for d in r["difference_from_saved"].values()
        ),
        "observed_join_keys": ["track_id", "spotify_row_id"],
        "atol": 1e-8,
        "rtol": 1e-10,
        "pipelines": pipeline_audit,
        "case_details_path": f"{PRIVATE}/reported_cases_inference.json",
    }


def future_evaluation(stages, matrix_keys):
    all_split = metadata(
        "data/processed/split_assignments_v0_1_1.parquet",
        KEYS + ["artist_group_id", "composition_group_id", "split_group_id", "split"],
    )
    historical_paths = [
        "data/processed/lyrics_pilot_cohort_v0_1.parquet",
        "data/processed/lyrics_pilot_supplemental_sample_v0_1_2.parquet",
        "data/derived/private_modeling/modeling_pilot_matrix_v0_3.parquet",
        "data/derived/private_modeling/modeling_recalibration_oof_predictions_v0_3_1.parquet",
    ]
    historical_keys = set(matrix_keys["composition_key"])
    usage = []
    for path in historical_paths:
        frame = metadata(path, ["composition_key"])
        historical_keys.update(frame["composition_key"].drop_nulls())
        usage.append(
            {
                "path": path,
                "rows": frame.height,
                "compositions": frame["composition_key"].n_unique(),
            }
        )
    # The user's earlier exported head included popularity. Read only IDs now, not its targets.
    preview_path = "preview_100_linhas.csv"
    preview = (
        pl.scan_csv(ROOT / preview_path, separator=";", infer_schema=False)
        .select("track_id")
        .collect()
    )
    READS.append(
        {
            "path": preview_path,
            "columns": ["track_id"],
            "target_loaded": False,
            "sha256_before": sha256_file(ROOT / preview_path),
            "infer_schema": False,
        }
    )
    usage.append(
        {
            "path": preview_path,
            "rows": preview.height,
            "projection": ["track_id"],
            "reason": "historical head exported with target; IDs only in this diagnosis",
        }
    )
    used = all_split.filter(
        pl.col("composition_key").is_in(sorted(historical_keys))
        | pl.col("track_id").is_in(preview["track_id"].implode())
    )
    used_artists = set(used["artist_group_id"])
    used_components = set(used["split_group_id"])
    used_compositions = set(used["composition_group_id"])
    remaining = all_split.filter(
        ~pl.col("artist_group_id").is_in(sorted(used_artists))
        & ~pl.col("split_group_id").is_in(sorted(used_components))
        & ~pl.col("composition_group_id").is_in(sorted(used_compositions))
    )
    eligible = stages["eligible_representatives"].join(
        remaining.select(KEYS), on=KEYS, how="inner", validate="1:1"
    )
    json_write(
        f"{PRIVATE}/historically_unused_metadata_candidates.json",
        eligible.select(
            KEYS
            + [
                "artist_group_id",
                "composition_group_id",
                "split_group_id",
                "split",
                "year",
                "genre",
            ]
        ).to_dicts(),
    )
    prior_sample = pl.concat(
        [
            stages["main_selected"].select("artist_group_id", "split_group_id"),
            stages["reserve_available"].select("artist_group_id", "split_group_id"),
        ]
    ).unique()
    conservative = eligible.filter(
        ~pl.col("artist_group_id").is_in(prior_sample["artist_group_id"].implode())
        & ~pl.col("split_group_id").is_in(prior_sample["split_group_id"].implode())
    )
    json_write(
        f"{PRIVATE}/not_previously_sampled_group_candidates.json",
        conservative.select(KEYS + ["artist_group_id", "split_group_id", "split"]).to_dicts(),
    )
    return {
        "historical_usage": usage,
        "used_groups": {
            "artists": len(used_artists),
            "connected_split_groups": len(used_components),
        },
        "metadata_only_candidates": stage_counts(eligible, "no_known_model_or_pilot_groups"),
        "not_previously_sampled_groups": stage_counts(
            conservative, "also_excludes_v04_cohort_and_reserve_groups"
        ),
        "new_test_sampled": False,
        "new_targets_loaded": False,
        "independence_certified": False,
        "other_historical_inspection_artifacts_not_opened": [
            "base_preview.xlsx",
            "reports/base_preview.xlsx",
            "preview_5_linhas_todas_310_colunas.json",
            "reports/match_review_sample_v0_1_1.xlsx",
            "reports/match_review_sample_v0_1_1_revision.xlsx",
        ],
        "caveat": "Identificadores sem uso conhecido em piloto/modelos, não um novo teste: alvos da fonte/base já foram perfilados agregadamente nas V0.1/V0.1.1; toda a fonte participou do desenho do matching. V0.6 não reutilizável como avaliação independente de revisões.",
    }


def main():
    (ROOT / PRIVATE).mkdir(parents=True, exist_ok=True)
    old_git = git_state()
    before = scientific_hashes(ROOT)
    json_write(f"{PRIVATE}/preservation_before.json", {"git": old_git, "scientific_hashes": before})
    print("V0.7: metadata-only coverage", flush=True)
    stages, funnel, matrix_keys = coverage()
    print("V0.7: source and artist traces", flush=True)
    trace, _, _ = source_trace(stages)
    source_cases = trace.pop("case_rows")
    print("V0.7: saved OOF and opened holdout diagnostics", flush=True)
    error_summary = errors(stages)
    print("V0.7: three frozen inference cases", flush=True)
    inference = case_inference(source_cases, stages)
    future = future_evaluation(stages, matrix_keys)
    after = scientific_hashes(ROOT)
    for read in READS:
        require(
            sha256_file(ROOT / read["path"]) == read["sha256_before"],
            f"Source changed: {read['path']}",
        )
    current_git = git_state()
    require(before == after, "Frozen scientific artifact changed")
    require(
        old_git["head"] == current_git["head"] and old_git["staged"] == current_git["staged"],
        "Git changed",
    )
    require(
        all(sha256_file(ROOT / p) == h for p, h in old_git["preexisting_file_hashes"].items()),
        "Pre-existing/personal file changed",
    )
    privacy = privacy_audit(ROOT)
    result = {
        "version": "v0.7",
        "status": "diagnostics_computed",
        "completed_at": utc_now(),
        "coverage": funnel,
        "source_trace": trace,
        "errors": error_summary,
        "demonstrator": inference,
        "future_evaluation": future,
        "metadata_read_projections": READS,
        "target_scope": ["development_oof_v0_5", "holdout_opened_v0_6"],
        "training_calls": 0,
        "new_collections": 0,
        "preservation": {
            "scientific_artifacts": len(before),
            "hashes_unchanged": True,
            "preexisting_files": len(old_git["preexisting_file_hashes"]),
            "personal_changes_preserved": True,
            "head": old_git["head"],
            "branch": old_git["branch"],
            "commit_or_push": False,
        },
        "privacy": privacy,
        "private_directory": PRIVATE,
        "figure_hashes": {p.name: sha256_file(p) for p in sorted((ROOT / FIGURES).glob("*.png"))},
        "verification_commands": [],
        "limitations": [
            "No authoritative recording/lyric identity or first-release year",
            "No new target exposure outside authorized final matrices",
            "Groups n<30 have counts only in shareable metrics",
            "OOF and opened V0.6 are exploratory for future revisions",
        ],
    }
    json_write(SUMMARY, result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "scientific_files_preserved": len(before),
                "case_max_prediction_difference": inference["max_difference_saved"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
