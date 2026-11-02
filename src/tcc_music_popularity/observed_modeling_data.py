"""Base comum e CV agrupada 5x3 do domínio observado; sem ajuste de modelos."""

import argparse
import hashlib
import json
import platform
import sqlite3
import time
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from . import multilingual_embeddings as embeddings
from . import text_descriptors as descriptors
from .lyrics_recovery import write_csv
from .manual_lyrics import atomic_frame, atomic_json, exclusive, fingerprint, require

ROOT = descriptors.ROOT
WORKSPACE = ROOT / "data/derived/private_modeling_200k_v1"
OUTPUT = ROOT / "reports/base_modelagem_200k_v1"
PROTOCOL = ROOT / "docs/protocolo_base_modelagem_200k_v1.md"
SEED = 20261101
TARGET = "spotify_popularity"
NUMERIC = (
    "year",
    "danceability",
    "energy",
    "loudness",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "duration_ms",
)
CATEGORICAL = ("genre", "key", "mode", "time_signature")
BASELINE = tuple("model_" + c for c in NUMERIC + CATEGORICAL)
UNIT_INTERVAL = {
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
}
INDEX_COLUMNS = (
    "track_id",
    "lyrics_text_ref",
    "text_input_sha256",
    "text_component_id",
    "text_characters",
    "lyrics_detected_language",
    "lyrics_language_status",
)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_metadata(frame):
    """Originais preservados; inválidos de X viram nulos novos, sem imputação."""
    require(not ({TARGET} | set(BASELINE)) & set(frame.columns), "Colunas derivadas já existem.")
    require(
        set(NUMERIC + CATEGORICAL + ("popularity",)) <= set(frame.columns),
        "Metadados de origem incompletos.",
    )
    target = frame["popularity"].cast(pl.String).str.strip_chars().cast(pl.Float64, strict=False)
    valid_target = (
        target.is_not_null()
        & target.is_finite()
        & target.is_between(0, 100)
        & (target == target.floor())
    ).fill_null(False)
    require(
        valid_target.all(),
        f"Popularidade inválida em {len(frame) - valid_target.sum()} linhas; fontes preservadas, sem exclusão.",
    )
    result = frame.with_columns(target.alias(TARGET))
    quality, invalid = [], []
    for name in NUMERIC + CATEGORICAL:
        raw = frame[name].cast(pl.String).str.strip_chars()
        present = (raw.is_not_null() & (raw != "")).fill_null(False)
        if name == "genre":
            valid = present
            value = raw
        else:
            value = raw.cast(pl.Float64, strict=False)
            valid = (present & value.is_not_null() & value.is_finite()).fill_null(False)
            if name in UNIT_INTERVAL:
                valid &= value.is_between(0, 1).fill_null(False)
            elif name == "year":
                valid &= (value.is_between(1000, 9999) & (value == value.floor())).fill_null(False)
            elif name in {"key", "mode", "time_signature"}:
                low, high = {"key": (-1, 11), "mode": (0, 1), "time_signature": (0, 7)}[name]
                valid &= (value.is_between(low, high) & (value == value.floor())).fill_null(False)
            elif name == "tempo":
                valid &= (value >= 0).fill_null(False)
            elif name == "duration_ms":
                valid &= (value > 0).fill_null(False)
        clean = pl.when(valid).then(value).otherwise(None)
        if name in CATEGORICAL and name != "genre":
            clean = clean.cast(pl.Int64).cast(pl.String)
        result = result.with_columns(clean.alias("model_" + name))
        bad = present & ~valid
        quality.append(
            {
                "source": name,
                "derived": "model_" + name,
                "kind": "categorical" if name in CATEGORICAL else "numeric",
                "source_missing": int((~present).sum()),
                "invalid_nonmissing": int(bad.sum()),
                "model_missing": result["model_" + name].null_count(),
            }
        )
        if bad.any():
            invalid.append(
                frame.filter(bad).select(
                    "track_id",
                    pl.lit(name).alias("source_column"),
                    pl.lit("invalid_by_frozen_rule").alias("reason"),
                )
            )
    issues = (
        pl.concat(invalid)
        if invalid
        else pl.DataFrame(
            schema={"track_id": pl.String, "source_column": pl.String, "reason": pl.String}
        )
    )
    require(result.select(frame.columns).equals(frame), "Campos originais alterados.")
    return result, quality, issues


