"""Embeddings MiniLM escalados v0.4 com o pipeline congelado da v0.2."""

from __future__ import annotations

import json
import time
from collections import Counter
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from .config import load_yaml, project_path
from .final_study_v040 import DEFAULT_CONFIG_PATH, EXPECTED_FROZEN_HASHES, _git_private_files
from .io import read_json, sha256_file, utc_now, write_json
from .lyrics_ambiguity_v011 import deduplicate_candidates, strict_plain_text_metrics
from .lyrics_embeddings_v020 import (
    FORBIDDEN_EMBEDDING_COLUMNS,
    _encode_unique_records,
    _load_model,
    _set_determinism,
    _tokenize_audit_records,
    build_embedding_frame,
    build_embedding_index,
    normalize_lyrics_text,
    sha256_text,
    validate_embedding_frame,
)
from .lyrics_pilot import _atomic_write_frame, _write_text
from .lyrics_pilot_v012 import ACCEPTED_STATUSES
from .lyrics_scale_v040 import audit_public_scale_outputs, locate_compatible_cache


def _embedding_config(config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "model": config["model"],
        "execution": config["embedding_execution"],
    }


def _load_private_text_records(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    results = pl.read_parquet(project_path(config["private_outputs"]["collection_results"]))
    lookup = pl.read_parquet(project_path(config["private_outputs"]["lookup"]))
    accepted = results.filter(pl.col("final_status").is_in(sorted(ACCEPTED_STATUSES))).select(
        "composition_key",
        "representative_track_id",
        "split",
        "selected_lrclib_id",
        "selected_candidate_key_sha256",
        "selected_strict_text_sha256",
        "final_status",
    )
    query_by_key = {str(row["composition_key"]): row for row in lookup.iter_rows(named=True)}
    current_dir = project_path(config["collection"]["cache_dir"])
    legacy_dir = project_path(config["inputs"]["legacy_cache"])
    output: list[dict[str, Any]] = []
    failures: Counter[str] = Counter()
    for row in accepted.sort("composition_key").iter_rows(named=True):
        key = str(row["composition_key"])
        query = query_by_key.get(key)
        if query is None:
            failures["query_missing"] += 1
            continue
        envelope, _ = locate_compatible_cache(query, current_dir, legacy_dir)
        if envelope is None:
            failures["cache_missing"] += 1
            continue
        candidates = [
            item
            for item in deduplicate_candidates(envelope)["unified"]
            if item["candidate_key_sha256"] == row["selected_candidate_key_sha256"]
        ]
        if len(candidates) != 1:
            failures["selected_candidate_missing"] += 1
            continue
        candidate = candidates[0]["candidate"]
        value = candidate.get("plainLyrics")
        if candidate.get("id") != row["selected_lrclib_id"]:
            failures["selected_lrclib_id_mismatch"] += 1
            continue
        if not isinstance(value, str) or not value.strip():
            failures["plain_lyrics_missing"] += 1
            continue
        strict_hash = strict_plain_text_metrics(value)["strict_text_sha256"]
        if strict_hash != row["selected_strict_text_sha256"]:
            failures["strict_sha256_mismatch"] += 1
            continue
        normalized = normalize_lyrics_text(value)
        if not normalized:
            failures["normalized_text_empty"] += 1
            continue
        output.append(
            {
                "composition_key": key,
                "track_id": row["representative_track_id"],
                "split": row["split"],
                "lyrics_sha256": sha256_text(normalized),
                "source_strict_sha256": strict_hash,
                "private_lyrics": normalized,
            }
        )
    if failures or len(output) != accepted.height:
        raise RuntimeError(
            "Pré-auditoria privada das letras falhou: "
            + json.dumps(dict(failures), ensure_ascii=False, sort_keys=True)
        )
    return output


def _pilot_vectors(config: Mapping[str, Any]) -> dict[str, np.ndarray]:
    path = project_path(config["inputs"]["pilot_embeddings"])
    if not path.exists():
        return {}
    frame = pl.read_parquet(path)
    revision = str(config["model"]["revision"])
    frame = frame.filter(pl.col("model_revision") == revision)
    vectors: dict[str, np.ndarray] = {}
    for row in frame.select("lyrics_sha256", "embedding").iter_rows(named=True):
        vector = np.asarray(row["embedding"], dtype=np.float32)
        if vector.shape == (384,) and np.isfinite(vector).all():
            norm = float(np.linalg.norm(vector))
            if abs(norm - 1.0) <= float(config["embedding_execution"]["numeric_tolerance"]):
                vectors[str(row["lyrics_sha256"])] = vector
    return vectors


def _numeric_aggregate(records: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = np.asarray([float(row[field]) for row in records], dtype=np.float64)
    return {
        "n": int(values.size),
        "mean": float(values.mean()) if values.size else None,
        "median": float(np.median(values)) if values.size else None,
        "minimum": float(values.min()) if values.size else None,
        "maximum": float(values.max()) if values.size else None,
    }


def _embedding_report(summary: Mapping[str, Any]) -> str:
    embeddings = summary["embeddings"]
    return f"""# Embeddings escalados das letras — v0.4

## Pipeline congelado

- Modelo: `sentence-transformers/all-MiniLM-L6-v2`.
- Revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
- Dimensão: 384; dtype: float32; limite: 256 word pieces, sendo 254 de conteúdo; overlap: 32.
- Agregação: média ponderada pelos tokens novos de cada chunk e normalização L2 final.
- Sem tradução, fine-tuning, PCA ou uso de popularidade.

## Resultados agregados

- Embeddings de desenvolvimento: {embeddings["development"]["rows"]} × 384.
- Embeddings de holdout: {embeddings["holdout"]["rows"]} × 384.
- Vetores do piloto reutilizados por hash compatível: {embeddings["reuse"]["compositions_reused_from_v0_2"]} composições.
- Novos hashes codificados: {embeddings["reuse"]["new_unique_hashes_encoded"]}.
- NaN: {embeddings["validation"]["nan_count"]}; infinito: {embeddings["validation"]["infinite_count"]}.
- Maior desvio da norma L2: {embeddings["validation"]["maximum_l2_deviation"]:.8f}.
- Idiomas: `{json.dumps(embeddings["language_status_counts"], ensure_ascii=False, sort_keys=True)}`.
- Tokens: `{json.dumps(embeddings["token_distribution"], ensure_ascii=False, sort_keys=True)}`.
- Chunks: `{json.dumps(embeddings["chunk_distribution"], ensure_ascii=False, sort_keys=True)}`.

As matrizes e índices individuais permanecem privados e separados por split. O arquivo de holdout não contém `spotify_popularity` nem qualquer target.
"""


def _reuse_complete(config: Mapping[str, Any]) -> dict[str, Any] | None:
    summary = read_json(config["public_outputs"]["scale_summary"], {})
    if not isinstance(summary, dict) or summary.get("status") != "complete":
        return None
    private = config["private_outputs"]
    for key in (
        "embeddings_development",
        "embeddings_holdout",
        "embedding_index_development",
        "embedding_index_holdout",
        "integrity_manifest",
    ):
        if not project_path(private[key]).exists():
            return None
    development = pl.read_parquet(project_path(private["embeddings_development"]))
    holdout = pl.read_parquet(project_path(private["embeddings_holdout"]))
    validate_embedding_frame(
        development,
        expected_rows=development.height,
        dimension=384,
        tolerance=float(config["embedding_execution"]["numeric_tolerance"]),
    )
    validate_embedding_frame(
        holdout,
        expected_rows=holdout.height,
        dimension=384,
        tolerance=float(config["embedding_execution"]["numeric_tolerance"]),
    )
    return {**summary, "idempotent_reuse": True}


def run_embeddings_scale_v040(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    force: bool = False,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    config = load_yaml(config_path)
    if not force:
        reused = _reuse_complete(config)
        if reused is not None:
            return reused
    summary = read_json(config["public_outputs"]["scale_summary"])
    if (
        not isinstance(summary, dict)
        or summary.get("status") != "collection_complete_embeddings_pending"
    ):
        raise AssertionError("Coleta v0.4 completa não encontrada.")
    if summary.get("holdout_target_loaded") is not False:
        raise AssertionError("Selo de target do holdout inválido.")
    records = _load_private_text_records(config)
    embedding_config = _embedding_config(config)
    _set_determinism(int(config["embedding_execution"]["seed"]))
    model = _load_model(embedding_config)
    audited, text_audit = _tokenize_audit_records(records, model.tokenizer, embedding_config)
    pilot = _pilot_vectors(config)
    needed_hashes = {str(row["lyrics_sha256"]) for row in audited}
    reused_vectors = {digest: pilot[digest] for digest in needed_hashes if digest in pilot}
    missing_records = [row for row in audited if str(row["lyrics_sha256"]) not in reused_vectors]
    generated = (
        _encode_unique_records(missing_records, model, embedding_config, progress)
        if missing_records
        else {}
    )
    vectors = {**reused_vectors, **generated}
    if set(vectors) != needed_hashes:
        raise AssertionError("Nem todos os hashes aceitos possuem embedding.")
    private = config["private_outputs"]
    validations: dict[str, dict[str, Any]] = {}
    split_outputs = {
        "development_train": ("embeddings_development", "embedding_index_development"),
        "holdout_test": ("embeddings_holdout", "embedding_index_holdout"),
    }
    frames: dict[str, pl.DataFrame] = {}
    for split, (embedding_key, index_key) in split_outputs.items():
        subset = [row for row in audited if row["split"] == split]
        frame = build_embedding_frame(subset, vectors, embedding_config)
        index = build_embedding_index(subset, vectors)
        if FORBIDDEN_EMBEDDING_COLUMNS & set(frame.columns):
            raise AssertionError("Embedding contém coluna proibida.")
        _atomic_write_frame(frame, private[embedding_key])
        _atomic_write_frame(index, private[index_key])
        persisted = pl.read_parquet(project_path(private[embedding_key]))
        validations[split] = validate_embedding_frame(
            persisted,
            expected_rows=len(subset),
            dimension=int(config["model"]["embedding_dimension"]),
            tolerance=float(config["embedding_execution"]["numeric_tolerance"]),
        )
        frames[split] = persisted
    all_matrix = np.vstack(
        [
            np.asarray(frames[split].get_column("embedding").to_list(), dtype=np.float32)
            for split in split_outputs
        ]
    )
    norms = np.linalg.norm(all_matrix, axis=1)
    reused_compositions = sum(str(row["lyrics_sha256"]) in reused_vectors for row in audited)
    language_counts = Counter(str(row["language_status"]) for row in audited)
    embedding_summary = {
        "model_id": config["model"]["id"],
        "model_revision": config["model"]["revision"],
        "dimension": 384,
        "dtype": "float32",
        "development": validations["development_train"],
        "holdout": validations["holdout_test"],
        "holdout_target_columns": [],
        "reuse": {
            "compositions_reused_from_v0_2": reused_compositions,
            "unique_hashes_reused_from_v0_2": len(reused_vectors),
            "new_unique_hashes_encoded": len(generated),
        },
        "language_status_counts": dict(sorted(language_counts.items())),
        "detected_language_counts": text_audit["detected_language_counts"],
        "token_distribution": _numeric_aggregate(audited, "token_count"),
        "chunk_distribution": _numeric_aggregate(audited, "chunk_count"),
        "validation": {
            "nan_count": int(np.isnan(all_matrix).sum()),
            "infinite_count": int(np.isinf(all_matrix).sum()),
            "maximum_l2_deviation": float(np.max(np.abs(norms - 1.0))),
            "all_tokens_covered_without_truncation": True,
            "separate_split_files": True,
        },
        "duration_seconds": time.perf_counter() - started,
    }
    if (
        embedding_summary["validation"]["nan_count"]
        or embedding_summary["validation"]["infinite_count"]
    ):
        raise AssertionError("Embeddings contêm NaN ou infinito.")
    if embedding_summary["holdout_target_columns"]:
        raise AssertionError("Target presente no arquivo de holdout.")
    private_hashes = {
        key: sha256_file(project_path(private[key]))
        for key in (
            "cohort",
            "reserve",
            "collection_results",
            "lyrics_index",
            "embeddings_development",
            "embeddings_holdout",
            "embedding_index_development",
            "embedding_index_holdout",
        )
    }
    manifest = {
        "status": "complete",
        "created_at": utc_now(),
        "private_artifact_hashes": private_hashes,
        "rows": {
            "accepted": len(audited),
            "development": frames["development_train"].height,
            "holdout": frames["holdout_test"].height,
        },
        "model_revision": config["model"]["revision"],
        "holdout_target_present": False,
    }
    write_json(private["integrity_manifest"], manifest)
    for path, expected in EXPECTED_FROZEN_HASHES.items():
        if sha256_file(project_path(path)) != expected:
            raise AssertionError("Base ou split mudaram durante os embeddings.")
    private_git = _git_private_files()
    if private_git["tracked"] or private_git["staged"]:
        raise AssertionError("Arquivo privado tracked ou staged.")
    summary["status"] = "complete"
    summary["completed_at"] = utc_now()
    summary["embeddings"] = embedding_summary
    summary["private_integrity_manifest_sha256"] = sha256_file(
        project_path(private["integrity_manifest"])
    )
    summary["privacy"] = {
        "private_tracked": [],
        "private_staged": [],
        "holdout_target_loaded": False,
        "lyrics_text_public": False,
        "individual_outputs_public": False,
    }
    _write_text(config["public_outputs"]["embeddings_report"], _embedding_report(summary))
    write_json(config["public_outputs"]["scale_summary"], summary)
    audit_public_scale_outputs(
        [
            config["public_outputs"]["lyrics_report"],
            config["public_outputs"]["embeddings_report"],
            config["public_outputs"]["scale_summary"],
        ]
    )
    return summary
