"""Somente fontes e respostas sintéticas; rede e encoder reais proibidos."""

import json
import socket
import time
import urllib.error
from contextlib import closing
from urllib.parse import parse_qs, urlparse

import pytest
import requests
from test_manual_lyrics import envelope, fake_client
from test_manual_lyrics import prepared as prepared
from test_manual_lyrics import source as source

from tcc_music_popularity import manual_lyrics as manual
from tcc_music_popularity import persistent_collection as persistent


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Rede real proibida neste teste")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(requests.Session, "request", denied)


class Clock:
    def __init__(self):
        self.value = time.time()
        self.waited = 0.0

    def now(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds
        self.waited += seconds

    def runtime(self, workspace, hours):
        return persistent.Runtime(
            workspace, hours, clock=self.now, monotonic=self.now, sleep=self.sleep
        )


@pytest.fixture
def clock(monkeypatch):
    value = Clock()
    monkeypatch.setattr(manual, "utc_now", lambda: persistent.iso(value.now()))
    return value


class Response:
    def __init__(self, status, payload, headers=None, raw=None):
        self.status_code, self.payload, self.headers = status, payload, headers or {}
        self.content = raw if raw is not None else json.dumps(payload).encode()

    def json(self):
        return json.loads(self.content)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


class Session:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls, self.closed = [], False

    def get(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        result = next(self.responses)
        if isinstance(result, Exception):
            raise result
        return result

    def close(self):
        self.closed = True


def test_same_session_reused_and_no_adapter_retries(tmp_path, clock):
    session = Session([Response(200, {"id": 1}), Response(200, [])])
    transport = persistent.PooledTransport(clock.runtime(tmp_path, 1), session=session)
    assert transport("https://example.invalid/api/get", {"Accept": "application/json"}, 20) == (
        200,
        {"id": 1},
    )
    assert transport("https://example.invalid/api/search", {}, 20) == (200, [])
    assert len(session.calls) == 2
    assert session.calls[0][1]["timeout"] == 20
    assert session.calls[0][1]["allow_redirects"] is False
    transport.close()
    assert session.closed
    default = persistent.PooledTransport(clock.runtime(tmp_path, 1))
    adapter = default.session.get_adapter("https://example.invalid")
    assert adapter.max_retries.total == 0 and adapter._pool_maxsize == 1
    assert default.session.verify is True
    default.close()


def test_server_retry_after_is_respected(tmp_path, clock):
    session = Session([Response(503, {}, {"Retry-After": "60"}), Response(200, [])])
    runtime = clock.runtime(tmp_path, 1)
    transport = persistent.PooledTransport(runtime, session=session)
    transport("https://example.invalid", {}, 20)
    saved = persistent.read_json(runtime.path)
    assert persistent.timestamp(saved["next_retry_at"]) == pytest.approx(clock.now() + 60)
    transport("https://example.invalid", {}, 20)
    assert clock.waited == pytest.approx(60)
    assert runtime.state["next_retry_at"] is None


def test_retry_after_http_date_and_invalid_values():
    assert persistent.retry_after_seconds("Thu, 01 Jan 1970 00:01:00 GMT", 20) == 40
    for value in ("nan", "inf", "broken", "-1", None):
        assert persistent.retry_after_seconds(value, 20) == 0


def test_transport_errors_are_compatible_and_private(tmp_path, clock):
    session = Session([requests.ConnectionError("private query must not leak")])
    transport = persistent.PooledTransport(clock.runtime(tmp_path, 1), session=session)
    with pytest.raises(urllib.error.URLError) as exc:
        transport("https://example.invalid", {}, 20)
    assert "private query" not in str(exc.value)
    assert transport.statistics()["http_status_counts"] == {"ConnectionError": 1}


def test_non_json_503_is_hashed_and_success_schema_error_blocks(tmp_path, clock):
    session = Session(
        [Response(503, None, raw=b"private body"), Response(200, None, raw=b"not json")]
    )
    transport = persistent.PooledTransport(clock.runtime(tmp_path, 1), session=session)
    status, payload = transport("https://example.invalid", {}, 20)
    assert status == 503 and "private" not in json.dumps(payload)
    with pytest.raises(ValueError):
        transport("https://example.invalid", {}, 20)


def test_requests_json_error_is_not_retried_as_connection_failure(tmp_path, clock):
    response = requests.Response()
    response.status_code = 200
    response._content = b"invalid json synthetic body"
    response._content_consumed = True
    transport = persistent.PooledTransport(clock.runtime(tmp_path, 1), session=Session([response]))
    with pytest.raises(ValueError, match="JSON inválido"):
        transport("https://example.invalid", {}, 20)
    assert transport.statistics()["http_status_counts"] == {"200": 1}


def test_original_client_acceptance_uses_pooled_transport_without_network(prepared, clock):
    class QuerySession(Session):
        def __init__(self):
            super().__init__([])

        def get(self, url, **kwargs):
            self.calls.append(url)
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            candidate = {
                "id": 1,
                "artistName": params["artist_name"][0],
                "trackName": params["track_name"][0],
                "albumName": None,
                "duration": 200,
                "plainLyrics": "Synthetic line one\nSynthetic line two",
                "syncedLyrics": None,
                "instrumental": False,
            }
            return Response(200, candidate if parsed.path == "/api/get" else [candidate])

    runtime = clock.runtime(prepared, 1)
    session = QuerySession()
    transport = persistent.PooledTransport(runtime, session=session)

    def factory(cfg):
        return manual.LRCLIBClient(cfg, transport=transport, sleep_fn=runtime.sleep)

    assert persistent.run(prepared, runtime_factory=clock.runtime, client_factory=factory) == 0
    assert len(session.calls) == 6
    assert persistent.snapshot(prepared)["accepted"] == 3
    assert clock.waited >= 1.5


def test_breaker_cools_down_and_resumes_with_original_attempt_limits(prepared, clock, monkeypatch):
    config = manual.load_yaml(manual.CONFIG)
    config["collection"]["circuit_breaker"]["consecutive_technical_errors"] = 2
    monkeypatch.setattr(manual, "load_yaml", lambda _: config)
    calls = []

    class Recovering:
        def __init__(self, config):
            self.cache_dir = None

        def lookup(self, query):
            status = 503 if len(calls) < 2 else 200
            calls.append(status)
            value = envelope(query, status=status)
            manual.atomic_json(self.cache_dir / f"{value['cache_key']}.json", value)
            return value

    assert (
        persistent.run(
            prepared,
            retry_errors_after=True,
            runtime_factory=clock.runtime,
            client_factory=Recovering,
        )
        == 0
    )
    assert calls == [503, 503, 200, 200, 200]
    assert clock.waited >= 3600  # Pausa do breaker e pausa antes do passe de erros.
    assert persistent.snapshot(prepared)["accepted"] == 3
    saved = persistent.read_json(prepared / "persistent_progress.json")
    assert saved["restarts_this_run"] == 1


def test_automatic_error_passes_never_exceed_three_cycles(prepared, clock):
    calls = []
    assert (
        persistent.run(
            prepared,
            retry_errors_after=True,
            runtime_factory=clock.runtime,
            client_factory=fake_client(503, calls),
        )
        == 0
    )
    assert len(calls) == 9
    counts = persistent.snapshot(prepared)
    assert counts["attempt_limit_reached"] == 3 and counts["retryable_errors"] == 0
    assert clock.waited == pytest.approx(2 * 1800)  # Duas pausas entre três passes.


def test_restart_limit_preserves_next_cooldown(prepared, clock, monkeypatch):
    config = manual.load_yaml(manual.CONFIG)
    config["collection"]["circuit_breaker"]["consecutive_technical_errors"] = 2
    monkeypatch.setattr(manual, "load_yaml", lambda _: config)
    assert (
        persistent.run(
            prepared, max_restarts=0, runtime_factory=clock.runtime, client_factory=fake_client(503)
        )
        == 2
    )
    saved = persistent.read_json(prepared / "persistent_progress.json")
    assert saved["reason"] == "maximum_restarts_reached"
    assert persistent.timestamp(saved["next_retry_at"]) == pytest.approx(
        clock.now() + 1800, abs=1e-5, rel=0
    )
    assert (
        persistent.run(prepared, runtime_factory=clock.runtime, client_factory=fake_client()) == 0
    )
    assert clock.waited >= 1800 - 1e-5
    assert persistent.snapshot(prepared)["technical_errors"] == 2


def test_limit_is_total_across_restarts(prepared, clock, monkeypatch):
    config = manual.load_yaml(manual.CONFIG)
    config["collection"]["circuit_breaker"]["consecutive_technical_errors"] = 2
    monkeypatch.setattr(manual, "load_yaml", lambda _: config)
    calls = []
    assert (
        persistent.run(
            prepared, limit=3, runtime_factory=clock.runtime, client_factory=fake_client(503, calls)
        )
        == 0
    )
    assert len(calls) == 3
    saved = persistent.read_json(prepared / "persistent_progress.json")
    assert saved["processed_this_run"] == 3 and saved["reason"] == "batch_limit_reached"


def test_interruption_after_cache_is_recovered_without_duplicate_query(prepared, clock):
    calls = []
    assert (
        persistent.run(
            prepared,
            runtime_factory=clock.runtime,
            client_factory=fake_client(calls=calls, interrupt_after_write=True),
        )
        == 2
    )
    assert len(calls) == 1
    assert (
        persistent.run(
            prepared, runtime_factory=clock.runtime, client_factory=fake_client(calls=calls)
        )
        == 0
    )
    assert len(calls) == 3 and persistent.snapshot(prepared)["accepted"] == 3


def test_time_budget_during_cooldown_does_not_issue_requests(prepared, clock):
    manual.atomic_json(
        prepared / "persistent_progress.json", {"next_retry_at": persistent.iso(clock.now() + 1800)}
    )
    calls = []
    assert (
        persistent.run(
            prepared,
            max_hours=1 / 60,
            runtime_factory=clock.runtime,
            client_factory=fake_client(calls=calls),
        )
        == 2
    )
    saved = persistent.read_json(prepared / "persistent_progress.json")
    assert calls == [] and saved["reason"] == "time_budget_reached"
    assert saved["next_retry_at"] is not None


def test_seal_never_rewrites_original_signature_and_rejects_changes(prepared, clock):
    with closing(manual.connect(prepared, readonly=True)) as db:
        before = manual.meta_get(db, "signature")
    persistent.seal(prepared)
    with closing(manual.connect(prepared, readonly=True)) as db:
        assert manual.meta_get(db, "signature") == before
    path = prepared / "persistent_protocol.json"
    value = persistent.read_json(path)
    value["requests_version"] = "different"
    manual.atomic_json(path, value)
    with pytest.raises(ValueError, match="Supervisor"):
        persistent.run(prepared, runtime_factory=clock.runtime, client_factory=fake_client())


def test_second_supervisor_cannot_start_even_during_cooldown(prepared, clock):
    with (
        manual.exclusive(prepared / "persistent_supervisor_lock"),
        pytest.raises(RuntimeError, match="Outro script"),
    ):
        persistent.run(prepared, runtime_factory=clock.runtime, client_factory=fake_client())
