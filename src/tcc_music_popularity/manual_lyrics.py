"""Orquestração manual, privada e retomável; regras científicas importadas do projeto."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sqlite3
import subprocess
from collections import Counter
from contextlib import closing, contextmanager
from pathlib import Path

import polars as pl

from .config import PROJECT_ROOT, load_yaml
from .final_study_v040 import (
    FORBIDDEN_SAMPLING_COLUMNS,
    load_target_free_source,
    select_representatives_without_target,
)
from .io import sha256_file, utc_now
from .lyrics_pilot import VERSION_FLAGS, LRCLIBClient, _version_flags, pilot_base_title
from .lyrics_pilot_v012 import ACCEPTED_STATUSES, classify_cached_composition_v012
from .lyrics_pilot_v013 import circuit_breaker_reason
from .lyrics_scale_v040 import cache_is_compatible

ROOT = PROJECT_ROOT
DEFAULT_WORKSPACE = ROOT / "data/derived/private_manual_lyrics_v1"
CONFIG = ROOT / "configs/final_scale_v0_4.yaml"
HISTORY_COLUMNS = (
    "composition_key",
    "track_id",
    "representative_track_id",
    "final_status",
    "status",
    "reclassified_status",
    "selected_strict_text_sha256",
    "lyrics_sha256",
)


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    temporary.replace(path)


def atomic_frame(path, frame):
    temporary = path.with_suffix(".parquet.tmp")
    frame.write_parquet(temporary)
    temporary.replace(path)


@contextmanager
def exclusive(workspace):
    """O sistema libera o bloqueio mesmo após Ctrl+C ou queda do processo."""
    workspace.mkdir(parents=True, exist_ok=True)
    with (workspace / "execution.lock").open("a+b") as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError(
                "Outro script está usando este workspace. Aguarde seu término."
            ) from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def connect(workspace, *, readonly=False):
    path = workspace / "state.sqlite"
    if readonly:
        require(path.is_file(), "Execute primeiro 01_preparar_universo_letras.py.")
        db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    else:
        db = sqlite3.connect(path)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
    db.row_factory = sqlite3.Row
    return db


def init_db(db):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tracks (track_id TEXT PRIMARY KEY, query_id TEXT, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS queries (
            query_id TEXT PRIMARY KEY, composition_key TEXT NOT NULL, data TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'not_queried', retryable INTEGER NOT NULL DEFAULT 0,
            result TEXT, cache_path TEXT, cache_sha256 TEXT, attempts INTEGER NOT NULL DEFAULT 0);
        CREATE INDEX IF NOT EXISTS query_status ON queries(status, retryable);
        CREATE TABLE IF NOT EXISTS cache_inventory (
            path TEXT PRIMARY KEY, composition_key TEXT, sha256 TEXT, valid INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS cache_composition ON cache_inventory(composition_key);
        CREATE TABLE IF NOT EXISTS history (
            source TEXT NOT NULL, ordinal INTEGER NOT NULL, composition_key TEXT, data TEXT,
            PRIMARY KEY(source, ordinal));
        CREATE INDEX IF NOT EXISTS history_composition ON history(composition_key);
        CREATE TABLE IF NOT EXISTS attempts (
            query_id TEXT, number INTEGER, cache_path TEXT, status TEXT,
            PRIMARY KEY(query_id,number));
        CREATE TABLE IF NOT EXISTS vectors (
            lyrics_sha256 TEXT PRIMARY KEY, config_sha256 TEXT NOT NULL, vector BLOB NOT NULL,
            vector_sha256 TEXT NOT NULL, metadata TEXT NOT NULL, origin TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS embedding_links (
            query_id TEXT PRIMARY KEY, lyrics_sha256 TEXT NOT NULL, strict_sha256 TEXT NOT NULL);
    """)


def meta_get(db, key, default=None):
    row = db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return json.loads(row[0]) if row else default


def meta_put(db, key, value):
    db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, json.dumps(value)))


