"""Reconcile v0.4 using private metadata; emit aggregate evidence only."""

from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import polars as pl

from tcc_music_popularity.config import load_yaml, project_path
from tcc_music_popularity.io import read_json, sha256_file, utc_now, write_json
from tcc_music_popularity.lyrics_scale_v040 import audit_public_scale_outputs


def reconcile() -> dict:
    config = load_yaml("configs/final_scale_v0_4.yaml")
    summary = read_json(config["public_outputs"]["scale_summary"])
    integrity = read_json(config["private_outputs"]["integrity_manifest"])
    protocol = read_json(config["public_outputs"]["protocol_summary"])
    assert summary["status"] == "complete"
    for path, expected in summary["frozen_hashes"].items():
        assert sha256_file(project_path(path)) == expected
    for name, expected in integrity["private_artifact_hashes"].items():
        assert sha256_file(project_path(config["private_outputs"][name])) == expected
    frames = [
        pl.read_parquet(project_path(config["private_outputs"][name]))
        for name in ("embeddings_development", "embeddings_holdout")
    ]
    combined = pl.concat(frames)
    unique = combined.unique("lyrics_sha256", maintain_order=True)
    pilot = pl.read_parquet(
        project_path(config["inputs"]["pilot_embeddings"]),
        columns=["lyrics_sha256", "model_revision"],
    ).filter(pl.col("model_revision") == config["model"]["revision"])
    reused = unique.filter(pl.col("lyrics_sha256").is_in(pilot["lyrics_sha256"].to_list()))
    generated = unique.filter(~pl.col("lyrics_sha256").is_in(pilot["lyrics_sha256"].to_list()))
    result = pl.read_parquet(
        project_path(config["private_outputs"]["collection_results"]),
        columns=["final_status", "technical_error", "http_status"],
    )
    technical = result["technical_error"].drop_nulls().len()
    errors = result.filter(pl.col("final_status") == "request_error")
    lookup = pl.read_parquet(
        project_path(config["private_outputs"]["lookup"]),
        columns=["composition_key", "representative_track_id", "split"],
    )
    grouping = pl.read_parquet(
        project_path(config["inputs"]["modeling_base"]),
        columns=["track_id", "artist_group_id"],
    ).rename({"track_id": "representative_track_id"})
    lookup = lookup.join(grouping, on="representative_track_id", how="left", validate="1:1")
    joined = combined.select("composition_key", "track_id").join(
        lookup, on="composition_key", how="left", validate="1:1"
    )
    assert joined.height == 10240 and joined["artist_group_id"].null_count() == 0
    assert (joined["track_id"] == joined["representative_track_id"]).all()
    dev = joined.filter(pl.col("split") == "development_train")
    hold = joined.filter(pl.col("split") == "holdout_test")
    matrix = np.asarray(combined["embedding"].to_list(), dtype=np.float32)
    chunks_all = int(combined["chunk_count"].sum())
    chunks_unique = int(unique["chunk_count"].sum())
    encoded_chunks = int(generated["chunk_count"].sum())
    assert encoded_chunks == 17593
    started = datetime.fromisoformat(summary["network"]["first_request_at"])
    consolidated = datetime.fromisoformat(summary["timestamp"])
    out = {
        "verified_at": utc_now(),
        "technical_error_exceptions": technical,
        "request_error_final_outcomes": errors.height,
        "request_error_http_patterns": errors.group_by("http_status")
        .len()
        .sort("http_status")
        .to_dicts(),
        "composition_chunks_total": chunks_all,
        "unique_hash_chunks_total": chunks_unique,
        "duplicate_composition_chunks": chunks_all - chunks_unique,
        "pilot_reused_unique_hash_chunks": int(reused["chunk_count"].sum()),
        "chunks_actually_encoded": encoded_chunks,
        "composition_chunk_mean": chunks_all / combined.height,
        "collection_wall_seconds_until_consolidated": (consolidated - started).total_seconds(),
        "last_idempotent_consolidation_seconds": summary["duration_seconds"],
        "development_rows": dev.height,
        "holdout_rows": hold.height,
        "artist_overlap": len(set(dev["artist_group_id"]) & set(hold["artist_group_id"])),
        "composition_overlap": len(set(dev["composition_key"]) & set(hold["composition_key"])),
        "lyrics_hash_overlap": len(
            set(frames[0]["lyrics_sha256"]) & set(frames[1]["lyrics_sha256"])
        ),
        "nan_count": int(np.isnan(matrix).sum()),
        "infinite_count": int(np.isinf(matrix).sum()),
        "hashes_match": True,
        "holdout_target_loaded": False,
        "cohort_hash": protocol["private_artifact_hashes"]["cohort_sha256"],
        "reserve_hash": protocol["private_artifact_hashes"]["reserve_sha256"],
    }
    write_json("reports/cohort_reconciliation_v0_4.json", out)
    text = f"""# Reconciliação documental da coorte final v0.4

Esta nota acrescenta evidências aos registros originais, preservados integralmente.

`technical_errors` conta resultados com `technical_error` não nulo. O campo vem de `_safe_attempt_error` (lyrics_pilot.py), que registra exceções com `error_type` nas tentativas; não conta respostas HTTP de erro. Foram {technical} exceções registradas e {errors.height} resultados finais `request_error`. Os padrões HTTP desses resultados constam no JSON agregado anexo. Uma resposta HTTP 503 pode resultar em `request_error` sem exceção de transporte; os dois contadores medem eventos diferentes.

O total de chunks somado por composição é {chunks_all}, isto é, {out["composition_chunk_mean"]} × 10240. Há {chunks_unique} chunks por hash único; {out["duplicate_composition_chunks"]} chunks pertencem a composições adicionais com texto normalizado idêntico. Dos chunks únicos, {out["pilot_reused_unique_hash_chunks"]} correspondem a vetores do piloto reutilizados e {encoded_chunks} foram efetivamente codificados na v0.4. A função `_encode_unique_records` deduplica por hash antes de codificar. Portanto, 17.593 é a codificação nova, não a soma por composição.

O intervalo de parede da primeira requisição até a consolidação final foi {out["collection_wall_seconds_until_consolidated"]:.3f} s; inclui execução, pausas, retomadas e consolidação. O campo original `duration_seconds={summary["duration_seconds"]:.3f}` mede somente a última chamada idempotente de consolidação, não toda a coleta nem tempo ativo acumulado. Não há registro suficiente para reconstruir exatamente todo o tempo ativo acumulado.

Auditoria: desenvolvimento {dev.height}, holdout {hold.height}; artistas compartilhados {out["artist_overlap"]}; composições compartilhadas {out["composition_overlap"]}; hashes normalizados de letras compartilhados {out["lyrics_hash_overlap"]}. Representantes correspondem integralmente ao lookup congelado. Hashes de base, split e oito artefatos privados conferem; NaN {out["nan_count"]}; infinito {out["infinite_count"]}. Nenhum alvo do holdout foi carregado.
"""
    project_path("reports/cohort_reconciliation_v0_4.md").write_text(text, encoding="utf-8")
    audit_public_scale_outputs(
        [
            "reports/lyrics_scale_report_v0_4.md",
            "reports/embeddings_scale_report_v0_4.md",
            "reports/run_summary_scale_v0_4.json",
            "reports/cohort_reconciliation_v0_4.json",
            "reports/cohort_reconciliation_v0_4.md",
        ]
    )
    return out


if __name__ == "__main__":
    print(json.dumps(reconcile(), ensure_ascii=False, indent=2))
