"""Uma rodada offline de recuperação; preserva integralmente a busca v1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sqlite3
import sys
import time
from contextlib import ExitStack, closing
from pathlib import Path

import numpy as np
import polars as pl

from . import local_lyrics as local
from . import sample_lyrics as base
from .catalog_audit import ROOT, markdown_table, sha256
from .catalog_sampling import numeric_values, weighted_summary
from .io import utc_now
from .lyrics_ambiguity_v011 import _representative_sort_key, strict_plain_text_metrics
from .lyrics_pilot import _text_present
from .manual_lyrics import (
    atomic_frame,
    atomic_json,
    exclusive,
    fingerprint,
    meta_get,
    meta_put,
    require,
)
from .normalization import conservative_normalize, normalize_spaces

VERSION = "sample-local-recovery-v2"
WORKSPACE = ROOT / "data/derived/private_sample_lyrics_200k_v2"
OUTPUT = ROOT / "reports/recuperacao_letras_200k_v2"
INDEX = local.DEFAULT_DESTINATION / "tcc_lookup_sample_200k_v2"
PROTOCOL = ROOT / "docs/protocolo_recuperacao_letras_200k_v2.md"
FEAT = re.compile(r"\s+(?:feat(?:uring)?\.?|ft\.?)\s+", re.I)
QUALIFIER = re.compile(
    r"\b(?:live|remix|mix|remaster(?:ed)?|acoustic|demo|karaoke|instrumental|"
    r"radio|edit|mono|stereo|clean|explicit|extended|sped up|slowed|nightcore|version)\b",
    re.I,
)
TIMESTAMP = re.compile(r"\[(\d{1,3}):([0-5]\d)(?:[.:](\d{1,3}))?\]")
LRC_META = re.compile(r"\[(?:ar|al|ti|au|by|re|ve|length|offset):[^\]\r\n]*\]", re.I)
TYPOGRAPHY = str.maketrans(
    {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-", "…": "...", "\u00a0": " "}
)
REASONS = {
    "distinct_strict_texts": "different_texts",
    "eligible_candidates_without_plain_prevent_equivalence": "empty_blocking_text",
    "metadata_conflict": "metadata_conflict",
    "version_conflict": "version_conflict",
    "instrumental_text_conflict": "instrumental_text_conflict",
    "same_id_payload_conflict": "same_id_conflict",
    "candidate_limit": "operational_limit",
    "text_size_limit": "operational_limit",
}


def metadata_key(value):
    """Sem remoção de acentos/transliteração; símbolos puros têm chave literal."""
    text = (normalize_spaces(value) or "").casefold()
    if not text:
        return ""
    if not any(c.isalnum() for c in text):
        return "symbol:" + text
    return re.sub(r"\s+", " ", re.sub(r"[^\w&+/]+", " ", text)).strip()


def profile(artist, title):
    artist, title = normalize_spaces(artist) or "", normalize_spaces(title) or ""
    parts = FEAT.split(artist, maxsplit=1)
    primary = parts[0]
    guests = [metadata_key(parts[1])] if len(parts) == 2 else []
    qualifiers = []
    # Só sufixos delimitados. Não interpreta palavras do título como versão.
    while True:
        match = re.search(r"\s*[\[(]([^\[\]()]+)[\])]\s*$", title)
        if match is None:
            match = re.search(r"\s+-\s+(.+)$", title)
        if match:
            content = match[1].strip()
            feature = FEAT.split("x " + content, maxsplit=1)
            if len(feature) == 2 and feature[0] == "x":
                guests.append(metadata_key(feature[1]))
            elif QUALIFIER.search(content):
                qualifiers.append(
                    metadata_key(re.sub(r"\bremastered\b", "remaster", content, flags=re.I))
                )
            else:
                break
            title = title[: match.start()].strip()
            continue
        feature = FEAT.split(title, maxsplit=1)
        if len(feature) == 2:
            title = feature[0].strip()
            guests.append(metadata_key(feature[1]))
        break
    return {
        "artist": metadata_key(primary),
        "title": metadata_key(title),
        "guests": sorted(set(guests)),
        "versions": sorted(qualifiers),
        "credit_conflict": len(set(guests)) > 1 or any(not g for g in guests),
    }


def recovery_query(row):
    query = base.query_for_metadata(row)
    if query:
        return query
    missing = {None, "", "NA", "N/A", "null", "None"}
    if any(
        (str(row[k]).strip() if row[k] is not None else None) in missing
        for k in ("artist_name", "track_name")
    ):
        return None
    # Nomes como !!! e títulos $$$$ são identificáveis literalmente.
    copy = dict(row, artist_name="placeholder", track_name="placeholder")
    query = base.query_for_metadata(copy)
    query.update(artist_name_query=row["artist_name"], track_name_query=row["track_name"])
    return query


def typography_hash(text):
    return strict_plain_text_metrics(str(text).translate(TYPOGRAPHY))["strict_text_sha256"]


def synced_text(value):
    """LRC de linhas: valida gramática; não ordena nem deduplica palavras/linhas."""
    lines, timed, previous_time = [], False, -1.0
    for raw in (
        str(value).replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ):
        if not raw.strip():
            continue  # espaçamento externo ao formato LRC não é verso
        if LRC_META.fullmatch(raw.strip()):
            continue
        rest, stamps = raw, []
        while (match := TIMESTAMP.match(rest)) is not None:
            fraction = float("0." + match[3]) if match[3] else 0.0
            stamps.append(int(match[1]) * 60 + int(match[2]) + fraction)
            rest = rest[match.end() :]
        # Múltiplos timestamps exigiriam expansão/reordenação: não improvisar.
        if len(stamps) > 1:
            return None, "unsupported_multi_timestamp_synced"
        if len(stamps) != 1 or re.search(r"(?:\[\d|<\d{1,3}:)", rest):
            return None, "invalid_or_extended_synced_format"
        if stamps[0] < previous_time:
            return None, "unordered_synced_timestamps"
        previous_time = stamps[0]
        lines.append(rest)
        timed = True
    text = "\n".join(lines)
    if not timed or not text.strip():
        return None, "empty_synced_text"
    return text, None


def duration_delta(query, candidate):
    values = []
    for value in (query.get("duration_seconds"), candidate.get("duration")):
        try:
            number = float(value)
            values.append(number if math.isfinite(number) and number > 0 else None)
        except (ValueError, TypeError):
            values.append(None)
    return abs(values[0] - values[1]) if all(v is not None for v in values) else None


def classify(query, candidates, incomplete=None, *, origin="cache"):
    require(set(query) <= base.MATCH_FIELDS, "Matching recebeu campo proibido.")
    result = {
        "status": "ambiguous",
        "reason": "metadata_conflict",
        "method": origin,
        "rules_version": VERSION,
        "language_status": "not_evaluated",
        "candidate_count": len(candidates) if not incomplete else None,
        "candidate_present": bool(candidates) if not incomplete else True,
        "text_present": any(
            _text_present(c.get("plainLyrics")) or _text_present(c.get("syncedLyrics"))
            for c in candidates
        )
        if not incomplete
        else None,
        "plain_present": any(_text_present(c.get("plainLyrics")) for c in candidates)
        if not incomplete
        else None,
        "synced_present": any(_text_present(c.get("syncedLyrics")) for c in candidates)
        if not incomplete
        else None,
        "eligible_count": 0,
        "equivalent_count": 0,
        "empty_ignored": 0,
        "operational_limit": bool(incomplete),
        "recovery_rule": None,
    }
    if incomplete:
        return {**result, "reason": "operational_limit:" + incomplete}, None
    if not candidates:
        return {**result, "status": "not_found", "reason": "no_candidate_controlled_keys"}, None
    unique = {}
    for c in candidates:
        if c["id"] in unique and unique[c["id"]] != c:
            return {**result, "reason": "same_id_payload_conflict"}, None
        unique[c["id"]] = c
    q = profile(query["artist_name_query"], query["track_name_query"])
    eligible, transformations, positive_version_conflict = [], {}, False
    if not q["artist"] or not q["title"] or q["credit_conflict"]:
        return {**result, "reason": "unresolved_credit_or_title"}, None
    for c in unique.values():
        p = profile(c.get("artistName"), c.get("trackName"))
        delta = duration_delta(query, c)
        if p["credit_conflict"] or any(q[k] != p[k] for k in ("artist", "title", "guests")):
            continue
        if delta is not None and delta > base.TOLERANCE:
            continue
        if q["versions"] != p["versions"]:
            positive_version_conflict = True
            continue
        transforms = []
        if any(v.startswith("symbol:") for v in (q["artist"], q["title"])):
            transforms.append("literal_symbols")
        if q["guests"] and (
            query["artist_name_query"] != c.get("artistName")
            or query["track_name_query"] != c.get("trackName")
        ):
            transforms.append("explicit_feat_layout")
        if q["versions"] and query["track_name_query"] != c.get("trackName"):
            transforms.append("qualifier_layout")
        if not transforms:
            transforms.append("contextual_metadata")
        transformations[str(c["id"])] = transforms
        eligible.append(
            {
                "candidate": c,
                "diagnostics": {"duration_difference_seconds": delta},
                "endpoints": ["sqlite"],
                "candidate_key_sha256": fingerprint(c["id"]),
            }
        )
    result.update(eligible_count=len(eligible), candidate_transformations=transformations)
    if positive_version_conflict:
        return {**result, "reason": "positive_version_conflict"}, None
    if not eligible:
        return result, None
    instruments = [e for e in eligible if e["candidate"].get("instrumental")]
    if instruments:
        if len(instruments) == len(eligible) and not any(
            _text_present(e["candidate"].get(k))
            for e in eligible
            for k in ("plainLyrics", "syncedLyrics")
        ):
            representative = min(eligible, key=_representative_sort_key)["candidate"]
            return {
                **result,
                "status": "instrumental",
                "reason": "compatible_source_instrumental_no_text",
                "selected_lrclib_id": representative["id"],
                "selected_lyrics_id": representative.get("local_lyrics_id"),
            }, None
        return {**result, "reason": "instrumental_text_conflict"}, None
    texts = []
    for item in eligible:
        c = item["candidate"]
        plain = c.get("plainLyrics") if _text_present(c.get("plainLyrics")) else None
        synced, error = (
            synced_text(c["syncedLyrics"]) if _text_present(c.get("syncedLyrics")) else (None, None)
        )
        if error:
            return {**result, "reason": error}, None
        if plain and synced and typography_hash(plain) != typography_hash(synced):
            return {**result, "reason": "plain_synced_conflict"}, None
        text = plain or synced
        if text is None:
            result["empty_ignored"] += 1
        else:
            texts.append({**item, "text": text, "derived": plain is None})
    if not texts:
        return {**result, "status": "no_text", "reason": "compatible_without_text"}, None
    strict = {strict_plain_text_metrics(e["text"])["strict_text_sha256"] for e in texts}
    if len({typography_hash(e["text"]) for e in texts}) != 1:
        return {**result, "reason": "substantively_distinct_texts"}, None
    selected = min(texts, key=_representative_sort_key)
    c, text = selected["candidate"], selected["text"]
    rules = {origin, *(rule for v in transformations.values() for rule in v)}
    if result["empty_ignored"]:
        rules.add("ignore_empty")
    if any(e["derived"] for e in texts):
        rules.add("synced_extraction")
    if len(strict) > 1:
        rules.add("typographic_equivalence")
    result.update(
        status="accepted",
        reason="compatible_equivalent_texts",
        equivalent_count=len(texts),
        selected_lrclib_id=c["id"],
        selected_lyrics_id=c.get("local_lyrics_id"),
        text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        strict_text_sha256=strict_plain_text_metrics(text)["strict_text_sha256"],
        typography_sha256=typography_hash(text),
        recovery_rule="+".join(sorted(rules)),
        text_origin="derived_synced" if selected["derived"] else "plain_lyrics_unmodified",
    )
    lyric = {
        # Campo interno requerido pelo exportador v1; exportação v2 o renomeia accepted_text.
        "plain_text_source": text,
        "synced_text_source": c.get("syncedLyrics"),
        "lrclib_id": c["id"],
        "lrclib_lyrics_id": c.get("local_lyrics_id"),
        "text_sha256": result["text_sha256"],
        "strict_text_sha256": result["strict_text_sha256"],
        "typography_sha256": result["typography_sha256"],
        "text_origin": result["text_origin"],
        "equivalent_lrclib_ids": sorted(e["candidate"]["id"] for e in texts),
        "candidate_transformations": transformations,
        "recovery_rule": result["recovery_rule"],
        "empty_ignored": result["empty_ignored"],
        "rules_version": VERSION,
        "source_plain_original": c.get("plainLyrics"),
        "representative_rule": "duration_then_completeness_then_id_only_after_text_equivalence",
    }
    return result, lyric


def file_stamp(path):
    stat = path.stat()
    return {"path": str(path.resolve()), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def make_queries(sample):
    queries, tracks = {}, []
    for row in sample.select("track_id", "artist_name", "track_name", "duration_ms").iter_rows(
        named=True
    ):
        q = recovery_query(row)
        key = fingerprint(q) if q else None
        if q:
            queries[key] = q
        tracks.append((row["track_id"], key))
    return queries, tracks


def initial_diagnostics(prior, old_indexes):
    """Diagnóstico por faixa antes da recuperação; sem carregar evidências/textos."""
    artist_cache, records = {}, []
    for row in prior.select(
        "track_id", "lyrics_status", "lyrics_reason", "artist_name", "track_name"
    ).iter_rows(named=True):
        status, reason = row["lyrics_status"], row["lyrics_reason"]
        diagnostic = REASONS.get(reason, reason)
        if status == "not_found":
            artist = conservative_normalize(row["artist_name"])
            if artist not in artist_cache:
                artist_cache[artist] = any(
                    index.execute(
                        "SELECT 1 FROM catalog WHERE artist_key=? LIMIT 1", (artist,)
                    ).fetchone()
                    is not None
                    for index in old_indexes
                )
            diagnostic = (
                "artist_present_title_not_found_v1"
                if artist_cache[artist]
                else "full_credit_not_found_v1"
            )
        elif status == "insufficient_metadata":
            query = recovery_query({k: row[k] for k in ("track_id", "artist_name", "track_name")})
            diagnostic = (
                "symbols_erased_by_v1_normalization" if query else "missing_artist_or_title"
            )
        records.append({"track_id": row["track_id"], "recovery_initial_diagnostic": diagnostic})
    return pl.DataFrame(records)


def initialize(db, old, seal, queries, tracks, prior, diagnostics):
    base.initialize(db, seal, queries, tracks)
    if not db.execute("SELECT 1 FROM sqlite_schema WHERE name='recovery'").fetchone():
        db.executescript("""BEGIN IMMEDIATE;
        CREATE TABLE recovery(query_id TEXT PRIMARY KEY REFERENCES queries(query_id),
          old_query_id TEXT, old_status TEXT, old_reason TEXT, phase TEXT NOT NULL DEFAULT 'cache');
        CREATE INDEX recovery_phase ON recovery(phase);
        """)
        mapping = dict(tracks)
        seen = set()
        with db:
            for row in prior.select(
                "track_id", "lyrics_query_id", "lyrics_status", "lyrics_reason"
            ).iter_rows(named=True):
                key = mapping[row["track_id"]]
                if key is None or key in seen:
                    continue
                seen.add(key)
                db.execute(
                    "INSERT INTO recovery(query_id,old_query_id,old_status,old_reason) VALUES (?,?,?,?)",
                    (key, row["lyrics_query_id"], row["lyrics_status"], row["lyrics_reason"]),
                )
    # Importação retomável; decisões antigas aceitas/instrumentais são copiadas sem reclassificar.
    rows = db.execute(
        "SELECT * FROM recovery WHERE phase='cache' AND old_status IN ('accepted','instrumental')"
    ).fetchall()
    import_started, last_import = time.monotonic(), 0.0
    for row in rows:
        stored = old.execute(
            "SELECT status,result FROM queries WHERE query_id=?", (row["old_query_id"],)
        ).fetchone()
        require(
            stored and stored["status"] == row["old_status"], "Estado anterior diverge do Parquet."
        )
        result = json.loads(stored["result"])
        result.update(
            recovery_rule="preserved_v1", method=result.get("method", "sqlite_snapshot_exact")
        )
        with db:
            if row["old_status"] == "accepted":
                lyric = old.execute(
                    "SELECT data FROM lyrics WHERE query_id=?", (row["old_query_id"],)
                ).fetchone()
                require(lyric is not None, "Letra aceita anterior sem referência.")
                db.execute(
                    "INSERT OR REPLACE INTO lyrics VALUES (?,?)", (row["query_id"], lyric[0])
                )
            db.execute(
                "UPDATE queries SET status=?,result=? WHERE query_id=?",
                (row["old_status"], json.dumps(result), row["query_id"]),
            )
            db.execute("UPDATE recovery SET phase='done' WHERE query_id=?", (row["query_id"],))
        if time.monotonic() - last_import >= 10:
            progress(db, Path(seal["workspace"]), "preserving_v1", import_started)
            last_import = time.monotonic()
    atomic_frame(Path(seal["workspace"]) / "diagnostico_inicial_privado.parquet", diagnostics)


def progress(db, workspace, stage, started, **extra):
    value = {
        "stage": stage,
        "updated_at": utc_now(),
        "elapsed_seconds": time.monotonic() - started,
        "queries_by_status": dict(
            db.execute("SELECT status,count(*) FROM queries GROUP BY status")
        ),
        "jobs_by_phase": dict(db.execute("SELECT phase,count(*) FROM recovery GROUP BY phase")),
        **extra,
    }
    atomic_json(workspace / "progress.json", value)
    print(json.dumps(value), flush=True)


def save_decision(db, key, result, lyric, evidence, source, detector):
    if lyric:
        lyric.update(query_id=key, source_dump=source)
        if evidence.get("origin") == "v1_evidence":
            seal = meta_get(db, "seal")
            lyric.update(
                previous_evidence_query_id=evidence["old_query_id"],
                previous_state_sha256=seal["baseline_state_sha256"],
                previous_state_path=seal["baseline_state_stamp"]["path"],
            )
        if detector is not None:
            try:
                result.update(
                    base.detect_language(
                        lyric["plain_text_source"], threshold=0.80, identifier=detector
                    )
                )
            except Exception:
                result["language_status"] = "not_evaluated_detector_error"
    with db:
        db.execute(
            "UPDATE queries SET status=?,result=? WHERE query_id=?",
            (result["status"], json.dumps(result), key),
        )
        if lyric:
            db.execute(
                "INSERT OR REPLACE INTO lyrics VALUES (?,?)",
                (key, json.dumps(lyric, ensure_ascii=False)),
            )
        db.execute(
            "INSERT OR REPLACE INTO evidence VALUES (?,?)",
            (key, json.dumps(evidence, ensure_ascii=False)),
        )
        db.execute("UPDATE recovery SET phase='done' WHERE query_id=?", (key,))


def cache_pass(db, old, workspace, source, detector):
    start, last = time.monotonic(), 0.0
    for job in db.execute(
        "SELECT r.*,q.data FROM recovery r JOIN queries q USING(query_id) WHERE phase='cache'"
    ).fetchall():
        key, query = job["query_id"], json.loads(job["data"])
        stored = (
            old.execute(
                "SELECT payload FROM evidence WHERE query_id=?", (job["old_query_id"],)
            ).fetchone()
            if job["old_query_id"]
            else None
        )
        require(
            stored is not None or job["old_status"] == "insufficient_metadata",
            "Evidência anterior ausente.",
        )
        evidence = (
            json.loads(stored[0]) if stored else {"candidates": [], "incomplete_reason": None}
        )
        if stored:
            require(
                evidence["query"] == query and evidence["source"] == source,
                "Cache incompatível com consulta/fonte.",
            )
            previous = old.execute(
                "SELECT status,result FROM queries WHERE query_id=?", (job["old_query_id"],)
            ).fetchone()
            require(
                previous["status"] == job["old_status"]
                and json.loads(previous["result"])["reason"] == job["old_reason"],
                "Motivo/status v1 diverge da evidência de origem.",
            )
        result, lyric = classify(query, evidence["candidates"], evidence.get("incomplete_reason"))
        # Uma passagem local adicional só onde a recuperação de metadados pode ajudar.
        needs_lookup = result["status"] == "not_found" or result["reason"] == "metadata_conflict"
        if needs_lookup:
            with db:
                db.execute("UPDATE recovery SET phase='lookup' WHERE query_id=?", (key,))
        else:
            save_decision(
                db,
                key,
                result,
                lyric,
                {"old_query_id": job["old_query_id"], "origin": "v1_evidence", "decision": result},
                source,
                detector,
            )
        if time.monotonic() - last >= 10:
            progress(db, workspace, "reclassifying_cache", start)
            last = time.monotonic()
    return time.monotonic() - start


def build_index(dump, destination, artists, identity):
    """Mesmo schema/commit do índice antigo, novo filtro de crédito primário explícito."""
    destination.mkdir(parents=True, exist_ok=True)
    seal = {
        "dump": identity,
        "artists": fingerprint(sorted(artists)),
        "rules": sha256(Path(__file__)),
    }
    with (
        exclusive(destination),
        closing(local.connection_index(destination / "lookup.sqlite")) as index,
    ):
        if not index.execute("SELECT 1 FROM sqlite_schema WHERE name='meta'").fetchone():
            require(
                not index.execute("SELECT 1 FROM sqlite_schema WHERE type='table'").fetchone(),
                "Índice desconhecido.",
            )
            index.executescript("BEGIN IMMEDIATE;" + local.INDEX_SQL)
            with index:
                meta_put(index, "seal", seal)
                meta_put(
                    index, "progress", {"last_id": 0, "scanned": 0, "indexed": 0, "complete": False}
                )
        require(meta_get(index, "seal") == seal, "Índice v2 incompatível; preservado.")
        state, wanted, last = meta_get(index, "progress"), set(artists), 0.0
        with closing(base.stable_readonly(dump)) as source:
            while not state["complete"]:
                local.space(destination)
                rows = source.execute(
                    "SELECT id,name,artist_name,album_name,duration,last_lyrics_id FROM tracks WHERE id>? ORDER BY id LIMIT 5000",
                    (state["last_id"],),
                ).fetchall()
                selected = []
                for row in rows:
                    artist = metadata_key(
                        FEAT.split(normalize_spaces(row["artist_name"]) or "", maxsplit=1)[0]
                    )
                    if artist in wanted:
                        p = profile(row["artist_name"], row["name"])
                        selected.append(
                            (
                                row["id"],
                                artist,
                                p["title"],
                                p["title"],
                                row["name"],
                                row["artist_name"],
                                row["album_name"],
                                row["duration"],
                                row["last_lyrics_id"],
                            )
                        )
                next_state = {
                    "last_id": rows[-1]["id"] if rows else state["last_id"],
                    "scanned": state["scanned"] + len(rows),
                    "indexed": state["indexed"] + len(selected),
                    "complete": not rows,
                    "updated_at": utc_now(),
                }
                with index:
                    index.executemany("INSERT INTO catalog VALUES (?,?,?,?,?,?,?,?,?)", selected)
                    meta_put(index, "progress", next_state)
                state = next_state
                if time.monotonic() - last >= 10 or state["complete"]:
                    atomic_json(destination / "progress.json", state)
                    print(json.dumps({"stage": "recovery_index", **state}), flush=True)
                    last = time.monotonic()
        atomic_json(destination / "progress.json", state)
    return state


def lookup(dump, index, query):
    p = profile(query["artist_name_query"], query["track_name_query"])
    deadline = time.monotonic() + 30
    for db in (dump, index):
        db.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
    try:
        rows = index.execute(
            "SELECT * FROM catalog WHERE artist_key=? AND title_key=? ORDER BY id LIMIT 501",
            (p["artist"], p["title"]),
        ).fetchall()
        if len(rows) > local.MAX_CANDIDATES:
            return [], "candidate_limit"
        candidates, total = [], 0
        for row in rows:
            if time.monotonic() > deadline:
                raise TimeoutError("local_query_timeout")
            lyric = None
            if row["last_lyrics_id"] is not None:
                sizes = dump.execute(
                    "SELECT track_id,length(plain_lyrics),length(synced_lyrics) FROM lyrics WHERE id=?",
                    (row["last_lyrics_id"],),
                ).fetchone()
                require(
                    sizes is not None and sizes[0] == row["id"], "Referência LRCLIB inconsistente."
                )
                chars = (sizes[1] or 0) + (sizes[2] or 0)
                total += chars
                if chars > local.MAX_TEXT_CHARACTERS or total > local.MAX_TOTAL_CHARACTERS:
                    return [], "text_size_limit"
                lyric = dump.execute(
                    "SELECT plain_lyrics,synced_lyrics,instrumental FROM lyrics WHERE id=?",
                    (row["last_lyrics_id"],),
                ).fetchone()
            candidates.append(
                {
                    "id": row["id"],
                    "trackName": row["name"],
                    "artistName": row["artist_name"],
                    "albumName": row["album_name"],
                    "duration": row["duration"],
                    "plainLyrics": lyric[0] if lyric else None,
                    "syncedLyrics": lyric[1] if lyric else None,
                    "instrumental": bool(lyric[2]) if lyric else False,
                    "local_lyrics_id": row["last_lyrics_id"],
                }
            )
        return candidates, None
    finally:
        for db in (dump, index):
            db.set_progress_handler(None, 0)


def search_pass(db, dump, index, workspace, source, detector, *, retry=False, limit=None):
    started, last = time.monotonic(), 0.0
    condition = (
        "q.status='pending' OR (q.status='technical_error' AND q.attempts<3)"
        if retry
        else "q.status='pending'"
    )
    jobs = db.execute(
        f"SELECT q.query_id,q.data FROM queries q JOIN recovery r USING(query_id) WHERE r.phase='lookup' AND ({condition}) ORDER BY q.query_id LIMIT ?",
        (limit if limit else -1,),
    ).fetchall()
    new = 0
    for key, raw in jobs:
        query = json.loads(raw)
        with db:
            db.execute("UPDATE queries SET attempts=attempts+1 WHERE query_id=?", (key,))
        try:
            local.space(workspace)
            candidates, incomplete = lookup(dump, index, query)
            result, lyric = classify(query, candidates, incomplete, origin="controlled_lookup")
            save_decision(
                db,
                key,
                result,
                lyric,
                {
                    "query": query,
                    "source": source,
                    "candidates": candidates,
                    "query_profile": profile(query["artist_name_query"], query["track_name_query"]),
                    "candidate_profiles": {
                        str(c["id"]): profile(c.get("artistName"), c.get("trackName"))
                        for c in candidates
                    },
                    "retrieval_rule": "primary_credit_and_contextual_title",
                    "incomplete_reason": incomplete,
                    "queried_at": utc_now(),
                    "decision": result,
                },
                source,
                detector,
            )
            new += 1
        except (sqlite3.Error, OSError, ValueError, TypeError, KeyError, TimeoutError) as exc:
            with db:
                db.execute(
                    "UPDATE queries SET status='technical_error',result=? WHERE query_id=?",
                    (
                        json.dumps(
                            {
                                "status": "technical_error",
                                "reason": type(exc).__name__,
                                "rules_version": VERSION,
                            }
                        ),
                        key,
                    ),
                )
            break
        if time.monotonic() - last >= 10:
            progress(db, workspace, "recovery_search", started, new_local_queries=new)
            last = time.monotonic()
    progress(db, workspace, "search_checkpoint", started, new_local_queries=new)
    return new, time.monotonic() - started


def export_private(db, sample, prior, diagnostics, workspace):
    final, count = base.export_private(db, sample, workspace)
    extra = []
    for key, raw in db.execute("SELECT query_id,result FROM queries"):
        r = json.loads(raw) if raw else {}
        extra.append(
            {
                "lyrics_query_id": key,
                "effective_rules_version": r.get("rules_version", VERSION),
                **{
                    "recovery_" + k: r.get(k)
                    for k in (
                        "recovery_rule",
                        "empty_ignored",
                        "text_origin",
                        "typography_sha256",
                        "operational_limit",
                    )
                },
                "recovery_candidate_transformations_json": json.dumps(
                    r.get("candidate_transformations", {}), ensure_ascii=False
                ),
            }
        )
    extras = pl.DataFrame(extra, infer_schema_length=None).rename(
        {"recovery_recovery_rule": "recovery_rule"}
    )
    final = (
        final.join(extras, on="lyrics_query_id", how="left", validate="m:1")
        .with_columns(
            pl.col("effective_rules_version").fill_null(VERSION).alias("lyrics_rules_version")
        )
        .drop("effective_rules_version")
    )
    old_columns = [c for c in prior.columns if c.startswith("lyrics_")]
    final = final.join(
        prior.select("track_id", *old_columns).rename({c: "v1_" + c for c in old_columns}),
        on="track_id",
        how="left",
        validate="1:1",
    ).join(diagnostics, on="track_id", validate="1:1")
    preserved = final.filter(pl.col("v1_lyrics_status").is_in(["accepted", "instrumental"]))
    require(
        (preserved["lyrics_status"] == preserved["v1_lyrics_status"]).all(),
        "Status protegido v1 mudou.",
    )
    accepted = preserved.filter(pl.col("lyrics_status") == "accepted")
    for field in (
        "text_sha256",
        "strict_text_sha256",
        "selected_lrclib_id",
        "selected_lyrics_id",
        "reason",
        "method",
    ):
        require(
            accepted["lyrics_" + field].equals(accepted["v1_lyrics_" + field]),
            "Aceitação anterior alterada.",
        )
    require(
        final.height == sample.height
        and final.select(sample.columns).sort("track_id").equals(sample.sort("track_id")),
        "Amostra/desenho mudou.",
    )
    # Streaming: acrescenta texto efetivo separado das duas representações originais.
    import pyarrow as pa
    import pyarrow.parquet as pq

    path = workspace / "letras_aceitas_200k.parquet"
    schema = (
        pq.read_schema(path)
        .append(pa.field("accepted_text", pa.string()))
        .append(pa.field("source_plain_sha256", pa.string()))
        .append(pa.field("source_synced_sha256", pa.string()))
    )
    with pq.ParquetWriter(path.with_suffix(".v2.tmp"), schema, compression="zstd") as writer:
        for batch in pq.ParquetFile(path).iter_batches(batch_size=256):
            records = []
            for row in batch.to_pylist():
                provenance = json.loads(row["provenance_json"])
                row["accepted_text"] = row["plain_text_source"]
                row["plain_text_source"] = provenance.pop(
                    "source_plain_original", row["plain_text_source"]
                )
                for name in ("plain", "synced"):
                    value = row[name + "_text_source"]
                    row["source_" + name + "_sha256"] = (
                        hashlib.sha256(value.encode()).hexdigest() if value is not None else None
                    )
                row["provenance_json"] = json.dumps(provenance, ensure_ascii=False)
                records.append(row)
            writer.write_table(pa.Table.from_pylist(records, schema=schema))
    path.with_suffix(".v2.tmp").replace(path)
    atomic_frame(workspace / "resultados_faixas_200k.parquet", final)
    # Inspeção dirigida, determinística, até 3 consultas por método; não estima precisão.
    recovered = final.filter(
        (pl.col("lyrics_status") == "accepted") & (pl.col("v1_lyrics_status") != "accepted")
    )
    review = []
    for _, group in recovered.partition_by("recovery_rule", as_dict=True).items():
        for row in (
            group.sort("track_id")
            .unique("lyrics_query_id", maintain_order=True)
            .head(3)
            .iter_rows(named=True)
        ):
            lyric = json.loads(
                db.execute(
                    "SELECT data FROM lyrics WHERE query_id=?", (row["lyrics_query_id"],)
                ).fetchone()[0]
            )
            query = json.loads(
                db.execute(
                    "SELECT data FROM queries WHERE query_id=?", (row["lyrics_query_id"],)
                ).fetchone()[0]
            )
            review.append(
                {
                    "track_id": row["track_id"],
                    "query_id": row["lyrics_query_id"],
                    "rule": row["recovery_rule"],
                    "previous_status": row["v1_lyrics_status"],
                    "query": query,
                    "lyric": lyric,
                    "human_review": "pending",
                }
            )
    atomic_json(workspace / "amostra_inspecao_novas_aceitacoes.json", review)
    return final, count, len(review)


def counts(frame, columns):
    return (
        frame.group_by(columns)
        .agg(pl.len().alias("n_tracks"), pl.col("sampling_weight").sum().alias("sum_weights"))
        .sort(columns)
        .to_dicts()
    )


def write_csv(path, rows):
    """Substituição atômica somente dentro da pasta v2 já selada."""
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def publish(final, prior, output, summary):
    comparison = []
    for phase, frame in (("before", prior), ("after", final)):
        comparison.extend({"phase": phase, **row} for row in base.coverage_tables(frame))
    write_csv(output / "comparacao_cobertura_recuperacao_200k.csv", comparison)
    summary["plots"] = base.public_plots([r for r in comparison if r["phase"] == "after"], output)
    transitions = counts(final, ["v1_lyrics_status", "lyrics_status"])
    write_csv(output / "transicoes_status_200k.csv", transitions)
    diagnostics = counts(final, ["v1_lyrics_status", "recovery_initial_diagnostic"])
    write_csv(output / "diagnostico_perdas_inicial_200k.csv", diagnostics)
    recovered = final.filter(
        (pl.col("lyrics_status") == "accepted") & (pl.col("v1_lyrics_status") != "accepted")
    )
    rules = (
        counts(recovered, ["recovery_rule"])
        if recovered.height
        else [{"recovery_rule": "none", "n_tracks": 0, "sum_weights": 0.0}]
    )
    write_csv(output / "recuperacoes_por_regra_200k.csv", rules)
    losses = counts(
        final.filter(pl.col("lyrics_status") != "accepted"), ["lyrics_status", "lyrics_reason"]
    )
    if losses:
        write_csv(output / "perdas_restantes_200k.csv", losses)
    instrument_rows = []
    # Título contextual é apenas indicador descritivo, nunca corte de elegibilidade.
    title_indicator = [
        any("instrumental" in qualifier.split() for qualifier in profile(a, t)["versions"])
        for a, t in final.select("artist_name", "track_name").iter_rows()
    ]
    instrument_frame = final.with_columns(
        pl.Series("title_instrumental_qualifier", title_indicator)
    )
    for marked in (True, False):
        subset = instrument_frame.filter((pl.col("v1_lyrics_status") == "instrumental") == marked)
        if not subset.height:
            continue
        for weighted in (False, True):
            w = subset["sampling_weight"].to_numpy() if weighted else np.ones(subset.height)
            stats = weighted_summary(numeric_values(subset, "instrumentalness")[0], w)
            instrument_rows.append(
                {
                    "v1_lrclib_instrumental": marked,
                    "weighted": weighted,
                    "n_tracks": subset.height,
                    "denominator_weight": float(w.sum()),
                    "title_indicator_n": int(subset["title_instrumental_qualifier"].sum()),
                    "title_indicator_weight": float(
                        w[subset["title_instrumental_qualifier"].to_numpy()].sum()
                    ),
                    **stats,
                }
            )
    write_csv(output / "comparacao_instrumentais_200k.csv", instrument_rows)
    summary.update(
        status_counts=dict(final.group_by("lyrics_status").len().iter_rows()),
        previous_status_counts=dict(prior.group_by("lyrics_status").len().iter_rows()),
        recovered_tracks=recovered.height,
        recovered_by_rule=rules,
        preserved_previous_accepted=prior.filter(pl.col("lyrics_status") == "accepted").height,
        preserved_previous_instrumental=prior.filter(
            pl.col("lyrics_status") == "instrumental"
        ).height,
        remaining_losses=losses,
        high_popularity=counts(
            final.filter(pl.col("popularity").cast(pl.Float64) >= 80).with_columns(
                pl.when(pl.col("popularity").cast(pl.Float64) >= 90)
                .then(pl.lit("90-100"))
                .otherwise(pl.lit("80-89"))
                .alias("high_band")
            ),
            ["high_band", "v1_lyrics_status", "lyrics_status"],
        ),
    )
    summary["completed"] = not any(
        summary["status_counts"].get(s, 0) for s in ("pending", "technical_error")
    )
    summary["status"] = "completed" if summary["completed"] else "incomplete"
    summary["checks"]["recovery_counts_reconcile"] = (
        sum(r["n_tracks"] for r in rules)
        == recovered.height
        == final.filter(pl.col("lyrics_status") == "accepted").height
        - prior.filter(pl.col("lyrics_status") == "accepted").height
    )
    require(summary["checks"]["recovery_counts_reconcile"], "Dupla contagem de recuperações.")
    profile_rows = [
        r
        for r in comparison
        if r["scope"] in ("accepted|weighted", "accepted|unweighted")
        and r["section"] == "numeric_all_finite"
        and r["variable"] in ("popularity", "duration_ms")
        and r["metric"] in ("mean", "q50")
    ]
    genre_lookup = {
        (r["phase"], r["scope"], r["category"]): r["value"]
        for r in comparison
        if r["section"] == "distribution"
        and r["variable"] == "_s_genre"
        and r["metric"] == "fraction"
        and r["scope"].startswith("accepted|")
    }
    genre_changes = []
    for scope in ("accepted|unweighted", "accepted|weighted"):
        for category in sorted({k[2] for k in genre_lookup}):
            before, after = (
                genre_lookup.get((phase, scope, category)) for phase in ("before", "after")
            )
            if before is not None and after is not None:
                genre_changes.append(
                    {
                        "scope": scope,
                        "genre": category,
                        "before_fraction": before,
                        "after_fraction": after,
                        "difference_percentage_points": 100 * (after - before),
                    }
                )
    genre_changes.sort(
        key=lambda r: (-abs(r["difference_percentage_points"]), r["scope"], r["genre"])
    )
    summary["coverage"] = []
    for phase, frame in (("before", prior), ("after", final)):
        accepted = frame.filter(pl.col("lyrics_status") == "accepted")
        summary["coverage"].append(
            {
                "phase": phase,
                "accepted_n": accepted.height,
                "denominator_n": frame.height,
                "unweighted_rate": accepted.height / frame.height,
                "accepted_weight": float(accepted["sampling_weight"].sum()),
                "denominator_weight": float(frame["sampling_weight"].sum()),
                "weighted_rate": float(
                    accepted["sampling_weight"].sum() / frame["sampling_weight"].sum()
                ),
            }
        )
    report = [
        "# Recuperação local de letras — rodada v2",
        f"Status: **{summary['status']}**. Novas faixas aceitas: **{recovered.height}**. Aceitas v1 preservadas: {summary['preserved_previous_accepted']}; instrumentais v1 preservados: {summary['preserved_previous_instrumental']}.",
        "## Diagnóstico anterior",
        markdown_table(
            diagnostics,
            ["v1_lyrics_status", "recovery_initial_diagnostic", "n_tracks", "sum_weights"],
        ),
        "## Transições",
        markdown_table(
            transitions, ["v1_lyrics_status", "lyrics_status", "n_tracks", "sum_weights"]
        ),
        "## Recuperações por método exclusivo",
        markdown_table(rules, ["recovery_rule", "n_tracks", "sum_weights"]),
        "Cada faixa recuperada pertence a uma combinação de regras; não somar componentes sobrepostos. n_tracks é contagem real; sum_weights usa os pesos congelados.",
        "## Perfil das aceitas antes/depois",
        markdown_table(
            summary["coverage"],
            [
                "phase",
                "accepted_n",
                "denominator_n",
                "unweighted_rate",
                "accepted_weight",
                "denominator_weight",
                "weighted_rate",
            ],
        ),
        markdown_table(
            profile_rows, ["phase", "scope", "variable", "metric", "value", "denominator"]
        ),
        "Maiores mudanças de proporção de gênero entre aceitas (até 20 linhas; diferenças em pontos percentuais):",
        markdown_table(
            genre_changes[:20],
            ["scope", "genre", "before_fraction", "after_fraction", "difference_percentage_points"],
        ),
        "O CSV de comparação inclui amostra completa, aceitas, não aceitas e cada status; gênero, período, ano, popularidade, duração, acústicas, créditos e concentração. Contagens e taxas ponderadas mantêm denominadores explícitos. As 499 faixas ≥80 são destacadas somente nesta análise.",
        markdown_table(
            summary["high_popularity"],
            ["high_band", "v1_lyrics_status", "lyrics_status", "n_tracks", "sum_weights"],
        ),
        "## Perdas restantes",
        markdown_table(losses, ["lyrics_status", "lyrics_reason", "n_tracks", "sum_weights"]),
        "## Regras e limites",
        "Uma rodada: evidências v1, seguida de uma consulta por par de chaves controladas quando necessária. Participação explícita feat./ft./featuring pode mudar de campo; não dividimos bandas por &, and, vírgula ou ponto e vírgula. Versões têm contexto e qualificadores completos. Duração mantém tolerância de dez segundos. Instrumentalness não participa da aceitação.",
        "Texto vazio deixa de bloquear texto compatível. LRC válido pode fornecer texto derivado; formatos não suportados e conflitos plain/synced permanecem explícitos. Equivalência adicional limita-se a sinais tipográficos, preservando palavras, caixa, versos e repetições. Similaridade não prova identidade.",
        "Aceitações são automáticas. A amostra privada dirigida, até três consultas por método, permanece sem revisão humana. Testes sintéticos não estimam precisão. Homônimos, créditos incompletos e versões insuficientemente descritas continuam limitando identidade; não há aliases nem transliteração.",
        "Limitações v1 foram identificadas no código: normalização pode colapsar sinais/acentos, flags detectavam palavras fora de qualificadores e representações sincronizadas não eram confrontadas. Isso não demonstra erro em uma aceitação específica; as aceitações antigas permanecem com sua regra/origem v1, sem alteração silenciosa.",
        "Marcação instrumental LRCLIB, instrumentalness e qualificador no título são evidências distintas, sem verdade absoluta ou corte de exclusão. Pesos amostrais não corrigem perdas por disponibilidade/aceitação. Nem tamanho do conjunto nem proximidade de distribuições demonstra representatividade. Não há afirmação causal, modelos ou novos splits; a exposição prévia do teste V0.6 permanece.",
        "## Tempos e execução",
        f"Tempo desta invocação até o relatório: {summary['invocation_elapsed_seconds']:.2f} s. Histórico por fase e retomada no JSON; invocações encerradas à força podem não ter tempo final salvo.",
        *[f"![{name}]({name})" for name in summary["plots"]],
    ]
    (output / "relatorio_recuperacao_letras_200k.md").write_text(
        "\n\n".join(report) + "\n", encoding="utf-8"
    )
    (output / "protocolo_recuperacao_letras_200k_v2.md").write_text(
        PROTOCOL.read_text(encoding="utf-8"), encoding="utf-8"
    )
    atomic_json(output / "resumo_recuperacao_letras_200k.json", summary)


def execute(
    *,
    sample_path=base.SAMPLE_DIR / "amostra_spotify_200k.parquet",
    sample_summary=base.SAMPLE_DIR / "resumo_amostra_200k.json",
    allocation=base.SAMPLE_DIR / "alocacao_amostra_200k.csv",
    baseline=base.WORKSPACE,
    baseline_report=base.OUTPUT / "resumo_busca_local_200k.json",
    dump=local.DEFAULT_DESTINATION / "lrclib-db-dump-20261012T090639Z.sqlite3",
    old_indexes=(local.DEFAULT_INDEX, base.INDEX),
    workspace=WORKSPACE,
    output=OUTPUT,
    index_dir=INDEX,
    retry=False,
    limit=None,
    expected=200_000,
):
    started = time.monotonic()
    baseline, workspace, output, index_dir, dump = [
        Path(p).resolve() for p in (baseline, workspace, output, index_dir, dump)
    ]
    sample_path, sample_summary, allocation, baseline_report = [
        Path(p).resolve() for p in (sample_path, sample_summary, allocation, baseline_report)
    ]
    old_indexes = [Path(p).resolve() for p in old_indexes]
    inputs = [baseline, baseline_report.parent, sample_path.parent, *old_indexes]
    destinations = [workspace, output, index_dir]
    require(
        all(
            not (a == b or a.is_relative_to(b) or b.is_relative_to(a))
            for i, a in enumerate(destinations)
            for b in destinations[i + 1 :] + inputs
        ),
        "Destinos devem ser separados e não sobrepor entradas.",
    )
    require(
        workspace.is_relative_to(ROOT / "data/derived") or expected != 200_000,
        "Workspace privado deve ficar sob data/derived.",
    )
    require(not dump.is_relative_to(index_dir), "Índice novo não pode sobrepor dump.")
    print("[1/6] Validando amostra e busca anterior; nenhuma escrita na v1...", flush=True)
    sample, _ = base.validate_sample(sample_path, sample_summary, allocation, expected=expected)
    previous = json.loads(baseline_report.read_text(encoding="utf-8"))
    require(
        previous["completed"] and previous["sample_sha256"] == sha256(sample_path),
        "Busca v1 incompleta ou de outra amostra.",
    )
    prior = pl.read_parquet(baseline / "resultados_faixas_200k.parquet")
    require(
        prior.height == expected
        and prior["track_id"].n_unique() == expected
        and prior.select(sample.columns).sort("track_id").equals(sample.sort("track_id")),
        "Resultado v1 não preserva a amostra.",
    )
    observed_counts = dict(prior.group_by("lyrics_status").len().iter_rows())
    require(
        observed_counts == previous["status_counts"]
        and not any(observed_counts.get(s, 0) for s in ("pending", "technical_error")),
        "Contagens v1 divergem.",
    )
    if expected == 200_000:
        require(
            observed_counts
            == {
                "accepted": 77391,
                "ambiguous": 25775,
                "not_found": 88049,
                "instrumental": 8748,
                "no_text": 10,
                "insufficient_metadata": 27,
            },
            "Baseline real diferente do protocolo.",
        )
    identity = local.checked_dump(dump)
    require(identity == previous["source"], "Dump diferente da busca v1.")
    queries, tracks = make_queries(sample)
    detector, language = base.language_detector()
    state_path = baseline / "state.sqlite"
    state_stamp = file_stamp(state_path)
    with ExitStack() as stack:
        old = stack.enter_context(closing(base.stable_readonly(state_path)))
        old_seal = meta_get(old, "seal")
        require(
            old_seal["source"] == identity
            and old_seal["sample_sha256"] == previous["sample_sha256"],
            "Selo v1 incompatível.",
        )
        require(
            dict(old.execute("SELECT track_id,query_id FROM tracks"))
            == dict(prior.select("track_id", "lyrics_query_id").iter_rows()),
            "Mapa v1 diverge do Parquet.",
        )
        indexes = []
        for path in old_indexes:
            index = stack.enter_context(closing(base.stable_readonly(path / "lookup.sqlite")))
            require(
                meta_get(index, "seal")["dump"] == identity
                and meta_get(index, "progress")["complete"],
                "Índice anterior incompatível/incompleto.",
            )
            indexes.append(index)
        code_files = [
            Path(__file__),
            PROTOCOL,
            Path(base.__file__),
            Path(local.__file__),
            ROOT / "src/tcc_music_popularity/normalization.py",
            ROOT / "src/tcc_music_popularity/lyrics_ambiguity_v011.py",
            ROOT / "src/tcc_music_popularity/lyrics_pilot.py",
            ROOT / "src/tcc_music_popularity/catalog_sampling.py",
            ROOT / "src/tcc_music_popularity/catalog_audit.py",
            ROOT / "src/tcc_music_popularity/manual_lyrics.py",
            ROOT / "src/tcc_music_popularity/lyrics_embeddings_v020.py",
        ]
        seal = {
            "version": VERSION,
            "workspace": str(workspace),
            "output": str(output),
            "index_dir": str(index_dir),
            "sample_sha256": sha256(sample_path),
            "sample_summary_sha256": sha256(sample_summary),
            "allocation_sha256": sha256(allocation),
            "baseline_report_sha256": sha256(baseline_report),
            "baseline_result_sha256": sha256(baseline / "resultados_faixas_200k.parquet"),
            "baseline_state_stamp": state_stamp,
            "baseline_state_sha256": sha256(state_path),
            "baseline_seal": old_seal,
            "source": identity,
            "language": language,
            "code": {p.name: sha256(p) for p in code_files},
        }
        owner = {"version": VERSION, "seal": fingerprint(seal)}
        if output.exists():
            require(
                (output / "owner.json").is_file()
                and json.loads((output / "owner.json").read_text()) == owner,
                "Pasta pública incompatível; preservada.",
            )
        else:
            output.mkdir(parents=True)
            atomic_json(output / "owner.json", owner)
        with exclusive(workspace), closing(base.state_connection(workspace)) as db:
            summary = {
                "version": VERSION,
                "completed": False,
                "status": "incomplete",
                "started_at": utc_now(),
                "source": identity,
                "input_hashes": {k: v for k, v in seal.items() if k.endswith("sha256")},
                "code_hashes": seal["code"],
                "language": language,
                "http_requests": 0,
                "sample_rows": expected,
                "checks": {},
                "command": [sys.executable, *sys.argv],
            }
            atomic_json(output / "resumo_recuperacao_letras_200k.json", summary)
            run = {
                "started_at": utc_now(),
                "cache_seconds": 0,
                "index_seconds": 0,
                "search_seconds": 0,
                "new_local_queries": 0,
            }
            try:
                print("[2/6] Diagnóstico inicial e preservação das decisões v1...", flush=True)
                diagnostics = initial_diagnostics(prior, indexes)
                initialize(db, old, seal, queries, tracks, prior, diagnostics)
                summary["initial_diagnostics"] = counts(
                    prior.join(diagnostics, on="track_id"),
                    ["lyrics_status", "recovery_initial_diagnostic"],
                )
                atomic_json(output / "resumo_recuperacao_letras_200k.json", summary)
                done_before = db.execute(
                    "SELECT count(*) FROM recovery WHERE phase='done'"
                ).fetchone()[0]
                print("[3/6] Reavaliando candidatos guardados, com checkpoints...", flush=True)
                run["cache_seconds"] = cache_pass(db, old, workspace, identity, detector)
                run["new_cache_decisions"] = (
                    db.execute("SELECT count(*) FROM recovery WHERE phase='done'").fetchone()[0]
                    - done_before
                )
                run["reused_decisions"] = done_before
                artists = meta_get(db, "lookup_artists")
                if artists is None:
                    artists = sorted(
                        {
                            profile(
                                json.loads(row[0])["artist_name_query"],
                                json.loads(row[0])["track_name_query"],
                            )["artist"]
                            for row in db.execute(
                                "SELECT q.data FROM queries q JOIN recovery r USING(query_id) WHERE phase='lookup'"
                            )
                        }
                    )
                    with db:
                        meta_put(db, "lookup_artists", artists)
                print(
                    f"[4/6] Índice auxiliar de recuperação: {len(artists)} chaves de artista; uma passagem retomável...",
                    flush=True,
                )
                if artists:
                    tick = time.monotonic()
                    summary["index"] = build_index(dump, index_dir, artists, identity)
                    run["index_seconds"] = time.monotonic() - tick
                    with (
                        closing(base.stable_readonly(dump)) as source,
                        closing(base.stable_readonly(index_dir / "lookup.sqlite")) as index,
                    ):
                        run["new_local_queries"], run["search_seconds"] = search_pass(
                            db,
                            source,
                            index,
                            workspace,
                            identity,
                            detector,
                            retry=retry,
                            limit=limit,
                        )
                print(
                    "[5/6] Exportando resultados privados e amostra dirigida para inspeção...",
                    flush=True,
                )
                final, texts, review = export_private(db, sample, prior, diagnostics, workspace)
                summary.update(private_text_rows=texts, private_review_rows=review)
                summary["checks"] = {
                    "sample_unchanged": sha256(sample_path) == seal["sample_sha256"],
                    "baseline_state_unchanged": file_stamp(state_path) == state_stamp,
                    "baseline_result_unchanged": sha256(baseline / "resultados_faixas_200k.parquet")
                    == seal["baseline_result_sha256"],
                    "one_row_per_track_and_weights_preserved": True,
                    "previous_accepted_and_instrumental_preserved": True,
                    "text_hashes_references_valid": True,
                }
                require(all(summary["checks"].values()), "Verificação de integridade falhou.")
                print("[6/6] Gerando transições, comparação ponderada e relatório...", flush=True)
                run["elapsed_seconds"] = time.monotonic() - started
                with db:
                    db.execute("INSERT INTO runs(data) VALUES (?)", (json.dumps(run),))
                summary["runs"] = [
                    json.loads(r[0]) for r in db.execute("SELECT data FROM runs ORDER BY id")
                ]
                summary["invocation_elapsed_seconds"] = time.monotonic() - started
                publish(final, prior, output, summary)
                summary["invocation_elapsed_seconds"] = time.monotonic() - started
                atomic_json(output / "resumo_recuperacao_letras_200k.json", summary)
                progress(db, workspace, summary["status"], started)
                return 0 if summary["completed"] else 2
            except BaseException as exc:
                summary.update(
                    status="incomplete",
                    completed=False,
                    error_type=type(exc).__name__,
                    invocation_elapsed_seconds=time.monotonic() - started,
                )
                atomic_json(output / "resumo_recuperacao_letras_200k.json", summary)
                raise


def cli(argv=None):
    parser = argparse.ArgumentParser(
        description="Uma rodada offline de recuperação 200k, preservando v1; execução real somente pelo pesquisador."
    )
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--retry-errors", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--index-dir", type=Path, default=INDEX)
    args = parser.parse_args(argv)
    if args.status:
        checkpoints = {}
        for name, path in (
            ("workspace", args.workspace / "progress.json"),
            ("index", args.index_dir / "progress.json"),
        ):
            if path.exists():
                checkpoints[name] = json.loads(path.read_text(encoding="utf-8"))
        print(
            json.dumps(checkpoints, ensure_ascii=False, indent=2)
            if checkpoints
            else "Ainda não inicializado."
        )
        return 0
    if not args.all and args.limit is None:
        parser.error("Informe --all ou --limit N; --status somente lê o checkpoint.")
    try:
        require(args.limit is None or args.limit > 0, "--limit deve ser positivo.")
        return execute(
            workspace=args.workspace,
            output=args.output,
            index_dir=args.index_dir,
            retry=args.retry_errors,
            limit=args.limit,
        )
    except KeyboardInterrupt:
        print("Interrompido. Repita o comando; checkpoints preservados.", file=sys.stderr)
        return 2
    except Exception as exc:
        print(
            f"Falha ({type(exc).__name__}): "
            + (
                str(exc)
                if isinstance(exc, ValueError)
                else "confira caminhos/SSD/espaço; estado preservado"
            ),
            file=sys.stderr,
        )
        return 1
