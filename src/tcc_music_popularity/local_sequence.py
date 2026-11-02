"""Sequência manual para deixar no terminal; não muda o código selado do índice."""

from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime

from .io import utc_now
from .local_lyrics import DEFAULT_INDEX, DEFAULT_LOCAL, execute
from .lrclib_dump import DEFAULT_DESTINATION, OFFICIAL_DUMP, load_json, save_json
from .manual_lyrics import DEFAULT_WORKSPACE, exclusive, require

DEFAULT_DUMP = DEFAULT_DESTINATION / OFFICIAL_DUMP.filename.removesuffix(".gz")


def workspace_busy(workspace):
    """Sonda o bloqueio real do script 06, sem mantê-lo durante a espera."""
    require((workspace / "state.sqlite").is_file(), "Inicie a preparação do índice primeiro.")
    try:
        with exclusive(workspace):
            return False
    except RuntimeError:
        return True


def verified_batch(value, started):
    return (
        value.get("stage") == "batch_complete"
        and value.get("errors_this_run") == 0
        and value.get("stop_reason") is None
        and value.get("processed_this_run") == value.get("planned_this_run")
        and bool(value.get("updated_at"))
        and datetime.fromisoformat(value["updated_at"]) >= datetime.fromisoformat(started)
        and value.get("local_retryable_errors") == 0
        and value.get("local_exhausted_errors") == 0
    )


def run(
    *,
    source=DEFAULT_WORKSPACE,
    workspace=DEFAULT_LOCAL,
    index_dir=DEFAULT_INDEX,
    dump=DEFAULT_DUMP,
    wait_hours=12,
    poll_seconds=15,
    executor=execute,
    busy=workspace_busy,
    sleeper=time.sleep,
    clock=time.monotonic,
):
    require((workspace / "state.sqlite").is_file(), "Inicie --prepare-index no script 06 primeiro.")
    journal = workspace / "local_sequence"
    with exclusive(journal):  # Impede dois sequenciadores no mesmo workspace.

        def emit(stage, **extra):
            value = {"stage": stage, "updated_at": utc_now(), **extra}
            save_json(journal / "progress.json", value)
            print(json.dumps(value, ensure_ascii=False), flush=True)

        started_wait = clock()
        try:
            idle_incomplete = 0
            while True:
                state = load_json(index_dir / "progress.json")
                occupied = busy(workspace)
                if state.get("complete") is True and not occupied:
                    break
                idle_incomplete = idle_incomplete + 1 if not occupied else 0
                if idle_incomplete >= 2:
                    emit("stopped", reason="index_incomplete_and_worker_not_running")
                    return 2
                if clock() - started_wait >= wait_hours * 3600:
                    emit("stopped", reason="index_wait_timeout")
                    return 2
                emit(
                    "waiting_index",
                    scanned=state.get("scanned"),
                    indexed=state.get("indexed"),
                    elapsed_wait_seconds=round(clock() - started_wait, 1),
                )
                sleeper(poll_seconds)

            for stage, limit in (("sample_50", 50), ("all_pending", None)):
                emit(stage)
                started = utc_now()
                code = executor(source, workspace, dump, index_dir, limit=limit)
                value = load_json(workspace / "local_progress.json")
                if code != 0 or not verified_batch(value, started):
                    emit(
                        "stopped",
                        reason="batch_failed_or_unverified",
                        batch=stage,
                        child_exit_code=code,
                        batch_stop_reason=value.get("stop_reason"),
                    )
                    return code if code != 0 else 2
                if value["local_pending"] == 0:
                    emit(
                        "complete",
                        local_pending=0,
                        accepted=value.get("accepted"),
                        ambiguous=value.get("ambiguous"),
                        not_found=value.get("not_found"),
                    )
                    return 0
            emit("stopped", reason="pending_remains_review_required")
            return 2
        except KeyboardInterrupt:
            emit("stopped", reason="interrupted_resume_same_command")
            return 2
        except Exception as exc:
            emit("failed", reason="preserve_files_review_required", error_type=type(exc).__name__)
            return 1


def cli():
    parser = argparse.ArgumentParser(
        description="Aguarda o índice e executa 50 consultas, depois todas; sem rede ou embeddings."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--status", action="store_true")
    parser.add_argument(
        "--wait-hours",
        type=float,
        default=12,
        help="Limite para aguardar o índice, não para coletar.",
    )
    args = parser.parse_args()
    if not math.isfinite(args.wait_hours) or args.wait_hours <= 0:
        parser.error("--wait-hours deve ser positivo e finito.")
    if args.status:
        print(
            json.dumps(
                load_json(DEFAULT_LOCAL / "local_sequence/progress.json")
                or {"stage": "not_started"},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    try:
        return run(wait_hours=args.wait_hours)
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"stage": "failed", "reason": str(exc)}, ensure_ascii=False))
        return 1
