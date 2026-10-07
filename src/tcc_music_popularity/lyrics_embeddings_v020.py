"""Geração privada e auditoria pública do piloto de embeddings de letras v0.2."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import platform
import random
import subprocess
import time
import unicodedata
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from .config import PROJECT_ROOT, load_yaml, project_path
from .io import git_commit, read_json, sha256_file, utc_now, write_json
from .lyrics_ambiguity_v011 import deduplicate_candidates, strict_plain_text_metrics
from .lyrics_pilot import _atomic_write_frame, _write_text

PROTOCOL_VERSION = "v0.2"
DEFAULT_CONFIG_PATH = "configs/lyrics_embeddings_v0_2.yaml"
ACCEPTED_STATUSES = {"accepted_exact_unique", "accepted_exact_equivalent"}
FORBIDDEN_INPUT_COLUMNS = {"spotify_popularity", "genius_lyrics_views", "lfm_playcount"}
FORBIDDEN_EMBEDDING_COLUMNS = {
    "plainLyrics",
    "syncedLyrics",
    "text",
    "snippet",
    "tokens",
    "token_ids",
    "ngrams",
    "n-grams",
    *FORBIDDEN_INPUT_COLUMNS,
}
PUBLIC_FORBIDDEN_KEYS = {
    "composition_key",
    "track_id",
    "lyrics_sha256",
    "plainlyrics",
    "syncedlyrics",
    "snippet",
    "token_ids",
}


def normalize_lyrics_text(value: str) -> str:
    """Aplica somente as normalizações textuais autorizadas pelo protocolo v0.2."""
    normalized = str(value).replace("\ufeff", "")
    normalized = unicodedata.normalize("NFC", normalized)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip(" \t") for line in normalized.split("\n")]
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_token_chunks(
    token_ids: Sequence[int], *, content_limit: int, overlap: int
) -> list[dict[str, Any]]:
    """Cria janelas completas e registra quantos tokens novos cada janela representa."""
    if content_limit <= 0:
        raise ValueError("content_limit deve ser positivo")
    if overlap < 0 or overlap >= content_limit:
        raise ValueError("overlap deve estar entre zero e content_limit - 1")
    total = len(token_ids)
    if total == 0:
        return []
    chunks: list[dict[str, Any]] = []
    start = 0
    previous_end = 0
    while start < total:
        end = min(start + content_limit, total)
        new_count = end - previous_end if chunks else end - start
        chunks.append(
            {
                "token_ids": list(token_ids[start:end]),
                "start": start,
                "end": end,
                "new_token_count": new_count,
            }
        )
        if end == total:
            break
        previous_end = end
        start = end - overlap
    validate_token_coverage(token_ids, chunks)
    return chunks


def validate_token_coverage(token_ids: Sequence[int], chunks: Sequence[Mapping[str, Any]]) -> None:
    total = len(token_ids)
    if total == 0:
        if chunks:
            raise AssertionError("Texto vazio não deve produzir chunks.")
        return
    coverage = np.zeros(total, dtype=np.int16)
    previous_end = 0
    weight_sum = 0
    for index, chunk in enumerate(chunks):
        start = int(chunk["start"])
        end = int(chunk["end"])
        observed = list(chunk["token_ids"])
        if observed != list(token_ids[start:end]):
            raise AssertionError("Chunk não corresponde ao intervalo original de tokens.")
        coverage[start:end] += 1
        expected_new = end - previous_end if index else end - start
        if int(chunk["new_token_count"]) != expected_new:
            raise AssertionError("Peso de tokens novos inconsistente.")
        weight_sum += expected_new
        previous_end = end
    if not bool(np.all(coverage >= 1)) or int(weight_sum) != total:
        raise AssertionError("Cobertura integral dos tokens não foi preservada.")


def weighted_chunk_aggregate(
    chunk_embeddings: np.ndarray, new_token_weights: Sequence[int]
) -> np.ndarray:
    vectors = np.asarray(chunk_embeddings, dtype=np.float32)
    weights = np.asarray(new_token_weights, dtype=np.float64)
    if vectors.ndim != 2 or vectors.shape[0] != weights.size or not weights.size:
        raise ValueError("Embeddings e pesos de chunks são incompatíveis.")
    if not np.isfinite(vectors).all() or not np.isfinite(weights).all() or np.any(weights <= 0):
        raise ValueError("Embeddings ou pesos inválidos.")
    pooled = np.average(vectors.astype(np.float64), axis=0, weights=weights)
    norm = float(np.linalg.norm(pooled))
    if not math.isfinite(norm) or norm == 0:
        raise ValueError("Agregação produziu vetor sem norma válida.")
    return (pooled / norm).astype(np.float32)


def classify_language_status(code: str, confidence: float, threshold: float) -> str:
    if confidence < threshold:
        return "uncertain"
    return "english" if code == "en" else "non_english"


def _language_identifier():
    from langid.langid import LanguageIdentifier, model

    return LanguageIdentifier.from_modelstring(model, norm_probs=True)


def detect_language(
    value: str, *, threshold: float, identifier: Any | None = None
) -> dict[str, Any]:
    identifier = identifier or _language_identifier()
    code, confidence = identifier.classify(value)
    return {
        "detected_language": str(code),
        "language_confidence": float(confidence),
        "language_status": classify_language_status(str(code), float(confidence), threshold),
    }


def _numeric_stats(values: Sequence[float | int]) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    if not array.size:
        return {
            "n": 0,
            "mean": None,
            "std": None,
            "minimum": None,
            "q1": None,
            "median": None,
            "q3": None,
            "maximum": None,
        }
    return {
        "n": int(array.size),
        "mean": round(float(array.mean()), 6),
        "std": round(float(array.std(ddof=1)), 6) if array.size > 1 else 0.0,
        "minimum": float(array.min()),
        "q1": round(float(np.quantile(array, 0.25)), 6),
        "median": round(float(np.median(array)), 6),
        "q3": round(float(np.quantile(array, 0.75)), 6),
        "maximum": float(array.max()),
    }


def _package_version(name: str) -> str:
    return importlib.metadata.version(name)


def _git_private_files() -> dict[str, list[str]]:
    tracked = subprocess.run(
        [
            "git",
            "ls-files",
            "data/raw/lyrics_private",
            "data/interim/lyrics_private",
            "data/derived/private_embeddings",
        ],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    staged_all = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    staged = [
        path
        for path in staged_all
        if path.startswith(
            (
                "data/raw/lyrics_private/",
                "data/interim/lyrics_private/",
                "data/derived/private_embeddings/",
            )
        )
    ]
    return {"tracked": tracked, "staged": staged}


def _load_accepted_private_inputs(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    results = pl.read_parquet(project_path(config["inputs"]["full_results"]))
    selected_columns = [
        "composition_key",
        "representative_track_id",
        "selected_candidate_key_sha256",
        "selected_lrclib_id",
        "selected_strict_text_sha256",
        "final_status",
    ]
    if FORBIDDEN_INPUT_COLUMNS & set(selected_columns):
        raise AssertionError("Variável resposta foi selecionada para o encoder.")
    accepted = results.filter(pl.col("final_status").is_in(sorted(ACCEPTED_STATUSES))).select(
        selected_columns
    )
    expected = int(config["expected_accepted_compositions"])
    if accepted.height != expected or accepted.get_column("composition_key").n_unique() != expected:
        raise AssertionError("O universo aceito não contém exatamente 1.441 chaves únicas.")
    cache_by_key: dict[str, dict[str, Any]] = {}
    for path in project_path(config["inputs"]["private_cache"]).glob("*.json"):
        envelope = json.loads(path.read_text(encoding="utf-8"))
        key = envelope.get("composition_key")
        if isinstance(key, str):
            cache_by_key[key] = envelope
    output: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for row in accepted.sort("composition_key").iter_rows(named=True):
        key = str(row["composition_key"])
        envelope = cache_by_key.get(key)
        if envelope is None:
            failures.append({"composition_key": key, "reason": "cache_missing"})
            continue
        candidates = [
            item
            for item in deduplicate_candidates(envelope)["unified"]
            if item["candidate_key_sha256"] == row["selected_candidate_key_sha256"]
        ]
        if len(candidates) != 1:
            failures.append({"composition_key": key, "reason": "selected_candidate_missing"})
            continue
        candidate = candidates[0]["candidate"]
        value = candidate.get("plainLyrics")
        if candidate.get("id") != row["selected_lrclib_id"]:
            failures.append({"composition_key": key, "reason": "selected_lrclib_id_mismatch"})
            continue
        if not isinstance(value, str) or not value.strip():
            failures.append({"composition_key": key, "reason": "plain_lyrics_missing"})
            continue
        observed_strict = strict_plain_text_metrics(value)["strict_text_sha256"]
        if observed_strict != row["selected_strict_text_sha256"]:
            failures.append({"composition_key": key, "reason": "strict_sha256_mismatch"})
            continue
        normalized = normalize_lyrics_text(value)
        if not normalized:
            failures.append({"composition_key": key, "reason": "normalized_text_empty"})
            continue
        output.append(
            {
                "composition_key": key,
                "track_id": row["representative_track_id"],
                "lyrics_sha256": sha256_text(normalized),
                "source_strict_sha256": observed_strict,
                "private_lyrics": normalized,
            }
        )
    if failures or len(output) != expected:
        counts = Counter(item["reason"] for item in failures)
        raise RuntimeError(
            "Pré-auditoria dos textos falhou: "
            + json.dumps(
                {"valid": len(output), "failures": counts}, ensure_ascii=False, default=dict
            )
        )
    return output


def _input_fingerprint(records: Sequence[Mapping[str, Any]]) -> str:
    payload = [
        {"composition_key": row["composition_key"], "lyrics_sha256": row["lyrics_sha256"]}
        for row in records
    ]
    return sha256_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def _set_determinism(seed: int) -> None:
    import torch

    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def _load_model(config: Mapping[str, Any]):
    from sentence_transformers import SentenceTransformer

    snapshot = project_path(config["model"]["private_snapshot"])
    revision = str(config["model"]["revision"])
    if not snapshot.is_dir() or snapshot.name != revision:
        raise RuntimeError("Snapshot local não corresponde à revision exata configurada.")
    model = SentenceTransformer(
        str(snapshot),
        device=str(config["execution"]["device"]),
        local_files_only=True,
    )
    model.eval()
    dimension = int(model.get_sentence_embedding_dimension())
    if dimension != int(config["model"]["embedding_dimension"]):
        raise AssertionError("Dimensão do modelo difere de 384.")
    if int(model.max_seq_length) != int(config["model"]["maximum_tokens_including_special"]):
        raise AssertionError("Limite do modelo difere de 256 tokens.")
    return model


def _tokenize_audit_records(
    records: Sequence[Mapping[str, Any]], tokenizer: Any, config: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    maximum = int(config["model"]["maximum_tokens_including_special"])
    special = int(tokenizer.num_special_tokens_to_add(pair=False))
    content_limit = maximum - special
    overlap = int(config["execution"]["overlap_content_tokens"])
    threshold = float(config["execution"]["language_confidence_threshold"])
    short_limit = int(config["execution"]["very_short_token_threshold"])
    audited: list[dict[str, Any]] = []
    language_identifier = _language_identifier()
    for record in records:
        value = str(record["private_lyrics"])
        token_ids = tokenizer.encode(
            value,
            add_special_tokens=False,
            truncation=False,
            verbose=False,
        )
        chunks = build_token_chunks(token_ids, content_limit=content_limit, overlap=overlap)
        language = detect_language(value, threshold=threshold, identifier=language_identifier)
        audited.append(
            {
                **record,
                "character_count": len(value),
                "line_count": len(value.split("\n")),
                "token_count": len(token_ids),
                "chunk_count": len(chunks),
                "token_ids_private": token_ids,
                "chunks_private": chunks,
                **language,
            }
        )
    hash_counts = Counter(str(row["lyrics_sha256"]) for row in audited)
    language_status_counts = Counter(row["language_status"] for row in audited)
    audit = {
        "accepted_compositions": len(audited),
        "strict_sha256_unique": len(hash_counts),
        "duplicate_compositions_beyond_unique_hashes": sum(
            value - 1 for value in hash_counts.values()
        ),
        "duplicate_hash_groups": sum(value > 1 for value in hash_counts.values()),
        "empty_lyrics": sum(int(row["token_count"]) == 0 for row in audited),
        "very_short_threshold_tokens": short_limit,
        "very_short_lyrics": sum(int(row["token_count"]) < short_limit for row in audited),
        "above_single_chunk_content_limit": sum(
            int(row["token_count"]) > content_limit for row in audited
        ),
        "model_maximum_including_special_tokens": maximum,
        "special_tokens_per_chunk": special,
        "content_tokens_per_chunk": content_limit,
        "overlap_content_tokens": overlap,
        "character_distribution": _numeric_stats([row["character_count"] for row in audited]),
        "line_distribution": _numeric_stats([row["line_count"] for row in audited]),
        "token_distribution": _numeric_stats([row["token_count"] for row in audited]),
        "chunk_distribution": _numeric_stats([row["chunk_count"] for row in audited]),
        "language_status_counts": {
            status: int(language_status_counts.get(status, 0))
            for status in ("english", "non_english", "uncertain")
        },
        "detected_language_counts": dict(
            sorted(Counter(row["detected_language"] for row in audited).items())
        ),
        "language_confidence_distribution": _numeric_stats(
            [row["language_confidence"] for row in audited]
        ),
    }
    if audit["empty_lyrics"]:
        raise AssertionError("Há letra vazia no universo aceito.")
    return audited, audit


def _encode_unique_records(
    audited: Sequence[Mapping[str, Any]],
    model: Any,
    config: Mapping[str, Any],
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, np.ndarray]:
    import torch
    import torch.nn.functional as functional

    tokenizer = model.tokenizer
    unique: dict[str, Mapping[str, Any]] = {}
    for record in audited:
        unique.setdefault(str(record["lyrics_sha256"]), record)
    ordered_hashes = sorted(unique)
    flat: list[dict[str, Any]] = []
    for digest in ordered_hashes:
        for chunk in unique[digest]["chunks_private"]:
            flat.append(
                {
                    "lyrics_sha256": digest,
                    "token_ids": chunk["token_ids"],
                    "weight": int(chunk["new_token_count"]),
                }
            )
    batch_size = int(config["execution"]["batch_size"])
    dimension = int(config["model"]["embedding_dimension"])
    vectors_by_hash: dict[str, list[np.ndarray]] = {digest: [] for digest in ordered_hashes}
    weights_by_hash: dict[str, list[int]] = {digest: [] for digest in ordered_hashes}
    maximum = int(config["model"]["maximum_tokens_including_special"])
    with torch.inference_mode():
        for start in range(0, len(flat), batch_size):
            batch = flat[start : start + batch_size]
            prepared = [
                tokenizer.prepare_for_model(
                    item["token_ids"],
                    add_special_tokens=True,
                    truncation=False,
                    max_length=maximum,
                    return_attention_mask=True,
                )
                for item in batch
            ]
            features = tokenizer.pad(prepared, padding=True, return_tensors="pt")
            features = {key: value.to(model.device) for key, value in features.items()}
            output = model(features)["sentence_embedding"]
            output = functional.normalize(output.float(), p=2, dim=1)
            encoded = output.cpu().numpy().astype(np.float32, copy=False)
            if encoded.shape != (len(batch), dimension):
                raise AssertionError("Batch retornou dimensão inesperada.")
            for item, vector in zip(batch, encoded, strict=True):
                digest = str(item["lyrics_sha256"])
                vectors_by_hash[digest].append(vector.copy())
                weights_by_hash[digest].append(int(item["weight"]))
            if progress:
                progress(min(start + len(batch), len(flat)), len(flat))
    return {
        digest: weighted_chunk_aggregate(np.stack(vectors_by_hash[digest]), weights_by_hash[digest])
        for digest in ordered_hashes
    }


def build_embedding_frame(
    audited: Sequence[Mapping[str, Any]],
    vectors_by_hash: Mapping[str, np.ndarray],
    config: Mapping[str, Any],
) -> pl.DataFrame:
    dimension = int(config["model"]["embedding_dimension"])
    rows: list[dict[str, Any]] = []
    vectors: list[list[float]] = []
    for record in audited:
        digest = str(record["lyrics_sha256"])
        vector = np.asarray(vectors_by_hash[digest], dtype=np.float32)
        rows.append(
            {
                "composition_key": record["composition_key"],
                "track_id": record["track_id"],
                "lyrics_sha256": digest,
                "token_count": int(record["token_count"]),
                "chunk_count": int(record["chunk_count"]),
                "detected_language": record["detected_language"],
                "language_status": record["language_status"],
                "language_confidence": float(record["language_confidence"]),
                "model_id": config["model"]["id"],
                "model_revision": config["model"]["revision"],
                "protocol_version": PROTOCOL_VERSION,
            }
        )
        vectors.append(vector.tolist())
    frame = pl.DataFrame(rows)
    return frame.with_columns(
        pl.Series("embedding", vectors, dtype=pl.Array(pl.Float32, dimension))
    ).select(
        "composition_key",
        "track_id",
        "lyrics_sha256",
        "embedding",
        "token_count",
        "chunk_count",
        "detected_language",
        "language_status",
        "language_confidence",
        "model_id",
        "model_revision",
        "protocol_version",
    )


def build_embedding_index(
    audited: Sequence[Mapping[str, Any]], vectors_by_hash: Mapping[str, np.ndarray]
) -> pl.DataFrame:
    counts = Counter(str(row["lyrics_sha256"]) for row in audited)
    metadata = {str(row["lyrics_sha256"]): row for row in audited}
    return pl.DataFrame(
        [
            {
                "vector_index": index,
                "lyrics_sha256": digest,
                "reuse_count": counts[digest],
                "token_count": int(metadata[digest]["token_count"]),
                "chunk_count": int(metadata[digest]["chunk_count"]),
                "detected_language": metadata[digest]["detected_language"],
                "language_status": metadata[digest]["language_status"],
            }
            for index, digest in enumerate(sorted(vectors_by_hash))
        ]
    )


def _embedding_matrix(frame: pl.DataFrame) -> np.ndarray:
    return np.asarray(frame.get_column("embedding").to_list(), dtype=np.float32)


def validate_embedding_frame(
    frame: pl.DataFrame, *, expected_rows: int, dimension: int, tolerance: float
) -> dict[str, Any]:
    import pyarrow as pa

    if frame.height != expected_rows:
        raise AssertionError("Quantidade de embeddings diferente do esperado.")
    if frame.get_column("composition_key").n_unique() != expected_rows:
        raise AssertionError("Há composition_key duplicada.")
    forbidden = sorted(FORBIDDEN_EMBEDDING_COLUMNS & set(frame.columns))
    if forbidden:
        raise AssertionError(f"Colunas proibidas nos embeddings: {forbidden}")
    arrow_type = frame.to_arrow().schema.field("embedding").type
    if (
        not pa.types.is_fixed_size_list(arrow_type)
        or arrow_type.list_size != dimension
        or arrow_type.value_type != pa.float32()
    ):
        raise AssertionError("Embedding não está armazenado como Array[float32, 384].")
    matrix = _embedding_matrix(frame)
    if matrix.shape != (expected_rows, dimension) or matrix.dtype != np.float32:
        raise AssertionError("Matriz de embeddings com forma ou dtype inválido.")
    nan_count = int(np.isnan(matrix).sum())
    infinite_count = int(np.isinf(matrix).sum())
    norms = np.linalg.norm(matrix, axis=1)
    maximum_deviation = float(np.max(np.abs(norms - 1.0)))
    if nan_count or infinite_count or maximum_deviation > tolerance:
        raise AssertionError("Falha na validação numérica dos embeddings.")
    duplicate_mismatches = 0
    for group in frame.group_by("lyrics_sha256", maintain_order=True):
        group_frame = group[1]
        if group_frame.height > 1:
            group_matrix = _embedding_matrix(group_frame)
            duplicate_mismatches += int(not bool(np.all(group_matrix == group_matrix[0])))
    if duplicate_mismatches:
        raise AssertionError("Hashes iguais não reutilizaram vetores idênticos.")
    return {
        "rows": frame.height,
        "dimensions": dimension,
        "dtype": "float32",
        "nan_count": nan_count,
        "infinite_count": infinite_count,
        "l2_norm_distribution": _numeric_stats(norms),
        "maximum_absolute_l2_deviation": maximum_deviation,
        "duplicate_hash_embedding_mismatches": duplicate_mismatches,
        "forbidden_columns": forbidden,
    }


def _dimension_diagnostics(matrix: np.ndarray) -> dict[str, Any]:
    means = matrix.mean(axis=0, dtype=np.float64)
    stds = matrix.std(axis=0, ddof=1, dtype=np.float64)
    return {
        "mean_by_dimension": [round(float(value), 9) for value in means],
        "std_by_dimension": [round(float(value), 9) for value in stds],
        "constant_dimensions_std_le_1e_12": int(np.sum(stds <= 1e-12)),
        "near_constant_dimensions_std_le_1e_6": int(np.sum(stds <= 1e-6)),
        "dimension_mean_distribution": _numeric_stats(means),
        "dimension_std_distribution": _numeric_stats(stds),
    }


def _similarity_diagnostics(matrix: np.ndarray, config: Mapping[str, Any]) -> dict[str, Any]:
    seed = int(config["execution"]["seed"])
    size = int(config["execution"]["deterministic_pair_sample_size"])
    rng = np.random.default_rng(seed)
    left = rng.integers(0, matrix.shape[0], size=size)
    right = rng.integers(0, matrix.shape[0], size=size)
    equal = left == right
    right[equal] = (right[equal] + 1) % matrix.shape[0]
    similarities = np.sum(matrix[left] * matrix[right], axis=1, dtype=np.float64)
    high = float(config["execution"]["excessive_similarity_threshold"])
    low = float(config["execution"]["excessive_difference_threshold"])
    stats = _numeric_stats(similarities)
    stats.update(
        {
            "sample_size": size,
            "seed": seed,
            "excessive_similarity_threshold": high,
            "excessively_similar_pairs": int(np.sum(similarities >= high)),
            "excessive_difference_threshold": low,
            "excessively_different_pairs": int(np.sum(similarities <= low)),
        }
    )
    return stats


def _pca_metrics(matrix: np.ndarray) -> dict[str, Any]:
    centered = matrix.astype(np.float64) - matrix.mean(axis=0, dtype=np.float64)
    singular_values = np.linalg.svd(centered, full_matrices=False, compute_uv=False)
    variances = singular_values**2 / max(matrix.shape[0] - 1, 1)
    total = float(variances.sum())
    ratios = variances / total if total else np.zeros_like(variances)
    cumulative = np.cumsum(ratios)

    def components_for(value: float) -> int:
        return int(np.searchsorted(cumulative, value, side="left") + 1)

    positive = ratios[ratios > 0]
    effective_rank = float(np.exp(-np.sum(positive * np.log(positive)))) if positive.size else 0.0
    return {
        "rows": int(matrix.shape[0]),
        "dimensions": int(matrix.shape[1]),
        "centered": True,
        "dimension_standardization": False,
        "first_20_explained_variance_ratio": [round(float(value), 9) for value in ratios[:20]],
        "first_20_cumulative_variance": [round(float(value), 9) for value in cumulative[:20]],
        "components_for_80_percent": components_for(0.80),
        "components_for_90_percent": components_for(0.90),
        "components_for_95_percent": components_for(0.95),
        "effective_rank": round(effective_rank, 6),
    }


def public_payload_is_aggregate(payload: Any) -> bool:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            folded = str(key).casefold()
            if folded in PUBLIC_FORBIDDEN_KEYS:
                return False
            if not public_payload_is_aggregate(value):
                return False
        return True
    if isinstance(payload, list):
        return all(public_payload_is_aggregate(value) for value in payload)
    if isinstance(payload, str):
        folded = payload.replace("\\", "/").casefold()
        return not any(
            marker in folded
            for marker in ("data/raw/lyrics_private", "data/derived/private_embeddings")
        )
    return True


def _markdown_table(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def _audit_report(summary: Mapping[str, Any]) -> str:
    audit = summary["text_audit"]
    numeric = summary["numeric_validation"]
    similarity = summary["similarity"]
    return f"""# Piloto de embeddings das letras — auditoria v0.2

