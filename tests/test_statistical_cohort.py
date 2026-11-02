"""Testes exclusivamente sintéticos da nova coorte e das regressões."""

import json
import socket
import sqlite3

import numpy as np
import polars as pl
import pytest

from tcc_music_popularity import cohort_regression as model
from tcc_music_popularity import cohort_statistics as cohort
from tcc_music_popularity.io import sha256_file


def synthetic(n=120):
    rng = np.random.default_rng(27)
    return pl.DataFrame(
        {
            "track_id": [f"t{i:04}" for i in range(n)],
            "spotify_row_id": list(range(n)),
            "query_id": [f"q{i}" for i in range(n)],
            "composition_key": [f"c{i // 2}" for i in range(n)],
            "artist_group_id": [f"a{i // 6}" for i in range(n)],
            "composition_group_id": [f"c{i // 2}" for i in range(n)],
            "split_group_id": [f"g{i // 6}" for i in range(n)],
            "source_strict_sha256": [f"s{i}" for i in range(n)],
            "lyrics_sha256": [f"h{i}" for i in range(n)],
            "split": ["development_train"] * n,
            "year": rng.integers(1990, 2024, n),
            "genre": ["pop" if i % 2 else "rock" for i in range(n)],
            "key": rng.integers(0, 12, n),
            "time_signature": [4] * n,
            "mode": rng.integers(0, 2, n),
            "energy": rng.uniform(0, 1, n),
            "lfm_demo": rng.poisson(10, n).astype(float),
            cohort.TARGET: rng.integers(0, 100, n).astype(float),
        }
    )


ALLOWED = {
    "baseline": ["year", "genre", "key", "time_signature", "mode", "energy"],
    "lfm": ["lfm_demo"],
}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Rede proibida nos testes sintéticos")

    monkeypatch.setattr(socket.socket, "connect", denied)


def test_optimized_correlations_are_pairwise_spearman():
    from scipy.stats import spearmanr

    rng = np.random.default_rng(16)
    values = rng.normal(size=(60, 5))
    values[:8, 0] = np.nan
    values[12:17, 1] = np.nan
    values[:8, 2] = np.nan
    values[:, 4] = 1
    names = [f"x{i}" for i in range(5)]
    frame = pl.DataFrame(values, schema=names)
    pairs = cohort.high_correlations(frame, names, minimum=10, threshold=0)
    assert len(pairs) == 6
    for p in pairs:
        left, right = values[:, names.index(p["left"])], values[:, names.index(p["right"])]
        ok = np.isfinite(left) & np.isfinite(right)
        assert p["n"] == ok.sum()
        assert p["spearman"] == pytest.approx(spearmanr(left[ok], right[ok]).statistic)


def test_no_target_input():
    with pytest.raises(ValueError, match="proibida"):
        model.input_matrix(synthetic(), ["energy", cohort.TARGET])


def test_development_projection(tmp_path):
    frame = pl.DataFrame(
        {"split": ["development_train", "holdout_test"], cohort.TARGET: [10.0, 9999.0]}
    )
    path = tmp_path / "mixed.parquet"
    frame.write_parquet(path)
    result = cohort.development_table(path, ["split", cohort.TARGET])
    assert result[cohort.TARGET].to_list() == [10.0]


def test_transitive_components_and_plan():
    frame = synthetic()
    # A letra repetida une dois artistas, e o vínculo deve ser transitivo.
    values = frame["lyrics_sha256"].to_list()
    values[6] = values[0]
    frame = frame.with_columns(pl.Series("lyrics_sha256", values))
    labels = cohort.components(frame, [*cohort.GROUPS, *cohort.HASHES])
    assert labels[0] == labels[11]
    frame = frame.with_columns(pl.Series("analysis_group", labels))
    first = cohort.partition_plan(frame)
    assert first == cohort.partition_plan(frame)
    shuffled = frame.reverse()
    reverse_labels = cohort.components(shuffled, [*cohort.GROUPS, *cohort.HASHES])
    assert reverse_labels[::-1] == labels
    broken = json.loads(json.dumps(first))
    broken["inner"]["0"][0]["valid"].append(broken["inner"]["0"][0]["train"][0])
    with pytest.raises(ValueError, match="Fuga"):
        cohort.validate_plan(frame, broken)


