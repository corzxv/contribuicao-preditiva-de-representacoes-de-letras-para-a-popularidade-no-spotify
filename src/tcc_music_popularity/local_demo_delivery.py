"""Read-only scientific integrity audit and packaging of existing public figures."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from .config import PROJECT_ROOT
from .io import sha256_file
from .local_demo import DEVELOPMENT, HOLDOUT, MANIFEST, SUMMARY, FrozenDemo, require

CAPTIONS = "reports/legendas_figuras_monografia_v0_6.md"
ZIP_PATH = "reports/figuras_monografia_v0_6.zip"
FIGURES = "reports/figures/final_holdout_v0_6"


def scientific_hashes(root: Path) -> dict[str, str]:
    """Include all sealed data, splits, nine models, code and published V0.5/V0.6 results."""

    def read(path):
        return json.loads((root / path).read_text(encoding="utf-8"))

    summary = read(SUMMARY)
    development_summary_path = "reports/run_summary_final_development_v0_5.json"
    development = read(development_summary_path)
    seal_path = f"{DEVELOPMENT}/execution_seal.json"
    require(
        sha256_file(root / seal_path) == development["private_integrity_hashes"]["execution_seal"],
        "Selo de desenvolvimento alterado.",
    )
    seal = read(seal_path)
    hashes = dict(seal["input_hashes"]) | seal["code_hashes"]
    hashes.update({f"{DEVELOPMENT}/{name}": value for name, value in seal["data_hashes"].items()})
    hashes.update(
        {
            f"{DEVELOPMENT}/models/{name}.joblib": value
            for name, value in summary["model_hashes"].items()
        }
    )
    hashes.update(
        {f"{HOLDOUT}/{name}": value for name, value in summary["private_artifact_hashes"].items()}
    )
    hashes.update(
        {f"reports/{name}": value for name, value in summary["public_artifact_hashes"].items()}
    )
    hashes.update({f"{FIGURES}/{name}": value for name, value in summary["figure_hashes"].items()})
    hashes.update(
        {
            MANIFEST: summary["model_manifest_sha256"],
            seal_path: development["private_integrity_hashes"]["execution_seal"],
            f"{DEVELOPMENT}/oof_predictions.parquet": development["oof_file_sha256"],
            "configs/final_development_v0_5.yaml": seal["configuration_sha256"],
            "src/tcc_music_popularity/final_holdout_v060.py": summary["evaluator_sha256"],
            "reports/final_holdout_evaluation_plan_v0_5.md": summary["evaluation_plan_sha256"],
        }
    )
    for path, expected in hashes.items():
        require((root / path).is_file(), f"Artefato congelado ausente: {path}.")
        require(sha256_file(root / path) == expected, f"Artefato científico alterado: {path}.")
    # These manifests were finalized after their own hashes; compare before/after this audit.
    hashes.update({path: sha256_file(root / path) for path in (SUMMARY, development_summary_path)})
    return hashes


def privacy_audit(root: Path) -> dict:
    def git(*arguments):
        return subprocess.run(
            ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
        ).stdout.splitlines()

    def private(path):
        return (
            path.startswith(
                (
                    "data/derived/",
                    "data/raw/lyrics_private/",
                    "data/interim/lyrics_private/",
                    ".tmp/",
                )
            )
            or path.endswith((".parquet", ".joblib", ".pkl", ".npz", ".npy"))
            or path in (".env", "configs/data_sources.yaml", "kaggle.json")
        )

    tracked = git("ls-files")
    staged = git("diff", "--cached", "--name-only")
    require(
        not any(private(path) for path in tracked), "Há artefatos privados rastreados pelo Git."
    )
    require(not any(private(path) for path in staged), "Há artefatos privados no stage do Git.")
    summary = json.loads((root / SUMMARY).read_text(encoding="utf-8"))
    paths = [f"{DEVELOPMENT}/models/{name}.joblib" for name in summary["model_hashes"]]
    paths += [
        f"{DEVELOPMENT}/holdout_features.parquet",
        f"{HOLDOUT}/holdout_target_raw.parquet",
        ZIP_PATH,
    ]
    ignored = git("check-ignore", *paths)
    require(set(ignored) == set(paths), "Modelo, dados ou ZIP não estão ignorados.")
    return {"private_tracked": 0, "private_staged": 0, "ignored_paths_checked": len(paths)}


def package_figures(root: Path = PROJECT_ROOT) -> dict:
    summary = json.loads((root / SUMMARY).read_text(encoding="utf-8"))
    figures = summary["figure_hashes"]
    expected_names = {
        "elastic_net_metrics.png",
        "primary_mae_adjusted_intervals.png",
        "residual_distributions.png",
        "observed_predicted_aggregated.png",
    }
    require(set(figures) == expected_names, "Esperados exatamente os quatro gráficos públicos.")
    content = {}
    for name in sorted(figures):
        path = root / FIGURES / name
        require(
            path.is_file() and sha256_file(path) == figures[name],
            f"Gráfico ausente/alterado: {name}.",
        )
        content[name] = path.read_bytes()
    content[Path(CAPTIONS).name] = (root / CAPTIONS).read_bytes()
    destination = root / ZIP_PATH
    if destination.exists():
        with ZipFile(destination) as archive:
            require(
                set(archive.namelist()) == set(content), "ZIP existente divergente; preservado."
            )
            require(
                all(archive.read(name) == value for name, value in content.items()),
                "ZIP existente divergente; preservado.",
            )
    else:
        with ZipFile(destination, mode="x", compression=ZIP_DEFLATED) as archive:
            for name, value in content.items():
                archive.writestr(name, value)
    with ZipFile(destination) as archive:
        require(
            len(archive.namelist()) == 5 and archive.testzip() is None, "Conteúdo inválido no ZIP."
        )
        require(
            all(archive.read(name) == value for name, value in content.items()),
            "Cópia divergente no ZIP.",
        )
    return {
        "path": ZIP_PATH,
        "members": list(content),
        "sha256": sha256_file(destination),
        "figure_hashes": {
            name: hashlib.sha256(value).hexdigest()
            for name, value in content.items()
            if name.endswith(".png")
        },
        "existing_figures_byte_identical": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify", action="store_true", help="Conferir inferência, sem recalcular métricas"
    )
    parser.add_argument(
        "--package", action="store_true", help="Empacotar os quatro PNGs existentes"
    )
    args = parser.parse_args()
    result = {}
    if args.verify:
        before = scientific_hashes(PROJECT_ROOT)
        result["prediction_verification"] = FrozenDemo().audit_predictions()
        after = scientific_hashes(PROJECT_ROOT)
        require(before == after, "Artefato científico modificado durante a demonstração.")
        result["scientific_artifacts_preserved"] = len(before)
        result["privacy"] = privacy_audit(PROJECT_ROOT)
    if args.package:
        result["zip"] = package_figures()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
