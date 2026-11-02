"""Avaliação limitada e aplicação determinística v3, sem construir índices."""

import argparse
import hashlib
import json
import re
import sqlite3
import time
import unicodedata
from contextlib import ExitStack, closing
from pathlib import Path

import numpy as np
import polars as pl
from rapidfuzz.fuzz import ratio

from . import lyrics_recovery as v2
from . import sample_lyrics as v1
from .manual_lyrics import (
    atomic_frame,
    atomic_json,
    exclusive,
    fingerprint,
    meta_get,
    meta_put,
    require,
)
from .normalization import conservative_normalize

VERSION = "lyrics-diagnostic-v3"
PRIVATE = v1.ROOT / "data/derived/private_sample_lyrics_200k_v3"
PUBLIC = v1.ROOT / "reports/avaliacao_letras_200k_v3"
FULL = v1.ROOT / "reports/recuperacao_letras_200k_v3"
PROTOCOL = v1.ROOT / "docs/protocolo_avaliacao_letras_v3.md"
SEED = 20261101


def comparison_text(text):
    # Conserva pontuação/apóstrofos/hífens e todos os sistemas de escrita.
    return re.sub(
        r"\s+", " ", unicodedata.normalize("NFC", text).translate(v2.TYPOGRAPHY).casefold()
    ).strip()


def agreement(q, c):
    a = v2.profile(q["artist_name_query"], q["track_name_query"])
    b = v2.profile(c["artistName"], c["trackName"])
    delta = v2.duration_delta(q, c)
    return {
        "artist_exact": a["artist"] == b["artist"],
        "title_exact": a["title"] == b["title"],
        "artist_alternative": conservative_normalize(a["artist"])
        == conservative_normalize(b["artist"]),
        "title_score": ratio(
            conservative_normalize(a["title"]), conservative_normalize(b["title"])
        ),
        "collaboration_exact": a["guests"] == b["guests"]
        and not a["credit_conflict"]
        and not b["credit_conflict"],
        "version_compatible": a["versions"] == b["versions"],
        "version_unspecified_both": not a["versions"] and not b["versions"],
        "duration_difference": delta,
        "duration_compatible": delta is None or delta <= 10,
    }


