"""Prepara uma amostra alternativa de 9.526 faixas com letras já vinculadas."""

from hashlib import sha256
from pathlib import Path

import numpy as np
import polars as pl

from . import lyrics_recovery_manifest as links
from .manual_lyrics import atomic_frame, atomic_json, exclusive, require

design = links.design
SIZE, SEED = 9526, 20261108
WORKSPACE = design.ROOT / "data/processed/private_amostra_com_letras_candidata_v1"
OUTPUT = design.ROOT / "reports/amostra_com_letras_candidata_v1"
HISTORICAL = design.ROOT / "data/derived/private_modeling_200k_v1/coorte_modelagem.parquet"
HISTORICAL_TEXTS = links.limit.recovery.WORKSPACE / "letras_aceitas_200k.parquet"
KEYS = ["band", "stratum_genre"]
COLUMNS = ["track_id", "genre", *links.metadata.description.NUMERIC]


def bands(frame):
    p = pl.col("popularity").cast(pl.Int16)
    return frame.with_columns(
        pl.when(p < 20)
        .then(pl.lit("00-19"))
        .when(p < 40)
        .then(pl.lit("20-39"))
        .when(p < 60)
        .then(pl.lit("40-59"))
        .when(p < 80)
        .then(pl.lit("60-79"))
        .otherwise(pl.lit("80-100"))
        .alias("band"),
        pl.when(p < 80).then(pl.col("genre")).otherwise(pl.lit("todos")).alias("stratum_genre"),
    )


def allocate(capacity, targets):
    """Ajusta cotas às capacidades com suporte para todas as células do quadro."""
    require(
        sum(capacity) >= sum(targets) >= sum(n > 0 for n in capacity),
        "Banda sem suporte para a alocação.",
    )
    allocation = [min(cap, max(1, goal)) for cap, goal in zip(capacity, targets, strict=True)]
    difference = sum(targets) - sum(allocation)
    if difference:
        room = [
            cap - n if difference > 0 else max(0, n - 1)
            for cap, n in zip(capacity, allocation, strict=True)
        ]
        available = [i for i, slots in enumerate(room) if slots > 0]
        units = design.proportional_allocation([room[i] for i in available], abs(difference))
        for i, count in zip(available, units, strict=True):
            allocation[i] += int(count) if difference > 0 else -int(count)
    require(
        sum(allocation) == sum(targets)
        and all(
            0 < n <= cap if cap else n == 0 for n, cap in zip(allocation, capacity, strict=True)
        ),
        "Alocação inválida.",
    )
    return allocation