def query_for_track(row):
    """Mantém o título completo e flags de origem; não compartilha só pela composição."""
    duration = row.get("duration_ms")
    if duration is not None:
        require(
            math.isfinite(float(duration)), "Duração não finita; revisar metadados, sem consultar."
        )
    return {
        "composition_key": row["composition_key"],
        "split": row["split"],
        "representative_track_id": row["track_id"],
        "representative_spotify_row_id": row["spotify_row_id"],
        "artist_name_query": row["artist_name_raw"],
        "track_name_query": row["track_name_raw"],
        "title_base_query": pilot_base_title(row["track_name_raw"]),
        "album_name_query": None,
        "duration_seconds": float(duration) / 1000 if duration is not None else None,
        **{flag: bool(row.get(flag)) for flag in VERSION_FLAGS},
        "karaoke": _version_flags(row["track_name_raw"])["karaoke"],
    }


def query_identity(query):
    # IDs de faixa não entram na consulta; split entra para preservar sua custódia.
    return {k: v for k, v in query.items() if not k.startswith("representative_")}


def build_universe(source):
    require(not FORBIDDEN_SAMPLING_COLUMNS.intersection(source.columns), "Fonte contém alvo/proxy.")
    require(
        source["track_id"].n_unique() == source.height,
        "track_id duplicado; não escolher silenciosamente.",
    )
    representatives, audit = select_representatives_without_target(source)
    representative_ids = set(representatives["track_id"])
    queries, tracks = {}, []
    for row in source.sort("spotify_row_id", "track_id").iter_rows(named=True):
        require(
            row["split"] in {"development_train", "holdout_test"}, "Split ausente/desconhecido."
        )
        reason, query_id = None, None
        if not row.get("composition_key"):
            reason = "missing_composition_key"
        elif not row.get("artist_name_raw") or not row.get("track_name_raw"):
            reason = "missing_artist_or_title"
        else:
            query = query_for_track(row)
            query_id = fingerprint(query_identity(query))
            queries.setdefault(query_id, query)
        tracks.append(
            {
                **row,
                "query_id": query_id,
                "ineligibility_reason": reason,
                "is_previous_composition_representative": row["track_id"] in representative_ids,
            }
        )
    return tracks, queries, audit


def discover_history(extra_cache_dirs=(), extra_results=()):
    """Procura múltiplas pastas, sem abrir fontes tabulares que contenham alvos."""
    cache_dirs = set(Path(p).resolve() for p in extra_cache_dirs)
    for root in (ROOT / "data/raw", ROOT / "data/interim", ROOT / "data/derived"):
        if root.exists():
            cache_dirs.update(p for p in root.rglob("lrclib_cache*") if p.is_dir())
    results = set(Path(p).resolve() for p in extra_results)
    for root in (ROOT / "data/processed", ROOT / "data/interim", ROOT / "data/derived"):
        if root.exists():
            results.update(root.rglob("*lyrics*results*.parquet"))
            results.update(root.rglob("*lyrics*reclassified*.parquet"))
    caches = sorted({p.resolve() for folder in cache_dirs for p in folder.rglob("*.json")})
    return caches, sorted(results)


def inventory_history(db, caches, results):
    counts = Counter()
    for path in caches:
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            key = envelope.get("composition_key")
            valid = isinstance(key, str) and isinstance(envelope.get("requests"), list)
        except (OSError, ValueError, AttributeError):
            key, valid = None, False
        db.execute(
            "INSERT OR REPLACE INTO cache_inventory VALUES (?,?,?,?)",
            (str(path), key, sha256_file(path), int(valid)),
        )
        counts["caches_valid_schema_candidate" if valid else "caches_unreadable"] += 1
    for path in results:
        require(path.is_file(), "Arquivo histórico informado não existe.")
        schema = pl.scan_parquet(path).collect_schema()
        columns = [c for c in HISTORY_COLUMNS if c in schema]
        if "composition_key" not in columns:
            counts["results_without_composition_key"] += 1
            continue
        # Projeção fechada ANTES de collect: nunca lê popularidade/letras/vetores.
        frame = pl.scan_parquet(path).select(columns).collect()
        for ordinal, row in enumerate(frame.iter_rows(named=True)):
            db.execute(
                "INSERT OR REPLACE INTO history VALUES (?,?,?,?)",
                (str(path), ordinal, row["composition_key"], json.dumps(row)),
            )
        counts["historical_result_rows"] += frame.height
    return dict(counts)


