"""Sequenciamento simulado: não executa índice, coleta ou esperas reais."""

import socket

import pytest

from tcc_music_popularity import local_sequence as seq


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Rede proibida")

    monkeypatch.setattr(socket.socket, "connect", denied)


@pytest.fixture
def setup(tmp_path):
    work = tmp_path / "workspace"
    index = tmp_path / "index"
    work.mkdir()
    index.mkdir()
    (work / "state.sqlite").touch()
    seq.save_json(index / "progress.json", {"complete": True})
    return work, index


def fake_executor(work, calls, *, code=0, error=0, pending_first=10, stale=False):
    def execute(*args, limit=None):
        calls.append(limit)
        seq.save_json(
            work / "local_progress.json",
            {
                "stage": "batch_complete",
                "errors_this_run": error,
                "stop_reason": None,
                "processed_this_run": 50,
                "planned_this_run": 50,
                "local_pending": pending_first if limit == 50 else 0,
                "local_retryable_errors": 0,
                "local_exhausted_errors": 0,
                "updated_at": "2000-01-01T00:00:00+00:00" if stale else seq.utc_now(),
            },
        )
        return code

    return execute


def run(setup, calls, **kwargs):
    work, index = setup
    return seq.run(
        workspace=work,
        index_dir=index,
        busy=kwargs.pop("busy", lambda _: False),
        executor=kwargs.pop("executor", fake_executor(work, calls)),
        **kwargs,
    )


def test_sample_then_full_only_after_index_and_unlock(setup):
    calls, sleeps = [], []
    seq.save_json(setup[1] / "progress.json", {"complete": False})

    def sleep(seconds):
        assert not calls
        sleeps.append(seconds)
        seq.save_json(setup[1] / "progress.json", {"complete": True})

    assert run(setup, calls, busy=lambda _: not sleeps, sleeper=sleep) == 0
    assert calls == [50, None] and sleeps == [15]


@pytest.mark.parametrize("options", [{"code": 2}, {"error": 1}, {"stale": True}])
def test_failed_or_stale_sample_never_starts_full(setup, options):
    calls = []
    assert run(setup, calls, executor=fake_executor(setup[0], calls, **options)) == 2
    assert calls == [50]


def test_no_more_pending_skips_full(setup):
    calls = []
    assert run(setup, calls, executor=fake_executor(setup[0], calls, pending_first=0)) == 0
    assert calls == [50]


def test_stopped_incomplete_index_does_not_start_lookup(setup):
    seq.save_json(setup[1] / "progress.json", {"complete": False})
    calls = []
    assert run(setup, calls, sleeper=lambda _: None) == 2
    assert not calls


def test_wait_budget_is_bounded(setup):
    calls, ticks = [], iter([0, 100])
    assert run(setup, calls, busy=lambda _: True, clock=lambda: next(ticks), wait_hours=0.001) == 2
    assert not calls


def test_interruption_preserves_checkpoint(setup):
    calls = []

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    assert run(setup, calls, executor=interrupt) == 2
    assert seq.load_json(setup[0] / "local_sequence/progress.json")["stage"] == "stopped"


def test_missing_workspace_is_not_created(tmp_path):
    with pytest.raises(ValueError):
        seq.run(workspace=tmp_path / "absent")
    assert not (tmp_path / "absent").exists()


def test_lock_probe_does_not_keep_worker_locked(setup):
    work = setup[0]
    with seq.exclusive(work):
        assert seq.workspace_busy(work)
    assert not seq.workspace_busy(work)
