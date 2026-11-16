import json
import sqlite3

import polars as pl
import pytest

from tcc_music_popularity import linkage_review_plan as mod


def fixture_frame():
    return pl.DataFrame(
        {
            "track_id": [f"faixa{i:03d}" for i in range(32)],
            "lyrics_query_id": [f"consulta{i // 2:03d}" for i in range(32)],
            "popularity": [10, 80, 10, 20] * 8,
            "lyrics_status": ["accepted"] * 16 + ["ambiguous"] * 16,
            "artist_name": ["Artista"] * 32,
            "track_name": ["Título"] * 32,
            "duration_ms": [180000] * 32,
            "lyrics_reason": ["regra"] * 32,
            "v1_lyrics_query_id": [f"anterior{i // 2:03d}" for i in range(32)],
            "lyrics_selected_lrclib_id": [1] * 32,
        }
    )


def test_plano_reproduzivel_sem_duplicar_consulta():
    frame = fixture_frame()
    first, allocation, missing, queries = mod.select_queries(frame, per_cell=2)
    second, _, _, _ = mod.select_queries(frame.reverse(), per_cell=2)
    assert first == second
    assert missing == 0 and queries == 16
    assert len({r["lyrics_query_id"] for r in first}) == len(first)
    assert all(r["review_inclusion_probability"] == 0.5 for r in first)
    assert all(r["selected_queries"] == 2 for r in allocation)
    assert any(r["extreme_tail"] for r in first)
    with pytest.raises(ValueError, match="vinte"):
        mod.select_queries(frame, per_cell=21)


def test_status_inconsistente_bloqueia_plano():
    frame = (
        fixture_frame()
        .with_row_index()
        .with_columns(
            pl.when(pl.col("index") == 0)
            .then(pl.lit("not_found"))
            .otherwise(pl.col("lyrics_status"))
            .alias("lyrics_status")
        )
        .drop("index")
    )
    with pytest.raises(ValueError, match="conflitantes"):
        mod.select_queries(frame)


def test_popularidade_textual_ordena_numericamente_e_preserva_original():
    frame = fixture_frame().with_columns(pl.col("popularity").cast(pl.String))
    frame = (
        frame.with_row_index()
        .with_columns(
            pl.when(pl.col("index") == 0)
            .then(pl.lit("9"))
            .when(pl.col("index") == 1)
            .then(pl.lit("100"))
            .otherwise(pl.col("popularity"))
            .alias("popularity")
        )
        .drop("index")
    )
    original = frame.clone()
    selected, _, _, _ = mod.select_queries(frame)
    row = next(r for r in selected if r["lyrics_query_id"] == "consulta000")
    assert row["track_id"] == "faixa001"
    assert row["popularity"] == "100"
    assert row["review_popularity_numeric"] == 100.0
    assert row["extreme_tail"] is True
    assert frame.equals(original)
    assert "review_popularity_numeric" not in frame.columns


@pytest.mark.parametrize("value", ["abc", "NaN", "inf", "-1", "101", "80.5", None])
def test_popularidade_textual_invalida_nao_e_excluida_silenciosamente(value):
    frame = fixture_frame().with_columns(pl.col("popularity").cast(pl.String))
    frame = (
        frame.with_row_index()
        .with_columns(
            pl.when(pl.col("index") == 0)
            .then(pl.lit(value, dtype=pl.String))
            .otherwise(pl.col("popularity"))
            .alias("popularity")
        )
        .drop("index")
    )
    original = frame.clone()
    with pytest.raises(ValueError):
        mod.select_queries(frame)
    assert frame.equals(original)


def test_cache_so_por_chave_sem_exportar_letra(tmp_path):
    path = tmp_path / "cache.sqlite"
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE evidence(query_id TEXT PRIMARY KEY, payload TEXT)")
    value = {
        "candidates": [
            {
                "id": 7,
                "artistName": "Artista",
                "plainLyrics": "Texto privado que não pode sair na ficha",
            }
        ]
        * 51
    }
    db.execute("INSERT INTO evidence VALUES (?,?)", ("anterior", json.dumps(value)))
    db.commit()
    db.close()
    before = path.read_bytes()
    db = mod.readonly_cache(path)
    try:
        row = mod.cached_metadata(
            [db], {"lyrics_query_id": "novo", "v1_lyrics_query_id": "anterior"}
        )
        assert row["candidate_count"] == 51
        assert row["candidate_list_truncated"]
        assert len(row["candidates"]) == 50
        assert "Texto privado" not in json.dumps(row)
        assert row["candidates"][0]["plain_text_present"]
        with pytest.raises(sqlite3.OperationalError):
            db.execute("DELETE FROM evidence")
    finally:
        db.close()
    assert before == path.read_bytes()
    db = mod.readonly_cache(path)
    try:
        row = mod.cached_metadata([db], {"lyrics_query_id": "ausente"})
        assert row["cache_status"] == "evidence_not_cached"
        assert row["candidate_count"] is None
    finally:
        db.close()


def test_cache_sem_indice_ou_com_wal_nao_e_varrido(tmp_path):
    path = tmp_path / "cache.sqlite"
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE evidence(query_id TEXT, payload TEXT)")
    db.close()
    with pytest.raises(ValueError, match="sem índice"):
        mod.readonly_cache(path)
    (tmp_path / "cache.sqlite-wal").write_bytes(b"escrita ativa")
    with pytest.raises(ValueError, match="WAL"):
        mod.readonly_cache(path)


def test_piloto_sintetico_completo_preserva_anotacoes_e_fontes(tmp_path):
    # Mesmo tipo bruto do Parquet real, incluindo a duração usada na exportação.
    frame = fixture_frame().with_columns(
        pl.col("popularity").cast(pl.String), pl.col("duration_ms").cast(pl.String)
    )
    source = tmp_path / "fonte.parquet"
    frame.write_parquet(source)
    caches = []
    for index in range(2):
        path = tmp_path / f"cache{index}.sqlite"
        db = sqlite3.connect(path)
        db.execute("CREATE TABLE evidence(query_id TEXT PRIMARY KEY, payload TEXT)")
        for i in range(16):
            payload = {
                "candidates": [
                    {
                        "id": i,
                        "artistName": "Artista",
                        "trackName": "Título",
                        "plainLyrics": "Não exportar esta letra",
                    }
                ]
            }
            db.execute(
                "INSERT INTO evidence VALUES (?,?)", (f"consulta{i:03d}", json.dumps(payload))
            )
        db.commit()
        db.close()
        caches.append(path)
    before = {p: mod.levels.digest(p) for p in (source, *caches)}
    work, output = tmp_path / "privado", tmp_path / "publico"
    result = mod.run(source=source, caches=caches, workspace=work, output=output, expected=32)
    assert result["completed"]
    assert result["selected_queries"] == 16
    assert result["human_review_completed"] is False
    manifest = (work / "manifesto_privado.json").read_text(encoding="utf-8")
    assert "Não exportar esta letra" not in manifest
    review_path = work / "casos_revisao.csv"
    headers = review_path.read_text(encoding="utf-8").splitlines()[0]
    assert "popularity" not in headers and "lyrics_status" not in headers
    review_path.write_text("Anotação humana a preservar", encoding="utf-8")
    mod.run(source=source, caches=caches, workspace=work, output=output, expected=32)
    assert review_path.read_text(encoding="utf-8") == "Anotação humana a preservar"
    assert before == {p: mod.levels.digest(p) for p in before}
