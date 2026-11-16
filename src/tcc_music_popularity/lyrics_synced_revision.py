"""Revisão de caixa nos conflitos entre letra simples e sincronizada."""

import argparse
import json
import time
from collections import Counter
from contextlib import closing
from hashlib import sha256
from pathlib import Path

import polars as pl

from . import lyrics_case_revision as case
from .manual_lyrics import atomic_frame, atomic_json, exclusive, fingerprint, require

revision = case.revision
local = case.local
recovery = local.recovery
design = case.design
VERSION = "nova-amostra-caixa-plain-lrc-v1"
WORKSPACE = design.ROOT / "data/derived/private_revisao_caixa_plain_lrc_nova_amostra_v1"
OUTPUT = design.ROOT / "reports/revisao_caixa_plain_lrc_nova_amostra_v1"
TARGET = "q.status='ambiguous' AND json_extract(q.result,'$.reason')='plain_synced_conflict'"
LYRIC_SCHEMA = {
    "query_id": pl.String,
    "accepted_text": pl.String,
    "plain_text_source": pl.String,
    "synced_text_source": pl.String,
    "lrclib_id": pl.Int64,
    "lrclib_lyrics_id": pl.Int64,
    "text_sha256": pl.String,
    "strict_text_sha256": pl.String,
    "rules_version": pl.String,
}


def case_signature(text):
    return recovery.typography_hash(" ".join(text.lower().split()))


def compare_synced(query, candidates):
    baseline, _ = revision.classify(query, candidates)
    require(baseline["reason"] == "plain_synced_conflict", "Conflito 43 não reproduzido.")
    views, resolved = [], []
    originals = {c["id"]: c for c in candidates}
    for candidate in candidates:
        view = dict(candidate)
        plain, synced = view["plainLyrics"], view["syncedLyrics"]
        if revision.compatible(query, view) and plain and plain.strip() and synced:
            text, error = recovery.synced_text(synced)
            if (
                error is None
                and not revision.whitespace_equal(plain, text)
                and case_signature(plain) == case_signature(text)
            ):
                view["syncedLyrics"] = None
                resolved.append(view["id"])
        views.append(view)

    result, lyric = revision.classify(query, views)
    evidence = {"resolved_plain_lrc_ids": sorted(set(resolved)), "outcome": result["reason"]}
    if result["reason"] == "substantively_distinct_texts":
        compared, lyric = case.compare_case(query, views, None)
        evidence.update(compared)
    if lyric is None:
        return evidence, None

    require(bool(resolved), "Aceitação sem resolução do conflito plain/LRC.")
    source = originals[lyric["lrclib_id"]]
    text = lyric.get("accepted_text", lyric["plain_text_source"])
    evidence.update(
        outcome="accepted_plain_lrc_case_equivalent",
        selected_lrclib_id=source["id"],
        comparison_sha256=case_signature(text),
        equivalent_candidate_ids=lyric.get(
            "equivalent_lrclib_ids", evidence.get("equivalent_candidate_ids")
        ),
    )
    return evidence, {
        "accepted_text": text,
        "plain_text_source": source["plainLyrics"],
        "synced_text_source": source["syncedLyrics"],
        "lrclib_id": source["id"],
        "lrclib_lyrics_id": source["local_lyrics_id"],
        "text_sha256": lyric["text_sha256"],
        "strict_text_sha256": lyric["strict_text_sha256"],
        "rules_version": VERSION,
    }


def restore_candidates(db, evidence):
    records = evidence["candidates_metadata"]
    require(
        not evidence["incomplete_reason"]
        and 0 < len(records) <= recovery.local.MAX_CANDIDATES
        and len({c["id"] for c in records}) == len(records),
        "Evidência 43 incompleta.",
    )
    total = 0
    for candidate in records:
        size = candidate["plainLyrics_characters"] + candidate["syncedLyrics_characters"]
        total += size
        require(
            size <= recovery.local.MAX_TEXT_CHARACTERS
            and total <= recovery.local.MAX_TOTAL_CHARACTERS,
            "Evidência acima do limite textual.",
        )
        if not revision.compatible(evidence["query"], candidate):
            continue
        key = candidate["local_lyrics_id"]
        row = (candidate["id"], None, None, False)
        if key is not None:
            row = db.execute(
                "SELECT track_id,plain_lyrics,synced_lyrics,instrumental FROM lyrics WHERE id=?",
                (key,),
            ).fetchone()
        require(
            row is not None
            and row[0] == candidate["id"]
            and bool(row[3]) == candidate["instrumental"],
            "Referência LRCLIB inconsistente.",
        )
        restored = dict(candidate)
        for name, value in zip(("plainLyrics", "syncedLyrics"), row[1:3], strict=True):
            digest = sha256(value.encode()).hexdigest() if value is not None else None
            require(digest == candidate[f"{name}_sha256"], "Texto diverge da evidência 43.")
            restored[name] = value
            del restored[f"{name}_sha256"], restored[f"{name}_characters"]
        yield restored