## Escopo

Foram processadas exclusivamente {audit["accepted_compositions"]} composições aceitas do `development_train`. Nenhuma variável de popularidade, métrica Genius/LFM, observação de holdout ou texto foi fornecida aos relatórios públicos. Não houve fine-tuning ou treinamento preditivo.

## Encoder e protocolo

- Modelo: `{summary["model"]["id"]}`.
- Revision imutável: `{summary["model"]["revision"]}`.
- Tokenizer: `{summary["model"]["tokenizer_class"]}`.
- Dispositivo/dtype: `{summary["environment"]["device"]}` / `{summary["environment"]["dtype"]}`.
- Limite: {audit["model_maximum_including_special_tokens"]} tokens incluindo {audit["special_tokens_per_chunk"]} especiais; capacidade de conteúdo {audit["content_tokens_per_chunk"]}.
- Overlap: {audit["overlap_content_tokens"]} tokens de conteúdo.

Para chunks normalizados $z_j$, intervalo $[s_j,e_j)$ e fim anterior $e_{{j-1}}$, o peso é $w_1=e_1-s_1$ e $w_j=e_j-e_{{j-1}}$. O vetor da música é $v=\\operatorname{{L2}}(\\sum_j w_j z_j / \\sum_j w_j)$. Assim, tokens de overlap não recebem peso duplicado.

