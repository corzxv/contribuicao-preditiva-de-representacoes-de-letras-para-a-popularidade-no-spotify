"""Atualiza a candidata de 9.526 faixas com os vínculos conferidos de 53 e 55."""

from pathlib import Path

import numpy as np
import polars as pl
from scipy.optimize import Bounds, LinearConstraint, milp

from . import linked_genre_recovery as recovery
from .manual_lyrics import atomic_frame, atomic_json, exclusive, require

triage = recovery.triage
historical, sample, design = triage.historical, triage.sample, triage.design
WORKSPACE = design.ROOT / "data/processed/private_amostra_com_letras_candidata_v2"
OUTPUT = design.ROOT / "reports/amostra_com_letras_candidata_v2"
KEYS = sample.KEYS


def extended_frame():
    original, frame, sources, origins = sample.input_frame()
    report53 = historical.OUTPUT / "resumo_revalidacao.json"
    report55 = recovery.OUTPUT / "resumo_recuperacao.json"
    a, b = map(design.read_json, (report53, report55))
    require(a["completed"] and b["completed"], "Recuperação em andamento.")
    require(
        a["source_hashes"]["original_lyrics_manifest_sha256"]
        == origins["original_lyrics_manifest_sha256"],
        "Quadro 53 divergente.",
    )
    require(
        b["seal"]["triage_sha256"] == design.sha256(triage.OUTPUT / "resumo_triagem.json"),
        "Triagem 55 divergente.",
    )
    history_links = pl.read_parquet(
        sample.links.verified(
            historical.WORKSPACE / "vinculos_revalidados.parquet",
            a["private_sha256"]["vinculos_revalidados.parquet"],
        )
    )
    genre_links = pl.read_parquet(
        sample.links.verified(
            recovery.WORKSPACE / "vinculos_aceitos.parquet",
            b["private_sha256"]["vinculos_aceitos.parquet"],
        )
    )
    catalog = design.read_json(design.DESCRIPTION / "resumo_descritiva.json")
    metadata = (
        pl.scan_csv(
            sample.links.verified(design.SOURCE, catalog["fontes"]["csv_sha256"]),
            infer_schema=False,
        )
        .filter(pl.col("track_id").is_in(history_links["track_id"].to_list()))
        .select(sample.COLUMNS)
        .collect()
    )
    joined = metadata.join(history_links, on=["track_id", "genre"], validate="1:1")
    require(
        joined.height == a["revalidated_tracks"]
        and genre_links.height == b["new_tracks_with_lyrics"],
        "Capacidade dos complementos divergente.",
    )
    frames = [frame]
    for stage, table, workspace, name, report in (
        (53, joined, historical.WORKSPACE, "letras_revalidadas.parquet", a),
        (55, genre_links, recovery.WORKSPACE, "letras_aceitas.parquet", b),
    ):
        path = workspace / name
        sources[path] = report["private_sha256"][name]
        table = table.with_columns(
            pl.lit(path.relative_to(design.ROOT).as_posix()).alias("source_text_parquet"),
            pl.lit(stage, dtype=pl.Int32).alias("source_stage"),
        ).select(frame.columns)
        sample.verify_texts(table, sources)
        frames.append(table)
    combined = pl.concat(frames)
    require(
        combined["track_id"].n_unique()
        == combined.height
        == a["capacity_after"] + b["new_tracks_with_lyrics"],
        "Sobreposição no quadro ampliado.",
    )
    return (
        original,
        combined,
        sources,
        {"53": design.sha256(report53), "55": design.sha256(report55)},
    )


def allocation(frame, original):
    targets = original.group_by(KEYS).len("target")
    cells = (
        frame.group_by(KEYS)
        .len("capacity")
        .join(targets, on=KEYS, how="full", coalesce=True)
        .fill_null(0)
        .sort(KEYS)
    )
    capacity = np.array(cells["capacity"], dtype=int)
    target = np.array(cells["target"], dtype=int)
    bands = np.array(cells["band"])
    genres = np.array(cells["stratum_genre"])
    size = cells.height
    rows, lower, upper = [], [], []

    def add(coefficients, lo, hi):
        rows.append(coefficients)
        lower.append(lo)
        upper.append(hi)

    genre_names = sorted(set(genres) - {"todos"})
    desired = [int(target[genres == g].sum()) for g in genre_names]
    minimum = [
        min(n, int(capacity[genres == g].sum())) for g, n in zip(genre_names, desired, strict=True)
    ]
    # Redistribui vagas de gêneros abaixo da cota proporcionalmente às outras cotas.
    preferred = minimum.copy()
    support = [
        i for i, (n, floor) in enumerate(zip(desired, minimum, strict=True)) if n == floor and n > 0
    ]
    deficit = sum(desired) - sum(minimum)
    if deficit:
        extra = design.proportional_allocation([desired[i] for i in support], deficit)
        for i, count in zip(support, extra, strict=True):
            preferred[i] += int(count)

    n_variables = 2 * size + len(genre_names)
    for band in sorted(set(bands)):
        coeff = np.zeros(n_variables)
        coeff[:size] = bands == band
        total = target[bands == band].sum()
        add(coeff, total, total)
    for i, genre in enumerate(genre_names):
        mask = genres == genre
        coeff = np.zeros(n_variables)
        coeff[:size] = mask
        add(coeff.copy(), minimum[i], np.inf)
        coeff[2 * size + i] = -1
        add(coeff.copy(), -np.inf, preferred[i])
        coeff[:size] *= -1
        add(coeff, -np.inf, -preferred[i])
    for i, value in enumerate(target):
        coeff = np.zeros(n_variables)
        coeff[i], coeff[size + i] = 1, -1
        add(coeff.copy(), -np.inf, value)
        coeff[i] = -1
        add(coeff, -np.inf, -value)

    # Uma unidade de desvio por gênero pesa mais do que todo o desvio possível por célula.
    costs = np.r_[
        np.arange(size) / (size * sample.SIZE * 10),
        np.ones(size),
        np.full(len(genre_names), 2 * sample.SIZE + 1),
    ]
    bounds = Bounds(
        np.r_[capacity > 0, np.zeros(n_variables - size)],
        np.r_[capacity, np.full(n_variables - size, np.inf)],
    )
    result = milp(
        costs,
        integrality=np.r_[np.ones(size), np.zeros(n_variables - size)],
        bounds=bounds,
        constraints=LinearConstraint(np.array(rows), lower, upper),
    )
    require(result.success, f"Cotas e capacidades incompatíveis: {result.message}")
    counts = np.rint(result.x[:size]).astype(int)
    require(
        (counts <= capacity).all()
        and (counts >= (capacity > 0)).all()
        and all(counts[bands == band].sum() == target[bands == band].sum() for band in set(bands))
        and all(
            counts[genres == g].sum() >= min(target[genres == g].sum(), capacity[genres == g].sum())
            for g in genre_names
        ),
        "A alocação diverge das restrições.",
    )
    return cells.with_columns(pl.Series("allocated", counts))


