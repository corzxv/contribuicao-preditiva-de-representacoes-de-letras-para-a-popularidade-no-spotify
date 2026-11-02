"""Embeddings manuais com checkpoints; sem PCA, fine-tuning ou preditores."""

from __future__ import annotations

import hashlib
import json
import os
from contextlib import closing
from pathlib import Path

import numpy as np
import polars as pl

from .config import load_yaml
from .io import sha256_file
from .lyrics_ambiguity_v011 import deduplicate_candidates, strict_plain_text_metrics
from .lyrics_embeddings_v020 import (
    _encode_unique_records,
    _load_model,
    _set_determinism,
    _tokenize_audit_records,
    build_embedding_frame,
    normalize_lyrics_text,
    sha256_text,
)
from .lyrics_pilot_v012 import ACCEPTED_STATUSES
from .manual_lyrics import (
    CONFIG,
    ROOT,
    atomic_frame,
    atomic_json,
    check_prepared,
    connect,
    exclusive,
    fingerprint,
    meta_get,
    meta_put,
    progress,
    require,
)

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def encoder_config(config, batch_size):
    cfg = {"model": dict(config["model"]), "execution": dict(config["embedding_execution"])}
    require(
        cfg["model"]["id"] == MODEL_ID and cfg["model"]["revision"] == REVISION,
        "Encoder/revision não correspondem ao congelado.",
    )
    require(
        cfg["model"]["embedding_dimension"] == 384
        and cfg["model"]["maximum_tokens_including_special"] == 256,
        "Dimensão/limite de tokens divergentes.",
    )
    require(
        cfg["execution"]["overlap_content_tokens"] == 32 and cfg["execution"]["dtype"] == "float32",
        "Configuração de trechos/dtype divergente.",
    )
    require(
        cfg["execution"]["device"] == "cpu", "Esta entrada conserva o dispositivo CPU congelado."
    )
    cfg["execution"]["batch_size"] = batch_size
    return cfg


def encoding_signature(cfg):
    # Batch size é operacional; não muda texto, revisão, trechos, pesos ou normalização.
    return fingerprint(
        {
            "model": {
                k: cfg["model"][k]
                for k in (
                    "id",
                    "revision",
                    "embedding_dimension",
                    "maximum_tokens_including_special",
                )
            },
            "execution": {
                k: cfg["execution"][k]
                for k in (
                    "dtype",
                    "device",
                    "overlap_content_tokens",
                    "language_confidence_threshold",
                    "very_short_token_threshold",
                )
            },
            "pipeline_sha256": sha256_file(
                ROOT / "src/tcc_music_popularity/lyrics_embeddings_v020.py"
            ),
            "aggregation": "new_token_weighted_mean_l2_chunks_and_final_v020",
        }
    )


def checked_vector(value, dimension=384, tolerance=1e-5):
    vector = np.asarray(value, dtype=np.float32)
    require(vector.shape == (dimension,), "Dimensão inválida do embedding.")
    require(np.isfinite(vector).all(), "Embedding contém NaN/infinito.")
    require(abs(float(np.linalg.norm(vector)) - 1.0) <= tolerance, "Norma L2 incompatível.")
    return vector


def save_vector(db, digest, vector, cfg_sha, metadata, origin):
    vector = checked_vector(vector)
    existing = db.execute("SELECT * FROM vectors WHERE lyrics_sha256=?", (digest,)).fetchone()
    if existing:
        old = read_vector(existing, cfg_sha)
        require(
            np.allclose(old, vector, atol=1e-5, rtol=0),
            "Vetores históricos conflitantes; revisar sem escolher arbitrariamente.",
        )
        return
    payload = vector.tobytes()
    db.execute(
        "INSERT INTO vectors VALUES (?,?,?,?,?,?)",
        (
            digest,
            cfg_sha,
            payload,
            hashlib.sha256(payload).hexdigest(),
            json.dumps(metadata),
            origin,
        ),
    )


def read_vector(row, cfg_sha):
    require(row["config_sha256"] == cfg_sha, "Checkpoint de encoder/configuração diferente.")
    payload = row["vector"]
    require(
        hashlib.sha256(payload).hexdigest() == row["vector_sha256"],
        "Checkpoint de vetor corrompido.",
    )
    return checked_vector(np.frombuffer(payload, dtype=np.float32))


