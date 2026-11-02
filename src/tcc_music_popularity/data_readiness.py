"""Pré-fechamento da coorte 200k: integridade, idioma e linhagem; execução manual."""

import argparse
import hashlib
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq

from . import sample_lyrics as base
from .lyrics_ambiguity_v011 import strict_plain_text_metrics
from .manual_lyrics import (
    atomic_frame,
    atomic_json,
    exclusive,
    fingerprint,
    meta_get,
    meta_put,
    require,
)
from .normalization import composition_key

WORKSPACE = base.ROOT / "data/derived/private_readiness_200k_v1"
OUTPUT = base.ROOT / "reports/prontidao_dados_200k_v1"
V2 = base.ROOT / "data/derived/private_sample_lyrics_200k_v2"
OLD = base.ROOT / "data/derived/private_final_development_v0_5"


def metadata_only(path, columns):
    require(
        not set(columns) & {"popularity", "spotify_popularity", "target", "y"},
        "Não carregar alvos históricos.",
    )
    return pl.read_parquet(path, columns=columns)


def lineage(accepted, assignments, evaluated, development):
    """Grupos abaixo são indicadores de colisão operacional; não são splits novos."""
    frame = accepted.with_columns(
        pl.struct("artist_name", "track_name")
        .map_elements(
            lambda row: composition_key(row["artist_name"], row["track_name"]),
            return_dtype=pl.String,
        )
        .alias("readiness_composition_key")
    )
    frame = frame.with_columns(
        pl.col("readiness_composition_key")
        .str.split_exact("|||", 1)
        .struct.field("field_0")
        .alias("readiness_artist_key")
    )
    require(
        assignments["track_id"].n_unique() == assignments.height,
        "Atribuições históricas com IDs repetidos.",
    )
    frame = frame.join(
        assignments.select("track_id", pl.col("split").alias("readiness_old_partition")),
        on="track_id",
        how="left",
        validate="m:1",
    )
    tested_artists = set(
        evaluated["composition_key"]
        .drop_nulls()
        .str.split_exact("|||", 1)
        .struct.field("field_0")
        .to_list()
    )
    return frame.with_columns(
        pl.col("track_id")
        .is_in(evaluated["track_id"].to_list())
        .alias("readiness_v06_evaluated_track"),
        pl.col("readiness_composition_key")
        .is_in(evaluated["composition_key"].drop_nulls().to_list())
        .fill_null(False)
        .alias("readiness_v06_composition_collision"),
        pl.col("readiness_artist_key")
        .is_in(sorted(tested_artists))
        .fill_null(False)
        .alias("readiness_v06_artist_collision"),
        pl.col("track_id")
        .is_in(development["track_id"].to_list())
        .alias("readiness_old_development_track"),
        pl.col("readiness_composition_key").is_null().alias("readiness_unknown_group"),
    )


def verify_texts(db, path, expected, *, limit=None):
    """Checkpoint por lote; lê textos em streaming, nunca carrega o corpus inteiro."""
    new, reused, last = 0, 0, 0.0
    seen = set()
    for batch in pq.ParquetFile(path).iter_batches(
        batch_size=512,
        columns=[
            "query_id",
            "accepted_text",
            "text_sha256",
            "strict_text_sha256",
            "lrclib_id",
            "lrclib_lyrics_id",
        ],
    ):
        verified = []
        for row in batch.to_pylist():
            key = row["query_id"]
            require(key not in seen, "Texto privado com query_id repetido.")
            seen.add(key)
            require(key in expected, "Letra privada sem referência na coorte aceita.")
            pair = (
                row["text_sha256"],
                row["strict_text_sha256"],
                row["lrclib_id"],
                row["lrclib_lyrics_id"],
            )
            require(pair == expected[key], "Referência/hash da decisão diverge do texto.")
            old = db.execute(
                "SELECT raw_hash,strict_hash FROM verified WHERE query_id=?", (key,)
            ).fetchone()
            if old:
                require(tuple(old) == pair[:2], "Checkpoint textual incompatível.")
                reused += 1
                continue
            if limit is not None and new >= limit:
                with db:
                    db.executemany("INSERT INTO verified VALUES (?,?,?)", verified)
                return False, new, reused
            text = row["accepted_text"]
            require(isinstance(text, str) and bool(text.strip()), "Texto aceito vazio/inválido.")
            require(
                hashlib.sha256(text.encode()).hexdigest() == pair[0]
                and strict_plain_text_metrics(text)["strict_text_sha256"] == pair[1],
                "Conteúdo textual não confere com hashes.",
            )
            verified.append((key, *pair[:2]))
            new += 1
        with db:
            db.executemany("INSERT INTO verified VALUES (?,?,?)", verified)
        if time.monotonic() - last >= 10:
            print(
                json.dumps({"stage": "checking_text_links", "new": new, "reused": reused}),
                flush=True,
            )
            last = time.monotonic()
    require(seen == set(expected), "Decisão aceita sem texto privado correspondente.")
    return True, new, reused


