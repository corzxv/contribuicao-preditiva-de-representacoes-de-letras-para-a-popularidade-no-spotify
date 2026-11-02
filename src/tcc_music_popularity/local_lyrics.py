"""Consulta local retomável. O dump é imutável; índice e resultados são separados."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from .config import load_yaml
from .io import sha256_file, utc_now
from .lrclib_dump import DEFAULT_DESTINATION, OFFICIAL_DUMP, load_json, save_json
from .lyrics_ambiguity_v011 import reclassify_cached_composition
from .lyrics_pilot import VERSION_FLAGS, pilot_base_title
from .manual_lyrics import (
    CONFIG,
    DEFAULT_WORKSPACE,
    ROOT,
    check_prepared,
    connect,
    exclusive,
    fingerprint,
    meta_get,
    meta_put,
    require,
    save_result,
    summary,
    workspace_arg,
)
from .normalization import conservative_normalize

DEFAULT_LOCAL = ROOT / "data/derived/private_local_lyrics_v1"
DEFAULT_INDEX = DEFAULT_DESTINATION / "tcc_lookup_v1"
QUERY_FIELDS = {
    "composition_key",
    "split",
    "representative_track_id",
    "representative_spotify_row_id",
    "artist_name_query",
    "track_name_query",
    "title_base_query",
    "album_name_query",
    "duration_seconds",
    "karaoke",
    *VERSION_FLAGS,
}
MAX_CANDIDATES = 500
MAX_TEXT_CHARACTERS = 2_000_000
MAX_TOTAL_CHARACTERS = 8_000_000
MAX_ATTEMPTS = 3
INDEX_BATCH = 5000
INDEX_SQL = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE catalog (
    id INTEGER PRIMARY KEY, artist_key TEXT NOT NULL, title_key TEXT, base_key TEXT,
    name TEXT, artist_name TEXT, album_name TEXT, duration REAL, last_lyrics_id INTEGER
);
CREATE INDEX catalog_title ON catalog(artist_key,title_key);
CREATE INDEX catalog_base ON catalog(artist_key,base_key);
"""


def readonly(path, *, immutable=True):
    require(path.is_file(), "Arquivo privado ausente; confira o SSD e o workspace.")
    uri = path.resolve().as_uri() + "?mode=ro" + ("&immutable=1" if immutable else "")
    db = sqlite3.connect(uri, uri=True)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    db.execute("PRAGMA cache_size=-65536")
    return db


def safe_query(raw):
    query = json.loads(raw)
    require(set(query) <= QUERY_FIELDS, "Consulta contém campo não autorizado; revisar manifesto.")
    require(query.get("split") in {"development_train", "holdout_test"}, "Split inválido.")
    require(
        bool(query.get("artist_name_query") and query.get("track_name_query")),
        "Metadados ausentes.",
    )
    duration = query.get("duration_seconds")
    require(duration is None or math.isfinite(float(duration)), "Duração inválida.")
    return query


def implementation_signature():
    files = [Path(__file__), ROOT / "src/tcc_music_popularity/normalization.py"]
    return {p.name: sha256_file(p) for p in files}


def checked_dump(path):
    """Não reexecuta quick_check nem relê 262 GB: exige checkpoint pronto do script 05."""
    path = path.resolve()
    state = load_json(path.parent / "dump_progress.json")
    require(
        state.get("status") == "ready"
        and state.get("sqlite_quick_check") == "ok"
        and state.get("gzip_crc_verified") is True,
        "Dump ainda não validado pelo script 05.",
    )
    require(Path(state.get("database_path", "")).resolve() == path, "Caminho difere do checkpoint.")
    require(
        path.is_file() and path.stat().st_size == state.get("extracted_bytes"),
        "Tamanho do dump divergiu.",
    )
    stat = path.stat()
    return {
        "path": str(path),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "verified_sha256": state["database_sha256"],
        "source": state["source"],
    }


def space(path, reserve=5 * 1024**3):
    require(
        shutil.disk_usage(path).free >= reserve,
        "Espaço livre abaixo da reserva; arquivos preservados.",
    )