def run(
    *,
    old_workspace=revision.WORKSPACE,
    old_summary=revision.OUTPUT / "resumo_revisao_matching.json",
    case_workspace=case.WORKSPACE,
    case_summary=case.OUTPUT / "resumo_revisao_caixa.json",
    dump=local.DUMP,
    workspace=WORKSPACE,
    output=OUTPUT,
):
    started = time.monotonic()
    require(
        workspace.resolve() not in {old_workspace.resolve(), case_workspace.resolve()},
        "A revisão exige uma pasta própria.",
    )
    old = design.read_json(old_summary)
    prior = design.read_json(case_summary)
    state = old_workspace / "state.sqlite"
    seal = {
        "version": VERSION,
        "code_sha256": design.sha256(Path(__file__)),
        "source43_summary_sha256": design.sha256(old_summary),
        "source43_state_sha256": design.sha256(state),
        "source46_summary_sha256": design.sha256(case_summary),
        "dump": recovery.local.checked_dump(dump),
    }
    require(
        old["completed"]
        and prior["completed"]
        and prior["seal"]["source_summary_sha256"] == seal["source43_summary_sha256"]
        and prior["seal"]["source_state_sha256"] == seal["source43_state_sha256"]
        and prior["seal"]["dump"] == old["seal"]["dump"] == seal["dump"]
        and old["seal"]["code_sha256"] == design.sha256(Path(revision.__file__))
        and prior["seal"]["code_sha256"] == design.sha256(Path(case.__file__)),
        "Fontes ou código divergentes das etapas 43/46.",
    )
    prior_links = case_workspace / "novos_vinculos.parquet"
    require(
        design.sha256(prior_links) == prior["private_sha256"][prior_links.name],
        "Vínculos 46 alterados.",
    )
    previous_ids = set(pl.read_parquet(prior_links, columns=["track_id"])["track_id"])
    with (
        exclusive(workspace),
        closing(local.base.stable_readonly(state)) as db,
        closing(local.base.stable_readonly(dump)) as source,
    ):
        jobs = db.execute(
            f"SELECT q.query_id,q.data,e.payload FROM queries q LEFT JOIN evidence e USING(query_id) WHERE {TARGET} ORDER BY q.query_id"
        ).fetchall()
        tracks = {}
        for track, key in db.execute(
            f"SELECT track_id,query_id FROM tracks JOIN queries q USING(query_id) WHERE {TARGET}"
        ):
            require(track not in previous_ids, "Alvo sobreposto aos vínculos de 46.")
            tracks.setdefault(key, []).append(track)
        require(set(tracks) == {key for key, _, _ in jobs}, "Alvos sem faixa vinculada.")
        print(
            f"Revisão dirigida de {len(jobs)} conflitos plain/LRC por IDs registrados.", flush=True
        )
        decisions, lyrics, links = [], [], []
        for key, raw_query, raw_evidence in jobs:
            query = json.loads(raw_query)
            evidence = json.loads(raw_evidence)
            require(
                fingerprint(query) == key
                and evidence["query"] == query
                and evidence["source"] == seal["dump"],
                "Evidência de outra consulta ou fonte.",
            )
            candidates = list(restore_candidates(source, evidence))
            result, lyric = compare_synced(query, candidates)
            decisions.append({"query_id": key, **result})
            if lyric:
                lyrics.append({"query_id": key, **lyric})
                links.extend({"track_id": track, "query_id": key} for track in tracks[key])

        require(
            design.sha256(state) == seal["source43_state_sha256"]
            and recovery.local.checked_dump(dump) == seal["dump"],
            "Fonte alterada durante a revisão.",
        )
        atomic_json(workspace / "decisoes.json", decisions)
        atomic_frame(
            workspace / "novas_letras_aceitas.parquet", pl.DataFrame(lyrics, schema=LYRIC_SCHEMA)
        )
        atomic_frame(
            workspace / "novos_vinculos.parquet",
            pl.DataFrame(links, schema={"track_id": pl.String, "query_id": pl.String}),
        )
        report = {
            "completed": True,
            "targets": len(jobs),
            "outcomes": dict(Counter(d["outcome"] for d in decisions)),
            "previous_accepted_tracks": prior["accepted_tracks_with_overlay"],
            "new_accepted_tracks": len(links),
            "new_accepted_queries": len(lyrics),
            "accepted_tracks_with_overlays": prior["accepted_tracks_with_overlay"] + len(links),
            "seconds": time.monotonic() - started,
            "seal": seal,
            "private_sha256": {
                name: design.sha256(workspace / name)
                for name in (
                    "decisoes.json",
                    "novas_letras_aceitas.parquet",
                    "novos_vinculos.parquet",
                )
            },
        }
        atomic_json(output / "resumo_revisao_caixa_plain_lrc.json", report)
    return report


def cli(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    try:
        report = run()
    except KeyboardInterrupt:
        print("Interrompido. Repita o comando para reavaliar o lote dirigido.")
        return 2
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "completed",
                    "targets",
                    "new_accepted_tracks",
                    "accepted_tracks_with_overlays",
                )
            }
        ),
        flush=True,
    )
    return 0
