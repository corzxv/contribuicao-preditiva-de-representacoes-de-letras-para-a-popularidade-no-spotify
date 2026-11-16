"""Conferências pequenas da descrição, sem leitura do catálogo real."""

import hashlib
import json

import numpy as np
import polars as pl
import pytest
import yaml

from tcc_music_popularity import catalog_description as mod


def fixture_frame(n=120):
    random = np.random.default_rng(20261106)
    data = {
        "_indice_fonte": [str(i) for i in range(n)],
        "artist_name": [f"Crédito sintético {i % 12}" for i in range(n)],
        "track_name": [f"Título sintético {i}" for i in range(n)],
        "track_id": [f"fixture_{i}" for i in range(n)],
        "genre": [["rock", "pop", "ambient", "jazz"][i % 4] for i in range(n)],
        "year": [str(2000 + i % 24) for i in range(n)],
        "popularity": [str(i % 101) for i in range(n)],
        "key": [str(i % 12) for i in range(n)],
        "mode": [str(i % 2) for i in range(n)],
        "time_signature": ["4"] * n,
    }
    for name in mod.ACOUSTIC:
        values = random.uniform(0.05, 0.95, n)
        if name == "tempo":
            values = values * 140 + 50
        elif name == "loudness":
            values = values * -30
        elif name == "duration_ms":
            values = values * 200000 + 100000
        data[name] = list(map(str, values))
    return pl.DataFrame(data)


def test_colunas_novas_unidades_e_denominadores():
    original = (
        fixture_frame()
        .with_row_index("i")
        .with_columns(
            pl.when(pl.col("i") == 0).then(pl.lit("0")).otherwise(pl.col("tempo")).alias("tempo"),
            pl.when(pl.col("i") == 1)
            .then(pl.lit("1.5"))
            .otherwise(pl.col("energy"))
            .alias("energy"),
        )
        .drop("i")
    )
    rules = yaml.safe_load(mod.RULES.read_text())["spotify"]
    frame, quality, dictionary = mod.prepare_frame(original, rules)
    assert frame.select(original.columns).equals(original)
    assert frame[mod.derived("duration_ms")][0] == pytest.approx(
        float(original["duration_ms"][0]) / 1000
    )
    assert frame[mod.derived("tempo")].null_count() == 1
    assert frame[mod.derived("energy")].null_count() == 1
    assert next(r for r in quality if r["variavel"] == "energy")["n_fora_regra_local"] == 1
    assert (
        next(r for r in dictionary if r["variavel_original"] == "genre")["papel_descritivo"]
        == "perfil"
    )
    rows, _ = mod.numerical_tables(frame)
    assert (
        next(r for r in rows if r["variavel"] == "energy" and r["escopo"] == "todos_finitos")["n"]
        == 120
    )
    assert (
        next(r for r in rows if r["variavel"] == "energy" and r["escopo"] == "regra_local")["n"]
        == 119
    )


def test_pca_corresponde_a_svd_e_exclui_constante():
    random = np.random.default_rng(91)
    values = random.normal(size=(90, 4))
    values[:, 1] = 0.8 * values[:, 0] + values[:, 1] * 0.2
    values[:, 3] = 2
    summary, rows, scores = mod.pca_values(values, ("a", "b", "c", "constante"))
    z = (values[:, :3] - values[:, :3].mean(axis=0)) / values[:, :3].std(axis=0, ddof=1)
    expected = np.linalg.svd(z, compute_uv=False) ** 2 / (len(z) - 1)
    assert summary["autovalores"] == pytest.approx(expected)
    assert summary["variaveis_constantes"] == ["constante"]
    assert np.cov(scores, rowvar=False) == pytest.approx(np.diag(expected), abs=1e-12)
    vectors = np.array(
        [[r["coeficiente_eixo"] for r in rows if r["variavel"] == name] for name in ("a", "b", "c")]
    )
    assert vectors.T @ vectors == pytest.approx(np.eye(3), abs=1e-12)


def test_execucao_sintetica_exporta_somente_agregados(tmp_path):
    source, output = tmp_path / "fixture.csv", tmp_path / "resultados"
    fixture_frame().write_csv(source)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    summary = mod.run(source, output)
    assert summary["concluido"] and summary["n_faixas"] == 120
    assert summary["n_generos_nao_ausentes"] == 4
    assert summary["n_campos_originais"] == 20
    assert len(list((output / "figuras").glob("*.png"))) == 13
    assert before == hashlib.sha256(source.read_bytes()).hexdigest()
    counts = pl.read_csv(output / "frequencias_categoricas.csv")
    for group in mod.CATEGORICAL:
        assert counts.filter(pl.col("variavel") == group)["n"].sum() == 120
    for file in output.glob("*.csv"):
        assert "fixture_" not in file.read_text(encoding="utf-8")
    pca = json.loads((output / "resumo_pca.json").read_text(encoding="utf-8"))
    assert pca["n_casos_completos"] == 120
    assert len(pca["variaveis"]) == 10