## Auditoria agregada dos textos

- Hashes estritos únicos: {audit["strict_sha256_unique"]}.
- Composições adicionais em hashes duplicados: {audit["duplicate_compositions_beyond_unique_hashes"]}.
- Letras vazias: {audit["empty_lyrics"]}.
- Muito curtas (< {audit["very_short_threshold_tokens"]} tokens): {audit["very_short_lyrics"]}.
- Acima de um chunk: {audit["above_single_chunk_content_limit"]}.
- Caracteres: `{json.dumps(audit["character_distribution"], ensure_ascii=False, sort_keys=True)}`.
- Linhas: `{json.dumps(audit["line_distribution"], ensure_ascii=False, sort_keys=True)}`.
- Tokens: `{json.dumps(audit["token_distribution"], ensure_ascii=False, sort_keys=True)}`.
- Chunks: `{json.dumps(audit["chunk_distribution"], ensure_ascii=False, sort_keys=True)}`.

## Idioma

- Status: `{json.dumps(audit["language_status_counts"], ensure_ascii=False, sort_keys=True)}`.
- Idiomas detectados: `{json.dumps(audit["detected_language_counts"], ensure_ascii=False, sort_keys=True)}`.
- Confiança: `{json.dumps(audit["language_confidence_distribution"], ensure_ascii=False, sort_keys=True)}`.
- Detector: `{summary["environment"]["language_detector"]}` com probabilidade normalizada e limiar {summary["parameters"]["language_confidence_threshold"]}.