def decide(q, candidates, incomplete=None):
    require(set(q) <= v1.MATCH_FIELDS, "Campo proibido no matching.")
    r = {
        "status": "ambiguous",
        "reason": "metadata_uncertain",
        "method": VERSION,
        "rules_version": VERSION,
        "candidate_count": len(candidates),
        "candidate_present": bool(candidates),
        "language_status": "not_evaluated",
        "text_present": any(
            v2._text_present(c.get(k)) for c in candidates for k in ("plainLyrics", "syncedLyrics")
        ),
        "warnings": [],
        "agreements": {},
        "eligible_count": 0,
        "equivalent_count": 0,
        "empty_ignored": 0,
    }
    if incomplete:
        return {
            **r,
            "reason": "operational_limit:" + incomplete,
            "enumeration_complete": False,
        }, None
    unique, eligible, proposed = {}, [], []
    for c in candidates:
        if c["id"] in unique and unique[c["id"]] != c:
            return {**r, "reason": "same_id_conflict"}, None
        unique[c["id"]] = c
    for c in unique.values():
        d = agreement(q, c)
        r["agreements"][str(c["id"])] = d
        if not (d["collaboration_exact"] and d["version_compatible"] and d["duration_compatible"]):
            continue  # exclusão individual; não veta os elegíveis
        if d["artist_exact"] and d["title_exact"]:
            eligible.append(c)
        elif d["artist_alternative"] and d["title_score"] >= 80:
            proposed.append(c["id"])
    r.update(eligible_count=len(eligible), proposed_ids=proposed)
    if not eligible:
        return {
            **r,
            "status": "ambiguous" if candidates else "not_found",
            "reason": "review_required"
            if proposed
            else "no_compatible_candidate_in_available_indexes",
        }, None
    if any(c.get("instrumental") for c in eligible):
        if all(
            c.get("instrumental")
            and not any(v2._text_present(c.get(k)) for k in ("plainLyrics", "syncedLyrics"))
            for c in eligible
        ):
            return {
                **r,
                "status": "instrumental",
                "reason": "source_instrumental",
                "selected_lrclib_id": min(c["id"] for c in eligible),
            }, None
        return {**r, "reason": "instrumental_text_conflict"}, None
    texts = []
    for c in eligible:
        plain = c.get("plainLyrics") if v2._text_present(c.get("plainLyrics")) else None
        synced, error = (
            v2.synced_text(c["syncedLyrics"])
            if v2._text_present(c.get("syncedLyrics"))
            else (None, None)
        )
        if error:
            r["warnings"].append({"id": c["id"], "synced_limitation": error})
            if not plain:
                return {**r, "reason": "synced_requires_review"}, None
        if plain and synced and comparison_text(plain) != comparison_text(synced):
            return {**r, "reason": "plain_synced_content_conflict"}, None
        text = plain or synced
        if text:
            texts.append((c, text, plain is None))
        else:
            r["empty_ignored"] += 1
    if not texts:
        return {**r, "status": "no_text", "reason": "compatible_empty"}, None
    if len({comparison_text(t) for _, t, _ in texts}) != 1:
        return {**r, "reason": "different_word_sequence_or_punctuation"}, None
    c, text, derived = min(
        texts,
        key=lambda x: (
            r["agreements"][str(x[0]["id"])]["duration_difference"]
            if r["agreements"][str(x[0]["id"])]["duration_difference"] is not None
            else float("inf"),
            x[0]["id"],
        ),
    )
    r.update(
        status="accepted",
        reason="deterministic_identity_text_sequence",
        equivalent_count=len(texts),
        selected_lrclib_id=c["id"],
        selected_lyrics_id=c.get("local_lyrics_id"),
        text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        strict_text_sha256=v2.strict_plain_text_metrics(text)["strict_text_sha256"],
    )
    lyric = {
        "plain_text_source": text,
        "source_plain_original": c.get("plainLyrics"),
        "synced_text_source": c.get("syncedLyrics"),
        "text_origin": "derived_synced" if derived else "plain_lyrics_unmodified",
        "lrclib_id": c["id"],
        "lrclib_lyrics_id": c.get("local_lyrics_id"),
        "text_sha256": r["text_sha256"],
        "strict_text_sha256": r["strict_text_sha256"],
        "comparison_sha256": hashlib.sha256(comparison_text(text).encode()).hexdigest(),
        "rules_version": VERSION,
    }
    return r, lyric


def diagnostic_plan(frame, sizes=(600, 300, 100)):
    rng, rows = np.random.default_rng(SEED), []
    for status, target in zip(("not_found", "ambiguous", "accepted"), sizes, strict=True):
        sub = frame.filter(pl.col("lyrics_status") == status).sort("track_id")
        require(sub.height >= target, "Grupo insuficiente para avaliação fixa.")
        groups = (
            sub.partition_by("lyrics_reason", maintain_order=True)
            if status == "ambiguous"
            else [sub]
        )
        # Alocação proporcional com piso por motivo e maiores restos; AAS dentro do motivo.
        allocated = np.array([min(1, g.height) for g in groups])
        require(allocated.sum() <= target, "Motivos demais para a alocação diagnóstica.")
        capacities = np.array([g.height for g in groups]) - allocated
        if target > allocated.sum():
            quotas = (target - allocated.sum()) * capacities / capacities.sum()
            extra = np.floor(quotas).astype(int)
            for j in np.argsort(-(quotas - extra), kind="stable")[
                : int(target - allocated.sum() - extra.sum())
            ]:
                extra[j] += 1
            allocated += extra
        for group, n in zip(groups, allocated, strict=True):
            for i in rng.choice(group.height, size=int(n), replace=False):
                row = group.row(int(i), named=True)
                rows.append(
                    {
                        "track_id": row["track_id"],
                        "diagnostic_group": status,
                        "diagnostic_reason": row["lyrics_reason"]
                        if status == "ambiguous"
                        else "all",
                        "diagnostic_N": group.height,
                        "diagnostic_n": int(n),
                        "diagnostic_probability": float(n / group.height),
                        "diagnostic_seed": SEED,
                    }
                )
    # Mistura grupos para não censurar controles ao alcançar o orçamento.
    return pl.DataFrame([rows[i] for i in rng.permutation(len(rows))])