def input_frame():
    d = design.ROOT
    reference = links.revision.OUTPUT / "resumo_revisao_matching.json"
    source = links.OUTPUT / "resumo_cobertura.json"
    readiness = d / "reports/prontidao_dados_200k_v1/resumo_prontidao.json"
    historical_summary = d / "reports/base_modelagem_200k_v1/resumo_base_modelagem.json"
    origin, new, ready, history = map(
        design.read_json, (reference, source, readiness, historical_summary)
    )
    require(all(r["completed"] for r in (origin, new, ready, history)), "Fonte incompleta.")
    source_files = {HISTORICAL_TEXTS: ready["inputs"]["inputs"][str(HISTORICAL_TEXTS)]}
    for number, module, filename, _, _ in links.OVERLAYS:
        summary = links.verified(
            module.OUTPUT / filename, new["stage_summaries_sha256"][str(number)]
        )
        source_files[module.WORKSPACE / "novas_letras_aceitas.parquet"] = design.read_json(summary)[
            "private_sha256"
        ]["novas_letras_aceitas.parquet"]
    links.verified(reference, new["stage_summaries_sha256"]["43"])
    source_files[links.revision.WORKSPACE / "letras_aceitas.parquet"] = origin["private_sha256"][
        "letras_aceitas.parquet"
    ]
    base = pl.read_parquet(
        links.verified(HISTORICAL, history["outputs_sha256"][HISTORICAL.name]),
        columns=[*COLUMNS, "lyrics_query_id", "lyrics_text_sha256", "lyrics_status"],
    )
    require(
        base.height
        == base["track_id"].n_unique()
        == ready["accepted_rows"]
        == history["cohort_rows"]
        and base["lyrics_status"].unique().to_list() == ["accepted"],
        "Quadro histórico diverge da auditoria.",
    )
    base = (
        base.rename({"lyrics_query_id": "query_id", "lyrics_text_sha256": "text_sha256"})
        .drop("lyrics_status")
        .with_columns(
            pl.lit(HISTORICAL_TEXTS.relative_to(d).as_posix()).alias("source_text_parquet"),
            pl.lit(14, dtype=pl.Int32).alias("source_stage"),
        )
    )
    sample = pl.read_parquet(
        links.verified(design.PRIVATE / "amostra_spotify.parquet", origin["seal"]["sample_sha256"]),
        columns=COLUMNS,
    )
    manifest = pl.read_parquet(
        links.verified(
            links.WORKSPACE / "vinculos_e_status.parquet", new["private_manifest_sha256"]
        )
    )
    refs = manifest.filter(pl.col("lyrics_status") == "accepted").select(
        "track_id", "query_id", "text_sha256", "source_text_parquet", "source_stage"
    )
    extra = sample.join(refs, on="track_id", how="inner", validate="1:1")
    require(
        sample.height == SIZE and extra.height == new["counts"]["accepted"],
        "Manifesto ou sorteio original divergente.",
    )
    overlap = base.join(extra, on="track_id", suffix="_new", validate="1:1")
    require(
        overlap.select(
            pl.all_horizontal(
                [pl.col(k) == pl.col(k + "_new") for k in [*COLUMNS[1:], "text_sha256"]]
            ).all()
        ).item(),
        "Vínculos repetidos divergem. Resolver antes do sorteio.",
    )
    frame = pl.concat(
        [base, extra.join(base.select("track_id"), on="track_id", how="anti").select(base.columns)]
    )
    return (
        sample,
        frame,
        source_files,
        {
            "historical_tracks": base.height,
            "accepted_in_original_draw": extra.height,
            "overlap_same_text": overlap.height,
            "historical_metadata_sha256": history["outputs_sha256"][HISTORICAL.name],
            "original_sample_sha256": origin["seal"]["sample_sha256"],
            "original_lyrics_manifest_sha256": new["private_manifest_sha256"],
        },
    )


def draw(frame, sample):
    original = sample.group_by(KEYS).len("target")
    capacity = frame.group_by(KEYS).len("capacity")
    cells = original.join(capacity, on=KEYS, how="full", coalesce=True).fill_null(0).sort(KEYS)
    allocation, chosen = [], []
    groups = frame.sort("track_id").partition_by(KEYS, as_dict=True)
    rng = np.random.default_rng(SEED)
    for rows in cells.partition_by("band", maintain_order=True):
        counts = allocate(rows["capacity"].to_list(), rows["target"].to_list())
        for row, n in zip(rows.iter_rows(named=True), counts, strict=True):
            allocation.append({**row, "allocated": n})
            if n:
                values = groups[(row["band"], row["stratum_genre"])]
                pos = rng.choice(values.height, size=n, replace=False).tolist()
                chosen.append(
                    values[pos].with_columns(
                        pl.lit(row["capacity"]).alias("linked_N_h"),
                        pl.lit(n).alias("linked_n_h"),
                        pl.lit(n / row["capacity"]).alias("linked_pi"),
                        pl.lit(row["capacity"] / n).alias("linked_weight"),
                    )
                )
    selected = pl.concat(chosen).sort("track_id")
    require(
        selected.height == selected["track_id"].n_unique() == SIZE,
        "Tamanho ou unicidade do sorteio divergente.",
    )
    require(
        selected.group_by("band")
        .len()
        .sort("band")
        .equals(sample.group_by("band").len().sort("band")),
        "Totais de popularidade divergentes.",
    )
    return selected, allocation