def audit_components(frame):
    require(not frame["text_group_unresolved"].any(), "Grupos não resolvidos; não excluir faixas.")
    units = (
        "text_artist_group_key",
        "text_composition_group_key",
        "lyrics_strict_text_sha256",
        "text_input_sha256",
    )
    for name in units:
        require(frame[name].null_count() == 0, f"Identidade operacional nula: {name}.")
        counts = frame.group_by(name).agg(pl.col("text_component_id").n_unique().alias("n"))
        require(counts["n"].max() == 1, f"Identidade cruza componentes: {name}.")
    # Reusa as regras congeladas, incluindo feat. explícito e fallback literal.
    check = descriptors.grouping(frame).sort("track_id")
    require(
        frame.select(check.columns).sort("track_id").equals(check),
        "Componentes divergem das regras de identidade do script 19.",
    )


def balanced_assignment(sizes, n_folds, seed):
    """Greedy por tamanho; desempate por SHA-256 com seed, independente do alvo."""
    require(len(sizes) >= n_folds, "Componentes insuficientes para os folds.")
    require(all(n > 0 for n in sizes.values()), "Tamanho de componente inválido.")

    def tie(value):
        return hashlib.sha256(f"{seed}\0{value}".encode()).hexdigest()

    loads, counts, assigned = [0] * n_folds, [0] * n_folds, {}
    for group in sorted(sizes, key=lambda g: (-sizes[g], tie(g), g)):
        fold = min(range(n_folds), key=lambda f: (loads[f], counts[f], tie(f)))
        assigned[group] = fold
        loads[fold] += sizes[group]
        counts[fold] += 1
    return assigned


def make_folds(frame, seed=SEED):
    sizes = dict(frame.group_by("text_component_id").len().iter_rows())
    outer = balanced_assignment(sizes, 5, seed)
    groups = frame["text_component_id"].to_list()
    result = frame.select("track_id", "text_component_id").with_columns(
        pl.Series("outer_fold", [outer[g] for g in groups], dtype=pl.Int8)
    )
    for o in range(5):
        inner = balanced_assignment(
            {g: n for g, n in sizes.items() if outer[g] != o}, 3, seed + 1000 + o
        )
        result = result.with_columns(
            pl.Series(f"inner_outer_{o}", [inner.get(g, -1) for g in groups], dtype=pl.Int8)
        )
    audit_folds(result)
    return result


def audit_folds(folds):
    require(folds["track_id"].n_unique() == folds.height, "IDs repetidos nos folds.")
    require(folds["text_component_id"].null_count() == 0, "Componente nulo nos folds.")
    require(set(folds["outer_fold"].to_list()) == set(range(5)), "Folds externos incompletos.")
    for column in ("outer_fold", *[f"inner_outer_{o}" for o in range(5)]):
        require(folds[column].null_count() == 0, "Fold nulo.")
        require(
            folds.group_by("text_component_id").agg(pl.col(column).n_unique().alias("n"))["n"].max()
            == 1,
            "Um componente cruza partições de avaliação.",
        )
    for o in range(5):
        column = f"inner_outer_{o}"
        require(
            ((folds[column] == -1) == (folds["outer_fold"] == o)).all(),
            "Teste externo entrou na CV interna.",
        )
        require(
            set(folds.filter(pl.col("outer_fold") != o)[column].to_list()) == {0, 1, 2},
            "Folds internos incompletos.",
        )


def fold_counts(frame, folds):
    joined = frame.select(
        "track_id",
        *[
            c
            for c in frame.columns
            if c.startswith("readiness_v06_") and frame[c].dtype == pl.Boolean
        ],
    ).join(folds, on="track_id", validate="1:1")
    result = []
    for outer in range(5):
        external = pl.col("outer_fold") == outer
        for inner in (None, 0, 1, 2):
            valid = (
                external
                if inner is None
                else (~external & (pl.col(f"inner_outer_{outer}") == inner))
            )
            train = ~external if inner is None else (~external & ~valid)
            record = {
                "outer_fold": outer,
                "inner_fold": inner,
                "stage": "outer" if inner is None else "inner",
            }
            for role, mask in (("train", train), ("valid", valid)):
                selected = joined.filter(mask)
                record[role + "_rows"] = selected.height
                record[role + "_components"] = selected["text_component_id"].n_unique()
                for c in joined.columns:
                    if c.startswith("readiness_v06_"):
                        record[role + "_" + c] = int(selected[c].sum())
            result.append(record)
    return result