def transient_error(envelope):
    return any(
        r.get("http_status") is None or r.get("http_status") in {408, 429, 500, 502, 503, 504}
        for r in envelope.get("requests", [])
    )


def classify_history(query, paths, tolerance=10.0):
    candidates = []
    for path in paths:
        try:
            envelope = json.loads(Path(path).read_text(encoding="utf-8"))
            if not cache_is_compatible(query, envelope):
                continue
            row = classify_cached_composition_v012(query, envelope, duration_tolerance=tolerance)
            candidates.append((row, str(path), envelope))
        except (OSError, ValueError, TypeError, KeyError):
            continue  # Mantido no inventário; não tratado como sucesso ou ausência.
    if not candidates:
        return None
    accepted = [c for c in candidates if c[0]["final_status"] in ACCEPTED_STATUSES]
    ambiguous = [c for c in candidates if c[0]["final_status"].startswith("ambiguous")]
    hashes = {c[0].get("selected_strict_text_sha256") for c in accepted}
    if ambiguous or len(hashes) > 1:
        if len(candidates) == 1:
            return candidates[0][0], candidates[0][1], False
        return (
            {"final_status": "ambiguous_history_conflict", "compatible_caches": len(candidates)},
            None,
            False,
        )
    # Mesmo texto estrito em todos os sucessos; falha técnica/404 não invalida um sucesso validado.
    chosen = sorted(accepted or candidates, key=lambda c: (str(c[2].get("queried_at", "")), c[1]))[
        -1
    ]
    return chosen[0], chosen[1], transient_error(chosen[2])


def save_result(db, query_id, result, cache_path, retryable):
    db.execute(
        "UPDATE queries SET status=?,retryable=?,result=?,cache_path=?,cache_sha256=? WHERE query_id=?",
        (
            result["final_status"],
            int(retryable),
            json.dumps(result),
            cache_path,
            sha256_file(Path(cache_path)) if cache_path else None,
            query_id,
        ),
    )


def summary(db, **extra):
    counts = dict(db.execute("SELECT status,COUNT(*) FROM queries GROUP BY status").fetchall())
    accepted = sum(counts.get(s, 0) for s in ACCEPTED_STATUSES)
    return {
        "tracks": db.execute("SELECT COUNT(*) FROM tracks").fetchone()[0],
        "compositions": db.execute(
            "SELECT COUNT(DISTINCT composition_key) FROM queries"
        ).fetchone()[0],
        "queries": sum(counts.values()),
        "accepted": accepted,
        "ambiguous": sum(n for s, n in counts.items() if s.startswith("ambiguous")),
        "not_found": counts.get("not_found", 0),
        "technical_errors": counts.get("request_error", 0),
        "not_queried": counts.get("not_queried", 0),
        "status_counts": counts,
        "embedding_queries_completed": db.execute(
            "SELECT COUNT(*) FROM embedding_links"
        ).fetchone()[0],
        "unique_vectors": db.execute("SELECT COUNT(*) FROM vectors").fetchone()[0],
        "retryable_errors": db.execute(
            "SELECT COUNT(*) FROM queries WHERE status='request_error' AND retryable=1 AND attempts<3"
        ).fetchone()[0],
        "attempt_limit_reached": db.execute(
            "SELECT COUNT(*) FROM queries WHERE status='request_error' AND attempts>=3"
        ).fetchone()[0],
        "updated_at": utc_now(),
        **extra,
    }


def progress(db, workspace, **extra):
    value = summary(db, **extra)
    atomic_json(workspace / "progress.json", value)
    print(json.dumps(value, ensure_ascii=False), flush=True)
    return value


