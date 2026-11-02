"""Transferência e extração inteiramente sintéticas, sem rede nem disco D:."""

import gzip
import hashlib
import json
import random
import socket
import sqlite3
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

from tcc_music_popularity import lrclib_dump as dump


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Rede real proibida")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(requests.Session, "request", denied)


class Response:
    def __init__(self, status, headers, body=b"", interrupt=None):
        self.status_code, self.headers, self.body, self.interrupt = status, headers, body, interrupt

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def iter_content(self, chunk_size):
        # Blocos pequenos garantem checkpoints e retomadas mesmo na amostra mínima.
        for offset in range(0, len(self.body), 1024):
            if offset and self.interrupt:
                raise self.interrupt
            yield self.body[offset : offset + 1024]


class Session:
    def __init__(self, spec, payload, *, ignore_range=False, interrupt=None, etag=None):
        self.spec, self.payload = spec, payload
        self.ignore_range, self.interrupt = ignore_range, interrupt
        self.etag = spec.etag if etag is None else etag
        self.headers, self.offsets, self.closed = {}, [], False

    def head(self, *args, **kwargs):
        return Response(200, {"Content-Length": str(len(self.payload)), "ETag": f'"{self.etag}"'})

    def get(self, url, *, headers, **kwargs):
        start = int(headers["Range"].split("=")[1].split("-")[0])
        self.offsets.append(start)
        if self.ignore_range:
            return Response(
                200,
                {"Content-Length": str(len(self.payload)), "ETag": f'"{self.etag}"'},
                self.payload,
            )
        return Response(
            206,
            {
                "Content-Range": f"bytes {start}-{len(self.payload) - 1}/{len(self.payload)}",
                "Content-Length": str(len(self.payload) - start),
                "ETag": f'"{self.etag}"',
            },
            self.payload[start:],
            self.interrupt,
        )

    def close(self):
        self.closed = True


@pytest.fixture
def sample(tmp_path):
    database = tmp_path / "source.sqlite3"
    db = sqlite3.connect(database)
    db.executescript(
        "CREATE TABLE tracks(id INTEGER PRIMARY KEY, name TEXT); CREATE TABLE lyrics(id INTEGER PRIMARY KEY, synthetic_payload BLOB);"
    )
    db.execute("INSERT INTO tracks VALUES(1,'synthetic')")
    db.execute("INSERT INTO lyrics VALUES(1,?)", (random.Random(42).randbytes(12000),))
    db.commit()
    db.close()
    original = database.read_bytes()
    payload = gzip.compress(original, mtime=0)
    spec = dump.DumpSpec(
        "synthetic.sqlite3.gz",
        "https://example.invalid/dump",
        len(payload),
        len(original),
        "synthetic-etag",
    )
    return spec, payload, original


def prepare(destination, sample, **kwargs):
    spec, payload, _ = sample
    return dump.run(
        destination, spec=spec, reserve_bytes=0, session=Session(spec, payload), **kwargs
    )


def test_download_extract_crc_sqlite_and_idempotent_rerun(tmp_path, sample):
    destination = tmp_path / "destination"
    assert prepare(destination, sample) == 0
    spec, payload, original = sample
    files = dump.paths(destination, spec)
    state = dump.load_json(files["state"])
    assert state["status"] == "ready" and state["sqlite_quick_check"] == "ok"
    assert state["gzip_crc_verified"] is True
    assert files["archive"].read_bytes() == payload
    assert files["database"].read_bytes() == original
    assert state["download_sha256"] == hashlib.sha256(payload).hexdigest()
    assert state["database_sha256"] == hashlib.sha256(original).hexdigest()
    before = files["database"].stat().st_mtime_ns
    assert prepare(destination, sample) == 0
    assert files["database"].stat().st_mtime_ns == before


def test_download_interrupt_then_resume_from_verified_offset(tmp_path, sample):
    spec, payload, _ = sample
    destination = tmp_path / "destination"
    session = Session(spec, payload, interrupt=KeyboardInterrupt())
    assert dump.run(destination, spec=spec, reserve_bytes=0, session=session) == 2
    files = dump.paths(destination, spec)
    state = dump.load_json(files["state"])
    assert state["downloaded_bytes"] == 1024
    session = Session(spec, payload)
    assert dump.run(destination, spec=spec, reserve_bytes=0, session=session) == 0
    assert session.offsets == [1024]


