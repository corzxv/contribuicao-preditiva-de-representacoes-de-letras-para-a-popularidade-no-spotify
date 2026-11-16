"""Piloto online para medir a recuperação adicional nas pendências sem candidato."""

import argparse
import http.client
import json
import math
import random
import sqlite3
import time
from collections import Counter
from contextlib import closing
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode

import polars as pl

from . import lyrics_artist_review as artist
from .manual_lyrics import atomic_json, exclusive, fingerprint, meta_get, meta_put, require

design, local, revision = artist.design, artist.local, artist.revision
VERSION = "piloto-online-pendencias-v1"
WORKSPACE = design.ROOT / "data/derived/private_piloto_online_nova_amostra_v1"
OUTPUT = design.ROOT / "reports/piloto_online_nova_amostra_v1"
HOST = "lrclib.net"
ENDPOINT = "/api/search"
USER_AGENT = (
    "TCC-popularidade-musical-piloto/1.0 (https://github.com/corzxv/tcc-popularidade-musical)"
)
SEED, SIZE = 20261107, 100
RESPONSE_LIMIT, BODY_LIMIT = 20, 8 * 1024**2
DURATION_LIMIT, DELAY, TIMEOUT = 2.0, 0.5, 15
FIELDS = (
    "id",
    "trackName",
    "artistName",
    "albumName",
    "duration",
    "instrumental",
    "plainLyrics",
    "syncedLyrics",
)


def plan():
    source = artist.OUTPUT / "resumo_revisao_variantes_artista.json"
    coverage = (
        design.ROOT
        / "reports/cobertura_pos_revisao_variantes_nova_amostra_v1/resumo_cobertura.json"
    )
    prior, counts = map(design.read_json, (source, coverage))
    state = revision.WORKSPACE / "state.sqlite"
    state_hash, source_hash = design.sha256(state), design.sha256(source)
    links = artist.WORKSPACE / "novos_vinculos.parquet"
    require(
        prior["completed"]
        and counts["completed"]
        and state_hash == prior["seal"]["source43_state_sha256"]
        and source_hash == counts["source48_summary_sha256"]
        and design.sha256(links) == prior["private_sha256"][links.name],
        "Fonte ou vínculos da recuperação local divergentes.",
    )
    removed = set(pl.read_parquet(links, columns=["track_id"])["track_id"])
    with closing(local.base.stable_readonly(state)) as old:
        rows = {
            track_id: (key, data)
            for track_id, key, data in old.execute(
                "SELECT track_id,query_id,data FROM tracks JOIN queries USING(query_id) WHERE status='not_found'"
            )
        }
    require(
        len(removed) == prior["new_accepted_tracks"] and removed <= rows.keys(),
        "Vínculos 48 fora das pendências de origem.",
    )
    eligible = sorted(rows.keys() - removed)
    require(
        len(eligible) == counts["counts"]["not_found"] and len(eligible) >= SIZE,
        "Universo do piloto divergente.",
    )
    selected = random.Random(SEED).sample(eligible, SIZE)
    jobs = {}
    for track_id in selected:
        key, raw = rows[track_id]
        query = json.loads(raw)
        require(
            fingerprint(query) == key and set(query) <= local.base.MATCH_FIELDS,
            "Consulta fora do protocolo.",
        )
        jobs.setdefault(key, {"query": query, "track_ids": []})["track_ids"].append(track_id)
    return {
        "version": VERSION,
        "seed": SEED,
        "universe_tracks": len(eligible),
        "sample_tracks": len(selected),
        "sample_queries": len(jobs),
        "source43_state_sha256": state_hash,
        "source48_summary_sha256": source_hash,
        "coverage_sha256": design.sha256(coverage),
        "code_sha256": design.sha256(Path(__file__)),
        "endpoint": f"https://{HOST}{ENDPOINT}",
        "jobs": jobs,
    }


