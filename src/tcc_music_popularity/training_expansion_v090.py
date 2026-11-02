"""V0.9: development-only analytical base and fixed-configuration learning curves."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import polars as pl
import sklearn
from threadpoolctl import threadpool_limits

from .final_study_v040 import load_target_free_source, select_representatives_without_target
from .modeling_pilot_v030 import FeatureBlocks
from .statistical_revision_v080 import fit_model, metrics, prepare_partition

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = Path("data/derived/private_training_expansion_v0_9")
PROTOCOL = Path("reports/protocolo_ampliacao_treino_v0_9.md")
FIGURES = Path("reports/figures/ampliacao_v0_9")
PUBLIC = {
    PROTOCOL,
    *(
        Path(f"reports/{name}")
        for name in (
            "base_analitica_ampliada_v0_9.md",
            "cobertura_popularidade_v0_9.csv",
            "curvas_aprendizagem_v0_9.csv",
            "experimento_ampliacao_v0_9.md",
            "run_summary_ampliacao_v0_9.json",
        )
    ),
}
BASE = Path("data/processed/modeling_base_lfm_v0_1_1.parquet")
SPLIT = Path("data/processed/split_assignments_v0_1_1.parquet")
MATCH = Path("data/processed/matching_audit_v0_1_1.parquet")
STUDY = Path("data/derived/private_final_study")
DEV = Path("data/derived/private_final_development_v0_5")
MANIFEST = Path("reports/final_model_manifest_v0_5.json")
CODE = Path("src/tcc_music_popularity/training_expansion_v090.py")
REPORT_CODE = Path("src/tcc_music_popularity/training_expansion_report_v090.py")
IDS = ["track_id", "spotify_row_id", "lfm_record_key"]
GROUPS = ["artist_group_id", "composition_key", "composition_group_id", "split_group_id"]
TARGET = "spotify_popularity"
SEEDS = (20261015, 20261016)
SIZES = (2000, 5000, 10000, 20000)
BLOCKS = ("baseline", "traditional")
FORBIDDEN = {
    TARGET,
    "genius_lyrics_views",
    "lfm_playcount",
    "embedding",
    "plain_lyrics",
    "synced_lyrics",
}
READS = []
HASH_SOURCES = (
    (
        STUDY / "final_lyrics_results_v0_4.parquet",
        "representative_track_id",
        "selected_strict_text_sha256",
        "strict",
    ),
    (
        Path("data/processed/lyrics_pilot_full_results_v0_1_3.parquet"),
        "representative_track_id",
        "selected_strict_text_sha256",
        "strict",
    ),
    (
        Path("data/processed/lyrics_pilot_supplemental_results_v0_1_2.parquet"),
        "representative_track_id",
        "selected_strict_text_sha256",
        "strict",
    ),
    (
        Path("data/processed/lyrics_pilot_smoke_results_v0_1.parquet"),
        "representative_track_id",
        "lyrics_sha256",
        "smoke_raw",
    ),
    (
        Path("data/derived/private_embeddings/lyrics_embeddings_minilm_v0_2.parquet"),
        "track_id",
        "lyrics_sha256",
        "normalized",
    ),
    (
        STUDY / "final_embeddings_development_v0_4.parquet",
        "track_id",
        "lyrics_sha256",
        "normalized",
    ),
    (STUDY / "final_embeddings_holdout_v0_4.parquet", "track_id", "lyrics_sha256", "normalized"),
)


def ensure(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.now(UTC).isoformat()


def digest(path):
    with (ROOT / path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def output(path):
    resolved = (ROOT / path).resolve()
    relative = resolved.relative_to(ROOT)
    ensure(
        relative in PUBLIC or relative.is_relative_to(PRIVATE) or relative.is_relative_to(FIGURES),
        "Escrita fora da V0.9",
    )
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_json(path, value):
    dest = output(path)
    temporary = dest.with_suffix(dest.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    temporary.replace(dest)


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout.decode(
        "utf-8"
    )


def metadata(path, columns, *, development=False):
    ensure(
        not FORBIDDEN.intersection(columns), "Leitura de metadados inclui alvo/vetor/letra/proxy"
    )
    query = pl.scan_parquet(ROOT / path)
    if development:
        query = query.filter(pl.col("split") == "development_train")
    frame = query.select(columns).collect()
    READS.append(
        {
            "path": str(path),
            "columns": columns,
            "development_filter": development,
            "target_loaded": False,
        }
    )
    return frame


def development_features(columns):
    ensure(
        not {"genius_lyrics_views", "lfm_playcount", "embedding"}.intersection(columns),
        "Proxy/vetor proibido",
    )
    # This predicate is applied before any target-bearing frame is materialized.
    query = (
        pl.scan_parquet(ROOT / BASE).filter(pl.col("split") == "development_train").select(columns)
    )
    frame = query.collect()
    ensure(
        frame["split"].unique().to_list() == ["development_train"], "Alvo fora do desenvolvimento"
    )
    READS.append(
        {
            "path": BASE.as_posix(),
            "columns": columns,
            "development_filter": True,
            "target_loaded": TARGET in columns,
            "returned_rows": frame.height,
        }
    )
    return frame


def feature_blocks():
    manifest = read_json(MANIFEST)
    allowed = manifest["allowed_features"]
    blocks = FeatureBlocks(tuple(allowed["baseline"]), tuple(allowed["lfm"]), (), {})
    configs = {}
    for block in BLOCKS:
        old = next(row for row in manifest["models"] if row["model"] == f"elastic_net__{block}")
        ensure(old["input_columns"] == blocks.columns(block), "Inputs divergentes do manifesto")
        ensure(
            old["params"] == {"alpha": 0.003, "l1_ratio": 0.95},
            "Configuração final V0.5 diverge do protocolo",
        )
        configs[block] = old["params"]
    ensure(
        len(blocks.baseline) == 23 and len(blocks.traditional) == 196,
        "Contagem de preditoras divergente",
    )
    ensure(
        not set(blocks.columns("traditional")) & (FORBIDDEN | set(IDS) | set(GROUPS)),
        "Input proibido",
    )
    return blocks, configs


def hash_catalog(assignments):
    rows = []
    for path, track, column, kind in HASH_SOURCES:
        frame = metadata(path, [track, "composition_key", column]).rename(
            {track: "track_id", column: "lyrics_hash"}
        )
        frame = frame.filter(pl.col("lyrics_hash").is_not_null() & (pl.col("lyrics_hash") != ""))
        rows.append(
            frame.with_columns(
                pl.lit(kind).alias("hash_kind"), pl.lit(path.as_posix()).alias("source")
            )
        )
    catalog = pl.concat(rows, how="vertical_relaxed").unique()
    catalog = catalog.join(
        assignments.select(
            "track_id", pl.col("composition_key").alias("assigned_composition"), "split"
        ),
        on="track_id",
        how="left",
        validate="m:1",
    )
    ensure(catalog["split"].null_count() == 0, "Hash de track não localizado no split")
    ensure(
        (catalog["composition_key"] == catalog["assigned_composition"]).all(),
        "Hash ligado a composição divergente",
    )
    return catalog.drop("assigned_composition").with_columns(
        pl.concat_str("hash_kind", "lyrics_hash", separator=":").alias("hash_key")
    )


def load_base():
    blocks, _ = feature_blocks()
    assignments = metadata(SPLIT, [*IDS, *GROUPS, "split"])
    ensure(assignments["track_id"].n_unique() == assignments.height, "Track duplicado no split")
    for group in GROUPS:
        crossing = (
            assignments.filter(pl.col(group).is_not_null())
            .group_by(group)
            .agg(pl.col("split").n_unique().alias("n"))
            .filter(pl.col("n") > 1)
            .height
        )
        ensure(crossing == 0, f"Grupo cruza split: {group}")
    # Reuse the exact prior target-free metadata/representative implementation.
    source = load_target_free_source(
        {
            "inputs": {
                "modeling_base": BASE.as_posix(),
                "split_assignments": SPLIT.as_posix(),
                "matching_audit": MATCH.as_posix(),
            }
        }
    )
    READS.append(
        {"path": "V0.4 load_target_free_source", "target_loaded": False, "columns": source.columns}
    )
    dev_meta = source.filter(pl.col("split") == "development_train")
    reps_meta, rep_audit = select_representatives_without_target(dev_meta)
    cols = list(
        dict.fromkeys(
            [
                *IDS,
                *[g for g in GROUPS if g != "composition_key"],
                "split",
                TARGET,
                *blocks.columns("traditional"),
            ]
        )
    )
    raw = development_features(cols)
    for group in ["artist_group_id", "composition_group_id", "split_group_id", "split"]:
        checked = raw.select(*IDS, group).join(
            assignments.select(*IDS, pl.col(group).alias("assigned")), on=IDS, validate="1:1"
        )
        ensure(
            checked.height == raw.height and (checked[group] == checked["assigned"]).all(),
            f"Alocação divergente: {group}",
        )
    ensure(
        raw.height == dev_meta.height and raw["track_id"].n_unique() == raw.height,
        "Faixas perdidas/duplicadas",
    )
    tracks = raw.join(
        dev_meta.select([*IDS, *[c for c in dev_meta.columns if c not in raw.columns]]),
        on=IDS,
        how="left",
        validate="1:1",
    )
    quality = metadata(
        MATCH,
        [
            *IDS,
            "lfm_artist_name_raw",
            "lfm_track_name_raw",
            "lfm_release_year",
            "temporal_compatible",
            "lfm_qf_release_year_implausible",
        ],
        development=True,
    )
    tracks = tracks.join(quality, on=IDS, how="left", validate="1:1")
    frames = []
    for name in ("final_cohort_v1_0.parquet", "final_reserve_v1_0.parquet"):
        frames.append(
            metadata(
                STUDY / name,
                [*IDS, "composition_key", "sampling_role", "reserve_batch"],
                development=True,
            )
        )
    selected = pl.concat(frames, how="vertical_relaxed")
    check = selected.join(
        reps_meta.select(*IDS, "composition_key"),
        on=[*IDS, "composition_key"],
        how="inner",
        validate="1:1",
    )
    ensure(check.height == selected.height, "Representantes diferem da V0.4")
    results = metadata(
        STUDY / "final_lyrics_results_v0_4.parquet",
        [
            "representative_track_id",
            "representative_spotify_row_id",
            "composition_key",
            "final_status",
            "http_status",
            "selected_strict_text_sha256",
        ],
        development=True,
    ).rename(
        {"representative_track_id": "track_id", "representative_spotify_row_id": "spotify_row_id"}
    )
    tracks = tracks.join(
        selected.select("track_id", "sampling_role", "reserve_batch"),
        on="track_id",
        how="left",
        validate="1:1",
    )
    tracks = tracks.join(
        results.drop("composition_key"),
        on=["track_id", "spotify_row_id"],
        how="left",
        validate="1:1",
    )
    catalog = hash_catalog(assignments)
    hash_counts = (
        catalog.filter(pl.col("split") == "development_train")
        .group_by("track_id")
        .agg(pl.col("hash_key").n_unique().alias("known_hash_count"))
    )
    tracks = (
        tracks.join(hash_counts, on="track_id", how="left", validate="1:1")
        .with_columns(
            pl.col("known_hash_count").fill_null(0),
            pl.col("final_status").fill_null("not_queried"),
            pl.col("sampling_role").fill_null("not_selected"),
            (pl.col("composition_key").is_not_null() & (pl.col("composition_key") != "")).alias(
                "composition_key_available"
            ),
            pl.col("track_id")
            .is_in(reps_meta["track_id"].implode())
            .alias("is_operational_representative"),
        )
        .with_columns(
            pl.col("final_status").str.starts_with("accepted").alias("lyrics_accepted_v04")
        )
    )
    tracks = tracks.sort("track_id")
    reps = tracks.filter(pl.col("is_operational_representative")).sort("composition_key")
    common_columns = [
        "composition_key",
        "track_id",
        "spotify_row_id",
        "artist_group_id",
        "split",
        "lyrics_sha256",
        TARGET,
        *blocks.columns("traditional"),
    ]
    common = (
        pl.scan_parquet(ROOT / DEV / "development_matrix.parquet")
        .filter(pl.col("split") == "development_train")
        .select(common_columns)
        .collect()
    )
    READS.append(
        {
            "path": (DEV / "development_matrix.parquet").as_posix(),
            "columns": common_columns,
            "development_filter": True,
            "target_loaded": True,
            "returned_rows": common.height,
        }
    )
    ensure(common.height == 7648, "Coorte comum alterada")
    comparison = common.select("track_id").join(
        reps, on="track_id", how="left", validate="1:1", maintain_order="left"
    )
    for column in [
        "composition_key",
        "spotify_row_id",
        "artist_group_id",
        TARGET,
        *blocks.columns("traditional"),
    ]:
        ensure(
            comparison[column].cast(common.schema[column]).equals(common[column]),
            f"Comum não coincide com base: {column}",
        )
    folds = metadata(
        DEV / "fold_assignments.parquet", ["composition_key", "artist_group_id", "outer_fold"]
    )
    common = common.join(
        folds,
        on=["composition_key", "artist_group_id"],
        how="left",
        validate="1:1",
        maintain_order="left",
    )
    ensure(common["outer_fold"].null_count() == 0, "Fold ausente")
    ensure(set(common["outer_fold"]) == set(range(5)), "Folds externos divergentes")
    ensure(
        reps.filter(pl.col("lyrics_accepted_v04")).height == 7648,
        "Letras aceitas diferem da coorte comum",
    )
    tracks = tracks.with_columns(
        pl.col("track_id").is_in(common["track_id"].implode()).alias("in_common_v05")
    )
    reps = reps.with_columns(
        pl.col("track_id").is_in(common["track_id"].implode()).alias("in_common_v05")
    )
    audit = {
        "development_tracks": tracks.height,
        "eligible_compositions": reps.height,
        "common_compositions": common.height,
        "additional_compositions": reps.height - common.height,
        "representative_audit": rep_audit,
        "duplicate_track_ids": tracks.height - tracks["track_id"].n_unique(),
        "identifier_audit": {
            column: {
                "missing": tracks[column].null_count(),
                "distinct": tracks[column].drop_nulls().n_unique(),
                "repeated_rows": tracks.height - tracks[column].n_unique(),
            }
            for column in IDS
        },
        "lfm_records_linked_to_multiple_tracks": tracks.group_by("lfm_record_key")
        .agg(pl.col("track_id").n_unique().alias("tracks"))
        .filter(pl.col("tracks") > 1)
        .height,
        "compositions_linked_to_multiple_artists": tracks.filter(
            pl.col("composition_key_available")
        )
        .group_by("composition_key")
        .agg(pl.col("artist_group_id").n_unique().alias("artists"))
        .filter(pl.col("artists") > 1)
        .height,
        "missing_groups": {g: tracks[g].null_count() for g in GROUPS},
        "tracks_per_composition_max": int(
            tracks.filter(pl.col("composition_key_available"))
            .group_by("composition_key")
            .len()["len"]
            .max()
        ),
        "missing_predictors": {c: tracks[c].null_count() for c in blocks.columns("traditional")},
        "nonfinite_predictors": {
            c: int((~tracks[c].drop_nulls().is_finite()).sum())
            for c in blocks.columns("traditional")
            if tracks.schema[c].is_numeric()
        },
        "missing_target": tracks[TARGET].null_count(),
        "nonfinite_target": int((~tracks[TARGET].drop_nulls().is_finite()).sum()),
        "target_outside_nominal_scale": int((~tracks[TARGET].is_between(0, 100)).sum()),
        "known_hash_tracks": catalog.filter(pl.col("split") == "development_train")[
            "track_id"
        ].n_unique(),
        "known_hash_sources": [str(row[0]) for row in HASH_SOURCES],
        "holdout_target_loaded": False,
        "rejected_by_target_value": 0,
        "source_target_scope": "development_train before materialization",
    }
    ensure(
        audit["missing_target"] == 0 and audit["nonfinite_target"] == 0,
        "Alvo ausente/não finito: não imputar",
    )
    ensure(not any(r["missing"] for r in audit["identifier_audit"].values()), "ID ausente")
    ensure(
        not any(audit["nonfinite_predictors"].values()),
        "Preditor não finito exige revisão explícita",
    )
    ensure(
        all(audit["missing_groups"][g] == 0 for g in GROUPS if g != "composition_key"),
        "Grupo ausente",
    )
    return tracks, reps, common, assignments, catalog, audit


def known_hash_map(catalog):
    result = {}
    for track, value in catalog.select("track_id", "hash_key").unique().iter_rows():
        result.setdefault(track, set()).add(value)
    return result


def hash_union(frame, mapping):
    result = set()
    for track in frame["track_id"]:
        result.update(mapping.get(track, ()))
    return result


def overlap_audit(train, valid, holdout, hash_map):
    row = {
        f"validation_{g}_overlap": len(set(train[g].drop_nulls()) & set(valid[g].drop_nulls()))
        for g in GROUPS
    }
    row.update(
        {
            f"holdout_{g}_overlap": len(set(train[g].drop_nulls()) & set(holdout[g].drop_nulls()))
            for g in GROUPS
        }
    )
    train_hashes = hash_union(train, hash_map)
    row["validation_known_hash_overlap"] = len(train_hashes & hash_union(valid, hash_map))
    row["holdout_known_hash_overlap"] = len(train_hashes & hash_union(holdout, hash_map))
    ensure(not any(row.values()), f"Contaminação encontrada: {row}")
    return row


def nested_artist_subsets(pool, *, seed, targets):
    groups = {}
    for row, artist in pool.select("matrix_row", "artist_group_id").iter_rows():
        groups.setdefault(artist, []).append(int(row))
    ordered = sorted(
        groups,
        key=lambda artist: (hashlib.sha256(f"v0.9|{seed}|{artist}".encode()).hexdigest(), artist),
    )
    cumulative = np.cumsum([len(groups[g]) for g in ordered])
    result = {}
    for size in targets:
        if size >= pool.height:
            result[size] = None
            continue
        stop = int(np.argmin(np.abs(cumulative - size))) + 1
        result[size] = sorted(row for group in ordered[:stop] for row in groups[group])
    return result


def build_plan(reps, common, assignments, catalog):
    indexed = reps.with_row_index("matrix_row")
    lookup = {
        r["track_id"]: int(r["matrix_row"])
        for r in indexed.select("track_id", "matrix_row").to_dicts()
    }
    mapping = known_hash_map(catalog)
    hold = assignments.filter(pl.col("split") == "holdout_test")
    hold_hashes = hash_union(hold, mapping)
    conditions, audits = [], []
    for fold in range(5):
        valid_tracks = common.filter(pl.col("outer_fold") == fold)["track_id"].to_list()
        original_tracks = common.filter(pl.col("outer_fold") != fold)["track_id"].to_list()
        valid_indices = [lookup[t] for t in valid_tracks]
        original_indices = sorted(lookup[t] for t in original_tracks)
        valid = indexed[valid_indices]
        original = indexed[original_indices]
        reference_check = overlap_audit(original, valid, hold, mapping)
        pool = indexed
        reasons = {}
        for group in GROUPS:
            forbidden = set(valid[group].drop_nulls()) | set(hold[group].drop_nulls())
            before = pool.height
            pool = pool.filter(~pl.col(group).is_in(sorted(forbidden)))
            reasons[group] = before - pool.height
        blocked_hashes = hash_union(valid, mapping) | hold_hashes
        blocked_tracks = [t for t, values in mapping.items() if values & blocked_hashes]
        before = pool.height
        pool = pool.filter(~pl.col("track_id").is_in(blocked_tracks))
        reasons["known_lyrics_hash"] = before - pool.height
        ensure(
            set(original_tracks).issubset(set(pool["track_id"])),
            "Ampliação remove treino comum original",
        )
        full_check = overlap_audit(pool, valid, hold, mapping)
        audits.append(
            {
                "fold": fold,
                "validation_n": valid.height,
                "common_train_n": original.height,
                "expanded_max_n": pool.height,
                "exclusions_sequential": reasons,
                "original_audit": reference_check,
                "expanded_audit": full_check,
                "expanded_known_hash_rows": sum(bool(mapping.get(t)) for t in pool["track_id"]),
            }
        )
        specs = [
            ("common", "original", None, None, original_indices),
            ("expanded", "maximum", None, None, sorted(pool["matrix_row"].to_list())),
        ]
        for universe, eligible, sizes in [
            ("common", original, SIZES[:2]),
            ("expanded", pool, SIZES),
        ]:
            for seed in SEEDS:
                for requested, selected in nested_artist_subsets(
                    eligible, seed=seed, targets=sizes
                ).items():
                    specs.append((universe, str(requested), seed, requested, selected))
        for universe, label, seed, requested, train_indices in specs:
            key = f"{universe}__{label}__seed{seed if seed is not None else 'shared'}"
            if train_indices is None:
                conditions.append(
                    {
                        "condition": key,
                        "fold": fold,
                        "status": "infeasible",
                        "universe": universe,
                        "size_label": label,
                        "seed": seed,
                        "requested_n": requested,
                    }
                )
                continue
            chosen = indexed[train_indices]
            checked = overlap_audit(chosen, valid, hold, mapping)
            conditions.append(
                {
                    "condition": key,
                    "fold": fold,
                    "status": "eligible",
                    "universe": universe,
                    "size_label": label,
                    "seed": seed,
                    "requested_n": requested,
                    "train_n": len(train_indices),
                    "train_artists": chosen["artist_group_id"].n_unique(),
                    "valid_n": len(valid_indices),
                    "train_indices": train_indices,
                    "valid_indices": valid_indices,
                    "train_sha256": signature(train_indices),
                    "valid_sha256": signature(valid_indices),
                    "common_train_rows_included": len(set(train_indices) & set(original_indices)),
                    "overlap_audit": checked,
                }
            )
    return {
        "conditions": conditions,
        "fold_audit": audits,
        "hash_unknown_limitation": "Só se pode conferir igualdade de hashes documentados; ausência de hash não comprova texto diferente.",
    }


def preservation_snapshot():
    exclude = PUBLIC | {
        CODE,
        REPORT_CODE,
        Path("tests/test_training_expansion_v090.py"),
        Path("docs/base_ampliada_v0_9.md"),
    }
    files = {
        Path(p)
        for p in git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0")
        if p
    }
    files.update(
        p.relative_to(ROOT)
        for p in (ROOT / "reports").rglob("*")
        if p.is_file() and not p.is_relative_to(ROOT / FIGURES)
    )
    for folder in (DEV / "models", Path("data/derived/private_statistical_revision_v0_8")):
        files.update(p.relative_to(ROOT) for p in (ROOT / folder).rglob("*") if p.is_file())
    files.update(
        (
            BASE,
            SPLIT,
            MATCH,
            DEV / "development_matrix.parquet",
            DEV / "fold_assignments.parquet",
            DEV / "oof_predictions.parquet",
        )
    )
    hashes = {p.as_posix(): digest(p) for p in sorted(files - exclude) if (ROOT / p).is_file()}
    meta = {}
    for path in (ROOT / "data").rglob("*"):
        if path.is_file() and not path.is_relative_to(ROOT / PRIVATE):
            stat = path.stat()
            meta[path.relative_to(ROOT).as_posix()] = [stat.st_size, stat.st_mtime_ns]
    return {
        "created_at": now(),
        "sha256": hashes,
        "data_metadata": meta,
        "head": git("rev-parse", "HEAD").strip(),
        "stage": git("diff", "--cached", "--binary"),
        "status": git("status", "--short"),
    }


def verify_preservation():
    snap = read_json(PRIVATE / "preservation_before.json")
    changed = [
        p for p, sha in snap["sha256"].items() if not (ROOT / p).is_file() or digest(p) != sha
    ]
    changed_meta = [
        p
        for p, value in snap["data_metadata"].items()
        if not (ROOT / p).is_file()
        or [(ROOT / p).stat().st_size, (ROOT / p).stat().st_mtime_ns] != value
    ]
    ensure(not changed and not changed_meta, "Artefato anterior mudou")
    ensure(
        git("rev-parse", "HEAD").strip() == snap["head"]
        and git("diff", "--cached", "--binary") == snap["stage"],
        "Git HEAD/stage mudou",
    )
    private_tracked = [
        p
        for p in git("ls-files", "-z").split("\0")
        if (p.startswith("data/") and not p.endswith(".gitkeep"))
        or p.endswith((".parquet", ".joblib", ".npz", ".pkl"))
    ]
    ensure(not private_tracked, "Dados privados rastreados")
    ensure(
        git("check-ignore", (PRIVATE / "representatives.parquet").as_posix()).strip(),
        "Pasta privada não ignorada",
    )
    return {
        "sha256_verified": len(snap["sha256"]),
        "old_data_metadata_verified": len(snap["data_metadata"]),
        "changed_hashes": changed,
        "changed_metadata": changed_meta,
        "head_stage_unchanged": True,
        "private_tracked": private_tracked,
        "private_ignored": True,
        "holdout_targets_loaded": False,
        "note": "Hashes de fontes, desenvolvimento/modelos V0.5–V0.8 e arquivos públicos/pessoais; outros dados conferidos por tamanho/mtime_ns.",
    }


def prepare():
    ensure(not (ROOT / PRIVATE / "seal.json").exists(), "Preparação já selada; preservar")
    write_json(PRIVATE / "preservation_before.json", preservation_snapshot())
    tracks, reps, common, assignments, catalog, audit = load_base()
    for name, frame in (
        ("tracks", tracks),
        ("representatives", reps),
        ("common", common),
        ("hash_catalog", catalog),
    ):
        frame.write_parquet(output(PRIVATE / f"{name}.parquet"))
    plan = build_plan(reps, common, assignments, catalog)
    write_json(PRIVATE / "partition_plan.json", plan)
    write_json(PRIVATE / "base_audit.json", audit)
    write_json(PRIVATE / "read_audit.json", READS)
    from .training_expansion_report_v090 import base_reports

    base_reports(tracks, reps, common, plan, audit)
    blocks, configs = feature_blocks()
    inputs = {
        BASE,
        SPLIT,
        MATCH,
        MANIFEST,
        DEV / "development_matrix.parquet",
        DEV / "fold_assignments.parquet",
        STUDY / "final_cohort_v1_0.parquet",
        STUDY / "final_reserve_v1_0.parquet",
        *[row[0] for row in HASH_SOURCES],
    }
    code = [
        CODE,
        REPORT_CODE,
        Path("src/tcc_music_popularity/statistical_revision_v080.py"),
        Path("src/tcc_music_popularity/modeling_recalibration_v031.py"),
        Path("src/tcc_music_popularity/final_study_v040.py"),
        Path("src/tcc_music_popularity/modeling_pilot_v030.py"),
    ]
    seal = {
        "sealed_before_any_fitting_at": now(),
        "protocol_sha256": digest(PROTOCOL),
        "code_sha256": {p.as_posix(): digest(p) for p in code},
        "inputs_sha256": {p.as_posix(): digest(p) for p in sorted(inputs)},
        "prepared_sha256": {
            p: digest(PRIVATE / p)
            for p in (
                "tracks.parquet",
                "representatives.parquet",
                "common.parquet",
                "hash_catalog.parquet",
                "partition_plan.json",
                "base_audit.json",
                "read_audit.json",
                "preservation_before.json",
            )
        },
        "configs": configs,
        "features": {block: blocks.columns(block) for block in BLOCKS},
        "seeds": list(SEEDS),
        "planned_model_fits": 2 * sum(c["status"] == "eligible" for c in plan["conditions"]),
        "versions": {
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
            "polars": pl.__version__,
        },
    }
    seal["seal_id"] = signature(seal)
    write_json(PRIVATE / "seal.json", seal)
    print(
        json.dumps(
            {
                "status": "prepared",
                "tracks": tracks.height,
                "compositions": reps.height,
                "additional": reps.height - common.height,
                "fits": seal["planned_model_fits"],
                "protocol_sha256": seal["protocol_sha256"],
                "fold_max_sizes": [r["expanded_max_n"] for r in plan["fold_audit"]],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return seal


def verify_seal():
    seal = read_json(PRIVATE / "seal.json")
    ensure(digest(PROTOCOL) == seal["protocol_sha256"], "Protocolo mudou")
    for path, sha in {**seal["code_sha256"], **seal["inputs_sha256"]}.items():
        ensure(digest(path) == sha, f"Código/entrada mudou: {path}")
    for path, sha in seal["prepared_sha256"].items():
        ensure(digest(PRIVATE / path) == sha, f"Artefato preparado mudou: {path}")
    ensure(
        signature({k: v for k, v in seal.items() if k != "seal_id"}) == seal["seal_id"],
        "Selo inválido",
    )
    return seal


def fit_condition(reps, blocks, spec, block, params):
    train, valid = np.array(spec["train_indices"]), np.array(spec["valid_indices"])
    start = time.perf_counter()
    # n_knots=None uses exactly the old linear-year representation, NOT a spline.
    part = prepare_partition(
        reps,
        blocks,
        block,
        train,
        valid,
        None,
        f"v09/{spec['condition']}/{block}/fold{spec['fold']}",
    )
    prep_seconds = time.perf_counter() - start
    # Reuse only the pure ElasticNet fitter; its historical family selector name
    # does not introduce splines. The transform above is independently specified.
    model, fitted = fit_model(
        "spline_en",
        params,
        part["train"],
        part["ytrain"],
        f"v09/{spec['condition']}/{block}/fold{spec['fold']}",
    )
    start_prediction = time.perf_counter()
    prediction = model.predict(part["valid"])
    ensure(prediction.shape == (len(valid),) and np.isfinite(prediction).all(), "Previsão inválida")
    from sklearn.pipeline import Pipeline

    pipeline = Pipeline([("representation", part["transformer"]), ("model", model)])
    payload = {
        "pipeline": pipeline,
        "prediction": prediction,
        "audit": part["audit"],
        "input_columns": blocks.columns(block),
    }
    measured = {
        "preprocess_seconds": prep_seconds,
        "fit_seconds": fitted["fit_seconds"],
        "fit_attempts": fitted["fit_attempts"],
        "prediction_seconds": time.perf_counter() - start_prediction,
        "total_wall_seconds": time.perf_counter() - start,
        "warnings": part["audit"]["warnings"] + fitted["warnings"],
        "pca_components": part["audit"]["pca_components"],
        "features_out": part["train"].shape[1],
    }
    return payload, measured


def benchmark():
    seal = verify_seal()
    ensure(not (ROOT / PRIVATE / "benchmark.json").exists(), "Benchmark já existe")
    reps = pl.read_parquet(ROOT / PRIVATE / "representatives.parquet")
    plan = read_json(PRIVATE / "partition_plan.json")
    blocks, configs = feature_blocks()
    cases = [
        ("baseline", f"expanded__2000__seed{SEEDS[0]}"),
        ("traditional", "expanded__maximum__seedshared"),
    ]
    records = []
    with threadpool_limits(limits=2):
        for block, name in cases:
            spec = next(c for c in plan["conditions"] if c["condition"] == name and c["fold"] == 0)
            _, result = fit_condition(reps, blocks, spec, block, configs[block])
            records.append(
                {"block": block, "condition": name, "train_n": spec["train_n"], **result}
            )
    value = {
        "created_at": now(),
        "seal_id": seal["seal_id"],
        "cases": records,
        "validation_metrics_used": False,
        "rough_upper_work_seconds": seal["planned_model_fits"]
        * max(r["total_wall_seconds"] for r in records),
        "note": "Estimativa conservadora usando custo do maior treino; overhead/carga podem alterar o prazo.",
    }
    write_json(PRIVATE / "benchmark.json", value)
    print(json.dumps(value, ensure_ascii=False), flush=True)
    return value


def checkpoint(spec, block):
    return PRIVATE / "models" / f"{spec['condition']}__{block}__fold{spec['fold']}.joblib"


def run():
    seal = verify_seal()
    ensure(
        read_json(PRIVATE / "benchmark.json")["seal_id"] == seal["seal_id"], "Benchmark divergente"
    )
    reps = pl.read_parquet(ROOT / PRIVATE / "representatives.parquet")
    plan = read_json(PRIVATE / "partition_plan.json")
    blocks, configs = feature_blocks()
    start = time.perf_counter()
    complete = 0
    try:
        with threadpool_limits(limits=2):
            for spec in plan["conditions"]:
                if spec["status"] != "eligible":
                    continue
                for block in BLOCKS:
                    path = checkpoint(spec, block)
                    meta_path = path.with_suffix(".json")
                    if (ROOT / meta_path).exists():
                        meta = read_json(meta_path)
                        ensure(
                            meta["seal_id"] == seal["seal_id"]
                            and digest(path) == meta["model_sha256"],
                            "Checkpoint divergente",
                        )
                    else:
                        ensure(
                            not (ROOT / path).exists(), "Checkpoint parcial; preservar e investigar"
                        )
                        payload, timing = fit_condition(reps, blocks, spec, block, configs[block])
                        payload.update(
                            {
                                "seal_id": seal["seal_id"],
                                "train_sha256": spec["train_sha256"],
                                "valid_sha256": spec["valid_sha256"],
                            }
                        )
                        joblib.dump(payload, output(path), compress=3)
                        meta = {
                            k: v
                            for k, v in spec.items()
                            if k not in {"train_indices", "valid_indices"}
                        }
                        meta.update(
                            {
                                "block": block,
                                "params": configs[block],
                                "seal_id": seal["seal_id"],
                                "model_sha256": digest(path),
                                **timing,
                                "warning_count": len(timing["warnings"]),
                                "completed_at": now(),
                                "metrics": metrics(
                                    reps[TARGET].to_numpy()[spec["valid_indices"]],
                                    payload["prediction"],
                                ),
                            }
                        )
                        write_json(meta_path, meta)
                    complete += 1
                    write_json(
                        PRIVATE / "progress.json",
                        {
                            "status": "running",
                            "completed": complete,
                            "planned": seal["planned_model_fits"],
                            "condition": spec["condition"],
                            "block": block,
                            "fold": spec["fold"],
                            "updated_at": now(),
                        },
                    )
                    print(
                        f"{complete}/{seal['planned_model_fits']} {spec['condition']} {block} fold={spec['fold']} n={spec['train_n']} {meta['total_wall_seconds']:.1f}s warnings={meta['warning_count']}",
                        flush=True,
                    )
        write_json(
            PRIVATE / "execution.json",
            {
                "completed_at": now(),
                "wall_seconds": time.perf_counter() - start,
                "fits": complete,
                "seal_id": seal["seal_id"],
            },
        )
        from .training_expansion_report_v090 import deliver

        deliver(seal, verify_preservation())
    except Exception as exc:
        write_json(
            PRIVATE / "failure.json",
            {
                "at": now(),
                "type": type(exc).__name__,
                "error": str(exc),
                "warnings": getattr(exc, "events", []),
            },
        )
        raise


def collect_predictions(seal, *, reproduce=False):
    reps = pl.read_parquet(ROOT / PRIVATE / "representatives.parquet")
    common = pl.read_parquet(ROOT / PRIVATE / "common.parquet")
    plan = read_json(PRIVATE / "partition_plan.json")
    position = {track: i for i, track in enumerate(common["track_id"])}
    predictions, counts, records, checks = {}, {}, [], []
    blocks, _ = feature_blocks()
    for spec in plan["conditions"]:
        if spec["status"] != "eligible":
            continue
        indices = np.array([position[t] for t in reps[spec["valid_indices"]]["track_id"]])
        for block in BLOCKS:
            path = checkpoint(spec, block)
            record = read_json(path.with_suffix(".json"))
            ensure(
                record["seal_id"] == seal["seal_id"] and digest(path) == record["model_sha256"],
                "Checkpoint corrompido",
            )
            part = joblib.load(ROOT / path)
            audit = part["audit"]
            ensure(
                audit["train_indices"] == spec["train_indices"]
                and audit["valid_indices"] == spec["valid_indices"],
                "Transformação não corresponde ao treino/validação",
            )
            ensure(
                audit["input_columns"] == blocks.columns(block)
                and TARGET not in part["input_columns"],
                "Input indevido",
            )
            ensure(
                audit["train_index_sha256"] == spec["train_sha256"]
                and audit["valid_index_sha256"] == spec["valid_sha256"],
                "Hash de índices divergente",
            )
            if block == "traditional":
                pca = (
                    part["pipeline"]
                    .named_steps["representation"]
                    .named_steps["preprocess"]
                    .named_transformers_["traditional"]
                    .named_steps["pca"]
                )
                ensure(
                    pca.n_samples_ == spec["train_n"] and pca.n_components == 0.9,
                    "PCA fora do treino",
                )
            ensure(
                set(common["outer_fold"].to_numpy()[indices].tolist()) == {spec["fold"]},
                "Fold da validação mudou",
            )
            if reproduce:
                fresh = part["pipeline"].predict(
                    reps[spec["valid_indices"]].select(blocks.columns(block))
                )
                ensure(
                    np.allclose(fresh, part["prediction"], atol=1e-10, rtol=0),
                    "Previsão não reproduzida",
                )
                checks.append(
                    {
                        "condition": spec["condition"],
                        "block": block,
                        "fold": spec["fold"],
                        "maximum_absolute_difference": float(
                            np.max(np.abs(fresh - part["prediction"]))
                        ),
                    }
                )
            key = f"{spec['condition']}__{block}"
            if key not in predictions:
                predictions[key], counts[key] = (
                    np.full(common.height, np.nan),
                    np.zeros(common.height, int),
                )
            predictions[key][indices] = part["prediction"]
            counts[key][indices] += 1
            records.append(record)
    for key, vector in predictions.items():
        ensure(
            np.isfinite(vector).all() and np.all(counts[key] == 1),
            f"OOF incompleta/duplicada: {key}",
        )
    return reps, common, predictions, records, checks


def verify():
    seal = verify_seal()
    reps = pl.read_parquet(ROOT / PRIVATE / "representatives.parquet")
    common = pl.read_parquet(ROOT / PRIVATE / "common.parquet")
    assignment = metadata(SPLIT, [*IDS, *GROUPS, "split"])
    catalog = pl.read_parquet(ROOT / PRIVATE / "hash_catalog.parquet")
    rebuilt = build_plan(reps, common, assignment, catalog)
    ensure(rebuilt == read_json(PRIVATE / "partition_plan.json"), "Partições não reproduzíveis")
    with threadpool_limits(limits=2):
        _, common, predictions, records, checks = collect_predictions(seal, reproduce=True)
    ensure(len(records) == seal["planned_model_fits"], "Ajustes incompletos")
    saved = pl.read_parquet(ROOT / PRIVATE / "oof_predictions.parquet")
    ensure(
        saved.select("track_id", "composition_key", TARGET, "outer_fold").equals(
            common.select("track_id", "composition_key", TARGET, "outer_fold")
        ),
        "OOF desalinhada",
    )
    for name, vector in predictions.items():
        ensure(
            np.array_equal(saved[f"prediction__{name}"].to_numpy(), vector),
            "OOF persistida divergente",
        )
    preservation = verify_preservation()
    value = {
        "verified_at": now(),
        "status": "complete_verified",
        "model_checks": checks,
        "prediction_columns": len(predictions),
        "common_rows": common.height,
        "folds_exact_and_partitions_rebuilt": True,
        "transformations_train_only": True,
        "holdout_target_loaded": False,
        "target_excluded_from_inputs": True,
        "all_oof_complete_finite_once": True,
        "atol": 1e-10,
        "rtol": 0,
        "preservation": preservation,
    }
    write_json(PRIVATE / "verification.json", value)
    from .training_expansion_report_v090 import deliver

    deliver(seal, preservation, verification=value)
    print(
        json.dumps(
            {
                "status": value["status"],
                "models": len(checks),
                "oof_vectors": len(predictions),
                "maximum_prediction_difference": max(
                    c["maximum_absolute_difference"] for c in checks
                ),
                "preservation": preservation,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "benchmark", "run", "verify"))
    args = parser.parse_args()
    {"prepare": prepare, "benchmark": benchmark, "run": run, "verify": verify}[args.stage]()


if __name__ == "__main__":
    main()
