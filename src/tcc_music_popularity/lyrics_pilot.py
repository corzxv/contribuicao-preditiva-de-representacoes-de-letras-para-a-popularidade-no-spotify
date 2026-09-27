"""Piloto controlado de consulta de letras no LRCLIB, sem texto em artefatos públicos."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import polars as pl

from .config import PROJECT_ROOT, load_yaml, project_path
from .io import git_commit, read_json, sha256_file, utc_now, write_json
from .normalization import base_title, classify_version, conservative_normalize

PILOT_VERSION = "v0.1"
DEFAULT_CONFIG_PATH = "configs/lyrics_pilot_v0_1.yaml"
PERIODS = ("2000-2005", "2006-2011", "2012-2017", "2018-2023")
VERSION_FLAGS = (
    "remaster",
    "remix",
    "live",
    "acoustic",
    "radio_edit",
    "mono_stereo",
    "instrumental",
    "demo",
    "karaoke",
)
SUCCESS_FIELDS = {"spotify_popularity", "genius_lyrics_views", "lfm_playcount"}
EXPECTED_FROZEN_HASHES = {
    "data/processed/modeling_base_lfm_v0_1.parquet": (
        "7a0c15c905081fb7fe672478513d706c40fbd709d2af4077173803484a02ab59"
    ),
    "data/processed/modeling_base_lfm_v0_1_1.parquet": (
        "1c28f31e9b466b76d7e0180b769ba7ac51c46d2590ad7b1ba1ed21eaebdd1c5c"
    ),
    "data/processed/split_assignments_v0_1_1.parquet": (
        "4b0ff5a0e9be21af15607b9bbced423c99247c7d1aaa9615635baf134b86856b"
    ),
}

_KARAOKE_RE = re.compile(r"\bkaraoke(?:\s+version)?\b", re.IGNORECASE)
_BRACKETED_RE = re.compile(r"\s*[\[(]([^\])]+)[\])]\s*")
_DASH_SUFFIX_RE = re.compile(r"\s+-\s+(.+)$")


def _atomic_write_frame(frame: pl.DataFrame, path: str | Path, *, csv: bool = False) -> None:
    destination = project_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    suffix = ".csv.tmp" if csv else ".parquet.tmp"
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False, suffix=suffix) as handle:
        temporary = Path(handle.name)
    try:
        if csv:
            frame.write_csv(temporary)
        else:
            frame.write_parquet(temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _write_text(path: str | Path, value: str) -> None:
    destination = project_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=destination.parent, delete=False, suffix=".tmp"
    ) as handle:
        handle.write(value)
        temporary = Path(handle.name)
    os.replace(temporary, destination)


def _stable_hash(seed: int, *values: Any) -> str:
    serialized = "|".join("" if value is None else str(value) for value in values)
    return hashlib.sha256(f"{seed}|{serialized}".encode()).hexdigest()


def _period(year: int | None) -> str | None:
    if year is None:
        return None
    if 2000 <= year <= 2005:
        return PERIODS[0]
    if 2006 <= year <= 2011:
        return PERIODS[1]
    if 2012 <= year <= 2017:
        return PERIODS[2]
    if 2018 <= year <= 2023:
        return PERIODS[3]
    return None


def _quintile(value: float | int, cutpoints: Sequence[float]) -> str:
    index = sum(float(value) > threshold for threshold in cutpoints) + 1
    return f"Q{index}"


def milliseconds_to_seconds(value: int | float | None) -> float | None:
    return None if value is None else float(value) / 1000.0


def _text_present(value: Any) -> bool:
    return value is not None and bool(str(value).strip())


def _version_flags(title: Any) -> dict[str, bool]:
    flags = classify_version(title)
    return {
        **{name: bool(flags.get(name)) for name in VERSION_FLAGS[:-1]},
        "karaoke": bool(_KARAOKE_RE.search(str(title or ""))),
    }


def pilot_base_title(value: Any) -> str | None:
    """Remove apenas qualificadores de versão conhecidos, incluindo karaoke."""
    result = base_title(value)
    if result is None:
        return None

    def bracket_replacer(match: re.Match[str]) -> str:
        return " " if _KARAOKE_RE.search(match.group(1)) else match.group(0)

    result = _BRACKETED_RE.sub(bracket_replacer, result)
    suffix = _DASH_SUFFIX_RE.search(result)
    if suffix and _KARAOKE_RE.search(suffix.group(1)):
        result = result[: suffix.start()]
    return re.sub(r"\s+", " ", result).strip()


def _version_profile(row: Mapping[str, Any]) -> str:
    active = [name for name in VERSION_FLAGS if bool(row.get(name))]
    return "+".join(active) if active else "original_sem_flag"


def _allocate_proportional(capacities: Mapping[str, int], total: int) -> dict[str, int]:
    """Alocação de Hamilton com capacidade e desempate lexical determinístico."""
    clean = {str(key): int(value) for key, value in capacities.items() if int(value) > 0}
    available = sum(clean.values())
    if total < 0 or total > available:
        raise ValueError(f"Amostra {total} incompatível com capacidade {available}.")
    if total == 0:
        return {key: 0 for key in clean}
    exact = {key: total * capacity / available for key, capacity in clean.items()}
    allocation = {key: min(capacity, math.floor(exact[key])) for key, capacity in clean.items()}
    remaining = total - sum(allocation.values())
    order = sorted(clean, key=lambda key: (-(exact[key] - math.floor(exact[key])), key))
    while remaining:
        progressed = False
        for key in order:
            if allocation[key] < clean[key]:
                allocation[key] += 1
                remaining -= 1
                progressed = True
                if remaining == 0:
                    break
        if not progressed:
            raise RuntimeError("Falha na redistribuição determinística da amostra.")
    return allocation


def _sample_records(
    records: Sequence[dict[str, Any]],
    size: int,
    seed: int,
    *,
    hash_label: str,
) -> list[dict[str, Any]]:
    primary: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        primary[f"{row['period']}|{row['popularity_quintile']}"].append(row)
    primary_quota = _allocate_proportional({key: len(rows) for key, rows in primary.items()}, size)
    selected: list[dict[str, Any]] = []
    for primary_key in sorted(primary):
        quota = primary_quota[primary_key]
        secondary: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in primary[primary_key]:
            secondary_key = "|".join(
                [str(row["genre_sampling"]), str(row["match_method"]), str(row["version_profile"])]
            )
            secondary[secondary_key].append(row)
        secondary_quota = _allocate_proportional(
            {key: len(rows) for key, rows in secondary.items()}, quota
        )
        for secondary_key in sorted(secondary):
            ordered = sorted(
                secondary[secondary_key],
                key=lambda row: (
                    _stable_hash(seed, hash_label, row["composition_key"]),
                    str(row["composition_key"]),
                ),
            )
            selected.extend(ordered[: secondary_quota[secondary_key]])
    return sorted(
        selected,
        key=lambda row: (
            _stable_hash(seed, hash_label, row["composition_key"]),
            str(row["composition_key"]),
        ),
    )


def _join_pilot_source(config: Mapping[str, Any]) -> tuple[pl.DataFrame, list[float]]:
    inputs = config["inputs"]
    base = pl.read_parquet(project_path(inputs["modeling_base"]))
    split = pl.read_parquet(project_path(inputs["split_assignments"]))
    audit = pl.read_parquet(project_path(inputs["matching_audit"]))
    identifiers = ["spotify_row_id", "track_id", "lfm_record_key"]
    required_base = [
        *identifiers,
        "split",
        "spotify_popularity",
        "year",
        "genre",
        "duration_ms",
        "remaster",
        "remix",
        "live",
        "acoustic",
        "radio_edit",
        "mono_stereo",
        "instrumental",
        "demo",
    ]
    source = (
        base.select(required_base)
        .join(
            split.select([*identifiers, "composition_key", "split_random_state", "split_version"]),
            on=identifiers,
            how="left",
            validate="1:1",
        )
        .join(
            audit.select(
                [
                    *identifiers,
                    "artist_name_raw",
                    "track_name_raw",
                    "match_method",
                    "match_score",
                    "match_status",
                    "version_compatible",
                    "matching_version",
                ]
            ),
            on=identifiers,
            how="left",
            validate="1:1",
        )
    )
    if source.height != base.height:
        raise AssertionError("Junção do piloto alterou a quantidade de linhas da base controlada.")
    development = source.filter(pl.col("split") == "development_train")
    probabilities = (0.2, 0.4, 0.6, 0.8)
    cutpoints = [
        float(development.get_column("spotify_popularity").quantile(q, interpolation="nearest"))
        for q in probabilities
    ]
    return development, cutpoints


def _representative_records(
    development: pl.DataFrame, cutpoints: Sequence[float]
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    excluded_missing_key = 0
    for source_row in development.iter_rows(named=True):
        if not _text_present(source_row["composition_key"]):
            excluded_missing_key += 1
            continue
        row = dict(source_row)
        flags = _version_flags(row["track_name_raw"])
        row["karaoke"] = flags["karaoke"]
        row["title_base"] = pilot_base_title(row["track_name_raw"])
        row["period"] = _period(row["year"])
        row["popularity_quintile"] = _quintile(row["spotify_popularity"], cutpoints)
        row["genre_sampling"] = str(row["genre"] or "(ausente)")
        row["version_profile"] = _version_profile(row)
        row["_preferred_original"] = int(
            not any(bool(row.get(name)) for name in ("live", "remix", "acoustic", "karaoke"))
        )
        row["_status_rank"] = {
            "accepted_high_confidence": 2,
            "accepted_with_rules": 1,
        }.get(str(row["match_status"]), 0)
        row["_method_rank"] = {
            "raw_exact": 4,
            "strict_normalized": 3,
            "conservative_normalized": 2,
            "base_title_version_compatible": 1,
        }.get(str(row["match_method"]), 0)
        row["_completeness"] = sum(
            [
                _text_present(row["artist_name_raw"]),
                _text_present(row["track_name_raw"]),
                row["duration_ms"] is not None,
            ]
        )
        rows.append(row)
    ordered = sorted(
        rows,
        key=lambda row: (
            str(row["composition_key"]),
            -row["_preferred_original"],
            -row["_status_rank"],
            -row["_method_rank"],
            -(float(row["match_score"]) if row["match_score"] is not None else -1.0),
            -row["_completeness"],
            int(row["spotify_row_id"]),
            str(row["track_id"]),
        ),
    )
    representatives: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in ordered:
        key = str(row["composition_key"])
        if key not in seen:
            representatives.append(row)
            seen.add(key)
    audit_counts = {
        "development_rows": development.height,
        "excluded_missing_composition_key_rows": excluded_missing_key,
        "eligible_unique_compositions": len(representatives),
        "duplicate_rows_collapsed": len(rows) - len(representatives),
    }
    return representatives, audit_counts


def _counter_rows(
    records: Iterable[Mapping[str, Any]], fields: Sequence[str]
) -> list[dict[str, Any]]:
    counts = Counter(tuple(str(row.get(field)) for field in fields) for row in records)
    return [
        {**{field: values[index] for index, field in enumerate(fields)}, "n": count}
        for values, count in sorted(counts.items())
    ]


def _markdown_table(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> str:
    if not rows:
        return "_Sem registros._"
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(str(row.get(column, "")).replace("|", "\\|") for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _frozen_state() -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    for relative, expected in EXPECTED_FROZEN_HASHES.items():
        path = project_path(relative)
        observed = sha256_file(path) if path.exists() else None
        artifacts[relative] = {
            "expected_sha256": expected,
            "observed_sha256": observed,
            "identical": observed == expected,
        }
    split = pl.read_parquet(project_path("data/processed/split_assignments_v0_1_1.parquet"))
    counts = {
        str(row["split"]): int(row["len"])
        for row in split.group_by("split").len().sort("split").to_dicts()
    }
    development_ids = set(
        split.filter(pl.col("split") == "development_train").get_column("spotify_row_id").to_list()
    )
    holdout_ids = set(
        split.filter(pl.col("split") == "holdout_test").get_column("spotify_row_id").to_list()
    )
    return {
        "artifacts": artifacts,
        "all_hashes_identical": all(item["identical"] for item in artifacts.values()),
        "split_counts": counts,
        "row_count": split.height,
        "development_holdout_id_overlap": len(development_ids & holdout_ids),
    }


def _source_assessment_text(config: Mapping[str, Any]) -> str:
    user_agent = config["lrclib"]["user_agent"]
    return f"""# Avaliação da fonte de letras — Piloto v0.1

