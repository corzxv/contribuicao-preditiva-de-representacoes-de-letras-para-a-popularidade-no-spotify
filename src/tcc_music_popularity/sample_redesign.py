"""Dimensionamento em agregados e sorteio manual separado da nova amostra."""

import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import NormalDist

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DESCRIPTION = ROOT / "reports/descritiva_catalogo_completo_v1"
REPORT = ROOT / "reports/nova_amostra_catalogo_v1"
PRIVATE = ROOT / "data/processed/nova_amostra_catalogo_v1"
SOURCE = ROOT / "data/raw/spotify/spotify_data.csv"
SEED = 20261106
CONFIDENCE = 0.95
MEAN_SD_MARGIN = 0.05
PROPORTION_MARGIN = 0.01


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def read_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def proportional_allocation(counts, size):
    """Maiores restos, com empate pela ordem alfabética previamente fixada."""
    counts = np.asarray(counts, dtype=np.int64)
    if size < 1 or size > int(counts.sum()) or np.any(counts < 1):
        raise ValueError("Tamanho/contagens incompatíveis com a população.")
    quotients, remainders = np.divmod(counts * size, int(counts.sum()))
    order = np.argsort(-remainders, kind="stable")
    quotients[order[: size - int(quotients.sum())]] += 1
    return quotients


def restored_variance(n, valid_n, mean, sd, variable):
    """Perfis usam BPM válido; reintroduz somente os zeros já documentados."""
    if valid_n != n and variable != "tempo":
        raise ValueError(f"Perdas não previstas no perfil de {variable}.")
    fraction = valid_n / n
    population_variance = fraction * (sd**2 + mean**2) - (fraction * mean) ** 2
    return max(population_variance, 0.0) * n / (n - 1)


def load_moments(description=DESCRIPTION):
    summary = read_json(description / "resumo_descritiva.json")
    if not summary["concluido"]:
        raise ValueError("Descrição não concluída.")
    names = ["perfis_grupos.csv", "resumo_numerico.csv", "frequencias_categoricas.csv"]
    for name in names:
        if sha256(description / name) != summary["arquivos"][name]:
            raise ValueError(f"Agregado alterado: {name}")
    numeric = [
        row
        for row in read_csv(description / "resumo_numerico.csv")
        if row["escopo"] == "todos_finitos"
    ]
    groups = read_csv(description / "perfis_grupos.csv")
    genres = sorted(
        (r for r in groups if r["agrupamento"] == "genre" and r["variavel"] == "popularity"),
        key=lambda r: r["categoria"],
    )
    counts = np.array([int(r["n_grupo"]) for r in genres], dtype=np.int64)
    total = int(counts.sum())
    if total != summary["n_faixas"]:
        raise ValueError("Contagens de gênero não reconciliadas.")
    variances = []
    for row in numeric:
        if int(row["n"]) != total:
            raise ValueError("Metadado com valores ausentes exige novo tratamento explícito.")
        by_genre = {
            r["categoria"]: r
            for r in groups
            if r["agrupamento"] == "genre" and r["variavel"] == row["variavel"]
        }
        within, means = [], []
        for genre, n in zip(genres, counts, strict=True):
            r = by_genre[genre["categoria"]]
            valid_n = int(r["n_validos"])
            mean = float(r["media"])
            within.append(
                restored_variance(
                    int(n), valid_n, mean, float(r["dp_populacional"]), row["variavel"]
                )
            )
            means.append(valid_n / n * mean)
        mean = float(counts @ np.array(means) / total)
        variance = float(
            (np.array(within) * (counts - 1) + counts * (np.array(means) - mean) ** 2).sum()
            / (total - 1)
        )
        if not np.isclose(mean, float(row["media"]), atol=1e-8, rtol=1e-10):
            raise ValueError(f"Média não reconciliada: {row['variavel']}")
        if not np.isclose(variance, float(row["variancia_divisor_n_menos_1"]), rtol=1e-8):
            raise ValueError(f"Variância não reconciliada: {row['variavel']}")
        variances.append(within)
    return summary, genres, counts, numeric, np.array(variances)


def precision(counts, allocation, variances, population_sd):
    weights = counts / counts.sum()
    factor = weights**2 * (1 / allocation - 1 / counts)
    mean_variances = variances @ factor
    z = NormalDist().inv_cdf((1 + CONFIDENCE) / 2)
    z_family = NormalDist().inv_cdf(1 - (1 - CONFIDENCE) / (2 * len(population_sd)))
    margins = z_family * np.sqrt(np.maximum(mean_variances, 0))
    binary_variance_bound = float(np.sum(factor * counts / (4 * (counts - 1))))
    return {
        "proportion_margin_bound": z * np.sqrt(max(binary_variance_bound, 0)),
        "mean_margins_family": margins,
        "mean_margins_sd": margins / population_sd,
        "mean_variances": mean_variances,
        "z_individual": z,
        "z_family": z_family,
    }


