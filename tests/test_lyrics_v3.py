import json
import math
import sqlite3
from contextlib import closing

import numpy as np
import polars as pl
import pytest
from test_lyrics_recovery import no_network, recovery_setup  # noqa: F401
from test_sample_lyrics import candidate, query
from test_sample_lyrics import setup as baseline_setup  # noqa: F401

from tcc_music_popularity import lyrics_evaluation as mod
from tcc_music_popularity import lyrics_statistical_opinion as stat


def test_candidate_exclusion_optional_sync_and_content():
    result, _ = mod.decide(query(), [candidate(), candidate(2, title="Song - Live")])
    assert result["status"] == "accepted"
    result, _ = mod.decide(query(), [candidate(syncedLyrics="unsupported")])
    assert result["status"] == "accepted" and result["warnings"]
    r, lyric = mod.decide(
        query(),
        [
            candidate(
                text="A line\nRepeated repeated",
                syncedLyrics="[00:01]a line repeated\n[00:02]repeated",
            ),
            candidate(2, text="a LINE repeated repeated"),
            candidate(3, text=None),
        ],
    )
    assert r["status"] == "accepted" and r["empty_ignored"] == 1
    assert lyric["plain_text_source"] == "A line\nRepeated repeated"
    for changed in (
        "A line repeated",
        "A different line repeated repeated",
        "repeated repeated A line",
        "A line\nRepeated-repeated",
    ):
        assert (
            mod.decide(
                query(), [candidate(text="A line repeated repeated"), candidate(2, text=changed)]
            )[0]["status"]
            == "ambiguous"
        )
    assert (
        mod.decide(query(), [candidate(text="words", syncedLyrics="[00:01]other words")])[0][
            "reason"
        ]
        == "plain_synced_content_conflict"
    )
    assert (
        mod.decide(
            query("Song - Live Paris"), [candidate(title="Song - Live London"), candidate()]
        )[0]["status"]
        != "accepted"
    )
    assert (
        mod.decide(query(), [candidate(), candidate(2, text="Homonym different text")])[0]["status"]
        == "ambiguous"
    )
    assert (
        mod.decide(query("Live Forever"), [candidate(title="Live Forever")])[0]["status"]
        == "accepted"
    )
    assert mod.decide(query(), [], "limit")[0]["reason"].startswith("operational_limit")


def test_variants_proposed_not_accepted():
    r, _ = mod.decide(query("Song", "Beyonce"), [candidate(artistName="Beyoncé")])
    assert r["status"] == "ambiguous" and r["proposed_ids"] == [1]
    assert (
        mod.decide(query("Song", "Band & Friends"), [candidate(artistName="Band")])[0]["status"]
        != "accepted"
    )
    assert (
        mod.decide(query("Song", "Old Artist feat. Guest"), [candidate(title="Song (ft. Guest)")])[
            0
        ]["status"]
        == "accepted"
    )
    assert mod.comparison_text("don't") != mod.comparison_text("dont")
    assert mod.comparison_text("東京\n東京") == mod.comparison_text("東京 東京")
    with pytest.raises(ValueError):
        mod.decide({**query(), "popularity": 100}, [])


def test_paginated_metadata_filter_before_text():
    index, dump = sqlite3.connect(":memory:"), sqlite3.connect(":memory:")
    index.row_factory = dump.row_factory = sqlite3.Row
    index.executescript(mod.v2.local.INDEX_SQL)
    dump.execute(
        "CREATE TABLE lyrics(id INTEGER PRIMARY KEY,track_id INTEGER,plain_lyrics TEXT,synced_lyrics TEXT,instrumental INTEGER)"
    )
    for i in range(1, 602):
        # Nenhuma revisão para os 600 incompatíveis: não devem ser lidas.
        index.execute(
            "INSERT INTO catalog VALUES (?,?,?,?,?,?,?,?,?)",
            (
                i,
                "old artist",
                "song",
                "song",
                "Song - Live" if i < 601 else "Song",
                "Old Artist",
                "Album",
                200,
                i,
            ),
        )
    dump.execute("INSERT INTO lyrics VALUES (601,601,'Synthetic',NULL,0)")
    candidates, incomplete = mod.retrieve(query(), [(index, False)], dump, math.inf)
    assert len(candidates) == 1 and incomplete is None
    assert mod.decide(query(), candidates)[0]["status"] == "accepted"
    with pytest.raises(TimeoutError):
        mod.retrieve(query(), [(index, False)], dump, 0)
    index.close()
    dump.close()


def test_probability_plan_fixed_sizes_and_no_duplicate():
    records = [
        {
            "track_id": str(i),
            "lyrics_status": "not_found" if i < 700 else "ambiguous" if i < 1100 else "accepted",
            "lyrics_reason": "a" if i % 3 else "b",
        }
        for i in range(1250)
    ]
    frame = pl.DataFrame(records)
    a, b = mod.diagnostic_plan(frame), mod.diagnostic_plan(frame.reverse())
    assert a.equals(b) and a.height == a["track_id"].n_unique() == 1000
    assert dict(a.group_by("diagnostic_group").len().iter_rows()) == {
        "not_found": 600,
        "ambiguous": 300,
        "accepted": 100,
    }
    assert np.allclose(
        a["diagnostic_probability"].to_numpy(),
        a["diagnostic_n"].to_numpy() / a["diagnostic_N"].to_numpy(),
    )


