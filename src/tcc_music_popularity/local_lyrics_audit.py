"""Audita a coleção aceita em leitura, sem modificar resultados ou carregar modelos."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from contextlib import closing
from datetime import UTC, datetime

from .io import sha256_file, utc_now
from .local_lyrics import DEFAULT_LOCAL, safe_query
from .lrclib_dump import save_json
from .manual_embeddings import read_accepted_text
from .manual_lyrics import DEFAULT_WORKSPACE, ROOT, connect, exclusive, require

ACCEPTED_SQL = "('accepted_exact_unique','accepted_exact_equivalent')"
AUDIT_ROOT = ROOT / "data/derived/private_local_lyrics_audit"


def manifest_signature(db):
    """Compara IDs, vínculos e metadados/splits; status novos podem diferir."""
    hashes = {}
    for table, columns, ordering in (
        ("tracks", "track_id,query_id,data", "track_id"),
        ("queries", "query_id,composition_key,data", "query_id"),
    ):
        digest, count = hashlib.sha256(), 0
        for row in db.execute(f"SELECT {columns} FROM {table} ORDER BY {ordering}"):
            block = json.dumps(tuple(row), ensure_ascii=False).encode("utf-8")
            digest.update(len(block).to_bytes(8, "big"))
            digest.update(block)
            count += 1
        hashes[table] = {"rows": count, "sha256": digest.hexdigest()}
    return hashes


def shared_hashes(groups):
    return {digest: rows for digest, rows in groups.items() if len({r["split"] for r in rows}) > 1}


def audit(source=DEFAULT_WORKSPACE, workspace=DEFAULT_LOCAL, output_root=AUDIT_ROOT):
    require((source / "state.sqlite").is_file(), "Checkpoint original ausente.")
    require((workspace / "state.sqlite").is_file(), "Coleta local ausente.")
    output = output_root / datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
    with (
        exclusive(source),
        exclusive(workspace),
        closing(connect(source, readonly=True)) as original,
        closing(connect(workspace, readonly=True)) as db,
    ):
        require(
            db.execute("SELECT count(*) FROM local_jobs WHERE state!='complete'").fetchone()[0]
            == 0,
            "A coleta possui pendências/erros; conclua ou revise antes da auditoria.",
        )
        output.mkdir(parents=True, exist_ok=False)
        before = {
            "source": sha256_file(source / "state.sqlite"),
            "local": sha256_file(workspace / "state.sqlite"),
        }
        original_manifest, current_manifest = manifest_signature(original), manifest_signature(db)
        unchanged = original_manifest == current_manifest
        status_counts = dict(db.execute("SELECT status,count(*) FROM queries GROUP BY status"))
        planned = sum(
            status_counts.get(s, 0) for s in ("accepted_exact_unique", "accepted_exact_equivalent")
        )
        strict_groups, normalized_groups = defaultdict(list), defaultdict(list)
        valid_by_split, errors = Counter(), []
        processed, interrupted = 0, False
        with (output / "accepted_text_index.jsonl").open("w", encoding="utf-8") as index:
            try:
                for row in db.execute(
                    f"SELECT * FROM queries WHERE status IN {ACCEPTED_SQL} ORDER BY query_id"
                ):
                    try:
                        safe_query(row["data"])
                        text = read_accepted_text(
                            row
                        )  # Hash do cache, candidato selecionado e hash estrito.
                        item = {k: v for k, v in text.items() if k != "private_lyrics"}
                        item["characters_normalized"] = len(text["private_lyrics"])
                        index.write(json.dumps(item, ensure_ascii=False) + "\n")
                        identity = {"query_id": row["query_id"], "split": text["split"]}
                        strict_groups[text["source_strict_sha256"]].append(identity)
                        normalized_groups[text["lyrics_sha256"]].append(identity)
                        valid_by_split[text["split"]] += 1
                    except (ValueError, OSError, TypeError, KeyError) as exc:
                        errors.append(
                            {"query_id": row["query_id"], "error_type": type(exc).__name__}
                        )
                    processed += 1
                    if processed % 250 == 0 or processed == planned:
                        print(
                            json.dumps(
                                {
                                    "stage": "auditing",
                                    "processed": processed,
                                    "planned": planned,
                                    "integrity_errors": len(errors),
                                }
                            ),
                            flush=True,
                        )
            except KeyboardInterrupt:
                interrupted = True
        group_splits = {
            key: defaultdict(set) for key in ("artist_group_id", "composition_group_id")
        }
        missing_groups = Counter()
        accepted_tracks = 0
        for row in db.execute(
            f"SELECT t.data FROM tracks t JOIN queries q ON t.query_id=q.query_id WHERE q.status IN {ACCEPTED_SQL}"
        ):
            metadata = json.loads(row[0])
            accepted_tracks += 1
            for key, groups in group_splits.items():
                if metadata.get(key) and metadata.get("split"):
                    groups[str(metadata[key])].add(metadata["split"])
                else:
                    missing_groups[key] += 1
        shared_groups = {
            key: {g: sorted(splits) for g, splits in groups.items() if len(splits) > 1}
            for key, groups in group_splits.items()
        }
        strict_shared, normalized_shared = (
            shared_hashes(strict_groups),
            shared_hashes(normalized_groups),
        )
        orphans = db.execute(
            "SELECT count(*) FROM tracks t WHERE query_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM queries q WHERE q.query_id=t.query_id)"
        ).fetchone()[0]
        after = {
            "source": sha256_file(source / "state.sqlite"),
            "local": sha256_file(workspace / "state.sqlite"),
        }
        needs_review = bool(
            errors
            or not unchanged
            or before != after
            or orphans
            or strict_shared
            or normalized_shared
            or missing_groups
            or any(shared_groups.values())
        )
        value = {
            "stage": "interrupted" if interrupted else "audit_complete",
            "complete": not interrupted and processed == planned,
            "updated_at": utc_now(),
            "accepted_queries": planned,
            "accepted_tracks": accepted_tracks,
            "processed": processed,
            "valid_texts_by_split": dict(valid_by_split),
            "unique_strict_texts": len(strict_groups),
            "unique_normalized_texts": len(normalized_groups),
            "shared_strict_hashes_between_splits": len(strict_shared),
            "shared_normalized_hashes_between_splits": len(normalized_shared),
            "shared_groups_between_splits": {k: len(v) for k, v in shared_groups.items()},
            "missing_group_metadata": dict(missing_groups),
            "integrity_errors": len(errors),
            "orphan_track_links": orphans,
            "manifest_and_splits_identical_to_original": unchanged,
            "input_files_unchanged": before == after,
            "status_counts": status_counts,
            "review_required": needs_review or interrupted,
            "scope": "integrity_and_exact_text_overlap_not_human_match_or_semantic_review",
            "output_directory": str(output),
        }
        save_json(
            output / "issues_private.json",
            {
                "integrity_errors": errors,
                "shared_strict": strict_shared,
                "shared_normalized": normalized_shared,
                "shared_groups": shared_groups,
            },
        )
        save_json(
            output / "provenance.json",
            {
                "inputs_before": before,
                "inputs_after": after,
                "original_manifest": original_manifest,
                "current_manifest": current_manifest,
                "code_sha256": sha256_file(__file__),
                "accepted_index_sha256": sha256_file(output / "accepted_text_index.jsonl"),
            },
        )
        save_json(output / "summary.json", value)
        print(json.dumps(value, ensure_ascii=False, indent=2), flush=True)
        return 2 if value["review_required"] else 0


def cli():
    parser = argparse.ArgumentParser(
        description="Audita caches aceitos, vínculos, splits e textos repetidos, sem embeddings."
    )
    parser.add_argument(
        "--all", action="store_true", required=True, help="Confere todas as consultas aceitas."
    )
    parser.parse_args()
    try:
        return audit()
    except (ValueError, RuntimeError, OSError) as exc:
        print(
            json.dumps(
                {
                    "stage": "failed",
                    "error_type": type(exc).__name__,
                    "reason": "audit_not_completed_preserve_inputs",
                }
            )
        )
        return 1