@pytest.mark.parametrize("family", model.FAMILIES)
def test_pipeline_missing_unseen_and_serialization(tmp_path, family):
    frame = synthetic()
    frame = frame.with_columns(
        pl.when(pl.int_range(pl.len()) < 3)
        .then(None)
        .otherwise(pl.col("lfm_demo"))
        .alias("lfm_demo")
    )
    columns = ALLOWED["baseline"] + ALLOWED["lfm"]
    x = model.input_matrix(frame, columns)
    params = model.candidates(family, "traditional")[-1]
    fitted = model.factory(columns, ALLOWED["lfm"], family, params)
    model.fit_checked(fitted, x[:90], frame[cohort.TARGET].to_numpy()[:90])
    x[90:, columns.index("genre")] = "never_seen_in_train"
    prediction, logs = model.predict_checked(fitted, x[90:])
    assert any("unknown categories" in w["message"] for w in logs)
    assert np.isfinite(prediction).all()
    path = tmp_path / "model.joblib"
    model.joblib.dump(fitted, path)
    reloaded, _ = model.predict_checked(model.joblib.load(path), x[90:])
    np.testing.assert_allclose(prediction, reloaded, atol=1e-10)


def test_imputer_does_not_learn_from_validation():
    columns = ["energy"]
    fitted = model.factory(columns, [], "ridge", {"alpha": 1})
    x = np.array([[1.0], [3.0], [np.nan]], dtype=object)
    fitted.fit(x, [1, 2, 3])
    fitted.predict(np.array([[100000.0], [np.nan]], dtype=object))
    imputer = fitted["prepare"].named_transformers_["numeric"]["impute"]
    assert imputer.statistics_.tolist() == [2.0]


def test_all_missing_spline():
    fitted = model.factory(["year", "energy"], [], "additive_ridge", {"alpha": 1})
    x = np.array([[np.nan, 0.2], [np.nan, 0.3], [np.nan, 0.4]], dtype=object)
    fitted.fit(x, [1, 2, 3])
    assert np.isfinite(fitted.predict(x)).all()


def test_bootstrap_pair_identity_and_direction():
    y = np.arange(20.0)
    groups = np.repeat(np.arange(5), 4)
    same = model.paired_interval(y, y + 4, y + 4, groups, repetitions=30)
    assert all(v == 0 for v in same.values())
    better = model.paired_interval(y, y + 4, y + 1, groups, repetitions=30)
    assert better["delta_mae_hi"] == -3