def verify_texts(selected, source_files):
    seals = {}
    for (ref,), group in selected.partition_by("source_text_parquet", as_dict=True).items():
        path = design.ROOT / ref
        digest = source_files[path]
        contents = (
            pl.scan_parquet(links.verified(path, digest))
            .filter(pl.col("query_id").is_in(group["query_id"].unique().to_list()))
            .select("query_id", "text_sha256", "accepted_text")
            .collect()
        )
        require(
            contents.height == contents["query_id"].n_unique(),
            "Consultas duplicadas na fonte de letras.",
        )
        require(
            group.select("query_id", "text_sha256")
            .join(contents, on=["query_id", "text_sha256"], how="anti")
            .is_empty(),
            "Vínculo ou hash textual ausente.",
        )
        require(
            all(
                text and text.strip() and sha256(text.encode()).hexdigest() == key
                for text, key in contents.select("accepted_text", "text_sha256").iter_rows()
            ),
            "Letra vazia ou divergente do hash auditado.",
        )
        seals[ref] = digest
    return seals


def run():
    sample, frame, source_files, origins = input_frame()
    sample, frame = bands(sample), bands(frame)
    selected, allocation = draw(frame, sample)
    seals = verify_texts(selected, source_files)
    genres = (
        sample.group_by("genre")
        .len("target")
        .join(frame.group_by("genre").len("capacity"), on="genre", how="left")
        .join(selected.group_by("genre").len("selected"), on="genre", how="left")
        .fill_null(0)
        .sort("genre")
    ).with_columns(
        (pl.col("target").cast(pl.Int64) - pl.col("capacity"))
        .clip(lower_bound=0)
        .alias("capacity_deficit")
    )
    reference = design.DESCRIPTION / "resumo_numerico.csv"
    reference_seal = design.read_json(design.DESCRIPTION / "resumo_descritiva.json")["arquivos"][
        reference.name
    ]
    refs = [
        r
        for r in design.read_csv(links.verified(reference, reference_seal))
        if r["escopo"] == "todos_finitos"
    ]
    moments = []
    for row in refs:
        key = row["variavel"]
        scale = 1000 if key == "duration_ms" else 1
        mean, sd = float(row["media"]), float(row["dp_populacional"])
        original = sample[key].cast(pl.Float64).mean() / scale
        alternative = selected[key].cast(pl.Float64).mean() / scale
        moments.append(
            {
                "variavel": key,
                "media_catalogo": mean,
                "media_sorteio_original": original,
                "media_candidata": alternative,
                "desvio_candidata_em_dp_catalogo": (alternative - mean) / sd,
            }
        )
    with exclusive(WORKSPACE):
        OUTPUT.mkdir(parents=True, exist_ok=True)
        private = WORKSPACE / "amostra_candidata_9526.parquet"
        atomic_frame(private, selected)
        genres.write_csv(OUTPUT / "cotas_genero.csv")
        design.write_csv(OUTPUT / "alocacao_candidata.csv", allocation)
        design.write_csv(OUTPUT / "comparacao_metadados.csv", moments)
        report = {
            "status": "candidata_a_validacao_metodologica",
            "seed": SEED,
            "frame_tracks": frame.height,
            "sample_tracks": selected.height,
            "verified_text_links": selected.height,
            "origins": origins,
            "frame_genres": frame["genre"].n_unique(),
            "sample_genres": selected["genre"].n_unique(),
            "genres_with_capacity_deficit": genres.filter(
                pl.col("capacity_deficit") > 0
            ).to_dicts(),
            "global_popularity_bands_match_original": True,
            "original_draw_overlap": selected.join(
                sample.select("track_id"), on="track_id", how="semi"
            ).height,
            "selected_from_historical": selected.filter(pl.col("source_stage") == 14).height,
            "weights_scope": "Probabilidades condicionadas ao quadro observado de faixas com vínculos aceitos.",
            "text_source_sha256": seals,
            "private_sample_sha256": design.sha256(private),
            "code_sha256": design.sha256(Path(__file__)),
            "public_sha256": {
                name: design.sha256(OUTPUT / name)
                for name in (
                    "cotas_genero.csv",
                    "alocacao_candidata.csv",
                    "comparacao_metadados.csv",
                )
            },
        }
        atomic_json(OUTPUT / "resumo_amostra_candidata.json", report)
    print(f"Amostra candidata concluída. {selected.height} faixas com vínculo textual conferido.")
    return report