def audit_vectors(path, expected_hashes, checkpoint_hashes):
    """Lê vetores em lotes; não carrega letras ou encoder, não gera novos vetores."""
    pf = pq.ParquetFile(path)
    field = pf.schema_arrow.field("embedding").type
    require(
        pa.types.is_fixed_size_list(field)
        and field.list_size == 384
        and field.value_type == pa.float32(),
        "Schema vetorial incompatível.",
    )
    seen, max_error = set(), 0.0
    for batch in pf.iter_batches(
        batch_size=256, columns=["text_input_sha256", "embedding", "vector_sha256"]
    ):
        for row in batch.to_pylist():
            key = row["text_input_sha256"]
            require(key in expected_hashes and key not in seen, "Vetor extra/repetido.")
            vector = np.asarray(row["embedding"], dtype=np.float32)
            require(vector.shape == (384,) and np.isfinite(vector).all(), "Vetor inválido.")
            error = abs(float(np.linalg.norm(vector)) - 1.0)
            require(error <= 1e-5, "Norma L2 incompatível.")
            digest = hashlib.sha256(vector.tobytes()).hexdigest()
            require(
                digest == row["vector_sha256"] == checkpoint_hashes.get(key),
                "Hash vetorial diverge do checkpoint.",
            )
            seen.add(key)
            max_error = max(max_error, error)
    require(seen == expected_hashes == set(checkpoint_hashes), "Vetores ausentes/extras.")
    return {"vectors": len(seen), "dimension": 384, "max_l2_error": max_error}


def blocks_manifest():
    traditional = list(descriptors.FEATURES)
    return {
        "target": TARGET,
        "unit": "track_id",
        "group": "text_component_id",
        "baseline_numeric": ["model_" + c for c in NUMERIC],
        "baseline_categorical": ["model_" + c for c in CATEGORICAL],
        "blocks": {
            "baseline": {"columns": list(BASELINE), "embedding": False},
            "traditional": {"columns": [*BASELINE, *traditional], "embedding": False},
            "deep": {"columns": list(BASELINE), "embedding": True},
            "combined": {"columns": [*BASELINE, *traditional], "embedding": True},
        },
        "embedding_key": "text_input_sha256",
        "embedding_dimension": 384,
        "learned_preprocessing": "only_inside_each_training_fold",
        "weighting": {
            "training": "equal_track_weights",
            "selection": "unweighted_MAE",
            "primary_evaluation": "pooled_outer_OOF_unweighted_MAE",
            "complementary_evaluation": ["unweighted_RMSE", "unweighted_R2"],
            "sensitivity_evaluation": "MAE_with_original_sampling_weight_same_OOF_predictions",
            "sensitivity_weight_column": "sampling_weight",
            "not_a_lyrics_selection_correction": True,
            "applied_in_data_preparation": False,
        },
        "historical_test_exposure": "v0.6 opened 2026-10-14; no new independent holdout",
    }


