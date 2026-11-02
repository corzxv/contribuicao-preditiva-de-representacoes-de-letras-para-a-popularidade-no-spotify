"""Entrada opcional: conexões reutilizadas e supervisor limitado, sem mudar o matching."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import time
import urllib.error
from collections import Counter
from contextlib import closing
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import requests

from . import manual_lyrics as manual

BREAKER_REASONS = {
    "10_consecutive_technical_errors",
    "request_error_rate_above_20_percent_in_last_50",
    "persistent_429_after_retries",
}
COOLDOWN_SECONDS = 1800
MAX_COOLDOWN_SECONDS = 7200


def iso(timestamp):
    return datetime.fromtimestamp(timestamp, UTC).isoformat()


def timestamp(value):
    return datetime.fromisoformat(value).timestamp() if value else 0.0


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def retry_after_seconds(value, now):
    """Respeita tanto segundos quanto a data HTTP; não reduz a espera do servidor."""
    if not value:
        return 0.0
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        try:
            seconds = parsedate_to_datetime(value).timestamp() - now
        except (TypeError, ValueError, OverflowError):
            return 0.0
    return max(seconds, 0.0) if math.isfinite(seconds) else 0.0


class TimeBudgetExpired(KeyboardInterrupt):
    """A coleta original já salva o checkpoint ao receber KeyboardInterrupt."""


class Runtime:
    def __init__(
        self, workspace, hours, *, clock=time.time, monotonic=time.monotonic, sleep=time.sleep
    ):
        self.path = workspace / "persistent_progress.json"
        self.clock, self.monotonic, self.sleeper = clock, monotonic, sleep
        self.deadline = monotonic() + hours * 3600
        self.expired = False
        previous = read_json(self.path)
        self.state = {
            "started_at": iso(clock()),
            "pid": os.getpid(),
            "status": "starting",
            "restarts_this_run": 0,
            "processed_this_run": 0,
            "consecutive_breakers": previous.get("consecutive_breakers", 0),
            "next_retry_at": previous.get("next_retry_at"),
            "maximum_hours": hours,
        }

    def update(self, **values):
        self.state.update(values, updated_at=iso(self.clock()))
        self.state["elapsed_seconds"] = round(self.clock() - timestamp(self.state["started_at"]), 3)
        manual.atomic_json(self.path, self.state)

    def check(self):
        if self.monotonic() >= self.deadline:
            self.expired = True
            raise TimeBudgetExpired

    def sleep(self, seconds):
        end = self.monotonic() + seconds
        while self.monotonic() < end:
            self.check()
            remaining = min(5, end - self.monotonic(), self.deadline - self.monotonic())
            if remaining > 0:
                self.sleeper(remaining)
        self.check()

    def wait_until(self, until, reason):
        if until <= self.clock():
            return
        self.update(status="cooling_down", reason=reason, next_retry_at=iso(until))
        print(json.dumps(self.state, ensure_ascii=False), flush=True)
        # A data persistida não é apagada por Ctrl+C: reiniciar não contorna a pausa.
        while self.clock() < until:
            self.sleep(min(5, until - self.clock()))
        self.update(status="running", reason=None, next_retry_at=None)


class PooledTransport:
    """Uma sessão e uma conexão em série; nenhuma retentativa oculta do adapter."""

    def __init__(self, runtime, session=None):
        self.runtime = runtime
        self.session = session if session is not None else requests.Session()
        if session is None:
            self.session.mount(
                "https://",
                requests.adapters.HTTPAdapter(
                    pool_connections=1, pool_maxsize=1, max_retries=0, pool_block=True
                ),
            )
        self.statuses = Counter()
        self.request_count = 0
        self.elapsed_seconds = 0.0

    def __call__(self, url, headers, timeout):
        self.runtime.check()
        self.runtime.wait_until(
            timestamp(self.runtime.state.get("next_retry_at")), "server_retry_after"
        )
        started = self.runtime.monotonic()
        self.request_count += 1
        try:
            # TLS verificado; configuração normal de proxy do ambiente é preservada.
            with self.session.get(
                url, headers=headers, timeout=timeout, allow_redirects=False
            ) as response:
                status = int(response.status_code)
                self.statuses[str(status)] += 1
                if status in {429, 503}:
                    delay = retry_after_seconds(
                        response.headers.get("Retry-After"), self.runtime.clock()
                    )
                    if delay:
                        self.runtime.update(next_retry_at=iso(self.runtime.clock() + delay))
                if not response.content:
                    payload = None
                else:
                    try:
                        payload = response.json()
                    except ValueError:
                        if status < 400:
                            # Requests.JSONDecodeError também herda RequestException;
                            # não converter erro de schema em falha transitória de rede.
                            raise ValueError("Resposta de sucesso contém JSON inválido.") from None
                        payload = {
                            "error_body_sha256": hashlib.sha256(response.content).hexdigest()
                        }
                return status, payload
        except requests.RequestException as exc:
            self.statuses[type(exc).__name__] += 1
            # Compatível com o tratamento existente, sem imprimir URL/corpo de resposta.
            raise urllib.error.URLError(type(exc).__name__) from None
        finally:
            self.elapsed_seconds += self.runtime.monotonic() - started

    def statistics(self):
        return {
            "http_attempts": self.request_count,
            "http_status_counts": dict(self.statuses),
            "http_elapsed_seconds": round(self.elapsed_seconds, 3),
        }

    def close(self):
        self.session.close()


def snapshot(workspace):
    with closing(manual.connect(workspace, readonly=True)) as db:
        return manual.summary(db)


def seal(workspace):
    """Não migra/regrava o banco antigo: verifica o selo original e sela só esta entrada."""
    with manual.exclusive(workspace), closing(manual.connect(workspace, readonly=True)) as db:
        manual.check_prepared(db, manual.load_yaml(manual.CONFIG))
        signature = {
            "original_signature": manual.meta_get(db, "signature"),
            "supervisor_sha256": manual.sha256_file(__file__),
            "requests_version": requests.__version__,
            "transport": "single_session_serial_no_adapter_retries_tls_verified",
            "matching_unchanged": True,
            "attempt_limits_unchanged": True,
        }
    path = workspace / "persistent_protocol.json"
    if path.exists():
        manual.require(
            read_json(path) == signature,
            "Supervisor/dependência mudou; preserve o checkpoint e revise.",
        )
    else:
        manual.atomic_json(path, signature)


def run(
    workspace,
    *,
    limit=None,
    retry_errors=False,
    retry_errors_after=False,
    max_restarts=48,
    max_hours=192,
    runtime_factory=Runtime,
    client_factory=None,
):
    manual.require(limit is None or limit > 0, "Limite deve ser positivo.")
    manual.require(
        max_restarts >= 0 and math.isfinite(max_hours) and max_hours > 0, "Limites inválidos."
    )
    manual.require(not (retry_errors and retry_errors_after), "Escolha um modo de retentativa.")
    # Outro 04 não entra nem durante a pausa; 02/03 não devem ser abertos em paralelo.
    with manual.exclusive(workspace / "persistent_supervisor_lock"):
        seal(workspace)
        runtime = runtime_factory(workspace, max_hours)
        transport = PooledTransport(runtime) if client_factory is None else None
        factory = client_factory or (
            lambda config: manual.LRCLIBClient(config, transport=transport, sleep_fn=runtime.sleep)
        )
        phase, processed, restarts = "errors" if retry_errors else "new", 0, 0
        runtime.update(maximum_restarts=max_restarts, phase=phase)
        reason, code = "completed", 0
        try:
            # Também conserva uma parada recente do script 02, caso seja a primeira execução do 04.
            previous = read_json(workspace / "progress.json")
            until = timestamp(runtime.state.get("next_retry_at"))
            if previous.get("stop_reason") in BREAKER_REASONS:
                until = max(until, timestamp(previous.get("updated_at")) + COOLDOWN_SECONDS)
            runtime.wait_until(until, "resume_pending_cooldown")
            while True:
                runtime.check()
                counts = snapshot(workspace)
                unfinished = counts["status_counts"].get("in_progress", 0)
                eligible = (
                    counts["retryable_errors"] if phase == "errors" else counts["not_queried"]
                )
                if limit is not None and processed >= limit:
                    reason = "batch_limit_reached"
                    break
                if not eligible and not unfinished:
                    if phase == "new" and retry_errors_after and counts["retryable_errors"]:
                        phase = "errors"
                        runtime.update(phase=phase)
                        runtime.wait_until(runtime.clock() + COOLDOWN_SECONDS, "before_error_pass")
                        continue
                    reason = "no_eligible_pending_queries"
                    break
                runtime.update(status="running", phase=phase, reason=None, counts=counts)
                result = manual.collect(
                    workspace,
                    limit=None if limit is None else limit - processed,
                    retry_errors=phase == "errors",
                    client_factory=factory,
                )
                batch = read_json(workspace / "progress.json")
                processed += batch["processed_this_run"]
                runtime.update(
                    processed_this_run=processed,
                    counts=snapshot(workspace),
                    **(transport.statistics() if transport else {}),
                )
                if runtime.expired:
                    reason, code = "time_budget_reached", 2
                    break
                stop = batch.get("stop_reason")
                if result and stop not in BREAKER_REASONS:
                    reason, code = stop or "unexpected_collection_stop", 2
                    break
                if limit is not None and processed >= limit:
                    reason, code = (stop, 2) if stop else ("batch_limit_reached", 0)
                    break
                # Um passe de erros pode terminar com falhas restantes: só retenta após pausa.
                needs_retry_pass = phase == "errors" and snapshot(workspace)["retryable_errors"] > 0
                if stop in BREAKER_REASONS or needs_retry_pass:
                    streak = runtime.state["consecutive_breakers"] + 1 if stop else 0
                    runtime.update(consecutive_breakers=streak)
                    delay = min(
                        MAX_COOLDOWN_SECONDS, COOLDOWN_SECONDS * (2 ** min(max(streak - 1, 0), 2))
                    )
                    until = max(
                        runtime.clock() + delay, timestamp(runtime.state.get("next_retry_at"))
                    )
                    runtime.update(next_retry_at=iso(until))
                    if restarts >= max_restarts:
                        reason, code = "maximum_restarts_reached", 2
                        break
                    restarts += 1
                    runtime.update(restarts_this_run=restarts)
                    runtime.wait_until(until, stop or "between_error_passes")
                else:
                    runtime.update(consecutive_breakers=0)
        except KeyboardInterrupt:
            reason, code = ("time_budget_reached" if runtime.expired else "interrupted"), 2
        except Exception:
            reason, code = "failed_review_required", 1
            raise
        finally:
            if transport:
                transport.close()
            runtime.update(
                status="completed" if code == 0 else "stopped",
                reason=reason,
                processed_this_run=processed,
                counts=snapshot(workspace),
                **(transport.statistics() if transport else {}),
            )
            print(json.dumps(runtime.state, ensure_ascii=False), flush=True)
        return code


def cli():
    parser = argparse.ArgumentParser(
        description="Coleta serial persistente; preserva o checkpoint e o matching existentes."
    )
    parser.add_argument("--workspace", type=manual.workspace_arg, default=manual.DEFAULT_WORKSPACE)
    parser.add_argument(
        "--status", action="store_true", help="Somente estado salvo e contagens; não inicia coleta."
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--all", action="store_true")
    scope.add_argument("--limit", type=int)
    retry = parser.add_mutually_exclusive_group()
    retry.add_argument("--retry-errors", action="store_true", help="Somente falhas transitórias.")
    retry.add_argument(
        "--retry-errors-after",
        action="store_true",
        help="Após as novas consultas, trata falhas transitórias elegíveis.",
    )
    parser.add_argument(
        "--max-restarts",
        type=int,
        default=48,
        help="Máximo de retomadas automáticas por invocação (padrão: 48).",
    )
    parser.add_argument(
        "--max-hours",
        type=float,
        default=192,
        help="Limite total de horas, incluindo pausas (padrão: 192).",
    )
    args = parser.parse_args()
    if not args.status and not args.all and args.limit is None:
        parser.error("Informe --all ou --limit N.")
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit deve ser positivo.")
    if args.max_restarts < 0 or not math.isfinite(args.max_hours) or args.max_hours <= 0:
        parser.error("Limites de tempo/retomadas inválidos.")
    ignored = subprocess.run(
        ["git", "check-ignore", str(args.workspace / "state.sqlite")],
        cwd=manual.ROOT,
        capture_output=True,
    )
    tracked = subprocess.run(
        ["git", "ls-files", "--", str(args.workspace)],
        cwd=manual.ROOT,
        capture_output=True,
        check=True,
    )
    manual.require(
        ignored.returncode == 0 and not tracked.stdout.strip(),
        "Workspace precisa ser privado, ignorado e não rastreado.",
    )
    if args.status:
        print(
            json.dumps(
                {
                    "supervisor": read_json(args.workspace / "persistent_progress.json"),
                    "current_counts": snapshot(args.workspace),
                    "last_collection": read_json(args.workspace / "progress.json"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    return run(
        args.workspace,
        limit=args.limit,
        retry_errors=args.retry_errors,
        retry_errors_after=args.retry_errors_after,
        max_restarts=args.max_restarts,
        max_hours=args.max_hours,
    )
