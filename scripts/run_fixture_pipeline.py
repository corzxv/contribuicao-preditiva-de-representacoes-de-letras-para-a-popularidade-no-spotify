"""Executa a pipeline completa duas vezes com fixtures e verifica idempotência."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def run(root: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["TCC_PROJECT_ROOT"] = str(root)
    return subprocess.run(
        [sys.executable, "-m", "tcc_music_popularity.cli", "all"],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="tcc-music-fixture-") as temporary:
        fixture_root = Path(temporary)
        (fixture_root / "configs").mkdir()
        (fixture_root / "data/raw/spotify").mkdir(parents=True)
        (fixture_root / "data/raw/lfm2b").mkdir(parents=True)
        for name in ("pipeline.yaml", "matching.yaml", "quality_rules.yaml"):
            shutil.copyfile(ROOT / "configs" / name, fixture_root / "configs" / name)
        (fixture_root / "configs/data_sources.yaml").write_text(
            """spotify:
  logical_name: spotify_fixture
  page_url: local-fixture
  identifier: fixture/spotify
  local_path: data/raw/spotify/spotify_data.csv
  archive_path: data/raw/spotify/unused.zip
  license_observed: synthetic
  license_url: local-fixture
lfm2b:
  logical_name: lfm2b_fixture
  page_url: local-fixture
  identifier: fixture/lfm2b
  local_path: data/raw/lfm2b/full_dataset.json.gz
  license_observed: synthetic
  license_url: local-fixture
""",
            encoding="utf-8",
        )
        shutil.copyfile(
            ROOT / "tests/fixtures/spotify_fixture.csv",
            fixture_root / "data/raw/spotify/spotify_data.csv",
        )
        with (
            (ROOT / "tests/fixtures/lfm2b_fixture.jsonl").open("rb") as source,
            gzip.open(fixture_root / "data/raw/lfm2b/full_dataset.json.gz", "wb") as target,
        ):
            shutil.copyfileobj(source, target)

        first = run(fixture_root)
        products = [
            "data/processed/spotify_tracks.parquet",
            "data/processed/lfm2b_tracks.parquet",
            "data/processed/spotify_lfm_matches.parquet",
            "data/processed/modeling_base_lfm_v0_1.parquet",
        ]
        first_hashes = {
            name: sha256(fixture_root / name) for name in products if (fixture_root / name).exists()
        }
        second = run(fixture_root)
        second_hashes = {
            name: sha256(fixture_root / name) for name in products if (fixture_root / name).exists()
        }
        second_summary = json.loads(
            (fixture_root / "reports/run_summary.json").read_text(encoding="utf-8")
        )
        debug = subprocess.run(
            [
                sys.executable,
                "-c",
                "from tcc_music_popularity.reporting import generate_reports; generate_reports()",
            ],
            cwd=ROOT,
            env={**os.environ, "TCC_PROJECT_ROOT": str(fixture_root)},
            text=True,
            capture_output=True,
            check=False,
        )
        evidence = {
            "first_return_code": first.returncode,
            "second_return_code": second.returncode,
            "first_hashes": first_hashes,
            "second_hashes": second_hashes,
            "idempotent_products": first_hashes == second_hashes,
            "second_run_status": second_summary["status"],
            "second_run_failures": second_summary["failures"],
            "second_run_records": second_summary["records_by_stage"],
            "first_stderr": first.stderr[-2000:],
            "second_stderr": second.stderr[-2000:],
            "report_debug_return_code": debug.returncode,
            "report_debug_stderr": debug.stderr[-4000:],
        }
        destination = ROOT / "reports/fixture_run_summary.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(evidence, indent=2, ensure_ascii=False))
        return (
            0
            if first.returncode == 0 and second.returncode == 0 and first_hashes == second_hashes
            else 1
        )


if __name__ == "__main__":
    raise SystemExit(main())
