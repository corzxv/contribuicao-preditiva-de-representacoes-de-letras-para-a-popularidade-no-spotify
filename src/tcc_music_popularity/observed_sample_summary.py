"""Consolidação leve de metadados: sorteio completo, domínio aceito e pendências."""

import json
import sqlite3
import time
from pathlib import Path

import matplotlib
import numpy as np
import polars as pl

from . import catalog_description as description
from . import lyrics_matching_revision as revision
from . import native_lookup_audit as audit
from . import sample_redesign as design
from .manual_lyrics import require

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = design.ROOT
OUTPUT = ROOT / "reports/consolidacao_dados_nova_amostra_v1"
PRIVATE = ROOT / "data/derived/private_consolidacao_nova_amostra_v1"


def summarize_metadata(frame, references):
    accepted = frame["lyrics_status"].to_numpy() == "accepted"
    require(accepted.sum() > 1, "Domínio aceito insuficiente para resumos de dispersão.")
    weights = frame["_nova_peso"].to_numpy()
    require(np.isfinite(weights).all() and (weights > 0).all(), "Pesos inválidos.")
    rows = []
    for reference in references:
        variable = reference["variavel"]
        values = frame[variable].cast(pl.Float64, strict=True).to_numpy()
        if variable == "duration_ms":
            values = values / 1000
        require(np.isfinite(values).all(), "Metadado não finito; não excluir silenciosamente.")
        mean, sd = float(reference["media"]), float(reference["dp_populacional"])
        sample_mean = float(np.average(values, weights=weights))
        accepted_mean = float(values[accepted].mean())
        rows.append(
            {
                "variavel": variable,
                "unidade": reference["unidade"],
                "n_sorteadas": len(frame),
                "n_aceitas": int(accepted.sum()),
                "media_catalogo": mean,
                "dp_catalogo": sd,
                "media_sorteio_ponderada": sample_mean,
                "media_sorteio_nao_ponderada": float(values.mean()),
                "media_aceitas_nao_ponderada": accepted_mean,
                "media_aceitas_ponderada_condicional": float(
                    np.average(values[accepted], weights=weights[accepted])
                ),
                "dp_aceitas_nao_ponderado": float(values[accepted].std(ddof=1)),
                "mediana_aceitas_nao_ponderada": float(np.median(values[accepted])),
                "desvio_sorteio_em_dp_catalogo": (sample_mean - mean) / sd,
                "desvio_aceitas_em_dp_catalogo": (accepted_mean - mean) / sd,
            }
        )
    return rows


