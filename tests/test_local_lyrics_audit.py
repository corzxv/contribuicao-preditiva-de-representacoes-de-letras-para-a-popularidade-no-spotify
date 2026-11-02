"""Auditoria em SQLite/caches sintéticos, sem modelo ou rede."""

import json
import socket
from contextlib import closing

import pytest

from tcc_music_popularity import local_lyrics_audit as audit
from tcc_music_popularity import manual_lyrics as manual
from tcc_music_popularity.io import sha256_file


@pytest.fixture
def example(tmp_path, monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Rede proibida")

    monkeypatch.setattr(socket.socket, "connect", denied)
    source, work, output = (tmp_path / n for n in ("source", "local", "out"))
    for path in (source, work):
        path.mkdir()
        with closing(manual.connect(path)) as db:
            manual.init_db(db)
            db.execute("CREATE TABLE local_jobs(state TEXT)")
            db.execute("INSERT INTO local_jobs VALUES ('complete')")
            for n, split in enumerate(("development_train", "holdout_test")):
                q = {"split": split, "artist_name_query": "Artist", "track_name_query": "Song"}
                db.execute(
                    "INSERT INTO queries(query_id,composition_key,data,status) VALUES (?,?,?,?)",
                    (str(n), str(n), json.dumps(q), "accepted_exact_unique"),
                )
                t = {
                    "track_id": str(n),
                    "split": split,
                    "artist_group_id": str(n),
                    "composition_group_id": str(n),
                }
                db.execute("INSERT INTO tracks VALUES (?,?,?)", (str(n), str(n), json.dumps(t)))
            db.commit()

    def reader(row):
        key = row["query_id"]
        return {
            "split": json.loads(row["data"])["split"],
            "query_id": key,
            "track_id": key,
            "source_strict_sha256": key,
            "lyrics_sha256": key,
            "private_lyrics": "Synthetic secret",
        }

    monkeypatch.setattr(audit, "read_accepted_text", reader)
    return source, work, output


def summary(output):
    return json.loads(next(output.glob("*/summary.json")).read_text())


def test_full_readonly_audit(example, capsys):
    source, work, output = example
    before = sha256_file(work / "state.sqlite")
    assert audit.audit(source, work, output) == 0
    result = summary(output)
    assert (
        result["unique_strict_texts"] == 2 and result["manifest_and_splits_identical_to_original"]
    )
    assert result["input_files_unchanged"] and result["complete"]
    assert sha256_file(work / "state.sqlite") == before
    assert "Synthetic secret" not in capsys.readouterr().out
    assert "Synthetic secret" not in next(output.glob("*/accepted_text_index.jsonl")).read_text()


def test_shared_hash_requires_review(example, monkeypatch):
    reader = audit.read_accepted_text
    monkeypatch.setattr(
        audit, "read_accepted_text", lambda row: {**reader(row), "lyrics_sha256": "shared"}
    )
    assert audit.audit(*example) == 2
    assert summary(example[2])["shared_normalized_hashes_between_splits"] == 1


def test_cache_error_is_not_success(example, monkeypatch):
    def broken(row):
        raise ValueError("Cache corrompido")

    monkeypatch.setattr(audit, "read_accepted_text", broken)
    assert audit.audit(*example) == 2
    assert summary(example[2])["integrity_errors"] == 2


def test_modified_split_detected(example):
    with closing(manual.connect(example[1])) as db:
        db.execute(
            "UPDATE tracks SET data=? WHERE track_id='0'", (json.dumps({"split": "holdout_test"}),)
        )
        db.commit()
    assert audit.audit(*example) == 2
    assert not summary(example[2])["manifest_and_splits_identical_to_original"]


def test_interruption_marked_partial(example, monkeypatch):
    def interrupted(row):
        raise KeyboardInterrupt

    monkeypatch.setattr(audit, "read_accepted_text", interrupted)
    assert audit.audit(*example) == 2
    assert not summary(example[2])["complete"]


def test_pending_collection_blocks_audit(example):
    with closing(manual.connect(example[1])) as db:
        db.execute("UPDATE local_jobs SET state='pending'")
        db.commit()
    with pytest.raises(ValueError, match="pendências"):
        audit.audit(*example)