def export_manifest(db, workspace):
    rows = []
    for row in db.execute("SELECT * FROM queries ORDER BY query_id"):
        query = json.loads(row["data"])
        historical = [
            json.loads(r[0])
            for r in db.execute(
                "SELECT data FROM history WHERE composition_key=?", (row["composition_key"],)
            )
        ]
        statuses = Counter(
            str(
                r.get("final_status")
                or r.get("reclassified_status")
                or r.get("status")
                or "unconfirmed"
            )
            for r in historical
        )
        rows.append(
            {
                **query,
                "query_id": row["query_id"],
                "final_status": row["status"],
                "retryable": bool(row["retryable"]),
                "manual_attempts": row["attempts"],
                "historical_rows": len(historical),
                "historical_status_counts": json.dumps(dict(statuses), sort_keys=True),
                "cache_evidence": (
                    "reclassified_compatible_cache"
                    if row["cache_path"]
                    else "historical_without_selected_cache"
                    if historical
                    else "no_selected_cache"
                ),
            }
        )
    frame = pl.DataFrame(rows, infer_schema_length=None)
    if rows:
        atomic_frame(workspace / "manifest.parquet", frame)
        atomic_frame(
            workspace / "pending.parquet",
            frame.filter(
                pl.col("final_status").is_in(["not_queried", "in_progress"])
                | (
                    (pl.col("final_status") == "request_error")
                    & pl.col("retryable")
                    & (pl.col("manual_attempts") < 3)
                )
            ),
        )
    tracks = [json.loads(r[0]) for r in db.execute("SELECT data FROM tracks ORDER BY track_id")]
    if tracks:
        atomic_frame(
            workspace / "track_mapping.parquet", pl.DataFrame(tracks, infer_schema_length=None)
        )


def scientific_signature(config):
    files = [
        Path(__file__),
        ROOT / "src/tcc_music_popularity/manual_embeddings.py",
        ROOT / "configs/final_scale_v0_4.yaml",
    ]
    files += [
        ROOT / "src/tcc_music_popularity" / name
        for name in (
            "lyrics_pilot.py",
            "lyrics_pilot_v012.py",
            "lyrics_ambiguity_v011.py",
            "lyrics_pilot_v013.py",
            "lyrics_scale_v040.py",
            "lyrics_embeddings_v020.py",
            "final_study_v040.py",
        )
    ]
    return {
        "code": {str(p): sha256_file(p) for p in files},
        "inputs": {
            str(ROOT / config["inputs"][k]): sha256_file(ROOT / config["inputs"][k])
            for k in ("modeling_base", "split_assignments", "matching_audit")
        },
    }


def check_prepared(db, config):
    require(
        meta_get(db, "prepared") is True, "Preparação incompleta; execute o script 01 novamente."
    )
    require(
        meta_get(db, "signature") == scientific_signature(config),
        "Entradas/código congelados mudaram. Preserve este workspace e revise antes de continuar.",
    )


def prepare(workspace, *, extra_cache_dirs=(), extra_results=()):
    config = load_yaml(CONFIG)
    with exclusive(workspace), closing(connect(workspace)) as db:
        init_db(db)
        if meta_get(db, "prepared"):
            require(
                not extra_cache_dirs and not extra_results,
                "Workspace já preparado. Para acrescentar fontes históricas, use um novo --workspace privado.",
            )
            check_prepared(db, config)
            export_manifest(db, workspace)
            return progress(db, workspace, stage="prepared_reused")
        with db:
            tracks, queries, audit = build_universe(load_target_free_source(config))
            for row in tracks:
                db.execute(
                    "INSERT OR REPLACE INTO tracks VALUES (?,?,?)",
                    (row["track_id"], row["query_id"], json.dumps(row)),
                )
            for key, query in queries.items():
                db.execute(
                    "INSERT OR IGNORE INTO queries(query_id,composition_key,data) VALUES (?,?,?)",
                    (key, query["composition_key"], json.dumps(query)),
                )
            caches, results = discover_history(extra_cache_dirs, extra_results)
            history = inventory_history(db, caches, results)
            for index, (key, query) in enumerate(sorted(queries.items()), 1):
                paths = [
                    r[0]
                    for r in db.execute(
                        "SELECT path FROM cache_inventory WHERE composition_key=? AND valid=1 ORDER BY path",
                        (query["composition_key"],),
                    )
                ]
                classified = classify_history(
                    query, paths, config["collection"]["duration_tolerance_seconds"]
                )
                if classified:
                    save_result(db, key, *classified)
                if index % 5000 == 0:
                    print(
                        f"Preparação offline: {index}/{len(queries)} consultas reconciliadas",
                        flush=True,
                    )
            meta_put(db, "signature", scientific_signature(config))
            meta_put(db, "history_inventory", history)
            meta_put(db, "representative_audit", audit)
            meta_put(db, "prepared", True)
        atomic_frame(
            workspace / "track_mapping.parquet", pl.DataFrame(tracks, infer_schema_length=None)
        )
        export_manifest(db, workspace)
        atomic_json(
            workspace / "preparation.json",
            {
                "audit": audit,
                "history": history,
                "signature": meta_get(db, "signature"),
                "target_loaded": False,
            },
        )
        return progress(
            db,
            workspace,
            stage="prepared",
            history=history,
            ineligible_tracks=sum(r["query_id"] is None for r in tracks),
        )


