"""Coorte aceita: preparação e descrição offline, sem ajuste de modelos reais automático."""

from __future__ import annotations

import argparse
import hashlib
import json
from contextlib import closing
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.model_selection import GroupKFold

from .final_study_v040 import load_target_free_source, select_representatives_without_target
from .io import sha256_file, utc_now
from .manual_lyrics import connect
from .modeling_pilot_v030 import FORBIDDEN_PREDICTORS

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "data/derived/private_statistical_cohort_v1"
AUDITS = ROOT / "data/derived/private_local_lyrics_audit"
LOCAL = ROOT / "data/derived/private_local_lyrics_v1"
BASE = ROOT / "data/processed/modeling_base_lfm_v0_1_1.parquet"
SPLIT = ROOT / "data/processed/split_assignments_v0_1_1.parquet"
MATCH = ROOT / "data/processed/matching_audit_v0_1_1.parquet"
MANIFEST = ROOT / "reports/final_model_manifest_v0_5.json"
DICTIONARY = ROOT / "reports/feature_manifest_v0_1_1_revision.csv"
PROTOCOL = ROOT / "docs/protocolo_coorte_aceita_v1.md"
TARGET = "spotify_popularity"
SEED = 20261028
CATEGORIES = ["genre", "key", "time_signature"]
GROUPS = ["artist_group_id", "composition_key", "composition_group_id", "split_group_id"]
HASHES = ["source_strict_sha256", "lyrics_sha256"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    temporary.replace(path)


def workspace(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT / "data/derived"), "Use saída privada em data/derived.")
    require(path.name.startswith("private_statistical_cohort_"), "Prefixo de saída não permitido.")
    return path


def features(manifest=MANIFEST):
    original = read_json(manifest)
    allowed = original["allowed_features"]
    baseline, lyrics = list(allowed["baseline"]), list(allowed["lfm"])
    require(len(baseline) == 23 and len(lyrics) == 196, "Manifesto não tem 23 + 196 atributos.")
    require(len(set(baseline + lyrics)) == 219, "Atributos duplicados.")
    require(not set(baseline + lyrics) & FORBIDDEN_PREDICTORS, "Preditor proibido.")
    for block, columns in (("baseline", baseline), ("traditional", baseline + lyrics)):
        old = next(m for m in original["models"] if m["model"] == f"elastic_net__{block}")
        require(old["input_columns"] == columns, "Manifesto e input antigo divergem.")
    return {"baseline": baseline, "lfm": lyrics}


def development_table(path, columns):
    """O filtro precede a materialização: nunca devolve alvos do holdout."""
    require("split" in columns, "A leitura precisa carregar split para validação.")
    result = (
        pl.scan_parquet(path)
        .filter(pl.col("split") == "development_train")
        .select(columns)
        .collect()
    )
    require(result["split"].unique().to_list() == ["development_train"], "Split inválido.")
    return result


def components(frame, columns):
    """União transitiva: artista OU composição OU hash compartilhado não cruza folds."""
    n = frame.height
    parent = list(range(n))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for column in columns:
        first = {}
        for i, value in enumerate(frame[column].to_list()):
            if value is None or str(value) == "":
                continue
            key = str(value)
            if key in first:
                a, b = root(i), root(first[key])
                parent[max(a, b)] = min(a, b)
            else:
                first[key] = i
    ids = frame["track_id"].cast(pl.String).to_list()
    labels = {}
    for i, track in enumerate(ids):
        r = root(i)
        labels[r] = min(track, labels.get(r, track))
    return [hashlib.sha256(labels[root(i)].encode()).hexdigest()[:24] for i in range(n)]


