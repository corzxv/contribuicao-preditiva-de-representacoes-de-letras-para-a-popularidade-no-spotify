from __future__ import annotations

import ast
import json
from pathlib import Path

import joblib
import polars as pl
import pytest

from tcc_music_popularity import local_demo as module
from tcc_music_popularity.io import sha256_file
from tcc_music_popularity.local_demo_delivery import CAPTIONS, FIGURES, ZIP_PATH, package_figures


class PredictOnlySynthetic:
    def __init__(self, scale):
        self.scale = scale

    def predict(self, inputs):
        assert inputs.columns == ["feature"]
        assert inputs.schema == {"feature": pl.Float64}
        return inputs["feature"].to_numpy() * self.scale

    def fit(self, *_args, **_kwargs):
        raise AssertionError("Training prohibited")

    def fit_transform(self, *_args, **_kwargs):
        raise AssertionError("Training prohibited")

    def partial_fit(self, *_args, **_kwargs):
        raise AssertionError("Training prohibited")


@pytest.fixture
def synthetic_demo(tmp_path):
    def write_json(path, content):
        destination = tmp_path / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(content), encoding="utf-8")

    def write_frame(path, frame):
        destination = tmp_path / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        frame.write_parquet(destination)
        return sha256_file(destination)

    keys = pl.DataFrame(
        {
            "composition_key": ["synth-c2", "synth-c0", "synth-c1"],
            "track_id": ["synth-t2", "synth-t0", "synth-t1"],
            "spotify_row_id": [12, 10, 11],
        }
    )
    features = keys.with_columns(pl.Series("feature", [-2.0, 12.0, 110.0]))
    feature_hash = write_frame(f"{module.DEVELOPMENT}/holdout_features.parquet", features)
    metadata = keys.with_columns(
        pl.Series("artist_name_raw", ["Zeta", "Álfa", "Beta"]),
        pl.Series("track_name_raw", ["Synthetic third", "Synthetic first", "Synthetic second"]),
        pl.Series("year", [2002, 2000, 2001]),
        pl.Series("genre", ["synthetic", "synthetic", "synthetic"]),
        pl.Series("duration_ms", [120000, 140000, 130000]),
    )
    source_hashes = {"holdout_features.parquet": feature_hash}
    for name, frame in (
        ("final_cohort_v1_0.parquet", metadata.head(2)),
        ("final_reserve_v1_0.parquet", metadata.tail(1)),
    ):
        source_hashes[name] = write_frame(f"{module.STUDY}/{name}", frame)
    models, model_hashes = [], {}
    predictions = keys
    for scale, name in enumerate(module.MODELS, start=1):
        path = tmp_path / module.DEVELOPMENT / "models" / f"{name}.joblib"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(PredictOnlySynthetic(scale), path)
        model_hashes[name] = sha256_file(path)
        models.append(
            {
                "model": name,
                "model_sha256": model_hashes[name],
                "input_columns": ["feature"],
                "input_schema": {"feature": "Float64"},
            }
        )
        predictions = predictions.with_columns(
            pl.Series(f"prediction__{name}", features["feature"] * scale)
        )
    prediction_hash = write_frame(
        f"{module.HOLDOUT}/predictions_pre_target.parquet", predictions.reverse()
    )
    target_hash = write_frame(
        f"{module.HOLDOUT}/holdout_target_raw.parquet",
        keys.select("track_id", "spotify_row_id").with_columns(
            pl.Series("spotify_popularity", [3.0, 79.0, 87.0])
        ),
    )
    write_json(
        module.MANIFEST,
        {"status": "frozen_pre_holdout", "candidate": module.CANDIDATE, "models": models},
    )
    write_json(
        module.SUMMARY,
        {
            "status": "complete",
            "model_manifest_sha256": sha256_file(tmp_path / module.MANIFEST),
            "candidate_predefined": module.CANDIDATE,
            "candidate_changed": False,
            "prediction_policy": "raw_unclipped",
            "versions": {},
            "source_artifact_hashes": source_hashes,
            "model_hashes": model_hashes,
            "predictions_sha256": prediction_hash,
            "private_artifact_hashes": {"holdout_target_raw.parquet": target_hash},
            "compositions": 3,
            "metrics": [{"model": name, "mae": 7.0, "r2": 0.5} for name in module.MODELS],
        },
    )
    return module.FrozenDemo(tmp_path)


def test_target_free_exact_inputs_raw_predictions_and_saved_order(synthetic_demo):
    result = synthetic_demo.estimate("synth-c2")
    assert list(result.values()) == [-2.0, -4.0, -6.0, -8.0]
    assert synthetic_demo.estimate("synth-c1")["elastic_net__baseline"] == 110.0
    audit = synthetic_demo.audit_predictions()
    assert audit["compositions"] == 3
    assert not audit["target_loaded"] and not audit["clipping"]
    assert set(audit["maximum_absolute_difference"].values()) == {0.0}


@pytest.mark.parametrize("target", sorted(module.FORBIDDEN_INPUTS))
def test_any_target_in_input_is_rejected(synthetic_demo, target):
    frame = pl.read_parquet(synthetic_demo.features_path).with_columns(pl.lit(50.0).alias(target))
    with pytest.raises(module.DemoError, match="Alvo"):
        synthetic_demo._predict_checked(frame)


def test_whole_feature_file_with_target_is_rejected(synthetic_demo):
    frame = pl.read_parquet(synthetic_demo.features_path).with_columns(
        pl.lit(50.0).alias("spotify_popularity")
    )
    frame.write_parquet(synthetic_demo.features_path)
    summary_path = synthetic_demo.root / module.SUMMARY
    summary = json.loads(summary_path.read_text())
    summary["source_artifact_hashes"]["holdout_features.parquet"] = sha256_file(
        synthetic_demo.features_path
    )
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(module.DemoError, match="Alvo/contagens"):
        module.FrozenDemo(synthetic_demo.root)


