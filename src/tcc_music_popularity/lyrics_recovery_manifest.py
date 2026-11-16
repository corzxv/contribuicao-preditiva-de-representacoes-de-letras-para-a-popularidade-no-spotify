"""Consolida os vínculos verificados da nova amostra por referência às fontes."""

from pathlib import Path

import polars as pl

from . import lyrics_limit_revision as limit
from . import observed_sample_summary as metadata
from .manual_lyrics import atomic_frame, atomic_json, exclusive, require

design, revision, artist = limit.design, limit.revision, limit.artist
synced, case = artist.synced, artist.synced.case
WORKSPACE = design.ROOT / "data/derived/private_vinculos_consolidados_nova_amostra_v1"
OUTPUT = design.ROOT / "reports/recuperacao_consolidada_nova_amostra_v1"
OVERLAYS = (
    (46, case, "resumo_revisao_caixa.json", "substantively_distinct_texts", "ambiguous"),
    (47, synced, "resumo_revisao_caixa_plain_lrc.json", "plain_synced_conflict", "ambiguous"),
    (
        48,
        artist,
        "resumo_revisao_variantes_artista.json",
        "no_candidate_controlled_keys",
        "not_found",
    ),
    (50, limit, "resumo_revisao_limites.json", "operational_limit:candidate_limit", "ambiguous"),
)


def verified(path, checksum):
    require(design.sha256(path) == checksum, f"Arquivo diverge do selo: {path.name}")
    return path


def references(links, texts_path, stage):
    hashes = pl.read_parquet(texts_path, columns=["query_id", "text_sha256"])
    require(
        hashes.height == hashes["query_id"].n_unique()
        and set(hashes["query_id"]) == set(links["query_id"])
        and hashes["text_sha256"].null_count() == 0
        and hashes["text_sha256"].str.contains(r"^[0-9a-f]{64}$").all(),
        f"Chaves ou hashes de texto divergentes na etapa {stage}.",
    )
    return links.join(hashes, on="query_id", how="inner", validate="m:1").with_columns(
        pl.lit(stage).alias("source_stage"),
        pl.lit(texts_path.relative_to(design.ROOT).as_posix()).alias("source_text_parquet"),
    )


def run():
    source = revision.OUTPUT / "resumo_revisao_matching.json"
    base = design.read_json(source)
    require(base["completed"], "Recuperação local incompleta.")
    path = verified(
        revision.WORKSPACE / "resultados_faixas.parquet",
        base["private_sha256"]["resultados_faixas.parquet"],
    )
    sample = pl.read_parquet(
        verified(design.PRIVATE / "amostra_spotify.parquet", base["seal"]["sample_sha256"])
    )
    frame = pl.read_parquet(path)
    require(
        frame.height == frame["track_id"].n_unique() == base["sample_rows"]
        and frame.select(sample.columns).sort("track_id").equals(sample.sort("track_id")),
        "Faixas, metadados ou pesos divergentes do sorteio.",
    )
    frame = frame.select(
        "track_id",
        pl.col("lyrics_query_id").alias("query_id"),
        pl.col("lyrics_status").alias("status_stage43"),
        pl.col("lyrics_reason").alias("reason_stage43"),
        "lyrics_text_sha256",
        "genre",
        "_nova_peso",
        *metadata.description.NUMERIC,
    )
    initial = frame.filter(pl.col("status_stage43") == "accepted")
    text_path = verified(
        revision.WORKSPACE / "letras_aceitas.parquet",
        base["private_sha256"]["letras_aceitas.parquet"],
    )
    all_refs = [references(initial.select("track_id", "query_id"), text_path, 43)]
    require(
        initial.sort("track_id")["lyrics_text_sha256"].to_list()
        == all_refs[0].sort("track_id")["text_sha256"].to_list()
        and initial.height == base["status_counts"]["accepted"],
        "Contagem ou hashes dos vínculos de 43 divergentes.",
    )
    stage_hashes = {"43": design.sha256(source)}
    accepted_by_stage = {"43": initial.height}
    for stage, module, name, reason, status in OVERLAYS:
        source = module.OUTPUT / name
        report = design.read_json(source)
        require(report["completed"], f"Etapa {stage} incompleta.")
        links = pl.read_parquet(
            verified(
                module.WORKSPACE / "novos_vinculos.parquet",
                report["private_sha256"]["novos_vinculos.parquet"],
            )
        )
        eligible = frame.filter(
            (pl.col("status_stage43") == status) & (pl.col("reason_stage43") == reason)
        )
        require(
            links.height == links["track_id"].n_unique() == report["new_accepted_tracks"]
            and links.join(
                eligible.select("track_id", "query_id"), on=["track_id", "query_id"], how="anti"
            ).is_empty(),
            f"Vínculo fora da seleção original da etapa {stage}.",
        )
        text_path = verified(
            module.WORKSPACE / "novas_letras_aceitas.parquet",
            report["private_sha256"]["novas_letras_aceitas.parquet"],
        )
        all_refs.append(references(links, text_path, stage))
        stage_hashes[str(stage)] = design.sha256(source)
        accepted_by_stage[str(stage)] = links.height
    accepted = pl.concat(all_refs).sort("track_id")
    require(
        accepted.height
        == accepted["track_id"].n_unique()
        == report["accepted_tracks_with_overlays"],
        "Sobreposição ou total divergente.",
    )
    domain = frame.join(
        accepted, on=["track_id", "query_id"], how="left", validate="1:1"
    ).with_columns(
        pl.when(pl.col("source_stage").is_not_null())
        .then(pl.lit("accepted"))
        .otherwise(pl.col("status_stage43"))
        .alias("lyrics_status")
    )
    with exclusive(WORKSPACE):
        return export(domain, accepted_by_stage, stage_hashes, report)


