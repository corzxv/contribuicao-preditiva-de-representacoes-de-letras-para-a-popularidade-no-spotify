"""Verificações do desenho com populações pequenas, sem tocar o catálogo real."""

import itertools

import numpy as np
import polars as pl
import pytest

from tcc_music_popularity import sample_redesign as mod


def test_maiores_restos_deterministico_e_sem_substituicao():
    counts = np.array([100, 100, 50])
    assert mod.proportional_allocation(counts, 9).tolist() == [4, 3, 2]
    for size in range(1, 251):
        allocation = mod.proportional_allocation(counts, size)
        assert allocation.sum() == size
        assert np.all(allocation <= counts)
        assert np.all(np.abs(allocation - size * counts / counts.sum()) < 1)


def test_variancia_exata_por_enumeracao_do_desenho():
    strata = [np.array([1.0, 2.0, 4.0, 8.0]), np.array([10.0, 20.0, 30.0])]
    counts = np.array([4, 3])
    allocation = np.array([2, 2])
    variances = np.array([[x.var(ddof=1) for x in strata]])
    population_sd = np.array([np.concatenate(strata).std(ddof=1)])
    result = mod.precision(counts, allocation, variances, population_sd)
    estimates = [
        sum(counts[h] / counts.sum() * np.mean(sample[h]) for h in range(2))
        for sample in itertools.product(*(list(itertools.combinations(x, 2)) for x in strata))
    ]
    assert result["mean_variances"][0] == pytest.approx(np.var(estimates), rel=1e-12)
    assert np.mean(estimates) == pytest.approx(np.concatenate(strata).mean())


def test_bpm_zero_reintroduzido_sem_excluir_do_universo():
    values = np.array([0.0, 0.0, 100.0, 120.0])
    valid = values[values > 0]
    restored = mod.restored_variance(4, 2, valid.mean(), valid.std(), "tempo")
    assert restored == pytest.approx(values.var(ddof=1))
    with pytest.raises(ValueError, match="Perdas"):
        mod.restored_variance(4, 2, valid.mean(), valid.std(), "energy")


def synthetic_description(tmp_path):
    description = tmp_path / "description"
    description.mkdir()
    rng = np.random.default_rng(12)
    n = 200
    data = {
        "": [str(i) for i in range(n)],
        "track_id": [f"sintetico_{i}" for i in range(n)],
        "genre": ["a"] * 100 + ["b"] * 100,
        "key": [str(i % 12) for i in range(n)],
        "mode": [str(i % 2) for i in range(n)],
        "time_signature": ["4"] * n,
    }
    variables = [
        "popularity",
        "year",
        "danceability",
        "energy",
        "loudness",
        "speechiness",
        "acousticness",
        "instrumentalness",
        "liveness",
        "valence",
        "tempo",
        "duration_ms",
    ]
    for variable in variables:
        if variable == "year":
            values = 2000 + np.arange(n) % 24
        elif variable == "popularity":
            values = np.arange(n) % 101
        else:
            values = rng.uniform(0.1, 0.9, n)
            if variable == "loudness":
                values = -30 * values
            if variable == "tempo":
                values = 80 + 100 * values
                values[[0, 100]] = 0
            if variable == "duration_ms":
                values *= 300_000
        data[variable] = list(map(str, values))
    frame = pl.DataFrame(data)
    source = tmp_path / "source.csv"
    frame.write_csv(source)
    numeric, profiles = [], []
    for variable in variables:
        values = np.array(data[variable], dtype=float)
        if variable == "duration_ms":
            values /= 1000
        record = {
            "variavel": variable,
            "escopo": "todos_finitos",
            "n": n,
            "media": values.mean(),
            "dp_populacional": values.std(),
            "variancia_divisor_n_menos_1": values.var(ddof=1),
            "unidade": "sintética",
        }
        for label, fraction in [
            ("p05", 0.05),
            ("p25", 0.25),
            ("mediana", 0.5),
            ("p75", 0.75),
            ("p95", 0.95),
        ]:
            record[label] = np.quantile(values, fraction)
        numeric.append(record)
        for genre, indexes in [("a", slice(0, 100)), ("b", slice(100, 200))]:
            subset = values[indexes]
            if variable == "tempo":
                subset = subset[subset > 0]
            profiles.append(
                {
                    "agrupamento": "genre",
                    "categoria": genre,
                    "variavel": variable,
                    "n_grupo": 100,
                    "n_validos": len(subset),
                    "media": subset.mean(),
                    "dp_populacional": subset.std(),
                }
            )
    categories = []
    for variable in ["genre", "year", "key", "mode", "time_signature", "periodo"]:
        values = (
            np.array(data[variable])
            if variable != "periodo"
            else np.where(
                np.array(data["year"], dtype=int) <= 2009,
                "2000–2009",
                np.where(np.array(data["year"], dtype=int) <= 2019, "2010–2019", "2020–2023"),
            )
        )
        for value in sorted(set(values)):
            count = int((values == value).sum())
            categories.append(
                {"variavel": variable, "categoria": value, "n": count, "fracao": count / n}
            )
    mod.write_csv(description / "resumo_numerico.csv", numeric)
    mod.write_csv(description / "perfis_grupos.csv", profiles)
    mod.write_csv(description / "frequencias_categoricas.csv", categories)
    mod.write_json(
        description / "resumo_descritiva.json",
        {
            "concluido": True,
            "n_faixas": n,
            "source_bytes": source.stat().st_size,
            "fontes": {"csv_sha256": mod.sha256(source)},
            "arquivos": {p.name: mod.sha256(p) for p in description.glob("*.csv")},
        },
    )
    return description, source, frame


def test_fluxo_sintetico_integral_preserva_campos_pesos_e_reutilizacao(tmp_path):
    description, source, original = synthetic_description(tmp_path)
    report, private = tmp_path / "report", tmp_path / "private"
    plan = mod.dimension(description, report)
    assert plan["n"] < len(original)
    result = mod.draw(report, description, source, private)
    sample = pl.read_parquet(private / "amostra_spotify.parquet")
    indexes = sample["_nova_linha_fonte"].to_list()
    assert sample.select(original.columns).equals(original[indexes])
    assert sample["_nova_peso"].sum() == pytest.approx(len(original))
    again = mod.select_frame(original, mod.read_csv(report / "alocacao_generos.csv"), plan["seed"])
    assert again.equals(sample)
    assert mod.draw(report, description, source, private) == result
    with pytest.raises(FileExistsError):
        mod.dimension(description, report)
    comparison = mod.read_csv(report / "comparacao_categorias.csv")
    for variable in {r["variavel"] for r in comparison}:
        assert sum(
            float(r["fracao_amostra_ponderada"]) for r in comparison if r["variavel"] == variable
        ) == pytest.approx(1)
    assert (
        max(abs(float(r["diferenca_pp"])) for r in comparison if r["variavel"] == "genre") < 1e-10
    )
