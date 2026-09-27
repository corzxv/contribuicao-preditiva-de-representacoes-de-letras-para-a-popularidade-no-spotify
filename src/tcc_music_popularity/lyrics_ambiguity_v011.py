"""Auditoria offline e recalibração conservadora das ambiguidades do smoke de letras."""

from __future__ import annotations

import hashlib
import json
import math
import re
import socket
import subprocess
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import polars as pl

from .config import PROJECT_ROOT, load_yaml, project_path
from .io import git_commit, read_json, sha256_file, write_json
from .lyrics_pilot import (
    DEFAULT_CONFIG_PATH,
    _atomic_write_frame,
    _candidate_diagnostics,
    _frozen_state,
    _git_tracked_private_files,
    _markdown_table,
    _text_present,
    _write_text,
)
from .normalization import conservative_normalize

AUDIT_VERSION = "v0.1.1"
FORBIDDEN_TEXT_FIELDS = {"plainLyrics", "syncedLyrics", "lyricsfile"}
FORBIDDEN_SUCCESS_FIELDS = {"spotify_popularity", "genius_lyrics_views", "lfm_playcount"}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def strict_plain_text_metrics(value: Any) -> dict[str, Any]:
    """Fingerprint conservador; não retorna o texto normalizado."""
    if not _text_present(value):
        return {
            "strict_text_sha256": None,
            "strict_character_count": None,
            "strict_line_count": None,
        }
    normalized = unicodedata.normalize("NFC", str(value)).replace("\ufeff", "")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).rstrip(" ") for line in normalized.split("\n")]
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    normalized = "\n".join(lines)
    return {
        "strict_text_sha256": _sha256(normalized),
        "strict_character_count": len(normalized),
        "strict_line_count": len(lines),
    }


def flexible_plain_text_metrics(value: Any) -> dict[str, Any]:
    """Fingerprint diagnóstico; nunca participa da aceitação automática."""
    strict = strict_plain_text_metrics(value)
    if strict["strict_text_sha256"] is None:
        return {"flexible_text_sha256": None}
    normalized = unicodedata.normalize("NFC", str(value)).replace("\ufeff", "")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n").casefold()
    lines: list[str] = []
    for line in normalized.split("\n"):
        folded = conservative_normalize(line) or ""
        lines.append(folded)
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    return {"flexible_text_sha256": _sha256("\n".join(lines))}


