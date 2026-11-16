"""Prepara tabelas e copia figuras da versão acadêmica 3, apenas de agregados leves."""

import csv
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "reports/monografia_template_200k_v3"
LABELS = {
    "baseline": "Baseline",
    "traditional": "Tradicional",
    "deep": "Profundo",
    "combined": "Combinado",
    "class_prior": "Proporções do treino",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path):
    if path.stat().st_size > 512 * 1024:
        raise ValueError("Tabela excede orçamento editorial de 512 KiB")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def fmt(value, decimals=2, percent=False):
    number = float(value) * (100 if percent else 1)
    return f"{number:.{decimals}f}".replace(".", ",")


def table(name, caption, label, spec, header, rows, note):
    lines = [
        r"\begin{table}[htbp]\centering\small",
        rf"\caption{{{caption}}}\label{{{label}}}",
        rf"\begin{{tabular}}{{{spec}}}\toprule",
        " & ".join(header) + r" \\\midrule",
        *[" & ".join(row) + r" \\" for row in rows],
        r"\bottomrule\end{tabular}",
        rf"\fonte{{Elaboração própria a partir das avaliações externas. {note}}}",
        r"\end{table}",
    ]
    (PROJECT / "tables" / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare():
    previous = PROJECT / "proveniencia_extensao.json"
    if previous.exists():
        expected = json.loads(previous.read_text(encoding="utf-8"))
        for name, value in expected["generated"].items():
            if digest(PROJECT / name) != value:
                raise ValueError(f"Preservar edição manual em {name}")
    sources = {
        "ordinal": ROOT / "reports/classificacao_ordinal_200k_v1/integral/metricas_externas.csv",
        "classes": ROOT / "reports/classificacao_ordinal_200k_v1/integral/metricas_por_classe.csv",
        "rules": ROOT / "reports/sensibilidade_decisao_ordinal_200k_v1/metricas_regras.csv",
        "rule_classes": ROOT
        / "reports/sensibilidade_decisao_ordinal_200k_v1/metricas_por_classe.csv",
        "comparison": ROOT
        / "reports/diagnosticos_classificacao_ordinal_200k_v1/comparacao_regressao_categorizada.csv",
    }
    inputs = {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in sources.values()}
    original = [
        row
        for row in read_rows(sources["ordinal"])
        if row["weighting"] == "equal_tracks" and row["outer_fold"] == "-1"
    ]
    if len(original) != 5 or any(int(row["n"]) != 77535 for row in original):
        raise ValueError("Agregados incompatíveis com cinco variantes/77.535 faixas")
    table(
        "classificacao.tex",
        "Desempenho da classificação ordinal: regra principal.",
        "tab:ordinal",
        "lrrrrr",
        ["Configuração", "AB (\\%)", "Ac. (\\%)", "Macro-F1", "Log-loss", "Brier"],
        [
            [
                LABELS[row["model"]],
                fmt(row["balanced_accuracy"], percent=True),
                fmt(row["accuracy"], percent=True),
                fmt(row["macro_f1"], 4),
                fmt(row["log_loss"], 4),
                fmt(row["brier_multiclass"], 4),
            ]
            for row in original
        ],
        "$n=77.535$. AB: acurácia balanceada; Ac.: acurácia comum. Pesos iguais por faixa; Brier soma as três classes.",
    )
    classes = [
        row
        for row in read_rows(sources["classes"])
        if row["model"] == "combined" and row["weighting"] == "equal_tracks"
    ]
    class_labels = {
        "0": ("Baixo (0--19)", "34.069"),
        "1": ("Intermediário (20--39)", "30.785"),
        "2": ("Elevado (40--100)", "12.681"),
    }
    table(
        "classes_ordinal.tex",
        "Desempenho por nível no Combinado: regra principal.",
        "tab:classesordinal",
        "lrrr",
        ["Nível observado", "Faixas", "Sensibilidade (\\%)", "Precisão (\\%)"],
        [
            [
                *class_labels[row["class_index"]],
                fmt(row["recall"], percent=True),
                fmt(row["precision"], percent=True),
            ]
            for row in classes
        ],
        "Níveis operacionais, sem definição oficial de sucesso musical.",
    )
    comparison = read_rows(sources["comparison"])
    table(
        "comparacao_categorica.tex",
        "Comparação sob os mesmos limites categóricos e folds.",
        "tab:comparacaocategorica",
        "lrrr",
        ["Configuração", "Ridge categ. (\\%)", "Ordinal (\\%)", "Diferença (p.p.)"],
        [
            [
                LABELS[row["model"]],
                fmt(row["regression_categorized_balanced_accuracy"], percent=True),
                fmt(row["ordinal_balanced_accuracy"], percent=True),
                fmt(row["delta_balanced_accuracy_pp"]),
            ]
            for row in comparison
        ],
        "Métrica: acurácia balanceada. Comparação exploratória entre procedimentos com critérios internos distintos.",
    )
    rules = [
        row
        for row in read_rows(sources["rules"])
        if row["model"] == "combined"
        and row["outer_fold"] == "-1"
        and row["weighting"] == "equal_tracks"
    ]
    by_rule = {row["decision_rule"]: row for row in rules}
    first, second = by_rule["argmax_original"], by_rule["inverse_training_prior"]
    values = [
        [label, fmt(first[key], percent=True), fmt(second[key], percent=True)]
        for label, key in [
            ("Acurácia balanceada", "balanced_accuracy"),
            ("Acurácia comum", "accuracy"),
            ("Erros extremos", "extreme_error_rate"),
        ]
    ]
    values.append(["Macro-F1", fmt(first["macro_f1"], 4), fmt(second["macro_f1"], 4)])
    rows = [
        row
        for row in read_rows(sources["rule_classes"])
        if row["model"] == "combined"
        and row["outer_fold"] == "-1"
        and row["weighting"] == "equal_tracks"
    ]
    indexed = {(row["decision_rule"], row["class_index"]): row for row in rows}
    for label, key, cls in [
        ("Sensibilidade baixa", "recall", "0"),
        ("Sensibilidade intermediária", "recall", "1"),
        ("Sensibilidade elevada", "recall", "2"),
        ("Precisão elevada", "precision", "2"),
    ]:
        values.append(
            [
                label,
                fmt(indexed[("argmax_original", cls)][key], percent=True),
                fmt(indexed[("inverse_training_prior", cls)][key], percent=True),
            ]
        )
    table(
        "regras_decisao.tex",
        "Sensibilidade da decisão no Combinado, com probabilidades fixas.",
        "tab:regras",
        "lrr",
        ["Medida", r"Principal: $\arg\max p$", r"Sensibilidade: $\arg\max p/\pi$"],
        values,
        "Valores em porcentagem, exceto Macro-F1. Não houve novo treinamento ou recalibração.",
    )
    figures = {
        "calibracao_combinado": "diagnosticos_classificacao_ordinal_200k_v1",
        "confusao_duas_regras": "analise_sensibilidade_decisao_ordinal_v1",
    }
    for name, directory in figures.items():
        for suffix in ("png", "svg"):
            source = ROOT / "reports" / directory / f"{name}.{suffix}"
            shutil.copyfile(source, PROJECT / "images" / source.name)
            inputs[str(source.relative_to(ROOT)).replace("\\", "/")] = digest(source)
    manifest = {
        "generator_sha256": digest(Path(__file__)),
        "inputs": inputs,
        "individual_data_read": False,
        "new_model_fits": 0,
        "generated": {
            str(p.relative_to(PROJECT)).replace("\\", "/"): digest(p)
            for p in (PROJECT / "tables").glob("*ordinal.tex")
        },
    }
    for name in ("classificacao.tex", "comparacao_categorica.tex", "regras_decisao.tex"):
        manifest["generated"]["tables/" + name] = digest(PROJECT / "tables" / name)
    for name in figures:
        for suffix in ("png", "svg"):
            relative = f"images/{name}.{suffix}"
            manifest["generated"][relative] = digest(PROJECT / relative)
    (PROJECT / "proveniencia_extensao.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Quatro tabelas e duas figuras de agregados preparadas; nenhum ajuste novo.")


if __name__ == "__main__":
    prepare()