Data de acesso documental: 2026-09-04.

## Fonte e acesso

- Fonte exclusiva: LRCLIB (`https://lrclib.net`).
- Documentação oficial: `https://lrclib.net/docs`.
- Endpoints GET implementados: `/api/get` (consulta por metadados) e `/api/search` (busca estruturada por artista e faixa).
- Os GET documentados são públicos e não exigem chave de API.
- A documentação informa que `/api/search` retorna no máximo 20 resultados e não oferece paginação.
- User-Agent identificador: `{user_agent}`.
- O coletor aplica cache local, timeout, tentativas limitadas, backoff e intervalo mínimo entre requisições.

## Licenças e direitos

O repositório oficial do servidor LRCLIB (`https://github.com/tranxuanthang/lrclib`) licencia o **código da plataforma** sob MIT. Essa licença de software não confirma licença aberta para reprodução ou redistribuição do **conteúdo das letras**. Não foi localizada, na documentação oficial consultada, uma licença aberta inequívoca que autorize redistribuir em massa as letras retornadas.

Consequentemente, este piloto trata o texto como material privado de pesquisa: respostas brutas e textos permanecem somente em `data/raw/lyrics_private/`, caminho ignorado pelo Git; nenhum trecho é gravado em relatórios, testes, logs, CSVs ou Parquets processados. Artefatos processados expõem apenas metadados técnicos, contagens e SHA-256. A ampliação além do smoke test depende de nova avaliação técnica e jurídica.
"""


def prepare_lyrics_pilot(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config = load_yaml(config_path)
    size = int(config["cohort_size"])
    smoke_size = int(config["smoke_size"])
    seed = int(config["random_state"])
    frozen_before = _frozen_state()
    if not frozen_before["all_hashes_identical"]:
        raise AssertionError(
            "Um ou mais artefatos congelados não correspondem ao checkpoint v0.1.1."
        )
    development, cutpoints = _join_pilot_source(config)
    representatives, audit_counts = _representative_records(development, cutpoints)
    eligible = [row for row in representatives if row["period"] in PERIODS]
    if len(eligible) < size:
        raise AssertionError(
            f"Somente {len(eligible)} composições elegíveis para amostra de {size}."
        )
    cohort_records = _sample_records(eligible, size, seed, hash_label="cohort")
    smoke_records = _sample_records(cohort_records, smoke_size, seed, hash_label="smoke")
    smoke_order = {str(row["composition_key"]): index for index, row in enumerate(smoke_records, 1)}
    public_rows: list[dict[str, Any]] = []
    lookup_rows: list[dict[str, Any]] = []
    for index, row in enumerate(cohort_records, 1):
        composition = str(row["composition_key"])
        duration_seconds = milliseconds_to_seconds(row["duration_ms"])
        public = {
            "pilot_version": PILOT_VERSION,
            "random_state": seed,
            "sample_order": index,
            "smoke_selected": composition in smoke_order,
            "smoke_order": smoke_order.get(composition),
            "composition_key": composition,
            "representative_spotify_row_id": row["spotify_row_id"],
            "representative_track_id": row["track_id"],
            "representative_lfm_record_key": row["lfm_record_key"],
            "artist_name_query": row["artist_name_raw"],
            "track_name_query": row["track_name_raw"],
            "title_base_query": row["title_base"],
            "album_name_query": None,
            "duration_ms": row["duration_ms"],
            "duration_seconds": duration_seconds,
            "year": row["year"],
            "period": row["period"],
            "genre": row["genre"],
            "popularity_quintile": row["popularity_quintile"],
            "spotify_popularity": row["spotify_popularity"],
            "match_method": row["match_method"],
            "match_status": row["match_status"],
            "match_score": row["match_score"],
            "version_compatible": row["version_compatible"],
            "version_profile": row["version_profile"],
            **{name: bool(row.get(name)) for name in VERSION_FLAGS},
            "selection_hash": _stable_hash(seed, "cohort", composition),
        }
        public_rows.append(public)
        lookup_rows.append(
            {
                "pilot_version": PILOT_VERSION,
                "sample_order": index,
                "smoke_selected": composition in smoke_order,
                "smoke_order": smoke_order.get(composition),
                "composition_key": composition,
                "representative_spotify_row_id": row["spotify_row_id"],
                "representative_track_id": row["track_id"],
                "artist_name_query": row["artist_name_raw"],
                "track_name_query": row["track_name_raw"],
                "title_base_query": row["title_base"],
                "album_name_query": None,
                "duration_ms": row["duration_ms"],
                "duration_seconds": duration_seconds,
                **{name: bool(row.get(name)) for name in VERSION_FLAGS},
            }
        )
    cohort = pl.DataFrame(public_rows)
    lookup = pl.DataFrame(lookup_rows)
    forbidden_lookup = SUCCESS_FIELDS & set(lookup.columns)
    if forbidden_lookup:
        raise AssertionError(f"Medidas de sucesso presentes no lookup: {sorted(forbidden_lookup)}")
    if cohort.height != size or cohort.get_column("composition_key").n_unique() != size:
        raise AssertionError("A coorte não contém exatamente 2.000 composições únicas.")
    if cohort.filter(pl.col("smoke_selected")).height != smoke_size:
        raise AssertionError("O subconjunto smoke não contém exatamente 100 composições.")
    if cohort.get_column("composition_key").null_count():
        raise AssertionError("A coorte contém composition_key ausente.")
    if cohort.filter(pl.col("split") == "holdout_test").height if "split" in cohort.columns else 0:
        raise AssertionError("A coorte contém observação do holdout.")
    outputs = config["outputs"]
    _atomic_write_frame(cohort, outputs["cohort_parquet"])
    _atomic_write_frame(cohort, outputs["cohort_csv"], csv=True)
    _atomic_write_frame(lookup, outputs["lookup_parquet"])
    primary_population = _counter_rows(eligible, ["period", "popularity_quintile"])
    primary_sample = _counter_rows(public_rows, ["period", "popularity_quintile"])
    smoke_primary = _counter_rows(
        [row for row in public_rows if row["smoke_selected"]],
        ["period", "popularity_quintile"],
    )
    report = f"""# Amostragem do Piloto de Letras v0.1