def test_grid_fixed_and_count():
    counts = sum(len(model.candidates(f, b)) for f in model.FAMILIES for b in model.BLOCKS)
    assert counts * 3 * 5 + 50 == 530


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    """Preparação completa com SQLite, índice e Parquets inventados, sem rede."""
    frame = synthetic()
    # Holdout propositalmente inválido: preparação não deve ler estes alvos.
    frame = frame.with_columns(
        pl.when(pl.col("spotify_row_id") >= 96)
        .then(pl.lit("holdout_test"))
        .otherwise(pl.col("split"))
        .alias("split"),
        pl.when(pl.col("spotify_row_id") >= 96)
        .then(pl.lit(9999.0))
        .otherwise(pl.col(cohort.TARGET))
        .alias(cohort.TARGET),
    )
    paths = {}
    for name in ("BASE", "SPLIT", "MATCH", "MANIFEST", "DICTIONARY", "PROTOCOL"):
        paths[name] = tmp_path / name
        paths[name].write_text("fixture", encoding="utf-8")
        monkeypatch.setattr(cohort, name, paths[name])
    frame.write_parquet(paths["BASE"])
    pl.DataFrame(
        {
            "nome": [cohort.TARGET, *ALLOWED["baseline"], *ALLOWED["lfm"]],
            "descrição": ["sintética"] * 8,
        }
    ).write_csv(paths["DICTIONARY"])
    local = tmp_path / "local"
    local.mkdir()
    monkeypatch.setattr(cohort, "LOCAL", local)
    db = sqlite3.connect(local / "state.sqlite")
    db.executescript(
        "CREATE TABLE tracks(track_id TEXT, query_id TEXT); CREATE TABLE queries(query_id TEXT, status TEXT);"
    )
    for row in frame.select("track_id", "query_id").iter_rows():
        db.execute("INSERT INTO tracks VALUES(?,?)", row)
        db.execute("INSERT INTO queries VALUES(?,?)", (row[1], "accepted_exact_unique"))
    db.commit()
    db.close()
    audit = tmp_path / "audit"
    audit.mkdir()
    index = frame.select("track_id", "query_id", "split", "composition_key", *cohort.HASHES)
    index.write_ndjson(audit / "accepted_text_index.jsonl")
    cohort.save_json(
        audit / "summary.json",
        {
            "complete": True,
            "review_required": False,
            "accepted_queries": len(frame),
            "accepted_tracks": len(frame),
        },
    )
    cohort.save_json(
        audit / "provenance.json",
        {
            "inputs_after": {"local": sha256_file(local / "state.sqlite")},
            "accepted_index_sha256": sha256_file(audit / "accepted_text_index.jsonl"),
        },
    )
    source = frame.drop(cohort.TARGET, "query_id", *cohort.HASHES).with_columns(
        pl.lit("artist").alias("artist_name_raw"),
        pl.lit("song").alias("track_name_raw"),
        pl.lit(1000).alias("duration_ms"),
        pl.lit("accepted_high_confidence").alias("match_status"),
        pl.lit("raw_exact").alias("match_method"),
        pl.lit(100.0).alias("match_score"),
    )
    monkeypatch.setattr(cohort, "load_target_free_source", lambda cfg: source)
    monkeypatch.setattr(cohort, "features", lambda: ALLOWED)
    monkeypatch.setattr(cohort, "workspace", lambda p: p)
    monkeypatch.setattr(cohort, "code_paths", lambda: [paths["PROTOCOL"]])
    out = tmp_path / "output"
    cohort.prepare(out, audit)
    return out


def test_preparation_preserves_and_rejects_stale(prepared):
    summary = cohort.read_json(prepared / "summary.json")
    assert summary["accepted_tracks_all_splits"] == 120
    assert summary["development_accepted_tracks"] == 96
    assert summary["development_compositions"] == 48
    assert not summary["holdout_targets_loaded"]
    matrix = pl.read_parquet(prepared / "development.parquet")
    assert matrix[cohort.TARGET].max() < 100
    seal = cohort.check_seal(prepared)
    path = next(iter(seal["inputs"]))
    with open(path, "ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="mudou"):
        cohort.check_seal(prepared)


def test_synthetic_end_to_end_resume_and_verify(prepared, monkeypatch):
    # Grade reduzida apenas no teste; nenhuma alteração do protocolo de produção.
    original = model.candidates
    monkeypatch.setattr(model, "candidates", lambda family, block: original(family, block)[:1])
    model.benchmark(prepared, 1)
    model.run(prepared, 1)
    result = cohort.read_json(prepared / "verification.json")
    assert result["saved_fold_models"] == 50
    assert result["max_prediction_difference"] == 0
    assert len(list((prepared / "models").glob("*.joblib"))) == 50
    assert (prepared / "results.md").exists()
    before = {p: sha256_file(p) for p in (prepared / "models").iterdir()}
    monkeypatch.setattr(
        model, "fit_checked", lambda *a: pytest.fail("Retomada reajustou checkpoint concluído")
    )
    model.run(prepared, 1)
    assert before == {p: sha256_file(p) for p in before}
    model.collect(prepared, reproduce=True, threads=1)
    target = prepared / "models/ols__baseline__fold0.npy"
    with target.open("ab") as stream:
        stream.write(b"tamper")
    with pytest.raises(ValueError, match="alterado"):
        model.part(prepared, "ols__baseline", 0)