def run():
    started = time.monotonic()
    summary = design.read_json(revision.OUTPUT / "resumo_revisao_matching.json")
    diagnosis = design.read_json(audit.OUTPUT / "resumo_diagnostico_chaves.json")
    require(summary["completed"] and diagnosis["completed"], "43/44 ainda incompletos.")
    require(summary["sample_rows"] <= 20_000, "Consolidação maior exige execução manual planejada.")
    path = revision.WORKSPACE / "resultados_faixas.parquet"
    require(path.stat().st_size <= 20 * 1024**2, "Entrada acima do limite de inspeção leve.")
    require(design.sha256(path) == summary["private_sha256"][path.name], "Resultado 43 alterado.")
    numeric = list(description.NUMERIC)
    columns = ["track_id", "genre", "_nova_peso", *numeric]
    frame = pl.read_parquet(path, columns=[*columns, "lyrics_status"])
    sample = pl.read_parquet(design.PRIVATE / "amostra_spotify.parquet", columns=columns)
    require(
        frame.height == summary["sample_rows"]
        and frame.select(columns).sort("track_id").equals(sample.sort("track_id")),
        "Metadados/sorteio diferem do cadastro original.",
    )
    reference_summary = design.read_json(design.DESCRIPTION / "resumo_descritiva.json")
    require(
        design.sha256(design.DESCRIPTION / "resumo_numerico.csv")
        == reference_summary["arquivos"]["resumo_numerico.csv"],
        "Referência descritiva alterada.",
    )
    references = [
        r
        for r in design.read_csv(design.DESCRIPTION / "resumo_numerico.csv")
        if r["escopo"] == "todos_finitos"
    ]
    rows = summarize_metadata(frame, references)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    design.write_csv(OUTPUT / "comparacao_metadados.csv", rows)
    genre = (
        frame.group_by("genre")
        .agg(
            pl.len().alias("n_sorteadas"),
            (pl.col("lyrics_status") == "accepted").sum().alias("n_aceitas"),
        )
        .with_columns(
            (100 * pl.col("n_aceitas") / pl.col("n_sorteadas")).alias("taxa_aceitacao_percentual"),
            (100 * pl.col("n_sorteadas") / frame.height).alias("composicao_sorteio_percentual"),
            (100 * pl.col("n_aceitas") / summary["status_counts"]["accepted"]).alias(
                "composicao_aceitas_percentual"
            ),
        )
        .sort("genre")
    )
    genre.write_csv(OUTPUT / "cobertura_generos.csv")
    cov = (
        frame.group_by("lyrics_status")
        .agg(pl.len().alias("n"), pl.col("_nova_peso").sum().alias("soma_pesos"))
        .sort("lyrics_status")
    )
    cov.write_csv(OUTPUT / "cobertura_status.csv")

    # As treze fichas são metadados privados para revisão, não novas aceitações.
    PRIVATE.mkdir(parents=True, exist_ok=True)
    dbpath = audit.WORKSPACE / "state.sqlite"
    before = revision.local.cache.stamp(dbpath)
    with sqlite3.connect(dbpath.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as db:
        db.row_factory = sqlite3.Row
        deadline = time.monotonic() + 10
        db.set_progress_handler(lambda: int(time.monotonic() > deadline), 10000)
        pairs = []
        query_ids = set()
        for stored in db.execute(
            "SELECT query_id,data,result FROM diagnostics WHERE json_extract(result,'$.diagnostic_label')='artist_key_variant' ORDER BY query_id"
        ):
            query, result = json.loads(stored["data"]), json.loads(stored["result"])
            query_ids.add(stored["query_id"])
            for candidate in result["candidates"]:
                if not candidate["artist_key_variant"]:
                    continue
                pairs.append(
                    {
                        "query_id": stored["query_id"],
                        "artista_spotify": query["artist_name_query"],
                        "titulo_spotify": query["track_name_query"],
                        "duracao_spotify_s": query["duration_seconds"],
                        "lrclib_id": candidate["id"],
                        "artista_lrclib": candidate["artist_name"],
                        "titulo_lrclib": candidate["name"],
                        "duracao_lrclib_s": candidate["duration"],
                        "delta_duracao_s": abs(query["duration_seconds"] - candidate["duration"]),
                        "possui_referencia_lyrics": candidate["last_lyrics_id"] is not None,
                        "revisao": "pendente_de_validacao_do_vinculo",
                        "aceitacao_automatica": False,
                    }
                )
    require(revision.local.cache.stamp(dbpath) == before, "Diagnóstico 44 mudou.")
    if pairs:
        design.write_csv(PRIVATE / "fichas_variantes_artista.csv", pairs)

    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(11.5, 6.8), constrained_layout=True)
    ax.barh(
        y - 0.18,
        [r["desvio_sorteio_em_dp_catalogo"] for r in rows],
        0.36,
        label="Sorteio completo — média ponderada",
        color="#7896a6",
    )
    ax.barh(
        y + 0.18,
        [r["desvio_aceitas_em_dp_catalogo"] for r in rows],
        0.36,
        label="Domínio com letras — média não ponderada",
        color="#9f6236",
    )
    ax.set(
        yticks=y,
        yticklabels=[description.LABELS[r["variavel"]] for r in rows],
        xlabel="(Média do grupo − média do catálogo) / DP do catálogo",
        title="Amostra sorteada e domínio observado de faixas com letras",
    )
    ax.invert_yaxis()
    ax.axvline(0, color="#555555", linewidth=0.8)
    ax.grid(axis="x", alpha=0.15)
    ax.spines[["right", "top"]].set_visible(False)
    ax.legend(loc="lower right", fontsize=9, frameon=False)
    for extension in ["png", "svg"]:
        fig.savefig(OUTPUT / f"selecao_metadados.{extension}", dpi=220)
    plt.close(fig)
    maximum = max(rows, key=lambda r: abs(r["desvio_aceitas_em_dp_catalogo"]))
    result = {
        "completed": True,
        "sample_rows": frame.height,
        "accepted_rows": summary["status_counts"]["accepted"],
        "numeric_variables": len(rows),
        "genres": genre.height,
        "largest_mean_shift": {
            k: maximum[k] for k in ["variavel", "desvio_aceitas_em_dp_catalogo"]
        },
        "artist_variant_queries_for_review": len(query_ids),
        "artist_variant_candidate_pairs": len(pairs),
        "new_accepted": 0,
        "source_statuses_changed": False,
        "lyrics_read": False,
        "source_metadata_bytes": path.stat().st_size,
        "individual_metadata_rows_read": frame.height,
        "catalogue_rows_reprocessed": 0,
        "dump_accessed": False,
        "models_trained": False,
        "source43_summary_sha256": design.sha256(revision.OUTPUT / "resumo_revisao_matching.json"),
        "source44_summary_sha256": design.sha256(audit.OUTPUT / "resumo_diagnostico_chaves.json"),
        "source_metadata_sha256": summary["private_sha256"][path.name],
        "code_sha256": design.sha256(Path(__file__)),
        "private_pairs_sha256": design.sha256(PRIVATE / "fichas_variantes_artista.csv")
        if pairs
        else None,
        "public_sha256": {
            name: design.sha256(OUTPUT / name)
            for name in [
                "comparacao_metadados.csv",
                "cobertura_generos.csv",
                "cobertura_status.csv",
                "selecao_metadados.png",
                "selecao_metadados.svg",
            ]
        },
        "weight_interpretation": "Médias ponderadas das aceitas são condicionais ao domínio observado; não corrigem disponibilidade de letras.",
        "seconds": time.monotonic() - started,
    }
    design.write_json(OUTPUT / "resumo_consolidacao.json", result)
    print(
        f"Consolidação leve concluída: {frame.height} metadados, {result['accepted_rows']} aceitas, {len(query_ids)} fichas de consulta; sem buscas ou alteração de vínculos."
    )
    return result