def initialize_workspace(source, workspace, config):
    """Snapshot SQLite consistente; mantém caches antigos referenciados, sem copiá-los."""
    require(
        source.resolve() != workspace.resolve(),
        "Use workspace NOVO; não sobrescrever a coleta anterior.",
    )
    require(
        (source / "state.sqlite").is_file(), "Checkpoint anterior ausente; não criar universo novo."
    )
    final = workspace / "state.sqlite"
    if final.exists():
        with closing(connect(workspace, readonly=True)) as db:
            origin = meta_get(db, "local_origin")
            require(
                origin and origin["source"] == str(source.resolve()),
                "Workspace não pertence a esta busca.",
            )
        return
    temporary = workspace / "state.initializing.sqlite"
    marker = workspace / "local_initialization.json"
    owner = {"owner": "tcc-local-lyrics-v1", "source": str(source.resolve())}
    if marker.exists():
        require(load_json(marker) == owner, "Inicialização pertence a outra origem.")
    else:
        require(
            not temporary.exists(), "Cópia temporária sem proveniência; preserve e use outra pasta."
        )
        save_json(marker, owner)
    # Uma cópia interrompida pode ser refeita pelo SQLite backup; nunca é o arquivo original.
    with exclusive(source), closing(connect(source, readonly=True)) as original:
        check_prepared(original, config)
        needed = (source / "state.sqlite").stat().st_size + 5 * 1024**3
        space(workspace, needed)
        with closing(sqlite3.connect(temporary)) as target:
            original.backup(target)
            target.execute("PRAGMA journal_mode=DELETE")
            meta_put(
                target, "local_origin", {"source": str(source.resolve()), "created_at": utc_now()}
            )
            target.execute("""CREATE TABLE local_jobs (
                query_id TEXT PRIMARY KEY, state TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
                baseline_status TEXT NOT NULL, baseline_result TEXT, baseline_cache_path TEXT,
                baseline_cache_sha256 TEXT, error_type TEXT, elapsed_seconds REAL
            )""")
            target.execute("""INSERT INTO local_jobs(query_id,baseline_status,baseline_result,baseline_cache_path,baseline_cache_sha256)
                SELECT query_id,status,result,cache_path,cache_sha256 FROM queries
                WHERE status NOT IN ('accepted_exact_unique','accepted_exact_equivalent','instrumental')
                AND status NOT LIKE 'ambiguous%'""")
            target.commit()
        temporary.rename(final)


def artist_keys(db):
    # Lê exclusivamente as consultas já preparadas e livres de alvos.
    return sorted(
        {
            conservative_normalize(safe_query(r[0])["artist_name_query"])
            for r in db.execute("SELECT data FROM queries")
        }
        - {None, ""}
    )