## Resultado

- Seed: `{seed}`.
- Universo: somente `development_train` da Base v0.1.1 revisada.
- Linhas no desenvolvimento: {audit_counts["development_rows"]:,}.
- Linhas excluídas por `composition_key` ausente: {audit_counts["excluded_missing_composition_key_rows"]:,}.
- Composições elegíveis únicas: {len(eligible):,}.
- Linhas redundantes colapsadas na escolha de representante: {audit_counts["duplicate_rows_collapsed"]:,}.
- Coorte selecionada: {cohort.height:,} composições únicas.
- Smoke test pré-selecionado: {smoke_size:,} composições únicas.
- Limiares dos quintis de `spotify_popularity`, calculados somente em `development_train`: {", ".join(str(value) for value in cutpoints)}.

## Regra do representante

Para cada `composition_key`, sem usar popularidade no ranqueamento: (1) preferência por registros sem flags live/remix/acoustic/karaoke; (2) maior confiança do match Spotify–LFM2b por status, método e score já congelados; (3) maior completude de artista, título e duração; (4) menor `spotify_row_id`, seguido do menor `track_id`, como desempate estável.

## Alocação

A alocação primária é proporcional nos 20 estratos período × quintil. Dentro de cada estrato, a alocação proporcional conjunta usa gênero, método de matching e perfil de versão. Restos e déficits são redistribuídos pelo método de Hamilton com desempate lexical determinístico. A seleção dentro das células usa SHA-256 com a seed informada. O mesmo princípio gera o smoke de 100 casos a partir da coorte de 2.000.

