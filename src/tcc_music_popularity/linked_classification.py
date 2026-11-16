"""Compara quatro blocos de preditores nas 9.526 faixas com letras verificadas."""

import argparse
import json
import sqlite3
from contextlib import ExitStack, closing
from hashlib import sha256
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from . import linked_sample_update as sample
from . import multilingual_embeddings as embeddings
from . import observed_classification as ordinal
from .lyrics_ambiguity_v011 import strict_plain_text_metrics
from .manual_lyrics import (
    atomic_frame,
    atomic_json,
    exclusive,
    fingerprint,
    meta_get,
    meta_put,
    require,
)
from .sample_lyrics import stable_readonly

design = sample.design
regression, common = ordinal.regression, ordinal.common
data = regression.data
descriptors = data.descriptors
WORKSPACE = design.ROOT / "data/derived/private_classificacao_9526_v1"
OUTPUT = design.ROOT / "reports/classificacao_9526_v1"
PROTOCOL = design.ROOT / "docs/protocolo_classificacao_9526_v1.md"
SETTINGS = {
    "version": "classificacao-ordinal-9526-v1",
    "cutpoints": [20, 40],
    "alphas": [0.001, 0.01, 0.1, 1.0],
    "preprocessing": ["none"],
    "max_iter": 1000,
    "gradient_tolerance": 1e-6,
    "tie_tolerance": 1e-12,
    "threads": 2,
}


def load_sample():
    summary = sample.OUTPUT / "resumo_amostra_candidata.json"
    selected = sample.WORKSPACE / "amostra_candidata_9526.parquet"
    report = design.read_json(summary)
    frame = pl.read_parquet(
        sample.sample.links.verified(selected, report["private_sample_sha256"])
    ).sort("track_id")
    require(
        frame.height
        == frame["track_id"].n_unique()
        == report["verified_text_links"]
        == sample.sample.SIZE,
        "Amostra incompleta ou duplicada.",
    )
    csv = design.SOURCE
    desc = design.DESCRIPTION / "resumo_descritiva.json"
    sample.sample.links.verified(csv, design.read_json(desc)["fontes"]["csv_sha256"])
    fields = ("artist_name", "track_name", "key", "mode", "time_signature")
    metadata = (
        pl.scan_csv(csv, infer_schema=False)
        .filter(pl.col("track_id").is_in(frame["track_id"].to_list()))
        .select("track_id", *fields, "genre", "duration_ms", "popularity")
        .collect()
        .sort("track_id")
    )
    shared = ["track_id", "genre", "duration_ms", "popularity"]
    require(metadata.select(shared).equals(frame.select(shared)), "Catálogo e amostra divergentes.")
    return frame.hstack(metadata.select(fields)), report, [summary, selected, desc, csv]


def resolve_texts(frame, sources):
    rows, texts = [], {}
    for (reference,), group in frame.partition_by("source_text_parquet", as_dict=True).items():
        path = sample.sample.links.verified(design.ROOT / reference, sources[reference])
        keys = group["query_id"].unique().to_list()
        lyrics = (
            pl.scan_parquet(path)
            .filter(pl.col("query_id").is_in(keys))
            .select("query_id", "text_sha256", "accepted_text")
            .collect()
        )
        require(
            lyrics.height == len(keys) == lyrics["query_id"].n_unique(),
            "Letras ausentes ou duplicadas.",
        )
        subset = group.select("track_id", "query_id", "text_sha256").join(
            lyrics, how="left", on=["query_id", "text_sha256"], validate="m:1"
        )
        for track, _, raw_hash, raw in subset.iter_rows():
            require(
                raw and sha256(raw.encode()).hexdigest() == raw_hash,
                "Letra diverge do vínculo selado.",
            )
            normalized = embeddings.normalize_lyrics_text(raw)
            require(bool(normalized.strip()), "Letra normalizada vazia.")
            digest = sha256(normalized.encode()).hexdigest()
            texts[digest] = normalized
            rows.append(
                {
                    "track_id": track,
                    "text_input_sha256": digest,
                    "lyrics_strict_text_sha256": strict_plain_text_metrics(raw)[
                        "strict_text_sha256"
                    ],
                }
            )
    return frame.join(pl.DataFrame(rows), on="track_id", validate="1:1").sort("track_id"), texts