def connection_index(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    return db


def index_seal(identity, artists):
    return {
        "dump": identity,
        "artists_sha256": fingerprint(artists),
        "code": implementation_signature(),
    }


def build_index(dump, index_dir, seal, artists, *, batch_size=INDEX_BATCH):
    """Uma varredura só de metadados, em lotes transacionais com retomada por ID."""
    with exclusive(index_dir), closing(connection_index(index_dir / "lookup.sqlite")) as index:
        exists = index.execute("SELECT 1 FROM sqlite_schema WHERE name='meta'").fetchone()
        if not exists:
            require(
                not index.execute("SELECT 1 FROM sqlite_schema WHERE type='table'").fetchone(),
                "Índice desconhecido.",
            )
            index.executescript("BEGIN IMMEDIATE;\n" + INDEX_SQL)
            with index:
                meta_put(index, "seal", seal)
                meta_put(
                    index, "progress", {"last_id": 0, "scanned": 0, "indexed": 0, "complete": False}
                )
        require(
            meta_get(index, "seal") == seal,
            "Índice pertence a outro dump/universo/código; preserve e use nova pasta.",
        )
        state = meta_get(index, "progress")
        wanted = set(artists)
        with closing(readonly(dump)) as source:
            require(
                {r[1] for r in source.execute("PRAGMA table_info(tracks)")}
                >= {"id", "name", "artist_name", "album_name", "duration", "last_lyrics_id"},
                "Schema tracks incompatível.",
            )
            last_print = 0.0
            while not state["complete"]:
                space(index_dir)
                rows = source.execute(
                    """SELECT id,name,artist_name,album_name,duration,last_lyrics_id
                    FROM tracks WHERE id>? ORDER BY id LIMIT ?""",
                    (state["last_id"], batch_size),
                ).fetchall()
                selected = []
                for row in rows:
                    artist = conservative_normalize(row["artist_name"])
                    if artist in wanted:
                        selected.append(
                            (
                                row["id"],
                                artist,
                                conservative_normalize(row["name"]),
                                conservative_normalize(pilot_base_title(row["name"])),
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
                if time.monotonic() - last_print >= 10 or state["complete"]:
                    value = {"stage": "index_ready" if state["complete"] else "indexing", **state}
                    save_json(index_dir / "progress.json", value)
                    print(json.dumps(value), flush=True)
                    last_print = time.monotonic()
        # Também corrige o JSON se a queda ocorreu entre o commit final e sua publicação.
        save_json(index_dir / "progress.json", {"stage": "index_ready", **state})
    return state


class LocalLookup:
    def __init__(self, dump, index, *, query_timeout=30):
        self.dump, self.index, self.query_timeout = dump, index, query_timeout

    def candidates(self, query):
        artist = conservative_normalize(query["artist_name_query"])
        title = conservative_normalize(query["track_name_query"])
        base = conservative_normalize(query.get("title_base_query"))
        deadline = time.monotonic() + self.query_timeout
        self.dump.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        self.index.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        try:
            rows = self.index.execute(
                """SELECT * FROM catalog WHERE id IN (
                SELECT id FROM catalog WHERE artist_key=? AND title_key=?
                UNION SELECT id FROM catalog WHERE artist_key=? AND base_key=?)
                ORDER BY id LIMIT ?""",
                (artist, title, artist, base, MAX_CANDIDATES + 1),
            ).fetchall()
            if len(rows) > MAX_CANDIDATES:
                return [], "candidate_limit"
            values, total_chars = [], 0
            for row in rows:
                if time.monotonic() > deadline:
                    raise TimeoutError("local_query_timeout")
                lyric = None
                if row["last_lyrics_id"] is not None:
                    sizes = self.dump.execute(
                        """SELECT track_id,length(plain_lyrics),length(synced_lyrics)
                        FROM lyrics WHERE id=?""",
                        (row["last_lyrics_id"],),
                    ).fetchone()
                    require(
                        sizes is not None and sizes[0] == row["id"],
                        "Referência tracks–lyrics inconsistente.",
                    )
                    chars = (sizes[1] or 0) + (sizes[2] or 0)
                    total_chars += chars
                    if chars > MAX_TEXT_CHARACTERS or total_chars > MAX_TOTAL_CHARACTERS:
                        return [], "text_size_limit"
                    lyric = self.dump.execute(
                        """SELECT plain_lyrics,synced_lyrics,instrumental
                        FROM lyrics WHERE id=?""",
                        (row["last_lyrics_id"],),
                    ).fetchone()
                values.append(
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
            return values, None
        finally:
            self.dump.set_progress_handler(None, 0)
            self.index.set_progress_handler(None, 0)


def envelope_for(query, candidates, seal, incomplete):
    """Formato legado só para reutilizar o classificador/leitor; nenhum HTTP é realizado."""
    return {
        "cache_version": "local-snapshot-v1",
        "composition_key": query["composition_key"],
        "queried_at": utc_now(),
        "transport": "sqlite_readonly",
        "http_requests": 0,
        "local_source": seal,
        "local_query_sha256": fingerprint(query),
        "incomplete_reason": incomplete,
        "legacy_adapter_status_codes_not_http": True,
        "requests": [
            {"endpoint": "/api/get", "http_status": 404, "payload": None, "attempts": []},
            {"endpoint": "/api/search", "http_status": 200, "payload": candidates, "attempts": []},
        ],
    }


def classify_local(query, envelope, old_status, tolerance):
    if envelope["incomplete_reason"]:
        return {
            "final_status": "ambiguous_local_incomplete",
            "ambiguity_cause": envelope["incomplete_reason"],
            "query_method": "sqlite_snapshot",
            "http_requests": 0,
        }
    # Mesmas regras exatas de artista/título-base, versão, duração e equivalência estrita.
    # A barreira de 20 resultados da API não se aplica: o índice local enumera todos os candidatos.
    row, _, _ = reclassify_cached_composition(
        query, envelope, old_status=old_status, duration_tolerance=tolerance
    )
    return {
        **row,
        "final_status": row["reclassified_status"],
        "query_method": "sqlite_snapshot",
        "http_requests": 0,
        "search_limit_20_reached": False,
        "api_limit_applicable": False,
        "candidate_enumeration_complete": True,
        "absence_scope": "normalized_metadata_in_fixed_snapshot",
    }


def local_status(db, **extra):
    jobs = dict(db.execute("SELECT state,count(*) FROM local_jobs GROUP BY state").fetchall())
    return summary(
        db,
        local_jobs=jobs,
        local_pending=jobs.get("pending", 0) + jobs.get("active", 0),
        local_retryable_errors=db.execute(
            "SELECT count(*) FROM local_jobs WHERE state='error' AND attempts<?", (MAX_ATTEMPTS,)
        ).fetchone()[0],
        local_exhausted_errors=db.execute(
            "SELECT count(*) FROM local_jobs WHERE state='error' AND attempts>=?", (MAX_ATTEMPTS,)
        ).fetchone()[0],
        **extra,
    )


def collect_local(
    workspace, dump_path, index_path, seal, config, *, limit=None, retry_errors=False
):
    with (
        closing(connect(workspace)) as db,
        closing(readonly(dump_path)) as dump,
        closing(readonly(index_path, immutable=False)) as index,
    ):
        require(
            meta_get(index, "seal") == seal and meta_get(index, "progress")["complete"],
            "Conclua --prepare-index primeiro.",
        )
        require(
            meta_get(db, "local_seal", seal) == seal,
            "Fonte/código mudou; preservar resultados e revisar.",
        )
        with db:
            meta_put(db, "local_seal", seal)
        lookup = LocalLookup(dump, index)
        condition = (
            "j.state='active' OR (j.state='error' AND j.attempts<3)"
            if retry_errors
            else "j.state IN ('pending','active')"
        )
        rows = db.execute(
            f"""SELECT q.*,j.state AS job_state,j.attempts AS local_attempts
            FROM queries q JOIN local_jobs j USING(query_id) WHERE {condition} ORDER BY q.query_id LIMIT ?""",
            (limit if limit is not None else -1,),
        ).fetchall()
        completed, failed, start, last_print = 0, 0, time.monotonic(), 0.0
        reason = None
        try:
            for stored in rows:
                space(workspace)
                query = safe_query(stored["data"])
                number = stored["local_attempts"] + (stored["job_state"] != "active")
                key = stored["query_id"]
                with db:
                    db.execute(
                        "UPDATE local_jobs SET state='active',attempts=? WHERE query_id=?",
                        (number, key),
                    )
                path = workspace / "lrclib_cache_local" / key[:2] / f"{key}_{number}.json"
                started = time.monotonic()
                try:
                    if path.exists():
                        envelope = load_json(path)
                        require(
                            envelope.get("local_source") == seal
                            and envelope.get("local_query_sha256") == fingerprint(query),
                            "Cache local incompatível.",
                        )
                    else:
                        candidates, incomplete = lookup.candidates(query)
                        envelope = envelope_for(query, candidates, seal, incomplete)
                        path.parent.mkdir(parents=True, exist_ok=True)
                        save_json(path, envelope)
                    result = classify_local(
                        query,
                        envelope,
                        stored["status"],
                        config["collection"]["duration_tolerance_seconds"],
                    )
                    with db:
                        save_result(db, key, result, str(path), False)
                        db.execute(
                            "UPDATE local_jobs SET state='complete',error_type=NULL,elapsed_seconds=? WHERE query_id=?",
                            (time.monotonic() - started, key),
                        )
                    completed += 1
                except (sqlite3.Error, OSError, ValueError, TypeError, KeyError) as exc:
                    with db:
                        db.execute(
                            "UPDATE local_jobs SET state='error',error_type=?,elapsed_seconds=? WHERE query_id=?",
                            (type(exc).__name__, time.monotonic() - started, key),
                        )
                    failed += 1
                    # Erros estruturais não devem percorrer milhares de consultas cegamente.
                    reason = "local_error_preserved_retry_explicitly"
                    break
                if time.monotonic() - last_print >= 10:
                    emit_status(
                        db, workspace, "collecting_local", completed, failed, len(rows), start, None
                    )
                    last_print = time.monotonic()
        except KeyboardInterrupt:
            reason = "interrupted_resume_same_command"
        except Exception:
            reason = "execution_failed_preserve_files"
            raise
        finally:
            emit_status(
                db,
                workspace,
                "stopped" if reason else "batch_complete",
                completed,
                failed,
                len(rows),
                start,
                reason,
            )
        return 2 if reason else 0


def emit_status(db, workspace, stage, completed, failed, planned, start, reason):
    elapsed = time.monotonic() - start
    value = local_status(
        db,
        stage=stage,
        processed_this_run=completed,
        errors_this_run=failed,
        planned_this_run=planned,
        elapsed_seconds=round(elapsed, 3),
        queries_per_second=round(completed / elapsed, 3) if elapsed else None,
        stop_reason=reason,
    )
    save_json(workspace / "local_progress.json", value)
    print(json.dumps(value, ensure_ascii=False), flush=True)


def execute(
    source, workspace, dump, index_dir, *, prepare_index=False, limit=None, retry_errors=False
):
    config = load_yaml(CONFIG)
    require(
        not index_dir.resolve().is_relative_to(ROOT.resolve()),
        "Índice deve ficar fora do repositório, no SSD.",
    )
    require(index_dir.resolve() != dump.parent.resolve(), "Use subpasta exclusiva para o índice.")
    require(
        index_dir.resolve().is_relative_to(dump.parent.resolve()),
        "Índice deve estar em subpasta ao lado do dump no SSD.",
    )
    identity = checked_dump(dump)
    with exclusive(workspace):
        initialize_workspace(source, workspace, config)
        with closing(connect(workspace, readonly=True)) as db:
            check_prepared(db, config)
            artists = artist_keys(db)
        seal = index_seal(identity, artists)
        if prepare_index:
            build_index(dump, index_dir, seal, artists)
            return 0
        return collect_local(
            workspace,
            dump,
            index_dir / "lookup.sqlite",
            seal,
            config,
            limit=limit,
            retry_errors=retry_errors,
        )


def cli():
    parser = argparse.ArgumentParser(
        description="Busca offline no dump validado; não gera embeddings nem treina."
    )
    parser.add_argument("--source-workspace", type=workspace_arg, default=DEFAULT_WORKSPACE)
    parser.add_argument("--workspace", type=workspace_arg, default=DEFAULT_LOCAL)
    parser.add_argument(
        "--dump",
        type=Path,
        default=DEFAULT_DESTINATION / OFFICIAL_DUMP.filename.removesuffix(".gz"),
    )
    parser.add_argument("--index-dir", type=Path, default=DEFAULT_INDEX)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-index", action="store_true")
    mode.add_argument("--limit", type=int, help="Número máximo de consultas pendentes neste lote.")
    mode.add_argument("--all", action="store_true", help="Todas as pendências; nunca usa a rede.")
    mode.add_argument("--status", action="store_true")
    parser.add_argument(
        "--retry-errors",
        action="store_true",
        help="Com --limit/--all: retenta somente erros locais, até 3 tentativas.",
    )
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit deve ser positivo.")
    if args.retry_errors and (args.status or args.prepare_index):
        parser.error("Use --retry-errors com --limit ou --all.")
    if args.status:
        value = {"stage": "not_started"}
        if (args.workspace / "state.sqlite").exists():
            with closing(connect(args.workspace, readonly=True)) as db:
                value = local_status(db)
            value["last_run"] = load_json(args.workspace / "local_progress.json")
        value["index"] = load_json(args.index_dir / "progress.json")
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    try:
        return execute(
            args.source_workspace,
            args.workspace,
            args.dump.resolve(),
            args.index_dir.resolve(),
            prepare_index=args.prepare_index,
            limit=args.limit,
            retry_errors=args.retry_errors,
        )
    except KeyboardInterrupt:
        print(json.dumps({"stage": "stopped", "reason": "interrupted_resume_same_command"}))
        return 2
    except Exception as exc:
        # Não imprimir SQL, metadados individuais nem letras em erros de execução.
        print(
            json.dumps(
                {
                    "stage": "failed",
                    "error_type": type(exc).__name__,
                    "reason": str(exc)
                    if isinstance(exc, ValueError)
                    else "local_execution_failed_preserve_files",
                },
                ensure_ascii=False,
            )
        )
        return 1