def choose_size(counts, variances, population_sd, proportion_margin=PROPORTION_MARGIN):
    # Busca sequencial: maiores restos não têm monotonicidade garantida a cada n.
    for size in range(2 * len(counts), min(int(counts.sum()), 50_000) + 1):
        allocation = proportional_allocation(counts, size)
        if np.any(allocation < 2):
            continue
        result = precision(counts, allocation, variances, population_sd)
        if (
            result["proportion_margin_bound"] <= proportion_margin
            and max(result["mean_margins_sd"]) <= MEAN_SD_MARGIN
        ):
            return size, allocation, result
    raise ValueError("Nenhum tamanho até 50 mil satisfaz as metas; revisar plano.")


def dimension(description=DESCRIPTION, report=REPORT):
    if report.exists() and any(report.iterdir()):
        raise FileExistsError("Plano já existe; preservar a versão e usar seus arquivos.")
    summary, genres, counts, numeric, variances = load_moments(description)
    population_sd = np.sqrt([float(r["variancia_divisor_n_menos_1"]) for r in numeric])
    scenarios = []
    selected = None
    for margin in [0.02, 0.015, PROPORTION_MARGIN]:
        size, allocation, result = choose_size(counts, variances, population_sd, margin)
        scenarios.append(
            {
                "margem_proporcao_pp": margin * 100,
                "n": size,
                "limite_margem_proporcao_pp": float(result["proportion_margin_bound"] * 100),
                "maior_margem_media_em_dp_bonferroni": float(max(result["mean_margins_sd"])),
            }
        )
        if margin == PROPORTION_MARGIN:
            selected = size, allocation, result
    size, allocation, result = selected
    report.mkdir(parents=True, exist_ok=True)
    allocation_rows = [
        {
            "genero": row["categoria"],
            "N_h": int(n),
            "n_h": int(nh),
            "pi_h": float(nh / n),
            "peso_h": float(n / nh),
            "fracao_catalogo": float(n / counts.sum()),
            "fracao_amostra": float(nh / size),
        }
        for row, n, nh in zip(genres, counts, allocation, strict=True)
    ]
    precision_rows = [
        {
            "variavel": row["variavel"],
            "unidade": row["unidade"],
            "media_catalogo": float(row["media"]),
            "dp_catalogo": float(sd),
            "variancia_media_desenho": float(v),
            "margem_95_individual": float(result["z_individual"] * np.sqrt(v)),
            "margem_95_familia_12": float(m),
            "margem_familia_em_dp": float(m / sd),
        }
        for row, sd, v, m in zip(
            numeric,
            population_sd,
            result["mean_variances"],
            result["mean_margins_family"],
            strict=True,
        )
    ]
    write_csv(report / "alocacao_generos.csv", allocation_rows)
    write_csv(report / "precisao_metadados.csv", precision_rows)
    write_csv(report / "cenarios_tamanho.csv", scenarios)
    plan = {
        "plano_concluido": True,
        "sorteio_executado": False,
        "criado_em": datetime.now(UTC).isoformat(),
        "decisao": "D-030",
        "N": int(counts.sum()),
        "n": size,
        "generos": len(counts),
        "seed": SEED,
        "desenho": "AAS sem reposição independente nos 82 gêneros; alocação proporcional por maiores restos",
        "meta_proporcao_margem": PROPORTION_MARGIN,
        "confianca_individual_proporcao_aproximada": CONFIDENCE,
        "meta_medias_margem_em_dp": MEAN_SD_MARGIN,
        "confianca_familia_medias_aproximada": CONFIDENCE,
        "ajuste_familia_medias": "Bonferroni para 12 médias, aproximação normal",
        "limite_margem_proporcao": float(result["proportion_margin_bound"]),
        "maior_margem_media_em_dp": float(max(result["mean_margins_sd"])),
        "z_individual": result["z_individual"],
        "z_familia": result["z_family"],
        "source_sha256": summary["fontes"]["csv_sha256"],
        "source_bytes": summary["source_bytes"],
        "description_sha256": sha256(description / "resumo_descritiva.json"),
        "code_sha256": sha256(Path(__file__)),
        "arquivos": {
            name: sha256(report / name)
            for name in ["alocacao_generos.csv", "precisao_metadados.csv", "cenarios_tamanho.csv"]
        },
        "csv_individual_lido_pelo_agente": False,
        "letras_buscadas": False,
        "treino": False,
        "limites": [
            "Metas referem-se ao sorteio completo antes da recuperação de letras.",
            "A margem de proporção é individual; não simultânea para todas as categorias.",
            "Não há precisão assegurada para gêneros raros ou popularidade extrema.",
            "Igualdade de distribuições, precisão preditiva e sucesso de recuperação não são garantidos.",
            "BPM zero permanece no universo; reconstrução dos momentos incluiu os 1.199 zeros documentados.",
        ],
    }
    write_json(report / "plano_amostral.json", plan)
    print(
        json.dumps(
            {
                "etapa": "dimensionamento",
                "N": plan["N"],
                "n": size,
                "n_h_min": int(min(allocation)),
                "n_h_max": int(max(allocation)),
                "sorteio_executado": False,
            }
        )
    )
    return plan


