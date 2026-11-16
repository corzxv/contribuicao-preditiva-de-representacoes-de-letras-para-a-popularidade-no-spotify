"""Diagnóstico de metadados das consultas sem candidato; não aceita letras."""

import argparse
import json
import re
import sqlite3
import sys
import time
from collections import Counter
from contextlib import closing
from pathlib import Path

from . import lyrics_matching_revision as revision
from . import new_sample_local as local
from . import sample_redesign as design
from .manual_lyrics import atomic_json, exclusive, meta_get, meta_put, require
from .normalization import conservative_normalize

ROOT = design.ROOT
VERSION = "native-lookup-audit-v1"
WORKSPACE = ROOT / "data/derived/private_diagnostico_chaves_nova_amostra_v1"
OUTPUT = ROOT / "reports/diagnostico_chaves_nova_amostra_v1"
MAX_ROWS = 100
MAX_SAVED = 50
BUDGET_SECONDS = 2.0
FIELDS = "id,name,artist_name,album_name,duration,last_lyrics_id"
TITLE_SQL = f"SELECT {FIELDS} FROM tracks INDEXED BY idx_tracks_name_lower WHERE name_lower=? AND duration BETWEEN ? AND ? ORDER BY id LIMIT ?"
ARTIST_SQL = f"SELECT {FIELDS} FROM tracks INDEXED BY idx_tracks_artist_name_lower WHERE artist_name_lower=? AND duration BETWEEN ? AND ? ORDER BY id LIMIT ?"
FTS_SQL = "SELECT t.id,t.name,t.artist_name,t.album_name,t.duration,t.last_lyrics_id FROM tracks_fts JOIN tracks t ON t.id=tracks_fts.rowid WHERE tracks_fts MATCH ? AND t.duration BETWEEN ? AND ? ORDER BY tracks_fts.rowid LIMIT ?"


def fts_expression(title, artist):
    title_terms = re.findall(r"\w+", title.lower())
    artist_terms = re.findall(r"\w+", artist.lower())
    if not title_terms or not artist_terms or len(title_terms) > 24 or len(artist_terms) > 12:
        return None
    return (
        'name_lower : "'
        + " ".join(title_terms)
        + '" AND artist_name_lower : ('
        + " AND ".join('"' + t + '"' for t in artist_terms)
        + ")"
    )


def validate_access(source):
    plans = {}
    for method, sql in [("exact_title", TITLE_SQL), ("exact_artist", ARTIST_SQL), ("fts", FTS_SQL)]:
        key = 'name_lower : "fixture"' if method == "fts" else "fixture"
        plan = " ".join(
            str(tuple(r))
            for r in source.execute("EXPLAIN QUERY PLAN " + sql, (key, 0, 1, MAX_ROWS + 1))
        )
        upper = plan.upper()
        if method == "fts":
            require(
                "VIRTUAL TABLE INDEX" in upper and "PRIMARY KEY" in upper,
                "FTS não usa índice textual e acesso por ID.",
            )
        else:
            require(
                "SEARCH" in upper and "SCAN" not in upper, "Consulta nativa sem índice: " + method
            )
        plans[method] = plan
    return plans


def metadata_flags(query, candidate):
    p = local.recovery.profile(query["artist_name_query"], query["track_name_query"])
    c = local.recovery.profile(candidate["artist_name"], candidate["name"])
    mapped = {
        "artistName": candidate["artist_name"],
        "trackName": candidate["name"],
        "duration": candidate["duration"],
    }
    same_artist = p["artist"] == c["artist"]
    conservative_artist = conservative_normalize(p["artist"]) == conservative_normalize(c["artist"])
    same_title = p["title"] == c["title"]
    same_context = all(p[k] == c[k] for k in ("guests", "versions"))
    return {
        "strict_profile_compatible": revision.compatible(query, mapped),
        "artist_key_variant": not same_artist
        and conservative_artist
        and same_title
        and same_context,
        "same_artist_other_title": same_artist and not same_title,
        "same_title_other_artist": same_title and not conservative_artist,
        "has_lyrics_reference": candidate["last_lyrics_id"] is not None,
    }