def partitions(frame):
    mapping = descriptors.grouping(frame)
    result = frame.join(mapping, on="track_id", validate="1:1").sort("track_id")
    data.audit_components(result)
    folds = data.make_folds(result)
    require(
        result.select("track_id", "text_component_id").equals(
            folds.select("track_id", "text_component_id")
        ),
        "Divisões desalinhadas.",
    )
    y = common.categories(result[data.TARGET], SETTINGS["cutpoints"], observed=True)
    outer_ids = folds["outer_fold"].to_numpy()
    for outer in range(5):
        outer_test = outer_ids == outer
        require(
            set(y[outer_test]) == {0, 1, 2} and set(y[~outer_test]) == {0, 1, 2},
            "Classe ausente na divisão externa.",
        )
        inner_ids = folds[f"inner_outer_{outer}"].to_numpy()
        for inner in range(3):
            require(
                set(y[inner_ids == inner]) == {0, 1, 2}
                and set(y[(~outer_test) & (inner_ids != inner)]) == {0, 1, 2},
                "Classe ausente na divisão interna.",
            )
    return result, folds, y


def cached_vectors(keys):
    path = embeddings.WORKSPACE / "state.sqlite"
    report = design.read_json(embeddings.OUTPUT / "integral/resumo_embeddings.json")
    with closing(stable_readonly(path)) as db:
        seal = meta_get(db, "seal")
        cfg = fingerprint(seal)
        require(
            report["completed"]
            and cfg == report["seal_sha256"]
            and seal["settings"] == embeddings.SETTINGS,
            "Cache de outro encoder ou configuração.",
        )
        for filename in (
            "multilingual_embeddings.py",
            "lyrics_embeddings_v020.py",
            "manual_embeddings.py",
        ):
            require(
                design.sha256(Path(embeddings.__file__).with_name(filename))
                == seal["code"][filename],
                "Código do encoder diverge do cache.",
            )
        cached = {}
        for digest in sorted(keys):
            row = db.execute("SELECT * FROM vectors WHERE lyrics_sha256=?", (digest,)).fetchone()
            if row is not None:
                cached[digest] = embeddings.read_vector(row, cfg)
    return cached, seal


def remaining_vectors(texts, vectors, source_seal, db, signature):
    pending = sorted(texts.keys() - vectors.keys())
    db.execute(
        "CREATE TABLE IF NOT EXISTS vectors(lyrics_sha256 TEXT PRIMARY KEY, config_sha256 TEXT NOT NULL, vector BLOB NOT NULL, vector_sha256 TEXT NOT NULL, metadata TEXT NOT NULL, origin TEXT NOT NULL)"
    )
    encoder = None
    new = 0
    for digest in pending:
        old = db.execute("SELECT * FROM vectors WHERE lyrics_sha256=?", (digest,)).fetchone()
        if old is not None:
            vectors[digest] = embeddings.read_vector(old, signature)
            continue
        if encoder is None:
            snapshot, manifest = embeddings.checked_snapshot(embeddings.WORKSPACE)
            require(
                manifest == source_seal["snapshot"],
                "Snapshot diverge do encoder dos vetores reaproveitados.",
            )
            encoder = embeddings.OfflineEncoder(snapshot, threads=SETTINGS["threads"])
        vector, details = embeddings.encode_text(texts[digest], encoder)
        with db:
            embeddings.save_vector(db, digest, vector, signature, details, "candidata_9526_v2")
        vectors[digest] = vector
        new += 1
        if new % 50 == 0:
            print(f"Embeddings disponíveis: {len(vectors)}/{len(texts)}.", flush=True)
    require(set(vectors) == set(texts), "Embeddings incompletos.")
    return new


def compare(frame, folds, y, db, signature):
    db.execute(
        "CREATE TABLE IF NOT EXISTS tuning(key TEXT PRIMARY KEY,payload TEXT NOT NULL,sha256 TEXT NOT NULL)"
    )
    directory = WORKSPACE / "parts"
    assignments = folds["outer_fold"].to_numpy()
    for outer in range(5):
        mask = assignments == outer
        valid, train = frame.filter(pl.Series(mask)), frame.filter(pl.Series(~mask))
        if ordinal.read_part(directory, signature, outer, ordinal.REFERENCE, valid) is None:
            prior = np.bincount(y[~mask], minlength=3) / len(train)
            ordinal.save_part(
                directory,
                signature,
                outer,
                ordinal.REFERENCE,
                prior,
                valid,
                np.tile(prior, (len(valid), 1)),
                {},
            )
        for block in ordinal.BLOCKS:
            if ordinal.read_part(directory, signature, outer, block, valid) is None:
                selected, _ = ordinal.tune(frame, folds, outer, block, db, "9526", SETTINGS)
                columns = regression.columns_for(block)
                prep = ordinal.preprocessor(block, selected["option"])
                model, details = ordinal.fit_model(
                    prep.fit_transform(train.select(columns)), y[~mask], selected["alpha"], SETTINGS
                )
                fitted = Pipeline([("prepare", prep), ("ordinal", model)])
                probabilities = fitted.predict_proba(valid.select(columns))
                ordinal.save_part(
                    directory,
                    signature,
                    outer,
                    block,
                    fitted,
                    valid,
                    probabilities,
                    {**details, "selected": selected},
                )
            print(
                f"{outer * len(ordinal.BLOCKS) + ordinal.BLOCKS.index(block) + 1}/20 partes concluídas.",
                flush=True,
            )
    return ordinal.evaluate(frame, folds, directory, signature, WORKSPACE, OUTPUT, SETTINGS)