def select_frame(frame, allocation_rows, seed):
    """Sorteio por posições no cadastro de bytes selados; campos originais intactos."""
    import polars as pl

    if any(name.startswith("_nova_") for name in frame.columns):
        raise ValueError("Entrada já possui campos reservados da nova amostra.")
    indexed = frame.with_row_index("_nova_linha_fonte")
    positions = {
        key[0]: part["_nova_linha_fonte"].to_numpy()
        for key, part in indexed.select("genre", "_nova_linha_fonte")
        .partition_by("genre", as_dict=True)
        .items()
    }
    expected = {r["genero"] for r in allocation_rows}
    if set(positions) != expected:
        raise ValueError("Gêneros da fonte diferem do plano.")
    selections = []
    for index, row in enumerate(sorted(allocation_rows, key=lambda r: r["genero"])):
        n, nh = int(row["N_h"]), int(row["n_h"])
        indexes = positions[row["genero"]]
        if len(indexes) != n:
            raise ValueError(f"N_h divergente: {row['genero']}")
        generator = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, index])))
        selected = np.sort(generator.choice(n, size=nh, replace=False))
        selections.extend(indexes[selected].tolist())
    selected = indexed[sorted(selections)]
    if selected["track_id"].null_count() or selected["track_id"].n_unique() != len(selected):
        raise ValueError("IDs ausentes ou repetidos na amostra.")
    allocations = pl.DataFrame(
        [
            {
                "genre": r["genero"],
                "_nova_N_h": int(r["N_h"]),
                "_nova_n_h": int(r["n_h"]),
                "_nova_pi": int(r["n_h"]) / int(r["N_h"]),
                "_nova_peso": int(r["N_h"]) / int(r["n_h"]),
            }
            for r in allocation_rows
        ]
    )
    return selected.join(
        allocations, on="genre", how="left", validate="m:1", maintain_order="left"
    ).with_columns(pl.lit(seed).alias("_nova_seed"), pl.lit("catalogo_v1").alias("_nova_desenho"))


def compare_metadata(sample, description, report):
    """Diagnóstico do único sorteio, sem descartar faixas para aproximar médias."""
    import polars as pl

    summary, _, _, numeric, _ = load_moments(description)
    weights = sample["_nova_peso"].to_numpy()
    comparisons = []
    for row in numeric:
        values = sample[row["variavel"]].cast(pl.Float64, strict=True).to_numpy()
        if row["variavel"] == "duration_ms":
            values = values / 1000
        mean = float(np.average(values, weights=weights))
        item = {
            "variavel": row["variavel"],
            "unidade": row["unidade"],
            "n": len(values),
            "media_catalogo": float(row["media"]),
            "media_amostra_ponderada": mean,
            "media_amostra_nao_ponderada": float(values.mean()),
            "diferenca_medias_em_dp": (mean - float(row["media"]))
            / np.sqrt(float(row["variancia_divisor_n_menos_1"])),
            "dp_catalogo": float(row["dp_populacional"]),
            "dp_amostra_nao_ponderado": float(values.std(ddof=1)),
        }
        for label, fraction in [
            ("p05", 0.05),
            ("p25", 0.25),
            ("mediana", 0.5),
            ("p75", 0.75),
            ("p95", 0.95),
        ]:
            item[f"{label}_catalogo"] = float(row[label])
            item[f"{label}_amostra_nao_ponderado"] = float(np.quantile(values, fraction))
        comparisons.append(item)
    write_csv(report / "comparacao_metadados.csv", comparisons)
    categories = read_csv(description / "frequencias_categoricas.csv")
    category_rows = []
    for variable in sorted({r["variavel"] for r in categories}):
        if variable == "periodo":
            years = sample["year"].cast(pl.Int32).to_numpy()
            observed = np.where(
                years <= 2009, "2000–2009", np.where(years <= 2019, "2010–2019", "2020–2023")
            )
        elif variable in sample.columns:
            observed = sample[variable].to_numpy()
        else:
            raise ValueError(f"Categoria sem tratamento explícito: {variable}")
        for r in categories:
            if r["variavel"] != variable:
                continue
            mask = observed == r["categoria"]
            fraction = float(weights[mask].sum() / summary["n_faixas"])
            category_rows.append(
                {
                    "variavel": variable,
                    "categoria": r["categoria"],
                    "n_catalogo": int(r["n"]),
                    "n_amostra": int(mask.sum()),
                    "fracao_catalogo": float(r["fracao"]),
                    "fracao_amostra_ponderada": fraction,
                    "diferenca_pp": 100 * (fraction - float(r["fracao"])),
                }
            )
    write_csv(report / "comparacao_categorias.csv", category_rows)


