"""Read-only inference over the sealed holdout; never a new scientific evaluation."""

from __future__ import annotations

import importlib.metadata
import json
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from .config import PROJECT_ROOT
from .io import sha256_file

MODELS = {
    "elastic_net__baseline": "Baseline",
    "elastic_net__traditional": "Tradicional",
    "elastic_net__deep": "Profundo",
    "elastic_net__combined": "Combinado",
}
CANDIDATE = "elastic_net__traditional"
KEYS = ["composition_key", "track_id", "spotify_row_id"]
FORBIDDEN_INPUTS = {"spotify_popularity", "genius_lyrics_views", "lfm_playcount"}
ATOL = 1e-8
RTOL = 1e-10
MANIFEST = "reports/final_model_manifest_v0_5.json"
SUMMARY = "reports/run_summary_final_holdout_v0_6.json"
DEVELOPMENT = "data/derived/private_final_development_v0_5"
HOLDOUT = "data/derived/private_final_holdout_v0_6"
STUDY = "data/derived/private_final_study"
DISCLAIMER = (
    "Demonstração acadêmica com músicas do catálogo estudado. Estima a popularidade "
    "registrada na base; não prevê sucesso comercial futuro."
)


class DemoError(RuntimeError):
    """An actionable, privacy-safe error suitable for the local interface."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DemoError(message)


def search_text(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


@dataclass
class DemoSession:
    """Only presentation state: changing the selection hides all previous results."""

    selected: str | None = None
    predictions: dict[str, float] = field(default_factory=dict)
    observed: float | None = None

    def select(self, composition: str | None) -> None:
        if composition != self.selected:
            self.selected = composition
            self.predictions = {}
            self.observed = None

    def estimate(self, demo: FrozenDemo) -> None:
        require(self.selected is not None, "Selecione uma composição.")
        self.predictions = {}
        self.observed = None
        self.predictions = demo.estimate(self.selected)

    def reveal(self, demo: FrozenDemo) -> None:
        require(bool(self.predictions), "Estime primeiro; o observado permanece oculto.")
        require(self.selected is not None, "Selecione uma composição.")
        self.observed = demo.reveal(self.selected)


class FrozenDemo:
    """Load trusted frozen artifacts locally; the target is deserialized only on reveal."""

    def __init__(self, root: Path = PROJECT_ROOT):
        self.root = Path(root)
        self._models: dict[str, Any] = {}
        self.summary = self._read_json(SUMMARY)
        require(self.summary.get("status") == "complete", "A V0.6 não está encerrada.")
        self._check(MANIFEST, self.summary["model_manifest_sha256"])
        self.manifest = self._read_json(MANIFEST)
        require(self.manifest.get("status") == "frozen_pre_holdout", "Manifesto não congelado.")
        require(
            self.manifest.get("candidate") == CANDIDATE
            and self.summary.get("candidate_predefined") == CANDIDATE
            and not self.summary.get("candidate_changed"),
            "O candidato predefinido deve continuar sendo o Tradicional.",
        )
        require(self.summary.get("prediction_policy") == "raw_unclipped", "Política divergente.")
        self.specs = {
            item["model"]: item for item in self.manifest["models"] if item["model"] in MODELS
        }
        require(set(self.specs) == set(MODELS), "Os quatro Elastic Net são necessários.")
        for name, version in self.summary["versions"].items():
            try:
                installed = (
                    sys.version.split()[0] if name == "python" else importlib.metadata.version(name)
                )
            except importlib.metadata.PackageNotFoundError as exc:
                raise DemoError(f"Dependência científica ausente: {name}=={version}.") from exc
            require(
                installed == version, f"Ambiente divergente: {name}; restaure a versão {version}."
            )
        self.hashes = {
            MANIFEST: self.summary["model_manifest_sha256"],
            f"{DEVELOPMENT}/holdout_features.parquet": self.summary["source_artifact_hashes"][
                "holdout_features.parquet"
            ],
            f"{HOLDOUT}/predictions_pre_target.parquet": self.summary["predictions_sha256"],
            **{
                f"{STUDY}/{name}": self.summary["source_artifact_hashes"][name]
                for name in ("final_cohort_v1_0.parquet", "final_reserve_v1_0.parquet")
            },
            **{
                f"{DEVELOPMENT}/models/{name}.joblib": self.summary["model_hashes"][name]
                for name in MODELS
            },
        }
        self.verify_integrity()
        self._existing(f"{HOLDOUT}/holdout_target_raw.parquet")
        self.features_path = self.root / DEVELOPMENT / "holdout_features.parquet"
        self.predictions_path = self.root / HOLDOUT / "predictions_pre_target.parquet"
        schema = pl.scan_parquet(self.features_path).collect_schema()
        require(not FORBIDDEN_INPUTS.intersection(schema), "Alvo/contagens presentes nas features.")
        for name, spec in self.specs.items():
            columns = spec["input_columns"]
            require(not FORBIDDEN_INPUTS.intersection(columns), "Input inclui coluna proibida.")
            require(len(set(columns)) == len(columns), "Input duplicado no manifesto.")
            require(spec["model_sha256"] == self.summary["model_hashes"][name], "Hash divergente.")
            require(
                all(str(schema.get(c)) == spec["input_schema"][c] for c in columns),
                f"Schema congelado divergente: {MODELS[name]}.",
            )
        keys = pl.read_parquet(self.features_path, columns=KEYS)
        require(keys.height == self.summary["compositions"], "Catálogo incompleto.")
        require(keys.unique().height == keys.height, "Representantes duplicados.")
        require(keys["composition_key"].n_unique() == keys.height, "Composições duplicadas.")
        metadata_columns = KEYS + [
            "artist_name_raw",
            "track_name_raw",
            "year",
            "genre",
            "duration_ms",
        ]
        metadata = pl.concat(
            [
                pl.read_parquet(self.root / STUDY / name, columns=metadata_columns)
                for name in ("final_cohort_v1_0.parquet", "final_reserve_v1_0.parquet")
            ]
        )
        try:
            catalog = keys.join(metadata, on=KEYS, how="left", validate="1:1")
        except pl.exceptions.PolarsError as exc:
            raise DemoError("Metadados não correspondem aos representantes congelados.") from exc
        require(
            catalog.height == keys.height
            and catalog["artist_name_raw"].null_count() == 0
            and catalog["track_name_raw"].null_count() == 0,
            "Metadados ausentes no catálogo completo.",
        )
        self.catalog = sorted(
            catalog.to_dicts(),
            key=lambda row: (
                search_text(row["artist_name_raw"]),
                search_text(row["track_name_raw"]),
                row["composition_key"],
            ),
        )
        self.by_composition = {row["composition_key"]: row for row in self.catalog}

    def _existing(self, relative: str) -> Path:
        path = self.root / relative
        require(
            path.is_file(),
            f"Arquivo local ausente: {relative}. Consulte docs/demonstrador_local.md.",
        )
        return path

    def _read_json(self, relative: str) -> dict:
        try:
            return json.loads(self._existing(relative).read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise DemoError(f"Não foi possível ler o manifesto local: {relative}.") from exc

    def _check(self, relative: str, expected: str) -> None:
        require(
            sha256_file(self._existing(relative)) == expected, f"Artefato alterado: {relative}."
        )

    def verify_integrity(self) -> None:
        for path, expected in self.hashes.items():
            self._check(path, expected)

    def search(self, query: str) -> list[dict]:
        words = search_text(query).split()
        return [
            row
            for row in self.catalog
            if all(
                word in search_text(f"{row['artist_name_raw']} {row['track_name_raw']}")
                for word in words
            )
        ]

    def _row(self, composition: str) -> dict:
        require(composition in self.by_composition, "Composição fora do holdout congelado.")
        return self.by_composition[composition]

    @staticmethod
    def _filter(row: dict) -> pl.Expr:
        return pl.all_horizontal([pl.col(key) == row[key] for key in KEYS])

    def _predict_checked(
        self, features: pl.DataFrame
    ) -> tuple[dict[str, np.ndarray], dict[str, float]]:
        require(not FORBIDDEN_INPUTS.intersection(features.columns), "Alvo presente no input.")
        reference = features.select(KEYS).join(
            pl.read_parquet(
                self.predictions_path, columns=KEYS + [f"prediction__{name}" for name in MODELS]
            ),
            on=KEYS,
            how="left",
            validate="1:1",
            maintain_order="left",
        )
        output, differences = {}, {}
        with threadpool_limits(limits=1):
            for name, spec in self.specs.items():
                if name not in self._models:
                    try:
                        self._models[name] = joblib.load(
                            self.root / DEVELOPMENT / "models" / f"{name}.joblib"
                        )
                    except Exception as exc:
                        raise DemoError(
                            f"Falha ao carregar o pipeline congelado {MODELS[name]}."
                        ) from exc
                # Exact frozen inputs; predict reuses fitted preprocessing, with no target or training.
                inputs = features.select(spec["input_columns"])
                require(
                    all(str(inputs.schema[c]) == spec["input_schema"][c] for c in inputs.columns),
                    "Schema de inferência divergente.",
                )
                try:
                    prediction = np.asarray(self._models[name].predict(inputs), dtype=float)
                except Exception as exc:
                    raise DemoError(
                        f"Falha de inferência no pipeline congelado {MODELS[name]}."
                    ) from exc
                expected = reference[f"prediction__{name}"].to_numpy()
                require(
                    prediction.shape == (features.height,)
                    and np.isfinite(prediction).all()
                    and np.isfinite(expected).all(),
                    "Previsões ausentes/não finitas.",
                )
                require(
                    np.allclose(prediction, expected, atol=ATOL, rtol=RTOL),
                    f"Previsão incompatível com a V0.6: {MODELS[name]}. Demonstração bloqueada.",
                )
                output[name] = prediction
                differences[name] = float(np.max(np.abs(prediction - expected)))
        return output, differences

    def estimate(self, composition: str) -> dict[str, float]:
        row = self._row(composition)
        self.verify_integrity()
        features = pl.scan_parquet(self.features_path).filter(self._filter(row)).collect()
        require(features.height == 1, "Representante congelado ausente/duplicado.")
        predictions, _ = self._predict_checked(features)
        self.verify_integrity()
        return {name: float(prediction[0]) for name, prediction in predictions.items()}

    def reveal(self, composition: str) -> float:
        row = self._row(composition)
        path = f"{HOLDOUT}/holdout_target_raw.parquet"
        self._check(path, self.summary["private_artifact_hashes"]["holdout_target_raw.parquet"])
        observed = (
            pl.scan_parquet(self.root / path)
            .filter(
                (pl.col("track_id") == row["track_id"])
                & (pl.col("spotify_row_id") == row["spotify_row_id"])
            )
            .select("spotify_popularity")
            .collect()
        )
        require(observed.height == 1, "Observado ausente/duplicado para o representante.")
        value = float(observed.item())
        require(np.isfinite(value), "Observado não finito.")
        return value

    def official_metrics(self) -> list[dict]:
        by_name = {row["model"]: row for row in self.summary["metrics"]}
        return [
            {
                "Modelo": label,
                "MAE oficial": by_name[name]["mae"],
                "R² oficial": by_name[name]["r2"],
            }
            for name, label in MODELS.items()
        ]

    def audit_predictions(self) -> dict:
        """Numerical reproduction only; never reads targets or recalculates metrics."""
        self.verify_integrity()
        features = pl.read_parquet(self.features_path)
        _, differences = self._predict_checked(features)
        self.verify_integrity()
        return {
            "compositions": features.height,
            "models": list(MODELS),
            "input_dimensions": {
                name: len(spec["input_columns"]) for name, spec in self.specs.items()
            },
            "tolerance": {"atol": ATOL, "rtol": RTOL, "rule": "abs(a-b) <= atol + rtol * abs(b)"},
            "maximum_absolute_difference": differences,
            "target_loaded": False,
            "training_calls": 0,
            "metrics_recalculated": False,
            "clipping": False,
            "candidate": CANDIDATE,
            "integrity_verified": True,
        }


def load_demo() -> FrozenDemo:
    return FrozenDemo()
