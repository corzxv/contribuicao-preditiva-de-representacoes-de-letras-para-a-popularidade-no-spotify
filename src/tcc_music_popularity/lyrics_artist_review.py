"""Registra vínculos pontuais com grafia de artista revisada em catálogos."""

import json
from collections import Counter
from contextlib import closing
from pathlib import Path

import polars as pl

from . import lyrics_synced_revision as synced
from . import native_lookup_audit as audit
from .manual_lyrics import atomic_frame, atomic_json, exclusive, fingerprint, meta_get, require

local, design, revision, recovery = synced.local, synced.design, synced.revision, synced.recovery
VERSION = "nova-amostra-grafia-artista-revisada-v1"
WORKSPACE = design.ROOT / "data/derived/private_revisao_variantes_artista_nova_amostra_v1"
OUTPUT = design.ROOT / "reports/revisao_variantes_artista_nova_amostra_v1"
TARGET = "json_extract(result,'$.diagnostic_label')='artist_key_variant'"


def retrieve(db, query, candidate):
    require(audit.metadata_flags(query, candidate)["artist_key_variant"], "Grafia fora da ficha.")
    original = db.execute(
        "SELECT name,artist_name,album_name,duration,last_lyrics_id FROM tracks WHERE id=?",
        (candidate["id"],),
    ).fetchone()
    require(
        original is not None
        and tuple(original)
        == tuple(
            candidate[k]
            for k in ("name", "artist_name", "album_name", "duration", "last_lyrics_id")
        ),
        "Metadados divergem da ficha.",
    )
    require(
        candidate["last_lyrics_id"] is not None
        and abs(query["duration_seconds"] - candidate["duration"]) <= 1.0
        and not recovery.profile(candidate["artist_name"], candidate["name"])["credit_conflict"],
        "Ficha fora dos critérios de duração, crédito ou referência textual.",
    )
    source = db.execute(
        "SELECT track_id,plain_lyrics,synced_lyrics,instrumental FROM lyrics WHERE id=?",
        (candidate["last_lyrics_id"],),
    ).fetchone()
    require(source is not None and source[0] == candidate["id"], "Letra fora da ficha.")
    require(
        sum(len(text or "") for text in source[1:3]) <= recovery.local.MAX_TEXT_CHARACTERS,
        "Texto acima do limite.",
    )
    return {
        "id": candidate["id"],
        "trackName": candidate["name"],
        # A grafia alternativa vale somente para o par registrado na ficha.
        "artistName": query["artist_name_query"],
        "albumName": candidate["album_name"],
        "duration": candidate["duration"],
        "plainLyrics": source[1],
        "syncedLyrics": source[2],
        "instrumental": bool(source[3]),
        "local_lyrics_id": candidate["last_lyrics_id"],
    }


def review_text(query, candidates):
    require(all(revision.compatible(query, c) for c in candidates), "Crédito ou versão divergente.")
    status, lyric = revision.classify(query, candidates)
    if status["reason"] == "plain_synced_conflict":
        status, lyric = synced.compare_synced(query, candidates)
    elif status["reason"] == "substantively_distinct_texts":
        status, lyric = synced.case.compare_case(query, candidates, None)
    if lyric is None:
        return status.get("outcome", status.get("reason")), None
    original = next(c for c in candidates if c["id"] == lyric["lrclib_id"])
    return "accepted_after_catalog_review", {
        "accepted_text": lyric.get("accepted_text", lyric["plain_text_source"]),
        "plain_text_source": original["plainLyrics"],
        "synced_text_source": original["syncedLyrics"],
        "lrclib_id": original["id"],
        "lrclib_lyrics_id": original["local_lyrics_id"],
        "text_sha256": lyric["text_sha256"],
        "strict_text_sha256": lyric["strict_text_sha256"],
        "rules_version": VERSION,
    }