def read_accepted_text(stored):
    """Texto só vem do candidato aprovado da consulta exata, nunca de outra versão."""
    require(stored["status"] in ACCEPTED_STATUSES, "Consulta não aceita.")
    path = Path(stored["cache_path"])
    require(
        path.is_file() and sha256_file(path) == stored["cache_sha256"],
        "Cache aceito ausente/alterado; revisar antes de codificar.",
    )
    envelope = json.loads(path.read_text(encoding="utf-8"))
    result = json.loads(stored["result"])
    selected = [
        c
        for c in deduplicate_candidates(envelope)["unified"]
        if c["candidate_key_sha256"] == result["selected_candidate_key_sha256"]
    ]
    require(len(selected) == 1, "Candidato selecionado não localizado de forma única.")
    candidate = selected[0]["candidate"]
    text = candidate.get("plainLyrics")
    require(
        candidate.get("id") == result["selected_lrclib_id"]
        and isinstance(text, str)
        and bool(text.strip()),
        "Identidade/texto do candidato inválidos.",
    )
    strict = strict_plain_text_metrics(text)["strict_text_sha256"]
    require(strict == result["selected_strict_text_sha256"], "Hash estrito da letra divergiu.")
    normalized = normalize_lyrics_text(text)
    require(bool(normalized), "Letra normalizada vazia.")
    query = json.loads(stored["data"])
    return {
        "composition_key": query["composition_key"],
        "track_id": query["representative_track_id"],
        "split": query["split"],
        "query_id": stored["query_id"],
        "source_strict_sha256": strict,
        "lyrics_sha256": sha256_text(normalized),
        "private_lyrics": normalized,
    }


def compatible_legacy_manifest(manifest, cfg, kind):
    if kind == "v02":
        model, params = manifest.get("model", {}), manifest.get("parameters", {})
        return (
            all(
                model.get(k) == cfg["model"][k]
                for k in (
                    "id",
                    "revision",
                    "embedding_dimension",
                    "maximum_tokens_including_special",
                )
            )
            and params.get("overlap_content_tokens") == cfg["execution"]["overlap_content_tokens"]
            and params.get("language_confidence_threshold")
            == cfg["execution"]["language_confidence_threshold"]
            and params.get("chunk_embedding_l2_normalized") is True
            and params.get("final_embedding_l2_normalized") is True
            and manifest.get("environment", {}).get("dtype") == "float32"
        )
    embedding = manifest.get("embeddings") or {}
    return (
        manifest.get("status") == "complete"
        and embedding.get("model_id") == MODEL_ID
        and embedding.get("model_revision") == REVISION
        and embedding.get("dimension") == 384
        and embedding.get("dtype") == "float32"
        and embedding.get("validation", {}).get("all_tokens_covered_without_truncation") is True
    )