### Universo elegível por estrato primário

{_markdown_table(primary_population, ["period", "popularity_quintile", "n"])}

### Coorte de 2.000 por estrato primário

{_markdown_table(primary_sample, ["period", "popularity_quintile", "n"])}

### Smoke de 100 por estrato primário

{_markdown_table(smoke_primary, ["period", "popularity_quintile", "n"])}

## Controles

- Nenhum registro do `holdout_test` foi utilizado.
- Casos sem `composition_key` não foram selecionados.
- O lookup de consulta não contém `spotify_popularity`, `genius_lyrics_views`, `lfm_playcount` nem qualquer quintil ou métrica de sucesso.
- A fonte não fornece álbum no schema congelado utilizado; `album_name_query` permanece nulo e não é inventado.
- A seleção busca cobertura e heterogeneidade; não pretende maximizar taxa de sucesso da coleta.
"""
    _write_text(outputs["sampling_report"], report)
    _write_text(outputs["source_assessment"], _source_assessment_text(config))
    frozen_after = _frozen_state()
    return {
        "status": "prepared",
        "pilot_version": PILOT_VERSION,
        "random_state": seed,
        "cohort_rows": cohort.height,
        "unique_compositions": cohort.get_column("composition_key").n_unique(),
        "smoke_rows": smoke_size,
        "lookup_columns": lookup.columns,
        "lookup_forbidden_success_fields": sorted(forbidden_lookup),
        "popularity_quintile_cutpoints": list(cutpoints),
        "audit": audit_counts,
        "frozen_before": frozen_before,
        "frozen_after": frozen_after,
        "outputs": {key: str(project_path(value)) for key, value in outputs.items()},
    }


Transport = Callable[[str, Mapping[str, str], float], tuple[int, Any]]


def _default_transport(url: str, headers: Mapping[str, str], timeout: float) -> tuple[int, Any]:
    request = urllib.request.Request(url, headers=dict(headers), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            status = int(response.status)
            body = response.read().decode("utf-8")
            return status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body) if body else None
        except json.JSONDecodeError:
            payload = {"error_body_sha256": hashlib.sha256(body.encode()).hexdigest()}
        return int(exc.code), payload


class LRCLIBClient:
    """Cliente GET com cache bruto privado e política explícita de retomada."""

    def __init__(
        self,
        config: Mapping[str, Any],
        *,
        transport: Transport | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.base_url = str(config["base_url"]).rstrip("/")
        self.cache_dir = project_path(config["cache_dir"])
        self.user_agent = str(config["user_agent"])
        self.timeout = float(config["timeout_seconds"])
        self.max_attempts = int(config["max_attempts"])
        self.backoff = float(config["backoff_seconds"])
        self.minimum_delay = float(config["minimum_delay_seconds"])
        self.cache_version = str(config.get("cache_version", PILOT_VERSION))
        self.transport = transport or _default_transport
        self.sleep_fn = sleep_fn
        self._last_request_at: float | None = None

    def _request(self, endpoint: str, parameters: Mapping[str, Any]) -> dict[str, Any]:
        clean_parameters = {
            key: value for key, value in parameters.items() if value not in (None, "")
        }
        url = f"{self.base_url}{endpoint}?{urllib.parse.urlencode(clean_parameters)}"
        attempts: list[dict[str, Any]] = []
        for number in range(1, self.max_attempts + 1):
            if self._last_request_at is not None:
                remaining = self.minimum_delay - (time.monotonic() - self._last_request_at)
                if remaining > 0:
                    self.sleep_fn(remaining)
            started = time.perf_counter()
            try:
                status, payload = self.transport(
                    url,
                    {"User-Agent": self.user_agent, "Accept": "application/json"},
                    self.timeout,
                )
                self._last_request_at = time.monotonic()
                attempts.append(
                    {
                        "attempt": number,
                        "http_status": int(status),
                        "elapsed_seconds": round(time.perf_counter() - started, 6),
                        "error_type": None,
                    }
                )
                if status not in {429, 500, 502, 503, 504} or number == self.max_attempts:
                    return {"http_status": int(status), "payload": payload, "attempts": attempts}
            except (TimeoutError, urllib.error.URLError, OSError) as exc:
                self._last_request_at = time.monotonic()
                attempts.append(
                    {
                        "attempt": number,
                        "http_status": None,
                        "elapsed_seconds": round(time.perf_counter() - started, 6),
                        "error_type": type(exc).__name__,
                        "error_message": str(exc)[:500],
                    }
                )
                if number == self.max_attempts:
                    return {"http_status": None, "payload": None, "attempts": attempts}
            self.sleep_fn(self.backoff * (2 ** (number - 1)))
        raise AssertionError("Laço de tentativas terminou sem retorno.")

    def lookup(self, row: Mapping[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
        cache_key = hashlib.sha256(str(row["composition_key"]).encode()).hexdigest()
        cache_path = self.cache_dir / f"{cache_key}.json"
        if cache_path.exists():
            with cache_path.open(encoding="utf-8") as handle:
                envelope = json.load(handle)
            envelope["cache_reused_current_run"] = True
            return envelope
        if dry_run:
            return {
                "cache_version": self.cache_version,
                "cache_key": cache_key,
                "cache_hit": False,
                "cache_reused_current_run": False,
                "dry_run": True,
                "composition_key": row["composition_key"],
                "requests": [],
            }
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        shared = {
            "artist_name": row["artist_name_query"],
            "track_name": row["track_name_query"],
            "album_name": row.get("album_name_query"),
        }
        get_parameters = {**shared, "duration": row.get("duration_seconds")}
        search_parameters = shared
        get_result = self._request("/api/get", get_parameters)
        search_result = self._request("/api/search", search_parameters)
        envelope = {
            "cache_version": self.cache_version,
            "cache_key": cache_key,
            "cache_hit": False,
            "cache_reused_current_run": False,
            "dry_run": False,
            "composition_key": row["composition_key"],
            "queried_at": utc_now(),
            "requests": [
                {"endpoint": "/api/get", "parameters": get_parameters, **get_result},
                {"endpoint": "/api/search", "parameters": search_parameters, **search_result},
            ],
        }
        write_json(cache_path, envelope)
        return envelope


def _candidate_version_compatible(query: Mapping[str, Any], candidate: Mapping[str, Any]) -> bool:
    returned = _version_flags(candidate.get("trackName") or candidate.get("name"))
    return all(bool(query.get(flag)) == bool(returned.get(flag)) for flag in VERSION_FLAGS)


def _candidate_diagnostics(
    query: Mapping[str, Any], candidate: Mapping[str, Any], duration_tolerance: float
) -> dict[str, Any]:
    query_artist = conservative_normalize(query.get("artist_name_query"))
    returned_artist = conservative_normalize(candidate.get("artistName"))
    query_title = conservative_normalize(query.get("track_name_query"))
    returned_title = conservative_normalize(candidate.get("trackName") or candidate.get("name"))
    query_base = conservative_normalize(query.get("title_base_query"))
    returned_base = conservative_normalize(
        pilot_base_title(candidate.get("trackName") or candidate.get("name"))
    )
    artist_exact = bool(query_artist and query_artist == returned_artist)
    title_exact = bool(query_title and query_title == returned_title)
    base_exact = bool(query_base and query_base == returned_base)
    query_duration = query.get("duration_seconds")
    returned_duration = candidate.get("duration")
    duration_difference = None
    duration_compatible = True
    if query_duration is not None and returned_duration is not None:
        duration_difference = abs(float(query_duration) - float(returned_duration))
        duration_compatible = duration_difference <= duration_tolerance
    version_compatible = _candidate_version_compatible(query, candidate)
    return {
        "artist_compatible": artist_exact,
        "title_compatible": title_exact or base_exact,
        "title_exact": title_exact,
        "base_title_exact": base_exact,
        "version_compatible": version_compatible,
        "duration_compatible": duration_compatible,
        "duration_difference_seconds": duration_difference,
        "accepted_by_rules": artist_exact
        and (title_exact or base_exact)
        and version_compatible
        and duration_compatible,
    }


def _safe_attempt_error(requests: Sequence[Mapping[str, Any]]) -> str | None:
    errors: list[str] = []
    for request in requests:
        for attempt in request.get("attempts", []):
            if attempt.get("error_type"):
                errors.append(
                    f"{request.get('endpoint')}:{attempt['error_type']}:{attempt.get('error_message', '')}"
                )
    return " | ".join(errors)[:1000] or None


def process_lookup_response(
    query: Mapping[str, Any], envelope: Mapping[str, Any], *, duration_tolerance: float = 10.0
) -> dict[str, Any]:
    requests = list(envelope.get("requests", []))
    by_endpoint = {str(request.get("endpoint")): request for request in requests}
    get_request = by_endpoint.get("/api/get", {})
    search_request = by_endpoint.get("/api/search", {})
    search_ok = search_request.get("http_status") == 200
    candidates: dict[str, dict[str, Any]] = {}
    get_payload = get_request.get("payload")
    if get_request.get("http_status") == 200 and isinstance(get_payload, dict):
        candidates[str(get_payload.get("id", "get_without_id"))] = get_payload
    search_payload = search_request.get("payload")
    if search_ok and isinstance(search_payload, list):
        for index, candidate in enumerate(search_payload):
            if isinstance(candidate, dict):
                candidates[str(candidate.get("id", f"search_without_id_{index}"))] = candidate
    candidate_list = list(candidates.values())
    diagnostics = [
        (candidate, _candidate_diagnostics(query, candidate, duration_tolerance))
        for candidate in candidate_list
    ]
    compatible = [(candidate, item) for candidate, item in diagnostics if item["accepted_by_rules"]]
    selected: dict[str, Any] | None = None
    selected_diagnostics: dict[str, Any] | None = None
    if not search_ok:
        status = "request_error"
    elif len(compatible) > 1:
        status = "ambiguous"
    elif len(compatible) == 1:
        selected, selected_diagnostics = compatible[0]
        status = "instrumental" if bool(selected.get("instrumental")) else "accepted_exact"
    elif candidate_list:
        status = "needs_review"
    else:
        status = "not_found"
    text_value: str | None = None
    text_source: str | None = None
    if selected is not None and status == "accepted_exact":
        if _text_present(selected.get("plainLyrics")):
            text_value = str(selected["plainLyrics"])
            text_source = "plain"
        elif _text_present(selected.get("syncedLyrics")):
            text_value = str(selected["syncedLyrics"])
            text_source = "synced"
    total_attempts = sum(len(request.get("attempts", [])) for request in requests)
    retry_attempts = max(total_attempts - len(requests), 0)
    retryable_http_attempts = sum(
        1
        for request in requests
        for attempt in request.get("attempts", [])
        if attempt.get("http_status") in {429, 500, 502, 503, 504}
    )
    http_statuses = ";".join(
        f"{request.get('endpoint')}:{request.get('http_status')}" for request in requests
    )
    http_attempt_statuses = ";".join(
        f"{request.get('endpoint')}:[{','.join(str(attempt.get('http_status')) for attempt in request.get('attempts', []))}]"
        for request in requests
    )
    return {
        "pilot_version": PILOT_VERSION,
        "composition_key": query["composition_key"],
        "representative_spotify_row_id": query["representative_spotify_row_id"],
        "representative_track_id": query["representative_track_id"],
        "lrclib_id": selected.get("id") if selected else None,
        "queried_artist": query.get("artist_name_query"),
        "queried_title": query.get("track_name_query"),
        "queried_album": query.get("album_name_query"),
        "queried_duration_seconds": query.get("duration_seconds"),
        "returned_artist": selected.get("artistName") if selected else None,
        "returned_title": (selected.get("trackName") or selected.get("name")) if selected else None,
        "returned_album": selected.get("albumName") if selected else None,
        "returned_duration_seconds": selected.get("duration") if selected else None,
        "duration_difference_seconds": (
            selected_diagnostics.get("duration_difference_seconds")
            if selected_diagnostics
            else None
        ),
        "candidate_count": len(candidate_list),
        "query_method": "metadata_get_plus_structured_search",
        "final_status": status,
        "match_score": None,
        "artist_compatible": selected_diagnostics.get("artist_compatible")
        if selected_diagnostics
        else None,
        "title_compatible": selected_diagnostics.get("title_compatible")
        if selected_diagnostics
        else None,
        "base_title_exact": selected_diagnostics.get("base_title_exact")
        if selected_diagnostics
        else None,
        "version_compatible": selected_diagnostics.get("version_compatible")
        if selected_diagnostics
        else None,
        "duration_compatible": selected_diagnostics.get("duration_compatible")
        if selected_diagnostics
        else None,
        "instrumental": bool(selected.get("instrumental")) if selected else False,
        "plain_lyrics_available": bool(selected and _text_present(selected.get("plainLyrics"))),
        "synced_lyrics_available": bool(selected and _text_present(selected.get("syncedLyrics"))),
        "lyrics_text_source_for_metrics": text_source,
        "lyrics_character_count": len(text_value) if text_value is not None else None,
        "lyrics_line_count": len(text_value.splitlines()) if text_value is not None else None,
        "lyrics_sha256": hashlib.sha256(text_value.encode()).hexdigest()
        if text_value is not None
        else None,
        "queried_at": envelope.get("queried_at"),
        "http_status": http_statuses,
        "http_attempt_statuses": http_attempt_statuses,
        "attempts": total_attempts,
        "retry_attempts": retry_attempts,
        "retryable_http_attempts": retryable_http_attempts,
        "cache_hit": bool(envelope.get("cache_hit")),
        "cache_reused_current_run": bool(envelope.get("cache_reused_current_run")),
        "technical_error": _safe_attempt_error(requests),
    }


def _git_tracked_private_files() -> list[str]:
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={PROJECT_ROOT.as_posix()}",
            "ls-files",
            "data/raw/lyrics_private",
            "data/interim/lyrics_private",
        ],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def _distribution(records: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in records).items()))


def _build_smoke_report(
    results: pl.DataFrame,
    cohort_smoke: pl.DataFrame,
    elapsed_seconds: float,
) -> str:
    joined = results.join(
        cohort_smoke.select(
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
    status_rows = joined.group_by("final_status").len().sort("final_status").to_dicts()
    for row in status_rows:
        row["percentual"] = round(100 * int(row["len"]) / max(results.height, 1), 2)
    accepted = joined.filter(pl.col("final_status") == "accepted_exact")
    duration = accepted.get_column("duration_difference_seconds").drop_nulls()
    duration_stats = {
        "n": duration.len(),
        "min": float(duration.min()) if duration.len() else None,
        "median": float(duration.median()) if duration.len() else None,
        "mean": float(duration.mean()) if duration.len() else None,
        "max": float(duration.max()) if duration.len() else None,
    }
    retried = results.filter(pl.col("retry_attempts") > 0).height
    retry_attempts = int(results.get_column("retry_attempts").sum())
    retryable_http_attempts = int(results.get_column("retryable_http_attempts").sum())
    technical_errors = results.get_column("technical_error").drop_nulls().len()
    candidate_counts = results.get_column("candidate_count")
    candidate_stats = {
        "min": int(candidate_counts.min()),
        "median": float(candidate_counts.median()),
        "mean": round(float(candidate_counts.mean()), 3),
        "max": int(candidate_counts.max()),
    }
    return f"""# Relatório do Smoke Test — Piloto de Letras v0.1

