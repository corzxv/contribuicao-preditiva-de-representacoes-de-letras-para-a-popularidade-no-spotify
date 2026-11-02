"""Descritores lexicais/estruturais e grupos operacionais, sem encoder ou treino."""

import argparse
import hashlib
import json
import math
import re
import sqlite3
import time
import unicodedata
from collections import Counter
from contextlib import closing
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow.parquet as pq

from . import sample_lyrics as base
from .lyrics_embeddings_v020 import normalize_lyrics_text
from .lyrics_recovery import FEAT, write_csv
from .manual_lyrics import (
    atomic_frame,
    atomic_json,
    exclusive,
    fingerprint,
    meta_get,
    meta_put,
    require,
)
from .normalization import composition_key, conservative_normalize, normalize_spaces

VERSION = "text-descriptors-observed-v1"
ROOT = base.ROOT
INPUT = ROOT / "data/derived/private_readiness_200k_v1/linhagem_aceitas.parquet"
TEXTS = ROOT / "data/derived/private_sample_lyrics_200k_v2/letras_aceitas_200k.parquet"
WORKSPACE = ROOT / "data/derived/private_text_descriptors_200k_v1"
OUTPUT = ROOT / "reports/descritores_textuais_200k_v1"
PROTOCOL = ROOT / "docs/contrato_representacoes_200k_v1.md"
SEGMENTS = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)
FEATURES = (
    "text_characters",
    "text_nonspace_characters",
    "text_nonempty_lines",
    "text_stanzas",
    "text_lexical_segments",
    "text_unique_segments",
    "text_segment_length_mean",
    "text_segment_length_std",
    "text_segment_type_ratio",
    "text_hapax_type_ratio",
    "text_segment_entropy",
    "text_line_length_mean",
    "text_line_length_std",
    "text_repeated_line_fraction",
    "text_letters_fraction",
    "text_digits_fraction",
    "text_punctuation_fraction",
    "text_uppercase_letter_fraction",
    "text_question_line_fraction",
    "text_exclamation_line_fraction",
    "text_no_lexical_segments",
)


def descriptors(text):
    """Segmentos Unicode não são palavras linguísticas universais; preservar repetição."""
    require(isinstance(text, str), "Descritores recebem somente texto, não metadados/alvos.")
    text = normalize_lyrics_text(text)
    lines = [s for s in text.split("\n") if s.strip()]
    chars = [c for c in text if not c.isspace()]
    letters = [c for c in chars if unicodedata.category(c).startswith("L")]
    tokens = SEGMENTS.findall(text.casefold())
    counts = Counter(tokens)
    lengths = [len(s) for s in tokens]
    line_lengths = [sum(not c.isspace() for c in line) for line in lines]
    line_keys = [re.sub(r"\s+", " ", line.casefold()).strip() for line in lines]

    def fraction(n, d):
        return n / d if d else 0.0

    def moments(values):
        return (float(np.mean(values)), float(np.std(values))) if values else (0.0, 0.0)

    segment_mean, segment_std = moments(lengths)
    line_mean, line_std = moments(line_lengths)
    result = dict(
        zip(
            FEATURES,
            (
                len(text),
                len(chars),
                len(lines),
                len(re.findall(r"(?:^|\n\s*\n)\s*\S", text)),
                len(tokens),
                len(counts),
                segment_mean,
                segment_std,
                fraction(len(counts), len(tokens)),
                fraction(sum(n == 1 for n in counts.values()), len(counts)),
                -sum((n / len(tokens)) * math.log2(n / len(tokens)) for n in counts.values()),
                line_mean,
                line_std,
                fraction(len(line_keys) - len(set(line_keys)), len(line_keys)),
                fraction(len(letters), len(chars)),
                fraction(sum(c.isdecimal() for c in chars), len(chars)),
                fraction(sum(unicodedata.category(c).startswith("P") for c in chars), len(chars)),
                fraction(sum(c.isupper() for c in letters), len(letters)),
                fraction(sum(any(c in line for c in "?？") for line in lines), len(lines)),
                fraction(sum(any(c in line for c in "!！") for line in lines), len(lines)),
                int(not tokens),
            ),
            strict=True,
        )
    )
    require(all(math.isfinite(v) for v in result.values()), "Descritor não finito.")
    return result