def run():
    decisions_path = WORKSPACE / "revisao_documental.json"
    previous_path = synced.OUTPUT / "resumo_revisao_caixa_plain_lrc.json"
    audit_path = audit.OUTPUT / "resumo_diagnostico_chaves.json"
    previous, diagnosis = map(design.read_json, (previous_path, audit_path))
    state43 = revision.WORKSPACE / "state.sqlite"
    identity = recovery.local.checked_dump(local.DUMP)
    require(
        previous["completed"]
        and diagnosis["completed"]
        and identity == previous["seal"]["dump"] == diagnosis["seal"]["dump"]
        and design.sha256(state43)
        == previous["seal"]["source43_state_sha256"]
        == diagnosis["seal"]["state43_sha256"],
        "A origem diverge das etapas 44 e 47.",
    )
    with (
        exclusive(WORKSPACE),
        closing(local.base.stable_readonly(audit.WORKSPACE / "state.sqlite")) as triage,
        closing(local.base.stable_readonly(state43)) as old,
        closing(local.base.stable_readonly(local.DUMP)) as dump,
    ):
        require(meta_get(triage, "seal") == diagnosis["seal"], "Checkpoint 44 divergente.")
        records = design.read_json(decisions_path)
        by_query = {r["query_id"]: r for r in records}
        targets = triage.execute(
            f"SELECT query_id,data,result FROM diagnostics WHERE {TARGET} ORDER BY query_id"
        ).fetchall()
        require(
            len(records)
            == len(targets)
            == len(by_query)
            == diagnosis["diagnostic_counts"]["artist_key_variant"]
            and set(by_query) == {r[0] for r in targets},
            "Fichas documentais não correspondem aos casos auditados.",
        )
        outcomes, texts, links = [], [], []
        for key, raw_query, raw_result in targets:
            review = by_query[key]
            approved = set(review["approved_candidate_ids"])
            outcome = "catalog_review_inconclusive"
            if approved:
                q = json.loads(raw_query)
                data, status = old.execute(
                    "SELECT data,status FROM queries WHERE query_id=?", (key,)
                ).fetchone()
                require(
                    fingerprint(q) == key and q == json.loads(data) and status == "not_found",
                    "Consulta de origem divergente.",
                )
                tracks = [
                    r[0]
                    for r in old.execute("SELECT track_id FROM tracks WHERE query_id=?", (key,))
                ]
                require(
                    tracks
                    and review["catalog_source"].startswith("https://")
                    and review["spotify_source"]
                    in {f"https://open.spotify.com/track/{t}" for t in tracks},
                    "Falta evidência de catálogo para a faixa sorteada.",
                )
                result = json.loads(raw_result)
                candidates = [c for c in result["candidates"] if c["id"] in approved]
                require(
                    not result["incomplete_methods"]
                    and result["candidate_records_saved"] == result["candidate_count_union_capped"]
                    and {c["id"] for c in candidates} == approved,
                    "Fichas ou candidatos incompletos.",
                )
                outcome, lyric = review_text(q, [retrieve(dump, q, c) for c in candidates])
                if lyric:
                    texts.append({"query_id": key, **lyric})
                    links.extend({"track_id": track, "query_id": key} for track in tracks)
            outcomes.append({"query_id": key, "outcome": outcome})

        atomic_json(WORKSPACE / "desfechos.json", outcomes)
        atomic_frame(
            WORKSPACE / "novas_letras_aceitas.parquet",
            pl.DataFrame(texts, schema=synced.LYRIC_SCHEMA),
        )
        atomic_frame(
            WORKSPACE / "novos_vinculos.parquet",
            pl.DataFrame(links, schema={"track_id": pl.String, "query_id": pl.String}),
        )
        report = {
            "completed": True,
            "targets": len(targets),
            "outcomes": dict(Counter(row["outcome"] for row in outcomes)),
            "new_accepted_tracks": len(links),
            "new_accepted_queries": len(texts),
            "accepted_tracks_with_overlays": previous["accepted_tracks_with_overlays"] + len(links),
            "seal": {
                "version": VERSION,
                "code_sha256": design.sha256(Path(__file__)),
                "source44_summary_sha256": design.sha256(audit_path),
                "source47_summary_sha256": design.sha256(previous_path),
                "source43_state_sha256": design.sha256(state43),
                "dump": identity,
            },
            "private_sha256": {
                name: design.sha256(WORKSPACE / name)
                for name in (
                    "revisao_documental.json",
                    "desfechos.json",
                    "novas_letras_aceitas.parquet",
                    "novos_vinculos.parquet",
                )
            },
        }
        atomic_json(OUTPUT / "resumo_revisao_variantes_artista.json", report)
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "completed",
                    "targets",
                    "new_accepted_tracks",
                    "accepted_tracks_with_overlays",
                )
            }
        )
    )
    return report