def request(query):
    parameters = {
        "track_name": query["track_name_query"],
        "artist_name": query["artist_name_query"],
    }
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    with closing(http.client.HTTPSConnection(HOST, timeout=TIMEOUT)) as client:
        client.request("GET", f"{ENDPOINT}?{urlencode(parameters)}", headers=headers)
        with client.getresponse() as response:
            body = response.read(BODY_LIMIT + 1) if response.status == 200 else None
            return response.status, response.getheader("Retry-After"), body


def retry_delay(value, now):
    try:
        return max(DELAY, int(value))
    except (ValueError, TypeError):
        try:
            return max(DELAY, parsedate_to_datetime(value).timestamp() - now)
        except (ValueError, TypeError, OverflowError):
            return 60


def classify_response(query, payload):
    require(isinstance(payload, list), "O retorno da busca deve ser uma lista.")
    details = {"returned": len(payload)}
    if len(payload) >= RESPONSE_LIMIT:
        return {**details, "outcome": "limite_da_busca"}, None
    if not payload:
        return {**details, "outcome": "sem_resultados"}, None
    eligible = []
    for item in payload:
        require(
            isinstance(item, dict)
            and all(field in item for field in FIELDS)
            and type(item["id"]) is int
            and type(item["instrumental"]) is bool
            and all(
                item[k] is None or isinstance(item[k], str)
                for k in FIELDS
                if k not in {"id", "duration", "instrumental"}
            )
            and all(
                isinstance(item[k], str) and item[k].strip() for k in ("trackName", "artistName")
            )
            and type(item["duration"]) in {int, float}
            and math.isfinite(item["duration"]),
            "Estrutura inesperada no candidato da API.",
        )
        delta = local.recovery.duration_delta(query, item)
        if delta is not None and delta <= DURATION_LIMIT and revision.compatible(query, item):
            # A API expõe o ID do registro, sem o ID separado da letra no dump.
            eligible.append({**{k: item[k] for k in FIELDS}, "local_lyrics_id": None})
    details.update(
        compatible=len(eligible),
        eligible_sha256=fingerprint(eligible),
        candidates=[
            {key: item[key] for key in ("id", "trackName", "artistName", "albumName", "duration")}
            for item in eligible
        ],
    )
    if not eligible:
        return {**details, "outcome": "sem_candidato_compativel"}, None
    outcome, text = artist.review_text(query, eligible)
    if text:
        text["rules_version"] = VERSION
        return {**details, "outcome": "candidata_provisoria"}, text
    return {**details, "outcome": outcome}, None


def query_once(query, fetch):
    try:
        status, after, raw = fetch(query)
        if status == 400:
            return {"outcome": "consulta_recusada", "http_status": status}, None, None
        if status != 200:
            return None, None, (f"HTTP {status}", retry_delay(after, time.time()))
        require(
            isinstance(raw, bytes) and len(raw) <= BODY_LIMIT, "Resposta excede o limite do piloto."
        )
        decision, text = classify_response(query, json.loads(raw))
        return (
            {**decision, "http_status": status, "response_sha256": sha256(raw).hexdigest()},
            text,
            None,
        )
    except (OSError, http.client.HTTPException, ValueError, OverflowError) as exc:
        return None, None, (type(exc).__name__, 60)