Nenhuma letra foi excluída por idioma.

## Validação numérica

- Forma: {numeric["rows"]} × {numeric["dimensions"]}.
- Dtype: `{numeric["dtype"]}`.
- NaN/infinito: {numeric["nan_count"]}/{numeric["infinite_count"]}.
- Normas L2: `{json.dumps(numeric["l2_norm_distribution"], ensure_ascii=False, sort_keys=True)}`.
- Maior desvio de norma: {numeric["maximum_absolute_l2_deviation"]}.
- Dimensões constantes/quase constantes: {summary["dimension_diagnostics"]["constant_dimensions_std_le_1e_12"]}/{summary["dimension_diagnostics"]["near_constant_dimensions_std_le_1e_6"]}.
- Reexecução determinística: maior diferença absoluta {numeric["deterministic_sample_max_absolute_difference"]}.
- Cobertura integral sem truncamento: {numeric["all_tokens_covered_without_truncation"]}.

## Similaridade

`{json.dumps(similarity, ensure_ascii=False, sort_keys=True)}`

Diagnóstico de colapso: `{summary["collapse_diagnosis"]}`.

## Privacidade e limites

Os artefatos públicos contêm apenas estatísticas agregadas. A análise é descritiva e não causal. A disponibilidade e o idioma das letras limitam a população para a qual análises futuras poderão generalizar.
"""


def _pca_report(summary: Mapping[str, Any]) -> str:
    pca = summary["pca_exploratory"]["by_composition"]
    rows = [
        {
            "componente": index + 1,
            "variancia": value,
            "acumulada": pca["first_20_cumulative_variance"][index],
        }
        for index, value in enumerate(pca["first_20_explained_variance_ratio"])
    ]
    comparison = summary["pca_exploratory"]["unique_hash_comparison"]
    return f"""# PCA exploratória dos embeddings de letras — v0.2