def audit_query(source, query):
    require(set(query) <= local.base.MATCH_FIELDS, "Campo proibido no diagnóstico.")
    duration = query.get("duration_seconds")
    require(duration is not None and duration > 0, "Duração ausente; diagnosticar separadamente.")
    low, high = duration - local.base.TOLERANCE, duration + local.base.TOLERANCE
    profile = local.recovery.profile(query["artist_name_query"], query["track_name_query"])
    methods = [
        ("exact_title", TITLE_SQL, query["track_name_query"].lower()),
        ("exact_artist", ARTIST_SQL, query["artist_name_query"].lower()),
    ]
    expressions = []
    for label, title in [
        ("fts_full_title", query["track_name_query"]),
        ("fts_core_title", profile["title"]),
    ]:
        expression = fts_expression(title, profile["artist"])
        if expression and expression not in expressions:
            expressions.append(expression)
            methods.append((label, FTS_SQL, expression))
    deadline = time.monotonic() + BUDGET_SECONDS
    candidates, methods_info = {}, []
    source.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
    try:
        for method, sql, value in methods:
            if time.monotonic() >= deadline:
                methods_info.append(
                    {"method": method, "status": "budget_exhausted", "truncated": True}
                )
                continue
            try:
                rows = source.execute(sql, (value, low, high, MAX_ROWS + 1)).fetchall()
            except sqlite3.OperationalError as exc:
                if "interrupted" not in str(exc).lower():
                    raise
                methods_info.append({"method": method, "status": "timeout", "truncated": True})
                continue
            methods_info.append(
                {
                    "method": method,
                    "status": "ok",
                    "n_capped": min(len(rows), MAX_ROWS),
                    "truncated": len(rows) > MAX_ROWS,
                }
            )
            for raw in rows[:MAX_ROWS]:
                row = dict(raw)
                key = row["id"]
                if key not in candidates:
                    row.update(metadata_flags(query, row), methods=[])
                    candidates[key] = row
                candidates[key]["methods"].append(method)
    finally:
        source.set_progress_handler(None, 0)
    flags = {
        name: any(c[name] for c in candidates.values())
        for name in (
            "strict_profile_compatible",
            "artist_key_variant",
            "same_artist_other_title",
            "same_title_other_artist",
            "has_lyrics_reference",
        )
    }
    label = "no_candidates_under_these_methods"
    for name in [
        "strict_profile_compatible",
        "artist_key_variant",
        "same_artist_other_title",
        "same_title_other_artist",
    ]:
        if flags[name]:
            label = name
            break
    if candidates and label == "no_candidates_under_these_methods":
        label = "other_metadata_candidates"
    ranked = sorted(
        candidates.values(),
        key=lambda c: (
            -int(c["strict_profile_compatible"]),
            -int(c["artist_key_variant"]),
            -int(c["same_artist_other_title"]),
            -int(c["same_title_other_artist"]),
            abs(float(c["duration"]) - duration),
            c["id"],
        ),
    )
    return {
        "diagnostic_label": label,
        "candidate_count_union_capped": len(candidates),
        "candidate_records_saved": min(len(ranked), MAX_SAVED),
        "flags": flags,
        "methods": methods_info,
        "incomplete_methods": any(m["truncated"] for m in methods_info),
        "long_or_empty_fts_form_skipped": len(expressions) == 0,
        "candidates": ranked[:MAX_SAVED],
        "new_acceptances": 0,
        "lyrics_read": False,
    }