def test_range_ignored_on_resume_never_appends_wrong_bytes(tmp_path, sample):
    spec, payload, _ = sample
    destination = tmp_path / "destination"
    dump.run(
        destination,
        spec=spec,
        reserve_bytes=0,
        session=Session(spec, payload, interrupt=KeyboardInterrupt()),
    )
    partial = dump.paths(destination, spec)["archive_part"]
    before = partial.read_bytes()
    assert (
        dump.run(
            destination,
            spec=spec,
            reserve_bytes=0,
            session=Session(spec, payload, ignore_range=True),
        )
        == 1
    )
    assert partial.read_bytes() == before


def test_changed_etag_blocks_before_download(tmp_path, sample):
    spec, payload, _ = sample
    destination = tmp_path / "destination"
    session = Session(spec, payload, etag="changed")
    assert dump.run(destination, spec=spec, reserve_bytes=0, session=session) == 1
    assert session.offsets == []
    assert not dump.paths(destination, spec)["archive_part"].exists()


def test_missing_space_blocks_network_and_leaves_unrelated_files(tmp_path, sample):
    spec, payload, _ = sample
    destination = tmp_path / "destination"
    destination.mkdir()
    unrelated = destination / "personal.txt"
    unrelated.write_text("preserve", encoding="utf-8")
    session = Session(spec, payload)
    assert (
        dump.run(
            destination,
            spec=spec,
            reserve_bytes=100,
            session=session,
            disk_usage=lambda _: SimpleNamespace(free=99),
        )
        == 1
    )
    assert unrelated.read_text() == "preserve" and session.offsets == []


def test_resume_discards_only_uncommitted_tail_of_owned_partial(tmp_path, sample):
    spec, payload, _ = sample
    destination = tmp_path / "destination"
    dump.run(
        destination,
        spec=spec,
        reserve_bytes=0,
        session=Session(spec, payload, interrupt=KeyboardInterrupt()),
    )
    files = dump.paths(destination, spec)
    with files["archive_part"].open("ab") as handle:
        handle.write(b"synthetic interrupted uncommitted tail")
    assert prepare(destination, sample) == 0
    assert files["archive"].read_bytes() == payload
    assert dump.load_json(files["state"])["recovered_uncommitted_tail"] is True


def test_corrupted_prefix_is_preserved_and_blocked(tmp_path, sample):
    spec, payload, _ = sample
    destination = tmp_path / "destination"
    dump.run(
        destination,
        spec=spec,
        reserve_bytes=0,
        session=Session(spec, payload, interrupt=KeyboardInterrupt()),
    )
    files = dump.paths(destination, spec)
    with files["archive_part"].open("r+b") as handle:
        handle.write(b"corrupt")
    before = files["archive_part"].read_bytes()
    assert prepare(destination, sample) == 1
    assert files["archive_part"].read_bytes() == before
    assert not files["archive"].exists()


def test_unknown_existing_archive_without_checkpoint_is_not_overwritten(tmp_path, sample):
    spec, _, _ = sample
    destination = tmp_path / "destination"
    destination.mkdir()
    path = dump.paths(destination, spec)["archive"]
    path.write_bytes(b"existing user data")
    with pytest.raises(ValueError, match="sem checkpoint"):
        prepare(destination, sample)
    assert path.read_bytes() == b"existing user data"


def test_extraction_interrupt_resumes_after_rechecking_prefix(tmp_path, sample, monkeypatch):
    spec, payload, original = sample
    destination = tmp_path / "destination"
    monkeypatch.setattr(dump, "CHUNK", 4096)
    old_write = dump.Transfer.checkpoint_write

    def interrupted(self, handle, block, digest, count_key, hash_key, status):
        old_write(self, handle, block, digest, count_key, hash_key, status)
        if count_key == "extracted_bytes":
            raise KeyboardInterrupt

    monkeypatch.setattr(dump.Transfer, "checkpoint_write", interrupted)
    assert prepare(destination, sample) == 2
    state = dump.load_json(dump.paths(destination, spec)["state"])
    assert state["extracted_bytes"] == 4096
    monkeypatch.setattr(dump.Transfer, "checkpoint_write", old_write)
    assert prepare(destination, sample, action="extract") == 0
    assert dump.paths(destination, spec)["database"].read_bytes() == original


