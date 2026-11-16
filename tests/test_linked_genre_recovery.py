"""A recuperação dirigida retoma consultas sem duplicar vínculos."""

import json
import sqlite3
from contextlib import closing

import polars as pl
import pytest

from tcc_music_popularity import linked_genre_recovery as mod


def test_resumes_without_requesting_finished_queries():
    queries = [{"track_name_query": name} for name in ("one", "two")]
    jobs = pl.DataFrame(
        {
            "query_id": [mod.fingerprint(query) for query in queries],
            "query_json": [json.dumps(query) for query in queries],
            "index_kind": ["principal", "principal"],
        }
    )
    observed = []

    def lookup(_, index, query):
        assert index == "fixture"
        observed.append(query)
        return {"outcome": "sem_candidato_compativel"}, None

    with closing(sqlite3.connect(":memory:")) as db:
        args = (db, jobs, None, {"principal": "fixture"})
        assert mod.process(*args, {"version": 1}, 1, lookup=lookup) == 2
        assert len(observed) == 1
        with pytest.raises(ValueError, match="outra origem"):
            mod.process(*args, {"version": 2}, None, lookup=lookup)
        assert mod.process(*args, {"version": 1}, None, lookup=lookup) == 2
        assert sorted(observed, key=lambda q: q["track_name_query"]) == queries