def run(*, prepare_only=False):
    frame, sample_report, sources = load_sample()
    frame, texts = resolve_texts(frame, sample_report["text_sources_sha256"])
    frame, quality, _ = data.prepare_metadata(frame)
    # O nome usado pelo avaliador identifica o peso do desenho desta amostra.
    frame, folds, y = partitions(
        frame.with_columns(pl.col("linked_weight").alias("sampling_weight"))
    )
    vectors, source_seal = cached_vectors(texts)
    inherited = len(vectors)
    summary = {
        "sample_tracks": frame.height,
        "components": frame["text_component_id"].n_unique(),
        "class_counts": np.bincount(y, minlength=3).tolist(),
        "unique_texts": len(texts),
        "cache_vectors_available": inherited,
        "vectors_to_compute_initially": len(texts) - inherited,
        "folds": {"outer": 5, "inner": 3},
        "sample_sha256": sample_report["private_sample_sha256"],
        "known_prior_cohort_overlap": sample_report["selected_by_source_stage"].get("14", 0),
    }
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    if prepare_only:
        return summary
    code = (
        Path(__file__),
        PROTOCOL,
        Path(ordinal.__file__),
        Path(regression.__file__),
        Path(data.__file__),
        Path(descriptors.__file__),
        Path(ordinal.ordinal.__file__),
        Path(common.__file__),
    )
    seal = {
        "settings": SETTINGS,
        "summary": summary,
        "encoder": fingerprint(source_seal),
        "code": {p.name: design.sha256(p) for p in code},
        "sources": {str(p): design.sha256(p) for p in sources},
        "vectors_reused_sha256": fingerprint(
            {key: sha256(v.tobytes()).hexdigest() for key, v in vectors.items()}
        ),
        "embedding_runtime": embeddings.versions(),
    }
    signature = fingerprint(seal)
    with exclusive(WORKSPACE), threadpool_limits(limits=SETTINGS["threads"]), ExitStack() as stack:
        common.prepare_output(WORKSPACE, seal, sources)
        common.prepare_output(OUTPUT, seal, sources)
        db = stack.enter_context(closing(sqlite3.connect(WORKSPACE / "state.sqlite")))
        db.row_factory = sqlite3.Row
        db.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        if meta_get(db, "seal") is None:
            with db:
                meta_put(db, "seal", seal)
        require(meta_get(db, "seal") == seal, "Checkpoint de outra versão.")
        atomic_json(
            OUTPUT / "resumo_classificacao.json",
            {**summary, "completed": False, "signature": signature},
        )
        atomic_frame(WORKSPACE / "folds_5x3.parquet", folds)
        common.write_csv(OUTPUT / "qualidade_metadados.csv", quality)
        new = remaining_vectors(texts, vectors, source_seal, db, signature)
        keys = frame["text_input_sha256"].to_list()
        features = {key: descriptors.descriptors(value) for key, value in texts.items()}
        frame = frame.hstack(pl.DataFrame([features[key] for key in keys]))
        frame = frame.hstack(
            pl.DataFrame(
                np.stack([vectors[key] for key in keys]), schema=list(regression.E5), orient="row"
            )
        )
        results = compare(frame, folds, y, db, signature)
        metrics = {
            row["model"]: row
            for row in design.read_csv(OUTPUT / "metricas_externas.csv")
            if row["outer_fold"] == "-1" and row["weighting"] == "equal_tracks"
        }
        baseline = float(metrics["baseline"]["balanced_accuracy"])
        common.write_csv(
            OUTPUT / "ganho_vs_baseline.csv",
            [
                {
                    "model": block,
                    "balanced_accuracy_delta": float(metrics[block]["balanced_accuracy"])
                    - baseline,
                }
                for block in ordinal.BLOCKS
                if block != "baseline"
            ],
        )
        output = {
            **summary,
            **results,
            "completed": True,
            "signature": signature,
            "new_vectors_this_run": new,
            "external_parts": 20,
            "folds_sha256": design.sha256(WORKSPACE / "folds_5x3.parquet"),
        }
        atomic_json(OUTPUT / "resumo_classificacao.json", output)
    print(json.dumps(output, ensure_ascii=False), flush=True)
    return output


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--conferir",
        action="store_true",
        help="Confere a base e as divisões sem gerar vetores ou treinar.",
    )
    args = parser.parse_args(argv)
    try:
        run(prepare_only=args.conferir)
    except KeyboardInterrupt:
        print("Progresso salvo. Repita o comando para retomar.", flush=True)
        return 2
    return 0