def run(
    *,
    source_workspace=revision.WORKSPACE,
    source_summary=revision.OUTPUT / "resumo_revisao_matching.json",
    dump=local.DUMP,
    workspace=WORKSPACE,
    output=OUTPUT,
    limit=None,
):
    source_workspace, source_summary, dump, workspace, output = map(
        Path, [source_workspace, source_summary, dump, workspace, output]
    )
    require(
        workspace.resolve() != source_workspace.resolve(), "Diagnóstico precisa de pasta separada."
    )
    print("[1/3] Conferindo 43 e índices nativos; sem alteração de letras/status...", flush=True)
    prior = design.read_json(source_summary)
    require(prior["completed"], "Revisão 43 incompleta.")
    require(
        prior["seal"]["code_sha256"] == design.sha256(Path(revision.__file__)),
        "Código 43 selado mudou.",
    )
    for name, value in prior["private_sha256"].items():
        require(design.sha256(source_workspace / name) == value, "Saída 43 alterada: " + name)
    identity = local.recovery.local.checked_dump(dump)
    require(identity == prior["seal"]["dump"], "Dump difere de 43.")
    path = source_workspace / "state.sqlite"
    stamp = local.cache.stamp(path)
    seal = {
        "version": VERSION,
        "source_summary_sha256": design.sha256(source_summary),
        "state43_sha256": design.sha256(path),
        "code_sha256": design.sha256(Path(__file__)),
        "dump": identity,
    }
    output.mkdir(parents=True, exist_ok=True)
    with (
        exclusive(workspace),
        closing(local.base.stable_readonly(path)) as old,
        closing(local.base.stable_readonly(dump)) as source,
        closing(sqlite3.connect(workspace / "state.sqlite")) as db,
    ):
        plans = validate_access(source)
        db.executescript(
            "CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL); CREATE TABLE IF NOT EXISTS diagnostics(query_id TEXT PRIMARY KEY,data TEXT NOT NULL,result TEXT NOT NULL);"
        )
        saved = meta_get(db, "seal")
        if saved is None:
            require(
                db.execute("SELECT count(*) FROM diagnostics").fetchone()[0] == 0,
                "Checkpoint sem selo.",
            )
            with db:
                meta_put(db, "seal", seal)
        else:
            require(saved == seal, "Fontes/código mudaram; preservar diagnóstico anterior.")
        targets = {
            key: json.loads(raw)
            for key, raw in old.execute(
                "SELECT query_id,data FROM queries WHERE status='not_found' ORDER BY query_id"
            )
        }
        stored = {}
        for key, raw, result in db.execute("SELECT query_id,data,result FROM diagnostics"):
            require(
                key in targets and json.loads(raw) == targets[key],
                "Diagnóstico fora das consultas previstas.",
            )
            stored[key] = json.loads(result)
        pending = [key for key in targets if key not in stored]
        if limit is not None:
            pending = pending[:limit]
        print(
            f"[2/3] {len(pending)} diagnósticos por índices prontos; nenhuma aceitação automática...",
            flush=True,
        )
        started, last = time.monotonic(), 0.0
        for number, key in enumerate(pending, start=1):
            result = audit_query(source, targets[key])
            with db:
                db.execute(
                    "INSERT INTO diagnostics VALUES (?,?,?)",
                    (
                        key,
                        json.dumps(targets[key], ensure_ascii=False),
                        json.dumps(result, ensure_ascii=False),
                    ),
                )
            stored[key] = result
            if time.monotonic() - last >= 10:
                value = {
                    "etapa": "diagnostico_metadados",
                    "novas_consultas": number,
                    "diagnosticos_concluidos": len(stored),
                    "total": len(targets),
                    "segundos": time.monotonic() - started,
                }
                atomic_json(workspace / "progress.json", value)
                print(json.dumps(value), flush=True)
                last = time.monotonic()
        require(local.cache.stamp(path) == stamp, "Checkpoint 43 foi alterado.")
        require(local.recovery.local.checked_dump(dump) == identity, "Dump foi alterado.")
        counts = Counter(r["diagnostic_label"] for r in stored.values())
        design.write_csv(
            output / "categorias_diagnostico.csv",
            [{"diagnostico": k, "n": v} for k, v in sorted(counts.items())],
        )
        result = {
            "completed": len(stored) == len(targets),
            "version": VERSION,
            "targets": len(targets),
            "diagnosed": len(stored),
            "diagnostic_counts": dict(counts),
            "incomplete_methods": sum(r["incomplete_methods"] for r in stored.values()),
            "prior_accepted": prior["status_counts"]["accepted"],
            "new_accepted": 0,
            "source_statuses_changed": False,
            "lyrics_read": False,
            "indices_created": False,
            "seal": seal,
            "access_plans": plans,
            "seconds": time.monotonic() - started,
            "candidates_are_review_suggestions": True,
            "scope": "Candidatos de metadados por métodos limitados; não letras aceitas, ausência comprovada ou aliases validados.",
            "public_sha256": {
                "categorias_diagnostico.csv": design.sha256(output / "categorias_diagnostico.csv")
            },
        }
        atomic_json(output / "resumo_diagnostico_chaves.json", result)
        atomic_json(
            workspace / "progress.json",
            {
                "etapa": "concluido" if result["completed"] else "parcial",
                "diagnostic_counts": dict(counts),
            },
        )
    print(
        json.dumps({"etapa": "resumo_diagnostico", "categorias": dict(counts), "novas_aceitas": 0}),
        flush=True,
    )
    print(
        f"[3/3] {'Concluído' if result['completed'] else 'Parcial; retomar'}; agregados em {output}",
        flush=True,
    )
    return result


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", action="store_true", help="Lê apenas o progresso salvo.")
    parser.add_argument(
        "--limit-queries", type=int, help="Limita diagnósticos e preserva retomada."
    )
    args = parser.parse_args(argv)
    if args.status:
        path = WORKSPACE / "progress.json"
        print(
            path.read_text(encoding="utf-8") if path.exists() else "Diagnóstico ainda não iniciado."
        )
        return 0
    if args.limit_queries is not None and args.limit_queries < 1:
        parser.error("Limite precisa ser positivo.")
    try:
        result = run(limit=args.limit_queries)
    except KeyboardInterrupt:
        print("Interrompido; retome com o mesmo comando. Resultados 43 intactos.", file=sys.stderr)
        return 2
    return 0 if result["completed"] else 2
