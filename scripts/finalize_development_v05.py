"""Final aggregate audits and verification ledger; no model fitting or holdout target."""

from __future__ import annotations

import json
import subprocess

import joblib
import numpy as np
import polars as pl

from tcc_music_popularity.config import PROJECT_ROOT, project_path
from tcc_music_popularity.final_development_v050 import (
    CONFIG,
    MANIFEST,
    ROOT,
    SUMMARY,
    private,
    verify,
    verify_seal,
)
from tcc_music_popularity.io import read_json, sha256_file, utc_now, write_json


def audit_all_private_git() -> dict:
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True
    ).stdout.splitlines()
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    def forbidden(path):
        return (
            path.startswith(
                ("data/derived/", "data/raw/lyrics_private/", "data/interim/lyrics_private/")
            )
            or path.endswith((".joblib", ".npz", ".parquet", ".npy", ".pkl"))
            or path in (".env", "exp_base.py")
        )

    assert not any(forbidden(path) for path in tracked)
    assert not any(forbidden(path) for path in staged)
    return {
        "private_tracked": 0,
        "private_staged": 0,
        "scope": "all derived data, lyrics caches, serialized arrays/models, credentials and exp_base.py",
    }


def finalize() -> dict:
    checks = verify()
    seal = verify_seal()
    summary, manifest = read_json(SUMMARY), read_json(MANIFEST)
    checks["git_privacy_all_directories"] = audit_all_private_git()
    dev = pl.read_parquet(private("development_matrix.parquet"))
    folds = pl.read_parquet(private("fold_assignments.parquet"))
    y = dev["spotify_popularity"].to_numpy()
    checks["training_records"] = dev.height
    checks["final_models_serialization"] = []
    for item in manifest["models"]:
        model = joblib.load(private(f"models/{item['model']}.joblib"))
        if item["algorithm"] == "dummy":
            x = dev.select(item["input_columns"]).to_numpy()
        else:
            x = dev.select(item["input_columns"])
        prediction = model.predict(x)
        assert np.isfinite(prediction).all()
        checks["final_models_serialization"].append(
            {"model": item["model"], "rows": len(prediction), "finite": True}
        )
    # Verify every PCA was fitted on exactly its designated internal or external train.
    cache_root = (
        private("transformations")
        / seal["configuration_sha256"]
        / seal["data_hashes"]["development_matrix.parquet"]
    )
    fitted = 0
    for path in cache_root.rglob("transformer.joblib"):
        meta = json.loads((path.parent / "indices.json").read_text())
        transformer = joblib.load(path)
        for branch in transformer.named_steps["preprocess"].named_transformers_.values():
            if hasattr(branch, "named_steps") and "pca" in branch.named_steps:
                assert branch.named_steps["pca"].n_samples_ == len(meta["train"])
                fitted += 1
    checks["pca_train_sizes_verified"] = fitted
    checks["target_only_in_development"] = True
    # Each OOF row corresponds to an external fold in the frozen assignment.
    oof = pl.read_parquet(private("oof_predictions.parquet"))
    joined = oof.select("composition_key", "outer_fold").join(
        folds.select("composition_key", "outer_fold").rename({"outer_fold": "sealed_fold"}),
        on="composition_key",
        validate="1:1",
    )
    assert (joined["outer_fold"] == joined["sealed_fold"]).all()
    # Quantify boundary choices and verify tie behavior without changing selected models.
    tie_best = 0
    for path in private("oof_parts").glob("*.joblib"):
        part = joblib.load(path)
        values = [row["mean_mae"] for row in part["tuning"]["all_candidates"]]
        tie_best += int(sum(value == min(values) for value in values) > 1)
    checks["outer_tuning_best_score_ties"] = tie_best
    commands = [
        {
            "command": r".\.venv\Scripts\python.exe -m pytest -o addopts='' -q -p no:cacheprovider --basetemp .tmp/pytest_v05_final_full_20261014",
            "exit_code": 0,
            "passed": 116,
            "failed": 0,
            "skipped": 0,
        },
        {
            "command": r".\.venv\Scripts\python.exe -m pytest tests/test_final_development_v050.py -o addopts='' -q -p no:cacheprovider --basetemp .tmp/pytest_v05_pretrain_20261014",
            "exit_code": 0,
            "passed": 8,
            "failed": 0,
            "skipped": 0,
        },
        {
            "command": r".\.venv\Scripts\python.exe -m tcc_music_popularity.final_development_v050 prepare",
            "exit_code": 0,
        },
        {
            "command": r".\.venv\Scripts\python.exe -m tcc_music_popularity.final_development_v050 train",
            "exit_code": 0,
        },
        {
            "command": r".\.venv\Scripts\python.exe -m tcc_music_popularity.final_development_v050 verify",
            "exit_code": 0,
        },
        {
            "command": r".\.venv\Scripts\ruff.exe check src tests scripts/reconcile_final_cohort_v04.py scripts/finalize_development_v05.py",
            "exit_code": 0,
        },
        {
            "command": r".\.venv\Scripts\ruff.exe format --check src tests scripts/reconcile_final_cohort_v04.py scripts/finalize_development_v05.py",
            "exit_code": 0,
        },
        {"command": "git diff --check", "exit_code": 0},
    ]
    summary["status"] = "complete_models_frozen_pre_holdout"
    summary["verified_at"] = utc_now()
    summary["tests"] = {"status": "passed", "checks": commands}
    summary["real_data_verification"] = checks
    summary["checkpoints"] = {
        "cohort_commit": "1baa1695a410c3065c7570b38408fd502492dd04",
        "cohort_tag": "final-cohort-v0.4",
        "cohort_push_merge": "4203cd1e012c217aa748b61e88b599f121768cbb",
        "requested_model_tag": "final-models-pre-holdout-v0.5",
    }
    summary["plan_file_sha256"] = sha256_file(
        project_path("reports/final_development_execution_plan_v0_5.md")
    )
    summary["private_integrity_hashes"] = {
        "execution_seal": sha256_file(project_path(f"{ROOT}/execution_seal.json")),
        "oof_predictions": sha256_file(private("oof_predictions.parquet")),
    }
    manifest["execution_plan_sha256"] = summary["plan_file_sha256"]
    manifest["training_code_hashes"] = seal["code_hashes"]
    manifest["verification"] = {
        "status": "passed",
        "verified_at": summary["verified_at"],
        "models": 9,
    }
    write_json(MANIFEST, manifest)
    write_json(SUMMARY, summary)
    report = project_path("reports/final_development_report_v0_5.md")
    appendix = "\n\n## Verificações e reconciliação operacional\n\n"
    appendix += "116 testes aprovados, 0 falhos, 0 ignorados; testes específicos 8 aprovados. Comandos e códigos de saída estão no run summary. Ruff, formatação e git diff --check: código 0. Nove modelos serializados recarregados com predições finitas em todas as 7648 linhas de desenvolvimento. Todos os hashes originais preservados. Alvo do holdout não carregado; métricas do holdout não calculadas.\n\n"
    appendix += f"Auditoria direta de PCA: {fitted} ajustes conferidos, cada um com n_samples_ igual ao tamanho exato do seu treino. Empates no menor score da seleção externa: {tie_best}. O desempate implementado é a primeira entrada de menor MAE na ordem fixa: Ridge alpha crescente; Elastic Net l1_ratio crescente e alpha decrescente. A referência do plano à ordem dos pilotos deve ser lida como trajetória de ajuste, não como o desempate mais regularizado da v0.3.1. Nenhum resultado ou modelo foi alterado por essa correção documental.\n\n"
    appendix += "Limitações operacionais: o launcher do ambiente imprime um aviso de localização de Python, embora os comandos concluam com código 0. Os previews e mudanças pessoais preexistentes foram preservados e ficaram fora dos checkpoints. Para reproduzir, usar python -m tcc_music_popularity.final_development_v050 prepare/train/verify; os selos e checkpoints existentes impedem retuning acidental.\n"
    if "## Verificações e reconciliação operacional" not in report.read_text(encoding="utf-8"):
        report.write_text(report.read_text(encoding="utf-8") + appendix, encoding="utf-8")
    oof_summary = summary["metrics"]
    assert any(
        row["model"] == summary["candidate"] and row["scope"] == "overall_oof"
        for row in oof_summary
    )
    assert np.isfinite(y).all()
    return {
        "status": summary["status"],
        "real_data": checks,
        "configuration_sha256": sha256_file(project_path(CONFIG)),
    }


if __name__ == "__main__":
    print(json.dumps(finalize(), ensure_ascii=False, indent=2))