def literal_key(value):
    text = normalize_spaces(value)
    if not text or text in {"NA", "N/A", "null", "None"}:
        return None
    return conservative_normalize(text) or "literal:" + text.casefold()


def grouping(frame):
    """Componentes por artista, composição e texto; apenas agrupamento, sem folds."""
    require(frame["track_id"].n_unique() == frame.height, "IDs repetidos na coorte.")
    identifiers = frame["track_id"].to_list()
    parent = list(range(len(identifiers)))
    sizes = [1] * len(identifiers)

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        a, b = root(i), root(j)
        if a == b:
            return
        if sizes[a] < sizes[b]:
            a, b = b, a
        parent[b] = a
        sizes[a] += sizes[b]

    first, metadata = {}, []
    for i, row in enumerate(
        frame.select("artist_name", "track_name", "lyrics_strict_text_sha256").iter_rows(named=True)
    ):
        # Feat. explícito somente: não dividir nomes de banda por &, and, vírgula etc.
        parts = FEAT.split(normalize_spaces(row["artist_name"]) or "", maxsplit=1)
        artists = [literal_key(part) for part in parts]
        composition = composition_key(row["artist_name"], row["track_name"])
        if not composition and artists[0] and literal_key(row["track_name"]):
            composition = artists[0] + "|||" + literal_key(row["track_name"])
        keys = [("artist", k) for k in artists if k] + [
            ("composition", composition),
            ("strict_text", row["lyrics_strict_text_sha256"]),
        ]
        for kind, key in keys:
            if key:
                if (kind, key) in first:
                    union(i, first[kind, key])
                else:
                    first[kind, key] = i
        metadata.append((artists[0], composition, not artists[0] or not composition))
    members = {}
    for i, tid in enumerate(identifiers):
        members.setdefault(root(i), []).append(tid)
    labels = {r: "component_" + fingerprint(sorted(ids))[:24] for r, ids in members.items()}
    return pl.DataFrame(
        {
            "track_id": identifiers,
            "text_artist_group_key": [m[0] for m in metadata],
            "text_composition_group_key": [m[1] for m in metadata],
            "text_group_unresolved": [m[2] for m in metadata],
            "text_component_id": [labels[root(i)] for i in range(len(identifiers))],
        }
    )