def cached(old, second, key):
    for db in (second, old):
        row = db.execute("SELECT payload FROM evidence WHERE query_id=?", (key,)).fetchone()
        if row:
            value = json.loads(row[0])
            if "candidates" in value:
                return value["candidates"], value.get("incomplete_reason")
    return [], None


def retrieve(q, indexes, dump, deadline, block_limit=2000):
    """Blocos de artista com paginação; nenhum índice novo, score só propõe revisão."""
    p = v2.profile(q["artist_name_query"], q["track_name_query"])
    metadata, incomplete = {}, None
    for db, modern in indexes:
        keys = (
            {p["artist"], v2.metadata_key(q["artist_name_query"])}
            if modern
            else {
                conservative_normalize(q["artist_name_query"]),
                conservative_normalize(p["artist"]),
            }
        )
        db.set_progress_handler(lambda: int(time.monotonic() >= deadline), 500)
        try:
            for key in sorted(keys - {None, ""}):
                last, seen = 0, 0
                while True:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("budget")
                    page = db.execute(
                        "SELECT * FROM catalog WHERE artist_key=? AND id>? ORDER BY id LIMIT 200",
                        (key, last),
                    ).fetchall()
                    if not page:
                        break
                    for row in page:
                        c = {
                            "id": row["id"],
                            "artistName": row["artist_name"],
                            "trackName": row["name"],
                            "albumName": row["album_name"],
                            "duration": row["duration"],
                            "local_lyrics_id": row["last_lyrics_id"],
                        }
                        d = agreement(q, c)
                        # Metadados antes de carregar textos; manter concorrentes plausíveis.
                        if (
                            d["artist_alternative"]
                            and d["collaboration_exact"]
                            and d["version_compatible"]
                            and d["duration_compatible"]
                            and d["title_score"] >= 80
                        ):
                            metadata[c["id"]] = c
                        last = row["id"]
                    seen += len(page)
                    if seen >= block_limit:
                        incomplete = "artist_block_limit"
                        break
        finally:
            db.set_progress_handler(None, 0)
    candidates, total = [], 0
    dump.set_progress_handler(lambda: int(time.monotonic() >= deadline), 500)
    try:
        for c in sorted(metadata.values(), key=lambda c: c["id"]):
            if time.monotonic() >= deadline:
                raise TimeoutError("budget")
            if c["local_lyrics_id"] is not None:
                size = dump.execute(
                    "SELECT track_id,length(plain_lyrics),length(synced_lyrics) FROM lyrics WHERE id=?",
                    (c["local_lyrics_id"],),
                ).fetchone()
                require(size and size[0] == c["id"], "Revisão LRCLIB inconsistente.")
                chars = (size[1] or 0) + (size[2] or 0)
                total += chars
                if chars > v2.local.MAX_TEXT_CHARACTERS or total > v2.local.MAX_TOTAL_CHARACTERS:
                    incomplete = "text_budget"
                    break
                row = dump.execute(
                    "SELECT plain_lyrics,synced_lyrics,instrumental FROM lyrics WHERE id=?",
                    (c["local_lyrics_id"],),
                ).fetchone()
            else:
                row = (None, None, False)
            candidates.append(
                {**c, "plainLyrics": row[0], "syncedLyrics": row[1], "instrumental": bool(row[2])}
            )
    finally:
        dump.set_progress_handler(None, 0)
    return candidates, incomplete