def test_catalog_complete_deterministic_search_independent_of_outcomes(synthetic_demo):
    assert [row["artist_name_raw"] for row in synthetic_demo.catalog] == ["Álfa", "Beta", "Zeta"]
    assert len(synthetic_demo.search("")) == 3
    assert synthetic_demo.search("ALFA")[0]["composition_key"] == "synth-c0"
    assert synthetic_demo.search("synthetic second")[0]["composition_key"] == "synth-c1"
    assert synthetic_demo.search("nonexistent") == []
    assert all(not module.FORBIDDEN_INPUTS.intersection(row) for row in synthetic_demo.catalog)


def test_estimate_reveal_and_selection_reset(synthetic_demo, monkeypatch):
    original = pl.scan_parquet
    target_calls = []

    def scan(path, *args, **kwargs):
        if Path(path).name == "holdout_target_raw.parquet":
            target_calls.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(pl, "scan_parquet", scan)
    session = module.DemoSession()
    session.select("synth-c0")
    with pytest.raises(module.DemoError, match="Estime primeiro"):
        session.reveal(synthetic_demo)
    session.estimate(synthetic_demo)
    assert not target_calls and session.observed is None
    session.reveal(synthetic_demo)
    assert len(target_calls) == 1 and session.observed == 79.0
    assert abs(session.observed - session.predictions["elastic_net__baseline"]) == 67.0
    session.select("synth-c1")
    assert session.observed is None and session.predictions == {}


def test_model_files_preserved(synthetic_demo):
    paths = list((synthetic_demo.root / module.DEVELOPMENT / "models").glob("*.joblib"))
    before = {path: sha256_file(path) for path in paths}
    synthetic_demo.estimate("synth-c0")
    synthetic_demo.audit_predictions()
    assert before == {path: sha256_file(path) for path in paths}


def test_saved_prediction_mismatch_blocks_inference(synthetic_demo):
    synthetic_demo._models["elastic_net__baseline"] = PredictOnlySynthetic(1.001)
    with pytest.raises(module.DemoError, match="incompatível"):
        synthetic_demo.estimate("synth-c0")


def test_missing_and_changed_private_files_fail_safely(synthetic_demo):
    path = synthetic_demo.root / module.DEVELOPMENT / "models/elastic_net__baseline.joblib"
    path.write_bytes(b"synthetic corruption")
    with pytest.raises(module.DemoError, match="Artefato alterado"):
        synthetic_demo.estimate("synth-c0")
    path.unlink()
    with pytest.raises(module.DemoError, match="Arquivo local ausente"):
        module.FrozenDemo(synthetic_demo.root)


def test_missing_public_manifests_fail_safely(tmp_path):
    with pytest.raises(module.DemoError, match="Arquivo local ausente"):
        module.FrozenDemo(tmp_path)


def test_unknown_composition_rejected(synthetic_demo):
    with pytest.raises(module.DemoError, match="fora do holdout"):
        synthetic_demo.estimate("outside")


def test_environment_version_mismatch_is_actionable(synthetic_demo):
    path = synthetic_demo.root / module.SUMMARY
    summary = json.loads(path.read_text())
    summary["versions"] = {"python": "0.0.synthetic"}
    path.write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(module.DemoError, match="Ambiente divergente"):
        module.FrozenDemo(synthetic_demo.root)


def test_missing_target_after_estimate_does_not_reveal(synthetic_demo):
    session = module.DemoSession()
    session.select("synth-c0")
    session.estimate(synthetic_demo)
    (synthetic_demo.root / module.HOLDOUT / "holdout_target_raw.parquet").unlink()
    with pytest.raises(module.DemoError, match="Arquivo local ausente"):
        session.reveal(synthetic_demo)
    assert session.observed is None


def test_no_training_or_remote_calls_in_demonstrator():
    root = Path(__file__).resolve().parents[1]
    forbidden = {"fit", "fit_transform", "partial_fit", "train", "tune", "urlopen", "get", "post"}
    # Dictionary .get is harmless; no HTTP modules are imported in the demo backend.
    forbidden -= {"get"}
    for path in (root / "src/tcc_music_popularity/local_demo.py", root / "apps/streamlit_demo.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = [
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        ]
        assert not forbidden.intersection(calls)
        assert "requests" not in path.read_text(encoding="utf-8")


def test_package_only_four_existing_figures_and_captions(synthetic_demo):
    root = synthetic_demo.root
    names = [
        "elastic_net_metrics.png",
        "primary_mae_adjusted_intervals.png",
        "residual_distributions.png",
        "observed_predicted_aggregated.png",
    ]
    hashes = {}
    for name in names:
        path = root / FIGURES / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"synthetic {name}".encode())
        hashes[name] = sha256_file(path)
    (root / CAPTIONS).write_text("Synthetic captions", encoding="utf-8")
    path = root / module.SUMMARY
    summary = json.loads(path.read_text()) | {"figure_hashes": hashes}
    path.write_text(json.dumps(summary), encoding="utf-8")
    first = package_figures(root)
    assert len(first["members"]) == 5
    assert first["figure_hashes"] == hashes
    assert package_figures(root)["sha256"] == first["sha256"]
    (root / CAPTIONS).write_text("Changed synthetic captions", encoding="utf-8")
    with pytest.raises(module.DemoError, match="preservado"):
        package_figures(root)
    assert sha256_file(root / ZIP_PATH) == first["sha256"]