def run():
    original, frame, sources, seals = extended_frame()
    original, frame = sample.bands(original), sample.bands(frame)
    plan = allocation(frame, original)
    groups = frame.sort("track_id").partition_by(KEYS, as_dict=True)
    rng = np.random.default_rng(sample.SEED)
    picked = []
    for band, genre, capacity, _, count in plan.iter_rows():
        if count:
            group = groups[(band, genre)]
            positions = rng.choice(capacity, size=count, replace=False).tolist()
            picked.append(
                group[positions].with_columns(
                    pl.lit(capacity).alias("linked_N_h"),
                    pl.lit(count).alias("linked_n_h"),
                    pl.lit(count / capacity).alias("linked_pi"),
                    pl.lit(capacity / count).alias("linked_weight"),
                )
            )
    chosen = pl.concat(picked).sort("track_id")
    require(
        chosen.height == chosen["track_id"].n_unique() == sample.SIZE,
        "Amostra de tamanho divergente.",
    )
    text_sources = sample.verify_texts(chosen, sources)
    genres = (
        original.group_by("genre")
        .len("target")
        .join(frame.group_by("genre").len("capacity"), on="genre")
        .join(chosen.group_by("genre").len("selected"), on="genre")
        .sort("genre")
    )
    numeric = design.DESCRIPTION / "resumo_numerico.csv"
    stats = design.read_json(design.DESCRIPTION / "resumo_descritiva.json")
    metrics = []
    for ref in design.read_csv(sample.links.verified(numeric, stats["arquivos"][numeric.name])):
        if ref["escopo"] == "todos_finitos":
            key = ref["variavel"]
            scale = 1000 if key == "duration_ms" else 1
            catalog_mean = float(ref["media"])
            mean = chosen[key].cast(pl.Float64).mean() / scale
            metrics.append(
                {
                    "variavel": key,
                    "media_catalogo": catalog_mean,
                    "media_candidata": mean,
                    "desvio_em_dp_catalogo": (mean - catalog_mean) / float(ref["dp_populacional"]),
                }
            )
    with exclusive(WORKSPACE):
        OUTPUT.mkdir(parents=True, exist_ok=True)
        path = WORKSPACE / "amostra_candidata_9526.parquet"
        atomic_frame(path, chosen)
        plan.write_csv(OUTPUT / "alocacao_candidata.csv")
        genres.write_csv(OUTPUT / "cotas_genero.csv")
        design.write_csv(OUTPUT / "comparacao_metadados.csv", metrics)
        report = {
            "status": "candidata_a_validacao_metodologica",
            "seed": sample.SEED,
            "frame_tracks": frame.height,
            "sample_tracks": chosen.height,
            "verified_text_links": chosen.height,
            "sample_genres": chosen["genre"].n_unique(),
            "original_popularity_band_totals": True,
            "selected_by_source_stage": dict(
                sorted(chosen.group_by("source_stage").len().iter_rows())
            ),
            "genre_shortfalls": genres.filter(pl.col("selected") < pl.col("target")).to_dicts(),
            "sum_design_weights": chosen["linked_weight"].sum(),
            "private_sample_sha256": design.sha256(path),
            "source_reports_sha256": seals,
            "text_sources_sha256": text_sources,
            "code_sha256": design.sha256(Path(__file__)),
            "public_sha256": {
                name: design.sha256(OUTPUT / name)
                for name in (
                    "alocacao_candidata.csv",
                    "cotas_genero.csv",
                    "comparacao_metadados.csv",
                )
            },
        }
        atomic_json(OUTPUT / "resumo_amostra_candidata.json", report)
    print(f"{chosen.height} faixas com letra conferida em um quadro de {frame.height}.")
    return report
