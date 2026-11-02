"""Synthetic V0.9 tests: never open project data or holdout targets."""

import json

import numpy as np
import polars as pl
import pytest
from threadpoolctl import threadpool_limits

from tcc_music_popularity import training_expansion_delivery_v090 as delivery
from tcc_music_popularity import training_expansion_report_v090 as report
from tcc_music_popularity import training_expansion_v090 as expansion
from tcc_music_popularity.modeling_pilot_v030 import FeatureBlocks


@pytest.fixture
def toy():
    n = 100
    rng = np.random.default_rng(13)
    artist = np.arange(n) // 2
    frame = pl.DataFrame(
        {
            "track_id": [f"synthetic_track_{i}" for i in range(n)],
            "spotify_row_id": np.arange(n),
            "lfm_record_key": [f"lfm_{i}" for i in range(n)],
            "composition_key": [f"composition_{i}" for i in range(n)],
            "artist_group_id": [f"artist_{i}" for i in artist],
            "composition_group_id": [f"composition_group_{i}" for i in range(n)],
            "split_group_id": [f"group_{i}" for i in artist],
            "split": ["development_train"] * n,
            expansion.TARGET: rng.uniform(0, 100, n),
            "year": 2000 + np.arange(n) % 25,
            "genre": np.where(np.arange(n) % 2, "a", "b"),
            "key": np.arange(n) % 12,
            "time_signature": np.full(n, 4),
            "mode": np.arange(n) % 2,
            "energy": rng.uniform(size=n),
            "lfm_one": rng.normal(size=n),
            "lfm_two": rng.normal(size=n),
            **{flag: np.zeros(n, bool) for flag in report.FLAGS},
            "sampling_role": ["main"] * 50 + ["not_selected"] * 50,
            "final_status": ["accepted_exact_unique"] * 50 + ["not_queried"] * 50,
            "lyrics_accepted_v04": [True] * 50 + [False] * 50,
            "in_common_v05": [True] * 50 + [False] * 50,
        }
    )
    common = frame.head(50).with_columns(pl.Series("outer_fold", artist[:50] % 5))
    catalog = pl.DataFrame(schema={"track_id": pl.String, "hash_key": pl.String})
    blocks = FeatureBlocks(
        ("year", "genre", "key", "time_signature", "mode", "energy", *report.FLAGS),
        ("lfm_one", "lfm_two"),
        (),
        {},
    )
    return frame, common, catalog, blocks


def test_nested_whole_artist_groups_deterministic_and_target_free(toy):
    frame, _, _, _ = toy
    pool = frame.with_row_index("matrix_row")
    one = expansion.nested_artist_subsets(pool, seed=17, targets=(11, 23, 51, 100))
    altered = pool.reverse().with_columns(pl.lit(-999).alias(expansion.TARGET))
    assert one == expansion.nested_artist_subsets(altered, seed=17, targets=(11, 23, 51, 100))
    assert one[100] is None
    assert set(one[11]) <= set(one[23]) <= set(one[51])
    for indices in (one[11], one[23], one[51]):
        selected = pool[indices]
        assert selected.group_by("artist_group_id").len()["len"].to_list() == [2] * (
            len(indices) // 2
        )
    assert one[11] != expansion.nested_artist_subsets(pool, seed=18, targets=(11,))[11]


@pytest.mark.parametrize("group", expansion.GROUPS)
def test_overlap_rejects_each_validation_and_holdout_group(toy, group):
    frame, _, _, _ = toy
    train, valid, hold = frame.head(2), frame.slice(10, 2), frame.slice(20, 2)
    assert not any(expansion.overlap_audit(train, valid, hold, {}).values())
    contaminated = valid.with_columns(pl.lit(train[group][0]).alias(group))
    with pytest.raises(ValueError, match="Contaminação"):
        expansion.overlap_audit(train, contaminated, hold, {})
    with pytest.raises(ValueError, match="Contaminação"):
        expansion.overlap_audit(train, valid, contaminated, {})


def test_known_hash_exclusion_respects_namespace(toy):
    frame, _, _, _ = toy
    train, valid, hold = frame.head(2), frame.slice(10, 2), frame.slice(20, 2)
    mapping = {train["track_id"][0]: {"strict:abc"}, valid["track_id"][0]: {"strict:abc"}}
    with pytest.raises(ValueError, match="Contaminação"):
        expansion.overlap_audit(train, valid, hold, mapping)
    mapping[valid["track_id"][0]] = {"normalized:abc"}
    assert not any(expansion.overlap_audit(train, valid, hold, mapping).values())