def test_gzip_crc_failure_never_produces_ready_database(tmp_path, sample):
    spec, payload, original = sample
    corrupted = bytearray(payload)
    corrupted[-8] ^= 0xFF
    destination = tmp_path / "destination"
    assert prepare(destination, (spec, bytes(corrupted), original)) == 1
    files = dump.paths(destination, spec)
    assert not files["database"].exists()
    assert dump.load_json(files["state"])["gzip_crc_verified"] is False


def test_uncompressed_size_limit_blocks_expansion(tmp_path, sample):
    spec, payload, original = sample
    tiny = replace(spec, database_bytes=4096)
    destination = tmp_path / "destination"
    assert prepare(destination, (tiny, payload, original)) == 1
    assert not dump.paths(destination, tiny)["database"].exists()


def test_network_failures_are_bounded_and_partial_survives(tmp_path, sample):
    spec, payload, _ = sample
    destination = tmp_path / "destination"
    session = Session(spec, payload, interrupt=requests.ConnectionError("synthetic"))
    assert (
        dump.run(
            destination,
            spec=spec,
            reserve_bytes=0,
            session=session,
            max_retries=1,
            sleeper=lambda _: None,
            monotonic=iter(range(100000)).__next__,
        )
        == 1
    )
    assert session.offsets == [0, 1024]
    assert dump.paths(destination, spec)["archive_part"].stat().st_size == 2048


def test_header_or_sqlite_corruption_is_rejected(tmp_path, sample):
    spec, _, original = sample
    corrupted = b"X" + original[1:]
    payload = gzip.compress(corrupted, mtime=0)
    new = replace(spec, compressed_bytes=len(payload))
    destination = tmp_path / "destination"
    assert prepare(destination, (new, payload, corrupted)) == 1
    state = dump.load_json(dump.paths(destination, new)["state"])
    assert state["status"] == "failed" and "Cabeçalho" in state["reason"]


def test_destination_must_not_be_drive_root_or_repository():
    with pytest.raises(ValueError):
        dump.validate_destination(str(dump.PROJECT_ROOT))
    with pytest.raises(ValueError):
        dump.validate_destination(dump.PROJECT_ROOT.anchor)
    with pytest.raises(ValueError):
        dump.validate_destination("relative-folder")


def test_state_source_identity_cannot_change(tmp_path, sample):
    spec, payload, _ = sample
    destination = tmp_path / "destination"
    assert prepare(destination, sample, action="download") == 0
    state_path = dump.paths(destination, spec)["state"]
    state = json.loads(state_path.read_text())
    state["source"]["etag"] = "wrong"
    state_path.write_text(json.dumps(state))
    with pytest.raises(ValueError, match="Checkpoint"):
        dump.run(destination, spec=spec, reserve_bytes=0, session=Session(spec, payload))


def test_checkpoint_retries_brief_windows_replace_lock(tmp_path, monkeypatch):
    original = Path.replace
    attempts = []

    def temporarily_locked(self, target):
        attempts.append(1)
        if len(attempts) < 3:
            raise PermissionError("synthetic Windows sharing lock")
        return original(self, target)

    monkeypatch.setattr(Path, "replace", temporarily_locked)
    monkeypatch.setattr(dump.time, "sleep", lambda _: None)
    path = tmp_path / "checkpoint.json"
    dump.save_json(path, {"synthetic": True})
    assert len(attempts) == 3 and dump.load_json(path) == {"synthetic": True}


def test_time_budget_stops_without_network_transfer(tmp_path, sample):
    spec, payload, _ = sample
    destination = tmp_path / "destination"
    session = Session(spec, payload)
    assert dump.run(destination, spec=spec, reserve_bytes=0, session=session, max_hours=1e-9) == 2
    state = dump.load_json(dump.paths(destination, spec)["state"])
    assert state["reason"] == "time_budget_reached" and session.offsets == []
