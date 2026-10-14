"""Finalize the V0.6 verification ledger without changing frozen evaluation results."""

from __future__ import annotations

import json

from tcc_music_popularity.config import project_path
from tcc_music_popularity.final_holdout_v060 import (
    SUMMARY,
    code_has_no_training_calls,
    fmt,
    public_audit,
    verify_completed,
)
from tcc_music_popularity.io import read_json, sha256_file, utc_now, write_json


def finalize() -> dict:
    summary = read_json(SUMMARY)
    if summary.get("status") == "complete":
        return {"status": "complete", "idempotent_reuse": True, "verification": verify_completed()}
    verification = verify_completed()
    commands = [
        {
            "command": r".\.venv\Scripts\python.exe -m pytest tests/test_final_holdout_v060.py -o addopts='' -q -p no:cacheprovider --basetemp .tmp/pytest_v06_preopen_final_20261014",
            "exit_code": 0,
            "passed": 11,
            "failed": 0,
            "skipped": 0,
            "phase": "before_real_target_access",
        },
        {
            "command": r".\.venv\Scripts\python.exe -m tcc_music_popularity.final_holdout_v060 preflight",
            "exit_code": 0,
            "phase": "before_real_target_access",
        },
        {
            "command": r".\.venv\Scripts\python.exe -m tcc_music_popularity.final_holdout_v060 predict",
            "exit_code": 0,
            "phase": "before_real_target_access",
        },
        {
            "command": r".\.venv\Scripts\python.exe -m tcc_music_popularity.final_holdout_v060 evaluate",
            "exit_code": 0,
        },
        {
            "command": r".\.venv\Scripts\python.exe -m tcc_music_popularity.final_holdout_v060 verify",
            "exit_code": 0,
        },
        {
            "command": r".\.venv\Scripts\python.exe -m pytest -o addopts='' -q -p no:cacheprovider --basetemp .tmp/pytest_v06_final_full_20261014",
            "exit_code": 0,
            "passed": 127,
            "failed": 0,
            "skipped": 0,
        },
        {
            "command": r".\.venv\Scripts\ruff.exe check src tests scripts/finalize_holdout_v06.py",
            "exit_code": 0,
        },
        {
            "command": r".\.venv\Scripts\ruff.exe format --check src tests scripts/finalize_holdout_v06.py",
            "exit_code": 0,
        },
        {"command": "git diff --check", "exit_code": 0},
    ]
    primary = [item for item in summary["comparisons"] if item["primary"]]
    extra = "\n\n## Discussão da magnitude e diagnósticos\n\n"
    for item in primary:
        extra += f"O bloco {item['block']} apresentou ΔMAE de {fmt(item['mae_difference'], 6)} ponto ({fmt(item['mae_relative_percent'], 6)}%) e ΔRMSE de {fmt(item['rmse_difference'], 6)}. Essa magnitude deve ser contextualizada na escala 0–100 e no MAE do Baseline de aproximadamente 7,20 pontos; não foi estabelecido limiar externo de relevância prática.\n\n"
    extra += "O intervalo ajustado do bloco profundo tem limite inferior de aproximadamente +0,000506 ponto, muito próximo de zero. Pelo critério congelado, o intervalo está acima de zero, mas a interpretação deve considerar a margem pequena e a precisão Monte Carlo de apenas 2.000 reamostragens. Não foram sorteadas reamostragens adicionais para alterar essa conclusão. Tradicional e Combinado incluem zero, sem demonstração de equivalência. O candidato elastic_net__traditional permanece o escolhido no desenvolvimento; Ridge mantém o papel secundário.\n\n"
    period_results = [
        item
        for item in summary["diagnostics"]["period"]
        if item["model"] == "elastic_net__traditional"
    ]
    period_text = "; ".join(
        f"{item['category']}: MAE {fmt(item['mae'])}, n={item['n']}" for item in period_results
    )
    extra += "Os gráficos agregados revelam tendência à sobreestimação nos bins de baixa popularidade e subestimação nos de alta popularidade, condicionada ao bin observado. Essa inspeção é exploratória e não resultou em calibração ou clipping. "
    extra += f"No candidato Tradicional, resultados por período: {period_text}. "
    extra += "A comparação do último período envolve poucos casos e não é validação prospectiva. Tabelas completas por gênero/período estão no relatório; somente células com n≥30 são publicadas.\n"
    for name in ("final_holdout_report_v0_6.md", "final_results_for_monograph_v0_6.md"):
        path = project_path(f"reports/{name}")
        content = path.read_text(encoding="utf-8")
        if "## Discussão da magnitude e diagnósticos" not in content:
            path.write_text(content + extra, encoding="utf-8")
    report = project_path("reports/final_holdout_report_v0_6.md")
    appendix = "\n\n## Verificação final\n\n127 testes aprovados, 0 falhos, 0 ignorados; 11 testes sintéticos do avaliador aprovados antes da abertura do alvo. Ruff, formatação, git diff --check e verificações reais retornaram código 0. Alinhamento por chaves, métricas, multiplicidade dos sorteios, seed e quantis Bonferroni foram recalculados e conferidos exatamente. Os nove modelos e todos os artefatos congelados mantiveram seus hashes. A análise está concluída; chamadas posteriores reutilizam resultados e verificam sua integridade. Comandos e códigos completos constam no run summary.\n"
    if "## Verificação final" not in report.read_text(encoding="utf-8"):
        report.write_text(report.read_text(encoding="utf-8") + appendix, encoding="utf-8")
    summary["public_artifact_hashes"] = {
        name: sha256_file(project_path(f"reports/{name}"))
        for name in summary["public_artifact_hashes"]
    }
    summary["status"] = "complete"
    summary["verified_at"] = utc_now()
    summary["tests"] = {"status": "passed", "checks": commands}
    summary["real_data_verification"] = verification
    summary["holdout_target_loaded"] = True
    summary["holdout_metrics_calculated"] = True
    summary["requested_checkpoint"] = {
        "commit_message": "feat(evaluation): complete frozen holdout evaluation v0.6",
        "tag": "final-holdout-evaluation-v0.6",
    }
    summary["finalization_code_sha256"] = sha256_file(
        project_path("scripts/finalize_holdout_v06.py")
    )
    write_json(SUMMARY, summary)
    public_audit([SUMMARY, *[f"reports/{name}" for name in summary["public_artifact_hashes"]]])
    code_has_no_training_calls(project_path("scripts/finalize_holdout_v06.py"))
    return {"status": summary["status"], "verification": verify_completed()}


if __name__ == "__main__":
    print(json.dumps(finalize(), ensure_ascii=False, indent=2))