def run(
    *,
    input_path=INPUT,
    texts=TEXTS,
    readiness=ROOT / "reports/prontidao_dados_200k_v1/resumo_prontidao.json",
    workspace=WORKSPACE,
    output=OUTPUT,
    expected=77535,
    limit=None,
):
    started = time.monotonic()
    require(
        workspace.resolve().is_relative_to(ROOT / "data/derived") or expected != 77535,
        "Workspace privado inválido.",
    )
    require(
        all(
            not p.resolve().is_relative_to(workspace.resolve())
            and not p.resolve().is_relative_to(output.resolve())
            for p in (input_path, texts, readiness)
        ),
        "Saídas sobrepõem fontes.",
    )
    require(output.resolve() != workspace.resolve(), "Separar saídas públicas/privadas.")
    audit = json.loads(readiness.read_text(encoding="utf-8"))
    require(
        audit["completed"] and audit["accepted_rows"] == expected,
        "Auditoria de prontidão incompleta/incompatível.",
    )
    print("[1/4] Selando coorte observada e contrato textual...", flush=True)
    cohort = pl.read_parquet(input_path)
    require(
        cohort.height == cohort["track_id"].n_unique() == expected
        and (cohort["lyrics_status"] == "accepted").all(),
        "Coorte diverge do domínio aceito.",
    )
    require(not set(FEATURES) & set(cohort.columns), "Entrada já contém descritores desta etapa.")
    expected_hash = audit["inputs"]["inputs"].get(str(texts.resolve()))
    require(
        expected_hash is not None and base.sha256(texts) == expected_hash,
        "Tabela de textos mudou após auditoria.",
    )
    seal = {
        "version": VERSION,
        "input": base.sha256(input_path),
        "texts": expected_hash,
        "readiness": base.sha256(readiness),
        "code": base.sha256(Path(__file__)),
        "protocol": base.sha256(PROTOCOL),
        "normalization": base.sha256(Path(__file__).with_name("lyrics_embeddings_v020.py")),
        "metadata_normalization": base.sha256(Path(__file__).with_name("normalization.py")),
        "features": list(FEATURES),
    }
    owner = {"seal": fingerprint(seal)}
    if output.exists():
        require(
            (output / "owner.json").is_file()
            and json.loads((output / "owner.json").read_text()) == owner,
            "Saída incompatível; preservada.",
        )
    else:
        output.mkdir(parents=True)
        atomic_json(output / "owner.json", owner)
    expected_refs = dict(cohort.select("lyrics_text_ref", "lyrics_text_sha256").iter_rows())
    references, seen = [], set()
    with exclusive(workspace), closing(sqlite3.connect(workspace / "state.sqlite")) as db:
        db.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        db.execute(
            "CREATE TABLE IF NOT EXISTS features(text_hash TEXT PRIMARY KEY,payload TEXT NOT NULL)"
        )
        if meta_get(db, "seal") is None:
            with db:
                meta_put(db, "seal", seal)
        require(meta_get(db, "seal") == seal, "Checkpoint de outra entrada/regra.")
        new, reused, last = 0, 0, 0.0
        print(
            "[2/4] Descritores em streaming com reuso por hash do texto normalizado...", flush=True
        )
        for batch in pq.ParquetFile(texts).iter_batches(
            batch_size=256, columns=["query_id", "accepted_text", "text_sha256"]
        ):
            for row in batch.to_pylist():
                key, raw = row["query_id"], row["accepted_text"]
                require(
                    key not in seen
                    and key in expected_refs
                    and hashlib.sha256(raw.encode()).hexdigest()
                    == row["text_sha256"]
                    == expected_refs[key],
                    "Referência/texto conflitante.",
                )
                seen.add(key)
                normalized = normalize_lyrics_text(raw)
                require(
                    bool(normalized.strip()),
                    "Texto normalizado vazio; não excluir automaticamente.",
                )
                digest = hashlib.sha256(normalized.encode()).hexdigest()
                references.append({"lyrics_text_ref": key, "text_input_sha256": digest})
                stored = db.execute(
                    "SELECT 1 FROM features WHERE text_hash=?", (digest,)
                ).fetchone()
                if stored:
                    reused += 1
                    continue
                if limit is not None and new >= limit:
                    atomic_json(
                        output / "resumo_descritores.json",
                        {
                            "completed": False,
                            "new_texts": new,
                            "reused_texts": reused,
                            "cohort_rows": expected,
                            "stop_reason": "limit_resume_same_command",
                            "seal": seal,
                        },
                    )
                    return 2
                with db:
                    db.execute(
                        "INSERT INTO features VALUES (?,?)",
                        (digest, json.dumps(descriptors(normalized))),
                    )
                new += 1
                if time.monotonic() - last >= 10:
                    progress = {
                        "stage": "descriptors",
                        "new_texts": new,
                        "reused_texts": reused,
                        "seconds": time.monotonic() - started,
                    }
                    atomic_json(workspace / "progress.json", progress)
                    print(json.dumps(progress), flush=True)
                    last = time.monotonic()
        require(seen == set(expected_refs), "Referências textuais incompletas.")
        features = pl.DataFrame(
            [
                {"text_input_sha256": r[0], **json.loads(r[1])}
                for r in db.execute("SELECT text_hash,payload FROM features")
            ]
        )
        linked = cohort.join(pl.DataFrame(references), on="lyrics_text_ref", validate="m:1").join(
            features, on="text_input_sha256", validate="m:1"
        )
        print("[3/4] Construindo componentes de identidade/texto sem criar splits...", flush=True)
        linked = linked.join(grouping(linked), on="track_id", validate="1:1")
        # Textos equivalentes no input padronizado também devem permanecer juntos.
        # Esse hash é mais estrito em espaços horizontais que o fingerprint já usado.
        require(
            linked.height == expected
            and linked.select(cohort.columns).sort("track_id").equals(cohort.sort("track_id")),
            "Linhas/campos/pesos alterados.",
        )
        require(
            not linked.select(
                pl.any_horizontal(
                    [pl.col(c).is_null() | ~pl.col(c).is_finite() for c in FEATURES]
                ).any()
            ).item(),
            "Descritores inválidos.",
        )
        atomic_frame(workspace / "coorte_descritores.parquet", linked)
        atomic_frame(workspace / "indice_textos.parquet", pl.DataFrame(references))
        sizes = linked.group_by("text_component_id").len().sort("len", descending=True)
        inherited = [
            c
            for c in linked.columns
            if c.startswith("readiness_v06_") and linked[c].dtype == pl.Boolean
        ]
        components = linked.group_by("text_component_id").agg(
            *[pl.col(c).any().alias(c) for c in inherited]
        )
        histogram = sizes.group_by(pl.col("len").alias("component_size")).agg(
            pl.len().alias("components")
        )
        write_csv(output / "tamanhos_componentes.csv", histogram.sort("component_size").to_dicts())
        quality = [
            {
                "feature": c,
                "n": expected,
                "mean": float(linked[c].mean()),
                "std": float(linked[c].std(ddof=0)),
                "min": float(linked[c].min()),
                "max": float(linked[c].max()),
            }
            for c in FEATURES
        ]
        write_csv(output / "resumo_variaveis.csv", quality)
        summary = {
            "completed": True,
            "seal": seal,
            "cohort_rows": expected,
            "features": list(FEATURES),
            "new_unique_texts": new,
            "reused_texts": reused,
            "unique_input_texts": features.height,
            "components": sizes.height,
            "largest_component": int(sizes["len"].max()),
            "unresolved_group_rows": int(linked["text_group_unresolved"].sum()),
            "no_lexical_segments_rows": int(linked["text_no_lexical_segments"].sum()),
            "components_with_history": {c: int(components[c].sum()) for c in inherited},
            "seconds": time.monotonic() - started,
            "embeddings_generated": False,
            "splits_created": False,
            "models_trained": False,
            "original_fields_weights_preserved": True,
        }
        atomic_json(output / "resumo_descritores.json", summary)
        (output / "relatorio_descritores.md").write_text(
            "# Descritores do domínio observado\n\n"
            + f"{expected} faixas preservadas, {len(FEATURES)} descritores, {features.height} textos normalizados únicos; {sizes.height} componentes, maior com {summary['largest_component']} faixas.\n\n"
            + "Segmentos lexicais Unicode não são palavras universais; contagens/ratios são operacionais, sem dicionários de sentimento ou proxies de popularidade. Repetições e originais preservados. Grupos são operacionais e ainda não definem splits. Precisão do matching e adequação do encoder não são comprovadas por esta geração.\n\n"
            + base.markdown_table(quality, ["feature", "n", "mean", "std", "min", "max"]),
            encoding="utf-8",
        )
        print(f"[4/4] Concluído; agregados em {output}", flush=True)
        return 0


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit-texts", type=int)
    args = parser.parse_args()
    require(args.limit_texts is None or args.limit_texts > 0, "Limite deve ser positivo.")
    return run(limit=args.limit_texts)
