"""Encoder multilingue offline, teste limitado e escala manual com checkpoint."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import sqlite3
import sys
import time
from contextlib import closing
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from . import sample_lyrics as base
from .lyrics_embeddings_v020 import (
    build_token_chunks,
    normalize_lyrics_text,
    weighted_chunk_aggregate,
)
from .manual_embeddings import checked_vector, read_vector, save_vector
from .manual_lyrics import (
    atomic_frame,
    atomic_json,
    exclusive,
    fingerprint,
    meta_get,
    meta_put,
    require,
)

MODEL = "intfloat/multilingual-e5-small"
REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
FILES = (
    "config.json",
    "model.safetensors",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "README.md",
)
ROOT = base.ROOT
CACHE = ROOT / "data/raw/lyrics_private/huggingface_cache"
WORKSPACE = ROOT / "data/derived/private_embeddings_200k_v1"
OUTPUT = ROOT / "reports/embeddings_multilingues_200k_v1"
DESCRIPTORS = ROOT / "data/derived/private_text_descriptors_200k_v1"
TEXTS = ROOT / "data/derived/private_sample_lyrics_200k_v2/letras_aceitas_200k.parquet"
REPORT = ROOT / "reports/descritores_textuais_200k_v1/resumo_descritores.json"
PROTOCOL = ROOT / "docs/protocolo_embeddings_multilingues_200k_v1.md"
SETTINGS = {
    "model": MODEL,
    "revision": REVISION,
    "dimension": 384,
    "max_length": 512,
    "prefix": "query: ",
    "overlap": 32,
    "dtype": "float32",
    "device": "cpu",
    "seed": 20261101,
    "pooling": "masked_mean_then_L2_per_chunk; new_content_token_weighted_mean_then_L2",
}


def versions():
    return {
        "python": sys.version,
        **{
            name: importlib.metadata.version(name)
            for name in (
                "torch",
                "transformers",
                "huggingface-hub",
                "safetensors",
                "tokenizers",
                "numpy",
            )
        },
    }


def download(cache=CACHE, workspace=WORKSPACE):
    """Única entrada com rede: somente arquivos do modelo, nunca letras."""
    from huggingface_hub import snapshot_download

    print(
        f"Baixando/verificando {MODEL}@{REVISION}; pesos safetensors e tokenizer, sem ONNX/bin...",
        flush=True,
    )
    with exclusive(workspace):
        path = Path(
            snapshot_download(
                repo_id=MODEL,
                revision=REVISION,
                cache_dir=cache,
                allow_patterns=list(FILES),
                max_workers=2,
            )
        )
        require(path.name == REVISION, "Snapshot não corresponde à revisão congelada.")
        require(all((path / name).is_file() for name in FILES), "Snapshot incompleto.")
        manifest = {
            "model": MODEL,
            "revision": REVISION,
            "snapshot": str(path.resolve()),
            "files": {name: base.sha256(path / name) for name in FILES},
            "license_declared": "MIT",
        }
        destination = workspace / "snapshot.json"
        if destination.exists():
            require(
                json.loads(destination.read_text(encoding="utf-8")) == manifest,
                "Snapshot existente diferente; preservar e revisar.",
            )
        else:
            atomic_json(destination, manifest)
    print("Snapshot local selado. Próxima etapa: smoke; nenhuma letra foi processada.", flush=True)


def checked_snapshot(workspace):
    path = workspace / "snapshot.json"
    require(path.is_file(), "Execute primeiro o modo download para preparar o snapshot local.")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    require(
        manifest["model"] == MODEL
        and manifest["revision"] == REVISION
        and set(manifest["files"]) == set(FILES),
        "Manifesto de outro encoder/revisão.",
    )
    snapshot = Path(manifest["snapshot"])
    require(snapshot.name == REVISION, "Nome da revisão local incompatível.")
    for name, digest in manifest["files"].items():
        require(
            (snapshot / name).is_file() and base.sha256(snapshot / name) == digest,
            "Arquivo do snapshot ausente/alterado.",
        )
    return snapshot, manifest


class OfflineEncoder:
    def __init__(self, snapshot, threads=2):
        import torch
        from transformers import AutoModel, AutoTokenizer

        torch.set_num_threads(threads)
        torch.manual_seed(SETTINGS["seed"])
        torch.use_deterministic_algorithms(True)
        self.torch = torch
        # tokenizer.json permite o tokenizer fast sem instalar sentencepiece.
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(snapshot), use_fast=True, local_files_only=True, trust_remote_code=False
        )
        require(
            self.tokenizer.is_fast,
            "Exigir tokenizer fast local; não instalar fallback automaticamente.",
        )
        self.model = AutoModel.from_pretrained(
            str(snapshot), local_files_only=True, trust_remote_code=False, use_safetensors=True
        ).to(device="cpu", dtype=torch.float32)
        self.model.eval()
        require(
            self.model.config.hidden_size == 384
            and self.model.config.max_position_embeddings >= 512,
            "Dimensão/contexto do encoder incompatíveis.",
        )

    def forward(self, inputs):
        torch, tokenizer = self.torch, self.tokenizer
        batch = tokenizer.pad(
            {"input_ids": inputs}, padding=True, return_attention_mask=True, return_tensors="pt"
        )
        require(batch["input_ids"].shape[1] <= 512, "Tokenização excedeu o limite; não truncar.")
        with torch.inference_mode():
            hidden = self.model(**batch).last_hidden_state
            mask = batch["attention_mask"].unsqueeze(-1).bool()
            pooled = hidden.masked_fill(~mask, 0).sum(dim=1) / mask.sum(dim=1)
            vectors = torch.nn.functional.normalize(pooled, p=2, dim=1)
        return vectors.cpu().numpy().astype(np.float32)


def encode_text(text, encoder, batch_size=8):
    """Nenhum metadado/alvo entra na representação. Cobrir todos os tokens."""
    require(isinstance(text, str) and bool(text.strip()), "Encoder recebe apenas texto não vazio.")
    require(batch_size > 0, "Batch size deve ser positivo.")
    tokenizer = encoder.tokenizer
    content = tokenizer.encode(text, add_special_tokens=False, truncation=False)
    prefix = tokenizer.encode(SETTINGS["prefix"], add_special_tokens=False, truncation=False)
    limit = SETTINGS["max_length"] - len(prefix) - tokenizer.num_special_tokens_to_add(pair=False)
    require(
        limit > SETTINGS["overlap"] and len(content) > 0,
        "Limite/prefixo/tokenização incompatíveis.",
    )
    chunks = build_token_chunks(content, content_limit=limit, overlap=SETTINGS["overlap"])
    vectors = []
    maximum = 0
    for start in range(0, len(chunks), batch_size):
        selected = chunks[start : start + batch_size]
        inputs = [
            tokenizer.build_inputs_with_special_tokens(prefix + c["token_ids"]) for c in selected
        ]
        maximum = max(maximum, max(map(len, inputs)))
        require(
            maximum <= SETTINGS["max_length"], "Truncamento proibido; preparar janelas menores."
        )
        result = np.asarray(encoder.forward(inputs), dtype=np.float32)
        require(result.shape == (len(inputs), 384), "Saída do encoder com dimensão inválida.")
        vectors.extend(checked_vector(row) for row in result)
    weights = [c["new_token_count"] for c in chunks]
    require(sum(weights) == len(content), "Cobertura/pesos dos tokens incompleta.")
    vector = checked_vector(weighted_chunk_aggregate(np.stack(vectors), weights))
    return vector, {
        "content_tokens": len(content),
        "chunks": len(chunks),
        "max_input_tokens": maximum,
        "prefix_tokens": len(prefix),
        "overlap": SETTINGS["overlap"],
        "token_weight_sum": sum(weights),
    }


def smoke_plan(metadata):
    unique = metadata.sort("track_id").unique("text_input_sha256", maintain_order=True)
    selected = []
    # 2 textos em cada um dos 8 idiomas estimados mais frequentes + extremos de extensão.
    groups = (
        unique.group_by("lyrics_detected_language")
        .len()
        .sort(["len", "lyrics_detected_language"], descending=[True, False])
        .head(8)
    )
    for code in groups["lyrics_detected_language"]:
        group = unique.filter(pl.col("lyrics_detected_language").eq_missing(code)).sort(
            "text_input_sha256"
        )
        selected += group.head(2)["text_input_sha256"].to_list()
    selected += (
        unique.sort(["text_characters", "text_input_sha256"], descending=[True, False])
        .head(3)["text_input_sha256"]
        .to_list()
    )
    selected += (
        unique.sort(["text_characters", "text_input_sha256"]).head(3)["text_input_sha256"].to_list()
    )
    selected += (
        unique.filter(pl.col("lyrics_language_status") == "uncertain")
        .sort("text_input_sha256")
        .head(2)["text_input_sha256"]
        .to_list()
    )
    return list(dict.fromkeys(selected))[:24]


def export_vectors(db, destination, cfg_sha, keys):
    schema = pa.schema(
        [
            ("text_input_sha256", pa.string()),
            ("embedding", pa.list_(pa.float32(), 384)),
            ("vector_sha256", pa.string()),
        ]
    )
    with pq.ParquetWriter(
        destination.with_suffix(".parquet.tmp"), schema, compression="zstd"
    ) as writer:
        batch = []
        for key in sorted(keys):
            row = db.execute("SELECT * FROM vectors WHERE lyrics_sha256=?", (key,)).fetchone()
            require(row is not None, "Vetor faltante na exportação.")
            vector = read_vector(row, cfg_sha)
            batch.append(
                {
                    "text_input_sha256": key,
                    "embedding": vector.tolist(),
                    "vector_sha256": row["vector_sha256"],
                }
            )
            if len(batch) == 256:
                writer.write_table(pa.Table.from_pylist(batch, schema=schema))
                batch = []
        if batch:
            writer.write_table(pa.Table.from_pylist(batch, schema=schema))
    destination.with_suffix(".parquet.tmp").replace(destination)


def run(
    mode,
    *,
    descriptors=DESCRIPTORS,
    texts=TEXTS,
    descriptor_report=REPORT,
    workspace=WORKSPACE,
    output=OUTPUT,
    batch_size=8,
    threads=2,
    limit=None,
    expected=77535,
    encoder=None,
    snapshot_info=None,
):
    require(mode in {"smoke", "all"} and threads > 0 and batch_size > 0, "Modo/recursos inválidos.")
    started = time.monotonic()
    require(
        workspace.resolve().is_relative_to(ROOT / "data/derived") or expected != 77535,
        "Workspace privado inválido.",
    )
    require(
        workspace.resolve() != descriptors.resolve()
        and not workspace.resolve().is_relative_to(descriptors.resolve())
        and output.resolve() != workspace.resolve(),
        "Destinos devem ser separados.",
    )
    print("[1/4] Verificando fontes e snapshot local; sem download de inferência...", flush=True)
    previous = json.loads(descriptor_report.read_text(encoding="utf-8"))
    require(
        previous["completed"] and previous["cohort_rows"] == expected,
        "Descritores não concluídos/incompatíveis.",
    )
    source_path = descriptors / "coorte_descritores.parquet"
    columns = [
        "track_id",
        "lyrics_text_ref",
        "text_input_sha256",
        "text_component_id",
        "text_characters",
        "lyrics_detected_language",
        "lyrics_language_status",
    ]
    metadata = pl.read_parquet(source_path, columns=columns)  # projeção sem popularidade/alvos
    require(
        metadata.height == metadata["track_id"].n_unique() == expected
        and metadata["text_input_sha256"].n_unique() == previous["unique_input_texts"],
        "Cardinalidade dos inputs incompatível.",
    )
    require(
        base.sha256(texts) == previous["seal"]["texts"],
        "Textos mudaram desde a geração de descritores.",
    )
    actual_snapshot, manifest = (
        checked_snapshot(workspace) if snapshot_info is None else snapshot_info
    )
    runtime = versions() if snapshot_info is None else {"synthetic": "1"}
    seal = {
        "settings": SETTINGS,
        "source_sha256": base.sha256(source_path),
        "descriptor_report": base.sha256(descriptor_report),
        "text_source": previous["seal"]["texts"],
        "snapshot": manifest,
        "versions": runtime,
        "code": {
            p.name: base.sha256(p)
            for p in [
                Path(__file__),
                PROTOCOL,
                Path(__file__).with_name("lyrics_embeddings_v020.py"),
                Path(__file__).with_name("manual_embeddings.py"),
            ]
        },
    }
    signature = fingerprint(seal)
    target_dir = output / ("smoke" if mode == "smoke" else "integral")
    owner = {"signature": signature}
    if target_dir.exists():
        require(
            (target_dir / "owner.json").is_file()
            and json.loads((target_dir / "owner.json").read_text()) == owner,
            "Pasta de outra execução; não sobrescrever.",
        )
    else:
        target_dir.mkdir(parents=True)
        atomic_json(target_dir / "owner.json", owner)
    with exclusive(workspace), closing(sqlite3.connect(workspace / "state.sqlite")) as db:
        db.row_factory = sqlite3.Row
        db.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        db.execute(
            "CREATE TABLE IF NOT EXISTS vectors(lyrics_sha256 TEXT PRIMARY KEY,config_sha256 TEXT NOT NULL,vector BLOB NOT NULL,vector_sha256 TEXT NOT NULL,metadata TEXT NOT NULL,origin TEXT NOT NULL)"
        )
        if meta_get(db, "seal") is None:
            with db:
                meta_put(db, "seal", seal)
        require(meta_get(db, "seal") == seal, "Checkpoint de outras fontes/encoder/configuração.")
        if mode == "all":
            require(
                meta_get(db, "smoke_verified", False),
                "Primeiro concluir e verificar smoke; escala não é iniciada automaticamente.",
            )
        else:
            with db:
                meta_put(db, "smoke_verified", False)
        keys = (
            smoke_plan(metadata)
            if mode == "smoke"
            else sorted(metadata["text_input_sha256"].unique().to_list())
        )
        wanted = set(keys)
        plan_path = workspace / "plano_smoke.json"
        if mode == "smoke":
            if plan_path.exists():
                require(json.loads(plan_path.read_text()) == keys, "Seleção smoke mudou.")
            else:
                atomic_json(plan_path, keys)
        summary = {
            "completed": False,
            "mode": mode,
            "settings": SETTINGS,
            "source_rows": expected,
            "requested_unique_texts": len(keys),
            "new_vectors": 0,
            "reused_vectors": 0,
            "versions": runtime,
            "snapshot_revision": REVISION,
            "seal_sha256": signature,
            "execution": {"batch_size": batch_size, "threads": threads},
            "splits_created": False,
            "predictive_models_trained": False,
        }
        atomic_json(target_dir / "resumo_embeddings.json", summary)
        pending = set()
        for key in wanted:
            stored = db.execute("SELECT * FROM vectors WHERE lyrics_sha256=?", (key,)).fetchone()
            if stored is None:
                pending.add(key)
            else:
                read_vector(stored, signature)
                summary["reused_vectors"] += 1
        print(
            f"[2/4] {len(pending)} textos pendentes, {summary['reused_vectors']} vetores reutilizados; modo {mode}...",
            flush=True,
        )
        engine = encoder
        seen_refs = set()
        last = 0.0
        first_text = None
        completed_keys = wanted - pending
        expected_refs = dict(metadata.select("lyrics_text_ref", "text_input_sha256").iter_rows())
        try:
            for batch in pq.ParquetFile(texts).iter_batches(
                batch_size=64, columns=["query_id", "accepted_text"]
            ):
                for row in batch.to_pylist():
                    require(
                        row["query_id"] not in seen_refs and row["query_id"] in expected_refs,
                        "Referência textual ausente/repetida.",
                    )
                    seen_refs.add(row["query_id"])
                    key = expected_refs[row["query_id"]]
                    if key not in wanted:
                        continue
                    text = normalize_lyrics_text(row["accepted_text"])
                    require(
                        hashlib.sha256(text.encode()).hexdigest() == key,
                        "Input textual diverge do usado nos descritores.",
                    )
                    if first_text is None:
                        first_text = (key, text)
                    if key not in pending:
                        continue
                    if limit is not None and summary["new_vectors"] >= limit:
                        break
                    if engine is None:
                        engine = OfflineEncoder(actual_snapshot, threads)
                    tick = time.monotonic()
                    vector, details = encode_text(text, engine, batch_size)
                    details["encode_seconds"] = time.monotonic() - tick
                    details.update(batch_size=batch_size, threads=threads)
                    with db:
                        save_vector(db, key, vector, signature, details, "multilingual_e5_frozen")
                    summary["new_vectors"] += 1
                    pending.remove(key)
                    completed_keys.add(key)
                    if time.monotonic() - last >= 10:
                        progress = {
                            "mode": mode,
                            "new_vectors": summary["new_vectors"],
                            "reused_vectors": summary["reused_vectors"],
                            "pending": len(pending),
                            "seconds": time.monotonic() - started,
                        }
                        atomic_json(workspace / "progress.json", progress)
                        print(json.dumps(progress), flush=True)
                        last = time.monotonic()
                else:
                    continue
                break
            if limit is None or summary["new_vectors"] < limit:
                require(seen_refs == set(expected_refs), "Textos privados/referências incompletos.")
            summary["completed"] = not pending
            if mode == "smoke" and summary["completed"]:
                require(first_text is not None, "Smoke sem texto de controle.")
                if engine is None:
                    engine = OfflineEncoder(actual_snapshot, threads)
                again, _ = encode_text(first_text[1], engine, batch_size)
                stored = db.execute(
                    "SELECT * FROM vectors WHERE lyrics_sha256=?", (first_text[0],)
                ).fetchone()
                difference = float(np.max(np.abs(again - read_vector(stored, signature))))
                require(difference <= 1e-5, "Reprodução do vetor de controle falhou.")
                summary["repeat_max_abs_difference"] = difference
                with db:
                    meta_put(db, "smoke_verified", True)
            print(
                "[3/4] Conferindo dimensão, finitude, L2 e exportando vetores privados...",
                flush=True,
            )
            export_vectors(
                db,
                workspace
                / ("embeddings_smoke.parquet" if mode == "smoke" else "embeddings.parquet"),
                signature,
                completed_keys,
            )
            selected_metadata = metadata.filter(
                pl.col("text_input_sha256").is_in(sorted(completed_keys))
            )
            if mode == "all" and summary["completed"]:
                require(
                    selected_metadata.height == expected, "Join das faixas ao embedding incompleto."
                )
            atomic_frame(
                workspace
                / ("indice_smoke.parquet" if mode == "smoke" else "indice_embeddings.parquet"),
                selected_metadata,
            )
            timings = [
                json.loads(r[0])
                for r in db.execute(
                    "SELECT metadata FROM vectors WHERE config_sha256=?", (signature,)
                )
            ]
            summary.update(
                private_index_rows=selected_metadata.height,
                dimension=384,
                chunks_saved=sum(r["chunks"] for r in timings),
                seconds_this_invocation=time.monotonic() - started,
                max_input_tokens=max((r["max_input_tokens"] for r in timings), default=0),
                unencoded_unique_texts=len(pending),
            )
            if mode == "smoke" and summary["completed"]:
                summary["rough_scale_encode_seconds"] = (
                    previous["unique_input_texts"]
                    * sum(r["encode_seconds"] for r in timings)
                    / len(timings)
                )
            atomic_json(target_dir / "resumo_embeddings.json", summary)
            (target_dir / "relatorio_embeddings.md").write_text(
                "# Embeddings multilingues\n\n"
                + f"Modo {mode}; concluído: {summary['completed']}; novos vetores {summary['new_vectors']}, reutilizados {summary['reused_vectors']}. Dimensão 384, tokens até {summary['max_input_tokens']}.\n\n"
                + "Teste técnico, não validação semântica ou ganho preditivo. Textos longos são cobertos por janelas, sem truncamento silencioso; pooling por tokens novos não elimina toda influência do overlap. Nenhuma faixa é excluída por idioma. Estimativa de escala, quando disponível, é grosseira: seleção dirigida de extremos/idiomas, aquecimento e cache afetam o tempo; não prevê duração total. Nenhum modelo preditivo, PCA ou split é ajustado.\n",
                encoding="utf-8",
            )
            print(
                f"[4/4] {'Concluído' if summary['completed'] else 'Parcial; retomar'}; agregados em {target_dir}",
                flush=True,
            )
            return 0 if summary["completed"] else 2
        except BaseException as exc:
            summary.update(
                completed=False,
                error_type=type(exc).__name__,
                seconds_this_invocation=time.monotonic() - started,
            )
            atomic_json(target_dir / "resumo_embeddings.json", summary)
            raise


def cli():
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["download", "smoke", "all"])
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--limit-texts", type=int)
    args = parser.parse_args()
    if args.mode == "download":
        download()
        return 0
    require(args.limit_texts is None or args.limit_texts > 0, "Limite deve ser positivo.")
    return run(args.mode, batch_size=args.batch_size, threads=args.threads, limit=args.limit_texts)
