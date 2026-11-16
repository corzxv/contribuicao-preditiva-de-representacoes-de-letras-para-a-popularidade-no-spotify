"""Confere vínculos históricos nos três gêneros identificados na etapa 52."""

import json
from collections import Counter
from contextlib import closing
from hashlib import sha256

import polars as pl

from . import linked_sample_design as sample
from . import local_lyrics as local
from .lyrics_scale_v040 import cache_is_compatible
from .manual_lyrics import (
    DEFAULT_WORKSPACE,
    atomic_frame,
    atomic_json,
    exclusive,
    fingerprint,
    query_identity,
    require,
)
from .sample_lyrics import stable_readonly

design = sample.design
artist = sample.links.limit.artist
recovery = artist.recovery
revision = artist.revision
WORKSPACE = design.ROOT / "data/derived/private_revalidacao_cache_historico_v1"
OUTPUT = design.ROOT / "reports/revalidacao_cache_historico_v1"
GENRES = ("chicago-house", "guitar", "minimal-techno")
ACCEPTED = ("accepted_exact_unique", "accepted_exact_equivalent")
VERSION = "cache-historico-revalidado-v1"


def revalidate(query, stored_query, envelope, historical, dump_sha256):
    requests = {request["endpoint"]: request for request in envelope["requests"]}
    search = requests["/api/search"]
    require(
        search["http_status"] == 200 and isinstance(search["payload"], list),
        "Busca histórica incompleta.",
    )
    candidates = list(search["payload"])
    if envelope.get("transport") == "sqlite_readonly":
        require(
            envelope["cache_version"] == "local-snapshot-v1"
            and not envelope.get("incomplete_reason")
            and historical.get("candidate_enumeration_complete") is True
            and envelope["local_query_sha256"] == fingerprint(stored_query)
            and envelope["local_source"]["dump"]["verified_sha256"] == dump_sha256,
            "Cache local incompleto ou de outra origem.",
        )
    else:
        require(
            cache_is_compatible(stored_query, envelope), "Consulta da API histórica divergente."
        )
        require(len(candidates) < 20, "Busca da API histórica no limite de resultados.")
        direct = requests["/api/get"]
        require(direct["http_status"] in (200, 404), "Resposta direta histórica incompleta.")
        if direct["http_status"] == 200:
            candidates.append(direct["payload"])

    require(
        0 < len(candidates) <= local.MAX_CANDIDATES
        and all(type(c.get("id")) is int for c in candidates),
        "Identificação ou número de candidatos divergente.",
    )
    selected = [c for c in candidates if c["id"] == historical["selected_lrclib_id"]]
    require(
        selected
        and all(
            c.get("plainLyrics")
            and recovery.strict_plain_text_metrics(c["plainLyrics"])["strict_text_sha256"]
            == historical["selected_strict_text_sha256"]
            for c in selected
        ),
        "Texto selecionado diverge do registro histórico.",
    )
    compatible = []
    for candidate in candidates:
        if revision.compatible(query, candidate):
            require(
                recovery.duration_delta(query, candidate) is not None,
                "Duração ausente em candidato compatível.",
            )
            compatible.append({"local_lyrics_id": None, **candidate})
    if not any(c["id"] == historical["selected_lrclib_id"] for c in compatible):
        return "vinculo_historico_incompativel", None
    reason, lyric = artist.review_text(query, compatible)
    if lyric is None:
        return reason, None
    if lyric["strict_text_sha256"] != historical["selected_strict_text_sha256"]:
        return "texto_revalidado_diverge_do_historico", None
    require(
        sha256(lyric["accepted_text"].encode()).hexdigest() == lyric["text_sha256"],
        "Hash textual inválido.",
    )
    lyric["rules_version"] = VERSION
    return "revalidada", lyric