def collect(workspace, *, limit=None, retry_errors=False, client_factory=LRCLIBClient):
    config = load_yaml(CONFIG)
    with exclusive(workspace), closing(connect(workspace)) as db:
        check_prepared(db, config)
        condition = (
            "status='request_error' AND retryable=1"
            if retry_errors
            else "status IN ('not_queried','in_progress')"
        )
        # Três ciclos totais por consulta nesta expansão, além das tentativas por endpoint.
        rows = db.execute(
            f"SELECT * FROM queries WHERE (({condition}) AND attempts<3) OR status='in_progress' ORDER BY query_id"
        ).fetchall()
        if limit is not None:
            rows = rows[:limit]
        recent, completed, reason = [], 0, None
        client = client_factory(
            {**config["collection"], "cache_dir": str(workspace / "lrclib_cache_manual")}
        )
        try:
            for stored in rows:
                query, key = json.loads(stored["data"]), stored["query_id"]
                number = stored["attempts"]
                previous = db.execute(
                    "SELECT cache_path FROM attempts WHERE query_id=? AND number=?", (key, number)
                ).fetchone()
                path = Path(previous[0]) if previous else None
                recovery = None
                if stored["status"] == "in_progress" and path and path.is_file():
                    recovery = classify_history(
                        query, [path], config["collection"]["duration_tolerance_seconds"]
                    )
                if recovery:
                    save_result(db, key, *recovery)
                    db.commit()
                    completed += 1
                    continue
                if number >= 3:
                    save_result(
                        db,
                        key,
                        {
                            "final_status": "request_error",
                            "reason": "attempt_limit_reached_after_interruption",
                        },
                        None,
                        False,
                    )
                    db.commit()
                    continue
                number += 1
                directory = workspace / "lrclib_cache_manual" / key / f"attempt_{number:02d}"
                path = directory / (
                    hashlib.sha256(query["composition_key"].encode()).hexdigest() + ".json"
                )
                require(
                    not path.exists(), "Tentativa já existente; preservar e revisar o checkpoint."
                )
                db.execute(
                    "INSERT INTO attempts VALUES (?,?,?,?)", (key, number, str(path), "in_progress")
                )
                db.execute(
                    "UPDATE queries SET attempts=?,status='in_progress' WHERE query_id=?",
                    (number, key),
                )
                db.commit()
                client.cache_dir = directory
                try:
                    envelope = client.lookup(query)
                    require(
                        cache_is_compatible(query, envelope),
                        "Resposta/cache com schema incompatível.",
                    )
                    result = classify_cached_composition_v012(
                        query,
                        envelope,
                        duration_tolerance=config["collection"]["duration_tolerance_seconds"],
                    )
                except (ValueError, TypeError, KeyError):
                    save_result(
                        db,
                        key,
                        {"final_status": "schema_error"},
                        str(path) if path.exists() else None,
                        False,
                    )
                    db.commit()
                    reason = "schema_error_review_required"
                    break
                save_result(db, key, result, str(path), transient_error(envelope))
                db.execute(
                    "UPDATE attempts SET status=? WHERE query_id=? AND number=?",
                    (result["final_status"], key, number),
                )
                db.commit()  # Cada consulta é um checkpoint, sem sobrescrever caches antigos.
                completed += 1
                recent.append(result["final_status"])
                reason = circuit_breaker_reason(
                    recent,
                    envelope,
                    {
                        "circuit_breaker": config["collection"]["circuit_breaker"],
                        "lrclib": config["collection"],
                    },
                )
                progress(
                    db,
                    workspace,
                    stage="collecting",
                    processed_this_run=completed,
                    planned_this_run=len(rows),
                    stop_reason=reason,
                )
                if reason:
                    break
        except KeyboardInterrupt:
            reason = "interrupted_resume_same_command"
        except Exception:
            reason = "execution_failed_review_required"
            raise
        finally:
            export_manifest(db, workspace)
            progress(
                db,
                workspace,
                stage="stopped" if reason else "batch_complete",
                processed_this_run=completed,
                planned_this_run=len(rows),
                stop_reason=reason,
            )
        return 2 if reason else 0