Esta PCA é exclusivamente exploratória, usa somente as {pca["rows"]} composições aceitas de `development_train`, centraliza os embeddings e não padroniza cada dimensão separadamente. Popularidade não participou do ajuste. Componentes não são interpretados causalmente e a transformação não foi salva como etapa definitiva.

## Resumo

- Componentes para 80%: {pca["components_for_80_percent"]}.
- Componentes para 90%: {pca["components_for_90_percent"]}.
- Componentes para 95%: {pca["components_for_95_percent"]}.
- Effective rank: {pca["effective_rank"]}.
- Comparação por hashes únicos: {comparison}.

## Primeiros componentes

{_markdown_table(rows, ["componente", "variancia", "acumulada"])}

## Regra para modelagem futura

A PCA definitiva dos modelos será ajustada somente dentro dos dados de treinamento de cada split/fold, nunca utilizando validação ou teste.

Esta exploração não substitui a análise sugerida pelo orientador para a modelagem final e não demonstra capacidade preditiva.
"""


def _file_hashes(paths: Sequence[str | Path]) -> dict[str, str]:
    return {Path(path).name: sha256_file(project_path(path)) for path in paths}


def _reuse_complete_run(config: Mapping[str, Any], input_fingerprint: str) -> dict[str, Any] | None:
    summary = read_json(config["outputs"]["run_summary"], {})
    required = [
        config["outputs"][key] for key in ("embeddings", "index", "manifest", "audit", "pca")
    ]
    if (
        summary.get("status") == "complete"
        and summary.get("input_dataset_fingerprint") == input_fingerprint
        and summary.get("model", {}).get("revision") == config["model"]["revision"]
        and all(project_path(path).exists() for path in required)
    ):
        validate_embedding_frame(
            pl.read_parquet(project_path(config["outputs"]["embeddings"])),
            expected_rows=int(config["expected_accepted_compositions"]),
            dimension=int(config["model"]["embedding_dimension"]),
            tolerance=float(config["execution"]["numeric_tolerance"]),
        )
        return summary
    return None


def run_lyrics_embeddings_v020(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    force: bool = False,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    config = load_yaml(config_path)
    seed = int(config["execution"]["seed"])
    _set_determinism(seed)
    frozen_paths = [config["inputs"]["modeling_base"], config["inputs"]["split_assignments"]]
    frozen_before = _file_hashes(frozen_paths)
    records = _load_accepted_private_inputs(config)
    fingerprint = _input_fingerprint(records)
    if not force:
        reused = _reuse_complete_run(config, fingerprint)
        if reused is not None:
            return {**reused, "idempotent_reuse": True}
    model = _load_model(config)
    tokenizer = model.tokenizer
    audited, text_audit = _tokenize_audit_records(records, tokenizer, config)
    generation_started = time.perf_counter()
    vectors_by_hash = _encode_unique_records(audited, model, config, progress)
    generation_seconds = time.perf_counter() - generation_started
    frame = build_embedding_frame(audited, vectors_by_hash, config)
    index = build_embedding_index(audited, vectors_by_hash)
    embeddings_path = project_path(config["outputs"]["embeddings"])
    index_path = project_path(config["outputs"]["index"])
    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_frame(frame, embeddings_path)
    _atomic_write_frame(index, index_path)
    persisted = pl.read_parquet(embeddings_path)
    validation = validate_embedding_frame(
        persisted,
        expected_rows=int(config["expected_accepted_compositions"]),
        dimension=int(config["model"]["embedding_dimension"]),
        tolerance=float(config["execution"]["numeric_tolerance"]),
    )
    sample_hashes = sorted(vectors_by_hash)[:5]
    sample = [row for row in audited if row["lyrics_sha256"] in set(sample_hashes)]
    repeated = _encode_unique_records(sample, model, config)
    validation["deterministic_sample_size"] = len(sample_hashes)
    validation["deterministic_sample_max_absolute_difference"] = max(
        float(np.max(np.abs(vectors_by_hash[digest] - repeated[digest])))
        for digest in sample_hashes
    )
    validation["all_tokens_covered_without_truncation"] = True
    validation["unique_composition_keys"] = persisted.get_column("composition_key").n_unique()
    validation["holdout_rows"] = 0
    validation["target_columns"] = sorted(FORBIDDEN_INPUT_COLUMNS & set(persisted.columns))
    matrix = _embedding_matrix(persisted)
    dimension_diagnostics = _dimension_diagnostics(matrix)
    similarity = _similarity_diagnostics(matrix, config)
    pca_composition = _pca_metrics(matrix)
    unique_indices = (
        persisted.unique(subset=["lyrics_sha256"], keep="first")
        .get_column("composition_key")
        .to_list()
    )
    unique_matrix = _embedding_matrix(
        persisted.filter(pl.col("composition_key").is_in(unique_indices))
    )
    pca_unique = _pca_metrics(unique_matrix)
    unique_comparison = (
        "idêntica, pois não foram observados hashes duplicados"
        if unique_matrix.shape[0] == matrix.shape[0]
        else {
            "composition_rows": matrix.shape[0],
            "unique_hash_rows": unique_matrix.shape[0],
            "unique_hash_components_for_80_percent": pca_unique["components_for_80_percent"],
            "unique_hash_effective_rank": pca_unique["effective_rank"],
        }
    )
    collapse = (
        "possível sinal de colapso; revisar antes da modelagem"
        if similarity["std"] is not None
        and (
            float(similarity["std"]) < 0.02
            or dimension_diagnostics["near_constant_dimensions_std_le_1e_6"]
            > int(config["model"]["embedding_dimension"]) * 0.10
            or pca_composition["effective_rank"] < 5
        )
        else "nenhum sinal agregado de colapso"
    )
    private_git = _git_private_files()
    if private_git["tracked"] or private_git["staged"]:
        raise AssertionError("Arquivo privado tracked ou staged.")
    frozen_after = _file_hashes(frozen_paths)
    if frozen_before != frozen_after:
        raise AssertionError("Base v0.1.1 ou split foi alterado.")
    environment = {
        "python": platform.python_version(),
        "sentence_transformers": _package_version("sentence-transformers"),
        "transformers": _package_version("transformers"),
        "torch": _package_version("torch"),
        "langid": _package_version("langid"),
        "numpy": _package_version("numpy"),
        "tokenizers": _package_version("tokenizers"),
        "operating_system": platform.platform(),
        "device": str(model.device),
        "dtype": str(config["execution"]["dtype"]),
        "language_detector": f"langid {_package_version('langid')}",
    }
    model_metadata = {
        "id": config["model"]["id"],
        "revision": config["model"]["revision"],
        "license": config["model"]["license"],
        "tokenizer_class": tokenizer.__class__.__name__,
        "tokenizer_id": config["model"]["id"],
        "maximum_tokens_including_special": int(
            config["model"]["maximum_tokens_including_special"]
        ),
        "embedding_dimension": int(config["model"]["embedding_dimension"]),
        "fine_tuned": False,
    }
    parameters = {
        "seed": seed,
        "batch_size": int(config["execution"]["batch_size"]),
        "overlap_content_tokens": int(config["execution"]["overlap_content_tokens"]),
        "language_confidence_threshold": float(
            config["execution"]["language_confidence_threshold"]
        ),
        "model_eval": True,
        "torch_inference_mode": True,
        "deterministic_algorithms_warn_only": True,
        "chunk_embedding_l2_normalized": True,
        "final_embedding_l2_normalized": True,
    }
    summary: dict[str, Any] = {
        "status": "complete",
        "protocol_version": PROTOCOL_VERSION,
        "timestamp": utc_now(),
        "checkpoint_commit": config["checkpoint_commit"],
        "checkpoint_tag": config["checkpoint_tag"],
        "execution_git_head": git_commit(),
        "model": model_metadata,
        "environment": environment,
        "parameters": parameters,
        "input_dataset_fingerprint": fingerprint,
        "text_audit": text_audit,
        "numeric_validation": validation,
        "dimension_diagnostics": dimension_diagnostics,
        "similarity": similarity,
        "collapse_diagnosis": collapse,
        "pca_exploratory": {
            "by_composition": pca_composition,
            "by_unique_hash": pca_unique,
            "unique_hash_comparison": unique_comparison,
            "definitive_pca_saved": False,
        },
        "timing": {
            "embedding_generation_seconds": round(generation_seconds, 6),
            "total_seconds": round(time.perf_counter() - started, 6),
        },
        "privacy": {
            "holdout_accessed": False,
            "target_provided_to_encoder": False,
            "public_artifacts_contain_text": False,
            "tracked_private_files": private_git["tracked"],
            "staged_private_files": private_git["staged"],
            "private_embedding_rows": frame.height,
            "private_index_rows": index.height,
        },
        "frozen_hashes_before": frozen_before,
        "frozen_hashes_after": frozen_after,
        "frozen_hashes_preserved": frozen_before == frozen_after,
        "recommendation": "executar modelagem piloto",
        "failures": [],
    }
    if not public_payload_is_aggregate(summary):
        raise AssertionError("Resumo público contém chave ou caminho privado proibido.")
    manifest = {
        key: summary[key]
        for key in (
            "protocol_version",
            "checkpoint_commit",
            "checkpoint_tag",
            "model",
            "environment",
            "parameters",
            "text_audit",
            "numeric_validation",
            "dimension_diagnostics",
            "similarity",
            "collapse_diagnosis",
            "pca_exploratory",
            "privacy",
            "frozen_hashes_preserved",
            "recommendation",
        )
    }
    if not public_payload_is_aggregate(manifest):
        raise AssertionError("Manifesto público contém informação privada proibida.")
    _write_text(config["outputs"]["audit"], _audit_report(summary))
    _write_text(config["outputs"]["pca"], _pca_report(summary))
    write_json(config["outputs"]["manifest"], manifest)
    public_outputs = [
        config["outputs"]["manifest"],
        config["outputs"]["audit"],
        config["outputs"]["pca"],
    ]
    summary["public_output_hashes"] = _file_hashes(public_outputs)
    summary["private_output_hashes"] = _file_hashes(
        [config["outputs"]["embeddings"], config["outputs"]["index"]]
    )
    write_json(config["outputs"]["run_summary"], summary)
    return summary


def record_embeddings_verification_v020(
    verification: Mapping[str, Any], config_path: str | Path = DEFAULT_CONFIG_PATH
) -> dict[str, Any]:
    config = load_yaml(config_path)
    summary = read_json(config["outputs"]["run_summary"], {})
    if summary.get("status") != "complete":
        raise RuntimeError("Resumo completo de embeddings v0.2 não disponível.")
    summary["verification"] = dict(verification)
    manifest = read_json(config["outputs"]["manifest"], {})
    manifest["verification"] = dict(verification)
    write_json(config["outputs"]["manifest"], manifest)
    marker = "\n## Validação final\n"
    for key in ("audit", "pca"):
        path = project_path(config["outputs"][key])
        current = path.read_text(encoding="utf-8").split(marker, 1)[0]
        appendix = (
            marker
            + "\n"
            + _markdown_table(verification.get("commands", []), ["command", "exit_code", "result"])
        )
        _write_text(path, current + appendix + "\n")
    summary["public_output_hashes"] = _file_hashes(
        [config["outputs"][key] for key in ("manifest", "audit", "pca")]
    )
    write_json(config["outputs"]["run_summary"], summary)
    return summary
