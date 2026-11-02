"""Diagnóstico motivado pelo token extra: quatro frases artificiais, sem cache.

Nenhum texto do corpus, treinamento, vetor exportado ou alteração dos resultados.
Oito forwards unitários de sequências curtas, máximo 64 tokens, CPU/duas threads.
"""

import json
import time

import numpy as np

from tcc_music_popularity import multilingual_embeddings as emb
from tcc_music_popularity.closure_diagnostics import digest
from tcc_music_popularity.manual_lyrics import atomic_json, require


def run():
    started = time.monotonic()
    output = emb.ROOT / "reports/fechamento_metodologico_200k_v1/desvio_prefixo_sintetico.json"
    require(not output.exists(), "Diagnóstico já existente preservado.")
    protected_paths = [
        emb.ROOT / "output/pdf/resultados_dominio_observado_200k_v1.pdf",
        emb.ROOT / "reports/overleaf_dominio_observado_200k_v1.zip",
        emb.WORKSPACE / "state.sqlite",
    ]
    protected = {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in protected_paths}
    snapshot, manifest = emb.checked_snapshot(emb.WORKSPACE)
    engine = emb.OfflineEncoder(snapshot, threads=2)
    probes = ["A calm morning.", "Uma manhã tranquila.", "صباح هادئ", "宁静的早晨"]
    rows = []
    for text in probes:
        content = engine.tokenizer.encode(text, add_special_tokens=False)
        prefix = engine.tokenizer.encode(emb.SETTINGS["prefix"], add_special_tokens=False)
        separate = engine.tokenizer.build_inputs_with_special_tokens(prefix + content)
        joint = engine.tokenizer.encode(emb.SETTINGS["prefix"] + text, add_special_tokens=True)
        require(len(separate) <= 64 and len(joint) <= 64, "Limite diagnóstico excedido.")
        actual = engine.forward([separate])[0].astype(np.float64)
        canonical = engine.forward([joint])[0].astype(np.float64)
        cosine = float(
            np.dot(actual, canonical) / np.linalg.norm(actual) / np.linalg.norm(canonical)
        )
        rows.append(
            {
                "synthetic_text": text,
                "actual_input_tokens": len(separate),
                "canonical_input_tokens": len(joint),
                "cosine": cosine,
                "l2_distance": float(np.linalg.norm(actual - canonical)),
                "max_abs_coordinate_difference": float(np.max(np.abs(actual - canonical))),
            }
        )
    require(
        protected == {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in protected_paths},
        "Artefato protegido mudou.",
    )
    result = {
        "completed": True,
        "trigger": "extra_whitespace_token_when_prefix_is_encoded_separately",
        "synthetic_sentences": 4,
        "forward_calls": 8,
        "max_tokens_allowed": 64,
        "model": emb.MODEL,
        "revision": emb.REVISION,
        "snapshot_hashes_reverified_including_weights": manifest["files"],
        "synthetic_probe_results": rows,
        "corpus_texts_read": 0,
        "corpus_embeddings_generated": 0,
        "vectors_exported": 0,
        "models_trained": False,
        "predictive_impact_measured": False,
        "original_artifact_size_mtime_unchanged": protected,
        "script_sha256": digest(__file__),
        "seconds": time.monotonic() - started,
    }
    atomic_json(output, result)
    print(
        json.dumps(
            {
                "completed": True,
                "synthetic_sentences": 4,
                "cosine_min": min(r["cosine"] for r in rows),
                "cosine_max": max(r["cosine"] for r in rows),
                "seconds": result["seconds"],
            }
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