def draw(report=REPORT, description=DESCRIPTION, source=SOURCE, private=PRIVATE):
    import polars as pl

    print("[1/4] Conferindo plano e fonte original; sem letras ou modelos...", flush=True)
    plan = read_json(report / "plano_amostral.json")
    if sha256(Path(__file__)) != plan["code_sha256"]:
        raise ValueError("Código difere do dimensionamento selado.")
    if sha256(description / "resumo_descritiva.json") != plan["description_sha256"]:
        raise ValueError("Descrição difere do plano.")
    for name, value in plan["arquivos"].items():
        if sha256(report / name) != value:
            raise ValueError(f"Plano alterado: {name}")
    completed = report / "resumo_sorteio.json"
    if completed.exists():
        result = read_json(completed)
        if (
            not result["concluido"]
            or sha256(private / "amostra_spotify.parquet") != result["parquet_sha256"]
        ):
            raise ValueError("Saída prévia incompleta ou alterada; preservar e investigar.")
        for name, value in result["agregados_sha256"].items():
            if sha256(report / name) != value:
                raise ValueError(f"Diagnóstico prévio alterado: {name}")
        print("Amostra existente conferida; nenhum novo sorteio.")
        return result
    if (private / "amostra_spotify.parquet").exists():
        raise FileExistsError("Parquet sem resumo de conclusão; preservar e investigar.")
    if source.stat().st_size != plan["source_bytes"] or sha256(source) != plan["source_sha256"]:
        raise ValueError("CSV original diverge do cadastro dimensionado.")
    print(f"[2/4] Sorteando {plan['n']:,} faixas nos gêneros; semente fixa...", flush=True)
    frame = pl.read_csv(source, infer_schema=False)
    if len(frame) != plan["N"]:
        raise ValueError("Total do cadastro diverge do plano.")
    sample = select_frame(frame, read_csv(report / "alocacao_generos.csv"), plan["seed"])
    if len(sample) != plan["n"] or not np.isclose(sample["_nova_peso"].sum(), plan["N"]):
        raise ValueError("Tamanho ou soma dos pesos divergente.")
    print(
        "[3/4] Comparando médias, dispersões, quantis e categorias; sem ressorteio...", flush=True
    )
    compare_metadata(sample, description, report)
    private.mkdir(parents=True, exist_ok=True)
    path = private / "amostra_spotify.parquet"
    temporary = private / "amostra_spotify.parquet.tmp"
    sample.write_parquet(temporary)
    temporary.replace(path)
    result = {
        "concluido": True,
        "criado_em": datetime.now(UTC).isoformat(),
        "N": plan["N"],
        "n": len(sample),
        "seed": plan["seed"],
        "source_sha256": plan["source_sha256"],
        "plano_sha256": sha256(report / "plano_amostral.json"),
        "parquet": str(path),
        "parquet_sha256": sha256(path),
        "soma_pesos": sample["_nova_peso"].sum(),
        "agregados_sha256": {
            name: sha256(report / name)
            for name in ["comparacao_metadados.csv", "comparacao_categorias.csv"]
        },
        "letras_buscadas": False,
        "modelos_treinados": False,
        "amostra_200k_alterada": False,
        "ressorteio_por_desempenho": False,
    }
    write_json(completed, result)
    print(f"[4/4] Concluído. Comparativos em {report}", flush=True)
    return result


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("etapa", choices=["dimensionar", "sortear"])
    args = parser.parse_args(argv)
    if args.etapa == "dimensionar":
        dimension()
    else:
        draw()
    return 0