def _technical_candidate_identity(candidate: Mapping[str, Any]) -> str:
    identifier = candidate.get("id")
    if identifier is not None:
        return f"lrclib_id:{identifier}"
    metadata = {
        "artist": conservative_normalize(candidate.get("artistName")),
        "title": conservative_normalize(candidate.get("trackName") or candidate.get("name")),
        "album": conservative_normalize(candidate.get("albumName")),
        "duration": candidate.get("duration"),
        "instrumental": bool(candidate.get("instrumental")),
        "has_plain": _text_present(candidate.get("plainLyrics")),
        "has_synced": _text_present(candidate.get("syncedLyrics")),
    }
    return "metadata_sha256:" + _sha256(
        json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def _candidate_occurrences(envelope: Mapping[str, Any]) -> list[dict[str, Any]]:
    occurrences: list[dict[str, Any]] = []
    for request_order, request in enumerate(envelope.get("requests", [])):
        endpoint = str(request.get("endpoint"))
        payload = request.get("payload")
        candidates: list[Any]
        if request.get("http_status") == 200 and isinstance(payload, dict):
            candidates = [payload]
        elif request.get("http_status") == 200 and isinstance(payload, list):
            candidates = payload
        else:
            candidates = []
        for endpoint_index, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                continue
            occurrences.append(
                {
                    "endpoint": endpoint,
                    "request_order": request_order,
                    "endpoint_index": endpoint_index,
                    "identity": _technical_candidate_identity(candidate),
                    "candidate": candidate,
                }
            )
    return occurrences


def _metadata_signature(candidate: Mapping[str, Any]) -> str:
    metadata = {
        "artist": candidate.get("artistName"),
        "title": candidate.get("trackName") or candidate.get("name"),
        "album": candidate.get("albumName"),
        "duration": candidate.get("duration"),
        "instrumental": candidate.get("instrumental"),
    }
    return _sha256(json.dumps(metadata, ensure_ascii=False, sort_keys=True, default=str))


def deduplicate_candidates(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Dedupe primeiro em cada endpoint e depois na união de endpoints."""
    occurrences = _candidate_occurrences(envelope)
    per_endpoint: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    by_identity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for occurrence in occurrences:
        per_endpoint[occurrence["endpoint"]][occurrence["identity"]].append(occurrence)
        by_identity[occurrence["identity"]].append(occurrence)
    within_endpoint_count = sum(len(items) for items in per_endpoint.values())
    endpoint_identity_sets = {endpoint: set(items) for endpoint, items in per_endpoint.items()}
    repeated_between = (
        set.intersection(*endpoint_identity_sets.values())
        if len(endpoint_identity_sets) >= 2
        else set()
    )
    unified: list[dict[str, Any]] = []
    for identity in sorted(by_identity):
        group = by_identity[identity]
        ordered = sorted(
            group,
            key=lambda item: (
                0 if item["endpoint"] == "/api/get" else 1,
                item["request_order"],
                item["endpoint_index"],
            ),
        )
        candidate = ordered[0]["candidate"]
        strict_hashes = {
            strict_plain_text_metrics(item["candidate"].get("plainLyrics"))["strict_text_sha256"]
            for item in group
            if _text_present(item["candidate"].get("plainLyrics"))
        }
        metadata_hashes = {_metadata_signature(item["candidate"]) for item in group}
        unified.append(
            {
                "identity": identity,
                "candidate_key_sha256": _sha256(identity),
                "candidate": candidate,
                "endpoints": sorted({item["endpoint"] for item in group}),
                "raw_occurrence_count": len(group),
                "same_identity_strict_text_hash_count": len(strict_hashes),
                "same_identity_metadata_hash_count": len(metadata_hashes),
                "identity_payload_conflict": len(strict_hashes) > 1,
            }
        )
    strict_group_keys: set[str] = set()
    flexible_group_keys: set[str] = set()
    for item in unified:
        candidate = item["candidate"]
        strict = strict_plain_text_metrics(candidate.get("plainLyrics"))["strict_text_sha256"]
        flexible = flexible_plain_text_metrics(candidate.get("plainLyrics"))["flexible_text_sha256"]
        strict_group_keys.add(strict or f"no_plain:{item['candidate_key_sha256']}")
        flexible_group_keys.add(flexible or f"no_plain:{item['candidate_key_sha256']}")
    return {
        "occurrences": occurrences,
        "unified": unified,
        "candidate_count_before_dedup": len(occurrences),
        "candidate_count_after_within_endpoint_id_dedup": within_endpoint_count,
        "candidate_count_after_endpoint_union": len(unified),
        "candidate_count_after_strict_text_grouping": len(strict_group_keys),
        "candidate_count_after_flexible_text_grouping": len(flexible_group_keys),
        "repeated_identities_between_endpoints": repeated_between,
    }


def _metadata_completeness(candidate: Mapping[str, Any]) -> int:
    return sum(
        [
            _text_present(candidate.get("artistName")),
            _text_present(candidate.get("trackName") or candidate.get("name")),
            _text_present(candidate.get("albumName")),
            candidate.get("duration") is not None,
        ]
    )


def _representative_sort_key(item: Mapping[str, Any]) -> tuple[Any, ...]:
    diagnostics = item["diagnostics"]
    difference = diagnostics.get("duration_difference_seconds")
    identifier = item["candidate"].get("id")
    try:
        identifier_key = (0, int(identifier))
    except (TypeError, ValueError):
        identifier_key = (1, math.inf)
    return (
        float(difference) if difference is not None else math.inf,
        0 if "/api/get" in item["endpoints"] else 1,
        -_metadata_completeness(item["candidate"]),
        identifier_key,
        item["candidate_key_sha256"],
    )


def _request_error_unrecovered(envelope: Mapping[str, Any]) -> bool:
    statuses = {
        str(request.get("endpoint")): request.get("http_status")
        for request in envelope.get("requests", [])
    }
    return statuses.get("/api/search") != 200 or statuses.get("/api/get") not in {200, 404}


def _metadata_conflict_cause(items: Sequence[Mapping[str, Any]]) -> str:
    if not items:
        return "other_observed_cause"
    if not any(item["diagnostics"]["artist_compatible"] for item in items):
        return "artist_conflict"
    artist_items = [item for item in items if item["diagnostics"]["artist_compatible"]]
    if not any(item["diagnostics"]["title_compatible"] for item in artist_items):
        return "title_conflict"
    title_items = [item for item in artist_items if item["diagnostics"]["title_compatible"]]
    if not any(item["diagnostics"]["version_compatible"] for item in title_items):
        return "version_conflict"
    version_items = [item for item in title_items if item["diagnostics"]["version_compatible"]]
    if not any(item["diagnostics"]["duration_compatible"] for item in version_items):
        return "duration_conflict"
    if any(not item["plain_lyrics_available"] for item in version_items):
        return "plain_lyrics_absent"
    if any(item["identity_payload_conflict"] for item in items):
        return "same_id_payload_conflict"
    return "other_observed_cause"


def reclassify_cached_composition(
    query: Mapping[str, Any],
    envelope: Mapping[str, Any],
    *,
    old_status: str,
    duration_tolerance: float = 10.0,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    deduplicated = deduplicate_candidates(envelope)
    evaluated: list[dict[str, Any]] = []
    for item in deduplicated["unified"]:
        candidate = item["candidate"]
        strict = strict_plain_text_metrics(candidate.get("plainLyrics"))
        flexible = flexible_plain_text_metrics(candidate.get("plainLyrics"))
        diagnostics = _candidate_diagnostics(query, candidate, duration_tolerance)
        evaluated.append(
            {
                **item,
                "diagnostics": diagnostics,
                **strict,
                **flexible,
                "plain_lyrics_available": _text_present(candidate.get("plainLyrics")),
                "synced_lyrics_available": _text_present(candidate.get("syncedLyrics")),
            }
        )
    compatible = [item for item in evaluated if item["diagnostics"]["accepted_by_rules"]]
    compatible_with_plain = [item for item in compatible if item["plain_lyrics_available"]]
    compatible_hashes = {
        item["strict_text_sha256"] for item in compatible_with_plain if item["strict_text_sha256"]
    }
    compatible_flexible_hashes = {
        item["flexible_text_sha256"]
        for item in compatible_with_plain
        if item["flexible_text_sha256"]
    }
    selected: dict[str, Any] | None = None
    if _request_error_unrecovered(envelope):
        final_status = "request_error"
    elif not evaluated:
        final_status = "not_found"
    elif compatible and all(
        bool(item["candidate"].get("instrumental")) and not item["plain_lyrics_available"]
        for item in compatible
    ):
        final_status = "instrumental"
        selected = sorted(compatible, key=_representative_sort_key)[0]
    elif len(compatible) == 1 and len(compatible_with_plain) == 1:
        final_status = "accepted_exact_unique"
        selected = compatible_with_plain[0]
    elif (
        len(compatible) >= 2
        and len(compatible) == len(compatible_with_plain)
        and len(compatible_hashes) == 1
        and not any(item["identity_payload_conflict"] for item in compatible)
    ):
        final_status = "accepted_exact_equivalent"
        selected = sorted(compatible_with_plain, key=_representative_sort_key)[0]
    elif len(compatible_with_plain) >= 2 and len(compatible_hashes) > 1:
        final_status = "ambiguous_distinct_lyrics"
    else:
        final_status = "ambiguous_metadata_conflict"

    raw_compatible_count = sum(
        1
        for occurrence in deduplicated["occurrences"]
        if _candidate_diagnostics(query, occurrence["candidate"], duration_tolerance)[
            "accepted_by_rules"
        ]
    )
    duplicate_between_count = len(deduplicated["repeated_identities_between_endpoints"])
    resolved_by_id_dedup = (
        old_status == "ambiguous"
        and final_status == "accepted_exact_unique"
        and raw_compatible_count > 1
        and len(compatible) == 1
        and duplicate_between_count > 0
    )
    resolved_by_strict_equivalence = (
        old_status == "ambiguous" and final_status == "accepted_exact_equivalent"
    )
    if final_status == "accepted_exact_unique":
        ambiguity_cause = (
            "duplicate_id_between_endpoints"
            if resolved_by_id_dedup
            else "unique_compatible_candidate"
        )
    elif final_status == "accepted_exact_equivalent":
        albums = {str(item["candidate"].get("albumName")) for item in compatible}
        durations = {str(item["candidate"].get("duration")) for item in compatible}
        ambiguity_cause = (
            "different_ids_same_text_different_metadata"
            if len(albums) > 1 or len(durations) > 1
            else "different_ids_strict_plain_equivalent"
        )
    elif final_status == "ambiguous_distinct_lyrics":
        ambiguity_cause = "multiple_distinct_plain_lyrics"
    elif final_status == "ambiguous_metadata_conflict":
        ambiguity_cause = _metadata_conflict_cause(evaluated)
    elif final_status == "instrumental":
        ambiguity_cause = "instrumental_without_plain_lyrics"
    elif final_status == "not_found":
        ambiguity_cause = "not_found"
    else:
        ambiguity_cause = "unrecovered_request_error"

    requests = {str(item.get("endpoint")): item for item in envelope.get("requests", [])}
    search_payload = requests.get("/api/search", {}).get("payload")
    search_result_count = len(search_payload) if isinstance(search_payload, list) else 0
    selected_candidate = selected["candidate"] if selected else {}
    selected_diagnostics = selected["diagnostics"] if selected else {}
    row = {
        "audit_version": AUDIT_VERSION,
        "composition_key": query["composition_key"],
        "representative_spotify_row_id": query["representative_spotify_row_id"],
        "representative_track_id": query["representative_track_id"],
        "old_status": old_status,
        "reclassified_status": final_status,
        "ambiguity_cause": ambiguity_cause,
        "candidate_count_before_dedup": deduplicated["candidate_count_before_dedup"],
        "candidate_count_after_within_endpoint_id_dedup": deduplicated[
            "candidate_count_after_within_endpoint_id_dedup"
        ],
        "candidate_count_after_endpoint_union": deduplicated[
            "candidate_count_after_endpoint_union"
        ],
        "candidate_count_after_strict_text_grouping": deduplicated[
            "candidate_count_after_strict_text_grouping"
        ],
        "candidate_count_after_flexible_text_grouping": deduplicated[
            "candidate_count_after_flexible_text_grouping"
        ],
        "duplicate_ids_between_endpoints": duplicate_between_count,
        "raw_compatible_candidate_count": raw_compatible_count,
        "compatible_candidate_count": len(compatible),
        "compatible_plain_candidate_count": len(compatible_with_plain),
        "compatible_strict_fingerprint_count": len(compatible_hashes),
        "compatible_flexible_fingerprint_count_diagnostic_only": len(compatible_flexible_hashes),
        "resolved_exclusively_by_id_dedup": resolved_by_id_dedup,
        "resolved_by_strict_text_equivalence": resolved_by_strict_equivalence,
        "search_result_count": search_result_count,
        "search_limit_20_reached": search_result_count >= 20,
        "any_plain_lyrics_available": any(item["plain_lyrics_available"] for item in evaluated),
        "any_synced_lyrics_available": any(item["synced_lyrics_available"] for item in evaluated),
        "selected_lrclib_id": selected_candidate.get("id"),
        "selected_candidate_key_sha256": selected.get("candidate_key_sha256") if selected else None,
        "selected_returned_artist": selected_candidate.get("artistName"),
        "selected_returned_title": selected_candidate.get("trackName")
        or selected_candidate.get("name"),
        "selected_returned_album": selected_candidate.get("albumName"),
        "selected_returned_duration_seconds": selected_candidate.get("duration"),
        "selected_duration_difference_seconds": selected_diagnostics.get(
            "duration_difference_seconds"
        ),
        "selected_plain_lyrics_available": selected.get("plain_lyrics_available")
        if selected
        else False,
        "selected_synced_lyrics_available": selected.get("synced_lyrics_available")
        if selected
        else False,
        "selected_strict_text_sha256": selected.get("strict_text_sha256") if selected else None,
        "selected_flexible_text_sha256_diagnostic_only": selected.get("flexible_text_sha256")
        if selected
        else None,
        "selected_strict_character_count": selected.get("strict_character_count")
        if selected
        else None,
        "selected_strict_line_count": selected.get("strict_line_count") if selected else None,
        "source_cache_queried_at": envelope.get("queried_at"),
    }
    candidate_rows: list[dict[str, Any]] = []
    compatible_group_size = Counter(
        item["strict_text_sha256"] for item in compatible_with_plain if item["strict_text_sha256"]
    )
    for item in evaluated:
        candidate = item["candidate"]
        diagnostics = item["diagnostics"]
        candidate_rows.append(
            {
                "audit_version": AUDIT_VERSION,
                "composition_key": query["composition_key"],
                "candidate_key_sha256": item["candidate_key_sha256"],
                "lrclib_id": candidate.get("id"),
                "source_endpoints": "|".join(item["endpoints"]),
                "source_endpoint_count": len(item["endpoints"]),
                "raw_occurrence_count": item["raw_occurrence_count"],
                "returned_artist": candidate.get("artistName"),
                "returned_title": candidate.get("trackName") or candidate.get("name"),
                "returned_album": candidate.get("albumName"),
                "returned_duration_seconds": candidate.get("duration"),
                "instrumental": bool(candidate.get("instrumental")),
                "artist_compatible": diagnostics["artist_compatible"],
                "title_compatible": diagnostics["title_compatible"],
                "version_compatible": diagnostics["version_compatible"],
                "duration_compatible": diagnostics["duration_compatible"],
                "duration_difference_seconds": diagnostics["duration_difference_seconds"],
                "compatible_by_exact_rules": diagnostics["accepted_by_rules"],
                "plain_lyrics_available": item["plain_lyrics_available"],
                "synced_lyrics_available": item["synced_lyrics_available"],
                "strict_text_sha256": item["strict_text_sha256"],
                "flexible_text_sha256_diagnostic_only": item["flexible_text_sha256"],
                "strict_character_count": item["strict_character_count"],
                "strict_line_count": item["strict_line_count"],
                "compatible_strict_group_size": compatible_group_size.get(
                    item["strict_text_sha256"], 0
                ),
                "same_identity_strict_text_hash_count": item[
                    "same_identity_strict_text_hash_count"
                ],
                "same_identity_metadata_hash_count": item["same_identity_metadata_hash_count"],
                "identity_payload_conflict": item["identity_payload_conflict"],
                "selected_representative": bool(
                    selected and item["candidate_key_sha256"] == selected["candidate_key_sha256"]
                ),
                "composition_reclassified_status": final_status,
                "composition_ambiguity_cause": ambiguity_cause,
                "search_limit_20_reached": search_result_count >= 20,
            }
        )
    equivalent_ids = [
        item["candidate"].get("id")
        for item in compatible_with_plain
        if final_status == "accepted_exact_equivalent"
    ]
    private_provenance = {
        "composition_key": query["composition_key"],
        "reclassified_status": final_status,
        "selected_lrclib_id": selected_candidate.get("id"),
        "equivalent_lrclib_ids": equivalent_ids,
        "equivalent_candidates": [
            {
                "lrclib_id": item["candidate"].get("id"),
                "endpoints": item["endpoints"],
                "strict_text_sha256": item["strict_text_sha256"],
            }
            for item in compatible_with_plain
            if final_status == "accepted_exact_equivalent"
        ],
    }
    return row, candidate_rows, private_provenance


def _directory_manifest(path: Path) -> dict[str, Any]:
    files = sorted(item for item in path.glob("*.json") if item.is_file())
    manifest = [(item.name, sha256_file(item)) for item in files]
    digest = _sha256(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")))
    return {"file_count": len(files), "manifest_sha256": digest}


def _tracked_or_staged_private_files() -> dict[str, list[str]]:
    tracked = _git_tracked_private_files()
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={PROJECT_ROOT.as_posix()}",
            "diff",
            "--cached",
            "--name-only",
        ],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    staged = [
        line
        for line in result.stdout.splitlines()
        if line.startswith(("data/raw/lyrics_private/", "data/interim/lyrics_private/"))
    ]
    return {"tracked": tracked, "staged": staged}


def _artifact_hashes(paths: Iterable[str | Path]) -> dict[str, str]:
    return {
        project_path(path).relative_to(PROJECT_ROOT).as_posix(): sha256_file(project_path(path))
        for path in paths
    }


def _assert_no_lyrics_in_public_artifacts(
    reclassified: pl.DataFrame,
    candidates: pl.DataFrame,
    report_text: str,
    raw_plain_texts: Sequence[str],
) -> None:
    for frame in (reclassified, candidates):
        forbidden = FORBIDDEN_TEXT_FIELDS & set(frame.columns)
        if forbidden:
            raise AssertionError(f"Campos de texto proibidos no artefato: {sorted(forbidden)}")
        if any(
            "token" in column.casefold() or "ngram" in column.casefold() for column in frame.columns
        ):
            raise AssertionError("Coluna de token ou n-grama detectada em artefato público.")
    report_folded = report_text.casefold()
    for text in raw_plain_texts:
        if len(text) >= 40 and text[:40].casefold() in report_folded:
            raise AssertionError("Trecho de letra detectado no relatório público.")
    public_strings: set[str] = set()
    for frame in (reclassified, candidates):
        for column, dtype in frame.schema.items():
            if dtype == pl.String:
                public_strings.update(str(value) for value in frame.get_column(column).drop_nulls())
    if any(text in public_strings for text in raw_plain_texts):
        raise AssertionError("Texto integral de letra detectado em artefato processado.")


def _status_counts(frame: pl.DataFrame, column: str) -> dict[str, int]:
    return {
        str(row[column]): int(row["len"])
        for row in frame.group_by(column).len().sort(column).to_dicts()
    }


def _distribution_table(frame: pl.DataFrame, columns: Sequence[str]) -> str:
    rows = frame.group_by(list(columns)).len().sort(list(columns)).to_dicts()
    return _markdown_table(rows, [*columns, "len"])


def _recommendation(metrics: Mapping[str, Any]) -> str:
    accepted = float(metrics["automatic_coverage_after"])
    request_errors = int(metrics["after_status_counts"].get("request_error", 0))
    resolved_equivalent = int(metrics["resolved_by_strict_text_equivalence"])
    if accepted >= 0.60 and request_errors == 0 and resolved_equivalent > 0:
        return "realizar um pequeno teste complementar"
    if accepted >= 0.45 and request_errors == 0:
        return "ajustar novamente as regras"
    return "testar uma fonte adicional"


def _build_report(frame: pl.DataFrame, metrics: Mapping[str, Any]) -> str:
    ambiguous_causes = (
        frame.filter(pl.col("old_status") == "ambiguous")
        .group_by("ambiguity_cause")
        .len()
        .sort("ambiguity_cause")
        .to_dicts()
    )
    return f"""# Auditoria e recalibração das ambiguidades — v0.1.1

## Escopo e controles

- Processamento integralmente offline a partir dos 100 caches privados existentes.
- Requisições de rede realizadas: **0**.
- Caches das outras 1.900 composições: **0**.
- Coorte de 2.000, Base v0.1.1 e split preservados.
- O fingerprint flexível foi calculado somente para diagnóstico e nunca participou da aceitação.
- Nenhum texto, trecho, token ou n-grama foi incluído nos artefatos públicos.

## Deduplicação observada

- Ocorrências brutas de candidatos: {metrics["raw_candidate_occurrences"]}.
- Candidatos após deduplicação por ID dentro de cada endpoint: {metrics["after_within_endpoint_id_dedup"]}.
- Candidatos após união de `/api/get` e `/api/search`: {metrics["after_endpoint_union"]}.
- Grupos após equivalência estrita de plain: {metrics["after_strict_text_grouping"]}.
- Grupos após fingerprint flexível, somente diagnóstico: {metrics["after_flexible_text_grouping"]}.
- Redução total de ocorrências pela deduplicação/unificação: {metrics["candidate_reduction_total"]}.
- IDs repetidos entre endpoints: {metrics["duplicate_ids_between_endpoints"]}.
- Composições afetadas por IDs repetidos entre endpoints: {metrics["compositions_with_duplicate_ids_between_endpoints"]}.
- Buscas que atingiram 20 resultados: {metrics["search_limit_20_compositions"]}.

## Antes × depois

| Métrica | Quantidade |
| --- | ---: |
| accepted_exact anterior | {metrics["before_status_counts"].get("accepted_exact", 0)} |
| accepted_exact_unique | {metrics["after_status_counts"].get("accepted_exact_unique", 0)} |
| accepted_exact_equivalent | {metrics["after_status_counts"].get("accepted_exact_equivalent", 0)} |
| total aceito após recalibração | {metrics["accepted_total_after"]} |
| ambiguous anterior | {metrics["before_status_counts"].get("ambiguous", 0)} |
| ambiguous_distinct_lyrics | {metrics["after_status_counts"].get("ambiguous_distinct_lyrics", 0)} |
| ambiguous_metadata_conflict | {metrics["after_status_counts"].get("ambiguous_metadata_conflict", 0)} |
| not_found | {metrics["after_status_counts"].get("not_found", 0)} |
| instrumental | {metrics["after_status_counts"].get("instrumental", 0)} |
| request_error | {metrics["after_status_counts"].get("request_error", 0)} |
| resolvidos exclusivamente por deduplicação de ID | {metrics["resolved_exclusively_by_id_dedup"]} |
| resolvidos por equivalência estrita de plain | {metrics["resolved_by_strict_text_equivalence"]} |
| ambiguidades genuínas remanescentes | {metrics["genuinely_ambiguous_after"]} |

- Cobertura bruta: {100 * metrics["raw_coverage"]:.2f}%.
- Cobertura automática anterior: {100 * metrics["automatic_coverage_before"]:.2f}%.
- Cobertura automática recalibrada: {100 * metrics["automatic_coverage_after"]:.2f}%.

## Causas mutuamente exclusivas nos 72 casos anteriormente ambíguos

{_markdown_table(ambiguous_causes, ["ambiguity_cause", "len"])}

Casos com IDs diferentes e fingerprint estrito igual: {metrics["old_ambiguous_with_same_strict_text"]}.
Casos anteriormente ambíguos com mais de um fingerprint estrito de plain: {metrics["old_ambiguous_with_distinct_strict_text"]}.
Destes, casos que colapsariam somente pelo fingerprint flexível, sem autorização para aceite: {metrics["old_ambiguous_flexible_only_equivalence"]}.
Casos equivalentes com diferenças de álbum ou duração: {metrics["equivalent_with_metadata_differences"]}.

## Distribuições do status recalibrado

### Período

{_distribution_table(frame, ["period", "reclassified_status"])}

### Quintil usado somente na amostragem

{_distribution_table(frame, ["popularity_quintile", "reclassified_status"])}

### Gênero

{_distribution_table(frame, ["genre", "reclassified_status"])}

### Método do match Spotify–LFM2b

{_distribution_table(frame, ["match_method", "reclassified_status"])}

### Disponibilidade de plain

{_distribution_table(frame, ["any_plain_lyrics_available", "reclassified_status"])}

### Disponibilidade de synced

{_distribution_table(frame, ["any_synced_lyrics_available", "reclassified_status"])}

## Interpretação e recomendação

A recalibração aceita somente um candidato exato único com plain disponível ou um conjunto de candidatos exatos cujos fingerprints estritos de plain sejam todos idênticos. Duração, endpoint, completude e ID servem apenas para escolher um representante dentro de um conjunto já comprovadamente equivalente; não transformam candidatos com textos distintos em aceitos.

**Recomendação: {metrics["recommendation"]}.** A cobertura automática subiu para {100 * metrics["automatic_coverage_after"]:.0f}% sem erro técnico, mas {metrics["after_status_counts"].get("ambiguous_distinct_lyrics", 0)} casos ainda contêm letras estritamente distintas e o smoke original não cobriu adequadamente métodos de matching e versões. Um teste complementar pequeno e estratificado deve preceder qualquer escala; as outras 1.900 composições não devem ser consultadas nesta versão.
"""


@contextmanager
def _offline_network_guard() -> Iterable[dict[str, int]]:
    counter = {"blocked_attempts": 0}

    def deny(*args: Any, **kwargs: Any) -> None:
        counter["blocked_attempts"] += 1
        raise RuntimeError("Acesso de rede proibido na auditoria offline v0.1.1.")

    with (
        patch.object(urllib.request, "urlopen", side_effect=deny),
        patch.object(socket, "create_connection", side_effect=deny),
    ):
        yield counter


def _run_offline_audit(config: Mapping[str, Any]) -> dict[str, Any]:
    outputs = config["outputs"]
    cache_dir = project_path(config["lrclib"]["cache_dir"])
    cohort_path = project_path(outputs["cohort_parquet"])
    lookup_path = project_path(outputs["lookup_parquet"])
    old_results_path = project_path(outputs["smoke_results"])
    cohort = pl.read_parquet(cohort_path)
    lookup = pl.read_parquet(lookup_path)
    old_results = pl.read_parquet(old_results_path)
    split = pl.read_parquet(project_path(config["inputs"]["split_assignments"]))
    smoke = cohort.filter(pl.col("smoke_selected")).sort("smoke_order")
    lookup_smoke = lookup.filter(pl.col("smoke_selected")).sort("smoke_order")
    if smoke.height != 100 or lookup_smoke.height != 100 or old_results.height != 100:
        raise AssertionError(
            "Smoke, lookup e resultado anterior devem conter exatamente 100 casos."
        )
    smoke_with_split = smoke.join(
        split.select(["spotify_row_id", "split"]),
        left_on="representative_spotify_row_id",
        right_on="spotify_row_id",
        how="left",
        validate="1:1",
    )
    smoke_split_values = sorted(smoke_with_split.get_column("split").unique().to_list())
    if smoke_split_values != ["development_train"]:
        raise AssertionError(f"Smoke fora do development_train: {smoke_split_values}")
    if FORBIDDEN_SUCCESS_FIELDS & set(lookup_smoke.columns):
        raise AssertionError("O lookup contém medida de sucesso proibida para decisão.")
    smoke_keys = set(smoke.get_column("composition_key"))
    expected_cache_names = {_sha256(key) for key in smoke_keys}
    observed_cache_names = {path.stem for path in cache_dir.glob("*.json")}
    missing_smoke_caches = expected_cache_names - observed_cache_names
    if missing_smoke_caches:
        raise AssertionError(
            f"Caches privados ausentes para {len(missing_smoke_caches)} composições do smoke."
        )
    non_smoke_cache_count = len(observed_cache_names - expected_cache_names)
    old_status_by_key = {
        str(row["composition_key"]): str(row["final_status"])
        for row in old_results.iter_rows(named=True)
    }
    reclassified_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    provenance_rows: list[dict[str, Any]] = []
    raw_plain_texts: list[str] = []
    source_timestamps: list[str] = []
    for query in lookup_smoke.iter_rows(named=True):
        cache_path = cache_dir / f"{_sha256(str(query['composition_key']))}.json"
        envelope = json.loads(cache_path.read_text(encoding="utf-8"))
        source_timestamps.append(str(envelope.get("queried_at")))
        for occurrence in _candidate_occurrences(envelope):
            value = occurrence["candidate"].get("plainLyrics")
            if _text_present(value):
                raw_plain_texts.append(str(value))
        row, rows, private = reclassify_cached_composition(
            query,
            envelope,
            old_status=old_status_by_key[str(query["composition_key"])],
            duration_tolerance=float(config["lrclib"]["duration_tolerance_seconds"]),
        )
        reclassified_rows.append(row)
        candidate_rows.extend(rows)
        provenance_rows.append(private)
    reclassified = (
        pl.DataFrame(reclassified_rows)
        .join(
            smoke.select(
                [
                    "composition_key",
                    "period",
                    "popularity_quintile",
                    "genre",
                    "match_method",
                    "version_profile",
                ]
            ),
            on="composition_key",
            how="left",
            validate="1:1",
        )
        .sort("composition_key")
    )
    candidates = pl.DataFrame(candidate_rows).sort(["composition_key", "candidate_key_sha256"])
    before_counts = _status_counts(reclassified, "old_status")
    after_counts = _status_counts(reclassified, "reclassified_status")
    accepted_after = after_counts.get("accepted_exact_unique", 0) + after_counts.get(
        "accepted_exact_equivalent", 0
    )
    raw_occurrences = int(reclassified.get_column("candidate_count_before_dedup").sum())
    after_within = int(
        reclassified.get_column("candidate_count_after_within_endpoint_id_dedup").sum()
    )
    after_union = int(reclassified.get_column("candidate_count_after_endpoint_union").sum())
    after_strict = int(reclassified.get_column("candidate_count_after_strict_text_grouping").sum())
    after_flexible = int(
        reclassified.get_column("candidate_count_after_flexible_text_grouping").sum()
    )
    metrics: dict[str, Any] = {
        "before_status_counts": before_counts,
        "after_status_counts": after_counts,
        "raw_candidate_occurrences": raw_occurrences,
        "after_within_endpoint_id_dedup": after_within,
        "after_endpoint_union": after_union,
        "after_strict_text_grouping": after_strict,
        "after_flexible_text_grouping": after_flexible,
        "candidate_reduction_total": raw_occurrences - after_union,
        "duplicate_ids_between_endpoints": int(
            reclassified.get_column("duplicate_ids_between_endpoints").sum()
        ),
        "compositions_with_duplicate_ids_between_endpoints": reclassified.filter(
            pl.col("duplicate_ids_between_endpoints") > 0
        ).height,
        "search_limit_20_compositions": reclassified.filter(
            pl.col("search_limit_20_reached")
        ).height,
        "accepted_total_after": accepted_after,
        "resolved_exclusively_by_id_dedup": reclassified.filter(
            pl.col("resolved_exclusively_by_id_dedup")
        ).height,
        "resolved_by_strict_text_equivalence": reclassified.filter(
            pl.col("resolved_by_strict_text_equivalence")
        ).height,
        "genuinely_ambiguous_after": after_counts.get("ambiguous_distinct_lyrics", 0)
        + after_counts.get("ambiguous_metadata_conflict", 0),
        "raw_coverage": reclassified.filter(
            pl.col("candidate_count_after_endpoint_union") > 0
        ).height
        / reclassified.height,
        "automatic_coverage_before": before_counts.get("accepted_exact", 0) / reclassified.height,
        "automatic_coverage_after": accepted_after / reclassified.height,
        "old_ambiguous_with_same_strict_text": reclassified.filter(
            (pl.col("old_status") == "ambiguous")
            & (pl.col("compatible_candidate_count") >= 2)
            & (pl.col("compatible_strict_fingerprint_count") == 1)
        ).height,
        "old_ambiguous_with_distinct_strict_text": reclassified.filter(
            (pl.col("old_status") == "ambiguous")
            & (pl.col("compatible_strict_fingerprint_count") > 1)
        ).height,
        "old_ambiguous_flexible_only_equivalence": reclassified.filter(
            (pl.col("old_status") == "ambiguous")
            & (pl.col("compatible_strict_fingerprint_count") > 1)
            & (pl.col("compatible_flexible_fingerprint_count_diagnostic_only") == 1)
        ).height,
        "equivalent_with_metadata_differences": reclassified.filter(
            pl.col("ambiguity_cause") == "different_ids_same_text_different_metadata"
        ).height,
    }
    metrics["recommendation"] = _recommendation(metrics)
    report_text = _build_report(reclassified, metrics)
    _assert_no_lyrics_in_public_artifacts(reclassified, candidates, report_text, raw_plain_texts)
    _atomic_write_frame(reclassified, outputs["smoke_reclassified_v0_1_1"])
    _atomic_write_frame(candidates, outputs["candidate_audit_v0_1_1"])
    _write_text(outputs["ambiguity_report_v0_1_1"], report_text)
    write_json(
        outputs["ambiguity_private_provenance_v0_1_1"],
        {
            "audit_version": AUDIT_VERSION,
            "source_cache_latest_timestamp": max(source_timestamps),
            "records": sorted(provenance_rows, key=lambda item: item["composition_key"]),
        },
    )
    return {
        "reclassified": reclassified,
        "candidates": candidates,
        "metrics": metrics,
        "source_cache_latest_timestamp": max(source_timestamps),
        "smoke_split_values": smoke_split_values,
        "non_smoke_cache_count": non_smoke_cache_count,
    }


def audit_lyrics_ambiguity_v011(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    outputs = config["outputs"]
    cache_dir = project_path(config["lrclib"]["cache_dir"])
    cache_before = _directory_manifest(cache_dir)
    frozen_before = _frozen_state()
    immutable_paths = [
        "data/processed/modeling_base_lfm_v0_1.parquet",
        "data/processed/modeling_base_lfm_v0_1_1.parquet",
        "data/processed/split_assignments_v0_1_1.parquet",
        outputs["cohort_parquet"],
        outputs["lookup_parquet"],
        outputs["smoke_results"],
    ]
    immutable_hashes_before = _artifact_hashes(immutable_paths)
    with _offline_network_guard() as network_guard:
        result = _run_offline_audit(config)
    cache_after = _directory_manifest(cache_dir)
    frozen_after = _frozen_state()
    immutable_hashes_after = _artifact_hashes(immutable_paths)
    if cache_before != cache_after:
        raise AssertionError("O cache privado foi alterado durante a auditoria offline.")
    if immutable_hashes_before != immutable_hashes_after:
        raise AssertionError("Um artefato imutável foi alterado durante a auditoria.")
    if network_guard["blocked_attempts"]:
        raise AssertionError("Uma tentativa de rede foi bloqueada durante a auditoria.")
    private_git = _tracked_or_staged_private_files()
    public_outputs = [
        outputs["smoke_reclassified_v0_1_1"],
        outputs["candidate_audit_v0_1_1"],
        outputs["ambiguity_report_v0_1_1"],
    ]
    summary = {
        "status": "complete",
        "audit_version": AUDIT_VERSION,
        "source_cache_latest_timestamp": result["source_cache_latest_timestamp"],
        "git_commit": git_commit(),
        "network_requests_made": 0,
        "network_attempts_blocked": network_guard["blocked_attempts"],
        "cache_before": cache_before,
        "cache_after": cache_after,
        "cache_unchanged": cache_before == cache_after,
        "smoke_compositions": result["reclassified"].height,
        "non_smoke_cache_count": result["non_smoke_cache_count"],
        "smoke_split_values": result["smoke_split_values"],
        **result["metrics"],
        "candidate_audit_rows": result["candidates"].height,
        "privacy": {
            "forbidden_text_fields_in_reclassified": sorted(
                FORBIDDEN_TEXT_FIELDS & set(result["reclassified"].columns)
            ),
            "forbidden_text_fields_in_candidate_audit": sorted(
                FORBIDDEN_TEXT_FIELDS & set(result["candidates"].columns)
            ),
            "tracked_private_files": private_git["tracked"],
            "staged_private_files": private_git["staged"],
            "lyrics_in_public_artifacts": False,
            "success_fields_used_in_decision": [],
        },
        "frozen_before": frozen_before,
        "frozen_after": frozen_after,
        "frozen_artifacts_preserved": frozen_before == frozen_after
        and frozen_after["all_hashes_identical"],
        "immutable_hashes_before": immutable_hashes_before,
        "immutable_hashes_after": immutable_hashes_after,
        "immutable_hashes_preserved": immutable_hashes_before == immutable_hashes_after,
        "output_hashes": _artifact_hashes(public_outputs),
        "recommendation_options": [
            "realizar um pequeno teste complementar",
            "escalar para as 1.900 restantes",
            "ajustar novamente as regras",
            "testar uma fonte adicional",
        ],
    }
    write_json(outputs["ambiguity_run_summary_v0_1_1"], summary)
    return summary


def record_ambiguity_verification_v011(
    verification: Mapping[str, Any],
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    """Registra verificações executadas depois da geração idempotente dos artefatos."""
    config = load_yaml(config_path)
    outputs = config["outputs"]
    summary_path = outputs["ambiguity_run_summary_v0_1_1"]
    report_path = project_path(outputs["ambiguity_report_v0_1_1"])
    summary = read_json(summary_path, {})
    if summary.get("status") != "complete":
        raise AssertionError("A auditoria precisa estar completa antes do registro de verificação.")
    summary["verification"] = dict(verification)
    marker_title = "## Verificação executada"
    report = report_path.read_text(encoding="utf-8")
    if f"\n{marker_title}" in report:
        report = report.split(f"\n{marker_title}", maxsplit=1)[0]
    report = report.rstrip()
    rows = [
        {
            "verificação": key,
            "comando": value.get("command"),
            "código": value.get("exit_code"),
            "resultado": value.get("result"),
        }
        for key, value in verification.items()
        if isinstance(value, Mapping) and "exit_code" in value
    ]
    report += (
        "\n\n"
        + marker_title
        + "\n\n"
        + _markdown_table(rows, ["verificação", "comando", "código", "resultado"])
        + "\n"
    )
    _write_text(report_path, report)
    summary["output_hashes"][report_path.relative_to(PROJECT_ROOT).as_posix()] = sha256_file(
        report_path
    )
    write_json(summary_path, summary)
    return summary