def run():
    _, frame, _, origins = sample.input_frame()
    mapping = DEFAULT_WORKSPACE / "track_mapping.parquet"
    state = local.DEFAULT_LOCAL / "state.sqlite"
    rows = (
        pl.scan_parquet(mapping)
        .filter(pl.col("genre").is_in(GENRES) & pl.col("query_id").is_not_null())
        .select("track_id", "genre", "query_id", "artist_name_raw", "track_name_raw", "duration_ms")
        .collect()
        .join(frame.select("track_id"), on="track_id", how="anti")
        .sort("track_id")
    )
    require(rows.height == rows["track_id"].n_unique(), "Faixas duplicadas no mapa histórico.")
    dump_sha = design.read_json(sample.links.limit.OUTPUT / "resumo_revisao_limites.json")["seal"][
        "dump"
    ]["verified_sha256"]
    decisions, lyrics, accepted = [], [], []
    with closing(stable_readonly(state)) as db:
        for row in rows.iter_rows(named=True):
            historical = db.execute(
                "SELECT data,result,cache_path,cache_sha256 FROM queries WHERE query_id=? AND status IN (?,?)",
                (row["query_id"], *ACCEPTED),
            ).fetchone()
            if historical is None:
                continue
            stored = local.safe_query(historical["data"])
            query = recovery.recovery_query(
                {
                    "track_id": row["track_id"],
                    "artist_name": row["artist_name_raw"],
                    "track_name": row["track_name_raw"],
                    "duration_ms": row["duration_ms"],
                }
            )
            require(
                stored["representative_track_id"] == row["track_id"]
                and fingerprint(query_identity(stored)) == row["query_id"],
                "Chave ou faixa representativa divergente.",
            )
            if not query or any(
                query[k] != stored[k]
                for k in ("artist_name_query", "track_name_query", "duration_seconds")
            ):
                continue
            path = design.ROOT / historical["cache_path"]
            envelope = design.read_json(sample.links.verified(path, historical["cache_sha256"]))
            result, lyric = revalidate(
                query, stored, envelope, json.loads(historical["result"]), dump_sha
            )
            decisions.append(
                {
                    "track_id": row["track_id"],
                    "genre": row["genre"],
                    "query_id": row["query_id"],
                    "cache_path": str(path.relative_to(design.ROOT)),
                    "cache_sha256": historical["cache_sha256"],
                    "cache_version": envelope["cache_version"],
                    "outcome": result,
                }
            )
            if lyric:
                lyrics.append({"query_id": row["query_id"], **lyric})
                accepted.append(
                    {
                        "track_id": row["track_id"],
                        "genre": row["genre"],
                        "query_id": row["query_id"],
                        "text_sha256": lyric["text_sha256"],
                    }
                )
    require(
        len(decisions) == 43 and len({row["query_id"] for row in decisions}) == 43,
        "A triagem de 43 consultas divergiu.",
    )
    with exclusive(WORKSPACE):
        atomic_frame(
            WORKSPACE / "letras_revalidadas.parquet",
            pl.DataFrame(lyrics, schema=artist.synced.LYRIC_SCHEMA),
        )
        atomic_frame(
            WORKSPACE / "vinculos_revalidados.parquet",
            pl.DataFrame(
                accepted,
                schema={
                    "track_id": pl.String,
                    "genre": pl.String,
                    "query_id": pl.String,
                    "text_sha256": pl.String,
                },
            ),
        )
        atomic_json(WORKSPACE / "decisoes.json", decisions)
        old = {row["genre"]: row for row in design.read_csv(sample.OUTPUT / "cotas_genero.csv")}
        counts = Counter(row["genre"] for row in accepted)
        capacities = []
        for name, row in sorted(old.items()):
            target, before = int(row["target"]), int(row["capacity"])
            after = before + counts[name]
            capacities.append(
                {
                    "genre": name,
                    "target": target,
                    "capacity_before": before,
                    "added": counts[name],
                    "capacity_after": after,
                    "deficit_after": max(0, target - after),
                }
            )
        report = {
            "completed": True,
            "reviewed_queries": len(decisions),
            "revalidated_tracks": len(accepted),
            "by_outcome": dict(Counter(row["outcome"] for row in decisions)),
            "reviewed_by_genre": dict(Counter(row["genre"] for row in decisions)),
            "revalidated_by_genre": dict(counts),
            "capacity_after": frame.height + len(accepted),
            "remaining_genre_deficits": [r for r in capacities if r["deficit_after"] > 0],
            "source_hashes": {"mapping": design.sha256(mapping), **origins},
            "private_sha256": {
                name: design.sha256(WORKSPACE / name)
                for name in (
                    "letras_revalidadas.parquet",
                    "vinculos_revalidados.parquet",
                    "decisoes.json",
                )
            },
        }
        OUTPUT.mkdir(parents=True, exist_ok=True)
        design.write_csv(OUTPUT / "capacidade_por_genero.csv", capacities)
        atomic_json(OUTPUT / "resumo_revalidacao.json", report)
    print(
        json.dumps(
            {key: report[key] for key in ("reviewed_queries", "revalidated_tracks", "by_outcome")}
        )
    )
    return report