def workspace_arg(value):
    path = (ROOT / value).resolve()
    private_parent = (ROOT / "data/derived").resolve()
    require(
        path.is_relative_to(private_parent) and path != private_parent,
        "Workspace deve ser subpasta privada de data/derived.",
    )
    return path


def cli(stage):
    parser = argparse.ArgumentParser(
        description={
            1: "Prepara o universo completo, offline e sem popularidade.",
            2: "Coleta LRCLIB com cache e retomada.",
            3: "Gera embeddings congelados, somente a pedido.",
        }[stage]
    )
    parser.add_argument("--workspace", type=workspace_arg, default=DEFAULT_WORKSPACE)
    parser.add_argument(
        "--status", action="store_true", help="Mostra somente contagens; não executa trabalho."
    )
    if stage == 1:
        parser.add_argument(
            "--cache-dir",
            action="append",
            default=[],
            help="Pasta histórica adicional, somente leitura.",
        )
        parser.add_argument(
            "--results-file",
            action="append",
            default=[],
            help="Parquet histórico adicional, com projeção sem alvo.",
        )
    else:
        scope = parser.add_mutually_exclusive_group()
        scope.add_argument("--limit", type=int, help="Máximo de consultas/letras nesta execução.")
        scope.add_argument(
            "--all", action="store_true", help="Percorre todas as pendências elegíveis."
        )
        if stage == 2:
            parser.add_argument(
                "--retry-errors",
                action="store_true",
                help="Somente falhas técnicas transitórias; nunca ambiguidades/404.",
            )
        else:
            parser.add_argument(
                "--batch-size", type=int, default=64, help="Trechos por batch do encoder."
            )
            parser.add_argument(
                "--checkpoint-every",
                type=int,
                default=32,
                help="Letras por checkpoint transacional.",
            )
    args = parser.parse_args()
    ignored = subprocess.run(
        ["git", "check-ignore", str(args.workspace / "state.sqlite")], cwd=ROOT, capture_output=True
    )
    require(
        ignored.returncode == 0, "Workspace privado não está ignorado pelo Git; execução bloqueada."
    )
    tracked = subprocess.run(
        ["git", "ls-files", "--", str(args.workspace)], cwd=ROOT, capture_output=True, check=True
    )
    require(
        not tracked.stdout.strip(),
        "Workspace privado contém arquivo rastreado; execução bloqueada.",
    )
    if args.status:
        with closing(connect(args.workspace, readonly=True)) as db:
            print(json.dumps(summary(db), ensure_ascii=False, indent=2))
        return 0
    if stage != 1:
        if not args.all and args.limit is None:
            parser.error("Informe --limit N ou --all; para apenas consultar, use --status.")
        if args.limit is not None and args.limit <= 0:
            parser.error("--limit deve ser positivo.")
    if stage == 1:
        prepare(args.workspace, extra_cache_dirs=args.cache_dir, extra_results=args.results_file)
        return 0
    if stage == 2:
        return collect(args.workspace, limit=args.limit, retry_errors=args.retry_errors)
    from .manual_embeddings import generate

    if args.batch_size <= 0 or args.checkpoint_every <= 0:
        parser.error("Tamanhos de lote/checkpoint devem ser positivos.")
    return generate(
        args.workspace,
        limit=args.limit,
        batch_size=args.batch_size,
        checkpoint_every=args.checkpoint_every,
    )
