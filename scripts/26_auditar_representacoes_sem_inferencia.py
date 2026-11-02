"""Auditoria limitada: oito letras/descritores, tokenizer local; nenhum forward E5."""

import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow.parquet as pq

from tcc_music_popularity import multilingual_embeddings as emb
from tcc_music_popularity import text_descriptors as desc
from tcc_music_popularity.closure_diagnostics import MAX_BYTES, digest
from tcc_music_popularity.manual_lyrics import atomic_json, fingerprint, meta_get, require

ROOT = emb.ROOT
OUTPUT = ROOT / "reports/fechamento_metodologico_200k_v1/auditoria_representacoes.json"


def run():
    started = time.monotonic()
    require(not OUTPUT.exists(), "Auditoria existente preservada.")
    original_files = [
        ROOT / "output/pdf/resultados_dominio_observado_200k_v1.pdf",
        ROOT / "reports/overleaf_dominio_observado_200k_v1.zip",
    ]
    originals = {str(p): digest(p) for p in original_files}
    descriptor_report = json.loads(emb.REPORT.read_text(encoding="utf-8"))
    embedding_report = json.loads(
        (emb.OUTPUT / "integral/resumo_embeddings.json").read_text(encoding="utf-8")
    )
    base_report = json.loads(
        (ROOT / "reports/base_modelagem_200k_v1/resumo_base_modelagem.json").read_text(
            encoding="utf-8"
        )
    )
    require(
        all(r["completed"] for r in (descriptor_report, embedding_report, base_report)),
        "Fonte incompleta.",
    )
    seal = descriptor_report["seal"]
    checked = {
        Path(desc.__file__): seal["code"],
        desc.PROTOCOL: seal["protocol"],
        Path(desc.__file__).with_name("lyrics_embeddings_v020.py"): seal["normalization"],
        Path(desc.__file__).with_name("normalization.py"): seal["metadata_normalization"],
    }
    database = emb.WORKSPACE / "state.sqlite"
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as db:
        encoder_seal = meta_get(db, "seal")
        smoke_verified = meta_get(db, "smoke_verified")
    require(
        smoke_verified and fingerprint(encoder_seal) == embedding_report["seal_sha256"],
        "Selo E5 divergente.",
    )
    for name, sha in encoder_seal["code"].items():
        path = emb.PROTOCOL if name.endswith(".md") else Path(emb.__file__).with_name(name)
        checked[path] = sha
    require(
        all(digest(p) == sha for p, sha in checked.items()), "Código/protocolo selado alterado."
    )
    manifest = json.loads((emb.WORKSPACE / "snapshot.json").read_text(encoding="utf-8"))
    require(
        manifest == encoder_seal["snapshot"] and encoder_seal["settings"] == emb.SETTINGS,
        "Snapshot/settings divergentes.",
    )
    snapshot = Path(manifest["snapshot"])
    small_files = {
        name: sha for name, sha in manifest["files"].items() if name != "model.safetensors"
    }
    require(
        all(digest(snapshot / name) == sha for name, sha in small_files.items()),
        "Config/tokenizer alterado.",
    )
    config = json.loads((snapshot / "config.json").read_text())
    require(
        config["hidden_size"] == 384 and config["max_position_embeddings"] >= 512,
        "Config inválida.",
    )
    # Apenas oito linhas textuais do primeiro lote. Não exportar texto/hash/IDs individuais.
    sample = next(
        pq.ParquetFile(emb.TEXTS).iter_batches(
            batch_size=8, columns=["query_id", "accepted_text", "text_sha256"]
        )
    ).to_pylist()
    require(
        len(sample) == 8 and sum(len(r["accepted_text"]) for r in sample) <= 100000,
        "Amostra excede limite leve.",
    )
    source = emb.DESCRIPTORS / "coorte_descritores.parquet"
    source_stat = (source.stat().st_size, source.stat().st_mtime_ns)
    columns = ["lyrics_text_ref", "text_input_sha256", *desc.FEATURES]
    metadata = pq.ParquetFile(source).metadata
    projected_bytes = sum(
        metadata.row_group(r).column(c).total_compressed_size
        for r in range(metadata.num_row_groups)
        for c in range(metadata.num_columns)
        if metadata.row_group(r).column(c).path_in_schema in columns
    )
    require(
        metadata.num_rows == 77535 and projected_bytes <= MAX_BYTES,
        "Projeção excede limite leve; ampliar somente em execução manual.",
    )
    # O arquivo completo também contém metadados; não reler tudo para rehash.
    # Conferir apenas a projeção pequena e a amostra textual; o hash integral é
    # evidência anterior da etapa 21, explicitamente identificado como tal.
    stored = pl.read_parquet(source, columns=columns)
    require(
        tuple(descriptor_report["features"]) == desc.FEATURES and len(desc.FEATURES) == 21,
        "Lista de features divergente.",
    )
    max_difference = 0.0
    for row in sample:
        text = row["accepted_text"]
        require(
            hashlib.sha256(text.encode()).hexdigest() == row["text_sha256"],
            "Hash original divergente na amostra.",
        )
        normalized = emb.normalize_lyrics_text(text)
        match = stored.filter(pl.col("lyrics_text_ref") == row["query_id"])
        require(
            match.height > 0 and match["text_input_sha256"].n_unique() == 1,
            "Vínculo ausente/divergente.",
        )
        require(
            match["text_input_sha256"][0] == hashlib.sha256(normalized.encode()).hexdigest(),
            "Input diverge do texto.",
        )
        recomputed = desc.descriptors(text)
        for feature, value in recomputed.items():
            difference = float(np.max(np.abs(match[feature].to_numpy() - value)))
            max_difference = max(max_difference, difference)
            require(difference <= 1e-10, "Descritor não reproduzido na amostra.")
    # Tokenizer real, somente frases artificiais; nenhum peso é carregado.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        str(snapshot), use_fast=True, local_files_only=True, trust_remote_code=False
    )
    probes = [
        "A calm morning.",
        "Uma manhã tranquila.",
        "Una mañana tranquila.",
        "صباح هادئ",
        "एक शांत सुबह",
        "静かな朝です",
        "宁静的早晨",
        "조용한 아침입니다",
        "  texto",
        "?!",
        "[Verse]\nSynthetic line",
    ]
    prefix = tokenizer.encode(emb.SETTINGS["prefix"], add_special_tokens=False)
    equal, synthetic_differences = [], []
    for text in probes:
        separate = prefix + tokenizer.encode(text, add_special_tokens=False)
        joint = tokenizer.encode(emb.SETTINGS["prefix"] + text, add_special_tokens=False)
        equal.append(separate == joint)
        if separate != joint:
            synthetic_differences.append(
                {
                    "synthetic_probe": text,
                    "separate_token_ids": separate,
                    "joint_token_ids": joint,
                    "separate_token_strings": tokenizer.convert_ids_to_tokens(separate),
                    "joint_token_strings": tokenizer.convert_ids_to_tokens(joint),
                    "separate_decoded": tokenizer.decode(separate),
                    "joint_decoded": tokenizer.decode(joint),
                }
            )
    sample_token_mismatches = 0
    for row in sample:
        text = emb.normalize_lyrics_text(row["accepted_text"])
        # Só compara tokenização; não gera janelas/modelo/vetor para essas letras.
        separate = prefix + tokenizer.encode(text, add_special_tokens=False, truncation=False)
        joint = tokenizer.encode(
            emb.SETTINGS["prefix"] + text, add_special_tokens=False, truncation=False
        )
        sample_token_mismatches += separate != joint
    limit = 512 - len(prefix) - tokenizer.num_special_tokens_to_add(pair=False)
    chunks = emb.build_token_chunks(list(range(2001)), content_limit=limit, overlap=32)
    max_tokens = max(
        len(tokenizer.build_inputs_with_special_tokens(prefix + c["token_ids"])) for c in chunks
    )
    require(
        sum(c["new_token_count"] for c in chunks) == 2001 and max_tokens <= 512,
        "Cobertura/limite divergente.",
    )
    require(originals == {str(p): digest(p) for p in original_files}, "PDF/ZIP parcial alterado.")
    require(
        source_stat == (source.stat().st_size, source.stat().st_mtime_ns),
        "Fonte alterada durante auditoria.",
    )
    result = {
        "completed": True,
        "descriptor_features": 21,
        "sample_texts_recomputed": len(sample),
        "sample_descriptor_max_abs_difference": max_difference,
        "descriptor_output_sha256_prior_stage21": base_report["seal"]["inputs"][
            str(source.resolve())
        ],
        "descriptor_output_full_rehash_this_audit": False,
        "descriptor_projection_compressed_bytes": projected_bytes,
        "descriptor_source_size_mtime_unchanged": True,
        "code_and_protocol_hashes_verified": {str(p): sha for p, sha in checked.items()},
        "encoder_revision": emb.REVISION,
        "encoder_settings_match_frozen_seal": True,
        "snapshot_small_files_hashes_verified": small_files,
        "weights_rehashed_this_audit": False,
        "weights_loaded": False,
        "weights_integrity_prior_evidence": "checked_snapshot at smoke/all, frozen seal; all stored vectors audited by stage 21",
        "prior_vector_audit": base_report["vectors"],
        "tokenizer_synthetic_probes": len(probes),
        "joint_and_separate_prefix_tokens_equal": all(equal),
        "synthetic_prefix_tokenization_differences": synthetic_differences,
        "sample_prefix_tokenization_mismatches": sample_token_mismatches,
        "prefix_tokens": len(prefix),
        "content_limit": limit,
        "synthetic_long_content_tokens": 2001,
        "synthetic_chunks": len(chunks),
        "max_input_tokens": max_tokens,
        "tokenizer_is_fast": tokenizer.is_fast,
        "models_trained": False,
        "embeddings_generated": False,
        "individual_outputs_written": False,
        "partial_artifact_hashes_unchanged": originals,
        "script_sha256": digest(Path(__file__)),
        "seconds": time.monotonic() - started,
    }
    atomic_json(OUTPUT, result)
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "completed",
                    "sample_texts_recomputed",
                    "sample_descriptor_max_abs_difference",
                    "tokenizer_synthetic_probes",
                    "max_input_tokens",
                    "seconds",
                )
            }
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
