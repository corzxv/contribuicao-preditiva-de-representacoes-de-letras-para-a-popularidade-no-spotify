import json
from pathlib import Path

import polars as pl
import pytest
from test_lyrics_recovery import no_network, recovery_setup  # noqa: F401
from test_sample_lyrics import setup as baseline_setup  # noqa: F401

from tcc_music_popularity import data_readiness as mod
from tcc_music_popularity.project_inventory import classification, inventory


def test_inventory_bounded_and_no_contents(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/a.py").write_text("Private data must not be copied", encoding="utf-8")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv/ignored.txt").write_text("not enumerated")
    (tmp_path / ".env").write_text("secret")
    cache = tmp_path / "data/derived/work/cache"
    cache.mkdir(parents=True)
    (cache / "individual.json").write_text("private lyric")
    result = inventory(tmp_path)
    assert [r["path"] for r in result["files"]] == ["src/a.py"]
    assert "Private data must not be copied" not in json.dumps(result)
    assert classification(Path("reports/final_holdout_metrics_v0_6.csv"))[0] == "HISTÓRICO"
    assert classification(Path("reports/avaliacao_letras_200k_v3/resumo.json"))[0] == "PENDENTE"
    assert classification(Path("scripts/17_auditar_prontidao_200k.py"))[0] == "ATIVO"


def test_lineage_flags_do_not_define_new_splits():
    accepted = pl.DataFrame(
        {
            "track_id": ["new", "old"],
            "artist_name": ["Artist", "Other"],
            "track_name": ["Song - Live", "Song"],
        }
    )
    assignments = pl.DataFrame({"track_id": ["old"], "split": ["development_train"]})
    tested = pl.DataFrame({"track_id": ["test"], "composition_key": ["artist|||song"]})
    development = pl.DataFrame({"track_id": ["old"]})
    result = mod.lineage(accepted, assignments, tested, development)
    assert result.height == 2 and "split" not in result.columns
    assert result["readiness_v06_composition_collision"].to_list() == [True, False]
    assert not result["readiness_v06_evaluated_track"].any()
    assert result["readiness_old_development_track"].to_list() == [False, True]
    with pytest.raises(ValueError, match="alvos"):
        mod.metadata_only(Path("not_opened.parquet"), ["spotify_popularity"])


def test_readiness_fixture_checkpoint_and_immutable_inputs(request):
    cfg = request.getfixturevalue("recovery_setup")
    from tcc_music_popularity.lyrics_recovery import execute

    assert execute(**cfg) == 0
    root = cfg["workspace"].parent
    assignments = root / "assignments.parquet"
    evaluated = root / "evaluated.parquet"
    development = root / "development.parquet"
    cohort = root / "cohort.parquet"
    pl.DataFrame(
        {"track_id": ["id00"], "split": ["holdout_test"], "spotify_popularity": [999]}
    ).write_parquet(assignments)
    pl.DataFrame(
        {
            "track_id": ["id00"],
            "composition_key": ["old artist|||song"],
            "spotify_popularity": [999],
        }
    ).write_parquet(evaluated)
    pl.DataFrame({"track_id": ["id01"], "spotify_popularity": [999]}).write_parquet(development)
    pl.DataFrame({"track_id": ["id02"], "spotify_popularity": [999]}).write_parquet(cohort)
    args = dict(
        sample_dir=cfg["sample_path"].parent,
        input_path=cfg["workspace"] / "resultados_faixas_200k.parquet",
        texts=cfg["workspace"] / "letras_aceitas_200k.parquet",
        assignments_path=assignments,
        evaluated_path=evaluated,
        development_path=development,
        cohort_path=cohort,
        workspace=root / "ready_private",
        output=root / "ready_public",
        expected=11,
    )
    originals = {
        p: mod.base.sha256(p)
        for p in [args["input_path"], args["texts"], assignments, evaluated, development, cohort]
    }
    assert mod.run(**args, limit=1) == 2
    assert mod.run(**args) == 0
    summary = json.loads((args["output"] / "resumo_prontidao.json").read_text(encoding="utf-8"))
    assert summary["completed"] and summary["reused_text_checks"] == 1
    assert summary["history_flags"]["readiness_v06_evaluated_track"] == 1
    assert not any(
        summary[k]
        for k in [
            "old_targets_loaded",
            "models_loaded",
            "ssd_queries",
            "training_executed",
            "cohort_frozen",
        ]
    )
    linked = pl.read_parquet(args["workspace"] / "linhagem_aceitas.parquet")
    source = pl.read_parquet(args["input_path"]).filter(pl.col("lyrics_status") == "accepted")
    assert linked.select(source.columns).equals(source)
    for path, digest in originals.items():
        assert mod.base.sha256(path) == digest
    for path in args["output"].glob("*.md"):
        assert "New synthetic text" not in path.read_text(encoding="utf-8")
    for path in args["output"].glob("*.json"):
        assert "id00" not in path.read_text(encoding="utf-8")


def test_changed_text_rejected_after_matching_seal(tmp_path):
    import sqlite3

    path = tmp_path / "texts.parquet"
    pl.DataFrame(
        {
            "query_id": ["q"],
            "accepted_text": ["tampered"],
            "text_sha256": ["expected"],
            "strict_text_sha256": ["strict"],
            "lrclib_id": [1],
            "lrclib_lyrics_id": [2],
        }
    ).write_parquet(path)
    with sqlite3.connect(":memory:") as db:
        db.execute(
            "CREATE TABLE verified(query_id TEXT PRIMARY KEY,raw_hash TEXT,strict_hash TEXT)"
        )
        with pytest.raises(ValueError, match="Conteúdo textual"):
            mod.verify_texts(db, path, {"q": ("expected", "strict", 1, 2)})
        with pytest.raises(ValueError, match="Referência/hash"):
            mod.verify_texts(db, path, {"q": ("expected", "strict", 99, 2)})