def partition_plan(frame):
    groups = frame["analysis_group"].to_numpy()
    require(len(set(groups)) >= 5, "Menos de cinco componentes independentes.")
    outer = np.full(len(groups), -1, dtype=int)
    inner = {}
    splitter = GroupKFold(5, shuffle=True, random_state=SEED)
    for fold, (train, valid) in enumerate(splitter.split(groups, groups=groups)):
        outer[valid] = fold
        require(len(set(groups[train])) >= 3, "Treino sem grupos para três folds internos.")
        parts = []
        nested = GroupKFold(3, shuffle=True, random_state=SEED + fold + 1)
        for a, b in nested.split(train, groups=groups[train]):
            parts.append({"train": train[a].tolist(), "valid": train[b].tolist()})
        inner[str(fold)] = parts
    plan = {"outer": outer.tolist(), "inner": inner}
    validate_plan(frame, plan)
    return plan


def validate_plan(frame, plan):
    outer = np.array(plan["outer"])
    require(len(outer) == frame.height and set(outer) == set(range(5)), "Folds inválidos.")
    for fold in range(5):
        train, valid = np.flatnonzero(outer != fold), np.flatnonzero(outer == fold)
        pairs = [(train, valid)]
        seen = []
        for part in plan["inner"][str(fold)]:
            a, b = np.asarray(part["train"], int), np.asarray(part["valid"], int)
            require(set(a).isdisjoint(b) and set(a) | set(b) == set(train), "Fuga no fold interno.")
            seen.extend(b.tolist())
            pairs.append((a, b))
        require(
            sorted(seen) == sorted(train.tolist()), "Validação interna não cobre treino uma vez."
        )
        for a, b in pairs:
            require(len(a) and len(b), "Partição vazia.")
            for column in [*GROUPS, *HASHES, "analysis_group"]:
                av = set(frame[column].gather(a).drop_nulls().to_list()) - {""}
                bv = set(frame[column].gather(b).drop_nulls().to_list()) - {""}
                require(not av & bv, f"Sobreposição de {column} no fold {fold}.")


def numerical_summary(values):
    x = np.asarray(values, float)
    finite = x[np.isfinite(x)]
    result = {"n": len(x), "missing_or_nonfinite": int((~np.isfinite(x)).sum())}
    if not len(finite):
        return {**result, "finite": 0}
    std = float(finite.std(ddof=1)) if len(finite) > 1 else 0.0
    centered = finite - finite.mean()
    m2 = np.mean(centered**2)
    return {
        **result,
        "finite": len(finite),
        "mean": float(finite.mean()),
        "std": std,
        "skew_moment": float(np.mean(centered**3) / m2**1.5) if m2 else None,
        "excess_kurtosis_moment": float(np.mean(centered**4) / m2**2 - 3) if m2 else None,
        **{f"q{q:g}": float(np.percentile(finite, q)) for q in (0, 1, 5, 25, 50, 75, 95, 99, 100)},
        "zero_n": int((finite == 0).sum()),
        "hundred_n": int((finite == 100).sum()),
    }


def high_correlations(frame, numeric, minimum=30, threshold=0.8):
    """Spearman exato por pares completos, reaproveitando padrões de ausência.

    Ranqueia uma vez por interseção de máscaras, em vez de reranquear 58 mil
    linhas para cada um dos aproximadamente 24 mil pares de atributos.
    """
    from scipy.stats import rankdata
    from threadpoolctl import threadpool_limits

    values = frame.select(pl.col(numeric).cast(pl.Float64)).to_numpy()
    patterns = {}
    for i in range(len(numeric)):
        mask = np.isfinite(values[:, i])
        key = np.packbits(mask).tobytes()
        if key not in patterns:
            patterns[key] = (mask, [])
        patterns[key][1].append(i)
    groups = list(patterns.values())
    pairs = []
    for a, (mask_a, cols_a) in enumerate(groups):
        for mask_b, cols_b in groups[a:]:
            mask = mask_a & mask_b
            n = int(mask.sum())
            if n < minimum:
                continue
            columns = list(dict.fromkeys(cols_a + cols_b))
            ranks = rankdata(values[np.ix_(mask, columns)], axis=0)
            ranks -= ranks.mean(axis=0)
            scale = np.sqrt(np.sum(ranks**2, axis=0))
            ranks /= np.where(scale > 0, scale, 1)
            with threadpool_limits(limits=4):
                correlation = ranks.T @ ranks
            lookup = {c: i for i, c in enumerate(columns)}
            same = cols_a is cols_b
            for left in cols_a:
                for right in cols_b:
                    if left == right or (same and left > right):
                        continue
                    i, j = lookup[left], lookup[right]
                    rho = float(np.clip(correlation[i, j], -1, 1))
                    if scale[i] > 0 and scale[j] > 0 and abs(rho) >= threshold:
                        pairs.append(
                            {
                                "left": numeric[min(left, right)],
                                "right": numeric[max(left, right)],
                                "n": n,
                                "spearman": rho,
                            }
                        )
    return pairs