def run(
    *,
    cohort_path=descriptors.WORKSPACE / "coorte_descritores.parquet",
    descriptor_report=descriptors.OUTPUT / "resumo_descritores.json",
    embedding_workspace=embeddings.WORKSPACE,
    embedding_report=embeddings.OUTPUT / "integral/resumo_embeddings.json",
    workspace=WORKSPACE,
    output=OUTPUT,
    expected=77535,
):
    started = time.monotonic()
    workspace, output = workspace.resolve(), output.resolve()
    require(
        workspace.is_relative_to(ROOT / "data/derived") or expected != 77535,
        "Workspace precisa ser privado.",
    )
    sources = [
        cohort_path,
        descriptor_report,
        embedding_report,
        embedding_workspace / "embeddings.parquet",
        embedding_workspace / "indice_embeddings.parquet",
    ]
    require(
        not workspace.is_relative_to(output) and not output.is_relative_to(workspace),
        "Separar diretórios privados e públicos.",
    )
    require(
        all(
            not p.resolve().is_relative_to(workspace) and not p.resolve().is_relative_to(output)
            for p in sources
        ),
        "Saídas sobrepõem fontes.",
    )
    print("[1/5] Conferindo fontes concluídas e selos; sem letras ou encoder...", flush=True)
    previous, report = read_json(descriptor_report), read_json(embedding_report)
    require(
        previous["completed"]
        and previous["cohort_rows"] == expected
        and report["completed"]
        and report["mode"] == "all"
        and report["unencoded_unique_texts"] == 0
        and report["private_index_rows"] == expected
        and report["source_rows"] == expected
        and report["dimension"] == 384
        and report["max_input_tokens"] <= 512
        and report["new_vectors"] + report["reused_vectors"] == previous["unique_input_texts"]
        and previous["features"] == list(descriptors.FEATURES)
        and report["requested_unique_texts"] == previous["unique_input_texts"],
        "Descritores/embeddings incompletos ou incompatíveis.",
    )
    with sqlite3.connect(
        (embedding_workspace / "state.sqlite").resolve().as_uri() + "?mode=ro", uri=True, timeout=2
    ) as db:
        meta = dict(db.execute("SELECT key,value FROM meta WHERE key IN ('seal','smoke_verified')"))
        source_seal = json.loads(meta["seal"])
        require(
            json.loads(meta["smoke_verified"])
            and fingerprint(source_seal) == report["seal_sha256"]
            and source_seal["settings"] == report["settings"] == embeddings.SETTINGS,
            "Selo do encoder divergiu.",
        )
        records = list(db.execute("SELECT lyrics_sha256,vector_sha256,config_sha256 FROM vectors"))
    require(
        len(records) == previous["unique_input_texts"]
        and all(r[2] == report["seal_sha256"] for r in records),
        "Checkpoint incompleto.",
    )
    checkpoint_hashes = {r[0]: r[1] for r in records}
    for name, digest in source_seal["code"].items():
        location = ROOT / ("src/tcc_music_popularity" if name.endswith(".py") else "docs") / name
        require(embeddings.base.sha256(location) == digest, "Código/protocolo do encoder mudou.")
    require(
        embeddings.base.sha256(Path(descriptors.__file__)) == previous["seal"]["code"]
        and embeddings.base.sha256(descriptors.PROTOCOL) == previous["seal"]["protocol"],
        "Regras dos descritores/grupos mudaram.",
    )
    hashes = {str(p.resolve()): embeddings.base.sha256(p) for p in sources}
    require(
        hashes[str(cohort_path.resolve())] == source_seal["source_sha256"]
        and hashes[str(descriptor_report.resolve())] == source_seal["descriptor_report"],
        "Fontes mudaram após geração dos embeddings.",
    )
    seal = {
        "version": "observed-modeling-data-v1",
        "inputs": hashes,
        "embedding_seal": report["seal_sha256"],
        "seed": SEED,
        "outer_folds": 5,
        "inner_folds": 3,
        "code": embeddings.base.sha256(Path(__file__)),
        "protocol": embeddings.base.sha256(PROTOCOL),
        "support_code": {
            name: embeddings.base.sha256(Path(__file__).with_name(name))
            for name in ("manual_lyrics.py", "normalization.py", "lyrics_recovery.py")
        },
        "runtime": {
            "python": platform.python_version(),
            "polars": pl.__version__,
            "numpy": np.__version__,
            "pyarrow": pa.__version__,
        },
    }
    owner = {"seal": fingerprint(seal)}
    with exclusive(workspace):
        for destination in (workspace, output):
            if (destination / "owner.json").exists():
                require(
                    read_json(destination / "owner.json") == owner,
                    "Saída incompatível; preservada.",
                )
            else:
                require(
                    not any(p.name != "execution.lock" for p in destination.iterdir())
                    if destination.exists()
                    else True,
                    "Diretório sem proprietário; preservado.",
                )
                destination.mkdir(parents=True, exist_ok=True)
                atomic_json(destination / "owner.json", owner)
        summary = {
            "completed": False,
            "seal": seal,
            "models_trained": False,
            "encoder_loaded": False,
            "embeddings_generated": False,
            "splits_created": False,
        }
        atomic_json(output / "resumo_base_modelagem.json", summary)
        try:
            frame = pl.read_parquet(cohort_path)
            require(
                frame.height == frame["track_id"].n_unique() == expected
                and frame["track_id"].null_count() == 0
                and (frame["lyrics_status"] == "accepted").all(),
                "Coorte inválida.",
            )
            for c in ("sampling_weight", "inclusion_probability"):
                require(
                    frame[c].null_count() == 0
                    and frame[c].is_finite().all()
                    and (frame[c] > 0).all(),
                    "Pesos/probabilidades inválidos.",
                )
            require(
                (frame["inclusion_probability"] <= 1).all()
                and (
                    (frame["sampling_weight"] * frame["inclusion_probability"] - 1).abs() <= 1e-8
                ).all(),
                "Pesos não correspondem às probabilidades originais.",
            )
            require(
                not frame.select(
                    pl.any_horizontal(
                        [pl.col(c).is_null() | ~pl.col(c).is_finite() for c in descriptors.FEATURES]
                    ).any()
                ).item(),
                "Descritores ausentes/não finitos.",
            )
            index = pl.read_parquet(embedding_workspace / "indice_embeddings.parquet")
            require(
                set(index.columns) == set(INDEX_COLUMNS)
                and index.height == index["track_id"].n_unique() == expected
                and frame.select(index.columns).sort("track_id").equals(index.sort("track_id")),
                "Índice de embeddings não corresponde exatamente à coorte.",
            )
            print("[2/5] Auditando vetores existentes em lotes; sem recalcular...", flush=True)
            vector_audit = audit_vectors(
                embedding_workspace / "embeddings.parquet",
                set(frame["text_input_sha256"].to_list()),
                checkpoint_hashes,
            )
            print("[3/5] Preparando colunas novas e auditando componentes...", flush=True)
            assembled, quality, issues = prepare_metadata(frame)
            audit_components(assembled)
            atomic_frame(workspace / "metadados_invalidos.parquet", issues)
            print(
                "[4/5] Criando e auditando folds agrupados comuns 5x3, sem usar o alvo...",
                flush=True,
            )
            folds = make_folds(assembled)
            counts = fold_counts(assembled, folds)
            blocks = blocks_manifest()
            blocks.update(
                cohort=str(workspace / "coorte_modelagem.parquet"),
                folds=str(workspace / "folds_5x3.parquet"),
                embeddings=str((embedding_workspace / "embeddings.parquet").resolve()),
                inputs_seal=owner["seal"],
            )
            # Confirmar imutabilidade antes de publicar a conclusão.
            require(
                all(embeddings.base.sha256(p) == hashes[str(p.resolve())] for p in sources),
                "Uma fonte foi alterada durante a montagem.",
            )
            atomic_frame(workspace / "coorte_modelagem.parquet", assembled)
            atomic_frame(workspace / "folds_5x3.parquet", folds)
            atomic_json(workspace / "blocos.json", blocks)
            write_csv(output / "folds_agregados.csv", counts)
            write_csv(output / "qualidade_metadados.csv", quality)
            sizes = assembled.group_by("text_component_id").len()
            summary.update(
                completed=True,
                cohort_rows=expected,
                original_rows_preserved=True,
                unique_input_texts=vector_audit["vectors"],
                vectors=vector_audit,
                components=sizes.height,
                largest_component=int(sizes["len"].max()),
                baseline_features=len(BASELINE),
                traditional_features=len(descriptors.FEATURES),
                predictor_invalid_cells=issues.height,
                outer_folds=5,
                inner_folds=3,
                splits_created=True,
                leakage_checks_passed=True,
                original_weights_preserved=True,
                weights_applied=False,
                outputs_sha256={
                    p.name: embeddings.base.sha256(p)
                    for p in (
                        workspace / "coorte_modelagem.parquet",
                        workspace / "folds_5x3.parquet",
                        workspace / "blocos.json",
                        workspace / "metadados_invalidos.parquet",
                    )
                },
                seconds=time.monotonic() - started,
            )
            (output / "relatorio_base_modelagem.md").write_text(
                "# Base comum e folds agrupados\n\n"
                + f"{expected} faixas preservadas; {vector_audit['vectors']} vetores de 384 dimensões; "
                + f"{sizes.height} componentes, maior {sizes['len'].max()}. "
                + "CV agrupada 5x3 comum aos quatro blocos, sem usar popularidade na atribuição.\n\n"
                + "15 campos de metadados/acústicas, 21 descritores tradicionais e 384 dimensões profundas. "
                + "Nenhuma imputação, escala, PCA, seleção de variável ou modelo ajustados. "
                + "Inválidos de preditores ficam nulos em colunas novas, com originais e registro privado.\n\n"
                + "Domínio observado, sem representatividade presumida do catálogo. Teste v0.6 já exposto; "
                + "nova CV não restaura confirmação independente. Identidades são operacionais. "
                + "Matching semântico e qualidade preditiva não certificados pela integridade técnica. "
                + "Pesos preservados e não aplicados nesta preparação.\n",
                encoding="utf-8",
            )
            atomic_json(output / "resumo_base_modelagem.json", summary)
            print(f"[5/5] Concluído; sem treino; agregados em {output}", flush=True)
            return 0
        except BaseException as exc:
            summary.update(
                completed=False,
                error_type=type(exc).__name__,
                error=str(exc),
                seconds=time.monotonic() - started,
            )
            atomic_json(output / "resumo_base_modelagem.json", summary)
            raise


def cli():
    argparse.ArgumentParser(description=__doc__).parse_args()
    return run()