def test_all_partitions_checked_and_maximum_preserves_original(toy, monkeypatch):
    frame, common, catalog, _ = toy
    monkeypatch.setattr(expansion, "SIZES", (10, 20, 30, 40))
    plan = expansion.build_plan(frame, common, frame, catalog)
    assert len(plan["conditions"]) == 70
    for fold in range(5):
        specs = [s for s in plan["conditions"] if s["fold"] == fold]
        original = next(s for s in specs if s["size_label"] == "original")
        maximum = next(s for s in specs if s["size_label"] == "maximum")
        assert set(original["train_indices"]) <= set(maximum["train_indices"])
        assert original["train_n"] == 40
        assert maximum["train_n"] == 90
        assert len({s["valid_sha256"] for s in specs}) == 1
        assert all(not any(s["overlap_audit"].values()) for s in specs)
        assert (
            frame[original["valid_indices"]]["track_id"].to_list()
            == common.filter(pl.col("outer_fold") == fold)["track_id"].to_list()
        )


def test_contaminated_original_reference_blocks_plan_before_fits(toy):
    frame, common, _, _ = toy
    catalog = pl.DataFrame(
        {"track_id": [frame["track_id"][0], frame["track_id"][2]], "hash_key": ["same"] * 2}
    )
    with pytest.raises(ValueError, match="Contaminação"):
        expansion.build_plan(frame, common, frame, catalog)


def test_additional_known_hash_is_excluded_without_losing_reference(toy):
    frame, common, _, _ = toy
    catalog = pl.DataFrame(
        {"track_id": [frame["track_id"][0], frame["track_id"][50]], "hash_key": ["same"] * 2}
    )
    plan = expansion.build_plan(frame, common, frame, catalog)
    assert plan["fold_audit"][0]["exclusions_sequential"]["known_lyrics_hash"] == 1
    maximum = next(c for c in plan["conditions"] if c["fold"] == 0 and c["size_label"] == "maximum")
    assert 50 not in maximum["train_indices"]
    assert maximum["common_train_rows_included"] == 40


def test_development_reader_filters_before_materialization(tmp_path, monkeypatch):
    monkeypatch.setattr(expansion, "ROOT", tmp_path)
    path = tmp_path / expansion.BASE
    path.parent.mkdir(parents=True)
    pl.DataFrame(
        {"split": ["development_train", "holdout_test"], expansion.TARGET: [42.0, -99999.0]}
    ).write_parquet(path)
    frame = expansion.development_features(["split", expansion.TARGET])
    assert frame.height == 1 and frame[expansion.TARGET].to_list() == [42.0]
    with pytest.raises(ValueError, match="Proxy"):
        expansion.development_features(["lfm_playcount"])


@pytest.mark.parametrize("column", sorted(expansion.FORBIDDEN))
def test_metadata_reader_rejects_forbidden_before_opening(column):
    with pytest.raises(ValueError, match="metadados"):
        expansion.metadata("nonexistent_synthetic_file", [column])


@pytest.mark.parametrize("block", expansion.BLOCKS)
def test_fit_transform_train_only_no_target_and_raw_prediction(toy, block):
    frame, _, _, blocks = toy
    modified = frame.with_columns(
        pl.when(pl.int_range(pl.len()) >= 80)
        .then(99999.0)
        .otherwise(pl.col("lfm_one"))
        .alias("lfm_one"),
        pl.when(pl.int_range(pl.len()) >= 80)
        .then(pl.lit("unseen"))
        .otherwise(pl.col("genre"))
        .alias("genre"),
    )
    spec = {
        "train_indices": list(range(80)),
        "valid_indices": list(range(80, 100)),
        "condition": "synthetic",
        "fold": 0,
    }
    with threadpool_limits(limits=1):
        payload, measured = expansion.fit_condition(
            modified, blocks, spec, block, {"alpha": 0.003, "l1_ratio": 0.95}
        )
    assert payload["input_columns"] == blocks.columns(block)
    assert expansion.TARGET not in payload["input_columns"]
    transform = payload["pipeline"].named_steps["representation"]
    named = transform.named_steps["preprocess"].named_transformers_
    assert "year_spline" not in named
    assert "unseen" not in named["baseline_categorical"].named_steps["one_hot"].categories_[0]
    if block == "traditional":
        assert named["traditional"].named_steps["pca"].n_samples_ == 80
        assert named["traditional"].named_steps["pca"].n_components == 0.9
        assert named["traditional"].named_steps["imputer"].statistics_[0] == pytest.approx(
            frame["lfm_one"][:80].median()
        )
    changed_target = modified.with_columns(pl.lit(-9999).alias(expansion.TARGET))
    x = changed_target.slice(80).select(payload["input_columns"])
    np.testing.assert_allclose(payload["pipeline"].predict(x), payload["prediction"], atol=1e-10)
    assert payload["audit"]["train_index_sha256"] == expansion.signature(list(range(80)))
    assert measured["fit_attempts"] == 1