def descriptive(frame, allowed, output):
    """Descrições empíricas; não escolhe família probabilística por teste de normalidade."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.stats import norm, spearmanr

    output.mkdir(exist_ok=True)
    columns = [*allowed["baseline"], *allowed["lfm"]]
    rows, categories, numeric = [], [], []
    for column in [TARGET, *columns]:
        series = frame[column]
        item = {"name": column, "dtype": str(series.dtype), "cardinality": series.n_unique()}
        if column in CATEGORIES:
            item.update(n=frame.height, missing_or_nonfinite=series.null_count())
            for row in (
                frame.group_by(column)
                .agg(
                    pl.len().alias("n"),
                    pl.col(TARGET).mean().alias("mean_y"),
                    pl.col(TARGET).median().alias("median_y"),
                )
                .to_dicts()
            ):
                categories.append({"variable": column, "category": str(row.pop(column)), **row})
        else:
            values = series.cast(pl.Float64).to_numpy()
            item.update(numerical_summary(values))
            if column != TARGET:
                numeric.append(column)
                ok = np.isfinite(values)
                y = frame[TARGET].to_numpy()
                item["spearman_n"] = int(ok.sum())
                item["spearman_y"] = (
                    float(spearmanr(values[ok], y[ok]).statistic)
                    if ok.sum() > 2 and np.ptp(values[ok]) and np.ptp(y[ok])
                    else None
                )
        rows.append(item)
    pl.DataFrame(rows, infer_schema_length=None).write_csv(output / "column_summary.csv")
    pl.DataFrame(categories).write_csv(output / "category_summary.csv")
    binned = []
    y = frame[TARGET].to_numpy()
    for column in numeric:
        values = frame[column].cast(pl.Float64).to_numpy()
        valid = np.isfinite(values)
        if not valid.any():
            continue
        edges = np.unique(np.quantile(values[valid], np.linspace(0, 1, 11)))
        for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:], strict=True)):
            mask = (
                valid & (values >= lo) & ((values <= hi) if i == len(edges) - 2 else (values < hi))
            )
            if mask.any():
                binned.append(
                    {
                        "variable": column,
                        "lower": float(lo),
                        "upper": float(hi),
                        "n": int(mask.sum()),
                        "mean_x": float(values[mask].mean()),
                        "mean_y": float(y[mask].mean()),
                        "median_y": float(np.median(y[mask])),
                    }
                )
    pl.DataFrame(binned).write_csv(output / "binned_relationships.csv")
    print("Descrição: correlações por pares completos e distribuição da resposta.", flush=True)
    pairs = high_correlations(frame, numeric)
    pl.DataFrame(
        pairs, schema={"left": pl.String, "right": pl.String, "n": pl.Int64, "spearman": pl.Float64}
    ).write_csv(output / "correlated_pairs.csv")
    y = frame[TARGET].to_numpy()
    hist, edges = np.histogram(y, bins=np.arange(0, 101, 10))
    pl.DataFrame(
        {"lower": edges[:-1], "upper": edges[1:], "n": hist, "proportion": hist / len(y)}
    ).write_csv(output / "target_bins.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    axes[0].hist(y, bins=np.arange(-0.5, 101, 1))
    axes[0].set(
        title="Popularidade no desenvolvimento", xlabel="Popularidade", ylabel="Composições"
    )
    ordered = np.sort(y)
    axes[1].plot(ordered, np.arange(1, len(y) + 1) / len(y))
    axes[1].set(
        title="Distribuição acumulada empírica", xlabel="Popularidade", ylabel="Fração acumulada"
    )
    p = (np.arange(len(y)) + 0.5) / len(y)
    axes[2].plot(norm.ppf(p), ordered, linewidth=1)
    axes[2].set(
        title="QQ marginal: não é diagnóstico dos resíduos",
        xlabel="Quantil normal",
        ylabel="Popularidade",
    )
    fig.tight_layout()
    fig.savefig(output / "target_distribution.png", dpi=150)
    plt.close(fig)
    sizes = frame.group_by("analysis_group").len()["len"].to_numpy()
    save_json(
        output / "summary.json",
        {
            "rows": frame.height,
            "artists": frame["artist_group_id"].n_unique(),
            "compositions": frame["composition_key"].n_unique(),
            "components": len(sizes),
            "component_size": numerical_summary(sizes),
            "target": numerical_summary(y),
            "high_correlation_pairs": len(pairs),
            "holdout_targets_loaded": False,
        },
    )
    (output / "leitura.md").write_text(
        f"# Descrição da coorte aceita — desenvolvimento\n\n{frame.height:,} representantes por composição operacional; "
        f"{len(sizes):,} componentes de validação.\n\n"
        "Leia target_distribution.png, target_bins.csv, column_summary.csv e category_summary.csv. "
        "binned_relationships.csv descreve relações por até dez faixas de quantis de cada preditora numérica, sem ajuste ou teste. "
        "correlated_pairs.csv lista |Spearman| ≥ 0,8 com pelo menos 30 pares completos. "
        "Ausências não foram imputadas nesta descrição. Correlações são exploratórias, sem testes múltiplos ou seleção de atributos. "
        "QQ da resposta marginal não testa os pressupostos dos erros de uma regressão. "
        "Não há ajuste automático de uma distribuição nem decisão de modelo pelo histograma.\n\n"
        "O alvo é um índice de snapshot, não uma contagem de eventos nem uma proporção binomial. "
        "Não se removeu nenhum caso por popularidade extrema. "
        "A disponibilidade de letras condiciona a amostra; coverage.csv descreve esse mecanismo no desenvolvimento.\n",
        encoding="utf-8",
    )


def code_paths():
    # Dependências científicas efetivamente reutilizadas também ficam seladas.
    names = [
        "cohort_statistics.py",
        "cohort_regression.py",
        "final_study_v040.py",
        "modeling_pilot_v030.py",
        "statistical_revision_v080.py",
    ]
    return [ROOT / "src/tcc_music_popularity" / n for n in names] + [PROTOCOL]


def prepare(output, audit_path=None):
    output = workspace(output)
    require(
        not output.exists(), "Saída já existe. Use --status ou outro --workspace; não sobrescrevo."
    )
    audits = sorted(AUDITS.glob("*/summary.json"))
    require(audit_path is not None or audits, "Conclua a auditoria 08 primeiro.")
    audit = Path(audit_path) if audit_path else audits[-1].parent
    summary, provenance = read_json(audit / "summary.json"), read_json(audit / "provenance.json")
    require(
        summary["complete"] and not summary["review_required"],
        "Auditoria incompleta ou com alertas.",
    )
    state = LOCAL / "state.sqlite"
    require(
        not Path(str(state) + "-wal").exists() or Path(str(state) + "-wal").stat().st_size == 0,
        "Checkpoint com WAL ativo: finalize a coleta.",
    )
    require(
        sha256_file(state) == provenance["inputs_after"]["local"],
        "Auditoria desatualizada: checkpoint mudou.",
    )
    require(
        sha256_file(audit / "accepted_text_index.jsonl") == provenance["accepted_index_sha256"],
        "Índice auditado alterado.",
    )
    inputs = [
        BASE,
        SPLIT,
        MATCH,
        MANIFEST,
        DICTIONARY,
        state,
        audit / "summary.json",
        audit / "provenance.json",
        audit / "accepted_text_index.jsonl",
    ]
    input_hashes = {str(p): sha256_file(p) for p in inputs}
    print("Montando coorte e grupos; sem letras, embeddings ou alvos do holdout.", flush=True)
    allowed = features()
    source = load_target_free_source(
        {
            "inputs": {
                "modeling_base": str(BASE),
                "split_assignments": str(SPLIT),
                "matching_audit": str(MATCH),
            }
        }
    )
    index = pl.read_ndjson(audit / "accepted_text_index.jsonl")
    require(
        index["query_id"].n_unique() == index.height == summary["accepted_queries"],
        "Índice inconsistente.",
    )
    with closing(connect(LOCAL, readonly=True)) as db:
        links = pl.DataFrame(
            [
                dict(r)
                for r in db.execute(
                    "SELECT t.track_id,t.query_id FROM tracks t JOIN queries q ON t.query_id=q.query_id "
                    "WHERE q.status IN ('accepted_exact_unique','accepted_exact_equivalent') ORDER BY t.track_id"
                )
            ]
        )
    links = links.join(
        index.select(
            "query_id",
            *HASHES,
            pl.col("split").alias("audit_split"),
            pl.col("composition_key").alias("audit_composition"),
        ),
        on="query_id",
        how="left",
        validate="m:1",
    )
    require(links.height == summary["accepted_tracks"], "Contagem de faixas diverge da auditoria.")
    accepted = source.join(links, on="track_id", how="inner", validate="1:1")
    require(accepted.height == links.height, "Faixas aceitas ausentes na fonte.")
    require(
        (accepted["split"] == accepted["audit_split"]).all(), "Split auditado diverge da fonte."
    )
    require(
        (accepted["composition_key"] == accepted["audit_composition"]).all(),
        "Composição da letra diverge do vínculo da faixa.",
    )
    for column in [*GROUPS, *HASHES]:
        require(
            accepted[column].null_count() == 0 and (accepted[column].cast(pl.String) != "").all(),
            f"Grupo/hash ausente: {column}.",
        )
        require(
            accepted.group_by(column)
            .agg(pl.col("split").n_unique().alias("n"))
            .filter(pl.col("n") > 1)
            .is_empty(),
            f"{column} cruza split.",
        )
    dev = accepted.filter(pl.col("split") == "development_train")
    # Componentes usam TODAS as versões aceitas antes do colapso de representantes.
    dev = dev.with_columns(pl.Series("analysis_group", components(dev, [*GROUPS, *HASHES])))
    reps, rep_audit = select_representatives_without_target(dev)
    raw = development_table(
        BASE, ["track_id", "split", TARGET, *allowed["baseline"], *allowed["lfm"]]
    )
    require(raw["track_id"].n_unique() == raw.height, "track_id duplicado na base.")
    cols = ["track_id", "spotify_row_id", "query_id", "split", *GROUPS, *HASHES, "analysis_group"]
    matrix = (
        reps.select(cols)
        .join(raw.drop("split"), on="track_id", how="left", validate="1:1")
        .sort("composition_key")
    )
    y = matrix[TARGET].to_numpy()
    require(
        np.isfinite(y).all() and ((y >= 0) & (y <= 100)).all(),
        "Alvo ausente/inválido; revisar, sem excluir silenciosamente.",
    )
    plan = partition_plan(matrix)
    output.mkdir(parents=True)
    matrix.write_parquet(output / "development.parquet")
    save_json(output / "folds.json", plan)
    metadata = accepted.select("track_id", "query_id", "split", *GROUPS, *HASHES).with_columns(
        pl.col("track_id").is_in(reps["track_id"].implode()).alias("development_representative")
    )
    metadata.write_parquet(output / "accepted_links.parquet")
    pl.read_csv(DICTIONARY, infer_schema_length=1000).filter(
        pl.col("nome").is_in([TARGET, *allowed["baseline"], *allowed["lfm"]])
    ).write_csv(output / "dictionary.csv")
    coverage = raw.with_columns(
        pl.col("track_id").is_in(dev["track_id"].implode()).alias("lyrics_accepted")
    )
    coverage.group_by("lyrics_accepted").agg(
        pl.len().alias("tracks"),
        pl.col(TARGET).mean().alias("mean_y"),
        pl.col(TARGET).median().alias("median_y"),
        pl.col("year").mean().alias("mean_year"),
    ).write_csv(output / "coverage.csv")
    coverage.group_by("genre", "lyrics_accepted").agg(pl.len().alias("tracks")).write_csv(
        output / "coverage_by_genre.csv"
    )
    descriptive(matrix, allowed, output / "description")
    require(
        all(sha256_file(p) == h for p, h in input_hashes.items()),
        "Entrada alterada durante a preparação.",
    )
    seal = {
        "created_at": utc_now(),
        "features": allowed,
        "inputs": input_hashes,
        "code": {str(p): sha256_file(p) for p in code_paths()},
        "artifacts": {
            name: sha256_file(output / name)
            for name in ("development.parquet", "folds.json", "accepted_links.parquet")
        },
        "seed": SEED,
        "representative_audit": rep_audit,
        "scope": "exploratory_development_only_new_accepted_cohort",
        "versions": versions(),
    }
    save_json(output / "seal.json", seal)
    result = {
        "stage": "prepared",
        "accepted_tracks_all_splits": accepted.height,
        "development_accepted_tracks": dev.height,
        "development_compositions": matrix.height,
        "holdout_accepted_tracks_metadata_only": accepted.height - dev.height,
        "analysis_components": matrix["analysis_group"].n_unique(),
        "collapsed_versions": dev.height - matrix.height,
        "holdout_targets_loaded": False,
        "inputs_unchanged": True,
        "workspace": str(output),
        "next": "10_modelar_baseline_tradicional.py --benchmark",
    }
    save_json(output / "summary.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


def versions():
    import platform

    import scipy
    import sklearn

    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "polars": pl.__version__,
        "scipy": scipy.__version__,
        "sklearn": sklearn.__version__,
    }


def check_seal(output):
    seal = read_json(output / "seal.json")
    require(seal["versions"] == versions(), "Versões do ambiente mudaram.")
    for kind in ("inputs", "code"):
        for path, expected in seal[kind].items():
            require(sha256_file(path) == expected, f"Arquivo mudou desde a preparação: {path}")
    for name, expected in seal["artifacts"].items():
        require(sha256_file(output / name) == expected, f"Artefato alterado: {name}")
    return seal


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--prepare", action="store_true", help="Prepara e descreve somente desenvolvimento."
    )
    action.add_argument("--status", action="store_true")
    parser.add_argument("--audit", type=Path, help="Pasta da auditoria 08; padrão: última pasta.")
    parser.add_argument("--workspace", type=Path, default=DEFAULT)
    args = parser.parse_args()
    try:
        out = workspace(args.workspace)
        if args.status:
            print(
                json.dumps(
                    read_json(out / "summary.json")
                    if (out / "summary.json").exists()
                    else {"stage": "not_prepared"},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            prepare(out, args.audit)
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print(f"Interrompido: {exc}", flush=True)
        return 1