def collect(db, manifest, fetch):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS decisions(query_id TEXT PRIMARY KEY,result TEXT NOT NULL,text TEXT);
    """)
    seal = fingerprint(manifest)
    if meta_get(db, "manifest") is None:
        require(
            db.execute("SELECT count(*) FROM decisions").fetchone()[0] == 0,
            "Checkpoint sem manifesto.",
        )
        with db:
            meta_put(db, "manifest", seal)
    require(meta_get(db, "manifest") == seal, "Checkpoint pertence a outro manifesto.")
    jobs = manifest["jobs"]
    decisions = dict(
        (key, json.loads(result))
        for key, result in db.execute("SELECT query_id,result FROM decisions")
    )
    require(decisions.keys() <= jobs.keys(), "Checkpoint inclui consulta fora do piloto.")
    print(
        f"Piloto de {manifest['sample_tracks']} faixas. {len(decisions)} consultas reaproveitadas.",
        flush=True,
    )
    pause = meta_get(db, "pause")
    for key, job in jobs.items():
        if key in decisions:
            continue
        if pause and pause["retry_at"] > time.time():
            break
        result, text, failed = query_once(job["query"], fetch)
        if failed:
            reason, wait = failed
            pause = {"reason": reason, "retry_at": time.time() + wait}
            with db:
                meta_put(db, "pause", pause)
            break
        pause = None
        result["queried_at"] = datetime.now(UTC).isoformat()
        with db:
            db.execute(
                "INSERT INTO decisions VALUES(?,?,?)",
                (key, json.dumps(result), json.dumps(text, ensure_ascii=False) if text else None),
            )
            meta_put(db, "pause", None)
        decisions[key] = result
        if len(decisions) % 10 == 0:
            print(f"{len(decisions)}/{len(jobs)} consultas concluídas.", flush=True)
        if len(decisions) < len(jobs):
            time.sleep(DELAY)
    return decisions, pause


def run(*, fetch=request):
    with exclusive(WORKSPACE):
        path = WORKSPACE / "manifesto.json"
        require(path.is_file(), "Manifesto ausente. Execute --preparar.")
        manifest = design.read_json(path)
        require(manifest == plan(), "Manifesto ou fontes locais divergentes.")
        with closing(sqlite3.connect(WORKSPACE / "state.sqlite")) as db:
            decisions, pause = collect(db, manifest, fetch)
        jobs = manifest["jobs"]
        outcomes = Counter()
        for key, result in decisions.items():
            outcomes[result["outcome"]] += len(jobs[key]["track_ids"])
        report = {
            "completed": len(decisions) == len(jobs),
            "universe_tracks": manifest["universe_tracks"],
            "sample_tracks": manifest["sample_tracks"],
            "sample_queries": len(jobs),
            "completed_queries": len(decisions),
            "pending_tracks": manifest["sample_tracks"] - sum(outcomes.values()),
            "outcomes_by_track": dict(outcomes),
            "provisional_tracks": outcomes["candidata_provisoria"],
            "new_confirmed_tracks": 0,
            "pause": pause,
            "manifest_sha256": design.sha256(path),
            "endpoint": manifest["endpoint"],
            "state_sha256": design.sha256(WORKSPACE / "state.sqlite"),
        }
        atomic_json(OUTPUT / "resumo_piloto_online.json", report)
    return report


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preparar", action="store_true", help="Sela o sorteio local sem consultar a API."
    )
    args = parser.parse_args(argv)
    if args.preparar:
        with exclusive(WORKSPACE):
            path = WORKSPACE / "manifesto.json"
            manifest = plan()
            if path.exists():
                require(
                    design.read_json(path) == manifest,
                    "Já existe outro manifesto. Preserve a seleção anterior.",
                )
            else:
                atomic_json(path, manifest)
        print(f"Seleção fixa: {manifest['sample_tracks']} de {manifest['universe_tracks']} faixas.")
        return 0
    try:
        report = run()
    except KeyboardInterrupt:
        print("Interrompido. Repita o comando para retomar as consultas pendentes.")
        return 2
    if report["pause"]:
        resume_at = datetime.fromtimestamp(report["pause"]["retry_at"]).astimezone()
        print(
            f"Pausa por {report['pause']['reason']}. Retome após {resume_at:%H:%M:%S %Z}.",
            flush=True,
        )
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "completed",
                    "sample_tracks",
                    "pending_tracks",
                    "provisional_tracks",
                    "outcomes_by_track",
                )
            }
        )
    )
    return 0 if report["completed"] else 2