def import_legacy_vectors(db, cfg):
    """Somente fontes conhecidas com manifesto e configuração verificáveis."""
    if meta_get(db, "legacy_vectors_imported"):
        return
    cfg_sha = encoding_signature(cfg)
    sources = [
        (
            "data/derived/private_embeddings/lyrics_embeddings_minilm_v0_2.parquet",
            "reports/lyrics_embedding_manifest_v0_2.json",
            "configs/lyrics_embeddings_v0_2.yaml",
            "v02",
        ),
        (
            "data/derived/private_final_study/final_embeddings_development_v0_4.parquet",
            "reports/run_summary_scale_v0_4.json",
            "configs/final_scale_v0_4.yaml",
            "v04",
        ),
        (
            "data/derived/private_final_study/final_embeddings_holdout_v0_4.parquet",
            "reports/run_summary_scale_v0_4.json",
            "configs/final_scale_v0_4.yaml",
            "v04",
        ),
    ]
    audit = []
    metadata_columns = [
        "token_count",
        "chunk_count",
        "detected_language",
        "language_status",
        "language_confidence",
    ]
    with db:
        for vector_name, manifest_name, config_name, kind in sources:
            vector_path, manifest_path = ROOT / vector_name, ROOT / manifest_name
            if not vector_path.is_file() or not manifest_path.is_file():
                audit.append({"source": vector_name, "status": "missing_not_reused"})
                continue
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            legacy = load_yaml(ROOT / config_name)
            legacy_cfg = {
                "model": legacy["model"],
                "execution": legacy["execution" if kind == "v02" else "embedding_execution"],
            }
            if encoding_signature(legacy_cfg) != cfg_sha or not compatible_legacy_manifest(
                manifest, cfg, kind
            ):
                audit.append(
                    {"source": vector_name, "status": "configuration_unconfirmed_not_reused"}
                )
                continue
            if kind == "v04":
                integrity_path = ROOT / legacy["private_outputs"]["integrity_manifest"]
                require(integrity_path.is_file(), "Manifesto de integridade V0.4 ausente.")
                integrity = json.loads(integrity_path.read_text(encoding="utf-8"))
                key = "embeddings_holdout" if "holdout" in vector_name else "embeddings_development"
                require(
                    integrity["private_artifact_hashes"][key] == sha256_file(vector_path),
                    "Embedding histórico V0.4 alterado.",
                )
            columns = [
                "lyrics_sha256",
                "embedding",
                "model_id",
                "model_revision",
                "protocol_version",
                *metadata_columns,
            ]
            frame = pl.scan_parquet(vector_path).select(columns).collect()
            imported = 0
            for row in frame.iter_rows(named=True):
                if (
                    row["model_id"] != MODEL_ID
                    or row["model_revision"] != REVISION
                    or row["protocol_version"] != "v0.2"
                ):
                    continue
                save_vector(
                    db,
                    row["lyrics_sha256"],
                    row["embedding"],
                    cfg_sha,
                    {c: row[c] for c in metadata_columns},
                    vector_name,
                )
                imported += 1
            audit.append(
                {
                    "source": vector_name,
                    "status": "validated",
                    "rows": imported,
                    "file_sha256": sha256_file(vector_path),
                    "manifest_sha256": sha256_file(manifest_path),
                }
            )
        meta_put(db, "legacy_vector_audit", audit)
        meta_put(db, "legacy_vectors_imported", True)


def export_embeddings(db, workspace, cfg_sha):
    vectors, index = [], []
    selected = db.execute(
        "SELECT v.* FROM vectors v WHERE EXISTS (SELECT 1 FROM embedding_links l WHERE l.lyrics_sha256=v.lyrics_sha256) ORDER BY lyrics_sha256"
    ).fetchall()
    positions = {}
    for position, row in enumerate(selected):
        positions[row["lyrics_sha256"]] = position
        vectors.append(
            {
                "vector_index": position,
                "lyrics_sha256": row["lyrics_sha256"],
                "embedding": read_vector(row, cfg_sha).tolist(),
                "model_id": MODEL_ID,
                "model_revision": REVISION,
                "configuration_sha256": cfg_sha,
            }
        )
    for row in db.execute(
        "SELECT t.data,t.query_id,l.lyrics_sha256,l.strict_sha256 FROM tracks t JOIN embedding_links l ON t.query_id=l.query_id ORDER BY t.track_id"
    ):
        track = json.loads(row["data"])
        index.append(
            {
                "track_id": track["track_id"],
                "spotify_row_id": track["spotify_row_id"],
                "lfm_record_key": track["lfm_record_key"],
                "composition_key": track["composition_key"],
                "split": track["split"],
                "query_id": row["query_id"],
                "lyrics_sha256": row["lyrics_sha256"],
                "source_strict_sha256": row["strict_sha256"],
                "vector_index": positions[row["lyrics_sha256"]],
            }
        )
    if vectors:
        frame = pl.DataFrame(vectors).with_columns(
            pl.col("embedding").cast(pl.Array(pl.Float32, 384))
        )
        atomic_frame(workspace / "vectors.parquet", frame)
        atomic_frame(workspace / "embedding_index.parquet", pl.DataFrame(index))
        atomic_json(
            workspace / "embedding_export.json",
            {
                "configuration_sha256": cfg_sha,
                "vectors": len(vectors),
                "tracks": len(index),
                "vectors_sha256": sha256_file(workspace / "vectors.parquet"),
                "index_sha256": sha256_file(workspace / "embedding_index.parquet"),
                "note": "Índice e vetores são um par: conferir ambos os hashes antes de uso; chave estável é lyrics_sha256.",
            },
        )


