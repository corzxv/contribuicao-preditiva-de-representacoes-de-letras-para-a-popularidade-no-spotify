"""Apenas dados sintéticos; sem executar o catálogo real."""

import csv
import json
from pathlib import Path

import numpy as np
import polars as pl
import pytest
import yaml

from tcc_music_popularity.catalog_audit import ACOUSTIC, ROOT, sha256
from tcc_music_popularity.catalog_sampling import (
    CERTAINTY,
    SEED,
    SamplingError,
    allocate,
    draw,
    load_catalog,
    read_original_csv,
    run,
    weighted_summary,
)


def key(genre):
    return 'S|["' + genre + '","2000–2009","0–19"]'


def make_fixture(folder: Path):
    header = ["", "track_id", "track_name", "artist_name", "popularity", "year", "genre", *ACOUSTIC]
    rows = []
    for genre, year, popularity, size in [
        ("A", "2005", "10", 10),
        ("A", "2015", "35", 8),
        ("B", "2021", "65", 6),
        ("B", "2021", "75", 2),
        ("C", "2003", "45", 1),
        ("D", "2015", "15", 4),
        ("A", "2023", "85", 1),
        ("B", "2023", "90", 1),
    ]:
        for _ in range(size):
            index = len(rows)
            row = {name: "0.5" for name in ACOUSTIC}
            row.update(
                {
                    "": str(index),
                    "track_id": f"id_{index:03d}",
                    "track_name": "Título igual",
                    "artist_name": f"Crédito {index % 4}",
                    "popularity": popularity,
                    "year": year,
                    "genre": genre,
                    "key": "1",
                    "mode": "1",
                    "time_signature": "4",
                    "tempo": "120",
                    "duration_ms": "180000",
                    "loudness": "-10",
                }
            )
            rows.append(row)
    # Estratos integrais pequenos: conservar ausências e problemas acústicos.
    rows[24]["track_name"] = ""
    rows[24]["artist_name"] = "NA"
    rows[24]["energy"] = "2"
    rows[24]["tempo"] = "0"
    rows[25]["energy"] = "NaN"
    rows[25]["loudness"] = ""
    source = folder / "catalog.csv"
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    audit = {
        "completed": True,
        "status": "completed",
        "input": {
            "path": str(source),
            "size_bytes": source.stat().st_size,
            "sha256": sha256(source),
        },
        "structure": {"rows": 33, "schema": [{"original_header": name} for name in header]},
        "duplicates": {"distinct_ids": 33},
        "quality_rules": {
            "rules": yaml.safe_load(
                (ROOT / "configs/quality_rules.yaml").read_text(encoding="utf-8")
            )["spotify"]
        },
        "scopes": {
            "linha": {
                "n": 33,
                "popularity": {"thresholds_overlapping": {"80": 2}},
                "time": {
                    "year": {
                        "annual": [
                            {"year": str(y), "n": n}
                            for y, n in [(2003, 1), (2005, 10), (2015, 12), (2021, 8), (2023, 2)]
                        ]
                    }
                },
                "genres": [
                    {"genre": g, "n": n} for g, n in [("A", 19), ("B", 9), ("C", 1), ("D", 4)]
                ],
            }
        },
    }
    audit_path = folder / "audit.json"
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    return source, audit_path, audit


def test_largest_remainders_small_strata_and_exact_integer_tie():
    counts = {key("b"): 5, key("a"): 5, key("small1"): 1, key("small2"): 2, CERTAINTY: 3}
    result = {r["stratum_id"]: r for r in allocate(counts, 11)}
    assert result[key("a")]["n_h"] == 3
    assert result[key("b")]["n_h"] == 2
    for k in [key("small1"), key("small2"), CERTAINTY]:
        assert result[k]["certainty_selection"] is True
        assert result[k]["sampling_weight"] == 1
        assert result[k]["inclusion_probability"] == 1
    assert sum(r["n_h"] for r in result.values()) == 11
    assert allocate(counts, 11) == allocate(dict(reversed(list(counts.items()))), 11)
    with pytest.raises(SamplingError, match="Orçamento"):
        allocate(counts, 9)
    assert all(r["certainty_selection"] for r in allocate(counts, sum(counts.values())))
    assert allocate({CERTAINTY: 3}, 3)[0]["n_h"] == 3
    large_counts_only = {
        key("large"): 900_000,
        key("medium"): 99_000,
        key("tiny"): 1,
        CERTAINTY: 499,
    }
    large_allocation = allocate(large_counts_only, 200_000)
    assert sum(r["n_h"] for r in large_allocation) == 200_000
    assert all(0 < r["n_h"] <= r["N_h"] for r in large_allocation)


def test_weighted_quantiles_moments_and_missing_denominators():
    summary = weighted_summary(
        np.array([0.0, 10.0, 20.0, np.nan, np.inf]), np.array([1.0, 1.0, 8.0, 50.0, 50.0])
    )
    assert summary["mean"] == pytest.approx(17)
    assert summary["std_population"] == pytest.approx(np.sqrt(41))
    assert summary["q05"] == 0
    assert summary["q25"] == summary["q50"] == 20
    assert summary["n_observed"] == 3 and summary["weight_observed"] == 10
    empty = weighted_summary(np.array([np.nan]), np.array([2.0]))
    assert empty["mean"] is None and empty["weight_observed"] == 0