## Execução observada

- Consultas únicas previstas e processadas: {results.height}.
- Tempo total: {elapsed_seconds:.3f} segundos.
- Cache preexistente na aquisição original: {results.filter(pl.col("cache_hit")).height}.
- Resultados reprocessados do cache nesta execução: {results.filter(pl.col("cache_reused_current_run")).height}.
- Casos com repetição de requisição: {retried}; tentativas adicionais: {retry_attempts}.
- Respostas HTTP transitórias elegíveis a retry (429/5xx): {retryable_http_attempts}.
- Casos com erro técnico registrado: {technical_errors}.
- Letras em formato plain disponíveis no candidato aceito/instrumental: {results.filter(pl.col("plain_lyrics_available")).height}.
- Letras sincronizadas disponíveis no candidato aceito/instrumental: {results.filter(pl.col("synced_lyrics_available")).height}.
- Nenhum texto de letra foi gravado neste relatório ou no Parquet processado.

## Status finais

{_markdown_table(status_rows, ["final_status", "len", "percentual"])}

Contagem de candidatos retornados/deduplicados por composição: `{json.dumps(candidate_stats, ensure_ascii=False)}`.

Combinações de status HTTP finais:

{_markdown_table(results.group_by("http_status").len().sort("http_status").to_dicts(), ["http_status", "len"])}