def review_pairs(db, frame, workspace):
    buckets, seen = {}, set()
    old = dict(frame.select("track_id", "lyrics_status").iter_rows())
    for row in db.execute(
        "SELECT t.track_id,q.query_id,q.data,q.result FROM tracks t JOIN queries q USING(query_id) WHERE q.result IS NOT NULL ORDER BY t.track_id"
    ):
        r = json.loads(row["result"])
        method = r.get("gain_stage", "none") + ":" + r["reason"]
        bucket = buckets.setdefault(method, [])
        if len(bucket) >= 100:
            continue
        stored = db.execute(
            "SELECT payload FROM evidence WHERE query_id=?", (row["query_id"],)
        ).fetchone()
        if stored is None:
            continue
        e = json.loads(stored[0])
        wanted = set(r.get("proposed_ids", [])) | {r.get("selected_lrclib_id")}
        if wanted == {None}:
            wanted = {c["id"] for c in e["candidates"][:3]}
        for c in e["candidates"]:
            pair = (row["query_id"], c["id"])
            if c["id"] in wanted and len(bucket) < 100 and pair not in seen:
                seen.add(pair)
                bucket.append(
                    {
                        "track_id": row["track_id"],
                        "query_id": row["query_id"],
                        "method": method,
                        "previous_status": old[row["track_id"]],
                        "query": json.loads(row["data"]),
                        "candidate": c,
                        "agreement": r.get("agreements", {}).get(str(c["id"])),
                        "review_label": "",
                        "allowed_labels": ["correto", "incorreto", "inconclusivo"],
                        "review_notes": "",
                    }
                )
    selected = []
    while len(selected) < 100 and any(buckets.values()):
        for key in sorted(buckets):
            if buckets[key] and len(selected) < 100:
                selected.append(buckets[key].pop(0))
    path = workspace / "pares_revisao_privados.json"
    if path.exists():
        annotated = [
            r
            for r in json.loads(path.read_text(encoding="utf-8"))
            if r.get("review_label") or r.get("review_notes")
        ]
        seen_pairs = {(r["query_id"], r["candidate"]["id"]) for r in annotated}
        selected = (
            annotated
            + [r for r in selected if (r["query_id"], r["candidate"]["id"]) not in seen_pairs]
        )[:100]
    atomic_json(path, selected)


