"""Triagem técnica limitada das fichas; não substitui revisão semântica humana."""

from collections import Counter
from pathlib import Path

from . import linkage_review_plan as pilot
from . import lyrics_evaluation as rules
from . import popularity_levels as common

ROOT = common.ROOT
SOURCE = pilot.WORKSPACE / "manifesto_privado.json"
OUTPUT = ROOT / "reports/triagem_piloto_vinculacao_200k_v1"
PRIVATE = ROOT / "data/derived/private_linkage_triage_200k_v1"


def triage(rows):
    common.require(0 < len(rows) <= 240, "Piloto excede 240 consultas.")
    common.require(len({r["case_id"] for r in rows}) == len(rows), "Ficha repetida.")
    result = []
    for row in rows:
        common.require(len(row["candidates"]) <= 50, "Ficha excede cinquenta candidatos.")
        query = {
            "artist_name_query": row["artist_name"],
            "track_name_query": row["track_name"],
            "duration_seconds": float(row["duration_ms"]) / 1000
            if row["duration_ms"] is not None
            else None,
        }
        selected = [
            c
            for c in row["candidates"]
            if str(c.get("id")) == str(row.get("lyrics_selected_lrclib_id"))
        ]
        checks = [rules.agreement(query, c) for c in selected]
        status = "not_an_accepted_case"
        if row["lyrics_status"] == "accepted":
            if not selected:
                status = "selected_candidate_not_available_in_sheet"
            elif all(
                all(
                    c[k]
                    for k in (
                        "artist_exact",
                        "title_exact",
                        "collaboration_exact",
                        "version_compatible",
                        "duration_compatible",
                    )
                )
                for c in checks
            ):
                status = "selected_metadata_consistent_under_v3_rules"
            else:
                status = "selected_metadata_requires_review_under_v3_rules"
        result.append(
            {
                "case_id": row["case_id"],
                "old_status": row["lyrics_status"],
                "extreme_tail": row["extreme_tail"],
                "cache_status": row["cache_status"],
                "candidate_list_truncated": row["candidate_list_truncated"],
                "source_incomplete": bool(row.get("source_incomplete_reason")),
                "technical_status": status,
                "selected_candidate_checks": checks,
                "human_semantic_review": "pending",
                "existing_decision_changed": False,
            }
        )
    return result


def run(source=SOURCE, output=OUTPUT, private=PRIVATE):
    from .manual_lyrics import exclusive

    source = Path(source)
    common.require(source.stat().st_size <= 2 * 1024**2, "Manifesto excede orçamento de 2 MiB.")
    seal = {
        "source": common.digest(source),
        "code": common.digest(Path(__file__)),
        "rules": common.digest(Path(rules.__file__)),
        "pilot": common.digest(Path(pilot.__file__)),
    }
    with exclusive(Path(private)):
        common.prepare_output(private, seal, [source])
        common.prepare_output(output, seal, [source])
        rows = triage(common.read_json(source))
        common.atomic_json(Path(private) / "triagem_tecnica.json", rows)
        counts = Counter(
            (
                r["old_status"],
                r["extreme_tail"],
                r["technical_status"],
                r["cache_status"],
                r["candidate_list_truncated"],
            )
            for r in rows
        )
        common.write_csv(
            Path(output) / "triagem_agregada.csv",
            [
                {
                    "old_status": k[0],
                    "extreme_tail": k[1],
                    "technical_status": k[2],
                    "cache_status": k[3],
                    "candidate_list_truncated": k[4],
                    "n_queries": n,
                }
                for k, n in sorted(counts.items())
            ],
        )
        summary = {
            "completed": True,
            "seal": seal,
            "queries": len(rows),
            "accepted_cases": sum(r["old_status"] == "accepted" for r in rows),
            "technical_counts": dict(Counter(r["technical_status"] for r in rows)),
            "human_review_completed": False,
            "precision_estimated": False,
            "existing_decisions_changed": False,
            "source_unchanged": common.digest(source) == seal["source"],
        }
        common.require(summary["source_unchanged"], "Manifesto mudou durante triagem.")
        common.atomic_json(Path(output) / "resumo_triagem.json", summary)
    print(
        "Triagem técnica concluída; revisão semântica permanece pendente. " + str(output),
        flush=True,
    )
    return summary


def cli():
    run()
    return 0