## Cobertura do desenho amostral

- Estratos período × quintil representados: {joined.select(["period", "popularity_quintile"]).unique().height} de 20.
- Gêneros representados: {joined.get_column("genre").n_unique()}.
- Métodos de matching representados: {joined.get_column("match_method").n_unique()}.
- Perfis de versão representados: {joined.get_column("version_profile").n_unique()}.
- Observação metodológica: o arredondamento proporcional nas células conjuntas gênero × método × versão preservou os 20 estratos primários e 25 gêneros, mas o smoke observado reteve somente dois métodos e apenas o perfil sem flag. Esse desequilíbrio marginal deve ser corrigido antes de qualquer repetição ou escala.

### Período × quintil

{_markdown_table(joined.group_by(["period", "popularity_quintile"]).len().sort(["period", "popularity_quintile"]).to_dicts(), ["period", "popularity_quintile", "len"])}

### Método de matching da base

{_markdown_table(joined.group_by("match_method").len().sort("match_method").to_dicts(), ["match_method", "len"])}

### Perfil de versão

{_markdown_table(joined.group_by("version_profile").len().sort("version_profile").to_dicts(), ["version_profile", "len"])}

### Gênero

{_markdown_table(joined.group_by("genre").len().sort("genre").to_dicts(), ["genre", "len"])}