def run(
    *,
    sample_dir=base.SAMPLE_DIR,
    input_path=V2 / "resultados_faixas_200k.parquet",
    texts=V2 / "letras_aceitas_200k.parquet",
    assignments_path=base.ROOT / "data/processed/split_assignments_v0_1_1.parquet",
    evaluated_path=OLD / "holdout_features.parquet",
    development_path=OLD / "development_matrix.parquet",
    cohort_path=base.ROOT / "data/derived/private_statistical_cohort_v1/development.parquet",
    workspace=WORKSPACE,
    output=OUTPUT,
    expected=200000,
    limit=None,
):
    start = time.monotonic()
    require(
        workspace.resolve().is_relative_to(base.ROOT / "data/derived") or expected != 200000,
        "Workspace privado fora de data/derived.",
    )
    paths = [
        sample_dir / "amostra_spotify_200k.parquet",
        input_path,
        texts,
        assignments_path,
        evaluated_path,
        development_path,
        cohort_path,
    ]
    require(
        all(
            not path.resolve().is_relative_to(output.resolve())
            and not path.resolve().is_relative_to(workspace.resolve())
            for path in paths
        ),
        "Destinos sobrepõem fontes.",
    )
    require(
        output.resolve() != workspace.resolve()
        and not output.resolve().is_relative_to(workspace.resolve())
        and not workspace.resolve().is_relative_to(output.resolve()),
        "Destinos privado/público devem ser separados.",
    )
    print("[1/4] Validando amostra congelada e registrando fontes...", flush=True)
    sample, _ = base.validate_sample(
        paths[0],
        sample_dir / "resumo_amostra_200k.json",
        sample_dir / "alocacao_amostra_200k.csv",
        expected=expected,
    )
    frame = pl.read_parquet(input_path)
    require(
        frame.height == expected
        and frame["track_id"].n_unique() == expected
        and frame.select(sample.columns).sort("track_id").equals(sample.sort("track_id")),
        "Resultado não preserva a amostra.",
    )
    require(
        not frame["lyrics_status"].is_in(["pending", "technical_error"]).any(),
        "Resultado científico ainda incompleto.",
    )
    accepted = frame.filter(pl.col("lyrics_status") == "accepted")
    require(
        accepted.height > 0 and accepted["lyrics_text_ref"].null_count() == 0,
        "Coorte aceita sem referências válidas.",
    )
    expected_texts = {}
    for key, raw, strict, source_id, revision_id in accepted.select(
        "lyrics_text_ref",
        "lyrics_text_sha256",
        "lyrics_strict_text_sha256",
        "lyrics_selected_lrclib_id",
        "lyrics_selected_lyrics_id",
    ).iter_rows():
        require(
            key not in expected_texts
            or expected_texts[key] == (raw, strict, source_id, revision_id),
            "Referência reutilizada com hashes conflitantes.",
        )
        expected_texts[key] = (raw, strict, source_id, revision_id)
    seal = {
        "inputs": {str(p.resolve()): base.sha256(p) for p in paths},
        "code": base.sha256(Path(__file__)),
        "normalization": base.sha256(Path(__file__).with_name("normalization.py")),
        "strict_fingerprint": base.sha256(Path(__file__).with_name("lyrics_ambiguity_v011.py")),
    }
    owner = {"seal": fingerprint(seal)}
    if output.exists():
        require(
            (output / "owner.json").is_file()
            and json.loads((output / "owner.json").read_text()) == owner,
            "Saída existente incompatível.",
        )
    else:
        output.mkdir(parents=True)
        atomic_json(output / "owner.json", owner)
    with exclusive(workspace), closing(sqlite3.connect(workspace / "state.sqlite")) as db:
        db.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        db.execute(
            "CREATE TABLE IF NOT EXISTS verified(query_id TEXT PRIMARY KEY,raw_hash TEXT,strict_hash TEXT)"
        )
        if meta_get(db, "seal") is None:
            with db:
                meta_put(db, "seal", seal)
        require(meta_get(db, "seal") == seal, "Checkpoint pertence a outras entradas/regras.")
        print("[2/4] Conferindo hashes e vínculos de textos com checkpoint...", flush=True)
        complete, new, reused = verify_texts(db, texts, expected_texts, limit=limit)
        summary = {
            "completed": False,
            "sample_rows": sample.height,
            "accepted_rows": accepted.height,
            "new_text_checks": new,
            "reused_text_checks": reused,
            "inputs": seal,
            "old_targets_loaded": False,
            "models_loaded": False,
            "ssd_queries": 0,
            "training_executed": False,
        }
        if not complete:
            summary["stop_reason"] = "limit_resume_same_command"
            atomic_json(output / "resumo_prontidao.json", summary)
            return 2
        print("[3/4] Reconciliando metadados históricos e idiomas...", flush=True)
        assignments = metadata_only(assignments_path, ["track_id", "split"])
        evaluated = metadata_only(evaluated_path, ["track_id", "composition_key"])
        development = metadata_only(development_path, ["track_id"])
        cohort = metadata_only(cohort_path, ["track_id"])
        linked = lineage(accepted, assignments, evaluated, development).with_columns(
            pl.col("track_id")
            .is_in(cohort["track_id"].to_list())
            .alias("readiness_old_cohort_track")
        )
        summary["history_flags"] = {
            c: int(linked[c].sum())
            for c in linked.columns
            if c.startswith("readiness_") and linked[c].dtype == pl.Boolean
        }
        summary["old_lfm_overlap_tracks"] = int(
            linked["readiness_old_partition"].is_not_null().sum()
        )
        summary["unknown_old_lfm_tracks"] = accepted.height - summary["old_lfm_overlap_tracks"]
        language = linked.group_by("lyrics_detected_language", "lyrics_language_status").agg(
            pl.len().alias("tracks"), pl.col("sampling_weight").sum().alias("sampling_weight_total")
        )
        summary["language_counts"] = language.to_dicts()
        summary["strict_text_duplicates_tracks"] = (
            accepted.height - accepted["lyrics_strict_text_sha256"].n_unique()
        )
        summary["texts_linking_multiple_operational_artists"] = (
            linked.group_by("lyrics_strict_text_sha256")
            .agg(pl.col("readiness_artist_key").n_unique().alias("artists"))
            .filter(pl.col("artists") > 1)
            .height
        )
        summary.update(
            completed=True,
            seconds=time.monotonic() - start,
            cohort_frozen=False,
            next="Revisar integridade/linhagem e congelar contrato de descritores/encoder/splits; não iniciar treino automaticamente.",
        )
        atomic_frame(workspace / "linhagem_aceitas.parquet", linked)
        atomic_json(output / "resumo_prontidao.json", summary)
        report = [
            "# Pré-fechamento da base recente",
            f"Amostra preservada: {sample.height}; aceitas: {accepted.height}; consultas textuais privadas verificadas: {len(expected_texts)}.",
            "Domínio analítico observado aprovado, sem representatividade presumida. Esta auditoria não congela coorte, gera preditores ou define splits.",
            base.markdown_table(
                language.to_dicts(),
                [
                    "lyrics_detected_language",
                    "lyrics_language_status",
                    "tracks",
                    "sampling_weight_total",
                ],
            ),
            base.markdown_table(
                [{"flag": k, "tracks": v} for k, v in summary["history_flags"].items()],
                ["flag", "tracks"],
            ),
            f"Interseção por ID com integração LFM antiga: {summary['old_lfm_overlap_tracks']}; sem vínculo antigo: {summary['unknown_old_lfm_tracks']}. Interseção não prova mesma versão/texto nem autoriza copiar descritores.",
            "Colisões de artista/composição são operacionais e servem para investigar exposição/leakage. Não reconstituem identidades universais e não substituem reconciliação de grupos. Partição histórica não equivale a confirmação de alvo avaliado; a flag v06 identifica especificamente o teste aberto. Nenhum alvo histórico ou modelo foi carregado.",
            "Hashes verificam integridade, não qualidade semântica do matching. Idioma é estimado, não rótulo humano. Nenhum filtro por idioma, instrumentalness ou popularidade. Todos os 200 mil registros permanecem no arquivo de origem, com pesos.",
            "Pendente: revisão de pares já disponíveis; política multilingue; descritores sobre o mesmo texto do embedding; identidade/grupos com hashes e histórico; contrato comum das quatro configurações. Não importar LFM2b ou vetores antigos apenas por track_id.",
        ]
        (output / "relatorio_prontidao.md").write_text("\n\n".join(report) + "\n", encoding="utf-8")
        print(f"[4/4] Auditoria concluída; agregados em {output}", flush=True)
        return 0


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit-texts", type=int)
    args = parser.parse_args()
    require(args.limit_texts is None or args.limit_texts > 0, "Limite deve ser positivo.")
    return run(limit=args.limit_texts)