def test_seal_and_output_guards(tmp_path, monkeypatch):
    monkeypatch.setattr(expansion, "ROOT", tmp_path)
    for path in (expansion.BASE, "reports/old.md", expansion.PRIVATE / ".." / "old.json"):
        with pytest.raises(ValueError):
            expansion.output(path)
    expansion.output(expansion.PROTOCOL).write_text("synthetic protocol", encoding="utf-8")
    seal = {
        "protocol_sha256": expansion.digest(expansion.PROTOCOL),
        "code_sha256": {},
        "inputs_sha256": {},
        "prepared_sha256": {},
    }
    seal["seal_id"] = expansion.signature(seal)
    expansion.write_json(expansion.PRIVATE / "seal.json", seal)
    assert expansion.verify_seal() == seal
    expansion.output(expansion.PROTOCOL).write_text("changed protocol", encoding="utf-8")
    with pytest.raises(ValueError, match="Protocolo mudou"):
        expansion.verify_seal()


def test_coverage_thresholds_statuses_and_private_artist_rows(toy, tmp_path, monkeypatch):
    frame, _, _, _ = toy
    monkeypatch.setattr(expansion, "ROOT", tmp_path)
    frame = frame.with_columns(pl.Series(expansion.TARGET, [0.0] * 97 + [60.0, 70.0, 80.0]))
    stats, rows = report.coverage(frame, frame)
    stage = next(s for s in stats if s["stage"] == "eligible_development_compositions")
    assert (stage["n_ge60"], stage["n_ge70"], stage["n_ge80"]) == (3, 2, 1)
    common = next(s for s in stats if s["stage"] == "common_v05")
    assert common["n"] == 50
    prohibited = {"track_id", "composition_key", "artist_group_id", expansion.TARGET}
    assert all(not prohibited.intersection(row) for row in rows)
    exported = json.dumps(rows)
    assert "synthetic_track_" not in exported and "artist_0" not in exported
    assert (tmp_path / expansion.PRIVATE / "coverage_artist_groups.parquet").is_file()


def test_curve_denominators_and_no_individual_data(toy):
    _, common, _, _ = toy
    records = [
        {
            "condition": "synthetic",
            "block": "baseline",
            "universe": "common",
            "size_label": "original",
            "seed": None,
            "requested_n": None,
            "fold": fold,
            "train_n": 40,
            "train_artists": 20,
        }
        for fold in range(5)
    ]
    y = common[expansion.TARGET].to_numpy()
    rows = report.curve_metrics(common, {"synthetic__baseline": y + 2}, records)
    assert len(rows) == 16
    assert rows[0]["n"] == 50 and rows[0]["mae"] == pytest.approx(2)
    assert sum(r["n"] for r in rows if r["scope"] == "fold") == 50
    assert sum(r["n"] for r in rows if r["scope"] == "target_band") == 50
    assert all(r["r2"] is None for r in rows if r["scope"] == "target_band")
    assert "track_id" not in json.dumps(rows)


def test_public_figures_and_paired_comparisons(tmp_path, monkeypatch):
    monkeypatch.setattr(expansion, "ROOT", tmp_path)
    rows = []
    conditions = [("common", "original", None, 40), ("expanded", "maximum", None, 90)]
    conditions += [
        (universe, size, seed, int(size))
        for universe in ("common", "expanded")
        for size in ("2000", "5000")
        for seed in expansion.SEEDS
    ]
    for universe, label, seed, count in conditions:
        for block in expansion.BLOCKS:
            value = 5 if block == "baseline" else 4.5
            rows.append(
                {
                    "scope": "oof",
                    "condition": f"{universe}__{label}__{seed}",
                    "universe": universe,
                    "size_label": label,
                    "seed": seed,
                    "block": block,
                    "train_n_mean": count,
                    **expansion.metrics(np.arange(50, dtype=float), np.arange(50) + value),
                }
            )
    comparisons = report.comparisons(rows)
    paired = [r for r in comparisons if r["kind"] == "traditional_vs_baseline_same_training"]
    assert len(paired) == len(conditions)
    assert all(r["delta_mae"] == -0.5 for r in paired)
    assert len(report.create_figures(rows)) == 4
    assert len(delivery.figures_from_aggregates(rows)) == 4
    assert len(list((tmp_path / expansion.FIGURES).glob("*.png"))) == 4