def test_draw_stability_no_replacement_and_same_titles(tmp_path):
    source, _, audit = make_fixture(tmp_path)
    _, frame, _ = load_catalog(source, audit)
    allocation = allocate(dict(frame.group_by("stratum_id").len().iter_rows()), 20)
    indices = draw(frame, allocation)
    assert np.array_equal(indices, draw(frame.reverse(), allocation))
    assert len(indices) == len(set(indices)) == 20
    selected = frame.filter(pl.col("_s_row").is_in(indices))
    assert selected.filter(pl.col("_s_pop") >= 80).height == 2
    assert selected["_s_title"].drop_nulls().n_unique() == 1
    assert selected["_s_id"].n_unique() == 20
    assert selected["_s_artist"].null_count() == 1


@pytest.fixture(scope="module")
def completed(tmp_path_factory):
    folder = tmp_path_factory.mktemp("sample")
    source, audit_path, _ = make_fixture(folder)
    output = folder / "result"
    summary = run(source, audit_path, output, total=20)
    return source, audit_path, output, summary


def test_end_to_end_preservation_weights_outputs_and_rerun(completed):
    source, audit_path, output, summary = completed
    assert summary["status"] == "completed"
    assert all(summary["checks"].values())
    assert summary["weight_sum"] == pytest.approx(33)
    sample = pl.read_parquet(output / "amostra_spotify_200k.parquet")
    assert sample.height == sample["track_id"].n_unique() == 20
    assert sample["seed"].unique().to_list() == [SEED]
    assert "" in sample.columns
    # Preservação de strings originais, não substituição por normalizações.
    missing_credit = sample.filter(pl.col("track_id") == "id_024")
    assert missing_credit["artist_name"][0] == "NA"
    assert missing_credit["track_name"][0] == ""
    assert missing_credit["energy"][0] == "2"
    before = {p.name: (sha256(p), p.stat().st_mtime_ns) for p in output.iterdir()}
    reused = run(source, audit_path, output, total=20)
    assert reused == summary
    assert before == {p.name: (sha256(p), p.stat().st_mtime_ns) for p in output.iterdir()}
    assert len(list(output.glob("*.png"))) == 3
    for name in [
        "comparacao_catalogo_amostra_200k.csv",
        "relatorio_amostra_200k.md",
        "resumo_amostra_200k.json",
    ]:
        text = (output / name).read_text(encoding="utf-8-sig")
        assert "id_024" not in text and "Título igual" not in text and "Crédito 0" not in text
    assert sha256(source) == summary["input_sha256"]


def test_weighted_comparison_counts_and_quality(completed):
    _, _, output, _ = completed
    with (output / "comparacao_catalogo_amostra_200k.csv").open(
        encoding="utf-8-sig", newline=""
    ) as stream:
        rows = list(csv.DictReader(stream))

    def value(scope, section, variable, category, metric):
        matches = [
            r
            for r in rows
            if (r["scope"], r["section"], r["variable"], r["category"], r["metric"])
            == (scope, section, variable, category, metric)
        ]
        assert len(matches) == 1
        return float(matches[0]["value"])

    for scope in ["catalogo", "amostra_com_pesos"]:
        assert value(scope, "distribution", "_s_pop", "90", "count") == 1
        assert value(scope, "distribution", "_s_genre", "A", "count") == pytest.approx(19)
        assert value(scope, "quality", "energy", "out_of_local_domain", "count") == 1
        assert value(scope, "quality", "energy", "invalid_parse_or_nonfinite", "count") == 1
    assert value("amostra_sem_pesos", "distribution", "_s_pop", "99", "count") == 0


@pytest.mark.parametrize(
    ("column", "new_value", "match"),
    [
        ("track_id", "id_001", "IDs ausentes/repetidos"),
        ("track_id", "", "IDs ausentes/repetidos"),
        ("popularity", "101", "popularidades"),
        ("year", "1999", "Novidade material"),
        ("genre", "novidade", "gêneros divergem"),
    ],
)
def test_preflight_blocks_without_silent_correction(tmp_path, column, new_value, match):
    source, _, audit = make_fixture(tmp_path)
    raw = read_original_csv(source)
    values = raw[column].to_list()
    values[0] = new_value
    raw.with_columns(pl.Series(column, values)).write_csv(source)
    with pytest.raises(SamplingError, match=match):
        load_catalog(source, audit)


def test_hash_mismatch_before_output_and_preserve_existing(tmp_path, completed):
    source, audit_path, _ = make_fixture(tmp_path)
    with source.open("a", encoding="utf-8") as stream:
        stream.write("\n")
    with pytest.raises(SamplingError, match="SHA-256"):
        run(source, audit_path, tmp_path / "blocked", total=20)
    assert not (tmp_path / "blocked").exists()
    source, audit_path, output, _ = completed
    before = sha256(output / "amostra_spotify_200k.parquet")
    with pytest.raises(SamplingError, match="configuração"):
        run(source, audit_path, output, total=21)
    assert sha256(output / "amostra_spotify_200k.parquet") == before


def test_tampered_output_blocked_without_resampling(tmp_path, completed):
    source, audit_path, original, summary = completed
    output = tmp_path / "previous"
    output.mkdir()
    # Manifesto válido, mas um agregado alterado/ausente: não tocar na amostra.
    sample_name = "amostra_spotify_200k.parquet"
    (output / sample_name).write_bytes((original / sample_name).read_bytes())
    (output / "resumo_amostra_200k.json").write_text(json.dumps(summary), encoding="utf-8")
    before = sha256(output / sample_name)
    with pytest.raises(SamplingError, match="alterado/ausente"):
        run(source, audit_path, output, total=20)
    assert sha256(output / sample_name) == before
