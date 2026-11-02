"""Verificações exclusivamente sintéticas da auditoria original Spotify."""

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tcc_music_popularity.catalog_audit import ROOT, run

FIXTURE = Path(__file__).parent / "fixtures/spotify_catalog_audit.csv"


@pytest.fixture(scope="module")
def audited(tmp_path_factory):
    output = tmp_path_factory.mktemp("catalog") / "result"
    before = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/11_auditar_catalogo_spotify.py"),
            "--input",
            str(FIXTURE),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "[6/6]" in completed.stdout
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == before
    return output, json.loads((output / "resumo_catalogo_spotify.json").read_text(encoding="utf-8"))


def test_duplicates_units_and_popularity(audited):
    _, summary = audited
    assert summary["completed"] is True
    assert summary["input"]["size_bytes"] == FIXTURE.stat().st_size
    assert summary["structure"]["rows"] == 15
    dup = summary["duplicates"]
    assert dup["distinct_ids"] == 11
    assert dup["missing_id_rows"] == 1
    assert dup["exact_duplicate_excess_rows"] == 1
    assert dup["exact_duplicate_involved_rows"] == 2
    assert dup["substantive_duplicate_excess_rows"] == 2
    assert dup["repeated_equal_ids"] == 1
    assert dup["conflicting_ids"] == 1
    assert dup["rows_conflicting_ids"] == 2
    assert summary["conflicts_by_field"]["popularity"] == 1
    assert summary["conflicts_by_field"]["genre"] == 1
    assert dup["excess_rows_over_distinct_ids"] == 3
    line = summary["scopes"]["linha"]
    track = summary["scopes"]["track_id_sem_conflito"]
    assert line["n"] == 15 and track["n"] == 10
    assert line["popularity"]["invalid"] == 4
    assert line["popularity"]["missing"] == 1
    assert line["popularity"]["zero_count"] == 3
    assert track["popularity"]["zero_count"] == 1
    assert track["popularity"]["thresholds_overlapping"] == {"60": 5, "70": 4, "80": 3, "90": 2}
    assert track["popularity"]["mean"] == pytest.approx(400 / 6)
    assert track["popularity"]["median"] == 75
    assert track["popularity"]["q25"] == pytest.approx(62.5)
    assert track["popularity"]["q75"] == pytest.approx(87.5)


def test_dates_domains_genres_and_strata(audited):
    _, summary = audited
    line = summary["scopes"]["linha"]
    track = summary["scopes"]["track_id_sem_conflito"]
    assert line["time"]["year"]["missing"] == 1
    assert line["time"]["year"]["invalid"] == 2
    assert line["time"]["release_date"]["invalid"] == 4
    assert line["time"]["year"]["since_2020"] == 4
    assert line["genre_structure"]["ids_with_multiple_genre_cells"] == 1
    assert line["genre_structure"]["multi_label_hint_rows"] == 1
    assert line["acoustic"]["danceability"]["out_of_domain"] == 2
    assert line["acoustic"]["danceability"]["nonnumeric_or_nonfinite"] == 1
    assert line["acoustic"]["key"]["out_of_domain"] == 2
    assert line["acoustic"]["duration_ms"]["out_of_domain"] == 2
    assert line["versions"]["live"]["n"] == 3
    assert track["versions"]["live"]["n"] == 1
    assert track["versions"]["remaster"]["n"] == 0
    assert sum(r["n"] for r in track["period_genre_popularity"]) == track["n"]
    assert sum(r["n"] for r in track["popularity_bands"]) == track["n"]
    for cells in summary["sampling"].values():
        assert cells["population"] == 10
        assert cells["observed_cells"] + cells["empty_cartesian_cells"] == cells["cartesian_cells"]


def test_aggregate_outputs_privacy_and_no_overwrite(audited):
    output, summary = audited
    assert len(list(output.glob("*.png"))) == 6
    assert not list(output.glob(".catalog_audit_*"))
    for filename in (
        "resumo_catalogo_spotify.json",
        "distribuicoes_catalogo_spotify.csv",
        "auditoria_catalogo_spotify.md",
    ):
        text = (output / filename).read_text(encoding="utf-8-sig")
        assert "Canção Live" not in text
        assert "Artista Sintético A" not in text
        assert "id_a" not in text
    with (output / "distribuicoes_catalogo_spotify.csv").open(
        encoding="utf-8-sig", newline=""
    ) as stream:
        rows = list(csv.DictReader(stream))
    assert {r["scope"] for r in rows} == {"linha", "track_id", "track_id_sem_conflito"}
    assert "period_genre_popularity" in {r["section"] for r in rows}
    before = (output / "resumo_catalogo_spotify.json").read_bytes()
    with pytest.raises(ValueError, match="já existe"):
        run(FIXTURE, output)
    assert (output / "resumo_catalogo_spotify.json").read_bytes() == before
    assert summary["command_argv"][0] == sys.executable


def test_incompatible_schema_records_incomplete(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("track_id,popularity\na,2\n", encoding="utf-8")
    output = tmp_path / "out"
    with pytest.raises(ValueError, match="Schema incompatível"):
        run(source, output)
    summary = json.loads((output / "resumo_catalogo_spotify.json").read_text(encoding="utf-8"))
    assert summary["completed"] is False
    assert summary["status"] == "incomplete"
    assert summary["error_type"] == "ValueError"


def test_all_conflicting_ids_has_no_silent_representative(tmp_path):
    source = tmp_path / "conflict.csv"
    source.write_text(
        "track_id,artist_name,track_name,popularity,year,genre\n"
        "a,A,Song,0,,rock\na,A,Song,99,2020,pop\n",
        encoding="utf-8",
    )
    summary = run(source, tmp_path / "out")
    assert summary["scopes"]["track_id_sem_conflito"]["n"] == 0
    assert summary["sampling"]["period_genre"]["observed_cells"] == 0
    assert summary["scopes"]["track_id_sem_conflito"]["popularity"]["mean"] is None