def export(domain, accepted_by_stage, stage_hashes, last_stage):
    ref_file = design.DESCRIPTION / "resumo_numerico.csv"
    ref_report = design.read_json(design.DESCRIPTION / "resumo_descritiva.json")
    verified(ref_file, ref_report["arquivos"][ref_file.name])
    refs = [r for r in design.read_csv(ref_file) if r["escopo"] == "todos_finitos"]
    comparison = metadata.summarize_metadata(domain, refs)
    accepted = pl.col("lyrics_status") == "accepted"
    counts = dict(sorted(domain.group_by("lyrics_status").len().iter_rows()))
    genres = (
        domain.group_by("genre")
        .agg(pl.len().alias("n"), accepted.sum().alias("aceitas"))
        .with_columns((100 * pl.col("aceitas") / pl.col("n")).alias("cobertura_percentual"))
        .sort("genre")
    )
    by_pop = []
    for low, high in [(0, 19), (20, 39), (40, 59), (60, 79), (80, 100)]:
        group = domain.filter(pl.col("popularity").cast(pl.Int32).is_between(low, high))
        n = group.height
        successes = group.filter(accepted).height
        by_pop.append(
            {
                "limites": [low, high],
                "n": n,
                "aceitas": successes,
                "cobertura_percentual": 100 * successes / n if n else None,
            }
        )
    report = {
        "completed": True,
        "sample_rows": domain.height,
        "counts": counts,
        "coverage_pct": 100 * counts["accepted"] / domain.height,
        "weighted_coverage_pct": 100
        * domain.filter(accepted)["_nova_peso"].sum()
        / domain["_nova_peso"].sum(),
        "genres_without_accepted": genres.filter(pl.col("aceitas") == 0).height,
        "popularity_coverage": by_pop,
        "accepted_by_source_stage": accepted_by_stage,
        "stage50_outcomes": last_stage["outcomes_by_track"],
        "stage_summaries_sha256": stage_hashes,
        "code_sha256": design.sha256(Path(__file__)),
        "weighted_coverage_interpretation": "Peso do sorteio; não ajusta a seleção de letras.",
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    link = WORKSPACE / "vinculos_e_status.parquet"
    atomic_frame(
        link,
        domain.select(
            "track_id",
            "query_id",
            "status_stage43",
            "reason_stage43",
            "lyrics_status",
            "source_stage",
            "source_text_parquet",
            "text_sha256",
        ).sort("track_id"),
    )
    design.write_csv(OUTPUT / "comparacao_metadados.csv", comparison)
    genres.write_csv(OUTPUT / "cobertura_generos.csv")
    report["private_manifest_sha256"] = design.sha256(link)
    report["public_sha256"] = {
        name: design.sha256(OUTPUT / name)
        for name in ("comparacao_metadados.csv", "cobertura_generos.csv")
    }
    atomic_json(OUTPUT / "resumo_cobertura.json", report)
    print(f"Consolidação concluída. {counts['accepted']} faixas aceitas em {domain.height}.")
    return report