def export_text_sources(workspace):
    """Reusa exportação v1 e separa texto efetivo das representações originais."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    path = workspace / "letras_aceitas_200k.parquet"
    schema = pq.read_schema(path).append(pa.field("accepted_text", pa.string()))
    with pq.ParquetWriter(path.with_suffix(".sources.tmp"), schema, compression="zstd") as writer:
        for batch in pq.ParquetFile(path).iter_batches(batch_size=128):
            records = batch.to_pylist()
            for row in records:
                provenance = json.loads(row["provenance_json"])
                row["accepted_text"] = row["plain_text_source"]
                row["plain_text_source"] = provenance.pop(
                    "source_plain_original", row["plain_text_source"]
                )
                row["provenance_json"] = json.dumps(provenance, ensure_ascii=False)
            writer.write_table(pa.Table.from_pylist(records, schema=schema))
    path.with_suffix(".sources.tmp").replace(path)


def run(
    mode,
    seconds=600,
    *,
    sample_dir=v1.SAMPLE_DIR,
    baseline=v2.WORKSPACE,
    old_workspace=v1.WORKSPACE,
    index_paths=None,
    workspace=PRIVATE,
    output=None,
    sizes=(600, 300, 100),
    expected=200000,
):
    started = time.monotonic()
    deadline = started + seconds
    require(mode in {"evaluate", "apply"} and seconds > 0, "Modo/orçamento inválido.")
    output = output or (PUBLIC if mode == "evaluate" else FULL)
    index_paths = index_paths or [
        (v2.local.DEFAULT_INDEX, False),
        (v1.INDEX, False),
        (v2.INDEX, True),
    ]
    require(
        workspace.resolve() not in {baseline.resolve(), old_workspace.resolve()}
        and (workspace.resolve().is_relative_to(v1.ROOT / "data/derived") or expected != 200000),
        "Workspace privado incompatível.",
    )
    print("Validando amostra e checkpoints locais; sem indexação...", flush=True)
    sample, _ = v1.validate_sample(
        sample_dir / "amostra_spotify_200k.parquet",
        sample_dir / "resumo_amostra_200k.json",
        sample_dir / "alocacao_amostra_200k.csv",
        expected=expected,
    )
    prior = pl.read_parquet(baseline / "resultados_faixas_200k.parquet")
    require(
        prior.height == expected
        and prior.select(sample.columns).sort("track_id").equals(sample.sort("track_id")),
        "Baseline/amostra divergentes.",
    )
    queries, tracks = v2.make_queries(sample)
    paths = [
        baseline / "state.sqlite",
        old_workspace / "state.sqlite",
        *[p / "lookup.sqlite" for p, _ in index_paths],
    ]
    seal = {
        "version": VERSION,
        "sample": v1.sha256(sample_dir / "amostra_spotify_200k.parquet"),
        "baseline": v1.sha256(baseline / "resultados_faixas_200k.parquet"),
        "sources": [v2.file_stamp(p) for p in paths],
        "code": {
            p.name: v1.sha256(p)
            for p in [
                Path(__file__),
                PROTOCOL,
                Path(v2.__file__),
                Path(v1.__file__),
                v1.ROOT / "src/tcc_music_popularity/normalization.py",
            ]
        },
    }
    with exclusive(workspace), closing(v1.state_connection(workspace)) as db, ExitStack() as stack:
        v1.initialize(db, seal, queries, tracks)
        if mode == "apply":
            require(
                meta_get(db, "evaluation_completed", False),
                "Conclua primeiro a avaliação; aceite aproximado permanece desativado.",
            )
        plan_path = workspace / "plano_diagnostico.parquet"
        if not plan_path.exists():
            atomic_frame(plan_path, diagnostic_plan(prior, sizes))
        plan = pl.read_parquet(plan_path)
        order = (
            plan["track_id"].to_list()
            if mode == "evaluate"
            else sample.sort("track_id")["track_id"].to_list()
        )
        track_map = dict(tracks)
        keys = list(dict.fromkeys(track_map[t] for t in order if track_map[t] is not None))
        require(
            not output.exists()
            or (output / "owner.json").exists()
            and json.loads((output / "owner.json").read_text())
            == {"seal": fingerprint(seal), "mode": mode},
            "Saída incompatível.",
        )
        output.mkdir(parents=True, exist_ok=True)
        atomic_json(output / "owner.json", {"seal": fingerprint(seal), "mode": mode})
        old = stack.enter_context(closing(v1.stable_readonly(paths[1])))
        second = stack.enter_context(closing(v1.stable_readonly(paths[0])))
        source = meta_get(second, "seal")["source"]
        require(v2.local.checked_dump(Path(source["path"])) == source, "Snapshot mudou.")
        dump = stack.enter_context(closing(v1.stable_readonly(Path(source["path"]))))
        indexes = [
            (stack.enter_context(closing(v1.stable_readonly(p / "lookup.sqlite"))), modern)
            for p, modern in index_paths
        ]
        for index, _ in indexes:
            require(
                meta_get(index, "progress")["complete"]
                and meta_get(index, "seal")["dump"] == source,
                "Índice incompatível.",
            )
        for cache in (old, second):
            cache.set_progress_handler(lambda: int(time.monotonic() >= deadline), 500)
        new, reused, last_print = 0, 0, 0
        try:
            for key in keys:
                stored = db.execute(
                    "SELECT status FROM queries WHERE query_id=?", (key,)
                ).fetchone()
                if stored[0] not in ("pending", "technical_error"):
                    reused += 1
                    continue
                if time.monotonic() >= deadline:
                    break
                q = queries[key]
                tick = time.monotonic()
                cs, inc = cached(old, second, key)
                r, lyric = decide(q, cs, inc)
                r["gain_stage"] = "classifier"
                if r["status"] not in ("accepted", "instrumental"):
                    additional, inc = retrieve(q, indexes, dump, deadline)
                    cs = cs + additional
                    r, lyric = decide(q, cs, inc)
                    r["gain_stage"] = "expanded_search"
                r["elapsed_seconds"] = time.monotonic() - tick
                with db:
                    db.execute(
                        "UPDATE queries SET status=?,result=?,attempts=attempts+1,elapsed_seconds=? WHERE query_id=?",
                        (r["status"], json.dumps(r), r["elapsed_seconds"], key),
                    )
                    db.execute(
                        "INSERT OR REPLACE INTO evidence VALUES (?,?)",
                        (
                            key,
                            json.dumps(
                                {"candidates": cs, "incomplete_reason": inc, "source": source},
                                ensure_ascii=False,
                            ),
                        ),
                    )
                    if lyric:
                        lyric.update(query_id=key, source_dump=source)
                        db.execute(
                            "INSERT OR REPLACE INTO lyrics VALUES (?,?)",
                            (key, json.dumps(lyric, ensure_ascii=False)),
                        )
                new += 1
                if time.monotonic() - last_print >= 10:
                    value = {
                        "mode": mode,
                        "new_queries": new,
                        "reused_queries": reused,
                        "elapsed_seconds": time.monotonic() - started,
                        "budget_seconds": seconds,
                    }
                    atomic_json(workspace / "progress.json", value)
                    print(json.dumps(value), flush=True)
                    last_print = time.monotonic()
        except (TimeoutError, KeyboardInterrupt):
            pass  # consulta incompleta permanece pendente; retomada explícita
        except (sqlite3.Error, OSError, ValueError, KeyError) as exc:
            if time.monotonic() < deadline:
                with db:
                    db.execute(
                        "UPDATE queries SET status='technical_error',result=? WHERE query_id=?",
                        (
                            json.dumps({"status": "technical_error", "reason": type(exc).__name__}),
                            key,
                        ),
                    )
        records = []
        old_status = dict(prior.select("track_id", "lyrics_status").iter_rows())
        for t in order:
            key = track_map[t]
            row = (
                db.execute(
                    "SELECT status,result,elapsed_seconds FROM queries WHERE query_id=?", (key,)
                ).fetchone()
                if key
                else None
            )
            r = json.loads(row[1]) if row and row[1] else {}
            records.append(
                {
                    "track_id": t,
                    "before": old_status[t],
                    "after": row[0] if row else "insufficient_metadata",
                    "reason": r.get("reason", "pending"),
                    "gain_stage": r.get("gain_stage", "none"),
                    "proposals": len(r.get("proposed_ids", [])),
                    "seconds": row[2] if row else None,
                }
            )
        result = pl.DataFrame(records)
        complete = not result["after"].is_in(["pending", "technical_error"]).any()
        if mode == "evaluate" and complete:
            with db:
                meta_put(db, "evaluation_completed", True)
        transitions = (
            result.group_by("before", "after", "gain_stage", "reason")
            .len()
            .sort("before", "after")
            .to_dicts()
        )
        v2.write_csv(output / "transicoes.csv", transitions)
        v2.write_csv(
            output / "alocacao_diagnostica.csv",
            plan.group_by(
                "diagnostic_group",
                "diagnostic_reason",
                "diagnostic_N",
                "diagnostic_n",
                "diagnostic_probability",
            )
            .len()
            .to_dicts(),
        )
        atomic_frame(workspace / f"resultados_{mode}.parquet", result)
        review_pairs(db, prior, workspace)
        totals = prior.group_by("lyrics_status").len()
        costs = []
        for status, n in totals.iter_rows():
            done = result.filter(
                (pl.col("before") == status)
                & ~pl.col("after").is_in(["pending", "technical_error"])
            )
            costs.append(
                {
                    "status": status,
                    "population_n": n,
                    "processed_n": done.height,
                    "naive_scale_seconds": n * float(done["seconds"].mean())
                    if done.height and done["seconds"].mean() is not None
                    else None,
                }
            )
        summary = {
            "mode": mode,
            "completed": complete,
            "budget_seconds": seconds,
            "elapsed_seconds_including_exports": time.monotonic() - started,
            "new_queries": new,
            "reused_queries": reused,
            "selected_tracks": len(order),
            "transitions": transitions,
            "scale_cost_by_group": costs,
            "approximate_auto_acceptance": False,
            "precision_measured": False,
            "new_indexes": 0,
            "seal": seal,
            "scope": "diagnostic_only" if mode == "evaluate" else "full_sample",
        }
        gains = result.filter((pl.col("before") != "accepted") & (pl.col("after") == "accepted"))
        summary.update(
            new_acceptances=gains.height,
            classifier_gain=gains.filter(pl.col("gain_stage") == "classifier").height,
            expanded_search_gain=gains.filter(pl.col("gain_stage") == "expanded_search").height,
            previous_acceptances_now_inconclusive=result.filter(
                (pl.col("before") == "accepted")
                & ~pl.col("after").is_in(["accepted", "pending", "technical_error"])
            ).height,
            proposed_candidate_pairs=int(result["proposals"].sum()),
        )
        if mode == "evaluate":
            measured = plan.join(result, on="track_id", validate="1:1")
            summary["projected_net_gain_in_three_diagnostic_groups"] = (
                float(
                    measured.select(
                        (
                            (pl.col("after") == "accepted").cast(pl.Int64)
                            - (pl.col("before") == "accepted").cast(pl.Int64)
                        )
                        / pl.col("diagnostic_probability")
                    )
                    .to_series()
                    .sum()
                )
                if complete
                else None
            )
        if mode == "apply":
            final, _ = v1.export_private(db, sample, workspace)
            export_text_sources(workspace)
            final = final.with_columns(pl.lit(VERSION).alias("lyrics_rules_version")).join(
                prior.select("track_id", pl.col("lyrics_status").alias("v2_lyrics_status")),
                on="track_id",
                validate="1:1",
            )
            atomic_frame(workspace / "resultados_faixas_200k.parquet", final)
            v2.write_csv(output / "comparacao_cobertura.csv", v1.coverage_tables(final))
        summary["elapsed_seconds_including_exports"] = time.monotonic() - started
        atomic_json(output / "resumo.json", summary)
        (output / "relatorio.md").write_text(
            "# Rodada v3\n\n"
            + f"Escopo: {summary['scope']}; concluída: {complete}. Avaliação diagnóstica não aprova a base final.\n\n"
            + f"Novas aceitações: {summary['new_acceptances']} (classificador: {summary['classifier_gain']}; busca ampliada: {summary['expanded_search_gain']}). Aceitações anteriores agora inconclusivas: {summary['previous_acceptances_now_inconclusive']}. Pares propostos: {summary['proposed_candidate_pairs']}. Projeção no JSON refere-se somente aos três grupos sorteados e a decisões automáticas, sem precisão humana aferida.\n\n"
            + v1.markdown_table(transitions, ["before", "after", "gain_stage", "reason", "len"])
            + "\n\nScores apenas recuperam candidatos; aceite aproximado desativado. Precisão ainda não medida. Custo de escala é extrapolação por grupo, sem incluir validação/exportação; censura por tempo e grupos não avaliados impedem previsão completa. Índices restritos não provam ausência no dump. Nenhuma nova varredura proposta automaticamente.\n",
            encoding="utf-8",
        )
        return 0 if complete else 2


def cli():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["evaluate", "apply"])
    p.add_argument("--seconds", type=float)
    a = p.parse_args()
    return run(
        a.mode, a.seconds if a.seconds is not None else (600 if a.mode == "evaluate" else 86400)
    )