def generate(
    workspace,
    *,
    limit=None,
    batch_size=64,
    checkpoint_every=32,
    model_loader=_load_model,
    tokenizer_audit=_tokenize_audit_records,
    encoder=_encode_unique_records,
):
    config = load_yaml(CONFIG)
    cfg = encoder_config(config, batch_size)
    cfg_sha = encoding_signature(cfg)
    with exclusive(workspace), closing(connect(workspace)) as db:
        check_prepared(db, config)
        import_legacy_vectors(db, cfg)
        rows = db.execute(
            "SELECT q.* FROM queries q LEFT JOIN embedding_links l ON q.query_id=l.query_id WHERE q.status IN ('accepted_exact_unique','accepted_exact_equivalent') AND l.query_id IS NULL ORDER BY q.query_id"
        ).fetchall()
        if limit is not None:
            rows = rows[:limit]
        processed, reused, generated, model = 0, 0, 0, None
        interrupted = False
        failed = False
        try:
            for start in range(0, len(rows), checkpoint_every):
                records = [
                    read_accepted_text(row) for row in rows[start : start + checkpoint_every]
                ]
                missing = []
                for record in records:
                    old = db.execute(
                        "SELECT * FROM vectors WHERE lyrics_sha256=?", (record["lyrics_sha256"],)
                    ).fetchone()
                    if old:
                        read_vector(old, cfg_sha)
                        reused += 1
                    else:
                        missing.append(record)
                audited, vectors = [], {}
                if missing:
                    if model is None:
                        os.environ["HF_HUB_OFFLINE"] = "1"
                        os.environ["TRANSFORMERS_OFFLINE"] = "1"
                        _set_determinism(int(cfg["execution"]["seed"]))
                        model = model_loader(cfg)  # Snapshot local exato; nunca baixa encoder.
                    audited, _ = tokenizer_audit(missing, model.tokenizer, cfg)
                    vectors = encoder(audited, model, cfg)
                    require(
                        set(vectors) == {r["lyrics_sha256"] for r in missing},
                        "Encoder não retornou todos os hashes.",
                    )
                    # Mantém a construção de metadados original, sem exigir composição única entre versões.
                    frame = build_embedding_frame(audited, vectors, cfg)
                    require(frame.height == len(missing), "Quantidade de embeddings divergente.")
                with db:
                    for record in audited:
                        metadata = {
                            k: record[k]
                            for k in (
                                "token_count",
                                "chunk_count",
                                "detected_language",
                                "language_status",
                                "language_confidence",
                            )
                        }
                        save_vector(
                            db,
                            record["lyrics_sha256"],
                            vectors[record["lyrics_sha256"]],
                            cfg_sha,
                            metadata,
                            "manual_frozen_encoder",
                        )
                    for record in records:
                        db.execute(
                            "INSERT INTO embedding_links VALUES (?,?,?)",
                            (
                                record["query_id"],
                                record["lyrics_sha256"],
                                record["source_strict_sha256"],
                            ),
                        )
                generated += len(vectors)
                processed += len(records)
                progress(
                    db,
                    workspace,
                    stage="embedding",
                    processed_this_run=processed,
                    planned_this_run=len(rows),
                    reused_queries=reused,
                    new_unique_vectors=generated,
                )
        except KeyboardInterrupt:
            interrupted = True
        except Exception:
            failed = True
            raise
        finally:
            export_embeddings(db, workspace, cfg_sha)
            progress(
                db,
                workspace,
                stage="embedding_failed"
                if failed
                else "embedding_interrupted"
                if interrupted
                else "embedding_batch_complete",
                processed_this_run=processed,
                planned_this_run=len(rows),
                reused_queries=reused,
                new_unique_vectors=generated,
            )
        return 2 if interrupted else 0
