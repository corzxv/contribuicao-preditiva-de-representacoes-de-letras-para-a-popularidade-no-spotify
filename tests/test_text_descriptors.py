import json
import math

import polars as pl
import pytest
from test_lyrics_recovery import no_network, recovery_setup  # noqa: F401
from test_sample_lyrics import setup as baseline_setup  # noqa: F401

from tcc_music_popularity import data_readiness as readiness
from tcc_music_popularity import lyrics_recovery as v2
from tcc_music_popularity import text_descriptors as mod


def test_descriptor_definitions_and_normalized_source():
    text = "\ufeffHello HELLO!\r\n\r\nHello HELLO!  \r\nWhy?\r\n"
    f = mod.descriptors(text)
    assert set(f) == set(mod.FEATURES) and len(f) == 21
    assert f["text_nonempty_lines"] == 3 and f["text_stanzas"] == 2
    assert f["text_lexical_segments"] == 5 and f["text_unique_segments"] == 2
    assert f["text_segment_type_ratio"] == 0.4
    assert f["text_hapax_type_ratio"] == 0.5
    assert f["text_repeated_line_fraction"] == pytest.approx(1 / 3)
    assert f["text_exclamation_line_fraction"] == pytest.approx(2 / 3)
    assert f["text_question_line_fraction"] == pytest.approx(1 / 3)
    assert f["text_uppercase_letter_fraction"] == pytest.approx(13 / 23)
    assert f == mod.descriptors("Hello HELLO!\n\nHello HELLO!\nWhy?")
    assert all(math.isfinite(v) for v in f.values())
    with pytest.raises(ValueError, match="somente texto"):
        mod.descriptors({"popularity": 80})


def test_multilingual_segments_and_repetitions():
    f = mod.descriptors("Não don't re-enter 東京 １２３\n東京？")
    assert f["text_lexical_segments"] == 5
    assert f["text_digits_fraction"] > 0 and f["text_question_line_fraction"] == 0.5
    assert mod.descriptors("!!!\n$$$")["text_no_lexical_segments"] == 1
    assert mod.descriptors("")["text_nonempty_lines"] == 0
    assert mod.descriptors("Again\nAgain")["text_repeated_line_fraction"] == 0.5
    assert mod.descriptors("Again")["text_segment_entropy"] == 0


def test_components_transitive_literal_and_stable():
    f = pl.DataFrame(
        {
            "track_id": ["a", "b", "c", "d", "e", "f"],
            "artist_name": [
                "!!!",
                "!!!",
                "Artist",
                "Other feat. Artist",
                "Band & Friends",
                "Unrelated",
            ],
            "track_name": ["One", "Two", "Song", "Song (Live)", "Song", "Other"],
            "lyrics_strict_text_sha256": ["same", "x", "same", "y", "z", "q"],
        }
    )
    a, b = mod.grouping(f), mod.grouping(f.reverse())
    assert a.sort("track_id").equals(b.sort("track_id"))
    assert not a["text_group_unresolved"].any()
    assert a["text_artist_group_key"][0] == "literal:!!!"
    assert a["text_component_id"][:4].n_unique() == 1
    assert a["text_component_id"].n_unique() == 3
    assert "split" not in a.columns


def test_manual_stage_checkpoint_join_and_private_sources(request):
    cfg = request.getfixturevalue("recovery_setup")
    assert v2.execute(**cfg) == 0
    root = cfg["workspace"].parent
    old = root / "old_keys.parquet"
    pl.DataFrame(
        {"track_id": ["id00"], "composition_key": ["old artist|||song"], "split": ["holdout_test"]}
    ).write_parquet(old)
    args = dict(
        sample_dir=cfg["sample_path"].parent,
        input_path=cfg["workspace"] / "resultados_faixas_200k.parquet",
        texts=cfg["workspace"] / "letras_aceitas_200k.parquet",
        assignments_path=old,
        evaluated_path=old,
        development_path=old,
        cohort_path=old,
        workspace=root / "readiness",
        output=root / "ready_report",
        expected=11,
    )
    assert readiness.run(**args) == 0
    p = dict(
        input_path=args["workspace"] / "linhagem_aceitas.parquet",
        texts=args["texts"],
        readiness=args["output"] / "resumo_prontidao.json",
        workspace=root / "features",
        output=root / "feature_reports",
        expected=9,
    )
    original_hashes = {x: mod.base.sha256(x) for x in [p["input_path"], p["texts"]]}
    assert mod.run(**p, limit=1) == 2
    assert mod.run(**p) == 0
    final = pl.read_parquet(p["workspace"] / "coorte_descritores.parquet")
    original = pl.read_parquet(p["input_path"])
    assert final.height == final["track_id"].n_unique() == 9
    assert final.select(original.columns).sort("track_id").equals(original.sort("track_id"))
    assert all(not final[c].null_count() for c in mod.FEATURES)
    report = json.loads((p["output"] / "resumo_descritores.json").read_text(encoding="utf-8"))
    assert report["completed"] and report["reused_texts"] >= 1
    assert not any(report[k] for k in ("embeddings_generated", "splits_created", "models_trained"))
    for path, digest in original_hashes.items():
        assert mod.base.sha256(path) == digest
    for path in p["output"].iterdir():
        assert "Synthetic line" not in path.read_text(
            encoding="utf-8-sig"
        ) and "id00" not in path.read_text(encoding="utf-8-sig")
    with pytest.raises(ValueError, match="incompatível"):
        (p["output"] / "owner.json").write_text("{}", encoding="utf-8")
        mod.run(**p)