def test_taylor_uses_full_strata_and_fpc():
    frame = pl.DataFrame(
        {"stratum_id": ["a"] * 4, "N_h": [8] * 4, "n_h": [4] * 4, "sampling_weight": [2.0] * 4}
    )
    r = stat.domain_ratio(
        np.array([2.0, 100.0, 6.0, -1.0]), np.array([True, False, True, False]), frame
    )
    assert r["estimate"] == 4 and r["se"] == pytest.approx(math.sqrt(4 / 3))
    census = frame.with_columns(pl.lit(4).alias("N_h"), pl.lit(1.0).alias("sampling_weight"))
    assert (
        stat.domain_ratio(np.array([2.0, 100.0, 6.0, -1.0]), np.ones(4, dtype=bool), census)["se"]
        == 0
    )
    assert stat.domain_ratio(np.ones(4), np.ones(4, dtype=bool), frame)["se"] is None
    with pytest.raises(ValueError, match="integral"):
        stat.domain_ratio(np.ones(2), np.ones(2, dtype=bool), frame.head(2))


def test_tost_three_outcomes_and_multiplicity():
    def decision(d, se):
        return stat.equivalence({"estimate": d, "se": se, "df": 100, "n": 100}, 0, 1, 100)

    assert decision(0.2, 0.1)["conclusion"] == "equivalent"
    assert decision(2, 0.1)["family_relevant"]
    assert decision(0.9, 0.2)["conclusion"] == "inconclusive"
    assert not decision(1.3, 0.1)["family_relevant"]


def test_budget_resume_apply_and_statistics(request, monkeypatch):
    paths = request.getfixturevalue("recovery_setup")
    assert mod.v2.execute(**paths) == 0
    root = paths["workspace"].parent
    args = dict(
        sample_dir=paths["sample_path"].parent,
        baseline=paths["workspace"],
        old_workspace=paths["baseline"],
        index_paths=[(p, False) for p in paths["old_indexes"]] + [(paths["index_dir"], True)],
        workspace=root / "v3",
        sizes=(0, 1, 2),
        expected=11,
    )
    output = root / "evaluation"
    assert mod.run("evaluate", 1e-9, output=output, **args) == 2
    with pytest.raises(ValueError, match="primeiro"):
        mod.run("apply", output=root / "full", **args)
    assert mod.run("evaluate", output=output, **args) == 0
    with closing(mod.v1.state_connection(args["workspace"])) as db:
        before = dict(db.execute("SELECT query_id,attempts FROM queries WHERE status!='pending'"))
    assert mod.run("apply", output=root / "full", **args) == 0
    with closing(mod.v1.state_connection(args["workspace"])) as db:
        assert all(
            db.execute("SELECT attempts FROM queries WHERE query_id=?", (k,)).fetchone()[0] == v
            for k, v in before.items()
        )
    final = pl.read_parquet(args["workspace"] / "resultados_faixas_200k.parquet")
    original = pl.read_parquet(paths["sample_path"])
    assert final.height == final["track_id"].n_unique() == 11
    assert final.select(original.columns).sort("track_id").equals(original.sort("track_id"))
    report = json.loads((output / "resumo.json").read_text())
    assert not report["approximate_auto_acceptance"] and report["new_indexes"] == 0
    pairs = json.loads(
        (args["workspace"] / "pares_revisao_privados.json").read_text(encoding="utf-8")
    )
    assert len(pairs) <= 100 and all(r["review_label"] == "" for r in pairs)
    if pairs:
        pairs[0]["review_label"] = "inconclusivo"
        pairs[0]["review_notes"] = "Synthetic manual annotation"
        (args["workspace"] / "pares_revisao_privados.json").write_text(
            json.dumps(pairs), encoding="utf-8"
        )
        with closing(mod.v1.state_connection(args["workspace"])) as db:
            mod.review_pairs(
                db,
                pl.read_parquet(paths["workspace"] / "resultados_faixas_200k.parquet"),
                args["workspace"],
            )
        preserved = json.loads(
            (args["workspace"] / "pares_revisao_privados.json").read_text(encoding="utf-8")
        )
        assert any(r["review_notes"] == "Synthetic manual annotation" for r in preserved)
    # Referência populacional sintética apenas: não acessa arquivo Spotify/dump real.
    aggregates = [
        dict(r, scope="catalogo")
        for r in mod.v1.coverage_tables(final)
        if r["scope"] == "complete|weighted"
    ]
    aggregate_path = paths["sample_path"].parent / "comparacao_catalogo_amostra_200k.csv"
    mod.v2.write_csv(aggregate_path, aggregates)
    summary_path = paths["sample_summary"]
    summary = json.loads(summary_path.read_text())
    summary["output_hashes"][aggregate_path.name] = mod.v1.sha256(aggregate_path)
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    monkeypatch.setattr(
        mod.v1, "stable_readonly", lambda *a: pytest.fail("Parecer não pode acessar SQLite/SSD")
    )
    stat.run(
        args["workspace"] / "resultados_faixas_200k.parquet",
        root / "opinion",
        sample_dir=args["sample_dir"],
        expected=11,
    )
    opinion = json.loads((root / "opinion/resumo.json").read_text())
    assert opinion["ssd_queries"] == 0 and opinion["design_checks_passed"]
    assert (root / "opinion/diagnostico_equivalencia.csv").exists()