## Diferenças de duração nos aceitos

`{json.dumps(duration_stats, ensure_ascii=False)}`

## Limitações e decisão

O `/api/search` limita a resposta a 20 candidatos sem paginação. O protocolo aceita apenas um candidato único após igualdade normalizada exata de artista e título/título-base, compatibilidade de versão e tolerância de duração de até 10 segundos. Casos aproximados ficam em revisão; a primeira posição retornada nunca é aceita por si só. A licença MIT identificada refere-se ao código do LRCLIB, não confirma licença aberta de redistribuição das letras. Assim, este smoke mede viabilidade técnica, não autoriza escala nem publicação do conteúdo.

**Recomendação operacional: {_recommendation(results)}.** A alta ambiguidade e o desequilíbrio marginal do smoke devem ser tratados antes de novas consultas; as outras 1.900 composições não devem ser consultadas nesta versão.
"""


def _recommendation(results: pl.DataFrame) -> str:
    total = max(results.height, 1)
    accepted_or_instrumental = results.filter(
        pl.col("final_status").is_in(["accepted_exact", "instrumental"])
    ).height
    error_rate = results.filter(pl.col("final_status") == "request_error").height / total
    ambiguity_rate = results.filter(pl.col("final_status") == "ambiguous").height / total
    coverage = accepted_or_instrumental / total
    if error_rate >= 0.10:
        return "ajustar e repetir"
    if coverage >= 0.70:
        return "parar por cautela jurídica"
    if ambiguity_rate >= 0.30:
        return "ajustar e repetir"
    if coverage >= 0.40:
        return "ajustar e repetir"
    return "trocar de fonte"


def run_lyrics_smoke(
    *,
    limit: int = 100,
    dry_run: bool = False,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    client: LRCLIBClient | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    configured_smoke = int(config["smoke_size"])
    if limit < 0 or limit > configured_smoke:
        raise ValueError(f"--limit deve estar entre 0 e {configured_smoke}.")
    lookup_path = project_path(config["outputs"]["lookup_parquet"])
    cohort_path = project_path(config["outputs"]["cohort_parquet"])
    if not lookup_path.exists() or not cohort_path.exists():
        prepare_lyrics_pilot(config_path)
    previous_summary = read_json(config["outputs"]["run_summary"], {})
    lookup = (
        pl.read_parquet(lookup_path)
        .filter(pl.col("smoke_selected"))
        .sort("smoke_order")
        .head(limit)
    )
    forbidden_lookup = SUCCESS_FIELDS & set(lookup.columns)
    if forbidden_lookup:
        raise AssertionError(f"Lookup contém medidas de sucesso: {sorted(forbidden_lookup)}")
    planned = {
        "status": "dry_run" if dry_run else "running",
        "pilot_version": PILOT_VERSION,
        "limit": limit,
        "network_requests_planned": 0 if dry_run else 2 * limit,
        "composition_keys": lookup.get_column("composition_key").to_list(),
    }
    if dry_run:
        return planned
    frozen_before = _frozen_state()
    if not frozen_before["all_hashes_identical"]:
        raise AssertionError("Artefatos congelados divergiram antes do smoke test.")
    active_client = client or LRCLIBClient(config["lrclib"])
    started = time.perf_counter()
    result_rows: list[dict[str, Any]] = []
    for index, row in enumerate(lookup.iter_rows(named=True), 1):
        envelope = active_client.lookup(row)
        result_rows.append(
            process_lookup_response(
                row,
                envelope,
                duration_tolerance=float(config["lrclib"]["duration_tolerance_seconds"]),
            )
        )
        if progress:
            progress(index, lookup.height)
    processing_elapsed = time.perf_counter() - started
    results = pl.DataFrame(result_rows)
    forbidden_text_columns = [
        column
        for column in results.columns
        if column in {"plainLyrics", "syncedLyrics", "lyricsfile"}
    ]
    if forbidden_text_columns:
        raise AssertionError(f"Texto de letra no resultado processado: {forbidden_text_columns}")
    _atomic_write_frame(results, config["outputs"]["smoke_results"])
    cohort_smoke = (
        pl.read_parquet(cohort_path)
        .filter(pl.col("smoke_selected"))
        .sort("smoke_order")
        .head(limit)
    )
    _write_text(
        config["outputs"]["smoke_report"],
        _build_smoke_report(
            results,
            cohort_smoke,
            float(previous_summary.get("duration_seconds", processing_elapsed))
            if results.filter(pl.col("cache_reused_current_run")).height == results.height
            else processing_elapsed,
        ),
    )
    frozen_after = _frozen_state()
    status_counts = {
        str(row["final_status"]): int(row["len"])
        for row in results.group_by("final_status").len().sort("final_status").to_dicts()
    }
    tracked_private = _git_tracked_private_files()
    observed_duration = (
        float(previous_summary.get("duration_seconds", processing_elapsed))
        if results.filter(pl.col("cache_reused_current_run")).height == results.height
        else processing_elapsed
    )
    output_paths = {
        key: project_path(value)
        for key, value in config["outputs"].items()
        if key != "run_summary" and project_path(value).exists()
    }
    summary = {
        "status": "complete",
        "pilot_version": PILOT_VERSION,
        "timestamp": utc_now(),
        "git_commit": git_commit(),
        "random_state": int(config["random_state"]),
        "limit": limit,
        "queried_only_smoke_subset": True,
        "cohort_size": int(config["cohort_size"]),
        "smoke_size": results.height,
        "status_counts": status_counts,
        "coverage_accepted_exact_or_instrumental": round(
            sum(status_counts.get(key, 0) for key in ("accepted_exact", "instrumental"))
            / max(results.height, 1),
            6,
        ),
        "plain_lyrics_available": results.filter(pl.col("plain_lyrics_available")).height,
        "synced_lyrics_available": results.filter(pl.col("synced_lyrics_available")).height,
        "cache_hits": results.filter(pl.col("cache_hit")).height,
        "cache_reused_current_run": results.filter(pl.col("cache_reused_current_run")).height,
        "total_http_attempts": int(results.get_column("attempts").sum()),
        "retry_attempts": int(results.get_column("retry_attempts").sum()),
        "retryable_http_attempts": int(results.get_column("retryable_http_attempts").sum()),
        "final_http_status_combinations": {
            str(row["http_status"]): int(row["len"])
            for row in results.group_by("http_status").len().sort("http_status").to_dicts()
        },
        "technical_error_cases": results.get_column("technical_error").drop_nulls().len(),
        "sampling_coverage": {
            "period_by_quintile_strata": cohort_smoke.select(["period", "popularity_quintile"])
            .unique()
            .height,
            "genres": cohort_smoke.get_column("genre").n_unique(),
            "matching_methods": cohort_smoke.get_column("match_method").n_unique(),
            "version_profiles": cohort_smoke.get_column("version_profile").n_unique(),
        },
        "duration_seconds": round(observed_duration, 6),
        "latest_processing_duration_seconds": round(processing_elapsed, 6),
        "recommendation": _recommendation(results),
        "recommendation_options": [
            "escalar",
            "ajustar e repetir",
            "trocar de fonte",
            "parar por motivo técnico",
            "parar por cautela jurídica",
        ],
        "privacy": {
            "raw_text_location": str(project_path(config["lrclib"]["cache_dir"])),
            "processed_text_columns": forbidden_text_columns,
            "tracked_private_files": tracked_private,
            "lyrics_text_in_reports": False,
        },
        "frozen_before": frozen_before,
        "frozen_after": frozen_after,
        "frozen_artifacts_preserved": frozen_before == frozen_after
        and frozen_after["all_hashes_identical"],
        "output_hashes": {
            path.relative_to(PROJECT_ROOT).as_posix(): sha256_file(path)
            for path in output_paths.values()
        },
    }
    write_json(config["outputs"]["run_summary"], summary)
    return summary


def format_observed_results(summary: Mapping[str, Any]) -> str:
    """Formata a abertura obrigatória do relato final, sem qualquer trecho de letra."""
    statuses = summary.get("status_counts", {})
    return "\n".join(
        [
            "RESULTADOS OBSERVADOS DO PILOTO DE LETRAS V0.1 — SMOKE TEST",
            f"1. Coorte: {summary.get('cohort_size')} composições; smoke: {summary.get('smoke_size')}.",
            f"2. Status finais: {json.dumps(statuses, ensure_ascii=False, sort_keys=True)}.",
            f"3. Cobertura aceita/instrumental: {summary.get('coverage_accepted_exact_or_instrumental')}.",
            f"4. Plain disponível: {summary.get('plain_lyrics_available')}.",
            f"5. Sincronizada disponível: {summary.get('synced_lyrics_available')}.",
            f"6. Casos com erro técnico: {summary.get('technical_error_cases')}.",
            f"7. Tentativas HTTP totais: {summary.get('total_http_attempts')}.",
            f"8. Cache hits: {summary.get('cache_hits')}.",
            f"9. Tempo observado: {summary.get('duration_seconds')} s.",
            f"10. Artefatos congelados preservados: {summary.get('frozen_artifacts_preserved')}.",
            f"11. Arquivos privados rastreados pelo Git: {len(summary.get('privacy', {}).get('tracked_private_files', []))}.",
            f"12. Recomendação: {summary.get('recommendation')}.",
        ]
    )
